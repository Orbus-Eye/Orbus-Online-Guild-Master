"""Phase 14 + 14.1 + 15 — Quests, Weekly Variety, Streak routes."""
from fastapi import APIRouter, Depends

from app.core.database import db
from app.core.security import get_current_user
from app.guilds.services import user_guild_or_404
from app.quests.services import (
    claim_quest,
    claim_streak_reward,
    claim_weekly_quest,
    get_streak,
    get_today_quests,
    get_weekly_quests,
)


router = APIRouter(prefix="/api/quests", tags=["quests"])


@router.get("/today")
async def quests_today(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    return await get_today_quests(db, guild["id"])


@router.post("/claim/{quest_id}")
async def quests_claim(quest_id: str, current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    return await claim_quest(db, guild["id"], quest_id)


# ─── Streak (Phase 15) ─────────────────────────────────────────────────────
@router.get("/streak")
async def quests_streak(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    return await get_streak(db, guild["id"])


@router.post("/streak/claim/{tier}")
async def quests_streak_claim(tier: int, current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    return await claim_streak_reward(db, guild["id"], tier)


# ─── Weekly variety (Phase 14.1) ───────────────────────────────────────────
@router.get("/weekly")
async def quests_weekly(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    return await get_weekly_quests(db, guild["id"])


@router.post("/weekly/claim/{slug}")
async def quests_weekly_claim(slug: str, current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    return await claim_weekly_quest(db, guild["id"], slug)


__all__ = ["router"]
