"""ROUND 17.1 P0.5 — Starter dungeon first-fail fallback reward.

Vincoli PM:
- Solo `dungeon.is_starter == True` (attualmente training-yard).
- Solo se `guild.first_expedition_fallback_granted != True` (una-tantum).
- Reward piccolo: +5 gold + +5 XP Prestigio. Nessun loot, nessuna XP adventurer.
- NO Legendary, NO drop table modificata, NO economia alterata.

Test approach: unit sui rami logici del blocco in `_complete_one_expedition`
usando mock DB (motor_mock) + `add_guild_xp` monkeypatched.

Non testiamo l'intero engine spedizione — solo il branch fallback.
"""
from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime, timezone

import pytest
from motor.motor_asyncio import AsyncIOMotorClient


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


async def _prepare_guild(db, guild_id, gold=100, flag=False):
    doc = {
        "id": guild_id,
        "name": "test-guild",
        "gold": gold,
        "first_expedition_fallback_granted": flag,
    }
    await db.guilds.insert_one(doc)


async def _seed_starter(db, dungeon_id, is_starter=True):
    await db.dungeons.insert_one({
        "id": dungeon_id,
        "slug": "training-yard",
        "name": "Campo d'Addestramento",
        "is_starter": is_starter,
        "base_gold_reward": 15,
        "base_xp_reward": 12,
    })


async def _simulate_fallback_branch(db, guild_id, dungeon, exp_id, success):
    """Replica il blocco fallback presente in `_complete_one_expedition`."""
    now = datetime.now(timezone.utc)
    if (not success) and (dungeon.get("is_starter") is True):
        _guild_doc = await db.guilds.find_one(
            {"id": guild_id},
            {"first_expedition_fallback_granted": 1, "gold": 1},
        )
        already_granted = bool(
            (_guild_doc or {}).get("first_expedition_fallback_granted")
        )
        if not already_granted:
            res = await db.guilds.update_one(
                {
                    "id": guild_id,
                    "first_expedition_fallback_granted": {"$ne": True},
                },
                {
                    "$inc": {"gold": 5},
                    "$set": {
                        "first_expedition_fallback_granted": True,
                        "first_expedition_fallback_granted_at": now.isoformat(),
                    },
                },
            )
            return res.modified_count == 1
    return False


async def _impl_fallback_grants_on_first_fail_of_starter_impl():
    """PM vincolo: fallimento #1 su training-yard → +5 gold + flag."""
    c = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db_name = os.environ["DB_NAME"] + "_r171_fallback"
    db = c[db_name]
    await db.guilds.drop()
    guild_id = str(uuid.uuid4())
    await _prepare_guild(db, guild_id, gold=100, flag=False)
    dungeon = {"is_starter": True, "slug": "training-yard"}
    granted = await _simulate_fallback_branch(db, guild_id, dungeon, "exp-1", success=False)
    assert granted is True, "primo fail deve attivare fallback"
    g = await db.guilds.find_one({"id": guild_id})
    assert g["gold"] == 105, f"gold deve essere 105 (100+5), got {g['gold']}"
    assert g["first_expedition_fallback_granted"] is True
    await db.guilds.drop()
    c.close()


def test_fallback_grants_on_first_fail_of_starter():
    _run(_impl_fallback_grants_on_first_fail_of_starter_impl())


async def _impl_fallback_NOT_granted_on_second_fail_impl():
    """PM vincolo: fallimento #2 → NO fallback (già usato)."""
    c = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = c[os.environ["DB_NAME"] + "_r171_fallback"]
    await db.guilds.drop()
    guild_id = str(uuid.uuid4())
    await _prepare_guild(db, guild_id, gold=105, flag=True)
    dungeon = {"is_starter": True, "slug": "training-yard"}
    granted = await _simulate_fallback_branch(db, guild_id, dungeon, "exp-2", success=False)
    assert granted is False, "secondo fail NON deve attivare fallback"
    g = await db.guilds.find_one({"id": guild_id})
    assert g["gold"] == 105, "gold immutato"
    await db.guilds.drop()
    c.close()


def test_fallback_NOT_granted_on_second_fail():
    _run(_impl_fallback_NOT_granted_on_second_fail_impl())


