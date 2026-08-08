"""FASE 3 (2026-08-08) — Seed: nuovi reagenti, consumabili, ricette professioni.

Contenuto (tutto idempotente, upsert su slug):
  * 12 nuovi materiali-reagente (uno per dungeon/raid di fascia alta) —
    nomi ITALIANI come canonici (name == display_name_it).
  * 5 consumabili con `consumable_effect` (Pietra della Conoscenza inclusa).
  * 4 ricette nuove per Cucina e Alchimia + campo `profession` sulle
    ricette esistenti (legacy → forge).

Design: memory/fase3_design_reagenti_crafting.md

Esecuzione (ambiente col DB):
    python -m app.seeds.seed_fase3_reagenti_consumabili
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone


def _material(slug: str, rarity: str, name_it: str, name_en: str,
              desc_it: str, desc_en: str, source: str = "dungeon") -> dict:
    return {
        "slug": slug,
        "item_type": "material", "rarity": rarity, "level_required": 1,
        "power_score": 0, "strength_bonus": 0, "agility_bonus": 0,
        "intellect_bonus": 0, "endurance_bonus": 0, "faith_bonus": 0,
        "stackable": True, "source": source, "craftable": False,
        # FASE 3 — item nuovi nascono con nome canonico ITALIANO.
        "name": name_it,
        "description": desc_it,
        "display_name_it": name_it, "description_it": desc_it,
        "display_name_en": name_en, "description_en": desc_en,
    }


NEW_MATERIALS: list[dict] = [
    # ── uncommon (dungeon) ───────────────────────────────────────────
    _material("ossa_antiche", "Uncommon", "Ossa Antiche", "Ancient Bones",
              "Ossa impregnate di magia necromantica, dal Santuario del Lich.",
              "Bones steeped in necromantic magic, from the Lich Sanctum."),
    _material("ghiaccio_eterno", "Uncommon", "Ghiaccio Eterno", "Everfrost Ice",
              "Ghiaccio che non si scioglie mai, dalle Grotte Gelate.",
              "Ice that never melts, from the Frost Cave."),
    _material("spezia_palustre", "Uncommon", "Spezia Palustre", "Marsh Spice",
              "Spezia pungente della Palude Salmastra: base della Cucina di gilda.",
              "A pungent spice from the Salt Marsh: guild Cooking staple."),
    # ── rare (dungeon) ───────────────────────────────────────────────
    _material("scaglia_di_drago", "Rare", "Scaglia di Drago", "Dragon Scale",
              "Scaglia strappata al Tesoro del Drago. Dura come l'acciaio.",
              "A scale torn from the Dragon's Hoard. Hard as steel."),
    _material("essenza_di_tempesta", "Rare", "Essenza di Tempesta", "Storm Essence",
              "Elettricità viva imbottigliata sulla Guglia delle Tempeste.",
              "Living lightning bottled atop the Storm Spire."),
    _material("ossidiana", "Rare", "Ossidiana", "Obsidian",
              "Vetro vulcanico dell'Arena d'Ossidiana: filo da rasoio.",
              "Volcanic glass from the Obsidian Arena: razor-sharp."),
    _material("ingranaggio_arcano", "Rare", "Ingranaggio Arcano", "Arcane Cogwheel",
              "Meccanismo incantato del Caveau a Orologeria.",
              "An enchanted mechanism from the Clockwork Vault."),
    _material("frammento_del_vuoto", "Rare", "Frammento del Vuoto", "Void Shard",
              "Scheggia di non-realtà caduta dalla Guglia del Vuoto.",
              "A sliver of un-reality fallen from the Voidspire."),
    # ── epic (dungeon di fine linea) ─────────────────────────────────
    _material("cenere_infernale", "Epic", "Cenere Infernale", "Infernal Ash",
              "Cenere che arde in eterno, dalla Fossa Infernale.",
              "Ash that burns forever, from the Infernal Pit."),
    _material("lacrima_celeste", "Epic", "Lacrima Celeste", "Celestial Tear",
              "Goccia di luce solidificata della Cittadella Celeste.",
              "A solidified drop of light from the Celestial Citadel."),
    _material("linfa_del_mondo", "Epic", "Linfa del Mondo", "Worldsap",
              "Linfa dorata delle Radici dell'Albero del Mondo.",
              "Golden sap from the World Tree's roots."),
    # ── reagenti da RAID ─────────────────────────────────────────────
    _material("polvere_di_luna", "Epic", "Polvere di Luna", "Moondust",
              "Pulviscolo argentato della Veglia di Lunacaduta. Solo dai raid.",
              "Silver dust from the Moonfall Vigil. Raid-only.", source="raid"),
    _material("nucleo_d_assedio", "Epic", "Nucleo d'Assedio", "Siege Core",
              "Cuore d'arma d'assedio del Bastione Infranto. Solo dai raid.",
              "The heart of a siege engine from the Broken Bastion. Raid-only.",
              source="raid"),
    _material("rintocco_spettrale", "Legendary", "Rintocco Spettrale", "Spectral Toll",
              "Eco cristallizzata delle Campane della Necropoli. Solo dai raid.",
              "A crystallized echo of the Necropolis Bells. Raid-only.",
              source="raid"),
]


def _consumable(slug: str, rarity: str, name_it: str, name_en: str,
                desc_it: str, desc_en: str, effect: dict,
                craftable: bool = True, source: str = "crafting") -> dict:
    return {
        "slug": slug,
        "item_type": "consumable", "rarity": rarity, "level_required": 1,
        "power_score": 0, "strength_bonus": 0, "agility_bonus": 0,
        "intellect_bonus": 0, "endurance_bonus": 0, "faith_bonus": 0,
        "stackable": True, "source": source, "craftable": craftable,
        "name": name_it,
        "description": desc_it,
        "display_name_it": name_it, "description_it": desc_it,
        "display_name_en": name_en, "description_en": desc_en,
        # FASE 3.3 — contratto effetto consumabile (vedi design §3).
        "consumable_effect": effect,
    }


NEW_CONSUMABLES: list[dict] = [
    # FASE 3.4 — Pietra della Conoscenza: droppa dai dungeon (20%),
    # NON si crafta.
    _consumable(
        "pietra_della_conoscenza", "Rare",
        "Pietra della Conoscenza", "Knowledge Stone",
        "Runa antica che accelera l'apprendimento: +50% esperienza per le "
        "prossime 5 spedizioni dell'avventuriero che la porta.",
        "An ancient rune that quickens learning: +50% XP for the bearer's "
        "next 5 expeditions.",
        {"type": "xp_boost", "magnitude": 0.5, "charges": 5},
        craftable=False, source="dungeon",
    ),
    # Cucina
    _consumable(
        "stufato_del_viandante", "Common",
        "Stufato del Viandante", "Wanderer's Stew",
        "Un pasto caldo prima della marcia: +5 potere per 3 spedizioni.",
        "A hot meal before the march: +5 power for 3 expeditions.",
        {"type": "power_boost", "magnitude": 5, "charges": 3},
    ),
    _consumable(
        "banchetto_dell_eroe", "Rare",
        "Banchetto dell'Eroe", "Hero's Feast",
        "Un banchetto degno delle saghe: +12 potere per 3 spedizioni.",
        "A feast worthy of the sagas: +12 power for 3 expeditions.",
        {"type": "power_boost", "magnitude": 12, "charges": 3},
    ),
    # Alchimia
    _consumable(
        "elisir_di_vigore", "Uncommon",
        "Elisir di Vigore", "Elixir of Vigor",
        "Tonifica corpo e spirito: +8 potere per 5 spedizioni.",
        "Braces body and spirit: +8 power for 5 expeditions.",
        {"type": "power_boost", "magnitude": 8, "charges": 5},
    ),
    _consumable(
        "tonico_del_sapiente", "Epic",
        "Tonico del Sapiente", "Sage's Tonic",
        "Distillato di Polvere di Luna: +25% esperienza per 3 spedizioni.",
        "Distilled Moondust: +25% XP for 3 expeditions.",
        {"type": "xp_boost", "magnitude": 0.25, "charges": 3},
    ),
]


NEW_RECIPES: list[dict] = [
    {
        "slug": "recipe_stufato_del_viandante",
        "profession": "cooking",
        "display_name_it": "Stufato del Viandante",
        "display_name_en": "Wanderer's Stew",
        "description_it": "Cucina uno stufato corroborante (2 Erbe Curative + 1 Spezia Palustre).",
        "description_en": "Cook a hearty stew (2 Healing Herbs + 1 Marsh Spice).",
        "inputs": [
            {"item_slug": "healing_herb", "quantity": 2},
            {"item_slug": "spezia_palustre", "quantity": 1},
        ],
        "gold_cost": 10,
        "output_item_slug": "stufato_del_viandante",
        "output_quantity": 1,
        "required_guild_level": 1,
    },
    {
        "slug": "recipe_banchetto_dell_eroe",
        "profession": "cooking",
        "display_name_it": "Banchetto dell'Eroe",
        "display_name_en": "Hero's Feast",
        "description_it": "Prepara un banchetto leggendario (2 Spezie Palustri + 1 Scaglia di Drago).",
        "description_en": "Prepare a legendary feast (2 Marsh Spice + 1 Dragon Scale).",
        "inputs": [
            {"item_slug": "spezia_palustre", "quantity": 2},
            {"item_slug": "scaglia_di_drago", "quantity": 1},
        ],
        "gold_cost": 40,
        "output_item_slug": "banchetto_dell_eroe",
        "output_quantity": 1,
        "required_guild_level": 3,
    },
    {
        "slug": "recipe_elisir_di_vigore",
        "profession": "alchemy",
        "display_name_it": "Elisir di Vigore",
        "display_name_en": "Elixir of Vigor",
        "description_it": "Distilla un elisir rinvigorente (2 Erbe Curative + 1 Polvere Arcana).",
        "description_en": "Distil an invigorating elixir (2 Healing Herbs + 1 Arcane Dust).",
        "inputs": [
            {"item_slug": "healing_herb", "quantity": 2},
            {"item_slug": "arcane_dust", "quantity": 1},
        ],
        "gold_cost": 20,
        "output_item_slug": "elisir_di_vigore",
        "output_quantity": 1,
        "required_guild_level": 2,
    },
    {
        "slug": "recipe_tonico_del_sapiente",
        "profession": "alchemy",
        "display_name_it": "Tonico del Sapiente",
        "display_name_en": "Sage's Tonic",
        "description_it": "Un distillato prezioso (1 Polvere di Luna + 2 Polveri Arcane). La Polvere di Luna cade solo nei raid.",
        "description_en": "A precious distillate (1 Moondust + 2 Arcane Dust). Moondust drops only in raids.",
        "inputs": [
            {"item_slug": "polvere_di_luna", "quantity": 1},
            {"item_slug": "arcane_dust", "quantity": 2},
        ],
        "gold_cost": 60,
        "output_item_slug": "tonico_del_sapiente",
        "output_quantity": 1,
        "required_guild_level": 5,
    },
]


async def seed_fase3(db) -> dict:
    """Upsert idempotente di materiali, consumabili e ricette."""
    now = datetime.now(timezone.utc).isoformat()
    counts = {"materials": 0, "consumables": 0, "recipes": 0,
              "legacy_profession_backfill": 0}

    for src in NEW_MATERIALS + NEW_CONSUMABLES:
        is_consumable = src["item_type"] == "consumable"
        set_fields = {**src, "is_active": True, "is_test": False,
                      "updated_at": now}
        res = await db.items.update_one(
            {"slug": src["slug"]},
            {
                "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now},
                "$set": set_fields,
            },
            upsert=True,
        )
        if res.upserted_id or res.modified_count:
            counts["consumables" if is_consumable else "materials"] += 1

    for src in NEW_RECIPES:
        res = await db.recipes.update_one(
            {"slug": src["slug"]},
            {
                "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now},
                "$set": {**src, "is_active": True, "is_test": False,
                         "updated_at": now},
            },
            upsert=True,
        )
        if res.upserted_id or res.modified_count:
            counts["recipes"] += 1

    # Backfill: le ricette senza professione sono della Fucina.
    res = await db.recipes.update_many(
        {"profession": {"$exists": False}},
        {"$set": {"profession": "forge", "updated_at": now}},
    )
    counts["legacy_profession_backfill"] = int(res.modified_count)
    return counts


if __name__ == "__main__":
    from app.core.database import db as _db

    async def _main():
        counts = await seed_fase3(_db)
        print(f"[seed_fase3] {counts}")

    asyncio.run(_main())
