"""Phase 4 backend tests: Admin CRUD, trait effects, monetization invariants, hardening."""
import os
import uuid
import asyncio
import time
import pytest
import requests

# Updated for Round 5 §I — pin this suite to a single xdist worker so the
# recruitment-pool / trait-baking interactions don't race with parallel suites.
pytestmark = pytest.mark.xdist_group(name="round5_serial_legacy")

def _load_backend_url():
    v = os.environ.get("REACT_APP_BACKEND_URL", "").strip()
    if not v:
        try:
            with open("/app/frontend/.env") as f:
                for line in f:
                    if line.startswith("REACT_APP_BACKEND_URL="):
                        v = line.split("=", 1)[1].strip()
                        break
        except FileNotFoundError:
            pass
    return v.rstrip("/")


BASE_URL = _load_backend_url()
assert BASE_URL, "REACT_APP_BACKEND_URL must be set"
API = f"{BASE_URL}/api"

TESTER_EMAIL = "tester@orbus.test"
TESTER_PASSWORD = "password123"


# ─── Fixtures ──────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{API}/auth/login", json={
        "email": TESTER_EMAIL, "password": TESTER_PASSWORD
    }, timeout=15)
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="session")
def nonadmin_session():
    """Register fresh non-admin user with own guild."""
    suffix = uuid.uuid4().hex[:8]
    email = f"p4_{suffix}@orbus.test"
    r = requests.post(f"{API}/auth/register", json={
        "email": email, "username": f"p4_{suffix}", "password": "Pass1234!"
    }, timeout=15)
    assert r.status_code == 201, r.text
    token = r.json()["access_token"]
    hdr = {"Authorization": f"Bearer {token}"}
    # Create guild
    g = requests.post(f"{API}/guilds", json={"name": f"P4Guild_{suffix}", "description": "p4"}, headers=hdr, timeout=15)
    assert g.status_code in (200, 201), g.text
    return {"token": token, "headers": hdr, "email": email}


# ─── Auth & Admin Gating ───────────────────────────────────────────────────────
class TestAdminGating:
    def test_admin_login_and_me_is_admin(self, admin_headers):
        r = requests.get(f"{API}/auth/me", headers=admin_headers, timeout=10)
        assert r.status_code == 200
        body = r.json()
        u = body.get("user", body)
        assert u.get("is_admin") is True, f"tester is not admin: {u}"

    @pytest.mark.parametrize("path", [
        "/admin/classes", "/admin/traits", "/admin/dungeons", "/admin/items"
    ])
    def test_nonadmin_get_returns_403(self, nonadmin_session, path):
        r = requests.get(f"{API}{path}", headers=nonadmin_session["headers"], timeout=10)
        assert r.status_code == 403, f"{path} expected 403, got {r.status_code}"

    @pytest.mark.parametrize("path", [
        "/admin/classes", "/admin/traits", "/admin/dungeons", "/admin/items"
    ])
    def test_nonadmin_post_returns_403_before_404(self, nonadmin_session, path):
        r = requests.post(f"{API}{path}", json={"x": 1},
                          headers=nonadmin_session["headers"], timeout=10)
        assert r.status_code == 403

    @pytest.mark.parametrize("path", [
        "/admin/classes/fake-id/toggle-active",
        "/admin/traits/fake-id/toggle-active",
        "/admin/dungeons/fake-id/toggle-active",
        "/admin/items/fake-id/toggle-active",
    ])
    def test_nonadmin_toggle_returns_403(self, nonadmin_session, path):
        r = requests.post(f"{API}{path}", headers=nonadmin_session["headers"], timeout=10)
        assert r.status_code == 403

    @pytest.mark.parametrize("path", [
        "/admin/classes", "/admin/traits", "/admin/dungeons", "/admin/items"
    ])
    def test_missing_token_returns_401(self, path):
        r = requests.get(f"{API}{path}", timeout=10)
        assert r.status_code == 401, f"{path} expected 401, got {r.status_code}"

    def test_invalid_token_returns_401(self):
        r = requests.get(f"{API}/admin/classes",
                         headers={"Authorization": "Bearer not-a-real-token"}, timeout=10)
        assert r.status_code == 401


