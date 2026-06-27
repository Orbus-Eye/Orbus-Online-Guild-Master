"""Orbus Online: Guild Master — Phase 5 backend tests (security hardening).

Covers:
- Password regex (letter + digit)
- Refresh token issued on register/login
- /api/auth/refresh + /api/auth/logout
- Login lockout (5 fails -> HTTP 429)
- Password reset request + confirm (revokes refresh tokens)
- Admin dependency: /api/admin/* requires is_admin
"""
import os
import time
import uuid
import pytest
import requests
from pathlib import Path
from dotenv import load_dotenv

# ROUND 6B FASE A — load shared test env (gitignored)
load_dotenv(Path(__file__).resolve().parent / ".env.test", override=False)

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") if os.environ.get("REACT_APP_BACKEND_URL") else None
if BASE_URL is None:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                break

API = f"{BASE_URL}/api"
# ROUND 6B FASE A — credentials sourced from `tests/.env.test`. No literal
# fallback: a missing key trips a clear KeyError instead of silently using
# a committed string.
TESTER_EMAIL = os.environ["TEST_USER_EMAIL"]
TESTER_PASSWORD = os.environ["TEST_USER_PASSWORD"]
DEFAULT_TEST_PASSWORD = os.environ["TEST_DEFAULT_PASSWORD"]
# Two invalid passwords used by the regex tests (kept in env so the
# literal strings don't appear in source).
PW_MISSING_DIGIT = os.environ["TEST_PASSWORD_MISSING_DIGIT"]
PW_MISSING_LETTER = os.environ["TEST_PASSWORD_MISSING_LETTER"]
# Minimum-policy compliant password used by the positive-path regex test.
PW_VALID_MINIMAL = os.environ["TEST_PASSWORD_VALID_MINIMAL"]


def _rand_email(prefix="p5"):
    return f"{prefix}_{uuid.uuid4().hex[:10]}@orbus.test"


def _register(email=None, password=None, username=None):
    email = email or _rand_email()
    username = username or ("u_" + uuid.uuid4().hex[:6])
    pw = password if password is not None else DEFAULT_TEST_PASSWORD
    r = requests.post(
        f"{API}/auth/register",
        json={"email": email, "username": username, "password": pw},
        timeout=15,
    )
    return r, email, pw


# ─── Password regex ────────────────────────────────────────────────────────────
class TestPasswordRegex:
    def test_password_missing_digit_400(self):
        r, _, _ = _register(password=PW_MISSING_DIGIT)
        assert r.status_code == 400, r.text
        body = r.json()
        assert "letter" in body["detail"].lower() and "digit" in body["detail"].lower()

    def test_password_missing_letter_400(self):
        r, _, _ = _register(password=PW_MISSING_LETTER)
        assert r.status_code == 400, r.text
        assert "letter" in r.json()["detail"].lower()

    def test_password_min_length_400(self):
        r, _, _ = _register(password="a1b2c3")
        assert r.status_code == 400

    def test_password_valid_letter_digit_201(self):
        r, _, _ = _register(password=PW_VALID_MINIMAL)
        assert r.status_code == 201, r.text


