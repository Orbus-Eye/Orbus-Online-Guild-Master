"""ROUND 16.3 Phase 4 — Recover stuck resource gathering missions.

Same pattern as raid/world_boss/continent_event recovery scripts.
Idempotent CAS resolution, no hard delete.

Usage:
    python -m app.scripts.recover_stuck_resource_missions --dry-run
    python -m app.scripts.recover_stuck_resource_missions --apply
"""
from __future__ import annotations

import argparse
import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger("orbus.dev.recover_resources")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")


async def _run(apply: bool) -> dict:
    from app.core.database import db
    from app.resources import _resolve_mission
    now_iso = datetime.now(timezone.utc).isoformat()
    q = {"status": "in_progress", "completes_at": {"$lte": now_iso}}
    stuck = await db.resource_gathering_missions.find(q, {"_id": 0}).to_list(200)
    logger.info("found %d stuck resource missions", len(stuck))
    if not apply:
        return {"status": "dry_run", "found": len(stuck),
                "ids": [d.get("id") for d in stuck]}
    resolved = 0
    for m in stuck:
        try:
            await _resolve_mission(m)
            resolved += 1
        except Exception as exc:
            logger.warning("resolve failed for %s: %s", m.get("id"), exc)
    # Mark recovered flag for traceability
    ids = [m["id"] for m in stuck]
    if ids:
        await db.resource_gathering_missions.update_many(
            {"id": {"$in": ids}},
            {"$set": {"recovered": True, "recovery_source": "script"}},
        )
    return {"status": "applied", "found": len(stuck), "resolved": resolved}


def main():
    p = argparse.ArgumentParser()
    grp = p.add_mutually_exclusive_group(required=True)
    grp.add_argument("--dry-run", action="store_true")
    grp.add_argument("--apply", action="store_true")
    args = p.parse_args()
    result = asyncio.run(_run(apply=args.apply))
    logger.info("result: %s", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
