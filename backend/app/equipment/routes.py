"""Equipment routes (Phase 5.5d)."""
from fastapi import APIRouter, Depends

from app.core.database import db
from app.core.security import get_current_user
from app.equipment.schemas import EquipIn, UnequipIn
from app.equipment.services import (
    equip_item_service,
    get_equipment_for_adventurer,
    unequip_item_service,
)
from app.guilds.services import user_guild_or_404


router = APIRouter(prefix="/api/adventurers", tags=["equipment"])


@router.get("/{adventurer_id}/equipment")
async def get_adventurer_equipment(
    adventurer_id: str, current_user: dict = Depends(get_current_user)
):
    guild = await user_guild_or_404(db, current_user["id"])
    return await get_equipment_for_adventurer(db, guild, adventurer_id)


@router.post("/{adventurer_id}/equip", status_code=201)
async def equip_item(
    adventurer_id: str,
    payload: EquipIn,
    current_user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, current_user["id"])
    return await equip_item_service(db, guild, adventurer_id, payload.item_id, payload.slot)


@router.post("/{adventurer_id}/unequip")
async def unequip_item(
    adventurer_id: str,
    payload: UnequipIn,
    current_user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, current_user["id"])
    return await unequip_item_service(db, guild, adventurer_id, payload.slot)


__all__ = ["router"]
