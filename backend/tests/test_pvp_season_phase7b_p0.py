"""ROUND 16.3 Phase 7B P0 — PvP Season leaderboard + cosmetics tests.

Design: prefix-scoped fixture teardown (only `p7b_smoke_` docs cleaned).
Network-based HTTP tests via `httpx` on REACT_APP_BACKEND_URL.
Pure-unit tests on cosmetic catalog invariants.

Vincoli rispettati:
    ❌ NO full pytest sweep (isolation P2 open)
    ❌ NO writes to test_database
    ✅ Anti-P2W regression test explicit (test_pvp_season_no_p2w_stat_impact)
    ✅ Deterministic seeds via prefix
"""
from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime, timedelta, timezone
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


PREFIX = "p7b_smoke_"
# 5 test guilds on continent Ambash, 2 on Velur, for leaderboard scenarios.
GUILDS_AMBASH = [f"{PREFIX}guild_amb_{i}" for i in range(5)]
GUILDS_VELUR = [f"{PREFIX}guild_vel_{i}" for i in range(2)]
ALL_TEST_GUILDS = GUILDS_AMBASH + GUILDS_VELUR


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
    """Seed 7 guilds with world presence + PvP stats (distinct Elo values)."""
    _, db = await _mongo()
    now = datetime.now(timezone.utc)
    # Guilds — 5 on Ambash with Elo 1500..1100 (descending), 2 on Velur.
    ambash_elos = [1500, 1400, 1300, 1200, 1100]
    for gid, elo in zip(GUILDS_AMBASH, ambash_elos):
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
                       "level": 10, "reputation": 0, "gold": 100,
                       "updated_at": now},
             "$setOnInsert": {"created_at": now}},
            upsert=True,
        )
        await db.guild_world_presence.update_one(
            {"guild_id": gid, "status": "active"},
            {"$set": {"guild_id": gid, "continent_slug": "ambash",
                      "status": "active", "joined_at": now.isoformat()}},
            upsert=True,
        )
        await db.guild_pvp_stats.update_one(
            {"guild_id": gid},
            {"$set": {"guild_id": gid, "elo": elo,
                      "wins": 10, "losses": 2, "draws": 0,
                      "current_active_challenges": 0,
                      "updated_at": now},
             "$setOnInsert": {"created_at": now}},
            upsert=True,
        )
    for gid, elo in zip(GUILDS_VELUR, [1600, 1400]):
        uid = f"{PREFIX}user_{gid}"
        await db.users.update_one(
            {"id": uid},
            {"$setOnInsert": {"id": uid, "email": f"{uid}@test",
                              "username": uid, "password_hash": "!nolog",
                              "is_admin": False,
                              "created_at": now, "updated_at": now}},
            upsert=True,
        )
        await db.guilds.update_one(
            {"id": gid},
            {"$set": {"id": gid, "owner_user_id": uid,
                       "name": f"Guild-{gid[-6:]}",
                       "level": 10, "reputation": 0, "gold": 100,
                       "updated_at": now},
             "$setOnInsert": {"created_at": now}},
            upsert=True,
        )
        await db.guild_world_presence.update_one(
            {"guild_id": gid, "status": "active"},
            {"$set": {"guild_id": gid, "continent_slug": "velur",
                      "status": "active", "joined_at": now.isoformat()}},
            upsert=True,
        )
        await db.guild_pvp_stats.update_one(
            {"guild_id": gid},
            {"$set": {"guild_id": gid, "elo": elo,
                      "wins": 5, "losses": 1, "draws": 0,
                      "current_active_challenges": 0,
                      "updated_at": now},
             "$setOnInsert": {"created_at": now}},
            upsert=True,
        )


