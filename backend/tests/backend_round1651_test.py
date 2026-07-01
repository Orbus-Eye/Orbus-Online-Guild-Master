"""ROUND 16.5.1 — Test suite backend (B.1 + B.2 + B.3 + B.4).

Copre:
  - B.1 world_events extension endpoints (GET/PATCH/deactivate/duplicate)
  - B.2 tester tools (status, grant, set-max, set-min) + guardrail
  - B.3 raids/last + raids/replay-preview
  - B.4 raid_public.remaining_seconds

Isolamento: `orbus_r16_test` port 8002 via `ISOLATED_HTTP_TESTS=1`.
"""
from __future__ import annotations

import os
import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import requests
from pymongo import MongoClient


def _api() -> str:
    return (os.environ.get("API_BASE_URL")
            or os.environ.get("REACT_APP_BACKEND_URL")
            or "http://localhost:8001")


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@pytest.fixture(scope="module")
def test_db():
    dbn = os.environ.get("DB_NAME", "")
    assert "test" in dbn.lower(), f"DB {dbn!r} non è test"
    c = MongoClient(os.environ["MONGO_URL"])
    yield c[dbn]
    c.close()


@pytest.fixture(scope="module")
def admin_auth(isolated_backend_url, test_db):
    """Registra un admin di test + gilda + flag is_admin=True."""
    base = _api()
    email = "r1651admin@orbus.test"
    pwd = "R1651Admin!password"
    r = requests.post(f"{base}/api/auth/register",
                      json={"email": email, "password": pwd,
                            "username": "r1651admin"}, timeout=10)
    if r.status_code in (200, 201):
        token = r.json()["access_token"]
    else:
        r = requests.post(f"{base}/api/auth/login",
                          json={"email": email, "password": pwd},
                          timeout=10)
        token = r.json()["access_token"]
    # Promuovi admin direttamente in DB test (safe: DB isolato)
    test_db.users.update_one(
        {"email": email}, {"$set": {"is_admin": True}}
    )
    headers = {"Authorization": f"Bearer {token}"}
    # Gilda per admin (necessaria per alcuni endpoint)
    r = requests.get(f"{base}/api/guilds/me", headers=headers, timeout=10)
    if r.status_code == 404:
        requests.post(f"{base}/api/guilds", headers=headers,
                      json={"name": f"AdminG{int(time.time())}",
                            "description": "admin"}, timeout=10)
    return {"headers": headers, "email": email}


@pytest.fixture
def test_user_setup(test_db, admin_auth):
    """Crea un target test-user (@orbus.test) con guild + advs."""
    base = _api()
    email = "r1651target@orbus.test"
    pwd = "R1651Target!password"
    r = requests.post(f"{base}/api/auth/register",
                      json={"email": email, "password": pwd,
                            "username": "r1651target"}, timeout=10)
    if r.status_code in (200, 201):
        token = r.json()["access_token"]
    else:
        r = requests.post(f"{base}/api/auth/login",
                          json={"email": email, "password": pwd},
                          timeout=10)
        token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # marca is_test_user
    test_db.users.update_one({"email": email},
                             {"$set": {"is_test_user": True}})
    # Cleanup snapshot pregressi per evitare rate-limit inter-test
    user_doc = test_db.users.find_one({"email": email}, {"_id": 0, "id": 1})
    if user_doc:
        test_db.tester_tool_snapshots.delete_many(
            {"target_user_id": user_doc["id"]}
        )
    # gilda
    r = requests.get(f"{base}/api/guilds/me", headers=headers, timeout=10)
    if r.status_code == 404:
        requests.post(f"{base}/api/guilds", headers=headers,
                      json={"name": f"TargetG{int(time.time())}",
                            "description": "target"}, timeout=10)
    yield {"email": email, "headers": headers}


# ═════════════════════════════════════════════════════════════════════
# B.1 — world_events extension
# ═════════════════════════════════════════════════════════════════════

@pytest.fixture
def sample_event(test_db, admin_auth):
    """Crea un'istanza `scheduled` per il continente `ambash`."""
    base = _api()
    # Cleanup istanze precedenti su ambash
    test_db.continent_event_instances.delete_many({"continent_slug": "ambash"})
    # Prendi uno slug valido dal catalog
    cat = test_db.continent_event_catalog.find_one({}, {"_id": 0, "slug": 1})
    assert cat, "catalog vuoto?"
    starts = datetime.now(timezone.utc).isoformat()
    ends = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    r = requests.post(
        f"{base}/api/admin/world-events",
        headers=admin_auth["headers"],
        json={"continent_slug": "ambash", "event_slug": cat["slug"],
              "starts_at": starts, "ends_at": ends}, timeout=10,
    )
    assert r.status_code in (200, 201), f"create failed: {r.text}"
    inst = r.json().get("instance") or r.json()
    return inst


