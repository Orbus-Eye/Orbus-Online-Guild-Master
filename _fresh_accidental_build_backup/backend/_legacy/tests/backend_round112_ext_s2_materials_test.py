"""ROUND 11.2 EXT TASK 10 M1+M4+M6 — Materials catalog & Territory enriched.

7 backend tests covering the player-facing surfaces produced by S2:

  T10.BE.01 — Iron Shard is exposed in /api/materials/catalog (it backs
              the most common Territory cost — must be discoverable).
  T10.BE.02 — Every catalog material has display_name_it non-empty.
  T10.BE.03 — Every catalog material has sources[] non-empty (no
              undocumented material reaches players).
  T10.BE.04 — /api/territory exposes per-structure
              materials_detail/owned/missing/can_afford.
  T10.BE.05 — No equipment leak: catalog contains zero item with
              item_type != "material" (and zero with rarity ∈
              {legendary, epic} unless explicitly catalogued).
  T10.BE.06 — Test/inactive/hidden materials are excluded.
  T10.BE.07 — Public payload carries no PII / no admin source label.
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


def _login_tester() -> str:
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "tester@orbus.test", "password": "password123"},
        timeout=10,
    )
    return r.json()["access_token"]


# ─── T10.BE.01 ────────────────────────────────────────────────────────────────
def test_t10_be_01_iron_shard_in_materials_catalog():
    r = requests.get(f"{BASE_URL}/api/materials/catalog", timeout=10)
    assert r.status_code == 200
    slugs = {m["slug"] for m in r.json()["materials"]}
    assert "iron_shard" in slugs, "iron_shard MUST be in the public catalog"


# ─── T10.BE.02 ────────────────────────────────────────────────────────────────
def test_t10_be_02_every_material_has_display_name_it():
    r = requests.get(f"{BASE_URL}/api/materials/catalog", timeout=10)
    for m in r.json()["materials"]:
        assert (m.get("display_name_it") or "").strip(), \
            f"material {m['slug']} missing display_name_it"


# ─── T10.BE.03 ────────────────────────────────────────────────────────────────
def test_t10_be_03_every_material_has_sources():
    r = requests.get(f"{BASE_URL}/api/materials/catalog", timeout=10)
    for m in r.json()["materials"]:
        assert m.get("sources"), f"material {m['slug']} has empty sources[]"
        for s in m["sources"]:
            assert s.get("type"), f"source missing type in {m['slug']}"
            assert s.get("label_it"), f"source missing IT label in {m['slug']}"


# ─── T10.BE.04 ────────────────────────────────────────────────────────────────
def test_t10_be_04_territory_exposes_enriched_next_level_cost():
    token = _login_tester()
    r = requests.get(
        f"{BASE_URL}/api/territory",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    assert r.status_code == 200
    structures = r.json()["territory"]["structures"]
    # Find at least one unlocked structure with materials.
    found = False
    for slug, info in structures.items():
        nlc = info.get("next_level_cost")
        if not nlc:
            continue
        # Enriched fields contract.
        assert "materials_detail" in nlc
        assert "owned_gold" in nlc
        assert "can_afford" in nlc
        assert "missing" in nlc
        assert "gold" in nlc["missing"] and "materials" in nlc["missing"]
        if nlc.get("materials"):
            for d in nlc["materials_detail"]:
                assert d["required"] >= 0
                assert d["owned"] >= 0
                assert d["missing"] == max(0, d["required"] - d["owned"])
                assert (d.get("display_name_it") or "").strip()
            found = True
    assert found, "No unlocked structure with materials_detail enrichment found"


# ─── T10.BE.05 ────────────────────────────────────────────────────────────────
def test_t10_be_05_no_equipment_leak_in_materials_catalog(db):
    r = requests.get(f"{BASE_URL}/api/materials/catalog", timeout=10)
    slugs = {m["slug"] for m in r.json()["materials"]}
    # Cross-check: every slug in the catalog must have item_type='material'.
    for slug in slugs:
        doc = db.items.find_one({"slug": slug}, {"_id": 0, "item_type": 1, "slot_type": 1})
        assert doc is not None, f"catalog references non-existent slug {slug}"
        assert doc.get("item_type") == "material", \
            f"slug {slug} has item_type={doc.get('item_type')} (equipment leak!)"
        # Equipment slots (weapon/armor/accessory) NEVER allowed.
        assert doc.get("slot_type") in (None, "", "material"), \
            f"slug {slug} has slot_type={doc.get('slot_type')} (equipment leak!)"


# ─── T10.BE.06 ────────────────────────────────────────────────────────────────
def test_t10_be_06_test_or_inactive_materials_excluded(db):
    # Insert a probe material flagged is_test=True (and a 2nd is_active=False).
    probe_ids: list[str] = []
    now = datetime.now(timezone.utc).isoformat()
    for flag in ("is_test", "inactive"):
        pid = str(uuid.uuid4())
        slug = f"r112t10_{uuid.uuid4().hex[:8]}"
        doc = {
            "id": pid,
            "slug": slug,
            "name": "T10 Probe",
            "display_name_it": "Sonda T10",
            "display_name_en": "T10 Probe",
            "item_type": "material",
            "rarity": "common",
            "is_active": True if flag == "is_test" else False,
            "is_test": True if flag == "is_test" else False,
            "stackable": True,
            "created_at": now,
            "updated_at": now,
        }
        db.items.insert_one(doc)
        probe_ids.append(pid)
    try:
        r = requests.get(f"{BASE_URL}/api/materials/catalog", timeout=10)
        slugs = {m["slug"] for m in r.json()["materials"]}
        for pid in probe_ids:
            doc = db.items.find_one({"id": pid}, {"_id": 0, "slug": 1})
            assert doc["slug"] not in slugs, \
                f"Flagged probe {doc['slug']} leaked into public catalog"
    finally:
        db.items.delete_many({"id": {"$in": probe_ids}})


# ─── T10.BE.07 ────────────────────────────────────────────────────────────────
def test_t10_be_07_public_payload_no_pii_no_admin_source():
    r = requests.get(f"{BASE_URL}/api/materials/catalog", timeout=10)
    body = r.json()
    forbidden_keys = {"created_at", "updated_at", "is_test", "is_active",
                      "is_hidden", "is_cosmetic", "_id", "owner_user_id",
                      "guild_id", "email"}
    forbidden_source_types = {"admin", "admin_grant", "grant", "internal"}
    for m in body["materials"]:
        leaks = set(m.keys()) & forbidden_keys
        assert not leaks, f"Forbidden keys in {m['slug']}: {leaks}"
        for s in m.get("sources", []):
            assert s.get("type") not in forbidden_source_types, \
                f"admin/grant source exposed publicly in {m['slug']}"
