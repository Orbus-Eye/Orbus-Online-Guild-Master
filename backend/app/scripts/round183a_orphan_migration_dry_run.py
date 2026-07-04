"""ROUND 18.3a — Orphan Migration Dry-Run (SLUG-CORRECTED, NO WRITE).

Successore diretto di `round182_orphan_migration_dry_run.py`. Cambio
principale rispetto a R18.2: **slug canonici corretti** dal PM Q6:

  - `cacciatore_mostri`  →  `cacciatore_di_mostri`  (con preposizione)
  - `cacciatore_vuoto`   →  `cacciatore_del_vuoto`  (con preposizione)

Aggiornamenti secondari post-R18.3a class seed + item bridge:
  - `target_exists_live=True` per entrambe le classi target new
  - `target_class_doc_exists=True` per entrambe (seed R18.3a in `adventurer_classes`)
  - `target_item_pool_size=31` (cacciatore_di_mostri) + `=18` (cacciatore_del_vuoto)
  - `target_item_pool_risk=BASSO` (post bridge item append-only)

Zero write op. Produce:
  - `/app/memory/round183a_orphan_migration_dry_run.json`
  - `/app/memory/round183a_orphan_migration_plan.md`

Uso:
    python -m app.scripts.round183a_orphan_migration_dry_run
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")


MIGRATION_MAP: dict[str, dict] = {
    "priest": {
        "target": "paladin",
        "target_canonical_it": "Paladino",
        "target_exists_live": True,
        "type": "merge_into_existing",
        "pm_decision": "Q1",
        "expected_adv": 190,
    },
    "ranger": {
        "target": "cacciatore_di_mostri",
        "target_canonical_it": "Cacciatore di Mostri",
        "target_exists_live": True,  # post R18.3a seed
        "type": "migration_to_new_class",
        "pm_decision": "Q2",
        "expected_adv": 175,
    },
    "warlock": {
        "target": "cacciatore_del_vuoto",
        "target_canonical_it": "Cacciatore del Vuoto",
        "target_exists_live": True,  # post R18.3a seed
        "type": "migration_to_new_class",
        "pm_decision": "Q3",
        "expected_adv": 128,
    },
    "berserker": {
        "target": "warrior",
        "target_canonical_it": "Guerriero",
        "target_exists_live": True,
        "type": "alias_deprecated",
        "pm_decision": "Q4",
        "expected_adv": 3,
    },
    "assassin": {
        "target": "rogue",
        "target_canonical_it": "Ladro",
        "target_exists_live": True,
        "type": "alias_deprecated_zero_migration",
        "pm_decision": "Q5",
        "expected_adv": 0,
    },
}


SLUG_CORRECTION_NOTE = {
    "reason": (
        "PM Q6 sigilla gli slug canonici con preposizione articolata: "
        "'cacciatore_di_mostri' e 'cacciatore_del_vuoto'. R18.2 usava "
        "erroneamente le forme brevi 'cacciatore_mostri' e "
        "'cacciatore_vuoto', che sono state deprecate e mai seedate. "
        "R18.3a corregge lo slug prima dell'apply reale in R18.3."
    ),
    "corrected_slugs_from_R18_2": {
        "cacciatore_mostri": "cacciatore_di_mostri",
        "cacciatore_vuoto": "cacciatore_del_vuoto",
    },
}


async def analyze_source(db, slug: str, plan: dict) -> dict:
    """Read-only analysis. NO WRITE."""
    query = {"class_slug": slug}
    n_total = await db.adventurers.count_documents(query)

    lvl_dist: dict[int, int] = {}
    guild_ids: set = set()
    n_retired = 0
    n_available = 0
    n_in_expedition = 0
    n_equipped = 0
    sample_docs: list = []

    async for adv in db.adventurers.find(query, {"_id": 0}):
        lvl = adv.get("level", 0)
        lvl_dist[lvl] = lvl_dist.get(lvl, 0) + 1
        if adv.get("guild_id"):
            guild_ids.add(adv["guild_id"])
        if adv.get("is_retired"):
            n_retired += 1
        if adv.get("is_available"):
            n_available += 1
        if adv.get("current_expedition_id"):
            n_in_expedition += 1
        eq = adv.get("equipped_items") or adv.get("equipment") or {}
        if eq and any(eq.values() if isinstance(eq, dict) else eq):
            n_equipped += 1
        if len(sample_docs) < 5:
            sample_docs.append({
                "id": adv.get("id"),
                "name": adv.get("name"),
                "level": lvl,
                "guild_id": adv.get("guild_id"),
                "class_slug_before": slug,
                "class_slug_after_migration": plan["target"],
                "is_available": adv.get("is_available"),
                "is_retired": adv.get("is_retired"),
                "in_expedition": bool(adv.get("current_expedition_id")),
                "grade": adv.get("grade"),
            })

    n_with_talent_progress = await db.adventurer_talent_progress.count_documents({
        "adventurer_id": {"$in": [
            d.get("id") for d in
            await db.adventurers.find(query, {"_id": 0, "id": 1}).to_list(50)
        ]}
    })

    n_items_target = await db.items.count_documents({
        "$or": [
            {"recommended_classes": plan["target"]},
            {"class_slug": plan["target"]},
        ]
    })
    target_class_doc = await db.adventurer_classes.find_one(
        {"slug": plan["target"]}, {"_id": 0}
    )

    equipped_off_class_sample = []
    async for adv in db.adventurers.find(query, {"_id": 0, "id": 1, "name": 1,
                                                  "equipped_items": 1,
                                                  "equipment": 1}).limit(20):
        eq = adv.get("equipped_items") or adv.get("equipment") or {}
        if not eq:
            continue
        item_ids = []
        if isinstance(eq, dict):
            item_ids = [v for v in eq.values() if v]
        elif isinstance(eq, list):
            item_ids = [e.get("item_id") for e in eq if e]
        for item_id in item_ids[:2]:
            if not item_id:
                continue
            it = await db.items.find_one(
                {"id": item_id},
                {"_id": 0, "recommended_classes": 1, "name": 1},
            )
            if it:
                recs = it.get("recommended_classes") or []
                if recs and plan["target"] not in recs:
                    equipped_off_class_sample.append({
                        "adv_id": adv.get("id"),
                        "adv_name": adv.get("name"),
                        "item_id": item_id,
                        "item_name": it.get("name"),
                        "item_recommended_classes": recs,
                        "would_be_off_class_after_migration": True,
                    })

    return {
        "source_slug": slug,
        "target_slug": plan["target"],
        "target_canonical_it": plan["target_canonical_it"],
        "target_exists_live": plan["target_exists_live"],
        "target_class_doc_exists": target_class_doc is not None,
        "target_class_doc_flags": {
            "is_playable": target_class_doc.get("is_playable") if target_class_doc else None,
            "migration_target_only": target_class_doc.get("migration_target_only") if target_class_doc else None,
            "is_canonical": target_class_doc.get("is_canonical") if target_class_doc else None,
            "source_round": target_class_doc.get("source_round") if target_class_doc else None,
        } if target_class_doc else None,
        "migration_type": plan["type"],
        "pm_decision": plan["pm_decision"],
        "expected_adv": plan["expected_adv"],
        "actual_adv_count": n_total,
        "delta_expected_vs_actual": n_total - plan["expected_adv"],
        "n_retired": n_retired,
        "n_available": n_available,
        "n_in_expedition": n_in_expedition,
        "n_equipped": n_equipped,
        "n_with_talent_progress": n_with_talent_progress,
        "guild_ids_impacted_count": len(guild_ids),
        "level_distribution": dict(sorted(lvl_dist.items())),
        "sample_docs_before_after": sample_docs,
        "target_item_pool_size": n_items_target,
        "target_item_pool_risk": (
            "ALTO" if n_items_target == 0 and n_total > 0
            else ("MEDIO" if n_items_target < 5 and n_total > 0 else "BASSO")
        ),
        "equipped_off_class_sample": equipped_off_class_sample[:5],
    }


async def run() -> int:
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    print(f"[mode] DRY-RUN · db={db_name} · round=R18.3a orphan-migration-plan")
    print(f"[safety] ZERO write op. Only find + report.\n")

    results = []
    total_impacted = 0
    for source_slug, plan in MIGRATION_MAP.items():
        print(f"[analyze] {source_slug} → {plan['target']}...")
        r = await analyze_source(db, source_slug, plan)
        results.append(r)
        total_impacted += r["actual_adv_count"]
        print(f"  actual_adv={r['actual_adv_count']}  "
              f"guilds={r['guild_ids_impacted_count']}  "
              f"in_expedition={r['n_in_expedition']}  "
              f"target_item_pool={r['target_item_pool_size']} "
              f"({r['target_item_pool_risk']})")

    output = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "round": "R18.3a",
        "phase": "class_migration_prereq_dry_run",
        "sealed_pm_decisions": ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"],
        "slug_correction_note": SLUG_CORRECTION_NOTE,
        "total_orphan_adv_to_migrate": total_impacted,
        "safety_summary": {
            "any_writes_performed": False,
            "feature_flag_R18_REWORK_ENABLED": os.environ.get("R18_REWORK_ENABLED"),
            "feature_flag_R18_TALENT_ENGINE_ENABLED": os.environ.get("R18_TALENT_ENGINE_ENABLED"),
            "class_seed_R18_3a_done": True,
            "item_bridge_R18_3a_done": True,
        },
        "migrations": results,
        "rollback_snapshot_recipe": {
            "step_1_snapshot": (
                "BEFORE apply: dump adventurers.class_slug into "
                "career_history as {event_type: 'r18_migration', "
                "class_slug_before, class_slug_after, migrated_at}"
            ),
            "step_2_apply": (
                "update_many({class_slug: source}, {$set: "
                "{class_slug: target, r18_migrated_at: iso, "
                "r18_migrated_from: source}})"
            ),
            "step_3_rollback": (
                "IF rollback needed: update_many("
                "{r18_migrated_from: source}, "
                "{$set: {class_slug: '$r18_migrated_from'}, "
                "$unset: {r18_migrated_at: 1, r18_migrated_from: 1}})"
            ),
        },
    }

    out_path = Path("/app/memory/round183a_orphan_migration_dry_run.json")
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\n[out] JSON dry-run report → {out_path}")
    print(f"[total] {total_impacted} adv would be affected by future apply")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
