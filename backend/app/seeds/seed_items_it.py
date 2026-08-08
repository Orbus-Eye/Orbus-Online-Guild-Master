"""Phase 14.6 (ROUND 3.A) — Italian item catalog seed.

17 items canonical to drive the loot tables + crafting recipes. Idempotent
upsert on `slug` so re-runs converge without duplicates and never overwrite
admin/user edits to runtime-only fields.

Anti-leak: every entry carries `is_test=False`, `is_active=True` and
contains no test prefix. The pollution sweep regex in `tests/conftest.py`
will never match these slugs.
"""
from __future__ import annotations

from datetime import datetime, timezone


def _it(name_it: str, desc_it: str) -> dict:
    return {"display_name_it": name_it, "description_it": desc_it}


def _starter_effect(
    effect_id: str,
    lore_key: str,
    summary_it: str,
    summary_en: str,
) -> dict:
    """Reference one immutable runtime definition from a lore-reviewed item."""

    return {
        "schema_version": 1,
        "effect_id": effect_id,
        "effect_version": 1,
        "lore_key": lore_key,
        "effect_summary_it": summary_it,
        "effect_summary_en": summary_en,
        "enabled": True,
    }


# (slug, item_type, rarity, level_required, power_score, stats, stackable, source, italian, english)
ITALIAN_ITEM_SEED: list[dict] = [
    # ─ Materials (5, all stackable, source=dungeon) ─────────────────────────
    {
        "slug": "iron_shard",
        "item_type": "material", "rarity": "Common", "level_required": 1,
        "power_score": 0, "strength_bonus": 0, "agility_bonus": 0,
        "intellect_bonus": 0, "endurance_bonus": 0, "faith_bonus": 0,
        "stackable": True, "source": "dungeon", "craftable": False,
        "name": "Iron Shard",
        "description": "A shard of unrefined iron — common forging material.",
        "display_name_it": "Frammento di Ferro",
        "description_it": "Un frammento di ferro grezzo — materiale comune da forgia.",
        "display_name_en": "Iron Shard",
        "description_en": "A shard of unrefined iron — common forging material.",
    },
    {
        "slug": "raw_leather",
        "item_type": "material", "rarity": "Common", "level_required": 1,
        "power_score": 0, "strength_bonus": 0, "agility_bonus": 0,
        "intellect_bonus": 0, "endurance_bonus": 0, "faith_bonus": 0,
        "stackable": True, "source": "dungeon", "craftable": False,
        "name": "Raw Leather",
        "description": "A piece of rough leather, usable for light armor.",
        "display_name_it": "Cuoio Grezzo",
        "description_it": "Un pezzo di cuoio rude, utile per armature leggere.",
        "display_name_en": "Raw Leather",
        "description_en": "A piece of rough leather, usable for light armor.",
    },
    {
        "slug": "healing_herb",
        "item_type": "material", "rarity": "Common", "level_required": 1,
        "power_score": 0, "strength_bonus": 0, "agility_bonus": 0,
        "intellect_bonus": 0, "endurance_bonus": 0, "faith_bonus": 0,
        "stackable": True, "source": "dungeon", "craftable": False,
        "name": "Healing Herb",
        "description": "A fragrant herb with mild restorative properties.",
        "display_name_it": "Erba Curativa",
        "description_it": "Un'erba aromatica con leggere proprietà curative.",
        "display_name_en": "Healing Herb",
        "description_en": "A fragrant herb with mild restorative properties.",
    },
    {
        "slug": "arcane_dust",
        "item_type": "material", "rarity": "Uncommon", "level_required": 1,
        "power_score": 0, "strength_bonus": 0, "agility_bonus": 0,
        "intellect_bonus": 0, "endurance_bonus": 0, "faith_bonus": 0,
        "stackable": True, "source": "dungeon", "craftable": False,
        "name": "Arcane Dust",
        "description": "Powdered residue of an arcane catalyst.",
        "display_name_it": "Polvere Arcana",
        "description_it": "Polvere residua di un catalizzatore arcano.",
        "display_name_en": "Arcane Dust",
        "description_en": "Powdered residue of an arcane catalyst.",
    },
    {
        "slug": "dull_gem",
        "item_type": "material", "rarity": "Uncommon", "level_required": 1,
        "power_score": 0, "strength_bonus": 0, "agility_bonus": 0,
        "intellect_bonus": 0, "endurance_bonus": 0, "faith_bonus": 0,
        "stackable": True, "source": "dungeon", "craftable": False,
        "name": "Dull Gem",
        "description": "An unpolished gem awaiting an enchanter's touch.",
        "display_name_it": "Gemma Opaca",
        "description_it": "Una gemma grezza in attesa del tocco di un incantatore.",
        "display_name_en": "Dull Gem",
        "description_en": "An unpolished gem awaiting an enchanter's touch.",
    },
    # ─ Weapons (4) ──────────────────────────────────────────────────────────
    {
        "slug": "iron_sword",
        "item_type": "weapon", "rarity": "Common", "level_required": 1,
        "power_score": 5, "strength_bonus": 3, "agility_bonus": 0,
        "intellect_bonus": 0, "endurance_bonus": 0, "faith_bonus": 0,
        "stackable": False, "source": "crafting", "craftable": True,
        "name": "Blade of Krastlov's First Oath",
        "description": "The first blade carried by those who swear before Krastlov's iron gate.",
        "display_name_it": "Lama del Primo Giuramento di Krastlov",
        "description_it": (
            "La prima lama affidata a chi giura davanti al cancello di ferro "
            "di Krastlov."
        ),
        "display_name_en": "Blade of Krastlov's First Oath",
        "description_en": (
            "The first blade carried by those who swear before Krastlov's "
            "iron gate."
        ),
        "flavor_text_it": "Il ferro ricorda la voce di chi promette di tornare.",
        "flavor_text_en": "The iron remembers the voice of those who vow to return.",
        "lore_tags": ["krastlov", "primo-giuramento"],
        "lore_source": "orbus_lore_book_v1",
        "lore_reviewed": True,
        "spoiler_level": "public",
        "slot_type": "weapon",
        "item_binding_policy": "soft",
        "recommended_classes": ["warrior", "guerriero"],
        "class_tags": ["warrior", "guerriero"],
        "effect_metadata": _starter_effect(
            "item.krastlov.first_oath",
            "krastlov",
            "Dopo un evento completato: +2 Tempra fino alla fine della fase.",
            "After a completed event: +2 Endurance until phase end.",
        ),
    },
    {
        "slug": "balanced_dagger",
        "item_type": "weapon", "rarity": "Uncommon", "level_required": 3,
        "power_score": 8, "strength_bonus": 2, "agility_bonus": 2,
        "intellect_bonus": 0, "endurance_bonus": 0, "faith_bonus": 0,
        "stackable": False, "source": "dungeon", "craftable": False,
        "name": "Dagger of Irthe's Last Step",
        "description": "A silent blade recovered where Irthe's procession lost its final pilgrim.",
        "display_name_it": "Pugnale dell'Ultimo Passo di Irthe",
        "description_it": (
            "Una lama silenziosa recuperata dove la processione di Irthe "
            "perse il suo ultimo pellegrino."
        ),
        "display_name_en": "Dagger of Irthe's Last Step",
        "description_en": (
            "A silent blade recovered where Irthe's procession lost its "
            "final pilgrim."
        ),
        "flavor_text_it": "Non lascia impronte. Solo una pausa nel corteo.",
        "flavor_text_en": "It leaves no tracks, only a pause in the procession.",
        "lore_tags": ["irthe", "ultimo-passo"],
        "lore_source": "orbus_lore_book_v1",
        "lore_reviewed": True,
        "spoiler_level": "mystery",
        "slot_type": "weapon",
        "item_binding_policy": "soft",
        "recommended_classes": ["rogue", "ladro"],
        "class_tags": ["rogue", "ladro"],
        "effect_metadata": _starter_effect(
            "item.irthe.last_step",
            "irthe",
            "Dopo un evento completato: +2 Agilità fino alla fine della fase.",
            "After a completed event: +2 Agility until phase end.",
        ),
    },
    {
        "slug": "apprentice_staff",
        "item_type": "weapon", "rarity": "Common", "level_required": 1,
        "power_score": 5, "strength_bonus": 0, "agility_bonus": 0,
        "intellect_bonus": 3, "endurance_bonus": 0, "faith_bonus": 0,
        "stackable": False, "source": "dungeon", "craftable": False,
        "name": "Staff of Ergolat's First Fracture",
        "description": "Its grain follows the first hairline crack recorded beneath Ergolat.",
        "display_name_it": "Bastone della Prima Faglia di Ergolat",
        "description_it": (
            "Le sue venature seguono la prima crepa sottile registrata sotto "
            "Ergolat."
        ),
        "display_name_en": "Staff of Ergolat's First Fracture",
        "description_en": (
            "Its grain follows the first hairline crack recorded beneath "
            "Ergolat."
        ),
        "flavor_text_it": "Vibra un istante prima che la realtà ceda.",
        "flavor_text_en": "It hums one instant before reality gives way.",
        "lore_tags": ["ergolat", "faglie-arcane"],
        "lore_source": "orbus_lore_book_v1",
        "lore_reviewed": True,
        "spoiler_level": "mystery",
        "slot_type": "weapon",
        "item_binding_policy": "soft",
        "recommended_classes": ["mage", "mago"],
        "class_tags": ["mage", "mago"],
        "effect_metadata": _starter_effect(
            "item.ergolat.first_fracture",
            "ergolat",
            "Dopo un evento completato: +2 Intelletto fino alla fine della fase.",
            "After a completed event: +2 Intellect until phase end.",
        ),
    },
    {
        "slug": "path_bow",
        "item_type": "weapon", "rarity": "Common", "level_required": 1,
        "power_score": 5, "strength_bonus": 2, "agility_bonus": 1,
        "intellect_bonus": 0, "endurance_bonus": 0, "faith_bonus": 0,
        "stackable": False, "source": "dungeon", "craftable": False,
        "name": "Bow of Elfwood's Silent Trail",
        "description": "Carved from a fallen branch beside a trail no monster crosses twice.",
        "display_name_it": "Arco del Sentiero Muto di Elfwood",
        "description_it": (
            "Intagliato da un ramo caduto accanto a un sentiero che nessun "
            "mostro attraversa due volte."
        ),
        "display_name_en": "Bow of Elfwood's Silent Trail",
        "description_en": (
            "Carved from a fallen branch beside a trail no monster crosses "
            "twice."
        ),
        "flavor_text_it": "Il bosco trattiene il fiato quando la corda si tende.",
        "flavor_text_en": "The forest holds its breath when the string is drawn.",
        "lore_tags": ["elfwood", "alberi-della-vita"],
        "lore_source": "orbus_lore_book_v1",
        "lore_reviewed": True,
        "spoiler_level": "public",
        "slot_type": "weapon",
        "item_binding_policy": "soft",
        "recommended_classes": ["ranger", "cacciatore_di_mostri"],
        "class_tags": ["ranger", "cacciatore_di_mostri"],
        "effect_metadata": _starter_effect(
            "item.elfwood.silent_trail",
            "elfwood",
            "Dopo un evento completato: +2 Agilità fino alla fine della fase.",
            "After a completed event: +2 Agility until phase end.",
        ),
    },
    # ─ Armors (3) ───────────────────────────────────────────────────────────
    {
        "slug": "light_cuirass",
        "item_type": "armor", "rarity": "Common", "level_required": 1,
        "power_score": 4, "strength_bonus": 0, "agility_bonus": 0,
        "intellect_bonus": 0, "endurance_bonus": 3, "faith_bonus": 0,
        "stackable": False, "source": "crafting", "craftable": True,
        "name": "Light Cuirass",
        "description": "A lightweight chest piece favored by skirmishers.",
        "display_name_it": "Corazza Leggera",
        "description_it": "Un pettorale leggero, preferito dai combattenti agili.",
        "display_name_en": "Light Cuirass",
        "description_en": "A lightweight chest piece favored by skirmishers.",
    },
    {
        "slug": "reinforced_cloak",
        "item_type": "armor", "rarity": "Uncommon", "level_required": 4,
        "power_score": 7, "strength_bonus": 0, "agility_bonus": 0,
        "intellect_bonus": 0, "endurance_bonus": 2, "faith_bonus": 1,
        "stackable": False, "source": "dungeon", "craftable": False,
        "name": "Reinforced Cloak",
        "description": "A travel cloak with reinforced stitching.",
        "display_name_it": "Mantello Rinforzato",
        "description_it": "Un mantello da viaggio con cuciture rinforzate.",
        "display_name_en": "Reinforced Cloak",
        "description_en": "A travel cloak with reinforced stitching.",
    },
    {
        "slug": "initiate_robe",
        "item_type": "armor", "rarity": "Common", "level_required": 1,
        "power_score": 4, "strength_bonus": 0, "agility_bonus": 0,
        "intellect_bonus": 2, "endurance_bonus": 0, "faith_bonus": 1,
        "stackable": False, "source": "dungeon", "craftable": False,
        "name": "Vestment of Halodi's Broken Vow",
        "description": "The vestment of an initiate who kept faith after the temple fell silent.",
        "display_name_it": "Veste del Voto Infranto di Halodi",
        "description_it": (
            "La veste di un iniziato che conservò la fede dopo che il tempio "
            "cadde nel silenzio."
        ),
        "display_name_en": "Vestment of Halodi's Broken Vow",
        "description_en": (
            "The vestment of an initiate who kept faith after the temple "
            "fell silent."
        ),
        "flavor_text_it": "Il voto si spezzò. La fede no.",
        "flavor_text_en": "The vow broke. The faith did not.",
        "lore_tags": ["halodi", "voto-infranto"],
        "lore_source": "orbus_lore_book_v1",
        "lore_reviewed": True,
        "spoiler_level": "mystery",
        "slot_type": "armor",
        "item_binding_policy": "soft",
        "recommended_classes": ["priest", "paladin", "paladino"],
        "class_tags": ["priest", "paladin", "paladino"],
        "effect_metadata": _starter_effect(
            "item.halodi.broken_vow",
            "halodi",
            "Dopo un evento completato: +2 Fede fino alla fine della fase.",
            "After a completed event: +2 Faith until phase end.",
        ),
    },
    # ─ Accessories (3) ──────────────────────────────────────────────────────
    {
        "slug": "chipped_ring",
        "item_type": "accessory", "rarity": "Common", "level_required": 1,
        "power_score": 2, "strength_bonus": 1, "agility_bonus": 0,
        "intellect_bonus": 0, "endurance_bonus": 0, "faith_bonus": 0,
        "stackable": False, "source": "crafting", "craftable": True,
        "name": "Chipped Ring",
        "description": "A small ring with a worn band, useful nonetheless.",
        "display_name_it": "Anello Scheggiato",
        "description_it": "Un piccolo anello con la fascia consumata, comunque utile.",
        "display_name_en": "Chipped Ring",
        "description_en": "A small ring with a worn band, useful nonetheless.",
    },
    {
        "slug": "wanderer_amulet",
        "item_type": "accessory", "rarity": "Uncommon", "level_required": 3,
        "power_score": 6, "strength_bonus": 1, "agility_bonus": 1,
        "intellect_bonus": 1, "endurance_bonus": 1, "faith_bonus": 1,
        "stackable": False, "source": "crafting", "craftable": True,
        "name": "Wanderer's Amulet",
        "description": "An amulet that subtly favors every facet of an adventurer.",
        "display_name_it": "Amuleto del Viandante",
        "description_it": "Un amuleto che favorisce sottilmente ogni aspetto di un avventuriero.",
        "display_name_en": "Wanderer's Amulet",
        "description_en": "An amulet that subtly favors every facet of an adventurer.",
    },
    {
        "slug": "minor_sigil",
        "item_type": "accessory", "rarity": "Rare", "level_required": 5,
        "power_score": 10, "strength_bonus": 0, "agility_bonus": 0,
        "intellect_bonus": 2, "endurance_bonus": 0, "faith_bonus": 2,
        "stackable": False, "source": "dungeon", "craftable": False,
        "name": "Minor Sigil",
        "description": "A small sigil that hums with restrained power.",
        "display_name_it": "Sigillo Minore",
        "description_it": "Un piccolo sigillo che vibra di un potere trattenuto.",
        "display_name_en": "Minor Sigil",
        "description_en": "A small sigil that hums with restrained power.",
    },
    # ─ Consumables (2) ──────────────────────────────────────────────────────
    {
        "slug": "minor_healing_potion",
        "item_type": "consumable", "rarity": "Common", "level_required": 1,
        "power_score": 0, "strength_bonus": 0, "agility_bonus": 0,
        "intellect_bonus": 0, "endurance_bonus": 0, "faith_bonus": 0,
        "stackable": True, "source": "crafting", "craftable": True,
        "name": "Minor Healing Potion",
        "description": "A small flask of restorative brew.",
        "display_name_it": "Pozione Curativa Minore",
        "description_it": "Una piccola fiala di intruglio curativo.",
        "display_name_en": "Minor Healing Potion",
        "description_en": "A small flask of restorative brew.",
    },
    {
        "slug": "travel_ration",
        "item_type": "consumable", "rarity": "Common", "level_required": 1,
        "power_score": 0, "strength_bonus": 0, "agility_bonus": 0,
        "intellect_bonus": 0, "endurance_bonus": 0, "faith_bonus": 0,
        "stackable": True, "source": "dungeon", "craftable": False,
        "name": "Travel Ration",
        "description": "Dried food enough for one day on the road.",
        "display_name_it": "Razione da Viaggio",
        "description_it": "Cibo essiccato sufficiente per un giorno di viaggio.",
        "display_name_en": "Travel Ration",
        "description_en": "Dried food enough for one day on the road.",
    },
]


