"""ROUND 16.3 Phase 7A — PvP Continental recovery CLI.

Read-only diagnostic + optional apply for stuck battles.

Usage:
    python -m app.scripts.recover_stuck_pvp_battles [--dry-run|--apply] [--limit N]
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient


async def _run(*, dry_run: bool, limit: int | None) -> dict:
    load_dotenv()
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    try:
        db = client[os.environ["DB_NAME"]]
        now_iso = datetime.now(timezone.utc).isoformat()
        q = {
            "$or": [
                {"status": "pending_response",
                 "response_deadline": {"$lte": now_iso}},
                {"status": "resolving",
                 "resolves_at": {"$lte": now_iso}},
            ],
        }
        total = await db.pvp_battles.count_documents(q)
        cursor = db.pvp_battles.find(q, {"_id": 0, "id": 1, "status": 1})
        if limit:
            cursor = cursor.limit(limit)
        battles = await cursor.to_list(limit or 500)
        if dry_run:
            return {"dry_run": True, "total_stuck": total,
                     "would_resolve": len(battles),
                     "sample_ids": [b["id"] for b in battles[:5]]}
        from app.pvp_continental.resolver import resolve_battle
        ok = 0
        fail = 0
        errors: list[dict] = []
        for b in battles:
            try:
                r = await resolve_battle(
                    db, b["id"], reason="cli_recovery",
                )
                if r.get("ok"):
                    ok += 1
                else:
                    fail += 1
                    errors.append({"id": b["id"], "reason": r.get("reason")})
            except Exception as exc:  # noqa: BLE001
                fail += 1
                errors.append({"id": b["id"], "error": str(exc)})
        return {"dry_run": False, "total_stuck": total,
                 "resolved": ok, "failed": fail,
                 "errors": errors[:5]}
    finally:
        client.close()


def main() -> int:
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true", default=True)
    g.add_argument("--apply", action="store_true")
    p.add_argument("--limit", type=int, default=None)
    args = p.parse_args()
    dry = not args.apply
    out = asyncio.run(_run(dry_run=dry, limit=args.limit))
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