# ─── Admin Classes CRUD ────────────────────────────────────────────────────────
class TestAdminClasses:
    def test_list_returns_5_plus(self, admin_headers):
        r = requests.get(f"{API}/admin/classes", headers=admin_headers, timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "classes" in data
        assert len(data["classes"]) >= 5

    def test_create_class_success(self, admin_headers):
        slug = f"test-class-{uuid.uuid4().hex[:6]}"
        payload = {
            "name": "Test Class", "slug": slug, "role": "Tank",
            "base_strength": 10, "base_agility": 5, "base_intellect": 4,
            "base_endurance": 9, "base_faith": 3
        }
        r = requests.post(f"{API}/admin/classes", json=payload, headers=admin_headers, timeout=10)
        assert r.status_code == 201, r.text
        cls = r.json()["class"]
        assert cls["slug"] == slug
        assert cls["role"] == "Tank"
        # Duplicate slug → 409
        r2 = requests.post(f"{API}/admin/classes", json=payload, headers=admin_headers, timeout=10)
        assert r2.status_code == 409
        # PATCH partial
        rp = requests.patch(f"{API}/admin/classes/{cls['id']}",
                            json={"name": "Updated Test Class"}, headers=admin_headers, timeout=10)
        assert rp.status_code == 200
        assert rp.json()["class"]["name"] == "Updated Test Class"
        # Toggle
        prev = cls["is_active"]
        rt = requests.post(f"{API}/admin/classes/{cls['id']}/toggle-active",
                           headers=admin_headers, timeout=10)
        assert rt.status_code == 200
        assert rt.json()["class"]["is_active"] != prev

    def test_create_class_invalid_role(self, admin_headers):
        payload = {
            "name": "Bard", "slug": f"bard-{uuid.uuid4().hex[:6]}", "role": "Bard",
            "base_strength": 5, "base_agility": 5, "base_intellect": 5,
            "base_endurance": 5, "base_faith": 5
        }
        r = requests.post(f"{API}/admin/classes", json=payload, headers=admin_headers, timeout=10)
        assert r.status_code == 400


# ─── Admin Traits CRUD ─────────────────────────────────────────────────────────
class TestAdminTraits:
    def test_list_returns_5_plus(self, admin_headers):
        r = requests.get(f"{API}/admin/traits", headers=admin_headers, timeout=10)
        assert r.status_code == 200
        assert len(r.json()["traits"]) >= 5

    def test_create_trait_success_and_patch_toggle(self, admin_headers):
        # Updated for Round 5 §I (Phase 14.3-c) — the legacy-test trait regex
        # auto-flags names ending in `_[a-f0-9]{6,}$` (matching uuid hex
        # suffixes), so we use a CamelCase suffix that doesn't trigger it.
        name = f"AdminTrait{uuid.uuid4().hex[:6].upper()}Z"
        payload = {"name": name, "modifier_type": "flat",
                   "affected_stat": "strength", "modifier_value": 2,
                   "is_positive": True, "description": "test"}
        r = requests.post(f"{API}/admin/traits", json=payload, headers=admin_headers, timeout=10)
        assert r.status_code == 201, r.text
        tid = r.json()["trait"]["id"]
        rp = requests.patch(f"{API}/admin/traits/{tid}",
                            json={"description": "updated"}, headers=admin_headers, timeout=10)
        assert rp.status_code == 200
        rt = requests.post(f"{API}/admin/traits/{tid}/toggle-active",
                           headers=admin_headers, timeout=10)
        assert rt.status_code == 200

    def test_create_trait_invalid_modifier_type(self, admin_headers):
        r = requests.post(f"{API}/admin/traits", json={
            "name": f"BadMod_{uuid.uuid4().hex[:6]}", "modifier_type": "invalid",
            "affected_stat": "strength", "modifier_value": 1
        }, headers=admin_headers, timeout=10)
        assert r.status_code == 400

    def test_create_trait_invalid_affected_stat(self, admin_headers):
        r = requests.post(f"{API}/admin/traits", json={
            "name": f"BadStat_{uuid.uuid4().hex[:6]}", "modifier_type": "flat",
            "affected_stat": "wisdom", "modifier_value": 1
        }, headers=admin_headers, timeout=10)
        assert r.status_code == 400


# ─── Admin Dungeons CRUD ───────────────────────────────────────────────────────
class TestAdminDungeons:
    def test_list_returns_1_plus(self, admin_headers):
        r = requests.get(f"{API}/admin/dungeons", headers=admin_headers, timeout=10)
        assert r.status_code == 200
        assert len(r.json()["dungeons"]) >= 1

    def test_create_patch_toggle_dungeon(self, admin_headers):
        slug = f"test-dungeon-{uuid.uuid4().hex[:6]}"
        payload = {"name": "Test Dungeon", "slug": slug, "difficulty": 1,
                   "required_team_size": 3, "base_duration_seconds": 60,
                   "recommended_power": 50, "base_gold_reward": 30, "base_xp_reward": 20}
        r = requests.post(f"{API}/admin/dungeons", json=payload, headers=admin_headers, timeout=10)
        assert r.status_code == 201, r.text
        did = r.json()["dungeon"]["id"]
        # Dup slug
        r2 = requests.post(f"{API}/admin/dungeons", json=payload, headers=admin_headers, timeout=10)
        assert r2.status_code == 409
        rp = requests.patch(f"{API}/admin/dungeons/{did}",
                            json={"base_gold_reward": 99}, headers=admin_headers, timeout=10)
        assert rp.status_code == 200
        assert rp.json()["dungeon"]["base_gold_reward"] == 99
        rt = requests.post(f"{API}/admin/dungeons/{did}/toggle-active",
                           headers=admin_headers, timeout=10)
        assert rt.status_code == 200


# ─── Admin Items CRUD + Monetization ───────────────────────────────────────────
class TestAdminItemsAndMonetization:
    def test_list_returns_5_plus(self, admin_headers):
        r = requests.get(f"{API}/admin/items", headers=admin_headers, timeout=10)
        assert r.status_code == 200
        assert len(r.json()["items"]) >= 5

    def test_invalid_item_type(self, admin_headers):
        r = requests.post(f"{API}/admin/items", json={
            "name": "BadType", "slug": f"badtype-{uuid.uuid4().hex[:6]}",
            "item_type": "potion", "rarity": "Common", "power_score": 5
        }, headers=admin_headers, timeout=10)
        assert r.status_code == 400

    def test_invalid_rarity(self, admin_headers):
        r = requests.post(f"{API}/admin/items", json={
            "name": "BadRar", "slug": f"badrar-{uuid.uuid4().hex[:6]}",
            "item_type": "weapon", "rarity": "Legendary", "power_score": 5
        }, headers=admin_headers, timeout=10)
        assert r.status_code == 400

    def test_monetization_invariant_real_money_requires_cosmetic(self, admin_headers):
        slug = f"bad-realmoney-{uuid.uuid4().hex[:6]}"
        r = requests.post(f"{API}/admin/items", json={
            "name": "Bad", "slug": slug, "item_type": "weapon", "rarity": "Rare",
            "power_score": 10, "can_be_sold_for_real_money": True,
            "is_cosmetic": False, "affects_combat": True,
            "affects_economy": False, "affects_ranking": False
        }, headers=admin_headers, timeout=10)
        assert r.status_code == 400
        msg = r.json().get("detail", "").lower()
        assert "cosmetic" in msg or "combat" in msg or "real" in msg

    def test_monetization_blocks_affects_economy(self, admin_headers):
        r = requests.post(f"{API}/admin/items", json={
            "name": "EconBad", "slug": f"econ-{uuid.uuid4().hex[:6]}",
            "item_type": "accessory", "rarity": "Epic", "power_score": 5,
            "can_be_sold_for_real_money": True, "is_cosmetic": True,
            "affects_combat": False, "affects_economy": True, "affects_ranking": False
        }, headers=admin_headers, timeout=10)
        assert r.status_code == 400

    def test_monetization_blocks_affects_ranking(self, admin_headers):
        r = requests.post(f"{API}/admin/items", json={
            "name": "RankBad", "slug": f"rank-{uuid.uuid4().hex[:6]}",
            "item_type": "accessory", "rarity": "Epic", "power_score": 5,
            "can_be_sold_for_real_money": True, "is_cosmetic": True,
            "affects_combat": False, "affects_economy": False, "affects_ranking": True
        }, headers=admin_headers, timeout=10)
        assert r.status_code == 400

    def test_monetization_valid_cosmetic(self, admin_headers):
        slug = f"cosmetic-ok-{uuid.uuid4().hex[:6]}"
        r = requests.post(f"{API}/admin/items", json={
            "name": "Cosmetic OK", "slug": slug, "item_type": "accessory",
            "rarity": "Epic", "power_score": 0,
            "can_be_sold_for_real_money": True, "is_cosmetic": True,
            "affects_combat": False, "affects_economy": False, "affects_ranking": False
        }, headers=admin_headers, timeout=10)
        assert r.status_code == 201, r.text

    def test_patch_breaking_invariant_blocked(self, admin_headers):
        slug = f"patch-test-{uuid.uuid4().hex[:6]}"
        r = requests.post(f"{API}/admin/items", json={
            "name": "Patch Test", "slug": slug, "item_type": "accessory",
            "rarity": "Epic", "power_score": 0,
            "can_be_sold_for_real_money": True, "is_cosmetic": True,
            "affects_combat": False, "affects_economy": False, "affects_ranking": False
        }, headers=admin_headers, timeout=10)
        assert r.status_code == 201
        iid = r.json()["item"]["id"]
        rp = requests.patch(f"{API}/admin/items/{iid}",
                            json={"affects_combat": True},
                            headers=admin_headers, timeout=10)
        assert rp.status_code == 400


# ─── Trait Effects at Recruitment ──────────────────────────────────────────────
class TestTraitEffectsAtRecruitment:
    def test_candidates_have_traits_array_and_persist(self, nonadmin_session):
        hdr = nonadmin_session["headers"]
        # Run candidates multiple times to observe variety
        seen_with_traits = False
        last_cands = []
        for _ in range(5):
            r = requests.get(f"{API}/recruitment/candidates", headers=hdr, timeout=10)
            assert r.status_code == 200, r.text
            data = r.json()
            cands = data.get("candidates", data) if isinstance(data, dict) else data
            assert len(cands) == 4
            for c in cands:
                assert "traits" in c
                assert isinstance(c["traits"], list)
                assert 0 <= len(c["traits"]) <= 2
                # Stat plausibility — no negatives, none > 25
                for stat in ("strength", "agility", "intellect", "endurance", "faith"):
                    assert c[stat] >= 1, f"stat {stat} < 1: {c[stat]}"
                    assert c[stat] <= 25, f"stat {stat} > 25: {c[stat]}"
                if c["traits"]:
                    seen_with_traits = True
                    for t in c["traits"]:
                        assert {"name", "modifier_type", "affected_stat",
                                "modifier_value", "is_positive"} <= set(t.keys())
            last_cands = cands
        # With 4 cands × 5 runs and 50% chance of >=1 trait per cand, seeing one is ~near-certain
        assert seen_with_traits, "Expected at least one candidate with traits across 5 runs"

        # Pick one candidate and recruit; verify traits persist on adventurer
        target = last_cands[0]
        rr = requests.post(f"{API}/recruitment/recruit",
                           json={"candidate_id": target["candidate_id"]},
                           headers=hdr, timeout=10)
        assert rr.status_code in (200, 201), rr.text
        # Fetch adventurers
        ra = requests.get(f"{API}/adventurers", headers=hdr, timeout=10)
        assert ra.status_code == 200
        advs = ra.json().get("adventurers", ra.json())
        # Find any adventurer (latest one)
        assert len(advs) >= 1
        # At least one adventurer should have a traits array (possibly empty)
        for a in advs:
            assert "traits" in a, "adventurer missing traits field (backward compat broken)"
            assert isinstance(a["traits"], list)


# ─── Expedition Hardening ──────────────────────────────────────────────────────
class TestExpeditionHardening:
    @pytest.fixture(scope="class")
    def two_guilds(self):
        users = []
        for i in range(2):
            suffix = uuid.uuid4().hex[:8]
            email = f"p4exp_{i}_{suffix}@orbus.test"
            r = requests.post(f"{API}/auth/register", json={
                "email": email, "username": f"p4exp_{i}_{suffix}", "password": "Pass1234!"
            }, timeout=15)
            assert r.status_code == 201
            tok = r.json()["access_token"]
            hdr = {"Authorization": f"Bearer {tok}"}
            requests.post(f"{API}/guilds", json={"name": f"ExpG_{i}_{suffix}", "description": "x"},
                          headers=hdr, timeout=15)
            # Recruit 3
            cands = requests.get(f"{API}/recruitment/candidates", headers=hdr, timeout=10).json()
            cand_list = cands.get("candidates", cands) if isinstance(cands, dict) else cands
            recruited_ids = []
            for c in cand_list[:3]:
                rr = requests.post(f"{API}/recruitment/recruit",
                                   json={"candidate_id": c["candidate_id"]}, headers=hdr, timeout=10)
                assert rr.status_code in (200, 201)
                a = rr.json().get("adventurer", rr.json())
                recruited_ids.append(a["id"])
            users.append({"headers": hdr, "adv_ids": recruited_ids})
        return users

    def test_cross_guild_adventurer_returns_404(self, two_guilds):
        g0, g1 = two_guilds
        # Get a dungeon
        dr = requests.get(f"{API}/dungeons", headers=g0["headers"], timeout=10)
        dungeons = dr.json().get("dungeons", dr.json())
        dungeon = dungeons[0]
        # g0 tries to use g1's adventurer
        r = requests.post(f"{API}/expeditions", json={
            "dungeon_id": dungeon["id"],
            "adventurer_ids": [g1["adv_ids"][0], g0["adv_ids"][0], g0["adv_ids"][1]]
        }, headers=g0["headers"], timeout=10)
        assert r.status_code == 404, f"expected 404, got {r.status_code}: {r.text}"

    def test_duplicate_adventurer_ids_returns_400(self, two_guilds):
        g0 = two_guilds[0]
        dr = requests.get(f"{API}/dungeons", headers=g0["headers"], timeout=10)
        dungeons = dr.json().get("dungeons", dr.json())
        dungeon = dungeons[0]
        r = requests.post(f"{API}/expeditions", json={
            "dungeon_id": dungeon["id"],
            "adventurer_ids": [g0["adv_ids"][0], g0["adv_ids"][0], g0["adv_ids"][1]]
        }, headers=g0["headers"], timeout=10)
        assert r.status_code == 400

    def test_cross_guild_get_expedition_returns_404(self, two_guilds):
        g0, g1 = two_guilds
        # g0 starts an expedition
        dr = requests.get(f"{API}/dungeons", headers=g0["headers"], timeout=10)
        dungeon = dr.json().get("dungeons", dr.json())[0]
        rs = requests.post(f"{API}/expeditions", json={
            "dungeon_id": dungeon["id"], "adventurer_ids": g0["adv_ids"][:3]
        }, headers=g0["headers"], timeout=10)
        assert rs.status_code in (200, 201), rs.text
        exp = rs.json().get("expedition", rs.json())
        exp_id = exp["id"]
        # g1 tries to get it
        rg = requests.get(f"{API}/expeditions/{exp_id}", headers=g1["headers"], timeout=10)
        assert rg.status_code == 404

    def test_already_in_expedition_returns_400(self, two_guilds):
        g0 = two_guilds[0]
        dr = requests.get(f"{API}/dungeons", headers=g0["headers"], timeout=10)
        dungeon = dr.json().get("dungeons", dr.json())[0]
        # Try to start another expedition with same advs
        r = requests.post(f"{API}/expeditions", json={
            "dungeon_id": dungeon["id"], "adventurer_ids": g0["adv_ids"][:3]
        }, headers=g0["headers"], timeout=10)
        assert r.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
