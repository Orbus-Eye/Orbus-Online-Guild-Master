"""ROUND 11.2 EXT PRE-S2 — Territory upgrade UX hotfix coverage.

The original player report was:
  "Ho l'oggetto ma non permette il potenziamento."

RCA: GET /api/territory used to return `next_level_cost: None` for every
unlocked structure (the cost map lived only inside `cost_for()` and was
never surfaced to the FE). Players clicked "Potenzia" blind, hit 422
"resources.material_insufficient", and concluded the backend was broken.

Fix: `_public_doc` now enriches each unlocked structure with
`next_level_cost = {target_level, gold, materials}` so the FE can render
a "Ti mancano: 36× Frammento di Ferro" preview BEFORE the click.

Two regression tests:
  PRE-S2.01 — Positive: GET /api/territory exposes next_level_cost with
              correct shape for an unlocked structure.
  PRE-S2.02 — Negative: POST /api/territory/upgrade still returns 422
              with `resources.material_insufficient` when materials
              fall short — atomicity preserved (no compensating leak).
"""
from __future__ import annotations

import os

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


def _login_tester() -> str:
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "tester@orbus.test", "password": "password123"},
        timeout=10,
    )
    return r.json()["access_token"]


# ─── PRE-S2.01 ────────────────────────────────────────────────────────────────
def test_pre_s2_01_territory_exposes_next_level_cost_for_unlocked():
    """The UX hotfix: every unlocked structure must surface a
    `next_level_cost` block so the FE can preview the cost."""
    token = _login_tester()
    r = requests.get(
        f"{BASE_URL}/api/territory",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    assert r.status_code == 200
    structures = r.json()["territory"]["structures"]
    # guild_hall is always Lv >= 1 (starter), so it must carry next_level_cost.
    gh = structures.get("guild_hall") or {}
    assert int(gh.get("level", 0)) >= 1
    nlc = gh.get("next_level_cost")
    assert nlc is not None, "guild_hall (Lv >= 1) missing next_level_cost"
    # Shape contract.
    assert "target_level" in nlc and "gold" in nlc and "materials" in nlc
    assert int(nlc["target_level"]) == int(gh["level"]) + 1
    assert isinstance(nlc["materials"], dict)
    # Lv 0 → No upgrade preview (Purchase CTA path instead).
    for slug, info in structures.items():
        if int(info.get("level", 0)) == 0:
            assert info.get("next_level_cost") is None, \
                f"{slug} (Lv0) should expose next_level_cost=None (use Purchase path)"


# ─── PRE-S2.02 ────────────────────────────────────────────────────────────────
def test_pre_s2_02_upgrade_with_insufficient_materials_returns_422(db):
    """Atomicity must be preserved: insufficient materials → 422 with
    `resources.material_insufficient`, no partial gold debit, no
    structure level bump."""
    token = _login_tester()
    # Snapshot tester guild gold + dormitories level pre-call.
    u = db.users.find_one({"email": "tester@orbus.test"})
    g_before = db.guilds.find_one({"owner_user_id": u["id"]}, {"_id": 0, "gold": 1, "id": 1})
    gid = g_before["id"]
    gold_before = int(g_before["gold"])
    gs_before = db.guild_structures.find_one({"guild_id": gid}, {"_id": 0, "structures.dormitories": 1})
    dorm_level_before = int(((gs_before or {}).get("structures") or {}).get("dormitories", {}).get("level", 0))

    # Tester has 1× iron_shard; dormitories Lv7→Lv8 needs 36 → guaranteed fail.
    r = requests.post(
        f"{BASE_URL}/api/territory/upgrade",
        json={"structure_slug": "dormitories"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    assert r.status_code == 422, r.text
    detail = r.json().get("detail", {})
    assert detail.get("code") == "resources.material_insufficient"
    assert detail.get("slug") == "iron_shard"
    assert int(detail.get("required", 0)) >= 1
    assert int(detail.get("available", -1)) >= 0  # available correctly reported

    # No state change: gold + level identical post-call.
    g_after = db.guilds.find_one({"id": gid}, {"_id": 0, "gold": 1})
    assert int(g_after["gold"]) == gold_before, \
        f"Gold mutated on failed upgrade: {gold_before} → {g_after['gold']}"
    gs_after = db.guild_structures.find_one({"guild_id": gid}, {"_id": 0, "structures.dormitories": 1})
    dorm_level_after = int(((gs_after or {}).get("structures") or {}).get("dormitories", {}).get("level", 0))
    assert dorm_level_after == dorm_level_before, \
        f"Dormitories level mutated on failed upgrade: {dorm_level_before} → {dorm_level_after}"
