"""ROUND 16.A Phase 1 — achievement trigger emission layer.

Verifies that the 11 catalog `trigger_event` values are wired to real
gameplay sites and that the central emitter behaves correctly
(idempotent, best-effort, engine-delegated).

Strategy:
    Many of these triggers live in complex services (PvP, market,
    auction, territory) whose full end-to-end setup is expensive. We
    take a hybrid approach:

      * Direct unit tests on the emitter (idempotency, no guild_id,
        unknown event).
      * For each wired trigger, we add a `trigger_emissions` collection
        assertion *if* the underlying flow can be exercised cheaply via
        the API on the tester guild; otherwise we drop a dedicated
        check that the trigger CODE PATH is present (grep on the source
        is acceptable as a smoke verification).
      * 1 trigger is DEFERRED (`leaderboard_rank_reached`): the
        leaderboard module computes ranks on-demand with no per-guild
        update hook, so there is no event to wire without inventing
        new infrastructure (out of scope for this round).
"""
from __future__ import annotations

import os
import re
import uuid
from pathlib import Path

import pytest
import requests


API_BASE = os.environ.get("API_BASE_URL") or "http://localhost:8001"
REPO_BACKEND = Path(__file__).resolve().parents[1] / "app"


@pytest.fixture(scope="module")
def auth_headers():
    r = requests.post(
        f"{API_BASE}/api/auth/login",
        json={"email": "tester@orbus.test", "password": "password123"},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="module")
def tester_guild_id(auth_headers):
    r = requests.get(f"{API_BASE}/api/guilds/me",
                     headers=auth_headers, timeout=10)
    assert r.status_code == 200
    data = r.json()
    return (data.get("guild") or data).get("id")


# ── 0. Emitter unit tests ────────────────────────────────────────────
def test_emitter_skips_when_guild_id_missing():
    import asyncio
    from app.achievements.trigger_emitter import emit_achievement_trigger
    out = asyncio.get_event_loop().run_until_complete(
        emit_achievement_trigger(
            db=None, guild_id=None, event_name="item_crafted", payload={}))
    assert out == []


def test_emitter_skips_when_event_name_missing():
    import asyncio
    from app.achievements.trigger_emitter import emit_achievement_trigger
    out = asyncio.get_event_loop().run_until_complete(
        emit_achievement_trigger(
            db=None, guild_id="g1", event_name="", payload={}))
    assert out == []


# ── Source-grep helper: confirms a trigger is wired in the codebase ──
def _grep(filename: str, pattern: str) -> bool:
    p = REPO_BACKEND / filename
    if not p.exists():
        return False
    txt = p.read_text(encoding="utf-8")
    return re.search(pattern, txt) is not None


# ── 1. item_crafted ──────────────────────────────────────────────────
def test_t01_item_crafted_wired():
    assert _grep(
        "crafting/services.py",
        r'emit_achievement_trigger\([^)]*"item_crafted"',
    ), "item_crafted not wired in crafting.craft_recipe"


# ── 2. market_purchase + 3. auction_purchase + 4. auction_sale +
# ── 9. material_purchased — all in buy_listing
def test_t02_market_purchase_wired():
    assert _grep("market/services.py",
                 r'emit_achievement_trigger\([^)]*"market_purchase"')


def test_t03_auction_purchase_wired():
    assert _grep("market/services.py",
                 r'emit_achievement_trigger\([^)]*"auction_purchase"')


def test_t04_auction_sale_wired_seller_side():
    src = (REPO_BACKEND / "market/services.py").read_text()
    # Must fire only when the listing fully closes (seller view) and the
    # guild_id passed to the emitter MUST be the seller_guild_id (not
    # the buyer). The payload identifies the counter-party (buyer).
    assert "flips_to_sold" in src and '"auction_sale"' in src
    assert re.search(
        r'emit_achievement_trigger\(\s*db,\s*listing\["seller_guild_id"\],\s*"auction_sale"',
        src,
    ), "auction_sale must target listing['seller_guild_id'] as guild_id"
    assert re.search(
        r'"auction_sale"[\s\S]{0,400}?buyer_guild_id', src
    ), "auction_sale payload must include buyer_guild_id"


