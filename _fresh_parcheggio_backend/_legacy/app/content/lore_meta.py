"""ROUND 13a — Single source of truth for content lore metadata.

Maps slugs → lore themes, content families, is_new flags. Used by:
  * Dungeon / raid serializers (expose `is_new`, `content_family`, `is_void_undead`).
  * Seed scripts (apply lore patches in bulk, idempotent).

NO spoilers: enemy_families / narrative_hook expose player-facing copy only.
"""
from __future__ import annotations

# ─── 10 dungeon Void/Undead nuovi (R11.3) ─────────────────────────────────────
NEW_DUNGEON_SLUGS_R113: set[str] = {
    "echoes-of-the-broken-thread",
    "shattered-seal-of-ergolat",
    "obelisks-of-the-void",
    "plague-warrens-of-irthe",
    "moonlit-strings-of-alevora",
    "ashkaroth-crypt-court",
    "eclipthra-veiled-sanctum",
    "gralca-tide-of-the-deep",
    "xal-zoraax-throat-of-silence",
    "tip-of-oblivion-trial",
}

NEW_RAID_SLUGS_R113: set[str] = {
    "rituale-del-vuoto-orde",
    "figli-di-irthe-rising",
    "alevora-marionetta-grande",
    "tempio-del-vuoto-eterno",
    "valys-mordivac-final-whisper",
}


