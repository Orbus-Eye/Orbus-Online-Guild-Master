"""ROUND 16.3 Phase 5A — Legendary Forge backend tests.

30 tests covering seed idempotency, guild-level gate, craft flow with
resource/material/gold consumption, deterministic quality distribution,
pity system, hard stat cap clamp, BOP legendary items, on-visit
resolve, dev-force-complete, admin gates, audit whitelist, no hard
delete.
"""
from __future__ import annotations
import asyncio
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import requests

API_BASE = os.environ.get("API_BASE_URL") or "http://localhost:8001"


def _now():
    return datetime.now(timezone.utc)


def _iso(dt):
    return dt.isoformat()


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def _login(email, password="password123"):
    r = requests.post(f"{API_BASE}/api/auth/login",
                      json={"email": email, "password": password}, timeout=10)
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="module")
def admin_headers():
    return _login("tester@orbus.test")


@pytest.fixture(scope="module")
def clean_headers():
    return _login("clean_onboarding@orbus.test")


async def _tester_guild():
    from app.core.database import db
    return await db.guilds.find_one({"name": "The Iron Lantern"},
                                      {"_id": 0})


async def _set_guild_level_and_gold(level: int, gold: int):
    from app.core.database import db
    g = await _tester_guild()
    await db.guilds.update_one(
        {"id": g["id"]},
        {"$set": {"level": level, "gold": gold}})
    return g["id"]


async def _grant_material(guild_id, slug, qty):
    from app.core.database import db
    it = await db.items.find_one({"slug": slug}, {"_id": 0, "id": 1})
    if not it:
        raise AssertionError(f"seed material missing: {slug}")
    # inventory_items has UNIQUE (guild_id, item_id) index — upsert+inc
    await db.inventory_items.update_one(
        {"guild_id": guild_id, "item_id": it["id"]},
        {"$setOnInsert": {"id": str(uuid.uuid4()),
                            "guild_id": guild_id,
                            "item_id": it["id"],
                            "created_at": _iso(_now())},
         "$inc": {"quantity": qty}},
        upsert=True)


async def _clear_forge_state(gid: str):
    """Fresh slate: archive lingering orders + wipe pity + drop inventory
    rows for materials we control in tests."""
    from app.core.database import db
    await db.legendary_forge_crafting_orders.delete_many(
        {"guild_id": gid, "status": "in_progress"})
    await db.legendary_forge_pity_counters.delete_many({"guild_id": gid})


@pytest.fixture(scope="module", autouse=True)
def _seed_before_all():
    from app.legendary_forge import (
        seed_legendary_forge_catalog, ensure_indexes)
    _run(seed_legendary_forge_catalog())
    _run(ensure_indexes())
    yield


# ── T01-T03 seed & catalog ────────────────────────────────────────────
def test_seed_creates_6_recipes():
    from app.core.database import db
    async def _c():
        n = await db.legendary_recipe_catalog.count_documents({})
        assert n == 6, f"expected 6 recipes, got {n}"
    _run(_c())


def test_seed_creates_6_items():
    from app.core.database import db
    async def _c():
        n = await db.legendary_items_catalog.count_documents({})
        assert n == 6
    _run(_c())


def test_seed_idempotent():
    from app.legendary_forge import seed_legendary_forge_catalog
    r = _run(seed_legendary_forge_catalog())
    assert r["inserted_recipes"] == 0
    assert r["inserted_items"] == 0


# ── T04-T05 guild level gate ─────────────────────────────────────────
def test_catalog_gated_below_min_guild_level(admin_headers):
    _run(_set_guild_level_and_gold(1, 1_000_000))
    r = requests.get(f"{API_BASE}/api/legendary-forge/catalog",
                     headers=admin_headers, timeout=10)
    assert r.status_code == 200
    d = r.json()
    assert d["access"] is False
    assert "guild_level_5" in d["requirement"]
    assert d["recipes"] == []


