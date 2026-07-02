"""ROUND 16.5.3 — Test suite backend (P0.1 + P0.2 + P1).

Copre:
  - P0.1 raid gate visibility (min_adventurer_level + enforce con
    raid_slug nel payload d'errore)
  - P0.2 activity sweep unificato (release lazy expedition/raid/mission
    su GET /api/adventurers e /api/roster/health)
  - P1 Guild XP drip (Prestigio di Gilda) — expedition, raid,
    resource mission + cap giornaliero + idempotenza

Isolamento: `orbus_r16_test` port 8002 via `ISOLATED_HTTP_TESTS=1`.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import requests
from pymongo import MongoClient


def _api() -> str:
    return (os.environ.get("API_BASE_URL")
            or os.environ.get("REACT_APP_BACKEND_URL")
            or "http://localhost:8001")


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iso_past(seconds: int = 60) -> str:
    return (datetime.now(timezone.utc)
            - timedelta(seconds=seconds)).isoformat()


@pytest.fixture(scope="module")
def test_db():
    dbn = os.environ.get("DB_NAME", "")
    assert "test" in dbn.lower(), f"DB {dbn!r} non è test"
    c = MongoClient(os.environ["MONGO_URL"])
    yield c[dbn]
    c.close()


def _register_or_login(base: str, email: str, pwd: str,
                        username: str) -> str:
    r = requests.post(f"{base}/api/auth/register",
                      json={"email": email, "password": pwd,
                            "username": username}, timeout=10)
    if r.status_code in (200, 201):
        return r.json()["access_token"]
    r = requests.post(f"{base}/api/auth/login",
                      json={"email": email, "password": pwd}, timeout=10)
    return r.json()["access_token"]


def _ensure_guild(base: str, token: str, name: str) -> dict:
    """Ritorna la gilda dell'utente, creandola se manca."""
    h = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{base}/api/guilds/me", headers=h, timeout=10)
    if r.status_code == 200:
        return r.json()["guild"]
    r = requests.post(f"{base}/api/guilds", headers=h,
                      json={"name": name, "description": "r1653"},
                      timeout=10)
    if r.status_code in (200, 201):
        return r.json()["guild"]
    # Try again
    r = requests.get(f"{base}/api/guilds/me", headers=h, timeout=10)
    return r.json()["guild"]


@pytest.fixture(scope="module")
def user_auth(isolated_backend_url, test_db):
    """Utente standard R16.5.3 + guild dedicata."""
    base = _api()
    email = "r1653user@orbus.test"
    pwd = "R1653User!password"
    token = _register_or_login(base, email, pwd, "r1653user")
    guild = _ensure_guild(base, token,
                          f"Guild_r1653_{uuid.uuid4().hex[:6]}")
    return {"token": token, "email": email, "guild_id": guild["id"]}


def _run_async(coro):
    """Run a coroutine to completion using asyncio.run. Avoids
    dependency on pytest-asyncio (not installed in this env)."""
    import asyncio
    return asyncio.run(coro)


def _adb():
    """Fresh AsyncIOMotorClient bound to the isolated test DB.
    Caller MUST close the underlying MotorClient after use."""
    from motor.motor_asyncio import AsyncIOMotorClient
    mc = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return mc, mc[os.environ["DB_NAME"]]


def _today_utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ═════════════════════════════════════════════════════════════════════
# P0.1 — Raid level gate visibility + enforcement
# ═════════════════════════════════════════════════════════════════════

def test_P0_1_raid_catalog_exposes_min_adventurer_level(user_auth):
    """`GET /api/raids/catalog` restituisce `min_adventurer_level`
    risolto (>=1) per ciascun raid_dungeon. Tier 1 → 8, Tier 2 → 12."""
    base = _api()
    h = {"Authorization": f"Bearer {user_auth['token']}"}
    r = requests.get(f"{base}/api/raids/catalog", headers=h, timeout=10)
    assert r.status_code == 200, r.text
    catalog = r.json().get("raid_dungeons") or r.json().get("catalog") or []
    assert len(catalog) > 0, "raid_dungeons catalog vuoto — seed mancante?"
    for rd in catalog:
        mal = rd.get("min_adventurer_level")
        assert isinstance(mal, int) and mal >= 1, (
            f"raid_dungeon {rd.get('slug')} min_adventurer_level={mal} "
            "non valido (atteso int >= 1)"
        )
        # Tier-specific asserts (documented mapping: 1→8, 2→12, 3→15)
        tier = int(rd.get("tier", 1))
        if tier == 1:
            assert mal == 8, f"tier1 raid min_lvl={mal} atteso 8"
        elif tier == 2:
            assert mal == 12, f"tier2 raid min_lvl={mal} atteso 12"


