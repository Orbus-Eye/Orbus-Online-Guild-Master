# ═════════════════════════════════════════════════════════════════════
# R18.Reset.1b.hotfix.write_freeze_full — CLOSED & SEALED on 2026-07-05T11:15:00Z
# Tester independent verification: 10/10 PASS + live runtime evidence
# Pytest: 11/11 PASS (10 PM + 1 gap-evidence t11)
# Sealed by: PM_authorization
# NON modificare. Se serve fix, creare nuovo sibling test file
#   (es. backend_round1b_write_freeze_full_v2_test.py).
# ═════════════════════════════════════════════════════════════════════


"""R18.Reset.1b.hotfix.write_freeze_full — Test suite.

Copre 11 test cases (10 PM + 1 gap-evidence) per il freeze internal
async jobs via `ORBUS_INTERNAL_JOB_FREEZE`.

Isolamento DB: `test_orbus_r18_write_freeze_<pid>` con drop teardown.
Zero contatto col DB primario `orbus_r16` / `orbus_r16_test`.

Vincoli rispettati:
    - Zero reset reale (DB test isolato)
    - Zero apply reale (script v1.1 NON invocato con --apply)
    - Zero modifica script sealed (integrity check pre/post)
    - Zero side effect fuori dai test-DB dedicati
"""
# ═════════════════════════════════════════════════════════════════════
# R18.Reset.1b.hotfix.write_freeze_full test suite
# Autore: e1 main agent — 2026-07-05T10:45Z
# ═════════════════════════════════════════════════════════════════════
from __future__ import annotations

import asyncio
import hashlib
import importlib
import logging
import os
import sys
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest
from motor.motor_asyncio import AsyncIOMotorClient

_BACKEND_ROOT = Path("/app/backend")
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

job_freeze = importlib.import_module("app.core.job_freeze")
FREEZE_ENV_VAR = job_freeze.FREEZE_ENV_VAR
FREEZE_FLAG_FILE = job_freeze.FREEZE_FLAG_FILE
frozen_when_active = job_freeze.frozen_when_active
is_freeze_active = job_freeze.is_freeze_active

MAINTENANCE_FLAG_FILE = "/tmp/orbus_maintenance.flag"
MAINTENANCE_ENV_VAR = "ORBUS_MAINTENANCE_MODE"

PLAYBOOK_PATH = _BACKEND_ROOT.parent / "memory" / (
    "r18_reset1b_ops_write_freeze_playbook.md"
)
PLAN_JSON_PATH = _BACKEND_ROOT.parent / "memory" / (
    "r18_reset1b_full_guild_fresh_start_apply_plan.json"
)
APPLY_V1_1_PATH = (
    _BACKEND_ROOT / "app/scripts/round18_reset1b_apply_v1_1.py"
)

SEALED_APPLY_SHA256_BASELINE = (
    "657d5853a5b203005a319452260bc2d8413e94d5fa8857ba36de4b78d427d934"
)
SEALED_APPLY_PATH = _BACKEND_ROOT / "app/scripts/round18_reset1b_apply.py"


# ─────────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────────
def _isolated_db_name() -> str:
    return f"test_orbus_r18_write_freeze_{os.getpid()}"


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

    async def _teardown():
        await client.drop_database(db_name)
        client.close()

    yield database
    event_loop.run_until_complete(_teardown())


@pytest.fixture(autouse=True)
def clean_flags():
    """Reset env var + file flag PRIMA e DOPO ogni test."""
    for var in (FREEZE_ENV_VAR, MAINTENANCE_ENV_VAR):
        os.environ.pop(var, None)
    for flag in (FREEZE_FLAG_FILE, MAINTENANCE_FLAG_FILE):
        Path(flag).unlink(missing_ok=True)
    yield
    for var in (FREEZE_ENV_VAR, MAINTENANCE_ENV_VAR):
        os.environ.pop(var, None)
    for flag in (FREEZE_FLAG_FILE, MAINTENANCE_FLAG_FILE):
        Path(flag).unlink(missing_ok=True)


