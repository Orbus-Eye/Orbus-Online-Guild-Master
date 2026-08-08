"""Compact BSON projections and feasibility measurements for RT2-C-P1."""

from __future__ import annotations

from base64 import b64decode, urlsafe_b64encode
from dataclasses import dataclass
from hashlib import sha256
from typing import Callable, Mapping, Sequence

from .models import (
    EffectDuration,
    EffectInstance,
    EffectLifecycleStatus,
)
from .registry import EffectRegistry, MAX_ABS_MAGNITUDE, MAX_USE_COUNT
from .resolver import (
    APPLICATION_ID_MAX_BYTES,
    EFFECT_INSTANCE_ID_MAX_BYTES,
    MAX_ACTIVE_INSTANCES,
    instance_order_key,
)


ACTIVE_EFFECT_BSON_BUDGET = 6_144
BASELINE_FULL_CAP_BSON_BYTES = 230_593
PROJECTED_FULL_CAP_TARGET_BYTES = 245_760
STATE_DOC_HARD_LIMIT_BYTES = 262_144

_DURATION_CODES = {
    EffectDuration.INSTANT: "i",
    EffectDuration.UNTIL_PHASE_END: "p",
    EffectDuration.UNTIL_EXPEDITION_END: "e",
    EffectDuration.USE_COUNT: "u",
}
_DURATION_FROM_CODE = {code: duration for duration, code in _DURATION_CODES.items()}


@dataclass(frozen=True)
class BsonFeasibility:
    layout: str
    active_instance_count: int
    active_effect_bytes: int
    projected_full_cap_bytes: int
    within_active_effect_budget: bool
    within_projected_full_cap_target: bool
    within_hard_limit: bool

    @property
    def passed(self) -> bool:
        return (
            self.within_active_effect_budget
            and self.within_projected_full_cap_target
            and self.within_hard_limit
        )


def _entry(instance: EffectInstance, *, include_target: bool = True) -> dict:
    if instance.lifecycle_status is not EffectLifecycleStatus.ACTIVE:
        raise ValueError("ONLY_ACTIVE_INSTANCES_CAN_BE_PROJECTED")
    # primitive, target_key and definition_priority are deliberately omitted:
    # the exact versioned static definition is authoritative for those values.
    entry = {
        "i": instance.effect_instance_id,
        "e": instance.effect_id,
        "v": instance.effect_version,
        "s": instance.source_adventurer_id,
        "a": instance.application_id,
        "q": instance.root_event_sequence,
        "m": instance.resolved_magnitude,
        "d": _DURATION_CODES[instance.duration],
        "n": instance.stack_count,
    }
    if include_target:
        entry["t"] = instance.target_id
    if instance.remaining_uses is not None:
        entry["u"] = instance.remaining_uses
    return entry


def project_layout_a(instances: Sequence[EffectInstance]) -> dict:
    """Layout A: one compact, globally ordered array."""

    ordered = sorted(instances, key=instance_order_key)
    return {"v": 1, "a": [_entry(instance) for instance in ordered]}


def project_layout_b(instances: Sequence[EffectInstance]) -> dict:
    """Layout B: Mongo-safe target-keyed buckets (recommended P1 target)."""

    buckets: dict[str, list[dict]] = {}
    for instance in sorted(instances, key=instance_order_key):
        # Reversible base64url keeps Mongo field names free from '$', '.' and
        # NUL while avoiding a second copy of the bounded target identifier.
        target_token = "t_" + urlsafe_b64encode(
            instance.target_id.encode("utf-8")
        ).decode("ascii").rstrip("=")
        buckets.setdefault(target_token, []).append(
            _entry(instance, include_target=False)
        )
    return {"v": 1, "t": buckets}


def project_layout_c(instances: Sequence[EffectInstance]) -> dict:
    """Layout C: Mongo-safe effect-version keyed buckets for comparison."""

    buckets: dict[str, dict] = {}
    for instance in sorted(instances, key=instance_order_key):
        identity = f"{instance.effect_id}@{instance.effect_version}"
        key = "e_" + sha256(identity.encode("utf-8")).hexdigest()[:32]
        entry = _entry(instance)
        entry.pop("e")
        entry.pop("v")
        bucket = buckets.setdefault(
            key,
            {"i": instance.effect_id, "v": instance.effect_version, "a": []},
        )
        bucket["a"].append(entry)
    return {"v": 1, "e": buckets}


