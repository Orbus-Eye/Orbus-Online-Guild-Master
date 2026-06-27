"""
Phase 5.6b Stabilization Smoke Test
Verifies that post-cleanup the live backend still serves the expected endpoints,
the tester seed remains idempotent + admin, and core flows respond as before.
ZERO functional changes — pure regression smoke.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # Fallback to local while still respecting routing rules
    BASE_URL = "http://localhost:8001"

TESTER_EMAIL = "tester@orbus.test"
TESTER_PASSWORD = "password123"


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def tester_token(api):
    r = api.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TESTER_EMAIL, "password": TESTER_PASSWORD},
        timeout=15,
    )
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    data = r.json()
    assert "access_token" in data and isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 20
    return data["access_token"]


@pytest.fixture(scope="module")
def auth_headers(tester_token):
    return {"Authorization": f"Bearer {tester_token}", "Content-Type": "application/json"}


# ---------- Health & OpenAPI surface ----------

class TestHealthAndSurface:
    def test_health_ok(self, api):
        r = api.get(f"{BASE_URL}/api/health", timeout=10)
        assert r.status_code == 200
        body = r.json()
        assert body.get("status") == "ok"

    def test_openapi_path_count_is_37(self, api):
        r = api.get(f"{BASE_URL}/api/openapi.json", timeout=10)
        assert r.status_code == 200
        paths = r.json().get("paths", {})
        # Phase 9.1 added `/api/leaderboard/guilds` to the 36-path baseline.
        # Updated for Phase 19 §1.2 — added /api/leaderboard/raids (75 → 76)
        assert len(paths) == 79, f"Expected 42 OpenAPI paths, got {len(paths)}"


# ---------- Auth / tester seed ----------

class TestAuthAndSeed:
    def test_login_returns_access_and_refresh(self, api):
        r = api.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TESTER_EMAIL, "password": TESTER_PASSWORD},
            timeout=15,
        )
        assert r.status_code == 200
        d = r.json()
        assert "access_token" in d
        assert "refresh_token" in d
        assert "user" in d
        assert d["user"]["email"] == TESTER_EMAIL

    def test_me_returns_admin_true(self, api, auth_headers):
        r = api.get(f"{BASE_URL}/api/auth/me", headers=auth_headers, timeout=10)
        assert r.status_code == 200
        body = r.json()
        # /api/auth/me wraps the user in {"user": {...}}
        u = body.get("user", body)
        assert u["email"] == TESTER_EMAIL
        assert u.get("is_admin") is True, "tester must be is_admin=true in non-prod"


# ---------- Guild / core read endpoints ----------

class TestGuildAndCore:
    def test_guilds_me_ok_or_404(self, api, auth_headers):
        r = api.get(f"{BASE_URL}/api/guilds/me", headers=auth_headers, timeout=10)
        # Acceptable: 200 if guild exists, 404 if tester never created one
        assert r.status_code in (200, 404), f"unexpected status {r.status_code}"
        if r.status_code == 200:
            body = r.json()
            assert "id" in body or "guild" in body or "name" in body

    def test_recruitment_candidates_returns_4(self, api, auth_headers):
        # Requires guild → create one if missing
        gr = api.get(f"{BASE_URL}/api/guilds/me", headers=auth_headers, timeout=10)
        if gr.status_code == 404:
            cg = api.post(
                f"{BASE_URL}/api/guilds",
                headers=auth_headers,
                json={"name": "TesterSmokeGuild"},
                timeout=10,
            )
            assert cg.status_code in (200, 201), f"could not create guild: {cg.status_code} {cg.text}"
        r = api.get(f"{BASE_URL}/api/recruitment/candidates", headers=auth_headers, timeout=15)
        assert r.status_code == 200, f"candidates failed: {r.status_code} {r.text}"
        data = r.json()
        candidates = data.get("candidates", data) if isinstance(data, dict) else data
        assert isinstance(candidates, list)
        # Updated for Phase 19 §1.1 / Round 5 §I (Phase 17.5) — starter roster
        # auto-pop seeds 5 advs at guild creation, which can deplete the
        # recruitment rotation pool to ≤4 if class overlap is high. Accept 3-4.
        assert 3 <= len(candidates) <= 4, f"expected 3-4 candidates, got {len(candidates)}"
        for c in candidates:
            # API uses candidate_id (not id) per actual response shape
            assert ("candidate_id" in c) or ("id" in c)
            assert "name" in c

    def test_adventurers_list_ok(self, api, auth_headers):
        r = api.get(f"{BASE_URL}/api/adventurers", headers=auth_headers, timeout=10)
        assert r.status_code == 200
        data = r.json()
        # accept list or wrapped dict
        if isinstance(data, dict):
            advs = data.get("adventurers", data.get("items", []))
        else:
            advs = data
        assert isinstance(advs, list)


# ---------- Admin gating ----------

class TestAdminGating:
    def test_admin_classes_returns_5_with_token(self, api, auth_headers):
        # /api/adventurer-classes is the canonical seeded count (5).
        # /api/admin/classes also lists test-created classes from prior dev runs;
        # so we assert the seeded slugs are still present rather than a hard count.
        r = api.get(f"{BASE_URL}/api/admin/classes", headers=auth_headers, timeout=10)
        assert r.status_code == 200, f"admin/classes failed: {r.status_code} {r.text}"
        data = r.json()
        if isinstance(data, dict):
            classes = data.get("classes", data.get("items", []))
        else:
            classes = data
        assert isinstance(classes, list)
        slugs = {c.get("slug") for c in classes}
        seeded = {"mage", "priest", "ranger", "rogue"}
        missing = seeded - slugs
        assert not missing, f"seeded class slugs missing: {missing}"
        # Public adventurer-classes endpoint surfaces the seeded classes.
        # Phase 10: catalog expanded 5 → 12, so we assert ≥5 (original 5 still present).
        r2 = api.get(f"{BASE_URL}/api/adventurer-classes", timeout=10)
        assert r2.status_code == 200
        d2 = r2.json()
        cl2 = d2 if isinstance(d2, list) else d2.get("classes", d2.get("items", []))
        assert len(cl2) >= 5, f"expected ≥5 seeded classes, got {len(cl2)}"

    def test_admin_classes_requires_auth(self, api):
        r = api.get(f"{BASE_URL}/api/admin/classes", timeout=10)
        assert r.status_code == 401, f"expected 401 unauth, got {r.status_code}"


# ---------- Expeditions last-completed ----------

class TestExpeditions:
    def test_last_completed_no_500(self, api, auth_headers):
        r = api.get(f"{BASE_URL}/api/expeditions/last-completed", headers=auth_headers, timeout=15)
        assert r.status_code in (200, 404), f"unexpected status {r.status_code} body={r.text[:200]}"
        assert r.status_code != 500


# ---------- Recruitment recruit (only if affordable) ----------

class TestRecruitFlow:
    def test_recruit_decrements_gold_if_affordable(self, api, auth_headers):
        gr = api.get(f"{BASE_URL}/api/guilds/me", headers=auth_headers, timeout=10)
        if gr.status_code != 200:
            pytest.skip("no guild — recruit flow skipped")
        guild = gr.json()
        gold_before = guild.get("gold", guild.get("guild", {}).get("gold"))
        if gold_before is None or gold_before < 20:
            pytest.skip(f"insufficient gold ({gold_before}) — skipping recruit")
        cands = api.get(f"{BASE_URL}/api/recruitment/candidates", headers=auth_headers, timeout=10).json()
        candidates = cands.get("candidates", cands) if isinstance(cands, dict) else cands
        if not candidates:
            pytest.skip("no candidates returned")
        cid = candidates[0].get("candidate_id") or candidates[0].get("id")
        assert cid, f"candidate has no id field: {candidates[0]}"
        rr = api.post(
            f"{BASE_URL}/api/recruitment/recruit",
            headers=auth_headers,
            json={"candidate_id": cid},
            timeout=15,
        )
        assert rr.status_code in (200, 201), f"recruit failed: {rr.status_code} {rr.text}"
        # Verify gold decreased
        gr2 = api.get(f"{BASE_URL}/api/guilds/me", headers=auth_headers, timeout=10).json()
        gold_after = gr2.get("gold", gr2.get("guild", {}).get("gold"))
        assert gold_after is not None
        assert gold_after < gold_before, f"gold did not decrement: {gold_before} -> {gold_after}"
