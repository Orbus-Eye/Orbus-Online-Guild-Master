"""ROUND 14.cleanup — Soft-archive demo/test guilds pre-launch.

Idempotent. Adds `is_archived_pre_launch=True` + `archived_at` + `archived_reason`
to guilds matching the cleanup criteria. **PRESERVES**:
  * The tester guild (owner `tester@orbus.test`).
  * The 3 lore-coherent demo opponents (`is_demo_opponent=True`).
  * Any guild already archived (rerun is no-op).

NO hard delete. Records remain queryable for admin/forensics.
"""
from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient


PRESERVE_EMAILS = {"tester@orbus.test"}
ARCHIVE_REASON = "round14_pre_launch_cleanup"


async def run(db) -> dict:
    now = datetime.now(timezone.utc).isoformat()

    # Resolve preserved guild ids (tester + 3 demo opponents).
    tester_users = await db.users.find(
        {"email": {"$in": list(PRESERVE_EMAILS)}}, {"_id": 0, "id": 1}
    ).to_list(20)
    tester_user_ids = {u["id"] for u in tester_users}
    preserve_ids = set()
    if tester_user_ids:
        async for g in db.guilds.find(
            {"owner_user_id": {"$in": list(tester_user_ids)}},
            {"_id": 0, "id": 1, "name": 1},
        ):
            preserve_ids.add(g["id"])
    # Preserve all demo opponents (lore guilds for PvP matchmaking).
    async for g in db.guilds.find(
        {"is_demo_opponent": True}, {"_id": 0, "id": 1, "name": 1},
    ):
        preserve_ids.add(g["id"])

    # Candidate query: test_artifact OR name pattern, NOT already archived,
    # NOT in preserve list.
    candidate_filter = {
        "$or": [
            {"is_test_artifact": True},
            # ROUND 14.v2.1 — Extended naming patterns to catch legacy
            # fixture guilds created by R4/R5/R6B/R6D/R11 seed scripts that
            # never set `is_test_artifact`. All match `^<round_prefix> <hex>$`.
            {"name": {"$regex": "^(G_|G |Test|Demo|tester|R[0-9]|[0-9]+[A-Z]|P[0-9]+[A-Za-z]*\\s+[0-9a-fA-F]|Ver\\s+ver_|RaidSmoke\\s+raidsmoke_)",
                      "$options": "i"}},
            # ROUND 14.v2.1 (close-out) — Catches every `Guild_*`, `Guild <hex>`,
            # and `Guildhouse <hex>` fixture families produced by phase/round
            # seed scripts (Guild_ref_*, Guild_gw_*, Guild_sc_*, Guild_unlock_*,
            # Guild_gates_*, Guild_disp_lock_*, Guildhouse <HEX>, Guild <hex>).
            # Safe vs preserved names (`The Iron Lantern`, `Custodi del Vento`,
            # `Esiliati del Vuoto`, `Compagnia delle Tre Lune`, `Sentiero di
            # Efreto`) — none of them start with `Guild` or `Guildhouse` + sep.
            {"name": {"$regex": "^Guild(house)?[_\\s]",
                      "$options": "i"}},
        ],
        "is_archived_pre_launch": {"$ne": True},
        "id": {"$nin": list(preserve_ids)},
    }

    before_total = await db.guilds.count_documents({})
    candidates = await db.guilds.find(
        candidate_filter,
        {"_id": 0, "id": 1, "name": 1, "is_test_artifact": 1,
         "is_demo_opponent": 1},
    ).to_list(50_000)

    # Apply soft-flag.
    archived_ids = []
    sample_archived = []
    for g in candidates:
        if g["id"] in preserve_ids:
            continue
        if g.get("is_demo_opponent"):
            # Extra safety: never archive demo opponents even if name matches.
            continue
        archived_ids.append(g["id"])
        if len(sample_archived) < 10:
            sample_archived.append({"id": g["id"], "name": g["name"]})

    if archived_ids:
        await db.guilds.update_many(
            {"id": {"$in": archived_ids}},
            {"$set": {
                "is_archived_pre_launch": True,
                "archived_at": now,
                "archived_reason": ARCHIVE_REASON,
            }},
        )
        # Audit events (best-effort, batched).
        try:
            from app.audit.log import write_audit
            for gid in archived_ids[:5000]:  # cap audit explosion
                try:
                    await write_audit(
                        db, event_type="guild_archived_pre_launch",
                        actor_guild_id=gid,
                        source="round14_cleanup_script",
                        metadata={"reason": ARCHIVE_REASON, "at": now},
                    )
                except Exception:  # noqa: BLE001
                    pass
        except Exception:  # noqa: BLE001
            pass

    after_archived = await db.guilds.count_documents(
        {"is_archived_pre_launch": True}
    )
    active_after = await db.guilds.count_documents(
        {"is_archived_pre_launch": {"$ne": True}}
    )
    return {
        "before_total_guilds": before_total,
        "preserved_ids_count": len(preserve_ids),
        "archived_in_this_run": len(archived_ids),
        "total_archived_now": after_archived,
        "active_after": active_after,
        "sample_archived": sample_archived,
        "preserved_names": [g["name"] for g in await db.guilds.find(
            {"id": {"$in": list(preserve_ids)}}, {"_id": 0, "name": 1}
        ).to_list(20)],
    }


async def main():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    try:
        report = await run(db)
        print("=== ROUND 14 cleanup result ===")
        for k, v in report.items():
            print(f"  {k}: {v}")
        return report
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