def _target_from_token(token: str) -> str:
    if not isinstance(token, str) or not token.startswith("t_"):
        raise ValueError("TARGET_TOKEN_INVALID")
    encoded = token[2:]
    try:
        padded = encoded + ("=" * (-len(encoded) % 4))
        target = b64decode(
            padded.encode("ascii"),
            altchars=b"-_",
            validate=True,
        ).decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError, ValueError) as exc:
        raise ValueError("TARGET_TOKEN_INVALID") from exc
    canonical = "t_" + urlsafe_b64encode(target.encode("utf-8")).decode("ascii").rstrip(
        "="
    )
    if canonical != token:
        raise ValueError("TARGET_TOKEN_NOT_CANONICAL")
    return target


def rehydrate_layout_b(
    projection: Mapping | None,
    registry: EffectRegistry,
) -> tuple[EffectInstance, ...]:
    """Rehydrate the P2 target-keyed persistence layout fail-closed.

    Primitive, target key and priority are restored only from the exact
    versioned static definition. Unknown definitions never become partially
    typed runtime state.
    """

    if projection in (None, {}):
        return ()
    if not isinstance(projection, Mapping) or projection.get("v") != 1:
        raise ValueError("EFFECT_LAYOUT_VERSION_INVALID")
    buckets = projection.get("t")
    if not isinstance(buckets, Mapping):
        raise ValueError("EFFECT_TARGET_BUCKETS_INVALID")

    instances: list[EffectInstance] = []
    seen_ids: set[str] = set()
    if any(not isinstance(token, str) for token in buckets):
        raise ValueError("TARGET_TOKEN_INVALID")
    for token in sorted(buckets):
        target_id = _target_from_token(token)
        if not target_id or len(target_id.encode("utf-8")) > 64:
            raise ValueError("TARGET_ID_INVALID")
        entries = buckets[token]
        if not isinstance(entries, list):
            raise ValueError("EFFECT_TARGET_BUCKET_INVALID")
        for raw in entries:
            if not isinstance(raw, Mapping):
                raise ValueError("EFFECT_ENTRY_INVALID")
            allowed_fields = {"i", "e", "v", "s", "a", "q", "m", "d", "n", "u"}
            required_fields = allowed_fields - {"u"}
            if not required_fields.issubset(raw):
                raise ValueError("EFFECT_ENTRY_FIELDS_MISSING")
            if not set(raw).issubset(allowed_fields):
                raise ValueError("EFFECT_ENTRY_FIELDS_UNEXPECTED")
            effect_id = raw.get("e")
            version = raw.get("v")
            if not isinstance(effect_id, str) or type(version) is not int:
                raise ValueError("EFFECT_DEFINITION_IDENTITY_INVALID")
            definition = registry.get(effect_id, version)
            if definition is None:
                reason = (
                    "EFFECT_VERSION_MISMATCH"
                    if registry.has_effect_id(effect_id)
                    else "EFFECT_DEFINITION_UNKNOWN"
                )
                raise ValueError(reason)

            instance_id = raw.get("i")
            source_id = raw.get("s")
            application_id = raw.get("a")
            sequence = raw.get("q")
            magnitude = raw.get("m")
            stack_count = raw.get("n")
            if (
                not isinstance(instance_id, str)
                or not instance_id
                or len(instance_id.encode("utf-8")) > EFFECT_INSTANCE_ID_MAX_BYTES
            ):
                raise ValueError("EFFECT_INSTANCE_ID_INVALID")
            if instance_id in seen_ids:
                raise ValueError("EFFECT_INSTANCE_ID_DUPLICATED")
            if (
                not isinstance(source_id, str)
                or not source_id
                or len(source_id.encode("utf-8")) > 64
            ):
                raise ValueError("SOURCE_ID_INVALID")
            if (
                not isinstance(application_id, str)
                or not application_id
                or len(application_id.encode("utf-8")) > APPLICATION_ID_MAX_BYTES
            ):
                raise ValueError("APPLICATION_ID_INVALID")
            if type(sequence) is not int or sequence < 1:
                raise ValueError("ROOT_EVENT_SEQUENCE_INVALID")
            if type(magnitude) is not int or abs(magnitude) > MAX_ABS_MAGNITUDE:
                raise ValueError("RESOLVED_MAGNITUDE_INVALID")
            if (
                type(stack_count) is not int
                or stack_count < 1
                or stack_count > definition.stack_cap
            ):
                raise ValueError("STACK_COUNT_INVALID")

            duration = _DURATION_FROM_CODE.get(raw.get("d"))
            if duration is None or duration is not definition.duration:
                raise ValueError("EFFECT_DURATION_INVALID")
            if duration is EffectDuration.INSTANT:
                raise ValueError("INSTANT_EFFECT_CANNOT_BE_ACTIVE")
            remaining_uses = raw.get("u")
            if duration is EffectDuration.USE_COUNT:
                if (
                    type(remaining_uses) is not int
                    or not 1 <= remaining_uses <= MAX_USE_COUNT
                ):
                    raise ValueError("REMAINING_USES_INVALID")
            elif remaining_uses is not None:
                raise ValueError("REMAINING_USES_UNEXPECTED")

            seen_ids.add(instance_id)
            instances.append(
                EffectInstance(
                    effect_instance_id=instance_id,
                    effect_id=effect_id,
                    effect_version=version,
                    source_adventurer_id=source_id,
                    target_id=target_id,
                    application_id=application_id,
                    root_event_sequence=sequence,
                    primitive=definition.primitive,
                    target_key=definition.target_key,
                    resolved_magnitude=magnitude,
                    duration=duration,
                    remaining_uses=remaining_uses,
                    stack_count=stack_count,
                    definition_priority=definition.priority,
                    lifecycle_status=EffectLifecycleStatus.ACTIVE,
                )
            )
    if len(instances) > MAX_ACTIVE_INSTANCES:
        raise ValueError("ACTIVE_INSTANCE_CAP_EXCEEDED")
    return tuple(sorted(instances, key=instance_order_key))


