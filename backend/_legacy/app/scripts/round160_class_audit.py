"""Round 16.0 — Class Audit (READ-ONLY).

Prints a snapshot of the current class catalog state, including:
  * count of active/deprecated classes
  * distribution of adventurers per class_name
  * impact metrics for deprecated classes (berserker / assassin / necromancer)
  * presence of new fields (class_slug, specialization_slug, race_slug, gender)

This script is read-only: it never writes to the database. It is safe to
run in production for diagnostics.

Usage:
    python -m app.scripts.round160_class_audit
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Any

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient


DEPRECATE_SLUGS = {"berserker", "assassin", "necromancer"}
DEPRECATE_NAMES = {"Berserker", "Assassin", "Necromancer"}
BASE_CLASS_SLUGS_FINAL = {
    "warrior", "rogue", "mage", "priest", "ranger",
    "paladin", "druid", "monk", "bard", "warlock",
}


async def _audit(db) -> dict[str, Any]:
    out: dict[str, Any] = {}

    # 1. Active class catalog
    catalog = await db.adventurer_classes.find(
        {"is_active": True}, {"_id": 0}
    ).to_list(50)
    out["active_classes"] = [
        {
            "slug": c.get("slug"),
            "display_name_it": c.get("display_name_it"),
            "primary_stat": c.get("primary_stat"),
            "role": c.get("role"),
        }
        for c in catalog
    ]
    out["active_classes_count"] = len(catalog)

    # 2. Adventurers per class_name
    pipe_name = [
        {"$group": {"_id": "$class_name", "c": {"$sum": 1}}},
        {"$sort": {"c": -1}},
    ]
    rows = await db.adventurers.aggregate(pipe_name).to_list(50)
    out["adventurers_per_class_name"] = {r["_id"]: r["c"] for r in rows}

    # 3. Impact metrics for deprecated classes
    impact = {}
    for slug in DEPRECATE_SLUGS:
        name = slug.capitalize()
        impact[slug] = {
            "adv_by_class_slug": await db.adventurers.count_documents(
                {"class_slug": slug}
            ),
            "adv_by_class_name": await db.adventurers.count_documents(
                {"class_name": name}
            ),
            "items_class_tags": await db.items.count_documents(
                {"class_tags": slug}
            ),
            "items_recommended": await db.items.count_documents(
                {"recommended_classes": slug}
            ),
            "achievements_name_match": await db.achievements_catalog.count_documents(
                {"name_it": {"$regex": slug, "$options": "i"}}
            ),
            "achievements_desc_match": await db.achievements_catalog.count_documents(
                {"description_it": {"$regex": slug, "$options": "i"}}
            ),
        }
    out["deprecated_impact"] = impact

    # 4. New fields presence
    total_adv = await db.adventurers.count_documents({})
    out["new_fields_presence"] = {
        "total_adventurers": total_adv,
        "with_class_slug": await db.adventurers.count_documents(
            {"class_slug": {"$ne": None, "$exists": True}}
        ),
        "with_specialization_slug": await db.adventurers.count_documents(
            {"specialization_slug": {"$ne": None, "$exists": True}}
        ),
        "with_training_specialization": await db.adventurers.count_documents(
            {"specialization": {"$ne": None}}
        ),
        "with_race_slug": await db.adventurers.count_documents(
            {"race_slug": {"$ne": None, "$exists": True}}
        ),
        "with_gender": await db.adventurers.count_documents(
            {"gender": {"$ne": None, "$exists": True}}
        ),
    }

    # 5. class_specializations existence
    if "class_specializations" in await db.list_collection_names():
        out["class_specializations_count"] = await db.class_specializations.count_documents({})
    else:
        out["class_specializations_count"] = "collection_missing"

    # 6. class_halls existence
    if "class_halls" in await db.list_collection_names():
        out["class_halls_count"] = await db.class_halls.count_documents({})
    else:
        out["class_halls_count"] = "collection_missing"

    # 7. Migration readiness flag
    needs_migration = sum(
        impact[s]["adv_by_class_slug"] + impact[s]["adv_by_class_name"]
        for s in DEPRECATE_SLUGS
    )
    out["needs_migration_adventurers_count"] = needs_migration
    out["migration_already_done"] = needs_migration == 0 and out[
        "class_specializations_count"
    ] not in ("collection_missing", 0)

    return out


async def main() -> int:
    load_dotenv()
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        print("ERROR: MONGO_URL / DB_NAME not configured", file=sys.stderr)
        return 2
    client = AsyncIOMotorClient(mongo_url)
    try:
        db = client[db_name]
        report = await _audit(db)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
