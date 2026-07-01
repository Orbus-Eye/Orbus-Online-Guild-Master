"""Round 16.0 — Migrate adventurers from deprecated classes.

For every adventurer with class in {berserker, assassin, necromancer}
(matched on `class_slug` lowercase OR `class_name` capitalized):
  * set `class_slug = successor_slug` (warrior / rogue / mage)
  * set `class_name = successor_capitalized` (Warrior / Rogue / Mage)
  * set `specialization_slug = successor_specialization_slug` (berserker_spec, …)
  * set `specialization_applied_at = utcnow`
  * preserve all other fields including the legacy `specialization` dict
    (training/respec snapshot from R6C) — never overwritten.

Idempotency:
  Filter is `{class_slug ∈ deprecated} OR {class_name ∈ deprecated names}`
  AND `specialization_slug` does NOT already match a migrated value.
  Rerun on a clean dataset yields `migrated=0`.

Audit:
  One `adventurer_class_migrated` row per record changed. No row for
  records already migrated.

Vincoli:
  * NO hard delete.
  * NO modifica al campo `specialization` (training/respec).
  * Batch da 500 con cursor per non saturare la memoria.

Usage:
    python -m app.scripts.round160_migrate_adventurers_deprecated_classes [--dry-run] [--limit N]
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from app.audit.log import write_audit


# Migration mapping — keep in sync with `round160_seed_classes_v2.py`.
MAPPING: dict[str, dict[str, str]] = {
    "berserker": {"successor_slug": "warrior",
                  "successor_name": "Warrior",
                  "successor_specialization_slug": "berserker_spec"},
    "assassin": {"successor_slug": "rogue",
                 "successor_name": "Rogue",
                 "successor_specialization_slug": "assassin_spec"},
    "necromancer": {"successor_slug": "mage",
                    "successor_name": "Mage",
                    "successor_specialization_slug": "necromancer_spec"},
}

DEPRECATED_SLUGS = list(MAPPING.keys())
DEPRECATED_NAMES = [s.capitalize() for s in DEPRECATED_SLUGS]

BATCH_SIZE = 500


def _resolve_target(doc: dict) -> dict[str, str] | None:
    slug = (doc.get("class_slug") or "").lower()
    if slug in MAPPING:
        return MAPPING[slug]
    name = (doc.get("class_name") or "").lower()
    if name in MAPPING:
        return MAPPING[name]
    return None


async def _migrate(db, *, dry_run: bool, limit: int | None) -> dict[str, int]:
    now = datetime.now(timezone.utc)
    migrated = 0
    skipped = 0
    seen = 0

    query = {
        "$or": [
            {"class_slug": {"$in": DEPRECATED_SLUGS}},
            {"class_name": {"$in": DEPRECATED_NAMES}},
        ],
    }
    cursor = db.adventurers.find(
        query,
        {"_id": 0, "id": 1, "guild_id": 1, "class_slug": 1, "class_name": 1,
         "specialization_slug": 1},
        batch_size=BATCH_SIZE,
    )

    async for adv in cursor:
        seen += 1
        if limit is not None and migrated >= limit:
            break
        target = _resolve_target(adv)
        if not target:
            skipped += 1
            continue
        # Idempotency: skip if specialization_slug already set to the
        # migration target.
        if adv.get("specialization_slug") == target["successor_specialization_slug"] \
                and (adv.get("class_slug") or "").lower() == target["successor_slug"]:
            skipped += 1
            continue
        if dry_run:
            migrated += 1
            continue
        before = {
            "class_slug": adv.get("class_slug"),
            "class_name": adv.get("class_name"),
            "specialization_slug": adv.get("specialization_slug"),
        }
        update_doc = {
            "class_slug": target["successor_slug"],
            "class_name": target["successor_name"],
            "specialization_slug": target["successor_specialization_slug"],
            "specialization_applied_at": now,
            "updated_at": now,
        }
        await db.adventurers.update_one(
            {"id": adv["id"]},
            {"$set": update_doc},
        )
        await write_audit(
            db, event_type="adventurer_class_migrated",
            actor_user_id=None, actor_guild_id=adv.get("guild_id"),
            source="round160.migrate_adventurers",
            metadata={
                "adventurer_id": adv["id"],
                "before": before,
                "after": {
                    "class_slug": target["successor_slug"],
                    "class_name": target["successor_name"],
                    "specialization_slug":
                        target["successor_specialization_slug"],
                },
            },
        )
        migrated += 1

    return {"seen": seen, "migrated": migrated, "skipped": skipped}


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit number of writes (debug).")
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
        out = await _migrate(db, dry_run=args.dry_run, limit=args.limit)
        print({"dry_run": args.dry_run, **out})
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
