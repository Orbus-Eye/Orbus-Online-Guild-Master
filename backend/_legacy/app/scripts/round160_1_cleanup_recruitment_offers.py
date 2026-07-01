"""ROUND 16.0.1 — Soft-deprecate pre-existing recruitment offers
that contain a candidate with a deprecated class (necromancer/assassin/berserker).

Behaviour:
  - Tag each affected `recruitment_offers` row with
    `is_deprecated_round160=True` and `deprecated_at=<now>`.
  - The read-path in `recruitment.services.get_or_init_candidates_for_guild`
    already skips offers tied to deprecated `adventurer_class_id`; this
    script makes the soft-deprecation explicit (audit + data hygiene).
  - Idempotent: rerun re-tags already-tagged rows with the same values.
  - NO hard delete.
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def main(dry_run: bool = False) -> dict:
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = cli[os.environ["DB_NAME"]]
    try:
        # Resolve the deprecated class ids dynamically (no slug hard-code in
        # the filter, so Phase 6+ deprecations are caught automatically).
        deprecated_ids: list[str] = [
            r["id"] async for r in db.adventurer_classes.find(
                {"$or": [
                    {"is_base_class": False},
                    {"deprecated_at": {"$ne": None}},
                    {"is_active": False},
                ]},
                {"_id": 0, "id": 1},
            )
        ]
        if not deprecated_ids:
            return {"dry_run": dry_run, "touched": 0, "deprecated_class_ids": 0}

        affected = await db.recruitment_offers.count_documents(
            {"adventurer_class_id": {"$in": deprecated_ids}})

        if dry_run or affected == 0:
            cli.close()
            return {"dry_run": dry_run, "affected": affected,
                    "deprecated_class_ids": len(deprecated_ids)}

        now = utc_now_iso()
        res = await db.recruitment_offers.update_many(
            {"adventurer_class_id": {"$in": deprecated_ids}},
            {"$set": {"is_deprecated_round160": True,
                       "deprecated_at": now,
                       "updated_at": now}},
        )

        # Audit
        from app.audit.log import write_audit
        await write_audit(
            db,
            event_type="recruitment_offers_deprecated_round160",
            actor_user_id=None,
            source="round160_1_cleanup",
            metadata={"affected": affected,
                       "matched": res.matched_count,
                       "modified": res.modified_count,
                       "deprecated_class_ids": len(deprecated_ids)},
        )
        return {"dry_run": dry_run, "affected": affected,
                "matched": res.matched_count, "modified": res.modified_count,
                "deprecated_class_ids": len(deprecated_ids)}
    finally:
        cli.close()


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    out = asyncio.run(main(dry_run=dry))
    print(out)
