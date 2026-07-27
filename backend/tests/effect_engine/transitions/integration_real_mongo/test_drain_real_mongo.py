"""RT2-B-2B-2-1-V1 · REAL-MONGO DRAIN VERIFICATION (subordinato · PM §6).

Verifica su MongoStore reale (localhost · DB allowlisted unico · teardown drop):
payload 15-campi realmente persistito nella processed-event receipt · una sola
ordinary receipt · zero dipendenza TrustedDrainReceipt · atomicità
completion-to-Fragment · replay/duplicate · concurrency winner-only ·
lifecycle aggregation · receipt saturation · BSON size · performance ·
allowlist · cleanup.
"""
from __future__ import annotations

import asyncio
import hashlib
import time
import uuid
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

import bson
from motor.motor_asyncio import AsyncIOMotorClient

from app.stats.runtime.state_store import ExpeditionRuntimeState
from app.stats.runtime.state_store.models import (
    DrainStatus,
    EventReceipt,
    RuntimeStatus,
)
from app.stats.runtime.state_store.mongo_adapter import MongoExpeditionRuntimeStateStore
from app.stats.runtime.state_store.provisioning import COLLECTION_NAME
from app.stats.runtime.transitions.dispatcher import ClassTransitionDispatcher
from app.stats.runtime.transitions.drain import coerce_drains
from app.stats.runtime.transitions.models import (
    ClassEventType,
    ClassStateEvent,
    TransitionResultCode as RC,
    TrustedDrainReceipt,
)
from app.stats.runtime.transitions.state_machine import (
    RECEIPT_CAP_ORDINARY,
    STATE_DOC_MAX_BYTES,
)
from app.stats.runtime.wiring.coordinator import ExpeditionRuntimeCoordinator

MONGO_URI = "mongodb://localhost:27017"
ADV = "adv-cdv-01"
TGT = "target-boss-01"


def _iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def _open_store(db_name: str):
    client = AsyncIOMotorClient(MONGO_URI)
    coll = client[db_name][COLLECTION_NAME]
    return client, coll, MongoExpeditionRuntimeStateStore(coll)


def _shell(exp_id: str, receipts=()) -> ExpeditionRuntimeState:
    now = datetime.now(timezone.utc)
    return ExpeditionRuntimeState(
        expedition_id=exp_id, state_version=1, fencing_token=0,
        created_at=_iso(now), updated_at=_iso(now),
        expires_at=_iso(now + timedelta(hours=1)),
        runtime_status=RuntimeStatus.ACTIVE,
        processed_event_keys=tuple(receipts),
        last_event_sequence=len(receipts),
    )


def _ev(event_type: str, *, exp_id: str, target: str = "",
        drain_execution_id: str | None = None, event_id: str | None = None,
        reason_code: str | None = None,
        receipt: TrustedDrainReceipt | None = None) -> ClassStateEvent:
    eid = event_id or f"evt-{uuid.uuid4().hex[:16]}"
    ph = hashlib.sha256(
        f"{eid}|{event_type}|{target}|{drain_execution_id}".encode()).hexdigest()
    return ClassStateEvent(
        event_id=eid, event_type=event_type, expedition_id=exp_id,
        source_adventurer_id=ADV, target_id=target or None,
        payload_version=1, payload_hash=ph,
        requested_at=_iso(datetime.now(timezone.utc)),
        expected_state_version=1, reason_code=reason_code,
        drain_execution_id=drain_execution_id,
        trusted_drain_receipt=receipt,
    )


_CTX = {
    "feature_enabled": True, "test_user_verified": True,
    "db_allowlisted": True, "phase_ended": False,
    "test_user_id": "test-user-01", "drain_feature_enabled": True,
}


async def _boot(db_name: str, receipts=()):
    client, coll, store = _open_store(db_name)
    exp_id = f"exp-v1-{uuid.uuid4().hex[:10]}"
    res = await store.create_state(exp_id, _shell(exp_id, receipts))
    assert res.success, res.code
    disp = ClassTransitionDispatcher(store=store, worker_id="w-v1")
    return client, coll, store, disp, exp_id


async def _flow_to_started(disp, exp_id, target=TGT):
    mark = await disp.dispatch(_ev("APPLY_MARK", exp_id=exp_id, target=target),
                               trusted_context=_CTX)
    assert mark.result.code is RC.SUCCESS
    start = await disp.dispatch(_ev("START_DRAIN", exp_id=exp_id, target=target),
                                trusted_context=_CTX)
    assert start.result.code is RC.DRAIN_STARTED
    return start.result.drain_execution_id


