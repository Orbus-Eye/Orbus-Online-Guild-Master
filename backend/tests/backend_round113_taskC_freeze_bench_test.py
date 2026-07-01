"""ROUND 11.3 Turno 3 — Fase 3A — TASK C Recruit Freeze Bench.

8 BE tests:
  C.01 — GET /frozen returns empty bench shape for a fresh guild.
  C.02 — POST /freeze happy path: removes candidate from pool, adds to bench,
         survives a /refresh, writes audit `recruit_candidate_frozen`.
  C.03 — POST /freeze 404 `recruit.candidate_not_found` for unknown id.
  C.04 — POST /freeze 409 `freeze_bench.full` when 2 slots already used.
  C.05 — POST /unfreeze happy path: bench shrinks, audit written, snapshot
         NOT returned to active pool.
  C.06 — POST /recruit-frozen happy path: creates adv, debits gold, removes
         from bench, audit written. PII guard on response.
  C.07 — POST /recruit-frozen 402 `economy.insufficient_gold` when gold low,
         snapshot restored on the bench.
  C.08 — POST /recruit-frozen 423 `roster_over_capacity` when cap full,
         snapshot restored on the bench and gold not debited.
"""
from __future__ import annotations

import os
import uuid

import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")


@pytest.fixture(scope="module")
def mdb():
    cli = MongoClient(MONGO_URL)
    yield cli[DB_NAME]
    cli.close()


def _register_throwaway(email: str | None = None) -> tuple[str, str]:
    """Spin up a fresh user+guild so each test owns its own state."""
    email = email or f"freeze-{uuid.uuid4().hex[:8]}@orbus.test"
    pw = "password123!"
    r = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": email, "username": email.split("@")[0], "password": pw},
        timeout=10,
    )
    assert r.status_code in (200, 201), r.text
    tok = r.json()["access_token"]
    g = requests.post(
        f"{BASE_URL}/api/guilds",
        json={"name": f"FreezeGuild-{uuid.uuid4().hex[:6]}", "description": "t"},
        headers={"Authorization": f"Bearer {tok}"},
        timeout=10,
    )
    assert g.status_code in (200, 201), g.text
    return tok, email


def _h(tok: str) -> dict:
    return {"Authorization": f"Bearer {tok}"}


def _seed_offer(mdb, guild_id: str) -> list[dict]:
    """Force a refresh so the offer pool is freshly populated for this guild."""
    # We cheat slightly by inserting offers manually if there's no offer
    # generator hook — but /candidates initialises the pool on first call,
    # so just hit that.
    return []


def _get_guild_id(mdb, email: str) -> str:
    u = mdb.users.find_one({"email": email}, {"_id": 0, "id": 1})
    g = mdb.guilds.find_one({"owner_user_id": u["id"]}, {"_id": 0, "id": 1})
    return g["id"]


def _upgrade_dorm_for_test(mdb, tok: str, guild_id: str, level: int = 2):
    """Bypass the Territory upgrade flow for tests that need extra roster
    capacity. First touches `GET /api/territory` to lazily seed the
    `guild_structures` doc, then bumps `dormitories.level` in place.
    Used ONLY in tests."""
    # Lazy-init the structures doc via the public endpoint.
    requests.get(f"{BASE_URL}/api/territory", headers=_h(tok), timeout=10)
    mdb.guild_structures.update_one(
        {"guild_id": guild_id},
        {"$set": {
            "structures.dormitories.level": level,
            "structures.dormitories.is_unlocked": True,
        }},
    )


def _list_pool_ids(tok: str) -> list[str]:
    r = requests.get(f"{BASE_URL}/api/recruitment/candidates", headers=_h(tok), timeout=10)
    body = r.json()
    return [c["candidate_id"] for c in body.get("candidates", [])]


# ─── C.01 ─────────────────────────────────────────────────────────────────────
def test_c_01_frozen_empty_for_fresh_guild():
    tok, _ = _register_throwaway()
    r = requests.get(f"{BASE_URL}/api/recruitment/frozen", headers=_h(tok), timeout=10)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["frozen"] == []
    assert body["max_slots"] == 2
    assert body["used_slots"] == 0


