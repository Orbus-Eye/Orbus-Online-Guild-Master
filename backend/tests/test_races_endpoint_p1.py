"""P1 races endpoint smoke test — network-based (no DB writes)."""
from __future__ import annotations

import os
from pathlib import Path

import httpx
import pytest
from dotenv import load_dotenv

load_dotenv(Path("/app/frontend/.env"))

BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL")
pytestmark = pytest.mark.skipif(
    not BACKEND_URL, reason="REACT_APP_BACKEND_URL not set"
)


@pytest.fixture(scope="module")
def api_base() -> str:
    return f"{BACKEND_URL}/api"


def test_list_races_returns_all_50(api_base: str) -> None:
    r = httpx.get(f"{api_base}/races", timeout=10.0)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 50
    assert len(data["races"]) == 50
    for race in data["races"]:
        assert race["slug"]
        assert race["name_it"]
        assert race["rarity"] in ("common", "uncommon", "rare", "epic")
        assert race["is_active"] is True
        assert race["is_playable"] is True


def test_list_races_filter_rarity_common(api_base: str) -> None:
    r = httpx.get(f"{api_base}/races", params={"rarity": "common"}, timeout=10.0)
    assert r.status_code == 200
    data = r.json()
    # Round 16 seed contract: 30 common
    assert data["total"] == 30, f"expected 30 common races, got {data['total']}"


def test_list_races_filter_rarity_epic(api_base: str) -> None:
    r = httpx.get(f"{api_base}/races", params={"rarity": "epic"}, timeout=10.0)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 2


def test_get_race_by_slug_ok(api_base: str) -> None:
    r = httpx.get(f"{api_base}/races/dhampir", timeout=10.0)
    assert r.status_code == 200
    body = r.json()
    assert body["race"]["slug"] == "dhampir"
    assert body["race"]["rarity"] == "epic"
    assert body["race"]["name_it"] == "Dhampir"


def test_get_race_by_slug_not_found(api_base: str) -> None:
    r = httpx.get(f"{api_base}/races/does_not_exist_slug", timeout=10.0)
    assert r.status_code == 404
    assert r.json().get("detail") == "race_not_found"


def test_races_endpoint_no_auth_required(api_base: str) -> None:
    """Public catalog: MUST NOT require auth."""
    r = httpx.get(f"{api_base}/races", timeout=10.0)
    assert r.status_code == 200