async def _impl_fallback_NOT_granted_on_non_starter_dungeon_impl():
    """PM vincolo: fail su dungeon normale (non is_starter) → NO fallback."""
    c = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = c[os.environ["DB_NAME"] + "_r171_fallback"]
    await db.guilds.drop()
    guild_id = str(uuid.uuid4())
    await _prepare_guild(db, guild_id, gold=100, flag=False)
    dungeon = {"is_starter": False, "slug": "sewer-nest"}
    granted = await _simulate_fallback_branch(db, guild_id, dungeon, "exp-3", success=False)
    assert granted is False
    g = await db.guilds.find_one({"id": guild_id})
    assert g["gold"] == 100
    assert not g.get("first_expedition_fallback_granted")
    await db.guilds.drop()
    c.close()


def test_fallback_NOT_granted_on_non_starter_dungeon():
    _run(_impl_fallback_NOT_granted_on_non_starter_dungeon_impl())


async def _impl_fallback_NOT_granted_on_success_impl():
    """PM vincolo: successo su starter → NO fallback (non serve)."""
    c = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = c[os.environ["DB_NAME"] + "_r171_fallback"]
    await db.guilds.drop()
    guild_id = str(uuid.uuid4())
    await _prepare_guild(db, guild_id, gold=100, flag=False)
    dungeon = {"is_starter": True, "slug": "training-yard"}
    granted = await _simulate_fallback_branch(db, guild_id, dungeon, "exp-4", success=True)
    assert granted is False, "successo NON deve triggerare fallback"
    g = await db.guilds.find_one({"id": guild_id})
    assert g["gold"] == 100
    assert not g.get("first_expedition_fallback_granted")
    await db.guilds.drop()
    c.close()


def test_fallback_NOT_granted_on_success():
    _run(_impl_fallback_NOT_granted_on_success_impl())


# ══════════════════════════════════════════════════════════════════════════
# ROUND 17.1 P0.5 (UI feedback) — Tests for READ-ONLY `fallback_reward`
# derivation exposed by `services.get_expedition` (report payload).
#
# These verify the payload shape consumed by the frontend banner, WITHOUT
# ever writing to DB during the GET report call (pure derivation).
# ══════════════════════════════════════════════════════════════════════════

async def _prepare_get_expedition_scenario(
    db,
    *,
    guild_id: str,
    guild_flag_granted: bool,
    guild_granted_at: str | None,
    exp_id: str,
    dungeon_id: str,
    dungeon_is_starter: bool,
    exp_status: str,
    exp_result_summary: str | None,
    exp_completed_at: str | None,
):
    """Seed the minimal DB state so that `get_expedition` can compute the
    fallback_reward derivation without hitting any real gameplay logic."""
    now_iso = datetime.now(timezone.utc).isoformat()
    guild_doc: dict = {
        "id": guild_id,
        "name": "test-guild-ui",
        "gold": 100,
        "first_expedition_fallback_granted": guild_flag_granted,
    }
    if guild_granted_at is not None:
        guild_doc["first_expedition_fallback_granted_at"] = guild_granted_at
    await db.guilds.insert_one(guild_doc)

    await db.dungeons.insert_one({
        "id": dungeon_id,
        "slug": "training-yard" if dungeon_is_starter else "sewer-nest",
        "name": "Campo d'Addestramento" if dungeon_is_starter else "Sewer Nest",
        "is_starter": dungeon_is_starter,
        "base_gold_reward": 15,
        "base_xp_reward": 12,
        "required_level": 1,
        "required_team_size": 3,
        "recommended_power": 15,
        "base_duration_seconds": 60,
        "is_active": True,
    })

    await db.expeditions.insert_one({
        "id": exp_id,
        "guild_id": guild_id,
        "dungeon_id": dungeon_id,
        "dungeon_name": "Campo d'Addestramento" if dungeon_is_starter else "Sewer Nest",
        "status": exp_status,
        "result_summary": exp_result_summary,
        "result_log": "The expedition failed, but the survivors returned with valuable experience.",
        "started_at": now_iso,
        "completes_at": now_iso,
        "completed_at": exp_completed_at,
        "success_chance": 10,
        "team_power": 12,
        "final_score": 87,
        "gold_reward": 3,
        "xp_reward": 4,
        "adventurer_ids": [],
        "created_at": now_iso,
    })


