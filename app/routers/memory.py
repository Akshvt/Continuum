from fastapi import APIRouter
from pydantic import BaseModel

from app.services.memory import (
    forget_resolved_misconception,
    get_lifecycle_log,
    improve_student_memory,
    recall_student_context,
    remember_interaction,
)


router = APIRouter()


class RememberRequest(BaseModel):
    student_id: str
    concept: str
    answer: str
    is_correct: bool
    misconception: str | None = None
    strategy_used: str
    mastery_delta: float


class RecallRequest(BaseModel):
    student_id: str
    query: str


class ImproveRequest(BaseModel):
    student_id: str


class ForgetRequest(BaseModel):
    student_id: str
    misconception: str
    confirmed_correct_count: int


@router.post("/remember")
async def remember(request: RememberRequest):
    await remember_interaction(**request.model_dump())
    return {"status": "ok"}


@router.post("/recall")
async def recall(request: RecallRequest):
    results = await recall_student_context(request.student_id, request.query)
    return {"results": results}


@router.post("/improve")
async def improve(request: ImproveRequest):
    await improve_student_memory(request.student_id)
    return {"status": "ok"}


@router.post("/forget")
async def forget(request: ForgetRequest):
    await forget_resolved_misconception(**request.model_dump())
    return {"status": "ok"}


@router.get("/log/{student_id}")
def lifecycle_log(student_id: str):
    return {"events": get_lifecycle_log(student_id)}
