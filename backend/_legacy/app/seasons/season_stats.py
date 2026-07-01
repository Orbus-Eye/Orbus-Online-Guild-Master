"""ROUND 13b — Seasonal incremental stat tracking.

Provides idempotent helpers that increment per-season counters on the
active `season_participation` document. Used by expedition/raid/contract/
training hooks to populate the 6 new seasonal leaderboard categories:

  * dungeon_clears
  * raid_clears
  * raid_score
  * territory_score        (read via delta: current - snapshot_at_start)
  * contracts_completed
  * training_score

Invariants (NON-negotiable):
  * No-op when there is no active season (`status != "active"`).
  * Idempotent: a replay of the same source event (expedition/raid/contract
    /training row) MUST NOT increment twice. Idempotency is enforced via a
    flag on the source document (`season_stat_recorded[field]=True`).
  * Audit on every successful increment.
  * No hard delete, no PII leak, no _id exposure.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("orbus.seasons.stats")

# Whitelist of fields the helper is allowed to increment.
ALLOWED_FIELDS = frozenset({
    "dungeon_clears",
    "raid_clears",
    "raid_score",
    "contracts_completed",
    "training_score",
})


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def get_active_season(db) -> Optional[dict]:
    """Returns the (single) active season doc, or None."""
    return await db.seasons.find_one({"status": "active"}, {"_id": 0})


async def _ensure_participation(db, *, season_id: str, guild_id: str) -> Optional[dict]:
    """Look up the participation; lazily create if missing AND the guild
    is non-test/non-demo. Returns the doc or None when guild is invalid.
    """
    part = await db.season_participations.find_one(
        {"season_id": season_id, "guild_id": guild_id}, {"_id": 0},
    )
    if part is not None:
        return part
    guild = await db.guilds.find_one({"id": guild_id}, {"_id": 0})
    if not guild:
        return None
    # Lazy bootstrap (used when a guild fires an event before joining a season
    # via PvP). Mirrors `seasons.services.get_or_create_participation` but
    # also snapshots `season_stats` defaults + territory baseline.
    from app.seasons.services import get_or_create_participation
    part = await get_or_create_participation(db, season_id=season_id, guild=guild)
    return part


async def _ensure_season_stats_subdoc(db, *, season_id: str, guild_id: str) -> None:
    """Initialise `season_stats` on the participation if missing.

    Snapshots `territory_score_at_start` lazily at first event.
    """
    part = await db.season_participations.find_one(
        {"season_id": season_id, "guild_id": guild_id},
        {"_id": 0, "season_stats": 1},
    )
    if not part:
        return
    if part.get("season_stats"):
        return
    # Snapshot current territory score.
    territory_at_start = await _compute_current_territory_score(db, guild_id)
    await db.season_participations.update_one(
        {"season_id": season_id, "guild_id": guild_id},
        {"$set": {
            "season_stats": {
                "dungeon_clears": 0,
                "raid_clears": 0,
                "raid_score": 0,
                "contracts_completed": 0,
                "training_score": 0,
                "territory_score_at_start": territory_at_start,
                "last_updated_at": _now_iso(),
            },
            "updated_at": _now_iso(),
        }},
    )


async def _compute_current_territory_score(db, guild_id: str) -> int:
    """Sum of `level` across the guild's `guild_structures.structures` dict.

    Mirrors `multi_category._calc_territory` so the seasonal delta uses the
    same scoring formula as the global category.
    """
    doc = await db.guild_structures.find_one(
        {"guild_id": guild_id}, {"_id": 0, "structures": 1},
    )
    if not doc:
        return 0
    total = 0
    for _slug, v in (doc.get("structures") or {}).items():
        if isinstance(v, dict):
            total += int(v.get("level", 0) or 0)
    return total


async def increment_seasonal_stat(
    db,
    *,
    guild_id: str,
    field: str,
    delta: int = 1,
    source: str = "unknown",
    source_collection: Optional[str] = None,
    source_id: Optional[str] = None,
    flag_key: Optional[str] = None,
) -> dict:
    """Increment `season_stats.<field>` by `delta` on the active season's
    participation document for `guild_id`, **once per source event**.

    Idempotency contract:
      * If `source_collection` + `source_id` + `flag_key` are all provided,
        the increment is atomically gated by setting `flag_key=True` on the
        source row via a CAS update with `flag_key != True` filter. A
        replay of the same event finds the flag already set and no-ops.
      * If any of those args is None, the caller asserts the call site is
        already idempotent (e.g. the source row was just transitioned to
        a terminal status atomically in the same transaction).

    Always best-effort: any error logged + swallowed (the upstream event
    must not be aborted because the LB hook failed).

    Returns a small report dict for tests/diagnostics:
        {"applied": bool, "reason": str, "season_id": str|None,
         "guild_id": str, "field": str, "delta": int}
    """
    report = {
        "applied": False,
        "reason": "",
        "season_id": None,
        "guild_id": guild_id,
        "field": field,
        "delta": delta,
    }
    try:
        if field not in ALLOWED_FIELDS:
            report["reason"] = "field_not_allowed"
            logger.warning("season_stat: rejected field=%s (not allowed)", field)
            return report
        season = await get_active_season(db)
        if not season:
            report["reason"] = "no_active_season"
            return report
        season_id = season["season_id"]
        report["season_id"] = season_id

        # Idempotency CAS on source row.
        if source_collection and source_id and flag_key:
            coll = getattr(db, source_collection)
            updated = await coll.find_one_and_update(
                {"id": source_id, flag_key: {"$ne": True}},
                {"$set": {flag_key: True, f"{flag_key}_at": _now_iso(),
                          f"{flag_key}_season_id": season_id}},
            )
            if not updated:
                report["reason"] = "already_recorded"
                return report

        # Ensure participation + season_stats subdoc exist.
        part = await _ensure_participation(db, season_id=season_id, guild_id=guild_id)
        if not part:
            report["reason"] = "no_participation"
            return report
        await _ensure_season_stats_subdoc(db, season_id=season_id, guild_id=guild_id)

        # Apply the increment.
        await db.season_participations.update_one(
            {"season_id": season_id, "guild_id": guild_id},
            {"$inc": {f"season_stats.{field}": int(delta)},
             "$set": {"season_stats.last_updated_at": _now_iso(),
                      "updated_at": _now_iso()}},
        )

        # Audit event (best-effort).
        try:
            from app.audit.log import write_audit
            await write_audit(
                db, event_type="season_stat_incremented",
                actor_guild_id=guild_id,
                source=f"season_stats.{source}",
                related_entity_id=source_id,
                metadata={
                    "season_id": season_id, "field": field, "delta": int(delta),
                    "source_collection": source_collection,
                },
            )
        except Exception:  # noqa: BLE001
            pass

        # Invalidate seasonal cache so the next /api/leaderboard call sees the
        # fresh number (60s TTL is fine for global; the per-event freshness
        # matters for the actor's "did my action count?" perception).
        try:
            from app.leaderboard.seasonal import invalidate_seasonal_cache
            invalidate_seasonal_cache(season_id)
        except Exception:  # noqa: BLE001
            pass

        report["applied"] = True
        report["reason"] = "incremented"
        return report
    except Exception as exc:  # noqa: BLE001
        logger.warning("increment_seasonal_stat failed (field=%s guild=%s): %s",
                       field, guild_id, exc)
        report["reason"] = f"error:{exc.__class__.__name__}"
        return report


__all__ = [
    "ALLOWED_FIELDS",
    "get_active_season",
    "increment_seasonal_stat",
    "_compute_current_territory_score",
]