# ─── Refresh token flow ────────────────────────────────────────────────────────
class TestRefreshToken:
    def test_register_returns_refresh_token(self):
        r, _, _ = _register()
        assert r.status_code == 201
        body = r.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert isinstance(body["refresh_token"], str)
        assert len(body["refresh_token"]) >= 20

    def test_login_returns_refresh_token(self):
        r, email, pw = _register()
        assert r.status_code == 201
        lg = requests.post(f"{API}/auth/login", json={"email": email, "password": pw}, timeout=15)
        assert lg.status_code == 200
        body = lg.json()
        assert "refresh_token" in body
        assert "access_token" in body

    def test_refresh_endpoint_returns_new_access(self):
        r, email, pw = _register()
        rt = r.json()["refresh_token"]
        rf = requests.post(f"{API}/auth/refresh", json={"refresh_token": rt}, timeout=15)
        assert rf.status_code == 200, rf.text
        body = rf.json()
        assert "access_token" in body
        assert body["user"]["email"] == email
        # New access token should authorize /auth/me
        me = requests.get(
            f"{API}/auth/me",
            headers={"Authorization": f"Bearer {body['access_token']}"},
            timeout=15,
        )
        assert me.status_code == 200

    def test_refresh_with_invalid_token_401(self):
        rf = requests.post(
            f"{API}/auth/refresh",
            json={"refresh_token": "definitely-not-a-real-token-xxxxxxxxxxxx"},
            timeout=15,
        )
        assert rf.status_code == 401

    def test_logout_revokes_refresh_token(self):
        r, _, _ = _register()
        rt = r.json()["refresh_token"]
        lo = requests.post(f"{API}/auth/logout", json={"refresh_token": rt}, timeout=15)
        assert lo.status_code == 200
        assert lo.json()["revoked"] is True
        # Subsequent refresh must 401
        rf = requests.post(f"{API}/auth/refresh", json={"refresh_token": rt}, timeout=15)
        assert rf.status_code == 401

    def test_multi_device_refresh_tokens(self):
        """Login twice → both refresh tokens should remain valid (multi-device)."""
        r, email, pw = _register()
        l1 = requests.post(f"{API}/auth/login", json={"email": email, "password": pw}, timeout=15).json()
        l2 = requests.post(f"{API}/auth/login", json={"email": email, "password": pw}, timeout=15).json()
        assert l1["refresh_token"] != l2["refresh_token"]
        rf1 = requests.post(f"{API}/auth/refresh", json={"refresh_token": l1["refresh_token"]}, timeout=15)
        rf2 = requests.post(f"{API}/auth/refresh", json={"refresh_token": l2["refresh_token"]}, timeout=15)
        assert rf1.status_code == 200
        assert rf2.status_code == 200


# ─── Login lockout ─────────────────────────────────────────────────────────────
class TestLoginLockout:
    def test_five_failed_logins_then_429(self):
        r, email, pw = _register()
        assert r.status_code == 201
        for _ in range(5):
            bad = requests.post(
                f"{API}/auth/login",
                json={"email": email, "password": "wrongpass"},
                timeout=15,
            )
            assert bad.status_code == 401
        # 6th try (even with correct pw) must be locked, with Retry-After header
        locked = requests.post(
            f"{API}/auth/login", json={"email": email, "password": pw}, timeout=15
        )
        assert locked.status_code == 429, locked.text
        assert "too many" in locked.json()["detail"].lower()
        # RFC 6585 / RFC 7231: Retry-After must be present and be a non-negative integer
        retry_after = locked.headers.get("Retry-After")
        assert retry_after is not None, "Retry-After header is required on 429"
        assert retry_after.isdigit(), f"Retry-After must be integer seconds, got {retry_after!r}"
        assert int(retry_after) > 0

    def test_successful_login_resets_attempts(self):
        r, email, pw = _register()
        # 3 fails, not enough to lock
        for _ in range(3):
            requests.post(
                f"{API}/auth/login",
                json={"email": email, "password": "wrongpass"},
                timeout=15,
            )
        # Successful login resets
        ok = requests.post(f"{API}/auth/login", json={"email": email, "password": pw}, timeout=15)
        assert ok.status_code == 200
        # Now 4 more fails should NOT lock (counter was reset)
        for _ in range(4):
            requests.post(
                f"{API}/auth/login",
                json={"email": email, "password": "wrongpass"},
                timeout=15,
            )
        # Login with correct creds still works
        ok2 = requests.post(f"{API}/auth/login", json={"email": email, "password": pw}, timeout=15)
        assert ok2.status_code == 200


