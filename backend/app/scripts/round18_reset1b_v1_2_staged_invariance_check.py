"""
R18.Reset.1b.hotfix.v1_2 STAGED — Invariance Check (READ-ONLY).

Compares live DB counts against Step 1 BEFORE snapshot
(/app/memory/r18_reset1b_v1_2_staged_db_snapshot_before.json).

READ-ONLY: no writes, no mutations.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")


COLLECTIONS = [
    "guilds",
    "adventurers",
    "inventory_items",
    "items",
    "expeditions",
    "raids",
    "audit_log",
    "users",
]

BEFORE_SNAPSHOT_PATH = "/app/memory/r18_reset1b_v1_2_staged_db_snapshot_before.json"
AFTER_SNAPSHOT_PATH = "/app/memory/r18_reset1b_v1_2_staged_db_snapshot_after.json"


async def main() -> int:
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        print("[FATAL] MONGO_URL or DB_NAME missing from environment.", file=sys.stderr)
        return 2

    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    counts: dict[str, int] = {}
    for coll in COLLECTIONS:
        counts[coll] = await db[coll].count_documents({})

    # Gold total across all guilds
    gold_pipeline = [{"$group": {"_id": None, "total": {"$sum": "$gold"}}}]
    gold_total = 0
    async for doc in db.guilds.aggregate(gold_pipeline):
        gold_total = int(doc.get("total") or 0)
        break
    counts["gold_total"] = gold_total

    after = {
        "snapshot": "AFTER_STAGED_STEP4",
        "at": datetime.now(timezone.utc).isoformat(),
        "counts": counts,
    }
    Path(AFTER_SNAPSHOT_PATH).write_text(json.dumps(after, indent=2))

    if not Path(BEFORE_SNAPSHOT_PATH).exists():
        print(f"[FATAL] BEFORE snapshot not found: {BEFORE_SNAPSHOT_PATH}", file=sys.stderr)
        return 3

    before = json.loads(Path(BEFORE_SNAPSHOT_PATH).read_text())
    before_counts = before.get("counts") or {}

    print("=" * 72)
    print("R18.Reset.1b.hotfix.v1_2 — Step 4 Invariance Check")
    print("=" * 72)
    print(f"BEFORE snapshot: {BEFORE_SNAPSHOT_PATH} (at={before.get('at')})")
    print(f"AFTER  snapshot: {AFTER_SNAPSHOT_PATH} (at={after['at']})")
    print("-" * 72)
    print(f"{'collection':<28}{'BEFORE':>12}{'AFTER':>12}{'DELTA':>12}  {'STATUS':>8}")
    print("-" * 72)

    total_delta_abs = 0
    fails: list[str] = []
    for key in list(before_counts.keys()):
        b = int(before_counts.get(key) or 0)
        a = int(counts.get(key) or 0)
        d = a - b
        total_delta_abs += abs(d)
        status = "OK" if d == 0 else "FAIL"
        if d != 0:
            fails.append(f"{key}: before={b} after={a} delta={d}")
        print(f"{key:<28}{b:>12}{a:>12}{d:>+12}  {status:>8}")

    print("-" * 72)
    if not fails:
        print("RESULT: PASS — DB invariance mantained (delta=0 across all tracked collections + gold_total).")
        return 0
    else:
        print("RESULT: FAIL — Invariance violated:")
        for f in fails:
            print(f"  - {f}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
