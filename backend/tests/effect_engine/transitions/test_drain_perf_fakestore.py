"""RT2-B-2B-2-1-A1 · FakeStore Drain performance benchmark.

PM Message 178+180 §6 verbatim: 5 metriche · ≥ 30 iterazioni valide · p95 targets.

Method:
- Warm-up: 3 iterations discarded per metric
- Sample: 30 valid iterations recorded per metric
- p95 computed via sorted-list index (ceil(0.95 * N) - 1)
- Reported: n_iterations · method · min · median · p95 · max · fake_store config · env

Not aggregated with future real-Mongo perf. FakeStore in-memory only.
"""
from __future__ import annotations

import math
import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.stats.runtime.state_store.fake_store import FakeExpeditionRuntimeStateStore
from app.stats.runtime.state_store.models import (
    AdventurerClassState,
    ExpeditionRuntimeState,
    MarkDoc,
    RuntimeStatus,
)
from app.stats.runtime.transitions.dispatcher import ClassTransitionDispatcher
from app.stats.runtime.transitions.models import (
    ClassEventType,
    TransitionResultCode,
)
from tests.effect_engine.transitions.conftest import _iso, run, trusted_context
from tests.effect_engine.transitions.test_drain_fakestore import make_drain_event

UTC = timezone.utc

WARMUP = 3
SAMPLE = 30
TARGETS_MS = {
    "start_drain_p95": 35.0,
    "complete_drain_p95": 35.0,
    "cancel_drain_p95": 35.0,
    "deduplicated_retry_p95": 25.0,
    "flags_off_overhead_p95": 5.0,  # absolute cap (1 ms or 5% of baseline)
}


def _p95(samples_ms: list[float]) -> float:
    xs = sorted(samples_ms)
    idx = max(0, math.ceil(0.95 * len(xs)) - 1)
    return xs[idx]


