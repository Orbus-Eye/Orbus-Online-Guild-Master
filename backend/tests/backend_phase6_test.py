"""Orbus Online: Guild Master — Phase 6 backend tests (Equip + UI password reset flow).

Covers:
- Equip / unequip happy path + error cases
- Available quantity coherence (equipped count)
- Compound unique (adventurer_id, slot)
- Locked adventurer (in expedition) — no equipment changes
- Equipment snapshot frozen on expedition_members
- team_power increases when adventurer is equipped
- Monetization invariant preserved on Phase-6 seed
- Password reset request/confirm (already covered in Phase 5; here we re-assert
  no-regression after Phase 6 changes)
"""
import os
import uuid
import time
import hashlib
import pytest
import requests
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") if os.environ.get("REACT_APP_BACKEND_URL") else None
if BASE_URL is None:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                break

API = f"{BASE_URL}/api"


def _load_dbname():
    if "DB_NAME" in os.environ:
        return os.environ["DB_NAME"]
    with open("/app/backend/.env") as f:
        for line in f:
            if line.startswith("DB_NAME="):
                return line.split("=", 1)[1].strip().strip('"')
    return "test_database"


MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = _load_dbname()


def _mongo():
    return MongoClient(MONGO_URL)[DB_NAME]


def _rand_email(prefix="p6"):
    return f"{prefix}_{uuid.uuid4().hex[:10]}@orbus.test"


def _register_and_guild():
    email = _rand_email()
    r = requests.post(
        f"{API}/auth/register",
        json={"email": email, "username": "u_" + uuid.uuid4().hex[:6], "password": "pass1234"},
        timeout=15,
    )
    assert r.status_code == 201, r.text
    tok = r.json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    gg = requests.post(
        f"{API}/guilds",
        json={"name": "G_" + uuid.uuid4().hex[:6], "description": ""},
        headers=h, timeout=15,
    )
    assert gg.status_code == 201, gg.text
    guild = gg.json()["guild"]
    return {"headers": h, "guild": guild, "email": email}


def _recruit_n(headers, n=1):
    candidates = requests.get(f"{API}/recruitment/candidates", headers=headers, timeout=15).json()["candidates"]
    advs = []
    for i in range(n):
        if i >= len(candidates):
            # need a fresh batch
            candidates = requests.get(f"{API}/recruitment/candidates", headers=headers, timeout=15).json()["candidates"]
        r = requests.post(
            f"{API}/recruitment/recruit",
            json={"candidate_id": candidates[i]["candidate_id"]},
            headers=headers, timeout=15,
        )
        assert r.status_code == 201, r.text
        advs.append(r.json()["adventurer"])
    return advs


def _grant_item(guild_id, item_id, quantity=1):
    """Test helper: insert/upsert an inventory_items row directly via Mongo."""
    db = _mongo()
    db.inventory_items.update_one(
        {"guild_id": guild_id, "item_id": item_id},
        {
            "$inc": {"quantity": quantity},
            "$setOnInsert": {
                "id": str(uuid.uuid4()),
                "guild_id": guild_id,
                "item_id": item_id,
                "acquired_at": datetime.now(timezone.utc).isoformat(),
            },
        },
        upsert=True,
    )


def _items_by_type():
    rows = requests.get(f"{API}/items", timeout=15).json()["items"]
    # Filter to canonical seed items + Phase 7 expansions so tests are not
    # affected by stale admin-test artifacts (cosmetics with zero bonuses).
    seed_slugs = {
        "rusted-sword", "goblin-dagger", "cracked-staff",
        "novice-charm", "torn-leather-vest",
        "cryptbone-blade", "spiritglass-staff", "gravewarden-mail", "relic-signet",
        "drakefang-greatsword", "embermind-focus", "dragonscale-vest", "hoardlords-seal",
    }
    rows = [i for i in rows if i["slug"] in seed_slugs]
    return {
        "weapon": [i for i in rows if i["item_type"] == "weapon"],
        "armor": [i for i in rows if i["item_type"] == "armor"],
        "accessory": [i for i in rows if i["item_type"] == "accessory"],
    }


