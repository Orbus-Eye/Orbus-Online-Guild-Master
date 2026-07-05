"""ROUND 18.Reset.1b DRY-RUN LIVE - Snapshot Utility (before/after).

Uso:
    python -m app.scripts.round18_reset1b_dry_run_live_snapshot \
        --label before \
        --out /app/memory/r18_reset1b_dry_run_live_before.json

    python -m app.scripts.round18_reset1b_dry_run_live_snapshot \
        --label after \
        --out /app/memory/r18_reset1b_dry_run_live_after.json

Contratto (PM directive R18.Reset.1b DRY-RUN LIVE):
    - Enumera TUTTE le collection presenti (list_collection_names).
    - Fa count_documents({}) per la watchlist estesa (guilds, adventurers,
      users, inventory_items, equipped_items, items, achievement_progress,
      expeditions, raids, resource_missions, audit_events, audit_log,
      audit_logs, adventurer_classes).
    - Verifica assenza (o presenza a 0 doc) di collection matching il pattern
      "*_r18_archive".
    - Se una collection della watchlist non esiste -> "N/A (collection absent)".
    - Se esiste ma vuota -> 0 (numerico).
    - Salva su file JSON con timestamp UTC ISO.

L'output e' pensato per un diff testuale ordinato (json.dumps con sort_keys).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")


WATCHLIST_COLLECTIONS = sorted([
    "guilds",
    "adventurers",
    "users",
    "inventory_items",
    "equipped_items",
    "items",
    "achievement_progress",
    "expeditions",
    "raids",
    "resource_missions",
    "audit_events",
    "audit_log",
    "audit_logs",
    "adventurer_classes",
])

R18_ARCHIVE_SUFFIX = "_r18_archive"


async def _build_snapshot(label: str) -> dict:
    ts_iso = datetime.now(timezone.utc).isoformat()
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    try:
        all_collections = sorted(await db.list_collection_names())

        # Watchlist counts (distinguendo N/A da 0)
        watchlist_counts: dict = {}
        for coll_name in WATCHLIST_COLLECTIONS:
            if coll_name in all_collections:
                cnt = await db[coll_name].count_documents({})
                watchlist_counts[coll_name] = cnt
            else:
                watchlist_counts[coll_name] = "N/A (collection absent)"

        # R18 archive detection: elenco + count per ciascuna
        r18_archive_collections = sorted([
            c for c in all_collections if c.endswith(R18_ARCHIVE_SUFFIX)
        ])
        r18_archive_counts: dict = {}
        for coll_name in r18_archive_collections:
            r18_archive_counts[coll_name] = (
                await db[coll_name].count_documents({})
            )

        # Full inventory counts (extra safety, for future forensic)
        full_counts: dict = {}
        for coll_name in all_collections:
            full_counts[coll_name] = await db[coll_name].count_documents({})

        return {
            "label": label,
            "captured_at_utc": ts_iso,
            "db_name": os.environ["DB_NAME"],
            "collections_total": len(all_collections),
            "collections_list": all_collections,
            "watchlist_counts": watchlist_counts,
            "r18_archive_present_count": len(r18_archive_collections),
            "r18_archive_collections": r18_archive_collections,
            "r18_archive_counts": r18_archive_counts,
            "full_counts": full_counts,
        }
    finally:
        client.close()


def _parse_args():
    p = argparse.ArgumentParser(
        description=(
            "R18.Reset.1b DRY-RUN LIVE snapshot util. "
            "Read-only. Nessuna mutazione."
        )
    )
    p.add_argument(
        "--label", required=True, choices=["before", "after"],
        help="Etichetta dello snapshot.",
    )
    p.add_argument(
        "--out", required=True,
        help="Path del file JSON di output.",
    )
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    snap = asyncio.run(_build_snapshot(args.label))
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(snap, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    print(
        f"[snapshot] label={args.label} "
        f"collections_total={snap['collections_total']} "
        f"r18_archive_present={snap['r18_archive_present_count']} "
        f"-> {out_path}",
        flush=True,
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
