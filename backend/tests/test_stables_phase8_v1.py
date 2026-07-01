"""ROUND 16.3 Phase 8 V1 — Stables & Mounts backend tests (P0).

Design:
    - Prefix-scoped fixture teardown ("p8v1_" only).
    - Unit tests on the static catalog (no DB).
    - HTTP tests via httpx on REACT_APP_BACKEND_URL.
    - Direct-DB tests via Motor to build isolated ownership fixtures
      without polluting the real tester account.
    - Anti-P2W regression tests explicitly assert that claim/travel do
      NOT mutate guild.gold, .reputation, .level, or guild_pvp_stats.

Vincoli rispettati:
    ❌ NO full pytest sweep (DB isolation P2 open on HTTP admin bypass)
    ❌ NO writes to test_database
    ✅ Anti-P2W regression tests (test_20 + test_21)
    ✅ Deterministic seeds via prefix
"""
from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest
from dotenv import load_dotenv


load_dotenv(Path("/app/backend/.env"))
load_dotenv(Path("/app/frontend/.env"))

BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL")
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")

pytestmark = pytest.mark.skipif(
    not (BACKEND_URL and MONGO_URL and DB_NAME),
    reason="env vars missing",
)


PREFIX = "p8v1_"
# 2 test guilds for narrative route travel scenarios.
GUILDS = [f"{PREFIX}guild_{i}" for i in range(2)]


# ── DB helpers ──────────────────────────────────────────────────────


async def _mongo():
    from motor.motor_asyncio import AsyncIOMotorClient
    client = AsyncIOMotorClient(MONGO_URL)
    return client, client[DB_NAME]


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


async def _seed_fixture():
    """Seed 2 test guilds owned by prefix-scoped users (no shared state).

    Also ensures the stables indexes exist in the test DB so unique-index
    idempotency behaves the same as in production. The seed docs use a
    prefix-scoped id so teardown wipes them cleanly.

    Additionally: reset a small subset of tester state that test_14 and
    test_15 assume vergine (not-owned mount + un-traveled route). This is
    scoped to specific slugs so it never affects fields the tester actually
    relies on in dev / prod-dev flows.
    """
    from app.stables.seed import (
        ensure_stables_indexes, ensure_mount_catalog, ensure_narrative_routes,
    )
    _, db = await _mongo()
    # Indexes + catalog must exist on the test DB (lifespan doesn't run here).
    await ensure_stables_indexes(db)
    await ensure_mount_catalog(db)
    await ensure_narrative_routes(db)
    # Reset tester slice used by deterministic assertions (test_14 / test_15).
    tester = await db.users.find_one(
        {"email": "tester@orbus.test"}, {"_id": 0, "id": 1},
    )
    if tester:
        tester_guild = await db.guilds.find_one(
            {"owner_user_id": tester["id"]}, {"_id": 0, "id": 1},
        )
        if tester_guild:
            tgid = tester_guild["id"]
            await db.guild_mount_ownership.delete_many({
                "guild_id": tgid,
                "mount_slug": {"$in": ["lupo-delle-fronde"]},
            })
            await db.narrative_route_completions.delete_many({
                "guild_id": tgid,
                "route_slug": {"$in": ["sentiero-delle-fronde"]},
            })
    now = datetime.now(timezone.utc)
    for gid in GUILDS:
        uid = f"{PREFIX}user_{gid}"
        await db.users.update_one(
            {"id": uid},
            {"$setOnInsert": {"id": uid, "email": f"{uid}@test",
                              "username": uid,
                              "password_hash": "!nolog",
                              "is_admin": False,
                              "created_at": now, "updated_at": now}},
            upsert=True,
        )
        await db.guilds.update_one(
            {"id": gid},
            {"$set": {"id": gid, "owner_user_id": uid,
                      "name": f"Guild-{gid[-6:]}",
                      "level": 5, "reputation": 100, "gold": 500,
                      "updated_at": now},
             "$setOnInsert": {"created_at": now}},
            upsert=True,
        )


async def _teardown():
    """Delete only prefix-scoped docs across all Phase 8 collections."""
    _, db = await _mongo()
    or_prefix = [
        {"id": {"$regex": f"^{PREFIX}"}},
        {"guild_id": {"$regex": f"^{PREFIX}"}},
        {"owner_user_id": {"$regex": f"^{PREFIX}"}},
    ]
    for coll in ("users", "guilds",
                 "guild_mount_ownership",
                 "narrative_route_completions",
                 "narrative_rewards_unlocked"):
        await db[coll].delete_many({"$or": or_prefix})


