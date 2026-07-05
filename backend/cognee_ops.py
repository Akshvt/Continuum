"""
Compatibility wrappers around the installed Cognee package (now migrating to Cognee Cloud).

This module routes all memory operations to the Cognee Cloud REST API.
It entirely bypasses the local `cognee` package and `litellm`, completely eliminating
the massive RAM overhead that causes Render free tier instances to crash.
"""

from __future__ import annotations

import os
import asyncio
import logging
from typing import Any
from uuid import UUID
import httpx
from types import SimpleNamespace

logger = logging.getLogger("continuum.cognee_ops")

# Maximum seconds to wait for short operations (recall, forget)
COGNEE_TIMEOUT_SECONDS: float = 30.0
# Generous timeout for long-running memory generation (cognify)
COGNEE_REMEMBER_TIMEOUT_SECONDS: float = 360.0

def _get_client() -> httpx.AsyncClient:
    """Returns an httpx AsyncClient configured for Cognee Cloud."""
    base_url = os.environ.get("API_BASE_URL", "").rstrip("/")
    api_key = os.environ.get("X_API_KEY", os.environ.get("COGNEE_API_KEY", ""))
    
    # We do not use a global client session here to avoid event loop attachment issues
    # when Uvicorn restarts workers. Instead, we use a context manager per operation.
    return httpx.AsyncClient(
        base_url=base_url,
        headers={"X-Api-Key": api_key},
        timeout=httpx.Timeout(COGNEE_TIMEOUT_SECONDS)
    )

async def remember(text: str, dataset_name: str, **kwargs: Any) -> Any:
    """Add text data and instantly cognify it."""
    try:
        async with _get_client() as client:
            # 1. Add Data
            files = {"data": ("data.txt", text.encode("utf-8"), "text/plain")}
            data = {"datasetName": dataset_name}
            
            r_add = await client.post("/api/v1/add", data=data, files=files)
            r_add.raise_for_status()
            add_resp = r_add.json()
            
            data_id = None
            if "data_ingestion_info" in add_resp and len(add_resp["data_ingestion_info"]) > 0:
                data_id = add_resp["data_ingestion_info"][0].get("data_id")
            
            # 2. Cognify
            payload = {
                "datasets": [dataset_name],
                "runInBackground": False
            }
            # Give cognify a much longer timeout
            r_cog = await client.post(
                "/api/v1/cognify", 
                json=payload, 
                timeout=COGNEE_REMEMBER_TIMEOUT_SECONDS
            )
            r_cog.raise_for_status()
            
            # Diagnostic logging matching old behavior
            logger.info(
                "cognee_ops.remember diagnostic: "
                "dataset_name=%r data_id=%r",
                dataset_name, data_id
            )
            
            # Return a simple mock object so `tutoring.py` can still access `result.data_id` 
            # if we ever decide to map it that way. Currently `tutoring.py` does not strictly 
            # need `result.data_id` since it's tracked differently, but we return something safe.
            return SimpleNamespace(dataset_name=dataset_name, data_id=data_id)
            
    except Exception as exc:
        logger.warning(
            "cognee_ops.remember: failed (%s: %s) — returning None",
            type(exc).__name__, exc,
        )
        return None

async def recall(query: str, datasets: list[str], **kwargs: Any) -> list[Any]:
    """Search the graph for the answer to the query."""
    try:
        async with _get_client() as client:
            payload = {
                "query": query,
                "searchType": "GRAPH_COMPLETION",
                "datasets": datasets
            }
            r = await client.post("/api/v1/search", json=payload, timeout=COGNEE_TIMEOUT_SECONDS)
            r.raise_for_status()
            
            # The search endpoint returns a list of results (strings or objects).
            # We return them directly.
            return r.json()
            
    except Exception as exc:
        logger.warning(
            "cognee_ops.recall: failed (%s: %s) — returning []",
            type(exc).__name__, exc,
        )
        return []

async def improve(dataset: str, **kwargs: Any) -> Any:
    """
    Rebuild the knowledge graph by clearing memory (but keeping raw text)
    and running cognify again.
    """
    try:
        async with _get_client() as client:
            # 1. Forget Memory Only
            payload_forget = {
                "dataset": dataset,
                "memoryOnly": True
            }
            r_forget = await client.post("/api/v1/forget", json=payload_forget, timeout=COGNEE_TIMEOUT_SECONDS)
            r_forget.raise_for_status()
            
            # 2. Re-cognify all preserved text
            payload_cog = {
                "datasets": [dataset],
                "runInBackground": False
            }
            r_cog = await client.post(
                "/api/v1/cognify", 
                json=payload_cog, 
                timeout=COGNEE_REMEMBER_TIMEOUT_SECONDS
            )
            r_cog.raise_for_status()
            return r_cog.json()
            
    except Exception as exc:
        logger.warning(
            "cognee_ops.improve: failed (%s: %s) — returning None",
            type(exc).__name__, exc,
        )
        return None

async def forget(
    dataset: str,
    data_id: UUID | str | None = None,
    memory_only: bool = False,
    **kwargs: Any,
) -> Any:
    """Delete a dataset, or a specific data_id within a dataset."""
    try:
        async with _get_client() as client:
            payload = {
                "dataset": dataset,
                "memoryOnly": memory_only
            }
            if data_id:
                payload["dataId"] = str(data_id)
                
            r = await client.post("/api/v1/forget", json=payload, timeout=COGNEE_TIMEOUT_SECONDS)
            r.raise_for_status()
            return r.json()
            
    except Exception as exc:
        logger.warning(
            "cognee_ops.forget: failed (%s: %s) — returning None",
            type(exc).__name__, exc,
        )
        return None
