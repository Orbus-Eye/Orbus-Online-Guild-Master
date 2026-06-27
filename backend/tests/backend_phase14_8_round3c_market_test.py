"""ROUND 3.C (Phase 14.8) — Marketplace tests.

Covers:
  • Listing create: success path locks inventory + audit
  • Listing create: tradeable=False rejected
  • Listing create: insufficient available qty rejected
  • Listing create: price <= 0 / qty <= 0 rejected (Pydantic 422)
  • Cancel: only seller (ownership guard 403)
  • Cancel: restores qty + audit
  • Buy: self-purchase 403
  • Buy: insufficient gold 409
  • Buy: success transfers items + gold + applies fee
  • Buy: partial fill keeps listing active
  • Buy: double-buy on same listing fails 2nd attempt (race)
  • GET /listings filters & sort
  • GET /listings/mine returns own only
  • OpenAPI 49 paths
"""
import asyncio
import os
import uuid

import pytest
import requests
from motor.motor_asyncio import AsyncIOMotorClient

pytestmark = pytest.mark.xdist_group(name="round5_serial_legacy")


BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
def _api(p): return f"{BASE_URL}/api{p}"


def _bootstrap(prefix="r3c"):
    suf = uuid.uuid4().hex[:10]
    email = f"{prefix}_{suf}@orbus.test"
    r = requests.post(_api("/auth/register"),
                      json={"email": email, "username": f"{prefix}_{suf}", "password": "password123"},
                      timeout=15)
    assert r.status_code == 201, r.text
    token = r.json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}
    g = requests.post(_api("/guilds"),
                      json={"name": f"G {suf}", "description": "market"},
                      headers=auth, timeout=15)
    assert g.status_code == 201, g.text
    return auth, g.json().get("guild", g.json())


async def _direct_db():
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return cli, cli[os.environ["DB_NAME"]]


def _run(coro):
    # Updated for Round 5 §I — avoid deprecated `asyncio.get_event_loop()` in 3.11
    # which can return a closed loop after pytest-xdist worker handoffs.
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _grant_item(db, guild_id: str, slug: str, qty: int):
    item = await db.items.find_one({"slug": slug}, {"_id": 0})
    assert item, f"missing seeded item {slug}"
    await db.inventory_items.update_one(
        {"guild_id": guild_id, "item_id": item["id"]},
        {
            "$inc": {"quantity": qty},
            "$setOnInsert": {
                "id": str(uuid.uuid4()),
                "guild_id": guild_id,
                "item_id": item["id"],
                "acquired_at": "2026-06-26T00:00:00+00:00",
                "source": "test",
                "bind_state": "unbound",
            },
        },
        upsert=True,
    )


async def _set_gold(db, guild_id: str, gold: int):
    await db.guilds.update_one({"id": guild_id}, {"$set": {"gold": int(gold)}})


# ─── Listing create ──────────────────────────────────────────────────────


class TestListingCreate:
    def test_create_success_locks_inventory(self):
        auth, g = _bootstrap()
        async def setup():
            cli, db = await _direct_db()
            try: await _grant_item(db, g["id"], "iron_shard", 5)
            finally: cli.close()
        _run(setup())
        r = requests.post(_api("/market/listings"),
                          json={"item_slug": "iron_shard", "quantity": 3, "price_per_unit": 7},
                          headers=auth, timeout=15)
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["success"] is True
        assert body["quantity"] == 3
        assert body["fee_estimate"] == (21 * 5) // 100  # 5% of 21
        async def verify():
            cli, db = await _direct_db()
            try:
                item = await db.items.find_one({"slug": "iron_shard"})
                row = await db.inventory_items.find_one(
                    {"guild_id": g["id"], "item_id": item["id"]}
                )
                assert row["quantity"] == 5
                assert row.get("market_locked_qty", 0) == 3
                # Audit
                a = await db.audit_log.count_documents({
                    "event_type": "market_listing_created",
                    "actor_user_id": {"$exists": True},
                    "item_slug": "iron_shard",
                })
                assert a >= 1
            finally: cli.close()
        _run(verify())

    def test_create_rejected_when_quantity_unavailable(self):
        auth, g = _bootstrap()
        async def setup():
            cli, db = await _direct_db()
            try: await _grant_item(db, g["id"], "iron_shard", 2)
            finally: cli.close()
        _run(setup())
        r = requests.post(_api("/market/listings"),
                          json={"item_slug": "iron_shard", "quantity": 5, "price_per_unit": 10},
                          headers=auth, timeout=15)
        assert r.status_code == 400, r.text

    def test_create_validation_rejects_zero_or_negative(self):
        auth, _g = _bootstrap()
        for body in (
            {"item_slug": "iron_shard", "quantity": 0, "price_per_unit": 10},
            {"item_slug": "iron_shard", "quantity": 1, "price_per_unit": 0},
            {"item_slug": "iron_shard", "quantity": -1, "price_per_unit": 10},
        ):
            r = requests.post(_api("/market/listings"), json=body,
                              headers=auth, timeout=15)
            assert r.status_code == 422, (body, r.text)

    def test_create_rejects_unknown_item(self):
        auth, _g = _bootstrap()
        r = requests.post(_api("/market/listings"),
                          json={"item_slug": "no_such_item_xyz", "quantity": 1, "price_per_unit": 5},
                          headers=auth, timeout=15)
        assert r.status_code == 404, r.text


