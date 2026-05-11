from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import routes
from backend.storage.database import init_db

app = FastAPI(title="RAG Data Pipeline API", version="1.0.0")

# Setup CORS to allow Chrome extension to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"], 
    allow_origin_regex=r"chrome-extension://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(routes.router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
