"""R18.Reset.1b.hotfix.v1_2 — Test suite (16 test cases).

File: /app/backend/tests/backend_round1b_hotfix_v1_2_starter_stats_test.py

Copre 16 test PM per il fix stat generation v1.2 (base_stats esatti, no
variance, doppio audit APPLIED+APPLIED_V1_2, idempotency guard
intelligente Q3).

Isolamento DB: `test_orbus_r18_hotfix_v1_2_<pid>` con drop teardown.
Zero contatto con `orbus_r16` / `orbus_r16_test` primari.
"""
from __future__ import annotations

import asyncio
import hashlib
import importlib
import json
import logging
import os
import sys
import uuid
from pathlib import Path

import pytest
from motor.motor_asyncio import AsyncIOMotorClient

_BACKEND_ROOT = Path("/app/backend")
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

apply_v1_2 = importlib.import_module(
    "app.scripts.round18_reset1b_apply_v1_2"
)

# Path sigilli 6 (preflight baseline v1_2)
_PREFLIGHT = json.load(open(
    "/app/memory/r18_reset1b_hotfix_v1_2_preflight.json"
))
SEALED_BASELINES = _PREFLIGHT

V1_2_APPLY_PATH = (
    _BACKEND_ROOT / "app/scripts/round18_reset1b_apply_v1_2.py"
)


# ─────────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────────
def _isolated_db_name() -> str:
    return f"test_orbus_r18_hotfix_v1_2_{os.getpid()}"


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def mongo_url() -> str:
    return os.environ.get("MONGO_URL", "mongodb://localhost:27017")


@pytest.fixture(scope="module")
def db(mongo_url, event_loop):
    db_name = _isolated_db_name()
    client = AsyncIOMotorClient(mongo_url)
    database = client[db_name]

    async def _setup():
        await database.inventory_items.create_index(
            [("guild_id", 1), ("item_id", 1)],
            unique=True, name="inv_guild_item_unique",
        )
        await database.items.create_index(
            [("slug", 1)], unique=True, name="items_slug_unique"
        )
        await database.items.create_index(
            [("id", 1)], unique=True, name="items_id_unique"
        )
        await database.adventurer_classes.create_index(
            [("slug", 1)], unique=True, name="cls_slug_unique"
        )

    async def _teardown():
        await client.drop_database(db_name)
        client.close()

    event_loop.run_until_complete(_setup())
    yield database
    event_loop.run_until_complete(_teardown())


@pytest.fixture
def seeded(db, event_loop):
    """Seeda DB con N guild + 11 classi safe con base_* + potion."""

    async def _apply(
        n_guilds: int = 3, skip_class: str = None,
        skip_stat_for_class: tuple = None,
    ):
        for coll in [
            "guilds", "items", "inventory_items",
            "adventurers", "audit_log", "adventurer_classes",
        ]:
            await db[coll].delete_many({})

        # Potion catalog
        potion_id = str(uuid.uuid4())
        await db.items.insert_one({
            "id": potion_id, "slug": "minor_healing_potion",
            "name": "Minor Healing Potion",
        })

        # Safe classes catalog
        base_stats = {
            "alchemist": (3, 6, 9, 6, 4),
            "bard": (3, 6, 7, 4, 5),
            "druid": (3, 5, 7, 5, 7),
            "mage": (2, 4, 10, 3, 3),
            "monk": (5, 9, 3, 6, 5),
            "paladin": (7, 3, 2, 7, 6),
            "priest": (2, 3, 6, 4, 10),
            "ranger": (5, 8, 4, 5, 3),
            "rogue": (5, 9, 3, 4, 2),
            "warlock": (4, 6, 10, 6, 6),
            "warrior": (8, 4, 2, 9, 2),
        }
        for slug, (s, a, i, e, f) in base_stats.items():
            if skip_class and slug == skip_class:
                continue
            doc = {
                "id": str(uuid.uuid4()), "slug": slug,
                "name": slug.title(), "is_active": True,
                "base_strength": s, "base_agility": a,
                "base_intellect": i, "base_endurance": e,
                "base_faith": f,
            }
            if skip_stat_for_class and slug == skip_stat_for_class[0]:
                doc.pop(f"base_{skip_stat_for_class[1]}", None)
            await db.adventurer_classes.insert_one(doc)

        # Guilds
        gids = []
        for k in range(n_guilds):
            gid = str(uuid.uuid4())
            gids.append(gid)
            await db.guilds.insert_one({
                "id": gid, "name": f"V12TestGuild_{k}",
                "gold": 0, "level": 1, "reputation": 0,
                "owner_user_id": str(uuid.uuid4()),
                "created_at": apply_v1_2._utc_iso(),
            })
        return {"guild_ids": gids, "potion_id": potion_id}

    return lambda **kwargs: event_loop.run_until_complete(_apply(**kwargs))


