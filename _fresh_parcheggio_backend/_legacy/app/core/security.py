"""Auth security helpers: bcrypt, JWT, password rules, current-user dep."""
import hashlib
import logging
import os
import re
from datetime import datetime, timezone, timedelta
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import (
    JWT_SECRET,
    JWT_ALGORITHM,
    ACCESS_TOKEN_TTL_DAYS,
)
from app.core.database import db


logger = logging.getLogger("orbus.auth")

# ROUND 11.1 Slice 2 — auth migration cookie/CSRF config.
ACCESS_COOKIE_NAME = "access_token"
CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
# httpOnly + Secure + SameSite=Lax. Secure is env-gated so localhost dev still
# works (`Secure` cookies require https; preview/prod set APP_ENV=production).
def _cookie_secure_flag() -> bool:
    return os.environ.get("APP_ENV", "development").lower() == "production"


PASSWORD_REGEX_LETTER = re.compile(r"[A-Za-z]")
PASSWORD_REGEX_DIGIT = re.compile(r"\d")
PASSWORD_RULES_MESSAGE = (
    "Password must be at least 8 characters and contain a letter and a digit"
)


# ─── Password hashing ────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def validate_password_strength(password: str) -> None:
    """Raise HTTP 400 if password does not satisfy the Phase-5 policy."""
    if (
        len(password) < 8
        or not PASSWORD_REGEX_LETTER.search(password)
        or not PASSWORD_REGEX_DIGIT.search(password)
    ):
        raise HTTPException(status_code=400, detail=PASSWORD_RULES_MESSAGE)


# ─── JWT ────────────────────────────────────────────────────────────────────
def create_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=ACCESS_TOKEN_TTL_DAYS)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ─── Bearer scheme + deps ────────────────────────────────────────────────────
# auto_error=False so missing/empty Authorization headers raise our own HTTP 401
# (FastAPI's HTTPBearer with auto_error=True would emit 403). This preserves
# the pre-refactor behavior expected by tests.
bearer_scheme = HTTPBearer(auto_error=False)
optional_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    """ROUND 11.1 Slice 2 — dual auth: cookie first, Bearer fallback.

    Order:
      1. Try `access_token` httpOnly cookie (new flow).
      2. Fallback to `Authorization: Bearer` (legacy 14-day window). Emits
         structured `auth.legacy_bearer_usage` log entry with a hashed
         user id so we can monitor how many clients still use Bearer.

    Auth method is attached to `request.state.auth_method` ∈ {"cookie",
    "bearer"} for downstream consumers (e.g. CSRF middleware).
    """
    token: str | None = None
    method: str = "none"
    cookie_tok = request.cookies.get(ACCESS_COOKIE_NAME)
    if cookie_tok:
        token = cookie_tok
        method = "cookie"
    elif creds is not None and creds.credentials:
        token = creds.credentials
        method = "bearer"

    if not token:
        raise HTTPException(status_code=401, detail={
            "code": "auth.missing",
            "user_message": "Sessione non attiva. Effettua il login.",
        })

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail={
            "code": "auth.expired",
            "user_message": "Sessione scaduta. Effettua di nuovo l'accesso.",
        })
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail={
            "code": "auth.invalid",
            "user_message": "Token non valido.",
        })

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail={
            "code": "auth.invalid_type", "user_message": "Token type invalid.",
        })
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail={
            "code": "auth.invalid", "user_message": "Token non valido.",
        })
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail={
            "code": "auth.user_not_found",
            "user_message": "Utente non trovato.",
        })

    request.state.auth_method = method
    request.state.user_id = user_id
    if method == "bearer":
        # ROUND 11.1 Slice 2 — Bearer fallback metric. Hashed user_id so the
        # log doesn't leak the internal UUID across log aggregators.
        uid_hash = hashlib.sha256(user_id.encode()).hexdigest()[:12]
        logger.info(
            "auth.legacy_bearer_usage",
            extra={"event": "auth.legacy_bearer_usage",
                   "user_id_hash": uid_hash,
                   "path": request.url.path,
                   "method": request.method},
        )
    return user


async def get_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Admin guard. ROUND 11.2 TASK 5a:
    - Primary: user.is_admin == True (DB flag)
    - Fallback: ADMIN_EMAILS env allowlist (comma-separated, lowercase)
    Both can authorize; either match grants admin scope.

    Non-admin → 403 with structured `admin.forbidden` code.
    """
    if current_user.get("is_admin") is True:
        return current_user
    # ADMIN_EMAILS env allowlist (bootstrap-safe for prod first admin onboarding).
    raw = os.environ.get("ADMIN_EMAILS", "") or ""
    allowed = {e.strip().lower() for e in raw.split(",") if e.strip()}
    email = (current_user.get("email") or "").strip().lower()
    if email and email in allowed:
        return current_user
    raise HTTPException(
        status_code=403,
        detail={
            "code": "admin.forbidden",
            "user_message": "Accesso admin richiesto.",
        },
    )


async def get_optional_user(
    request: Request,
    creds: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer_scheme),
) -> Optional[dict]:
    token = request.cookies.get(ACCESS_COOKIE_NAME)
    if not token and creds is not None and creds.credentials:
        token = creds.credentials
    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        return await db.users.find_one({"id": user_id}, {"_id": 0})
    except Exception:
        return None


__all__ = [
    "hash_password",
    "verify_password",
    "validate_password_strength",
    "create_access_token",
    "decode_token",
    "bearer_scheme",
    "optional_bearer_scheme",
    "get_current_user",
    "get_admin_user",
    "get_optional_user",
    "PASSWORD_REGEX_LETTER",
    "PASSWORD_REGEX_DIGIT",
    "PASSWORD_RULES_MESSAGE",
]
