"""Teaching strategy selection service.

Chooses a teaching style for a student + concept pair by recalling
what strategies have worked historically, with occasional exploration.
"""

from __future__ import annotations

import logging
import random
from typing import Any

from app.services.memory import recall_student_context

logger = logging.getLogger("continuum.strategy")

# The fixed set of teaching strategies the tutoring engine supports.
STRATEGIES: list[str] = [
    "worked_example_first",
    "analogy_first",
    "question_first",
]

DEFAULT_STRATEGY = "question_first"

# Probability of exploring a random strategy instead of the preferred one.
EXPLORATION_RATE = 0.20


async def choose_teaching_style(student_id: str, concept: str) -> str:
    """Pick the best teaching strategy for this student on this concept.

    Calls recall to find which strategies worked recently, then uses a
    recency-weighted preference. With EXPLORATION_RATE probability,
    picks a random strategy to avoid getting stuck in a rut.

    Returns one of the STRATEGIES strings. Falls back to DEFAULT_STRATEGY
    when recall is empty or errors.
    """
    # Exploration: occasionally try something new
    if random.random() < EXPLORATION_RATE:
        chosen = random.choice(STRATEGIES)
        logger.info(
            "strategy: exploring '%s' for student=%s concept=%s",
            chosen, student_id, concept,
        )
        return chosen

    try:
        results = await recall_student_context(
            student_id,
            f"Which teaching strategies worked best for this student on {concept}? "
            f"What strategy led to correct answers most recently?",
        )
    except Exception as exc:
        logger.warning("strategy: recall failed (%s), using default", exc)
        return DEFAULT_STRATEGY

    if not results:
        return DEFAULT_STRATEGY

    return _pick_from_recall(results)


def _pick_from_recall(results: list[Any]) -> str:
    """Extract strategy preference from recall results.

    Scans the recall text for mentions of known strategies, weighted
    by recency (later results = more recent interactions = higher weight).
    Returns the highest-scoring strategy, or DEFAULT_STRATEGY if none found.
    """
    scores: dict[str, float] = {s: 0.0 for s in STRATEGIES}

    for idx, result in enumerate(results):
        text = _result_to_text(result).lower()
        # Recency weight: later items in the list get higher weight
        weight = 1.0 + (idx * 0.5)
        for strategy in STRATEGIES:
            # Match both underscore and space forms
            readable = strategy.replace("_", " ")
            if strategy in text or readable in text:
                # Extra boost if the context mentions "correct" near the strategy
                correctness_boost = 1.5 if "correct" in text else 1.0
                scores[strategy] += weight * correctness_boost

    best_strategy = max(scores, key=scores.get)  # type: ignore[arg-type]
    if scores[best_strategy] > 0:
        logger.info(
            "strategy: chose '%s' (score=%.1f) from recall",
            best_strategy, scores[best_strategy],
        )
        return best_strategy

    return DEFAULT_STRATEGY


def _result_to_text(result: Any) -> str:
    """Convert a single recall result to a string for scanning."""
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        return " ".join(str(v) for v in result.values())
    return str(result)
