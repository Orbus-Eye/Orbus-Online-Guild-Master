"""RT2-B-2B-2-1-V1 · Mongo adapter DrainDoc rehydration (pure-unit, no Mongo).

PM Message 182 §3 (STEP 3) verbatim requirement:
- Backward compatibility (legacy DrainDoc without RT2-B-2B-2-1 fields)
- Field defaults (rehydration when fields missing)
- Serialization/rehydration symmetry (round-trip)
- Assenza perdita dati Drain
- Assenza mutazioni durante sola lettura

Testa direttamente `_document_to_state` (funzione pura, non richiede Motor/Mongo).
"""
from __future__ import annotations

import copy

import pytest

from app.stats.runtime.state_store.models import (
    AdventurerClassState,
    DrainDoc,
    DrainStatus,
    ExpeditionRuntimeState,
    RuntimeStatus,
)
from app.stats.runtime.state_store.mongo_adapter import (
    _document_to_state,
    _serialize_class_states,
)


# ═══════════════════════ Helpers ═══════════════════════
def _base_doc(**overrides):
    """Minimum-valid Mongo document shape for _document_to_state()."""
    doc = {
        "_id": "exp-rehyd-1",
        "state_version": 1,
        "created_at": "2026-07-27T20:00:00Z",
        "updated_at": "2026-07-27T20:00:00Z",
        "expires_at": "2026-07-27T21:00:00Z",
        "runtime_status": "active",
        "last_event_sequence": 0,
        "fencing_token": 0,
        "adventurer_class_states": {},
        "processed_event_keys": [],
    }
    doc.update(overrides)
    return doc


def _drain_dict_full():
    """Fully-populated Drain dict (all 13 fields present)."""
    return {
        "drain_execution_id": "drn-abc-11111111-2222-4333-8444-555555555555",
        "source_adventurer_id": "adv-1",
        "target_id": "tg-1",
        "required_mark_application_id": "app-full-001",
        "started_at": "2026-07-27T20:00:00Z",
        "completed_at": "2026-07-27T20:00:05Z",
        "runtime_status": "resolved",
        "resolution_version": 2,
        "reward_resolved": True,
        "mark_id": "mrk-full-001",
        "cancelled_at": None,
        "cancellation_reason": None,
        "drain_version": 2,
    }


def _drain_dict_legacy():
    """Legacy Drain dict pre-RT2-B-2B-2-1 (no mark_id/cancelled_at/cancellation_reason/drain_version)."""
    return {
        "drain_execution_id": "drn-legacy-11111111-2222-4333-8444-555555555555",
        "source_adventurer_id": "adv-legacy",
        "target_id": "tg-legacy",
        "required_mark_application_id": "app-legacy-001",
        "started_at": "2026-07-27T20:00:00Z",
        # completed_at absent
        "runtime_status": "in_progress",
        "resolution_version": 1,
        "reward_resolved": False,
        # RT2-B-2B-2-1 new fields ABSENT: mark_id, cancelled_at, cancellation_reason, drain_version
    }


# ═══════════════════════ 1 · Full DrainDoc rehydration ═══════════════════════
def test_rehydration_full_drain_produces_typed_DrainDoc():
    doc = _base_doc(adventurer_class_states={
        "adv-1": {
            "adventurer_id": "adv-1",
            "active_marks": [],
            "active_drain_executions": [_drain_dict_full()],
            "fragment_count": 0,
            "focus_bonus_usage": [],
            "class_state_version": 1,
        }
    })
    state = _document_to_state(doc)
    assert isinstance(state, ExpeditionRuntimeState)
    assert len(state.adventurer_class_states) == 1
    aid, cs = state.adventurer_class_states[0]
    assert aid == "adv-1"
    assert len(cs.active_drain_executions) == 1
    d = cs.active_drain_executions[0]
    # Type check: must be DrainDoc, NOT dict
    assert isinstance(d, DrainDoc)
    # All 13 fields correctly reidrated
    assert d.drain_execution_id == "drn-abc-11111111-2222-4333-8444-555555555555"
    assert d.source_adventurer_id == "adv-1"
    assert d.target_id == "tg-1"
    assert d.required_mark_application_id == "app-full-001"
    assert d.started_at == "2026-07-27T20:00:00Z"
    assert d.completed_at == "2026-07-27T20:00:05Z"
    assert d.runtime_status is DrainStatus.RESOLVED  # enum coerced from string
    assert d.resolution_version == 2
    assert d.reward_resolved is True
    assert d.mark_id == "mrk-full-001"
    assert d.cancelled_at is None
    assert d.cancellation_reason is None
    assert d.drain_version == 2


