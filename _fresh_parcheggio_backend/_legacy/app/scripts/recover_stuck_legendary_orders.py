"""ROUND 16.3 Phase 5A — Legendary Forge recovery CLI.

Idempotent CAS-safe: resolves crafting orders stuck in `in_progress`
past their `completes_at` (with optional grace window). Uses the same
`_resolve_order` used by on-visit fallback.

Usage:
    python -m app.scripts.recover_stuck_legendary_orders --dry-run
    python -m app.scripts.recover_stuck_legendary_orders --apply
    python -m app.scripts.recover_stuck_legendary_orders --guild-id X --apply
"""
from __future__ import annotations
import argparse
import asyncio
import logging
from datetime import datetime, timezone


async def _run(dry_run: bool, guild_id: str | None, grace_min: int) -> dict:
    from app.core.database import db
    from app.legendary_forge import _resolve_order
    now = datetime.now(timezone.utc).isoformat()
    q = {"status": "in_progress", "completes_at": {"$lte": now}}
    if guild_id:
        q["guild_id"] = guild_id
    stuck = await db.legendary_forge_crafting_orders.find(
        q, {"_id": 0}).to_list(500)
    if dry_run:
        return {"scanned": len(stuck), "resolved": 0, "dry_run": True}
    resolved = 0
    for o in stuck:
        try:
            await _resolve_order(o)
            resolved += 1
        except Exception as exc:
            logging.warning("recover %s: %s", o.get("id"), exc)
    return {"scanned": len(stuck), "resolved": resolved, "dry_run": False}


def main() -> None:
    p = argparse.ArgumentParser()
    grp = p.add_mutually_exclusive_group(required=True)
    grp.add_argument("--dry-run", action="store_true")
    grp.add_argument("--apply", action="store_true")
    p.add_argument("--guild-id", default=None)
    p.add_argument("--grace-min", type=int, default=0)
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO)
    res = asyncio.run(_run(dry_run=args.dry_run, guild_id=args.guild_id,
                              grace_min=args.grace_min))
    print(res)


if __name__ == "__main__":
    main()
