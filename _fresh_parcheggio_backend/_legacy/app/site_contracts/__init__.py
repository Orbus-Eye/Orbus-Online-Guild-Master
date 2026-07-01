"""ROUND 16.3 Phase 3 — Site Contracts (guild passive income) V1.

Formula (trasparente):
    level      = guild.guild_level or guild.level or 1
    base       = config.base_income + config.level_bonus_per_level * (level - 1)
    rep_mult   = 1 + min(guild.reputation / 1000, 0.2)  (max +20%)
    event_mod  = active_continent_event.modifier_value / 100 se site_income_pct
    gross      = base * rep_mult * (1 + event_mod)
    final      = min(gross, config.hard_cap_daily)

Idempotency: unique index (guild_id, day_bucket) su guild_site_income_ledger.
On-visit fallback: la row del giorno è creata al primo hit di /today.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.database import db
from app.core.security import get_current_user, get_admin_user
from app.guilds.services import user_guild_or_404

logger = logging.getLogger("orbus.site_contracts")

router = APIRouter(prefix="/api/site-income", tags=["site-income"])
admin_router = APIRouter(prefix="/api/admin/site-income",
                         tags=["admin", "site-income"])

CONFIG_ID = "singleton"
DEFAULT_CONFIG = {
    "id": CONFIG_ID,
    "base_income": 20,
    "level_bonus_per_level": 5,
    "hard_cap_daily": 500,
    "reputation_multiplier_max": 1.2,
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _day_bucket(dt: Optional[datetime] = None) -> str:
    d = dt or _now()
    return d.strftime("%Y-%m-%d")


async def seed_site_income_config() -> dict:
    r = await db.guild_site_income_config.update_one(
        {"id": CONFIG_ID},
        {"$setOnInsert": {**DEFAULT_CONFIG, "created_at": _iso(_now())}},
        upsert=True,
    )
    return {"inserted": bool(r.upserted_id)}


async def _get_config() -> dict:
    doc = await db.guild_site_income_config.find_one(
        {"id": CONFIG_ID}, {"_id": 0},
    )
    if not doc:
        # First-time cold-start: seed then re-read
        await seed_site_income_config()
        doc = await db.guild_site_income_config.find_one(
            {"id": CONFIG_ID}, {"_id": 0},
        )
    return doc or DEFAULT_CONFIG


async def _emit_audit(event_type: str, actor_user_id: Optional[str],
                      actor_guild_id: Optional[str], related_entity_id: str,
                      metadata: dict) -> None:
    try:
        from app.audit.log import write_audit
        await write_audit(
            db, event_type=event_type, actor_user_id=actor_user_id,
            actor_guild_id=actor_guild_id, source="site_contracts",
            related_entity_id=related_entity_id, metadata=metadata,
        )
    except Exception as exc:
        logger.debug("site_contracts.audit_emit skipped %s: %s", event_type, exc)


def _guild_level(guild: dict) -> int:
    lv = guild.get("guild_level") or guild.get("level") or 1
    try:
        return max(1, int(lv))
    except (TypeError, ValueError):
        return 1


def _reputation_multiplier(guild: dict, cap: float = 1.2) -> float:
    rep = guild.get("reputation") or 0
    try:
        rep_f = float(rep)
    except (TypeError, ValueError):
        rep_f = 0.0
    return min(1.0 + max(0.0, rep_f) / 1000.0, cap)


async def _get_active_event_modifier(guild: dict) -> tuple[int, Optional[dict]]:
    """Returns (modifier_pct_int, event_info | None) for active event on the guild's continent."""
    pres = await db.guild_world_presence.find_one(
        {"guild_id": guild["id"], "status": "active"}, {"_id": 0, "continent_slug": 1},
    )
    if not pres:
        return 0, None
    slug = pres["continent_slug"]
    from app.world_events import _get_active_event_for_continent
    data = await _get_active_event_for_continent(slug)
    if not data:
        return 0, None
    cat = data.get("catalog") or {}
    if cat.get("modifier_type") != "site_income_pct":
        return 0, {"event_slug": cat.get("slug"), "modifier_type": cat.get("modifier_type"),
                   "modifier_value": 0}
    return int(cat.get("modifier_value") or 0), {
        "event_slug": cat.get("slug"),
        "modifier_type": "site_income_pct",
        "modifier_value": int(cat.get("modifier_value") or 0),
    }


