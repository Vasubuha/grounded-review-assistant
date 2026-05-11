from dotenv import load_dotenv
import os

from langchain_experimental.text_splitter import SemanticChunker
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

# Gemini embeddings
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=os.getenv("GEMINI_API_KEY")
)



splitter = RecursiveCharacterTextSplitter(
    chunk_size=120,
    chunk_overlap=20
)

# Semantic chunking
text_splitter = SemanticChunker(
    embeddings,
    breakpoint_threshold_type="percentile",
    breakpoint_threshold_amount=80,
    min_chunk_size=20
)

sample = """
Farmers grow crops and prepare soil for cultivation.
Agriculture depends heavily on rainfall and climate.

Virat Kohli is one of the best IPL players.
Cricket is the most popular sport in India.

Artificial intelligence is changing software engineering.
LLMs are widely used in automation and chatbots.

Terrorism creates instability and threatens public safety.
Governments invest heavily in national security.
"""

docs = text_splitter.create_documents([sample])

print(len(docs))

for i, doc in enumerate(docs, 1):
    print(f"\nChunk {i}:")
    print(doc.page_content)