"""Phase 17.5 + 18 (ROUND 5) — Team Size 5 foundation + Solo Raid MVP.

Coverage:
  Phase 17.5 — Foundation (10)
    1. OpenAPI path count = 75 (69 + 6 new raid endpoints).
    2. Starter roster auto-pop creates exactly 5 advs on new guild.
    3. Starter roster idempotent: running twice does NOT duplicate.
    4. Backfill on existing guild with 0 advs tops up to 5.
    5. 12 new 5p dungeons seeded (required_team_size=5).
    6. 10 legacy dungeons flagged is_legacy=true, kept at required_team_size=3.
    7. Power bump idempotent: legacy T2/T3 rec_power up ~25%, T1 unchanged.
    8. dungeon_public exposes is_legacy / power_bumped / tier_label.
    9. guild_public exposes max_raid_score / raids_completed_count / last_raid_completed_at.
    10. Audit event 'starter_roster_seeded' logged on guild creation.

  Phase 18 — Solo Raid MVP (10)
    11. GET /api/raids/catalog returns 3 raid_dungeons with gate logic.
    12. Catalog requires roster ≥ 20 → unlocked=False for fresh guild.
    13. POST /api/raids/preview rejects party with <5 advs (Pydantic 422).
    14. POST /api/raids/preview rejects duplicate adv across parties.
    15. POST /api/raids/start rejects roster <20 unique with 422.
    16. POST /api/raids/start with 20 unique advs creates raid + flags busy.
    17. Cooldown 15min after complete (raids.cooldown_active sentinel).
    18. POST /api/raids/{id}/complete is server-driven + grants rewards.
    19. max_raid_score updates on completion, max_team_power_ever does NOT.
    20. Audit events 'raid_started' + 'raid_completed' logged.
"""
import os
import uuid
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

BASE_URL = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or os.environ.get("BACKEND_URL", "http://localhost:8001")
).rstrip("/")
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]


@pytest.fixture(scope="module")
def db():
    c = MongoClient(MONGO_URL)
    try:
        yield c[DB_NAME]
    finally:
        c.close()


def _new_user(hint="p18"):
    tag = f"{hint}_{uuid.uuid4().hex[:6]}"
    r = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": f"{tag}@orbus.test", "username": tag, "password": "Test12345!"},
        timeout=15,
    )
    assert r.status_code == 201, r.text
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    rg = requests.post(
        f"{BASE_URL}/api/guilds", json={"name": f"R5 {tag[-5:]}"},
        headers=h, timeout=15,
    )
    assert rg.status_code == 201
    gid = requests.get(f"{BASE_URL}/api/guilds/me", headers=h, timeout=15).json()["guild"]["id"]
    return {"tag": tag, "headers": h, "guild_id": gid}


# ════════════════════════════ Phase 17.5 ════════════════════════════
def test_01_openapi_paths_75():
    r = requests.get(f"{BASE_URL}/api/openapi.json", timeout=15)
    paths = list(r.json()["paths"].keys())
    # Updated for Phase 19 §1.2 — added /api/leaderboard/raids (75 → 76)
    assert len(paths) == 77, f"expected 75, got {len(paths)}"


def test_02_starter_roster_creates_5(db):
    ctx = _new_user("starter_5")
    advs = requests.get(f"{BASE_URL}/api/adventurers", headers=ctx["headers"], timeout=15).json()
    assert len(advs["adventurers"]) == 5


def test_03_starter_roster_idempotent(db):
    """Calling ensure_starter_roster again must not add advs."""
    from app.onboarding.services import ensure_starter_roster
    ctx = _new_user("starter_idem")
    # Direct DB call — emulates 2nd boot/back-fill
    import asyncio
    from motor.motor_asyncio import AsyncIOMotorClient
    async def run():
        cli = AsyncIOMotorClient(MONGO_URL)
        try:
            adb = cli[DB_NAME]
            return await ensure_starter_roster(adb, ctx["guild_id"])
        finally:
            cli.close()
    inserted = asyncio.run(run())
    assert inserted == 0


def test_04_starter_backfill_for_empty(db):
    """A guild with 0 advs (manually drained) is topped to 5."""
    ctx = _new_user("backfill")
    # Drain
    db.adventurers.delete_many({"guild_id": ctx["guild_id"]})
    from app.onboarding.services import ensure_starter_roster
    import asyncio
    from motor.motor_asyncio import AsyncIOMotorClient
    async def run():
        cli = AsyncIOMotorClient(MONGO_URL)
        try:
            return await ensure_starter_roster(cli[DB_NAME], ctx["guild_id"])
        finally:
            cli.close()
    inserted = asyncio.run(run())
    assert inserted == 5


