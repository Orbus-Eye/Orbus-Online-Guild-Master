"""Phase 14 — Daily Quests routes."""
from fastapi import APIRouter, Depends

from app.core.database import db
from app.core.security import get_current_user
from app.guilds.services import user_guild_or_404
from app.quests.services import claim_quest, get_today_quests


router = APIRouter(prefix="/api/quests", tags=["quests"])


@router.get("/today")
async def quests_today(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    return await get_today_quests(db, guild["id"])


@router.post("/claim/{quest_id}")
async def quests_claim(
    quest_id: str, current_user: dict = Depends(get_current_user)
):
    guild = await user_guild_or_404(db, current_user["id"])
    return await claim_quest(db, guild["id"], quest_id)


__all__ = ["router"]
