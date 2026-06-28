"""ROUND 11.2 TASK 6 G1-G2 — Public catalog endpoints (traits + stats).

5 backend tests as per the user's GO message (Msg 441 + clarification):

  T6.01 GET /api/traits/catalog → 200 OK senza Authorization header (PUBBLICO).
  T6.02 GET /api/stats/catalog  → 200 OK senza Authorization header (PUBBLICO).
  T6.03 /api/traits/catalog NON espone traits con is_test=True.
  T6.04 /api/traits/catalog NON espone traits con is_active=False.
  T6.05 /api/traits/catalog mappa la polarity correttamente (positive/negative/mixed)
        ed espone i campi pubblici attesi (no `code`, no `is_test`, no `is_active`).

Tutti i test usano `requests` puro contro la preview/local backend (no Bearer).
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


def _insert_test_trait(db, **overrides):
    """Insert a one-off trait directly for filtering assertions."""
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": str(uuid.uuid4()),
        "code": f"r112t6_{uuid.uuid4().hex[:8]}",
        "name": f"r112t6_{uuid.uuid4().hex[:8]}",
        "display_name": "T6 Probe",
        "display_name_it": "Sonda T6",
        "display_name_en": "T6 Probe",
        "description": "Descrizione probe IT.",
        "description_en": "T6 probe description.",
        "rarity": "common",
        "polarity": "positive",
        "modifier_type": "flat",
        "affected_stat": "strength",
        "modifier_value": 1.0,
        "is_positive": True,
        "is_active": True,
        "is_test": False,
        "created_at": now,
        "updated_at": now,
    }
    doc.update(overrides)
    db.adventurer_traits.insert_one(doc)
    return doc


# ─── T6.01 ────────────────────────────────────────────────────────────────────
def test_t6_01_traits_catalog_public_no_auth():
    r = requests.get(f"{BASE_URL}/api/traits/catalog", timeout=10)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "total" in body and "traits" in body
    assert isinstance(body["traits"], list)
    assert body["total"] >= 1  # almeno i 10 Italian seeds devono essere presenti


# ─── T6.02 ────────────────────────────────────────────────────────────────────
def test_t6_02_stats_catalog_public_no_auth():
    r = requests.get(f"{BASE_URL}/api/stats/catalog", timeout=10)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "total" in body and "stats" in body
    keys = {s["key"] for s in body["stats"]}
    # Core stats che il brief richiede esplicitamente
    for required in ("strength", "agility", "intellect", "endurance", "faith",
                     "stamina", "morale", "level", "experience", "power_score"):
        assert required in keys, f"Missing stat key: {required}"


# ─── T6.03 ────────────────────────────────────────────────────────────────────
def test_t6_03_traits_catalog_filters_is_test(db):
    probe = _insert_test_trait(db, is_test=True, is_active=True)
    try:
        r = requests.get(f"{BASE_URL}/api/traits/catalog", timeout=10)
        ids = {t["id"] for t in r.json()["traits"]}
        assert probe["id"] not in ids, "Trait con is_test=True esposto al pubblico"
    finally:
        db.adventurer_traits.delete_one({"id": probe["id"]})


# ─── T6.04 ────────────────────────────────────────────────────────────────────
def test_t6_04_traits_catalog_filters_is_active_false(db):
    probe = _insert_test_trait(db, is_test=False, is_active=False)
    try:
        r = requests.get(f"{BASE_URL}/api/traits/catalog", timeout=10)
        ids = {t["id"] for t in r.json()["traits"]}
        assert probe["id"] not in ids, "Trait con is_active=False esposto al pubblico"
    finally:
        db.adventurer_traits.delete_one({"id": probe["id"]})


# ─── T6.05 ────────────────────────────────────────────────────────────────────
def test_t6_05_traits_catalog_polarity_mapping_and_safe_shape(db):
    probe_pos = _insert_test_trait(
        db,
        polarity="positive",
        is_positive=True,
    )
    probe_neg = _insert_test_trait(
        db,
        polarity="negative",
        is_positive=False,
        modifier_value=-2.0,
    )
    probe_mixed = _insert_test_trait(
        db,
        polarity="mixed",
        is_positive=True,
    )
    try:
        r = requests.get(f"{BASE_URL}/api/traits/catalog", timeout=10)
        assert r.status_code == 200
        by_id = {t["id"]: t for t in r.json()["traits"]}
        # Polarity mapping
        assert by_id[probe_pos["id"]]["polarity"] == "positive"
        assert by_id[probe_neg["id"]]["polarity"] == "negative"
        assert by_id[probe_mixed["id"]]["polarity"] == "mixed"
        # Safe public shape: no internal/moderation fields leak
        sample = by_id[probe_pos["id"]]
        for forbidden in ("code", "is_test", "is_active", "name", "is_positive",
                          "created_at", "updated_at"):
            assert forbidden not in sample, f"Field '{forbidden}' leaked in public response"
        # Required public fields present
        for required in ("id", "display_name_it", "display_name_en", "description_it",
                         "description_en", "rarity", "polarity", "affected_stat",
                         "modifier_type", "modifier_value"):
            assert required in sample, f"Missing public field: {required}"
    finally:
        db.adventurer_traits.delete_many({
            "id": {"$in": [probe_pos["id"], probe_neg["id"], probe_mixed["id"]]}
        })
