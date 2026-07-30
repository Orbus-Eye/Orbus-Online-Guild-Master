"""Deterministic, player-visible projection of equipped item effects.

The generic effect dispatcher remains independently gated. This module uses
the same static registry and fail-closed compiler to calculate the departure
snapshot that affects expedition power in tester environments. Database item
metadata may reference an effect, but never defines executable rules.
"""

from __future__ import annotations

import os
from collections import defaultdict
from typing import Iterable, Mapping

from app.stats.runtime.effects.item_catalog import (
    STARTER_ITEM_EFFECT_REGISTRY,
)
from app.stats.runtime.effects.item_hooks import (
    ItemEffectHookEvent,
    canonical_item_blueprint_id,
    compile_item_effect_requests,
)
from app.stats.runtime.effects.models import EffectPrimitive, EffectTrigger


_TRUTHY = frozenset({"1", "true", "yes", "on"})


def item_effect_projection_enabled() -> bool:
    """Default ON for local/tester builds and fail-closed in production."""

    raw = os.getenv("ORBUS_ITEM_EFFECT_PROJECTION_ENABLED")
    if raw is not None:
        return raw.strip().lower() in _TRUTHY
    app_env = (os.getenv("APP_ENV") or "development").strip().lower()
    return app_env in {"development", "dev", "preview", "test", "testing"}


def _empty_projection(*, enabled: bool) -> dict:
    return {
        "enabled": enabled,
        "power_bonus": 0,
        "stat_bonuses": {},
        "effects": [],
        "inactive": [],
    }


def project_equipped_item_effects(
    *,
    expedition_id: str,
    adventurer: Mapping[str, object],
    equipment_items: Iterable[Mapping[str, object]] | None,
) -> dict:
    """Compile and project supported item effects into an immutable snapshot."""

    if not item_effect_projection_enabled():
        return _empty_projection(enabled=False)

    items = tuple(equipment_items or ())
    compilation = compile_item_effect_requests(
        event=ItemEffectHookEvent(
            expedition_id=expedition_id,
            root_event_id="expedition-dispatch",
            root_event_sequence=1,
            trigger=EffectTrigger.ON_EVENT_COMPLETION,
            source_adventurer_id=str(adventurer.get("id") or ""),
            target_id=str(adventurer.get("id") or ""),
            adventurer_class_slug=str(adventurer.get("class_slug") or ""),
        ),
        equipment_items=items,
        registry=STARTER_ITEM_EFFECT_REGISTRY,
    )

    items_by_effect: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for item in sorted(items, key=canonical_item_blueprint_id):
        metadata = item.get("effect_metadata")
        if isinstance(metadata, Mapping) and metadata.get("enabled", True) is not False:
            effect_id = str(metadata.get("effect_id") or "")
            if effect_id:
                items_by_effect[effect_id].append(item)

    effects: list[dict] = []
    stat_bonuses: dict[str, int] = {}
    power_bonus = 0
    for request in compilation.requests:
        definition = STARTER_ITEM_EFFECT_REGISTRY.get(
            request.effect_id,
            request.effect_version,
        )
        if definition is None:  # compiler already guarantees this
            continue
        matching_items = items_by_effect.get(request.effect_id) or []
        item = matching_items.pop(0) if matching_items else {}
        metadata = item.get("effect_metadata")
        metadata = metadata if isinstance(metadata, Mapping) else {}
        supported = (
            definition.primitive is EffectPrimitive.STAT_FLAT_TEMPORARY
            and bool(definition.target_key)
        )
        magnitude = int(definition.magnitude) if supported else 0
        if supported:
            stat = str(definition.target_key)
            stat_bonuses[stat] = stat_bonuses.get(stat, 0) + magnitude
            power_bonus += magnitude
        effects.append(
            {
                "item_id": item.get("id"),
                "blueprint_id": (
                    canonical_item_blueprint_id(item) if item else None
                ),
                "item_name": (
                    item.get("display_name_it")
                    or item.get("name")
                    or request.effect_id
                ),
                "effect_id": request.effect_id,
                "effect_version": request.effect_version,
                "summary_it": metadata.get("effect_summary_it"),
                "lore_key": metadata.get("lore_key"),
                "lore_source": item.get("lore_source"),
                "target_stat": definition.target_key,
                "magnitude": magnitude,
                "power_delta": magnitude,
                "trigger": definition.trigger.value,
                "supported_in_expedition": supported,
            }
        )

    return {
        "enabled": True,
        "power_bonus": power_bonus,
        "stat_bonuses": stat_bonuses,
        "effects": effects,
        "inactive": [
            {
                "blueprint_id": inactive.item_blueprint_id,
                "reason_code": inactive.reason_code,
            }
            for inactive in compilation.inactive
        ],
    }


__all__ = [
    "item_effect_projection_enabled",
    "project_equipped_item_effects",
]
