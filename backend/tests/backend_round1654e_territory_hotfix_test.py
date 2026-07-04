"""ROUND 16.5.4e HOTFIX — Territory `KeyError: 'library'` defensive fallback.

Root cause: `get_structure_max_level(slug)` faceva un lookup diretto
`STRUCTURE_CATALOG[slug]` senza guard. Alcuni documenti `guild_structures`
legacy contengono slug (es. `library`) che sono stati rimossi dal catalog
in un refactor storico; ogni `GET /api/territory/my` per queste gilde
crashava con `KeyError: 'library'` in `_public_doc` → `get_structure_max_level`.

Fix (`app/territory/structures.py::get_structure_max_level`): sostituito
`STRUCTURE_CATALOG[slug]` con `STRUCTURE_CATALOG.get(slug)` + fallback a
`0` con log WARN una-tantum. Slug sconosciuti restano nella response
(non li nascondiamo) ma senza `next_level_cost`, quindi non upgradabili
via user — corretto per legacy data.
"""
from __future__ import annotations

import logging

import pytest

from app.territory import services as territory_services
from app.territory.structures import (
    STRUCTURE_CATALOG,
    get_structure_max_level,
)


# ─────────────────────────────────────────────────────────────────────
# Unit test — get_structure_max_level fallback
# ─────────────────────────────────────────────────────────────────────

def test_get_structure_max_level_known_slug_returns_catalog_value():
    """Sanity check: slug conosciuti (`guild_hall`) restituiscono il valore
    definito in `STRUCTURE_CATALOG` (nessuna regressione dal fix)."""
    assert "guild_hall" in STRUCTURE_CATALOG
    expected = int(STRUCTURE_CATALOG["guild_hall"]["max_level"])
    assert get_structure_max_level("guild_hall") == expected
    # dormitories con `allow_legacy` deve continuare a funzionare
    assert get_structure_max_level("dormitories", allow_legacy=False) == 11
    assert get_structure_max_level("dormitories", allow_legacy=True) == 11


def test_get_structure_max_level_unknown_slug_no_keyerror():
    """HOTFIX check: slug sconosciuto NON deve più lanciare KeyError."""
    # Verifica esplicitamente che `library` (slug legacy dropped) sia
    # assente dal catalog attuale (base ipotesi del root cause).
    assert "library" not in STRUCTURE_CATALOG
    # Chiamata sotto test: pre-fix lanciava KeyError, post-fix ritorna 0.
    result = get_structure_max_level("library")
    assert result == 0, (
        f"expected 0 sentinel for unknown slug, got {result!r}"
    )


def test_get_structure_max_level_unknown_slug_with_legacy_flag_no_keyerror():
    """HOTFIX check: allow_legacy=True su slug sconosciuto non deve
    accedere al catalog inesistente (nessuna eccezione)."""
    result = get_structure_max_level("library", allow_legacy=True)
    assert result == 0
    # Anche altri slug fantasma
    assert get_structure_max_level("cursed-atlas-hall") == 0
    assert get_structure_max_level("") == 0


def test_get_structure_max_level_unknown_slug_emits_warning(caplog):
    """HOTFIX check: viene emesso un WARN quando lo slug è sconosciuto,
    così l'ops team può poi decidere di ripulire i doc legacy."""
    caplog.set_level(logging.WARNING, logger="orbus.territory")
    _ = get_structure_max_level("library")
    warns = [
        r for r in caplog.records
        if r.levelno == logging.WARNING
        and "unknown structure slug" in r.getMessage()
        and "'library'" in r.getMessage()
    ]
    assert warns, (
        f"expected a WARN log for unknown slug 'library', "
        f"got records: {[r.getMessage() for r in caplog.records]}"
    )


# ─────────────────────────────────────────────────────────────────────
# Integration test — `_public_doc` non crasha su doc legacy con slug orfano
# ─────────────────────────────────────────────────────────────────────

def test_public_doc_survives_legacy_orphan_slug():
    """Root cause path replay: un doc `guild_structures` con uno slug
    orfano (`library` Lv1) doveva causare `KeyError` in `_public_doc`
    tramite `get_structure_max_level`. Post-fix il payload esce intero,
    con la struttura orfana presente ma priva di `next_level_cost`.
    """
    legacy_doc = {
        "id": "test-guild-legacy-1",
        "guild_id": "guild-legacy-1",
        "structures": {
            # Struttura reale, upgradabile.
            "guild_hall": {
                "level": 2,
                "is_unlocked": True,
                "purchased_at": None,
                "upgraded_at": None,
                "acquired_via": "default",
            },
            # Struttura fantasma legacy che pre-fix crashava.
            "library": {
                "level": 1,
                "is_unlocked": True,
                "purchased_at": None,
                "upgraded_at": None,
                "acquired_via": "migration",
            },
        },
        "created_at": None,
        "updated_at": None,
    }

    # Pre-fix: KeyError. Post-fix: dict pulito.
    payload = territory_services._public_doc(legacy_doc)

    assert payload["id"] == "test-guild-legacy-1"
    assert "structures" in payload
    assert "guild_hall" in payload["structures"]
    assert "library" in payload["structures"], (
        "orphan slug deve rimanere nella response per non alterare la "
        "shape client (only next_level_cost è None)"
    )
    # Slug valido → potenziale upgrade calcolato
    gh = payload["structures"]["guild_hall"]
    assert gh["level"] == 2
    # Slug orfano → next_level_cost None (max_lv=0, cur_level=1, 1 < 0 False)
    lib = payload["structures"]["library"]
    assert lib["level"] == 1
    assert lib.get("next_level_cost") is None, (
        f"expected next_level_cost=None for orphan slug, "
        f"got {lib.get('next_level_cost')!r}"
    )


def test_public_doc_no_crash_when_all_slugs_are_orphan():
    """Edge case estremo: doc composto da soli slug orfani (dopo un
    refactor che elimina tutte le strutture del catalog storico).
    Deve restituire una response valida senza `next_level_cost` su
    nessun campo."""
    payload = territory_services._public_doc({
        "id": "t-1", "guild_id": "g-1", "structures": {
            "library": {"level": 3, "is_unlocked": True,
                        "purchased_at": None, "upgraded_at": None,
                        "acquired_via": "migration"},
            "arcane_lab": {"level": 1, "is_unlocked": True,
                           "purchased_at": None, "upgraded_at": None,
                           "acquired_via": "migration"},
        },
        "created_at": None, "updated_at": None,
    })
    for slug in ("library", "arcane_lab"):
        assert slug in payload["structures"]
        assert payload["structures"][slug]["next_level_cost"] is None
