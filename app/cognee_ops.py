"""
Compatibility wrappers around the installed Cognee package.

The app and test files use a small, stable surface area, while the
underlying package keeps the real memory operations.
"""

from __future__ import annotations

import inspect
from typing import Any

from cognee import forget as _forget
from cognee import improve as _improve
from cognee import recall as _recall
from cognee import remember as _remember


async def _call(operation, /, *args: Any, **kwargs: Any):
    result = operation(*args, **kwargs)
    if inspect.isawaitable(result):
        return await result
    return result


async def remember(text: str, dataset_name: str, **kwargs: Any):
    return await _call(_remember, text, dataset_name=dataset_name, **kwargs)


async def recall(query: str, datasets: list[str], **kwargs: Any):
    return await _call(_recall, query, datasets=datasets, **kwargs)


async def improve(dataset: str, **kwargs: Any):
    return await _call(_improve, dataset=dataset, **kwargs)


async def forget(dataset: str, memory_only: bool = False, **kwargs: Any):
    return await _call(_forget, dataset=dataset, memory_only=memory_only, **kwargs)
