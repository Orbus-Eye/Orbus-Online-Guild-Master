"""ROUND 15 — Phase 3 / Task 11 — Achievement service projections.

Pure read-side helpers consumed by `app.achievements.routes`. No mutation.
"""
from __future__ import annotations

from typing import Optional

from .levels import xp_progress


def catalog_public(doc: dict, *, hide_payload: bool = False) -> dict:
    """Strip non-public fields from a catalog row."""
    out = {
        "slug": doc["slug"],
        "category": doc.get("category"),
        "name_it": doc.get("name_it"),
        "name_en": doc.get("name_en"),
        "description_it": doc.get("description_it"),
        "description_en": doc.get("description_en"),
        "points": int(doc.get("points", 0) or 0),
        "guild_xp_reward": int(doc.get("guild_xp_reward", 0) or 0),
        "reward_type": doc.get("reward_type"),
        "is_repeatable": bool(doc.get("is_repeatable", False)),
        "is_hidden": bool(doc.get("is_hidden", False)),
        "spoiler_level": doc.get("spoiler_level", "public"),
        "trigger_event": doc.get("trigger_event"),
        "progress_target": int(doc.get("progress_target", 1) or 1),
        "display_order": int(doc.get("display_order", 999) or 999),
    }
    if not hide_payload:
        out["reward_payload"] = doc.get("reward_payload") or {}
    return out


def progress_public(row: dict) -> dict:
    return {
        "achievement_slug": row.get("achievement_slug"),
        "progress_current": int(row.get("progress_current", 0) or 0),
        "progress_target": int(row.get("progress_target", 1) or 1),
        "completed_at": row.get("completed_at"),
        "claimed_at": row.get("claimed_at"),
        "guild_xp_awarded": int(row.get("guild_xp_awarded", 0) or 0),
        "points_awarded": int(row.get("points_awarded", 0) or 0),
        "last_event_at": row.get("last_event_at"),
    }


async def list_catalog(db, *, state: Optional[str] = None,
                       category: Optional[str] = None,
                       guild_id: Optional[str] = None) -> list[dict]:
    """List the catalog filtered by category. Hidden-spoiler entries are
    omitted unless `state="completed"` and the caller's guild has
    already completed them."""
    q: dict = {"is_active": {"$ne": False}}
    if category:
        q["category"] = category
    rows = await db.achievements_catalog.find(q, {"_id": 0}).sort(
        [("display_order", 1), ("slug", 1)],
    ).to_list(500)

    if state == "in_progress":
        # Hide all is_hidden=True from the in-progress listing — they only
        # appear once completed.
        rows = [r for r in rows if not r.get("is_hidden")]
    elif state == "completed" and guild_id:
        completed_slugs = {
            p["achievement_slug"]
            async for p in db.achievement_progress.find(
                {"guild_id": guild_id, "completed_at": {"$ne": None}},
                {"_id": 0, "achievement_slug": 1},
            )
        }
        rows = [r for r in rows if r["slug"] in completed_slugs]
    return [catalog_public(r) for r in rows]


async def get_progress_for_guild(db, guild_id: str) -> list[dict]:
    rows = await db.achievement_progress.find(
        {"guild_id": guild_id}, {"_id": 0},
    ).to_list(500)
    return [progress_public(r) for r in rows]


async def get_summary_for_guild(db, guild: dict) -> dict:
    completed_count = await db.achievement_progress.count_documents({
        "guild_id": guild["id"], "completed_at": {"$ne": None},
    })
    in_progress_count = await db.achievement_progress.count_documents({
        "guild_id": guild["id"], "completed_at": None,
    })
    total_catalog = await db.achievements_catalog.count_documents(
        {"is_active": {"$ne": False}},
    )
    xp = int(guild.get("guild_xp", 0) or 0)
    return {
        "guild_id": guild["id"],
        "guild_xp": xp,
        "guild_level": int(guild.get("guild_level", 1) or 1),
        "achievement_points": int(guild.get("achievement_points", 0) or 0),
        "completed_count": completed_count,
        "in_progress_count": in_progress_count,
        "total_catalog_count": total_catalog,
        "last_guild_level_up_at": guild.get("last_guild_level_up_at"),
        "progress": xp_progress(xp),
    }


__all__ = [
    "catalog_public",
    "progress_public",
    "list_catalog",
    "get_progress_for_guild",
    "get_summary_for_guild",
]
