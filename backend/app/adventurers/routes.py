"""Adventurers + classes routes (Phase 5.5d, Phase 19.2 rename, ROUND 6B.2a retire)."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from pymongo import ASCENDING

from app.adventurers.retire import retire_adventurer
from app.adventurers.services import (
    class_public,
    list_adventurers_for_guild,
    rename_adventurer,
    trait_preview_for_adventurer,
)
from app.core.database import db
from app.core.security import get_current_user
from app.guilds.services import user_guild_or_404
from app.territory.guards import compute_adventurer_cap_state


router = APIRouter(tags=["adventurers"])


# ROUND 6B.4 Task 3 — `retire_via` enum kept strict at the API surface.
# `retired_by` (storage enum) stays the canonical "who triggered it" field;
# `via` (this enum) describes the user flow. Defaults to "single" when the
# caller doesn't specify.
RETIRE_VIA_VALUES = {"single", "bulk_capacity"}


class AdventurerRenameIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=30)


class AdventurerRetireIn(BaseModel):
    reason: str | None = Field(default=None, max_length=200)
    force_unequip: bool = Field(default=False)
    via: str = Field(default="single", max_length=32)
    # ROUND 6C — opt-in flag for retiring an adventurer who has a
    # specialization signature_item. Default `false` keeps the safe
    # behaviour: signature items still block the retire via the generic
    # bound-items guard. Setting `true` soft-discards signature items
    # only (`discarded_at` set, `bound_to_adventurer_id` cleared,
    # audit emitted); non-signature bound items still block.
    discard_signature_items: bool = Field(default=False)


@router.get("/api/adventurer-classes")
async def list_classes():
    classes = (
        await db.adventurer_classes.find({"is_active": True}, {"_id": 0})
        .sort("name", ASCENDING)
        .to_list(100)
    )
    return {"classes": [class_public(c) for c in classes]}


@router.get("/api/adventurers")
async def list_adventurers(
    include_retired: bool = False,
    current_user: dict = Depends(get_current_user),
):
    guild = await user_guild_or_404(db, current_user["id"])
    return {"adventurers": await list_adventurers_for_guild(
        db, guild["id"], include_retired=include_retired
    )}


@router.get("/api/adventurers/{adventurer_id}/trait-preview")
async def get_trait_preview(
    adventurer_id: str, current_user: dict = Depends(get_current_user)
):
    """Phase 13 — read-only preview of trait effects on stats / power."""
    guild = await user_guild_or_404(db, current_user["id"])
    return await trait_preview_for_adventurer(db, guild["id"], adventurer_id)


@router.patch("/api/adventurers/{adventurer_id}/name")
async def patch_adventurer_name(
    adventurer_id: str,
    payload: AdventurerRenameIn,
    current_user: dict = Depends(get_current_user),
):
    """Phase 19.2 — rename adventurer (max 2 lifetime). Free, no gold cost."""
    guild = await user_guild_or_404(db, current_user["id"])
    return await rename_adventurer(db, guild["id"], adventurer_id, payload.name)


@router.post("/api/adventurers/{adventurer_id}/retire")
async def post_adventurer_retire(
    adventurer_id: str,
    payload: AdventurerRetireIn,
    current_user: dict = Depends(get_current_user),
):
    """ROUND 6B.2a — soft retire (no hard delete). Frees the roster slot
    for cap purposes; history records remain intact. ROUND 6B.4 adds
    `via` metadata + adventurer-bound items guard."""
    guild = await user_guild_or_404(db, current_user["id"])
    via = payload.via if payload.via in RETIRE_VIA_VALUES else "single"
    return await retire_adventurer(
        db,
        guild_id=guild["id"],
        adventurer_id=adventurer_id,
        reason=payload.reason,
        force_unequip=payload.force_unequip,
        actor_user_id=current_user["id"],
        via=via,
        discard_signature_items=payload.discard_signature_items,
    )


# ROUND 6B.4 Task 1 — Roster Health endpoint.
# Thin wrapper around `compute_adventurer_cap_state` that adds the 4-state
# semantic decision so the FE doesn't duplicate threshold logic. Thresholds
# locked at Q1 default: 0.7 / 0.9 / 1.0 (over_cap = current > cap).
def _resolve_roster_state(current: int, cap: int) -> str:
    if cap <= 0:
        return "over_cap" if current > 0 else "healthy"
    if current > cap:
        return "over_cap"
    ratio = current / cap
    if ratio > 0.9:
        return "at_cap"
    if ratio > 0.7:
        return "filling"
    return "healthy"


@router.get("/api/roster/health")
async def get_roster_health(current_user: dict = Depends(get_current_user)):
    """ROUND 6B.4 — public roster health for the dashboard widget.

    Returns: {current, cap, headroom, dormitory_level, is_over_cap, state}
    where `state ∈ {"healthy","filling","at_cap","over_cap"}`.
    No PII is exposed: only numeric counts + structure level.
    """
    guild = await user_guild_or_404(db, current_user["id"])
    cap_state = await compute_adventurer_cap_state(db, guild["id"])
    state_label = _resolve_roster_state(cap_state["current"], cap_state["cap"])
    return {**cap_state, "state": state_label}


__all__ = ["router"]
