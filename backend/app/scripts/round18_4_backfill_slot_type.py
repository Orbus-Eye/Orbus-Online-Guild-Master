"""
ROUND 18.4 — Phase B3 Dry-Run — Backfill slot_type per items catalog
========================================================================

═══════════════════════════════════════════════════════════════════════
🔒 DRY-RUN DEFAULT — APPLY_ENABLED = False (LOCKED per R18.4 Phase B3)
🔒 Sibling script del registry documental-only /app/memory/r18_4_class_bound_registry.json
🔒 Non wired al runtime. Chiamato solo esplicitamente (python -m app.scripts.round18_4_backfill_slot_type).
🔒 Doppio flag richiesto per real apply: --apply --i-understand-this-will-backfill-slot-type
🔒 APPLY_ENABLED = True richiede nuovo PM gate esplicito post-review pre-report B3.
🔒 Guard hard-stop: rifiuta payload che contenga qualsiasi BLOCKED_FIELDS.
═══════════════════════════════════════════════════════════════════════

**Status**: DRY-RUN default. `APPLY_ENABLED = False` (LOCKED). Zero DB write.

**Purpose**:
    Genera il payload $set per il backfill di `items.slot_type` sui 140 items
    equipabili con slot_type null/missing. Mapping SQ1(a):
        weapon    → slot_type = "weapon"
        armor     → slot_type = "armor"
        accessory → slot_type = "accessory"
        shield    → slot_type = "armor"     (SQ1 opzione a locked)

**Governance (LOCKED per R18.4 Phase B2 PM decisions)**:
    - NO DB apply reale (APPLY_ENABLED=False)
    - NO overwrite di slot_type già populated (SKIP 17 items)
    - NO touch a materials/consumables (out of scope)
    - NO modifica altri field oltre slot_type
    - NO audit event emesso in dry-run
    - NO touch ai 19 sigilli byte-identical

**Wired to runtime**: NO. Sibling script del registry documental-only R18.4 Phase B3.

**Usage**:
    Dry-run (default):
        python -m app.scripts.round18_4_backfill_slot_type

    Real apply (BLOCKED in this version — richiede doppio flag e nuovo gate PM):
        python -m app.scripts.round18_4_backfill_slot_type --apply \\
            --i-understand-this-will-backfill-slot-type

    Il modulo rifiuta l'esecuzione reale a prescindere dal flag finché
    `APPLY_ENABLED = False`.

**Audit event atteso (NON emesso in dry-run)**:
    event_type: R18_4_SLOT_TYPE_BACKFILL_APPLIED
    aggregated: True (1 solo evento per l'intero apply, NO audit per-doc)
    metadata:
        {
            "source_round": "R18.4 Phase B3",
            "apply_id": "<uuid4>",
            "docs_modified": <count>,
            "mapping_applied": {"weapon":"weapon","armor":"armor",...,"shield":"armor"},
            "registry_sha256": "<sha256 of registry file>"
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

# Slot type mapping locked (SQ1 opzione a)
SLOT_TYPE_MAPPING: dict[str, str] = {
    "weapon": "weapon",
    "armor": "armor",
    "accessory": "accessory",
    "shield": "armor",  # SQ1(a) locked: shield → armor
}

# Equipable item_types eligibili al backfill
EQUIPABLE_ITEM_TYPES: frozenset[str] = frozenset(SLOT_TYPE_MAPPING.keys())

# Blocked fields: qualsiasi presenza in payload → fail-fast
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
    "item_binding_policy",  # backfill separato (round18_4_apply_class_bound.py)
    "required_class_optional",
    "class_tags",
    "recommended_classes",
    "name",
    "display_name",
    "description",
    "slug",  # never touch slug
})

# Solo SAFE_FIELD ammesso in $set payload
SAFE_FIELDS: tuple[str, ...] = ("slot_type",)


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
    """Hard-stop guard: fail-fast se payload contiene qualsiasi BLOCKED field
    o key non in SAFE_FIELDS.
    """
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
    # slot_type value validation
    st = payload.get("slot_type")
    if st not in {"weapon", "armor", "accessory"}:
        raise SystemExit(
            f"[GUARD FAIL-FAST] slug={slug!r} invalid slot_type={st!r}. "
            f"Must be one of {{'weapon','armor','accessory'}}."
        )


def _derive_slot_type(item_type: str) -> str:
    """Deriva slot_type dal mapping SQ1(a) locked."""
    if item_type not in SLOT_TYPE_MAPPING:
        raise SystemExit(
            f"[GUARD FAIL-FAST] item_type={item_type!r} not in EQUIPABLE_ITEM_TYPES. "
            f"Backfill scope: {sorted(EQUIPABLE_ITEM_TYPES)}"
        )
    return SLOT_TYPE_MAPPING[item_type]


# ─── Main dry-run ────────────────────────────────────────────────────────
async def _dry_run_async() -> dict[str, Any]:
    """Esegue il dry-run: legge items live, costruisce payload per ogni target,
    applica guard, ritorna report count. **Zero DB write.**
    """
    from motor.motor_asyncio import AsyncIOMotorClient

    registry = _load_registry()
    _load_decision_lock()  # side-effect: verify decision lock exists + parses

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
        "target_count_expected": 140,
        "would_modify_count": 0,
        "skipped_count": 0,
        "errors_count": 0,
        "guard_hard_stop_checks_passed": 0,
        "breakdown_by_item_type": {},
        "breakdown_by_target_slot_type": {},
        "shield_mapped_to_armor_slugs": [],
        "audit_event_would_emit": {
            "event_type": "R18_4_SLOT_TYPE_BACKFILL_APPLIED",
            "aggregated": True,
            "count_docs": 0,
            "actually_emitted": False,
        },
        "backup_snapshot_would_write": {
            "path_expected": f"/app/memory/r18_4_slot_type_pre_apply_snapshot_{applied_at_utc.replace(':', '').replace('-', '')}.json",
            "actually_written": False,
        },
        "payload_samples": [],
    }

    try:
        # Filter: slot_type is null/missing AND item_type in equipable
        cursor = db.items.find(
            {
                "item_type": {"$in": list(EQUIPABLE_ITEM_TYPES)},
                "$or": [{"slot_type": {"$exists": False}}, {"slot_type": None}],
            },
            {"slug": 1, "item_type": 1},
        )

        async for doc in cursor:
            slug = doc.get("slug")
            item_type = doc.get("item_type")
            try:
                target_slot_type = _derive_slot_type(item_type)
                payload = {"slot_type": target_slot_type}
                _guard_payload_hard_stop(payload, slug)
                report["guard_hard_stop_checks_passed"] += 1

                report["would_modify_count"] += 1
                report["breakdown_by_item_type"][item_type] = (
                    report["breakdown_by_item_type"].get(item_type, 0) + 1
                )
                report["breakdown_by_target_slot_type"][target_slot_type] = (
                    report["breakdown_by_target_slot_type"].get(target_slot_type, 0) + 1
                )
                if item_type == "shield":
                    report["shield_mapped_to_armor_slugs"].append(slug)

                if len(report["payload_samples"]) < 5:
                    report["payload_samples"].append(
                        {"slug": slug, "item_type": item_type, "$set": payload}
                    )
            except SystemExit:
                raise
            except Exception as exc:  # noqa: BLE001
                report["errors_count"] += 1
                print(f"[ERROR] slug={slug!r}: {exc}", file=sys.stderr)

    finally:
        client.close()

    report["audit_event_would_emit"]["count_docs"] = report["would_modify_count"]

    if not APPLY_ENABLED:
        report["real_apply_result"] = (
            "BLOCKED — APPLY_ENABLED=False (LOCKED per R18.4 Phase B2). "
            "Nuovo PM gate esplicito richiesto per flip."
        )

    return report


def dry_run() -> dict[str, Any]:
    """Sync wrapper attorno a _dry_run_async."""
    import asyncio

    return asyncio.run(_dry_run_async())


def apply_real(ack: bool) -> None:
    """Reale $set apply del backfill slot_type.

    Guards obbligatori (fail-fast):
    - APPLY_ENABLED == True (attualmente False → BLOCKED)
    - ack flag esplicito richiesto
    - Registry parsabile
    - Decision lock parsabile
    """
    if not APPLY_ENABLED:
        raise SystemExit(
            "[FAIL-FAST] Real apply BLOCKED. APPLY_ENABLED=False (LOCKED per R18.4 Phase B2).\n"
            "A new PM gate is required to flip APPLY_ENABLED to True. See\n"
            "/app/memory/r18_4_phase_b2_pm_decisions.md for governance."
        )
    if not ack:
        raise SystemExit(
            "[FAIL-FAST] Missing acknowledgment flag "
            "`--i-understand-this-will-backfill-slot-type`."
        )
    # Se APPLY_ENABLED viene flippato in un futuro round (con PM GO), la logica
    # reale di apply andrà implementata qui: legge il dry-run report, esegue
    # update_many con $set slot_type, emette audit event aggregato,
    # scrive backup snapshot pre-apply.
    raise SystemExit(
        "[NOT_IMPLEMENTED] Real apply body non implementato. "
        "Stub in attesa di PM gate + implementazione in round successivo."
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="R18.4 Phase B3 — Backfill slot_type dry-run script"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Attempt real apply (BLOCKED in R18.4 Phase B3 — requires new PM gate).",
    )
    parser.add_argument(
        "--i-understand-this-will-backfill-slot-type",
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
        # apply_real solleva sempre SystemExit finché APPLY_ENABLED=False
        apply_real(ack=args.ack)
        return 0

    # Default: dry-run
    report = dry_run()
    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print("=== R18.4 Phase B3 — Backfill slot_type Dry-Run Report ===")
        print(f"  mode                        = {report['mode']}")
        print(f"  apply_enabled               = {report['apply_enabled']}")
        print(f"  source_round                = {report['source_round']}")
        print(f"  registry_sha256             = {report['registry_sha256']}")
        print(f"  decision_lock_sha256        = {report['decision_lock_sha256']}")
        print(f"  target_count_expected       = {report['target_count_expected']}")
        print(f"  would_modify_count          = {report['would_modify_count']}")
        print(f"  guard_hard_stop_passed      = {report['guard_hard_stop_checks_passed']}")
        print(f"  breakdown_by_item_type      = {report['breakdown_by_item_type']}")
        print(f"  breakdown_by_target_slot    = {report['breakdown_by_target_slot_type']}")
        print(f"  shield_to_armor_mapped      = {len(report['shield_mapped_to_armor_slugs'])} slugs")
        print(f"  audit_event.actually_emit   = {report['audit_event_would_emit']['actually_emitted']}")
        print(f"  backup_snapshot.actually_wr = {report['backup_snapshot_would_write']['actually_written']}")
        print(f"  real_apply_result           = {report.get('real_apply_result', 'n/a')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
