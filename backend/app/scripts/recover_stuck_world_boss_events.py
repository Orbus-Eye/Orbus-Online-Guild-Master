"""ROUND 16.3 Phase 1 — CLI to recover stuck World Boss events.

Same UX pattern as `recover_stuck_raids.py` (R16.1.1).

Usage:
  python -m app.scripts.recover_stuck_world_boss_events           # dry-run
  python -m app.scripts.recover_stuck_world_boss_events --apply
  python -m app.scripts.recover_stuck_world_boss_events --apply --event-id X
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient

from app.world_boss import resolve_stuck_world_boss_event


async def _find_all_stuck(db) -> list[dict]:
    now_iso = datetime.now(timezone.utc).isoformat()
    cur = db.world_boss_events.find(
        {"status": {"$in": ["active", "scheduled"]},
         "ends_at": {"$lte": now_iso}},
        {"_id": 0},
    ).sort("ends_at", 1)
    return await cur.to_list(500)


async def main():
    parser = argparse.ArgumentParser(
        description="Recover World Boss events stuck past ends_at (idempotent).",
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", dest="dry_run_explicit", action="store_true")
    parser.add_argument("--event-id", default=None)
    args = parser.parse_args()
    dry_run = not args.apply

    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        print("ERROR: MONGO_URL or DB_NAME missing.", file=sys.stderr)
        sys.exit(2)
    cli = AsyncIOMotorClient(mongo_url)
    db = cli[db_name]

    if args.event_id:
        rows = await db.world_boss_events.find(
            {"id": args.event_id}, {"_id": 0}
        ).to_list(1)
        if not rows:
            print(f"ERROR: event {args.event_id} not found.", file=sys.stderr)
            sys.exit(3)
    else:
        rows = await _find_all_stuck(db)

    if not rows:
        print("No stuck world boss events found.")
        return

    mode = "DRY-RUN" if dry_run else "APPLY"
    print(f"=== World Boss Recovery [{mode}] — {len(rows)} candidate(s) ===")
    print(f"{'event_id':<12} {'boss_slug':<28} {'hp':>10} {'outcome':<10} action")
    print("-" * 80)
    totals = {"resolved": 0, "skipped": 0, "previewed": 0, "error": 0}
    for ev in rows:
        eid = ev.get("id", "?")
        try:
            out = await resolve_stuck_world_boss_event(
                eid, dry_run=dry_run, reason="cli_recover_stuck_wb",
            )
            action = out.get("action", "?")
            outcome = out.get("outcome") or out.get("proposed_outcome") or "-"
            hp = ev.get("current_hp", "?")
            totals[action] = totals.get(action, 0) + 1
            print(f"{eid[:10]+'..':<12} {ev.get('boss_slug','?'):<28} "
                  f"{hp:>10} {outcome:<10} {action}")
        except Exception as exc:
            totals["error"] += 1
            print(f"{eid[:10]+'..':<12} ERROR: {exc}")
    print("-" * 80)
    print(f"Totals: {totals}")
    if dry_run:
        print("\n(DRY-RUN — re-run with --apply to commit.)")


if __name__ == "__main__":
    asyncio.run(main())
