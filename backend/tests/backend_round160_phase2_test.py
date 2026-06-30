"""ROUND 16.0 — Phase 2 backend invariants.

Verifies the rework migration has settled and the new endpoints behave
as designed:
  * 10 active base classes (including warlock)
  * 3 deprecated classes flagged correctly with successor pointers
  * 30 specializations seeded across the 10 base classes
  * 0 adventurers still in a deprecated class
  * migrated adventurers carry `specialization_slug`
  * equip validator v2 accepts legacy items via spec_unlocks
  * `/api/class-halls` lifecycle (list, detail, unlock spec)
"""
from __future__ import annotations

import asyncio
import os

import requests
from motor.motor_asyncio import AsyncIOMotorClient

from app.equipment.compatibility import check_equip_compatibility


BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
API = f"{BACKEND_URL}/api"


def _login(email: str = "tester@orbus.test",
           password: str = "password123") -> str:
    r = requests.post(f"{API}/auth/login",
                      json={"email": email, "password": password}, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _db():
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return cli[os.environ["DB_NAME"]], cli


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro) \
        if False else asyncio.new_event_loop().run_until_complete(coro)


def test_t01_ten_active_base_classes():
    """Post-R16.0.1 the catalog has 11 active base classes (10 + alchemist).
    The assertion remains permissive (≥10) and explicitly checks both
    Warlock (R16.0) and Alchemist (R16.0.1) are present."""
    async def _q():
        db, cli = _db()
        try:
            rows = await db.adventurer_classes.find(
                {"is_active": True, "is_base_class": True,
                 "slug": {"$not": {"$regex": r"^test-"}}},
                {"_id": 0, "slug": 1},
            ).to_list(50)
            return sorted(r["slug"] for r in rows)
        finally:
            cli.close()
    slugs = _run(_q())
    assert len(slugs) >= 10, f"Expected ≥10 base classes, got {slugs}"
    assert "warlock" in slugs
    assert "alchemist" in slugs


def test_t02_three_deprecated_with_successor():
    async def _q():
        db, cli = _db()
        try:
            return await db.adventurer_classes.find(
                {"deprecated_at": {"$ne": None}},
                {"_id": 0, "slug": 1, "successor_slug": 1,
                 "successor_specialization_slug": 1},
            ).to_list(50)
        finally:
            cli.close()
    rows = _run(_q())
    expected = {
        "berserker": ("warrior", "berserker_spec"),
        "assassin": ("rogue", "assassin_spec"),
        "necromancer": ("mage", "necromancer_spec"),
    }
    found = {r["slug"]: (r["successor_slug"],
                        r["successor_specialization_slug"]) for r in rows}
    assert found == expected, found


def test_t03_warlock_primary_stat_intellect():
    async def _q():
        db, cli = _db()
        try:
            return await db.adventurer_classes.find_one({"slug": "warlock"})
        finally:
            cli.close()
    doc = _run(_q())
    assert doc is not None
    assert doc.get("primary_stat") == "intellect"
    assert doc.get("is_base_class") is True


def test_t04_thirty_specializations():
    """Round 16.0 baselined 30 specs (10 base classes × 3). Round 16.0.1 added
    the Alchemist (+3 specs → 33). This assertion now allows the post-R16.0.1
    superset and verifies each known base class has exactly 3."""
    async def _q():
        db, cli = _db()
        try:
            n = await db.class_specializations.count_documents({"is_active": True})
            per_class = {}
            for slug in ("warrior", "rogue", "mage", "priest", "ranger",
                         "paladin", "druid", "monk", "bard", "warlock",
                         # ROUND 16.0.1 — 11th base class.
                         "alchemist"):
                per_class[slug] = await db.class_specializations.count_documents(
                    {"$or": [
                        {"class_slug": slug, "is_active": True},
                        {"parent_class_slug": slug, "is_active": True},
                    ]})
            return n, per_class
        finally:
            cli.close()
    n, per_class = _run(_q())
    assert n >= 30, f"Expected ≥30 active specializations, got {n}"
    for slug, c in per_class.items():
        assert c == 3, f"{slug} should have 3 specs (got {c})"


def test_t05_no_adventurer_in_deprecated_class():
    async def _q():
        db, cli = _db()
        try:
            return await db.adventurers.count_documents(
                {"$or": [
                    {"class_slug": {"$in": ["berserker", "assassin",
                                            "necromancer"]}},
                    {"class_name": {"$in": ["Berserker", "Assassin",
                                            "Necromancer"]}},
                ]})
        finally:
            cli.close()
    n = _run(_q())
    assert n == 0, f"Found {n} adventurers still in deprecated classes"