# ═════════════════════════════════════════════════════════════════════
# P0.2 — Activity sweep unificato: release lazy via /api/adventurers
# ═════════════════════════════════════════════════════════════════════

def test_P0_2_get_adventurers_releases_stale_expedition_squad(
    user_auth, test_db,
):
    """Squad in un'expedition scaduta (completes_at nel passato) DEVE
    essere rilasciata su `GET /api/adventurers` senza dover aprire
    dettaglio dell'expedition.
    """
    base = _api()
    h = {"Authorization": f"Bearer {user_auth['token']}"}
    guild_id = user_auth["guild_id"]

    # Lock 3 avventurieri via DB (simuliamo dispatch)
    advs = list(test_db.adventurers.find(
        {"guild_id": guild_id}, {"_id": 0, "id": 1}
    ).limit(3))
    if len(advs) < 3:
        pytest.skip("meno di 3 adv nel roster — impossibile testare sweep")
    adv_ids = [a["id"] for a in advs]

    test_db.adventurers.update_many(
        {"id": {"$in": adv_ids}},
        {"$set": {"is_available": False,
                  "expedition_in_progress": True}},
    )
    # Serve un dungeon reale per FK
    dg = test_db.dungeons.find_one({"is_active": True}, {"_id": 0})
    if not dg:
        pytest.skip("no active dungeon seeded")

    exp_id = str(uuid.uuid4())
    test_db.expeditions.insert_one({
        "id": exp_id,
        "guild_id": guild_id,
        "dungeon_id": dg["id"],
        "status": "in_progress",
        "adventurer_ids": adv_ids,
        "team_power": 100,
        "success_chance": 90,
        "started_at": _iso_past(3600),
        "completes_at": _iso_past(60),  # 1 min fa → scaduta
        "created_at": _iso_past(3600),
        "updated_at": _iso_past(3600),
    })
    # Members
    test_db.expedition_members.insert_many([
        {"id": str(uuid.uuid4()),
         "expedition_id": exp_id,
         "adventurer_id": a["id"],
         "guild_id": guild_id,
         "name_snapshot": "T", "class_name_snapshot": "Fighter",
         "level_snapshot": 1, "power_snapshot": 30,
         "total_power_snapshot": 30,
         "equipment_snapshot": [], "equipment_power_snapshot": 0,
         "traits_snapshot": []}
        for a in advs
    ])

    # Sanity: adventurers currently unavailable
    unavail_before = test_db.adventurers.count_documents(
        {"id": {"$in": adv_ids}, "is_available": False}
    )
    assert unavail_before == 3

    # Hit GET /api/adventurers → deve triggerare sweep unificato
    r = requests.get(f"{base}/api/adventurers", headers=h, timeout=15)
    assert r.status_code == 200, r.text

    # Post-sweep: adventurers rilasciati
    avail_after = test_db.adventurers.count_documents(
        {"id": {"$in": adv_ids}, "is_available": True}
    )
    assert avail_after == 3, (
        f"Sweep non ha rilasciato tutti gli adv "
        f"(available={avail_after}/3)"
    )

    # Expedition marcata completed
    exp_final = test_db.expeditions.find_one({"id": exp_id}, {"_id": 0})
    assert exp_final["status"] == "completed", exp_final.get("status")


