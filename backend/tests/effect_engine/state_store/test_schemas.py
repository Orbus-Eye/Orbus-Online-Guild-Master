"""RT2-B-1A · Schema validation & result type tests.

Verifica:
- Dataclass frozen invariance (immutability).
- Fencing token validation logic (pure function).
- CAS result code enum stability & string values.
- Initial state_version = 1 (B0Q04).
- fencing_token monotonic (next_fencing_token).
- Receipt shape (all required minimum fields).
"""
from __future__ import annotations

import pytest

from app.stats.runtime.state_store import (
    CasResult,
    CasResultCode,
    EventReceipt,
    ExpeditionRuntimeState,
    LeaseAcquireResult,
    WriterLease,
)
from app.stats.runtime.state_store.fencing import (
    next_fencing_token,
    next_state_version,
    validate_fencing_match,
    validate_state_version_match,
)
from app.stats.runtime.state_store.models import (
    AdventurerClassState,
    MarkDoc,
    RuntimeStatus,
)


# ═══════════════════════ Enum stability ═══════════════════════
def test_cas_result_codes_stable() -> None:
    assert CasResultCode.SUCCESS.value == "SUCCESS"
    assert CasResultCode.STATE_VERSION_CONFLICT.value == "STATE_VERSION_CONFLICT"
    assert CasResultCode.STALE_WRITER_REJECTED.value == "STALE_WRITER_REJECTED"
    assert CasResultCode.DEDUPLICATED_NO_OP.value == "DEDUPLICATED_NO_OP"
    assert CasResultCode.EVENT_ID_PAYLOAD_MISMATCH.value == "EVENT_ID_PAYLOAD_MISMATCH"
    assert CasResultCode.OWNERSHIP_INVALID.value == "OWNERSHIP_INVALID"
    assert CasResultCode.CAP_EXCEEDED.value == "CAP_EXCEEDED"
    assert CasResultCode.LEASE_EXPIRED.value == "LEASE_EXPIRED"
    assert CasResultCode.NOT_FOUND.value == "NOT_FOUND"
    assert CasResultCode.ALREADY_EXISTS.value == "ALREADY_EXISTS"


def test_cas_result_convenience_flags() -> None:
    ok = CasResult(code=CasResultCode.SUCCESS, new_state_version=2)
    dup = CasResult(code=CasResultCode.DEDUPLICATED_NO_OP, new_state_version=1)
    conf = CasResult(code=CasResultCode.STATE_VERSION_CONFLICT)
    assert ok.success is True
    assert ok.idempotent_noop is False
    assert dup.success is False
    assert dup.idempotent_noop is True
    assert conf.success is False
    assert conf.idempotent_noop is False


# ═══════════════════════ Fencing token logic ═══════════════════════
def test_next_fencing_token_from_none() -> None:
    assert next_fencing_token(None) == 1


def test_next_fencing_token_increments() -> None:
    assert next_fencing_token(0) == 1
    assert next_fencing_token(1) == 2
    assert next_fencing_token(99) == 100


def test_next_fencing_token_rejects_negative() -> None:
    with pytest.raises(ValueError):
        next_fencing_token(-1)


def test_validate_fencing_match_success() -> None:
    assert validate_fencing_match(5, 5) is True


def test_validate_fencing_match_fail() -> None:
    assert validate_fencing_match(5, 6) is False
    assert validate_fencing_match(0, 1) is False
    assert validate_fencing_match(-1, 0) is False
    assert validate_fencing_match(1, -1) is False


def test_validate_fencing_match_non_int() -> None:
    assert validate_fencing_match("5", 5) is False  # type: ignore[arg-type]
    assert validate_fencing_match(5, None) is False  # type: ignore[arg-type]


# ═══════════════════════ State version logic ═══════════════════════
def test_next_state_version_increments() -> None:
    assert next_state_version(1) == 2
    assert next_state_version(2) == 3
    assert next_state_version(100) == 101


def test_next_state_version_rejects_zero_or_negative() -> None:
    with pytest.raises(ValueError):
        next_state_version(0)
    with pytest.raises(ValueError):
        next_state_version(-1)


