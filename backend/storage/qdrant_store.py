from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from backend.core.config import settings
import os

# Ensure data directory exists
os.makedirs("./qdrant_data", exist_ok=True)

# Initialize local Qdrant client
client = QdrantClient(path="./qdrant_data")

def init_qdrant():
    collections = client.get_collections().collections
    collection_names = [col.name for col in collections]
    
    # We assume embedding size of 768 for models like sentence-transformers or Gemini if specified
    # Using 768 as a placeholder for standard sentence-transformers
    if settings.QDRANT_COLLECTION_NAME not in collection_names:
        client.create_collection(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )

init_qdrant()

def get_qdrant_client():
    return client
