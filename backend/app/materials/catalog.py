"""ROUND 11.2 EXT TASK 10 M4 — Materials data-driven catalog.

Single source of truth for player-facing material metadata: display name
IT/EN, rarity, description, in-game drop sources, and the structures /
recipes that consume them.

Why a code module instead of a DB collection:
  * Materials are a TINY, slow-changing set (≤20). Code-defined gives us
    type-safety, code review, and one less seed migration.
  * The `items` collection still owns the canonical record (slug, name,
    item_type='material'). This module is a thin overlay that enriches
    public surfaces without duplicating identity.
  * Anti-spoiler: we curate sources explicitly. Equipment (weapons,
    armor, accessories, set items, legendaries) is NEVER in this catalog,
    enforced by `is_material=True`.

Filter contract (also enforced by routes.py):
  * `is_material = True`
  * `is_equipment = False`
  * `is_active = True`
  * `is_hidden = False`
  * `is_test = False`

If a material exists in `items` collection but no entry here, it is NOT
exposed publicly (safe default — content gap surfaced via tests).

`Admin grant` is intentionally NEVER listed as a public source — player
must discover materials through legitimate gameplay channels.
"""
from __future__ import annotations


# Source type taxonomy (player-facing labels).
SOURCE_LABEL_IT = {
    "dungeon": "Dungeon",
    "expedition": "Spedizioni",
    "raid": "Raid",
    "contract": "Contratti",
    "market_npc": "Mercato NPC",
    "auction": "Asta",
    "forge_disenchant": "Disincanto (Fucina)",
    "crafting": "Crafting",
    "quest_reward": "Reward quest",
    "shop": "Mercato",
}
SOURCE_LABEL_EN = {
    "dungeon": "Dungeons",
    "expedition": "Expeditions",
    "raid": "Raids",
    "contract": "Contracts",
    "market_npc": "NPC Market",
    "auction": "Auction",
    "forge_disenchant": "Forge disenchant",
    "crafting": "Crafting",
    "quest_reward": "Quest reward",
    "shop": "Market",
}


