from sqlalchemy import create_engine, Column, String, Integer, DateTime, JSON, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

DATABASE_URL = "sqlite:///./rag_pipeline.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    
    id = Column(String, primary_key=True, index=True) # sha256 hash
    canonical_name = Column(String, index=True)
    brand = Column(String)
    model = Column(String)
    variant = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class IngestionState(Base):
    __tablename__ = "ingestion_state"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, index=True)
    source_url = Column(String)
    source_type = Column(String) # amazon, flipkart, youtube, spec
    status = Column(String) # pending, scraping, completed, failed
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    last_attempt = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
