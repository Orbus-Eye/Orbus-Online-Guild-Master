"""RT2-B-2B-1 · Class-state transition models (events, results, reason codes).

Modelli dati immutabili (frozen dataclass) per le transizioni class-state.
Nessuna dipendenza HTTP/Mongo/frontend.

Verdetti PM Message 151:
- B2BQ01 · phase model = SINGLE_EXPEDITION_PHASE_V1
- B2BQ02 · entry point = ExpeditionRuntimeCoordinator.dispatch_class_state_event
- B2BQ06 · Drain completion output = audit-only (drain reference used solo per
  Fragment gain gate — Drain runtime deferred a RT2-B-2B-2)
- B2BQ07 · Fragment gain source = accepted Drain completion only
- B2BQ14 · receipt cap 512 total / 504 ordinary / 8 reserved
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple


# ═══════════════════════ Event types ═══════════════════════
class ClassEventType(str, Enum):
    """Tipi di eventi class-state autorizzati in RT2-B-2B-1.

    Drain start/complete/cancel = **DEFERRED** a RT2-B-2B-2.
    """

    # Mark lifecycle
    APPLY_MARK = "APPLY_MARK"
    REFRESH_MARK = "REFRESH_MARK"
    LAZY_MARK_EXPIRATION = "LAZY_MARK_EXPIRATION"
    OPPORTUNISTIC_MARK_CLEANUP = "OPPORTUNISTIC_MARK_CLEANUP"

    # Fragment lifecycle
    GAIN_FRAGMENT = "GAIN_FRAGMENT"
    SPEND_FRAGMENT = "SPEND_FRAGMENT"
    RESET_FRAGMENTS = "RESET_FRAGMENTS"
    DISCARD_FRAGMENT_OVERFLOW = "DISCARD_FRAGMENT_OVERFLOW"

    # Drain lifecycle (RT2-B-2B-2-1 · PM Message 170 B2B2Q16)
    START_DRAIN = "START_DRAIN"
    COMPLETE_DRAIN = "COMPLETE_DRAIN"
    CANCEL_DRAIN = "CANCEL_DRAIN"

    # Resource segment lifecycle
    OPEN_RESOURCE_SEGMENT = "OPEN_RESOURCE_SEGMENT"
    CLOSE_RESOURCE_SEGMENT = "CLOSE_RESOURCE_SEGMENT"
    AUTO_CLOSE_ON_ZERO = "AUTO_CLOSE_ON_ZERO"
    AUTO_CLOSE_ON_PHASE_END = "AUTO_CLOSE_ON_PHASE_END"
    AUTO_CLOSE_ON_EXPEDITION_TERMINAL = "AUTO_CLOSE_ON_EXPEDITION_TERMINAL"

    # Lifecycle receipts (RESERVED category, 8 slots)
    PHASE_END = "PHASE_END"
    EXPEDITION_TERMINAL = "EXPEDITION_TERMINAL"
    CLEANUP_CRITICAL = "CLEANUP_CRITICAL"


# ═══════════════════════ Receipt category ═══════════════════════
class ReceiptCategory(str, Enum):
    """Categorizzazione receipt per cap enforcement (B2BQ14 · 504+8 = 512)."""

    ORDINARY = "ORDINARY"
    RESERVED = "RESERVED"


# Eventi che consumano una receipt slot RESERVED (max 8).
RESERVED_EVENT_TYPES: frozenset[str] = frozenset({
    ClassEventType.PHASE_END.value,
    ClassEventType.EXPEDITION_TERMINAL.value,
    ClassEventType.CLEANUP_CRITICAL.value,
    ClassEventType.AUTO_CLOSE_ON_PHASE_END.value,
    ClassEventType.AUTO_CLOSE_ON_EXPEDITION_TERMINAL.value,
})


def categorize_event(event_type: str) -> ReceiptCategory:
    """Ritorna categoria receipt per un event_type. Fail-safe: ordinary default."""
    if event_type in RESERVED_EVENT_TYPES:
        return ReceiptCategory.RESERVED
    return ReceiptCategory.ORDINARY


# ═══════════════════════ Result codes ═══════════════════════
class TransitionResultCode(str, Enum):
    """Codici risultato canonici delle transizioni class-state.

    Superset semantico dei CasResultCode: aggiunge i codici applicativi
    (cap, ownership, receipt saturation, feature gating).
    """

    # Success
    SUCCESS = "SUCCESS"

    # Feature gating
    FEATURE_DISABLED = "FEATURE_DISABLED"
    TEST_USER_BOUNDARY_VIOLATION = "TEST_USER_BOUNDARY_VIOLATION"
    DB_NOT_ALLOWLISTED = "DB_NOT_ALLOWLISTED"

    # Ownership / validation
    OWNERSHIP_INVALID = "OWNERSHIP_INVALID"
    TARGET_INVALID = "TARGET_INVALID"
    SOURCE_INVALID = "SOURCE_INVALID"

    # Mark
    MARK_ALREADY_ACTIVE_FOR_PAIR = "MARK_ALREADY_ACTIVE_FOR_PAIR"
    MARK_CAP_EXCEEDED = "MARK_CAP_EXCEEDED"
    MARK_EXPIRED = "MARK_EXPIRED"
    MARK_NOT_FOUND = "MARK_NOT_FOUND"

    # Fragment
    FRAGMENT_CAP_REACHED = "FRAGMENT_CAP_REACHED"
    FRAGMENT_INSUFFICIENT = "FRAGMENT_INSUFFICIENT"
    FRAGMENT_INVALID_AMOUNT = "FRAGMENT_INVALID_AMOUNT"
    FRAGMENT_GAIN_UNAUTHORIZED = "FRAGMENT_GAIN_UNAUTHORIZED"
    FRAGMENT_OVERFLOW_DISCARDED = "FRAGMENT_OVERFLOW_DISCARDED"

    # Resource segment
    SEGMENT_NOT_OPEN = "SEGMENT_NOT_OPEN"
    FOCUS_BONUS_CAP_EXCEEDED = "FOCUS_BONUS_CAP_EXCEEDED"

    # Receipt / atomicity
    RECEIPT_CAP_REACHED = "RECEIPT_CAP_REACHED"
    RESERVED_CAPACITY_EXHAUSTED = "RESERVED_CAPACITY_EXHAUSTED"
    EVENT_ID_PAYLOAD_MISMATCH = "EVENT_ID_PAYLOAD_MISMATCH"
    DEDUPLICATED_NO_OP = "DEDUPLICATED_NO_OP"
    STATE_VERSION_CONFLICT = "STATE_VERSION_CONFLICT"
    STALE_WRITER_REJECTED = "STALE_WRITER_REJECTED"
    CAS_WITHOUT_VALID_LEASE = "CAS_WITHOUT_VALID_LEASE"

    # Ordering / phase
    EVENT_POST_TERMINAL_REJECTED = "EVENT_POST_TERMINAL_REJECTED"
    PHASE_ENDED = "PHASE_ENDED"

    # Retry ceiling
    RETRY_CEILING_EXCEEDED = "RETRY_CEILING_EXCEEDED"

    # ── RT2-B-2B-2-1 · Drain canonical result codes (B2B2Q09 verbatim) ──
    # Success
    DRAIN_STARTED = "DRAIN_STARTED"
    DRAIN_COMPLETED = "DRAIN_COMPLETED"
    DRAIN_CANCELLED = "DRAIN_CANCELLED"
    # Start rejection (MARK_NOT_FOUND · MARK_EXPIRED · TARGET_INVALID ·
    # SOURCE_INVALID · RECEIPT_CAP_REACHED già presenti sopra)
    DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR = "DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR"
    MARK_OWNERSHIP_MISMATCH = "MARK_OWNERSHIP_MISMATCH"
    MARK_APPLICATION_CHANGED = "MARK_APPLICATION_CHANGED"
    EXPEDITION_TERMINAL_REJECTED = "EXPEDITION_TERMINAL_REJECTED"
    PHASE_INACTIVE = "PHASE_INACTIVE"
    # State rejection
    DRAIN_NOT_STARTED = "DRAIN_NOT_STARTED"
    DRAIN_ALREADY_COMPLETED = "DRAIN_ALREADY_COMPLETED"
    DRAIN_ALREADY_CANCELLED = "DRAIN_ALREADY_CANCELLED"
    # Integrity/concurrency (EVENT_ID_PAYLOAD_MISMATCH ·
    # STATE_VERSION_CONFLICT · STALE_WRITER_REJECTED già presenti sopra)
    LEASE_ACQUISITION_FAILED = "LEASE_ACQUISITION_FAILED"
    RETRY_LIMIT_REACHED = "RETRY_LIMIT_REACHED"

    # Infra / unexpected
    STATE_DOCUMENT_SIZE_BUDGET_EXCEEDED = "STATE_DOCUMENT_SIZE_BUDGET_EXCEEDED"
    NOT_FOUND = "NOT_FOUND"


# ═══════════════════════ Reason codes (B2BQ05 verbatim) ═══════════════════════
class ReasonCode(str, Enum):
    """Reason codes obbligatori per cancellation / rejection.

    B2BQ05 verbatim (Drain cancellation) — riutilizzato per rejection context
    dove semanticamente applicabile.
    """

    MARK_EXPIRED = "MARK_EXPIRED"
    MARK_OWNERSHIP_MISMATCH = "MARK_OWNERSHIP_MISMATCH"
    MARK_APPLICATION_CHANGED = "MARK_APPLICATION_CHANGED"
    TARGET_INVALID = "TARGET_INVALID"
    SOURCE_INVALID = "SOURCE_INVALID"
    PHASE_ENDED = "PHASE_ENDED"
    EXPEDITION_TERMINAL = "EXPEDITION_TERMINAL"
    EXPLICIT_SERVER_CANCEL = "EXPLICIT_SERVER_CANCEL"


# ═══════════════════════ Trusted Drain receipt (fixture-only in RT2-B-2B-1) ═══════════════════════
@dataclass(frozen=True)
class TrustedDrainReceipt:
    """Ricevuta Drain completata usata SOLO come fixture di test in RT2-B-2B-1.

    B2BQ07 verbatim: `GAIN_FRAGMENT` valido richiede accepted `drain_execution_id`
    + accepted Drain completion receipt. In RT2-B-2B-1 (Drain runtime deferred),
    questa receipt è generata SOLO da test fixture server-side. Nessun code path
    gameplay/client/admin può crearla.

    NON usare in produzione — marker esplicito.
    """

    drain_execution_id: str
    source_adventurer_id: str
    target_id: str
    mark_application_id: str  # application_id del Mark valido alla completion
    completed_at: str  # ISO UTC
    result_code: str = "SUCCESS"
    expedition_id: str = ""
    phase_id: str = ""
    fixture_only_marker: str = "RT2B2B1_TRUSTED_FIXTURE_ONLY"


# ═══════════════════════ Class state event ═══════════════════════
@dataclass(frozen=True)
class ClassStateEvent:
    """Evento class-state con schema minimo (B2BQ02 verbatim).

    Client fields:
        event_id · event_type · expedition_id · source_adventurer_id · target_id?
        payload_version · payload_hash · requested_at · expected_state_version
    Server-derived (assigned dal dispatcher):
        event_sequence · fencing_validation · processed_at · result_code

    Il client NON controlla event_sequence/fencing_token/owner/cap/result_code.
    """

    event_id: str
    event_type: str  # ClassEventType value
    expedition_id: str
    source_adventurer_id: str
    payload_version: int
    payload_hash: str
    requested_at: str  # ISO UTC
    expected_state_version: int
    target_id: Optional[str] = None
    amount: int = 0  # per fragment spend/gain (0..5)
    reason_code: Optional[str] = None
    trusted_drain_receipt: Optional[TrustedDrainReceipt] = None
    phase_id: Optional[str] = None
    # RT2-B-2B-2-1: targeting per COMPLETE_DRAIN / CANCEL_DRAIN.
    # Il client NON genera mai questo ID (server-authoritative a START_DRAIN,
    # B2B2Q01); qui referenzia soltanto un execution ID già assegnato.
    drain_execution_id: Optional[str] = None


# ═══════════════════════ Transition result ═══════════════════════
@dataclass(frozen=True)
class TransitionResult:
    """Risultato di una transizione class-state.

    Contratto (B2BQ06): audit-only, NO gameplay payload.
    """

    code: TransitionResultCode
    event_id: str
    event_type: str
    expedition_id: str
    source_adventurer_id: str
    assigned_event_sequence: Optional[int] = None
    state_version_before: Optional[int] = None
    state_version_after: Optional[int] = None
    duration_ms: float = 0.0
    reason_code: Optional[str] = None
    mark_id: Optional[str] = None
    mark_application_id: Optional[str] = None
    resource_segment_id: Optional[str] = None
    fragment_count_after: Optional[int] = None
    active_marks_count_after: Optional[int] = None
    focus_bonus_used_after: Optional[int] = None
    overflow_discarded: int = 0
    retry_attempts: int = 0
    dedup_reference: Optional[str] = None
    # ── RT2-B-2B-2-1 · Drain result fields (B2B2Q07/Q08/Q11) ──
    drain_execution_id: Optional[str] = None
    cancellation_reason: Optional[str] = None
    fragment_gain_requested: int = 0
    fragment_gain_applied: int = 0
    fragment_overflow_discarded: int = 0
    mark_valid_at_completion: Optional[bool] = None
    drains_cancelled_count: int = 0
    cancelled_drain_execution_ids: Tuple[str, ...] = ()

    @property
    def success(self) -> bool:
        return self.code in _SUCCESS_CODES

    @property
    def is_dedup_noop(self) -> bool:
        return self.code is TransitionResultCode.DEDUPLICATED_NO_OP


# Success family: SUCCESS legacy + Drain canonical success codes (B2B2Q09).
_SUCCESS_CODES: frozenset = frozenset({
    TransitionResultCode.SUCCESS,
    TransitionResultCode.DRAIN_STARTED,
    TransitionResultCode.DRAIN_COMPLETED,
    TransitionResultCode.DRAIN_CANCELLED,
})


__all__ = [
    "ClassEventType",
    "ClassStateEvent",
    "ReasonCode",
    "ReceiptCategory",
    "RESERVED_EVENT_TYPES",
    "TransitionResult",
    "TransitionResultCode",
    "TrustedDrainReceipt",
    "categorize_event",
]