# ─── Lore patch table per dungeon (slug → metadata) ───────────────────────────
# `content_family`: baseline | void_undead | divine | nature | memory | cycle | arcane | urban
# `lore_theme`: ergolat, irthe, alevora, ashkaroth, eclipthra, gralca, xal_zoraax,
#               vuoto, non-morte, memoria, ciclo, soe, velur, efreto, halodi,
#               ambash, draco, infernale, celeste, fucina, mare, urban, frontiera
# `emotional_tone`: mystery | dread | wonder | melancholy | tension | grim | hope
# `spoiler_level`: public | mystery | hidden
DUNGEON_LORE_PATCHES: dict[str, dict] = {
    # ───── Baseline 22 (rework lore additivo) ─────
    "sewer-nest": {
        "name_it": "Nido nelle Fogne",
        "lore_theme": "urban", "content_family": "baseline",
        "emotional_tone": "tension", "location_hint": "fogne sotto le città di confine",
        "narrative_hook": "Qualcosa è risalito dal basso e ora scava verso la superficie.",
        "enemy_families": ["rats", "kobolds"], "spoiler_level": "public",
    },
    "goblin-warrens": {
        "name_it": "Tane dei Goblin",
        "lore_theme": "frontiera", "content_family": "baseline",
        "emotional_tone": "tension", "location_hint": "boschi di Halodi orientale",
        "narrative_hook": "I tamburi dei goblin segnano il passo di un'invasione minore.",
        "enemy_families": ["goblins"], "spoiler_level": "public",
    },
    "bandit-hideout": {
        "name_it": "Covo dei Banditi",
        "lore_theme": "urban", "content_family": "baseline",
        "emotional_tone": "tension", "location_hint": "passi di montagna di Aveol",
        "narrative_hook": "Briganti disertori della Crociata d'Argento si nascondono qui.",
        "enemy_families": ["bandits"], "spoiler_level": "public",
    },
    "wolf-den-5p": {
        "name_it": "Tana dei Lupi",
        "lore_theme": "soe", "content_family": "nature",
        "emotional_tone": "wonder", "location_hint": "foreste settentrionali di Soe",
        "narrative_hook": "Lupi più grandi della media seguono un'eco che non senti.",
        "enemy_families": ["warg", "wolves"], "spoiler_level": "public",
    },
    "frost-cave-5p": {
        "name_it": "Caverna del Gelo",
        "lore_theme": "halodi", "content_family": "nature",
        "emotional_tone": "melancholy", "location_hint": "ghiacciai di Halodi",
        "narrative_hook": "Il gelo qui non sciogli con il fuoco. Solo con la memoria.",
        "enemy_families": ["frost_elementals"], "spoiler_level": "public",
    },
    "salt-marsh-5p": {
        "name_it": "Palude Salata",
        "lore_theme": "velur", "content_family": "memory",
        "emotional_tone": "melancholy", "location_hint": "estuari dimenticati di Velur",
        "narrative_hook": "L'acqua salata conserva i ricordi che la terra rifiuta.",
        "enemy_families": ["bog_revenants"], "spoiler_level": "public",
    },
    "shadow-crypts": {
        "name_it": "Cripte d'Ombra",
        "lore_theme": "irthe", "content_family": "void_undead",
        "emotional_tone": "dread", "location_hint": "cripte ai margini del culto di Irthe",
        "narrative_hook": "Gli Esiliati pregano qui chi non risponde più.",
        "enemy_families": ["wights", "shadowkin"], "spoiler_level": "mystery",
    },
    "druid-grove": {
        "name_it": "Bosco dei Druidi Corrotti",
        "lore_theme": "soe", "content_family": "nature",
        "emotional_tone": "grim", "location_hint": "boschi di Soe inverditi a forza",
        "narrative_hook": "Una pioggia di linfa nera ha rotto il giuramento del bosco.",
        "enemy_families": ["corrupted_druids", "treants"], "spoiler_level": "public",
    },
    "cursed-mines": {
        "name_it": "Miniere Maledette",
        "lore_theme": "efreto", "content_family": "arcane",
        "emotional_tone": "dread", "location_hint": "vene profonde sotto Efreto",
        "narrative_hook": "I minatori cantano una canzone che non hanno imparato.",
        "enemy_families": ["miners_undead"], "spoiler_level": "mystery",
    },
    "sunken-library": {
        "name_it": "Biblioteca Sommersa",
        "lore_theme": "memoria", "content_family": "memory",
        "emotional_tone": "wonder", "location_hint": "rovine sotto il livello del mare di Velur",
        "narrative_hook": "Pagine leggono i lettori. Stai attento a cosa pensi qui.",
        "enemy_families": ["scribe_specters"], "spoiler_level": "mystery",
    },
    "iron-foundry-5p": {
        "name_it": "Fonderia di Ferro",
        "lore_theme": "fucina", "content_family": "arcane",
        "emotional_tone": "tension", "location_hint": "officine di Aveol",
        "narrative_hook": "Le incudini battono da sole, senza fabbri.",
        "enemy_families": ["construct"], "spoiler_level": "public",
    },
    "silent-monastery-5p": {
        "name_it": "Monastero del Silenzio",
        "lore_theme": "memoria", "content_family": "memory",
        "emotional_tone": "melancholy", "location_hint": "vette di Halodi superiore",
        "narrative_hook": "Qui i monaci hanno smesso di parlare prima che il Vuoto ascoltasse.",
        "enemy_families": ["silent_monks"], "spoiler_level": "mystery",
    },
    "pirate-fleet-5p": {
        "name_it": "Flotta dei Corsari",
        "lore_theme": "mare", "content_family": "baseline",
        "emotional_tone": "tension", "location_hint": "rotte del Mare di Velur",
        "narrative_hook": "Le bandiere nere coprono una nave che non dovrebbe galleggiare.",
        "enemy_families": ["pirates"], "spoiler_level": "public",
    },
    "dragons-hoard": {
        "name_it": "Tesoro del Drago",
        "lore_theme": "draco", "content_family": "arcane",
        "emotional_tone": "wonder", "location_hint": "antri pre-cataclisma",
        "narrative_hook": "Il drago dorme. Le monete contano i suoi sogni.",
        "enemy_families": ["draconic"], "spoiler_level": "mystery",
    },
    "lich-sanctum": {
        "name_it": "Santuario del Lich",
        "lore_theme": "irthe", "content_family": "void_undead",
        "emotional_tone": "dread", "location_hint": "cattedrale profanata di Irthe",
        "narrative_hook": "Il lich ha negoziato con la morte. La morte ride poco.",
        "enemy_families": ["lich", "undead"], "spoiler_level": "mystery",
    },
    "storm-spire": {
        "name_it": "Guglia della Tempesta",
        "lore_theme": "ambash", "content_family": "arcane",
        "emotional_tone": "wonder", "location_hint": "faglia di Ambash superiore",
        "narrative_hook": "Il fulmine qui non scende dal cielo. Sale.",
        "enemy_families": ["storm_elementals"], "spoiler_level": "public",
    },
    "obsidian-arena-5p": {
        "name_it": "Arena d'Ossidiana",
        "lore_theme": "infernale", "content_family": "arcane",
        "emotional_tone": "grim", "location_hint": "rovine pre-Patto di Ergolat",
        "narrative_hook": "Il pubblico è morto. Continua ad applaudire.",
        "enemy_families": ["gladiators_revenant"], "spoiler_level": "mystery",
    },
    "clockwork-vault-5p": {
        "name_it": "Camera degli Ingranaggi",
        "lore_theme": "fucina", "content_family": "arcane",
        "emotional_tone": "tension", "location_hint": "fortezza meccanica di Aveol",
        "narrative_hook": "Una macchina antica conta a ritroso. Da molto.",
        "enemy_families": ["construct"], "spoiler_level": "public",
    },
    "voidspire-5p": {
        "name_it": "Pinnacolo del Vuoto",
        "lore_theme": "vuoto", "content_family": "void_undead",
        "emotional_tone": "dread", "location_hint": "frattura nel Cielo Spezzato",
        "narrative_hook": "La torre cresce verso l'alto e verso ciò che non esiste ancora.",
        "enemy_families": ["void_kin"], "spoiler_level": "mystery",
    },
    "infernal-pit-5p": {
        "name_it": "Fossa Infernale",
        "lore_theme": "infernale", "content_family": "arcane",
        "emotional_tone": "dread", "location_hint": "lacerazione profonda di Efreto",
        "narrative_hook": "Il fuoco qui ha imparato a mentire.",
        "enemy_families": ["fiends"], "spoiler_level": "mystery",
    },
    "celestial-citadel-5p": {
        "name_it": "Cittadella Celeste",
        "lore_theme": "celeste", "content_family": "divine",
        "emotional_tone": "hope", "location_hint": "rovine sospese sopra Aveol",
        "narrative_hook": "Le luci sopra il muro non sono stelle. Stanno guardando.",
        "enemy_families": ["celestial_guardians"], "spoiler_level": "mystery",
    },
    "world-tree-roots-5p": {
        "name_it": "Radici dell'Albero del Mondo",
        "lore_theme": "soe", "content_family": "nature",
        "emotional_tone": "wonder", "location_hint": "abisso vegetale di Soe",
        "narrative_hook": "Le radici sognano. È l'albero che dorme da troppo.",
        "enemy_families": ["primal_spirits"], "spoiler_level": "mystery",
    },

    # ───── 10 nuovi Void/Undead (R11.3) — patch additivo ─────
    "echoes-of-the-broken-thread": {
        "name_it": "Echi del Filo Spezzato",
        "lore_theme": "vuoto", "content_family": "void_undead",
        "emotional_tone": "melancholy", "location_hint": "sentieri lacerati nel Filo",
        "narrative_hook": "I primi sussurri del Vuoto si imparano da quaggiù.",
        "enemy_families": ["void_echoes"], "spoiler_level": "mystery",
    },
    "shattered-seal-of-ergolat": {
        "name_it": "Il Sigillo Spezzato di Ergolat",
        "lore_theme": "ergolat", "content_family": "void_undead",
        "emotional_tone": "dread", "location_hint": "santuario interdetto",
        "narrative_hook": "Il sigillo non chiudeva il Vuoto. Lo addomesticava.",
        "enemy_families": ["void_acolytes"], "spoiler_level": "mystery",
    },
    "obelisks-of-the-void": {
        "name_it": "Gli Obelischi del Vuoto",
        "lore_theme": "vuoto", "content_family": "void_undead",
        "emotional_tone": "wonder", "location_hint": "altopiano dei Sette Pilastri",
        "narrative_hook": "Sette obelischi. Tre rispondono. Quattro ti rispondono.",
        "enemy_families": ["void_kin"], "spoiler_level": "mystery",
    },
    "plague-warrens-of-irthe": {
        "name_it": "Tane Putride della Piaga dei Mille Volti",
        "lore_theme": "irthe", "content_family": "void_undead",
        "emotional_tone": "grim", "location_hint": "fosse sacre alla Piaga",
        "narrative_hook": "Mille facce, una sola voce. E ride poco.",
        "enemy_families": ["plague_bearers", "undead"], "spoiler_level": "mystery",
    },
    "moonlit-strings-of-alevora": {
        "name_it": "I Fili Lunari di Alevora",
        "lore_theme": "alevora", "content_family": "void_undead",
        "emotional_tone": "wonder", "location_hint": "teatro sospeso sotto la Luna Morta",
        "narrative_hook": "Le marionette tirano i loro fili. I fili tirano te.",
        "enemy_families": ["marionettes_lunar"], "spoiler_level": "mystery",
    },
    "ashkaroth-crypt-court": {
        "name_it": "Corte Cripta di Ashkaroth",
        "lore_theme": "ashkaroth", "content_family": "void_undead",
        "emotional_tone": "dread", "location_hint": "tribunale dei morti silenti",
        "narrative_hook": "Il giudice è cieco. Il verdetto è inciso nelle ossa.",
        "enemy_families": ["ash_kin", "undead"], "spoiler_level": "mystery",
    },
    "eclipthra-veiled-sanctum": {
        "name_it": "Santuario Velato di Eclipthra",
        "lore_theme": "eclipthra", "content_family": "void_undead",
        "emotional_tone": "melancholy", "location_hint": "tempio dietro l'eclissi",
        "narrative_hook": "Il velo si solleva di un capello. È già abbastanza.",
        "enemy_families": ["veil_priests"], "spoiler_level": "mystery",
    },
    "gralca-tide-of-the-deep": {
        "name_it": "La Marea di Gralca",
        "lore_theme": "gralca", "content_family": "void_undead",
        "emotional_tone": "dread", "location_hint": "abissi senza luce di Velur profondo",
        "narrative_hook": "La marea sale verso l'alto. Anche dove non c'è cielo.",
        "enemy_families": ["deep_kin"], "spoiler_level": "mystery",
    },
    "xal-zoraax-throat-of-silence": {
        "name_it": "La Gola di Silenzio di Xal'Zoraax",
        "lore_theme": "xal_zoraax", "content_family": "void_undead",
        "emotional_tone": "dread", "location_hint": "gola del silenzio finale",
        "narrative_hook": "Xal'Zoraax non parla. Non ne ha bisogno.",
        "enemy_families": ["silence_kin"], "spoiler_level": "hidden",
    },
    "tip-of-oblivion-trial": {
        "name_it": "Prova della Punta dell'Oblio",
        "lore_theme": "vuoto", "content_family": "void_undead",
        "emotional_tone": "dread", "location_hint": "Punta dell'Oblio",
        "narrative_hook": "L'ultimo passo conta verso il basso, sempre.",
        "enemy_families": ["oblivion_kin"], "spoiler_level": "hidden",
    },
}


