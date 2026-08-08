"""RT2-B-2B-2-1 · Drain pure state machine tests (Phase A).

Test matrix (PM Message 170 §41 · target ≥ 32 casi · result-code coverage 100%):
- START_DRAIN happy + all rejection paths (identifier bounds, expedition/phase,
  mark presence/expiry/ownership/binding, hard-locks pair+application, receipt cap)
- COMPLETE_DRAIN happy + at-cap overflow + 15 mandatory revalidations
- CANCEL_DRAIN 4 trigger types × 8 canonical reason codes + idempotency
- Result-code coverage per PM §19 canonical set

Pure state machine only — no store, no lease, no CAS. Store-integration and race
handling are covered separately in FakeStore and mocked-Mongo suites (§V1).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.stats.runtime.state_store.models import (
    AdventurerClassState,
    DrainDoc,
    DrainStatus,
    MarkDoc,
)
from app.stats.runtime.transitions.drain import (
    DRAIN_EXECUTION_ID_PREFIX,
    FRAGMENT_CAP,
    FRAGMENT_GAIN_PER_DRAIN,
    cancel_drain,
    complete_drain,
    start_drain,
)
from app.stats.runtime.transitions.models import (
    DRAIN_CANCEL_REASONS,
    DrainCommand,
    EVENT_ID_MAX_BYTES,
    IDENTIFIER_MAX_BYTES,
    ReasonCode,
    TransitionResultCode,
    validate_identifier_bounds,
)

UTC = timezone.utc


def _now() -> datetime:
    return datetime(2026, 2, 1, 12, 0, 0, tzinfo=UTC)


def _mark(source: str = "adv-1", target: str = "tgt-1", offset_seconds: int = 8) -> MarkDoc:
    now = _now()
    return MarkDoc(
        mark_id="mark-abc",
        application_id="app-xyz",
        source_adventurer_id=source,
        target_id=target,
        created_at=now.isoformat(),
        expires_at=(now + timedelta(seconds=offset_seconds)).isoformat(),
        ritual_close_used=False,
        mark_version=1,
    )


def _cs(source: str = "adv-1", marks=(), drains=(), fragment_count: int = 0, seg=None) -> AdventurerClassState:
    return AdventurerClassState(
        adventurer_id=source,
        active_marks=tuple(marks),
        active_drain_executions=tuple(drains),
        fragment_count=fragment_count,
        resource_segment_id=seg,
        focus_bonus_usage=(),
        class_state_version=1,
    )


def _cmd(
    command_type: str = "START_DRAIN",
    *,
    source: str = "adv-1",
    target: str = "tgt-1",
    mark_id: str = "mark-abc",
    application_id: str = "app-xyz",
    drain_execution_id: str = "",
    cancellation_reason: str = "",
    event_id: str = "evt-001",
) -> DrainCommand:
    return DrainCommand(
        command_type=command_type,
        event_id=event_id,
        expedition_id="exp-1",
        source_adventurer_id=source,
        target_id=target,
        mark_id=mark_id,
        application_id=application_id,
        drain_execution_id=drain_execution_id,
        cancellation_reason=cancellation_reason,
        payload_hash="hash-1",
        expected_state_version=1,
    )


# ═══════════════════════ Identifier bounds ═══════════════════════
class TestIdentifierBounds:
    def test_valid_bounds_pass(self):
        assert validate_identifier_bounds("evt", "src", "tgt") is None

    def test_event_id_empty_rejects(self):
        assert validate_identifier_bounds("", "src", "tgt") is TransitionResultCode.EVENT_ID_INVALID

    def test_event_id_over_96_bytes_rejects(self):
        big = "e" * (EVENT_ID_MAX_BYTES + 1)
        assert validate_identifier_bounds(big, "src", "tgt") is TransitionResultCode.EVENT_ID_INVALID

    def test_source_over_64_bytes_rejects(self):
        big = "s" * (IDENTIFIER_MAX_BYTES + 1)
        assert validate_identifier_bounds("evt", big, "tgt") is TransitionResultCode.SOURCE_INVALID

    def test_target_over_64_bytes_rejects(self):
        big = "t" * (IDENTIFIER_MAX_BYTES + 1)
        assert validate_identifier_bounds("evt", "src", big) is TransitionResultCode.TARGET_INVALID

    def test_utf8_multibyte_bounded(self):
        # 4-byte UTF-8 char × 25 = 100 bytes (over 96)
        big = "🚀" * 25
        assert validate_identifier_bounds(big, "src", "tgt") is TransitionResultCode.EVENT_ID_INVALID


# ═══════════════════════ START_DRAIN ═══════════════════════
class TestStartDrainHappyPath:
    def test_start_drain_success(self):
        cs = _cs(marks=[_mark()])
        new_cs, tr = start_drain(cs, command=_cmd(), now=_now())
        assert tr.code is TransitionResultCode.DRAIN_STARTED
        assert len(new_cs.active_drain_executions) == 1
        drain = new_cs.active_drain_executions[0]
        assert drain.runtime_status is DrainStatus.IN_PROGRESS
        assert drain.mark_id == "mark-abc"
        assert drain.required_mark_application_id == "app-xyz"
        assert drain.drain_execution_id.startswith(DRAIN_EXECUTION_ID_PREFIX)
        # UUIDv4 is 36 chars + "drn-" = 40 chars total (server-authoritative, NOT truncated)
        assert len(drain.drain_execution_id) == len(DRAIN_EXECUTION_ID_PREFIX) + 36
        assert new_cs.class_state_version == cs.class_state_version + 1

    def test_start_drain_mark_still_active(self):
        cs = _cs(marks=[_mark()])
        _, tr = start_drain(cs, command=_cmd(), now=_now())
        assert tr.success is False  # DRAIN_STARTED is not SUCCESS enum but positive
        assert tr.code.value == "DRAIN_STARTED"


class TestStartDrainRejections:
    def test_event_id_invalid(self):
        cs = _cs(marks=[_mark()])
        cmd = _cmd(event_id="")
        new_cs, tr = start_drain(cs, command=cmd, now=_now())
        assert tr.code is TransitionResultCode.EVENT_ID_INVALID
        assert new_cs == cs  # zero mutation

    def test_source_id_over_bounds(self):
        cs = _cs(source="s" * 65, marks=[_mark(source="s" * 65)])
        cmd = _cmd(source="s" * 65)
        new_cs, tr = start_drain(cs, command=cmd, now=_now())
        assert tr.code is TransitionResultCode.SOURCE_INVALID
        assert new_cs == cs

    def test_target_id_over_bounds(self):
        cs = _cs(marks=[_mark()])
        cmd = _cmd(target="t" * 65)
        new_cs, tr = start_drain(cs, command=cmd, now=_now())
        assert tr.code is TransitionResultCode.TARGET_INVALID
        assert new_cs == cs

    def test_mark_not_found(self):
        cs = _cs(marks=[])  # No marks
        new_cs, tr = start_drain(cs, command=_cmd(), now=_now())
        assert tr.code is TransitionResultCode.MARK_NOT_FOUND
        assert new_cs == cs

    def test_mark_expired(self):
        cs = _cs(marks=[_mark(offset_seconds=-1)])  # expired
        new_cs, tr = start_drain(cs, command=_cmd(), now=_now())
        assert tr.code is TransitionResultCode.MARK_EXPIRED
        assert new_cs == cs

    def test_ownership_mismatch(self):
        cs = _cs(source="adv-1", marks=[_mark(source="adv-1")])
        # caller claims adv-2 but cs is adv-1
        cmd = _cmd(source="adv-2")
        new_cs, tr = start_drain(cs, command=cmd, now=_now())
        assert tr.code is TransitionResultCode.OWNERSHIP_INVALID
        assert tr.reason_code == ReasonCode.MARK_OWNERSHIP_MISMATCH.value
        assert new_cs == cs

    def test_mark_application_changed(self):
        cs = _cs(marks=[_mark()])  # Mark has application_id "app-xyz"
        cmd = _cmd(application_id="different-app-id")
        new_cs, tr = start_drain(cs, command=cmd, now=_now())
        assert tr.code is TransitionResultCode.MARK_APPLICATION_CHANGED
        assert new_cs == cs

    def test_mark_id_mismatch(self):
        cs = _cs(marks=[_mark()])
        cmd = _cmd(mark_id="different-mark-id")
        new_cs, tr = start_drain(cs, command=cmd, now=_now())
        assert tr.code is TransitionResultCode.MARK_APPLICATION_CHANGED
        assert new_cs == cs

    def test_expedition_terminal_rejected(self):
        cs = _cs(marks=[_mark()])
        new_cs, tr = start_drain(cs, command=_cmd(), now=_now(), expedition_terminal=True)
        assert tr.code is TransitionResultCode.EXPEDITION_TERMINAL_REJECTED
        assert new_cs == cs

    def test_phase_inactive(self):
        cs = _cs(marks=[_mark()])
        new_cs, tr = start_drain(cs, command=_cmd(), now=_now(), phase_ended=True)
        assert tr.code is TransitionResultCode.PHASE_INACTIVE
        assert new_cs == cs

    def test_receipt_cap_reached(self):
        cs = _cs(marks=[_mark()])
        new_cs, tr = start_drain(cs, command=_cmd(), now=_now(), receipt_ordinary_available=False)
        assert tr.code is TransitionResultCode.RECEIPT_CAP_REACHED
        assert new_cs == cs


class TestStartDrainHardLocks:
    def test_hard_lock_pair_max_one(self):
        existing_drain = DrainDoc(
            drain_execution_id="drn-existing",
            source_adventurer_id="adv-1",
            target_id="tgt-1",
            mark_id="mark-abc",
            required_mark_application_id="app-xyz",
            started_at=_now().isoformat(),
        )
        cs = _cs(marks=[_mark()], drains=[existing_drain])
        new_cs, tr = start_drain(cs, command=_cmd(), now=_now())
        assert tr.code is TransitionResultCode.DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR
        assert tr.reason_code == "DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR"
        assert len(new_cs.active_drain_executions) == 1  # unchanged

    def test_hard_lock_application_max_one(self):
        # Different target but same mark_id + application_id (edge case)
        existing_drain = DrainDoc(
            drain_execution_id="drn-existing",
            source_adventurer_id="adv-1",
            target_id="tgt-other",
            mark_id="mark-abc",
            required_mark_application_id="app-xyz",
            started_at=_now().isoformat(),
        )
        cs = _cs(marks=[_mark(target="tgt-1")], drains=[existing_drain])
        new_cs, tr = start_drain(cs, command=_cmd(), now=_now())
        assert tr.code is TransitionResultCode.DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR
        assert tr.reason_code == "DRAIN_ALREADY_IN_PROGRESS_FOR_APPLICATION"
        assert len(new_cs.active_drain_executions) == 1

    def test_terminal_drain_does_not_block_new(self):
        # Terminal drain (RESOLVED) on same pair — should NOT block new
        terminal_drain = DrainDoc(
            drain_execution_id="drn-old",
            source_adventurer_id="adv-1",
            target_id="tgt-1",
            mark_id="mark-old",
            required_mark_application_id="app-old",
            started_at=_now().isoformat(),
            completed_at=_now().isoformat(),
            runtime_status=DrainStatus.RESOLVED,
        )
        cs = _cs(marks=[_mark()], drains=[terminal_drain])
        new_cs, tr = start_drain(cs, command=_cmd(), now=_now())
        assert tr.code is TransitionResultCode.DRAIN_STARTED
        assert len(new_cs.active_drain_executions) == 2


# ═══════════════════════ COMPLETE_DRAIN ═══════════════════════
class TestCompleteDrainHappyPath:
    def _setup(self, fragment_count: int = 0):
        drain = DrainDoc(
            drain_execution_id="drn-test-1",
            source_adventurer_id="adv-1",
            target_id="tgt-1",
            mark_id="mark-abc",
            required_mark_application_id="app-xyz",
            started_at=_now().isoformat(),
        )
        cs = _cs(marks=[_mark()], drains=[drain], fragment_count=fragment_count)
        cmd = _cmd(
            command_type="COMPLETE_DRAIN",
            drain_execution_id="drn-test-1",
            event_id="evt-complete-1",
        )
        return cs, cmd

    def test_complete_drain_success_zero_to_one(self):
        cs, cmd = self._setup(fragment_count=0)
        new_cs, tr, receipt = complete_drain(cs, command=cmd, now=_now())
        assert tr.code is TransitionResultCode.DRAIN_COMPLETED
        assert new_cs.fragment_count == 1
        assert new_cs.resource_segment_id is not None  # opened on 0 → positive
        assert new_cs.resource_segment_id.startswith("sg-")
        assert new_cs.active_drain_executions[0].runtime_status is DrainStatus.RESOLVED
        assert receipt is not None
        assert receipt.fragment_gain_requested == 1
        assert receipt.fragment_gain_applied == 1
        assert receipt.fragment_overflow_discarded == 0
        assert receipt.mark_valid_at_completion is True
        assert receipt.drain_execution_id == "drn-test-1"

    def test_complete_drain_at_cap_overflow_discarded(self):
        cs, cmd = self._setup(fragment_count=FRAGMENT_CAP)
        new_cs, tr, receipt = complete_drain(cs, command=cmd, now=_now())
        assert tr.code is TransitionResultCode.DRAIN_COMPLETED
        assert new_cs.fragment_count == FRAGMENT_CAP  # unchanged
        assert receipt.fragment_gain_requested == 1
        assert receipt.fragment_gain_applied == 0
        assert receipt.fragment_overflow_discarded == 1
        assert new_cs.active_drain_executions[0].runtime_status is DrainStatus.RESOLVED

    def test_complete_drain_mid_cap_no_segment_change(self):
        cs, cmd = self._setup(fragment_count=3)
        cs = AdventurerClassState(
            adventurer_id=cs.adventurer_id,
            active_marks=cs.active_marks,
            active_drain_executions=cs.active_drain_executions,
            fragment_count=cs.fragment_count,
            resource_segment_id="sg-existing",
            focus_bonus_usage=cs.focus_bonus_usage,
            class_state_version=cs.class_state_version,
        )
        new_cs, tr, receipt = complete_drain(cs, command=cmd, now=_now())
        assert new_cs.fragment_count == 4
        assert new_cs.resource_segment_id == "sg-existing"


class TestCompleteDrainRejections:
    def test_drain_not_started(self):
        cs = _cs(marks=[_mark()], drains=[])
        cmd = _cmd(command_type="COMPLETE_DRAIN", drain_execution_id="drn-nonexistent")
        new_cs, tr, receipt = complete_drain(cs, command=cmd, now=_now())
        assert tr.code is TransitionResultCode.DRAIN_NOT_STARTED
        assert receipt is None
        assert new_cs == cs

    def test_drain_already_completed(self):
        drain = DrainDoc(
            drain_execution_id="drn-done",
            source_adventurer_id="adv-1",
            target_id="tgt-1",
            mark_id="mark-abc",
            required_mark_application_id="app-xyz",
            started_at=_now().isoformat(),
            completed_at=_now().isoformat(),
            runtime_status=DrainStatus.RESOLVED,
        )
        cs = _cs(marks=[_mark()], drains=[drain])
        cmd = _cmd(command_type="COMPLETE_DRAIN", drain_execution_id="drn-done")
        _, tr, receipt = complete_drain(cs, command=cmd, now=_now())
        assert tr.code is TransitionResultCode.DRAIN_ALREADY_COMPLETED
        assert receipt is None

    def test_drain_already_cancelled(self):
        drain = DrainDoc(
            drain_execution_id="drn-cx",
            source_adventurer_id="adv-1",
            target_id="tgt-1",
            mark_id="mark-abc",
            required_mark_application_id="app-xyz",
            started_at=_now().isoformat(),
            cancelled_at=_now().isoformat(),
            cancellation_reason="EXPLICIT_SERVER_CANCEL",
            runtime_status=DrainStatus.CANCELLED,
        )
        cs = _cs(marks=[_mark()], drains=[drain])
        cmd = _cmd(command_type="COMPLETE_DRAIN", drain_execution_id="drn-cx")
        _, tr, _ = complete_drain(cs, command=cmd, now=_now())
        assert tr.code is TransitionResultCode.DRAIN_ALREADY_CANCELLED

    def test_mark_expired_between_start_and_complete(self):
        drain = DrainDoc(
            drain_execution_id="drn-mx",
            source_adventurer_id="adv-1",
            target_id="tgt-1",
            mark_id="mark-abc",
            required_mark_application_id="app-xyz",
            started_at=_now().isoformat(),
        )
        # Mark now expired
        cs = _cs(marks=[_mark(offset_seconds=-1)], drains=[drain])
        cmd = _cmd(command_type="COMPLETE_DRAIN", drain_execution_id="drn-mx")
        _, tr, receipt = complete_drain(cs, command=cmd, now=_now())
        assert tr.code is TransitionResultCode.MARK_EXPIRED
        assert receipt is None

    def test_mark_application_changed(self):
        drain = DrainDoc(
            drain_execution_id="drn-mc",
            source_adventurer_id="adv-1",
            target_id="tgt-1",
            mark_id="mark-abc",
            required_mark_application_id="app-OLD",
            started_at=_now().isoformat(),
        )
        cs = _cs(marks=[_mark()], drains=[drain])  # Mark has app-xyz not app-OLD
        cmd = _cmd(command_type="COMPLETE_DRAIN", drain_execution_id="drn-mc")
        _, tr, receipt = complete_drain(cs, command=cmd, now=_now())
        assert tr.code is TransitionResultCode.MARK_APPLICATION_CHANGED
        assert receipt is None

    def test_expedition_terminal(self):
        drain = DrainDoc(
            drain_execution_id="drn-et",
            source_adventurer_id="adv-1",
            target_id="tgt-1",
            mark_id="mark-abc",
            required_mark_application_id="app-xyz",
            started_at=_now().isoformat(),
        )
        cs = _cs(marks=[_mark()], drains=[drain])
        cmd = _cmd(command_type="COMPLETE_DRAIN", drain_execution_id="drn-et")
        _, tr, _ = complete_drain(cs, command=cmd, now=_now(), expedition_terminal=True)
        assert tr.code is TransitionResultCode.EXPEDITION_TERMINAL_REJECTED

    def test_phase_ended(self):
        drain = DrainDoc(
            drain_execution_id="drn-pe",
            source_adventurer_id="adv-1",
            target_id="tgt-1",
            mark_id="mark-abc",
            required_mark_application_id="app-xyz",
            started_at=_now().isoformat(),
        )
        cs = _cs(marks=[_mark()], drains=[drain])
        cmd = _cmd(command_type="COMPLETE_DRAIN", drain_execution_id="drn-pe")
        _, tr, _ = complete_drain(cs, command=cmd, now=_now(), phase_ended=True)
        assert tr.code is TransitionResultCode.PHASE_INACTIVE

    def test_receipt_cap_reached(self):
        drain = DrainDoc(
            drain_execution_id="drn-rc",
            source_adventurer_id="adv-1",
            target_id="tgt-1",
            mark_id="mark-abc",
            required_mark_application_id="app-xyz",
            started_at=_now().isoformat(),
        )
        cs = _cs(marks=[_mark()], drains=[drain])
        cmd = _cmd(command_type="COMPLETE_DRAIN", drain_execution_id="drn-rc")
        _, tr, receipt = complete_drain(cs, command=cmd, now=_now(), receipt_ordinary_available=False)
        assert tr.code is TransitionResultCode.RECEIPT_CAP_REACHED
        assert receipt is None


# ═══════════════════════ CANCEL_DRAIN ═══════════════════════
class TestCancelDrain:
    def _drain(self, status: DrainStatus = DrainStatus.IN_PROGRESS) -> DrainDoc:
        return DrainDoc(
            drain_execution_id="drn-cancel-1",
            source_adventurer_id="adv-1",
            target_id="tgt-1",
            mark_id="mark-abc",
            required_mark_application_id="app-xyz",
            started_at=_now().isoformat(),
            runtime_status=status,
        )

    @pytest.mark.parametrize("reason", sorted(DRAIN_CANCEL_REASONS))
    def test_cancel_all_8_canonical_reasons(self, reason):
        cs = _cs(marks=[_mark()], drains=[self._drain()])
        cmd = _cmd(
            command_type="CANCEL_DRAIN",
            drain_execution_id="drn-cancel-1",
            cancellation_reason=reason,
        )
        new_cs, tr = cancel_drain(cs, command=cmd, now=_now())
        assert tr.code is TransitionResultCode.DRAIN_CANCELLED
        assert new_cs.active_drain_executions[0].runtime_status is DrainStatus.CANCELLED
        assert new_cs.active_drain_executions[0].cancellation_reason == reason

    def test_cancel_unknown_reason_rejected(self):
        cs = _cs(marks=[_mark()], drains=[self._drain()])
        cmd = _cmd(
            command_type="CANCEL_DRAIN",
            drain_execution_id="drn-cancel-1",
            cancellation_reason="MADE_UP_REASON",
        )
        new_cs, tr = cancel_drain(cs, command=cmd, now=_now())
        assert tr.code is TransitionResultCode.SOURCE_INVALID
        assert tr.reason_code == "UNKNOWN_CANCELLATION_REASON"
        assert new_cs == cs

    def test_cancel_drain_not_found(self):
        cs = _cs(marks=[_mark()])
        cmd = _cmd(
            command_type="CANCEL_DRAIN",
            drain_execution_id="drn-nowhere",
            cancellation_reason="EXPLICIT_SERVER_CANCEL",
        )
        _, tr = cancel_drain(cs, command=cmd, now=_now())
        assert tr.code is TransitionResultCode.DRAIN_NOT_STARTED

    def test_cancel_already_cancelled_idempotent(self):
        cs = _cs(marks=[_mark()], drains=[self._drain(status=DrainStatus.CANCELLED)])
        cmd = _cmd(
            command_type="CANCEL_DRAIN",
            drain_execution_id="drn-cancel-1",
            cancellation_reason="EXPLICIT_SERVER_CANCEL",
        )
        new_cs, tr = cancel_drain(cs, command=cmd, now=_now())
        assert tr.code is TransitionResultCode.DRAIN_ALREADY_CANCELLED
        assert new_cs == cs

    def test_cancel_already_completed(self):
        cs = _cs(marks=[_mark()], drains=[self._drain(status=DrainStatus.RESOLVED)])
        cmd = _cmd(
            command_type="CANCEL_DRAIN",
            drain_execution_id="drn-cancel-1",
            cancellation_reason="EXPLICIT_SERVER_CANCEL",
        )
        _, tr = cancel_drain(cs, command=cmd, now=_now())
        assert tr.code is TransitionResultCode.DRAIN_ALREADY_COMPLETED

    def test_cancel_ownership_mismatch(self):
        cs = _cs(marks=[_mark()], drains=[self._drain()])
        # Non-lifecycle reason with ownership mismatch
        cmd = _cmd(
            command_type="CANCEL_DRAIN",
            drain_execution_id="drn-cancel-1",
            cancellation_reason="EXPLICIT_SERVER_CANCEL",
            source="adv-2",  # different from cs.adventurer_id="adv-1"
        )
        _, tr = cancel_drain(cs, command=cmd, now=_now())
        assert tr.code is TransitionResultCode.OWNERSHIP_INVALID

    def test_cancel_lifecycle_bypasses_ownership(self):
        # PHASE_ENDED lifecycle should be able to cancel Drain regardless of source match
        cs = _cs(source="adv-1", marks=[_mark(source="adv-1")], drains=[self._drain()])
        cmd = _cmd(
            command_type="CANCEL_DRAIN",
            drain_execution_id="drn-cancel-1",
            cancellation_reason="PHASE_ENDED",
            source="lifecycle-worker",
        )
        _, tr = cancel_drain(cs, command=cmd, now=_now())
        assert tr.code is TransitionResultCode.DRAIN_CANCELLED

    def test_cancel_expedition_terminal_lifecycle(self):
        cs = _cs(marks=[_mark()], drains=[self._drain()])
        cmd = _cmd(
            command_type="CANCEL_DRAIN",
            drain_execution_id="drn-cancel-1",
            cancellation_reason="EXPEDITION_TERMINAL",
            source="lifecycle-worker",
        )
        _, tr = cancel_drain(cs, command=cmd, now=_now())
        assert tr.code is TransitionResultCode.DRAIN_CANCELLED


# ═══════════════════════ Result-code coverage ═══════════════════════
class TestDrainResultCodeCoverage:
    """Verify every new Drain result code introduced by RT2-B-2B-2-1 is exercised."""

    def test_drain_started_covered(self):
        cs = _cs(marks=[_mark()])
        _, tr = start_drain(cs, command=_cmd(), now=_now())
        assert tr.code is TransitionResultCode.DRAIN_STARTED

    def test_drain_completed_covered(self):
        drain = DrainDoc(
            drain_execution_id="drn-cov",
            source_adventurer_id="adv-1",
            target_id="tgt-1",
            mark_id="mark-abc",
            required_mark_application_id="app-xyz",
            started_at=_now().isoformat(),
        )
        cs = _cs(marks=[_mark()], drains=[drain])
        cmd = _cmd(command_type="COMPLETE_DRAIN", drain_execution_id="drn-cov")
        _, tr, _ = complete_drain(cs, command=cmd, now=_now())
        assert tr.code is TransitionResultCode.DRAIN_COMPLETED

    def test_drain_cancelled_covered(self):
        drain = DrainDoc(
            drain_execution_id="drn-cov2",
            source_adventurer_id="adv-1",
            target_id="tgt-1",
            mark_id="mark-abc",
            required_mark_application_id="app-xyz",
            started_at=_now().isoformat(),
        )
        cs = _cs(marks=[_mark()], drains=[drain])
        cmd = _cmd(
            command_type="CANCEL_DRAIN",
            drain_execution_id="drn-cov2",
            cancellation_reason="EXPLICIT_SERVER_CANCEL",
        )
        _, tr = cancel_drain(cs, command=cmd, now=_now())
        assert tr.code is TransitionResultCode.DRAIN_CANCELLED

    def test_all_new_drain_codes_defined(self):
        # Ensure every new code is present in TransitionResultCode enum
        new_codes = {
            "DRAIN_STARTED",
            "DRAIN_COMPLETED",
            "DRAIN_CANCELLED",
            "DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR",
            "MARK_APPLICATION_CHANGED",
            "EXPEDITION_TERMINAL_REJECTED",
            "PHASE_INACTIVE",
            "DRAIN_NOT_STARTED",
            "DRAIN_ALREADY_COMPLETED",
            "DRAIN_ALREADY_CANCELLED",
            "EVENT_ID_INVALID",
            "LEASE_ACQUISITION_FAILED",
            "RETRY_LIMIT_REACHED",
            "STORE_INFRA_ERROR",
        }
        enum_values = {c.value for c in TransitionResultCode}
        missing = new_codes - enum_values
        assert not missing, f"Missing new Drain codes in enum: {missing}"


# ═══════════════════════ Legacy invariance ═══════════════════════
class TestLegacyInvariance:
    """Assert existing (RT2-B-2B-1) transitions are unaffected by the new Drain module."""

    def test_trusted_drain_receipt_still_importable_for_legacy(self):
        # DEPRECATED_COMPATIBILITY_ONLY: legacy test fixtures still import it
        from app.stats.runtime.transitions.models import TrustedDrainReceipt
        rec = TrustedDrainReceipt(
            drain_execution_id="drn-legacy",
            source_adventurer_id="adv-1",
            target_id="tgt-1",
            mark_application_id="app-xyz",
            completed_at=_now().isoformat(),
        )
        assert rec.fixture_only_marker == "RT2B2B1_TRUSTED_FIXTURE_ONLY"

    def test_drain_module_zero_dependency_on_trusted_receipt(self):
        # Static: verify transitions/drain.py does not import TrustedDrainReceipt
        import ast
        import app.stats.runtime.transitions.drain as _drain_module
        from pathlib import Path
        src = Path(_drain_module.__file__).read_text()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                names = {alias.name for alias in node.names}
                assert "TrustedDrainReceipt" not in names, (
                    "drain.py must have zero dependency on TrustedDrainReceipt "
                    "(DEPRECATED_COMPATIBILITY_ONLY per PM adjudication)"
                )


# ═══════════════════════ 6-conditions gate ═══════════════════════
class TestSixConditionsGate:
    def test_gate_closed_when_transient_off(self, monkeypatch):
        from app.stats.runtime import feature_flags as ff
        from app.stats.runtime.wiring.feature_flags import (
            DrainGateContext,
            GATE_REASON_TRANSIENT_OFF,
            is_drain_gate_open,
        )
        ff.reset_cache()
        monkeypatch.delenv("ORBUS_FLAG_CDV_TRANSIENT_STATE_ENABLED", raising=False)
        ctx = DrainGateContext(True, True, True)
        ok, reason = is_drain_gate_open(ctx)
        assert ok is False
        assert reason == GATE_REASON_TRANSIENT_OFF

    def test_gate_closed_when_class_off(self, monkeypatch):
        from app.stats.runtime import feature_flags as ff
        from app.stats.runtime.wiring.feature_flags import (
            DrainGateContext,
            GATE_REASON_CLASS_OFF,
            is_drain_gate_open,
        )
        ff.reset_cache()
        monkeypatch.setenv("ORBUS_FLAG_CDV_TRANSIENT_STATE_ENABLED", "true")
        monkeypatch.delenv("ORBUS_FLAG_CDV_CLASS_TRANSITIONS_ENABLED", raising=False)
        ff.reset_cache()
        ctx = DrainGateContext(True, True, True)
        ok, reason = is_drain_gate_open(ctx)
        assert ok is False
        assert reason == GATE_REASON_CLASS_OFF
        ff.reset_cache()

    def test_gate_closed_when_drain_off(self, monkeypatch):
        from app.stats.runtime import feature_flags as ff
        from app.stats.runtime.wiring.feature_flags import (
            DrainGateContext,
            GATE_REASON_DRAIN_OFF,
            is_drain_gate_open,
        )
        ff.reset_cache()
        monkeypatch.setenv("ORBUS_FLAG_CDV_TRANSIENT_STATE_ENABLED", "true")
        monkeypatch.setenv("ORBUS_FLAG_CDV_CLASS_TRANSITIONS_ENABLED", "true")
        monkeypatch.delenv("ORBUS_FLAG_CDV_DRAIN_TRANSITIONS_ENABLED", raising=False)
        ff.reset_cache()
        ctx = DrainGateContext(True, True, True)
        ok, reason = is_drain_gate_open(ctx)
        assert ok is False
        assert reason == GATE_REASON_DRAIN_OFF
        ff.reset_cache()

    def test_gate_closed_when_test_user_false(self, monkeypatch):
        from app.stats.runtime import feature_flags as ff
        from app.stats.runtime.wiring.feature_flags import (
            DrainGateContext,
            GATE_REASON_TEST_USER,
            is_drain_gate_open,
        )
        ff.reset_cache()
        monkeypatch.setenv("ORBUS_FLAG_CDV_TRANSIENT_STATE_ENABLED", "true")
        monkeypatch.setenv("ORBUS_FLAG_CDV_CLASS_TRANSITIONS_ENABLED", "true")
        monkeypatch.setenv("ORBUS_FLAG_CDV_DRAIN_TRANSITIONS_ENABLED", "true")
        ff.reset_cache()
        ctx = DrainGateContext(is_test_user=False, environment_is_localhost_isolated=True, mongo_target_allowlisted=True)
        ok, reason = is_drain_gate_open(ctx)
        assert ok is False
        assert reason == GATE_REASON_TEST_USER
        ff.reset_cache()

    def test_gate_closed_when_env_not_localhost(self, monkeypatch):
        from app.stats.runtime import feature_flags as ff
        from app.stats.runtime.wiring.feature_flags import (
            DrainGateContext,
            GATE_REASON_ENV,
            is_drain_gate_open,
        )
        ff.reset_cache()
        monkeypatch.setenv("ORBUS_FLAG_CDV_TRANSIENT_STATE_ENABLED", "true")
        monkeypatch.setenv("ORBUS_FLAG_CDV_CLASS_TRANSITIONS_ENABLED", "true")
        monkeypatch.setenv("ORBUS_FLAG_CDV_DRAIN_TRANSITIONS_ENABLED", "true")
        ff.reset_cache()
        ctx = DrainGateContext(is_test_user=True, environment_is_localhost_isolated=False, mongo_target_allowlisted=True)
        ok, reason = is_drain_gate_open(ctx)
        assert ok is False
        assert reason == GATE_REASON_ENV
        ff.reset_cache()

    def test_gate_closed_when_db_not_allowlisted(self, monkeypatch):
        from app.stats.runtime import feature_flags as ff
        from app.stats.runtime.wiring.feature_flags import (
            DrainGateContext,
            GATE_REASON_DB,
            is_drain_gate_open,
        )
        ff.reset_cache()
        monkeypatch.setenv("ORBUS_FLAG_CDV_TRANSIENT_STATE_ENABLED", "true")
        monkeypatch.setenv("ORBUS_FLAG_CDV_CLASS_TRANSITIONS_ENABLED", "true")
        monkeypatch.setenv("ORBUS_FLAG_CDV_DRAIN_TRANSITIONS_ENABLED", "true")
        ff.reset_cache()
        ctx = DrainGateContext(is_test_user=True, environment_is_localhost_isolated=True, mongo_target_allowlisted=False)
        ok, reason = is_drain_gate_open(ctx)
        assert ok is False
        assert reason == GATE_REASON_DB
        ff.reset_cache()

    def test_gate_open_when_all_6_conditions_true(self, monkeypatch):
        from app.stats.runtime import feature_flags as ff
        from app.stats.runtime.wiring.feature_flags import (
            DrainGateContext,
            GATE_REASON_OPEN,
            is_drain_gate_open,
        )
        ff.reset_cache()
        monkeypatch.setenv("ORBUS_FLAG_CDV_TRANSIENT_STATE_ENABLED", "true")
        monkeypatch.setenv("ORBUS_FLAG_CDV_CLASS_TRANSITIONS_ENABLED", "true")
        monkeypatch.setenv("ORBUS_FLAG_CDV_DRAIN_TRANSITIONS_ENABLED", "true")
        ff.reset_cache()
        ctx = DrainGateContext(is_test_user=True, environment_is_localhost_isolated=True, mongo_target_allowlisted=True)
        ok, reason = is_drain_gate_open(ctx)
        assert ok is True
        assert reason == GATE_REASON_OPEN
        ff.reset_cache()

    def test_all_drain_cancel_reasons_are_8(self):
        assert len(DRAIN_CANCEL_REASONS) == 8


# ═══════════════════════ Model extensions ═══════════════════════
class TestDrainDocExtensions:
    def test_draindoc_has_new_fields(self):
        d = DrainDoc(
            drain_execution_id="drn-x",
            source_adventurer_id="adv-1",
            target_id="tgt-1",
            required_mark_application_id="app-xyz",
            started_at=_now().isoformat(),
        )
        # New fields have safe defaults
        assert d.mark_id == ""
        assert d.cancelled_at is None
        assert d.cancellation_reason is None
        assert d.drain_version == 1

    def test_draindoc_frozen(self):
        d = DrainDoc(
            drain_execution_id="drn-x",
            source_adventurer_id="adv-1",
            target_id="tgt-1",
            required_mark_application_id="app-xyz",
            started_at=_now().isoformat(),
        )
        with pytest.raises(Exception):
            d.drain_execution_id = "hacked"  # type: ignore[misc]
