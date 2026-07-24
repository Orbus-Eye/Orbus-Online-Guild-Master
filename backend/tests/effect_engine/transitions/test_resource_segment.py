"""RT2-B-2B-1 · Resource segment + phase reset tests (items 16-22)."""
from __future__ import annotations

from app.stats.runtime.transitions.dispatcher import ClassTransitionDispatcher
from app.stats.runtime.transitions.models import (
    ClassEventType,
    TransitionResultCode,
)
from tests.effect_engine.transitions.conftest import (
    make_event,
    make_trusted_receipt,
    run,
    trusted_context,
)


def _dispatch(store, event, *, ctx_override: dict | None = None):
    disp = ClassTransitionDispatcher(store=store, worker_id="w-test", now_fn=store._clock)
    ctx = trusted_context()
    if ctx_override:
        ctx.update(ctx_override)
    return run(disp.dispatch(event, trusted_context=ctx))


def _seed_fragments(store, exp_id, adventurer_id, target_id, count):
    for _ in range(count):
        receipt = make_trusted_receipt(source_adventurer_id=adventurer_id, target_id=target_id, expedition_id=exp_id)
        ev = make_event(ClassEventType.GAIN_FRAGMENT.value, expedition_id=exp_id,
                        source_adventurer_id=adventurer_id, amount=1, trusted_drain_receipt=receipt)
        r = _dispatch(store, ev)
        assert r.result.code is TransitionResultCode.SUCCESS


def test_16_phase_reset(initialized_state, adventurer_id, target_id):
    store, exp_id = initialized_state
    _seed_fragments(store, exp_id, adventurer_id, target_id, 3)
    reset_ev = make_event(ClassEventType.PHASE_END.value, expedition_id=exp_id,
                          source_adventurer_id=adventurer_id, reason_code="PHASE_ENDED")
    out = _dispatch(store, reset_ev)
    assert out.result.code is TransitionResultCode.SUCCESS
    assert out.result.fragment_count_after == 0
    assert out.result.resource_segment_id is None


def test_17_expedition_terminal_reset(initialized_state, adventurer_id, target_id):
    store, exp_id = initialized_state
    _seed_fragments(store, exp_id, adventurer_id, target_id, 2)
    ev = make_event(ClassEventType.EXPEDITION_TERMINAL.value, expedition_id=exp_id,
                    source_adventurer_id=adventurer_id, reason_code="EXPEDITION_TERMINAL")
    out = _dispatch(store, ev)
    assert out.result.code is TransitionResultCode.SUCCESS
    assert out.result.fragment_count_after == 0


def test_18_segment_opens_on_first_gain(initialized_state, adventurer_id, target_id):
    store, exp_id = initialized_state
    receipt = make_trusted_receipt(source_adventurer_id=adventurer_id, target_id=target_id, expedition_id=exp_id)
    ev = make_event(ClassEventType.GAIN_FRAGMENT.value, expedition_id=exp_id,
                    source_adventurer_id=adventurer_id, amount=1, trusted_drain_receipt=receipt)
    out = _dispatch(store, ev)
    assert out.result.code is TransitionResultCode.SUCCESS
    assert out.result.resource_segment_id is not None
    seg_id = out.result.resource_segment_id
    receipt2 = make_trusted_receipt(source_adventurer_id=adventurer_id, target_id=target_id, expedition_id=exp_id)
    ev2 = make_event(ClassEventType.GAIN_FRAGMENT.value, expedition_id=exp_id,
                     source_adventurer_id=adventurer_id, amount=1, trusted_drain_receipt=receipt2)
    out2 = _dispatch(store, ev2)
    assert out2.result.resource_segment_id == seg_id


def test_19_partial_spend_preserves_segment(initialized_state, adventurer_id, target_id):
    store, exp_id = initialized_state
    _seed_fragments(store, exp_id, adventurer_id, target_id, 4)
    read = run(store.get_state(exp_id))
    seg_before = read.state.class_state_for(adventurer_id).resource_segment_id
    spend = make_event(ClassEventType.SPEND_FRAGMENT.value, expedition_id=exp_id,
                       source_adventurer_id=adventurer_id, amount=2)
    out = _dispatch(store, spend)
    assert out.result.code is TransitionResultCode.SUCCESS
    assert out.result.fragment_count_after == 2
    assert out.result.resource_segment_id == seg_before


def test_20_zero_balance_closes_segment(initialized_state, adventurer_id, target_id):
    store, exp_id = initialized_state
    _seed_fragments(store, exp_id, adventurer_id, target_id, 2)
    spend = make_event(ClassEventType.SPEND_FRAGMENT.value, expedition_id=exp_id,
                       source_adventurer_id=adventurer_id, amount=2)
    out = _dispatch(store, spend)
    assert out.result.code is TransitionResultCode.SUCCESS
    assert out.result.fragment_count_after == 0
    assert out.result.resource_segment_id is None


def test_21_explicit_segment_close(initialized_state, adventurer_id, target_id):
    store, exp_id = initialized_state
    _seed_fragments(store, exp_id, adventurer_id, target_id, 3)
    close = make_event(ClassEventType.CLOSE_RESOURCE_SEGMENT.value, expedition_id=exp_id,
                       source_adventurer_id=adventurer_id, reason_code="EXPLICIT_SERVER_CANCEL")
    out = _dispatch(store, close)
    assert out.result.code is TransitionResultCode.SUCCESS
    assert out.result.fragment_count_after == 0
    assert out.result.resource_segment_id is None


def test_22_focus_bonus_cap(initialized_state, adventurer_id, target_id):
    store, exp_id = initialized_state
    _seed_fragments(store, exp_id, adventurer_id, target_id, 5)
    for i in range(2):
        spend = make_event(ClassEventType.SPEND_FRAGMENT.value, expedition_id=exp_id,
                           source_adventurer_id=adventurer_id, amount=1,
                           reason_code="USES_FOCUS_BONUS")
        r = _dispatch(store, spend)
        assert r.result.code is TransitionResultCode.SUCCESS
    spend3 = make_event(ClassEventType.SPEND_FRAGMENT.value, expedition_id=exp_id,
                        source_adventurer_id=adventurer_id, amount=1,
                        reason_code="USES_FOCUS_BONUS")
    out = _dispatch(store, spend3)
    assert out.result.code is TransitionResultCode.FOCUS_BONUS_CAP_EXCEEDED