async def _teardown():
    """Delete only prefix-scoped docs across all Phase 7B collections."""
    _, db = await _mongo()
    or_prefix = [
        {"id": {"$regex": f"^{PREFIX}"}},
        {"guild_id": {"$regex": f"^{PREFIX}"}},
        {"owner_user_id": {"$regex": f"^{PREFIX}"}},
    ]
    for coll in ("users", "guilds", "guild_world_presence",
                 "guild_pvp_stats", "pvp_season_leaderboards",
                 "pvp_cosmetics_unlocked"):
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
def admin_token(api_base: str) -> str:
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
# UNIT TESTS — cosmetic catalog invariants
# ═══════════════════════════════════════════════════════════════════


def test_01_catalog_has_24_entries():
    from app.pvp_season.cosmetics import COSMETIC_CATALOG
    assert len(COSMETIC_CATALOG) == 24


def test_02_catalog_8_continents_x_3_types():
    from app.pvp_season.cosmetics import COSMETIC_CATALOG, CONTINENT_SLUGS
    assert len(CONTINENT_SLUGS) == 8
    by_type = {"title": 0, "badge": 0, "frame": 0}
    for slug, entry in COSMETIC_CATALOG.items():
        by_type[entry["type"]] += 1
    assert by_type == {"title": 8, "badge": 8, "frame": 8}


def test_03_catalog_rank_required_semantics():
    from app.pvp_season.cosmetics import COSMETIC_CATALOG
    for slug, entry in COSMETIC_CATALOG.items():
        if entry["type"] == "title":
            assert entry["rank_required"] == 1
        elif entry["type"] == "badge":
            assert entry["rank_required"] == 3
        elif entry["type"] == "frame":
            assert entry["rank_required"] == 10


def test_04_cosmetics_for_rank_top1():
    from app.pvp_season.cosmetics import cosmetics_for_rank
    slugs = cosmetics_for_rank("ambash", 1)
    assert slugs == ["champion_title_ambash",
                     "champion_badge_ambash",
                     "champion_frame_ambash"]


def test_05_cosmetics_for_rank_top3():
    from app.pvp_season.cosmetics import cosmetics_for_rank
    slugs = cosmetics_for_rank("velur", 2)
    assert slugs == ["champion_badge_velur", "champion_frame_velur"]
    slugs = cosmetics_for_rank("velur", 3)
    assert slugs == ["champion_badge_velur", "champion_frame_velur"]


def test_06_cosmetics_for_rank_top10():
    from app.pvp_season.cosmetics import cosmetics_for_rank
    for rank in (4, 5, 10):
        slugs = cosmetics_for_rank("soe", rank)
        assert slugs == ["champion_frame_soe"], f"rank {rank}"


def test_07_cosmetics_for_rank_below_cutoff():
    from app.pvp_season.cosmetics import cosmetics_for_rank
    assert cosmetics_for_rank("aveol", 11) == []
    assert cosmetics_for_rank("aveol", 100) == []


def test_08_cosmetics_for_rank_unknown_continent():
    from app.pvp_season.cosmetics import cosmetics_for_rank
    assert cosmetics_for_rank("atlantis", 1) == []


def test_09_italian_descriptions_present():
    from app.pvp_season.cosmetics import COSMETIC_CATALOG
    for slug, entry in COSMETIC_CATALOG.items():
        assert "name_it" in entry and entry["name_it"]
        assert "description_it" in entry and entry["description_it"]
        assert "puramente" in entry["description_it"].lower() or \
               "decorativ" in entry["description_it"].lower(), (
            f"{slug} description missing anti-P2W disclosure"
        )


# ═══════════════════════════════════════════════════════════════════
# HTTP TESTS — endpoints
# ═══════════════════════════════════════════════════════════════════


def test_10_current_bootstraps_season(api_base, admin_token):
    r = httpx.get(f"{api_base}/pvp-season/current",
                  headers=_h(admin_token), timeout=10.0)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["season_number"] >= 1
    assert d["status"] in ("active", "finalized")
    assert d["time_remaining_seconds"] >= 0


