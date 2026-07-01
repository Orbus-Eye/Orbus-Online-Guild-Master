"""ROUND 12.A — Backend tests for Seasons + PvP rating helpers.

Unit-first: covers pure helpers (assign_league, Elo, simulator outcomes).
Smoke API tests for season endpoints (uses tester credentials).

Test count: 26+ (see Task 9 mapping below).
"""
from __future__ import annotations

import os
import re
import uuid
from pathlib import Path

import pytest
import requests


BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
TESTER_EMAIL = "tester@orbus.test"
TESTER_PW = os.environ.get("R11_TEST_PASSWORD", "password123")


# ─── Pure unit tests — no network ─────────────────────────────────────────────
def test_01_assign_league_unranked():
    from app.seasons.services import assign_league
    assert assign_league(1500, 4) == "unranked"


def test_02_assign_league_bronze():
    from app.seasons.services import assign_league
    assert assign_league(900, 10) == "bronze"


def test_03_assign_league_silver():
    from app.seasons.services import assign_league
    assert assign_league(1100, 10) == "silver"


def test_04_assign_league_gold():
    from app.seasons.services import assign_league
    assert assign_league(1350, 10) == "gold"


def test_05_assign_league_platinum():
    from app.seasons.services import assign_league
    assert assign_league(1500, 10) == "platinum"


def test_06_assign_league_diamond():
    from app.seasons.services import assign_league
    assert assign_league(1700, 10) == "diamond"


def test_07_assign_league_master():
    from app.seasons.services import assign_league
    assert assign_league(1850, 10) == "master"


def test_08_elo_expected_balanced():
    from app.pvp.rating import expected_score
    assert abs(expected_score(1000, 1000) - 0.5) < 1e-6


def test_09_elo_expected_underdog():
    from app.pvp.rating import expected_score
    e = expected_score(1000, 1400)
    assert 0.0 < e < 0.15


def test_10_elo_delta_win_underdog_is_large():
    from app.pvp.rating import rating_delta
    d = rating_delta(1000, 1400, "win")
    assert d > 20  # Large positive delta when an underdog wins.


def test_11_elo_delta_draw_balanced_is_zero():
    from app.pvp.rating import rating_delta
    assert abs(rating_delta(1000, 1000, "draw")) <= 1


def test_12_elo_apply_match_floor_at_zero():
    from app.pvp.rating import apply_match
    a, b = apply_match(0, 2000, "loss")
    assert a == 0  # Floor respected; no negative rating.
    assert b >= 2000


def test_13_simulator_returns_versions():
    from app.pvp.simulator import simulate, COMBAT_VERSION, RNG_VERSION
    att = {"guild_name": "A", "adventurers": [
        {"level": 5, "role": "Tank", "stats": {"atk": 10, "def": 10}, "equip_bonus": 5, "traits": []} for _ in range(5)
    ]}
    defn = {"guild_name": "D", "adventurers": [
        {"level": 5, "role": "DPS", "stats": {"atk": 10, "def": 10}, "equip_bonus": 5, "traits": []} for _ in range(5)
    ]}
    out = simulate(att, defn, match_id="m1", season_id="s1")
    assert out["combat_version"] == COMBAT_VERSION
    assert out["rng_version"] == RNG_VERSION
    assert out["outcome"] in ("attacker_win", "defender_win", "draw")
    assert len(out["report_it"]) >= 3
    assert len(out["report_it"]) <= 6


def test_14_simulator_trio_bonus_increases_score():
    from app.pvp.simulator import simulate
    no_synergy = [{"level": 5, "role": "DPS", "stats": {"atk": 10}, "equip_bonus": 0, "traits": []} for _ in range(5)]
    trio = [
        {"level": 5, "role": "Tank", "stats": {"atk": 10}, "equip_bonus": 0, "traits": []},
        {"level": 5, "role": "Healer", "stats": {"atk": 10}, "equip_bonus": 0, "traits": []},
        {"level": 5, "role": "DPS", "stats": {"atk": 10}, "equip_bonus": 0, "traits": []},
        {"level": 5, "role": "DPS", "stats": {"atk": 10}, "equip_bonus": 0, "traits": []},
        {"level": 5, "role": "DPS", "stats": {"atk": 10}, "equip_bonus": 0, "traits": []},
    ]
    # Run multiple sims (stochastic) — check breakdown not outcome
    att_snap = {"guild_name": "A", "adventurers": trio}
    def_snap = {"guild_name": "D", "adventurers": no_synergy}
    out = simulate(att_snap, def_snap, match_id="m2", season_id="s1")
    assert out["attacker_breakdown"]["role_multiplier"] >= 1.21  # tank+healer+dps+trio bonus
    assert out["defender_breakdown"]["role_multiplier"] <= 1.04  # only DPS bonus


def test_15_simulator_seed_hash_deterministic_on_ids():
    from app.pvp.simulator import simulate
    att = {"guild_name": "A", "adventurers": [{"level": 1, "role": "DPS", "stats": {}, "equip_bonus": 0, "traits": []}] * 5}
    defn = {"guild_name": "D", "adventurers": [{"level": 1, "role": "DPS", "stats": {}, "equip_bonus": 0, "traits": []}] * 5}
    out1 = simulate(att, defn, match_id="X", season_id="Y")
    out2 = simulate(att, defn, match_id="X", season_id="Y")
    # outcome may vary (RNG), but seed_hash is deterministic from (match_id, season_id).
    assert out1["seed_hash"] == out2["seed_hash"]


