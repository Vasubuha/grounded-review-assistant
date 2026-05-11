from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.storage.database import get_db
from backend.storage.qdrant_store import get_qdrant_client
from backend.core.config import settings
from backend.processing.deduplication import embeddings_model

router = APIRouter()

class IngestRequest(BaseModel):
    product_query: str

class QueryRequest(BaseModel):
    query: str
    product_id: str = Field(None, description="Optional product ID to filter by")

@router.post("/ingest")
async def ingest_product(request: IngestRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if not request.product_query:
        raise HTTPException(status_code=400, detail="Product query cannot be empty")
    
    # Import here to avoid circular imports during setup
    from backend.ingestion.pipeline import run_ingestion_pipeline
    
    # Add the ingestion process to background tasks
    background_tasks.add_task(run_ingestion_pipeline, request.product_query, db)
    
    return {"message": "Ingestion process started", "product_query": request.product_query}

class ExtensionReviewRequest(BaseModel):
    product_query: str
    platform: str
    url: str
    reviews: list

@router.post("/ingest/reviews")
async def ingest_reviews_from_extension(request: ExtensionReviewRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if not request.product_query or not request.reviews:
        raise HTTPException(status_code=400, detail="Product query and reviews cannot be empty")
        
    from backend.ingestion.pipeline import process_structured_reviews
    
    # Run structured review ingestion in background
    background_tasks.add_task(
        process_structured_reviews, 
        request.product_query, 
        request.platform, 
        request.url, 
        request.reviews, 
        db
    )
    
    return {"message": f"Queued {len(request.reviews)} reviews for ingestion"}

@router.post("/query")
async def query_knowledge_graph(request: QueryRequest):
    if not request.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    client = get_qdrant_client()
    query_vector = embeddings_model.embed_query(request.query)
    
    # Intent-aware weighting
    query_lower = request.query.lower()
    is_issue_query = any(w in query_lower for w in ["issue", "problem", "bad", "worst", "heating", "lag", "drain"])
    
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    
    query_filter = None
    if request.product_id:
        if len(request.product_id) != 64:
            from backend.processing.normalization import normalize_product_name
            request.product_id = normalize_product_name(request.product_id)["id"]
        must_conditions = [FieldCondition(key="product_id", match=MatchValue(value=request.product_id))]
        query_filter = Filter(must=must_conditions)
    
    search_response = client.query_points(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        query=query_vector,
        query_filter=query_filter,
        limit=5
    )
    search_result = search_response.points
    
    results = [
        {
            "score": res.score,
            "text": res.payload.get("text"),
            "source_type": res.payload.get("source_type"),
            "sentiment": res.payload.get("sentiment"),
            "taxonomy": res.payload.get("taxonomy"),
            "rating": res.payload.get("rating"),
            "author": res.payload.get("author"),
            "date": res.payload.get("date"),
            "verified": res.payload.get("verified"),
            "helpful_votes": res.payload.get("helpful_votes")
        }
        for res in search_result
    ]
    
    return {"query": request.query, "is_issue_query": is_issue_query, "results": results}

class ChatRequest(BaseModel):
    query: str
    product_id: str = Field(None, description="Optional product ID to filter by")

@router.post("/chat")
async def generate_chat(request: ChatRequest):
    if not request.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    # If a raw product name was passed instead of the SHA256 hash, convert it
    if request.product_id and len(request.product_id) != 64:
        from backend.processing.normalization import normalize_product_name
        request.product_id = normalize_product_name(request.product_id)["id"]
        
    from backend.retrieval.chat import generate_chat_response
    
    # Generate synchronous chat response
    response_data = generate_chat_response(request.query, request.product_id)
    
    return response_data

@router.get("/diagnostics")
async def get_diagnostics(limit: int = 50):
    from backend.observability.logger import diagnostic_logger
    return {"logs": diagnostic_logger.get_logs(limit)}
