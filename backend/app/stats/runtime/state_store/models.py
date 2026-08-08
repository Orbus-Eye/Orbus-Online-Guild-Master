"""RT2-B-1A · State / Lease / Event Receipt schemas (immutable dataclasses).

Modelli dati per la runtime-state library. Frozen dataclasses per
determinismo, no runtime mutation su istanze (le mutation avvengono via
creazione di nuove istanze e CAS store-side).

Regole invarianti:
- `state_version` monotonic int · initial = 1 (verdict PM B0Q04).
- `fencing_token` monotonic int · incrementato ad ogni **nuova** acquisizione
  valida della lease (verdict PM B0Q02+B0Q08).
- `class_state_version` monotonic per adventurer (co-variabile con
  `state_version` ma indipendente da altri adventurers).
- `cross_expedition_class_state = false` (invariante):
  - `AdventurerClassState` è sempre "figlio" di uno `ExpeditionRuntimeState`.
- Valori finali item ESCLUSI (mandato §7 RT2-B-P0).
- Nessuna PII / secret / RNG seed / boss metadata dentro questi schemas.

Cap invariants (RT1 verbatim):
- active Marks ≤ 5 per source adventurer
- Mark per source-target ≤ 1
- Mark duration ≤ 10 seconds (application-time)
- Fragment count ≤ 5 · overflow discarded
- focus_bonus_usage per resource_segment ≤ 2
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Dict, List, Optional, Tuple

from app.stats.runtime.effects.models import EffectInstance


# ═══════════════════════ Enum · runtime_status ═══════════════════════
class RuntimeStatus(str, Enum):
    """Stato lifecycle del runtime-state document per una spedizione."""

    ACTIVE = "active"
    COMPLETING = "completing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


# ═══════════════════════ Mark ═══════════════════════
@dataclass(frozen=True)
class MarkDoc:
    """Marchio attivo su un target.

    Cap invariants applicati store-side via CAS pre-write pruning:
    - Un `source_adventurer_id` può avere al massimo 5 Marchi attivi (RT1).
    - Un `source-target` pair non può avere più di 1 Marchio (RT1).
    - `duration ≤ 10s` (`expires_at = created_at + 10s`).
    """

    mark_id: str
    application_id: str  # unique per application event
    source_adventurer_id: str
    target_id: str
    created_at: str  # ISO UTC
    expires_at: str  # ISO UTC = created_at + 10s
    ritual_close_used: bool = False
    mark_version: int = 1


# ═══════════════════════ Drain ═══════════════════════
class DrainStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass(frozen=True)
class DrainCompletionPayload:
    """RT2-B-2B-2-1 · Completion result payload (B2B2Q07 verbatim · 15 campi).

    PM adjudication (correzione ratificata): il payload è EMBEDDED nella
    **processed-event receipt** (`EventReceipt.result_payload`) — fonte
    autoritativa del completion result. Questo dataclass è lo SCHEMA canonico
    usato per costruire deterministicamente il dict pre-CAS.
    Una sola receipt ORDINARY consumata · mai un secondo slot · una sola
    mutation · un solo incremento di `state_version`.

    Esclusioni verbatim: damage · healing · XP · loot · item proc · combat
    result · RNG seed · reward payload.
    """

    drain_execution_id: str
    completion_event_id: str
    source_adventurer_id: str
    target_id: str
    mark_id: str
    application_id: str
    result_code: str  # SUCCESS | rejection code
    mark_valid_at_completion: bool
    fragment_gain_requested: int  # fissato = 1 (B2B2Q05)
    fragment_gain_applied: int  # 0 o 1 (post cap check)
    fragment_overflow_discarded: int  # 0 o 1
    resource_segment_id: Optional[str]
    assigned_event_sequence: int
    state_version_after: int
    processed_at: str  # ISO UTC


@dataclass(frozen=True)
class DrainDoc:
    """Drenaggio execution runtime state.

    Verbatim RT1:
    - own active Mark required at start · own active Mark required at completion
    - Drain does NOT consume Mark · one resolution per execution id

    RT2-B-2B-2-1 (PM Message 170 §9 binding contract) — campi aggiunti:
    - `mark_id`: binding al Mark letto a START_DRAIN (B2B2Q03 strict)
    - `cancelled_at` + `cancellation_reason` (uno degli 8 canonici B2B2Q08)
    - `drain_version`: monotonic per aggregato (initial=1)
    - `start_event_id`: event_id dello START accettato (dedup replay → prior ID)
    - `completion_event_id`: event_id della completion accettata (linkage 1:1
      con la processed-event receipt autoritativa · dedup/validazione)
    - `completion_payload`: DEPRECATED-NON-AUTHORITATIVE (PM adjudication
      B2B2Q07): la fonte autoritativa è `EventReceipt.result_payload`. Il
      nuovo runtime Drain NON lo popola (resta None · nessuna duplicazione).

    Hard-lock PM Message 170 §18:
    - max active Drain per (source,target) pair = 1
    - max active Drain per Mark application = 1
    """

    drain_execution_id: str
    source_adventurer_id: str
    target_id: str
    required_mark_application_id: str
    started_at: str  # ISO UTC
    completed_at: Optional[str] = None
    runtime_status: DrainStatus = DrainStatus.IN_PROGRESS
    resolution_version: int = 1
    reward_resolved: bool = False
    mark_id: str = ""
    cancelled_at: Optional[str] = None
    cancellation_reason: Optional[str] = None
    drain_version: int = 1
    start_event_id: str = ""
    completion_event_id: str = ""
    completion_payload: Optional[DrainCompletionPayload] = None


# ═══════════════════════ Fragment usage per segment ═══════════════════════
@dataclass(frozen=True)
class FragmentUsage:
    """Utilizzo del focus bonus per singolo resource_segment.

    Cap: `focus_bonus_used ≤ 2` per `resource_segment_id`.
    """

    resource_segment_id: str
    focus_bonus_used: int = 0


# ═══════════════════════ Adventurer class state ═══════════════════════
@dataclass(frozen=True)
class AdventurerClassState:
    """Stato della classe (Cacciatore del Vuoto) per singolo avventuriero.

    Chiave nel parent map: `adventurer_id`.
    NON persiste cross-expedition (invariante).
    """

    adventurer_id: str
    active_marks: Tuple[MarkDoc, ...] = ()
    active_drain_executions: Tuple[DrainDoc, ...] = ()
    fragment_count: int = 0  # cap ≤ 5
    resource_segment_id: Optional[str] = None
    focus_bonus_usage: Tuple[FragmentUsage, ...] = ()
    class_state_version: int = 1


# ═══════════════════════ Event Receipt ═══════════════════════
@dataclass(frozen=True)
class EventReceipt:
    """Receipt di deduplication per singolo event.

    Chiave dedup: `(expedition_id, event_id)`. Retention = lifetime del
    state document. Al limite di capacità: fail-closed (no eviction
    durante expedition attiva).

    Contenuto (B0Q06 verbatim minimum):

    RT2-B-2B-2-1 · PM adjudication B2B2Q07 (correzione ratificata):
    `result_payload` contiene il completion result payload a 15 campi per
    COMPLETE_DRAIN (e per i fold-commit di completion). La processed-event
    receipt è la FONTE AUTORITATIVA del completion result. Default None per
    tutti gli eventi legacy (byte-shape invariata). Costruito
    deterministicamente PRE-CAS · scritto nello stesso singolo CAS ·
    nessuna persistenza post-CAS · nessuna seconda receipt.
    """

    event_id: str
    event_type: str
    source_adventurer_id: str
    payload_hash: str
    assigned_event_sequence: int
    result_code: str  # canonical CasResultCode string
    state_version_after: int
    processed_at: str  # ISO UTC
    result_payload: Optional[Dict[str, object]] = None


# ═══════════════════════ Writer Lease ═══════════════════════
@dataclass(frozen=True)
class WriterLease:
    """Lease del writer per una spedizione (Model A).

    Regole:
    - `fencing_token` monotonic int, incrementato ad OGNI nuova acquisizione
      valida (non su renewal — renewal preserva il token).
    - `acquired_at + lease_duration_seconds = expires_at` (default 30s).
    - `renewal_interval_seconds = 10s`, `grace_period_seconds = 5s`.
    - Il clock applicativo NON è sufficiente da solo — l'acquisizione e il
      rinnovo passano SEMPRE attraverso una mutation atomica store-side.
    """

    lease_id: str
    owner_id: str
    acquired_at: str  # ISO UTC
    expires_at: str  # ISO UTC
    fencing_token: int
    renewed_at: Optional[str] = None
    lease_version: int = 1


# ═══════════════════════ Expedition Runtime State ═══════════════════════
@dataclass(frozen=True)
class ExpeditionRuntimeState:
    """Documento runtime-state per una singola spedizione.

    Chiave: `expedition_id` (unique in `expedition_runtime_states`).
    `state_version` monotonic int (initial = 1); incrementa +1 su ogni
    mutation accettata.

    Regole cross-cutting:
    - `adventurer_class_states` è keyed by `adventurer_id` (map).
    - `processed_event_keys` è bounded per spedizione: `MAX_PROCESSED_EVENTS`.
    - `last_event_sequence` è server-authoritative: assegnato dalla mutation
      accettata (B0Q05 verbatim).
    - `runtime_status` sticky (once terminal, no further mutations).
    - Valori finali item ESCLUSI (mandato).
    """

    expedition_id: str
    state_version: int  # monotonic; initial=1
    created_at: str  # ISO UTC
    updated_at: str  # ISO UTC
    expires_at: str  # ISO UTC (TTL candidate)
    runtime_status: RuntimeStatus = RuntimeStatus.ACTIVE
    owner_worker_or_lease_id: Optional[str] = None
    lease: Optional[WriterLease] = None  # None if no writer currently
    loadout_snapshot_version: int = 0  # reserved for future RT2-A wiring
    adventurer_class_states: Tuple[Tuple[str, AdventurerClassState], ...] = ()
    active_effect_instances: Tuple[EffectInstance, ...] = ()
    processed_event_keys: Tuple[EventReceipt, ...] = ()
    last_event_sequence: int = 0
    fencing_token: int = 0  # writer's current fencing_token (0 if no writer)

    # ── Bounded processed_event_keys ring (B0Q06 · RT2-B-2B-1 PM verdict B2BQ14) ──
    # RT2-B-2B-1 · PM Message 151 §9 verbatim: total receipt capacity = 512
    # (504 ordinary + 8 reserved lifecycle/system). Application-level enforcement
    # in transitions/state_machine.py distingue ordinary vs reserved. Il valore
    # qui è il HARD CAP tecnico del ring bounded del store.
    MAX_PROCESSED_EVENTS: int = 512

    def class_state_for(self, adventurer_id: str) -> Optional[AdventurerClassState]:
        """Read helper: ritorna lo stato classe per un avventuriero, o None."""
        for key, cs in self.adventurer_class_states:
            if key == adventurer_id:
                return cs
        return None

    def receipt_for(self, event_id: str) -> Optional[EventReceipt]:
        """Read helper: ritorna la receipt per un event_id, o None."""
        for r in self.processed_event_keys:
            if r.event_id == event_id:
                return r
        return None

    def effect_instance_for(self, effect_instance_id: str) -> Optional[EffectInstance]:
        """Read helper for a top-level active generic-effect instance."""

        for instance in self.active_effect_instances:
            if instance.effect_instance_id == effect_instance_id:
                return instance
        return None
