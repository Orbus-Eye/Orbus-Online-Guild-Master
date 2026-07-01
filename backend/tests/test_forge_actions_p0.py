"""P0 Forge routes smoke — Round 16.x post-recovery.

Verifies that the 5 forge action endpoints on `POST /api/inventory/{instance_id}/*`
are **registered** (i.e. do NOT return 404 route-not-found), and that the
authorization/feature-gate layer answers with the expected structured error.

Rationale
---------
The user-facing "Forgia 404" P0 was caused by the frontend calling
non-existent legacy paths (`/api/forge/refine`, ...). The backend has
always exposed the correct routes under `/api/inventory/{instance_id}/…`
(see `app/forge/routes.py`). Frontend was already fixed in a prior
`search_replace` pass to hit the correct URLs. This file verifies the
**contract**, not the DB state, so it is safe to run without polluting
`orbus_r16` (no writes, no fixtures).

Design decisions
----------------
- Uses `REACT_APP_BACKEND_URL` (external preview URL) via `httpx.Client`
  rather than `TestClient(app)` to avoid importing the app graph in the
  test session (which itself would trigger DB writes via lifespan seeds).
- Uses the pre-seeded `tester@orbus.test / password123` account — no
  new users/guilds created.
- All assertions target HTTP status + response `detail.code`, never DB.
- If the network is unreachable (offline dev), the whole module is
  `pytest.skip`-ped so the test never becomes a false-negative gate.
"""
from __future__ import annotations

import os
from pathlib import Path

import httpx
import pytest
from dotenv import load_dotenv

# Load /app/frontend/.env to reach REACT_APP_BACKEND_URL (single source of truth).
load_dotenv(Path("/app/frontend/.env"))

BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL")
TESTER_EMAIL = "tester@orbus.test"
TESTER_PASSWORD = "password123"

pytestmark = pytest.mark.skipif(
    not BACKEND_URL,
    reason="REACT_APP_BACKEND_URL not set — skipping network-based forge P0 test",
)


@pytest.fixture(scope="module")
def api_base() -> str:
    return f"{BACKEND_URL}/api"


@pytest.fixture(scope="module")
def bearer_token(api_base: str) -> str:
    """Login once per module. If backend unreachable, skip whole file."""
    try:
        r = httpx.post(
            f"{api_base}/auth/login",
            json={"email": TESTER_EMAIL, "password": TESTER_PASSWORD},
            timeout=10.0,
        )
    except httpx.HTTPError as exc:
        pytest.skip(f"backend unreachable at {api_base}: {exc}")
    assert r.status_code == 200, f"login failed: HTTP {r.status_code} {r.text}"
    data = r.json()
    assert "access_token" in data, "login response missing access_token"
    return data["access_token"]


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ─────────────────────────────────────────────────────────────────────────────
# Contract assertions — each endpoint must NOT be a 404-route-not-found.
# Acceptable responses (with tester@orbus.test on `orbus_r16` post-recovery):
#   • 423 feature.locked (Fucina not upgraded — expected on fresh guild)
#   • 404 with detail == "inventory instance not found" (route exists,
#     just no matching item) — only for `enchant-options` which has no
#     `require_unlocked` guard.
# Explicitly rejected: HTTP 404 with detail == "Not Found" (FastAPI's
# default for missing routes) → this is the exact symptom of the P0 bug.
# ─────────────────────────────────────────────────────────────────────────────

INSTANCE_ID_STUB = "p0-nonexistent-instance-id"


def _assert_route_registered(resp: httpx.Response, endpoint: str) -> None:
    """Route must not be missing. 404 is allowed ONLY when it's a domain 404."""
    assert resp.status_code != 405, f"{endpoint} → 405 Method Not Allowed (wrong verb registered)"
    if resp.status_code == 404:
        body = resp.json()
        detail = body.get("detail")
        # FastAPI missing-route default: {"detail": "Not Found"}
        assert detail != "Not Found", (
            f"{endpoint} → HTTP 404 with default detail 'Not Found' — "
            f"route is NOT registered! This is the exact P0 bug we're guarding."
        )
        # Any structured 404 (e.g. "inventory instance not found") is fine:
        # it means the router matched, business logic returned domain 404.


def test_forge_refine_route_registered(api_base: str, bearer_token: str) -> None:
    r = httpx.post(
        f"{api_base}/inventory/{INSTANCE_ID_STUB}/refine",
        headers=_headers(bearer_token),
        timeout=10.0,
    )
    _assert_route_registered(r, "POST /api/inventory/{id}/refine")
    # On a fresh guild, we expect feature.locked (423) OR domain 404.
    assert r.status_code in (404, 423), f"unexpected status {r.status_code}: {r.text}"
    if r.status_code == 423:
        assert r.json()["detail"]["code"] == "feature.locked"


def test_forge_enchant_route_registered(api_base: str, bearer_token: str) -> None:
    r = httpx.post(
        f"{api_base}/inventory/{INSTANCE_ID_STUB}/enchant",
        headers=_headers(bearer_token),
        json={"enchant_slug": "irrelevant"},
        timeout=10.0,
    )
    _assert_route_registered(r, "POST /api/inventory/{id}/enchant")
    assert r.status_code in (404, 423), f"unexpected status {r.status_code}: {r.text}"


def test_forge_disenchant_route_registered(api_base: str, bearer_token: str) -> None:
    r = httpx.post(
        f"{api_base}/inventory/{INSTANCE_ID_STUB}/disenchant",
        headers=_headers(bearer_token),
        timeout=10.0,
    )
    _assert_route_registered(r, "POST /api/inventory/{id}/disenchant")
    assert r.status_code in (404, 423), f"unexpected status {r.status_code}: {r.text}"


def test_forge_reroll_affixes_route_registered(api_base: str, bearer_token: str) -> None:
    r = httpx.post(
        f"{api_base}/inventory/{INSTANCE_ID_STUB}/reroll-affixes",
        headers=_headers(bearer_token),
        timeout=10.0,
    )
    _assert_route_registered(r, "POST /api/inventory/{id}/reroll-affixes")
    assert r.status_code in (404, 423), f"unexpected status {r.status_code}: {r.text}"


def test_forge_enchant_options_route_registered(api_base: str, bearer_token: str) -> None:
    """`enchant-options` has no feature-lock guard, so on stub id it must be
    a structured domain 404 ("inventory instance not found")."""
    r = httpx.post(
        f"{api_base}/inventory/{INSTANCE_ID_STUB}/enchant-options",
        headers=_headers(bearer_token),
        timeout=10.0,
    )
    _assert_route_registered(r, "POST /api/inventory/{id}/enchant-options")
    assert r.status_code == 404
    assert r.json().get("detail") == "inventory instance not found"


def test_forge_routes_require_auth(api_base: str) -> None:
    """Sanity: without a bearer token, endpoints must reject with 401,
    NOT with 404 route-not-found."""
    r = httpx.post(
        f"{api_base}/inventory/{INSTANCE_ID_STUB}/refine",
        timeout=10.0,
    )
    assert r.status_code == 401, f"expected 401 without auth, got {r.status_code}: {r.text}"
    body = r.json()
    assert body.get("detail", {}).get("code") == "auth.missing"