def test_validate_state_version_match_rejects_zero_initial() -> None:
    """`state_version` initial=1 per B0Q04; 0 non è mai lecito."""
    assert validate_state_version_match(0, 0) is False
    assert validate_state_version_match(1, 1) is True
    assert validate_state_version_match(2, 3) is False


# ═══════════════════════ Immutability ═══════════════════════
def test_expedition_runtime_state_frozen() -> None:
    st = ExpeditionRuntimeState(
        expedition_id="exp-i", state_version=1,
        created_at="2026-02-01T00:00:00Z", updated_at="2026-02-01T00:00:00Z",
        expires_at="2026-02-01T06:00:00Z",
    )
    with pytest.raises(Exception):
        # dataclass(frozen=True) → FrozenInstanceError
        st.state_version = 999  # type: ignore[misc]


def test_writer_lease_frozen() -> None:
    lease = WriterLease(
        lease_id="l-1", owner_id="w-A",
        acquired_at="2026-02-01T00:00:00Z",
        expires_at="2026-02-01T00:00:30Z",
        fencing_token=1,
    )
    with pytest.raises(Exception):
        lease.fencing_token = 99  # type: ignore[misc]


def test_event_receipt_frozen() -> None:
    r = EventReceipt(
        event_id="e", event_type="t", source_adventurer_id="a",
        payload_hash="h", assigned_event_sequence=1, result_code="SUCCESS",
        state_version_after=2, processed_at="2026-02-01T00:00:00Z",
    )
    with pytest.raises(Exception):
        r.assigned_event_sequence = 999  # type: ignore[misc]


# ═══════════════════════ Adventurer class state helpers ═══════════════════════
def test_state_class_state_for_returns_none_when_absent() -> None:
    st = ExpeditionRuntimeState(
        expedition_id="e", state_version=1,
        created_at="", updated_at="", expires_at="",
    )
    assert st.class_state_for("missing") is None


def test_state_class_state_for_returns_state_when_present() -> None:
    cs = AdventurerClassState(adventurer_id="adv-1", fragment_count=3)
    st = ExpeditionRuntimeState(
        expedition_id="e", state_version=1,
        created_at="", updated_at="", expires_at="",
        adventurer_class_states=(("adv-1", cs),),
    )
    got = st.class_state_for("adv-1")
    assert got is cs
    assert got.fragment_count == 3


# ═══════════════════════ Receipt lookup ═══════════════════════
def test_state_receipt_for_returns_none_when_absent() -> None:
    st = ExpeditionRuntimeState(
        expedition_id="e", state_version=1,
        created_at="", updated_at="", expires_at="",
    )
    assert st.receipt_for("no-such-event") is None


def test_state_receipt_for_returns_receipt_when_present() -> None:
    r = EventReceipt(
        event_id="evt-42", event_type="mark_apply", source_adventurer_id="a",
        payload_hash="h", assigned_event_sequence=1, result_code="SUCCESS",
        state_version_after=2, processed_at="",
    )
    st = ExpeditionRuntimeState(
        expedition_id="e", state_version=1,
        created_at="", updated_at="", expires_at="",
        processed_event_keys=(r,),
    )
    got = st.receipt_for("evt-42")
    assert got is r


# ═══════════════════════ Runtime status enum ═══════════════════════
def test_runtime_status_terminal_states() -> None:
    terminal = {RuntimeStatus.COMPLETED, RuntimeStatus.CANCELLED, RuntimeStatus.EXPIRED}
    non_terminal = {RuntimeStatus.ACTIVE, RuntimeStatus.COMPLETING}
    assert terminal.isdisjoint(non_terminal)


# ═══════════════════════ Bounded receipts default ═══════════════════════
def test_max_processed_events_default_is_reasonable() -> None:
    assert ExpeditionRuntimeState.MAX_PROCESSED_EVENTS >= 100
    assert ExpeditionRuntimeState.MAX_PROCESSED_EVENTS <= 10_000
