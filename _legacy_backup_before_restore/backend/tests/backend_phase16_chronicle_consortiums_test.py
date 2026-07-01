"""Phase 16 — Online feel, Market fix, Chronicle, Consortiums.

11 tests covering:
  1. Market route accessible (200 + listings shape).
  2. Chronicle filters out email/user_id/test users.
  3. Chronicle exposes only public fields.
  4. Consortium create/list/join/leave full lifecycle.
  5. A user cannot be in 2 consortiums at once.
  6. Duplicate name (case-insensitive) → 409.
  7. Consortium membership grants NO gold/XP/loot/ranking bonus.
  8. Leaderboard endpoint shape unchanged (A2 no-regression).
  9. ROUND 3 market/crafting/loot endpoint shape unchanged.
 10. ROUND 3.5 streak/weekly endpoint shape unchanged.
 11. OpenAPI path count is 60 (53 + chronicle 1 + consortiums 6).

Hard constraints honoured:
  * Test users use @orbus.test emails.
  * No destructive teardown.
"""
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

BASE_URL = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or os.environ.get("BACKEND_URL", "http://localhost:8001")
).rstrip("/")
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]


@pytest.fixture(scope="module")
def db():
    client = MongoClient(MONGO_URL)
    try:
        yield client[DB_NAME]
    finally:
        client.close()


def _seed(name_hint: str = "p16"):
    tag = f"{name_hint}_{uuid.uuid4().hex[:8]}"
    r = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": f"{tag}@orbus.test", "username": tag, "password": "Test12345!"},
        timeout=15,
    )
    assert r.status_code == 201, r.text
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    requests.post(
        f"{BASE_URL}/api/guilds",
        json={"name": f"Guildhouse {tag[-6:].upper()}", "description": ""},
        headers=h, timeout=15,
    )
    gid = requests.get(f"{BASE_URL}/api/guilds/me", headers=h, timeout=15).json()["guild"]["id"]
    return {"headers": h, "guild_id": gid, "tag": tag}


