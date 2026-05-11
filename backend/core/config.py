import os
from dotenv import load_dotenv

env_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    '.env'
)

load_dotenv(dotenv_path=env_path)

class Settings:
    # Qdrant
    QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
    QDRANT_COLLECTION_NAME = os.getenv(
        "QDRANT_COLLECTION_NAME",
        "products_knowledge_graph_v2"
    )

    QDRANT_URL = os.getenv("QDRANT_URL")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

    # API Keys
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    HF_TOKEN = os.getenv(
        "HF_TOKEN"
    )

settings = Settings()