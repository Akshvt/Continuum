"""Dashboard aggregation endpoint.

GET /api/dashboard/{student_id}

Calls recall_student_context to fetch mastery and strategy data from the
student's Cognee memory graph, then parses the returned text into a clean
structured payload.  No hardcoded sample data — if recall returns nothing
(new student, or Cognee unavailable), the response is an empty but
correctly shaped object.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from fastapi import APIRouter

from app.services.memory import recall_student_context

logger = logging.getLogger("continuum.router.dashboard")

router = APIRouter()


# ─────────────────────────────────────────────
# Known concept and strategy vocabularies
# (kept in sync with curriculum.py and strategy.py)
# ─────────────────────────────────────────────

_KNOWN_CONCEPTS = [
    "literals_and_values",
    "variables",
    "data_types",
    "print_and_input",
    "operators",
    "strings",
    "boolean_logic",
    "conditionals",
    "lists",
    "loops",
    "functions",
    "dictionaries",
]

_KNOWN_STRATEGIES = [
    "worked_example_first",
    "analogy_first",
    "question_first",
]


# ─────────────────────────────────────────────
# GET /api/dashboard/{student_id}
# ─────────────────────────────────────────────

@router.get("/{student_id}")
async def dashboard(student_id: str):
    """Return aggregated mastery and strategy data for a student.

    Queries Cognee memory for mastery level per concept and current
    favoured teaching strategy per concept.

    Response shape:
        {
            "student_id": str,
            "concepts": [
                {
                    "concept": str,
                    "mastery_level": float | null,
                    "mastery_label": "unknown" | "low" | "medium" | "high",
                    "favoured_strategy": str | null,
                    "interaction_count": int,
                }
            ],
            "recall_available": bool,
            "raw_recall_snippets": int,
        }
    """
    mastery_results: list[Any] = []
    strategy_results: list[Any] = []

    try:
        mastery_results = await recall_student_context(
            student_id,
            (
                "For each concept this student has studied, what is their mastery level? "
                "How many times did they answer correctly versus incorrectly? "
                "What is their mastery delta trend? List every concept you have data for."
            ),
        )
    except Exception as exc:
        logger.warning(
            "dashboard: mastery recall failed for student=%s (%s)", student_id, exc
        )

    try:
        strategy_results = await recall_student_context(
            student_id,
            (
                "For each concept this student has studied, which teaching strategy "
                "worked best? Was it worked_example_first, analogy_first, or "
                "question_first? List every concept you have strategy data for."
            ),
        )
    except Exception as exc:
        logger.warning(
            "dashboard: strategy recall failed for student=%s (%s)", student_id, exc
        )

    all_results = mastery_results + strategy_results
    total_snippets = len(all_results)

    # Parse recall text into per-concept records
    concept_map: dict[str, dict[str, Any]] = {}
    for result in all_results:
        text = _result_to_text(result).lower()
        _extract_concepts(text, concept_map)

    # Build response in curriculum order; only include concepts that appeared
    concepts_out: list[dict[str, Any]] = [
        {
            "concept": concept,
            "mastery_level": entry.get("mastery_level"),
            "mastery_label": _mastery_label(entry.get("mastery_level")),
            "favoured_strategy": entry.get("favoured_strategy"),
            "interaction_count": entry.get("interaction_count", 0),
        }
        for concept in _KNOWN_CONCEPTS
        if concept in (entry := concept_map.get(concept, {})) or concept in concept_map
    ]

    # Rebuild cleanly (the walrus assignment above is tricky to read)
    concepts_out = []
    for concept in _KNOWN_CONCEPTS:
        if concept not in concept_map:
            continue
        entry = concept_map[concept]
        concepts_out.append({
            "concept": concept,
            "mastery_level": entry.get("mastery_level"),
            "mastery_label": _mastery_label(entry.get("mastery_level")),
            "favoured_strategy": entry.get("favoured_strategy"),
            "interaction_count": entry.get("interaction_count", 0),
        })

    return {
        "student_id": student_id,
        "concepts": concepts_out,
        "recall_available": total_snippets > 0,
        "raw_recall_snippets": total_snippets,
    }


# ─────────────────────────────────────────────
# Parsing helpers
# ─────────────────────────────────────────────

def _result_to_text(result: Any) -> str:
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        return " ".join(str(v) for v in result.values())
    return str(result)


def _extract_concepts(text: str, concept_map: dict[str, dict[str, Any]]) -> None:
    """Scan a recall snippet and update concept_map in place."""
    for concept in _KNOWN_CONCEPTS:
        readable = concept.replace("_", " ")
        if concept not in text and readable not in text:
            continue

        if concept not in concept_map:
            concept_map[concept] = {}

        entry = concept_map[concept]

        # Mastery delta: accumulate "+0.10" / "-0.15" patterns
        for delta_str in re.findall(r"mastery delta[:\s]+([+-]?\d+\.?\d*)", text):
            try:
                delta = float(delta_str)
                current = entry.get("mastery_level") or 0.5
                entry["mastery_level"] = round(max(0.0, min(1.0, current + delta)), 3)
            except ValueError:
                pass

        # Interaction count from "N times correct / incorrect" patterns
        correct_n = sum(
            int(m) for m in re.findall(r"(\d+)\s+time[s]?\s+correct", text)
        )
        incorrect_n = sum(
            int(m) for m in re.findall(r"(\d+)\s+time[s]?\s+incorrect", text)
        )
        if correct_n + incorrect_n > 0:
            entry["interaction_count"] = (
                entry.get("interaction_count", 0) + correct_n + incorrect_n
            )
            if "mastery_level" not in entry:
                entry["mastery_level"] = round(
                    correct_n / (correct_n + incorrect_n), 3
                )

        # Strategy: first recognised strategy name near this concept
        if "favoured_strategy" not in entry:
            for strategy in _KNOWN_STRATEGIES:
                if strategy in text or strategy.replace("_", " ") in text:
                    entry["favoured_strategy"] = strategy
                    break

        # Coarse mastery signal from lone "correct" / "incorrect" words
        if "mastery_level" not in entry:
            has_correct = "correct" in text
            has_incorrect = "incorrect" in text
            if has_correct and not has_incorrect:
                entry["mastery_level"] = 0.75
            elif has_incorrect and not has_correct:
                entry["mastery_level"] = 0.25


def _mastery_label(level: float | None) -> str:
    if level is None:
        return "unknown"
    if level >= 0.7:
        return "high"
    if level >= 0.4:
        return "medium"
    return "low"
