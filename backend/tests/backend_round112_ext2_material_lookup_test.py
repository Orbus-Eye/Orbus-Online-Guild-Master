"""ROUND 11.2 EXT-2 — Material lookup endpoint + Territory regression.

3 BE tests for the new `GET /api/materials/lookup/{slug}`:
  EXT2.BE.01 — 200 with full payload for a known curated material.
  EXT2.BE.02 — 404 for an unknown / typo slug (no existence leak).
  EXT2.BE.03 — 404 for an equipment slug (security: equipment data
               MUST NOT leak through the public material endpoint).

3 regression tests guarding the surfaces EXT-2 touches:
  EXT2.REG.01 — /api/materials/catalog still 200 with stable shape.
  EXT2.REG.02 — /api/territory still exposes per-structure
               `next_level_cost.can_afford` & `materials_detail`.
  EXT2.REG.03 — Double-spend gate intact: an inventory row with
               `market_locked_qty == quantity` makes the upgrade
               preview report `can_afford = false`.
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


# ─── EXT2.BE.01 ───────────────────────────────────────────────────────────────
def test_ext2_be_01_lookup_known_material_200():
    """Known curated material returns full enriched payload."""
    r = requests.get(f"{BASE_URL}/api/materials/lookup/iron_shard", timeout=10)
    assert r.status_code == 200, r.text
    body = r.json()
    # Public shape contract.
    assert body["slug"] == "iron_shard"
    assert isinstance(body.get("display_name_it"), str) and body["display_name_it"]
    assert isinstance(body.get("display_name_en"), str) and body["display_name_en"]
    assert body.get("rarity") in {"common", "uncommon", "rare", "epic", "legendary"}
    assert isinstance(body.get("description_it"), str)
    assert isinstance(body.get("sources"), list) and len(body["sources"]) >= 1
    # Each source carries the IT+EN label so the modal can switch language.
    for src in body["sources"]:
        assert "type" in src and "label_it" in src and "label_en" in src
    # Anti-spoiler: `admin_grant` must NEVER leak as a public source type.
    assert all(src["type"] != "admin_grant" for src in body["sources"])
    # PII guard.
    assert "_id" not in body


# ─── EXT2.BE.02 ───────────────────────────────────────────────────────────────
def test_ext2_be_02_lookup_unknown_slug_404():
    """Unknown / typo slug must 404 (not 200 with null/empty)."""
    r = requests.get(
        f"{BASE_URL}/api/materials/lookup/this_material_does_not_exist_zzz",
        timeout=10,
    )
    assert r.status_code == 404, r.text
    detail = (r.json() or {}).get("detail") or {}
    # Stable error code for FE branching.
    if isinstance(detail, dict):
        assert detail.get("code") == "material.not_found"


# ─── EXT2.BE.03 ───────────────────────────────────────────────────────────────
def test_ext2_be_03_lookup_equipment_404(db):
    """Security: equipment slugs (weapons/armor/legendaries/sets) MUST NOT
    leak through the material lookup endpoint, even though they live in the
    same `items` collection.

    Strategy: pick a real equipment row from `items` where item_type !=
    'material' and assert the lookup returns 404.
    """
    eq = db.items.find_one(
        {"item_type": {"$ne": "material"}, "slug": {"$exists": True}},
        {"_id": 0, "slug": 1, "item_type": 1},
    )
    if eq is None:
        pytest.skip("No equipment row available in this environment.")
    r = requests.get(f"{BASE_URL}/api/materials/lookup/{eq['slug']}", timeout=10)
    assert r.status_code == 404, (
        f"Equipment slug `{eq['slug']}` (item_type={eq['item_type']}) leaked "
        f"through the public material lookup endpoint. Response: {r.text}"
    )


# ─── EXT2.REG.01 ──────────────────────────────────────────────────────────────
def test_ext2_reg_01_catalog_still_ok():
    """`/api/materials/catalog` is still a 200 with the expected shape."""
    r = requests.get(f"{BASE_URL}/api/materials/catalog", timeout=10)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "materials" in body and isinstance(body["materials"], list)
    assert "total" in body and body["total"] == len(body["materials"])
    slugs = {m["slug"] for m in body["materials"]}
    # iron_shard is a stability anchor — its removal would break many
    # Territory upgrades and is a signal of catalog regression.
    assert "iron_shard" in slugs


# ─── EXT2.REG.02 ──────────────────────────────────────────────────────────────
def test_ext2_reg_02_territory_preview_payload_intact():
    """`/api/territory` still carries `next_level_cost.can_afford` and the
    enriched `materials_detail` array on every upgradable structure.

    The FE relies on this shape to render `CostBreakdown` — if it ever
    silently drops back to the unenriched form, the Potenzia button stops
    being disabled-on-missing-materials and we regress to the original UX
    trap that motivated EXT-2 in the first place.
    """
    tok = _login_tester()
    r = requests.get(
        f"{BASE_URL}/api/territory",
        headers={"Authorization": f"Bearer {tok}"},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    structures = r.json()["territory"]["structures"]
    saw_enriched = False
    for slug, info in structures.items():
        nlc = info.get("next_level_cost")
        if not nlc:
            continue
        # Required keys produced by `_enrich_territory_with_inventory`.
        for k in ("target_level", "gold", "owned_gold", "can_afford", "missing", "materials_detail"):
            assert k in nlc, (
                f"`next_level_cost.{k}` missing on structure `{slug}` — "
                f"enrichment is broken. Payload: {nlc!r}"
            )
        assert isinstance(nlc["can_afford"], bool)
        assert isinstance(nlc["materials_detail"], list)
        saw_enriched = True
    assert saw_enriched, "No structure exposed `next_level_cost` — tester has no upgradable structure?"


# ─── EXT2.REG.03 ──────────────────────────────────────────────────────────────
def test_ext2_reg_03_double_spend_guard_in_preview(db):
    """Inventory rows fully locked by an auction listing must report
    `available = 0` in the territory cost preview (NOT `quantity`).

    Strategy: temporarily flip the tester's iron_shard inventory row so
    that `market_locked_qty == quantity` (i.e. the entire stack is
    "listed on the auction"). The preview must then report `owned = 0`
    for any structure whose next level requires iron_shard. Restore the
    original row at the end.
    """
    tok = _login_tester()
    me_resp = requests.get(
        f"{BASE_URL}/api/auth/me",
        headers={"Authorization": f"Bearer {tok}"},
        timeout=10,
    ).json()
    me = me_resp.get("user", me_resp)
    guild = db.guilds.find_one({"owner_user_id": me["id"]}, {"_id": 0, "id": 1, "gold": 1})
    if guild is None:
        pytest.skip("Tester has no guild in this environment.")
    iron = db.items.find_one({"slug": "iron_shard"}, {"_id": 0, "id": 1})
    if iron is None:
        pytest.skip("iron_shard template missing from items collection.")

    inv = db.inventory_items.find_one(
        {"guild_id": guild["id"], "item_id": iron["id"]},
        {"_id": 0, "id": 1, "quantity": 1, "market_locked_qty": 1},
    )
    if inv is None or int(inv.get("quantity", 0)) <= 0:
        pytest.skip("Tester has no iron_shard inventory row to lock.")

    original_locked = int(inv.get("market_locked_qty", 0))
    qty = int(inv["quantity"])
    # Lock the entire stack — emulate "everything is in an active auction".
    db.inventory_items.update_one(
        {"id": inv["id"]},
        {"$set": {"market_locked_qty": qty}},
    )
    try:
        r = requests.get(
            f"{BASE_URL}/api/territory",
            headers={"Authorization": f"Bearer {tok}"},
            timeout=10,
        )
        assert r.status_code == 200
        structures = r.json()["territory"]["structures"]
        relevant = []
        for slug, info in structures.items():
            nlc = info.get("next_level_cost") or {}
            if "iron_shard" in (nlc.get("materials") or {}):
                relevant.append((slug, nlc))
        if not relevant:
            pytest.skip("No upgradable structure requires iron_shard for tester.")
        for slug, nlc in relevant:
            row = next((d for d in nlc["materials_detail"] if d["slug"] == "iron_shard"), None)
            assert row is not None
            assert row["owned"] == 0, (
                f"Double-spend regression on `{slug}.iron_shard`: locked "
                f"inventory still counted as available. owned={row['owned']}, "
                f"required={row['required']}"
            )
    finally:
        # Restore the original `market_locked_qty` so the tester's state
        # is untouched at the end of the test run.
        db.inventory_items.update_one(
            {"id": inv["id"]},
            {"$set": {"market_locked_qty": original_locked}},
        )