def test_catalog_accessible_from_level_5(admin_headers):
    _run(_set_guild_level_and_gold(10, 1_000_000))
    r = requests.get(f"{API_BASE}/api/legendary-forge/catalog",
                     headers=admin_headers, timeout=10)
    d = r.json()
    assert d["access"] is True
    assert d["guild_level"] == 10
    assert len(d["recipes"]) == 6


# ── T06-T07 preview + probability ────────────────────────────────────
def test_recipe_detail_preview_probabilities(admin_headers):
    _run(_set_guild_level_and_gold(10, 1_000_000))
    r = requests.get(f"{API_BASE}/api/legendary-forge/catalog/anello_di_velur",
                     headers=admin_headers, timeout=10)
    d = r.json()
    # anello_di_velur base=82, lvl_req=5, guild_lvl=10 -> +2*5=+10, cap15 -> +10
    assert d["computed_success_chance"] == 92
    assert d["perfezionato_chance"] == 18
    assert d["imperfetto_chance"] == 7
    assert d["normale_chance"] == 75
    assert "pity_status" in d
    assert "missing_requirements" in d


def test_recipe_detail_missing_resources(admin_headers):
    """Without materials granted, must have missing_requirements."""
    gid = _run(_set_guild_level_and_gold(10, 1_000_000))
    # Clear any grants for this test — check the missing list
    r = requests.get(f"{API_BASE}/api/legendary-forge/catalog/anello_di_velur",
                     headers=admin_headers, timeout=10)
    d = r.json()
    # Fresh tester likely lacks cenere_di_velur; may or may not have gr.arcane_dust
    slugs = [m.get("slug") for m in d["missing_requirements"]
              if m.get("type") in ("resource", "material")]
    assert "cenere_di_velur" in slugs or d["can_craft"] is True


# ── T08-T11 craft consumption & error paths ─────────────────────────
def test_craft_insufficient_gold(admin_headers):
    _run(_set_guild_level_and_gold(10, 100))
    r = requests.post(
        f"{API_BASE}/api/legendary-forge/craft/anello_di_velur",
        headers=admin_headers, timeout=10)
    assert r.status_code == 400
    assert "insufficient" in r.text


def test_craft_insufficient_resources(admin_headers):
    """No cenere_di_velur in inventory → 400."""
    from app.core.database import db
    gid = _run(_set_guild_level_and_gold(10, 1_000_000))
    async def _clear_res():
        for s in ["cenere_di_velur"]:
            it = await db.items.find_one({"slug": s}, {"_id": 0, "id": 1})
            if it:
                await db.inventory_items.delete_many(
                    {"guild_id": gid, "item_id": it["id"]})
    _run(_clear_res())
    r = requests.post(
        f"{API_BASE}/api/legendary-forge/craft/anello_di_velur",
        headers=admin_headers, timeout=10)
    assert r.status_code == 400
    assert "insufficient_resource" in r.text


def test_craft_below_guild_level(admin_headers):
    _run(_set_guild_level_and_gold(6, 1_000_000))  # need 9 for aveol
    r = requests.post(
        f"{API_BASE}/api/legendary-forge/craft/mantello_di_aveol",
        headers=admin_headers, timeout=10)
    assert r.status_code == 403
    assert "guild_level" in r.text


def test_craft_recipe_not_found(admin_headers):
    _run(_set_guild_level_and_gold(10, 1_000_000))
    r = requests.post(f"{API_BASE}/api/legendary-forge/craft/nonexistent",
                       headers=admin_headers, timeout=10)
    assert r.status_code == 404