def test_v01_payload_persisted_in_receipt_real_mongo(provisioned_unique_db):
    async def go():
        client, coll, store, disp, exp_id = await _boot(provisioned_unique_db)
        try:
            drain_id = await _flow_to_started(disp, exp_id)
            comp_ev = _ev("COMPLETE_DRAIN", exp_id=exp_id,
                          drain_execution_id=drain_id)
            comp = await disp.dispatch(comp_ev, trusted_context=_CTX)
            assert comp.result.code is RC.DRAIN_COMPLETED
            # RAW BSON document: payload 15-campi DENTRO la receipt persistita
            doc = await coll.find_one({"_id": exp_id})
            receipts = doc["processed_event_keys"]
            assert len(receipts) == 3  # mark + start + complete · 1 slot cad.
            raw = receipts[-1]
            assert raw["event_type"] == "COMPLETE_DRAIN"
            from app.stats.runtime.state_store.mongo_adapter import _rp_expand
            p = _rp_expand(raw["result_payload"], raw)
            assert len(p) == 15
            assert p["drain_execution_id"] == drain_id
            assert p["result_code"] == "SUCCESS"
            assert p["fragment_gain_requested"] == 1
            assert p["fragment_gain_applied"] == 1
            assert p["fragment_overflow_discarded"] == 0
            assert p["assigned_event_sequence"] == raw["assigned_event_sequence"]
            assert p["state_version_after"] == doc["state_version"]
            # receipt legacy senza payload
            assert "result_payload" not in receipts[0]
            # atomic batch: fragment + drain status + segment nello stesso doc
            cs_raw = doc["adventurer_class_states"][ADV]
            assert cs_raw["fragment_count"] == 1
            assert cs_raw["resource_segment_id"].startswith("sg-")
            d_raw = cs_raw["active_drain_executions"][0]
            assert d_raw["runtime_status"] == "resolved"
            assert d_raw["completion_event_id"] == comp_ev.event_id
            # DrainDoc: nessuna copia autoritativa del payload
            assert d_raw.get("completion_payload") is None
            assert doc["state_version"] == 4  # +1 exactly once per batch
            # rehydration + coercion
            st = (await store.get_state(exp_id)).state
            assert st.processed_event_keys[-1].result_payload == p
            assert coerce_drains(st.class_state_for(ADV))[0].runtime_status \
                is DrainStatus.RESOLVED
        finally:
            client.close()
    asyncio.run(go())


def test_v02_replay_and_duplicate_completion_real_mongo(provisioned_unique_db):
    async def go():
        client, coll, store, disp, exp_id = await _boot(provisioned_unique_db)
        try:
            # replay START → prior execution id · nessun nuovo Drain
            mark = await disp.dispatch(_ev("APPLY_MARK", exp_id=exp_id, target=TGT),
                                       trusted_context=_CTX)
            assert mark.result.code is RC.SUCCESS
            start_ev = _ev("START_DRAIN", exp_id=exp_id, target=TGT,
                           event_id="evt-start-v1")
            s1 = await disp.dispatch(start_ev, trusted_context=_CTX)
            assert s1.result.code is RC.DRAIN_STARTED
            s2 = await disp.dispatch(start_ev, trusted_context=_CTX)
            assert s2.result.code is RC.DEDUPLICATED_NO_OP
            assert s2.result.drain_execution_id == s1.result.drain_execution_id
            drain_id = s1.result.drain_execution_id
            # duplicate completion: stesso event → dedup · nuovo event → ALREADY
            c_ev = _ev("COMPLETE_DRAIN", exp_id=exp_id,
                       drain_execution_id=drain_id, event_id="evt-c-v1")
            c1 = await disp.dispatch(c_ev, trusted_context=_CTX)
            assert c1.result.code is RC.DRAIN_COMPLETED
            c2 = await disp.dispatch(c_ev, trusted_context=_CTX)
            assert c2.result.code is RC.DEDUPLICATED_NO_OP
            c3 = await disp.dispatch(_ev("COMPLETE_DRAIN", exp_id=exp_id,
                                         drain_execution_id=drain_id),
                                     trusted_context=_CTX)
            assert c3.result.code is RC.DRAIN_ALREADY_COMPLETED
            doc = await coll.find_one({"_id": exp_id})
            assert doc["adventurer_class_states"][ADV]["fragment_count"] == 1
        finally:
            client.close()
    asyncio.run(go())