# ─────────────────────────────────────────────────────────────────────
# t01 — 6 sealed scripts byte-identici (SHA256)
# ─────────────────────────────────────────────────────────────────────
def test_t01_sealed_scripts_untouched():
    """Nessuno dei 6 sealed (v1.0, v1.1, 1c restore, 1c cleanup,
    staged materialize, job_freeze) deve essere modificato."""
    for rel_path, base in SEALED_BASELINES.items():
        full = _BACKEND_ROOT / rel_path
        with full.open("rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        assert digest == base["sha256"], (
            f"SEALED DRIFT: {rel_path} "
            f"attuale={digest[:16]}... baseline={base['sha256'][:16]}..."
        )


# ─────────────────────────────────────────────────────────────────────
# t02 — v1.2 esiste come sibling
# ─────────────────────────────────────────────────────────────────────
def test_t02_v1_2_exists_as_sibling():
    assert V1_2_APPLY_PATH.exists()
    src = V1_2_APPLY_PATH.read_text()
    assert "R18.Reset.1b.hotfix.v1_2" in src
    assert 'AUDIT_EVENT_APPLIED_V1_2' in src
    assert 'APPLY_VERSION = "v1.2"' in src
    assert 'STAT_STRATEGY = "base_stats_exact_no_variance"' in src


# ─────────────────────────────────────────────────────────────────────
# t03 — 11 classi safe hanno tutti base_* (verificate su fixture)
# ─────────────────────────────────────────────────────────────────────
def test_t03_all_11_safe_classes_have_base_stats(
    db, event_loop, seeded
):
    seeded(n_guilds=1)

    async def _run():
        return await apply_v1_2._preload_class_base_stats(db)

    templates = event_loop.run_until_complete(_run())
    assert len(templates) == 11
    for slug in apply_v1_2.SAFE_STARTER_SLUGS:
        assert slug in templates
        for field in apply_v1_2.REQUIRED_STAT_FIELDS:
            assert templates[slug][field] is not None
            assert isinstance(templates[slug][field], int)


# ─────────────────────────────────────────────────────────────────────
# t04 — dry-run genera roster con 5 stat sul 100% degli adv
# ─────────────────────────────────────────────────────────────────────
def test_t04_dry_run_roster_5_stats_100_percent(
    db, event_loop, seeded
):
    seeded(n_guilds=4)

    async def _run():
        templates = await apply_v1_2._preload_class_base_stats(db)
        result = await apply_v1_2._regen_starter_roster(
            db, "DRY_RUN", templates
        )
        return result

    result = event_loop.run_until_complete(_run())
    assert result["stat_strategy"] == "base_stats_exact_no_variance"
    assert result["guilds_processed"] == 4
    # In DRY_RUN nessun documento realmente scritto ma sample_adv_stats
    # deve contenere i 5 stat popolati
    sample = result["per_guild_sample"][0]["stat_sample"]
    assert sample is not None
    for stat in apply_v1_2.REQUIRED_STAT_FIELDS:
        assert stat in sample
        assert sample[stat] is not None


# ─────────────────────────────────────────────────────────────────────
# t05 — nessun adv simulato con stat missing/null
# ─────────────────────────────────────────────────────────────────────
def test_t05_no_adv_null_stat(db, event_loop, seeded):
    seeded(n_guilds=2)

    async def _run():
        templates = await apply_v1_2._preload_class_base_stats(db)
        return await apply_v1_2._regen_starter_roster(
            db, "APPLY", templates
        )

    result = event_loop.run_until_complete(_run())
    assert result["total_created"] == 10  # 2 guild × 5

    async def _check():
        null_count = 0
        async for a in db.adventurers.find({}):
            for k in apply_v1_2.REQUIRED_STAT_FIELDS:
                if a.get(k) is None:
                    null_count += 1
                    break
        return null_count

    null_count = event_loop.run_until_complete(_check())
    assert null_count == 0, (
        f"{null_count} adv su 10 con stat null/missing"
    )


