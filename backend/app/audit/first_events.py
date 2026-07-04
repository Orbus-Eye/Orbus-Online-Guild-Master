"""ROUND 17.1 — Funnel FIRST_* events helper.

Emit centralizzato con idempotency guard: una sola emissione per gilda
per `event_type`. Best-effort: fallimenti non bloccano mai il flow
principale del route (registrazione, spedizione, ecc.).

Metadata leggero (`guild_id`, `user_id_masked`, `timestamp`). Nessun PII.

Uso:
    from app.audit.first_events import emit_first_event
    await emit_first_event(
        db, event_type="FIRST_ADVENTURER_VIEWED",
        guild_id=guild["id"], user_id=user["id"],
        extra={"context": "list_route"},
    )
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from app.audit.log import write_audit

logger = logging.getLogger("orbus.audit.first_events")

# ─── Constants ───────────────────────────────────────────────────────────
FUNNEL_EVENT_TYPES = frozenset({
    "REGISTERED",
    "GUILD_CREATED",
    "FIRST_ADVENTURER_VIEWED",
    "FIRST_DUNGEON_VIEWED",
    "FIRST_EXPEDITION_PREVIEWED",
    "FIRST_EXPEDITION_STARTED",
    "FIRST_EXPEDITION_COMPLETED",
    "FIRST_REPORT_OPENED",
    "FIRST_PRESTIGE_GAINED",
})


def _mask_user_id(user_id: str) -> str:
    """`3c2603d0-f59a-4715-84d8-6fba5b7696c7` → `3c2603...5b7696c7`.
    Riduce PII residua nei log senza perdere debuggability."""
    if not user_id or len(user_id) < 12:
        return "***"
    return f"{user_id[:6]}...{user_id[-8:]}"


async def emit_first_event(
    db,
    *,
    event_type: str,
    guild_id: Optional[str] = None,
    user_id: Optional[str] = None,
    extra: Optional[dict[str, Any]] = None,
) -> bool:
    """Emit `event_type` una-tantum per gilda.

    Returns:
        True se il doc è stato inserito (prima emissione).
        False se già emesso in precedenza (idempotency HIT) o se input
        invalido (best-effort, non solleva).
    """
    if event_type not in FUNNEL_EVENT_TYPES:
        logger.warning(
            "emit_first_event: unknown event_type %r (must be in FUNNEL_EVENT_TYPES)",
            event_type,
        )
        return False

    # Per `REGISTERED` non c'è ancora una guild → dedupe su user_id.
    dedupe_filter: dict[str, Any] = {"event_type": event_type}
    if guild_id:
        dedupe_filter["actor_guild_id"] = guild_id
    elif user_id:
        dedupe_filter["actor_user_id"] = user_id
    else:
        logger.warning(
            "emit_first_event: %s called without guild_id nor user_id",
            event_type,
        )
        return False

    try:
        existing = await db.audit_log.find_one(dedupe_filter, {"_id": 1})
        if existing is not None:
            # Idempotency HIT — evento già emesso in passato.
            return False

        metadata = {
            "user_id_masked": _mask_user_id(user_id) if user_id else None,
            "emitted_at": datetime.now(timezone.utc).isoformat(),
        }
        if extra:
            metadata.update(extra)

        await write_audit(
            db,
            event_type=event_type,
            actor_user_id=user_id,
            actor_guild_id=guild_id,
            source="r17_funnel",
            related_entity_id=guild_id or user_id,
            metadata=metadata,
        )
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "emit_first_event(%s) failed (best-effort, ignoring): %s",
            event_type, exc,
        )
        return False


__all__ = ["emit_first_event", "FUNNEL_EVENT_TYPES"]
