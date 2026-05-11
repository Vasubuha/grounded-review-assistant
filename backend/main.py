from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import routes
from storage.database import init_db
import os

print("Application starting...")
print("PORT:", os.getenv("PORT"))

app = FastAPI(title="RAG Data Pipeline API", version="1.0.0")

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
    try:
        init_db()
        print("Database initialized")
    except Exception as e:
        print(f"Startup error: {e}")

app.include_router(routes.router, prefix="/api/v1")

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "rag-pipeline-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)