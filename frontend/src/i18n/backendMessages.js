/**
 * Phase 12 — best-effort backend-message → i18n key mapper.
 *
 * Backend error/lock strings stay in English (no backend i18n in Phase 12).
 * The frontend tries to parse known patterns and route them through the
 * normal `t()` helper. If parsing fails we return the original English
 * string so the user always sees *something* meaningful.
 */

/**
 * Map a `unlock_reason` coming from `GET /api/dungeons` to a localized
 * string via `t()`.
 *
 * Known patterns:
 *  - "Requires N adventurers, you have M"
 *  - "Requires peak team power >= N"
 *  - "Requires guild level >= L OR peak power >= P"
 *  - "Shadow Crypts sticky gate: ..."
 *  - "Dragon's Hoard sticky gate"
 */
export function localizeUnlockReason(t, reason, dungeonSlug) {
    if (!reason) return "";
    const r = String(reason);

    // min_adventurers pattern
    let m = r.match(/(\d+)\s+adventurers?, you have\s+(\d+)/i);
    if (m) {
        return t("dungeons.unlock_reasons.min_adventurers", {
            n: m[1],
            have: m[2],
        });
    }

    // min_level_or_power pattern (T3 OR gate)
    m = r.match(/level\s*>?=?\s*(\d+).*?(?:OR|or).*?power\s*>?=?\s*(\d+)/i);
    if (m) {
        return t("dungeons.unlock_reasons.min_level_or_power", {
            level: m[1],
            power: m[2],
        });
    }

    // dragons-hoard sticky
    if (dungeonSlug === "dragons-hoard" || /dragon'?s? hoard/i.test(r)) {
        return t("dungeons.unlock_reasons.dragons_hoard");
    }

    // shadow-crypts gate (Phase 7 — explicit power threshold)
    m = r.match(/power\s*>?=?\s*(\d+)/i);
    if (m && dungeonSlug === "shadow-crypts") {
        return t("dungeons.unlock_reasons.shadow_crypts", { need: m[1] });
    }

    // generic min_power
    if (m) {
        // try "you have N" suffix
        const h = r.match(/have\s+(\d+)/i);
        return t("dungeons.unlock_reasons.min_power", {
            need: m[1],
            have: h ? h[1] : "?",
        });
    }

    // Unknown pattern → fall back to the original (English) backend string.
    return r;
}

/**
 * Map a backend error response (axios error) to a localized string.
 * Handles known patterns; otherwise returns the original `detail`.
 */
export function localizeBackendError(t, err) {
    const detail = err?.response?.data?.detail;
    if (!detail) return t("errors.network");
    const status = err?.response?.status;
    const msg = typeof detail === "string" ? detail : JSON.stringify(detail);

    // Insufficient gold pattern: "Insufficient gold (need X, have Y)"
    const g = msg.match(/need\s+(\d+).*?have\s+(\d+)/i);
    if (g && status === 402) {
        return t("errors.insufficient_gold", { need: g[1], have: g[2] });
    }

    // Dungeon locked pattern
    const d = msg.match(/(?:dungeon\s+locked|locked):\s*(.+)/i);
    if (d) {
        return t("errors.dungeon_locked", { reason: d[1] });
    }

    if (status === 401) return t("errors.unauthorized");
    if (status === 403) return t("errors.forbidden");
    if (status === 404) return t("errors.not_found");
    if (status === 422) return t("errors.validation");
    if (status >= 500) return t("errors.server");

    return msg;
}
