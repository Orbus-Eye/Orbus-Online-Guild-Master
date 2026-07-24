"""RT2-B-2B-1 · Mark transitions tests (items 1-8 · PM §15).

Pattern sync + asyncio.run().
"""
from __future__ import annotations

from app.stats.runtime.transitions.dispatcher import ClassTransitionDispatcher
from app.stats.runtime.transitions.models import (
    ClassEventType,
    TransitionResultCode,
)
from tests.effect_engine.transitions.conftest import (
    make_event,
    run,
    trusted_context,
)


def _dispatch(store, event):
    disp = ClassTransitionDispatcher(store=store, worker_id="w-test", now_fn=store._clock)
    return run(disp.dispatch(event, trusted_context=trusted_context()))


# ─── Item 1: Mark apply success ─────────────────────────────────
def test_01_mark_apply_success(initialized_state, adventurer_id, target_id):
    store, exp_id = initialized_state
    event = make_event(
        ClassEventType.APPLY_MARK.value,
        expedition_id=exp_id,
        source_adventurer_id=adventurer_id,
        target_id=target_id,
    )
    out = _dispatch(store, event)
    assert out.result.code is TransitionResultCode.SUCCESS
    assert out.result.mark_id
    assert out.result.mark_application_id
    assert out.result.active_marks_count_after == 1
    assert out.lease_acquired is True


# ─── Item 2: Mark duplicate source-target rejection ─────────────
def test_02_mark_duplicate_pair_rejected(initialized_state, adventurer_id, target_id):
    store, exp_id = initialized_state
    e1 = make_event(ClassEventType.APPLY_MARK.value, expedition_id=exp_id,
                    source_adventurer_id=adventurer_id, target_id=target_id)
    _dispatch(store, e1)
    e2 = make_event(ClassEventType.APPLY_MARK.value, expedition_id=exp_id,
                    source_adventurer_id=adventurer_id, target_id=target_id)
    out = _dispatch(store, e2)
    assert out.result.code is TransitionResultCode.MARK_ALREADY_ACTIVE_FOR_PAIR


# ─── Item 3: Mark cap rejection (6th Mark) ──────────────────────
def test_03_mark_cap_exceeded_rejected(initialized_state, adventurer_id):
    store, exp_id = initialized_state
    for i in range(5):
        e = make_event(ClassEventType.APPLY_MARK.value, expedition_id=exp_id,
                       source_adventurer_id=adventurer_id, target_id=f"target-{i}")
        r = _dispatch(store, e)
        assert r.result.code is TransitionResultCode.SUCCESS, f"apply {i} failed: {r.result.code}"
    e6 = make_event(ClassEventType.APPLY_MARK.value, expedition_id=exp_id,
                    source_adventurer_id=adventurer_id, target_id="target-6")
    out = _dispatch(store, e6)
    assert out.result.code is TransitionResultCode.MARK_CAP_EXCEEDED
    assert out.result.active_marks_count_after == 5


# ─── Item 4: Mark refresh success ───────────────────────────────
def test_04_mark_refresh_success(initialized_state, adventurer_id, target_id, clock_fn):
    store, exp_id = initialized_state
    e = make_event(ClassEventType.APPLY_MARK.value, expedition_id=exp_id,
                   source_adventurer_id=adventurer_id, target_id=target_id)
    apply_out = _dispatch(store, e)
    assert apply_out.result.code is TransitionResultCode.SUCCESS
    original_app_id = apply_out.result.mark_application_id
    clock_fn.advance(3)
    refresh_e = make_event(ClassEventType.REFRESH_MARK.value, expedition_id=exp_id,
                           source_adventurer_id=adventurer_id, target_id=target_id)
    r = _dispatch(store, refresh_e)
    assert r.result.code is TransitionResultCode.SUCCESS
    assert r.result.mark_application_id == original_app_id


# ─── Item 5: Expired Mark refresh rejection ─────────────────────
def test_05_expired_mark_refresh_rejected(initialized_state, adventurer_id, target_id, clock_fn):
    store, exp_id = initialized_state
    e = make_event(ClassEventType.APPLY_MARK.value, expedition_id=exp_id,
                   source_adventurer_id=adventurer_id, target_id=target_id)
    _dispatch(store, e)
    clock_fn.advance(15)
    refresh_e = make_event(ClassEventType.REFRESH_MARK.value, expedition_id=exp_id,
                           source_adventurer_id=adventurer_id, target_id=target_id)
    out = _dispatch(store, refresh_e)
    assert out.result.code is TransitionResultCode.MARK_EXPIRED


# ─── Item 6: Lazy expiration ─────────────────────────────────────
def test_06_lazy_expiration(initialized_state, adventurer_id, target_id, clock_fn):
    store, exp_id = initialized_state
    e = make_event(ClassEventType.APPLY_MARK.value, expedition_id=exp_id,
                   source_adventurer_id=adventurer_id, target_id=target_id)
    _dispatch(store, e)
    clock_fn.advance(15)
    lazy_e = make_event(ClassEventType.LAZY_MARK_EXPIRATION.value, expedition_id=exp_id,
                        source_adventurer_id=adventurer_id)
    out = _dispatch(store, lazy_e)
    assert out.result.code is TransitionResultCode.SUCCESS
    assert out.result.active_marks_count_after == 0


# ─── Item 7: Opportunistic cleanup ──────────────────────────────
def test_07_opportunistic_cleanup(initialized_state, adventurer_id, clock_fn):
    store, exp_id = initialized_state
    for i in range(3):
        e = make_event(ClassEventType.APPLY_MARK.value, expedition_id=exp_id,
                       source_adventurer_id=adventurer_id, target_id=f"target-{i}")
        _dispatch(store, e)
    clock_fn.advance(15)
    cleanup_e = make_event(ClassEventType.OPPORTUNISTIC_MARK_CLEANUP.value,
                           expedition_id=exp_id, source_adventurer_id=adventurer_id)
    out = _dispatch(store, cleanup_e)
    assert out.result.code is TransitionResultCode.SUCCESS
    assert out.result.active_marks_count_after == 0


# ─── Item 8: Multi-CdV ownership isolation ──────────────────────
def test_08_multi_cdv_ownership_isolation(initialized_state, target_id):
    store, exp_id = initialized_state
    e1 = make_event(ClassEventType.APPLY_MARK.value, expedition_id=exp_id,
                    source_adventurer_id="adv-A", target_id=target_id)
    r1 = _dispatch(store, e1)
    assert r1.result.code is TransitionResultCode.SUCCESS
    e2 = make_event(ClassEventType.APPLY_MARK.value, expedition_id=exp_id,
                    source_adventurer_id="adv-B", target_id=target_id)
    r2 = _dispatch(store, e2)
    assert r2.result.code is TransitionResultCode.SUCCESS
    read = run(store.get_state(exp_id))
    assert read.state is not None
    cs_a = read.state.class_state_for("adv-A")
    cs_b = read.state.class_state_for("adv-B")
    assert cs_a is not None and cs_b is not None
    assert len(cs_a.active_marks) == 1
    assert len(cs_b.active_marks) == 1
    refresh = make_event(ClassEventType.REFRESH_MARK.value, expedition_id=exp_id,
                         source_adventurer_id="adv-A", target_id=target_id)
    out = _dispatch(store, refresh)
    assert out.result.code is TransitionResultCode.SUCCESS
