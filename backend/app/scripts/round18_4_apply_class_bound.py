"""
ROUND 18.4 — Phase B3 Dry-Run — Apply item_binding_policy per catalog items
========================================================================

═══════════════════════════════════════════════════════════════════════
🔒 DRY-RUN DEFAULT — APPLY_ENABLED = False (LOCKED per R18.4 Phase B3)
🔒 Sibling script del registry documental-only /app/memory/r18_4_class_bound_registry.json
🔒 Non wired al runtime. Chiamato solo esplicitamente (python -m app.scripts.round18_4_apply_class_bound).
🔒 Doppio flag richiesto per real apply: --apply --i-understand-this-will-set-item-binding-policy
🔒 APPLY_ENABLED = True richiede nuovo PM gate esplicito post-review pre-report B3.
🔒 Guard hard-stop: rifiuta payload che contenga qualsiasi BLOCKED_FIELDS.
═══════════════════════════════════════════════════════════════════════

**Status**: DRY-RUN default. `APPLY_ENABLED = False` (LOCKED). Zero DB write.

**Purpose**:
    Genera il payload $set per l'aggiunta di `items.item_binding_policy` su
    tutti i 178 items del catalog, derivato dal bucket algorithm SQ6:

        Step 1: hard      → if required_class_optional populated
        Step 2: universal → if item_type in {material, material_continental,
                                              material_event, consumable}
        Step 3: soft      → else (residuo)

    Target counts locked in registry:
        hard: 11 · universal: 21 · soft: 146 · TOTAL: 178

**Governance (LOCKED per R18.4 Phase B2 PM decisions)**:
    - NO DB apply reale (APPLY_ENABLED=False)
    - NO overwrite di item_binding_policy già populated (SKIP se presente)
    - NO modifica altri field oltre item_binding_policy
    - NO enforcement runtime (solo catalog metadata)
    - NO audit event emesso in dry-run
    - NO touch ai 19 sigilli byte-identical

**Wired to runtime**: NO. Sibling script del registry documental-only R18.4 Phase B3.

**Usage**:
    Dry-run (default):
        python -m app.scripts.round18_4_apply_class_bound

    Real apply (BLOCKED — richiede doppio flag e nuovo gate PM):
        python -m app.scripts.round18_4_apply_class_bound --apply \\
            --i-understand-this-will-set-item-binding-policy

**Audit event atteso (NON emesso in dry-run)**:
    event_type: R18_4_ITEM_BINDING_POLICY_APPLIED
    aggregated: True (1 solo evento per l'intero apply)
    metadata:
        {
            "source_round": "R18.4 Phase B3",
            "apply_id": "<uuid4>",
            "docs_modified": <count>,
            "breakdown": {"hard":11,"soft":146,"universal":21},
            "registry_sha256": "<sha256>"
        }
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ─── Hard governance flags ───────────────────────────────────────────────
APPLY_ENABLED: bool = False  # LOCKED per R18.4 Phase B2. Richiede nuovo PM gate.
SOURCE_ROUND_TAG: str = "R18.4 Phase B3"
REGISTRY_PATH = Path("/app/memory/r18_4_class_bound_registry.json")
DECISION_LOCK_PATH = Path("/app/memory/r18_4_phase_b2_pm_decisions.json")

# Enum valori ammessi
VALID_POLICY_VALUES: frozenset[str] = frozenset({"hard", "soft", "universal"})

# Universal item types (SQ6 step 2)
UNIVERSAL_ITEM_TYPES: frozenset[str] = frozenset({
    "material",
    "material_continental",
    "material_event",
    "consumable",
})

# Blocked fields: fail-fast se presenti in payload
BLOCKED_FIELDS: frozenset[str] = frozenset({
    "class_slug",
    "role",
    "primary_stat",
    "secondary_stats",
    "base_strength",
    "base_agility",
    "base_intellect",
    "base_endurance",
    "base_faith",
    "is_playable",
    "is_active",
    "is_canonical",
    "slot_type",  # backfill separato (round18_4_backfill_slot_type.py)
    "required_class_optional",
    "class_tags",
    "recommended_classes",
    "name",
    "display_name",
    "description",
    "slug",
    "specialization_unlocks",
    "item_type",
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
    """Hard-stop guard: fail-fast su BLOCKED_FIELDS o chiavi non-SAFE."""
    keys = set(payload.keys())
    intersect_blocked = keys & BLOCKED_FIELDS
    if intersect_blocked:
        raise SystemExit(
            f"[GUARD FAIL-FAST] slug={slug!r} payload contains BLOCKED field(s): "
            f"{sorted(intersect_blocked)}. Payload keys: {sorted(keys)}"
        )
    extra = keys - set(SAFE_FIELDS)
    if extra:
        raise SystemExit(
            f"[GUARD FAIL-FAST] slug={slug!r} payload contains non-SAFE key(s): "
            f"{sorted(extra)}. Only SAFE_FIELDS={SAFE_FIELDS} are eligible."
        )
    policy = payload.get("item_binding_policy")
    if policy not in VALID_POLICY_VALUES:
        raise SystemExit(
            f"[GUARD FAIL-FAST] slug={slug!r} invalid item_binding_policy={policy!r}. "
            f"Must be one of {sorted(VALID_POLICY_VALUES)}."
        )


def _derive_item_binding_policy(item: dict[str, Any]) -> str:
    """SQ6 locked derivation: hard > universal > soft."""
    # Step 1: hard
    req = item.get("required_class_optional")
    if req is not None and req != "" and req != []:
        return "hard"
    # Step 2: universal
    it = item.get("item_type")
    if it in UNIVERSAL_ITEM_TYPES:
        return "universal"
    # Step 3: soft
    return "soft"


# ─── Main dry-run ────────────────────────────────────────────────────────
async def _dry_run_async() -> dict[str, Any]:
    from motor.motor_asyncio import AsyncIOMotorClient

    registry = _load_registry()
    _load_decision_lock()

    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        raise SystemExit("[FAIL-FAST] MONGO_URL/DB_NAME env vars missing")

    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    applied_at_utc = _now_utc_iso()
    report: dict[str, Any] = {
        "mode": "dry_run",
        "apply_enabled": APPLY_ENABLED,
        "source_round": SOURCE_ROUND_TAG,
        "registry_sha256": _sha256_file(REGISTRY_PATH),
        "decision_lock_sha256": _sha256_file(DECISION_LOCK_PATH),
        "would_apply_at_utc": applied_at_utc,
        "target_count_expected_total": 178,
        "target_count_expected_hard": 11,
        "target_count_expected_universal": 21,
        "target_count_expected_soft": 146,
        "would_modify_count": 0,
        "already_populated_skipped_count": 0,
        "errors_count": 0,
        "guard_hard_stop_checks_passed": 0,
        "breakdown_by_policy": {"hard": 0, "soft": 0, "universal": 0},
        "audit_event_would_emit": {
            "event_type": "R18_4_ITEM_BINDING_POLICY_APPLIED",
            "aggregated": True,
            "count_docs": 0,
            "actually_emitted": False,
        },
        "backup_snapshot_would_write": {
            "path_expected": f"/app/memory/r18_4_class_bound_pre_apply_snapshot_{applied_at_utc.replace(':', '').replace('-', '')}.json",
            "actually_written": False,
        },
        "payload_samples_per_policy": {"hard": [], "soft": [], "universal": []},
    }

    try:
        cursor = db.items.find(
            {},
            {"slug": 1, "item_type": 1, "required_class_optional": 1, "item_binding_policy": 1},
        )

        async for doc in cursor:
            slug = doc.get("slug")
            try:
                # Skip if already populated (no overwrite policy)
                if doc.get("item_binding_policy") in VALID_POLICY_VALUES:
                    report["already_populated_skipped_count"] += 1
                    continue

                policy = _derive_item_binding_policy(doc)
                payload = {"item_binding_policy": policy}
                _guard_payload_hard_stop(payload, slug)
                report["guard_hard_stop_checks_passed"] += 1

                report["would_modify_count"] += 1
                report["breakdown_by_policy"][policy] += 1

                samples = report["payload_samples_per_policy"][policy]
                if len(samples) < 3:
                    samples.append({"slug": slug, "item_type": doc.get("item_type"), "$set": payload})

            except SystemExit:
                raise
            except Exception as exc:  # noqa: BLE001
                report["errors_count"] += 1
                print(f"[ERROR] slug={slug!r}: {exc}", file=sys.stderr)

    finally:
        client.close()

    report["audit_event_would_emit"]["count_docs"] = report["would_modify_count"]

    # Verify breakdown matches expected
    br = report["breakdown_by_policy"]
    report["breakdown_matches_expected"] = (
        br["hard"] == 11 and br["universal"] == 21 and br["soft"] == 146
    )

    if not APPLY_ENABLED:
        report["real_apply_result"] = (
            "BLOCKED — APPLY_ENABLED=False (LOCKED per R18.4 Phase B2). "
            "Nuovo PM gate esplicito richiesto per flip."
        )

    return report


def dry_run() -> dict[str, Any]:
    import asyncio

    return asyncio.run(_dry_run_async())


def apply_real(ack: bool) -> None:
    if not APPLY_ENABLED:
        raise SystemExit(
            "[FAIL-FAST] Real apply BLOCKED. APPLY_ENABLED=False (LOCKED per R18.4 Phase B2).\n"
            "A new PM gate is required to flip APPLY_ENABLED to True. See\n"
            "/app/memory/r18_4_phase_b2_pm_decisions.md for governance."
        )
    if not ack:
        raise SystemExit(
            "[FAIL-FAST] Missing acknowledgment flag "
            "`--i-understand-this-will-set-item-binding-policy`."
        )
    raise SystemExit(
        "[NOT_IMPLEMENTED] Real apply body non implementato. "
        "Stub in attesa di PM gate + implementazione in round successivo."
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="R18.4 Phase B3 — Apply item_binding_policy dry-run script"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Attempt real apply (BLOCKED in R18.4 Phase B3 — requires new PM gate).",
    )
    parser.add_argument(
        "--i-understand-this-will-set-item-binding-policy",
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
        apply_real(ack=args.ack)
        return 0

    report = dry_run()
    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print("=== R18.4 Phase B3 — item_binding_policy Dry-Run Report ===")
        print(f"  mode                        = {report['mode']}")
        print(f"  apply_enabled               = {report['apply_enabled']}")
        print(f"  source_round                = {report['source_round']}")
        print(f"  registry_sha256             = {report['registry_sha256']}")
        print(f"  target_count_expected       = {report['target_count_expected_total']}")
        print(f"  would_modify_count          = {report['would_modify_count']}")
        print(f"  already_populated_skipped   = {report['already_populated_skipped_count']}")
        print(f"  guard_hard_stop_passed      = {report['guard_hard_stop_checks_passed']}")
        print(f"  breakdown_by_policy         = {report['breakdown_by_policy']}")
        print(f"  breakdown_matches_expected  = {report['breakdown_matches_expected']}")
        print(f"  audit_event.actually_emit   = {report['audit_event_would_emit']['actually_emitted']}")
        print(f"  backup_snapshot.actually_wr = {report['backup_snapshot_would_write']['actually_written']}")
        print(f"  real_apply_result           = {report.get('real_apply_result', 'n/a')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