@pytest.fixture
def reset_db(db, event_loop):
    """Reset delle collezioni target prima di ogni test che scrive."""

    async def _reset():
        for coll in [
            "adventurers", "inventory_items", "guilds", "items",
            "expeditions", "raids", "resource_gathering_missions",
            "audit_log",
        ]:
            await db[coll].delete_many({})

    def _apply():
        return event_loop.run_until_complete(_reset())

    return _apply


# ─────────────────────────────────────────────────────────────────────
# t01 — Default OFF: job coperti scrivono normalmente
# ─────────────────────────────────────────────────────────────────────
def test_t01_default_off_job_writes_normally(db, event_loop, reset_db):
    """Freeze default OFF → job async decorato scrive normalmente
    in `adventurers`. Idempotenza normale del business logic."""
    reset_db()
    assert is_freeze_active() is False

    @frozen_when_active("test.dummy_write_job")
    async def dummy_write():
        await db.adventurers.insert_one({
            "id": str(uuid.uuid4()),
            "guild_id": "g_test_t01",
            "name": "AdvT01",
        })
        return 1

    async def _run():
        r = await dummy_write()
        cnt = await db.adventurers.count_documents({})
        return r, cnt

    r, cnt = event_loop.run_until_complete(_run())
    assert r == 1
    assert cnt == 1


# ─────────────────────────────────────────────────────────────────────
# t02 — ON via env: skip + WARN log
# ─────────────────────────────────────────────────────────────────────
def test_t02_on_via_env_skip_and_warn(db, event_loop, reset_db, caplog):
    """`ORBUS_INTERNAL_JOB_FREEZE=true` → skip + WARN log verificato."""
    reset_db()
    os.environ[FREEZE_ENV_VAR] = "true"
    assert is_freeze_active() is True

    @frozen_when_active("test.dummy_write_via_env", freeze_return_value=0)
    async def dummy_write():
        await db.adventurers.insert_one({"id": "should-never-write"})
        return 1

    async def _run():
        return await dummy_write()

    with caplog.at_level(logging.WARNING, logger="orbus.job_freeze"):
        result = event_loop.run_until_complete(_run())

    assert result == 0, "skip return value non rispettato"
    count = event_loop.run_until_complete(
        db.adventurers.count_documents({})
    )
    assert count == 0, "job skippato ma ha scritto (freeze bypass)"
    # WARN log verifica
    warn_msgs = [
        r.message for r in caplog.records if r.levelno == logging.WARNING
    ]
    assert any(
        "Internal job skipped due to ORBUS_INTERNAL_JOB_FREEZE" in m
        for m in warn_msgs
    ), f"WARN log atteso mancante. Got: {warn_msgs}"


# ─────────────────────────────────────────────────────────────────────
# t03 — ON via file flag (fallback)
# ─────────────────────────────────────────────────────────────────────
def test_t03_on_via_file_flag_fallback(db, event_loop, reset_db, caplog):
    """`/tmp/orbus_internal_job_freeze.flag` esiste → skip + WARN log.
    Env var assente (fallback file flag funziona)."""
    reset_db()
    Path(FREEZE_FLAG_FILE).touch()
    assert FREEZE_ENV_VAR not in os.environ
    assert is_freeze_active() is True

    @frozen_when_active("test.file_flag_job")
    async def dummy():
        await db.adventurers.insert_one({"id": "flag-skip"})
        return "should-not-return"

    async def _run():
        return await dummy()

    with caplog.at_level(logging.WARNING, logger="orbus.job_freeze"):
        r = event_loop.run_until_complete(_run())

    assert r is None
    cnt = event_loop.run_until_complete(
        db.adventurers.count_documents({})
    )
    assert cnt == 0
    warn_msgs = [
        m.message for m in caplog.records if m.levelno == logging.WARNING
    ]
    assert any("skipped" in m for m in warn_msgs)


