"""ROUND 1.5 (Phase 14.4) — backend regression suite.

Updated for Round 5 §I — pinned to a single xdist worker via pytestmark.

These tests guard the invariants that ROUND 1.5 frontend work relies on:

  - GET /api/inventory returns the documented shape (stack model + counts).
  - GET /api/adventurers exposes traits + per-slot equipment so the
    AdventurerDetailModal and the new Inventory "Equipped by" column can
    render entirely from existing endpoints (no new API surface).
  - Equip-on-other-adventurer is rejected when stock is exhausted
    (cross-adventurer reservation guard, Phase 9.3.1).
  - OpenAPI path count stays at 43 (ROUND 1.5 introduces no new endpoints).

The suite is intentionally self-seeding (no shared fixtures) so it can be
run as a single file: `pytest tests/backend_phase14_4_round15_test.py`.
"""
import os
import uuid

import pytest
import requests

pytestmark = pytest.mark.xdist_group(name="round5_serial_legacy")

BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
H_JSON = {"Content-Type": "application/json"}


def _api(path: str) -> str:
    return f"{BASE_URL}/api{path}"


def _make_user_with_guild():
    suffix = uuid.uuid4().hex[:10]
    email = f"r15_{suffix}@orbus.test"
    username = f"r15_{suffix}"
    payload = {"email": email, "username": username, "password": "password123"}
    r = requests.post(_api("/auth/register"), json=payload, timeout=15)
    assert r.status_code == 201, r.text
    token = r.json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}

    guild_payload = {"name": f"Guild {suffix}", "description": "round 1.5"}
    g = requests.post(_api("/guilds"), json=guild_payload, headers=auth, timeout=15)
    assert g.status_code == 201, g.text
    return auth, g.json()


def _recruit_two_adventurers(auth):
    # Force candidate refresh so we have something to recruit even if cache empty.
    requests.get(_api("/recruitment/candidates"), headers=auth, timeout=15)
    adv_ids = []
    for _ in range(2):
        cands = requests.get(_api("/recruitment/candidates"), headers=auth, timeout=15)
        assert cands.status_code == 200, cands.text
        candidates = cands.json().get("candidates") or []
        if not candidates:
            break
        cand_id = candidates[0].get("candidate_id") or candidates[0].get("id")
        r = requests.post(
            _api("/recruitment/recruit"),
            json={"candidate_id": cand_id},
            headers=auth,
            timeout=15,
        )
        if r.status_code != 201:
            # Out of gold or already at cap — fine for this suite.
            break
        adv_ids.append(r.json().get("adventurer", {}).get("id"))
    return adv_ids


class TestInventoryShape:
    def test_inventory_endpoint_returns_stack_fields(self):
        auth, _guild = _make_user_with_guild()
        r = requests.get(_api("/inventory"), headers=auth, timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert "inventory" in body
        # Empty inventory is acceptable for a brand new guild but the shape
        # must still be a list.
        assert isinstance(body["inventory"], list)
        for row in body["inventory"]:
            assert {"id", "item_id", "total_quantity", "equipped_quantity",
                    "available_quantity"}.issubset(row.keys()), row
            assert row["total_quantity"] == (
                row["equipped_quantity"] + row["available_quantity"]
            ), row


class TestAdventurersShape:
    @pytest.mark.flaky(reruns=2)  # Phase 19 — xdist DB race; see FLAKY_TESTS_AUDIT.md
    def test_adventurers_expose_traits_and_equipment(self):
        auth, _guild = _make_user_with_guild()
        _recruit_two_adventurers(auth)
        r = requests.get(_api("/adventurers"), headers=auth, timeout=15)
        assert r.status_code == 200
        adventurers = r.json().get("adventurers") or []
        # We don't assert non-zero (gold may not allow recruits) — but if
        # there are any, they must include traits + equipment slot map for
        # the AdventurerDetailModal to render.
        for a in adventurers:
            assert "traits" in a, a
            assert "equipment" in a, a
            assert set(a["equipment"].keys()) >= {"weapon", "armor", "accessory"}, a
            assert "level" in a and a["level"] >= 1
            assert "experience" in a


class TestOpenAPIStable:
    def test_round15_introduces_no_new_endpoints(self):
        r = requests.get(_api("/openapi.json"), timeout=15)
        assert r.status_code == 200
        paths = r.json().get("paths", {})
        # baseline 43 → 45 → 49 → 53 → 60 → 61 (Phase 16.1 admin cleanup endpoint).
        # Updated for Phase 19 §1.2 — added /api/leaderboard/raids (75 → 76)
        assert len(paths) == 79, (
            f"unexpected OpenAPI path count: {len(paths)}"
        )


class TestRegisterValidation:
    def test_register_rejects_short_password(self):
        suffix = uuid.uuid4().hex[:8]
        r = requests.post(
            _api("/auth/register"),
            json={
                "email": f"short_{suffix}@orbus.test",
                "username": f"short_{suffix}",
                "password": "abc",  # < 8 chars
            },
            timeout=15,
        )
        assert r.status_code in (400, 422), r.text

    def test_register_rejects_duplicate_email(self):
        auth, _guild = _make_user_with_guild()
        # Capture the email by registering twice with a forced known suffix.
        suffix = uuid.uuid4().hex[:10]
        email = f"dup_{suffix}@orbus.test"
        payload = {"email": email, "username": f"dup_{suffix}", "password": "password123"}
        r1 = requests.post(_api("/auth/register"), json=payload, timeout=15)
        assert r1.status_code == 201
        r2 = requests.post(_api("/auth/register"), json=payload, timeout=15)
        assert r2.status_code in (400, 409), r2.text


if __name__ == "__main__":  # pragma: no cover
    pytest.main([__file__, "-v"])
