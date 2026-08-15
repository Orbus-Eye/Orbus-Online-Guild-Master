"""FASE 10B — censimento IT dei nomi Dungeon/Raid player-facing.

Regola: gli slug/enum/campi API restano invariati; cambia SOLO la
rappresentazione mostrata al giocatore. Il backend è la fonte
autoritativa del nome italiano (``app.content.display_names``), anche
per i documenti legacy che hanno persistito solo il nome inglese.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.content.display_names import (
    dungeon_display_name_it,
    raid_display_name_it,
)
from app.content.lore_meta import DUNGEON_LORE_PATCHES, RAID_LORE_PATCHES
from app.core.email_templates import render_welcome
from app.expeditions.report_builder import build_expedition_report
from app.expeditions.services import expedition_public
from app.raids import raid_public
from app.seeds.seed_data import DUNGEON_SEED
from app.seeds.seed_round5 import DUNGEON_5P_SEED, RAID_DUNGEON_SEED


def test_ogni_dungeon_seedato_ha_un_nome_italiano() -> None:
    """Censimento: nessun dungeon del catalogo può restare col nome EN."""
    for row in [*DUNGEON_SEED, *DUNGEON_5P_SEED]:
        italian = dungeon_display_name_it(slug=row["slug"], name=row["name"])
        assert italian, row["slug"]
        assert italian != row["name"], (
            f"{row['slug']} mostra ancora il nome inglese: {row['name']}"
        )


def test_ogni_raid_ha_un_nome_italiano() -> None:
    for row in RAID_DUNGEON_SEED:
        italian = raid_display_name_it(slug=row["slug"], name=row["name"])
        assert italian and italian != row["name"], row["slug"]
    # I raid R113 sono coperti dalle patch lore per slug.
    for slug in RAID_LORE_PATCHES:
        assert raid_display_name_it(slug=slug) != slug


def test_patch_lore_dungeon_hanno_tutte_name_it() -> None:
    missing = [
        slug for slug, patch in DUNGEON_LORE_PATCHES.items()
        if not patch.get("name_it")
    ]
    assert missing == []


def test_expedition_public_espone_nome_it_anche_sui_doc_legacy() -> None:
    """Acceptance del mandato: 'Dungeon completato: Tane dei Goblin',
    MAI 'Goblin Warrens' — anche per spedizioni persistite pre-FASE 10."""
    now = datetime.now(timezone.utc)
    legacy = {
        "id": "exp-legacy",
        "guild_id": "g-1",
        "dungeon_id": "d-1",
        "dungeon_name": "Goblin Warrens",  # nessun campo IT persistito
        "status": "completed",
        "completed_at": now.isoformat(),
        "created_at": now.isoformat(),
    }
    out = expedition_public(legacy)
    assert out["dungeon_name"] == "Goblin Warrens"  # campo API invariato
    assert out["dungeon_name_it"] == "Tane dei Goblin"

    fresh = dict(legacy, id="exp-new", dungeon_slug="shadow-crypts",
                 dungeon_name="Shadow Crypts",
                 dungeon_name_it="Cripte d'Ombra")
    assert expedition_public(fresh)["dungeon_name_it"] == "Cripte d'Ombra"


def test_raid_public_espone_nome_it_anche_sui_doc_legacy() -> None:
    now = datetime.now(timezone.utc)
    legacy = {
        "id": "raid-legacy",
        "guild_id": "g-1",
        "raid_dungeon_slug": "moonfall-vigil",  # nessun nome persistito
        "status": "in_progress",
        "team_power_combined": 1000,
        "recommended_power_combined": 900,
        "success_chance_combined": 70,
        "started_at": now.isoformat(),
        "ends_at": (now + timedelta(hours=1)).isoformat(),
    }
    out = raid_public(legacy)
    assert out["raid_name_it"] == "Veglia della Luna Infranta"
    assert out["raid_dungeon_slug"] == "moonfall-vigil"  # slug invariato


def test_narrativa_report_it_usa_il_nome_italiano() -> None:
    now = datetime.now(timezone.utc)
    exp = {
        "id": "exp-1",
        "guild_id": "g-1",
        "dungeon_id": "d-1",
        "dungeon_name": "Goblin Warrens",
        "status": "completed",
        "result_summary": "Success",
        "final_team_power": 100,
        "success_chance": 80,
        "gold_reward": 10,
        "xp_reward": 10,
        "completed_at": now.isoformat(),
    }
    dungeon = {"id": "d-1", "slug": "goblin-warrens",
               "name": "Goblin Warrens", "recommended_power": 45}
    report = build_expedition_report(
        exp=exp, members=[], dungeon=dungeon, loot_items=[],
    )
    summary = report["report_summary"]
    assert "Tane dei Goblin" in summary["narrative_summary"]
    assert "Goblin Warrens" not in summary["narrative_summary"]
    # narrative_it può non citare il nome (ramo overpower), ma se lo
    # cita non può essere quello inglese.
    assert "Goblin Warrens" not in summary["narrative_it"]


def test_email_benvenuto_it_senza_nomi_inglesi() -> None:
    subject, html, text = render_welcome(
        "it", "https://orbusonline.net", "Capo"
    )
    assert "Goblin Warrens" not in html
    assert "Goblin Warrens" not in text
    assert "Tane dei Goblin" in text