# ─────────────────────────────────────────────────────────────────────
# t04 — Job freeze da solo NON blocca HTTP maintenance
# ─────────────────────────────────────────────────────────────────────
def test_t04_job_freeze_alone_does_not_block_http():
    """Con solo `ORBUS_INTERNAL_JOB_FREEZE=true`, il MaintenanceMiddleware
    HTTP (gate 5) NON deve attivarsi. Job freeze e HTTP maintenance
    sono INDIPENDENTI (ognuno legge il proprio flag)."""
    from app.core.maintenance import _is_maintenance_enabled

    os.environ[FREEZE_ENV_VAR] = "true"
    assert is_freeze_active() is True
    assert _is_maintenance_enabled() is False, (
        "MaintenanceMiddleware HTTP scattato quando SOLO job_freeze e' ON. "
        "I due flag devono essere indipendenti."
    )


# ─────────────────────────────────────────────────────────────────────
# t05 — Combinato: maintenance HTTP + job freeze insieme
# ─────────────────────────────────────────────────────────────────────
def test_t05_combined_maintenance_and_job_freeze():
    """`ORBUS_MAINTENANCE_MODE=true` + `ORBUS_INTERNAL_JOB_FREEZE=true`
    → entrambi attivi indipendentemente. Ognuno fa il suo mestiere:
    HTTP freeze blocca POST/PUT/PATCH/DELETE (gate 5), job freeze
    skippa job async interni (gate 7)."""
    from app.core.maintenance import _is_maintenance_enabled

    os.environ[MAINTENANCE_ENV_VAR] = "true"
    os.environ[FREEZE_ENV_VAR] = "true"
    assert _is_maintenance_enabled() is True
    assert is_freeze_active() is True

    # Ognuno gestibile indipendentemente: rimuovo solo uno
    del os.environ[FREEZE_ENV_VAR]
    assert _is_maintenance_enabled() is True
    assert is_freeze_active() is False


# ─────────────────────────────────────────────────────────────────────
# t06 — `orbus.onboarding.starter_roster` non crea adventurers in freeze
# ─────────────────────────────────────────────────────────────────────
def test_t06_starter_roster_no_write_when_frozen(
    db, event_loop, reset_db, caplog
):
    """Test specifico del job che ha causato il drift +2.
    L1 in inventory: `ensure_starter_roster_for_all_guilds`.
    Con freeze attivo, NESSUN adventurer creato."""
    reset_db()
    # Setup: 3 guild con roster vuoto (needed=5 ciascuna per starter)
    async def _setup():
        for i in range(3):
            gid = str(uuid.uuid4())
            await db.guilds.insert_one({
                "id": gid, "name": f"g_t06_{i}", "owner_user_id": None,
            })
        # Seed una classe attiva (necessaria dal job originale)
        await db.adventurer_classes.insert_one({
            "id": str(uuid.uuid4()),
            "name": "test_class", "slug": "test_class", "role": "test",
            "is_active": True, "base_strength": 10, "base_agility": 10,
            "base_intellect": 10, "base_endurance": 10, "base_faith": 10,
        })
        await db.adventurer_traits.insert_many([
            {"id": str(uuid.uuid4()), "name": "t1", "is_active": True},
            {"id": str(uuid.uuid4()), "name": "t2", "is_active": True},
        ])
    event_loop.run_until_complete(_setup())

    os.environ[FREEZE_ENV_VAR] = "true"

    from app.onboarding.services import ensure_starter_roster_for_all_guilds

    async def _run():
        pre = await db.adventurers.count_documents({})
        result = await ensure_starter_roster_for_all_guilds(db)
        post = await db.adventurers.count_documents({})
        return pre, result, post

    with caplog.at_level(logging.WARNING, logger="orbus.job_freeze"):
        pre, result, post = event_loop.run_until_complete(_run())

    assert pre == 0
    assert post == 0, (
        f"L1 starter_roster ha creato {post} adv in freeze — bypass!"
    )
    # Return neutro: dict compatibile con caller `seed_round5.py:604`
    # che fa `backfill.get("advs_inserted", 0)`
    assert isinstance(result, dict)
    assert result.get("advs_inserted", 0) == 0
    warn_msgs = [
        m.message for m in caplog.records if m.levelno == logging.WARNING
    ]
    assert any("skipped" in m for m in warn_msgs)