# ─────────────────────────────────────────────────────────────────────
# t06 — starter kit dry-run: N guilds × quantity=3
# ─────────────────────────────────────────────────────────────────────
def test_t06_dry_run_kit_produces_expected_docs(
    db, event_loop, seeded
):
    seeded(n_guilds=5)

    async def _run():
        return await apply_v1_2._regen_starter_kit(db, "DRY_RUN")

    r = event_loop.run_until_complete(_run())
    assert r["would_create_inventory_docs"] == 5
    assert r["quantity_per_doc"] == 3
    assert r["item_id_resolved"] is not None


# ─────────────────────────────────────────────────────────────────────
# t07 — apply reale: nessun item_id null
# ─────────────────────────────────────────────────────────────────────
def test_t07_no_item_id_null(db, event_loop, seeded):
    seeded(n_guilds=3)

    async def _run():
        await apply_v1_2._regen_starter_kit(db, "APPLY")
        return await db.inventory_items.count_documents({"item_id": None})

    null_c = event_loop.run_until_complete(_run())
    assert null_c == 0


# ─────────────────────────────────────────────────────────────────────
# t08 — nessun duplicate key su (guild_id, item_id)
# ─────────────────────────────────────────────────────────────────────
def test_t08_no_duplicate_key(db, event_loop, seeded):
    seeded(n_guilds=6)

    async def _run():
        await apply_v1_2._regen_starter_kit(db, "APPLY")
        # Re-run: idempotenza
        await apply_v1_2._regen_starter_kit(db, "APPLY")
        # Check duplicati
        pipeline = [
            {"$group": {"_id": {"g": "$guild_id", "i": "$item_id"},
                        "n": {"$sum": 1}}},
            {"$match": {"n": {"$gt": 1}}},
        ]
        dupes = await db.inventory_items.aggregate(pipeline).to_list(None)
        return len(dupes), await db.inventory_items.count_documents({})

    dupe_count, total = event_loop.run_until_complete(_run())
    assert dupe_count == 0
    assert total == 6  # 1 doc/guild


# ─────────────────────────────────────────────────────────────────────
# t09 — Idempotency guard NON blocca per v1.1 rollbackata
# ─────────────────────────────────────────────────────────────────────
def test_t09_guard_does_not_block_for_rolled_back_v1_1(
    db, event_loop, seeded
):
    seeded(n_guilds=2)

    async def _run():
        # Simula storico: APPLIED (v1.1) + ROLLED_BACK successivo
        await db.audit_log.insert_one({
            "id": str(uuid.uuid4()),
            "event_type": apply_v1_2.AUDIT_EVENT_APPLIED,
            "metadata": {"apply_version": "v1.1"},
            "created_at": "2026-07-05T11:00:00+00:00",
        })
        await db.audit_log.insert_one({
            "id": str(uuid.uuid4()),
            "event_type": "R18_FULL_GUILD_FRESH_START_APPLIED_V1_1",
            "metadata": {"apply_version": "v1.1"},
            "created_at": "2026-07-05T11:00:00+00:00",
        })
        await db.audit_log.insert_one({
            "id": str(uuid.uuid4()),
            "event_type": apply_v1_2.AUDIT_EVENT_ROLLED_BACK,
            "metadata": {},
            "created_at": "2026-07-05T12:00:00+00:00",  # dopo apply
        })
        # Nessuna guild con r18_reset1b_applied=true (post-cleanup)
        return await apply_v1_2._apply_state_check(db)

    state = event_loop.run_until_complete(_run())
    assert state["block"] is False, (
        f"Guard bloccato per v1.1 rollbackata: {state['reason']}"
    )
    assert state["hard_stop_needed"] is False


# ─────────────────────────────────────────────────────────────────────
# t10 — Idempotency guard BLOCCA per v1.2 attivo non rollbackato
# ─────────────────────────────────────────────────────────────────────
def test_t10_guard_blocks_for_active_v1_2(db, event_loop, seeded):
    fx = seeded(n_guilds=2)

    async def _run():
        # Set: 1 guild con r18_reset1b_applied=true (apply attivo)
        await db.guilds.update_one(
            {"id": fx["guild_ids"][0]},
            {"$set": {"r18_reset1b_applied": True}},
        )
        return await apply_v1_2._apply_state_check(db)

    state = event_loop.run_until_complete(_run())
    assert state["block"] is True
    assert "r18_reset1b_applied=true" in state["reason"]

    async def _run_v1_2_audit():
        # Reset flag guild + inserisci APPLIED_V1_2 senza rollback
        await db.guilds.update_many(
            {}, {"$set": {"r18_reset1b_applied": False}}
        )
        await db.audit_log.insert_one({
            "id": str(uuid.uuid4()),
            "event_type": apply_v1_2.AUDIT_EVENT_APPLIED_V1_2,
            "metadata": {"apply_version": "v1.2"},
            "created_at": "2026-07-05T13:00:00+00:00",
        })
        return await apply_v1_2._apply_state_check(db)

    state2 = event_loop.run_until_complete(_run_v1_2_audit())
    assert state2["block"] is True
    assert "V1_2" in state2["reason"]


