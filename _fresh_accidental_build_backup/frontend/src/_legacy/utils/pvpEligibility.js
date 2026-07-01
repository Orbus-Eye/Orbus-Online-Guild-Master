// ROUND 12.B — Eligibility helper for PvP defense/attack team picker.
// Mirror of `utils/levelGate.js` but PvP-specific.
//
// An adventurer is eligible if:
//   * `is_available` is true (not retired, not frozen, not on expedition).
//   * `level >= minLevel` (server-driven, comes from /api/pvp/defense-team).
//   * not already in the team being assembled.
//
// Returns `{ eligible: bool, reason: string|null }` so the UI can grey-out
// and surface why.

export function pvpEligibility(adv, { minLevel, alreadyChosenIds = [] } = {}) {
    if (!adv) return { eligible: false, reason: "missing" };
    if (alreadyChosenIds.includes(adv.id)) {
        return { eligible: false, reason: "Già nella squadra" };
    }
    if (adv.is_available === false) {
        return { eligible: false, reason: "Non disponibile" };
    }
    if ((adv.level || 0) < (minLevel || 1)) {
        return { eligible: false, reason: `Livello insufficiente (min ${minLevel})` };
    }
    if (adv.archived || adv.retired) {
        return { eligible: false, reason: "Archiviato" };
    }
    if (adv.frozen) {
        return { eligible: false, reason: "Congelato" };
    }
    return { eligible: true, reason: null };
}
