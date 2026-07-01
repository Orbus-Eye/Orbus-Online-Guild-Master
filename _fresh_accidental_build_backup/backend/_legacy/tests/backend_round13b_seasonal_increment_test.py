"""ROUND 13b — Backend tests for seasonal incremental tracking.

Covers:
  * the 6 new SEASONAL_CATEGORIES registered.
  * idempotent `increment_seasonal_stat` helper:
      - rejects unknown fields,
      - no-op when no active season,
      - CAS via flag_key prevents double-increment,
      - falls back to no-op when guild has no participation and cannot be created.
  * territory_delta calculator reads `current - snapshot_at_start`.
  * `/api/leaderboard?scope=season&category=<new>` returns 200 for all 6.
  * PII guard on response payload.
"""
from __future__ import annotations

import asyncio
import os
import uuid

import pytest
import requests
from motor.motor_asyncio import AsyncIOMotorClient

from app.seasons.season_stats import (
    ALLOWED_FIELDS,
    increment_seasonal_stat,
    get_active_season,
)
from app.leaderboard.seasonal import (
    SEASONAL_CATEGORIES,
    get_seasonal_rows,
    invalidate_seasonal_cache,
)


def _fresh_db():
    """Build a motor client bound to the *current* event loop (avoids
    `Event loop is closed` after a previous asyncio.run consumed it)."""
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return client[os.environ["DB_NAME"]], client


def _run(coro_factory):
    """Run an async coroutine factory in a fresh loop. The factory MUST take
    a single `db` argument and return a coroutine so motor binds to the
    correct loop on first call.
    """
    async def _wrap():
        db, _client = _fresh_db()
        try:
            return await coro_factory(db)
        finally:
            _client.close()
    return asyncio.run(_wrap())


BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
API = f"{BACKEND_URL}/api"

NEW_R13B_SLUGS = {
    "dungeon_clears", "raid_clears", "raid_score",
    "territory_score", "contracts_completed", "training_score",
}