# ─── A. Equip basic flow ─────────────────────────────────────────────────────
class TestEquipBasic:
    def test_equip_owned_item_success_201(self):
        u = _register_and_guild()
        adv = _recruit_n(u["headers"], 1)[0]
        items = _items_by_type()
        weapon = items["weapon"][0]
        _grant_item(u["guild"]["id"], weapon["id"], 1)

        r = requests.post(
            f"{API}/adventurers/{adv['id']}/equip",
            json={"item_id": weapon["id"], "slot": "weapon"},
            headers=u["headers"], timeout=15,
        )
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["slots"]["weapon"] is not None
        assert body["slots"]["weapon"]["item"]["id"] == weapon["id"]
        assert body["equipment_power"] >= 0
        assert body["total_power"] == body["base_power"] + body["equipment_power"]

    def test_equip_item_not_in_inventory_404(self):
        u = _register_and_guild()
        adv = _recruit_n(u["headers"], 1)[0]
        items = _items_by_type()
        weapon = items["weapon"][0]
        # do NOT grant the item
        r = requests.post(
            f"{API}/adventurers/{adv['id']}/equip",
            json={"item_id": weapon["id"], "slot": "weapon"},
            headers=u["headers"], timeout=15,
        )
        assert r.status_code == 404
        assert "inventory" in r.json()["detail"].lower()

    def test_equip_other_guild_adventurer_404(self):
        uA = _register_and_guild()
        uB = _register_and_guild()
        advB = _recruit_n(uB["headers"], 1)[0]
        items = _items_by_type()
        weapon = items["weapon"][0]
        _grant_item(uA["guild"]["id"], weapon["id"], 1)
        # uA tries to equip uB's adventurer
        r = requests.post(
            f"{API}/adventurers/{advB['id']}/equip",
            json={"item_id": weapon["id"], "slot": "weapon"},
            headers=uA["headers"], timeout=15,
        )
        assert r.status_code == 404

    def test_equip_wrong_slot_type_400(self):
        u = _register_and_guild()
        adv = _recruit_n(u["headers"], 1)[0]
        items = _items_by_type()
        weapon = items["weapon"][0]
        _grant_item(u["guild"]["id"], weapon["id"], 1)
        r = requests.post(
            f"{API}/adventurers/{adv['id']}/equip",
            json={"item_id": weapon["id"], "slot": "armor"},
            headers=u["headers"], timeout=15,
        )
        assert r.status_code == 400
        assert "cannot be equipped" in r.json()["detail"].lower()

    def test_equip_slot_already_occupied_400(self):
        u = _register_and_guild()
        adv = _recruit_n(u["headers"], 1)[0]
        items = _items_by_type()
        w1 = items["weapon"][0]
        w2 = items["weapon"][1]
        _grant_item(u["guild"]["id"], w1["id"], 1)
        _grant_item(u["guild"]["id"], w2["id"], 1)
        # equip first weapon
        r1 = requests.post(
            f"{API}/adventurers/{adv['id']}/equip",
            json={"item_id": w1["id"], "slot": "weapon"},
            headers=u["headers"], timeout=15,
        )
        assert r1.status_code == 201
        # try a second weapon in same slot → 400
        r2 = requests.post(
            f"{API}/adventurers/{adv['id']}/equip",
            json={"item_id": w2["id"], "slot": "weapon"},
            headers=u["headers"], timeout=15,
        )
        assert r2.status_code == 400
        assert "slot" in r2.json()["detail"].lower()

    def test_unequip_returns_available_quantity(self):
        u = _register_and_guild()
        adv = _recruit_n(u["headers"], 1)[0]
        items = _items_by_type()
        w = items["weapon"][0]
        _grant_item(u["guild"]["id"], w["id"], 1)
        requests.post(
            f"{API}/adventurers/{adv['id']}/equip",
            json={"item_id": w["id"], "slot": "weapon"},
            headers=u["headers"], timeout=15,
        )
        inv1 = requests.get(f"{API}/inventory", headers=u["headers"], timeout=15).json()["inventory"]
        entry = next(e for e in inv1 if e["item_id"] == w["id"])
        assert entry["total_quantity"] == 1
        assert entry["equipped_quantity"] == 1
        assert entry["available_quantity"] == 0

        ru = requests.post(
            f"{API}/adventurers/{adv['id']}/unequip",
            json={"slot": "weapon"},
            headers=u["headers"], timeout=15,
        )
        assert ru.status_code == 200
        inv2 = requests.get(f"{API}/inventory", headers=u["headers"], timeout=15).json()["inventory"]
        entry2 = next(e for e in inv2 if e["item_id"] == w["id"])
        assert entry2["equipped_quantity"] == 0
        assert entry2["available_quantity"] == 1

    def test_equip_unequip_cycle_no_drift(self):
        u = _register_and_guild()
        adv = _recruit_n(u["headers"], 1)[0]
        items = _items_by_type()
        w = items["weapon"][0]
        _grant_item(u["guild"]["id"], w["id"], 1)
        # Cycle 3 times
        for _ in range(3):
            r = requests.post(
                f"{API}/adventurers/{adv['id']}/equip",
                json={"item_id": w["id"], "slot": "weapon"},
                headers=u["headers"], timeout=15,
            )
            assert r.status_code == 201
            r = requests.post(
                f"{API}/adventurers/{adv['id']}/unequip",
                json={"slot": "weapon"},
                headers=u["headers"], timeout=15,
            )
            assert r.status_code == 200
        inv = requests.get(f"{API}/inventory", headers=u["headers"], timeout=15).json()["inventory"]
        entry = next(e for e in inv if e["item_id"] == w["id"])
        assert entry["total_quantity"] == 1
        assert entry["equipped_quantity"] == 0
        assert entry["available_quantity"] == 1


