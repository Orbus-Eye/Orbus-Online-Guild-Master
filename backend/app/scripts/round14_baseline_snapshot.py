"""ROUND 14.A.1 — Baseline snapshot (read-only).

Extracts beta-readiness metrics from MongoDB without mutating any document.
Excludes test/demo guilds + never exposes PII (no email, no _id, no
owner_user_id). Output JSON saved to /app/memory/.

Run:
    cd /app/backend && python -m app.scripts.round14_baseline_snapshot
"""
from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from collections import Counter

from motor.motor_asyncio import AsyncIOMotorClient


# ─── Filters: never count test artifacts in player-facing economy stats ───
EXCLUDE_GUILD = {
    "$and": [
        {"is_test_artifact": {"$ne": True}},
        {"is_demo_opponent": {"$ne": True}},
        {"is_demo_owner": {"$ne": True}},
        {"deleted_at": {"$exists": False}},
    ]
}


def _percentiles(vals: list[int], pcts=(25, 50, 75, 90, 95)) -> dict:
    if not vals:
        return {f"p{p}": 0 for p in pcts}
    s = sorted(vals)
    n = len(s)
    out = {}
    for p in pcts:
        i = min(n - 1, max(0, int(round((p / 100.0) * (n - 1)))))
        out[f"p{p}"] = s[i]
    return out


