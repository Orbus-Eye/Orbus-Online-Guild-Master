from __future__ import annotations

import asyncio
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from types import ModuleType
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

# Several legacy domain packages eagerly import their HTTP routes from
# ``__init__``.  Unit tests need the service modules only, so install minimal
# namespace packages and avoid loading unrelated auth/database integrations.
_APP_ROOT = Path(__file__).resolve().parents[1] / "app"
for _domain in ("adventurers", "class_halls", "equipment", "recruitment"):
    _name = f"app.{_domain}"
    if _name not in sys.modules:
        _package = ModuleType(_name)
        _package.__path__ = [str(_APP_ROOT / _domain)]
        sys.modules[_name] = _package

from app.adventurers.common import _generate_classless_candidate
from app.adventurers.classless import (
    is_explicit_classless_recruit,
    require_class_hall_assignment,
)
from app.adventurers.services import adventurer_public
from app.class_halls.catalog import CLASS_HALLS, class_hall_choices_public
from app.class_halls.feature_flags import assignment_enabled_for_hall
from app.class_halls.journey import (
    complete_safe_trial,
    confirm_class_hall_assignment,
)
from app.equipment.compatibility import check_equip_compatibility
from app.equipment.level_gate import resolve_item_required_level
from app.expeditions.services import (
    CANONICAL_CLASS_LEVELUP_STAT,
    _resolve_levelup,
)
from app.onboarding.services import _build_starter_adventurer
from app.recruitment.freeze_bench import recruit_from_bench
from app.recruitment.services import candidate_public, recruit_from_offer
from app.shared.constants import ADVENTURER_MAX_LEVEL
from app.seeds.seed_class_hall_content import (
    CANONICAL_CLASS_HALL_ITEM_SEED,
    CANONICAL_CLASS_SEED,
    seed_canonical_class_hall_content,
    validate_canonical_class_hall_content,
)
from app.seeds.seed_items_it import ITALIAN_ITEM_SEED
from app.stats.runtime.effects.item_catalog import (
    STARTER_ITEM_EFFECT_DEFINITIONS,
    STARTER_ITEM_EFFECT_REGISTRY,
)
from app.stats.runtime.effects.item_hooks import (
    ItemEffectHookEvent,
    compile_item_effect_requests,
)
from app.stats.runtime.effects.models import EffectTrigger


NOW = datetime(2026, 7, 28, 12, 0, tzinfo=timezone.utc)


def _classless(**overrides) -> dict:
    values = {
        "id": "adv-classless",
        "guild_id": "guild-1",
        "name": "Mira",
        "adventurer_class_id": None,
        "class_name": None,
        "class_role": None,
        "class_proficiency": None,
        "class_slug": None,
        "canonical_class_slug": None,
        "class_hall_id": None,
        "class_hall_assigned_at": None,
        "hall_master_witness_npc": None,
        "recruit_status": "recruit_unassigned",
        "narrative_intro_shown": False,
        "rarity": "Common",
        "level": 1,
        "experience": 0,
        "strength": 5,
        "agility": 5,
        "intellect": 5,
        "endurance": 5,
        "faith": 5,
        "stamina": 100,
        "morale": 100,
        "traits": [],
        "is_available": True,
        "created_at": NOW.isoformat(),
        "updated_at": NOW.isoformat(),
    }
    values.update(overrides)
    return values


def test_classless_candidate_has_no_implicit_class_and_public_cta() -> None:
    candidate = _generate_classless_candidate(
        "guild-1",
        NOW,
        rng=random.Random(7),
        forced_rarity="Common",
    )

    for field in (
        "adventurer_class_id",
        "class_name",
        "class_role",
        "class_proficiency",
        "class_slug",
        "canonical_class_slug",
        "class_hall_id",
        "class_hall_assigned_at",
        "hall_master_witness_npc",
    ):
        assert candidate[field] is None
    assert candidate["recruit_status"] == "recruit_unassigned"
    assert candidate["narrative_intro_shown"] is False

    offer = candidate_public(candidate)
    roster = adventurer_public(
        {
            **candidate,
            "is_available": True,
            "updated_at": candidate["created_at"],
        }
    )
    assert offer["class_selection_required"] is True
    assert roster["class_selection_required"] is True
    assert offer["class_display_name_it"] == "Senza Classe"
    assert roster["class_slug"] is None


