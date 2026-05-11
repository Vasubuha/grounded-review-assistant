# Chrome Extension Side Panel - Setup & Deployment Guide

## Overview

This guide converts the RAG Product Ingestor extension into a **fully integrated side-panel assistant** that:
- 🔍 Auto-detects smartphone products on Amazon and Flipkart
- ⚡ Instantly opens a persistent side panel in the browser
- 💬 Provides RAG-based chat without leaving the product page
- 🎯 Auto-ingests product data in the background
- 📊 Displays retrieved sources, reviews, and insights

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Shopping Tab (Amazon/Flipkart)               │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  [Product Page]              │  [Chrome Side Panel]              │
│                              │                                   │
│                              │  ┌─────────────────────────────┐  │
│                              │  │   RAG Assistant Panel       │  │
│                              │  │  ┌─────────────────────────┐ │  │
│  Content Script             │  │  │ Product Name: [Auto]    │ │  │
│  ↓                          │  │  │ Status: [Ingesting...] │ │  │
│  Extracts Product Name      │  │  └─────────────────────────┘ │  │
│  Sends to Background ──────────→ Background Service Worker    │  │
│                              │  │                             │  │
│                              │  │  ┌─────────────────────────┐ │  │
│                              │  │  │  Chat Area              │ │  │
│                              │  │  │  ┌─────────────────────┐ │ │  │
│                              │  │  │  │ Retrieved Response  │ │ │  │
│                              │  │  │  │ Sources & Reviews   │ │ │  │
│                              │  │  │  └─────────────────────┘ │ │  │
│                              │  │  │  ┌─────────────────────┐ │ │  │
│                              │  │  │  │ Input: Ask...       │ │ │  │
│                              │  │  │  └─────────────────────┘ │ │  │
│                              │  │                             │  │
│                              │  └─────────────────────────────┘  │
│                              │                                   │
└─────────────────────────────────────────────────────────────────┘
                                    ↓
                        FastAPI Backend (localhost:8000)
                        - /api/v1/ingest
                        - /api/v1/chat
                        - /api/v1/query
```

## Prerequisites

### System Requirements
- **Chrome/Chromium** browser (v120+)
- **Node.js** (v18+) for frontend build
- **Python** (v3.10+) for backend
- **Qdrant** vector database (running on localhost:6333)

### Environment Setup
```bash
# Backend
cd d:\langchain_model
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

## Setup Steps

### 1. Ensure Backend is Running

```bash
# From the backend directory
cd d:\langchain_model

# Activate Python environment
venv\Scripts\activate

# Start FastAPI server
python -m backend.main
```

The backend should start on `http://localhost:8000`

Check the API: `curl http://localhost:8000/api/v1/ingest`

### 2. Build/Run Frontend

#### Development Mode (with hot reload)
```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:5173`

#### Production Build
```bash
cd frontend
npm run build
```

### 3. Load the Extension in Chrome

1. **Open Chrome** and go to `chrome://extensions/`
2. Enable **Developer mode** (toggle in top right)
3. Click **Load unpacked**
4. Navigate to and select: `d:\langchain_model\extension`
5. ✅ Extension loaded!

### 4. Test the Extension

#### Test Auto-Detection & Side Panel

1. **Open Amazon or Flipkart** in a new tab
   - Example: `https://www.amazon.in/s?k=realme+phone`
   - Or any product page: `https://www.flipkart.com/realme-12-pro/...`

2. **Product Detection** should trigger automatically:
   - Content script extracts product name from page
   - Sends to background script
   - Background script auto-ingests product data
   - Side panel opens automatically on the right side

3. **Side Panel appears** with:
   - Product name displayed at the top
   - Status badge showing ingestion progress
   - Chat input ready to accept queries

4. **Query the Product**:
   - Enter: "What are the pros and cons of this phone?"
   - Or: "Tell me about battery performance"
   - Watch as the RAG pipeline retrieves information and generates an answer

#### Manual Ingestion (Popup)

If auto-detection doesn't trigger:
1. Click the extension icon (top right of browser)
2. A popup appears with the detected product name
3. Click "Ingest Product"
4. Status shows: "Ingestion started successfully!"
5. Side panel opens automatically

## Configuration

### Backend URL

The extension uses `http://localhost:8000` as the default backend. To change:

**In `background.js`:**
```javascript
const BACKEND_URL = 'http://localhost:8000';
```

**In `side-panel.js`:**
```javascript
const BACKEND_URL = 'http://localhost:8000';
```

**In React `chatService.ts`:**
```typescript
const res = await fetch('http://127.0.0.1:8000/api/v1/chat', ...);
```

### Frontend URL

The side panel iframe loads the frontend from `http://localhost:5173`. To change:

