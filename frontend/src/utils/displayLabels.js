// ROUND 15 — Phase 4 — Display labels in Italiano per rarity, item type,
// armor/weapon tags. NON modifica gli slug interni del DB: serve solo a
// chi renderizza testo player-facing.
//
// Importa la funzione per la singola classe di label necessaria:
//
//     import { rarityLabel, itemTypeLabel, tagLabel } from "@/utils/displayLabels";
//     <span>{rarityLabel(item.rarity)}</span>
//
// Tutte le funzioni sono tolleranti al case (lowercase normalization) e
// fanno fallback alla stringa originale se la chiave non è in mappa
// (così i nuovi slug non rompono l'UI silenziosamente).

const RARITY_IT = {
    common: "Comune",
    uncommon: "Non comune",
    rare: "Raro",
    epic: "Epico",
    legendary: "Leggendario",
    relic: "Reliquia",
};

const ITEM_TYPE_IT = {
    weapon: "Arma",
    armor: "Armatura",
    accessory: "Accessorio",
    consumable: "Consumabile",
    material: "Materiale",
};

const TAG_IT = {
    // armor weight
    heavy: "Pesante",
    medium: "Media",
    light: "Leggera",
    robe: "Vesti",
    cloth: "Stoffa",
    leather: "Cuoio",
    plate: "Piastre",
    mail: "Maglia",
    scale: "Scaglie",
    natural: "Naturale",
    shield: "Scudo",
    // weapon handling
    one_handed: "A 1 mano",
    two_handed: "A 2 mani",
    finesse: "Finezza",
    ranged: "A distanza",
    // weapon families
    sword: "Spada",
    dagger: "Daga",
    bow: "Arco",
    staff: "Bastone",
    wand: "Bacchetta",
    grimoire: "Grimorio",
    axe: "Ascia",
    mace: "Mazza",
    spear: "Lancia",
    scythe: "Falce",
    instrument: "Strumento",
    // weapon flavour
    arcane: "Arcana",
    holy: "Sacra",
    dark: "Oscura",
    blade: "Lama",
    sonic: "Sonora",
    // role/playstyle (mirrors ROLE_IT in Guida)
    tank: "Difensore",
    dps: "Attaccante",
    dps_melee: "Attacco in mischia",
    dps_ranged: "Attacco a distanza",
    dps_caster: "Incantatore",
    healer: "Guaritore",
    healer_dedicated: "Guaritore dedicato",
    healer_aoe: "Guaritore di gruppo",
    support: "Supporto",
    stealth: "Furtività",
    frontline: "Prima linea",
};


function _norm(s) {
    return (s || "").toString().toLowerCase().trim();
}

export function rarityLabel(rarity) {
    const k = _norm(rarity);
    return RARITY_IT[k] || rarity || "";
}

export function itemTypeLabel(t) {
    const k = _norm(t);
    return ITEM_TYPE_IT[k] || t || "";
}

export function tagLabel(tag) {
    const k = _norm(tag);
    return TAG_IT[k] || tag || "";
}

export function tagListLabel(tags, sep = " · ") {
    if (!Array.isArray(tags) || tags.length === 0) return "";
    return tags.map(tagLabel).join(sep);
}

export const RARITY_IT_MAP = RARITY_IT;
export const ITEM_TYPE_IT_MAP = ITEM_TYPE_IT;
export const TAG_IT_MAP = TAG_IT;
