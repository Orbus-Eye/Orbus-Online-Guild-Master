import hashlib
import json

from app.admin.tester_journey import compile_tester_vertical_slice


def _mechanic(build_id: str) -> dict:
    return {
        "active_build": {
            "build_id": build_id,
            "resonance_active": True,
        }
    }


def _payload(*, second_build_after_raid: bool = True) -> dict:
    adventurer = {
        "id": "adv-1",
        "name": "Alda",
        "level": 80,
        "class_hall_id": "hall_guerriero",
        "canonical_class_slug": "guerriero",
        "class_slug": "guerriero",
        "adventurer_class_id": "class-1",
        "recruit_status": "class_assigned",
    }
    expeditions = [
        {
            "id": "exp-1",
            "status": "completed",
            "completed_at": "2026-01-01T10:00:00+00:00",
            "result_summary": "Success",
            "team_power": 100,
            "recommended_power": 100,
        },
        {
            "id": "exp-2",
            "status": "completed",
            "completed_at": (
                "2026-01-01T12:00:00+00:00"
                if second_build_after_raid
                else "2026-01-01T10:30:00+00:00"
            ),
            "result_summary": "Failed",
            "team_power": 100,
            "recommended_power": 100,
        },
    ]
    return {
        "user": {"id": "user-1", "email": "tester@orbus.test"},
        "guild": {"id": "guild-1"},
        "adventurers": [adventurer],
        "signature_items": [
            {
                "id": "item-signature",
                "name": "Firma",
                "source": "class_hall:hall_guerriero",
                "acquisition_track_order": 0,
            }
        ],
        "equipped_items": [
            {"adventurer_id": "adv-1", "item_id": "item-signature"}
        ],
        "expeditions": expeditions,
        "expedition_members": [
            {
                "expedition_id": "exp-1",
                "adventurer_id": "adv-1",
                "equipment_snapshot": [{"item_id": "item-signature"}],
                "class_mechanic_snapshot": _mechanic("bastione"),
                "total_power_snapshot": 30,
                "equipment_power_snapshot": 6,
                "item_effect_power_bonus": 2,
                "class_item_resonance_bonus": 2,
            },
            {
                "expedition_id": "exp-2",
                "adventurer_id": "adv-1",
                "equipment_snapshot": [{"item_id": "item-path-2"}],
                "class_mechanic_snapshot": _mechanic("condottiero"),
                "total_power_snapshot": 34,
                "equipment_power_snapshot": 8,
                "item_effect_power_bonus": 2,
                "class_item_resonance_bonus": 2,
            },
        ],
        "raids": [
            {
                "id": "raid-1",
                "status": "completed",
                "completed_at": "2026-01-01T11:00:00+00:00",
                "outcome": "victory",
                "team_power_combined": 1000,
                "recommended_power_combined": 1000,
            }
        ],
        "raid_participants": [
            {
                "raid_id": "raid-1",
                "adventurer_id": "adv-1",
                "class_mechanic_snapshot": _mechanic("bastione"),
                "outcome": "survived",
                "total_power_snapshot": 36,
                "equipment_power_snapshot": 7,
            }
        ],
        "raid_reward_grants": [
            {"raid_id": "raid-1", "status": "applied"}
        ],
    }