# ─── B. Lock adventurer during expedition ────────────────────────────────────
class TestExpeditionLocksEquipment:
    def _start_expedition(self, u, advs):
        dungeon = requests.get(f"{API}/dungeons", headers=u["headers"], timeout=15).json()["dungeons"][0]
        ids = [a["id"] for a in advs[:dungeon["required_team_size"]]]
        r = requests.post(
            f"{API}/expeditions",
            json={"dungeon_id": dungeon["id"], "adventurer_ids": ids},
            headers=u["headers"], timeout=15,
        )
        assert r.status_code == 201, r.text
        return r.json()

    def test_cannot_equip_locked_adventurer(self):
        u = _register_and_guild()
        advs = _recruit_n(u["headers"], 3)
        items = _items_by_type()
        w = items["weapon"][0]
        _grant_item(u["guild"]["id"], w["id"], 1)
        self._start_expedition(u, advs)
        r = requests.post(
            f"{API}/adventurers/{advs[0]['id']}/equip",
            json={"item_id": w["id"], "slot": "weapon"},
            headers=u["headers"], timeout=15,
        )
        assert r.status_code == 400
        assert "expedition" in r.json()["detail"].lower()

    def test_cannot_unequip_locked_adventurer(self):
        u = _register_and_guild()
        advs = _recruit_n(u["headers"], 3)
        items = _items_by_type()
        w = items["weapon"][0]
        _grant_item(u["guild"]["id"], w["id"], 1)
        # equip BEFORE starting expedition
        requests.post(
            f"{API}/adventurers/{advs[0]['id']}/equip",
            json={"item_id": w["id"], "slot": "weapon"},
            headers=u["headers"], timeout=15,
        )
        self._start_expedition(u, advs)
        ru = requests.post(
            f"{API}/adventurers/{advs[0]['id']}/unequip",
            json={"slot": "weapon"},
            headers=u["headers"], timeout=15,
        )
        assert ru.status_code == 400
        assert "expedition" in ru.json()["detail"].lower()


