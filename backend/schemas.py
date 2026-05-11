from pydantic import BaseModel
from typing import Optional, List

class DocumentPayload(BaseModel):
    product_id: str
    canonical_name: str
    category: str
    source: str
    doc_type: str
    sentiment: str
    text_hash: str
    text: str
    source_url: Optional[str] = None
    sentiment_score: Optional[float] = None
    taxonomy: Optional[List[str]] = None
    rating: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None
    verified: Optional[bool] = None
    helpful_votes: Optional[str] = None
