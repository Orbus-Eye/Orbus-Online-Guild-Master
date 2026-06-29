"""ROUND 15 — Fase 1 / Task 2: idempotent migration for class identity.

Adds the following descriptive fields to every active class document in
`adventurer_classes`:

    primary_stat (string, mandatory for is_active=True)
    secondary_stats (list[str])
    allowed_weapon_tags (list[str])
    allowed_armor_tags (list[str])
    preferred_item_tags (list[str])
    role_tags (list[str])
    xp_primary_stat_policy (dict, **inactive in Phase 1** — defined only)
    guide_description_it (str)
    guide_description_en (str)

Idempotency contract:
    Read → diff → write only the missing/changed fields. Re-runs on a
    clean DB produce 0 updates. Backfill only writes `primary_stat` if
    null (test-class-* docs are skipped because is_active=False).

Audit:
    Every doc actually written emits an `audit_logs` row with
    `event = 'class_identity_updated_round15'`. Inactive/test docs
    are never logged.

Run:
    cd /app/backend
    export $(grep -v '^#' .env | xargs)
    python3 -m app.scripts.round15_seed_class_identity
    python3 -m app.scripts.round15_seed_class_identity --dry-run
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient


# Single source of truth for the 12 active classes.
CLASS_IDENTITY: dict[str, dict] = {
    # ─── TANKS ────────────────────────────────────────────────────────────
    "warrior": {
        "primary_stat": "strength",
        "secondary_stats": ["endurance"],
        "allowed_weapon_tags": ["sword", "axe", "mace", "two_handed"],
        "allowed_armor_tags": ["heavy", "shield", "medium"],
        "preferred_item_tags": ["frontline", "stamina"],
        "role_tags": ["tank", "frontline"],
        "guide_description_it": (
            "Il Guerriero è la spina dorsale della linea avanzata. "
            "Pareggia colpi con la corazza, intercetta nemici con lo "
            "scudo, e tiene il fronte mentre il resto della squadra "
            "lavora. Forza alta per imporsi nei dungeon corpo a corpo "
            "e Resistenza per non cedere. La sua primary stat è Forza: "
            "una stat troppo bassa rallenterà la sua crescita di XP "
            "(meccanica attiva da Round 15.2)."
        ),
        "guide_description_en": (
            "The Warrior anchors the front line. Heavy armour, shield, "
            "and a willingness to take the first hit. Strength as primary, "
            "Endurance as backbone."
        ),
    },
    "paladin": {
        "primary_stat": "faith",
        "secondary_stats": ["strength", "endurance"],
        "allowed_weapon_tags": ["sword", "mace", "two_handed"],
        "allowed_armor_tags": ["heavy", "shield", "holy"],
        "preferred_item_tags": ["frontline", "holy", "support_heal"],
        "role_tags": ["tank", "off_healer"],
        "guide_description_it": (
            "Il Paladino combina lo scudo del tank con la mano "
            "guaritrice del sacerdote. È meno duro di un Guerriero "
            "puro, ma può curare l'alleato accanto e applicare colpi "
            "sacri ai nemici corrotti. La sua primary stat è Fede — "
            "scarsa, e la sua identità ibrida sparisce. Da 15.2 "
            "questo costerà XP."
        ),
        "guide_description_en": (
            "The Paladin trades raw Warrior toughness for hybrid utility: "
            "shield, blade, and a hand of light. Faith primary."
        ),
    },
    # ─── PHYSICAL DPS ─────────────────────────────────────────────────────
    "rogue": {
        "primary_stat": "agility",
        "secondary_stats": ["strength"],
        "allowed_weapon_tags": ["dagger", "shortsword", "finesse"],
        "allowed_armor_tags": ["light", "leather"],
        "preferred_item_tags": ["stealth", "crit", "finesse"],
        "role_tags": ["dps_melee", "stealth"],
        "guide_description_it": (
            "Il Ladro si infila dove gli altri non riescono. Veloce, "
            "leggero, letale al primo colpo se coglie il fianco. "
            "L'Agilità governa tutto: schivata, danno critico, "
            "iniziativa. Senza AGI alta il Ladro è solo un Guerriero "
            "magro. Da 15.2 una primary bassa lo penalizzerà."
        ),
        "guide_description_en": (
            "The Rogue thrives on speed and angles. Agility primary, "
            "Strength to back up the killing strike."
        ),
    },
    "ranger": {
        "primary_stat": "agility",
        "secondary_stats": ["endurance"],
        "allowed_weapon_tags": ["bow", "crossbow", "ranged"],
        "allowed_armor_tags": ["light", "medium", "leather"],
        "preferred_item_tags": ["ranged", "tracking", "outdoor"],
        "role_tags": ["dps_ranged", "scout"],
        "guide_description_it": (
            "Il Ranger lavora a distanza: archi, balestre, frecce "
            "stregate. Non è un assassino — è un cacciatore. "
            "Resistenza per lunghe esplorazioni, Agilità per mirare. "
            "Senza Agilità alta i tiri scivolano via. Da 15.2 una "
            "primary bassa ridurrà l'XP guadagnato."
        ),
        "guide_description_en": (
            "The Ranger keeps distance and patience. Agility primary, "
            "Endurance for long marches and recovery."
        ),
    },
    "assassin": {
        "primary_stat": "agility",
        "secondary_stats": ["strength"],
        "allowed_weapon_tags": ["dagger", "finesse", "poison"],
        "allowed_armor_tags": ["light"],
        "preferred_item_tags": ["stealth", "crit", "poison"],
        "role_tags": ["dps_burst", "stealth"],
        "guide_description_it": (
            "L'Assassino vive per il colpo che chiude lo scontro "
            "prima che inizi. Il Ladro ruba in mezzo al combattimento; "
            "l'Assassino aspetta nell'ombra e poi sparisce. Agilità "
            "estrema, armatura inesistente — un solo errore e cade. "
            "Da 15.2 una stat primaria troppo bassa rallenterà l'XP."
        ),
        "guide_description_en": (
            "The Assassin lives one perfect strike at a time. Pure Agility, "
            "thin armour, no second chances."
        ),
    },
    "berserker": {
        "primary_stat": "strength",
        "secondary_stats": ["endurance"],
        "allowed_weapon_tags": ["two_handed", "axe", "rage"],
        "allowed_armor_tags": ["medium", "light"],
        "preferred_item_tags": ["frontline", "rage", "anti_armor"],
        "role_tags": ["dps_melee", "frontline"],
        "guide_description_it": (
            "Il Berserker rinuncia all'armatura pesante in cambio di "
            "potenza bruta. Due mani sull'arma, nessuno scudo, e un "
            "boost al danno mentre la salute scende. Forza estrema "
            "come priorità assoluta. Da 15.2, una primary bassa "
            "spegnerà l'XP."
        ),
        "guide_description_en": (
            "The Berserker swings hardest the closer to death he gets. "
            "Strength uber alles, Endurance to outlast the swing."
        ),
    },
    "monk": {
        "primary_stat": "agility",
        "secondary_stats": ["endurance", "faith"],
        "allowed_weapon_tags": ["unarmed", "staff", "martial"],
        "allowed_armor_tags": ["cloth", "light", "martial"],
        "preferred_item_tags": ["martial", "ki", "self_heal"],
        "role_tags": ["dps_melee", "self_sustain"],
        "guide_description_it": (
            "Il Monaco trasforma corpo e respiro in armi: nessuna spada, "
            "nessuna armatura pesante, solo allenamento. Più resistente "
            "del Ladro, meno fragile dell'Assassino, e quel pizzico di "
            "Fede gli permette di curarsi piccole ferite tra una mossa "
            "e l'altra. Agilità su tutto. Da 15.2 una primary bassa "
            "rallenterà la sua crescita."
        ),
        "guide_description_en": (
            "The Monk weaponises body and breath. Agility primary, "
            "Endurance and a touch of Faith for self-sustain."
        ),
    },
    # ─── MAGIC DPS ────────────────────────────────────────────────────────
    "mage": {
        "primary_stat": "intellect",
        "secondary_stats": ["endurance"],
        "allowed_weapon_tags": ["staff", "wand", "arcane"],
        "allowed_armor_tags": ["cloth", "robe", "light"],
        "preferred_item_tags": ["arcane", "burst", "control"],
        "role_tags": ["dps_caster", "control"],
        "guide_description_it": (
            "Il Mago studia le tavole arcane e libera incantesimi devastanti. "
            "Fragile in armatura, ma la sua Intelletto governa tutto: "
            "potenza, varietà, costo magico. Resistenza per sopravvivere "
            "alla prima onda. Da 15.2 una primary bassa frenerà l'XP."
        ),
        "guide_description_en": (
            "The Mage trades armour for arcane firepower. Intellect primary, "
            "Endurance to survive the cast."
        ),
    },
    "necromancer": {
        "primary_stat": "intellect",
        "secondary_stats": ["agility"],
        "allowed_weapon_tags": ["staff", "scythe", "dark"],
        "allowed_armor_tags": ["cloth", "bone"],
        "preferred_item_tags": ["dark", "drain", "undead"],
        "role_tags": ["dps_caster", "summoner"],
        "guide_description_it": (
            "Il Negromante è il fratello oscuro del Mago: pari Intelletto "
            "ma anziché controllare l'arcano controlla la decadenza. Evoca "
            "scheletri, drena vita, plasma servitori dai cadaveri. "
            "Agilità secondaria per evitare il contraccolpo. Da 15.2 una "
            "primary bassa fermerà la crescita."
        ),
        "guide_description_en": (
            "The Necromancer drains, raises and rots. Intellect primary, "
            "Agility to keep distance from the bound spirits."
        ),
    },
    # ─── HEALERS ──────────────────────────────────────────────────────────
    "priest": {
        "primary_stat": "faith",
        "secondary_stats": ["intellect"],
        "allowed_weapon_tags": ["mace", "scepter", "holy"],
        "allowed_armor_tags": ["cloth", "robe", "holy"],
        "preferred_item_tags": ["heal", "holy", "single_target"],
        "role_tags": ["healer_dedicated", "support"],
        "guide_description_it": (
            "Il Sacerdote cura la singola ferita decisiva: braccio "
            "spezzato, anima vacillante, alleato sul punto di cadere. "
            "Più focalizzato del Druido ma meno versatile. La Fede è "
            "tutto. Da 15.2 una Fede troppo bassa azzererà la crescita."
        ),
        "guide_description_en": (
            "The Priest is the single-target lifeline. Faith dominant, "
            "Intellect for the longer chants."
        ),
    },
    "druid": {
        "primary_stat": "faith",
        "secondary_stats": ["intellect"],
        "allowed_weapon_tags": ["staff", "club", "natural"],
        "allowed_armor_tags": ["leather", "cloth", "natural"],
        "preferred_item_tags": ["nature", "heal_aoe", "shapeshift"],
        "role_tags": ["healer_aoe", "support"],
        "guide_description_it": (
            "Il Druido è meno specializzato del Sacerdote ma più adattabile: "
            "cura più alleati assieme, sa danneggiare con incantesimi "
            "naturali, e in pizzo può mutare forma. Fede primaria, "
            "Intelletto vicino per gli incantesimi più complessi. "
            "Da 15.2 una primary bassa ridurrà l'XP."
        ),
        "guide_description_en": (
            "The Druid mends crowds and shifts shape. Faith primary, "
            "Intellect close behind."
        ),
    },
    # ─── SUPPORT ──────────────────────────────────────────────────────────
    "bard": {
        "primary_stat": "intellect",
        "secondary_stats": ["agility", "faith"],
        "allowed_weapon_tags": ["dagger", "instrument", "sonic"],
        "allowed_armor_tags": ["light", "leather"],
        "preferred_item_tags": ["buff", "debuff", "sonic", "social"],
        "role_tags": ["support", "buffer", "debuffer"],
        "guide_description_it": (
            "Il Bardo non fa il danno più alto né cura più di tutti. Ma "
            "moltiplica chi ha vicino: alleati che colpiscono più forte, "
            "nemici che sbagliano la prossima mossa. Intelletto e una "
            "buona Agilità per restare lontano dai colpi. Una primary "
            "bassa, da 15.2, vorrà dire canzoni stonate e XP zero."
        ),
        "guide_description_en": (
            "The Bard tilts the fight without firing the loudest shot. "
            "Intellect primary; Agility and Faith for verses and travel."
        ),
    },
}


# Placeholder XP policy — Phase 1 only declares it; Phase 2 will turn it on.
DEFAULT_XP_POLICY = {
    "enabled": False,                # 15.2 will flip to True
    "threshold_per_level": 1,        # primary stat ≥ 1 required at L1
    "debuff_steps": [
        {"shortfall": 1, "xp_mult": 0.75},
        {"shortfall": 2, "xp_mult": 0.50},
        {"shortfall": 3, "xp_mult": 0.25},
    ],
    "schema_version": 1,
}


async def _audit_log(db, event: str, payload: dict) -> None:
    """Append an audit_logs row. Non-fatal if collection missing."""
    try:
        await db.audit_logs.insert_one({
            "event": event,
            "payload": payload,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] audit log insert failed: {exc!r}")


async def main():
    parser = argparse.ArgumentParser(
        description="Round 15 — seed primary_stat + class identity (idempotent).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Calcola il delta senza scrivere su Mongo.",
    )
    args = parser.parse_args()

    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    total_active = await db.adventurer_classes.count_documents({"is_active": True})
    total_all = await db.adventurer_classes.count_documents({})
    print(f"adventurer_classes — total={total_all}, active={total_active}")

    expected = set(CLASS_IDENTITY.keys())
    db_active_slugs = set()
    async for d in db.adventurer_classes.find({"is_active": True}, {"_id": 0, "slug": 1}):
        db_active_slugs.add(d["slug"])

    missing_in_seed = db_active_slugs - expected
    missing_in_db = expected - db_active_slugs
    if missing_in_seed:
        print(f"[warn] classi attive presenti in DB ma non nel seed map: {sorted(missing_in_seed)}")
    if missing_in_db:
        print(f"[warn] classi del seed map non trovate fra le attive in DB: {sorted(missing_in_db)}")

    updated = 0
    untouched = 0
    skipped_inactive = 0
    conflicts: list[dict] = []
    now_iso = datetime.now(timezone.utc).isoformat()

    for slug, ident in CLASS_IDENTITY.items():
        doc = await db.adventurer_classes.find_one({"slug": slug}, {"_id": 0})
        if not doc:
            print(f"[skip] '{slug}' non trovato in adventurer_classes")
            continue
        if not doc.get("is_active", False):
            skipped_inactive += 1
            continue

        # Build the delta only with missing/empty fields → idempotent.
        delta: dict = {}
        for k, v in ident.items():
            if doc.get(k) in (None, "", []) or doc.get(k) != v:
                # If the doc already has a non-empty primary_stat that
                # disagrees with the seed map, log it as conflict but
                # still respect the seed map (the seed is the truth source).
                if k == "primary_stat" and doc.get(k) and doc.get(k) != v:
                    conflicts.append({
                        "slug": slug, "db": doc.get(k), "seed": v,
                    })
                delta[k] = v

        if doc.get("xp_primary_stat_policy") is None:
            delta["xp_primary_stat_policy"] = DEFAULT_XP_POLICY

        if not delta:
            untouched += 1
            continue

        delta["updated_at"] = now_iso

        if args.dry_run:
            print(f"[dry-run] {slug}: would update {sorted(delta.keys())}")
        else:
            await db.adventurer_classes.update_one(
                {"slug": slug, "is_active": True},
                {"$set": delta},
            )
            await _audit_log(db, "class_identity_updated_round15", {
                "slug": slug,
                "fields_set": sorted(delta.keys()),
            })
        updated += 1

    print()
    print("=== SUMMARY ===")
    print(f"  updated:           {updated}")
    print(f"  untouched:         {untouched}")
    print(f"  skipped_inactive:  {skipped_inactive}")
    print(f"  conflicts:         {len(conflicts)}")
    if conflicts:
        for c in conflicts:
            print(f"    - {c}")
    if args.dry_run:
        print("  (dry-run: nessuna scrittura su Mongo, nessun audit log)")

    # Final verification.
    with_primary = await db.adventurer_classes.count_documents(
        {"is_active": True, "primary_stat": {"$nin": [None, ""]}},
    )
    print(f"  classi attive con primary_stat:  {with_primary}/{total_active}")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
