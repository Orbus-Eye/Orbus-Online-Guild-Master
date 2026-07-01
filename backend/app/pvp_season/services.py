"""ROUND 16.3 Phase 7B — PvP season services.

Season lifecycle:
    - Season 1 bootstrapped on first hit to any pvp-season endpoint.
    - Each season lasts SEASON_DURATION_DAYS (7 days by default).
    - On any read after `ends_at`, an on-visit fallback calls
      `finalize_season_if_due()` which:
        1. CAS locks the season status active→closing (idempotent)
        2. Snapshots top10 per continent to `pvp_season_leaderboards`
        3. Awards cosmetics to top10 guilds (idempotent via unique index)
        4. Rolls the season to `finalized` and creates the next active one
    - No global scheduler; visitors drive rollover deterministically.

Anti-P2W: reads `guild_pvp_stats` (source of truth for Elo) but NEVER
writes to it. No stat/gold/XP changes anywhere in this module.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from pymongo.errors import DuplicateKeyError

from app.audit.log import write_audit
from app.pvp_season.cosmetics import (
    COSMETIC_CATALOG,
    CONTINENT_SLUGS,
    cosmetics_for_rank,
)


logger = logging.getLogger("orbus.pvp_season")


# ── Constants ───────────────────────────────────────────────────────
SEASON_DURATION_DAYS: int = 7
TOP_N_PER_CONTINENT: int = 10
MIN_GUILD_LEVEL_FOR_LEADERBOARD: int = 8  # aligned with PvP 7A gate


# ── Utilities ───────────────────────────────────────────────────────


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


# ── Index setup ─────────────────────────────────────────────────────


async def ensure_indexes(database=None) -> None:
    """Create Mongo indexes for the 3 season collections.

    Called from `app_factory.startup`. Idempotent (Mongo skips existing).
    """
    if database is None:
        from app.core.database import db as _db
        database = _db
    try:
        await database.pvp_seasons.create_index(
            [("status", 1), ("ends_at", 1)], name="status_ends_at",
        )
        await database.pvp_seasons.create_index(
            "id", unique=True, name="season_id_unique",
        )
        await database.pvp_seasons.create_index(
            "season_number", unique=True, name="season_number_unique",
        )
        await database.pvp_season_leaderboards.create_index(
            [("season_id", 1), ("continent_slug", 1), ("rank", 1)],
            unique=True, name="season_continent_rank_unique",
        )
        await database.pvp_season_leaderboards.create_index(
            [("guild_id", 1), ("season_id", 1)],
            name="guild_season_idx",
        )
        await database.pvp_cosmetics_unlocked.create_index(
            [("guild_id", 1), ("cosmetic_slug", 1)],
            unique=True, name="guild_cosmetic_unique",
        )
        await database.pvp_cosmetics_unlocked.create_index(
            [("guild_id", 1), ("unlocked_at", -1)],
            name="guild_unlocked_at_idx",
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("pvp_season indexes ensure failed: %s", exc)


# ── Season lifecycle ────────────────────────────────────────────────


async def _find_active_season(db) -> Optional[dict]:
    return await db.pvp_seasons.find_one(
        {"status": "active"}, {"_id": 0},
    )


async def _next_season_number(db) -> int:
    """Determine the next season_number monotonically."""
    doc = await db.pvp_seasons.find(
        {}, {"_id": 0, "season_number": 1},
    ).sort("season_number", -1).limit(1).to_list(1)
    if not doc:
        return 1
    return int(doc[0]["season_number"]) + 1


async def _create_next_season(db) -> dict:
    """Create the next active season (idempotent via season_number unique).

    Returns the created (or existing) season document.
    """
    now = _now()
    started = now
    ends = started + timedelta(days=SEASON_DURATION_DAYS)
    for _ in range(3):  # tiny retry loop for race on unique(season_number)
        num = await _next_season_number(db)
        doc = {
            "id": str(uuid.uuid4()),
            "season_number": num,
            "started_at": _iso(started),
            "ends_at": _iso(ends),
            "status": "active",
            "finalized_at": None,
            "created_at": _iso(now),
        }
        try:
            await db.pvp_seasons.insert_one({**doc})
        except DuplicateKeyError:
            # Concurrent bootstrap already created it; retry number lookup.
            continue
        await write_audit(
            db, event_type="PVP_SEASON_STARTED",
            related_entity_id=doc["id"], source="pvp_season",
            metadata={"season_number": num, "ends_at": doc["ends_at"]},
        )
        # Strip Mongo-added _id if any (we didn't set it, but be safe).
        doc.pop("_id", None)
        return doc
    # Fallback: fetch whatever is active now.
    active = await _find_active_season(db)
    if active is None:
        raise RuntimeError("pvp_season bootstrap failed after 3 tries")
    return active


async def get_or_bootstrap_active_season(db) -> dict:
    """Return the current active season, bootstrapping season 1 if none.

    Also performs the on-visit rollover: if the current active season is
    past its `ends_at`, finalize it and create the next one.
    """
    active = await _find_active_season(db)
    if active is None:
        return await _create_next_season(db)
    # On-visit fallback: rollover if expired.
    try:
        if _iso(_now()) >= active["ends_at"]:
            await finalize_season(db, active["id"])
            new_active = await _find_active_season(db)
            if new_active is not None:
                return new_active
    except Exception as exc:  # noqa: BLE001
        # Never crash a read handler because of rollover; log and return.
        logger.warning(
            "on_visit_rollover_failed season_id=%s err=%s",
            active.get("id"), exc,
        )
    return active


# ── Leaderboard computation ─────────────────────────────────────────


async def _compute_live_top_n(db, continent_slug: str,
                              n: int = TOP_N_PER_CONTINENT) -> list[dict]:
    """Compute the current top-N Elo ranking for a continent.

    Filters:
        - guild_world_presence.status == "active" && continent_slug matches
        - guilds.level >= MIN_GUILD_LEVEL_FOR_LEADERBOARD
        - guild_pvp_stats exists (fallback Elo=1200 for gate-passers with
          no battles yet — same default as ELO_DEFAULT in resolver)

    Returns rows with `{guild_id, guild_name, elo, wins, losses, draws, rank}`.
    """
    # 1) All active presences on this continent.
    presences = await db.guild_world_presence.find(
        {"continent_slug": continent_slug, "status": "active"},
        {"_id": 0, "guild_id": 1},
    ).to_list(10_000)
    presence_ids = [p["guild_id"] for p in presences]
    if not presence_ids:
        return []
    # 2) Filter guilds by min level.
    guilds = await db.guilds.find(
        {"id": {"$in": presence_ids},
         "level": {"$gte": MIN_GUILD_LEVEL_FOR_LEADERBOARD}},
        {"_id": 0, "id": 1, "name": 1, "level": 1},
    ).to_list(len(presence_ids))
    if not guilds:
        return []
    eligible_ids = [g["id"] for g in guilds]
    gmap = {g["id"]: g for g in guilds}
    # 3) Fetch PvP stats.
    stats = await db.guild_pvp_stats.find(
        {"guild_id": {"$in": eligible_ids}},
        {"_id": 0, "guild_id": 1, "elo": 1, "wins": 1,
         "losses": 1, "draws": 1},
    ).to_list(len(eligible_ids))
    stats_map = {s["guild_id"]: s for s in stats}
    # 4) Build rows (fallback to defaults for guilds w/o stats yet).
    rows = []
    for gid in eligible_ids:
        s = stats_map.get(gid, {})
        rows.append({
            "guild_id": gid,
            "guild_name": gmap[gid]["name"],
            "elo": int(s.get("elo") or 1200),
            "wins": int(s.get("wins") or 0),
            "losses": int(s.get("losses") or 0),
            "draws": int(s.get("draws") or 0),
        })
    # 5) Rank by (elo desc, wins desc, guild_id asc) — stable & deterministic.
    rows.sort(key=lambda r: (-r["elo"], -r["wins"], r["guild_id"]))
    top = rows[:n]
    for i, r in enumerate(top, start=1):
        r["rank"] = i
    return top


async def get_finalized_leaderboard(db, season_id: str,
                                    continent_slug: str) -> list[dict]:
    """Read a snapshotted leaderboard for a finalized season."""
    rows = await db.pvp_season_leaderboards.find(
        {"season_id": season_id, "continent_slug": continent_slug},
        {"_id": 0},
    ).sort("rank", 1).to_list(TOP_N_PER_CONTINENT)
    return rows


# ── Cosmetic award ──────────────────────────────────────────────────


async def award_cosmetic(db, *, guild_id: str, cosmetic_slug: str,
                         season_id: str, season_number: int,
                         continent_slug: str, rank: int) -> bool:
    """Idempotent award — returns True if a new row was inserted.

    Uniqueness enforced by `(guild_id, cosmetic_slug)`. If the guild has
    already unlocked this cosmetic in a previous season, we keep the
    ORIGINAL row (no duplicate, no overwrite of `unlocked_at`).
    """
    entry = COSMETIC_CATALOG.get(cosmetic_slug)
    if entry is None:
        logger.warning("award_cosmetic unknown slug=%s", cosmetic_slug)
        return False
    now = _now()
    doc = {
        "id": str(uuid.uuid4()),
        "guild_id": guild_id,
        "cosmetic_slug": cosmetic_slug,
        "cosmetic_type": entry["type"],
        "continent_slug": continent_slug,
        "season_id": season_id,
        "season_number": season_number,
        "rank_awarded": rank,
        "unlocked_at": _iso(now),
    }
    try:
        await db.pvp_cosmetics_unlocked.insert_one({**doc})
    except DuplicateKeyError:
        return False
    await write_audit(
        db, event_type="PVP_COSMETIC_AWARDED",
        actor_guild_id=guild_id, related_entity_id=cosmetic_slug,
        source="pvp_season",
        metadata={"cosmetic_slug": cosmetic_slug,
                  "cosmetic_type": entry["type"],
                  "continent_slug": continent_slug,
                  "season_number": season_number, "rank": rank},
    )
    return True


# ── Snapshot + finalize + rollover ───────────────────────────────────


async def finalize_season(db, season_id: str) -> dict:
    """Idempotent finalize of a season.

    Steps:
        1. CAS status active → closing (only one caller wins)
        2. For each continent: compute top10, insert into
           `pvp_season_leaderboards`, award cosmetics
        3. Mark season status=finalized, finalized_at=now
        4. Create the next active season (unless already exists)
        5. Emit PVP_SEASON_FINALIZED audit event

    Safe to re-invoke: after step 1 CAS fails, the caller returns without
    duplicating awards. Individual leaderboard rows use unique index for
    protection. Cosmetics use `award_cosmetic` (also unique).
    """
    now_iso = _iso(_now())
    cas = await db.pvp_seasons.update_one(
        {"id": season_id, "status": "active"},
        {"$set": {"status": "closing", "updated_at": now_iso}},
    )
    if cas.matched_count == 0:
        # Already closing or finalized → idempotent no-op path.
        current = await db.pvp_seasons.find_one({"id": season_id}, {"_id": 0})
        return {"season_id": season_id,
                "status": (current or {}).get("status", "unknown"),
                "rollover_created": False, "changed": False}

    season = await db.pvp_seasons.find_one({"id": season_id}, {"_id": 0})
    if season is None:
        return {"season_id": season_id, "status": "missing",
                "rollover_created": False, "changed": False}

    total_awarded = 0
    total_entries = 0
    for continent in CONTINENT_SLUGS:
        top = await _compute_live_top_n(db, continent, TOP_N_PER_CONTINENT)
        for row in top:
            slugs = cosmetics_for_rank(continent, row["rank"])
            lb_doc = {
                "id": str(uuid.uuid4()),
                "season_id": season_id,
                "continent_slug": continent,
                "guild_id": row["guild_id"],
                "guild_name_snapshot": row["guild_name"],
                "rank": row["rank"],
                "elo_snapshot": row["elo"],
                "wins_snapshot": row["wins"],
                "losses_snapshot": row["losses"],
                "draws_snapshot": row["draws"],
                "cosmetics_awarded": slugs,
                "snapshotted_at": now_iso,
            }
            try:
                await db.pvp_season_leaderboards.insert_one({**lb_doc})
                total_entries += 1
            except DuplicateKeyError:
                # Concurrent finalize inserted this rank already.
                pass
            # Award cosmetics.
            for slug in slugs:
                inserted = await award_cosmetic(
                    db,
                    guild_id=row["guild_id"],
                    cosmetic_slug=slug,
                    season_id=season_id,
                    season_number=int(season["season_number"]),
                    continent_slug=continent,
                    rank=row["rank"],
                )
                if inserted:
                    total_awarded += 1

    # Mark finalized.
    await db.pvp_seasons.update_one(
        {"id": season_id, "status": "closing"},
        {"$set": {"status": "finalized",
                  "finalized_at": now_iso, "updated_at": now_iso}},
    )
    # Create next.
    existing_next = await _find_active_season(db)
    rollover_created = False
    if existing_next is None:
        await _create_next_season(db)
        rollover_created = True

    await write_audit(
        db, event_type="PVP_SEASON_FINALIZED",
        related_entity_id=season_id, source="pvp_season",
        metadata={"season_number": int(season["season_number"]),
                  "entries_snapshotted": total_entries,
                  "cosmetics_awarded": total_awarded,
                  "rollover_created": rollover_created},
    )
    return {"season_id": season_id, "status": "finalized",
            "entries_snapshotted": total_entries,
            "cosmetics_awarded": total_awarded,
            "rollover_created": rollover_created, "changed": True}


async def finalize_season_if_due(db) -> Optional[dict]:
    """Convenience wrapper for background/admin triggers.

    Fetches the current active season and finalizes it IFF `ends_at` has
    passed. Never raises.
    """
    try:
        active = await _find_active_season(db)
        if active is None:
            return None
        if _iso(_now()) < active["ends_at"]:
            return None
        return await finalize_season(db, active["id"])
    except Exception as exc:  # noqa: BLE001
        logger.warning("finalize_season_if_due failed: %s", exc)
        return None


__all__ = [
    "SEASON_DURATION_DAYS",
    "TOP_N_PER_CONTINENT",
    "MIN_GUILD_LEVEL_FOR_LEADERBOARD",
    "ensure_indexes",
    "get_or_bootstrap_active_season",
    "_compute_live_top_n",
    "get_finalized_leaderboard",
    "award_cosmetic",
    "finalize_season",
    "finalize_season_if_due",
]