# ─── C. Equipment snapshot + team_power influence ────────────────────────────
class TestExpeditionEquipmentImpact:
    def test_equipment_snapshot_and_team_power(self):
        u = _register_and_guild()
        advs = _recruit_n(u["headers"], 3)
        items = _items_by_type()
        weapon = items["weapon"][0]

        # Compute baseline team_power WITHOUT equipment
        # (start expedition immediately with no equip; we'll then unlock by
        # waiting for completion, but for the assertion we only need team_power
        # at start.)
        dungeon = requests.get(f"{API}/dungeons", headers=u["headers"], timeout=15).json()["dungeons"][0]
        ids = [a["id"] for a in advs[:dungeon["required_team_size"]]]
        r = requests.post(
            f"{API}/expeditions",
            json={"dungeon_id": dungeon["id"], "adventurer_ids": ids},
            headers=u["headers"], timeout=15,
        )
        assert r.status_code == 201
        baseline_tp = r.json()["expedition"]["team_power"]
        members = r.json()["members"]
        # Snapshot should be empty list, power 0, total=base
        for m in members:
            assert m["equipment_snapshot"] == []
            assert m["equipment_power_snapshot"] == 0

        # Wait for completion (60s) then equip + 2nd expedition
        # To avoid 60s wait in tests, instead just verify SNAPSHOT for the
        # equipped case via a 2nd setup with equipment, equipped BEFORE
        # starting expedition.
        u2 = _register_and_guild()
        advs2 = _recruit_n(u2["headers"], 3)
        eq_power_sum = 0
        for i, adv in enumerate(advs2):
            _grant_item(u2["guild"]["id"], weapon["id"], 1)
            requests.post(
                f"{API}/adventurers/{adv['id']}/equip",
                json={"item_id": weapon["id"], "slot": "weapon"},
                headers=u2["headers"], timeout=15,
            )
            eq_power_sum += (
                int(weapon["strength_bonus"])
                + int(weapon["agility_bonus"])
                + int(weapon["intellect_bonus"])
                + int(weapon["endurance_bonus"])
                + int(weapon["faith_bonus"])
                + int(weapon["power_score"])
            )

        ids2 = [a["id"] for a in advs2[:dungeon["required_team_size"]]]
        r2 = requests.post(
            f"{API}/expeditions",
            json={"dungeon_id": dungeon["id"], "adventurer_ids": ids2},
            headers=u2["headers"], timeout=15,
        )
        assert r2.status_code == 201
        equipped_tp = r2.json()["expedition"]["team_power"]
        equipped_members = r2.json()["members"]

        # Snapshot present and matches item
        for m in equipped_members:
            assert len(m["equipment_snapshot"]) == 1
            snap = m["equipment_snapshot"][0]
            assert snap["item_id"] == weapon["id"]
            assert snap["item_name"] == weapon["name"]
            assert m["equipment_power_snapshot"] > 0
            assert m["total_power_snapshot"] >= m["equipment_power_snapshot"]

        # Equipped team_power should be exactly baseline + eq_power_sum
        # NOTE baseline is on a DIFFERENT random guild, so we cannot directly
        # compare; instead, check that team_power matches the formula on this
        # team: sum(total_power_snapshot of members) + role bonuses.
        adv_get = requests.get(f"{API}/adventurers", headers=u2["headers"], timeout=15).json()["adventurers"]
        team = [a for a in adv_get if a["id"] in ids2]
        expected_base_sum = sum(
            a["strength"] + a["agility"] + a["intellect"]
            + a["endurance"] + a["faith"] + a["level"] * 2
            for a in team
        )
        roles = {a["class_role"] for a in team}
        bonus = 0
        if "Tank" in roles: bonus += 5
        if "Healer" in roles: bonus += 5
        if "DPS" in roles: bonus += 5
        if {"Tank", "Healer", "DPS"}.issubset(roles): bonus += 10
        expected_team_power = expected_base_sum + eq_power_sum + bonus
        assert equipped_tp == expected_team_power, (
            f"team_power={equipped_tp} expected={expected_team_power} "
            f"(base={expected_base_sum} eq={eq_power_sum} bonus={bonus})"
        )

    def test_snapshot_is_immutable_after_start(self):
        """Even if the underlying item is admin-toggled inactive after start,
        the expedition_members snapshot must keep the frozen data.
        """
        u = _register_and_guild()
        adv = _recruit_n(u["headers"], 3)
        items = _items_by_type()
        weapon = items["weapon"][0]
        _grant_item(u["guild"]["id"], weapon["id"], 1)
        # equip on first adv
        requests.post(
            f"{API}/adventurers/{adv[0]['id']}/equip",
            json={"item_id": weapon["id"], "slot": "weapon"},
            headers=u["headers"], timeout=15,
        )
        dungeon = requests.get(f"{API}/dungeons", headers=u["headers"], timeout=15).json()["dungeons"][0]
        ids = [a["id"] for a in adv[:dungeon["required_team_size"]]]
        rs = requests.post(
            f"{API}/expeditions",
            json={"dungeon_id": dungeon["id"], "adventurer_ids": ids},
            headers=u["headers"], timeout=15,
        ).json()
        exp_id = rs["expedition"]["id"]

        # Tamper with the live item directly in DB (simulate admin toggle)
        _mongo().items.update_one({"id": weapon["id"]}, {"$set": {"is_active": False}})
        try:
            # Re-fetch expedition detail
            det = requests.get(f"{API}/expeditions/{exp_id}", headers=u["headers"], timeout=15).json()
            members = det["members"]
            equipped_member = next(m for m in members if m["adventurer_id"] == adv[0]["id"])
            assert len(equipped_member["equipment_snapshot"]) == 1
            assert equipped_member["equipment_snapshot"][0]["item_id"] == weapon["id"]
            assert equipped_member["equipment_power_snapshot"] > 0
        finally:
            # Restore
            _mongo().items.update_one({"id": weapon["id"]}, {"$set": {"is_active": True}})


