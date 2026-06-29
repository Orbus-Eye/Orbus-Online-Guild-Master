"""ROUND 12.C — Polish tests: reward cosmetic guard, league field in
seasonal LB, scope=global vs season, admin gates, account_age_gate, etc.
"""
from __future__ import annotations

import os
import asyncio
import uuid

import pytest
import requests


BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
TESTER_EMAIL = "tester@orbus.test"
TESTER_PW = os.environ.get("R11_TEST_PASSWORD", "password123")


@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"email": TESTER_EMAIL, "password": TESTER_PW}, timeout=10)
    if r.status_code != 200:
        pytest.skip(f"tester login failed: {r.status_code}")
    # Tester is admin by seed; fetch CSRF for mutating requests.
    csrf = s.get(f"{BASE_URL}/api/auth/csrf", timeout=10).json()
    s.headers.update({"X-CSRF-Token": csrf.get("csrf_token", "")})
    return s


# ─── Reward cosmetic enforcement (unit + API) ─────────────────────────────────
def test_31_reward_whitelist_blocks_non_cosmetic():
    from app.rewards.services import _validate_cosmetic
    with pytest.raises(Exception):
        _validate_cosmetic({"reward_type": "gold", "cosmetic_only": True,
                            "name_it": "Boost Oro", "description_it": "Extra gold"})


def test_32_reward_whitelist_blocks_forbidden_field_in_text():
    from app.rewards.services import _validate_cosmetic
    with pytest.raises(Exception):
        # Title is cosmetic but text contains "boost" → blocked.
        _validate_cosmetic({"reward_type": "title", "cosmetic_only": True,
                            "name_it": "Boost Hero", "description_it": "Stats boost"})


def test_33_reward_cosmetic_passes():
    from app.rewards.services import _validate_cosmetic
    _validate_cosmetic({"reward_type": "badge", "cosmetic_only": True,
                        "name_it": "Distintivo Veterano",
                        "description_it": "Onore per la prima Preseason."})


def test_34_reward_cosmetic_only_required():
    from app.rewards.services import _validate_cosmetic
    with pytest.raises(Exception):
        _validate_cosmetic({"reward_type": "title", "cosmetic_only": False,
                            "name_it": "X", "description_it": "Y"})


def test_35_rewards_public_listing():
    r = requests.get(f"{BASE_URL}/api/seasons/arena-preseason-2026/rewards", timeout=10)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] >= 4
    slugs = {x["reward_id"] for x in body["rewards"]}
    assert "preseason_veteran_title" in slugs
    assert "glory_master_title" in slugs
    for rew in body["rewards"]:
        assert rew["cosmetic_only"] is True


