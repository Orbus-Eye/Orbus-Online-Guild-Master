"""Canonical dungeon encounter contract for the level-80 journey.

Historical seeds remain the source of names, lore and economy values. This
module owns gameplay classification: party size, difficulty, duration,
level/power curve and counterable threats.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.shared.content_curve import DUNGEON_CURVE


@dataclass(frozen=True, slots=True)
class DungeonEncounter:
    slug: str
    difficulty: int
    team_size: int
    duration_seconds: int
    encounter_type: str
    threat_tags: tuple[str, ...]


COUNTER_THREAT_MAP: dict[str, tuple[str, ...]] = {
    "counter_boss": ("boss",),
    "counter_minion": ("minion",),
    "counter_spell": ("spell", "magic_barrier"),
    "counter_trap": ("trap",),
    "counter_curse": ("curse",),
    "counter_ambush": ("ambush", "stealth"),
    "counter_elite": ("elite",),
    "counter_undead": ("undead", "curse"),
    "counter_beast": ("beast",),
    "counter_elemental": ("elemental",),
    "counter_void": ("void", "magic_barrier"),
    "counter_poison": ("poison", "disease"),
    "counter_disease": ("disease",),
    "counter_siege": ("siege",),
    "counter_stealth": ("stealth",),
    "counter_magic_barrier": ("magic_barrier",),
}


def _encounter(
    slug: str,
    difficulty: int,
    team_size: int,
    duration_seconds: int,
    encounter_type: str,
    *threat_tags: str,
) -> DungeonEncounter:
    return DungeonEncounter(
        slug,
        difficulty,
        team_size,
        duration_seconds,
        encounter_type,
        tuple(threat_tags),
    )


DUNGEON_ENCOUNTERS: dict[str, DungeonEncounter] = {
    "training-yard": _encounter(
        "training-yard", 1, 3, 30, "tutorial", "minion",
    ),
    "sewer-nest": _encounter(
        "sewer-nest", 1, 3, 45, "exploration", "beast", "disease",
    ),
    "goblin-warrens": _encounter(
        "goblin-warrens", 1, 3, 60, "assault", "ambush", "trap", "minion",
    ),
    "bandit-hideout": _encounter(
        "bandit-hideout", 1, 3, 75, "assault", "ambush", "stealth",
    ),
    "druid-grove": _encounter(
        "druid-grove", 2, 3, 90, "purification", "beast", "poison", "spell",
    ),
    "shadow-crypts": _encounter(
        "shadow-crypts", 2, 3, 120, "purification",
        "undead", "curse", "minion",
    ),
    "cursed-mines": _encounter(
        "cursed-mines", 2, 3, 120, "exploration", "undead", "curse", "trap",
    ),
    "sunken-library": _encounter(
        "sunken-library", 2, 3, 150, "ritual",
        "spell", "magic_barrier", "trap",
    ),
    "lich-sanctum": _encounter(
        "lich-sanctum", 3, 3, 180, "boss",
        "undead", "curse", "boss", "magic_barrier",
    ),
    "dragons-hoard": _encounter(
        "dragons-hoard", 3, 3, 300, "boss", "elemental", "boss", "spell",
    ),
    "storm-spire": _encounter(
        "storm-spire", 3, 3, 240, "ritual",
        "elemental", "spell", "magic_barrier",
    ),
    "wolf-den-5p": _encounter(
        "wolf-den-5p", 1, 5, 60, "hunt", "beast", "ambush",
    ),
    "frost-cave-5p": _encounter(
        "frost-cave-5p", 1, 5, 75, "exploration", "elemental", "ambush",
    ),
    "salt-marsh-5p": _encounter(
        "salt-marsh-5p", 1, 5, 90, "survival", "disease", "poison", "beast",
    ),
    "iron-foundry-5p": _encounter(
        "iron-foundry-5p", 2, 5, 120, "sabotage", "siege", "elite", "trap",
    ),
    "silent-monastery-5p": _encounter(
        "silent-monastery-5p", 2, 5, 150, "purification",
        "undead", "curse", "spell",
    ),
    "pirate-fleet-5p": _encounter(
        "pirate-fleet-5p", 2, 5, 180, "assault",
        "ambush", "stealth", "minion",
    ),
    "obsidian-arena-5p": _encounter(
        "obsidian-arena-5p", 3, 5, 240, "boss", "boss", "elite", "ambush",
    ),
    "clockwork-vault-5p": _encounter(
        "clockwork-vault-5p", 3, 5, 300, "sabotage",
        "trap", "magic_barrier", "elite",
    ),
    "voidspire-5p": _encounter(
        "voidspire-5p", 3, 7, 360, "ritual",
        "void", "magic_barrier", "spell",
    ),
    "infernal-pit-5p": _encounter(
        "infernal-pit-5p", 4, 7, 420, "boss", "elemental", "curse", "boss",
    ),
    "celestial-citadel-5p": _encounter(
        "celestial-citadel-5p", 4, 7, 540, "siege",
        "siege", "spell", "magic_barrier", "boss",
    ),
    "world-tree-roots-5p": _encounter(
        "world-tree-roots-5p", 4, 7, 720, "boss",
        "beast", "elemental", "boss", "disease",
    ),
}

# Player-facing identity is kept here beside the mechanical contract so seed
# age can no longer make a dungeon fall back to a generic English placeholder.
DUNGEON_LORE: dict[str, tuple[str, str, str]] = {
    "training-yard": ("Il Cortile delle Prime Promesse", "Le reclute giurano di tornare insieme prima di affrontare i fantocci animati del vecchio maestro.", "Cronache della Gilda · Libro dei Fondatori"),
    "sewer-nest": ("Il Nido sotto Orbus", "Sotto le cisterne cittadine una covata malata divora le targhe con i nomi dei dispersi.", "Orbus · Registro delle Acque Basse"),
    "goblin-warrens": ("Le Tane della Lanterna Rubata", "I goblin hanno sottratto una lanterna che indicava la via ai pellegrini durante le notti senza luna.", "Onirade · Sentieri della Luna Spenta"),
    "bandit-hideout": ("Il Rifugio dei Senza Sigillo", "Disertori senza casata custodiscono lettere capaci di incrinare un antico trattato.", "Krastlov · Archivio dei Giuramenti"),
    "druid-grove": ("Il Bosco del Cervo Cavo", "Un guardiano senza cuore diffonde una linfa nera nelle radici consacrate.", "Alveora · Canti della Linfa"),
    "shadow-crypts": ("Le Cripte delle Ombre Fedeli", "Le ombre dei sepolti continuano a proteggere un sovrano il cui nome è stato cancellato.", "Irthe · Tavole Funerarie"),
    "cursed-mines": ("Le Miniere del Giuramento Sepolto", "Ogni colpo di piccone ripete la promessa infranta dell'ultima compagnia di minatori.", "Krastlov · Memorie del Ferro"),
    "sunken-library": ("La Biblioteca delle Pagine Sommerse", "Libri sigillati respirano sotto l'acqua e riscrivono i ricordi di chi li apre.", "Onirade · Catalogo delle Opere Perdute"),
    "lich-sanctum": ("Il Santuario del Re Senza Data", "Un lich ha cancellato il giorno della propria morte per impedire al tempo di reclamarlo.", "Irthe · Calendario dei Morti"),
    "dragons-hoard": ("Il Tesoro che Ricorda", "Le monete di un drago conservano l'ultima voce di ogni proprietario e ora cantano tutte insieme.", "Ariale · Canto delle Scaglie"),
    "storm-spire": ("La Guglia del Fulmine Immobile", "Un fulmine incatenato alimenta una torre eretta per parlare con una divinità che non rispose.", "Ariale · Mappe del Cielo"),
    "wolf-den-5p": ("La Tana dei Lupi del Patto", "I lupi custodiscono il luogo in cui uomini e bestie firmarono il primo patto di caccia.", "Alveora · Patto delle Zanne"),
    "frost-cave-5p": ("La Grotta del Respiro Bianco", "Nel ghiaccio dorme il respiro di un gigante, spezzato in elementali che temono il disgelo.", "Ariale · Inverno delle Origini"),
    "salt-marsh-5p": ("Le Paludi del Sale Piangente", "Il sale affiora dove un villaggio venne sommerso senza che nessuna campana desse l'allarme.", "Irthe · Libro delle Città Annegate"),
    "iron-foundry-5p": ("La Fonderia del Martello Orfano", "Un martello senza padrone continua a forgiare guardiani per una guerra terminata secoli fa.", "Krastlov · Officine del Primo Ferro"),
    "silent-monastery-5p": ("Il Monastero dell'Ultima Parola", "I monaci morirono trattenendo una parola che ora tenta di pronunciare se stessa.", "Onirade · Liturgie del Silenzio"),
    "pirate-fleet-5p": ("La Flotta delle Tre Vedove", "Tre relitti legati fra loro navigano seguendo la voce imbottigliata di una strega del mare.", "Ariale · Rotte Senza Porto"),
    "obsidian-arena-5p": ("L'Arena delle Ceneri in Piedi", "Un campione morto combatte finché qualcuno non ricorderà il suo vero nome.", "Irthe · Elenco dei Vincitori Cancellati"),
    "clockwork-vault-5p": ("La Volta delle Ore Rubate", "Automi-giudici proteggono le ore sottratte alla vita dei debitori di un antico regno.", "Krastlov · Contabilità dell'Orologiaio"),
    "voidspire-5p": ("La Guglia dell'Altrove", "La torre fora il confine del mondo e usa i ricordi dei visitatori per correggere la propria geometria.", "Onirade · Carte del Vuoto"),
    "infernal-pit-5p": ("Il Pozzo delle Cortesie Infernali", "I demoni offrono patti sempre più gentili mentre la discesa rende impossibile rifiutarli.", "Ariale · Codice delle Fiamme"),
    "celestial-citadel-5p": ("La Cittadella degli Aureolati Caduti", "I custodi ricordano la santità perduta e assediano chi porta ancora una speranza.", "Onirade · Scisma delle Stelle"),
    "world-tree-roots-5p": ("Le Radici che Sognano Draghi", "Sotto l'albero del mondo, sogni di scaglie e denti stanno imparando a diventare reali.", "Alveora · Anelli della Radice Madre"),
}


_RARITIES_BY_DIFFICULTY = {
    1: ("Common", "Uncommon"),
    2: ("Common", "Uncommon", "Rare"),
    3: ("Uncommon", "Rare", "Epic"),
    4: ("Common", "Uncommon", "Rare", "Epic"),
}

_CATEGORY_BY_TYPE = {
    "tutorial": ("equipment",),
    "exploration": ("equipment", "material", "lore_fragment"),
    "assault": ("weapon", "armor", "material"),
    "purification": ("relic", "armor", "lore_fragment"),
    "ritual": ("focus", "tome", "lore_fragment"),
    "boss": ("equipment", "boss_trophy", "lore_fragment"),
    "hunt": ("weapon", "material", "trophy"),
    "survival": ("armor", "consumable", "material"),
    "sabotage": ("weapon", "focus", "crafting_material"),
    "siege": ("equipment", "crafting_material", "boss_trophy"),
}


def encounter_phases(encounter: DungeonEncounter) -> list[dict]:
    """Return three deterministic, readable phases for an encounter."""
    threats = list(encounter.threat_tags)
    entry_threats = threats[:1]
    climax_threats = threats[-2:] if len(threats) > 1 else threats
    objective_threats = [
        threat
        for threat in threats
        if threat not in entry_threats and threat not in climax_threats
    ] or threats[1:2] or threats
    climax_label = (
        "Boss o culmine"
        if "boss" in threats or encounter.encounter_type == "boss"
        else "Obiettivo decisivo"
    )
    return [
        {
            "phase_id": "ingresso",
            "name_it": "Ingresso e ricognizione",
            "threat_tags": entry_threats,
            "modifier": "preparazione",
            "success_condition_it": (
                "Entrare senza perdere il controllo della formazione."
            ),
        },
        {
            "phase_id": "obiettivo",
            "name_it": "Cuore dell'incarico",
            "threat_tags": objective_threats,
            "modifier": encounter.encounter_type,
            "success_condition_it": (
                "Completare l'obiettivo contrastando almeno una minaccia."
            ),
        },
        {
            "phase_id": "culmine",
            "name_it": climax_label,
            "threat_tags": climax_threats,
            "modifier": (
                "pressione_crescente"
                if encounter.difficulty >= 3
                else "chiusura"
            ),
            "success_condition_it": (
                "Superare il culmine e riportare indietro la squadra."
            ),
        },
    ]


def dungeon_reward_profile(encounter: DungeonEncounter) -> dict:
    """Describe reward categories without selecting or creating item rows."""
    return {
        "profile_id": (
            f"dungeon.{encounter.encounter_type}.d{encounter.difficulty}"
        ),
        "source_type": "ordinary_dungeon",
        "source_policy_id": "ordinary_dungeon",
        "categories": list(
            _CATEGORY_BY_TYPE.get(
                encounter.encounter_type,
                ("equipment", "material"),
            )
        ),
        "allowed_rarities": list(
            _RARITIES_BY_DIFFICULTY[encounter.difficulty]
        ),
        "max_rarity": (
            _RARITIES_BY_DIFFICULTY[encounter.difficulty][-1]
        ),
        "legendary_allowed": False,
        "unique_allowed": False,
        "class_relevance_required": True,
        "lore_link_required": encounter.difficulty >= 2,
        "pool_status": "blueprint_only",
    }


def apply_dungeon_encounter(dungeon: dict | None) -> dict | None:
    """Overlay authoritative gameplay fields without mutating the input."""
    if dungeon is None:
        return None
    slug = str(dungeon.get("slug") or "")
    encounter = DUNGEON_ENCOUNTERS.get(slug)
    curve = DUNGEON_CURVE.get(slug)
    if encounter is None or curve is None:
        return dict(dungeon)
    lore = DUNGEON_LORE.get(slug)
    return {
        **dungeon,
        **({
            "name_it": lore[0],
            "description_it": lore[1],
            "lore_source": lore[2],
            "lore_reviewed": True,
        } if lore else {}),
        "difficulty": encounter.difficulty,
        "required_team_size": encounter.team_size,
        "base_duration_seconds": encounter.duration_seconds,
        "encounter_type": encounter.encounter_type,
        "encounter_phases": encounter_phases(encounter),
        "reward_profile": dungeon_reward_profile(encounter),
        "threat_tags": list(encounter.threat_tags),
        "threat_count": len(encounter.threat_tags),
        "required_level": curve.required_level,
        "min_adventurer_level": curve.required_level,
        "recommended_power": curve.recommended_power,
        "base_xp_reward": curve.xp_reward,
        "bucket": curve.bucket,
        "curve_version": "level80-t2-v1",
    }


async def reconcile_dungeon_encounters(db) -> dict[str, int]:
    """Persist the canonical contract on existing dungeon documents."""
    now = datetime.now(timezone.utc).isoformat()
    matched = 0
    modified = 0
    canonical_keys = (
        "difficulty",
        "required_team_size",
        "base_duration_seconds",
        "encounter_type",
        "encounter_phases",
        "reward_profile",
        "threat_tags",
        "threat_count",
        "required_level",
        "min_adventurer_level",
        "recommended_power",
        "base_xp_reward",
        "bucket",
        "curve_version",
        "name_it",
        "description_it",
        "lore_source",
        "lore_reviewed",
    )
    for slug in DUNGEON_ENCOUNTERS:
        existing = await db.dungeons.find_one({"slug": slug}, {"_id": 0})
        if existing is None:
            continue
        matched += 1
        canonical = apply_dungeon_encounter(existing)
        fields = {key: canonical[key] for key in canonical_keys}
        if all(existing.get(key) == value for key, value in fields.items()):
            continue
        fields["updated_at"] = now
        result = await db.dungeons.update_one({"slug": slug}, {"$set": fields})
        modified += int(result.modified_count)
    return {"matched": matched, "modified": modified}


__all__ = [
    "COUNTER_THREAT_MAP",
    "DUNGEON_ENCOUNTERS",
    "DungeonEncounter",
    "apply_dungeon_encounter",
    "dungeon_reward_profile",
    "encounter_phases",
    "reconcile_dungeon_encounters",
]
