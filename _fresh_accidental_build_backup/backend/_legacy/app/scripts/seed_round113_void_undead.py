"""ROUND 11.3 Turno 3 — Fase 3B — TASK E: Void/Undead content pack.

Idempotent seed of 10 new dungeons + 5 new raid dungeons, all
Lore-coherent with the Orbus Lore Book (Ergolat, Vuoto Eterno, Filo
Spezzato, Sinfonia dei Fili, Irthe, Piaga dei Mille Volti,
Punta dell'Oblio, Obelischi del Vuoto, Orde Senza Volto, Sigillo
Spezzato, Tempio del Vuoto Eterno, Valys Mordivac, Esiliati del Vuoto
Eterno, Alevora Marionettista Lunare, Ashkaroth, Eclipthra, Gralca,
Xal'Zoraax, Figli di Irthe).

Run:
    cd /app/backend && MONGO_URL=... DB_NAME=... \
        python -m app.scripts.seed_round113_void_undead

Idempotency: every record is keyed by `slug`; re-runs upsert in place
(NO duplicates, NO mass deletes). Logs each insert/update.

Vocabulary policy: EVERY proper noun (place, entity, order, deity) used
in the `description` or `name` fields below is taken VERBATIM from the
Lore Book — no fantasy generic copy. Levels & power scale conservatively
so the preview environment (rosters Lv1-5) is still playable on the
lowest-tier dungeons.
"""
from __future__ import annotations

import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger("orbus.seed.void_undead")
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s: %(message)s")


