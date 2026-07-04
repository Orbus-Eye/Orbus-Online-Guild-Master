"""ROUND 18.1 Follow-up — Audit-log retroactive backfill.

Il main migration script `round181_schema_foundation.py` ha scritto i 7
audit event R18_* nella collezione `audit_events` (secondaria, non alimenta
il Dashboard admin). Il feed pubblico `/api/admin/audit/events` legge invece
`audit_log`, quindi il PM non li vedeva.

Questo script append-only e idempotente:
  1. Legge il primo/ultimo doc R18_* da `audit_events` per ciascuno dei 7
     tipi (fonte di verità per timestamp e metadata operativi)
  2. Emette 1 event summary per tipo in `audit_log` con:
       - schema conforme a audit_log (id, event_type, actor_*, source, ...)
       - `metadata.is_retroactive = True` per trasparenza
       - `metadata.round = "R18.1"`
       - `metadata.original_occurred_at` preservato
  3. Idempotente: presenza in audit_log verificata via
     `event_type + metadata.round + metadata.is_retroactive`

Uso:
    python -m app.scripts.round181_audit_log_backfill --dry-run
    python -m app.scripts.round181_audit_log_backfill --apply
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


R18_EVENT_TYPES = [
    "R18_MIGRATION_STARTED",
    "R18_MIGRATION_COMPLETED",
    "R18_ORPHAN_MARKED_UNASSIGNED",
    "R18_GUARDIAN_CLERIC_ALIASED",
    "R18_GRADE_BACKFILLED",
    "R18_ROSTER_CAP_COMPUTED",
    "R18_BETA_FIELD_PREPARED",
]


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _fetch_source_event(db, event_type: str) -> dict | None:
    """Read the FIRST (chronological) R18_* event from audit_events for the
    given type. Timestamp fedele + metadata operativi preservati."""
    doc = await db.audit_events.find_one(
        {"event_type": event_type},
        {"_id": 0},
        sort=[("occurred_at", 1)],
    )
    return doc


async def _already_backfilled(db, event_type: str) -> bool:
    """Idempotency check: is there already a retroactive doc in audit_log?"""
    n = await db.audit_log.count_documents({
        "event_type": event_type,
        "metadata.round": "R18.1",
        "metadata.is_retroactive": True,
    })
    return n > 0


async def _emit_retroactive(db, event_type: str, source: dict) -> bool:
    """Insert 1 retroactive summary doc in audit_log. Returns True if new."""
    if await _already_backfilled(db, event_type):
        return False
    src_meta = source.get("metadata", {}) if source else {}
    original_ts = source.get("occurred_at") if source else None
    doc = {
        "id": str(uuid.uuid4()),
        "event_type": event_type,
        "actor_user_id": None,
        "actor_guild_id": None,
        "item_slug": None,
        "item_template_id": None,
        "quantity": None,
        "gold_delta": None,
        "source": "script.round181_audit_log_backfill",
        "related_entity_id": None,
        "metadata": {
            "round": "R18.1",
            "is_retroactive": True,
            "original_occurred_at": original_ts,
            "original_source": (
                source.get("source") if source else None
            ),
            # Preserve original operational metadata
            **{k: v for k, v in src_meta.items() if k != "round"},
        },
        "created_at": _utc_iso(),
    }
    await db.audit_log.insert_one(doc)
    return True


async def run(dry_run: bool) -> int:
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        print("[fatal] MONGO_URL / DB_NAME missing", file=sys.stderr)
        return 2
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    mode = "DRY-RUN" if dry_run else "APPLY"
    print(f"[mode] {mode} · db={db_name} · round=R18.1 audit-backfill")

    plan = []
    for evt in R18_EVENT_TYPES:
        source = await _fetch_source_event(db, evt)
        already = await _already_backfilled(db, evt)
        status = "skip (already)" if already else (
            "emit (source found)" if source else "emit (no source, best-effort)"
        )
        plan.append((evt, source, already, status))
        print(f"  · {evt:<32}  audit_events_found={'Y' if source else 'N'}  "
              f"already_in_audit_log={'Y' if already else 'N'}  → {status}")

    if dry_run:
        print("\n[dry-run] Re-run con --apply per scrivere.")
        return 0

    inserted = 0
    for evt, source, already, _ in plan:
        if already:
            continue
        # Se non c'è source (mai emesso originale), scriviamo comunque
        # summary retroattivo con metadata minima
        if source is None:
            source = {
                "occurred_at": None,
                "source": "unknown",
                "metadata": {},
            }
        if await _emit_retroactive(db, evt, source):
            inserted += 1
            print(f"  [emit] {evt}  (retroactive summary in audit_log)")

    print(f"\n[apply] Inserted {inserted}/{len(R18_EVENT_TYPES)} "
          "retroactive event summaries into audit_log.")
    # Sanity re-check
    total_r18_in_log = await db.audit_log.count_documents({
        "event_type": {"$regex": "^R18_"}
    })
    print(f"[verify] audit_log R18_* total: {total_r18_in_log} "
          "(expected ≥ 7)")
    return 0


def _parse_args():
    p = argparse.ArgumentParser(description=__doc__ or "")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true", default=True)
    g.add_argument("--apply", dest="apply_", action="store_true")
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    sys.exit(asyncio.run(run(dry_run=not args.apply_)))


if __name__ == "__main__":
    main()
