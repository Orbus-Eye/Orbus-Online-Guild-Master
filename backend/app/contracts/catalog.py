"""ROUND 6D — Contract catalog & reward tables (single source of truth).

Three layers, all server-authoritative:
  • Daily contracts: 3 fixed, UTC-midnight reset, low gold reward, NO reputation.
  • Weekly contracts: 4 active (rotation pool, ISO-Monday reset), medium gold +
    1-2 uncommon mats + small reputation reward.
  • Milestones: persistent achievements, 3-tier progressive unlock:
       Tier 1 — active from guild Lv1 (3 milestones)
       Tier 2 — unlocked after ALL Tier 1 claimed (4 milestones, placeholders)
       Tier 3 — unlocked after ALL Tier 2 claimed (3 milestones, placeholders)

Reward magnitudes (binding — DO NOT re-balance without product re-authorization):
   daily      ≈ 30% of a dungeon clear (no reputation, anti-grind)
   weekly     ≈ 80% of a dungeon clear (+ 1-3 reputation)
   milestone1 ≈ 100-200g + 1-2 uncommon mats + 5 reputation
   milestone2 ≈ 500-800g + 1 rare + 20 reputation
   milestone3 ≈ 2000-3000g + 1 epic + 50 reputation (~200% of a dungeon clear)

Objective types (canonical) — each must have a matching producer hook in
`app.contracts.services::increment_contract_progress`. Adding a new type
requires updating BOTH the catalog and the corresponding business module
hook in the same change.
"""
from __future__ import annotations

# Reputation source: NEW in 6D. Daily contracts NEVER award reputation
# (anti-inflation). Weekly + Milestone do.
REPUTATION_DAILY_MAX = 0  # invariant: daily.reward_reputation must be 0

# ──────────────────────────────────────────────────────────────────────
# Daily contracts (3 active, UTC midnight reset)
# ──────────────────────────────────────────────────────────────────────
DAILY_CONTRACTS: list[dict] = [
    {
        "slug": "daily_complete_expedition_1",
        "display_key": "contracts.daily.complete_expedition_1",
        "objective_type": "expeditions_completed",
        "objective_target": 1,
        "reward_gold": 60,
        "reward_materials": [],
        "reward_reputation": 0,
    },
    {
        "slug": "daily_market_listing_1",
        "display_key": "contracts.daily.market_listing_1",
        "objective_type": "market_listings_created",
        "objective_target": 1,
        "reward_gold": 40,
        "reward_materials": [{"slug": "iron_shard", "qty": 1}],
        "reward_reputation": 0,
    },
    {
        "slug": "daily_craft_item_1",
        "display_key": "contracts.daily.craft_item_1",
        "objective_type": "items_crafted",
        "objective_target": 1,
        "reward_gold": 50,
        "reward_materials": [],
        "reward_reputation": 0,
    },
    # ROUND 6E — 3 new daily contracts (+ feature_gated where applicable).
    # `feature_gate` is the structure slug that must be unlocked AND at the
    # minimum level shown — generation-time filter via
    # `app.contracts.services._is_objective_available`.
    {
        "slug": "daily_complete_raid_1",
        "display_key": "contracts.daily.complete_raid_1",
        "objective_type": "raids_completed",
        "objective_target": 1,
        "reward_gold": 70,
        "reward_materials": [{"slug": "iron_shard", "qty": 1}],
        "reward_reputation": 0,
        "feature_gate": {"slug": "war_room", "min_level": 1},
    },
    {
        "slug": "daily_forge_refine_1",
        "display_key": "contracts.daily.forge_refine_1",
        "objective_type": "forge_refinements",
        "objective_target": 1,
        "reward_gold": 50,
        "reward_materials": [{"slug": "iron_shard", "qty": 1}],
        "reward_reputation": 0,
        "feature_gate": {"slug": "forge", "min_level": 1},
    },
    {
        "slug": "daily_recruit_1",
        "display_key": "contracts.daily.recruit_1",
        "objective_type": "recruits_added",
        "objective_target": 1,
        "reward_gold": 50,
        "reward_materials": [],
        "reward_reputation": 0,
    },
]
DAILY_BY_SLUG = {c["slug"]: c for c in DAILY_CONTRACTS}

