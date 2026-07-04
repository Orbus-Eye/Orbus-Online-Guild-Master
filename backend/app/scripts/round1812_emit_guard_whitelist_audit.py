"""ROUND 18.1.2 — Emit `R18_GUARD_WHITELIST_EXTENDED` audit event (idempotent).

Il round R18.1.2 estende il guard R18.1.1 nell'expedition dispatch per
accettare una whitelist esplicita di classi target R18.3 migration con
`is_playable=false + migration_target_only=true`. Il codice del guard è
già stato patchato in `app/expeditions/services.py`; questo script è
solo l'osservabilità retroattiva (audit_log).

Idempotente: se `R18_GUARD_WHITELIST_EXTENDED` è già presente in
`audit_log`, skip. Altrimenti insert 1 doc.

Uso:
    python -m app.scripts.round1812_emit_guard_whitelist_audit --apply
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


EVENT_TYPE = "R18_GUARD_WHITELIST_EXTENDED"

R18_MIGRATION_TARGET_WHITELIST = [
    "cacciatore_di_mostri",
    "cacciatore_del_vuoto",
]


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def run(dry_run: bool) -> int:
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        print("[fatal] MONGO_URL / DB_NAME missing", file=sys.stderr)
        return 2

    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    mode = "DRY-RUN" if dry_run else "APPLY"
    print(f"[mode] {mode} · db={db_name} · round=R18.1.2 guard-whitelist-audit")

    existing = await db.audit_log.count_documents({"event_type": EVENT_TYPE})
    print(f"[scan] existing {EVENT_TYPE} in audit_log: {existing}")
    if existing >= 1:
        print("[idempotent] event already present — no insert")
        return 0

    doc = {
        "id": str(uuid.uuid4()),
        "event_type": EVENT_TYPE,
        "actor_user_id": None,
        "actor_guild_id": None,
        "item_slug": None,
        "item_template_id": None,
        "quantity": None,
        "gold_delta": None,
        "source": "script.round1812_emit_guard_whitelist_audit",
        "related_entity_id": None,
        "metadata": {
            "round": "R18.1.2",
            "allowed_migration_target_slugs": R18_MIGRATION_TARGET_WHITELIST,
            "guard_scope": "expedition.dispatch",
            "guard_file": "app/expeditions/services.py",
            "is_playable_false_still_hidden": True,
            "migration_apply": False,
            "feature_flag_R18_REWORK_ENABLED": os.environ.get("R18_REWORK_ENABLED"),
            "feature_flag_R18_TALENT_ENGINE_ENABLED": os.environ.get("R18_TALENT_ENGINE_ENABLED"),
        },
        "created_at": _utc_iso(),
    }

    if dry_run:
        print(f"\n[dry-run] would insert 1 audit_log doc:")
        print(f"  event_type={EVENT_TYPE}")
        print(f"  metadata.allowed_migration_target_slugs={doc['metadata']['allowed_migration_target_slugs']}")
        return 0

    await db.audit_log.insert_one(doc)
    print(f"\n[apply] inserted 1 audit_log doc event_type={EVENT_TYPE}")
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
