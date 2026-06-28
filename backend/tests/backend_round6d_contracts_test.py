"""ROUND 6D — Contracts (daily/weekly/milestones) + signature visibility.

Covers:

  • /api/contracts/{daily,weekly,milestones} read shape + locked gating
  • lazy reset semantics (UTC midnight, ISO Monday)
  • atomic claim (CAS — no double claim, no premature claim)
  • progress fan-out hook on business writes (expeditions, market, crafting,
    territory upgrade, recruitment, specialization)
  • milestone progressive tier unlock
  • reward magnitudes within Round 6D Q5=a bounds
  • audit log emission
  • signature item visibility (Round 6C WARN P2) — `/api/inventory` returns
    the bound signature item with a populated `item.name` after the boot
    seed runs.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")


@pytest.fixture(scope="module")
def db():
    cli = MongoClient(MONGO_URL)
    yield cli[DB_NAME]
    cli.close()


def _fresh_guild(db, *, prefix: str = "r6d", gold: int = 50_000):
    tag = f"{prefix}_{uuid.uuid4().hex[:8]}"
    email = f"{tag}@orbus.test"
    requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": email, "username": tag, "password": "Test12345!",
    }, timeout=15)
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": email, "password": "Test12345!",
    }, timeout=15)
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    requests.post(
        f"{BASE_URL}/api/guilds", json={"name": f"6D {tag[-6:]}"},
        headers=h, timeout=15,
    )
    g = requests.get(f"{BASE_URL}/api/guilds/me", headers=h, timeout=15).json()["guild"]
    db.users.update_one({"email": email}, {"$set": {"is_test_user": True}})
    db.guilds.update_one({"id": g["id"]}, {"$set": {"gold": gold}})
    return h, g["id"], email


def _unlock_contract_board(db, guild_id, headers, level: int = 1) -> None:
    """Force-unlock the Contract Board structure (bypass purchase cost)."""
    requests.get(f"{BASE_URL}/api/territory", headers=headers, timeout=15)
    db.guild_structures.update_one(
        {"guild_id": guild_id},
        {"$set": {
            "structures.contract_board.is_unlocked": True,
            "structures.contract_board.level": level,
        }},
    )


def _force_complete_daily(db, guild_id, slug: str) -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    db.guilds.update_one(
        {"id": guild_id},
        {"$set": {
            "daily_contract_state.window_start_utc": today,
            f"daily_contract_state.contracts.{slug}.progress": 999,
            f"daily_contract_state.contracts.{slug}.claimed": False,
        }},
    )


def _force_complete_weekly(db, guild_id, slug: str) -> None:
    db.guilds.update_one(
        {"id": guild_id},
        {"$set": {
            f"weekly_contract_state.contracts.{slug}.progress": 999,
            f"weekly_contract_state.contracts.{slug}.claimed": False,
        }},
    )


# ─── 1+2. Lazy reset generates lists on first read ──────────────────────


def test_daily_contracts_generated_on_first_get(db):
    h, gid, _ = _fresh_guild(db)
    _unlock_contract_board(db, gid, h)
    r = requests.get(f"{BASE_URL}/api/contracts/daily", headers=h, timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert body["locked"] is False
    assert body["contract_board_level"] >= 1
    assert len(body["contracts"]) == 3
    slugs = [c["slug"] for c in body["contracts"]]
    assert "daily_complete_expedition_1" in slugs


def test_weekly_contracts_generated_on_first_get(db):
    h, gid, _ = _fresh_guild(db)
    _unlock_contract_board(db, gid, h)
    r = requests.get(f"{BASE_URL}/api/contracts/weekly", headers=h, timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert body["locked"] is False
    assert len(body["contracts"]) == 4
    assert "rotation_week" in body


# ─── 3. Producer hook increments progress on business write ─────────────


def test_progress_increment_on_specialization_applied(db):
    """ROUND 6C↔6D synergy — applying a spec ticks the weekly contract."""
    from app.training.catalog import SPEC_BY_SLUG  # noqa: F401  (existence check)
    h, gid, _ = _fresh_guild(db)
    _unlock_contract_board(db, gid, h)
    # Force training_grounds Lv1 too (needed by /api/training/specialize)
    db.guild_structures.update_one(
        {"guild_id": gid},
        {"$set": {
            "structures.training_grounds.is_unlocked": True,
            "structures.training_grounds.level": 1,
        }},
    )
    # Generate weekly state with the apply-spec contract active under the
    # CURRENT ISO week (so `increment_contract_progress`'s CAS filter on
    # `rotation_week == current` matches and the $inc actually applies).
    iso_year, iso_week, _ = datetime.now(timezone.utc).isocalendar()
    current_week_key = f"{iso_year}-W{iso_week:02d}"
    db.guilds.update_one(
        {"id": gid},
        {"$set": {
            "weekly_contract_state.rotation_week": current_week_key,
            "weekly_contract_state.active_slugs": ["weekly_apply_specialization_1"],
            "weekly_contract_state.contracts": {
                "weekly_apply_specialization_1": {
                    "progress": 0, "claimed": False, "claimed_at": None,
                    "completed_at": None,
                },
            },
        }},
    )
    # Seed an eligible adv.
    cls = db.adventurer_classes.find_one({"slug": "warrior"}, {"_id": 0, "id": 1})
    adv_id = str(uuid.uuid4())
    db.adventurers.insert_one({
        "id": adv_id, "guild_id": gid, "name": "WeeklyHookAdv",
        "adventurer_class_id": cls["id"], "class_name": "Warrior",
        "class_role": "Tank", "rarity": "Common", "level": 5,
        "experience": 0, "strength": 10, "agility": 10, "intellect": 10,
        "endurance": 10, "faith": 10, "stamina": 100, "morale": 100,
        "is_available": True, "is_retired": False, "traits": [],
        "is_starter": False, "is_test_seed": True,
        "created_at": "2026-06-28T07:00:00+00:00",
        "updated_at": "2026-06-28T07:00:00+00:00",
    })
    r = requests.post(
        f"{BASE_URL}/api/training/specialize/{adv_id}",
        json={"spec_slug": "spec_difensore"}, headers=h, timeout=15,
    )
    assert r.status_code == 200, r.text
    state = db.guilds.find_one({"id": gid}, {"_id": 0, "weekly_contract_state": 1})
    progress = state["weekly_contract_state"]["contracts"]["weekly_apply_specialization_1"]["progress"]
    assert progress >= 1, "specialization apply must tick the weekly contract"


# ─── 4+5. Atomic claim (CAS) ────────────────────────────────────────────


def test_claim_blocked_when_not_completed(db):
    h, gid, _ = _fresh_guild(db)
    _unlock_contract_board(db, gid, h)
    requests.get(f"{BASE_URL}/api/contracts/daily", headers=h, timeout=15)
    r = requests.post(
        f"{BASE_URL}/api/contracts/daily/daily_complete_expedition_1/claim",
        headers=h, timeout=15,
    )
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "contracts.not_claimable"


def test_claim_idempotent_second_call_blocked(db):
    h, gid, _ = _fresh_guild(db)
    _unlock_contract_board(db, gid, h)
    requests.get(f"{BASE_URL}/api/contracts/daily", headers=h, timeout=15)
    _force_complete_daily(db, gid, "daily_craft_item_1")
    r1 = requests.post(
        f"{BASE_URL}/api/contracts/daily/daily_craft_item_1/claim",
        headers=h, timeout=15,
    )
    assert r1.status_code == 200
    # second claim is a no-op (idempotent)
    r2 = requests.post(
        f"{BASE_URL}/api/contracts/daily/daily_craft_item_1/claim",
        headers=h, timeout=15,
    )
    assert r2.status_code == 422
    assert r2.json()["detail"]["code"] == "contracts.not_claimable"


# ─── 6+7. Reset semantics ────────────────────────────────────────────────


def test_daily_reset_when_window_changes(db):
    h, gid, _ = _fresh_guild(db)
    _unlock_contract_board(db, gid, h)
    requests.get(f"{BASE_URL}/api/contracts/daily", headers=h, timeout=15)
    # Simulate yesterday's window by writing a stale `window_start_utc`.
    db.guilds.update_one(
        {"id": gid},
        {"$set": {
            "daily_contract_state.window_start_utc": "2020-01-01",
            "daily_contract_state.contracts.daily_craft_item_1.progress": 99,
        }},
    )
    r = requests.get(f"{BASE_URL}/api/contracts/daily", headers=h, timeout=15)
    body = r.json()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    assert body["window_start_utc"] == today
    craft = next(c for c in body["contracts"] if c["slug"] == "daily_craft_item_1")
    assert craft["progress"] == 0  # rotation wiped progress


def test_weekly_reset_when_rotation_changes(db):
    h, gid, _ = _fresh_guild(db)
    _unlock_contract_board(db, gid, h)
    requests.get(f"{BASE_URL}/api/contracts/weekly", headers=h, timeout=15)
    db.guilds.update_one(
        {"id": gid},
        {"$set": {
            "weekly_contract_state.rotation_week": "1970-W01",
        }},
    )
    r = requests.get(f"{BASE_URL}/api/contracts/weekly", headers=h, timeout=15)
    body = r.json()
    assert body["rotation_week"] != "1970-W01"


# ─── 8+9. Milestone persistence + tier unlock ──────────────────────────


def test_milestone_progress_persistent_across_resets(db):
    h, gid, _ = _fresh_guild(db)
    _unlock_contract_board(db, gid, h)
    requests.get(f"{BASE_URL}/api/contracts/milestones", headers=h, timeout=15)
    db.guilds.update_one(
        {"id": gid},
        {"$set": {
            "guild_milestone_state.milestones.milestone_run_10_expeditions.progress": 7,
        }},
    )
    # Force a daily reset — milestone progress must survive.
    db.guilds.update_one(
        {"id": gid},
        {"$set": {"daily_contract_state.window_start_utc": "2020-01-01"}},
    )
    requests.get(f"{BASE_URL}/api/contracts/daily", headers=h, timeout=15)
    r = requests.get(f"{BASE_URL}/api/contracts/milestones", headers=h, timeout=15)
    ms = {m["slug"]: m for m in r.json()["milestones"]}
    assert ms["milestone_run_10_expeditions"]["progress"] == 7


def test_milestone_tier_2_locked_until_tier_1_claimed(db):
    h, gid, _ = _fresh_guild(db)
    _unlock_contract_board(db, gid, h)
    r = requests.get(f"{BASE_URL}/api/contracts/milestones", headers=h, timeout=15)
    body = r.json()
    # Tier 2 must be locked because no Tier 1 milestone has been claimed yet.
    assert body["tiers"]["2"] is False
    # Every Tier 1 milestone must report `tier_unlocked: True`.
    for m in body["milestones"]:
        if m["tier"] == 1:
            assert m["tier_unlocked"] is True


# ─── 10+11. Reward bounds / no-P2W invariants ──────────────────────────


def test_reward_magnitudes_within_round6d_bounds(db):  # noqa: ARG001
    from app.contracts.catalog import (
        DAILY_CONTRACTS, MILESTONES_TIER_1, REPUTATION_DAILY_MAX,
        WEEKLY_CONTRACT_POOL,
    )
    for c in DAILY_CONTRACTS:
        assert c["reward_gold"] <= 80, f"{c['slug']} > 80g daily ceiling"
        assert c["reward_reputation"] == REPUTATION_DAILY_MAX
    for c in WEEKLY_CONTRACT_POOL:
        assert 150 <= c["reward_gold"] <= 300, f"{c['slug']} outside 150-300g weekly band"
        assert 0 <= c["reward_reputation"] <= 3
    for m in MILESTONES_TIER_1:
        assert 100 <= m["reward_gold"] <= 200
        assert m["reward_reputation"] == 5


def test_no_p2w_no_premium_in_reward_materials(db):  # noqa: ARG001
    from app.contracts.catalog import (
        DAILY_CONTRACTS, MILESTONES_ALL, WEEKLY_CONTRACT_POOL,
    )
    forbidden_substrings = ("premium", "gem", "real_money", "boost")
    for c in (*DAILY_CONTRACTS, *WEEKLY_CONTRACT_POOL, *MILESTONES_ALL):
        for mat in c.get("reward_materials") or []:
            slug = (mat.get("slug") or "").lower()
            for bad in forbidden_substrings:
                assert bad not in slug, (
                    f"{c['slug']} grants forbidden material {slug!r}"
                )


# ─── 12. Test users excluded from public chronicle ─────────────────────


def test_claim_by_test_user_not_in_public_chronicle(db):
    h, gid, _ = _fresh_guild(db)
    _unlock_contract_board(db, gid, h)
    requests.get(f"{BASE_URL}/api/contracts/daily", headers=h, timeout=15)
    _force_complete_daily(db, gid, "daily_craft_item_1")
    requests.post(
        f"{BASE_URL}/api/contracts/daily/daily_craft_item_1/claim",
        headers=h, timeout=15,
    )
    # Public chronicle (without auth) MUST not list this test-user event.
    r = requests.get(f"{BASE_URL}/api/chronicle?limit=50", timeout=15)
    events = r.json().get("events") if isinstance(r.json(), dict) else r.json()
    if events:
        for ev in events:
            assert ev.get("actor_guild_id") != gid, (
                "test-user contract claim leaked to public chronicle"
            )


# ─── 13+14. Audit log emission ────────────────────────────────────────


def test_audit_log_on_daily_claim(db):
    h, gid, _ = _fresh_guild(db)
    _unlock_contract_board(db, gid, h)
    requests.get(f"{BASE_URL}/api/contracts/daily", headers=h, timeout=15)
    _force_complete_daily(db, gid, "daily_complete_expedition_1")
    r = requests.post(
        f"{BASE_URL}/api/contracts/daily/daily_complete_expedition_1/claim",
        headers=h, timeout=15,
    )
    assert r.status_code == 200
    audit = db.audit_log.find_one({
        "event_type": "contract_claimed",
        "actor_guild_id": gid,
        "metadata.slug": "daily_complete_expedition_1",
    })
    assert audit is not None
    assert audit["metadata"]["scope"] == "daily"


def test_audit_log_on_milestone_completion(db):
    h, gid, _ = _fresh_guild(db)
    _unlock_contract_board(db, gid, h)
    requests.get(f"{BASE_URL}/api/contracts/milestones", headers=h, timeout=15)
    # Direct DB tickle of milestone progress over threshold then call the
    # increment hook to trigger the `completed_at` stamping + audit emit.
    from app.contracts.services import increment_contract_progress  # noqa: PLC0415
    import asyncio
    db.guilds.update_one(
        {"id": gid},
        {"$set": {
            "guild_milestone_state.milestones.milestone_recruit_5_adventurers.progress": 4,
        }},
    )
    asyncio.run(_async_increment(gid))
    audit = db.audit_log.find_one({
        "event_type": "guild_milestone_reached",
        "actor_guild_id": gid,
        "metadata.slug": "milestone_recruit_5_adventurers",
    })
    assert audit is not None


async def _async_increment(gid: str) -> None:
    """Async wrapper so we can invoke the increment hook from sync tests."""
    from app.contracts.services import increment_contract_progress
    from app.core.database import db as motor_db
    await increment_contract_progress(motor_db, gid, "recruits_added", 1)


# ─── 15. Weekly apply_specialization synergy already covered by test #3.

# ─── EXTRA — Round 6C WARN P2: signature visibility ───────────────────


def test_signature_template_seeded_in_items_catalog(db):
    """Every signature catalog entry must be upserted into `db.items`
    with a populated `name` (required by `item_public`)."""
    from app.training.catalog import SPEC_SIGNATURE_ITEMS
    for slug in SPEC_SIGNATURE_ITEMS:
        row = db.items.find_one({"id": slug}, {"_id": 0, "name": 1, "is_signature": 1})
        assert row is not None, f"missing template for {slug!r}"
        assert row.get("name"), f"{slug!r} has no `name`"
        assert row.get("is_signature") is True


def test_specialized_adventurer_signature_visible_in_inventory(db):
    """End-to-end: apply spec → signature item appears in /api/inventory
    with a populated `item.name` and the correct `bound_to_adventurer_id`.
    """
    h, gid, _ = _fresh_guild(db)
    _unlock_contract_board(db, gid, h)
    db.guild_structures.update_one(
        {"guild_id": gid},
        {"$set": {
            "structures.training_grounds.is_unlocked": True,
            "structures.training_grounds.level": 1,
        }},
    )
    cls = db.adventurer_classes.find_one({"slug": "warrior"}, {"_id": 0, "id": 1})
    adv_id = str(uuid.uuid4())
    db.adventurers.insert_one({
        "id": adv_id, "guild_id": gid, "name": "SigVisAdv",
        "adventurer_class_id": cls["id"], "class_name": "Warrior",
        "class_role": "Tank", "rarity": "Common", "level": 5,
        "experience": 0, "strength": 10, "agility": 10, "intellect": 10,
        "endurance": 10, "faith": 10, "stamina": 100, "morale": 100,
        "is_available": True, "is_retired": False, "traits": [],
        "is_starter": False, "is_test_seed": True,
        "created_at": "2026-06-28T07:00:00+00:00",
        "updated_at": "2026-06-28T07:00:00+00:00",
    })
    rspec = requests.post(
        f"{BASE_URL}/api/training/specialize/{adv_id}",
        json={"spec_slug": "spec_difensore"}, headers=h, timeout=15,
    )
    assert rspec.status_code == 200
    sig_id = rspec.json()["signature_item"]["id"]
    inv = requests.get(f"{BASE_URL}/api/inventory", headers=h, timeout=15).json()
    sig_rows = [r for r in inv["inventory"]
                if r.get("bound_reason") == "specialization_signature"
                and r.get("bound_to_adventurer_id") == adv_id]
    assert len(sig_rows) == 1
    row = sig_rows[0]
    assert row["id"] == sig_id
    assert (row.get("item") or {}).get("name"), "item.name must be populated"
    assert (row.get("item") or {}).get("rarity") == "Rare"