# ─── C.02 ─────────────────────────────────────────────────────────────────────
def test_c_02_freeze_happy_persists_across_refresh(mdb):
    tok, email = _register_throwaway()
    gid = _get_guild_id(mdb, email)
    pool = _list_pool_ids(tok)
    assert pool, "Empty initial pool — generator regression?"
    cid = pool[0]

    r = requests.post(
        f"{BASE_URL}/api/recruitment/freeze",
        json={"candidate_id": cid},
        headers=_h(tok),
        timeout=10,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["used_slots"] == 1
    assert len(body["frozen"]) == 1
    frozen_id = body["frozen"][0]["frozen_id"]
    # Original candidate is removed from the active pool.
    assert mdb.recruitment_offers.find_one({"id": cid}) is None

    # Force a refresh and confirm the bench survives.
    rr = requests.post(f"{BASE_URL}/api/recruitment/refresh", headers=_h(tok), timeout=10)
    assert rr.status_code == 200, rr.text
    after = requests.get(f"{BASE_URL}/api/recruitment/frozen", headers=_h(tok), timeout=10).json()
    assert after["used_slots"] == 1
    assert any(s["frozen_id"] == frozen_id for s in after["frozen"])

    # Audit event written. Collection name is `audit_log` (not audit_events).
    audit = mdb.audit_log.find_one({
        "event_type": "recruit_candidate_frozen",
        "actor_guild_id": gid,
        "related_entity_id": frozen_id,
    })
    assert audit is not None, "Audit `recruit_candidate_frozen` missing."


# ─── C.03 ─────────────────────────────────────────────────────────────────────
def test_c_03_freeze_404_for_unknown_candidate():
    tok, _ = _register_throwaway()
    bogus = str(uuid.uuid4())
    r = requests.post(
        f"{BASE_URL}/api/recruitment/freeze",
        json={"candidate_id": bogus},
        headers=_h(tok),
        timeout=10,
    )
    assert r.status_code == 404, r.text
    detail = (r.json() or {}).get("detail") or {}
    assert detail.get("code") == "recruit.candidate_not_found"


# ─── C.04 ─────────────────────────────────────────────────────────────────────
def test_c_04_freeze_409_when_bench_full():
    tok, _ = _register_throwaway()
    # Fill 2 slots by freezing 2 candidates.
    pool = _list_pool_ids(tok)
    assert len(pool) >= 3, "Pool too small for full-bench test."
    for cid in pool[:2]:
        rr = requests.post(
            f"{BASE_URL}/api/recruitment/freeze",
            json={"candidate_id": cid},
            headers=_h(tok),
            timeout=10,
        )
        assert rr.status_code == 200, rr.text
    # Third attempt must 409.
    third = pool[2]
    r = requests.post(
        f"{BASE_URL}/api/recruitment/freeze",
        json={"candidate_id": third},
        headers=_h(tok),
        timeout=10,
    )
    assert r.status_code == 409, r.text
    detail = (r.json() or {}).get("detail") or {}
    assert detail.get("code") == "freeze_bench.full"
    assert detail.get("max_slots") == 2
    # The third candidate must still be in the active pool (no consumption
    # on the rejection path).
    after_pool = _list_pool_ids(tok)
    assert third in after_pool, "Candidate consumed despite 409 rejection."


# ─── C.05 ─────────────────────────────────────────────────────────────────────
def test_c_05_unfreeze_drops_slot_and_audits(mdb):
    tok, email = _register_throwaway()
    gid = _get_guild_id(mdb, email)
    pool = _list_pool_ids(tok)
    cid = pool[0]
    r = requests.post(
        f"{BASE_URL}/api/recruitment/freeze",
        json={"candidate_id": cid},
        headers=_h(tok),
        timeout=10,
    )
    fid = r.json()["frozen"][0]["frozen_id"]

    # Unfreeze.
    r = requests.post(
        f"{BASE_URL}/api/recruitment/unfreeze",
        json={"frozen_id": fid},
        headers=_h(tok),
        timeout=10,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["used_slots"] == 0
    # Snapshot is dropped, NOT returned to active pool.
    pool_after = _list_pool_ids(tok)
    assert cid not in pool_after, "Unfreeze leaked candidate back to active pool."

    # Audit. Collection name is `audit_log`.
    audit = mdb.audit_log.find_one({
        "event_type": "recruit_candidate_unfrozen",
        "actor_guild_id": gid,
        "related_entity_id": fid,
    })
    assert audit is not None, "Audit `recruit_candidate_unfrozen` missing."


# ─── C.06 ─────────────────────────────────────────────────────────────────────
def test_c_06_recruit_frozen_happy(mdb):
    tok, email = _register_throwaway()
    gid = _get_guild_id(mdb, email)
    # Lift the dorm cap to make room for the recruit (starter takes 5/5).
    _upgrade_dorm_for_test(mdb, tok, gid, level=2)
    pool = _list_pool_ids(tok)
    cid = pool[0]
    r = requests.post(
        f"{BASE_URL}/api/recruitment/freeze",
        json={"candidate_id": cid},
        headers=_h(tok),
        timeout=10,
    )
    fid = r.json()["frozen"][0]["frozen_id"]

    # Recruit frozen.
    r = requests.post(
        f"{BASE_URL}/api/recruitment/recruit-frozen",
        json={"frozen_id": fid},
        headers=_h(tok),
        timeout=10,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    # PII guard.
    assert "email" not in body and "_id" not in body and "user_id" not in body
    assert body["adventurer"]["name"]
    # Bench is now empty.
    bench_after = requests.get(f"{BASE_URL}/api/recruitment/frozen", headers=_h(tok), timeout=10).json()
    assert bench_after["used_slots"] == 0

    # Audit.
    audit = mdb.audit_log.find_one({
        "event_type": "recruit_frozen_candidate_hired",
        "actor_guild_id": gid,
    })
    assert audit is not None, "Audit `recruit_frozen_candidate_hired` missing."


# ─── C.07 ─────────────────────────────────────────────────────────────────────
def test_c_07_recruit_frozen_402_insufficient_gold(mdb):
    tok, email = _register_throwaway()
    gid = _get_guild_id(mdb, email)
    # Lift the dorm cap so the pre-flight cap guard doesn't pre-empt the
    # gold check we want to assert on.
    _upgrade_dorm_for_test(mdb, tok, gid, level=2)
    pool = _list_pool_ids(tok)
    cid = pool[0]
    r = requests.post(
        f"{BASE_URL}/api/recruitment/freeze",
        json={"candidate_id": cid},
        headers=_h(tok),
        timeout=10,
    )
    fid = r.json()["frozen"][0]["frozen_id"]

    # Drain the guild's gold to 0.
    mdb.guilds.update_one({"id": gid}, {"$set": {"gold": 0}})

    r = requests.post(
        f"{BASE_URL}/api/recruitment/recruit-frozen",
        json={"frozen_id": fid},
        headers=_h(tok),
        timeout=10,
    )
    assert r.status_code == 402, r.text
    detail = (r.json() or {}).get("detail") or {}
    assert detail.get("code") == "economy.insufficient_gold"

    # Snapshot must still be on the bench (compensating restore worked).
    bench = requests.get(f"{BASE_URL}/api/recruitment/frozen", headers=_h(tok), timeout=10).json()
    assert bench["used_slots"] == 1
    assert bench["frozen"][0]["frozen_id"] == fid


# ─── C.08 ─────────────────────────────────────────────────────────────────────
def test_c_08_recruit_frozen_423_cap_full(mdb):
    """Simulate roster cap full and confirm the recruit-frozen path rejects
    cleanly without consuming the bench slot or debiting gold."""
    tok, email = _register_throwaway()
    gid = _get_guild_id(mdb, email)
    pool = _list_pool_ids(tok)
    cid = pool[0]
    r = requests.post(
        f"{BASE_URL}/api/recruitment/freeze",
        json={"candidate_id": cid},
        headers=_h(tok),
        timeout=10,
    )
    fid = r.json()["frozen"][0]["frozen_id"]

    # Force the guild's roster count >= cap by inserting filler advs.
    # Dormitories Lv1 cap = 5. Tester starter roster already at 5. Insert
    # an extra filler to push current > cap so the pre-flight guard fires.
    gold_before = mdb.guilds.find_one({"id": gid}, {"_id": 0, "gold": 1})["gold"]
    for i in range(6):  # over a Lv1 dorm cap (=5) for sure.
        mdb.adventurers.insert_one({
            "id": f"filler-{uuid.uuid4().hex[:8]}",
            "guild_id": gid,
            "name": f"Filler {i}", "adventurer_class_id": "x", "class_name": "Warrior",
            "class_role": "DPS", "rarity": "Common", "level": 1, "experience": 0,
            "strength": 5, "agility": 5, "intellect": 5, "endurance": 5, "faith": 5,
            "stamina": 100, "morale": 100, "traits": [],
            "is_available": True, "is_starter": False, "rename_count": 0,
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
        })

    r = requests.post(
        f"{BASE_URL}/api/recruitment/recruit-frozen",
        json={"frozen_id": fid},
        headers=_h(tok),
        timeout=10,
    )
    assert r.status_code == 423, r.text
    detail = (r.json() or {}).get("detail") or {}
    assert detail.get("code") == "roster_over_capacity"

    # Bench unchanged.
    bench = requests.get(f"{BASE_URL}/api/recruitment/frozen", headers=_h(tok), timeout=10).json()
    assert bench["used_slots"] == 1
    # Gold unchanged (no debit before the cap guard fired).
    gold_after = mdb.guilds.find_one({"id": gid}, {"_id": 0, "gold": 1})["gold"]
    assert gold_after == gold_before
