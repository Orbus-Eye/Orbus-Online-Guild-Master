"""Narrative coverage invariants for the tester-facing Common catalog."""

from app.scripts.seed_round13a_items_lore import (
    COMMON_LORE_OVERRIDES,
    _build_display_it,
    _build_flavor,
    _build_lore_tags,
)


def test_common_lore_overrides_are_complete_singular_and_player_facing():
    assert len(COMMON_LORE_OVERRIDES) == 37
    names = [
        entry["it"].strip().casefold()
        for entry in COMMON_LORE_OVERRIDES.values()
    ]
    flavors = [
        entry["flavor_it"].strip().casefold()
        for entry in COMMON_LORE_OVERRIDES.values()
    ]
    assert len(names) == len(set(names)) == 37
    assert len(flavors) == len(set(flavors)) == 37
    assert all(entry["tags"] for entry in COMMON_LORE_OVERRIDES.values())
    assert all(
        len(entry["flavor_it"]) <= 240
        for entry in COMMON_LORE_OVERRIDES.values()
    )


def test_common_lore_helpers_resolve_every_override_without_fallback():
    for slug, expected in COMMON_LORE_OVERRIDES.items():
        item = {
            "slug": slug,
            "name": f"Legacy {slug}",
            "rarity": "Common",
        }
        display_it, display_en = _build_display_it(item)
        flavor_it, flavor_en = _build_flavor(item)
        tags = _build_lore_tags(item)
        assert display_it == expected["it"]
        assert display_en == item["name"]
        assert flavor_it == expected["flavor_it"]
        assert flavor_en is None
        assert tags == expected["tags"]
