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
from typing import Optional

from app.shared.constants import LOOT_DROP_CHANCE_LEGACY, LOOT_RARITIES_LEGACY

# Phase 5.6: use cryptographically-secure RNG for loot rolls. The numerical
# distributions are unchanged — only the entropy source is upgraded.
_rng = secrets.SystemRandom()


DUNGEON_LOOT_TABLES = {
    # ─── Tier 1 — Common / Uncommon only ─────────────────────────────────────
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
        return [_rng.choice(pool)["id"]] if pool else []

    branch = table["success" if success else "failure"]
    if _rng.random() >= branch["chance"]:
        return []
    weights = branch.get("weights") or {}
    rarities = [r for r, w in weights.items() if w > 0]
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
    pool = await db.items.find(
        {"is_active": True, "rarity": chosen_rarity}, {"_id": 0}
    ).to_list(200)
    if not pool:
        # Degrade to next-lower rarity, still honouring the failure rule
        for r in ["Epic", "Rare", "Uncommon", "Common"]:
            if r == chosen_rarity:
                continue
            if not success and r not in ("Common", "Uncommon"):
                continue
            cand = await db.items.find(
                {"is_active": True, "rarity": r}, {"_id": 0}
            ).to_list(200)
            if cand:
                pool = cand
                break
    return [_rng.choice(pool)["id"]] if pool else []
