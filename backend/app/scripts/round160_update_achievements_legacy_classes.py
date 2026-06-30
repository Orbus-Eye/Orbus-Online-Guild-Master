"""Round 16.0 — Update achievement texts referencing deprecated classes.

Searches the `achievements_catalog` collection for `name_it` / `description_it`
entries that mention the Italian display names of deprecated classes
("Berserker", "Assassino", "Negromante", "berserker", "assassino", "negromante").
For every hit, the script proposes a textual substitution that mentions
both the successor base class and the specialization, e.g.:

  Before:  "Recluta primo Negromante"
  After:   "Recluta primo Negromante (Mago — Negromante)"

Idempotency:
  The script avoids touching any text that already contains the
  successor base class name parenthetical.

Audit:
  One `achievement_text_updated_round160` event per row changed.

Expected outcome on the current dataset:
  0 changes (audit confirmed 0 matches). Script is provided for
  future-proofing should new achievements introduce deprecated names.

Usage:
    python -m app.scripts.round160_update_achievements_legacy_classes [--dry-run]
"""
from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from app.audit.log import write_audit


# Display-name → (successor base IT, spec IT) pairs.
NAME_MAPPING: dict[str, tuple[str, str]] = {
    "Berserker": ("Guerriero", "Berserker"),
    "berserker": ("Guerriero", "Berserker"),
    "Assassino": ("Ladro", "Assassino"),
    "assassino": ("Ladro", "Assassino"),
    "Negromante": ("Mago", "Negromante"),
    "negromante": ("Mago", "Negromante"),
}


def _maybe_rewrite(text: str | None) -> tuple[str | None, list[str]]:
    if not text:
        return text, []
    mutations: list[str] = []
    out = text
    for legacy, (base_it, spec_it) in NAME_MAPPING.items():
        # Skip if already parenthetically annotated.
        marker = f"{spec_it} ({base_it} — "
        if marker in out:
            continue
        pattern = re.compile(rf"\b{re.escape(legacy)}\b")
        if pattern.search(out):
            replacement = f"{spec_it} ({base_it} — {spec_it})"
            out = pattern.sub(replacement, out)
            mutations.append(f"{legacy}→{replacement}")
    return out, mutations


async def _run(db, *, dry_run: bool) -> dict[str, int]:
    updated = 0
    seen = 0
    skipped = 0
    cursor = db.achievements_catalog.find({}, {
        "_id": 0, "slug": 1, "name_it": 1, "description_it": 1,
    })
    async for ach in cursor:
        seen += 1
        new_name, mut_name = _maybe_rewrite(ach.get("name_it"))
        new_desc, mut_desc = _maybe_rewrite(ach.get("description_it"))
        if not (mut_name or mut_desc):
            skipped += 1
            continue
        if dry_run:
            updated += 1
            continue
        set_ops: dict = {"updated_at": datetime.now(timezone.utc)}
        if mut_name:
            set_ops["name_it"] = new_name
        if mut_desc:
            set_ops["description_it"] = new_desc
        await db.achievements_catalog.update_one(
            {"slug": ach["slug"]}, {"$set": set_ops},
        )
        await write_audit(
            db, event_type="achievement_text_updated_round160",
            actor_user_id=None, actor_guild_id=None,
            source="round160.update_achievements_legacy_classes",
            metadata={
                "slug": ach["slug"],
                "mutations_name": mut_name,
                "mutations_desc": mut_desc,
            },
        )
        updated += 1
    return {"seen": seen, "updated": updated, "skipped": skipped}


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    load_dotenv()
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        print("ERROR: MONGO_URL / DB_NAME not configured", file=sys.stderr)
        return 2
    client = AsyncIOMotorClient(mongo_url)
    try:
        db = client[db_name]
        out = await _run(db, dry_run=args.dry_run)
        print({"dry_run": args.dry_run, **out})
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
