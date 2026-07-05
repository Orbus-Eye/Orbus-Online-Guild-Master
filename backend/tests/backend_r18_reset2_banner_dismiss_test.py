"""R18.Reset.2 — Fresh Start Banner UI/API Test Suite (backend).

Tests verificano:
- endpoint `POST /api/guilds/me/r18-reset-banner/dismiss` (auth, isolation,
  idempotency, side-effects)
- endpoint `GET /api/guilds/me/r18-reset-banner` (message byte-exact IT)
- `/api/guilds/me` espone `r18_reset1b_banner_dismissed`
- nessun leak di metadata tecnici (backup, archive, apply_id, ecc.)
- regressione core endpoint (adventurers, dungeons)
- freeze OFF (nessun 503 su login)

Pattern: 2 utenti temporanei creati via `/api/auth/register` con guild
distinte + cleanup finale delle guild e degli utenti.
"""
from __future__ import annotations

import asyncio
import os
import uuid

import pytest
import requests
from dotenv import dotenv_values
from motor.motor_asyncio import AsyncIOMotorClient

_ENV = dotenv_values("/app/backend/.env")
PROD_MONGO_URL = _ENV["MONGO_URL"]
PROD_DB_NAME = _ENV["DB_NAME"]

with open("/app/frontend/.env") as f:
    for line in f:
        if line.startswith("REACT_APP_BACKEND_URL="):
            BASE = line.split("=", 1)[1].strip().strip('"').strip("'")
            break

BANNER_MESSAGE_IT_BYTE_EXACT = (
    "Le gilde sono state riallineate per il nuovo inizio di Orbus. "
    "Il nome della tua gilda è stato preservato; progressi, roster e "
    "risorse sono ripartiti da zero."
)

TENANT_A = f"reset2test_a_{uuid.uuid4().hex[:8]}"
TENANT_B = f"reset2test_b_{uuid.uuid4().hex[:8]}"


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture(scope="module")
def prod_db():
    client = AsyncIOMotorClient(PROD_MONGO_URL)
    yield client[PROD_DB_NAME]
    client.close()


def _register_and_login(email_prefix: str) -> dict:
    """Register a fresh user + create guild; return dict with token, user_id, guild_id."""
    email = f"{email_prefix}@orbus.test"
    pwd = "PasswordR18Reset2!"
    # Register
    r = requests.post(f"{BASE}/api/auth/register", json={
        "email": email, "password": pwd, "username": email_prefix,
    }, timeout=15)
    if r.status_code not in (200, 201):
        # try login if already registered
        r = requests.post(f"{BASE}/api/auth/login", json={
            "email": email, "password": pwd,
        }, timeout=15)
    assert r.status_code in (200, 201), f"register/login {email}: {r.status_code} {r.text}"
    tok = r.json()["access_token"]
    hdr = {"Authorization": f"Bearer {tok}"}
    # Ensure guild exists
    gr = requests.get(f"{BASE}/api/guilds/me", headers=hdr, timeout=15)
    if gr.status_code == 404:
        cr = requests.post(f"{BASE}/api/guilds", headers=hdr, json={
            "name": f"Guild_{email_prefix}",
            "description": "R18.Reset.2 test guild",
        }, timeout=15)
        assert cr.status_code in (200, 201), f"create guild {email}: {cr.status_code} {cr.text}"
        gr = requests.get(f"{BASE}/api/guilds/me", headers=hdr, timeout=15)
    assert gr.status_code == 200, f"get guild {email}: {gr.status_code}"
    body = gr.json()
    # /api/guilds/me returns {"guild": {...}} wrapper
    guild = body.get("guild") if isinstance(body, dict) and "guild" in body else body
    return {"token": tok, "hdr": hdr, "email": email, "guild": guild}


@pytest.fixture(scope="module")
def tenant_a():
    return _register_and_login(TENANT_A)


@pytest.fixture(scope="module")
def tenant_b():
    return _register_and_login(TENANT_B)


