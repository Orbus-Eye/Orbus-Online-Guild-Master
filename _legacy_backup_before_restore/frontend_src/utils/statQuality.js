/**
 * ROUND 16.0 — Phase 3 — Frontend stat quality helper.
 *
 * Maps a numeric stat to a qualitative tier used to colour-code the
 * adventurer roster grid. Single source of truth for both
 * Adventurers.jsx and any future detail page.
 *
 * Tiers:
 *   common      → value ≤ 55% of maxValue   (white-grey)
 *   good        → 55% < value ≤ 75%         (green)
 *   rare        → 75% < value ≤ 95%         (purple)
 *   legendary   → value > 95%               (orange)
 *
 * Accessibility: `label` is always returned in Italian; consumers
 * SHOULD set aria-label and/or render the textual label so the tier
 * is conveyed without colour alone.
 */

const QUALITY_RULES = [
    { tier: "legendary", ratio: 0.95, label: "Eccellente",
      className: "stat-quality-legendary", color: "#ff8a3d" },
    { tier: "rare", ratio: 0.75, label: "Alta",
      className: "stat-quality-rare", color: "#a855f7" },
    { tier: "good", ratio: 0.55, label: "Buona",
      className: "stat-quality-good", color: "#22c55e" },
    { tier: "common", ratio: -Infinity, label: "Comune",
      className: "stat-quality-common", color: "#cbd5e1" },
];

/**
 * @param {number} value          Stat value (e.g. 12)
 * @param {number} [maxValue=15]  Max value the stat is benchmarked against.
 * @returns {{tier:string,label:string,className:string,color:string}}
 */
export function getStatQuality(value, maxValue = 15) {
    const v = Number.isFinite(value) ? Number(value) : 0;
    const m = Number.isFinite(maxValue) && maxValue > 0 ? Number(maxValue) : 15;
    const ratio = v / m;
    if (ratio > QUALITY_RULES[0].ratio) return QUALITY_RULES[0];
    if (ratio > QUALITY_RULES[1].ratio) return QUALITY_RULES[1];
    if (ratio > QUALITY_RULES[2].ratio) return QUALITY_RULES[2];
    return QUALITY_RULES[3];
}

export const QUALITY_TIERS = QUALITY_RULES.map((q) => q.tier);

export function statQualityLabel(value, maxValue = 15) {
    return getStatQuality(value, maxValue).label;
}