async def collect(db) -> dict:
    out: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "round": "14.A.1",
    }

    # ── Guilds ──
    guilds = await db.guilds.find(EXCLUDE_GUILD, {
        "_id": 0, "id": 1, "name": 1, "level": 1, "gold": 1, "reputation": 1,
        "guild_public_id": 1,
    }).to_list(10_000)
    out["guilds"] = {
        "active_total": len(guilds),
        "level_dist": dict(Counter(g.get("level", 1) for g in guilds)),
        "gold": {
            "total_in_circulation": sum(int(g.get("gold") or 0) for g in guilds),
            "avg": (sum(int(g.get("gold") or 0) for g in guilds) // max(1, len(guilds))),
            **_percentiles([int(g.get("gold") or 0) for g in guilds]),
        },
        "reputation_p50": _percentiles(
            [int(g.get("reputation") or 0) for g in guilds]
        )["p50"],
        "top_5_by_gold_public": sorted(
            [{"public_id": g.get("guild_public_id"), "name": g.get("name"),
              "gold": int(g.get("gold") or 0)} for g in guilds],
            key=lambda r: -r["gold"],
        )[:5],
    }
    guild_ids = {g["id"] for g in guilds}

    # ── Adventurers / roster ──
    advs = await db.adventurers.find(
        {"guild_id": {"$in": list(guild_ids)},
         "is_retired": {"$ne": True}},
        {"_id": 0, "guild_id": 1, "level": 1},
    ).to_list(100_000)
    rosters = Counter()
    for a in advs:
        rosters[a["guild_id"]] += 1
    out["roster"] = {
        "total_adventurers": len(advs),
        "roster_size_dist": dict(Counter(rosters.values())),
        **_percentiles(list(rosters.values())),
        "avg_level": (
            sum(a.get("level", 1) for a in advs) // max(1, len(advs))
        ),
    }

    # ── Materials & items in inventory (by template) ──
    inv = await db.inventory_items.find(
        {"guild_id": {"$in": list(guild_ids)}},
        {"_id": 0, "item_id": 1, "quantity": 1, "guild_id": 1},
    ).to_list(500_000)
    item_qty = Counter()
    for r in inv:
        item_qty[r["item_id"]] += int(r.get("quantity") or 1)
    items_meta = await db.items.find(
        {"id": {"$in": list(item_qty.keys())}},
        {"_id": 0, "id": 1, "slug": 1, "rarity": 1, "item_type": 1,
         "lore_reviewed": 1, "display_name_it": 1, "is_active": 1},
    ).to_list(10_000)
    by_rarity = Counter()
    materials_dist = []
    items_dist = []
    for it in items_meta:
        qty = item_qty.get(it["id"], 0)
        by_rarity[it.get("rarity", "Common")] += qty
        row = {
            "slug": it["slug"],
            "name": it.get("display_name_it") or it["slug"],
            "rarity": it.get("rarity"),
            "type": it.get("item_type"),
            "total_in_inventories": qty,
        }
        if it.get("item_type") in ("material", "consumable"):
            materials_dist.append(row)
        else:
            items_dist.append(row)
    materials_dist.sort(key=lambda r: -r["total_in_inventories"])
    items_dist.sort(key=lambda r: -r["total_in_inventories"])
    out["items_economy"] = {
        "by_rarity_total_units": dict(by_rarity),
        "top_10_materials_by_volume": materials_dist[:10],
        "bottom_5_materials_by_volume": materials_dist[-5:] if len(materials_dist) > 5 else [],
        "top_10_equipment_by_volume": items_dist[:10],
        "unique_item_templates_in_circulation": len(item_qty),
    }

    # ── Equipped vs stored ──
    equipped_total = await db.equipped_items.count_documents(
        {"guild_id": {"$in": list(guild_ids)}}
    )
    out["equipment"] = {
        "equipped_total": equipped_total,
        "inventory_rows_total": len(inv),
    }

    # ── Items catalog quality ──
    all_items = await db.items.count_documents({})
    reviewed = await db.items.count_documents({"lore_reviewed": True})
    req_level_set = await db.items.count_documents(
        {"required_adventurer_level": {"$gte": 1}}
    )
    out["items_catalog"] = {
        "total_items_in_catalog": all_items,
        "lore_reviewed": reviewed,
        "with_required_adventurer_level": req_level_set,
    }

    # ── PvP / Seasons ──
    season = await db.seasons.find_one({"status": "active"}, {"_id": 0})
    pvp_rows = []
    if season:
        pvp_rows = await db.season_participations.find(
            {"season_id": season["season_id"],
             "guild_id": {"$in": list(guild_ids)},
             "is_test": {"$ne": True}},
            {"_id": 0, "rating": 1, "league": 1, "wins": 1, "losses": 1,
             "draws": 1, "attacks_played": 1, "season_stats": 1},
        ).to_list(10_000)
    out["competitive"] = {
        "active_season_slug": season["season_id"] if season else None,
        "participants": len(pvp_rows),
        "ratings": _percentiles([int(p.get("rating") or 1000) for p in pvp_rows]),
        "leagues": dict(Counter(p.get("league") or "unranked" for p in pvp_rows)),
        "matches_played_total": sum(
            int(p.get("attacks_played") or 0) for p in pvp_rows
        ),
        "season_stats_aggregates": {
            "dungeon_clears_total": sum(
                int((p.get("season_stats") or {}).get("dungeon_clears") or 0)
                for p in pvp_rows
            ),
            "raid_clears_total": sum(
                int((p.get("season_stats") or {}).get("raid_clears") or 0)
                for p in pvp_rows
            ),
            "raid_score_total": sum(
                int((p.get("season_stats") or {}).get("raid_score") or 0)
                for p in pvp_rows
            ),
            "contracts_completed_total": sum(
                int((p.get("season_stats") or {}).get("contracts_completed") or 0)
                for p in pvp_rows
            ),
            "training_score_total": sum(
                int((p.get("season_stats") or {}).get("training_score") or 0)
                for p in pvp_rows
            ),
        },
    }

    # ── Dungeons / raids catalog ──
    out["content"] = {
        "dungeons_total": await db.dungeons.count_documents({}),
        "dungeons_lore_reviewed": await db.dungeons.count_documents(
            {"lore_reviewed": True}
        ),
        "raids_total": await db.raid_dungeons.count_documents({}),
        "raids_lore_reviewed": await db.raid_dungeons.count_documents(
            {"lore_reviewed": True}
        ),
    }

    # ── Audit ledger snapshot (24h gold & material events) ──
    cutoff_24h = (
        datetime.now(timezone.utc).timestamp() - 24 * 3600
    )
    from_iso = datetime.fromtimestamp(cutoff_24h, tz=timezone.utc).isoformat()
    cursor = db.audit_log.find(
        {"created_at": {"$gte": from_iso}},
        {"_id": 0, "event_type": 1, "gold_delta": 1, "quantity": 1,
         "source": 1, "actor_guild_id": 1},
    )
    events_24h = await cursor.to_list(50_000)
    # Strip events from test/demo guilds.
    events_24h = [e for e in events_24h
                  if (e.get("actor_guild_id") in guild_ids
                      or e.get("actor_guild_id") is None)]
    event_counts = Counter(e["event_type"] for e in events_24h)
    out["audit_ledger_24h"] = {
        "total_events": len(events_24h),
        "by_event_type": dict(event_counts.most_common(30)),
        "shop_buy_24h": event_counts.get("shop_system_purchase", 0),
        "shop_sell_24h": event_counts.get("shop_system_sale", 0),
        "season_stat_increments_24h": event_counts.get(
            "season_stat_incremented", 0
        ),
    }

    # ── Recruitment ──
    out["recruitment"] = {
        "frozen_total": await db.recruitment_state.count_documents(
            {"guild_id": {"$in": list(guild_ids)},
             "frozen_candidates": {"$exists": True, "$ne": []}}
        ),
    }
    return out


async def main():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    try:
        report = await collect(db)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = f"/app/memory/round14_baseline_{ts}.json"
        with open(out_path, "w") as f:
            json.dump(report, f, indent=2)
        # Print a 20-line summary on stdout.
        print(f"Saved → {out_path}")
        print(f"  guilds:           {report['guilds']['active_total']}")
        print(f"  gold_total:       {report['guilds']['gold']['total_in_circulation']:,}")
        print(f"  gold_p50/p95:     {report['guilds']['gold']['p50']:,} / {report['guilds']['gold']['p95']:,}")
        print(f"  advs:             {report['roster']['total_adventurers']}")
        print(f"  roster_p50/p95:   {report['roster']['p50']} / {report['roster']['p95']}")
        print(f"  items_catalog:    {report['items_catalog']['total_items_in_catalog']} (lore_reviewed={report['items_catalog']['lore_reviewed']})")
        print(f"  dungeons:         {report['content']['dungeons_total']}/{report['content']['dungeons_lore_reviewed']} reviewed")
        print(f"  raids:            {report['content']['raids_total']}/{report['content']['raids_lore_reviewed']} reviewed")
        print(f"  season:           {report['competitive']['active_season_slug']} participants={report['competitive']['participants']}")
        print(f"  pvp_matches:      {report['competitive']['matches_played_total']}")
        print(f"  audit_events_24h: {report['audit_ledger_24h']['total_events']}")
        print(f"  shop_buy_24h:     {report['audit_ledger_24h']['shop_buy_24h']}")
        return out_path
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