def test_P0_2_get_adventurers_no_release_for_active_activity(
    user_auth, test_db,
):
    """Attività NON scaduta (completes_at futuro) → adv restano
    is_available=false. Regression: lo sweep non deve pinvolvere
    expedition in corso."""
    base = _api()
    h = {"Authorization": f"Bearer {user_auth['token']}"}
    guild_id = user_auth["guild_id"]

    advs = list(test_db.adventurers.find(
        {"guild_id": guild_id, "is_available": True},
        {"_id": 0, "id": 1},
    ).limit(2))
    if len(advs) < 2:
        pytest.skip("no free adv per il regression test")
    adv_ids = [a["id"] for a in advs]

    test_db.adventurers.update_many(
        {"id": {"$in": adv_ids}},
        {"$set": {"is_available": False,
                  "expedition_in_progress": True}},
    )
    dg = test_db.dungeons.find_one({"is_active": True}, {"_id": 0})
    exp_id = str(uuid.uuid4())
    test_db.expeditions.insert_one({
        "id": exp_id,
        "guild_id": guild_id,
        "dungeon_id": dg["id"],
        "status": "in_progress",
        "adventurer_ids": adv_ids,
        "team_power": 100,
        "success_chance": 90,
        "started_at": _iso_now(),
        # Futuro: 1 ora avanti
        "completes_at": (datetime.now(timezone.utc)
                          + timedelta(hours=1)).isoformat(),
        "created_at": _iso_now(),
        "updated_at": _iso_now(),
    })

    r = requests.get(f"{base}/api/adventurers", headers=h, timeout=15)
    assert r.status_code == 200

    still_busy = test_db.adventurers.count_documents(
        {"id": {"$in": adv_ids}, "is_available": False}
    )
    assert still_busy == 2, (
        "Sweep ha rilasciato erroneamente adv su expedition attiva!"
    )
    # Cleanup
    test_db.expeditions.delete_one({"id": exp_id})
    test_db.adventurers.update_many(
        {"id": {"$in": adv_ids}},
        {"$set": {"is_available": True, "expedition_in_progress": False}},
    )


def test_P0_2_sweep_idempotent_no_double_reward(user_auth, test_db):
    """Chiamare `GET /api/adventurers` 2 volte consecutive dopo un
    expedition scaduta non deve doppiare i reward (gold guild)."""
    base = _api()
    h = {"Authorization": f"Bearer {user_auth['token']}"}
    guild_id = user_auth["guild_id"]

    advs = list(test_db.adventurers.find(
        {"guild_id": guild_id}, {"_id": 0, "id": 1}
    ).limit(3))
    if len(advs) < 3:
        pytest.skip("meno di 3 adv")
    adv_ids = [a["id"] for a in advs]
    test_db.adventurers.update_many(
        {"id": {"$in": adv_ids}},
        {"$set": {"is_available": False,
                  "expedition_in_progress": True}},
    )
    dg = test_db.dungeons.find_one({"is_active": True}, {"_id": 0})
    exp_id = str(uuid.uuid4())
    test_db.expeditions.insert_one({
        "id": exp_id,
        "guild_id": guild_id,
        "dungeon_id": dg["id"],
        "status": "in_progress",
        "adventurer_ids": adv_ids,
        "team_power": 100,
        "success_chance": 100,  # forzo success
        "started_at": _iso_past(3600),
        "completes_at": _iso_past(120),
        "created_at": _iso_past(3600),
        "updated_at": _iso_past(3600),
    })
    test_db.expedition_members.insert_many([
        {"id": str(uuid.uuid4()),
         "expedition_id": exp_id,
         "adventurer_id": a["id"], "guild_id": guild_id,
         "name_snapshot": "T", "class_name_snapshot": "Fighter",
         "level_snapshot": 1, "power_snapshot": 30,
         "total_power_snapshot": 30,
         "equipment_snapshot": [], "equipment_power_snapshot": 0,
         "traits_snapshot": []}
        for a in advs
    ])

    g_before = test_db.guilds.find_one({"id": guild_id},
                                         {"_id": 0, "gold": 1})
    gold_before = int(g_before.get("gold", 0))

    # Prima chiamata → sweep + reward
    requests.get(f"{base}/api/adventurers", headers=h, timeout=15)
    g_mid = test_db.guilds.find_one({"id": guild_id},
                                      {"_id": 0, "gold": 1})
    gold_mid = int(g_mid.get("gold", 0))
    delta_1 = gold_mid - gold_before
    assert delta_1 > 0, f"gold non aumentato dopo sweep (delta={delta_1})"

    # Seconda chiamata → NO double credit
    requests.get(f"{base}/api/adventurers", headers=h, timeout=15)
    g_after = test_db.guilds.find_one({"id": guild_id},
                                        {"_id": 0, "gold": 1})
    gold_after = int(g_after.get("gold", 0))
    delta_2 = gold_after - gold_mid
    assert delta_2 == 0, (
        f"Sweep IDEMPOTENZA VIOLATA: seconda call ha aggiunto {delta_2} gold"
    )