@pytest.fixture(scope="module", autouse=True)
def cleanup(prod_db):
    """Reset banner flag for tenants after tests (best-effort)."""
    yield
    async def _cleanup():
        for prefix in (TENANT_A, TENANT_B):
            email = f"{prefix}@orbus.test"
            u = await prod_db.users.find_one({"email": email})
            if u:
                await prod_db.guilds.delete_many({"owner_user_id": u["id"]})
                await prod_db.users.delete_one({"id": u["id"]})
    _run(_cleanup())


# ─── 1 — endpoint richiede auth ────────────────────────────────────
def test_1_dismiss_requires_auth():
    r = requests.post(f"{BASE}/api/guilds/me/r18-reset-banner/dismiss", timeout=15)
    assert r.status_code in (401, 403), f"expected 401/403 without token, got {r.status_code}"


# ─── 2 — dismiss setta il flag SOLO sulla propria guild ────────────
def test_2_dismiss_sets_flag_own_guild(tenant_a, prod_db):
    r = requests.post(f"{BASE}/api/guilds/me/r18-reset-banner/dismiss",
                      headers=tenant_a["hdr"], timeout=15)
    assert r.status_code == 200, f"dismiss A: {r.status_code} {r.text}"
    body = r.json()
    assert body.get("r18_reset1b_banner_dismissed") is True
    # verify DB
    gid = tenant_a["guild"]["id"]
    doc = _run(prod_db.guilds.find_one({"id": gid}))
    assert doc is not None
    assert doc.get("r18_reset1b_banner_dismissed") is True


# ─── 3 — idempotenza: 2° e 3° chiamata restano 200 ─────────────────
def test_3_dismiss_idempotent(tenant_a):
    for _ in range(3):
        r = requests.post(f"{BASE}/api/guilds/me/r18-reset-banner/dismiss",
                          headers=tenant_a["hdr"], timeout=15)
        assert r.status_code == 200
        assert r.json().get("r18_reset1b_banner_dismissed") is True


# ─── 4 — isolation: dismiss di A NON tocca guild di B ──────────────
def test_4_dismiss_isolates_tenant(tenant_b, prod_db):
    # B non ha ancora fatto dismiss → deve essere False
    gid_b = tenant_b["guild"]["id"]
    doc_b = _run(prod_db.guilds.find_one({"id": gid_b}))
    # explicit default False
    assert doc_b.get("r18_reset1b_banner_dismissed") in (False, None), (
        f"tenant B banner_dismissed leaked: {doc_b.get('r18_reset1b_banner_dismissed')}"
    )


