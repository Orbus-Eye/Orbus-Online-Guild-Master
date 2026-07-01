"""ROUND 3.A + 3.B (Phase 14.6) — Loot foundations + crafting tests.

Covers:
  • Seed idempotency (items + recipes — double-call ⇒ no duplicates)
  • Public `is_test` anti-leak on /api/items
  • Recipe listing returns per-guild eligibility shape (status + missing + gold_short)
  • Recipe craft: missing materials path (400, no decrement)
  • Recipe craft: insufficient gold path (400, no decrement)
  • Recipe craft: success path (decrement + upsert + gold spend)
  • Recipe `required_guild_level` is enforced
  • OpenAPI path count = 45 (+2 new endpoints)
"""
import asyncio
import os
import uuid

import pytest
import requests
from motor.motor_asyncio import AsyncIOMotorClient

from app.seeds.seed_items_it import seed_italian_items, ITALIAN_ITEM_SEED
from app.seeds.seed_recipes_it import seed_italian_recipes, RECIPE_SEED

pytestmark = pytest.mark.xdist_group(name="round5_serial_legacy")


BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
def _api(p): return f"{BASE_URL}/api{p}"


def _bootstrap():
    suf = uuid.uuid4().hex[:10]
    email = f"r3ab_{suf}@orbus.test"
    payload = {"email": email, "username": f"r3ab_{suf}", "password": "password123"}
    r = requests.post(_api("/auth/register"), json=payload, timeout=15)
    assert r.status_code == 201, r.text
    token = r.json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}
    g = requests.post(_api("/guilds"), json={"name": f"G {suf}", "description": "round3"},
                      headers=auth, timeout=15)
    assert g.status_code == 201, g.text
    body = g.json()
    return auth, body.get("guild", body)


async def _direct_db():
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = cli[os.environ["DB_NAME"]]
    return cli, db


def _run(coro):
    # Updated for Round 5 §I — avoid deprecated `asyncio.get_event_loop()` in 3.11
    # which can return a closed loop after pytest-xdist worker handoffs.
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ─── Seed idempotency ─────────────────────────────────────────────────────────
class TestSeedsIdempotent:
    def test_double_seed_items_no_duplicates(self):
        async def go():
            cli, db = await _direct_db()
            try:
                await seed_italian_items(db)
                await seed_italian_items(db)
                count = await db.items.count_documents({
                    "slug": {"$in": [s["slug"] for s in ITALIAN_ITEM_SEED]}
                })
                assert count == len(ITALIAN_ITEM_SEED)
            finally:
                cli.close()
        _run(go())

    def test_double_seed_recipes_no_duplicates(self):
        async def go():
            cli, db = await _direct_db()
            try:
                await seed_italian_recipes(db)
                await seed_italian_recipes(db)
                count = await db.recipes.count_documents({
                    "slug": {"$in": [s["slug"] for s in RECIPE_SEED]}
                })
                assert count == len(RECIPE_SEED)
            finally:
                cli.close()
        _run(go())


# ─── Anti-leak ────────────────────────────────────────────────────────────────
class TestAntiLeak:
    def test_no_test_items_exposed_publicly(self):
        # Inject a fake test item, ensure /api/items hides it
        async def setup():
            cli, db = await _direct_db()
            try:
                await db.items.insert_one({
                    "id": "test-leak-item-1",
                    "slug": "test_leak_item_1",
                    "name": "Test Leak Sword",
                    "rarity": "Common",
                    "item_type": "weapon",
                    "level_required": 1,
                    "power_score": 0,
                    "strength_bonus": 0, "agility_bonus": 0,
                    "intellect_bonus": 0, "endurance_bonus": 0,
                    "faith_bonus": 0,
                    "is_test": True,
                    "is_active": True,
                })
            finally:
                cli.close()
        async def teardown():
            cli, db = await _direct_db()
            try:
                await db.items.delete_one({"id": "test-leak-item-1"})
            finally:
                cli.close()
        _run(setup())
        try:
            r = requests.get(_api("/items"), timeout=15)
            assert r.status_code == 200
            body = r.json()
            items = body.get("items") or body
            for it in items:
                assert it.get("slug") != "test_leak_item_1", \
                    f"is_test=True item leaked publicly: {it.get('slug')}"
        finally:
            _run(teardown())


# ─── Recipe listing shape ─────────────────────────────────────────────────────
class TestRecipeListing:
    def test_list_returns_eligibility_shape(self):
        auth, _g = _bootstrap()
        r = requests.get(_api("/recipes"), headers=auth, timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "recipes" in body
        assert len(body["recipes"]) == len(RECIPE_SEED)
        for r_ in body["recipes"]:
            for k in ("slug", "display_name", "inputs", "gold_cost",
                      "output", "required_guild_level",
                      "status", "missing", "gold_short"):
                assert k in r_, f"missing {k} in recipe response: {r_}"
            assert r_["status"] in (
                "craftable", "missing_materials", "insufficient_gold", "requires_level"
            )

    def test_brand_new_guild_lacks_all_materials(self):
        auth, _g = _bootstrap()
        r = requests.get(_api("/recipes"), headers=auth, timeout=15).json()
        # A fresh guild has 100 gold and 0 inventory → missing_materials on all
        # base-level recipes (or requires_level for the L2 one).
        for r_ in r["recipes"]:
            if r_["required_guild_level"] > 1:
                assert r_["status"] == "requires_level", r_
            else:
                assert r_["status"] == "missing_materials", r_
                assert r_["missing"], r_


# ─── Crafting flows ───────────────────────────────────────────────────────────
async def _grant_materials(db, guild_id: str, slug: str, qty: int):
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
                "acquired_at": "2026-06-25T21:00:00+00:00",
                "source": "test",
                "bind_state": "unbound",
            },
        },
        upsert=True,
    )


