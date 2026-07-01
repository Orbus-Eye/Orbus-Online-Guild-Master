"""ROUND 16.0 — Seed class_halls for every active guild.

Idempotent. For each guild not flagged `archived_pre_launch=True`, ensures
one `class_halls` row per base class (10 rows per guild). Halls become
`is_unlocked=true` if the guild has at least one adventurer of that
class.

Usage:
    python -m app.scripts.round160_seed_class_halls [--dry-run]
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from app.class_halls.services import seed_class_halls_for_guild


async def _run(db, *, dry_run: bool) -> dict[str, int]:
    seen = 0
    inserted_total = 0
    skipped_total = 0
    # Skip pre-launch archived guilds (R14 cleanup batch).
    query = {"archived_pre_launch": {"$ne": True}}
    cursor = db.guilds.find(query, {"_id": 0, "id": 1, "name": 1})
    async for g in cursor:
        seen += 1
        if dry_run:
            # Count how many rows would be inserted without writing.
            existing = await db.class_halls.count_documents(
                {"guild_id": g["id"]})
            inserted_total += max(0, 10 - existing)
            skipped_total += existing
            continue
        res = await seed_class_halls_for_guild(
            db, guild_id=g["id"], actor_user_id=None)
        inserted_total += res["inserted"]
        skipped_total += res["skipped"]
    return {"guilds_seen": seen, "halls_inserted": inserted_total,
            "halls_skipped": skipped_total}


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    load_dotenv()
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        print("ERROR: MONGO_URL / DB_NAME not configured", file=sys.stderr)
        return 2
    client = AsyncIOMotorClient(mongo_url)
    try:
        db = client[db_name]
        out = await _run(db, dry_run=args.dry_run)
        print({"dry_run": args.dry_run, **out})
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