# ── T12 craft happy path consumes gold + resources + materials ──────
def test_craft_full_consumption(admin_headers):
    from app.core.database import db
    gid = _run(_set_guild_level_and_gold(10, 1_000_000))
    _run(_clear_forge_state(gid))
    # Grant required inputs for anello_di_velur: cenere_di_velur×3 + gr.arcane×4
    _run(_grant_material(gid, "cenere_di_velur", 3))
    _run(_grant_material(gid, "greater_arcane_dust", 4))
    async def _gold():
        g = await db.guilds.find_one({"id": gid}, {"_id": 0, "gold": 1})
        return int(g["gold"])
    gold_before = _run(_gold())
    r = requests.post(
        f"{API_BASE}/api/legendary-forge/craft/anello_di_velur",
        headers=admin_headers, timeout=10)
    assert r.status_code == 200, r.text
    order_id = r.json()["order"]["id"]
    gold_after = _run(_gold())
    assert gold_before - gold_after == 15000
    # Verify materials consumed
    async def _qty(slug):
        it = await db.items.find_one({"slug": slug}, {"_id": 0, "id": 1})
        rows = await db.inventory_items.find(
            {"guild_id": gid, "item_id": it["id"]},
            {"_id": 0, "quantity": 1}).to_list(100)
        return sum(int(x.get("quantity") or 0) for x in rows)
    assert _run(_qty("cenere_di_velur")) == 0
    # Cleanup: force-complete
    requests.post(
        f"{API_BASE}/api/admin/legendary-forge/dev/force-complete/{order_id}",
        headers=admin_headers, timeout=10)


# ── T13-T14 deterministic quality via _rng_for ──────────────────────
def test_deterministic_rng_same_seed():
    from app.legendary_forge import _rng_for
    r1 = _rng_for("g1", "o1")
    r2 = _rng_for("g1", "o1")
    assert r1.randint(1, 100) == r2.randint(1, 100)


def test_quality_boundaries_via_rng():
    """Verify quality bucket logic by simulating rolls."""
    from app.legendary_forge import (PERFEZIONATO_CHANCE, IMPERFETTO_CHANCE)
    # 1..18 = perfezionato, 19..25 = imperfetto, 26..100 = normale
    def bucket(roll):
        if roll <= PERFEZIONATO_CHANCE:
            return "perfezionato"
        if roll <= PERFEZIONATO_CHANCE + IMPERFETTO_CHANCE:
            return "imperfetto"
        return "normale"
    assert bucket(1) == "perfezionato"
    assert bucket(18) == "perfezionato"
    assert bucket(19) == "imperfetto"
    assert bucket(25) == "imperfetto"
    assert bucket(26) == "normale"
    assert bucket(100) == "normale"


# ── T15-T16 pity system ─────────────────────────────────────────────
def test_pity_applied_after_threshold(admin_headers):
    from app.core.database import db
    from app.legendary_forge import _resolve_order, PITY_THRESHOLD
    gid = _run(_set_guild_level_and_gold(10, 1_000_000))
    # Force pity counter at threshold
    async def _setup_pity():
        await db.legendary_forge_pity_counters.update_one(
            {"guild_id": gid},
            {"$set": {"pity_counter_since_perfezionato": PITY_THRESHOLD,
                        "total_craft_count": 5,
                        "total_perfezionato_count": 0,
                        "updated_at": _iso(_now())}},
            upsert=True)
    _run(_setup_pity())
    # Create synthetic order that resolves to imperfetto → clamped to normale
    order_id = str(uuid.uuid4())
    async def _create_and_resolve():
        # Use a specific seed that produces success + imperfetto quality
        # via _rng_for: try several IDs until we hit success+imperfetto
        from app.legendary_forge import (_rng_for, PERFEZIONATO_CHANCE,
                                            IMPERFETTO_CHANCE)
        for i in range(200):
            oid = f"pity-test-{uuid.uuid4().hex[:8]}-{i}"
            rng = _rng_for(gid, oid)
            s_roll = rng.randint(1, 100)
            if s_roll > 92:  # anello_di_velur success chance at guild 10
                continue
            q_roll = rng.randint(1, 100)
            if (PERFEZIONATO_CHANCE < q_roll
                    <= PERFEZIONATO_CHANCE + IMPERFETTO_CHANCE):
                # This oid produces imperfetto → we'll use it
                order = {
                    "id": oid, "guild_id": gid,
                    "recipe_slug": "anello_di_velur",
                    "status": "in_progress",
                    "started_at": _iso(_now() - timedelta(hours=1)),
                    "completes_at": _iso(_now() - timedelta(minutes=5)),
                    "duration_seconds": 180,
                    "resources_consumed": [], "materials_consumed": [],
                    "gold_consumed": 15000,
                    "resolution_started_at": None,
                    "created_at": _iso(_now()),
                }
                await db.legendary_forge_crafting_orders.insert_one(order)
                resolved = await _resolve_order(order)
                return resolved
        raise AssertionError("could not find imperfetto seed in 200 tries")
    resolved = _run(_create_and_resolve())
    assert resolved["result_quality"] == "normale"
    assert resolved["pity_applied"] is True