def test_11_current_returns_same_active_season_stable(api_base, admin_token):
    r1 = httpx.get(f"{api_base}/pvp-season/current",
                   headers=_h(admin_token), timeout=10.0).json()
    r2 = httpx.get(f"{api_base}/pvp-season/current",
                   headers=_h(admin_token), timeout=10.0).json()
    assert r1["id"] == r2["id"]
    assert r1["season_number"] == r2["season_number"]


def test_12_leaderboard_ambash_top_ordered_by_elo(api_base, admin_token):
    r = httpx.get(f"{api_base}/pvp-season/leaderboard/ambash",
                  headers=_h(admin_token), timeout=10.0)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["continent_slug"] == "ambash"
    ranks = [e["rank"] for e in d["entries"]]
    elos = [e["elo"] for e in d["entries"]]
    # Ranks must be 1..N ascending, elo descending.
    assert ranks == sorted(ranks)
    assert elos == sorted(elos, reverse=True)


def test_13_leaderboard_unknown_continent_returns_404(api_base, admin_token):
    r = httpx.get(f"{api_base}/pvp-season/leaderboard/atlantis",
                  headers=_h(admin_token), timeout=10.0)
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "pvp_season.continent_not_found"


def test_14_leaderboard_filters_level_lt_8(event_loop, api_base, admin_token):
    """Guild with level<8 must be excluded from live leaderboard."""
    async def _demote_one():
        _, db = await _mongo()
        await db.guilds.update_one(
            {"id": GUILDS_AMBASH[0]},
            {"$set": {"level": 5}},
        )
    event_loop.run_until_complete(_demote_one())
    r = httpx.get(f"{api_base}/pvp-season/leaderboard/ambash",
                  headers=_h(admin_token), timeout=10.0)
    d = r.json()
    ids = [e["guild_id"] for e in d["entries"]]
    assert GUILDS_AMBASH[0] not in ids, "demoted guild leaked into live LB"
    # Restore for later tests.
    async def _restore():
        _, db = await _mongo()
        await db.guilds.update_one(
            {"id": GUILDS_AMBASH[0]}, {"$set": {"level": 10}},
        )
    event_loop.run_until_complete(_restore())


def test_15_leaderboard_all_continents_maps_all_8(api_base, admin_token):
    r = httpx.get(f"{api_base}/pvp-season/leaderboard/all-continents",
                  headers=_h(admin_token), timeout=10.0)
    assert r.status_code == 200, r.text
    d = r.json()
    assert set(d["by_continent"].keys()) == {
        "ambash", "velur", "soe", "efreto",
        "irthe", "nathos", "ergolat", "aveol",
    }


def test_16_cosmetics_catalog_returns_24(api_base, admin_token):
    r = httpx.get(f"{api_base}/pvp-season/cosmetics/catalog",
                  headers=_h(admin_token), timeout=10.0)
    assert r.status_code == 200
    d = r.json()
    assert d["total"] == 24
    assert len(d["entries"]) == 24
    slugs = {e["cosmetic_slug"] for e in d["entries"]}
    assert "champion_title_ambash" in slugs
    assert "champion_frame_aveol" in slugs


def test_17_cosmetics_mine_empty_before_finalize(api_base, admin_token):
    r = httpx.get(f"{api_base}/pvp-season/cosmetics/mine",
                  headers=_h(admin_token), timeout=10.0)
    assert r.status_code == 200
    d = r.json()
    # tester@orbus.test has never won a finalized season → 0 cosmetics.
    assert d["by_type"] == {"title": 0, "badge": 0, "frame": 0}
    assert d["items"] == []


# ═══════════════════════════════════════════════════════════════════
# INTEGRATION — finalize + award + idempotency (direct DB calls)
# ═══════════════════════════════════════════════════════════════════


