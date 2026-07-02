"""Session timeline endpoint.

GET /api/timeline/{student_id}

Reads the existing lifecycle_log.json via get_lifecycle_log() and returns
every event for the student as a chronological list.  Each entry is tagged
with the operation type and surfaced with all detail fields already stored
in that log entry (concept, misconception, strategy_used, mastery_delta,
data_id, etc.).  No new storage is used or created.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter

from app.services.memory import get_lifecycle_log

logger = logging.getLogger("continuum.router.timeline")

router = APIRouter()


# Fields that are always present on every log entry (structural)
_STRUCTURAL_FIELDS = {"operation", "student_id", "dataset", "timestamp"}

# Per-operation detail fields to surface explicitly (others pass through)
_OPERATION_DETAIL_FIELDS: dict[str, list[str]] = {
    "remember": [
        "concept", "is_correct", "strategy_used", "misconception",
        "mastery_delta", "data_id",
    ],
    "recall": ["query", "result_count"],
    "improve": ["trigger"],
    "forget": [
        "misconception", "confirmed_correct_count", "data_id", "reason",
    ],
}


# ─────────────────────────────────────────────
# GET /api/timeline/{student_id}
# ─────────────────────────────────────────────

@router.get("/{student_id}")
async def timeline(student_id: str):
    """Return a chronological list of all memory lifecycle events for a student.

    Reads lifecycle_log.json as-is — no new storage is involved.

    Each event has:
        - operation: "remember" | "recall" | "improve" | "forget"
        - timestamp: ISO-8601 UTC string
        - detail: dict of operation-specific fields already in the log
        - raw: the original log entry (passthrough for any extra fields)

    Response shape:
        {
            "student_id": str,
            "event_count": int,
            "events": [
                {
                    "operation": str,
                    "timestamp": str,
                    "detail": { ... operation-specific fields ... },
                }
            ]
        }
    """
    raw_events: list[dict[str, Any]] = get_lifecycle_log(student_id)

    # Log is appended in order so it is already chronological.
    # Build a clean event list, keeping all fields that exist in the log.
    events: list[dict[str, Any]] = []
    for entry in raw_events:
        operation = entry.get("operation", "unknown")

        # Pull out the known detail fields for this operation type
        expected_fields = _OPERATION_DETAIL_FIELDS.get(operation, [])
        detail: dict[str, Any] = {}

        for field in expected_fields:
            if field in entry:
                detail[field] = entry[field]

        # Also pass through any extra fields that aren't structural
        for key, value in entry.items():
            if key not in _STRUCTURAL_FIELDS and key not in detail:
                detail[key] = value

        events.append({
            "operation": operation,
            "timestamp": entry.get("timestamp"),
            "detail": detail,
        })

    return {
        "student_id": student_id,
        "event_count": len(events),
        "events": events,
    }
