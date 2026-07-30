"""Per-dungeon loot table + weighted sampler.

The sampler is async because it queries Mongo for the actual item pool;
the table itself is a pure constant.

Behaviour contract (Phase 7 + Phase 10):
- On *failure*, only Common/Uncommon rarities may be returned (never
  Rare/Epic), as a consolation drop with low chance. Enforced both by
  the per-dungeon `failure` weights AND by the hard-cap below.
- On *success*, the per-dungeon weights apply.
- Tier 1 dungeons: Common / Uncommon only.
- Tier 2 dungeons: Common / Uncommon / Rare.
- Tier 3 dungeons: Uncommon / Rare / Epic.

Phase 10 — expanded from 3 entries to 10. Original entries for
`goblin-warrens`, `shadow-crypts`, `dragons-hoard` are BYTE-IDENTICAL to
preserve existing behaviour and the `test_shadow_crypts_failure_never_rare`
invariant.
"""
import secrets

from app.items.catalog_contract import (
    ITEM_CATALOG_VERSION_T6,
    ordinary_random_drop_allowed,
)
from app.rewards.source_engine import evaluate_reward_eligibility
from app.shared.constants import LOOT_DROP_CHANCE_LEGACY, LOOT_RARITIES_LEGACY

# Phase 5.6: use cryptographically-secure RNG for loot rolls. The numerical
# distributions are unchanged — only the entropy source is upgraded.
_rng = secrets.SystemRandom()


def _eligible_ordinary_pool(pool: list[dict], dungeon: dict) -> list[dict]:
    content_level = int(
        dungeon.get("required_level")
        or dungeon.get("min_adventurer_level")
        or 1
    )
    return [
        item
        for item in pool
        if evaluate_reward_eligibility(
            item=item,
            source_policy_id="ordinary_dungeon",
            adventurer_level=content_level,
        )["eligible"]
    ]


async def _load_dungeon_source_pool(
    db,
    dungeon: dict,
    rarity: str,
    *,
    limit: int = 200,
) -> list[dict]:
    """Prefer the authored T6 source pool, then preserve legacy compatibility."""
    slug = str(dungeon.get("slug") or "")
    if slug:
        authored = await db.items.find(
            {
                "is_active": True,
                "is_test": {"$ne": True},
                "catalog_version": ITEM_CATALOG_VERSION_T6,
                "rarity": rarity,
                "acquisition_sources": {
                    "$elemMatch": {
                        "source_type": "dungeon",
                        "source_slug": slug,
                    }
                },
            },
            {"_id": 0},
        ).to_list(limit)
        authored = _eligible_ordinary_pool(authored, dungeon)
        if authored:
            return authored
    legacy = await db.items.find(
        {
            "is_active": True,
            "is_test": {"$ne": True},
            "rarity": rarity,
        },
        {"_id": 0},
    ).to_list(limit)
    return _eligible_ordinary_pool(legacy, dungeon)


