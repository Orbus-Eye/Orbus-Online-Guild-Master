"""Phase 19.4b — System NPC Shop tests."""
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
    c = MongoClient(MONGO_URL)
    try:
        yield c[DB_NAME]
    finally:
        c.close()


def _user(db, hint="p194b", gold=1000):
    tag = f"{hint}_{uuid.uuid4().hex[:6]}"
    requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": f"{tag}@orbus.test", "username": tag, "password": "Test12345!",
    }, timeout=15)
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": f"{tag}@orbus.test", "password": "Test12345!",
    }, timeout=15)
    tok = r.json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    requests.post(f"{BASE_URL}/api/guilds", json={"name": f"P194b {tag[-5:]}"}, headers=h, timeout=15)
    g = requests.get(f"{BASE_URL}/api/guilds/me", headers=h, timeout=15).json()["guild"]
    # Top up gold so we can run buy tests
    db.guilds.update_one({"id": g["id"]}, {"$set": {"gold": gold}})
    # Flag test user so global chat etc. doesn't pollute
    db.users.update_one({"email": f"{tag}@orbus.test"}, {"$set": {"is_test_user": True}})
    # ROUND 6B.2a — Territory guard: shop/sell needs market_stall Lv2.
    # Force the lazy doc creation + bump structure level so legacy tests pass.
    requests.get(f"{BASE_URL}/api/territory", headers=h, timeout=15)
    db.guild_structures.update_one(
        {"guild_id": g["id"]},
        {"$set": {
            "structures.market_stall.level": 2,
            "structures.market_stall.is_unlocked": True,
        }},
        upsert=True,
    )
    return {"headers": h, "guild_id": g["id"], "tag": tag, "email": f"{tag}@orbus.test"}


