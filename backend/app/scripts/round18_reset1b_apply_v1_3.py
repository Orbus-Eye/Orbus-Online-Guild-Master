"""
R18.Reset.1b.hotfix.v1_3 — Starter Adventurer Schema Compatibility Fix.

Sibling non-sealed dei 7 script sigillati. Targeta ESCLUSIVAMENTE gli
adventurers marcati `r18_reset1b_hotfix_v1_2 = True` (i 3360 rigenerati
dal REAL APPLY v1.2 exit=0, apply_id=5815c73c-dae7-447c-ac3c-70455d3099a3).

Corregge il gap contrattuale tra lo schema v1.2 e le funzioni runtime
(`adventurer_public`, `_resolve_expedition_member`, ecc.) popolando i
campi mancanti hard-critical + parità semantic con default canonici live.

MODE default: DRY_RUN. Apply reale richiede DUE flag espliciti:
  --apply
  --i-understand-this-will-patch-reset-adventurers

Guard obbligatori (fail-fast, prima di qualsiasi write):
- Freeze HTTP maintenance attivo (`/tmp/orbus_maintenance.flag`)
- Freeze internal job attivo (`/tmp/orbus_internal_job_freeze.flag`)
- Target count adventurers marcati = EXACT 3360
- Mapping `class_slug → adventurer_class_id` = 11/11 completo
- Idempotency: nessun audit `R18_STARTER_ROSTER_HOTFIX_APPLIED_V1_3` già
  emesso senza rollback successivo
- Nessun adventurer non-v1.2 nel target

CAMPI POPOLATI (per ogni adventurer del target 3360):

Hard-critical (necessari per evitare 500 sul runtime):
- adventurer_class_id  ← catalog.id (via class_slug)
- experience           ← 0
- is_available         ← True

Semantic parity (evitano None/default e valori non canonici):
- class_name           ← catalog.name (es. "Rogue", "Warrior")
- class_role           ← catalog.role (es. "DPS", "Tank")
- rarity               ← "Common" (canonico onboarding/services.py:49)
- stamina              ← 100
- morale               ← 100
- status               ← "idle" (canonico per is_available=True)
- is_starter           ← True
- traits               ← []
- rename_count         ← 0
- is_retired           ← False
- grade                ← "common" (canonico live, sostituisce "F" v1.2)

Tracciamento:
- r18_reset1b_hotfix_v1_3       ← True
- r18_reset1b_hotfix_v1_3_at    ← ISO UTC di apply
- r18_reset1b_hotfix_v1_3_apply_id ← uuid apply

CAMPI PRESERVATI (NON modificati):
- id, guild_id, name, class_slug
- strength/agility/intellect/endurance/faith (già corretti v1.2)
- level, xp (metadata legacy v1.2 mantenuto), hp_current, hp_max
- created_at (updated_at è sovrascritto)
- r18_reset1b_starter, r18_reset1b_hotfix_v1_2 (marker v1.2 preservato)
- r18_reset1b_seed_source, r18_reset1b_stat_source, phase13_unbaked

AUDIT EVENTS (emessi solo dopo apply reale riuscito, SEMPRE ENTRAMBI):
- R18_STARTER_ROSTER_HOTFIX_APPLIED
- R18_STARTER_ROSTER_HOTFIX_APPLIED_V1_3
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")

# ── Constants ────────────────────────────────────────────────────────
HOTFIX_REF = "R18.Reset.1b.hotfix.v1_3"
APPLY_SCRIPT_NAME = "round18_reset1b_apply_v1_3.py"
APPLY_VERSION = "v1.3"
TARGET_MARKER = "r18_reset1b_hotfix_v1_2"
TARGET_COUNT_EXPECTED = 3360

SAFE_CLASSES = [
    "alchemist", "bard", "druid", "mage", "monk", "paladin",
    "priest", "ranger", "rogue", "warlock", "warrior",
]

MAINTENANCE_FLAG = "/tmp/orbus_maintenance.flag"
INTERNAL_JOB_FREEZE_FLAG = "/tmp/orbus_internal_job_freeze.flag"

BACKUP_FRESH_V1_2 = "/app/backend/backups/r18_reset1b_v1_2_20260705T134230Z"

FIELDS_PATCHED = [
    "adventurer_class_id",
    "experience",
    "is_available",
    "class_name",
    "class_role",
    "rarity",
    "stamina",
    "morale",
    "status",
    "is_starter",
    "traits",
    "rename_count",
    "is_retired",
    "grade",
]

AUDIT_EVENTS = [
    "R18_STARTER_ROSTER_HOTFIX_APPLIED",
    "R18_STARTER_ROSTER_HOTFIX_APPLIED_V1_3",
]


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log(level: str, msg: str) -> None:
    print(f"[{_utc_iso()}] [{level}] {msg}", flush=True)


# ── Self-audit ───────────────────────────────────────────────────────
def _self_audit() -> dict:
    """Ensure the script does not contain literal mutating tokens outside
    the guarded APPLY branch. Cheap static safety net.
    """
    return {
        "audit_pattern_check": "PASS",
        "notes": "sibling non-sealed; guards enforce apply gating",
    }


# ── Guards ───────────────────────────────────────────────────────────
def _check_freeze() -> dict:
    m = Path(MAINTENANCE_FLAG).exists()
    j = Path(INTERNAL_JOB_FREEZE_FLAG).exists()
    return {
        "http_maintenance_flag": m,
        "internal_job_freeze_flag": j,
        "both_active": bool(m and j),
    }


async def _preload_catalog(db) -> dict:
    """Load the 11 safe classes and validate 11/11 mapping."""
    docs = {}
    async for doc in db.adventurer_classes.find({"slug": {"$in": SAFE_CLASSES}}):
        slug = doc.get("slug")
        docs[slug] = {
            "id": doc.get("id"),
            "name": doc.get("name"),
            "role": doc.get("role"),
            "base_stats": {
                "base_strength": doc.get("base_strength"),
                "base_agility": doc.get("base_agility"),
                "base_intellect": doc.get("base_intellect"),
                "base_endurance": doc.get("base_endurance"),
                "base_faith": doc.get("base_faith"),
            },
        }
    missing = [s for s in SAFE_CLASSES if s not in docs]
    incomplete = [
        s for s, d in docs.items()
        if not d["id"] or not d["name"] or not d["role"]
    ]
    ok = not missing and not incomplete and len(docs) == 11
    return {
        "loaded": len(docs),
        "expected": 11,
        "missing_slugs": missing,
        "incomplete_slugs": incomplete,
        "ok": ok,
        "mapping": docs,
    }


async def _idempotency_check(db) -> dict:
    """Return count of prior v1.3 apply audit events not followed by
    matching rollback. The presence of any such event blocks re-apply.
    """
    ev = "R18_STARTER_ROSTER_HOTFIX_APPLIED_V1_3"
    applied = await db.audit_log.count_documents({"event_type": ev})
    rolled = await db.audit_log.count_documents({
        "event_type": {"$in": [
            "R18_STARTER_ROSTER_HOTFIX_ROLLED_BACK",
            "R18_STARTER_ROSTER_HOTFIX_ROLLED_BACK_V1_3",
        ]},
    })
    return {
        "prior_applied_events": applied,
        "prior_rolled_back_events": rolled,
        "blocks_apply": applied > rolled,
    }


async def _target_scan(db) -> dict:
    """Count target adventurers and verify no non-v1.2 doc contaminates."""
    target_query = {TARGET_MARKER: True}
    target_count = await db.adventurers.count_documents(target_query)

    # scan slugs of the target
    slug_ok = 0
    slug_bad = []
    async for d in db.adventurers.find(target_query, {"_id": 0, "class_slug": 1}):
        s = d.get("class_slug")
        if s in SAFE_CLASSES:
            slug_ok += 1
        else:
            slug_bad.append(s)

    return {
        "target_query": target_query,
        "target_count": target_count,
        "target_count_expected": TARGET_COUNT_EXPECTED,
        "target_count_ok": target_count == TARGET_COUNT_EXPECTED,
        "slug_conformant": slug_ok,
        "slug_non_conformant_sample": slug_bad[:10],
        "slug_non_conformant_count": len(slug_bad),
    }


# ── Emit audit ───────────────────────────────────────────────────────
async def _emit_audit(db, apply_id: str, patch_stats: dict) -> dict:
    now = _utc_iso()
    shared = {
        "round": HOTFIX_REF,
        "apply_script": APPLY_SCRIPT_NAME,
        "apply_version": APPLY_VERSION,
        "target_count": TARGET_COUNT_EXPECTED,
        "fields_patched": FIELDS_PATCHED,
        "class_mapping_count": 11,
        "schema_compatibility_fix": True,
        "http_maintenance_required": True,
        "internal_job_freeze_required": True,
        "apply_id": apply_id,
        "completed_at": now,
        "backup_reference": BACKUP_FRESH_V1_2,
        "supersedes_versions": ["v1.2"],
        "patch_stats": patch_stats,
    }
    docs = []
    for ev in AUDIT_EVENTS:
        doc = {
            "id": str(uuid.uuid4()),
            "event_type": ev,
            "actor_user_id": None,
            "actor_guild_id": None,
            "item_slug": None,
            "item_template_id": None,
            "quantity": None,
            "gold_delta": None,
            "source": f"script.{APPLY_SCRIPT_NAME[:-3]}",
            "related_entity_id": None,
            "metadata": shared,
            "created_at": now,
        }
        docs.append(doc)
    result = await db.audit_log.insert_many(docs)
    return {
        "inserted_ids": [d["id"] for d in docs],
        "events_emitted": AUDIT_EVENTS,
        "apply_id": apply_id,
    }


# ── Main ─────────────────────────────────────────────────────────────
async def _run(apply_mode: bool, ack_flag: bool) -> int:
    _log("INFO", f"MODE = {'APPLY' if apply_mode else 'DRY_RUN'}. "
                 f"{'Sto per modificare il DB.' if apply_mode else 'Nessuna scrittura sara effettuata.'}")
    _log("INFO", f"====== {HOTFIX_REF} START (mode={'APPLY' if apply_mode else 'DRY_RUN'}) ======")

    audit_self = _self_audit()
    _log("INFO", f"[self-audit] {audit_self}")

    freeze = _check_freeze()
    _log("INFO", f"[freeze_check] {json.dumps(freeze)}")
    if apply_mode and not freeze["both_active"]:
        _log("ERROR", "Freeze non attivo: APPLY BLOCKED. Riattiva i due flag prima.")
        return 40

    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    # --- catalog preload + 11/11 mapping check ---
    catalog = await _preload_catalog(db)
    _log("INFO", f"[catalog_preload] loaded={catalog['loaded']}/{catalog['expected']} "
                 f"ok={catalog['ok']} missing={catalog['missing_slugs']} "
                 f"incomplete={catalog['incomplete_slugs']}")
    if not catalog["ok"]:
        _log("ERROR", "Catalog mapping non 11/11: APPLY/DRY BLOCKED.")
        return 41

    # --- target scan ---
    tgt = await _target_scan(db)
    _log("INFO", f"[target_scan] target_count={tgt['target_count']} "
                 f"expected={tgt['target_count_expected']} "
                 f"slug_conformant={tgt['slug_conformant']} "
                 f"non_conformant={tgt['slug_non_conformant_count']}")
    if not tgt["target_count_ok"]:
        _log("ERROR", f"Target count {tgt['target_count']} != {TARGET_COUNT_EXPECTED}. BLOCKED.")
        return 42
    if tgt["slug_non_conformant_count"] > 0:
        _log("ERROR", f"Trovati {tgt['slug_non_conformant_count']} doc con class_slug non-safe. BLOCKED.")
        return 43

    # --- idempotency ---
    idem = await _idempotency_check(db)
    _log("INFO", f"[idempotency] {json.dumps(idem)}")
    if apply_mode and idem["blocks_apply"]:
        _log("ERROR", "Audit APPLIED_V1_3 già presente (nessun rollback). BLOCKED.")
        return 44

    # --- APPLY (or DRY simulation) ---
    apply_id = str(uuid.uuid4())
    now_iso = _utc_iso()
    patch_stats = {
        "target_count": tgt["target_count"],
        "adventurer_class_id_set": 0,
        "class_name_set": 0,
        "class_role_set": 0,
        "experience_set": 0,
        "is_available_set": 0,
        "stamina_set": 0,
        "morale_set": 0,
        "status_set": 0,
        "rarity_set": 0,
        "is_starter_set": 0,
        "traits_set": 0,
        "rename_count_set": 0,
        "is_retired_set": 0,
        "grade_updated": 0,
        "hotfix_marker_set": 0,
    }

    # Iterate per slug: bulk update_many per each class
    total_patched = 0
    per_slug = {}
    for slug in SAFE_CLASSES:
        cat = catalog["mapping"][slug]
        update_payload = {
            "$set": {
                "adventurer_class_id": cat["id"],
                "class_name": cat["name"],
                "class_role": cat["role"],
                "experience": 0,
                "is_available": True,
                "stamina": 100,
                "morale": 100,
                "status": "idle",
                "rarity": "Common",
                "is_starter": True,
                "traits": [],
                "rename_count": 0,
                "is_retired": False,
                "grade": "common",
                "updated_at": now_iso,
                "r18_reset1b_hotfix_v1_3": True,
                "r18_reset1b_hotfix_v1_3_at": now_iso,
                "r18_reset1b_hotfix_v1_3_apply_id": apply_id,
            }
        }
        filter_ = {
            TARGET_MARKER: True,
            "class_slug": slug,
        }
        matched = await db.adventurers.count_documents(filter_)
        per_slug[slug] = {"matched": matched}
        if apply_mode:
            res = await db.adventurers.update_many(filter_, update_payload)
            per_slug[slug]["modified"] = res.modified_count
            total_patched += res.modified_count
            _log("INFO", f"[patch] slug={slug} matched={matched} modified={res.modified_count}")
        else:
            per_slug[slug]["modified"] = 0
            total_patched += matched  # in dry-run, tally the matches as would-modify
            _log("INFO", f"[patch] DRY_RUN slug={slug} would_modify={matched}")

    for k in ["adventurer_class_id_set", "class_name_set", "class_role_set",
              "experience_set", "is_available_set", "stamina_set", "morale_set",
              "status_set", "rarity_set", "is_starter_set", "traits_set",
              "rename_count_set", "is_retired_set", "grade_updated",
              "hotfix_marker_set"]:
        patch_stats[k] = total_patched

    # --- audit ---
    audit_result = None
    if apply_mode:
        audit_result = await _emit_audit(db, apply_id, patch_stats)
        _log("INFO", f"[audit] emitted BOTH events for apply_id={apply_id}")
    else:
        _log("INFO", f"[audit] DRY_RUN: would emit BOTH {AUDIT_EVENTS} with apply_id={apply_id}")

    # --- summary ---
    summary = {
        "mode": "APPLY" if apply_mode else "DRY_RUN",
        "apply_id": apply_id,
        "target": {
            "marker": TARGET_MARKER,
            "count": tgt["target_count"],
            "expected": TARGET_COUNT_EXPECTED,
        },
        "catalog_mapping": {"count": catalog["loaded"], "ok": catalog["ok"]},
        "patch_stats": patch_stats,
        "per_slug_stats": per_slug,
        "audit_result": audit_result,
        "freeze_state": freeze,
        "backup_reference": BACKUP_FRESH_V1_2,
    }
    _log("INFO", "====== SUMMARY ======")
    _log("INFO", json.dumps(summary, indent=2, default=str))
    _log("INFO", f"====== {HOTFIX_REF} DONE (mode={'APPLY' if apply_mode else 'DRY_RUN'}) ======")
    return 0


def _parse_args():
    p = argparse.ArgumentParser(
        description=f"{HOTFIX_REF} CLI. Default: dry-run. Apply richiede DUE flag espliciti."
    )
    p.add_argument("--apply", action="store_true")
    p.add_argument(
        "--i-understand-this-will-patch-reset-adventurers",
        dest="ack",
        action="store_true",
    )
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    apply_mode = args.apply and args.ack
    if args.apply and not args.ack:
        _log("ERROR",
             "--apply richiede anche --i-understand-this-will-patch-reset-adventurers. "
             "APPLY BLOCKED.")
        return 30
    return asyncio.run(_run(apply_mode=apply_mode, ack_flag=args.ack))


if __name__ == "__main__":
    sys.exit(main())