# ─────────────────────────────────────────────────────────────────────
# t11 — Doppio audit event previsto solo dopo apply riuscito
# ─────────────────────────────────────────────────────────────────────
def test_t11_double_audit_only_on_success(db, event_loop, seeded):
    seeded(n_guilds=2)

    async def _run_dry():
        # DRY_RUN: events_would_emit ma NOT actually written
        r = await apply_v1_2._emit_audit_events(
            db, "DRY_RUN", {"guild_reset": {"guilds_target": 2}},
            "/tmp/dummy.json",
        )
        actual_count = await db.audit_log.count_documents({})
        return r, actual_count

    dry_r, actual = event_loop.run_until_complete(_run_dry())
    assert dry_r["emitted"] is False
    assert actual == 0
    assert dry_r["events_would_emit"] == [
        "R18_FULL_GUILD_FRESH_START_APPLIED",
        "R18_FULL_GUILD_FRESH_START_APPLIED_V1_2",
    ]

    async def _run_apply():
        r = await apply_v1_2._emit_audit_events(
            db, "APPLY",
            {
                "guild_reset": {"guilds_target": 2},
                "roster": {
                    "total_adv_created": 10,
                    "class_templates_used": ["mage", "warrior"],
                },
                "kit": {"created_inventory_docs": 2},
            },
            "/tmp/dummy.json",
        )
        events = [
            e async for e in db.audit_log.find({}).sort("event_type", 1)
        ]
        return r, events

    apply_r, events = event_loop.run_until_complete(_run_apply())
    assert apply_r["emitted"] is True
    assert len(events) == 2
    types = sorted(e["event_type"] for e in events)
    assert types == [
        "R18_FULL_GUILD_FRESH_START_APPLIED",
        "R18_FULL_GUILD_FRESH_START_APPLIED_V1_2",
    ]
    # Metadata obbligatoria
    for e in events:
        md = e["metadata"]
        for k in ("round", "apply_script", "apply_version",
                  "starter_kit_fix", "starter_roster_stats_fix",
                  "stat_strategy",
                  "inventory_unique_index_respected",
                  "http_maintenance_required",
                  "internal_job_freeze_required"):
            assert k in md, f"metadata missing key: {k}"
        assert md["apply_version"] == "v1.2"
        assert md["stat_strategy"] == "base_stats_exact_no_variance"
    # Identical shared_metadata fra i due eventi
    assert events[0]["metadata"] == events[1]["metadata"]


# ─────────────────────────────────────────────────────────────────────
# t12 — GET /api/adventurers non fallirebbe per KeyError stat (schema)
# ─────────────────────────────────────────────────────────────────────
def test_t12_get_adventurers_schema_stat_safe(db, event_loop, seeded):
    """Verifica che il roster generato NON abbia mai KeyError potenziale
    sui campi stat (endpoint reads assumono presenza)."""
    seeded(n_guilds=2)

    async def _run():
        templates = await apply_v1_2._preload_class_base_stats(db)
        await apply_v1_2._regen_starter_roster(db, "APPLY", templates)
        # Simula response API: itera adv e prova d[stat]
        bad = []
        async for a in db.adventurers.find({}):
            try:
                _ = (
                    a["strength"] + a["agility"] + a["intellect"] +
                    a["endurance"] + a["faith"]
                )
            except (KeyError, TypeError) as e:
                bad.append(str(e))
        return bad

    bad = event_loop.run_until_complete(_run())
    assert bad == [], f"KeyError/TypeError su stat: {bad}"


