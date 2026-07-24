"""RT2-B-2B-1-V1 · Real-Mongo integration tests per transitions (matrice 30 item · PM §5).

Pattern: `asyncio.run(go())` per ciascun test, Motor client istanziato dentro il coroutine.

Copertura minima 30 item:
  Mark (1-8) · Fragment (9-14) · Segment (15-18) · Phase/Terminal (19-20)
  Ordering/Dedup (21-23) · Receipt policy (24-26) · Atomicity/CAS (27-29) · Terminal boundary (30)
"""
from __future__ import annotations

import asyncio
import hashlib
import time
import uuid
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

import bson
import pytest
from motor.motor_asyncio import AsyncIOMotorClient

from app.stats.runtime.state_store import CasResultCode, ExpeditionRuntimeState
from app.stats.runtime.state_store.models import (
    AdventurerClassState,
    EventReceipt,
    RuntimeStatus,
)
from app.stats.runtime.state_store.mongo_adapter import MongoExpeditionRuntimeStateStore
from app.stats.runtime.state_store.provisioning import COLLECTION_NAME
from app.stats.runtime.transitions.dispatcher import ClassTransitionDispatcher
from app.stats.runtime.transitions.models import (
    ClassEventType,
    ClassStateEvent,
    TransitionResultCode,
    TrustedDrainReceipt,
)
from app.stats.runtime.transitions.state_machine import (
    RECEIPT_CAP_ORDINARY,
    RECEIPT_CAP_RESERVED,
    RECEIPT_CAP_TOTAL,
    STATE_DOC_MAX_BYTES,
)


MONGO_URI = "mongodb://localhost:27017"


def _iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def _open_store(db_name: str):
    client = AsyncIOMotorClient(MONGO_URI)
    coll = client[db_name][COLLECTION_NAME]
    return client, MongoExpeditionRuntimeStateStore(coll)


def _shell(exp_id: str) -> ExpeditionRuntimeState:
    now = datetime.now(timezone.utc)
    return ExpeditionRuntimeState(
        expedition_id=exp_id,
        state_version=1,
        fencing_token=0,
        created_at=_iso(now),
        updated_at=_iso(now),
        expires_at=_iso(now + timedelta(hours=1)),
        runtime_status=RuntimeStatus.ACTIVE,
        adventurer_class_states=(),
        processed_event_keys=(),
        last_event_sequence=0,
    )


def _mk_event(
    event_type: str,
    *,
    exp_id: str,
    source: str,
    target: str = "",
    amount: int = 0,
    reason_code: str | None = None,
    receipt: TrustedDrainReceipt | None = None,
    event_id: str | None = None,
    payload_hash: str | None = None,
) -> ClassStateEvent:
    eid = event_id or f"evt-{uuid.uuid4().hex[:16]}"
    ph = payload_hash or hashlib.sha256(f"{eid}|{event_type}|{target}|{amount}".encode()).hexdigest()
    return ClassStateEvent(
        event_id=eid,
        event_type=event_type,
        expedition_id=exp_id,
        source_adventurer_id=source,
        target_id=target or None,
        amount=amount,
        payload_version=1,
        payload_hash=ph,
        requested_at=_iso(datetime.now(timezone.utc)),
        expected_state_version=1,
        reason_code=reason_code,
        trusted_drain_receipt=receipt,
    )


def _receipt(source: str, exp_id: str, target: str = "tg-boss-01") -> TrustedDrainReceipt:
    return TrustedDrainReceipt(
        drain_execution_id=f"drn-{uuid.uuid4().hex[:16]}",
        source_adventurer_id=source,
        target_id=target,
        mark_application_id=f"app-{uuid.uuid4().hex[:16]}",
        completed_at=_iso(datetime.now(timezone.utc)),
        result_code="SUCCESS",
        expedition_id=exp_id,
    )


def _ctx(*, feature_enabled: bool = True, test_user_verified: bool = True,
         db_allowlisted: bool = True) -> dict:
    return {
        "feature_enabled": feature_enabled,
        "test_user_verified": test_user_verified,
        "test_user_id": "test-user-mongo",
        "db_allowlisted": db_allowlisted,
        "phase_ended": False,
    }


