"""R18.Reset.1b.hotfix — Test suite per `round18_reset1b_apply_v1_1.py`.

Autore: e1 main agent — 2026-07-05T09:44Z.

Copre 12 casi (t01..t12) per lo starter kit inventory unique index fix.

Isolamento DB:
    - Ogni test module usa un DB Mongo dedicato con nome:
        `test_orbus_r18_hotfix_<pid>`
    - Nessun test tocca `orbus_r16`, `orbus_r16_test`, nè le
      collections live. Fixture `db` fa drop del DB test alla fine.

Zero side effect:
    - Non esegue apply reale sul DB primario.
    - Verifica solo il comportamento delle funzioni pure di
      `round18_reset1b_apply_v1_1` invocate su un DB Motor isolato.

Bypass del conftest globale (guard-rail `_is_test_db`):
    Il DB name usato contiene "test" → soddisfa la guard globale
    definita in `/app/backend/tests/conftest.py` righe 34-49.
"""
from __future__ import annotations

import asyncio
import hashlib
import importlib
import inspect
import os
import sys
import uuid
from pathlib import Path

import pytest
from motor.motor_asyncio import AsyncIOMotorClient

# Assicura import del package `app.scripts` come modulo Python.
_BACKEND_ROOT = Path("/app/backend")
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

apply_v1_1 = importlib.import_module(
    "app.scripts.round18_reset1b_apply_v1_1"
)

SEALED_APPLY_PATH = _BACKEND_ROOT / "app/scripts/round18_reset1b_apply.py"
V1_1_APPLY_PATH = (
    _BACKEND_ROOT / "app/scripts/round18_reset1b_apply_v1_1.py"
)
ROLLBACK_PATH = _BACKEND_ROOT / "app/scripts/round18_reset1b_rollback.py"
CLEANUP_PATH = (
    _BACKEND_ROOT / "app/scripts/round18_reset1c_field_cleanup.py"
)

# Sealed baseline SHA-256 (dal preflight R18.Reset.1b.hotfix)
SEALED_APPLY_SHA256_BASELINE = (
    "657d5853a5b203005a319452260bc2d8413e94d5fa8857ba36de4b78d427d934"
)
SEALED_APPLY_MTIME_BASELINE = 1783235358


# ─────────────────────────────────────────────────────────────────────
# FIXTURE: DB isolato Mongo per test (drop on teardown)
# ─────────────────────────────────────────────────────────────────────
def _isolated_db_name() -> str:
    return f"test_orbus_r18_hotfix_{os.getpid()}"


