from app.class_halls.build_lab import compile_class_hall_build_lab
from app.class_halls.catalog import CLASS_HALLS
from app.seeds.seed_class_hall_content import (
    CANONICAL_CLASS_HALL_ITEM_SEED,
)


def _warrior_context():
    profile = CLASS_HALLS["hall_guerriero"]
    items = [
        {**item, "id": f"id-{item['slug']}"}
        for item in CANONICAL_CLASS_HALL_ITEM_SEED
        if item["source"] == "class_hall:hall_guerriero"
        and item.get("build_path_id")
    ]
    adventurer = {
        "id": "adventurer-warrior",
        "name": "Alda",
        "level": 10,
        "class_hall_id": profile.hall_id,
        "canonical_class_slug": profile.canonical_class_slug,
        "class_slug": profile.canonical_class_slug,
    }
    return profile, adventurer, items


def test_build_lab_marks_a_single_path_as_isolated_and_ready():
    profile, adventurer, items = _warrior_context()
    target = next(
        item for item in items if item["build_path_id"] == "bastione"
    )
    result = compile_class_hall_build_lab(
        profile=profile,
        adventurer=adventurer,
        path_items=items,
        inventory_rows=[
            {"item_id": item["id"], "quantity": 1} for item in items
        ],
        equipped_rows=[
            {"item_id": target["id"], "slot": target["slot_type"]}
        ],
        equipped_items=[target],
    )

    bastione = next(
        path for path in result["paths"] if path["build_id"] == "bastione"
    )
    assert result["isolated_ready_count"] == 1
    assert bastione["active_now"] is True
    assert bastione["isolated_ready"] is True
    assert bastione["action_code"] == "run_activity"


def test_build_lab_identifies_competing_equipped_paths():
    profile, adventurer, items = _warrior_context()
    bastione_item = next(
        item for item in items if item["build_path_id"] == "bastione"
    )
    condottiero_item = next(
        item for item in items if item["build_path_id"] == "condottiero"
    )
    result = compile_class_hall_build_lab(
        profile=profile,
        adventurer=adventurer,
        path_items=items,
        inventory_rows=[
            {"item_id": item["id"], "quantity": 1} for item in items
        ],
        equipped_rows=[
            {"item_id": bastione_item["id"], "slot": "armor"},
            {"item_id": condottiero_item["id"], "slot": "weapon"},
        ],
        equipped_items=[bastione_item, condottiero_item],
    )

    bastione = next(
        path for path in result["paths"] if path["build_id"] == "bastione"
    )
    assert bastione["isolated_ready"] is False
    assert bastione["action_code"] == "unequip_competing_items"
    assert bastione["competing_equipped_items"][0][
        "activates_build_id"
    ] == "condottiero"
