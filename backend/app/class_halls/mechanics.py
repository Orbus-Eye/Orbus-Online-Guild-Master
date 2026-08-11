"""FASE 9C — Meccaniche di classe SENZA build.

Il vecchio modello (81 build item-driven: 27 classi × 3 BuildIdentity,
Wave A–E) è stato eliminato. Ogni classe ha UNA meccanica fissa che
deriva dall'identità della classe stessa:

  * bonus base (+1) per il solo fatto di avere una classe;
  * bonus di risonanza (+2) quando l'equipaggiamento è allineato ai tag
    canonici della PROPRIA classe (armor/weapon tags del registry) —
    nessuna scelta del giocatore, nessuna build da attivare;
  * `counter_tags` fissi di classe per il sistema minacce.

I numeri (+1/+2) sono identici al vecchio sistema: il potere totale
delle squadre non cambia, cambia solo COME si ottiene la risonanza
(vestire la propria classe invece di pescare la build giusta).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from app.classes import registry_entry


@dataclass(frozen=True, slots=True)
class ClassMechanic:
    mechanic_id: str
    class_slug: str
    name_it: str
    summary_it: str
    primary_stat: str
    counter_tags: tuple[str, ...]


CLASS_MECHANICS: dict[str, ClassMechanic] = {
    "guerriero": ClassMechanic(
        "class.guerriero.tempra", "guerriero", "Tempra della Linea",
        "Il Guerriero trasforma l'equipaggiamento marziale in pressione "
        "costante sul fronte.",
        "endurance", ("counter_boss", "counter_siege")),
    "ladro": ClassMechanic(
        "class.ladro.slancio", "ladro", "Slancio nell'Ombra",
        "Il Ladro converte l'arma in apertura, elusione e sabotaggio.",
        "agility", ("counter_trap", "counter_stealth")),
    "mago": ClassMechanic(
        "class.mago.risonanza", "mago", "Risonanza dei Sigilli",
        "Il Mago accorda il proprio sapere al tramite arcano equipaggiato.",
        "intellect", ("counter_spell", "counter_magic_barrier")),
    "paladino": ClassMechanic(
        "class.paladino.voto", "paladino", "Voto della Luce Fissa",
        "Il Paladino converte il proprio equipaggiamento in protezione "
        "consacrata.",
        "faith", ("counter_undead", "counter_curse")),
    "cacciatore_di_mostri": ClassMechanic(
        "class.cacciatore_di_mostri.predazione", "cacciatore_di_mostri",
        "Studio della Preda",
        "Il Cacciatore legge la minaccia e la trattiene su di sé.",
        "agility", ("counter_beast", "counter_ambush")),
    "alchimista": ClassMechanic(
        "class.alchimista.dosaggio", "alchimista", "Dosaggio Esatto",
        "L'Alchimista decide se ogni preparato debba curare, corrodere o "
        "mutare.",
        "intellect", ("counter_poison", "counter_disease")),
    "bardo": ClassMechanic(
        "class.bardo.armonia", "bardo", "Armonia Incompiuta",
        "Il Bardo trasforma ritmo, presenza e lama in vantaggio condiviso.",
        "faith", ("counter_spell", "counter_curse")),
    "druido": ClassMechanic(
        "class.druido.ciclo", "druido", "Ciclo del Salice",
        "Il Druido adatta il proprio ciclo a crescita, cura e custodia.",
        "faith", ("counter_beast", "counter_elemental")),
    "monaco": ClassMechanic(
        "class.monaco.disciplina", "monaco", "Disciplina di Cinabro",
        "Il Monaco converte continuità e postura in pressione controllata.",
        "agility", ("counter_boss", "counter_trap")),
    "negromante": ClassMechanic(
        "class.negromante.memoria", "negromante", "Memoria del Cerchio",
        "Il Negromante comanda, ricorda e recide i morti.",
        "intellect", ("counter_undead", "counter_void")),
    "sciamano": ClassMechanic(
        "class.sciamano.risonanza_spiriti", "sciamano",
        "Risonanza degli Spiriti",
        "Lo Sciamano accorda il gruppo a spirito, elemento e memoria.",
        "faith", ("counter_elemental", "counter_disease")),
    "cacciatore_del_vuoto": ClassMechanic(
        "class.cacciatore_del_vuoto.ancoraggio", "cacciatore_del_vuoto",
        "Ancoraggio del Riflesso",
        "Il Cacciatore del Vuoto fissa ciò che non possiede peso né ombra.",
        "intellect", ("counter_void", "counter_magic_barrier")),
    "artificiere": ClassMechanic(
        "class.artificiere.protocollo", "artificiere", "Protocollo Modulare",
        "L'Artificiere riconfigura il proprio dispositivo prima di ogni "
        "impresa.",
        "agility", ("counter_siege", "counter_trap")),
    "cartografo": ClassMechanic(
        "class.cartografo.rotta", "cartografo", "Rotta Memorizzata",
        "Il Cartografo converte ogni strumento in una via sicura "
        "nell'ignoto.",
        "agility", ("counter_ambush", "counter_trap")),
    "cronista": ClassMechanic(
        "class.cronista.margine", "cronista", "Margine Vivente",
        "Il Cronista sceglie quale versione degli eventi rendere "
        "autorevole.",
        "intellect", ("counter_spell", "counter_curse")),
    "fabbro_arcano": ClassMechanic(
        "class.fabbro_arcano.tempra", "fabbro_arcano", "Tempra Runica",
        "Il Fabbro Arcano risveglia la memoria custodita nel metallo.",
        "strength", ("counter_siege", "counter_magic_barrier")),
    "mercante": ClassMechanic(
        "class.mercante.patto", "mercante", "Patto Equo",
        "Il Mercante trasforma preparazione e fiducia in vantaggio "
        "operativo.",
        "agility", ("counter_ambush", "counter_stealth")),
    "runista": ClassMechanic(
        "class.runista.geometria", "runista", "Geometria Imposta",
        "Il Runista decide quale legge debba valere entro il proprio "
        "tracciato.",
        "intellect", ("counter_trap", "counter_magic_barrier")),
    "astrologo": ClassMechanic(
        "class.astrologo.congiunzione", "astrologo",
        "Congiunzione Inevitabile",
        "L'Astrologo sceglie quale segno celeste rendere dominante.",
        "intellect", ("counter_spell", "counter_boss")),
    "burattinaio": ClassMechanic(
        "class.burattinaio.filo", "burattinaio", "Tensione del Filo",
        "Il Burattinaio distribuisce controllo tra mano, filo e marionetta.",
        "agility", ("counter_ambush", "counter_stealth")),
    "giocatore_d_azzardo": ClassMechanic(
        "class.giocatore_d_azzardo.puntata", "giocatore_d_azzardo",
        "Puntata Coperta",
        "Il Giocatore d'Azzardo lega la sorte allo strumento della puntata.",
        "agility", ("counter_trap", "counter_curse")),
    "parassita": ClassMechanic(
        "class.parassita.simbiosi", "parassita", "Simbiosi Affamata",
        "Il Parassita sottrae vigore al nemico e ne fa corazza.",
        "endurance", ("counter_disease", "counter_boss")),
    "pittore": ClassMechanic(
        "class.pittore.pigmento", "pittore", "Pigmento Vivente",
        "Il Pittore rende reale il tratto sostenuto dal proprio strumento.",
        "intellect", ("counter_stealth", "counter_magic_barrier")),
    "sognatore": ClassMechanic(
        "class.sognatore.lucidita", "sognatore", "Lucidità Condivisa",
        "Il Sognatore veglia sul gruppo dall'interno del sogno.",
        "intellect", ("counter_spell", "counter_curse")),
    "cacciatore_del_sangue": ClassMechanic(
        "class.cacciatore_del_sangue.traccia", "cacciatore_del_sangue",
        "Traccia Ematica",
        "Il Cacciatore del Sangue trasforma ogni ferita in una pista.",
        "strength", ("counter_beast", "counter_boss")),
    "cavaliere_della_morte": ClassMechanic(
        "class.cavaliere_della_morte.vessillo", "cavaliere_della_morte",
        "Vessillo Inamovibile",
        "Il Cavaliere della Morte converte memoria funebre in dominio.",
        "endurance", ("counter_undead", "counter_curse")),
    "cavaliere_di_draghi": ClassMechanic(
        "class.cavaliere_di_draghi.patto", "cavaliere_di_draghi",
        "Patto delle Fiamme",
        "Il Cavaliere di Draghi accorda arma, scaglie e fiamma.",
        "strength", ("counter_elemental", "counter_siege")),
}

CLASS_MECHANIC_BASE_BONUS = 1
CLASS_EQUIP_RESONANCE_BONUS = 2
# Alias retro-compatibile: stesso valore, nuovo significato (risonanza
# di CLASSE, non di build).
ITEM_BUILD_RESONANCE_BONUS = CLASS_EQUIP_RESONANCE_BONUS


def _equipment_tags(items: Iterable[Mapping[str, object]]) -> frozenset[str]:
    tags: set[str] = set()
    for item in items:
        for field in ("weapon_tags", "armor_tags", "tags"):
            values = item.get(field)
            if isinstance(values, (list, tuple)):
                tags.update(
                    str(value).strip().lower()
                    for value in values
                    if str(value).strip()
                )
        for field in ("weapon_type", "armor_type", "item_subtype"):
            value = item.get(field)
            if isinstance(value, str) and value.strip():
                tags.add(value.strip().lower())
    return frozenset(tags)


def class_equipment_tags(class_slug: str) -> frozenset[str]:
    """Tag equip canonici della classe (armor + weapon) dal registry."""
    entry = registry_entry(class_slug)
    if entry is None:
        return frozenset()
    return frozenset(
        tag.strip().lower()
        for tag in (*entry.armor_tags, *entry.weapon_tags)
        if tag.strip()
    )


def resolve_class_mechanic(
    *,
    adventurer: Mapping[str, object],
    equipment_items: Iterable[Mapping[str, object]] | None,
) -> dict:
    """Meccanica di classe attiva — SENZA build.

    Risonanza attiva ⇔ almeno un item equipaggiato porta un tag
    armor/weapon canonico della classe. counter_tags sempre di classe.
    """
    class_slug = str(
        adventurer.get("canonical_class_slug")
        or adventurer.get("class_slug")
        or ""
    ).strip().lower()
    mechanic = CLASS_MECHANICS.get(class_slug)
    if mechanic is None:
        # Slug legacy inglese → risolvi via registry e riprova.
        entry = registry_entry(class_slug)
        if entry is not None:
            mechanic = CLASS_MECHANICS.get(entry.class_id)
            class_slug = entry.class_id
    if mechanic is None:
        return {"active": False, "power_bonus": 0, "counter_tags": []}

    equipped_tags = _equipment_tags(equipment_items or ())
    matched = equipped_tags.intersection(class_equipment_tags(class_slug))
    resonance = CLASS_EQUIP_RESONANCE_BONUS if matched else 0
    power_bonus = CLASS_MECHANIC_BASE_BONUS + resonance
    return {
        "active": True,
        "mechanic_id": mechanic.mechanic_id,
        "class_slug": mechanic.class_slug,
        "name_it": mechanic.name_it,
        "summary_it": mechanic.summary_it,
        "primary_stat": mechanic.primary_stat,
        "base_bonus": CLASS_MECHANIC_BASE_BONUS,
        "item_resonance_bonus": resonance,
        "power_bonus": power_bonus,
        "counter_tags": list(mechanic.counter_tags),
        "active_counter_tags": (
            list(mechanic.counter_tags) if matched else []
        ),
        "equipped_tags": sorted(equipped_tags),
        "resonance_active": bool(matched),
        "matched_tags": sorted(matched),
    }


def class_mechanic_public(class_slug: str) -> dict | None:
    """Metadati sicuri per la scelta in Sala e la UI (niente build)."""
    entry = registry_entry(class_slug)
    resolved = entry.class_id if entry else (class_slug or "").strip().lower()
    mechanic = CLASS_MECHANICS.get(resolved)
    if mechanic is None:
        return None
    return {
        "mechanic_id": mechanic.mechanic_id,
        "name_it": mechanic.name_it,
        "summary_it": mechanic.summary_it,
        "primary_stat": mechanic.primary_stat,
        "counter_tags": list(mechanic.counter_tags),
        "resonance_tags": sorted(class_equipment_tags(resolved)),
    }


def resolve_wave_a_class_mechanic(
    *,
    adventurer: Mapping[str, object],
    equipment_items: Iterable[Mapping[str, object]] | None,
) -> dict:
    """Backward-compatible alias retained for existing expedition imports."""
    return resolve_class_mechanic(
        adventurer=adventurer,
        equipment_items=equipment_items,
    )


__all__ = [
    "CLASS_MECHANICS",
    "CLASS_MECHANIC_BASE_BONUS",
    "CLASS_EQUIP_RESONANCE_BONUS",
    "ClassMechanic",
    "ITEM_BUILD_RESONANCE_BONUS",
    "class_equipment_tags",
    "class_mechanic_public",
    "resolve_class_mechanic",
    "resolve_wave_a_class_mechanic",
]
