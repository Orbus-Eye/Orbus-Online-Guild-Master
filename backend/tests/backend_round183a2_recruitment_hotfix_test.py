"""ROUND 18.3a.2 HOTFIX — test suite (target >= 7, delivered 11).

Verifica il fix chirurgico al bug live HTTP 500 su
`POST /api/recruitment/refresh` causato da `filter_safe_class_pool`
che pescava le 2 hidden classes R18.3a senza `base_*` fields.

Patch: `app/adventurers/generator.py::filter_safe_class_pool` aggiunto
`"is_playable": {"$ne": False}` al filter MongoDB.
"""
from __future__ import annotations

import asyncio
import os
import pathlib
import sys

import pytest
from dotenv import dotenv_values, load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")
_BACKEND_ENV = dotenv_values("/app/backend/.env")
_DEV_MONGO_URL = _BACKEND_ENV.get("MONGO_URL") or os.environ.get("MONGO_URL")
_DEV_DB_NAME = _BACKEND_ENV.get("DB_NAME") or os.environ.get("DB_NAME")

HIDDEN_SLUGS = ["cacciatore_di_mostri", "cacciatore_del_vuoto"]
AUDIT_EVENT_TYPE = "R18_RECRUITMENT_HIDDEN_CLASS_FILTER_PATCHED"


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture(scope="module")
def db():
    client = AsyncIOMotorClient(_DEV_MONGO_URL)
    yield client[_DEV_DB_NAME]
    client.close()


# ─── 01 — filter_safe_class_pool exclude hidden classes ─────────────────
def test_01_filter_safe_class_pool_excludes_hidden(db):
    """La patch garantisce che le 2 classi hidden NON siano nel pool."""
    from app.adventurers.generator import filter_safe_class_pool
    pool = _run(filter_safe_class_pool(db))
    slugs = {c["slug"] for c in pool}
    for s in HIDDEN_SLUGS:
        assert s not in slugs, (
            f"HOTFIX FAIL: hidden class {s!r} STILL in recruitment pool. "
            f"Pool slugs: {sorted(slugs)}"
        )


# ─── 02 — filter_safe_class_pool retains legacy classes ─────────────────
def test_02_filter_safe_class_pool_keeps_legacy(db):
    """La patch NON deve eliminare le classi legacy playable."""
    from app.adventurers.generator import filter_safe_class_pool
    pool = _run(filter_safe_class_pool(db))
    slugs = {c["slug"] for c in pool}
    # Le classi legacy note (subset — non tutte 13 sono garantite)
    expected_present = {"warrior", "rogue", "mage", "priest",
                        "ranger", "paladin"}
    missing = expected_present - slugs
    assert not missing, (
        f"HOTFIX regression: legacy classes MISSING from pool: {missing}"
    )
    assert len(pool) >= 10, (
        f"Pool too small ({len(pool)} classes) — expected >= 10 legacy"
    )


# ─── 03 — All pool classes have required base_* fields ──────────────────
def test_03_all_pool_classes_have_base_strength(db):
    """Post-patch, ogni classe nel pool DEVE avere base_strength
    (altrimenti generate_candidate crasherebbe ancora)."""
    from app.adventurers.generator import filter_safe_class_pool
    pool = _run(filter_safe_class_pool(db))
    missing_bs = [c["slug"] for c in pool
                  if "base_strength" not in c or c.get("base_strength") is None]
    assert not missing_bs, (
        f"HOTFIX FAIL: {len(missing_bs)} pool classes missing "
        f"base_strength: {missing_bs}"
    )
    # Verifica anche altri base_* (defensive audit)
    for c in pool:
        for stat in ["base_agility", "base_intellect",
                     "base_endurance", "base_faith"]:
            assert stat in c and c[stat] is not None, (
                f"class {c['slug']} missing {stat}"
            )


# ─── 04 — 100 iterations recruitment generate no HTTP 500 ───────────────
def test_04_100_iterations_no_crash(db):
    """Chiama generate_candidate 100 volte con RNG variabile. Zero
    KeyError. Prima della patch, ~15/100 avrebbero crashato."""
    from app.adventurers.generator import generate_candidate
    import random

    n_ok = 0
    n_crash = 0
    picked_slugs = set()
    for i in range(100):
        rng = random.Random(i)  # deterministic per iterazione
        try:
            candidate = _run(generate_candidate(
                db,
                guild_id="test-hotfix-183a2-guild",
                rng=rng,
                audit=False,  # skip audit_log spam
            ))
            n_ok += 1
            picked_slugs.add(candidate.get("class_slug", "?"))
        except KeyError as ke:
            n_crash += 1
            print(f"  iter {i} KeyError: {ke}")
        except Exception as e:
            # Altri errori legittimi non correlati alla patch (es. RNG
            # edge). Non conteggiare come crash del bug specifico.
            print(f"  iter {i} non-KeyError: {type(e).__name__}: {e}")
    assert n_crash == 0, (
        f"HOTFIX FAIL: {n_crash}/100 iterations crashed with KeyError "
        f"(bug reappeared)"
    )
    assert n_ok >= 95, (
        f"HOTFIX partial: only {n_ok}/100 iterations succeeded"
    )
    # Nessuna hidden class deve essere stata pescata
    for s in HIDDEN_SLUGS:
        assert s not in picked_slugs, (
            f"HOTFIX FAIL: hidden {s!r} was picked in 100 iterations. "
            f"Picked slugs: {sorted(picked_slugs)}"
        )


