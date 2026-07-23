"""RT2-B-1A · Fake in-memory state store implementation (TEST-ONLY).

**`PRODUCTION_USE = FORBIDDEN`** — questa implementazione è destinata SOLO
a fixture/unit/contract test. Non usare in ambiente runtime, non wire, non
importare da servizi applicativi.

Semantica:
- Storage: `dict[expedition_id, ExpeditionRuntimeState]` (process-local).
- Concurrency: `asyncio.Lock` per operazione (atomicità dei metodi async
  entro un event loop). NON safe per multi-process (by design: fake).
- Rispetta contract identico a `MongoExpeditionRuntimeStateStore`:
  CAS su `{state_version, fencing_token}`, dedup via `apply_event_once`,
  lease + fencing_token monotonic.
- Time source: `datetime.now(timezone.utc)`; iniettabile via `clock` param
  del costruttore per test deterministici.

Motivazione del marker `PRODUCTION_USE = FORBIDDEN`: nessun writer stale
può essere davvero simulato con storage process-local (§3 dispatch RT2-B-P0
+ §7 direttiva RT2-B-1A). Il fake serve a verificare che i contract siano
rispettati identicamente da qualsiasi implementazione.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Optional

from app.stats.runtime.state_store.errors import StoreInfraError
from app.stats.runtime.state_store.fencing import (
    next_fencing_token,
    next_state_version,
    validate_fencing_match,
    validate_state_version_match,
)
from app.stats.runtime.state_store.interface import ExpeditionRuntimeStateStore
from app.stats.runtime.state_store.models import (
    EventReceipt,
    ExpeditionRuntimeState,
    RuntimeStatus,
    WriterLease,
)
from app.stats.runtime.state_store.results import (
    CasResult,
    CasResultCode,
    LeaseAcquireResult,
    ReadResult,
)


# ═══════════════════════ MARKER · production ban ═══════════════════════
PRODUCTION_USE: str = "FORBIDDEN"
"""Do NOT instantiate this store in application runtime. Tests / fixtures only."""


def _iso_now(clock: Callable[[], datetime]) -> str:
    return clock().isoformat().replace("+00:00", "Z")


def _iso_add(clock: Callable[[], datetime], seconds: int) -> str:
    return (clock() + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


class FakeExpeditionRuntimeStateStore(ExpeditionRuntimeStateStore):
    """In-memory fake · TEST-ONLY."""

    def __init__(
        self,
        *,
        clock: Optional[Callable[[], datetime]] = None,
        health_ok: bool = True,
    ) -> None:
        # Sanity: fake explicit intent — no accidental production wiring.
        assert PRODUCTION_USE == "FORBIDDEN", "FakeExpeditionRuntimeStateStore is TEST-ONLY"
        self._storage: Dict[str, ExpeditionRuntimeState] = {}
        self._lock = asyncio.Lock()
        self._clock: Callable[[], datetime] = clock or _default_clock
        self._health_ok: bool = health_ok

    # ═══════════════════════ 1. create_state ═══════════════════════
    async def create_state(
        self,
        expedition_id: str,
        initial_state: ExpeditionRuntimeState,
    ) -> CasResult:
        async with self._lock:
            if expedition_id in self._storage:
                return CasResult(
                    code=CasResultCode.ALREADY_EXISTS,
                    reason=f"state already exists for {expedition_id}",
                )
            if initial_state.state_version != 1:
                return CasResult(
                    code=CasResultCode.STATE_VERSION_CONFLICT,
                    reason="initial state_version must be 1 (B0Q04)",
                )
            if initial_state.fencing_token != 0:
                return CasResult(
                    code=CasResultCode.STALE_WRITER_REJECTED,
                    reason="initial fencing_token must be 0",
                )
            self._storage[expedition_id] = initial_state
            return CasResult(
                code=CasResultCode.SUCCESS,
                new_state_version=initial_state.state_version,
            )

    # ═══════════════════════ 2. get_state ═══════════════════════
    async def get_state(self, expedition_id: str) -> ReadResult:
        async with self._lock:
            st = self._storage.get(expedition_id)
            if st is None:
                return ReadResult(code=CasResultCode.NOT_FOUND)
            return ReadResult(code=CasResultCode.SUCCESS, state=st)

    # ═══════════════════════ 3. compare_and_update ═══════════════════════
    async def compare_and_update(
        self,
        expedition_id: str,
        expected_state_version: int,
        expected_fencing_token: int,
        mutation: Dict[str, Any],
    ) -> CasResult:
        async with self._lock:
            st = self._storage.get(expedition_id)
            if st is None:
                return CasResult(code=CasResultCode.NOT_FOUND)
            if not validate_state_version_match(expected_state_version, st.state_version):
                return CasResult(
                    code=CasResultCode.STATE_VERSION_CONFLICT,
                    new_state_version=st.state_version,
                )
            if not validate_fencing_match(expected_fencing_token, st.fencing_token):
                return CasResult(
                    code=CasResultCode.STALE_WRITER_REJECTED,
                    new_state_version=st.state_version,
                )
            # Apply mutation atomically. Only whitelisted fields allowed to
            # keep the fake deterministic. Unknown fields → ignored.
            new_fields: Dict[str, Any] = {}
            for k, v in mutation.items():
                if k in (
                    "adventurer_class_states", "runtime_status",
                    "loadout_snapshot_version", "expires_at",
                    "last_event_sequence",
                ):
                    new_fields[k] = v
            new_fields["state_version"] = next_state_version(st.state_version)
            new_fields["updated_at"] = _iso_now(self._clock)
            new_st = ExpeditionRuntimeState(
                expedition_id=st.expedition_id,
                state_version=new_fields.get("state_version", st.state_version),
                created_at=st.created_at,
                updated_at=new_fields.get("updated_at", st.updated_at),
                expires_at=new_fields.get("expires_at", st.expires_at),
                runtime_status=new_fields.get("runtime_status", st.runtime_status),
                owner_worker_or_lease_id=st.owner_worker_or_lease_id,
                lease=st.lease,
                loadout_snapshot_version=new_fields.get("loadout_snapshot_version", st.loadout_snapshot_version),
                adventurer_class_states=new_fields.get("adventurer_class_states", st.adventurer_class_states),
                processed_event_keys=st.processed_event_keys,
                last_event_sequence=new_fields.get("last_event_sequence", st.last_event_sequence),
                fencing_token=st.fencing_token,
            )
            self._storage[expedition_id] = new_st
            return CasResult(
                code=CasResultCode.SUCCESS,
                new_state_version=new_st.state_version,
            )

    # ═══════════════════════ 4. apply_event_once ═══════════════════════
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
        async with self._lock:
            st = self._storage.get(expedition_id)
            if st is None:
                return CasResult(code=CasResultCode.NOT_FOUND)
            # 1) dedup check (before CAS): same event_id?
            prior = st.receipt_for(event_id)
            if prior is not None:
                if prior.payload_hash != payload_hash:
                    return CasResult(
                        code=CasResultCode.EVENT_ID_PAYLOAD_MISMATCH,
                        prior_result_reference=event_id,
                    )
                # Idempotent no-op
                return CasResult(
                    code=CasResultCode.DEDUPLICATED_NO_OP,
                    new_state_version=st.state_version,
                    assigned_event_sequence=prior.assigned_event_sequence,
                    prior_result_reference=event_id,
                )
            # 2) CAS filters
            if not validate_state_version_match(expected_state_version, st.state_version):
                return CasResult(
                    code=CasResultCode.STATE_VERSION_CONFLICT,
                    new_state_version=st.state_version,
                )
            if not validate_fencing_match(expected_fencing_token, st.fencing_token):
                return CasResult(
                    code=CasResultCode.STALE_WRITER_REJECTED,
                    new_state_version=st.state_version,
                )
            # 3) bounded receipts ring (fail-closed at limit)
            if len(st.processed_event_keys) >= ExpeditionRuntimeState.MAX_PROCESSED_EVENTS:
                return CasResult(
                    code=CasResultCode.CAP_EXCEEDED,
                    reason=f"processed_event_keys ring at limit ({ExpeditionRuntimeState.MAX_PROCESSED_EVENTS}) · fail-closed",
                )
            # 4) apply
            new_sequence = st.last_event_sequence + 1
            new_version = next_state_version(st.state_version)
            new_receipt = EventReceipt(
                event_id=event_id,
                event_type=event_type,
                source_adventurer_id=source_adventurer_id,
                payload_hash=payload_hash,
                assigned_event_sequence=new_sequence,
                result_code=CasResultCode.SUCCESS.value,
                state_version_after=new_version,
                processed_at=_iso_now(self._clock),
            )
            # Merge mutation (whitelist)
            fields: Dict[str, Any] = {}
            for k, v in mutation.items():
                if k in (
                    "adventurer_class_states", "runtime_status",
                    "loadout_snapshot_version", "expires_at",
                ):
                    fields[k] = v
            new_st = ExpeditionRuntimeState(
                expedition_id=st.expedition_id,
                state_version=new_version,
                created_at=st.created_at,
                updated_at=_iso_now(self._clock),
                expires_at=fields.get("expires_at", st.expires_at),
                runtime_status=fields.get("runtime_status", st.runtime_status),
                owner_worker_or_lease_id=st.owner_worker_or_lease_id,
                lease=st.lease,
                loadout_snapshot_version=fields.get("loadout_snapshot_version", st.loadout_snapshot_version),
                adventurer_class_states=fields.get("adventurer_class_states", st.adventurer_class_states),
                processed_event_keys=st.processed_event_keys + (new_receipt,),
                last_event_sequence=new_sequence,
                fencing_token=st.fencing_token,
            )
            self._storage[expedition_id] = new_st
            return CasResult(
                code=CasResultCode.SUCCESS,
                new_state_version=new_version,
                assigned_event_sequence=new_sequence,
            )

    # ═══════════════════════ 5. reserve_writer ═══════════════════════
    async def reserve_writer(
        self,
        expedition_id: str,
        writer_worker_id: str,
        lease_ttl_seconds: int = 30,
    ) -> LeaseAcquireResult:
        async with self._lock:
            if not writer_worker_id:
                return LeaseAcquireResult(
                    code=CasResultCode.OWNERSHIP_INVALID,
                    reason="writer_worker_id required",
                )
            if lease_ttl_seconds <= 0:
                return LeaseAcquireResult(
                    code=CasResultCode.OWNERSHIP_INVALID,
                    reason="lease_ttl_seconds must be > 0",
                )
            st = self._storage.get(expedition_id)
            if st is None:
                return LeaseAcquireResult(code=CasResultCode.NOT_FOUND)
            now = self._clock()
            # If lease present and NOT expired → reject
            if st.lease is not None:
                exp_at = datetime.fromisoformat(st.lease.expires_at.replace("Z", "+00:00"))
                if exp_at > now:
                    return LeaseAcquireResult(
                        code=CasResultCode.STATE_VERSION_CONFLICT,
                        reason="lease held by other and not expired",
                    )
            new_token = next_fencing_token(st.fencing_token)
            lease_id = f"lease-{expedition_id}-{new_token}"
            new_lease = WriterLease(
                lease_id=lease_id,
                owner_id=writer_worker_id,
                acquired_at=_iso_now(self._clock),
                expires_at=_iso_add(self._clock, lease_ttl_seconds),
                fencing_token=new_token,
            )
            new_st = ExpeditionRuntimeState(
                expedition_id=st.expedition_id,
                state_version=st.state_version,
                created_at=st.created_at,
                updated_at=_iso_now(self._clock),
                expires_at=st.expires_at,
                runtime_status=st.runtime_status,
                owner_worker_or_lease_id=writer_worker_id,
                lease=new_lease,
                loadout_snapshot_version=st.loadout_snapshot_version,
                adventurer_class_states=st.adventurer_class_states,
                processed_event_keys=st.processed_event_keys,
                last_event_sequence=st.last_event_sequence,
                fencing_token=new_token,
            )
            self._storage[expedition_id] = new_st
            return LeaseAcquireResult(
                code=CasResultCode.SUCCESS,
                lease_id=lease_id,
                fencing_token=new_token,
                lease_expires_at=new_lease.expires_at,
            )

    # ═══════════════════════ 6. renew_writer_lease ═══════════════════════
    async def renew_writer_lease(
        self,
        expedition_id: str,
        lease_id: str,
        fencing_token: int,
        extend_seconds: int = 30,
    ) -> LeaseAcquireResult:
        async with self._lock:
            st = self._storage.get(expedition_id)
            if st is None:
                return LeaseAcquireResult(code=CasResultCode.NOT_FOUND)
            if st.lease is None:
                return LeaseAcquireResult(code=CasResultCode.LEASE_EXPIRED)
            if st.lease.lease_id != lease_id:
                return LeaseAcquireResult(code=CasResultCode.STALE_WRITER_REJECTED)
            if not validate_fencing_match(fencing_token, st.fencing_token):
                return LeaseAcquireResult(code=CasResultCode.STALE_WRITER_REJECTED)
            now = self._clock()
            exp_at = datetime.fromisoformat(st.lease.expires_at.replace("Z", "+00:00"))
            # Grace period: allow renewal within 5s past expires_at
            if exp_at + timedelta(seconds=5) < now:
                return LeaseAcquireResult(code=CasResultCode.LEASE_EXPIRED)
            new_lease = WriterLease(
                lease_id=st.lease.lease_id,
                owner_id=st.lease.owner_id,
                acquired_at=st.lease.acquired_at,
                expires_at=_iso_add(self._clock, extend_seconds),
                renewed_at=_iso_now(self._clock),
                lease_version=st.lease.lease_version + 1,
                fencing_token=st.lease.fencing_token,
            )
            self._storage[expedition_id] = ExpeditionRuntimeState(
                expedition_id=st.expedition_id,
                state_version=st.state_version,
                created_at=st.created_at,
                updated_at=_iso_now(self._clock),
                expires_at=st.expires_at,
                runtime_status=st.runtime_status,
                owner_worker_or_lease_id=st.owner_worker_or_lease_id,
                lease=new_lease,
                loadout_snapshot_version=st.loadout_snapshot_version,
                adventurer_class_states=st.adventurer_class_states,
                processed_event_keys=st.processed_event_keys,
                last_event_sequence=st.last_event_sequence,
                fencing_token=st.fencing_token,
            )
            return LeaseAcquireResult(
                code=CasResultCode.SUCCESS,
                lease_id=new_lease.lease_id,
                fencing_token=new_lease.fencing_token,
                lease_expires_at=new_lease.expires_at,
            )

    # ═══════════════════════ 7. release_writer ═══════════════════════
    async def release_writer(
        self,
        expedition_id: str,
        lease_id: str,
        fencing_token: int,
    ) -> CasResult:
        async with self._lock:
            st = self._storage.get(expedition_id)
            if st is None:
                return CasResult(code=CasResultCode.NOT_FOUND)
            if st.lease is None:
                return CasResult(code=CasResultCode.DEDUPLICATED_NO_OP)
            if st.lease.lease_id != lease_id:
                return CasResult(code=CasResultCode.STALE_WRITER_REJECTED)
            if not validate_fencing_match(fencing_token, st.fencing_token):
                return CasResult(code=CasResultCode.STALE_WRITER_REJECTED)
            self._storage[expedition_id] = ExpeditionRuntimeState(
                expedition_id=st.expedition_id,
                state_version=st.state_version,
                created_at=st.created_at,
                updated_at=_iso_now(self._clock),
                expires_at=st.expires_at,
                runtime_status=st.runtime_status,
                owner_worker_or_lease_id=None,
                lease=None,
                loadout_snapshot_version=st.loadout_snapshot_version,
                adventurer_class_states=st.adventurer_class_states,
                processed_event_keys=st.processed_event_keys,
                last_event_sequence=st.last_event_sequence,
                fencing_token=st.fencing_token,
            )
            return CasResult(code=CasResultCode.SUCCESS)

    # ═══════════════════════ 8. expire_state ═══════════════════════
    async def expire_state(self, expedition_id: str) -> CasResult:
        async with self._lock:
            st = self._storage.get(expedition_id)
            if st is None:
                return CasResult(code=CasResultCode.NOT_FOUND)
            if st.runtime_status in (RuntimeStatus.EXPIRED, RuntimeStatus.COMPLETED, RuntimeStatus.CANCELLED):
                return CasResult(code=CasResultCode.DEDUPLICATED_NO_OP)
            self._storage[expedition_id] = ExpeditionRuntimeState(
                expedition_id=st.expedition_id,
                state_version=next_state_version(st.state_version),
                created_at=st.created_at,
                updated_at=_iso_now(self._clock),
                expires_at=st.expires_at,
                runtime_status=RuntimeStatus.EXPIRED,
                owner_worker_or_lease_id=st.owner_worker_or_lease_id,
                lease=st.lease,
                loadout_snapshot_version=st.loadout_snapshot_version,
                adventurer_class_states=st.adventurer_class_states,
                processed_event_keys=st.processed_event_keys,
                last_event_sequence=st.last_event_sequence,
                fencing_token=st.fencing_token,
            )
            return CasResult(
                code=CasResultCode.SUCCESS,
                new_state_version=self._storage[expedition_id].state_version,
            )

    # ═══════════════════════ 9. delete_state ═══════════════════════
    async def delete_state(self, expedition_id: str) -> CasResult:
        async with self._lock:
            if expedition_id not in self._storage:
                return CasResult(code=CasResultCode.NOT_FOUND)
            del self._storage[expedition_id]
            return CasResult(code=CasResultCode.SUCCESS)

    # ═══════════════════════ 10. get_version ═══════════════════════
    async def get_version(self, expedition_id: str) -> ReadResult:
        async with self._lock:
            st = self._storage.get(expedition_id)
            if st is None:
                return ReadResult(code=CasResultCode.NOT_FOUND)
            return ReadResult(code=CasResultCode.SUCCESS, version_only=st.state_version)

    # ═══════════════════════ 11. health_check ═══════════════════════
    async def health_check(self) -> bool:
        return bool(self._health_ok)
