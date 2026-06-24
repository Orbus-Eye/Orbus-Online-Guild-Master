"""Orbus Online: Guild Master — Phase 1 backend tests (pytest)."""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") if os.environ.get("REACT_APP_BACKEND_URL") else None
if BASE_URL is None:
    # Fall back to reading frontend/.env
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                break

API = f"{BASE_URL}/api"
TESTER_EMAIL = "tester@orbus.test"
TESTER_PASSWORD = "password123"


# ─── Health ────────────────────────────────────────────────────────────────────
class TestHealth:
    def test_health_ok(self):
        r = requests.get(f"{API}/health", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["env"] == "development"

    def test_openapi(self):
        r = requests.get(f"{API}/openapi.json", timeout=15)
        assert r.status_code == 200
        assert "openapi" in r.json()


# ─── Auth: register ───────────────────────────────────────────────────────────
def _rand_email():
    return f"test_{uuid.uuid4().hex[:10]}@orbus.test"


class TestRegister:
    def test_register_success(self):
        email = _rand_email()
        payload = {"email": email.upper(), "username": "tu_" + uuid.uuid4().hex[:6], "password": "password123"}
        r = requests.post(f"{API}/auth/register", json=payload, timeout=15)
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["token_type"] == "bearer"
        assert isinstance(body["access_token"], str) and len(body["access_token"]) > 10
        user = body["user"]
        assert user["email"] == email.lower()  # normalized
        assert user["username"] == payload["username"]
        assert user["is_admin"] is False
        assert "id" in user and "created_at" in user

        # Persistence: /auth/me works with returned token
        me = requests.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"}, timeout=15)
        assert me.status_code == 200
        assert me.json()["user"]["email"] == email.lower()

    def test_register_duplicate_email_409(self):
        email = _rand_email()
        payload = {"email": email, "username": "dup_" + uuid.uuid4().hex[:6], "password": "password123"}
        r1 = requests.post(f"{API}/auth/register", json=payload, timeout=15)
        assert r1.status_code == 201

        payload2 = {"email": email, "username": "dup2_" + uuid.uuid4().hex[:6], "password": "password123"}
        r2 = requests.post(f"{API}/auth/register", json=payload2, timeout=15)
        assert r2.status_code == 409
        assert r2.json()["detail"] == "Email already registered"

    def test_register_short_password_400(self):
        r = requests.post(
            f"{API}/auth/register",
            json={"email": _rand_email(), "username": "shortpw", "password": "abc"},
            timeout=15,
        )
        assert r.status_code == 400

    def test_register_invalid_email_422(self):
        r = requests.post(
            f"{API}/auth/register",
            json={"email": "not-an-email", "username": "bademail", "password": "password123"},
            timeout=15,
        )
        assert r.status_code == 422


# ─── Auth: login ──────────────────────────────────────────────────────────────
class TestLogin:
    def test_login_tester_success(self):
        r = requests.post(
            f"{API}/auth/login",
            json={"email": TESTER_EMAIL, "password": TESTER_PASSWORD},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["token_type"] == "bearer"
        assert body["user"]["email"] == TESTER_EMAIL
        assert isinstance(body["access_token"], str)

    def test_login_wrong_password_401(self):
        r = requests.post(
            f"{API}/auth/login",
            json={"email": TESTER_EMAIL, "password": "wrongpass"},
            timeout=15,
        )
        assert r.status_code == 401
        assert r.json()["detail"] == "Invalid email or password"


# ─── Auth: me ─────────────────────────────────────────────────────────────────
class TestAuthMe:
    def test_me_no_header_401(self):
        r = requests.get(f"{API}/auth/me", timeout=15)
        assert r.status_code == 401
        assert r.json()["detail"] == "Not authenticated"

    def test_me_bogus_token_401(self):
        r = requests.get(f"{API}/auth/me", headers={"Authorization": "Bearer not.a.real.jwt"}, timeout=15)
        assert r.status_code == 401
        assert r.json()["detail"] == "Invalid token"

    def test_me_valid_token(self):
        login = requests.post(
            f"{API}/auth/login",
            json={"email": TESTER_EMAIL, "password": TESTER_PASSWORD},
            timeout=15,
        )
        token = login.json()["access_token"]
        r = requests.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert r.status_code == 200
        assert r.json()["user"]["email"] == TESTER_EMAIL


# ─── Guilds ───────────────────────────────────────────────────────────────────
@pytest.fixture
def fresh_user_token():
    """Create a brand-new user and return their JWT."""
    payload = {
        "email": _rand_email(),
        "username": "gu_" + uuid.uuid4().hex[:6],
        "password": "password123",
    }
    r = requests.post(f"{API}/auth/register", json=payload, timeout=15)
    assert r.status_code == 201
    return r.json()["access_token"]


class TestGuilds:
    def test_get_my_guild_404_when_none(self, fresh_user_token):
        r = requests.get(
            f"{API}/guilds/me",
            headers={"Authorization": f"Bearer {fresh_user_token}"},
            timeout=15,
        )
        assert r.status_code == 404
        assert r.json()["detail"] == "No guild found for this user"

    def test_create_guild_success_and_persistence(self, fresh_user_token):
        h = {"Authorization": f"Bearer {fresh_user_token}"}
        name = "TEST_Guild_" + uuid.uuid4().hex[:6]
        r = requests.post(
            f"{API}/guilds",
            json={"name": name, "description": "A test guild"},
            headers=h,
            timeout=15,
        )
        assert r.status_code == 201, r.text
        guild = r.json()["guild"]
        assert guild["name"] == name
        assert guild["description"] == "A test guild"
        assert guild["level"] == 1
        assert guild["reputation"] == 0
        assert guild["gold"] == 100
        assert "id" in guild and "owner_user_id" in guild and "created_at" in guild

        # GET /guilds/me → must return same guild
        g = requests.get(f"{API}/guilds/me", headers=h, timeout=15)
        assert g.status_code == 200
        fetched = g.json()["guild"]
        assert fetched["id"] == guild["id"]
        assert fetched["name"] == name

    def test_create_guild_second_time_400(self, fresh_user_token):
        h = {"Authorization": f"Bearer {fresh_user_token}"}
        name = "TEST_G_" + uuid.uuid4().hex[:6]
        r1 = requests.post(f"{API}/guilds", json={"name": name}, headers=h, timeout=15)
        assert r1.status_code == 201

        r2 = requests.post(
            f"{API}/guilds",
            json={"name": "TEST_Another_" + uuid.uuid4().hex[:6]},
            headers=h,
            timeout=15,
        )
        assert r2.status_code == 400
        assert r2.json()["detail"] == "You already own a guild"

    def test_create_guild_name_too_short_422(self, fresh_user_token):
        h = {"Authorization": f"Bearer {fresh_user_token}"}
        r = requests.post(f"{API}/guilds", json={"name": "ab"}, headers=h, timeout=15)
        assert r.status_code == 422

    def test_create_guild_name_too_long_422(self, fresh_user_token):
        h = {"Authorization": f"Bearer {fresh_user_token}"}
        r = requests.post(f"{API}/guilds", json={"name": "x" * 41}, headers=h, timeout=15)
        assert r.status_code == 422

    def test_create_guild_no_auth_401(self):
        r = requests.post(f"{API}/guilds", json={"name": "NoAuthGuild"}, timeout=15)
        assert r.status_code == 401
