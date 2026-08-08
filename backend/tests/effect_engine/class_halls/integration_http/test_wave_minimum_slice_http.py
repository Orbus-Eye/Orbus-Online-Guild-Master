"""Managed-API proof of all 27 item-first journeys and 81 class builds."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import os

from pymongo import MongoClient
import pytest
import requests

from app.territory.structures import STRUCTURE_CATALOG


BASE_URL = os.environ.get("ORBUS_HTTP_E2E_BASE_URL", "").rstrip("/")
MONGO_URL = os.environ.get("MONGO_URL", "")
DB_NAME = os.environ.get("DB_NAME", "")

pytestmark = pytest.mark.skipif(
    not BASE_URL or not MONGO_URL or not DB_NAME,
    reason="requires the managed T5 API and its isolated Mongo database",
)

EXPECTED_WAVE_CLASS_COUNTS = {"A": 5, "B": 7, "C": 6, "D": 6, "E": 3}


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


def _admin_session() -> tuple[requests.Session, dict]:
    session = requests.Session()
    logged_in = _call(
        session,
        "POST",
        "/api/auth/login",
        expected=200,
        json={"email": "tester@orbus.test", "password": "password123"},
    )
    csrf = session.cookies.get("csrf_token")
    assert csrf
    return session, {
        "Authorization": f"Bearer {logged_in['access_token']}",
        "X-CSRF-Token": csrf,
    }


def _assign_hall(
    session: requests.Session,
    auth: dict,
    *,
    adventurer_id: str,
    hall_id: str,
) -> dict:
    trial = _call(
        session,
        "POST",
        f"/api/class-halls/{hall_id}/trial/start",
        expected=200,
        headers=auth,
        json={"adventurer_id": adventurer_id},
    )["trial"]
    _call(
        session,
        "POST",
        f"/api/class-halls/{hall_id}/trial/complete",
        expected=200,
        headers=auth,
        json={
            "adventurer_id": adventurer_id,
            "trial_id": trial["id"],
            "completed_steps": trial["required_steps"],
        },
    )
    return _call(
        session,
        "POST",
        f"/api/class-halls/{hall_id}/class/confirm",
        expected=200,
        headers=auth,
        json={
            "adventurer_id": adventurer_id,
            "trial_id": trial["id"],
            "explicit_confirmation": True,
        },
    )


def _finish_expeditions(db, expedition_ids: list[str]) -> None:
    past = (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat()
    result = db.expeditions.update_many(
        {"id": {"$in": expedition_ids}, "status": "in_progress"},
        {"$set": {"completes_at": past}},
    )
    assert result.modified_count == len(expedition_ids)


def _run_solo_training(
    session: requests.Session,
    auth: dict,
    db,
    *,
    dungeon_id: str,
    adventurer_ids: list[str],
) -> list[str]:
    assert len(adventurer_ids) % 3 == 0
    expedition_ids = []
    for offset in range(0, len(adventurer_ids), 3):
        team_ids = adventurer_ids[offset:offset + 3]
        started = _call(
            session,
            "POST",
            "/api/expeditions",
            expected=201,
            headers=auth,
            json={
                "dungeon_id": dungeon_id,
                "adventurer_ids": team_ids,
            },
        )
        expedition_ids.append(started["expedition"]["id"])
    _finish_expeditions(db, expedition_ids)
    _call(
        session,
        "GET",
        "/api/expeditions",
        expected=200,
        headers=auth,
    )
    completed = list(
        db.expeditions.find(
            {"id": {"$in": expedition_ids}},
            {"_id": 0, "id": 1, "status": 1},
        )
    )
    assert len(completed) == len(expedition_ids)
    assert all(row["status"] == "completed" for row in completed)
    return expedition_ids


def _run_comparable_samples(
    session: requests.Session,
    auth: dict,
    db,
    *,
    dungeon: dict,
    team_ids: list[str],
    sample_count: int,
    class_slug: str,
    build_id: str,
    power_observations: list[dict],
) -> list[str]:
    expedition_ids = []
    recommended = int(dungeon["recommended_power"])
    for _index in range(sample_count):
        started = _call(
            session,
            "POST",
            "/api/expeditions",
            expected=201,
            headers=auth,
            json={
                "dungeon_id": dungeon["id"],
                "adventurer_ids": team_ids,
            },
        )["expedition"]
        ratio = int(started["final_team_power"]) / recommended
        power_observations.append(
            {
                "class_slug": class_slug,
                "build_id": build_id,
                "slug": dungeon["slug"],
                "team_power": started["final_team_power"],
                "recommended_power": recommended,
                "ratio": ratio,
            }
        )
        expedition_ids.append(started["id"])
        _finish_expeditions(db, [started["id"]])
        maxed = _call(
            session,
            "GET",
            f"/api/expeditions/{started['id']}",
            expected=200,
            headers=auth,
        )
    return expedition_ids


def _complete_raid(
    session: requests.Session,
    auth: dict,
    db,
    *,
    adventurer_ids: list[str],
    raid_slug: str,
) -> str:
    assert len(adventurer_ids) in {10, 15, 20, 40}
    party_count = len(adventurer_ids) // 5
    parties = [
        {
            "party_idx": index + 1,
            "adventurer_ids": adventurer_ids[index * 5:(index + 1) * 5],
        }
        for index in range(party_count)
    ]
    raid = _call(
        session,
        "POST",
        "/api/raids/start",
        expected=201,
        headers=auth,
        json={"raid_slug": raid_slug, "parties": parties},
    )["raid"]
    past = (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat()
    assert db.raids.update_one(
        {"id": raid["id"], "status": "in_progress"},
        {"$set": {"ends_at": past}},
    ).modified_count == 1
    completed = _call(
        session,
        "POST",
        f"/api/raids/{raid['id']}/complete",
        expected=200,
        headers=auth,
    )["raid"]
    assert completed["status"] == "completed"
    assert db.raid_reward_grants.count_documents(
        {"raid_id": raid["id"], "status": "applied"}
    ) == 1
    return raid["id"]


def _advance_raid_cooldown(db, raid_id: str) -> None:
    raid = db.raids.find_one({"id": raid_id}, {"_id": 0, "guild_id": 1})
    assert raid and raid.get("guild_id")
    elapsed = (
        datetime.now(timezone.utc) - timedelta(minutes=16)
    ).isoformat()
    assert db.guilds.update_one(
        {"id": raid["guild_id"]},
        {"$set": {"last_raid_completed_at": elapsed}},
    ).modified_count == 1


def test_complete_item_first_journey_and_tuning_for_all_classes() -> None:
    session, auth = _admin_session()
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    try:
        target = "tester@orbus.test"
        _call(
            session,
            "POST",
            "/api/admin/tester-tools/reset-class-hall-journey",
            expected=200,
            headers=auth,
            json={"target_email": target, "confirm": True},
        )
        maxed = _call(
            session,
            "POST",
            "/api/admin/tester-tools/set-max",
            expected=200,
            headers=auth,
            json={"target_email": target, "confirm": True},
        )
        assert maxed["active_roster"] == 39
        structures_doc = db.guild_structures.find_one(
            {"guild_id": maxed["guild_id"]},
            {"_id": 0, "structures": 1},
        )
        assert structures_doc
        assert all(
            structures_doc["structures"][slug]["is_unlocked"] is True
            and structures_doc["structures"][slug]["level"]
            == meta["max_level"]
            for slug, meta in STRUCTURE_CATALOG.items()
        )
        expanded = _call(
            session,
            "POST",
            "/api/admin/tester-tools/grant-adventurers",
            expected=200,
            headers=auth,
            json={
                "target_email": target,
                "target_count": 39,
                "confirm": True,
            },
        )
        assert expanded["target_count"] == 39
        assert expanded["total_after"] == 39
        assert expanded["created"] == 0
        _call(
            session,
            "POST",
            "/api/admin/tester-tools/set-max",
            expected=200,
            headers=auth,
            json={"target_email": target, "confirm": True},
        )

        roster = _call(
            session,
            "GET",
            "/api/adventurers",
            expected=200,
            headers=auth,
        )["adventurers"]
        assert len(roster) == 39
        assert all(row["level"] == 80 for row in roster)
        assert all(row["class_selection_required"] is True for row in roster)
        cap = _call(
            session,
            "GET",
            "/api/roster/health",
            expected=200,
            headers=auth,
        )
        assert cap["current"] == 39
        assert cap["cap"] >= 35
        assert cap["is_over_cap"] is False

        choices = _call(
            session,
            "GET",
            "/api/class-halls/assignment/choices",
            expected=200,
            headers=auth,
        )["halls"]
        assert len(choices) == 27
        assert len({row["canonical_class_slug"] for row in choices}) == 27
        assert {
            wave: sum(row["wave"] == wave for row in choices)
            for wave in EXPECTED_WAVE_CLASS_COUNTS
        } == EXPECTED_WAVE_CLASS_COUNTS

        class_roster = roster[:27]
        support_roster = roster[27:]
        assert len(support_roster) == 12
        signature_rewards: dict[str, dict] = {}
        class_by_adventurer: dict[str, dict] = {}
        for adventurer, hall in zip(class_roster, choices, strict=True):
            assignment = _assign_hall(
                session,
                auth,
                adventurer_id=adventurer["id"],
                hall_id=hall["hall_id"],
            )
            assert (
                assignment["adventurer"]["canonical_class_slug"]
                == hall["canonical_class_slug"]
            )
            signature_rewards[adventurer["id"]] = assignment["reward"]
            class_by_adventurer[adventurer["id"]] = hall
        for adventurer in support_roster:
            _assign_hall(
                session,
                auth,
                adventurer_id=adventurer["id"],
                hall_id="hall_guerriero",
            )

        inventory = _call(
            session,
            "GET",
            "/api/inventory",
            expected=200,
            headers=auth,
        )["inventory"]
        inventory_by_item = {row["item_id"]: row for row in inventory}
        for adventurer in class_roster:
            reward = signature_rewards[adventurer["id"]]
            signature = inventory_by_item[reward["item_id"]]["item"]
            slot = signature.get("slot_type") or signature["item_type"]
            _call(
                session,
                "POST",
                f"/api/adventurers/{adventurer['id']}/equip",
                expected=201,
                headers=auth,
                json={"item_id": reward["item_id"], "slot": slot},
            )

        dungeons = _call(
            session,
            "GET",
            "/api/dungeons",
            expected=200,
            headers=auth,
        )["dungeons"]
        training = next(row for row in dungeons if row["slug"] == "training-yard")
        assert training["required_team_size"] == 3
        roster_ids = [row["id"] for row in class_roster]
        support_cohorts = [
            [row["id"] for row in support_roster[:6]],
            [row["id"] for row in support_roster[6:]],
        ]
        assert all(len(cohort) == 6 for cohort in support_cohorts)
        _run_solo_training(
            session,
            auth,
            db,
            dungeon_id=training["id"],
            adventurer_ids=roster_ids,
        )

        first_raid_id = _complete_raid(
            session,
            auth,
            db,
            adventurer_ids=roster_ids[:15],
            raid_slug="broken-bastion-siege",
        )
        _advance_raid_cooldown(db, first_raid_id)
        second_raid_id = _complete_raid(
            session,
            auth,
            db,
            adventurer_ids=roster_ids[7:27],
            raid_slug="necropolis-bells",
        )
        raid_ids = [first_raid_id, second_raid_id]
        assert len(set(raid_ids)) == 2

        changed_builds: dict[str, tuple[str, str]] = {}
        build_items_by_class: dict[str, list[dict]] = {}
        current_slot_by_adventurer: dict[str, str] = {}
        for adventurer in class_roster:
            hall = class_by_adventurer[adventurer["id"]]
            hall_id = hall["hall_id"]
            class_slug = hall["canonical_class_slug"]
            track = _call(
                session,
                "GET",
                (
                    f"/api/class-halls/{hall_id}/item-track"
                    f"?adventurer_id={adventurer['id']}"
                ),
                expected=200,
                headers=auth,
            )
            signature_entry = track["items"][0]
            initial_build = signature_entry["item"]["build_path_id"]
            alternative = next(
                entry
                for entry in track["items"][1:]
                if entry["status"] == "claimable"
                and entry["item"].get("build_path_id")
                and entry["item"]["build_path_id"] != initial_build
            )
            claimed = _call(
                session,
                "POST",
                (
                    f"/api/class-halls/{hall_id}/item-track/"
                    f"{alternative['item']['slug']}/claim"
                ),
                expected=200,
                headers=auth,
                json={"adventurer_id": adventurer["id"]},
            )
            signature_slot = (
                signature_entry["item"].get("slot_type")
                or signature_entry["item"]["item_type"]
            )
            _call(
                session,
                "POST",
                f"/api/adventurers/{adventurer['id']}/unequip",
                expected=200,
                headers=auth,
                json={"slot": signature_slot},
            )
            new_item = alternative["item"]
            new_slot = new_item.get("slot_type") or new_item["item_type"]
            _call(
                session,
                "POST",
                f"/api/adventurers/{adventurer['id']}/equip",
                expected=201,
                headers=auth,
                json={"item_id": claimed["reward"]["item_id"], "slot": new_slot},
            )
            lab = _call(
                session,
                "GET",
                (
                    f"/api/class-halls/{hall_id}/build-lab"
                    f"?adventurer_id={adventurer['id']}"
                ),
                expected=200,
                headers=auth,
            )
            new_build = new_item["build_path_id"]
            assert lab["current_build"]["build_id"] == new_build
            assert next(
                path for path in lab["paths"] if path["build_id"] == new_build
            )["isolated_ready"] is True
            changed_builds[class_slug] = (initial_build, new_build)
            build_items_by_class[class_slug] = [
                signature_entry["item"],
                new_item,
            ]
            current_slot_by_adventurer[adventurer["id"]] = new_slot
            assert initial_build != new_build, hall["wave"]

        _run_solo_training(
            session,
            auth,
            db,
            dungeon_id=training["id"],
            adventurer_ids=roster_ids,
        )
        vertical = _call(
            session,
            "GET",
            f"/api/admin/tester-tools/vertical-slice?target_email={target}",
            expected=200,
            headers=auth,
        )
        assert vertical["completed_journeys"] == 27
        assert vertical["t5_completion_ready"] is False
        assert vertical["t5_gate"]["journeys_ready"] is True
        assert vertical["t5_gate"]["class_build_coverage_ready"] is False
        assert vertical["t5_bottleneck"]["key"] == "all_class_builds"
        assert vertical["coverage"]["minimum_wave_slice_ready"] is True
        assert vertical["telemetry"]["distinct_resonant_builds_observed"] == 54
        assert all(
            row["minimum_slice_ready"] is True
            for row in vertical["coverage"]["waves"]
        )
        journey_by_id = {
            row["adventurer_id"]: row for row in vertical["adventurers"]
        }
        for adventurer in class_roster:
            hall = class_by_adventurer[adventurer["id"]]
            class_slug = hall["canonical_class_slug"]
            journey = journey_by_id[adventurer["id"]]
            assert journey["journey_completed"] is True, hall["wave"]
            evidence = journey["steps"][-1]["evidence"]
            assert (
                evidence["previous_build_id"],
                evidence["new_build_id"],
            ) == changed_builds[class_slug]

        endgame = next(
            row for row in dungeons if row["slug"] == "world-tree-roots-5p"
        )
        assert endgame["required_team_size"] == 7
        assert endgame["min_adventurer_level"] == 70
        power_observations: list[dict] = []

        for adventurer in class_roster:
            hall = class_by_adventurer[adventurer["id"]]
            hall_id = hall["hall_id"]
            class_slug = hall["canonical_class_slug"]
            existing_items = build_items_by_class[class_slug]
            existing_build_ids = {
                item["build_path_id"] for item in existing_items
            }
            track = _call(
                session,
                "GET",
                (
                    f"/api/class-halls/{hall_id}/item-track"
                    f"?adventurer_id={adventurer['id']}"
                ),
                expected=200,
                headers=auth,
            )
            third = next(
                entry
                for entry in track["items"][1:]
                if entry["status"] == "claimable"
                and entry["item"].get("build_path_id")
                and entry["item"]["build_path_id"] not in existing_build_ids
            )
            claimed = _call(
                session,
                "POST",
                (
                    f"/api/class-halls/{hall_id}/item-track/"
                    f"{third['item']['slug']}/claim"
                ),
                expected=200,
                headers=auth,
                json={"adventurer_id": adventurer["id"]},
            )
            assert claimed["reward"]["item_id"] == third["item"]["id"]
            build_items = [*existing_items, third["item"]]
            assert len({item["build_path_id"] for item in build_items}) == 3

            for item in build_items:
                _call(
                    session,
                    "POST",
                    f"/api/adventurers/{adventurer['id']}/unequip",
                    expected=200,
                    headers=auth,
                    json={
                        "slot": current_slot_by_adventurer[
                            adventurer["id"]
                        ]
                    },
                )
                slot = item.get("slot_type") or item["item_type"]
                _call(
                    session,
                    "POST",
                    f"/api/adventurers/{adventurer['id']}/equip",
                    expected=201,
                    headers=auth,
                    json={"item_id": item["id"], "slot": slot},
                )
                current_slot_by_adventurer[adventurer["id"]] = slot
                lab = _call(
                    session,
                    "GET",
                    (
                        f"/api/class-halls/{hall_id}/build-lab"
                        f"?adventurer_id={adventurer['id']}"
                    ),
                    expected=200,
                    headers=auth,
                )
                build_id = item["build_path_id"]
                assert lab["current_build"]["build_id"] == build_id
                assert next(
                    path
                    for path in lab["paths"]
                    if path["build_id"] == build_id
                )["isolated_ready"] is True
                for support_ids in support_cohorts:
                    _run_comparable_samples(
                        session,
                        auth,
                        db,
                        dungeon=endgame,
                        team_ids=[adventurer["id"], *support_ids],
                        sample_count=5,
                        class_slug=class_slug,
                        build_id=build_id,
                        power_observations=power_observations,
                    )

        assert len(power_observations) == 810
        # The 27 classes intentionally keep distinct stat identities. A
        # calibrated ±20% band for seven-member teams preserves them while
        # still catching a stale five-member recommended-power target.
        outside_power_band = [
            row
            for row in power_observations
            if not 0.80 <= row["ratio"] <= 1.20
        ]
        assert not outside_power_band, {
            "minimum": min(row["ratio"] for row in power_observations),
            "maximum": max(row["ratio"] for row in power_observations),
            "outside_count": len(outside_power_band),
            "outside": outside_power_band,
        }

        tuned = _call(
            session,
            "GET",
            f"/api/admin/tester-tools/vertical-slice?target_email={target}",
            expected=200,
            headers=auth,
        )
        assert tuned["t5_completion_ready"] is True
        assert tuned["t5_gate"] == {
            "journeys_ready": True,
            "class_build_coverage_ready": True,
            "sample_coverage_ready": True,
            "controlled_replication_ready": True,
        }
        assert tuned["t5_bottleneck"] is None
        all_builds = tuned["balance"]["builds"]
        assert len(all_builds) == 81
        assert all(row["sample_ready"] is True for row in all_builds)
        assert all(
            row["comparable_samples"] >= 5
            for row in all_builds
        )
        assert tuned["balance"]["sample_ready_build_count"] == 81
        assert tuned["balance"]["total_comparable_samples"] >= 810
        controlled = tuned["balance"]["controlled"]
        assert controlled["comparison_ready"] is True
        assert controlled["ready_class_count"] == 27
        assert controlled["ready_build_count"] == 81
        assert controlled["replication_ready"] is True
        assert controlled["replicated_ready_class_count"] == 27
        assert controlled["replicated_ready_build_count"] == 81
        assert all(
            row["controlled_comparison"]["ready"] is True
            and row["controlled_comparison"]["replicated_ready"] is True
            and row["controlled_comparison"]["cohort_count"] >= 2
            and row["controlled_comparison"]["samples"] >= 10
            for row in all_builds
        )
        review_queue = controlled["review_queue"]
        assert [
            row["severity_score"] for row in review_queue
        ] == sorted(
            (row["severity_score"] for row in review_queue),
            reverse=True,
        )
        assert all(
            row["automatic_change_allowed"] is False
            and row["recommended_scope"] in {
                "item",
                "class_resonance",
                "encounter",
                "mixed",
            }
            and row["manual_action_it"]
            for row in review_queue
        )
        export_bundle = controlled["export_bundle"]
        assert export_bundle["schema_version"] == "t5.manual-tuning.v1"
        assert len(export_bundle["sha256"]) == 64
        assert (
            hashlib.sha256(
                export_bundle["canonical_json"].encode("utf-8")
            ).hexdigest()
            == export_bundle["sha256"]
        )
        assert json.loads(export_bundle["canonical_json"]) == (
            export_bundle["payload"]
        )
        assert export_bundle["payload"]["gate"] == {
            "minimum_samples_per_build_per_cohort": 5,
            "minimum_replicated_cohorts": 2,
            "ready_class_count": 27,
            "expected_class_count": 27,
            "ready_build_count": 81,
            "expected_build_count": 81,
        }
        repeated = _call(
            session,
            "GET",
            f"/api/admin/tester-tools/vertical-slice?target_email={target}",
            expected=200,
            headers=auth,
        )
        assert (
            repeated["balance"]["controlled"]["export_bundle"]
            == export_bundle
        )
        assert tuned["coverage"]["full_class_build_coverage_ready"] is True
        coverage_by_class = {
            row["class_slug"]: row for row in tuned["coverage"]["classes"]
        }
        assert len(coverage_by_class) == 27
        for hall in choices:
            class_slug = hall["canonical_class_slug"]
            row = coverage_by_class[class_slug]
            assert row["observed_build_count"] == 3, hall["wave"]
            assert row["ready_for_tuning"] is True, hall["wave"]
        assert all(
            row["full_coverage_ready"] is True
            for row in tuned["coverage"]["waves"]
        )
    finally:
        client.close()
