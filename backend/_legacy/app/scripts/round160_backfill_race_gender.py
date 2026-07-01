"""ROUND 16.0 — Phase 3 — Backfill race + gender on every adventurer.

For each adventurer with `race_slug=None` OR `gender=None`, assigns:
  * race_slug: weighted random by rarity
        common=0.60, uncommon=0.25, rare=0.12, epic=0.03
  * gender: 50/50 male/female via `secrets.SystemRandom`

Strict invariants:
  * No two writes to the same adventurer on rerun (filter excludes
    already-assigned docs).
  * Audit emits TWO events per adventurer touched: one for race, one
    for gender (each only if that field was previously null).
  * Batch size 1000, cursor-based — safe for the 90.611-record table.

Usage:
    python -m app.scripts.round160_backfill_race_gender [--dry-run]
                                                       [--limit N]
"""
from __future__ import annotations

import argparse
import asyncio
import os
import secrets
import sys
from collections import Counter
from datetime import datetime, timezone

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from app.audit.log import write_audit


RARITY_WEIGHTS = {"common": 0.60, "uncommon": 0.25, "rare": 0.12, "epic": 0.03}
BATCH_SIZE = 1000

_rng = secrets.SystemRandom()


async def _load_race_pool(db) -> dict[str, list[str]]:
    pool: dict[str, list[str]] = {k: [] for k in RARITY_WEIGHTS}
    async for r in db.races.find({"is_active": True, "is_playable": True},
                                 {"_id": 0, "slug": 1, "rarity": 1}):
        if r["rarity"] in pool:
            pool[r["rarity"]].append(r["slug"])
    for rar, slugs in pool.items():
        assert slugs, f"No races for rarity {rar}; run seed_races first"
    return pool


def _pick_race(pool: dict[str, list[str]]) -> str:
    roll = _rng.random()
    cum = 0.0
    for rar, weight in RARITY_WEIGHTS.items():
        cum += weight
        if roll <= cum:
            return _rng.choice(pool[rar])
    return _rng.choice(pool["common"])


def _pick_gender() -> str:
    return "male" if _rng.random() < 0.5 else "female"


async def _run(db, *, dry_run: bool, limit: int | None) -> dict:
    pool = await _load_race_pool(db)
    now = datetime.now(timezone.utc)
    query = {"$or": [
        {"race_slug": {"$in": [None]}},
        {"race_slug": {"$exists": False}},
        {"gender": {"$in": [None]}},
        {"gender": {"$exists": False}},
    ]}
    cursor = db.adventurers.find(
        query,
        {"_id": 0, "id": 1, "guild_id": 1, "race_slug": 1, "gender": 1},
        batch_size=BATCH_SIZE,
    )
    seen = 0
    updated = 0
    race_writes = 0
    gender_writes = 0
    rarity_hist: Counter = Counter()
    gender_hist: Counter = Counter()

    async for adv in cursor:
        seen += 1
        if limit is not None and updated >= limit:
            break
        set_ops: dict = {"updated_at": now}
        needs_race = not adv.get("race_slug")
        needs_gender = not adv.get("gender")
        if needs_race:
            race_slug = _pick_race(pool)
            set_ops["race_slug"] = race_slug
        if needs_gender:
            gender = _pick_gender()
            set_ops["gender"] = gender
        if "race_slug" not in set_ops and "gender" not in set_ops:
            continue
        if dry_run:
            updated += 1
            if needs_race:
                race_writes += 1
            if needs_gender:
                gender_writes += 1
            continue
        await db.adventurers.update_one({"id": adv["id"]}, {"$set": set_ops})
        if needs_race:
            race_writes += 1
            rarity_hist[set_ops["race_slug"]] += 1
            await write_audit(
                db, event_type="adventurer_race_assigned",
                actor_user_id=None, actor_guild_id=adv.get("guild_id"),
                source="round160.backfill_race_gender",
                metadata={"adventurer_id": adv["id"],
                          "race_slug": set_ops["race_slug"]},
            )
        if needs_gender:
            gender_writes += 1
            gender_hist[set_ops["gender"]] += 1
            await write_audit(
                db, event_type="adventurer_gender_assigned",
                actor_user_id=None, actor_guild_id=adv.get("guild_id"),
                source="round160.backfill_race_gender",
                metadata={"adventurer_id": adv["id"],
                          "gender": set_ops["gender"]},
            )
        updated += 1

    return {"seen": seen, "updated": updated,
            "race_writes": race_writes, "gender_writes": gender_writes,
            "gender_hist": dict(gender_hist)}


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    load_dotenv()
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    try:
        out = await _run(cli[os.environ["DB_NAME"]],
                         dry_run=args.dry_run, limit=args.limit)
        print({"dry_run": args.dry_run, **out})
        return 0
    finally:
        cli.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
