from __future__ import annotations

import asyncio
from copy import deepcopy
from datetime import datetime, timezone

import pytest

from app.items.services import item_public
from app.expeditions.formulas import build_equipment_delta
from app.expeditions.report_builder import build_expedition_report
from app.seeds.seed_items_it import ITALIAN_ITEM_SEED
from app.stats.runtime import feature_flags
from app.stats.runtime.effects.dispatcher import EffectDispatcher
from app.stats.runtime.effects.item_catalog import (
    STARTER_ITEM_EFFECT_DEFINITIONS,
    STARTER_ITEM_EFFECT_REGISTRY,
)
from app.stats.runtime.effects.item_hooks import (
    ItemEffectHookError,
    ItemEffectHookEvent,
    canonical_item_blueprint_id,
    compile_item_effect_requests,
)
from app.stats.runtime.effects.expedition_projection import (
    project_equipped_item_effects,
)
from app.stats.runtime.effects.models import EffectTrigger
from app.stats.runtime.state_store.fake_store import (
    FakeExpeditionRuntimeStateStore,
)
from app.stats.runtime.state_store.models import ExpeditionRuntimeState
from app.stats.runtime.wiring.feature_flags import EffectGateContext


NOW = datetime(2026, 7, 28, 15, 0, tzinfo=timezone.utc)

STARTER_CASES = (
    ("iron_sword", "guerriero", "item.krastlov.first_oath", "krastlov"),
    ("balanced_dagger", "ladro", "item.irthe.last_step", "irthe"),
    ("apprentice_staff", "mago", "item.ergolat.first_fracture", "ergolat"),
    ("initiate_robe", "paladino", "item.halodi.broken_vow", "halodi"),
    (
        "path_bow",
        "cacciatore_di_mostri",
        "item.elfwood.silent_trail",
        "elfwood",
    ),
)


def _seed_item(slug: str) -> dict:
    return deepcopy(next(item for item in ITALIAN_ITEM_SEED if item["slug"] == slug))


def _event(**overrides) -> ItemEffectHookEvent:
    values = {
        "expedition_id": "exp-item-hook",
        "root_event_id": "root-event-1",
        "root_event_sequence": 1,
        "trigger": EffectTrigger.ON_EVENT_COMPLETION,
        "source_adventurer_id": "adv-item-hook",
        "target_id": "adv-item-hook",
        "adventurer_class_slug": "guerriero",
    }
    values.update(overrides)
    return ItemEffectHookEvent(**values)


def _state() -> ExpeditionRuntimeState:
    return ExpeditionRuntimeState(
        expedition_id="exp-item-hook",
        state_version=1,
        created_at="2026-07-28T15:00:00Z",
        updated_at="2026-07-28T15:00:00Z",
        expires_at="2026-07-28T16:00:00Z",
    )


def test_starter_catalog_is_five_unique_lore_linked_definitions():
    assert len(STARTER_ITEM_EFFECT_DEFINITIONS) == 27
    assert len({d.effect_id for d in STARTER_ITEM_EFFECT_DEFINITIONS}) == 27
    for definition in STARTER_ITEM_EFFECT_DEFINITIONS:
        assert "item" in definition.tags
        assert "starter" in definition.tags


@pytest.mark.parametrize("slug,class_slug,effect_id,lore_key", STARTER_CASES)
def test_each_starter_item_has_singular_lore_identity_and_compiles(
    slug,
    class_slug,
    effect_id,
    lore_key,
):
    item = _seed_item(slug)
    assert canonical_item_blueprint_id(item) == slug
    assert item["effect_metadata"]["effect_id"] == effect_id
    assert item["effect_metadata"]["lore_key"] == lore_key
    assert lore_key in item["lore_tags"]
    assert item["lore_reviewed"] is True
    assert item["flavor_text_it"]
    assert item["display_name_it"]

    compiled = compile_item_effect_requests(
        event=_event(adventurer_class_slug=class_slug),
        equipment_items=(item,),
        registry=STARTER_ITEM_EFFECT_REGISTRY,
    )
    assert len(compiled.requests) == 1
    assert compiled.requests[0].effect_id == effect_id
    assert compiled.requests[0].target_id == "adv-item-hook"
    assert compiled.inactive == ()


