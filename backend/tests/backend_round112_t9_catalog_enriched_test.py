"""ROUND 11.2 EXT TASK 9 (S1) — Traits/Stats catalog enriched coverage.

6 backend tests targeting the new public catalog shape required by the
Guide tabs §10 (Statistiche) and §11 (Tratti).

  T9.01 — Stats catalog returns only safe stats (none flagged hidden/test).
  T9.02 — Traits catalog excludes is_test=True and is_active=False.
  T9.03 — Traits with test-name patterns are still allowed when they are
          real seeded traits (e.g. "lucky" is NOT a test trait); only the
          DB flags drive exclusion.
  T9.04 — Polarity classification: every active trait gets one of
          {positive, negative, mixed, neutral} — never empty.
  T9.05 — No tech-slug leak in payload: forbidden keys
          (code/is_test/is_active/is_positive/name/created_at) absent.
  T9.06 — Trait with no measurable effect returns explicit fallback
          (gameplay_effect_it starts with the Italian descriptive text).
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


def _insert_trait(db, **overrides):
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": str(uuid.uuid4()),
        "code": f"r112t9_{uuid.uuid4().hex[:8]}",
        "name": f"r112t9_{uuid.uuid4().hex[:8]}",
        "display_name": "T9 Probe",
        "display_name_it": "Sonda T9",
        "display_name_en": "T9 Probe",
        "description": "Descrizione probe IT.",
        "description_en": "T9 probe description.",
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


# ─── T9.01 ────────────────────────────────────────────────────────────────────
def test_t9_01_stats_catalog_only_safe_stats():
    r = requests.get(f"{BASE_URL}/api/stats/catalog", timeout=10)
    assert r.status_code == 200
    body = r.json()
    # No internal markers leaked.
    for s in body["stats"]:
        assert "is_test" not in s
        assert "is_hidden" not in s
        assert "is_internal" not in s
        # Every stat row carries IT + EN human-readable fields.
        assert s.get("display_name_it"), f"stat {s['key']} missing display_name_it"
        assert s.get("description_it"), f"stat {s['key']} missing description_it"


# ─── T9.02 ────────────────────────────────────────────────────────────────────
def test_t9_02_traits_catalog_excludes_test_and_inactive(db):
    p_test = _insert_trait(db, is_test=True, is_active=True)
    p_inactive = _insert_trait(db, is_test=False, is_active=False)
    try:
        r = requests.get(f"{BASE_URL}/api/traits/catalog", timeout=10)
        ids = {t["id"] for t in r.json()["traits"]}
        assert p_test["id"] not in ids
        assert p_inactive["id"] not in ids
    finally:
        db.adventurer_traits.delete_many({
            "id": {"$in": [p_test["id"], p_inactive["id"]]}
        })


# ─── T9.03 ────────────────────────────────────────────────────────────────────
def test_t9_03_real_traits_with_test_like_names_are_allowed():
    """Anti-regression: the legacy seed includes a trait code='lucky' with
    display_name='Fortunato'. A naive regex like \bluck would falsely
    classify it as test. Verify it IS exposed and the polarity is set."""
    r = requests.get(f"{BASE_URL}/api/traits/catalog", timeout=10)
    fortunato = next(
        (t for t in r.json()["traits"] if t["display_name_it"] == "Fortunato"),
        None,
    )
    assert fortunato is not None, "Real seeded trait 'Fortunato' was excluded"
    assert fortunato["polarity"] in {"positive", "negative", "mixed", "neutral"}


# ─── T9.04 ────────────────────────────────────────────────────────────────────
def test_t9_04_every_trait_has_a_polarity_label():
    r = requests.get(f"{BASE_URL}/api/traits/catalog", timeout=10)
    valid = {"positive", "negative", "mixed", "neutral"}
    for t in r.json()["traits"]:
        assert t.get("polarity") in valid, f"Bad polarity for {t['display_name_it']!r}: {t.get('polarity')!r}"


# ─── T9.05 ────────────────────────────────────────────────────────────────────
def test_t9_05_no_internal_keys_leak_in_payload():
    r = requests.get(f"{BASE_URL}/api/traits/catalog", timeout=10)
    forbidden = {"code", "is_test", "is_active", "is_positive", "name",
                 "created_at", "updated_at", "_id"}
    sample_n = 0
    for t in r.json()["traits"]:
        leaks = set(t.keys()) & forbidden
        assert not leaks, f"Forbidden keys leaked in {t['display_name_it']}: {leaks}"
        sample_n += 1
    assert sample_n >= 1


# ─── T9.06 ────────────────────────────────────────────────────────────────────
def test_t9_06_trait_without_effect_has_fallback_gameplay_text(db):
    """A trait with modifier_value=0 / no affected_stat must surface
    a player-readable IT fallback instead of silently empty text."""
    probe = _insert_trait(
        db,
        affected_stat=None,
        modifier_value=0,
        polarity="neutral",
        is_positive=True,
    )
    try:
        r = requests.get(f"{BASE_URL}/api/traits/catalog", timeout=10)
        view = next((t for t in r.json()["traits"] if t["id"] == probe["id"]), None)
        assert view is not None
        assert view.get("affects_power") is False
        assert "descrittivo" in (view.get("gameplay_effect_it") or "").lower(), \
            f"Fallback IT text missing: got {view.get('gameplay_effect_it')!r}"
    finally:
        db.adventurer_traits.delete_one({"id": probe["id"]})
