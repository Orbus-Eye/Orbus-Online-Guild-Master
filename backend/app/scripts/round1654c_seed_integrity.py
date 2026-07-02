"""ROUND 16.5.4c — ADJ-9 backfill `class_slug` per adventurers legacy.

Contesto (dal REOPEN #2 di R16.5.4b): il 94.01% degli avventurieri in
`orbus_r16` non ha il campo `class_slug` popolato. La `Auto-Equip` fa
fallback runtime su `class_name → class → lowercase`, ma il campo DB
resta assente e altri consumer (report, filtri, spec eligibility) sono
costretti al fallback.

Fix: script idempotente in due modalità:
  * `--dry-run` (default): stampa cosa verrebbe scritto, non scrive nulla.
  * `--apply`: applica `$set: {class_slug, updated_at}` sui documenti che
    lo richiedono. Il secondo `--apply` risulta in zero scritture.

Regole di risoluzione (in ordine):
  1. `class_slug` già presente e non vuoto → nessuna modifica.
  2. Lookup canonico su `adventurer_classes` per `class_name` lowercase.
  3. Lookup canonico su `adventurer_classes` per campo `class` lowercase.
  4. Se tutti i lookup falliscono → doc marcato `unresolved` (non toccato).

Nessun hard delete. Nessuna modifica a campi diversi da `class_slug` e
`updated_at`. Nessun impatto su balance/drop/reward.

Uso:
    python -m app.scripts.round1654c_seed_integrity --dry-run
    python -m app.scripts.round1654c_seed_integrity --apply
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient

SNAPSHOT_PATH = Path("/app/memory/round1654c_adj9_snapshot.json")
AUDIT_EVENT = "ADVENTURER_CLASS_SLUG_BACKFILL_APPLIED"


def _utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


async def _build_name_to_slug(db) -> dict[str, str]:
    """Read `adventurer_classes` and build a lowercase name→slug map.

    Includes name→slug, display_name→slug, and slug→slug (self) so the
    resolver survives edge cases where `class_name` is already the slug.
    """
    mapping: dict[str, str] = {}
    async for cls in db.adventurer_classes.find(
        {}, {"_id": 0, "slug": 1, "name": 1, "display_name": 1, "name_it": 1}
    ):
        slug = (cls.get("slug") or "").strip().lower()
        if not slug:
            continue
        for key in (
            cls.get("name"),
            cls.get("display_name"),
            cls.get("name_it"),
            slug,
        ):
            if not key:
                continue
            mapping[str(key).strip().lower()] = slug
    return mapping


def _resolve_slug(doc: dict, name_to_slug: dict[str, str]) -> str | None:
    """Return the canonical slug for `doc`, or None if unresolvable."""
    for field in ("class_name", "class"):
        raw = doc.get(field)
        if not raw:
            continue
        key = str(raw).strip().lower()
        slug = name_to_slug.get(key)
        if slug:
            return slug
    return None


async def _audit_emit(db, *, dry_run: bool, matched: int, updated: int,
                     unresolved: list[dict]) -> None:
    """Best-effort audit event; failures never block the script."""
    if dry_run:
        return
    try:
        await db.audit_events.insert_one({
            "event_type": AUDIT_EVENT,
            "actor_user_id": None,
            "actor_guild_id": None,
            "related_entity_id": None,
            "source": "script.round1654c_seed_integrity",
            "occurred_at": _utc_iso_now(),
            "metadata": {
                "matched": matched,
                "updated": updated,
                "unresolved_count": len(unresolved),
                "unresolved_sample": unresolved[:20],
            },
        })
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] audit emit failed: {exc}", file=sys.stderr)


async def _snapshot_pre_change(sample_docs: list[dict]) -> None:
    payload = {
        "generated_at": _utc_iso_now(),
        "sample_count": len(sample_docs),
        "sample": sample_docs,
    }
    body = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    SNAPSHOT_PATH.write_text(body + "\n", encoding="utf-8")
    print(f"[snapshot] {SNAPSHOT_PATH} · sha256={_sha256(body)[:16]}…")


async def run(dry_run: bool) -> int:
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        print("[fatal] MONGO_URL o DB_NAME mancante nell'ambiente",
              file=sys.stderr)
        return 2
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    print(f"[mode] {'DRY-RUN' if dry_run else 'APPLY'} · db={db_name}")

    name_to_slug = await _build_name_to_slug(db)
    print(f"[catalog] {len(name_to_slug)} name→slug entries")

    # Idempotency filter: only documents missing class_slug.
    match_filter = {"$or": [
        {"class_slug": {"$exists": False}},
        {"class_slug": None},
        {"class_slug": ""},
    ]}

    total = await db.adventurers.count_documents({})
    to_touch = await db.adventurers.count_documents(match_filter)
    print(f"[audit] adventurers total={total} · missing_class_slug={to_touch}")

    if to_touch == 0:
        print("[idempotent] nessun documento da modificare, exit.")
        return 0

    # Snapshot only a sample (20 docs) — the collection may be large.
    sample_cursor = db.adventurers.find(
        match_filter,
        {"_id": 0, "id": 1, "class_name": 1, "class": 1, "class_slug": 1,
         "guild_id": 1, "level": 1},
    ).limit(20)
    sample_docs = [d async for d in sample_cursor]
    if not dry_run:
        await _snapshot_pre_change(sample_docs)

    matched = 0
    updated = 0
    unresolved: list[dict] = []
    now = _utc_iso_now()

    # Group docs by resolved slug for bulk updates (fewer round trips).
    from collections import defaultdict
    to_update_by_slug: dict[str, list[str]] = defaultdict(list)

    cursor = db.adventurers.find(
        match_filter,
        {"_id": 0, "id": 1, "class_name": 1, "class": 1},
    )
    async for d in cursor:
        matched += 1
        slug = _resolve_slug(d, name_to_slug)
        if slug is None:
            unresolved.append({
                "id": d.get("id"),
                "class_name": d.get("class_name"),
                "class": d.get("class"),
            })
        else:
            to_update_by_slug[slug].append(d["id"])

    # Preview
    print("\n[plan] backfill per slug (dry-run preview):")
    for slug, ids in sorted(to_update_by_slug.items(),
                            key=lambda kv: -len(kv[1])):
        print(f"  {slug:14s} → {len(ids):4d} docs")
    print(f"[plan] unresolved: {len(unresolved)} docs")
    if unresolved:
        print("[plan] esempio unresolved (max 10):")
        for u in unresolved[:10]:
            print(f"  - id={u['id']} class_name={u['class_name']!r} "
                  f"class={u['class']!r}")

    if dry_run:
        print("\n[dry-run] nessuna scrittura. Rieseguire con --apply per "
              "applicare.")
        return 0

    # Apply — bulk update per slug.
    for slug, ids in to_update_by_slug.items():
        if not ids:
            continue
        res = await db.adventurers.update_many(
            {"id": {"$in": ids}, "$or": [
                {"class_slug": {"$exists": False}},
                {"class_slug": None},
                {"class_slug": ""},
            ]},
            {"$set": {"class_slug": slug, "updated_at": now}},
        )
        updated += res.modified_count
        print(f"[apply] slug={slug:14s} matched={res.matched_count:4d} "
              f"modified={res.modified_count:4d}")

    print(f"\n[apply] TOTAL updated={updated} · unresolved={len(unresolved)}")
    await _audit_emit(
        db, dry_run=False, matched=matched, updated=updated,
        unresolved=unresolved,
    )
    return 0


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__ or "")
    grp = p.add_mutually_exclusive_group()
    grp.add_argument("--dry-run", action="store_true", default=True)
    grp.add_argument("--apply", dest="apply_", action="store_true")
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    dry_run = not args.apply_
    rc = asyncio.run(run(dry_run=dry_run))
    sys.exit(rc)


if __name__ == "__main__":
    main()
