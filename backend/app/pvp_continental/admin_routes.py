"""ROUND 16.3 Phase 7A — PvP Continental admin routes."""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException

from app.core.database import db
from app.core.security import get_admin_user
from app.pvp_continental.resolver import ELO_DEFAULT, resolve_battle


router = APIRouter(prefix="/api/admin/pvp", tags=["pvp_continental_admin"])


@router.get("/stats")
async def admin_stats(admin: dict = Depends(get_admin_user)):
    active_pending = await db.pvp_battles.count_documents(
        {"status": "pending_response"},
    )
    active_resolving = await db.pvp_battles.count_documents(
        {"status": "resolving"},
    )
    total_resolved = await db.pvp_battles.count_documents(
        {"status": "resolved"},
    )
    # Elo histogram (buckets of 100)
    hist_cursor = db.guild_pvp_stats.aggregate([
        {"$bucket": {
            "groupBy": "$elo",
            "boundaries": [800, 900, 1000, 1100, 1200, 1300, 1400, 1500,
                            1600, 1700, 1800, 1900, 2000, 2100, 2200, 2300,
                            2400],
            "default": "other",
            "output": {"count": {"$sum": 1}},
        }},
    ])
    histogram = [h async for h in hist_cursor]
    top10 = await db.guild_pvp_stats.find(
        {}, {"_id": 0, "guild_id": 1, "elo": 1, "wins": 1, "losses": 1,
              "draws": 1},
    ).sort("elo", -1).limit(10).to_list(10)
    gids = [t["guild_id"] for t in top10]
    gdocs = await db.guilds.find(
        {"id": {"$in": gids}}, {"_id": 0, "id": 1, "name": 1},
    ).to_list(10)
    gmap = {g["id"]: g["name"] for g in gdocs}
    for row in top10:
        row["guild_name"] = gmap.get(row["guild_id"], "?")
    return {
        "active": {"pending_response": active_pending,
                    "resolving": active_resolving},
        "total_resolved": total_resolved,
        "elo_default": ELO_DEFAULT,
        "elo_histogram": histogram,
        "top10_by_elo": top10,
    }


@router.post("/dev/force-resolve/{battle_id}")
async def dev_force_resolve(
    battle_id: str, admin: dict = Depends(get_admin_user),
):
    if (os.environ.get("APP_ENV") or "development").lower() == "production":
        raise HTTPException(
            status_code=403,
            detail={"code": "pvp.dev_disabled_in_prod",
                    "user_message":
                    "Il force-resolve dev è disabilitato in produzione."},
        )
    # Bypass the "not yet" gate by setting resolves_at in the past.
    from datetime import datetime, timezone, timedelta
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    await db.pvp_battles.update_one(
        {"id": battle_id, "status": {"$in": ["pending_response", "resolving"]}},
        {"$set": {"resolves_at": past, "response_deadline": past}},
    )
    result = await resolve_battle(db, battle_id, reason="admin_force")
    return {"result": result}
