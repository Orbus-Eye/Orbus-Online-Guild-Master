"""Orbus Online — Phase 3 backend tests (dungeons, items, expeditions, inventory, level-up, isolation)."""
import os
import time
import uuid
import pytest
import requests
from concurrent.futures import ThreadPoolExecutor

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip()
                break
BASE_URL = BASE_URL.rstrip("/")
API = f"{BASE_URL}/api"

EXPECTED_ITEM_SLUGS = {"rusted-sword", "goblin-dagger", "cracked-staff", "novice-charm", "torn-leather-vest"}


# ─── helpers ─────────────────────────────────────────────────────────────────
def _rand_email():
    return f"p3_{uuid.uuid4().hex[:10]}@orbus.test"


def _register():
    payload = {"email": _rand_email(), "username": "p3_" + uuid.uuid4().hex[:6], "password": "password123"}
    r = requests.post(f"{API}/auth/register", json=payload, timeout=15)
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def _create_guild(token):
    h = {"Authorization": f"Bearer {token}"}
    r = requests.post(f"{API}/guilds", json={"name": "TEST_P3_" + uuid.uuid4().hex[:6]}, headers=h, timeout=15)
    assert r.status_code == 201, r.text
    return r.json()["guild"]


def _recruit_n(token, n=3):
    h = {"Authorization": f"Bearer {token}"}
    ids = []
    while len(ids) < n:
        cands = requests.get(f"{API}/recruitment/candidates", headers=h, timeout=15).json()["candidates"]
        for c in cands:
            if len(ids) >= n:
                break
            r = requests.post(f"{API}/recruitment/recruit",
                              json={"candidate_id": c["candidate_id"]}, headers=h, timeout=15)
            if r.status_code == 201:
                ids.append(r.json()["adventurer"]["id"])
            elif r.status_code == 400:
                return ids  # out of gold
    return ids


def _new_user_with_team():
    token = _register()
    guild = _create_guild(token)
    h = {"Authorization": f"Bearer {token}"}
    ids = _recruit_n(token, 3)
    assert len(ids) == 3, f"could not recruit 3, got {len(ids)}"
    return {"token": token, "guild": guild, "headers": h, "adv_ids": ids}


def _get_dungeon():
    r = requests.get(f"{API}/dungeons", timeout=15)
    assert r.status_code == 200, r.text
    dungeons = r.json()["dungeons"]
    for d in dungeons:
        if d["slug"] == "goblin-warrens":
            return d
    pytest.fail("goblin-warrens not seeded")


# ─── module-level fixtures ───────────────────────────────────────────────────
@pytest.fixture(scope="module")
def dungeon():
    return _get_dungeon()


@pytest.fixture(scope="module")
def user_A(dungeon):
    return _new_user_with_team()


# ─── Catalog tests ───────────────────────────────────────────────────────────
class TestDungeonsAndItems:
    def test_dungeons_lists_goblin_warrens(self, dungeon):
        assert dungeon["slug"] == "goblin-warrens"
        assert dungeon["required_team_size"] == 3
        assert dungeon["base_duration_seconds"] == 60
        assert dungeon["recommended_power"] == 45
        assert dungeon["base_gold_reward"] == 35
        assert dungeon["base_xp_reward"] == 25
        assert dungeon["is_active"] is True

    def test_items_seeded_no_realmoney(self):
        r = requests.get(f"{API}/items", timeout=15)
        assert r.status_code == 200
        items = r.json()["items"]
        slugs = {i["slug"] for i in items}
        assert EXPECTED_ITEM_SLUGS.issubset(slugs), f"missing: {EXPECTED_ITEM_SLUGS - slugs}"
        for it in items:
            if it["slug"] in EXPECTED_ITEM_SLUGS:
                assert it["can_be_sold_for_real_money"] is False


# ─── Validation tests on POST /expeditions ──────────────────────────────────
class TestExpeditionValidation:
    def test_wrong_team_size_2(self, user_A, dungeon):
        r = requests.post(f"{API}/expeditions",
                          json={"dungeon_id": dungeon["id"], "adventurer_ids": user_A["adv_ids"][:2]},
                          headers=user_A["headers"], timeout=15)
        assert r.status_code == 400, r.text
        assert "3" in r.json()["detail"]

    def test_wrong_team_size_4(self, dungeon):
        u = _new_user_with_team()
        # need 4: recruit one more
        more = _recruit_n(u["token"], 1)
        if not more:
            pytest.skip("could not recruit 4th adventurer")
        ids4 = u["adv_ids"] + more
        r = requests.post(f"{API}/expeditions",
                          json={"dungeon_id": dungeon["id"], "adventurer_ids": ids4},
                          headers=u["headers"], timeout=15)
        assert r.status_code == 400

    def test_duplicate_adventurer(self, user_A, dungeon):
        ids = [user_A["adv_ids"][0], user_A["adv_ids"][0], user_A["adv_ids"][1]]
        r = requests.post(f"{API}/expeditions",
                          json={"dungeon_id": dungeon["id"], "adventurer_ids": ids},
                          headers=user_A["headers"], timeout=15)
        assert r.status_code == 400
        assert "duplicate" in r.json()["detail"].lower()

    def test_cross_guild_adventurer_404(self, dungeon):
        uA = _new_user_with_team()
        uB = _new_user_with_team()
        ids = [uA["adv_ids"][0]] + uB["adv_ids"][:2]
        r = requests.post(f"{API}/expeditions",
                          json={"dungeon_id": dungeon["id"], "adventurer_ids": ids},
                          headers=uB["headers"], timeout=15)
        assert r.status_code == 404, r.text
        assert "not found" in r.json()["detail"].lower()


