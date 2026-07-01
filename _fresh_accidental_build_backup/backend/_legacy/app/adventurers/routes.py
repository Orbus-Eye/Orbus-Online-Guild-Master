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
    class_slug: str | None = None,
    spec_slug: str | None = None,
    role: str | None = None,
    race_slug: str | None = None,
    improvable_equip: bool = False,
    no_spec: bool = False,
    ready_for_dungeon: bool = False,
    sort: str | None = None,
    current_user: dict = Depends(get_current_user),
):
    # ROUND 16.1 Phase 2 — light server-side filter + sort overlay.
    # The base list is loaded once via list_adventurers_for_guild() for
    # equip-power join; remaining slicing is done in-process to stay simple
    # and avoid an N+1 cursor (rosters are capped ≤500 rows).
    guild = await user_guild_or_404(db, current_user["id"])
    rows = await list_adventurers_for_guild(
        db, guild["id"], include_retired=include_retired)

    if class_slug:
        rows = [r for r in rows if r.get("class_slug") == class_slug]
    if spec_slug:
        rows = [r for r in rows if r.get("specialization_slug") == spec_slug]
    if role:
        rows = [r for r in rows if (r.get("class_role") or "").lower() == role.lower()]
    if race_slug:
        rows = [r for r in rows if r.get("race_slug") == race_slug]
    if no_spec:
        rows = [r for r in rows if not r.get("specialization_slug")]
    if improvable_equip:
        # Best-effort: count equipped slots; consider improvable if < 4.
        def _is_improvable(a: dict) -> bool:
            slots = a.get("equipment") or {}
            equipped = sum(1 for v in slots.values() if v)
            return equipped < 4
        rows = [r for r in rows if _is_improvable(r)]
    if ready_for_dungeon:
        rows = [r for r in rows
                if (r.get("level") or 0) >= 3
                and not r.get("is_retired")
                and not r.get("is_injured")]

    # Sort overlay
    sort_map = {
        "level_desc":   lambda a: -(a.get("level") or 0),
        "level_asc":    lambda a: (a.get("level") or 0),
        "power_desc":   lambda a: -((a.get("equipment_power") or 0)
                                      + (a.get("base_power") or 0)),
        "power_asc":    lambda a: ((a.get("equipment_power") or 0)
                                      + (a.get("base_power") or 0)),
        "class_asc":    lambda a: (a.get("class_slug") or ""),
        "name_asc":     lambda a: (a.get("name") or "").lower(),
        "primary_desc": lambda a: -_primary_stat_value(a),
        "primary_asc":  lambda a: _primary_stat_value(a),
    }
    if sort in sort_map:
        rows = sorted(rows, key=sort_map[sort])

    return {"adventurers": rows, "total": len(rows)}


def _primary_stat_value(a: dict) -> int:
    """Return the value of the adventurer's primary stat, or 0."""
    stat = (a.get("primary_stat") or "").lower()
    stats = a.get("stats") or {}
    return int(stats.get(stat) or 0)


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

    Returns: {current, cap, headroom, dormitory_level, is_over_cap, state,
              dormitories_next_upgrade}
    where `state ∈ {"healthy","filling","at_cap","over_cap"}`.

    ROUND 6E Task 5 — single source of truth for next dormitory upgrade
    cost (FE no longer recomputes from STRUCTURE_COSTS).
    """
    guild = await user_guild_or_404(db, current_user["id"])
    cap_state = await compute_adventurer_cap_state(db, guild["id"])
    state_label = _resolve_roster_state(cap_state["current"], cap_state["cap"])
    # ROUND 6E — next upgrade hint (null target_level if at max).
    from app.territory.costs import cost_for
    from app.territory.structures import STRUCTURE_CATALOG
    current_dorm_level = int(cap_state.get("dormitory_level") or 0)
    dorm_max = int(STRUCTURE_CATALOG.get("dormitories", {}).get("max_level", 6))
    next_target = current_dorm_level + 1
    next_upgrade: dict
    if next_target > dorm_max:
        next_upgrade = {
            "target_level": None,
            "cost_gold": 0,
            "cost_materials": {},
            "prereq_met": True,
        }
    else:
        cost = cost_for("dormitories", next_target) or {}
        next_upgrade = {
            "target_level": next_target,
            "cost_gold": int(cost.get("gold", 0)),
            "cost_materials": dict(cost.get("materials") or {}),
            "prereq_met": True,  # dormitories have no prerequisites
        }
    return {
        **cap_state,
        "state": state_label,
        "dormitories_next_upgrade": next_upgrade,
    }


__all__ = ["router"]
