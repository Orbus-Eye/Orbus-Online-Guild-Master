"""ROUND 6B.1 — Territory HTTP routes.

3 endpoints, all JWT-required, all scoped to the caller's guild.
No PII leak: response is restricted to the public shape (no owner email,
no Mongo `_id`).
"""
from fastapi import APIRouter, Depends

from app.core.database import db
from app.core.security import get_current_user
from app.guilds.services import user_guild_or_404
from app.territory.schemas import PurchaseIn, UpgradeIn
from app.territory.services import (
    get_territory,
    purchase_structure,
    upgrade_structure,
)


router = APIRouter(prefix="/api/territory", tags=["territory"])


@router.get("")
async def get_my_territory(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    territory = await get_territory(db, guild["id"])
    return {"territory": territory}


@router.post("/purchase")
async def purchase(
    payload: PurchaseIn, current_user: dict = Depends(get_current_user)
):
    guild = await user_guild_or_404(db, current_user["id"])
    territory = await purchase_structure(db, guild, payload.structure_slug)
    return {"territory": territory}


@router.post("/upgrade")
async def upgrade(
    payload: UpgradeIn, current_user: dict = Depends(get_current_user)
):
    guild = await user_guild_or_404(db, current_user["id"])
    territory = await upgrade_structure(db, guild, payload.structure_slug)
    return {"territory": territory}
