"""RT2-B-1A · `ExpeditionRuntimeStateStore` interface (abstract base class).

Contratto astratto per lo state store distribuito.

Le 11 operazioni astratte sono documentate dal PM verdict RT2-B-P0 §10 e §16:
`create_state · get_state · compare_and_update · apply_event_once ·
reserve_writer · renew_writer_lease · release_writer · expire_state ·
delete_state · get_version · health_check`.

Regole invarianti valide per QUALSIASI implementazione:
- Mutation atomica per-expedition (single-document CAS).
- Filter minimo su mutation: `{_id: expedition_id, state_version: expected,
  fencing_token: expected}` — verdict PM B0Q04.
- Nessuna partial mutation su conflict.
- Idempotenza via `apply_event_once` con dedup key `(expedition_id, event_id)`.
- Server-authoritative event sequence (client non sceglie sequenza).
- Server-generated / server-owned `state_version` e `fencing_token`.
- Nessuna operazione qui persiste PII / secret / seed RNG / boss payload.
- Il return NON espone documenti Mongo raw: solo `ExpeditionRuntimeState`
  strutturato o `CasResult`.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from app.stats.runtime.state_store.models import (
    ExpeditionRuntimeState,
    WriterLease,
)
from app.stats.runtime.state_store.results import (
    CasResult,
    LeaseAcquireResult,
    ReadResult,
)


class ExpeditionRuntimeStateStore(ABC):
    """Interfaccia astratta per lo state store multi-worker.

    Non è cablata al runtime applicativo. Le implementazioni concrete sono:
    - `FakeExpeditionRuntimeStateStore` (in-memory, test only).
    - `MongoExpeditionRuntimeStateStore` (Mongo adapter, injected collection,
      NON istanziato dal runtime).
    """

    # ═══════════════════════ 1. create_state ═══════════════════════
    @abstractmethod
    async def create_state(
        self,
        expedition_id: str,
        initial_state: ExpeditionRuntimeState,
    ) -> CasResult:
        """Crea il documento stato per una spedizione.

        Preconditions:
            - `expedition_id` unique (no pre-existing document).
            - `initial_state.state_version == 1` (initial value per B0Q04).
            - `initial_state.fencing_token == 0` (no writer at creation).
        Atomicity:
            INSERT_IF_NOT_EXISTS single-document.
        Idempotency:
            Duplicate create → `CasResultCode.ALREADY_EXISTS` (no-op).
        Conflict result:
            `ALREADY_EXISTS` if `expedition_id` already has a document.
        Timeout behavior:
            Store implementation raises `StoreInfraError`.
        Retry behavior:
            NOT retryable at this level (caller's decision).
        Audit event:
            `runtime_state_created` on SUCCESS.
        Failure code:
            `ALREADY_EXISTS` | `STATE_INFRA_UNAVAILABLE`.
        """

    # ═══════════════════════ 2. get_state ═══════════════════════
    @abstractmethod
    async def get_state(self, expedition_id: str) -> ReadResult:
        """Read completo dello stato.

        Preconditions: none (read-only).
        Atomicity: SINGLE_READ.
        Idempotency: read-only (natural).
        Conflict result: `NOT_FOUND` if missing.
        Timeout behavior: `StoreInfraError`.
        Retry behavior: safe to retry.
        Audit event: `runtime_state_read` (sampled, at caller layer).
        Failure code: `NOT_FOUND` | `STATE_INFRA_UNAVAILABLE`.
        """

    # ═══════════════════════ 3. compare_and_update ═══════════════════════
    @abstractmethod
    async def compare_and_update(
        self,
        expedition_id: str,
        expected_state_version: int,
        expected_fencing_token: int,
        mutation: Dict[str, Any],
    ) -> CasResult:
        """CAS mutation con filtro min `{_id, state_version, fencing_token}`.

        Preconditions:
            - `expected_state_version` matches current.
            - `expected_fencing_token` matches current writer's token.
        Atomicity:
            ATOMIC_CAS single-document. On success: `state_version += 1`.
        Idempotency:
            NOT idempotent (mutation-scoped); caller should use
            `apply_event_once` for event-scoped idempotency.
        Conflict result:
            `STATE_VERSION_CONFLICT` (state_version mismatch) |
            `STALE_WRITER_REJECTED` (fencing_token mismatch) |
            `NOT_FOUND`.
        Timeout behavior: `StoreInfraError`.
        Retry behavior: max 3 automatic retries (caller-decided), only after
            fresh state re-read.
        Audit event: `runtime_state_updated` | `runtime_state_conflict`.
        Failure code: `STATE_VERSION_CONFLICT` | `STALE_WRITER_REJECTED` |
            `NOT_FOUND` | `STATE_INFRA_UNAVAILABLE`.
        """

    # ═══════════════════════ 4. apply_event_once ═══════════════════════
    @abstractmethod
    async def apply_event_once(
        self,
        expedition_id: str,
        event_id: str,
        event_type: str,
        source_adventurer_id: str,
        payload_hash: str,
        expected_state_version: int,
        expected_fencing_token: int,
        mutation: Dict[str, Any],
    ) -> CasResult:
        """Applica un event con dedup atomica.

        Preconditions:
            - `event_id` è la deduplication key composta con `expedition_id`.
            - `payload_hash` è stabile per identità dell'evento.
        Atomicity:
            ATOMIC (dedup check + CAS in single `find_one_and_update`).
        Idempotency:
            Same `event_id` + same `payload_hash` → `DEDUPLICATED_NO_OP`
            con `prior_result_reference = event_id`.
        Conflict result:
            `EVENT_ID_PAYLOAD_MISMATCH` (same event_id, diff payload_hash)
            | `STATE_VERSION_CONFLICT` | `STALE_WRITER_REJECTED` |
            `NOT_FOUND`.
        Sequence assignment:
            On SUCCESS, `assigned_event_sequence = last_event_sequence + 1`
            (server-authoritative, B0Q05).
        Timeout behavior: `StoreInfraError`.
        Retry behavior: retry with same `event_id` → deduplicated no-op.
        Audit event: `runtime_state_updated` (SUCCESS) |
            `duplicate_event_suppressed` (DEDUPLICATED_NO_OP) |
            `runtime_state_conflict` | `event_sequence_rejected` (if used).
        Failure code: standard set.
        """

    # ═══════════════════════ 5. reserve_writer ═══════════════════════
    @abstractmethod
    async def reserve_writer(
        self,
        expedition_id: str,
        writer_worker_id: str,
        lease_ttl_seconds: int = 30,
    ) -> LeaseAcquireResult:
        """Acquisisce la lease del writer autoritativo (Model A).

        Preconditions:
            - `writer_worker_id` non vuoto.
            - `lease_ttl_seconds > 0`.
        Atomicity:
            CAS su `{lease is None} OR {lease.expires_at < now}`.
            Increments `fencing_token`. Sets new `lease`.
        Idempotency:
            Same `writer_worker_id` re-acquire (dopo scadenza) → success with
            NEW fencing_token.
        Conflict result:
            `STATE_VERSION_CONFLICT` (concurrent lease acquisition attempts)
            → caller retries with fresh state.
            `NOT_FOUND` if state doesn't exist.
        Timeout behavior: `StoreInfraError`.
        Audit event: `writer_lease_acquired` | `writer_lease_rejected`.
        """

    # ═══════════════════════ 6. renew_writer_lease ═══════════════════════
    @abstractmethod
    async def renew_writer_lease(
        self,
        expedition_id: str,
        lease_id: str,
        fencing_token: int,
        extend_seconds: int = 30,
    ) -> LeaseAcquireResult:
        """Rinnova la lease esistente (stesso fencing_token).

        Preconditions:
            - `lease_id + fencing_token` match state.
            - `lease.expires_at > now` OR entro `grace_period_seconds`.
        Atomicity:
            CAS con filtro `{lease.lease_id, fencing_token}`.
        Idempotency:
            Idempotent entro la lease window.
        Conflict result:
            `STALE_WRITER_REJECTED` (fencing mismatch) |
            `LEASE_EXPIRED` (past grace period) |
            `NOT_FOUND`.
        Audit event: `writer_lease_renewed` | `writer_lease_rejected` |
            `writer_lease_expired`.
        """

    # ═══════════════════════ 7. release_writer ═══════════════════════
    @abstractmethod
    async def release_writer(
        self,
        expedition_id: str,
        lease_id: str,
        fencing_token: int,
    ) -> CasResult:
        """Rilascia la lease (cooperative).

        Preconditions: `lease_id + fencing_token` match.
        Atomicity: CAS clear `lease` field.
        Idempotency: duplicate release → `DEDUPLICATED_NO_OP`.
        Conflict result: `STALE_WRITER_REJECTED` (fencing mismatch, silent).
        Audit event: `writer_lease_released`.
        """

    # ═══════════════════════ 8. expire_state ═══════════════════════
    @abstractmethod
    async def expire_state(self, expedition_id: str) -> CasResult:
        """Marca lo stato come `expired` (terminal).

        Preconditions: none.
        Atomicity: CAS su `runtime_status ∉ terminal`.
        Idempotency: duplicate expire → `DEDUPLICATED_NO_OP`.
        Audit event: `runtime_state_expired`.
        """

    # ═══════════════════════ 9. delete_state ═══════════════════════
    @abstractmethod
    async def delete_state(self, expedition_id: str) -> CasResult:
        """Cancella hard il documento (recovery / manual op).

        Atomicity: SINGLE_DELETE.
        Idempotency: duplicate delete → `NOT_FOUND` (silent no-op).
        Audit event: `runtime_state_deleted`.
        """

    # ═══════════════════════ 10. get_version ═══════════════════════
    @abstractmethod
    async def get_version(self, expedition_id: str) -> ReadResult:
        """Read proiettivo solo di `state_version` (bandwidth-optimized).

        Atomicity: SINGLE_READ_PROJECTION.
        Idempotency: read-only.
        """

    # ═══════════════════════ 11. health_check ═══════════════════════
    @abstractmethod
    async def health_check(self) -> bool:
        """Ping dello store per liveness/readiness (no side effect)."""
