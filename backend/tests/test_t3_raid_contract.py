"""T3 canonical raid responsibilities, phases and reward safety."""
from app.raids.contracts import (
    RAID_CONTRACTS,
    apply_raid_contract,
    raid_progression_rewards,
)


def test_four_raids_bridge_levels_forty_sixty_seventy_eighty():
    projected = [
        apply_raid_contract({"slug": slug})
        for slug in RAID_CONTRACTS
    ]
    assert [raid["required_level"] for raid in projected] == [40, 60, 70, 80]
    # FASE 8A — rebalance canonico dei poteri raid (era 1500/2400/3500/8000
    # pre-curva; questi sono i valori del contract attuale).
    assert [raid["recommended_power_combined"] for raid in projected] == [
        3100,
        7700,
        10925,
        24100,
    ]


def test_each_raid_has_contract_defined_distinct_parties_and_phases():
    for slug in RAID_CONTRACTS:
        raid = apply_raid_contract({"slug": slug})
        responsibilities = raid["party_responsibilities"]
        expected_parties = list(range(1, raid["required_party_count"] + 1))
        assert [row["party_idx"] for row in responsibilities] == expected_parties
        assert len({row["name_it"] for row in responsibilities}) == len(expected_parties)
        assert all(row["threat_tags"] for row in responsibilities)
        assert len(raid["phases"]) >= 2
        assert raid["phases"][-1]["required_parties"] == expected_parties


def test_only_level_eighty_raid_authorizes_legendary_blueprints():
    level_60 = apply_raid_contract({"slug": "broken-bastion-siege"})
    level_70 = apply_raid_contract({"slug": "necropolis-bells"})
    level_80 = apply_raid_contract({"slug": "dragon-vault"})
    assert level_60["reward_profile"]["legendary_allowed"] is False
    assert level_70["reward_profile"]["legendary_allowed"] is False
    assert level_80["reward_profile"]["legendary_allowed"] is True
    assert level_80["reward_profile"]["legendary_requires_victory"] is True


def test_no_raid_contract_can_drop_unique_or_the_unique_ring():
    for slug in RAID_CONTRACTS:
        profile = apply_raid_contract({"slug": slug})["reward_profile"]
        assert profile["unique_allowed"] is False
        assert profile.get("unique_ring_allowed", False) is False
        assert "Unique" not in profile["allowed_rarities"]


def test_progression_rewards_are_coherent_across_outcomes():
    wipe = raid_progression_rewards("dragon-vault", "wipe")
    partial = raid_progression_rewards("dragon-vault", "partial")
    victory = raid_progression_rewards("dragon-vault", "victory")
    assert wipe["raid_tokens"] < partial["raid_tokens"]
    assert partial["raid_tokens"] < victory["raid_tokens"]
    assert wipe["legendary_fragments"] == 0
    assert partial["legendary_fragments"] < victory["legendary_fragments"]
    assert victory["legendary_blueprint_eligible"] is True


def test_only_level_eighty_victory_is_blueprint_eligible():
    for slug in RAID_CONTRACTS:
        for outcome in ("wipe", "partial", "victory"):
            rewards = raid_progression_rewards(slug, outcome)
            expected = slug == "dragon-vault" and outcome == "victory"
            assert rewards["legendary_blueprint_eligible"] is expected
            assert rewards["unique_eligible"] is False
            assert rewards["unique_ring_eligible"] is False
