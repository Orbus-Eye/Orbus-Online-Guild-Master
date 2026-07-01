"""ROUND 15 — Fase 2 / Task A4: legacy auto-unequip for incompatible items.

Sweeps `equipped_items` and, for every row whose item × adventurer pair
triggers a HARD BLOCK from `check_equip_compatibility`, moves the item
back to `inventory_items` (unequipped state) and deletes the equipped
row. No item is ever deleted — only relocated.

Idempotency:
    Re-run safe. A clean DB produces 0 unequip events because the only
    rows touched are those whose validator returns severity=='block'.

Audit:
    Every unequip emits an `audit_logs` row:
        event = 'legacy_auto_unequip_round15'

Run:
    cd /app/backend
    export $(grep -v '^#' .env | xargs)
    python3 -m app.scripts.round15_legacy_unequip_incompatible
    python3 -m app.scripts.round15_legacy_unequip_incompatible --dry-run
"""
from __future__ import annotations

import argparse
import asyncio
import os
import uuid
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient

from app.equipment.compatibility import check_equip_compatibility


async def _audit_log(db, event: str, payload: dict) -> None:
    try:
        await db.audit_logs.insert_one({
            "event": event,
            "payload": payload,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] audit log insert failed: {exc!r}")


async def main():
    parser = argparse.ArgumentParser(
        description="ROUND 15 — Phase 2: legacy auto-unequip incompatible items (idempotent).",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    rows = await db.equipped_items.find({}, {"_id": 0}).to_list(5000)
    print(f"equipped_items scanned: {len(rows)}")

    # Pre-cache adventurers + items for the rows we touch.
    adv_ids = {r["adventurer_id"] for r in rows if r.get("adventurer_id")}
    item_ids = {r["item_id"] for r in rows if r.get("item_id")}
    adv_docs = {
        a["id"]: a
        async for a in db.adventurers.find(
            {"id": {"$in": list(adv_ids)}}, {"_id": 0}
        )
    }
    item_docs = {
        it["id"]: it
        async for it in db.items.find(
            {"id": {"$in": list(item_ids)}}, {"_id": 0}
        )
    }

    unequipped = 0
    skipped = 0
    sample: list[dict] = []
    now_iso = datetime.now(timezone.utc).isoformat()

    for row in rows:
        if not row.get("adventurer_id") or not row.get("item_id"):
            skipped += 1
            continue
        adv = adv_docs.get(row["adventurer_id"])
        item = item_docs.get(row["item_id"])
        if not adv or not item:
            skipped += 1
            continue
        result = check_equip_compatibility(adv, item)
        if result.get("severity") != "block":
            skipped += 1
            continue

        if len(sample) < 5:
            sample.append({
                "guild_id": row.get("guild_id"),
                "adventurer_id": row.get("adventurer_id"),
                "item_slug": item.get("slug"),
                "slot": row.get("slot"),
                "reason_code": result.get("reason_code"),
            })

        if args.dry_run:
            unequipped += 1
            continue

        # Move to inventory (upsert qty +1).
        await db.inventory_items.update_one(
            {"guild_id": row["guild_id"], "item_id": row["item_id"]},
            {
                "$inc": {"quantity": 1},
                "$setOnInsert": {
                    "id": str(uuid.uuid4()),
                    "instance_id": str(uuid.uuid4()),
                    "guild_id": row["guild_id"],
                    "item_id": row["item_id"],
                    "acquired_at": now_iso,
                    "source": "legacy_unequip_round15",
                    "bind_state": "unbound",
                    "is_bound": False,
                    "disenchanted_at": None,
                    "refinement_level": 0,
                    "enchants": [],
                    "affixes": [],
                    "reroll_count": 0,
                },
            },
            upsert=True,
        )
        # Release reservation (best-effort).
        await db.inventory_items.update_one(
            {
                "guild_id": row["guild_id"],
                "item_id": row["item_id"],
                "reserved_qty": {"$gt": 0},
            },
            {"$inc": {"reserved_qty": -1}},
        )
        # Delete the equipped row.
        await db.equipped_items.delete_one({"id": row["id"]})

        await _audit_log(db, "legacy_auto_unequip_round15", {
            "guild_id": row["guild_id"],
            "adventurer_id": row["adventurer_id"],
            "item_id": row["item_id"],
            "item_slug": item.get("slug"),
            "slot": row.get("slot"),
            "reason_code": result.get("reason_code"),
        })
        unequipped += 1

    print("=== SUMMARY ===")
    print(f"  unequipped:      {unequipped}")
    print(f"  skipped (compatible or orphan): {skipped}")
    print("  sample (first 5):")
    for s in sample:
        print(f"    - adv={s['adventurer_id'][:8]}.. item={s['item_slug']:30s} slot={s['slot']:10s} reason={s['reason_code']}")
    if args.dry_run:
        print("  (dry-run: nessuna scrittura)")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