_LAYOUTS: Mapping[str, Callable[[Sequence[EffectInstance]], dict]] = {
    "A": project_layout_a,
    "B": project_layout_b,
    "C": project_layout_c,
}


def bson_size(
    document: Mapping,
    *,
    encoder: Callable[[Mapping], bytes] | None = None,
) -> int:
    """Measure raw BSON bytes; an encoder can be injected for pure unit tests."""

    if encoder is None:
        from bson import BSON

        encoder = BSON.encode
    return len(encoder(document))


def measure_bson_feasibility(
    instances: Sequence[EffectInstance],
    *,
    layout: str = "B",
    baseline_full_cap_bytes: int = BASELINE_FULL_CAP_BSON_BYTES,
    encoder: Callable[[Mapping], bytes] | None = None,
) -> BsonFeasibility:
    if layout not in _LAYOUTS:
        raise ValueError("UNKNOWN_LAYOUT")
    if len(instances) > MAX_ACTIVE_INSTANCES:
        raise ValueError("ACTIVE_INSTANCE_CAP_EXCEEDED")
    projection = _LAYOUTS[layout](instances)
    active_bytes = bson_size(projection, encoder=encoder)
    projected = baseline_full_cap_bytes + active_bytes
    return BsonFeasibility(
        layout=layout,
        active_instance_count=len(instances),
        active_effect_bytes=active_bytes,
        projected_full_cap_bytes=projected,
        within_active_effect_budget=active_bytes <= ACTIVE_EFFECT_BSON_BUDGET,
        within_projected_full_cap_target=projected <= PROJECTED_FULL_CAP_TARGET_BYTES,
        within_hard_limit=projected <= STATE_DOC_HARD_LIMIT_BYTES,
    )


__all__ = [
    "ACTIVE_EFFECT_BSON_BUDGET",
    "BASELINE_FULL_CAP_BSON_BYTES",
    "BsonFeasibility",
    "PROJECTED_FULL_CAP_TARGET_BYTES",
    "STATE_DOC_HARD_LIMIT_BYTES",
    "bson_size",
    "measure_bson_feasibility",
    "project_layout_a",
    "project_layout_b",
    "project_layout_c",
    "rehydrate_layout_b",
]
