"""ROUND 16.3 Phase 7B — Public PvP season routes."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.core.database import db
from app.core.security import get_current_user
from app.guilds.services import user_guild_or_404
from app.pvp_season.cosmetics import (
    COSMETIC_CATALOG,
    CONTINENT_SLUGS,
    iter_catalog,
)
from app.pvp_season.services import (
    TOP_N_PER_CONTINENT,
    _compute_live_top_n,
    get_finalized_leaderboard,
    get_or_bootstrap_active_season,
)


router = APIRouter(prefix="/api/pvp-season", tags=["pvp_season"])


def _time_remaining(ends_at_iso: str) -> int:
    end = datetime.fromisoformat(ends_at_iso)
    now = datetime.now(timezone.utc)
    return max(0, int((end - now).total_seconds()))


def _me_guild_id(db_ref, user: dict) -> str | None:
    """Best-effort helper — returns the current user's guild id or None."""
    # Endpoints below tolerate absence of a guild (public reads).
    return None


async def _my_guild_id(user: dict) -> str | None:
    g = await db.guilds.find_one(
        {"owner_user_id": user["id"]}, {"_id": 0, "id": 1},
    )
    return g["id"] if g else None


# ── Season info ─────────────────────────────────────────────────────


@router.get("/current")
async def get_current_season(user: dict = Depends(get_current_user)):
    season = await get_or_bootstrap_active_season(db)
    return {
        "id": season["id"],
        "season_number": int(season["season_number"]),
        "started_at": season["started_at"],
        "ends_at": season["ends_at"],
        "status": season["status"],
        "time_remaining_seconds": _time_remaining(season["ends_at"]),
    }


# ── Leaderboards ────────────────────────────────────────────────────


@router.get("/leaderboard/all-continents")
async def get_all_continent_leaderboards(
    user: dict = Depends(get_current_user),
):
    season = await get_or_bootstrap_active_season(db)
    my_guild_id = await _my_guild_id(user)
    finalized = (season["status"] == "finalized")
    by_continent: dict[str, list[dict]] = {}
    for slug in CONTINENT_SLUGS:
        if finalized:
            rows = await get_finalized_leaderboard(db, season["id"], slug)
            by_continent[slug] = [
                {
                    "rank": r["rank"], "guild_id": r["guild_id"],
                    "guild_name": r.get("guild_name_snapshot") or "?",
                    "elo": r["elo_snapshot"], "wins": r["wins_snapshot"],
                    "losses": r["losses_snapshot"],
                    "draws": r["draws_snapshot"],
                    "is_my_guild": (my_guild_id == r["guild_id"]),
                    "cosmetics_awarded": r.get("cosmetics_awarded") or [],
                }
                for r in rows
            ]
        else:
            rows = await _compute_live_top_n(db, slug, TOP_N_PER_CONTINENT)
            by_continent[slug] = [
                {
                    "rank": r["rank"], "guild_id": r["guild_id"],
                    "guild_name": r["guild_name"],
                    "elo": r["elo"], "wins": r["wins"],
                    "losses": r["losses"], "draws": r["draws"],
                    "is_my_guild": (my_guild_id == r["guild_id"]),
                    "cosmetics_awarded": [],
                }
                for r in rows
            ]
    return {
        "season_id": season["id"],
        "season_number": int(season["season_number"]),
        "finalized": finalized,
        "by_continent": by_continent,
    }