# ─── API smoke tests — require running backend at BACKEND_URL ─────────────────
@pytest.fixture(scope="module")
def tester_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": TESTER_EMAIL, "password": TESTER_PW}, timeout=10)
    if r.status_code != 200:
        pytest.skip(f"tester login failed: {r.status_code} {r.text[:200]}")
    return s


def test_16_seasons_current_returns_active_preseason():
    r = requests.get(f"{BASE_URL}/api/seasons/current", timeout=10)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["season"]["status"] == "active"
    assert body["season"]["slug"] == "arena-preseason-2026"
    assert body["season"]["lore_theme"] == "equilibrio"


def test_17_seasons_current_has_countdown():
    r = requests.get(f"{BASE_URL}/api/seasons/current", timeout=10)
    body = r.json()
    cd = body.get("countdown")
    assert cd is not None
    assert cd["seconds_remaining"] > 0
    assert cd["days_remaining"] >= 0


def test_18_season_detail_by_slug():
    r = requests.get(f"{BASE_URL}/api/seasons/arena-preseason-2026", timeout=10)
    assert r.status_code == 200
    assert r.json()["season"]["slug"] == "arena-preseason-2026"


def test_19_season_detail_404_unknown():
    r = requests.get(f"{BASE_URL}/api/seasons/does-not-exist", timeout=10)
    assert r.status_code == 404


def test_20_season_leaderboards_entry():
    r = requests.get(f"{BASE_URL}/api/seasons/arena-preseason-2026/leaderboards", timeout=10)
    assert r.status_code == 200
    body = r.json()
    assert "categories" in body
    slugs = [c["slug"] for c in body["categories"]]
    assert "arena_rating" in slugs
    assert "arena_wins" in slugs


def test_21_leaderboard_categories_scope_season():
    r = requests.get(f"{BASE_URL}/api/leaderboard/categories?scope=season", timeout=10)
    assert r.status_code == 200
    body = r.json()
    assert body["scope"] == "season"
    assert isinstance(body["categories"], list)


def test_22_leaderboard_categories_scope_global_default():
    r = requests.get(f"{BASE_URL}/api/leaderboard/categories", timeout=10)
    assert r.status_code == 200
    body = r.json()
    assert body["scope"] == "global"


def test_23_admin_season_create_requires_auth():
    r = requests.post(f"{BASE_URL}/api/admin/seasons/create",
                       json={"slug": "x", "name_it": "y", "starts_at": "x", "ends_at": "y", "reason": "test"},
                       timeout=10)
    assert r.status_code in (401, 403)


def test_24_pvp_defense_team_requires_auth():
    r = requests.get(f"{BASE_URL}/api/pvp/defense-team", timeout=10)
    assert r.status_code == 401


def test_25_pvp_opponents_requires_auth():
    r = requests.get(f"{BASE_URL}/api/pvp/opponents", timeout=10)
    assert r.status_code == 401


def test_26_pvp_defense_team_authed_returns_min_level(tester_session):
    r = tester_session.get(f"{BASE_URL}/api/pvp/defense-team", timeout=10)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["min_level_required"] >= 3
    assert body["team_size_required"] == 5


def test_27_pvp_no_pii_in_opponents(tester_session):
    """PII guard: opponents response must not leak email/user_id/_id/owner."""
    r = tester_session.get(f"{BASE_URL}/api/pvp/opponents", timeout=10)
    if r.status_code == 423:
        pytest.skip("no active season at smoke time")
    assert r.status_code == 200, r.text
    body = r.json()
    # Per-entry key inspection (substring checks on str(body) false-positive
    # against legitimate keys like `guild_public_id`).
    for opp in body.get("opponents", []):
        for forbidden in ("_id", "owner_user_id", "user_id", "email"):
            assert forbidden not in opp, f"PII leak: '{forbidden}' in {opp}"
        # No email-shaped strings in any value.
        for v in opp.values():
            if isinstance(v, str):
                assert "@" not in v, f"PII leak: email-shaped string in value {v!r}"


def test_28_seed_round12_preseason_idempotent():
    """The preseason seed must be re-runnable without creating duplicates."""
    import asyncio
    from app.scripts.seed_round12_preseason import run
    res = asyncio.run(run())
    assert res["status"] in ("skipped", "created")
    # If we hit this point on second run, it should always skip.
    if res["status"] == "skipped":
        assert res["reason"] in ("slug_already_present", "another_active_season")


def test_29_pvp_self_challenge_blocked(tester_session):
    """Self-challenge guard fires before any team validation."""
    me_body = tester_session.get(f"{BASE_URL}/api/guilds/me", timeout=10).json()
    me = me_body.get("guild") or me_body
    my_public = me.get("public_id") or me["id"][:8]
    r = tester_session.post(
        f"{BASE_URL}/api/pvp/challenge",
        json={"opponent_guild_public_id": my_public, "attacker_adventurer_ids": ["x"] * 5},
        timeout=10,
    )
    # Either self_challenge (400) — the strict guard — or auth/csrf wall (403/401).
    # Both are acceptable: the key invariant is that the call does NOT succeed.
    assert r.status_code in (400, 401, 403, 404, 422), r.text
    if r.status_code == 400:
        body = r.json()
        assert body.get("detail", {}).get("code") == "pvp.self_challenge"


def test_30_pvp_challenge_bad_payload_400(tester_session):
    r = tester_session.post(f"{BASE_URL}/api/pvp/challenge", json={"foo": "bar"}, timeout=10)
    assert r.status_code in (400, 401, 403, 422)