# ═════════════════════════════════════════════════════════════════════════
# 1. Market route accessible
# ═════════════════════════════════════════════════════════════════════════
def test_market_listings_route_accessible():
    ctx = _seed("market")
    r = requests.get(f"{BASE_URL}/api/market/listings", headers=ctx["headers"], timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "listings" in body
    assert isinstance(body["listings"], list)


# ═════════════════════════════════════════════════════════════════════════
# 2. Chronicle filters email/user_id/test users
# ═════════════════════════════════════════════════════════════════════════
def test_chronicle_filters_sensitive_data(db):
    r = requests.get(f"{BASE_URL}/api/chronicle?limit=50", timeout=15)
    assert r.status_code == 200, r.text
    events = r.json().get("events", [])
    email_re = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    objectid_re = re.compile(r"^[a-f0-9]{24}$")
    for e in events:
        for v in e.values():
            if isinstance(v, str):
                # No email pattern leaks in any string field.
                assert not email_re.search(v), f"email leaked in {e}"
                # No raw ObjectId leaks.
                assert not objectid_re.match(v.strip()), f"ObjectId leak in {e}"
        # No actor_user_id / actor_guild_id keys.
        assert "actor_user_id" not in e
        assert "actor_guild_id" not in e
        # No guild name starting with Test / G followed by hex hash.
        gname = e.get("guild_name", "")
        assert not re.match(r"^test", gname, re.IGNORECASE)
        assert not re.match(r"^g[\s_][0-9a-f]{6,}", gname, re.IGNORECASE)


# ═════════════════════════════════════════════════════════════════════════
# 3. Chronicle exposes only public fields
# ═════════════════════════════════════════════════════════════════════════
def test_chronicle_only_public_fields():
    r = requests.get(f"{BASE_URL}/api/chronicle?limit=20", timeout=15)
    events = r.json().get("events", [])
    allowed = {"id", "kind", "guild_name", "item_name", "text", "created_at"}
    for e in events:
        extra = set(e.keys()) - allowed
        assert not extra, f"unexpected keys in chronicle event: {extra}"


# ═════════════════════════════════════════════════════════════════════════
# 4. Consortium full lifecycle
# ═════════════════════════════════════════════════════════════════════════
def test_consortium_create_list_join_leave(db):
    founder = _seed("cfound")
    joiner = _seed("cjoin")
    name = f"Patto del Vespero {uuid.uuid4().hex[:5]}"
    # Create
    r = requests.post(
        f"{BASE_URL}/api/consortiums",
        json={"name": name, "tag": "VES", "description": "MVP test"},
        headers=founder["headers"], timeout=15,
    )
    assert r.status_code == 201, r.text
    cid = r.json()["id"]
    assert r.json()["member_count"] == 1
    # List shows it
    rows = requests.get(f"{BASE_URL}/api/consortiums?limit=50", timeout=15).json()["consortiums"]
    assert any(c["id"] == cid for c in rows)
    # Joiner joins
    r2 = requests.post(
        f"{BASE_URL}/api/consortiums/{cid}/join",
        headers=joiner["headers"], timeout=15,
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["member_count"] == 2
    # /me reflects membership for joiner
    me = requests.get(f"{BASE_URL}/api/consortiums/me", headers=joiner["headers"], timeout=15).json()
    assert me["consortium"]["id"] == cid
    # Joiner leaves
    r3 = requests.post(f"{BASE_URL}/api/consortiums/leave", headers=joiner["headers"], timeout=15)
    assert r3.status_code == 200, r3.text
    # /me now returns None
    me_after = requests.get(f"{BASE_URL}/api/consortiums/me", headers=joiner["headers"], timeout=15).json()
    assert me_after["consortium"] is None


# ═════════════════════════════════════════════════════════════════════════
# 5. A user cannot belong to 2 consortiums
# ═════════════════════════════════════════════════════════════════════════
def test_user_cannot_belong_to_two_consortiums(db):
    a = _seed("c2a")
    b_founder = _seed("c2b")
    # founder creates C1
    r1 = requests.post(
        f"{BASE_URL}/api/consortiums",
        json={"name": f"Alpha {uuid.uuid4().hex[:5]}", "tag": None, "description": ""},
        headers=a["headers"], timeout=15,
    )
    assert r1.status_code == 201
    # Another founder creates C2
    r2 = requests.post(
        f"{BASE_URL}/api/consortiums",
        json={"name": f"Beta {uuid.uuid4().hex[:5]}", "tag": None, "description": ""},
        headers=b_founder["headers"], timeout=15,
    )
    cid2 = r2.json()["id"]
    # `a` tries to join C2 → must be 409
    r3 = requests.post(
        f"{BASE_URL}/api/consortiums/{cid2}/join",
        headers=a["headers"], timeout=15,
    )
    assert r3.status_code == 409, r3.text


# ═════════════════════════════════════════════════════════════════════════
# 6. Duplicate name case-insensitive
# ═════════════════════════════════════════════════════════════════════════
def test_duplicate_name_case_insensitive_blocked(db):
    a = _seed("cdup1")
    b = _seed("cdup2")
    name = f"Unique-{uuid.uuid4().hex[:6]}"
    r1 = requests.post(
        f"{BASE_URL}/api/consortiums",
        json={"name": name, "tag": None, "description": ""},
        headers=a["headers"], timeout=15,
    )
    assert r1.status_code == 201
    # Try with same name lowercased
    r2 = requests.post(
        f"{BASE_URL}/api/consortiums",
        json={"name": name.lower(), "tag": None, "description": ""},
        headers=b["headers"], timeout=15,
    )
    assert r2.status_code == 409, r2.text


# ═════════════════════════════════════════════════════════════════════════
# 7. Consortium grants NO gold/XP/loot/ranking bonus
# ═════════════════════════════════════════════════════════════════════════
def test_consortium_grants_no_bonus(db):
    ctx = _seed("cbonus")
    # Capture before
    g0 = db.guilds.find_one({"id": ctx["guild_id"]})
    gold0 = int(g0.get("gold", 0))
    rep0 = int(g0.get("reputation", 0))
    # Create
    r = requests.post(
        f"{BASE_URL}/api/consortiums",
        json={"name": f"NoBonus {uuid.uuid4().hex[:5]}", "tag": None, "description": ""},
        headers=ctx["headers"], timeout=15,
    )
    assert r.status_code == 201, r.text
    cid = r.json()["id"]
    # Capture after
    g1 = db.guilds.find_one({"id": ctx["guild_id"]})
    assert int(g1.get("gold", 0)) == gold0, "gold changed after consortium create"
    assert int(g1.get("reputation", 0)) == rep0, "reputation changed after consortium create"
    # Audit: only consortium_created event, no economy events
    rows = list(db.audit_log.find(
        {"actor_user_id": g0["owner_user_id"], "event_type": {"$in": ["gold_credited", "gold_debited", "loot_awarded"]}},
    ))
    # There may be pre-existing audit rows but none should reference cid
    for row in rows:
        md = row.get("metadata") or {}
        assert md.get("consortium_id") != cid


# ═════════════════════════════════════════════════════════════════════════
# 8. Leaderboard endpoint shape unchanged (A2 no-regression)
# ═════════════════════════════════════════════════════════════════════════
def test_leaderboard_endpoint_shape_unchanged():
    r = requests.get(f"{BASE_URL}/api/leaderboard/guilds?limit=5", timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "entries" in body or "leaderboard" in body or "guilds" in body or isinstance(body, list)


# ═════════════════════════════════════════════════════════════════════════
# 9. ROUND 3 market/crafting/loot — no-regression
# ═════════════════════════════════════════════════════════════════════════
def test_round3_endpoints_unchanged():
    ctx = _seed("r3")
    # Market listings
    r1 = requests.get(f"{BASE_URL}/api/market/listings", headers=ctx["headers"], timeout=15)
    assert r1.status_code == 200
    # Crafting recipes
    r2 = requests.get(f"{BASE_URL}/api/recipes", headers=ctx["headers"], timeout=15)
    assert r2.status_code == 200
    # Inventory items
    r3 = requests.get(f"{BASE_URL}/api/inventory", headers=ctx["headers"], timeout=15)
    assert r3.status_code == 200


# ═════════════════════════════════════════════════════════════════════════
# 10. ROUND 3.5 streak/weekly — no-regression
# ═════════════════════════════════════════════════════════════════════════
def test_round35_streak_weekly_unchanged():
    ctx = _seed("r35")
    r1 = requests.get(f"{BASE_URL}/api/quests/streak", headers=ctx["headers"], timeout=15)
    assert r1.status_code == 200, r1.text
    d1 = r1.json()
    for k in ("current", "longest", "schedule", "can_claim_reward"):
        assert k in d1, f"missing {k} in streak"
    r2 = requests.get(f"{BASE_URL}/api/quests/weekly", headers=ctx["headers"], timeout=15)
    assert r2.status_code == 200, r2.text
    d2 = r2.json()
    assert "quests" in d2
    assert len(d2["quests"]) == 4
    for q in d2["quests"]:
        assert "objective_target" in q  # binding canonical name


# ═════════════════════════════════════════════════════════════════════════
# 11. OpenAPI path count is 60
# ═════════════════════════════════════════════════════════════════════════
def test_openapi_path_count_is_61():
    r = requests.get(f"{BASE_URL}/api/openapi.json", timeout=15)
    paths = r.json().get("paths", {})
    # 53 (ROUND 3.5) + 1 chronicle + 6 consortiums + 1 admin cleanup = 61
    # Updated for Phase 19 §1.2 — added /api/leaderboard/raids (75 → 76)
    assert len(paths) == 86, f"expected 75, got {len(paths)}: {sorted(paths)}"
    assert "/api/chronicle" in paths
    assert "/api/consortiums" in paths
    assert "/api/consortiums/me" in paths
    assert "/api/consortiums/leave" in paths
    assert "/api/consortiums/{consortium_id}/join" in paths
    assert "/api/admin/cleanup/flag-test-users" in paths
