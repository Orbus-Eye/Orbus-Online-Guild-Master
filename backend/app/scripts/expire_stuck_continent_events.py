"""ROUND 16.3 Phase 3 — Expire stuck continent events recovery script.

Trova continent_event_instances con status="active" e ends_at <= now,
li flippa a "expired" idempotentemente (best-effort audit emit).

Usage:
    python -m app.scripts.expire_stuck_continent_events --dry-run
    python -m app.scripts.expire_stuck_continent_events --apply
"""
from __future__ import annotations

import argparse
import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger("orbus.dev.expire_events")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")


async def _run(apply: bool) -> dict:
    from app.core.database import db
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    q = {"status": "active", "ends_at": {"$lte": now_iso}}
    stuck = await db.continent_event_instances.find(q, {"_id": 0}).to_list(200)
    logger.info("found %d stuck events", len(stuck))
    if not apply:
        return {"status": "dry_run", "found": len(stuck),
                "ids": [d.get("id") for d in stuck]}
    flipped_count = 0
    for d in stuck:
        eid = d["id"]
        r = await db.continent_event_instances.find_one_and_update(
            {"id": eid, "status": "active"},
            {"$set": {"status": "expired", "expired_at": now_iso,
                      "recovery_source": "script"}},
        )
        if r:
            flipped_count += 1
            try:
                from app.audit.log import write_audit
                await write_audit(
                    db, event_type="CONTINENT_EVENT_EXPIRED",
                    actor_user_id=None, actor_guild_id=None,
                    source="recovery_script", related_entity_id=eid,
                    metadata={"continent_slug": d.get("continent_slug"),
                             "event_slug": d.get("event_slug"),
                             "recovery": True},
                )
            except Exception as exc:
                logger.debug("audit emit skipped: %s", exc)
    return {"status": "applied", "found": len(stuck), "flipped": flipped_count}


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
