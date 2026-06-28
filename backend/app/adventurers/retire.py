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


async def _check_exists_and_not_retired(db, *, guild_id: str, adventurer_id: str) -> dict:
    """Steps 1+2 of the retire preflight. Returns the adventurer doc."""
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
    return adv


async def _check_not_in_active_expedition(db, *, guild_id: str, adventurer_id: str) -> None:
    """Step 3: HARD-block if the adventurer is in an in-flight expedition."""
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


async def _check_not_in_active_raid(db, *, guild_id: str, adventurer_id: str) -> None:
    """Step 3b: HARD-block if the adventurer is in an in-flight raid."""
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


async def _check_not_in_active_squad(db, *, guild_id: str, adventurer_id: str) -> None:
    """Step 4: HARD-block if the adventurer is in any non-archived squad."""
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


async def _check_no_bound_items(db, *, guild_id: str, adventurer_id: str) -> None:
    """ROUND 6B.4 Step 4b: HARD-block if the adventurer has 1+ inventory
    items bound to them. The retire must wait until the items are
    transferred or unbound (transfer/unbound flow ships in Round 6C).
    """
    from app.inventory.bound import find_inventory_bound_to_adventurer
    bound_rows = await find_inventory_bound_to_adventurer(
        db, guild_id=guild_id, adventurer_id=adventurer_id, limit=20,
    )
    if not bound_rows:
        return
    item_names = [r["item_name"] for r in bound_rows[:10]]
    raise HTTPException(
        status_code=422,
        detail={
            "code": "adventurer.has_bound_items",
            "adventurer_id": adventurer_id,
            "bound_count": len(bound_rows),
            "bound_items": item_names,
            "user_message": (
                f"Avventuriero ha {len(bound_rows)} oggetto/i legato/i. "
                f"Trasferisci o sblocca i seguenti item prima di congedarlo: "
                f"{', '.join(item_names)}."
            ),
        },
    )


async def _handle_equipped(
    db, *, adventurer_id: str, force_unequip: bool,
) -> list[dict]:
    """Step 5: equipment policy.

    - If equipped AND force_unequip=False → 409 with slot list.
    - If equipped AND force_unequip=True  → bulk-unequip + return the list.
    - If not equipped → returns [].
    """
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
    if not equipped:
        return []
    returned = [
        {"instance_id": e.get("instance_id"), "slot": e.get("slot")}
        for e in equipped
    ]
    await db.equipped_items.delete_many({"adventurer_id": adventurer_id})
    return returned


async def _emit_retire_audit(
    db, *, actor_user_id: str, guild_id: str, adventurer_id: str,
    reason: Optional[str], was_equipped: bool, equipment_returned_count: int,
    retire_via: str = "single",
) -> None:
    """Step 6b: best-effort audit log. Never blocks the retire flow."""
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
                "reason": reason,
                "was_equipped": was_equipped,
                "equipment_returned_count": equipment_returned_count,
                # ROUND 6B.4 Q4 — Free-form metadata tag (not part of the
                # strict `retired_by` enum). Values: "single", "bulk_capacity".
                "retire_via": retire_via,
            },
        )
    except Exception:
        pass
    # ROUND 6B.4 — Companion audit event for bulk retires (helps the
    # operational dashboard to group cap-driven cleanups separately).
    if retire_via == "bulk_capacity":
        try:
            from app.audit.log import write_audit
            await write_audit(
                db,
                event_type="adventurer_retired_bulk",
                actor_user_id=actor_user_id,
                actor_guild_id=guild_id,
                source="adventurers.retire.bulk",
                related_entity_id=adventurer_id,
                metadata={"adventurer_id": adventurer_id},
            )
        except Exception:
            pass


async def retire_adventurer(
    db,
    *,
    guild_id: str,
    adventurer_id: str,
    reason: Optional[str],
    force_unequip: bool,
    actor_user_id: str,
    via: str = "single",
) -> dict:
    # ROUND 6B FASE C — preflight checks moved to single-responsibility
    # helpers above; this orchestrator is now linear (CC ≈ 3, was CC ≈ 16).
    await _check_exists_and_not_retired(db, guild_id=guild_id, adventurer_id=adventurer_id)
    await _check_not_in_active_expedition(db, guild_id=guild_id, adventurer_id=adventurer_id)
    await _check_not_in_active_raid(db, guild_id=guild_id, adventurer_id=adventurer_id)
    await _check_not_in_active_squad(db, guild_id=guild_id, adventurer_id=adventurer_id)
    # ROUND 6B.4 — bound-items pre-check happens BEFORE the equipment
    # branch so a force_unequip with bound items still fails fast (we don't
    # want to silently unequip then leave the user blocked).
    await _check_no_bound_items(db, guild_id=guild_id, adventurer_id=adventurer_id)
    returned_items = await _handle_equipped(
        db, adventurer_id=adventurer_id, force_unequip=force_unequip,
    )

    # 6. Soft retire — set the flags and free busy-state.
    now = datetime.now(timezone.utc).isoformat()
    update = {
        "is_retired": True,
        "is_available": False,  # also frees the busy-state used by recruit/raid
        "retired_at": now,
        "retirement_reason": (reason or "").strip()[:200] or None,
        # ROUND 6B.3 Wave 1.5 — track who/what triggered the retire.
        # Values: "user" (this endpoint), "system" (future automation),
        # "auto_over_cap" (future bulk cleanup). Legacy retires before
        # Wave 1.5 stay `None` and are treated as "user" by readers.
        "retired_by": "user",
        # ROUND 6B.4 — `retire_via` is the user-flow tag (single vs bulk).
        # Stored alongside `retired_by` to make /roster/archive sortable.
        "retire_via": via if via in {"single", "bulk_capacity"} else "single",
        "updated_at": now,
    }
    await db.adventurers.update_one(
        {"id": adventurer_id, "guild_id": guild_id}, {"$set": update}
    )

    await _emit_retire_audit(
        db,
        actor_user_id=actor_user_id,
        guild_id=guild_id,
        adventurer_id=adventurer_id,
        reason=update["retirement_reason"],
        was_equipped=bool(returned_items),
        equipment_returned_count=len(returned_items),
        retire_via=update["retire_via"],
    )

    return {
        "adventurer_id": adventurer_id,
        "retired_at": now,
        "equipment_returned": returned_items,
        "retire_via": update["retire_via"],
    }
