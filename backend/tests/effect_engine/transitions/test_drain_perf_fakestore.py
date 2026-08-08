"""RT2-B-2B-2-1 · Drain FakeStore performance benchmarks (§17 dispatch).

Target (FakeStore · NON sostituisce la futura V1 real-Mongo):
    START_DRAIN p95 <= 35 ms
    COMPLETE_DRAIN + Fragment p95 <= 35 ms
    CANCEL_DRAIN p95 <= 35 ms
    deduplicated retry p95 <= 25 ms
    flags-OFF overhead p95 <= max(5%, 1 ms)
"""
from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.stats.runtime.state_store.fake_store import FakeExpeditionRuntimeStateStore
from app.stats.runtime.state_store.models import ExpeditionRuntimeState, RuntimeStatus
from app.stats.runtime.transitions.dispatcher import ClassTransitionDispatcher
from app.stats.runtime.transitions.models import (
    ClassEventType,
    TransitionResultCode as RC,
)
from app.stats.runtime.wiring.coordinator import ExpeditionRuntimeCoordinator
from tests.effect_engine.transitions.conftest import (
    make_event,
    run,
    trusted_context,
)

ADV = "adv-cdv-01"
TGT = "target-boss-01"
N = 120

_RESULTS_PATH = Path("/tmp/rt2b2b21_drain_perf_fakestore.json")


def _p95(samples: list[float]) -> float:
    ordered = sorted(samples)
    idx = max(0, int(round(0.95 * len(ordered))) - 1)
    return ordered[idx]


def _fresh_env():
    clock = lambda: datetime.now(timezone.utc)  # noqa: E731
    store = FakeExpeditionRuntimeStateStore(clock=clock)
    exp_id = f"exp-perf-{uuid.uuid4().hex[:10]}"
    now = clock()
    shell = ExpeditionRuntimeState(
        expedition_id=exp_id, state_version=1, fencing_token=0,
        created_at=now.isoformat(), updated_at=now.isoformat(),
        expires_at=(now + timedelta(hours=6)).isoformat(),
        runtime_status=RuntimeStatus.ACTIVE,
    )
    assert run(store.create_state(exp_id, shell)).success
    return store, exp_id


def _dispatch(store, event):
    disp = ClassTransitionDispatcher(store=store, worker_id="w-perf")
    return run(disp.dispatch(event, trusted_context=trusted_context()))


def _timed(fn) -> float:
    t0 = time.monotonic()
    fn()
    return (time.monotonic() - t0) * 1000.0


def test_perf_drain_fakestore_p95():
    start_ms, complete_ms, cancel_ms, dedup_ms, off_ms = [], [], [], [], []

    for _ in range(N):
        store, exp_id = _fresh_env()
        assert _dispatch(store, make_event(
            ClassEventType.APPLY_MARK.value, expedition_id=exp_id,
            source_adventurer_id=ADV, target_id=TGT)).result.code is RC.SUCCESS

        # START_DRAIN
        start_ev = make_event(ClassEventType.START_DRAIN.value,
                              expedition_id=exp_id,
                              source_adventurer_id=ADV, target_id=TGT)
        holder = {}

        def _do_start():
            holder["out"] = _dispatch(store, start_ev)

        start_ms.append(_timed(_do_start))
        assert holder["out"].result.code is RC.DRAIN_STARTED
        drain_id = holder["out"].result.drain_execution_id

        # deduplicated retry (replay stesso START)
        dedup_ms.append(_timed(lambda: _dispatch(store, start_ev)))

        # COMPLETE_DRAIN + Fragment batch
        comp_ev = make_event(ClassEventType.COMPLETE_DRAIN.value,
                             expedition_id=exp_id, source_adventurer_id=ADV,
                             drain_execution_id=drain_id)

        def _do_complete():
            holder["comp"] = _dispatch(store, comp_ev)

        complete_ms.append(_timed(_do_complete))
        assert holder["comp"].result.code is RC.DRAIN_COMPLETED

        # CANCEL_DRAIN (nuovo drain su nuovo target)
        assert _dispatch(store, make_event(
            ClassEventType.APPLY_MARK.value, expedition_id=exp_id,
            source_adventurer_id=ADV, target_id="t2")).result.code is RC.SUCCESS
        out2 = _dispatch(store, make_event(
            ClassEventType.START_DRAIN.value, expedition_id=exp_id,
            source_adventurer_id=ADV, target_id="t2"))
        cancel_ev = make_event(ClassEventType.CANCEL_DRAIN.value,
                               expedition_id=exp_id, source_adventurer_id=ADV,
                               drain_execution_id=out2.result.drain_execution_id)

        def _do_cancel():
            holder["can"] = _dispatch(store, cancel_ev)

        cancel_ms.append(_timed(_do_cancel))
        assert holder["can"].result.code is RC.DRAIN_CANCELLED

        # flags-OFF overhead (coordinator · drain kill-switch OFF · 0 DB)
        coord = ExpeditionRuntimeCoordinator(store, "orbus_r16_rt2b_test")
        ctx_off = trusted_context()
        ctx_off["drain_feature_enabled"] = False
        off_ev = make_event(ClassEventType.START_DRAIN.value,
                            expedition_id=exp_id, source_adventurer_id=ADV,
                            target_id="t3")

        def _do_off():
            holder["off"] = run(coord.dispatch_class_state_event(off_ev, ctx_off))

        off_ms.append(_timed(_do_off))
        assert holder["off"].result.code is RC.FEATURE_DISABLED

    metrics = {
        "iterations": N,
        "start_drain_p95_ms": round(_p95(start_ms), 3),
        "complete_drain_fragment_p95_ms": round(_p95(complete_ms), 3),
        "cancel_drain_p95_ms": round(_p95(cancel_ms), 3),
        "deduplicated_retry_p95_ms": round(_p95(dedup_ms), 3),
        "flags_off_overhead_p95_ms": round(_p95(off_ms), 3),
        "targets": {
            "start_drain_p95_ms": 35.0,
            "complete_drain_fragment_p95_ms": 35.0,
            "cancel_drain_p95_ms": 35.0,
            "deduplicated_retry_p95_ms": 25.0,
            "flags_off_overhead_p95_ms": 1.0,
        },
    }
    _RESULTS_PATH.write_text(json.dumps(metrics, indent=2))

    assert metrics["start_drain_p95_ms"] <= 35.0, metrics
    assert metrics["complete_drain_fragment_p95_ms"] <= 35.0, metrics
    assert metrics["cancel_drain_p95_ms"] <= 35.0, metrics
    assert metrics["deduplicated_retry_p95_ms"] <= 25.0, metrics
    # flags-OFF overhead <= max(5% del budget 35ms, 1 ms) = max(1.75, 1) → 1.75;
    # asserzione conservativa a 1.0 ms (il path OFF non tocca store né audit)
    assert metrics["flags_off_overhead_p95_ms"] <= 1.0, metrics
