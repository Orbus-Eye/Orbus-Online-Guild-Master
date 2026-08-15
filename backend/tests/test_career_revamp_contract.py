from app.adventurers.career import (
    CAREER_RARITY_STAT_MULTIPLIERS,
    career_effective_stats,
    career_progress_snapshot,
    career_rarity_for_counts,
)
from app.dungeons.encounters import DUNGEON_ENCOUNTERS, DUNGEON_LORE
from app.items.catalog_contract import (
    ULTRA_RARE_RANDOM_DROP_SLUG,
    effective_catalog_required_level,
    ultra_rare_random_drop_allowed,
)
from app.raids.contracts import RAID_CONTRACTS
from app.recruitment.base_models import base_model_cost_for_active_roster
from app.rewards.company_ring import (
    ONE_IN,
    WORLD_BOSS_SOURCE_SLUG,
    company_ring_world_boss_eligible,
)
from app.shared.constants import ADVENTURER_MAX_LEVEL, EQUIPMENT_SLOTS
from app.shared.progression import cumulative_xp_required_for_level
from app.squads.schemas import SQUAD_SIZE


def test_career_rarity_threshold_boundaries():
    assert career_rarity_for_counts(49, 999) == "Common"
    assert career_rarity_for_counts(50, 0) == "Uncommon"
    assert career_rarity_for_counts(150, 0) == "Rare"
    assert career_rarity_for_counts(500, 4) == "Rare"
    assert career_rarity_for_counts(500, 5) == "Epic"
    assert career_rarity_for_counts(2000, 149) == "Epic"
    assert career_rarity_for_counts(2000, 150) == "Legendary"


def test_career_progress_reports_both_requirements():
    progress = career_progress_snapshot(
        {"career_dungeons_completed": 700, "career_raids_completed": 12}
    )
    assert progress["rarity"] == "Epic"
    assert progress["next_rarity"] == "Legendary"
    assert progress["remaining"] == {"dungeons": 1300, "raids": 138}


def test_each_career_rank_doubles_all_stats_without_mutating_base():
    base = {
        "strength": 5,
        "agility": 6,
        "intellect": 7,
        "endurance": 8,
        "faith": 9,
    }
    cases = [
        (0, 0, "Common", 1),
        (50, 0, "Uncommon", 2),
        (150, 0, "Rare", 4),
        (500, 5, "Epic", 8),
        (2000, 150, "Legendary", 16),
    ]
    for dungeons, raids, rarity, multiplier in cases:
        adventurer = {
            **base,
            "career_dungeons_completed": dungeons,
            "career_raids_completed": raids,
        }
        assert CAREER_RARITY_STAT_MULTIPLIERS[rarity] == multiplier
        assert career_effective_stats(adventurer) == {
            stat: value * multiplier for stat, value in base.items()
        }
        assert {stat: adventurer[stat] for stat in base} == base


def test_recruitment_cost_is_free_for_six_then_progressive():
    # FASE 9A — i fondatori gratuiti sono SEI (era 5): il costo
    # progressivo parte dal settimo avventuriero creato.
    assert [base_model_cost_for_active_roster(n) for n in range(6)] == [0] * 6
    assert base_model_cost_for_active_roster(6) == 100
    assert base_model_cost_for_active_roster(7) == 125
    assert base_model_cost_for_active_roster(999) == 2500


def test_level_80_is_long_term_and_canonical():
    assert ADVENTURER_MAX_LEVEL == 80
    assert cumulative_xp_required_for_level(80) == 2_817_584


def test_all_canonical_group_sizes_are_supported():
    assert {enc.team_size for enc in DUNGEON_ENCOUNTERS.values()} == {3, 5, 7}
    assert {
        contract["required_party_count"] * 5
        for contract in RAID_CONTRACTS.values()
    } == {10, 15, 20, 40}
    assert {3, 5, 7, 10, 15, 20, 40}.issubset(set(SQUAD_SIZE.values()))


def test_every_dungeon_has_reviewed_lore_identity():
    assert set(DUNGEON_ENCOUNTERS) == set(DUNGEON_LORE)
    assert all(all(part.strip() for part in lore) for lore in DUNGEON_LORE.values())


def test_equipment_contract_has_ten_physical_slots():
    assert EQUIPMENT_SLOTS == (
        "weapon", "chest", "legs", "head", "accessory", "back",
        "ring_1", "ring_2", "trinket_1", "trinket_2",
    )


def test_company_ring_is_level_80_and_one_in_a_million():
    item = {
        "slug": ULTRA_RARE_RANDOM_DROP_SLUG,
        "rarity": "Unique",
        "required_adventurer_level": 80,
    }
    assert ultra_rare_random_drop_allowed(item)
    assert effective_catalog_required_level(item) == 80
    assert ONE_IN == 1_000_000
    assert company_ring_world_boss_eligible(
        boss_slug=WORLD_BOSS_SOURCE_SLUG,
        outcome="completed",
        contribution=1,
    )
    assert not company_ring_world_boss_eligible(
        boss_slug=WORLD_BOSS_SOURCE_SLUG,
        outcome="failed",
        contribution=1,
    )
    assert not company_ring_world_boss_eligible(
        boss_slug=WORLD_BOSS_SOURCE_SLUG,
        outcome="completed",
        contribution=0,
    )
