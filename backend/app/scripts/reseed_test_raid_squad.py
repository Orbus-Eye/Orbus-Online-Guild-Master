"""ROUND 6A.2c — Reseed/update the 'Test Raid 6A2b' raid_20 squad with 20
fresh, currently-available adventurer ids for tester@orbus.test.

Pre-condition: the tester guild must have ≥20 available adventurers
(use seed_tester_adventurers.py first if needed).

Idempotent semantics:
- If the squad does not exist → create it with 20 fresh ids + 5+5+5+5 raid_parties.
- If the squad exists and has missing_adventurer_ids > 0 → replace its ids
  with 20 fresh ones and reset raid_parties.
- If the squad exists and member_count == 20 (no missing) → no-op.

Refuses APP_ENV=production.
"""
import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

TESTER_EMAIL = "tester@orbus.test"
SQUAD_NAME = "Test Raid 6A2b"
SQUAD_TYPE = "raid_20"
SIZE = 20
PARTY_SIZE = 5


async def run() -> int:
    if os.environ.get("APP_ENV") == "production":
        print("ERROR: refuses to run with APP_ENV=production", file=sys.stderr)
        return 2

    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    user = await db.users.find_one({"email": TESTER_EMAIL}, {"_id": 0, "id": 1})
    if not user:
        print(f"ERROR: tester user not found: {TESTER_EMAIL}", file=sys.stderr)
        return 1
    guild = await db.guilds.find_one(
        {"owner_user_id": user["id"]}, {"_id": 0, "id": 1, "name": 1}
    )
    if not guild:
        print("ERROR: tester has no guild", file=sys.stderr)
        return 1

    advs = await db.adventurers.find(
        {"guild_id": guild["id"], "is_available": True},
        {"_id": 0, "id": 1},
    ).limit(SIZE).to_list(SIZE)
    if len(advs) < SIZE:
        print(
            f"ERROR: need {SIZE} available adventurers, have {len(advs)}. "
            "Run seed_tester_adventurers.py first.",
            file=sys.stderr,
        )
        return 1
    fresh_ids = [a["id"] for a in advs]

    raid_parties = {
        "party_1": fresh_ids[0:5],
        "party_2": fresh_ids[5:10],
        "party_3": fresh_ids[10:15],
        "party_4": fresh_ids[15:20],
    }

    now_iso = datetime.now(timezone.utc).isoformat()
    existing = await db.squads.find_one(
        {"guild_id": guild["id"], "name": SQUAD_NAME, "is_archived": False},
        {"_id": 0},
    )

    if existing:
        # Check if it's already healthy: all 20 ids must still be available.
        current_ids = set(existing.get("adventurer_ids", []))
        if len(current_ids) == SIZE:
            present = await db.adventurers.count_documents({
                "guild_id": guild["id"],
                "id": {"$in": list(current_ids)},
                "is_available": True,
            })
            if present == SIZE:
                print(f"OK: squad {SQUAD_NAME!r} already healthy (20/20, no missing). No-op.")
                return 0

        await db.squads.update_one(
            {"id": existing["id"]},
            {"$set": {
                "adventurer_ids": fresh_ids,
                "raid_parties": raid_parties,
                "updated_at": now_iso,
            }},
        )
        print(
            f"OK: updated existing squad {SQUAD_NAME!r} (id={existing['id']}) "
            f"with 20 fresh adventurer ids."
        )
        return 0

    doc = {
        "id": str(uuid.uuid4()),
        "owner_user_id": user["id"],
        "guild_id": guild["id"],
        "name": SQUAD_NAME,
        "squad_type": SQUAD_TYPE,
        "adventurer_ids": fresh_ids,
        "raid_parties": raid_parties,
        "is_archived": False,
        "created_at": now_iso,
        "updated_at": now_iso,
    }
    await db.squads.insert_one(doc)
    print(f"OK: created squad {SQUAD_NAME!r} (id={doc['id']}) with 20 fresh adventurer ids.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