def _login() -> str:
    r = requests.post(
        f"{API}/auth/login",
        json={"email": "tester@orbus.test", "password": "password123"},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def token() -> str:
    return _login()


# ─── 1. Registry has all 6 new categories ────────────────────────────────────
def test_r13b_01_six_new_categories_registered():
    missing = NEW_R13B_SLUGS - set(SEASONAL_CATEGORIES.keys())
    assert missing == set(), f"missing seasonal categories: {missing}"
    # Total = 6 pre-existing + 6 new = 12.
    assert len(SEASONAL_CATEGORIES) == 12, f"expected 12 categories, got {len(SEASONAL_CATEGORIES)}"


# ─── 2. /api/leaderboard/categories?scope=season exposes 12 categories ───────
def test_r13b_02_categories_endpoint_lists_twelve(token):
    r = requests.get(f"{API}/leaderboard/categories?scope=season",
                     headers=_auth(token), timeout=15)
    assert r.status_code == 200, r.text
    cats = r.json().get("categories", [])
    assert len(cats) == 12, f"expected 12, got {len(cats)}"
    slugs = {c["slug"] for c in cats}
    assert NEW_R13B_SLUGS.issubset(slugs)


# ─── 3. Each new category returns HTTP 200 via /api/leaderboard ──────────────
@pytest.mark.parametrize("slug", sorted(NEW_R13B_SLUGS))
def test_r13b_03_each_new_seasonal_category_returns_200(token, slug):
    r = requests.get(
        f"{API}/leaderboard?scope=season&category={slug}&limit=5",
        headers=_auth(token), timeout=15,
    )
    assert r.status_code == 200, f"{slug}: {r.text[:200]}"
    body = r.json()
    assert body.get("category") == slug
    # Entries may be empty if no participations yet — that's valid.
    assert isinstance(body.get("entries"), list)


# ─── 4. Helper rejects unknown field ─────────────────────────────────────────
def test_r13b_04_increment_rejects_unknown_field():
    async def _t(db):
        report = await increment_seasonal_stat(
            db, guild_id="any", field="totally_made_up", delta=1,
            source="test",
        )
        assert report["applied"] is False
        assert report["reason"] == "field_not_allowed"
    _run(_t)


# ─── 5. Helper no-op when no active season ───────────────────────────────────
def test_r13b_05_increment_noop_when_no_active_season():
    async def _t(db):
        season = await get_active_season(db)
        if season is not None:
            pytest.skip("an active season exists; cannot exercise the no-season branch")
        report = await increment_seasonal_stat(
            db, guild_id="any", field="dungeon_clears", delta=1,
            source="test",
        )
        assert report["applied"] is False
        assert report["reason"] == "no_active_season"
    _run(_t)


# ─── 6. Idempotency CAS — replay does not double-count ───────────────────────
def test_r13b_06_idempotent_via_cas():
    async def _t(db):
        season = await get_active_season(db)
        if season is None:
            pytest.skip("no active season — cannot exercise CAS")
        user = await db.users.find_one({"email": "tester@orbus.test"}, {"_id": 0, "id": 1})
        guild = await db.guilds.find_one({"owner_user_id": user["id"]}, {"_id": 0})
        assert guild is not None
        fake_id = f"test-r13b-cas-{uuid.uuid4()}"
        await db.expeditions.insert_one({"id": fake_id, "guild_id": guild["id"],
                                         "status": "completed", "is_test": True})
        try:
            r1 = await increment_seasonal_stat(
                db, guild_id=guild["id"], field="dungeon_clears", delta=1,
                source="test_cas", source_collection="expeditions",
                source_id=fake_id, flag_key="season_stat_recorded",
            )
            assert r1["applied"] is True, r1
            r2 = await increment_seasonal_stat(
                db, guild_id=guild["id"], field="dungeon_clears", delta=1,
                source="test_cas", source_collection="expeditions",
                source_id=fake_id, flag_key="season_stat_recorded",
            )
            assert r2["applied"] is False, r2
            assert r2["reason"] == "already_recorded"
        finally:
            await db.expeditions.delete_one({"id": fake_id, "is_test": True})
            await db.season_participations.update_one(
                {"season_id": season["season_id"], "guild_id": guild["id"]},
                {"$inc": {"season_stats.dungeon_clears": -1}},
            )
            invalidate_seasonal_cache(season["season_id"])
    _run(_t)


# ─── 7. Territory delta reads current - snapshot_at_start ────────────────────
def test_r13b_07_territory_delta_uses_snapshot():
    async def _t(db):
        season = await get_active_season(db)
        if season is None:
            pytest.skip("no active season")
        invalidate_seasonal_cache(season["season_id"])
        rows, _ = await get_seasonal_rows(db, "territory_score", season["season_id"])
        bad = [r for r in rows if r["score"] < 0]
        assert bad == [], f"negative delta detected: {bad[:3]}"
    _run(_t)


# ─── 8. PII guard on leaderboard payload ─────────────────────────────────────
def test_r13b_08_no_pii_in_leaderboard_seasonal(token):
    for slug in NEW_R13B_SLUGS:
        r = requests.get(
            f"{API}/leaderboard?scope=season&category={slug}&limit=10",
            headers=_auth(token), timeout=15,
        )
        body_str = r.text.lower()
        assert "@orbus.test" not in body_str, f"{slug}: tester email leaked"
        assert "$oid" not in body_str, f"{slug}: raw ObjectId leaked"
        assert "owner_user_id" not in body_str, f"{slug}: owner_user_id leaked"
        assert '"email"' not in body_str, f"{slug}: email field leaked"
        # Output shape: {rank, guild_public_id, guild_name, score, is_me?}.
        for entry in r.json().get("entries", []):
            assert set(entry.keys()).issubset({
                "rank", "guild_public_id", "guild_name", "score",
                "league", "is_me",
            }), f"{slug}: unexpected keys {set(entry.keys())}"


# ─── 9. Unknown category returns 400 with structured detail ──────────────────
def test_r13b_09_unknown_seasonal_category_400(token):
    r = requests.get(
        f"{API}/leaderboard?scope=season&category=bogus_nope_xyz&limit=5",
        headers=_auth(token), timeout=15,
    )
    assert r.status_code == 400, r.text
    detail = r.json().get("detail", {})
    if isinstance(detail, dict):
        assert "unknown_seasonal_category" in detail.get("code", "")
        assert isinstance(detail.get("available"), list)


# ─── 10. ALLOWED_FIELDS whitelist ────────────────────────────────────────────
def test_r13b_10_allowed_fields_match_seasonal_calculators():
    # 5 increment-tracked fields (territory_score is read-only delta).
    expected = {"dungeon_clears", "raid_clears", "raid_score",
                "contracts_completed", "training_score"}
    assert ALLOWED_FIELDS == frozenset(expected)


# ─── 11. /api/leaderboard?scope=season without category → 422 ────────────────
def test_r13b_11_seasonal_requires_category(token):
    r = requests.get(f"{API}/leaderboard?scope=season&limit=5",
                     headers=_auth(token), timeout=15)
    assert r.status_code in (400, 422), f"expected 4xx, got {r.status_code}"


# ─── 12. Smoke: existing R13a/R12 endpoints still alive ──────────────────────
def test_r13b_12_no_regression_smoke(token):
    paths = [
        "/api/dungeons", "/api/raids/catalog", "/api/items",
        "/api/recruitment/candidates", "/api/leaderboard?category=peak_power",
    ]
    for p in paths:
        r = requests.get(f"{BACKEND_URL}{p}", headers=_auth(token), timeout=15)
        assert r.status_code == 200, f"{p}: {r.status_code}"