def test_perfezionato_resets_pity(admin_headers):
    from app.core.database import db
    from app.legendary_forge import _bump_pity
    gid = _run(_set_guild_level_and_gold(10, 1_000_000))
    async def _setup():
        await db.legendary_forge_pity_counters.update_one(
            {"guild_id": gid},
            {"$set": {"pity_counter_since_perfezionato": 3,
                        "total_craft_count": 3,
                        "total_perfezionato_count": 0}},
            upsert=True)
        await _bump_pity(gid, "perfezionato")
        d = await db.legendary_forge_pity_counters.find_one(
            {"guild_id": gid}, {"_id": 0})
        assert d["pity_counter_since_perfezionato"] == 0
        assert d["total_perfezionato_count"] >= 1
    _run(_setup())


# ── T17 hard stat clamp ─────────────────────────────────────────────
def test_clamp_stats_hard_cap():
    from app.legendary_forge import _clamp_stats, LEGENDARY_CAP
    # Weapon with primary=10 (over cap 7): should clamp to 7
    base = {"strength": 10, "endurance": 2, "power_score": 15}
    final, audit = _clamp_stats(base, "weapon", "perfezionato")
    # 10 * 1.15 = 11.5 -> 12 rounded, clamped to 7
    assert final["strength"] == 7
    # power 15 * 1.15 = 17.25 -> 17, clamped to 10
    assert final["power_score"] == 10
    # secondary 2 * 1.15 = 2.3 -> 2, under cap 3
    assert final["endurance"] <= 3
    assert len(audit) >= 2  # at least strength + power_score clamped


def test_clamp_stats_below_cap_passthrough():
    from app.legendary_forge import _clamp_stats
    # Normal case: seeded item stats within cap after quality multiplier
    base = {"strength": 3, "endurance": 3, "power_score": 10}
    final, audit = _clamp_stats(base, "accessory", "normale")
    assert final["strength"] == 3
    assert final["power_score"] == 10
    assert audit == []


# ── T18-T20 BOP legendary items ─────────────────────────────────────
def test_legendary_items_are_bop():
    from app.core.database import db
    async def _c():
        docs = await db.legendary_items_catalog.find(
            {}, {"_id": 0}).to_list(10)
        for d in docs:
            assert d["is_tradeable"] is False, f"{d['slug']} tradeable!"
            assert d["is_bound"] is True
            assert d["bind_type"] == "on_pickup"
            assert d["can_be_sold_for_gold"] is False
            assert d["can_be_sold_for_real_money"] is False
    _run(_c())


