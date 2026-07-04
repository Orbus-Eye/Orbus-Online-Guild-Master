"""ROUND 18.2 PILOT — Talent Tree Placeholder Seed.

Seed 9 × 60 = 540 doc placeholder in `talent_tree_definitions` per le
9 classi PILOT (live 1:1 sicure). Nessun talento reale, solo scaffolding
strutturale. Idempotente (secondo run = 0 modifiche).

Feature flag double-gate check: R18_REWORK_ENABLED e R18_TALENT_ENGINE_ENABLED
DEVONO essere OFF prima di eseguire (safety-only, seed è schema).

Uso:
    python -m app.scripts.round182_talent_tree_pilot_seed --dry-run
    python -m app.scripts.round182_talent_tree_pilot_seed --apply
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

# Add /app/backend to path if invoked directly
sys.path.insert(0, "/app/backend")

from app.talents.models import (
    BRANCHES_PER_CLASS,
    PILOT_CLASS_SLUGS,
    SLOTS_PER_TIER,
    SLOTS_PER_CLASS,
    TIERS_PER_BRANCH,
    TalentTreeDefinition,
    build_placeholder_id,
)

load_dotenv("/app/backend/.env")


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _check_flags() -> bool:
    """Both flags MUST remain OFF for R18.2 PILOT. Non-blocking on OFF."""
    macro = os.environ.get("R18_REWORK_ENABLED", "false").strip().lower()
    sub = os.environ.get("R18_TALENT_ENGINE_ENABLED", "false").strip().lower()
    if macro not in ("false", "0", "no", ""):
        print(f"[FAIL] R18_REWORK_ENABLED='{macro}' must be OFF for PILOT")
        return False
    if sub not in ("false", "0", "no", ""):
        print(f"[FAIL] R18_TALENT_ENGINE_ENABLED='{sub}' must be OFF for PILOT")
        return False
    return True


async def _emit_audit(db, count_new: int, count_total: int) -> None:
    doc = {
        "id": str(uuid.uuid4()),
        "event_type": "R18_TALENT_PILOT_SEEDED",
        "actor_user_id": None,
        "actor_guild_id": None,
        "item_slug": None,
        "item_template_id": None,
        "quantity": count_new,
        "gold_delta": None,
        "source": "script.round182_talent_tree_pilot_seed",
        "related_entity_id": None,
        "metadata": {
            "round": "R18.2",
            "phase": "PILOT",
            "pilot_class_slugs": sorted(PILOT_CLASS_SLUGS),
            "slots_per_class": SLOTS_PER_CLASS,
            "docs_new_this_run": count_new,
            "docs_total_after_run": count_total,
            "is_placeholder_only": True,
        },
        "created_at": _utc_iso(),
    }
    await db.audit_log.insert_one(doc)


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
    print(f"[mode] {mode} · db={db_name} · round=R18.2 talent-pilot-seed")
    print(f"[flags] R18_REWORK_ENABLED=OFF · R18_TALENT_ENGINE_ENABLED=OFF")
    print(f"[scope] {len(PILOT_CLASS_SLUGS)} classi PILOT × "
          f"{SLOTS_PER_CLASS} slot = "
          f"{len(PILOT_CLASS_SLUGS) * SLOTS_PER_CLASS} doc target")

    # Build target set
    targets: list[TalentTreeDefinition] = []
    for cls in sorted(PILOT_CLASS_SLUGS):
        for branch in range(1, BRANCHES_PER_CLASS + 1):
            for tier in range(1, TIERS_PER_BRANCH + 1):
                for slot in range(1, SLOTS_PER_TIER + 1):
                    pid = build_placeholder_id(cls, branch, tier, slot)
                    targets.append(TalentTreeDefinition(
                        class_slug=cls,
                        branch_id=branch,
                        tier=tier,
                        slot_index=slot,
                        placeholder_id=pid,
                    ))

    # Find existing docs
    existing = set()
    async for d in db.talent_tree_definitions.find(
        {"placeholder_id": {"$in": [t.placeholder_id for t in targets]}},
        {"_id": 0, "placeholder_id": 1},
    ):
        existing.add(d["placeholder_id"])
    to_insert = [t for t in targets if t.placeholder_id not in existing]

    print(f"[scan] target={len(targets)} existing={len(existing)} "
          f"to_insert={len(to_insert)}")

    if dry_run:
        print("\n[dry-run] Re-run --apply per scrivere.")
        # Print first 5 sample placeholder_ids
        for t in targets[:5]:
            print(f"  · {t.placeholder_id}")
        return 0

    # APPLY
    if to_insert:
        docs = [t.model_dump() for t in to_insert]
        await db.talent_tree_definitions.insert_many(docs, ordered=False)
    total_after = await db.talent_tree_definitions.count_documents({
        "is_placeholder": True, "round_seeded": "R18.2"
    })
    print(f"\n[apply] inserted={len(to_insert)}  total_after={total_after}")

    # Audit event (only on real insert to avoid spam)
    if len(to_insert) > 0:
        await _emit_audit(db, len(to_insert), total_after)
        print("[audit] R18_TALENT_PILOT_SEEDED emitted to audit_log")
    else:
        print("[audit] no-op run: no audit event emitted (idempotent)")

    # Verify
    n_r18 = await db.audit_log.count_documents(
        {"event_type": "R18_TALENT_PILOT_SEEDED"}
    )
    print(f"[verify] audit_log R18_TALENT_PILOT_SEEDED total: {n_r18}")
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