# ──────────────────────────────────────────────────────────────────────
# Weekly contracts (4 visible, ISO-Monday rotation from a 5-entry pool)
# ──────────────────────────────────────────────────────────────────────
# Includes the explicit 6C↔6D synergy: `weekly_apply_specialization_1`.
# Reward magnitude conservative (200g + 1 uncommon) to deter spec-and-respec
# abuse once respec ships in a later round.
WEEKLY_CONTRACT_POOL: list[dict] = [
    {
        "slug": "weekly_complete_expeditions_5",
        "display_key": "contracts.weekly.complete_expeditions_5",
        "objective_type": "expeditions_completed",
        "objective_target": 5,
        "reward_gold": 250,
        "reward_materials": [{"slug": "iron_shard", "qty": 2}],
        "reward_reputation": 2,
    },
    {
        "slug": "weekly_market_volume_3",
        "display_key": "contracts.weekly.market_volume_3",
        "objective_type": "market_sales_count",
        "objective_target": 3,
        "reward_gold": 180,
        "reward_materials": [{"slug": "raw_leather", "qty": 1}],
        "reward_reputation": 1,
    },
    {
        "slug": "weekly_upgrade_structure_1",
        "display_key": "contracts.weekly.upgrade_structure_1",
        "objective_type": "structures_upgraded",
        "objective_target": 1,
        "reward_gold": 300,
        "reward_materials": [{"slug": "lesser_arcane_dust", "qty": 1}],
        "reward_reputation": 3,
    },
    # FASE 9C — le specializzazioni non esistono più: il weekly premia
    # l'assegnazione di una classe a una recluta (Sala di Classe).
    {
        "slug": "weekly_assign_class_1",
        "display_key": "contracts.weekly.assign_class_1",
        "objective_type": "class_halls_assigned",
        "objective_target": 1,
        "reward_gold": 200,
        "reward_materials": [{"slug": "lesser_arcane_dust", "qty": 1}],
        "reward_reputation": 2,
    },
    # 5th pool entry rotates in once per 5 weeks — keeps variety without
    # exploding objective_type complexity.
    {
        "slug": "weekly_recruit_2",
        "display_key": "contracts.weekly.recruit_2",
        "objective_type": "recruits_added",
        "objective_target": 2,
        "reward_gold": 150,
        "reward_materials": [{"slug": "iron_shard", "qty": 1}],
        "reward_reputation": 1,
    },
    # ROUND 6E — 3 new weekly contracts (feature-gated where applicable)
    {
        "slug": "weekly_complete_raids_3",
        "display_key": "contracts.weekly.complete_raids_3",
        "objective_type": "raids_completed",
        "objective_target": 3,
        "reward_gold": 280,
        "reward_materials": [{"slug": "lesser_arcane_dust", "qty": 2}],
        "reward_reputation": 3,
        "feature_gate": {"slug": "war_room", "min_level": 1},
    },
    {
        "slug": "weekly_forge_actions_3",
        "display_key": "contracts.weekly.forge_actions_3",
        "objective_type": "forge_refinements",
        "objective_target": 3,
        "reward_gold": 200,
        "reward_materials": [{"slug": "iron_shard", "qty": 3}],
        "reward_reputation": 2,
        "feature_gate": {"slug": "forge", "min_level": 1},
    },
    {
        "slug": "weekly_auction_listings_2",
        "display_key": "contracts.weekly.auction_listings_2",
        "objective_type": "auction_listings_created",
        "objective_target": 2,
        "reward_gold": 220,
        "reward_materials": [{"slug": "raw_leather", "qty": 2}],
        "reward_reputation": 2,
        "feature_gate": {"slug": "auction_house", "min_level": 1},
    },
]
WEEKLY_BY_SLUG = {c["slug"]: c for c in WEEKLY_CONTRACT_POOL}
WEEKLY_ACTIVE_COUNT = 4

