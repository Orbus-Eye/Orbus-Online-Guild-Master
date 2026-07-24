"""RT2-B-2B-1 · Class-state transitions module (Mark · Fragment · Resource Segment).

Modulo autorizzato dal gate `R18.6.RV3-IS2-B-P2B-RT2-B-2B-1 · MARK & RESOURCE STATE
TRANSITION FOUNDATION` (PM Message 151 verbatim).

Boundary invariante (PM §11):
- Pure/deterministic state machines · nessuna conoscenza HTTP/frontend/env/Mongo
- Riceve ESPLICITAMENTE: current state, trusted event, authoritative time, policy config
- Nessuna istanziazione diretta di client Mongo
- Nessuna dipendenza circolare con `wiring/`

Scope autorizzato:
- Mark apply/refresh/lazy expiration/opportunistic cleanup/ownership+cap validation
- Fragment gain primitive (trusted-fixture only) + spend + reset + overflow discard
- Resource segment open/close
- Event ordering + event receipt generation (cap 512/504+8)
- Lease per event batch + fencing + CAS

Fuori scope (VIETATO):
- Drain runtime transitions (deferred RT2-B-2B-2)
- damage · healing · XP · loot · guild XP
- item effects · procs · cooldown engine
- public API · frontend · shared environment
"""
from app.stats.runtime.transitions.models import (
    ClassEventType,
    ClassStateEvent,
    ReasonCode,
    ReceiptCategory,
    TransitionResult,
    TransitionResultCode,
    TrustedDrainReceipt,
)
from app.stats.runtime.transitions.phase import (
    SINGLE_EXPEDITION_PHASE_VERSION,
    build_phase_id,
    is_transition_allowed_in_phase,
)
from app.stats.runtime.transitions.state_machine import (
    RECEIPT_CAP_ORDINARY,
    RECEIPT_CAP_RESERVED,
    RECEIPT_CAP_TOTAL,
    apply_mark,
    close_resource_segment,
    discard_fragment_overflow,
    gain_fragment,
    lazy_expire_marks,
    opportunistic_cleanup,
    refresh_mark,
    reset_fragments,
    spend_fragment,
)
from app.stats.runtime.transitions.dispatcher import (
    RETRY_MAX,
    ClassTransitionDispatcher,
    DispatchOutcome,
)

__all__ = [
    # models
    "ClassEventType",
    "ClassStateEvent",
    "ReasonCode",
    "ReceiptCategory",
    "TransitionResult",
    "TransitionResultCode",
    "TrustedDrainReceipt",
    # phase
    "SINGLE_EXPEDITION_PHASE_VERSION",
    "build_phase_id",
    "is_transition_allowed_in_phase",
    # state_machine
    "RECEIPT_CAP_ORDINARY",
    "RECEIPT_CAP_RESERVED",
    "RECEIPT_CAP_TOTAL",
    "apply_mark",
    "close_resource_segment",
    "discard_fragment_overflow",
    "gain_fragment",
    "lazy_expire_marks",
    "opportunistic_cleanup",
    "refresh_mark",
    "reset_fragments",
    "spend_fragment",
    # dispatcher
    "RETRY_MAX",
    "ClassTransitionDispatcher",
    "DispatchOutcome",
]