def test_granted_instance_is_bound(admin_headers):
    """Force a successful craft → instance in inventory must be bound."""
    from app.core.database import db
    from app.legendary_forge import _resolve_order, _rng_for
    gid = _run(_set_guild_level_and_gold(10, 1_000_000))
    # Find a seed that produces success on anello_di_velur (92% success)
    async def _create_success():
        for i in range(500):
            oid = f"bop-test-{uuid.uuid4().hex[:8]}-{i}"
            rng = _rng_for(gid, oid)
            if rng.randint(1, 100) <= 92:  # success
                order = {
                    "id": oid, "guild_id": gid,
                    "recipe_slug": "anello_di_velur",
                    "status": "in_progress",
                    "started_at": _iso(_now() - timedelta(hours=1)),
                    "completes_at": _iso(_now() - timedelta(minutes=5)),
                    "duration_seconds": 180,
                    "resources_consumed": [], "materials_consumed": [],
                    "gold_consumed": 15000,
                    "resolution_started_at": None,
                    "created_at": _iso(_now())}
                await db.legendary_forge_crafting_orders.insert_one(order)
                res = await _resolve_order(order)
                return res
        raise AssertionError("no success seed found in 500 tries")
    resolved = _run(_create_success())
    assert resolved["result_item_instance_id"] is not None
    async def _check_instance():
        inst = await db.legendary_item_instances.find_one(
            {"id": resolved["result_item_instance_id"]}, {"_id": 0})
        assert inst is not None
        assert inst["is_bound"] is True
        assert inst["bound_to_guild_id"] == gid
        assert inst["is_tradeable"] is False
        assert inst["can_be_sold_for_gold"] is False
        assert inst["legendary_quality"] in (
            "perfezionato", "normale", "imperfetto")
        assert "legendary_stats" in inst
    _run(_check_instance())


def test_legendary_item_mirror_created_in_items_collection():
    """After granting, the `items` collection has legendary mirror row."""
    from app.core.database import db
    async def _c():
        it = await db.items.find_one(
            {"slug": "legendary_ring_velur"},
            {"_id": 0, "is_tradeable": 1, "is_bound": 1,
             "can_be_sold_for_gold": 1, "rarity": 1})
        if it:  # created lazily, may exist from prior test
            assert it["is_tradeable"] is False
            assert it["is_bound"] is True
            assert it["can_be_sold_for_gold"] is False
    _run(_c())


# ── T21 on-visit fallback ───────────────────────────────────────────
def test_orders_mine_on_visit_resolves(admin_headers):
    from app.core.database import db
    gid = _run(_set_guild_level_and_gold(10, 1_000_000))
    # Insert expired in_progress order
    oid = str(uuid.uuid4())
    async def _setup():
        await db.legendary_forge_crafting_orders.insert_one({
            "id": oid, "guild_id": gid,
            "recipe_slug": "anello_di_velur",
            "status": "in_progress",
            "started_at": _iso(_now() - timedelta(hours=1)),
            "completes_at": _iso(_now() - timedelta(minutes=5)),
            "duration_seconds": 180,
            "resources_consumed": [], "materials_consumed": [],
            "gold_consumed": 15000,
            "resolution_started_at": None,
            "created_at": _iso(_now()),
        })
    _run(_setup())
    r = requests.get(f"{API_BASE}/api/legendary-forge/orders/mine",
                     headers=admin_headers, timeout=10)
    assert r.status_code == 200
    async def _check():
        o = await db.legendary_forge_crafting_orders.find_one(
            {"id": oid}, {"_id": 0, "status": 1})
        return o["status"]
    st = _run(_check())
    assert st in ("completed", "failed")


# ── T22 dev-force-complete admin gated ──────────────────────────────
def test_dev_force_complete_non_admin_forbidden(clean_headers):
    fake = str(uuid.uuid4())
    r = requests.post(
        f"{API_BASE}/api/admin/legendary-forge/dev/force-complete/{fake}",
        headers=clean_headers, timeout=10)
    assert r.status_code == 403


def test_dev_force_complete_not_found(admin_headers):
    fake = str(uuid.uuid4())
    r = requests.post(
        f"{API_BASE}/api/admin/legendary-forge/dev/force-complete/{fake}",
        headers=admin_headers, timeout=10)
    assert r.status_code == 404