def test_starter_roster_adventurer_is_also_explicitly_classless() -> None:
    starter = _build_starter_adventurer("guild-1", [])

    for field in (
        "adventurer_class_id",
        "class_name",
        "class_role",
        "class_proficiency",
        "class_slug",
        "canonical_class_slug",
        "class_hall_id",
        "class_hall_assigned_at",
        "hall_master_witness_npc",
    ):
        assert starter[field] is None
    assert starter["recruit_status"] == "recruit_unassigned"
    assert starter["is_starter"] is True
    assert starter["is_available"] is True
    assert starter["rarity"] == "Common"
    assert "expires_at" not in starter
    assert starter["created_at"] == starter["updated_at"]
    assert all(
        3 <= starter[stat] <= 7
        for stat in ("strength", "agility", "intellect", "endurance", "faith")
    )
    assert adventurer_public(starter)["class_selection_required"] is True


def test_all_27_halls_are_unique_and_tester_ready() -> None:
    choices = class_hall_choices_public()
    assert len(choices) == 27
    assert len({choice["hall_id"] for choice in choices}) == 27
    assert len({choice["canonical_class_slug"] for choice in choices}) == 27
    assert len({choice["starter_item_name_it"] for choice in choices}) == 27
    assert all(choice["lore_hook_it"] for choice in choices)
    assert all(choice["hall_master_witness_npc"] for choice in choices)
    assert all(choice["lifecycle"] == "ACTIVE" for choice in choices)
    assert all(choice["readiness"] == "APPROVED" for choice in choices)
    assert CLASS_HALLS["hall_paladino"].class_proficiency == "Priest"


def test_all_27_classes_level_their_canonical_primary_stat() -> None:
    assert len(CANONICAL_CLASS_LEVELUP_STAT) == 27
    for class_seed in CANONICAL_CLASS_SEED:
        primary = class_seed["primary_stat"]
        adventurer = _classless(
            class_name=class_seed["name"],
            class_slug=class_seed["slug"],
            canonical_class_slug=class_seed["slug"],
            recruit_status="class_assigned",
            experience=100,
        )
        before = adventurer[primary]
        leveled = _resolve_levelup(adventurer)
        assert leveled["level"] == 2
        assert leveled[primary] == before + 1


def test_assignment_gate_is_playable_for_testers_and_closed_in_production() -> None:
    with patch.dict(
        os.environ,
        {"APP_ENV": "test"},
        clear=True,
    ):
        assert assignment_enabled_for_hall("hall_sognatore") is True
    with patch.dict(
        os.environ,
        {"APP_ENV": "production"},
        clear=True,
    ):
        assert assignment_enabled_for_hall("hall_sognatore") is False
    with patch.dict(
        os.environ,
        {
            "APP_ENV": "production",
            "ORBUS_CLASS_HALL_ASSIGNMENT_ENABLED": "true",
            "ORBUS_CLASS_HALL_ASSIGNMENT_HALLS": "hall_guerriero",
        },
        clear=True,
    ):
        assert assignment_enabled_for_hall("hall_guerriero") is True
        assert assignment_enabled_for_hall("hall_sognatore") is False


