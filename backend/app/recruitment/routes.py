"""Recruitment routes (Phase 5.5c.3 + Phase 11.2 refresh limit + ROUND 6B.2a cap)."""
from fastapi import APIRouter, Depends

from app.adventurers.services import adventurer_public
from app.core.database import db
from app.core.security import get_current_user
from app.guilds.services import user_guild_or_404
from app.recruitment.schemas import RecruitIn
from app.recruitment.services import (
    get_or_init_candidates_for_guild,
    recruit_from_offer,
    refresh_candidates_for_guild,
)
from app.territory.cap_guard import assert_not_over_cap


router = APIRouter(prefix="/api/recruitment", tags=["recruitment"])


@router.get("/candidates")
async def get_recruitment_candidates(current_user: dict = Depends(get_current_user)):
    """GET — returns the current persisted offer (or seeds one on first call).
    Phase 11.2: this endpoint NEVER consumes a refresh or gold."""
    guild = await user_guild_or_404(db, current_user["id"])
    return await get_or_init_candidates_for_guild(db, guild)


@router.post("/refresh", status_code=200)
async def refresh_recruitment_candidates(
    current_user: dict = Depends(get_current_user),
):
    """POST — forces a new roll. Phase 11.2: 3 free/day then 10/20/30g."""
    guild = await user_guild_or_404(db, current_user["id"])
    return await refresh_candidates_for_guild(db, guild)


@router.post("/recruit", status_code=201)
async def recruit_adventurer(
    payload: RecruitIn, current_user: dict = Depends(get_current_user)
):
    guild = await user_guild_or_404(db, current_user["id"])
    # ROUND 6B.3 Wave 1.5 — over-cap guard centralised. Returns 423 with
    # `roster_over_capacity` so the FE banner/interceptor can unify the UX.
    # `additional=1` because recruit will add 1 to the roster.
    await assert_not_over_cap(
        db, guild["id"], source="recruitment.recruit", additional=1,
    )
    adventurer_doc, updated_guild = await recruit_from_offer(
        db, guild, payload.candidate_id
    )
    return {
        "adventurer": adventurer_public(adventurer_doc),
        "guild": {"gold": updated_guild["gold"]},
    }


__all__ = ["router"]
