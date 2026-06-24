"""Phase 9.3.1 — Security hardening tests.

Covers two fixes:
* P1-1: equipment item duplication race via atomic reserved_qty
* P1-3: HTML/header injection in welcome email username + Pydantic regex
"""
import asyncio
import os
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
    client = MongoClient(MONGO_URL)
    try:
        yield client[DB_NAME]
    finally:
        client.close()


def _register(tag_prefix="p931", username=None):
    tag = f"{tag_prefix}_{uuid.uuid4().hex[:8]}"
    email = f"{tag}@orbus.test"
    uname = username or tag
    r = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": email, "username": uname, "password": "Test12345!"},
        timeout=15,
    )
    return r, tag, email


def _setup_guild_with_advs(db, count=2):
    r, tag, email = _register()
    assert r.status_code == 201, r.text
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    requests.post(f"{BASE_URL}/api/guilds", json={"name": f"G_{tag}", "description": ""}, headers=h, timeout=15)
    me = requests.get(f"{BASE_URL}/api/guilds/me", headers=h, timeout=15).json()["guild"]
    gid = me["id"]
    # Bulk-seed N adventurers directly in Mongo (bypass recruitment refresh limit)
    adv_ids = []
    for i in range(count):
        aid = str(uuid.uuid4())
        db.adventurers.insert_one({
            "id": aid, "guild_id": gid,
            "name": f"AdvP931_{i}", "adventurer_class_id": "x",
            "class_name": "Warrior", "class_role": "Tank",
            "rarity": "Common", "level": 5, "experience": 0,
            "strength": 10, "agility": 10, "intellect": 10, "endurance": 10, "faith": 10,
            "stamina": 100, "morale": 100, "traits": [], "is_available": True,
            "created_at": "2026-01-01T00:00:00+00:00", "updated_at": "2026-01-01T00:00:00+00:00",
        })
        adv_ids.append(aid)
    return {"headers": h, "guild_id": gid, "adv_ids": adv_ids, "email": email}


# ────────────────────────────────────────────────────────────────────────
# P1-1 — Equipment race / reservation tests
# ────────────────────────────────────────────────────────────────────────
class TestEquipmentReservationP11:
    def _inject_inventory(self, db, gid, slot="weapon", item_type="weapon", quantity=1):
        item_id = str(uuid.uuid4())
        # Define item in items collection
        db.items.insert_one({
            "id": item_id, "slug": f"itm-{item_id[:8]}",
            "name": "TestWeapon", "description": "p931 test",
            "item_type": item_type, "slot": slot, "rarity": "Common",
            "level_required": 1, "power_score": 10,
            "strength_bonus": 5, "agility_bonus": 0,
            "intellect_bonus": 0, "endurance_bonus": 0, "faith_bonus": 0,
            "affects_combat": True, "is_cosmetic": False,
            "affects_economy": False, "affects_ranking": False,
            "can_be_sold_for_gold": True, "can_be_sold_for_real_money": False,
            "is_tradeable": True, "is_active": True,
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
        })
        # Add to guild inventory
        db.inventory_items.insert_one({
            "id": str(uuid.uuid4()), "guild_id": gid, "item_id": item_id,
            "quantity": quantity, "reserved_qty": 0,
            "acquired_at": "2026-01-01T00:00:00+00:00",
        })
        return item_id

    def test_single_equip_increments_reservation(self, db):
        ctx = _setup_guild_with_advs(db, count=1)
        item_id = self._inject_inventory(db, ctx["guild_id"], quantity=1)
        r = requests.post(
            f"{BASE_URL}/api/adventurers/{ctx['adv_ids'][0]}/equip",
            json={"item_id": item_id, "slot": "weapon"},
            headers=ctx["headers"], timeout=15,
        )
        assert r.status_code in (200, 201), r.text
        inv = db.inventory_items.find_one({"guild_id": ctx["guild_id"], "item_id": item_id})
        assert inv["reserved_qty"] == 1

    def test_concurrent_equip_qty1_only_one_succeeds(self, db):
        """The race that motivated P1-1: two concurrent equips of a qty-1 item
        on two different adventurers. Exactly one must succeed."""
        ctx = _setup_guild_with_advs(db, count=2)
        item_id = self._inject_inventory(db, ctx["guild_id"], quantity=1)

        import concurrent.futures as cf
        def equip(adv_id):
            return requests.post(
                f"{BASE_URL}/api/adventurers/{adv_id}/equip",
                json={"item_id": item_id, "slot": "weapon"},
                headers=ctx["headers"], timeout=15,
            )
        with cf.ThreadPoolExecutor(max_workers=2) as ex:
            futs = [ex.submit(equip, ctx["adv_ids"][0]), ex.submit(equip, ctx["adv_ids"][1])]
            results = [f.result() for f in futs]
        statuses = sorted(r.status_code for r in results)
        # Exactly one 2xx and one 409
        assert statuses[0] in (200, 201), f"first should succeed, got {statuses}"
        assert statuses[1] == 409, f"second should 409, got {statuses} bodies={[r.text for r in results]}"
        inv = db.inventory_items.find_one({"guild_id": ctx["guild_id"], "item_id": item_id})
        assert inv["reserved_qty"] == 1, f"reserved_qty should stay 1, got {inv['reserved_qty']}"

    def test_reservation_caps_at_quantity(self, db):
        ctx = _setup_guild_with_advs(db, count=3)
        item_id = self._inject_inventory(db, ctx["guild_id"], quantity=2)
        for i, adv in enumerate(ctx["adv_ids"]):
            r = requests.post(
                f"{BASE_URL}/api/adventurers/{adv}/equip",
                json={"item_id": item_id, "slot": "weapon"},
                headers=ctx["headers"], timeout=15,
            )
            if i < 2:
                assert r.status_code in (200, 201), r.text
            else:
                assert r.status_code == 409, r.text
        inv = db.inventory_items.find_one({"guild_id": ctx["guild_id"], "item_id": item_id})
        assert inv["reserved_qty"] == 2

    def test_unequip_releases_reservation(self, db):
        ctx = _setup_guild_with_advs(db, count=1)
        item_id = self._inject_inventory(db, ctx["guild_id"], quantity=1)
        # Equip
        r1 = requests.post(
            f"{BASE_URL}/api/adventurers/{ctx['adv_ids'][0]}/equip",
            json={"item_id": item_id, "slot": "weapon"},
            headers=ctx["headers"], timeout=15,
        )
        assert r1.status_code in (200, 201)
        # Unequip
        r2 = requests.post(
            f"{BASE_URL}/api/adventurers/{ctx['adv_ids'][0]}/unequip",
            json={"slot": "weapon"},
            headers=ctx["headers"], timeout=15,
        )
        assert r2.status_code == 200, r2.text
        inv = db.inventory_items.find_one({"guild_id": ctx["guild_id"], "item_id": item_id})
        assert inv["reserved_qty"] == 0, "reservation must be released on unequip"

    def test_cross_guild_equip_blocked(self, db):
        ctx_a = _setup_guild_with_advs(db, count=1)
        ctx_b = _setup_guild_with_advs(db, count=1)
        item_id = self._inject_inventory(db, ctx_a["guild_id"], quantity=1)
        # B tries to equip an item belonging to A
        r = requests.post(
            f"{BASE_URL}/api/adventurers/{ctx_b['adv_ids'][0]}/equip",
            json={"item_id": item_id, "slot": "weapon"},
            headers=ctx_b["headers"], timeout=15,
        )
        assert r.status_code in (403, 404), r.text


