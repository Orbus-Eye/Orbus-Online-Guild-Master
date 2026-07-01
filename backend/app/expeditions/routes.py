"""Expedition HTTP routes (Phase 5.5e + ROUND 6B.3 Wave 1.5 over-cap guard).

Route order matters: `/last-completed` and `/replay-last` are registered
BEFORE the `/{expedition_id}` catch-all so FastAPI doesn't capture the
literal segments as a UUID parameter.
"""
from fastapi import APIRouter, Depends

from app.core.database import db
from app.core.security import get_current_user
from app.expeditions.preview import preview_expedition
from app.expeditions.preview_schema import ExpeditionPreviewIn
from app.expeditions.schemas import ExpeditionCreateIn
from app.expeditions.services import (
    get_expedition as svc_get_expedition,
    get_last_completed,
    list_expeditions,
    replay_last,
    start_expedition,
)
from app.guilds.services import user_guild_or_404
from app.territory.cap_guard import over_cap_dep


router = APIRouter(prefix="/api/expeditions", tags=["expeditions"])


@router.post(
    "",
    status_code=201,
    dependencies=[Depends(over_cap_dep("expedition.create"))],
)
async def start_expedition_route(
    payload: ExpeditionCreateIn,
    current_user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, current_user["id"])
    return await start_expedition(db, guild, payload)


@router.post("/preview")
async def preview_expedition_route(
    payload: ExpeditionPreviewIn,
    current_user: dict = Depends(get_current_user),
):
    """Phase 14.3-c — read-only preview: success chance, injury risk,
    expected reward, modifiers list. NEVER writes to DB.
    Wave 1.5 — intentionally NOT gated by over-cap; the FE shows a warning
    banner using the cap_state from the dashboard widget."""
    guild = await user_guild_or_404(db, current_user["id"])
    return await preview_expedition(
        db, guild, payload.dungeon_id, payload.adventurer_ids
    )


@router.get("/last-completed")
async def get_last_completed_route(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    return await get_last_completed(db, guild)


@router.post(
    "/replay-last",
    status_code=201,
    dependencies=[Depends(over_cap_dep("expedition.replay"))],
)
async def replay_last_route(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    return await replay_last(db, guild)


@router.get("")
async def list_expeditions_route(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    return await list_expeditions(db, guild)


@router.get("/{expedition_id}")
async def get_expedition_route(
    expedition_id: str,
    current_user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, current_user["id"])
    return await svc_get_expedition(db, expedition_id, guild)


__all__ = ["router"]
