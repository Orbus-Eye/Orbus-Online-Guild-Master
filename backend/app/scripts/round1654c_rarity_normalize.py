"""ROUND 16.5.4c — ADJ-1 rarity normalization su `db.items`.

Audit R16.5.4c ha rilevato 17 item con `rarity` in forma non canonica
(lowercase: `epic`, `legendary`, `rare`), mescolati a item con forma
canonica `Capitalized`. Le tabelle di gate e i filtri UI sono
case-sensitive → filtri "Legendary" mancavano `legendary_sword_alveora`
e altri 5 Legendary del catalog R16.3 Phase 5A.

Fix: uso `app.shared.rarity.canonicalize_rarity` come single-source-of-
truth per la forma canonica. Lo script è idempotente:
  * `--dry-run` (default): stampa cosa verrebbe modificato.
  * `--apply`: emette `$set` per ogni doc non canonico.
  * Secondo `--apply` → 0 update.

Nessun hard delete. Nessuna modifica ad altri campi. Nessuna dipendenza
su drop/reward/expedition/recipe.

Uso:
    python -m app.scripts.round1654c_rarity_normalize --dry-run
    python -m app.scripts.round1654c_rarity_normalize --apply
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient

from app.shared.rarity import canonicalize_rarity, CANONICAL_RARITIES

SNAPSHOT_PATH = Path("/app/memory/round1654c_adj1_snapshot.json")
AUDIT_EVENT = "ITEM_RARITY_NORMALIZED"


def _utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def run(dry_run: bool) -> int:
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        print("[fatal] MONGO_URL o DB_NAME mancante", file=sys.stderr)
        return 2
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    mode = "DRY-RUN" if dry_run else "APPLY"
    print(f"[mode] {mode} · db={db_name}")

    # Collect mismatched docs (rarity present but not canonical).
    to_fix: list[tuple[str, str, str]] = []
    unrecognized: list[tuple[str, str]] = []
    async for doc in db.items.find(
        {"rarity": {"$exists": True, "$ne": None}},
        {"_id": 0, "slug": 1, "rarity": 1},
    ):
        raw = doc.get("rarity")
        if raw in CANONICAL_RARITIES:
            continue
        canonical = canonicalize_rarity(raw)
        if canonical is None:
            unrecognized.append((doc.get("slug", "?"), raw))
        else:
            to_fix.append((doc.get("slug", "?"), raw, canonical))

    print(f"[audit] mismatch canonicalizzabili: {len(to_fix)}")
    print(f"[audit] unrecognized (lasciati intatti): {len(unrecognized)}")

    if not to_fix and not unrecognized:
        print("[idempotent] catalog già canonico, 0 modifiche.")
        return 0

    # Report first 30 mismatches
    if to_fix:
        print("\n[plan] normalizzazione (max 30 righe):")
        for slug, raw, canon in to_fix[:30]:
            print(f"  {slug:40s}  {raw!r:12s} → {canon!r}")

    if unrecognized:
        print("\n[plan] unrecognized (NESSUNA modifica):")
        for slug, raw in unrecognized[:20]:
            print(f"  {slug:40s}  {raw!r}")

    if dry_run:
        print("\n[dry-run] nessuna scrittura. Rieseguire con --apply.")
        return 0

    # Snapshot pre-change (rarity mismatch soltanto)
    payload = {
        "generated_at": _utc_iso_now(),
        "mismatch_count": len(to_fix),
        "unrecognized_count": len(unrecognized),
        "mismatch_sample": [{"slug": s, "before": r, "after": c}
                            for s, r, c in to_fix],
        "unrecognized_sample": [{"slug": s, "rarity": r}
                                for s, r in unrecognized],
    }
    SNAPSHOT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[snapshot] {SNAPSHOT_PATH}")

    now = _utc_iso_now()
    updated = 0
    # Bulk per canonical value (few update_many round trips).
    from collections import defaultdict
    by_canon: dict[str, list[str]] = defaultdict(list)
    for slug, raw, canon in to_fix:
        by_canon[canon].append(slug)
    for canon, slugs in by_canon.items():
        res = await db.items.update_many(
            {"slug": {"$in": slugs}, "rarity": {"$nin": list(CANONICAL_RARITIES)}},
            {"$set": {"rarity": canon, "updated_at": now}},
        )
        updated += res.modified_count
        print(f"[apply] canon={canon!r:12s} matched={res.matched_count:4d} "
              f"modified={res.modified_count:4d}")

    print(f"\n[apply] TOTAL updated={updated} · unrecognized skipped="
          f"{len(unrecognized)}")

    # Audit event
    try:
        await db.audit_events.insert_one({
            "event_type": AUDIT_EVENT,
            "actor_user_id": None,
            "related_entity_id": None,
            "source": "script.round1654c_rarity_normalize",
            "occurred_at": now,
            "metadata": {
                "matched": len(to_fix),
                "updated": updated,
                "unrecognized": len(unrecognized),
            },
        })
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] audit emit failed: {exc}", file=sys.stderr)
    return 0


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__ or "")
    grp = p.add_mutually_exclusive_group()
    grp.add_argument("--dry-run", action="store_true", default=True)
    grp.add_argument("--apply", dest="apply_", action="store_true")
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    rc = asyncio.run(run(dry_run=not args.apply_))
    sys.exit(rc)


if __name__ == "__main__":
    main()