def _compute_breakdown(config: dict, guild: dict, event_mod_pct: int) -> dict:
    level = _guild_level(guild)
    base_flat = int(config.get("base_income", 20))
    lvl_bonus_per = int(config.get("level_bonus_per_level", 5))
    hard_cap = int(config.get("hard_cap_daily", 500))
    rep_cap = float(config.get("reputation_multiplier_max", 1.2))
    base = base_flat + lvl_bonus_per * (level - 1)
    rep_mult = _reputation_multiplier(guild, cap=rep_cap)
    reputation_bonus = int(round(base * (rep_mult - 1.0)))
    event_multiplier = 1.0 + (event_mod_pct / 100.0)
    gross = (base + reputation_bonus) * event_multiplier
    final = int(min(round(gross), hard_cap))
    event_bonus = int(round((base + reputation_bonus) * (event_multiplier - 1.0)))
    return {
        "level": level,
        "base": base_flat,
        "level_bonus": base - base_flat,
        "reputation_bonus": reputation_bonus,
        "event_modifier_pct": event_mod_pct,
        "event_bonus": event_bonus,
        "hard_cap_daily": hard_cap,
        "total_amount": final,
    }


async def _ensure_today_row(guild: dict) -> dict:
    day = _day_bucket()
    existing = await db.guild_site_income_ledger.find_one(
        {"guild_id": guild["id"], "day_bucket": day}, {"_id": 0},
    )
    if existing:
        return existing
    config = await _get_config()
    event_mod_pct, event_info = await _get_active_event_modifier(guild)
    breakdown = _compute_breakdown(config, guild, event_mod_pct)
    doc = {
        "id": str(uuid.uuid4()),
        "guild_id": guild["id"],
        "day_bucket": day,
        "base_income": breakdown["base"],
        "level_bonus": breakdown["level_bonus"],
        "reputation_bonus": breakdown["reputation_bonus"],
        "continent_bonus": 0,  # reserved for Phase 4
        "event_modifier_pct": breakdown["event_modifier_pct"],
        "event_bonus": breakdown["event_bonus"],
        "event_info": event_info,
        "hard_cap_daily": breakdown["hard_cap_daily"],
        "total_amount": breakdown["total_amount"],
        "claimed_at": None,
        "audit_source": "site_income_daily",
        "created_at": _iso(_now()),
    }
    try:
        await db.guild_site_income_ledger.insert_one(doc)
    except Exception as exc:
        # Race: unique index (guild_id, day_bucket) may reject a duplicate insert.
        logger.debug("site_income insert race — re-fetching: %s", exc)
        existing = await db.guild_site_income_ledger.find_one(
            {"guild_id": guild["id"], "day_bucket": day}, {"_id": 0},
        )
        if existing:
            return existing
        raise
    doc.pop("_id", None)
    return doc


def _pub_ledger(row: dict) -> dict:
    out = {k: v for k, v in row.items() if not k.startswith("_")}
    out.pop("_id", None)
    return out


