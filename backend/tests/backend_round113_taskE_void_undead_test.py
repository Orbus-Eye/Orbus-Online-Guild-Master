"""ROUND 11.3 Turno 3 — Fase 3B — TASK E seed validation tests.

5 tests:
  E.01 — Seed idempotenza: run 2 volte → stessi 15 record, 0 duplicati.
  E.02 — Level gate per dungeon: under-level → 423 `adventurer.level_too_low`.
  E.03 — Tutti i nomi/descrizioni IT (smoke check anti-EN copy generico).
  E.04 — ≥6/10 dungeons + 5/5 raid hanno keyword Lore canoniche.
  E.05 — Progressione `min_adventurer_level` rispettata su entrambi i set.
"""
from __future__ import annotations

import asyncio
import os
import re

import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")

# Vocabolario canonico estratto dal Lore Book Orbus.
LORE_KEYWORDS = [
    "ergolat", "vuoto", "irthe", "alevora", "ashkaroth", "eclipthra",
    "gralca", "xal'zoraax", "xal-zoraax",
    "sinfonia dei fili", "filo spezzato", "sigillo spezzato",
    "punta dell'oblio", "obelisch", "orde senza volto",
    "piaga dei mille volti", "valys mordivac", "sussurro del nulla",
    "rituale del vuoto", "tempio del vuoto eterno", "figli di irthe",
    "figli del vuoto", "vuoto eterno", "marionettista lunare",
    "breccia del vuoto", "vuoto che divora", "esiliati",
]

DUNGEON_SLUGS = [
    "echoes-of-the-broken-thread", "shattered-seal-of-ergolat",
    "obelisks-of-the-void", "plague-warrens-of-irthe",
    "moonlit-strings-of-alevora", "ashkaroth-crypt-court",
    "eclipthra-veiled-sanctum", "gralca-tide-of-the-deep",
    "xal-zoraax-throat-of-silence", "tip-of-oblivion-trial",
]
RAID_SLUGS = [
    "rituale-del-vuoto-orde", "figli-di-irthe-rising",
    "alevora-marionetta-grande", "tempio-del-vuoto-eterno",
    "valys-mordivac-final-whisper",
]


@pytest.fixture(scope="module")
def mdb():
    cli = MongoClient(MONGO_URL)
    yield cli[DB_NAME]
    cli.close()


def _has_keyword(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in LORE_KEYWORDS)


# ─── E.01 ─────────────────────────────────────────────────────────────────────
def test_e_01_seed_is_idempotent(mdb):
    """Re-run del seed: stessi 15 record, 0 duplicati."""
    from app.scripts.seed_round113_void_undead import run as seed_run

    before_d = mdb.dungeons.count_documents({"slug": {"$in": DUNGEON_SLUGS}})
    before_r = mdb.raid_dungeons.count_documents({"slug": {"$in": RAID_SLUGS}})
    assert before_d == len(DUNGEON_SLUGS), f"Pre-test: {before_d}/{len(DUNGEON_SLUGS)} dungeons missing"
    assert before_r == len(RAID_SLUGS), f"Pre-test: {before_r}/{len(RAID_SLUGS)} raids missing"

    # Capture original ids — re-run must NOT mint new ids.
    ids_d_before = {d["slug"]: d["id"] for d in mdb.dungeons.find({"slug": {"$in": DUNGEON_SLUGS}}, {"_id": 0, "slug": 1, "id": 1})}
    ids_r_before = {r["slug"]: r["id"] for r in mdb.raid_dungeons.find({"slug": {"$in": RAID_SLUGS}}, {"_id": 0, "slug": 1, "id": 1})}

    asyncio.run(seed_run())

    after_d = mdb.dungeons.count_documents({"slug": {"$in": DUNGEON_SLUGS}})
    after_r = mdb.raid_dungeons.count_documents({"slug": {"$in": RAID_SLUGS}})
    assert after_d == before_d, f"Dungeon count drifted: {before_d} → {after_d}"
    assert after_r == before_r, f"Raid count drifted: {before_r} → {after_r}"

    ids_d_after = {d["slug"]: d["id"] for d in mdb.dungeons.find({"slug": {"$in": DUNGEON_SLUGS}}, {"_id": 0, "slug": 1, "id": 1})}
    ids_r_after = {r["slug"]: r["id"] for r in mdb.raid_dungeons.find({"slug": {"$in": RAID_SLUGS}}, {"_id": 0, "slug": 1, "id": 1})}
    assert ids_d_before == ids_d_after, "Dungeon ids re-minted on re-run"
    assert ids_r_before == ids_r_after, "Raid ids re-minted on re-run"


