"""Dungeons domain services (Phase 5.5c.2).

Pure serialization + list+gate logic for read-only dungeons catalog. The gate
evaluation (`_evaluate_dungeon_gate`) intentionally stays in `server.py`
because it is also called by the expedition dispatch + replay-eligibility
helpers. We invoke it via a lazy import here to avoid a circular dependency.
"""
from typing import Optional


def dungeon_public(d: dict) -> dict:
    """Project a Mongo dungeon document to its public JSON shape."""
    return {
        "id": d["id"],
        "slug": d["slug"],
        "name": d["name"],
        "description": d.get("description", ""),
        "difficulty": d["difficulty"],
        "required_team_size": d["required_team_size"],
        "base_duration_seconds": d["base_duration_seconds"],
        "recommended_power": d["recommended_power"],
        "base_gold_reward": d["base_gold_reward"],
        "base_xp_reward": d["base_xp_reward"],
        "is_active": d.get("is_active", True),
    }


async def list_dungeons_for_guild(db, guild: Optional[dict]) -> list[dict]:
    """Return the active dungeon catalog with per-guild gate evaluation.

    When `guild` is None (unauthenticated reader) all dungeons are reported as
    unlocked — this preserves the pre-refactor behavior of the original route.
    """
    rows = (
        await db.dungeons.find({"is_active": True}, {"_id": 0})
        .sort("difficulty", 1)
        .to_list(100)
    )
    # Lazy import to avoid a circular dependency: server.py is still loading
    # at module-import time of this package.
    from server import _evaluate_dungeon_gate

    out = []
    for d in rows:
        pub = dungeon_public(d)
        if guild:
            unlocked, reason = await _evaluate_dungeon_gate(d, guild)
        else:
            unlocked, reason = True, None
        pub["unlocked"] = unlocked
        pub["unlock_reason"] = reason
        out.append(pub)
    return out


__all__ = ["dungeon_public", "list_dungeons_for_guild"]