# ── PUBLIC ROUTES ────────────────────────────────────────────────────
@router.get("/today")
async def today(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    row = await _ensure_today_row(guild)
    return {
        "day_bucket": row["day_bucket"],
        "breakdown": {
            "base": row["base_income"],
            "level_bonus": row["level_bonus"],
            "reputation_bonus": row.get("reputation_bonus", 0),
            "event_bonus": row.get("event_bonus", 0),
            "event_modifier_pct": row.get("event_modifier_pct", 0),
            "event_info": row.get("event_info"),
        },
        "total_amount": row["total_amount"],
        "claimed_at": row.get("claimed_at"),
    }


@router.post("/claim")
async def claim(current_user: dict = Depends(get_current_user)):
    guild = await user_guild_or_404(db, current_user["id"])
    row = await _ensure_today_row(guild)
    now_iso = _iso(_now())
    # CAS: only claim if claimed_at is None
    flipped = await db.guild_site_income_ledger.find_one_and_update(
        {"id": row["id"], "claimed_at": None},
        {"$set": {"claimed_at": now_iso}},
        projection={"_id": 0},
    )
    if not flipped:
        return {"status": "skipped", "reason": "already_claimed",
                "row": _pub_ledger(row)}
    # Credit gold atomically
    amount = int(row["total_amount"])
    await db.guilds.update_one(
        {"id": guild["id"]},
        {"$inc": {"gold": amount},
         "$set": {"updated_at": now_iso}},
    )
    await _emit_audit(
        "SITE_INCOME_CLAIMED", current_user.get("id"), guild["id"], row["id"],
        {"day_bucket": row["day_bucket"], "amount": amount,
         "event_modifier_pct": row.get("event_modifier_pct", 0)},
    )
    flipped["claimed_at"] = now_iso
    return {"status": "ok", "amount": amount,
            "row": _pub_ledger(flipped)}


@router.get("/history")
async def history(days: int = 7, current_user: dict = Depends(get_current_user)):
    days = max(1, min(int(days), 30))
    guild = await user_guild_or_404(db, current_user["id"])
    rows = await db.guild_site_income_ledger.find(
        {"guild_id": guild["id"]}, {"_id": 0},
    ).sort("day_bucket", -1).limit(days).to_list(days)
    return {"rows": [_pub_ledger(r) for r in rows]}


# ── ADMIN ROUTES ────────────────────────────────────────────────────
class ConfigPatchBody(BaseModel):
    base_income: Optional[int] = Field(default=None, ge=0, le=1000)
    level_bonus_per_level: Optional[int] = Field(default=None, ge=0, le=100)
    hard_cap_daily: Optional[int] = Field(default=None, ge=0, le=100000)
    reputation_multiplier_max: Optional[float] = Field(default=None, ge=1.0, le=3.0)


@admin_router.get("/config")
async def admin_get_config(admin: dict = Depends(get_admin_user)):
    return {"config": await _get_config()}


@admin_router.patch("/config")
async def admin_patch_config(body: ConfigPatchBody,
                              admin: dict = Depends(get_admin_user)):
    changes = {k: v for k, v in body.model_dump().items() if v is not None}
    if not changes:
        raise HTTPException(400, "no_changes_provided")
    changes["updated_at"] = _iso(_now())
    r = await db.guild_site_income_config.find_one_and_update(
        {"id": CONFIG_ID},
        {"$set": changes},
        upsert=True,
        projection={"_id": 0},
    )
    if not r:
        r = await _get_config()
    r.update(changes)
    await _emit_audit(
        "SITE_INCOME_CONFIG_UPDATED", admin.get("id"), None, CONFIG_ID,
        {"changes": {k: v for k, v in changes.items() if k != "updated_at"}},
    )
    return {"config": r}


@admin_router.get("/stats")
async def admin_stats(window_days: int = 7,
                      admin: dict = Depends(get_admin_user)):
    window_days = max(1, min(int(window_days), 30))
    from datetime import timedelta
    since = _day_bucket(_now() - timedelta(days=window_days))
    cur = db.guild_site_income_ledger.aggregate([
        {"$match": {"day_bucket": {"$gte": since},
                    "claimed_at": {"$ne": None}}},
        {"$group": {"_id": "$guild_id",
                    "total_amount": {"$sum": "$total_amount"},
                    "days_claimed": {"$sum": 1}}},
        {"$sort": {"total_amount": -1}},
        {"$limit": 10},
    ])
    top = await cur.to_list(10)
    total_agg = db.guild_site_income_ledger.aggregate([
        {"$match": {"day_bucket": {"$gte": since},
                    "claimed_at": {"$ne": None}}},
        {"$group": {"_id": None, "total": {"$sum": "$total_amount"},
                    "rows": {"$sum": 1}}},
    ])
    total = (await total_agg.to_list(1)) or [{}]
    return {
        "window_days": window_days,
        "total_amount_paid": total[0].get("total", 0),
        "rows_claimed": total[0].get("rows", 0),
        "top_guilds": [
            {"guild_id": r["_id"], "total_amount": r["total_amount"],
             "days_claimed": r["days_claimed"]}
            for r in top
        ],
    }


async def ensure_indexes() -> None:
    """Best-effort ensure of unique index on ledger + config."""
    try:
        await db.guild_site_income_ledger.create_index(
            [("guild_id", 1), ("day_bucket", 1)], unique=True,
            name="uniq_guild_day",
        )
    except Exception as exc:
        logger.debug("index create skipped: %s", exc)


__all__ = ["router", "admin_router", "seed_site_income_config",
           "ensure_indexes", "_compute_breakdown", "_ensure_today_row",
           "_get_active_event_modifier", "CONFIG_ID"]