DUNGEON_LOOT_TABLES = {
    # ─── Tier 1 — Common / Uncommon only ─────────────────────────────────────
    "training-yard": {
        "success": {"chance": 1.00, "weights": {"Common": 100}},
        "failure": {"chance": 0.00, "weights": {}},
    },
    "goblin-warrens": {
        "success": {"chance": 0.50, "weights": {"Common": 85, "Uncommon": 15}},
        "failure": {"chance": 0.00, "weights": {}},
    },
    "sewer-nest": {
        "success": {"chance": 0.45, "weights": {"Common": 90, "Uncommon": 10}},
        "failure": {"chance": 0.00, "weights": {}},
    },
    "bandit-hideout": {
        "success": {"chance": 0.55, "weights": {"Common": 75, "Uncommon": 25}},
        "failure": {"chance": 0.05, "weights": {"Common": 100}},
    },

    # ─── Tier 2 — Common / Uncommon / Rare ───────────────────────────────────
    "druid-grove": {
        "success": {"chance": 0.60, "weights": {"Common": 55, "Uncommon": 35, "Rare": 10}},
        "failure": {"chance": 0.08, "weights": {"Common": 100}},
    },
    "cursed-mines": {
        "success": {"chance": 0.62, "weights": {"Common": 50, "Uncommon": 35, "Rare": 15}},
        "failure": {"chance": 0.08, "weights": {"Common": 100}},
    },
    "shadow-crypts": {
        "success": {"chance": 0.65, "weights": {"Common": 50, "Uncommon": 35, "Rare": 15}},
        "failure": {"chance": 0.10, "weights": {"Common": 100}},
    },
    "sunken-library": {
        "success": {"chance": 0.65, "weights": {"Common": 45, "Uncommon": 35, "Rare": 20}},
        "failure": {"chance": 0.10, "weights": {"Common": 100}},
    },

    # ─── Tier 3 — Uncommon / Rare / Epic ─────────────────────────────────────
    "lich-sanctum": {
        "success": {"chance": 0.72, "weights": {"Uncommon": 55, "Rare": 35, "Epic": 10}},
        "failure": {"chance": 0.05, "weights": {"Uncommon": 100}},
    },
    "storm-spire": {
        "success": {"chance": 0.75, "weights": {"Uncommon": 50, "Rare": 38, "Epic": 12}},
        "failure": {"chance": 0.05, "weights": {"Uncommon": 100}},
    },
    "dragons-hoard": {
        "success": {"chance": 0.80, "weights": {"Uncommon": 50, "Rare": 35, "Epic": 15}},
        "failure": {"chance": 0.05, "weights": {"Common": 100}},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # ROUND 5 (Phase 17.5 + 18.1) — 12 new 5p dungeons
    # T1-5p: Common / Uncommon only (kid-friendly curve)
    # T2-5p: Common / Uncommon / Rare
    # T3-5p: Uncommon / Rare / Epic
    # T4-5p: Common 5% · Uncommon 25% · Rare 40% · Epic 30%.
    # Legendary/Unique are endgame-source rewards, never ordinary random loot.
    # ═══════════════════════════════════════════════════════════════════════════
    "wolf-den-5p": {
        "success": {"chance": 0.55, "weights": {"Common": 80, "Uncommon": 20}},
        "failure": {"chance": 0.05, "weights": {"Common": 100}},
    },
    "frost-cave-5p": {
        "success": {"chance": 0.55, "weights": {"Common": 75, "Uncommon": 25}},
        "failure": {"chance": 0.05, "weights": {"Common": 100}},
    },
    "salt-marsh-5p": {
        "success": {"chance": 0.58, "weights": {"Common": 70, "Uncommon": 30}},
        "failure": {"chance": 0.05, "weights": {"Common": 100}},
    },
    "iron-foundry-5p": {
        "success": {"chance": 0.65, "weights": {"Common": 45, "Uncommon": 40, "Rare": 15}},
        "failure": {"chance": 0.08, "weights": {"Common": 100}},
    },
    "silent-monastery-5p": {
        "success": {"chance": 0.65, "weights": {"Common": 40, "Uncommon": 42, "Rare": 18}},
        "failure": {"chance": 0.08, "weights": {"Common": 100}},
    },
    "pirate-fleet-5p": {
        "success": {"chance": 0.68, "weights": {"Common": 35, "Uncommon": 45, "Rare": 20}},
        "failure": {"chance": 0.08, "weights": {"Common": 100}},
    },
    "obsidian-arena-5p": {
        "success": {"chance": 0.72, "weights": {"Uncommon": 48, "Rare": 38, "Epic": 14}},
        "failure": {"chance": 0.05, "weights": {"Uncommon": 100}},
    },
    "clockwork-vault-5p": {
        "success": {"chance": 0.72, "weights": {"Uncommon": 45, "Rare": 40, "Epic": 15}},
        "failure": {"chance": 0.05, "weights": {"Uncommon": 100}},
    },
    "voidspire-5p": {
        "success": {"chance": 0.75, "weights": {"Uncommon": 40, "Rare": 42, "Epic": 18}},
        "failure": {"chance": 0.05, "weights": {"Uncommon": 100}},
    },
    # T4-5p Elite — ordinary item drops stop at Epic.
    "infernal-pit-5p": {
        "success": {"chance": 0.78, "weights": {"Common": 5, "Uncommon": 25, "Rare": 40, "Epic": 30}},
        "failure": {"chance": 0.05, "weights": {"Common": 50, "Uncommon": 50}},
    },
    "celestial-citadel-5p": {
        "success": {"chance": 0.78, "weights": {"Common": 5, "Uncommon": 25, "Rare": 40, "Epic": 30}},
        "failure": {"chance": 0.05, "weights": {"Common": 50, "Uncommon": 50}},
    },
    "world-tree-roots-5p": {
        "success": {"chance": 0.80, "weights": {"Common": 5, "Uncommon": 25, "Rare": 40, "Epic": 30}},
        "failure": {"chance": 0.05, "weights": {"Common": 50, "Uncommon": 50}},
    },
}


async def roll_loot_for_dungeon(db, dungeon: dict, success: bool) -> list[str]:
    """Roll at most one item id from the dungeon's loot pool.

    `db` is the active Motor AsyncIOMotorDatabase handle.
    """
    table = DUNGEON_LOOT_TABLES.get(dungeon.get("slug", ""))
    if not table:
        # Backward-compat fallback: legacy global pool (Common/Uncommon)
        if not success:
            return []
        if _rng.random() >= LOOT_DROP_CHANCE_LEGACY:
            return []
        pool = await db.items.find(
            {"is_active": True, "rarity": {"$in": LOOT_RARITIES_LEGACY}},
            {"_id": 0},
        ).to_list(100)
        pool = _eligible_ordinary_pool(pool, dungeon)
        return [_rng.choice(pool)["id"]] if pool else []

    branch = table["success" if success else "failure"]
    if _rng.random() >= branch["chance"]:
        return []
    weights = branch.get("weights") or {}
    # T0 defence-in-depth: stale/future tables cannot leak an endgame rarity
    # through the ordinary dungeon sampler.
    rarities = [
        r for r, w in weights.items()
        if w > 0 and ordinary_random_drop_allowed(r)
    ]
    if not rarities:
        return []
    # Failure branch is hard-capped to Common/Uncommon (defence-in-depth).
    if not success:
        rarities = [r for r in rarities if r in ("Common", "Uncommon")]
        if not rarities:
            return []
    chosen_rarity = _rng.choices(
        rarities, weights=[weights[r] for r in rarities], k=1
    )[0]
    pool = await _load_dungeon_source_pool(db, dungeon, chosen_rarity)
    if not pool:
        # Degrade to next-lower rarity, still honouring the failure rule
        for r in ["Epic", "Rare", "Uncommon", "Common"]:
            if r == chosen_rarity:
                continue
            if not success and r not in ("Common", "Uncommon"):
                continue
            cand = await _load_dungeon_source_pool(db, dungeon, r)
            if cand:
                pool = cand
                break
    return [_rng.choice(pool)["id"]] if pool else []
