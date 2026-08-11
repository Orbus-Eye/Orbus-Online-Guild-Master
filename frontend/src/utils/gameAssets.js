// FASE 4 (2026-08-08) — Mapping centralizzato degli asset di gioco.
//
// Tutti gli asset vivono in /public/assets (placeholder SVG generati da
// scripts/fase4_genera_assets.py). Quando arriva l'art definitiva basta
// sostituire i FILE mantenendo i nomi: questo modulo non cambia.
// Ogni helper ritorna una CATENA di fallback (usata da <GameImage/>):
// [specifico, tema, default] — un file mancante non rompe mai la UI.

// Dungeon slug → tema visivo (famiglie in /assets/themes/*.svg).
const DUNGEON_THEME = {
    "training-yard": "tutorial",
    "sewer-nest": "caves",
    "goblin-warrens": "caves",
    "bandit-hideout": "beast",
    "druid-grove": "nature",
    "shadow-crypts": "crypt",
    "cursed-mines": "mines",
    "sunken-library": "library",
    "lich-sanctum": "crypt",
    "dragons-hoard": "dragon",
    "storm-spire": "storm",
    "wolf-den-5p": "beast",
    "frost-cave-5p": "frost",
    "salt-marsh-5p": "marsh",
    "iron-foundry-5p": "forge",
    "silent-monastery-5p": "celestial",
    "pirate-fleet-5p": "sea",
    "obsidian-arena-5p": "arena",
    "clockwork-vault-5p": "clockwork",
    "voidspire-5p": "void",
    "infernal-pit-5p": "infernal",
    "celestial-citadel-5p": "celestial",
    "world-tree-roots-5p": "worldtree",
};

/** Catena immagini per una card dungeon. */
export function dungeonImageSources(slugOrDungeon) {
    const slug = typeof slugOrDungeon === "string"
        ? slugOrDungeon
        : slugOrDungeon?.slug || "";
    const theme = DUNGEON_THEME[slug];
    const chain = [`/assets/dungeons/${slug}.svg`];
    if (theme) chain.push(`/assets/themes/${theme}.svg`);
    chain.push("/assets/themes/default.svg");
    return chain;
}

/** Catena immagini per una card raid. */
export function raidImageSources(slug) {
    return [
        `/assets/raids/${slug}.svg`,
        "/assets/themes/default.svg",
    ];
}

// FASE 6 — gli upload custom sono serviti dal BACKEND (/api/uploads/...):
// il path relativo va risolto sull'origin del backend, non su quello FE.
const BACKEND_ORIGIN = process.env.REACT_APP_BACKEND_URL || "";

function resolveCustomAvatarUrl(url) {
    if (!url) return null;
    if (/^https?:\/\//i.test(url)) return url;
    return `${BACKEND_ORIGIN}${url}`;
}

/** Catena avatar per un avventuriero (razza × genere).
 *  `custom_avatar_url` (upload Fase 6) ha la precedenza quando presente. */
export function avatarSources(adv) {
    const chain = [];
    const custom = resolveCustomAvatarUrl(adv?.custom_avatar_url);
    if (custom) chain.push(custom);
    const race = adv?.race_slug;
    const gender = adv?.gender === "female" ? "female" : "male";
    if (race) chain.push(`/assets/avatars/${race}_${gender}.svg`);
    chain.push("/assets/avatars/default.svg");
    return chain;
}

/** Banner di sezione (/assets/banners/*.svg). */
export function sectionBanner(section) {
    return [
        `/assets/banners/${section}.svg`,
        "/assets/banners/dashboard.svg",
    ];
}

/** FASE 9K — catena banner della gilda: il banner personalizzato
 *  caricato dal PC ha PRIORITÀ sul banner standard; rimosso l'upload
 *  si torna al banner di sezione (mai immagini rotte). */
export function guildBannerSources(guild) {
    const chain = [];
    const custom = resolveCustomAvatarUrl(guild?.custom_banner_url);
    if (custom) chain.push(custom);
    chain.push(...sectionBanner("dashboard"));
    return chain;
}

export { DUNGEON_THEME, resolveCustomAvatarUrl };
