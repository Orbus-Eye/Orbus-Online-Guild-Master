"""ROUND 6B.2c bug fix verification tests.

Validates that expedition GET endpoint exposes a non-empty `adventurer_ids`
field so the frontend "Salva come squadra" button renders on historical
victorious expeditions.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://drain-dispatch.preview.emergentagent.com").rstrip("/")
TESTER_EMAIL = "tester@orbus.test"
TESTER_PASS = "password123"
HISTORIC_EXP_ID = "301b6f17-7347-41aa-9536-ebf132c51934"  # Sewer Nest victory


@pytest.fixture(scope="module")
def auth_token():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TESTER_EMAIL, "password": TESTER_PASS},
        timeout=15,
    )
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    data = r.json()
    assert "access_token" in data
    return data["access_token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


# --- Bug fix: historical expedition exposes adventurer_ids ---
def test_historic_expedition_returns_adventurer_ids(auth_headers):
    r = requests.get(f"{BASE_URL}/api/expeditions/{HISTORIC_EXP_ID}", headers=auth_headers, timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "expedition" in body
    exp = body["expedition"]
    ids = exp.get("adventurer_ids")
    assert isinstance(ids, list), f"adventurer_ids must be a list, got {type(ids)}"
    assert len(ids) > 0, "adventurer_ids must be non-empty for save-as-squad button to render"
    # Spec: 3 IDs for Sewer Nest (dungeon_3)
    assert len(ids) == 3, f"Expected 3 adventurer_ids, got {len(ids)}: {ids}"
    # All UUIDs (string and non-empty)
    for i in ids:
        assert isinstance(i, str) and len(i) > 0


def test_historic_expedition_is_victory(auth_headers):
    """The save-as-squad button only renders for isDone && result_summary == 'Success'."""
    r = requests.get(f"{BASE_URL}/api/expeditions/{HISTORIC_EXP_ID}", headers=auth_headers, timeout=15)
    assert r.status_code == 200
    exp = r.json()["expedition"]
    assert exp["status"] in ("completed",), f"expected completed status, got {exp['status']}"
    assert exp["result_summary"] == "Success", f"expected Success, got {exp['result_summary']}"


def test_adventurer_ids_match_members(auth_headers):
    """Reconstructed adventurer_ids should be consistent with expedition_members snapshot."""
    r = requests.get(f"{BASE_URL}/api/expeditions/{HISTORIC_EXP_ID}", headers=auth_headers, timeout=15)
    assert r.status_code == 200
    body = r.json()
    exp_ids = set(body["expedition"]["adventurer_ids"])
    member_ids = {m["adventurer_id"] for m in body["members"]}
    assert exp_ids == member_ids, f"adventurer_ids {exp_ids} should match member ids {member_ids}"


# --- Regression: list endpoint also includes adventurer_ids ---
def test_expeditions_list_includes_adventurer_ids(auth_headers):
    r = requests.get(f"{BASE_URL}/api/expeditions", headers=auth_headers, timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert "expeditions" in body
    # At least one expedition expected for tester. Field key must be present (may be empty list for list view).
    for exp in body["expeditions"]:
        # adventurer_ids should always be a list (possibly empty in list view for pre-6B.2c records)
        assert "adventurer_ids" in exp
        assert isinstance(exp["adventurer_ids"], list)


# --- API existence baseline ---
def test_health_check():
    r = requests.get(f"{BASE_URL}/api/health", timeout=10)
    assert r.status_code == 200
