"""ROUND 16.5.3 P0.2 — Cross-domain activity sweep helper.

Rilascia lazy le squadre bloccate per attività scadute (expedition,
raid, resource mission) su read-time endpoints che il player visita
comunemente (roster list, roster health, guilds/me).

Motivazione: prima di R16.5.3 la release avveniva solo lazy dagli
endpoint domain-specific (GET /api/expeditions, GET /api/raids, ecc).
Se il player finiva un'expedition e apriva solo il roster senza mai
cliccare sul report, gli avv restavano `is_available=false` finché
non passava da uno di quegli endpoint. Bug UX-facing.

Fix: un helper unico `sweep_activities_for_guild` che chiama i 3
resolver sync in sequenza best-effort. Idempotenza garantita dai
CAS interni dei resolver esistenti (nessun double-reward).

Note tecniche:
  - Best-effort: nessuna exception si propaga; log warning se
    qualcosa fallisce (rare-path, non blocca la request principale).
  - I resolver interni sono già rate-limited su `completes_at <= now`
    e su CAS `status` — non toccano attività non scadute.
  - Latenza tipica: <30ms per guild con 0 attività in coda, ~80ms
    con 3 attività scadute contemporanee.
"""
from __future__ import annotations

import logging

_LOG = logging.getLogger("orbus.activity_sweep")


async def sweep_activities_for_guild(db, guild_id: str) -> None:
    """Chiude expedition/raid/resource mission scaduti per la gilda.

    Chiamato dai read-time endpoints "pass-through" (roster list,
    roster health, guilds/me) per garantire che il player veda
    sempre lo stato aggiornato senza dover navigare specificamente
    sulla pagina della singola attività.

    Idempotente: tutti e 3 i resolver sotto usano CAS interno; chiamate
    ripetute NON generano double-reward né double-audit.

    Best-effort: exception in un resolver NON blocca gli altri due
    né la request principale. Le eccezioni vengono loggate a livello
    WARNING per debug ma non propagate.
    """
    if not guild_id:
        return

    # 1. Expeditions (dungeon) — resolver Phase 5.5e.
    try:
        from app.expeditions.services import complete_due_expeditions
        await complete_due_expeditions(db, guild_id)
    except Exception as exc:  # noqa: BLE001
        _LOG.warning(
            "activity_sweep.expeditions_failed guild_id=%s err=%s",
            guild_id, exc,
        )

    # 2. Raids — recovery hotfix R16.1.1.
    try:
        from app.raids.recovery import auto_resolve_stuck_raids_for_guild
        await auto_resolve_stuck_raids_for_guild(db, guild_id)
    except Exception as exc:  # noqa: BLE001
        _LOG.warning(
            "activity_sweep.raids_failed guild_id=%s err=%s",
            guild_id, exc,
        )

    # 3. Resource missions (world missions) — R16.3 resource domain.
    try:
        from app.resources import _resolve_expired_missions_for_guild
        await _resolve_expired_missions_for_guild(guild_id)
    except Exception as exc:  # noqa: BLE001
        _LOG.warning(
            "activity_sweep.resource_missions_failed guild_id=%s err=%s",
            guild_id, exc,
        )


__all__ = ["sweep_activities_for_guild"]
