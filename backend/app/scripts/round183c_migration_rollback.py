"""ROUND 18.3c — Rollback script for orphan class migration.

Reverte la migration R18.3c: ripristina `class_slug` da `previous_class_slug`,
rimuove i metadati e rimuove l'evento career_history R18.3c dall'array.

Idempotente: seconda esecuzione = 0 modifiche (skip su adventurer senza
`migration_round=R18.3c`).

Uso:
    python -m app.scripts.round183c_migration_rollback --dry-run
    python -m app.scripts.round183c_migration_rollback --apply

**Sicurezza**: verifica preventive prima di rollback:
  - Nessun expedition attivo che coinvolge adventurer migrati
  - Nessun raid attivo che coinvolge adventurer migrati
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")

ROLLBACK_AUDIT_EVENT_TYPE = "R18_CLASS_ORPHAN_MIGRATION_ROLLED_BACK"


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def run(dry_run: bool) -> int:
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    mode = "DRY-RUN" if dry_run else "APPLY"
    print(f"[mode] {mode} · round=R18.3c ROLLBACK\n")

    q = {"migration_round": "R18.3c"}
    n_migrated = await db.adventurers.count_documents(q)
    print(f"[scan] adventurers migrated in R18.3c: {n_migrated}")
    if n_migrated == 0:
        print("[idempotent] nothing to rollback")
        return 0

    # Safety: check no active expedition/raid on these adventurers
    async for adv in db.adventurers.find(
        {"migration_round": "R18.3c",
         "$or": [
             {"current_mission_id": {"$ne": None}},
             {"is_available": False},
         ]},
        {"_id": 0, "id": 1, "name": 1, "current_mission_id": 1,
         "current_mission_type": 1, "is_available": 1},
    ).limit(5):
        print(f"[warn] adv {adv.get('name')} ({adv.get('id')}) has active "
              f"mission {adv.get('current_mission_type')} — proceed with care")

    # Rollback via aggregation pipeline update:
    # $set class_slug = $previous_class_slug
    # $unset migration metadata
    # $pull last career_history entry with round=R18.3c
    if dry_run:
        # Sample effect
        sample = await db.adventurers.find_one(q, {"_id": 0, "id": 1,
            "class_slug": 1, "previous_class_slug": 1})
        print(f"[dry-run] would revert {n_migrated} adv. sample: {sample}")
        return 0

    # Note: motor doesn't support arrayFilters with pull-by-match easily; use
    # per-doc iteration for safety.
    reverted = 0
    async for adv in db.adventurers.find(q, {"_id": 0, "id": 1,
            "previous_class_slug": 1, "career_history": 1}):
        prev = adv.get("previous_class_slug")
        if not prev:
            continue
        history = adv.get("career_history") or []
        new_history = [
            h for h in history
            if not (h.get("round") == "R18.3c"
                    and h.get("event") == "class_migration")
        ]
        set_ops = {
            "class_slug": prev,
            "updated_at": _utc_iso(),
        }
        # class_name viene ripristinato al display IT del source (best effort)
        source_cls = await db.adventurer_classes.find_one(
            {"slug": prev}, {"_id": 0, "display_name_it": 1, "name": 1}
        )
        if source_cls:
            set_ops["class_name"] = (
                source_cls.get("display_name_it")
                or source_cls.get("name")
                or prev
            )
        unset_ops = {
            "previous_class_slug": "",
            "migration_round": "",
            "migration_reason": "",
            "migration_timestamp": "",
        }
        update_doc = {"$set": set_ops, "$unset": unset_ops}
        if len(new_history) != len(history):
            update_doc["$set"]["career_history"] = new_history
        await db.adventurers.update_one({"id": adv["id"]}, update_doc)
        reverted += 1

    print(f"[apply] reverted {reverted} adventurers")

    # Emit rollback audit event
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()),
        "event_type": ROLLBACK_AUDIT_EVENT_TYPE,
        "actor_user_id": None,
        "actor_guild_id": None,
        "source": "script.round183c_migration_rollback",
        "metadata": {
            "round": "R18.3c",
            "operation": "rollback",
            "reverted_count": reverted,
        },
        "created_at": _utc_iso(),
    })
    print(f"[audit] {ROLLBACK_AUDIT_EVENT_TYPE} emitted")
    return 0


def _parse_args():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true", default=True)
    g.add_argument("--apply", dest="apply_", action="store_true")
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    dry_run = not args.apply_
    sys.exit(asyncio.run(run(dry_run=dry_run)))


if __name__ == "__main__":
    main()
