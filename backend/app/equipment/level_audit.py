"""ROUND 11.3 TASK B — Legacy equipment level audit.

Scans `equipped_items` and finds rows where the equipped item's
`required_adventurer_level` exceeds the adventurer's current level. For
each offending row it performs a **soft unequip** (release reservation,
delete the equipped_items row) and writes an audit event. The item is
NEVER deleted — it stays in the guild inventory (`equipped_by=null`).

Why soft + audit, not hard delete:
  * Players keep ownership of the legendary they earned at Lv8 — they
    just can't equip it until they hit the required level.
  * Audit lets us track how many advs were affected by the round 11.3
    patch and surfaces patterns to balance design.

Idempotent: re-running on a fixed pool does no work (the query returns 0).
"""
from __future__ import annotations

import logging
from typing import Optional

from app.equipment.level_gate import resolve_item_required_level

logger = logging.getLogger("orbus.equipment_level_audit")


async def audit_and_unequip_legacy(
    db,
    *,
    dry_run: bool = True,
    guild_id_filter: Optional[str] = None,
) -> dict:
    """Scan + (optionally) soft-unequip every legacy invalid equip.

    Returns a structured report:
        {
            "scanned": <int>,                 # equipped_items rows examined
            "invalid": <int>,                 # rows that breach the gate
            "auto_unequipped": <int>,         # rows actually unequipped (0 in dry_run)
            "by_item_slug": {slug: count},    # which items hit the gate most
            "by_guild": {guild_id: count},    # blast radius per guild (id is internal UUID, safe)
            "dry_run": bool,
        }
    """
    q: dict = {}
    if guild_id_filter:
        q["guild_id"] = guild_id_filter
    rows = await db.equipped_items.find(q, {"_id": 0}).to_list(10_000)

    if not rows:
        return {
            "scanned": 0, "invalid": 0, "auto_unequipped": 0,
            "by_item_slug": {}, "by_guild": {}, "dry_run": dry_run,
        }

    item_ids = list({r["item_id"] for r in rows if r.get("item_id")})
    items = await db.items.find({"id": {"$in": item_ids}}, {"_id": 0}).to_list(1000)
    items_by_id = {i["id"]: i for i in items}

    adv_ids = list({r["adventurer_id"] for r in rows})
    advs = await db.adventurers.find(
        {"id": {"$in": adv_ids}}, {"_id": 0, "id": 1, "level": 1, "guild_id": 1}
    ).to_list(5000)
    advs_by_id = {a["id"]: a for a in advs}

    invalid_rows = []
    by_item: dict = {}
    by_guild: dict = {}
    for r in rows:
        if not r.get("item_id") or not r.get("adventurer_id"):
            continue
        item = items_by_id.get(r["item_id"])
        adv = advs_by_id.get(r["adventurer_id"])
        if not item or not adv:
            continue  # orphaned row — skip silently, not our concern
        required = resolve_item_required_level(item)
        current = int(adv.get("level", 1) or 1)
        if current >= required:
            continue
        invalid_rows.append({"row": r, "item": item, "adv": adv, "required": required, "current": current})
        by_item[item.get("slug", "?")] = by_item.get(item.get("slug", "?"), 0) + 1
        by_guild[r.get("guild_id", "?")] = by_guild.get(r.get("guild_id", "?"), 0) + 1

    auto_unequipped = 0
    if not dry_run:
        from app.audit.log import write_audit
        for entry in invalid_rows:
            r = entry["row"]
            item = entry["item"]
            # Soft unequip: delete equipped_items row + release reservation.
            # The inventory row keeps `quantity` as-is, so the item stays
            # in the player's deposit.
            await db.equipped_items.delete_one({"id": r["id"]})
            await db.inventory_items.update_one(
                {
                    "guild_id": r["guild_id"],
                    "item_id": r["item_id"],
                    "reserved_qty": {"$gt": 0},
                },
                {"$inc": {"reserved_qty": -1}},
            )
            try:
                await write_audit(
                    db,
                    event_type="equipment_auto_unequipped_level_requirement",
                    actor_guild_id=r["guild_id"],
                    item_slug=item.get("slug"),
                    item_template_id=item.get("id"),
                    quantity=1,
                    source="equipment.level_audit",
                    related_entity_id=r["adventurer_id"],
                    metadata={
                        "slot": r.get("slot"),
                        "required_level": entry["required"],
                        "current_level": entry["current"],
                    },
                )
            except Exception:
                logger.exception("audit write failed for equipped_item id=%s", r.get("id"))
            auto_unequipped += 1

    return {
        "scanned": len(rows),
        "invalid": len(invalid_rows),
        "auto_unequipped": auto_unequipped,
        "by_item_slug": by_item,
        "by_guild": by_guild,
        "dry_run": dry_run,
    }


__all__ = ["audit_and_unequip_legacy"]
