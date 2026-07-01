"""ROUND 11.2 TASK 8 — SEO public pages backend coverage.

The SEO surfaces (`/traits`, `/stats`) are React routes — FastAPI never
serves them directly. The backend's job here is to keep the catalog
endpoints they consume **publicly reachable** (no Authorization header
required, no CSRF on GET) so a crawler-driven page load completes.

Two lightweight smoke tests:
  T8.BE.01 — /api/traits/catalog returns 200 anonymous with PII-safe shape.
  T8.BE.02 — /api/stats/catalog returns 200 anonymous with the 11 documented
             keys (strength, agility, intellect, endurance, faith, stamina,
             morale, level, experience, power_score, rarity).

These complement (not replace) `backend_round112_t6_catalog_test.py`
(5 tests) which already covers filter logic in depth.
"""
from __future__ import annotations

import os

import pytest
import requests

BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")


def test_t8_be_01_traits_catalog_anonymous_seo_ready():
    """A search-engine crawler hits /api/traits/catalog without any auth and
    must receive a 200 + a PII-safe payload usable for indexing."""
    r = requests.get(f"{BASE_URL}/api/traits/catalog", timeout=10)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "total" in body and "traits" in body
    assert isinstance(body["traits"], list)
    assert body["total"] >= 1
    # Each trait MUST carry the IT-first SEO shape (display_name_it +
    # description_it) — that's what the SEO page renders into <title>,
    # <meta description>, OG tags and the H1/H2 structure.
    sample = body["traits"][0]
    for required in ("id", "display_name_it", "description_it", "polarity", "rarity"):
        assert required in sample, f"Missing public SEO field: {required}"


def test_t8_be_02_stats_catalog_anonymous_seo_ready():
    """Crawler hits /api/stats/catalog anonymously and must get a 200 with
    every documented stat — used by the /stats SEO page hero + description."""
    r = requests.get(f"{BASE_URL}/api/stats/catalog", timeout=10)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "total" in body and "stats" in body
    keys = {s["key"] for s in body["stats"]}
    for required in (
        "strength", "agility", "intellect", "endurance", "faith",
        "stamina", "morale", "level", "experience", "power_score", "rarity",
    ):
        assert required in keys, f"Missing SEO stat key: {required}"
    # PWR synthesis row must be marked affects_pwr (used by the /stats
    # `Sintesi` group rendering).
    pwr_row = next((s for s in body["stats"] if s["key"] == "power_score"), None)
    assert pwr_row is not None
    assert pwr_row.get("affects_pwr") is True
