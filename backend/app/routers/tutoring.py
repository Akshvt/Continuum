"""Tutoring API routes: question generation and answer grading."""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
import asyncio
from app.services.status import increment_pending, decrement_pending

from app.services.grading import grade_answer
from app.services.memory import (
    forget_resolved_misconception,
    get_lifecycle_log,
    improve_student_memory,
    remember_interaction,
)
from app.services.tutoring import generate_tutoring_question
from config import config

logger = logging.getLogger("continuum.router.tutoring")

router = APIRouter()


# ─────────────────────────────────────────────
# Request / Response models
# ─────────────────────────────────────────────

class TutoringRequest(BaseModel):
    student_id: str
    current_concept: str


class AnswerRequest(BaseModel):
    student_id: str
    concept: str
    question: str
    student_answer: str
    strategy_used: str


# ─────────────────────────────────────────────
# POST /api/tutoring/question
# ─────────────────────────────────────────────

@router.post("/question")
async def question(request: TutoringRequest):
    return await generate_tutoring_question(**request.model_dump())


# ─────────────────────────────────────────────
# POST /api/tutoring/answer
# ─────────────────────────────────────────────

async def _process_memory_save(
    student_id: str,
    concept: str,
    student_answer: str,
    is_correct: bool,
    misconception: str | None,
    strategy_used: str,
    mastery_delta: float,
):
    try:
        # 4. Remember the interaction (persists data_id in lifecycle log)
        data_id = await remember_interaction(
            student_id=student_id,
            concept=concept,
            answer=student_answer,
            is_correct=is_correct,
            misconception=misconception,
            strategy_used=strategy_used,
            mastery_delta=mastery_delta,
        )

        # 5. Auto-triggers (Improve & Forget run AFTER remember)
        await _check_improve_trigger(student_id)
        if is_correct:
            await _check_forget_trigger(student_id, concept)
    except Exception as e:
        logger.error("Background memory save failed for student %s: %s", student_id, e, exc_info=True)
    finally:
        decrement_pending(student_id)


@router.post("/answer")
async def answer(request: AnswerRequest, background_tasks: BackgroundTasks):
    """Grade a student answer, log it, and fire auto-triggers.

    If the LLM grader is unavailable the response includes
    ``grading_unavailable: true`` and nothing is written to Cognee or
    the lifecycle log — the interaction never happened from the memory
    system's perspective.  The caller should surface the feedback to the
    student and prompt them to retry.
    """

    # 1. Grade the answer via LLM
    grading = await grade_answer(
        student_id=request.student_id,
        concept=request.concept,
        question=request.question,
        student_answer=request.student_answer,
    )

    # 2. Short-circuit: do NOT write to memory when grading fell back.
    #    A fallback grade is not a real outcome — logging it would corrupt
    #    mastery scores and the forget-trigger consecutive-correct streak.
    if grading["grading_unavailable"]:
        logger.warning(
            "answer: grading unavailable for student=%s concept=%s — "
            "skipping remember_interaction to protect memory integrity",
            request.student_id, request.concept,
        )
        return {
            "student_id": request.student_id,
            "concept": request.concept,
            "is_correct": grading["is_correct"],
            "misconception": grading["misconception"],
            "feedback": grading["feedback"],
            "grading_unavailable": True,
            "mastery_delta": 0.0,
            "data_id": None,
            "triggers_fired": [],
        }

    # 3. Compute a simple mastery delta (only reached for real LLM grades)
    mastery_delta = 0.1 if grading["is_correct"] else -0.15

    # Register background task and increment pending counter
    increment_pending(request.student_id)
    background_tasks.add_task(
        _process_memory_save,
        student_id=request.student_id,
        concept=request.concept,
        student_answer=request.student_answer,
        is_correct=grading["is_correct"],
        misconception=grading["misconception"],
        strategy_used=request.strategy_used,
        mastery_delta=mastery_delta,
    )

    return {
        "student_id": request.student_id,
        "concept": request.concept,
        "is_correct": grading["is_correct"],
        "misconception": grading["misconception"],
        "feedback": grading["feedback"],
        "grading_unavailable": False,
        "mastery_delta": mastery_delta,
        "data_id": None,  # Computed asynchronously now
        "triggers_fired": [],  # Checked asynchronously now
    }


