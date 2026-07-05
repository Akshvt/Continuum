"""Auth router — minimal email-based student identity.

POST /api/auth/login   { "email": "..." }  → { "student_id": "...", "email": "..." }
POST /api/auth/signup  { "email": "..." }  → { "student_id": "...", "email": "..." }
GET  /api/auth/me?student_id=...           → { "student_id": "...", "email": "..." }

student_id is derived deterministically from the email address using a SHA-256
hash so the same email always maps to the same student in Cognee.  No passwords,
no sessions, no JWTs — the student_id is stored in the browser and sent with
every subsequent API call.
"""

from __future__ import annotations

import hashlib

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _student_id_from_email(email: str) -> str:
    """Derive a stable, URL-safe student identifier from an email address or name."""
    return "s_" + hashlib.sha256(email.lower().strip().encode()).hexdigest()[:16]


# ─────────────────────────────────────────────
# Request / Response models
# ─────────────────────────────────────────────

class AuthRequest(BaseModel):
    # Field is kept as "email" for backward compatibility with frontend
    # but now accepts any non-empty string (e.g. arbitrary student names).
    email: str = Field(min_length=1, max_length=100)


class AuthResponse(BaseModel):
    student_id: str
    email: str


# ─────────────────────────────────────────────
# POST /api/auth/login
# ─────────────────────────────────────────────

@router.post("/login", response_model=AuthResponse)
async def login(request: AuthRequest) -> AuthResponse:
    """Accept an email address and return the corresponding student_id.

    This is intentionally passwordless — it matches the existing UI which
    only collects an email address.  All session data is keyed on student_id
    in Cognee, so returning the same id for the same email is sufficient for
    continuity across sessions.
    """
    return AuthResponse(
        student_id=_student_id_from_email(request.email),
        email=str(request.email),
    )


# ─────────────────────────────────────────────
# POST /api/auth/signup
# ─────────────────────────────────────────────

@router.post("/signup", response_model=AuthResponse)
async def signup(request: AuthRequest) -> AuthResponse:
    """Register a new student — same logic as login (identity is derived from email)."""
    return AuthResponse(
        student_id=_student_id_from_email(request.email),
        email=str(request.email),
    )


# ─────────────────────────────────────────────
# GET /api/auth/me
# ─────────────────────────────────────────────

@router.get("/me", response_model=AuthResponse)
async def me(student_id: str) -> AuthResponse:
    """Validate that a student_id looks well-formed (used on page load to
    verify a stored credential is still usable).

    Since there is no server-side session store the only validation we can do
    is a format check.  A real auth layer would verify a JWT here.
    """
    if not student_id.startswith("s_") or len(student_id) != 18:
        raise HTTPException(status_code=401, detail="Invalid student_id")
    return AuthResponse(student_id=student_id, email="")
