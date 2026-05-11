import hashlib
from typing import Optional, Dict, Any
from backend.schemas import DocumentPayload
from backend.observability.logger import log_validation_failure

JUNK_PHRASES = [
    "sign in", "privacy notice", "copyright", "terms of service", 
    "all rights reserved", "skip to main content", "add to cart", 
    "buy now", "customer reviews", "frequently bought together"
]

def is_junk(text: str) -> bool:
    text_lower = text.lower()
    return any(phrase in text_lower for phrase in JUNK_PHRASES) or len(text.split()) < 3

def generate_text_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def explicit_product_match(text: str, brand: str, model_number: str) -> bool:
    """Validate that scraped chunks contain high-confidence identity tokens (brand + exact model)."""
    text_lower = text.lower()
    
    brand_words = brand.lower().split() if brand else []
    model_words = model_number.lower().split() if model_number else []
    
    if not brand_words and not model_words:
        return False
        
    for bw in brand_words:
        if len(bw) > 1 and bw not in text_lower:
            return False
            
    for mw in model_words:
        if len(mw) > 1 and mw not in text_lower:
            return False
            
    return True

def validate_and_normalize_chunk(text: str, metadata: Dict[str, Any]) -> Optional[DocumentPayload]:
    """Applies junk filtering, boilerplate rejection, and payload schema validation."""
    if is_junk(text):
        log_validation_failure(text, "junk_filter", metadata)
        return None
        
    canonical_name = metadata.get("canonical_name", "")
    brand = metadata.get("brand", "")
    model_number = metadata.get("model_number", "")
    
    doc_type = metadata.get("doc_type", "review")
    
    # Page-level trust inheritance: if it's a dedicated review chunk, skip strict identity match
    if doc_type != "review":
        if not explicit_product_match(text, brand, model_number):
            log_validation_failure(text, "identity_mismatch", metadata)
            return None

    try:
        payload = DocumentPayload(
            product_id=metadata.get("product_id"),
            canonical_name=canonical_name,
            category=metadata.get("category", "smartphone"),
            source=metadata.get("source", metadata.get("source_type", "unknown")),
            doc_type=doc_type,
            sentiment=metadata.get("sentiment", "NEUTRAL"),
            text_hash=generate_text_hash(text),
            text=text,
            source_url=metadata.get("source_url"),
            sentiment_score=metadata.get("sentiment_score"),
            taxonomy=metadata.get("taxonomy", []),
            rating=metadata.get("rating"),
            author=metadata.get("author"),
            date=metadata.get("date"),
            verified=metadata.get("verified"),
            helpful_votes=metadata.get("helpful_votes")
        )
        return payload
    except Exception as e:
        print(f"Validation failed for chunk: {e}")
        return None