# ─────────────────────────────────────────────
# Auto-trigger helpers
# ─────────────────────────────────────────────

async def _check_improve_trigger(student_id: str) -> list[str]:
    """Fire improve() when the student's remember count is a multiple of N."""
    log = get_lifecycle_log(student_id)
    remember_count = sum(1 for e in log if e.get("operation") == "remember")

    n = config.IMPROVE_TRIGGER_EVERY_N
    if remember_count > 0 and remember_count % n == 0:
        logger.info(
            "AUTO-TRIGGER improve: student=%s has %d remember events (every %d)",
            student_id, remember_count, n,
        )
        print(
            f"[auto-trigger] IMPROVE fired for student={student_id} "
            f"(interaction #{remember_count}, triggers every {n})"
        )
        await improve_student_memory(student_id)
        return [f"improve (interaction #{remember_count})"]

    return []


async def _check_forget_trigger(student_id: str, concept: str) -> list[str]:
    """Fire forget() when a concept has N consecutive correct answers
    after previously logged misconceptions on that concept.

    Tracks the streak per CONCEPT, not per exact misconception text.
    When the streak threshold is met, ALL active (not-yet-forgotten)
    misconceptions for this concept are resolved together. This handles
    the case where the LLM grader produces differently-worded
    misconception text for the same underlying misunderstanding.
    """
    log = get_lifecycle_log(student_id)
    n = config.FORGET_MISCONCEPTION_AFTER_N_CORRECT

    # Filter to remember events for this specific concept, newest first
    concept_events = [
        e for e in reversed(log)
        if e.get("operation") == "remember" and e.get("concept") == concept
    ]

    if len(concept_events) < n:
        return []

    # Check if the last N events are all correct
    recent = concept_events[:n]
    all_correct = all(e.get("is_correct") is True for e in recent)
    if not all_correct:
        return []

    # Collect ALL misconceptions ever logged for this concept
    all_misconceptions = [
        e for e in concept_events
        if e.get("misconception")
    ]

    if not all_misconceptions:
        return []

    # Check which misconceptions for this concept have already been forgotten
    already_forgotten_on_concept = any(
        e.get("operation") == "forget"
        and e.get("concept") == concept
        for e in log
    )

    # Collect the set of unique misconception texts NOT yet forgotten.
    # We use the forget log to check by concept scope, not exact text.
    forgotten_texts = set()
    for e in log:
        if e.get("operation") == "forget" and e.get("misconception"):
            forgotten_texts.add(e["misconception"])

    active_misconceptions = [
        e for e in all_misconceptions
        if e["misconception"] not in forgotten_texts
    ]

    if not active_misconceptions:
        return []

    # Forget ALL active misconceptions for this concept
    triggers_fired = []
    for misc_event in active_misconceptions:
        misconception_text = misc_event["misconception"]
        misconception_data_id = misc_event.get("data_id")

        logger.info(
            "AUTO-TRIGGER forget: student=%s resolved misconception '%s' on concept=%s "
            "(%d consecutive correct, data_id=%s)",
            student_id, misconception_text, concept, n, misconception_data_id,
        )
        print(
            f"[auto-trigger] FORGET fired for student={student_id} "
            f"concept={concept} misconception='{misconception_text}' "
            f"({n} consecutive correct answers)"
        )
        await forget_resolved_misconception(
            student_id=student_id,
            misconception=misconception_text,
            confirmed_correct_count=n,
            data_id=misconception_data_id,
        )
        triggers_fired.append(f"forget (misconception: '{misconception_text}')")

        # Mark this text as forgotten to avoid duplicate processing
        # within this same batch
        forgotten_texts.add(misconception_text)

    return triggers_fired

