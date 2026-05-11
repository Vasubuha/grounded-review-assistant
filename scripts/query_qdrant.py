import os
from dotenv import load_dotenv
load_dotenv('backend/.env')
from backend.services.qdrant_store import get_qdrant_client
from backend.core.config import settings

client = get_qdrant_client()
points, _ = client.scroll(collection_name=settings.QDRANT_COLLECTION_NAME, limit=200, with_payload=True)

for p in points:
    url = p.payload.get('source_url', '')
    if url and 'gsmarena' in url:
        print(f"Product ID: {p.payload.get('product_id')}")
        print(f"URL: {url}")
        print(f"Text: {p.payload.get('text')[:100]}")
        print("---")