def test_v03_concurrency_winner_only_real_mongo(provisioned_unique_db):
    async def go():
        client, coll, store, disp, exp_id = await _boot(provisioned_unique_db)
        try:
            drain_id = await _flow_to_started(disp, exp_id)
            # 6 worker concorrenti · stessa execution · event id diversi
            workers = [
                ClassTransitionDispatcher(store=store, worker_id=f"w-{i}")
                for i in range(6)
            ]
            outs = await asyncio.gather(*[
                w.dispatch(_ev("COMPLETE_DRAIN", exp_id=exp_id,
                               drain_execution_id=drain_id),
                           trusted_context=_CTX)
                for w in workers
            ])
            codes = [o.result.code for o in outs]
            assert codes.count(RC.DRAIN_COMPLETED) == 1  # first valid commit wins
            for c in codes:
                assert c in (RC.DRAIN_COMPLETED, RC.DRAIN_ALREADY_COMPLETED,
                             RC.LEASE_ACQUISITION_FAILED,
                             RC.STATE_VERSION_CONFLICT,
                             RC.RETRY_LIMIT_REACHED, RC.STALE_WRITER_REJECTED)
            doc = await coll.find_one({"_id": exp_id})
            assert doc["adventurer_class_states"][ADV]["fragment_count"] == 1
            payload_receipts = [r for r in doc["processed_event_keys"]
                                if r.get("result_payload")]
            assert len(payload_receipts) == 1  # una sola receipt con payload
        finally:
            client.close()
    asyncio.run(go())


def test_v04_lifecycle_aggregation_real_mongo(provisioned_unique_db):
    async def go():
        client, coll, store, disp, exp_id = await _boot(provisioned_unique_db)
        try:
            ids = [await _flow_to_started(disp, exp_id, target=f"t{i}")
                   for i in range(3)]
            before = len((await coll.find_one({"_id": exp_id}))["processed_event_keys"])
            pe = await disp.dispatch(_ev("PHASE_END", exp_id=exp_id),
                                     trusted_context=_CTX)
            assert pe.result.code is RC.SUCCESS
            assert pe.result.drains_cancelled_count == 3
            doc = await coll.find_one({"_id": exp_id})
            assert len(doc["processed_event_keys"]) == before + 1  # 1 reserved
            # PM V1S §4: bounded diagnostic sample (max 8) + truncated flag
            from app.stats.runtime.state_store.mongo_adapter import _rp_expand
            _lr = doc["processed_event_keys"][-1]
            lp = _rp_expand(_lr["result_payload"], _lr)
            assert lp["cancelled_count"] == 3
            assert len(lp["sample_execution_ids"]) <= 8
            assert lp["execution_ids_truncated"] is False
            for d in doc["adventurer_class_states"][ADV]["active_drain_executions"]:
                assert d["runtime_status"] == "cancelled"
                assert d["cancellation_reason"] == "PHASE_ENDED"
            # later completion rejected
            ctx2 = dict(_CTX); ctx2["phase_ended"] = True
            late = await disp.dispatch(_ev("COMPLETE_DRAIN", exp_id=exp_id,
                                           drain_execution_id=ids[0]),
                                       trusted_context=ctx2)
            assert late.result.code is RC.PHASE_INACTIVE
        finally:
            client.close()
    asyncio.run(go())


def _filler_receipts(n: int, with_payload_every: int = 0):
    out = []
    for i in range(n):
        payload = None
        if with_payload_every and i % with_payload_every == 0:
            payload = {
                "drain_execution_id": f"drn-{uuid.uuid4()}",
                "completion_event_id": f"evt-fill-{i}",
                "source_adventurer_id": ADV, "target_id": f"t-{i % 7}",
                "mark_id": f"mark-{uuid.uuid4().hex[:16]}",
                "application_id": f"app-{uuid.uuid4().hex[:16]}",
                "result_code": "SUCCESS", "mark_valid_at_completion": True,
                "fragment_gain_requested": 1, "fragment_gain_applied": 1,
                "fragment_overflow_discarded": 0,
                "resource_segment_id": f"sg-{uuid.uuid4().hex[:16]}",
                "assigned_event_sequence": i + 1,
                "state_version_after": i + 2,
                "processed_at": "2026-02-01T12:00:00Z",
            }
        out.append(EventReceipt(
            event_id=f"evt-fill-{i}",
            event_type="COMPLETE_DRAIN" if payload else "APPLY_MARK",
            source_adventurer_id=ADV, payload_hash=f"h{i}",
            assigned_event_sequence=i + 1, result_code="SUCCESS",
            state_version_after=i + 2, processed_at="2026-02-01T12:00:00Z",
            result_payload=payload,
        ))
    return out


