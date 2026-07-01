"""ROUND 16.3 Phase 6 seal — QA cleanup utility.

Archivia i pacts residui del testing E2E + eventuale specialization
attiva del tester per riportare l'account allo stato "pulito" per il
playtest finale utente.

Gated APP_ENV != "production". Idempotente.

Usage:
    cd /app/backend && set -a && source .env && set +a && \\
        python -m app.scripts.reset_test_account_phase6_state
    # or specify email:
    python -m app.scripts.reset_test_account_phase6_state --email tester@orbus.test
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone

logger = logging.getLogger("orbus.dev.reset_phase6")
logging.basicConfig(level=logging.INFO,
                     format="%(levelname)s %(name)s %(message)s")

# Explicit pact IDs to archive (from Phase 6 E2E cleanup brief).
CLEANUP_PACT_IDS = [
    "4c7357b2-5bc5-4f52-97f4-b290cb12e595",
    "2353685a-ba36-4706-a7e1-cffd828f054c",
    "17f80651-23d0-440f-9d1d-f59fe45566e7",
    "5a86e5b1-6bf4-44a5-a240-c628e2da7c0a",
    "ec9b57df-73d0-4700-a0e9-87ff81fc5293",
    "4b8c098a-bed3-464d-9977-ce5921d7ab3a",
]


def _iso(dt: datetime) -> str:
    return dt.isoformat()


async def _emit_audit(db, event_type: str, guild_id, target_id: str,
                       metadata: dict) -> None:
    try:
        await db.audit_log.insert_one({
            "id": str(uuid.uuid4()),
            "event_type": event_type,
            "actor_id": None,
            "actor_guild_id": guild_id,
            "target_id": target_id,
            "metadata": metadata,
            "created_at": _iso(datetime.now(timezone.utc)),
        })
    except Exception as exc:
        logger.warning("audit emit %s: %s", event_type, exc)


async def _archive_pacts(db) -> dict:
    now_iso = _iso(datetime.now(timezone.utc))
    archived = 0
    already = 0
    not_found = 0
    for pid in CLEANUP_PACT_IDS:
        row = await db.guild_trade_pacts.find_one({"id": pid}, {"_id": 0})
        if not row:
            not_found += 1
            continue
        if row.get("status") == "cleanup_archived":
            already += 1
            continue
        r = await db.guild_trade_pacts.update_one(
            {"id": pid,
             "status": {"$nin": ["cleanup_archived"]}},
            {"$set": {"status": "cleanup_archived",
                      "dissolved_at": now_iso,
                      "dissolved_by": "qa_cleanup",
                      "dissolution_reason": "qa_cleanup",
                      "cooldown_ends_at": None,
                      "updated_at": now_iso}})
        if r.modified_count:
            archived += 1
            await _emit_audit(db, "TRADE_PACT_FORCE_DISSOLVED",
                                None, pid,
                                {"source": "qa_cleanup",
                                 "prior_status": row.get("status")})
    return {"archived": archived, "already": already,
            "not_found": not_found,
            "total_targeted": len(CLEANUP_PACT_IDS)}


async def _archive_specialization(db, guild_id: str) -> dict:
    now_iso = _iso(datetime.now(timezone.utc))
    active = await db.guild_specialization_choice.find_one(
        {"guild_id": guild_id, "status": "active"}, {"_id": 0})
    if not active:
        return {"status": "no_active_choice"}
    r = await db.guild_specialization_choice.update_one(
        {"id": active["id"], "status": "active"},
        {"$set": {"status": "archived",
                  "last_reset_at": now_iso,
                  "updated_at": now_iso}})
    if r.modified_count:
        await _emit_audit(db, "GUILD_SPECIALIZATION_RESET",
                            guild_id, active["id"],
                            {"source": "qa_cleanup",
                             "old_slug": active["specialization_slug"],
                             "new_slug": None})
        return {"status": "archived",
                "prior_slug": active["specialization_slug"],
                "choice_id": active["id"]}
    return {"status": "cas_race", "choice_id": active["id"]}


async def _reset(email: str) -> dict:
    from app.core.database import db
    if os.environ.get("APP_ENV") == "production":
        raise RuntimeError("Refusing to run in production")
    user = await db.users.find_one({"email": email}, {"_id": 0, "id": 1})
    if not user:
        return {"status": "error", "reason": f"user_not_found:{email}"}
    guild = await db.guilds.find_one(
        {"owner_user_id": user["id"]}, {"_id": 0, "id": 1, "name": 1})
    if not guild:
        return {"status": "error", "reason": f"guild_not_found:{email}"}
    pacts_result = await _archive_pacts(db)
    spec_result = await _archive_specialization(db, guild["id"])
    return {"status": "ok",
            "email": email,
            "guild": {"id": guild["id"], "name": guild["name"]},
            "pacts": pacts_result,
            "specialization": spec_result}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", default="tester@orbus.test")
    args = parser.parse_args()
    result = asyncio.run(_reset(args.email))
    logger.info("Phase 6 cleanup result: %s", result)
    print(result)


if __name__ == "__main__":
    main()
