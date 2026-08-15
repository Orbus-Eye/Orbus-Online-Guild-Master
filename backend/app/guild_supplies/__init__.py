"""FASE 10C-F — BENI DI GILDA (guild_supplies).

Risorsa di gilda con cap fisso 120, refill giornaliero a 120 alle 00:00
(giorno UTC: stessa convenzione del reset giornaliero di quest/streak) e
consumo server-authoritative (mai saldo negativo, mai sopra il cap).

Design:
  * Refill LAZY + idempotente: il primo tocco del giorno (lettura,
    spesa, accredito) riporta il saldo a 120 via CAS sul campo
    ``guild_supplies_last_refill``. Un secondo trigger nello stesso
    giorno non ha alcun effetto — nessuno scheduler nuovo.
  * Fallback legacy: gilda senza campo ``guild_supplies`` → 120.
  * Spesa atomica: filtro ``$gte`` sull'update (niente double-charge da
    double-click/retry: il secondo tentativo trova il saldo già scalato
    o fallisce il filtro).
  * Accredito con cap: CAS-loop sul saldo letto, ``min(cap, cur+n)``.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException

from app.audit.log import write_audit

GUILD_SUPPLIES_CAP = 120
DAILY_REFILL_VALUE = 120

MARKET_PACK_SUPPLIES = 100
MARKET_PACK_GOLD_COST = 2000

DUNGEON_MANUAL_REWARD = 5
RAID_REWARD = 50
MISSION_REWARD = 10

AUTO_DUNGEON_COST = 15


def _today() -> str:
    """Giorno di gioco (UTC) — stessa convenzione di quest/streak."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def effective_supplies(guild: dict | None, today: str | None = None) -> int:
    """Saldo effettivo SENZA scrivere: considera refill del giorno e
    fallback legacy (campo assente → 120)."""
    if not guild:
        return GUILD_SUPPLIES_CAP
    balance = guild.get("guild_supplies")
    if balance is None:
        return GUILD_SUPPLIES_CAP
    if guild.get("guild_supplies_last_refill") != (today or _today()):
        return DAILY_REFILL_VALUE
    return max(0, min(GUILD_SUPPLIES_CAP, int(balance)))


async def ensure_daily_refill(db, guild_id: str) -> bool:
    """Refill idempotente: qualsiasi saldo → 120 al primo tocco del
    giorno. Ritorna True solo se il refill è avvenuto ADESSO."""
    today = _today()
    res = await db.guilds.update_one(
        {"id": guild_id, "guild_supplies_last_refill": {"$ne": today}},
        {"$set": {
            "guild_supplies": DAILY_REFILL_VALUE,
            "guild_supplies_last_refill": today,
            "updated_at": _now_iso(),
        }},
    )
    refilled = bool(getattr(res, "modified_count", 0))
    if refilled:
        try:
            await write_audit(
                db,
                event_type="guild_supplies_daily_refill",
                actor_user_id=None,
                actor_guild_id=guild_id,
                source="guild_supplies.daily_refill",
                metadata={"value": DAILY_REFILL_VALUE, "day": today},
            )
        except Exception:
            pass
    return refilled


async def get_supplies(db, guild_id: str) -> dict:
    """Stato corrente (dopo il refill lazy)."""
    await ensure_daily_refill(db, guild_id)
    guild = await db.guilds.find_one(
        {"id": guild_id},
        {"_id": 0, "guild_supplies": 1, "guild_supplies_last_refill": 1},
    )
    return {
        "supplies": effective_supplies(guild),
        "cap": GUILD_SUPPLIES_CAP,
        "last_refill": (guild or {}).get("guild_supplies_last_refill"),
    }


async def spend_supplies(
    db,
    guild_id: str,
    amount: int,
    *,
    reason: str,
    event_type: str,
    actor_user_id: str | None = None,
    metadata: dict | None = None,
) -> int:
    """Scala `amount` Beni in modo atomico. 409 se insufficienti."""
    if amount <= 0:
        raise ValueError("amount must be positive")
    await ensure_daily_refill(db, guild_id)
    res = await db.guilds.update_one(
        {"id": guild_id, "guild_supplies": {"$gte": amount}},
        {"$inc": {"guild_supplies": -amount},
         "$set": {"updated_at": _now_iso()}},
    )
    if not getattr(res, "modified_count", 0):
        raise HTTPException(
            status_code=409,
            detail={
                "code": "guild_supplies.insufficient",
                "required": amount,
                "user_message": (
                    "Beni di Gilda insufficienti. "
                    f"Servono {amount} Beni di Gilda."
                ),
            },
        )
    guild = await db.guilds.find_one(
        {"id": guild_id}, {"_id": 0, "guild_supplies": 1},
    )
    balance = int((guild or {}).get("guild_supplies", 0))
    try:
        await write_audit(
            db,
            event_type=event_type,
            actor_user_id=actor_user_id,
            actor_guild_id=guild_id,
            source=f"guild_supplies.{reason}",
            metadata={
                "amount": -amount,
                "balance_after": balance,
                **(metadata or {}),
            },
        )
    except Exception:
        pass
    return balance


