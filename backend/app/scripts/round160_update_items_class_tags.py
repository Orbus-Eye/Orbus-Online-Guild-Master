"""Round 16.0 — Update items.class_tags for deprecated → base+spec.

For every item whose `class_tags` (or `recommended_classes`) contains a
deprecated class slug (berserker / assassin / necromancer):
  * ADD the base successor slug (warrior / rogue / mage) to `class_tags`
    and `recommended_classes` if missing.
  * ADD the specialization slug (berserker_spec / assassin_spec /
    necromancer_spec) to a new optional field `specialization_unlocks`.
  * PRESERVE the legacy tag (no removal) so the audit chain is reversible.

Idempotency:
  Skip items where both the base slug AND the specialization_unlocks
  entry are already present.

Audit:
  One `item_class_tags_extended` event per item touched.

Vincoli:
  * NO removal of any existing tag.
  * NO modifica a item_type, rarity, level, stats, drop_table.

Usage:
    python -m app.scripts.round160_update_items_class_tags [--dry-run]
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


MAPPING: dict[str, dict[str, str]] = {
    "berserker": {"base": "warrior", "spec": "berserker_spec"},
    "assassin": {"base": "rogue", "spec": "assassin_spec"},
    "necromancer": {"base": "mage", "spec": "necromancer_spec"},
}


def _compute_update(item: dict) -> tuple[dict, list[str]]:
    """Return (set_ops, mutations_summary). mutations_summary empty == no-op."""
    class_tags = list(item.get("class_tags") or [])
    recommended = list(item.get("recommended_classes") or [])
    spec_unlocks = list(item.get("specialization_unlocks") or [])
    mutations: list[str] = []

    for deprecated, target in MAPPING.items():
        if deprecated in class_tags or deprecated in recommended:
            if target["base"] not in class_tags:
                class_tags.append(target["base"])
                mutations.append(f"+class_tag:{target['base']}")
            if target["base"] not in recommended:
                recommended.append(target["base"])
                mutations.append(f"+recommended:{target['base']}")
            if target["spec"] not in spec_unlocks:
                spec_unlocks.append(target["spec"])
                mutations.append(f"+spec_unlock:{target['spec']}")
    if not mutations:
        return {}, []
    return {
        "class_tags": class_tags,
        "recommended_classes": recommended,
        "specialization_unlocks": spec_unlocks,
        "updated_at": datetime.now(timezone.utc),
    }, mutations


async def _run(db, *, dry_run: bool) -> dict[str, int]:
    updated = 0
    skipped = 0
    seen = 0

    cursor = db.items.find(
        {"$or": [
            {"class_tags": {"$in": list(MAPPING.keys())}},
            {"recommended_classes": {"$in": list(MAPPING.keys())}},
        ]},
        {"_id": 0, "id": 1, "slug": 1, "class_tags": 1,
         "recommended_classes": 1, "specialization_unlocks": 1},
    )
    async for item in cursor:
        seen += 1
        set_ops, mutations = _compute_update(item)
        if not mutations:
            skipped += 1
            continue
        if dry_run:
            updated += 1
            continue
        await db.items.update_one(
            {"id": item.get("id")} if item.get("id") else {"slug": item.get("slug")},
            {"$set": set_ops},
        )
        await write_audit(
            db, event_type="item_class_tags_extended",
            actor_user_id=None, actor_guild_id=None,
            source="round160.update_items_class_tags",
            metadata={
                "item_id": item.get("id"),
                "item_slug": item.get("slug"),
                "mutations": mutations,
            },
        )
        updated += 1
    return {"seen": seen, "updated": updated, "skipped": skipped}


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
