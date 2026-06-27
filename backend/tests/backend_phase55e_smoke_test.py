"""
Phase 5.5e Expeditions Domain Split — Regression Smoke Test
============================================================
Validates that extracting /api/expeditions/* into app/expeditions/ produced
ZERO behavioural change vs. the pre-split server.py. Specifically tested:

1. OpenAPI surface = 36 paths (unchanged)
2. Tester login + /api/auth/me is_admin=true
3. Expedition start: team_size validation (Goblin Warrens=3) + ownership +
   duplicate adventurer rejection + cross-guild rejection
4. GET /api/expeditions/last-completed → {expedition, adventurer_ids,
   can_replay, cannot_replay_reason}
5. POST /api/expeditions/replay-last creates is_replay=true expedition
6. GET /api/expeditions list returns seconds_remaining + sorted desc
7. GET /api/expeditions/{id} cross-guild → 404 (NOT 403 leak)
8. Loot tables: failure expeditions never produce Rare/Epic
9. Equipment delta snapshot fields persisted on start and immutable
10. Lazy completion sweep is idempotent (no duplicate reward)
"""
import os
import uuid
import pytest
import requests
from pymongo import MongoClient


# ---------- Config ----------
def _load_env_value(path, key, default=None):
    try:
        with open(path) as f:
            for line in f:
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"')
    except FileNotFoundError:
        pass
    return default


BASE_URL = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or _load_env_value("/app/frontend/.env", "REACT_APP_BACKEND_URL")
).rstrip("/")
API = f"{BASE_URL}/api"

MONGO_URL = os.environ.get("MONGO_URL") or _load_env_value(
    "/app/backend/.env", "MONGO_URL", "mongodb://localhost:27017"
)
DB_NAME = os.environ.get("DB_NAME") or _load_env_value(
    "/app/backend/.env", "DB_NAME", "test_database"
)


def _mongo():
    return MongoClient(MONGO_URL)[DB_NAME]


# ---------- Helpers ----------
def _rand_email(prefix="p55e"):
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
    safety = 0
    while len(out) < n and safety < 30:
        safety += 1
        cands = requests.get(f"{API}/recruitment/candidates", headers=headers, timeout=15).json()["candidates"]
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
    assert len(out) == n, f"could not recruit {n} adventurers"
    return out


def _dungeons(headers):
    return {
        d["slug"]: d
        for d in requests.get(f"{API}/dungeons", headers=headers, timeout=15).json()["dungeons"]
    }


def _start_and_force_complete(u, dungeon_id, adv_ids, success: bool):
    r = requests.post(
        f"{API}/expeditions",
        json={"dungeon_id": dungeon_id, "adventurer_ids": adv_ids},
        headers=u["headers"], timeout=15,
    )
    assert r.status_code == 201, r.text
    exp = r.json()["expedition"]
    _mongo().expeditions.update_one(
        {"id": exp["id"]},
        {"$set": {
            "success_chance": 100 if success else 0,
            "completes_at": "2000-01-01T00:00:00+00:00",
        }},
    )
    requests.get(f"{API}/guilds/me", headers=u["headers"], timeout=15)
    return exp["id"], exp


