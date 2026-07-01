"""ROUND 16.3 Phase 6 — Trade Pacts V0 (social alliances).

V0 = purely social + informative. Zero numerical modifiers on economy,
market taxes, drop rates. Setup for future Phase 6.5+ (reduced taxes
between partners, preferred orders).

Rules:
- Max 3 accepted pacts per guild
- Cross-continent block: both guilds must share `continent_slug` via
  `guild_world_presence.status='active'`
- Unilateral dissolve triggers 7-day cooldown between the two guilds
- No hard delete: dissolved rows kept for audit trail
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.database import db
from app.core.security import get_current_user, get_admin_user
from app.guilds.services import user_guild_or_404

logger = logging.getLogger("orbus.trade_pacts")

router = APIRouter(prefix="/api/trade-pacts", tags=["trade-pacts"])
admin_router = APIRouter(prefix="/api/admin/trade-pacts",
                          tags=["admin", "trade-pacts"])

MAX_ACCEPTED_PACTS = 3
UNILATERAL_COOLDOWN_DAYS = 7


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


async def ensure_indexes():
    try:
        await db.guild_trade_pacts.create_index([("guild_a_id", 1),
                                                    ("guild_b_id", 1),
                                                    ("status", 1)])
        await db.guild_trade_pacts.create_index("status")
    except Exception as exc:
        logger.debug("trade_pacts idx: %s", exc)


async def _emit_audit(event_type: str, actor_id: Optional[str],
                       guild_id: Optional[str], target_id: Optional[str],
                       metadata: dict) -> None:
    try:
        await db.audit_log.insert_one({
            "id": str(uuid.uuid4()),
            "event_type": event_type,
            "actor_id": actor_id,
            "actor_guild_id": guild_id,
            "target_id": target_id,
            "metadata": metadata,
            "created_at": _iso(_now()),
        })
    except Exception as exc:
        logger.warning("audit %s: %s", event_type, exc)


async def _guild_continent(guild_id: str) -> Optional[str]:
    p = await db.guild_world_presence.find_one(
        {"guild_id": guild_id, "status": "active"},
        {"_id": 0, "continent_slug": 1})
    return p.get("continent_slug") if p else None


async def _has_active_or_pending_between(a: str, b: str) -> Optional[dict]:
    return await db.guild_trade_pacts.find_one({
        "$or": [
            {"guild_a_id": a, "guild_b_id": b},
            {"guild_a_id": b, "guild_b_id": a},
        ],
        "status": {"$in": ["pending_request", "accepted"]},
    }, {"_id": 0})


async def _cooldown_active_between(a: str, b: str) -> Optional[dict]:
    """Return the most recent unilateral-dissolved pact between a and b
    if the 7-day cooldown has not expired yet."""
    now_iso = _iso(_now())
    return await db.guild_trade_pacts.find_one({
        "$or": [
            {"guild_a_id": a, "guild_b_id": b},
            {"guild_a_id": b, "guild_b_id": a},
        ],
        "status": "dissolved",
        "dissolution_reason": "unilateral",
        "cooldown_ends_at": {"$gt": now_iso},
    }, {"_id": 0}, sort=[("dissolved_at", -1)])


def _pact_public(pact: dict) -> dict:
    """Strip Mongo internals, return safe JSON."""
    return {k: pact.get(k) for k in (
        "id", "guild_a_id", "guild_b_id", "status", "requested_at",
        "responded_at", "activated_at", "dissolved_at", "dissolved_by",
        "dissolution_reason", "cooldown_ends_at", "continent_slug",
    )}


# ── Public routes ────────────────────────────────────────────────────
@router.post("/request/{target_guild_id}")
async def request_pact(target_guild_id: str,
                        user: dict = Depends(get_current_user)):
    mine = await user_guild_or_404(db, user["id"])
    if mine["id"] == target_guild_id:
        raise HTTPException(400, "cannot_request_self")
    target = await db.guilds.find_one({"id": target_guild_id},
                                        {"_id": 0, "id": 1, "name": 1})
    if not target:
        raise HTTPException(404, "target_guild_not_found")
    my_cont = await _guild_continent(mine["id"])
    tg_cont = await _guild_continent(target_guild_id)
    if not my_cont:
        raise HTTPException(400, "no_active_continent_for_requester")
    if not tg_cont:
        raise HTTPException(400, "no_active_continent_for_target")
    if my_cont != tg_cont:
        raise HTTPException(400,
                            f"cross_continent_block:mine={my_cont}:target={tg_cont}")
    dup = await _has_active_or_pending_between(mine["id"], target_guild_id)
    if dup:
        raise HTTPException(409, f"pact_already_exists:{dup['status']}")
    cd = await _cooldown_active_between(mine["id"], target_guild_id)
    if cd:
        raise HTTPException(409,
                            f"cooldown_active:ends_at={cd['cooldown_ends_at']}")
    now = _now()
    pact = {
        "id": str(uuid.uuid4()),
        "guild_a_id": mine["id"],
        "guild_b_id": target_guild_id,
        "status": "pending_request",
        "requested_at": _iso(now),
        "responded_at": None,
        "activated_at": None,
        "dissolved_at": None,
        "dissolved_by": None,
        "dissolution_reason": None,
        "cooldown_ends_at": None,
        "continent_slug": my_cont,
        "audit_log_ids": [],
        "created_at": _iso(now),
        "updated_at": _iso(now),
    }
    await db.guild_trade_pacts.insert_one(pact)
    await _emit_audit("TRADE_PACT_REQUESTED", user["id"], mine["id"],
                       pact["id"],
                       {"target_guild_id": target_guild_id,
                        "continent_slug": my_cont})
    return {"status": "ok", "pact": _pact_public(pact)}


@router.get("/received")
async def received_requests(user: dict = Depends(get_current_user)):
    mine = await user_guild_or_404(db, user["id"])
    cur = db.guild_trade_pacts.find(
        {"guild_b_id": mine["id"], "status": "pending_request"},
        {"_id": 0}).sort("requested_at", -1)
    pacts = [_pact_public(p) async for p in cur]
    return {"pacts": pacts, "count": len(pacts)}


@router.post("/{pact_id}/accept")
async def accept_pact(pact_id: str,
                       user: dict = Depends(get_current_user)):
    mine = await user_guild_or_404(db, user["id"])
    pact = await db.guild_trade_pacts.find_one({"id": pact_id}, {"_id": 0})
    if not pact:
        raise HTTPException(404, "pact_not_found")
    if pact["guild_b_id"] != mine["id"]:
        raise HTTPException(403, "not_pact_target")
    if pact["status"] != "pending_request":
        raise HTTPException(409, f"invalid_status:{pact['status']}")
    active_count = await db.guild_trade_pacts.count_documents(
        {"$or": [{"guild_a_id": mine["id"]},
                   {"guild_b_id": mine["id"]}],
         "status": "accepted"})
    if active_count >= MAX_ACCEPTED_PACTS:
        raise HTTPException(409, "max_accepted_pacts_reached")
    now_iso = _iso(_now())
    r = await db.guild_trade_pacts.find_one_and_update(
        {"id": pact_id, "status": "pending_request"},
        {"$set": {"status": "accepted",
                    "responded_at": now_iso,
                    "activated_at": now_iso,
                    "updated_at": now_iso}},
        return_document=True)
    if not r:
        raise HTTPException(409, "cas_race_condition")
    await _emit_audit("TRADE_PACT_ACCEPTED", user["id"], mine["id"],
                       pact_id,
                       {"partner_guild_id": pact["guild_a_id"]})
    return {"status": "ok", "pact": _pact_public(r)}


@router.post("/{pact_id}/reject")
async def reject_pact(pact_id: str,
                       user: dict = Depends(get_current_user)):
    mine = await user_guild_or_404(db, user["id"])
    pact = await db.guild_trade_pacts.find_one({"id": pact_id}, {"_id": 0})
    if not pact:
        raise HTTPException(404, "pact_not_found")
    if pact["guild_b_id"] != mine["id"]:
        raise HTTPException(403, "not_pact_target")
    if pact["status"] != "pending_request":
        raise HTTPException(409, f"invalid_status:{pact['status']}")
    now_iso = _iso(_now())
    r = await db.guild_trade_pacts.find_one_and_update(
        {"id": pact_id, "status": "pending_request"},
        {"$set": {"status": "rejected",
                    "responded_at": now_iso,
                    "updated_at": now_iso}},
        return_document=True)
    await _emit_audit("TRADE_PACT_REJECTED", user["id"], mine["id"],
                       pact_id, {"requester_guild_id": pact["guild_a_id"]})
    return {"status": "ok", "pact": _pact_public(r)}


@router.post("/{pact_id}/dissolve")
async def dissolve_pact(pact_id: str,
                          reason: str = Query("unilateral"),
                          user: dict = Depends(get_current_user)):
    if reason not in ("unilateral", "mutual"):
        raise HTTPException(400, "invalid_reason")
    mine = await user_guild_or_404(db, user["id"])
    pact = await db.guild_trade_pacts.find_one({"id": pact_id}, {"_id": 0})
    if not pact:
        raise HTTPException(404, "pact_not_found")
    if mine["id"] not in (pact["guild_a_id"], pact["guild_b_id"]):
        raise HTTPException(403, "not_pact_member")
    if pact["status"] not in ("accepted", "pending_request"):
        raise HTTPException(409, f"invalid_status:{pact['status']}")
    now = _now()
    cooldown_iso = None
    if reason == "unilateral":
        cooldown_iso = _iso(now + timedelta(days=UNILATERAL_COOLDOWN_DAYS))
    r = await db.guild_trade_pacts.find_one_and_update(
        {"id": pact_id,
         "status": {"$in": ["accepted", "pending_request"]}},
        {"$set": {"status": "dissolved",
                    "dissolved_at": _iso(now),
                    "dissolved_by": mine["id"],
                    "dissolution_reason": reason,
                    "cooldown_ends_at": cooldown_iso,
                    "updated_at": _iso(now)}},
        return_document=True)
    if not r:
        raise HTTPException(409, "cas_race_condition")
    await _emit_audit("TRADE_PACT_DISSOLVED", user["id"], mine["id"],
                       pact_id,
                       {"reason": reason,
                        "cooldown_ends_at": cooldown_iso,
                        "other_guild_id":
                            pact["guild_b_id"] if mine["id"] == pact["guild_a_id"]
                                else pact["guild_a_id"]})
    return {"status": "ok", "pact": _pact_public(r)}


@router.get("/mine")
async def mine_pacts(status: Optional[str] = None,
                       user: dict = Depends(get_current_user)):
    mine = await user_guild_or_404(db, user["id"])
    q: dict = {"$or": [{"guild_a_id": mine["id"]},
                         {"guild_b_id": mine["id"]}]}
    if status:
        q["status"] = status
    cur = db.guild_trade_pacts.find(q, {"_id": 0}).sort("created_at", -1)
    pacts = [_pact_public(p) async for p in cur]
    active_count = sum(1 for p in pacts if p.get("status") == "accepted")
    return {"pacts": pacts,
            "active_count": active_count,
            "max_accepted": MAX_ACCEPTED_PACTS}


@router.get("/partners")
async def active_partners(user: dict = Depends(get_current_user)):
    mine = await user_guild_or_404(db, user["id"])
    cur = db.guild_trade_pacts.find(
        {"$or": [{"guild_a_id": mine["id"]},
                   {"guild_b_id": mine["id"]}],
         "status": "accepted"},
        {"_id": 0})
    partners = []
    async for p in cur:
        other_id = p["guild_b_id"] if p["guild_a_id"] == mine["id"] else p["guild_a_id"]
        g = await db.guilds.find_one({"id": other_id},
                                       {"_id": 0, "id": 1, "name": 1})
        if g:
            partners.append({"guild_id": g["id"], "guild_name": g["name"],
                                "since": p["activated_at"],
                                "pact_id": p["id"]})
    return {"partners": partners, "count": len(partners)}


# ── Admin routes ─────────────────────────────────────────────────────
@admin_router.get("/stats")
async def admin_stats(admin: dict = Depends(get_admin_user)):
    pipe = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    by_status = await db.guild_trade_pacts.aggregate(pipe).to_list(50)
    total_active = next((x["count"] for x in by_status
                            if x["_id"] == "accepted"), 0)
    return {"by_status": by_status,
            "total_active": total_active}


@admin_router.post("/{pact_id}/force-dissolve")
async def admin_force_dissolve(pact_id: str,
                                 admin: dict = Depends(get_admin_user)):
    now_iso = _iso(_now())
    r = await db.guild_trade_pacts.find_one_and_update(
        {"id": pact_id,
         "status": {"$in": ["accepted", "pending_request"]}},
        {"$set": {"status": "dissolved",
                    "dissolved_at": now_iso,
                    "dissolved_by": "admin",
                    "dissolution_reason": "admin_force",
                    "cooldown_ends_at": None,
                    "updated_at": now_iso}},
        return_document=True)
    if not r:
        raise HTTPException(404, "pact_not_found_or_already_resolved")
    await _emit_audit("TRADE_PACT_FORCE_DISSOLVED", admin["id"], None,
                       pact_id, {"admin_id": admin["id"]})
    return {"status": "ok", "pact": _pact_public(r)}


__all__ = ["router", "admin_router", "ensure_indexes",
             "MAX_ACCEPTED_PACTS", "UNILATERAL_COOLDOWN_DAYS"]
