"""ROUND 6D — Contract routes (read + claim)."""
from fastapi import APIRouter, Depends

from app.contracts.services import (
    claim_daily_contract,
    claim_milestone,
    claim_weekly_contract,
    get_milestones,
    get_today_contracts,
    get_weekly_contracts,
)
from app.core.database import db
from app.core.security import get_current_user
from app.guilds.services import user_guild_or_404


router = APIRouter(prefix="/api/contracts", tags=["contracts"])


@router.get("/daily")
async def get_daily(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    return await get_today_contracts(db, guild["id"])


@router.get("/weekly")
async def get_weekly(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    return await get_weekly_contracts(db, guild["id"])


@router.get("/milestones")
async def get_milestones_route(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    return await get_milestones(db, guild["id"])


@router.post("/daily/{slug}/claim")
async def post_claim_daily(slug: str, current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    return await claim_daily_contract(
        db, guild_id=guild["id"], actor_user_id=current_user["id"], slug=slug,
    )


@router.post("/weekly/{slug}/claim")
async def post_claim_weekly(slug: str, current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    return await claim_weekly_contract(
        db, guild_id=guild["id"], actor_user_id=current_user["id"], slug=slug,
    )


@router.post("/milestones/{slug}/claim")
async def post_claim_milestone(slug: str, current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    return await claim_milestone(
        db, guild_id=guild["id"], actor_user_id=current_user["id"], slug=slug,
    )


__all__ = ["router"]