# ═══════════════════════ 2 · Backward compat (legacy doc) ═══════════════════════
def test_rehydration_legacy_drain_applies_defaults_for_missing_rt2b2b21_fields():
    """Legacy Mongo document (pre-RT2-B-2B-2-1) must rehydrate with sensible defaults, no crash."""
    doc = _base_doc(adventurer_class_states={
        "adv-legacy": {
            "adventurer_id": "adv-legacy",
            "active_marks": [],
            "active_drain_executions": [_drain_dict_legacy()],
            "fragment_count": 0,
            "focus_bonus_usage": [],
            "class_state_version": 1,
        }
    })
    state = _document_to_state(doc)
    d = state.adventurer_class_states[0][1].active_drain_executions[0]
    assert isinstance(d, DrainDoc)
    # RT1 legacy fields preserved
    assert d.drain_execution_id == "drn-legacy-11111111-2222-4333-8444-555555555555"
    assert d.source_adventurer_id == "adv-legacy"
    assert d.required_mark_application_id == "app-legacy-001"
    assert d.runtime_status is DrainStatus.IN_PROGRESS
    assert d.resolution_version == 1
    assert d.reward_resolved is False
    # RT2-B-2B-2-1 new fields at defaults
    assert d.completed_at is None  # missing → default None
    assert d.mark_id == ""  # missing → default ""
    assert d.cancelled_at is None  # missing → default None
    assert d.cancellation_reason is None  # missing → default None
    assert d.drain_version == 1  # missing → default 1


# ═══════════════════════ 3 · Empty drains list ═══════════════════════
def test_rehydration_empty_active_drains_produces_empty_tuple():
    doc = _base_doc(adventurer_class_states={
        "adv-x": {
            "adventurer_id": "adv-x",
            "active_marks": [],
            "active_drain_executions": [],
            "fragment_count": 0,
            "focus_bonus_usage": [],
            "class_state_version": 1,
        }
    })
    state = _document_to_state(doc)
    cs = state.adventurer_class_states[0][1]
    assert cs.active_drain_executions == ()
    assert isinstance(cs.active_drain_executions, tuple)


# ═══════════════════════ 4 · Multiple drains + mixed states ═══════════════════════
def test_rehydration_multiple_drains_preserves_order_and_types():
    d_active = _drain_dict_full()
    d_active["drain_execution_id"] = "drn-active-1"
    d_active["runtime_status"] = "in_progress"
    d_active["completed_at"] = None
    d_active["reward_resolved"] = False

    d_cancelled = _drain_dict_full()
    d_cancelled["drain_execution_id"] = "drn-cancelled-2"
    d_cancelled["runtime_status"] = "cancelled"
    d_cancelled["cancelled_at"] = "2026-07-27T20:00:03Z"
    d_cancelled["cancellation_reason"] = "EXPLICIT_SERVER_CANCEL"

    doc = _base_doc(adventurer_class_states={
        "adv-multi": {
            "adventurer_id": "adv-multi",
            "active_marks": [],
            "active_drain_executions": [d_active, d_cancelled],
            "fragment_count": 0,
            "focus_bonus_usage": [],
            "class_state_version": 1,
        }
    })
    state = _document_to_state(doc)
    drains = state.adventurer_class_states[0][1].active_drain_executions
    assert len(drains) == 2
    # Order preserved
    assert drains[0].drain_execution_id == "drn-active-1"
    assert drains[0].runtime_status is DrainStatus.IN_PROGRESS
    assert drains[0].reward_resolved is False
    assert drains[1].drain_execution_id == "drn-cancelled-2"
    assert drains[1].runtime_status is DrainStatus.CANCELLED
    assert drains[1].cancelled_at == "2026-07-27T20:00:03Z"
    assert drains[1].cancellation_reason == "EXPLICIT_SERVER_CANCEL"


