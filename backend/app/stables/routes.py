"""ROUND 16.3 Phase 8 V1 — Public stables routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.database import db
from app.core.security import get_current_user
from app.guilds.services import user_guild_or_404
from app.stables.models import SetActiveMountPayload
from app.stables.services import (
    claim_starter_mount, get_catalog_with_ownership, get_my_stable,
    list_narrative_rewards_mine, list_narrative_routes,
    set_active_mount, travel_narrative_route,
)


router = APIRouter(prefix="/api/stables", tags=["stables"])


@router.get("/catalog")
async def get_catalog(user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    return await get_catalog_with_ownership(db, guild["id"])


@router.get("/mine")
async def get_mine(user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    return await get_my_stable(db, guild["id"])


@router.post("/set-active")
async def set_active(payload: SetActiveMountPayload,
                     user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    return await set_active_mount(db, guild, payload.mount_slug)


@router.post("/quest/starter/claim")
async def claim_starter(user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    return await claim_starter_mount(db, guild)


@router.get("/narrative-routes")
async def narrative_routes(user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    return await list_narrative_routes(db, guild)


@router.post("/narrative-routes/{route_slug}/travel")
async def travel_route(route_slug: str,
                       user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    return await travel_narrative_route(db, guild, route_slug)


@router.get("/narrative-rewards/mine")
async def narrative_rewards_mine(user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    return await list_narrative_rewards_mine(db, guild["id"])