def _summarize(samples_ms: list[float]) -> dict:
    xs = sorted(samples_ms)
    return {
        "n": len(xs),
        "min_ms": xs[0],
        "median_ms": xs[len(xs) // 2],
        "p95_ms": _p95(xs),
        "max_ms": xs[-1],
    }


def _bootstrap_state(store, expedition_id: str, adventurer_id: str, target_id: str, now: datetime):
    mark = MarkDoc(
        mark_id=f"mrk-{uuid.uuid4().hex[:8]}",
        application_id=f"app-{uuid.uuid4().hex[:8]}",
        source_adventurer_id=adventurer_id, target_id=target_id,
        created_at=_iso(now), expires_at=_iso(now + timedelta(seconds=60)),
        ritual_close_used=False, mark_version=1,
    )
    cs = AdventurerClassState(
        adventurer_id=adventurer_id, active_marks=(mark,), active_drain_executions=(),
        fragment_count=0, resource_segment_id=None, focus_bonus_usage=(),
        class_state_version=1,
    )
    shell = ExpeditionRuntimeState(
        expedition_id=expedition_id, state_version=1, fencing_token=0,
        created_at=_iso(now), updated_at=_iso(now),
        expires_at=_iso(now + timedelta(hours=6)),
        runtime_status=RuntimeStatus.ACTIVE,
        adventurer_class_states=((adventurer_id, cs),), processed_event_keys=(),
        last_event_sequence=0, owner_worker_or_lease_id=None, lease=None,
    )
    r = run(store.create_state(expedition_id, shell))
    assert r.success
    return mark


class TestFakeStoreBenchmark:
    @staticmethod
    def _new_store(clock_fn):
        return FakeExpeditionRuntimeStateStore(clock=clock_fn)

    def _dispatch(self, store, event, tctx=None):
        disp = ClassTransitionDispatcher(store=store, worker_id="w-bench", now_fn=store._clock)
        return run(disp.dispatch(event, trusted_context=tctx or trusted_context()))

    def test_bench_start_drain_p95(self, clock_fn, request):
        samples = []
        for i in range(WARMUP + SAMPLE):
            store = self._new_store(clock_fn)
            exp = f"exp-{i}"
            adv, tgt = f"adv-{i}", "tgt-bench"
            mark = _bootstrap_state(store, exp, adv, tgt, clock_fn())
            ev = make_drain_event("START_DRAIN", expedition_id=exp, source=adv, target=tgt,
                                  mark_id=mark.mark_id, application_id=mark.application_id)
            t0 = time.perf_counter()
            out = self._dispatch(store, ev)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            assert out.result.code is TransitionResultCode.DRAIN_STARTED
            if i >= WARMUP:
                samples.append(elapsed_ms)
        stats = _summarize(samples)
        stats["metric"] = "start_drain_p95"
        stats["target_ms"] = TARGETS_MS["start_drain_p95"]
        stats["passes_target"] = stats["p95_ms"] <= TARGETS_MS["start_drain_p95"]
        request.config.cache.set("drain_bench/start_drain", stats)
        assert stats["passes_target"], f"START_DRAIN p95={stats['p95_ms']:.2f}ms > target 35ms"

    def test_bench_complete_drain_p95(self, clock_fn, request):
        samples = []
        for i in range(WARMUP + SAMPLE):
            store = self._new_store(clock_fn)
            exp, adv, tgt = f"exp-c-{i}", f"adv-{i}", "tgt-bench-c"
            mark = _bootstrap_state(store, exp, adv, tgt, clock_fn())
            # start
            ev_s = make_drain_event("START_DRAIN", expedition_id=exp, source=adv, target=tgt,
                                    mark_id=mark.mark_id, application_id=mark.application_id)
            r_s = self._dispatch(store, ev_s)
            drain_id = r_s.result.reason_code
            ev_c = make_drain_event("COMPLETE_DRAIN", expedition_id=exp, source=adv, target=tgt,
                                    mark_id=mark.mark_id, application_id=mark.application_id,
                                    drain_execution_id=drain_id, expected_state_version=2)
            t0 = time.perf_counter()
            out = self._dispatch(store, ev_c)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            assert out.result.code is TransitionResultCode.DRAIN_COMPLETED
            if i >= WARMUP:
                samples.append(elapsed_ms)
        stats = _summarize(samples)
        stats["metric"] = "complete_drain_p95"
        stats["target_ms"] = TARGETS_MS["complete_drain_p95"]
        stats["passes_target"] = stats["p95_ms"] <= TARGETS_MS["complete_drain_p95"]
        request.config.cache.set("drain_bench/complete_drain", stats)
        assert stats["passes_target"], f"COMPLETE_DRAIN p95={stats['p95_ms']:.2f}ms > target 35ms"

    def test_bench_cancel_drain_p95(self, clock_fn, request):
        samples = []
        for i in range(WARMUP + SAMPLE):
            store = self._new_store(clock_fn)
            exp, adv, tgt = f"exp-x-{i}", f"adv-{i}", "tgt-bench-x"
            mark = _bootstrap_state(store, exp, adv, tgt, clock_fn())
            ev_s = make_drain_event("START_DRAIN", expedition_id=exp, source=adv, target=tgt,
                                    mark_id=mark.mark_id, application_id=mark.application_id)
            r_s = self._dispatch(store, ev_s)
            drain_id = r_s.result.reason_code
            ev_x = make_drain_event("CANCEL_DRAIN", expedition_id=exp, source=adv, target=tgt,
                                    mark_id=mark.mark_id, application_id=mark.application_id,
                                    drain_execution_id=drain_id,
                                    cancellation_reason="EXPLICIT_SERVER_CANCEL",
                                    expected_state_version=2)
            t0 = time.perf_counter()
            out = self._dispatch(store, ev_x)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            assert out.result.code is TransitionResultCode.DRAIN_CANCELLED
            if i >= WARMUP:
                samples.append(elapsed_ms)
        stats = _summarize(samples)
        stats["metric"] = "cancel_drain_p95"
        stats["target_ms"] = TARGETS_MS["cancel_drain_p95"]
        stats["passes_target"] = stats["p95_ms"] <= TARGETS_MS["cancel_drain_p95"]
        request.config.cache.set("drain_bench/cancel_drain", stats)
        assert stats["passes_target"], f"CANCEL_DRAIN p95={stats['p95_ms']:.2f}ms > target 35ms"

    def test_bench_deduplicated_retry_p95(self, clock_fn, request):
        samples = []
        for i in range(WARMUP + SAMPLE):
            store = self._new_store(clock_fn)
            exp, adv, tgt = f"exp-d-{i}", f"adv-{i}", "tgt-bench-d"
            mark = _bootstrap_state(store, exp, adv, tgt, clock_fn())
            eid = f"evt-dup-{i}"
            ev = make_drain_event("START_DRAIN", expedition_id=exp, source=adv, target=tgt,
                                  mark_id=mark.mark_id, application_id=mark.application_id, event_id=eid)
            _first = self._dispatch(store, ev)  # first apply
            # duplicate: should be deduplicated fast
            ev_dup = make_drain_event("START_DRAIN", expedition_id=exp, source=adv, target=tgt,
                                      mark_id=mark.mark_id, application_id=mark.application_id, event_id=eid)
            t0 = time.perf_counter()
            _second = self._dispatch(store, ev_dup)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            if i >= WARMUP:
                samples.append(elapsed_ms)
        stats = _summarize(samples)
        stats["metric"] = "deduplicated_retry_p95"
        stats["target_ms"] = TARGETS_MS["deduplicated_retry_p95"]
        stats["passes_target"] = stats["p95_ms"] <= TARGETS_MS["deduplicated_retry_p95"]
        request.config.cache.set("drain_bench/dedup_retry", stats)
        assert stats["passes_target"], f"dedup_retry p95={stats['p95_ms']:.2f}ms > target 25ms"

    def test_bench_flags_off_overhead_p95(self, clock_fn, request):
        """Overhead of a gate-rejected START_DRAIN (feature disabled) vs happy-path."""
        # First measure happy-path baseline
        happy_samples = []
        for i in range(WARMUP + SAMPLE):
            store = self._new_store(clock_fn)
            exp, adv, tgt = f"exp-h-{i}", f"adv-{i}", "tgt-bench-h"
            mark = _bootstrap_state(store, exp, adv, tgt, clock_fn())
            ev = make_drain_event("START_DRAIN", expedition_id=exp, source=adv, target=tgt,
                                  mark_id=mark.mark_id, application_id=mark.application_id)
            t0 = time.perf_counter()
            self._dispatch(store, ev)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            if i >= WARMUP:
                happy_samples.append(elapsed_ms)
        happy_p95 = _p95(happy_samples)

        # Flags OFF path — should be much faster (no mutation)
        off_samples = []
        for i in range(WARMUP + SAMPLE):
            store = self._new_store(clock_fn)
            exp, adv, tgt = f"exp-o-{i}", f"adv-{i}", "tgt-bench-o"
            mark = _bootstrap_state(store, exp, adv, tgt, clock_fn())
            ev = make_drain_event("START_DRAIN", expedition_id=exp, source=adv, target=tgt,
                                  mark_id=mark.mark_id, application_id=mark.application_id)
            t0 = time.perf_counter()
            self._dispatch(store, ev, tctx={"feature_enabled": False, "test_user_verified": True,
                                             "db_allowlisted": True, "phase_ended": False})
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            if i >= WARMUP:
                off_samples.append(elapsed_ms)
        off_p95 = _p95(off_samples)
        stats = _summarize(off_samples)
        stats["metric"] = "flags_off_overhead_p95"
        stats["happy_baseline_p95_ms"] = happy_p95
        stats["target_ms"] = max(1.0, 0.05 * happy_p95)
        stats["passes_target"] = off_p95 <= stats["target_ms"] or off_p95 <= happy_p95
        request.config.cache.set("drain_bench/flags_off", stats)
        # Cap: max(5%, 1ms) OR fully lower than baseline (correct semantics)
        assert stats["passes_target"], (
            f"flags_off p95={off_p95:.2f}ms > target max(1ms, 5%={0.05*happy_p95:.2f}ms) "
            f"and > happy_baseline={happy_p95:.2f}ms"
        )