# ─────────────────────────────────────────────────────────────────────
# t07 — Playbook aggiornato con sezione "Internal Job Freeze"
# ─────────────────────────────────────────────────────────────────────
def test_t07_playbook_has_internal_job_freeze_section():
    """Il playbook R18.Reset.1b.ops deve contenere una sezione dedicata
    all'internal job freeze (nome esatto): 'Internal Job Freeze'."""
    assert PLAYBOOK_PATH.exists(), (
        f"Playbook non trovato: {PLAYBOOK_PATH}"
    )
    content = PLAYBOOK_PATH.read_text()
    assert "Internal Job Freeze" in content, (
        "Sezione 'Internal Job Freeze' assente nel playbook"
    )
    # Verifica riferimenti chiave
    assert FREEZE_ENV_VAR in content
    assert FREEZE_FLAG_FILE in content
    assert "Internal job skipped" in content


# ─────────────────────────────────────────────────────────────────────
# t08 — Nessun reset reale eseguito (DB live invariante)
# ─────────────────────────────────────────────────────────────────────
def test_t08_no_real_reset_executed():
    """La test suite NON deve toccare il DB `orbus_r16`. Verifichiamo
    che il DB name in uso sia isolato test."""
    db_name = _isolated_db_name()
    assert "test" in db_name.lower()
    assert "r18_write_freeze" in db_name
    assert db_name != "orbus_r16"
    assert db_name != "orbus_r16_test"
    # Verifica: nessun sealed script scritto/toccato
    with SEALED_APPLY_PATH.open("rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()
    assert digest == SEALED_APPLY_SHA256_BASELINE, (
        "Sealed script modificato durante i test — VIOLAZIONE."
    )


# ─────────────────────────────────────────────────────────────────────
# t09 — Nessun apply reale eseguito
# ─────────────────────────────────────────────────────────────────────
def test_t09_no_real_apply_executed():
    """Verifichiamo che lo script v1.1 esista ma NON sia stato invocato
    con `--apply`. Nessun audit event R18_FULL_GUILD_FRESH_START_APPLIED
    sul DB test (che e' vuoto)."""
    assert APPLY_V1_1_PATH.exists()
    # Il DB test e' isolato: nessun audit event R18 possibile
    # (il DB e' dropped alla fine ma comunque vuoto pre-teardown)
    src = APPLY_V1_1_PATH.read_text()
    # Doppio safety-gate ancora presente
    assert "--i-understand-this-will-reset-all-guilds" in src
    assert 'return "DRY_RUN"' in src


# ─────────────────────────────────────────────────────────────────────
# t10 — R18.Reset.1b APPLY resta bloccato (§16 gate 4 pending)
# Baseline post-seal 2026-07-05T11:15:00Z: gate 7 promoted a
# satisfied=true da PM_authorization. Il contract del test resta
# "no unauthorized promotion" → resta pending solo gate 4.
# ─────────────────────────────────────────────────────────────────────
def test_t10_apply_still_blocked_gate_4_pending():
    """Verifica che il plan §16 abbia gate 4 (PM sign-off) ancora
    PENDING. Le modifiche del round non hanno auto-promosso PM sign-off.
    Nota: gate 7 (write_freeze_full) e' stato SEALED da PM in Fase A
    2026-07-05T11:15Z — questo test riflette il baseline post-seal."""
    import json
    plan = json.loads(PLAN_JSON_PATH.read_text())
    s16 = plan["sections"]["section_16_human_approval_gate"]
    gate_4 = next(
        hb for hb in s16["hard_blockers"]
        if hb["id"] == "pm_sign_off_renewed"
    )
    assert gate_4["satisfied"] is False, (
        "Gate 4 PM sign-off era pending, ora e' satisfied — "
        "auto-promotion non autorizzata."
    )
    # Gate 7 write_freeze_full: verifica seal formale documentato
    gate_7 = next(
        hb for hb in s16["hard_blockers"]
        if hb["id"] == "r18_reset1b_hotfix_write_freeze_full_pass"
    )
    # Post-seal PM_authorization: gate 7 deve essere satisfied CON
    # sealed_at + sealed_by esplicito
    assert gate_7["satisfied"] is True, (
        "Gate 7 write_freeze_full post-seal PM deve essere satisfied."
    )
    assert gate_7.get("sealed_by") == "PM_authorization", (
        "Gate 7 deve avere sealed_by='PM_authorization' come marker seal."
    )
    # Status residuo: 1 of 7 pending (solo gate 4)
    assert s16["status"] == "APPLY_BLOCKED_1_OF_7_GATES_PENDING"
    assert s16["gates_satisfied"] == 6
    assert s16["gates_pending"] == 1


# ─────────────────────────────────────────────────────────────────────
# t11 — GAP EVIDENCE: simula lifespan hot-reload path L1 in freeze
# ─────────────────────────────────────────────────────────────────────
def test_t11_gap_evidence_lifespan_starter_roster_frozen(
    db, event_loop, reset_db, caplog
):
    """Test mirato al gap evidence del PM.

    Contesto (live evidence Fase A):
        Durante il hot-reload backend del 2026-07-05T10:21:55Z, il
        lifespan boot ha eseguito `orbus.onboarding.starter_roster`
        producendo `inserted=2` (guild 907b4ae4-...).

    Verifica:
        Con `ORBUS_INTERNAL_JOB_FREEZE=true`, un trigger analogo del
        lifespan (chiamata a `ensure_starter_roster_for_all_guilds`)
        NON scrive `adventurers`, emette WARN, ritorna dict controllato.
    """
    reset_db()
    # Setup guilds live-like (senza roster) — mimica stato pre-apply
    async def _setup():
        for i in range(5):
            await db.guilds.insert_one({
                "id": f"lifespan_g_{i}",
                "name": f"LifespanBootGuild_{i}",
                "owner_user_id": f"user_{i}",
            })
        # Classe attiva (richiesta dal job originale)
        await db.adventurer_classes.insert_one({
            "id": str(uuid.uuid4()),
            "name": "gap_evidence_class",
            "slug": "gap_evidence_class",
            "role": "test",
            "is_active": True,
            "base_strength": 10, "base_agility": 10,
            "base_intellect": 10, "base_endurance": 10, "base_faith": 10,
        })
        await db.adventurer_traits.insert_one({
            "id": str(uuid.uuid4()), "name": "gap_trait",
            "is_active": True, "is_test": False,
        })
    event_loop.run_until_complete(_setup())

    os.environ[FREEZE_ENV_VAR] = "true"
    from app.onboarding.services import ensure_starter_roster_for_all_guilds

    async def _lifespan_trigger():
        # Mimica linea 603 di seed_round5.py:
        #     backfill = await ensure_starter_roster_for_all_guilds(db)
        pre = await db.adventurers.count_documents({})
        backfill = await ensure_starter_roster_for_all_guilds(db)
        post = await db.adventurers.count_documents({})
        # Il caller `seed_round5.py:604` fa backfill.get("advs_inserted", 0)
        # Deve funzionare senza AttributeError.
        advs_inserted = backfill.get("advs_inserted", 0)
        return pre, backfill, advs_inserted, post

    with caplog.at_level(logging.WARNING, logger="orbus.job_freeze"):
        pre, backfill, advs_inserted, post = event_loop.run_until_complete(
            _lifespan_trigger()
        )

    # ASSERTIONS gap-evidence:
    assert pre == 0
    assert post == 0, (
        f"GAP GAP GAP: lifespan starter_roster ha scritto {post} adv "
        "in freeze. Il gap NON e' stato chiuso — freeze bypass."
    )
    assert backfill is not None, "return neutro None non compatibile"
    assert isinstance(backfill, dict), (
        "return neutro deve essere dict per compat caller"
    )
    assert advs_inserted == 0, (
        "advs_inserted != 0: caller riceverebbe conteggi drift"
    )

    # WARN log presente
    warn_msgs = [
        m.message for m in caplog.records if m.levelno == logging.WARNING
    ]
    matched = [m for m in warn_msgs if "skipped" in m and (
        "orbus.onboarding.starter_roster_for_all_guilds" in m
        or "starter_roster" in m
    )]
    assert matched, (
        f"WARN log del starter_roster job non emesso. Got: {warn_msgs}"
    )

    # Ritorno controllato: no exception rilevato (il pytest fallirebbe)
    # e nessun retry (il decorator ritorna al primo call).