def test_item_first_catalog_has_five_singular_lore_items_per_class() -> None:
    validate_canonical_class_hall_content()
    assert len(CANONICAL_CLASS_SEED) == 27
    assert len(CANONICAL_CLASS_HALL_ITEM_SEED) == 135
    assert len(STARTER_ITEM_EFFECT_DEFINITIONS) == 27
    assert (
        len(
            {
                item["display_name_it"].casefold()
                for item in CANONICAL_CLASS_HALL_ITEM_SEED
            }
        )
        == 135
    )
    assert all(item["lore_reviewed"] is True for item in CANONICAL_CLASS_HALL_ITEM_SEED)
    assert all(item["lore_source"] for item in CANONICAL_CLASS_HALL_ITEM_SEED)
    assert all(
        item["required_adventurer_level"] == 1
        for item in CANONICAL_CLASS_HALL_ITEM_SEED
    )
    assert all(
        len(item["acquisition_sources"]) == 1
        and item["acquisition_hint_it"]
        for item in CANONICAL_CLASS_HALL_ITEM_SEED
    )
    for class_seed in CANONICAL_CLASS_SEED:
        class_items = [
            item
            for item in CANONICAL_CLASS_HALL_ITEM_SEED
            if class_seed["slug"] in item["class_tags"]
        ]
        assert len(class_items) == 5
        assert sorted(
            item["acquisition_track_order"] for item in class_items
        ) == [0, 1, 2, 3, 4]
        assert sum(bool(item.get("effect_metadata")) for item in class_items) == 1
    final_live_names = {
        item["slug"]: item["display_name_it"] for item in ITALIAN_ITEM_SEED
    }
    final_live_names.update(
        {
            item["slug"]: item["display_name_it"]
            for item in CANONICAL_CLASS_HALL_ITEM_SEED
        }
    )
    assert len({name.casefold() for name in final_live_names.values()}) == len(
        final_live_names
    )


def test_item_level_gate_normalizes_legacy_rarity_but_honors_hall_override() -> None:
    assert resolve_item_required_level({"rarity": "epic"}) == 8
    assert (
        resolve_item_required_level({"rarity": "LEGENDARY"})
        == ADVENTURER_MAX_LEVEL
    )
    assert resolve_item_required_level(
        {"rarity": "Uncommon", "required_adventurer_level": 1}
    ) == 1


def test_all_27_signature_items_compile_against_static_effect_registry() -> None:
    stat_labels_it = {
        "strength": "Forza",
        "agility": "Agilità",
        "intellect": "Intelletto",
        "endurance": "Tempra",
        "faith": "Fede",
    }
    signatures = [
        item for item in CANONICAL_CLASS_HALL_ITEM_SEED if item.get("effect_metadata")
    ]
    assert len(signatures) == 27
    for item in signatures:
        class_slug = item["required_class_optional"]
        compiled = compile_item_effect_requests(
            event=ItemEffectHookEvent(
                expedition_id="exp-canonical",
                root_event_id=f"event-{class_slug}",
                root_event_sequence=1,
                trigger=EffectTrigger.ON_EVENT_COMPLETION,
                source_adventurer_id=f"adv-{class_slug}",
                target_id=f"adv-{class_slug}",
                adventurer_class_slug=class_slug,
            ),
            equipment_items=[item],
            registry=STARTER_ITEM_EFFECT_REGISTRY,
        )
        assert len(compiled.requests) == 1
        request = compiled.requests[0]
        definition = STARTER_ITEM_EFFECT_REGISTRY.get(
            request.effect_id,
            request.effect_version,
        )
        assert definition is not None
        summary_it = item["effect_metadata"]["effect_summary_it"]
        assert f"+{definition.magnitude}" in summary_it
        assert stat_labels_it[definition.target_key] in summary_it
        assert definition.target_key not in summary_it


def test_canonical_seed_uses_non_conflicting_idempotent_upserts() -> None:
    async def go() -> None:
        unchanged = SimpleNamespace(upserted_id=None, modified_count=0)
        db = SimpleNamespace(
            adventurer_classes=AsyncMock(),
            items=AsyncMock(),
        )
        db.adventurer_classes.update_one.return_value = unchanged
        db.items.update_one.return_value = unchanged
        result = await seed_canonical_class_hall_content(db)
        assert result == {"classes": 0, "items": 0}
        assert db.adventurer_classes.update_one.await_count == 27
        assert db.items.update_one.await_count == 135
        for call in (
            db.adventurer_classes.update_one.await_args_list
            + db.items.update_one.await_args_list
        ):
            update = call.args[1]
            assert not (set(update["$setOnInsert"]) & set(update["$set"]))

    asyncio.run(go())


def test_classless_equipment_is_fail_closed_except_universal_utility() -> None:
    adventurer = _classless()
    weapon = {"item_type": "weapon", "weapon_tags": ["sword"]}
    universal = {"item_type": "accessory", "is_universal": True}
    consumable = {"item_type": "consumable"}

    blocked = check_equip_compatibility(adventurer, weapon)
    assert blocked["allowed"] is False
    assert blocked["reason_code"] == "class_required"
    assert check_equip_compatibility(adventurer, universal)["reason_code"] == (
        "universal_classless"
    )
    assert check_equip_compatibility(adventurer, consumable)["allowed"] is True


