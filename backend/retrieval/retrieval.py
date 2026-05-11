from storage.qdrant_store import get_qdrant_client
from processing.deduplication import embeddings_model
from core.config import settings
from qdrant_client.models import Filter, FieldCondition, MatchValue
# CrossEncoder removed to prevent Out of Memory (OOM) errors on 512MB Render instances.
# We will use Qdrant's native vector similarity score instead.

def classify_intent(query: str) -> str:
    """Lightweight intent classifier based on keywords."""
    query_lower = query.lower()
    issue_keywords = ["issue", "problem", "bad", "worst", "heating", "lag", "drain", "battery", "slow", "bug", "terrible"]
    spec_keywords = ["spec", "specifications", "processor", "ram", "display", "screen", "weight", "dimensions", "charger"]
    
    if any(w in query_lower for w in issue_keywords):
        return "issue"
    elif any(w in query_lower for w in spec_keywords):
        return "spec"
    return "general"

def retrieve_context(query: str, product_id: str = None, top_k: int = 5) -> dict:
    """
    Retrieves and reranks context from Qdrant based on intent.
    Returns structured retrieved chunks and metadata.
    """
    client = get_qdrant_client()
    query_vector = embeddings_model.embed_query(query)
    intent = classify_intent(query)
    
    # 1. Build Filter
    must_conditions = [
    FieldCondition(
        key="product_id",
        match=MatchValue(value=product_id)
    ),
    FieldCondition(
        key="category",
        match=MatchValue(value="smartphone")
    )
]
        
    # We retrieve a larger pool (e.g., 50) and then rerank
    pool_size = 50
    
    search_response = client.query_points(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        query=query_vector,
        query_filter=Filter(must=must_conditions) if must_conditions else None,
        limit=pool_size
    )
    search_result = search_response.points
    
    if not search_result:
        return {
            "chunks": [],
            "intent": intent,
            "message": "insufficient product data available"
        }
        
    # Combine results with scores and apply intent-based heuristics
    reranked_results = []
    for idx, res in enumerate(search_result):
        score = res.score
        payload = res.payload
        
        # Intent-based boosting
        if intent == "issue" and payload.get("sentiment") == "NEGATIVE":
            score += 0.2  # Boost negative reviews for issue queries (scaled for vector score)
        elif intent == "spec" and payload.get("doc_type") == "spec":
            score += 0.2  # Boost specs for spec queries (scaled for vector score)
            
        reranked_results.append({
            "text": payload.get("text", ""),
            "source": payload.get("source", "unknown"),
            "sentiment": payload.get("sentiment", "NEUTRAL"),
            "source_url": payload.get("source_url", ""),
            "cross_score": float(score),
            "vector_score": float(res.score)
        })
        
    # Sort descending by cross_score
    reranked_results.sort(key=lambda x: x["cross_score"], reverse=True)
    
    # Take top_k
    final_chunks = reranked_results[:top_k]
    
    from observability.logger import log_retrieval
    log_retrieval(query, final_chunks)
    
    # Debug Logging
    print(f"--- Retrieval Inspection ---")
    print(f"Intent: {intent}")
    print(f"Top chunks:")
    for i, c in enumerate(final_chunks):
        print(f"  {i+1}. [Score: {c['cross_score']:.2f} | Source: {c['source']}] TEXT_REDACTED")
    print(f"----------------------------")
    
    return {
        "chunks": final_chunks,
        "intent": intent,
        "message": "success",
        "sources_used": list(set([c["source_url"] for c in final_chunks if c["source_url"]]))
    }
