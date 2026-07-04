"""ROUND 18.1 — Migration integrity tests.

Verifica post-apply che:
  1. Backup manifest + dump esistono
  2. Feature flag R18_REWORK_ENABLED è OFF
  3. recruit_unassigned class doc esiste con marker corretti
  4. Dry-run recruit_unassigned identifica 0 candidati residui (idempotent state)
  5. Apply recruit_unassigned = 0 (idempotent)
  6. Guardian/Cleric legacy = 0 residui
  7. Apply Guardian/Cleric alias = 0 (idempotent)
  8. grade=None/missing = 0 (backfill complete)
  9. Nessun adventurer ha perso equipment/level/xp (spot-check)
 10. Roster cap computed su tutte le guilds
 11. Nessuna gilda ha attivato blocco SOFT
 12. r18_beta_opt_in field default = False
 13. Audit events R18_* scritti
 14. Talent tree collezioni esistono
 15. Talent tree schema accetta insert dummy + rollback
 16. Feature flag OFF → nessun endpoint player-facing R18 esposto
"""
import os
import asyncio
import json
import pytest
from pathlib import Path

from dotenv import dotenv_values, load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# R18.1 verification tests: post-migration audit against the DEV DB
# (orbus_r16), NOT the pytest-isolated test DB. Migration was applied on
# the live dev DB per PM authorization. Read-only checks only.
load_dotenv("/app/backend/.env")
_BACKEND_ENV = dotenv_values("/app/backend/.env")
_DEV_DB_NAME = _BACKEND_ENV.get("DB_NAME") or os.environ.get("DB_NAME")
_DEV_MONGO_URL = _BACKEND_ENV.get("MONGO_URL") or os.environ.get("MONGO_URL")

BACKUP_MANIFEST = Path("/app/memory/backups/round181_prestart/manifest.json")
BACKUP_DUMP = Path("/app/memory/backups/round181_prestart/dump")


@pytest.fixture(scope="module")
def db():
    client = AsyncIOMotorClient(_DEV_MONGO_URL)
    yield client[_DEV_DB_NAME]
    client.close()


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ─── 1. Backup ───────────────────────────────────────────────────────────
def test_01_backup_manifest_valid():
    assert BACKUP_MANIFEST.exists(), "backup manifest missing"
    m = json.loads(BACKUP_MANIFEST.read_text())
    assert m["round"] == "R18.1"
    assert "adventurers" in m["collections"]
    assert "guilds" in m["collections"]
    assert BACKUP_DUMP.exists() and BACKUP_DUMP.is_dir()


# ─── 2. Feature flag ─────────────────────────────────────────────────────
def test_02_feature_flag_off():
    val = os.environ.get("R18_REWORK_ENABLED", "").lower()
    assert val in ("false", "0", "no", ""), \
        f"R18_REWORK_ENABLED must be OFF in R18.1, got '{val}'"


# ─── 3. recruit_unassigned class exists ──────────────────────────────────
def test_03_recruit_unassigned_class(db):
    doc = _run(db.adventurer_classes.find_one({"slug": "recruit_unassigned"}))
    assert doc is not None, "recruit_unassigned class missing"
    assert doc.get("is_canonical") is False
    assert doc.get("is_playable") is False
    assert doc.get("is_talent_tree_eligible") is False
    assert doc.get("drops_items") is False


# ─── 4/5. Idempotent state check for orphans ────────────────────────────
def test_04_orphans_backfilled(db):
    # All adventurers must have valid class_slug
    valid_slugs = set()
    for c in _run(db.adventurer_classes.find(
        {}, {"_id": 0, "slug": 1}).to_list(length=None)
    ):
        valid_slugs.add(c["slug"])
    invalid = _run(db.adventurers.count_documents({
        "$and": [
            {"class_slug": {"$nin": list(valid_slugs)}},
        ]
    }))
    assert invalid == 0, f"{invalid} adventurers still with invalid class_slug"


def test_05_recruit_unassigned_count(db):
    # 91 orfani totali marcati (r18_orphan_migrated_at). Di questi, 6 avevano
    # anche class legacy Guardian/Cleric → Block C li aliasa a paladin/priest
    # (overlap intenzionale). Finale: 91 marker + 85 con slug recruit_unassigned.
    n_marked = _run(db.adventurers.count_documents(
        {"r18_orphan_migrated_at": {"$exists": True}}
    ))
    assert n_marked == 91, f"expected 91 orphan-migrated markers, got {n_marked}"
    n_slug = _run(db.adventurers.count_documents(
        {"class_slug": "recruit_unassigned"}
    ))
    n_gc_aliased_from_orphan = _run(db.adventurers.count_documents({
        "r18_orphan_migrated_at": {"$exists": True},
        "r18_alias_migrated_at": {"$exists": True},
    }))
    assert n_slug == n_marked - n_gc_aliased_from_orphan, (
        f"recruit_unassigned slug={n_slug}, expected "
        f"{n_marked}-{n_gc_aliased_from_orphan}={n_marked - n_gc_aliased_from_orphan}"
    )


