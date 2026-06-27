"""ROUND 6B.2a — Adventurer retire (soft) service.

Order of preconditions (strict):
  1. adventurer ownership / existence    → 404
  2. already retired                      → 409 already_retired (idempotent signal)
  3. in active expedition/raid            → 409 in_expedition  (HARD blocking)
  4. in non-archived squad                → 409 in_squad       (with squad list)
  5. equipped (without force_unequip)     → 409 equipped       (returns slot list)
  6. happy path                           → 200 + audit
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException


async def retire_adventurer(
    db,
    *,
    guild_id: str,
    adventurer_id: str,
    reason: Optional[str],
    force_unequip: bool,
    actor_user_id: str,
) -> dict:
    adv = await db.adventurers.find_one(
        {"id": adventurer_id, "guild_id": guild_id}, {"_id": 0}
    )
    if not adv:
        raise HTTPException(
            status_code=404,
            detail={"code": "adventurer.not_found", "adventurer_id": adventurer_id},
        )

    if adv.get("is_retired"):
        raise HTTPException(
            status_code=409,
            detail={"code": "adventurer.already_retired",
                    "adventurer_id": adventurer_id,
                    "retired_at": adv.get("retired_at")},
        )

    # 3. Active expedition (status=in_progress, completing, started)
    busy_exp = await db.expeditions.find_one(
        {"guild_id": guild_id,
         "adventurer_ids": adventurer_id,
         "status": {"$in": ["in_progress", "completing", "started"]}},
        {"_id": 0, "id": 1, "status": 1},
    )
    if busy_exp:
        raise HTTPException(
            status_code=409,
            detail={"code": "adventurer.in_expedition",
                    "adventurer_id": adventurer_id,
                    "expedition_id": busy_exp.get("id"),
                    "user_message": (
                        "Avventuriero impegnato in una spedizione attiva. "
                        "Attendi il completamento prima di congedarlo."
                    )},
        )

    # 3b. Active raid
    busy_raid = await db.raids.find_one(
        {"guild_id": guild_id,
         "parties.adventurer_ids": adventurer_id,
         "status": "in_progress"},
        {"_id": 0, "id": 1},
    )
    if busy_raid:
        raise HTTPException(
            status_code=409,
            detail={"code": "adventurer.in_expedition",
                    "adventurer_id": adventurer_id,
                    "raid_id": busy_raid.get("id"),
                    "user_message": (
                        "Avventuriero impegnato in un raid attivo. "
                        "Attendi il completamento prima di congedarlo."
                    )},
        )

    # 4. Non-archived squad membership
    in_squads = await db.squads.find(
        {"guild_id": guild_id,
         "adventurer_ids": adventurer_id,
         "is_archived": False},
        {"_id": 0, "id": 1, "name": 1, "squad_type": 1},
    ).to_list(10)
    if in_squads:
        raise HTTPException(
            status_code=409,
            detail={"code": "adventurer.in_squad",
                    "adventurer_id": adventurer_id,
                    "squads": [{"squad_id": s["id"], "name": s["name"],
                                "squad_type": s["squad_type"]} for s in in_squads],
                    "user_message": (
                        "Avventuriero in una o più squadre salvate. "
                        "Rimuovilo prima di congedarlo."
                    )},
        )

    # 5. Equipped — optionally auto-unequip
    equipped = await db.equipped_items.find(
        {"adventurer_id": adventurer_id}, {"_id": 0, "instance_id": 1, "slot": 1},
    ).to_list(20)
    if equipped and not force_unequip:
        raise HTTPException(
            status_code=409,
            detail={"code": "adventurer.equipped",
                    "adventurer_id": adventurer_id,
                    "equipped_slots": [e.get("slot") for e in equipped],
                    "equipped_count": len(equipped),
                    "user_message": (
                        f"Avventuriero ha {len(equipped)} equipaggiamenti. "
                        f"Passa force_unequip=true per disequipaggiarli automaticamente."
                    )},
        )
    returned_items = []
    if equipped and force_unequip:
        for e in equipped:
            returned_items.append({"instance_id": e.get("instance_id"),
                                   "slot": e.get("slot")})
        await db.equipped_items.delete_many({"adventurer_id": adventurer_id})

    # 6. Soft retire
    now = datetime.now(timezone.utc).isoformat()
    update = {
        "is_retired": True,
        "is_available": False,  # also frees the busy-state used by recruit/raid
        "retired_at": now,
        "retirement_reason": (reason or "").strip()[:200] or None,
        "updated_at": now,
    }
    await db.adventurers.update_one(
        {"id": adventurer_id, "guild_id": guild_id}, {"$set": update}
    )

    # Audit
    try:
        from app.audit.log import write_audit
        await write_audit(
            db,
            event_type="adventurer_retired",
            actor_user_id=actor_user_id,
            actor_guild_id=guild_id,
            source="adventurers.retire",
            related_entity_id=adventurer_id,
            metadata={
                "adventurer_id": adventurer_id,
                "reason": update["retirement_reason"],
                "was_equipped": bool(equipped),
                "equipment_returned_count": len(returned_items),
            },
        )
    except Exception:
        pass

    return {
        "adventurer_id": adventurer_id,
        "retired_at": now,
        "equipment_returned": returned_items,
    }
