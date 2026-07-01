"""ROUND 16.3 Phase 7A — Arfus applier PvP-filtered.

Additive parallel path to the PvE applier in `app.arfus_forge`. Only 6
tech categories affect PvP battles; all others are ignored to prevent
P2W bleed-over (e.g. `arcane_knowledge`, `exploration_luck`,
`leader_experience`, `forge_efficiency`).

This module MUST NOT be imported by expedition / raid / world_boss
services. It exists solely for `pvp_continental.resolver`.
"""
from __future__ import annotations

from typing import Iterable


# Whitelist (6 categories only)
PVP_APPLICABLE_CATEGORIES: frozenset[str] = frozenset({
    "combat_damage",
    "combat_healing",
    "combat_defense",
    "counter_effectiveness",
    "iron_will",
    "team_morale",
})

# Total bonus cap (percentage) — prevents runaway stacking.
PVP_TOTAL_BONUS_CAP: float = 0.50


async def get_pvp_arfus_bonus_sum(db, guild_id: str) -> float:
    """Return additive percentage bonus (0.0 .. PVP_TOTAL_BONUS_CAP) for
    the given guild, considering ONLY the 6 PvP-applicable categories.

    Reads the same source-of-truth used by the PvE applier
    (`get_active_bonuses_for_guild` in `app.arfus_forge`) but filters
    categories BEFORE the sum. Returns 0.0 if no active tech.
    """
    if not guild_id:
        return 0.0
    from app.arfus_forge import get_active_bonuses_for_guild
    all_bonuses: dict = await get_active_bonuses_for_guild(guild_id)
    total_pct = sum(
        val for cat, val in all_bonuses.items()
        if cat in PVP_APPLICABLE_CATEGORIES
    )
    fraction = total_pct / 100.0
    return min(fraction, PVP_TOTAL_BONUS_CAP)


def is_pvp_applicable(category: str) -> bool:
    """Introspection helper (used by tests + admin diagnostics)."""
    return category in PVP_APPLICABLE_CATEGORIES


def filter_pvp_categories(categories: Iterable[str]) -> list[str]:
    return [c for c in categories if c in PVP_APPLICABLE_CATEGORIES]
