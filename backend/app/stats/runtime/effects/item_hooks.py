"""Fail-closed bridge from equipped item metadata to generic effects.

Item documents may only reference static definitions.  They cannot provide a
primitive, magnitude, duration, target or stacking rule.  Effect-bearing
items must also carry reviewed lore metadata and a stable singular blueprint
identity before this bridge will produce an :class:`EffectRequest`.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable, Mapping, Optional

from app.stats.runtime.effects.models import (
    EffectRequest,
    EffectTargetScope,
    EffectTrigger,
)
from app.stats.runtime.effects.registry import EffectRegistry


ITEM_EFFECT_SCHEMA_VERSION = 1
MAX_ITEM_EFFECTS_PER_EVENT = 8
MAX_ITEM_BLUEPRINT_ID_BYTES = 64
MAX_ROOT_EVENT_ID_BYTES = 64
CLASSLESS_SLUGS = frozenset(("", "recruit_unassigned"))

_ALLOWED_METADATA_FIELDS = frozenset(
    (
        "schema_version",
        "effect_id",
        "effect_version",
        "lore_key",
        "effect_summary_it",
        "effect_summary_en",
        "enabled",
    )
)


class ItemEffectHookError(ValueError):
    """Raised when an effect-bearing item fails the server-side contract."""


@dataclass(frozen=True)
class ItemEffectHookEvent:
    expedition_id: str
    root_event_id: str
    root_event_sequence: int
    trigger: EffectTrigger
    source_adventurer_id: str
    target_id: str
    adventurer_class_slug: str


@dataclass(frozen=True)
class InactiveItemEffect:
    item_blueprint_id: str
    reason_code: str


@dataclass(frozen=True)
class ItemEffectHookCompilation:
    requests: tuple[EffectRequest, ...]
    inactive: tuple[InactiveItemEffect, ...] = ()


def canonical_item_blueprint_id(item: Mapping[str, object]) -> str:
    """Return the stable singular blueprint identity for an item document.

    ``blueprint_id`` is preferred for future registry rows, then the stable
    catalog ``slug``.  Mongo UUID ``id`` is a legacy fallback only.
    """

    for field in ("blueprint_id", "slug", "id"):
        value = item.get(field)
        if isinstance(value, str) and value.strip():
            identity = value.strip()
            if len(identity.encode("utf-8")) > MAX_ITEM_BLUEPRINT_ID_BYTES:
                raise ItemEffectHookError("ITEM_BLUEPRINT_ID_TOO_LONG")
            return identity
    raise ItemEffectHookError("ITEM_BLUEPRINT_ID_MISSING")


def _require_bounded(value: object, *, code: str, max_bytes: int = 64) -> str:
    if not isinstance(value, str) or not value:
        raise ItemEffectHookError(f"{code}_MISSING")
    if len(value.encode("utf-8")) > max_bytes:
        raise ItemEffectHookError(f"{code}_TOO_LONG")
    return value


def _validate_event(event: ItemEffectHookEvent) -> str:
    _require_bounded(event.expedition_id, code="EXPEDITION_ID")
    _require_bounded(
        event.root_event_id,
        code="ROOT_EVENT_ID",
        max_bytes=MAX_ROOT_EVENT_ID_BYTES,
    )
    _require_bounded(event.source_adventurer_id, code="SOURCE_ADVENTURER_ID")
    _require_bounded(event.target_id, code="TARGET_ID")
    if type(event.root_event_sequence) is not int or event.root_event_sequence < 1:
        raise ItemEffectHookError("ROOT_EVENT_SEQUENCE_INVALID")
    if not isinstance(event.trigger, EffectTrigger):
        raise ItemEffectHookError("TRIGGER_INVALID")
    class_slug = (
        event.adventurer_class_slug.strip().lower()
        if isinstance(event.adventurer_class_slug, str)
        else ""
    )
    if class_slug in CLASSLESS_SLUGS:
        raise ItemEffectHookError("CLASS_REQUIRED_FOR_ITEM_EFFECT")
    return class_slug


def _string_tags(item: Mapping[str, object], field: str) -> tuple[str, ...]:
    raw = item.get(field)
    if raw is None:
        return ()
    if not isinstance(raw, (list, tuple)):
        raise ItemEffectHookError(f"{field.upper()}_INVALID")
    tags = tuple(str(value).strip().lower() for value in raw if str(value).strip())
    if len(tags) != len(set(tags)):
        raise ItemEffectHookError(f"{field.upper()}_DUPLICATED")
    return tags


def _effect_metadata(
    item: Mapping[str, object],
    *,
    blueprint_id: str,
) -> Optional[Mapping[str, object]]:
    raw = item.get("effect_metadata")
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        raise ItemEffectHookError(f"ITEM_EFFECT_METADATA_INVALID:{blueprint_id}")
    unknown = set(raw) - _ALLOWED_METADATA_FIELDS
    if unknown:
        raise ItemEffectHookError(f"ITEM_EFFECT_METADATA_UNKNOWN_FIELDS:{blueprint_id}")
    enabled = raw.get("enabled", True)
    if type(enabled) is not bool:
        raise ItemEffectHookError(f"ITEM_EFFECT_ENABLED_INVALID:{blueprint_id}")
    if enabled is False:
        return raw
    if raw.get("schema_version") != ITEM_EFFECT_SCHEMA_VERSION:
        raise ItemEffectHookError(f"ITEM_EFFECT_SCHEMA_INVALID:{blueprint_id}")
    _require_bounded(raw.get("effect_id"), code="EFFECT_ID")
    if type(raw.get("effect_version")) is not int or raw["effect_version"] < 1:
        raise ItemEffectHookError(f"EFFECT_VERSION_INVALID:{blueprint_id}")
    _require_bounded(raw.get("lore_key"), code="LORE_KEY", max_bytes=32)
    _require_bounded(
        raw.get("effect_summary_it"),
        code="EFFECT_SUMMARY_IT",
        max_bytes=240,
    )
    return raw


def _validate_lore(
    item: Mapping[str, object],
    metadata: Mapping[str, object],
    *,
    blueprint_id: str,
) -> None:
    if item.get("lore_reviewed") is not True:
        raise ItemEffectHookError(f"ITEM_LORE_NOT_REVIEWED:{blueprint_id}")
    lore_tags = _string_tags(item, "lore_tags")
    lore_key = str(metadata["lore_key"]).strip().lower()
    if lore_key not in lore_tags:
        raise ItemEffectHookError(f"ITEM_LORE_KEY_NOT_TAGGED:{blueprint_id}")
    has_copy = any(
        isinstance(item.get(field), str) and bool(str(item.get(field)).strip())
        for field in ("flavor_text_it", "lore_source", "description_it")
    )
    if not has_copy:
        raise ItemEffectHookError(f"ITEM_LORE_COPY_MISSING:{blueprint_id}")


def _class_effect_is_active(
    item: Mapping[str, object],
    *,
    class_slug: str,
    blueprint_id: str,
) -> bool:
    policy = str(item.get("item_binding_policy") or "").strip().lower()
    if policy not in {"hard", "soft", "universal"}:
        raise ItemEffectHookError(f"ITEM_BINDING_POLICY_INVALID:{blueprint_id}")
    required = str(item.get("required_class_optional") or "").strip().lower()
    recommended = set(_string_tags(item, "recommended_classes"))
    class_tags = set(_string_tags(item, "class_tags"))
    compatible = recommended | class_tags
    if policy == "hard":
        if not required and not compatible:
            raise ItemEffectHookError(f"HARD_ITEM_CLASS_MISSING:{blueprint_id}")
        if class_slug != required and class_slug not in compatible:
            raise ItemEffectHookError(f"HARD_ITEM_CLASS_MISMATCH:{blueprint_id}")
        return True
    if policy == "soft" and compatible and class_slug not in compatible:
        return False
    return True


def _derived_ids(
    *,
    event: ItemEffectHookEvent,
    blueprint_id: str,
    effect_id: str,
    effect_version: int,
) -> tuple[str, str]:
    token = "|".join(
        (
            event.expedition_id,
            event.root_event_id,
            event.source_adventurer_id,
            blueprint_id,
            effect_id,
            str(effect_version),
            event.trigger.value,
        )
    )
    digest = sha256(token.encode("utf-8")).hexdigest()
    return f"ie-{digest[:40]}", f"itm-{digest[:28]}"


def compile_item_effect_requests(
    *,
    event: ItemEffectHookEvent,
    equipment_items: Iterable[Mapping[str, object]] | None,
    registry: EffectRegistry,
) -> ItemEffectHookCompilation:
    """Compile deterministic requests for the matching equipped item effects.

    Legacy items without ``effect_metadata`` are valid and ignored.  Any
    malformed effect-bearing item fails the whole compilation before a store
    or dispatcher can be reached.
    """

    class_slug = _validate_event(event)
    if not isinstance(registry, EffectRegistry):
        raise ItemEffectHookError("EFFECT_REGISTRY_INVALID")

    prepared: list[tuple[str, Mapping[str, object]]] = []
    seen_blueprints: set[str] = set()
    seen_names: set[str] = set()
    for item in equipment_items or ():
        if not isinstance(item, Mapping):
            raise ItemEffectHookError("EQUIPMENT_ITEM_INVALID")
        blueprint_id = canonical_item_blueprint_id(item)
        if blueprint_id in seen_blueprints:
            raise ItemEffectHookError(f"ITEM_BLUEPRINT_DUPLICATED:{blueprint_id}")
        seen_blueprints.add(blueprint_id)
        metadata = _effect_metadata(item, blueprint_id=blueprint_id)
        if metadata is None:
            continue
        display_name = str(
            item.get("display_name_it") or item.get("name") or ""
        ).strip()
        if not display_name:
            raise ItemEffectHookError(f"ITEM_DISPLAY_NAME_MISSING:{blueprint_id}")
        folded_name = display_name.casefold()
        if folded_name in seen_names:
            raise ItemEffectHookError(f"ITEM_DISPLAY_NAME_DUPLICATED:{display_name}")
        seen_names.add(folded_name)
        prepared.append((blueprint_id, item))

    requests: list[EffectRequest] = []
    inactive: list[InactiveItemEffect] = []
    for blueprint_id, item in sorted(prepared, key=lambda pair: pair[0]):
        metadata = _effect_metadata(item, blueprint_id=blueprint_id)
        if metadata is None:  # defensive
            continue
        if metadata.get("enabled", True) is False:
            inactive.append(InactiveItemEffect(blueprint_id, "ITEM_EFFECT_DISABLED"))
            continue
        _validate_lore(item, metadata, blueprint_id=blueprint_id)
        if not _class_effect_is_active(
            item,
            class_slug=class_slug,
            blueprint_id=blueprint_id,
        ):
            inactive.append(
                InactiveItemEffect(blueprint_id, "OFF_CLASS_EFFECT_INACTIVE")
            )
            continue

        effect_id = str(metadata["effect_id"])
        effect_version = int(metadata["effect_version"])
        definition = registry.get(effect_id, effect_version)
        if definition is None:
            raise ItemEffectHookError(f"ITEM_EFFECT_DEFINITION_UNKNOWN:{blueprint_id}")
        lore_key = str(metadata["lore_key"]).strip().lower()
        if "item" not in definition.tags or lore_key not in definition.tags:
            raise ItemEffectHookError(
                f"ITEM_EFFECT_DEFINITION_LORE_MISMATCH:{blueprint_id}"
            )
        if definition.trigger is not event.trigger:
            inactive.append(InactiveItemEffect(blueprint_id, "TRIGGER_NOT_MATCHED"))
            continue

        event_id, application_id = _derived_ids(
            event=event,
            blueprint_id=blueprint_id,
            effect_id=effect_id,
            effect_version=effect_version,
        )
        target_id = (
            event.source_adventurer_id
            if definition.target_scope is EffectTargetScope.SELF
            else event.target_id
        )
        requests.append(
            EffectRequest(
                expedition_id=event.expedition_id,
                event_id=event_id,
                root_event_sequence=event.root_event_sequence,
                effect_id=effect_id,
                effect_version=effect_version,
                trigger=event.trigger,
                source_adventurer_id=event.source_adventurer_id,
                target_id=target_id,
                application_id=application_id,
                idempotency_key=event_id,
            )
        )

    if len(requests) > MAX_ITEM_EFFECTS_PER_EVENT:
        raise ItemEffectHookError("ITEM_EFFECTS_PER_EVENT_CAP_EXCEEDED")
    return ItemEffectHookCompilation(
        requests=tuple(requests),
        inactive=tuple(inactive),
    )


__all__ = [
    "CLASSLESS_SLUGS",
    "ITEM_EFFECT_SCHEMA_VERSION",
    "MAX_ITEM_BLUEPRINT_ID_BYTES",
    "MAX_ITEM_EFFECTS_PER_EVENT",
    "InactiveItemEffect",
    "ItemEffectHookCompilation",
    "ItemEffectHookError",
    "ItemEffectHookEvent",
    "canonical_item_blueprint_id",
    "compile_item_effect_requests",
]