# ─── Seasonal LB: league field exposure ───────────────────────────────────────
def test_36_seasonal_lb_arena_rating_includes_league():
    r = requests.get(
        f"{BASE_URL}/api/leaderboard?scope=season&season=arena-preseason-2026&category=arena_rating",
        timeout=10,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    # No participants in fresh DB yet → entries can be empty; test for shape.
    for e in body.get("entries", []):
        assert "league" in e, f"entry missing league: {e}"


def test_37_seasonal_lb_arena_wins_includes_league():
    r = requests.get(
        f"{BASE_URL}/api/leaderboard?scope=season&season=arena-preseason-2026&category=arena_wins",
        timeout=10,
    )
    assert r.status_code == 200, r.text
    for e in r.json().get("entries", []):
        assert "league" in e


# ─── Scope routing ────────────────────────────────────────────────────────────
def test_38_scope_global_vs_season_differ():
    """The two scopes share infrastructure but expose different category sets."""
    g = requests.get(f"{BASE_URL}/api/leaderboard/categories", timeout=10).json()
    s = requests.get(f"{BASE_URL}/api/leaderboard/categories?scope=season", timeout=10).json()
    assert g["scope"] == "global"
    assert s["scope"] == "season"
    g_slugs = {c["slug"] for c in g["categories"]}
    s_slugs = {c["slug"] for c in s["categories"]}
    assert "arena_rating" in s_slugs
    assert "arena_rating" not in g_slugs


def test_39_global_scope_preserved_backward_compat():
    """Default scope is global (no query → still works)."""
    r = requests.get(f"{BASE_URL}/api/leaderboard?category=peak_power", timeout=10)
    assert r.status_code == 200


# ─── Admin gates ──────────────────────────────────────────────────────────────
def test_40_admin_grant_rewards_requires_admin():
    r = requests.post(
        f"{BASE_URL}/api/admin/seasons/nonexistent/grant_rewards",
        json={"reason": "test", "dry_run": True}, timeout=10,
    )
    assert r.status_code in (401, 403)


def test_41_admin_grant_rewards_reason_required(admin_session):
    # Use the active season id.
    cur = requests.get(f"{BASE_URL}/api/seasons/current", timeout=10).json()
    season_id = cur["season"]["season_id"]
    r = admin_session.post(
        f"{BASE_URL}/api/admin/seasons/{season_id}/grant_rewards",
        json={"reason": "ab", "dry_run": True}, timeout=10,
    )
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "admin.reason_too_short"


def test_42_admin_grant_rewards_dry_run_idempotent(admin_session):
    cur = requests.get(f"{BASE_URL}/api/seasons/current", timeout=10).json()
    season_id = cur["season"]["season_id"]
    r1 = admin_session.post(
        f"{BASE_URL}/api/admin/seasons/{season_id}/grant_rewards",
        json={"reason": "dry-run smoke 12.C", "dry_run": True}, timeout=10,
    )
    assert r1.status_code == 200, r1.text
    body = r1.json()
    assert body["dry_run"] is True
    assert body["ok"] is True


# ─── Account age gate ─────────────────────────────────────────────────────────
def test_43_min_guild_age_constant_exists():
    from app.pvp.services import MIN_GUILD_AGE_SECONDS
    assert MIN_GUILD_AGE_SECONDS >= 60 * 60  # at least 1h preview, 24h prod target.


# ─── PII guards on opponents (sanity, R12.A had test_27; here we cross-verify) ─
def test_44_opponents_response_safe_keys(admin_session):
    r = admin_session.get(f"{BASE_URL}/api/pvp/opponents", timeout=10)
    if r.status_code == 423:
        pytest.skip("season inactive")
    assert r.status_code == 200
    for opp in r.json()["opponents"]:
        for forbidden in ("email", "owner_user_id", "user_id", "_id"):
            assert forbidden not in opp
        # Public ID is allowed but is NOT the full UUID.
        assert len(opp.get("guild_public_id", "")) <= 32


# ─── OpenAPI sanity: new endpoints registered ─────────────────────────────────
def test_45_openapi_includes_round12_endpoints():
    r = requests.get(f"{BASE_URL}/api/openapi.json", timeout=10)
    paths = list(r.json()["paths"].keys())
    expected = [
        "/api/seasons/current",
        "/api/pvp/challenge",
        "/api/pvp/defense-team",
        "/api/pvp/matches",
        "/api/admin/seasons/{season_id}/activate",
        "/api/admin/seasons/{season_id}/grant_rewards",
        "/api/seasons/{slug}/rewards",
    ]
    for p in expected:
        assert p in paths, f"missing endpoint in OpenAPI: {p}"


def test_46_seed_round12_rewards_idempotent():
    from app.scripts.seed_round12_rewards import run
    res = asyncio.run(run())
    assert res["status"] in ("done", "skipped")


# ─── ROUND 12.D — Demo opponents + validation ordering ────────────────────────
DEMO_GUILD_NAMES = {
    "Custodi del Vento",
    "Esiliati del Vuoto",
    "Compagnia delle Tre Lune",
}


def test_47_demo_opponents_visible_in_pvp_opponents(admin_session):
    """ROUND 12.D.6.a — The 3 lore-coherent demo guilds must be visible to
    the tester in /api/pvp/opponents (matchmaking unranked → all leagues)."""
    r = admin_session.get(f"{BASE_URL}/api/pvp/opponents?limit=20", timeout=10)
    if r.status_code == 423:
        pytest.skip("season inactive")
    assert r.status_code == 200, r.text
    names = {o["guild_name"] for o in r.json()["opponents"]}
    missing = DEMO_GUILD_NAMES - names
    assert not missing, f"missing demo opponents in /api/pvp/opponents: {missing}"


def test_48_demo_opponents_excluded_from_seasonal_leaderboard():
    """ROUND 12.D.6.b — Demo guilds must NOT appear in any seasonal LB."""
    r = requests.get(
        f"{BASE_URL}/api/leaderboard"
        f"?scope=season&season=arena-preseason-2026&category=arena_rating",
        timeout=10,
    )
    assert r.status_code == 200, r.text
    entries = r.json().get("entries", [])
    leaked = [e["guild_name"] for e in entries if e["guild_name"] in DEMO_GUILD_NAMES]
    assert not leaked, f"demo guilds leaked into seasonal LB: {leaked}"


def test_49_challenge_validation_orders_team_size_first(admin_session):
    """ROUND 12.D.6.c — `pvp.team_size_mismatch` (422) must precede any
    opponent-lookup error (404). Send a malformed payload pointing to a
    bogus opponent and verify the team-size error fires."""
    bogus_opp = "zzz9zzz9"  # guaranteed not to exist as guild public_id
    r = admin_session.post(
        f"{BASE_URL}/api/pvp/challenge",
        json={
            "opponent_guild_public_id": bogus_opp,
            "attacker_adventurer_ids": ["only-one-id"],  # len=1, not 5
            "mode": "ranked",
        },
        timeout=10,
    )
    assert r.status_code == 422, r.text
    body = r.json()
    assert body["detail"]["code"] == "pvp.team_size_mismatch", body


def test_50_challenge_blocks_self_challenge(admin_session):
    """ROUND 12.D.6.d — Self-challenge must yield 400 pvp.self_challenge,
    even when payload shape is technically valid (5 ids)."""
    me = admin_session.get(f"{BASE_URL}/api/guilds/me", timeout=10).json()
    g = me["guild"]
    # PvP services derive public_id from `g['public_id']` or `g['id'][:8]`.
    my_public_id = g.get("public_id") or g["id"][:8]
    r = admin_session.post(
        f"{BASE_URL}/api/pvp/challenge",
        json={
            "opponent_guild_public_id": my_public_id,
            # 5 fake but list-shape-valid ids so we pass the size check
            "attacker_adventurer_ids": [f"fake-{i}" for i in range(5)],
            "mode": "ranked",
        },
        timeout=10,
    )
    assert r.status_code == 400, r.text
    assert r.json()["detail"]["code"] == "pvp.self_challenge"