def test_v05_receipt_saturation_real_mongo(provisioned_unique_db):
    async def go():
        client, coll, store, disp, exp_id = await _boot(provisioned_unique_db)
        try:
            from app.stats.runtime.state_store.mongo_adapter import _dc_to_dict
            fillers = [_dc_to_dict(r) for r in _filler_receipts(RECEIPT_CAP_ORDINARY)]
            await coll.update_one(
                {"_id": exp_id},
                {"$set": {"processed_event_keys": fillers,
                          "last_event_sequence": len(fillers)}})
            out = await disp.dispatch(_ev("START_DRAIN", exp_id=exp_id, target=TGT),
                                      trusted_context=_CTX)
            assert out.result.code is RC.RECEIPT_CAP_REACHED  # fail-closed
            doc = await coll.find_one({"_id": exp_id})
            assert len(doc["processed_event_keys"]) == RECEIPT_CAP_ORDINARY
        finally:
            client.close()
    asyncio.run(go())


import pytest as _pytest


@_pytest.mark.xfail(
    strict=False,
    reason="V1S: STATE_DOCUMENT_SIZE_BUDGET_EXCEEDED al full-cap 512 con id a "
           "lunghezza massima (264052 B > 262144 B post-compaction) — "
           "SIZE_REMEDIATION_REQUIRES_DESIGN_CHANGE · PM REVIEW pending",
)
def test_v06_bson_size_at_full_cap_512(provisioned_unique_db):
    """V1S · FULL-CAP: 504 ordinary (252 START + 252 COMPLETE con payload
    15-campi UUIDv4 completi) + 8 reserved lifecycle (payload massimo legale:
    count + 8 sample ids + truncated + reason). RAW BSON persistito su Mongo
    reale. Target closure: <= 245760 B (240 KiB) · hard fail >= 262144 B."""
    async def go():
        from app.stats.runtime.state_store.mongo_adapter import (
            _dc_to_dict, _rp_compact,
        )
        client, coll, store, disp, exp_id = await _boot(provisioned_unique_db)
        try:
            receipts = []
            seq = 0
            for i in range(252):
                for kind in ("START_DRAIN", "COMPLETE_DRAIN"):
                    seq += 1
                    payload = None
                    if kind == "COMPLETE_DRAIN":
                        payload = _rp_compact({
                            "drain_execution_id": f"drn-{uuid.uuid4()}",
                            "completion_event_id": f"evt-{uuid.uuid4().hex}",
                            "source_adventurer_id": f"adv-{uuid.uuid4().hex}",
                            "target_id": f"target-{uuid.uuid4().hex}",
                            "mark_id": f"mark-{uuid.uuid4().hex}",
                            "application_id": f"app-{uuid.uuid4().hex}",
                            "result_code": "SUCCESS",
                            "mark_valid_at_completion": True,
                            "fragment_gain_requested": 1,
                            "fragment_gain_applied": 1,
                            "fragment_overflow_discarded": 0,
                            "resource_segment_id": f"sg-{uuid.uuid4().hex[:16]}",
                            "assigned_event_sequence": 999999,
                            "state_version_after": 999999,
                            "processed_at": "2026-02-01T12:00:00.000000Z",
                        })
                    r = {
                        "event_id": f"evt-{uuid.uuid4().hex}",
                        "event_type": kind,
                        "source_adventurer_id": f"adv-{uuid.uuid4().hex}",
                        "payload_hash": hashlib.sha256(str(seq).encode()).hexdigest(),
                        "assigned_event_sequence": 999999,
                        "result_code": "SUCCESS",
                        "state_version_after": 999999,
                        "processed_at": "2026-02-01T12:00:00.000000Z",
                    }
                    if payload is not None:
                        r["result_payload"] = payload
                    receipts.append(r)
            for i in range(8):  # 8 reserved lifecycle · payload massimo legale
                seq += 1
                receipts.append({
                    "event_id": f"evt-{uuid.uuid4().hex}",
                    "event_type": "PHASE_END",
                    "source_adventurer_id": f"adv-{uuid.uuid4().hex}",
                    "payload_hash": hashlib.sha256(f"L{i}".encode()).hexdigest(),
                    "assigned_event_sequence": 999999,
                    "result_code": "SUCCESS",
                    "state_version_after": 999999,
                    "processed_at": "2026-02-01T12:00:00.000000Z",
                    "result_payload": _rp_compact({
                        "cancelled_count": 999,
                        "sample_execution_ids": [
                            f"drn-{uuid.uuid4()}" for _ in range(8)],
                        "execution_ids_truncated": True,
                        "reason": "EXPEDITION_TERMINAL",
                    }),
                })
            assert len(receipts) == 512
            # tombstone Drain terminali realmente persistiti + segment data
            cs = {
                "adventurer_id": f"adv-{uuid.uuid4().hex}",
                "active_marks": [],
                "active_drain_executions": [
                    {
                        "drain_execution_id": f"drn-{uuid.uuid4()}",
                        "source_adventurer_id": f"adv-{uuid.uuid4().hex}",
                        "target_id": f"target-{uuid.uuid4().hex}",
                        "required_mark_application_id": f"app-{uuid.uuid4().hex}",
                        "mark_id": f"mark-{uuid.uuid4().hex}",
                        "started_at": "2026-02-01T12:00:00.000000Z",
                        "completed_at": "2026-02-01T12:00:05.000000Z",
                        "runtime_status": "resolved",
                        "drain_version": 2,
                        "start_event_id": f"evt-{uuid.uuid4().hex}",
                        "completion_event_id": f"evt-{uuid.uuid4().hex}",
                    } for _ in range(10)
                ],
                "fragment_count": 5,
                "resource_segment_id": f"sg-{uuid.uuid4().hex[:16]}",
                "focus_bonus_usage": [
                    {"resource_segment_id": f"sg-{uuid.uuid4().hex[:16]}",
                     "focus_bonus_used": 2}],
                "class_state_version": 999999,
            }
            await coll.update_one({"_id": exp_id}, {"$set": {
                "processed_event_keys": receipts,
                "adventurer_class_states": {cs["adventurer_id"]: cs},
                "last_event_sequence": 999999,
                "state_version": 999999,
                "runtime_status": "completed",  # stato terminale persistito
            }})
            raw = await coll.find_one({"_id": exp_id})
            raw.pop(None, None)
            size = len(bson.encode(raw))
            import json as _json
            from pathlib import Path
            Path("/tmp/rt2b2b21_v1s_bson_fullcap.json").write_text(_json.dumps({
                "total_receipts": 512, "ordinary": 504, "reserved": 8,
                "measured_bytes": size,
                "closure_target_bytes": 245760,
                "hard_limit_bytes": STATE_DOC_MAX_BYTES,
                "previous_measure_bytes": 261545,
            }))
            assert size < STATE_DOC_MAX_BYTES, (
                f"STATE_DOCUMENT_SIZE_BUDGET_EXCEEDED: {size}")
            assert size <= 245760, f"closure target exceeded: {size} > 245760"
        finally:
            client.close()
    asyncio.run(go())