def test_vertical_slice_requires_and_recognizes_a_new_post_raid_build():
    result = compile_tester_vertical_slice(**_payload())

    assert result["ready_for_playtest"] is True
    assert result["t5_completion_ready"] is False
    assert result["t5_gate"] == {
        "journeys_ready": False,
        "class_build_coverage_ready": False,
        "sample_coverage_ready": False,
        "controlled_replication_ready": False,
    }
    assert result["t5_bottleneck"]["key"] == "all_class_journeys"
    assert result["completed_journeys"] == 1
    assert result["bottleneck"] is None
    row = result["adventurers"][0]
    assert row["completed_steps"] == 6
    assert row["steps"][-1]["evidence"]["previous_build_id"] == "bastione"
    assert row["steps"][-1]["evidence"]["new_build_id"] == "condottiero"
    coverage = result["coverage"]
    assert coverage["class_count"] == 27
    assert coverage["expected_build_count"] == 81
    assert [
        (
            wave["wave"],
            wave["class_count"],
            wave["expected_build_count"],
        )
        for wave in coverage["waves"]
    ] == [
        ("A", 5, 15),
        ("B", 7, 21),
        ("C", 6, 18),
        ("D", 6, 18),
        ("E", 3, 9),
    ]
    warrior = next(
        row
        for row in coverage["classes"]
        if row["class_slug"] == "guerriero"
    )
    assert warrior["observed_build_count"] == 2
    assert warrior["completed_journeys"] == 1
    assert warrior["ready_for_tuning"] is False
    assert coverage["minimum_wave_slice_ready"] is False
    assert coverage["full_class_build_coverage_ready"] is False
    balance = result["balance"]
    assert balance["minimum_samples_per_build"] == 5
    assert balance["expected_build_count"] == 81
    assert balance["sample_ready_build_count"] == 0
    assert balance["total_activity_samples"] == 3
    assert balance["total_comparable_samples"] == 3
    bastione = next(
        row
        for row in balance["builds"]
        if row["class_slug"] == "guerriero"
        and row["build_id"] == "bastione"
    )
    assert bastione["samples"] == 2
    assert bastione["comparable_samples"] == 2
    assert bastione["power_context"]["matched"] == 2
    assert bastione["dungeon"]["success_rate"] == 1.0
    assert bastione["raid"]["survival_rate"] == 1.0
    assert bastione["power"]["average_total"] == 33.0


def test_vertical_slice_does_not_count_a_build_used_before_the_reward():
    result = compile_tester_vertical_slice(
        **_payload(second_build_after_raid=False)
    )

    assert result["ready_for_playtest"] is False
    assert result["completed_journeys"] == 0
    assert result["bottleneck"]["key"] == "new_build_activated"
    assert result["adventurers"][0]["completed_steps"] == 5


def test_vertical_slice_orders_mixed_timezone_offsets_chronologically():
    payload = _payload()
    payload["expeditions"][0]["completed_at"] = (
        "2026-01-01T07:30:00+00:00"
    )
    payload["raids"][0]["completed_at"] = "2026-01-01T10:00:00+02:00"
    payload["expeditions"][1]["completed_at"] = (
        "2026-01-01T10:30:00+03:00"
    )

    result = compile_tester_vertical_slice(**payload)

    assert result["ready_for_playtest"] is False
    assert result["completed_journeys"] == 0
    assert result["bottleneck"]["key"] == "new_build_activated"
    assert result["adventurers"][0]["completed_steps"] == 5


def test_vertical_slice_rejects_noncanonical_build_ids():
    payload = _payload()
    for member in payload["expedition_members"]:
        member["class_mechanic_snapshot"] = _mechanic("build-inventata")
    payload["raid_participants"][0][
        "class_mechanic_snapshot"
    ] = _mechanic("build-inventata")

    result = compile_tester_vertical_slice(**payload)

    assert result["ready_for_playtest"] is False
    assert result["bottleneck"]["key"] == "resonant_dungeon_completed"
    assert result["adventurers"][0]["completed_steps"] == 2
    warrior = next(
        row
        for row in result["coverage"]["classes"]
        if row["class_slug"] == "guerriero"
    )
    assert warrior["observed_build_count"] == 0


def test_balance_telemetry_flags_extreme_rates_only_after_minimum_sample():
    payload = _payload()
    payload["raids"] = []
    payload["raid_participants"] = []
    payload["raid_reward_grants"] = []
    payload["expeditions"] = []
    payload["expedition_members"] = []
    for index in range(5):
        expedition_id = f"exp-fail-{index}"
        payload["expeditions"].append(
            {
                "id": expedition_id,
                "status": "completed",
                "completed_at": f"2026-01-02T1{index}:00:00+00:00",
                "result_summary": "Failed",
                "team_power": 100,
                "recommended_power": 100,
            }
        )
        payload["expedition_members"].append(
            {
                "expedition_id": expedition_id,
                "adventurer_id": "adv-1",
                "equipment_snapshot": [{"item_id": "item-signature"}],
                "class_mechanic_snapshot": _mechanic("bastione"),
                "total_power_snapshot": 30,
                "equipment_power_snapshot": 6,
                "item_effect_power_bonus": 2,
                "class_item_resonance_bonus": 2,
            }
        )

    result = compile_tester_vertical_slice(**payload)
    bastione = next(
        row
        for row in result["balance"]["builds"]
        if row["class_slug"] == "guerriero"
        and row["build_id"] == "bastione"
    )

    assert bastione["sample_ready"] is True
    assert bastione["status"] == "review_signal"
    assert bastione["dungeon"]["success_rate"] == 0.0
    assert bastione["review_signals"] == ["low_dungeon_success"]
    assert result["balance"]["sample_ready_build_count"] == 1
    assert result["balance"]["review_signal_count"] == 1


