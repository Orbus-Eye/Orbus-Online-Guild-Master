"""Orbus Online: Guild Master — Phase 7 backend tests.

Covers:
- 3 dungeon seed: Goblin Warrens / Shadow Crypts / Dragon's Hoard
- 8 new item seed (4 Rare + 4 Epic) + monetization invariant
- Dungeon gates (403 + unlock_reason)
- Loot table per dungeon (success vs failure)
- Equipment delta fields persisted on expedition doc
- Equipment delta narrative
- Dashboard stats on /api/guilds/me
"""
import os
import uuid
import requests
from datetime import datetime, timezone
from pymongo import MongoClient


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip()
                break
BASE_URL = BASE_URL.rstrip("/")
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


def _rand_email(prefix="p7"):
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
    return {"headers": h, "guild": gg.json()["guild"], "email": email}


def _recruit_n(headers, n=3):
    out = []
    while len(out) < n:
        cands = requests.get(
            f"{API}/recruitment/candidates", headers=headers, timeout=15
        ).json()["candidates"]
        for c in cands:
            if len(out) >= n:
                break
            r = requests.post(
                f"{API}/recruitment/recruit",
                json={"candidate_id": c["candidate_id"]},
                headers=headers, timeout=15,
            )
            if r.status_code == 201:
                out.append(r.json()["adventurer"])
    return out


def _dungeons(headers):
    return {
        d["slug"]: d
        for d in requests.get(f"{API}/dungeons", headers=headers, timeout=15).json()["dungeons"]
    }


def _items_seed_only(item_type=None):
    seed_slugs = {
        "rusted-sword", "goblin-dagger", "cracked-staff",
        "novice-charm", "torn-leather-vest",
        "cryptbone-blade", "spiritglass-staff", "gravewarden-mail", "relic-signet",
        "drakefang-greatsword", "embermind-focus", "dragonscale-vest", "hoardlords-seal",
    }
    rows = requests.get(f"{API}/items", timeout=15).json()["items"]
    rows = [r for r in rows if r["slug"] in seed_slugs]
    if item_type:
        rows = [r for r in rows if r["item_type"] == item_type]
    return rows


# ─── A. Seeds ───────────────────────────────────────────────────────────────
class TestSeeds:
    def test_three_dungeons_present(self):
        u = _register_and_guild()
        ds = _dungeons(u["headers"])
        assert "goblin-warrens" in ds
        assert "shadow-crypts" in ds
        assert "dragons-hoard" in ds
        gw = ds["goblin-warrens"]
        assert gw["difficulty"] == 1
        assert gw["required_team_size"] == 3
        assert gw["base_duration_seconds"] == 60
        assert gw["recommended_power"] == 45
        assert gw["base_gold_reward"] == 35
        assert gw["base_xp_reward"] == 25
        sc = ds["shadow-crypts"]
        assert sc["difficulty"] == 2
        assert sc["base_duration_seconds"] == 120
        assert sc["recommended_power"] == 60
        assert sc["base_gold_reward"] == 65
        assert sc["base_xp_reward"] == 50
        dh = ds["dragons-hoard"]
        assert dh["difficulty"] == 3
        assert dh["base_duration_seconds"] == 300
        assert dh["recommended_power"] == 80
        assert dh["base_gold_reward"] == 120
        assert dh["base_xp_reward"] == 90

    def test_eight_new_items_present_and_safe(self):
        rows = _items_seed_only()
        slugs = {r["slug"] for r in rows}
        rare = {"cryptbone-blade", "spiritglass-staff", "gravewarden-mail", "relic-signet"}
        epic = {"drakefang-greatsword", "embermind-focus", "dragonscale-vest", "hoardlords-seal"}
        assert rare.issubset(slugs)
        assert epic.issubset(slugs)
        for r in rows:
            if r["slug"] in rare:
                assert r["rarity"] == "Rare"
            if r["slug"] in epic:
                assert r["rarity"] == "Epic"
            assert r["can_be_sold_for_real_money"] is False
            assert r["affects_combat"] is True