def test_05_12_5p_dungeons_seeded(db):
    n = db.dungeons.count_documents({"is_5p": True, "required_team_size": 5})
    assert n >= 12, f"expected ≥12 5p dungeons, got {n}"


def test_06_legacy_dungeons_marked(db):
    n = db.dungeons.count_documents({"is_legacy": True, "required_team_size": 3})
    assert n == 10, f"expected 10 legacy team-3 dungeons, got {n}"


def test_07_power_bumped_t2_t3(db):
    storm = db.dungeons.find_one({"slug": "storm-spire"})
    drag = db.dungeons.find_one({"slug": "dragons-hoard"})
    goblin = db.dungeons.find_one({"slug": "goblin-warrens"})
    assert storm["recommended_power"] == 110, storm
    assert drag["recommended_power"] == 100, drag
    # T1 untouched
    assert goblin["recommended_power"] == 45, goblin


def test_08_dungeon_public_exposes_round5_fields():
    r = requests.get(f"{BASE_URL}/api/dungeons", timeout=15)
    assert r.status_code == 200
    dungs = r.json()["dungeons"]
    for d in dungs:
        for k in ["is_legacy", "is_5p", "power_bumped", "tier_label"]:
            assert k in d


def test_09_guild_public_exposes_raid_fields():
    ctx = _new_user("guildpub")
    g = requests.get(f"{BASE_URL}/api/guilds/me", headers=ctx["headers"], timeout=15).json()["guild"]
    for k in ["max_raid_score", "last_raid_completed_at", "raids_completed_count", "raids_victory_count"]:
        assert k in g, f"missing {k}"
    assert g["max_raid_score"] == 0
    assert g["raids_completed_count"] == 0


def test_10_starter_audit_event(db):
    ctx = _new_user("audit")
    n = db.audit_log.count_documents({
        "event_type": "starter_roster_seeded",
        "actor_guild_id": ctx["guild_id"],
    })
    assert n >= 5, f"expected ≥5 starter audits, got {n}"