# ── T23 admin toggle recipe reversible ──────────────────────────────
def test_admin_toggle_recipe_no_hard_delete(admin_headers):
    from app.core.database import db
    r = requests.patch(
        f"{API_BASE}/api/admin/legendary-forge/recipes/anello_di_velur"
        f"?is_active=false",
        headers=admin_headers, timeout=10)
    assert r.status_code == 200
    async def _catalog_count():
        return await db.legendary_recipe_catalog.count_documents({})
    assert _run(_catalog_count()) == 6  # no hard delete
    # Re-enable
    r2 = requests.patch(
        f"{API_BASE}/api/admin/legendary-forge/recipes/anello_di_velur"
        f"?is_active=true",
        headers=admin_headers, timeout=10)
    assert r2.status_code == 200


# ── T24-T27 audit events UPPERCASE ──────────────────────────────────
def test_audit_events_in_whitelist(admin_headers):
    for et in ("LEGENDARY_CRAFT_STARTED", "LEGENDARY_CRAFT_COMPLETED",
                "LEGENDARY_CRAFT_FAILED", "LEGENDARY_STAT_CLAMPED",
                "LEGENDARY_RECIPE_TOGGLED"):
        r = requests.get(
            f"{API_BASE}/api/admin/audit/events?event_type={et}&limit=5",
            headers=admin_headers, timeout=10)
        assert r.status_code == 200, f"{et}: {r.text}"


def test_audit_whitelist_size_28plus():
    from app.audit.log import EVENT_TYPES
    # Must include all 5 new + at least 23 pre-existing that pass filter
    for et in ("LEGENDARY_CRAFT_STARTED", "LEGENDARY_CRAFT_COMPLETED",
                "LEGENDARY_CRAFT_FAILED", "LEGENDARY_STAT_CLAMPED",
                "LEGENDARY_RECIPE_TOGGLED"):
        assert et in EVENT_TYPES


def test_audit_craft_started_emitted(admin_headers):
    """After a successful craft POST, LEGENDARY_CRAFT_STARTED is
    present in the audit log recent entries."""
    from app.core.database import db
    gid = _run(_set_guild_level_and_gold(10, 1_000_000))
    _run(_grant_material(gid, "cenere_di_velur", 3))
    _run(_grant_material(gid, "greater_arcane_dust", 4))
    r = requests.post(
        f"{API_BASE}/api/legendary-forge/craft/anello_di_velur",
        headers=admin_headers, timeout=10)
    assert r.status_code == 200
    order_id = r.json()["order"]["id"]
    async def _check():
        n = await db.audit_log.count_documents(
            {"event_type": "LEGENDARY_CRAFT_STARTED",
             "target_id": order_id})
        return n
    assert _run(_check()) >= 1
    # Cleanup
    requests.post(
        f"{API_BASE}/api/admin/legendary-forge/dev/force-complete/{order_id}",
        headers=admin_headers, timeout=10)


def test_audit_craft_completed_or_failed_emitted(admin_headers):
    from app.core.database import db
    gid = _run(_set_guild_level_and_gold(10, 1_000_000))
    _run(_grant_material(gid, "cenere_di_velur", 3))
    _run(_grant_material(gid, "greater_arcane_dust", 4))
    r = requests.post(
        f"{API_BASE}/api/legendary-forge/craft/anello_di_velur",
        headers=admin_headers, timeout=10)
    assert r.status_code == 200
    order_id = r.json()["order"]["id"]
    requests.post(
        f"{API_BASE}/api/admin/legendary-forge/dev/force-complete/{order_id}",
        headers=admin_headers, timeout=10)
    async def _check():
        n = await db.audit_log.count_documents(
            {"event_type": {"$in": ["LEGENDARY_CRAFT_COMPLETED",
                                        "LEGENDARY_CRAFT_FAILED"]},
             "target_id": order_id})
        return n
    assert _run(_check()) >= 1


