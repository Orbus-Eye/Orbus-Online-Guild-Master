"""Router HTTP per il dominio gilde."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user
from app.guilds.models import GuildCreateInput, GuildPublic
from app.guilds.services import create_guild, get_my_guild, _to_public

router = APIRouter(prefix="/api/guilds", tags=["guilds"])


@router.post("", response_model=GuildPublic, status_code=201)
async def create(
    payload: GuildCreateInput,
    user: dict = Depends(get_current_user),
) -> GuildPublic:
    guild = await create_guild(user["id"], payload.name, payload.description)
    return GuildPublic(**_to_public(guild))


@router.get("/mine", response_model=GuildPublic)
async def mine(user: dict = Depends(get_current_user)) -> GuildPublic:
    guild = await get_my_guild(user["id"])
    if not guild:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nessuna gilda trovata per questo utente.",
        )
    return GuildPublic(**_to_public(guild))


# Alias per compatibilità con il problem statement (GET /api/guilds/me)
@router.get("/me", response_model=GuildPublic, include_in_schema=False)
async def me_alias(user: dict = Depends(get_current_user)) -> GuildPublic:
    return await mine(user)
