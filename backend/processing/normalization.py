import hashlib
import json
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from numpy.strings import lower
from pydantic import BaseModel, Field
import os

class ProductInfo(BaseModel):
    brand: str = Field(description="Exact brand literal if present (e.g., vivo, samsung, apple).")
    model_number: str = Field(description="Exact physical model identifier (e.g., t5x, s23, 15). DO NOT invent synthetic groups like 't-series'. MUST be specific.")
    connectivity: str = Field(description="Connectivity type literal (e.g., 5g, 4g). Empty if none.")
    storage: str = Field(description="Storage capacity literal (e.g., 256gb). Empty if none.")
    ram: str = Field(description="RAM capacity literal (e.g., 8gb). Empty if none.")
    edition: str = Field(description="Special edition literal (e.g., pro, ultra, plus, fe). Empty if none.")

INVALID_QUERY_SIGNALS = [
    "online shopping",
    "shop online",
    "flipkart",
    "home page",
    "sign in",
    "buy online",
    "mobiles, books",
]

def normalize_product_name(raw_query: str) -> dict:
    # Guard before hitting Groq API
    lower = raw_query.lower()
    if any(signal in lower for signal in INVALID_QUERY_SIGNALS) or len(raw_query.strip()) < 5:
        raise ValueError(f"Incomplete product identity in query: {raw_query}")
    
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a strict deterministic identity engine for smartphones. Extract only exact literal identifiers that physically exist in the input text. DO NOT invent synthetic labels, families, or semantic expansions (e.g. do not add 't-series' if only 't5x' is present). If the input is just a brand without a model number, leave model_number empty."),
        ("human", "{text}")
    ])
    
    chain = prompt | llm.with_structured_output(ProductInfo)
    
    try:
        result = chain.invoke({"text": raw_query})

        # Reject partial names that lack specific model numbers
        if not result.brand or not result.model_number:
            print(f"Rejected partial product name: {raw_query}")
            raise ValueError(f"Incomplete product identity in query: {raw_query}")

        parts = []
        if result.brand: parts.append(result.brand.strip().lower())
        if result.model_number: parts.append(result.model_number.strip().lower())
        if result.edition: parts.append(result.edition.strip().lower())
        if result.connectivity: parts.append(result.connectivity.strip().lower())
        if result.ram: parts.append(result.ram.strip().lower())
        if result.storage: parts.append(result.storage.strip().lower())
        
        canonical_name = " ".join([p for p in parts if p])
        
        product_id = hashlib.sha256(canonical_name.encode('utf-8')).hexdigest()
        
        # Map back to old schema for DB compatibility
        model = result.model_number.lower().strip()
        variant_parts = [p for p in [result.edition, result.connectivity, result.ram, result.storage] if p]
        variant = " ".join(variant_parts).strip()
        
        normalized_data = {
            "id": product_id,
            "canonical_name": canonical_name,
            "brand": result.brand.lower().strip() if result.brand else "",
            "model": model,
            "variant": variant,
            "model_number": result.model_number.lower().strip() if result.model_number else "",
            "connectivity": result.connectivity.lower().strip() if result.connectivity else "",
            "storage": result.storage.lower().strip() if result.storage else "",
            "ram": result.ram.lower().strip() if result.ram else "",
            "edition": result.edition.lower().strip() if result.edition else ""
        }
        
        print(f"--- Normalization Result for '{raw_query}' ---")
        print(json.dumps(normalized_data, indent=2))
        print(f"----------------------------------------------")
        
        return normalized_data
        
    except Exception as e:
        print(f"Error normalizing product: {e}")
        raise ValueError(f"Failed to normalize product identity: {raw_query} - {e}")