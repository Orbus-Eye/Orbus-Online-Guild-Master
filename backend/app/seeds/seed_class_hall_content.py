"""Idempotent runtime seed for all 27 canonical classes and 135 lore items."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.class_halls.catalog import CLASS_HALLS, ClassHallProfile
from app.class_halls.build_reachability import (
    require_all_class_hall_builds_reachable,
)
from app.class_halls.mechanics import CLASS_MECHANICS, resolve_class_mechanic
from app.stats.runtime.effects.item_catalog import (
    STARTER_ITEM_EFFECT_REGISTRY,
)


_STAT_LABELS_IT = {
    "strength": "Forza",
    "agility": "Agilità",
    "intellect": "Intelletto",
    "endurance": "Tempra",
    "faith": "Fede",
}


_KIT_NAMES: dict[str, tuple[str, str, str, str]] = {
    "alchimista": (
        "Pugnale del Dosaggio Esatto",
        "Grembiule delle Mattonelle Numerate",
        "Fiala della Cura Separata",
        "Rame Condensato del Primo Alambicco",
    ),
    "artificiere": (
        "Martello della Cateratta Aperta",
        "Guanti delle Otto Parti",
        "Monocolo della Scintilla Ordinata",
        "Molla dell'Ingranaggio Salvato",
    ),
    "astrologo": (
        "Bastone dell'Orizzonte Capovolto",
        "Manto della Costellazione Fissa",
        "Lente della Tredicesima Invisibile",
        "Inchiostro di Stella Nera",
    ),
    "bardo": (
        "Lama della Canzone Interrotta",
        "Farsetto del Palco Basso",
        "Plettro della Nota Mancante",
        "Candela della Taverna Insonne",
    ),
    "burattinaio": (
        "Pugnale del Filo Liberatore",
        "Giacca del Sipario Perpetuo",
        "Campanello che Non Deve Suonare",
        "Rocchetto del Primo Burattino",
    ),
    "cacciatore_del_sangue": (
        "Ascia della Traccia Rossa",
        "Corazza delle Tre Notti",
        "Talismano della Caduta Ritrovata",
        "Sale dell'Ossario Bianco",
    ),
    "cacciatore_del_vuoto": (
        "Balestra dell'Ombra Senza Peso",
        "Mantello del Faro Rovesciato",
        "Specchio del Riflesso Vuoto",
        "Olio della Lanterna Muta",
    ),
    "cacciatore_di_mostri": (
        "Coltello del Cinghiale-Fantasma",
        "Giaco del Sentiero Selvaggio",
        "Richiamo del Vecchio Falconiere",
        "Ontano della Faretra Silenziosa",
    ),
    "cartografo": (
        "Pugnale della Stanza Cieca",
        "Cappa della Rotta Ricordata",
        "Squadra della Mappa che Respira",
        "Inchiostro Seppia del Polso",
    ),
    "cavaliere_della_morte": (
        "Spada della Legione Caduta",
        "Corazza del Giro della Cripta",
        "Fibbia dell'Elmo Chiuso",
        "Brandello del Vessillo che Sventola",
    ),
    "cavaliere_di_draghi": (
        "Lancia dello Sguardo Retto",
        "Corazza del Draconcello Vigile",
        "Bracciale del Fuoco Non Comandato",
        "Basalto del Patto delle Fiamme",
    ),
    "cronista": (
        "Pugnale della Riga Esatta",
        "Veste del Giorno che Non Finì",
        "Calamaio di Mnemos Presente",
        "Pergamena dell'Oggi Perpetuo",
    ),
    "druido": (
        "Falce del Silenzio della Foresta",
        "Manto della Radura Consacrata",
        "Talismano della Domanda del Salice",
        "Linfa del Giro di Sole",
    ),
    "fabbro_arcano": (
        "Ascia del Metallo che Ricorda",
        "Grembiule della Fucina Muta",
        "Anello della Prima Incisione",
        "Scoria della Notte Senza Bocca",
    ),
    "giocatore_d_azzardo": (
        "Pugnale della Faccia Invisibile",
        "Giacca del Croupier Perpetuo",
        "Gettone del Lancio Salvatore",
        "Polvere del Tredici Nero",
    ),
    "guerriero": (
        "Scudo del Braciere Completo",
        "Pettorale della Spalla Marchiata",
        "Anello della Tempra Sostenuta",
        "Scaglia dell'Ascia Rituale",
    ),
    "ladro": (
        "Balestra del Campanello Immobile",
        "Cappa della Sala Buia",
        "Marchio della Loggia Invisibile",
        "Filo del Giuramento Sussurrato",
    ),
    "mago": (
        "Tomo dell'Ottava Nicchia",
        "Manto della Pergamena Vergine",
        "Chiave dei Nove Sigilli",
        "Inchiostro del Nome Inciso",
    ),
    "mercante": (
        "Stocco dell'Accordo Accettato",
        "Farsetto della Loggia Equa",
        "Peso del Prezzo Giusto",
        "Oliva d'Inchiostro del Mignolo",
    ),
    "monaco": (
        "Bastone del Passo Senza Terra",
        "Veste dell'Equilibrio di Cinabro",
        "Nodo della Prima Disciplina",
        "Fibra della Corda Intera",
    ),
    "negromante": (
        "Bastone del Nome Specchiato",
        "Veste del Cerchio Richiuso",
        "Sigillo di Silas Nomeperduto",
        "Polvere dell'Ossario Continuo",
    ),
    "paladino": (
        "Martello della Brace Vegliata",
        "Guanti dell'Ambra Custodita",
        "Reliquiario della Prima Luce",
        "Cenere dell'Altare Mai Spento",
    ),
    "parassita": (
        "Falce della Radice Affamata",
        "Manto della Vita Presa in Prestito",
        "Goccia del Collo Segnato",
        "Corteccia di Ciò che si Trova",
    ),
    "pittore": (
        "Lama del Pigmento Costoso",
        "Veste della Tela che si Muove",
        "Tavolozza di Genoveva Rosso",
        "Olio del Colore Vivente",
    ),
    "runista": (
        "Martello della Pietra Centrale",
        "Cotta del Cerchio Imposto",
        "Frammento della Runa Rotta",
        "Polvere dell'Indice Inciso",
    ),
    "sciamano": (
        "Mazza dello Spirito Risposto",
        "Manto dei Tamburi Rotti",
        "Totem della Memoria Ferma",
        "Corda della Piuma Personale",
    ),
    "sognatore": (
        "Bastone del Risveglio Esatto",
        "Veste del Sogno che Continuò",
        "Cuscino del Dettaglio Immutato",
        "Filo della Branda dei Nove",
    ),
}

_SIGNATURE_SPECS: dict[str, tuple[str, str, str]] = {
    "guerriero": ("weapon", "weapon", "sword"),
    "ladro": ("weapon", "weapon", "dagger"),
    "mago": ("weapon", "weapon", "staff"),
    "paladino": ("armor", "chest", "cloth"),
    "cacciatore_di_mostri": ("weapon", "weapon", "bow"),
}


def _slug_token(value: str) -> str:
    return (
        value.lower()
        .replace("'", "")
        .replace("-", "_")
        .replace(" ", "_")
        .replace("à", "a")
        .replace("è", "e")
        .replace("é", "e")
        .replace("ì", "i")
        .replace("ò", "o")
        .replace("ù", "u")
    )


def _bonuses(primary_stat: str, amount: int) -> dict[str, int]:
    bonuses = {
        "strength_bonus": 0,
        "agility_bonus": 0,
        "intellect_bonus": 0,
        "endurance_bonus": 0,
        "faith_bonus": 0,
    }
    bonuses[f"{primary_stat}_bonus"] = amount
    return bonuses


def _item_base(
    profile: ClassHallProfile,
    *,
    slug: str,
    name: str,
    item_type: str,
    slot_type: str | None,
    power_score: int,
    primary_bonus: int,
    binding_policy: str,
) -> dict:
    lore_source = (
        f"R18.6 · {profile.hall_name_it}: {profile.lore_hook_it} "
        f"Custodito da {profile.hall_master_witness_npc}."
    )
    class_tags = [
        profile.canonical_class_slug,
        *profile.legacy_class_slugs,
    ]
    item = {
        "blueprint_id": f"bp.{slug}",
        "slug": slug,
        "name": name,
        "display_name_it": name,
        "display_name_en": name,
        "description": (
            f"Oggetto singolare del cammino {profile.class_name_it}, "
            f"custodito nella {profile.hall_name_it}."
        ),
        "description_it": (
            f"Oggetto singolare del cammino {profile.class_name_it}; "
            f"porta i segni della {profile.hall_name_it}."
        ),
        "description_en": f"Singular lore item of the {profile.class_name_it} path.",
        "flavor_text_it": profile.lore_hook_it,
        "flavor_text_en": profile.lore_hook_it,
        "lore_source": lore_source,
        "lore_tags": [
            profile.starter_lore_key,
            profile.canonical_class_slug,
            profile.hall_id,
            f"wave_{profile.wave.lower()}",
        ],
        "lore_reviewed": True,
        "spoiler_level": "starter",
        "item_type": item_type,
        "slot_type": slot_type,
        "rarity": "Uncommon" if power_score >= 3 else "Common",
        "level_required": 1,
        # Canonical Hall equipment is deliberately part of the level-1
        # item-first journey.  This explicit field prevents the legacy
        # rarity fallback from turning Uncommon starter rewards into Lv3
        # gear that cannot be equipped when the class is first chosen.
        "required_adventurer_level": 1,
        "power_score": power_score,
        **_bonuses(profile.primary_stat, primary_bonus),
        "stackable": item_type in {"material", "consumable"},
        "source": f"class_hall:{profile.hall_id}",
        "craftable": False,
        "item_binding_policy": binding_policy,
        "required_class_optional": (
            profile.canonical_class_slug if binding_policy == "hard" else None
        ),
        "recommended_classes": class_tags,
        "class_tags": class_tags,
        "weapon_tags": ([profile.weapon_tags[0]] if item_type == "weapon" else []),
        "armor_tags": [profile.armor_tags[0]] if item_type == "armor" else [],
        "is_tradeable": True,
        "is_cosmetic": False,
        "affects_combat": item_type in {"weapon", "armor", "accessory"},
        "affects_economy": False,
        "affects_ranking": False,
        "can_be_sold_for_gold": True,
        "can_be_sold_for_real_money": False,
        "is_active": True,
        "is_test": False,
        "bind_state": "unbound",
    }
    return item


def _apply_build_path(
    item: dict,
    *,
    profile: ClassHallProfile,
    build,
) -> None:
    item["build_path_id"] = build.build_id
    item["build_path_name_it"] = build.name_it
    item["build_path_description_it"] = build.description_it
    item["build_path_item_tags"] = list(build.item_tags)
    item["tags"] = list(build.item_tags)
    if item.get("item_type") == "weapon":
        weapon_tags = [
            tag for tag in build.item_tags
            if tag in profile.weapon_tags
        ]
        if weapon_tags:
            item["weapon_tags"] = weapon_tags
    elif item.get("item_type") == "armor":
        armor_tags = [
            tag for tag in build.item_tags
            if tag in profile.armor_tags
        ]
        if armor_tags:
            item["armor_tags"] = armor_tags


def _assign_build_paths(
    profile: ClassHallProfile,
    kit: list[dict],
) -> None:
    mechanic = CLASS_MECHANICS[profile.canonical_class_slug]
    signature = kit[0]
    resolved_signature = resolve_class_mechanic(
        adventurer={
            "canonical_class_slug": profile.canonical_class_slug,
        },
        equipment_items=[signature],
    )
    active_signature = resolved_signature.get("active_build") or {}
    signature_build = next(
        (
            build for build in mechanic.builds
            if build.build_id == active_signature.get("build_id")
            and active_signature.get("resonance_active") is True
        ),
        mechanic.builds[0],
    )
    _apply_build_path(
        signature,
        profile=profile,
        build=signature_build,
    )

    available = list(kit[1:4])
    for build in (
        candidate
        for candidate in mechanic.builds
        if candidate.build_id != signature_build.build_id
    ):
        weapon_match = bool(
            set(build.item_tags).intersection(profile.weapon_tags)
        )
        armor_match = bool(
            set(build.item_tags).intersection(profile.armor_tags)
        )

        def rank(item: dict) -> int:
            item_type = item.get("item_type")
            if item_type == "weapon" and weapon_match:
                return 0
            if item_type == "armor" and armor_match:
                return 0
            if item_type == "accessory":
                return 1
            return 2

        chosen = min(
            enumerate(available),
            key=lambda row: (rank(row[1]), row[0]),
        )[1]
        available.remove(chosen)
        _apply_build_path(
            chosen,
            profile=profile,
            build=build,
        )


def _build_item_kit(profile: ClassHallProfile) -> tuple[dict, ...]:
    extra_names = _KIT_NAMES[profile.canonical_class_slug]
    signature_type, signature_slot, signature_tag = _SIGNATURE_SPECS.get(
        profile.canonical_class_slug,
        ("accessory", "accessory", ""),
    )
    signature = _item_base(
        profile,
        slug=profile.starter_item_slug,
        name=profile.starter_item_name_it,
        item_type=signature_type,
        slot_type=signature_slot,
        power_score=3,
        primary_bonus=1,
        binding_policy="hard",
    )
    if signature_type == "weapon":
        signature["weapon_tags"] = [signature_tag]
    elif signature_type == "armor":
        signature["armor_tags"] = [signature_tag]
    effect_definition = STARTER_ITEM_EFFECT_REGISTRY.get(
        profile.starter_effect_id,
        1,
    )
    if effect_definition is None or not effect_definition.target_key:
        raise RuntimeError(
            f"missing signature effect definition for {profile.starter_effect_id}"
        )
    effect_stat = str(effect_definition.target_key)
    effect_magnitude = int(effect_definition.magnitude)
    effect_stat_it = _STAT_LABELS_IT[effect_stat]
    signature["effect_metadata"] = {
        "schema_version": 1,
        "effect_id": profile.starter_effect_id,
        "effect_version": 1,
        "lore_key": profile.starter_lore_key,
        "effect_summary_it": (
            f"Durante la spedizione: +{effect_magnitude} {effect_stat_it}."
        ),
        "effect_summary_en": (
            f"During the expedition: +{effect_magnitude} "
            f"{effect_stat.capitalize()}."
        ),
        "enabled": True,
    }
    track_route = f"/api/class-halls/{profile.hall_id}/item-track"
    signature["acquisition_track_order"] = 0
    signature["acquisition_hint_it"] = (
        f"Scegli la {profile.hall_name_it} e completa il giuramento iniziale."
    )
    signature["acquisition_sources"] = [
        {
            "source_type": "class_hall_assignment",
            "hall_id": profile.hall_id,
            "milestone": "class_hall_chosen",
            "guaranteed": True,
            "route": track_route,
            "hint_it": signature["acquisition_hint_it"],
        }
    ]
    suffixes = ("arma", "armatura", "reliquia", "memoria")
    specs = (
        ("weapon", "weapon", 4, 2, "hard"),
        ("armor", "chest", 4, 1, "hard"),
        ("accessory", "accessory", 2, 1, "hard"),
        ("material", None, 0, 0, "soft"),
    )
    milestones = (
        (
            "signature_item_equipped",
            "Equipaggia l'item-firma ricevuto dal Maestro della Sala.",
        ),
        (
            "first_expedition_completed",
            "Completa una spedizione con questo avventuriero.",
        ),
        (
            "adventurer_level_2",
            "Raggiungi il livello 2 con questo avventuriero.",
        ),
        (
            "three_expeditions_completed",
            "Completa tre spedizioni con questo avventuriero.",
        ),
    )
    extras: list[dict] = []
    for order, (suffix, name, spec, milestone) in enumerate(
        zip(suffixes, extra_names, specs, milestones),
        start=1,
    ):
        item_type, slot_type, power_score, primary_bonus, policy = spec
        item = _item_base(
            profile,
            slug=f"hall_{profile.canonical_class_slug}_{suffix}",
            name=name,
            item_type=item_type,
            slot_type=slot_type,
            power_score=power_score,
            primary_bonus=primary_bonus,
            binding_policy=policy,
        )
        milestone_code, hint_it = milestone
        item["acquisition_track_order"] = order
        item["acquisition_hint_it"] = hint_it
        item["acquisition_sources"] = [
            {
                "source_type": "class_hall_item_track",
                "hall_id": profile.hall_id,
                "milestone": milestone_code,
                "guaranteed": True,
                "route": track_route,
                "hint_it": hint_it,
            }
        ]
        extras.append(item)
    kit = [signature, *extras]
    _assign_build_paths(profile, kit)
    return tuple(kit)


CANONICAL_CLASS_HALL_ITEM_SEED: tuple[dict, ...] = tuple(
    item
    for profile in sorted(
        CLASS_HALLS.values(),
        key=lambda value: value.canonical_class_slug,
    )
    for item in _build_item_kit(profile)
)


def _class_seed(profile: ClassHallProfile) -> dict:
    base = {
        "base_strength": 5,
        "base_agility": 5,
        "base_intellect": 5,
        "base_endurance": 5,
        "base_faith": 5,
    }
    base[f"base_{profile.primary_stat}"] = 8
    if profile.class_role in {"Tank", "Hybrid"}:
        base["base_endurance"] = max(base["base_endurance"], 7)
    return {
        "slug": profile.canonical_class_slug,
        "name": profile.class_name_it,
        "display_name_it": profile.class_name_it,
        "role": profile.class_role,
        "description": profile.gameplay_style_it,
        "guide_description_it": (
            f"{profile.gameplay_style_it} Sala: {profile.hall_name_it}. "
            f"Maestro: {profile.hall_master_witness_npc}."
        ),
        "primary_stat": profile.primary_stat,
        "allowed_weapon_tags": list(profile.weapon_tags),
        "allowed_armor_tags": list(profile.armor_tags),
        "preferred_item_tags": [
            profile.starter_lore_key,
            profile.canonical_class_slug,
        ],
        "role_tags": [profile.class_role.lower()],
        "class_proficiency": profile.class_proficiency,
        "class_hall_id": profile.hall_id,
        "assignment_ready": True,
        "assignment_readiness_version": profile.readiness_version,
        "is_active": True,
        "is_playable": True,
        "is_base_class": True,
        "is_specialization": False,
        "migration_target_only": False,
        "source_round": "R18.6-runtime",
        **base,
    }


CANONICAL_CLASS_SEED: tuple[dict, ...] = tuple(
    _class_seed(profile)
    for profile in sorted(
        CLASS_HALLS.values(),
        key=lambda value: value.canonical_class_slug,
    )
)


def validate_canonical_class_hall_content() -> None:
    if len(CANONICAL_CLASS_SEED) != 27:
        raise RuntimeError("canonical class seed must contain exactly 27 classes")
    if len(CANONICAL_CLASS_HALL_ITEM_SEED) != 135:
        raise RuntimeError("canonical Hall item seed must contain exactly 135 items")
    for field in ("slug", "blueprint_id", "display_name_it"):
        values = [
            str(item.get(field) or "").casefold()
            for item in CANONICAL_CLASS_HALL_ITEM_SEED
        ]
        if any(not value for value in values) or len(values) != len(set(values)):
            raise RuntimeError(f"canonical Hall item field must be singular: {field}")
    if not all(
        item.get("lore_reviewed") is True
        and item.get("lore_source")
        and item.get("flavor_text_it")
        for item in CANONICAL_CLASS_HALL_ITEM_SEED
    ):
        raise RuntimeError("every canonical Hall item must carry reviewed lore")
    if not all(
        len(item.get("acquisition_sources") or []) == 1
        and item.get("acquisition_hint_it")
        and isinstance(item.get("acquisition_track_order"), int)
        for item in CANONICAL_CLASS_HALL_ITEM_SEED
    ):
        raise RuntimeError(
            "every canonical Hall item needs one visible acquisition source"
        )
    if (
        sum(1 for item in CANONICAL_CLASS_HALL_ITEM_SEED if item.get("effect_metadata"))
        != 27
    ):
        raise RuntimeError("each canonical class must have one signature effect item")
    require_all_class_hall_builds_reachable(
        CANONICAL_CLASS_HALL_ITEM_SEED
    )


async def seed_canonical_class_hall_content(db) -> dict[str, int]:
    """Upsert the 27 classes and 135 singular items without rewriting IDs."""
    validate_canonical_class_hall_content()
    now = datetime.now(timezone.utc).isoformat()
    class_changes = 0
    item_changes = 0
    for source in CANONICAL_CLASS_SEED:
        result = await db.adventurer_classes.update_one(
            {"slug": source["slug"]},
            {
                "$setOnInsert": {
                    "id": str(uuid.uuid4()),
                    "created_at": now,
                },
                "$set": {**source, "updated_at": now},
            },
            upsert=True,
        )
        if result.upserted_id or result.modified_count:
            class_changes += 1
    for source in CANONICAL_CLASS_HALL_ITEM_SEED:
        result = await db.items.update_one(
            {"slug": source["slug"]},
            {
                "$setOnInsert": {
                    "id": str(uuid.uuid4()),
                    "created_at": now,
                },
                "$set": {**source, "updated_at": now},
            },
            upsert=True,
        )
        if result.upserted_id or result.modified_count:
            item_changes += 1
    return {"classes": class_changes, "items": item_changes}


__all__ = [
    "CANONICAL_CLASS_HALL_ITEM_SEED",
    "CANONICAL_CLASS_SEED",
    "seed_canonical_class_hall_content",
    "validate_canonical_class_hall_content",
]
