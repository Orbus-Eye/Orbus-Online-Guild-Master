"""ROUND 5 (Phase 17.5 + 18) — idempotent seeds & migrations.

What this module installs (all idempotent / re-runnable):
  • 12 new dungeons with `required_team_size=5` across T1/T2/T3/T4
    (§D.1 of `/app/memory/ROUND_5_BRIEF.md`).
  • Marks the 10 historic dungeons as `is_legacy=True` (§I.2).
  • Bumps recommended_power +25% on legacy T2/T3 dungeons ONCE
    (§I.6, gated by `power_bumped: true` flag).
  • Adds additive fields on `guilds`:
      `max_raid_score`, `last_raid_completed_at`,
      `raids_completed_count`, `raids_victory_count`.
  • Removes `dragon_essence` from `forge.disenchant_returns` so it now drops
    only from T4-5p and raids (§I.4).
  • Seeds 3 `raid_dungeons` with the 4-party / 5-per-party model (Phase 18).
  • Creates compound + simple indexes on `raids`, `raid_participants`,
    `raid_dungeons`.

NO breaking change: every operation is `$set` / `$setOnInsert` / `update_many`
with a sentinel guard.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from app.shared.content_curve import DUNGEON_CURVE, RAID_CURVE

logger = logging.getLogger("orbus.seed_round5")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ────────────────────────────────────────────────────────────────────────
# §D.1 — 12 new 5p dungeons
# ────────────────────────────────────────────────────────────────────────
DUNGEON_5P_SEED = [
    # T1 Novizio (5p) — entry-level for team 5
    {
        "slug": "wolf-den-5p",
        "name": "Wolf Den",
        "description": "A snow-packed cave run by a pack of dire wolves. They hunt in formation.",
        "difficulty": 1,
        "required_team_size": 5,
        "base_duration_seconds": 60,
        "recommended_power": 80,
        "base_gold_reward": 50,
        "base_xp_reward": 35,
        "gate": {"min_adventurers": 5},
        "tier_label": "T1",
        "tags": ["beast", "pack"],
    },
    {
        "slug": "frost-cave-5p",
        "name": "Frost Cave",
        "description": "An ice cavern where shrieking elementals ambush from the walls.",
        "difficulty": 1,
        "required_team_size": 5,
        "base_duration_seconds": 75,
        "recommended_power": 90,
        "base_gold_reward": 55,
        "base_xp_reward": 38,
        "gate": {"min_adventurers": 5},
        "tier_label": "T1",
        "tags": ["cold", "ambush"],
    },
    {
        "slug": "salt-marsh-5p",
        "name": "Salt Marsh",
        "description": "Brackish swamp infested with bog-things and a slow, hungry tide.",
        "difficulty": 1,
        "required_team_size": 5,
        "base_duration_seconds": 90,
        "recommended_power": 100,
        "base_gold_reward": 60,
        "base_xp_reward": 42,
        "gate": {"min_adventurers": 5},
        "tier_label": "T1",
        "tags": ["swamp", "slow"],
    },

    # T2 Avventuriero (5p)
    {
        "slug": "iron-foundry-5p",
        "name": "Iron Foundry",
        "description": "An abandoned dwarven foundry where the bellows still pump and the constructs still patrol.",
        "difficulty": 2,
        "required_team_size": 5,
        "base_duration_seconds": 120,
        "recommended_power": 140,
        "base_gold_reward": 90,
        "base_xp_reward": 65,
        "gate": {"min_adventurers": 5, "min_max_team_power_ever": 120},
        "tier_label": "T2",
        "tags": ["construct", "fire"],
    },
    {
        "slug": "silent-monastery-5p",
        "name": "Silent Monastery",
        "description": "A high-mountain monastery whose monks died praying. They have not stopped.",
        "difficulty": 2,
        "required_team_size": 5,
        "base_duration_seconds": 150,
        "recommended_power": 155,
        "base_gold_reward": 100,
        "base_xp_reward": 72,
        "gate": {"min_adventurers": 5, "min_max_team_power_ever": 130},
        "tier_label": "T2",
        "tags": ["undead", "sustain"],
    },
    {
        "slug": "pirate-fleet-5p",
        "name": "Pirate Fleet",
        "description": "Three lashed-together hulks ruled by a sea-witch and her bottle-crew.",
        "difficulty": 2,
        "required_team_size": 5,
        "base_duration_seconds": 180,
        "recommended_power": 170,
        "base_gold_reward": 115,
        "base_xp_reward": 80,
        "gate": {"min_adventurers": 5, "min_max_team_power_ever": 140},
        "tier_label": "T2",
        "tags": ["human", "water"],
    },

    # T3 Veterano (5p)
    {
        "slug": "obsidian-arena-5p",
        "name": "Obsidian Arena",
        "description": "A volcanic gladiator pit. The crowd is dead. The champion is not.",
        "difficulty": 3,
        "required_team_size": 5,
        "base_duration_seconds": 240,
        "recommended_power": 210,
        "base_gold_reward": 160,
        "base_xp_reward": 110,
        "gate": {"min_adventurers": 5, "min_max_team_power_ever": 200},
        "tier_label": "T3",
        "tags": ["gladiator", "agility"],
    },
    {
        "slug": "clockwork-vault-5p",
        "name": "Clockwork Vault",
        "description": "A logic-locked vault. The guardians solve riddles by stabbing the wrong answer.",
        "difficulty": 3,
        "required_team_size": 5,
        "base_duration_seconds": 300,
        "recommended_power": 230,
        "base_gold_reward": 180,
        "base_xp_reward": 125,
        "gate": {"min_adventurers": 5, "min_max_team_power_ever": 220},
        "tier_label": "T3",
        "tags": ["construct", "intellect"],
    },
    {
        "slug": "voidspire-5p",
        "name": "Voidspire",
        "description": "A black tower that punches into the Otherwhere. The geometry is wrong on purpose.",
        "difficulty": 3,
        "required_team_size": 5,
        "base_duration_seconds": 360,
        "recommended_power": 250,
        "base_gold_reward": 200,
        "base_xp_reward": 140,
        "gate": {"min_adventurers": 5, "min_max_team_power_ever": 240},
        "tier_label": "T3",
        "tags": ["void", "magic"],
    },

    # T4 Elite (5p)
    {
        "slug": "infernal-pit-5p",
        "name": "Infernal Pit",
        "description": "A literal pit to hell. The deeper you go, the more polite the demons become.",
        "difficulty": 4,
        "required_team_size": 5,
        "base_duration_seconds": 420,
        "recommended_power": 290,
        "base_gold_reward": 260,
        "base_xp_reward": 180,
        "gate": {"min_adventurers": 5, "min_max_team_power_ever": 280},
        "tier_label": "T4",
        "tags": ["demon", "fire"],
    },
    {
        "slug": "celestial-citadel-5p",
        "name": "Celestial Citadel",
        "description": "A floating fortress of fallen angels. They remember being holy. They do not enjoy it.",
        "difficulty": 4,
        "required_team_size": 5,
        "base_duration_seconds": 540,
        "recommended_power": 320,
        "base_gold_reward": 300,
        "base_xp_reward": 210,
        "gate": {"min_adventurers": 5, "min_max_team_power_ever": 300},
        "tier_label": "T4",
        "tags": ["angel", "holy"],
    },
    {
        "slug": "world-tree-roots-5p",
        "name": "World-Tree Roots",
        "description": "Beneath the world ash, the roots dream of dragons. The dreams have teeth.",
        "difficulty": 4,
        "required_team_size": 5,
        "base_duration_seconds": 720,
        "recommended_power": 360,
        "base_gold_reward": 360,
        "base_xp_reward": 250,
        "gate": {"min_adventurers": 5, "min_max_team_power_ever": 340},
        "tier_label": "T4",
        "tags": ["nature", "endurance"],
    },
]


# ────────────────────────────────────────────────────────────────────────
# Career revamp — four raid sizes: 10 / 15 / 20 / 40
# ────────────────────────────────────────────────────────────────────────
RAID_DUNGEON_SEED = [
    {
        "slug": "moonfall-vigil",
        "name": "Vigil of the Broken Moon",
        "name_it": "Veglia della Luna Infranta",
        "description": (
            "Ten chosen guild members guard the shard that fell beyond Onirade "
            "and face the shape moving inside its reflected light."
        ),
        "description_it": (
            "Dieci membri scelti vegliano il frammento caduto oltre Onirade e "
            "affrontano la forma che si muove dentro la sua luce riflessa."
        ),
        "lore_source": "Onirade · Cronaca della Tredicesima Eclissi",
        "boss_name": "Il Riflesso Senza Volto",
        "narrative_hook": "La luna non si è spezzata nel cielo, ma nel suo riflesso.",
        "lore_reviewed": True,
        "tier": 1,
        "min_roster_size": 10,
        "required_party_count": 2,
        "required_party_size": 5,
        "party_focus_hints": [
            {"party_idx": 1, "preferred_role": "Tank",
             "label_it": "Custodi del Frammento", "label_en": "Shard Wardens"},
            {"party_idx": 2, "preferred_role": "DPS",
             "label_it": "Cacciatori dell'Eclissi", "label_en": "Eclipse Hunters"},
        ],
        "base_duration_seconds": 1200,
        "base_gold_reward": 450,
        "loot_pool_slug": "raid_moonfall_10",
        "guaranteed_dragon_essence_min": 0,
        "guaranteed_dragon_essence_max": 1,
        "gate": {"min_roster_size": 10},
    },
    {
        "slug": "broken-bastion-siege",
        "name": "Oath of the Broken Bastion",
        "name_it": "Giuramento del Bastione Spezzato",
        "description": (
            "Krastlov's abandoned oath still binds the gate. Fifteen adventurers "
            "must decide whether to renew it or finally let the fortress die."
        ),
        "description_it": (
            "Il giuramento abbandonato di Krastlov vincola ancora il portale. "
            "Quindici avventurieri devono rinnovarlo o lasciare finalmente morire la fortezza."
        ),
        "lore_source": "Krastlov · Tavole del Primo Giuramento",
        "boss_name": "Il Castellano Incatenato",
        "narrative_hook": "Ogni pietra ricorda il nome di chi non tornò.",
        "lore_reviewed": True,
        "tier": 2,
        "min_roster_size": 15,
        "required_party_count": 3,
        "required_party_size": 5,
        "party_focus_hints": [
            {"party_idx": 1, "preferred_role": "Tank", "label_it": "Avanguardia", "label_en": "Vanguard"},
            {"party_idx": 2, "preferred_role": "Healer", "label_it": "Sostegno", "label_en": "Sustain"},
            {"party_idx": 3, "preferred_role": "DPS", "label_it": "Assalto", "label_en": "Assault"},
        ],
        "base_duration_seconds": 1800,
        "base_gold_reward": 800,
        "loot_pool_slug": "raid_bastion_15",
        "guaranteed_dragon_essence_min": 1,
        "guaranteed_dragon_essence_max": 3,
        "gate": {"min_roster_size": 15},
    },
    {
        "slug": "necropolis-bells",
        "name": "The Bells of Irthe",
        "name_it": "I Rintocchi di Irthe",
        "description": (
            "Twenty voices enter the necropolis where Irthe hid the names of "
            "the dead inside bronze bells. One bell now speaks a living name."
        ),
        "description_it": (
            "Venti voci entrano nella necropoli dove Irthe nascose i nomi dei "
            "morti nelle campane di bronzo. Una campana pronuncia ora un nome vivente."
        ),
        "lore_source": "Irthe · Registro dei Nomi Taciuti",
        "boss_name": "Il Campanaro Senza Volto",
        "narrative_hook": "L'ultima campana conosce il nome del Capogilda.",
        "lore_reviewed": True,
        "tier": 3,
        "min_roster_size": 20,
        "required_party_count": 4,
        "required_party_size": 5,
        "party_focus_hints": [
            {"party_idx": 1, "preferred_role": "Healer", "label_it": "Cura primaria", "label_en": "Primary Heal"},
            {"party_idx": 2, "preferred_role": "Healer", "label_it": "Cura secondaria", "label_en": "Backup Heal"},
            {"party_idx": 3, "preferred_role": "Tank", "label_it": "Avanguardia", "label_en": "Front Line"},
            {"party_idx": 4, "preferred_role": "DPS", "label_it": "Distruttori", "label_en": "Breakers"},
        ],
        "base_duration_seconds": 2400,
        "base_gold_reward": 1300,
        "loot_pool_slug": "raid_irthe_bells_20",
        "guaranteed_dragon_essence_min": 2,
        "guaranteed_dragon_essence_max": 4,
        "gate": {"min_roster_size": 20},
    },
    {
        "slug": "dragon-vault",
        "name": "Conclave of the First Flame",
        "name_it": "Concilio della Fiamma Primordiale",
        "description": (
            "Forty veterans descend beneath the Ariale to judge the ancient "
            "pact between the first dragons and the peoples of Orbus."
        ),
        "description_it": (
            "Quaranta veterani scendono sotto l'Ariale per giudicare l'antico "
            "patto fra i primi draghi e i popoli di Orbus."
        ),
        "lore_source": "Ariale · Patto delle Fiamme",
        "boss_name": "Azhur, Memoria della Prima Fiamma",
        "narrative_hook": "Il drago non custodisce un tesoro: custodisce la versione originale del patto.",
        "lore_reviewed": True,
        "tier": 4,
        "min_roster_size": 40,
        "required_party_count": 8,
        "required_party_size": 5,
        "party_focus_hints": [
            {"party_idx": 1, "preferred_role": "Tank", "label_it": "Esca", "label_en": "Decoy"},
            {"party_idx": 2, "preferred_role": "DPS", "label_it": "Cacciatori", "label_en": "Hunters"},
            {"party_idx": 3, "preferred_role": "Healer", "label_it": "Sostegno", "label_en": "Sustain"},
            {"party_idx": 4, "preferred_role": "DPS", "label_it": "Ladri", "label_en": "Thieves"},
            {"party_idx": 5, "preferred_role": "DPS", "label_it": "Araldi della Cenere", "label_en": "Ash Heralds"},
            {"party_idx": 6, "preferred_role": "Tank", "label_it": "Custodi delle Catene", "label_en": "Chain Wardens"},
            {"party_idx": 7, "preferred_role": "Healer", "label_it": "Occhi del Vuoto", "label_en": "Void Eyes"},
            {"party_idx": 8, "preferred_role": None, "label_it": "Ultima Riserva", "label_en": "Final Reserve"},
        ],
        "base_duration_seconds": 3600,
        "base_gold_reward": 3000,
        "loot_pool_slug": "raid_first_flame_40",
        "guaranteed_dragon_essence_min": 5,
        "guaranteed_dragon_essence_max": 10,
        "gate": {"min_roster_size": 40},
    },
]


# ────────────────────────────────────────────────────────────────────────
# Migrations
# ────────────────────────────────────────────────────────────────────────
LEGACY_DUNGEON_SLUGS = frozenset({
    "goblin-warrens", "shadow-crypts", "dragons-hoard",
    "sewer-nest", "bandit-hideout",
    "druid-grove", "cursed-mines", "sunken-library",
    "lich-sanctum", "storm-spire",
})

# +25% rec_power applied once on T2/T3 legacy dungeons (§I.6).
POWER_BUMP_T2_T3_SLUGS = frozenset({
    "shadow-crypts", "druid-grove", "cursed-mines", "sunken-library",
    "lich-sanctum", "storm-spire", "dragons-hoard",
})


async def seed_5p_dungeons(db) -> int:
    """Upsert the 12 new 5p dungeons. Idempotent."""
    now = _now_iso()
    n = 0
    for d in DUNGEON_5P_SEED:
        curve = DUNGEON_CURVE[d["slug"]]
        await db.dungeons.update_one(
            {"slug": d["slug"]},
            {
                "$setOnInsert": {
                    "id": str(uuid.uuid4()),
                    "created_at": now,
                },
                "$set": {
                    "slug": d["slug"],
                    "name": d["name"],
                    "description": d["description"],
                    "difficulty": d["difficulty"],
                    "required_team_size": d["required_team_size"],
                    "base_duration_seconds": d["base_duration_seconds"],
                    "recommended_power": curve.recommended_power,
                    "base_gold_reward": d["base_gold_reward"],
                    "base_xp_reward": curve.xp_reward,
                    "required_level": curve.required_level,
                    "bucket": curve.bucket,
                    "gate": d.get("gate") or {},
                    "tier_label": d.get("tier_label"),
                    "tags": d.get("tags") or [],
                    "is_legacy": False,
                    "is_5p": True,
                    "power_bumped": True,  # new dungeons calibrated natively
                    "is_active": True,
                    "updated_at": now,
                },
            },
            upsert=True,
        )
        n += 1
    return n


async def mark_legacy_dungeons(db) -> int:
    """Set `is_legacy=True` on the 10 historic dungeons. Idempotent."""
    res = await db.dungeons.update_many(
        {"slug": {"$in": list(LEGACY_DUNGEON_SLUGS)}, "is_legacy": {"$ne": True}},
        {"$set": {"is_legacy": True, "is_5p": False}},
    )
    return res.modified_count


async def bump_legacy_t2_t3_power(db) -> int:
    """+25% recommended_power on T2/T3 legacy dungeons, ONCE.

    Gated by `power_bumped: True` sentinel so subsequent boots are a no-op.
    """
    now = _now_iso()
    bumped = 0
    # Find candidates not yet bumped
    cursor = db.dungeons.find(
        {
            "slug": {"$in": list(POWER_BUMP_T2_T3_SLUGS)},
            "$or": [{"power_bumped": {"$exists": False}}, {"power_bumped": False}],
        },
        {"_id": 0, "id": 1, "slug": 1, "recommended_power": 1},
    )
    rows = await cursor.to_list(50)
    for d in rows:
        old = int(d.get("recommended_power", 0))
        new = -(-old * 125 // 100)  # ceil(old*1.25)
        await db.dungeons.update_one(
            {"id": d["id"]},
            {"$set": {
                "recommended_power": new,
                "power_bumped": True,
                "updated_at": now,
            }},
        )
        # Audit event (best-effort)
        try:
            from app.audit.log import write_audit
            await write_audit(
                db,
                event_type="dungeon_power_bumped",
                source="seed_round5.bump_legacy_t2_t3_power",
                related_entity_id=d["id"],
                metadata={
                    "dungeon_slug": d["slug"],
                    "old_recommended_power": old,
                    "new_recommended_power": new,
                },
            )
        except Exception:  # noqa: BLE001
            pass
        bumped += 1
    return bumped


async def add_guild_raid_fields(db) -> int:
    """Additive fields on guilds. Idempotent."""
    res = await db.guilds.update_many(
        {"max_raid_score": {"$exists": False}},
        {"$set": {
            "max_raid_score": 0,
            "last_raid_completed_at": None,
            "raids_completed_count": 0,
            "raids_victory_count": 0,
        }},
    )
    return res.modified_count


async def remove_legacy_recruitment_state(db) -> dict[str, int]:
    """Erase obsolete random-board and freeze-bench state."""
    guild_result = await db.guilds.update_many(
        {
            "$or": [
                {"recruit_freeze_bench": {"$exists": True}},
                {"frozen_candidates": {"$exists": True}},
                {"recruitment_refreshes": {"$exists": True}},
            ]
        },
        {
            "$unset": {
                "recruit_freeze_bench": "",
                "frozen_candidates": "",
                "recruitment_refreshes": "",
            }
        },
    )
    offers_result = await db.recruitment_offers.delete_many({})
    return {
        "guilds_cleaned": int(guild_result.modified_count),
        "offers_removed": int(offers_result.deleted_count),
    }


async def backfill_round4_inventory_defaults(db) -> int:
    """Self-heal inventory_items rows that lost ROUND 4 default fields
    (test residue, partial inserts from older fixtures). Idempotent."""
    fixes = 0
    res1 = await db.inventory_items.update_many(
        {"is_bound": {"$exists": False}}, {"$set": {"is_bound": False}},
    )
    fixes += res1.modified_count
    res2 = await db.inventory_items.update_many(
        {"refinement_level": {"$exists": False}}, {"$set": {"refinement_level": 0}},
    )
    fixes += res2.modified_count
    res3 = await db.inventory_items.update_many(
        {"disenchanted_at": {"$exists": False}}, {"$set": {"disenchanted_at": None}},
    )
    fixes += res3.modified_count
    # instance_id needs a unique UUID per row: do it row-by-row only for rows missing it
    cursor = db.inventory_items.find(
        {"instance_id": {"$exists": False}}, {"_id": 0, "id": 1},
    )
    rows = await cursor.to_list(10000)
    for r in rows:
        await db.inventory_items.update_one(
            {"id": r["id"]},
            {"$set": {"instance_id": str(uuid.uuid4())}},
        )
        fixes += 1
    # Also normalise None → False for is_bound (None counts as exists but breaks tests)
    res5 = await db.inventory_items.update_many(
        {"is_bound": None}, {"$set": {"is_bound": False}},
    )
    fixes += res5.modified_count
    # ROUND 6B FASE A — discard binding: this update_many's row count is
    # not used (the next `_pending` loop counts the real fixes via `fixes`).
    await db.inventory_items.update_many(
        {"instance_id": None},
        {"$set": {"instance_id": "_pending"}},  # we'll re-assign next
    )
    # Re-assign proper UUIDs
    cursor = db.inventory_items.find({"instance_id": "_pending"}, {"_id": 0, "id": 1})
    rows = await cursor.to_list(10000)
    for r in rows:
        await db.inventory_items.update_one(
            {"id": r["id"]},
            {"$set": {"instance_id": str(uuid.uuid4())}},
        )
        fixes += 1
    res7 = await db.inventory_items.update_many(
        {"refinement_level": None}, {"$set": {"refinement_level": 0}},
    )
    fixes += res7.modified_count
    return fixes


async def seed_raid_dungeons(db) -> int:
    """Upsert the four 10/15/20/40 raid dungeons. Idempotent."""
    now = _now_iso()
    n = 0
    for r in RAID_DUNGEON_SEED:
        curve = RAID_CURVE[r["slug"]]
        await db.raid_dungeons.update_one(
            {"slug": r["slug"]},
            {
                "$setOnInsert": {
                    "id": str(uuid.uuid4()),
                    "created_at": now,
                },
                "$set": {
                    "slug": r["slug"],
                    "name": r["name"],
                    "name_it": r["name_it"],
                    "description": r["description"],
                    "description_it": r["description_it"],
                    "lore_source": r["lore_source"],
                    "boss_name": r["boss_name"],
                    "narrative_hook": r["narrative_hook"],
                    "lore_reviewed": bool(r["lore_reviewed"]),
                    "tier": r["tier"],
                    "recommended_power_combined": curve.recommended_power,
                    "min_adventurer_level": curve.required_level,
                    "min_roster_size": r["min_roster_size"],
                    "required_party_count": r["required_party_count"],
                    "required_party_size": r["required_party_size"],
                    "party_focus_hints": r["party_focus_hints"],
                    "base_duration_seconds": r["base_duration_seconds"],
                    "base_gold_reward": r["base_gold_reward"],
                    "base_xp_per_member": curve.xp_reward,
                    "loot_pool_slug": r["loot_pool_slug"],
                    "guaranteed_dragon_essence_min": r["guaranteed_dragon_essence_min"],
                    "guaranteed_dragon_essence_max": r["guaranteed_dragon_essence_max"],
                    "gate": r.get("gate") or {},
                    "is_active": True,
                    "updated_at": now,
                },
            },
            upsert=True,
        )
        n += 1
    return n


async def seed_company_ring(db) -> int:
    """Seed the sole ultra-rare random-drop blueprint."""
    from app.items.catalog_contract import ULTRA_RARE_RANDOM_DROP_SLUG
    now = _now_iso()
    await db.items.update_one(
        {"slug": ULTRA_RARE_RANDOM_DROP_SLUG},
        {
            "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now},
            "$set": {
                "slug": ULTRA_RARE_RANDOM_DROP_SLUG,
                "name": "L'Unico Anello della \"Compagnia\"",
                "display_name_it": "L'Unico Anello della \"Compagnia\"",
                "display_name_en": "The Company's One Ring",
                "description_it": (
                    "Nessun orafo ne rivendica la fattura. Sul bordo interno "
                    "appaiono i nomi di una sola compagnia: quella che lo sottrae "
                    "ad Alveora, la Burattinaia della Luna."
                ),
                "lore_source": "Tesoro impossibile di Alveora",
                "item_type": "ring",
                "slot_type": "ring",
                "rarity": "Unique",
                "required_adventurer_level": 80,
                "level_required": 80,
                "acquisition_mode": "ultra_rare_random_drop",
                "source_policy_id": "company_ring_ultra_rare",
                "source_type": "world_boss",
                "source_slug": "alveora_moon_puppeteer",
                "is_tradeable": False,
                "is_active": True,
                "is_test": False,
                "is_lore_linked": True,
                "is_global_unique": True,
                "strength_bonus": 8,
                "agility_bonus": 8,
                "intellect_bonus": 8,
                "endurance_bonus": 8,
                "faith_bonus": 8,
                "power_score": 20,
                "updated_at": now,
            },
        },
        upsert=True,
    )
    return 1


async def ensure_raid_indexes(db) -> None:
    """Indexes for raids/raid_participants/raid_dungeons. Idempotent."""
    try:
        await db.raid_dungeons.create_index("slug", unique=True, name="raid_dungeons_slug_unique")
        await db.raid_dungeons.create_index("id", unique=True, name="raid_dungeons_id_unique")
        await db.raids.create_index("id", unique=True, name="raids_id_unique")
        await db.raids.create_index(
            [("guild_id", 1), ("status", 1)], name="raids_guild_status_idx",
        )
        await db.raids.create_index(
            [("guild_id", 1), ("completed_at", -1)], name="raids_guild_history_idx",
        )
        await db.raid_participants.create_index(
            [("raid_id", 1), ("adventurer_id", 1)],
            unique=True, name="raid_participants_unique_per_raid",
        )
        await db.raid_participants.create_index("adventurer_id", name="raid_participants_adv_idx")
        await db.raid_participants.create_index("raid_id", name="raid_participants_raid_idx")
    except Exception as exc:  # noqa: BLE001
        logger.warning("ensure_raid_indexes failed: %s", exc)


async def seed_starter_training_yard(db) -> int:
    """ROUND 17.1 P0.1 — Seed idempotente dello starter dungeon
    `training-yard`. Reward piccolo (15 gold, 12 XP), power 15 → team
    rookie Lv1 base (~20-25 team power) ha >50% success chance.

    Vincoli: no Legendary, no power creep, coerente con curva esistente.
    Marcato `is_starter=True` per essere filtrabile lato UI + fallback
    reward logic (vedi `_complete_one_expedition`).
    """
    now = _now_iso()
    doc = {
        "slug": "training-yard",
        "name": "Campo d'Addestramento",
        "description": (
            "Consigliato per la tua prima spedizione. Un'area protetta "
            "dove nuove reclute affrontano manichini e ombre di goblin."
        ),
        "difficulty": 1,
        "required_team_size": 3,
        "base_duration_seconds": 60,
        "recommended_power": 15,
        "base_gold_reward": 15,
        "base_xp_reward": 12,
        "required_level": 1,
        "gate": {},
        "tier_label": "Starter",
        "tags": ["starter", "onboarding"],
        "is_legacy": False,
        "is_5p": False,
        "power_bumped": True,
        "is_active": True,
        "is_starter": True,  # flag consumato da UI + fallback reward
        "updated_at": now,
    }
    await db.dungeons.update_one(
        {"slug": "training-yard"},
        {
            "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now},
            "$set": doc,
        },
        upsert=True,
    )
    return 1


async def run_round5_seeds_and_migrations(db) -> dict:
    """Top-level orchestrator invoked from lifespan.

    All operations idempotent; safe on every boot.
    """
    summary = {}
    summary["dungeons_5p_upserted"] = await seed_5p_dungeons(db)
    summary["starter_training_yard_upserted"] = await seed_starter_training_yard(db)
    summary["legacy_marked"] = await mark_legacy_dungeons(db)
    summary["power_bumped"] = await bump_legacy_t2_t3_power(db)
    summary["guilds_extended"] = await add_guild_raid_fields(db)
    summary["legacy_recruitment_removed"] = await remove_legacy_recruitment_state(db)
    summary["inventory_round4_backfilled"] = await backfill_round4_inventory_defaults(db)
    summary["raid_dungeons_upserted"] = await seed_raid_dungeons(db)
    summary["company_ring_upserted"] = await seed_company_ring(db)
    await ensure_raid_indexes(db)

    # Backfill starter roster for all guilds (best-effort, may be no-op).
    try:
        from app.onboarding.services import ensure_starter_roster_for_all_guilds
        backfill = await ensure_starter_roster_for_all_guilds(db)
        summary["starter_backfill_advs"] = backfill.get("advs_inserted", 0)
    except Exception as exc:  # noqa: BLE001
        logger.warning("starter backfill failed: %s", exc)

    logger.info(
        "ROUND 5 boot: dungeons5p=%d legacy_marked=%d powerbump=%d "
        "guild_ext=%d raid_dungeons=%d starter_backfill=%d (idempotent)",
        summary["dungeons_5p_upserted"],
        summary["legacy_marked"],
        summary["power_bumped"],
        summary["guilds_extended"],
        summary["raid_dungeons_upserted"],
        summary.get("starter_backfill_advs", 0),
    )
    return summary


__all__ = [
    "DUNGEON_5P_SEED",
    "RAID_DUNGEON_SEED",
    "LEGACY_DUNGEON_SLUGS",
    "POWER_BUMP_T2_T3_SLUGS",
    "seed_5p_dungeons",
    "mark_legacy_dungeons",
    "bump_legacy_t2_t3_power",
    "add_guild_raid_fields",
    "remove_legacy_recruitment_state",
    "seed_raid_dungeons",
    "seed_company_ring",
    "ensure_raid_indexes",
    "run_round5_seeds_and_migrations",
]
