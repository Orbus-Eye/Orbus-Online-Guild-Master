"""T2 canonical dungeon curve and class-counter coverage."""
from app.class_halls.mechanics import CLASS_MECHANICS
from app.class_halls.mechanics import resolve_class_mechanic
from app.dungeons.encounters import (
    COUNTER_THREAT_MAP,
    DUNGEON_ENCOUNTERS,
    apply_dungeon_encounter,
)
from app.shared.content_curve import DUNGEON_CURVE


def test_every_curve_dungeon_has_one_encounter_contract():
    assert set(DUNGEON_ENCOUNTERS) == set(DUNGEON_CURVE)
    assert len(DUNGEON_ENCOUNTERS) == 23


def test_encounter_contract_projects_level_80_curve_over_stale_rows():
    stale = {
        "slug": "world-tree-roots-5p",
        "difficulty": 1,
        "required_team_size": 3,
        "recommended_power": 10,
        "base_xp_reward": 1,
        "base_duration_seconds": 30,
    }
    canonical = apply_dungeon_encounter(stale)
    assert canonical["required_level"] == 70
    # FASE 8A ha ricalibrato la curva (+50-200%): il canonico per il
    # 7-piazze Lv70 è 3335 (il vecchio 1600 era pre-rebalance).
    assert canonical["recommended_power"] == 3335
    assert canonical["required_team_size"] == 7
    assert canonical["difficulty"] == 4
    assert canonical["base_duration_seconds"] == 720
    assert canonical["base_xp_reward"] == 1400
    assert canonical["curve_version"] == "level80-t2-v1"


def test_dungeon_path_uses_only_three_five_and_seven_member_content():
    team_sizes = {
        encounter.team_size
        for encounter in DUNGEON_ENCOUNTERS.values()
    }
    assert team_sizes == {3, 5, 7}
    assert sum(
        encounter.team_size == 3
        for encounter in DUNGEON_ENCOUNTERS.values()
    ) == 11
    assert sum(
        encounter.team_size == 5
        for encounter in DUNGEON_ENCOUNTERS.values()
    ) == 8
    assert sum(
        encounter.team_size == 7
        for encounter in DUNGEON_ENCOUNTERS.values()
    ) == 4


def test_all_sixteen_threats_have_an_encounter_and_a_counter():
    used_threats = {
        threat
        for encounter in DUNGEON_ENCOUNTERS.values()
        for threat in encounter.threat_tags
    }
    countered_threats = {
        threat
        for threats in COUNTER_THREAT_MAP.values()
        for threat in threats
    }
    assert len(used_threats) == 16
    assert used_threats <= countered_threats


def test_every_class_counter_is_valid_and_useful_in_current_dungeons():
    used_threats = {
        threat
        for encounter in DUNGEON_ENCOUNTERS.values()
        for threat in encounter.threat_tags
    }
    for class_slug, mechanic in CLASS_MECHANICS.items():
        assert mechanic.counter_tags
        for counter_tag in mechanic.counter_tags:
            assert counter_tag in COUNTER_THREAT_MAP, (
                f"{class_slug} usa una contromisura sconosciuta"
            )
            assert used_threats.intersection(
                COUNTER_THREAT_MAP[counter_tag]
            ), f"{class_slug}/{counter_tag} non serve in alcun dungeon"


def test_class_counterplay_requires_an_item_resonant_path():
    # FASE 9C — la risonanza è di CLASSE (tag del registry), non di
    # build: un Guerriero (DPS) risuona con le sue armi marziali.
    baseline = resolve_class_mechanic(
        adventurer={"canonical_class_slug": "guerriero"},
        equipment_items=[],
    )
    resonant = resolve_class_mechanic(
        adventurer={"canonical_class_slug": "guerriero"},
        equipment_items=[{"tags": ["sword"]}],
    )
    assert baseline["counter_tags"]
    assert baseline["active_counter_tags"] == []
    assert resonant["active_counter_tags"] == resonant["counter_tags"]


def test_threat_pressure_grows_toward_high_level_content():
    low = [
        len(encounter.threat_tags)
        for slug, encounter in DUNGEON_ENCOUNTERS.items()
        if DUNGEON_CURVE[slug].required_level <= 10
    ]
    high = [
        len(encounter.threat_tags)
        for slug, encounter in DUNGEON_ENCOUNTERS.items()
        if DUNGEON_CURVE[slug].required_level >= 60
    ]
    assert max(low) <= 3
    assert min(high) >= 3


def test_every_dungeon_has_three_readable_phases():
    for slug in DUNGEON_ENCOUNTERS:
        dungeon = apply_dungeon_encounter({"slug": slug})
        phases = dungeon["encounter_phases"]
        assert [phase["phase_id"] for phase in phases] == [
            "ingresso",
            "obiettivo",
            "culmine",
        ]
        assert all(phase["name_it"] for phase in phases)
        assert all(phase["success_condition_it"] for phase in phases)
        assert all(phase["threat_tags"] for phase in phases)


def test_ordinary_dungeon_profiles_never_authorize_endgame_rarity():
    for slug in DUNGEON_ENCOUNTERS:
        profile = apply_dungeon_encounter({"slug": slug})[
            "reward_profile"
        ]
        assert profile["pool_status"] == "blueprint_only"
        assert profile["class_relevance_required"] is True
        assert profile["legendary_allowed"] is False
        assert profile["unique_allowed"] is False
        assert "Legendary" not in profile["allowed_rarities"]
        assert "Unique" not in profile["allowed_rarities"]
        assert profile["max_rarity"] in {"Uncommon", "Rare", "Epic"}
