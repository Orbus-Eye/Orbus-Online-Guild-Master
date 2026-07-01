"""Dungeons domain services (Phase 5.5c.2).

Pure serialization + list+gate logic for read-only dungeons catalog. The gate
evaluation now lives in `app.expeditions.services` (Phase 5.5e) and is
imported eagerly at module level — no module-level cycle since
`expeditions.services` does not import anything from `app.dungeons`.
"""
from typing import Optional

from app.expeditions.services import _evaluate_dungeon_gate
from app.expeditions.level_gate import legacy_min_level_for_dungeon


def dungeon_public(d: dict) -> dict:
    """Project a Mongo dungeon document to its public JSON shape."""
    from app.content.lore_meta import dungeon_lore_meta
    meta = dungeon_lore_meta(d.get("slug", ""))
    return {
        "id": d["id"],
        "slug": d["slug"],
        "name": d["name"],
        # ROUND 13a — IT display name + lore meta (additive).
        "name_it": d.get("name_it") or meta.get("name_it") or d["name"],
        "description": d.get("description", ""),
        "description_it": d.get("description_it") or d.get("description", ""),
        "difficulty": d["difficulty"],
        "required_team_size": d["required_team_size"],
        "team_size": d["required_team_size"],  # alias for FE clarity
        "base_duration_seconds": d["base_duration_seconds"],
        "recommended_power": d["recommended_power"],
        "base_gold_reward": d["base_gold_reward"],
        "base_xp_reward": d["base_xp_reward"],
        # ROUND 5 — additive flags (default-safe for legacy reads)
        "is_legacy": bool(d.get("is_legacy", False)),
        "is_5p": bool(d.get("is_5p", False)),
        "power_bumped": bool(d.get("power_bumped", False)),
        "tier": d.get("tier") or d.get("tier_label"),
        "tier_label": d.get("tier_label"),
        "tags": d.get("tags") or [],
        "is_active": d.get("is_active", True),
        # ROUND 11.3 TASK A — adventurer-level gate exposed to FE so the
        # roster builder can grey-out under-level cards before dispatch.
        # Falls back on a `difficulty`-derived default for legacy seeds.
        "min_adventurer_level": legacy_min_level_for_dungeon(d),
        # ROUND 13a — Lore meta (additive, PII-safe).
        "lore_theme": d.get("lore_theme") or meta.get("lore_theme"),
        "content_family": d.get("content_family") or meta.get("content_family") or "baseline",
        "emotional_tone": d.get("emotional_tone") or meta.get("emotional_tone"),
        "location_hint": d.get("location_hint") or meta.get("location_hint"),
        "narrative_hook": d.get("narrative_hook") or meta.get("narrative_hook"),
        "enemy_families": d.get("enemy_families") or meta.get("enemy_families") or [],
        "spoiler_level": d.get("spoiler_level") or meta.get("spoiler_level") or "public",
        "is_new": meta.get("is_new", False),
        "is_void_undead": meta.get("is_void_undead", False),
        "lore_reviewed": bool(d.get("lore_reviewed", False)),
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