# ─── Full lifecycle: happy path + idempotency ───────────────────────────────
class TestExpeditionLifecycle:
    def test_full_lifecycle_and_idempotency(self, dungeon):
        u = _new_user_with_team()
        h = u["headers"]

        # Pre-state
        guild0 = requests.get(f"{API}/guilds/me", headers=h, timeout=15).json()["guild"]
        gold0 = guild0["gold"]
        advs0 = requests.get(f"{API}/adventurers", headers=h, timeout=15).json()["adventurers"]
        xp_by_id = {a["id"]: a["experience"] for a in advs0}

        # Compute expected team_power
        members = [a for a in advs0 if a["id"] in u["adv_ids"]]
        expected_power = sum(a["strength"]+a["agility"]+a["intellect"]+a["endurance"]+a["faith"]+a["level"]*2
                             for a in members)
        roles = {a["class_role"] for a in members}
        if "Tank" in roles: expected_power += 5
        if "Healer" in roles: expected_power += 5
        if "DPS" in roles: expected_power += 5
        if {"Tank","Healer","DPS"}.issubset(roles): expected_power += 10
        expected_sc = max(10, min(95, 50 + expected_power - 45))

        # Start expedition
        r = requests.post(f"{API}/expeditions",
                          json={"dungeon_id": dungeon["id"], "adventurer_ids": u["adv_ids"]},
                          headers=h, timeout=15)
        assert r.status_code == 201, r.text
        exp = r.json()["expedition"]
        exp_id = exp["id"]
        assert exp["team_power"] == expected_power, f"power {exp['team_power']} != {expected_power}"
        assert exp["success_chance"] == expected_sc
        assert exp["status"] == "in_progress"

        # Adventurers locked
        advs1 = requests.get(f"{API}/adventurers", headers=h, timeout=15).json()["adventurers"]
        locked = {a["id"]: a["is_available"] for a in advs1 if a["id"] in u["adv_ids"]}
        assert all(v is False for v in locked.values()), locked

        # Same team cannot be dispatched again
        r2 = requests.post(f"{API}/expeditions",
                           json={"dungeon_id": dungeon["id"], "adventurer_ids": u["adv_ids"]},
                           headers=h, timeout=15)
        assert r2.status_code == 400

        # Active expedition count + last_expedition_id
        guild1 = requests.get(f"{API}/guilds/me", headers=h, timeout=15).json()["guild"]
        assert guild1["active_expedition_count"] >= 1
        assert guild1["last_expedition_id"] == exp_id

        # During the 60s, status stays in_progress
        time.sleep(2)
        midlist = requests.get(f"{API}/expeditions", headers=h, timeout=15).json()["expeditions"]
        midexp = next(e for e in midlist if e["id"] == exp_id)
        assert midexp["status"] == "in_progress"
        assert "seconds_remaining" in midexp
        assert midexp["seconds_remaining"] >= 0

        # Wait until complete (60s + buffer)
        time.sleep(62)

        # Trigger lazy sweep via /expeditions
        list1 = requests.get(f"{API}/expeditions", headers=h, timeout=15).json()["expeditions"]
        done = next(e for e in list1 if e["id"] == exp_id)
        assert done["status"] == "completed", done
        assert done["result_summary"] in {"Success", "Failed"}
        assert 1 <= done["final_score"] <= 100
        assert done["completed_at"]
        assert done["result_log"] and dungeon["name"] in done["result_log"]

        success = done["result_summary"] == "Success"

        # Check rewards
        guild_after = requests.get(f"{API}/guilds/me", headers=h, timeout=15).json()["guild"]
        gold_after = guild_after["gold"]

        if success:
            assert gold_after - gold0 == 35, f"expected +35 gold, got {gold_after - gold0}"
            assert done["gold_reward"] == 35
            assert done["xp_reward"] == 25
        else:
            assert gold_after - gold0 == 9, f"expected +9 gold on failure, got {gold_after - gold0}"
            assert done["gold_reward"] == 9
            assert done["xp_reward"] == 10
            assert done["loot_item_ids"] == []

        # Adventurers freed
        advs2 = requests.get(f"{API}/adventurers", headers=h, timeout=15).json()["adventurers"]
        for a in advs2:
            if a["id"] in u["adv_ids"]:
                assert a["is_available"] is True
                # XP gained (level may have advanced; check effective xp added)
                xp_gained = done["xp_reward"]
                # If level advanced, current xp = (prev_xp + xp_gained) - threshold
                # accept both possibilities
                prev = xp_by_id[a["id"]]
                expected_xp = prev + xp_gained
                # account for possible level up
                threshold = 100  # was level 1 → 100
                if expected_xp >= threshold:
                    assert a["level"] >= 2
                    assert a["experience"] == expected_xp - threshold * (a["level"] - 1)
                else:
                    assert a["experience"] == expected_xp

        # IDEMPOTENCY: second fetch should NOT change gold
        guild_after2 = requests.get(f"{API}/guilds/me", headers=h, timeout=15).json()["guild"]
        assert guild_after2["gold"] == gold_after, "Gold changed on second fetch — idempotency broken!"
        list2 = requests.get(f"{API}/expeditions", headers=h, timeout=15).json()["expeditions"]
        done2 = next(e for e in list2 if e["id"] == exp_id)
        assert done2["final_score"] == done["final_score"]

        # GET by id also idempotent
        detail = requests.get(f"{API}/expeditions/{exp_id}", headers=h, timeout=15).json()
        assert detail["expedition"]["status"] == "completed"
        assert len(detail["loot_items"]) == len(done["loot_item_ids"])

        # If loot dropped: inventory contains it
        if done["loot_item_ids"]:
            inv = requests.get(f"{API}/inventory", headers=h, timeout=15).json()["inventory"]
            inv_item_ids = {e["item_id"]: e["quantity"] for e in inv}
            for lid in done["loot_item_ids"]:
                assert lid in inv_item_ids
                assert inv_item_ids[lid] >= 1