# ─── 10 Dungeon Void/Undead ───────────────────────────────────────────────────
DUNGEONS = [
    # min_lvl 1 — onboarding
    {
        "slug": "echoes-of-the-broken-thread",
        "name": "Echi del Filo Spezzato",
        "description": (
            "Le prime crepe del Filo Spezzato attraversano un sentiero di pietra. "
            "Sussurri orfani guidano i nuovi reclutati lungo le crepe della Sinfonia dei Fili. "
            "Una prova lieve, ma il Vuoto ascolta già."
        ),
        "difficulty": 1, "min_adventurer_level": 1,
        "base_duration_seconds": 60, "recommended_power": 45,
        "base_gold_reward": 35, "base_xp_reward": 25,
    },
    # min_lvl 2
    {
        "slug": "shattered-seal-of-ergolat",
        "name": "Il Sigillo Spezzato di Ergolat",
        "description": (
            "Un piccolo sigillo dimenticato si è incrinato sotto il sussurro di Ergolat, "
            "il Vuoto che custodisce se stesso. Le Orde Senza Volto fiutano l'apertura: "
            "richiudete la frattura prima che la falla si allarghi."
        ),
        "difficulty": 2, "min_adventurer_level": 2,
        "base_duration_seconds": 60, "recommended_power": 70,
        "base_gold_reward": 60, "base_xp_reward": 45,
    },
    # min_lvl 4
    {
        "slug": "obelisks-of-the-void",
        "name": "Gli Obelischi del Vuoto",
        "description": (
            "Quattro Obelischi Neri pulsano in una valle dimenticata. Ogni obelisco "
            "è un'eco minore del Tempio del Vuoto Eterno e attira piccoli Figli del Vuoto. "
            "Disinnescate la risonanza prima che le Orde Senza Volto si moltiplichino."
        ),
        "difficulty": 3, "min_adventurer_level": 4,
        "base_duration_seconds": 90, "recommended_power": 110,
        "base_gold_reward": 90, "base_xp_reward": 75,
    },
    # min_lvl 6
    {
        "slug": "plague-warrens-of-irthe",
        "name": "Tane Putride della Piaga dei Mille Volti",
        "description": (
            "Sotto una collina cariata pulsa la Piaga dei Mille Volti, dono perverso di Irthe. "
            "I Figli di Irthe hanno scavato gallerie di carne e tendine, ognuna un volto "
            "diverso che recita la stessa litania."
        ),
        "difficulty": 4, "min_adventurer_level": 6,
        "base_duration_seconds": 120, "recommended_power": 170,
        "base_gold_reward": 140, "base_xp_reward": 120,
    },
    # min_lvl 8
    {
        "slug": "moonlit-strings-of-alevora",
        "name": "I Fili Lunari di Alevora",
        "description": (
            "Alevora, la Marionettista Lunare, ha teso i suoi fili sopra un boschetto morto. "
            "I cadaveri danzano come marionette obbedienti alla Sinfonia dei Fili. "
            "Recidete i nodi prima che la pantomima diventi richiamo."
        ),
        "difficulty": 5, "min_adventurer_level": 8,
        "base_duration_seconds": 180, "recommended_power": 240,
        "base_gold_reward": 210, "base_xp_reward": 180,
    },
    # min_lvl 10
    {
        "slug": "ashkaroth-crypt-court",
        "name": "Corte Cripta di Ashkaroth",
        "description": (
            "Una corte sepolcrale dove il signore Ashkaroth raduna i suoi nobili decaduti. "
            "Le loro corone arrugginiscono ma le pretese restano: un tribunale dei morti "
            "che chiede il vostro nome scritto nel Sussurro del Nulla."
        ),
        "difficulty": 6, "min_adventurer_level": 10,
        "base_duration_seconds": 300, "recommended_power": 320,
        "base_gold_reward": 300, "base_xp_reward": 250,
    },
    # min_lvl 12
    {
        "slug": "eclipthra-veiled-sanctum",
        "name": "Santuario Velato di Eclipthra",
        "description": (
            "Eclipthra ha velato un santuario sotto un'eclissi che non finisce mai. "
            "Pochi che vi entrano ricordano il proprio nome: il Vuoto che Divora rosicchia "
            "la memoria prima della carne."
        ),
        "difficulty": 7, "min_adventurer_level": 12,
        "base_duration_seconds": 600, "recommended_power": 400,
        "base_gold_reward": 400, "base_xp_reward": 320,
    },
    # min_lvl 15
    {
        "slug": "gralca-tide-of-the-deep",
        "name": "La Marea di Gralca",
        "description": (
            "Le maree di Gralca portano alla riva carcasse senza occhi e canti senza bocca. "
            "Le profondità custodiscono un eco della Breccia del Vuoto, e la marea ne ripete "
            "la cadenza con ogni risacca."
        ),
        "difficulty": 8, "min_adventurer_level": 15,
        "base_duration_seconds": 900, "recommended_power": 470,
        "base_gold_reward": 520, "base_xp_reward": 410,
    },
    # min_lvl 18
    {
        "slug": "xal-zoraax-throat-of-silence",
        "name": "La Gola di Silenzio di Xal'Zoraax",
        "description": (
            "Xal'Zoraax respira solo silenzio. La sua gola è una caverna in cui ogni suono "
            "muore prima di nascere — l'opposto perfetto della Sinfonia dei Fili. "
            "Sopravvivere significa parlare con i gesti soltanto."
        ),
        "difficulty": 9, "min_adventurer_level": 18,
        "base_duration_seconds": 1200, "recommended_power": 540,
        "base_gold_reward": 680, "base_xp_reward": 520,
    },
    # min_lvl 20
    {
        "slug": "tip-of-oblivion-trial",
        "name": "Prova della Punta dell'Oblio",
        "description": (
            "La Punta dell'Oblio era prigione e fine: oggi un suo ramo accessorio si è "
            "aperto come prova di soglia. Gli Esiliati del Vuoto Eterno vi attendono "
            "per misurare se siete pronti al Rituale del Vuoto."
        ),
        "difficulty": 10, "min_adventurer_level": 20,
        "base_duration_seconds": 1800, "recommended_power": 620,
        "base_gold_reward": 850, "base_xp_reward": 650,
    },
]