# ═════════════════════════════════════════════════════════════════════
# P1 — Guild XP drip (Prestigio di Gilda)
# ═════════════════════════════════════════════════════════════════════

def test_P1_expedition_success_credits_15_xp(user_auth):
    """Hook drip: expedition success → +15 XP guild."""
    from app.achievements.xp_hooks import on_expedition_completed
    guild_id = user_auth["guild_id"]

    async def _run():
        mc, adb = _adb()
        try:
            today = _today_utc_iso()
            await adb.guild_xp_daily_cap_tracker.delete_many(
                {"guild_id": guild_id, "source": "expedition_completed",
                 "date_utc_iso": today}
            )
            exp_id = f"test-exp-{uuid.uuid4()}"
            g_before = await adb.guilds.find_one(
                {"id": guild_id}, {"_id": 0, "guild_xp": 1}
            )
            xp_before = int((g_before or {}).get("guild_xp", 0) or 0)
            snap = await on_expedition_completed(
                adb, guild_id, expedition_id=exp_id, success=True,
            )
            return xp_before, snap
        finally:
            mc.close()

    xp_before, snap = _run_async(_run())
    assert snap is not None, "hook ha ritornato None (skip inatteso)"
    assert int(snap["guild_xp"]) == xp_before + 15, (
        f"guild_xp non aumentato di 15 "
        f"(before={xp_before}, after={snap['guild_xp']})"
    )


def test_P1_expedition_fail_credits_5_xp(user_auth):
    from app.achievements.xp_hooks import on_expedition_completed
    guild_id = user_auth["guild_id"]

    async def _run():
        mc, adb = _adb()
        try:
            exp_id = f"test-fail-exp-{uuid.uuid4()}"
            g_before = await adb.guilds.find_one(
                {"id": guild_id}, {"_id": 0, "guild_xp": 1}
            )
            xp_before = int((g_before or {}).get("guild_xp", 0) or 0)
            snap = await on_expedition_completed(
                adb, guild_id, expedition_id=exp_id, success=False,
            )
            return xp_before, snap
        finally:
            mc.close()

    xp_before, snap = _run_async(_run())
    assert snap is not None
    assert int(snap["guild_xp"]) == xp_before + 5


def test_P1_raid_victory_credits_80_xp(user_auth):
    from app.achievements.xp_hooks import on_raid_completed
    guild_id = user_auth["guild_id"]

    async def _run():
        mc, adb = _adb()
        try:
            today = _today_utc_iso()
            await adb.guild_xp_daily_cap_tracker.delete_many(
                {"guild_id": guild_id, "source": "raid_completed",
                 "date_utc_iso": today}
            )
            raid_id = f"test-raid-{uuid.uuid4()}"
            g_before = await adb.guilds.find_one(
                {"id": guild_id}, {"_id": 0, "guild_xp": 1}
            )
            xp_before = int((g_before or {}).get("guild_xp", 0) or 0)
            snap = await on_raid_completed(
                adb, guild_id, raid_id=raid_id, outcome="victory",
            )
            return xp_before, snap
        finally:
            mc.close()

    xp_before, snap = _run_async(_run())
    assert snap is not None
    assert int(snap["guild_xp"]) == xp_before + 80


def test_P1_resource_mission_credits_10_xp(user_auth):
    from app.achievements.xp_hooks import on_resource_mission_completed
    guild_id = user_auth["guild_id"]

    async def _run():
        mc, adb = _adb()
        try:
            today = _today_utc_iso()
            await adb.guild_xp_daily_cap_tracker.delete_many(
                {"guild_id": guild_id, "source": "resource_mission",
                 "date_utc_iso": today}
            )
            m_id = f"test-mis-{uuid.uuid4()}"
            g_before = await adb.guilds.find_one(
                {"id": guild_id}, {"_id": 0, "guild_xp": 1}
            )
            xp_before = int((g_before or {}).get("guild_xp", 0) or 0)
            snap = await on_resource_mission_completed(
                adb, guild_id, mission_id=m_id, success=True,
            )
            m2_id = f"test-mis-fail-{uuid.uuid4()}"
            snap_fail = await on_resource_mission_completed(
                adb, guild_id, mission_id=m2_id, success=False,
            )
            return xp_before, snap, snap_fail
        finally:
            mc.close()

    xp_before, snap, snap_fail = _run_async(_run())
    assert snap is not None
    assert int(snap["guild_xp"]) == xp_before + 10
    assert snap_fail is None, "resource mission fallita non deve dare XP"


