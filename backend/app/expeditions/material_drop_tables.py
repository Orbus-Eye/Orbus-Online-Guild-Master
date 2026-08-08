"""ROUND 15 — Fase 2 / Tasks C+D: Material drop tables and roller.

Materials drop INDEPENDENTLY from items. Both rolls are cryptographically
secure (secrets.SystemRandom) and produce 0..N results — they never
compete for a single slot.

Rate philosophy:
    The Phase-1 baseline assumed materials dropped only from quests/
    contracts. Round 15 introduces a dedicated expedition material pool.
    Per-rarity caps:
        Common ≤ 85%, Uncommon ≤ 55%, Rare ≤ 25%, Epic ≤ 15%,
        Legendary ≤ 10%.
    Baseline rates are documented in `round15_material_drop_diff.md`;
    the live rates here are the +70% boosted version, clipped to the
    caps above. Materials essential for early progression (iron_shard,
    raw_leather, healing_herb) are floored at 17% to keep mid-game
    progression visible.

Reward separation:
    `roll_materials_for_dungeon(db, dungeon, success)` returns a list of
    `{slug, qty, rarity}` dicts. Item drops continue to live in
    `loot_tables.roll_loot_for_dungeon`. The two rolls share no state.

Idempotency note:
    The expedition completer already uses CAS via the
    `status: in_progress → completing` claim. Materials are persisted
    on the same atomic write, so a retry of `_complete_one_expedition`
    can never duplicate the reward.
"""
from __future__ import annotations

import secrets

_rng = secrets.SystemRandom()


# Per-rarity cap (post +70% clipping).
RARITY_CAP = {
    "common": 0.85,
    "uncommon": 0.55,
    "rare": 0.25,
    "epic": 0.15,
    "legendary": 0.10,
}


# Baseline (pre +70% bump) and tuned drop rates per dungeon tier.
# Format: `tier → list[(material_slug, rarity, base_rate, qty_range)]`.
# `qty_range = (min, max)` inclusive.
#
# Tier 1 dungeons drop only common materials.
# Tier 2 introduces uncommons.
# Tier 3 starts rares.
# Tier 4 (5p elite) sees epic materials (dragon_essence) at the cap.
TIER_MATERIAL_TABLE: dict[str, list[tuple]] = {
    "T1": [
        ("iron_shard", "common", 0.20, (1, 2)),       # essential floor 17% → bumped to 34%
        ("raw_leather", "common", 0.15, (1, 2)),
        ("healing_herb", "common", 0.10, (1, 1)),
    ],
    "T2": [
        ("iron_shard", "common", 0.25, (1, 3)),
        ("raw_leather", "common", 0.20, (1, 2)),
        ("healing_herb", "common", 0.15, (1, 2)),
        ("arcane_dust", "uncommon", 0.15, (1, 1)),
        ("dull_gem", "uncommon", 0.10, (1, 1)),
    ],
    "T3": [
        ("iron_shard", "common", 0.30, (2, 4)),
        ("raw_leather", "common", 0.20, (1, 3)),
        ("arcane_dust", "uncommon", 0.20, (1, 2)),
        ("dull_gem", "uncommon", 0.12, (1, 2)),
        ("dragon_essence", "rare", 0.06, (1, 1)),
    ],
    "T4": [
        ("iron_shard", "common", 0.30, (2, 5)),
        ("arcane_dust", "uncommon", 0.25, (1, 3)),
        ("dull_gem", "uncommon", 0.15, (1, 2)),
        ("dragon_essence", "rare", 0.12, (1, 2)),
    ],
}


def _classify_dungeon_tier(dungeon: dict) -> str:
    """Best-effort tier classification using slug suffix + base_xp / level."""
    slug = (dungeon.get("slug") or "").lower()
    if slug in ("goblin-warrens", "sewer-nest", "bandit-hideout"):
        return "T1"
    if slug.endswith("-5p"):
        if "infernal-pit" in slug or "celestial-citadel" in slug or "world-tree-roots" in slug:
            return "T4"
        if "obsidian-arena" in slug or "clockwork-vault" in slug or "voidspire" in slug:
            return "T3"
        if "iron-foundry" in slug or "silent-monastery" in slug or "pirate-fleet" in slug:
            return "T2"
        return "T2"  # default for 5p
    if slug in ("druid-grove", "cursed-mines", "shadow-crypts", "sunken-library"):
        return "T2"
    if slug in ("lich-sanctum", "storm-spire", "dragons-hoard"):
        return "T3"
    # Numeric fallback via base_xp_reward.
    xp = int(dungeon.get("base_xp_reward", 0) or 0)
    if xp >= 100:
        return "T3"
    if xp >= 40:
        return "T2"
    return "T1"


# +70% boost factor applied at runtime to baseline rates.
BOOST_FACTOR = 1.70


def boosted_rate(base_rate: float, rarity: str) -> float:
    """Apply +70% boost, then clip to the per-rarity cap."""
    cap = RARITY_CAP.get(rarity.lower(), 1.0)
    return min(cap, round(base_rate * BOOST_FACTOR, 4))


async def roll_materials_for_dungeon(
    db, dungeon: dict, success: bool
) -> list[dict]:
    """Return a list of `{slug, qty, rarity}` drops. Independent of items.

    Behaviour:
      - On *failure*, each material rolls at 50% of its boosted rate
        (consolation prize, never zero per-tier guarantee).
      - On *success*, full boosted rate per entry.
      - Each material is rolled INDEPENDENTLY (no exclusive slot).
    """
    # FASE 3.1 (2026-08-08) — se il dungeon ha un reagente principale
    # mappato, cade SOLO quello (identità di farm per contenuto). La
    # tabella tier resta come fallback per slug non mappati (contenuti
    # futuri/test). Design: memory/fase3_design_reagenti_crafting.md §1.
    from app.expeditions.reagent_tables import (
        primary_reagent_for_dungeon,
        roll_primary_reagent,
    )
    slug = (dungeon.get("slug") or "").lower()
    if primary_reagent_for_dungeon(slug):
        drops = roll_primary_reagent(slug, success)
        if not drops:
            return []
        # Il reagente deve esistere nel catalogo items (seed fase 3).
        known_primary = await db.items.find_one(
            {"slug": drops[0]["slug"], "is_active": True,
             "item_type": "material"},
            {"_id": 0, "slug": 1},
        )
        return drops if known_primary else []

    tier = _classify_dungeon_tier(dungeon)
    entries = TIER_MATERIAL_TABLE.get(tier, [])
    if not entries:
        return []

    drops: list[dict] = []
    failure_penalty = 0.5 if not success else 1.0

    # We could pre-filter by which materials exist in the catalog, but
    # the items collection is small (<10) and this loop is at most ~5
    # entries — the overhead is negligible and the catalog query stays
    # explicit (clearer audit trail if a material slug drifts).
    known = {
        m["slug"]
        async for m in db.items.find(
            {"is_active": True, "item_type": "material"},
            {"_id": 0, "slug": 1},
        )
    }

    for slug, rarity, base_rate, (qmin, qmax) in entries:
        if slug not in known:
            continue
        effective_rate = boosted_rate(base_rate, rarity) * failure_penalty
        if _rng.random() < effective_rate:
            qty = _rng.randint(qmin, qmax)
            drops.append({"slug": slug, "rarity": rarity, "qty": qty})

    return drops


__all__ = [
    "TIER_MATERIAL_TABLE",
    "RARITY_CAP",
    "BOOST_FACTOR",
    "boosted_rate",
    "roll_materials_for_dungeon",
    "_classify_dungeon_tier",
]
