// ROUND 6B.2b — Structure metadata mirror (frontend-side, no API drift).
// Source of truth on the backend lives in app/territory/structures.py.
// Names/descriptions are duplicated here for fast rendering without an extra
// API call. Keep in sync if the catalog changes.

export const STRUCTURE_META = {
    guild_hall: {
        name_it: "Sala della Gilda",
        name_en: "Guild Hall",
        desc_it: "Il cuore amministrativo della gilda. Sblocca le altre strutture.",
        desc_en: "The administrative heart. Unlocks the other structures.",
        order: 1,
    },
    dormitories: {
        name_it: "Dormitori",
        name_en: "Dormitories",
        // ROUND 11.2 TASK 4 — scala 1-11, cap massimo 100.
        desc_it: "Determina la capienza massima del roster (scala 1-11, cap massimo 100: 5 → 10 → 15 → 20 → 25 → 30 → 40 → 50 → 65 → 80 → 100).",
        desc_en: "Sets the roster capacity (range 1-11, max cap 100: 5 → 10 → 15 → 20 → 25 → 30 → 40 → 50 → 65 → 80 → 100).",
        order: 2,
    },
    expedition_board: {
        name_it: "Bacheca Spedizioni",
        name_en: "Expedition Board",
        desc_it: "Bacheca delle spedizioni. Più alto = dungeon di tier maggiore.",
        desc_en: "Expedition board. Higher level unlocks higher-tier dungeons.",
        order: 3,
    },
    war_room: {
        name_it: "Sala della Guerra",
        name_en: "War Room",
        desc_it: "Strategia per le incursioni. Lv2 sblocca i Raid T1, Lv3 i T2.",
        desc_en: "Raid command. Lv2 unlocks T1 raids, Lv3 the T2.",
        order: 4,
    },
    market_stall: {
        name_it: "Banco del Mercato",
        name_en: "Market Stall",
        desc_it: "Accesso al mercato NPC: Lv1 per comprare, Lv2 anche per vendere.",
        desc_en: "NPC shop: Lv1 to buy, Lv2 also to sell.",
        order: 5,
    },
    auction_house: {
        name_it: "Casa d'Aste",
        name_en: "Auction House",
        desc_it: "Mercato tra giocatori: Lv1 per comprare, Lv2 per mettere in vendita.",
        desc_en: "Player-to-player market: Lv1 buy, Lv2 list.",
        order: 6,
    },
    workshop: {
        name_it: "Officina",
        name_en: "Workshop",
        desc_it: "Crafting di nuovi oggetti dalle ricette. Lv↑ ricette più rare.",
        desc_en: "Crafting recipes. Higher level = rarer items.",
        order: 7,
    },
    forge: {
        name_it: "Fucina",
        name_en: "Forge",
        desc_it: "Potenziamento equipaggiamento: Lv1 dis-incantare, Lv2 raffinare, Lv3 incantare, Lv4 reroll.",
        desc_en: "Equip upgrades: Lv1 disenchant, Lv2 refine, Lv3 enchant, Lv4 reroll.",
        order: 8,
    },
    consortium_hall: {
        name_it: "Sala dei Consorzi",
        name_en: "Consortium Hall",
        desc_it: "Lv1 per unirti a un consorzio, Lv2 per crearne uno.",
        desc_en: "Lv1 to join a consortium, Lv2 to create one.",
        order: 9,
    },
    communication_hall: {
        name_it: "Sala delle Comunicazioni",
        name_en: "Communication Hall",
        desc_it: "Lv1 sblocca la chat globale, Lv2 la chat consorzio.",
        desc_en: "Lv1 unlocks global chat, Lv2 consortium chat.",
        order: 10,
    },
    training_grounds: {
        name_it: "Campo di Addestramento",
        name_en: "Training Grounds",
        desc_it: "Specializzazioni avventurieri (in arrivo).",
        desc_en: "Adventurer specializations (coming soon).",
        order: 11,
    },
};

export const STRUCTURE_SLUGS = Object.keys(STRUCTURE_META).sort(
    (a, b) => STRUCTURE_META[a].order - STRUCTURE_META[b].order,
);

export function getStructureName(slug, lang = "it") {
    const meta = STRUCTURE_META[slug];
    return (meta && meta[`name_${lang}`]) || slug;
}

export function getStructureDescription(slug, lang = "it") {
    const meta = STRUCTURE_META[slug];
    return (meta && meta[`desc_${lang}`]) || "";
}