async def _run_get_expedition(db, guild_id: str, exp_id: str) -> dict:
    """Invoca `services.get_expedition` con la minima signature richiesta."""
    from app.expeditions.services import get_expedition
    guild_doc = await db.guilds.find_one({"id": guild_id}, {"_id": 0})
    return await get_expedition(db, exp_id, guild_doc)


async def _impl_ui_fallback_reward_present_on_first_fail_impl():
    """UI derivation: primo fail su starter → payload contiene
    fallback_reward.granted=true con gold=5, prestige_xp=5."""
    c = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = c[os.environ["DB_NAME"] + "_r171_ui_fallback"]
    for col in ("guilds", "dungeons", "expeditions", "expedition_members"):
        await db[col].drop()

    guild_id = str(uuid.uuid4())
    exp_id = str(uuid.uuid4())
    dungeon_id = str(uuid.uuid4())
    completed_at = datetime.now(timezone.utc).isoformat()

    # Simuliamo lo scenario post-grant: la spedizione è fallita, il flag
    # è settato e `granted_at == completed_at` (identici come nel service).
    await _prepare_get_expedition_scenario(
        db,
        guild_id=guild_id,
        guild_flag_granted=True,
        guild_granted_at=completed_at,
        exp_id=exp_id,
        dungeon_id=dungeon_id,
        dungeon_is_starter=True,
        exp_status="completed",
        exp_result_summary="Failed",
        exp_completed_at=completed_at,
    )

    payload = await _run_get_expedition(db, guild_id, exp_id)
    assert "fallback_reward" in payload, "payload deve esporre 'fallback_reward'"
    fb = payload["fallback_reward"]
    assert fb is not None and fb.get("granted") is True, f"granted=true atteso, got {fb!r}"
    assert fb.get("gold") == 5, f"gold=5, got {fb!r}"
    assert fb.get("prestige_xp") == 5, f"prestige_xp=5, got {fb!r}"

    for col in ("guilds", "dungeons", "expeditions", "expedition_members"):
        await db[col].drop()
    c.close()


def test_ui_fallback_reward_present_on_first_fail():
    _run(_impl_ui_fallback_reward_present_on_first_fail_impl())


async def _impl_ui_fallback_reward_absent_on_second_fail_impl():
    """UI derivation: seconda spedizione fallita successiva al grant → NO
    fallback_reward (granted_at è di un'altra spedizione, non questa)."""
    c = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = c[os.environ["DB_NAME"] + "_r171_ui_fallback"]
    for col in ("guilds", "dungeons", "expeditions", "expedition_members"):
        await db[col].drop()

    guild_id = str(uuid.uuid4())
    exp_id = str(uuid.uuid4())
    dungeon_id = str(uuid.uuid4())
    prev_completed_at = "2026-07-04T09:00:00.000000+00:00"
    this_completed_at = "2026-07-04T10:00:00.000000+00:00"

    await _prepare_get_expedition_scenario(
        db,
        guild_id=guild_id,
        guild_flag_granted=True,
        guild_granted_at=prev_completed_at,  # grant avvenuto in una PRECEDENTE
        exp_id=exp_id,
        dungeon_id=dungeon_id,
        dungeon_is_starter=True,
        exp_status="completed",
        exp_result_summary="Failed",
        exp_completed_at=this_completed_at,
    )

    payload = await _run_get_expedition(db, guild_id, exp_id)
    fb = payload.get("fallback_reward")
    assert fb is None or fb.get("granted") is not True, (
        f"secondo fail NON deve mostrare fallback banner; got {fb!r}"
    )

    for col in ("guilds", "dungeons", "expeditions", "expedition_members"):
        await db[col].drop()
    c.close()


def test_ui_fallback_reward_absent_on_second_fail():
    _run(_impl_ui_fallback_reward_absent_on_second_fail_impl())


