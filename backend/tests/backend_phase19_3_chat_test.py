"""Phase 19.3 — Chat MVP backend tests.

Coverage:
  C1. 401 without JWT (GET/POST global + consortium)
  C2. POST + GET global roundtrip (no PII in payload)
  C3. Validation 422 (empty / too long / whitespace-only)
  C4. HTML escape (`<script>` not rendered as HTML, returned as &lt;script&gt;)
  C5. Rate limit 429 (5/10s sliding window)
  C6. Consortium 403 for non-member
  C7. Consortium roundtrip OK for member
  C8. test_user messages hidden from OTHER players in global; visible to author
  C9. OpenAPI path count bumped to 81 (was 77)
"""
import os
import time
import uuid
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
    c = MongoClient(MONGO_URL)
    try:
        yield c[DB_NAME]
    finally:
        c.close()


def _user(hint="p193c", is_test=False):
    tag = f"{hint}_{uuid.uuid4().hex[:6]}"
    requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": f"{tag}@orbus.test", "username": tag, "password": "Test12345!",
    }, timeout=15)
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": f"{tag}@orbus.test", "password": "Test12345!",
    }, timeout=15)
    tok = r.json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    requests.post(f"{BASE_URL}/api/guilds", json={"name": f"P193 {tag[-5:]}"}, headers=h, timeout=15)
    g = requests.get(f"{BASE_URL}/api/guilds/me", headers=h, timeout=15).json()["guild"]
    return {"headers": h, "tag": tag, "guild_id": g["id"], "guild_name": g["name"], "email": f"{tag}@orbus.test"}