# ──────────────────────────────────────────────────────────────────────
# Milestones (persistent achievements, 3-tier progressive unlock)
# ──────────────────────────────────────────────────────────────────────
# Tier 1 — 3 entries, active from day 1.
MILESTONES_TIER_1: list[dict] = [
    {
        "slug": "milestone_run_10_expeditions",
        "tier": 1,
        "display_key": "contracts.milestone.run_10_expeditions",
        "objective_type": "expeditions_completed",
        "objective_target": 10,
        "reward_gold": 200,
        "reward_materials": [{"slug": "lesser_arcane_dust", "qty": 1}],
        "reward_reputation": 5,
    },
    {
        "slug": "milestone_craft_10_items",
        "tier": 1,
        "display_key": "contracts.milestone.craft_10_items",
        "objective_type": "items_crafted",
        "objective_target": 10,
        "reward_gold": 150,
        "reward_materials": [{"slug": "iron_shard", "qty": 3}],
        "reward_reputation": 5,
    },
    {
        "slug": "milestone_recruit_5_adventurers",
        "tier": 1,
        "display_key": "contracts.milestone.recruit_5_adventurers",
        "objective_type": "recruits_added",
        "objective_target": 5,
        "reward_gold": 100,
        "reward_materials": [{"slug": "raw_leather", "qty": 2}],
        "reward_reputation": 5,
    },
]
# Tier 2 — 7 entries, unlocked after ALL Tier 1 milestones are claimed.
# Reward magnitudes: 500-800g + 20 Rep + uncommon mats (no rare-tier item
# templates exist in the catalog, so we scale via increased qty of uncommons).
MILESTONES_TIER_2: list[dict] = [
    {
        "slug": "milestone_run_50_expeditions",
        "tier": 2,
        "display_key": "contracts.milestone.run_50_expeditions",
        "objective_type": "expeditions_completed",
        "objective_target": 50,
        "reward_gold": 750,
        "reward_materials": [{"slug": "lesser_arcane_dust", "qty": 3}],
        "reward_reputation": 20,
    },
    {
        "slug": "milestone_craft_50_items",
        "tier": 2,
        "display_key": "contracts.milestone.craft_50_items",
        "objective_type": "items_crafted",
        "objective_target": 50,
        "reward_gold": 600,
        "reward_materials": [{"slug": "iron_shard", "qty": 8}],
        "reward_reputation": 20,
    },
    {
        "slug": "milestone_recruit_25_adventurers",
        "tier": 2,
        "display_key": "contracts.milestone.recruit_25_adventurers",
        "objective_type": "recruits_added",
        "objective_target": 25,
        "reward_gold": 500,
        "reward_materials": [{"slug": "raw_leather", "qty": 5}],
        "reward_reputation": 20,
    },
    {
        "slug": "milestone_complete_10_raids",
        "tier": 2,
        "display_key": "contracts.milestone.complete_10_raids",
        "objective_type": "raids_completed",
        "objective_target": 10,
        "reward_gold": 800,
        "reward_materials": [{"slug": "greater_arcane_dust", "qty": 1}],
        "reward_reputation": 20,
    },
    {
        "slug": "milestone_market_25_sales",
        "tier": 2,
        "display_key": "contracts.milestone.market_25_sales",
        "objective_type": "market_sales_count",
        "objective_target": 25,
        "reward_gold": 600,
        "reward_materials": [{"slug": "lesser_arcane_dust", "qty": 3}],
        "reward_reputation": 20,
    },
    {
        "slug": "milestone_upgrade_5_structures",
        "tier": 2,
        "display_key": "contracts.milestone.upgrade_5_structures",
        "objective_type": "structures_upgraded",
        "objective_target": 5,
        "reward_gold": 700,
        "reward_materials": [{"slug": "lesser_arcane_dust", "qty": 2},
                             {"slug": "iron_shard", "qty": 5}],
        "reward_reputation": 20,
    },
    {
        "slug": "milestone_assign_3_classes",
        "tier": 2,
        "display_key": "contracts.milestone.assign_3_classes",
        "objective_type": "class_halls_assigned",
        "objective_target": 3,
        "reward_gold": 700,
        "reward_materials": [{"slug": "lesser_arcane_dust", "qty": 3}],
        "reward_reputation": 20,
    },
]
# Tier 3 — 7 entries, unlocked after ALL Tier 2 milestones are claimed.
# End-game tail: 2000-3000g + 50 Rep + greater_arcane_dust/iron_shard stacks.
MILESTONES_TIER_3: list[dict] = [
    {
        "slug": "milestone_run_200_expeditions",
        "tier": 3,
        "display_key": "contracts.milestone.run_200_expeditions",
        "objective_type": "expeditions_completed",
        "objective_target": 200,
        "reward_gold": 3000,
        "reward_materials": [{"slug": "greater_arcane_dust", "qty": 5},
                             {"slug": "iron_shard", "qty": 8}],
        "reward_reputation": 50,
    },
    {
        "slug": "milestone_craft_200_items",
        "tier": 3,
        "display_key": "contracts.milestone.craft_200_items",
        "objective_type": "items_crafted",
        "objective_target": 200,
        "reward_gold": 2500,
        "reward_materials": [{"slug": "greater_arcane_dust", "qty": 5}],
        "reward_reputation": 50,
    },
    {
        "slug": "milestone_recruit_50_adventurers",
        "tier": 3,
        "display_key": "contracts.milestone.recruit_50_adventurers",
        "objective_type": "recruits_added",
        "objective_target": 50,
        "reward_gold": 2000,
        "reward_materials": [{"slug": "greater_arcane_dust", "qty": 3},
                             {"slug": "raw_leather", "qty": 10}],
        "reward_reputation": 50,
    },
    {
        "slug": "milestone_complete_50_raids",
        "tier": 3,
        "display_key": "contracts.milestone.complete_50_raids",
        "objective_type": "raids_completed",
        "objective_target": 50,
        "reward_gold": 3000,
        "reward_materials": [{"slug": "greater_arcane_dust", "qty": 5},
                             {"slug": "iron_shard", "qty": 8}],
        "reward_reputation": 50,
    },
    {
        "slug": "milestone_market_100_sales",
        "tier": 3,
        "display_key": "contracts.milestone.market_100_sales",
        "objective_type": "market_sales_count",
        "objective_target": 100,
        "reward_gold": 2500,
        "reward_materials": [{"slug": "greater_arcane_dust", "qty": 5}],
        "reward_reputation": 50,
    },
    {
        "slug": "milestone_upgrade_15_structures",
        "tier": 3,
        "display_key": "contracts.milestone.upgrade_15_structures",
        "objective_type": "structures_upgraded",
        "objective_target": 15,
        "reward_gold": 2800,
        "reward_materials": [{"slug": "greater_arcane_dust", "qty": 5}],
        "reward_reputation": 50,
    },
    {
        "slug": "milestone_assign_8_classes",
        "tier": 3,
        "display_key": "contracts.milestone.assign_8_classes",
        "objective_type": "class_halls_assigned",
        "objective_target": 8,
        "reward_gold": 2200,
        "reward_materials": [{"slug": "greater_arcane_dust", "qty": 4}],
        "reward_reputation": 50,
    },
]

