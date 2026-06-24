"""Guilds services (Phase 5.5c).

Pure business logic + serialization for the guilds domain. All functions
accept the Motor `db` handle as first arg → unit-testable. Behavior is
byte-identical to the previous inline implementation in `server.py`.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def guild_public(doc: dict) -> dict:
    """Project a Mongo guild document to its public JSON shape.

    Includes the Phase-8 sticky-peak field `max_team_power_ever`.
    """
    return {
        "id": doc["id"],
        "owner_user_id": doc["owner_user_id"],
        "name": doc["name"],
        "description": doc.get("description", ""),
        "level": doc.get("level", 1),
        "reputation": doc.get("reputation", 0),
        "gold": doc.get("gold", 100),
        # Phase 8: peak team_power across all expeditions (sticky for gate)
        "max_team_power_ever": int(doc.get("max_team_power_ever", 0)),
        "created_at": doc["created_at"],
        "updated_at": doc["updated_at"],
    }


async def user_guild_or_404(db, user_id: str) -> dict:
    """Return the guild owned by `user_id` or raise HTTP 404."""
    guild = await db.guilds.find_one({"owner_user_id": user_id}, {"_id": 0})
    if not guild:
        raise HTTPException(status_code=404, detail="No guild found for this user")
    return guild


async def create_guild_for_user(
    db, user_id: str, name: str, description: str
) -> dict:
    """Insert a new guild owned by `user_id`. Raises 400 on duplicate.

    Idempotency is enforced both at the application level (find_one check)
    and at the index level (unique index on `owner_user_id` catches a race).
    """
    existing = await db.guilds.find_one({"owner_user_id": user_id})
    if existing:
        raise HTTPException(status_code=400, detail="You already own a guild")

    now = utc_now()
    guild_doc = {
        "id": str(uuid.uuid4()),
        "owner_user_id": user_id,
        "name": name.strip(),
        "description": description.strip(),
        "level": 1,
        "reputation": 0,
        "gold": 100,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    try:
        await db.guilds.insert_one(guild_doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="You already own a guild")
    return guild_doc


async def compute_dashboard_stats(db, guild: dict) -> dict:
    """Compute the on-the-fly dashboard projection for a guild.

    Returns a dict matching the public `/api/guilds/me` extension fields:
    `adventurer_count`, `active_expedition_count`, `last_expedition_id/summary`,
    `highest_dungeon_slug`, `total_expeditions_completed`, `last_loot_item`.
    """
    guild_id = guild["id"]

    adv_count = await db.adventurers.count_documents({"guild_id": guild_id})
    active_exp = await db.expeditions.count_documents(
        {"guild_id": guild_id, "status": "in_progress"}
    )
    last_exp = await db.expeditions.find_one(
        {"guild_id": guild_id},
        {"_id": 0, "id": 1, "status": 1, "result_summary": 1, "completed_at": 1, "created_at": 1},
        sort=[("created_at", -1)],
    )

    # Phase 7: dashboard progression stats
    total_completed = await db.expeditions.count_documents(
        {"guild_id": guild_id, "status": "completed"}
    )
    highest_dungeon_slug: Optional[str] = None
    cursor = db.expeditions.find(
        {"guild_id": guild_id, "status": "completed", "result_summary": "Success"},
        {"_id": 0, "dungeon_id": 1},
    )
    success_dungeon_ids = list({row["dungeon_id"] async for row in cursor})
    if success_dungeon_ids:
        ranked = (
            await db.dungeons.find(
                {"id": {"$in": success_dungeon_ids}}, {"_id": 0, "slug": 1, "difficulty": 1}
            )
            .sort("difficulty", -1)
            .to_list(10)
        )
        if ranked:
            highest_dungeon_slug = ranked[0]["slug"]

    last_loot_item: Optional[dict] = None
    last_exp_with_loot = await db.expeditions.find_one(
        {"guild_id": guild_id, "status": "completed", "loot_item_ids": {"$ne": []}},
        {"_id": 0, "loot_item_ids": 1, "completed_at": 1, "created_at": 1},
        sort=[("completed_at", -1)],
    )
    if last_exp_with_loot and last_exp_with_loot.get("loot_item_ids"):
        last_item_id = last_exp_with_loot["loot_item_ids"][-1]
        item_doc = await db.items.find_one(
            {"id": last_item_id}, {"_id": 0, "name": 1, "rarity": 1}
        )
        if item_doc:
            last_loot_item = {
                "name": item_doc["name"],
                "rarity": item_doc.get("rarity", "Common"),
            }

    return {
        "adventurer_count": adv_count,
        "active_expedition_count": active_exp,
        "last_expedition_id": last_exp["id"] if last_exp else None,
        "last_expedition_summary": last_exp.get("result_summary") if last_exp else None,
        "highest_dungeon_slug": highest_dungeon_slug,
        "total_expeditions_completed": total_completed,
        "last_loot_item": last_loot_item,
    }


__all__ = [
    "utc_now",
    "guild_public",
    "user_guild_or_404",
    "create_guild_for_user",
    "compute_dashboard_stats",
]
