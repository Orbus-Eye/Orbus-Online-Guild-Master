"""Deterministic T6 final catalog: 27x50 class items + 150 universal.

The module builds and validates blueprints only.  It does not connect to
Mongo and does not populate loot tables; activation is a later T6 gate.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
import uuid

from app.class_halls.catalog import CLASS_HALLS
from app.class_halls.mechanics import CLASS_MECHANICS
from app.dungeons.encounters import DUNGEON_LORE
from app.items.catalog_contract import (
    ITEM_CATALOG_TARGET_TOTAL,
    ITEM_CATALOG_VERSION_T6,
    RARITY_CATALOG_TARGETS,
    ULTRA_RARE_RANDOM_DROP_SLUG,
)
from app.raids.contracts import RAID_CONTRACTS
from app.rewards.company_ring import WORLD_BOSS_SOURCE_SLUG
from app.rewards.source_engine import SOURCE_POLICIES
from app.seeds.seed_class_hall_content import CANONICAL_CLASS_HALL_ITEM_SEED
from app.shared.constants import ADVENTURER_MAX_LEVEL
from app.shared.content_curve import (
    DUNGEON_CURVE,
    DUNGEON_RARITY_SOURCE_POOLS,
    RAID_CURVE,
)


CATALOG_VERSION = ITEM_CATALOG_VERSION_T6
CATALOG_NAMESPACE = uuid.UUID("9ce56626-f9a5-48c7-a7cb-a20effa3454d")

CLASS_RARITY_TARGET = {
    "Common": 18,
    "Uncommon": 13,
    "Rare": 10,
    "Epic": 7,
    "Legendary": 2,
    "Unique": 0,
}
UNIVERSAL_RARITY_TARGET = {
    rarity: RARITY_CATALOG_TARGETS[rarity]
    - CLASS_RARITY_TARGET[rarity] * 27
    for rarity in RARITY_CATALOG_TARGETS
}

SLOT_SPECS = (
    ("weapon", "weapon", "Arma"),
    ("chest", "armor", "Corazza"),
    ("legs", "legs", "Gambali"),
    ("head", "helmet", "Elmo"),
    ("accessory", "accessory", "Accessorio"),
    ("back", "back", "Mantello"),
    ("ring_1", "ring", "Anello"),
    ("ring_2", "ring", "Vera"),
    ("trinket_1", "trinket", "Monile"),
    ("trinket_2", "trinket", "Reliquia"),
)

WEAPON_NAMES_IT = {
    "sword": "Spada",
    "axe": "Ascia",
    "hammer": "Martello",
    "shield": "Scudo",
    "spear": "Lancia",
    "polearm": "Alabarda",
    "dagger": "Pugnale",
    "crossbow": "Balestra",
    "staff": "Bastone",
    "wand": "Verga",
    "focus": "Focus",
    "tome": "Tomo",
    "bow": "Arco",
    "scythe": "Falce",
    "mace": "Mazza",
    "rapier": "Stocco",
}

# Forty-five authored epithets: every added class item receives a distinct
# identity even before the Hall name and source are appended.
CLASS_EPITHETS = (
    "del Giuramento Ritrovato",
    "della Lanterna che Veglia",
    "del Nome Restituito",
    "della Porta senza Cardini",
    "del Primo Rintocco",
    "della Mappa Incompiuta",
    "del Ferro che Ricorda",
    "della Radice Paziente",
    "del Passo non Udito",
    "della Stella Immobile",
    "del Patto delle Zanne",
    "della Pagina Sommersa",
    "del Martello Orfano",
    "della Terza Vedova",
    "dell'Ora Restituita",
    "del Cervo Cavo",
    "della Brace Cortese",
    "del Sigillo Infranto",
    "della Cenere in Piedi",
    "del Fulmine Incatenato",
    "della Campana Taciuta",
    "del Re senza Data",
    "della Moneta che Canta",
    "del Respiro Bianco",
    "della Rotta senza Porto",
    "dell'Ombra Fedele",
    "del Debito delle Ore",
    "della Geometria Corretta",
    "della Speranza Assediata",
    "del Sogno di Scaglie",
    "del Sale Piangente",
    "della Promessa Sepolta",
    "del Sipario Perpetuo",
    "della Sinfonia Spezzata",
    "del Faro Rovesciato",
    "della Forgia Muta",
    "del Tredici Nero",
    "della Costellazione Fissa",
    "del Vessillo Caduto",
    "della Luna Spenta",
    "del Cuore della Volta",
    "delle Catene di Cenere",
    "dell'Ultima Riserva",
    "del Drago che Ricorda",
    "della Compagnia Tornata",
)

UNIVERSAL_EPITHETS = (
    "delle Cinque Strade",
    "dei Nomi sul Ponte",
    "della Notte senza Luna",
    "delle Acque Basse",
    "del Confine Ricucito",
    "delle Sei Memorie",
    "del Viandante senza Ombra",
    "della Torre Capovolta",
    "delle Ceneri Lucenti",
    "del Patto Dimenticato",
    "della Voce Imbottigliata",
    "del Giorno Cancellato",
    "della Radice Madre",
    "dell'Orologiaio Cieco",
    "della Stella che Ritorna",
)

RAID_LORE = {
    "moonfall-vigil": (
        "Veglia della Luna Cadente",
        "La frattura nel cielo lascia passare una presenza che osserva i giuramenti.",
        "Onirade · Tavole dell'Eclissi",
    ),
    "broken-bastion-siege": (
        "Assedio del Bastione Spezzato",
        "Le mura ricordano ogni difensore e rifiutano di cadere una seconda volta.",
        "Krastlov · Cronache delle Mura",
    ),
    "necropolis-bells": (
        "Le Campane della Necropoli",
        "Il Campanaro Senza Volto chiama i morti con i nomi dei vivi.",
        "Irthe · Liturgia dei Rintocchi",
    ),
    "dragon-vault": (
        "La Volta del Drago Addormentato",
        "Il cuore della Volta custodisce le promesse che il drago non ha divorato.",
        "Ariale · Canto del Cuore di Scaglia",
    ),
}

RARITY_BONUS = {
    "Common": 1,
    "Uncommon": 2,
    "Rare": 4,
    "Epic": 7,
    "Legendary": 11,
    "Unique": 14,
}

CLASS_ADDED_RARITIES = (
    ("Common",) * 16
    + ("Uncommon",) * 10
    + ("Rare",) * 10
    + ("Epic",) * 7
    + ("Legendary",) * 2
)

UNIVERSAL_REMAINING_RARITIES = tuple(
    rarity
    for rarity, count in UNIVERSAL_RARITY_TARGET.items()
    for _ in range(0 if rarity == "Unique" else count)
)

UNIQUE_MILESTONES = (
    "ventisette_sale",
    "ottanta_senza_caduti",
    "mille_dungeon",
    "centocinquanta_raid",
    "maestria_forgia",
    "maestria_crafting",
    "territori_completi",
    "cronaca_completa",
    "tutte_le_build",
    "tutti_i_boss",
    "compagnia_quaranta",
    "tutte_le_fonti",
    "collezione_leggendaria",
    "ultimo_segreto",
)


def _stable_id(slug: str) -> str:
    return str(uuid.uuid5(CATALOG_NAMESPACE, slug))


def _source_payload(source_type: str, source_slug: str) -> dict:
    if source_type == "dungeon":
        curve = DUNGEON_CURVE[source_slug]
        name, description, lore_source = DUNGEON_LORE[source_slug]
        return {
            "source_type": "dungeon",
            "source_slug": source_slug,
            "source_policy_id": "ordinary_dungeon",
            "required_level": curve.required_level,
            "name_it": name,
            "description_it": description,
            "lore_source": lore_source,
            "guaranteed": False,
        }
    if source_type == "raid":
        curve = RAID_CURVE[source_slug]
        name, description, lore_source = RAID_LORE[source_slug]
        policy = RAID_CONTRACTS[source_slug]["reward_profile"]["source_policy_id"]
        return {
            "source_type": "raid",
            "source_slug": source_slug,
            "source_policy_id": policy,
            "required_level": curve.required_level,
            "name_it": name,
            "description_it": description,
            "lore_source": lore_source,
            "guaranteed": False,
        }
    if source_type == "unique_milestone":
        return {
            "source_type": "unique_milestone",
            "source_slug": source_slug,
            "source_policy_id": "unique_endgame_milestone",
            "required_level": ADVENTURER_MAX_LEVEL,
            "name_it": "Archivio dei Traguardi Irripetibili",
            "description_it": (
                "Una prova endgame non ripetibile, verificata dal server e "
                "consegnata senza tiro casuale."
            ),
            "lore_source": "Cronaca segreta della Gilda",
            "guaranteed": True,
        }
    raise ValueError(f"unsupported T6 source: {source_type}:{source_slug}")


def _source_for_rarity(rarity: str, index: int) -> dict:
    # Raid catalog slices are authored explicitly: presence percentages never
    # become drop chances, and every raid receives a coherent rarity band.
    if rarity == "Uncommon" and index % 8 == 0:
        return _source_payload("raid", "moonfall-vigil")
    if rarity == "Rare" and index % 6 == 0:
        return _source_payload("raid", "moonfall-vigil")
    if rarity == "Rare" and index % 6 == 1:
        return _source_payload("raid", "broken-bastion-siege")
    if rarity == "Rare" and index % 6 == 2:
        return _source_payload("raid", "necropolis-bells")
    if rarity == "Epic" and index % 4 == 0:
        return _source_payload("raid", "broken-bastion-siege")
    if rarity == "Epic" and index % 4 == 1:
        return _source_payload("raid", "necropolis-bells")
    if rarity == "Epic" and index % 4 == 2:
        return _source_payload("raid", "dragon-vault")
    if rarity in DUNGEON_RARITY_SOURCE_POOLS:
        pool = DUNGEON_RARITY_SOURCE_POOLS[rarity]
        # Epic indices also reserve three positions out of four for raids;
        # collapse the index so the remaining dungeon positions still walk
        # every high-level dungeon instead of repeating one residue.
        source_index = index // 4 if rarity == "Epic" else index
        return _source_payload("dungeon", pool[source_index % len(pool)])
    if rarity == "Legendary":
        return _source_payload("raid", "dragon-vault")
    raise ValueError(f"rarity has no ordinary source: {rarity}")


def _slot_spec(index: int) -> tuple[str, str, str]:
    return SLOT_SPECS[index % len(SLOT_SPECS)]


def _weapon_noun(profile, default_noun: str) -> str:
    if default_noun != "Arma":
        return default_noun
    tag = profile.weapon_tags[0] if profile.weapon_tags else "sword"
    return WEAPON_NAMES_IT.get(tag, "Arma")


def _bonuses(primary: str, rarity: str, index: int, level: int) -> dict:
    stats = {
        "strength_bonus": 0,
        "agility_bonus": 0,
        "intellect_bonus": 0,
        "endurance_bonus": 0,
        "faith_bonus": 0,
    }
    base = RARITY_BONUS[rarity] + min(4, level // 20)
    stats[f"{primary}_bonus"] = base + (index % 2)
    secondary_order = (
        "endurance", "agility", "faith", "intellect", "strength"
    )
    secondary = secondary_order[index % len(secondary_order)]
    if secondary != primary and rarity in {"Rare", "Epic", "Legendary", "Unique"}:
        stats[f"{secondary}_bonus"] = max(1, base // 3)
    return stats


def _acquisition_fields(source: dict, rarity: str) -> dict:
    mode = (
        "legendary_blueprint"
        if rarity == "Legendary"
        else "ordinary_random_drop"
    )
    return {
        "source": f"{source['source_type']}:{source['source_slug']}",
        "source_policy_id": source["source_policy_id"],
        "acquisition_mode": mode,
        "acquisition_hint_it": (
            f"Fonte: {source['name_it']} (livello {source['required_level']})."
        ),
        "acquisition_sources": [
            {
                "source_type": source["source_type"],
                "source_slug": source["source_slug"],
                "source_policy_id": source["source_policy_id"],
                "required_level": source["required_level"],
                "guaranteed": source["guaranteed"],
                "hint_it": f"Affronta {source['name_it']}.",
            }
        ],
    }


def _normalize_hall_item(item: dict, profile) -> dict:
    row = deepcopy(item)
    row["id"] = row.get("id") or _stable_id(row["slug"])
    row["canonical_class_slug"] = profile.canonical_class_slug
    row["catalog_scope"] = "class"
    row["catalog_version"] = CATALOG_VERSION
    if row.get("slot_type") == "armor":
        row["slot_type"] = "chest"
    if row.get("item_type") == "material" and not row.get("slot_type"):
        row["slot_type"] = "material"
    row["source_policy_id"] = (
        (row.get("acquisition_sources") or [{}])[0].get("source_type")
        or "class_hall_item_track"
    )
    row["acquisition_mode"] = "class_hall_milestone"
    row["gameplay_effect_it"] = (
        (row.get("effect_metadata") or {}).get("effect_summary_it")
        or (
            "Rinforza il cammino della classe tramite i propri bonus."
            if row.get("item_type") != "material"
            else "Materiale di memoria usato nella progressione della Sala."
        )
    )
    row["effect_kind"] = (
        "registered_runtime_effect"
        if row.get("effect_metadata")
        else "equipment_stats"
    )
    return row


def _class_added_item(profile, class_index: int, index: int) -> dict:
    rarity = CLASS_ADDED_RARITIES[(index * 17) % len(CLASS_ADDED_RARITIES)]
    slot_type, item_type, default_noun = _slot_spec(index + class_index)
    noun = _weapon_noun(profile, default_noun)
    source = _source_for_rarity(rarity, class_index * 45 + index)
    mechanic = CLASS_MECHANICS[profile.canonical_class_slug]
    build = mechanic.builds[index % len(mechanic.builds)]
    epithet = CLASS_EPITHETS[index]
    name = f"{noun} {epithet} — {profile.hall_name_it}"
    slug = (
        f"t6_{profile.canonical_class_slug}_"
        f"{slot_type}_{index + 1:02d}"
    )
    level = (
        ADVENTURER_MAX_LEVEL
        if rarity == "Legendary"
        else source["required_level"]
    )
    stats = _bonuses(profile.primary_stat, rarity, index, level)
    return {
        "id": _stable_id(slug),
        "blueprint_id": f"bp.{slug}",
        "slug": slug,
        "name": name,
        "display_name_it": name,
        "display_name_en": name,
        "description": (
            f"Oggetto del cammino {profile.class_name_it}, modellato dal "
            f"ricordo di {source['name_it']}."
        ),
        "description_it": (
            f"Il {profile.hall_master_witness_npc} lo affida soltanto a chi "
            f"ha compreso il sentiero {build.name_it}."
        ),
        "description_en": (
            f"Singular {profile.class_name_it} item tied to {source['name_it']}."
        ),
        "flavor_text_it": (
            f"{source['description_it']} {profile.lore_hook_it}"
        ),
        "flavor_text_en": profile.lore_hook_it,
        "lore_source": (
            f"{source['lore_source']} · {profile.hall_name_it}"
        ),
        "lore_tags": [
            profile.starter_lore_key,
            profile.canonical_class_slug,
            source["source_slug"],
            build.build_id,
        ],
        "lore_reviewed": True,
        "spoiler_level": "mystery" if rarity == "Legendary" else "public",
        "item_type": item_type,
        "slot_type": slot_type,
        "rarity": rarity,
        "level_required": level,
        "required_adventurer_level": level,
        "power_score": RARITY_BONUS[rarity] + max(0, level // 20),
        **stats,
        "stackable": False,
        "craftable": False,
        "item_binding_policy": "hard",
        "required_class_optional": profile.canonical_class_slug,
        "canonical_class_slug": profile.canonical_class_slug,
        "recommended_classes": [
            profile.canonical_class_slug,
            *profile.legacy_class_slugs,
        ],
        "class_tags": [
            profile.canonical_class_slug,
            *profile.legacy_class_slugs,
        ],
        "weapon_tags": (
            [profile.weapon_tags[index % len(profile.weapon_tags)]]
            if item_type == "weapon" and profile.weapon_tags else []
        ),
        "armor_tags": (
            [profile.armor_tags[index % len(profile.armor_tags)]]
            if item_type == "armor" and profile.armor_tags else []
        ),
        "build_path_id": build.build_id,
        "build_path_name_it": build.name_it,
        "build_path_description_it": build.description_it,
        "build_path_item_tags": list(build.item_tags),
        "tags": list(build.item_tags),
        "gameplay_effect_it": (
            f"Bonus permanente da equipaggiamento: "
            f"+{stats[f'{profile.primary_stat}_bonus']} "
            f"{profile.primary_stat}; sostiene la build {build.name_it}."
        ),
        "effect_kind": "equipment_stats",
        "is_tradeable": rarity not in {"Legendary"},
        "is_cosmetic": False,
        "affects_combat": True,
        "affects_economy": False,
        "affects_ranking": False,
        "can_be_sold_for_gold": rarity != "Legendary",
        "can_be_sold_for_real_money": False,
        "is_active": True,
        "is_test": False,
        "catalog_scope": "class",
        "catalog_version": CATALOG_VERSION,
        **_acquisition_fields(source, rarity),
    }


def build_class_catalog() -> list[dict]:
    hall_by_class = {
        profile.canonical_class_slug: profile
        for profile in CLASS_HALLS.values()
    }
    rows: list[dict] = []
    for item in CANONICAL_CLASS_HALL_ITEM_SEED:
        class_slug = (
            item.get("required_class_optional")
            or next(
                (
                    value for value in item.get("recommended_classes", [])
                    if value in hall_by_class
                ),
                None,
            )
        )
        if class_slug not in hall_by_class:
            raise RuntimeError(f"Hall item has no canonical class: {item['slug']}")
        rows.append(_normalize_hall_item(item, hall_by_class[class_slug]))
    for class_index, profile in enumerate(
        sorted(CLASS_HALLS.values(), key=lambda value: value.canonical_class_slug)
    ):
        rows.extend(
            _class_added_item(profile, class_index, index)
            for index in range(45)
        )
    return rows


def _universal_item(index: int, rarity: str) -> dict:
    slot_type, item_type, noun = _slot_spec(index)
    source = _source_for_rarity(rarity, 9000 + index)
    epithet = UNIVERSAL_EPITHETS[(index // len(SLOT_SPECS)) % 15]
    name = f"{noun} {epithet}"
    slug = f"t6_universale_{slot_type}_{index + 1:03d}"
    level = (
        ADVENTURER_MAX_LEVEL
        if rarity in {"Legendary", "Unique"}
        else source["required_level"]
    )
    primary = ("strength", "agility", "intellect", "endurance", "faith")[
        index % 5
    ]
    stats = _bonuses(primary, rarity, index, level)
    return {
        "id": _stable_id(slug),
        "blueprint_id": f"bp.{slug}",
        "slug": slug,
        "name": name,
        "display_name_it": name,
        "display_name_en": name,
        "description": f"Equipaggiamento trasversale legato a {source['name_it']}.",
        "description_it": (
            "Un oggetto che non riconosce una sola Sala: conserva il ricordo "
            f"di {source['name_it']} per ogni classe."
        ),
        "description_en": f"Universal item tied to {source['name_it']}.",
        "flavor_text_it": source["description_it"],
        "flavor_text_en": source["description_it"],
        "lore_source": source["lore_source"],
        "lore_tags": ["universale", source["source_slug"], primary],
        "lore_reviewed": True,
        "spoiler_level": "mystery" if rarity in {"Legendary", "Unique"} else "public",
        "item_type": item_type,
        "slot_type": slot_type,
        "rarity": rarity,
        "level_required": level,
        "required_adventurer_level": level,
        "power_score": RARITY_BONUS[rarity] + max(0, level // 20),
        **stats,
        "stackable": False,
        "craftable": False,
        "item_binding_policy": "universal",
        "required_class_optional": None,
        "canonical_class_slug": None,
        "recommended_classes": [],
        "class_tags": [],
        "weapon_tags": [],
        "armor_tags": [],
        "gameplay_effect_it": (
            f"Bonus universale da equipaggiamento centrato su {primary}."
        ),
        "effect_kind": "equipment_stats",
        "is_tradeable": rarity not in {"Legendary", "Unique"},
        "is_cosmetic": False,
        "affects_combat": True,
        "affects_economy": False,
        "affects_ranking": False,
        "can_be_sold_for_gold": rarity not in {"Legendary", "Unique"},
        "can_be_sold_for_real_money": False,
        "is_active": True,
        "is_test": False,
        "catalog_scope": "universal",
        "catalog_version": CATALOG_VERSION,
        **_acquisition_fields(source, rarity),
    }


def _unique_milestone_item(index: int, milestone: str) -> dict:
    slot_type, item_type, noun = _slot_spec(index + 3)
    source = _source_payload("unique_milestone", milestone)
    epithet = UNIVERSAL_EPITHETS[index]
    name = f"{noun} Irripetibile {epithet}"
    slug = f"t6_unico_{milestone}"
    primary = ("strength", "agility", "intellect", "endurance", "faith")[
        index % 5
    ]
    stats = _bonuses(primary, "Unique", index, ADVENTURER_MAX_LEVEL)
    # Start from the level-80 ordinary template only to reuse the normalized
    # equipment fields. Unique relics replace its source and acquisition rule.
    row = _universal_item(index + 120, "Legendary")
    row.update(
        {
            "id": _stable_id(slug),
            "blueprint_id": f"bp.{slug}",
            "slug": slug,
            "name": name,
            "display_name_it": name,
            "display_name_en": name,
            "description": source["description_it"],
            "description_it": source["description_it"],
            "description_en": "A non-random, one-time endgame milestone relic.",
            "flavor_text_it": (
                "La Cronaca lo nomina una volta soltanto; dopo la consegna, "
                "la riga si chiude."
            ),
            "flavor_text_en": "The Chronicle names it only once.",
            "lore_source": source["lore_source"],
            "lore_tags": ["unico", "traguardo", milestone],
            "rarity": "Unique",
            "item_type": item_type,
            "slot_type": slot_type,
            "power_score": RARITY_BONUS["Unique"] + 4,
            **stats,
            "source": f"unique_milestone:{milestone}",
            "source_policy_id": "unique_endgame_milestone",
            "acquisition_mode": "guaranteed_unique_milestone",
            "acquisition_hint_it": (
                "Completa il traguardo endgame irripetibile indicato nella Cronaca."
            ),
            "acquisition_sources": [
                {
                    "source_type": "unique_milestone",
                    "source_slug": milestone,
                    "source_policy_id": "unique_endgame_milestone",
                    "required_level": ADVENTURER_MAX_LEVEL,
                    "guaranteed": True,
                    "hint_it": "Completa il traguardo endgame della Cronaca.",
                }
            ],
            "gameplay_effect_it": (
                f"Reliquia universale unica: potenzia {primary} e non può "
                "essere ottenuta casualmente."
            ),
        }
    )
    return row


def _company_ring_blueprint() -> dict:
    slug = ULTRA_RARE_RANDOM_DROP_SLUG
    name = 'L\'Unico Anello della "Compagnia"'
    stats = {
        "strength_bonus": 8,
        "agility_bonus": 8,
        "intellect_bonus": 8,
        "endurance_bonus": 8,
        "faith_bonus": 8,
    }
    return {
        "id": _stable_id(slug),
        "blueprint_id": f"bp.{slug}",
        "slug": slug,
        "name": name,
        "display_name_it": name,
        "display_name_en": "The Company's One Ring",
        "description": (
            "Nessun orafo ne rivendica la fattura; Alveora custodiva l'unica copia."
        ),
        "description_it": (
            "Nessun orafo ne rivendica la fattura. Sul bordo interno appaiono "
            "i nomi della sola compagnia che riesce a sottrarlo ad Alveora."
        ),
        "description_en": "The sole ring hidden among Alveora's impossible treasures.",
        "flavor_text_it": (
            "Un cerchio, una Compagnia, una sola possibilità tra un milione."
        ),
        "flavor_text_en": "One circle, one Company, one chance in a million.",
        "lore_source": "Tesoro impossibile di Alveora",
        "lore_tags": ["unico", "compagnia", "alveora", "luna_morta"],
        "lore_reviewed": True,
        "spoiler_level": "mystery",
        "item_type": "ring",
        "slot_type": "ring_1",
        "rarity": "Unique",
        "level_required": ADVENTURER_MAX_LEVEL,
        "required_adventurer_level": ADVENTURER_MAX_LEVEL,
        "power_score": 20,
        **stats,
        "stackable": False,
        "craftable": False,
        "item_binding_policy": "universal",
        "required_class_optional": None,
        "canonical_class_slug": None,
        "recommended_classes": [],
        "class_tags": [],
        "weapon_tags": [],
        "armor_tags": [],
        "source": f"world_boss:{WORLD_BOSS_SOURCE_SLUG}",
        "source_policy_id": "company_ring_ultra_rare",
        "acquisition_mode": "ultra_rare_random_drop",
        "acquisition_hint_it": (
            "Contribuisci alla sconfitta di Alveora. La probabilità resta segreta."
        ),
        "acquisition_sources": [
            {
                "source_type": "world_boss",
                "source_slug": WORLD_BOSS_SOURCE_SLUG,
                "source_policy_id": "company_ring_ultra_rare",
                "required_level": ADVENTURER_MAX_LEVEL,
                "guaranteed": False,
                "hint_it": "Sconfiggi Alveora dopo aver contribuito allo scontro.",
            }
        ],
        "gameplay_effect_it": (
            "Bonus +8 a tutte le statistiche primarie; esiste una sola copia globale."
        ),
        "effect_kind": "equipment_stats",
        "is_tradeable": False,
        "is_cosmetic": False,
        "affects_combat": True,
        "affects_economy": False,
        "affects_ranking": False,
        "can_be_sold_for_gold": False,
        "can_be_sold_for_real_money": False,
        "is_active": True,
        "is_test": False,
        "is_global_unique": True,
        "catalog_scope": "universal",
        "catalog_version": CATALOG_VERSION,
    }


def build_universal_catalog() -> list[dict]:
    # Multiplication by 37 permutes the 135 positions (37 is coprime to 135),
    # spreading rarities across slots without changing exact totals.
    count = len(UNIVERSAL_REMAINING_RARITIES)
    rows = [
        _universal_item(
            index,
            UNIVERSAL_REMAINING_RARITIES[(index * 37) % count],
        )
        for index in range(count)
    ]
    rows.extend(
        _unique_milestone_item(index, milestone)
        for index, milestone in enumerate(UNIQUE_MILESTONES)
    )
    rows.append(_company_ring_blueprint())
    return rows


def build_final_catalog() -> tuple[dict, ...]:
    return tuple(build_class_catalog() + build_universal_catalog())


def _duplicates(rows: list[dict], field: str) -> list[str]:
    values = Counter(
        str(row.get(field) or "").strip().casefold()
        for row in rows
    )
    return sorted(value for value, count in values.items() if value and count > 1)


def validate_final_catalog(rows=None) -> dict:
    items = list(rows if rows is not None else build_final_catalog())
    rarity_counts = Counter(item.get("rarity") for item in items)
    class_counts = Counter(
        item.get("canonical_class_slug")
        for item in items
        if item.get("catalog_scope") == "class"
    )
    universal_count = sum(
        item.get("catalog_scope") == "universal" for item in items
    )
    errors: list[str] = []
    if len(items) != ITEM_CATALOG_TARGET_TOTAL:
        errors.append(f"catalog.total:{len(items)}")
    if dict(rarity_counts) != RARITY_CATALOG_TARGETS:
        errors.append(f"catalog.rarities:{dict(rarity_counts)}")
    expected_classes = {
        profile.canonical_class_slug for profile in CLASS_HALLS.values()
    }
    if set(class_counts) != expected_classes:
        errors.append("catalog.class_set")
    for class_slug in sorted(expected_classes):
        if class_counts[class_slug] != 50:
            errors.append(f"catalog.class_count:{class_slug}:{class_counts[class_slug]}")
    if universal_count != 150:
        errors.append(f"catalog.universal_count:{universal_count}")
    for field in ("id", "blueprint_id", "slug", "display_name_it"):
        duplicate = _duplicates(items, field)
        if duplicate:
            errors.append(f"catalog.duplicate:{field}:{len(duplicate)}")
    required_text = (
        "slug", "display_name_it", "description_it", "flavor_text_it",
        "lore_source", "gameplay_effect_it", "source", "source_policy_id",
        "item_binding_policy", "acquisition_mode", "slot_type",
    )
    valid_slots = {
        slot for slot, _, _ in SLOT_SPECS
    } | {"accessory", "weapon", "material"}
    slot_types = {item_type for _, item_type, _ in SLOT_SPECS}
    for item in items:
        slug = item.get("slug", "?")
        for field in required_text:
            if not str(item.get(field) or "").strip():
                errors.append(f"item.required:{slug}:{field}")
        if item.get("lore_reviewed") is not True:
            errors.append(f"item.lore_unreviewed:{slug}")
        if not item.get("acquisition_sources"):
            errors.append(f"item.source_missing:{slug}")
        if item.get("source_policy_id") not in SOURCE_POLICIES:
            errors.append(f"item.source_policy_unknown:{slug}")
        if item.get("item_type") not in slot_types | {"material"}:
            errors.append(f"item.type_invalid:{slug}")
        if (
            item.get("slot_type") not in valid_slots
        ):
            errors.append(f"item.slot_invalid:{slug}")
        if int(item.get("required_adventurer_level", 0) or 0) < 1:
            errors.append(f"item.level_missing:{slug}")
        if item.get("rarity") in {"Legendary", "Unique"} and int(
            item.get("required_adventurer_level", 0) or 0
        ) != ADVENTURER_MAX_LEVEL:
            errors.append(f"item.endgame_level:{slug}")
    random_ultra = [
        item["slug"] for item in items
        if item.get("acquisition_mode") == "ultra_rare_random_drop"
    ]
    if random_ultra != [ULTRA_RARE_RANDOM_DROP_SLUG]:
        errors.append(f"catalog.ultra_rare_random:{random_ultra}")
    ring = next(
        (item for item in items if item["slug"] == ULTRA_RARE_RANDOM_DROP_SLUG),
        None,
    )
    if (
        not ring
        or ring.get("source")
        != f"world_boss:{WORLD_BOSS_SOURCE_SLUG}"
        or ring.get("source_policy_id") != "company_ring_ultra_rare"
    ):
        errors.append("catalog.company_ring_source")
    unique_non_ring = [
        item for item in items
        if item.get("rarity") == "Unique"
        and item.get("slug") != ULTRA_RARE_RANDOM_DROP_SLUG
    ]
    if any(
        item.get("acquisition_mode") != "guaranteed_unique_milestone"
        for item in unique_non_ring
    ):
        errors.append("catalog.unique_non_random")
    canonical = json.dumps(
        items,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "catalog_version": CATALOG_VERSION,
        "valid": not errors,
        "errors": errors,
        "total": len(items),
        "rarity_counts": dict(rarity_counts),
        "class_counts": dict(sorted(class_counts.items())),
        "universal_count": universal_count,
        "unique_random_drop_slugs": random_ultra,
        "sha256": sha256(canonical).hexdigest(),
    }


FINAL_ITEM_CATALOG = build_final_catalog()


__all__ = [
    "CATALOG_VERSION",
    "CLASS_RARITY_TARGET",
    "FINAL_ITEM_CATALOG",
    "UNIVERSAL_RARITY_TARGET",
    "build_final_catalog",
    "validate_final_catalog",
]
