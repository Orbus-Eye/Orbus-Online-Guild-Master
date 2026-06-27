"""ROUND 6B.2a — Server-side enforcement helpers.

Two responsibilities:

1. **Adventurer cap** — `compute_adventurer_cap_state(db, guild_id)` returns
   the current cap (driven by `dormitories.level`) plus the active
   adventurer count. `count_active_adventurers` filters `is_retired=true`.

2. **`require_unlocked(action)`** — a FastAPI dependency factory that
   reads the caller's `guild_structures` doc and raises 423 Locked if
   the declarative `UNLOCK_REQUIREMENTS[action]` is not satisfied.
"""
from __future__ import annotations

from typing import Callable

from fastapi import Depends, HTTPException

from app.core.database import db as default_db
from app.core.security import get_current_user
from app.guilds.services import user_guild_or_404
from app.territory.services import ensure_guild_structures_doc
from app.territory.structures import (
    STRUCTURE_CATALOG,
    dormitory_cap_for_level,
    get_display_name,
)
from app.territory.unlock_table import UNLOCK_REQUIREMENTS


# ---------- Adventurer cap ----------------------------------------------------

async def count_active_adventurers(db, guild_id: str) -> int:
    """Count adventurers that occupy a roster slot.

    Retired adventurers (`is_retired=true`) are EXCLUDED — they keep their
    history record but free up roster capacity.
    """
    return await db.adventurers.count_documents({
        "guild_id": guild_id,
        "is_retired": {"$ne": True},
    })


async def compute_adventurer_cap_state(db, guild_id: str) -> dict:
    """Resolve `{cap, current, dormitory_level, headroom}` for one guild."""
    territory = await ensure_guild_structures_doc(db, guild_id)
    dorm = territory["structures"].get("dormitories") or {}
    level = int(dorm.get("level", 1))
    cap = dormitory_cap_for_level(level)
    current = await count_active_adventurers(db, guild_id)
    return {
        "dormitory_level": level,
        "cap": cap,
        "current": current,
        "headroom": max(0, cap - current),
        "is_over_cap": current > cap,
    }


# ---------- require_unlocked dependency --------------------------------------

def require_unlocked(action: str) -> Callable:
    """FastAPI dependency: enforce an `UNLOCK_REQUIREMENTS[action]` gate.

    Usage in routes:
        @router.post("/something", dependencies=[Depends(require_unlocked("auction.list"))])

    Behaviour:
      - 401 if no JWT (delegated to `get_current_user`).
      - 423 Locked if the structure level is below `min_level`.
      - Pass-through otherwise.

    Performance: one extra `find_one` on `guild_structures` per gated call.
    No request-level cache yet — kept simple; the doc is small and indexed.
    """
    req = UNLOCK_REQUIREMENTS.get(action)
    if req is None:
        raise RuntimeError(
            f"require_unlocked: unknown action {action!r}. "
            "Add it to app.territory.unlock_table.UNLOCK_REQUIREMENTS."
        )

    structure_slug = req["structure"]
    min_level = int(req["min_level"])

    async def _checker(current_user: dict = Depends(get_current_user)) -> None:
        guild = await user_guild_or_404(default_db, current_user["id"])
        terr = await ensure_guild_structures_doc(default_db, guild["id"])
        cur = terr["structures"].get(structure_slug) or {}
        current_level = int(cur.get("level", 0))
        if not cur.get("is_unlocked") or current_level < min_level:
            raise HTTPException(
                status_code=423,
                detail={
                    "code": "feature.locked",
                    "action": action,
                    "required_structure": structure_slug,
                    "required_structure_name_it": get_display_name(structure_slug, "it"),
                    "required_level": min_level,
                    "current_level": current_level,
                    "user_message": (
                        f"Richiede {get_display_name(structure_slug, 'it')} "
                        f"Livello {min_level}. "
                        f"Visita il Territorio per potenziarla."
                    ),
                },
            )

    return _checker


__all__ = [
    "count_active_adventurers",
    "compute_adventurer_cap_state",
    "require_unlocked",
]
