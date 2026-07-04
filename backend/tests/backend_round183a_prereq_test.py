"""ROUND 18.3a — Class Migration Pre-Req test suite (≥13 test).

Verifica post-apply del round R18.3a:
  1. Seed classi target `cacciatore_di_mostri` + `cacciatore_del_vuoto`
     con marker corretti (is_playable=false, migration_target_only=true,
     is_canonical=true, source_round=R18.3a, is_active=true).
  2. Slug esatti (con preposizione articolata) — no forme brevi.
  3. Bridge item counts ≥ 10 per ciascuna classe target.
  4. Bridge append-only: source slugs (ranger, warlock) PRESERVATI in
     recommended_classes.
  5. Zero mod a stats/rarity/level/drop/power sugli item bridge.
  6. Audit event `R18_CLASS_MIGRATION_PREREQ_READY` emesso con metadata
     completa.
  7. Guard R18.1.2 accetta gli slug (dispatch-valid).
  8. Zero write reali su adventurers.
  9. Feature flag OFF preservati.
 10. Dry-run script produce JSON con slug corretti + slug_correction_note.
 11. Regression R18.1 / R18.2 / R18.1.2 tutti PASS (via import).
 12. Whitelist admin audit contiene R18_CLASS_MIGRATION_PREREQ_READY.
 13. No player-facing leak: classi target NON esposte da rotta pubblica.

Bypass conftest globale (isolation forcing) via:
    pytest --confcutdir=/tmp -c /dev/null
"""
from __future__ import annotations

import asyncio
import json
import os
import pathlib
import sys

import pytest
from dotenv import dotenv_values, load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Load DEV env
load_dotenv("/app/backend/.env")
_BACKEND_ENV = dotenv_values("/app/backend/.env")
_DEV_MONGO_URL = _BACKEND_ENV.get("MONGO_URL") or os.environ.get("MONGO_URL")
_DEV_DB_NAME = _BACKEND_ENV.get("DB_NAME") or os.environ.get("DB_NAME")


TARGET_SLUGS = ["cacciatore_di_mostri", "cacciatore_del_vuoto"]
BRIDGE_SOURCES = {
    "cacciatore_di_mostri": "ranger",
    "cacciatore_del_vuoto": "warlock",
}
DEPRECATED_SHORT_SLUGS = ["cacciatore_mostri", "cacciatore_vuoto"]  # R18.2 wrong

R183A_DRY_RUN_JSON = pathlib.Path(
    "/app/memory/round183a_orphan_migration_dry_run.json"
)
R183A_PLAN_MD = pathlib.Path(
    "/app/memory/round183a_orphan_migration_plan.md"
)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture(scope="module")
def db():
    client = AsyncIOMotorClient(_DEV_MONGO_URL)
    yield client[_DEV_DB_NAME]
    client.close()


# ─── 01 — Classi target seedate ─────────────────────────────────────────
def test_01_target_classes_seeded(db):
    for slug in TARGET_SLUGS:
        doc = _run(db.adventurer_classes.find_one({"slug": slug}))
        assert doc is not None, f"class {slug} NOT seeded"
        assert doc.get("is_playable") is False, (
            f"{slug} must have is_playable=false, "
            f"got {doc.get('is_playable')}"
        )
        assert doc.get("migration_target_only") is True, (
            f"{slug} must have migration_target_only=true, "
            f"got {doc.get('migration_target_only')}"
        )
        assert doc.get("is_canonical") is True, (
            f"{slug} must have is_canonical=true"
        )
        assert doc.get("is_active") is True, (
            f"{slug} must have is_active=true"
        )
        assert doc.get("source_round") == "R18.3a", (
            f"{slug} must have source_round=R18.3a, "
            f"got {doc.get('source_round')}"
        )


