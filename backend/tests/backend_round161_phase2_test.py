"""ROUND 16.1 Phase 2 — Roster filter+sort + Dungeon Preview + Report narrative.

End-to-end tests via the FastAPI app (tester guild fixture).
Tester guild seeded by infra has ~40 adventurers across multiple classes,
specs, and roles — enough to verify filtering/sorting works correctly.
"""
from __future__ import annotations

import os
import pytest
import requests

from app.expeditions.report_builder import _build_why_narrative


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


# ── T01: class filter returns only matching class ────────────────────
def test_t01_class_filter_only_matches(auth_headers):
    # Pick a class present in the tester roster.
    r_all = requests.get(f"{API_BASE}/api/adventurers",
                         headers=auth_headers, timeout=10)
    assert r_all.status_code == 200
    all_advs = r_all.json()["adventurers"]
    assert len(all_advs) > 0, "tester guild should have adventurers"
    target_class = all_advs[0]["class_slug"]
    r = requests.get(
        f"{API_BASE}/api/adventurers?class_slug={target_class}",
        headers=auth_headers, timeout=10)
    assert r.status_code == 200
    filtered = r.json()["adventurers"]
    assert len(filtered) > 0, f"expected at least 1 {target_class}"
    assert all(a["class_slug"] == target_class for a in filtered), (
        "filter must return only the requested class")
    # And the filtered list must be a subset of the full list.
    assert len(filtered) <= len(all_advs)


# ── T02: improvable_equip filter returns a (typically) smaller subset ─
def test_t02_improvable_equip_subset(auth_headers):
    r_all = requests.get(f"{API_BASE}/api/adventurers",
                         headers=auth_headers, timeout=10)
    all_count = r_all.json()["total"]
    r = requests.get(
        f"{API_BASE}/api/adventurers?improvable_equip=true",
        headers=auth_headers, timeout=10)
    assert r.status_code == 200
    payload = r.json()
    assert payload["total"] <= all_count
    # Each returned adventurer must have <4 equipped slots.
    for a in payload["adventurers"]:
        eq = a.get("equipment") or {}
        equipped = sum(1 for v in eq.values() if v)
        assert equipped < 4, (
            f"adventurer {a.get('name')} has {equipped} equipped slots, "
            "should be <4 to qualify as improvable")


# ── T03: power_desc sort orders correctly ───────────────────────────
def test_t03_power_desc_sort(auth_headers):
    r = requests.get(
        f"{API_BASE}/api/adventurers?sort=power_desc",
        headers=auth_headers, timeout=10)
    assert r.status_code == 200
    advs = r.json()["adventurers"]
    assert len(advs) >= 2, "need at least 2 advs to assert ordering"
    powers = [
        (a.get("equipment_power") or 0) + (a.get("base_power") or 0)
        for a in advs
    ]
    # Strictly non-increasing (allow ties).
    for i in range(len(powers) - 1):
        assert powers[i] >= powers[i + 1], (
            f"power_desc broken at index {i}: {powers[i]} < {powers[i+1]}")


# ── T04: preview for void/undead dungeon includes threats + bonus ────
def test_t04_preview_void_dungeon_has_threats(auth_headers):
    # Need a 3-member team for `shadow-crypts`.
    r_adv = requests.get(f"{API_BASE}/api/adventurers",
                         headers=auth_headers, timeout=10)
    advs = [a for a in r_adv.json()["adventurers"] if a.get("is_available")]
    assert len(advs) >= 3
    team_ids = ",".join(a["id"] for a in advs[:3])
    r = requests.get(
        f"{API_BASE}/api/dungeons/shadow-crypts/preview?team_ids={team_ids}",
        headers=auth_headers, timeout=10)
    assert r.status_code == 200, r.text
    p = r.json()
    assert p.get("error") != "not_found"
    # Void/undead dungeons MUST carry threats.
    assert len(p["threats"]) > 0, "shadow-crypts must have threat_tags"
    for t in p["threats"]:
        for k in ("slug", "name_it", "name_en", "countered", "by"):
            assert k in t
    # Threat resolution applies on this dungeon.
    assert p["threat_resolution"] is not None
    assert p["threat_resolution"].get("applies") is True
    # FASE 2 (2026-08-08) — il cap 95 è stato rimosso: la curva
    # logistica arriva al 100% reale (min 5). Vedi
    # memory/fase2_design_bilanciamento.md.
    sc = p["success_chance"]
    assert isinstance(sc, int)
    assert 5 <= sc <= 100
    # Bilingual weakness suggestion: either both or neither.
    assert (p["weakness_suggestion_it"] is None) == (
        p["weakness_suggestion_en"] is None)


