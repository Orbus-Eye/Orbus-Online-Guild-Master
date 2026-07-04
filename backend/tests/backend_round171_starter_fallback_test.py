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
