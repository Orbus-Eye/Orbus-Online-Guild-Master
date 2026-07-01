"""ROUND 11.2 EXT S3 Parte A — P1 double-spend fix coverage.

3 backend tests for the `available = quantity - market_locked_qty` gate
in `_atomic_debit_materials` and the matching enrichment.

Strategy: use the natural `expedition_board` Lv1→Lv2 path
(cost = 200g + 2× iron_shard). The starter guild always boots with
expedition_board at Lv 1 and we only need to put materials into the
single iron_shard inventory row to vary the scenario.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")


@pytest.fixture(scope="module")
def db():
    cli = MongoClient(MONGO_URL)
    yield cli[DB_NAME]
    cli.close()


def _new_guild() -> tuple[str, dict, str]:
    """Register fresh tester + create guild. Returns (token, user, guild_id)."""
    email = f"r112p1_{uuid.uuid4().hex[:8]}@orbus.test"
    r = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": email, "username": f"r112p1_{uuid.uuid4().hex[:6]}",
              "password": "password123"},
        timeout=10,
    )
    assert r.status_code in (200, 201), r.text
    token = r.json()["access_token"]
    user = r.json()["user"]
    r2 = requests.post(
        f"{BASE_URL}/api/guilds",
        json={"name": f"P1_{uuid.uuid4().hex[:6]}", "description": "P1"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    assert r2.status_code in (200, 201), r2.text
    return token, user, r2.json()["guild"]["id"]


def _seed_iron_shard(db, gid: str, total_qty: int, market_locked: int) -> str:
    """Upsert the single iron_shard inventory row for the guild."""
    iron = db.items.find_one({"slug": "iron_shard"}, {"_id": 0, "id": 1})
    db.inventory_items.update_one(
        {"guild_id": gid, "item_id": iron["id"]},
        {"$set": {
            "id": str(uuid.uuid4()),
            "guild_id": gid, "item_id": iron["id"],
            "instance_id": str(uuid.uuid4()),
            "quantity": total_qty,
            "market_locked_qty": market_locked,
            "is_bound": False, "refinement_level": 0,
            "enchants": [], "affixes": [], "reroll_count": 0,
            "acquired_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )
    # Make sure guild gold covers the 200g upgrade.
    db.guilds.update_one({"id": gid}, {"$inc": {"gold": 5000}})
    return iron["id"]


# ─── P1.01 ───────────────────────────────────────────────────────────────────
def test_p1_01_upgrade_with_listed_materials_blocked(db):
    token, _u, gid = _new_guild()
    # 2 iron_shard total, all 2 locked in auction → available = 0
    iron_id = _seed_iron_shard(db, gid, total_qty=2, market_locked=2)
    r = requests.post(
        f"{BASE_URL}/api/territory/upgrade",
        json={"structure_slug": "expedition_board"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    assert r.status_code == 422, r.text
    detail = r.json().get("detail", {})
    assert detail.get("code") == "resources.material_insufficient"
    assert detail.get("slug") == "iron_shard"
    assert int(detail.get("available", -1)) == 0, \
        f"available must report 0 (raw quantity was 2): got {detail.get('available')}"
    row = db.inventory_items.find_one({"guild_id": gid, "item_id": iron_id})
    assert row["quantity"] == 2
    assert row.get("market_locked_qty", 0) == 2


# ─── P1.02 ───────────────────────────────────────────────────────────────────
def test_p1_02_upgrade_consumes_only_available_not_listed(db):
    token, _u, gid = _new_guild()
    # 5 iron_shard total, 3 locked → available = 2 (matches required for Lv1→2)
    iron_id = _seed_iron_shard(db, gid, total_qty=5, market_locked=3)
    r = requests.post(
        f"{BASE_URL}/api/territory/upgrade",
        json={"structure_slug": "expedition_board"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    row = db.inventory_items.find_one({"guild_id": gid, "item_id": iron_id})
    # Consumed 2 from raw quantity (5 → 3); market_locked stays at 3 → available now 0.
    assert row["quantity"] == 3
    assert row.get("market_locked_qty", 0) == 3


# ─── P1.03 ───────────────────────────────────────────────────────────────────
def test_p1_03_territory_payload_shows_available_owned(db):
    token, _u, gid = _new_guild()
    # 10 iron_shard, 8 locked → available = 2.
    _seed_iron_shard(db, gid, total_qty=10, market_locked=8)
    r = requests.get(
        f"{BASE_URL}/api/territory",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    assert r.status_code == 200
    eb = r.json()["territory"]["structures"]["expedition_board"]
    nlc = eb.get("next_level_cost")
    assert nlc is not None
    iron_row = next(
        (d for d in nlc["materials_detail"] if d["slug"] == "iron_shard"),
        None,
    )
    assert iron_row is not None
    # owned MUST be available (= 2), NOT raw quantity (= 10).
    assert iron_row["owned"] == 2, \
        f"owned must be available=2, not raw quantity=10: got {iron_row['owned']}"
    assert iron_row["missing"] == max(0, iron_row["required"] - 2)
