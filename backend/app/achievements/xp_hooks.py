"""ROUND 16.5.3 P1 — Guild XP "Prestigio di Gilda" activity drip hooks (V1 bare-minimum).

Aggiunge XP di Prestigio di Gilda su 3 attività core:
  * Expedition completed (success +15, fail +5) — cap 8/giorno
  * Raid completed (victory +80, partial +40, defeat +15) — cap 1/giorno
  * Resource mission completed (success +10) — cap 6/giorno

Vincoli architetturali (Round 16.5.3 STEP 2.B, PM-approved):
  1. **NO backfill retroattivo**: gli hook si attivano SOLO su nuove
     completion post-deploy. Le attività storiche restano invariate.
  2. **Idempotenza per activity_id**: usa `source_id` come chiave unica
     di dedup. Se lo stesso `source_id` è già stato creditato → skip
     silent (no double-XP anche in caso di sweep re-run).
  3. **Cap giornaliero UTC-fair**: nuova collection
     `guild_xp_daily_cap_tracker` con unique index
     `(guild_id, source, date_utc_iso)`. Increment via CAS
     `find_one_and_update` con condizione `count < cap`.
  4. **Best-effort**: exception NON propagata; XP guild non è un
     side-effect critico dell'attività principale.
  5. **Audit trail**: ogni credit passa da `add_guild_xp` che emette
     `guild_xp_gained` con source distinto.

Cap raid — decisione tecnica del round:
  Scelto **1/giorno** (invece di 3/settimana) per allineamento col
  pattern giornaliero di expedition/resource. La collection tracker
  usa la stessa granularità UTC per tutte e 3 le sorgenti,
  semplificando la reset logic (midnight UTC comune).

Payload minimo per il FE:
  Il FE non ha bisogno di conoscere lo stato del cap in dettaglio
  per V1 — il suggerimento "Cosa fare per salire" è statico. V2 potrà
  esporre lo stato residuo via `GET /api/guilds/me/xp-progress`.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

_LOG = logging.getLogger("orbus.xp_hooks")


# Cap giornaliero per source (chiave = source string).
# Valori PM-approvati (STEP 2.B, Q4-a con raid modificato a 1/giorno).
_DAILY_CAP: dict[str, int] = {
    "expedition_completed": 8,   # 8 expedition/giorno max (drip 15 XP each → 120 XP/day cap)
    "raid_completed":       1,   # 1 raid/giorno max (drip 80 max → 80 XP/day cap)
    "resource_mission":     6,   # 6 mission/giorno max (drip 10 each → 60 XP/day cap)
}


def _today_utc_iso_date() -> str:
    """YYYY-MM-DD UTC. Reset del cap a mezzanotte UTC."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


async def _already_credited(db, guild_id: str, source: str,
                             source_id: str) -> bool:
    """Idempotency check: activity_id già creditato?

    Le audit rows di `add_guild_xp` includono `related_entity_id =
    source_id`. Un match esatto (guild + source + source_id) indica che
    lo stesso event è stato già processato → skip silent.
    """
    if not source_id:
        return False
    try:
        existing = await db.audit_log.find_one(
            {
                "event_type": "guild_xp_gained",
                "actor_guild_id": guild_id,
                "source": source,
                "related_entity_id": source_id,
            },
            {"_id": 1},
        )
        return existing is not None
    except Exception:  # noqa: BLE001
        return False


# Lazy bootstrap flag — la prima chiamata dopo import garantisce
# la presenza dell'unique index (cross-fork safety per test isolati).
_INDEX_READY_DB_IDS: set[int] = set()