**In `side-panel.js`:**
```javascript
iframe.src = 'http://localhost:5173'; // Change this
```

### Add/Remove Shopping Sites

To add more e-commerce platforms, edit:

**`manifest.json`** - Add to `host_permissions`:
```json
"host_permissions": [
  "https://*.mynewsite.com/*",
  ...
]
```

**`manifest.json`** - Add to `content_scripts[0].matches`:
```json
"matches": [
  "https://*.mynewsite.com/*",
  ...
]
```

**`content.js`** - Add detection function:
```javascript
function extractMyNewSiteProduct() {
  // CSS selectors for product title
  const selectors = ['h1.title', 'span.product-name'];
  for (const selector of selectors) {
    const element = document.querySelector(selector);
    if (element?.textContent?.trim()) {
      return element.textContent.trim();
    }
  }
  return null;
}
```

Then update `extractProductInfo()` to check for your site.

## Extension Files & Their Roles

| File | Purpose |
|------|---------|
| **manifest.json** | Extension configuration, permissions, side panel declaration |
| **background.js** | Service worker - monitors tabs, auto-ingests, routes messages |
| **content.js** | Injects on shopping pages - extracts product info, sends to background |
| **side-panel.html** | UI shell for the side panel with header and iframe container |
| **side-panel.js** | Manages side panel state, loads React app in iframe, handles IPC |
| **popup.html / popup.js** | Traditional popup for manual ingestion (fallback) |

## Message Flow

### Auto-Detection Flow
```
1. User navigates to Amazon/Flipkart
   ↓
2. Content script (content.js) extracts product name via DOM selectors
   ↓
3. Content script sends: chrome.runtime.sendMessage({
      type: 'PRODUCT_DETECTED_FROM_PAGE',
      productName: 'Realme 12 Pro',
      platform: 'amazon',
      url: 'https://...'
   })
   ↓
4. Background script (background.js) receives message
   ↓
5. Background calls: autoIngestProduct(productName)
   ↓
6. POST to http://localhost:8000/api/v1/ingest
   ↓
7. Ingestion runs in background on FastAPI
   ↓
8. Background opens side panel via: chrome.sidePanel.open()
   ↓
9. Side panel loads React app in iframe
   ↓
10. React app receives product name via postMessage
```

### Chat Flow
```
1. User types query and clicks Send in React app
   ↓
2. React calls: sendChatQuery(query, productId)
   ↓
3. Fetches: POST http://localhost:8000/api/v1/chat
   ↓
4. Backend returns RAG response with:
   - answer: LLM-generated response
   - retrieved_chunks: Context from vector DB
   - sources_used: URLs of retrieved documents
   - intent: Detected query intent
   - confidence_score: Confidence of classification
   ↓
5. React displays response with sources and chunks
   ↓
6. If in side panel (iframe), response sent to side-panel.js
```

## Troubleshooting

### Side Panel Not Opening

**Issue**: Side panel doesn't appear after product detection

**Solutions**:
1. Check Chrome version: `chrome://version/` - must be v120+
2. Verify manifest.json has `"sidePanel"` entry
3. Check console for errors: `chrome://extensions/` → Select extension → Details → Inspect views → service worker
4. Reload extension: Toggle off/on

### Product Not Detected

**Issue**: Extension doesn't extract product name

**Solutions**:
1. Check content script is running:
   - Right-click page → Inspect → Console
   - Should see: `[Content script] Product detected`
2. Verify CSS selectors in `content.js` match the page
   - For Amazon: right-click product title → Inspect
   - Look for `h1 span.a-size-large` or `span#productTitle`
3. Try manual ingestion via popup
4. Check background script logs: `chrome://extensions/` → Select extension → Inspect views → service worker

### Backend Connection Failed

**Issue**: "Communication with the backend failed"

**Solutions**:
1. Verify backend is running: `curl http://localhost:8000/api/v1/chat`
2. Check backend URL in:
   - `side-panel.js` line ~4
   - `background.js` line ~3
   - React `chatService.ts` line ~20
3. Ensure FastAPI server is on `localhost:8000`
4. Check Windows Firewall: allow port 8000
5. Verify Qdrant is running (required by backend)

### Product Ingestion Stuck

**Issue**: Ingestion shows "Ingesting..." but never completes

**Solutions**:
1. Check backend ingestion pipeline: `backend/services/pipeline.py`
2. Verify Qdrant collection exists and is accessible
3. Check backend console for errors
4. Restart backend service
5. Check storage: `chrome://extensions/` → Select extension → Manage extension storage

### Chat Not Responding

**Issue**: Chat returns "Communication with the backend failed" or "insufficient product data"

**Solutions**:
1. Verify product was ingested:
   - Backend console should show ingestion logs
   - Qdrant should have vectors for product
