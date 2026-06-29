"""ROUND 12.A — Seasonal leaderboard categories.

Lazy-computed, cached 60s like the global registry. Categories are
season-scoped: rows come from `season_participations` aggregates (for
arena/Elo) or from per-season aggregates on existing collections.

Currently implemented (12.A):
  * arena_rating, arena_wins, arena_defense_wins, arena_win_rate (min 10 ranked matches).
  * peak_team_power, roster_avg_level (per-season snapshot of latest aggregates).
  * reputation (snapshot from guilds.reputation, season-scoped via creation cut-off).

Deferred to 12.C: raid_score, dungeon_clears, raid_clears, territory,
contracts, training (require new per-season aggregate tables).
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Awaitable, Callable

from fastapi import HTTPException

logger = logging.getLogger("orbus.leaderboard.seasonal")

SEASONAL_CATEGORIES: dict[str, dict] = {}


def _register(slug: str, label_it: str, description_it: str):
    def deco(fn):
        SEASONAL_CATEGORIES[slug] = {
            "slug": slug,
            "label_it": label_it,
            "description_it": description_it,
            "compute": fn,
        }
        return fn
    return deco


async def _eligible_parts(db, season_id: str) -> list[dict]:
    rows = await db.season_participations.find(
        {"season_id": season_id, "is_test": {"$ne": True}, "is_demo": {"$ne": True}},
        {"_id": 0},
    ).to_list(10_000)
    # Also exclude participants whose guild is test_artifact, demo_opponent, or owned by test user.
    test_owner_ids = set(await db.users.distinct("id", {"is_test_user": True}))
    demo_owner_ids = set(await db.users.distinct("id", {"is_demo_owner": True}))
    test_guild_ids = set(await db.guilds.distinct("id", {"$or": [
        {"is_test_artifact": True},
        {"is_demo_opponent": True},
        # ROUND 14 — exclude pre-launch cleanup archives.
        {"is_archived_pre_launch": True},
        {"owner_user_id": {"$in": list(test_owner_ids | demo_owner_ids)}},
    ]}))
    return [r for r in rows if r["guild_id"] not in test_guild_ids]


@_register("arena_rating", "Arena — Rating", "Classifica per rating Elo nella stagione attuale.")
async def _calc_arena_rating(db, season_id: str) -> list[dict]:
    parts = await _eligible_parts(db, season_id)
    rows = [{"guild_public_id": p["guild_public_id"], "guild_name": p["guild_name"],
             "score": p["rating"], "league": p["league"]}
            for p in parts]
    rows.sort(key=lambda r: -r["score"])
    return rows


@_register("arena_wins", "Arena — Vittorie", "Classifica per numero di vittorie ranked.")
async def _calc_arena_wins(db, season_id: str) -> list[dict]:
    parts = await _eligible_parts(db, season_id)
    rows = [{"guild_public_id": p["guild_public_id"], "guild_name": p["guild_name"],
             "score": p["wins"], "league": p["league"]}
            for p in parts]
    rows.sort(key=lambda r: -r["score"])
    return rows


@_register("arena_defense_wins", "Arena — Difese vinte", "Classifica per difese riuscite.")
async def _calc_arena_def_wins(db, season_id: str) -> list[dict]:
    parts = await _eligible_parts(db, season_id)
    rows = [{"guild_public_id": p["guild_public_id"], "guild_name": p["guild_name"],
             "score": p["defense_wins"], "league": p["league"]}
            for p in parts]
    rows.sort(key=lambda r: -r["score"])
    return rows


@_register("arena_win_rate", "Arena — Win rate", "Classifica per win-rate (min 10 ranked match).")
async def _calc_arena_win_rate(db, season_id: str) -> list[dict]:
    parts = await _eligible_parts(db, season_id)
    rows = []
    for p in parts:
        total = p["wins"] + p["losses"] + p["draws"]
        if total < 10:
            continue
        rate = int(round((p["wins"] / total) * 10000))
        rows.append({"guild_public_id": p["guild_public_id"], "guild_name": p["guild_name"],
                     "score": rate, "league": p["league"]})
    rows.sort(key=lambda r: -r["score"])
    return rows


@_register("peak_team_power", "Picco di Potenza (stagionale)",
           "Massimo team_power per la stagione attuale.")
async def _calc_peak_power_season(db, season_id: str) -> list[dict]:
    # 12.A: snapshot from current guild stat (full per-season tracking deferred to 12.C).
    parts = await _eligible_parts(db, season_id)
    guild_ids = [p["guild_id"] for p in parts]
    guilds = await db.guilds.find(
        {"id": {"$in": guild_ids}}, {"_id": 0, "id": 1, "max_team_power_ever": 1},
    ).to_list(10_000)
    by_id = {g["id"]: int(g.get("max_team_power_ever") or 0) for g in guilds}
    rows = [{"guild_public_id": p["guild_public_id"], "guild_name": p["guild_name"],
             "score": by_id.get(p["guild_id"], 0)} for p in parts]
    rows.sort(key=lambda r: -r["score"])
    return rows


@_register("reputation", "Reputazione (stagionale)",
           "Snapshot della reputazione della gilda.")
async def _calc_reputation_season(db, season_id: str) -> list[dict]:
    parts = await _eligible_parts(db, season_id)
    guild_ids = [p["guild_id"] for p in parts]
    guilds = await db.guilds.find(
        {"id": {"$in": guild_ids}}, {"_id": 0, "id": 1, "reputation": 1},
    ).to_list(10_000)
    by_id = {g["id"]: int(g.get("reputation") or 0) for g in guilds}
    rows = [{"guild_public_id": p["guild_public_id"], "guild_name": p["guild_name"],
             "score": by_id.get(p["guild_id"], 0)} for p in parts]
    rows.sort(key=lambda r: -r["score"])
    return rows


# ─── ROUND 13b — Incremental per-season categories ───────────────────────────
# All six read `season_participations.season_stats.<field>` populated by the
# expedition/raid/contract/training hooks (see `app/seasons/season_stats.py`).

def _stat(part: dict, field: str) -> int:
    return int((part.get("season_stats") or {}).get(field) or 0)


@_register("dungeon_clears", "Dungeon completati (stagione)",
           "Numero di dungeon conquistati durante la stagione corrente.")
async def _calc_dungeon_clears_season(db, season_id: str) -> list[dict]:
    parts = await _eligible_parts(db, season_id)
    rows = [{"guild_public_id": p["guild_public_id"], "guild_name": p["guild_name"],
             "score": _stat(p, "dungeon_clears")} for p in parts]
    rows.sort(key=lambda r: -r["score"])
    return rows


@_register("raid_clears", "Raid completati (stagione)",
           "Numero di raid 20-uomini chiusi con outcome victory/partial nella stagione.")
async def _calc_raid_clears_season(db, season_id: str) -> list[dict]:
    parts = await _eligible_parts(db, season_id)
    rows = [{"guild_public_id": p["guild_public_id"], "guild_name": p["guild_name"],
             "score": _stat(p, "raid_clears")} for p in parts]
    rows.sort(key=lambda r: -r["score"])
    return rows


@_register("raid_score", "Punteggio Raid (stagione)",
           "Somma dei raid_score guadagnati durante la stagione.")
async def _calc_raid_score_season(db, season_id: str) -> list[dict]:
    parts = await _eligible_parts(db, season_id)
    rows = [{"guild_public_id": p["guild_public_id"], "guild_name": p["guild_name"],
             "score": _stat(p, "raid_score")} for p in parts]
    rows.sort(key=lambda r: -r["score"])
    return rows


@_register("territory_score", "Sviluppo Territoriale (stagione)",
           "Crescita dei livelli strutture territoriali rispetto all'inizio della stagione.")
async def _calc_territory_delta_season(db, season_id: str) -> list[dict]:
    """Reads delta = current_territory_score - season_stats.territory_score_at_start.

    `territory_score_at_start` is snapshotted lazily at first PvP/event for
    each guild (see `seasons.services.get_or_create_participation`).
    """
    from app.seasons.season_stats import _compute_current_territory_score
    parts = await _eligible_parts(db, season_id)
    rows = []
    for p in parts:
        at_start = int((p.get("season_stats") or {}).get("territory_score_at_start") or 0)
        current = await _compute_current_territory_score(db, p["guild_id"])
        delta = max(0, current - at_start)
        rows.append({
            "guild_public_id": p["guild_public_id"], "guild_name": p["guild_name"],
            "score": delta,
        })
    rows.sort(key=lambda r: -r["score"])
    return rows


@_register("contracts_completed", "Contratti completati (stagione)",
           "Numero di contratti daily/weekly reclamati durante la stagione.")
async def _calc_contracts_season(db, season_id: str) -> list[dict]:
    parts = await _eligible_parts(db, season_id)
    rows = [{"guild_public_id": p["guild_public_id"], "guild_name": p["guild_name"],
             "score": _stat(p, "contracts_completed")} for p in parts]
    rows.sort(key=lambda r: -r["score"])
    return rows


@_register("training_score", "Allenamenti (stagione)",
           "Somma del power_score guadagnato tramite specializzazioni durante la stagione.")
async def _calc_training_season(db, season_id: str) -> list[dict]:
    parts = await _eligible_parts(db, season_id)
    rows = [{"guild_public_id": p["guild_public_id"], "guild_name": p["guild_name"],
             "score": _stat(p, "training_score")} for p in parts]
    rows.sort(key=lambda r: -r["score"])
    return rows


# ─── Cache ────────────────────────────────────────────────────────────────────
_TTL = 60
_CACHE: dict[str, dict] = {}  # key = "<slug>:<season_id>"
_LOCKS: dict[str, asyncio.Lock] = {}


def _key(category: str, season_id: str) -> str:
    return f"{category}:{season_id}"


def invalidate_seasonal_cache(season_slug_or_id: str | None = None) -> None:
    """Wipe cache for a season; if no arg, wipe everything."""
    if season_slug_or_id is None:
        _CACHE.clear()
        return
    for k in list(_CACHE.keys()):
        if season_slug_or_id in k:
            _CACHE.pop(k, None)


async def get_seasonal_rows(db, category: str, season_id: str) -> tuple[list[dict], bool]:
    if category not in SEASONAL_CATEGORIES:
        raise HTTPException(400, {
            "code": "leaderboard.unknown_seasonal_category",
            "available": list(SEASONAL_CATEGORIES.keys()),
            "user_message": "Categoria stagionale sconosciuta.",
        })
    k = _key(category, season_id)
    now = time.time()
    cached = _CACHE.get(k)
    if cached and (now - cached["ts"]) < _TTL:
        return cached["rows"], True
    lock = _LOCKS.setdefault(k, asyncio.Lock())
    async with lock:
        cached = _CACHE.get(k)
        if cached and (time.time() - cached["ts"]) < _TTL:
            return cached["rows"], True
        rows = await SEASONAL_CATEGORIES[category]["compute"](db, season_id)
        # ROUND 15.1 — score=0 filter (same rationale as multi_category).
        rows = [r for r in rows if int(r.get("score", 0)) > 0]
        _CACHE[k] = {"rows": rows, "ts": time.time()}
        return rows, False


def list_seasonal_categories() -> list[dict]:
    return [{"slug": s, "label_it": c["label_it"], "description_it": c["description_it"]}
            for s, c in SEASONAL_CATEGORIES.items()]


def seasonal_category_meta(slug: str) -> dict:
    c = SEASONAL_CATEGORIES[slug]
    return {"slug": c["slug"], "label_it": c["label_it"], "description_it": c["description_it"]}


__all__ = [
    "SEASONAL_CATEGORIES",
    "get_seasonal_rows", "invalidate_seasonal_cache",
    "list_seasonal_categories", "seasonal_category_meta",
]
