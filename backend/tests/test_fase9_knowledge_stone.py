"""FASE 9J — Sigillo XP (Pietra della Conoscenza): copertura totale.

Acceptance del mandato: ALL ACTIVE DUNGEONS → XP SEAL PRESENT.
Ogni completamento dungeon passa dal path legacy o dal finalize a
stanze: entrambi DEVONO usare l'helper condiviso (una sola policy:
20%, solo successo, mai moltiplicata dall'Overpower).
"""
import asyncio
import inspect

from app.dungeons.rooms_blueprints import ROOM_BLUEPRINTS
from app.expeditions import rooms_engine, services as expedition_services
from app.expeditions.knowledge_stone import (
    KNOWLEDGE_STONE_DROP_RATE,
    KNOWLEDGE_STONE_SLUG,
    maybe_roll_knowledge_stone,
)
from app.seeds.seed_fase3_reagenti_consumabili import NEW_CONSUMABLES
from app.shared.content_curve import DUNGEON_CURVE


class _FakeItems:
    def __init__(self, present: bool = True):
        self.present = present
        self.queries = []

    async def find_one(self, query, proj=None):
        self.queries.append(query)
        if self.present:
            return {"id": "stone-item-id"}
        return None


class _FakeDB:
    def __init__(self, present: bool = True):
        self.items = _FakeItems(present)


class _FixedRng:
    def __init__(self, value: float):
        self.value = value

    def random(self) -> float:
        return self.value


def _roll(*, success: bool, rng_value: float, present: bool = True):
    return asyncio.run(maybe_roll_knowledge_stone(
        _FakeDB(present), success=success, rng=_FixedRng(rng_value),
    ))


def test_identificatore_e_effetto_canonici():
    stone = next(
        c for c in NEW_CONSUMABLES if c["slug"] == KNOWLEDGE_STONE_SLUG
    )
    assert stone["name"] == "Pietra della Conoscenza"
    assert stone["rarity"] == "Rare"
    assert stone["craftable"] is False
    effect = stone["consumable_effect"]
    assert effect["type"] == "xp_boost"
    assert effect["magnitude"] == 0.5   # +50% XP
    assert effect["charges"] == 5       # per 5 spedizioni


def test_policy_di_drop_canonica():
    assert KNOWLEDGE_STONE_DROP_RATE == 0.20
    # 20%: sotto soglia droppa, sopra no.
    assert _roll(success=True, rng_value=0.19) == "stone-item-id"
    assert _roll(success=True, rng_value=0.20) is None
    # Mai su fallimento (il tiro non viene nemmeno consumato).
    assert _roll(success=False, rng_value=0.0) is None
    # Seed fase 3 assente: nessun crash, solo niente pietra.
    assert _roll(success=True, rng_value=0.0, present=False) is None


def test_query_filtra_su_slug_attivo():
    db = _FakeDB()
    asyncio.run(maybe_roll_knowledge_stone(
        db, success=True, rng=_FixedRng(0.0),
    ))
    assert db.items.queries == [
        {"slug": KNOWLEDGE_STONE_SLUG, "is_active": True},
    ]


def test_entrambi_i_path_di_completamento_usano_l_helper():
    """Copertura TOTALE: legacy + stanze chiamano la policy condivisa,
    e nessuno dei due reimplementa un tiro locale."""
    legacy_src = inspect.getsource(expedition_services)
    rooms_src = inspect.getsource(rooms_engine)
    assert "maybe_roll_knowledge_stone" in legacy_src
    assert "maybe_roll_knowledge_stone" in rooms_src
    # Il vecchio inline (find_one diretto sullo slug) non deve esistere più.
    assert legacy_src.count(f'"{KNOWLEDGE_STONE_SLUG}"') == 0
    assert rooms_src.count(f'"{KNOWLEDGE_STONE_SLUG}"') == 0


def test_tutti_i_dungeon_attivi_sono_coperti():
    """Ogni dungeon della curva canonica ha un blueprint a stanze
    (finalize a stanze) e in ogni caso il path legacy copre qualunque
    completamento non-stanze: la Pietra è quindi nel pool di TUTTI."""
    curve_slugs = set(DUNGEON_CURVE)
    blueprint_slugs = set(ROOM_BLUEPRINTS)
    missing = curve_slugs - blueprint_slugs
    # training-yard (tutorial) è l'unico ammesso fuori dalle stanze:
    # viene comunque coperto dal path legacy condiviso.
    assert missing <= {"training-yard"}, missing