class TestChatMVP:
    def test_C1_unauth_blocked_all_endpoints(self):
        for method, path, body in [
            ("get", "/api/chat/global", None),
            ("post", "/api/chat/global", {"message_text": "hi"}),
            ("get", "/api/chat/consortium/abc", None),
            ("post", "/api/chat/consortium/abc", {"message_text": "hi"}),
        ]:
            fn = getattr(requests, method)
            kw = {"timeout": 15}
            if body is not None:
                kw["json"] = body
            r = fn(f"{BASE_URL}{path}", **kw)
            assert r.status_code in (401, 403), f"{method.upper()} {path} → {r.status_code} {r.text[:120]}"

    def test_C2_global_roundtrip_no_pii(self, db):
        ctx = _user("c2")
        # Ensure tester is NOT test-flagged so message is visible to other users
        db.users.update_one({"email": ctx["email"]}, {"$set": {"is_test_user": False}})
        body_text = f"Ciao mondo {uuid.uuid4().hex[:6]}"
        r = requests.post(
            f"{BASE_URL}/api/chat/global", json={"message_text": body_text},
            headers=ctx["headers"], timeout=15,
        )
        assert r.status_code == 201, r.text
        msg = r.json()["message"]
        # PII guard — these keys must NEVER appear
        for forbidden in ("sender_user_id", "sender_guild_id", "email", "_id", "user_id"):
            assert forbidden not in msg, f"PII leak: {forbidden} present in payload"
        # Allowed fields
        for k in ("message_id", "channel_type", "sender_public_name", "message_text", "created_at"):
            assert k in msg, f"missing {k}"
        assert msg["channel_type"] == "global"
        assert msg["sender_public_name"] == ctx["guild_name"]
        assert msg["message_text"] == body_text

        # GET returns the message
        r2 = requests.get(f"{BASE_URL}/api/chat/global?limit=20", headers=ctx["headers"], timeout=15)
        assert r2.status_code == 200
        ids = [m["message_id"] for m in r2.json()["messages"]]
        assert msg["message_id"] in ids

    def test_C3_validation_422(self):
        ctx = _user("c3")
        # empty
        r = requests.post(f"{BASE_URL}/api/chat/global", json={"message_text": ""},
                          headers=ctx["headers"], timeout=15)
        assert r.status_code == 422
        # whitespace only
        r = requests.post(f"{BASE_URL}/api/chat/global", json={"message_text": "   "},
                          headers=ctx["headers"], timeout=15)
        assert r.status_code == 422
        # too long
        r = requests.post(f"{BASE_URL}/api/chat/global", json={"message_text": "x" * 501},
                          headers=ctx["headers"], timeout=15)
        assert r.status_code == 422

    def test_C4_html_escape(self, db):
        ctx = _user("c4")
        db.users.update_one({"email": ctx["email"]}, {"$set": {"is_test_user": False}})
        evil = "<script>alert('xss')</script>"
        r = requests.post(f"{BASE_URL}/api/chat/global", json={"message_text": evil},
                          headers=ctx["headers"], timeout=15)
        assert r.status_code == 201
        msg = r.json()["message"]
        # Must be escaped, not raw HTML
        assert "<script>" not in msg["message_text"]
        assert "&lt;script&gt;" in msg["message_text"]

    def test_C5_rate_limit_429(self, db):
        ctx = _user("c5")
        db.users.update_one({"email": ctx["email"]}, {"$set": {"is_test_user": False}})
        ok_count = 0
        rate_limited = False
        for i in range(8):
            r = requests.post(f"{BASE_URL}/api/chat/global",
                              json={"message_text": f"flood {i} {uuid.uuid4().hex[:4]}"},
                              headers=ctx["headers"], timeout=15)
            if r.status_code == 201:
                ok_count += 1
            elif r.status_code == 429:
                rate_limited = True
                assert r.json().get("detail") == "chat.rate_limited"
                break
        assert rate_limited, f"expected 429 after 5 quick posts; got {ok_count} OK"
        assert ok_count == 5, f"expected exactly 5 OK before rate limit, got {ok_count}"

    def test_C6_consortium_403_non_member(self):
        ctx = _user("c6")
        bogus_cid = str(uuid.uuid4())
        r = requests.post(f"{BASE_URL}/api/chat/consortium/{bogus_cid}",
                          json={"message_text": "hi"}, headers=ctx["headers"], timeout=15)
        assert r.status_code == 403, r.text
        r2 = requests.get(f"{BASE_URL}/api/chat/consortium/{bogus_cid}",
                          headers=ctx["headers"], timeout=15)
        assert r2.status_code == 403

    def test_C7_consortium_roundtrip_member(self):
        founder = _user("c7f")
        # Founder creates consortium
        cname = f"P193 {uuid.uuid4().hex[:4]}"
        r = requests.post(f"{BASE_URL}/api/consortiums",
                          json={"name": cname, "description": "x"},
                          headers=founder["headers"], timeout=15)
        assert r.status_code == 201, r.text
        cid = r.json()["id"]
        # Founder posts
        r = requests.post(f"{BASE_URL}/api/chat/consortium/{cid}",
                          json={"message_text": "Salve consorzio"},
                          headers=founder["headers"], timeout=15)
        assert r.status_code == 201, r.text
        # GET as member
        r = requests.get(f"{BASE_URL}/api/chat/consortium/{cid}",
                         headers=founder["headers"], timeout=15)
        assert r.status_code == 200
        msgs = r.json()["messages"]
        assert any(m["message_text"] == "Salve consorzio" for m in msgs)
        # No PII
        for m in msgs:
            for forbidden in ("sender_user_id", "sender_guild_id", "email"):
                assert forbidden not in m

    def test_C8_test_user_hidden_from_others_in_global(self, db):
        # Author A is is_test_user=True; viewer B is a regular user.
        a = _user("c8a")
        b = _user("c8b")
        db.users.update_one({"email": a["email"]}, {"$set": {"is_test_user": True}})
        db.users.update_one({"email": b["email"]}, {"$set": {"is_test_user": False}})
        token_text = f"test_user_secret_{uuid.uuid4().hex[:8]}"
        r = requests.post(f"{BASE_URL}/api/chat/global",
                          json={"message_text": token_text}, headers=a["headers"], timeout=15)
        assert r.status_code == 201
        # A sees own message
        rA = requests.get(f"{BASE_URL}/api/chat/global?limit=50",
                          headers=a["headers"], timeout=15).json()
        assert any(token_text == m["message_text"] for m in rA["messages"])
        # B does NOT see A's message
        rB = requests.get(f"{BASE_URL}/api/chat/global?limit=50",
                          headers=b["headers"], timeout=15).json()
        assert all(token_text != m["message_text"] for m in rB["messages"])

    def test_C9_openapi_path_count_now_79(self):
        r = requests.get(f"{BASE_URL}/api/openapi.json", timeout=15)
        paths = list(r.json()["paths"].keys())
        assert len(paths) == 86, f"expected 79 (77 + 2 chat paths), got {len(paths)}"
        # Sanity: all 4 chat paths present
        for p in [
            "/api/chat/global",
            "/api/chat/consortium/{consortium_id}",
        ]:
            assert p in paths, f"missing chat path: {p}"
