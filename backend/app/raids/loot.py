"""T6 source-authored raid item rewards.

One deterministic roll is made per raid instance. The grant ledger and
inventory upsert make completion/recovery replays safe.
"""
from __future__ import annotations

from datetime import datetime, timezone
import random
import uuid

from app.items.catalog_contract import ITEM_CATALOG_VERSION_T6
from app.raids.contracts import RAID_CONTRACTS
from app.rewards.source_engine import evaluate_reward_eligibility
from app.shared.content_curve import RAID_CURVE


RAID_ITEM_DROP_PROFILES = {
    "moonfall-vigil": {
        "victory": (0.72, {"Uncommon": 35, "Rare": 65}),
        "partial": (0.20, {"Uncommon": 75, "Rare": 25}),
    },
    "broken-bastion-siege": {
        "victory": (0.78, {"Rare": 55, "Epic": 45}),
        "partial": (0.24, {"Rare": 85, "Epic": 15}),
    },
    "necropolis-bells": {
        "victory": (0.84, {"Rare": 35, "Epic": 65}),
        "partial": (0.28, {"Rare": 75, "Epic": 25}),
    },
    "dragon-vault": {
        "victory": (0.90, {"Epic": 96, "Legendary": 4}),
        "partial": (0.25, {"Epic": 100}),
    },
}


def _weighted_rarity(rng: random.Random, weights: dict[str, int]) -> str:
    rarities = tuple(weights)
    return rng.choices(
        rarities,
        weights=[weights[rarity] for rarity in rarities],
        k=1,
    )[0]


async def _authored_raid_pool(
    db,
    *,
    guild_id: str,
    raid_slug: str,
    rarity: str,
    outcome: str,
) -> list[dict]:
    contract = RAID_CONTRACTS[raid_slug]["reward_profile"]
    if rarity not in contract["allowed_rarities"]:
        return []
    if rarity == "Legendary" and outcome != "victory":
        return []
    policy_id = contract["source_policy_id"]
    level = RAID_CURVE[raid_slug].required_level
    owned_item_ids = await db.inventory_items.distinct(
        "item_id",
        {"guild_id": guild_id},
    )
    query = {
            "is_active": True,
            "is_test": {"$ne": True},
            "catalog_version": ITEM_CATALOG_VERSION_T6,
            "rarity": rarity,
            "acquisition_sources": {
                "$elemMatch": {
                    "source_type": "raid",
                    "source_slug": raid_slug,
                    "source_policy_id": policy_id,
                }
            },
        }
    if owned_item_ids:
        query["id"] = {"$nin": owned_item_ids}
    rows = await db.items.find(
        query,
        {"_id": 0},
    ).sort("slug", 1).to_list(500)
    return [
        item
        for item in rows
        if evaluate_reward_eligibility(
            item=item,
            source_policy_id=policy_id,
            adventurer_level=level,
        )["eligible"]
    ]


async def grant_raid_item_reward(
    db,
    *,
    guild_id: str,
    raid_id: str,
    raid_slug: str,
    outcome: str,
) -> dict | None:
    """Roll and grant at most one item, idempotently, for a raid instance."""
    existing = await db.raid_item_reward_grants.find_one(
        {"raid_id": raid_id},
        {"_id": 0},
    )
    if existing and existing.get("status") == "applied":
        return existing.get("reward")

    profile = RAID_ITEM_DROP_PROFILES.get(raid_slug, {}).get(outcome)
    reward = None
    if profile:
        chance, weights = profile
        rng = random.Random(f"t6-raid-item:{raid_id}")
        if rng.random() < chance:
            rarity = _weighted_rarity(rng, weights)
            pool = await _authored_raid_pool(
                db,
                guild_id=guild_id,
                raid_slug=raid_slug,
                rarity=rarity,
                outcome=outcome,
            )
            if pool:
                item = pool[rng.randrange(len(pool))]
                reward = {
                    "item_id": item["id"],
                    "item_slug": item["slug"],
                    "display_name_it": item["display_name_it"],
                    "rarity": item["rarity"],
                    "source_policy_id": item["source_policy_id"],
                }

    now = datetime.now(timezone.utc).isoformat()
    grant_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"orbus:t6:raid-item:{raid_id}",
        )
    )
    await db.raid_item_reward_grants.update_one(
        {"raid_id": raid_id},
        {
            "$setOnInsert": {
                "id": grant_id,
                "raid_id": raid_id,
                "guild_id": guild_id,
                "raid_slug": raid_slug,
                "reward": reward,
                "status": "pending",
                "created_at": now,
            }
        },
        upsert=True,
    )
    ledger = await db.raid_item_reward_grants.find_one(
        {"raid_id": raid_id},
        {"_id": 0},
    )
    reward = ledger.get("reward") if ledger else reward
    if reward:
        await db.inventory_items.update_one(
            {"source_grant_id": grant_id},
            {
                "$setOnInsert": {
                    "id": str(uuid.uuid4()),
                    "instance_id": str(uuid.uuid4()),
                    "source_grant_id": grant_id,
                    "guild_id": guild_id,
                    "item_id": reward["item_id"],
                    "quantity": 1,
                    "refinement_level": 0,
                    "enchants": [],
                    "affixes": [],
                    "reroll_count": 0,
                    "is_bound": reward["source_policy_id"] == "raid_level80_victory",
                    "disenchanted_at": None,
                    "acquired_at": now,
                    "source": "t6_raid_item_reward",
                }
            },
            upsert=True,
        )
    await db.raid_item_reward_grants.update_one(
        {"raid_id": raid_id},
        {"$set": {"status": "applied", "applied_at": now}},
    )
    return reward


__all__ = [
    "RAID_ITEM_DROP_PROFILES",
    "grant_raid_item_reward",
]