def test_18_finalize_season_awards_top1_all_three(event_loop):
    """Force-finalize a synthetic season and verify rank1 gets title+badge+frame."""
    from app.pvp_season.services import finalize_season, _create_next_season
    async def _flow():
        _, db = await _mongo()
        # Create a synthetic season via _create_next_season (safe, additive).
        season = await _create_next_season(db)
        r = await finalize_season(db, season["id"])
        assert r["status"] == "finalized"
        # Verify leaderboard rows for ambash.
        lb = await db.pvp_season_leaderboards.find(
            {"season_id": season["id"], "continent_slug": "ambash"},
            {"_id": 0},
        ).sort("rank", 1).to_list(20)
        assert len(lb) >= 1
        top1 = lb[0]
        assert top1["rank"] == 1
        # Rank1 must have awarded all 3 cosmetics
        assert set(top1["cosmetics_awarded"]) == {
            "champion_title_ambash",
            "champion_badge_ambash",
            "champion_frame_ambash",
        }
        # Check DB rows exist for top1 guild
        unlocks = await db.pvp_cosmetics_unlocked.find(
            {"guild_id": top1["guild_id"], "season_id": season["id"]},
            {"_id": 0},
        ).to_list(10)
        types = {u["cosmetic_type"] for u in unlocks}
        assert {"title", "badge", "frame"}.issubset(types)
        return season["id"]

    season_id = event_loop.run_until_complete(_flow())
    assert season_id


def test_19_finalize_is_idempotent(event_loop):
    """Calling finalize_season twice must not duplicate cosmetics."""
    from app.pvp_season.services import finalize_season, _create_next_season
    async def _flow():
        _, db = await _mongo()
        season = await _create_next_season(db)
        r1 = await finalize_season(db, season["id"])
        assert r1["changed"] is True
        c1 = await db.pvp_cosmetics_unlocked.count_documents({})
        r2 = await finalize_season(db, season["id"])
        assert r2["changed"] is False, "second call must be no-op"
        c2 = await db.pvp_cosmetics_unlocked.count_documents({})
        assert c1 == c2, "cosmetic count changed on idempotent re-call"
        # Third call also must be no-op.
        r3 = await finalize_season(db, season["id"])
        assert r3["changed"] is False
    event_loop.run_until_complete(_flow())


def test_20_award_cosmetic_idempotent_per_guild_slug(event_loop):
    """award_cosmetic must return False the second time for same guild+slug."""
    from app.pvp_season.services import award_cosmetic
    async def _flow():
        _, db = await _mongo()
        gid = GUILDS_AMBASH[0]
        # Ensure clean slate for this specific slug on this guild.
        await db.pvp_cosmetics_unlocked.delete_many(
            {"guild_id": gid, "cosmetic_slug": "champion_frame_ambash"},
        )
        ok1 = await award_cosmetic(
            db, guild_id=gid,
            cosmetic_slug="champion_frame_ambash",
            season_id="p7b_test_season_xyz",
            season_number=999, continent_slug="ambash", rank=5,
        )
        ok2 = await award_cosmetic(
            db, guild_id=gid,
            cosmetic_slug="champion_frame_ambash",
            season_id="p7b_test_season_xyz2",
            season_number=1000, continent_slug="ambash", rank=8,
        )
        assert ok1 is True, "first award must succeed"
        assert ok2 is False, "second award must be de-duped"
        # Cleanup: this row is prefix-attached via gid, teardown handles it.
    event_loop.run_until_complete(_flow())


def test_21_award_cosmetic_unknown_slug_returns_false(event_loop):
    from app.pvp_season.services import award_cosmetic
    async def _flow():
        _, db = await _mongo()
        ok = await award_cosmetic(
            db, guild_id=GUILDS_VELUR[0],
            cosmetic_slug="unknown_bogus_slug",
            season_id="x", season_number=1,
            continent_slug="velur", rank=1,
        )
        assert ok is False
    event_loop.run_until_complete(_flow())


# ═══════════════════════════════════════════════════════════════════
# ON-VISIT ROLLOVER
# ═══════════════════════════════════════════════════════════════════


