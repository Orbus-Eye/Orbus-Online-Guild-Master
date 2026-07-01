"""ROUND 12.A — Season CRUD + lifecycle helpers.

All mutation paths emit an audit event. Status transitions:
    draft → scheduled → active → ended → archived
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import HTTPException

from app.audit.log import write_audit

logger = logging.getLogger("orbus.seasons")

VALID_STATUSES = {"draft", "scheduled", "active", "ended", "archived"}
LORE_THEMES = {
    "verglasio", "renovare", "luminara", "crepuscolo", "umbralia", "equilibrio",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _scrub(doc: dict) -> dict:
    """Strip Mongo internals before exposing season to API consumers."""
    if not doc:
        return doc
    out = {k: v for k, v in doc.items() if k != "_id"}
    return out


async def ensure_season_indexes(db) -> None:
    """Idempotent index setup. Called from startup."""
    try:
        await db.seasons.create_index("season_id", unique=True)
        await db.seasons.create_index("slug", unique=True)
        await db.seasons.create_index("public_id", unique=True)
        await db.seasons.create_index("status")
        # Partial unique index enforcing single-active invariant.
        await db.seasons.create_index(
            "status",
            unique=True,
            name="only_one_active_season",
            partialFilterExpression={"status": "active"},
        )
        # season_participations indexes
        await db.season_participations.create_index(
            [("season_id", 1), ("guild_id", 1)], unique=True,
        )
        await db.season_participations.create_index([("season_id", 1), ("rating", -1)])
        await db.season_participations.create_index([("season_id", 1), ("league", 1)])
    except Exception as exc:  # noqa: BLE001
        logger.warning("ensure_season_indexes failed: %s", exc)


async def get_current_season(db) -> Optional[dict]:
    s = await db.seasons.find_one({"status": "active"})
    return _scrub(s) if s else None


async def list_seasons(db, *, include_drafts: bool = False) -> list[dict]:
    flt = {} if include_drafts else {"status": {"$ne": "draft"}}
    rows = await db.seasons.find(flt).sort("starts_at", -1).to_list(200)
    return [_scrub(r) for r in rows]


async def get_season_by_slug(db, slug: str) -> Optional[dict]:
    s = await db.seasons.find_one({"slug": slug})
    return _scrub(s) if s else None


async def create_season(
    db,
    *,
    slug: str,
    name_it: str,
    name_en: str,
    lore_theme: str,
    starts_at: str,
    ends_at: str,
    actor_user_id: str,
    reason: str,
    status: str = "draft",
) -> dict:
    if status not in VALID_STATUSES:
        raise HTTPException(400, {"code": "season.invalid_status", "user_message": "Stato non valido."})
    if lore_theme not in LORE_THEMES:
        raise HTTPException(400, {
            "code": "season.invalid_lore_theme",
            "user_message": f"Tema lore non valido. Disponibili: {', '.join(sorted(LORE_THEMES))}.",
        })
    existing = await db.seasons.find_one({"slug": slug})
    if existing:
        raise HTTPException(409, {"code": "season.slug_taken", "user_message": "Slug già usato."})
    season_id = str(uuid.uuid4())
    doc = {
        "season_id": season_id,
        "public_id": slug,
        "slug": slug,
        "name_it": name_it,
        "name_en": name_en,
        "lore_theme": lore_theme,
        "status": status,
        "starts_at": starts_at,
        "ends_at": ends_at,
        "scoring_version": 1,
        "rules_version": 1,
        "reward_version": 1,
        "is_ranked": True,
        "is_test": False,
        "created_at": _now(),
        "updated_at": _now(),
        "ended_at": None,
        "archived_at": None,
    }
    await db.seasons.insert_one(doc)
    await write_audit(
        db, event_type="season_created", actor_user_id=actor_user_id,
        source="seasons.create",
        metadata={"season_id": season_id, "slug": slug, "reason": reason, "status": status},
    )
    return _scrub(doc)


async def activate_season(db, *, season_id: str, actor_user_id: str, reason: str) -> dict:
    """Atomically transition the given season to `active`, demoting any
    currently-active season to `ended` if present. The partial unique
    index `only_one_active_season` guarantees safety even under races.
    """
    target = await db.seasons.find_one({"season_id": season_id})
    if not target:
        raise HTTPException(404, {"code": "season.not_found", "user_message": "Stagione non trovata."})
    if target["status"] == "active":
        return _scrub(target)
    if target["status"] in ("ended", "archived"):
        raise HTTPException(400, {
            "code": "season.invalid_transition",
            "user_message": "Impossibile attivare una stagione conclusa/archiviata.",
        })
    # Demote prior active
    prev = await db.seasons.find_one({"status": "active"})
    if prev:
        await db.seasons.update_one(
            {"season_id": prev["season_id"]},
            {"$set": {"status": "ended", "ended_at": _now(), "updated_at": _now()}},
        )
        await write_audit(
            db, event_type="season_ended", actor_user_id=actor_user_id,
            source="seasons.activate.auto_demote",
            metadata={"season_id": prev["season_id"], "slug": prev["slug"], "reason": "superseded by " + season_id},
        )
    await db.seasons.update_one(
        {"season_id": season_id},
        {"$set": {"status": "active", "updated_at": _now()}},
    )
    await write_audit(
        db, event_type="season_activated", actor_user_id=actor_user_id,
        source="seasons.activate",
        metadata={"season_id": season_id, "slug": target["slug"], "reason": reason},
    )
    return _scrub(await db.seasons.find_one({"season_id": season_id}))


async def end_season(db, *, season_id: str, actor_user_id: str, reason: str) -> dict:
    target = await db.seasons.find_one({"season_id": season_id})
    if not target:
        raise HTTPException(404, {"code": "season.not_found", "user_message": "Stagione non trovata."})
    if target["status"] != "active":
        raise HTTPException(400, {
            "code": "season.invalid_transition",
            "user_message": "Solo le stagioni attive possono essere concluse.",
        })
    await db.seasons.update_one(
        {"season_id": season_id},
        {"$set": {"status": "ended", "ended_at": _now(), "updated_at": _now()}},
    )
    await write_audit(
        db, event_type="season_ended", actor_user_id=actor_user_id,
        source="seasons.end",
        metadata={"season_id": season_id, "slug": target["slug"], "reason": reason},
    )
    return _scrub(await db.seasons.find_one({"season_id": season_id}))


async def archive_season(db, *, season_id: str, actor_user_id: str, reason: str) -> dict:
    target = await db.seasons.find_one({"season_id": season_id})
    if not target:
        raise HTTPException(404, {"code": "season.not_found", "user_message": "Stagione non trovata."})
    if target["status"] not in ("ended",):
        raise HTTPException(400, {
            "code": "season.invalid_transition",
            "user_message": "Solo le stagioni concluse possono essere archiviate.",
        })
    await db.seasons.update_one(
        {"season_id": season_id},
        {"$set": {"status": "archived", "archived_at": _now(), "updated_at": _now()}},
    )
    await write_audit(
        db, event_type="season_archived", actor_user_id=actor_user_id,
        source="seasons.archive",
        metadata={"season_id": season_id, "slug": target["slug"], "reason": reason},
    )
    return _scrub(await db.seasons.find_one({"season_id": season_id}))


# ─── Season participations (per guild) ────────────────────────────────────────

def assign_league(rating: int, placement_count: int) -> str:
    """Pure helper. Buckets a rating into one of the 7 league slugs."""
    if placement_count < 5:
        return "unranked"
    if rating >= 1800:
        return "master"
    if rating >= 1600:
        return "diamond"
    if rating >= 1400:
        return "platinum"
    if rating >= 1200:
        return "gold"
    if rating >= 1000:
        return "silver"
    return "bronze"


async def get_or_create_participation(db, *, season_id: str, guild: dict) -> dict:
    p = await db.season_participations.find_one(
        {"season_id": season_id, "guild_id": guild["id"]}, {"_id": 0}
    )
    if p:
        return p
    # ROUND 13b — snapshot territory_score_at_start lazily for the new
    # `territory_score` seasonal category (delta vs season start).
    try:
        from app.seasons.season_stats import _compute_current_territory_score
        territory_at_start = await _compute_current_territory_score(db, guild["id"])
    except Exception:
        territory_at_start = 0
    doc = {
        "season_id": season_id,
        "guild_id": guild["id"],
        "guild_public_id": guild.get("public_id") or guild["id"][:8],
        "guild_name": guild["name"],
        "league": "unranked",
        "rating": 1000,
        "placement_matches_played": 0,
        "wins": 0, "losses": 0, "draws": 0,
        "attacks_played": 0,
        "defense_wins": 0, "defense_losses": 0,
        "best_rating": 1000,
        "highest_league": "unranked",
        "last_match_at": None,
        "is_test": bool(guild.get("is_test_artifact", False)),
        # ROUND 13b — per-season incremental counters.
        "season_stats": {
            "dungeon_clears": 0,
            "raid_clears": 0,
            "raid_score": 0,
            "contracts_completed": 0,
            "training_score": 0,
            "territory_score_at_start": int(territory_at_start),
            "last_updated_at": _now(),
        },
        "created_at": _now(),
        "updated_at": _now(),
    }
    await db.season_participations.insert_one(doc)
    return {k: v for k, v in doc.items() if k != "_id"}


__all__ = [
    "ensure_season_indexes",
    "get_current_season", "list_seasons", "get_season_by_slug",
    "create_season", "activate_season", "end_season", "archive_season",
    "assign_league", "get_or_create_participation",
    "VALID_STATUSES", "LORE_THEMES",
]