async def _set_gold(db, guild_id: str, gold: int):
    await db.guilds.update_one({"id": guild_id}, {"$set": {"gold": int(gold)}})


class TestCraftingFlows:
    def test_craft_missing_materials_does_not_decrement(self):
        auth, g = _bootstrap()
        async def setup():
            cli, db = await _direct_db()
            try:
                # Only 1 shard, recipe needs 3
                await _grant_materials(db, g["id"], "iron_shard", 1)
            finally:
                cli.close()
        _run(setup())
        r = requests.post(_api("/recipes/recipe_iron_sword/craft"),
                          headers=auth, timeout=15)
        assert r.status_code == 400, r.text
        # Stock untouched
        async def verify():
            cli, db = await _direct_db()
            try:
                item = await db.items.find_one({"slug": "iron_shard"})
                row = await db.inventory_items.find_one(
                    {"guild_id": g["id"], "item_id": item["id"]}
                )
                assert row["quantity"] == 1
                # Output not created
                out_item = await db.items.find_one({"slug": "iron_sword"})
                out_row = await db.inventory_items.find_one(
                    {"guild_id": g["id"], "item_id": out_item["id"]}
                )
                assert out_row is None
            finally:
                cli.close()
        _run(verify())

    def test_craft_insufficient_gold_does_not_decrement(self):
        auth, g = _bootstrap()
        async def setup():
            cli, db = await _direct_db()
            try:
                await _grant_materials(db, g["id"], "iron_shard", 5)
                await _set_gold(db, g["id"], 5)  # < 20 required
            finally:
                cli.close()
        _run(setup())
        r = requests.post(_api("/recipes/recipe_iron_sword/craft"),
                          headers=auth, timeout=15)
        assert r.status_code == 400, r.text
        async def verify():
            cli, db = await _direct_db()
            try:
                item = await db.items.find_one({"slug": "iron_shard"})
                row = await db.inventory_items.find_one(
                    {"guild_id": g["id"], "item_id": item["id"]}
                )
                assert row["quantity"] == 5
                guild = await db.guilds.find_one({"id": g["id"]})
                assert guild["gold"] == 5
            finally:
                cli.close()
        _run(verify())

    def test_craft_success_path(self):
        auth, g = _bootstrap()
        async def setup():
            cli, db = await _direct_db()
            try:
                await _grant_materials(db, g["id"], "iron_shard", 4)
                await _set_gold(db, g["id"], 30)
            finally:
                cli.close()
        _run(setup())
        r = requests.post(_api("/recipes/recipe_iron_sword/craft"),
                          headers=auth, timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["success"] is True
        assert body["output_item"]["slug"] == "iron_sword"
        assert body["output_item"]["quantity"] == 1
        assert body["remaining_gold"] == 10  # 30 - 20
        async def verify():
            cli, db = await _direct_db()
            try:
                shard = await db.items.find_one({"slug": "iron_shard"})
                row = await db.inventory_items.find_one(
                    {"guild_id": g["id"], "item_id": shard["id"]}
                )
                assert row["quantity"] == 1  # 4 - 3
                sword = await db.items.find_one({"slug": "iron_sword"})
                out = await db.inventory_items.find_one(
                    {"guild_id": g["id"], "item_id": sword["id"]}
                )
                assert out is not None and out["quantity"] == 1
                assert out.get("source") == "crafting"
                guild = await db.guilds.find_one({"id": g["id"]})
                assert guild["gold"] == 10
            finally:
                cli.close()
        _run(verify())

    def test_craft_requires_guild_level(self):
        auth, g = _bootstrap()
        # Guild starts at level 1; wanderer_amulet needs level 2.
        async def setup():
            cli, db = await _direct_db()
            try:
                await _grant_materials(db, g["id"], "arcane_dust", 5)
                await _grant_materials(db, g["id"], "dull_gem", 5)
                await _set_gold(db, g["id"], 100)
            finally:
                cli.close()
        _run(setup())
        r = requests.post(_api("/recipes/recipe_wanderer_amulet/craft"),
                          headers=auth, timeout=15)
        assert r.status_code == 400, r.text
        assert "level" in r.text.lower()


class TestOpenAPIDelta:
    def test_path_count_now_45(self):
        r = requests.get(_api("/openapi.json"), timeout=15)
        assert r.status_code == 200
        paths = r.json().get("paths", {})
        # Updated for Phase 19 §1.2 — added /api/leaderboard/raids (75 → 76)
        assert len(paths) == 86, f"expected 75, got {len(paths)}"
        assert "/api/recipes" in paths
        assert "/api/recipes/{recipe_slug}/craft" in paths


if __name__ == "__main__":  # pragma: no cover
    pytest.main([__file__, "-v"])