MILESTONES_ALL: list[dict] = MILESTONES_TIER_1 + MILESTONES_TIER_2 + MILESTONES_TIER_3
MILESTONES_BY_SLUG = {m["slug"]: m for m in MILESTONES_ALL}

# Tier-unlock rule: a tier is "unlocked" iff all milestones of the
# previous tier are `claimed`. Tier 1 is always unlocked.
TIER_UNLOCK_REQUIRES = {
    1: None,
    2: 1,
    3: 2,
}

# ──────────────────────────────────────────────────────────────────────
# Objective-type registry (must match what `increment_contract_progress`
# accepts). Tests assert that every contract/milestone declares a type in
# this set so a typo can't silently disable progress.
# ──────────────────────────────────────────────────────────────────────
VALID_OBJECTIVE_TYPES = frozenset({
    "expeditions_completed",
    "items_crafted",
    "market_listings_created",
    "market_sales_count",
    "structures_upgraded",
    # FASE 9C — sostituisce "specializations_applied": si assegnano
    # classi (Sala di Classe), non specializzazioni.
    "class_halls_assigned",
    "recruits_added",
    # ROUND 6E — new types (with matching hooks in raids + forge + auction).
    "raids_completed",
    "forge_refinements",
    "auction_listings_created",
})


def select_active_weekly(week_index: int) -> list[dict]:
    """Pick `WEEKLY_ACTIVE_COUNT` entries from the pool, rotating by ISO week.

    Deterministic per-week selection so two requests in the same week always
    see the same contracts regardless of which guild hits the endpoint first.
    """
    pool = WEEKLY_CONTRACT_POOL
    n = len(pool)
    return [pool[(week_index + i) % n] for i in range(WEEKLY_ACTIVE_COUNT)]


def assert_catalog_invariants() -> None:
    """Run at module import time so bad data never reaches production."""
    # Daily reputation invariant.
    for c in DAILY_CONTRACTS:
        assert c["reward_reputation"] == REPUTATION_DAILY_MAX, (
            f"daily contract {c['slug']!r} cannot grant reputation (anti-grind)"
        )
    # Objective type allowlist.
    for c in (*DAILY_CONTRACTS, *WEEKLY_CONTRACT_POOL, *MILESTONES_ALL):
        assert c["objective_type"] in VALID_OBJECTIVE_TYPES, (
            f"contract {c['slug']!r} declares unknown objective_type "
            f"{c['objective_type']!r}"
        )
    # Unique slugs across the catalog.
    all_slugs = [c["slug"] for c in DAILY_CONTRACTS]
    all_slugs += [c["slug"] for c in WEEKLY_CONTRACT_POOL]
    all_slugs += [m["slug"] for m in MILESTONES_ALL]
    assert len(all_slugs) == len(set(all_slugs)), "duplicate contract slug"


assert_catalog_invariants()


__all__ = [
    "DAILY_CONTRACTS",
    "DAILY_BY_SLUG",
    "WEEKLY_CONTRACT_POOL",
    "WEEKLY_BY_SLUG",
    "WEEKLY_ACTIVE_COUNT",
    "MILESTONES_ALL",
    "MILESTONES_BY_SLUG",
    "MILESTONES_TIER_1",
    "TIER_UNLOCK_REQUIRES",
    "VALID_OBJECTIVE_TYPES",
    "select_active_weekly",
]
