"""ROUND 12.A — PvP Arena REST routes."""
from fastapi import APIRouter, Body, Depends, HTTPException, Query

from app.core.database import db
from app.core.security import get_current_user
from app.guilds.services import user_guild_or_404
from app.pvp.services import (
    build_team_summary,
    challenge,
    delete_defense_team,
    get_defense_team,
    get_match,
    list_my_matches,
    list_opponents,
    upsert_defense_team,
    MIN_LEVEL_PVP,
    TEAM_SIZE,
)
from app.seasons.services import get_current_season

router = APIRouter(prefix="/api/pvp", tags=["pvp"])


@router.get("/defense-team")
async def get_my_defense_team(user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    dt = await get_defense_team(db, guild_id=guild["id"])
    if not dt:
        return {
            "team": None,
            "summary": None,
            "min_level_required": MIN_LEVEL_PVP,
            "team_size_required": TEAM_SIZE,
        }
    summary = await build_team_summary(db, guild_id=guild["id"], adventurer_ids=dt["adventurer_ids"])
    return {
        "team": dt,
        "summary": summary,
        "min_level_required": MIN_LEVEL_PVP,
        "team_size_required": TEAM_SIZE,
    }


@router.put("/defense-team")
async def put_defense_team(payload: dict = Body(...), user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    ids = payload.get("adventurer_ids") or []
    if not isinstance(ids, list):
        raise HTTPException(400, {"code": "pvp.bad_payload", "user_message": "adventurer_ids deve essere una lista."})
    dt = await upsert_defense_team(db, guild_id=guild["id"], adventurer_ids=ids, actor_user_id=user["id"])
    summary = await build_team_summary(db, guild_id=guild["id"], adventurer_ids=dt["adventurer_ids"])
    return {"team": dt, "summary": summary}


@router.delete("/defense-team")
async def delete_my_defense_team(user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    await delete_defense_team(db, guild_id=guild["id"], actor_user_id=user["id"])
    return {"ok": True}


@router.get("/opponents")
async def get_opponents(limit: int = Query(10, ge=1, le=20), user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    season = await get_current_season(db)
    if not season or season["status"] != "active":
        raise HTTPException(423, {
            "code": "pvp.season_inactive",
            "user_message": "Nessuna stagione attiva.",
        })
    opps = await list_opponents(db, my_guild=guild, season=season, limit=limit)
    return {"opponents": opps, "season_slug": season["slug"]}


@router.post("/challenge")
async def post_challenge(payload: dict = Body(...), user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    opp_public = payload.get("opponent_guild_public_id")
    ids = payload.get("attacker_adventurer_ids") or []
    mode = payload.get("mode", "ranked")
    if not opp_public:
        raise HTTPException(400, {"code": "pvp.bad_payload", "user_message": "opponent_guild_public_id richiesto."})
    if mode not in ("ranked", "casual"):
        raise HTTPException(400, {"code": "pvp.bad_mode", "user_message": "Modalità non supportata."})
    match = await challenge(
        db,
        attacker_guild=guild,
        attacker_user_id=user["id"],
        opponent_guild_public_id=opp_public,
        attacker_adventurer_ids=ids,
        mode=mode,
    )
    return {"match": match}


@router.get("/matches")
async def my_matches(limit: int = Query(50, ge=1, le=100), user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    rows = await list_my_matches(db, guild_id=guild["id"], limit=limit)
    return {"matches": rows, "total": len(rows)}


@router.get("/matches/{match_id}")
async def get_match_detail(match_id: str, user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, user["id"])
    m = await get_match(db, guild_id=guild["id"], match_id=match_id)
    if not m:
        raise HTTPException(404, {"code": "pvp.match_not_found", "user_message": "Match non trovato o non visibile."})
    return {"match": m}


__all__ = ["router"]
