"""T4 reward source, eligibility, binding and dedup contract."""
from app.rewards.source_engine import (
    SOURCE_POLICIES,
    evaluate_reward_eligibility,
    reward_grant_key,
)
from app.rewards.simulator import (
    MAX_TESTER_TRIALS,
    simulate_company_ring,
    source_inflation_projection,
)


def test_presence_percentages_are_not_source_drop_rates():
    policies_with_probability = [
        source_id
        for source_id, policy in SOURCE_POLICIES.items()
        if "private_drop_probability" in policy
    ]
    assert policies_with_probability == ["company_ring_ultra_rare"]
    assert SOURCE_POLICIES["company_ring_ultra_rare"][
        "private_drop_probability"
    ] == 0.000001


def test_ordinary_dungeons_reject_endgame_rarities():
    for rarity in ("Legendary", "Unique"):
        result = evaluate_reward_eligibility(
            item={"slug": f"test-{rarity}", "rarity": rarity},
            source_policy_id="ordinary_dungeon",
            adventurer_level=80,
        )
        assert result["eligible"] is False
        assert "reward.rarity.not_allowed_by_source" in result["reasons"]


def test_legendary_requires_level_eighty_and_authorized_raid():
    item = {"slug": "blueprint-leggendario", "rarity": "Legendary"}
    low = evaluate_reward_eligibility(
        item=item,
        source_policy_id="raid_level80_victory",
        adventurer_level=79,
    )
    endgame = evaluate_reward_eligibility(
        item=item,
        source_policy_id="raid_level80_victory",
        adventurer_level=80,
    )
    assert low["eligible"] is False
    assert endgame["eligible"] is True
    assert endgame["binding_policy"] == "hard"


def test_only_company_ring_can_use_unique_random_source():
    ring = {
        "slug": "l_unico_anello_della_compagnia",
        "rarity": "Unique",
    }
    allowed = evaluate_reward_eligibility(
        item=ring,
        source_policy_id="company_ring_ultra_rare",
        adventurer_level=80,
    )
    wrong_item = evaluate_reward_eligibility(
        item={"slug": "altro-unico", "rarity": "Unique"},
        source_policy_id="company_ring_ultra_rare",
        adventurer_level=80,
    )
    assert allowed["eligible"] is True
    assert wrong_item["eligible"] is False


def test_global_unique_guard_blocks_second_ring():
    result = evaluate_reward_eligibility(
        item={
            "slug": "l_unico_anello_della_compagnia",
            "rarity": "Unique",
        },
        source_policy_id="company_ring_ultra_rare",
        adventurer_level=80,
        global_unique_already_granted=True,
    )
    assert result["eligible"] is False
    assert "reward.unique.already_granted" in result["reasons"]


def test_first_clear_and_duplicate_policies_are_explicit():
    item = {"slug": "firma-hall", "rarity": "Uncommon"}
    denied = evaluate_reward_eligibility(
        item=item,
        source_policy_id="class_hall_assignment",
        adventurer_level=3,
        first_clear=False,
    )
    duplicate = evaluate_reward_eligibility(
        item=item,
        source_policy_id="class_hall_assignment",
        adventurer_level=3,
        first_clear=True,
        already_owned=True,
    )
    assert "reward.first_clear.required" in denied["reasons"]
    assert duplicate["duplicate_action"] == "deny"
    assert duplicate["eligible"] is False


def test_grant_key_is_stable_and_source_instance_sensitive():
    first = reward_grant_key(
        guild_id="g1",
        source_policy_id="ordinary_dungeon",
        source_instance_id="run-1",
        item_slug="item-a",
    )
    retry = reward_grant_key(
        guild_id="g1",
        source_policy_id="ordinary_dungeon",
        source_instance_id="run-1",
        item_slug="item-a",
    )
    other_run = reward_grant_key(
        guild_id="g1",
        source_policy_id="ordinary_dungeon",
        source_instance_id="run-2",
        item_slug="item-a",
    )
    assert first == retry
    assert first != other_run


def test_ring_simulator_is_read_only_and_deterministic():
    first = simulate_company_ring(trials=100_000, seed=7)
    retry = simulate_company_ring(trials=100_000, seed=7)
    assert first == retry
    assert first["simulation_only"] is True
    assert first["grants_created"] == 0
    assert first["inventory_mutations"] == 0
    assert first["one_in"] == 1_000_000


def test_ring_simulator_rejects_unbounded_workloads():
    try:
        simulate_company_ring(trials=MAX_TESTER_TRIALS + 1)
    except ValueError as exc:
        assert str(exc) == "reward.simulation.trials_out_of_range"
    else:
        raise AssertionError("trial cap non applicato")


def test_inflation_projection_flags_large_net_supply():
    safe = source_inflation_projection(
        eligible_runs=1000,
        grants_per_run=0.5,
        duplicate_conversion_rate=0.2,
    )
    unsafe = source_inflation_projection(
        eligible_runs=100_000,
        grants_per_run=0.5,
        duplicate_conversion_rate=0.0,
    )
    assert safe["net_new_items"] == 400
    assert safe["requires_review"] is False
    assert unsafe["requires_review"] is True
