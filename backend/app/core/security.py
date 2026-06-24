"""Auth security helpers: bcrypt, JWT, password rules, current-user dep."""
import re
from datetime import datetime, timezone, timedelta
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import (
    JWT_SECRET,
    JWT_ALGORITHM,
    ACCESS_TOKEN_TTL_DAYS,
)
from app.core.database import db


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
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(creds.credentials)
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def get_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


async def get_optional_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer_scheme),
) -> Optional[dict]:
    if creds is None or not creds.credentials:
        return None
    try:
        payload = decode_token(creds.credentials)
        if payload.get("type") != "access":
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        return await db.users.find_one({"id": user_id}, {"_id": 0})
    except HTTPException:
        return None
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
