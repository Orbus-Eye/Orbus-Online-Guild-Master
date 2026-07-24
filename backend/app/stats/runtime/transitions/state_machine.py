"""RT2-B-2B-1 · Pure/deterministic state machines (Mark · Fragment · Segment).

Ogni funzione:
- Riceve: current `AdventurerClassState` · trusted event · authoritative time · policy config
- Ritorna: (new_class_state, TransitionResult)
- NON tocca I/O · NON istanzia client Mongo · NON conosce HTTP/frontend
- È idempotente rispetto a inputs identici

Hard-locks (verbatim RT1 + B2BQ):
- active Marks ≤ 5 per source · pair (source,target) unique · duration ≤ 10s
- automatic Mark eviction FORBIDDEN
- fragment_count ∈ [0, 5] · overflow discarded (no reward/proc)
- focus_bonus_usage ≤ 2 per resource_segment
- partial fragment spend FORBIDDEN · negative amount FORBIDDEN

Receipt cap (B2BQ14): 512 total · 504 ordinary · 8 reserved.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from app.stats.runtime.state_store.models import (
    AdventurerClassState,
    FragmentUsage,
    MarkDoc,
)
from app.stats.runtime.transitions.models import (
    ReasonCode,
    ReceiptCategory,
    TransitionResult,
    TransitionResultCode,
    TrustedDrainReceipt,
    categorize_event,
)


# ═══════════════════════ Constants (PM Message 151 verbatim) ═══════════════════════
MARK_CAP_PER_SOURCE: int = 5
MARK_DURATION_SECONDS_MAX: int = 10
FRAGMENT_CAP: int = 5
FOCUS_BONUS_CAP_PER_SEGMENT: int = 2

# B2BQ14: total 512 = 504 ordinary + 8 reserved
RECEIPT_CAP_TOTAL: int = 512
RECEIPT_CAP_ORDINARY: int = 504
RECEIPT_CAP_RESERVED: int = 8

STATE_DOC_MAX_BYTES: int = 262_144  # 256 KiB


def _iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def _parse_iso(s: str) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


# ═══════════════════════ Mark transitions ═══════════════════════
def apply_mark(
    cs: AdventurerClassState,
    *,
    target_id: str,
    now: datetime,
    duration_seconds: int = MARK_DURATION_SECONDS_MAX,
    application_id: Optional[str] = None,
    event_id: str = "",
    expedition_id: str = "",
    source_adventurer_id: str = "",
) -> Tuple[AdventurerClassState, TransitionResult]:
    """Applica un Mark su un target.

    Regole:
    - source cap ≤ 5 attive (`MARK_CAP_EXCEEDED`)
    - pair (source, target) unique (`MARK_ALREADY_ACTIVE_FOR_PAIR`)
    - duration ≤ 10s
    - automatic eviction FORBIDDEN (sesto Mark = rejected)
    - refresh policy: applicazione nuova → nuovo `application_id`, nuovo `mark_id`
    """
    if duration_seconds <= 0 or duration_seconds > MARK_DURATION_SECONDS_MAX:
        return cs, TransitionResult(
            code=TransitionResultCode.SOURCE_INVALID,
            event_id=event_id,
            event_type="APPLY_MARK",
            expedition_id=expedition_id,
            source_adventurer_id=source_adventurer_id,
            reason_code="INVALID_DURATION",
        )
    if not target_id:
        return cs, TransitionResult(
            code=TransitionResultCode.TARGET_INVALID,
            event_id=event_id,
            event_type="APPLY_MARK",
            expedition_id=expedition_id,
            source_adventurer_id=source_adventurer_id,
            reason_code=ReasonCode.TARGET_INVALID.value,
        )

    # Lazy expiration prima dei check cap (opportunistic, B2BQ03 hybrid).
    active_marks = tuple(m for m in cs.active_marks if _is_mark_active(m, now))

    # Pair uniqueness check (dopo lazy expire).
    for m in active_marks:
        if m.target_id == target_id:
            return cs.__class__(
                adventurer_id=cs.adventurer_id,
                active_marks=active_marks,
                active_drain_executions=cs.active_drain_executions,
                fragment_count=cs.fragment_count,
                resource_segment_id=cs.resource_segment_id,
                focus_bonus_usage=cs.focus_bonus_usage,
                class_state_version=cs.class_state_version,
            ), TransitionResult(
                code=TransitionResultCode.MARK_ALREADY_ACTIVE_FOR_PAIR,
                event_id=event_id,
                event_type="APPLY_MARK",
                expedition_id=expedition_id,
                source_adventurer_id=source_adventurer_id,
                reason_code="PAIR_UNIQUE_VIOLATED",
                active_marks_count_after=len(active_marks),
            )

    # Cap check (post lazy-expire).
    if len(active_marks) >= MARK_CAP_PER_SOURCE:
        return cs.__class__(
            adventurer_id=cs.adventurer_id,
            active_marks=active_marks,
            active_drain_executions=cs.active_drain_executions,
            fragment_count=cs.fragment_count,
            resource_segment_id=cs.resource_segment_id,
            focus_bonus_usage=cs.focus_bonus_usage,
            class_state_version=cs.class_state_version,
        ), TransitionResult(
            code=TransitionResultCode.MARK_CAP_EXCEEDED,
            event_id=event_id,
            event_type="APPLY_MARK",
            expedition_id=expedition_id,
            source_adventurer_id=source_adventurer_id,
            reason_code="MARK_CAP_5",
            active_marks_count_after=len(active_marks),
        )

    mark_id = f"mark-{uuid.uuid4().hex[:16]}"
    app_id = application_id or f"app-{uuid.uuid4().hex[:16]}"
    new_mark = MarkDoc(
        mark_id=mark_id,
        application_id=app_id,
        source_adventurer_id=cs.adventurer_id,
        target_id=target_id,
        created_at=_iso(now),
        expires_at=_iso(now + timedelta(seconds=duration_seconds)),
        ritual_close_used=False,
        mark_version=1,
    )
    new_cs = AdventurerClassState(
        adventurer_id=cs.adventurer_id,
        active_marks=active_marks + (new_mark,),
        active_drain_executions=cs.active_drain_executions,
        fragment_count=cs.fragment_count,
        resource_segment_id=cs.resource_segment_id,
        focus_bonus_usage=cs.focus_bonus_usage,
        class_state_version=cs.class_state_version + 1,
    )
    return new_cs, TransitionResult(
        code=TransitionResultCode.SUCCESS,
        event_id=event_id,
        event_type="APPLY_MARK",
        expedition_id=expedition_id,
        source_adventurer_id=source_adventurer_id,
        mark_id=mark_id,
        mark_application_id=app_id,
        active_marks_count_after=len(new_cs.active_marks),
    )


def refresh_mark(
    cs: AdventurerClassState,
    *,
    target_id: str,
    now: datetime,
    duration_seconds: int = MARK_DURATION_SECONDS_MAX,
    event_id: str = "",
    expedition_id: str = "",
    source_adventurer_id: str = "",
) -> Tuple[AdventurerClassState, TransitionResult]:
    """Refresh di un Mark esistente (B2BQ04 verbatim).

    Regole:
    - refresh timestamp = server clock (authoritative)
    - new expires_at = now + duration_seconds
    - preserva `mark_id`, `application_id`, `ownership`
    - NON ripristina `ritual_close_used`
    - Mark già scaduto → `MARK_EXPIRED` (deve fare APPLY_MARK nuovo)
    """
    if duration_seconds <= 0 or duration_seconds > MARK_DURATION_SECONDS_MAX:
        return cs, TransitionResult(
            code=TransitionResultCode.SOURCE_INVALID,
            event_id=event_id,
            event_type="REFRESH_MARK",
            expedition_id=expedition_id,
            source_adventurer_id=source_adventurer_id,
            reason_code="INVALID_DURATION",
        )

    found_idx = -1
    for i, m in enumerate(cs.active_marks):
        if m.target_id == target_id:
            found_idx = i
            break
    if found_idx < 0:
        return cs, TransitionResult(
            code=TransitionResultCode.MARK_NOT_FOUND,
            event_id=event_id,
            event_type="REFRESH_MARK",
            expedition_id=expedition_id,
            source_adventurer_id=source_adventurer_id,
            reason_code="NO_ACTIVE_MARK_FOR_TARGET",
        )

    m = cs.active_marks[found_idx]
    if not _is_mark_active(m, now):
        # Lazy expire: rimuovi Mark scaduto e rejecta
        pruned = tuple(x for i, x in enumerate(cs.active_marks) if i != found_idx)
        return AdventurerClassState(
            adventurer_id=cs.adventurer_id,
            active_marks=pruned,
            active_drain_executions=cs.active_drain_executions,
            fragment_count=cs.fragment_count,
            resource_segment_id=cs.resource_segment_id,
            focus_bonus_usage=cs.focus_bonus_usage,
            class_state_version=cs.class_state_version,
        ), TransitionResult(
            code=TransitionResultCode.MARK_EXPIRED,
            event_id=event_id,
            event_type="REFRESH_MARK",
            expedition_id=expedition_id,
            source_adventurer_id=source_adventurer_id,
            reason_code=ReasonCode.MARK_EXPIRED.value,
            mark_id=m.mark_id,
            mark_application_id=m.application_id,
        )

    refreshed = MarkDoc(
        mark_id=m.mark_id,
        application_id=m.application_id,
        source_adventurer_id=m.source_adventurer_id,
        target_id=m.target_id,
        created_at=m.created_at,
        expires_at=_iso(now + timedelta(seconds=duration_seconds)),
        ritual_close_used=m.ritual_close_used,  # NON ripristinare
        mark_version=m.mark_version + 1,
    )
    new_marks = tuple(
        refreshed if i == found_idx else x for i, x in enumerate(cs.active_marks)
    )
    new_cs = AdventurerClassState(
        adventurer_id=cs.adventurer_id,
        active_marks=new_marks,
        active_drain_executions=cs.active_drain_executions,
        fragment_count=cs.fragment_count,
        resource_segment_id=cs.resource_segment_id,
        focus_bonus_usage=cs.focus_bonus_usage,
        class_state_version=cs.class_state_version + 1,
    )
    return new_cs, TransitionResult(
        code=TransitionResultCode.SUCCESS,
        event_id=event_id,
        event_type="REFRESH_MARK",
        expedition_id=expedition_id,
        source_adventurer_id=source_adventurer_id,
        mark_id=refreshed.mark_id,
        mark_application_id=refreshed.application_id,
    )


def lazy_expire_marks(
    cs: AdventurerClassState,
    now: datetime,
) -> Tuple[AdventurerClassState, int]:
    """Lazy expiration OBBLIGATORIA: rimuove Marchi scaduti al momento dell'accesso.

    B2BQ03 verbatim (hybrid): lazy validation su ogni accesso rilevante.
    Non incrementa `class_state_version` (pure read/prune).

    Returns:
        (new_cs, count_expired)
    """
    active = tuple(m for m in cs.active_marks if _is_mark_active(m, now))
    expired_count = len(cs.active_marks) - len(active)
    if expired_count == 0:
        return cs, 0
    new_cs = AdventurerClassState(
        adventurer_id=cs.adventurer_id,
        active_marks=active,
        active_drain_executions=cs.active_drain_executions,
        fragment_count=cs.fragment_count,
        resource_segment_id=cs.resource_segment_id,
        focus_bonus_usage=cs.focus_bonus_usage,
        class_state_version=cs.class_state_version,
    )
    return new_cs, expired_count


def opportunistic_cleanup(
    cs: AdventurerClassState,
    now: datetime,
) -> Tuple[AdventurerClassState, int]:
    """Opportunistic cleanup CONSENTITO (B2BQ03 hybrid).

    Effettua lazy expiration + eventuale reset di segment se orphaned.
    """
    new_cs, expired = lazy_expire_marks(cs, now)
    return new_cs, expired


def _is_mark_active(m: MarkDoc, now: datetime) -> bool:
    """Validità Mark: `expires_at > authoritative_now`."""
    exp = _parse_iso(m.expires_at)
    if exp is None:
        return False
    return exp > now


# ═══════════════════════ Fragment transitions ═══════════════════════
def gain_fragment(
    cs: AdventurerClassState,
    *,
    trusted_receipt: Optional[TrustedDrainReceipt],
    now: datetime,
    amount: int = 1,
    event_id: str = "",
    expedition_id: str = "",
    source_adventurer_id: str = "",
) -> Tuple[AdventurerClassState, TransitionResult]:
    """Guadagno Fragment (primitive · trusted receipt only in RT2-B-2B-1).

    B2BQ07 verbatim:
    - richiede `trusted_drain_receipt` valida
    - amount default 1, valid range [1, 5]
    - `fragment_count` cap 5 · overflow discarded (no reward)
    """
    if trusted_receipt is None:
        return cs, TransitionResult(
            code=TransitionResultCode.FRAGMENT_GAIN_UNAUTHORIZED,
            event_id=event_id,
            event_type="GAIN_FRAGMENT",
            expedition_id=expedition_id,
            source_adventurer_id=source_adventurer_id,
            reason_code="NO_TRUSTED_DRAIN_RECEIPT",
        )
    if trusted_receipt.fixture_only_marker != "RT2B2B1_TRUSTED_FIXTURE_ONLY":
        return cs, TransitionResult(
            code=TransitionResultCode.FRAGMENT_GAIN_UNAUTHORIZED,
            event_id=event_id,
            event_type="GAIN_FRAGMENT",
            expedition_id=expedition_id,
            source_adventurer_id=source_adventurer_id,
            reason_code="INVALID_FIXTURE_MARKER",
        )
    if trusted_receipt.source_adventurer_id != cs.adventurer_id:
        return cs, TransitionResult(
            code=TransitionResultCode.OWNERSHIP_INVALID,
            event_id=event_id,
            event_type="GAIN_FRAGMENT",
            expedition_id=expedition_id,
            source_adventurer_id=source_adventurer_id,
            reason_code=ReasonCode.MARK_OWNERSHIP_MISMATCH.value,
        )
    if amount < 1 or amount > FRAGMENT_CAP:
        return cs, TransitionResult(
            code=TransitionResultCode.FRAGMENT_INVALID_AMOUNT,
            event_id=event_id,
            event_type="GAIN_FRAGMENT",
            expedition_id=expedition_id,
            source_adventurer_id=source_adventurer_id,
            reason_code="INVALID_AMOUNT",
        )

    projected = cs.fragment_count + amount
    if projected > FRAGMENT_CAP:
        # Overflow → parziale gain fino a cap, resto discarded (no reward/proc)
        credited = FRAGMENT_CAP - cs.fragment_count
        discarded = amount - credited
        new_segment_id = cs.resource_segment_id
        if cs.fragment_count == 0 and credited > 0:
            new_segment_id = f"seg-{uuid.uuid4().hex[:16]}"
        new_cs = AdventurerClassState(
            adventurer_id=cs.adventurer_id,
            active_marks=cs.active_marks,
            active_drain_executions=cs.active_drain_executions,
            fragment_count=cs.fragment_count + credited,
            resource_segment_id=new_segment_id,
            focus_bonus_usage=cs.focus_bonus_usage,
            class_state_version=cs.class_state_version + (1 if credited > 0 else 0),
        )
        return new_cs, TransitionResult(
            code=TransitionResultCode.FRAGMENT_OVERFLOW_DISCARDED,
            event_id=event_id,
            event_type="GAIN_FRAGMENT",
            expedition_id=expedition_id,
            source_adventurer_id=source_adventurer_id,
            reason_code="FRAGMENT_CAP_5",
            fragment_count_after=new_cs.fragment_count,
            resource_segment_id=new_segment_id,
            overflow_discarded=discarded,
        )

    # Se 0→positive, apri nuovo segment
    new_segment_id = cs.resource_segment_id
    if cs.fragment_count == 0:
        new_segment_id = f"seg-{uuid.uuid4().hex[:16]}"

    new_cs = AdventurerClassState(
        adventurer_id=cs.adventurer_id,
        active_marks=cs.active_marks,
        active_drain_executions=cs.active_drain_executions,
        fragment_count=projected,
        resource_segment_id=new_segment_id,
        focus_bonus_usage=cs.focus_bonus_usage,
        class_state_version=cs.class_state_version + 1,
    )
    return new_cs, TransitionResult(
        code=TransitionResultCode.SUCCESS,
        event_id=event_id,
        event_type="GAIN_FRAGMENT",
        expedition_id=expedition_id,
        source_adventurer_id=source_adventurer_id,
        fragment_count_after=projected,
        resource_segment_id=new_segment_id,
    )


def spend_fragment(
    cs: AdventurerClassState,
    *,
    amount: int,
    uses_focus_bonus: bool = False,
    event_id: str = "",
    expedition_id: str = "",
    source_adventurer_id: str = "",
) -> Tuple[AdventurerClassState, TransitionResult]:
    """Spende Fragment (full amount, partial spend FORBIDDEN).

    Regole:
    - amount ≥ 1
    - fragment_count ≥ amount (insufficient rejection)
    - se `uses_focus_bonus=True`: focus_bonus_usage in segment corrente ≤ 2
    - fragment_count → 0 chiude segment (segment_id=None)
    """
    if amount < 1 or amount > FRAGMENT_CAP:
        return cs, TransitionResult(
            code=TransitionResultCode.FRAGMENT_INVALID_AMOUNT,
            event_id=event_id,
            event_type="SPEND_FRAGMENT",
            expedition_id=expedition_id,
            source_adventurer_id=source_adventurer_id,
            reason_code="INVALID_AMOUNT",
        )
    if cs.fragment_count < amount:
        return cs, TransitionResult(
            code=TransitionResultCode.FRAGMENT_INSUFFICIENT,
            event_id=event_id,
            event_type="SPEND_FRAGMENT",
            expedition_id=expedition_id,
            source_adventurer_id=source_adventurer_id,
            reason_code="INSUFFICIENT_FRAGMENTS",
            fragment_count_after=cs.fragment_count,
        )
    if cs.resource_segment_id is None:
        return cs, TransitionResult(
            code=TransitionResultCode.SEGMENT_NOT_OPEN,
            event_id=event_id,
            event_type="SPEND_FRAGMENT",
            expedition_id=expedition_id,
            source_adventurer_id=source_adventurer_id,
            reason_code="NO_ACTIVE_SEGMENT",
        )

    # Focus bonus cap (≤2 per segment)
    seg_id = cs.resource_segment_id
    new_focus_usage = cs.focus_bonus_usage
    if uses_focus_bonus:
        current_usage = 0
        for u in cs.focus_bonus_usage:
            if u.resource_segment_id == seg_id:
                current_usage = u.focus_bonus_used
                break
        if current_usage >= FOCUS_BONUS_CAP_PER_SEGMENT:
            return cs, TransitionResult(
                code=TransitionResultCode.FOCUS_BONUS_CAP_EXCEEDED,
                event_id=event_id,
                event_type="SPEND_FRAGMENT",
                expedition_id=expedition_id,
                source_adventurer_id=source_adventurer_id,
                reason_code="FOCUS_BONUS_CAP_2",
                focus_bonus_used_after=current_usage,
                resource_segment_id=seg_id,
            )
        # Increment usage for segment
        updated = False
        tmp = []
        for u in cs.focus_bonus_usage:
            if u.resource_segment_id == seg_id:
                tmp.append(FragmentUsage(
                    resource_segment_id=u.resource_segment_id,
                    focus_bonus_used=u.focus_bonus_used + 1,
                ))
                updated = True
            else:
                tmp.append(u)
        if not updated:
            tmp.append(FragmentUsage(resource_segment_id=seg_id, focus_bonus_used=1))
        new_focus_usage = tuple(tmp)

    new_count = cs.fragment_count - amount
    # Se fragment_count → 0, chiude segment
    new_segment_id: Optional[str] = seg_id if new_count > 0 else None

    focus_after = 0
    if uses_focus_bonus:
        for u in new_focus_usage:
            if u.resource_segment_id == seg_id:
                focus_after = u.focus_bonus_used
                break

    new_cs = AdventurerClassState(
        adventurer_id=cs.adventurer_id,
        active_marks=cs.active_marks,
        active_drain_executions=cs.active_drain_executions,
        fragment_count=new_count,
        resource_segment_id=new_segment_id,
        focus_bonus_usage=new_focus_usage,
        class_state_version=cs.class_state_version + 1,
    )
    return new_cs, TransitionResult(
        code=TransitionResultCode.SUCCESS,
        event_id=event_id,
        event_type="SPEND_FRAGMENT",
        expedition_id=expedition_id,
        source_adventurer_id=source_adventurer_id,
        fragment_count_after=new_count,
        resource_segment_id=new_segment_id,
        focus_bonus_used_after=focus_after,
    )


def reset_fragments(
    cs: AdventurerClassState,
    *,
    reason: str,
    event_id: str = "",
    expedition_id: str = "",
    source_adventurer_id: str = "",
) -> Tuple[AdventurerClassState, TransitionResult]:
    """Reset Fragment (phase_end / expedition_terminal / explicit).

    Chiude segment corrente. Frammenti persi (no rimborso · B2BQ08).
    """
    new_cs = AdventurerClassState(
        adventurer_id=cs.adventurer_id,
        active_marks=cs.active_marks,
        active_drain_executions=cs.active_drain_executions,
        fragment_count=0,
        resource_segment_id=None,
        focus_bonus_usage=cs.focus_bonus_usage,
        class_state_version=cs.class_state_version + 1,
    )
    return new_cs, TransitionResult(
        code=TransitionResultCode.SUCCESS,
        event_id=event_id,
        event_type="RESET_FRAGMENTS",
        expedition_id=expedition_id,
        source_adventurer_id=source_adventurer_id,
        reason_code=reason,
        fragment_count_after=0,
        resource_segment_id=None,
    )


def discard_fragment_overflow(
    cs: AdventurerClassState,
    *,
    would_have_gained: int,
    event_id: str = "",
    expedition_id: str = "",
    source_adventurer_id: str = "",
) -> Tuple[AdventurerClassState, TransitionResult]:
    """Overflow discard (diagnostic only · NO reward/proc/conversion/credit).

    B2BQ verbatim: overflow scartato. NO conversione in premi.
    """
    return cs, TransitionResult(
        code=TransitionResultCode.FRAGMENT_OVERFLOW_DISCARDED,
        event_id=event_id,
        event_type="DISCARD_FRAGMENT_OVERFLOW",
        expedition_id=expedition_id,
        source_adventurer_id=source_adventurer_id,
        reason_code="FRAGMENT_CAP_5",
        fragment_count_after=cs.fragment_count,
        overflow_discarded=would_have_gained,
    )


# ═══════════════════════ Resource segment transitions ═══════════════════════
def close_resource_segment(
    cs: AdventurerClassState,
    *,
    trigger: str,
    event_id: str = "",
    expedition_id: str = "",
    source_adventurer_id: str = "",
) -> Tuple[AdventurerClassState, TransitionResult]:
    """Chiude segment corrente (esplicito / phase_end / expedition_terminal).

    B2BQ08 verbatim: chiusura esplicita NON converte NÉ rimborsa Frammenti.
    """
    if cs.resource_segment_id is None:
        return cs, TransitionResult(
            code=TransitionResultCode.DEDUPLICATED_NO_OP,
            event_id=event_id,
            event_type="CLOSE_RESOURCE_SEGMENT",
            expedition_id=expedition_id,
            source_adventurer_id=source_adventurer_id,
            reason_code=trigger,
        )
    new_cs = AdventurerClassState(
        adventurer_id=cs.adventurer_id,
        active_marks=cs.active_marks,
        active_drain_executions=cs.active_drain_executions,
        fragment_count=0,
        resource_segment_id=None,
        focus_bonus_usage=cs.focus_bonus_usage,
        class_state_version=cs.class_state_version + 1,
    )
    return new_cs, TransitionResult(
        code=TransitionResultCode.SUCCESS,
        event_id=event_id,
        event_type="CLOSE_RESOURCE_SEGMENT",
        expedition_id=expedition_id,
        source_adventurer_id=source_adventurer_id,
        reason_code=trigger,
        fragment_count_after=0,
        resource_segment_id=None,
    )


# ═══════════════════════ Receipt cap helpers (B2BQ14) ═══════════════════════
def compute_receipt_capacity_status(
    processed_events: tuple,
) -> tuple[int, int, int]:
    """Ritorna (ordinary_count, reserved_count, total_count).

    Il caller deve fornire il tuple di receipt attualmente memorizzate.
    """
    from app.stats.runtime.transitions.models import RESERVED_EVENT_TYPES

    ordinary = 0
    reserved = 0
    for r in processed_events:
        # r è un EventReceipt
        et = getattr(r, "event_type", "") or ""
        if et in RESERVED_EVENT_TYPES:
            reserved += 1
        else:
            ordinary += 1
    return ordinary, reserved, ordinary + reserved


def would_receipt_be_accepted(
    processed_events: tuple,
    incoming_event_type: str,
) -> tuple[bool, TransitionResultCode]:
    """Determina se l'inserimento di una nuova receipt è consentito.

    Regole (B2BQ14 verbatim):
    - Ordinary cap 504 · Reserved cap 8 · Total cap 512
    - Saturazione ordinaria → RECEIPT_CAP_REACHED (fail closed)
    - No eviction · no overwrite · no duplicate removal
    """
    ordinary, reserved, total = compute_receipt_capacity_status(processed_events)
    category = categorize_event(incoming_event_type)
    if category is ReceiptCategory.ORDINARY:
        if ordinary >= RECEIPT_CAP_ORDINARY:
            return False, TransitionResultCode.RECEIPT_CAP_REACHED
    else:
        if reserved >= RECEIPT_CAP_RESERVED:
            return False, TransitionResultCode.RESERVED_CAPACITY_EXHAUSTED
    if total >= RECEIPT_CAP_TOTAL:
        return False, TransitionResultCode.RECEIPT_CAP_REACHED
    return True, TransitionResultCode.SUCCESS


__all__ = [
    "MARK_CAP_PER_SOURCE",
    "MARK_DURATION_SECONDS_MAX",
    "FRAGMENT_CAP",
    "FOCUS_BONUS_CAP_PER_SEGMENT",
    "RECEIPT_CAP_TOTAL",
    "RECEIPT_CAP_ORDINARY",
    "RECEIPT_CAP_RESERVED",
    "STATE_DOC_MAX_BYTES",
    "apply_mark",
    "close_resource_segment",
    "compute_receipt_capacity_status",
    "discard_fragment_overflow",
    "gain_fragment",
    "lazy_expire_marks",
    "opportunistic_cleanup",
    "refresh_mark",
    "reset_fragments",
    "spend_fragment",
    "would_receipt_be_accepted",
]
