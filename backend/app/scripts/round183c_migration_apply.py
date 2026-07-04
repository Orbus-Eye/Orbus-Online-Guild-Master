"""ROUND 18.3c — Orphan Class Migration APPLY (mode `adventurer_class_slug_only`).

Migra i 496 adventurer legacy verso i 5 target canonici. **Zero touch al catalog
`adventurer_classes` in questo round** — mode split R18.3b/R18.3b.1 pending
per stat/role enum reconciliation.

Mapping (esatto, non traducibile):
    priest     → paladin                (190 adv)
    ranger     → cacciatore_di_mostri   (175 adv)
    warlock    → cacciatore_del_vuoto   (128 adv)
    berserker  → warrior                (3 adv)
    assassin   → rogue                  (0 adv)
    TOTAL: 496

Per ogni adventurer migrato (`$set`):
    class_slug            = <target>
    class_name            = <target.display_name_it>  # one-shot lookup catalog
    previous_class_slug   = <source>
    migration_round       = "R18.3c"
    migration_reason      = "orphan_legacy_class_canonicalization"
    migration_timestamp   = <ISO UTC>

E `$push` su embedded array `career_history`:
    {event: "class_migration", round: "R18.3c",
     from: <source>, to: <target>, timestamp: <ISO UTC>}

Vincoli assoluti rispettati:
  - `role`, `class_role`, `primary_stat`, `secondary_stats` sull'adventurer:
    **NON toccati** (mantengono valore recruit-frozen o null preesistente).
  - `level`, `experience`, `xp`, `grade`, `equipment`, `inventory`, `traits`,
    `stamina`, `morale`, `base_*` stats, gold, dungeon/raid history:
    **NON toccati**.
  - Catalog `adventurer_classes`: **NESSUNA scrittura** in questo script.

Idempotente: seconda esecuzione = 0 nuove modifiche (skip su adventurer con
`migration_round=R18.3c` già presente).

Uso:
    python -m app.scripts.round183c_migration_apply --dry-run
    python -m app.scripts.round183c_migration_apply --apply
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


MIGRATION_MAP: dict[str, dict] = {
    "priest":    {"target": "paladin",              "expected": 190},
    "ranger":    {"target": "cacciatore_di_mostri", "expected": 175},
    "warlock":   {"target": "cacciatore_del_vuoto", "expected": 128},
    "berserker": {"target": "warrior",              "expected": 3},
    "assassin":  {"target": "rogue",                "expected": 0},
}

TOTAL_EXPECTED = 496
AUDIT_EVENT_TYPE = "R18_CLASS_ORPHAN_MIGRATION_APPLIED"


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _preflight(db) -> dict:
    """Verifica precondizioni. Fermarsi se anche 1 fallisce."""
    checks = {"pass": True, "errors": []}
    # 1. Count per source slug
    counts = {}
    for src, info in MIGRATION_MAP.items():
        n = await db.adventurers.count_documents({"class_slug": src})
        counts[src] = n
        if n != info["expected"]:
            checks["errors"].append(
                f"count mismatch {src}: expected {info['expected']}, got {n}"
            )
            checks["pass"] = False
    checks["counts_by_source"] = counts
    checks["counts_total"] = sum(counts.values())
    if checks["counts_total"] != TOTAL_EXPECTED:
        checks["errors"].append(
            f"total mismatch: expected {TOTAL_EXPECTED}, got {checks['counts_total']}"
        )
        checks["pass"] = False

    # 2. Target catalog exists + dispatch-valid
    for src, info in MIGRATION_MAP.items():
        target = info["target"]
        cls = await db.adventurer_classes.find_one({"slug": target})
        if not cls:
            checks["errors"].append(f"target class {target} missing from catalog")
            checks["pass"] = False
            continue
        # Whitelist R18.1.2 guard: target must be dispatch-valid
        is_playable_ok = cls.get("is_playable") is not False
        is_whitelisted = (
            cls.get("is_playable") is False
            and cls.get("migration_target_only") is True
            and target in ("cacciatore_di_mostri", "cacciatore_del_vuoto")
        )
        if not (is_playable_ok or is_whitelisted):
            checks["errors"].append(
                f"target {target} not dispatch-valid via R18.1.2 guard"
            )
            checks["pass"] = False

    # 3. Item pool >0 per i 2 target R18.3a
    for target in ("cacciatore_di_mostri", "cacciatore_del_vuoto"):
        n = await db.items.count_documents({"recommended_classes": target})
        checks[f"item_pool_{target}"] = n
        if n <= 0:
            checks["errors"].append(f"item pool {target} = {n} (must be > 0)")
            checks["pass"] = False

    return checks


async def _apply_migration(db, dry_run: bool) -> dict:
    """Applica la migration idempotente."""
    result = {
        "mode": "adventurer_class_slug_only",
        "dry_run": dry_run,
        "by_source": {},
        "applied_total": 0,
        "skipped_total": 0,
    }
    display_names = {}
    for src, info in MIGRATION_MAP.items():
        target = info["target"]
        cls = await db.adventurer_classes.find_one(
            {"slug": target}, {"_id": 0, "display_name_it": 1, "name": 1}
        )
        display_names[target] = (
            cls.get("display_name_it") or cls.get("name") or target
        )

    for src, info in MIGRATION_MAP.items():
        target = info["target"]
        target_display = display_names[target]

        # Idempotency: skip adventurer già migrato R18.3c
        query_new = {"class_slug": src, "migration_round": {"$ne": "R18.3c"}}
        query_all = {"class_slug": src}

        n_all = await db.adventurers.count_documents(query_all)
        n_to_migrate = await db.adventurers.count_documents(query_new)
        n_already = n_all - n_to_migrate

        if dry_run:
            result["by_source"][src] = {
                "target": target,
                "target_display_it": target_display,
                "n_source_total": n_all,
                "n_already_migrated_r18_3c": n_already,
                "n_would_migrate": n_to_migrate,
                "action": "dry-run",
            }
            result["applied_total"] += n_to_migrate
            continue

        # APPLY
        now_iso = _utc_iso()
        career_event = {
            "event": "class_migration",
            "round": "R18.3c",
            "from": src,
            "to": target,
            "timestamp": now_iso,
        }
        # Uso update_many per performance (idempotent because query filters
        # `migration_round != R18.3c`).
        # Nota importante: NON tocchiamo `class_role`, `primary_stat`,
        # `secondary_stats`, base_*, level, experience, xp, grade, equipment,
        # inventory, traits — solo class_slug + class_name + metadata.
        res = await db.adventurers.update_many(
            query_new,
            {
                "$set": {
                    "class_slug": target,
                    "class_name": target_display,
                    "previous_class_slug": src,
                    "migration_round": "R18.3c",
                    "migration_reason": "orphan_legacy_class_canonicalization",
                    "migration_timestamp": now_iso,
                    "updated_at": now_iso,
                },
                "$push": {
                    "career_history": career_event,
                },
            },
        )
        result["by_source"][src] = {
            "target": target,
            "target_display_it": target_display,
            "n_source_total": n_all,
            "n_already_migrated_r18_3c": n_already,
            "modified": res.modified_count,
            "matched": res.matched_count,
            "action": "applied",
        }
        result["applied_total"] += res.modified_count
        result["skipped_total"] += n_already

    return result


async def _post_verify(db) -> dict:
    """Verifica post-apply: 0 orphan residui, count target incrementati."""
    verify = {"pass": True, "errors": []}
    residual = {}
    for src in MIGRATION_MAP.keys():
        # Solo assassin ha expected=0 pre-apply; per gli altri, residual deve
        # essere == n_already_migrated (che potrebbe non essere 0 se re-run).
        # Idempotent: dopo apply, class_slug=src implica migration_round=R18.3c
        # per gli adv già migrati? NO, migrated adv hanno class_slug=target.
        # Quindi residual class_slug=src DEVE essere 0.
        n = await db.adventurers.count_documents({"class_slug": src})
        residual[src] = n
        if n != 0:
            verify["errors"].append(f"residual {src}: {n} (must be 0 post-apply)")
            verify["pass"] = False
    verify["residual_by_source"] = residual

    # Target count grew
    target_counts = {}
    for info in MIGRATION_MAP.values():
        t = info["target"]
        n = await db.adventurers.count_documents({"class_slug": t})
        target_counts[t] = n
    verify["target_counts"] = target_counts

    # Migrated count with metadata
    n_migrated = await db.adventurers.count_documents({"migration_round": "R18.3c"})
    verify["migrated_r18_3c_count"] = n_migrated
    if n_migrated != TOTAL_EXPECTED:
        verify["errors"].append(
            f"migrated count {n_migrated} != expected {TOTAL_EXPECTED}"
        )
        verify["pass"] = False

    return verify


async def _emit_audit(db, result: dict, verify: dict) -> str:
    """Idempotent emit audit event."""
    existing = await db.audit_log.count_documents({"event_type": AUDIT_EVENT_TYPE})
    if existing >= 1:
        return "skip-idempotent"
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()),
        "event_type": AUDIT_EVENT_TYPE,
        "actor_user_id": None,
        "actor_guild_id": None,
        "item_slug": None,
        "source": "script.round183c_migration_apply",
        "metadata": {
            "round": "R18.3c",
            "mode": "adventurer_class_slug_only",
            "dry_run_count": TOTAL_EXPECTED,
            "applied_count": result["applied_total"],
            "skipped_count": result["skipped_total"],
            "catalog_role_stat_updates": False,
            "mapping": {
                src: info["target"] for src, info in MIGRATION_MAP.items()
            },
            "rollback_ready": True,
            "rollback_script_path": (
                "app.scripts.round183c_migration_rollback"
            ),
            "player_banner_enabled": True,
            "backup_path": "/app/memory/backups/round183c_prestart/",
            "enum_conflict_deferred_to": "R18.3b.1",
            "residual_check": verify.get("residual_by_source"),
            "target_counts_post_apply": verify.get("target_counts"),
            "feature_flag_R18_REWORK_ENABLED": os.environ.get(
                "R18_REWORK_ENABLED"
            ),
        },
        "created_at": _utc_iso(),
    })
    return "inserted"


async def run(dry_run: bool) -> int:
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    mode = "DRY-RUN" if dry_run else "APPLY"
    print(f"[mode] {mode} · round=R18.3c orphan-class-migration "
          f"mode=adventurer_class_slug_only")
    print(f"[safety] catalog `adventurer_classes` NON toccato in questo round\n")

    # Idempotency short-circuit: se già migrato R18.3c, no-op
    n_already_migrated = await db.adventurers.count_documents(
        {"migration_round": "R18.3c"}
    )
    if n_already_migrated == TOTAL_EXPECTED:
        print(f"[idempotent] {n_already_migrated} adventurers already migrated "
              f"in R18.3c — no-op")
        # Verify residual = 0
        residual = {}
        for src in MIGRATION_MAP.keys():
            residual[src] = await db.adventurers.count_documents(
                {"class_slug": src}
            )
        print(f"[idempotent] residual by source: {residual}")
        if all(v == 0 for v in residual.values()):
            print(f"[idempotent] SAFE — no re-apply needed")
            return 0
        else:
            print(f"[warn] residual sources present but full migration count "
                  f"reached — check DB state")
            return 5

    # Preflight
    print("[preflight] checking preconditions...")
    checks = await _preflight(db)
    print(f"[preflight] {json.dumps(checks, indent=2, default=str)}")
    if not checks["pass"]:
        print(f"\n[FAIL] preflight errors: {checks['errors']}", file=sys.stderr)
        return 3
    print(f"[preflight] OK · total {checks['counts_total']} adv to migrate\n")

    # Apply
    result = await _apply_migration(db, dry_run=dry_run)
    print(f"\n[result] {json.dumps(result, indent=2, default=str)}")

    if dry_run:
        print("\n[dry-run] no changes committed. re-run with --apply.")
        return 0

    # Post-verify
    verify = await _post_verify(db)
    print(f"\n[post-verify] {json.dumps(verify, indent=2, default=str)}")
    if not verify["pass"]:
        print(f"[WARN] post-verify errors: {verify['errors']}", file=sys.stderr)

    # Audit
    audit_result = await _emit_audit(db, result, verify)
    print(f"\n[audit] event {AUDIT_EVENT_TYPE}: {audit_result}")

    return 0 if verify["pass"] else 4


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
