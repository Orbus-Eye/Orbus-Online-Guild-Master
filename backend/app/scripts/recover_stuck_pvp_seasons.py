"""ROUND 16.3 Phase 7B — Recovery CLI for stuck PvP seasons.

Read-only diagnostic + optional apply for seasons that have been in
`active` status past their `ends_at` by more than 24h. Idempotent apply:
calls `finalize_season()` which is safe to re-run.

Usage:
    python -m app.scripts.recover_stuck_pvp_seasons [--dry-run|--apply] [--limit N]
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient


async def _run(*, dry_run: bool, limit: int | None) -> dict:
    load_dotenv()
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    try:
        db = client[os.environ["DB_NAME"]]
        now = datetime.now(timezone.utc)
        stuck_cutoff = (now - timedelta(hours=24)).isoformat()
        q = {"status": "active", "ends_at": {"$lte": stuck_cutoff}}
        total = await db.pvp_seasons.count_documents(q)
        cursor = db.pvp_seasons.find(q, {"_id": 0, "id": 1,
                                          "season_number": 1, "ends_at": 1})
        if limit:
            cursor = cursor.limit(limit)
        stuck = await cursor.to_list(limit or 500)
        if dry_run:
            return {"dry_run": True, "total_stuck": total,
                    "sampled": len(stuck),
                    "stuck": stuck}
        # Apply: finalize each stuck season (idempotent).
        from app.pvp_season.services import finalize_season
        results = []
        for s in stuck:
            r = await finalize_season(db, s["id"])
            results.append({"season_id": s["id"],
                            "season_number": s["season_number"],
                            "result": r})
        return {"dry_run": False, "total_stuck": total,
                "processed": len(results), "results": results}
    finally:
        client.close()


def main() -> int:
    p = argparse.ArgumentParser(
        description="Recover stuck PvP seasons "
                    "(status=active with ends_at past by ≥24h).",
    )
    grp = p.add_mutually_exclusive_group(required=True)
    grp.add_argument("--dry-run", action="store_true",
                     help="Report only (no writes).")
    grp.add_argument("--apply", action="store_true",
                     help="Finalize each stuck season (idempotent).")
    p.add_argument("--limit", type=int, default=None,
                   help="Sample cap.")
    args = p.parse_args()
    result = asyncio.run(_run(dry_run=args.dry_run, limit=args.limit))
    import json
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
