"""FASE 9P — serializer: timer autoritativo della stanza corrente.

Il FE non inventa un orologio: `expedition_public` espone
room_started_at / room_completes_at / room_duration_seconds (durata
EFFETTIVA, riposo incluso) + seconds_remaining SOLO quando il gruppo è
davvero dentro una stanza.
"""
from datetime import datetime, timedelta, timezone

from app.expeditions.services import expedition_public


def _rooms_doc(**overrides) -> dict:
    now = datetime.now(timezone.utc)
    doc = {
        "id": "exp-1",
        "guild_id": "guild-1",
        "dungeon_id": "d-1",
        "status": "in_progress",
        "mode": "rooms",
        "room_state": "in_room",
        "current_room_idx": 1,
        "room_started_at": (now - timedelta(seconds=100)).isoformat(),
        "room_duration_seconds": 600,
        "completes_at": (now + timedelta(seconds=500)).isoformat(),
        "rooms_snapshot": [
            {"idx": 0, "name_it": "Ingresso", "duration_seconds": 300},
            {"idx": 1, "name_it": "Sala delle Guardie",
             "duration_seconds": 600},
        ],
        "created_at": now.isoformat(),
    }
    doc.update(overrides)
    return doc


def test_stanza_attiva_espone_il_timer_autoritativo():
    out = expedition_public(_rooms_doc())
    assert out["room_duration_seconds"] == 600
    assert out["room_completes_at"] == out["completes_at"]
    assert out["room_started_at"]
    # seconds_remaining coerente e MAI negativo.
    assert 0 <= out["seconds_remaining"] <= 600
    assert abs(out["seconds_remaining"] - 500) <= 2


def test_fallback_doc_legacy_senza_campi_9p():
    """Doc pre-9P: durata dalla stanza corrente dello snapshot e inizio
    derivato da completes_at - durata."""
    doc = _rooms_doc()
    doc.pop("room_started_at")
    doc.pop("room_duration_seconds")
    out = expedition_public(doc)
    assert out["room_duration_seconds"] == 600  # idx corrente = 1
    started = datetime.fromisoformat(out["room_started_at"])
    completes = datetime.fromisoformat(out["room_completes_at"])
    assert (completes - started).total_seconds() == 600


def test_niente_timer_in_attesa_di_scelta():
    out = expedition_public(_rooms_doc(room_state="awaiting_choice"))
    assert "room_duration_seconds" not in out
    assert "room_completes_at" not in out


def test_niente_timer_a_run_conclusa():
    out = expedition_public(_rooms_doc(status="completed"))
    assert "room_duration_seconds" not in out
    assert "seconds_remaining" not in out


def test_niente_timer_sul_legacy_single():
    now = datetime.now(timezone.utc)
    out = expedition_public({
        "id": "exp-2", "guild_id": "g", "dungeon_id": "d",
        "status": "in_progress", "mode": "single",
        "completes_at": (now + timedelta(seconds=60)).isoformat(),
        "created_at": now.isoformat(),
    })
    assert "room_duration_seconds" not in out
    assert out["seconds_remaining"] >= 0  # il timer run legacy resta


def test_remaining_mai_negativo_su_stanza_scaduta():
    now = datetime.now(timezone.utc)
    out = expedition_public(_rooms_doc(
        completes_at=(now - timedelta(seconds=30)).isoformat(),
    ))
    assert out["seconds_remaining"] == 0
    assert out["room_duration_seconds"] == 600
