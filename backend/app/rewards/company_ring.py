"""Secret, globally unique World Boss grant for the Company ring."""
from __future__ import annotations

from datetime import datetime, timezone
import secrets
import uuid

from pymongo.errors import DuplicateKeyError

from app.items.catalog_contract import ULTRA_RARE_RANDOM_DROP_SLUG


ONE_IN = 1_000_000
GLOBAL_CLAIM_ID = f"global-unique:{ULTRA_RARE_RANDOM_DROP_SLUG}"
WORLD_BOSS_SOURCE_SLUG = "alveora_moon_puppeteer"


def company_ring_world_boss_eligible(
    *, boss_slug: str, outcome: str, contribution: int
) -> bool:
    """Only a real contributor to a defeated Alveora receives a secret roll."""
    return (
        boss_slug == WORLD_BOSS_SOURCE_SLUG
        and outcome == "completed"
        and int(contribution or 0) > 0
    )


async def try_grant_company_ring_from_world_boss(
    db,
    *,
    guild_id: str,
    event_id: str,
    boss_slug: str,
    outcome: str,
    contribution: int,
) -> dict:
    """Roll once per guild/event and deliver at most one global instance."""
    if not company_ring_world_boss_eligible(
        boss_slug=boss_slug,
        outcome=outcome,
        contribution=contribution,
    ):
        return {"eligible": False, "granted": False}

    now = datetime.now(timezone.utc).isoformat()
    roll_id = f"company-ring-roll:world-boss:{event_id}:{guild_id}"
    roll_doc = await db.reward_secret_rolls.find_one({"id": roll_id}, {"_id": 0})
    if roll_doc is None:
        candidate = {
            "id": roll_id,
            "source_type": "world_boss",
            "source_id": event_id,
            "source_slug": boss_slug,
            "guild_id": guild_id,
            "item_slug": ULTRA_RARE_RANDOM_DROP_SLUG,
            "one_in": ONE_IN,
            "success": secrets.randbelow(ONE_IN) == 0,
            "created_at": now,
        }
        try:
            await db.reward_secret_rolls.insert_one(candidate)
            roll_doc = candidate
        except DuplicateKeyError:
            roll_doc = await db.reward_secret_rolls.find_one(
                {"id": roll_id}, {"_id": 0}
            )
    if not roll_doc or not roll_doc.get("success"):
        return {"eligible": True, "granted": False}

    claim = {
        "id": GLOBAL_CLAIM_ID,
        "item_slug": ULTRA_RARE_RANDOM_DROP_SLUG,
        "guild_id": guild_id,
        "source_type": "world_boss",
        "source_id": event_id,
        "source_slug": boss_slug,
        "source_roll_id": roll_id,
        "claimed_at": now,
        "delivered": False,
    }
    try:
        await db.reward_global_uniques.insert_one(dict(claim))
    except DuplicateKeyError:
        claim = await db.reward_global_uniques.find_one(
            {"id": GLOBAL_CLAIM_ID}, {"_id": 0}
        )
        if not claim or claim.get("source_roll_id") != roll_id:
            return {"eligible": True, "granted": False, "globally_claimed": True}

    item = await db.items.find_one(
        {"slug": ULTRA_RARE_RANDOM_DROP_SLUG, "is_active": True},
        {"_id": 0},
    )
    if not item:
        return {"eligible": True, "granted": False, "delivery_pending": True}

    await db.inventory_items.update_one(
        {"guild_id": guild_id, "item_id": item["id"]},
        {
            "$setOnInsert": {
                "id": str(uuid.uuid4()),
                "instance_id": str(uuid.uuid4()),
                "guild_id": guild_id,
                "item_id": item["id"],
                "quantity": 1,
                "refinement_level": 0,
                "enchants": [],
                "affixes": [],
                "reroll_count": 0,
                "is_bound": True,
                "bound_reason": "global_unique_world_boss_drop",
                "disenchanted_at": None,
                "acquired_at": now,
                "source": "world_boss_company_ring_ultra_rare",
                "source_event_id": event_id,
                "source_boss_slug": boss_slug,
            }
        },
        upsert=True,
    )
    await db.reward_global_uniques.update_one(
        {"id": GLOBAL_CLAIM_ID, "source_roll_id": roll_id},
        {"$set": {"delivered": True, "delivered_at": now}},
    )
    return {"eligible": True, "granted": True, "item_slug": item["slug"]}


__all__ = [
    "GLOBAL_CLAIM_ID",
    "ONE_IN",
    "WORLD_BOSS_SOURCE_SLUG",
    "company_ring_world_boss_eligible",
    "try_grant_company_ring_from_world_boss",
]