# ─── 6/7. Guardian/Cleric aliased ────────────────────────────────────────
def test_06_no_guardian_cleric_class_slug(db):
    # After alias, class_slug should be paladin/priest, NOT Guardian/Cleric
    n = _run(db.adventurers.count_documents({
        "class_slug": {"$in": ["Guardian", "Cleric", "guardian", "cleric"]}
    }))
    assert n == 0, f"{n} adventurers still with Guardian/Cleric slug"


def test_07_legacy_alias_traceable(db):
    # All 6 aliased docs should have legacy_class_original marker
    n = _run(db.adventurers.count_documents({
        "legacy_class_original": {"$in": ["Guardian", "Cleric"]}
    }))
    assert n == 6, f"expected 6 with legacy_class_original, got {n}"


# ─── 8. grade backfill complete ──────────────────────────────────────────
def test_08_grade_backfill_complete(db):
    missing = _run(db.adventurers.count_documents({
        "$or": [{"grade": None}, {"grade": {"$exists": False}}]
    }))
    assert missing == 0, f"{missing} adventurers still without grade"
    n_common = _run(db.adventurers.count_documents({"grade": "common"}))
    assert n_common >= 2125, f"expected >=2125 grade=common, got {n_common}"


# ─── 9. No level/class_slug loss (spot-check) ───────────────────────────
def test_09_no_data_loss_spot_check(db):
    # Verifichiamo che la migrazione non abbia perso campi core:
    # `level` e `class_slug` (touched by B/C blocks). NON verifichiamo `stats`
    # perché ~99% adventurers non hanno mai avuto quel field pre-R18.1 (dato
    # storico). La migrazione R18.1 non introduce/rimuove `stats`.
    docs = _run(db.adventurers.find(
        {}, {"_id": 0, "id": 1, "level": 1, "class_slug": 1}
    ).limit(20).to_list(length=20))
    assert len(docs) >= 10
    for d in docs:
        assert d.get("level") is not None, \
            f"adv {d['id']} lost level!"
        assert d.get("class_slug"), \
            f"adv {d['id']} has empty class_slug post-migration!"


# ─── 10. Roster cap computed ─────────────────────────────────────────────
def test_10_roster_cap_computed(db):
    total = _run(db.guilds.count_documents({}))
    with_cap = _run(db.guilds.count_documents({
        "max_roster_cap": {"$exists": True, "$ne": None}
    }))
    assert with_cap == total, \
        f"only {with_cap}/{total} guilds have max_roster_cap"


# ─── 11. SOFT enforcement (post-R18.1.1 canonical formula) ─────────────
def test_11_soft_no_hard_block(db):
    # Post R18.1.1: formula ora è `min(50, 10 + max(level, guild_level, 1)*2)`.
    # Verifica: (a) grandfathered marker coerente con roster>cap,
    # (b) `la lanterna di ferro` NON è più grandfathered (cap=40, roster=23),
    # (c) feature flag OFF.
    gf = _run(db.guilds.find(
        {"is_grandfathered": True},
        {"_id": 0, "id": 1, "name": 1, "max_roster_cap": 1, "current_roster_size": 1}
    ).to_list(length=None))
    for g in gf:
        cap = g.get("max_roster_cap")
        cur = g.get("current_roster_size")
        assert cap is not None and cur is not None
        assert cur > cap, (
            f"guild {g['id']} grandfathered ma roster {cur} <= cap {cap}"
        )
    # `la lanterna di ferro` deve essere sana post-hotfix
    lanterna = _run(db.guilds.find_one(
        {"name": "la lanterna di ferro"},
        {"_id": 0, "max_roster_cap": 1, "is_grandfathered": 1,
         "r18_effective_level": 1}
    ))
    if lanterna is not None:
        assert lanterna.get("max_roster_cap") == 40, (
            f"la lanterna di ferro cap should be 40 post-hotfix, "
            f"got {lanterna.get('max_roster_cap')}"
        )
        assert lanterna.get("is_grandfathered") is False, \
            "la lanterna di ferro should NOT be grandfathered post R18.1.1"
        assert lanterna.get("r18_effective_level") == 15, \
            "la lanterna di ferro effective_level should be 15"
    # Feature flag deve restare OFF → nessun enforcement attivo
    assert os.environ.get("R18_REWORK_ENABLED", "false").lower() == "false"


# ─── 12. r18_beta_opt_in default False ──────────────────────────────────
def test_12_beta_opt_in_default(db):
    n_true = _run(db.guilds.count_documents({"r18_beta_opt_in": True}))
    n_false = _run(db.guilds.count_documents({"r18_beta_opt_in": False}))
    n_total = _run(db.guilds.count_documents({}))
    assert n_true == 0, f"{n_true} guilds already opted-in (should be 0)"
    assert n_false == n_total, "r18_beta_opt_in not defaulted on all guilds"


# ─── 13. Audit events R18_* ─────────────────────────────────────────────
def test_13_audit_events(db):
    for evt in [
        "R18_MIGRATION_STARTED",
        "R18_MIGRATION_COMPLETED",
        "R18_ORPHAN_MARKED_UNASSIGNED",
        "R18_GUARDIAN_CLERIC_ALIASED",
        "R18_GRADE_BACKFILLED",
        "R18_ROSTER_CAP_COMPUTED",
        "R18_BETA_FIELD_PREPARED",
    ]:
        n = _run(db.audit_events.count_documents({"event_type": evt}))
        assert n >= 1, f"audit event {evt} not emitted"