# ─── D. Monetization invariant + seed update ─────────────────────────────────
class TestMonetizationSeed:
    def test_all_seed_items_not_real_money(self):
        rows = requests.get(f"{API}/items", timeout=15).json()["items"]
        # Phase-6 reseed: the 5 canonical seed items must remain not real-money sellable
        seed_slugs = {"rusted-sword", "goblin-dagger", "cracked-staff",
                      "novice-charm", "torn-leather-vest"}
        seed_items = [it for it in rows if it["slug"] in seed_slugs]
        assert len(seed_items) == 5, f"expected 5 seed items, got {len(seed_items)}"
        for it in seed_items:
            assert it["can_be_sold_for_real_money"] is False, (
                f"seed item {it['slug']} has real-money flag set"
            )

    def test_admin_create_weapon_realmoney_400(self):
        # Login as tester (admin in non-prod)
        lg = requests.post(
            f"{API}/auth/login",
            json={"email": "tester@orbus.test", "password": "password123"},
            timeout=15,
        )
        assert lg.status_code == 200, lg.text
        tok = lg.json()["access_token"]
        h = {"Authorization": f"Bearer {tok}"}
        slug = "p6-bad-weapon-" + uuid.uuid4().hex[:6]
        r = requests.post(
            f"{API}/admin/items",
            json={
                "name": "P6 Bad Weapon",
                "slug": slug,
                "item_type": "weapon",
                "rarity": "Rare",
                "power_score": 10,
                "can_be_sold_for_real_money": True,
                "is_cosmetic": False,
                "affects_combat": True,
            },
            headers=h, timeout=15,
        )
        assert r.status_code == 400, r.text


# ─── E. Password reset full flow (UI-driven, but server-only test here) ──────
class TestPasswordResetEndToEnd:
    def test_request_then_confirm_then_login_with_new_pw(self):
        # Register a user
        email = _rand_email("pr6")
        r = requests.post(
            f"{API}/auth/register",
            json={"email": email, "username": "pr6u", "password": "pass1234"},
            timeout=15,
        )
        assert r.status_code == 201
        # Trigger request
        rr = requests.post(
            f"{API}/auth/password-reset/request",
            json={"email": email}, timeout=15,
        )
        assert rr.status_code == 200
        # Mongo-insert a synthetic token (the test bypasses console-log parsing)
        plain = "p6tok_" + uuid.uuid4().hex
        token_hash = hashlib.sha256(plain.encode()).hexdigest()
        now = datetime.now(timezone.utc)
        user = _mongo().users.find_one({"email": email})
        _mongo().password_reset_tokens.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "token_hash": token_hash,
            "created_at": now,
            "expires_at": now + timedelta(minutes=60),
            "used": False,
        })
        # Confirm
        cf = requests.post(
            f"{API}/auth/password-reset/confirm",
            json={"token": plain, "new_password": "freshpass99"},
            timeout=15,
        )
        assert cf.status_code == 200, cf.text
        # Login with new password
        lg = requests.post(
            f"{API}/auth/login",
            json={"email": email, "password": "freshpass99"},
            timeout=15,
        )
        assert lg.status_code == 200
