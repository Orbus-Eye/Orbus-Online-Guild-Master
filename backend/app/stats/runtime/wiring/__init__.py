"""RT2-B-2A · Local Shadow Wiring & State Lifecycle Foundation.

Modulo isolato per il cablaggio SHADOW del `MongoExpeditionRuntimeStateStore`
al lifecycle applicativo delle spedizioni.

Regole invarianti (PM verdicts B2Q01..B2Q12 · 2026-02):
- **Wiring layer = EXPEDITION SERVICE ORCHESTRATION LAYER** (B2Q01).
- **Calcolo corrente resta autoritativo** — nessuna autorità gameplay per il runtime state.
- **First integration mode = LOCAL SHADOW ONLY** (B2Q02 · B2Q10).
- **Doppio guardrail** obbligatorio:
    1. `feature_flags.is_enabled("cdv_transient_state_enabled")` (B2Q07).
    2. `users.is_test_user == True` server-authoritative (B2Q06 fail-closed).
- **Adapter = application-scoped dependency**; **Coordinator = request-scoped** (B2Q11 + B2Q03).
- **Class gameplay transitions = NONE** in RT2-B-2A (B2Q09).
- **Terminalization** = COMPLETED / CANCELLED / COMPLETED_WITH_FAILURE (B2Q04).
- **Fallback isolation policy** (B2Q08): failure → gameplay preserved + audit warn,
  no partial mutation, no automatic fallback, no silent granting.
- **Audit destination** = existing server-side substrate (B2Q05); no new collection,
  no public endpoint, no player-facing log.
- **Anti-P2W**: nessun bonus derivato dal transient state su gold/xp/rank/economy.

Public API:
- `ExpeditionRuntimeCoordinator` — request-scoped coordinator.
- `maybe_shadow_dispatch(db, current_user, guild, expedition_doc)` — hook post-validation.
- `maybe_shadow_terminalize(db, expedition_doc, success)` — hook post-completion.
"""
from __future__ import annotations

from app.stats.runtime.wiring.coordinator import (
    ExpeditionRuntimeCoordinator,
    TerminalOutcome,
)
from app.stats.runtime.wiring.shadow_hooks import (
    maybe_shadow_dispatch,
    maybe_shadow_terminalize,
)

__all__ = [
    "ExpeditionRuntimeCoordinator",
    "TerminalOutcome",
    "maybe_shadow_dispatch",
    "maybe_shadow_terminalize",
]