# ─── E.02 ─────────────────────────────────────────────────────────────────────
def test_e_02_level_gate_blocks_under_level_adv(mdb):
    """Lo Xal'Zoraax dungeon (min_lvl 18) deve essere bloccato per un Lv1."""
    import uuid as _uuid
    email = f"r113e-{_uuid.uuid4().hex[:6]}@orbus.test"
    pw = "password123!"
    r = requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": email, "username": email.split("@")[0], "password": pw,
    }, timeout=10)
    tok = r.json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    requests.post(f"{BASE_URL}/api/guilds", json={"name": f"R113E-{_uuid.uuid4().hex[:6]}", "description": "t"}, headers=h, timeout=10)

    # Find Xal'Zoraax id.
    dungeons = requests.get(f"{BASE_URL}/api/dungeons", headers=h, timeout=10).json()["dungeons"]
    target = next((d for d in dungeons if d["slug"] == "xal-zoraax-throat-of-silence"), None)
    assert target is not None
    assert target["min_adventurer_level"] == 18

    advs = requests.get(f"{BASE_URL}/api/adventurers", headers=h, timeout=10).json()
    if isinstance(advs, dict):
        advs = advs.get("adventurers") or advs.get("items") or []
    chosen_ids = [a["id"] for a in advs[:3]]

    rr = requests.post(f"{BASE_URL}/api/expeditions/preview", json={
        "dungeon_id": target["id"], "adventurer_ids": chosen_ids,
    }, headers=h, timeout=10)
    assert rr.status_code == 423, f"Expected 423, got {rr.status_code}: {rr.text}"
    detail = (rr.json() or {}).get("detail") or {}
    assert detail.get("code") == "adventurer.level_too_low"
    assert detail.get("min_required_level") == 18


# ─── E.03 ─────────────────────────────────────────────────────────────────────
def test_e_03_no_generic_english_copy(mdb):
    """Smoke check: name/description del campo IT non devono contenere copy generico EN."""
    banned_patterns = [
        r"\bdungeon of\b", r"\bcave of\b", r"\bthe forgotten\b",
        r"\ban ancient evil\b", r"\bdark forest\b", r"\bmysterious tower\b",
    ]
    rx = [re.compile(p, re.IGNORECASE) for p in banned_patterns]

    for slug in DUNGEON_SLUGS:
        d = mdb.dungeons.find_one({"slug": slug}, {"_id": 0, "name": 1, "description": 1})
        for r in rx:
            assert not r.search(d["name"]), f"Generic EN copy in dungeon name: {d['name']}"
            # description here is IT (we didn't dual-language dungeons by design)
            assert not r.search(d["description"]), f"Generic EN copy in dungeon desc: {slug}"

    for slug in RAID_SLUGS:
        rd = mdb.raid_dungeons.find_one({"slug": slug}, {"_id": 0, "name_it": 1, "description_it": 1})
        for r in rx:
            assert not r.search(rd["name_it"]), f"Generic EN copy in raid name_it: {rd['name_it']}"
            assert not r.search(rd["description_it"]), f"Generic EN copy in raid desc_it: {slug}"


# ─── E.04 ─────────────────────────────────────────────────────────────────────
def test_e_04_lore_keyword_coverage(mdb):
    """≥6/10 dungeons + 5/5 raid devono contenere almeno una keyword Lore."""
    dungeons_hit = 0
    for slug in DUNGEON_SLUGS:
        d = mdb.dungeons.find_one({"slug": slug}, {"_id": 0, "name": 1, "description": 1})
        if _has_keyword(d["name"]) or _has_keyword(d["description"]):
            dungeons_hit += 1
    assert dungeons_hit >= 6, f"Dungeon lore coverage: {dungeons_hit}/10 (min 6)"

    raids_hit = 0
    for slug in RAID_SLUGS:
        rd = mdb.raid_dungeons.find_one({"slug": slug}, {"_id": 0, "name_it": 1, "description_it": 1})
        if _has_keyword(rd["name_it"]) or _has_keyword(rd["description_it"]):
            raids_hit += 1
    assert raids_hit == 5, f"Raid lore coverage: {raids_hit}/5 (must be 5)"


# ─── E.05 ─────────────────────────────────────────────────────────────────────
def test_e_05_min_level_progression(mdb):
    """min_adventurer_level cresce monotonicamente nella sequenza definita."""
    expected_d = [1, 2, 4, 6, 8, 10, 12, 15, 18, 20]
    levels = [mdb.dungeons.find_one({"slug": s}, {"_id": 0, "min_adventurer_level": 1})["min_adventurer_level"]
              for s in DUNGEON_SLUGS]
    assert levels == expected_d, f"Dungeon min_lvl progression off: {levels} vs {expected_d}"

    expected_r = [10, 14, 18, 24, 30]
    rlevels = [mdb.raid_dungeons.find_one({"slug": s}, {"_id": 0, "min_adventurer_level": 1})["min_adventurer_level"]
               for s in RAID_SLUGS]
    assert rlevels == expected_r, f"Raid min_lvl progression off: {rlevels} vs {expected_r}"
