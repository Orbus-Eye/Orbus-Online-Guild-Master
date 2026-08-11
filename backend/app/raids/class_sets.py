"""FASE 9E — Set raid di classe: 27 classi × 4 raid = 108 set (540 pezzi).

Ogni raid possiede un set per OGNI classe; ogni set ha 5 pezzi sugli
slot canonici (weapon, chest, legs, head, accessory — nessuno slot
inventato) e rafforza il RUOLO FISSO della classe (registry: DPS →
stat primaria, TANK → endurance, HEALER → faith), mai una
specializzazione.

Progressione (curva RAID_CURVE canonica):
  T1 moonfall-vigil        Lv40  Rare       "Veglia Lunare"
  T2 broken-bastion-siege  Lv60  Epic       "Baluardo Infranto"
  T3 necropolis-bells      Lv70  Epic       "Rintocco della Necropoli"
  T4 dragon-vault          Lv80  Legendary  "Cuore della Volta"

Le rarità rispettano le SOURCE_POLICIES dei raid (raid_level40 →
Uncommon/Rare, … raid_level80_victory → Epic/Legendary): i pezzi
entrano nel pool di drop esistente (`raids/loot.py`) senza nuovi
meccanismi, perché portano `catalog_version` T6 e `acquisition_sources`
con la stessa (source_type, source_slug, source_policy_id).

Bonus set (parziale a 3 pezzi, completo a 5): stat REALI del runtime,
sommate all'equipment power tramite `set_bonus_stats` — visibili nel
payload avventuriero, MAI invisibili.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from types import MappingProxyType

from app.classes import CLASS_REGISTRY, role_focus_stats
from app.items.catalog_contract import ITEM_CATALOG_VERSION_T6
from app.shared.content_curve import RAID_CURVE

# Namespace stabile: gli id dei 540 pezzi sono deterministici per slug.
SET_CATALOG_NAMESPACE = uuid.UUID("5d1f7c1e-4b7a-4f7e-9a30-abc9e00108ab")

SET_PARTIAL_PIECES = 3
SET_FULL_PIECES = 5

# (raid_slug, tier, rarità, prefisso set, genitivo set, lore raid)
_RAID_THEMES = (
    ("moonfall-vigil", 1, "Rare", "Veglia Lunare", "della Veglia Lunare",
     "Forgiato sotto la frattura del cielo, dove la luna cadente osserva i giuramenti."),
    ("broken-bastion-siege", 2, "Epic", "Baluardo Infranto", "del Baluardo Infranto",
     "Temprato fra le mura che ricordano ogni difensore e rifiutano di cadere due volte."),
    ("necropolis-bells", 3, "Epic", "Rintocco della Necropoli", "del Rintocco della Necropoli",
     "Consacrato al suono delle campane che chiamano i morti con i nomi dei vivi."),
    ("dragon-vault", 4, "Legendary", "Cuore della Volta", "del Cuore della Volta",
     "Strappato al tesoro del drago addormentato, custode delle promesse non divorate."),
)

_RAID_POLICY = {
    "moonfall-vigil": "raid_level40",
    "broken-bastion-siege": "raid_level60",
    "necropolis-bells": "raid_level70",
    "dragon-vault": "raid_level80_victory",
}

_RAID_NAME_IT = {
    "moonfall-vigil": "Veglia di Lunacaduta",
    "broken-bastion-siege": "Assedio del Bastione Spezzato",
    "necropolis-bells": "Le Campane della Necropoli",
    "dragon-vault": "La Volta del Drago Addormentato",
}

# Budget stat per pezzo e bonus set per tier (progressione reale).
_TIER_PIECE_BUDGET = {1: (6, 2), 2: (10, 3), 3: (12, 4), 4: (16, 5)}
_TIER_SET_BONUS = {1: (3, 6), 2: (5, 10), 3: (6, 12), 4: (8, 16)}
_TIER_POWER_SCORE = {1: 6, 2: 10, 3: 10, 4: 15}

_WEAPON_NOUN = {
    "sword": "Spada", "axe": "Ascia", "hammer": "Martello",
    "shield": "Scudo", "spear": "Lancia", "polearm": "Alabarda",
    "dagger": "Pugnale", "crossbow": "Balestra", "staff": "Bastone",
    "focus": "Focus", "tome": "Tomo", "bow": "Arco", "mace": "Mazza",
    "rapier": "Stocco", "fist": "Cesti da Battaglia",
    "instrument": "Liuto", "vial": "Fiala", "sickle": "Falcetto",
    "totem": "Totem", "relic": "Reliquia",
}
_CHEST_NOUN = {"plate": "Corazza", "mail": "Corazza",
               "leather": "Farsetto", "cloth": "Veste"}
_LEGS_NOUN = {"plate": "Gambali", "mail": "Gambali",
              "leather": "Brache", "cloth": "Calzari"}
_HEAD_NOUN = {"plate": "Elmo", "mail": "Elmo",
              "leather": "Cappuccio", "cloth": "Diadema"}

# (slot, item_type) canonici — subset degli SLOT_SPECS runtime.
_SET_SLOTS = (
    ("weapon", "weapon"),
    ("chest", "armor"),
    ("legs", "legs"),
    ("head", "helmet"),
    ("accessory", "accessory"),
)


def _genitive(name: str) -> str:
    lowered = name.lower()
    if lowered[0] in "aeiou":
        return f"dell'{name}"
    if lowered.startswith(("sc", "sp", "st", "sb", "sg", "sm", "sn", "z")):
        return f"dello {name}"
    return f"del {name}"


def _stable_id(slug: str) -> str:
    return str(uuid.uuid5(SET_CATALOG_NAMESPACE, slug))


@dataclass(frozen=True, slots=True)
class RaidClassSet:
    set_id: str
    raid_slug: str
    raid_name_it: str
    class_slug: str
    class_role: str
    tier: int
    rarity: str
    required_level: int
    name_it: str
    lore_it: str
    focus_stat: str
    secondary_stat: str
    piece_slugs: tuple[str, ...]
    bonus_partial: dict
    bonus_full: dict


def _piece_noun(definition, slot: str) -> str:
    armor = definition.armor_tags[0] if definition.armor_tags else "cloth"
    if slot == "weapon":
        tag = definition.weapon_tags[0] if definition.weapon_tags else "sword"
        return _WEAPON_NOUN.get(tag, "Arma")
    if slot == "chest":
        return _CHEST_NOUN.get(armor, "Corazza")
    if slot == "legs":
        return _LEGS_NOUN.get(armor, "Gambali")
    if slot == "head":
        return _HEAD_NOUN.get(armor, "Elmo")
    return "Sigillo"


def _build_catalog() -> tuple[dict[str, RaidClassSet], tuple[dict, ...]]:
    sets: dict[str, RaidClassSet] = {}
    items: list[dict] = []
    for raid_slug, tier, rarity, prefix, prefix_genitive, raid_lore in _RAID_THEMES:
        level = RAID_CURVE[raid_slug].required_level
        policy = _RAID_POLICY[raid_slug]
        main_budget, secondary_budget = _TIER_PIECE_BUDGET[tier]
        partial_bonus, full_bonus = _TIER_SET_BONUS[tier]
        for class_slug, definition in CLASS_REGISTRY.items():
            focus, secondary = role_focus_stats(class_slug)
            set_id = f"set_{raid_slug}_{class_slug}"
            set_name = f"{prefix} {_genitive(definition.class_name)}"
            lore = (
                f"{raid_lore} {definition.class_identity} "
                f"Chi lo indossa porta il ruolo {definition.class_role} "
                f"della propria classe fino in fondo."
            )
            piece_slugs: list[str] = []
            for slot, item_type in _SET_SLOTS:
                slug = f"{set_id}_{slot}"
                piece_slugs.append(slug)
                noun = _piece_noun(definition, slot)
                name = f"{noun} {prefix_genitive} {_genitive(definition.class_name)}"
                stats = {
                    "strength_bonus": 0,
                    "agility_bonus": 0,
                    "intellect_bonus": 0,
                    "endurance_bonus": 0,
                    "faith_bonus": 0,
                }
                stats[f"{focus}_bonus"] = main_budget
                stats[f"{secondary}_bonus"] = secondary_budget
                weapon_tags = (
                    [definition.weapon_tags[0]]
                    if slot == "weapon" and definition.weapon_tags else []
                )
                armor_tags = (
                    [definition.armor_tags[0]]
                    if slot in ("chest", "legs", "head")
                    and definition.armor_tags else []
                )
                items.append({
                    "id": _stable_id(slug),
                    "blueprint_id": f"bp.{slug}",
                    "slug": slug,
                    "name": name,
                    "display_name_it": name,
                    "display_name_en": name,
                    "description": lore,
                    "description_it": lore,
                    "description_en": (
                        f"{definition.class_name} raid set piece "
                        f"({_RAID_NAME_IT[raid_slug]})."
                    ),
                    "flavor_text_it": raid_lore,
                    "flavor_text_en": raid_lore,
                    "lore_source": f"{_RAID_NAME_IT[raid_slug]} · Set di classe",
                    "lore_tags": ["set_raid", raid_slug, class_slug],
                    "lore_reviewed": True,
                    "spoiler_level": "mystery" if rarity == "Legendary" else "public",
                    "item_type": item_type,
                    "slot_type": slot,
                    "rarity": rarity,
                    "level_required": level,
                    "required_adventurer_level": level,
                    "power_score": _TIER_POWER_SCORE[tier],
                    **stats,
                    "stackable": False,
                    "craftable": False,
                    "item_binding_policy": "hard" if tier == 4 else "soft",
                    "required_class_optional": class_slug,
                    "canonical_class_slug": class_slug,
                    "recommended_classes": [class_slug],
                    "class_tags": [class_slug],
                    "weapon_tags": weapon_tags,
                    "armor_tags": armor_tags,
                    "tags": (weapon_tags or armor_tags
                             or ([definition.weapon_tags[0]]
                                 if definition.weapon_tags else [])),
                    "set_id": set_id,
                    "set_name_it": set_name,
                    "set_tier": tier,
                    "gameplay_effect_it": (
                        f"Pezzo del set {set_name}: +{main_budget} {focus}, "
                        f"+{secondary_budget} {secondary}. "
                        f"{SET_PARTIAL_PIECES} pezzi: +{partial_bonus} {focus}; "
                        f"{SET_FULL_PIECES} pezzi: +{full_bonus} {focus} e "
                        f"+{full_bonus // 2} {secondary}."
                    ),
                    "effect_kind": "equipment_stats",
                    "is_tradeable": tier != 4,
                    "is_cosmetic": False,
                    "affects_combat": True,
                    "affects_economy": False,
                    "affects_ranking": False,
                    "can_be_sold_for_gold": tier != 4,
                    "can_be_sold_for_real_money": False,
                    "is_active": True,
                    "is_test": False,
                    "catalog_scope": "class_set",
                    "catalog_version": ITEM_CATALOG_VERSION_T6,
                    "source": f"raid:{raid_slug}",
                    "source_policy_id": policy,
                    "acquisition_mode": "ordinary_random_drop",
                    "acquisition_hint_it": (
                        f"Bottino di {_RAID_NAME_IT[raid_slug]} "
                        f"(livello {level})."
                    ),
                    "acquisition_sources": [{
                        "source_type": "raid",
                        "source_slug": raid_slug,
                        "source_policy_id": policy,
                        "required_level": level,
                        "guaranteed": False,
                        "hint_it": (
                            f"Affronta {_RAID_NAME_IT[raid_slug]} con la tua "
                            f"compagnia."
                        ),
                    }],
                })
            sets[set_id] = RaidClassSet(
                set_id=set_id,
                raid_slug=raid_slug,
                raid_name_it=_RAID_NAME_IT[raid_slug],
                class_slug=class_slug,
                class_role=definition.class_role,
                tier=tier,
                rarity=rarity,
                required_level=level,
                name_it=set_name,
                lore_it=lore,
                focus_stat=focus,
                secondary_stat=secondary,
                piece_slugs=tuple(piece_slugs),
                bonus_partial={focus: partial_bonus},
                bonus_full={focus: full_bonus, secondary: full_bonus // 2},
            )
    return sets, tuple(items)


_SETS, RAID_CLASS_SET_ITEMS = _build_catalog()
RAID_CLASS_SETS: MappingProxyType[str, RaidClassSet] = MappingProxyType(_SETS)


def set_bonus_stats(equipped_items) -> dict[str, int]:
    """Bonus set attivi (parziale ≥3 pezzi, completo 5) come stat reali.

    `equipped_items` = iterable di doc item equipaggiati (serve `set_id`
    e `slug`/`slot_type` per contare pezzi DISTINTI)."""
    by_set: dict[str, set[str]] = {}
    for item in equipped_items or ():
        set_id = item.get("set_id")
        if not set_id or set_id not in RAID_CLASS_SETS:
            continue
        key = str(item.get("slug") or item.get("slot_type") or item.get("id"))
        by_set.setdefault(set_id, set()).add(key)
    totals: dict[str, int] = {}
    for set_id, pieces in by_set.items():
        definition = RAID_CLASS_SETS[set_id]
        bonus = None
        if len(pieces) >= SET_FULL_PIECES:
            bonus = definition.bonus_full
        elif len(pieces) >= SET_PARTIAL_PIECES:
            bonus = definition.bonus_partial
        if bonus:
            for stat, value in bonus.items():
                totals[stat] = totals.get(stat, 0) + int(value)
    return totals


def set_bonus_power(equipped_items) -> int:
    return sum(set_bonus_stats(equipped_items).values())


def active_set_bonuses(equipped_items) -> list[dict]:
    """Riepilogo player-facing dei set indossati (anche sotto soglia)."""
    by_set: dict[str, set[str]] = {}
    for item in equipped_items or ():
        set_id = item.get("set_id")
        if not set_id or set_id not in RAID_CLASS_SETS:
            continue
        key = str(item.get("slug") or item.get("slot_type") or item.get("id"))
        by_set.setdefault(set_id, set()).add(key)
    out: list[dict] = []
    for set_id, pieces in sorted(by_set.items()):
        definition = RAID_CLASS_SETS[set_id]
        tier_bonus = (
            definition.bonus_full if len(pieces) >= SET_FULL_PIECES
            else definition.bonus_partial
            if len(pieces) >= SET_PARTIAL_PIECES
            else {}
        )
        out.append({
            "set_id": set_id,
            "name_it": definition.name_it,
            "raid_name_it": definition.raid_name_it,
            "pieces_equipped": len(pieces),
            "pieces_total": SET_FULL_PIECES,
            "partial_at": SET_PARTIAL_PIECES,
            "active_bonus": tier_bonus,
            "bonus_partial": definition.bonus_partial,
            "bonus_full": definition.bonus_full,
        })
    return out


def class_sets_public(class_slug: str) -> list[dict]:
    """I 4 set della classe, in ordine di progressione (per la Sala)."""
    slug = (class_slug or "").strip().lower()
    rows = [
        {
            "set_id": d.set_id,
            "name_it": d.name_it,
            "raid_slug": d.raid_slug,
            "raid_name_it": d.raid_name_it,
            "tier": d.tier,
            "rarity": d.rarity,
            "required_level": d.required_level,
            "class_role": d.class_role,
            "focus_stat": d.focus_stat,
            "bonus_partial": d.bonus_partial,
            "bonus_full": d.bonus_full,
            "pieces": SET_FULL_PIECES,
        }
        for d in RAID_CLASS_SETS.values()
        if d.class_slug == slug
    ]
    rows.sort(key=lambda r: r["tier"])
    return rows


async def seed_raid_class_sets(db) -> dict[str, int]:
    """Upsert idempotente dei 540 pezzi set in `items` (per slug)."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    changed = 0
    for source in RAID_CLASS_SET_ITEMS:
        result = await db.items.update_one(
            {"slug": source["slug"]},
            {
                "$setOnInsert": {"created_at": now},
                "$set": {**source, "updated_at": now},
            },
            upsert=True,
        )
        if result.upserted_id or result.modified_count:
            changed += 1
    return {"class_set_items": changed, "total": len(RAID_CLASS_SET_ITEMS)}


__all__ = [
    "RAID_CLASS_SETS",
    "RAID_CLASS_SET_ITEMS",
    "RaidClassSet",
    "SET_FULL_PIECES",
    "SET_PARTIAL_PIECES",
    "active_set_bonuses",
    "class_sets_public",
    "seed_raid_class_sets",
    "set_bonus_power",
    "set_bonus_stats",
]
