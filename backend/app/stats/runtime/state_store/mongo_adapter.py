"""RT2-B-1A · Mongo adapter (dependency-injected collection · NON-WIRED).

**INVARIANT**: la collection è iniettata al costruttore. NON importiamo il
db globale dell'applicazione. Non c'è alcun percorso che istanzi questo
adapter dal runtime applicativo (verifica: `grep MongoExpeditionRuntimeStateStore`
sul codebase attuale ritorna 0 occorrenze fuori da questo modulo, dai test
e dagli __init__ RT2-B-1A).

Il Mongo adapter mappa le operazioni logiche su `find_one_and_update` con
filtri CAS canonici `{_id, state_version, fencing_token}`. Le eccezioni
Mongo (`PyMongoError`) sono catturate e mappate su `StoreInfraError`
(che il caller può a sua volta gestire).

Ogni mutation:
- Filter esatto include SEMPRE almeno `_id`, `state_version`, e (dove
  writer-scoped) `fencing_token`.
- Update usa `$inc {state_version: 1}` + `$set {updated_at: <iso>, ...}`.
- `return_document=ReturnDocument.AFTER` per ottenere state_version aggiornato.

L'adapter è **async** — usa `motor.motor_asyncio.AsyncIOMotorCollection`
via duck-typing (non-imported). Compatibile con collection injectate
di tipo mock (`AsyncMock`) per unit test.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Optional, Tuple

from app.stats.runtime.state_store.errors import StoreInfraError
from app.stats.runtime.state_store.fencing import (
    next_fencing_token,
    validate_fencing_match,
    validate_state_version_match,
)
from app.stats.runtime.state_store.interface import ExpeditionRuntimeStateStore
from app.stats.runtime.state_store.models import (
    AdventurerClassState,
    EventReceipt,
    ExpeditionRuntimeState,
    FragmentUsage as _FragmentUsage,
    MarkDoc as _MarkDoc,
    RuntimeStatus,
    WriterLease,
)
from app.stats.runtime.state_store.results import (
    CasResult,
    CasResultCode,
    LeaseAcquireResult,
    ReadResult,
)


def _iso_now(clock: Callable[[], datetime]) -> str:
    return clock().isoformat().replace("+00:00", "Z")


def _iso_add(clock: Callable[[], datetime], seconds: int) -> str:
    return (clock() + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")



# RT2-B-2B-2-1-V1S · PM: alias BSON brevi (rappresentazione interna non
# pubblica). I 15 nomi canonici restano al layer applicativo: la rehydration
# rimappa alias -> canonici. Nessun campo rimosso · nessun blob opaco.
_RP_ALIASES = {
    "drain_execution_id": "d", "completion_event_id": "c",
    "source_adventurer_id": "s", "target_id": "t", "mark_id": "m",
    "application_id": "a", "result_code": "r",
    "mark_valid_at_completion": "v", "fragment_gain_requested": "q",
    "fragment_gain_applied": "g", "fragment_overflow_discarded": "o",
    "resource_segment_id": "seg", "assigned_event_sequence": "e",
    "state_version_after": "w", "processed_at": "p",
    "cancelled_count": "cc", "sample_execution_ids": "si",
    "execution_ids_truncated": "tr", "reason": "rs",
}
_RP_ALIASES_REV = {v: k for k, v in _RP_ALIASES.items()}


# Campi payload duplicati 1:1 dai campi base della STESSA receipt: omessi
# nella rappresentazione persistita e ricostruiti DETERMINISTICAMENTE in
# rehydration (copia esatta dallo stesso documento). I 15 campi canonici
# restano integralmente presenti al layer applicativo.
_RP_DERIVED_FROM_RECEIPT = {
    "completion_event_id": "event_id",
    "source_adventurer_id": "source_adventurer_id",
    "assigned_event_sequence": "assigned_event_sequence",
    "state_version_after": "state_version_after",
    "processed_at": "processed_at",
}


def _rp_compact(payload):
    if not isinstance(payload, dict):
        return payload
    return {
        _RP_ALIASES.get(k, k): v for k, v in payload.items()
        if k not in _RP_DERIVED_FROM_RECEIPT
    }


def _rp_expand(payload, receipt=None):
    if not isinstance(payload, dict):
        return payload
    out = {_RP_ALIASES_REV.get(k, k): v for k, v in payload.items()}
    if receipt is not None:
        for canon, base in _RP_DERIVED_FROM_RECEIPT.items():
            if canon not in out:
                out[canon] = receipt.get(base)
    return out


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


def _serialize_class_states(items: Tuple[Tuple[str, AdventurerClassState], ...]) -> Dict[str, Any]:
    """Serialize adventurer_class_states tuple to Mongo-friendly dict-of-dicts.

    NON usato dalla mutation di questo gate (il caller passa il dict già
    pronto in `mutation`); esposta come helper per i test.
    """
    return {aid: _dc_to_dict(cs) for aid, cs in items}


def _dc_to_dict(obj: Any) -> Any:
    """Dataclass → dict serializer minimale, ricorsivo."""
    try:
        from dataclasses import asdict, is_dataclass
    except Exception:  # pragma: no cover
        return obj
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, tuple):
        return [_dc_to_dict(x) for x in obj]
    return obj


def _document_to_state(doc: Dict[str, Any]) -> ExpeditionRuntimeState:
    """Reconstruct `ExpeditionRuntimeState` from Mongo doc (best-effort).

    In RT2-B-1A this function is exercised only in tests (Mongo adapter
    is not runtime-instantiated). Fields not present default appropriately.
    """
    lease_dict = doc.get("lease")
    lease: Optional[WriterLease] = None
    if isinstance(lease_dict, dict):
        lease = WriterLease(
            lease_id=lease_dict.get("lease_id", ""),
            owner_id=lease_dict.get("owner_id", ""),
            acquired_at=lease_dict.get("acquired_at", ""),
            expires_at=lease_dict.get("expires_at", ""),
            fencing_token=int(lease_dict.get("fencing_token", 0)),
            renewed_at=lease_dict.get("renewed_at"),
            lease_version=int(lease_dict.get("lease_version", 1)),
        )
    # processed_event_keys → tuple of EventReceipt
    receipts_raw = doc.get("processed_event_keys", []) or []
    receipts = tuple(
        EventReceipt(
            event_id=r.get("event_id", ""),
            event_type=r.get("event_type", ""),
            source_adventurer_id=r.get("source_adventurer_id", ""),
            payload_hash=r.get("payload_hash", ""),
            assigned_event_sequence=int(r.get("assigned_event_sequence", 0)),
            result_code=r.get("result_code", ""),
            state_version_after=int(r.get("state_version_after", 0)),
            processed_at=r.get("processed_at", ""),
            result_payload=_rp_expand(r.get("result_payload"), r),
        )
        for r in receipts_raw
    )
    # RT2-B-2B-1-V1 · PM Message 153 §10: rehydrate adventurer_class_states
    # dal dict-of-dicts Mongo. Necessario perché il dispatcher legge lo stato
    # tra un event batch e il successivo (accumulated marks/fragments).
    acs_raw = doc.get("adventurer_class_states", {}) or {}
    adventurer_class_states: tuple = ()
    if isinstance(acs_raw, dict):
        entries = []
        for aid, cs_dict in acs_raw.items():
            if not isinstance(cs_dict, dict):
                continue
            marks_raw = cs_dict.get("active_marks", []) or []
            active_marks = tuple(
                _MarkDoc(
                    mark_id=m.get("mark_id", ""),
                    application_id=m.get("application_id", ""),
                    source_adventurer_id=m.get("source_adventurer_id", ""),
                    target_id=m.get("target_id", ""),
                    created_at=m.get("created_at", ""),
                    expires_at=m.get("expires_at", ""),
                    ritual_close_used=bool(m.get("ritual_close_used", False)),
                    mark_version=int(m.get("mark_version", 1)),
                )
                for m in marks_raw
                if isinstance(m, dict)
            )
            focus_raw = cs_dict.get("focus_bonus_usage", []) or []
            focus_usage = tuple(
                _FragmentUsage(
                    resource_segment_id=u.get("resource_segment_id", ""),
                    focus_bonus_used=int(u.get("focus_bonus_used", 0)),
                )
                for u in focus_raw
                if isinstance(u, dict)
            )
            drains_raw = cs_dict.get("active_drain_executions", []) or []
            entries.append((aid, AdventurerClassState(
                adventurer_id=cs_dict.get("adventurer_id", aid),
                active_marks=active_marks,
                active_drain_executions=tuple(drains_raw),
                fragment_count=int(cs_dict.get("fragment_count", 0)),
                resource_segment_id=cs_dict.get("resource_segment_id"),
                focus_bonus_usage=focus_usage,
                class_state_version=int(cs_dict.get("class_state_version", 0)),
            )))
        adventurer_class_states = tuple(entries)
    status_raw = doc.get("runtime_status", RuntimeStatus.ACTIVE.value)
    try:
        status = RuntimeStatus(status_raw)
    except ValueError:
        status = RuntimeStatus.ACTIVE
    return ExpeditionRuntimeState(
        expedition_id=doc.get("_id", doc.get("expedition_id", "")),
        state_version=int(doc.get("state_version", 1)),
        created_at=doc.get("created_at", ""),
        updated_at=doc.get("updated_at", ""),
        expires_at=doc.get("expires_at", ""),
        runtime_status=status,
        owner_worker_or_lease_id=doc.get("owner_worker_or_lease_id"),
        lease=lease,
        loadout_snapshot_version=int(doc.get("loadout_snapshot_version", 0)),
        adventurer_class_states=adventurer_class_states,
        processed_event_keys=receipts,
        last_event_sequence=int(doc.get("last_event_sequence", 0)),
        fencing_token=int(doc.get("fencing_token", 0)),
    )


class MongoExpeditionRuntimeStateStore(ExpeditionRuntimeStateStore):
    """Mongo-backed `ExpeditionRuntimeStateStore` con collection iniettata.

    Il costruttore ACCETTA solo collection già configurata (motor async
    collection o AsyncMock). NON crea/importa client, database, o env.
    """

    def __init__(
        self,
        collection: Any,
        *,
        clock: Optional[Callable[[], datetime]] = None,
    ) -> None:
        if collection is None:
            raise ValueError(
                "MongoExpeditionRuntimeStateStore requires an injected collection · "
                "runtime instantiation is forbidden in RT2-B-1A"
            )
        self._collection = collection
        self._clock: Callable[[], datetime] = clock or _default_clock

    # ═══════════════════════ 1. create_state ═══════════════════════
    async def create_state(
        self,
        expedition_id: str,
        initial_state: ExpeditionRuntimeState,
    ) -> CasResult:
        if initial_state.state_version != 1:
            return CasResult(
                code=CasResultCode.STATE_VERSION_CONFLICT,
                reason="initial state_version must be 1",
            )
        if initial_state.fencing_token != 0:
            return CasResult(
                code=CasResultCode.STALE_WRITER_REJECTED,
                reason="initial fencing_token must be 0",
            )
        doc = {
            "_id": expedition_id,
            "state_version": 1,
            "created_at": initial_state.created_at,
            "updated_at": initial_state.updated_at,
            "expires_at": initial_state.expires_at,
            "runtime_status": initial_state.runtime_status.value,
            "owner_worker_or_lease_id": None,
            "lease": None,
            "loadout_snapshot_version": initial_state.loadout_snapshot_version,
            "adventurer_class_states": {},
            "processed_event_keys": [],
            "last_event_sequence": 0,
            "fencing_token": 0,
        }
        try:
            await self._collection.insert_one(doc)
        except Exception as exc:  # DuplicateKeyError or other
            msg = str(exc).lower()
            if "duplicate" in msg or "e11000" in msg:
                return CasResult(code=CasResultCode.ALREADY_EXISTS)
            raise StoreInfraError(str(exc)) from exc
        return CasResult(code=CasResultCode.SUCCESS, new_state_version=1)

    # ═══════════════════════ 2. get_state ═══════════════════════
    async def get_state(self, expedition_id: str) -> ReadResult:
        try:
            doc = await self._collection.find_one({"_id": expedition_id})
        except Exception as exc:
            raise StoreInfraError(str(exc)) from exc
        if doc is None:
            return ReadResult(code=CasResultCode.NOT_FOUND)
        return ReadResult(code=CasResultCode.SUCCESS, state=_document_to_state(doc))

    # ═══════════════════════ 3. compare_and_update ═══════════════════════
    async def compare_and_update(
        self,
        expedition_id: str,
        expected_state_version: int,
        expected_fencing_token: int,
        mutation: Dict[str, Any],
    ) -> CasResult:
        # Filter min: _id + state_version + fencing_token (B0Q04)
        cas_filter = {
            "_id": expedition_id,
            "state_version": expected_state_version,
            "fencing_token": expected_fencing_token,
        }
        set_fields: Dict[str, Any] = {
            "updated_at": _iso_now(self._clock),
        }
        for k, v in mutation.items():
            if k in (
                "adventurer_class_states", "runtime_status",
                "loadout_snapshot_version", "expires_at",
                "last_event_sequence",
            ):
                # RT2-B-2B-1-V1 · serialize dataclass tuple → BSON-friendly dict
                if k == "adventurer_class_states" and isinstance(v, tuple):
                    set_fields[k] = _serialize_class_states(v)
                else:
                    set_fields[k] = v
        update = {
            "$inc": {"state_version": 1},
            "$set": set_fields,
        }
        try:
            doc = await self._collection.find_one_and_update(
                cas_filter,
                update,
                return_document=True,
            )
        except Exception as exc:
            raise StoreInfraError(str(exc)) from exc
        if doc is None:
            # CAS mismatch: distinguish version vs fencing via probe read
            try:
                probe = await self._collection.find_one(
                    {"_id": expedition_id},
                    {"state_version": 1, "fencing_token": 1},
                )
            except Exception as exc:
                raise StoreInfraError(str(exc)) from exc
            if probe is None:
                return CasResult(code=CasResultCode.NOT_FOUND)
            cur_sv = int(probe.get("state_version", 0))
            cur_ft = int(probe.get("fencing_token", 0))
            if not validate_fencing_match(expected_fencing_token, cur_ft):
                return CasResult(
                    code=CasResultCode.STALE_WRITER_REJECTED,
                    new_state_version=cur_sv,
                )
            return CasResult(
                code=CasResultCode.STATE_VERSION_CONFLICT,
                new_state_version=cur_sv,
            )
        new_version = int(doc.get("state_version", expected_state_version + 1))
        return CasResult(code=CasResultCode.SUCCESS, new_state_version=new_version)

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
        result_payload: Dict[str, Any] | None = None,
    ) -> CasResult:
        # 1) dedup probe (best-effort): read receipts and check event_id
        try:
            probe = await self._collection.find_one(
                {"_id": expedition_id},
                {
                    "state_version": 1, "fencing_token": 1,
                    "last_event_sequence": 1, "processed_event_keys": 1,
                },
            )
        except Exception as exc:
            raise StoreInfraError(str(exc)) from exc
        if probe is None:
            return CasResult(code=CasResultCode.NOT_FOUND)
        prior_receipts = probe.get("processed_event_keys", []) or []
        prior = None
        for r in prior_receipts:
            if r.get("event_id") == event_id:
                prior = r
                break
        if prior is not None:
            if prior.get("payload_hash") != payload_hash:
                return CasResult(
                    code=CasResultCode.EVENT_ID_PAYLOAD_MISMATCH,
                    prior_result_reference=event_id,
                )
            return CasResult(
                code=CasResultCode.DEDUPLICATED_NO_OP,
                new_state_version=int(probe.get("state_version", 0)),
                assigned_event_sequence=int(prior.get("assigned_event_sequence", 0)),
                prior_result_reference=event_id,
            )
        # 2) bounded receipts ring — fail-closed
        if len(prior_receipts) >= ExpeditionRuntimeState.MAX_PROCESSED_EVENTS:
            return CasResult(
                code=CasResultCode.CAP_EXCEEDED,
                reason=f"processed_event_keys ring at limit ({ExpeditionRuntimeState.MAX_PROCESSED_EVENTS})",
            )
        # 3) CAS with filter also checking event_id absence
        current_seq = int(probe.get("last_event_sequence", 0))
        new_sequence = current_seq + 1
        now_iso = _iso_now(self._clock)
        cas_filter = {
            "_id": expedition_id,
            "state_version": expected_state_version,
            "fencing_token": expected_fencing_token,
            # guard against concurrent same-event insertion
            "processed_event_keys.event_id": {"$ne": event_id},
        }
        set_fields: Dict[str, Any] = {"updated_at": now_iso, "last_event_sequence": new_sequence}
        for k, v in mutation.items():
            if k in (
                "adventurer_class_states", "runtime_status",
                "loadout_snapshot_version", "expires_at",
            ):
                # RT2-B-2B-1-V1 · serialize dataclass tuple → BSON-friendly dict
                if k == "adventurer_class_states" and isinstance(v, tuple):
                    set_fields[k] = _serialize_class_states(v)
                else:
                    set_fields[k] = v
        # We use $inc for state_version and $push for the new receipt.
        # The new state_version_after is expected_state_version + 1.
        new_receipt = {
            "event_id": event_id,
            "event_type": event_type,
            "source_adventurer_id": source_adventurer_id,
            "payload_hash": payload_hash,
            "assigned_event_sequence": new_sequence,
            "result_code": CasResultCode.SUCCESS.value,
            "state_version_after": expected_state_version + 1,
            "processed_at": now_iso,
        }
        # RT2-B-2B-2-1 · PM B2B2Q07 (adjudicated): completion result payload
        # EMBEDDED nella processed-event receipt · stesso CAS · stessa slot.
        # Omesso quando None per preservare byte-shape delle receipt legacy.
        if result_payload is not None:
            new_receipt["result_payload"] = _rp_compact(result_payload)
        update = {
            "$inc": {"state_version": 1},
            "$set": set_fields,
            "$push": {"processed_event_keys": new_receipt},
        }
        try:
            doc = await self._collection.find_one_and_update(
                cas_filter, update, return_document=True,
            )
        except Exception as exc:
            raise StoreInfraError(str(exc)) from exc
        if doc is None:
            # CAS failed: probe again to determine reason
            try:
                probe2 = await self._collection.find_one(
                    {"_id": expedition_id},
                    {"state_version": 1, "fencing_token": 1},
                )
            except Exception as exc:
                raise StoreInfraError(str(exc)) from exc
            if probe2 is None:
                return CasResult(code=CasResultCode.NOT_FOUND)
            cur_sv = int(probe2.get("state_version", 0))
            cur_ft = int(probe2.get("fencing_token", 0))
            if not validate_fencing_match(expected_fencing_token, cur_ft):
                return CasResult(
                    code=CasResultCode.STALE_WRITER_REJECTED,
                    new_state_version=cur_sv,
                )
            return CasResult(
                code=CasResultCode.STATE_VERSION_CONFLICT,
                new_state_version=cur_sv,
            )
        return CasResult(
            code=CasResultCode.SUCCESS,
            new_state_version=int(doc.get("state_version", expected_state_version + 1)),
            assigned_event_sequence=new_sequence,
        )

    # ═══════════════════════ 5. reserve_writer ═══════════════════════
    async def reserve_writer(
        self,
        expedition_id: str,
        writer_worker_id: str,
        lease_ttl_seconds: int = 30,
    ) -> LeaseAcquireResult:
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
        try:
            probe = await self._collection.find_one(
                {"_id": expedition_id}, {"fencing_token": 1, "lease": 1},
            )
        except Exception as exc:
            raise StoreInfraError(str(exc)) from exc
        if probe is None:
            return LeaseAcquireResult(code=CasResultCode.NOT_FOUND)
        # Determine target fencing_token
        cur_ft = int(probe.get("fencing_token", 0))
        new_ft = next_fencing_token(cur_ft)
        now_iso = _iso_now(self._clock)
        exp_iso = _iso_add(self._clock, lease_ttl_seconds)
        lease_id = f"lease-{expedition_id}-{new_ft}"
        lease_doc = {
            "lease_id": lease_id,
            "owner_id": writer_worker_id,
            "acquired_at": now_iso,
            "expires_at": exp_iso,
            "fencing_token": new_ft,
            "renewed_at": None,
            "lease_version": 1,
        }
        # CAS: only if lease is currently null OR expired
        cas_filter = {
            "_id": expedition_id,
            "fencing_token": cur_ft,
            "$or": [
                {"lease": None},
                {"lease.expires_at": {"$lt": now_iso}},
            ],
        }
        try:
            doc = await self._collection.find_one_and_update(
                cas_filter,
                {
                    "$set": {
                        "lease": lease_doc,
                        "owner_worker_or_lease_id": writer_worker_id,
                        "fencing_token": new_ft,
                        "updated_at": now_iso,
                    },
                },
                return_document=True,
            )
        except Exception as exc:
            raise StoreInfraError(str(exc)) from exc
        if doc is None:
            return LeaseAcquireResult(
                code=CasResultCode.STATE_VERSION_CONFLICT,
                reason="lease held or concurrent acquisition",
            )
        return LeaseAcquireResult(
            code=CasResultCode.SUCCESS,
            lease_id=lease_id,
            fencing_token=new_ft,
            lease_expires_at=exp_iso,
        )

    # ═══════════════════════ 6. renew_writer_lease ═══════════════════════
    async def renew_writer_lease(
        self,
        expedition_id: str,
        lease_id: str,
        fencing_token: int,
        extend_seconds: int = 30,
    ) -> LeaseAcquireResult:
        now_iso = _iso_now(self._clock)
        # Grace: allow renewal within 5s past expires_at
        grace_cutoff_iso = (self._clock() - timedelta(seconds=5)).isoformat().replace("+00:00", "Z")
        new_exp = _iso_add(self._clock, extend_seconds)
        cas_filter = {
            "_id": expedition_id,
            "lease.lease_id": lease_id,
            "fencing_token": fencing_token,
            "lease.expires_at": {"$gt": grace_cutoff_iso},
        }
        try:
            doc = await self._collection.find_one_and_update(
                cas_filter,
                {
                    "$set": {
                        "lease.expires_at": new_exp,
                        "lease.renewed_at": now_iso,
                        "updated_at": now_iso,
                    },
                    "$inc": {"lease.lease_version": 1},
                },
                return_document=True,
            )
        except Exception as exc:
            raise StoreInfraError(str(exc)) from exc
        if doc is None:
            # Distinguish reason
            try:
                probe = await self._collection.find_one(
                    {"_id": expedition_id}, {"fencing_token": 1, "lease": 1},
                )
            except Exception as exc:
                raise StoreInfraError(str(exc)) from exc
            if probe is None:
                return LeaseAcquireResult(code=CasResultCode.NOT_FOUND)
            if int(probe.get("fencing_token", 0)) != fencing_token:
                return LeaseAcquireResult(code=CasResultCode.STALE_WRITER_REJECTED)
            return LeaseAcquireResult(code=CasResultCode.LEASE_EXPIRED)
        return LeaseAcquireResult(
            code=CasResultCode.SUCCESS,
            lease_id=lease_id,
            fencing_token=fencing_token,
            lease_expires_at=new_exp,
        )

    # ═══════════════════════ 7. release_writer ═══════════════════════
    async def release_writer(
        self,
        expedition_id: str,
        lease_id: str,
        fencing_token: int,
    ) -> CasResult:
        cas_filter = {
            "_id": expedition_id,
            "lease.lease_id": lease_id,
            "fencing_token": fencing_token,
        }
        try:
            doc = await self._collection.find_one_and_update(
                cas_filter,
                {"$set": {"lease": None, "owner_worker_or_lease_id": None, "updated_at": _iso_now(self._clock)}},
                return_document=True,
            )
        except Exception as exc:
            raise StoreInfraError(str(exc)) from exc
        if doc is None:
            # Silent: either not-found or stale fencing.
            try:
                probe = await self._collection.find_one(
                    {"_id": expedition_id}, {"lease": 1},
                )
            except Exception as exc:
                raise StoreInfraError(str(exc)) from exc
            if probe is None:
                return CasResult(code=CasResultCode.NOT_FOUND)
            if probe.get("lease") is None:
                return CasResult(code=CasResultCode.DEDUPLICATED_NO_OP)
            return CasResult(code=CasResultCode.STALE_WRITER_REJECTED)
        return CasResult(code=CasResultCode.SUCCESS)

    # ═══════════════════════ 8. expire_state ═══════════════════════
    async def expire_state(self, expedition_id: str) -> CasResult:
        cas_filter = {
            "_id": expedition_id,
            "runtime_status": {"$nin": [
                RuntimeStatus.EXPIRED.value,
                RuntimeStatus.COMPLETED.value,
                RuntimeStatus.CANCELLED.value,
            ]},
        }
        try:
            doc = await self._collection.find_one_and_update(
                cas_filter,
                {
                    "$set": {"runtime_status": RuntimeStatus.EXPIRED.value, "updated_at": _iso_now(self._clock)},
                    "$inc": {"state_version": 1},
                },
                return_document=True,
            )
        except Exception as exc:
            raise StoreInfraError(str(exc)) from exc
        if doc is None:
            try:
                probe = await self._collection.find_one({"_id": expedition_id}, {"runtime_status": 1})
            except Exception as exc:
                raise StoreInfraError(str(exc)) from exc
            if probe is None:
                return CasResult(code=CasResultCode.NOT_FOUND)
            return CasResult(code=CasResultCode.DEDUPLICATED_NO_OP)
        return CasResult(
            code=CasResultCode.SUCCESS,
            new_state_version=int(doc.get("state_version", 0)),
        )

    # ═══════════════════════ 9. delete_state ═══════════════════════
    async def delete_state(self, expedition_id: str) -> CasResult:
        try:
            r = await self._collection.delete_one({"_id": expedition_id})
        except Exception as exc:
            raise StoreInfraError(str(exc)) from exc
        deleted = getattr(r, "deleted_count", 0)
        if deleted == 0:
            return CasResult(code=CasResultCode.NOT_FOUND)
        return CasResult(code=CasResultCode.SUCCESS)

    # ═══════════════════════ 10. get_version ═══════════════════════
    async def get_version(self, expedition_id: str) -> ReadResult:
        try:
            doc = await self._collection.find_one(
                {"_id": expedition_id}, {"state_version": 1},
            )
        except Exception as exc:
            raise StoreInfraError(str(exc)) from exc
        if doc is None:
            return ReadResult(code=CasResultCode.NOT_FOUND)
        return ReadResult(code=CasResultCode.SUCCESS, version_only=int(doc.get("state_version", 0)))

    # ═══════════════════════ 11. health_check ═══════════════════════
    async def health_check(self) -> bool:
        try:
            # ping via count on a definitely-empty filter (bounded read)
            _ = await self._collection.find_one({"_id": "__healthcheck_probe__"})
        except Exception:
            return False
        return True
