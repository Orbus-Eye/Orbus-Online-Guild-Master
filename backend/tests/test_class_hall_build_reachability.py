from app.class_halls.build_reachability import (
    audit_class_hall_build_reachability,
)
from app.class_halls.mechanics import resolve_class_mechanic
from app.seeds.seed_class_hall_content import (
    CANONICAL_CLASS_HALL_ITEM_SEED,
    validate_canonical_class_hall_content,
)


def test_all_eighty_one_builds_have_one_declared_reachable_hall_item():
    validate_canonical_class_hall_content()
    audit = audit_class_hall_build_reachability(
        CANONICAL_CLASS_HALL_ITEM_SEED
    )

    assert audit["expected_class_count"] == 27
    assert audit["expected_build_count"] == 81
    assert audit["reachable_build_count"] == 81
    assert audit["exact_declared_build_count"] == 81
    assert audit["invalid_declared_item_count"] == 0
    assert audit["missing_builds"] == []
    assert audit["all_builds_reachable"] is True


def test_every_declared_item_activates_the_build_printed_on_it():
    declared_items = [
        item
        for item in CANONICAL_CLASS_HALL_ITEM_SEED
        if item.get("build_path_id")
    ]
    assert len(declared_items) == 81

    for item in declared_items:
        class_slug = item["recommended_classes"][0]
        result = resolve_class_mechanic(
            adventurer={"canonical_class_slug": class_slug},
            equipment_items=[item],
        )
        assert result["active_build"]["resonance_active"] is True
        assert result["active_build"]["build_id"] == item["build_path_id"]
