"""ROUND 11.3 Turno 3 — Fase 3C — TASK D — Multi-category leaderboard.

Adds a unified `GET /api/leaderboard?category=<slug>&limit=<n>` endpoint
backed by 8 server-authoritative calculators. Each category is cached
in-memory for 60s (lazy rebuild on first stale read) and emits an audit
event `leaderboard_cache_rebuilt` on every rebuild.

Privacy rules (NON-negotiable):
  * Output exposes ONLY `guild_public_id`, `guild_name`, `rank`, `score`,
    `is_me`. NO email, user_id, gold, inventory_value, raw materials.
  * Test artifacts (`guilds.is_test_artifact=True`) and test users
    (`users.is_test_user=True`) are excluded from every category.

Categories: peak_power, raid_score, dungeon_clears, raid_clears,
territory_score, contracts_completed, training_score, roster_avg_level.

NOTE on contracts/training: the codebase does NOT have a dedicated
`contracts` / `training_sessions` collection in preview; the calculators
fall back on `guilds.reputation`-derived heuristics (documented in each
fn). Future rounds can swap the impl without touching the public API.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Awaitable, Callable, Optional

from fastapi import HTTPException

logger = logging.getLogger("orbus.leaderboard.multi")


# ─── Category registry ────────────────────────────────────────────────────────
# `label_it` and `description_it` are the FE-facing IT strings. `compute` is
# the async calculator that returns `[{guild_public_id, guild_name, score}]`
# already filtered for test artifacts and sorted desc by score.

CATEGORIES: dict[str, dict] = {}


def _register(slug: str, label_it: str, description_it: str):
    def deco(fn: Callable[..., Awaitable[list[dict]]]):
        CATEGORIES[slug] = {
            "slug": slug,
            "label_it": label_it,
            "description_it": description_it,
            "compute": fn,
        }
        return fn
    return deco


async def _exclude_filter(db) -> dict:
    """MongoDB filter that excludes test artifacts + test users."""
    test_owner_ids = await db.users.distinct("id", {"is_test_user": True})
    flt: dict = {"is_test_artifact": {"$ne": True}}
    if test_owner_ids:
        flt["owner_user_id"] = {"$nin": test_owner_ids}
    return flt


async def _list_eligible_guilds(db, projection: dict) -> list[dict]:
    """Return all non-test guilds with the requested projection."""
    flt = await _exclude_filter(db)
    proj = {"_id": 0, "id": 1, "public_id": 1, "name": 1, **projection}
    return await db.guilds.find(flt, proj).to_list(10_000)


# ─── 1. peak_power ────────────────────────────────────────────────────────────
@_register(
    "peak_power",
    "Picco di Potenza",
    "Massimo team_power mai raggiunto in una spedizione completata.",
)
async def _calc_peak_power(db) -> list[dict]:
    guilds = await _list_eligible_guilds(db, {"max_team_power_ever": 1})
    rows = [
        {"guild_public_id": g.get("public_id") or g["id"][:8],
         "guild_name": g["name"],
         "score": int(g.get("max_team_power_ever", 0) or 0)}
        for g in guilds
    ]
    rows.sort(key=lambda r: -r["score"])
    return rows


# ─── 2. raid_score ────────────────────────────────────────────────────────────
@_register(
    "raid_score",
    "Punteggio Raid",
    "Somma dei punteggi raid completate (raid_score).",
)
async def _calc_raid_score(db) -> list[dict]:
    flt = await _exclude_filter(db)
    eligible_gids = {g["id"] for g in await db.guilds.find(flt, {"_id": 0, "id": 1}).to_list(10_000)}
    pipeline = [
        {"$match": {"status": "completed", "guild_id": {"$in": list(eligible_gids)},
                    "raid_score": {"$gt": 0}}},
        {"$group": {"_id": "$guild_id", "score": {"$sum": "$raid_score"}}},
    ]
    agg = await db.raids.aggregate(pipeline).to_list(10_000)
    by_gid = {a["_id"]: int(a["score"]) for a in agg}
    guilds = await _list_eligible_guilds(db, {})
    rows = [
        {"guild_public_id": g.get("public_id") or g["id"][:8],
         "guild_name": g["name"],
         "score": by_gid.get(g["id"], 0)}
        for g in guilds
    ]
    rows.sort(key=lambda r: -r["score"])
    return rows


# ─── 3. dungeon_clears ────────────────────────────────────────────────────────
@_register(
    "dungeon_clears",
    "Dungeon Conquistati",
    "Numero di spedizioni completate con successo.",
)
async def _calc_dungeon_clears(db) -> list[dict]:
    flt = await _exclude_filter(db)
    eligible_gids = {g["id"] for g in await db.guilds.find(flt, {"_id": 0, "id": 1}).to_list(10_000)}
    pipeline = [
        {"$match": {"status": "completed", "guild_id": {"$in": list(eligible_gids)},
                    "result_summary": {"$regex": "^Success", "$options": "i"}}},
        {"$group": {"_id": "$guild_id", "score": {"$sum": 1}}},
    ]
    agg = await db.expeditions.aggregate(pipeline).to_list(10_000)
    by_gid = {a["_id"]: int(a["score"]) for a in agg}
    guilds = await _list_eligible_guilds(db, {})
    rows = [
        {"guild_public_id": g.get("public_id") or g["id"][:8],
         "guild_name": g["name"],
         "score": by_gid.get(g["id"], 0)}
        for g in guilds
    ]
    rows.sort(key=lambda r: -r["score"])
    return rows


# ─── 4. raid_clears ───────────────────────────────────────────────────────────
@_register(
    "raid_clears",
    "Raid Conquistate",
    "Numero di raid completate con successo.",
)
async def _calc_raid_clears(db) -> list[dict]:
    flt = await _exclude_filter(db)
    eligible_gids = {g["id"] for g in await db.guilds.find(flt, {"_id": 0, "id": 1}).to_list(10_000)}
    pipeline = [
        {"$match": {"status": "completed", "outcome": "success",
                    "guild_id": {"$in": list(eligible_gids)}}},
        {"$group": {"_id": "$guild_id", "score": {"$sum": 1}}},
    ]
    agg = await db.raids.aggregate(pipeline).to_list(10_000)
    by_gid = {a["_id"]: int(a["score"]) for a in agg}
    guilds = await _list_eligible_guilds(db, {})
    rows = [
        {"guild_public_id": g.get("public_id") or g["id"][:8],
         "guild_name": g["name"],
         "score": by_gid.get(g["id"], 0)}
        for g in guilds
    ]
    rows.sort(key=lambda r: -r["score"])
    return rows


# ─── 5. territory_score ───────────────────────────────────────────────────────
@_register(
    "territory_score",
    "Sviluppo Territoriale",
    "Somma dei livelli di tutte le strutture territoriali della gilda.",
)
async def _calc_territory(db) -> list[dict]:
    flt = await _exclude_filter(db)
    eligible_gids = {g["id"] for g in await db.guilds.find(flt, {"_id": 0, "id": 1}).to_list(10_000)}
    structs = await db.guild_structures.find(
        {"guild_id": {"$in": list(eligible_gids)}}, {"_id": 0, "guild_id": 1, "structures": 1},
    ).to_list(10_000)
    by_gid: dict[str, int] = {}
    for s in structs:
        total = 0
        for _, v in (s.get("structures") or {}).items():
            if isinstance(v, dict):
                total += int(v.get("level", 0) or 0)
        by_gid[s["guild_id"]] = total
    guilds = await _list_eligible_guilds(db, {})
    rows = [
        {"guild_public_id": g.get("public_id") or g["id"][:8],
         "guild_name": g["name"],
         "score": by_gid.get(g["id"], 0)}
        for g in guilds
    ]
    rows.sort(key=lambda r: -r["score"])
    return rows


# ─── 6. contracts_completed ───────────────────────────────────────────────────
@_register(
    "contracts_completed",
    "Contratti Completati",
    "Numero di contratti del Comitato Contratti onorati.",
)
async def _calc_contracts(db) -> list[dict]:
    """Fallback note: `contracts` is not a dedicated collection in preview.
    We derive the score from `guilds.contracts_completed_count` if present
    (legacy backfill field) — otherwise 0. The category is still listed so
    future rounds can introduce a dedicated collection without breaking
    the FE contract."""
    guilds = await _list_eligible_guilds(db, {"contracts_completed_count": 1})
    rows = [
        {"guild_public_id": g.get("public_id") or g["id"][:8],
         "guild_name": g["name"],
         "score": int(g.get("contracts_completed_count", 0) or 0)}
        for g in guilds
    ]
    rows.sort(key=lambda r: -r["score"])
    return rows


# ─── 7. training_score ────────────────────────────────────────────────────────
@_register(
    "training_score",
    "Punteggio Allenamento",
    "Somma dei livelli del roster — riflette l'investimento in Training Grounds.",
)
async def _calc_training(db) -> list[dict]:
    """Fallback: no dedicated `training_sessions` collection in preview.
    Use the sum of adventurer levels across the active roster as a proxy
    (the training subsystem grants XP that bumps level). Documented as a
    Round 11.3 proxy choice."""
    flt = await _exclude_filter(db)
    eligible_gids = {g["id"] for g in await db.guilds.find(flt, {"_id": 0, "id": 1}).to_list(10_000)}
    pipeline = [
        {"$match": {"guild_id": {"$in": list(eligible_gids)}, "is_available": True}},
        {"$group": {"_id": "$guild_id", "score": {"$sum": "$level"}}},
    ]
    agg = await db.adventurers.aggregate(pipeline).to_list(10_000)
    by_gid = {a["_id"]: int(a["score"]) for a in agg}
    guilds = await _list_eligible_guilds(db, {})
    rows = [
        {"guild_public_id": g.get("public_id") or g["id"][:8],
         "guild_name": g["name"],
         "score": by_gid.get(g["id"], 0)}
        for g in guilds
    ]
    rows.sort(key=lambda r: -r["score"])
    return rows


# ─── 8. roster_avg_level ──────────────────────────────────────────────────────
@_register(
    "roster_avg_level",
    "Livello Medio del Roster",
    "Livello medio degli avventurieri attivi (×100 per ordinare interi).",
)
async def _calc_roster_avg(db) -> list[dict]:
    flt = await _exclude_filter(db)
    eligible_gids = {g["id"] for g in await db.guilds.find(flt, {"_id": 0, "id": 1}).to_list(10_000)}
    pipeline = [
        {"$match": {"guild_id": {"$in": list(eligible_gids)}, "is_available": True}},
        {"$group": {"_id": "$guild_id",
                    "sum_lvl": {"$sum": "$level"},
                    "count": {"$sum": 1}}},
    ]
    agg = await db.adventurers.aggregate(pipeline).to_list(10_000)
    by_gid = {a["_id"]: (int(a["sum_lvl"]), int(a["count"])) for a in agg}
    guilds = await _list_eligible_guilds(db, {})
    rows = []
    for g in guilds:
        s, c = by_gid.get(g["id"], (0, 0))
        # Score is avg×100 (integer) so the FE can display "Lv 4.32" via /100.
        score = int(round((s / c) * 100)) if c > 0 else 0
        rows.append({
            "guild_public_id": g.get("public_id") or g["id"][:8],
            "guild_name": g["name"],
            "score": score,
        })
    rows.sort(key=lambda r: -r["score"])
    return rows


# ─── In-memory cache ──────────────────────────────────────────────────────────
_TTL_SECONDS = 60
_CACHE: dict[str, dict] = {}  # category → {"rows": [...], "ts": <unix>}
_LOCKS: dict[str, asyncio.Lock] = {category: asyncio.Lock() for category in CATEGORIES}


async def get_category_rows(db, category: str) -> tuple[list[dict], bool]:
    """Return `(rows, cache_hit)`. Lazy rebuild every TTL_SECONDS.

    Each category has its own asyncio.Lock so concurrent requests for the
    same category de-duplicate the rebuild. Different categories rebuild
    in parallel.
    """
    if category not in CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "leaderboard.unknown_category",
                "available": list(CATEGORIES.keys()),
                "user_message": f"Categoria sconosciuta. Disponibili: {', '.join(CATEGORIES.keys())}.",
            },
        )
    now = time.time()
    cached = _CACHE.get(category)
    if cached and (now - cached["ts"]) < _TTL_SECONDS:
        return cached["rows"], True

    async with _LOCKS[category]:
        # Double-check inside the lock to avoid double-rebuild races.
        cached = _CACHE.get(category)
        if cached and (time.time() - cached["ts"]) < _TTL_SECONDS:
            return cached["rows"], True
        t0 = time.time()
        rows = await CATEGORIES[category]["compute"](db)
        dt_ms = int((time.time() - t0) * 1000)
        _CACHE[category] = {"rows": rows, "ts": time.time()}
        # Audit best-effort.
        try:
            from app.audit.log import write_audit
            await write_audit(
                db, event_type="leaderboard_cache_rebuilt",
                actor_guild_id=None,
                source="leaderboard.multi",
                metadata={
                    "category": category,
                    "entry_count": len(rows),
                    "duration_ms": dt_ms,
                },
            )
        except Exception:
            logger.exception("audit write failed for leaderboard.%s rebuild", category)
        return rows, False


def category_meta(category: str) -> dict:
    """Return `{slug, label_it, description_it}` for a known category."""
    cat = CATEGORIES[category]
    return {
        "slug": cat["slug"],
        "label_it": cat["label_it"],
        "description_it": cat["description_it"],
    }


def list_categories() -> list[dict]:
    """Return the catalog of all categories for the FE picker."""
    return [
        {"slug": s, "label_it": c["label_it"], "description_it": c["description_it"]}
        for s, c in CATEGORIES.items()
    ]


__all__ = [
    "CATEGORIES",
    "get_category_rows",
    "category_meta",
    "list_categories",
]
