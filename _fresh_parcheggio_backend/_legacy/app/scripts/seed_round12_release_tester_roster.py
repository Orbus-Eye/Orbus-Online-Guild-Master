"""ROUND 12.D.3 — Preview-only: release tester's stuck adventurers.

Idempotent script invoked at lifespan startup. It only runs when
APP_ENV != "production". Looks up `tester@orbus.test`, finds their
guild, and flips `is_available=true` on any adventurer that is
`is_available=false`, NOT retired, NOT archived, NOT frozen.

Emits a single audit log row `tester_roster_released_preview` with
the count of released adventurers (zero is fine, still logged on first
run only).

Safe to invoke on every boot: a follow-up call with all roster already
available will return {status: "noop", released: 0} and skip audit write.
"""
from __future__ import annotations

import logging
import os
from typing import Any

from app.audit.log import write_audit
from app.core.database import db

logger = logging.getLogger("orbus.seed_round12_release_tester_roster")

TESTER_EMAIL = "tester@orbus.test"


async def run() -> dict[str, Any]:
    if (os.environ.get("APP_ENV") or "").lower() == "production":
        return {"status": "skipped", "reason": "production_env"}

    user = await db.users.find_one({"email": TESTER_EMAIL}, {"_id": 0, "id": 1})
    if not user:
        return {"status": "skipped", "reason": "tester_user_missing"}

    guild = await db.guilds.find_one(
        {"owner_user_id": user["id"]},
        {"_id": 0, "id": 1, "name": 1, "public_id": 1},
    )
    if not guild:
        return {"status": "skipped", "reason": "tester_guild_missing"}

    flt = {
        "guild_id": guild["id"],
        "is_available": False,
        "retired": {"$ne": True},
        "archived": {"$ne": True},
        "frozen": {"$ne": True},
    }
    stuck_ids = [
        a["id"]
        for a in await db.adventurers.find(flt, {"_id": 0, "id": 1}).to_list(200)
    ]
    if not stuck_ids:
        return {"status": "noop", "released": 0, "guild_id": guild["id"]}

    res = await db.adventurers.update_many(flt, {"$set": {"is_available": True}})

    await write_audit(
        db,
        event_type="tester_roster_released_preview",
        actor_guild_id=guild["id"],
        source="seed.round12_release_tester_roster",
        metadata={
            "released_count": int(res.modified_count),
            "adventurer_ids": stuck_ids[:50],  # cap to avoid huge audit rows
            "guild_name": guild.get("name"),
            "guild_public_id": guild.get("public_id"),
            "reason": "preview only — keep tester roster available for PvP setup",
        },
    )
    logger.info(
        "tester_roster_released_preview: released=%d guild=%s",
        res.modified_count, guild.get("name"),
    )
    return {
        "status": "released",
        "released": int(res.modified_count),
        "guild_id": guild["id"],
        "adventurer_ids": stuck_ids,
    }


if __name__ == "__main__":
    import asyncio
    print(asyncio.run(run()))
