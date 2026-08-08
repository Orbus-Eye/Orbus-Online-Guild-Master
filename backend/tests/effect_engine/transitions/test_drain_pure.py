"""RT2-B-2B-2-1 · Drain pure state-machine tests (0 network · 0 DB).

Copertura B2B2Q01/Q03/Q04/Q05/Q06/Q07/Q08/Q10 pure-level.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta, timezone

from app.stats.runtime.state_store.models import (
    AdventurerClassState,
    DrainDoc,
    DrainStatus,
    FragmentUsage,
    MarkDoc,
)
from app.stats.runtime.transitions.drain import (
    CANONICAL_CANCELLATION_REASONS,
    cancel_drain,
    cancel_started_drains_for_lifecycle,
    complete_drain,
    generate_drain_execution_id,
    start_drain,
)
from app.stats.runtime.transitions.models import TransitionResultCode as RC

NOW = datetime(2026, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
ADV = "adv-cdv-01"
TGT = "target-boss-01"
EXP = "exp-pure-01"

_UUID4_RE = re.compile(
    r"^drn-[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def _iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def _mark(target=TGT, source=ADV, expires_in=10, application_id=None, mark_id=None):
    return MarkDoc(
        mark_id=mark_id or f"mark-{uuid.uuid4().hex[:16]}",
        application_id=application_id or f"app-{uuid.uuid4().hex[:16]}",
        source_adventurer_id=source,
        target_id=target,
        created_at=_iso(NOW),
        expires_at=_iso(NOW + timedelta(seconds=expires_in)),
    )


def _cs(marks=(), drains=(), fragment_count=0, segment=None, focus=()):
    return AdventurerClassState(
        adventurer_id=ADV,
        active_marks=tuple(marks),
        active_drain_executions=tuple(drains),
        fragment_count=fragment_count,
        resource_segment_id=segment,
        focus_bonus_usage=tuple(focus),
    )


def _start(cs, target=TGT, source=ADV, now=NOW, event_id="evt-start-1"):
    return start_drain(
        cs, target_id=target, now=now, event_id=event_id,
        expedition_id=EXP, source_adventurer_id=source,
    )


def _complete(cs, drain_id, source=ADV, now=NOW, event_id="evt-comp-1", seq=2, ver=3):
    return complete_drain(
        cs, drain_execution_id=drain_id, now=now, event_id=event_id,
        expedition_id=EXP, source_adventurer_id=source,
        next_event_sequence=seq, state_version_after=ver,
    )


# ═══════ B2B2Q01 · execution identity ═══════
def test_p01_execution_id_full_canonical_uuidv4():
    for _ in range(20):
        eid = generate_drain_execution_id()
        assert _UUID4_RE.match(eid), f"non-canonical execution id: {eid}"
        assert len(eid) == 4 + 36  # 'drn-' + full UUID (NON troncato)


def test_p02_start_valid_creates_in_progress_drain():
    mark = _mark()
    new_cs, tr = _start(_cs(marks=[mark]))
    assert tr.code is RC.DRAIN_STARTED
    assert _UUID4_RE.match(tr.drain_execution_id)
    drains = new_cs.active_drain_executions
    assert len(drains) == 1
    d = drains[0]
    assert d.runtime_status is DrainStatus.IN_PROGRESS
    assert d.mark_id == mark.mark_id
    assert d.required_mark_application_id == mark.application_id
    assert d.start_event_id == "evt-start-1"
    assert d.drain_version == 1


def test_p03_start_does_not_consume_mark():
    mark = _mark()
    new_cs, tr = _start(_cs(marks=[mark]))
    assert tr.code is RC.DRAIN_STARTED
    assert new_cs.active_marks == (mark,)  # Drain consumes Mark = false


# ═══════ START rejections ═══════
def test_p04_start_no_mark_rejected():
    _, tr = _start(_cs())
    assert tr.code is RC.MARK_NOT_FOUND


def test_p05_start_expired_mark_rejected():
    cs = _cs(marks=[_mark(expires_in=-1)])
    new_cs, tr = _start(cs)
    assert tr.code is RC.MARK_EXPIRED
    assert new_cs is cs  # no mutation


def test_p06_start_invalid_target_rejected():
    cs = _cs(marks=[_mark()])
    _, tr = _start(cs, target="")
    assert tr.code is RC.TARGET_INVALID
    _, tr2 = _start(cs, target=ADV)  # self-target
    assert tr2.code is RC.TARGET_INVALID


def test_p07_start_invalid_source_rejected():
    cs = _cs(marks=[_mark()])
    _, tr = _start(cs, source="adv-other")
    assert tr.code is RC.SOURCE_INVALID


def test_p08_start_foreign_mark_ownership_mismatch():
    cs = _cs(marks=[_mark(source="adv-foreign")])
    _, tr = _start(cs)
    assert tr.code is RC.MARK_OWNERSHIP_MISMATCH


# ═══════ PM §18 hard-locks ═══════
def test_p09_pair_hard_lock_max_one_active_drain():
    mark = _mark()
    cs1, tr1 = _start(_cs(marks=[mark]))
    assert tr1.code is RC.DRAIN_STARTED
    cs2, tr2 = _start(cs1, event_id="evt-start-2")
    assert tr2.code is RC.DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR
    assert tr2.drain_execution_id == tr1.drain_execution_id
    assert cs2 is cs1  # no mutation


def test_p10_application_hard_lock():
    mark = _mark()
    stale = DrainDoc(
        drain_execution_id=generate_drain_execution_id(),
        source_adventurer_id=ADV,
        target_id="target-legacy",  # pair diverso · stessa application
        required_mark_application_id=mark.application_id,
        mark_id=mark.mark_id,
        started_at=_iso(NOW),
        runtime_status=DrainStatus.IN_PROGRESS,
    )
    _, tr = _start(_cs(marks=[mark], drains=[stale]))
    assert tr.code is RC.DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR
    assert tr.reason_code == "APPLICATION_HARD_LOCK"


def test_p11_terminal_drain_does_not_block_new_start():
    mark = _mark()
    old = DrainDoc(
        drain_execution_id=generate_drain_execution_id(),
        source_adventurer_id=ADV,
        target_id=TGT,
        required_mark_application_id="app-old",
        mark_id="mark-old",
        started_at=_iso(NOW - timedelta(seconds=30)),
        runtime_status=DrainStatus.CANCELLED,
        cancellation_reason="MARK_EXPIRED",
    )
    new_cs, tr = _start(_cs(marks=[mark], drains=[old]))
    assert tr.code is RC.DRAIN_STARTED
    assert len(new_cs.active_drain_executions) == 2


# ═══════ COMPLETE · valid path + completion-to-Fragment (B2B2Q05/Q06/Q07) ═══════
def test_p12_complete_valid_fragment_gain_fixed_1():
    mark = _mark()
    cs1, tr1 = _start(_cs(marks=[mark]))
    cs2, tr2 = _complete(cs1, tr1.drain_execution_id)
    assert tr2.code is RC.DRAIN_COMPLETED
    assert tr2.fragment_gain_requested == 1
    assert tr2.fragment_gain_applied == 1
    assert tr2.fragment_overflow_discarded == 0
    assert tr2.mark_valid_at_completion is True
    assert cs2.fragment_count == 1
    d = cs2.active_drain_executions[0]
    assert d.runtime_status is DrainStatus.RESOLVED
    assert d.completed_at is not None
    assert d.drain_version == 2


def test_p13_completion_payload_embedded_15_fields():
    mark = _mark()
    cs1, tr1 = _start(_cs(marks=[mark]))
    cs2, tr2 = _complete(cs1, tr1.drain_execution_id, seq=7, ver=9)
    # PM adjudication B2B2Q07: il payload autoritativo viaggia in
    # TransitionResult.result_payload → persistito dal dispatcher DENTRO la
    # processed-event receipt (stesso CAS · stessa slot).
    p = tr2.result_payload
    assert p is not None
    # 15 campi verbatim B2B2Q07
    assert p["drain_execution_id"] == tr1.drain_execution_id
    assert p["completion_event_id"] == "evt-comp-1"
    assert p["source_adventurer_id"] == ADV
    assert p["target_id"] == TGT
    assert p["mark_id"] == mark.mark_id
    assert p["application_id"] == mark.application_id
    assert p["result_code"] == "SUCCESS"
    assert p["mark_valid_at_completion"] is True
    assert p["fragment_gain_requested"] == 1
    assert p["fragment_gain_applied"] == 1
    assert p["fragment_overflow_discarded"] == 0
    assert p["resource_segment_id"] == cs2.resource_segment_id
    assert p["assigned_event_sequence"] == 7
    assert p["state_version_after"] == 9
    assert p["processed_at"]
    assert len(p) == 15
    # DrainDoc: SOLO campi minimi · nessuna duplicazione autoritativa
    d = cs2.active_drain_executions[0]
    assert d.completion_event_id == "evt-comp-1"
    assert d.completion_payload is None


def test_p14_complete_does_not_consume_mark():
    mark = _mark()
    cs1, tr1 = _start(_cs(marks=[mark]))
    cs2, _ = _complete(cs1, tr1.drain_execution_id)
    assert cs2.active_marks == (mark,)


def test_p15_segment_opens_on_0_to_positive_with_sg_prefix():
    mark = _mark()
    cs1, tr1 = _start(_cs(marks=[mark]))
    cs2, tr2 = _complete(cs1, tr1.drain_execution_id)
    assert cs2.resource_segment_id is not None
    assert cs2.resource_segment_id.startswith("sg-")
    assert tr2.resource_segment_id == cs2.resource_segment_id


def test_p16_segment_preserved_when_already_active():
    mark = _mark()
    cs = _cs(marks=[mark], fragment_count=2, segment="sg-existing")
    cs1, tr1 = _start(cs)
    cs2, tr2 = _complete(cs1, tr1.drain_execution_id)
    assert cs2.resource_segment_id == "sg-existing"
    assert cs2.fragment_count == 3


def test_p17_overflow_at_cap_completed_with_discard():
    mark = _mark()
    cs = _cs(marks=[mark], fragment_count=5, segment="sg-full")
    cs1, tr1 = _start(cs)
    cs2, tr2 = _complete(cs1, tr1.drain_execution_id)
    # B2B2Q06 verbatim: COMPLETED · requested=1 · applied=0 · discarded=1
    assert tr2.code is RC.DRAIN_COMPLETED
    assert tr2.fragment_gain_requested == 1
    assert tr2.fragment_gain_applied == 0
    assert tr2.fragment_overflow_discarded == 1
    assert cs2.fragment_count == 5  # no credito futuro · no compensazione
    assert cs2.active_drain_executions[0].runtime_status is DrainStatus.RESOLVED


def test_p18_focus_bonus_usage_invariance():
    mark = _mark()
    focus = (FragmentUsage(resource_segment_id="sg-x", focus_bonus_used=1),)
    cs = _cs(marks=[mark], fragment_count=1, segment="sg-x", focus=focus)
    cs1, tr1 = _start(cs)
    cs2, _ = _complete(cs1, tr1.drain_execution_id)
    assert cs2.focus_bonus_usage == focus  # §30 FORBIDDEN mutation


# ═══════ COMPLETE · Mark revalidation (B2B2Q03/Q04) + fold (B2B2Q14) ═══════
def test_p19_complete_after_refresh_still_valid():
    mark = _mark()
    cs1, tr1 = _start(_cs(marks=[mark]))
    # Refresh valido: stesso mark_id + application_id · expires esteso
    refreshed = MarkDoc(
        mark_id=mark.mark_id, application_id=mark.application_id,
        source_adventurer_id=ADV, target_id=TGT,
        created_at=mark.created_at,
        expires_at=_iso(NOW + timedelta(seconds=10)),
        mark_version=2,
    )
    cs1b = AdventurerClassState(
        adventurer_id=ADV, active_marks=(refreshed,),
        active_drain_executions=cs1.active_drain_executions,
        fragment_count=0, resource_segment_id=None,
        class_state_version=cs1.class_state_version,
    )
    _, tr2 = _complete(cs1b, tr1.drain_execution_id, now=NOW + timedelta(seconds=8))
    assert tr2.code is RC.DRAIN_COMPLETED


def test_p20_complete_after_expiration_folds_cancellation():
    mark = _mark(expires_in=10)
    cs1, tr1 = _start(_cs(marks=[mark]))
    late = NOW + timedelta(seconds=11)
    cs2, tr2 = _complete(cs1, tr1.drain_execution_id, now=late)
    assert tr2.code is RC.MARK_EXPIRED
    assert tr2.cancellation_reason == "MARK_EXPIRED"
    assert tr2.mark_valid_at_completion is False
    d = cs2.active_drain_executions[0]
    assert d.runtime_status is DrainStatus.CANCELLED  # fold auto-cancel
    assert d.cancellation_reason == "MARK_EXPIRED"
    assert cs2.fragment_count == 0  # no Fragment
    assert cs2 is not cs1  # mutation da committare nella STESSA receipt


def test_p21_complete_after_reapplication_folds_application_changed():
    mark = _mark()
    cs1, tr1 = _start(_cs(marks=[mark]))
    # Nuova applicazione: nuovo mark/application sullo stesso pair
    new_mark = _mark()
    cs1b = AdventurerClassState(
        adventurer_id=ADV, active_marks=(new_mark,),
        active_drain_executions=cs1.active_drain_executions,
        fragment_count=0, resource_segment_id=None,
        class_state_version=cs1.class_state_version,
    )
    cs2, tr2 = _complete(cs1b, tr1.drain_execution_id)
    assert tr2.code is RC.MARK_APPLICATION_CHANGED
    assert cs2.active_drain_executions[0].runtime_status is DrainStatus.CANCELLED
    assert cs2.active_drain_executions[0].cancellation_reason == "MARK_APPLICATION_CHANGED"
    assert cs2.fragment_count == 0


def test_p22_complete_foreign_source_rejected_no_mutation():
    mark = _mark()
    cs1, tr1 = _start(_cs(marks=[mark]))
    cs2, tr2 = _complete(cs1, tr1.drain_execution_id, source="adv-attacker")
    assert tr2.code is RC.MARK_OWNERSHIP_MISMATCH
    assert cs2 is cs1


def test_p23_complete_unknown_id_drain_not_started():
    _, tr = _complete(_cs(marks=[_mark()]), "drn-" + str(uuid.uuid4()))
    assert tr.code is RC.DRAIN_NOT_STARTED


def test_p24_duplicate_completion_no_mutation_no_double_fragment():
    mark = _mark()
    cs1, tr1 = _start(_cs(marks=[mark]))
    cs2, tr2 = _complete(cs1, tr1.drain_execution_id)
    assert tr2.code is RC.DRAIN_COMPLETED
    cs3, tr3 = _complete(cs2, tr1.drain_execution_id, event_id="evt-comp-2")
    assert tr3.code is RC.DRAIN_ALREADY_COMPLETED
    assert cs3 is cs2
    assert cs3.fragment_count == 1  # doppia assegnazione = IMPOSSIBILE


def test_p25_complete_after_cancel_rejected():
    mark = _mark()
    cs1, tr1 = _start(_cs(marks=[mark]))
    cs2, tr2 = cancel_drain(
        cs1, drain_execution_id=tr1.drain_execution_id, now=NOW,
        event_id="evt-can-1", expedition_id=EXP, source_adventurer_id=ADV,
    )
    assert tr2.code is RC.DRAIN_CANCELLED
    cs3, tr3 = _complete(cs2, tr1.drain_execution_id)
    assert tr3.code is RC.DRAIN_ALREADY_CANCELLED
    assert cs3 is cs2
    assert cs3.fragment_count == 0  # no Fragment post-cancellation


# ═══════ CANCEL (B2B2Q08 · B2B2Q10) ═══════
def test_p26_explicit_cancel_default_reason():
    mark = _mark()
    cs1, tr1 = _start(_cs(marks=[mark]))
    cs2, tr2 = cancel_drain(
        cs1, drain_execution_id=tr1.drain_execution_id, now=NOW,
        event_id="evt-can-1", expedition_id=EXP, source_adventurer_id=ADV,
    )
    assert tr2.code is RC.DRAIN_CANCELLED
    assert tr2.cancellation_reason == "EXPLICIT_SERVER_CANCEL"
    d = cs2.active_drain_executions[0]
    assert d.runtime_status is DrainStatus.CANCELLED
    assert d.cancelled_at is not None


def test_p27_cancel_non_canonical_reason_rejected():
    mark = _mark()
    cs1, tr1 = _start(_cs(marks=[mark]))
    cs2, tr2 = cancel_drain(
        cs1, drain_execution_id=tr1.drain_execution_id, now=NOW,
        reason_code="MADE_UP_REASON",
        event_id="evt-can-1", expedition_id=EXP, source_adventurer_id=ADV,
    )
    assert tr2.code is RC.SOURCE_INVALID
    assert cs2 is cs1
    assert len(CANONICAL_CANCELLATION_REASONS) == 8  # NO extensions


def test_p28_cancel_after_completion_first_committed_wins():
    mark = _mark()
    cs1, tr1 = _start(_cs(marks=[mark]))
    cs2, _ = _complete(cs1, tr1.drain_execution_id)
    cs3, tr3 = cancel_drain(
        cs2, drain_execution_id=tr1.drain_execution_id, now=NOW,
        event_id="evt-can-1", expedition_id=EXP, source_adventurer_id=ADV,
    )
    assert tr3.code is RC.DRAIN_ALREADY_COMPLETED
    assert cs3 is cs2  # no mutation · Fragment preservato
    assert cs3.fragment_count == 1


def test_p29_cancel_already_cancelled():
    mark = _mark()
    cs1, tr1 = _start(_cs(marks=[mark]))
    cs2, _ = cancel_drain(
        cs1, drain_execution_id=tr1.drain_execution_id, now=NOW,
        event_id="evt-can-1", expedition_id=EXP, source_adventurer_id=ADV,
    )
    cs3, tr3 = cancel_drain(
        cs2, drain_execution_id=tr1.drain_execution_id, now=NOW,
        event_id="evt-can-2", expedition_id=EXP, source_adventurer_id=ADV,
    )
    assert tr3.code is RC.DRAIN_ALREADY_CANCELLED
    assert cs3 is cs2


# ═══════ Lifecycle bulk (B2B2Q11) ═══════
def test_p30_lifecycle_bulk_cancels_only_started():
    m1, m2 = _mark(target="t1"), _mark(target="t2")
    cs = _cs(marks=[m1, m2])
    cs, tr1 = _start(cs, target="t1", event_id="e1")
    cs, tr2 = _start(cs, target="t2", event_id="e2")
    cs, trc = _complete(cs, tr1.drain_execution_id)
    assert trc.code is RC.DRAIN_COMPLETED
    new_cs, cancelled = cancel_started_drains_for_lifecycle(
        cs, reason="PHASE_ENDED", now=NOW,
    )
    assert cancelled == (tr2.drain_execution_id,)
    by_id = {d.drain_execution_id: d for d in new_cs.active_drain_executions}
    # Completion committata prima mantiene il Fragment assegnato (B2B2Q11)
    assert by_id[tr1.drain_execution_id].runtime_status is DrainStatus.RESOLVED
    assert by_id[tr2.drain_execution_id].runtime_status is DrainStatus.CANCELLED
    assert by_id[tr2.drain_execution_id].cancellation_reason == "PHASE_ENDED"
    assert new_cs.fragment_count == cs.fragment_count


def test_p31_lifecycle_bulk_noop_when_no_started_drains():
    cs = _cs(marks=[_mark()])
    new_cs, cancelled = cancel_started_drains_for_lifecycle(
        cs, reason="EXPEDITION_TERMINAL", now=NOW,
    )
    assert cancelled == ()
    assert new_cs is cs