# ---------- Module-level health / auth ----------
class TestSurfaceAndAuth:
    def test_health_ok(self):
        r = requests.get(f"{API}/health", timeout=10)
        assert r.status_code == 200
        assert r.json() == {"status": "ok", "env": "development"}

    def test_openapi_paths_count_37(self):
        r = requests.get(f"{API}/openapi.json", timeout=10)
        assert r.status_code == 200
        paths = r.json().get("paths", {})
        # Phase 9.1 added `/api/leaderboard/guilds` to the 36-path baseline.
        # Updated for Phase 19 §1.2 — added /api/leaderboard/raids (75 → 76)
        assert len(paths) == 76, f"expected 75 OpenAPI paths, got {len(paths)}"
        # Expedition route order: /last-completed + /replay-last must exist
        # before /{expedition_id} (verified by their literal presence as keys)
        assert "/api/expeditions/last-completed" in paths
        assert "/api/expeditions/replay-last" in paths
        assert "/api/expeditions/{expedition_id}" in paths

    def test_tester_login_and_admin(self):
        r = requests.post(
            f"{API}/auth/login",
            json={"email": "tester@orbus.test", "password": "password123"},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        tok = r.json()["access_token"]
        me = requests.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {tok}"}, timeout=15)
        assert me.status_code == 200
        assert me.json()["user"]["is_admin"] is True


# ---------- Expedition start validation ----------
class TestExpeditionStartValidation:
    def test_goblin_warrens_requires_exact_team_size_3(self):
        u = _register_and_guild()
        advs = _recruit_n(u["headers"], 3)
        ds = _dungeons(u["headers"])
        gw = ds["goblin-warrens"]
        # Wrong team size (2)
        r = requests.post(
            f"{API}/expeditions",
            json={"dungeon_id": gw["id"], "adventurer_ids": [a["id"] for a in advs[:2]]},
            headers=u["headers"], timeout=15,
        )
        assert r.status_code == 400, r.text
        assert "team" in r.text.lower() or "exactly" in r.text.lower() or "3" in r.text

    def test_duplicate_adventurer_ids_rejected(self):
        u = _register_and_guild()
        advs = _recruit_n(u["headers"], 3)
        ds = _dungeons(u["headers"])
        gw = ds["goblin-warrens"]
        dup_ids = [advs[0]["id"], advs[0]["id"], advs[1]["id"]]
        r = requests.post(
            f"{API}/expeditions",
            json={"dungeon_id": gw["id"], "adventurer_ids": dup_ids},
            headers=u["headers"], timeout=15,
        )
        assert r.status_code in (400, 422), r.text

    def test_cross_guild_adventurer_rejected(self):
        ua = _register_and_guild()
        ub = _register_and_guild()
        a_advs = _recruit_n(ua["headers"], 3)
        b_advs = _recruit_n(ub["headers"], 2)
        ds = _dungeons(ua["headers"])
        gw = ds["goblin-warrens"]
        # Mix one adventurer from guild B
        team = [a_advs[0]["id"], a_advs[1]["id"], b_advs[0]["id"]]
        r = requests.post(
            f"{API}/expeditions",
            json={"dungeon_id": gw["id"], "adventurer_ids": team},
            headers=ua["headers"], timeout=15,
        )
        assert r.status_code in (400, 404), r.text


# ---------- Expedition list / detail / cross-guild leak ----------
class TestExpeditionListAndDetail:
    def test_list_in_progress_has_seconds_remaining(self):
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
        lst = requests.get(f"{API}/expeditions", headers=u["headers"], timeout=15).json()
        exps = lst["expeditions"]
        assert len(exps) >= 1
        in_progress = [e for e in exps if e.get("status") == "in_progress"]
        assert in_progress, "expected at least one in_progress expedition"
        assert "seconds_remaining" in in_progress[0]
        assert isinstance(in_progress[0]["seconds_remaining"], int)

    def test_list_sorted_created_at_desc(self):
        u = _register_and_guild()
        advs = _recruit_n(u["headers"], 3)
        ds = _dungeons(u["headers"])
        gw = ds["goblin-warrens"]
        # First run completed quickly
        _start_and_force_complete(u, gw["id"], [a["id"] for a in advs], True)
        # Second run still in progress
        requests.post(
            f"{API}/expeditions",
            json={"dungeon_id": gw["id"], "adventurer_ids": [a["id"] for a in advs]},
            headers=u["headers"], timeout=15,
        )
        lst = requests.get(f"{API}/expeditions", headers=u["headers"], timeout=15).json()["expeditions"]
        assert len(lst) >= 2
        # created_at strings ISO8601 — lexicographic desc check
        cats = [e["created_at"] for e in lst]
        assert cats == sorted(cats, reverse=True), "expedition list not sorted created_at desc"

    def test_cross_guild_detail_returns_404_not_403(self):
        ua = _register_and_guild()
        ub = _register_and_guild()
        a_advs = _recruit_n(ua["headers"], 3)
        ds = _dungeons(ua["headers"])
        gw = ds["goblin-warrens"]
        r = requests.post(
            f"{API}/expeditions",
            json={"dungeon_id": gw["id"], "adventurer_ids": [a["id"] for a in a_advs]},
            headers=ua["headers"], timeout=15,
        )
        exp_id = r.json()["expedition"]["id"]
        # Guild B tries to read guild A's expedition
        rb = requests.get(f"{API}/expeditions/{exp_id}", headers=ub["headers"], timeout=15)
        assert rb.status_code == 404, f"expected 404 (no leak), got {rb.status_code}: {rb.text}"

    def test_detail_includes_members_and_loot_items(self):
        u = _register_and_guild()
        advs = _recruit_n(u["headers"], 3)
        ds = _dungeons(u["headers"])
        gw = ds["goblin-warrens"]
        exp_id, _ = _start_and_force_complete(u, gw["id"], [a["id"] for a in advs], True)
        r = requests.get(f"{API}/expeditions/{exp_id}", headers=u["headers"], timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "expedition" in body
        assert "members" in body
        assert len(body["members"]) == 3
        # loot_items must be present (may be empty list)
        assert "loot_items" in body
        assert isinstance(body["loot_items"], list)


# ---------- Last-completed + Replay ----------
class TestReplayFlow:
    def test_last_completed_then_replay(self):
        u = _register_and_guild()
        advs = _recruit_n(u["headers"], 3)
        ds = _dungeons(u["headers"])
        gw = ds["goblin-warrens"]
        exp_id, first = _start_and_force_complete(u, gw["id"], [a["id"] for a in advs], True)

        lc = requests.get(f"{API}/expeditions/last-completed", headers=u["headers"], timeout=15)
        assert lc.status_code == 200, lc.text
        body = lc.json()
        assert body["expedition"]["id"] == exp_id
        assert set(body["adventurer_ids"]) == {a["id"] for a in advs}
        assert "can_replay" in body and "cannot_replay_reason" in body

        if body["can_replay"]:
            rp = requests.post(f"{API}/expeditions/replay-last", headers=u["headers"], timeout=15)
            assert rp.status_code == 201, rp.text
            new_exp = rp.json()["expedition"]
            assert new_exp["is_replay"] is True
            assert new_exp["id"] != exp_id
            # Must contain equipment-delta snapshot fields
            for field in (
                "base_team_power",
                "equipment_power_bonus",
                "final_team_power",
                "success_chance_without_equipment",
                "success_chance_with_equipment",
                "equipment_delta_text",
            ):
                assert field in new_exp, f"replay expedition missing {field}"


# ---------- Equipment delta snapshot immutability ----------
class TestEquipmentDeltaSnapshot:
    def test_snapshot_fields_present_and_immutable(self):
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
        snapshot = {
            "base_team_power": exp["base_team_power"],
            "equipment_power_bonus": exp["equipment_power_bonus"],
            "final_team_power": exp["final_team_power"],
            "success_chance_without_equipment": exp["success_chance_without_equipment"],
            "success_chance_with_equipment": exp["success_chance_with_equipment"],
        }
        assert "equipment_delta_text" in exp
        # Re-fetch via detail endpoint — must not change
        d = requests.get(f"{API}/expeditions/{exp['id']}", headers=u["headers"], timeout=15).json()["expedition"]
        for k, v in snapshot.items():
            assert d[k] == v, f"snapshot field {k} mutated: {v} → {d[k]}"


# ---------- Dungeon gates sticky semantics ----------
class TestDungeonGates:
    def test_shadow_crypts_locked_for_fresh_guild(self):
        # Updated for Round 5 §I (Phase 17.5) — wipe starter roster so the
        # adv_count<3 gate condition is observable on a "fresh" guild.
        u = _register_and_guild()
        _mongo().adventurers.delete_many({"guild_id": u["guild"]["id"]})
        ds = _dungeons(u["headers"])
        sc = ds["shadow-crypts"]
        # Fresh guild has level=1 OK but adv_count=0 → locked
        assert sc["unlocked"] is False
        reason = sc["unlock_reason"].lower()
        assert "3" in reason or "adventurer" in reason

    def test_dragons_hoard_locked_for_fresh_guild_message_includes_peak(self):
        # Updated for Round 5 §I (Phase 17.5) — wipe starter roster so the
        # best-3 power gate stays unmet on a "fresh" guild.
        u = _register_and_guild()
        _mongo().adventurers.delete_many({"guild_id": u["guild"]["id"]})
        ds = _dungeons(u["headers"])
        dh = ds["dragons-hoard"]
        assert dh["unlocked"] is False
        reason = dh["unlock_reason"].lower()
        # message must mention level 2 + 65 + peak
        assert "level 2" in reason
        assert "65" in reason
        assert "peak" in reason


# ---------- Loot tables rarity rules ----------
class TestLootRarityRules:
    def test_failure_never_yields_rare_or_epic(self):
        u = _register_and_guild()
        advs = _recruit_n(u["headers"], 3)
        ds = _dungeons(u["headers"])
        gw = ds["goblin-warrens"]
        # Force 5 failures and aggregate the rarities seen
        bad_rarities = set()
        for _ in range(5):
            exp_id, _ = _start_and_force_complete(u, gw["id"], [a["id"] for a in advs], success=False)
            detail = requests.get(f"{API}/expeditions/{exp_id}", headers=u["headers"], timeout=15).json()
            for it in detail.get("loot_items", []):
                rar = (it.get("rarity") or "").lower()
                bad_rarities.add(rar)
        assert "rare" not in bad_rarities, f"failure produced rare loot: {bad_rarities}"
        assert "epic" not in bad_rarities, f"failure produced epic loot: {bad_rarities}"


# ---------- Lazy completion idempotency ----------
class TestLazyCompletionIdempotent:
    def test_concurrent_sweeps_do_not_double_reward(self):
        u = _register_and_guild()
        advs = _recruit_n(u["headers"], 3)
        ds = _dungeons(u["headers"])
        gw = ds["goblin-warrens"]
        # Start + force completion clock to past
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
        # Trigger sweep multiple times
        for _ in range(3):
            requests.get(f"{API}/guilds/me", headers=u["headers"], timeout=15)
        # Guild gold should reflect ONE completion only — capture inventory count
        inv1 = requests.get(f"{API}/inventory", headers=u["headers"], timeout=15).json()
        count1 = len(inv1.get("inventory", inv1.get("items", [])))
        # Re-sweep
        for _ in range(3):
            requests.get(f"{API}/expeditions", headers=u["headers"], timeout=15)
        inv2 = requests.get(f"{API}/inventory", headers=u["headers"], timeout=15).json()
        count2 = len(inv2.get("inventory", inv2.get("items", [])))
        assert count1 == count2, f"sweep duplicated loot: {count1} → {count2}"
        # Expedition is completed exactly once
        det = requests.get(f"{API}/expeditions/{exp_id}", headers=u["headers"], timeout=15).json()
        assert det["expedition"]["status"] == "completed"
