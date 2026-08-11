"""FASE 9 A4 — 6 fondatori gratuiti iniziali, senza classe.

Contratto puro (niente Mongo):
  * STARTER_TARGET = 6 e le tuple nomi/identità sono lunghe 6;
  * ogni identità usa uno slug razza REALE del seed Round 16.0
    (il quinto+1 fondatore aveva rischiato "dragonborn", slug inesistente);
  * FREE_FOUNDER_COUNT (costo reclutamento) resta allineato;
  * i primi 6 sono gratis, il settimo paga.
"""
from app.onboarding.services import (
    STARTER_IDENTITIES,
    STARTER_NAMES,
    STARTER_TARGET,
)
from app.recruitment.base_models import (
    FREE_FOUNDER_COUNT,
    base_model_cost_for_created_total,
)
from app.scripts.round160_seed_races import RACES


def test_sei_fondatori_iniziali():
    assert STARTER_TARGET == 6
    assert len(STARTER_NAMES) == 6
    assert len(STARTER_IDENTITIES) == 6
    assert len(set(STARTER_NAMES)) == 6


def test_identita_starter_usano_razze_reali():
    valid_slugs = {r["slug"] for r in RACES}
    for race_slug, gender in STARTER_IDENTITIES:
        assert race_slug in valid_slugs, f"slug razza inesistente: {race_slug}"
        assert gender in ("male", "female")


def test_free_founder_count_allineato():
    assert FREE_FOUNDER_COUNT == STARTER_TARGET == 6


def test_costo_reclutamento_parte_dal_settimo():
    for created in range(6):
        assert base_model_cost_for_created_total(created) == 0
    assert base_model_cost_for_created_total(6) > 0
