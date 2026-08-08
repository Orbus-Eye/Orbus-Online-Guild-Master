"""T1 final Wave-D/E expansion for all twenty-seven classes."""
from collections import Counter

from app.class_halls.catalog import CLASS_HALLS
from app.class_halls.mechanics import (
    CLASS_MECHANICS,
    WAVE_D_CLASS_MECHANICS,
    WAVE_E_CLASS_MECHANICS,
    class_mechanic_public,
    resolve_class_mechanic,
)


WAVE_D_CASES = {
    "astrologo": ("tome", "efemerista"),
    "burattinaio": ("crossbow", "ballestario"),
    "giocatore_d_azzardo": ("dagger", "baro"),
    "parassita": ("fist", "innestato"),
    "pittore": ("staff", "affreschista"),
    "sognatore": ("focus", "lucido"),
}

WAVE_E_CASES = {
    "cacciatore_del_sangue": ("spear", "trafittore"),
    "cavaliere_della_morte": ("shield", "baluardo_nero"),
    "cavaliere_di_draghi": ("sword", "lama_del_drago"),
}


def test_final_waves_cover_nine_classes_and_twenty_seven_builds():
    assert set(WAVE_D_CLASS_MECHANICS) == set(WAVE_D_CASES)
    assert set(WAVE_E_CLASS_MECHANICS) == set(WAVE_E_CASES)
    assert len(WAVE_D_CLASS_MECHANICS) == 6
    assert len(WAVE_E_CLASS_MECHANICS) == 3
    assert sum(
        len(mechanic.builds)
        for mechanic in (
            *WAVE_D_CLASS_MECHANICS.values(),
            *WAVE_E_CLASS_MECHANICS.values(),
        )
    ) == 27


def test_all_twenty_seven_classes_have_three_builds():
    assert len(CLASS_MECHANICS) == 27
    assert sum(len(mechanic.builds) for mechanic in CLASS_MECHANICS.values()) == 81
    assert Counter(mechanic.wave for mechanic in CLASS_MECHANICS.values()) == {
        "A": 5,
        "B": 7,
        "C": 6,
        "D": 6,
        "E": 3,
    }


def test_final_wave_item_tags_select_expected_builds():
    for class_slug, (tag, expected_build) in {
        **WAVE_D_CASES,
        **WAVE_E_CASES,
    }.items():
        result = resolve_class_mechanic(
            adventurer={"canonical_class_slug": class_slug},
            equipment_items=[{"tags": [tag]}],
        )
        assert result["active"] is True
        assert result["active_build"]["build_id"] == expected_build
        assert result["power_bonus"] == 3


def test_all_eighty_one_builds_use_class_hall_compatible_items():
    profiles_by_class = {
        profile.canonical_class_slug: profile
        for profile in CLASS_HALLS.values()
    }
    assert set(profiles_by_class) == set(CLASS_MECHANICS)
    for class_slug, mechanic in CLASS_MECHANICS.items():
        profile = profiles_by_class[class_slug]
        allowed_tags = set(profile.weapon_tags) | set(profile.armor_tags)
        for build in mechanic.builds:
            assert allowed_tags.intersection(build.item_tags), (
                f"{class_slug}/{build.build_id} non ha item compatibili"
            )


def test_every_class_hall_exposes_its_three_item_paths():
    for class_slug, mechanic in CLASS_MECHANICS.items():
        public = class_mechanic_public(class_slug)
        assert public is not None
        assert public["wave"] == mechanic.wave
        assert len(public["builds"]) == 3
