# RAG Data Pipeline Upgrade Walkthrough

We have successfully rebuilt the RAG data pipeline from a synchronous Jupyter Notebook script into a robust, asynchronous API architecture that fulfills all the stated requirements.

## 1. Minimal Chrome Extension
A lightweight Chrome Extension is located in the `extension/` folder. It simply reads the title of the current active tab and exposes a UI popup with an "Ingest Product" button. When clicked, it sends a REST `POST` request to the backend.

## 2. FastAPI Backend & Database
The backend is powered by **FastAPI** (`backend/main.py`), running on Uvicorn. 
It uses `BackgroundTasks` to immediately acknowledge the ingestion request from the extension and spawn the scraping pipeline asynchronously in the background.

State management is handled via **SQLite** (`backend/database.py`):
- `products`: Tracks the canonical product name, brand, model, variant, and stable SHA256 IDs.
- `ingestion_state`: Tracks each individual URL's ingestion progress (pending, scraping, completed, failed) for robust retry and failure handling.

## 3. Normalization & Autonomous Source Expansion
- **Normalization Layer** (`backend/services/normalization.py`): Uses the **Groq LLM** (`llama-3.3-70b-versatile`) with Structured Output to reliably extract Brand, Model, and Variant from noisy strings like "Vivo Y56 5G - Amazon.in". It generates a stable `product_id` using `hashlib.sha256()`.
- **Expander Layer** (`backend/services/expander.py`): Uses the `ddgs` library to autonomously discover missing source URLs for Amazon, Flipkart, YouTube, and tech spec sites based purely on the canonical name.

## 4. Asynchronous Scraping & Cleaning
- **Scrapers** (`backend/services/scrapers.py`): Provide asynchronous fetching logic with built-in retries (`scrape_url`). YouTube transcripts are automatically pulled and chunked using the object-oriented API format.
- **Cleaning & Taxonomy** (`backend/services/pipeline.py`): 
  - Automatically discards junk fragments (e.g., "sign in", "privacy notice").
  - Each review is split and chunked independently.
  - Applies a fine-grained taxonomy classification (`battery_issue`, `camera_issue`, `gaming_feedback`, `network_issue`).
  - Sentiment Analysis is only applied to user reviews (skipped for technical specs).

## 5. Semantic Deduplication & Qdrant Integration
- **Deduplication** (`backend/services/deduplication.py`): We use `sentence-transformers` via `HuggingFaceEmbeddings` to compute vector similarity. If a similar review already exists for the specific `product_id` in Qdrant (score > 0.95), it is skipped.
- **Qdrant Storage** (`backend/services/qdrant_store.py`): Serves as the continuous knowledge graph vector database. The collection explicitly utilizes `size=384` to match the `all-MiniLM-L6-v2` embeddings, preventing dimension misalignment during retrieval.

## 6. Retrieval & Chat Generation
- **Intent-Aware Retrieval & Reranking** (`backend/services/retrieval.py`): Uses a lightweight intent classifier to categorize queries (`issue`, `spec`, `general`). It queries Qdrant with the auto-hashed `product_id`, then utilizes a `CrossEncoder` (`ms-marco-MiniLM-L-6-v2`) to accurately rerank chunks, deliberately weighting negative reviews heavily if the query intent is "issue".
- **Generation Engine** (`backend/services/chat.py`): Extracts the top 10 reranked chunks and applies aggressive deduplication and semantic sectioning (e.g. `[POSITIVE REVIEWS]`, `[SPECIFICATIONS]`) to prevent context overflow. Synthesizes a response using `ChatGroq`, constrained by a strict system prompt to avoid hallucinations and mandate direct citation.

## 7. React + Vite Debugging UI
- **Frontend Dashboard** (`frontend/src/App.tsx`): A lightweight, modern React application built with Tailwind CSS and Vite.
- **Architecture**: Emphasizes transparency over UX polish. It utilizes local `useState` rather than complex stores, preventing excessive abstraction.
- **Features**: Features a tri-pane layout allowing rapid active product switching, a centralized single-turn chat interaction window, and a dedicated **Retrieval Debug Panel** that visualizes underlying retrieval mechanics (chunk sentiment, origin, confidence scores, and raw content).

### Next Steps to Run Locally
1. **Start the backend**: 
   ```bash
   cd d:/langchain_model && .\venv\Scripts\Activate.ps1 && uvicorn backend.main:app --reload
   ```
2. **Start the frontend**: 
   ```bash
   cd d:/langchain_model/frontend && npm run dev
   ```
3. **Load Chrome Extension**: Load the unpacked extension in Chrome pointing to `d:/langchain_model/extension`.
4. **Environment**: Ensure your API keys (`GROQ_API_KEY`) are loaded in your `.env` file for the Normalizer and Chat LLM.
