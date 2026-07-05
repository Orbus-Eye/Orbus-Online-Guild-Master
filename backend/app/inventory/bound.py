"""ROUND 6B.4 — Adventurer-bound inventory helpers.

Two complementary "bound" concepts coexist in the inventory schema:

* `is_bound: bool` (Phase 4 / Round 4 — guild-bound BoE):
    Set to True by Forge after refine/enchant/reroll. Already prevents the
    item from being listed on Auction or sold to the NPC shop. Stays equippable
    by any adventurer of the guild.

* `bound_to_adventurer_id: str | None` (this module — adventurer-bound):
    New in Round 6B.4. When set, the item is bound to that specific adventurer
    and:
      - Can ONLY be equipped on that adventurer (422 elsewhere)
      - Cannot be sold to NPC shop or listed on Auction (422)
      - Blocks retire of the adventurer until transferred/unbound
      - Companion fields: `bound_reason: str | None`, `bound_at: ISO str | None`

The two concepts are independent: an item can be guild-bound and/or
adventurer-bound simultaneously. Round 6B.4 ships the schema + the guards,
but no real source populates `bound_to_adventurer_id` yet — that arrives in
Round 6C (training rewards) and Round 6D (contract rewards). Use the dev seed
script in `backend/app/scripts/seed_test_bound_items.py` to exercise guards.
"""
from __future__ import annotations

from typing import Optional


BOUND_FIELDS = ("bound_to_adventurer_id", "bound_reason", "bound_at")


def is_bound_to_adventurer(inv_row: dict, adventurer_id: str) -> bool:
    """True if `inv_row` is adventurer-bound to *exactly* this adventurer."""
    return inv_row.get("bound_to_adventurer_id") == adventurer_id


def is_bound_to_other_adventurer(inv_row: dict, adventurer_id: str) -> bool:
    """True if `inv_row` is bound to a DIFFERENT adventurer.

    `None` (unbound) returns False — unbound items are equippable by anyone.
    """
    bound_to = inv_row.get("bound_to_adventurer_id")
    return bound_to is not None and bound_to != adventurer_id


async def find_inventory_bound_to_adventurer(
    db, *, guild_id: str, adventurer_id: str, limit: int = 50,
) -> list[dict]:
    """Return inventory rows bound to this adventurer with denormalised item
    name resolved for clearer error messages on the retire blocker."""
    rows = await db.inventory_items.find(
        {
            "guild_id": guild_id,
            "bound_to_adventurer_id": adventurer_id,
        },
        {"_id": 0, "id": 1, "instance_id": 1, "item_id": 1,
         "bound_reason": 1, "bound_at": 1},
    ).to_list(limit)
    if not rows:
        return []
    # Resolve item template names in one round-trip.
    item_ids = list({r["item_id"] for r in rows if r.get("item_id")})
    name_by_id: dict[str, str] = {}
    if item_ids:
        async for it in db.items.find(
            {"id": {"$in": item_ids}}, {"_id": 0, "id": 1, "name": 1},
        ):
            name_by_id[it["id"]] = it.get("name") or it["id"]
    enriched: list[dict] = []
    for r in rows:
        enriched.append({
            "inventory_id": r.get("id"),
            "instance_id": r.get("instance_id"),
            "item_id": r.get("item_id"),
            "item_name": name_by_id.get(r.get("item_id"), r.get("item_id")),
            "bound_reason": r.get("bound_reason"),
            "bound_at": r.get("bound_at"),
        })
    return enriched


from app.core.job_freeze import frozen_when_active as _frozen_when_active


@_frozen_when_active(
    "orbus.inventory.backfill_bound_fields_if_missing",
    freeze_return_value={"migrated_count": 0, "already_present_count": "skipped_freeze"},
)
async def backfill_bound_fields_if_missing(db) -> dict:
    """Idempotent migration: ensure every `inventory_items` row has the three
    Round 6B.4 bound fields (default `None`). Safe to run repeatedly — the
    `$exists: false` filter only touches legacy rows.

    Returns: {migrated_count, already_present_count}.
    """
    # Count legacy rows so caller can log clearly.
    legacy = await db.inventory_items.count_documents(
        {"bound_to_adventurer_id": {"$exists": False}}
    )
    if legacy == 0:
        return {"migrated_count": 0, "already_present_count": "all"}
    res = await db.inventory_items.update_many(
        {"bound_to_adventurer_id": {"$exists": False}},
        {"$set": {
            "bound_to_adventurer_id": None,
            "bound_reason": None,
            "bound_at": None,
        }},
    )
    return {
        "migrated_count": res.modified_count,
        "already_present_count": "see-prev-rows",
    }


async def ensure_bound_indexes(db) -> None:
    """Sparse index on `bound_to_adventurer_id` for fast retire-blocker
    lookups. Sparse means it skips rows where the field is null — perfect
    for our default `None` case."""
    await db.inventory_items.create_index(
        [("bound_to_adventurer_id", 1)],
        sparse=True,
        name="bound_to_adventurer_id_sparse",
    )


__all__ = [
    "BOUND_FIELDS",
    "backfill_bound_fields_if_missing",
    "ensure_bound_indexes",
    "find_inventory_bound_to_adventurer",
    "is_bound_to_adventurer",
    "is_bound_to_other_adventurer",
]


def _public_bound_block(inv_row: Optional[dict]) -> Optional[dict]:
    """Pure helper used by the inventory serialiser to expose the bound
    payload on the API response (FE renders the badge from this)."""
    if not inv_row:
        return None
    bound_to = inv_row.get("bound_to_adventurer_id")
    if not bound_to:
        return None
    return {
        "adventurer_id": bound_to,
        "reason": inv_row.get("bound_reason"),
        "at": inv_row.get("bound_at"),
    }
