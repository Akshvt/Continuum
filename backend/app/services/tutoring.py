"""Tutoring engine orchestration for the frontend-facing API."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict, deque
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

import random as _random

# Question format pool — a random subset is injected into each prompt so the
# LLM sees variety instead of one template it can lock onto.
_QUESTION_FORMATS = [
    "Direct definition: 'What does the term ___ mean in Python?'",
    "Predict-the-output: 'What will this code print?\\n```python\\nsome_code_here\\n```'",
    "Fill-in-the-blank: 'Complete the line: ___ = 42  — what data type is this value?'",
    "Scenario-based: 'A student writes `x = \"5\" + 3`. What happens and why?'",
    "Compare-and-contrast: 'How are ___ and ___ different in Python?'",
    "Fix-the-bug: 'This code has an error — what is wrong and how would you fix it?'",
    "True-or-false with justification: 'True or false: ___ — explain your reasoning.'",
    "Short-answer application: 'Write one line of Python that demonstrates ___.'",
    "Reverse engineering: 'The output is `Hello World`. Write a single line of Python that produces this.'",
    "Explain like I'm 5: 'How would you explain the concept of ___ to someone who has never coded before?'",
    "Spot the difference: 'Code A does X, Code B does Y. What causes this difference?'",
    "Real-world analogy: 'If variables are like labeled boxes, what is a literal?'",
    "Refactoring: 'How could you rewrite this code to be more readable while keeping the same behavior?'",
    "Edge case testing: 'What happens if we pass a negative number or zero to this piece of code?'",
    "Multiple choice (conceptual): 'Which of these three statements about ___ is false, and why?'",
]

# Per-student cache of recently generated questions (kept in memory, lost on restart).
# Used to tell the LLM what NOT to repeat.
_recent_questions_cache: dict[str, deque[str]] = {}


async def _generate_question(
    student_id: str,
    current_concept: str,
    focus_concept: str,
    student_context: str,
    curriculum_context_text: str,
    teaching_style: str = DEFAULT_TEACHING_STYLE,
    recent_questions: list[str] | None = None,
) -> str:
    if not config.LLM_API_KEY:
        return _fallback_question(current_concept, focus_concept)

    # Pick 4 random formats so the LLM sees genuine variety each time
    sampled_formats = _random.sample(_QUESTION_FORMATS, min(4, len(_QUESTION_FORMATS)))
    format_list = "\n".join(f"  - {fmt}" for fmt in sampled_formats)

    # Build a "do NOT repeat" block from recently asked questions
    recent_block = ""
    if recent_questions:
        recent_lines = "\n".join(f'  - "{q}"' for q in recent_questions[-3:])
        recent_block = (
            f"\n\nRecently asked questions (DO NOT repeat or closely rephrase these):\n"
            f"{recent_lines}"
        )

    try:
        client = _make_llm_client()
        response = await client.chat.completions.create(
            model=config.LLM_MODEL,
            temperature=0.75,
            max_tokens=180,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Python tutoring engine that creates engaging, varied questions.\n\n"
                        "RULES:\n"
                        "1. Write exactly ONE question. No answers, no hints, no bullet lists, no markdown headers.\n"
                        "2. You MUST pick a DIFFERENT question format each time. Choose from formats like:\n"
                        f"{format_list}\n"
                        "3. If the teaching style is 'worked_example_first', include a short code snippet.\n"
                        "   If 'analogy_first', frame the question using a real-world analogy.\n"
                        "   If 'question_first', ask a direct conceptual question.\n"
                        "4. Vary sentence structure — never start with 'What is the difference between'.\n"
                        "5. Keep the question concise (1-3 sentences max, or a short code block + one sentence)."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Concept being studied: {current_concept}\n"
                        f"Focus area: {focus_concept}\n"
                        f"Teaching style: {teaching_style}\n"
                        f"Student history:\n{student_context or '(new student, no history yet)'}\n\n"
                        f"Curriculum context:\n{curriculum_context_text}\n"
                        f"{recent_block}\n\n"
                        "Generate one question."
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
    async def safe_choose_teaching_style():
        try:
            return await choose_teaching_style(student_id, normalized_current)
        except Exception as exc:
            logger.warning("strategy selection failed (%s), using default", exc)
            return DEFAULT_TEACHING_STYLE

    async def safe_recall_student():
        try:
            return await recall_student_context(
                student_id,
                (
                    f"What weak points, misconceptions, or recent struggles does this student have "
                    f"that matter for {display_current}?"
                ),
            )
        except Exception as exc:
            logger.warning("student recall failed (%s)", exc)
            return []

    async def safe_recall_curriculum():
        try:
            return await recall(
                (
                    f"For {display_current}, what prerequisites or dependent concepts should the tutor "
                    f"focus on first?"
                ),
                datasets=[config.CURRICULUM_DATASET],
            )
        except Exception as exc:
            logger.warning("curriculum recall failed (%s)", exc)
            return []

    # Run the 3 independent context gathers concurrently to significantly reduce latency
    teaching_style, student_results, curriculum_results = await asyncio.gather(
        safe_choose_teaching_style(),
        safe_recall_student(),
        safe_recall_curriculum(),
    )

    student_text = _render_results(student_results)
    curriculum_text = _render_results(curriculum_results) or curriculum_context()
    focus_concept = _choose_focus_concept(normalized_current, f"{student_text}\n{curriculum_text}")
    display_focus_concept = _display_concept(focus_concept)
    # Pull recently asked questions from cache to feed the "do not repeat" block
    recent_qs = list(_recent_questions_cache.get(student_id, []))

    question = await _generate_question(
        student_id=student_id,
        current_concept=display_current,
        focus_concept=display_focus_concept,
        student_context=student_text,
        curriculum_context_text=curriculum_text,
        teaching_style=teaching_style,
        recent_questions=recent_qs,
    )

    # Store in cache for next call (keep last 5 per student)
    if student_id not in _recent_questions_cache:
        _recent_questions_cache[student_id] = deque(maxlen=5)
    _recent_questions_cache[student_id].append(question)

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
