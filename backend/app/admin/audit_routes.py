"""ROUND 16.A Phase 3 — Admin Read-Only Audit Dashboard.

Three GET endpoints mounted under `/api/admin/audit/*`, all gated by
`get_admin_user` (returns 401 for missing creds, 403 for non-admin).

This module is intentionally read-only: the dashboard surfaces existing
data already persisted by Phase 1 (`trigger_emissions`) and Phase 2
(`audit_log`) — no new writes, no migrations.

Surfaces:
  * GET /api/admin/audit/trigger-emissions  → Phase 1 emissions feed
  * GET /api/admin/audit/events             → Phase 2 audit_log feed
  * GET /api/admin/audit/summary            → aggregated KPI for the dash
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.database import db
from app.core.security import get_admin_user


logger = logging.getLogger("orbus.admin.audit")


router = APIRouter(prefix="/api/admin/audit", tags=["admin", "audit"])


# Event-type whitelist for the audit_log feed — keeps internal event_types
# (admin ops, gold grants, etc.) out of the dashboard surface.
AUDIT_EVENT_WHITELIST = frozenset({
    "achievement_unlocked",
    "guild_xp_gained",
    "onboarding_graduated",
})

# Whitelist for the trigger_emissions feed — mirrors the 11 R16.A Phase 1
# events. Unknown event_name values still pass (no leak risk since the
# collection only contains data we wrote) but typo-protection is nice.
TRIGGER_EVENT_WHITELIST = frozenset({
    "item_crafted", "market_purchase", "auction_sale", "auction_purchase",
    "consortium_joined", "season_league_reached",
    "leaderboard_rank_reached", "item_disenchanted", "material_purchased",
    "pvp_match_completed", "territory_upgraded",
})

# Hard caps to keep admin queries cheap.
MAX_LIMIT = 200
DEFAULT_LIMIT = 50
MAX_WINDOW_HOURS = 720  # 30 days


def _strip_mongo_id(doc: dict) -> dict:
    doc.pop("_id", None)
    return doc


# ─── 1. Trigger emissions feed ────────────────────────────────────────────
@router.get("/trigger-emissions")
async def list_trigger_emissions(
    event_name: Optional[str] = Query(default=None, max_length=80),
    guild_id: Optional[str] = Query(default=None, max_length=80),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0, le=10_000),
    _user: dict = Depends(get_admin_user),
):
    q: dict = {}
    if event_name:
        q["event_name"] = event_name
    if guild_id:
        q["guild_id"] = guild_id
    total = await db.trigger_emissions.count_documents(q)
    cur = (
        db.trigger_emissions.find(q)
        .sort([("created_at", -1)])
        .skip(offset)
        .limit(limit)
    )
    items = [_strip_mongo_id(d) async for d in cur]
    return {
        "items": items,
        "total": int(total),
        "has_more": (offset + len(items)) < int(total),
        "limit": limit,
        "offset": offset,
    }


# ─── 2. Audit-log timeline ────────────────────────────────────────────────
@router.get("/events")
async def list_audit_events(
    event_type: Optional[str] = Query(default=None, max_length=80),
    guild_id: Optional[str] = Query(default=None, max_length=80),
    from_: Optional[str] = Query(default=None, alias="from"),
    to: Optional[str] = Query(default=None),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0, le=10_000),
    _user: dict = Depends(get_admin_user),
):
    if event_type is not None and event_type not in AUDIT_EVENT_WHITELIST:
        raise HTTPException(
            status_code=400,
            detail={
                "user_message": f"event_type '{event_type}' not allowed",
                "allowed": sorted(AUDIT_EVENT_WHITELIST),
            },
        )

    q: dict = {}
    if event_type:
        q["event_type"] = event_type
    else:
        # Default scope: ONLY the 3 R16.A event types — keeps unrelated
        # legacy audit events (gold grants, admin ops, ...) out of view.
        q["event_type"] = {"$in": list(AUDIT_EVENT_WHITELIST)}
    if guild_id:
        q["actor_guild_id"] = guild_id

    # ISO8601 date filters → string comparison works because we always
    # persist timestamps in canonical ISO8601 UTC format.
    if from_ or to:
        q["created_at"] = {}
        if from_:
            q["created_at"]["$gte"] = from_
        if to:
            q["created_at"]["$lte"] = to

    total = await db.audit_log.count_documents(q)
    cur = (
        db.audit_log.find(q)
        .sort([("created_at", -1)])
        .skip(offset)
        .limit(limit)
    )
    items = [_strip_mongo_id(d) async for d in cur]
    return {
        "items": items,
        "total": int(total),
        "has_more": (offset + len(items)) < int(total),
        "limit": limit,
        "offset": offset,
    }


# ─── 3. Aggregated KPI summary ────────────────────────────────────────────
@router.get("/summary")
async def get_audit_summary(
    window_hours: int = Query(default=24, ge=1),
    _user: dict = Depends(get_admin_user),
):
    # Clamp window to MAX_WINDOW_HOURS regardless of upper bound — query
    # body keeps the looser upper limit but we never actually look back
    # further than 30 days.
    clamped_hours = min(window_hours, MAX_WINDOW_HOURS)
    cutoff_iso = (
        datetime.now(timezone.utc) - timedelta(hours=clamped_hours)
    ).isoformat()

    # Achievement unlocks
    n_ach = await db.audit_log.count_documents({
        "event_type": "achievement_unlocked",
        "created_at": {"$gte": cutoff_iso},
    })

    # Guild XP gained: aggregate amount + count
    xp_pipe = [
        {"$match": {
            "event_type": "guild_xp_gained",
            "created_at": {"$gte": cutoff_iso},
        }},
        {"$group": {
            "_id": None,
            "total_amount": {"$sum": "$metadata.xp_amount"},
            "event_count": {"$sum": 1},
        }},
    ]
    xp_agg = await db.audit_log.aggregate(xp_pipe).to_list(1)
    xp_total = int(xp_agg[0]["total_amount"]) if xp_agg else 0
    xp_count = int(xp_agg[0]["event_count"]) if xp_agg else 0

    # Onboarding graduations
    n_grad = await db.audit_log.count_documents({
        "event_type": "onboarding_graduated",
        "created_at": {"$gte": cutoff_iso},
    })

    # Top trigger events
    top_pipe = [
        {"$match": {"created_at": {"$gte": cutoff_iso}}},
        {"$group": {"_id": "$event_name", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ]
    top_rows = await db.trigger_emissions.aggregate(top_pipe).to_list(10)
    top_trigger = [
        {"event_name": r["_id"], "count": int(r["count"])}
        for r in top_rows if r["_id"]
    ]

    return {
        "window_hours": clamped_hours,
        "window_clamped": (clamped_hours != window_hours),
        "achievement_unlocked_count": int(n_ach),
        "guild_xp_gained_total_amount": xp_total,
        "guild_xp_gained_event_count": xp_count,
        "guilds_graduated_count": int(n_grad),
        "top_trigger_events": top_trigger,
    }


__all__ = ["router"]
