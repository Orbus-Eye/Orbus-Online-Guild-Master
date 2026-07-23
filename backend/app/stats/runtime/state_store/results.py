"""RT2-B-1A · CAS result types (enum + result dataclasses).

Le operazioni della state store ritornano oggetti tipizzati `CasResult` /
`LeaseAcquireResult` / `ReadResult` invece di sollevare eccezioni sui path
funzionali. Le eccezioni (in `errors.py`) sono riservate a path infra o
programmazione difensiva. Il codice diagnostico `CasResultCode` è
stringato e stabile — pensato per audit event e observability.

`partial mutation` è sempre forbidden: se `code != SUCCESS`, nessun campo
dello stato è stato modificato lato store.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class CasResultCode(str, Enum):
    """Codici canonici degli esiti di ogni operazione state-store.

    Stringati per essere stabili in audit event / receipt senza serialization
    surprise (Enum → str via inherit).
    """

    SUCCESS = "SUCCESS"
    STATE_VERSION_CONFLICT = "STATE_VERSION_CONFLICT"
    STALE_WRITER_REJECTED = "STALE_WRITER_REJECTED"
    DEDUPLICATED_NO_OP = "DEDUPLICATED_NO_OP"
    EVENT_ID_PAYLOAD_MISMATCH = "EVENT_ID_PAYLOAD_MISMATCH"
    OWNERSHIP_INVALID = "OWNERSHIP_INVALID"
    CAP_EXCEEDED = "CAP_EXCEEDED"
    LEASE_EXPIRED = "LEASE_EXPIRED"
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"

    def __str__(self) -> str:  # pragma: no cover — cosmetic
        return self.value


@dataclass(frozen=True)
class CasResult:
    """Risultato di una mutation CAS o di un `apply_event_once`.

    Attributes:
        code: enum `CasResultCode`.
        new_state_version: valore di `state_version` DOPO la mutation (solo se
            code == SUCCESS o code == DEDUPLICATED_NO_OP). Altrimenti None.
        assigned_event_sequence: sequenza server-authoritative assegnata
            (solo per mutation event-scoped). None per operazioni non-event.
        prior_result_reference: puntatore alla receipt precedente in caso di
            DEDUPLICATED_NO_OP (event_id).
        reason: messaggio umano-leggibile opzionale (non usato per branching).
    """

    code: CasResultCode
    new_state_version: Optional[int] = None
    assigned_event_sequence: Optional[int] = None
    prior_result_reference: Optional[str] = None
    reason: Optional[str] = None

    @property
    def success(self) -> bool:
        """True se la mutation ha effettivamente applicato uno state change."""
        return self.code is CasResultCode.SUCCESS

    @property
    def idempotent_noop(self) -> bool:
        """True se il risultato è un no-op idempotente (retry deduplicato)."""
        return self.code is CasResultCode.DEDUPLICATED_NO_OP


@dataclass(frozen=True)
class LeaseAcquireResult:
    """Risultato di `reserve_writer` / `renew_writer_lease`.

    Se `code == SUCCESS`: `lease_id`, `fencing_token`, `lease_expires_at`
    sono valorizzati. Altrimenti None.
    """

    code: CasResultCode
    lease_id: Optional[str] = None
    fencing_token: Optional[int] = None
    lease_expires_at: Optional[str] = None  # ISO UTC str
    reason: Optional[str] = None


@dataclass(frozen=True)
class ReadResult:
    """Risultato di `get_state` / `get_version`.

    Se `code == SUCCESS`: `state` è valorizzato (o `version_only`).
    Se `code == NOT_FOUND`: entrambi None.
    """

    code: CasResultCode
    state: Optional[Any] = None  # ExpeditionRuntimeState (avoid circular import; declared Any)
    version_only: Optional[int] = None
    reason: Optional[str] = None
