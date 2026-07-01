"""ROUND 15 — Phase 3 / Task 11 — Achievement HTTP routes."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_user
from app.core.database import db
from app.guilds.services import user_guild_or_404

from .services import (
    get_progress_for_guild,
    get_summary_for_guild,
    list_catalog,
)


router = APIRouter(prefix="/api/achievements", tags=["achievements"])


@router.get("/catalog")
async def get_catalog(
    state: Optional[str] = Query(
        None,
        description="Filter: 'in_progress' (hide hidden) | 'completed' (only completed) | None (all public+visible)",
    ),
    category: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    guild_id: Optional[str] = None
    try:
        guild = await user_guild_or_404(db, current_user["id"])
        guild_id = guild["id"]
    except Exception:  # noqa: BLE001
        # No guild → still allow catalog read (player onboarding flow).
        guild_id = None
    items = await list_catalog(db, state=state, category=category, guild_id=guild_id)
    return {"achievements": items, "count": len(items)}


@router.get("/progress")
async def get_progress(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    rows = await get_progress_for_guild(db, guild["id"])
    return {"progress": rows, "count": len(rows)}


@router.get("/summary")
async def get_summary(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    return await get_summary_for_guild(db, guild)


__all__ = ["router"]