# ─── Lore patch per raid ──────────────────────────────────────────────────────
RAID_LORE_PATCHES: dict[str, dict] = {
    "broken-bastion-siege": {
        "name_it": "Assedio al Bastione Spezzato",
        "lore_theme": "ergolat", "content_family": "baseline",
        "emotional_tone": "tension", "boss_name": "Comandante del Bastione",
        "narrative_hook": "Il bastione cade. Quello che assedia non si vede.",
        "spoiler_level": "public",
    },
    "necropolis-bells": {
        "name_it": "Necropoli delle Mille Campane",
        "lore_theme": "irthe", "content_family": "void_undead",
        "emotional_tone": "grim", "boss_name": "Campanaro Senza Volto",
        "narrative_hook": "Mille campane. Mille tombe. Una si è risvegliata.",
        "spoiler_level": "mystery",
    },
    "dragon-vault": {
        "name_it": "Volta del Drago Addormentato",
        "lore_theme": "draco", "content_family": "arcane",
        "emotional_tone": "wonder", "boss_name": "Drago di Pietra",
        "narrative_hook": "Il drago dorme da mille anni. Forse abbastanza.",
        "spoiler_level": "mystery",
    },
    "rituale-del-vuoto-orde": {
        "name_it": "Il Rituale del Vuoto",
        "lore_theme": "vuoto", "content_family": "void_undead",
        "emotional_tone": "dread", "boss_name": "Officiante delle Orde",
        "narrative_hook": "Le orde marciano in cerchio. Il centro non esiste.",
        "spoiler_level": "mystery",
    },
    "figli-di-irthe-rising": {
        "name_it": "Marcia dei Figli di Irthe",
        "lore_theme": "irthe", "content_family": "void_undead",
        "emotional_tone": "grim", "boss_name": "Primogenito di Irthe",
        "narrative_hook": "Una processione che non finisce, perché non ricorda dov'era diretta.",
        "spoiler_level": "mystery",
    },
    "alevora-marionetta-grande": {
        "name_it": "Il Gran Teatro di Alevora",
        "lore_theme": "alevora", "content_family": "void_undead",
        "emotional_tone": "wonder", "boss_name": "Marionettista Lunare",
        "narrative_hook": "L'ultimo atto inizia quando il pubblico tace.",
        "spoiler_level": "mystery",
    },
    "tempio-del-vuoto-eterno": {
        "name_it": "Tempio del Vuoto Eterno",
        "lore_theme": "vuoto", "content_family": "void_undead",
        "emotional_tone": "dread", "boss_name": "Erede del Tempio",
        "narrative_hook": "Il tempio non venera nulla. Insegna a non avere bisogno di nulla.",
        "spoiler_level": "hidden",
    },
    "valys-mordivac-final-whisper": {
        "name_it": "L'Ultimo Sussurro di Valys Mordivac",
        "lore_theme": "vuoto", "content_family": "void_undead",
        "emotional_tone": "dread", "boss_name": "Valys Mordivac",
        "narrative_hook": "Valys non grida mai. Non ne ha bisogno.",
        "spoiler_level": "hidden",
    },
}


def dungeon_lore_meta(slug: str) -> dict:
    """Return computed lore meta + is_new/is_void_undead for a dungeon slug."""
    patch = DUNGEON_LORE_PATCHES.get(slug, {})
    is_new = slug in NEW_DUNGEON_SLUGS_R113
    is_void = patch.get("content_family") == "void_undead"
    return {
        **patch,
        "is_new": is_new,
        "is_void_undead": is_void,
    }


def raid_lore_meta(slug: str) -> dict:
    patch = RAID_LORE_PATCHES.get(slug, {})
    is_new = slug in NEW_RAID_SLUGS_R113
    is_void = patch.get("content_family") == "void_undead"
    return {
        **patch,
        "is_new": is_new,
        "is_void_undead": is_void,
    }


__all__ = [
    "NEW_DUNGEON_SLUGS_R113", "NEW_RAID_SLUGS_R113",
    "DUNGEON_LORE_PATCHES", "RAID_LORE_PATCHES",
    "dungeon_lore_meta", "raid_lore_meta",
]