def test_P1_expedition_daily_cap_8(user_auth):
    from app.achievements.xp_hooks import on_expedition_completed
    guild_id = user_auth["guild_id"]

    async def _run():
        mc, adb = _adb()
        try:
            today = _today_utc_iso()
            await adb.guild_xp_daily_cap_tracker.delete_many(
                {"guild_id": guild_id, "source": "expedition_completed",
                 "date_utc_iso": today}
            )
            credited = 0
            for i in range(9):
                eid = f"test-cap-exp-{i}-{uuid.uuid4()}"
                snap = await on_expedition_completed(
                    adb, guild_id, expedition_id=eid, success=True,
                )
                if snap is not None:
                    credited += 1
            return credited
        finally:
            mc.close()

    credited = _run_async(_run())
    assert credited == 8, (
        f"cap giornaliero violato: creditate {credited}/9 (atteso 8)"
    )


def test_P1_raid_daily_cap_1(user_auth):
    from app.achievements.xp_hooks import on_raid_completed
    guild_id = user_auth["guild_id"]

    async def _run():
        mc, adb = _adb()
        try:
            today = _today_utc_iso()
            await adb.guild_xp_daily_cap_tracker.delete_many(
                {"guild_id": guild_id, "source": "raid_completed",
                 "date_utc_iso": today}
            )
            snap1 = await on_raid_completed(
                adb, guild_id, raid_id=f"cap-r1-{uuid.uuid4()}",
                outcome="victory",
            )
            snap2 = await on_raid_completed(
                adb, guild_id, raid_id=f"cap-r2-{uuid.uuid4()}",
                outcome="victory",
            )
            return snap1, snap2
        finally:
            mc.close()

    snap1, snap2 = _run_async(_run())
    assert snap1 is not None, "prima raid deve creditare"
    assert snap2 is None, (
        f"seconda raid stessa giornata deve saturare cap (snap={snap2})"
    )


def test_P1_idempotent_same_activity_id(user_auth):
    from app.achievements.xp_hooks import on_expedition_completed
    guild_id = user_auth["guild_id"]

    async def _run():
        mc, adb = _adb()
        try:
            today = _today_utc_iso()
            await adb.guild_xp_daily_cap_tracker.delete_many(
                {"guild_id": guild_id, "source": "expedition_completed",
                 "date_utc_iso": today}
            )
            eid = f"idem-exp-{uuid.uuid4()}"
            await adb.audit_log.delete_many(
                {"event_type": "guild_xp_gained",
                 "related_entity_id": eid}
            )
            snap1 = await on_expedition_completed(
                adb, guild_id, expedition_id=eid, success=True,
            )
            snap2 = await on_expedition_completed(
                adb, guild_id, expedition_id=eid, success=True,
            )
            return snap1, snap2
        finally:
            mc.close()

    snap1, snap2 = _run_async(_run())
    assert snap1 is not None
    assert snap2 is None, (
        "stesso expedition_id ha creditato due volte "
        f"(snap2={snap2})"
    )


def test_P1_audit_event_emitted_with_source(user_auth):
    from app.achievements.xp_hooks import on_expedition_completed
    guild_id = user_auth["guild_id"]

    async def _run():
        mc, adb = _adb()
        try:
            today = _today_utc_iso()
            await adb.guild_xp_daily_cap_tracker.delete_many(
                {"guild_id": guild_id, "source": "expedition_completed",
                 "date_utc_iso": today}
            )
            eid = f"audit-exp-{uuid.uuid4()}"
            snap = await on_expedition_completed(
                adb, guild_id, expedition_id=eid, success=True,
            )
            ev = await adb.audit_log.find_one({
                "event_type": "guild_xp_gained",
                "actor_guild_id": guild_id,
                "related_entity_id": eid,
            }, {"_id": 0})
            return snap, ev
        finally:
            mc.close()

    snap, ev = _run_async(_run())
    assert snap is not None
    assert ev is not None, "audit event non emesso"
    assert ev["source"] == "expedition_completed"
    assert int(ev["metadata"]["xp_amount"]) == 15