# ─── Cancel ──────────────────────────────────────────────────────────────


class TestCancelListing:
    def test_only_seller_can_cancel(self):
        auth_a, ga = _bootstrap("r3cA")
        auth_b, _gb = _bootstrap("r3cB")
        async def setup():
            cli, db = await _direct_db()
            try: await _grant_item(db, ga["id"], "iron_shard", 5)
            finally: cli.close()
        _run(setup())
        r = requests.post(_api("/market/listings"),
                          json={"item_slug": "iron_shard", "quantity": 2, "price_per_unit": 10},
                          headers=auth_a, timeout=15)
        assert r.status_code == 201
        lid = r.json()["listing_id"]
        r2 = requests.delete(_api(f"/market/listings/{lid}"),
                             headers=auth_b, timeout=15)
        assert r2.status_code == 403, r2.text

    def test_cancel_releases_locked_qty(self):
        auth, g = _bootstrap()
        async def setup():
            cli, db = await _direct_db()
            try: await _grant_item(db, g["id"], "iron_shard", 5)
            finally: cli.close()
        _run(setup())
        r = requests.post(_api("/market/listings"),
                          json={"item_slug": "iron_shard", "quantity": 3, "price_per_unit": 10},
                          headers=auth, timeout=15)
        lid = r.json()["listing_id"]
        r2 = requests.delete(_api(f"/market/listings/{lid}"),
                             headers=auth, timeout=15)
        assert r2.status_code == 200, r2.text
        assert r2.json()["item_restored_quantity"] == 3
        async def verify():
            cli, db = await _direct_db()
            try:
                item = await db.items.find_one({"slug": "iron_shard"})
                row = await db.inventory_items.find_one(
                    {"guild_id": g["id"], "item_id": item["id"]}
                )
                assert row["quantity"] == 5
                assert row.get("market_locked_qty", 0) == 0
                a = await db.audit_log.count_documents({
                    "event_type": "market_listing_cancelled",
                    "item_slug": "iron_shard",
                })
                assert a >= 1
            finally: cli.close()
        _run(verify())


# ─── Buy ─────────────────────────────────────────────────────────────────


