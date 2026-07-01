// Round 11.3 Task 3D.3 — UI-side level-gate helpers.
//
// Backend is authoritative; these helpers only drive presentation
// (opacity, badges, disabled handlers, tooltips). They MUST mirror
// the same rules used server-side:
//   - Dungeons/Raids: adventurer.level >= content.min_adventurer_level
//   - Items: adventurer.level >= item.required_adventurer_level
//
// All user-facing strings are in Italian (IT-first UX).

/**
 * @param {{level?: number}} adv
 * @param {number|undefined|null} minLevel
 * @returns {boolean} true if the adventurer is BELOW the required level
 */
export function isAdventurerUnderLeveled(adv, minLevel) {
    if (!adv) return false;
    const min = Number(minLevel) || 1;
    if (min <= 1) return false;
    return (Number(adv.level) || 1) < min;
}

/**
 * @param {{required_adventurer_level?: number|null}} item
 * @param {{level?: number}} adv
 * @returns {boolean} true if the item REQUIRES a higher level than the adventurer has
 */
export function isItemUnderLeveled(item, adv) {
    if (!item || !adv) return false;
    const req = Number(item.required_adventurer_level) || 1;
    if (req <= 1) return false;
    return (Number(adv.level) || 1) < req;
}

/** Short IT badge for adventurer cards: "Lv min: 8" */
export function advMinLevelBadge(minLevel) {
    return `Lv min: ${minLevel}`;
}

/** Short IT badge for item cards: "Lv 12 richiesto" */
export function itemReqLevelBadge(requiredLevel) {
    return `Lv ${requiredLevel} richiesto`;
}

/** Full IT tooltip for under-leveled adventurer in a dungeon */
export function advDungeonTooltip(minLevel) {
    return `Servono Lv ${minLevel}+ per questo dungeon`;
}

/** Full IT tooltip for under-leveled adventurer in a raid */
export function advRaidTooltip(minLevel) {
    return `Servono Lv ${minLevel}+ per questo raid`;
}

/** Full IT tooltip for an item the adventurer cannot equip yet */
export function itemReqLevelTooltip(requiredLevel) {
    return `Questo equipaggiamento richiede Lv ${requiredLevel}.`;
}