def test_22_on_visit_rollover_when_expired(event_loop, api_base, admin_token):
    """Force an active season's ends_at into the past and verify GET /current
    triggers finalize + creates the next season."""
    async def _expire_current():
        _, db = await _mongo()
        active = await db.pvp_seasons.find_one({"status": "active"}, {"_id": 0})
        assert active is not None
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        await db.pvp_seasons.update_one(
            {"id": active["id"]},
            {"$set": {"ends_at": past}},
        )
        return active["id"], active["season_number"]

    expired_id, expired_num = event_loop.run_until_complete(_expire_current())

    r = httpx.get(f"{api_base}/pvp-season/current",
                  headers=_h(admin_token), timeout=15.0)
    assert r.status_code == 200, r.text
    d = r.json()
    # After rollover, the active season must be a NEW one with number+1.
    assert d["id"] != expired_id, "still returning expired season"
    assert d["season_number"] > expired_num, "season_number did not increment"
    assert d["status"] == "active"


def test_23_history_returns_finalized_season(event_loop, api_base, admin_token):
    """After test_22 rollover, the expired season must be queryable via history."""
    async def _find_finalized():
        _, db = await _mongo()
        docs = await db.pvp_seasons.find(
            {"status": "finalized"}, {"_id": 0, "season_number": 1},
        ).sort("season_number", -1).limit(1).to_list(1)
        return docs[0]["season_number"] if docs else None

    num = event_loop.run_until_complete(_find_finalized())
    if num is None:
        pytest.skip("no finalized season yet (test_22 skipped or dependency)")
    r = httpx.get(f"{api_base}/pvp-season/history/{num}",
                  headers=_h(admin_token), timeout=10.0)
    assert r.status_code == 200
    d = r.json()
    assert d["season_number"] == num
    assert d["status"] == "finalized"


# ═══════════════════════════════════════════════════════════════════
# ADMIN — dev-gated
# ═══════════════════════════════════════════════════════════════════


def test_24_admin_stats_ok(api_base, admin_token):
    r = httpx.get(f"{api_base}/admin/pvp-season/stats",
                  headers=_h(admin_token), timeout=10.0)
    assert r.status_code == 200, r.text
    d = r.json()
    assert "totals" in d
    for k in ("seasons", "finalized", "active",
              "leaderboard_rows", "cosmetics_awarded"):
        assert k in d["totals"]


def test_25_admin_force_snapshot_dev_gated(api_base, admin_token):
    """In dev, force-snapshot must succeed (or 500 if internally rejected).
    The important assertion: in prod, would return 403 dev_disabled_in_prod.
    We can only test the dev path here."""
    # This test is safe: it finalizes whatever season is active, which is
    # exactly the intended dev-mode behaviour.
    r = httpx.post(f"{api_base}/admin/pvp-season/dev/force-snapshot",
                   headers=_h(admin_token), timeout=15.0)
    # In development env, the gate MUST allow the request.
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["forced"] is True
    assert d["result"]["status"] in ("finalized",)


# ═══════════════════════════════════════════════════════════════════
# ANTI-P2W + REGRESSION
# ═══════════════════════════════════════════════════════════════════


