"""ROUND 16.0 — Phase 4 — Threat resolution helper.

Schema-only logic applied at start-expedition time: when a dungeon
carries `threat_tags`, we look up the squad's combined counter
capabilities and compute a small success-chance bonus + injury
reduction. The drop tables are **not** touched (Fase 4 explicitly
forbids loot bonuses).

Public API:
    `await compute_threat_resolution(db, team_members, dungeon)`
        → {"applies": bool, "threats": [...], "threats_countered": [...],
           "counter_ratio": float, "success_bonus_pct": int,
           "injury_reduction_pct": int}

The function is read-only (loads `class_specializations`,
`counter_tags`, and `adventurer_traits` from the DB) and is safe to
call on every expedition; for dungeons without `threat_tags` it
returns `applies=False` with no further DB reads beyond the dungeon
lookup performed by the caller.
"""
from __future__ import annotations

from typing import Any, Iterable


SUCCESS_BONUS_CAP_PCT = 12  # +12% max
INJURY_REDUCTION_CAP_PCT = 8  # -8% max


async def _load_counters_map(db) -> dict[str, set[str]]:
    """Resolve `counter_slug → set(threat_slugs it counters)`."""
    out: dict[str, set[str]] = {}
    async for row in db.counter_tags.find(
        {"is_active": True},
        {"_id": 0, "slug": 1, "threats_countered": 1},
    ):
        out[row["slug"]] = set(row.get("threats_countered") or [])
    return out


async def _gather_team_counter_slugs(
    db, team_members: Iterable[dict],
) -> set[str]:
    """Collect every `counter_tag` slug provided by the team via spec or traits."""
    spec_slugs: set[str] = set()
    trait_slugs: set[str] = set()
    for adv in team_members:
        s = adv.get("specialization_slug")
        if s:
            spec_slugs.add(s)
        for t in (adv.get("traits") or adv.get("traits_snapshot") or []):
            if isinstance(t, str):
                trait_slugs.add(t)
            elif isinstance(t, dict) and t.get("slug"):
                trait_slugs.add(t["slug"])
    counters: set[str] = set()
    if spec_slugs:
        async for row in db.class_specializations.find(
            {"slug": {"$in": list(spec_slugs)}},
            {"_id": 0, "counter_tags": 1},
        ):
            counters.update(row.get("counter_tags") or [])
    if trait_slugs:
        async for row in db.adventurer_traits.find(
            {"slug": {"$in": list(trait_slugs)}},
            {"_id": 0, "counter_tags": 1},
        ):
            counters.update(row.get("counter_tags") or [])
    return counters


async def compute_threat_resolution(
    db, *, team_members: list[dict], dungeon: dict,
) -> dict[str, Any]:
    """Return the threat-resolution summary or `{"applies": False}`."""
    threats = list(dungeon.get("threat_tags") or [])
    if not threats:
        return {"applies": False}
    team_counter_slugs = await _gather_team_counter_slugs(db, team_members)
    if not team_counter_slugs:
        return {"applies": True, "threats": threats,
                "threats_countered": [], "counter_ratio": 0.0,
                "success_bonus_pct": 0, "injury_reduction_pct": 0}
    counters_map = await _load_counters_map(db)
    resolved: set[str] = set()
    for slug in team_counter_slugs:
        resolved.update(counters_map.get(slug, set()))
    threats_countered = sorted(t for t in threats if t in resolved)
    ratio = len(threats_countered) / len(threats)
    bonus = int(round(ratio * SUCCESS_BONUS_CAP_PCT))
    injury_red = int(round(ratio * INJURY_REDUCTION_CAP_PCT))
    return {
        "applies": True,
        "threats": threats,
        "threats_countered": threats_countered,
        "counter_ratio": round(ratio, 3),
        "success_bonus_pct": bonus,
        "injury_reduction_pct": injury_red,
    }


__all__ = [
    "compute_threat_resolution",
    "SUCCESS_BONUS_CAP_PCT",
    "INJURY_REDUCTION_CAP_PCT",
]
