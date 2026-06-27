"""Adventurers + classes routes (Phase 5.5d, Phase 19.2 rename)."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from pymongo import ASCENDING

from app.adventurers.services import (
    class_public,
    list_adventurers_for_guild,
    rename_adventurer,
    trait_preview_for_adventurer,
)
from app.core.database import db
from app.core.security import get_current_user
from app.guilds.services import user_guild_or_404


router = APIRouter(tags=["adventurers"])


class AdventurerRenameIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=30)


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


@router.patch("/api/adventurers/{adventurer_id}/name")
async def patch_adventurer_name(
    adventurer_id: str,
    payload: AdventurerRenameIn,
    current_user: dict = Depends(get_current_user),
):
    """Phase 19.2 — rename adventurer (max 2 lifetime). Free, no gold cost."""
    guild = await user_guild_or_404(db, current_user["id"])
    return await rename_adventurer(db, guild["id"], adventurer_id, payload.name)


__all__ = ["router"]