# ─────────────────────────────────────────────────────────────────────
# t13 — GET /api/dungeons non fallirebbe per stat mancanti
# ─────────────────────────────────────────────────────────────────────
def test_t13_get_dungeons_schema_stat_safe(db, event_loop, seeded):
    """Dungeons requires guild adventurers stat aggregation (power calc)."""
    seeded(n_guilds=2)

    async def _run():
        templates = await apply_v1_2._preload_class_base_stats(db)
        await apply_v1_2._regen_starter_roster(db, "APPLY", templates)
        # Simula computation power (typical dungeon list needs it)
        errors = []
        async for a in db.adventurers.find({}):
            try:
                power = (
                    a.get("strength", 0) + a.get("agility", 0) +
                    a.get("intellect", 0) + a.get("endurance", 0) +
                    a.get("faith", 0)
                )
                # Power must be > 0 (not all None)
                if power == 0:
                    errors.append(a["id"])
            except (TypeError, KeyError) as e:
                errors.append(str(e))
        return errors

    errors = event_loop.run_until_complete(_run())
    assert errors == [], f"Power calc failure: {errors}"


# ─────────────────────────────────────────────────────────────────────
# t14 — POST /api/expeditions non fallirebbe per KeyError stat
# ─────────────────────────────────────────────────────────────────────
def test_t14_post_expeditions_no_keyerror_stat(
    db, event_loop, seeded
):
    """Expedition creation: team di 5 adv, ognuno con stat. Verify che
    lo stack non ha KeyError su team-power computation."""
    seeded(n_guilds=1)

    async def _run():
        templates = await apply_v1_2._preload_class_base_stats(db)
        await apply_v1_2._regen_starter_roster(db, "APPLY", templates)
        # Team di 5 adv per la sola guild
        team = [a async for a in db.adventurers.find({}).limit(5)]
        assert len(team) == 5
        # Simula expedition mass: somma stat
        try:
            for adv in team:
                _ = {
                    "adv_id": adv["id"],
                    "power": (
                        adv["strength"] * 2 + adv["agility"] +
                        adv["intellect"] + adv["endurance"] +
                        adv["faith"]
                    ),
                }
        except (KeyError, TypeError) as e:
            return f"FAIL: {e}"
        return "OK"

    result = event_loop.run_until_complete(_run())
    assert result == "OK"


# ─────────────────────────────────────────────────────────────────────
# t15 — Nessun DB write in dry-run
# ─────────────────────────────────────────────────────────────────────
def test_t15_dry_run_no_db_writes(db, event_loop, seeded):
    seeded(n_guilds=3)

    async def _run():
        pre_adv = await db.adventurers.count_documents({})
        pre_inv = await db.inventory_items.count_documents({})
        pre_audit = await db.audit_log.count_documents({})
        templates = await apply_v1_2._preload_class_base_stats(db)
        await apply_v1_2._regen_starter_roster(
            db, "DRY_RUN", templates
        )
        await apply_v1_2._regen_starter_kit(db, "DRY_RUN")
        await apply_v1_2._emit_audit_events(
            db, "DRY_RUN", {}, "/tmp/x.json"
        )
        post_adv = await db.adventurers.count_documents({})
        post_inv = await db.inventory_items.count_documents({})
        post_audit = await db.audit_log.count_documents({})
        return (pre_adv, post_adv, pre_inv, post_inv,
                pre_audit, post_audit)

    a1, a2, i1, i2, u1, u2 = event_loop.run_until_complete(_run())
    assert a1 == a2 == 0
    assert i1 == i2 == 0
    assert u1 == u2 == 0


# ─────────────────────────────────────────────────────────────────────
# t16 — HARD STOP se classe safe manca base_*
# ─────────────────────────────────────────────────────────────────────
def test_t16_hard_stop_if_class_missing_base_stat(
    db, event_loop, seeded
):
    """V2.F1 fail-fast: se anche solo 1 classe safe manca base_*,
    RuntimeError hard-stop PRIMA di scrivere alcun adv."""
    # Seed con `mage` che manca `base_intellect`
    seeded(n_guilds=2, skip_stat_for_class=("mage", "intellect"))

    async def _run():
        with pytest.raises(RuntimeError) as exc_info:
            await apply_v1_2._preload_class_base_stats(db)
        return str(exc_info.value)

    err = event_loop.run_until_complete(_run())
    assert "V2.F1_HARD_STOP" in err
    assert "mage" in err
    assert "intellect" in err

    # Verifica NO adv scritti pre-hard-stop
    async def _check():
        return await db.adventurers.count_documents({})

    adv_c = event_loop.run_until_complete(_check())
    assert adv_c == 0