# ─── Password reset ────────────────────────────────────────────────────────────
class TestPasswordReset:
    def test_reset_request_always_200(self):
        # Existing user
        r, email, _ = _register()
        ok = requests.post(
            f"{API}/auth/password-reset/request",
            json={"email": email},
            timeout=15,
        )
        assert ok.status_code == 200
        # Non-existing user → still 200 (no enumeration)
        no = requests.post(
            f"{API}/auth/password-reset/request",
            json={"email": _rand_email("ghost")},
            timeout=15,
        )
        assert no.status_code == 200

    def test_reset_confirm_with_invalid_token_400(self):
        bad = requests.post(
            f"{API}/auth/password-reset/confirm",
            json={"token": "totally-fake-token-zzz", "new_password": "newpass123"},
            timeout=15,
        )
        assert bad.status_code == 400

    def test_reset_confirm_full_flow(self):
        """Inserts a reset token directly via mongo so we can confirm the flow
        end-to-end without parsing backend logs.
        """
        import hashlib
        from datetime import datetime, timezone, timedelta
        from pymongo import MongoClient
        c = MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
        dbname = os.environ.get("DB_NAME", "test_database")
        # Load DB_NAME from backend/.env if env not set
        if "DB_NAME" not in os.environ:
            with open("/app/backend/.env") as f:
                for line in f:
                    if line.startswith("DB_NAME="):
                        dbname = line.split("=", 1)[1].strip().strip('"')
                        break
        db = c[dbname]

        r, email, _ = _register()
        user_id = r.json()["user"]["id"]
        rt_old = r.json()["refresh_token"]

        plain = "manualtok_" + uuid.uuid4().hex
        token_hash = hashlib.sha256(plain.encode()).hexdigest()
        now = datetime.now(timezone.utc)
        db.password_reset_tokens.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "token_hash": token_hash,
            "created_at": now,
            "expires_at": now + timedelta(minutes=60),
            "used": False,
        })

        # Confirm
        cf = requests.post(
            f"{API}/auth/password-reset/confirm",
            json={"token": plain, "new_password": "brandnew99"},
            timeout=15,
        )
        assert cf.status_code == 200, cf.text

        # Old password should fail
        old = requests.post(f"{API}/auth/login", json={"email": email, "password": DEFAULT_TEST_PASSWORD}, timeout=15)
        assert old.status_code == 401
        # New password should work
        nw = requests.post(f"{API}/auth/login", json={"email": email, "password": "brandnew99"}, timeout=15)
        assert nw.status_code == 200

        # Previously-issued refresh token must be revoked
        rf = requests.post(f"{API}/auth/refresh", json={"refresh_token": rt_old}, timeout=15)
        assert rf.status_code == 401

        # The reset token cannot be reused
        again = requests.post(
            f"{API}/auth/password-reset/confirm",
            json={"token": plain, "new_password": "yetanother9"},
            timeout=15,
        )
        assert again.status_code == 400

    def test_reset_confirm_weak_password_400(self):
        bad = requests.post(
            f"{API}/auth/password-reset/confirm",
            json={"token": "anything", "new_password": "weakpass"},  # no digit
            timeout=15,
        )
        assert bad.status_code == 400


# ─── Admin dependency audit ────────────────────────────────────────────────────
class TestAdminDependency:
    @pytest.fixture(scope="class")
    def non_admin_token(self):
        r, _, _ = _register()
        return r.json()["access_token"]

    def test_admin_classes_requires_admin(self, non_admin_token):
        r = requests.get(
            f"{API}/admin/classes",
            headers={"Authorization": f"Bearer {non_admin_token}"},
            timeout=15,
        )
        assert r.status_code == 403

    def test_admin_dungeons_requires_admin(self, non_admin_token):
        r = requests.get(
            f"{API}/admin/dungeons",
            headers={"Authorization": f"Bearer {non_admin_token}"},
            timeout=15,
        )
        assert r.status_code == 403

    def test_admin_items_requires_admin(self, non_admin_token):
        r = requests.get(
            f"{API}/admin/items",
            headers={"Authorization": f"Bearer {non_admin_token}"},
            timeout=15,
        )
        assert r.status_code == 403

    def test_admin_traits_requires_admin(self, non_admin_token):
        r = requests.get(
            f"{API}/admin/traits",
            headers={"Authorization": f"Bearer {non_admin_token}"},
            timeout=15,
        )
        assert r.status_code == 403

    def test_admin_missing_token_401(self):
        r = requests.get(f"{API}/admin/classes", timeout=15)
        assert r.status_code == 401
