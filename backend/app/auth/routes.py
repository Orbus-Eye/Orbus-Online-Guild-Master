"""Auth domain routes (Phase 5.5b).

Mounted under prefix `/api/auth`. Endpoint paths, payloads and status codes
are preserved byte-identical with the previous implementation in `server.py`.
The router pulls all dependencies from `app.core.*` and `app.auth.services`.
"""
from fastapi import APIRouter, Depends

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
    user_public,
)
from app.core.database import db
from app.core.security import (
    create_access_token,
    get_current_user,
    validate_password_strength,
)


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", status_code=201)
async def register(payload: RegisterIn):
    validate_password_strength(payload.password)
    email = payload.email.lower().strip()
    username = payload.username.strip()
    user_doc, access, refresh = await register_user(db, email, username, payload.password)
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "user": user_public(user_doc),
    }


@router.post("/login")
async def login(payload: LoginIn):
    email = payload.email.lower().strip()
    user, access, refresh = await authenticate_login(db, email, payload.password)
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "user": user_public(user),
    }


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    return {"user": user_public(current_user)}


@router.post("/refresh")
async def refresh_token_endpoint(payload: RefreshIn):
    user = await _consume_refresh_token(db, payload.refresh_token)
    new_access = create_access_token(user["id"])
    return {
        "access_token": new_access,
        "token_type": "bearer",
        "user": user_public(user),
    }


@router.post("/logout")
async def logout(payload: LogoutIn):
    revoked = await _revoke_refresh_token(db, payload.refresh_token)
    return {"revoked": revoked}


@router.post("/password-reset/request")
async def password_reset_request(payload: PasswordResetRequestIn):
    """Always returns 200 to avoid email enumeration."""
    email = payload.email.lower().strip()
    await request_password_reset(db, email)
    return {"status": "ok"}


@router.post("/password-reset/confirm")
async def password_reset_confirm(payload: PasswordResetConfirmIn):
    validate_password_strength(payload.new_password)
    await confirm_password_reset(db, payload.token, payload.new_password)
    return {"status": "ok"}


__all__ = ["router"]