# Material catalog. Keys are `items.slug` values.
MATERIAL_CATALOG: dict[str, dict] = {
    "iron_shard": {
        "rarity": "common",
        "description_it": "Scheggia di ferro grezzo: materiale base per la maggior parte dei potenziamenti del Territorio e per le ricette comuni in Fucina.",
        "description_en": "Crude iron shard: the foundational material for most Territory upgrades and common Forge recipes.",
        "sources": [
            {"type": "dungeon", "tier": "T1", "note": "Spedizioni iniziali (Lv1-3)."},
            {"type": "contract", "frequency": "daily", "note": "Alcuni contratti giornalieri."},
            {"type": "market_npc", "frequency": "daily_rotation", "note": "Disponibile in rotazione al Mercato NPC."},
            {"type": "forge_disenchant", "note": "Disincanto di equip common (richiede Fucina)."},
        ],
        "used_for_it": [
            "Potenziamento Dormitori, Sala Gilda, Bacheca Spedizioni",
            "Ricette base in Fucina",
        ],
    },
    "lesser_arcane_dust": {
        "rarity": "uncommon",
        "description_it": "Polvere arcana di qualità minore. Reagente magico per potenziamenti intermedi e crafting di equip uncommon.",
        "description_en": "Minor arcane dust: a magical reagent for intermediate upgrades and uncommon equip crafting.",
        "sources": [
            {"type": "dungeon", "tier": "T2", "note": "Dungeon Lv4-8."},
            {"type": "contract", "frequency": "weekly", "note": "Contratti settimanali."},
            {"type": "forge_disenchant", "note": "Disincanto di equip uncommon."},
        ],
        "used_for_it": [
            "Potenziamento Sala Gilda Lv3+, Bacheca Spedizioni Lv3+",
            "Ricette uncommon in Fucina",
        ],
    },
    "greater_arcane_dust": {
        "rarity": "rare",
        "description_it": "Polvere arcana di alta qualità. Reagente per potenziamenti avanzati e crafting rare/epic.",
        "description_en": "High-quality arcane dust: a reagent for advanced upgrades and rare/epic crafting.",
        "sources": [
            {"type": "dungeon", "tier": "T3", "note": "Dungeon Lv9+."},
            {"type": "raid", "tier": "T1-T2", "note": "Reward raid base."},
            {"type": "forge_disenchant", "note": "Disincanto di equip rare/epic."},
        ],
        "used_for_it": [
            "Potenziamento Dormitori Lv7+, Sala Gilda Lv5+, Sala Guerra Lv5+",
            "Ricette rare/epic in Fucina",
        ],
    },
    "raw_leather": {
        "rarity": "common",
        "description_it": "Cuoio grezzo: materiale base per la lavorazione di armature leggere.",
        "description_en": "Crude leather: base material for light armor crafting.",
        "sources": [
            {"type": "dungeon", "tier": "T1", "note": "Drop frequente nei dungeon iniziali."},
            {"type": "market_npc"},
        ],
        "used_for_it": ["Ricette armature leggere in Fucina"],
    },
    "healing_herb": {
        "rarity": "common",
        "description_it": "Erba curativa: reagente per consumabili e potion di base.",
        "description_en": "Healing herb: a reagent for basic consumables and potions.",
        "sources": [
            {"type": "expedition", "note": "Drop in spedizioni con classe Healer."},
            {"type": "contract", "frequency": "daily"},
        ],
        "used_for_it": ["Ricette consumable in Fucina"],
    },
    "arcane_dust": {
        "rarity": "uncommon",
        "description_it": "Polvere arcana standard. Variante legacy di Lesser Arcane Dust — usata in alcune ricette di transizione.",
        "description_en": "Standard arcane dust: legacy variant of Lesser Arcane Dust, used in some transition recipes.",
        "sources": [
            {"type": "dungeon", "tier": "T2"},
            {"type": "forge_disenchant"},
        ],
        "used_for_it": ["Ricette legacy in Fucina (transizione)"],
    },
    "dull_gem": {
        "rarity": "uncommon",
        "description_it": "Gemma opaca: reagente per accessori e gioielli base.",
        "description_en": "Dull gem: a reagent for basic accessories and jewelry.",
        "sources": [
            {"type": "dungeon", "tier": "T2"},
            {"type": "market_npc"},
        ],
        "used_for_it": ["Ricette accessori in Fucina"],
    },
    "dragon_essence": {
        "rarity": "legendary",
        "description_it": "Essenza di drago: il reagente esclusivo del raid Caveau del Drago.",
        "description_en": "Dragon essence: the exclusive reagent of the Dragon Vault raid.",
        "sources": [
            {"type": "raid", "note": "SOLO dal raid Caveau del Drago (garantita a vittoria)."},
        ],
        "used_for_it": ["Ricette epiche/leggendarie in Fucina", "Potenziamenti late-game"],
    },
    # ── FASE 3.1 (2026-08-08) — reagenti principali per dungeon/raid ────
    # Ogni contenuto ha UN reagente: la fonte elencata è quella canonica.
    # Vedi memory/fase3_design_reagenti_crafting.md §1.
    "ossa_antiche": {
        "rarity": "uncommon",
        "description_it": "Ossa impregnate di magia necromantica.",
        "description_en": "Bones steeped in necromantic magic.",
        "sources": [{"type": "dungeon", "note": "Santuario del Lich."}],
        "used_for_it": ["Ricette di Alchimia oscura (future)"],
    },
    "ghiaccio_eterno": {
        "rarity": "uncommon",
        "description_it": "Ghiaccio che non si scioglie mai.",
        "description_en": "Ice that never melts.",
        "sources": [{"type": "dungeon", "note": "Grotte Gelate."}],
        "used_for_it": ["Ricette di Cucina e Alchimia (future)"],
    },
    "spezia_palustre": {
        "rarity": "uncommon",
        "description_it": "Spezia pungente: la base della Cucina di gilda.",
        "description_en": "A pungent spice: the guild Cooking staple.",
        "sources": [{"type": "dungeon", "note": "Palude Salmastra."}],
        "used_for_it": ["Stufato del Viandante", "Banchetto dell'Eroe"],
    },
    "scaglia_di_drago": {
        "rarity": "rare",
        "description_it": "Scaglia dura come l'acciaio.",
        "description_en": "A scale hard as steel.",
        "sources": [{"type": "dungeon", "note": "Tesoro del Drago."}],
        "used_for_it": ["Banchetto dell'Eroe", "Ricette di Fucina (future)"],
    },
    "essenza_di_tempesta": {
        "rarity": "rare",
        "description_it": "Elettricità viva imbottigliata.",
        "description_en": "Living lightning, bottled.",
        "sources": [{"type": "dungeon", "note": "Guglia delle Tempeste."}],
        "used_for_it": ["Ricette di Alchimia (future)"],
    },
    "ossidiana": {
        "rarity": "rare",
        "description_it": "Vetro vulcanico dal filo di rasoio.",
        "description_en": "Razor-sharp volcanic glass.",
        "sources": [{"type": "dungeon", "note": "Arena d'Ossidiana."}],
        "used_for_it": ["Ricette di Fucina (future)"],
    },
    "ingranaggio_arcano": {
        "rarity": "rare",
        "description_it": "Meccanismo incantato di fattura perduta.",
        "description_en": "An enchanted mechanism of lost make.",
        "sources": [{"type": "dungeon", "note": "Caveau a Orologeria."}],
        "used_for_it": ["Ricette di Fucina (future)"],
    },
    "frammento_del_vuoto": {
        "rarity": "rare",
        "description_it": "Scheggia di non-realtà.",
        "description_en": "A sliver of un-reality.",
        "sources": [{"type": "dungeon", "note": "Guglia del Vuoto."}],
        "used_for_it": ["Ricette di Alchimia (future)"],
    },
    "cenere_infernale": {
        "rarity": "epic",
        "description_it": "Cenere che arde in eterno.",
        "description_en": "Ash that burns forever.",
        "sources": [{"type": "dungeon", "note": "Fossa Infernale."}],
        "used_for_it": ["Potenziamenti late-game (futuri)"],
    },
    "lacrima_celeste": {
        "rarity": "epic",
        "description_it": "Goccia di luce solidificata.",
        "description_en": "A solidified drop of light.",
        "sources": [{"type": "dungeon", "note": "Cittadella Celeste."}],
        "used_for_it": ["Potenziamenti late-game (futuri)"],
    },
    "linfa_del_mondo": {
        "rarity": "epic",
        "description_it": "Linfa dorata dell'Albero del Mondo.",
        "description_en": "Golden sap of the World Tree.",
        "sources": [{"type": "dungeon", "note": "Radici dell'Albero del Mondo."}],
        "used_for_it": ["Potenziamenti late-game (futuri)"],
    },
    "polvere_di_luna": {
        "rarity": "epic",
        "description_it": "Pulviscolo argentato. Cade SOLO nei raid.",
        "description_en": "Silver dust. Drops ONLY in raids.",
        "sources": [{"type": "raid", "note": "Veglia di Lunacaduta (garantita a vittoria)."}],
        "used_for_it": ["Tonico del Sapiente"],
    },
    "nucleo_d_assedio": {
        "rarity": "epic",
        "description_it": "Cuore d'arma d'assedio. Cade SOLO nei raid.",
        "description_en": "The heart of a siege engine. Raid-only.",
        "sources": [{"type": "raid", "note": "Assedio del Bastione Infranto (garantito a vittoria)."}],
        "used_for_it": ["Ricette di Fucina (future)"],
    },
    "rintocco_spettrale": {
        "rarity": "legendary",
        "description_it": "Eco cristallizzata delle Campane. Cade SOLO nei raid.",
        "description_en": "A crystallized echo of the Bells. Raid-only.",
        "sources": [{"type": "raid", "note": "Campane della Necropoli (garantito a vittoria)."}],
        "used_for_it": ["Ricette leggendarie (future)"],
    },
}


def get_material_overlay(slug: str) -> dict | None:
    """Return the curated catalog entry for `slug`, or None if not exposed."""
    return MATERIAL_CATALOG.get(slug)


def all_known_material_slugs() -> list[str]:
    return sorted(MATERIAL_CATALOG.keys())


__all__ = [
    "MATERIAL_CATALOG",
    "SOURCE_LABEL_IT",
    "SOURCE_LABEL_EN",
    "get_material_overlay",
    "all_known_material_slugs",
]
