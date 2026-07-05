"""ROUND 6C — Signature item template seeder + backfill.

Two responsibilities, both idempotent and called at backend boot:

1. **Template seed**: every `SPEC_SIGNATURE_ITEMS` entry is upserted into
   `db.items` with ``id = slug`` so the inventory lookup join
   (`items_map[r.item_id]`) resolves and `/api/inventory` returns a populated
   `item` field. Templates carry the same display name + rarity + slot + stat
   bonuses as the embedded `signature` sub-doc on inventory rows.

2. **Inventory backfill**: for every adventurer with a populated
   `specialization.signature_item_id` whose target `inventory_items` row is
   missing (the row was previously wiped by the pytest orphan cleanup, which
   itself has now been fixed in `conftest.py`), regenerate the row from the
   catalog so the player sees the signature item in `/api/inventory` again.

Both are safe to call repeatedly — no hard deletes, only `update_one` upserts
and `insert_one` for missing rows.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.training.catalog import SPEC_SIGNATURE_ITEMS

logger = logging.getLogger("orbus.training.seed")

SIGNATURE_BOUND_REASON = "specialization_signature"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _template_doc_for(slug: str, sig: dict) -> dict:
    """Build the `db.items` row that mirrors a signature item template.

    Uses ``id = slug`` so the inventory join matches without an extra mapping.
    Note: `name` is the canonical field that `app.items.services.item_public`
    expects. We default to the Italian name (the game's primary locale) and
    expose `display_name_it`/`display_name_en` for the frontend selector.
    """
    now_iso = _utc_now_iso()
    name_it = sig.get("name_it") or slug
    name_en = sig.get("name_en") or name_it
    return {
        "id": slug,
        "slug": slug,
        # Canonical name (required by item_public — see items/services.py).
        "name": name_it,
        "display_name_it": name_it,
        "display_name_en": name_en,
        "description": sig.get("description_it", ""),
        "rarity": sig.get("rarity", "Rare"),
        "item_type": sig.get("item_type") or sig.get("slot") or "weapon",
        "slot": sig.get("slot"),
        # Stat bonuses (mirror the embedded signature sub-doc).
        "strength_bonus": int(sig.get("strength_bonus", 0)),
        "agility_bonus": int(sig.get("agility_bonus", 0)),
        "intellect_bonus": int(sig.get("intellect_bonus", 0)),
        "endurance_bonus": int(sig.get("endurance_bonus", 0)),
        "faith_bonus": int(sig.get("faith_bonus", 0)),
        "power_score": int(sig.get("power_score", 0)),
        "level_required": int(sig.get("level_required", 5)),
        # Monetization flags — signature items NEVER touch real money or
        # the gold/material economy of other guilds.
        "is_tradeable": False,
        "is_cosmetic": False,
        "affects_combat": True,
        "affects_economy": False,
        "affects_ranking": True,
        "can_be_sold_for_gold": False,
        "can_be_sold_for_real_money": False,
        "is_active": True,
        # Markers for visibility in audits / debug tools.
        "is_signature": True,
        "is_listable_on_market": False,
        "is_listable_on_auction": False,
        "is_test": False,
        "created_at": now_iso,
        "updated_at": now_iso,
    }


async def seed_signature_templates(db) -> dict:
    """Upsert all signature templates in `db.items`. Returns counters."""
    inserted = 0
    updated = 0
    for slug, sig in SPEC_SIGNATURE_ITEMS.items():
        doc = _template_doc_for(slug, sig)
        # Use $setOnInsert for stable timestamps; $set for the rest so a
        # catalog edit (e.g. stat tweak) propagates on the next boot.
        res = await db.items.update_one(
            {"id": slug},
            {
                "$set": {k: v for k, v in doc.items()
                         if k not in ("id", "created_at")},
                "$setOnInsert": {"id": slug, "created_at": doc["created_at"]},
            },
            upsert=True,
        )
        if res.upserted_id is not None:
            inserted += 1
        elif res.modified_count:
            updated += 1
    return {"templates_inserted": inserted, "templates_updated": updated}


from app.core.job_freeze import frozen_when_active as _frozen_when_active


@_frozen_when_active(
    "orbus.training.backfill_missing_signature_inventory_rows",
    freeze_return_value={"signature_rows_restored": 0, "skipped_no_template": 0, "skipped_freeze": True},
)
async def backfill_missing_signature_inventory_rows(db) -> dict:
    """Re-create `inventory_items` rows for advs with a dangling `signature_item_id`.

    Runs after the template seed so the items lookup join immediately resolves.
    Idempotent: if the inventory row already exists, no write happens.
    """
    restored = 0
    skipped_no_template = 0
    cursor = db.adventurers.find(
        {"specialization.signature_item_id": {"$ne": None}},
        {"_id": 0, "id": 1, "guild_id": 1, "specialization": 1, "is_retired": 1},
    )
    async for adv in cursor:
        spec = adv.get("specialization") or {}
        sig_id = spec.get("signature_item_id")
        spec_slug = spec.get("slug")
        if not sig_id or not spec_slug:
            continue
        existing = await db.inventory_items.find_one(
            {"id": sig_id}, {"_id": 0, "id": 1},
        )
        if existing:
            continue
        # Find the template slug from the spec catalog. The signature_item_slug
        # is the link from spec → template.
        from app.training.catalog import SPEC_BY_SLUG
        spec_def = SPEC_BY_SLUG.get(spec_slug)
        if not spec_def:
            skipped_no_template += 1
            continue
        sig_slug = spec_def.get("signature_item_slug")
        sig_template = SPEC_SIGNATURE_ITEMS.get(sig_slug)
        if not sig_template:
            skipped_no_template += 1
            continue
        now_iso = _utc_now_iso()
        # Build the inventory row the same way `training.services` does — keep
        # `id == sig_id` so the existing `adv.specialization.signature_item_id`
        # reference remains valid (no schema migration needed).
        row = {
            "id": sig_id,
            "instance_id": sig_id,
            "guild_id": adv["guild_id"],
            "item_id": sig_slug,
            "quantity": 1,
            "acquired_at": now_iso,
            "is_material": False,
            "is_bound": True,
            "refinement_level": 0,
            "enchants": [],
            "affixes": [],
            "reroll_count": 0,
            "bound_to_adventurer_id": adv["id"],
            "bound_reason": SIGNATURE_BOUND_REASON,
            "bound_at": now_iso,
            "discarded_at": None,
            "discard_reason": None,
            "signature": {
                "spec_slug": spec_slug,
                **{k: v for k, v in sig_template.items() if k != "signature_item_slug"},
            },
            "is_signature_backfill": True,
        }
        await db.inventory_items.insert_one(row)
        restored += 1
    return {"signature_rows_restored": restored,
            "skipped_no_template": skipped_no_template}


__all__ = [
    "seed_signature_templates",
    "backfill_missing_signature_inventory_rows",
    "SIGNATURE_BOUND_REASON",
]