# ═══════════════════════ Items 1-8 · Mark ═══════════════════════

def test_item_01_apply_mark_success(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-item01"
            await store.create_state(exp_id, _shell(exp_id))
            disp = ClassTransitionDispatcher(store=store, worker_id="w-01")
            ev = _mk_event(ClassEventType.APPLY_MARK.value, exp_id=exp_id, source="adv-1", target="tg-1")
            out = await disp.dispatch(ev, trusted_context=_ctx())
            assert out.result.code is TransitionResultCode.SUCCESS
            assert out.result.mark_id
            assert out.result.active_marks_count_after == 1
        finally:
            client.close()
    asyncio.run(go())


def test_item_02_duplicate_pair_rejected(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-item02"
            await store.create_state(exp_id, _shell(exp_id))
            disp = ClassTransitionDispatcher(store=store, worker_id="w-02")
            await disp.dispatch(_mk_event(ClassEventType.APPLY_MARK.value, exp_id=exp_id, source="adv-1", target="tg-1"), trusted_context=_ctx())
            out = await disp.dispatch(_mk_event(ClassEventType.APPLY_MARK.value, exp_id=exp_id, source="adv-1", target="tg-1"), trusted_context=_ctx())
            assert out.result.code is TransitionResultCode.MARK_ALREADY_ACTIVE_FOR_PAIR
        finally:
            client.close()
    asyncio.run(go())


def test_item_03_mark_cap_exceeded(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-item03"
            await store.create_state(exp_id, _shell(exp_id))
            disp = ClassTransitionDispatcher(store=store, worker_id="w-03")
            for i in range(5):
                r = await disp.dispatch(_mk_event(ClassEventType.APPLY_MARK.value, exp_id=exp_id, source="adv-1", target=f"tg-{i}"), trusted_context=_ctx())
                assert r.result.code is TransitionResultCode.SUCCESS
            out = await disp.dispatch(_mk_event(ClassEventType.APPLY_MARK.value, exp_id=exp_id, source="adv-1", target="tg-6"), trusted_context=_ctx())
            assert out.result.code is TransitionResultCode.MARK_CAP_EXCEEDED
            assert out.result.active_marks_count_after == 5
        finally:
            client.close()
    asyncio.run(go())


def test_item_04_refresh_success(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-item04"
            await store.create_state(exp_id, _shell(exp_id))
            disp = ClassTransitionDispatcher(store=store, worker_id="w-04")
            r1 = await disp.dispatch(_mk_event(ClassEventType.APPLY_MARK.value, exp_id=exp_id, source="adv-1", target="tg-1"), trusted_context=_ctx())
            original_app_id = r1.result.mark_application_id
            r2 = await disp.dispatch(_mk_event(ClassEventType.REFRESH_MARK.value, exp_id=exp_id, source="adv-1", target="tg-1"), trusted_context=_ctx())
            assert r2.result.code is TransitionResultCode.SUCCESS
            assert r2.result.mark_application_id == original_app_id
        finally:
            client.close()
    asyncio.run(go())


def test_item_05_expired_refresh_rejected(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-item05"
            await store.create_state(exp_id, _shell(exp_id))
            # Use frozen clock via dispatcher now_fn to simulate 15s elapse
            base = datetime.now(timezone.utc)
            clock = {"now": base}

            def clock_fn():
                return clock["now"]

            disp = ClassTransitionDispatcher(store=store, worker_id="w-05", now_fn=clock_fn)
            await disp.dispatch(_mk_event(ClassEventType.APPLY_MARK.value, exp_id=exp_id, source="adv-1", target="tg-1"), trusted_context=_ctx())
            clock["now"] = base + timedelta(seconds=15)
            out = await disp.dispatch(_mk_event(ClassEventType.REFRESH_MARK.value, exp_id=exp_id, source="adv-1", target="tg-1"), trusted_context=_ctx())
            assert out.result.code is TransitionResultCode.MARK_EXPIRED
        finally:
            client.close()
    asyncio.run(go())


def test_item_06_lazy_expiration(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-item06"
            await store.create_state(exp_id, _shell(exp_id))
            base = datetime.now(timezone.utc)
            clock = {"now": base}
            disp = ClassTransitionDispatcher(store=store, worker_id="w-06", now_fn=lambda: clock["now"])
            await disp.dispatch(_mk_event(ClassEventType.APPLY_MARK.value, exp_id=exp_id, source="adv-1", target="tg-1"), trusted_context=_ctx())
            clock["now"] = base + timedelta(seconds=15)
            out = await disp.dispatch(_mk_event(ClassEventType.LAZY_MARK_EXPIRATION.value, exp_id=exp_id, source="adv-1"), trusted_context=_ctx())
            assert out.result.code is TransitionResultCode.SUCCESS
            assert out.result.active_marks_count_after == 0
        finally:
            client.close()
    asyncio.run(go())


def test_item_07_opportunistic_cleanup(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-item07"
            await store.create_state(exp_id, _shell(exp_id))
            base = datetime.now(timezone.utc)
            clock = {"now": base}
            disp = ClassTransitionDispatcher(store=store, worker_id="w-07", now_fn=lambda: clock["now"])
            for i in range(3):
                await disp.dispatch(_mk_event(ClassEventType.APPLY_MARK.value, exp_id=exp_id, source="adv-1", target=f"tg-{i}"), trusted_context=_ctx())
            clock["now"] = base + timedelta(seconds=15)
            out = await disp.dispatch(_mk_event(ClassEventType.OPPORTUNISTIC_MARK_CLEANUP.value, exp_id=exp_id, source="adv-1"), trusted_context=_ctx())
            assert out.result.code is TransitionResultCode.SUCCESS
            assert out.result.active_marks_count_after == 0
        finally:
            client.close()
    asyncio.run(go())


def test_item_08_multi_cdv_ownership_isolation(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-item08"
            await store.create_state(exp_id, _shell(exp_id))
            disp = ClassTransitionDispatcher(store=store, worker_id="w-08")
            r1 = await disp.dispatch(_mk_event(ClassEventType.APPLY_MARK.value, exp_id=exp_id, source="adv-A", target="tg-boss"), trusted_context=_ctx())
            r2 = await disp.dispatch(_mk_event(ClassEventType.APPLY_MARK.value, exp_id=exp_id, source="adv-B", target="tg-boss"), trusted_context=_ctx())
            assert r1.result.code is TransitionResultCode.SUCCESS
            assert r2.result.code is TransitionResultCode.SUCCESS
            read = await store.get_state(exp_id)
            cs_a = read.state.class_state_for("adv-A")
            cs_b = read.state.class_state_for("adv-B")
            assert cs_a and len(cs_a.active_marks) == 1
            assert cs_b and len(cs_b.active_marks) == 1
        finally:
            client.close()
    asyncio.run(go())


# ═══════════════════════ Items 9-14 · Fragment ═══════════════════════

def test_item_09_fragment_gain_trusted(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-item09"
            await store.create_state(exp_id, _shell(exp_id))
            disp = ClassTransitionDispatcher(store=store, worker_id="w-09")
            r = await disp.dispatch(
                _mk_event(ClassEventType.GAIN_FRAGMENT.value, exp_id=exp_id, source="adv-1", amount=2, receipt=_receipt("adv-1", exp_id)),
                trusted_context=_ctx(),
            )
            assert r.result.code is TransitionResultCode.SUCCESS
            assert r.result.fragment_count_after == 2
            assert r.result.resource_segment_id is not None
        finally:
            client.close()
    asyncio.run(go())


def test_item_10_fragment_gain_replay_dedup(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-item10"
            await store.create_state(exp_id, _shell(exp_id))
            disp = ClassTransitionDispatcher(store=store, worker_id="w-10")
            ev = _mk_event(ClassEventType.GAIN_FRAGMENT.value, exp_id=exp_id, source="adv-1", amount=1, receipt=_receipt("adv-1", exp_id))
            r1 = await disp.dispatch(ev, trusted_context=_ctx())
            r2 = await disp.dispatch(ev, trusted_context=_ctx())
            assert r1.result.code is TransitionResultCode.SUCCESS
            assert r2.result.code is TransitionResultCode.DEDUPLICATED_NO_OP
        finally:
            client.close()
    asyncio.run(go())


def test_item_11_fragment_gain_untrusted_rejected(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-item11"
            await store.create_state(exp_id, _shell(exp_id))
            disp = ClassTransitionDispatcher(store=store, worker_id="w-11")
            r = await disp.dispatch(
                _mk_event(ClassEventType.GAIN_FRAGMENT.value, exp_id=exp_id, source="adv-1", amount=1, receipt=None),
                trusted_context=_ctx(),
            )
            assert r.result.code is TransitionResultCode.FRAGMENT_GAIN_UNAUTHORIZED
        finally:
            client.close()
    asyncio.run(go())


def test_item_12_fragment_cap_overflow(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-item12"
            await store.create_state(exp_id, _shell(exp_id))
            disp = ClassTransitionDispatcher(store=store, worker_id="w-12")
            for i in range(5):
                r = await disp.dispatch(_mk_event(ClassEventType.GAIN_FRAGMENT.value, exp_id=exp_id, source="adv-1", amount=1, receipt=_receipt("adv-1", exp_id)), trusted_context=_ctx())
                assert r.result.code is TransitionResultCode.SUCCESS
            out = await disp.dispatch(_mk_event(ClassEventType.GAIN_FRAGMENT.value, exp_id=exp_id, source="adv-1", amount=2, receipt=_receipt("adv-1", exp_id)), trusted_context=_ctx())
            assert out.result.code is TransitionResultCode.FRAGMENT_OVERFLOW_DISCARDED
            assert out.result.fragment_count_after == 5
            assert out.result.overflow_discarded == 2
        finally:
            client.close()
    asyncio.run(go())


def test_item_13_fragment_spend_success(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-item13"
            await store.create_state(exp_id, _shell(exp_id))
            disp = ClassTransitionDispatcher(store=store, worker_id="w-13")
            await disp.dispatch(_mk_event(ClassEventType.GAIN_FRAGMENT.value, exp_id=exp_id, source="adv-1", amount=3, receipt=_receipt("adv-1", exp_id)), trusted_context=_ctx())
            r = await disp.dispatch(_mk_event(ClassEventType.SPEND_FRAGMENT.value, exp_id=exp_id, source="adv-1", amount=2), trusted_context=_ctx())
            assert r.result.code is TransitionResultCode.SUCCESS
            assert r.result.fragment_count_after == 1
        finally:
            client.close()
    asyncio.run(go())


def test_item_14_fragment_spend_insufficient(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-item14"
            await store.create_state(exp_id, _shell(exp_id))
            disp = ClassTransitionDispatcher(store=store, worker_id="w-14")
            await disp.dispatch(_mk_event(ClassEventType.GAIN_FRAGMENT.value, exp_id=exp_id, source="adv-1", amount=2, receipt=_receipt("adv-1", exp_id)), trusted_context=_ctx())
            r = await disp.dispatch(_mk_event(ClassEventType.SPEND_FRAGMENT.value, exp_id=exp_id, source="adv-1", amount=3), trusted_context=_ctx())
            assert r.result.code is TransitionResultCode.FRAGMENT_INSUFFICIENT
        finally:
            client.close()
    asyncio.run(go())


# ═══════════════════════ Items 15-18 · Resource segment ═══════════════════════

def test_item_15_segment_opening(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-item15"
            await store.create_state(exp_id, _shell(exp_id))
            disp = ClassTransitionDispatcher(store=store, worker_id="w-15")
            r = await disp.dispatch(_mk_event(ClassEventType.GAIN_FRAGMENT.value, exp_id=exp_id, source="adv-1", amount=1, receipt=_receipt("adv-1", exp_id)), trusted_context=_ctx())
            assert r.result.code is TransitionResultCode.SUCCESS
            assert r.result.resource_segment_id is not None
        finally:
            client.close()
    asyncio.run(go())


def test_item_16_partial_spend_preserves_segment(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-item16"
            await store.create_state(exp_id, _shell(exp_id))
            disp = ClassTransitionDispatcher(store=store, worker_id="w-16")
            for _ in range(3):
                await disp.dispatch(_mk_event(ClassEventType.GAIN_FRAGMENT.value, exp_id=exp_id, source="adv-1", amount=1, receipt=_receipt("adv-1", exp_id)), trusted_context=_ctx())
            read = await store.get_state(exp_id)
            seg_before = read.state.class_state_for("adv-1").resource_segment_id
            r = await disp.dispatch(_mk_event(ClassEventType.SPEND_FRAGMENT.value, exp_id=exp_id, source="adv-1", amount=1), trusted_context=_ctx())
            assert r.result.code is TransitionResultCode.SUCCESS
            assert r.result.resource_segment_id == seg_before
            assert r.result.fragment_count_after == 2
        finally:
            client.close()
    asyncio.run(go())


def test_item_17_zero_balance_closes_segment(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-item17"
            await store.create_state(exp_id, _shell(exp_id))
            disp = ClassTransitionDispatcher(store=store, worker_id="w-17")
            await disp.dispatch(_mk_event(ClassEventType.GAIN_FRAGMENT.value, exp_id=exp_id, source="adv-1", amount=2, receipt=_receipt("adv-1", exp_id)), trusted_context=_ctx())
            r = await disp.dispatch(_mk_event(ClassEventType.SPEND_FRAGMENT.value, exp_id=exp_id, source="adv-1", amount=2), trusted_context=_ctx())
            assert r.result.code is TransitionResultCode.SUCCESS
            assert r.result.fragment_count_after == 0
            assert r.result.resource_segment_id is None
        finally:
            client.close()
    asyncio.run(go())


def test_item_18_explicit_segment_close(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-item18"
            await store.create_state(exp_id, _shell(exp_id))
            disp = ClassTransitionDispatcher(store=store, worker_id="w-18")
            for _ in range(3):
                await disp.dispatch(_mk_event(ClassEventType.GAIN_FRAGMENT.value, exp_id=exp_id, source="adv-1", amount=1, receipt=_receipt("adv-1", exp_id)), trusted_context=_ctx())
            r = await disp.dispatch(_mk_event(ClassEventType.CLOSE_RESOURCE_SEGMENT.value, exp_id=exp_id, source="adv-1", reason_code="EXPLICIT_SERVER_CANCEL"), trusted_context=_ctx())
            assert r.result.code is TransitionResultCode.SUCCESS
            assert r.result.fragment_count_after == 0
            assert r.result.resource_segment_id is None
        finally:
            client.close()
    asyncio.run(go())


# ═══════════════════════ Items 19-20 · Phase/Terminal ═══════════════════════

def test_item_19_phase_end_reset(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-item19"
            await store.create_state(exp_id, _shell(exp_id))
            disp = ClassTransitionDispatcher(store=store, worker_id="w-19")
            await disp.dispatch(_mk_event(ClassEventType.GAIN_FRAGMENT.value, exp_id=exp_id, source="adv-1", amount=3, receipt=_receipt("adv-1", exp_id)), trusted_context=_ctx())
            r = await disp.dispatch(_mk_event(ClassEventType.PHASE_END.value, exp_id=exp_id, source="adv-1", reason_code="PHASE_ENDED"), trusted_context=_ctx())
            assert r.result.code is TransitionResultCode.SUCCESS
            assert r.result.fragment_count_after == 0
            assert r.result.resource_segment_id is None
        finally:
            client.close()
    asyncio.run(go())


def test_item_20_expedition_terminal_reset(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-item20"
            await store.create_state(exp_id, _shell(exp_id))
            disp = ClassTransitionDispatcher(store=store, worker_id="w-20")
            await disp.dispatch(_mk_event(ClassEventType.GAIN_FRAGMENT.value, exp_id=exp_id, source="adv-1", amount=2, receipt=_receipt("adv-1", exp_id)), trusted_context=_ctx())
            r = await disp.dispatch(_mk_event(ClassEventType.EXPEDITION_TERMINAL.value, exp_id=exp_id, source="adv-1", reason_code="EXPEDITION_TERMINAL"), trusted_context=_ctx())
            assert r.result.code is TransitionResultCode.SUCCESS
            assert r.result.fragment_count_after == 0
        finally:
            client.close()
    asyncio.run(go())


# ═══════════════════════ Items 21-23 · Ordering + Dedup ═══════════════════════

def test_item_21_event_total_ordering(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-item21"
            await store.create_state(exp_id, _shell(exp_id))
            disp = ClassTransitionDispatcher(store=store, worker_id="w-21")
            seqs = []
            for i in range(4):
                r = await disp.dispatch(_mk_event(ClassEventType.APPLY_MARK.value, exp_id=exp_id, source="adv-1", target=f"tg-{i}"), trusted_context=_ctx())
                assert r.result.code is TransitionResultCode.SUCCESS
                seqs.append(r.result.assigned_event_sequence)
            assert seqs == [1, 2, 3, 4]
        finally:
            client.close()
    asyncio.run(go())


def test_item_22_same_id_same_payload_dedup(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-item22"
            await store.create_state(exp_id, _shell(exp_id))
            disp = ClassTransitionDispatcher(store=store, worker_id="w-22")
            ev = _mk_event(ClassEventType.APPLY_MARK.value, exp_id=exp_id, source="adv-1", target="tg-1", event_id="fixed-22")
            r1 = await disp.dispatch(ev, trusted_context=_ctx())
            r2 = await disp.dispatch(ev, trusted_context=_ctx())
            assert r1.result.code is TransitionResultCode.SUCCESS
            assert r2.result.code is TransitionResultCode.DEDUPLICATED_NO_OP
        finally:
            client.close()
    asyncio.run(go())


def test_item_23_same_id_diff_payload_rejected(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-item23"
            await store.create_state(exp_id, _shell(exp_id))
            disp = ClassTransitionDispatcher(store=store, worker_id="w-23")
            r1 = await disp.dispatch(_mk_event(ClassEventType.APPLY_MARK.value, exp_id=exp_id, source="adv-1", target="tg-A", event_id="dup-23", payload_hash="a"*64), trusted_context=_ctx())
            r2 = await disp.dispatch(_mk_event(ClassEventType.APPLY_MARK.value, exp_id=exp_id, source="adv-1", target="tg-B", event_id="dup-23", payload_hash="b"*64), trusted_context=_ctx())
            assert r1.result.code is TransitionResultCode.SUCCESS
            assert r2.result.code is TransitionResultCode.EVENT_ID_PAYLOAD_MISMATCH
        finally:
            client.close()
    asyncio.run(go())


# ═══════════════════════ Items 24-26 · Receipt policy ═══════════════════════

def test_item_24_ordinary_cap_504_saturation(provisioned_unique_db):
    """Popola 504 receipts ordinary via insert diretto, poi verifica RECEIPT_CAP_REACHED."""
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-item24"
            now = datetime.now(timezone.utc)
            # Insert diretto: bypass create_state per pre-caricare receipts
            preload_doc = {
                "_id": exp_id,
                "state_version": RECEIPT_CAP_ORDINARY,
                "created_at": _iso(now),
                "updated_at": _iso(now),
                "expires_at": _iso(now + timedelta(hours=1)),
                "runtime_status": RuntimeStatus.ACTIVE.value,
                "owner_worker_or_lease_id": None,
                "lease": None,
                "loadout_snapshot_version": 0,
                "adventurer_class_states": {},
                "processed_event_keys": [
                    {
                        "event_id": f"pre-{i:04d}",
                        "event_type": ClassEventType.APPLY_MARK.value,
                        "source_adventurer_id": "adv-1",
                        "payload_hash": hashlib.sha256(str(i).encode()).hexdigest(),
                        "assigned_event_sequence": i + 1,
                        "result_code": "SUCCESS",
                        "state_version_after": i + 1,
                        "processed_at": _iso(now),
                    }
                    for i in range(RECEIPT_CAP_ORDINARY)
                ],
                "last_event_sequence": RECEIPT_CAP_ORDINARY,
                "fencing_token": 0,
            }
            await client[provisioned_unique_db][COLLECTION_NAME].insert_one(preload_doc)
            disp = ClassTransitionDispatcher(store=store, worker_id="w-24")
            # New ordinary event → RECEIPT_CAP_REACHED
            out = await disp.dispatch(
                _mk_event(ClassEventType.APPLY_MARK.value, exp_id=exp_id, source="adv-1", target="tg-cap"),
                trusted_context=_ctx(),
            )
            assert out.result.code is TransitionResultCode.RECEIPT_CAP_REACHED
            read = await store.get_state(exp_id)
            assert len(read.state.processed_event_keys) == RECEIPT_CAP_ORDINARY
        finally:
            client.close()
    asyncio.run(go())


def test_item_25_reserved_lifecycle_capacity(provisioned_unique_db):
    """504 ordinary + PHASE_END reserved event → deve poter usare slot riservato."""
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-item25"
            now = datetime.now(timezone.utc)
            preload_doc = {
                "_id": exp_id,
                "state_version": RECEIPT_CAP_ORDINARY,
                "created_at": _iso(now),
                "updated_at": _iso(now),
                "expires_at": _iso(now + timedelta(hours=1)),
                "runtime_status": RuntimeStatus.ACTIVE.value,
                "owner_worker_or_lease_id": None,
                "lease": None,
                "loadout_snapshot_version": 0,
                "adventurer_class_states": {},
                "processed_event_keys": [
                    {
                        "event_id": f"ord-{i:04d}",
                        "event_type": ClassEventType.APPLY_MARK.value,
                        "source_adventurer_id": "adv-1",
                        "payload_hash": hashlib.sha256(str(i).encode()).hexdigest(),
                        "assigned_event_sequence": i + 1,
                        "result_code": "SUCCESS",
                        "state_version_after": i + 1,
                        "processed_at": _iso(now),
                    }
                    for i in range(RECEIPT_CAP_ORDINARY)
                ],
                "last_event_sequence": RECEIPT_CAP_ORDINARY,
                "fencing_token": 0,
            }
            await client[provisioned_unique_db][COLLECTION_NAME].insert_one(preload_doc)
            disp = ClassTransitionDispatcher(store=store, worker_id="w-25")
            # RESERVED event (PHASE_END) deve essere accettato dal cap check
            out = await disp.dispatch(
                _mk_event(ClassEventType.PHASE_END.value, exp_id=exp_id, source="adv-1", reason_code="PHASE_ENDED"),
                trusted_context=_ctx(),
            )
            assert out.result.code is TransitionResultCode.SUCCESS, f"reserved slot rejected: {out.result.code}"
        finally:
            client.close()
    asyncio.run(go())


def test_item_26_no_eviction(provisioned_unique_db):
    """Prima receipt persiste dopo N mutazioni successive (no eviction/overwrite)."""
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-item26"
            await store.create_state(exp_id, _shell(exp_id))
            disp = ClassTransitionDispatcher(store=store, worker_id="w-26")
            first_ev_id = "PIN-EVT-01"
            await disp.dispatch(
                _mk_event(ClassEventType.APPLY_MARK.value, exp_id=exp_id, source="adv-1", target="tg-1", event_id=first_ev_id),
                trusted_context=_ctx(),
            )
            for i in range(4):
                await disp.dispatch(_mk_event(ClassEventType.APPLY_MARK.value, exp_id=exp_id, source="adv-1", target=f"tg-more-{i}"), trusted_context=_ctx())
            read = await store.get_state(exp_id)
            ids = [r.event_id for r in read.state.processed_event_keys]
            assert first_ev_id in ids, f"first receipt evicted: {ids}"
            # BSON size verify — use _id as primary key (store uses _id)
            raw = await client[provisioned_unique_db][COLLECTION_NAME].find_one({"_id": exp_id})
            assert raw is not None, "state doc not found"
            bson_bytes = bson.encode(raw)
            assert len(bson_bytes) < STATE_DOC_MAX_BYTES
        finally:
            client.close()
    asyncio.run(go())


# ═══════════════════════ Items 27-29 · Atomicity/CAS ═══════════════════════

def test_item_27_stale_fencing_rejected(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-item27"
            await store.create_state(exp_id, _shell(exp_id))
            lease1 = await store.reserve_writer(exp_id, "w-A", lease_ttl_seconds=1)
            stale = lease1.fencing_token
            await store.release_writer(exp_id, lease1.lease_id, lease1.fencing_token)
            lease2 = await store.reserve_writer(exp_id, "w-B", lease_ttl_seconds=1)
            assert lease2.fencing_token > stale
            cas = await store.compare_and_update(
                expedition_id=exp_id,
                expected_state_version=1,
                expected_fencing_token=stale,
                mutation={"adventurer_class_states": (("adv-X", AdventurerClassState(adventurer_id="adv-X")),)},
            )
            assert cas.code is CasResultCode.STALE_WRITER_REJECTED
        finally:
            client.close()
    asyncio.run(go())


def test_item_28_state_version_cas_conflict(provisioned_unique_db):
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-item28"
            await store.create_state(exp_id, _shell(exp_id))
            lease = await store.reserve_writer(exp_id, "w-A")
            r1 = await store.compare_and_update(
                expedition_id=exp_id, expected_state_version=1, expected_fencing_token=lease.fencing_token,
                mutation={"adventurer_class_states": (("adv-1", AdventurerClassState(adventurer_id="adv-1")),)},
            )
            assert r1.code is CasResultCode.SUCCESS
            r2 = await store.compare_and_update(
                expedition_id=exp_id, expected_state_version=1, expected_fencing_token=lease.fencing_token,
                mutation={"adventurer_class_states": (("adv-2", AdventurerClassState(adventurer_id="adv-2")),)},
            )
            assert r2.code is CasResultCode.STATE_VERSION_CONFLICT
        finally:
            client.close()
    asyncio.run(go())


def test_item_29_retry_max_3(provisioned_unique_db):
    """Verifica: RETRY_MAX = 3 (statica) + tests item 21 mostrano no state-version drift oltre 3."""
    from app.stats.runtime.transitions import dispatcher as disp_mod
    assert disp_mod.RETRY_MAX == 3


# ═══════════════════════ Item 30 · Terminal boundary ═══════════════════════

def test_item_30_terminal_rejects_later_ordinary(provisioned_unique_db):
    """Espedition in stato terminale rifiuta eventi ordinary post-terminal."""
    async def go():
        client, store = _open_store(provisioned_unique_db)
        try:
            exp_id = "exp-item30"
            # Crea state con runtime_status=COMPLETED
            now = datetime.now(timezone.utc)
            shell = ExpeditionRuntimeState(
                expedition_id=exp_id,
                state_version=1,
                fencing_token=0,
                created_at=_iso(now), updated_at=_iso(now),
                expires_at=_iso(now + timedelta(hours=1)),
                runtime_status=RuntimeStatus.COMPLETED,  # terminale
            )
            await store.create_state(exp_id, shell)
            disp = ClassTransitionDispatcher(store=store, worker_id="w-30")
            out = await disp.dispatch(
                _mk_event(ClassEventType.APPLY_MARK.value, exp_id=exp_id, source="adv-1", target="tg-1"),
                trusted_context=_ctx(),
            )
            assert out.result.code is TransitionResultCode.EVENT_POST_TERMINAL_REJECTED
        finally:
            client.close()
    asyncio.run(go())
