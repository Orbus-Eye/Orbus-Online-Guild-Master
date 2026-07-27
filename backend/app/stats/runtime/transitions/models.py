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

    # RT2-B-2B-2-1 Drain lifecycle (PM Message 170 §13, §17)
    START_DRAIN = "START_DRAIN"
    COMPLETE_DRAIN = "COMPLETE_DRAIN"
    CANCEL_DRAIN = "CANCEL_DRAIN"


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

    # Infra / unexpected
    STATE_DOCUMENT_SIZE_BUDGET_EXCEEDED = "STATE_DOCUMENT_SIZE_BUDGET_EXCEEDED"
    NOT_FOUND = "NOT_FOUND"

    # ═══ RT2-B-2B-2-1 Drain result codes (PM Message 170 §19 verbatim) ═══
    # Success
    DRAIN_STARTED = "DRAIN_STARTED"
    DRAIN_COMPLETED = "DRAIN_COMPLETED"
    DRAIN_CANCELLED = "DRAIN_CANCELLED"

    # Start rejection
    DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR = "DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR"
    MARK_APPLICATION_CHANGED = "MARK_APPLICATION_CHANGED"
    EXPEDITION_TERMINAL_REJECTED = "EXPEDITION_TERMINAL_REJECTED"
    PHASE_INACTIVE = "PHASE_INACTIVE"

    # Drain state
    DRAIN_NOT_STARTED = "DRAIN_NOT_STARTED"
    DRAIN_ALREADY_COMPLETED = "DRAIN_ALREADY_COMPLETED"
    DRAIN_ALREADY_CANCELLED = "DRAIN_ALREADY_CANCELLED"

    # Identifier bounds (PM §3 verbatim · zero mutation on invalid · no silent truncation)
    EVENT_ID_INVALID = "EVENT_ID_INVALID"

    # Lease/CAS
    LEASE_ACQUISITION_FAILED = "LEASE_ACQUISITION_FAILED"
    RETRY_LIMIT_REACHED = "RETRY_LIMIT_REACHED"

    # Store infra bubbling
    STORE_INFRA_ERROR = "STORE_INFRA_ERROR"


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


