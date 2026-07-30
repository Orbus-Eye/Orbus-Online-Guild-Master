"""T1 Wave-B expansion and cross-wave balance parity."""
from app.class_halls.catalog import CLASS_HALLS
from app.class_halls.mechanics import (
    CLASS_MECHANICS,
    CLASS_MECHANIC_BASE_BONUS,
    ITEM_BUILD_RESONANCE_BONUS,
    WAVE_A_CLASS_MECHANICS,
    WAVE_B_CLASS_MECHANICS,
    class_mechanic_public,
    resolve_class_mechanic,
)


WAVE_B_CASES = {
    "alchimista": ("vial", "cerusico"),
    "bardo": ("instrument", "cantore"),
    "druido": ("sickle", "predatore"),
    "monaco": ("fist", "pugno_vuoto"),
    "negromante": ("tome", "onomante"),
    "sciamano": ("totem", "totemista"),
    "cacciatore_del_vuoto": ("focus", "ancoratore"),
}


def test_wave_b_has_seven_mechanics_and_twenty_one_builds():
    assert set(WAVE_B_CLASS_MECHANICS) == set(WAVE_B_CASES)
    assert len(WAVE_B_CLASS_MECHANICS) == 7
    assert sum(
        len(mechanic.builds)
        for mechanic in WAVE_B_CLASS_MECHANICS.values()
    ) == 21
    assert len(CLASS_MECHANICS) == (
        len(WAVE_A_CLASS_MECHANICS) + len(WAVE_B_CLASS_MECHANICS)
    )


def test_wave_b_item_tags_select_the_expected_builds():
    for class_slug, (tag, expected_build) in WAVE_B_CASES.items():
        result = resolve_class_mechanic(
            adventurer={"canonical_class_slug": class_slug},
            equipment_items=[
                {
                    "slug": f"test-{class_slug}-{tag}",
                    "weapon_tags": [tag],
                    "armor_tags": [tag],
                }
            ],
        )
        assert result["active"] is True
        assert result["wave"] == "B"
        assert result["active_build"]["build_id"] == expected_build
        assert result["active_build"]["resonance_active"] is True
        assert result["power_bonus"] == (
            CLASS_MECHANIC_BASE_BONUS + ITEM_BUILD_RESONANCE_BONUS
        )


def test_wave_a_and_b_share_the_same_power_budget():
    all_resonant_bonuses = set()
    all_baseline_bonuses = set()
    for class_slug, mechanic in CLASS_MECHANICS.items():
        tag = mechanic.builds[0].item_tags[0]
        resonant = resolve_class_mechanic(
            adventurer={"canonical_class_slug": class_slug},
            equipment_items=[{"weapon_tags": [tag], "armor_tags": [tag]}],
        )
        baseline = resolve_class_mechanic(
            adventurer={"canonical_class_slug": class_slug},
            equipment_items=[],
        )
        all_resonant_bonuses.add(resonant["power_bonus"])
        all_baseline_bonuses.add(baseline["power_bonus"])
    assert all_resonant_bonuses == {3}
    assert all_baseline_bonuses == {1}


def test_wave_b_public_contract_exposes_three_item_paths():
    for class_slug in WAVE_B_CASES:
        public = class_mechanic_public(class_slug)
        assert public is not None
        assert public["wave"] == "B"
        assert len(public["builds"]) == 3
        assert all(build["item_tags"] for build in public["builds"])


def test_every_wave_b_build_uses_equipment_allowed_by_its_class_hall():
    profiles_by_class = {
        profile.canonical_class_slug: profile
        for profile in CLASS_HALLS.values()
    }
    for class_slug, mechanic in WAVE_B_CLASS_MECHANICS.items():
        profile = profiles_by_class[class_slug]
        allowed_tags = set(profile.weapon_tags) | set(profile.armor_tags)
        for build in mechanic.builds:
            assert allowed_tags.intersection(build.item_tags), (
                f"{class_slug}/{build.build_id} non ha item compatibili"
            )
