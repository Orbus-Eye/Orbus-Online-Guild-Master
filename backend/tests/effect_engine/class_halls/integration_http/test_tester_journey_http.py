"""Black-box tester journey against a running Orbus API.

The suite is opt-in so ordinary unit runs never depend on a local server:
set ``ORBUS_HTTP_E2E_BASE_URL`` to an isolated test deployment.
"""

from __future__ import annotations

import os
import uuid

import pytest
import requests


BASE_URL = os.environ.get("ORBUS_HTTP_E2E_BASE_URL", "").rstrip("/")

pytestmark = pytest.mark.skipif(
    not BASE_URL,
    reason="set ORBUS_HTTP_E2E_BASE_URL to run the black-box tester journey",
)


def _call(
    session: requests.Session,
    method: str,
    path: str,
    *,
    expected: int,
    headers: dict | None = None,
    json: dict | None = None,
) -> dict:
    response = session.request(
        method,
        f"{BASE_URL}{path}",
        headers=headers,
        json=json,
        timeout=30,
    )
    assert response.status_code == expected, (
        f"{method} {path}: expected {expected}, got {response.status_code}: "
        f"{response.text}"
    )
    return response.json()


def test_classless_to_hall_item_equip_and_first_expedition() -> None:
    """A tester can finish the complete item-first onboarding via public APIs."""
    suffix = uuid.uuid4().hex[:10]
    session = requests.Session()

    registered = _call(
        session,
        "POST",
        "/api/auth/register",
        expected=201,
        json={
            "email": f"hall_e2e_{suffix}@orbus.test",
            "username": f"hall_e2e_{suffix}",
            "password": "Test12345!",
        },
    )
    # Registration establishes the same cookie session used by the browser.
    # Keep the Bearer token for backward-compat coverage, but include the
    # double-submit header because cookie authentication has precedence.
    csrf = session.cookies.get("csrf_token")
    assert csrf
    auth = {
        "Authorization": f"Bearer {registered['access_token']}",
        "X-CSRF-Token": csrf,
    }
    created = _call(
        session,
        "POST",
        "/api/guilds",
        expected=201,
        headers=auth,
        json={
            "name": f"Sentieri {suffix}",
            "description": "Collaudo item-first isolato",
        },
    )
    assert created["guild"]["id"]

    roster = _call(
        session, "GET", "/api/adventurers", expected=200, headers=auth
    )["adventurers"]
    assert len(roster) == 5
    assert all(adventurer["is_starter"] is True for adventurer in roster)
    assert all(adventurer["class_selection_required"] is True for adventurer in roster)
    assert all(adventurer["class_slug"] is None for adventurer in roster)
    assert all(
        adventurer["recruit_status"] == "recruit_unassigned"
        for adventurer in roster
    )

    choices = _call(
        session,
        "GET",
        "/api/class-halls/assignment/choices",
        expected=200,
        headers=auth,
    )["halls"]
    assert len(choices) == 27
    assert len({choice["hall_id"] for choice in choices}) == 27
    assert len({choice["canonical_class_slug"] for choice in choices}) == 27
    assert all(choice["assignment_enabled"] is True for choice in choices)
    assert all(choice["starter_item_name_it"] for choice in choices)
    assert all(choice["lore_hook_it"] for choice in choices)

    catalog = _call(
        session, "GET", "/api/items", expected=200, headers=auth
    )["items"]
    display_names = [
        (item["display_name_it"] or item["name"]).strip().casefold()
        for item in catalog
    ]
    assert len(catalog) >= 261
    assert len(display_names) == len(set(display_names))
    assert len({item["slug"].casefold() for item in catalog}) == len(catalog)
    assert all(item["lore_reviewed"] is True for item in catalog)
    assert all(item["lore_source"] for item in catalog)
    assert sum(bool(item["flavor_text_it"]) for item in catalog) / len(catalog) >= 0.8
    hall_items = [
        item
        for item in catalog
        if str(item.get("source") or "").startswith("class_hall:")
    ]
    assert len(hall_items) == 135
    assert all(item["required_adventurer_level"] == 1 for item in hall_items)
    assert all(len(item["acquisition_sources"]) == 1 for item in hall_items)
    assert all(item["acquisition_hint_it"] for item in hall_items)
    assert sum(item["has_runtime_effect"] is True for item in hall_items) == 27
    build_path_items = [
        item for item in hall_items if item.get("build_path_id")
    ]
    assert len(build_path_items) == 81
    for hall_source in {item["source"] for item in hall_items}:
        hall_build_paths = {
            item["build_path_id"]
            for item in build_path_items
            if item["source"] == hall_source
        }
        assert len(hall_build_paths) == 3
    assert all(
        item.get("build_path_name_it")
        and item.get("build_path_description_it")
        and item.get("build_path_item_tags")
        for item in build_path_items
    )

    dungeons = _call(
        session, "GET", "/api/dungeons", expected=200, headers=auth
    )["dungeons"]
    first_dungeon = next(
        dungeon
        for dungeon in dungeons
        if dungeon["unlocked"]
    )
    assert first_dungeon["slug"] == "training-yard"
    assert first_dungeon["min_adventurer_level"] == 1
    assert first_dungeon["difficulty"] == 1
    assert first_dungeon["required_team_size"] == 3
    blocked = _call(
        session,
        "POST",
        "/api/expeditions",
        expected=423,
        headers=auth,
        json={
            "dungeon_id": first_dungeon["id"],
            "adventurer_ids": [row["id"] for row in roster[:3]],
        },
    )
    assert blocked["detail"]["code"] == "class_hall.selection_required"
    assert blocked["detail"]["count"] == 3

    selected_halls = ("hall_guerriero", "hall_ladro", "hall_mago")
    assignments: list[dict] = []
    first_trial_id: str | None = None
    first_reward: dict | None = None

    for adventurer, hall_id in zip(roster[:3], selected_halls, strict=True):
        trial = _call(
            session,
            "POST",
            f"/api/class-halls/{hall_id}/trial/start",
            expected=200,
            headers=auth,
            json={"adventurer_id": adventurer["id"]},
        )["trial"]
        assert trial["safe_mode"] is True
        assert trial["rewards_enabled"] is False
        completed = _call(
            session,
            "POST",
            f"/api/class-halls/{hall_id}/trial/complete",
            expected=200,
            headers=auth,
            json={
                "adventurer_id": adventurer["id"],
                "trial_id": trial["id"],
                "completed_steps": trial["required_steps"],
            },
        )["trial"]
        assert completed["status"] == "completed"
        confirmed = _call(
            session,
            "POST",
            f"/api/class-halls/{hall_id}/class/confirm",
            expected=200,
            headers=auth,
            json={
                "adventurer_id": adventurer["id"],
                "trial_id": trial["id"],
                "explicit_confirmation": True,
            },
        )
        assert confirmed["idempotent"] is False
        assert confirmed["adventurer"]["class_selection_required"] is False
        assert confirmed["adventurer"]["class_hall_id"] == hall_id
        assert confirmed["reward"]["status"] == "delivered"
        assignments.append(confirmed)
        if first_reward is None:
            first_reward = confirmed["reward"]
            first_trial_id = trial["id"]

    assert first_reward is not None
    assert first_trial_id is not None
    retry = _call(
        session,
        "POST",
        "/api/class-halls/hall_guerriero/class/confirm",
        expected=200,
        headers=auth,
        json={
            "adventurer_id": roster[0]["id"],
            "trial_id": first_trial_id,
            "explicit_confirmation": True,
        },
    )
    assert retry["idempotent"] is True
    assert retry["reward"]["grant_id"] == first_reward["grant_id"]

    inventory = _call(
        session, "GET", "/api/inventory", expected=200, headers=auth
    )["inventory"]
    signature = next(
        row for row in inventory if row["item_id"] == first_reward["item_id"]
    )
    assert signature["quantity"] == 1
    assert signature["available_quantity"] == 1
    assert signature["item"]["display_name_it"] == first_reward["item_name_it"]
    assert signature["item"]["lore_reviewed"] is True
    assert signature["item"]["lore_source"]
    assert signature["item"]["flavor_text_it"]
    assert signature["item"]["has_runtime_effect"] is True

    slot = signature["item"].get("slot_type") or signature["item"]["item_type"]
    equipped = _call(
        session,
        "POST",
        f"/api/adventurers/{roster[0]['id']}/equip",
        expected=201,
        headers=auth,
        json={"item_id": first_reward["item_id"], "slot": slot},
    )
    assert equipped["slots"][slot]["item"]["id"] == first_reward["item_id"]
    assert equipped["equipment_power"] > 0

    track_path = (
        f"/api/class-halls/hall_guerriero/item-track"
        f"?adventurer_id={roster[0]['id']}"
    )
    item_track = _call(
        session,
        "GET",
        track_path,
        expected=200,
        headers=auth,
    )
    assert item_track["total_count"] == 5
    assert [entry["status"] for entry in item_track["items"]] == [
        "claimed",
        "claimable",
        "locked",
        "locked",
        "locked",
    ]
    assert sum(
        bool(entry["item"].get("build_path_id"))
        for entry in item_track["items"]
    ) == 3
    build_lab = _call(
        session,
        "GET",
        (
            "/api/class-halls/hall_guerriero/build-lab"
            f"?adventurer_id={roster[0]['id']}"
        ),
        expected=200,
        headers=auth,
    )
    assert build_lab["total_builds"] == 3
    assert build_lab["current_build"]["build_id"] == "condottiero"
    assert build_lab["current_build"]["resonance_active"] is True
    condottiero_lab = next(
        path
        for path in build_lab["paths"]
        if path["build_id"] == "condottiero"
    )
    assert condottiero_lab["isolated_ready"] is True
    assert condottiero_lab["action_code"] == "run_activity"
    first_extra_slug = item_track["items"][1]["item"]["slug"]
    first_extra = _call(
        session,
        "POST",
        (
            "/api/class-halls/hall_guerriero/item-track/"
            f"{first_extra_slug}/claim"
        ),
        expected=200,
        headers=auth,
        json={"adventurer_id": roster[0]["id"]},
    )
    assert first_extra["reward"]["status"] == "delivered"
    assert first_extra["reward"]["idempotent"] is False
    assert first_extra["track"]["claimed_count"] == 2
    first_extra_retry = _call(
        session,
        "POST",
        (
            "/api/class-halls/hall_guerriero/item-track/"
            f"{first_extra_slug}/claim"
        ),
        expected=200,
        headers=auth,
        json={"adventurer_id": roster[0]["id"]},
    )
    assert first_extra_retry["reward"]["idempotent"] is True

    collection = _call(
        session,
        "GET",
        "/api/class-halls/collection-book",
        expected=200,
        headers=auth,
    )
    assert collection["total_count"] == 135
    assert collection["total_halls"] == 27
    assert collection["owned_count"] == 4
    assert len(collection["halls"]) == 27
    warrior_collection = next(
        hall
        for hall in collection["halls"]
        if hall["hall_id"] == "hall_guerriero"
    )
    assert warrior_collection["owned_count"] == 2
    assert warrior_collection["equipped_count"] == 1
    assert [entry["order"] for entry in warrior_collection["items"]] == [
        0, 1, 2, 3, 4,
    ]
    assert [entry["status"] for entry in warrior_collection["items"]] == [
        "equipped",
        "owned",
        "undiscovered",
        "undiscovered",
        "undiscovered",
    ]

    model = _call(
        session,
        "GET",
        "/api/recruitment/model",
        expected=200,
        headers=auth,
    )
    assert model["method"] == "player_authored_base_model"
    assert model["random_generation"] is False
    assert model["active_roster"] == model["roster_cap"] == 5
    assert model["races"]
    capacity_block = _call(
        session,
        "POST",
        "/api/recruitment/model",
        expected=423,
        headers=auth,
        json={
            "name": "Sesta Fondatrice",
            "race_slug": model["races"][0]["slug"],
            "gender": "female",
        },
    )
    assert capacity_block["detail"]["code"] == "roster_over_capacity"
    assert capacity_block["detail"]["current"] == 5
    assert capacity_block["detail"]["cap"] == 5

    started = _call(
        session,
        "POST",
        "/api/expeditions",
        expected=201,
        headers=auth,
        json={
            "dungeon_id": first_dungeon["id"],
            "adventurer_ids": [row["id"] for row in roster[:3]],
        },
    )
    assert started["expedition"]["status"] == "in_progress"
    assert len(started["members"]) == 3
    assert started["expedition"]["team_power"] > 0
    assert started["expedition"]["item_effect_power_bonus"] == 2
    assert started["expedition"]["equipment_base_power_bonus"] > 0
    warrior_member = next(
        member
        for member in started["members"]
        if member["adventurer_id"] == roster[0]["id"]
    )
    assert warrior_member["item_effect_power_bonus"] == 2
    assert warrior_member["item_effect_stat_bonuses"] == {"endurance": 2}
    assert len(warrior_member["item_effects_snapshot"]) == 1
    visible_effect = warrior_member["item_effects_snapshot"][0]
    assert visible_effect["item_id"] == first_reward["item_id"]
    assert visible_effect["effect_id"] == "item.krastlov.first_oath"
    assert visible_effect["target_stat"] == "endurance"
    assert visible_effect["magnitude"] == 2
    assert visible_effect["summary_it"]
    assert visible_effect["lore_source"]

    expedition_id = started["expedition"]["id"]
    fetched = _call(
        session,
        "GET",
        f"/api/expeditions/{expedition_id}",
        expected=200,
        headers=auth,
    )
    assert fetched["expedition"]["id"] == expedition_id
    assert fetched["expedition"]["item_effect_power_bonus"] == 2
    assert next(
        member
        for member in fetched["members"]
        if member["adventurer_id"] == roster[0]["id"]
    )["item_effects_snapshot"][0]["item_name"] == first_reward["item_name_it"]