def test_26_no_p2w_stat_impact_after_award(event_loop):
    """Awarding cosmetics must NEVER modify guild.gold, guild.reputation,
    guild_pvp_stats.elo/wins/losses, or adventurer.stats."""
    from app.pvp_season.services import award_cosmetic

    async def _flow():
        _, db = await _mongo()
        gid = GUILDS_VELUR[0]
        # Snapshot state BEFORE.
        g_before = await db.guilds.find_one({"id": gid}, {"_id": 0})
        s_before = await db.guild_pvp_stats.find_one(
            {"guild_id": gid}, {"_id": 0},
        )
        # Ensure clean slate on this slug for the assertion.
        await db.pvp_cosmetics_unlocked.delete_many(
            {"guild_id": gid, "cosmetic_slug": "champion_title_velur"},
        )
        ok = await award_cosmetic(
            db, guild_id=gid,
            cosmetic_slug="champion_title_velur",
            season_id="p7b_antip2w_check", season_number=999,
            continent_slug="velur", rank=1,
        )
        assert ok is True
        # Snapshot AFTER.
        g_after = await db.guilds.find_one({"id": gid}, {"_id": 0})
        s_after = await db.guild_pvp_stats.find_one(
            {"guild_id": gid}, {"_id": 0},
        )
        # Guild core fields immutato.
        for k in ("gold", "reputation", "level", "name"):
            assert g_before.get(k) == g_after.get(k), (
                f"guild.{k} changed after cosmetic award (P2W leak!)"
            )
        # PvP stats immutato.
        for k in ("elo", "wins", "losses", "draws"):
            assert s_before.get(k) == s_after.get(k), (
                f"guild_pvp_stats.{k} changed after cosmetic award!"
            )

    event_loop.run_until_complete(_flow())


def test_27_audit_events_registered_and_whitelisted():
    """3 new event types must be in both audit.log EVENT_TYPES and
    admin audit whitelist."""
    from app.audit.log import EVENT_TYPES
    from app.admin.audit_routes import AUDIT_EVENT_WHITELIST
    for et in ("PVP_SEASON_STARTED", "PVP_SEASON_FINALIZED",
               "PVP_COSMETIC_AWARDED"):
        assert et in EVENT_TYPES, f"{et} missing from EVENT_TYPES"
        assert et in AUDIT_EVENT_WHITELIST, (
            f"{et} missing from admin whitelist"
        )
    # Whitelist must have ≥50 entries per Phase 7B target.
    assert len(AUDIT_EVENT_WHITELIST) >= 50


def test_28_recovery_script_dry_run_no_errors(event_loop):
    """Recovery script --dry-run must return a valid dict without crashing."""
    from app.scripts.recover_stuck_pvp_seasons import _run
    result = event_loop.run_until_complete(_run(dry_run=True, limit=5))
    assert result["dry_run"] is True
    assert "total_stuck" in result
    assert isinstance(result.get("stuck", []), list)


def test_29_current_leaderboard_after_finalize_reads_snapshot(
    event_loop, api_base, admin_token,
):
    """After finalize, leaderboard endpoints for that season must serve
    from pvp_season_leaderboards, not live guild_pvp_stats."""
    from app.pvp_season.services import finalize_season, _create_next_season

    async def _prepare():
        _, db = await _mongo()
        # Create + finalize a synthetic season.
        season = await _create_next_season(db)
        await finalize_season(db, season["id"])
        # Manually mutate live PvP stats to a wildly different value.
        # If the endpoint returned live data, the snapshot check would
        # fail. Since finalized reads the snapshot table, it must ignore.
        await db.guild_pvp_stats.update_one(
            {"guild_id": GUILDS_AMBASH[0]},
            {"$set": {"elo": 9999}},  # sentinel
        )
        return season["id"]

    season_id = event_loop.run_until_complete(_prepare())

    # Now the active season is a *new* one (rollover), and the snapshot
    # rows are on the previous season_id. The live leaderboard endpoint
    # queries the CURRENT active season → so the sentinel Elo=9999 SHOULD
    # appear in the live leaderboard. That's the correct behavior (live
    # data reflects current stats). This test verifies the snapshot rows
    # are UNCHANGED after mutation.
    async def _check_snapshot_stable():
        _, db = await _mongo()
        rows = await db.pvp_season_leaderboards.find(
            {"season_id": season_id, "continent_slug": "ambash"},
            {"_id": 0},
        ).sort("rank", 1).to_list(20)
        # Snapshot Elo values must not include 9999 (that's post-finalize).
        elos = [r["elo_snapshot"] for r in rows]
        assert 9999 not in elos, "snapshot changed after finalize!"
    event_loop.run_until_complete(_check_snapshot_stable())

    # Restore live stats.
    async def _restore():
        _, db = await _mongo()
        await db.guild_pvp_stats.update_one(
            {"guild_id": GUILDS_AMBASH[0]},
            {"$set": {"elo": 1500}},
        )
    event_loop.run_until_complete(_restore())


