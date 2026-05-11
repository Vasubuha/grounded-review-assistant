# 🚀 Quick Start Guide - Side Panel RAG Assistant

Get the extension running in **5 minutes**!

## Prerequisites Check ✅

```bash
# Check Node.js
node --version  # Should be v18+

# Check Python
python --version  # Should be v3.10+

# Check npm
npm --version  # Should be v9+
```

## Step 1: Start the Backend (1 min)

```bash
cd d:\langchain_model

# Activate Python environment
venv\Scripts\activate

# Start FastAPI server
python -m backend.main
```

✅ Backend should start on `http://localhost:8000`

**Verify:** Open http://localhost:8000/docs in browser - should see FastAPI Swagger UI

---

## Step 2: Start the Frontend (1 min)

**Terminal 2:**
```bash
cd d:\langchain_model\frontend

# Install dependencies (first time only)
npm install

# Start dev server
npm run dev
```

✅ Frontend should be at `http://localhost:5173`

**Verify:** Open http://localhost:5173 in browser - should see chat UI

---

## Step 3: Load Extension in Chrome (2 min)

1. Open Chrome
2. Go to **chrome://extensions/**
3. Toggle **Developer mode** (top right)
4. Click **Load unpacked**
5. Select: `d:\langchain_model\extension`
6. ✅ Extension loaded!

**Verify:** Extension icon appears in Chrome toolbar

---

## Step 4: Test It! (1 min)

1. **Open a new Chrome tab**
2. **Go to Amazon or Flipkart:**
   - Amazon: https://www.amazon.in/s?k=phone
   - Flipkart: https://www.flipkart.com/search?q=phone
3. **Click a product** (any phone listing)
4. 🎉 **Side panel should open automatically on the right!**
5. **Type a question:**
   - "What are the specs?"
   - "Tell me about battery life"
   - "Pros and cons of this phone?"
6. 🤖 **Get instant AI response with sources!**

---

## Troubleshooting

### Side Panel Not Opening?
- [ ] Check Chrome version: `chrome://version/` (must be 120+)
- [ ] Go to `chrome://extensions/` and reload the extension
- [ ] Check background logs: Extensions → Select extension → Inspect views → service worker

### Product Not Detected?
- [ ] Right-click page → Inspect → Console
- [ ] Look for: `[Content script] Product detected`
- [ ] Try Amazon instead of Flipkart (better selector support)
- [ ] Refresh page and try again

### Backend Connection Failed?
- [ ] Verify backend running: `curl http://localhost:8000/docs`
- [ ] Check if FastAPI is on localhost:8000
- [ ] Check firewall isn't blocking port 8000
- [ ] Restart backend: Stop and run again

### No Response from Chat?
- [ ] Make sure product was ingested (check backend logs)
- [ ] Try simpler question: "Tell me about this phone"
- [ ] Restart both backend and refresh browser
- [ ] Check Qdrant is running (backend depends on it)

---

## File Locations Quick Ref

```
d:\langchain_model\
├── extension/              # Chrome extension files ✅
│   ├── manifest.json       # Extension configuration
│   ├── background.js       # Auto-detection logic
│   ├── content.js          # Product extraction
│   ├── side-panel.html     # Side panel UI
│   ├── side-panel.js       # Side panel logic
│   ├── popup.html
│   └── popup.js
├── frontend/               # React app ✅
│   ├── src/
│   │   └── App.tsx        # Updated for side panel
│   ├── package.json
│   └── vite.config.ts
├── backend/                # FastAPI backend ✅
│   ├── main.py
│   └── api/routes.py
├── EXTENSION_SETUP.md      # Full setup guide 📖
├── CHANGES_SUMMARY.md      # What changed 📝
└── requirements.txt        # Python dependencies
```

---

## Architecture Overview

```
Shopping Page
     ↓
[Content Script] Detects product
     ↓
[Background Script] Auto-ingests & opens side panel
     ↓
[Side Panel] Displays React app in iframe
     ↓
[React App] Sends queries to backend
     ↓
[FastAPI] Processes RAG pipeline
     ↓
[Response] Displayed in side panel with sources!
```

---

## Common Commands

```bash
# Kill backend
# Ctrl+C in the terminal

# Reload extension
# Chrome DevTools: Extensions → Select extension → Reload button
# Or press F5 on extensions page

# View logs
# Chrome: chrome://extensions/ → Select extension → Inspect views

# Reset extension storage
chrome://extensions/
Select extension → Details → Manage extension storage → Clear data

# Check Qdrant
curl http://localhost:6333/collections

# Check backend endpoints
curl http://localhost:8000/api/v1/ingest

# Build frontend for production
cd frontend && npm run build
```

---

## What's New?

✨ **Original Features Still Work:**
- Popup ingestion (click extension icon)
- Standalone React app at localhost:5173
- Manual product queries

✨ **NEW Side Panel Features:**
- Auto-detection on Amazon/Flipkart
- Auto-ingestion in background
- Side panel opens automatically
- Chat without leaving product page
- No manual setup needed!

---

## Next: Full Documentation

For detailed setup, troubleshooting, API reference, and production deployment:

👉 See [EXTENSION_SETUP.md](EXTENSION_SETUP.md)

---

## Support

Having issues? 
1. Check console logs: `chrome://extensions/` → Extensions → Inspect service worker
2. Verify all services running:
   - Backend: http://localhost:8000/docs
   - Frontend: http://localhost:5173
   - Qdrant: http://localhost:6333
3. Try reloading extension and refreshing page
4. Check [EXTENSION_SETUP.md](EXTENSION_SETUP.md) troubleshooting section

---

**Enjoy your AI-powered side panel assistant! 🚀**
