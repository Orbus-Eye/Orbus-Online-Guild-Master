"""RT2-B-2B-1 · Fragment transitions tests (items 9-15 · PM §15)."""
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


def _dispatch(store, event):
    disp = ClassTransitionDispatcher(store=store, worker_id="w-test", now_fn=store._clock)
    return run(disp.dispatch(event, trusted_context=trusted_context()))


def test_09_fragment_gain_with_trusted_receipt(initialized_state, adventurer_id, target_id):
    store, exp_id = initialized_state
    receipt = make_trusted_receipt(source_adventurer_id=adventurer_id, target_id=target_id, expedition_id=exp_id)
    ev = make_event(ClassEventType.GAIN_FRAGMENT.value, expedition_id=exp_id,
                    source_adventurer_id=adventurer_id, amount=2, trusted_drain_receipt=receipt)
    out = _dispatch(store, ev)
    assert out.result.code is TransitionResultCode.SUCCESS
    assert out.result.fragment_count_after == 2
    assert out.result.resource_segment_id is not None


def test_10_fragment_gain_untrusted_rejected(initialized_state, adventurer_id):
    store, exp_id = initialized_state
    ev = make_event(ClassEventType.GAIN_FRAGMENT.value, expedition_id=exp_id,
                    source_adventurer_id=adventurer_id, amount=1, trusted_drain_receipt=None)
    out = _dispatch(store, ev)
    assert out.result.code is TransitionResultCode.FRAGMENT_GAIN_UNAUTHORIZED
    assert out.result.reason_code == "NO_TRUSTED_DRAIN_RECEIPT"


def test_11_fragment_cap(initialized_state, adventurer_id, target_id):
    store, exp_id = initialized_state
    for i in range(5):
        receipt = make_trusted_receipt(source_adventurer_id=adventurer_id, target_id=target_id, expedition_id=exp_id)
        ev = make_event(ClassEventType.GAIN_FRAGMENT.value, expedition_id=exp_id,
                        source_adventurer_id=adventurer_id, amount=1, trusted_drain_receipt=receipt)
        r = _dispatch(store, ev)
        assert r.result.code is TransitionResultCode.SUCCESS
    receipt = make_trusted_receipt(source_adventurer_id=adventurer_id, target_id=target_id, expedition_id=exp_id)
    ev6 = make_event(ClassEventType.GAIN_FRAGMENT.value, expedition_id=exp_id,
                     source_adventurer_id=adventurer_id, amount=1, trusted_drain_receipt=receipt)
    out = _dispatch(store, ev6)
    assert out.result.code is TransitionResultCode.FRAGMENT_OVERFLOW_DISCARDED
    assert out.result.fragment_count_after == 5


def test_12_fragment_overflow_discard(initialized_state, adventurer_id, target_id):
    store, exp_id = initialized_state
    for _ in range(4):
        receipt = make_trusted_receipt(source_adventurer_id=adventurer_id, target_id=target_id, expedition_id=exp_id)
        ev = make_event(ClassEventType.GAIN_FRAGMENT.value, expedition_id=exp_id,
                        source_adventurer_id=adventurer_id, amount=1, trusted_drain_receipt=receipt)
        _dispatch(store, ev)
    receipt = make_trusted_receipt(source_adventurer_id=adventurer_id, target_id=target_id, expedition_id=exp_id)
    ev = make_event(ClassEventType.GAIN_FRAGMENT.value, expedition_id=exp_id,
                    source_adventurer_id=adventurer_id, amount=3, trusted_drain_receipt=receipt)
    out = _dispatch(store, ev)
    assert out.result.code is TransitionResultCode.FRAGMENT_OVERFLOW_DISCARDED
    assert out.result.fragment_count_after == 5
    assert out.result.overflow_discarded == 2


def test_13_fragment_spend_success(initialized_state, adventurer_id, target_id):
    store, exp_id = initialized_state
    receipt = make_trusted_receipt(source_adventurer_id=adventurer_id, target_id=target_id, expedition_id=exp_id)
    gain = make_event(ClassEventType.GAIN_FRAGMENT.value, expedition_id=exp_id,
                      source_adventurer_id=adventurer_id, amount=3, trusted_drain_receipt=receipt)
    _dispatch(store, gain)
    spend = make_event(ClassEventType.SPEND_FRAGMENT.value, expedition_id=exp_id,
                       source_adventurer_id=adventurer_id, amount=2)
    out = _dispatch(store, spend)
    assert out.result.code is TransitionResultCode.SUCCESS
    assert out.result.fragment_count_after == 1
    assert out.result.resource_segment_id is not None


def test_14_fragment_spend_insufficient(initialized_state, adventurer_id, target_id):
    store, exp_id = initialized_state
    receipt = make_trusted_receipt(source_adventurer_id=adventurer_id, target_id=target_id, expedition_id=exp_id)
    gain = make_event(ClassEventType.GAIN_FRAGMENT.value, expedition_id=exp_id,
                      source_adventurer_id=adventurer_id, amount=2, trusted_drain_receipt=receipt)
    _dispatch(store, gain)
    spend = make_event(ClassEventType.SPEND_FRAGMENT.value, expedition_id=exp_id,
                       source_adventurer_id=adventurer_id, amount=3)
    out = _dispatch(store, spend)
    assert out.result.code is TransitionResultCode.FRAGMENT_INSUFFICIENT


def test_15_fragment_spend_negative_zero_rejected(initialized_state, adventurer_id):
    store, exp_id = initialized_state
    for amount in (0, -1, 6):
        spend = make_event(ClassEventType.SPEND_FRAGMENT.value, expedition_id=exp_id,
                           source_adventurer_id=adventurer_id, amount=amount)
        out = _dispatch(store, spend)
        assert out.result.code is TransitionResultCode.FRAGMENT_INVALID_AMOUNT, (
            f"amount={amount} accepted: {out.result.code}"
        )
