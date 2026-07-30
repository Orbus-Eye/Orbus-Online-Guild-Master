"""Idempotent activation seed for the canonical T6 item catalog.

The T6 catalog coexists with legacy rows during the tester migration. Runtime
loot can prefer ``catalog_version == t6.final.v1`` while old inventory
references remain valid. Existing item IDs are never rewritten.
"""
from __future__ import annotations

from datetime import datetime, timezone

from pymongo import UpdateOne

from app.items.final_catalog import (
    CATALOG_VERSION,
    FINAL_ITEM_CATALOG,
    validate_final_catalog,
)


BULK_BATCH_SIZE = 250


def _upsert_operation(source: dict, now: str) -> UpdateOne:
    payload = dict(source)
    stable_id = payload.pop("id")
    payload.pop("created_at", None)
    payload.update(
        {
            "catalog_version": CATALOG_VERSION,
            "catalog_revision": CATALOG_VERSION,
            "is_active": True,
            "is_test": False,
        }
    )
    return UpdateOne(
        {"slug": source["slug"]},
        {
            "$setOnInsert": {
                "id": stable_id,
                "created_at": now,
            },
            "$set": payload,
        },
        upsert=True,
    )


async def seed_t6_final_catalog(db) -> dict[str, int | str]:
    """Upsert all 1,500 blueprints in bounded batches.

    The function intentionally does not deactivate legacy rows. That migration
    is a separate release gate after tester inventory compatibility has been
    audited.
    """
    report = validate_final_catalog(FINAL_ITEM_CATALOG)
    if not report["valid"]:
        raise RuntimeError(
            "T6 catalog activation refused: " + ", ".join(report["errors"][:20])
        )

    now = datetime.now(timezone.utc).isoformat()
    matched = modified = inserted = 0
    for offset in range(0, len(FINAL_ITEM_CATALOG), BULK_BATCH_SIZE):
        batch = FINAL_ITEM_CATALOG[offset : offset + BULK_BATCH_SIZE]
        result = await db.items.bulk_write(
            [_upsert_operation(item, now) for item in batch],
            ordered=False,
        )
        matched += int(result.matched_count)
        modified += int(result.modified_count)
        inserted += int(result.upserted_count)

    return {
        "catalog_version": CATALOG_VERSION,
        "total": len(FINAL_ITEM_CATALOG),
        "matched": matched,
        "modified": modified,
        "inserted": inserted,
        "sha256": report["sha256"],
    }


__all__ = [
    "BULK_BATCH_SIZE",
    "seed_t6_final_catalog",
]
