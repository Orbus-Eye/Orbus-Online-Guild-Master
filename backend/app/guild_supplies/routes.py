"""FASE 10C-F — route Beni di Gilda."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.database import db
from app.core.security import get_current_user
from app.guilds.services import user_guild_or_404
from app.guild_supplies import (
    GUILD_SUPPLIES_CAP,
    MARKET_PACK_GOLD_COST,
    MARKET_PACK_SUPPLIES,
    get_supplies,
    purchase_market_pack,
)

router = APIRouter(prefix="/api/guild-supplies", tags=["guild-supplies"])


@router.get("")
async def read_guild_supplies(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    state = await get_supplies(db, guild["id"])
    balance = state["supplies"]
    max_usable = GUILD_SUPPLIES_CAP - balance
    return {
        **state,
        "market": {
            "pack_supplies": MARKET_PACK_SUPPLIES,
            "gold_cost": MARKET_PACK_GOLD_COST,
            "purchasable": max_usable >= MARKET_PACK_SUPPLIES,
            "lost_if_purchased": max(0, MARKET_PACK_SUPPLIES - max_usable),
        },
    }


@router.post("/market/purchase")
async def buy_supplies_pack(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    return await purchase_market_pack(
        db, guild, actor_user_id=current_user["id"],
    )
