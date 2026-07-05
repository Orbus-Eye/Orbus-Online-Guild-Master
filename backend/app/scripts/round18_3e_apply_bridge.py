"""
ROUND 18.3e — Phase B Stage B2 — Legacy↔Canonical Bridge Dry-Run Script
========================================================================

**Status**: DRY-RUN ONLY. `APPLY_ENABLED = False`. Zero DB write.

**Purpose**:
    Genera il payload $set per 5 SAFE bridge metadata field su `adventurer_classes`
    docs (16 legacy + 2 canonical native = 18 doc totali), verifica il payload
    contro un hard-stop guard (13 field BLOCKED), e ritorna un report count.

**Governance (LOCKED per R18.3e Phase B — vedi /app/memory/r18_3e_phase_b_pm_decisions.md)**:
    - NO DB apply reale (bridge metadata)
    - NO migration class_slug
    - NO rewrite adventurers / items
    - NO modifica frontend label player-facing
    - NO unlock classi hidden
    - NO seed nuove classi
    - NO hard delete
    - NO audit event emesso in dry-run
    - NO touch ai 16 sigilli (14 R18.Reset.1b/1.2/1c + 2 R18.3d Phase B)

**Wired to runtime**: NO. Sibling script del registry documental-only R18.3e Phase B.

**Usage**:
    Dry-run (default):
        python -m app.scripts.round18_3e_apply_bridge

    Real apply (BLOCKED in this version — richiede doppio flag e nuovo gate PM):
        python -m app.scripts.round18_3e_apply_bridge --apply \
            --i-understand-this-will-write-bridge-metadata

    Il modulo rifiuta l'esecuzione reale a prescindere dal flag finché
    `APPLY_ENABLED = False`.

**Backup/Snapshot pre-apply**:
    Path atteso (NON creato in dry-run):
        /app/memory/r18_3e_bridge_pre_apply_snapshot_YYYYMMDDTHHMMSSZ.json

**Audit event atteso (NON emesso in dry-run)**:
    event_type: R18_3E_BRIDGE_METADATA_APPLIED
    aggregated: True (1 solo evento per l'intero apply, NO audit per-doc)
    metadata:
        {
            "source_round": "R18.3e Phase B",
            "apply_id": "<uuid4>",
            "docs_modified": 18,
            "safe_fields_applied": [...],
            "registry_sha256": "<sha256 of registry file>"
        }
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ─── Hard governance flags ───────────────────────────────────────────────
APPLY_ENABLED: bool = False  # Re-locked to False post-B2 apply (2026-07-05T19:45:31Z, apply_id=35302c0c-98dc-4b3b-b5b2-f1646540b74a). Was temporarily flipped to True for R18.3e B2 apply reale per PM GO.
SOURCE_ROUND_TAG: str = "R18.3e Phase B"
REGISTRY_PATH = Path("/app/memory/r18_3e_bridge_registry.json")
DECISION_LOCK_PATH = Path("/app/memory/r18_3e_phase_b_pm_decisions.json")

# 5 SAFE fields (only these are eligible for $set)
SAFE_FIELDS: tuple[str, ...] = (
    "canonical_slug",
    "alias_target",
    "bridge_status",
    "bridge_source_round",
    "bridge_applied_at",
)

# 15 BLOCKED fields (hard-stop: any presence in payload → fail-fast exit non-zero)
BLOCKED_FIELDS: frozenset[str] = frozenset({
    "class_slug",
    "display_name_it",
    "primary_stat",
    "secondary_stats",
    "role",
    "base_strength",
    "base_agility",
    "base_intellect",
    "base_endurance",
    "base_faith",
    "is_playable",
    "is_active",
    "is_canonical",
    "slug",   # applicative guard
    "name",   # applicative guard
})

# 7 valid bridge_status values
VALID_BRIDGE_STATUS: frozenset[str] = frozenset({
    "mapped_canonical",
    "mapped_alias",
    "deprecated_alias",
    "technical_placeholder",
    "test_artifact",
    "canonical_native",
    "ambiguous_pending_pm",
})


# ─── Helpers ─────────────────────────────────────────────────────────────
def _load_registry() -> dict[str, Any]:
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(f"Registry not found: {REGISTRY_PATH}")
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _load_decision_lock() -> dict[str, Any]:
    if not DECISION_LOCK_PATH.exists():
        raise FileNotFoundError(f"Decision lock not found: {DECISION_LOCK_PATH}")
    return json.loads(DECISION_LOCK_PATH.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_set_payload(entry: dict[str, Any], applied_at_utc: str) -> dict[str, Any]:
    """Costruisce il payload $set per una singola entry del registry.

    Deve contenere ESCLUSIVAMENTE i 5 SAFE_FIELDS. Nessun altro key.
    """
    return {
        "canonical_slug": entry.get("canonical_slug"),
        "alias_target": entry.get("alias_target"),
        "bridge_status": entry.get("bridge_status"),
        "bridge_source_round": SOURCE_ROUND_TAG,
        "bridge_applied_at": applied_at_utc,
    }


def _guard_payload_hard_stop(payload: dict[str, Any], slug: str) -> None:
    """Hard-stop guard: fail-fast se payload contiene qualsiasi BLOCKED field
    o qualsiasi key non in SAFE_FIELDS.
    """
    keys = set(payload.keys())
    # 1) forbidden fields
    intersect_blocked = keys & BLOCKED_FIELDS
    if intersect_blocked:
        raise SystemExit(
            f"[GUARD FAIL-FAST] slug={slug!r} payload contains BLOCKED field(s): "
            f"{sorted(intersect_blocked)}. Payload keys: {sorted(keys)}"
        )
    # 2) only SAFE fields allowed
    extra = keys - set(SAFE_FIELDS)
    if extra:
        raise SystemExit(
            f"[GUARD FAIL-FAST] slug={slug!r} payload contains non-SAFE key(s): "
            f"{sorted(extra)}. Only SAFE_FIELDS={SAFE_FIELDS} are eligible."
        )
    # 3) bridge_status enum validation
    bs = payload.get("bridge_status")
    if bs not in VALID_BRIDGE_STATUS:
        raise SystemExit(
            f"[GUARD FAIL-FAST] slug={slug!r} invalid bridge_status={bs!r}. "
            f"Must be one of {sorted(VALID_BRIDGE_STATUS)}."
        )
    # 4) bridge_source_round must be the LOCKED tag
    if payload.get("bridge_source_round") != SOURCE_ROUND_TAG:
        raise SystemExit(
            f"[GUARD FAIL-FAST] slug={slug!r} bridge_source_round tag drift: "
            f"got {payload.get('bridge_source_round')!r}, expected {SOURCE_ROUND_TAG!r}."
        )


def _validate_canonical_slug_reference(
    entry: dict[str, Any], canonical_set: set[str]
) -> None:
    """Assicura che canonical_slug (se non None) sia uno dei 27 canonical IT."""
    cs = entry.get("canonical_slug")
    if cs is not None and cs not in canonical_set:
        raise SystemExit(
            f"[GUARD FAIL-FAST] slug={entry['slug']!r} canonical_slug={cs!r} "
            f"is NOT in the canonical 27 IT set."
        )
    at = entry.get("alias_target")
    if at is not None and at not in canonical_set:
        # alias_target CAN be a canonical or (in future) a legacy slug; for
        # R18.3e v1 all alias_target values are canonical, so we enforce it.
        raise SystemExit(
            f"[GUARD FAIL-FAST] slug={entry['slug']!r} alias_target={at!r} "
            f"is NOT in the canonical 27 IT set (v1 constraint)."
        )


# ─── Main dry-run ────────────────────────────────────────────────────────
def dry_run() -> dict[str, Any]:
    """Esegue il dry-run: costruisce i payload $set per tutte le 18 entries,
    applica i guard, e ritorna un report count. **Zero DB write.**
    """
    registry = _load_registry()
    _load_decision_lock()  # side-effect: verify decision lock exists + parses

    canonical_set: set[str] = set(registry["canonical_it_set_27_locked"])
    assert len(canonical_set) == 27, "Canonical IT set must contain exactly 27 slugs"

    entries: list[dict[str, Any]] = registry["bridge_entries"]
    assert len(entries) == 18, "Bridge registry must contain exactly 18 entries"

    applied_at_utc = _now_utc_iso()
    report: dict[str, Any] = {
        "mode": "dry_run",
        "apply_enabled": APPLY_ENABLED,
        "source_round": SOURCE_ROUND_TAG,
        "registry_sha256": _sha256_file(REGISTRY_PATH),
        "decision_lock_sha256": _sha256_file(DECISION_LOCK_PATH),
        "would_apply_at_utc": applied_at_utc,
        "total_entries": len(entries),
        "would_modify_count": 0,
        "skipped_count": 0,
        "errors_count": 0,
        "guard_hard_stop_checks_passed": 0,
        "canonical_slug_ref_checks_passed": 0,
        "audit_event_would_emit": {
            "event_type": "R18_3E_BRIDGE_METADATA_APPLIED",
            "aggregated": True,
            "count_docs": 0,  # populated below
            "actually_emitted": False,
        },
        "backup_snapshot_would_write": {
            "path_expected": f"/app/memory/r18_3e_bridge_pre_apply_snapshot_{applied_at_utc.replace(':', '').replace('-', '')}.json",
            "actually_written": False,
        },
        "breakdown_by_bridge_status": {},
        "payload_samples": [],
    }

    for entry in entries:
        slug = entry.get("slug")
        try:
            _validate_canonical_slug_reference(entry, canonical_set)
            report["canonical_slug_ref_checks_passed"] += 1

            payload = _build_set_payload(entry, applied_at_utc)
            _guard_payload_hard_stop(payload, slug)
            report["guard_hard_stop_checks_passed"] += 1

            report["would_modify_count"] += 1
            bs = entry.get("bridge_status", "?")
            report["breakdown_by_bridge_status"][bs] = (
                report["breakdown_by_bridge_status"].get(bs, 0) + 1
            )
            if len(report["payload_samples"]) < 3:
                report["payload_samples"].append({"slug": slug, "$set": payload})
        except SystemExit:
            raise
        except Exception as exc:  # noqa: BLE001
            report["errors_count"] += 1
            print(f"[ERROR] slug={slug!r}: {exc}", file=sys.stderr)

    report["audit_event_would_emit"]["count_docs"] = report["would_modify_count"]

    # Enforce apply_enabled=False even if flags are passed
    if not APPLY_ENABLED:
        report["real_apply_result"] = "BLOCKED — APPLY_ENABLED=False (LOCKED per R18.3e Phase B)"

    return report


def apply_real(ack: bool) -> None:
    """Reale $set apply dei 5 SAFE bridge metadata field su 18 doc adventurer_classes.

    Guards obbligatori (fail-fast se falliscono):
    - target_count == 18
    - canonical_native_count == 2
    - legacy_count == 16
    - Registry parsabile
    - Mapping completo
    - Rollback script presente

    Emette 1 solo audit event aggregato R18_3E_BRIDGE_METADATA_APPLIED (NO per-doc).
    """
    import asyncio
    import os
    import uuid
    from datetime import datetime, timezone

    from dotenv import load_dotenv
    from motor.motor_asyncio import AsyncIOMotorClient

    if not APPLY_ENABLED:
        raise SystemExit(
            "[FAIL-FAST] Real apply BLOCKED. APPLY_ENABLED=False (LOCKED per R18.3e Phase B).\n"
            "A new PM gate is required to flip APPLY_ENABLED to True. See\n"
            "/app/memory/r18_3e_phase_b_pm_decisions.md for governance."
        )
    if not ack:
        raise SystemExit(
            "[FAIL-FAST] Missing acknowledgment flag "
            "`--i-understand-this-will-write-bridge-metadata`."
        )

    # Load registry + decision lock (raises if missing/unparsable)
    registry = _load_registry()
    _load_decision_lock()

    entries: list[dict[str, Any]] = registry["bridge_entries"]
    canonical_set: set[str] = set(registry["canonical_it_set_27_locked"])

    # Guard 1: target_count == 18
    if len(entries) != 18:
        raise SystemExit(
            f"[GUARD FAIL-FAST] target_count drift: {len(entries)} != 18. Aborting apply."
        )

    # Guard 2/3: canonical_native == 2 AND legacy == 16
    canonical_native = [e for e in entries if e.get("bridge_status") == "canonical_native"]
    non_native = [e for e in entries if e.get("bridge_status") != "canonical_native"]
    if len(canonical_native) != 2:
        raise SystemExit(
            f"[GUARD FAIL-FAST] canonical_native_count drift: {len(canonical_native)} != 2."
        )
    if len(non_native) != 16:
        raise SystemExit(
            f"[GUARD FAIL-FAST] legacy_count drift: {len(non_native)} != 16."
        )

    # Guard 4: canonical_slug references point to canonical 27 (or null)
    for e in entries:
        _validate_canonical_slug_reference(e, canonical_set)

    # Guard 5: rollback script presente (sibling)
    rollback_path = Path("/app/backend/app/scripts/round18_3e_rollback_bridge.py")
    if not rollback_path.exists():
        raise SystemExit(
            f"[GUARD FAIL-FAST] Rollback script missing at {rollback_path}. "
            f"Refusing to apply without symmetric rollback available."
        )

    # Guard 6: backup snapshot pre-apply presente
    backups_dir = Path("/app/backend/backups")
    prepatch_dirs = list(backups_dir.glob("r18_3e_bridge_prepatch_*"))
    if not prepatch_dirs:
        raise SystemExit(
            f"[GUARD FAIL-FAST] No pre-apply backup snapshot found under {backups_dir}."
        )
    latest_backup = max(prepatch_dirs, key=lambda p: p.stat().st_mtime)
    backup_file = latest_backup / "adventurer_classes.jsonl"
    if not backup_file.exists():
        raise SystemExit(
            f"[GUARD FAIL-FAST] Backup file missing: {backup_file}"
        )

    applied_at_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    apply_id = str(uuid.uuid4())

    async def _run_apply() -> dict[str, Any]:
        load_dotenv("/app/backend/.env")
        client = AsyncIOMotorClient(os.environ["MONGO_URL"])
        try:
            db = client[os.environ["DB_NAME"]]
            modified = 0
            skipped = 0
            errors: list[str] = []
            for entry in entries:
                slug = entry["slug"]
                payload = _build_set_payload(entry, applied_at_utc)
                # Pre-write guard (defense-in-depth)
                _guard_payload_hard_stop(payload, slug)
                try:
                    res = await db.adventurer_classes.update_one(
                        {"slug": slug}, {"$set": payload}
                    )
                    if res.matched_count == 1:
                        modified += 1
                    else:
                        skipped += 1
                        errors.append(
                            f"slug={slug!r}: matched={res.matched_count}, modified={res.modified_count}"
                        )
                except Exception as exc:
                    errors.append(f"slug={slug!r}: {exc}")

            # Emit 1 aggregated audit event
            audit_event = {
                "id": str(uuid.uuid4()),
                "event_type": "R18_3E_BRIDGE_METADATA_APPLIED",
                "created_at": applied_at_utc,
                "metadata": {
                    "round": "R18.3e",
                    "phase": "B",
                    "apply_id": apply_id,
                    "target_count": len(entries),
                    "legacy_count": 16,
                    "canonical_native_count": 2,
                    "modified_count": modified,
                    "skipped_count": skipped,
                    "errors_count": len(errors),
                    "errors": errors,
                    "fields_set": list(SAFE_FIELDS),
                    "registry_sha256": _sha256_file(REGISTRY_PATH),
                    "decision_lock_sha256": _sha256_file(DECISION_LOCK_PATH),
                    "backup_snapshot_path": str(backup_file),
                    "migration_slug_rewrite": False,
                    "runtime_wiring": False,
                    "item_rewrite": False,
                    "adventurer_rewrite": False,
                    "applied_at_utc": applied_at_utc,
                    "source_round": SOURCE_ROUND_TAG,
                },
            }
            await db.audit_log.insert_one(audit_event)

            return {
                "mode": "apply",
                "apply_id": apply_id,
                "applied_at_utc": applied_at_utc,
                "total_entries": len(entries),
                "modified_count": modified,
                "skipped_count": skipped,
                "errors_count": len(errors),
                "errors": errors,
                "audit_event_id": audit_event["id"],
                "audit_event_type": audit_event["event_type"],
                "backup_snapshot_used": str(backup_file),
            }
        finally:
            client.close()

    result = asyncio.run(_run_apply())
    print(json.dumps(result, indent=2, default=str))
    if result["errors_count"] > 0 or result["skipped_count"] > 0:
        raise SystemExit(
            f"[APPLY WARN] modified={result['modified_count']} "
            f"skipped={result['skipped_count']} errors={result['errors_count']}. "
            f"See audit event {result['audit_event_id']} for details."
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="R18.3e Phase B — Legacy↔Canonical Bridge Dry-Run Script"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Attempt real apply (BLOCKED in R18.3e Phase B — requires new PM gate).",
    )
    parser.add_argument(
        "--i-understand-this-will-write-bridge-metadata",
        dest="ack",
        action="store_true",
        help="Explicit ack flag (required together with --apply).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the dry-run report as JSON to stdout.",
    )
    args = parser.parse_args()

    if args.apply:
        # apply_real will always raise SystemExit while APPLY_ENABLED=False
        apply_real(ack=args.ack)
        return 0

    # Default: dry-run
    report = dry_run()
    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print("=== R18.3e Phase B — Dry-Run Report ===")
        print(f"  mode                        = {report['mode']}")
        print(f"  apply_enabled               = {report['apply_enabled']}")
        print(f"  source_round                = {report['source_round']}")
        print(f"  registry_sha256             = {report['registry_sha256']}")
        print(f"  decision_lock_sha256        = {report['decision_lock_sha256']}")
        print(f"  total_entries               = {report['total_entries']}")
        print(f"  would_modify_count          = {report['would_modify_count']}")
        print(f"  skipped_count               = {report['skipped_count']}")
        print(f"  errors_count                = {report['errors_count']}")
        print(f"  guard_hard_stop_passed      = {report['guard_hard_stop_checks_passed']}")
        print(f"  canonical_slug_ref_passed   = {report['canonical_slug_ref_checks_passed']}")
        print(f"  breakdown_by_bridge_status  = {report['breakdown_by_bridge_status']}")
        print(f"  audit_event.actually_emit   = {report['audit_event_would_emit']['actually_emitted']}")
        print(f"  backup_snapshot.actually_wr = {report['backup_snapshot_would_write']['actually_written']}")
        print(f"  real_apply_result           = {report.get('real_apply_result', 'n/a')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
