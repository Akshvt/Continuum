from fastapi import APIRouter
from app.services.status import has_pending

router = APIRouter()

@router.get("/{student_id}")
async def get_status(student_id: str):
    """Return whether the student has pending memory background writes."""
    return {"has_pending_writes": has_pending(student_id)}