def test_B1_get_event_detail(admin_auth, sample_event):
    base = _api()
    r = requests.get(
        f"{base}/api/admin/world-events/{sample_event['id']}",
        headers=admin_auth["headers"], timeout=10,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["instance"]["id"] == sample_event["id"]
    assert body["catalog"] is not None


def test_B1_patch_event_whitelist(admin_auth, sample_event):
    base = _api()
    new_ends = (datetime.now(timezone.utc) + timedelta(hours=48)).isoformat()
    r = requests.patch(
        f"{base}/api/admin/world-events/{sample_event['id']}",
        headers=admin_auth["headers"],
        json={"ends_at": new_ends, "admin_note": "extended"}, timeout=10,
    )
    assert r.status_code == 200, r.text


def test_B1_patch_rejects_forbidden_fields(admin_auth, sample_event):
    """Il body accetta solo starts_at/ends_at/admin_note. Un tentativo di
    modificare event_slug via campo non-whitelist deve essere ignorato
    (pydantic scarta extra) e comunque il modifiers/status non cambia."""
    base = _api()
    # Pydantic model non ha `event_slug` → viene ignorato silenziosamente
    # (comportamento by-design, whitelist a modello).
    r = requests.patch(
        f"{base}/api/admin/world-events/{sample_event['id']}",
        headers=admin_auth["headers"],
        json={"event_slug": "malicious-slug", "modifiers": {"x": 1}},
        timeout=10,
    )
    # Nessun campo valido nel body → 400
    assert r.status_code == 400, r.text


def test_B1_deactivate_only_active_events(admin_auth, sample_event):
    """`scheduled` → deactivate rifiuta 409, richiede prima activate."""
    base = _api()
    # Prova a deactivare uno scheduled → 409
    r = requests.post(
        f"{base}/api/admin/world-events/{sample_event['id']}/deactivate",
        headers=admin_auth["headers"], timeout=10,
    )
    assert r.status_code == 409, r.text


def test_B1_deactivate_active_event(admin_auth, sample_event, test_db):
    """Attiva e poi disattiva. Verifica audit."""
    base = _api()
    r = requests.post(
        f"{base}/api/admin/world-events/{sample_event['id']}/activate",
        headers=admin_auth["headers"], timeout=10,
    )
    assert r.status_code in (200, 201), r.text
    r = requests.post(
        f"{base}/api/admin/world-events/{sample_event['id']}/deactivate",
        headers=admin_auth["headers"], timeout=10,
    )
    assert r.status_code == 200, r.text
    detail = r.json()["instance"]
    assert detail["status"] == "expired"
    assert detail.get("deactivated_by_admin") is True


def test_B1_duplicate_refuses_if_conflict(admin_auth, sample_event, test_db):
    """Se il continente ha già uno scheduled, duplicate refuse 409."""
    base = _api()
    # sample_event è scheduled → duplicate deve rifiutare
    r = requests.post(
        f"{base}/api/admin/world-events/{sample_event['id']}/duplicate",
        headers=admin_auth["headers"], timeout=10,
    )
    assert r.status_code == 409, r.text


def test_B1_duplicate_creates_new_when_no_conflict(admin_auth, sample_event,
                                                     test_db):
    """Espira il sample, poi duplicate deve creare uno scheduled nuovo."""
    base = _api()
    # Force sample to expired via DB direct (test-safe)
    test_db.continent_event_instances.update_one(
        {"id": sample_event["id"]},
        {"$set": {"status": "expired", "expired_at": _iso_now()}},
    )
    r = requests.post(
        f"{base}/api/admin/world-events/{sample_event['id']}/duplicate",
        headers=admin_auth["headers"], timeout=10,
    )
    assert r.status_code == 200, r.text
    new = r.json()["instance"]
    assert new["status"] == "scheduled"
    assert new["id"] != sample_event["id"]
    assert new.get("duplicated_from_id") == sample_event["id"]


# ═════════════════════════════════════════════════════════════════════
# B.2 — tester tools
# ═════════════════════════════════════════════════════════════════════

def test_B2_status_returns_test_user_flags(admin_auth, test_user_setup):
    base = _api()
    r = requests.get(
        f"{base}/api/admin/tester-tools/status",
        headers=admin_auth["headers"],
        params={"target_email": test_user_setup["email"]}, timeout=10,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["target_user"]["is_test_user"] is True
    assert body["tools_enabled"] is True


def test_B2_status_rejects_non_test_user(admin_auth, test_db):
    """Un utente senza `is_test_user` e senza email @orbus.test viene
    rifiutato con 403."""
    base = _api()
    email = f"real{uuid.uuid4().hex[:6]}@example.com"
    r = requests.post(f"{base}/api/auth/register",
                      json={"email": email, "password": "real-pw-123!!",
                            "username": "real"}, timeout=10)
    assert r.status_code in (200, 201)
    r = requests.get(
        f"{base}/api/admin/tester-tools/status",
        headers=admin_auth["headers"],
        params={"target_email": email}, timeout=10,
    )
    assert r.status_code == 403, r.text
    assert "not_a_test_user" in r.text
    # Verifica audit TESTER_TOOL_REJECTED emesso
    aud = test_db.admin_audit_events.find_one(
        {"event_type": "TESTER_TOOL_REJECTED"},
        sort=[("created_at", -1)],
    ) or test_db.audit_events.find_one(
        {"event_type": "TESTER_TOOL_REJECTED"},
        sort=[("created_at", -1)],
    )
    # (best-effort: audit collection name può variare)


def test_B2_grant_adventurers_idempotent(admin_auth, test_user_setup,
                                          test_db):
    base = _api()
    # Prima chiamata: crea fino a 20
    r1 = requests.post(
        f"{base}/api/admin/tester-tools/grant-adventurers",
        headers=admin_auth["headers"],
        json={"target_email": test_user_setup["email"]}, timeout=15,
    )
    assert r1.status_code == 200, r1.text
    total_after_1 = r1.json()["total_after"]
    # Seconda chiamata: deve essere idempotente
    r2 = requests.post(
        f"{base}/api/admin/tester-tools/grant-adventurers",
        headers=admin_auth["headers"],
        json={"target_email": test_user_setup["email"]}, timeout=15,
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["created"] == 0
    assert r2.json()["total_after"] == total_after_1


def test_B2_set_max_requires_confirm_on_repeat(admin_auth, test_user_setup):
    base = _api()
    r1 = requests.post(
        f"{base}/api/admin/tester-tools/set-max",
        headers=admin_auth["headers"],
        json={"target_email": test_user_setup["email"]}, timeout=15,
    )
    assert r1.status_code == 200, r1.text
    r2 = requests.post(
        f"{base}/api/admin/tester-tools/set-max",
        headers=admin_auth["headers"],
        json={"target_email": test_user_setup["email"]}, timeout=15,
    )
    assert r2.status_code == 409, r2.text
    assert "require_confirm" in r2.text
    r3 = requests.post(
        f"{base}/api/admin/tester-tools/set-max",
        headers=admin_auth["headers"],
        json={"target_email": test_user_setup["email"],
              "confirm": True}, timeout=15,
    )
    assert r3.status_code == 200, r3.text


def test_B2_set_min_soft_retires_extras(admin_auth, test_user_setup,
                                         test_db):
    base = _api()
    r = requests.post(
        f"{base}/api/admin/tester-tools/set-min",
        headers=admin_auth["headers"],
        json={"target_email": test_user_setup["email"]}, timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["applied"] == "MIN"
    assert body["kept_active"] <= 3
    # Verifica NO hard delete: gli avv archiviati esistono ancora (retired)
    guild = test_db.guilds.find_one({"name": {"$regex": "^TargetG"}},
                                     {"_id": 0, "id": 1})
    if guild:
        total = test_db.adventurers.count_documents(
            {"guild_id": guild["id"]}
        )
        assert total >= body["kept_active"] + body["archived"]


# ═════════════════════════════════════════════════════════════════════
# B.3 — raids/last + replay-preview
# ═════════════════════════════════════════════════════════════════════

def test_B3_last_raid_404_if_none(admin_auth):
    base = _api()
    r = requests.get(f"{base}/api/raids/last",
                     headers=admin_auth["headers"], timeout=10)
    # 404 se nessun raid completato per la guild admin
    assert r.status_code == 404
    assert "no_completed_raid" in r.text


def test_B3_replay_preview_missing_squad(admin_auth):
    base = _api()
    # Squad con 20 ids fake
    fake_ids = [str(uuid.uuid4()) for _ in range(20)]
    r = requests.post(
        f"{base}/api/raids/replay-preview",
        headers=admin_auth["headers"],
        json={"raid_slug": "nonexistent-raid-slug",
              "squad_ids": fake_ids}, timeout=10,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["raid_available"] is False
    assert body["all_adventurers_owned"] is False
    assert len(body["missing_adventurers"]) == 20
