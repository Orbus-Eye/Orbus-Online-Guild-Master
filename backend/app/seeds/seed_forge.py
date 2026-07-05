"""ROUND 4 — Idempotent seed for forge data (sets, enchants, materials, Legendary items).

All operations are upsert-by-slug. Safe to run on every backend boot.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

logger = logging.getLogger("orbus.seed_forge")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Materials (extends Phase 14.6 seeds) ──────────────────────────────
_FORGE_MATERIALS = [
    {
        "slug": "dragon_essence",
        "name": "Dragon Essence",
        "display_name_it": "Essenza di Drago",
        "display_name_en": "Dragon Essence",
        "description": "Distilled aether from a dragon's hoard. Required for high-tier refinement.",
        "item_type": "material",
        "rarity": "Rare",
        "power_score": 0,
        "is_tradeable": True,
        "affects_combat": False,
        "is_active": True,
    },
]

# ─── Legendary baseline items (3 sets × 5 pieces = 15, but we seed 5 standalone for MVP) ──
_LEGENDARY_ITEMS = [
    {
        "slug": "drake_slayer_helm",
        "name": "Drake Slayer Helm",
        "display_name_it": "Elmo Cacciadrago",
        "display_name_en": "Drake Slayer Helm",
        "description": "Forged from the skull of a young drake.",
        "item_type": "armor",
        "slot": "armor",
        "slot_type": "helm",
        "rarity": "Legendary",
        "set_id": "drake_slayer",
        "power_score": 35,
        "strength_bonus": 3,
        "endurance_bonus": 5,
        "max_refinement": 10,
        "enchant_slots": 2,
        "is_tradeable": True,
        "affects_combat": True,
        "is_active": True,
    },
    {
        "slug": "drake_slayer_chest",
        "name": "Drake Slayer Cuirass",
        "display_name_it": "Corazza Cacciadrago",
        "display_name_en": "Drake Slayer Cuirass",
        "description": "Scale-mail armor. Resistant to fire.",
        "item_type": "armor",
        "slot": "armor",
        "slot_type": "chest",
        "rarity": "Legendary",
        "set_id": "drake_slayer",
        "power_score": 45,
        "strength_bonus": 4,
        "endurance_bonus": 8,
        "max_refinement": 10,
        "enchant_slots": 2,
        "is_tradeable": True,
        "affects_combat": True,
        "is_active": True,
    },
    {
        "slug": "drake_slayer_blade",
        "name": "Drake Slayer Blade",
        "display_name_it": "Lama Cacciadrago",
        "display_name_en": "Drake Slayer Blade",
        "description": "A weapon meant for legends.",
        "item_type": "weapon",
        "slot": "weapon",
        "slot_type": "weapon_main",
        "rarity": "Legendary",
        "set_id": "drake_slayer",
        "power_score": 60,
        "strength_bonus": 10,
        "agility_bonus": 3,
        "max_refinement": 10,
        "enchant_slots": 2,
        "is_tradeable": True,
        "affects_combat": True,
        "is_active": True,
    },
    {
        "slug": "arcane_adept_orb",
        "name": "Arcane Adept Orb",
        "display_name_it": "Orbe del Maestro Arcano",
        "display_name_en": "Arcane Adept Orb",
        "description": "A pulsating sphere of pure mana.",
        "item_type": "accessory",
        "slot": "accessory",
        "slot_type": "amulet",
        "rarity": "Legendary",
        "set_id": "arcane_adept",
        "power_score": 55,
        "intellect_bonus": 12,
        "max_refinement": 10,
        "enchant_slots": 2,
        "is_tradeable": True,
        "affects_combat": True,
        "is_active": True,
    },
    {
        "slug": "goblin_hunter_ring",
        "name": "Goblin Hunter Ring",
        "display_name_it": "Anello del Cacciatore di Goblin",
        "display_name_en": "Goblin Hunter Ring",
        "description": "A trophy ring made of goblin teeth.",
        "item_type": "accessory",
        "slot": "accessory",
        "slot_type": "ring",
        "rarity": "Legendary",
        "set_id": "goblin_hunter",
        "power_score": 40,
        "agility_bonus": 6,
        "strength_bonus": 4,
        "max_refinement": 10,
        "enchant_slots": 2,
        "is_tradeable": True,
        "affects_combat": True,
        "is_active": True,
    },
]

# ─── Item sets (Q3 LOCKED — tier-based 3/5) ──────────────────────────────
_ITEM_SETS = [
    {
        "slug": "drake_slayer",
        "name": "Drake Slayer Set",
        "name_it": "Set Cacciadrago",
        "description": "Forged in dragonfire — small bonus at 3 pieces, full glory at 5.",
        "pieces": ["drake_slayer_helm", "drake_slayer_chest", "drake_slayer_blade"],
        "tiers": [
            {"count": 3, "bonus_stat": "strength", "bonus_value": 3, "description": "+3 STR"},
            {"count": 5, "bonus_stat": "endurance", "bonus_value": 10, "description": "+10 END, full set"},
        ],
    },
    {
        "slug": "arcane_adept",
        "name": "Arcane Adept Set",
        "name_it": "Set del Maestro Arcano",
        "description": "Scholar's regalia.",
        "pieces": ["arcane_adept_orb"],
        "tiers": [
            {"count": 3, "bonus_stat": "intellect", "bonus_value": 4, "description": "+4 INT"},
            {"count": 5, "bonus_stat": "intellect", "bonus_value": 10, "description": "+10 INT, full set"},
        ],
    },
    {
        "slug": "goblin_hunter",
        "name": "Goblin Hunter Set",
        "name_it": "Set del Cacciatore di Goblin",
        "description": "Light gear for swift hunters.",
        "pieces": ["goblin_hunter_ring"],
        "tiers": [
            {"count": 3, "bonus_stat": "agility", "bonus_value": 3, "description": "+3 AGI"},
            {"count": 5, "bonus_stat": "agility", "bonus_value": 8, "description": "+8 AGI, full set"},
        ],
    },
]

# ─── Enchants (Q5 LOCKED — pool, player picks) ──────────────────────────
_ENCHANTS = [
    # Common
    {"slug": "small_str", "name": "Minor Strength", "rarity": "Common",   "bonus_stat": "strength_bonus",  "bonus_value": 1, "cost_gold": 50,  "cost_materials": {"iron_shard": 1}},
    {"slug": "small_agi", "name": "Minor Agility",  "rarity": "Common",   "bonus_stat": "agility_bonus",   "bonus_value": 1, "cost_gold": 50,  "cost_materials": {"iron_shard": 1}},
    {"slug": "small_int", "name": "Minor Intellect","rarity": "Common",   "bonus_stat": "intellect_bonus", "bonus_value": 1, "cost_gold": 50,  "cost_materials": {"iron_shard": 1}},
    {"slug": "small_end", "name": "Minor Endurance","rarity": "Common",   "bonus_stat": "endurance_bonus", "bonus_value": 1, "cost_gold": 50,  "cost_materials": {"iron_shard": 1}},
    # Uncommon
    {"slug": "med_str",   "name": "Strength",       "rarity": "Uncommon", "bonus_stat": "strength_bonus",  "bonus_value": 3, "cost_gold": 200, "cost_materials": {"arcane_dust": 1}},
    {"slug": "med_agi",   "name": "Agility",        "rarity": "Uncommon", "bonus_stat": "agility_bonus",   "bonus_value": 3, "cost_gold": 200, "cost_materials": {"arcane_dust": 1}},
    {"slug": "med_int",   "name": "Intellect",      "rarity": "Uncommon", "bonus_stat": "intellect_bonus", "bonus_value": 3, "cost_gold": 200, "cost_materials": {"arcane_dust": 1}},
    {"slug": "med_end",   "name": "Endurance",      "rarity": "Uncommon", "bonus_stat": "endurance_bonus", "bonus_value": 3, "cost_gold": 200, "cost_materials": {"arcane_dust": 1}},
    {"slug": "med_fai",   "name": "Faith",          "rarity": "Uncommon", "bonus_stat": "faith_bonus",     "bonus_value": 3, "cost_gold": 200, "cost_materials": {"arcane_dust": 1}},
    # Rare
    {"slug": "big_str",   "name": "Major Strength", "rarity": "Rare",     "bonus_stat": "strength_bonus",  "bonus_value": 5, "cost_gold": 500, "cost_materials": {"dull_gem": 1}},
    {"slug": "big_agi",   "name": "Major Agility",  "rarity": "Rare",     "bonus_stat": "agility_bonus",   "bonus_value": 5, "cost_gold": 500, "cost_materials": {"dull_gem": 1}},
    {"slug": "big_int",   "name": "Major Intellect","rarity": "Rare",     "bonus_stat": "intellect_bonus", "bonus_value": 5, "cost_gold": 500, "cost_materials": {"dull_gem": 1}},
    # Epic
    {"slug": "epic_pwr",  "name": "Apex Power",     "rarity": "Epic",     "bonus_stat": "strength_bonus",  "bonus_value": 8, "cost_gold": 1500,"cost_materials": {"dragon_essence": 1}},
]


async def run_forge_seeds(db) -> None:
    """Phase 17 (ROUND 4) idempotent seed."""
    now = _now()

    # Materials (extends Phase 14.6 seeds; upsert by slug)
    for m in _FORGE_MATERIALS:
        await db.items.update_one(
            {"slug": m["slug"]},
            {"$set": {**m, "updated_at": now},
             "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now}},
            upsert=True,
        )

    # Legendary items (upsert by slug)
    for li in _LEGENDARY_ITEMS:
        await db.items.update_one(
            {"slug": li["slug"]},
            {"$set": {**li, "updated_at": now},
             "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now}},
            upsert=True,
        )

    # Item sets
    for s in _ITEM_SETS:
        await db.item_sets.update_one(
            {"slug": s["slug"]},
            {"$set": {**s, "updated_at": now},
             "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now}},
            upsert=True,
        )

    # Enchants
    for e in _ENCHANTS:
        await db.enchants.update_one(
            {"slug": e["slug"]},
            {"$set": {**e, "is_active": True, "updated_at": now},
             "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now}},
            upsert=True,
        )

    logger.info(
        "ROUND 4 forge seeds: +%d materials, +%d Legendary, +%d sets, +%d enchants (idempotent)",
        len(_FORGE_MATERIALS), len(_LEGENDARY_ITEMS), len(_ITEM_SETS), len(_ENCHANTS),
    )


from app.core.job_freeze import frozen_when_active as _frozen_when_active


@_frozen_when_active("orbus.seed_forge.run_forge_migration")
async def run_forge_migration(db) -> None:
    """ROUND 4 additive migration. Idempotent: re-runnable any number of times."""
    # Step 0 — inventory_items per-instance fields
    await db.inventory_items.update_many(
        {"instance_id": {"$exists": False}},
        [{"$set": {"instance_id": "$id"}}],   # aggregation pipeline
    )
    await db.inventory_items.update_many(
        {"refinement_level": {"$exists": False}},
        {"$set": {
            "refinement_level": 0,
            "enchants": [],
            "affixes": [],
            "reroll_count": 0,
            "is_bound": False,
            "disenchanted_at": None,
        }},
    )

    # Step 1 — items template extended fields
    await db.items.update_many(
        {"slot_type": {"$exists": False}},
        {"$set": {
            "slot_type": None,
            "set_id": None,
            "max_refinement": 0,
            "enchant_slots": 0,
            "affix_pool_tag": None,
        }},
    )
    LEGACY_SLOT_MAP = {"weapon": "weapon_main", "armor": "chest", "accessory": "amulet"}
    for legacy, new in LEGACY_SLOT_MAP.items():
        await db.items.update_many(
            {"slot": legacy, "slot_type": None},
            {"$set": {"slot_type": new}},
        )

    # Step 3 — indices (idempotent)
    try:
        await db.inventory_items.create_index("instance_id", name="inv_instance_id_idx")
        await db.item_sets.create_index("slug", unique=True, name="item_sets_slug_unique")
        await db.item_sets.create_index("id", unique=True, name="item_sets_id_unique")
        await db.enchants.create_index("slug", unique=True, name="enchants_slug_unique")
        await db.enchants.create_index("id", unique=True, name="enchants_id_unique")
    except Exception as exc:  # noqa: BLE001
        logger.warning("forge index ensure: %s", exc)

    logger.info("ROUND 4 forge migration: applied (idempotent)")


__all__ = ["run_forge_seeds", "run_forge_migration"]
