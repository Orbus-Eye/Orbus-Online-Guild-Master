// Phase 14.2 — frontend-only content translation helpers.
//
// The backend serves canonical English content (dungeon names/descriptions,
// trait names, class names, etc.) and we already have the localized values
// pre-baked in `i18n/lang/<lang>.json` under the `content.*` namespace.
//
// This module wires them up at the call sites that still receive the raw
// backend strings (expedition objects only ship `dungeon_name`, not
// `dungeon_slug`). The functions degrade safely: if no mapping is found
// they return the fallback (the original backend string), so the UI
// never shows an empty cell or a translation-key placeholder.

import en from "./lang/en.json";

// Build the reverse map: english-name -> slug, lazily, once.
let _nameToSlug = null;
function ensureNameToSlugMap() {
    if (_nameToSlug !== null) return _nameToSlug;
    _nameToSlug = {};
    const d = (en && en.content && en.content.dungeon) || {};
    Object.keys(d).forEach((slug) => {
        const n = d[slug] && d[slug].name;
        if (typeof n === "string") _nameToSlug[n] = slug;
    });
    return _nameToSlug;
}

/** Translate a dungeon name. Accepts the slug if you have it,
 * otherwise the canonical English `name` (which we reverse-map). */
export function translateDungeonName(tContent, dungeonOrName, lang) {
    if (!dungeonOrName) return "";
    if (typeof dungeonOrName === "object") {
        const slug = dungeonOrName.slug;
        const name = dungeonOrName.name;
        if (slug) return tContent("dungeon", slug, "name", name);
        return translateDungeonName(tContent, name, lang);
    }
    // String input — try reverse lookup.
    const map = ensureNameToSlugMap();
    const slug = map[dungeonOrName];
    if (slug) return tContent("dungeon", slug, "name", dungeonOrName);
    return dungeonOrName; // unknown — display untouched
}

/** FASE 10B — nome dungeon di una spedizione, IT-first.
 * Il backend ora espone `dungeon_name_it` (server-authoritative, anche
 * per i doc legacy); il reverse-map resta come ultima difesa. */
export function expeditionDungeonName(tContent, expedition, lang) {
    if (!expedition) return "";
    if (lang !== "en" && expedition.dungeon_name_it) {
        return expedition.dungeon_name_it;
    }
    return translateDungeonName(tContent, expedition.dungeon_name, lang);
}

/** Translate a dungeon description. Slug required for descriptions
 * because they don't appear in expedition payloads. */
export function translateDungeonDescription(tContent, dungeon) {
    if (!dungeon) return "";
    const slug = dungeon.slug;
    const desc = dungeon.description;
    if (slug) return tContent("dungeon", slug, "description", desc);
    return desc || "";
}