def test_underpowered_results_do_not_trigger_balance_signals():
    payload = _payload()
    payload["raids"] = []
    payload["raid_participants"] = []
    payload["raid_reward_grants"] = []
    payload["expeditions"] = []
    payload["expedition_members"] = []
    for index in range(5):
        expedition_id = f"exp-underpowered-{index}"
        payload["expeditions"].append(
            {
                "id": expedition_id,
                "status": "completed",
                "completed_at": f"2026-01-03T1{index}:00:00+00:00",
                "result_summary": "Failed",
                "team_power": 50,
                "recommended_power": 100,
            }
        )
        payload["expedition_members"].append(
            {
                "expedition_id": expedition_id,
                "adventurer_id": "adv-1",
                "equipment_snapshot": [{"item_id": "item-signature"}],
                "class_mechanic_snapshot": _mechanic("bastione"),
                "total_power_snapshot": 20,
                "equipment_power_snapshot": 4,
                "item_effect_power_bonus": 2,
                "class_item_resonance_bonus": 2,
            }
        )

    result = compile_tester_vertical_slice(**payload)
    bastione = next(
        row
        for row in result["balance"]["builds"]
        if row["class_slug"] == "guerriero"
        and row["build_id"] == "bastione"
    )

    assert bastione["samples"] == 5
    assert bastione["comparable_samples"] == 0
    assert bastione["power_context"]["underpowered"] == 5
    assert bastione["sample_ready"] is False
    assert bastione["dungeon"]["success_rate"] is None
    assert bastione["review_signals"] == []


def _controlled_payload(*cohorts: tuple[str, str, str]) -> dict:
    payload = _payload()
    payload["raids"] = []
    payload["raid_participants"] = []
    payload["raid_reward_grants"] = []
    payload["expeditions"] = []
    payload["expedition_members"] = []
    build_samples = (
        ("bastione", 30, 6, 2, 2, 0),
        ("condottiero", 34, 7, 3, 2, 3),
        ("assaltatore", 42, 8, 9, 3, 5),
    )
    for cohort, support_id, dungeon_id in cohorts:
        for (
            build_id,
            total,
            equipment,
            item_effect,
            resonance,
            successes,
        ) in build_samples:
            for index in range(5):
                expedition_id = (
                    f"controlled-{cohort}-{build_id}-{index}"
                )
                payload["expeditions"].append(
                    {
                        "id": expedition_id,
                        "dungeon_id": dungeon_id,
                        "status": "completed",
                        "completed_at": (
                            f"2026-01-04T1{index}:00:00+00:00"
                        ),
                        "result_summary": (
                            "Success" if index < successes else "Failed"
                        ),
                        "team_power": 100,
                        "recommended_power": 100,
                    }
                )
                payload["expedition_members"].extend(
                    [
                        {
                            "expedition_id": expedition_id,
                            "adventurer_id": "adv-1",
                            "equipment_snapshot": [
                                {"item_id": f"item-{build_id}"}
                            ],
                            "class_mechanic_snapshot": _mechanic(build_id),
                            "total_power_snapshot": total,
                            "equipment_power_snapshot": equipment,
                            "item_effect_power_bonus": item_effect,
                            "class_item_resonance_bonus": resonance,
                        },
                        {
                            "expedition_id": expedition_id,
                            "adventurer_id": support_id,
                            "equipment_snapshot": [],
                            "class_mechanic_snapshot": {},
                            "total_power_snapshot": 20,
                            "equipment_power_snapshot": 0,
                            "item_effect_power_bonus": 0,
                            "class_item_resonance_bonus": 0,
                        },
                    ]
                )
    return payload