// Upgrade costs duplicated (no API for now). Mirrors backend
// `app/territory/costs.py`. Index = target level. null = legacy-only.
// ROUND 11.2 TASK 4 — `dormitories` extended Lv7-Lv11 (cap 40→100) with
// progressive gold + materials costs (aligned exactly with backend).
export const UPGRADE_COSTS = {
    guild_hall: [null, { gold: 0 }, { gold: 200 }, { gold: 500 }, { gold: 1200 }, { gold: 2500 }, { gold: 5000 }],
    dormitories: [
        null,
        { gold: 0 },                                       // Lv 1 (cap 5)
        { gold: 200 },                                     // Lv 2 (cap 10)
        { gold: 500 },                                     // Lv 3 (cap 15)
        { gold: 1200 },                                    // Lv 4 (cap 20)
        { gold: 2500, materials: { iron_shard: 8 } },      // Lv 5 (cap 25)
        { gold: 5000, materials: { iron_shard: 16 } },     // Lv 6 (cap 30)
        { gold: 8500, materials: { iron_shard: 24, greater_arcane_dust: 3 } },   // Lv 7 (cap 40)
        { gold: 14000, materials: { iron_shard: 36, greater_arcane_dust: 6 } },  // Lv 8 (cap 50)
        { gold: 22000, materials: { iron_shard: 50, greater_arcane_dust: 10, lesser_arcane_dust: 4 } }, // Lv 9 (cap 65)
        { gold: 32000, materials: { iron_shard: 70, greater_arcane_dust: 16, lesser_arcane_dust: 8 } }, // Lv 10 (cap 80)
        { gold: 50000, materials: { iron_shard: 100, greater_arcane_dust: 25, lesser_arcane_dust: 12 } }, // Lv 11 (cap 100)
    ],
    expedition_board: [null, { gold: 0 }, { gold: 200 }, { gold: 500 }, { gold: 1200 }, { gold: 2500 }, { gold: 5000 }],
    war_room: [null, { gold: 100 }, { gold: 250 }, { gold: 700 }, { gold: 1500 }, { gold: 3000 }, { gold: 6000 }],
    market_stall: [null, { gold: 50 }, { gold: 200 }, { gold: 500 }, { gold: 1200 }, { gold: 2500 }, { gold: 5000 }],
    auction_house: [null, { gold: 100 }, { gold: 300 }, { gold: 700 }, { gold: 1500 }, { gold: 3000 }, { gold: 6000 }],
    workshop: [null, { gold: 100 }, { gold: 300 }, { gold: 700 }, { gold: 1500 }, { gold: 3000 }, { gold: 6000 }],
    forge: [null, { gold: 150 }, { gold: 400 }, { gold: 900 }, { gold: 1800 }, { gold: 3500 }, { gold: 7000 }],
    consortium_hall: [null, { gold: 100 }, { gold: 300 }, { gold: 700 }, { gold: 1500 }, { gold: 3000 }, { gold: 6000 }],
    communication_hall: [null, { gold: 50 }, { gold: 200 }, { gold: 500 }, { gold: 1200 }, { gold: 2500 }, { gold: 5000 }],
    training_grounds: [null, { gold: 200 }, { gold: 500 }, { gold: 1200 }, { gold: 2500 }, { gold: 5000 }, { gold: 10000 }],
};

export const PREREQUISITES = {
    war_room: { guild_hall: 2 },
    market_stall: { guild_hall: 1 },
    auction_house: { guild_hall: 2 },
    workshop: { guild_hall: 2 },
    forge: { guild_hall: 2, workshop: 1 },
    consortium_hall: { guild_hall: 3 },
    communication_hall: { guild_hall: 2 },
    training_grounds: { guild_hall: 3, dormitories: 2 },
};

export const MAX_LEVEL = 6;          // default cap (legacy callers)
export const DORM_CAP_BY_LEVEL = [0, 5, 10, 15, 20, 25, 30, 40, 50, 65, 80, 100];

// ROUND 11.2 TASK 4 — per-structure max level. Mirrors backend
// `app/territory/structures.py::STRUCTURE_CATALOG[*].max_level`. Anything
// not listed falls back to `MAX_LEVEL` (6) for backwards compatibility.
export const STRUCTURE_MAX_LEVEL = {
    dormitories: 11,
};

export function getStructureMaxLevel(slug) {
    return STRUCTURE_MAX_LEVEL[slug] ?? MAX_LEVEL;
}

/** Resolve the card state for a structure given the territory + guild gold. */
export function resolveCardState({ slug, structure, structures, gold }) {
    const level = Number(structure?.level || 0);
    const isUnlocked = Boolean(structure?.is_unlocked);
    const isLegacy = structure?.acquired_via === "migration_legacy";
    // ROUND 11.2 TASK 4 — per-structure max. Dormitories now goes up to Lv11.
    const maxLevel = getStructureMaxLevel(slug);
    const isMaxed = level >= maxLevel;
    const costTable = UPGRADE_COSTS[slug] || [];

    // ROUND 11.2 P1 fix — `legacy` is INFO, not a blocker. If the legacy
    // structure is below its max level it MUST still be upgradable so the
    // player can advance (e.g. legacy Lv7 dormitory → Lv8 cap 50).
    if (isLegacy && isMaxed) {
        return { kind: "legacy", level, isLegacy: true, isMaxed: true };
    }
    if (isMaxed) {
        return { kind: "max", level, isMaxed: true };
    }

    // Check prerequisites against the desired target level.
    const targetLevel = level + 1;
    const cost = costTable[targetLevel];
    if (cost === null || cost === undefined) {
        return { kind: "max", level, isMaxed: true };
    }
    const prereqs = PREREQUISITES[slug] || {};
    const unmet = Object.entries(prereqs).filter(
        ([reqSlug, reqLvl]) => Number(structures?.[reqSlug]?.level || 0) < reqLvl,
    );

    const goldNeeded = Number(cost.gold || 0);
    const hasGold = Number(gold || 0) >= goldNeeded;

    // Lv0 + not-unlocked = "purchase" path; Lv≥1 = "upgrade" path.
    const isPurchase = level === 0 || !isUnlocked;

    if (unmet.length > 0) {
        return {
            kind: "locked_prereq",
            level,
            unmet: unmet.map(([reqSlug, reqLvl]) => ({ slug: reqSlug, min_level: reqLvl })),
            targetLevel,
            cost,
            isLegacy,  // surface to UI as info badge even when upgradable
        };
    }
    return {
        kind: hasGold ? (isPurchase ? "buyable" : "upgradable") : "insufficient_gold",
        level,
        targetLevel,
        cost,
        goldNeeded,
        isPurchase,
        isLegacy,  // surface to UI as info badge even when upgradable
    };
}
