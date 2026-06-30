"""ROUND 16.1 Phase 1 — Dashboard endpoints (suggestions / onboarding / daily-loop).

End-to-end tests via the FastAPI app (tester guild fixture).
"""
from __future__ import annotations

import os
import pytest
import requests


API_BASE = os.environ.get("API_BASE_URL") or "http://localhost:8001"


@pytest.fixture(scope="module")
def auth_headers():
    r = requests.post(
        f"{API_BASE}/api/auth/login",
        json={"email": "tester@orbus.test", "password": "password123"},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ── T01: /dashboard/suggestions shape ────────────────────────────────
def test_t01_suggestions_shape(auth_headers):
    r = requests.get(f"{API_BASE}/api/dashboard/suggestions",
                     headers=auth_headers, timeout=10)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)
    assert len(data["suggestions"]) <= 5
    for s in data["suggestions"]:
        for k in ("id", "priority", "title_it", "title_en", "cta_it",
                  "cta_en", "link", "icon"):
            assert k in s, f"missing {k} in suggestion {s.get('id')}"
        assert isinstance(s["priority"], int)


# ── T02: suggestions sorted by priority desc ────────────────────────
def test_t02_suggestions_sorted(auth_headers):
    r = requests.get(f"{API_BASE}/api/dashboard/suggestions",
                     headers=auth_headers, timeout=10)
    suggestions = r.json()["suggestions"]
    priorities = [s["priority"] for s in suggestions]
    assert priorities == sorted(priorities, reverse=True)


# ── T03: /dashboard/onboarding shape (8 steps) ──────────────────────
def test_t03_onboarding_eight_steps(auth_headers):
    r = requests.get(f"{API_BASE}/api/dashboard/onboarding",
                     headers=auth_headers, timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert data["total_count"] == 8
    assert len(data["steps"]) == 8
    expected_ids = {"create_guild", "view_roster", "recruit_one", "equip_one",
                     "first_run", "read_report", "visit_training", "visit_halls"}
    assert {s["id"] for s in data["steps"]} == expected_ids
    for s in data["steps"]:
        for k in ("id", "title_it", "title_en", "cta_it", "cta_en",
                  "link", "completed"):
            assert k in s
        assert isinstance(s["completed"], bool)
    # Step 1 is always completed (guild exists if we got here).
    create_guild = next(s for s in data["steps"] if s["id"] == "create_guild")
    assert create_guild["completed"] is True


# ── T04: tester guild is far past onboarding (most steps done) ──────
def test_t04_onboarding_tester_advanced(auth_headers):
    r = requests.get(f"{API_BASE}/api/dashboard/onboarding",
                     headers=auth_headers, timeout=10)
    data = r.json()
    # Tester has 40+ adventurers, expeditions, class halls — all 8 steps done.
    assert data["completed_count"] >= 6


# ── T05: /dashboard/daily-loop shape (6 items) ──────────────────────
def test_t05_daily_loop_shape(auth_headers):
    r = requests.get(f"{API_BASE}/api/dashboard/daily-loop",
                     headers=auth_headers, timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert data["total_count"] == 6
    assert len(data["items"]) == 6
    expected_ids = {"daily_expedition", "daily_recruit", "daily_auto_equip",
                     "daily_visit_halls", "daily_threat_run", "daily_market"}
    assert {it["id"] for it in data["items"]} == expected_ids
    for it in data["items"]:
        for k in ("id", "title_it", "title_en", "link", "completed"):
            assert k in it
    # date is today (YYYY-MM-DD)
    assert len(data["date"]) == 10
    assert data["date"][4] == "-" and data["date"][7] == "-"


# ── T06: dismiss onboarding endpoint ────────────────────────────────
def test_t06_dismiss_onboarding(auth_headers):
    r = requests.post(f"{API_BASE}/api/dashboard/onboarding/dismiss",
                      headers=auth_headers, json={}, timeout=10)
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is True
    # Verify it sticks.
    r2 = requests.get(f"{API_BASE}/api/dashboard/onboarding",
                      headers=auth_headers, timeout=10)
    assert r2.json()["dismissed"] is True
    # Re-enable for subsequent runs (DB cleanup).
    # We cannot directly toggle off via API; tolerate the state for now —
    # the next regression run is independent of this flag.


# ── T07: unauthenticated access blocked ─────────────────────────────
def test_t07_unauth_blocked():
    r = requests.get(f"{API_BASE}/api/dashboard/suggestions", timeout=10)
    assert r.status_code in (401, 403)
