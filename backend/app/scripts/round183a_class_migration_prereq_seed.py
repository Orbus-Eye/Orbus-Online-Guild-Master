"""ROUND 18.3a — Class Migration Pre-Req: seed 2 classi target + bridge items.

Prepara il pool tecnico per la migrazione futura R18.3 dei 496 orphan
adventurer, senza toccare gli adventurer reali. Idempotente su tutti i
sub-step.

Sub-step:
  1. Seed classe `cacciatore_di_mostri` in `adventurer_classes` con
     `is_playable=false`, `migration_target_only=true`, `is_active=true`,
     `is_canonical=true`, `source_round="R18.3a"`.
  2. Seed classe `cacciatore_del_vuoto` con gli stessi marker.
  3. Bridge items: append `cacciatore_di_mostri` a `recommended_classes`
     di TUTTI gli item già taggati `ranger` (31 item attesi).
  4. Bridge items: append `cacciatore_del_vuoto` a `recommended_classes`
     di TUTTI gli item già taggati `warlock` (18 item attesi).
  5. Emit audit event `R18_CLASS_MIGRATION_PREREQ_READY` in `audit_log`
     UNA SOLA VOLTA (idempotente: skip se già presente).

Zero migration reale su adventurer. Zero modifica a stats/rarity/level/
drop/power/reward. Solo aggiunta slug in `recommended_classes` (append-
only). Feature flag `R18_REWORK_ENABLED=false` deve restare OFF.

Uso:
    python -m app.scripts.round183a_class_migration_prereq_seed --dry-run
    python -m app.scripts.round183a_class_migration_prereq_seed --apply
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


CLASSES_TO_SEED: list[dict] = [
    {
        "slug": "cacciatore_di_mostri",
        "name": "Cacciatore di Mostri",
        "display_name_it": "Cacciatore di Mostri",
        "source_slug_bridge": "ranger",
        "pm_decision": "Q2",
    },
    {
        "slug": "cacciatore_del_vuoto",
        "name": "Cacciatore del Vuoto",
        "display_name_it": "Cacciatore del Vuoto",
        "source_slug_bridge": "warlock",
        "pm_decision": "Q3",
    },
]

AUDIT_EVENT_TYPE = "R18_CLASS_MIGRATION_PREREQ_READY"


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _check_flags() -> bool:
    """Feature flags MUST remain OFF for R18.3a Pre-Req seed."""
    macro = os.environ.get("R18_REWORK_ENABLED", "false").strip().lower()
    talent = os.environ.get("R18_TALENT_ENGINE_ENABLED", "false").strip().lower()
    if macro not in ("false", "0", "no", ""):
        print(f"[FAIL] R18_REWORK_ENABLED='{macro}' must be OFF for R18.3a")
        return False
    if talent not in ("false", "0", "no", ""):
        print(f"[FAIL] R18_TALENT_ENGINE_ENABLED='{talent}' must be OFF for R18.3a")
        return False
    return True


async def _seed_class(db, cls: dict, dry_run: bool) -> dict:
    """Seed single class with idempotency check."""
    slug = cls["slug"]
    existing = await db.adventurer_classes.find_one({"slug": slug})
    if existing:
        # Idempotent: verifica marker corretti se già esiste
        needs_update: dict = {}
        for key, expected in [
            ("is_playable", False),
            ("migration_target_only", True),
            ("is_canonical", True),
            ("is_active", True),
        ]:
            if existing.get(key) != expected:
                needs_update[key] = expected
        # source_round: marchia se manca
        if existing.get("source_round") != "R18.3a":
            needs_update["source_round"] = "R18.3a"
        if not needs_update:
            return {"slug": slug, "action": "skip-idempotent", "id": existing.get("id")}
        # Serve un update dei marker (append-only)
        if dry_run:
            return {"slug": slug, "action": "would-update", "fields": list(needs_update.keys())}
        needs_update["updated_at"] = _utc_iso()
        await db.adventurer_classes.update_one(
            {"slug": slug}, {"$set": needs_update}
        )
        return {"slug": slug, "action": "updated", "fields": list(needs_update.keys())}

    # Insert nuovo doc
    doc = {
        "id": str(uuid.uuid4()),
        "slug": slug,
        "name": cls["name"],
        "display_name_it": cls["display_name_it"],
        "description": (
            f"Migration target class R18.3a for orphan migration from "
            f"'{cls['source_slug_bridge']}'. Not exposed to recruitment "
            f"until R18.3 apply."
        ),
        "is_playable": False,
        "migration_target_only": True,
        "is_canonical": True,
        "is_active": True,
        "source_round": "R18.3a",
        "source_slug_bridge": cls["source_slug_bridge"],
        "pm_decision": cls["pm_decision"],
        "created_at": _utc_iso(),
        "updated_at": _utc_iso(),
    }
    if dry_run:
        return {"slug": slug, "action": "would-insert", "id": doc["id"]}
    await db.adventurer_classes.insert_one(doc)
    return {"slug": slug, "action": "inserted", "id": doc["id"]}


async def _bridge_items(
    db, target_slug: str, source_slug: str, dry_run: bool
) -> dict:
    """Append `target_slug` to `recommended_classes` for all items already
    tagged with `source_slug`. Idempotent: skip docs where target is
    already present. Append-only: NO override / delete of source_slug.
    """
    q = {"recommended_classes": source_slug}
    total = await db.items.count_documents(q)
    already = await db.items.count_documents({
        **q, "recommended_classes": target_slug
    })
    to_update = total - already
    slot_dist: dict[str, int] = {}
    rarity_dist: dict[str, int] = {}
    level_dist: dict[int, int] = {}
    updated_ids: list[str] = []

    if dry_run:
        async for it in db.items.find(
            {"recommended_classes": source_slug},
            {"_id": 0, "id": 1, "slot": 1, "item_type": 1, "rarity": 1,
             "required_adventurer_level": 1, "required_level": 1,
             "recommended_classes": 1},
        ):
            recs = it.get("recommended_classes") or []
            if target_slug in recs:
                continue
            slot = it.get("slot") or it.get("item_type") or "unknown"
            slot_dist[slot] = slot_dist.get(slot, 0) + 1
            rarity = str(it.get("rarity") or "unknown").lower()
            rarity_dist[rarity] = rarity_dist.get(rarity, 0) + 1
            lvl = it.get("required_adventurer_level") or it.get("required_level") or 0
            try:
                lvl = int(lvl)
            except (TypeError, ValueError):
                lvl = 0
            level_dist[lvl] = level_dist.get(lvl, 0) + 1
        return {
            "source_slug": source_slug,
            "target_slug": target_slug,
            "items_total_source": total,
            "items_already_bridged": already,
            "items_to_append": to_update,
            "action": "dry-run",
            "slot_distribution": slot_dist,
            "rarity_distribution": rarity_dist,
            "level_distribution": dict(sorted(level_dist.items())),
        }

    # APPLY (append-only via $addToSet + no other field touched)
    if to_update > 0:
        # Iter per rilevare distribuzioni post-apply + collezionare ids
        async for it in db.items.find(
            {"recommended_classes": source_slug,
             "recommended_classes": {"$ne": target_slug}}
            if False else {"recommended_classes": source_slug},
            {"_id": 0, "id": 1, "slot": 1, "item_type": 1, "rarity": 1,
             "required_adventurer_level": 1, "required_level": 1,
             "recommended_classes": 1},
        ):
            recs = it.get("recommended_classes") or []
            if target_slug in recs:
                continue
            updated_ids.append(it.get("id"))
            slot = it.get("slot") or it.get("item_type") or "unknown"
            slot_dist[slot] = slot_dist.get(slot, 0) + 1
            rarity = str(it.get("rarity") or "unknown").lower()
            rarity_dist[rarity] = rarity_dist.get(rarity, 0) + 1
            lvl = it.get("required_adventurer_level") or it.get("required_level") or 0
            try:
                lvl = int(lvl)
            except (TypeError, ValueError):
                lvl = 0
            level_dist[lvl] = level_dist.get(lvl, 0) + 1
        # Bulk append via addToSet ($addToSet è idempotente per definizione)
        res = await db.items.update_many(
            {"recommended_classes": source_slug},
            {"$addToSet": {"recommended_classes": target_slug}},
        )
        return {
            "source_slug": source_slug,
            "target_slug": target_slug,
            "items_total_source": total,
            "items_already_bridged": already,
            "items_appended": res.modified_count,
            "items_updated_ids_sample": updated_ids[:10],
            "slot_distribution": slot_dist,
            "rarity_distribution": rarity_dist,
            "level_distribution": dict(sorted(level_dist.items())),
            "action": "applied",
        }
    return {
        "source_slug": source_slug,
        "target_slug": target_slug,
        "items_total_source": total,
        "items_already_bridged": already,
        "items_appended": 0,
        "slot_distribution": slot_dist,
        "rarity_distribution": rarity_dist,
        "level_distribution": dict(sorted(level_dist.items())),
        "action": "idempotent-noop",
    }


async def _emit_audit(db, seed_results: list, bridge_results: list) -> str:
    """Idempotent emit of R18_CLASS_MIGRATION_PREREQ_READY (skip se
    già presente in audit_log)."""
    existing = await db.audit_log.count_documents({"event_type": AUDIT_EVENT_TYPE})
    if existing >= 1:
        return "skip-idempotent"
    doc = {
        "id": str(uuid.uuid4()),
        "event_type": AUDIT_EVENT_TYPE,
        "actor_user_id": None,
        "actor_guild_id": None,
        "item_slug": None,
        "item_template_id": None,
        "quantity": None,
        "gold_delta": None,
        "source": "script.round183a_class_migration_prereq_seed",
        "related_entity_id": None,
        "metadata": {
            "round": "R18.3a",
            "classes_seeded": [c["slug"] for c in CLASSES_TO_SEED],
            "is_playable": False,
            "migration_target_only": True,
            "item_bridge_strategy": "recommended_classes_append_only",
            "item_bridge_counts": {
                b["target_slug"]: b.get("items_appended", b.get("items_to_append", 0))
                for b in bridge_results
            },
            "orphans_impacted_estimated": 303,  # 175 ranger + 128 warlock
            "migration_apply": False,
            "dry_run_only": True,
            "slug_correction_from_R18_2": True,
            "corrected_slugs_from_R18_2": {
                "cacciatore_mostri": "cacciatore_di_mostri",
                "cacciatore_vuoto": "cacciatore_del_vuoto",
            },
            "feature_flag_R18_REWORK_ENABLED": os.environ.get("R18_REWORK_ENABLED"),
            "feature_flag_R18_TALENT_ENGINE_ENABLED": os.environ.get("R18_TALENT_ENGINE_ENABLED"),
            "seed_results": seed_results,
        },
        "created_at": _utc_iso(),
    }
    await db.audit_log.insert_one(doc)
    return "inserted"


async def run(dry_run: bool) -> int:
    if not _check_flags():
        return 3
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        print("[fatal] MONGO_URL / DB_NAME missing", file=sys.stderr)
        return 2

    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    mode = "DRY-RUN" if dry_run else "APPLY"
    print(f"[mode] {mode} · db={db_name} · round=R18.3a class-migration-prereq")
    print(f"[flags] R18_REWORK_ENABLED=OFF · R18_TALENT_ENGINE_ENABLED=OFF")

    # ─ Seed classes ─
    seed_results: list = []
    for cls in CLASSES_TO_SEED:
        r = await _seed_class(db, cls, dry_run=dry_run)
        seed_results.append(r)
        print(f"  [class] {r}")

    # ─ Bridge items ─
    bridge_results: list = []
    for cls in CLASSES_TO_SEED:
        r = await _bridge_items(
            db, target_slug=cls["slug"],
            source_slug=cls["source_slug_bridge"],
            dry_run=dry_run,
        )
        bridge_results.append(r)
        print(f"  [bridge] {cls['source_slug_bridge']} → {cls['slug']} "
              f"total={r['items_total_source']} "
              f"already={r['items_already_bridged']} "
              f"to_append={r.get('items_to_append', r.get('items_appended', 0))}")

    # ─ Audit event ─
    if dry_run:
        print(f"\n[dry-run] audit event {AUDIT_EVENT_TYPE} NOT emitted "
              "(re-run --apply)")
    else:
        audit_result = await _emit_audit(db, seed_results, bridge_results)
        print(f"\n[audit] event {AUDIT_EVENT_TYPE}: {audit_result}")

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
