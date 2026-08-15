"""Dungeons domain services (Phase 5.5c.2).

Pure serialization + list+gate logic for read-only dungeons catalog. The gate
evaluation now lives in `app.expeditions.services` (Phase 5.5e) and is
imported eagerly at module level — no module-level cycle since
`expeditions.services` does not import anything from `app.dungeons`.
"""
from typing import Optional

from app.dungeons.encounters import apply_dungeon_encounter
from app.expeditions.services import _evaluate_dungeon_gate
from app.expeditions.level_gate import legacy_min_level_for_dungeon
from app.expeditions.power_gate import required_team_power_for as _required_team_power
from app.dungeons.rooms import rooms_mode_for_dungeon as _rooms_mode


def dungeon_public(d: dict) -> dict:
    """Project a Mongo dungeon document to its public JSON shape."""
    from app.content.lore_meta import dungeon_lore_meta
    d = apply_dungeon_encounter(d)
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
        "encounter_type": d.get("encounter_type"),
        "encounter_phases": d.get("encounter_phases") or [],
        "reward_profile": d.get("reward_profile"),
        "threat_tags": d.get("threat_tags") or [],
        "threat_count": int(d.get("threat_count", 0)),
        "progression_bucket": d.get("bucket"),
        "curve_version": d.get("curve_version"),
        "is_active": d.get("is_active", True),
        # ROUND 11.3 TASK A — adventurer-level. FASE 2.2: NON è più un
        # blocco, resta esposto come fascia consigliata informativa.
        "min_adventurer_level": legacy_min_level_for_dungeon(d),
        # FASE 2.2 — soglia di potere squadra per entrare (gate reale).
        "required_team_power": _required_team_power(d),
        # FASE 5 — questo dungeon parte in modalità a stanze (pilota)?
        "rooms_mode": _rooms_mode(d),
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
        .sort(
            [
                ("is_starter", -1),
                ("difficulty", 1),
                ("recommended_power", 1),
                ("slug", 1),
            ]
        )
        .to_list(100)
    )
    # FASE 10G — disponibilità della modalità AUTOMATICA per gilda:
    # dungeon a stanze + almeno un clear MANUALE registrato (10J).
    from app.dungeons.rooms import auto_route_duration_seconds
    from app.guild_supplies import AUTO_DUNGEON_COST
    manual_clears = (guild or {}).get("manual_dungeon_clears") or {}

    out = []
    for d in rows:
        pub = dungeon_public(d)
        if guild:
            unlocked, reason = await _evaluate_dungeon_gate(db, d, guild)
        else:
            unlocked, reason = True, None
        pub["unlocked"] = unlocked
        pub["unlock_reason"] = reason
        clear = manual_clears.get(d.get("slug") or "")
        auto_ok = bool(
            guild and pub["rooms_mode"] and clear
            and clear.get("route_snapshot")
        )
        pub["auto_available"] = auto_ok
        pub["auto_cost_supplies"] = AUTO_DUNGEON_COST
        pub["auto_duration_seconds"] = (
            auto_route_duration_seconds(clear["route_snapshot"])
            if auto_ok else None
        )
        out.append(pub)
    if guild:
        # FASE 1.9 (2026-08-08) — visibilità progressiva: sbloccati + solo
        # il primo bloccato ("prossima sfida"). Reader non autenticato:
        # catalogo intero (comportamento pubblico/SEO invariato).
        from app.shared.progressive_visibility import apply_progressive_visibility
        return apply_progressive_visibility(out)
    return out


__all__ = ["dungeon_public", "list_dungeons_for_guild"]
