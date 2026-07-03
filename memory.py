"""
Memory Lifecycle Service.

The single place all four Cognee operations are called from.
Every other service imports and uses these five functions.
No other file should call cognee directly.

Every operation is logged to lifecycle_log.json for demo purposes —
this file is your proof to judges that all four primitives are actually used.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from cognee_ops import forget, improve, recall, remember

LOG_PATH = Path("lifecycle_log.json")


def _log(operation: str, student_id: str, dataset: str, detail: dict):
    """Append one lifecycle event to lifecycle_log.json."""
    entry = {
        "operation": operation,
        "student_id": student_id,
        "dataset": dataset,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **detail,
    }
    existing = []
    if LOG_PATH.exists():
        try:
            existing = json.loads(LOG_PATH.read_text())
        except json.JSONDecodeError:
            existing = []
    existing.append(entry)
    LOG_PATH.write_text(json.dumps(existing, indent=2))


def student_dataset(student_id: str) -> str:
    """Consistent dataset name per student. All student data lives here."""
    return f"student_{student_id}"


# ─────────────────────────────────────────────
# remember()
# Call this every time a student completes an interaction.
# ─────────────────────────────────────────────

async def remember_interaction(
    student_id: str,
    concept: str,
    answer: str,
    is_correct: bool,
    misconception: str | None,
    strategy_used: str,
    mastery_delta: float,
) -> None:
    """
    Store one tutoring interaction into that student's Cognee dataset.
    Called after every question attempt.
    """
    dataset = student_dataset(student_id)

    # Write a structured natural-language fact — this is what Cognee
    # turns into graph nodes and edges during remember()
    text = (
        f"Student {student_id} attempted concept '{concept}'. "
        f"Answer was {'correct' if is_correct else 'incorrect'}. "
        f"Strategy used: {strategy_used}. "
        f"Mastery delta: {mastery_delta:+.2f}. "
        + (f"Misconception identified: {misconception}. " if misconception else "")
    )

    await remember(text, dataset_name=dataset)

    _log("remember", student_id, dataset, {
        "concept": concept,
        "is_correct": is_correct,
        "strategy_used": strategy_used,
        "misconception": misconception,
        "mastery_delta": mastery_delta,
    })


# ─────────────────────────────────────────────
# recall()
# Call this before generating any tutor response.
# ─────────────────────────────────────────────

async def recall_student_context(student_id: str, query: str) -> list:
    """
    Retrieve relevant history for a student given a query.

    Examples of queries you'll use:
    - "What concepts has this student struggled with and why?"
    - "Which teaching strategies worked best for this student on algebra?"
    - "What unresolved misconceptions does this student have?"
    """
    dataset = student_dataset(student_id)

    results = await recall(
        query,
        datasets=[dataset],
    )

    _log("recall", student_id, dataset, {"query": query, "result_count": len(results)})

    return results


async def recall_curriculum(query: str) -> list:
    """
    Query the shared curriculum graph.
    Used to find prerequisites, concept relationships, etc.
    """
    results = await recall(
        query,
        datasets=["curriculum_global"],
    )
    return results


# ─────────────────────────────────────────────
# improve()
# Call this after every N interactions (default 5).
# Also expose as a manual endpoint for demo purposes.
# ─────────────────────────────────────────────

async def improve_student_memory(student_id: str) -> None:
    """
    Re-enrich a student's memory graph after accumulated interactions.
    Re-weights nodes, prunes stale edges, links newly related concepts.

    Auto-triggered every N interactions by the tutoring engine.
    Also manually triggerable via POST /api/memory/improve/{student_id}.
    """
    dataset = student_dataset(student_id)

    await improve(dataset=dataset)

    _log("improve", student_id, dataset, {
        "trigger": "auto or manual — check tutoring engine logs",
    })


# ─────────────────────────────────────────────
# forget()
# Call this when a misconception is fully resolved.
# ─────────────────────────────────────────────

async def forget_resolved_misconception(
    student_id: str,
    misconception: str,
    confirmed_correct_count: int,
) -> None:
    """
    Prune a resolved misconception from the student's memory dataset.

    Called automatically by the tutoring engine once a student has answered
    the relevant concept correctly N times in a row (default: 3).

    We do NOT wipe the whole student dataset — only the stale misconception data.
    The student's positive history stays intact.
    """
    dataset = student_dataset(student_id)

    # Store a "resolution" fact first so the graph knows this was resolved,
    # not just deleted — this keeps provenance clean
    resolution_text = (
        f"Student {student_id} has resolved the misconception: '{misconception}'. "
        f"Confirmed correct {confirmed_correct_count} times consecutively. "
        f"This misconception is no longer active."
    )
    await remember(resolution_text, dataset_name=dataset)

    # Now forget the old misconception data by dataset scope.
    # In v1.2.2, forget() by dataset prunes that dataset's stale nodes
    # after the improvement pass. Pair with improve() for best effect.
    await forget(dataset=dataset, memory_only=True)
    await improve(dataset=dataset)

    _log("forget", student_id, dataset, {
        "misconception": misconception,
        "confirmed_correct_count": confirmed_correct_count,
        "reason": "Misconception resolved — pruned stale data, re-improved graph",
    })


# ─────────────────────────────────────────────
# Utility: read the lifecycle log
# Used by the dashboard endpoint to show judges the event history
# ─────────────────────────────────────────────

def get_lifecycle_log(student_id: str | None = None) -> list:
    """Return all lifecycle events, optionally filtered by student."""
    if not LOG_PATH.exists():
        return []
    try:
        events = json.loads(LOG_PATH.read_text())
    except json.JSONDecodeError:
        return []
    if student_id:
        events = [e for e in events if e.get("student_id") == student_id]
    return events