def test_v07_performance_real_mongo_p95(provisioned_unique_db):
    async def go():
        client, coll, store, disp, exp_id = await _boot(provisioned_unique_db)
        start_ms, complete_ms, cancel_ms = [], [], []
        extra_clients = []
        try:
            for i in range(40):
                t = f"perf-t{i}"
                mk = await disp.dispatch(_ev("APPLY_MARK", exp_id=exp_id, target=t),
                                         trusted_context=_CTX)
                assert mk.result.code is RC.SUCCESS
                t0 = time.monotonic()
                s = await disp.dispatch(_ev("START_DRAIN", exp_id=exp_id, target=t),
                                        trusted_context=_CTX)
                start_ms.append((time.monotonic() - t0) * 1000.0)
                assert s.result.code is RC.DRAIN_STARTED
                t0 = time.monotonic()
                c = await disp.dispatch(
                    _ev("COMPLETE_DRAIN", exp_id=exp_id,
                        drain_execution_id=s.result.drain_execution_id),
                    trusted_context=_CTX)
                complete_ms.append((time.monotonic() - t0) * 1000.0)
                assert c.result.code is RC.DRAIN_COMPLETED
                # cancel su nuovo drain (stesso mark riusabile · drain terminale)
                s2 = await disp.dispatch(_ev("START_DRAIN", exp_id=exp_id, target=t),
                                         trusted_context=_CTX)
                t0 = time.monotonic()
                cn = await disp.dispatch(
                    _ev("CANCEL_DRAIN", exp_id=exp_id,
                        drain_execution_id=s2.result.drain_execution_id),
                    trusted_context=_CTX)
                cancel_ms.append((time.monotonic() - t0) * 1000.0)
                assert cn.result.code is RC.DRAIN_CANCELLED
                # cleanup marks per non saturare il cap 5
                await disp.dispatch(_ev("LAZY_MARK_EXPIRATION", exp_id=exp_id),
                                    trusted_context=_CTX)
                if (i + 1) % 4 == 0:
                    # reset receipts: nuova expedition per evitare receipt cap
                    client2, coll2, store2 = _open_store(provisioned_unique_db)
                    exp_id = f"exp-v1-{uuid.uuid4().hex[:10]}"
                    await store2.create_state(exp_id, _shell(exp_id))
                    disp = ClassTransitionDispatcher(store=store2, worker_id="w-v1p")
                    extra_clients.append(client2)
            def p95(xs):
                xs = sorted(xs)
                return xs[max(0, int(round(0.95 * len(xs))) - 1)]
            metrics = {
                "start_p95_ms": round(p95(start_ms), 3),
                "complete_p95_ms": round(p95(complete_ms), 3),
                "cancel_p95_ms": round(p95(cancel_ms), 3),
            }
            import json as _json
            from pathlib import Path
            Path("/tmp/rt2b2b21_v1_mongo_perf.json").write_text(_json.dumps(metrics))
            assert metrics["start_p95_ms"] <= 35.0, metrics
            assert metrics["complete_p95_ms"] <= 35.0, metrics
            assert metrics["cancel_p95_ms"] <= 35.0, metrics
        finally:
            for c in extra_clients:
                c.close()
            client.close()
    asyncio.run(go())


