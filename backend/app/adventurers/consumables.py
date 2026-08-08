"""FASE 3.3 (2026-08-08) — Scomparto "Consumabile" degli avventurieri.

Un avventuriero può portare UN consumabile attivo alla volta
(`active_consumable` sul documento). L'attivazione consuma 1 copia
dall'inventario di gilda (decremento condizionale, mai negativo); le
cariche scendono di 1 a ogni spedizione completata e a 0 il buff sparisce.

Effetti (contratto `items.consumable_effect`, design fase 3 §3):
  * power_boost — potere flat aggiunto al membro al dispatch
  * xp_boost    — moltiplicatore XP del membro al completamento

Le funzioni di lettura pure sono in fondo (unit-testabili senza Mongo).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import HTTPException

from app.audit.log import write_audit

logger = logging.getLogger("orbus.adventurers.consumables")

VALID_EFFECT_TYPES = frozenset({"xp_boost", "power_boost"})


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def activate_consumable(
    db, *, guild: dict, adventurer_id: str, item_id: str,
    actor_user_id: str | None = None,
) -> dict:
    """Attiva un consumabile sull'avventuriero (consuma 1 copia)."""
    adv = await db.adventurers.find_one(
        {"id": adventurer_id, "guild_id": guild["id"]},
        {"_id": 0, "id": 1, "name": 1, "active_consumable": 1,
         "is_retired": 1},
    )
    if not adv:
        raise HTTPException(status_code=404, detail={
            "code": "consumable.adventurer_not_found",
            "user_message": "Avventuriero non trovato in questa gilda.",
        })
    if adv.get("is_retired") is True:
        raise HTTPException(status_code=423, detail={
            "code": "consumable.target_retired",
            "user_message": "Non puoi dare consumabili a un avventuriero congedato.",
        })
    current = adv.get("active_consumable") or None
    if current and int(current.get("charges_left", 0)) > 0:
        adv_name = adv.get("name") or "L'avventuriero"
        raise HTTPException(status_code=409, detail={
            "code": "consumable.already_active",
            "active": current,
            "user_message": (
                f"{adv_name} ha già un consumabile attivo "
                f"({current.get('name_it', '?')}, "
                f"{current.get('charges_left', 0)} cariche). Annullalo prima "
                "di assegnarne un altro."
            ),
        })

    item = await db.items.find_one(
        {"id": item_id, "is_active": True, "item_type": "consumable"},
        {"_id": 0},
    )
    effect = (item or {}).get("consumable_effect") or {}
    if not item or effect.get("type") not in VALID_EFFECT_TYPES:
        raise HTTPException(status_code=422, detail={
            "code": "consumable.not_usable",
            "user_message": "Questo oggetto non è un consumabile utilizzabile.",
        })

    # Consumo atomico: 1 copia NON prenotata dall'equipaggiamento.
    consumed = await db.inventory_items.find_one_and_update(
        {
            "guild_id": guild["id"],
            "item_id": item_id,
            "$expr": {
                "$gt": [
                    {"$ifNull": ["$quantity", 0]},
                    {"$ifNull": ["$reserved_qty", 0]},
                ]
            },
        },
        {"$inc": {"quantity": -1}},
        projection={"_id": 0, "id": 1},
    )
    if not consumed:
        raise HTTPException(status_code=409, detail={
            "code": "consumable.not_in_inventory",
            "user_message": "Non hai copie disponibili di questo consumabile.",
        })

    active = {
        "item_id": item["id"],
        "slug": item.get("slug"),
        "name_it": item.get("display_name_it") or item.get("name"),
        "type": effect["type"],
        "magnitude": float(effect.get("magnitude", 0) or 0),
        "charges_left": int(effect.get("charges", 1) or 1),
        "activated_at": _utc_now_iso(),
    }
    await db.adventurers.update_one(
        {"id": adventurer_id},
        {"$set": {"active_consumable": active,
                  "updated_at": _utc_now_iso()}},
    )
    await write_audit(
        db, event_type="consumable_activated",
        actor_user_id=actor_user_id, actor_guild_id=guild["id"],
        source="adventurers.consumable",
        related_entity_id=adventurer_id,
        metadata={"item_slug": item.get("slug"),
                  "charges": active["charges_left"]},
    )
    return {"adventurer_id": adventurer_id, "active_consumable": active}


async def cancel_consumable(
    db, *, guild: dict, adventurer_id: str,
    actor_user_id: str | None = None,
) -> dict:
    """Annulla il buff attivo (nessun rimborso delle cariche residue)."""
    adv = await db.adventurers.find_one(
        {"id": adventurer_id, "guild_id": guild["id"]},
        {"_id": 0, "id": 1, "active_consumable": 1},
    )
    if not adv:
        raise HTTPException(status_code=404, detail={
            "code": "consumable.adventurer_not_found",
            "user_message": "Avventuriero non trovato in questa gilda.",
        })
    if not adv.get("active_consumable"):
        raise HTTPException(status_code=409, detail={
            "code": "consumable.none_active",
            "user_message": "Nessun consumabile attivo da annullare.",
        })
    await db.adventurers.update_one(
        {"id": adventurer_id},
        {"$set": {"active_consumable": None,
                  "updated_at": _utc_now_iso()}},
    )
    await write_audit(
        db, event_type="consumable_cancelled",
        actor_user_id=actor_user_id, actor_guild_id=guild["id"],
        source="adventurers.consumable",
        related_entity_id=adventurer_id,
        metadata={},
    )
    return {"adventurer_id": adventurer_id, "active_consumable": None}


async def decrement_consumable_charges(db, adventurer_id: str) -> None:
    """-1 carica dopo una spedizione completata; a 0 il buff sparisce.

    Best-effort: mai un'eccezione verso il completamento spedizione.
    """
    try:
        adv = await db.adventurers.find_one(
            {"id": adventurer_id},
            {"_id": 0, "active_consumable": 1},
        )
        active = (adv or {}).get("active_consumable")
        if not active:
            return
        left = int(active.get("charges_left", 0)) - 1
        if left <= 0:
            await db.adventurers.update_one(
                {"id": adventurer_id},
                {"$set": {"active_consumable": None}},
            )
        else:
            await db.adventurers.update_one(
                {"id": adventurer_id},
                {"$set": {"active_consumable.charges_left": left}},
            )
    except Exception:  # noqa: BLE001
        logger.exception("consumable charge decrement failed adv=%s",
                         adventurer_id)


# ── Letture pure (unit-testabili) ────────────────────────────────────────

def consumable_power_bonus(adv: dict) -> int:
    """Potere flat dal consumabile attivo (0 se assente/esaurito/altro tipo)."""
    active = (adv or {}).get("active_consumable") or {}
    if active.get("type") != "power_boost":
        return 0
    if int(active.get("charges_left", 0)) <= 0:
        return 0
    return int(active.get("magnitude", 0) or 0)


def consumable_xp_multiplier(adv: dict) -> float:
    """Moltiplicatore XP dal consumabile attivo (1.0 se non applicabile)."""
    active = (adv or {}).get("active_consumable") or {}
    if active.get("type") != "xp_boost":
        return 1.0
    if int(active.get("charges_left", 0)) <= 0:
        return 1.0
    return 1.0 + float(active.get("magnitude", 0) or 0)


__all__ = [
    "VALID_EFFECT_TYPES",
    "activate_consumable",
    "cancel_consumable",
    "decrement_consumable_charges",
    "consumable_power_bonus",
    "consumable_xp_multiplier",
]