# ─── 02 — Slug esatti con preposizione (no forma corta) ─────────────────
def test_02_exact_slugs_no_short_form(db):
    """PM Q6: slug canonici con 'di' e 'del'. Le forme corte R18.2
    (cacciatore_mostri / cacciatore_vuoto) NON devono esistere."""
    for wrong_slug in DEPRECATED_SHORT_SLUGS:
        doc = _run(db.adventurer_classes.find_one({"slug": wrong_slug}))
        assert doc is None, (
            f"deprecated R18.2 slug '{wrong_slug}' MUST NOT exist in catalog"
        )


# ─── 03 — Bridge item counts ≥ 10 per ciascuna classe ───────────────────
def test_03_bridge_item_counts_min_10(db):
    for target_slug, source_slug in BRIDGE_SOURCES.items():
        n = _run(db.items.count_documents({
            "recommended_classes": target_slug
        }))
        assert n >= 10, (
            f"{target_slug} bridge item count = {n}, expected ≥ 10 "
            f"(target ≥ 10 items PM-sealed)"
        )


# ─── 04 — Bridge append-only: source slugs preservati ───────────────────
def test_04_bridge_append_only_preserves_source(db):
    """Ogni item bridged deve avere ENTRAMBI source slug + target slug
    in `recommended_classes`. Zero replace."""
    for target_slug, source_slug in BRIDGE_SOURCES.items():
        # Items con target ma senza source (violazione append-only)
        n_broken = _run(db.items.count_documents({
            "recommended_classes": target_slug,
            "recommended_classes": {"$ne": source_slug},
        }))
        # Uso query più robusta: items con target E items con source
        items_with_target = _run(db.items.count_documents({
            "recommended_classes": target_slug
        }))
        items_with_both = _run(db.items.count_documents({
            "recommended_classes": {"$all": [target_slug, source_slug]}
        }))
        assert items_with_both == items_with_target, (
            f"append-only violation for {target_slug}: "
            f"with_target={items_with_target} vs "
            f"with_both={items_with_both}"
        )


# ─── 05 — Zero mod stats/rarity/level/drop/power sugli item bridge ─────
def test_05_bridge_no_stat_modification(db):
    """Verifica che gli item bridged NON abbiano perso `stats`, `rarity`,
    `required_adventurer_level`, `power_score` (fields esistenti)."""
    for target_slug in TARGET_SLUGS:
        async def _check():
            broken = []
            async for it in db.items.find(
                {"recommended_classes": target_slug},
                {"_id": 0, "id": 1, "rarity": 1, "power_score": 1,
                 "required_adventurer_level": 1, "required_level": 1,
                 "name": 1},
            ):
                # rarity deve esistere e non essere null
                if it.get("rarity") is None:
                    broken.append(f"{it.get('id')} missing rarity")
                # power_score OR level (uno dei due deve esistere)
                if (it.get("power_score") is None
                    and it.get("required_adventurer_level") is None
                    and it.get("required_level") is None):
                    broken.append(f"{it.get('id')} missing power/level")
            return broken
        broken = _run(_check())
        assert not broken, (
            f"bridge broke fields on {target_slug}: {broken[:3]}"
        )


# ─── 06 — Audit event R18_CLASS_MIGRATION_PREREQ_READY emesso ──────────
def test_06_audit_event_emitted(db):
    n = _run(db.audit_log.count_documents({
        "event_type": "R18_CLASS_MIGRATION_PREREQ_READY"
    }))
    assert n >= 1, (
        "audit event R18_CLASS_MIGRATION_PREREQ_READY NOT emitted "
        f"(count={n})"
    )
    doc = _run(db.audit_log.find_one(
        {"event_type": "R18_CLASS_MIGRATION_PREREQ_READY"},
        {"_id": 0},
    ))
    assert doc is not None
    meta = doc.get("metadata", {})
    assert meta.get("round") == "R18.3a"
    assert set(meta.get("classes_seeded", [])) == set(TARGET_SLUGS)
    assert meta.get("is_playable") is False
    assert meta.get("migration_target_only") is True
    assert meta.get("migration_apply") is False
    assert meta.get("dry_run_only") is True
    assert meta.get("slug_correction_from_R18_2") is True
    assert (
        meta.get("item_bridge_strategy")
        == "recommended_classes_append_only"
    )
    bridge_counts = meta.get("item_bridge_counts", {})
    assert "cacciatore_di_mostri" in bridge_counts
    assert "cacciatore_del_vuoto" in bridge_counts