# ─── 5 — banner visibile se dismissed=false ────────────────────────
def test_5_banner_visible_if_not_dismissed(tenant_b):
    r = requests.get(f"{BASE}/api/guilds/me/r18-reset-banner",
                     headers=tenant_b["hdr"], timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert body["show"] is True
    assert body["dismissed"] is False
    assert body["message_it"] == BANNER_MESSAGE_IT_BYTE_EXACT


# ─── 6 — banner non visibile dopo dismiss ──────────────────────────
def test_6_banner_hidden_after_dismiss(tenant_a):
    r = requests.get(f"{BASE}/api/guilds/me/r18-reset-banner",
                     headers=tenant_a["hdr"], timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert body["show"] is False
    assert body["dismissed"] is True


# ─── 7 — endpoint POST corretto (verifica route accessibile e attiva) ─
def test_7_dismiss_endpoint_route_active(tenant_b):
    r = requests.post(f"{BASE}/api/guilds/me/r18-reset-banner/dismiss",
                      headers=tenant_b["hdr"], timeout=15)
    assert r.status_code == 200
    assert "r18_reset1b_banner_dismissed" in r.json()


# ─── 8 — refresh: GET conferma stato dismissed permane ─────────────
def test_8_refresh_state_persists(tenant_a):
    r = requests.get(f"{BASE}/api/guilds/me/r18-reset-banner",
                     headers=tenant_a["hdr"], timeout=15)
    assert r.status_code == 200
    assert r.json()["dismissed"] is True


# ─── 9 — migration-banner endpoint resta funzionante ───────────────
def test_9_migration_banner_still_works(tenant_a):
    r = requests.get(f"{BASE}/api/guilds/me/migration-banner",
                     headers=tenant_a["hdr"], timeout=15)
    assert r.status_code == 200
    # New guild has no R18.3c migrations
    assert r.json().get("migrated_count") == 0
    # Ensure separate field: R18.Reset.2 doesn't touch migration-banner state
    assert "message_it" in r.json()


# ─── 10 — nessun leak tecnico in /api/guilds/me ────────────────────
def test_10_no_technical_leak_in_guild_me(tenant_a):
    r = requests.get(f"{BASE}/api/guilds/me", headers=tenant_a["hdr"], timeout=15)
    assert r.status_code == 200
    raw = r.json()
    body = raw.get("guild") if isinstance(raw, dict) and "guild" in raw else raw
    # allowed exposure
    assert body.get("r18_reset1b_banner_dismissed") is True
    # forbidden leaks
    forbidden = {
        "r18_reset1b_hotfix_v1_2", "r18_reset1b_hotfix_v1_3",
        "r18_reset1b_hotfix_v1_3_at", "r18_reset1b_hotfix_v1_3_apply_id",
        "r18_reset1b_seed_source", "r18_reset1b_stat_source",
        "apply_id", "backup_path", "archive_count", "phase13_unbaked",
    }
    for k in forbidden:
        assert k not in body, f"technical field leaked: {k}"


# ─── 11 — regression: login OK 200 ─────────────────────────────────
def test_11_login_regression():
    r = requests.post(f"{BASE}/api/auth/login", json={
        "email": "tester@orbus.test", "password": "password123",
    }, timeout=15)
    assert r.status_code == 200, f"login regression FAIL: {r.status_code}"
    assert "access_token" in r.json()


# ─── 12 — regression: recruitment candidates 200 ───────────────────
def test_12_recruitment_regression(tenant_a):
    r = requests.get(f"{BASE}/api/recruitment/candidates",
                     headers=tenant_a["hdr"], timeout=15)
    assert r.status_code == 200


# ─── 13 — regression: adventurers list 200 ─────────────────────────
def test_13_adventurers_regression(tenant_a):
    r = requests.get(f"{BASE}/api/adventurers",
                     headers=tenant_a["hdr"], timeout=15)
    assert r.status_code == 200


# ─── 14 — regression: dungeons + expedition non-500 ────────────────
def test_14_dungeons_and_expedition_regression(tenant_a):
    r = requests.get(f"{BASE}/api/dungeons",
                     headers=tenant_a["hdr"], timeout=15)
    assert r.status_code == 200
    # expedition create should NOT be 500 (functional errors accepted)
    dungeons = r.json() if isinstance(r.json(), list) else (r.json().get("items") or [])
    if dungeons:
        adv_r = requests.get(f"{BASE}/api/adventurers",
                             headers=tenant_a["hdr"], timeout=15)
        advs = adv_r.json() if isinstance(adv_r.json(), list) else (adv_r.json().get("items") or [])
        if advs:
            e = requests.post(f"{BASE}/api/expeditions",
                              headers=tenant_a["hdr"],
                              json={"dungeon_id": dungeons[0].get("id"),
                                    "adventurer_ids": [a["id"] for a in advs[:3]]},
                              timeout=15)
            assert e.status_code != 500, f"expedition POST returned 500: {e.text[:300]}"


# ─── 15 — freeze non riattivato (no 503 su login) ──────────────────
def test_15_freeze_off():
    import pathlib
    assert not pathlib.Path("/tmp/orbus_maintenance.flag").exists()
    assert not pathlib.Path("/tmp/orbus_internal_job_freeze.flag").exists()
    r = requests.post(f"{BASE}/api/auth/login", json={
        "email": "tester@orbus.test", "password": "password123",
    }, timeout=15)
    assert r.status_code != 503, "login returned 503: freeze re-activated?"
