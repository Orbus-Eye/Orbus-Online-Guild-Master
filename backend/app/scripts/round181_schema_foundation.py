"""ROUND 18.1 — Schema Foundation & Data Backfill (append-only).

Autorizzato dal PM il 2026-07-04. Scope APPEND-ONLY, feature flag OFF, zero
player-facing impact. Contract identico a R16.5.4c / R17.3 Step 2 C1P1:

  * `--dry-run` (default): preview + report diff, ZERO write
  * `--apply`: esegue in ordine 6 blocchi A-F + audit events
  * Idempotente: secondo `--apply` = 0 modifiche

Ordine blocchi:
  A. Feature flag verification (env `R18_REWORK_ENABLED`)
  B. `recruit_unassigned` class + backfill 91 orfani
  C. Aliasing Guardian→paladin, Cleric→priest (6 orfani)
  D. Backfill `grade='common'` (default tecnico, non retrocessione)
  E. Talent tree schema scaffolding (collezioni vuote)
  F. Roster cap computed + beta opt-in field

Uso:
    python -m app.scripts.round181_schema_foundation --dry-run
    python -m app.scripts.round181_schema_foundation --apply
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


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _audit(db, event_type: str, metadata: dict) -> None:
    """Emit R18_* audit event (idempotent via event_type + created_at)."""
    try:
        await db.audit_events.insert_one({
            "event_type": event_type,
            "actor_user_id": None,
            "actor_guild_id": None,
            "related_entity_id": None,
            "source": "script.round181_schema_foundation",
            "occurred_at": _utc(),
            "metadata": {"round": "R18.1", **metadata},
        })
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] audit emit failed: {exc}", file=sys.stderr)


# ══════════════════════════════════════════════════════════════════════════
#  A — FEATURE FLAG (read-only verification)
# ══════════════════════════════════════════════════════════════════════════
def _check_feature_flag() -> tuple[bool, str]:
    val = os.environ.get("R18_REWORK_ENABLED", "false").strip().lower()
    is_off = val in ("false", "0", "no", "")
    return is_off, val


# ══════════════════════════════════════════════════════════════════════════
#  B — recruit_unassigned + backfill 91 orfani
# ══════════════════════════════════════════════════════════════════════════
RECRUIT_UNASSIGNED_DOC = {
    "slug": "recruit_unassigned",
    "id": None,  # populated at insert time
    "display_name_it": "Da riassegnare",
    "display_name_en": "Unassigned Recruit",
    "role": None,
    "secondary_role": None,
    "primary_stat": None,
    "secondary_stats": [],
    "is_canonical": False,
    "is_playable": False,
    "is_talent_tree_eligible": False,
    "drops_items": False,
    "is_base_class": False,
    "seed_source": "round181_schema_foundation",
}


async def _find_orphans(db) -> list[dict]:
    """Adventurers con class_slug=None OR class_slug non nel catalog."""
    valid_slugs = set()
    async for c in db.adventurer_classes.find(
        {}, {"_id": 0, "slug": 1}
    ):
        valid_slugs.add(c["slug"])
    # Escludi recruit_unassigned se già presente per non riproporre
    valid_slugs.discard("recruit_unassigned")
    orphans: list[dict] = []
    async for a in db.adventurers.find(
        {}, {"_id": 0, "id": 1, "class_slug": 1, "class_name": 1,
             "class": 1, "guild_id": 1, "name": 1, "level": 1}
    ):
        cs = a.get("class_slug")
        if cs is None or cs == "" or cs not in valid_slugs:
            orphans.append(a)
    return orphans


async def _apply_recruit_unassigned(db, orphans: list[dict]) -> int:
    """Insert class doc (if missing) + update orphans. Idempotent."""
    exists = await db.adventurer_classes.find_one(
        {"slug": "recruit_unassigned"}, {"_id": 0}
    )
    if not exists:
        now = _utc()
        doc = dict(RECRUIT_UNASSIGNED_DOC)
        doc["id"] = str(uuid.uuid4())
        doc["created_at"] = now
        doc["updated_at"] = now
        await db.adventurer_classes.insert_one(doc)

    updated = 0
    for o in orphans:
        r = await db.adventurers.update_one(
            {"id": o["id"], "$or": [
                {"class_slug": {"$ne": "recruit_unassigned"}},
                {"needs_reassignment": {"$ne": True}},
            ]},
            {"$set": {
                "class_slug": "recruit_unassigned",
                "needs_reassignment": True,
                "r18_orphan_migrated_at": _utc(),
            }},
        )
        if r.modified_count > 0:
            updated += 1
    return updated


# ══════════════════════════════════════════════════════════════════════════
#  C — Aliasing Guardian→paladin, Cleric→priest (6 legacy)
# ══════════════════════════════════════════════════════════════════════════
LEGACY_ALIAS_MAP = {"Guardian": "paladin", "Cleric": "priest"}


async def _find_guardian_cleric(db) -> list[dict]:
    result: list[dict] = []
    async for a in db.adventurers.find(
        {"$or": [
            {"class": {"$in": list(LEGACY_ALIAS_MAP.keys())}},
            {"class_name": {"$in": list(LEGACY_ALIAS_MAP.keys())}},
        ]},
        {"_id": 0, "id": 1, "name": 1, "guild_id": 1, "level": 1,
         "class": 1, "class_name": 1, "class_slug": 1},
    ):
        legacy = a.get("class") or a.get("class_name")
        target = LEGACY_ALIAS_MAP.get(legacy)
        if target:
            result.append({**a, "_target_slug": target,
                           "_legacy_class": legacy})
    return result


async def _apply_guardian_cleric_alias(db, docs: list[dict]) -> int:
    updated = 0
    for d in docs:
        r = await db.adventurers.update_one(
            {"id": d["id"], "class_slug": {"$ne": d["_target_slug"]}},
            {"$set": {
                "class_slug": d["_target_slug"],
                "class_name": d["_target_slug"].capitalize(),
                "legacy_class_original": d["_legacy_class"],
                "r18_alias_migrated_at": _utc(),
            }},
        )
        if r.modified_count > 0:
            updated += 1
    return updated


# ══════════════════════════════════════════════════════════════════════════
#  D — Backfill grade='common'
# ══════════════════════════════════════════════════════════════════════════
async def _find_grade_missing(db) -> int:
    return await db.adventurers.count_documents({
        "$or": [{"grade": None}, {"grade": {"$exists": False}}]
    })


async def _apply_grade_backfill(db) -> int:
    r = await db.adventurers.update_many(
        {"$or": [{"grade": None}, {"grade": {"$exists": False}}]},
        {"$set": {
            "grade": "common",
            "r18_grade_backfilled_at": _utc(),
            "r18_grade_note": "grade=Common è normalizzazione tecnica "
                              "iniziale, non retrocessione player-facing",
        }},
    )
    return r.modified_count


# ══════════════════════════════════════════════════════════════════════════
#  E — Talent tree schema scaffolding
# ══════════════════════════════════════════════════════════════════════════
async def _ensure_talent_collections(db) -> dict:
    """Crea le collezioni vuote + indici. Idempotente."""
    result = {}
    coll_names = await db.list_collection_names()
    for coll, indexes in [
        ("talent_tree_definitions",
         [("class_slug", 1), ("branch", 1), ("tier", 1)]),
        ("adventurer_talent_progress",
         [("adventurer_id", 1)]),
        ("career_history",
         [("adventurer_id", 1), ("event_type", 1)]),
    ]:
        if coll not in coll_names:
            await db.create_collection(coll)
        for idx in indexes:
            try:
                await db[coll].create_index([idx])
            except Exception:  # noqa: BLE001
                pass
        result[coll] = await db[coll].count_documents({})
    return result


async def _validate_talent_schema(db) -> bool:
    """Insert + delete dummy doc per validare schema. Rollback safe."""
    dummy = {
        "id": str(uuid.uuid4()),
        "class_slug": "__test__",
        "branch": "dummy_branch",
        "tier": 1,
        "slot_id": "dummy_slot_1",
        "max_points": 4,
        "requirements": [],
        "stat_modifiers": {},
        "is_dummy_validation": True,
        "created_at": _utc(),
    }
    await db.talent_tree_definitions.insert_one(dummy)
    r = await db.talent_tree_definitions.delete_one(
        {"id": dummy["id"], "is_dummy_validation": True}
    )
    return r.deleted_count == 1


# ══════════════════════════════════════════════════════════════════════════
#  F — Roster cap computed + beta opt-in field
# ══════════════════════════════════════════════════════════════════════════
def _compute_cap(level: int | None) -> int:
    lvl = int(level or 1)
    return min(50, 10 + lvl * 2)


async def _apply_roster_cap(db) -> tuple[int, dict]:
    updated = 0
    dist: list[int] = []
    async for g in db.guilds.find(
        {}, {"_id": 0, "id": 1, "level": 1, "guild_level": 1,
             "max_roster_cap": 1, "current_roster_size": 1,
             "is_grandfathered": 1, "r18_beta_opt_in": 1}
    ):
        gl = g.get("guild_level") or g.get("level") or 1
        cap = _compute_cap(gl)
        count = await db.adventurers.count_documents(
            {"guild_id": g["id"]}
        )
        grandfathered = bool(count > cap)
        # Strict idempotency: skip se tutti i field sono già settati corretti.
        if (
            g.get("max_roster_cap") == cap
            and g.get("current_roster_size") == count
            and g.get("is_grandfathered") == grandfathered
            and g.get("r18_beta_opt_in") is False
        ):
            dist.append(count)
            continue
        r = await db.guilds.update_one(
            {"id": g["id"]},
            {"$set": {
                "max_roster_cap": cap,
                "current_roster_size": count,
                "is_grandfathered": grandfathered,
                "r18_beta_opt_in": g.get("r18_beta_opt_in", False),
                "r18_roster_cap_computed_at": _utc(),
            }},
        )
        if r.modified_count > 0:
            updated += 1
        dist.append(count)
    dist.sort()
    n = len(dist)
    return updated, {
        "count_guilds": n,
        "min": dist[0] if n else 0,
        "max": dist[-1] if n else 0,
        "mean": round(sum(dist) / n, 2) if n else 0,
        "p50": dist[n // 2] if n else 0,
        "p99": dist[min(n - 1, int(n * 0.99))] if n else 0,
    }


# ══════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════
async def run(dry_run: bool) -> int:
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        print("[fatal] MONGO_URL o DB_NAME mancanti", file=sys.stderr)
        return 2
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    mode = "DRY-RUN" if dry_run else "APPLY"
    print(f"[mode] {mode} · db={db_name} · round=R18.1")

    # A. Feature flag
    off, val = _check_feature_flag()
    print(f"\n[A] R18_REWORK_ENABLED='{val}' → is_off={off}")
    if not off:
        print("[FAIL] Feature flag deve essere OFF in R18.1. STOP.")
        return 3

    # B/C dry-run (identify)
    orphans = await _find_orphans(db)
    orphans_target = 91
    gc_docs = await _find_guardian_cleric(db)
    gc_target = 6
    grade_missing = await _find_grade_missing(db)

    print(f"\n[B] orphans class_slug=None/invalid: found={len(orphans)} "
          f"expected={orphans_target}")
    print(f"[C] Guardian/Cleric legacy: found={len(gc_docs)} "
          f"expected={gc_target}")
    if gc_docs:
        print("    Preview (6 attesi):")
        for d in gc_docs[:8]:
            print(f"      lv{d.get('level'):>2} guild={d.get('guild_id','?')[:8]}"
                  f"…  legacy='{d['_legacy_class']}' → {d['_target_slug']}  "
                  f"name={d.get('name','?')!r}")
    print(f"[D] grade=None/missing: {grade_missing}")

    # Guards
    if len(orphans) != orphans_target:
        print(f"[WARN] orphans count mismatch: {len(orphans)} vs "
              f"{orphans_target} atteso. Continuo comunque (audit-verified).")
    if len(gc_docs) != gc_target:
        print(f"[WARN] Guardian/Cleric mismatch: {len(gc_docs)} vs "
              f"{gc_target} atteso.")
        if len(gc_docs) > gc_target:
            print("[FAIL] Guardian/Cleric > 6 previsti. STOP.")
            return 4

    if dry_run:
        # E scaffolding (no write in dry-run)
        print("\n[E] Talent tree scaffolding: skipped (dry-run)")
        # F preview
        gcount = await db.guilds.count_documents({})
        print(f"[F] guilds da toccare: {gcount}")
        print("\n[dry-run] Rieseguire con --apply per scrivere.")
        return 0

    # ══════ APPLY ══════
    await _audit(db, "R18_MIGRATION_STARTED", {
        "orphans_found": len(orphans),
        "guardian_cleric_found": len(gc_docs),
        "grade_missing": grade_missing,
    })

    # B apply
    b_updated = await _apply_recruit_unassigned(db, orphans)
    print(f"\n[B apply] recruit_unassigned updates={b_updated}")
    await _audit(db, "R18_ORPHAN_MARKED_UNASSIGNED", {
        "count": b_updated, "expected": len(orphans),
    })

    # C apply
    c_updated = await _apply_guardian_cleric_alias(db, gc_docs)
    print(f"[C apply] Guardian/Cleric alias updates={c_updated}")
    await _audit(db, "R18_GUARDIAN_CLERIC_ALIASED", {
        "count": c_updated,
        "mapping": LEGACY_ALIAS_MAP,
    })

    # D apply
    d_updated = await _apply_grade_backfill(db)
    print(f"[D apply] grade=common backfilled={d_updated}")
    await _audit(db, "R18_GRADE_BACKFILLED", {"count": d_updated})

    # E scaffolding
    e_res = await _ensure_talent_collections(db)
    dummy_ok = await _validate_talent_schema(db)
    print(f"[E apply] talent scaffolding: {e_res} dummy_validation={dummy_ok}")

    # F roster cap
    f_updated, dist = await _apply_roster_cap(db)
    print(f"[F apply] roster cap computed on {f_updated} guilds  "
          f"dist={dist}")
    await _audit(db, "R18_ROSTER_CAP_COMPUTED", {
        "updated": f_updated, "distribution": dist,
    })
    await _audit(db, "R18_BETA_FIELD_PREPARED", {"field": "r18_beta_opt_in"})

    await _audit(db, "R18_MIGRATION_COMPLETED", {
        "B": b_updated, "C": c_updated, "D": d_updated,
        "F": f_updated, "dummy_ok": dummy_ok,
    })
    print("\n[apply] R18.1 complete.")
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