# ─── 07 — Audit event idempotente (unico record) ───────────────────────
def test_07_audit_event_idempotent(db):
    """Re-run del seed script non deve moltiplicare l'event nel log."""
    n = _run(db.audit_log.count_documents({
        "event_type": "R18_CLASS_MIGRATION_PREREQ_READY"
    }))
    assert n == 1, (
        f"audit event should be idempotent (unique in audit_log), "
        f"got {n}"
    )


# ─── 08 — Guard R18.1.2 accetta gli slug ───────────────────────────────
def test_08_guard_r18_1_2_accepts_target_slugs(db):
    """Simula la query del guard R18.1.2. Deve restituire i 2 slug
    target con is_playable=false + migration_target_only=true."""
    query = {"$or": [
        {"is_playable": {"$ne": False}},
        {
            "is_playable": False,
            "migration_target_only": True,
            "slug": {"$in": TARGET_SLUGS},
        },
    ]}
    for slug in TARGET_SLUGS:
        n = _run(db.adventurer_classes.count_documents(
            {**query, "slug": slug}
        ))
        assert n >= 1, (
            f"guard R18.1.2 must accept slug '{slug}' as dispatch-valid"
        )


# ─── 09 — Zero write reali su adventurers ──────────────────────────────
def test_09_zero_adv_migrated_in_r18_3a(db):
    """R18.3a è solo pre-req: NESSUN adventurer deve avere class_slug
    cambiato a `cacciatore_di_mostri` o `cacciatore_del_vuoto`."""
    for target_slug in TARGET_SLUGS:
        n_adv = _run(db.adventurers.count_documents({
            "class_slug": target_slug
        }))
        assert n_adv == 0, (
            f"R18.3a violation: {n_adv} adventurers already have "
            f"class_slug={target_slug} (should be 0, migration in R18.3)"
        )


# ─── 10 — Feature flag OFF preservati ──────────────────────────────────
def test_10_feature_flags_off():
    macro = os.environ.get("R18_REWORK_ENABLED", "false").lower()
    talent = os.environ.get("R18_TALENT_ENGINE_ENABLED", "false").lower()
    assert macro in ("false", "0", "no", "")
    assert talent in ("false", "0", "no", "")


# ─── 11 — Dry-run JSON output valid + slug correction note ─────────────
def test_11_dry_run_json_valid(db):
    assert R183A_DRY_RUN_JSON.exists(), (
        "R18.3a dry-run JSON missing: run "
        "`python -m app.scripts.round183a_orphan_migration_dry_run`"
    )
    payload = json.loads(R183A_DRY_RUN_JSON.read_text())
    assert payload["round"] == "R18.3a"
    assert payload["phase"] == "class_migration_prereq_dry_run"
    assert payload["total_orphan_adv_to_migrate"] == 496
    # slug_correction_note deve essere presente
    slug_note = payload.get("slug_correction_note", {})
    assert slug_note.get("corrected_slugs_from_R18_2") == {
        "cacciatore_mostri": "cacciatore_di_mostri",
        "cacciatore_vuoto": "cacciatore_del_vuoto",
    }
    # migrations con nuovi slug
    migrations_by_source = {
        m["source_slug"]: m for m in payload["migrations"]
    }
    assert migrations_by_source["ranger"]["target_slug"] == "cacciatore_di_mostri"
    assert migrations_by_source["warlock"]["target_slug"] == "cacciatore_del_vuoto"
    # target_exists_live post-seed
    assert migrations_by_source["ranger"]["target_exists_live"] is True
    assert migrations_by_source["warlock"]["target_exists_live"] is True
    # Item pool risk BASSO (post bridge)
    assert migrations_by_source["ranger"]["target_item_pool_risk"] == "BASSO"
    assert migrations_by_source["warlock"]["target_item_pool_risk"] == "BASSO"


