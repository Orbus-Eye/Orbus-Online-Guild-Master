"""FASE 10G-N — Dungeon automatici + Riposo limitato.

Regole del mandato coperte qui:
  * AUTO solo per dungeon a stanze GIÀ completati manualmente;
  * durata percorso ×1.20 (5m+8m+7m = 20m → 24m);
  * route replay: stessa sequenza del clear manuale, MAI branch nuovi;
  * nessun click: la stanza successiva parte da sola (niente
    awaiting_choice), nessun rest bonus in AUTO;
  * RIPOSA E PROCEDI una sola volta per INTERO dungeon;
  * le run AUTO non sbloccano dungeon nuovi (gate);
  * PROCEDI resta sempre disponibile (10M).
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.dungeons.rooms import (
    AUTO_DURATION_FACTOR,
    auto_route_duration_seconds,
    build_auto_route_snapshot,
)
from app.expeditions.rooms_engine import (
    _resolve_current_room,
    _start_next_room,
    advance_rooms_action,
)
from app.expeditions.schemas import ExpeditionCreateIn
from app.expeditions.services import expedition_public


def _room(idx: int, *, duration: int, chance: int = 70, kind: str = "guard",
          has_loot: bool = False) -> dict:
    return {
        "type": "room", "idx": idx, "slug": f"stanza-{idx}",
        "name_it": f"Stanza {idx}", "kind": kind, "narrative_it": "",
        "has_loot": has_loot, "duration_seconds": duration,
        "gold": 10, "xp": 8, "chance": chance,
    }


# ── 10H: durata ×1.20 e route replay puro ────────────────────────────────

def test_durata_automatica_e_del_20_percento_piu_lunga() -> None:
    # Esempio ESATTO del mandato: 5m + 8m + 7m = 20m → 24m.
    route = [
        _room(0, duration=300), _room(1, duration=480), _room(2, duration=420),
    ]
    assert AUTO_DURATION_FACTOR == 1.20
    assert auto_route_duration_seconds(route) == 1440  # 24 minuti

    snap = build_auto_route_snapshot(
        route, stored_base_chance=70, base_chance=70,
    )
    assert [r["duration_seconds"] for r in snap] == [360, 576, 504]
    assert sum(r["duration_seconds"] for r in snap) == 1440


def test_route_replay_ricalcola_le_chance_e_scarta_i_fork() -> None:
    stored = [
        _room(0, duration=100, chance=75),        # modifier +5
        {"type": "fork", "idx": 1, "fork_id": "f", "options": []},
        _room(2, duration=200, chance=60, kind="boss"),  # modifier -10
    ]
    snap = build_auto_route_snapshot(
        stored, stored_base_chance=70, base_chance=50,
    )
    # Il fork non risolto NON viene replayato (mai branch nuovi).
    assert [r["slug"] for r in snap] == ["stanza-0", "stanza-2"]
    assert [r["idx"] for r in snap] == [0, 1]  # reindicizzato
    # Chance = nuova base + modificatore congelato del clear manuale.
    assert snap[0]["chance"] == 55   # 50 + (75-70)
    assert snap[1]["chance"] == 40   # 50 + (60-70)


def test_schema_dispatch_ha_flag_auto_default_false() -> None:
    payload = ExpeditionCreateIn(
        dungeon_id="d" * 12, adventurer_ids=["a1", "a2", "a3"],
    )
    assert payload.auto is False


# ── 10G: gate first-clear manuale ────────────────────────────────────────

def test_auto_richiede_il_first_clear_manuale() -> None:
    from app.expeditions.services import _dispatch_expedition

    async def go() -> None:
        db = SimpleNamespace(dungeons=AsyncMock())
        db.dungeons.find_one.return_value = {
            "id": "d-1", "slug": "goblin-warrens", "name": "Goblin Warrens",
            "is_active": True, "difficulty": 1, "required_team_size": 3,
            "base_duration_seconds": 60, "recommended_power": 45,
            "base_gold_reward": 35, "base_xp_reward": 25,
        }
        with patch(
            "app.expeditions.services._evaluate_dungeon_gate",
            new=AsyncMock(return_value=(True, None)),
        ):
            with pytest.raises(HTTPException) as exc:
                await _dispatch_expedition(
                    db,
                    guild={"id": "g-1"},  # nessun manual_dungeon_clears
                    dungeon_id="d-1",
                    adventurer_ids=["a1", "a2", "a3"],
                    auto_mode=True,
                )
        assert exc.value.status_code == 409
        assert exc.value.detail["code"] == "auto.manual_first_clear_required"

    asyncio.run(go())


def test_gate_sblocchi_ignora_le_run_automatiche() -> None:
    from app.dungeons.gates import evaluate_data_driven_gate

    async def go() -> None:
        db = SimpleNamespace(
            adventurers=AsyncMock(), expeditions=AsyncMock(),
        )
        db.expeditions.count_documents.return_value = 0
        unlocked, _reason = await evaluate_data_driven_gate(
            db,
            {"gate": {"min_total_expeditions_completed": 3}},
            {"id": "g-1"},
        )
        assert unlocked is False
        flt = db.expeditions.count_documents.await_args.args[0]
        assert flt["auto_mode"] == {"$ne": True}  # AUTO non sblocca nulla

    asyncio.run(go())


# ── 10H: nessun click — la stanza successiva parte da sola ───────────────

def test_auto_salta_awaiting_choice_e_non_da_rest_bonus() -> None:
    async def go() -> None:
        exp = {
            "id": "exp-1", "guild_id": "g-1", "dungeon_id": "d-1",
            "status": "in_progress", "mode": "rooms", "auto_mode": True,
            "room_state": "in_room", "current_room_idx": 0,
            "rest_bonus_next": 0,
            "rooms_snapshot": [
                _room(0, duration=120, chance=100),
                _room(1, duration=240, chance=100),
                _room(2, duration=120, chance=100),
            ],
        }
        db = SimpleNamespace(expeditions=AsyncMock(), dungeons=AsyncMock())
        fake_rng = SimpleNamespace(randint=lambda a, b: 1,
                                   random=lambda: 0.99,
                                   choice=lambda seq: seq[0])
        with patch("app.expeditions.rooms_engine._rng", fake_rng):
            await _resolve_current_room(db, exp)
        update_filter, update = db.expeditions.update_one.await_args.args
        assert update_filter["current_room_idx"] == 0
        assert update["$set"]["current_room_idx"] == 1
        assert update["$set"]["room_state"] == "in_room"  # MAI attesa click
        assert update["$set"]["rest_bonus_next"] == 0     # 10N: no riposo
        assert update["$set"]["room_duration_seconds"] == 240

    asyncio.run(go())


def test_azioni_manuali_vietate_sulla_run_automatica() -> None:
    async def go() -> None:
        db = SimpleNamespace(expeditions=AsyncMock())
        db.expeditions.find_one.return_value = {
            "id": "exp-1", "guild_id": "g-1", "status": "in_progress",
            "mode": "rooms", "auto_mode": True,
            "room_state": "awaiting_choice",
        }
        with pytest.raises(HTTPException) as exc:
            await advance_rooms_action(
                db, {"id": "g-1"}, "exp-1", "continue",
            )
        assert exc.value.status_code == 409
        assert exc.value.detail["code"] == "rooms.auto_mode"

    asyncio.run(go())


# ── 10M: riposo una sola volta per dungeon ───────────────────────────────

def test_secondo_riposo_impossibile_ma_procedi_sempre_disponibile() -> None:
    async def go() -> None:
        db = SimpleNamespace(expeditions=AsyncMock())
        exp = {
            "id": "exp-1", "guild_id": "g-1", "dungeon_id": "d-1",
            "status": "in_progress",
            "mode": "rooms", "auto_mode": False,
            "room_state": "awaiting_choice", "current_room_idx": 0,
            "created_at": "2026-08-15T00:00:00+00:00",
            "rest_used": True,  # riposo già consumato
            "rooms_snapshot": [
                _room(0, duration=100), _room(1, duration=100),
            ],
        }
        db.expeditions.find_one.return_value = exp
        # Secondo RIPOSA E PROCEDI → 409 dedicato.
        with pytest.raises(HTTPException) as exc:
            await advance_rooms_action(
                db, {"id": "g-1"}, "exp-1", "rest_and_continue",
            )
        assert exc.value.detail["code"] == "rooms.rest_already_used"

        # PROCEDI resta sempre disponibile.
        db.expeditions.update_one.return_value = SimpleNamespace(
            modified_count=1,
        )
        out = await advance_rooms_action(
            db, {"id": "g-1"}, "exp-1", "continue",
        )
        assert "expedition" in out

    asyncio.run(go())


def test_cas_del_riposo_blocca_anche_le_race() -> None:
    async def go() -> None:
        db = SimpleNamespace(expeditions=AsyncMock())
        db.expeditions.update_one.return_value = SimpleNamespace(
            modified_count=1,
        )
        exp = {
            "id": "exp-1", "guild_id": "g-1", "status": "in_progress",
            "mode": "rooms", "room_state": "awaiting_choice",
            "current_room_idx": 0,
            "rooms_snapshot": [
                _room(0, duration=100), _room(1, duration=100),
            ],
        }
        with patch("app.audit.log.write_audit", new=AsyncMock()):
            applied = await _start_next_room(db, exp, rest=True, auto=False)
        assert applied is True
        cas_filter, update = db.expeditions.update_one.await_args.args
        assert cas_filter["rest_used"] == {"$ne": True}   # backstop race
        assert update["$set"]["rest_used"] is True
        assert update["$set"]["rest_bonus_next"] > 0      # bonus canonico
        # Durata stanza successiva allungata dal riposo (+25%).
        assert update["$set"]["room_duration_seconds"] == 125

    asyncio.run(go())


# ── Serializer ───────────────────────────────────────────────────────────

def test_serializer_espone_auto_e_rest_used() -> None:
    base = {
        "id": "e-1", "guild_id": "g-1", "dungeon_id": "d-1",
        "status": "in_progress", "mode": "rooms",
        "created_at": "2026-08-15T00:00:00+00:00",
    }
    out = expedition_public(dict(base))
    assert out["auto_mode"] is False           # legacy default
    assert out["rest_used"] is False
    assert out["auto_total_duration_seconds"] is None

    out = expedition_public(dict(
        base, auto_mode=True, rest_used=True,
        auto_total_duration_seconds=1440,
    ))
    assert out["auto_mode"] is True
    assert out["rest_used"] is True
    assert out["auto_total_duration_seconds"] == 1440
