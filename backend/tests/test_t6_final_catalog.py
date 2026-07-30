from collections import Counter

from app.items.catalog_contract import RARITY_CATALOG_TARGETS
from app.items.final_catalog import (
    CLASS_RARITY_TARGET,
    FINAL_ITEM_CATALOG,
    UNIVERSAL_RARITY_TARGET,
    validate_final_catalog,
)
from app.rewards.company_ring import WORLD_BOSS_SOURCE_SLUG
from app.rewards.source_engine import evaluate_reward_eligibility
from app.shared.constants import ADVENTURER_MAX_LEVEL


def test_t6_catalog_passes_all_content_gates():
    report = validate_final_catalog()
    assert report["valid"], report["errors"][:20]
    assert report["total"] == 1500
    assert report["rarity_counts"] == RARITY_CATALOG_TARGETS
    assert set(report["class_counts"].values()) == {50}
    assert report["universal_count"] == 150


def test_t6_class_and_universal_rarity_math_is_exact():
    assert sum(CLASS_RARITY_TARGET.values()) == 50
    assert sum(UNIVERSAL_RARITY_TARGET.values()) == 150
    for rarity, target in RARITY_CATALOG_TARGETS.items():
        assert CLASS_RARITY_TARGET[rarity] * 27 + UNIVERSAL_RARITY_TARGET[rarity] == target


def test_t6_every_blueprint_is_singular_lore_linked_and_sourced():
    for field in ("id", "blueprint_id", "slug", "display_name_it"):
        values = [str(item[field]).casefold() for item in FINAL_ITEM_CATALOG]
        assert len(values) == len(set(values))
    assert all(item["lore_reviewed"] is True for item in FINAL_ITEM_CATALOG)
    assert all(item.get("lore_source") for item in FINAL_ITEM_CATALOG)
    assert all(item.get("flavor_text_it") for item in FINAL_ITEM_CATALOG)
    assert all(item.get("gameplay_effect_it") for item in FINAL_ITEM_CATALOG)
    assert all(item.get("acquisition_sources") for item in FINAL_ITEM_CATALOG)


def test_t6_only_company_ring_is_random_unique_and_it_comes_from_world_boss():
    random_unique = [
        item for item in FINAL_ITEM_CATALOG
        if item.get("acquisition_mode") == "ultra_rare_random_drop"
    ]
    assert len(random_unique) == 1
    ring = random_unique[0]
    assert ring["slug"] == "l_unico_anello_della_compagnia"
    assert ring["source"] == f"world_boss:{WORLD_BOSS_SOURCE_SLUG}"
    other_uniques = [
        item for item in FINAL_ITEM_CATALOG
        if item["rarity"] == "Unique" and item is not ring
    ]
    assert len(other_uniques) == 14
    assert Counter(
        item["acquisition_mode"] for item in other_uniques
    ) == {"guaranteed_unique_milestone": 14}


def test_t6_every_runtime_dungeon_and_raid_has_an_authored_item_pool():
    from app.expeditions.loot_tables import DUNGEON_LOOT_TABLES
    from app.raids.contracts import RAID_CONTRACTS

    source_pairs = {
        (source["source_type"], source.get("source_slug"))
        for item in FINAL_ITEM_CATALOG
        for source in item.get("acquisition_sources", [])
        if source.get("source_slug")
    }
    assert {
        ("dungeon", slug) for slug in DUNGEON_LOOT_TABLES
    } <= source_pairs
    assert {
        ("raid", slug) for slug in RAID_CONTRACTS
    } <= source_pairs
    raid_rarities = {
        (source["source_slug"], item["rarity"])
        for item in FINAL_ITEM_CATALOG
        for source in item.get("acquisition_sources", [])
        if source["source_type"] == "raid" and source.get("source_slug")
    }
    for slug, contract in RAID_CONTRACTS.items():
        for rarity in contract["reward_profile"]["allowed_rarities"]:
            assert (slug, rarity) in raid_rarities


def test_t6_non_random_unique_milestones_are_eligible_only_at_level_80():
    relic = next(
        item for item in FINAL_ITEM_CATALOG
        if item.get("acquisition_mode") == "guaranteed_unique_milestone"
    )
    denied = evaluate_reward_eligibility(
        item=relic,
        source_policy_id="unique_endgame_milestone",
        adventurer_level=ADVENTURER_MAX_LEVEL - 1,
        first_clear=True,
    )
    allowed = evaluate_reward_eligibility(
        item=relic,
        source_policy_id="unique_endgame_milestone",
        adventurer_level=ADVENTURER_MAX_LEVEL,
        first_clear=True,
    )
    assert not denied["eligible"]
    assert allowed["eligible"], allowed["reasons"]
