"""Orbus Online: Guild Master — Phase 2 backend tests (pytest).

Covers: adventurer-classes, recruitment candidates/recruit, adventurers,
cross-user isolation, insufficient-gold refund, stat consistency.
"""
import os
import uuid
import pytest
import requests

# Resolve BASE_URL
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip()
                break
BASE_URL = BASE_URL.rstrip("/")
API = f"{BASE_URL}/api"

EXPECTED_CLASSES = {
    "Warrior": ("Tank", 8, 4, 2, 9, 2),
    "Rogue":   ("DPS",  5, 9, 3, 4, 2),
    "Mage":    ("DPS",  2, 4, 10, 3, 3),
    "Priest":  ("Healer", 2, 3, 6, 4, 10),
    "Ranger":  ("DPS",  5, 8, 4, 5, 3),
}
ALLOWED_RARITIES = {"Common", "Uncommon", "Rare", "Epic"}


def _rand_email():
    return f"p2_{uuid.uuid4().hex[:10]}@orbus.test"


def _register():
    payload = {"email": _rand_email(), "username": "p2_" + uuid.uuid4().hex[:6], "password": "password123"}
    r = requests.post(f"{API}/auth/register", json=payload, timeout=15)
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def _create_guild(token, name=None):
    name = name or "TEST_P2_" + uuid.uuid4().hex[:6]
    h = {"Authorization": f"Bearer {token}"}
    r = requests.post(f"{API}/guilds", json={"name": name}, headers=h, timeout=15)
    assert r.status_code == 201, r.text
    return r.json()["guild"]


@pytest.fixture(scope="module")
def user_with_guild():
    """Fresh user + guild (100 gold)."""
    token = _register()
    guild = _create_guild(token)
    return {"token": token, "guild": guild, "headers": {"Authorization": f"Bearer {token}"}}


# ─── Adventurer Classes ────────────────────────────────────────────────────────
class TestAdventurerClasses:
    def test_list_classes_no_auth(self):
        r = requests.get(f"{API}/adventurer-classes", timeout=15)
        assert r.status_code == 200
        classes = r.json()["classes"]
        assert isinstance(classes, list)
        active = [c for c in classes if c.get("is_active", True)]
        # Phase 10: expanded 5 → 12. Test verifies the ORIGINAL 5 are still present
        # with their original stats; new classes are allowed but not validated here.
        assert len(active) >= 5
        by_name = {c["name"]: c for c in active}
        for cname, (role, s, a, i, e, f) in EXPECTED_CLASSES.items():
            assert cname in by_name, f"missing class {cname}"
            c = by_name[cname]
            assert c["role"] == role
            assert (c["base_strength"], c["base_agility"], c["base_intellect"],
                    c["base_endurance"], c["base_faith"]) == (s, a, i, e, f), c


# ─── Guild adventurer_count ────────────────────────────────────────────────────
class TestGuildAdventurerCount:
    def test_adventurer_count_present(self, user_with_guild):
        r = requests.get(f"{API}/guilds/me", headers=user_with_guild["headers"], timeout=15)
        assert r.status_code == 200
        guild = r.json()["guild"]
        assert "adventurer_count" in guild
        assert isinstance(guild["adventurer_count"], int)
        assert guild["adventurer_count"] >= 0


