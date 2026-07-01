"""Modelli Pydantic per il dominio Account."""
from __future__ import annotations

import re
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field

# Regex email pragmatica: accetta anche TLD "riservati" come .test per QA.
_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


def _validate_email(value: str) -> str:
    v = value.strip().lower()
    if not _EMAIL_RE.match(v):
        raise ValueError("Formato email non valido.")
    if len(v) > 254:
        raise ValueError("Email troppo lunga.")
    return v


Email = Annotated[str, AfterValidator(_validate_email)]


# ─── Input ───────────────────────────────────────────────────────────────
class RegisterInput(BaseModel):
    email: Email
    password: str = Field(min_length=8, max_length=128)


class LoginInput(BaseModel):
    email: Email
    password: str = Field(min_length=1, max_length=128)


# ─── Output ──────────────────────────────────────────────────────────────
class UserPublic(BaseModel):
    id: str
    email: str
    role: str
    created_at: str


class AuthResponse(BaseModel):
    user: UserPublic
    access_token: str
    token_type: str = "bearer"