async def grant_supplies(
    db,
    guild_id: str,
    amount: int,
    *,
    reason: str,
    event_type: str,
    metadata: dict | None = None,
) -> int:
    """Accredita `amount` Beni con cap 120 (CAS-loop, mai oltre il cap)."""
    if amount <= 0:
        return await _current_balance(db, guild_id)
    await ensure_daily_refill(db, guild_id)
    balance = None
    for _ in range(5):
        guild = await db.guilds.find_one(
            {"id": guild_id},
            {"_id": 0, "guild_supplies": 1, "guild_supplies_last_refill": 1},
        )
        if guild is None:
            return 0
        current = effective_supplies(guild)
        target = min(GUILD_SUPPLIES_CAP, current + amount)
        res = await db.guilds.update_one(
            {"id": guild_id, "guild_supplies": guild.get("guild_supplies")},
            {"$set": {
                "guild_supplies": target,
                "updated_at": _now_iso(),
            }},
        )
        if getattr(res, "modified_count", 0):
            balance = target
            break
    if balance is None:
        # Contesa anomala: nessun accredito silenzioso oltre cap.
        balance = await _current_balance(db, guild_id)
        return balance
    try:
        await write_audit(
            db,
            event_type=event_type,
            actor_user_id=None,
            actor_guild_id=guild_id,
            source=f"guild_supplies.{reason}",
            metadata={
                "amount": amount,
                "balance_after": balance,
                "capped": balance >= GUILD_SUPPLIES_CAP,
                **(metadata or {}),
            },
        )
    except Exception:
        pass
    return balance


async def _current_balance(db, guild_id: str) -> int:
    guild = await db.guilds.find_one(
        {"id": guild_id},
        {"_id": 0, "guild_supplies": 1, "guild_supplies_last_refill": 1},
    )
    return effective_supplies(guild)


async def purchase_market_pack(
    db, guild: dict, *, actor_user_id: str | None,
) -> dict:
    """Mercato: 100 Beni per 2000 MO. Bloccato se il pacchetto non è
    interamente utilizzabile (cap 120): niente Beni persi in silenzio."""
    guild_id = guild["id"]
    await ensure_daily_refill(db, guild_id)
    fresh = await db.guilds.find_one(
        {"id": guild_id},
        {"_id": 0, "gold": 1, "guild_supplies": 1,
         "guild_supplies_last_refill": 1},
    )
    balance = effective_supplies(fresh)
    max_usable = GUILD_SUPPLIES_CAP - balance
    if max_usable < MARKET_PACK_SUPPLIES:
        lost = MARKET_PACK_SUPPLIES - max_usable
        raise HTTPException(
            status_code=409,
            detail={
                "code": "guild_supplies.pack_exceeds_cap",
                "balance": balance,
                "cap": GUILD_SUPPLIES_CAP,
                "pack": MARKET_PACK_SUPPLIES,
                "lost": lost,
                "user_message": (
                    f"Hai {balance}/{GUILD_SUPPLIES_CAP} Beni di Gilda: "
                    f"del pacchetto da {MARKET_PACK_SUPPLIES} ne andrebbero "
                    f"persi {lost}. Usa prima i tuoi Beni."
                ),
            },
        )
    # Atomico: oro sufficiente E saldo ancora compatibile col cap.
    res = await db.guilds.update_one(
        {
            "id": guild_id,
            "gold": {"$gte": MARKET_PACK_GOLD_COST},
            "guild_supplies": {
                "$lte": GUILD_SUPPLIES_CAP - MARKET_PACK_SUPPLIES
            },
        },
        {"$inc": {
            "gold": -MARKET_PACK_GOLD_COST,
            "guild_supplies": MARKET_PACK_SUPPLIES,
        }, "$set": {"updated_at": _now_iso()}},
    )
    if not getattr(res, "modified_count", 0):
        current = await db.guilds.find_one(
            {"id": guild_id}, {"_id": 0, "gold": 1},
        )
        if int((current or {}).get("gold", 0)) < MARKET_PACK_GOLD_COST:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "guild_supplies.not_enough_gold",
                    "cost": MARKET_PACK_GOLD_COST,
                    "user_message": (
                        f"Oro insufficiente: servono "
                        f"{MARKET_PACK_GOLD_COST} MO."
                    ),
                },
            )
        raise HTTPException(
            status_code=409,
            detail={
                "code": "guild_supplies.pack_exceeds_cap",
                "user_message": (
                    "Il saldo è cambiato: il pacchetto supererebbe il cap."
                ),
            },
        )
    state = await db.guilds.find_one(
        {"id": guild_id}, {"_id": 0, "gold": 1, "guild_supplies": 1},
    )
    try:
        await write_audit(
            db,
            event_type="guild_supplies_market_purchase",
            actor_user_id=actor_user_id,
            actor_guild_id=guild_id,
            source="guild_supplies.market",
            metadata={
                "pack": MARKET_PACK_SUPPLIES,
                "gold_cost": MARKET_PACK_GOLD_COST,
                "balance_after": int((state or {}).get("guild_supplies", 0)),
            },
        )
    except Exception:
        pass
    return {
        "supplies": int((state or {}).get("guild_supplies", 0)),
        "cap": GUILD_SUPPLIES_CAP,
        "gold": int((state or {}).get("gold", 0)),
    }


__all__ = [
    "AUTO_DUNGEON_COST",
    "DAILY_REFILL_VALUE",
    "DUNGEON_MANUAL_REWARD",
    "GUILD_SUPPLIES_CAP",
    "MARKET_PACK_GOLD_COST",
    "MARKET_PACK_SUPPLIES",
    "MISSION_REWARD",
    "RAID_REWARD",
    "effective_supplies",
    "ensure_daily_refill",
    "get_supplies",
    "grant_supplies",
    "purchase_market_pack",
    "spend_supplies",
]
