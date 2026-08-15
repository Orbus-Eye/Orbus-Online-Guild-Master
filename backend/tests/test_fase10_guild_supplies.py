"""FASE 10C-F — Beni di Gilda: cap 120, refill giornaliero, mercato,
reward. Test puri (db mockato), zero rete."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.guild_supplies import (
    AUTO_DUNGEON_COST,
    DAILY_REFILL_VALUE,
    DUNGEON_MANUAL_REWARD,
    GUILD_SUPPLIES_CAP,
    MARKET_PACK_GOLD_COST,
    MARKET_PACK_SUPPLIES,
    MISSION_REWARD,
    RAID_REWARD,
    _today,
    effective_supplies,
    ensure_daily_refill,
    grant_supplies,
    purchase_market_pack,
    spend_supplies,
)


def test_costanti_del_mandato() -> None:
    assert GUILD_SUPPLIES_CAP == 120
    assert DAILY_REFILL_VALUE == 120
    assert MARKET_PACK_SUPPLIES == 100
    assert MARKET_PACK_GOLD_COST == 2000
    assert DUNGEON_MANUAL_REWARD == 5
    assert RAID_REWARD == 50
    assert MISSION_REWARD == 10
    assert AUTO_DUNGEON_COST == 15


def test_effective_supplies_fallback_e_refill() -> None:
    today = _today()
    # Gilda esistente senza campo → fallback 120.
    assert effective_supplies({"id": "g"}) == 120
    assert effective_supplies(None) == 120
    # Refill di ieri → oggi il saldo effettivo è 120 (refill pendente).
    assert effective_supplies(
        {"guild_supplies": 30, "guild_supplies_last_refill": "2026-08-14"},
        today,
    ) == 120
    # Refill di oggi → saldo reale.
    assert effective_supplies(
        {"guild_supplies": 30, "guild_supplies_last_refill": today}, today,
    ) == 30
    # Clamp difensivo.
    assert effective_supplies(
        {"guild_supplies": 999, "guild_supplies_last_refill": today}, today,
    ) == 120
    assert effective_supplies(
        {"guild_supplies": -5, "guild_supplies_last_refill": today}, today,
    ) == 0


def _db(**collections) -> SimpleNamespace:
    return SimpleNamespace(**collections)


def test_refill_idempotente_stesso_giorno() -> None:
    async def go() -> None:
        db = _db(guilds=AsyncMock())
        db.guilds.update_one.return_value = SimpleNamespace(modified_count=1)
        with patch("app.guild_supplies.write_audit", new=AsyncMock()) as audit:
            assert await ensure_daily_refill(db, "g-1") is True
            audit.assert_awaited_once()
        # Il filtro CAS usa il giorno: un secondo trigger NON matcha.
        flt = db.guilds.update_one.await_args.args[0]
        assert flt["guild_supplies_last_refill"] == {"$ne": _today()}
        update = db.guilds.update_one.await_args.args[1]
        assert update["$set"]["guild_supplies"] == 120

        db.guilds.update_one.return_value = SimpleNamespace(modified_count=0)
        with patch("app.guild_supplies.write_audit", new=AsyncMock()) as audit:
            assert await ensure_daily_refill(db, "g-1") is False
            audit.assert_not_awaited()  # nessun effetto duplicato

    asyncio.run(go())


def test_spesa_atomica_e_mai_negativa() -> None:
    async def go() -> None:
        db = _db(guilds=AsyncMock())
        # ensure refill (no-op) + spesa ok.
        db.guilds.update_one.side_effect = [
            SimpleNamespace(modified_count=0),   # refill già fatto oggi
            SimpleNamespace(modified_count=1),   # spesa
        ]
        db.guilds.find_one.return_value = {"guild_supplies": 105}
        with patch("app.guild_supplies.write_audit", new=AsyncMock()):
            balance = await spend_supplies(
                db, "g-1", 15, reason="auto_dispatch",
                event_type="auto_dungeon_dispatched",
            )
        assert balance == 105
        spend_filter = db.guilds.update_one.await_args.args[0]
        assert spend_filter["guild_supplies"] == {"$gte": 15}  # mai < 0

        # Saldo insufficiente → 409 col messaggio del mandato.
        db.guilds.update_one.side_effect = [
            SimpleNamespace(modified_count=0),
            SimpleNamespace(modified_count=0),
        ]
        with pytest.raises(HTTPException) as exc:
            await spend_supplies(
                db, "g-1", 15, reason="auto_dispatch",
                event_type="auto_dungeon_dispatched",
            )
        assert exc.value.status_code == 409
        assert exc.value.detail["code"] == "guild_supplies.insufficient"
        assert "Servono 15 Beni di Gilda" in exc.value.detail["user_message"]

    asyncio.run(go())


def test_accredito_cappato_a_120() -> None:
    async def go() -> None:
        today = _today()
        db = _db(guilds=AsyncMock())
        db.guilds.update_one.side_effect = [
            SimpleNamespace(modified_count=0),   # refill no-op
            SimpleNamespace(modified_count=1),   # CAS grant
        ]
        db.guilds.find_one.return_value = {
            "guild_supplies": 118, "guild_supplies_last_refill": today,
        }
        with patch("app.guild_supplies.write_audit", new=AsyncMock()):
            balance = await grant_supplies(
                db, "g-1", DUNGEON_MANUAL_REWARD,
                reason="dungeon_reward",
                event_type="guild_supplies_dungeon_reward",
            )
        assert balance == 120  # 118 + 5 → cap, MAI 123
        update = db.guilds.update_one.await_args.args[1]
        assert update["$set"]["guild_supplies"] == 120

    asyncio.run(go())


def test_mercato_blocca_pacchetto_oltre_cap() -> None:
    async def go() -> None:
        today = _today()
        db = _db(guilds=AsyncMock())
        db.guilds.update_one.return_value = SimpleNamespace(modified_count=0)
        db.guilds.find_one.return_value = {
            "gold": 5000, "guild_supplies": 85,
            "guild_supplies_last_refill": today,
        }
        with pytest.raises(HTTPException) as exc:
            await purchase_market_pack(
                db, {"id": "g-1"}, actor_user_id="u-1",
            )
        detail = exc.value.detail
        assert detail["code"] == "guild_supplies.pack_exceeds_cap"
        # La UI riceve saldo/cap/pacchetto/persi per comunicare tutto.
        assert detail["balance"] == 85
        assert detail["cap"] == 120
        assert detail["pack"] == 100
        assert detail["lost"] == 65  # 85 + 100 = 185 → 65 persi

    asyncio.run(go())


def test_mercato_acquisto_valido_e_oro_insufficiente() -> None:
    async def go() -> None:
        today = _today()
        db = _db(guilds=AsyncMock())
        # Acquisto valido: saldo 10 → +100 = 110 ≤ 120.
        db.guilds.update_one.side_effect = [
            SimpleNamespace(modified_count=0),   # refill no-op
            SimpleNamespace(modified_count=1),   # acquisto atomico
        ]
        db.guilds.find_one.side_effect = [
            {"gold": 2500, "guild_supplies": 10,
             "guild_supplies_last_refill": today},
            {"gold": 500, "guild_supplies": 110},
        ]
        with patch("app.guild_supplies.write_audit", new=AsyncMock()):
            out = await purchase_market_pack(
                db, {"id": "g-1"}, actor_user_id="u-1",
            )
        assert out == {"supplies": 110, "cap": 120, "gold": 500}
        buy_filter = db.guilds.update_one.await_args.args[0]
        assert buy_filter["gold"] == {"$gte": 2000}
        assert buy_filter["guild_supplies"] == {"$lte": 20}

        # Oro insufficiente: il filtro atomico fallisce → 409 dedicato.
        db.guilds.update_one.side_effect = [
            SimpleNamespace(modified_count=0),
            SimpleNamespace(modified_count=0),
        ]
        db.guilds.find_one.side_effect = [
            {"gold": 100, "guild_supplies": 0,
             "guild_supplies_last_refill": today},
            {"gold": 100},
        ]
        with pytest.raises(HTTPException) as exc:
            await purchase_market_pack(
                db, {"id": "g-1"}, actor_user_id="u-1",
            )
        assert exc.value.detail["code"] == "guild_supplies.not_enough_gold"

    asyncio.run(go())


def test_guild_public_espone_saldo_effettivo() -> None:
    from app.guilds.services import guild_public

    doc = {
        "id": "g-1", "owner_user_id": "u-1", "name": "Gilda",
        "created_at": "2026-08-15T00:00:00+00:00",
        "updated_at": "2026-08-15T00:00:00+00:00",
        "guild_supplies": 42,
        "guild_supplies_last_refill": _today(),
    }
    out = guild_public(doc)
    assert out["guild_supplies"] == 42
    assert out["guild_supplies_cap"] == 120
    # Gilda legacy senza campo → 120 (fallback del mandato).
    doc.pop("guild_supplies")
    doc.pop("guild_supplies_last_refill")
    assert guild_public(doc)["guild_supplies"] == 120
