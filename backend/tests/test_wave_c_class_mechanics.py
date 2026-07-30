"""T1 Wave-C expansion and item compatibility."""
from app.class_halls.catalog import CLASS_HALLS
from app.class_halls.mechanics import (
    CLASS_MECHANICS,
    CLASS_MECHANIC_BASE_BONUS,
    ITEM_BUILD_RESONANCE_BONUS,
    WAVE_C_CLASS_MECHANICS,
    class_mechanic_public,
    resolve_class_mechanic,
)


WAVE_C_CASES = {
    "artificiere": ("hammer", "ingegnere"),
    "cartografo": ("crossbow", "rilevatore"),
    "cronista": ("tome", "archivista"),
    "fabbro_arcano": ("axe", "incisore"),
    "mercante": ("rapier", "contrattatore"),
    "runista": ("focus", "vincolatore"),
}


def test_wave_c_has_six_mechanics_and_eighteen_builds():
    assert set(WAVE_C_CLASS_MECHANICS) == set(WAVE_C_CASES)
    assert len(WAVE_C_CLASS_MECHANICS) == 6
    assert sum(
        len(mechanic.builds)
        for mechanic in WAVE_C_CLASS_MECHANICS.values()
    ) == 18
    assert len(CLASS_MECHANICS) == 18


def test_wave_c_item_tags_select_the_expected_builds():
    for class_slug, (tag, expected_build) in WAVE_C_CASES.items():
        result = resolve_class_mechanic(
            adventurer={"canonical_class_slug": class_slug},
            equipment_items=[{"slug": f"test-{class_slug}", "tags": [tag]}],
        )
        assert result["active"] is True
        assert result["wave"] == "C"
        assert result["active_build"]["build_id"] == expected_build
        assert result["active_build"]["resonance_active"] is True
        assert result["power_bonus"] == (
            CLASS_MECHANIC_BASE_BONUS + ITEM_BUILD_RESONANCE_BONUS
        )


def test_every_wave_c_build_uses_equipment_allowed_by_its_class_hall():
    profiles_by_class = {
        profile.canonical_class_slug: profile
        for profile in CLASS_HALLS.values()
    }
    for class_slug, mechanic in WAVE_C_CLASS_MECHANICS.items():
        profile = profiles_by_class[class_slug]
        allowed_tags = set(profile.weapon_tags) | set(profile.armor_tags)
        for build in mechanic.builds:
            assert allowed_tags.intersection(build.item_tags), (
                f"{class_slug}/{build.build_id} non ha item compatibili"
            )


def test_wave_c_public_contract_exposes_three_item_paths():
    for class_slug in WAVE_C_CASES:
        public = class_mechanic_public(class_slug)
        assert public is not None
        assert public["wave"] == "C"
        assert len(public["builds"]) == 3


def test_all_three_waves_keep_the_same_power_budget():
    baseline_bonuses = set()
    resonant_bonuses = set()
    for class_slug, mechanic in CLASS_MECHANICS.items():
        tag = mechanic.builds[0].item_tags[0]
        baseline = resolve_class_mechanic(
            adventurer={"canonical_class_slug": class_slug},
            equipment_items=[],
        )
        resonant = resolve_class_mechanic(
            adventurer={"canonical_class_slug": class_slug},
            equipment_items=[{"tags": [tag]}],
        )
        baseline_bonuses.add(baseline["power_bonus"])
        resonant_bonuses.add(resonant["power_bonus"])
    assert baseline_bonuses == {1}
    assert resonant_bonuses == {3}
