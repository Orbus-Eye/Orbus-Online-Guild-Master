"""Squads HTTP routes (ROUND 6A.2a)."""
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.database import db
from app.core.security import get_current_user
from app.guilds.services import user_guild_or_404
from app.squads.schemas import SquadCreateIn, SquadUpdateIn
from app.squads.services import (
    archive_squad,
    create_squad,
    get_squad,
    list_squads,
    update_squad,
)


router = APIRouter(prefix="/api/squads", tags=["squads"])


@router.get("")
async def list_my_squads(
    type: Optional[str] = Query(None, alias="type"),
    current_user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, current_user["id"])
    return {"squads": await list_squads(db, guild["id"], squad_type=type)}


@router.get("/{squad_id}")
async def get_my_squad(squad_id: str, current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    return await get_squad(db, guild["id"], squad_id)


@router.post("", status_code=201)
async def create_my_squad(
    payload: SquadCreateIn, current_user: dict = Depends(get_current_user)
):
    guild = await user_guild_or_404(db, current_user["id"])
    return await create_squad(
        db, owner_user_id=current_user["id"], guild_id=guild["id"], payload=payload
    )


@router.patch("/{squad_id}")
async def update_my_squad(
    squad_id: str,
    payload: SquadUpdateIn,
    current_user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, current_user["id"])
    return await update_squad(
        db,
        owner_user_id=current_user["id"],
        guild_id=guild["id"],
        squad_id=squad_id,
        payload=payload,
    )


@router.delete("/{squad_id}")
async def archive_my_squad(
    squad_id: str, current_user: dict = Depends(get_current_user)
):
    guild = await user_guild_or_404(db, current_user["id"])
    return await archive_squad(
        db,
        owner_user_id=current_user["id"],
        guild_id=guild["id"],
        squad_id=squad_id,
    )


__all__ = ["router"]
