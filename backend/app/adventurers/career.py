"""Adventurer career rarity driven exclusively by completed activities.

Rarity is not rolled and does not measure innate quality.  Every adventurer
starts Common and earns higher career ranks by being used by the player.
Activity events are recorded exactly once so lazy completion, recovery and
HTTP retries cannot duplicate progress.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError


ActivityKind = Literal["dungeon", "raid"]

CAREER_RARITY_ORDER: tuple[str, ...] = (
    "Common",
    "Uncommon",
    "Rare",
    "Epic",
    "Legendary",
)

CAREER_RARITY_THRESHOLDS: dict[str, dict[str, int]] = {
    "Common": {"dungeons": 0, "raids": 0},
    "Uncommon": {"dungeons": 50, "raids": 0},
    "Rare": {"dungeons": 150, "raids": 0},
    "Epic": {"dungeons": 500, "raids": 5},
    "Legendary": {"dungeons": 2000, "raids": 150},
}

CAREER_RARITY_STAT_MULTIPLIERS: dict[str, int] = {
    "Common": 1,
    "Uncommon": 2,
    "Rare": 4,
    "Epic": 8,
    "Legendary": 16,
}


def career_rarity_for_counts(dungeons: int, raids: int) -> str:
    """Return the highest career rarity reached by cumulative participation."""
    dungeon_count = max(0, int(dungeons or 0))
    raid_count = max(0, int(raids or 0))
    rarity = "Common"
    for candidate in CAREER_RARITY_ORDER[1:]:
        threshold = CAREER_RARITY_THRESHOLDS[candidate]
        if (
            dungeon_count >= threshold["dungeons"]
            and raid_count >= threshold["raids"]
        ):
            rarity = candidate
    return rarity


def career_stat_multiplier(adventurer: dict) -> int:
    """Return the multiplier earned from activity, never from a stored roll."""
    rarity = career_rarity_for_counts(
        adventurer.get("career_dungeons_completed", 0),
        adventurer.get("career_raids_completed", 0),
    )
    return CAREER_RARITY_STAT_MULTIPLIERS[rarity]


def career_effective_stats(
    adventurer: dict,
    stats: dict[str, int] | None = None,
) -> dict[str, int]:
    """Derive primary stats without mutating or compounding stored base stats."""
    source = stats if stats is not None else adventurer
    multiplier = career_stat_multiplier(adventurer)
    return {
        stat: max(0, int(source.get(stat, 0) or 0)) * multiplier
        for stat in ("strength", "agility", "intellect", "endurance", "faith")
    }


def career_progress_snapshot(adventurer: dict) -> dict:
    """Build the public career progress and next milestone for one adventurer."""
    dungeons = max(0, int(adventurer.get("career_dungeons_completed", 0) or 0))
    raids = max(0, int(adventurer.get("career_raids_completed", 0) or 0))
    rarity = career_rarity_for_counts(dungeons, raids)
    try:
        current_idx = CAREER_RARITY_ORDER.index(rarity)
    except ValueError:
        current_idx = 0
        rarity = "Common"
    next_rarity = (
        CAREER_RARITY_ORDER[current_idx + 1]
        if current_idx + 1 < len(CAREER_RARITY_ORDER)
        else None
    )
    next_threshold = (
        dict(CAREER_RARITY_THRESHOLDS[next_rarity]) if next_rarity else None
    )
    return {
        "rarity": rarity,
        "stat_multiplier": CAREER_RARITY_STAT_MULTIPLIERS[rarity],
        "dungeons_completed": dungeons,
        "raids_completed": raids,
        "next_rarity": next_rarity,
        "next_threshold": next_threshold,
        "remaining": (
            {
                "dungeons": max(0, next_threshold["dungeons"] - dungeons),
                "raids": max(0, next_threshold["raids"] - raids),
            }
            if next_threshold
            else None
        ),
    }


async def record_career_activity(
    db,
    *,
    guild_id: str,
    adventurer_id: str,
    activity_kind: ActivityKind,
    activity_id: str,
) -> dict | None:
    """Credit one terminal activity exactly once and promote when eligible."""
    if activity_kind not in {"dungeon", "raid"}:
        raise ValueError(f"Unsupported career activity: {activity_kind}")
    now = datetime.now(timezone.utc).isoformat()
    event_id = f"{activity_kind}:{activity_id}:{adventurer_id}"
    try:
        await db.adventurer_career_events.insert_one(
            {
                "id": event_id,
                "guild_id": guild_id,
                "adventurer_id": adventurer_id,
                "activity_kind": activity_kind,
                "activity_id": activity_id,
                "created_at": now,
            }
        )
    except DuplicateKeyError:
        return await db.adventurers.find_one(
            {"id": adventurer_id, "guild_id": guild_id}, {"_id": 0}
        )

    counter = (
        "career_dungeons_completed"
        if activity_kind == "dungeon"
        else "career_raids_completed"
    )
    updated = await db.adventurers.find_one_and_update(
        {
            "id": adventurer_id,
            "guild_id": guild_id,
            "is_retired": {"$ne": True},
        },
        {
            "$inc": {counter: 1},
            "$set": {"updated_at": now},
        },
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        return None

    earned_rarity = career_rarity_for_counts(
        updated.get("career_dungeons_completed", 0),
        updated.get("career_raids_completed", 0),
    )
    previous_rarity = updated.get("rarity") or "Common"
    if earned_rarity != previous_rarity:
        promoted = (
            previous_rarity in CAREER_RARITY_ORDER
            and CAREER_RARITY_ORDER.index(earned_rarity)
            > CAREER_RARITY_ORDER.index(previous_rarity)
        )
        await db.adventurers.update_one(
            {"id": adventurer_id, "guild_id": guild_id},
            {
                "$set": {
                    "rarity": earned_rarity,
                    **({"career_rarity_promoted_at": now} if promoted else {}),
                    "updated_at": now,
                }
            },
        )
        updated["rarity"] = earned_rarity
        if promoted:
            updated["career_rarity_promoted_at"] = now
    return updated


async def record_career_activity_for_many(
    db,
    *,
    guild_id: str,
    adventurer_ids: list[str],
    activity_kind: ActivityKind,
    activity_id: str,
) -> list[dict]:
    """Credit every distinct participant, preserving deterministic order."""
    results: list[dict] = []
    for adventurer_id in dict.fromkeys(adventurer_ids):
        updated = await record_career_activity(
            db,
            guild_id=guild_id,
            adventurer_id=adventurer_id,
            activity_kind=activity_kind,
            activity_id=activity_id,
        )
        if updated:
            results.append(updated)
    return results


__all__ = [
    "CAREER_RARITY_ORDER",
    "CAREER_RARITY_STAT_MULTIPLIERS",
    "CAREER_RARITY_THRESHOLDS",
    "career_effective_stats",
    "career_progress_snapshot",
    "career_rarity_for_counts",
    "career_stat_multiplier",
    "record_career_activity",
    "record_career_activity_for_many",
]