class TestShopDailyOffers:
    def test_S1_daily_offers_returns_six(self, db):
        ctx = _user(db, "s1")
        r = requests.get(f"{BASE_URL}/api/shop/daily_offers", headers=ctx["headers"], timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "offers" in body and "next_reset_at" in body and "day_key" in body
        assert len(body["offers"]) == 6, f"expected 6 offers, got {len(body['offers'])}"
        # Each offer has correct shape
        for o in body["offers"]:
            for k in ("offer_id", "item", "buy_price", "sell_price", "stock_remaining", "max_quantity"):
                assert k in o, f"missing {k}"
            assert o["sell_price"] < o["buy_price"], "sell must be < buy"
            assert o["sell_price"] == round(o["buy_price"] * 0.4)

    def test_S2_daily_offers_deterministic_per_day(self, db):
        ctx = _user(db, "s2")
        r1 = requests.get(f"{BASE_URL}/api/shop/daily_offers", headers=ctx["headers"], timeout=15).json()
        r2 = requests.get(f"{BASE_URL}/api/shop/daily_offers", headers=ctx["headers"], timeout=15).json()
        ids1 = sorted(o["offer_id"] for o in r1["offers"])
        ids2 = sorted(o["offer_id"] for o in r2["offers"])
        assert ids1 == ids2, "same-day offers must be deterministic"

    def test_S3_auth_required(self):
        r = requests.get(f"{BASE_URL}/api/shop/daily_offers", timeout=15)
        assert r.status_code in (401, 403)


class TestShopBuy:
    def _pick_offer(self, ctx):
        r = requests.get(f"{BASE_URL}/api/shop/daily_offers", headers=ctx["headers"], timeout=15).json()
        return r["offers"][0]

    def test_S4_buy_success_updates_gold_and_stock(self, db):
        ctx = _user(db, "s4", gold=5000)
        offer = self._pick_offer(ctx)
        guild_before = db.guilds.find_one({"id": ctx["guild_id"]}, {"_id": 0, "gold": 1})
        r = requests.post(
            f"{BASE_URL}/api/shop/buy", headers=ctx["headers"],
            json={"offer_id": offer["offer_id"], "quantity": 2}, timeout=15,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["success"] is True
        assert body["gold_spent"] == offer["buy_price"] * 2
        # Gold debited
        guild_after = db.guilds.find_one({"id": ctx["guild_id"]}, {"_id": 0, "gold": 1})
        assert guild_after["gold"] == guild_before["gold"] - body["gold_spent"]
        # Stock decremented
        assert body["offer"]["stock_remaining"] == offer["stock_remaining"] - 2

    def test_S5_buy_insufficient_gold_402(self, db):
        ctx = _user(db, "s5", gold=1)
        offer = self._pick_offer(ctx)
        r = requests.post(
            f"{BASE_URL}/api/shop/buy", headers=ctx["headers"],
            json={"offer_id": offer["offer_id"], "quantity": 1}, timeout=15,
        )
        assert r.status_code == 402, r.text
        assert r.json()["detail"] == "shop.insufficient_gold"

    def test_S6_buy_unknown_offer_404(self, db):
        ctx = _user(db, "s6")
        r = requests.post(
            f"{BASE_URL}/api/shop/buy", headers=ctx["headers"],
            json={"offer_id": "bogus_offer_id_xxx", "quantity": 1}, timeout=15,
        )
        assert r.status_code == 404
        assert r.json()["detail"] == "shop.offer_not_found"

    def test_S7_buy_invalid_quantity_422(self, db):
        ctx = _user(db, "s7")
        offer = self._pick_offer(ctx)
        # quantity > 99
        r = requests.post(
            f"{BASE_URL}/api/shop/buy", headers=ctx["headers"],
            json={"offer_id": offer["offer_id"], "quantity": 100}, timeout=15,
        )
        assert r.status_code == 422
        # quantity <= 0
        r = requests.post(
            f"{BASE_URL}/api/shop/buy", headers=ctx["headers"],
            json={"offer_id": offer["offer_id"], "quantity": 0}, timeout=15,
        )
        assert r.status_code == 422

    def test_S8_audit_log_written(self, db):
        ctx = _user(db, "s8", gold=5000)
        offer = self._pick_offer(ctx)
        before = db.audit_log.count_documents({
            "event_type": "shop_system_purchase", "actor_user_id": db.users.find_one({"email": ctx["email"]})["id"],
        })
        r = requests.post(
            f"{BASE_URL}/api/shop/buy", headers=ctx["headers"],
            json={"offer_id": offer["offer_id"], "quantity": 1}, timeout=15,
        )
        assert r.status_code == 200
        uid = db.users.find_one({"email": ctx["email"]})["id"]
        after = db.audit_log.count_documents({
            "event_type": "shop_system_purchase", "actor_user_id": uid,
        })
        assert after == before + 1


class TestShopSell:
    def _seed_inventory(self, db, ctx, item_slug="raw_leather", qty=3, is_bound=False):
        """Insert an inventory_items row directly for test isolation."""
        item = db.items.find_one({"slug": item_slug}, {"_id": 0, "id": 1})
        inst = str(uuid.uuid4())
        db.inventory_items.insert_one({
            "id": str(uuid.uuid4()),
            "instance_id": inst,
            "guild_id": ctx["guild_id"],
            "item_id": item["id"],
            "quantity": qty,
            "is_bound": is_bound,
            "disenchanted_at": None,
            "refinement_level": 0,
            "enchants": [],
            "affixes": [],
            "reroll_count": 0,
            "acquired_at": "2026-06-27T00:00:00+00:00",
            "source": "test_seed",
        })
        return inst

    def test_S9_sell_success(self, db):
        ctx = _user(db, "s9")
        inst = self._seed_inventory(db, ctx, qty=3)
        r = requests.post(
            f"{BASE_URL}/api/shop/sell", headers=ctx["headers"],
            json={"instance_id": inst, "quantity": 2}, timeout=15,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["success"] is True
        assert body["quantity"] == 2
        assert body["gold_earned"] > 0

    def test_S10_sell_bound_409(self, db):
        ctx = _user(db, "s10")
        inst = self._seed_inventory(db, ctx, is_bound=True)
        r = requests.post(
            f"{BASE_URL}/api/shop/sell", headers=ctx["headers"],
            json={"instance_id": inst, "quantity": 1}, timeout=15,
        )
        assert r.status_code == 409
        assert r.json()["detail"] == "shop.sell.bound"

    def test_S11_sell_unknown_item_404(self, db):
        ctx = _user(db, "s11")
        r = requests.post(
            f"{BASE_URL}/api/shop/sell", headers=ctx["headers"],
            json={"instance_id": "no-such-instance", "quantity": 1}, timeout=15,
        )
        assert r.status_code == 404
        assert r.json()["detail"] == "shop.item_not_found"
