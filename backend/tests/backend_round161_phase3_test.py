"""ROUND 16.1 Phase 3 — Class Halls enrichment + Auto-Equip bilingual.

5 end-to-end checks via the FastAPI app (tester guild fixture).
"""
from __future__ import annotations

import os
import pytest
import requests

from app.equipment.auto_equip import auto_equip_adventurer


API_BASE = os.environ.get("API_BASE_URL") or "http://localhost:8001"


@pytest.fixture(scope="module")
def auth_headers():
    r = requests.post(
        f"{API_BASE}/api/auth/login",
        json={"email": "tester@orbus.test", "password": "password123"},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ── T01: GET /api/class-halls returns 11 halls + kpi + enriched fields ────
def test_t01_class_halls_enriched(auth_headers):
    r = requests.get(f"{API_BASE}/api/class-halls",
                     headers=auth_headers, timeout=10)
    assert r.status_code == 200, r.text
    payload = r.json()
    halls = payload["halls"]
    assert isinstance(halls, list) and len(halls) >= 11
    kpi = payload.get("kpi") or {}
    for key in ("halls_unlocked", "halls_total", "specs_unlocked", "specs_total"):
        assert key in kpi
    # Each hall must carry the new fields.
    for h in halls:
        for key in ("adventurers_of_class", "available_to_specialize",
                    "top_adventurers", "specializations", "bonuses",
                    "unlock_hint_it", "unlock_hint_en"):
            assert key in h, f"hall {h['class_slug']} missing {key}"
        # Top 3 has ≤3 entries with required fields.
        assert len(h["top_adventurers"]) <= 3
        for a in h["top_adventurers"]:
            assert {"id", "name", "level", "total_power"} <= set(a)
        # Specializations: 3 with bilingual names.
        assert len(h["specializations"]) == 3
        for s in h["specializations"]:
            assert "name_it" in s and "name_en" in s
            assert "is_unlocked" in s
        # Counts coherence.
        assert h["available_to_specialize"] <= h["adventurers_of_class"]


# ── T02: Auto-equip response carries bilingual reasons + delta ────────────
def test_t02_auto_equip_bilingual(auth_headers):
    r_adv = requests.get(f"{API_BASE}/api/adventurers",
                         headers=auth_headers, timeout=10)
    advs = r_adv.json()["adventurers"]
    assert advs, "tester guild must have adventurers"
    # Pick one with low equipment count (≥1 swap likely available).
    target = sorted(advs, key=lambda a: sum(
        1 for v in (a.get("equipment") or {}).values() if v))[0]
    r = requests.post(
        f"{API_BASE}/api/adventurers/{target['id']}/auto-equip",
        headers=auth_headers, timeout=10)
    assert r.status_code in (200, 201), r.text
    s = r.json()
    for key in ("score_before", "score_after", "score_delta",
                "reasons", "unchanged_slots_detail", "primary_stat"):
        assert key in s, f"missing {key} in auto-equip response"
    assert s["score_delta"] == s["score_after"] - s["score_before"]
    # Every reason must carry bilingual fields.
    for rs in s["reasons"]:
        for k in ("slot", "reason_it", "reason_en", "stat_delta",
                  "primary_stat", "primary_gain"):
            assert k in rs, f"reason missing {k}"
        assert isinstance(rs["reason_it"], str) and len(rs["reason_it"]) > 3
        assert isinstance(rs["reason_en"], str) and len(rs["reason_en"]) > 3
        assert rs["reason_it"] != rs["reason_en"]
    # Unchanged slots also bilingual.
    for u in s["unchanged_slots_detail"]:
        assert "reason_it" in u and "reason_en" in u


# ── T03: Auto-equip is idempotent: 2nd call yields swaps_count == 0 ────────
def test_t03_auto_equip_idempotent(auth_headers):
    r_adv = requests.get(f"{API_BASE}/api/adventurers",
                         headers=auth_headers, timeout=10)
    advs = r_adv.json()["adventurers"]
    if not advs:
        pytest.skip("no adventurers")
    target = advs[0]
    # First call (may swap or not).
    requests.post(f"{API_BASE}/api/adventurers/{target['id']}/auto-equip",
                  headers=auth_headers, timeout=10)
    # Second call MUST be 0 swaps + unchanged_slots_detail populated.
    r = requests.post(
        f"{API_BASE}/api/adventurers/{target['id']}/auto-equip",
        headers=auth_headers, timeout=10)
    s = r.json()
    assert s["swaps_count"] == 0, f"expected 0 swaps on 2nd call, got {s['swaps_count']}"
    # Unchanged detail must exist (covers every slot) OR be empty when
    # there is literally no compatible candidate at all (returns warnings).
    assert isinstance(s["unchanged_slots_detail"], list)


# ── T04: KPI totals match the halls count ─────────────────────────────────
def test_t04_kpi_consistency(auth_headers):
    r = requests.get(f"{API_BASE}/api/class-halls",
                     headers=auth_headers, timeout=10)
    payload = r.json()
    halls = payload["halls"]
    kpi = payload["kpi"]
    assert kpi["halls_total"] == len(halls)
    assert kpi["specs_total"] == len(halls) * 3
    assert kpi["halls_unlocked"] == sum(1 for h in halls if h.get("is_unlocked"))
    expected_specs = sum(len(h.get("unlocked_specializations") or [])
                         for h in halls)
    assert kpi["specs_unlocked"] == expected_specs


# ── T05: empty-state contract — /api/expeditions exposes a list field ─────
# This test guarantees the FE can safely render an "empty" CTA when no
# expedition is present (key shape used by the FE empty-state).
def test_t05_expeditions_list_shape(auth_headers):
    r = requests.get(f"{API_BASE}/api/expeditions",
                     headers=auth_headers, timeout=10)
    assert r.status_code == 200
    data = r.json()
    # The FE checks `expeditions` array → ensure it always exists, even empty.
    assert "expeditions" in data
    assert isinstance(data["expeditions"], list)


# ── T06 (bonus): unlock-specialization stays idempotent ───────────────────
def test_t06_unlock_idempotent(auth_headers):
    halls = requests.get(f"{API_BASE}/api/class-halls",
                         headers=auth_headers, timeout=10).json()["halls"]
    target = next((h for h in halls
                   if h["is_unlocked"]
                   and h.get("specializations")
                   and h["specializations"][0]["is_unlockable"]), None)
    if not target:
        pytest.skip("no unlockable spec on tester guild")
    spec = target["specializations"][0]
    payload = {"specialization_slug": spec["slug"]}
    r1 = requests.post(
        f"{API_BASE}/api/class-halls/{target['class_slug']}/unlock-specialization",
        json=payload, headers=auth_headers, timeout=10)
    assert r1.status_code in (200, 201), r1.text
    r2 = requests.post(
        f"{API_BASE}/api/class-halls/{target['class_slug']}/unlock-specialization",
        json=payload, headers=auth_headers, timeout=10)
    assert r2.status_code in (200, 201), r2.text
    after = r2.json()["hall"]
    assert spec["slug"] in (after.get("unlocked_specializations") or [])