def test_all_starter_names_and_blueprint_ids_are_unique():
    items = [_seed_item(case[0]) for case in STARTER_CASES]
    assert len({item["slug"] for item in items}) == 5
    assert len({item["display_name_it"].casefold() for item in items}) == 5


def test_compilation_is_deterministic_and_sorted_by_blueprint():
    first = _seed_item("path_bow")
    second = _seed_item("balanced_dagger")
    # Use a class compatible with both only for this ordering contract.
    first["recommended_classes"].append("tester_multi")
    first["class_tags"].append("tester_multi")
    second["recommended_classes"].append("tester_multi")
    second["class_tags"].append("tester_multi")
    event = _event(adventurer_class_slug="tester_multi")
    a = compile_item_effect_requests(
        event=event,
        equipment_items=(first, second),
        registry=STARTER_ITEM_EFFECT_REGISTRY,
    )
    b = compile_item_effect_requests(
        event=event,
        equipment_items=(second, first),
        registry=STARTER_ITEM_EFFECT_REGISTRY,
    )
    assert a == b
    assert tuple(request.effect_id for request in a.requests) == (
        "item.irthe.last_step",
        "item.elfwood.silent_trail",
    )
    assert len({request.event_id for request in a.requests}) == 2
    assert len({request.application_id for request in a.requests}) == 2


def test_legacy_item_without_metadata_is_valid_and_ignored():
    compiled = compile_item_effect_requests(
        event=_event(),
        equipment_items=({"slug": "legacy-sword", "name": "Legacy Sword"},),
        registry=STARTER_ITEM_EFFECT_REGISTRY,
    )
    assert compiled.requests == ()
    assert compiled.inactive == ()


def test_classless_adventurer_cannot_activate_item_effect():
    with pytest.raises(
        ItemEffectHookError,
        match="CLASS_REQUIRED_FOR_ITEM_EFFECT",
    ):
        compile_item_effect_requests(
            event=_event(adventurer_class_slug="recruit_unassigned"),
            equipment_items=(_seed_item("iron_sword"),),
            registry=STARTER_ITEM_EFFECT_REGISTRY,
        )


def test_soft_off_class_item_stays_equippable_but_effect_is_inactive():
    compiled = compile_item_effect_requests(
        event=_event(adventurer_class_slug="mago"),
        equipment_items=(_seed_item("iron_sword"),),
        registry=STARTER_ITEM_EFFECT_REGISTRY,
    )
    assert compiled.requests == ()
    assert compiled.inactive[0].reason_code == "OFF_CLASS_EFFECT_INACTIVE"


def test_effect_bearing_item_requires_reviewed_matching_lore():
    item = _seed_item("iron_sword")
    item["lore_reviewed"] = False
    with pytest.raises(ItemEffectHookError, match="ITEM_LORE_NOT_REVIEWED"):
        compile_item_effect_requests(
            event=_event(),
            equipment_items=(item,),
            registry=STARTER_ITEM_EFFECT_REGISTRY,
        )

    item = _seed_item("iron_sword")
    item["effect_metadata"]["lore_key"] = "irthe"
    with pytest.raises(ItemEffectHookError, match="ITEM_LORE_KEY_NOT_TAGGED"):
        compile_item_effect_requests(
            event=_event(),
            equipment_items=(item,),
            registry=STARTER_ITEM_EFFECT_REGISTRY,
        )