# ─── Recruitment candidates ────────────────────────────────────────────────────
class TestRecruitmentCandidates:
    def test_candidates_no_auth_401(self):
        r = requests.get(f"{API}/recruitment/candidates", timeout=15)
        assert r.status_code == 401

    def test_candidates_no_guild_404(self):
        token = _register()
        r = requests.get(f"{API}/recruitment/candidates",
                         headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert r.status_code == 404
        assert r.json()["detail"] == "No guild found for this user"

    def test_candidates_returns_four_valid(self, user_with_guild):
        r = requests.get(f"{API}/recruitment/candidates",
                         headers=user_with_guild["headers"], timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        cands = body["candidates"]
        assert len(cands) == 4
        # Phase 10: catalog expanded — class_name may be any of the 12 seeded
        # classes (5 original + 7 new), role may be Tank/DPS/Healer/Support.
        ALLOWED_ROLES_P10 = {"Tank", "DPS", "Healer", "Support"}
        for c in cands:
            assert isinstance(c["candidate_id"], str) and len(c["candidate_id"]) >= 8
            assert isinstance(c["name"], str) and len(c["name"]) > 0
            assert isinstance(c["class_name"], str) and len(c["class_name"]) > 0
            assert c["class_role"] in ALLOWED_ROLES_P10, c["class_role"]
            assert c["rarity"] in ALLOWED_RARITIES
            assert c["level"] == 1
            assert c["experience"] == 0
            for stat in ("strength", "agility", "intellect", "endurance", "faith"):
                v = c[stat]
                assert isinstance(v, int) and 1 <= v <= 20, f"{stat}={v}"
            assert c["stamina"] == 100
            assert c["morale"] == 100
            assert c["cost_gold"] == 20

    def test_candidates_replaces_prior_offer(self, user_with_guild):
        h = user_with_guild["headers"]
        r1 = requests.get(f"{API}/recruitment/candidates", headers=h, timeout=15)
        old_id = r1.json()["candidates"][0]["candidate_id"]
        # New offer
        r2 = requests.get(f"{API}/recruitment/candidates", headers=h, timeout=15)
        new_ids = {c["candidate_id"] for c in r2.json()["candidates"]}
        assert old_id not in new_ids
        # Old id should now return 404 on recruit
        rr = requests.post(f"{API}/recruitment/recruit",
                           json={"candidate_id": old_id}, headers=h, timeout=15)
        assert rr.status_code == 404
        assert "not found" in rr.json()["detail"].lower() or "already" in rr.json()["detail"].lower()


# ─── Recruitment recruit ───────────────────────────────────────────────────────
class TestRecruit:
    def test_recruit_no_auth_401(self):
        r = requests.post(f"{API}/recruitment/recruit", json={"candidate_id": "x" * 12}, timeout=15)
        assert r.status_code == 401

    def test_recruit_success_stats_match_and_gold_decremented(self):
        token = _register()
        guild = _create_guild(token)
        h = {"Authorization": f"Bearer {token}"}

        before_g = requests.get(f"{API}/guilds/me", headers=h, timeout=15).json()["guild"]
        gold_before = before_g["gold"]
        adv_count_before = before_g["adventurer_count"]

        cands = requests.get(f"{API}/recruitment/candidates", headers=h, timeout=15).json()["candidates"]
        chosen = cands[0]

        r = requests.post(f"{API}/recruitment/recruit",
                          json={"candidate_id": chosen["candidate_id"]}, headers=h, timeout=15)
        assert r.status_code == 201, r.text
        body = r.json()
        adv = body["adventurer"]
        # Stats EXACTLY match the offered candidate (no mutation)
        for field in ("name", "class_name", "class_role", "rarity", "level", "experience",
                      "strength", "agility", "intellect", "endurance", "faith",
                      "stamina", "morale"):
            assert adv[field] == chosen[field], f"{field} mismatch: {adv[field]} vs {chosen[field]}"
        assert adv["adventurer_class_id"] == chosen["adventurer_class_id"]

        # Gold returned in response is decremented by exactly 20
        assert body["guild"]["gold"] == gold_before - 20

        # GET /guilds/me reflects the new count + gold
        after = requests.get(f"{API}/guilds/me", headers=h, timeout=15).json()["guild"]
        assert after["gold"] == gold_before - 20
        assert after["adventurer_count"] == adv_count_before + 1

        # Adventurer visible in /adventurers
        listing = requests.get(f"{API}/adventurers", headers=h, timeout=15).json()["adventurers"]
        ids = {a["id"] for a in listing}
        assert adv["id"] in ids
        # Pull the listed copy and compare critical stats too
        listed = next(a for a in listing if a["id"] == adv["id"])
        for field in ("strength", "agility", "intellect", "endurance", "faith", "rarity"):
            assert listed[field] == chosen[field]

    def test_recruit_twice_same_candidate_returns_404(self):
        token = _register()
        _create_guild(token)
        h = {"Authorization": f"Bearer {token}"}
        cands = requests.get(f"{API}/recruitment/candidates", headers=h, timeout=15).json()["candidates"]
        cid = cands[0]["candidate_id"]
        r1 = requests.post(f"{API}/recruitment/recruit", json={"candidate_id": cid}, headers=h, timeout=15)
        assert r1.status_code == 201
        r2 = requests.post(f"{API}/recruitment/recruit", json={"candidate_id": cid}, headers=h, timeout=15)
        assert r2.status_code == 404
        assert r2.json()["detail"] == "Candidate not found or already recruited"

    def test_cross_guild_recruit_404(self):
        # User A creates guild, gets candidates
        tokenA = _register()
        _create_guild(tokenA)
        hA = {"Authorization": f"Bearer {tokenA}"}
        candsA = requests.get(f"{API}/recruitment/candidates", headers=hA, timeout=15).json()["candidates"]
        a_cid = candsA[0]["candidate_id"]

        # User B tries to recruit A's candidate
        tokenB = _register()
        _create_guild(tokenB)
        hB = {"Authorization": f"Bearer {tokenB}"}
        r = requests.post(f"{API}/recruitment/recruit",
                          json={"candidate_id": a_cid}, headers=hB, timeout=15)
        assert r.status_code == 404, r.text

        # A's candidate still recruitable by A (no leak / no consumption)
        rA = requests.post(f"{API}/recruitment/recruit",
                           json={"candidate_id": a_cid}, headers=hA, timeout=15)
        assert rA.status_code == 201

    def test_insufficient_gold_400_and_refund_offer(self):
        token = _register()
        _create_guild(token)
        h = {"Authorization": f"Bearer {token}"}

        # Drain gold: starting 100 gold → 5 successful recruits = 0 gold
        for i in range(5):
            cands = requests.get(f"{API}/recruitment/candidates", headers=h, timeout=15).json()["candidates"]
            cid = cands[0]["candidate_id"]
            r = requests.post(f"{API}/recruitment/recruit",
                              json={"candidate_id": cid}, headers=h, timeout=15)
            assert r.status_code == 201, f"recruit {i} failed: {r.text}"

        g = requests.get(f"{API}/guilds/me", headers=h, timeout=15).json()["guild"]
        assert g["gold"] == 0

        # 6th recruit must 400 'Insufficient gold'
        cands = requests.get(f"{API}/recruitment/candidates", headers=h, timeout=15).json()["candidates"]
        cid = cands[0]["candidate_id"]
        r = requests.post(f"{API}/recruitment/recruit",
                          json={"candidate_id": cid}, headers=h, timeout=15)
        assert r.status_code == 400
        assert r.json()["detail"] == "Insufficient gold"

        # Offer should be refunded — the candidate id is still recruitable
        # (we can't add gold via API, so verify by listing candidates still includes it)
        cur = requests.get(f"{API}/recruitment/candidates", headers=h, timeout=15)
        # Note: calling /candidates REPLACES the prior offer, so we can't check inclusion that way.
        # Instead, check that BEFORE re-listing, the failed recruit didn't consume the offer:
        # Do a second insufficient-gold attempt with the SAME cid — should still be 400 (not 404).
        token2 = _register()
        _create_guild(token2)
        h2 = {"Authorization": f"Bearer {token2}"}
        # Drain user2 too
        for i in range(5):
            cands2 = requests.get(f"{API}/recruitment/candidates", headers=h2, timeout=15).json()["candidates"]
            requests.post(f"{API}/recruitment/recruit", json={"candidate_id": cands2[0]["candidate_id"]}, headers=h2, timeout=15)
        cands2 = requests.get(f"{API}/recruitment/candidates", headers=h2, timeout=15).json()["candidates"]
        cid2 = cands2[0]["candidate_id"]
        r_a = requests.post(f"{API}/recruitment/recruit", json={"candidate_id": cid2}, headers=h2, timeout=15)
        assert r_a.status_code == 400
        r_b = requests.post(f"{API}/recruitment/recruit", json={"candidate_id": cid2}, headers=h2, timeout=15)
        assert r_b.status_code == 400, (
            f"Offer was consumed on failed-gold attempt — expected 400 again, got {r_b.status_code}: {r_b.text}"
        )


# ─── Adventurers listing isolation ────────────────────────────────────────────
class TestAdventurersList:
    def test_adventurers_no_auth_401(self):
        r = requests.get(f"{API}/adventurers", timeout=15)
        assert r.status_code == 401

    def test_no_guild_404(self):
        token = _register()
        r = requests.get(f"{API}/adventurers",
                         headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert r.status_code == 404

    def test_cross_user_isolation(self):
        # User A with guild + 1 recruit
        tokenA = _register()
        _create_guild(tokenA)
        hA = {"Authorization": f"Bearer {tokenA}"}
        candsA = requests.get(f"{API}/recruitment/candidates", headers=hA, timeout=15).json()["candidates"]
        rA = requests.post(f"{API}/recruitment/recruit",
                           json={"candidate_id": candsA[0]["candidate_id"]}, headers=hA, timeout=15)
        a_adv_id = rA.json()["adventurer"]["id"]

        # User B with guild + 0 recruits
        tokenB = _register()
        _create_guild(tokenB)
        hB = {"Authorization": f"Bearer {tokenB}"}

        listB = requests.get(f"{API}/adventurers", headers=hB, timeout=15).json()["adventurers"]
        assert isinstance(listB, list)
        ids_b = {a["id"] for a in listB}
        assert a_adv_id not in ids_b
        # B has no adventurers
        assert all(a["guild_id"] != candsA[0].get("guild_id", "?") for a in listB) or len(listB) == 0
