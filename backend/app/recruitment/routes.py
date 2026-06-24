"""Recruitment routes (Phase 5.5c.3)."""
from fastapi import APIRouter, Depends

from app.adventurers.services import adventurer_public
from app.core.database import db
from app.core.security import get_current_user
from app.guilds.services import user_guild_or_404
from app.recruitment.schemas import RecruitIn
from app.recruitment.services import (
    generate_candidates_for_guild,
    recruit_from_offer,
)


router = APIRouter(prefix="/api/recruitment", tags=["recruitment"])


@router.get("/candidates")
async def get_recruitment_candidates(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    return await generate_candidates_for_guild(db, guild)


@router.post("/recruit", status_code=201)
async def recruit_adventurer(
    payload: RecruitIn, current_user: dict = Depends(get_current_user)
):
    guild = await user_guild_or_404(db, current_user["id"])
    adventurer_doc, updated_guild = await recruit_from_offer(
        db, guild, payload.candidate_id
    )
    return {
        "adventurer": adventurer_public(adventurer_doc),
        "guild": {"gold": updated_guild["gold"]},
    }


__all__ = ["router"]