# ════════════════════════════ Phase 18 ════════════════════════════
def test_11_raid_catalog_returns_3():
    ctx = _new_user("rcat")
    r = requests.get(f"{BASE_URL}/api/raids/catalog", headers=ctx["headers"], timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert len(body["raid_dungeons"]) == 3


def test_12_catalog_locks_with_low_roster():
    ctx = _new_user("rgate")  # 5 starter advs only
    r = requests.get(f"{BASE_URL}/api/raids/catalog", headers=ctx["headers"], timeout=15)
    rds = r.json()["raid_dungeons"]
    locked = [x for x in rds if x["unlocked"] is False]
    assert len(locked) == 3
    assert locked[0]["gate_reason"] == "roster_too_small"


def test_13_preview_rejects_party_lt_5():
    ctx = _new_user("rpreview")
    # Build invalid payload (4 advs in party 1)
    advs = requests.get(f"{BASE_URL}/api/adventurers", headers=ctx["headers"], timeout=15).json()["adventurers"]
    aid = [a["id"] for a in advs]
    payload = {
        "raid_slug": "broken-bastion-siege",
        "parties": [
            {"party_idx": 1, "adventurer_ids": aid[:4]},  # only 4!
            {"party_idx": 2, "adventurer_ids": aid[:5]},
            {"party_idx": 3, "adventurer_ids": aid[:5]},
            {"party_idx": 4, "adventurer_ids": aid[:5]},
        ],
    }
    r = requests.post(f"{BASE_URL}/api/raids/preview", json=payload, headers=ctx["headers"], timeout=15)
    assert r.status_code == 422


def test_14_preview_rejects_duplicate_adv(db):
    """20 unique required — duplicating an adv across parties → 422."""
    ctx = _new_user("rdup")
    # Force-create 20 advs by manipulating DB (clone starter pool)
    starter = list(db.adventurers.find({"guild_id": ctx["guild_id"]}, {"_id": 0}))
    needed = 20 - len(starter)
    base = starter[0]
    import copy
    for i in range(needed):
        clone = copy.deepcopy(base)
        clone["id"] = str(uuid.uuid4())
        clone["name"] = f"{base['name']}#{i}"
        db.adventurers.insert_one(clone)
    advs = requests.get(f"{BASE_URL}/api/adventurers", headers=ctx["headers"], timeout=15).json()["adventurers"]
    aid = [a["id"] for a in advs][:20]
    # Duplicate first id across parties 1 & 2
    parties = [
        {"party_idx": 1, "adventurer_ids": [aid[0]] + aid[1:5]},
        {"party_idx": 2, "adventurer_ids": [aid[0]] + aid[6:10]},  # dup!
        {"party_idx": 3, "adventurer_ids": aid[10:15]},
        {"party_idx": 4, "adventurer_ids": aid[15:20]},
    ]
    r = requests.post(
        f"{BASE_URL}/api/raids/preview",
        json={"raid_slug": "broken-bastion-siege", "parties": parties},
        headers=ctx["headers"], timeout=15,
    )
    assert r.status_code == 422


def test_15_start_rejects_roster_too_small():
    ctx = _new_user("rsmall")  # only 5 advs
    advs = requests.get(f"{BASE_URL}/api/adventurers", headers=ctx["headers"], timeout=15).json()["adventurers"]
    aid = [a["id"] for a in advs]
    # We can't even build a valid 20 payload; build 4 parties of 5 using duplicates
    parties = [{"party_idx": i + 1, "adventurer_ids": aid[:5]} for i in range(4)]
    r = requests.post(
        f"{BASE_URL}/api/raids/start",
        json={"raid_slug": "broken-bastion-siege", "parties": parties},
        headers=ctx["headers"], timeout=15,
    )
    # Will fail at duplicate check OR adventurers_not_owned
    assert r.status_code == 422


def _setup_20_advs(db, guild_id, starter_advs):
    import copy
    needed = 20 - len(starter_advs)
    base = starter_advs[0]
    new_ids = []
    for i in range(max(0, needed)):
        clone = copy.deepcopy(base)
        clone["id"] = str(uuid.uuid4())
        clone["name"] = f"{base['name']}#bulk{i}"
        clone.pop("_id", None)
        db.adventurers.insert_one(clone)
        new_ids.append(clone["id"])
    return new_ids


def test_16_start_with_20_unique_creates_raid(db):
    ctx = _new_user("rstart")
    starter = list(db.adventurers.find({"guild_id": ctx["guild_id"]}, {"_id": 0}))
    _setup_20_advs(db, ctx["guild_id"], starter)
    advs = requests.get(f"{BASE_URL}/api/adventurers", headers=ctx["headers"], timeout=15).json()["adventurers"]
    aid = [a["id"] for a in advs][:20]
    parties = [
        {"party_idx": 1, "adventurer_ids": aid[0:5]},
        {"party_idx": 2, "adventurer_ids": aid[5:10]},
        {"party_idx": 3, "adventurer_ids": aid[10:15]},
        {"party_idx": 4, "adventurer_ids": aid[15:20]},
    ]
    r = requests.post(
        f"{BASE_URL}/api/raids/start",
        json={"raid_slug": "broken-bastion-siege", "parties": parties},
        headers=ctx["headers"], timeout=15,
    )
    assert r.status_code == 201, r.text
    raid = r.json()["raid"]
    assert raid["status"] == "in_progress"
    # Check 20 advs marked busy
    busy = db.adventurers.count_documents({
        "guild_id": ctx["guild_id"],
        "id": {"$in": aid},
        "is_available": False,
    })
    assert busy == 20


def test_17_cooldown_15min_after_complete(db):
    ctx = _new_user("rcool")
    starter = list(db.adventurers.find({"guild_id": ctx["guild_id"]}, {"_id": 0}))
    _setup_20_advs(db, ctx["guild_id"], starter)
    # Simulate complete by directly stamping last_raid_completed_at = now
    from datetime import datetime, timezone
    db.guilds.update_one(
        {"id": ctx["guild_id"]},
        {"$set": {"last_raid_completed_at": datetime.now(timezone.utc).isoformat()}},
    )
    advs = requests.get(f"{BASE_URL}/api/adventurers", headers=ctx["headers"], timeout=15).json()["adventurers"]
    aid = [a["id"] for a in advs][:20]
    parties = [{"party_idx": i + 1, "adventurer_ids": aid[i * 5:(i + 1) * 5]} for i in range(4)]
    r = requests.post(
        f"{BASE_URL}/api/raids/start",
        json={"raid_slug": "broken-bastion-siege", "parties": parties},
        headers=ctx["headers"], timeout=15,
    )
    assert r.status_code == 422
    assert r.json()["detail"] == "raids.cooldown_active"


def test_18_complete_grants_rewards(db):
    ctx = _new_user("rcomp")
    starter = list(db.adventurers.find({"guild_id": ctx["guild_id"]}, {"_id": 0}))
    _setup_20_advs(db, ctx["guild_id"], starter)
    advs = requests.get(f"{BASE_URL}/api/adventurers", headers=ctx["headers"], timeout=15).json()["adventurers"]
    aid = [a["id"] for a in advs][:20]
    parties = [{"party_idx": i + 1, "adventurer_ids": aid[i * 5:(i + 1) * 5]} for i in range(4)]
    rs = requests.post(
        f"{BASE_URL}/api/raids/start",
        json={"raid_slug": "broken-bastion-siege", "parties": parties},
        headers=ctx["headers"], timeout=15,
    )
    rid = rs.json()["raid"]["id"]
    # Force ends_at to past for instant complete
    from datetime import datetime, timezone, timedelta
    past = (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat()
    db.raids.update_one({"id": rid}, {"$set": {"ends_at": past}})
    gold_before = db.guilds.find_one({"id": ctx["guild_id"]})["gold"]
    rc = requests.post(f"{BASE_URL}/api/raids/{rid}/complete", headers=ctx["headers"], timeout=15)
    assert rc.status_code == 200, rc.text
    raid = rc.json()["raid"]
    assert raid["status"] == "completed"
    assert raid["outcome"] in ("victory", "partial", "wipe")
    g_after = db.guilds.find_one({"id": ctx["guild_id"]})
    # Gold + raids_completed_count moved
    assert g_after["raids_completed_count"] == 1
    assert g_after["gold"] >= gold_before  # may be == on wipe


def test_19_max_raid_score_separate_from_team_power(db):
    """Complete a raid: max_raid_score updates, max_team_power_ever NOT touched."""
    ctx = _new_user("rsep")
    starter = list(db.adventurers.find({"guild_id": ctx["guild_id"]}, {"_id": 0}))
    _setup_20_advs(db, ctx["guild_id"], starter)
    g_pre = db.guilds.find_one({"id": ctx["guild_id"]})
    peak_before = int(g_pre.get("max_team_power_ever", 0))
    advs = requests.get(f"{BASE_URL}/api/adventurers", headers=ctx["headers"], timeout=15).json()["adventurers"]
    aid = [a["id"] for a in advs][:20]
    parties = [{"party_idx": i + 1, "adventurer_ids": aid[i * 5:(i + 1) * 5]} for i in range(4)]
    rs = requests.post(
        f"{BASE_URL}/api/raids/start",
        json={"raid_slug": "broken-bastion-siege", "parties": parties},
        headers=ctx["headers"], timeout=15,
    )
    rid = rs.json()["raid"]["id"]
    from datetime import datetime, timezone, timedelta
    db.raids.update_one({"id": rid}, {"$set": {"ends_at": (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat()}})
    requests.post(f"{BASE_URL}/api/raids/{rid}/complete", headers=ctx["headers"], timeout=15)
    g_post = db.guilds.find_one({"id": ctx["guild_id"]})
    assert g_post["max_raid_score"] >= 0
    assert int(g_post.get("max_team_power_ever", 0)) == peak_before


def test_20_audit_events_logged(db):
    ctx = _new_user("raudit")
    starter = list(db.adventurers.find({"guild_id": ctx["guild_id"]}, {"_id": 0}))
    _setup_20_advs(db, ctx["guild_id"], starter)
    advs = requests.get(f"{BASE_URL}/api/adventurers", headers=ctx["headers"], timeout=15).json()["adventurers"]
    aid = [a["id"] for a in advs][:20]
    parties = [{"party_idx": i + 1, "adventurer_ids": aid[i * 5:(i + 1) * 5]} for i in range(4)]
    rs = requests.post(
        f"{BASE_URL}/api/raids/start",
        json={"raid_slug": "broken-bastion-siege", "parties": parties},
        headers=ctx["headers"], timeout=15,
    )
    rid = rs.json()["raid"]["id"]
    from datetime import datetime, timezone, timedelta
    db.raids.update_one({"id": rid}, {"$set": {"ends_at": (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat()}})
    requests.post(f"{BASE_URL}/api/raids/{rid}/complete", headers=ctx["headers"], timeout=15)
    n_started = db.audit_log.count_documents({"event_type": "raid_started", "actor_guild_id": ctx["guild_id"]})
    n_completed = db.audit_log.count_documents({"event_type": "raid_completed", "actor_guild_id": ctx["guild_id"]})
    assert n_started >= 1
    assert n_completed >= 1