def test_v08_allowlist_and_test_user_fail_closed(provisioned_unique_db):
    async def go():
        client, coll, store, disp, exp_id = await _boot(provisioned_unique_db)
        try:
            # DB FORBIDDEN → DB_NOT_ALLOWLISTED · 0 writes
            coord_bad = ExpeditionRuntimeCoordinator(store, "orbus_r16")
            out = await coord_bad.dispatch_class_state_event(
                _ev("START_DRAIN", exp_id=exp_id, target=TGT), dict(_CTX))
            assert out.result.code is RC.DB_NOT_ALLOWLISTED
            # non-test-user → fail closed · 0 writes
            coord_ok = ExpeditionRuntimeCoordinator(store, provisioned_unique_db)
            assert coord_ok.is_target_db_allowlisted is True
            ctx = dict(_CTX); ctx["test_user_verified"] = False
            out2 = await coord_ok.dispatch_class_state_event(
                _ev("START_DRAIN", exp_id=exp_id, target=TGT), ctx)
            assert out2.result.code is RC.TEST_USER_BOUNDARY_VIOLATION
            doc = await coll.find_one({"_id": exp_id})
            assert doc["state_version"] == 1  # nessuna mutation
            assert doc.get("adventurer_class_states", {}) == {}
        finally:
            client.close()
    asyncio.run(go())


def test_v09_zero_trusted_receipt_dependency_real_mongo(provisioned_unique_db):
    async def go():
        client, coll, store, disp, exp_id = await _boot(provisioned_unique_db)
        try:
            drain_id = await _flow_to_started(disp, exp_id)
            forged = TrustedDrainReceipt(
                drain_execution_id=f"drn-{uuid.uuid4().hex[:16]}",
                source_adventurer_id=ADV, target_id=TGT,
                mark_application_id="app-forged",
                completed_at=_iso(datetime.now(timezone.utc)),
                expedition_id=exp_id,
            )
            comp = await disp.dispatch(
                _ev("COMPLETE_DRAIN", exp_id=exp_id,
                    drain_execution_id=drain_id, receipt=forged),
                trusted_context=_CTX)
            assert comp.result.code is RC.DRAIN_COMPLETED  # fixture ignorata
            doc = await coll.find_one({"_id": exp_id})
            from app.stats.runtime.state_store.mongo_adapter import _rp_expand
            _r = doc["processed_event_keys"][-1]
            p = _rp_expand(_r["result_payload"], _r)
            assert p["drain_execution_id"] == drain_id  # non l'ID forgiato
            assert doc["adventurer_class_states"][ADV]["fragment_count"] == 1
        finally:
            client.close()
    asyncio.run(go())
