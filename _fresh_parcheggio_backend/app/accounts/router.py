"""Router HTTP per il dominio account (auth)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.accounts.models import (
    AuthResponse,
    LoginInput,
    RegisterInput,
    UserPublic,
)
from app.accounts.services import authenticate, create_user, _to_public
from app.core.deps import get_current_user
from app.core.security import create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(payload: RegisterInput) -> AuthResponse:
    user = await create_user(payload.email, payload.password)
    token = create_access_token(user["id"])
    return AuthResponse(user=UserPublic(**_to_public(user)), access_token=token)


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginInput) -> AuthResponse:
    user = await authenticate(payload.email, payload.password)
    token = create_access_token(user["id"])
    return AuthResponse(user=UserPublic(**_to_public(user)), access_token=token)


@router.get("/me", response_model=UserPublic)
async def me(user: dict = Depends(get_current_user)) -> UserPublic:
    return UserPublic(**_to_public(user))
