"""Guilds routes (Phase 5.5c).

Mounted under prefix `/api/guilds`. Endpoint paths, payloads and status codes
are preserved byte-identical with the previous inline implementation in
`server.py`.
"""
from fastapi import APIRouter, Depends

from app.core.database import db
from app.core.security import get_current_user
from app.expeditions.services import complete_due_expeditions
from app.guilds.schemas import GuildCreateIn
from app.guilds.services import (
    compute_dashboard_stats,
    create_guild_for_user,
    guild_public,
    user_guild_or_404,
)


router = APIRouter(prefix="/api/guilds", tags=["guilds"])


@router.post("", status_code=201)
async def create_guild(
    payload: GuildCreateIn, current_user: dict = Depends(get_current_user)
):
    guild_doc = await create_guild_for_user(
        db, current_user["id"], payload.name, payload.description
    )
    return {"guild": guild_public(guild_doc)}


@router.get("/me")
async def get_my_guild(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    # Phase 5.5e: lazy completion sweep (formerly imported lazily from server.py
    # to break a circular dep; now imported eagerly from `app.expeditions.services`).
    await complete_due_expeditions(db, guild["id"])
    # Re-fetch guild after sweep (gold/level may have changed)
    guild = await user_guild_or_404(db, current_user["id"])

    payload = guild_public(guild)
    stats = await compute_dashboard_stats(db, guild)
    payload.update(stats)
    return {"guild": payload}


__all__ = ["router"]