def test_explicit_classless_guard_blocks_activities_but_not_legacy_nulls() -> None:
    recruit = _classless()
    legacy_null = {
        **recruit,
        "id": "legacy-null",
        "recruit_status": None,
    }
    assert is_explicit_classless_recruit(recruit) is True
    assert is_explicit_classless_recruit(legacy_null) is False
    with pytest.raises(HTTPException) as exc:
        require_class_hall_assignment([legacy_null, recruit], source="test.activity")
    assert exc.value.status_code == 423
    assert exc.value.detail["code"] == "class_hall.selection_required"
    require_class_hall_assignment([legacy_null], source="test.activity")


def test_safe_trial_requires_exact_server_script_order() -> None:
    async def go() -> None:
        db = SimpleNamespace(
            class_hall_trial_sessions=AsyncMock(),
        )
        profile = CLASS_HALLS["hall_guerriero"]
        with patch(
            "app.class_halls.journey.assignment_enabled_for_hall",
            return_value=True,
        ):
            with pytest.raises(HTTPException) as exc:
                await complete_safe_trial(
                    db,
                    guild_id="guild-1",
                    adventurer_id="adv-classless",
                    hall_id=profile.hall_id,
                    trial_id="trial-1",
                    completed_steps=list(reversed(profile.trial_steps)),
                    actor_user_id="user-1",
                )
        assert exc.value.status_code == 400
        assert exc.value.detail["code"] == "class_hall.trial_steps_invalid"
        db.class_hall_trial_sessions.find_one_and_update.assert_not_awaited()

    asyncio.run(go())


def test_classless_cap_rejects_offer_without_consuming_it() -> None:
    async def go() -> None:
        db = SimpleNamespace(
            recruitment_offers=AsyncMock(),
            adventurers=AsyncMock(),
        )
        db.recruitment_offers.find_one.return_value = {
            "id": "candidate-1",
            "recruit_status": "recruit_unassigned",
            "class_slug": None,
            "class_name": None,
        }
        db.adventurers.count_documents.return_value = 3

        with pytest.raises(HTTPException) as exc:
            await recruit_from_offer(db, {"id": "guild-1"}, "candidate-1")
        assert exc.value.status_code == 423
        assert exc.value.detail["code"] == "recruit.classless_cap_reached"
        db.recruitment_offers.find_one_and_delete.assert_not_awaited()

    asyncio.run(go())


def test_classless_cap_keeps_frozen_recruit_on_bench() -> None:
    async def go() -> None:
        frozen = {
            "frozen_id": "frozen-1",
            "recruit_status": "recruit_unassigned",
            "class_slug": None,
            "class_name": None,
        }
        guild = {
            "id": "guild-1",
            "recruit_freeze_bench": {
                "frozen_candidates": [frozen],
                "max_slots": 2,
            },
        }
        db = SimpleNamespace(
            guilds=AsyncMock(),
            adventurers=AsyncMock(),
        )
        db.adventurers.count_documents.return_value = 3

        with pytest.raises(HTTPException) as exc:
            await recruit_from_bench(db, guild, "frozen-1")
        assert exc.value.status_code == 423
        assert exc.value.detail["code"] == "recruit.classless_cap_reached"
        db.guilds.find_one_and_update.assert_not_awaited()

    asyncio.run(go())


