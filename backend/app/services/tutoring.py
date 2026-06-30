"""Tutoring engine orchestration for the frontend-facing API."""

from __future__ import annotations

import logging
from typing import Any

from openai import AsyncOpenAI

from cognee_ops import recall
from app.services.curriculum import (
    CURRICULUM_CONCEPTS,
    curriculum_context,
    curriculum_prerequisites,
    normalize_concept_name,
    seed_curriculum_dataset,
)
from app.services.memory import recall_student_context
from app.services.strategy import choose_teaching_style
from config import config

logger = logging.getLogger("continuum.tutoring")

DEFAULT_TEACHING_STYLE = "question_first"

# Mistral's OpenAI-compatible base URL
_MISTRAL_BASE_URL = "https://api.mistral.ai/v1"


def _make_llm_client() -> AsyncOpenAI:
    """Return an AsyncOpenAI client pointed at the configured LLM provider."""
    if config.LLM_PROVIDER.lower() == "mistral":
        return AsyncOpenAI(
            api_key=config.LLM_API_KEY,
            base_url=_MISTRAL_BASE_URL,
        )
    return AsyncOpenAI(api_key=config.LLM_API_KEY)


def _stringify_result(result: Any) -> str:
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        return " ".join(f"{key}: {value}" for key, value in result.items())
    return str(result)


def _render_results(results: list[Any]) -> str:
    return "\n".join(_stringify_result(item) for item in results)


def _find_known_concepts(text: str) -> list[str]:
    haystack = text.lower()
    found = []
    for concept in CURRICULUM_CONCEPTS:
        if concept in haystack:
            found.append(concept)
    return found


def _choose_focus_concept(current_concept: str, student_text: str) -> str:
    normalized_current = normalize_concept_name(current_concept)
    prerequisites = curriculum_prerequisites(normalized_current)
    if not prerequisites:
        return normalized_current

    student_concepts = _find_known_concepts(student_text)
    for prerequisite in prerequisites:
        if prerequisite in student_concepts or prerequisite in student_text.lower():
            return prerequisite

    for concept in student_concepts:
        if concept in prerequisites:
            return concept

    return normalized_current


def _fallback_question(current_concept: str, focus_concept: str) -> str:
    if focus_concept != current_concept:
        return (
            f"How does {focus_concept} support your understanding of {current_concept}?"
        )
    return f"What is the next step you would take to solve a problem about {current_concept}?"


def _display_concept(concept: str) -> str:
    return concept.replace("_", " ").strip()

async def _generate_question(
    student_id: str,
    current_concept: str,
    focus_concept: str,
    student_context: str,
    curriculum_context_text: str,
    teaching_style: str = DEFAULT_TEACHING_STYLE,
) -> str:
    if not config.LLM_API_KEY:
        return _fallback_question(current_concept, focus_concept)

    try:
        client = _make_llm_client()
        response = await client.chat.completions.create(
            model=config.LLM_MODEL,
            temperature=0.4,
            max_tokens=120,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a tutoring engine. Write exactly one concise student question. "
                        "Do not include answers, hints, bullets, or markdown."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Student ID: {student_id}\n"
                        f"Current concept: {current_concept}\n"
                        f"Focus concept: {focus_concept}\n"
                        f"Teaching style: {teaching_style}\n"
                        f"Student recall:\n{student_context}\n\n"
                        f"Curriculum graph:\n{curriculum_context_text}\n\n"
                        "Write one question that checks understanding of the focus concept while staying aligned to the current concept."
                    ),
                },
            ],
        )
        question = response.choices[0].message.content or ""
        question = question.strip()
        if question:
            return question
    except Exception as exc:
        logger.error("question generation: LLM call failed (%s), using fallback", exc)

    return _fallback_question(current_concept, focus_concept)


async def generate_tutoring_question(student_id: str, current_concept: str) -> dict[str, Any]:
    await seed_curriculum_dataset()

    normalized_current = normalize_concept_name(current_concept)
    display_current = _display_concept(normalized_current)

    # Dynamic strategy selection based on student history
    try:
        teaching_style = await choose_teaching_style(student_id, normalized_current)
    except Exception as exc:
        logger.warning("strategy selection failed (%s), using default", exc)
        teaching_style = DEFAULT_TEACHING_STYLE

    try:
        student_results = await recall_student_context(
            student_id,
            (
                f"What weak points, misconceptions, or recent struggles does this student have "
                f"that matter for {display_current}?"
            ),
        )
    except Exception as exc:
        logger.warning("student recall failed (%s)", exc)
        student_results = []

    try:
        curriculum_results = await recall(
            (
                f"For {display_current}, what prerequisites or dependent concepts should the tutor "
                f"focus on first?"
            ),
            datasets=[config.CURRICULUM_DATASET],
        )
    except Exception as exc:
        logger.warning("curriculum recall failed (%s)", exc)
        curriculum_results = []

    student_text = _render_results(student_results)
    curriculum_text = _render_results(curriculum_results) or curriculum_context()
    focus_concept = _choose_focus_concept(normalized_current, f"{student_text}\n{curriculum_text}")
    display_focus_concept = _display_concept(focus_concept)
    question = await _generate_question(
        student_id=student_id,
        current_concept=display_current,
        focus_concept=display_focus_concept,
        student_context=student_text,
        curriculum_context_text=curriculum_text,
        teaching_style=teaching_style,
    )

    return {
        "student_id": student_id,
        "current_concept": display_current,
        "focus_concept": display_focus_concept,
        "teaching_style": teaching_style,
        "question": question,
        "student_weak_points": _find_known_concepts(student_text),
        "curriculum_prerequisites": curriculum_prerequisites(normalized_current),
        "student_context": student_text,
        "curriculum_context": curriculum_text,
    }
