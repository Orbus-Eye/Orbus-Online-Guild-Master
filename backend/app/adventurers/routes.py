"""Adventurers + classes routes (Phase 5.5d)."""
from fastapi import APIRouter, Depends
from pymongo import ASCENDING

from app.adventurers.services import (
    class_public,
    list_adventurers_for_guild,
    trait_preview_for_adventurer,
)
from app.core.database import db
from app.core.security import get_current_user
from app.guilds.services import user_guild_or_404


router = APIRouter(tags=["adventurers"])


@router.get("/api/adventurer-classes")
async def list_classes():
    classes = (
        await db.adventurer_classes.find({"is_active": True}, {"_id": 0})
        .sort("name", ASCENDING)
        .to_list(100)
    )
    return {"classes": [class_public(c) for c in classes]}


@router.get("/api/adventurers")
async def list_adventurers(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    return {"adventurers": await list_adventurers_for_guild(db, guild["id"])}


@router.get("/api/adventurers/{adventurer_id}/trait-preview")
async def get_trait_preview(
    adventurer_id: str, current_user: dict = Depends(get_current_user)
):
    """Phase 13 — read-only preview of trait effects on stats / power."""
    guild = await user_guild_or_404(db, current_user["id"])
    return await trait_preview_for_adventurer(db, guild["id"], adventurer_id)


__all__ = ["router"]
