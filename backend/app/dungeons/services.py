"""Dungeons domain services (Phase 5.5c.2).

Pure serialization + list+gate logic for read-only dungeons catalog. The gate
evaluation now lives in `app.expeditions.services` (Phase 5.5e) and is
imported eagerly at module level — no module-level cycle since
`expeditions.services` does not import anything from `app.dungeons`.
"""
from typing import Optional

from app.expeditions.services import _evaluate_dungeon_gate


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
        # ROUND 5 — additive flags (default-safe for legacy reads)
        "is_legacy": bool(d.get("is_legacy", False)),
        "is_5p": bool(d.get("is_5p", False)),
        "power_bumped": bool(d.get("power_bumped", False)),
        "tier_label": d.get("tier_label"),
        "tags": d.get("tags") or [],
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
    out = []
    for d in rows:
        pub = dungeon_public(d)
        if guild:
            unlocked, reason = await _evaluate_dungeon_gate(db, d, guild)
        else:
            unlocked, reason = True, None
        pub["unlocked"] = unlocked
        pub["unlock_reason"] = reason
        out.append(pub)
    return out


__all__ = ["dungeon_public", "list_dungeons_for_guild"]
