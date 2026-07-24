"""RT2-B-2B-1 · SINGLE_EXPEDITION_PHASE_V1 (transitional phase model).

PM Message 151 B2BQ01 verbatim: modello di fase TRANSITORIO.
Un vero combat-phase subsystem richiede version bump + PM adjudication dedicata.

Regole:
- 1 sola fase per spedizione (`phase_id = expedition:<expedition_id>:phase:1`)
- phase start = state initialized dopo expedition validation
- phase end = immediatamente prima expedition terminalization
- stato iniziale: Fragments=0, resource_segment=inactive
- stato finale: Fragments→0, resource_segment→closed, active Drains→cancelled

Non introduce:
- combat phase subsystem
- scheduler
- phase endpoint
- nuovo phase model persistente
"""
from __future__ import annotations

from typing import Optional

# Version tag della fase transitoria (B2BQ01 verbatim).
SINGLE_EXPEDITION_PHASE_VERSION: str = "SINGLE_EXPEDITION_PHASE_V1"


def build_phase_id(expedition_id: str) -> str:
    """Costruisce il phase_id deterministico per una spedizione.

    Formato: `expedition:<expedition_id>:phase:1`
    """
    if not expedition_id:
        raise ValueError("expedition_id required to build phase_id")
    return f"expedition:{expedition_id}:phase:1"


def parse_expedition_from_phase_id(phase_id: str) -> Optional[str]:
    """Estrae expedition_id da un phase_id ben-formato. Ritorna None se malformato."""
    if not phase_id:
        return None
    prefix = "expedition:"
    suffix = ":phase:1"
    if not phase_id.startswith(prefix) or not phase_id.endswith(suffix):
        return None
    core = phase_id[len(prefix):-len(suffix)]
    if not core:
        return None
    return core


def is_transition_allowed_in_phase(
    phase_ended: bool,
    expedition_terminal: bool,
    event_type: str,
) -> tuple[bool, Optional[str]]:
    """Verifica se una transizione è consentita nella fase corrente.

    Regole (B2BQ01 + B2BQ05):
    - Se `expedition_terminal=True` → ordinary events rejected (post-terminal).
      SOLO lifecycle receipts riservati sono ammessi (già consumati alla terminalizzazione).
    - Se `phase_ended=True` → ordinary events rejected. Auto-close events consentiti.
    - Altrimenti → allowed.

    Returns:
        (allowed, rejection_reason) tuple.
    """
    from app.stats.runtime.transitions.models import RESERVED_EVENT_TYPES

    # Post-terminal boundary
    if expedition_terminal:
        if event_type in RESERVED_EVENT_TYPES:
            return True, None
        return False, "EXPEDITION_TERMINAL"

    if phase_ended:
        if event_type in RESERVED_EVENT_TYPES:
            return True, None
        # Auto-close on phase end è consentito anche se la fase è marcata come chiusa
        # (idempotent no-op path).
        if event_type in ("AUTO_CLOSE_ON_PHASE_END", "CLOSE_RESOURCE_SEGMENT"):
            return True, None
        return False, "PHASE_ENDED"

    return True, None


__all__ = [
    "SINGLE_EXPEDITION_PHASE_VERSION",
    "build_phase_id",
    "is_transition_allowed_in_phase",
    "parse_expedition_from_phase_id",
]