# ────────────────────────────────────────────────────────────────────────
# P1-3 — Welcome email injection tests
# ────────────────────────────────────────────────────────────────────────
class TestWelcomeEmailInjectionP13:
    def test_html_escape_in_body(self):
        from app.core.email_templates import render_welcome
        evil = "<script>alert(1)</script>"
        _, html, _ = render_welcome("en", "https://orbus.test", evil)
        assert "<script>alert(1)</script>" not in html
        # The escaped form is empty here because _safe_text strips <>&, so
        # the username collapses to "scriptalert(1)/script" — verify presence
        # AS the stripped variant (not as raw HTML tags).
        assert "<script" not in html
        assert "</script" not in html

    def test_subject_strips_html_meta(self):
        from app.core.email_templates import render_welcome
        evil = "<bad>name</bad>"
        subj, _, _ = render_welcome("en", "https://orbus.test", evil)
        assert "<" not in subj
        assert ">" not in subj

    def test_pydantic_rejects_html_username(self):
        r = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={"email": f"reject_{uuid.uuid4().hex[:6]}@orbus.test",
                  "username": "<bad>", "password": "Test12345!"},
            timeout=15,
        )
        assert r.status_code == 422

    def test_pydantic_rejects_newline_username(self):
        r = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={"email": f"reject2_{uuid.uuid4().hex[:6]}@orbus.test",
                  "username": "good\nName", "password": "Test12345!"},
            timeout=15,
        )
        assert r.status_code == 422

    def test_pydantic_accepts_valid_username(self):
        r, *_ = _register("ok", username="Good User_42")
        assert r.status_code == 201, r.text

    def test_pydantic_accepts_hyphen_underscore_space(self):
        for name in ("Good-User", "Good_User", "Good User"):
            r, *_ = _register("ok", username=name)
            assert r.status_code == 201, f"{name} rejected: {r.text}"

    def test_password_reset_template_still_renders(self):
        from app.core.email_templates import render_password_reset
        subj, html, text = render_password_reset("en", "https://x.test/r?t=abc")
        assert "Reset" in subj
        assert "https://x.test/r?t=abc" in html
        assert "https://x.test/r?t=abc" in text


# ────────────────────────────────────────────────────────────────────────
# OpenAPI invariant
# ────────────────────────────────────────────────────────────────────────
class TestPhase931OpenAPI:
    def test_paths_count_unchanged_at_39(self):
        r = requests.get(f"{BASE_URL}/api/openapi.json", timeout=15)
        paths = r.json().get("paths", {})
        assert len(paths) == 39, f"expected 39, got {len(paths)}"