def test_database_metadata_cannot_define_executable_magnitude():
    item = _seed_item("iron_sword")
    item["effect_metadata"]["magnitude"] = 9999
    with pytest.raises(
        ItemEffectHookError,
        match="ITEM_EFFECT_METADATA_UNKNOWN_FIELDS",
    ):
        compile_item_effect_requests(
            event=_event(),
            equipment_items=(item,),
            registry=STARTER_ITEM_EFFECT_REGISTRY,
        )


def test_unknown_definition_fails_before_dispatch():
    item = _seed_item("iron_sword")
    item["effect_metadata"]["effect_id"] = "item.unknown"
    with pytest.raises(ItemEffectHookError, match="ITEM_EFFECT_DEFINITION_UNKNOWN"):
        compile_item_effect_requests(
            event=_event(),
            equipment_items=(item,),
            registry=STARTER_ITEM_EFFECT_REGISTRY,
        )


def test_duplicate_blueprint_or_display_name_fails_closed():
    item = _seed_item("iron_sword")
    with pytest.raises(ItemEffectHookError, match="ITEM_BLUEPRINT_DUPLICATED"):
        compile_item_effect_requests(
            event=_event(),
            equipment_items=(item, deepcopy(item)),
            registry=STARTER_ITEM_EFFECT_REGISTRY,
        )

    other = _seed_item("balanced_dagger")
    other["display_name_it"] = item["display_name_it"].upper()
    other["recommended_classes"].append("guerriero")
    other["class_tags"].append("guerriero")
    with pytest.raises(ItemEffectHookError, match="ITEM_DISPLAY_NAME_DUPLICATED"):
        compile_item_effect_requests(
            event=_event(),
            equipment_items=(item, other),
            registry=STARTER_ITEM_EFFECT_REGISTRY,
        )


def test_effects_per_root_event_cap_is_enforced():
    template = _seed_item("iron_sword")
    items = []
    for index in range(9):
        item = deepcopy(template)
        item["slug"] = f"test-singular-{index}"
        item["display_name_it"] = f"Oggetto Singolare {index}"
        items.append(item)
    with pytest.raises(
        ItemEffectHookError, match="ITEM_EFFECTS_PER_EVENT_CAP_EXCEEDED"
    ):
        compile_item_effect_requests(
            event=_event(),
            equipment_items=tuple(items),
            registry=STARTER_ITEM_EFFECT_REGISTRY,
        )


def test_public_item_projection_exposes_story_and_summary_not_rules():
    item = _seed_item("iron_sword")
    item["id"] = "item-id"
    public = item_public(item)
    assert public["description_it"] == item["description_it"]
    assert public["lore_source"] == "orbus_lore_book_v1"
    assert public["has_runtime_effect"] is True
    assert public["effect_summary_it"]
    assert public["effect_lore_key"] == "krastlov"
    assert "effect_metadata" not in public
    assert "magnitude" not in public


def test_compiled_starter_item_dispatches_to_fake_store(monkeypatch):
    monkeypatch.setenv("ORBUS_FLAG_CDV_TRANSIENT_STATE_ENABLED", "true")
    monkeypatch.setenv("ORBUS_FLAG_ITEM_EFFECT_ENGINE_ENABLED", "true")
    feature_flags.reset_cache()
    request = compile_item_effect_requests(
        event=_event(),
        equipment_items=(_seed_item("iron_sword"),),
        registry=STARTER_ITEM_EFFECT_REGISTRY,
    ).requests[0]

    async def go():
        store = FakeExpeditionRuntimeStateStore(clock=lambda: NOW)
        assert (await store.create_state("exp-item-hook", _state())).success
        dispatcher = EffectDispatcher(
            store=store,
            registry=STARTER_ITEM_EFFECT_REGISTRY,
            gate_context=EffectGateContext(
                is_test_user=True,
                environment_is_localhost_isolated=True,
                mongo_target_allowlisted=True,
            ),
        )
        outcome = await dispatcher.dispatch(request)
        assert outcome.resolution.accepted
        state = (await store.get_state("exp-item-hook")).state
        assert len(state.active_effect_instances) == 1
        instance = state.active_effect_instances[0]
        assert instance.effect_id == "item.krastlov.first_oath"
        assert instance.target_key == "endurance"
        assert instance.resolved_magnitude == 2

    try:
        asyncio.run(go())
    finally:
        feature_flags.reset_cache()


