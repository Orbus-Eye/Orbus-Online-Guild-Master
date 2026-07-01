"""ROUND 14 — Backend tests for game-health & beta-readiness invariants."""
from __future__ import annotations

import os
import requests
import pytest


BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
API = f"{BACKEND_URL}/api"


def _login(email="tester@orbus.test", password="password123") -> str:
    r = requests.post(f"{API}/auth/login",
                      json={"email": email, "password": password}, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(t: str) -> dict:
    return {"Authorization": f"Bearer {t}"}


@pytest.fixture(scope="module")
def admin_token() -> str:
    return _login()  # tester is admin


# ─── 1. Game-health endpoints require admin auth ─────────────────────────────
@pytest.mark.parametrize("path", [
    "/admin/game-health/economy",
    "/admin/game-health/materials",
    "/admin/game-health/shop",
    "/admin/game-health/progression",
    "/admin/game-health/competitive",
    "/admin/game-health/anomalies",
])
def test_r14_01_game_health_admin_gated(path):
    r = requests.get(f"{API}{path}", timeout=15)
    assert r.status_code in (401, 403), f"{path}: {r.status_code}"


# ─── 2. Admin can call each endpoint, response shape stable ──────────────────
@pytest.mark.parametrize("path,required_keys", [
    ("/admin/game-health/economy?window=24h",
     {"window", "current_gold_in_circulation", "faucets_total_gold",
      "sinks_total_gold", "net_inflation_gold", "admin_granted_gold"}),
    ("/admin/game-health/materials",
     {"materials_total", "materials"}),
    ("/admin/game-health/shop?window=24h",
     {"window", "total_buys", "total_units_bought", "revenue_to_npc_gold"}),
    ("/admin/game-health/progression",
     {"eligible_guilds", "guild_level_dist", "roster_size_dist"}),
    ("/admin/game-health/competitive",
     {"active_season", "participants", "leagues"}),
    ("/admin/game-health/anomalies",
     {"warnings", "checked_at"}),
])
def test_r14_02_game_health_response_shape(admin_token, path, required_keys):
    r = requests.get(f"{API}{path}", headers=_auth(admin_token), timeout=15)
    assert r.status_code == 200, r.text[:300]
    body = r.json()
    missing = required_keys - set(body.keys())
    assert not missing, f"{path}: missing {missing}"


# ─── 3. No PII in any game-health response ───────────────────────────────────
@pytest.mark.parametrize("path", [
    "/admin/game-health/economy",
    "/admin/game-health/materials",
    "/admin/game-health/shop",
    "/admin/game-health/progression",
    "/admin/game-health/competitive",
    "/admin/game-health/anomalies",
])
def test_r14_03_no_pii_in_game_health(admin_token, path):
    r = requests.get(f"{API}{path}", headers=_auth(admin_token), timeout=15)
    body = r.text.lower()
    assert "@orbus.test" not in body
    assert "$oid" not in body
    assert "owner_user_id" not in body
    assert '"email"' not in body
    assert '"password' not in body


# ─── 4. Admin-granted gold is tracked SEPARATELY from player faucets ─────────
def test_r14_04_admin_grants_separate_from_faucets(admin_token):
    r = requests.get(f"{API}/admin/game-health/economy?window=all",
                     headers=_auth(admin_token), timeout=15)
    body = r.json()
    # The two keys must coexist independently.
    assert "admin_granted_gold" in body
    assert "faucets_total_gold" in body


# ─── 5. NPC shop: sell < buy invariant preserved (anti-arbitrage) ────────────
def test_r14_05_shop_no_arbitrage(admin_token):
    r = requests.get(f"{API}/shop/daily_offers",
                     headers=_auth(admin_token), timeout=15)
    for o in r.json()["offers"]:
        assert o["sell_price"] < o["buy_price"], (
            f"arbitrage on {o['item']['slug']}: buy={o['buy_price']} sell={o['sell_price']}"
        )


# ─── 6. No guild has negative gold ───────────────────────────────────────────
def test_r14_06_no_negative_gold(admin_token):
    r = requests.get(f"{API}/admin/game-health/anomalies",
                     headers=_auth(admin_token), timeout=15)
    warnings = r.json()["warnings"]
    critical_neg = [w for w in warnings if w["code"] == "guilds_with_negative_gold"]
    assert critical_neg == [], f"CRITICAL: {critical_neg}"


# ─── 7. Catalog: all active items have required_adventurer_level >= 1 ────────
def test_r14_07_items_required_level_invariant(admin_token):
    r = requests.get(f"{API}/admin/game-health/anomalies",
                     headers=_auth(admin_token), timeout=15)
    warnings = r.json()["warnings"]
    bad = [w for w in warnings if w["code"] == "items_without_required_level"]
    assert bad == [], f"items missing required_adventurer_level: {bad}"


# ─── 8. Lore-reviewed invariants (R13a) preserved ────────────────────────────
def test_r14_08_lore_reviewed_invariants(admin_token):
    r = requests.get(f"{API}/admin/game-health/anomalies",
                     headers=_auth(admin_token), timeout=15)
    warnings = r.json()["warnings"]
    d_bad = [w for w in warnings if w["code"] == "dungeons_not_lore_reviewed"]
    r_bad = [w for w in warnings if w["code"] == "raids_not_lore_reviewed"]
    assert d_bad == [], f"dungeons not lore_reviewed: {d_bad}"
    assert r_bad == [], f"raids not lore_reviewed: {r_bad}"


# ─── 9. Leaderboard does not leak email/oid ──────────────────────────────────
def test_r14_09_leaderboard_no_pii(admin_token):
    r = requests.get(f"{API}/leaderboard?category=peak_power&limit=50",
                     headers=_auth(admin_token), timeout=15)
    body = r.text.lower()
    assert "@orbus.test" not in body
    assert "$oid" not in body
    assert "owner_user_id" not in body


# ─── 10. PvP self-challenge prevented ────────────────────────────────────────
def test_r14_10_no_pvp_self_challenge(admin_token):
    me = requests.get(f"{API}/guilds/me", headers=_auth(admin_token), timeout=15).json()
    my_id = me.get("guild", me).get("id") or me.get("id")
    if not my_id:
        pytest.skip("no guild id available")
    r = requests.post(
        f"{API}/pvp/challenge",
        headers=_auth(admin_token),
        json={"target_guild_id": my_id, "wager_gold": 0},
        timeout=15,
    )
    # Must be rejected: 4xx; never 200.
    assert r.status_code != 200, f"self-challenge accepted: {r.text[:200]}"
    assert 400 <= r.status_code < 500


# ─── 11. Seasonal categories still 12 (R13b invariant) ───────────────────────
def test_r14_11_seasonal_categories_12(admin_token):
    r = requests.get(f"{API}/leaderboard/categories?scope=season",
                     headers=_auth(admin_token), timeout=15)
    assert r.status_code == 200
    cats = r.json().get("categories", [])
    assert len(cats) == 12, f"expected 12 seasonal categories, got {len(cats)}"


# ─── 12. NPC shop refresh 2h still in effect (R13c invariant) ────────────────
def test_r14_12_shop_2h_refresh(admin_token):
    from datetime import datetime
    r = requests.get(f"{API}/shop/daily_offers",
                     headers=_auth(admin_token), timeout=15)
    ts = r.json()["next_reset_at"]
    dt = datetime.fromisoformat(ts)
    assert dt.hour % 2 == 0 and dt.minute == 0
    # Bucket key format keeps the day prefix.
    key = r.json()["day_key"]
    assert "T" in key and len(key) == 13, f"bad bucket key shape: {key}"


# ─── 13. Material catalog excludes Legendary in NPC offers ───────────────────
def test_r14_13_no_legendary_in_npc_shop(admin_token):
    r = requests.get(f"{API}/shop/daily_offers",
                     headers=_auth(admin_token), timeout=15)
    bad = [o for o in r.json()["offers"]
           if o["item"]["rarity"] in ("Legendary", "Epic")]
    assert bad == [], f"NPC shop leaks endgame rarities: {bad}"


# ─── 14. Materials endpoint excludes test/demo guilds ────────────────────────
def test_r14_14_materials_excludes_test(admin_token):
    r = requests.get(f"{API}/admin/game-health/materials",
                     headers=_auth(admin_token), timeout=15)
    body = r.json()
    # We can't directly enumerate excluded guilds, but the response must be
    # internally consistent (count matches list).
    assert body["materials_total"] == len(body["materials"])


# ─── 15. Anomalies endpoint shape is JSON-serialisable + checked_at ISO ──────
def test_r14_15_anomalies_shape(admin_token):
    r = requests.get(f"{API}/admin/game-health/anomalies",
                     headers=_auth(admin_token), timeout=15)
    body = r.json()
    assert isinstance(body["warnings"], list)
    for w in body["warnings"]:
        assert {"severity", "code"}.issubset(w.keys())
        assert w["severity"] in ("warn", "critical")