def test_t09_material_purchased_wired():
    src = (REPO_BACKEND / "market/services.py").read_text()
    assert "material_purchased" in src
    assert "is_material" in src, (
        "material_purchased should gate on listing item_type == 'material'")


# ── 5. consortium_joined ─────────────────────────────────────────────
def test_t05_consortium_joined_wired():
    assert _grep(
        "consortiums/services.py",
        r'emit_achievement_trigger\([^)]*"consortium_joined"',
    )


# ── 6. season_league_reached ─────────────────────────────────────────
def test_t06_season_league_reached_wired():
    src = (REPO_BACKEND / "pvp/services.py").read_text()
    assert '"season_league_reached"' in src
    # Must fire when highest_league actually advanced.
    assert "highest_league" in src


# ── 7. leaderboard_rank_reached ─ DEFERRED ───────────────────────────
@pytest.mark.skip(
    reason="DEFERRED: leaderboard ranks are computed on-demand "
           "(no per-guild update hook in current architecture). "
           "Will be wired in Round 16.A Phase 2 if a rank-cache is added."
)
def test_t07_leaderboard_rank_reached_wired():
    """Placeholder — see deferred reason."""


# ── 8. item_disenchanted ─────────────────────────────────────────────
def test_t08_item_disenchanted_wired():
    assert _grep(
        "forge/services.py",
        r'emit_achievement_trigger\([^)]*"item_disenchanted"',
    )


# ── 10. pvp_match_completed ──────────────────────────────────────────
def test_t10_pvp_match_completed_wired_both_sides():
    src = (REPO_BACKEND / "pvp/services.py").read_text()
    # Must fire for both attacker and defender, with `outcome` in payload.
    occurrences = src.count('"pvp_match_completed"')
    assert occurrences >= 2, (
        f"pvp_match_completed should fire twice (att+def), found {occurrences}")
    assert '"outcome"' in src and ("att_outcome" in src or "outcome" in src)


# ── 11. territory_upgraded ───────────────────────────────────────────
def test_t11_territory_upgraded_wired():
    assert _grep(
        "territory/services.py",
        r'emit_achievement_trigger\([^)]*"territory_upgraded"',
    )


# ── E2E behavioural smoke: item_crafted actually emits ───────────────
# We use the tester guild + an existing recipe. We don't require an
# achievement unlock — we only need to verify the trigger_emissions row
# was inserted (when an idempotency_key is present) OR that the engine
# was invoked (audit `item_crafted` row already proves business path).
def test_emitter_logs_actual_event_via_known_recipe(
        auth_headers, tester_guild_id):
    """Best-effort: ensure the emitter writes a `trigger_emissions`
    row when called with idempotency_key. We invoke it directly with the
    real motor DB handle so we don't depend on having craftable
    materials on the tester guild."""
    import asyncio
    from app.core.database import db as motor_db
    from app.achievements.trigger_emitter import emit_achievement_trigger

    key = f"r16A-test-{uuid.uuid4()}"

    async def _run():
        await emit_achievement_trigger(
            motor_db, tester_guild_id, "item_crafted",
            {"item_slug": "iron_dagger", "rarity": "Common"},
            idempotency_key=key,
        )
        # Second call with same key — must be tolerated (upsert).
        await emit_achievement_trigger(
            motor_db, tester_guild_id, "item_crafted",
            {"item_slug": "iron_dagger", "rarity": "Common"},
            idempotency_key=key,
        )
        row = await motor_db.trigger_emissions.find_one(
            {"idempotency_key": key})
        return row

    row = asyncio.get_event_loop().run_until_complete(_run())
    assert row is not None, "trigger_emissions row was not created"
    assert row["event_name"] == "item_crafted"
    assert row["guild_id"] == tester_guild_id


# ── R16.1 regression smoke — bundled here to catch obvious breakage ──
def test_r161_regression_dashboard_endpoints_still_healthy(auth_headers):
    for ep in ("suggestions", "onboarding", "daily-loop"):
        r = requests.get(f"{API_BASE}/api/dashboard/{ep}",
                         headers=auth_headers, timeout=10)
        assert r.status_code == 200, f"/api/dashboard/{ep} → {r.status_code}"