# ═══════════════════════ Trusted Drain receipt (DEPRECATED_COMPATIBILITY_ONLY post RT2-B-2B-2-1) ═══════════════════════
@dataclass(frozen=True)
class TrustedDrainReceipt:
    """Ricevuta Drain completata usata SOLO come fixture di test in RT2-B-2B-1.

    ⚠️ DEPRECATED_COMPATIBILITY_ONLY (RT2-B-2B-2-1 PM adjudication §3):
    - Il nuovo runtime Drain (state machine `transitions/drain.py`) ha
      **dipendenza zero** da questo modello.
    - Preservato SOLO per backward compat con test/legacy fixture chain (RT1
      `gain_fragment` gating path).
    - Nessun nuovo codice runtime deve importare/utilizzare questo modello.

    B2BQ07 (RT2-B-2B-1 legacy): `GAIN_FRAGMENT` valido richiedeva accepted
    `drain_execution_id` + accepted Drain completion receipt come fixture.
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


# ═══════════════════════ RT2-B-2B-2-1 · Drain models ═══════════════════════

# Identifier bounds (PM §3 verbatim)
EVENT_ID_MAX_BYTES: int = 96
IDENTIFIER_MAX_BYTES: int = 64  # source_adventurer_id, target_id


def validate_identifier_bounds(
    event_id: str,
    source_adventurer_id: str,
    target_id: str,
) -> Optional["TransitionResultCode"]:
    """Enforce identifier byte-length bounds (PM §3 verbatim).

    - `event_id` ≤ 96 byte UTF-8 → EVENT_ID_INVALID
    - `source_adventurer_id` ≤ 64 byte UTF-8 → SOURCE_INVALID
    - `target_id` ≤ 64 byte UTF-8 → TARGET_INVALID

    Returns:
        `None` if all bounds pass. Otherwise the appropriate rejection code.
        **Never truncates silently** (§3, §7 forbidden).
    """
    if not event_id or len(event_id.encode("utf-8")) > EVENT_ID_MAX_BYTES:
        return TransitionResultCode.EVENT_ID_INVALID
    if not source_adventurer_id or len(source_adventurer_id.encode("utf-8")) > IDENTIFIER_MAX_BYTES:
        return TransitionResultCode.SOURCE_INVALID
    if not target_id or len(target_id.encode("utf-8")) > IDENTIFIER_MAX_BYTES:
        return TransitionResultCode.TARGET_INVALID
    return None


# 8 cancellation reason codes (PM Message 170 §18 verbatim · NO extensions)
DRAIN_CANCEL_REASONS: frozenset[str] = frozenset({
    "MARK_EXPIRED",
    "MARK_OWNERSHIP_MISMATCH",
    "MARK_APPLICATION_CHANGED",
    "TARGET_INVALID",
    "SOURCE_INVALID",
    "PHASE_ENDED",
    "EXPEDITION_TERMINAL",
    "EXPLICIT_SERVER_CANCEL",
})


@dataclass(frozen=True)
class DrainCompletionReceipt:
    """15-field completion payload EMBEDDED in processed event receipt (§25 verbatim).

    PM Message 170 B2B2Q07: **completion receipt = result payload EMBEDDED in the
    processed event receipt** · NON occupare un secondo slot indipendente nella
    capacità 512.

    Emitted from `transitions/drain.py::complete_drain` and folded into the
    single ORDINARY receipt for the COMPLETE_DRAIN event.
    """

    drain_execution_id: str
    completion_event_id: str
    source_adventurer_id: str
    target_id: str
    mark_id: str
    application_id: str
    result_code: str  # SUCCESS or rejection code
    mark_valid_at_completion: bool
    fragment_gain_requested: int  # fissato = 1 (B2B2Q05)
    fragment_gain_applied: int  # 0 or 1
    fragment_overflow_discarded: int  # 0 or 1
    resource_segment_id: Optional[str]
    assigned_event_sequence: int
    state_version_after: int
    processed_at: str  # ISO UTC


@dataclass(frozen=True)
class DrainCommand:
    """Structured Drain command (server-side, post-gating).

    Server-authoritative: identità caller + phase + expedition già validati
    upstream. Il puro state machine drain riceve questo record per applicare
    la transizione senza toccare I/O.
    """

    command_type: str  # START_DRAIN | COMPLETE_DRAIN | CANCEL_DRAIN
    event_id: str
    expedition_id: str
    source_adventurer_id: str
    target_id: str
    mark_id: str  # empty string for CANCEL_DRAIN cascade cases where drain lookup by id
    application_id: str
    drain_execution_id: str = ""  # empty at START_DRAIN (server-generated); required for COMPLETE/CANCEL
    cancellation_reason: str = ""  # required for CANCEL_DRAIN, one of DRAIN_CANCEL_REASONS
    payload_hash: str = ""
    expected_state_version: int = 0
    phase_id: Optional[str] = None


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

    RT2-B-2B-2-1 additions (default None · backward compat):
        drain_execution_id · drain_mark_id · drain_application_id ·
        drain_cancellation_reason
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
    # RT2-B-2B-2-1 Drain fields
    drain_execution_id: Optional[str] = None
    drain_mark_id: Optional[str] = None
    drain_application_id: Optional[str] = None
    drain_cancellation_reason: Optional[str] = None


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

    @property
    def success(self) -> bool:
        return self.code is TransitionResultCode.SUCCESS

    @property
    def is_dedup_noop(self) -> bool:
        return self.code is TransitionResultCode.DEDUPLICATED_NO_OP


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
    # RT2-B-2B-2-1 additions
    "DrainCommand",
    "DrainCompletionReceipt",
    "DRAIN_CANCEL_REASONS",
    "EVENT_ID_MAX_BYTES",
    "IDENTIFIER_MAX_BYTES",
    "validate_identifier_bounds",
]
