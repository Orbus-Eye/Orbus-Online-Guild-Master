"""Inventory routes (Phase 5.5c.2)."""
from fastapi import APIRouter, Depends

from app.core.database import db
from app.core.security import get_current_user
from app.guilds.services import user_guild_or_404
from app.inventory.services import list_inventory_for_guild


router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.get("")
async def list_inventory(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    return {"inventory": await list_inventory_for_guild(db, guild["id"])}


__all__ = ["router"]