# ── T05: preview for non-void dungeon returns empty threats ──────────
def test_t05_preview_non_void_no_threats(auth_headers):
    r_adv = requests.get(f"{API_BASE}/api/adventurers",
                         headers=auth_headers, timeout=10)
    advs = [a for a in r_adv.json()["adventurers"] if a.get("is_available")]
    team_ids = ",".join(a["id"] for a in advs[:3])
    r = requests.get(
        f"{API_BASE}/api/dungeons/goblin-warrens/preview?team_ids={team_ids}",
        headers=auth_headers, timeout=10)
    assert r.status_code == 200, r.text
    p = r.json()
    # goblin-warrens has no threat_tags → threats list MUST be empty.
    assert p["threats"] == [], (
        f"goblin-warrens should have no threats, got {p['threats']}")
    # threat_resolution must be None (not applies).
    assert p["threat_resolution"] is None
    # Without threats there can be no weakness_suggestion.
    assert p["weakness_suggestion_it"] is None
    assert p["weakness_suggestion_en"] is None


# ── T06: report builder emits bilingual narrative_it/narrative_en ────
def test_t06_report_narrative_bilingual():
    """Unit test on `_build_why_narrative` — verifies it always emits
    non-empty IT and EN strings, with distinct content."""
    # Build a synthetic completed expedition + members payload.
    exp = {
        "status": "completed",
        "result_summary": "Success",
        "final_score": 60,
        "success_chance": 70,
        "team_power": 120,
        "threat_resolution": {
            "applies": True,
            "threats": ["void", "undead"],
            "threats_countered": ["void"],
            "success_bonus_pct": 6,
        },
    }
    members = [
        {"name_snapshot": "Lyra", "specialization_slug": "voidwarden",
         "class_name_snapshot": "Mage", "role_snapshot": "Caster"},
        {"name_snapshot": "Ortham", "class_name_snapshot": "Warrior",
         "role_snapshot": "Tank"},
        {"name_snapshot": "Sif", "class_name_snapshot": "Priest",
         "role_snapshot": "Healer"},
    ]
    narr_it = _build_why_narrative(
        lang="it", outcome="success", dungeon_name="Shadow Crypts",
        team_power=120, rec_power=100, exp=exp, members=members)
    narr_en = _build_why_narrative(
        lang="en", outcome="success", dungeon_name="Shadow Crypts",
        team_power=120, rec_power=100, exp=exp, members=members)
    assert isinstance(narr_it, str) and len(narr_it) > 20
    assert isinstance(narr_en, str) and len(narr_en) > 20
    # IT must mention an Italian-only word; EN must mention an EN-only word.
    assert ("riusc" in narr_it.lower()) or ("squadra" in narr_it.lower()) \
        or ("contromisure" in narr_it.lower())
    assert ("succeed" in narr_en.lower()) or ("party" in narr_en.lower()) \
        or ("counter" in narr_en.lower()) or ("team" in narr_en.lower())
    # Distinct content.
    assert narr_it != narr_en
    # Length budget (kept under ~600 chars).
    assert len(narr_it) <= 600
    assert len(narr_en) <= 600


# ── T07 (bonus): report endpoint exposes narrative on completed exp ─
def test_t07_report_endpoint_carries_narrative(auth_headers):
    """Smoke check: any completed expedition on the tester guild MUST
    expose `report_summary.narrative_it` and `narrative_en` keys."""
    r = requests.get(f"{API_BASE}/api/expeditions",
                     headers=auth_headers, timeout=10)
    assert r.status_code == 200
    completed = [e for e in r.json().get("expeditions", [])
                 if e.get("status") == "completed"]
    if not completed:
        pytest.skip("tester guild has no completed expeditions to check")
    exp_id = completed[0]["id"]
    r2 = requests.get(f"{API_BASE}/api/expeditions/{exp_id}",
                      headers=auth_headers, timeout=10)
    assert r2.status_code == 200
    rs = (r2.json() or {}).get("report_summary") or {}
    assert "narrative_it" in rs
    assert "narrative_en" in rs
    assert isinstance(rs["narrative_it"], str) and len(rs["narrative_it"]) > 5
    assert isinstance(rs["narrative_en"], str) and len(rs["narrative_en"]) > 5
