"""
🔒 R18.4 — Item Class-Bound Player-Facing — CLOSED & SEALED
R18.4 CLOSED & SEALED
DO NOT MODIFY. SHA256 verified in /app/backend/tests/backend_r18_4_sealed_integrity_test.py

ROUND 18.4 — Phase B3 REAL APPLY — item_binding_policy per catalog items
========================================================================

═══════════════════════════════════════════════════════════════════════
🚀 REAL APPLY SCRIPT — APPLY_ENABLED = True (autorizzato PM 2026-07-06)
🔒 Sibling del dry-run round18_4_apply_class_bound.py (LOCKED, byte-identical).
🔒 Doppio flag: --apply --i-understand-this-will-set-item-binding-policy-real
🔒 Guard hard-stop + backup snapshot + count match target 178 (11/146/21)
🔒 Idempotency: skip write se item_binding_policy già coincidente col target
═══════════════════════════════════════════════════════════════════════

**Status**: REAL APPLY. `APPLY_ENABLED = True`. Autorizzato da PM 2026-07-06.

**Purpose**:
    Applica `items.item_binding_policy` su tutti i 178 items catalog derivato dal
    bucket algorithm SQ6:
        Step 1: if required_class_optional populated → hard  (11 items)
        Step 2: if item_type in {material,material_continental,material_event,
                consumable} → universal (21 items)
        Step 3: else → soft (146 items)

**Prerequisito**: eseguito DOPO round18_4_backfill_slot_type_apply.py (ordine PM).

**Governance (LOCKED per R18.4 Phase B2 + B3 real apply GO)**:
    - APPLY_ENABLED=True (unico script del pair class_bound apply)
    - NO touch al dry-run script B3 (byte-identical)
    - NO modifica altri field oltre item_binding_policy
    - NO overwrite se già coincidente (idempotency)
    - NO touch ai 19 sigilli
    - Backup snapshot pre-apply obbligatorio
    - Audit event aggregato R18_4_ITEM_BINDING_POLICY_APPLIED
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ─── Hard governance flags ───────────────────────────────────────────────
APPLY_ENABLED: bool = True  # AUTORIZZATO PM 2026-07-06 (Real Apply)
SOURCE_ROUND_TAG: str = "R18.4 Phase B3 REAL APPLY"
REGISTRY_PATH = Path("/app/memory/r18_4_class_bound_registry.json")
DECISION_LOCK_PATH = Path("/app/memory/r18_4_phase_b2_pm_decisions.json")
BACKUPS_DIR = Path("/app/backend/backups")

# Expected target counts (LOCKED per PM)
EXPECTED_TARGET_TOTAL: int = 178
EXPECTED_HARD: int = 11
EXPECTED_UNIVERSAL: int = 21
EXPECTED_SOFT: int = 146

VALID_POLICY_VALUES: frozenset[str] = frozenset({"hard", "soft", "universal"})
UNIVERSAL_ITEM_TYPES: frozenset[str] = frozenset({
    "material", "material_continental", "material_event", "consumable",
})

BLOCKED_FIELDS: frozenset[str] = frozenset({
    "class_slug", "role", "primary_stat", "secondary_stats",
    "base_strength", "base_agility", "base_intellect", "base_endurance", "base_faith",
    "is_playable", "is_active", "is_canonical",
    "slot_type", "required_class_optional", "class_tags", "recommended_classes",
    "name", "display_name", "description", "slug",
    "specialization_unlocks", "item_type",
})
SAFE_FIELDS: tuple[str, ...] = ("item_binding_policy",)


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


def _guard_payload_hard_stop(payload: dict[str, Any], slug: str) -> None:
    keys = set(payload.keys())
    intersect_blocked = keys & BLOCKED_FIELDS
    if intersect_blocked:
        raise SystemExit(
            f"[GUARD FAIL-FAST] slug={slug!r} payload contains BLOCKED field(s): "
            f"{sorted(intersect_blocked)}"
        )
    extra = keys - set(SAFE_FIELDS)
    if extra:
        raise SystemExit(
            f"[GUARD FAIL-FAST] slug={slug!r} payload contains non-SAFE key(s): "
            f"{sorted(extra)}"
        )
    policy = payload.get("item_binding_policy")
    if policy not in VALID_POLICY_VALUES:
        raise SystemExit(
            f"[GUARD FAIL-FAST] slug={slug!r} invalid policy={policy!r}"
        )


def _derive_item_binding_policy(item: dict[str, Any]) -> str:
    """SQ6 locked derivation: hard > universal > soft."""
    req = item.get("required_class_optional")
    if req is not None and req != "" and req != []:
        return "hard"
    if item.get("item_type") in UNIVERSAL_ITEM_TYPES:
        return "universal"
    return "soft"


# ─── Backup snapshot ─────────────────────────────────────────────────────
async def _create_backup_snapshot(db, applied_at_utc: str) -> tuple[Path, str, int]:
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = applied_at_utc.replace(":", "").replace("-", "")
    backup_dir = BACKUPS_DIR / f"r18_4_class_bound_prepatch_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_file = backup_dir / "items_class_bound_snapshot.jsonl"

    count = 0
    with open(backup_file, "w", encoding="utf-8") as f:
        cursor = db.items.find(
            {},
            {
                "slug": 1, "id": 1, "item_type": 1,
                "item_binding_policy": 1, "required_class_optional": 1,
            },
        )
        async for doc in cursor:
            derived = _derive_item_binding_policy(doc)
            record = {
                "slug": doc.get("slug"),
                "id": doc.get("id"),
                "item_type": doc.get("item_type"),
                "required_class_optional": doc.get("required_class_optional"),
                "item_binding_policy_pre_state": doc.get("item_binding_policy"),
                "target_item_binding_policy": derived,
            }
            f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
            count += 1

    sha = hashlib.sha256(backup_file.read_bytes()).hexdigest()
    return backup_file, sha, count


# ─── Dry-run integrato ───────────────────────────────────────────────────
async def _dry_run_integrated(db) -> dict[str, Any]:
    would_modify = 0
    already_correct = 0
    breakdown: dict[str, int] = {"hard": 0, "soft": 0, "universal": 0}
    cursor = db.items.find(
        {},
        {"slug": 1, "item_type": 1, "required_class_optional": 1, "item_binding_policy": 1},
    )
    async for doc in cursor:
        target = _derive_item_binding_policy(doc)
        _guard_payload_hard_stop({"item_binding_policy": target}, doc.get("slug"))
        breakdown[target] += 1
        if doc.get("item_binding_policy") == target:
            already_correct += 1
        else:
            would_modify += 1
    return {
        "would_modify": would_modify,
        "already_correct": already_correct,
        "total_target": would_modify + already_correct,
        "breakdown_by_policy_target": breakdown,
    }


# ─── Real apply ──────────────────────────────────────────────────────────
async def _apply_real_async() -> dict[str, Any]:
    from motor.motor_asyncio import AsyncIOMotorClient

    _load_registry()
    _load_decision_lock()

    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        raise SystemExit("[FAIL-FAST] MONGO_URL/DB_NAME env vars missing")

    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    applied_at_utc = _now_utc_iso()
    apply_id = str(uuid.uuid4())

    try:
        # Step A: Backup snapshot
        backup_file, backup_sha, backup_count = await _create_backup_snapshot(db, applied_at_utc)
        if backup_count != EXPECTED_TARGET_TOTAL:
            raise SystemExit(
                f"[GUARD FAIL-FAST] Backup count drift: got {backup_count}, "
                f"expected {EXPECTED_TARGET_TOTAL}"
            )

        # Step B: Pre-apply dry-run (verify target breakdown match locked)
        dryrun = await _dry_run_integrated(db)
        if dryrun["total_target"] != EXPECTED_TARGET_TOTAL:
            raise SystemExit(
                f"[GUARD FAIL-FAST] Pre-apply dry-run total drift: "
                f"got {dryrun['total_target']}, expected {EXPECTED_TARGET_TOTAL}"
            )
        br = dryrun["breakdown_by_policy_target"]
        if not (br["hard"] == EXPECTED_HARD and br["universal"] == EXPECTED_UNIVERSAL
                and br["soft"] == EXPECTED_SOFT):
            raise SystemExit(
                f"[GUARD FAIL-FAST] Pre-apply breakdown drift: got {br}, "
                f"expected {{'hard':{EXPECTED_HARD}, 'universal':{EXPECTED_UNIVERSAL}, "
                f"'soft':{EXPECTED_SOFT}}}"
            )

        # Step C: Real apply
        modified = 0
        already_correct = 0
        skipped = 0
        errors: list[str] = []
        breakdown_applied: dict[str, int] = {"hard": 0, "soft": 0, "universal": 0}

        cursor = db.items.find(
            {},
            {"slug": 1, "item_type": 1, "required_class_optional": 1, "item_binding_policy": 1},
        )
        async for doc in cursor:
            slug = doc.get("slug")
            target = _derive_item_binding_policy(doc)
            payload = {"item_binding_policy": target}
            _guard_payload_hard_stop(payload, slug)
            current = doc.get("item_binding_policy")
            if current == target:
                already_correct += 1
                continue
            try:
                res = await db.items.update_one({"slug": slug}, {"$set": payload})
                if res.matched_count == 1 and res.modified_count == 1:
                    modified += 1
                    breakdown_applied[target] += 1
                elif res.matched_count == 1 and res.modified_count == 0:
                    already_correct += 1
                else:
                    skipped += 1
                    errors.append(f"slug={slug!r}: matched={res.matched_count}")
            except Exception as exc:
                errors.append(f"slug={slug!r}: {exc}")

        # Step D: Audit event
        audit_event = {
            "id": str(uuid.uuid4()),
            "event_type": "R18_4_ITEM_BINDING_POLICY_APPLIED",
            "created_at": applied_at_utc,
            "metadata": {
                "round": "R18.4",
                "phase": "B3 REAL APPLY",
                "apply_id": apply_id,
                "source_round": SOURCE_ROUND_TAG,
                "target_count_total": EXPECTED_TARGET_TOTAL,
                "target_count_hard": EXPECTED_HARD,
                "target_count_universal": EXPECTED_UNIVERSAL,
                "target_count_soft": EXPECTED_SOFT,
                "modified_count": modified,
                "already_correct_count": already_correct,
                "skipped_count": skipped,
                "errors_count": len(errors),
                "errors": errors,
                "breakdown_applied": breakdown_applied,
                "field_set": "item_binding_policy",
                "derivation_rule": "SQ6 locked: hard > universal > soft",
                "registry_sha256": _sha256_file(REGISTRY_PATH),
                "decision_lock_sha256": _sha256_file(DECISION_LOCK_PATH),
                "backup_snapshot_path": str(backup_file),
                "backup_snapshot_sha256": backup_sha,
                "backup_item_count": backup_count,
                "class_slug_migration": False,
                "class_tags_rewrite": False,
                "runtime_wiring": False,
                "item_rewrite": False,
                "hard_delete": False,
                "runtime_enforcement": False,
                "applied_at_utc": applied_at_utc,
            },
        }
        await db.audit_log.insert_one(audit_event)

        # Step E: Post-apply verify
        post_hard = await db.items.count_documents({"item_binding_policy": "hard"})
        post_soft = await db.items.count_documents({"item_binding_policy": "soft"})
        post_uni = await db.items.count_documents({"item_binding_policy": "universal"})
        post_null = await db.items.count_documents({
            "$or": [{"item_binding_policy": {"$exists": False}}, {"item_binding_policy": None}]
        })
        post_verify = {
            "post_hard": post_hard,
            "post_soft": post_soft,
            "post_universal": post_uni,
            "post_null_or_missing": post_null,
            "post_total_populated": post_hard + post_soft + post_uni,
            "verify_pass": (
                post_hard == EXPECTED_HARD
                and post_soft == EXPECTED_SOFT
                and post_uni == EXPECTED_UNIVERSAL
                and post_null == 0
            ),
        }

        return {
            "mode": "real_apply",
            "apply_enabled": APPLY_ENABLED,
            "apply_id": apply_id,
            "applied_at_utc": applied_at_utc,
            "source_round": SOURCE_ROUND_TAG,
            "registry_sha256": _sha256_file(REGISTRY_PATH),
            "decision_lock_sha256": _sha256_file(DECISION_LOCK_PATH),
            "backup_snapshot_path": str(backup_file),
            "backup_snapshot_sha256": backup_sha,
            "backup_item_count": backup_count,
            "target_count_total": EXPECTED_TARGET_TOTAL,
            "dryrun_pre_apply": dryrun,
            "modified_count": modified,
            "already_correct_count": already_correct,
            "skipped_count": skipped,
            "errors_count": len(errors),
            "errors": errors,
            "breakdown_applied": breakdown_applied,
            "post_apply_verify": post_verify,
            "audit_event_id": audit_event["id"],
            "audit_event_type": audit_event["event_type"],
        }
    finally:
        client.close()


def apply_real(ack: bool) -> dict[str, Any]:
    if not APPLY_ENABLED:
        raise SystemExit("[FAIL-FAST] Real apply BLOCKED. APPLY_ENABLED=False.")
    if not ack:
        raise SystemExit(
            "[FAIL-FAST] Missing acknowledgment flag "
            "`--i-understand-this-will-set-item-binding-policy-real`."
        )
    import asyncio
    return asyncio.run(_apply_real_async())


# ─── Rollback dry-run ────────────────────────────────────────────────────
async def _rollback_dry_run_async(backup_file: Path) -> dict[str, Any]:
    from motor.motor_asyncio import AsyncIOMotorClient
    if not backup_file.exists():
        raise SystemExit(f"[FAIL-FAST] Backup file not found: {backup_file}")
    entries: list[dict[str, Any]] = []
    with open(backup_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    try:
        found = 0
        would_restore = 0
        for e in entries:
            doc = await db.items.find_one({"slug": e["slug"]}, {"item_binding_policy": 1})
            if doc is None:
                continue
            found += 1
            if doc.get("item_binding_policy") == e.get("target_item_binding_policy"):
                would_restore += 1
        return {
            "mode": "rollback_dry_run",
            "backup_file": str(backup_file),
            "backup_entries_count": len(entries),
            "found_in_db": found,
            "would_restore_count": would_restore,
            "rollback_feasible": (found == len(entries)),
            "note": "Rollback dry-run only. Zero DB write.",
        }
    finally:
        client.close()


def rollback_dry_run(backup_file: Path) -> dict[str, Any]:
    import asyncio
    return asyncio.run(_rollback_dry_run_async(backup_file))


# ─── CLI ─────────────────────────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(
        description="R18.4 Phase B3 REAL APPLY — item_binding_policy"
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--i-understand-this-will-set-item-binding-policy-real",
        dest="ack", action="store_true",
    )
    parser.add_argument("--rollback-dry-run", action="store_true")
    parser.add_argument("--backup-file", type=str, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.rollback_dry_run:
        if not args.backup_file:
            raise SystemExit("[FAIL-FAST] --backup-file required for --rollback-dry-run")
        report = rollback_dry_run(Path(args.backup_file))
        print(json.dumps(report, indent=2, default=str))
        return 0

    if args.apply:
        report = apply_real(ack=args.ack)
        print(json.dumps(report, indent=2, default=str))
        return 0

    raise SystemExit(
        "[FAIL-FAST] No mode selected. Use --apply --i-understand-* or --rollback-dry-run."
    )


if __name__ == "__main__":
    sys.exit(main())
