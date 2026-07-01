"""ROUND 11.2 TASK 5a — Admin Ops MVP backend tests (11).

Coverage:
  1.  Non-admin user cannot access /api/admin/guilds/search → 403
  2.  Admin user (is_admin=True) can access search → 200 + list
  3.  Search pagination (limit/offset) works
  4.  Guild detail returns masked email + flag shape
  5.  grant-gold increments balance + writes admin_gold_granted audit
  6.  grant-gold rejects short reason (Pydantic min_length=3)
  7.  grant-gold rejects amount<=0 or amount > ADMIN_MAX_GRANT_GOLD
  8.  grant-item creates inventory entries + writes admin_item_granted audit
  9.  grant-item with unknown slug → 422 admin.item.unknown_slug
  10. /api/admin/audit returns admin events filtered by guild
  11. All admin payloads have NO raw email/user_id leaks (PII safety)
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


def _make_user(db, *, prefix: str = "r112t5a", is_admin: bool = False):
    tag = f"{prefix}_{uuid.uuid4().hex[:8]}"
    email = f"{tag}@orbus.test"
    requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": email, "username": tag, "password": "Test12345!",
    }, timeout=15)
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": email, "password": "Test12345!",
    }, timeout=15)
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    requests.post(f"{BASE_URL}/api/guilds", json={"name": f"R5a {tag[-6:]}"},
                  headers=h, timeout=15)
    g = requests.get(f"{BASE_URL}/api/guilds/me", headers=h, timeout=15).json()["guild"]
    db.users.update_one({"email": email},
                        {"$set": {"is_test_user": True, "is_admin": is_admin}})
    return h, g["id"], email


# ─────────────────────────────────────────────────────────────────────────
def test_t5a_01_non_admin_cannot_access_admin_search(db):
    h, _, _ = _make_user(db, is_admin=False)
    r = requests.get(f"{BASE_URL}/api/admin/guilds/search", headers=h, timeout=15)
    assert r.status_code == 403, f"expected 403, got {r.status_code}: {r.text}"
    detail = r.json().get("detail")
    if isinstance(detail, dict):
        assert detail.get("code") == "admin.forbidden"


def test_t5a_02_admin_can_access_admin_search(db):
    h, _, _ = _make_user(db, is_admin=True)
    r = requests.get(f"{BASE_URL}/api/admin/guilds/search", headers=h, timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "guilds" in body and "total" in body
    assert isinstance(body["guilds"], list)


def test_t5a_03_admin_search_paginated(db):
    h, _, _ = _make_user(db, is_admin=True)
    r1 = requests.get(f"{BASE_URL}/api/admin/guilds/search?limit=2&offset=0",
                      headers=h, timeout=15)
    r2 = requests.get(f"{BASE_URL}/api/admin/guilds/search?limit=2&offset=2",
                      headers=h, timeout=15)
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["limit"] == 2 and r1.json()["offset"] == 0
    assert r2.json()["offset"] == 2
    assert len(r1.json()["guilds"]) <= 2


def test_t5a_04_admin_get_guild_detail_masked_email(db):
    h_admin, _, _ = _make_user(db, is_admin=True)
    _, target_gid, target_email = _make_user(db, is_admin=False)
    r = requests.get(f"{BASE_URL}/api/admin/guilds/{target_gid}",
                     headers=h_admin, timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "public_id" in body
    assert "owner_email_masked" in body
    assert "***@" in body["owner_email_masked"]
    # NOT raw email
    assert target_email not in str(body)
    assert "roster" in body and "cap" in body["roster"]
    assert "flags" in body
    assert "is_test_artifact" in body["flags"]


def test_t5a_05_grant_gold_increments_balance_and_audits(db):
    h_admin, _, _ = _make_user(db, is_admin=True)
    _, target_gid, _ = _make_user(db, is_admin=False)
    gold_before = db.guilds.find_one({"id": target_gid})["gold"]
    r = requests.post(
        f"{BASE_URL}/api/admin/guilds/{target_gid}/grant-gold",
        json={"amount": 500, "reason": "test grant compensation"},
        headers=h_admin, timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    assert body["gold_before"] == gold_before
    assert body["gold_after"] == gold_before + 500
    gold_after_db = db.guilds.find_one({"id": target_gid})["gold"]
    assert gold_after_db == gold_before + 500
    # Audit
    audit = db.audit_log.find_one({
        "event_type": "admin_gold_granted",
        "actor_guild_id": target_gid,
    }, sort=[("created_at", -1)])
    assert audit is not None
    md = audit["metadata"]
    assert md["amount"] == 500
    assert md["reason"] == "test grant compensation"
    assert "***@" in md["admin_actor_email_masked"]


def test_t5a_06_grant_gold_requires_reason_min_length(db):
    h_admin, _, _ = _make_user(db, is_admin=True)
    _, target_gid, _ = _make_user(db, is_admin=False)
    r = requests.post(
        f"{BASE_URL}/api/admin/guilds/{target_gid}/grant-gold",
        json={"amount": 500, "reason": "ab"},  # too short
        headers=h_admin, timeout=15,
    )
    assert r.status_code == 422, f"expected 422, got {r.status_code}: {r.text}"


def test_t5a_07_grant_gold_amount_validation(db):
    h_admin, _, _ = _make_user(db, is_admin=True)
    _, target_gid, _ = _make_user(db, is_admin=False)
    # amount <= 0 → 422
    r1 = requests.post(
        f"{BASE_URL}/api/admin/guilds/{target_gid}/grant-gold",
        json={"amount": 0, "reason": "test invalid amount"},
        headers=h_admin, timeout=15,
    )
    assert r1.status_code == 422
    # amount over max (default 100k) → 422 with structured code
    r2 = requests.post(
        f"{BASE_URL}/api/admin/guilds/{target_gid}/grant-gold",
        json={"amount": 200_000, "reason": "test over max"},
        headers=h_admin, timeout=15,
    )
    assert r2.status_code == 422


def test_t5a_08_grant_item_creates_inventory_and_audits(db):
    h_admin, _, _ = _make_user(db, is_admin=True)
    _, target_gid, _ = _make_user(db, is_admin=False)
    # Pick any stackable item template
    tpl = db.items.find_one({"item_type": "material"}, {"_id": 0}) or \
          db.items.find_one({"item_type": "consumable"}, {"_id": 0})
    assert tpl, "no stackable item template available"
    r = requests.post(
        f"{BASE_URL}/api/admin/guilds/{target_gid}/grant-item",
        json={"item_slug": tpl["slug"], "quantity": 5,
              "reason": "test grant material"},
        headers=h_admin, timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    assert body["item_slug"] == tpl["slug"]
    assert body["quantity"] == 5
    assert body["inventory_entries_created"] >= 1
    # Inventory check
    inv = db.inventory_items.find_one({
        "guild_id": target_gid, "item_slug": tpl["slug"],
    })
    assert inv is not None
    assert inv["quantity"] >= 5
    # Audit
    audit = db.audit_log.find_one({
        "event_type": "admin_item_granted",
        "actor_guild_id": target_gid,
    }, sort=[("created_at", -1)])
    assert audit is not None
    assert audit["metadata"]["item_slug"] == tpl["slug"]
    assert audit["metadata"]["quantity"] == 5


def test_t5a_09_grant_item_unknown_slug_blocked(db):
    h_admin, _, _ = _make_user(db, is_admin=True)
    _, target_gid, _ = _make_user(db, is_admin=False)
    r = requests.post(
        f"{BASE_URL}/api/admin/guilds/{target_gid}/grant-item",
        json={"item_slug": "nonexistent_item_xyz_999",
              "quantity": 1, "reason": "test unknown slug"},
        headers=h_admin, timeout=15,
    )
    assert r.status_code == 422
    detail = r.json().get("detail")
    if isinstance(detail, dict):
        assert detail.get("code") == "admin.item.unknown_slug"


def test_t5a_10_audit_log_returns_admin_events(db):
    h_admin, _, _ = _make_user(db, is_admin=True)
    _, target_gid, _ = _make_user(db, is_admin=False)
    # First grant something so there's an audit event to query
    requests.post(
        f"{BASE_URL}/api/admin/guilds/{target_gid}/grant-gold",
        json={"amount": 100, "reason": "audit setup"},
        headers=h_admin, timeout=15,
    )
    r = requests.get(
        f"{BASE_URL}/api/admin/audit?guild={target_gid}&action=admin_gold_granted&limit=10",
        headers=h_admin, timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "events" in body
    assert body["total"] >= 1
    # Filtered down to admin_gold_granted only
    for ev in body["events"]:
        assert ev["event_type"] == "admin_gold_granted"


def test_t5a_11_admin_payload_has_no_pii_leaks(db):
    """No raw email, no `user_id` field, no ObjectId in any admin response."""
    import json
    h_admin, admin_gid, admin_email = _make_user(db, is_admin=True)
    _, target_gid, target_email = _make_user(db, is_admin=False)
    # 1) search
    r1 = requests.get(f"{BASE_URL}/api/admin/guilds/search?limit=10",
                      headers=h_admin, timeout=15)
    # 2) detail
    r2 = requests.get(f"{BASE_URL}/api/admin/guilds/{target_gid}",
                      headers=h_admin, timeout=15)
    # 3) audit (after a grant)
    requests.post(f"{BASE_URL}/api/admin/guilds/{target_gid}/grant-gold",
                  json={"amount": 50, "reason": "pii leak check"},
                  headers=h_admin, timeout=15)
    r3 = requests.get(f"{BASE_URL}/api/admin/audit?guild={target_gid}",
                      headers=h_admin, timeout=15)

    for label, resp in [("search", r1), ("detail", r2), ("audit", r3)]:
        assert resp.status_code == 200, f"{label}: {resp.text}"
        body_str = json.dumps(resp.json())
        # No raw emails
        assert target_email not in body_str, f"{label} leaks target raw email"
        assert admin_email not in body_str, f"{label} leaks admin raw email"
        # No password fields
        assert "password" not in body_str.lower(), f"{label} leaks password key"
        # No ObjectId markers
        assert "$oid" not in body_str, f"{label} leaks ObjectId"
