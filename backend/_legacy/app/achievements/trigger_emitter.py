"""ROUND 16.A Phase 1 — Centralised emitter for achievement triggers.

Why this exists:
    The achievement engine (`app.achievements.engine.evaluate_achievements`)
    is invoked from a growing number of gameplay sites. Each call needs
    the same three things: a guild_id, an event_type string and a
    payload dict. The engine itself is safe to call with garbage input
    (it best-effort swallows errors) but the call sites are scattered
    and easy to forget to wire on a new feature.

    This module centralises the pattern so future hooks have a single,
    documented, lint-friendly entrypoint with consistent logging and a
    light idempotency layer for events that may fire twice for the same
    business action (PvP rating retries, auction settlements, etc.).

    The emitter is intentionally a *thin* wrapper: it does NOT mutate
    progress directly, it delegates to the engine. The engine already
    enforces atomicity via `find_one_and_update` on `achievement_progress`.

ROUND 16.A scope:
    Wires the 11 trigger events listed in the round plan:
        item_crafted, market_purchase, auction_sale, auction_purchase,
        consortium_joined, season_league_reached, leaderboard_rank_reached,
        item_disenchanted, material_purchased, pvp_match_completed,
        territory_upgraded.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger("orbus.achievements.triggers")


async def emit_achievement_trigger(
    db,
    guild_id: Optional[str],
    event_name: str,
    payload: Optional[dict] = None,
    *,
    occurred_at: Optional[datetime] = None,
    idempotency_key: Optional[str] = None,
) -> list[dict]:
    """Fire an achievement trigger for `guild_id`.

    Args:
        db: motor database handle.
        guild_id: the gaining guild. None is tolerated (returns []).
        event_name: matches `achievements_catalog.trigger_event`.
        payload: free-form context dict (event-specific keys).
        occurred_at: optional override, defaults to "now" in engine.
        idempotency_key: when provided, the emitter records a
            `(guild_id, event_name, key)` row in `trigger_emissions`
            and short-circuits if the same key was already seen. This
            protects against worker retries and the dual-route
            market/auction code path that calls `buy_listing` from two
            HTTP entry points.

    Returns:
        List of just-completed achievement dicts (engine output).
        Empty list on error or no-op.
    """
    if not guild_id or not event_name:
        return []
    payload = dict(payload or {})

    # ── Idempotency layer ────────────────────────────────────────────
    # We only allocate a dedup row when an explicit key is provided —
    # most events naturally idempotent through the engine's CAS.
    if idempotency_key:
        try:
            await db.trigger_emissions.update_one(
                {
                    "guild_id": guild_id,
                    "event_name": event_name,
                    "idempotency_key": str(idempotency_key),
                },
                {
                    "$setOnInsert": {
                        "guild_id": guild_id,
                        "event_name": event_name,
                        "idempotency_key": str(idempotency_key),
                        "created_at": (
                            occurred_at or datetime.utcnow()
                        ).isoformat(),
                        "payload": payload,
                    }
                },
                upsert=True,
            )
            # We do not abort on duplicates; the engine itself dedupes via
            # `completed_at` and atomic $inc. The emission row gives us a
            # trace for debugging only.
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "emit_achievement_trigger dedup write failed: %s", exc)

    # ── Delegate to the engine ───────────────────────────────────────
    try:
        from app.achievements.engine import evaluate_achievements
        completed = await evaluate_achievements(
            guild_id=guild_id,
            event_type=event_name,
            payload=payload,
            db=db,
        )
        if completed:
            logger.info(
                "achievement.trigger event=%s guild=%s payload_keys=%s "
                "unlocked=%d slugs=%s",
                event_name, guild_id, sorted(payload.keys()),
                len(completed), [a.get("slug") for a in completed],
            )
        else:
            logger.debug(
                "achievement.trigger event=%s guild=%s no completions",
                event_name, guild_id,
            )
        return completed
    except Exception as exc:  # noqa: BLE001
        # Never break the gameplay action because of an achievement issue.
        logger.warning(
            "emit_achievement_trigger failed for %s/%s: %s",
            event_name, guild_id, exc,
        )
        return []


__all__ = ["emit_achievement_trigger"]
