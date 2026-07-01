"""ROUND 6A.2b — Seed ≥N adventurers for tester@orbus.test.

Idempotent: counts current available adventurers and only tops up the
difference. Uses the standard random generator (no special rarity boost,
no power bump) so the seed respects production distribution.

Refuses APP_ENV=production.
"""
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

TESTER_EMAIL = "tester@orbus.test"
TARGET_AVAILABLE = 22  # 20 for raid_20 + 2 headroom for spedizioni concorrenti


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
    guild = await db.guilds.find_one({"owner_user_id": user["id"]}, {"_id": 0, "id": 1, "name": 1})
    if not guild:
        print("ERROR: tester has no guild", file=sys.stderr)
        return 1

    current_available = await db.adventurers.count_documents({
        "guild_id": guild["id"], "is_available": True,
    })
    if current_available >= TARGET_AVAILABLE:
        print(f"OK: guild={guild['name']!r} already has {current_available} available (target {TARGET_AVAILABLE}). No-op.")
        return 0

    needed = TARGET_AVAILABLE - current_available
    print(f"guild={guild['name']!r} available={current_available} target={TARGET_AVAILABLE} → generating {needed}")

    # Lazy import to avoid circular load at module-import time.
    from app.adventurers.generator import (
        generate_candidate,
        filter_safe_class_pool,
        filter_safe_trait_pool,
    )

    class_pool = await filter_safe_class_pool(db)
    # Merge legacy adventurer_traits with new traits collection (same
    # behavior as recruitment._roll_and_persist_offer).
    primary = await filter_safe_trait_pool(db)
    legacy = await db.adventurer_traits.find(
        {"is_active": True, "is_test": {"$ne": True}}, {"_id": 0}
    ).to_list(300)
    trait_pool = (primary or []) + [
        t for t in (legacy or [])
        if not (t.get("name", "").startswith("Test")
                or t.get("slug", "").startswith("test"))
    ]

    import random
    rng = random.Random()
    rng.seed()  # production-like randomness

    import uuid
    from datetime import datetime, timezone
    now_iso = datetime.now(timezone.utc).isoformat()

    inserted = 0
    rarities = []
    for _ in range(needed):
        cand = await generate_candidate(
            db,
            guild_id=guild["id"],
            rng=rng,
            class_pool=class_pool,
            trait_pool=trait_pool,
            audit=True,
            audit_source="dev_seed_tester_adventurers",
        )
        adv_doc = {
            "id": str(uuid.uuid4()),
            "guild_id": guild["id"],
            "name": cand["name"],
            "adventurer_class_id": cand["adventurer_class_id"],
            "class_name": cand["class_name"],
            "class_role": cand["class_role"],
            "rarity": cand["rarity"],
            "level": cand["level"],
            "experience": cand["experience"],
            "strength": cand["strength"],
            "agility": cand["agility"],
            "intellect": cand["intellect"],
            "endurance": cand["endurance"],
            "faith": cand["faith"],
            "stamina": cand["stamina"],
            "morale": cand["morale"],
            "traits": cand.get("traits", []),
            "is_available": True,
            "is_starter": False,
            "rename_count": 0,
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        await db.adventurers.insert_one(adv_doc)
        inserted += 1
        rarities.append(cand["rarity"])

    final = await db.adventurers.count_documents({
        "guild_id": guild["id"], "is_available": True,
    })
    from collections import Counter
    dist = Counter(rarities)
    print(f"OK: inserted={inserted}, final_available={final}, rarities={dict(dist)}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
