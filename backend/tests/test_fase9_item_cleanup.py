"""FASE 9M — contratto dello script fase9_old_item_cleanup (parte pura)."""
from app.scripts.fase9_old_item_cleanup import (
    BUILD_FIELDS_ON_ITEM,
    LEGACY_ENGLISH_CLASS_SLUGS,
    SPEC_FIELDS_ON_ADVENTURER,
    _canonical_slugs,
)


def test_cataloghi_canonici_completi():
    slugs = _canonical_slugs()
    # T6 (27×50 class + universali) + 540 set + consumabili/materiali.
    assert len(slugs) >= 1500 + 540
    assert "pietra_della_conoscenza" in slugs
    assert "set_dragon-vault_paladino_weapon" in slugs
    assert "t6_universale_weapon_001" in slugs
    # Gli item firma di specializzazione NON sono canonici.
    assert not any(s.startswith("spec_signature_") for s in slugs)


def test_campi_da_ripulire():
    assert "specialization_slug" in SPEC_FIELDS_ON_ADVENTURER
    assert "specialization" in SPEC_FIELDS_ON_ADVENTURER
    assert "signature_item_id" in SPEC_FIELDS_ON_ADVENTURER
    assert "build_path_id" in BUILD_FIELDS_ON_ITEM
    assert "warrior" in LEGACY_ENGLISH_CLASS_SLUGS
    assert "alchemist" in LEGACY_ENGLISH_CLASS_SLUGS
    # Le 27 classi canoniche italiane NON sono nella lista legacy.
    assert "guerriero" not in LEGACY_ENGLISH_CLASS_SLUGS
    assert "alchimista" not in LEGACY_ENGLISH_CLASS_SLUGS