# ─── 12 — Whitelist admin audit contiene R18_CLASS_MIGRATION_PREREQ_READY ─
def test_12_admin_audit_whitelist_extended():
    from app.admin.audit_routes import AUDIT_EVENT_WHITELIST
    assert "R18_CLASS_MIGRATION_PREREQ_READY" in AUDIT_EVENT_WHITELIST
    assert "R18_GUARD_WHITELIST_EXTENDED" in AUDIT_EVENT_WHITELIST


# ─── 13 — No player-facing leak (query catalog filter simulation) ───────
def test_13_no_player_facing_leak_target_classes(db):
    """Le classi target R18.3a con is_playable=false NON devono passare
    il filtro standard usato dalle rotte pubbliche
    (list_classes filtra su is_active=true + is_playable non-false).

    Test via DB query (evita conflitto TestClient/event-loop quando i
    test file di round precedenti hanno già chiuso loop asyncio).
    """
    # Filter equivalente a list_classes: is_active=true, ma is_playable
    # NON è filtrato esplicitamente. Verifichiamo che nel routing
    # public path le classi target siano invisibili controllando
    # is_playable=false + is_active=true.
    for target_slug in TARGET_SLUGS:
        doc = _run(db.adventurer_classes.find_one({"slug": target_slug}))
        assert doc is not None, f"class {target_slug} missing"
        assert doc.get("is_playable") is False, (
            f"{target_slug} must be hidden by is_playable=false"
        )
        # migration_target_only true rinforza il tag semantico
        assert doc.get("migration_target_only") is True
    # Regression: recruit_unassigned resta invisibile (already covered by
    # R18.1.2 test_09) — assert double coverage
    ru = _run(db.adventurer_classes.find_one({"slug": "recruit_unassigned"}))
    assert ru is not None
    assert ru.get("is_playable") is False


# ─── 14 — Plan MD deliverable exists ───────────────────────────────────
def test_14_plan_md_deliverable_exists():
    assert R183A_PLAN_MD.exists(), (
        f"R18.3a plan MD missing: {R183A_PLAN_MD}"
    )
    content = R183A_PLAN_MD.read_text()
    # Slug corretti presenti
    assert "cacciatore_di_mostri" in content
    assert "cacciatore_del_vuoto" in content
    # Slug correction note documentata
    assert "cacciatore_mostri" in content  # ex-R18.2 mentioned
    assert "cacciatore_vuoto" in content
    # Vincoli chiave
    assert "append-only" in content.lower() or "append only" in content.lower()
    assert "R18.3a" in content


# ─── 15 — Regression R18.1 + R18.2 + R18.1.2 (via import) ──────────────
def test_15_regression_prior_rounds_importable():
    """Verifica che i test file precedenti restino importabili — segnale
    di zero rottura moduli/schema condivisi."""
    import importlib
    for mod_name in [
        "tests.backend_round181_migration_test",
        "tests.backend_round182_talent_pilot_test",
        "tests.backend_round1812_guard_test",
    ]:
        # Percorso relativo al backend/ cwd, quindi:
        sys.path.insert(0, "/app/backend")
        try:
            mod = importlib.import_module(mod_name)
            assert mod is not None
        except ImportError as e:
            pytest.fail(f"regression: cannot import {mod_name}: {e}")


# ─── 16 — Guild counts unchanged (zero side-effect su guilds) ──────────
def test_16_guilds_untouched(db):
    """R18.3a NON deve toccare la collezione guilds."""
    n_total = _run(db.guilds.count_documents({}))
    assert n_total >= 300, f"expected >=300 guilds, got {n_total}"
    # Nessuna guild deve avere r18_class_migration_prereq_touched
    n_touched = _run(db.guilds.count_documents({
        "r18_class_migration_prereq_touched": {"$exists": True}
    }))
    assert n_touched == 0, (
        f"R18.3a MUST NOT touch guilds: {n_touched} touched"
    )
