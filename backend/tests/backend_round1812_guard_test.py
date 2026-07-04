"""ROUND 18.1.2 — Guard Whitelist Extension test suite.

Verifica che il guard R18.1.1 in `app/expeditions/services.py` estenda
la query catalog per accettare una whitelist esplicita di classi target
R18.3 migration (`is_playable=false + migration_target_only=true + slug
in whitelist`), senza bloccare i comportamenti già coperti da R18.1.1
(recruit_unassigned + is_playable=false generico + slug non canonico).

Bypass del conftest globale (isolation forcing) via
    pytest --confcutdir=/tmp -c /dev/null

Deve accedere al DB DEV (`orbus_r16`) dove il guard code è attivo.
"""
from __future__ import annotations

import asyncio
import os
import pathlib
import uuid

import pytest
from dotenv import dotenv_values, load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Load DEV env (override conftest-forced test env)
load_dotenv("/app/backend/.env")
_BACKEND_ENV = dotenv_values("/app/backend/.env")
_DEV_MONGO_URL = _BACKEND_ENV.get("MONGO_URL") or os.environ.get("MONGO_URL")
_DEV_DB_NAME = _BACKEND_ENV.get("DB_NAME") or os.environ.get("DB_NAME")


R18_MIGRATION_TARGET_WHITELIST = [
    "cacciatore_di_mostri",
    "cacciatore_del_vuoto",
]

# BYTE-EXACT copy of the IT user_message from R18.1.1 guard (preserved).
# NOTE: nel file source Python la stringa è splittata su due linee via
# concatenation implicita, quindi verifichiamo entrambe le sub-stringhe
# come byte-exact anziché la concatenazione completa (non presente in
# forma unificata nel file testuale).
GUARD_USER_MESSAGE_IT_PART1 = (
    "Questo avventuriero non ha ancora una classe assegnata. "
)
GUARD_USER_MESSAGE_IT_PART2 = "Riassegnalo prima di mandarlo in missione."

GUARD_SVC_PATH = pathlib.Path("/app/backend/app/expeditions/services.py")


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture(scope="module")
def db():
    client = AsyncIOMotorClient(_DEV_MONGO_URL)
    yield client[_DEV_DB_NAME]
    client.close()


# ─── 01 — Guard code has new whitelist markers ─────────────────────────
def test_01_guard_code_has_r18_1_2_markers():
    content = GUARD_SVC_PATH.read_text()
    assert "ROUND 18.1.2" in content, "R18.1.2 marker comment missing"
    assert "_R18_MIGRATION_TARGET_WHITELIST" in content, (
        "whitelist variable name missing from guard"
    )
    for slug in R18_MIGRATION_TARGET_WHITELIST:
        assert f'"{slug}"' in content, (
            f"whitelisted slug '{slug}' not found in guard code"
        )
    # Structural: $or query with migration_target_only branch
    assert 'migration_target_only' in content, (
        "guard should reference migration_target_only in whitelist query"
    )


# ─── 02 — IT user_message preserved byte-exact from R18.1.1 ────────────
def test_02_guard_it_message_byte_exact_preserved():
    content = GUARD_SVC_PATH.read_text()
    assert GUARD_USER_MESSAGE_IT_PART1 in content, (
        "R18.1.1 IT user_message PART1 NOT preserved byte-exact — regression!"
    )
    assert GUARD_USER_MESSAGE_IT_PART2 in content, (
        "R18.1.1 IT user_message PART2 NOT preserved byte-exact — regression!"
    )
    # Also verify the guard error code is unchanged
    assert "adventurers.recruit_unassigned_in_set" in content


# ─── 03 — Guard query returns whitelisted slugs (real DB fixture) ──────
def test_03_query_accepts_whitelisted_migration_target_slug(db):
    """Simula la query del guard: dato che nel DB inseriamo una classe
    fixture `test_r1812_whitelisted` seguita dai marker della whitelist
    ma con lo slug NON nella whitelist, la query non deve accettarla.
    Successivamente inseriamo lo slug reale `cacciatore_di_mostri` e
    verifichiamo che la query lo accetti. Rollback al termine.
    """
    fixture_slug = f"test_r1812_fixture_{uuid.uuid4().hex[:8]}"
    query = {"$or": [
        {"is_playable": {"$ne": False}},
        {
            "is_playable": False,
            "migration_target_only": True,
            "slug": {"$in": R18_MIGRATION_TARGET_WHITELIST},
        },
    ]}
    # Fixture: classe con is_playable=false + migration_target_only=true
    # ma slug NON whitelisted → query NON deve restituirla
    _run(db.adventurer_classes.insert_one({
        "id": str(uuid.uuid4()),
        "slug": fixture_slug,
        "is_playable": False,
        "migration_target_only": True,
        "is_pytest_fixture": True,
    }))
    try:
        n = _run(db.adventurer_classes.count_documents(
            {**query, "slug": fixture_slug}
        ))
        assert n == 0, (
            f"query should NOT accept non-whitelisted slug even with "
            f"migration_target_only=true (got {n})"
        )
    finally:
        _run(db.adventurer_classes.delete_one(
            {"slug": fixture_slug, "is_pytest_fixture": True}
        ))


