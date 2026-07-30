"""T0 item-first contract: quotas, endgame gates and acquisition separation."""
from app.items.catalog_contract import (
    ITEM_CATALOG_TARGET_TOTAL,
    RARITY_CATALOG_PRESENCE_PERCENT,
    RARITY_CATALOG_TARGETS,
    audit_catalog_items,
    ordinary_random_drop_allowed,
    public_catalog_contract,
    ultra_rare_random_drop_allowed,
    validate_item_blueprint,
)
from app.shared.constants import ADVENTURER_MAX_LEVEL
from app.equipment.level_gate import resolve_item_required_level


def test_catalog_targets_are_exact():
    assert ITEM_CATALOG_TARGET_TOTAL == 1500
    assert RARITY_CATALOG_TARGETS == {
        "Common": 525,
        "Uncommon": 375,
        "Rare": 300,
        "Epic": 225,
        "Legendary": 60,
        "Unique": 15,
    }
    assert sum(RARITY_CATALOG_TARGETS.values()) == 1500
    assert sum(RARITY_CATALOG_PRESENCE_PERCENT.values()) == 100


def test_public_contract_keeps_presence_separate_from_drop_chance():
    contract = public_catalog_contract()
    assert contract["presence_is_drop_chance"] is False
    assert contract["class_count"] == 27
    assert contract["items_per_class_target"] == 50
    assert contract["class_bound_target"] == 1350
    assert contract["universal_target"] == 150
    assert contract["adventurer_max_level"] == ADVENTURER_MAX_LEVEL == 80
    by_name = {row["name"]: row for row in contract["rarities"]}
    assert by_name["Legendary"]["ordinary_random_drop_allowed"] is False
    assert by_name["Unique"]["ordinary_random_drop_allowed"] is False
    assert by_name["Legendary"]["default_required_level"] == 80
    assert by_name["Unique"]["default_required_level"] == 80


def test_endgame_blueprints_cannot_lower_the_max_level_gate():
    legendary = {
        "slug": "legacy_legendary",
        "rarity": "Legendary",
        "required_adventurer_level": 12,
    }
    unique = {
        "slug": "not_the_ring",
        "rarity": "Unique",
        "level_required": 1,
    }
    assert "item.level.endgame_requires_max_level" in validate_item_blueprint(
        legendary
    )
    assert "item.level.endgame_requires_max_level" in validate_item_blueprint(
        unique
    )
    assert resolve_item_required_level(legendary) == ADVENTURER_MAX_LEVEL
    assert resolve_item_required_level(unique) == ADVENTURER_MAX_LEVEL


def test_ordinary_random_loot_stops_at_epic():
    assert ordinary_random_drop_allowed("Common")
    assert ordinary_random_drop_allowed("Epic")
    assert not ordinary_random_drop_allowed("Legendary")
    assert not ordinary_random_drop_allowed("Unique")
    assert "item.acquisition.ordinary_drop_forbidden" in validate_item_blueprint(
        {"slug": "wrong", "rarity": "Legendary", "acquisition_mode": "random_drop"}
    )


def test_every_ordinary_dungeon_table_excludes_endgame_rarities():
    from app.expeditions.loot_tables import DUNGEON_LOOT_TABLES

    for slug, table in DUNGEON_LOOT_TABLES.items():
        weights = table["success"]["weights"]
        assert "Legendary" not in weights, slug
        assert "Unique" not in weights, slug
    for slug in (
        "infernal-pit-5p",
        "celestial-citadel-5p",
        "world-tree-roots-5p",
    ):
        assert sum(DUNGEON_LOOT_TABLES[slug]["success"]["weights"].values()) == 100


def test_ultra_rare_random_roll_is_reserved_for_the_company_ring():
    ring = {
        "slug": "l_unico_anello_della_compagnia",
        "rarity": "Unique",
        "required_adventurer_level": ADVENTURER_MAX_LEVEL,
        "acquisition_mode": "ultra_rare_random_drop",
    }
    impostor = {
        "slug": "another_unique",
        "rarity": "Unique",
        "required_adventurer_level": ADVENTURER_MAX_LEVEL,
        "acquisition_mode": "ultra_rare_random_drop",
    }
    assert ultra_rare_random_drop_allowed(ring)
    assert validate_item_blueprint(ring) == []
    assert not ultra_rare_random_drop_allowed(impostor)
    assert "item.acquisition.ultra_rare_drop_reserved" in (
        validate_item_blueprint(impostor)
    )


def test_catalog_audit_reports_remaining_overflow_and_invalid_rows():
    rows = (
        [{"rarity": "Common"}] * 526
        + [{"rarity": "unique"}] * 2
        + [{"rarity": "mythic"}]
        + [{"rarity": "Epic", "is_test": True}]
        + [{"rarity": "Rare", "is_active": False}]
    )
    audit = audit_catalog_items(rows)
    assert audit["current_total"] == 529
    assert audit["invalid_rarity_count"] == 1
    assert audit["has_quota_overflow"] is True
    assert audit["by_rarity"]["Common"] == {
        "current": 526,
        "target": 525,
        "remaining": 0,
        "overflow": 1,
        "presence_percent": 35,
    }
    assert audit["by_rarity"]["Unique"]["current"] == 2
    assert audit["by_rarity"]["Unique"]["remaining"] == 13


def test_rarity_quota_guard_is_fail_closed_for_future_writes():
    counts = {"Unique": 15}
    errors = validate_item_blueprint(
        {"slug": "sixteenth_unique", "rarity": "Unique"},
        current_rarity_counts=counts,
    )
    assert "item.catalog.rarity_quota_exhausted" in errors
