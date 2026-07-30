"""T4 runtime dungeon candidate filtering."""
from app.expeditions.loot_tables import _eligible_ordinary_pool


def test_runtime_pool_rejects_endgame_and_overlevel_items():
    pool = [
        {"id": "c", "slug": "comune", "rarity": "Common"},
        {"id": "r", "slug": "raro", "rarity": "Rare"},
        {"id": "l", "slug": "leggendario", "rarity": "Legendary"},
        {
            "id": "e",
            "slug": "epico-livello-alto",
            "rarity": "Epic",
            "required_adventurer_level": 50,
        },
    ]
    eligible = _eligible_ordinary_pool(
        pool,
        {"required_level": 10},
    )
    assert [item["id"] for item in eligible] == ["c", "r"]


def test_runtime_pool_allows_epic_at_sufficient_content_level():
    eligible = _eligible_ordinary_pool(
        [{
            "id": "e",
            "slug": "epico",
            "rarity": "Epic",
            "required_adventurer_level": 40,
        }],
        {"required_level": 40},
    )
    assert [item["id"] for item in eligible] == ["e"]
