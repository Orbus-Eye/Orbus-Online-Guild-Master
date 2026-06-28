"""Auth services (Phase 5.5b).

Pure business logic for auth endpoints. All functions accept the Motor `db`
handle and the current UTC time as parameters where relevant, so they remain
unit-testable without monkey-patching globals. Behavior is byte-identical to
the previous inline implementation in `server.py`.
"""
import hashlib
import logging
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.shared.constants import (
    LOGIN_LOCK_DURATION_MINUTES,
    LOGIN_LOCK_MAX_ATTEMPTS,
    PASSWORD_RESET_TTL_MINUTES,
    REFRESH_TOKEN_TTL_DAYS,
)

logger = logging.getLogger("orbus")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def user_public(doc: dict) -> dict:
    """Project a Mongo user document to its public JSON shape."""
    return {
        "id": doc["id"],
        "email": doc["email"],
        "username": doc["username"],
        "is_admin": doc.get("is_admin", False),
        "created_at": doc["created_at"],
    }


# ─── Opaque token helpers (refresh + password reset) ─────────────────────────
def _hash_token(token: str) -> str:
    """SHA-256 hex digest. Used for opaque refresh/reset tokens at rest."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _new_opaque_token() -> str:
    """URL-safe 256-bit opaque token."""
    return secrets.token_urlsafe(32)


# ─── Login lockout ───────────────────────────────────────────────────────────
async def _check_login_lock(db, email: str) -> None:
    row = await db.login_attempts.find_one({"email": email})
    if not row:
        return
    locked_until = row.get("locked_until")
    if locked_until and isinstance(locked_until, datetime):
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)
        if locked_until > utc_now():
            remaining = max(1, int((locked_until - utc_now()).total_seconds()))
            raise HTTPException(
                status_code=429,
                detail="Too many failed login attempts. Try again later.",
                headers={"Retry-After": str(remaining)},
            )


async def _record_login_failure(db, email: str) -> None:
    now = utc_now()
    row = await db.login_attempts.find_one_and_update(
        {"email": email},
        {
            "$inc": {"failed_count": 1},
            "$set": {"last_attempt_at": now},
            "$setOnInsert": {"email": email, "created_at": now},
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    if row.get("failed_count", 0) >= LOGIN_LOCK_MAX_ATTEMPTS:
        lock_until = now + timedelta(minutes=LOGIN_LOCK_DURATION_MINUTES)
        await db.login_attempts.update_one(
            {"email": email},
            {"$set": {"locked_until": lock_until, "last_attempt_at": now}},
        )


async def _reset_login_attempts(db, email: str) -> None:
    await db.login_attempts.delete_one({"email": email})


# ─── Refresh tokens ──────────────────────────────────────────────────────────
async def _create_refresh_token(db, user_id: str) -> str:
    token = _new_opaque_token()
    now = utc_now()
    await db.refresh_tokens.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "token_hash": _hash_token(token),
        "created_at": now,
        "expires_at": now + timedelta(days=REFRESH_TOKEN_TTL_DAYS),
        "revoked": False,
    })
    return token


async def _consume_refresh_token(db, token: str) -> dict:
    row = await db.refresh_tokens.find_one({"token_hash": _hash_token(token)})
    if not row or row.get("revoked"):
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    expires_at = row.get("expires_at")
    if expires_at and isinstance(expires_at, datetime):
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= utc_now():
            raise HTTPException(status_code=401, detail="Refresh token expired")
    user = await db.users.find_one({"id": row["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def _revoke_refresh_token(db, token: str) -> bool:
    res = await db.refresh_tokens.update_one(
        {"token_hash": _hash_token(token)},
        {"$set": {"revoked": True, "revoked_at": utc_now()}},
    )
    return res.modified_count > 0


async def _revoke_all_refresh_tokens(db, user_id: str) -> int:
    res = await db.refresh_tokens.update_many(
        {"user_id": user_id, "revoked": False},
        {"$set": {"revoked": True, "revoked_at": utc_now()}},
    )
    return res.modified_count


# ─── High-level service operations used by routes ────────────────────────────
async def register_user(db, email: str, username: str, password: str) -> tuple[dict, str, str]:
    """Insert a new user. Raises 409 on duplicate. Returns (user_doc, access, refresh)."""
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    now = utc_now()
    user_id = str(uuid.uuid4())
    # ROUND 11.1 B6 — explicit `is_test_user` flag instead of inferring
    # from `APP_ENV == "development"`. Any registration with an
    # `@orbus.test` domain (or other documented test-only domain) is
    # flagged so leaderboard / auction / chronicle filters can exclude
    # them in prod without depending on the environment variable.
    is_test = email.lower().endswith("@orbus.test")
    user_doc = {
        "id": user_id,
        "email": email,
        "username": username,
        "password_hash": hash_password(password),
        "is_admin": False,
        "is_test_user": is_test,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    try:
        await db.users.insert_one(user_doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Email already registered")

    access = create_access_token(user_id)
    refresh = await _create_refresh_token(db, user_id)
    return user_doc, access, refresh


async def authenticate_login(db, email: str, password: str) -> tuple[dict, str, str]:
    """Login flow with lockout. Returns (user_doc, access, refresh) or raises."""
    await _check_login_lock(db, email)
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(password, user["password_hash"]):
        await _record_login_failure(db, email)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    await _reset_login_attempts(db, email)
    access = create_access_token(user["id"])
    refresh = await _create_refresh_token(db, user["id"])
    return user, access, refresh


async def request_password_reset(db, email: str, *, accept_language: str | None = None) -> None:
    """Always returns silently — caller must respond with HTTP 200 regardless
    of whether the email exists, to prevent account enumeration.

    Phase 9.3: sends the reset link via the configured EmailProvider. In
    development (`EMAIL_PROVIDER=console`) the provider logs the message
    (token still visible in stdout). In production with `EMAIL_PROVIDER=resend`
    the real email is sent; missing API key triggers NoopProvider which logs
    an error but never raises (no enumeration).
    """
    from app.core.email import detect_locale, get_email_provider
    from app.core.email_templates import render_password_reset

    user = await db.users.find_one({"email": email})
    if not user:
        return
    token = _new_opaque_token()
    now = utc_now()
    await db.password_reset_tokens.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "token_hash": _hash_token(token),
        "created_at": now,
        "expires_at": now + timedelta(minutes=PASSWORD_RESET_TTL_MINUTES),
        "used": False,
    })

    lang = detect_locale(accept_language)
    app_base = os.environ.get("APP_BASE_URL", "").rstrip("/")
    reset_url = f"{app_base}/password-reset/confirm?token={token}" if app_base else token

    provider = get_email_provider()
    subject, html, text = render_password_reset(lang, reset_url)
    try:
        await provider.send(to=email, subject=subject, html=html, text=text)
    except Exception as exc:  # provider must not crash the request flow
        logger.error("[PASSWORD-RESET] provider raised: %s", exc)

    # Phase 9.3.2 — NEVER log the raw token. We emit only an sha256[:12]
    # fingerprint, which is enough for log correlation but useless to an
    # attacker (cannot be replayed into /password-reset/confirm). Applies
    # uniformly to every provider — `console` mode is no longer a free pass.
    token_fingerprint = hashlib.sha256(token.encode()).hexdigest()[:12]
    logger.info(
        "[PASSWORD-RESET] email=%s provider=%s token_hash=%s expires_in=%dmin",
        email, provider.name, token_fingerprint, PASSWORD_RESET_TTL_MINUTES,
    )


async def send_welcome_email_safe(email: str, username: str, *, accept_language: str | None = None) -> bool:
    """Phase 9.3 — Fire-and-forget welcome email after register().

    NEVER raises: a mailer failure must NOT fail registration. Returns the
    boolean from the provider so callers can log a metric but should ignore
    it on the hot path.
    """
    from app.core.email import detect_locale, get_email_provider
    from app.core.email_templates import render_welcome

    if (os.environ.get("SEND_WELCOME_EMAIL", "true").strip().lower() in ("false", "0", "no")):
        return False
    lang = detect_locale(accept_language)
    app_url = (os.environ.get("APP_BASE_URL") or "").rstrip("/") or "/"
    provider = get_email_provider()
    subject, html, text = render_welcome(lang, app_url, username)
    try:
        return await provider.send(to=email, subject=subject, html=html, text=text)
    except Exception as exc:
        logger.warning("[WELCOME-EMAIL] provider raised for %s: %s", email, exc)
        return False


async def confirm_password_reset(db, token: str, new_password: str) -> None:
    """Apply a new password using an opaque reset token. Caller must have
    already validated `new_password` strength. Revokes ALL refresh tokens for
    the user on success."""
    row = await db.password_reset_tokens.find_one({"token_hash": _hash_token(token)})
    if not row or row.get("used"):
        raise HTTPException(status_code=400, detail="Invalid or already-used reset token")
    expires_at = row.get("expires_at")
    if expires_at and isinstance(expires_at, datetime):
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= utc_now():
            raise HTTPException(status_code=400, detail="Reset token expired")

    user = await db.users.find_one({"id": row["user_id"]})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid reset token")

    now = utc_now()
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "password_hash": hash_password(new_password),
            "updated_at": now.isoformat(),
        }},
    )
    await db.password_reset_tokens.update_one(
        {"id": row["id"]},
        {"$set": {"used": True, "used_at": now}},
    )
    await _revoke_all_refresh_tokens(db, user["id"])
    await _reset_login_attempts(db, user["email"])


__all__ = [
    "utc_now",
    "user_public",
    "_hash_token",
    "_new_opaque_token",
    "_check_login_lock",
    "_record_login_failure",
    "_reset_login_attempts",
    "_create_refresh_token",
    "_consume_refresh_token",
    "_revoke_refresh_token",
    "_revoke_all_refresh_tokens",
    "register_user",
    "authenticate_login",
    "request_password_reset",
    "send_welcome_email_safe",
    "confirm_password_reset",
]