async def _try_reserve_cap_slot(db, guild_id: str, source: str) -> bool:
    """CAS-based cap slot reservation.

    Returns True se il cap non era ancora saturo (slot riservato).
    Returns False se il cap è raggiunto (skip silent, no XP credited).

    Uso: aumenta il counter atomicamente solo se `count < cap`. Se
    fallisce → cap raggiunto per oggi. Idempotente (l'aumento avviene
    solo su una chiamata effettiva post-check).
    """
    cap = _DAILY_CAP.get(source, 0)
    if cap <= 0:
        return False
    # Lazy bootstrap dell'unique index (safe se già presente).
    if id(db) not in _INDEX_READY_DB_IDS:
        try:
            await ensure_cap_tracker_indexes(db)
        except Exception:
            pass
        _INDEX_READY_DB_IDS.add(id(db))
    date_iso = _today_utc_iso_date()
    try:
        # Try to reserve: increment count only if `count < cap` (via find_one_and_update).
        # Motor doesn't support conditional $inc in a single op cleanly, so use two-step CAS:
        # 1) find with count<cap → update+1
        # 2) if not found → try insert (first credit of the day)
        r = await db.guild_xp_daily_cap_tracker.find_one_and_update(
            {
                "guild_id": guild_id,
                "source": source,
                "date_utc_iso": date_iso,
                "count": {"$lt": cap},
            },
            {"$inc": {"count": 1}},
            upsert=False,
        )
        if r:
            return True  # existing tracker, incremented within cap
        # No existing under-cap row. Two possibilities:
        # a) No row today → insert with count=1
        # b) Row exists but count>=cap → cap already reached
        try:
            await db.guild_xp_daily_cap_tracker.insert_one({
                "guild_id": guild_id,
                "source": source,
                "date_utc_iso": date_iso,
                "count": 1,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            return True
        except Exception:
            # Duplicate key → the row exists, and count>=cap (else the
            # find_one_and_update above would have matched). Cap reached.
            return False
    except Exception as exc:  # noqa: BLE001
        _LOG.warning("xp_hooks.cap_reserve_failed guild=%s source=%s err=%s",
                     guild_id, source, exc)
        return False


async def _credit_xp(db, guild_id: str, source: str, amount: int,
                     source_id: Optional[str] = None) -> Optional[dict]:
    """Credit XP + audit se non già creditato + cap non ancora saturo.

    Returns snapshot post-credit oppure None se:
      - idempotency skip (già creditato)
      - cap raggiunto per oggi
      - errore infra
    """
    if amount <= 0 or not guild_id or not source:
        return None
    # Step 1: idempotency (activity-level dedup)
    if source_id and await _already_credited(db, guild_id, source, source_id):
        return None
    # Step 2: cap reservation
    if not await _try_reserve_cap_slot(db, guild_id, source):
        return None
    # Step 3: credit + audit via canonical helper.
    try:
        from app.achievements.engine import add_guild_xp
        snap = await add_guild_xp(
            db, guild_id, amount,
            source=source, source_id=source_id,
        )
        return snap
    except Exception as exc:  # noqa: BLE001
        _LOG.warning("xp_hooks.credit_failed guild=%s source=%s err=%s",
                     guild_id, source, exc)
        return None


# ═════════════════════════════════════════════════════════════════════
# PUBLIC HOOKS — chiamati dai resolver dei domini
# ═════════════════════════════════════════════════════════════════════

async def on_expedition_completed(db, guild_id: str, *, expedition_id: str,
                                    success: bool) -> Optional[dict]:
    """Drip XP per expedition completed.

    +15 su successo, +5 su fail. Cap 8/giorno.
    Idempotente su expedition_id.
    """
    amount = 15 if success else 5
    return await _credit_xp(
        db, guild_id, source="expedition_completed",
        amount=amount, source_id=expedition_id,
    )


async def on_raid_completed(db, guild_id: str, *, raid_id: str,
                              outcome: str) -> Optional[dict]:
    """Drip XP per raid completed.

    +80 victory, +40 partial, +15 defeat/fail. Cap 1/giorno.
    Idempotente su raid_id.
    """
    outcome_normalized = (outcome or "").lower()
    if outcome_normalized == "victory":
        amount = 80
    elif outcome_normalized == "partial":
        amount = 40
    else:
        amount = 15
    return await _credit_xp(
        db, guild_id, source="raid_completed",
        amount=amount, source_id=raid_id,
    )


async def on_resource_mission_completed(db, guild_id: str, *,
                                          mission_id: str,
                                          success: bool,
                                          rarity: Optional[str] = None) -> Optional[dict]:
    """Drip XP per resource mission completed.

    ROUND 17.2 P0.3 — XP tier per resource rarity:
        rare → +8 XP Prestigio
        epic → +10 XP Prestigio
        (fallback: +10 se rarity unknown, backward-compat R16.5.3)
    Cap 6/giorno. Nessun consolation su fail (le mission fallite non danno XP guild).
    Idempotente su mission_id.
    """
    if not success:
        return None
    amount = 10  # backward-compat default (matches pre-R17.2 behavior)
    if rarity == "rare":
        amount = 8
    elif rarity == "epic":
        amount = 10
    return await _credit_xp(
        db, guild_id, source="resource_mission",
        amount=amount, source_id=mission_id,
    )


async def ensure_cap_tracker_indexes(db) -> None:
    """Idempotent index creation for the cap tracker collection.

    Chiamato al boot dell'app tramite lifespan; safe da chiamare
    ripetutamente."""
    try:
        await db.guild_xp_daily_cap_tracker.create_index(
            [("guild_id", 1), ("source", 1), ("date_utc_iso", 1)],
            unique=True,
            name="uniq_guild_source_date",
        )
    except Exception as exc:  # noqa: BLE001
        _LOG.warning("xp_hooks.index_create_failed err=%s", exc)


__all__ = [
    "on_expedition_completed",
    "on_raid_completed",
    "on_resource_mission_completed",
    "ensure_cap_tracker_indexes",
]
