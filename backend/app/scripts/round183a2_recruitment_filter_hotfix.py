"""ROUND 18.3a.2 HOTFIX — Recruitment Hidden Class Filter.

Emette l'audit event `R18_RECRUITMENT_HIDDEN_CLASS_FILTER_PATCHED` per
tracciare l'applicazione della patch chirurgica a
`app/adventurers/generator.py::filter_safe_class_pool` (line 87-109).

**La patch NON modifica dati.** L'audit event è marker one-shot per
audit trail. Idempotente: secondo run non ri-emette l'evento.

Bug live risolto:
    POST /api/recruitment/refresh -> HTTP 500 (~15% failure rate)
    KeyError: 'base_strength' in app/adventurers/common.py:115
    Root cause: filter_safe_class_pool includeva le 2 classi hidden
    seedate da R18.3a (`cacciatore_di_mostri`, `cacciatore_del_vuoto`)
    che sono `is_playable=false` + `migration_target_only=true` e
    mancano dei campi `base_*` stat. Quando rng.choice() le pescava
    (~2/13 = 15%), il generator crashava.

Fix:
    Aggiunta chiave `"is_playable": {"$ne": False}` al filter MongoDB
    di `filter_safe_class_pool`. Preserva backward compat: doc senza
    is_playable passano (nessuna regression sui 11 doc legacy).

Uso:
    python -m app.scripts.round183a2_recruitment_filter_hotfix --apply
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


AUDIT_EVENT_TYPE = "R18_RECRUITMENT_HIDDEN_CLASS_FILTER_PATCHED"
HIDDEN_SLUGS = ["cacciatore_di_mostri", "cacciatore_del_vuoto"]


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def run(dry_run: bool) -> int:
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    mode = "DRY-RUN" if dry_run else "APPLY"
    print(f"[mode] {mode} · round=R18.3a.2 recruitment-hidden-class-filter")

    # Read-only diagnostic: confirm the 2 hidden classes are still in
    # place from R18.3a and lack base_strength.
    hidden_docs = await db.adventurer_classes.find(
        {"slug": {"$in": HIDDEN_SLUGS}},
        {"_id": 0, "slug": 1, "is_playable": 1,
         "migration_target_only": 1, "base_strength": 1},
    ).to_list(10)
    print(f"[scan] hidden docs found: {len(hidden_docs)}")
    for d in hidden_docs:
        has_bs = "base_strength" in d
        print(f"  {d['slug']} · is_playable={d.get('is_playable')} "
              f"migration_target_only={d.get('migration_target_only')} "
              f"has_base_strength={has_bs}")

    # Audit event (idempotent — only if never emitted)
    existing = await db.audit_log.count_documents(
        {"event_type": AUDIT_EVENT_TYPE}
    )
    if existing >= 1:
        print(f"[audit] {AUDIT_EVENT_TYPE} already logged (n={existing}) "
              f"— skip (idempotent)")
    elif dry_run:
        print("[dry-run] audit event NOT emitted")
    else:
        await db.audit_log.insert_one({
            "id": str(uuid.uuid4()),
            "event_type": AUDIT_EVENT_TYPE,
            "actor_user_id": None,
            "actor_guild_id": None,
            "item_slug": None,
            "item_template_id": None,
            "quantity": None,
            "gold_delta": None,
            "source": "script.round183a2_recruitment_filter_hotfix",
            "related_entity_id": None,
            "metadata": {
                "round": "R18.3a.2",
                "hotfix_for": "R18.3a",
                "file": "app/adventurers/generator.py",
                "function": "filter_safe_class_pool",
                "line_range": "87-109 (actual patch); brief cited line 64",
                "filter_added": "is_playable != false",
                "db_write": False,
                "schema_migration": False,
                "adventurers_touched": False,
                "combat_math_changed": False,
                "auto_equip_changed": False,
                "role_enum_changed": False,
                "player_facing_bug_fixed": True,
                "bug_source_round": "R18.3a",
                "bug_symptom": (
                    "HTTP 500 recruitment refresh ~15% failure rate due "
                    "to hidden classes without base_* fields"
                ),
                "bug_endpoint": "/api/recruitment/refresh",
                "bug_error": "KeyError: 'base_strength'",
                "bug_probability_pre_patch": "~2/13 = ~15%",
                "hidden_slugs_excluded": HIDDEN_SLUGS,
                "hidden_docs_in_db_intact": len(hidden_docs),
                "hidden_docs_untouched": True,
            },
            "created_at": _utc_iso(),
        })
        print(f"[audit] {AUDIT_EVENT_TYPE} emitted")

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
