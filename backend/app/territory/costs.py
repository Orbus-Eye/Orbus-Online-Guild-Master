"""ROUND 6B.1 — Upgrade costs (data only, no atomic deduction yet).

`UPGRADE_COSTS[slug]` is a list indexed by TARGET LEVEL.
- Index 0 = N/A placeholder (level 0 = locked state, no cost).
- Index 1 = purchase cost to unlock (Lv 0 → 1).
- Index N (N>=2) = cost to upgrade from level (N-1) → N.

For dormitories Lv7 (Legacy Wing) we set cost = None — that level is
reachable ONLY via the migration script, not via `POST /api/territory/upgrade`.

Materials reference well-known item slugs from the existing forge seeds
(see ROUND 4). If a material slug is missing in the DB the upgrade check
in 6B.2 will reject the upgrade with a clean error.

Atomic transaction (gold debit + materials consume + structure update)
lands in 6B.2. 6B.1 only checks the cost.
"""
from __future__ import annotations

from typing import Optional


# Sentinel for migration-only levels (cannot be purchased by users).
_LEGACY_ONLY = None


UPGRADE_COSTS: dict[str, list[Optional[dict]]] = {
    # Cores — guild_hall is the only true gating spine, kept cheap early.
    # ROUND 6B.3 — material slugs normalized to `underscore_case` to match
    # the actual `items.slug` convention in DB. Kebab-case slugs (e.g.
    # `iron-shard`) were never resolvable against the inventory and caused
    # the atomic-debit fix to silently miss the materials step.
    "guild_hall": [
        None,                                           # Lv 0 (N/A — starter Lv1)
        {"gold": 0},                                    # Lv 1 (starter, free)
        {"gold": 200, "materials": {"iron_shard": 3}},  # Lv 2
        {"gold": 500, "materials": {"iron_shard": 6, "lesser_arcane_dust": 3}},  # Lv 3
        {"gold": 1200, "materials": {"iron_shard": 12, "lesser_arcane_dust": 6}}, # Lv 4
        {"gold": 2500, "materials": {"iron_shard": 20, "greater_arcane_dust": 4}},# Lv 5
        {"gold": 5000, "materials": {"iron_shard": 30, "greater_arcane_dust": 8}},# Lv 6
    ],
    "dormitories": [
        None,
        {"gold": 0},                                    # Lv 1 (starter, cap 5)
        {"gold": 200},                                  # Lv 2 (cap 10)
        {"gold": 500},                                  # Lv 3 (cap 15)
        {"gold": 1200},                                 # Lv 4 (cap 20)
        {"gold": 2500, "materials": {"iron_shard": 8}}, # Lv 5 (cap 25)
        {"gold": 5000, "materials": {"iron_shard": 16}},# Lv 6 (cap 30)
        _LEGACY_ONLY,                                   # Lv 7 (cap 50) — migration only
    ],
    "expedition_board": [
        None,
        {"gold": 0},
        {"gold": 200, "materials": {"iron_shard": 2}},
        {"gold": 500, "materials": {"iron_shard": 5, "lesser_arcane_dust": 2}},
        {"gold": 1200, "materials": {"iron_shard": 10, "lesser_arcane_dust": 4}},
        {"gold": 2500, "materials": {"greater_arcane_dust": 3}},
        {"gold": 5000, "materials": {"greater_arcane_dust": 6}},
    ],
    "war_room": [
        None,
        {"gold": 100, "materials": {"iron_shard": 2}},  # Lv 1 (unlock)
        {"gold": 250, "materials": {"iron_shard": 5}},  # Lv 2 (raid t1)
        {"gold": 700, "materials": {"lesser_arcane_dust": 4}},  # Lv 3 (raid t2)
        {"gold": 1500, "materials": {"lesser_arcane_dust": 8}},
        {"gold": 3000, "materials": {"greater_arcane_dust": 4}},
        {"gold": 6000, "materials": {"greater_arcane_dust": 8}},
    ],
    "market_stall": [
        None,
        {"gold": 50},                                   # Lv 1 (shop buy)
        {"gold": 200, "materials": {"iron_shard": 3}},  # Lv 2 (shop sell)
        {"gold": 500, "materials": {"iron_shard": 6}},
        {"gold": 1200, "materials": {"lesser_arcane_dust": 4}},
        {"gold": 2500, "materials": {"greater_arcane_dust": 3}},
        {"gold": 5000, "materials": {"greater_arcane_dust": 6}},
    ],
    "auction_house": [
        None,
        {"gold": 100, "materials": {"iron_shard": 2}},  # Lv 1 (auction buy)
        {"gold": 300, "materials": {"iron_shard": 5}},  # Lv 2 (auction list)
        {"gold": 700, "materials": {"lesser_arcane_dust": 3}},
        {"gold": 1500, "materials": {"lesser_arcane_dust": 6}},
        {"gold": 3000, "materials": {"greater_arcane_dust": 4}},
        {"gold": 6000, "materials": {"greater_arcane_dust": 8}},
    ],
    "workshop": [
        None,
        {"gold": 100, "materials": {"iron_shard": 2}},  # Lv 1 (craft basic)
        {"gold": 300, "materials": {"iron_shard": 5}},  # Lv 2 (craft uncommon)
        {"gold": 700, "materials": {"lesser_arcane_dust": 4}}, # Lv 3 (craft rare)
        {"gold": 1500, "materials": {"lesser_arcane_dust": 8}},
        {"gold": 3000, "materials": {"greater_arcane_dust": 4}},
        {"gold": 6000, "materials": {"greater_arcane_dust": 8}},
    ],
    "forge": [
        None,
        {"gold": 150, "materials": {"iron_shard": 3}},  # Lv 1 (disenchant)
        {"gold": 400, "materials": {"iron_shard": 6}},  # Lv 2 (refine)
        {"gold": 900, "materials": {"lesser_arcane_dust": 4}}, # Lv 3 (enchant)
        {"gold": 1800, "materials": {"lesser_arcane_dust": 8, "greater_arcane_dust": 2}}, # Lv 4 (reroll)
        {"gold": 3500, "materials": {"greater_arcane_dust": 5}},
        {"gold": 7000, "materials": {"greater_arcane_dust": 10}},
    ],
    "consortium_hall": [
        None,
        {"gold": 100},                                  # Lv 1 (join)
        {"gold": 300, "materials": {"iron_shard": 3}},  # Lv 2 (create)
        {"gold": 700, "materials": {"lesser_arcane_dust": 3}},
        {"gold": 1500, "materials": {"lesser_arcane_dust": 6}},
        {"gold": 3000, "materials": {"greater_arcane_dust": 3}},
        {"gold": 6000, "materials": {"greater_arcane_dust": 6}},
    ],
    "communication_hall": [
        None,
        {"gold": 50},                                   # Lv 1 (global chat)
        {"gold": 200, "materials": {"iron_shard": 2}},  # Lv 2 (consortium chat)
        {"gold": 500, "materials": {"iron_shard": 5}},
        {"gold": 1200, "materials": {"lesser_arcane_dust": 4}},
        {"gold": 2500, "materials": {"greater_arcane_dust": 3}},
        {"gold": 5000, "materials": {"greater_arcane_dust": 6}},
    ],
    "training_grounds": [
        None,
        {"gold": 200, "materials": {"iron_shard": 4}},  # Lv 1 (placeholder for ROUND 6C)
        {"gold": 500, "materials": {"iron_shard": 8}},
        {"gold": 1200, "materials": {"lesser_arcane_dust": 5}},
        {"gold": 2500, "materials": {"lesser_arcane_dust": 10}},
        {"gold": 5000, "materials": {"greater_arcane_dust": 5}},
        {"gold": 10000, "materials": {"greater_arcane_dust": 10}},
    ],
}


def cost_for(slug: str, target_level: int) -> Optional[dict]:
    """Return cost dict to reach `target_level`. None means migration-only."""
    table = UPGRADE_COSTS.get(slug)
    if not table:
        return None
    if target_level < 1 or target_level >= len(table):
        return None
    return table[target_level]


__all__ = ["UPGRADE_COSTS", "cost_for"]