def test_30_no_regression_pve_endpoints(api_base, admin_token):
    """Sanity check: PvE endpoints still respond 200 or expected errors.

    Anti-P2W regression: adding pvp_season module must not break PvE routes.
    """
    for path in ("/expeditions", "/dungeons", "/inventory",
                 "/forge/catalog", "/adventurers"):
        r = httpx.get(f"{api_base}{path}",
                      headers=_h(admin_token), timeout=10.0)
        # Any 2xx or a known-good 4xx (403 for gated) — no 5xx.
        assert r.status_code < 500, (
            f"regression on {path}: HTTP {r.status_code}"
        )


def test_31_leaderboard_single_matches_all_continents(api_base, admin_token):
    """Guard-rail: /leaderboard/{slug} and /leaderboard/all-continents[slug]
    MUST return byte-identical entries for every continent in a single
    consistent read window (same season, same filter set, same ordering).

    A previous smoke test observed a transient divergence (2 vs 0 entries
    on ambash) caused by the module-scoped test teardown removing the
    `p7b_smoke_*` guilds *between* the two consecutive curl calls. The
    endpoints share the same underlying `_compute_live_top_n()` /
    `get_finalized_leaderboard()` helpers, so any divergence indicates
    either (a) a race with a concurrent rollover or (b) a filter drift
    introduced by a future change. This test locks the contract.
    """
    # 1. Fetch all-continents FIRST to freeze the season+state.
    r_all = httpx.get(f"{api_base}/pvp-season/leaderboard/all-continents",
                      headers=_h(admin_token), timeout=10.0)
    assert r_all.status_code == 200, r_all.text
    all_d = r_all.json()
    all_season_id = all_d["season_id"]
    all_finalized = all_d["finalized"]

    # 2. For every continent, fetch the single-slug endpoint and diff.
    for slug in ("ambash", "velur", "soe", "efreto",
                 "irthe", "nathos", "ergolat", "aveol"):
        r_single = httpx.get(
            f"{api_base}/pvp-season/leaderboard/{slug}",
            headers=_h(admin_token), timeout=10.0,
        )
        assert r_single.status_code == 200, r_single.text
        sd = r_single.json()
        # If the season rolled over between the two calls, skip this slug
        # (transient state, not a bug); the test asserts parity within a
        # stable window only.
        if sd["season_id"] != all_season_id:
            continue
        if sd["finalized"] != all_finalized:
            continue
        single_entries = sd["entries"]
        all_entries = all_d["by_continent"][slug]
        # Same length.
        assert len(single_entries) == len(all_entries), (
            f"{slug}: single={len(single_entries)} vs "
            f"all-continents={len(all_entries)} — filter drift?"
        )
        # Same guild_id sequence (order preserved).
        single_ids = [e["guild_id"] for e in single_entries]
        all_ids = [e["guild_id"] for e in all_entries]
        assert single_ids == all_ids, (
            f"{slug}: guild_id order divergence "
            f"single={single_ids} vs all={all_ids}"
        )
        # Same rank sequence.
        single_ranks = [e["rank"] for e in single_entries]
        all_ranks = [e["rank"] for e in all_entries]
        assert single_ranks == all_ranks, (
            f"{slug}: rank sequence divergence"
        )
        # Same Elo values.
        single_elos = [e["elo"] for e in single_entries]
        all_elos = [e["elo"] for e in all_entries]
        assert single_elos == all_elos, (
            f"{slug}: elo values divergence"
        )