# ─── Cross-guild isolation ──────────────────────────────────────────────────
class TestCrossGuildIsolation:
    def test_get_expedition_other_guild_404(self, dungeon):
        uA = _new_user_with_team()
        r = requests.post(f"{API}/expeditions",
                          json={"dungeon_id": dungeon["id"], "adventurer_ids": uA["adv_ids"]},
                          headers=uA["headers"], timeout=15)
        assert r.status_code == 201
        exp_id = r.json()["expedition"]["id"]

        uB = _new_user_with_team()
        rB = requests.get(f"{API}/expeditions/{exp_id}", headers=uB["headers"], timeout=15)
        assert rB.status_code == 404
        # also inventory should not leak
        invB = requests.get(f"{API}/inventory", headers=uB["headers"], timeout=15).json()["inventory"]
        # B's inventory should be empty initially
        assert isinstance(invB, list)


# ─── Inventory upsert (item validation + idempotency of unique index) ──────
class TestInventoryUpsert:
    def test_inventory_empty_for_new_user(self):
        u = _new_user_with_team()
        inv = requests.get(f"{API}/inventory", headers=u["headers"], timeout=15).json()["inventory"]
        assert inv == []


# ─── Item monetization validator (direct unit-style via helper) ─────────────
class TestItemMonetizationValidator:
    def test_validator_rejects_combat_with_realmoney(self):
        import sys
        sys.path.insert(0, "/app/backend")
        from server import validate_item_monetization
        from fastapi import HTTPException

        bad = {"can_be_sold_for_real_money": True, "is_cosmetic": False,
               "affects_combat": True, "affects_economy": False, "affects_ranking": False}
        with pytest.raises(HTTPException) as ei:
            validate_item_monetization(bad)
        assert ei.value.status_code == 400

        bad2 = {"can_be_sold_for_real_money": True, "is_cosmetic": True,
                "affects_combat": False, "affects_economy": True, "affects_ranking": False}
        with pytest.raises(HTTPException):
            validate_item_monetization(bad2)

        # Valid: pure cosmetic
        ok = {"can_be_sold_for_real_money": True, "is_cosmetic": True,
              "affects_combat": False, "affects_economy": False, "affects_ranking": False}
        validate_item_monetization(ok)  # no raise


# ─── Level-up loop test (multi-level) ───────────────────────────────────────
class TestLevelUpLoop:
    def test_resolve_levelup_multi_level(self):
        import sys
        sys.path.insert(0, "/app/backend")
        from server import _resolve_levelup
        adv = {"level": 1, "experience": 350, "class_name": "Mage",
               "strength": 2, "agility": 4, "intellect": 10, "endurance": 3, "faith": 3}
        # Level 1: threshold 100 (xp 350-100=250, lvl 2)
        # Level 2: threshold 200 (xp 250-200=50, lvl 3)
        updated = _resolve_levelup(dict(adv))
        assert updated["level"] == 3
        assert updated["experience"] == 50
        # Mage gains +intellect per level (2 levels gained → +2)
        assert updated["intellect"] == 12
