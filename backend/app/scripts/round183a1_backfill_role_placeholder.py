"""ROUND 18.3a.1 hotfix — Backfill `role="TBD"` placeholder sui doc
seedati da R18.3a (`cacciatore_di_mostri`, `cacciatore_del_vuoto`).

Il PM ha deferrato la decisione ruolo (Q7-Q24) — questo backfill inserisce
un placeholder esplicito `role="TBD" + role_placeholder=true +
role_pm_decision_pending=true` per prevenire crash e marcare il ruolo
come provvisorio.

Idempotente: se i marker esistono già = 0 modifiche.

Emit opzionale audit event `R18_CLASS_ROLE_PLACEHOLDER_BACKFILLED`.

Uso:
    python -m app.scripts.round183a1_backfill_role_placeholder --apply
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")


TARGET_SLUGS = ["cacciatore_di_mostri", "cacciatore_del_vuoto"]
AUDIT_EVENT_TYPE = "R18_CLASS_ROLE_PLACEHOLDER_BACKFILLED"


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def run(dry_run: bool) -> int:
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    mode = "DRY-RUN" if dry_run else "APPLY"
    print(f"[mode] {mode} · round=R18.3a.1 role-placeholder-backfill")

    query = {
        "slug": {"$in": TARGET_SLUGS},
        "source_round": "R18.3a",
    }
    docs = await db.adventurer_classes.find(
        query, {"_id": 0, "id": 1, "slug": 1, "role": 1,
                "role_placeholder": 1, "role_pm_decision_pending": 1}
    ).to_list(10)
    print(f"[scan] docs found: {len(docs)}")
    for d in docs:
        print(f"  {d['slug']} · role={d.get('role')} "
              f"placeholder={d.get('role_placeholder')} "
              f"pending={d.get('role_pm_decision_pending')}")

    # Idempotency: skip se tutti i doc hanno già i 3 marker corretti
    n_needing_backfill = 0
    for d in docs:
        if (d.get("role") != "TBD"
            or d.get("role_placeholder") is not True
            or d.get("role_pm_decision_pending") is not True):
            n_needing_backfill += 1

    if n_needing_backfill == 0:
        print("[idempotent] all docs already backfilled — no update")
    elif dry_run:
        print(f"[dry-run] would backfill {n_needing_backfill} doc(s)")
    else:
        res = await db.adventurer_classes.update_many(
            query,
            {"$set": {
                "role": "TBD",
                "role_placeholder": True,
                "role_pm_decision_pending": True,
                "updated_at": _utc_iso(),
            }},
        )
        print(f"[apply] update_many: matched={res.matched_count} "
              f"modified={res.modified_count}")

    # Audit event (idempotent — only if never emitted)
    existing = await db.audit_log.count_documents(
        {"event_type": AUDIT_EVENT_TYPE}
    )
    if existing >= 1:
        print(f"[audit] {AUDIT_EVENT_TYPE} already logged — skip")
    elif dry_run:
        print(f"[dry-run] audit event NOT emitted")
    else:
        await db.audit_log.insert_one({
            "id": str(uuid.uuid4()),
            "event_type": AUDIT_EVENT_TYPE,
            "actor_user_id": None,
            "actor_guild_id": None,
            "item_slug": None,
            "item_template_id": None,
            "quantity": None,
            "gold_delta": None,
            "source": "script.round183a1_backfill_role_placeholder",
            "related_entity_id": None,
            "metadata": {
                "round": "R18.3a.1",
                "hotfix_for": "R18.3a",
                "reason": "Prevent HTTP 500 on class_public() when doc missing 'role'",
                "slugs_affected": TARGET_SLUGS,
                "role_placeholder_value": "TBD",
                "role_pm_decision_pending": True,
                "pm_decision_deferred_questions": "Q7-Q24",
                "docs_matched": len(docs),
                "docs_backfilled": n_needing_backfill,
            },
            "created_at": _utc_iso(),
        })
        print(f"[audit] {AUDIT_EVENT_TYPE} emitted")

    return 0


def _parse_args():
    p = argparse.ArgumentParser(description=__doc__ or "")
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