def test_t06_migrated_adventurers_have_consistent_spec_class():
    async def _q():
        db, cli = _db()
        try:
            return await db.adventurers.find(
                {"specialization_slug": {"$in": [
                    "berserker_spec", "assassin_spec", "necromancer_spec"]}},
                {"_id": 0, "class_slug": 1, "specialization_slug": 1},
            ).to_list(200)
        finally:
            cli.close()
    rows = _run(_q())
    assert len(rows) > 0, "No migrated adventurers found"
    mapping = {
        "berserker_spec": "warrior",
        "assassin_spec": "rogue",
        "necromancer_spec": "mage",
    }
    for r in rows:
        assert r["class_slug"] == mapping[r["specialization_slug"]], (
            f"Inconsistent: {r}")


def test_t07_equip_validator_accepts_legacy_via_spec_unlocks():
    adv = {"class_slug": "warrior", "specialization_slug": "berserker_spec"}
    item_migrated = {
        "class_tags": ["berserker", "warrior"],
        "recommended_classes": ["berserker", "warrior"],
        "specialization_unlocks": ["berserker_spec"],
        "weapon_tags": ["axe"],
    }
    out = check_equip_compatibility(adv, item_migrated)
    assert out["allowed"] is True
    assert out["severity"] == "ok"
    assert out["reason_code"] == "specialization_match"


def test_t07b_equip_validator_warning_on_spec_mismatch():
    adv = {"class_slug": "warrior", "specialization_slug": "guardian_spec"}
    item = {
        "class_tags": ["berserker", "warrior"],
        "recommended_classes": ["berserker", "warrior"],
        "specialization_unlocks": ["berserker_spec"],
    }
    out = check_equip_compatibility(adv, item)
    assert out["allowed"] is True
    assert out["severity"] == "warning"
    assert out["reason_code"] == "specialization_mismatch"


def test_t08_class_halls_seeded_for_tester():
    async def _q():
        db, cli = _db()
        try:
            g = await db.guilds.find_one({"name": "The Iron Lantern"},
                                         {"id": 1})
            assert g
            rows = await db.class_halls.find(
                {"guild_id": g["id"]},
                {"_id": 0, "class_slug": 1, "is_unlocked": 1},
            ).to_list(50)
            return rows
        finally:
            cli.close()
    rows = _run(_q())
    slugs = {r["class_slug"] for r in rows}
    expected = {"warrior", "rogue", "mage", "priest", "ranger",
                "paladin", "druid", "monk", "bard", "warlock",
                # ROUND 16.0.1 — 11th base class.
                "alchemist"}
    assert expected <= slugs, f"Missing halls: {expected - slugs}"
    unlocked = {r["class_slug"] for r in rows if r["is_unlocked"]}
    assert {"warrior", "rogue", "mage"} <= unlocked


def test_t09_unlock_specialization_endpoint_and_idempotent():
    token = _login()
    r = requests.get(f"{API}/class-halls", headers=_h(token), timeout=10)
    assert r.status_code == 200
    halls = r.json()["halls"]
    # ROUND 16.0.1 — alchemist joined the catalog → 11 halls.
    assert len(halls) >= 10
    r1 = requests.post(
        f"{API}/class-halls/warrior/unlock-specialization",
        headers=_h(token), json={"specialization_slug": "guardian_spec"},
        timeout=10,
    )
    assert r1.status_code == 200, r1.text
    specs_after = r1.json()["hall"]["unlocked_specializations"]
    assert "guardian_spec" in specs_after
    r2 = requests.post(
        f"{API}/class-halls/warrior/unlock-specialization",
        headers=_h(token), json={"specialization_slug": "guardian_spec"},
        timeout=10,
    )
    assert r2.status_code == 200
    assert r2.json()["hall"]["unlocked_specializations"] == specs_after


def test_t10_unlock_locked_hall_returns_423():
    token = _login()
    r = requests.post(
        f"{API}/class-halls/warlock/unlock-specialization",
        headers=_h(token), json={"specialization_slug": "demon_pact_spec"},
        timeout=10,
    )
    assert r.status_code == 423, r.text
    body = r.json()
    assert body["detail"]["code"] == "class_hall.locked"