@router.get("/leaderboard/{continent_slug}")
async def get_continent_leaderboard(
    continent_slug: str,
    user: dict = Depends(get_current_user),
):
    if continent_slug not in CONTINENT_SLUGS:
        raise HTTPException(
            status_code=404,
            detail={"code": "pvp_season.continent_not_found",
                    "user_message": "Continente sconosciuto."},
        )
    season = await get_or_bootstrap_active_season(db)
    my_guild_id = await _my_guild_id(user)
    finalized = (season["status"] == "finalized")
    if finalized:
        rows = await get_finalized_leaderboard(db, season["id"], continent_slug)
        entries = [
            {
                "rank": r["rank"],
                "guild_id": r["guild_id"],
                "guild_name": r.get("guild_name_snapshot") or "?",
                "elo": r["elo_snapshot"],
                "wins": r["wins_snapshot"],
                "losses": r["losses_snapshot"],
                "draws": r["draws_snapshot"],
                "is_my_guild": (my_guild_id == r["guild_id"]),
                "cosmetics_awarded": r.get("cosmetics_awarded") or [],
            }
            for r in rows
        ]
    else:
        rows = await _compute_live_top_n(db, continent_slug, TOP_N_PER_CONTINENT)
        entries = [
            {
                "rank": r["rank"],
                "guild_id": r["guild_id"],
                "guild_name": r["guild_name"],
                "elo": r["elo"],
                "wins": r["wins"],
                "losses": r["losses"],
                "draws": r["draws"],
                "is_my_guild": (my_guild_id == r["guild_id"]),
                "cosmetics_awarded": [],
            }
            for r in rows
        ]
    return {
        "season_id": season["id"],
        "season_number": int(season["season_number"]),
        "continent_slug": continent_slug,
        "finalized": finalized,
        "entries": entries,
    }


# ── History ─────────────────────────────────────────────────────────


@router.get("/history/{season_number}")
async def get_season_history(
    season_number: int,
    user: dict = Depends(get_current_user),
):
    season = await db.pvp_seasons.find_one(
        {"season_number": season_number}, {"_id": 0},
    )
    if not season:
        raise HTTPException(
            status_code=404,
            detail={"code": "pvp_season.season_not_found",
                    "user_message": "Stagione non trovata."},
        )
    my_guild_id = await _my_guild_id(user)
    by_continent: dict[str, list[dict]] = {}
    for slug in CONTINENT_SLUGS:
        rows = await get_finalized_leaderboard(db, season["id"], slug)
        by_continent[slug] = [
            {
                "rank": r["rank"], "guild_id": r["guild_id"],
                "guild_name": r.get("guild_name_snapshot") or "?",
                "elo": r["elo_snapshot"],
                "wins": r["wins_snapshot"],
                "losses": r["losses_snapshot"],
                "draws": r["draws_snapshot"],
                "is_my_guild": (my_guild_id == r["guild_id"]),
                "cosmetics_awarded": r.get("cosmetics_awarded") or [],
            }
            for r in rows
        ]
    return {
        "season_id": season["id"],
        "season_number": int(season["season_number"]),
        "started_at": season["started_at"],
        "ends_at": season["ends_at"],
        "status": season["status"],
        "finalized_at": season.get("finalized_at"),
        "by_continent": by_continent,
    }


# ── Cosmetics ───────────────────────────────────────────────────────


@router.get("/cosmetics/mine")
async def get_my_cosmetics(user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    rows = await db.pvp_cosmetics_unlocked.find(
        {"guild_id": guild["id"]}, {"_id": 0},
    ).sort("unlocked_at", -1).to_list(1000)
    items = []
    by_type: dict[str, int] = {"title": 0, "badge": 0, "frame": 0}
    for r in rows:
        entry = COSMETIC_CATALOG.get(r["cosmetic_slug"], {})
        items.append({
            "id": r["id"],
            "cosmetic_slug": r["cosmetic_slug"],
            "type": r.get("cosmetic_type") or entry.get("type") or "?",
            "name_it": entry.get("name_it") or r["cosmetic_slug"],
            "continent_slug": r["continent_slug"],
            "season_number": int(r["season_number"]),
            "rank_awarded": int(r["rank_awarded"]),
            "unlocked_at": r["unlocked_at"],
        })
        t = r.get("cosmetic_type") or entry.get("type")
        if t in by_type:
            by_type[t] += 1
    return {
        "guild_id": guild["id"],
        "total": len(items),
        "by_type": by_type,
        "items": items,
    }


@router.get("/cosmetics/catalog")
async def get_cosmetic_catalog(user: dict = Depends(get_current_user)):
    entries = []
    for slug, entry in iter_catalog():
        # Derive continent from slug suffix (last underscore-separated token).
        continent_slug = slug.rsplit("_", 1)[-1]
        entries.append({
            "cosmetic_slug": slug,
            "type": entry["type"],
            "name_it": entry["name_it"],
            "description_it": entry["description_it"],
            "rank_required": entry["rank_required"],
            "continent_slug": continent_slug,
        })
    return {"total": len(entries), "entries": entries}
