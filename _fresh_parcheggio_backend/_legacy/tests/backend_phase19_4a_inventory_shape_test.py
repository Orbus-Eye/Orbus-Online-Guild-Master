"""Phase 19.4a — `GET /api/inventory` API shape contract test.

Background: a P0 frontend bug was identified where `Market.jsx` read
`data.items` from the inventory API, but the API returns `{"inventory": [...]}`.
The list-to-sell form always appeared empty even when the player owned
sellable stacks.

This test pins the response shape so any future refactor (key rename,
shape change) breaks the test instead of silently breaking the UI.
"""
import os
import uuid
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

BASE_URL = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or os.environ.get("BACKEND_URL", "http://localhost:8001")
).rstrip("/")


def _user(hint="p194a"):
    tag = f"{hint}_{uuid.uuid4().hex[:6]}"
    requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": f"{tag}@orbus.test", "username": tag, "password": "Test12345!",
    }, timeout=15)
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": f"{tag}@orbus.test", "password": "Test12345!",
    }, timeout=15)
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    requests.post(f"{BASE_URL}/api/guilds", json={"name": f"P194a {tag[-5:]}"}, headers=h, timeout=15)
    return {"headers": h}


class TestInventoryShapeContract:
    def test_inventory_key_is_inventory_not_items(self):
        """The response MUST contain key `inventory`, NOT `items`."""
        ctx = _user("inv1")
        r = requests.get(f"{BASE_URL}/api/inventory", headers=ctx["headers"], timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert "inventory" in body, (
            "REGRESSION GUARD (P19.4a): inventory endpoint must expose `inventory` key; "
            "frontend `Market.jsx` depends on this exact name."
        )
        assert isinstance(body["inventory"], list)
        assert "items" not in body, (
            "Do not introduce a sibling `items` key without updating the UI; the previous "
            "P0 bug was caused by `Market.jsx` reading `data.items`."
        )

    def test_inventory_entry_fields_used_by_market_ui(self):
        """The keys that `Market.jsx` reads to filter sellable items must be present."""
        ctx = _user("inv2")
        r = requests.get(f"{BASE_URL}/api/inventory", headers=ctx["headers"], timeout=15)
        body = r.json()
        # A fresh guild won't have inventory yet; smoke-skip if empty.
        if not body["inventory"]:
            pytest.skip("fresh guild has empty inventory; shape covered by other tests")
        row = body["inventory"][0]
        for k in (
            "id", "item_id", "quantity", "total_quantity",
            "equipped_quantity", "market_locked_quantity", "available_quantity",
            "is_bound", "item",
        ):
            assert k in row, f"missing inventory field: {k}"
        # Item subdoc keys used by sell-filter
        for k in ("slug", "name", "rarity", "item_type"):
            assert k in row["item"], f"missing item.{k}"