def test_admin_tester_can_reset_and_audit_the_classless_journey() -> None:
    """The tester console can create a repeatable, vision-aligned journey."""
    session = requests.Session()
    logged_in = _call(
        session,
        "POST",
        "/api/auth/login",
        expected=200,
        json={
            "email": "tester@orbus.test",
            "password": "password123",
        },
    )
    csrf = session.cookies.get("csrf_token")
    assert csrf
    auth = {
        "Authorization": f"Bearer {logged_in['access_token']}",
        "X-CSRF-Token": csrf,
    }
    target = "tester@orbus.test"
    status_path = f"/api/admin/tester-tools/status?target_email={target}"
    status = _call(
        session,
        "GET",
        status_path,
        expected=200,
        headers=auth,
    )
    if not status["guild"]["id"]:
        suffix = uuid.uuid4().hex[:8]
        _call(
            session,
            "POST",
            "/api/guilds",
            expected=201,
            headers=auth,
            json={
                "name": f"Tester Sentieri {suffix}",
                "description": "Gilda locale per reset Class Hall",
            },
        )

    refused = _call(
        session,
        "POST",
        "/api/admin/tester-tools/reset-class-hall-journey",
        expected=400,
        headers=auth,
        json={"target_email": target, "confirm": False},
    )
    assert (
        refused["detail"]["code"]
        == "tester_journey.explicit_confirmation_required"
    )

    first_reset = _call(
        session,
        "POST",
        "/api/admin/tester-tools/reset-class-hall-journey",
        expected=200,
        headers=auth,
        json={"target_email": target, "confirm": True},
    )
    assert first_reset["created_classless_adventurers"] == 5
    assert first_reset["class_selection_required"] is True
    assert first_reset["history_preserved"] is True

    roster = _call(
        session,
        "GET",
        "/api/adventurers",
        expected=200,
        headers=auth,
    )["adventurers"]
    assert len(roster) == 5
    assert all(row["class_selection_required"] is True for row in roster)

    profile = next(
        choice
        for choice in _call(
            session,
            "GET",
            "/api/class-halls/assignment/choices",
            expected=200,
            headers=auth,
        )["halls"]
        if choice["hall_id"] == "hall_guerriero"
    )
    trial = _call(
        session,
        "POST",
        "/api/class-halls/hall_guerriero/trial/start",
        expected=200,
        headers=auth,
        json={"adventurer_id": roster[0]["id"]},
    )["trial"]
    _call(
        session,
        "POST",
        "/api/class-halls/hall_guerriero/trial/complete",
        expected=200,
        headers=auth,
        json={
            "adventurer_id": roster[0]["id"],
            "trial_id": trial["id"],
            "completed_steps": profile["trial_steps"],
        },
    )
    assigned = _call(
        session,
        "POST",
        "/api/class-halls/hall_guerriero/class/confirm",
        expected=200,
        headers=auth,
        json={
            "adventurer_id": roster[0]["id"],
            "trial_id": trial["id"],
            "explicit_confirmation": True,
        },
    )
    inventory = _call(
        session,
        "GET",
        "/api/inventory",
        expected=200,
        headers=auth,
    )["inventory"]
    signature = next(
        row
        for row in inventory
        if row["item_id"] == assigned["reward"]["item_id"]
    )
    slot = signature["item"].get("slot_type") or signature["item"]["item_type"]
    _call(
        session,
        "POST",
        f"/api/adventurers/{roster[0]['id']}/equip",
        expected=201,
        headers=auth,
        json={"item_id": signature["item_id"], "slot": slot},
    )

    second_reset = _call(
        session,
        "POST",
        "/api/admin/tester-tools/reset-class-hall-journey",
        expected=200,
        headers=auth,
        json={"target_email": target, "confirm": True},
    )
    assert second_reset["archived_adventurers"] == 5
    assert second_reset["equipment_released"] == 1
    new_roster = _call(
        session,
        "GET",
        "/api/adventurers",
        expected=200,
        headers=auth,
    )["adventurers"]
    assert len(new_roster) == 5
    assert {row["id"] for row in new_roster}.isdisjoint(
        {row["id"] for row in roster}
    )
    assert all(row["class_selection_required"] is True for row in new_roster)

    matrix = _call(
        session,
        "GET",
        f"/api/admin/tester-tools/smoke-matrix?target_email={target}",
        expected=200,
        headers=auth,
    )
    assert matrix["ready_for_tester_slice"] is True
    assert matrix["blocking_failures"] == []
    assert matrix["summary"]["classless_adventurers"] == 5
    assert matrix["summary"]["invalid_class_states"] == 0
    assert matrix["summary"]["reachable_hall_builds"] == 81
    reachability = next(
        check
        for check in matrix["checks"]
        if check["key"] == "hall_build_reachability"
    )
    assert reachability["ok"] is True
    long_term = next(
        check
        for check in matrix["checks"]
        if check["key"] == "long_term_item_catalog"
    )
    assert long_term["blocking"] is False
    assert long_term["target"] == 1500

    granted = _call(
        session,
        "POST",
        "/api/admin/tester-tools/grant-adventurers",
        expected=200,
        headers=auth,
        json={"target_email": target},
    )
    assert granted["total_after"] == 20
    assert granted["class_selection_required"] is True
    final_status = _call(
        session,
        "GET",
        status_path,
        expected=200,
        headers=auth,
    )
    assert final_status["roster"]["active_count"] == 20
    assert final_status["roster"]["classless_count"] == 20
    assert final_status["roster"]["invalid_class_state_count"] == 0

    maxed = _call(
        session,
        "POST",
        "/api/admin/tester-tools/set-max",
        expected=200,
        headers=auth,
        json={"target_email": target, "confirm": True},
    )
    assert maxed["active_roster"] == 39
    max_status = _call(
        session,
        "GET",
        status_path,
        expected=200,
        headers=auth,
    )
    assert max_status["roster"]["active_count"] == 39
    assert max_status["roster"]["classless_count"] == 39

    minimized = _call(
        session,
        "POST",
        "/api/admin/tester-tools/set-min",
        expected=200,
        headers=auth,
        json={"target_email": target, "confirm": True},
    )
    assert minimized["active_roster"] == 3
    assert minimized["archived"] == 36
    min_status = _call(
        session,
        "GET",
        status_path,
        expected=200,
        headers=auth,
    )
    assert min_status["roster"]["active_count"] == 3
    assert min_status["roster"]["invalid_class_state_count"] == 0
