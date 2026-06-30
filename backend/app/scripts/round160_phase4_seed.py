"""ROUND 16.0 — Phase 4 — Threats & Counters seed (idempotent, additive).

Seeds:
  * `dungeon_threats` catalog (16 entries)
  * `counter_tags` catalog (16 entries, each mapped to threats it counters)
  * `dungeons.threat_tags` for ~10 curated void/undead dungeons
  * `class_specializations.counter_tags` updated for lore-coherent specs
  * `adventurer_traits.counter_tags` updated for legacy lore-coherent traits
  * 10 new "mission" traits added to `adventurer_traits`

No hard delete. Re-running yields zero new writes.

Usage:
    python -m app.scripts.round160_phase4_seed [--dry-run]
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from app.audit.log import write_audit


# ── 16 THREATS ────────────────────────────────────────────────────────
THREATS = [
    {"slug": "boss", "name_it": "Boss", "description_it": "Nemico singolo molto potente."},
    {"slug": "minion", "name_it": "Sgherri", "description_it": "Folla di nemici minori."},
    {"slug": "spell", "name_it": "Incantesimo", "description_it": "Magia offensiva ad area."},
    {"slug": "trap", "name_it": "Trappola", "description_it": "Trappole nascoste nel dungeon."},
    {"slug": "curse", "name_it": "Maledizione", "description_it": "Effetto malefico persistente."},
    {"slug": "ambush", "name_it": "Imboscata", "description_it": "Assalto a sorpresa."},
    {"slug": "elite", "name_it": "Elite", "description_it": "Nemici corazzati e tattici."},
    {"slug": "undead", "name_it": "Non-morto", "description_it": "Creature non viventi animate."},
    {"slug": "beast", "name_it": "Bestia", "description_it": "Animali predatori o mostruosi."},
    {"slug": "elemental", "name_it": "Elementale", "description_it": "Creature di elementi puri."},
    {"slug": "void", "name_it": "Vuoto", "description_it": "Entità del Vuoto e dell'Abisso.", "lore_tag": "void"},
    {"slug": "poison", "name_it": "Veleno", "description_it": "Attacchi tossici e gas."},
    {"slug": "disease", "name_it": "Malattia", "description_it": "Contagi e pestilenze."},
    {"slug": "siege", "name_it": "Assedio", "description_it": "Combattimento contro fortificazioni."},
    {"slug": "stealth", "name_it": "Furtività", "description_it": "Nemici invisibili o nascosti."},
    {"slug": "magic_barrier", "name_it": "Barriera Magica", "description_it": "Difese arcane impenetrabili."},
]

# ── 16 COUNTER TAGS ──────────────────────────────────────────────────
COUNTERS = [
    {"slug": "counter_boss", "name_it": "Anti-Boss", "threats_countered": ["boss"]},
    {"slug": "counter_minion", "name_it": "Anti-Sgherri", "threats_countered": ["minion"]},
    {"slug": "counter_spell", "name_it": "Anti-Incantesimo", "threats_countered": ["spell", "magic_barrier"]},
    {"slug": "counter_trap", "name_it": "Anti-Trappola", "threats_countered": ["trap"]},
    {"slug": "counter_curse", "name_it": "Anti-Maledizione", "threats_countered": ["curse"]},
    {"slug": "counter_ambush", "name_it": "Anti-Imboscata", "threats_countered": ["ambush", "stealth"]},
    {"slug": "counter_elite", "name_it": "Anti-Elite", "threats_countered": ["elite"]},
    {"slug": "counter_undead", "name_it": "Anti-Non-morti", "threats_countered": ["undead", "curse"]},
    {"slug": "counter_beast", "name_it": "Anti-Bestia", "threats_countered": ["beast"]},
    {"slug": "counter_elemental", "name_it": "Anti-Elementale", "threats_countered": ["elemental"]},
    {"slug": "counter_void", "name_it": "Anti-Vuoto", "threats_countered": ["void", "magic_barrier"]},
    {"slug": "counter_poison", "name_it": "Anti-Veleno", "threats_countered": ["poison", "disease"]},
    {"slug": "counter_disease", "name_it": "Anti-Malattia", "threats_countered": ["disease"]},
    {"slug": "counter_siege", "name_it": "Anti-Assedio", "threats_countered": ["siege"]},
    {"slug": "counter_stealth", "name_it": "Anti-Furtività", "threats_countered": ["stealth"]},
    {"slug": "counter_magic_barrier", "name_it": "Anti-Barriera Magica", "threats_countered": ["magic_barrier"]},
]

# ── Curated dungeon → threats mapping ────────────────────────────────
DUNGEON_THREAT_MAP = {
    "shadow-crypts": ["undead", "curse", "minion"],
    "lich-sanctum": ["undead", "curse", "boss", "magic_barrier"],
    "voidspire-5p": ["void", "magic_barrier", "elite", "boss"],
    "echoes-of-the-broken-thread": ["void", "spell", "ambush"],
    "shattered-seal-of-ergolat": ["void", "magic_barrier", "elite"],
    "obelisks-of-the-void": ["void", "spell", "trap"],
    "eclipthra-veiled-sanctum": ["void", "curse", "stealth"],
    "gralca-tide-of-the-deep": ["void", "elemental", "minion"],
    "tip-of-oblivion-trial": ["void", "boss", "magic_barrier"],
}

# Spec slug → counter_tags (lore-coherent)
SPEC_COUNTERS = {
    "guardian_spec": ["counter_minion", "counter_siege"],
    "weapon_master_spec": ["counter_elite"],
    "berserker_spec": ["counter_boss"],
    "duelist_spec": ["counter_elite"],
    "shadow_spec": ["counter_stealth", "counter_ambush"],
    "assassin_spec": ["counter_stealth", "counter_boss"],
    "elementalist_spec": ["counter_elemental"],
    "arcanist_spec": ["counter_spell", "counter_magic_barrier"],
    "necromancer_spec": ["counter_undead"],
    "healer_spec": ["counter_poison", "counter_disease"],
    "exorcist_spec": ["counter_undead", "counter_curse"],
    "oracle_spec": ["counter_curse", "counter_ambush"],
    "marksman_spec": ["counter_boss"],
    "monster_hunter_spec": ["counter_beast"],
    "scout_spec": ["counter_trap", "counter_ambush"],
    "leafwarden_spec": ["counter_poison", "counter_disease"],
    "shapeshifter_spec": ["counter_beast"],
    "shaman_spec": ["counter_elemental"],
    "inner_fist_spec": ["counter_minion"],
    "spirit_guardian_spec": ["counter_curse"],
    "ascetic_spec": ["counter_spell"],
    "warsinger_spec": ["counter_minion"],
    "herald_spec": ["counter_minion"],
    "inspiration_weaver_spec": ["counter_curse"],
    "oath_defender_spec": ["counter_boss", "counter_siege"],
    "rune_knight_spec": ["counter_spell", "counter_magic_barrier"],
    "vindicator_spec": ["counter_undead"],
    "demon_pact_spec": ["counter_curse"],
    "void_pact_spec": ["counter_void", "counter_magic_barrier"],
    "stellar_pact_spec": ["counter_void"],
}

# 10 NEW mission traits (Round 16.0)
MISSION_TRAITS = [
    {"slug": "long_mission_specialist", "name_it": "Specialista Missioni Lunghe",
     "description_it": "Aumenta il successo nelle missioni che durano oltre 30 minuti.",
     "counter_tags": []},
    {"slug": "swift_planner", "name_it": "Pianificatore Veloce",
     "description_it": "Riduce del 5% il tempo di completamento delle spedizioni.",
     "counter_tags": []},
    {"slug": "resourceful", "name_it": "Intraprendente",
     "description_it": "Possibilità di raccogliere un materiale extra dal bottino.",
     "counter_tags": []},
    {"slug": "careful", "name_it": "Prudente",
     "description_it": "Riduce la probabilità di ferite gravi.",
     "counter_tags": []},
    {"slug": "boss_tactician", "name_it": "Stratega Anti-Boss",
     "description_it": "Tattiche specifiche per affrontare i Boss.",
     "counter_tags": ["counter_boss"]},
    {"slug": "trap_sense", "name_it": "Sesto Senso per le Trappole",
     "description_it": "Riconosce e disinnesca trappole nascoste.",
     "counter_tags": ["counter_trap"]},
    {"slug": "arcane_disruptor", "name_it": "Disgregatore Arcano",
     "description_it": "Spezza incantesimi e barriere magiche nemiche.",
     "counter_tags": ["counter_spell", "counter_magic_barrier"]},
    {"slug": "undead_hunter", "name_it": "Cacciatore di Non-morti",
     "description_it": "Specializzato contro creature non viventi.",
     "counter_tags": ["counter_undead"]},
    {"slug": "beast_tracker", "name_it": "Tracciatore di Bestie",
     "description_it": "Segue tracce e prevede mosse di mostri animali.",
     "counter_tags": ["counter_beast"]},
    {"slug": "void_resistant", "name_it": "Resistente al Vuoto",
     "description_it": "Mente forgiata contro le suggestioni del Vuoto.",
     "counter_tags": ["counter_void"]},
]


async def _seed_collection(
    db, *, coll: str, docs: list[dict], audit_event: str, dry_run: bool,
) -> dict[str, int]:
    now = datetime.now(timezone.utc)
    inserted = 0
    skipped = 0
    for d in docs:
        slug = d["slug"]
        existing = await db[coll].find_one({"slug": slug})
        if existing:
            skipped += 1
            continue
        doc = {**d, "is_active": True,
               "created_at": now, "updated_at": now}
        if "id" not in doc:
            doc["id"] = str(uuid.uuid4())
        if dry_run:
            inserted += 1
            continue
        await db[coll].insert_one(doc)
        await write_audit(
            db, event_type=audit_event,
            actor_user_id=None, actor_guild_id=None,
            source="round160.phase4_seed",
            metadata={"slug": slug, "coll": coll},
        )
        inserted += 1
    return {"inserted": inserted, "skipped": skipped}


async def _enrich_dungeons(db, *, dry_run: bool) -> dict:
    updated = 0
    skipped = 0
    now = datetime.now(timezone.utc)
    for slug, threats in DUNGEON_THREAT_MAP.items():
        d = await db.dungeons.find_one({"slug": slug},
                                       {"_id": 0, "id": 1, "threat_tags": 1})
        if not d:
            skipped += 1
            continue
        if d.get("threat_tags") == threats:
            skipped += 1
            continue
        if dry_run:
            updated += 1
            continue
        await db.dungeons.update_one(
            {"slug": slug},
            {"$set": {"threat_tags": threats, "updated_at": now.isoformat()}},
        )
        await write_audit(
            db, event_type="dungeon_threats_assigned_round160",
            actor_user_id=None, actor_guild_id=None,
            source="round160.phase4_seed",
            metadata={"dungeon_slug": slug, "threat_tags": threats},
        )
        updated += 1
    return {"updated": updated, "skipped": skipped}


async def _update_spec_counters(db, *, dry_run: bool) -> dict:
    updated = 0
    skipped = 0
    now = datetime.now(timezone.utc)
    for slug, tags in SPEC_COUNTERS.items():
        existing = await db.class_specializations.find_one(
            {"slug": slug}, {"_id": 0, "counter_tags": 1})
        if not existing:
            skipped += 1
            continue
        if sorted(existing.get("counter_tags") or []) == sorted(tags):
            skipped += 1
            continue
        if dry_run:
            updated += 1
            continue
        await db.class_specializations.update_one(
            {"slug": slug},
            {"$set": {"counter_tags": tags, "updated_at": now}},
        )
        await write_audit(
            db, event_type="spec_counter_tags_updated_round160",
            actor_user_id=None, actor_guild_id=None,
            source="round160.phase4_seed",
            metadata={"spec_slug": slug, "counter_tags": tags},
        )
        updated += 1
    return {"updated": updated, "skipped": skipped}


async def _seed_mission_traits(db, *, dry_run: bool) -> dict:
    now = datetime.now(timezone.utc)
    inserted = 0
    skipped = 0
    for t in MISSION_TRAITS:
        existing = await db.adventurer_traits.find_one({"slug": t["slug"]})
        if existing:
            # Only patch counter_tags / origin if missing, never overwrite name.
            if existing.get("counter_tags") == t["counter_tags"]:
                skipped += 1
                continue
            if dry_run:
                inserted += 1
                continue
            await db.adventurer_traits.update_one(
                {"slug": t["slug"]},
                {"$set": {"counter_tags": t["counter_tags"],
                          "updated_at": now}},
            )
            await write_audit(
                db, event_type="trait_counter_tags_updated_round160",
                actor_user_id=None, actor_guild_id=None,
                source="round160.phase4_seed",
                metadata={"trait_slug": t["slug"],
                          "counter_tags": t["counter_tags"]},
            )
            inserted += 1
            continue
        doc = {
            **t,
            "id": str(uuid.uuid4()),
            "name": t["name_it"],
            "display_name_it": t["name_it"],
            "description": t["description_it"],
            "is_active": True,
            "is_positive": True,
            "modifier_type": "narrative",
            "modifier_value": 0,
            "affected_stat": "none",
            "round_intro": 16,
            "created_at": now,
            "updated_at": now,
        }
        if dry_run:
            inserted += 1
            continue
        await db.adventurer_traits.insert_one(doc)
        await write_audit(
            db, event_type="mission_trait_seeded_round160",
            actor_user_id=None, actor_guild_id=None,
            source="round160.phase4_seed",
            metadata={"trait_slug": t["slug"]},
        )
        inserted += 1
    return {"inserted": inserted, "skipped": skipped}


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    load_dotenv()
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    try:
        db = cli[os.environ["DB_NAME"]]
        threats = await _seed_collection(
            db, coll="dungeon_threats", docs=THREATS,
            audit_event="threat_seeded_round160", dry_run=args.dry_run)
        counters = await _seed_collection(
            db, coll="counter_tags", docs=COUNTERS,
            audit_event="counter_tag_seeded_round160", dry_run=args.dry_run)
        dungeons = await _enrich_dungeons(db, dry_run=args.dry_run)
        specs = await _update_spec_counters(db, dry_run=args.dry_run)
        traits = await _seed_mission_traits(db, dry_run=args.dry_run)
        print({"dry_run": args.dry_run,
               "threats": threats, "counter_tags": counters,
               "dungeons": dungeons, "specs": specs, "traits": traits})
        return 0
    finally:
        cli.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