async def seed_italian_items(db) -> int:
    """Idempotent upsert by `slug`. Returns the number of inserted/updated docs.

    Uses `$setOnInsert` for the immutable identity (slug, id, created_at) and
    `$set` for the canonical IT/EN copy + flags. Admin runtime edits via the
    admin panel will be re-asserted on every boot — by design — to keep the
    seed truly canonical.
    """
    import uuid
    now = datetime.now(timezone.utc).isoformat()
    upserted = 0
    for src in ITALIAN_ITEM_SEED:
        slug = src["slug"]
        set_on_insert = {
            "id": str(uuid.uuid4()),
            "slug": slug,
            "created_at": now,
        }
        set_fields = {
            "name": src["name"],
            "description": src["description"],
            "item_type": src["item_type"],
            "rarity": src["rarity"],
            "level_required": int(src["level_required"]),
            "power_score": int(src["power_score"]),
            "strength_bonus": int(src["strength_bonus"]),
            "agility_bonus": int(src["agility_bonus"]),
            "intellect_bonus": int(src["intellect_bonus"]),
            "endurance_bonus": int(src["endurance_bonus"]),
            "faith_bonus": int(src["faith_bonus"]),
            "stackable": bool(src.get("stackable", False)),
            "source": src.get("source", "unknown"),
            "craftable": bool(src.get("craftable", False)),
            "display_name_it": src["display_name_it"],
            "description_it": src["description_it"],
            "display_name_en": src["display_name_en"],
            "description_en": src["description_en"],
            "is_tradeable": True,
            "is_cosmetic": False,
            "affects_combat": src["item_type"] in ("weapon", "armor", "accessory"),
            "affects_economy": False,
            "affects_ranking": False,
            "can_be_sold_for_gold": True,
            "can_be_sold_for_real_money": False,
            "is_active": True,
            "is_test": False,
            "bind_state": "unbound",
            "updated_at": now,
        }
        for field in (
            "description_it",
            "flavor_text_it",
            "flavor_text_en",
            "lore_tags",
            "lore_source",
            "lore_reviewed",
            "spoiler_level",
            "slot_type",
            "item_binding_policy",
            "recommended_classes",
            "class_tags",
            "effect_metadata",
        ):
            if field in src:
                set_fields[field] = src[field]
        res = await db.items.update_one(
            {"slug": slug},
            {"$setOnInsert": set_on_insert, "$set": set_fields},
            upsert=True,
        )
        if res.upserted_id or res.modified_count:
            upserted += 1
    return upserted


__all__ = ["ITALIAN_ITEM_SEED", "seed_italian_items"]
