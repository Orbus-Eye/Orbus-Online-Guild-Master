"""ROUND 16.0 — Phase 3 — Seed 50 playable races.

Idempotent. Each entry carries:
  * slug, name_it, rarity, lore_group
  * stat_modifiers = {} (flavour-only in Phase 3 — schema is ready
    for Phase 4+ if balance later wants tiny tweaks)
  * is_playable=true, is_active=true

Distribution: 30 common + 12 uncommon + 6 rare + 2 epic = 50.

Usage:
    python -m app.scripts.round160_seed_races [--dry-run]
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from app.audit.log import write_audit


# fmt: off
RACES: list[dict[str, Any]] = [
    # ── 30 COMMON ─────────────────────────────────────────────────────
    {"slug": "human", "name_it": "Umano", "rarity": "common", "lore_group": "umano"},
    {"slug": "high_elf", "name_it": "Alto Elfo", "rarity": "common", "lore_group": "elfico"},
    {"slug": "wood_elf", "name_it": "Elfo dei Boschi", "rarity": "common", "lore_group": "elfico"},
    {"slug": "half_elf", "name_it": "Mezzelfo", "rarity": "common", "lore_group": "elfico"},
    {"slug": "dwarf_mountain", "name_it": "Nano della Montagna", "rarity": "common", "lore_group": "nanico"},
    {"slug": "dwarf_hill", "name_it": "Nano delle Colline", "rarity": "common", "lore_group": "nanico"},
    {"slug": "halfling_lightfoot", "name_it": "Halfling Piediscalzi", "rarity": "common", "lore_group": "halfling"},
    {"slug": "halfling_stout", "name_it": "Halfling Tarchiato", "rarity": "common", "lore_group": "halfling"},
    {"slug": "gnome_forest", "name_it": "Gnomo della Foresta", "rarity": "common", "lore_group": "feerico"},
    {"slug": "gnome_rock", "name_it": "Gnomo della Roccia", "rarity": "common", "lore_group": "nanico"},
    {"slug": "half_orc", "name_it": "Mezz'Orco", "rarity": "common", "lore_group": "orco"},
    {"slug": "orc", "name_it": "Orco", "rarity": "common", "lore_group": "orco"},
    {"slug": "goblin", "name_it": "Goblin", "rarity": "common", "lore_group": "selvaggio"},
    {"slug": "hobgoblin", "name_it": "Hobgoblin", "rarity": "common", "lore_group": "selvaggio"},
    {"slug": "kobold", "name_it": "Kobold", "rarity": "common", "lore_group": "draconico"},
    {"slug": "lizardfolk", "name_it": "Uomo Lucertola", "rarity": "common", "lore_group": "rettiloide"},
    {"slug": "tabaxi", "name_it": "Tabaxi", "rarity": "common", "lore_group": "ferino"},
    {"slug": "tortle", "name_it": "Tortuga", "rarity": "common", "lore_group": "ferino"},
    {"slug": "dragonborn_red", "name_it": "Dragonide Rosso", "rarity": "common", "lore_group": "draconico"},
    {"slug": "dragonborn_silver", "name_it": "Dragonide d'Argento", "rarity": "common", "lore_group": "draconico"},
    {"slug": "dragonborn_green", "name_it": "Dragonide Verde", "rarity": "common", "lore_group": "draconico"},
    {"slug": "tiefling", "name_it": "Tiefling", "rarity": "common", "lore_group": "infernale"},
    {"slug": "aasimar", "name_it": "Aasimar", "rarity": "common", "lore_group": "celestiale"},
    {"slug": "genasi_fire", "name_it": "Genasi di Fuoco", "rarity": "common", "lore_group": "elementale"},
    {"slug": "genasi_water", "name_it": "Genasi d'Acqua", "rarity": "common", "lore_group": "elementale"},
    {"slug": "genasi_earth", "name_it": "Genasi di Terra", "rarity": "common", "lore_group": "elementale"},
    {"slug": "genasi_air", "name_it": "Genasi d'Aria", "rarity": "common", "lore_group": "elementale"},
    {"slug": "firbolg", "name_it": "Firbolg", "rarity": "common", "lore_group": "feerico"},
    {"slug": "centaur", "name_it": "Centauro", "rarity": "common", "lore_group": "primordiale"},
    {"slug": "minotaur", "name_it": "Minotauro", "rarity": "common", "lore_group": "primordiale"},
    # ── 12 UNCOMMON ───────────────────────────────────────────────────
    {"slug": "goliath", "name_it": "Goliath", "rarity": "uncommon", "lore_group": "gigante"},
    {"slug": "warforged", "name_it": "Costrutto Bellico", "rarity": "uncommon", "lore_group": "costrutto"},
    {"slug": "changeling", "name_it": "Mutaforma", "rarity": "uncommon", "lore_group": "feerico"},
    {"slug": "shifter", "name_it": "Mutapelle", "rarity": "uncommon", "lore_group": "ferino"},
    {"slug": "kalashtar", "name_it": "Kalashtar", "rarity": "uncommon", "lore_group": "psionico"},
    {"slug": "tabaxi_jaguar", "name_it": "Tabaxi Giaguaro", "rarity": "uncommon", "lore_group": "ferino"},
    {"slug": "yuan_ti", "name_it": "Yuan-Ti", "rarity": "uncommon", "lore_group": "rettiloide"},
    {"slug": "fairy", "name_it": "Folletto", "rarity": "uncommon", "lore_group": "feerico"},
    {"slug": "satyr", "name_it": "Satiro", "rarity": "uncommon", "lore_group": "feerico"},
    {"slug": "harengon", "name_it": "Harengon", "rarity": "uncommon", "lore_group": "feerico"},
    {"slug": "owlin", "name_it": "Civettide", "rarity": "uncommon", "lore_group": "feerico"},
    {"slug": "autognome", "name_it": "Autognomo", "rarity": "uncommon", "lore_group": "costrutto"},
    # ── 6 RARE ────────────────────────────────────────────────────────
    {"slug": "shadar_kai", "name_it": "Shadar-kai", "rarity": "rare", "lore_group": "shadowfell"},
    {"slug": "eladrin_spring", "name_it": "Eladrin di Primavera", "rarity": "rare", "lore_group": "feerico"},
    {"slug": "eladrin_autumn", "name_it": "Eladrin d'Autunno", "rarity": "rare", "lore_group": "feerico"},
    {"slug": "githyanki", "name_it": "Githyanki", "rarity": "rare", "lore_group": "astrale"},
    {"slug": "githzerai", "name_it": "Githzerai", "rarity": "rare", "lore_group": "astrale"},
    {"slug": "revenant", "name_it": "Redivivo", "rarity": "rare", "lore_group": "non_morto"},
    # ── 2 EPIC ────────────────────────────────────────────────────────
    {"slug": "dhampir", "name_it": "Dhampir", "rarity": "epic", "lore_group": "non_morto"},
    {"slug": "cycle_heir", "name_it": "Erede del Ciclo", "rarity": "epic", "lore_group": "primordiale"},
]
# fmt: on


def _validate_distribution() -> None:
    from collections import Counter
    counts = Counter(r["rarity"] for r in RACES)
    assert counts["common"] == 30, counts
    assert counts["uncommon"] == 12, counts
    assert counts["rare"] == 6, counts
    assert counts["epic"] == 2, counts
    assert len(RACES) == 50


async def _run(db, *, dry_run: bool) -> dict[str, int]:
    _validate_distribution()
    now = datetime.now(timezone.utc)
    inserted = 0
    skipped = 0
    for r in RACES:
        existing = await db.races.find_one({"slug": r["slug"]})
        if existing:
            skipped += 1
            continue
        doc = {
            **r,
            "name_en": r["name_it"],
            "is_playable": True,
            "is_active": True,
            "stat_modifiers": {},
            "tags": [],
            "description_it": None,
            "created_at": now,
            "updated_at": now,
        }
        if dry_run:
            inserted += 1
            continue
        await db.races.insert_one(doc)
        await write_audit(
            db, event_type="race_seeded_round160",
            actor_user_id=None, actor_guild_id=None,
            source="round160.seed_races",
            metadata={"slug": r["slug"], "rarity": r["rarity"]},
        )
        inserted += 1
    return {"inserted": inserted, "skipped": skipped, "total": len(RACES)}


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    load_dotenv()
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    try:
        out = await _run(cli[os.environ["DB_NAME"]], dry_run=args.dry_run)
        print({"dry_run": args.dry_run, **out})
        return 0
    finally:
        cli.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
