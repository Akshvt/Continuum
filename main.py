"""
FastAPI entry point.

Day 1 goal: server starts, health check works,
one real /api/memory/remember endpoint is live.

Run with:
    uvicorn main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
import sys

import uvicorn

sys.path.append(str(Path(__file__).resolve().parent))

from config import config
from app.cognee_ops import improve, forget, recall, remember
from app.routers import memory as memory_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate env on startup — crash early if API key is missing
    config.validate()
    print(f"[startup] LLM provider: {config.LLM_PROVIDER} / {config.LLM_MODEL}")
    yield


app = FastAPI(
    title="Never Lose the Plot",
    description="AI tutor that never forgets. Powered by Cognee.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten this if you add auth later
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(memory_router.router, prefix="/api/memory", tags=["memory"])


@app.get("/health")
def health():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "Never Lose the Plot",
    }


__all__ = ["app", "remember", "recall", "improve", "forget"]


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)