"""Lore-linked starter item effects for the first tester vertical slice.

The definitions are static and immutable.  Item documents reference them by
``effect_id`` + ``effect_version``; item data never defines executable
behaviour.  This keeps balance changes reviewable and prevents database
metadata from becoming an unchecked rules engine.
"""

from __future__ import annotations

from app.stats.runtime.effects.models import (
    EffectDefinition,
    EffectDuration,
    EffectPrimitive,
    EffectStacking,
    EffectTargetScope,
    EffectTrigger,
    EffectVisibility,
)
from app.stats.runtime.effects.registry import EffectRegistry
from app.class_halls.catalog import CLASS_HALLS


_WAVE_A_EFFECT_DEFINITIONS: tuple[EffectDefinition, ...] = (
    EffectDefinition(
        effect_id="item.krastlov.first_oath",
        version=1,
        primitive=EffectPrimitive.STAT_FLAT_TEMPORARY,
        trigger=EffectTrigger.ON_EVENT_COMPLETION,
        duration=EffectDuration.UNTIL_PHASE_END,
        target_scope=EffectTargetScope.SELF,
        target_key="endurance",
        magnitude=2,
        i18n_key="items.effects.krastlov_first_oath",
        stacking=EffectStacking.NONE,
        priority=200,
        tags=("item", "starter", "guerriero", "krastlov"),
        audit_class="item_effect",
        visibility=EffectVisibility.PRIVATE,
    ),
    EffectDefinition(
        effect_id="item.irthe.last_step",
        version=1,
        primitive=EffectPrimitive.STAT_FLAT_TEMPORARY,
        trigger=EffectTrigger.ON_EVENT_COMPLETION,
        duration=EffectDuration.UNTIL_PHASE_END,
        target_scope=EffectTargetScope.SELF,
        target_key="agility",
        magnitude=2,
        i18n_key="items.effects.irthe_last_step",
        stacking=EffectStacking.NONE,
        priority=210,
        tags=("item", "starter", "ladro", "irthe"),
        audit_class="item_effect",
        visibility=EffectVisibility.PRIVATE,
    ),
    EffectDefinition(
        effect_id="item.ergolat.first_fracture",
        version=1,
        primitive=EffectPrimitive.STAT_FLAT_TEMPORARY,
        trigger=EffectTrigger.ON_EVENT_COMPLETION,
        duration=EffectDuration.UNTIL_PHASE_END,
        target_scope=EffectTargetScope.SELF,
        target_key="intellect",
        magnitude=2,
        i18n_key="items.effects.ergolat_first_fracture",
        stacking=EffectStacking.NONE,
        priority=220,
        tags=("item", "starter", "mago", "ergolat"),
        audit_class="item_effect",
        visibility=EffectVisibility.PRIVATE,
    ),
    EffectDefinition(
        effect_id="item.halodi.broken_vow",
        version=1,
        primitive=EffectPrimitive.STAT_FLAT_TEMPORARY,
        trigger=EffectTrigger.ON_EVENT_COMPLETION,
        duration=EffectDuration.UNTIL_PHASE_END,
        target_scope=EffectTargetScope.SELF,
        target_key="faith",
        magnitude=2,
        i18n_key="items.effects.halodi_broken_vow",
        stacking=EffectStacking.NONE,
        priority=230,
        tags=("item", "starter", "paladino", "halodi"),
        audit_class="item_effect",
        visibility=EffectVisibility.PRIVATE,
    ),
    EffectDefinition(
        effect_id="item.elfwood.silent_trail",
        version=1,
        primitive=EffectPrimitive.STAT_FLAT_TEMPORARY,
        trigger=EffectTrigger.ON_EVENT_COMPLETION,
        duration=EffectDuration.UNTIL_PHASE_END,
        target_scope=EffectTargetScope.SELF,
        target_key="agility",
        magnitude=2,
        i18n_key="items.effects.elfwood_silent_trail",
        stacking=EffectStacking.NONE,
        priority=240,
        tags=("item", "starter", "cacciatore_di_mostri", "elfwood"),
        audit_class="item_effect",
        visibility=EffectVisibility.PRIVATE,
    ),
)


def _build_expansion_definitions() -> tuple[EffectDefinition, ...]:
    existing = {definition.effect_id for definition in _WAVE_A_EFFECT_DEFINITIONS}
    definitions: list[EffectDefinition] = []
    for index, profile in enumerate(
        sorted(CLASS_HALLS.values(), key=lambda value: value.hall_id),
        start=1,
    ):
        if profile.starter_effect_id in existing:
            continue
        definitions.append(
            EffectDefinition(
                effect_id=profile.starter_effect_id,
                version=1,
                primitive=EffectPrimitive.STAT_FLAT_TEMPORARY,
                trigger=EffectTrigger.ON_EVENT_COMPLETION,
                duration=EffectDuration.UNTIL_PHASE_END,
                target_scope=EffectTargetScope.SELF,
                target_key=profile.primary_stat,
                magnitude=2,
                i18n_key=(
                    "items.effects."
                    f"{profile.starter_lore_key}_{profile.canonical_class_slug}"
                ),
                stacking=EffectStacking.NONE,
                priority=300 + index,
                tags=(
                    "item",
                    "starter",
                    profile.canonical_class_slug,
                    profile.starter_lore_key,
                    f"wave_{profile.wave.lower()}",
                ),
                audit_class="item_effect",
                visibility=EffectVisibility.PRIVATE,
            )
        )
    return tuple(definitions)


STARTER_ITEM_EFFECT_DEFINITIONS = (
    _WAVE_A_EFFECT_DEFINITIONS + _build_expansion_definitions()
)
STARTER_ITEM_EFFECT_REGISTRY = EffectRegistry(STARTER_ITEM_EFFECT_DEFINITIONS)


__all__ = [
    "STARTER_ITEM_EFFECT_DEFINITIONS",
    "STARTER_ITEM_EFFECT_REGISTRY",
]