2. Try different query: "Tell me about this phone"
3. Check backend `/api/v1/chat` endpoint
4. Verify product_id is being sent correctly
5. Restart backend and try again

## Development Workflow

### Local Testing

1. **Terminal 1 - Backend**:
   ```bash
   cd d:\langchain_model
   venv\Scripts\activate
   python -m backend.main
   ```

2. **Terminal 2 - Frontend Dev Server**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Chrome Extensions**:
   - Go to `chrome://extensions/`
   - Enable Developer mode
   - Load unpacked → select `extension` folder
   - Keep console open: `chrome://extensions/` → Extensions → Inspect views → service worker

4. **Open Shopping Site**:
   - Amazon, Flipkart, or localhost:5173 directly
   - Product should auto-detect
   - Side panel opens
   - Chat becomes available

### Making Changes

**Extension Changes**:
1. Edit `extension/*.js` or `.html`
2. Go to `chrome://extensions/`
3. Click **Reload** button for the extension
4. Refresh the shopping tab

**Frontend Changes**:
1. Edit `frontend/src/**`
2. Frontend auto-reloads at localhost:5173
3. Refresh side panel to see changes

**Backend Changes**:
1. Edit `backend/**`
2. Restart the backend server
3. Try chat query again

## Production Deployment

### Building Extension for Distribution

```bash
# Create release package
mkdir dist
cd extension
# Manually create .zip with all extension files
```

### Creating Chrome Web Store Package

1. Build extension as .zip
2. Go to [Chrome Web Store Developer Dashboard](https://chromewebstore.google.com/publish)
3. Upload .zip
4. Fill in store listing details
5. Submit for review

### Deploying Backend

For production, use:
- Gunicorn/Uvicorn for ASGI server
- Nginx as reverse proxy
- Environment variables for configuration
- SSL/TLS for HTTPS
- Docker for containerization

See `backend/main.py` for production configurations.

## API Reference

### Ingest Endpoint

```bash
POST http://localhost:8000/api/v1/ingest
Content-Type: application/json

{
  "product_query": "Realme 12 Pro"
}

Response:
{
  "message": "Ingestion process started",
  "product_query": "Realme 12 Pro"
}
```

### Chat Endpoint

```bash
POST http://localhost:8000/api/v1/chat
Content-Type: application/json

{
  "query": "What are the specs?",
  "product_id": "Realme 12 Pro"
}

Response:
{
  "answer": "The Realme 12 Pro features...",
  "retrieved_chunks": [
    {
      "text": "12GB RAM, 256GB storage",
      "source": "https://amazon.in/...",
      "sentiment": "positive",
      "score": 0.89
    }
  ],
  "sources_used": ["https://amazon.in/...", "https://flipkart.com/..."],
  "intent": "specification",
  "confidence_score": 0.95
}
```

### Query Endpoint

```bash
POST http://localhost:8000/api/v1/query
Content-Type: application/json

{
  "query": "battery performance",
  "product_id": "Realme 12 Pro"
}

Response:
{
  "query": "battery performance",
  "is_issue_query": false,
  "results": [
    {
      "score": 0.87,
      "text": "Battery lasts 2 days...",
      "source_type": "review",
      "sentiment": "positive"
    }
  ]
}
```

## Performance Optimization

### Frontend Optimization
- Side panel iframe runs at 60fps
- Chat responses cached in memory
- Product detection debounced to avoid duplicate ingestions
- CSS animations optimized with GPU acceleration

### Backend Optimization
- Qdrant vector searches use HNSW indexing
- Background ingestion prevents blocking chat
- Embeddings cached across requests
- Intent classification uses lightweight model

### Network Optimization
- Messages batched when possible
- Service worker caches Chrome storage data
- Side panel uses single iframe (vs. multiple windows)

## Security Considerations

1. **Content Script Isolation**:
   - Content scripts run in isolated context
   - Cannot access sensitive data outside shopping pages
   - DOM-based detection only

2. **Message Passing Security**:
   - Background script validates message types
   - Popup and side panel restricted to extension context
   - No untrusted external messages processed

3. **Data Privacy**:
   - Product data sent only to localhost backend
   - No external API calls by extension
   - Chrome storage used for temporary state only
   - Product ingestion runs locally

4. **Backend Security** (setup separately):
   - Use HTTPS in production
   - Implement authentication for API endpoints
   - Validate all inputs on backend
   - Use rate limiting to prevent abuse

## Next Steps

1. ✅ Load extension in Chrome
2. ✅ Open Amazon/Flipkart product page
3. ✅ Wait for auto-detection and side panel
4. ✅ Enter query in chat
5. 🎉 Get AI-powered product insights instantly!

---

**Questions or issues?** Check the troubleshooting section above or inspect the background service worker console.
