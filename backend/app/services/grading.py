"""Grading and misconception classification service.

Calls the LLM to evaluate student answers, determine correctness,
and classify misconceptions in plain natural language when wrong.
"""

from __future__ import annotations

import json
import logging
from typing import Any, TypedDict

from openai import AsyncOpenAI

from config import config

logger = logging.getLogger("continuum.grading")

# Mistral's OpenAI-compatible base URL
_MISTRAL_BASE_URL = "https://api.mistral.ai/v1"


def _make_llm_client() -> AsyncOpenAI:
    """Return an AsyncOpenAI client pointed at the configured LLM provider.

    Mistral exposes an OpenAI-compatible REST API, so we can reuse the
    openai SDK by overriding base_url.  Other providers (e.g. openai) work
    with the default base URL.
    """
    if config.LLM_PROVIDER.lower() == "mistral":
        return AsyncOpenAI(
            api_key=config.LLM_API_KEY,
            base_url=_MISTRAL_BASE_URL,
        )
    return AsyncOpenAI(api_key=config.LLM_API_KEY)


class GradingResult(TypedDict):
    is_correct: bool
    misconception: str | None
    feedback: str
    grading_unavailable: bool
    """True when the result came from the fallback, not the LLM.

    Callers must NOT write this interaction to permanent memory when
    grading_unavailable is True — the grade is not real and would corrupt
    mastery scores and forget-trigger streak counts.
    """


async def grade_answer(
    student_id: str,
    concept: str,
    question: str,
    student_answer: str,
) -> GradingResult:
    """Evaluate a student's answer using the LLM.

    Returns a GradingResult.  Check ``grading_unavailable`` before
    persisting: when True, the grade is a fallback placeholder and must
    NOT be written to Cognee or the lifecycle log.
    """
    if not config.LLM_API_KEY:
        logger.warning("grading: LLM_API_KEY not set, using heuristic fallback")
        return _fallback_grade(student_answer)

    try:
        return await _llm_grade(student_id, concept, question, student_answer)
    except Exception as exc:
        logger.error("grading: LLM call failed (%s), using fallback", exc)
        return _fallback_grade(student_answer)


async def _llm_grade(
    student_id: str,
    concept: str,
    question: str,
    student_answer: str,
) -> GradingResult:
    """Use the configured LLM provider to grade the answer and classify any misconception."""
    client = _make_llm_client()

    response = await client.chat.completions.create(
        model=config.LLM_MODEL,
        temperature=0.2,
        max_tokens=300,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert Python tutor grading a student's answer. "
                    "Respond with ONLY a valid JSON object (no markdown, no backticks) "
                    "with exactly these keys:\n"
                    '  "is_correct": true or false,\n'
                    '  "misconception": null if correct, or a short plain-language '
                    "description of the student's misunderstanding if wrong,\n"
                    '  "feedback": a brief, encouraging explanation for the student.\n'
                    "Be strict about correctness but kind in feedback."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Concept: {concept}\n"
                    f"Question: {question}\n"
                    f"Student answer: {student_answer}\n\n"
                    "Grade this answer."
                ),
            },
        ],
    )

    raw = response.choices[0].message.content or ""
    raw = raw.strip()

    # Strip markdown code fences if the model wrapped the JSON
    if raw.startswith("```"):
        lines = raw.split("\n")
        # Remove first line (```json or ```) and last line (```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        raw = "\n".join(lines).strip()

    parsed = json.loads(raw)

    return GradingResult(
        is_correct=bool(parsed.get("is_correct", False)),
        misconception=parsed.get("misconception"),
        feedback=str(parsed.get("feedback", "No feedback available.")),
        grading_unavailable=False,
    )


def _fallback_grade(student_answer: str) -> GradingResult:
    """Conservative fallback when the LLM is unavailable.

    Marks the answer as incorrect with a friendly explanation rather
    than the previous "non-empty = correct" heuristic.  This prevents
    false-positive mastery deltas from corrupting the student's memory
    graph when the grading LLM is temporarily unreachable.
    """
    if not student_answer.strip():
        return GradingResult(
            is_correct=False,
            misconception="Empty or blank answer provided",
            feedback="No answer was provided.",
            grading_unavailable=True,
        )

    return GradingResult(
        is_correct=False,
        misconception=None,
        feedback=(
            "Your answer was recorded but could not be graded right now "
            "(AI grading temporarily unavailable). It will be reviewed "
            "when the service is restored. Don't worry — this won't "
            "count against you."
        ),
        grading_unavailable=True,
    )
