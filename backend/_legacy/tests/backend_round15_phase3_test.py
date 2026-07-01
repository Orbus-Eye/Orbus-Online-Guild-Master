"""ROUND 15 — Phase 3 backend tests."""
from __future__ import annotations

import asyncio
import os

import pytest
import requests

from app.achievements.engine import evaluate_achievements, ALLOWED_REWARD_TYPES
from app.achievements.levels import (
    current_level_for_xp,
    xp_progress,
    xp_required_for_level,
)


BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
API = f"{BACKEND_URL}/api"


def _login(email="tester@orbus.test", password="password123") -> str:
    r = requests.post(
        f"{API}/auth/login",
        json={"email": email, "password": password},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(t: str) -> dict:
    return {"Authorization": f"Bearer {t}"}


# ─── Level curve ────────────────────────────────────────────────────────────
def test_r15p3_01_level_curve_monotone():
    prev = -1
    for lvl in range(1, 51):
        v = xp_required_for_level(lvl)
        assert v > prev, f"non-monotone at L{lvl}"
        prev = v


def test_r15p3_02_level_curve_checkpoints():
    assert xp_required_for_level(1) == 0
    assert xp_required_for_level(2) == 100
    assert xp_required_for_level(5) == 900
    assert xp_required_for_level(10) == 5000
    assert 23000 <= xp_required_for_level(20) <= 27000
    assert 70000 <= xp_required_for_level(30) <= 80000
    assert 280000 <= xp_required_for_level(50) <= 320000


def test_r15p3_03_current_level_for_xp():
    assert current_level_for_xp(0) == 1
    assert current_level_for_xp(99) == 1
    assert current_level_for_xp(100) == 2
    assert current_level_for_xp(5000) == 10


def test_r15p3_04_xp_progress_shape():
    p = xp_progress(200)
    assert set(p.keys()) == {"level", "xp", "xp_into_level", "xp_for_next_level", "next_level_at"}
    assert p["level"] == 2
    assert p["xp_into_level"] == 100


# ─── Live API ───────────────────────────────────────────────────────────────
def test_r15p3_05_catalog_count_at_least_100():
    t = _login()
    r = requests.get(f"{API}/achievements/catalog", headers=_auth(t), timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body, dict)
    items = body["achievements"]
    # All 14 categories represented in the seed.
    assert len(items) >= 100, f"expected ≥100, got {len(items)}"
    cats = {it["category"] for it in items}
    expected = {
        "primi_passi", "roster", "dungeon", "raid", "equipaggiamento",
        "classi_stats", "territorio", "crafting", "economia",
        "pvp_stagioni", "leaderboard", "consorzi", "lore",
    }
    missing = expected - cats
    assert not missing, f"missing categories: {missing}"


def test_r15p3_06_catalog_in_progress_hides_hidden():
    t = _login()
    r = requests.get(
        f"{API}/achievements/catalog?state=in_progress",
        headers=_auth(t), timeout=15,
    )
    assert r.status_code == 200
    items = r.json()["achievements"]
    assert not any(i.get("is_hidden") for i in items), (
        "hidden achievements must not appear in `in_progress` listing"
    )


def test_r15p3_07_summary_shape_and_no_pii():
    t = _login()
    r = requests.get(f"{API}/achievements/summary", headers=_auth(t), timeout=15)
    assert r.status_code == 200
    body = r.json()
    for f in ("guild_id", "guild_xp", "guild_level", "achievement_points",
              "completed_count", "total_catalog_count", "progress"):
        assert f in body
    text = r.text.lower()
    assert "@orbus.test" not in text
    assert "password" not in text
    assert "$oid" not in text


def test_r15p3_08_progress_endpoint_returns_progress_rows():
    t = _login()
    r = requests.get(f"{API}/achievements/progress", headers=_auth(t), timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert "progress" in body
    assert isinstance(body["progress"], list)


# ─── Reward whitelist invariant ─────────────────────────────────────────────
def test_r15p3_09_reward_whitelist_is_cosmetic_only():
    assert "gold" not in ALLOWED_REWARD_TYPES
    assert "drop_boost" not in ALLOWED_REWARD_TYPES
    assert "xp_boost" not in ALLOWED_REWARD_TYPES
    assert ALLOWED_REWARD_TYPES == frozenset({
        "xp_points", "xp_points_title", "xp_points_badge", "xp_points_frame",
    })


# ─── Engine: admin-source filter & idempotency ──────────────────────────────
def test_r15p3_10_admin_source_does_not_trigger():
    """Use the engine directly against a fake DB stub to verify the
    admin-source guard short-circuits before any DB call."""
    class _Stub:
        called = False
        achievements_catalog = type("c", (), {
            "find": lambda *a, **k: (_ for _ in ()).throw(
                AssertionError("admin source must short-circuit")
            )
        })()

    async def _run():
        out = await evaluate_achievements(
            "fake-guild-id", "dungeon_completed",
            {"source": "admin"}, db=_Stub(),
        )
        assert out == []

    asyncio.run(_run())