@pytest.fixture(scope="module")
def event_loop():
    """Loop scoped al modulo per condividere il client Motor fra test."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def mongo_url() -> str:
    return os.environ.get("MONGO_URL", "mongodb://localhost:27017")


@pytest.fixture(scope="module")
def db(mongo_url, event_loop):
    """DB isolato per il modulo. Drop finale su teardown."""
    db_name = _isolated_db_name()
    client = AsyncIOMotorClient(mongo_url)
    database = client[db_name]

    async def _setup():
        # Indice `inv_guild_item_unique` mirror del prod (mandatory
        # per verificare che il fix rispetti l'unique constraint).
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

    async def _teardown():
        await client.drop_database(db_name)
        client.close()

    event_loop.run_until_complete(_setup())
    yield database
    event_loop.run_until_complete(_teardown())


@pytest.fixture
def seed_guilds(db, event_loop):
    """Popola il DB isolato con N guild + item catalog + audit_log
    vuoto. Ritorna una funzione che accetta n_guilds e la applica."""

    async def _apply(n_guilds: int = 3, seed_potion: bool = True):
        # Reset collections rilevanti (isolamento fra test)
        for coll in [
            "guilds", "items", "inventory_items",
            "adventurers", "audit_log",
        ]:
            await db[coll].delete_many({})

        # Item catalog: minor_healing_potion
        potion_id = None
        if seed_potion:
            potion_id = str(uuid.uuid4())
            await db.items.insert_one({
                "id": potion_id,
                "slug": "minor_healing_potion",
                "name": "Minor Healing Potion",
                "type": "consumable",
                "rarity": "Common",
            })

        # Guilds
        guild_ids = []
        for i in range(n_guilds):
            gid = str(uuid.uuid4())
            guild_ids.append(gid)
            await db.guilds.insert_one({
                "id": gid,
                "name": f"TestGuildFixture_{i}",
                "gold": 0,
                "level": 1,
                "reputation": 0,
                "owner_user_id": str(uuid.uuid4()),
                "created_at": apply_v1_1._utc_iso(),
            })
        return {"guild_ids": guild_ids, "potion_id": potion_id}

    return lambda **kwargs: event_loop.run_until_complete(_apply(**kwargs))


# ─────────────────────────────────────────────────────────────────────
# t01 — sealed_script_untouched (sha256 baseline invariato)
# ─────────────────────────────────────────────────────────────────────
def test_t01_sealed_script_untouched():
    """Lo script sealed `round18_reset1b_apply.py` NON deve essere
    modificato dall'hotfix. Verifichiamo sha256 vs baseline preflight."""
    with SEALED_APPLY_PATH.open("rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()
    assert digest == SEALED_APPLY_SHA256_BASELINE, (
        f"Sealed script MODIFICATO! sha256 attuale={digest} "
        f"baseline={SEALED_APPLY_SHA256_BASELINE}"
    )
    mtime = int(SEALED_APPLY_PATH.stat().st_mtime)
    assert mtime == SEALED_APPLY_MTIME_BASELINE, (
        f"mtime cambiato: attuale={mtime} baseline={SEALED_APPLY_MTIME_BASELINE}"
    )


# ─────────────────────────────────────────────────────────────────────
# t02 — v1_1_exists_as_sibling
# ─────────────────────────────────────────────────────────────────────
def test_t02_v1_1_exists_as_sibling():
    """Il nuovo script `round18_reset1b_apply_v1_1.py` esiste come
    file SIBLING (stessa dir dello sealed), non come patch."""
    assert V1_1_APPLY_PATH.exists(), (
        f"File sibling assente: {V1_1_APPLY_PATH}"
    )
    assert V1_1_APPLY_PATH.parent == SEALED_APPLY_PATH.parent, (
        "v1_1 script NON e' sibling dello sealed"
    )
    assert V1_1_APPLY_PATH != SEALED_APPLY_PATH, (
        "v1_1 e sealed sono lo stesso file"
    )
    # Contract: costanti hotfix presenti
    src = V1_1_APPLY_PATH.read_text()
    assert 'R18.Reset.1b.hotfix' in src
    assert 'AUDIT_EVENT_APPLIED_V1_1' in src
    assert 'R18_FULL_GUILD_FRESH_START_APPLIED_V1_1' in src


# ─────────────────────────────────────────────────────────────────────
# t03 — dry_run_no_writes
# ─────────────────────────────────────────────────────────────────────
def test_t03_dry_run_no_writes(db, event_loop, seed_guilds):
    """`_regen_starter_kit` in DRY_RUN NON deve scrivere docs
    in `inventory_items`. Ritorno deve contenere `applied=False` e
    `would_create_inventory_docs > 0`."""
    seed_guilds(n_guilds=4)

    async def _run():
        pre = await db.inventory_items.count_documents({})
        result = await apply_v1_1._regen_starter_kit(db, "DRY_RUN")
        post = await db.inventory_items.count_documents({})
        return pre, post, result

    pre, post, result = event_loop.run_until_complete(_run())
    assert pre == 0, "pre-state non pulito"
    assert post == 0, f"DRY_RUN ha scritto {post} docs (atteso 0)"
    assert result["applied"] is False
    assert result["would_create_inventory_docs"] == 4
    assert result["quantity_per_doc"] == 3
    assert result["item_id_resolved"] is not None


# ─────────────────────────────────────────────────────────────────────
# t04 — apply_creates_single_inv_row_per_guild
# ─────────────────────────────────────────────────────────────────────
def test_t04_apply_creates_single_inv_row_per_guild(
    db, event_loop, seed_guilds
):
    """Dopo APPLY, deve esserci ESATTAMENTE 1 doc `inventory_items`
    per (guild_id, item_id) — mai piu' di uno."""
    fx = seed_guilds(n_guilds=5)

    async def _run():
        result = await apply_v1_1._regen_starter_kit(db, "APPLY")
        docs_per_guild = {}
        async for d in db.inventory_items.find({}):
            docs_per_guild.setdefault(d["guild_id"], []).append(d)
        return result, docs_per_guild

    result, docs_per_guild = event_loop.run_until_complete(_run())
    assert result["applied"] is True
    assert result["created_inventory_docs"] == 5
    assert set(docs_per_guild.keys()) == set(fx["guild_ids"])
    for gid, docs in docs_per_guild.items():
        assert len(docs) == 1, (
            f"guild {gid} ha {len(docs)} docs invece di 1"
        )


# ─────────────────────────────────────────────────────────────────────
# t05 — apply_quantity_is_3
# ─────────────────────────────────────────────────────────────────────
def test_t05_apply_quantity_is_3(db, event_loop, seed_guilds):
    """Ogni doc `inventory_items` starter kit deve avere `quantity=3`
    (STARTER_KIT_POTIONS). La semantica business e' preservata: ogni
    guild ha 3 pozioni disponibili in un solo record."""
    seed_guilds(n_guilds=4)

    async def _run():
        await apply_v1_1._regen_starter_kit(db, "APPLY")
        return [d async for d in db.inventory_items.find({})]

    docs = event_loop.run_until_complete(_run())
    assert len(docs) == 4
    for d in docs:
        assert d.get("quantity") == 3, f"quantity != 3: {d}"
        assert d.get("item_slug") == "minor_healing_potion"
        assert d.get("r18_reset1b_starter_kit") is True
        assert d.get("r18_reset1b_hotfix_v1_1") is True
        assert d.get("item_id") is not None


# ─────────────────────────────────────────────────────────────────────
# t06 — apply_respects_unique_index (no E11000)
# ─────────────────────────────────────────────────────────────────────
def test_t06_apply_respects_unique_index(
    db, event_loop, seed_guilds
):
    """L'apply NON deve mai violare `inv_guild_item_unique`. Test:
    esegui apply su un DB con l'indice attivo e verifica che
    nessuna eccezione E11000 sia sollevata."""
    seed_guilds(n_guilds=6)

    async def _run():
        # Verifica che l'indice sia attivo
        indexes = await db.inventory_items.index_information()
        assert "inv_guild_item_unique" in indexes, (
            f"Test setup FAIL: indice mancante. Indexes: "
            f"{list(indexes.keys())}"
        )
        assert indexes["inv_guild_item_unique"].get("unique") is True
        # Se il fix e' corretto, questo non solleva DuplicateKeyError
        result = await apply_v1_1._regen_starter_kit(db, "APPLY")
        return result

    result = event_loop.run_until_complete(_run())
    assert result["applied"] is True
    assert result["created_inventory_docs"] == 6


# ─────────────────────────────────────────────────────────────────────
# t07 — idempotency_second_run_noop
# ─────────────────────────────────────────────────────────────────────
def test_t07_idempotency_second_run_noop(db, event_loop, seed_guilds):
    """Un secondo apply su stato gia' popolato NON deve duplicare
    docs (grazie a `$setOnInsert` upsert). `upsert_skipped` deve
    riflettere l'idempotency."""
    seed_guilds(n_guilds=3)

    async def _run():
        r1 = await apply_v1_1._regen_starter_kit(db, "APPLY")
        count_after_first = await db.inventory_items.count_documents({})
        r2 = await apply_v1_1._regen_starter_kit(db, "APPLY")
        count_after_second = await db.inventory_items.count_documents({})
        return r1, count_after_first, r2, count_after_second

    r1, c1, r2, c2 = event_loop.run_until_complete(_run())
    assert r1["created_inventory_docs"] == 3
    assert c1 == 3
    assert r2["created_inventory_docs"] == 0, (
        f"seconda run ha creato {r2['created_inventory_docs']} docs "
        "invece di 0 (idempotency violata)"
    )
    assert r2["upsert_skipped"] == 3
    assert c2 == 3, f"docs totali {c2} != 3 dopo seconda run"


# ─────────────────────────────────────────────────────────────────────
# t08 — double_audit_events_emitted (payload identico)
# ─────────────────────────────────────────────────────────────────────
def test_t08_double_audit_events_emitted(
    db, event_loop, seed_guilds
):
    """`_emit_audit_events` in APPLY deve emettere DUE eventi:
    `APPLIED` + `APPLIED_V1_1`, con `metadata` byte-identico e
    payload esteso richiesto dal PM."""
    seed_guilds(n_guilds=2)

    async def _run():
        summary = {
            "backup": {"created": False},
            "archive": {"collections_touched": 32},
            "wipe": {"collections_wiped": 32},
            "guild_reset": {
                "guilds_target": 2, "guilds_modified": 2
            },
            "roster": {
                "guilds_processed": 2, "total_adv_created": 10
            },
            "kit": {
                "created_inventory_docs": 2,
                "quantity_per_doc": 3,
                "item_id_resolved": "dummy-item-id",
                "upsert_skipped": 0,
            },
        }
        result = await apply_v1_1._emit_audit_events(
            db, "APPLY", summary, "/tmp/fake_manifest.json"
        )
        events = [
            e async for e in db.audit_log.find({}).sort("event_type", 1)
        ]
        return result, events

    result, events = event_loop.run_until_complete(_run())
    assert result["emitted"] is True
    assert len(events) == 2
    event_types = sorted(e["event_type"] for e in events)
    assert event_types == [
        "R18_FULL_GUILD_FRESH_START_APPLIED",
        "R18_FULL_GUILD_FRESH_START_APPLIED_V1_1",
    ]
    # Payload esteso: chiavi obbligatorie
    required_keys = {
        "round", "apply_script", "starter_kit_fix",
        "inventory_unique_index_respected", "hotfix_ref",
        "original_failure", "manifest_path", "apply_id",
        "guild_count", "adv_regen_count", "potions_regen_count",
        "gold_total_after", "completed_at",
    }
    for e in events:
        md = e.get("metadata", {})
        missing = required_keys - set(md.keys())
        assert not missing, f"metadata missing keys: {missing}"
        assert md["hotfix_ref"] == "R18.Reset.1b.hotfix"
        assert md["apply_script"] == "round18_reset1b_apply_v1_1.py"
        assert md["starter_kit_fix"] is True
        assert md["inventory_unique_index_respected"] is True
        assert md["original_failure"].startswith("E11000_step_S7")
    # Payload byte-identico fra i due eventi
    assert events[0]["metadata"] == events[1]["metadata"], (
        "metadata divergente fra APPLIED e APPLIED_V1_1"
    )
    # Stesso apply_id
    assert events[0]["metadata"]["apply_id"] == (
        events[1]["metadata"]["apply_id"]
    )


# ─────────────────────────────────────────────────────────────────────
# t09 — archive_collections_populated (list unchanged vs sealed)
# ─────────────────────────────────────────────────────────────────────
def test_t09_archive_collections_populated():
    """L'array `ARCHIVE_COLLECTIONS` di v1.1 deve essere IDENTICO
    a quello dello sealed (nessun cambio di scope archive)."""
    sealed_src = SEALED_APPLY_PATH.read_text()
    v11_src = V1_1_APPLY_PATH.read_text()

    def _extract(src):
        start = src.index("ARCHIVE_COLLECTIONS = [")
        end = src.index("]", start) + 1
        return src[start:end]

    sealed_block = _extract(sealed_src)
    v11_block = _extract(v11_src)
    assert sealed_block == v11_block, (
        "ARCHIVE_COLLECTIONS divergente vs sealed - "
        "il fix non deve toccare lo scope archive"
    )
    # Sanity: 32 collezioni + guilds separate
    assert len(apply_v1_1.ARCHIVE_COLLECTIONS) == 32


# ─────────────────────────────────────────────────────────────────────
# t10 — rollback_compatible
# ─────────────────────────────────────────────────────────────────────
def test_t10_rollback_compatible():
    """Il rollback script sealed usa lo stesso ARCHIVE_COLLECTIONS
    array + legge audit `R18_FULL_GUILD_FRESH_START_APPLIED`. Il
    v1.1 emette SEMPRE quell'evento (oltre a V1_1), quindi
    rollback funziona senza modifiche."""
    rb_src = ROLLBACK_PATH.read_text()
    # Rollback continua ad essere sealed / unchanged
    assert 'AUDIT_EVENT_APPLIED = "R18_FULL_GUILD_FRESH_START_APPLIED"' in rb_src
    # v1.1 emette l'evento storico
    assert apply_v1_1.AUDIT_EVENT_APPLIED == (
        "R18_FULL_GUILD_FRESH_START_APPLIED"
    )
    # v1.1 usa lo stesso set di collections
    v11_colls = set(apply_v1_1.ARCHIVE_COLLECTIONS)
    # Parse ARCHIVE_COLLECTIONS dal rollback source
    rb_start = rb_src.index("ARCHIVE_COLLECTIONS = [")
    rb_end = rb_src.index("]", rb_start) + 1
    rb_block = rb_src[rb_start:rb_end]
    # Ogni collection del v11 deve apparire nel rollback block
    for coll in v11_colls:
        assert f'"{coll}"' in rb_block, (
            f"collection {coll} presente in v1.1 ma non nel rollback"
        )


# ─────────────────────────────────────────────────────────────────────
# t11 — write_freeze_required (idempotency guard vs re-apply)
# ─────────────────────────────────────────────────────────────────────
def test_t11_write_freeze_required(db, event_loop, seed_guilds):
    """L'idempotency guard `_already_applied` deve tornare True se
    esiste anche solo UNO dei due audit event (APPLIED o V1_1).
    Questo fa sì che un secondo apply venga BLOCCATO — la write
    freeze / re-apply protection e' comportamentale."""
    seed_guilds(n_guilds=1)

    async def _run():
        # Stato pulito: guard False
        pre = await apply_v1_1._already_applied(db)
        # Simula presenza SOLO APPLIED_V1_1
        await db.audit_log.insert_one({
            "id": str(uuid.uuid4()),
            "event_type": "R18_FULL_GUILD_FRESH_START_APPLIED_V1_1",
            "created_at": apply_v1_1._utc_iso(),
        })
        with_v11 = await apply_v1_1._already_applied(db)
        await db.audit_log.delete_many({})
        # Simula presenza SOLO APPLIED (storico)
        await db.audit_log.insert_one({
            "id": str(uuid.uuid4()),
            "event_type": "R18_FULL_GUILD_FRESH_START_APPLIED",
            "created_at": apply_v1_1._utc_iso(),
        })
        with_applied = await apply_v1_1._already_applied(db)
        return pre, with_v11, with_applied

    pre, with_v11, with_applied = event_loop.run_until_complete(_run())
    assert pre is False, "guard e' True su DB pulito (bug)"
    assert with_v11 is True, (
        "guard non blocca re-apply quando APPLIED_V1_1 esiste"
    )
    assert with_applied is True, (
        "guard non blocca re-apply quando APPLIED (storico) esiste"
    )


# ─────────────────────────────────────────────────────────────────────
# t12 — field_cleanup_not_needed
# ─────────────────────────────────────────────────────────────────────
def test_t12_field_cleanup_not_needed(db, event_loop, seed_guilds):
    """Il v1.1 non introduce campi residui/temporanei che
    richiederebbero un ulteriore R18.Reset.1c.cleanup. I doc
    inventory hanno solo campi voluti (`r18_reset1b_starter_kit`,
    `r18_reset1b_hotfix_v1_1`, campi standard). Nessun campo
    'obsoleto' introdotto (es. `null`-only fields o placeholder).
    """
    seed_guilds(n_guilds=2)

    async def _run():
        await apply_v1_1._regen_starter_kit(db, "APPLY")
        return [d async for d in db.inventory_items.find({}, {"_id": 0})]

    docs = event_loop.run_until_complete(_run())
    assert len(docs) == 2
    # Fields esplicitamente attesi
    expected_keys = {
        "id", "guild_id", "item_id", "item_slug", "quantity",
        "r18_reset1b_starter_kit", "r18_reset1b_hotfix_v1_1",
        "created_at",
    }
    for d in docs:
        actual = set(d.keys())
        # No missing
        missing = expected_keys - actual
        assert not missing, f"missing fields: {missing} in {d}"
        # No campi null-only / placeholder (che 1c.cleanup dovrebbe
        # rimuovere post-apply)
        for k, v in d.items():
            if k in ("item_slug",):
                continue
            assert v is not None, (
                f"campo {k}=None (candidato per cleanup post-apply)"
            )
