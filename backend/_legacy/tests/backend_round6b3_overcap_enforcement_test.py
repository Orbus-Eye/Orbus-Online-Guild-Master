"""ROUND 6B.3 Wave 1.5 — Over-cap roster enforcement.

15 backend tests covering:
 * over-cap server-side block on recruit / expedition / raid / replay-last
 * retired-in-set block on expedition / raid / squad-create / squad-update
 * equip blocked when target is retired
 * cap_state escape valves: territory.upgrade and adventurer.retire MUST
   stay accessible while over-cap (the only two ways out)
 * `retired_by` field is set to "user" on the retire endpoint
 * squads silently filter retired members on read (no 500)
 * old expedition reports remain readable after retire
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
def db():
    cli = MongoClient(MONGO_URL)
    yield cli[DB_NAME]
    cli.close()


# ─── Helpers ───────────────────────────────────────────────────────────


def _fresh_user(db, prefix: str = "r6b3_oc"):
    tag = f"{prefix}_{uuid.uuid4().hex[:8]}"
    email = f"{tag}@orbus.test"
    requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": email, "username": tag, "password": "Test12345!",
    }, timeout=15)
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": email, "password": "Test12345!",
    }, timeout=15)
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    requests.post(
        f"{BASE_URL}/api/guilds", json={"name": f"OC {tag[-6:]}"},
        headers=h, timeout=15,
    )
    g = requests.get(f"{BASE_URL}/api/guilds/me", headers=h, timeout=15).json()["guild"]
    db.users.update_one({"email": email}, {"$set": {"is_test_user": True}})
    db.guilds.update_one({"id": g["id"]}, {"$set": {"gold": 200_000}})
    return h, g["id"], email


def _make_starter_advs(db, guild_id: str, count: int) -> list[str]:
    """Bulk insert non-retired adventurers belonging to `guild_id`.

    Skips the recruit flow so we can build over-cap fixtures fast.
    We mimic the minimum projection contract from `adventurer_public()` /
    `_adventurer_unit_power()` — missing fields would 500 the GET roster.
    """
    # Pick any seeded class so `adventurer_class_id` matches a real row.
    cls = db.adventurer_classes.find_one({}, {"_id": 0, "id": 1, "slug": 1, "role": 1})
    assert cls, "no adventurer_classes seeded — tests cannot continue"
    now = "2026-06-27T22:00:00+00:00"
    docs = []
    for i in range(count):
        docs.append({
            "id": str(uuid.uuid4()),
            "guild_id": guild_id,
            "name": f"Test Adv {i}",
            "adventurer_class_id": cls["id"],
            "class_name": cls.get("slug"),
            "class_role": cls.get("role"),
            "rarity": "Common",
            "level": 1, "experience": 0,
            "strength": 10, "agility": 10, "intellect": 10,
            "endurance": 10, "faith": 10,
            "stamina": 100, "morale": 100,
            "is_available": True,
            "is_retired": False,
            "traits": [],
            "is_starter": False,
            "is_test_seed": True,
            "created_at": now,
            "updated_at": now,
        })
    if docs:
        db.adventurers.insert_many(docs)
    return [d["id"] for d in docs]


def _ensure_territory_doc(db, guild_id: str) -> None:
    """Make sure the guild_structures doc exists for `guild_id`.
    Inserts a bare doc directly if missing — fast path, no HTTP."""
    if db.guild_structures.find_one({"guild_id": guild_id}, {"_id": 1}) is None:
        db.guild_structures.insert_one({
            "id": str(uuid.uuid4()),
            "guild_id": guild_id,
            "structures": {},
            "created_at": "2026-06-27T00:00:00+00:00",
            "updated_at": "2026-06-27T00:00:00+00:00",
        })


def _force_over_cap(db, guild_id: str, *, current: int = 8, cap: int = 5) -> list[str]:
    """Set up a guild with `current > cap`. We bulk-delete the onboarding
    starter roster first so the count is exactly `current`. Dormitory Lv1
    → cap=5 by default; pass `cap` >= current to verify the no-block path.
    """
    db.adventurers.delete_many({"guild_id": guild_id})
    _ensure_territory_doc(db, guild_id)
    dormitory_level_for_cap = {0: 0, 5: 1, 10: 2, 15: 3, 20: 4, 25: 5, 30: 6}
    dl = dormitory_level_for_cap.get(cap, 1)
    db.guild_structures.update_one(
        {"guild_id": guild_id},
        {"$set": {"structures.dormitories": {
            "level": dl, "is_unlocked": True,
            "purchased_at": "2026-06-27T00:00:00+00:00",
            "upgraded_at": "2026-06-27T00:00:00+00:00",
            "acquired_via": "test_setup",
        }}},
    )
    return _make_starter_advs(db, guild_id, current)


def _set_dormitory_cap(db, guild_id: str, cap: int) -> None:
    """Configure dormitory level so cap is at least `cap`."""
    _ensure_territory_doc(db, guild_id)
    dormitory_level_for_cap = {0: 0, 5: 1, 10: 2, 15: 3, 20: 4, 25: 5, 30: 6}
    dl = dormitory_level_for_cap.get(cap, 3)
    db.guild_structures.update_one(
        {"guild_id": guild_id},
        {"$set": {"structures.dormitories": {
            "level": dl, "is_unlocked": True,
            "purchased_at": "2026-06-27T00:00:00+00:00",
            "upgraded_at": "2026-06-27T00:00:00+00:00",
            "acquired_via": "test_setup",
        }}},
    )


def _retire_via_api(h, adv_id) -> requests.Response:
    return requests.post(
        f"{BASE_URL}/api/adventurers/{adv_id}/retire",
        json={"reason": "test"}, headers=h, timeout=15,
    )


# ─── Tests ─────────────────────────────────────────────────────────────


class TestOverCapEnforcement:
    """Wave 1.5 — block destructive write flows when current > cap."""

    def test_01_recruit_blocked_when_over_cap(self, db):
        h, gid, _ = _fresh_user(db)
        _force_over_cap(db, gid)  # 8 advs / cap 5 (over by 3)
        # First trigger candidates so an offer exists
        candidates = requests.get(
            f"{BASE_URL}/api/recruitment/candidates", headers=h, timeout=15,
        ).json()
        cid = candidates["candidates"][0]["candidate_id"]
        r = requests.post(
            f"{BASE_URL}/api/recruitment/recruit",
            json={"candidate_id": cid}, headers=h, timeout=15,
        )
        assert r.status_code == 423, r.text
        body = r.json()["detail"]
        assert body["code"] == "roster_over_capacity"
        assert body["current"] == 8
        assert body["cap"] == 5
        assert body["must_retire"] == 4  # 8 + 1 - 5

    def test_02_expedition_create_blocked_when_over_cap(self, db):
        h, gid, _ = _fresh_user(db)
        adv_ids = _force_over_cap(db, gid)
        dung = requests.get(f"{BASE_URL}/api/dungeons", headers=h, timeout=15).json()
        dungeon_id = dung[0]["id"] if isinstance(dung, list) else dung["dungeons"][0]["id"]
        r = requests.post(
            f"{BASE_URL}/api/expeditions",
            json={"dungeon_id": dungeon_id, "adventurer_ids": adv_ids[:3]},
            headers=h, timeout=15,
        )
        assert r.status_code == 423, r.text
        assert r.json()["detail"]["code"] == "roster_over_capacity"

    def test_03_expedition_create_blocked_when_payload_has_retired(self, db):
        h, gid, _ = _fresh_user(db)
        _set_dormitory_cap(db, gid, cap=20)  # avoid over-cap path
        adv_ids = _make_starter_advs(db, gid, 4)
        # Mark one as retired directly in DB
        db.adventurers.update_one(
            {"id": adv_ids[0]}, {"$set": {"is_retired": True, "is_available": False}},
        )
        dung = requests.get(f"{BASE_URL}/api/dungeons", headers=h, timeout=15).json()
        dungeon_id = dung[0]["id"] if isinstance(dung, list) else dung["dungeons"][0]["id"]
        r = requests.post(
            f"{BASE_URL}/api/expeditions",
            json={"dungeon_id": dungeon_id, "adventurer_ids": adv_ids[:3]},
            headers=h, timeout=15,
        )
        assert r.status_code == 423, r.text
        body = r.json()["detail"]
        assert body["code"] == "adventurers.retired_in_set"
        assert adv_ids[0] in body["retired_adventurer_ids"]

    def test_04_replay_last_blocked_when_over_cap(self, db):
        h, gid, _ = _fresh_user(db)
        _force_over_cap(db, gid)
        r = requests.post(f"{BASE_URL}/api/expeditions/replay-last", headers=h, timeout=15)
        # replay-last with over-cap → 423 BEFORE any business logic
        assert r.status_code == 423, r.text
        assert r.json()["detail"]["code"] == "roster_over_capacity"

    def test_05_raid_start_blocked_when_over_cap(self, db):
        h, gid, _ = _fresh_user(db)
        _force_over_cap(db, gid)
        # Even without a valid payload the over-cap guard fires first
        r = requests.post(
            f"{BASE_URL}/api/raids/start",
            json={"dungeon_id": "fake", "parties": []}, headers=h, timeout=15,
        )
        # raid.start.t1 lock OR over-cap — either way must NOT be 200.
        assert r.status_code in (403, 423), r.text

    def test_06_squad_create_blocked_when_payload_has_retired(self, db):
        h, gid, _ = _fresh_user(db)
        _set_dormitory_cap(db, gid, cap=20)
        ids = _make_starter_advs(db, gid, 4)
        db.adventurers.update_one(
            {"id": ids[0]}, {"$set": {"is_retired": True, "is_available": False}},
        )
        r = requests.post(
            f"{BASE_URL}/api/squads",
            json={
                "name": "test squad",
                "squad_type": "dungeon_3",
                "adventurer_ids": ids[:3],
            },
            headers=h, timeout=15,
        )
        assert r.status_code == 423, r.text
        body = r.json()["detail"]
        assert body["code"] == "adventurers.retired_in_set"

    def test_07_squad_update_blocked_when_payload_has_retired(self, db):
        h, gid, _ = _fresh_user(db)
        _set_dormitory_cap(db, gid, cap=20)
        ids = _make_starter_advs(db, gid, 5)
        # Create valid squad first
        r1 = requests.post(
            f"{BASE_URL}/api/squads",
            json={"name": "valid", "squad_type": "dungeon_3",
                  "adventurer_ids": ids[:3]},
            headers=h, timeout=15,
        )
        assert r1.status_code == 201, r1.text
        sid = r1.json()["squad_id"]
        # Retire one member then try to PATCH with new selection including it
        db.adventurers.update_one(
            {"id": ids[3]}, {"$set": {"is_retired": True, "is_available": False}},
        )
        r2 = requests.patch(
            f"{BASE_URL}/api/squads/{sid}",
            json={"adventurer_ids": [ids[1], ids[2], ids[3]]},
            headers=h, timeout=15,
        )
        assert r2.status_code == 423, r2.text
        assert r2.json()["detail"]["code"] == "adventurers.retired_in_set"

    def test_08_equip_blocked_when_target_retired(self, db):
        h, gid, _ = _fresh_user(db)
        ids = _make_starter_advs(db, gid, 1)
        adv_id = ids[0]
        db.adventurers.update_one(
            {"id": adv_id}, {"$set": {"is_retired": True, "is_available": False}},
        )
        # Pick any equippable item from seed
        inv = requests.get(f"{BASE_URL}/api/inventory", headers=h, timeout=15)
        items = (inv.json() if inv.status_code == 200 else {}).get("items", [])
        if not items:
            # No inventory items — skip
            pytest.skip("no inventory items available in fresh guild")
        item_id = items[0]["item_id"]
        r = requests.post(
            f"{BASE_URL}/api/adventurers/{adv_id}/equip",
            json={"item_id": item_id, "slot": "weapon"},
            headers=h, timeout=15,
        )
        assert r.status_code == 423, r.text
        assert r.json()["detail"]["code"] == "equip.target_retired"

    def test_09_get_endpoints_NOT_blocked_when_over_cap(self, db):
        h, gid, _ = _fresh_user(db)
        _force_over_cap(db, gid)
        # All GETs must still succeed when over-cap
        assert requests.get(f"{BASE_URL}/api/guilds/me", headers=h, timeout=15).status_code == 200
        assert requests.get(f"{BASE_URL}/api/adventurers", headers=h, timeout=15).status_code == 200
        assert requests.get(f"{BASE_URL}/api/territory", headers=h, timeout=15).status_code == 200
        assert requests.get(f"{BASE_URL}/api/squads", headers=h, timeout=15).status_code == 200
        assert requests.get(f"{BASE_URL}/api/expeditions", headers=h, timeout=15).status_code == 200

    def test_10_territory_upgrade_NOT_blocked_when_over_cap(self, db):
        """Escape valve: player must still be able to upgrade dormitories."""
        h, gid, _ = _fresh_user(db)
        _force_over_cap(db, gid)
        # Try the upgrade — it MUST go past the guard. Whether the upgrade
        # itself succeeds depends on gold/materials; what we test is that
        # the response code is NOT 423 `roster_over_capacity`.
        r = requests.post(
            f"{BASE_URL}/api/territory/upgrade",
            json={"structure_slug": "dormitories"},
            headers=h, timeout=15,
        )
        if r.status_code == 423:
            assert (r.json().get("detail") or {}).get("code") != "roster_over_capacity"

    def test_11_retire_NOT_blocked_when_over_cap(self, db):
        """Escape valve: player must still be able to retire to come back."""
        h, gid, _ = _fresh_user(db)
        ids = _force_over_cap(db, gid)
        r = _retire_via_api(h, ids[0])
        assert r.status_code == 200, r.text
        # Verify retired_by="user" was persisted
        doc = db.adventurers.find_one({"id": ids[0]}, {"_id": 0, "retired_by": 1})
        assert doc.get("retired_by") == "user"

    def test_12_squad_load_filters_retired_silently(self, db):
        h, gid, _ = _fresh_user(db)
        _set_dormitory_cap(db, gid, cap=20)
        ids = _make_starter_advs(db, gid, 4)
        r1 = requests.post(
            f"{BASE_URL}/api/squads",
            json={"name": "mixed", "squad_type": "dungeon_3",
                  "adventurer_ids": ids[:3]},
            headers=h, timeout=15,
        )
        assert r1.status_code == 201, r1.text
        sid = r1.json()["squad_id"]
        # Retire one member directly in DB (bypasses the squad-active guard)
        db.adventurers.update_one(
            {"id": ids[0]}, {"$set": {"is_retired": True, "is_available": False}},
        )
        # Now read the squad — must NOT 500. The retired member ends up in
        # `missing_adventurer_ids` (because the public projection joins via
        # the live adventurer index which filters `is_available=True`).
        r2 = requests.get(f"{BASE_URL}/api/squads/{sid}", headers=h, timeout=15)
        assert r2.status_code == 200, r2.text
        squad_pub = r2.json()
        # adventurer_ids still includes the retired id (stable history)
        assert ids[0] in (squad_pub.get("adventurer_ids") or [])
        # but missing_adventurer_ids surfaces it, and member_count drops to 2
        assert ids[0] in (squad_pub.get("missing_adventurer_ids") or [])
        assert squad_pub.get("member_count") == 2

    def test_13_retired_by_field_in_adventurer_public(self, db):
        h, gid, _ = _fresh_user(db)
        ids = _make_starter_advs(db, gid, 1)
        _retire_via_api(h, ids[0])
        # The roster GET should expose `retired_by: "user"`
        r = requests.get(f"{BASE_URL}/api/adventurers?include_retired=true",
                         headers=h, timeout=15)
        assert r.status_code == 200, r.text
        advs = r.json().get("adventurers") or r.json()
        found = [a for a in advs if a["id"] == ids[0]]
        assert found, f"retired adventurer not returned: {r.json()}"
        assert found[0].get("retired_by") == "user"
        assert found[0].get("is_retired") is True

    def test_14_legacy_retired_advs_default_to_none_retired_by(self, db):
        h, gid, _ = _fresh_user(db)
        ids = _make_starter_advs(db, gid, 1)
        # Set is_retired=True directly WITHOUT going through the API.
        # This simulates a legacy doc created before Wave 1.5.
        db.adventurers.update_one(
            {"id": ids[0]},
            {"$set": {"is_retired": True, "is_available": False,
                      "retired_at": "2025-01-01T00:00:00+00:00"}},
        )
        r = requests.get(f"{BASE_URL}/api/adventurers?include_retired=true",
                         headers=h, timeout=15)
        advs = r.json().get("adventurers") or r.json()
        found = [a for a in advs if a["id"] == ids[0]]
        assert found, "legacy retired adv missing from roster"
        assert found[0].get("retired_by") is None
        assert found[0].get("is_retired") is True

    def test_15_audit_event_written_on_over_cap_block(self, db):
        """Best-effort analytics — when a flow is blocked, an audit row is
        appended so we can attribute the friction point in dashboards."""
        h, gid, _ = _fresh_user(db)
        _force_over_cap(db, gid)
        before = db.audit_log.count_documents({
            "event_type": "roster_over_capacity_blocked",
            "actor_guild_id": gid,
        })
        # Trigger any of the gated flows
        r = requests.post(f"{BASE_URL}/api/expeditions/replay-last",
                          headers=h, timeout=15)
        assert r.status_code == 423
        after = db.audit_log.count_documents({
            "event_type": "roster_over_capacity_blocked",
            "actor_guild_id": gid,
        })
        assert after >= before + 1, "audit row not written on over-cap block"