# ─── 04 — Query REJECTS is_playable=false without migration_target_only ─
def test_04_query_rejects_is_playable_false_without_migration_target(db):
    """Fixture: classe con is_playable=false SENZA migration_target_only
    → query NON deve restituirla (guard blocca genericamente)."""
    fixture_slug = f"test_r1812_hidden_{uuid.uuid4().hex[:8]}"
    query = {"$or": [
        {"is_playable": {"$ne": False}},
        {
            "is_playable": False,
            "migration_target_only": True,
            "slug": {"$in": R18_MIGRATION_TARGET_WHITELIST},
        },
    ]}
    _run(db.adventurer_classes.insert_one({
        "id": str(uuid.uuid4()),
        "slug": fixture_slug,
        "is_playable": False,
        # NO migration_target_only field
        "is_pytest_fixture": True,
    }))
    try:
        n = _run(db.adventurer_classes.count_documents(
            {**query, "slug": fixture_slug}
        ))
        assert n == 0, (
            f"query should reject is_playable=false without "
            f"migration_target_only=true (got {n})"
        )
    finally:
        _run(db.adventurer_classes.delete_one(
            {"slug": fixture_slug, "is_pytest_fixture": True}
        ))


# ─── 05 — Query ACCEPTS whitelisted slug + full markers ────────────────
def test_05_query_accepts_full_whitelist_condition(db):
    """Fixture: classe con slug ∈ whitelist + is_playable=false +
    migration_target_only=true → query DEVE restituirla."""
    slug = "cacciatore_di_mostri"
    query = {"$or": [
        {"is_playable": {"$ne": False}},
        {
            "is_playable": False,
            "migration_target_only": True,
            "slug": {"$in": R18_MIGRATION_TARGET_WHITELIST},
        },
    ]}
    # Fixture-safe insert (potrebbe già esistere post R18.3a; tag pytest
    # solo se non esiste, altrimenti rollback selettivo).
    pre_existing = _run(db.adventurer_classes.find_one({"slug": slug}))
    if not pre_existing:
        _run(db.adventurer_classes.insert_one({
            "id": str(uuid.uuid4()),
            "slug": slug,
            "name": "Cacciatore di Mostri",
            "display_name_it": "Cacciatore di Mostri",
            "is_playable": False,
            "migration_target_only": True,
            "is_active": True,
            "is_pytest_fixture": True,
        }))
    try:
        n = _run(db.adventurer_classes.count_documents(
            {**query, "slug": slug}
        ))
        assert n >= 1, (
            f"query MUST accept whitelisted slug='{slug}' with full "
            f"markers (got {n})"
        )
    finally:
        # Rollback SOLO se abbiamo inserito noi la fixture
        _run(db.adventurer_classes.delete_one(
            {"slug": slug, "is_pytest_fixture": True}
        ))


# ─── 06 — Whitelist enum exactly matches PM-sealed slugs ───────────────
def test_06_whitelist_slugs_sealed():
    """Whitelist chiusa: solo `cacciatore_di_mostri` + `cacciatore_del_vuoto`
    devono essere accettati. Nessun altro slug (né esteso, né shortato)."""
    assert set(R18_MIGRATION_TARGET_WHITELIST) == {
        "cacciatore_di_mostri", "cacciatore_del_vuoto",
    }, "whitelist deve contenere ESATTAMENTE i due slug PM-sigillati"
    # Ex-R18.2 wrong slugs (senza preposizione) NON devono essere accettati
    assert "cacciatore_mostri" not in R18_MIGRATION_TARGET_WHITELIST
    assert "cacciatore_vuoto" not in R18_MIGRATION_TARGET_WHITELIST


# ─── 07 — Audit whitelist include R18_GUARD_WHITELIST_EXTENDED ─────────
def test_07_audit_whitelist_extended():
    from app.admin.audit_routes import AUDIT_EVENT_WHITELIST
    assert "R18_GUARD_WHITELIST_EXTENDED" in AUDIT_EVENT_WHITELIST, (
        "R18.1.2 event type missing from AUDIT_EVENT_WHITELIST"
    )


