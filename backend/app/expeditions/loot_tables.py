"""Per-dungeon loot table + weighted sampler.

The sampler is async because it queries Mongo for the actual item pool;
the table itself is a pure constant.

Behaviour contract (Phase 7):
- On *failure*, only Common/Uncommon rarities may be returned (never
  Rare/Epic), as a consolation drop with low chance.
- On *success*, the per-dungeon weights apply.
"""
import random
from typing import Optional

from app.shared.constants import LOOT_DROP_CHANCE_LEGACY, LOOT_RARITIES_LEGACY


DUNGEON_LOOT_TABLES = {
    "goblin-warrens": {
        "success": {"chance": 0.50, "weights": {"Common": 85, "Uncommon": 15}},
        "failure": {"chance": 0.00, "weights": {}},
    },
    "shadow-crypts": {
        "success": {"chance": 0.65, "weights": {"Common": 50, "Uncommon": 35, "Rare": 15}},
        "failure": {"chance": 0.10, "weights": {"Common": 100}},
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
        if random.random() >= LOOT_DROP_CHANCE_LEGACY:
            return []
        pool = await db.items.find(
            {"is_active": True, "rarity": {"$in": LOOT_RARITIES_LEGACY}},
            {"_id": 0},
        ).to_list(100)
        return [random.choice(pool)["id"]] if pool else []

    branch = table["success" if success else "failure"]
    if random.random() >= branch["chance"]:
        return []
    weights = branch.get("weights") or {}
    rarities = [r for r, w in weights.items() if w > 0]
    if not rarities:
        return []
    # Failure branch is hard-capped to Common/Uncommon
    if not success:
        rarities = [r for r in rarities if r in ("Common", "Uncommon")]
        if not rarities:
            return []
    chosen_rarity = random.choices(
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
    return [random.choice(pool)["id"]] if pool else []