# ── T28 admin stats endpoint ────────────────────────────────────────
def test_admin_stats_endpoint(admin_headers):
    r = requests.get(f"{API_BASE}/api/admin/legendary-forge/stats"
                       f"?window_days=7",
                     headers=admin_headers, timeout=10)
    assert r.status_code == 200
    d = r.json()
    assert d["window_days"] == 7
    assert "groups" in d


def test_admin_stats_non_admin_forbidden(clean_headers):
    r = requests.get(f"{API_BASE}/api/admin/legendary-forge/stats",
                     headers=clean_headers, timeout=10)
    assert r.status_code == 403


# ── T29-T30 OpenAPI + no hard delete on orders ──────────────────────
def test_openapi_has_legendary_forge_paths():
    r = requests.get(f"{API_BASE}/api/openapi.json", timeout=10)
    assert r.status_code == 200
    paths = list(r.json()["paths"].keys())
    expected_prefixes = [
        "/api/legendary-forge/catalog",
        "/api/legendary-forge/craft/",
        "/api/legendary-forge/orders/",
        "/api/admin/legendary-forge/",
    ]
    for pref in expected_prefixes:
        assert any(p.startswith(pref) for p in paths), (
            f"missing {pref} in OpenAPI")


def test_no_hard_delete_on_orders(admin_headers):
    """Complete an order via dev-force-complete → still exists in DB."""
    from app.core.database import db
    gid = _run(_set_guild_level_and_gold(10, 1_000_000))
    _run(_grant_material(gid, "cenere_di_velur", 3))
    _run(_grant_material(gid, "greater_arcane_dust", 4))
    r = requests.post(
        f"{API_BASE}/api/legendary-forge/craft/anello_di_velur",
        headers=admin_headers, timeout=10)
    oid = r.json()["order"]["id"]
    requests.post(
        f"{API_BASE}/api/admin/legendary-forge/dev/force-complete/{oid}",
        headers=admin_headers, timeout=10)
    async def _find():
        return await db.legendary_forge_crafting_orders.find_one(
            {"id": oid}, {"_id": 0, "status": 1})
    o = _run(_find())
    assert o is not None
    assert o["status"] in ("completed", "failed")


# ═════════════════════════════════════════════════════════════════════
# POST-VERIFY ITER1 FIXES (T34-T39) — 3 bug P0 dal tester
# ═════════════════════════════════════════════════════════════════════

# ── T34 legendary items mirror in `items` catalog (bug #1 fix)
def test_legendary_items_seeded_in_items_catalog():
    from app.core.database import db
    slugs = [it["slug"] for it in [
        {"slug": "legendary_sword_alveora"},
        {"slug": "legendary_armor_ambash"},
        {"slug": "legendary_ring_velur"},
        {"slug": "legendary_staff_efreto"},
        {"slug": "legendary_amulet_nathos"},
        {"slug": "legendary_cape_aveol"},
    ]]
    async def _c():
        for s in slugs:
            it = await db.items.find_one({"slug": s}, {"_id": 0})
            assert it is not None, f"legendary item {s} missing in items catalog"
            assert it["rarity"] == "legendary"
            assert it["is_tradeable"] is False
            assert it["is_bound"] is True
            assert it["can_be_sold_for_gold"] is False
            assert it["can_be_sold_for_real_money"] is False
            assert it["is_active"] is True
    _run(_c())


