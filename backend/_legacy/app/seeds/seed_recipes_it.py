"""Phase 14.6 (ROUND 3.B) — Crafting recipes seed (Italian catalog).

5 starter recipes. Idempotent upsert on `slug`. Consumes the 17 IT items
seeded by `seed_items_it.py` and produces the 5 craftable outputs flagged
`craftable=True` in that seed.
"""
from __future__ import annotations

from datetime import datetime, timezone


RECIPE_SEED: list[dict] = [
    {
        "slug": "recipe_iron_sword",
        "display_name_it": "Spada di Ferro",
        "display_name_en": "Iron Sword",
        "description_it": "Forgia una Spada di Ferro da 3 Frammenti di Ferro.",
        "description_en": "Forge an Iron Sword from 3 Iron Shards.",
        "inputs": [{"item_slug": "iron_shard", "quantity": 3}],
        "gold_cost": 20,
        "output_item_slug": "iron_sword",
        "output_quantity": 1,
        "required_guild_level": 1,
    },
    {
        "slug": "recipe_light_cuirass",
        "display_name_it": "Corazza Leggera",
        "display_name_en": "Light Cuirass",
        "description_it": "Una corazza leggera da Frammenti di Ferro e Cuoio Grezzo.",
        "description_en": "A light cuirass crafted from iron shards and rough leather.",
        "inputs": [
            {"item_slug": "iron_shard", "quantity": 2},
            {"item_slug": "raw_leather", "quantity": 2},
        ],
        "gold_cost": 25,
        "output_item_slug": "light_cuirass",
        "output_quantity": 1,
        "required_guild_level": 1,
    },
    {
        "slug": "recipe_healing_potion",
        "display_name_it": "Pozione Curativa Minore (x3)",
        "display_name_en": "Minor Healing Potion (x3)",
        "description_it": "Distilla 3 pozioni curative da 2 Erbe Curative.",
        "description_en": "Brew 3 healing potions from 2 Healing Herbs.",
        "inputs": [{"item_slug": "healing_herb", "quantity": 2}],
        "gold_cost": 10,
        "output_item_slug": "minor_healing_potion",
        "output_quantity": 3,
        "required_guild_level": 1,
    },
    {
        "slug": "recipe_chipped_ring",
        "display_name_it": "Anello Scheggiato",
        "display_name_en": "Chipped Ring",
        "description_it": "Forgia un Anello Scheggiato da un Frammento di Ferro e una Gemma Opaca.",
        "description_en": "Forge a Chipped Ring from one Iron Shard and one Dull Gem.",
        "inputs": [
            {"item_slug": "iron_shard", "quantity": 1},
            {"item_slug": "dull_gem", "quantity": 1},
        ],
        "gold_cost": 15,
        "output_item_slug": "chipped_ring",
        "output_quantity": 1,
        "required_guild_level": 1,
    },
    {
        "slug": "recipe_wanderer_amulet",
        "display_name_it": "Amuleto del Viandante",
        "display_name_en": "Wanderer's Amulet",
        "description_it": "Un amuleto raffinato che richiede polvere arcana e una gemma opaca.",
        "description_en": "A refined amulet that requires arcane dust and a dull gem.",
        "inputs": [
            {"item_slug": "arcane_dust", "quantity": 2},
            {"item_slug": "dull_gem", "quantity": 1},
        ],
        "gold_cost": 50,
        "output_item_slug": "wanderer_amulet",
        "output_quantity": 1,
        "required_guild_level": 2,
    },
]


async def seed_italian_recipes(db) -> int:
    """Idempotent upsert by `slug`. Returns the number of inserted/updated docs."""
    import uuid
    now = datetime.now(timezone.utc).isoformat()
    upserted = 0
    for src in RECIPE_SEED:
        slug = src["slug"]
        set_on_insert = {
            "id": str(uuid.uuid4()),
            "slug": slug,
            "created_at": now,
        }
        set_fields = {
            "display_name_it": src["display_name_it"],
            "display_name_en": src["display_name_en"],
            "description_it": src["description_it"],
            "description_en": src["description_en"],
            "inputs": [
                {"item_slug": str(i["item_slug"]), "quantity": int(i["quantity"])}
                for i in src["inputs"]
            ],
            "gold_cost": int(src["gold_cost"]),
            "output_item_slug": src["output_item_slug"],
            "output_quantity": int(src["output_quantity"]),
            "required_guild_level": int(src.get("required_guild_level", 1)),
            "is_active": True,
            "is_test": False,
            "updated_at": now,
        }
        res = await db.recipes.update_one(
            {"slug": slug},
            {"$setOnInsert": set_on_insert, "$set": set_fields},
            upsert=True,
        )
        if res.upserted_id or res.modified_count:
            upserted += 1
    return upserted


__all__ = ["RECIPE_SEED", "seed_italian_recipes"]