# ═══════════════════════ 5 · Status enum coercion (all 4 status values) ═══════════════════════
@pytest.mark.parametrize("status_str,expected_enum", [
    ("in_progress", DrainStatus.IN_PROGRESS),
    ("resolved", DrainStatus.RESOLVED),
    ("cancelled", DrainStatus.CANCELLED),
    ("expired", DrainStatus.EXPIRED),
])
def test_rehydration_runtime_status_string_coerced_to_enum(status_str, expected_enum):
    d = _drain_dict_full()
    d["runtime_status"] = status_str
    doc = _base_doc(adventurer_class_states={
        "adv-s": {
            "adventurer_id": "adv-s",
            "active_marks": [],
            "active_drain_executions": [d],
            "fragment_count": 0,
            "focus_bonus_usage": [],
            "class_state_version": 1,
        }
    })
    state = _document_to_state(doc)
    drain = state.adventurer_class_states[0][1].active_drain_executions[0]
    assert drain.runtime_status is expected_enum


# ═══════════════════════ 6 · Round-trip symmetry (state → dict → state) ═══════════════════════
def test_round_trip_symmetry_full_drain():
    """Serialize typed state to dict, rehydrate, compare — must be byte-equal on Drain data."""
    original = DrainDoc(
        drain_execution_id="drn-rt-11111111-2222-4333-8444-555555555555",
        source_adventurer_id="adv-rt",
        target_id="tg-rt",
        required_mark_application_id="app-rt-001",
        started_at="2026-07-27T20:00:00Z",
        completed_at="2026-07-27T20:00:05Z",
        runtime_status=DrainStatus.RESOLVED,
        resolution_version=2,
        reward_resolved=True,
        mark_id="mrk-rt-001",
        cancelled_at=None,
        cancellation_reason=None,
        drain_version=2,
    )
    cs_original = AdventurerClassState(
        adventurer_id="adv-rt",
        active_drain_executions=(original,),
        class_state_version=1,
    )
    # State → dict-of-dicts (via helper)
    serialized = _serialize_class_states((("adv-rt", cs_original),))
    # Note: dataclasses.asdict() preserves tuple type; _document_to_state iterates
    # either list or tuple, both work.
    # dict → state
    doc = _base_doc(adventurer_class_states=serialized)
    rehydrated = _document_to_state(doc)
    d_rt = rehydrated.adventurer_class_states[0][1].active_drain_executions[0]
    # Byte-equal on all DrainDoc fields (frozen dataclass supports __eq__)
    assert d_rt == original


def test_round_trip_symmetry_legacy_drain_defaults_preserved():
    """A DrainDoc built with all defaults (RT1 legacy shape) must round-trip identically."""
    original = DrainDoc(
        drain_execution_id="drn-legrt-11111111-2222-4333-8444-555555555555",
        source_adventurer_id="adv-legrt",
        target_id="tg-legrt",
        required_mark_application_id="app-legrt",
        started_at="2026-07-27T20:00:00Z",
        # All other fields default
    )
    cs_original = AdventurerClassState(
        adventurer_id="adv-legrt",
        active_drain_executions=(original,),
        class_state_version=1,
    )
    serialized = _serialize_class_states((("adv-legrt", cs_original),))
    doc = _base_doc(adventurer_class_states=serialized)
    rehydrated = _document_to_state(doc)
    d_rt = rehydrated.adventurer_class_states[0][1].active_drain_executions[0]
    assert d_rt == original
    # Explicit default-preservation asserts
    assert d_rt.completed_at is None
    assert d_rt.runtime_status is DrainStatus.IN_PROGRESS
    assert d_rt.resolution_version == 1
    assert d_rt.reward_resolved is False
    assert d_rt.mark_id == ""
    assert d_rt.cancelled_at is None
    assert d_rt.cancellation_reason is None
    assert d_rt.drain_version == 1


# ═══════════════════════ 7 · Zero mutation on read (function purity) ═══════════════════════
def test_document_to_state_does_not_mutate_input_doc():
    """`_document_to_state` must be pure: no side-effects on input dict."""
    doc = _base_doc(adventurer_class_states={
        "adv-pure": {
            "adventurer_id": "adv-pure",
            "active_marks": [],
            "active_drain_executions": [_drain_dict_full(), _drain_dict_legacy()],
            "fragment_count": 0,
            "focus_bonus_usage": [],
            "class_state_version": 1,
        }
    })
    doc_snapshot = copy.deepcopy(doc)
    _document_to_state(doc)  # discard result
    assert doc == doc_snapshot  # dict must be byte-equal post-call