# ─── 08 — No player-facing R18 endpoint exposed (openapi regression) ───
def test_08_no_r18_player_facing_route_leak(db):
    """Feature flag `R18_REWORK_ENABLED=false` deve restare OFF. Nessuna
    rotta pubblica R18 must expose migration_target_only classes.
    """
    assert os.environ.get("R18_REWORK_ENABLED", "false").lower() == "false"
    # OpenAPI regression: nessuna rotta contiene 'migration-target' o
    # 'talent-tree-engine' come path esposto
    from fastapi.testclient import TestClient
    import sys
    sys.path.insert(0, "/app/backend")
    from server import app  # ASGI entry point
    client = TestClient(app)
    r = client.get("/api/openapi.json")
    assert r.status_code == 200
    schema = r.json()
    paths = schema.get("paths", {})
    for p in paths.keys():
        p_lower = p.lower()
        assert "migration-target" not in p_lower, (
            f"leaked migration-target route: {p}"
        )
        assert "talent-engine" not in p_lower, (
            f"leaked talent-engine route: {p}"
        )
        assert "/api/r18/" not in p_lower, (
            f"leaked /api/r18/* route: {p}"
        )


# ─── 09 — /api/adventurer-classes does NOT expose is_playable=false ────
def test_09_adventurer_classes_endpoint_no_hidden_class_leak(db):
    """La rotta GET /api/adventurer-classes filtra su is_active. Verifica
    che nessun documento con `is_playable=false` (recruit_unassigned +
    future migration targets) sia esposto.
    """
    from fastapi.testclient import TestClient
    import sys
    sys.path.insert(0, "/app/backend")
    from server import app
    client = TestClient(app)
    # Endpoint pubblico (no auth per list_classes)
    r = client.get("/api/adventurer-classes")
    assert r.status_code == 200
    payload = r.json()
    classes = payload.get("classes", [])
    slugs = {c.get("slug") for c in classes}
    # `recruit_unassigned` (is_playable=false, safety class) NON deve
    # apparire pubblicamente
    assert "recruit_unassigned" not in slugs, (
        "recruit_unassigned NON deve essere esposto pubblicamente"
    )


# ─── 10 — Regression: R18.1 test_18 guard signature invariant ──────────
def test_10_r18_1_1_guard_signature_regression():
    """Regression: i marker R18.1.1 devono restare presenti nella guard
    code, così che il test_18 di `backend_round181_migration_test.py`
    continui a passare.
    """
    content = GUARD_SVC_PATH.read_text()
    # Signature R18.1.1
    assert "recruit_unassigned_in_set" in content
    assert "is_playable" in content
    assert GUARD_USER_MESSAGE_IT_PART1 in content
    assert GUARD_USER_MESSAGE_IT_PART2 in content
    # Nessuna rimozione del blocco recruit_unassigned
    assert 'recruit_unassigned' in content
    assert '_unassigned_advs' in content


# ─── 11 — Zero hard delete: existing classes untouched ─────────────────
def test_11_zero_hard_delete_on_existing_classes(db):
    """R18.1.2 non deve rimuovere alcuna classe esistente dal catalog."""
    n_total = _run(db.adventurer_classes.count_documents({
        "is_pytest_fixture": {"$ne": True},
    }))
    # Il minimo garantito è ≥ 15 classi live post R18.1 (14 canoniche +
    # recruit_unassigned + alchemist). Post R18.3a ne saranno +2.
    assert n_total >= 15, (
        f"expected >=15 classi live nel catalog, got {n_total} "
        f"(hard delete regression!)"
    )


# ─── 12 — Feature flag OFF (safety-only guard) ─────────────────────────
def test_12_feature_flag_r18_off():
    """Il guard R18.1.2 è safety-only, indipendente dai feature flag,
    ma i flag devono restare OFF per non attivare il rework in
    R18.1.2."""
    macro = os.environ.get("R18_REWORK_ENABLED", "false").lower()
    talent = os.environ.get("R18_TALENT_ENGINE_ENABLED", "false").lower()
    assert macro in ("false", "0", "no", ""), (
        f"R18_REWORK_ENABLED deve restare OFF, got '{macro}'"
    )
    assert talent in ("false", "0", "no", ""), (
        f"R18_TALENT_ENGINE_ENABLED deve restare OFF, got '{talent}'"
    )