def test_equipped_signature_projects_visible_power_and_lore(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    item = _seed_item("iron_sword")
    item["id"] = "item-signature-warrior"
    projection = project_equipped_item_effects(
        expedition_id="exp-visible-item",
        adventurer={"id": "adv-warrior", "class_slug": "guerriero"},
        equipment_items=(item,),
    )
    assert projection["enabled"] is True
    assert projection["power_bonus"] == 2
    assert projection["stat_bonuses"] == {"endurance": 2}
    assert projection["inactive"] == []
    effect = projection["effects"][0]
    assert effect["item_name"] == item["display_name_it"]
    assert effect["effect_id"] == "item.krastlov.first_oath"
    assert effect["lore_source"] == "orbus_lore_book_v1"
    assert effect["magnitude"] == 2


def test_item_effect_projection_is_fail_closed_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("ORBUS_ITEM_EFFECT_PROJECTION_ENABLED", raising=False)
    projection = project_equipped_item_effects(
        expedition_id="exp-prod-off",
        adventurer={"id": "adv-warrior", "class_slug": "guerriero"},
        equipment_items=(_seed_item("iron_sword"),),
    )
    assert projection == {
        "enabled": False,
        "power_bonus": 0,
        "stat_bonuses": {},
        "effects": [],
        "inactive": [],
    }


def test_item_effect_power_is_separate_and_visible_in_completed_report():
    effect = {
        "item_id": "item-signature-warrior",
        "blueprint_id": "iron_sword",
        "item_name": "Giuramento di Krastlov",
        "effect_id": "item.krastlov.first_oath",
        "summary_it": "Il primo giuramento sostiene chi regge la linea.",
        "lore_source": "orbus_lore_book_v1",
        "target_stat": "endurance",
        "magnitude": 2,
        "power_delta": 2,
    }
    members = [
        {
            "adventurer_id": "adv-warrior",
            "name_snapshot": "Alda",
            "class_name_snapshot": "Warrior",
            "role_snapshot": "Tank",
            "total_power_snapshot": 24,
            "equipment_power_snapshot": 2,
            "item_effect_power_bonus": 2,
            "item_effects_snapshot": [effect],
            "traits_snapshot": [],
        }
    ]
    delta = build_equipment_delta(
        members,
        {"recommended_power": 20},
        final_team_power=29,
        success_chance_with_eq=59,
    )
    assert delta["base_team_power"] == 25
    assert delta["equipment_base_power_bonus"] == 2
    assert delta["item_effect_power_bonus"] == 2
    assert delta["equipment_power_bonus"] == 4
    assert "equipaggiamento base ha aggiunto +2" in delta["equipment_delta_text"]
    assert "effetti degli item di lore +2" in delta["equipment_delta_text"]

    report = build_expedition_report(
        {
            "status": "completed",
            "result_summary": "Success",
            "final_score": 10,
            "success_chance": 59,
            "success_chance_with_equipment": 59,
            "final_team_power": 29,
            "team_power": 29,
            "dungeon_name": "Cripta di Prova",
            "gold_reward": 8,
            "xp_reward": 5,
        },
        members,
        {"slug": "trial-crypt", "name": "Cripta di Prova", "recommended_power": 20},
        [],
    )
    summary = report["report_summary"]
    assert summary["item_effect_power_bonus"] == 2
    assert summary["item_effects"][0]["item_name"] == "Giuramento di Krastlov"
    assert summary["item_effects"][0]["adventurer_name"] == "Alda"