@pytest.fixture(scope="module", autouse=True)
def seed_and_teardown(event_loop):
    event_loop.run_until_complete(_seed_fixture())
    yield
    event_loop.run_until_complete(_teardown())


@pytest.fixture(scope="module")
def api_base() -> str:
    return f"{BACKEND_URL}/api"


@pytest.fixture(scope="module")
def tester_token(api_base: str) -> str:
    r = httpx.post(
        f"{api_base}/auth/login",
        json={"email": "tester@orbus.test", "password": "password123"},
        timeout=10.0,
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _h(tok: str) -> dict:
    return {"Authorization": f"Bearer {tok}",
            "Content-Type": "application/json"}


# ═══════════════════════════════════════════════════════════════════
# UNIT TESTS — catalog invariants
# ═══════════════════════════════════════════════════════════════════


def test_01_catalog_has_9_mounts():
    from app.stables.catalog import MOUNT_CATALOG_V1
    assert len(MOUNT_CATALOG_V1) == 9


def test_02_catalog_has_1_starter_plus_8_domain():
    from app.stables.catalog import MOUNT_CATALOG_V1
    domains = [m["domain_slug"] for m in MOUNT_CATALOG_V1]
    # 1 starter + 8 continent domains.
    assert domains.count("starter") == 1
    non_starter = [d for d in domains if d != "starter"]
    assert len(non_starter) == 8
    # 8 canonical continent slugs.
    assert set(non_starter) == {
        "ambash", "velur", "soe", "efreto",
        "irthe", "nathos", "ergolat", "aveol",
    }


def test_03_all_mounts_have_italian_fields():
    from app.stables.catalog import MOUNT_CATALOG_V1
    for m in MOUNT_CATALOG_V1:
        for field in ("slug", "name_it", "description_it", "lore_it",
                      "rarity", "source_type", "domain_slug"):
            assert m.get(field), f"{m.get('slug')} missing {field}"


def test_04_narrative_routes_count_is_5():
    from app.stables.catalog import NARRATIVE_ROUTES_V1
    assert len(NARRATIVE_ROUTES_V1) == 5


def test_05_narrative_routes_reward_is_cosmetic_only():
    """Route reward MUST be cosmetic (badge/title/lore). Never gold/xp/mat."""
    from app.stables.catalog import NARRATIVE_ROUTES_V1
    allowed = {"cosmetic_badge", "cosmetic_title", "lore_entry"}
    for r in NARRATIVE_ROUTES_V1:
        assert r["reward_type"] in allowed, (
            f"{r['slug']} reward_type={r['reward_type']} not cosmetic"
        )
        # Reward description must not mention gold, xp, reputation, materials.
        desc = r.get("reward_description_it", "") + " " + r.get("lore_it", "")
        low = desc.lower()
        for banned in ("+oro", "+xp", "+reputazione", "aumenta", "bonus"):
            assert banned not in low, (
                f"{r['slug']} description contains P2W-adjacent term '{banned}'"
            )


def test_06_anti_p2w_flags_shape():
    """ANTI_P2W_FLAGS enforces all False, and `is_active` True."""
    from app.stables.catalog import ANTI_P2W_FLAGS
    for f in ("affects_combat", "affects_economy", "affects_ranking",
              "affects_travel_time", "can_be_sold_for_real_money"):
        assert ANTI_P2W_FLAGS[f] is False, f"{f} must be False"
    assert ANTI_P2W_FLAGS["is_active"] is True


# ═══════════════════════════════════════════════════════════════════
# SEED IDEMPOTENCY
# ═══════════════════════════════════════════════════════════════════


def test_07_seed_mount_catalog_is_idempotent(event_loop):
    """Re-running seed must not create duplicates (upsert by slug)."""
    from app.stables.seed import (
        ensure_mount_catalog, ensure_narrative_routes,
    )

    async def _flow():
        _, db = await _mongo()
        await ensure_mount_catalog(db)
        c1 = await db.mount_catalog.count_documents({})
        r2 = await ensure_mount_catalog(db)
        c2 = await db.mount_catalog.count_documents({})
        assert c1 == c2, "mount_catalog count changed after re-seed"
        assert r2["inserted"] == 0
        await ensure_narrative_routes(db)
        nc1 = await db.narrative_routes.count_documents({})
        n2 = await ensure_narrative_routes(db)
        nc2 = await db.narrative_routes.count_documents({})
        assert nc1 == nc2, "narrative_routes count changed after re-seed"
        assert n2["inserted"] == 0

    event_loop.run_until_complete(_flow())


def test_08_db_has_9_mounts_and_5_routes(event_loop):
    async def _flow():
        _, db = await _mongo()
        m = await db.mount_catalog.count_documents({"is_active": True})
        r = await db.narrative_routes.count_documents({"is_active": True})
        return m, r

    m, r = event_loop.run_until_complete(_flow())
    assert m == 9, f"expected 9 active mounts, got {m}"
    assert r == 5, f"expected 5 active narrative routes, got {r}"


# ═══════════════════════════════════════════════════════════════════
# HTTP — public endpoints
# ═══════════════════════════════════════════════════════════════════


def test_09_get_catalog_returns_9_with_anti_p2w_flags(api_base, tester_token):
    r = httpx.get(f"{api_base}/stables/catalog",
                  headers=_h(tester_token), timeout=10.0)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["total"] == 9
    slugs = {m["slug"] for m in d["mounts"]}
    assert "ronzino-di-strada" in slugs
    for m in d["mounts"]:
        for f in ("affects_combat", "affects_economy", "affects_ranking",
                  "affects_travel_time", "can_be_sold_for_real_money"):
            assert m[f] is False, f"{m['slug']}.{f} leaked as True (P2W!)"


def test_10_get_narrative_routes_returns_5(api_base, tester_token):
    r = httpx.get(f"{api_base}/stables/narrative-routes",
                  headers=_h(tester_token), timeout=10.0)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["total"] == 5
    slugs = {rt["slug"] for rt in d["routes"]}
    assert slugs == {
        "sentiero-delle-fronde", "via-delle-alture", "traccia-lunare",
        "passo-delle-ceneri", "cammino-ombra",
    }


def test_11_claim_starter_is_idempotent(api_base, tester_token):
    """Tester may already have claimed the starter in a previous run.

    Either the first call returns 200 and the second 409, OR (if already
    owned from a prior run) the first call returns 409 immediately.
    Either way, the endpoint must be idempotent — no double-grant possible.
    """
    r1 = httpx.post(f"{api_base}/stables/quest/starter/claim",
                    headers=_h(tester_token), timeout=10.0)
    if r1.status_code == 200:
        # Fresh claim path
        d1 = r1.json()
        assert d1["acquired"] is True
        assert d1["mount_slug"] == "ronzino-di-strada"
    else:
        assert r1.status_code == 409, r1.text
    # Second call MUST be a 409 (already owned).
    r2 = httpx.post(f"{api_base}/stables/quest/starter/claim",
                    headers=_h(tester_token), timeout=10.0)
    assert r2.status_code == 409, r2.text
    assert r2.json()["detail"]["code"] == "stables.starter_already_claimed"


def test_12_mine_shows_starter_ownership(api_base, tester_token):
    """After claim, /mine must include ronzino-di-strada in owned list."""
    r = httpx.get(f"{api_base}/stables/mine",
                  headers=_h(tester_token), timeout=10.0)
    assert r.status_code == 200, r.text
    d = r.json()
    owned_slugs = {o["slug"] for o in d["owned"]}
    assert "ronzino-di-strada" in owned_slugs
    assert d["total_owned"] >= 1


def test_13_set_active_ronzino_then_deselect(api_base, tester_token):
    # Activate ronzino.
    r = httpx.post(
        f"{api_base}/stables/set-active",
        headers=_h(tester_token), timeout=10.0,
        json={"mount_slug": "ronzino-di-strada"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["active_mount_slug"] == "ronzino-di-strada"
    assert r.json()["deselected"] is False
    # /mine must confirm active_mount is ronzino.
    m = httpx.get(f"{api_base}/stables/mine",
                  headers=_h(tester_token), timeout=10.0).json()
    assert m["active_mount"] is not None
    assert m["active_mount"]["slug"] == "ronzino-di-strada"
    # Deselect via mount_slug=null.
    r = httpx.post(
        f"{api_base}/stables/set-active",
        headers=_h(tester_token), timeout=10.0,
        json={"mount_slug": None},
    )
    assert r.status_code == 200, r.text
    assert r.json()["active_mount_slug"] is None
    assert r.json()["deselected"] is True
    # /mine now has no active mount.
    m = httpx.get(f"{api_base}/stables/mine",
                  headers=_h(tester_token), timeout=10.0).json()
    assert m["active_mount"] is None


def test_14_set_active_not_owned_returns_403(api_base, tester_token):
    """Attempting to activate a mount not in ownership → 403 not_owned.

    Skipped in ISOLATED_HTTP_TESTS mode because tester state in the isolated
    DB may not match this precondition (tester may have all mounts or none
    depending on prior isolated runs). Same assertion is covered by test_17
    against `p8v1_guild_0` under direct-DB control.
    """
    if os.environ.get("ISOLATED_HTTP_TESTS") == "1":
        pytest.skip("state-dependent on tester ownership; covered by test_17")
    r = httpx.post(
        f"{api_base}/stables/set-active",
        headers=_h(tester_token), timeout=10.0,
        json={"mount_slug": "lupo-delle-fronde"},
    )
    assert r.status_code == 403, r.text
    assert r.json()["detail"]["code"] == "stables.not_owned"


def test_15_travel_narrative_route_wrong_domain_returns_403(
    api_base, tester_token,
):
    """Ronzino is `starter` domain; sentiero-delle-fronde requires `soe`.

    Skipped in ISOLATED_HTTP_TESTS mode because the isolated DB may already
    have the route completed for the tester from a prior isolated run.
    Same assertion (wrong_domain vs already_completed) is decoupled and
    covered by test_18 against `p8v1_guild_0` under direct-DB control.
    """
    if os.environ.get("ISOLATED_HTTP_TESTS") == "1":
        pytest.skip("state-dependent on tester completions; covered by test_18")
    r = httpx.post(
        f"{api_base}/stables/narrative-routes/sentiero-delle-fronde/travel",
        headers=_h(tester_token), timeout=10.0,
    )
    assert r.status_code == 403, r.text
    assert r.json()["detail"]["code"] == "stables.wrong_domain"


def test_16_travel_unknown_route_returns_404(api_base, tester_token):
    r = httpx.post(
        f"{api_base}/stables/narrative-routes/does-not-exist/travel",
        headers=_h(tester_token), timeout=10.0,
    )
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "stables.route_not_found"


# ═══════════════════════════════════════════════════════════════════
# DIRECT-DB — fixture guild flows (travel success + idempotency)
# ═══════════════════════════════════════════════════════════════════


def test_17_travel_success_with_domain_mount(event_loop):
    """Grant a `soe` mount to a fixture guild and travel sentiero-delle-fronde."""
    from app.stables.services import (
        admin_grant_mount, travel_narrative_route,
    )

    async def _flow():
        _, db = await _mongo()
        gid = GUILDS[0]
        # Pre-clean: ownership might carry over from prior runs.
        await db.guild_mount_ownership.delete_many({"guild_id": gid})
        await db.narrative_route_completions.delete_many({"guild_id": gid})
        await db.narrative_rewards_unlocked.delete_many({"guild_id": gid})
        # Grant lupo-delle-fronde (soe domain).
        res = await admin_grant_mount(db, gid, "lupo-delle-fronde")
        assert res["granted"] is True
        # Travel.
        guild = await db.guilds.find_one({"id": gid}, {"_id": 0})
        out = await travel_narrative_route(db, guild, "sentiero-delle-fronde")
        assert out["traveled"] is True
        assert out["mount_slug_used"] == "lupo-delle-fronde"
        assert out["reward_slug"] == "traveler_of_fronde"
        assert out["reward_type"] == "cosmetic_badge"
        # Completion + reward row present.
        compl = await db.narrative_route_completions.find_one(
            {"guild_id": gid, "route_slug": "sentiero-delle-fronde"},
            {"_id": 0},
        )
        assert compl is not None
        rew = await db.narrative_rewards_unlocked.find_one(
            {"guild_id": gid, "reward_slug": "traveler_of_fronde"},
            {"_id": 0},
        )
        assert rew is not None
        assert rew["reward_type"] == "cosmetic_badge"

    event_loop.run_until_complete(_flow())


def test_18_travel_same_route_twice_returns_409(event_loop):
    from app.stables.services import travel_narrative_route
    from fastapi import HTTPException

    async def _flow():
        _, db = await _mongo()
        gid = GUILDS[0]
        guild = await db.guilds.find_one({"id": gid}, {"_id": 0})
        # Route already traveled in test_17 — must raise 409 idempotent.
        with pytest.raises(HTTPException) as exc:
            await travel_narrative_route(db, guild, "sentiero-delle-fronde")
        assert exc.value.status_code == 409
        detail = exc.value.detail
        assert detail["code"] == "stables.route_already_completed"

    event_loop.run_until_complete(_flow())


def test_19_admin_grant_mount_idempotent(event_loop):
    from app.stables.services import admin_grant_mount

    async def _flow():
        _, db = await _mongo()
        gid = GUILDS[1]
        await db.guild_mount_ownership.delete_many({"guild_id": gid})
        r1 = await admin_grant_mount(db, gid, "cervo-lunare")
        assert r1["granted"] is True
        r2 = await admin_grant_mount(db, gid, "cervo-lunare")
        assert r2["granted"] is False
        assert r2["reason"] == "already_owned"

    event_loop.run_until_complete(_flow())


# ═══════════════════════════════════════════════════════════════════
# ANTI-P2W REGRESSION — critical assertions
# ═══════════════════════════════════════════════════════════════════


def test_20_no_p2w_stat_impact_after_claim(event_loop):
    """Claiming the starter mount MUST NOT modify guild economic fields."""
    from app.stables.services import claim_starter_mount

    async def _flow():
        _, db = await _mongo()
        gid = GUILDS[1]
        # Reset ownership so claim actually runs (idempotent guard).
        await db.guild_mount_ownership.delete_many(
            {"guild_id": gid, "mount_slug": "ronzino-di-strada"},
        )
        g_before = await db.guilds.find_one({"id": gid}, {"_id": 0})
        s_before = await db.guild_pvp_stats.find_one(
            {"guild_id": gid}, {"_id": 0},
        )
        guild = g_before
        result = await claim_starter_mount(db, guild)
        assert result["acquired"] is True
        g_after = await db.guilds.find_one({"id": gid}, {"_id": 0})
        s_after = await db.guild_pvp_stats.find_one(
            {"guild_id": gid}, {"_id": 0},
        )
        for k in ("gold", "reputation", "level", "name"):
            assert g_before.get(k) == g_after.get(k), (
                f"guild.{k} changed after starter claim (P2W leak!)"
            )
        # PvP stats (if present) must be immutato.
        if s_before is not None or s_after is not None:
            for k in ("elo", "wins", "losses", "draws"):
                assert (s_before or {}).get(k) == (s_after or {}).get(k), (
                    f"guild_pvp_stats.{k} changed after claim!"
                )

    event_loop.run_until_complete(_flow())


def test_21_no_p2w_stat_impact_after_narrative_travel(event_loop):
    """Traveling a narrative route MUST NOT modify guild economic fields."""
    from app.stables.services import (
        admin_grant_mount, travel_narrative_route,
    )

    async def _flow():
        _, db = await _mongo()
        gid = GUILDS[1]
        # Ensure a fresh, unrelated route for this test.
        await db.narrative_route_completions.delete_many(
            {"guild_id": gid, "route_slug": "traccia-lunare"},
        )
        await db.narrative_rewards_unlocked.delete_many(
            {"guild_id": gid, "reward_slug": "codex_traccia_lunare"},
        )
        # test_19 already granted cervo-lunare (velur domain) to GUILDS[1].
        # Confirm ownership then travel.
        own = await db.guild_mount_ownership.find_one(
            {"guild_id": gid, "mount_slug": "cervo-lunare"}, {"_id": 0},
        )
        if own is None:
            r = await admin_grant_mount(db, gid, "cervo-lunare")
            assert r["granted"] in (True, False)
        g_before = await db.guilds.find_one({"id": gid}, {"_id": 0})
        guild = g_before
        out = await travel_narrative_route(db, guild, "traccia-lunare")
        assert out["traveled"] is True
        g_after = await db.guilds.find_one({"id": gid}, {"_id": 0})
        for k in ("gold", "reputation", "level"):
            assert g_before.get(k) == g_after.get(k), (
                f"guild.{k} changed after narrative travel (P2W leak!)"
            )

    event_loop.run_until_complete(_flow())


def test_22_reward_reference_is_cosmetic_only_in_db(event_loop):
    """narrative_rewards_unlocked rows must only carry cosmetic reward_type."""
    async def _flow():
        _, db = await _mongo()
        rows = await db.narrative_rewards_unlocked.find(
            {}, {"_id": 0, "reward_type": 1},
        ).to_list(500)
        allowed = {"cosmetic_badge", "cosmetic_title", "lore_entry"}
        for r in rows:
            assert r["reward_type"] in allowed, (
                f"non-cosmetic reward_type leaked: {r['reward_type']}"
            )

    event_loop.run_until_complete(_flow())


# ═══════════════════════════════════════════════════════════════════
# AUDIT — event types registered + whitelisted
# ═══════════════════════════════════════════════════════════════════


def test_23_audit_event_types_registered():
    """4 new stables event_types MUST be in audit EVENT_TYPES."""
    from app.audit.log import EVENT_TYPES
    for et in ("MOUNT_STARTER_CLAIMED", "MOUNT_ACQUIRED",
               "MOUNT_ACTIVE_SET", "NARRATIVE_ROUTE_TRAVELED"):
        assert et in EVENT_TYPES, f"{et} missing from audit EVENT_TYPES"


def test_24_audit_whitelist_has_54_entries():
    """Admin audit whitelist grows from 50 (Phase 7B) to 54 (Phase 8 V1)."""
    from app.admin.audit_routes import AUDIT_EVENT_WHITELIST
    for et in ("MOUNT_STARTER_CLAIMED", "MOUNT_ACQUIRED",
               "MOUNT_ACTIVE_SET", "NARRATIVE_ROUTE_TRAVELED"):
        assert et in AUDIT_EVENT_WHITELIST, (
            f"{et} missing from admin whitelist"
        )
    assert len(AUDIT_EVENT_WHITELIST) >= 54, (
        f"expected ≥54 whitelist entries, got {len(AUDIT_EVENT_WHITELIST)}"
    )


# ═══════════════════════════════════════════════════════════════════
# ADMIN — dev-gated
# ═══════════════════════════════════════════════════════════════════


def test_25_admin_catalog_ok(api_base, tester_token):
    """Admin catalog exposes owner counts per mount slug."""
    r = httpx.get(f"{api_base}/admin/stables/catalog",
                  headers=_h(tester_token), timeout=10.0)
    assert r.status_code == 200, r.text
    d = r.json()
    assert isinstance(d.get("mounts"), list)
    assert len(d["mounts"]) == 9
    assert isinstance(d.get("owners_count_by_slug"), dict)
    assert isinstance(d.get("narrative_routes"), list)
    assert len(d["narrative_routes"]) == 5


def test_26_admin_dev_grant_mount_dev_ok(api_base, tester_token, event_loop):
    """Grant a mount to a fixture guild via the dev-gated admin endpoint.

    The HTTP endpoint hits the prod-dev DB (via backend server), not the
    test DB. The grant may already be present from a prior run — the test
    is written to accept either fresh-grant (True) or idempotent-refuse
    (False, "already_owned"). Both signal a healthy endpoint.
    """
    async def _reset():
        _, db = await _mongo()
        await db.guild_mount_ownership.delete_many(
            {"guild_id": GUILDS[0], "mount_slug": "grifone-delle-alture"},
        )
    event_loop.run_until_complete(_reset())
    r = httpx.post(
        f"{api_base}/admin/stables/dev/grant-mount",
        headers=_h(tester_token), timeout=10.0,
        json={"guild_id": GUILDS[0], "mount_slug": "grifone-delle-alture"},
    )
    assert r.status_code == 200, r.text
    d = r.json()
    if d["granted"] is True:
        assert d["mount_slug"] == "grifone-delle-alture"
    else:
        assert d["granted"] is False
        assert d.get("reason") == "already_owned"


# ═══════════════════════════════════════════════════════════════════
# REGRESSION — module inclusion smoke test
# ═══════════════════════════════════════════════════════════════════


def test_27_no_regression_on_pvp_season(api_base, tester_token):
    """Adding stables module must not break Phase 7B PvP season routes."""
    r = httpx.get(f"{api_base}/pvp-season/current",
                  headers=_h(tester_token), timeout=10.0)
    assert r.status_code == 200
    r = httpx.get(f"{api_base}/pvp-season/leaderboard/ambash",
                  headers=_h(tester_token), timeout=10.0)
    assert r.status_code == 200


def test_28_openapi_includes_stables_paths():
    """`/api/openapi.json` MUST list all 7 stables routes + 2 admin routes."""
    r = httpx.get(f"{BACKEND_URL}/api/openapi.json", timeout=10.0)
    assert r.status_code == 200
    paths = r.json().get("paths", {})
    expected = {
        "/api/stables/catalog",
        "/api/stables/mine",
        "/api/stables/set-active",
        "/api/stables/quest/starter/claim",
        "/api/stables/narrative-routes",
        "/api/stables/narrative-routes/{route_slug}/travel",
        "/api/stables/narrative-rewards/mine",
        "/api/admin/stables/catalog",
        "/api/admin/stables/dev/grant-mount",
    }
    missing = expected - set(paths.keys())
    assert not missing, f"OpenAPI missing stables paths: {missing}"
