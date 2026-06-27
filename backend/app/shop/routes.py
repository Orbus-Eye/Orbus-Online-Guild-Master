"""Phase 19.4b — Shop routes. NPC system shop with daily offer rotation.

All endpoints require JWT bearer.
"""
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.database import db
from app.core.security import get_current_user
from app.guilds.services import user_guild_or_404
from app.shop.services import (
    MAX_TX_QUANTITY,
    buy_from_shop,
    get_or_seed_daily_offers,
    offer_public,
    sell_to_shop,
    _next_reset_at,
    _shop_day_key,
)


router = APIRouter(prefix="/api/shop", tags=["shop"])


class BuyBody(BaseModel):
    offer_id: str = Field(..., min_length=1, max_length=120)
    quantity: int = Field(..., gt=0, le=MAX_TX_QUANTITY)


class SellBody(BaseModel):
    instance_id: str = Field(..., min_length=1, max_length=120)
    quantity: int = Field(default=1, gt=0, le=MAX_TX_QUANTITY)


@router.get("/daily_offers")
async def get_daily_offers(current_user: dict = Depends(get_current_user)):
    """Return today's offers + next reset countdown.

    Idempotent: seeds the day's offer set on first call of the cycle.
    """
    offers = await get_or_seed_daily_offers(db)
    return {
        "day_key": _shop_day_key(),
        "next_reset_at": _next_reset_at().isoformat(),
        "offers": [offer_public(o) for o in offers],
        "count": len(offers),
    }


@router.post("/buy")
async def post_buy(
    body: BuyBody,
    current_user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, current_user["id"])
    return await buy_from_shop(
        db, current_user=current_user, guild=guild,
        offer_id=body.offer_id, quantity=body.quantity,
    )


@router.post("/sell")
async def post_sell(
    body: SellBody,
    current_user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, current_user["id"])
    return await sell_to_shop(
        db, current_user=current_user, guild=guild,
        instance_id=body.instance_id, quantity=body.quantity,
    )


__all__ = ["router"]
