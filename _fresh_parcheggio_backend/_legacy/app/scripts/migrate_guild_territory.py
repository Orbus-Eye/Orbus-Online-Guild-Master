"""ROUND 6B.1 — Migrate legacy guilds to the new Territory model.

Idempotent backfill:
  - Skip guilds that already have a `guild_structures` doc.
  - For every other guild, compute structure levels from HISTORICAL ACTIVITY
    (snapshot of current DB state — conservative, not from audit trails).
  - Insert one `guild_structures` doc + a `guild_territory_migrated` audit row.

Activity → backfill mapping (decided in the round design):
  - dormitories          ← roster size (Lv2..Lv6 standard, Lv7 LEGACY WING for >30)
  - auction_house Lv2    ← any market_listings.seller_guild_id == guild
  - auction_house Lv1    ← any market_listings.buyer_guild_id == guild (and no Lv2)
  - forge Lv3            ← any inventory_items.enchants.0 active
  - forge Lv2            ← any inventory_items.refinement_level > 0 (and no Lv3)
  - war_room Lv2         ← any raids by guild
  - consortium_hall Lv1  ← any consortium_members membership
  - communication_hall Lv2 ← any chat_messages with channel_type != global
  - communication_hall Lv1 ← any chat_messages with channel_type == global (and no Lv2)
  - market_stall         ← system shop (audit_log `shop_system_purchase`/`_sale`)
                            Lv2 if any sale, Lv1 if only purchase.

Run modes:
  python -m app.scripts.migrate_guild_territory --dry-run
  python -m app.scripts.migrate_guild_territory --dry-run --limit 10
  python -m app.scripts.migrate_guild_territory                 (full run)

Refuses APP_ENV=production.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# We import structures lazily inside main so a direct python invocation works
# from any cwd without polluting the test importer.


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _activity_signals(db, guild_id: str) -> dict:
    """Probe activity-derived signals for one guild. All `find_one`s are
    O(1) with existing indexes (guild_id is indexed in every collection).
    """
    sig = {}
    sig["roster_size"] = await db.adventurers.count_documents({"guild_id": guild_id})
    sig["mkt_sold"] = await db.market_listings.find_one(
        {"seller_guild_id": guild_id}, {"_id": 1}
    ) is not None
    sig["mkt_bought"] = await db.market_listings.find_one(
        {"buyer_guild_id": guild_id}, {"_id": 1}
    ) is not None
    sig["item_enchanted"] = await db.inventory_items.find_one(
        {"guild_id": guild_id, "enchants.0": {"$exists": True}}, {"_id": 1}
    ) is not None
    sig["item_refined"] = await db.inventory_items.find_one(
        {"guild_id": guild_id, "refinement_level": {"$gt": 0}}, {"_id": 1}
    ) is not None
    sig["raid_any"] = await db.raids.find_one(
        {"guild_id": guild_id}, {"_id": 1}
    ) is not None
    sig["consortium_member"] = await db.consortium_members.find_one(
        {"guild_id": guild_id}, {"_id": 1}
    ) is not None
    sig["chat_consortium"] = await db.chat_messages.find_one(
        {"sender_guild_id": guild_id, "channel_type": {"$ne": "global"}}, {"_id": 1}
    ) is not None
    sig["chat_global"] = await db.chat_messages.find_one(
        {"sender_guild_id": guild_id, "channel_type": "global"}, {"_id": 1}
    ) is not None
    # Shop NPC (Phase 19.4b): audit log signals
    sig["shop_sold"] = await db.audit_log.find_one(
        {"actor_guild_id": guild_id, "event_type": "shop_system_sale"}, {"_id": 1}
    ) is not None
    sig["shop_bought"] = await db.audit_log.find_one(
        {"actor_guild_id": guild_id, "event_type": "shop_system_purchase"}, {"_id": 1}
    ) is not None
    return sig


def _compute_structures(sig: dict, default_doc: dict, *,
                        required_dormitory_level_for_roster) -> tuple[dict, list[str]]:
    """Pure projection: signals → final structures dict + audit reasons."""
    structures = {k: dict(v) for k, v in default_doc.items()}
    reasons: list[str] = []

    # Dormitories: only if >5 adventurers (else default Lv1 stays).
    n = int(sig.get("roster_size", 0))
    if n > 5:
        tgt = required_dormitory_level_for_roster(n)
        legacy = tgt >= 7
        structures["dormitories"] = {
            "level": tgt,
            "is_unlocked": True,
            "purchased_at": None,
            "upgraded_at": _utc_now_iso(),
            "acquired_via": "migration_legacy" if legacy else "migration",
        }
        reasons.append(
            f"dormitories→Lv{tgt}{' (LEGACY)' if legacy else ''} (roster={n})"
        )

    # Auction house: seller (Lv2) > buyer (Lv1).
    if sig["mkt_sold"]:
        structures["auction_house"] = _migrated(2)
        reasons.append("auction_house→Lv2 (market sales)")
    elif sig["mkt_bought"]:
        structures["auction_house"] = _migrated(1)
        reasons.append("auction_house→Lv1 (market purchases)")

    # Forge: enchant (Lv3) > refine (Lv2).
    if sig["item_enchanted"]:
        structures["forge"] = _migrated(3)
        reasons.append("forge→Lv3 (enchanted items)")
    elif sig["item_refined"]:
        structures["forge"] = _migrated(2)
        reasons.append("forge→Lv2 (refined items)")

    # War room: any raid history → Lv2 (raid.start.t1 unlock).
    if sig["raid_any"]:
        structures["war_room"] = _migrated(2)
        reasons.append("war_room→Lv2 (raid history)")

    # Consortium hall: membership → Lv1.
    if sig["consortium_member"]:
        structures["consortium_hall"] = _migrated(1)
        reasons.append("consortium_hall→Lv1 (member)")

    # Communication hall: consortium chat (Lv2) > global chat (Lv1).
    if sig["chat_consortium"]:
        structures["communication_hall"] = _migrated(2)
        reasons.append("communication_hall→Lv2 (consortium chat)")
    elif sig["chat_global"]:
        structures["communication_hall"] = _migrated(1)
        reasons.append("communication_hall→Lv1 (global chat)")

    # Market stall: shop NPC sell (Lv2) > buy (Lv1).
    if sig["shop_sold"]:
        structures["market_stall"] = _migrated(2)
        reasons.append("market_stall→Lv2 (shop NPC sales)")
    elif sig["shop_bought"]:
        structures["market_stall"] = _migrated(1)
        reasons.append("market_stall→Lv1 (shop NPC purchases)")

    return structures, reasons


def _migrated(level: int) -> dict:
    return {
        "level": int(level),
        "is_unlocked": True,
        "purchased_at": None,
        "upgraded_at": _utc_now_iso(),
        "acquired_via": "migration",
    }


async def run(args) -> int:
    if os.environ.get("APP_ENV") == "production":
        print("ERROR: refuses to run with APP_ENV=production", file=sys.stderr)
        return 2

    # Lazy import — keeps script CLI fast and decoupled from the FastAPI app.
    from app.territory.structures import (
        default_structures_doc,
        required_dormitory_level_for_roster,
    )

    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    q = db.guilds.find({}, {"_id": 0, "id": 1, "name": 1})
    if args.limit:
        q = q.limit(int(args.limit))

    total = 0
    migrated = 0
    skipped = 0
    samples = []  # capture the first N reports for the user
    async for guild in q:
        total += 1
        gid = guild["id"]
        existing = await db.guild_structures.find_one({"guild_id": gid}, {"_id": 1})
        if existing:
            skipped += 1
            continue

        sig = await _activity_signals(db, gid)
        structures, reasons = _compute_structures(
            sig, default_structures_doc(),
            required_dormitory_level_for_roster=required_dormitory_level_for_roster,
        )

        if args.dry_run:
            samples.append({"guild": guild.get("name"), "id": gid,
                            "reasons": reasons, "roster": sig["roster_size"]})
            migrated += 1
            continue

        now = _utc_now_iso()
        doc = {
            "id": str(uuid.uuid4()),
            "guild_id": gid,
            "structures": structures,
            "created_at": now,
            "updated_at": now,
        }
        try:
            await db.guild_structures.insert_one(doc)
        except Exception as exc:  # duplicate guild_id (race) → tolerated
            print(f"WARN insert failed for {gid}: {exc}", file=sys.stderr)
            continue
        # Best-effort audit row
        try:
            await db.audit_log.insert_one({
                "id": str(uuid.uuid4()),
                "event_type": "guild_territory_migrated",
                "actor_user_id": None,
                "actor_guild_id": gid,
                "item_slug": None, "item_template_id": None,
                "quantity": None, "gold_delta": None,
                "source": "migrate_guild_territory",
                "related_entity_id": doc["id"],
                "metadata": {"reasons": reasons,
                             "roster_size": sig["roster_size"]},
                "created_at": now,
            })
        except Exception:
            pass
        migrated += 1

    print(f"\n=== migrate_guild_territory ({'DRY-RUN' if args.dry_run else 'APPLIED'}) ===")
    print(f"  total scanned: {total}")
    print(f"  migrated:      {migrated}")
    print(f"  skipped (existed): {skipped}")
    if samples:
        print(f"\nSample (first {min(len(samples), 10)} guilds, dry-run):")
        for s in samples[:10]:
            label = s["guild"][:32] if s["guild"] else "<noname>"
            print(f"  - {label:<32} roster={s['roster']:>3}  → {', '.join(s['reasons']) or '(defaults only)'}")
    return 0


def parse_args(argv):
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true",
                   help="Compute & print without writing.")
    p.add_argument("--limit", type=int, default=None,
                   help="Process at most N guilds (preview).")
    return p.parse_args(argv)


if __name__ == "__main__":
    sys.exit(asyncio.run(run(parse_args(sys.argv[1:]))))
