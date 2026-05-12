import asyncio
from sqlalchemy.orm import Session
from processing.normalization import normalize_product_name
from ingestion.expander import expand_sources
from ingestion.scrapers import scrape_url
from processing.deduplication import store_document
from storage.database import Product, IngestionState
from processing.validators import validate_and_normalize_chunk
# Use a lightweight heuristic for sentiment to avoid Out of Memory (OOM) 
# and remove heavy PyTorch/transformers dependencies on Render's 512MB tier.
def get_sentiment(text: str) -> dict:
    text_lower = text.lower()
    negative_words = ["bad", "terrible", "worst", "hate", "slow", "lag", "drain", "issue", "problem", "heat", "warm", "poor", "awful", "bug", "glitch", "crash", "overheat"]
    positive_words = ["good", "great", "best", "love", "fast", "smooth", "excellent", "amazing", "awesome", "perfect", "solid", "impressive", "brilliant"]
    
    neg_count = sum(1 for w in negative_words if w in text_lower)
    pos_count = sum(1 for w in positive_words if w in text_lower)
    
    if neg_count > pos_count:
        return {"label": "NEGATIVE", "score": 0.8 + (neg_count * 0.05)}
    elif pos_count > neg_count:
        return {"label": "POSITIVE", "score": 0.8 + (pos_count * 0.05)}
    return {"label": "NEUTRAL", "score": 0.5}

def classify_taxonomy(text: str) -> list[str]:
    """Simple heuristic-based taxonomy classification for prototype."""
    text_lower = text.lower()
    tags = []
    if any(w in text_lower for w in ["battery", "charge", "drain"]):
        tags.append("battery_issue")
    if any(w in text_lower for w in ["camera", "photo", "lens", "video"]):
        tags.append("camera_issue")
    if any(w in text_lower for w in ["game", "gaming", "lag", "fps", "heating", "warm"]):
        tags.append("gaming_feedback")
    if any(w in text_lower for w in ["network", "signal", "wifi", "5g", "drop"]):
        tags.append("network_issue")
    return tags

async def process_source(url: str, source_type: str, product_id: str, canonical_name: str, brand: str, model_number: str, db: Session):
    print(f"Processing {source_type} at {url}")
    state = IngestionState(product_id=product_id, source_url=url, source_type=source_type, status="scraping")
    db.add(state)
    db.commit()
    db.refresh(state)

    try:
        raw_chunks = await scrape_url(url, source_type)
        
        for chunk in raw_chunks:
            metadata = {
                "product_id": product_id,
                "canonical_name": canonical_name,
                "brand": brand,
                "model_number": model_number,
                "category": "smartphone",
                "source": source_type,
                "doc_type": "spec" if source_type == "spec" else "review",
                "source_url": url,
                "taxonomy": classify_taxonomy(chunk)
            }
            
            # Run sentiment only on reviews, not specs
            if source_type != "spec":
                try:
                    sentiment = get_sentiment(chunk[:512])
                    metadata["sentiment"] = sentiment["label"].upper()
                    metadata["sentiment_score"] = sentiment["score"]
                except Exception as e:
                    print(f"Sentiment error: {e}")
            else:
                metadata["sentiment"] = "NEUTRAL"
                
            payload = validate_and_normalize_chunk(chunk, metadata)
            if payload:
                store_document(payload)
            
        state.status = "completed"
        db.commit()
    except Exception as e:
        state.status = "failed"
        state.error_message = str(e)
        db.commit()

async def run_ingestion_pipeline_async(product_query: str, db: Session):
    print(f"Starting ingestion pipeline for: {product_query}")
    
    try:
        canonical_info = normalize_product_name(product_query)
    except ValueError as e:
        print(f"[Pipeline] Skipping invalid query: {e}")
        return  # ← silent exit, no crash, no ASGI exception
    
    product_id = canonical_info["id"]
    
    # Save/update product in DB
    existing_product = db.query(Product).filter(Product.id == product_id).first()
    if not existing_product:
        new_product = Product(
            id=product_id,
            canonical_name=canonical_info["canonical_name"],
            brand=canonical_info["brand"],
            model=canonical_info["model"],
            variant=canonical_info["variant"]
        )
        db.add(new_product)
        db.commit()
    
    # 2. Source Expansion
    sources = expand_sources(canonical_info["canonical_name"], canonical_info.get("model_number", ""))
    
    # 3. Scraping & Processing concurrently
    tasks = []
    for source_type, url in sources.items():
        if url:
            tasks.append(process_source(url, source_type, product_id, canonical_info["canonical_name"], canonical_info["brand"], canonical_info["model_number"], db))
            
    await asyncio.gather(*tasks)
    print(f"Finished pipeline for {product_query}")

def run_ingestion_pipeline(product_query: str, db: Session):
    # Workaround: BackgroundTasks runs in the event loop, so we shouldn't use asyncio.run inside an async context.
    # Actually, FastAPI BackgroundTasks runs sync functions in a threadpool and async functions in the event loop.
    # Since run_ingestion_pipeline was added as a sync function in routes.py, we can use an event loop or change routes.py to add the async function directly.
    # It's better to update routes.py to add `run_ingestion_pipeline_async` directly or handle loop here.
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    if loop.is_running():
        # Create task in existing loop
        loop.create_task(run_ingestion_pipeline_async(product_query, db))
    else:
        loop.run_until_complete(run_ingestion_pipeline_async(product_query, db))

async def process_structured_reviews(product_query: str, platform: str, url: str, reviews: list, db: Session):
    print(f"Processing {len(reviews)} structured reviews from {platform} for: {product_query}")
    
    # 1. Normalization
    canonical_info = normalize_product_name(product_query)
    product_id = canonical_info["id"]
    
    # Save/update product in DB
    existing_product = db.query(Product).filter(Product.id == product_id).first()
    if not existing_product:
        new_product = Product(
            id=product_id,
            canonical_name=canonical_info["canonical_name"],
            brand=canonical_info["brand"],
            model=canonical_info["model"],
            variant=canonical_info["variant"]
        )
        db.add(new_product)
        db.commit()

    for r in reviews:
        chunk = r.get("text", "")
        if not chunk: continue
        
        metadata = {
            "product_id": product_id,
            "canonical_name": canonical_info["canonical_name"],
            "brand": canonical_info["brand"],
            "model_number": canonical_info["model_number"],
            "category": "smartphone",
            "source": platform,
            "doc_type": "review",
            "source_url": url,
            "taxonomy": classify_taxonomy(chunk),
            "rating": r.get("rating"),
            "author": r.get("author"),
            "date": r.get("date"),
            "verified": r.get("verified"),
            "helpful_votes": r.get("helpful_votes")
        }
        
        try:
            sentiment = get_sentiment(chunk[:512])
            metadata["sentiment"] = sentiment["label"].upper()
            metadata["sentiment_score"] = sentiment["score"]
        except Exception:
            metadata["sentiment"] = "NEUTRAL"
            
        payload = validate_and_normalize_chunk(chunk, metadata)
        if payload:
            store_document(payload)
    
    print(f"Finished structured ingestion for {product_query}")
