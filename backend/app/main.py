from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.api.v1.endpoints.chat import router as chat_router
from app.api.v1.endpoints.auth import router as auth_router


BASE_DIR = Path(__file__).resolve().parent


app = FastAPI(
    title="AI Production Assistant",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ai-production-assistant",
    }


@app.get("/")
def home():
    return FileResponse(
        BASE_DIR / "static" / "index.html"
    )

app.include_router(
    auth_router,
    prefix="/api/v1",
)

app.include_router(
    chat_router,
    prefix="/api/v1",
)