"""ROUND 6B.3 Wave 1.5 — Over-cap roster enforcement guards.

Two server-side helpers + one FastAPI dependency factory:

1. `assert_not_over_cap(db, guild_id, *, source)`:
   Raises 423 `roster_over_capacity` if `current > cap`. Returns the full
   cap_state dict on success.

2. `assert_adventurers_not_retired(db, guild_id, adventurer_ids, *, source)`:
   Raises 423 `adventurers.retired_in_set` if at least one of the supplied
   ids belongs to a retired adventurer in the same guild.

3. `over_cap_dep`:
   FastAPI dependency factory — `Depends(over_cap_dep("expedition.create"))`.
   Resolves the caller's guild via `user_guild_or_404` and runs
   `assert_not_over_cap`. Returns the cap_state for downstream use.

Design notes
------------
- HTTP 423 ("Locked") is used for both flows (per Wave 1.5 user decision).
  The previous `recruitment.cap_reached` code stays under the new umbrella
  for backwards-compat callers but is also 423 now.
- `roster_over_capacity` is a COMPUTED state (not persisted on `db.guilds`).
  Recomputed on every gated request via `compute_adventurer_cap_state`.
- The two escape valves — `POST /api/territory/upgrade` and
  `POST /api/adventurers/{id}/retire` — are intentionally NOT gated.
"""
from __future__ import annotations

from typing import Callable, Iterable

from fastapi import Depends, HTTPException

from app.core.database import db as default_db
from app.core.security import get_current_user
from app.guilds.services import user_guild_or_404
from app.territory.guards import compute_adventurer_cap_state


# ─── Pure assertion helpers ──────────────────────────────────────────────────


async def assert_not_over_cap(
    db, guild_id: str, *, source: str, additional: int = 0,
) -> dict:
    """Raise 423 `roster_over_capacity` if active roster would exceed cap.

    `additional` = expected delta added by the caller (1 for recruit, 0
    for the read-only flows like expedition/raid/squad operations on
    existing roster). With `additional=0` the check is "are we currently
    over-cap?". With `additional=1` it is "would adding one new adventurer
    push us over?".

    Returns the resolved cap_state dict on success.
    """
    state = await compute_adventurer_cap_state(db, guild_id)
    projected = state["current"] + int(additional)
    if projected > state["cap"]:
        must_retire = projected - state["cap"]
        # Best-effort analytics. Never block the user flow.
        try:
            from app.audit.log import write_audit
            await write_audit(
                db,
                event_type="roster_over_capacity_blocked",
                actor_guild_id=guild_id,
                source=source,
                metadata={
                    "cap": state["cap"],
                    "current": state["current"],
                    "additional": int(additional),
                    "must_retire": must_retire,
                    "dormitory_level": state["dormitory_level"],
                },
            )
        except Exception:  # noqa: BLE001
            pass
        raise HTTPException(
            status_code=423,
            detail={
                "code": "roster_over_capacity",
                "current": state["current"],
                "cap": state["cap"],
                "additional": int(additional),
                "must_retire": must_retire,
                "dormitory_level": state["dormitory_level"],
                "user_message": (
                    f"Roster oltre capacità: {state['current']}/{state['cap']}. "
                    f"Congeda {must_retire} avventurier"
                    f"{'i' if must_retire > 1 else 'o'} oppure potenzia "
                    f"i Dormitori per sbloccare questa azione."
                ),
            },
        )
    return state


async def assert_adventurers_not_retired(
    db, guild_id: str, adventurer_ids: Iterable[str], *, source: str,
) -> None:
    """Raise 423 `adventurers.retired_in_set` if any id resolves to a
    retired adventurer in the same guild.

    Pass-through for empty input (callers should still pre-validate
    `len(adventurer_ids) > 0` for their own semantics).
    """
    ids = [a for a in adventurer_ids if a]
    if not ids:
        return
    retired = await default_db_safe_find_retired(db, guild_id, ids)
    if retired:
        raise HTTPException(
            status_code=423,
            detail={
                "code": "adventurers.retired_in_set",
                "source": source,
                "retired_adventurer_ids": retired,
                "count": len(retired),
                "user_message": (
                    "Selezione include "
                    f"{len(retired)} avventurier"
                    f"{'i' if len(retired) > 1 else 'o'} congedat"
                    f"{'i' if len(retired) > 1 else 'o'}. "
                    "Rimuovili dalla selezione."
                ),
            },
        )


async def default_db_safe_find_retired(
    db, guild_id: str, adventurer_ids: list[str],
) -> list[str]:
    """Internal: return the subset of `adventurer_ids` that are retired."""
    cursor = db.adventurers.find(
        {"guild_id": guild_id,
         "id": {"$in": adventurer_ids},
         "is_retired": True},
        {"_id": 0, "id": 1},
    )
    return [r["id"] async for r in cursor]


# ─── FastAPI dependency factory ──────────────────────────────────────────────


def over_cap_dep(source: str) -> Callable:
    """FastAPI dependency: enforce `assert_not_over_cap` BEFORE the route runs.

    Usage:
        @router.post(
            "",
            dependencies=[Depends(over_cap_dep("expedition.create"))],
        )

    The dependency returns the cap_state dict; routes that want to read it
    can re-call `compute_adventurer_cap_state` instead of adding the dep as
    a parameter (most routes just need the side-effect of the 423 raise).
    """
    async def _checker(current_user: dict = Depends(get_current_user)) -> dict:
        guild = await user_guild_or_404(default_db, current_user["id"])
        return await assert_not_over_cap(
            default_db, guild["id"], source=source,
        )
    return _checker


__all__ = [
    "assert_not_over_cap",
    "assert_adventurers_not_retired",
    "over_cap_dep",
]
