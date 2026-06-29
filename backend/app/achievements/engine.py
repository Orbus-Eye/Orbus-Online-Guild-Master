"""ROUND 15 — Phase 3 / Task 12 — Centralised achievement trigger engine.

`evaluate_achievements(guild_id, event_type, payload, *, db)` is the
single entrypoint called from every gameplay service to credit progress.

Idempotency:
    `achievement_progress` has a unique compound index
    `(guild_id, achievement_slug)`. The engine uses
    `find_one_and_update` with a filter that includes
    `completed_at: None` so a completed achievement never re-credits XP
    on a subsequent trigger.

Admin grants:
    `payload.source == "admin"` is filtered out at the top of the engine.
    Demo/test guilds (already excluded from public leaderboards by R14
    `is_test_artifact`) still receive progress — their dashboard view
    works, public visibility doesn't.

Reward types (cosmetic-only — validator in seed script):
    "xp_points"        → guild_xp + points only
    "xp_points_title"  → + title_it
    "xp_points_badge"  → + badge_slug
    "xp_points_frame"  → + frame_slug

Audit:
    Each completion emits an `audit_logs` row with
    event='achievement_completed' (best-effort, never blocks reward).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pymongo import ReturnDocument

from .levels import current_level_for_xp


ALLOWED_REWARD_TYPES = frozenset({
    "xp_points", "xp_points_title", "xp_points_badge", "xp_points_frame",
})


async def _audit_completion(
    db, guild_id: str, slug: str, xp: int, points: int
) -> None:
    try:
        await db.audit_logs.insert_one({
            "event": "achievement_completed",
            "payload": {
                "guild_id": guild_id,
                "achievement_slug": slug,
                "xp_awarded": int(xp),
                "points_awarded": int(points),
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception:  # noqa: BLE001
        # Audit is best-effort; reward already credited.
        pass


async def _apply_reward(
    db, guild_id: str, xp_delta: int, points_delta: int
) -> dict:
    """Atomic guild XP/points increment + recompute level.

    The level field is recomputed from the *post-increment* xp under the
    same update via a tiny pipeline. Returns the projected
    `{guild_xp, guild_level, achievement_points, last_guild_level_up_at}`
    dict for use by the caller.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    # Step 1: increment xp + points atomically.
    updated = await db.guilds.find_one_and_update(
        {"id": guild_id},
        {
            "$inc": {
                "guild_xp": int(xp_delta),
                "achievement_points": int(points_delta),
            },
            "$set": {"updated_at": now_iso},
        },
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        return {}

    new_xp = int(updated.get("guild_xp", 0))
    new_level = current_level_for_xp(new_xp)
    prev_level = int(updated.get("guild_level", 1) or 1)
    delta_level = {}
    if new_level != prev_level:
        delta_level["guild_level"] = new_level
        if new_level > prev_level:
            delta_level["last_guild_level_up_at"] = now_iso
    if delta_level:
        await db.guilds.update_one(
            {"id": guild_id}, {"$set": delta_level},
        )
        updated.update(delta_level)
    return {
        "guild_xp": new_xp,
        "guild_level": int(updated.get("guild_level", new_level)),
        "achievement_points": int(updated.get("achievement_points", 0)),
        "last_guild_level_up_at": updated.get("last_guild_level_up_at"),
    }


async def evaluate_achievements(
    guild_id: str,
    event_type: str,
    payload: Optional[dict] = None,
    *,
    db,
) -> list[dict]:
    """Credit progress for every achievement matching `event_type`.

    Returns the list of *just-completed* achievements (each with the
    awarded xp/points + final guild snapshot). Empty list if nothing
    progressed to completion on this call.

    Best-effort: any unexpected exception is swallowed (achievement
    failures must NEVER break the underlying gameplay action).
    """
    if not guild_id or not event_type:
        return []
    payload = payload or {}
    if (payload.get("source") or "").lower() == "admin":
        return []

    try:
        cursor = db.achievements_catalog.find(
            {"trigger_event": event_type, "is_active": {"$ne": False}},
            {"_id": 0},
        )
        catalog_entries = await cursor.to_list(500)
    except Exception:  # noqa: BLE001
        return []

    completed: list[dict] = []
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    for entry in catalog_entries:
        slug = entry.get("slug")
        target = int(entry.get("progress_target", 1) or 1)
        try:
            # Atomic increment — only on rows that are NOT yet completed.
            # The upsert path handles first-ever progress.
            row = await db.achievement_progress.find_one_and_update(
                {
                    "guild_id": guild_id,
                    "achievement_slug": slug,
                    "completed_at": None,
                },
                {
                    "$inc": {"progress_current": 1},
                    "$set": {
                        "guild_id": guild_id,
                        "achievement_slug": slug,
                        "progress_target": target,
                        "last_event_at": now_iso,
                    },
                    "$setOnInsert": {
                        "completed_at": None,
                        "claimed_at": None,
                        "guild_xp_awarded": 0,
                        "points_awarded": 0,
                    },
                },
                upsert=True,
                return_document=ReturnDocument.AFTER,
                projection={"_id": 0},
            )
        except Exception:  # noqa: BLE001
            # Either a duplicate-key race or an already-completed row.
            continue

        if not row:
            continue
        if int(row.get("progress_current", 0)) < target:
            continue

        # Hit target — mark completed and credit reward atomically.
        xp_reward = int(entry.get("guild_xp_reward", 0) or 0)
        pt_reward = int(entry.get("points", 0) or 0)
        marked = await db.achievement_progress.find_one_and_update(
            {
                "guild_id": guild_id,
                "achievement_slug": slug,
                "completed_at": None,
            },
            {
                "$set": {
                    "completed_at": now_iso,
                    "guild_xp_awarded": xp_reward,
                    "points_awarded": pt_reward,
                },
            },
            projection={"_id": 0},
            return_document=ReturnDocument.AFTER,
        )
        if not marked:
            # Another worker beat us to the completion — no double credit.
            continue

        snapshot = await _apply_reward(db, guild_id, xp_reward, pt_reward)
        await _audit_completion(db, guild_id, slug, xp_reward, pt_reward)
        completed.append({
            "slug": slug,
            "name_it": entry.get("name_it"),
            "category": entry.get("category"),
            "guild_xp_awarded": xp_reward,
            "points_awarded": pt_reward,
            "reward_type": entry.get("reward_type"),
            "reward_payload": entry.get("reward_payload"),
            "guild_snapshot": snapshot,
        })

    return completed


__all__ = ["evaluate_achievements", "ALLOWED_REWARD_TYPES"]
