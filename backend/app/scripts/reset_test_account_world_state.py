"""ROUND 16.3 Phase 2 seal — Cleanup dev utility.

Ripristina lo stato "pulito" per un test account (default: tester@orbus.test):
    - Archivia TUTTE le presence attive (no hard delete)
    - Crea nuova presence 'ambash' active con change_count=0 e
      next_change_available_at = now + 30 giorni
    - Emette audit event WORLD_CONTINENT_CHANGED con source: "dev_reset"

Gated APP_ENV != "production".

Usage:
    cd /app/backend && set -a && source .env && set +a && \\
        python -m app.scripts.reset_test_account_world_state
    # or specify email:
    python -m app.scripts.reset_test_account_world_state --email tester@orbus.test
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone

logger = logging.getLogger("orbus.dev.reset_world")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")


async def _reset(email: str, target_slug: str = "ambash") -> dict:
    from app.core.database import db
    if os.environ.get("APP_ENV") == "production":
        raise RuntimeError("Refusing to run in production")

    user = await db.users.find_one({"email": email}, {"_id": 0, "id": 1})
    if not user:
        return {"status": "error", "reason": f"user not found: {email}"}
    guild = await db.guilds.find_one(
        {"owner_user_id": user["id"]}, {"_id": 0, "id": 1, "name": 1},
    )
    if not guild:
        return {"status": "error", "reason": f"guild not found for {email}"}

    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    next_change = (now + timedelta(days=30)).isoformat()

    # Archive ALL active presence (no hard delete)
    archived = await db.guild_world_presence.update_many(
        {"guild_id": guild["id"], "status": "active"},
        {"$set": {"status": "archived", "archived_at": now_iso,
                  "updated_at": now_iso}},
    )

    # Insert clean new presence
    new_id = str(uuid.uuid4())
    doc = {
        "id": new_id,
        "guild_id": guild["id"], "continent_slug": target_slug,
        "joined_at": now_iso, "last_changed_at": now_iso,
        "next_change_available_at": next_change,
        "change_count": 0, "status": "active",
        "created_at": now_iso, "updated_at": now_iso,
        "_dev_reset": True,
    }
    await db.guild_world_presence.insert_one(doc)

    # History append (append-only)
    await db.guild_world_presence_history.insert_one({
        "id": str(uuid.uuid4()),
        "guild_id": guild["id"], "continent_slug": target_slug,
        "action": "dev_reset", "at": now_iso, "presence_id": new_id,
    })

    # Audit — best-effort
    try:
        from app.audit.log import write_audit
        await write_audit(
            db, event_type="WORLD_CONTINENT_CHANGED",
            actor_user_id=user["id"], actor_guild_id=guild["id"],
            source="dev_reset", related_entity_id=new_id,
            metadata={"target_slug": target_slug, "archived_count": archived.modified_count,
                     "utility": "reset_test_account_world_state"},
        )
    except Exception as exc:
        logger.warning("audit emit skipped: %s", exc)

    return {
        "status": "ok",
        "email": email,
        "guild_id": guild["id"],
        "guild_name": guild.get("name"),
        "archived_count": archived.modified_count,
        "new_presence_id": new_id,
        "new_continent_slug": target_slug,
        "next_change_available_at": next_change,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--email", default="tester@orbus.test")
    p.add_argument("--continent", default="ambash")
    args = p.parse_args()
    out = asyncio.run(_reset(args.email, args.continent))
    logger.info("reset result: %s", out)
    return 0 if out.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
