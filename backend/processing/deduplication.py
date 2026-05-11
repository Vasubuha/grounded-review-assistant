from storage.qdrant_store import get_qdrant_client
from core.config import settings
from langchain_huggingface import HuggingFaceEmbeddings
import uuid
import warnings

# Suppress some transformers warnings
warnings.filterwarnings("ignore")

embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def is_duplicate(vector: list[float], product_id: str, threshold: float = 0.98) -> bool:
    """
    Checks if a semantically similar review already exists for this product.
    """
    client = get_qdrant_client()
    
    # Search Qdrant for similar vectors with the same product_id
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    
    search_response = client.query_points(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        query=vector,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="product_id",
                    match=MatchValue(value=product_id)
                )
            ]
        ),
        limit=1,
        score_threshold=threshold
    )
    
    return len(search_response.points) > 0

def store_document(payload) -> bool:
    """
    Stores a document in Qdrant if it's not a duplicate.
    """
    from backend.schemas import DocumentPayload
    from backend.observability.logger import log_duplicate_suppressed
    
    if not isinstance(payload, DocumentPayload):
        print("Invalid payload.")
        return False
        
    client = get_qdrant_client()
    vector = embeddings_model.embed_query(payload.text)
    
    if is_duplicate(vector, payload.product_id):
        print("Duplicate review found, skipping.")
        log_duplicate_suppressed(payload.product_id, payload.text)
        return False

    from qdrant_client.models import PointStruct
    client.upsert(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        points=[
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload=payload.model_dump()
            )
        ]
    )
    print(f"Stored new document for product {payload.product_id}")
    return True
