"""ROUND 16.0 — Phase 3 backend invariants.

Verifies:
  * 50 active races seeded with the planned rarity distribution.
  * 100% of adventurers carry race_slug + gender after backfill.
  * Gender split is ~50/50 (±2%).
  * `/api/adventurers/{id}/auto-equip` is idempotent and never returns
    a regression in score.
"""
from __future__ import annotations

import asyncio
import os

import requests
from motor.motor_asyncio import AsyncIOMotorClient


BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
API = f"{BACKEND_URL}/api"


def _db_run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def _client():
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return cli[os.environ["DB_NAME"]], cli


def _login() -> str:
    r = requests.post(f"{API}/auth/login",
                      json={"email": "tester@orbus.test",
                            "password": "password123"}, timeout=10)
    r.raise_for_status()
    return r.json()["access_token"]


def test_t01_fifty_active_races():
    async def _q():
        db, cli = _client()
        try:
            n = await db.races.count_documents({"is_active": True})
            return n
        finally:
            cli.close()
    assert _db_run(_q()) == 50


def test_t02_rarity_distribution():
    async def _q():
        db, cli = _client()
        try:
            pipe = [{"$group": {"_id": "$rarity", "c": {"$sum": 1}}}]
            return {r["_id"]: r["c"]
                    async for r in db.races.aggregate(pipe)}
        finally:
            cli.close()
    counts = _db_run(_q())
    assert counts == {"common": 30, "uncommon": 12, "rare": 6, "epic": 2}, counts


def test_t03_all_adventurers_have_race_and_gender():
    async def _q():
        db, cli = _client()
        try:
            total = await db.adventurers.count_documents({})
            with_race = await db.adventurers.count_documents(
                {"race_slug": {"$ne": None, "$exists": True}})
            with_gender = await db.adventurers.count_documents(
                {"gender": {"$in": ["male", "female"]}})
            return total, with_race, with_gender
        finally:
            cli.close()
    total, race, gender = _db_run(_q())
    assert race == total, f"race missing on {total - race} adventurers"
    assert gender == total, f"gender missing on {total - gender} adventurers"


def test_t04_gender_split_around_50_50():
    async def _q():
        db, cli = _client()
        try:
            pipe = [{"$group": {"_id": "$gender", "c": {"$sum": 1}}}]
            return {r["_id"]: r["c"]
                    async for r in db.adventurers.aggregate(pipe)}
        finally:
            cli.close()
    counts = _db_run(_q())
    male = counts.get("male", 0)
    female = counts.get("female", 0)
    total = male + female
    assert total > 0
    male_pct = male / total
    assert 0.48 <= male_pct <= 0.52, f"male share={male_pct:.3f}"


def test_t05_adventurer_dto_exposes_race_and_gender():
    token = _login()
    r = requests.get(f"{API}/adventurers",
                     headers={"Authorization": f"Bearer {token}"}, timeout=10)
    assert r.status_code == 200
    body = r.json()
    advs = body if isinstance(body, list) else body.get("adventurers") or []
    assert advs
    sample = advs[0]
    assert "race_slug" in sample
    assert "gender" in sample
    assert sample["race_slug"]
    assert sample["gender"] in ("male", "female")


def test_t06_auto_equip_idempotent_and_no_regression():
    token = _login()
    advs = requests.get(
        f"{API}/adventurers",
        headers={"Authorization": f"Bearer {token}"}, timeout=10,
    ).json()
    advs = advs if isinstance(advs, list) else advs.get("adventurers") or []
    # Pick the highest-level adventurer for the most realistic flow.
    target = max(advs, key=lambda a: a.get("level") or 0)
    h = {"Authorization": f"Bearer {token}"}
    r1 = requests.post(f"{API}/adventurers/{target['id']}/auto-equip",
                       headers=h, timeout=15)
    assert r1.status_code == 200, r1.text
    s1 = r1.json()
    assert s1["score_after"] >= s1["score_before"]
    r2 = requests.post(f"{API}/adventurers/{target['id']}/auto-equip",
                       headers=h, timeout=15)
    assert r2.status_code == 200
    s2 = r2.json()
    # Idempotent — same state, no further swaps.
    assert s2["swaps_count"] == 0, s2
    assert s2["score_after"] == s1["score_after"]


def test_t07_audit_events_emitted_for_race_and_gender():
    async def _q():
        db, cli = _client()
        try:
            return {
                "race": await db.audit_log.count_documents(
                    {"event_type": "adventurer_race_assigned"}),
                "gender": await db.audit_log.count_documents(
                    {"event_type": "adventurer_gender_assigned"}),
                "seed": await db.audit_log.count_documents(
                    {"event_type": "race_seeded_round160"}),
                "auto_equip": await db.audit_log.count_documents(
                    {"event_type": "adventurer_auto_equipped"}),
            }
        finally:
            cli.close()
    counts = _db_run(_q())
    assert counts["seed"] == 50
    assert counts["race"] >= 92_000
    assert counts["gender"] >= 92_000
    assert counts["auto_equip"] >= 1
