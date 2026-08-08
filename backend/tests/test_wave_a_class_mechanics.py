"""T1 Wave-A class depth and item-driven build identities."""
from app.class_halls.mechanics import (
    CLASS_MECHANIC_BASE_BONUS,
    ITEM_BUILD_RESONANCE_BONUS,
    WAVE_A_CLASS_MECHANICS,
    class_mechanic_public,
    resolve_wave_a_class_mechanic,
)


SIGNATURE_CASES = {
    "guerriero": ("sword", "condottiero"),
    "ladro": ("dagger", "ombra"),
    "mago": ("staff", "arcanista"),
    "paladino": ("cloth", "ierofante"),
    "cacciatore_di_mostri": ("bow", "tiratore"),
}


def _resolve(class_slug: str, tag: str) -> dict:
    field = "armor_tags" if tag in {"cloth", "leather", "mail", "plate"} else "weapon_tags"
    return resolve_wave_a_class_mechanic(
        adventurer={
            "id": f"adv-{class_slug}",
            "canonical_class_slug": class_slug,
        },
        equipment_items=[{"slug": f"item-{tag}", field: [tag]}],
    )


def test_wave_a_has_five_distinct_mechanics_and_three_builds_each():
    assert set(WAVE_A_CLASS_MECHANICS) == set(SIGNATURE_CASES)
    assert len({
        mechanic.mechanic_id
        for mechanic in WAVE_A_CLASS_MECHANICS.values()
    }) == 5
    for class_slug, mechanic in WAVE_A_CLASS_MECHANICS.items():
        assert len(mechanic.builds) == 3, class_slug
        assert len({build.build_id for build in mechanic.builds}) == 3
        assert class_mechanic_public(class_slug)["builds"]


def test_each_signature_item_activates_its_intended_build_and_resonance():
    for class_slug, (tag, expected_build) in SIGNATURE_CASES.items():
        result = _resolve(class_slug, tag)
        assert result["active"] is True
        assert result["active_build"]["build_id"] == expected_build
        assert result["active_build"]["resonance_active"] is True
        assert result["item_resonance_bonus"] == ITEM_BUILD_RESONANCE_BONUS
        assert result["power_bonus"] == (
            CLASS_MECHANIC_BASE_BONUS + ITEM_BUILD_RESONANCE_BONUS
        )
        assert tag in result["active_build"]["matched_tags"]


def test_class_identity_exists_without_gear_but_item_resonance_does_not():
    result = resolve_wave_a_class_mechanic(
        adventurer={"canonical_class_slug": "mago"},
        equipment_items=[],
    )
    assert result["active"] is True
    assert result["power_bonus"] == CLASS_MECHANIC_BASE_BONUS
    assert result["item_resonance_bonus"] == 0
    assert result["active_build"]["resonance_active"] is False


def test_classes_without_an_implemented_mechanic_and_classless_are_unchanged():
    for class_slug in ("artificiere", "recruit_unassigned", ""):
        result = resolve_wave_a_class_mechanic(
            adventurer={"canonical_class_slug": class_slug},
            equipment_items=[{"weapon_tags": ["staff"]}],
        )
        assert result == {
            "active": False,
            "power_bonus": 0,
            "counter_tags": [],
        }


def test_each_mechanic_provides_canonical_threat_counters():
    for mechanic in WAVE_A_CLASS_MECHANICS.values():
        assert mechanic.counter_tags
        assert all(tag.startswith("counter_") for tag in mechanic.counter_tags)