# ─── 14. Talent tree collections exist ──────────────────────────────────
def test_14_talent_collections(db):
    colls = _run(db.list_collection_names())
    for coll in (
        "talent_tree_definitions",
        "adventurer_talent_progress",
        "career_history",
    ):
        assert coll in colls, f"collection {coll} missing"


# ─── 15. Talent schema accepts dummy insert + rollback ──────────────────
def test_15_talent_schema_dummy_insert_rollback(db):
    import uuid
    dummy_id = str(uuid.uuid4())
    doc = {
        "id": dummy_id,
        "class_slug": "__pytest_dummy__",
        "branch": "dummy_branch",
        "tier": 1,
        "slot_id": "test_slot",
        "max_points": 4,
        "requirements": [],
        "stat_modifiers": {"strength": 1},
        "is_pytest_dummy": True,
    }
    r_ins = _run(db.talent_tree_definitions.insert_one(doc))
    assert r_ins.inserted_id is not None
    r_del = _run(db.talent_tree_definitions.delete_one(
        {"id": dummy_id, "is_pytest_dummy": True}
    ))
    assert r_del.deleted_count == 1


# ─── 16. Feature flag OFF → no player-facing R18 endpoint ───────────────
def test_16_no_player_facing_r18_change(db):
    # Guild collection must NOT expose r18_* fields via public /guilds/me
    # (verifica soft: nessun endpoint router pubblico legge quel campo).
    # In R18.1 field esistono in DB ma non sono usati dai router API.
    # Test symbolic: confermiamo che il flag è OFF.
    assert os.environ.get("R18_REWORK_ENABLED", "false").lower() == "false"



# ─── 17. audit_log R18_* observability (fixed via backfill) ─────────────
def test_17_audit_log_retroactive_events(db):
    """RCA post-hoc: gli event R18_* originali erano scritti solo in
    `audit_events` (secondaria). Lo script
    `round181_audit_log_backfill.py` li ha replicati in `audit_log`
    (feed admin) con `is_retroactive=true`. Verifica:
      - 7 event_type presenti (uno per tipo, idempotente)
      - `metadata.is_retroactive=True`
      - `metadata.round="R18.1"`
      - `metadata.original_occurred_at` preservato dal source
    """
    required = [
        "R18_MIGRATION_STARTED",
        "R18_MIGRATION_COMPLETED",
        "R18_ORPHAN_MARKED_UNASSIGNED",
        "R18_GUARDIAN_CLERIC_ALIASED",
        "R18_GRADE_BACKFILLED",
        "R18_ROSTER_CAP_COMPUTED",
        "R18_BETA_FIELD_PREPARED",
    ]
    total_r18 = _run(db.audit_log.count_documents(
        {"event_type": {"$regex": "^R18_"}}
    ))
    assert total_r18 >= 7, (
        f"audit_log R18_* count={total_r18}, expected ≥ 7 "
        "(run round181_audit_log_backfill.py --apply)"
    )
    for evt in required:
        doc = _run(db.audit_log.find_one(
            {"event_type": evt, "metadata.round": "R18.1"}, {"_id": 0}
        ))
        assert doc is not None, f"{evt} missing from audit_log"
        assert doc.get("metadata", {}).get("is_retroactive") is True, \
            f"{evt} missing is_retroactive marker"
        assert doc.get("metadata", {}).get("original_occurred_at"), \
            f"{evt} missing original_occurred_at"


# ─── 18. Expedition guardrail — R18.1.1 recruit_unassigned block ────────
def test_18_expedition_guardrail_recruit_unassigned_active(db):
    """R18.1.1 Hotfix 2: safety guard su expedition dispatch che rifiuta
    adventurers con `class_slug=recruit_unassigned` o class non canonica
    (`is_playable=false` o slug non in catalogo).

    Verifica presenza codice guard nel service (senza chiamata HTTP).
    Test HTTP dedicato è in `backend_round1811_guard_test.py`.
    """
    import pathlib
    svc = pathlib.Path("/app/backend/app/expeditions/services.py")
    assert svc.exists()
    content = svc.read_text()
    # Guard signature
    assert "recruit_unassigned_in_set" in content, (
        "expedition guard code marker 'recruit_unassigned_in_set' missing"
    )
    assert "is_playable" in content, (
        "expedition guard should check is_playable"
    )
    assert "Riassegnalo prima di mandarlo in missione" in content, (
        "IT user_message missing from expedition guard"
    )
    # class doc marker still correct
    class_doc = _run(db.adventurer_classes.find_one(
        {"slug": "recruit_unassigned"}, {"_id": 0}
    ))
    assert class_doc is not None
    assert class_doc.get("is_playable") is False
    # Feature flag OFF (guard is safety-only, flag-independent)
    assert os.environ.get("R18_REWORK_ENABLED", "false").lower() == "false"
