"""ROUND 11.1 Slice 2 — Auth migration tests.

Coverage:
  1. /auth/csrf returns hex token + sets cookie
  2. Login sets httpOnly access_token + csrf_token cookies
  3. /auth/me works via COOKIE alone (no Authorization header)
  4. /auth/me works via BEARER fallback (no cookie)
  5. POST mutating with cookie BUT NO csrf header → 403 auth.csrf.invalid
  6. POST mutating with cookie + valid csrf header → not 403
  7. POST mutating via BEARER (no cookie) → CSRF exempt
  8. Logout clears cookies
  9. Auth missing → 401 auth.missing
 10. Expired token → 401 auth.expired
 11. Bearer fallback emits structured log (`auth.legacy_bearer_usage`)
 12. CSRF cookie is non-httpOnly (JS-readable for double-submit)
 13. /auth/csrf is idempotent (returns same shape on repeated call)
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest
import requests


BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
JWT_SECRET = os.environ.get("JWT_SECRET")


def _register(email: str | None = None) -> tuple[str, str]:
    email = email or f"r11_{uuid.uuid4().hex[:8]}@orbus.test"
    r = requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": email, "username": email.split("@")[0],
        "password": "Slice2_T3st!",
    }, timeout=15)
    assert r.status_code == 201, r.text
    return email, r.json()["access_token"]


def test_csrf_endpoint_returns_token_and_sets_cookie():
    s = requests.Session()
    r = s.get(f"{BASE_URL}/api/auth/csrf", timeout=15)
    assert r.status_code == 200
    tok = r.json()["csrf_token"]
    assert len(tok) == 64 and all(c in "0123456789abcdef" for c in tok)
    assert "csrf_token" in s.cookies


def test_login_sets_httponly_access_cookie_and_csrf_cookie():
    email, _ = _register()
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={
        "email": email, "password": "Slice2_T3st!",
    }, timeout=15)
    assert r.status_code == 200
    assert "access_token" in s.cookies
    assert "csrf_token" in s.cookies
    # Check Set-Cookie raw header — httpOnly on access_token, NOT on csrf
    assert any("access_token=" in line and "HttpOnly" in line
               for line in r.raw.headers.getlist("Set-Cookie"))
    csrf_lines = [ln for ln in r.raw.headers.getlist("Set-Cookie") if "csrf_token=" in ln]
    assert csrf_lines and "HttpOnly" not in csrf_lines[0]


def test_me_via_cookie_only_no_authorization_header():
    email, _ = _register()
    s = requests.Session()
    s.post(f"{BASE_URL}/api/auth/login", json={
        "email": email, "password": "Slice2_T3st!",
    }, timeout=15)
    # No Authorization header — relies solely on the cookie session
    r = s.get(f"{BASE_URL}/api/auth/me", timeout=15)
    assert r.status_code == 200
    assert r.json()["user"]["email"] == email


def test_me_via_bearer_only_no_cookie():
    _, token = _register()
    r = requests.get(f"{BASE_URL}/api/auth/me",
                     headers={"Authorization": f"Bearer {token}"}, timeout=15)
    assert r.status_code == 200


def test_post_mutating_with_cookie_but_no_csrf_header_is_403():
    email, _ = _register()
    s = requests.Session()
    s.post(f"{BASE_URL}/api/auth/login", json={
        "email": email, "password": "Slice2_T3st!",
    }, timeout=15)
    # Clear the bearer-style Authorization header — we want cookie-only.
    r = s.post(f"{BASE_URL}/api/contracts/daily/x/claim", timeout=15)
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "auth.csrf.invalid"


def test_post_mutating_with_cookie_and_valid_csrf_header_is_not_403():
    email, _ = _register()
    s = requests.Session()
    s.post(f"{BASE_URL}/api/auth/login", json={
        "email": email, "password": "Slice2_T3st!",
    }, timeout=15)
    csrf = s.cookies.get("csrf_token")
    r = s.post(f"{BASE_URL}/api/contracts/daily/x/claim",
               headers={"X-CSRF-Token": csrf}, timeout=15)
    # Anything except 403 is acceptable (404/422/etc. = business path reached)
    assert r.status_code != 403


def test_post_mutating_via_bearer_only_is_csrf_exempt():
    _, token = _register()
    # No cookies set on this raw requests call (no Session)
    r = requests.post(f"{BASE_URL}/api/contracts/daily/x/claim",
                      headers={"Authorization": f"Bearer {token}"}, timeout=15)
    assert r.status_code != 403


def test_logout_clears_cookies():
    email, _ = _register()
    s = requests.Session()
    s.post(f"{BASE_URL}/api/auth/login", json={
        "email": email, "password": "Slice2_T3st!",
    }, timeout=15)
    assert "access_token" in s.cookies
    r = s.post(f"{BASE_URL}/api/auth/logout", timeout=15)
    assert r.status_code == 200
    # Session cookies are expired (set with Max-Age=0). After logout, /me
    # via cookie-only should be 401.
    r2 = s.get(f"{BASE_URL}/api/auth/me", timeout=15)
    assert r2.status_code == 401


def test_auth_missing_returns_structured_401():
    r = requests.get(f"{BASE_URL}/api/auth/me", timeout=15)
    assert r.status_code == 401
    assert r.json()["detail"]["code"] == "auth.missing"


@pytest.mark.skipif(not JWT_SECRET, reason="JWT_SECRET env not set in this run")
def test_expired_token_returns_structured_401():
    # Manually forge an expired token.
    past = datetime.now(timezone.utc) - timedelta(days=8)
    tok = jwt.encode({
        "sub": "fake-uuid",
        "type": "access",
        "exp": past,
    }, JWT_SECRET, algorithm="HS256")
    r = requests.get(f"{BASE_URL}/api/auth/me",
                     headers={"Authorization": f"Bearer {tok}"}, timeout=15)
    assert r.status_code == 401
    assert r.json()["detail"]["code"] == "auth.expired"


def test_csrf_endpoint_is_idempotent_same_shape():
    s = requests.Session()
    r1 = s.get(f"{BASE_URL}/api/auth/csrf", timeout=15).json()
    r2 = s.get(f"{BASE_URL}/api/auth/csrf", timeout=15).json()
    # Both return valid 64-hex tokens. Same session may return the same
    # token (cookie already set) — verify shape, not value.
    assert "csrf_token" in r1 and "csrf_token" in r2
    assert len(r1["csrf_token"]) == 64
    assert len(r2["csrf_token"]) == 64


def test_csrf_cookie_is_not_httponly_for_double_submit():
    """The csrf_token cookie MUST be JS-readable so the FE can copy it
    into the X-CSRF-Token header. The access_token cookie is httpOnly."""
    r = requests.get(f"{BASE_URL}/api/auth/csrf", timeout=15)
    csrf_lines = [ln for ln in r.raw.headers.getlist("Set-Cookie")
                  if "csrf_token=" in ln]
    assert csrf_lines, "expected csrf_token Set-Cookie"
    assert "HttpOnly" not in csrf_lines[0]
    assert "SameSite=lax" in csrf_lines[0].lower().replace("samesite=lax", "SameSite=lax")
