"""ROUND 14.B — Admin Game Health endpoints (read-only).

Mounted under `/api/admin/game-health/*`. All endpoints require admin
auth (`get_admin_user`). No mutations, no PII, no test/demo guilds.

Endpoints (P0 scope):
  • GET /economy?window=24h|7d|all   → faucets/sinks/net inflation
  • GET /materials                   → top materials by inventory volume
  • GET /shop?window=...             → NPC shop volume + revenue
  • GET /progression                 → roster + guild level distribution
  • GET /competitive                 → PvP rating distribution
  • GET /anomalies                   → high-priority warnings

Deferred to Round 14 v2 (out of scope for first beta-readiness pass):
  • Material source/sink matrix UI
  • Loot frequency simulation endpoint
  • Onboarding funnel timing
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query

from app.core.database import db
from app.core.security import get_admin_user


router = APIRouter(prefix="/api/admin/game-health", tags=["admin-game-health"])


EXCLUDE_GUILD = {
    "is_test_artifact": {"$ne": True},
    "is_demo_opponent": {"$ne": True},
    "is_demo_owner": {"$ne": True},
    "deleted_at": {"$exists": False},
}


def _window_cutoff(window: str) -> str | None:
    now = datetime.now(timezone.utc)
    if window == "24h":
        return (now - timedelta(hours=24)).isoformat()
    if window == "7d":
        return (now - timedelta(days=7)).isoformat()
    return None  # all-time


async def _eligible_guild_ids() -> list[str]:
    rows = await db.guilds.find(EXCLUDE_GUILD, {"_id": 0, "id": 1}).to_list(20_000)
    return [r["id"] for r in rows]


async def _audit_by_window(gids: list[str], cutoff: str | None) -> list[dict]:
    q: dict = {}
    if cutoff:
        q["created_at"] = {"$gte": cutoff}
    rows = await db.audit_log.find(
        q, {"_id": 0, "event_type": 1, "gold_delta": 1, "quantity": 1,
             "source": 1, "actor_guild_id": 1, "metadata": 1}
    ).to_list(200_000)
    # Drop test/demo events; admin grants are split out separately.
    gset = set(gids)
    return [r for r in rows if r.get("actor_guild_id") in gset
            or r.get("actor_guild_id") is None]


@router.get("/economy")
async def economy_health(
    window: str = Query("24h", regex="^(24h|7d|all)$"),
    _admin: dict = Depends(get_admin_user),
) -> dict:
    """Faucets/sinks/net inflation summary. Admin-granted gold excluded."""
    cutoff = _window_cutoff(window)
    gids = await _eligible_guild_ids()
    events = await _audit_by_window(gids, cutoff)

    faucet_evt = {"shop_system_sale", "expedition_complete_gold",
                  "raid_complete_gold", "contract_claimed"}
    sink_evt = {"shop_system_purchase", "auction_create_fee",
                "training_specialization", "territory_upgrade"}
    admin_grant_evt = {"admin_grant_gold", "admin_grant_item"}

    faucets = 0
    sinks = 0
    admin_grants = 0
    by_type: Counter = Counter()
    for e in events:
        et = e.get("event_type") or "unknown"
        delta = int(e.get("gold_delta") or 0)
        by_type[et] += 1
        if et in admin_grant_evt:
            admin_grants += abs(delta)
            continue
        if et in faucet_evt or delta > 0:
            faucets += abs(delta)
        elif et in sink_evt or delta < 0:
            sinks += abs(delta)

    # Current gold balance in circulation (player-facing).
    guilds = await db.guilds.find(
        {**EXCLUDE_GUILD}, {"_id": 0, "gold": 1}
    ).to_list(20_000)
    total_gold = sum(int(g.get("gold") or 0) for g in guilds)

    return {
        "window": window,
        "eligible_guilds": len(gids),
        "current_gold_in_circulation": total_gold,
        "faucets_total_gold": faucets,
        "sinks_total_gold": sinks,
        "net_inflation_gold": faucets - sinks,
        "admin_granted_gold": admin_grants,  # tracked SEPARATELY
        "audit_event_counts": dict(by_type.most_common(20)),
    }


@router.get("/materials")
async def materials_health(
    _admin: dict = Depends(get_admin_user),
) -> dict:
    """Top materials by inventory volume across all eligible guilds."""
    gids = await _eligible_guild_ids()
    inv = await db.inventory_items.find(
        {"guild_id": {"$in": gids}},
        {"_id": 0, "item_id": 1, "quantity": 1},
    ).to_list(500_000)
    qty_by_item: Counter = Counter()
    for r in inv:
        qty_by_item[r["item_id"]] += int(r.get("quantity") or 1)
    metas = await db.items.find(
        {"id": {"$in": list(qty_by_item.keys())},
         "item_type": {"$in": ["material", "consumable"]}},
        {"_id": 0, "id": 1, "slug": 1, "display_name_it": 1, "rarity": 1,
         "item_type": 1, "required_adventurer_level": 1},
    ).to_list(2_000)
    rows = []
    for m in metas:
        rows.append({
            "slug": m["slug"],
            "name_it": m.get("display_name_it") or m["slug"],
            "rarity": m.get("rarity"),
            "type": m.get("item_type"),
            "required_level": m.get("required_adventurer_level"),
            "total_in_circulation": qty_by_item.get(m["id"], 0),
        })
    rows.sort(key=lambda r: -r["total_in_circulation"])
    return {"materials_total": len(rows), "materials": rows}


@router.get("/shop")
async def shop_health(
    window: str = Query("24h", regex="^(24h|7d|all)$"),
    _admin: dict = Depends(get_admin_user),
) -> dict:
    """NPC shop purchase volume + revenue per material."""
    cutoff = _window_cutoff(window)
    gids = await _eligible_guild_ids()
    events = await _audit_by_window(gids, cutoff)
    purchases = [e for e in events if e.get("event_type") == "shop_system_purchase"]
    by_slug: Counter = Counter()
    revenue = 0
    for e in purchases:
        meta = e.get("metadata") or {}
        slug = meta.get("item_slug") or "unknown"
        qty = int(meta.get("quantity") or 1)
        by_slug[slug] += qty
        revenue += int(meta.get("gold_spent") or 0)
    return {
        "window": window,
        "total_buys": len(purchases),
        "total_units_bought": sum(by_slug.values()),
        "revenue_to_npc_gold": revenue,
        "top_5_materials_bought": [
            {"slug": s, "units": c} for s, c in by_slug.most_common(5)
        ],
    }


@router.get("/progression")
async def progression_health(
    _admin: dict = Depends(get_admin_user),
) -> dict:
    gids = await _eligible_guild_ids()
    guilds = await db.guilds.find(
        {**EXCLUDE_GUILD},
        {"_id": 0, "id": 1, "level": 1},
    ).to_list(20_000)
    advs = await db.adventurers.find(
        {"guild_id": {"$in": gids}, "is_retired": {"$ne": True}},
        {"_id": 0, "guild_id": 1, "level": 1},
    ).to_list(200_000)
    rosters: Counter = Counter()
    for a in advs:
        rosters[a["guild_id"]] += 1
    return {
        "eligible_guilds": len(gids),
        "guild_level_dist": dict(Counter(g.get("level", 1) for g in guilds)),
        "roster_size_dist": dict(Counter(rosters.values()).most_common(20)),
        "adv_level_dist": dict(Counter(a.get("level", 1) for a in advs).most_common(20)),
        "avg_roster_size": sum(rosters.values()) // max(1, len(gids)),
    }


@router.get("/competitive")
async def competitive_health(
    _admin: dict = Depends(get_admin_user),
) -> dict:
    season = await db.seasons.find_one({"status": "active"}, {"_id": 0})
    if not season:
        return {"active_season": None, "participants": 0}
    gids = await _eligible_guild_ids()
    parts = await db.season_participations.find(
        {"season_id": season["season_id"],
         "guild_id": {"$in": gids}, "is_test": {"$ne": True}},
        {"_id": 0, "rating": 1, "league": 1, "wins": 1, "losses": 1,
         "attacks_played": 1},
    ).to_list(20_000)
    return {
        "active_season": season.get("slug") or season.get("season_id"),
        "participants": len(parts),
        "leagues": dict(Counter(p.get("league") or "unranked" for p in parts)),
        "rating_avg": (
            sum(int(p.get("rating") or 1000) for p in parts) // max(1, len(parts))
        ),
        "attacks_played_total": sum(int(p.get("attacks_played") or 0) for p in parts),
        "wins_total": sum(int(p.get("wins") or 0) for p in parts),
    }


@router.get("/anomalies")
async def anomalies_health(
    _admin: dict = Depends(get_admin_user),
) -> dict:
    """List of high-priority warnings detected at runtime."""
    warnings = []
    # 1. Items in catalog without required_adventurer_level.
    bad_items = await db.items.count_documents(
        {"is_active": True,
         "$or": [{"required_adventurer_level": {"$exists": False}},
                 {"required_adventurer_level": None},
                 {"required_adventurer_level": {"$lt": 1}}]}
    )
    if bad_items > 0:
        warnings.append({
            "severity": "warn",
            "code": "items_without_required_level",
            "count": bad_items,
        })
    # 2. Guilds with negative gold (should be impossible).
    neg_gold = await db.guilds.count_documents({"gold": {"$lt": 0}, **EXCLUDE_GUILD})
    if neg_gold > 0:
        warnings.append({
            "severity": "critical",
            "code": "guilds_with_negative_gold",
            "count": neg_gold,
        })
    # 3. Dungeons/raids without lore_reviewed.
    d_bad = await db.dungeons.count_documents({"lore_reviewed": {"$ne": True}})
    r_bad = await db.raid_dungeons.count_documents({"lore_reviewed": {"$ne": True}})
    if d_bad > 0:
        warnings.append({"severity": "warn", "code": "dungeons_not_lore_reviewed",
                         "count": d_bad})
    if r_bad > 0:
        warnings.append({"severity": "warn", "code": "raids_not_lore_reviewed",
                         "count": r_bad})
    # 4. Equipment rows with adventurer below required_level (post-audit residual).
    # Cheap proxy: count equipped_items where flagged by last audit run.
    return {"warnings": warnings, "checked_at": datetime.now(timezone.utc).isoformat()}


__all__ = ["router"]
