"""
FastAPI entry point.

Run with:
    uvicorn main:app --reload
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
import sys

import uvicorn

sys.path.append(str(Path(__file__).resolve().parent))

from app.cognee_patches import apply_patches
apply_patches()

from config import config
from cognee_ops import improve, forget, recall, remember
from app.routers import auth as auth_router
from app.routers import memory as memory_router
from app.routers import tutoring as tutoring_router
from app.routers import dashboard as dashboard_router
from app.routers import timeline as timeline_router
from app.routers import status as status_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate env on startup — crash early if API key is missing
    config.validate()
    print(f"[startup] LLM provider: {config.LLM_PROVIDER} / {config.LLM_MODEL}")
    print(f"[startup] CORS allowed origins: {_cors_origins}")
    yield

app = FastAPI(
    title="Never Lose the Plot",
    description="AI tutor that never forgets. Powered by Cognee.",
    version="0.1.0",
    lifespan=lifespan,
)

_cors_origins = [
    origin.strip()
    for origin in os.environ.get(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router, prefix="/api/auth", tags=["auth"])
app.include_router(memory_router.router, prefix="/api/memory", tags=["memory"])
app.include_router(tutoring_router.router, prefix="/api/tutoring", tags=["tutoring"])
app.include_router(dashboard_router.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(timeline_router.router, prefix="/api/timeline", tags=["timeline"])
app.include_router(status_router.router, prefix="/api/status", tags=["status"])


@app.get("/health")
def health():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "Never Lose the Plot",
    }


__all__ = ["app", "remember", "recall", "improve", "forget"]


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
        reload=os.environ.get("ENV", "development") == "development",
    )