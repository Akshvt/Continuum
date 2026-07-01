"""
Compatibility wrappers around the installed Cognee package.

The app and test files use a small, stable surface area, while the
underlying package keeps the real memory operations.

Each wrapper applies a hard timeout (COGNEE_TIMEOUT_SECONDS) so that
when the embedding engine is unavailable (e.g. no OPENAI_API_KEY), we
fail fast instead of hanging through Cognee's exponential-backoff retry
loop (2 s → 4 s → 8 s → 16 s → 32 s → 65 s …).  All callers already
wrap cognee_ops in try/except and fall back to degraded mode.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from typing import Any
from uuid import UUID

import litellm

# mistral-embed does not accept a 'dimensions' parameter.
# drop_params=True tells litellm to silently discard any unsupported params
# rather than raising UnsupportedParamsError and aborting the pipeline.
litellm.drop_params = True

from cognee import forget as _forget
from cognee import improve as _improve
from cognee import recall as _recall
from cognee import remember as _remember

logger = logging.getLogger("continuum.cognee_ops")

# Maximum seconds to wait for short Cognee operations (recall, improve, forget)
COGNEE_TIMEOUT_SECONDS: float = 10.0
# Generous timeout for long-running memory generation
COGNEE_REMEMBER_TIMEOUT_SECONDS: float = 360.0


async def _call(operation, timeout: float, *args: Any, **kwargs: Any):
    result = operation(*args, **kwargs)
    if inspect.isawaitable(result):
        return await asyncio.wait_for(result, timeout=timeout)
    return result


async def remember(text: str, dataset_name: str, **kwargs: Any):
    try:
        result = await _call(_remember, COGNEE_REMEMBER_TIMEOUT_SECONDS, text, dataset_name=dataset_name, **kwargs)
        # ── Diagnostic logging (Option B investigation) ─────────────────────────
        # Log every field of RememberResult that _resolve() populates so we can
        # see exactly what cognify() returned and why .items may be empty.
        logger.info(
            "cognee_ops.remember diagnostic: "
            "status=%r dataset_id=%r pipeline_run_id=%r "
            "items_processed=%r items=%r entry_id=%r entry_type=%r "
            "raw_result_type=%s raw_result=%r",
            getattr(result, "status", "N/A"),
            getattr(result, "dataset_id", "N/A"),
            getattr(result, "pipeline_run_id", "N/A"),
            getattr(result, "items_processed", "N/A"),
            getattr(result, "items", "N/A"),
            getattr(result, "entry_id", "N/A"),
            getattr(result, "entry_type", "N/A"),
            type(getattr(result, "raw_result", None)).__name__,
            getattr(result, "raw_result", "N/A"),
        )
        return result
    except Exception as exc:
        logger.warning(
            "cognee_ops.remember: failed (%s: %s) — returning None",
            type(exc).__name__, exc,
        )
        return None


async def recall(query: str, datasets: list[str], **kwargs: Any):
    try:
        return await _call(_recall, COGNEE_TIMEOUT_SECONDS, query, datasets=datasets, **kwargs)
    except Exception as exc:
        logger.warning(
            "cognee_ops.recall: failed (%s: %s) — returning []",
            type(exc).__name__, exc,
        )
        return []


async def improve(dataset: str, **kwargs: Any):
    try:
        return await _call(_improve, COGNEE_TIMEOUT_SECONDS, dataset=dataset, **kwargs)
    except Exception as exc:
        logger.warning(
            "cognee_ops.improve: failed (%s: %s) — returning None",
            type(exc).__name__, exc,
        )
        return None


async def forget(
    dataset: str,
    data_id: UUID | None = None,
    memory_only: bool = False,
    **kwargs: Any,
):
    try:
        return await _call(
            _forget,
            COGNEE_TIMEOUT_SECONDS,
            dataset=dataset,
            data_id=data_id,
            memory_only=memory_only,
            **kwargs,
        )
    except Exception as exc:
        logger.warning(
            "cognee_ops.forget: failed (%s: %s) — returning None",
            type(exc).__name__, exc,
        )
        return None

