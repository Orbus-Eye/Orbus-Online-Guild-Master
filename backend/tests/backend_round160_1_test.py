"""ROUND 16.0.1 — Alchemist class + admin/recruitment cleanup invariants.

Read-only and DB-shape tests:
  T01 Alchemist base class active.
  T02 3 Alchemist specializations active with correct counter_tags.
  T03 1 Class Hall per guild for the alchemist (= guild count).
  T04 filter_safe_class_pool returns exactly the 11 base classes
       (10 R16.0 + alchemist) and zero deprecated slugs.
  T05 Admin classes endpoint default excludes deprecated (filter
       payload check, no auth in unit test — direct query mimics route).
  T06 Audit whitelist contains the new R16.0.1 events.
"""
from __future__ import annotations

import asyncio
import os

import pytest
from motor.motor_asyncio import AsyncIOMotorClient


BASE_CLASSES_R161 = {
    "warrior", "paladin", "rogue", "ranger", "monk",
    "mage", "priest", "druid", "bard", "warlock", "alchemist",
}


def _db_run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def _client():
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return cli[os.environ["DB_NAME"]], cli


# ── T01 ─────────────────────────────────────────────────────────────
def test_t01_alchemist_base_class_active():
    async def _q():
        db, cli = _client()
        try:
            return await db.adventurer_classes.find_one(
                {"slug": "alchemist"},
                {"_id": 0, "slug": 1, "is_base_class": 1,
                 "is_active": 1, "deprecated_at": 1, "round_intro": 1})
        finally:
            cli.close()
    a = _db_run(_q())
    assert a is not None, "alchemist class doc not found"
    assert a["is_active"] is True
    assert a["is_base_class"] is True
    assert a.get("deprecated_at") in (None, ""), "alchemist must not be deprecated"
    assert a.get("round_intro") == "16.0.1"


# ── T02 ─────────────────────────────────────────────────────────────
def test_t02_alchemist_specs_with_counters():
    expected = {
        "bombardier_spec": {"counter_siege"},
        "toxicologist_spec": {"counter_poison", "counter_disease"},
        "transmuter_spec": {"counter_curse", "counter_magic_barrier"},
    }
    async def _q():
        db, cli = _client()
        try:
            return [s async for s in db.class_specializations.find(
                {"parent_class_slug": "alchemist"},
                {"_id": 0, "slug": 1, "counter_tags": 1, "is_active": 1})]
        finally:
            cli.close()
    specs = _db_run(_q())
    assert len(specs) == 3, f"expected 3 alchemist specs, got {len(specs)}"
    by_slug = {s["slug"]: s for s in specs}
    for slug, expected_tags in expected.items():
        assert slug in by_slug, f"missing spec {slug}"
        assert by_slug[slug]["is_active"] is True
        assert set(by_slug[slug]["counter_tags"]) == expected_tags


# ── T03 ─────────────────────────────────────────────────────────────
def test_t03_alchemist_class_halls_per_guild():
    async def _q():
        db, cli = _client()
        try:
            n_guilds = await db.guilds.count_documents({})
            n_halls = await db.class_halls.count_documents(
                {"class_slug": "alchemist"})
            return n_guilds, n_halls
        finally:
            cli.close()
    n_guilds, n_halls = _db_run(_q())
    assert n_halls == n_guilds, (
        f"alchemist class_halls count ({n_halls}) must equal guilds ({n_guilds})")


# ── T04 ─────────────────────────────────────────────────────────────
def test_t04_safe_class_pool_only_active_base():
    from app.adventurers.generator import filter_safe_class_pool
    async def _q():
        db, cli = _client()
        try:
            return await filter_safe_class_pool(db)
        finally:
            cli.close()
    pool = _db_run(_q())
    non_test = [p for p in pool if not p["slug"].startswith("test")]
    slugs = {p["slug"] for p in non_test}
    # The 11 active base classes must all appear in the pool …
    assert slugs == BASE_CLASSES_R161, (
        f"unexpected pool slugs (extra={slugs-BASE_CLASSES_R161}, "
        f"missing={BASE_CLASSES_R161-slugs})")
    # … and none of the 3 deprecated legacy slugs may be present.
    assert not (slugs & {"necromancer", "assassin", "berserker"})


# ── T05 ─────────────────────────────────────────────────────────────
def test_t05_admin_classes_filter_excludes_deprecated():
    """The admin listing endpoint uses this query when
    `?include_deprecated=false` (the default). Verify the query
    produces no rows with deprecated_at != null."""
    async def _q():
        db, cli = _client()
        try:
            query = {
                "$and": [
                    {"deprecated_at": None},
                    {"$or": [
                        {"is_base_class": True},
                        {"is_base_class": {"$exists": False}},
                    ]},
                ]
            }
            rows = [r async for r in db.adventurer_classes.find(
                query, {"_id": 0, "slug": 1, "deprecated_at": 1,
                         "is_base_class": 1})
                    if not r["slug"].startswith("test")]
            return rows
        finally:
            cli.close()
    rows = _db_run(_q())
    deprecated = [r for r in rows if r.get("deprecated_at")]
    assert not deprecated, f"deprecated classes leaked: {deprecated}"
    slugs = {r["slug"] for r in rows}
    # All 11 base classes must be present.
    assert BASE_CLASSES_R161 <= slugs, (
        f"missing base classes from admin default list: "
        f"{BASE_CLASSES_R161 - slugs}")


# ── T06 ─────────────────────────────────────────────────────────────
def test_t06_audit_whitelist_round160_1_events():
    from app.audit.log import EVENT_TYPES
    required = {
        "alchemist_class_seeded",
        "alchemist_class_halls_seeded",
        "recruitment_offers_deprecated_round160",
    }
    missing = required - EVENT_TYPES
    assert not missing, f"R16.0.1 events missing from whitelist: {missing}"


# ── T07 ─────────────────────────────────────────────────────────────
def test_t07_recruitment_offers_deprecated_tagged():
    """Pre-existing offers that point to a deprecated class must carry
    `is_deprecated_round160=True` after running the cleanup script."""
    async def _q():
        db, cli = _client()
        try:
            deprecated_ids = [r["id"] async for r in db.adventurer_classes.find(
                {"$or": [{"is_base_class": False},
                          {"deprecated_at": {"$ne": None}}]},
                {"_id": 0, "id": 1})]
            untagged = await db.recruitment_offers.count_documents({
                "adventurer_class_id": {"$in": deprecated_ids},
                "is_deprecated_round160": {"$ne": True},
            })
            tagged = await db.recruitment_offers.count_documents({
                "adventurer_class_id": {"$in": deprecated_ids},
                "is_deprecated_round160": True,
            })
            return untagged, tagged
        finally:
            cli.close()
    untagged, tagged = _db_run(_q())
    assert untagged == 0, f"{untagged} legacy recruitment_offers still untagged"
    # The tagged count should be >0 if any offers existed before the migration.
    # (If the test DB has no legacy offers, both will be 0 — also acceptable.)
    assert tagged >= 0
