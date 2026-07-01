// Phase 14.1 — centralized date / time formatting for IT and EN locales.
//
// Backend stores everything in UTC. The frontend displays values in the
// user's current language with the matching timezone:
//   - "it"  → it-IT  + Europe/Rome
//   - "en"  → en-GB  + UTC (preserves the previous "… UTC" behaviour)
//
// Three exports cover every existing call site:
//   - formatDateTime(iso, lang)      → "12/02/2026, 18:42" (IT) / "12/02/2026 16:42 UTC" (EN)
//   - formatDateShort(iso, lang)     → "12/02/2026" (IT) / "2026-02-12" (EN)
//   - formatRelative(iso, lang, t)   → "5m fa" (IT) / "5m ago" (EN), via t() keys
//   - formatCountdown(deltaIsoOrSec) → "Xh Ym" — locale-neutral, unchanged.
//
// Keep this module side-effect free and dependency-free. It must work
// during SSR and in tests.

const ZONE_BY_LANG = {
    it: "Europe/Rome",
    en: "UTC",
};

const NUMERIC_LOCALE = {
    it: "it-IT",
    en: "en-GB",
};

export function getTimezoneForLang(lang) {
    return ZONE_BY_LANG[lang] || "UTC";
}

export function getNumericLocale(lang) {
    return NUMERIC_LOCALE[lang] || "en-GB";
}

/** Full date + time. Adds " UTC" suffix on EN to stay backward-compatible. */
export function formatDateTime(iso, lang) {
    if (!iso) return "—";
    try {
        const d = new Date(iso);
        const tz = getTimezoneForLang(lang);
        const loc = getNumericLocale(lang);
        const opts = {
            timeZone: tz,
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
        };
        const formatted = new Intl.DateTimeFormat(loc, opts).format(d);
        return lang === "en" ? `${formatted} UTC` : formatted;
    } catch {
        return iso;
    }
}

/** Date only, no time. */
export function formatDateShort(iso, lang) {
    if (!iso) return "—";
    try {
        const d = new Date(iso);
        const tz = getTimezoneForLang(lang);
        const loc = getNumericLocale(lang);
        return new Intl.DateTimeFormat(loc, {
            timeZone: tz,
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
        }).format(d);
    } catch {
        return iso;
    }
}

/**
 * Relative time, ago. Needs the i18n `t` accessor to localize the
 * unit suffix. Falls back to English literals if `t` is not provided.
 *
 * Expected i18n keys (added in Phase 14.1):
 *   common.relative.s_ago, m_ago, h_ago, d_ago
 */
export function formatRelative(iso, lang, t) {
    if (!iso) return "";
    try {
        const target = new Date(iso).getTime();
        const diff = Math.max(0, Date.now() - target);
        const s = Math.floor(diff / 1000);
        const fallback = (n, unit) => `${n}${unit} ago`;
        const localize = (key, params) =>
            (typeof t === "function" ? t(key, params) : null) || fallback(params.n, key.slice(-5, -4));
        if (s < 60) return localize("common.relative.s_ago", { n: s });
        const m = Math.floor(s / 60);
        if (m < 60) return localize("common.relative.m_ago", { n: m });
        const h = Math.floor(m / 60);
        if (h < 24) return localize("common.relative.h_ago", { n: h });
        const d = Math.floor(h / 24);
        return localize("common.relative.d_ago", { n: d });
    } catch {
        return "";
    }
}

/** Countdown to a future ISO timestamp. Locale-neutral ("Xh Ym"). */
export function formatCountdown(targetIso) {
    try {
        const target = new Date(targetIso).getTime();
        const diff = Math.max(0, target - Date.now());
        const h = Math.floor(diff / 3_600_000);
        const m = Math.floor((diff % 3_600_000) / 60_000);
        return `${h}h ${m}m`;
    } catch {
        return "";
    }
}
