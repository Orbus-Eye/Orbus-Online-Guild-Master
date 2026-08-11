"""FASE 9C — vertical slice tester SENZA build.

Il viaggio è: Hall → item-firma → dungeon con risonanza di CLASSE →
raid → ricompensa registrata. Cinque gradini, nessuna build.
"""
from app.admin.tester_journey import (
    VERTICAL_SLICE_STEPS,
    compile_tester_vertical_slice,
)


def _mechanic(resonant: bool = True) -> dict:
    return {"resonance_active": resonant, "item_resonance_bonus": 2 if resonant else 0}


def _legacy_mechanic() -> dict:
    # Snapshot storico pre-FASE 9 (formato build-era): deve essere
    # ancora riconosciuto come risonanza attiva.
    return {"active_build": {"build_id": "bastione", "resonance_active": True}}


def _payload(
    *,
    resonant: bool = True,
    raid_before_dungeon: bool = False,
    legacy_snapshot: bool = False,
    reward_applied: bool = True,
) -> dict:
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
    mechanic = _legacy_mechanic() if legacy_snapshot else _mechanic(resonant)
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
        "expeditions": [
            {
                "id": "exp-1",
                "status": "completed",
                "completed_at": "2026-01-01T10:00:00+00:00",
                "result_summary": "Success",
            },
        ],
        "expedition_members": [
            {
                "expedition_id": "exp-1",
                "adventurer_id": "adv-1",
                "equipment_snapshot": [{"item_id": "item-signature"}],
                "class_mechanic_snapshot": mechanic,
            },
        ],
        "raids": [
            {
                "id": "raid-1",
                "status": "completed",
                "completed_at": (
                    "2026-01-01T09:00:00+00:00"
                    if raid_before_dungeon
                    else "2026-01-01T11:00:00+00:00"
                ),
                "outcome": "victory",
            }
        ],
        "raid_participants": [
            {
                "raid_id": "raid-1",
                "adventurer_id": "adv-1",
                "class_mechanic_snapshot": mechanic,
                "outcome": "survived",
            }
        ],
        "raid_reward_grants": (
            [{"raid_id": "raid-1", "status": "applied"}]
            if reward_applied else []
        ),
    }


def test_slice_ha_cinque_gradini_senza_build():
    keys = [key for key, _ in VERTICAL_SLICE_STEPS]
    assert keys == [
        "class_hall_chosen",
        "signature_item_equipped",
        "resonant_dungeon_completed",
        "raid_completed",
        "raid_reward_tracked",
    ]
    assert "new_build_activated" not in keys


def test_viaggio_completo_chiude_il_gate_t5():
    result = compile_tester_vertical_slice(**_payload())
    assert result["completed_journeys"] == 1
    assert result["ready_for_playtest"] is True
    assert result["t5_completion_ready"] is True
    row = result["adventurers"][0]
    assert row["journey_completed"] is True
    assert row["class_role"] == "DPS"  # guerriero: ruolo fisso dal registry
    assert all(step["completed"] for step in row["steps"])


def test_senza_risonanza_il_dungeon_non_conta():
    result = compile_tester_vertical_slice(**_payload(resonant=False))
    row = result["adventurers"][0]
    by_key = {step["key"]: step["completed"] for step in row["steps"]}
    assert by_key["class_hall_chosen"] is True
    assert by_key["signature_item_equipped"] is True
    assert by_key["resonant_dungeon_completed"] is False
    assert row["journey_completed"] is False
    assert result["t5_completion_ready"] is False
    assert result["bottleneck"]["key"] == "resonant_dungeon_completed"


def test_raid_prima_del_dungeon_non_conta():
    result = compile_tester_vertical_slice(**_payload(raid_before_dungeon=True))
    row = result["adventurers"][0]
    by_key = {step["key"]: step["completed"] for step in row["steps"]}
    assert by_key["resonant_dungeon_completed"] is True
    assert by_key["raid_completed"] is False
    assert result["completed_journeys"] == 0


def test_ricompensa_non_applicata_blocca_l_ultimo_gradino():
    result = compile_tester_vertical_slice(**_payload(reward_applied=False))
    row = result["adventurers"][0]
    by_key = {step["key"]: step["completed"] for step in row["steps"]}
    assert by_key["raid_completed"] is True
    assert by_key["raid_reward_tracked"] is False
    assert result["completed_journeys"] == 0


def test_snapshot_legacy_build_era_ancora_riconosciuto():
    result = compile_tester_vertical_slice(**_payload(legacy_snapshot=True))
    assert result["completed_journeys"] == 1


def test_senza_gilda_il_gate_resta_chiuso():
    result = compile_tester_vertical_slice(
        user={"id": "user-1", "email": "tester@orbus.test"},
        guild=None,
        adventurers=[], signature_items=[], equipped_items=[],
        expeditions=[], expedition_members=[], raids=[],
        raid_participants=[], raid_reward_grants=[],
    )
    assert result["t5_completion_ready"] is False
    assert result["bottleneck"]["key"] == "tester_guild"
