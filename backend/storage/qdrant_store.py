from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from core.config import settings

def get_qdrant_client():
    return QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
    )

def init_qdrant():
    client = get_qdrant_client()

    collections = client.get_collections().collections
    collection_names = [col.name for col in collections]

    if settings.QDRANT_COLLECTION_NAME not in collection_names:
        client.create_collection(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            vectors_config=VectorParams(
                size=384,
                distance=Distance.COSINE,
            ),
        )

    # Always ensure the index exists (this operation is idempotent in Qdrant)
    from qdrant_client.models import PayloadSchemaType
    client.create_payload_index(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        field_name="product_id",
        field_schema=PayloadSchemaType.KEYWORD,
    )