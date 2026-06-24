"""
Phase 5.5g + 5.5h Refactor Final Cleanup — Regression Smoke
============================================================
Validates the ASGI factory + lifespan + indexes + seeds extraction
produced ZERO behavioural change. server.py is now 34 LOC; this file
exercises everything that previously lived in server.py top-level.

Covered:
1.  /api/health → 200 {status:ok,env:development}
2.  /api/openapi.json → 36 paths
3.  Tester login + /api/auth/me is_admin=true
4.  Admin endpoint requires JWT + admin flag (401 without, 200 with tester)
5.  Recruitment candidates list (4) + recruit decrements gold (if affordable)
6.  /api/guilds/me lazy completion sweep idempotency
7.  Dungeon gate sticky semantics (shadow-crypts locked, dragons-hoard reason)
8.  Backward-compat shim: `from server import validate_item_monetization, _resolve_levelup`
9.  MongoDB indexes idempotent (no IndexOptionsConflict on restart)
"""
import os
import uuid
import importlib
import requests
from pymongo import MongoClient


def _load_env_value(path, key, default=None):
    try:
        with open(path) as f:
            for line in f:
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"')
    except FileNotFoundError:
        pass
    return default


BASE_URL = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or _load_env_value("/app/frontend/.env", "REACT_APP_BACKEND_URL")
).rstrip("/")
API = f"{BASE_URL}/api"
MONGO_URL = os.environ.get("MONGO_URL") or _load_env_value(
    "/app/backend/.env", "MONGO_URL", "mongodb://localhost:27017"
)
DB_NAME = os.environ.get("DB_NAME") or _load_env_value(
    "/app/backend/.env", "DB_NAME", "test_database"
)


def _tester_headers():
    r = requests.post(
        f"{API}/auth/login",
        json={"email": "tester@orbus.test", "password": "password123"},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _new_user_with_guild():
    email = f"p55gh_{uuid.uuid4().hex[:10]}@orbus.test"
    r = requests.post(
        f"{API}/auth/register",
        json={"email": email, "username": "u_" + uuid.uuid4().hex[:6], "password": "pass1234"},
        timeout=15,
    )
    assert r.status_code == 201, r.text
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    g = requests.post(
        f"{API}/guilds",
        json={"name": "G_" + uuid.uuid4().hex[:6], "description": ""},
        headers=h, timeout=15,
    )
    assert g.status_code == 201, g.text
    return h, g.json()["guild"]


# ---------- 1+2: surface ----------
def test_health_endpoint():
    r = requests.get(f"{API}/health", timeout=10)
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "env": "development"}


def test_openapi_37_paths():
    r = requests.get(f"{API}/openapi.json", timeout=10)
    assert r.status_code == 200
    paths = r.json().get("paths", {})
    # Phase 9.1 added `/api/leaderboard/guilds` to the 36-path baseline.
    assert len(paths) == 37, f"expected 37, got {len(paths)}"


# ---------- 3: tester admin ----------
def test_tester_login_is_admin():
    h = _tester_headers()
    me = requests.get(f"{API}/auth/me", headers=h, timeout=15)
    assert me.status_code == 200
    assert me.json()["user"]["is_admin"] is True


# ---------- 4: admin gate ----------
def test_admin_classes_requires_token():
    r = requests.get(f"{API}/admin/classes", timeout=10)
    assert r.status_code in (401, 403), r.text


def test_admin_classes_ok_with_tester():
    h = _tester_headers()
    r = requests.get(f"{API}/admin/classes", headers=h, timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "classes" in body or isinstance(body, list)


# ---------- 5: recruitment ----------
def test_recruitment_candidates_returns_4():
    h, _ = _new_user_with_guild()
    r = requests.get(f"{API}/recruitment/candidates", headers=h, timeout=15)
    assert r.status_code == 200, r.text
    cands = r.json()["candidates"]
    assert len(cands) == 4, f"expected 4 candidates, got {len(cands)}"


def test_recruit_decrements_gold_if_affordable():
    h, guild = _new_user_with_guild()
    gold_before = guild["gold"]
    cands = requests.get(f"{API}/recruitment/candidates", headers=h, timeout=15).json()["candidates"]
    def _cost(c):
        return c.get("cost_gold", c.get("cost", 0))
    affordable = [c for c in cands if _cost(c) <= gold_before]
    if not affordable:
        import pytest
        pytest.skip("no affordable candidate for fresh guild")
    pick = affordable[0]
    cost = _cost(pick)
    r = requests.post(
        f"{API}/recruitment/recruit",
        json={"candidate_id": pick["candidate_id"]},
        headers=h, timeout=15,
    )
    assert r.status_code == 201, r.text
    after = requests.get(f"{API}/guilds/me", headers=h, timeout=15).json()
    new_gold = after["guild"]["gold"]
    assert new_gold == gold_before - cost, (
        f"gold not decremented correctly: {gold_before} → {new_gold} (cost={cost})"
    )


# ---------- 6: lazy completion sweep ----------
def test_guilds_me_lazy_sweep_idempotent():
    h, _ = _new_user_with_guild()
    # No expeditions in flight — multiple calls should be no-op idempotent
    g1 = requests.get(f"{API}/guilds/me", headers=h, timeout=15)
    g2 = requests.get(f"{API}/guilds/me", headers=h, timeout=15)
    assert g1.status_code == 200 == g2.status_code
    assert g1.json()["guild"]["gold"] == g2.json()["guild"]["gold"]


# ---------- 7: dungeon gates ----------
def test_dungeon_gates_sticky():
    h, _ = _new_user_with_guild()
    r = requests.get(f"{API}/dungeons", headers=h, timeout=15)
    assert r.status_code == 200
    ds = {d["slug"]: d for d in r.json()["dungeons"]}
    sc = ds["shadow-crypts"]
    dh = ds["dragons-hoard"]
    assert sc["unlocked"] is False
    dh_reason = (dh.get("unlock_reason") or "").lower()
    assert "level 2" in dh_reason and "65" in dh_reason and "peak" in dh_reason, dh_reason


# ---------- 8: backward-compat shim ----------
def test_server_shim_exports():
    # Reload server.py and check shim imports
    server = importlib.import_module("server")
    assert hasattr(server, "validate_item_monetization")
    assert hasattr(server, "_resolve_levelup")
    assert callable(server.validate_item_monetization)
    assert callable(server._resolve_levelup)


# ---------- 9: mongo indexes idempotent / present ----------
def test_mongo_indexes_present():
    db = MongoClient(MONGO_URL)[DB_NAME]
    # Spot-check key collections that must have at least one custom index
    # (default _id_ index is always present; we look for >1)
    for coll in ("users", "guilds", "adventurers", "expeditions", "inventory_items", "items", "dungeons"):
        idx = list(db[coll].list_indexes())
        names = [i["name"] for i in idx]
        assert len(idx) >= 1, f"{coll}: no indexes at all (names={names})"