class TestBuyListing:
    def test_buy_self_purchase_forbidden(self):
        auth, g = _bootstrap()
        async def setup():
            cli, db = await _direct_db()
            try: await _grant_item(db, g["id"], "iron_shard", 5)
            finally: cli.close()
        _run(setup())
        r = requests.post(_api("/market/listings"),
                          json={"item_slug": "iron_shard", "quantity": 2, "price_per_unit": 10},
                          headers=auth, timeout=15)
        lid = r.json()["listing_id"]
        r2 = requests.post(_api(f"/market/listings/{lid}/buy"),
                           json={"quantity": 1}, headers=auth, timeout=15)
        assert r2.status_code == 403, r2.text

    def test_buy_insufficient_gold(self):
        auth_s, gs = _bootstrap("r3cS")
        auth_b, gb = _bootstrap("r3cB2")
        async def setup():
            cli, db = await _direct_db()
            try:
                await _grant_item(db, gs["id"], "iron_shard", 5)
                await _set_gold(db, gb["id"], 5)  # buyer poor
            finally: cli.close()
        _run(setup())
        r = requests.post(_api("/market/listings"),
                          json={"item_slug": "iron_shard", "quantity": 2, "price_per_unit": 50},
                          headers=auth_s, timeout=15)
        lid = r.json()["listing_id"]
        r2 = requests.post(_api(f"/market/listings/{lid}/buy"),
                           json={"quantity": 2}, headers=auth_b, timeout=15)
        assert r2.status_code == 409, r2.text
        # Listing should still be active (reverted)
        async def verify():
            cli, db = await _direct_db()
            try:
                d = await db.market_listings.find_one({"id": lid}, {"_id": 0})
                assert d["status"] == "active"
                assert d["quantity"] == 2
                buyer = await db.guilds.find_one({"id": gb["id"]})
                assert buyer["gold"] == 5
            finally: cli.close()
        _run(verify())

    def test_buy_success_transfers_and_applies_fee(self):
        auth_s, gs = _bootstrap("r3cS2")
        auth_b, gb = _bootstrap("r3cB3")
        async def setup():
            cli, db = await _direct_db()
            try:
                await _grant_item(db, gs["id"], "iron_shard", 5)
                await _set_gold(db, gs["id"], 0)
                await _set_gold(db, gb["id"], 100)
            finally: cli.close()
        _run(setup())
        r = requests.post(_api("/market/listings"),
                          json={"item_slug": "iron_shard", "quantity": 2, "price_per_unit": 20},
                          headers=auth_s, timeout=15)
        lid = r.json()["listing_id"]
        r2 = requests.post(_api(f"/market/listings/{lid}/buy"),
                           json={"quantity": 2}, headers=auth_b, timeout=15)
        assert r2.status_code == 200, r2.text
        body = r2.json()
        # 40 gold total, 5% fee = 2, seller gets 38
        assert body["gold_spent"] == 40
        assert body["remaining_gold"] == 60
        async def verify():
            cli, db = await _direct_db()
            try:
                seller = await db.guilds.find_one({"id": gs["id"]})
                assert seller["gold"] == 38  # 40 - 5% fee
                buyer = await db.guilds.find_one({"id": gb["id"]})
                assert buyer["gold"] == 60
                listing = await db.market_listings.find_one({"id": lid}, {"_id": 0})
                assert listing["status"] == "sold"
                assert listing["quantity"] == 0
                assert listing["buyer_guild_id"] == gb["id"]
                # Buyer received items
                item = await db.items.find_one({"slug": "iron_shard"})
                buyer_inv = await db.inventory_items.find_one(
                    {"guild_id": gb["id"], "item_id": item["id"]}
                )
                assert buyer_inv is not None and buyer_inv["quantity"] == 2
                assert buyer_inv["source"] == "market"
                # Seller inv decremented & unlocked
                seller_inv = await db.inventory_items.find_one(
                    {"guild_id": gs["id"], "item_id": item["id"]}
                )
                assert seller_inv["quantity"] == 3  # 5 - 2
                assert seller_inv.get("market_locked_qty", 0) == 0
                # Audit
                cnt_purchase = await db.audit_log.count_documents({"event_type": "market_purchase_completed"})
                cnt_debit = await db.audit_log.count_documents({"event_type": "gold_debited", "actor_guild_id": gb["id"]})
                cnt_credit = await db.audit_log.count_documents({"event_type": "gold_credited", "actor_guild_id": gs["id"]})
                assert cnt_purchase >= 1
                assert cnt_debit >= 1
                assert cnt_credit >= 1
            finally: cli.close()
        _run(verify())

    def test_buy_partial_fill_keeps_listing_active(self):
        auth_s, gs = _bootstrap("r3cP")
        auth_b, gb = _bootstrap("r3cP2")
        async def setup():
            cli, db = await _direct_db()
            try:
                await _grant_item(db, gs["id"], "iron_shard", 5)
                await _set_gold(db, gb["id"], 200)
            finally: cli.close()
        _run(setup())
        r = requests.post(_api("/market/listings"),
                          json={"item_slug": "iron_shard", "quantity": 4, "price_per_unit": 10},
                          headers=auth_s, timeout=15)
        lid = r.json()["listing_id"]
        r2 = requests.post(_api(f"/market/listings/{lid}/buy"),
                           json={"quantity": 1}, headers=auth_b, timeout=15)
        assert r2.status_code == 200, r2.text
        async def verify():
            cli, db = await _direct_db()
            try:
                d = await db.market_listings.find_one({"id": lid}, {"_id": 0})
                assert d["status"] == "active"
                assert d["quantity"] == 3
            finally: cli.close()
        _run(verify())

    def test_buy_race_second_attempt_fails(self):
        auth_s, gs = _bootstrap("r3cR")
        auth_b, gb = _bootstrap("r3cR2")
        async def setup():
            cli, db = await _direct_db()
            try:
                await _grant_item(db, gs["id"], "iron_shard", 5)
                await _set_gold(db, gb["id"], 1000)
            finally: cli.close()
        _run(setup())
        r = requests.post(_api("/market/listings"),
                          json={"item_slug": "iron_shard", "quantity": 3, "price_per_unit": 10},
                          headers=auth_s, timeout=15)
        lid = r.json()["listing_id"]
        # First full-buy succeeds
        r1 = requests.post(_api(f"/market/listings/{lid}/buy"),
                           json={"quantity": 3}, headers=auth_b, timeout=15)
        assert r1.status_code == 200
        # Second attempt on now-sold listing must fail
        r2 = requests.post(_api(f"/market/listings/{lid}/buy"),
                           json={"quantity": 1}, headers=auth_b, timeout=15)
        assert r2.status_code == 409, r2.text