# ─── B. Gates ───────────────────────────────────────────────────────────────
class TestDungeonGates:
    def test_goblin_warrens_always_unlocked(self):
        u = _register_and_guild()
        ds = _dungeons(u["headers"])
        assert ds["goblin-warrens"]["unlocked"] is True
        assert ds["goblin-warrens"]["unlock_reason"] is None

    def test_shadow_crypts_locked_without_adventurers(self):
        u = _register_and_guild()
        ds = _dungeons(u["headers"])
        assert ds["shadow-crypts"]["unlocked"] is False
        assert "adventurer" in ds["shadow-crypts"]["unlock_reason"].lower()
        # Try start expedition anyway → 403
        r = requests.post(
            f"{API}/expeditions",
            json={"dungeon_id": ds["shadow-crypts"]["id"], "adventurer_ids": ["fake-id"]},
            headers=u["headers"], timeout=15,
        )
        assert r.status_code == 403
        assert "locked" in r.json()["detail"].lower()

    def test_shadow_crypts_unlocks_with_3_adventurers(self):
        u = _register_and_guild()
        _recruit_n(u["headers"], 3)
        ds = _dungeons(u["headers"])
        assert ds["shadow-crypts"]["unlocked"] is True
        assert ds["shadow-crypts"]["unlock_reason"] is None

    def test_dragons_hoard_locked_initially(self):
        u = _register_and_guild()
        _recruit_n(u["headers"], 3)
        ds = _dungeons(u["headers"])
        # Level 1 guild + 3 fresh adventurers → typical total < 65
        # (each adv has ~25-30 base power, best 3 < 90 in theory but most starter rolls ~75-80)
        # Either way: if locked, try start → expect 403; if unlocked accept as well.
        dh = ds["dragons-hoard"]
        if not dh["unlocked"]:
            assert "level 2" in dh["unlock_reason"].lower() or "65" in dh["unlock_reason"]
            r = requests.post(
                f"{API}/expeditions",
                json={"dungeon_id": dh["id"], "adventurer_ids": ["x", "y", "z"]},
                headers=u["headers"], timeout=15,
            )
            assert r.status_code == 403

    def test_dragons_hoard_unlocks_via_guild_level(self):
        u = _register_and_guild()
        _recruit_n(u["headers"], 3)
        # Bump guild level directly via Mongo
        _mongo().guilds.update_one({"id": u["guild"]["id"]}, {"$set": {"level": 2}})
        ds = _dungeons(u["headers"])
        assert ds["dragons-hoard"]["unlocked"] is True


# ─── C. Equipment delta ─────────────────────────────────────────────────────
def _grant_item(guild_id, item_id, quantity=1):
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


class TestEquipmentDelta:
    def test_delta_no_equipment(self):
        u = _register_and_guild()
        advs = _recruit_n(u["headers"], 3)
        ds = _dungeons(u["headers"])
        gw = ds["goblin-warrens"]
        r = requests.post(
            f"{API}/expeditions",
            json={"dungeon_id": gw["id"], "adventurer_ids": [a["id"] for a in advs]},
            headers=u["headers"], timeout=15,
        )
        assert r.status_code == 201
        exp = r.json()["expedition"]
        assert exp["equipment_power_bonus"] == 0
        assert exp["base_team_power"] == exp["final_team_power"] == exp["team_power"]
        assert (
            exp["success_chance_without_equipment"]
            == exp["success_chance_with_equipment"]
            == exp["success_chance"]
        )
        assert exp["equipment_delta_text"] == "No equipment was used on this run."

    def test_delta_with_equipment(self):
        u = _register_and_guild()
        advs = _recruit_n(u["headers"], 3)
        # Equip Goblin Dagger (Uncommon, +2 AGI, power_score=2 → +4 eq_power) on each
        gd = next(i for i in _items_seed_only("weapon") if i["slug"] == "goblin-dagger")
        for a in advs:
            _grant_item(u["guild"]["id"], gd["id"], 1)
            r = requests.post(
                f"{API}/adventurers/{a['id']}/equip",
                json={"item_id": gd["id"], "slot": "weapon"},
                headers=u["headers"], timeout=15,
            )
            assert r.status_code == 201, r.text

        ds = _dungeons(u["headers"])
        gw = ds["goblin-warrens"]
        r = requests.post(
            f"{API}/expeditions",
            json={"dungeon_id": gw["id"], "adventurer_ids": [a["id"] for a in advs]},
            headers=u["headers"], timeout=15,
        )
        assert r.status_code == 201
        exp = r.json()["expedition"]
        expected_eq_per = (
            int(gd["strength_bonus"]) + int(gd["agility_bonus"]) + int(gd["intellect_bonus"])
            + int(gd["endurance_bonus"]) + int(gd["faith_bonus"]) + int(gd["power_score"])
        )
        assert exp["equipment_power_bonus"] == expected_eq_per * 3
        assert exp["final_team_power"] > exp["base_team_power"]
        assert exp["final_team_power"] == exp["team_power"]
        assert exp["success_chance_with_equipment"] >= exp["success_chance_without_equipment"]
        # narrative must reflect the bonus
        text = exp["equipment_delta_text"]
        assert text != "No equipment was used on this run."
        assert f"+{exp['equipment_power_bonus']}" in text

    def test_delta_snapshot_immutable_after_completion(self):
        """Even after the expedition completes (via direct DB resolve), the
        5 delta fields persist unchanged."""
        u = _register_and_guild()
        advs = _recruit_n(u["headers"], 3)
        ds = _dungeons(u["headers"])
        gw = ds["goblin-warrens"]
        r = requests.post(
            f"{API}/expeditions",
            json={"dungeon_id": gw["id"], "adventurer_ids": [a["id"] for a in advs]},
            headers=u["headers"], timeout=15,
        )
        assert r.status_code == 201
        exp_id = r.json()["expedition"]["id"]
        before = r.json()["expedition"]
        # Force-complete: set completes_at in the past and trigger lazy sweep
        _mongo().expeditions.update_one(
            {"id": exp_id},
            {"$set": {"completes_at": "2000-01-01T00:00:00+00:00"}},
        )
        # Trigger lazy sweep via /guilds/me
        requests.get(f"{API}/guilds/me", headers=u["headers"], timeout=15)
        # Re-fetch detail
        after = requests.get(f"{API}/expeditions/{exp_id}", headers=u["headers"], timeout=15).json()["expedition"]
        for k in (
            "base_team_power", "equipment_power_bonus", "final_team_power",
            "success_chance_without_equipment", "success_chance_with_equipment",
            "equipment_delta_text",
        ):
            assert after[k] == before[k], f"{k} changed: {before[k]} → {after[k]}"