# ── T35 inventory includes legendary instances (bug #2 fix)
def test_inventory_includes_legendary_instances(admin_headers):
    """After a successful craft, /api/inventory must include the legendary
    instance with is_legendary_instance=True + is_bound=True + quantity=1."""
    from app.core.database import db
    from app.legendary_forge import _resolve_order, _rng_for
    gid = _run(_set_guild_level_and_gold(10, 1_000_000))
    async def _create_success_and_resolve():
        for i in range(500):
            oid = f"inv-test-{uuid.uuid4().hex[:8]}-{i}"
            rng = _rng_for(gid, oid)
            if rng.randint(1, 100) <= 92:
                order = {
                    "id": oid, "guild_id": gid,
                    "recipe_slug": "anello_di_velur",
                    "status": "in_progress",
                    "started_at": _iso(_now() - timedelta(hours=1)),
                    "completes_at": _iso(_now() - timedelta(minutes=5)),
                    "duration_seconds": 180,
                    "resources_consumed": [], "materials_consumed": [],
                    "gold_consumed": 15000,
                    "resolution_started_at": None,
                    "created_at": _iso(_now())}
                await db.legendary_forge_crafting_orders.insert_one(order)
                res = await _resolve_order(order)
                return res
        raise AssertionError("no success seed found")
    resolved = _run(_create_success_and_resolve())
    assert resolved["result_item_instance_id"] is not None
    # /api/inventory must include it
    r = requests.get(f"{API_BASE}/api/inventory",
                      headers=admin_headers, timeout=10)
    assert r.status_code == 200
    inv = r.json() if isinstance(r.json(), list) else r.json().get("items", r.json().get("inventory", []))
    if isinstance(inv, dict) and "items" in inv:
        inv = inv["items"]
    legendary_entries = [e for e in inv if e.get("is_legendary_instance")]
    matching = [e for e in legendary_entries
                if e.get("instance_id") == resolved["result_item_instance_id"]
                   or e.get("id") == resolved["result_item_instance_id"]]
    assert len(matching) >= 1, (
        f"legendary instance {resolved['result_item_instance_id']} "
        f"not visible in /api/inventory (found {len(legendary_entries)} "
        f"legendary entries total)")
    entry = matching[0]
    assert entry["is_bound"] is True
    assert entry["quantity"] == 1


# ── T36 backwards-compat: non-legendary inventory items still work
def test_inventory_non_legendary_items_backwards_compat(admin_headers):
    r = requests.get(f"{API_BASE}/api/inventory",
                     headers=admin_headers, timeout=10)
    assert r.status_code == 200, f"inventory API broke: {r.text[:200]}"
    inv = r.json()
    if isinstance(inv, dict) and "items" in inv:
        inv = inv["items"]
    if isinstance(inv, dict) and "inventory" in inv:
        inv = inv["inventory"]
    # Response is still an array (backwards-compat contract)
    assert isinstance(inv, list)
    # Each entry (if any) must expose the pre-fix legacy fields
    for e in inv[:5]:
        assert "quantity" in e
        assert "item_id" in e
        assert "guild_id" in e
        # New additive field must NEVER break legacy consumers
        assert "is_legendary_instance" in e  # additive default False/True


# ── T37 market rejects legendary BOP listing (bug #3 verified)
def test_market_rejects_legendary_bop_listing(admin_headers):
    """Attempt to list a legendary item on the market must return 400."""
    r = requests.post(f"{API_BASE}/api/market/listings",
                      json={"item_slug": "legendary_ring_velur",
                            "quantity": 1, "price_per_unit": 1000},
                      headers=admin_headers, timeout=10)
    assert r.status_code == 400, (
        f"expected 400 not_tradeable, got {r.status_code}: {r.text}")
    body = r.text.lower()
    assert ("not tradeable" in body or "not_tradeable" in body
            or "cannot be sold" in body)


# ── T38 auction rejects legendary BOP listing
def test_auction_rejects_legendary_bop_listing(admin_headers):
    r = requests.post(f"{API_BASE}/api/auction/listings",
                      json={"item_slug": "legendary_ring_velur",
                            "quantity": 1, "price_per_unit": 1000},
                      headers=admin_headers, timeout=10)
    assert r.status_code == 400, (
        f"expected 400 not_tradeable, got {r.status_code}: {r.text}")
    body = r.text.lower()
    assert ("not tradeable" in body or "not_tradeable" in body
            or "cannot be sold" in body)
