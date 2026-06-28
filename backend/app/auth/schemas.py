"""Auth domain Pydantic schemas (Phase 5.5b).

These are the exact schemas previously inlined in server.py. Field constraints
and validators are preserved verbatim to keep request/response behavior
identical (HTTP 422 for shape errors, HTTP 400 for password policy enforced at
the route level).
"""
from typing import Annotated, Optional

from email_validator import EmailNotValidError, validate_email
from pydantic import BaseModel, BeforeValidator, Field


def _normalize_email(v):
    if not isinstance(v, str):
        raise ValueError("email must be a string")
    try:
        result = validate_email(
            v.strip(),
            check_deliverability=False,
            test_environment=True,
        )
    except EmailNotValidError as e:
        raise ValueError(str(e))
    return result.normalized.lower()


# Lenient email type: validates format but allows reserved TLDs like `.test`
OrbusEmail = Annotated[str, BeforeValidator(_normalize_email)]


class RegisterIn(BaseModel):
    email: OrbusEmail
    # Phase 9.3.1 — strict username pattern to prevent HTML/header injection
    # in welcome emails. Allowed: ASCII letters, digits, underscore, hyphen,
    # space. Length 3-32 (raised from 2 to leave room for sane bot detection).
    # Existing accounts with non-conforming usernames stay valid (validation
    # only runs on register).
    username: str = Field(
        min_length=3, max_length=32,
        pattern=r"^[A-Za-z0-9_\- ]+$",
    )
    # Password is validated in the route handler (HTTP 400) — not via Pydantic (422)
    password: str = Field(max_length=128)


class LoginIn(BaseModel):
    email: OrbusEmail
    password: str = Field(min_length=1, max_length=128)


class RefreshIn(BaseModel):
    refresh_token: str = Field(min_length=8, max_length=256)


class LogoutIn(BaseModel):
    # ROUND 11.1 Slice 2 P1 — `refresh_token` is now OPTIONAL.
    # Logout must succeed (clearing cookies) even when called without a
    # body, with `{}`, or with the field omitted. Validation is preserved
    # ONLY for the case where the field is actually provided.
    refresh_token: Optional[str] = Field(default=None, min_length=8, max_length=256)


class PasswordResetRequestIn(BaseModel):
    email: OrbusEmail


class PasswordResetConfirmIn(BaseModel):
    token: str = Field(min_length=8, max_length=256)
    # new_password is validated in the route handler (HTTP 400) — not via Pydantic (422)
    new_password: str = Field(max_length=128)


__all__ = [
    "OrbusEmail",
    "RegisterIn",
    "LoginIn",
    "RefreshIn",
    "LogoutIn",
    "PasswordResetRequestIn",
    "PasswordResetConfirmIn",
]
