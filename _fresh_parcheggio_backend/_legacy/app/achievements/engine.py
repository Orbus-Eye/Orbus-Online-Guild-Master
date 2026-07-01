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
    db, guild_id: str, slug: str, xp: int, points: int,
    *, trigger_event: Optional[str] = None,
) -> None:
    """ROUND 16.A Phase 2 — emit canonical `achievement_unlocked` audit.

    Idempotency is enforced one level up by the `completed_at: None` CAS
    in `find_one_and_update`. By the time we get here the achievement
    has flipped exactly once, so emitting unconditionally is safe.
    """
    try:
        from app.audit.log import write_audit
        await write_audit(
            db,
            event_type="achievement_unlocked",
            actor_guild_id=guild_id,
            source="achievement.engine",
            related_entity_id=slug,
            metadata={
                "achievement_slug": slug,
                "guild_xp_reward": int(xp),
                "achievement_points_reward": int(points),
                "trigger_event_that_caused_it": trigger_event,
            },
        )
    except Exception:  # noqa: BLE001
        # Audit is best-effort; reward already credited.
        pass


async def add_guild_xp(
    db,
    guild_id: str,
    amount: int,
    *,
    source: str,
    source_id: Optional[str] = None,
    points_delta: int = 0,
) -> dict:
    """ROUND 16.A Phase 2 — canonical Guild XP helper.

    Single, audited entry-point for all `guild_xp` credits. Wraps the
    atomic `$inc` previously inlined in `_apply_reward` so every XP
    transaction can be traced via the `guild_xp_gained` audit event.

    `source` is a free-form enum-style string: `achievement_unlock`,
    `expedition_completed`, `daily_bonus`, etc. `source_id` ties the
    event back to the originating row (achievement slug, expedition id…).

    Returns the post-update guild snapshot (same shape as the legacy
    `_apply_reward` helper). When `amount` is 0 we still recompute the
    level (no-op) but do NOT emit an audit row — there is nothing to
    audit when nothing happened.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    if amount == 0 and points_delta == 0:
        # Read-only path — return current snapshot without touching DB.
        cur = await db.guilds.find_one(
            {"id": guild_id},
            projection={
                "_id": 0, "guild_xp": 1, "guild_level": 1,
                "achievement_points": 1, "last_guild_level_up_at": 1,
            },
        ) or {}
        return {
            "guild_xp": int(cur.get("guild_xp", 0) or 0),
            "guild_level": int(cur.get("guild_level", 1) or 1),
            "achievement_points": int(cur.get("achievement_points", 0) or 0),
            "last_guild_level_up_at": cur.get("last_guild_level_up_at"),
        }

    updated = await db.guilds.find_one_and_update(
        {"id": guild_id},
        {
            "$inc": {
                "guild_xp": int(amount),
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

    # ROUND 16.A Phase 2 — emit `guild_xp_gained` audit event.
    if amount != 0:
        try:
            from app.audit.log import write_audit
            await write_audit(
                db,
                event_type="guild_xp_gained",
                actor_guild_id=guild_id,
                source=source or "unknown",
                related_entity_id=source_id,
                metadata={
                    "xp_amount": int(amount),
                    "source": source,
                    "source_id": source_id,
                    "new_total_xp": new_xp,
                    "new_level": int(updated.get("guild_level", new_level)),
                    "level_changed": bool(delta_level),
                },
            )
        except Exception:  # noqa: BLE001
            # Best-effort: XP already credited.
            pass

    return {
        "guild_xp": new_xp,
        "guild_level": int(updated.get("guild_level", new_level)),
        "achievement_points": int(updated.get("achievement_points", 0)),
        "last_guild_level_up_at": updated.get("last_guild_level_up_at"),
    }


async def _apply_reward(
    db, guild_id: str, xp_delta: int, points_delta: int,
    *, source_id: Optional[str] = None,
) -> dict:
    """Thin shim around `add_guild_xp` to keep the call sites stable."""
    return await add_guild_xp(
        db, guild_id, xp_delta,
        source="achievement_unlock",
        source_id=source_id,
        points_delta=points_delta,
    )


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

        snapshot = await _apply_reward(db, guild_id, xp_reward, pt_reward,
                                       source_id=slug)
        await _audit_completion(db, guild_id, slug, xp_reward, pt_reward,
                                trigger_event=event_type)
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


__all__ = ["evaluate_achievements", "add_guild_xp", "ALLOWED_REWARD_TYPES"]
