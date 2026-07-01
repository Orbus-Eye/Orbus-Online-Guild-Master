"""ROUND 16.1.1 Hotfix — CLI script to recover stuck raids.

Usage:
  python -m app.scripts.recover_stuck_raids                     # dry-run (default)
  python -m app.scripts.recover_stuck_raids --dry-run           # dry-run explicit
  python -m app.scripts.recover_stuck_raids --apply             # actually apply
  python -m app.scripts.recover_stuck_raids --apply --raid-id X # single raid

Output (dry-run):
  [raid_id | guild_id | members_blocked | proposed_outcome | reward_dup_risk]

Output (apply):
  [raid_id | resolved/skipped/error]
  Totals: resolved=N skipped=M error=K
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient

from app.raids.recovery import resolve_stuck_raid


async def _find_all_stuck(db) -> list[dict]:
    now_iso = datetime.now(timezone.utc).isoformat()
    cur = db.raids.find(
        {"status": "in_progress", "ends_at": {"$lte": now_iso}},
        {"_id": 0},
    ).sort("ends_at", 1)
    return await cur.to_list(1000)


async def _check_dup_risk(db, raid_id: str) -> str:
    """Heuristic: if `audit_log` already has a `raid_completed` or
    `raid_recovered` row for this raid_id, flag dup risk.
    """
    n = await db.audit_log.count_documents({
        "related_entity_id": raid_id,
        "event_type": {"$in": ["raid_completed", "raid_recovered"]},
    })
    return "YES" if n > 0 else "no"


async def main():
    parser = argparse.ArgumentParser(
        description="Recover raids stuck `in_progress` after `ends_at` (idempotent).",
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Actually apply the recovery (default: dry-run).",
    )
    parser.add_argument(
        "--dry-run", dest="dry_run_explicit", action="store_true",
        help="Explicit dry-run flag (same as default).",
    )
    parser.add_argument(
        "--raid-id", default=None,
        help="Operate on a single raid_id (otherwise all stuck raids).",
    )
    args = parser.parse_args()

    apply_mode = args.apply
    dry_run = not apply_mode

    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        print("ERROR: MONGO_URL or DB_NAME missing from env.", file=sys.stderr)
        sys.exit(2)
    cli = AsyncIOMotorClient(mongo_url)
    db = cli[db_name]

    if args.raid_id:
        raids = await db.raids.find({"id": args.raid_id}, {"_id": 0}).to_list(1)
        if not raids:
            print(f"ERROR: raid {args.raid_id} not found.", file=sys.stderr)
            sys.exit(3)
    else:
        raids = await _find_all_stuck(db)

    if not raids:
        print("No stuck raids found. Nothing to do.")
        return

    mode_label = "DRY-RUN" if dry_run else "APPLY"
    print(f"=== Raid Recovery [{mode_label}] — {len(raids)} candidate(s) ===")
    print(f"{'raid_id':<10} {'guild_id':<10} {'members':>8} "
          f"{'outcome':<10} {'dup_risk':<10} action")
    print("-" * 80)

    totals = {"resolved": 0, "skipped": 0, "previewed": 0, "error": 0}
    for raid in raids:
        rid = raid.get("id", "?")
        gid = raid.get("guild_id", "?")
        dup = await _check_dup_risk(db, rid)
        try:
            out = await resolve_stuck_raid(
                db, rid, dry_run=dry_run,
                reason="cli_recover_stuck_raids",
            )
            action = out.get("action", "?")
            outcome = out.get("proposed_outcome") or out.get("outcome") or "-"
            members = out.get("members_blocked") or out.get("members_released") or 0
            totals[action] = totals.get(action, 0) + 1
            print(f"{rid[:8]+'..':<10} {gid[:8]+'..':<10} {members:>8} "
                  f"{outcome:<10} {dup:<10} {action}")
        except Exception as exc:
            totals["error"] += 1
            print(f"{rid[:8]+'..':<10} {gid[:8]+'..':<10} "
                  f"{'?':>8} {'?':<10} {dup:<10} ERROR: {exc}")

    print("-" * 80)
    print(f"Totals: {totals}")
    if dry_run:
        print("\n(DRY-RUN — nothing was written. Re-run with --apply to commit.)")


if __name__ == "__main__":
    asyncio.run(main())
