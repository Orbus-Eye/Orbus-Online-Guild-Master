"""FASE 10A — P0: scelta classe del nuovo avventuriero.

Root cause del bug tester: /class-halls/assignment/choices ha cambiato
shape in FASE 9 (class_mechanic senza ``builds``) e la UI della scelta
classe crashava in render. Questi test congelano il contratto payload
lato backend e verificano l'assegnazione end-to-end (mock) per le 5
classi richieste dal mandato (DPS / TANK / HEALER, slug diversi).
"""
from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

# Stesso shim dei test journey esistenti: servono solo i moduli service.
_APP_ROOT = Path(__file__).resolve().parents[1] / "app"
for _domain in ("adventurers", "class_halls", "equipment", "recruitment"):
    _name = f"app.{_domain}"
    if _name not in sys.modules:
        _package = ModuleType(_name)
        _package.__path__ = [str(_APP_ROOT / _domain)]
        sys.modules[_name] = _package

from app.class_halls.catalog import class_hall_choices_public
from app.class_halls.journey import confirm_class_hall_assignment
from app.classes import class_role_for

NOW = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)

# Le 5 classi del mandato: coprono i 3 ruoli e slug multi-parola.
MANDATED_CLASSES = [
    ("hall_guerriero", "guerriero", "DPS"),
    ("hall_paladino", "paladino", "TANK"),
    ("hall_alchimista", "alchimista", "HEALER"),
    ("hall_astrologo", "astrologo", "HEALER"),
    ("hall_cavaliere_di_draghi", "cavaliere_di_draghi", "TANK"),
]


def test_choices_payload_contract_is_build_free_and_ui_safe() -> None:
    """Il contratto che la UI della scelta classe renderizza: 27 Sale,
    class_mechanic SENZA builds e CON resonance_tags. È esattamente il
    punto rotto dal P0 (FE faceva class_mechanic.builds.map)."""
    choices = class_hall_choices_public()
    assert len(choices) == 27
    for choice in choices:
        mechanic = choice["class_mechanic"]
        assert mechanic is not None, choice["hall_id"]
        assert "builds" not in mechanic, choice["hall_id"]
        assert isinstance(mechanic["resonance_tags"], list)
        assert mechanic["resonance_tags"], choice["hall_id"]
        assert mechanic["name_it"]
        assert mechanic["summary_it"]
        # Campi che la card della Sala mostra sempre.
        for field in (
            "class_name_it",
            "hall_name_it",
            "hall_master_witness_npc",
            "starter_item_name_it",
            "lore_hook_it",
            "gameplay_style_it",
            "primary_stat",
            "trial_steps",
            "wave",
        ):
            assert choice.get(field), f"{choice['hall_id']}: {field}"
        # Ruolo canonico del registry, mai la vecchia tassonomia.
        assert choice["class_role"] in {"DPS", "TANK", "HEALER"}


@pytest.mark.parametrize(
    ("hall_id", "class_slug", "expected_role"), MANDATED_CLASSES
)
def test_new_adventurer_receives_class_and_fixed_role(
    hall_id: str, class_slug: str, expected_role: str
) -> None:
    assert class_role_for(class_slug) == expected_role

    async def go() -> None:
        classless = {
            "id": "adv-new",
            "guild_id": "guild-1",
            "name": "Recluta",
            "adventurer_class_id": None,
            "class_name": None,
            "class_role": None,
            "class_proficiency": None,
            "class_slug": None,
            "canonical_class_slug": None,
            "class_hall_id": None,
            "recruit_status": "recruit_unassigned",
            "level": 1,
        }
        assigned = {
            **classless,
            "class_slug": class_slug,
            "canonical_class_slug": class_slug,
            "class_hall_id": hall_id,
            "recruit_status": "class_assigned",
            "class_assignment_id": "assignment-1",
            "starter_item_reward_status": "pending",
        }
        delivered = {**assigned, "starter_item_reward_status": "delivered"}
        db = SimpleNamespace(
            adventurers=AsyncMock(),
            class_hall_trial_sessions=AsyncMock(),
            adventurer_classes=AsyncMock(),
            items=AsyncMock(),
            class_hall_reward_grants=AsyncMock(),
            inventory_items=AsyncMock(),
        )
        db.adventurers.find_one.side_effect = [classless, delivered]
        db.adventurers.find_one_and_update.return_value = assigned
        db.class_hall_trial_sessions.find_one.return_value = {
            "id": "trial-1",
            "completed_at": NOW.isoformat(),
        }
        db.adventurer_classes.find_one.return_value = {
            "id": f"class-{class_slug}",
            "slug": class_slug,
        }
        db.items.find_one.return_value = {
            "id": "item-starter",
            "slug": f"hall_{class_slug}_starter",
            "name_it": "Item di Lore",
        }
        db.inventory_items.find_one.return_value = None
        db.inventory_items.update_one.return_value = SimpleNamespace(
            matched_count=0
        )

        with (
            patch(
                "app.class_halls.journey.assignment_enabled_for_hall",
                return_value=True,
            ),
            patch("app.class_halls.journey.write_audit", new=AsyncMock()),
        ):
            result = await confirm_class_hall_assignment(
                db,
                guild_id="guild-1",
                adventurer_id="adv-new",
                hall_id=hall_id,
                trial_id="trial-1",
                explicit_confirmation=True,
                actor_user_id="user-1",
            )

        assert result["idempotent"] is False
        update = db.adventurers.find_one_and_update.await_args.args[1]
        # La classe scelta e il RUOLO FISSO canonico vengono scritti insieme.
        assert update["$set"]["canonical_class_slug"] == class_slug
        assert update["$set"]["class_hall_id"] == hall_id
        assert update["$set"]["class_role"] == expected_role
        assert update["$set"]["class_assignment_status"] == "COMMITTED"

    asyncio.run(go())