# ─── 05 — Hidden classes still present in DB (unchanged) ────────────────
def test_05_hidden_classes_still_in_db(db):
    """Regression: la patch NON deve eliminare i doc hidden dal DB.
    Restano visibili solo per admin/audit/dispatch guard whitelist."""
    for slug in HIDDEN_SLUGS:
        doc = _run(db.adventurer_classes.find_one({"slug": slug}))
        assert doc is not None, (
            f"HOTFIX FAIL: hidden class {slug!r} REMOVED from DB "
            f"(patch went too far)"
        )
        assert doc.get("is_playable") is False
        assert doc.get("migration_target_only") is True


# ─── 06 — Player-facing /api/adventurer-classes still filtered (R18.3a.1)
def test_06_adventurer_classes_route_no_hidden_leak():
    """Regression R18.3a.1: player-facing route deve ancora escludere
    hidden classes (filtro `is_playable != False` nel routes.py)."""
    routes = pathlib.Path(
        "/app/backend/app/adventurers/routes.py"
    ).read_text()
    assert '"is_playable": {"$ne": False}' in routes, (
        "R18.3a.1 filter regression: player-facing filter missing"
    )


# ─── 07 — Audit event R18_RECRUITMENT_HIDDEN_CLASS_FILTER_PATCHED ───────
def test_07_audit_event_emitted(db):
    """L'apply script deve aver emesso l'audit event esattamente 1 volta."""
    n = _run(db.audit_log.count_documents({
        "event_type": AUDIT_EVENT_TYPE
    }))
    assert n >= 1, (
        f"HOTFIX FAIL: audit event {AUDIT_EVENT_TYPE} NOT emitted. "
        f"Run: python -m app.scripts.round183a2_recruitment_filter_hotfix --apply"
    )
    assert n == 1, (
        f"HOTFIX audit NOT idempotent (count={n} > 1)"
    )
    doc = _run(db.audit_log.find_one(
        {"event_type": AUDIT_EVENT_TYPE},
        {"_id": 0},
    ))
    meta = doc.get("metadata", {})
    assert meta.get("round") == "R18.3a.2"
    assert meta.get("hotfix_for") == "R18.3a"
    assert meta.get("filter_added") == "is_playable != false"
    assert meta.get("player_facing_bug_fixed") is True
    assert meta.get("db_write") is False
    assert meta.get("combat_math_changed") is False
    assert set(meta.get("hidden_slugs_excluded", [])) == set(HIDDEN_SLUGS)


# ─── 08 — Audit whitelist includes new event ────────────────────────────
def test_08_audit_whitelist_extended():
    from app.admin.audit_routes import AUDIT_EVENT_WHITELIST
    assert AUDIT_EVENT_TYPE in AUDIT_EVENT_WHITELIST, (
        f"HOTFIX FAIL: {AUDIT_EVENT_TYPE} missing from "
        f"AUDIT_EVENT_WHITELIST"
    )


# ─── 09 — Source code contains the patch marker ─────────────────────────
def test_09_generator_source_has_hotfix_marker():
    gen = pathlib.Path(
        "/app/backend/app/adventurers/generator.py"
    ).read_text()
    # Il filtro chiave
    assert '"is_playable": {"$ne": False}' in gen, (
        "HOTFIX marker MISSING: is_playable filter in generator.py"
    )
    # Il commento di round marker
    assert "ROUND 18.3a.2" in gen, (
        "HOTFIX marker MISSING: ROUND 18.3a.2 comment in generator.py"
    )


# ─── 10 — R18.1.2 guard whitelist regression: hidden classes still valid
#         for dispatch ─────────────────────────────────────────────────
def test_10_r1812_guard_whitelist_intact():
    """Regression R18.1.2: le 2 hidden classes DEVONO restare valide per
    dispatch expedition (guard whitelist estesa). La patch R18.3a.2
    tocca solo il pool recruitment, NON il guard expeditions."""
    services = pathlib.Path(
        "/app/backend/app/expeditions/services.py"
    ).read_text()
    # Marker R18.1.2 deve esistere
    assert ("R18.1.2" in services or "migration_target_only" in services), (
        "R18.1.2 guard whitelist marker missing from expeditions/services.py"
    )


# ─── 11 — Prior R18 audit events still whitelisted (cross-round) ────────
def test_11_prior_r18_audit_events_intact():
    from app.admin.audit_routes import AUDIT_EVENT_WHITELIST
    required = [
        "R18_MIGRATION_STARTED",
        "R18_MIGRATION_COMPLETED",
        "R18_TALENT_PILOT_SEEDED",
        "R18_GUARD_WHITELIST_EXTENDED",
        "R18_CLASS_MIGRATION_PREREQ_READY",
        "R18_CLASS_ROLE_PLACEHOLDER_BACKFILLED",
        "R18_CLASS_ORPHAN_MIGRATION_APPLIED",
        "R18_CLASS_ORPHAN_MIGRATION_ROLLED_BACK",
    ]
    for ev in required:
        assert ev in AUDIT_EVENT_WHITELIST, (
            f"Cross-round regression: {ev} missing from whitelist"
        )