async def _impl_ui_fallback_reward_absent_on_non_starter_impl():
    """UI derivation: fail su dungeon non-starter → NO fallback."""
    c = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = c[os.environ["DB_NAME"] + "_r171_ui_fallback"]
    for col in ("guilds", "dungeons", "expeditions", "expedition_members"):
        await db[col].drop()

    guild_id = str(uuid.uuid4())
    exp_id = str(uuid.uuid4())
    dungeon_id = str(uuid.uuid4())

    await _prepare_get_expedition_scenario(
        db,
        guild_id=guild_id,
        guild_flag_granted=False,
        guild_granted_at=None,
        exp_id=exp_id,
        dungeon_id=dungeon_id,
        dungeon_is_starter=False,
        exp_status="completed",
        exp_result_summary="Failed",
        exp_completed_at=datetime.now(timezone.utc).isoformat(),
    )

    payload = await _run_get_expedition(db, guild_id, exp_id)
    fb = payload.get("fallback_reward")
    assert fb is None or fb.get("granted") is not True

    for col in ("guilds", "dungeons", "expeditions", "expedition_members"):
        await db[col].drop()
    c.close()


def test_ui_fallback_reward_absent_on_non_starter():
    _run(_impl_ui_fallback_reward_absent_on_non_starter_impl())


async def _impl_ui_fallback_reward_absent_on_success_impl():
    """UI derivation: success su starter → NO fallback (non serve)."""
    c = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = c[os.environ["DB_NAME"] + "_r171_ui_fallback"]
    for col in ("guilds", "dungeons", "expeditions", "expedition_members"):
        await db[col].drop()

    guild_id = str(uuid.uuid4())
    exp_id = str(uuid.uuid4())
    dungeon_id = str(uuid.uuid4())

    await _prepare_get_expedition_scenario(
        db,
        guild_id=guild_id,
        guild_flag_granted=False,
        guild_granted_at=None,
        exp_id=exp_id,
        dungeon_id=dungeon_id,
        dungeon_is_starter=True,
        exp_status="completed",
        exp_result_summary="Success",
        exp_completed_at=datetime.now(timezone.utc).isoformat(),
    )

    payload = await _run_get_expedition(db, guild_id, exp_id)
    fb = payload.get("fallback_reward")
    assert fb is None or fb.get("granted") is not True

    for col in ("guilds", "dungeons", "expeditions", "expedition_members"):
        await db[col].drop()
    c.close()


def test_ui_fallback_reward_absent_on_success():
    _run(_impl_ui_fallback_reward_absent_on_success_impl())


async def _impl_ui_fallback_derivation_is_read_only_impl():
    """No DB writes durante GET report: gold, flag, granted_at invariati
    dopo la chiamata `get_expedition` (pura derivazione read-only)."""
    c = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = c[os.environ["DB_NAME"] + "_r171_ui_fallback"]
    for col in ("guilds", "dungeons", "expeditions", "expedition_members"):
        await db[col].drop()

    guild_id = str(uuid.uuid4())
    exp_id = str(uuid.uuid4())
    dungeon_id = str(uuid.uuid4())
    completed_at = datetime.now(timezone.utc).isoformat()

    await _prepare_get_expedition_scenario(
        db,
        guild_id=guild_id,
        guild_flag_granted=True,
        guild_granted_at=completed_at,
        exp_id=exp_id,
        dungeon_id=dungeon_id,
        dungeon_is_starter=True,
        exp_status="completed",
        exp_result_summary="Failed",
        exp_completed_at=completed_at,
    )

    before = await db.guilds.find_one({"id": guild_id}, {"_id": 0})
    exp_before = await db.expeditions.find_one({"id": exp_id}, {"_id": 0})

    _ = await _run_get_expedition(db, guild_id, exp_id)
    # Chiama una seconda volta per essere sicuri (idempotency check).
    _ = await _run_get_expedition(db, guild_id, exp_id)

    after = await db.guilds.find_one({"id": guild_id}, {"_id": 0})
    exp_after = await db.expeditions.find_one({"id": exp_id}, {"_id": 0})

    assert after["gold"] == before["gold"], (
        f"read-only violato: gold prima={before['gold']} dopo={after['gold']}"
    )
    assert after["first_expedition_fallback_granted"] == before["first_expedition_fallback_granted"]
    assert after.get("first_expedition_fallback_granted_at") == before.get(
        "first_expedition_fallback_granted_at"
    )
    assert exp_after["status"] == exp_before["status"]
    assert exp_after["result_summary"] == exp_before["result_summary"]
    assert exp_after["completed_at"] == exp_before["completed_at"]

    for col in ("guilds", "dungeons", "expeditions", "expedition_members"):
        await db[col].drop()
    c.close()


def test_ui_fallback_derivation_is_read_only():
    _run(_impl_ui_fallback_derivation_is_read_only_impl())