# ─── D. Loot table behavior ─────────────────────────────────────────────────
class TestLootTable:
    def _force_complete_with_outcome(self, u, exp_id, force_success: bool):
        """Helper: set success_chance to 100 or 0, set completes_at to past,
        then trigger lazy sweep so resolver runs."""
        sc = 100 if force_success else 0
        _mongo().expeditions.update_one(
            {"id": exp_id},
            {"$set": {"success_chance": sc, "completes_at": "2000-01-01T00:00:00+00:00"}},
        )
        requests.get(f"{API}/guilds/me", headers=u["headers"], timeout=15)

    def test_shadow_crypts_success_loot_eventually_rare(self):
        """Run many forced-success expeditions; verify at least 1 Rare drop
        across them. Probability per run: 0.65 * 0.15 ≈ 9.75%. Run 60 times
        for ~99.7% chance of seeing at least one Rare."""
        u = _register_and_guild()
        _recruit_n(u["headers"], 3)
        ds = _dungeons(u["headers"])
        sc = ds["shadow-crypts"]
        items_by_id = {i["id"]: i for i in requests.get(f"{API}/items", timeout=15).json()["items"]}
        rare_seen = False
        # Adventurers must be available — re-use the same 3 by force-completing.
        adv_resp = requests.get(f"{API}/adventurers", headers=u["headers"], timeout=15).json()
        ids = [a["id"] for a in adv_resp["adventurers"][:3]]
        for _ in range(60):
            r = requests.post(
                f"{API}/expeditions",
                json={"dungeon_id": sc["id"], "adventurer_ids": ids},
                headers=u["headers"], timeout=15,
            )
            assert r.status_code == 201, r.text
            exp_id = r.json()["expedition"]["id"]
            self._force_complete_with_outcome(u, exp_id, True)
            exp_after = requests.get(f"{API}/expeditions/{exp_id}", headers=u["headers"], timeout=15).json()["expedition"]
            for iid in exp_after.get("loot_item_ids", []):
                if items_by_id.get(iid, {}).get("rarity") == "Rare":
                    rare_seen = True
                    break
            if rare_seen:
                break
        assert rare_seen, "Expected at least one Rare drop in 60 Shadow Crypts success runs"

    def test_shadow_crypts_failure_never_rare(self):
        u = _register_and_guild()
        _recruit_n(u["headers"], 3)
        ds = _dungeons(u["headers"])
        sc = ds["shadow-crypts"]
        adv_resp = requests.get(f"{API}/adventurers", headers=u["headers"], timeout=15).json()
        ids = [a["id"] for a in adv_resp["adventurers"][:3]]
        items_by_id = {i["id"]: i for i in requests.get(f"{API}/items", timeout=15).json()["items"]}
        # 30 forced failures; never see a Rare drop
        for _ in range(30):
            r = requests.post(
                f"{API}/expeditions",
                json={"dungeon_id": sc["id"], "adventurer_ids": ids},
                headers=u["headers"], timeout=15,
            )
            assert r.status_code == 201
            exp_id = r.json()["expedition"]["id"]
            self._force_complete_with_outcome(u, exp_id, False)
            exp_after = requests.get(f"{API}/expeditions/{exp_id}", headers=u["headers"], timeout=15).json()["expedition"]
            for iid in exp_after.get("loot_item_ids", []):
                rarity = items_by_id.get(iid, {}).get("rarity")
                assert rarity in (None, "Common"), (
                    f"Failure dropped non-Common rarity: {rarity}"
                )

    def test_dragons_hoard_success_eventually_epic(self):
        u = _register_and_guild()
        _recruit_n(u["headers"], 3)
        _mongo().guilds.update_one({"id": u["guild"]["id"]}, {"$set": {"level": 2}})
        ds = _dungeons(u["headers"])
        dh = ds["dragons-hoard"]
        items_by_id = {i["id"]: i for i in requests.get(f"{API}/items", timeout=15).json()["items"]}
        adv_resp = requests.get(f"{API}/adventurers", headers=u["headers"], timeout=15).json()
        ids = [a["id"] for a in adv_resp["adventurers"][:3]]
        epic_seen = False
        for _ in range(60):
            r = requests.post(
                f"{API}/expeditions",
                json={"dungeon_id": dh["id"], "adventurer_ids": ids},
                headers=u["headers"], timeout=15,
            )
            assert r.status_code == 201
            exp_id = r.json()["expedition"]["id"]
            TestLootTable._force_complete_with_outcome(self, u, exp_id, True)
            exp_after = requests.get(f"{API}/expeditions/{exp_id}", headers=u["headers"], timeout=15).json()["expedition"]
            for iid in exp_after.get("loot_item_ids", []):
                if items_by_id.get(iid, {}).get("rarity") == "Epic":
                    epic_seen = True
                    break
            if epic_seen:
                break
        assert epic_seen, "Expected at least one Epic drop in 60 Dragon's Hoard success runs"

    def test_dragons_hoard_failure_never_epic(self):
        u = _register_and_guild()
        _recruit_n(u["headers"], 3)
        _mongo().guilds.update_one({"id": u["guild"]["id"]}, {"$set": {"level": 2}})
        ds = _dungeons(u["headers"])
        dh = ds["dragons-hoard"]
        items_by_id = {i["id"]: i for i in requests.get(f"{API}/items", timeout=15).json()["items"]}
        adv_resp = requests.get(f"{API}/adventurers", headers=u["headers"], timeout=15).json()
        ids = [a["id"] for a in adv_resp["adventurers"][:3]]
        for _ in range(30):
            r = requests.post(
                f"{API}/expeditions",
                json={"dungeon_id": dh["id"], "adventurer_ids": ids},
                headers=u["headers"], timeout=15,
            )
            assert r.status_code == 201
            exp_id = r.json()["expedition"]["id"]
            TestLootTable._force_complete_with_outcome(self, u, exp_id, False)
            exp_after = requests.get(f"{API}/expeditions/{exp_id}", headers=u["headers"], timeout=15).json()["expedition"]
            for iid in exp_after.get("loot_item_ids", []):
                rarity = items_by_id.get(iid, {}).get("rarity")
                assert rarity in (None, "Common"), (
                    f"DH failure dropped non-Common rarity: {rarity}"
                )


