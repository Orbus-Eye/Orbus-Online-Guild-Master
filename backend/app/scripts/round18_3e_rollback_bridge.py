"""
ROUND 18.3e — Rollback Bridge Metadata Sibling Script
======================================================

═══════════════════════════════════════════════════════════════════════
🔒 CLOSED & SEALED — R18.3e Phase B — 2026-07-05T20:15:00Z UTC
🔒 SEAL AUTHORITY: PM Orchestrator
🔒 SEAL NOTE: Rollback sibling di apply_bridge.py. Dry-run 18/18 PASS
🔒 verificato post-B2. Default DRY-RUN preserved. Real rollback richiede
🔒 doppio flag (--apply + --i-understand-this-will-unset-bridge-metadata)
🔒 e nuovo gate PM esplicito. Rollback source-of-truth per emergency-only.
🔒 Byte-identical enforcement: verify manuale con sha256sum.
═══════════════════════════════════════════════════════════════════════

**Status**: SEALED. Default DRY-RUN. Sibling di `round18_3e_apply_bridge.py`.
Se lanciato con `--apply --i-understand-this-will-unset-bridge-metadata`, esegue
$unset simmetrico dei 5 SAFE bridge metadata field sui 18 doc adventurer_classes.

**Governance**:
    - Rimuove ESCLUSIVAMENTE i 5 SAFE fields: canonical_slug, alias_target,
      bridge_status, bridge_source_round, bridge_applied_at.
    - Non tocca class_slug, display_name_it, primary_stat, role, base_*, is_*.
    - Emette 1 solo audit event aggregato R18_3E_BRIDGE_METADATA_ROLLED_BACK.

**Wired to runtime**: NO.

**Usage**:
    Dry-run (default):
        python -m app.scripts.round18_3e_rollback_bridge

    Real rollback:
        python -m app.scripts.round18_3e_rollback_bridge --apply \
            --i-understand-this-will-unset-bridge-metadata
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# 5 SAFE fields (identical to apply script)
SAFE_FIELDS: tuple[str, ...] = (
    "canonical_slug",
    "alias_target",
    "bridge_status",
    "bridge_source_round",
    "bridge_applied_at",
)

REGISTRY_PATH = Path("/app/memory/r18_3e_bridge_registry.json")
SOURCE_ROUND_TAG = "R18.3e Phase B"


def _load_registry() -> dict[str, Any]:
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(f"Registry not found: {REGISTRY_PATH}")
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def dry_run() -> dict[str, Any]:
    registry = _load_registry()
    entries: list[dict[str, Any]] = registry["bridge_entries"]
    unset_payload = {f: "" for f in SAFE_FIELDS}
    report = {
        "mode": "dry_run",
        "source_round": SOURCE_ROUND_TAG,
        "total_entries": len(entries),
        "would_unset_count": len(entries),
        "fields_would_unset": list(SAFE_FIELDS),
        "unset_payload_sample": {"$unset": unset_payload},
        "audit_event_would_emit": {
            "event_type": "R18_3E_BRIDGE_METADATA_ROLLED_BACK",
            "actually_emitted": False,
        },
    }
    return report


def apply_rollback(ack: bool) -> None:
    import asyncio
    import os
    import uuid
    from datetime import datetime, timezone

    from dotenv import load_dotenv
    from motor.motor_asyncio import AsyncIOMotorClient

    if not ack:
        raise SystemExit(
            "[FAIL-FAST] Missing acknowledgment flag "
            "`--i-understand-this-will-unset-bridge-metadata`."
        )

    registry = _load_registry()
    entries: list[dict[str, Any]] = registry["bridge_entries"]
    if len(entries) != 18:
        raise SystemExit(
            f"[GUARD FAIL-FAST] target_count drift: {len(entries)} != 18."
        )

    rolled_back_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rollback_id = str(uuid.uuid4())
    unset_payload = {f: "" for f in SAFE_FIELDS}

    async def _run() -> dict[str, Any]:
        load_dotenv("/app/backend/.env")
        client = AsyncIOMotorClient(os.environ["MONGO_URL"])
        try:
            db = client[os.environ["DB_NAME"]]
            modified = 0
            skipped = 0
            errors: list[str] = []
            for entry in entries:
                slug = entry["slug"]
                try:
                    res = await db.adventurer_classes.update_one(
                        {"slug": slug}, {"$unset": unset_payload}
                    )
                    if res.matched_count == 1:
                        modified += 1
                    else:
                        skipped += 1
                        errors.append(f"slug={slug!r}: matched={res.matched_count}")
                except Exception as exc:
                    errors.append(f"slug={slug!r}: {exc}")

            audit_event = {
                "id": str(uuid.uuid4()),
                "event_type": "R18_3E_BRIDGE_METADATA_ROLLED_BACK",
                "created_at": rolled_back_at,
                "metadata": {
                    "round": "R18.3e",
                    "phase": "B_rollback",
                    "rollback_id": rollback_id,
                    "target_count": len(entries),
                    "modified_count": modified,
                    "skipped_count": skipped,
                    "errors_count": len(errors),
                    "errors": errors,
                    "fields_unset": list(SAFE_FIELDS),
                    "rolled_back_at_utc": rolled_back_at,
                    "source_round": SOURCE_ROUND_TAG,
                },
            }
            await db.audit_log.insert_one(audit_event)
            return {
                "mode": "rollback_apply",
                "rollback_id": rollback_id,
                "rolled_back_at_utc": rolled_back_at,
                "total_entries": len(entries),
                "modified_count": modified,
                "skipped_count": skipped,
                "errors_count": len(errors),
                "audit_event_id": audit_event["id"],
            }
        finally:
            client.close()

    result = asyncio.run(_run())
    print(json.dumps(result, indent=2, default=str))
    if result["errors_count"] > 0 or result["skipped_count"] > 0:
        raise SystemExit(
            f"[ROLLBACK WARN] modified={result['modified_count']} "
            f"skipped={result['skipped_count']} errors={result['errors_count']}."
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="R18.3e Rollback Bridge — symmetric $unset of 5 SAFE bridge metadata fields"
    )
    parser.add_argument("--apply", action="store_true", help="Execute real rollback (requires ack)")
    parser.add_argument(
        "--i-understand-this-will-unset-bridge-metadata",
        dest="ack",
        action="store_true",
        help="Explicit ack flag (required with --apply)",
    )
    parser.add_argument("--json", action="store_true", help="Print report as JSON")
    args = parser.parse_args()

    if args.apply:
        apply_rollback(ack=args.ack)
        return 0

    report = dry_run()
    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print("=== R18.3e Rollback Bridge — Dry-Run Report ===")
        for k, v in report.items():
            print(f"  {k} = {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