def test_assignment_cas_commits_identity_and_delivers_one_lore_item() -> None:
    async def go() -> None:
        classless = _classless()
        assigned = _classless(
            adventurer_class_id="class-warrior",
            class_name="Guerriero",
            class_role="Tank",
            class_proficiency="Warrior",
            class_slug="guerriero",
            canonical_class_slug="guerriero",
            class_hall_id="hall_guerriero",
            hall_master_witness_npc="Comandante Aldric del Ferro",
            recruit_status="class_assigned",
            narrative_intro_shown=True,
            class_assignment_id="assignment-1",
            starter_item_reward_status="pending",
        )
        delivered = {**assigned, "starter_item_reward_status": "delivered"}
        db = SimpleNamespace(
            adventurers=AsyncMock(),
            class_hall_trial_sessions=AsyncMock(),
            adventurer_classes=AsyncMock(),
            items=AsyncMock(),
            class_hall_reward_grants=AsyncMock(),
            inventory_items=AsyncMock(),
        )
        db.adventurers.find_one.side_effect = [classless, delivered]
        db.adventurers.find_one_and_update.return_value = assigned
        db.class_hall_trial_sessions.find_one.return_value = {
            "id": "trial-1",
            "completed_at": NOW.isoformat(),
        }
        db.adventurer_classes.find_one.return_value = {
            "id": "class-warrior",
            "slug": "guerriero",
        }
        db.items.find_one.return_value = {
            "id": "item-iron-sword",
            "slug": "iron_sword",
            "name_it": "Lama del Primo Giuramento di Krastlov",
        }
        db.inventory_items.find_one.return_value = None
        db.inventory_items.update_one.return_value = SimpleNamespace(matched_count=0)

        with (
            patch(
                "app.class_halls.journey.assignment_enabled_for_hall",
                return_value=True,
            ),
            patch(
                "app.class_halls.journey.write_audit",
                new=AsyncMock(),
            ),
        ):
            result = await confirm_class_hall_assignment(
                db,
                guild_id="guild-1",
                adventurer_id="adv-classless",
                hall_id="hall_guerriero",
                trial_id="trial-1",
                explicit_confirmation=True,
                actor_user_id="user-1",
            )

        assert result["idempotent"] is False
        assert result["reward"]["status"] == "delivered"
        assert result["adventurer"]["class_slug"] == "guerriero"
        assignment_filter = db.adventurers.find_one_and_update.await_args.args[0]
        assert assignment_filter["class_slug"] is None
        assert assignment_filter["class_proficiency"] is None
        assignment_update = db.adventurers.find_one_and_update.await_args.args[1]
        assert assignment_update["$set"]["class_hall_id"] == "hall_guerriero"
        assert assignment_update["$set"]["class_assignment_status"] == "COMMITTED"
        inserted = db.inventory_items.insert_one.await_args.args[0]
        assert inserted["quantity"] == 1
        assert inserted["class_hall_grant_ids"] == [
            "class_hall_starter::adv-classless::hall_guerriero"
        ]

    asyncio.run(go())


def test_same_hall_retry_reconciles_without_reassigning_or_duplicating() -> None:
    async def go() -> None:
        assigned = _classless(
            adventurer_class_id="class-warrior",
            class_name="Guerriero",
            class_role="Tank",
            class_proficiency="Warrior",
            class_slug="guerriero",
            canonical_class_slug="guerriero",
            class_hall_id="hall_guerriero",
            recruit_status="class_assigned",
            narrative_intro_shown=True,
            starter_item_reward_status="delivered",
        )
        db = SimpleNamespace(
            adventurers=AsyncMock(),
            class_hall_trial_sessions=AsyncMock(),
            adventurer_classes=AsyncMock(),
            items=AsyncMock(),
            class_hall_reward_grants=AsyncMock(),
            inventory_items=AsyncMock(),
        )
        db.adventurers.find_one.side_effect = [assigned, assigned]
        db.items.find_one.return_value = {
            "id": "item-iron-sword",
            "slug": "iron_sword",
            "name_it": "Lama del Primo Giuramento di Krastlov",
        }
        db.inventory_items.find_one.return_value = {"id": "inventory-1"}

        with (
            patch(
                "app.class_halls.journey.assignment_enabled_for_hall",
                return_value=True,
            ),
            patch(
                "app.class_halls.journey.write_audit",
                new=AsyncMock(),
            ),
        ):
            result = await confirm_class_hall_assignment(
                db,
                guild_id="guild-1",
                adventurer_id="adv-classless",
                hall_id="hall_guerriero",
                trial_id="trial-ignored-on-idempotent-retry",
                explicit_confirmation=True,
                actor_user_id="user-1",
            )

        assert result["idempotent"] is True
        db.adventurers.find_one_and_update.assert_not_awaited()
        db.inventory_items.update_one.assert_not_awaited()
        db.inventory_items.insert_one.assert_not_awaited()

    asyncio.run(go())