# ─── 5 Raid Void/Undead ───────────────────────────────────────────────────────
RAIDS = [
    # min_lvl 10
    {
        "slug": "rituale-del-vuoto-orde",
        "name_it": "Il Rituale del Vuoto",
        "name": "Ritual of the Void",
        "description_it": (
            "Le Orde Senza Volto stanno completando un Rituale del Vuoto in una piana "
            "deserta. Quattro squadre devono spezzare i quattro Obelischi Neri "
            "simultaneamente prima che la cerimonia si chiuda. Una squadra in ritardo "
            "fa fallire tutte le altre — il Vuoto non perdona la dissonanza."
        ),
        "description": (
            "The Faceless Hordes are completing a Void Ritual on a wasteland plain. "
            "Four parties must shatter four Black Obelisks simultaneously before the "
            "ceremony closes. A late party dooms the others — the Void forgives no dissonance."
        ),
        "tier": 1, "min_adventurer_level": 10,
        "base_duration_seconds": 1800, "recommended_power_combined": 1500,
        "base_gold_reward": 700, "base_xp_per_member": 120,
    },
    # min_lvl 14
    {
        "slug": "figli-di-irthe-rising",
        "name_it": "Marcia dei Figli di Irthe",
        "name": "March of Irthe's Children",
        "description_it": (
            "I Figli di Irthe si sono rialzati in falangi di carne unita. Ogni passo "
            "ripete la litania della Piaga dei Mille Volti. Reggete le linee per "
            "abbastanza tempo che il Sigillo Spezzato si richiuda dal lato vivente."
        ),
        "description": (
            "Irthe's Children rise in fused-flesh phalanxes. Each footstep echoes the "
            "litany of the Thousand-Faces Plague. Hold the lines long enough for the "
            "Broken Seal to close from the side of the living."
        ),
        "tier": 1, "min_adventurer_level": 14,
        "base_duration_seconds": 2100, "recommended_power_combined": 2200,
        "base_gold_reward": 950, "base_xp_per_member": 160,
    },
    # min_lvl 18
    {
        "slug": "alevora-marionetta-grande",
        "name_it": "Il Gran Teatro di Alevora",
        "name": "Alevora's Grand Theatre",
        "description_it": (
            "Alevora, la Marionettista Lunare, ha allestito un Gran Teatro sotto la luna piena. "
            "Vent'avventurieri devono ballare al ritmo della Sinfonia dei Fili senza farsi "
            "intrecciare le membra. Spezzate il bastone della direttrice prima del finale."
        ),
        "description": (
            "Alevora, the Moonlit Puppeteer, has staged a Grand Theatre under a full moon. "
            "Twenty adventurers must dance to the Symphony of Threads without letting their "
            "limbs be threaded. Break the conductor's baton before the finale."
        ),
        "tier": 2, "min_adventurer_level": 18,
        "base_duration_seconds": 2400, "recommended_power_combined": 3200,
        "base_gold_reward": 1400, "base_xp_per_member": 220,
    },
    # min_lvl 24
    {
        "slug": "tempio-del-vuoto-eterno",
        "name_it": "Tempio del Vuoto Eterno",
        "name": "Temple of the Eternal Void",
        "description_it": (
            "Il Tempio del Vuoto Eterno si apre dopo secoli di silenzio. Gli Esiliati del "
            "Vuoto Eterno vi attendono come custodi disperati. Quattro squadre devono "
            "attraversare quattro sale concentriche, ognuna un volto del Vuoto che Divora."
        ),
        "description": (
            "The Temple of the Eternal Void opens after centuries of silence. The Exiles "
            "of the Eternal Void stand as desperate custodians. Four parties must clear "
            "four concentric halls, each a face of the Devouring Void."
        ),
        "tier": 2, "min_adventurer_level": 24,
        "base_duration_seconds": 2700, "recommended_power_combined": 4400,
        "base_gold_reward": 1900, "base_xp_per_member": 300,
    },
    # min_lvl 30
    {
        "slug": "valys-mordivac-final-whisper",
        "name_it": "L'Ultimo Sussurro di Valys Mordivac",
        "name": "Valys Mordivac's Final Whisper",
        "description_it": (
            "Valys Mordivac, custode del Sussurro del Nulla, ha letto l'ultima pagina. "
            "Le Mani che reggevano il libro ora reggono il Filo Spezzato. Affrontatelo "
            "alla Punta dell'Oblio: la sua sconfitta non guarisce la Breccia del Vuoto, "
            "ma compra al mondo un altro respiro."
        ),
        "description": (
            "Valys Mordivac, keeper of the Whisper of the Naught, has read the last page. "
            "The Hands that held the book now hold the Broken Thread. Face them at the "
            "Tip of Oblivion: their defeat does not heal the Void Breach, but it buys "
            "the world one more breath."
        ),
        "tier": 3, "min_adventurer_level": 30,
        "base_duration_seconds": 3600, "recommended_power_combined": 6200,
        "base_gold_reward": 2800, "base_xp_per_member": 450,
    },
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def upsert_dungeons(db) -> dict:
    inserted, updated = 0, 0
    for d in DUNGEONS:
        existing = await db.dungeons.find_one({"slug": d["slug"]}, {"_id": 0, "id": 1})
        doc = {
            **d,
            "required_team_size": 3,
            "is_active": True,
            "is_legacy": False,
            "is_5p": False,
            "gate": {},
            "updated_at": _now(),
        }
        if existing:
            await db.dungeons.update_one({"slug": d["slug"]}, {"$set": doc})
            updated += 1
            logger.info("dungeon UPDATED slug=%s min_lvl=%d", d["slug"], d["min_adventurer_level"])
        else:
            doc["id"] = str(uuid.uuid4())
            doc["created_at"] = _now()
            await db.dungeons.insert_one(doc)
            inserted += 1
            logger.info("dungeon INSERTED slug=%s id=%s", d["slug"], doc["id"])
    return {"inserted": inserted, "updated": updated, "total": len(DUNGEONS)}


async def upsert_raids(db) -> dict:
    inserted, updated = 0, 0
    for r in RAIDS:
        existing = await db.raid_dungeons.find_one({"slug": r["slug"]}, {"_id": 0})
        doc = {
            **r,
            "min_roster_size": 20,
            "required_party_count": 4,
            "required_party_size": 5,
            "guaranteed_dragon_essence_min": 1,
            "guaranteed_dragon_essence_max": 3,
            "is_active": True,
            "gate": {"min_roster_size": 20},
            "loot_pool_slug": f"raid_r{r['tier']}",
            "party_focus_hints": [
                {"party_idx": 1, "preferred_role": "Tank", "label_it": "Vanguardia", "label_en": "Vanguard"},
                {"party_idx": 2, "preferred_role": "Healer", "label_it": "Sostegno", "label_en": "Sustain"},
                {"party_idx": 3, "preferred_role": "DPS", "label_it": "Assalto", "label_en": "Assault"},
                {"party_idx": 4, "preferred_role": None, "label_it": "Riserva", "label_en": "Reserve"},
            ],
            "updated_at": _now(),
        }
        if existing:
            await db.raid_dungeons.update_one({"slug": r["slug"]}, {"$set": doc})
            updated += 1
            logger.info("raid UPDATED slug=%s min_lvl=%d", r["slug"], r["min_adventurer_level"])
        else:
            doc["id"] = str(uuid.uuid4())
            doc["created_at"] = _now()
            await db.raid_dungeons.insert_one(doc)
            inserted += 1
            logger.info("raid INSERTED slug=%s id=%s", r["slug"], doc["id"])
    return {"inserted": inserted, "updated": updated, "total": len(RAIDS)}


async def run() -> dict:
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        raise RuntimeError("MONGO_URL and DB_NAME env vars are required.")
    cli = AsyncIOMotorClient(mongo_url)
    db = cli[db_name]
    try:
        d_report = await upsert_dungeons(db)
        r_report = await upsert_raids(db)
        logger.info("DONE — dungeons: %s, raids: %s", d_report, r_report)
        return {"dungeons": d_report, "raids": r_report}
    finally:
        cli.close()


if __name__ == "__main__":
    asyncio.run(run())