def test_controlled_comparison_separates_build_components_in_same_cohort():
    payload = _controlled_payload(
        ("alpha", "support-alpha", "controlled-dungeon"),
        ("beta", "support-beta", "controlled-dungeon"),
    )

    result = compile_tester_vertical_slice(**payload)
    controlled = result["balance"]["controlled"]
    assert controlled["ready_class_count"] == 1
    assert controlled["ready_build_count"] == 3
    assert controlled["replicated_ready_class_count"] == 1
    assert controlled["replicated_ready_build_count"] == 3
    assert controlled["replication_ready"] is False
    warrior = next(
        row
        for row in controlled["classes"]
        if row["class_slug"] == "guerriero"
    )
    assert warrior["ready"] is True
    assert warrior["controlled_cohort_count"] == 2
    assert warrior["controlled_independent_team_count"] == 2
    assert warrior["controlled_samples"] == 30
    assert warrior["replicated_ready"] is True
    assert warrior["decision"] == "inspect_components"
    assert set(warrior["review_reasons"]) == {
        "controlled_total_power_spread",
        "controlled_equipment_spread",
        "controlled_item_effect_spread",
        "controlled_class_resonance_spread",
        "controlled_dungeon_outcome_spread",
    }
    assert warrior["severity_score"] > 0
    assert warrior["severity"] in {"medium", "high", "critical"}
    assert warrior["recommended_scope"] == "mixed"
    assert warrior["automatic_change_allowed"] is False
    assert warrior["manual_action_it"]
    assert "due coorti indipendenti" in warrior["manual_action_it"]
    assert controlled["review_queue"][0]["class_slug"] == "guerriero"
    assailant = next(
        row
        for row in result["balance"]["builds"]
        if row["class_slug"] == "guerriero"
        and row["build_id"] == "assaltatore"
    )
    comparison = assailant["controlled_comparison"]
    assert comparison["ready"] is True
    assert comparison["samples"] == 10
    assert comparison["cohort_count"] == 2
    assert comparison["independent_team_count"] == 2
    assert comparison["replicated_ready"] is True
    assert comparison["encounters"] == ["controlled-dungeon"]
    assert comparison["average_team_power_ratio"] == 1.0
    assert comparison["power"]["average_item_effect"] == 9.0
    assert warrior["controlled_spreads"]["item_effect"]["ratio"] == 1.499
    assert (
        warrior["controlled_spreads"]["class_resonance"]["ratio"]
        == 0.429
    )
    assert (
        comparison["delta_from_class_average"]["average_total"]["value"]
        > 0
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
    repeated = compile_tester_vertical_slice(**payload)
    assert (
        repeated["balance"]["controlled"]["export_bundle"]
        == export_bundle
    )


def test_replication_requires_distinct_teams_and_holds_preliminary_signals():
    payload = _controlled_payload(
        ("alpha", "support-shared", "controlled-dungeon-a"),
        ("beta", "support-shared", "controlled-dungeon-b"),
    )

    result = compile_tester_vertical_slice(**payload)
    controlled = result["balance"]["controlled"]
    warrior = next(
        row
        for row in controlled["classes"]
        if row["class_slug"] == "guerriero"
    )

    assert warrior["ready"] is True
    assert warrior["controlled_cohort_count"] == 2
    assert warrior["controlled_independent_team_count"] == 1
    assert warrior["replicated_ready"] is False
    assert warrior["review_required"] is False
    assert warrior["preliminary_review_detected"] is True
    assert warrior["decision"] == "collect_replication"
    assert warrior["review_reasons"] == []
    assert warrior["preliminary_review_reasons"]
    assert all(
        row["class_slug"] != "guerriero"
        for row in controlled["review_queue"]
    )
    assert any(
        row["class_slug"] == "guerriero"
        for row in controlled["preliminary_review_queue"]
    )

    export_payload = controlled["export_bundle"]["payload"]
    assert all(
        row["class_slug"] != "guerriero"
        for row in export_payload["proposals"]
    )
    warrior_hold = next(
        row
        for row in export_payload["holds"]
        if row["class_slug"] == "guerriero"
    )
    assert warrior_hold["decision"] == "collect_replication"
    assert warrior_hold["preliminary_review_reasons"]