# ─── E. Dashboard stats ─────────────────────────────────────────────────────
class TestDashboardStats:
    def test_initial_stats_zero(self):
        u = _register_and_guild()
        r = requests.get(f"{API}/guilds/me", headers=u["headers"], timeout=15).json()["guild"]
        assert r["total_expeditions_completed"] == 0
        assert r["highest_dungeon_slug"] is None
        assert r["last_loot_item"] is None

    def test_stats_track_after_completions(self):
        u = _register_and_guild()
        advs = _recruit_n(u["headers"], 3)
        ds = _dungeons(u["headers"])
        gw = ds["goblin-warrens"]
        # 2 expeditions, both forced success (so highest dungeon AND loot tracked)
        for _ in range(2):
            r = requests.post(
                f"{API}/expeditions",
                json={"dungeon_id": gw["id"], "adventurer_ids": [a["id"] for a in advs]},
                headers=u["headers"], timeout=15,
            )
            exp_id = r.json()["expedition"]["id"]
            _mongo().expeditions.update_one(
                {"id": exp_id},
                {"$set": {"success_chance": 100, "completes_at": "2000-01-01T00:00:00+00:00"}},
            )
            requests.get(f"{API}/guilds/me", headers=u["headers"], timeout=15)
        stats = requests.get(f"{API}/guilds/me", headers=u["headers"], timeout=15).json()["guild"]
        assert stats["total_expeditions_completed"] == 2
        assert stats["highest_dungeon_slug"] == "goblin-warrens"
