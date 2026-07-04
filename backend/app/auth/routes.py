"""Auth domain routes (Phase 5.5b + ROUND 11.1 Slice 2 cookie+CSRF migration)."""
import secrets

from fastapi import APIRouter, Depends, Request, Response

from app.auth.schemas import (
    LoginIn,
    LogoutIn,
    PasswordResetConfirmIn,
    PasswordResetRequestIn,
    RefreshIn,
    RegisterIn,
)
from app.auth.services import (
    _consume_refresh_token,
    _revoke_refresh_token,
    authenticate_login,
    confirm_password_reset,
    register_user,
    request_password_reset,
    send_welcome_email_safe,
    user_public,
)
from app.core.config import ACCESS_TOKEN_TTL_DAYS
from app.core.database import db
from app.core.security import (
    ACCESS_COOKIE_NAME,
    CSRF_COOKIE_NAME,
    _cookie_secure_flag,
    create_access_token,
    get_current_user,
    validate_password_strength,
)


router = APIRouter(prefix="/api/auth", tags=["auth"])

_ACCESS_MAX_AGE = ACCESS_TOKEN_TTL_DAYS * 24 * 3600


def _set_access_cookie(resp: Response, token: str) -> None:
    """ROUND 11.1 Slice 2 — httpOnly access cookie."""
    resp.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=token,
        max_age=_ACCESS_MAX_AGE,
        httponly=True,
        secure=_cookie_secure_flag(),
        samesite="lax",
        path="/",
    )


def _set_csrf_cookie(resp: Response, token: str) -> None:
    """ROUND 11.1 Slice 2 — NON-httpOnly csrf cookie (double-submit pattern).

    The frontend reads this cookie via JS, echoes it in X-CSRF-Token header
    on mutating requests; the server validates equality (no DB lookup).
    """
    resp.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=token,
        max_age=_ACCESS_MAX_AGE,
        httponly=False,
        secure=_cookie_secure_flag(),
        samesite="lax",
        path="/",
    )


def _clear_auth_cookies(resp: Response) -> None:
    resp.delete_cookie(ACCESS_COOKIE_NAME, path="/")
    resp.delete_cookie(CSRF_COOKIE_NAME, path="/")


@router.post("/register", status_code=201)
async def register(payload: RegisterIn, request: Request, response: Response):
    validate_password_strength(payload.password)
    email = payload.email.lower().strip()
    username = payload.username.strip()
    user_doc, access, refresh = await register_user(db, email, username, payload.password)
    _set_access_cookie(response, access)
    _set_csrf_cookie(response, secrets.token_hex(32))
    await send_welcome_email_safe(
        email, username,
        accept_language=request.headers.get("accept-language"),
    )
    # ROUND 17.1 P0.3 — funnel event REGISTERED (idempotente per user).
    try:
        from app.audit.first_events import emit_first_event
        await emit_first_event(
            db, event_type="REGISTERED",
            user_id=user_doc.get("id"),
        )
    except Exception:  # noqa: BLE001
        pass
    return {
        "access_token": access,    # legacy bearer (14gg fallback)
        "refresh_token": refresh,
        "token_type": "bearer",
        "user": user_public(user_doc),
    }


@router.post("/login")
async def login(payload: LoginIn, response: Response):
    email = payload.email.lower().strip()
    user, access, refresh = await authenticate_login(db, email, payload.password)
    _set_access_cookie(response, access)
    _set_csrf_cookie(response, secrets.token_hex(32))
    return {
        "access_token": access,    # legacy bearer (14gg fallback)
        "refresh_token": refresh,
        "token_type": "bearer",
        "user": user_public(user),
    }


@router.get("/csrf")
async def get_csrf(request: Request, response: Response):
    """ROUND 11.1 Slice 2 — emit a fresh CSRF token (double-submit cookie).

    Idempotent: calling multiple times rotates the token. The frontend
    fetches this at app boot + after login + on 403 csrf retry.
    """
    existing = request.cookies.get(CSRF_COOKIE_NAME)
    token = existing if existing and len(existing) == 64 else secrets.token_hex(32)
    _set_csrf_cookie(response, token)
    return {"csrf_token": token}


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    return {"user": user_public(current_user)}


@router.post("/refresh")
async def refresh_token_endpoint(payload: RefreshIn, response: Response):
    user = await _consume_refresh_token(db, payload.refresh_token)
    new_access = create_access_token(user["id"])
    _set_access_cookie(response, new_access)
    return {
        "access_token": new_access,
        "token_type": "bearer",
        "user": user_public(user),
    }


@router.post("/logout")
async def logout(payload: LogoutIn | None = None, response: Response = None):
    """ROUND 11.1 Slice 2 — clears auth cookies + revokes refresh token.

    Safe to call without a payload body (idempotent). CSRF-exempt to allow
    the frontend to logout even if the CSRF cookie was already expired.
    """
    revoked = False
    if payload and payload.refresh_token:
        revoked = await _revoke_refresh_token(db, payload.refresh_token)
    _clear_auth_cookies(response)
    return {"revoked": revoked}


@router.post("/password-reset/request")
async def password_reset_request(payload: PasswordResetRequestIn, request: Request):
    """Always returns 200 to avoid email enumeration."""
    email = payload.email.lower().strip()
    await request_password_reset(
        db, email,
        accept_language=request.headers.get("accept-language"),
    )
    return {"status": "ok"}


@router.post("/password-reset/confirm")
async def password_reset_confirm(payload: PasswordResetConfirmIn):
    validate_password_strength(payload.new_password)
    await confirm_password_reset(db, payload.token, payload.new_password)
    return {"status": "ok"}


__all__ = ["router"]
