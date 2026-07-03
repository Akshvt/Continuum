from fastapi import APIRouter
from pydantic import BaseModel

from app.services.tutoring import generate_tutoring_question


router = APIRouter()


class TutoringRequest(BaseModel):
    student_id: str
    current_concept: str


@router.post("/question")
async def question(request: TutoringRequest):
    return await generate_tutoring_question(**request.model_dump())
