from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from backend.retrieval.retrieval import retrieve_context

def format_context(chunks: list) -> str:
    """Aggressively groups and formats retrieved chunks to prevent noisy prompts."""
    sections = {
        "SPECIFICATIONS": [],
        "POSITIVE REVIEWS": [],
        "NEGATIVE REVIEWS": [],
        "YOUTUBE ANALYSIS": []
    }
    
    # Deduplicate text
    seen_texts = set()
    
    for c in chunks:
        text = c["text"].strip()
        if text in seen_texts:
            continue
        seen_texts.add(text)
        
        source = c.get("source", "UNKNOWN").upper()
        sentiment = c["sentiment"]
        
        formatted_entry = f"[{source}] {text}"
        
        if source == "SPEC":
            sections["SPECIFICATIONS"].append(formatted_entry)
        elif source == "YOUTUBE":
            sections["YOUTUBE ANALYSIS"].append(formatted_entry)
        elif sentiment == "POSITIVE":
            sections["POSITIVE REVIEWS"].append(formatted_entry)
        elif sentiment == "NEGATIVE":
            sections["NEGATIVE REVIEWS"].append(formatted_entry)
        else:
            # Group neutral reviews with positive/general
            sections["POSITIVE REVIEWS"].append(formatted_entry)
            
    # Build final context string
    context_str = ""
    for sec_title, items in sections.items():
        if items:
            context_str += f"\n--- {sec_title} ---\n"
            context_str += "\n".join(items) + "\n"
            
    return context_str

def generate_chat_response(query: str, product_id: str = None) -> dict:
    """
    Retrieves context and generates a grounded response using Groq.
    Returns synchronous JSON including metadata.
    """
    # 1. Retrieve
    # Limit to top 10 to ensure we stay well within the token budget (~8k for llama3, though groq handles large contexts, it reduces noise)
    retrieval_data = retrieve_context(query, product_id, top_k=10)
    
    if not retrieval_data["chunks"]:
        return {
            "answer": "I have insufficient product data available to answer this question.",
            "sources_used": [],
            "retrieved_chunks": [],
            "intent": retrieval_data["intent"],
            "confidence_score": 0.0
        }
        
    # 2. Format Context
    context_str = format_context(retrieval_data["chunks"])
    print(f"\n--- Final Prompt Context ---\n{context_str.encode('ascii', 'ignore').decode('ascii')}\n----------------------------\n")
    
    # 3. Initialize LLM
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1)
    
    # 4. Strict Grounding Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert, objective smartphone analyst. "
                   "Only answer using the retrieved context provided below. "
                   "Do not invent missing details. If the context does not contain the answer, explicitly state that the information is unavailable. "
                   "When making claims, explicitly cite the source category (e.g. 'According to YouTube analysis...' or 'User reviews indicate...').\n\n"
                   "CONTEXT:\n{context}"),
        ("human", "{query}")
])
    
    chain = prompt | llm
    
    try:
        result = chain.invoke({
            "context": context_str,
            "query": query
        })
        answer = result.content
    except Exception as e:
        print(f"LLM Generation Error: {e}")
        answer = "I encountered an error while generating the response."
        
    # Calculate a mock confidence score based on the top retrieved chunk's cross-encoder score
    top_score = retrieval_data["chunks"][0]["cross_score"] if retrieval_data["chunks"] else 0.0
    confidence = min(max((top_score + 10) / 20, 0.0), 1.0) # Normalize score roughly to 0-1
    
    return {
        "answer": answer,
        "sources_used": retrieval_data["sources_used"],
        "retrieved_chunks": [{
            "text": c["text"], 
            "source": c.get("source"),
            "sentiment": c.get("sentiment"),
            "score": c.get("cross_score"),
            "url": c.get("source_url")
        } for c in retrieval_data["chunks"]],
        "intent": retrieval_data["intent"],
        "confidence_score": float(confidence)
    }
