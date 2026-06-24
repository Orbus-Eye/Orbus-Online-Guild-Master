"""Dungeons routes (Phase 5.5c.2)."""
from typing import Optional

from fastapi import APIRouter, Depends

from app.core.database import db
from app.core.security import get_optional_user
from app.dungeons.services import list_dungeons_for_guild


router = APIRouter(prefix="/api/dungeons", tags=["dungeons"])


@router.get("")
async def list_dungeons(current_user: Optional[dict] = Depends(get_optional_user)):
    guild = None
    if current_user:
        guild = await db.guilds.find_one(
            {"owner_user_id": current_user["id"]}, {"_id": 0}
        )
    return {"dungeons": await list_dungeons_for_guild(db, guild)}


__all__ = ["router"]
