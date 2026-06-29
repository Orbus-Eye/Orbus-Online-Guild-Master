"""Recruitment routes (Phase 5.5c.3 + Phase 11.2 refresh limit + ROUND 6B.2a cap).

ROUND 11.3 TASK C — adds 4 Recruit Freeze Bench endpoints. Each freezes /
unfreezes / recruits up to 2 candidates that persist across pool refreshes.
See `app.recruitment.freeze_bench` for the storage and atomicity rationale.
"""
from fastapi import APIRouter, Depends, HTTPException

from app.adventurers.services import adventurer_public
from app.core.database import db
from app.core.security import get_current_user
from app.guilds.services import user_guild_or_404
from app.recruitment.schemas import (
    FreezeIn,
    RecruitFrozenIn,
    RecruitIn,
    UnfreezeIn,
)
from app.recruitment.services import (
    get_or_init_candidates_for_guild,
    recruit_from_offer,
    refresh_candidates_for_guild,
)
from app.recruitment.freeze_bench import (
    freeze_candidate,
    get_frozen,
    recruit_from_bench,
    unfreeze_candidate,
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


# ─── ROUND 11.3 TASK C — Recruit Freeze Bench ─────────────────────────────────
@router.get("/frozen")
async def list_frozen_candidates(current_user: dict = Depends(get_current_user)):
    """GET — list of frozen candidates + slot capacity. Survives refresh."""
    guild = await user_guild_or_404(db, current_user["id"])
    return await get_frozen(db, guild["id"])


@router.post("/freeze", status_code=200)
async def freeze_recruit_candidate(
    payload: FreezeIn, current_user: dict = Depends(get_current_user)
):
    """POST — move a candidate from the active offer pool onto the bench.

    Errors:
      * 404 `recruit.candidate_not_found` — candidate not in active pool.
      * 409 `freeze_bench.full` — bench already at max_slots.
      * 409 `freeze_bench.already_frozen` — candidate already on bench
        (defensive against double-submit).
    """
    guild = await user_guild_or_404(db, current_user["id"])
    return await freeze_candidate(db, guild, payload.candidate_id)


@router.post("/unfreeze", status_code=200)
async def unfreeze_recruit_candidate(
    payload: UnfreezeIn, current_user: dict = Depends(get_current_user)
):
    """POST — release a bench slot. Snapshot is dropped (not returned to pool).
    Audit: `recruit_candidate_unfrozen`.

    Errors: 404 `freeze_bench.not_found`.
    """
    guild = await user_guild_or_404(db, current_user["id"])
    return await unfreeze_candidate(db, guild, payload.frozen_id)


@router.post("/recruit-frozen", status_code=201)
async def recruit_frozen_candidate(
    payload: RecruitFrozenIn, current_user: dict = Depends(get_current_user)
):
    """POST — hire from the bench. Atomic + audited like a normal recruit.

    Errors:
      * 404 `freeze_bench.not_found` — slot not on bench.
      * 402 `economy.insufficient_gold` — not enough gold.
      * 423 `roster_over_capacity` — bumped via post-insert recount.
    """
    guild = await user_guild_or_404(db, current_user["id"])
    # Pre-flight cap guard (mirrors the regular recruit path). The
    # post-insert recount inside `recruit_from_bench` is still the
    # authoritative race-safe gate; this just gives the player a faster
    # 423 when the cap is statically full.
    await assert_not_over_cap(
        db, guild["id"], source="recruitment.recruit_frozen", additional=1,
    )
    adv_doc, updated_guild = await recruit_from_bench(db, guild, payload.frozen_id)
    return {
        "adventurer": adventurer_public(adv_doc),
        "guild": {"gold": updated_guild["gold"]},
    }


__all__ = ["router"]
