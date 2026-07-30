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
    unique: "Unico",
    relic: "Reliquia",
};

const ITEM_TYPE_IT = {
    weapon: "Arma",
    armor: "Corazza",
    legs: "Gambe",
    helmet: "Elmo",
    accessory: "Accessorio",
    back: "Schiena",
    ring: "Anello",
    trinket: "Monile",
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

// ROUND 16.0 — Class & specialization display labels (Italian).
// The DB keeps internal slugs (`warrior`, `berserker_spec`, …); the UI
// always shows the Italian display name via these helpers.

const CLASS_IT = {
    warrior: "Guerriero",
    rogue: "Ladro",
    mage: "Mago",
    priest: "Sacerdote",
    ranger: "Ranger",
    paladin: "Paladino",
    druid: "Druido",
    monk: "Monaco",
    bard: "Bardo",
    warlock: "Occultista",
    // ROUND 16.0.1 — 11th base class.
    alchemist: "Alchimista",
    // Deprecated legacy slugs kept for safe rendering on old data:
    berserker: "Berserker",
    assassin: "Assassino",
    necromancer: "Negromante",
};

const SPEC_IT = {
    // Warrior
    berserker_spec: "Berserker",
    guardian_spec: "Guardiano",
    weapon_master_spec: "Maestro d'Armi",
    // Rogue
    assassin_spec: "Assassino",
    duelist_spec: "Duellante",
    shadow_spec: "Ombra",
    // Mage
    necromancer_spec: "Negromante",
    elementalist_spec: "Elementalista",
    arcanist_spec: "Arcanista",
    // Priest
    healer_spec: "Guaritore",
    exorcist_spec: "Esorcista",
    oracle_spec: "Oracolo",
    // Ranger
    marksman_spec: "Tiratore Scelto",
    monster_hunter_spec: "Cacciatore di Mostri",
    scout_spec: "Esploratore",
    // Druid
    leafwarden_spec: "Custode delle Foglie",
    shapeshifter_spec: "Mutaforma",
    shaman_spec: "Sciamano",
    // Monk
    inner_fist_spec: "Pugno Interiore",
    spirit_guardian_spec: "Guardiano Spirituale",
    ascetic_spec: "Asceta",
    // Bard
    warsinger_spec: "Canto di Guerra",
    herald_spec: "Araldo",
    inspiration_weaver_spec: "Tessitore d'Ispirazione",
    // Paladin
    oath_defender_spec: "Difensore del Giuramento",
    rune_knight_spec: "Cavaliere Runico",
    vindicator_spec: "Vendicatore",
    // Warlock
    demon_pact_spec: "Patto Infernale",
    void_pact_spec: "Patto del Vuoto",
    stellar_pact_spec: "Patto Stellare",
    // ROUND 16.0.1 — Alchemist
    bombardier_spec: "Bombardiere",
    toxicologist_spec: "Tossicologo",
    transmuter_spec: "Trasmutatore",
};

export function classLabel(slug) {
    const k = _norm(slug);
    return CLASS_IT[k] || slug || "";
}

export function specLabel(slug) {
    const k = _norm(slug);
    return SPEC_IT[k] || slug || "";
}

export const CLASS_IT_MAP = CLASS_IT;
export const SPEC_IT_MAP = SPEC_IT;

export const RARITY_IT_MAP = RARITY_IT;
export const ITEM_TYPE_IT_MAP = ITEM_TYPE_IT;
export const TAG_IT_MAP = TAG_IT;
