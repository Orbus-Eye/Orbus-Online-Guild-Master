"""Phase 19.2 — dev-only seed script for tester's inventory.

Idempotent: grants 1 × weapon (Rusted Sword), 1 × armor (Torn Leather Vest),
1 × accessory (Novice Charm) — all Common, level_required=1, NOT bound,
NOT equipped — to the `tester@orbus.test` guild. Skips items already present.

Refuses to run unless `APP_ENV != "production"`.

Usage:
    cd /app/backend && python -m app.scripts.seed_tester_inventory
"""
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient


TESTER_EMAIL = "tester@orbus.test"
ITEM_SLUGS_OR_NAMES = [
    ("weapon", "Rusted Sword"),
    ("armor", "Torn Leather Vest"),
    ("accessory", "Novice Charm"),
]


def main() -> int:
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    app_env = (os.environ.get("APP_ENV") or "development").lower()
    if app_env == "production":
        print("REFUSED: APP_ENV=production. This seed is dev-only.", file=sys.stderr)
        return 2

    mongo_url = os.environ["MONGO_URL"]
    db_name = os.environ["DB_NAME"]
    client = MongoClient(mongo_url)
    try:
        db = client[db_name]
        user = db.users.find_one({"email": TESTER_EMAIL}, {"_id": 0, "id": 1})
        if not user:
            print(f"REFUSED: tester user '{TESTER_EMAIL}' not found.", file=sys.stderr)
            return 3
        guild = db.guilds.find_one({"owner_user_id": user["id"]}, {"_id": 0, "id": 1, "name": 1})
        if not guild:
            print(f"REFUSED: tester '{TESTER_EMAIL}' has no guild.", file=sys.stderr)
            return 4

        now_iso = datetime.now(timezone.utc).isoformat()
        granted: list[str] = []
        skipped: list[str] = []
        for slot, name in ITEM_SLUGS_OR_NAMES:
            item = db.items.find_one(
                {"name": name, "item_type": slot}, {"_id": 0, "id": 1, "name": 1}
            )
            if not item:
                print(f"WARN: item '{name}' ({slot}) not found in catalog — skipped.")
                continue
            existing = db.inventory_items.find_one(
                {
                    "guild_id": guild["id"],
                    "item_id": item["id"],
                    "is_bound": {"$ne": True},
                }
            )
            if existing:
                skipped.append(item["name"])
                continue
            db.inventory_items.insert_one({
                "id": str(uuid.uuid4()),
                "instance_id": str(uuid.uuid4()),
                "guild_id": guild["id"],
                "item_id": item["id"],
                "quantity": 1,
                "refinement_level": 0,
                "enchants": [],
                "affixes": [],
                "reroll_count": 0,
                "is_bound": False,
                "disenchanted_at": None,
                "acquired_at": now_iso,
                "source": "dev_seed_tester_inventory",
            })
            granted.append(item["name"])

        print(f"OK: guild='{guild['name']}' granted={granted} skipped(already_present)={skipped}")
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())