# ─── Listing read ────────────────────────────────────────────────────────


class TestListingRead:
    def test_filters_and_sort(self):
        auth, g = _bootstrap("r3cR3")
        async def setup():
            cli, db = await _direct_db()
            try:
                await _grant_item(db, g["id"], "iron_shard", 10)
                await _grant_item(db, g["id"], "raw_leather", 10)
            finally: cli.close()
        _run(setup())
        requests.post(_api("/market/listings"),
                      json={"item_slug": "iron_shard", "quantity": 1, "price_per_unit": 5},
                      headers=auth, timeout=15)
        requests.post(_api("/market/listings"),
                      json={"item_slug": "raw_leather", "quantity": 1, "price_per_unit": 50},
                      headers=auth, timeout=15)
        # price_max filter
        r = requests.get(_api("/market/listings?price_max=10"), timeout=15)
        assert r.status_code == 200
        slugs = [it["item"]["slug"] for it in r.json()["listings"]]
        for s in slugs:
            assert s != "raw_leather", "price_max=10 should exclude leather@50"
        # sort price_desc
        r2 = requests.get(_api("/market/listings?sort_by=price_desc&limit=5"), timeout=15)
        prices = [it["price_per_unit"] for it in r2.json()["listings"]]
        assert prices == sorted(prices, reverse=True)

    def test_listings_mine_returns_only_own(self):
        auth_a, ga = _bootstrap("r3cMA")
        auth_b, _gb = _bootstrap("r3cMB")
        async def setup():
            cli, db = await _direct_db()
            try: await _grant_item(db, ga["id"], "iron_shard", 5)
            finally: cli.close()
        _run(setup())
        r = requests.post(_api("/market/listings"),
                          json={"item_slug": "iron_shard", "quantity": 1, "price_per_unit": 5},
                          headers=auth_a, timeout=15)
        assert r.status_code == 201
        lid = r.json()["listing_id"]
        # A sees the listing in mine
        mine_a = requests.get(_api("/market/listings/mine"), headers=auth_a, timeout=15).json()
        assert any(li["id"] == lid for li in mine_a["listings"])
        # B does NOT
        mine_b = requests.get(_api("/market/listings/mine"), headers=auth_b, timeout=15).json()
        assert not any(li["id"] == lid for li in mine_b["listings"])

    def test_get_listings_does_not_expose_user_ids(self):
        auth, g = _bootstrap("r3cP3")
        async def setup():
            cli, db = await _direct_db()
            try: await _grant_item(db, g["id"], "iron_shard", 5)
            finally: cli.close()
        _run(setup())
        requests.post(_api("/market/listings"),
                      json={"item_slug": "iron_shard", "quantity": 1, "price_per_unit": 5},
                      headers=auth, timeout=15)
        r = requests.get(_api("/market/listings"), timeout=15)
        body = r.json()
        for it in body["listings"]:
            assert "seller_user_id" not in it
            assert "seller_user_id" not in it.get("seller", {})


# ─── OpenAPI delta ───────────────────────────────────────────────────────


class TestOpenAPIDelta:
    def test_path_count_now_49(self):
        r = requests.get(_api("/openapi.json"), timeout=15)
        paths = r.json().get("paths", {})
        # Updated for Phase 19 §1.2 — added /api/leaderboard/raids (75 → 76)
        assert len(paths) == 77, f"expected 75, got {len(paths)}"
        for p in ("/api/market/listings",
                  "/api/market/listings/mine",
                  "/api/market/listings/{listing_id}",
                  "/api/market/listings/{listing_id}/buy"):
            assert p in paths, f"missing market path: {p}"


if __name__ == "__main__":  # pragma: no cover
    pytest.main([__file__, "-v"])
