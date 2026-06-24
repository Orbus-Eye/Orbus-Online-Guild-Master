/**
 * Phase 12 — i18n core (EN/IT).
 *
 * Tiny custom implementation (no i18next/formatjs): nested dict lookup with
 * dot-path keys, mustache-style {param} interpolation, robust fallback chain
 * (it → en → key string). NEVER returns undefined and NEVER throws.
 */
import {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useState,
} from "react";
import en from "./lang/en.json";
import it from "./lang/it.json";

const DICTS = { en, it };
const SUPPORTED = ["en", "it"];
const STORAGE_KEY = "orbus.lang";
const FALLBACK = "en";

function detectBrowserLang() {
    if (typeof navigator === "undefined") return FALLBACK;
    const raw = (navigator.language || navigator.languages?.[0] || "").toLowerCase();
    if (raw.startsWith("it")) return "it";
    return FALLBACK;
}

function readStoredLang() {
    if (typeof localStorage === "undefined") return null;
    try {
        const v = localStorage.getItem(STORAGE_KEY);
        if (v && SUPPORTED.includes(v)) return v;
    } catch (_e) {
        // ignore
    }
    return null;
}

function lookup(dict, key) {
    if (!dict || !key) return undefined;
    const parts = key.split(".");
    let node = dict;
    for (const p of parts) {
        if (node && typeof node === "object" && p in node) {
            node = node[p];
        } else {
            return undefined;
        }
    }
    return node;
}

function interpolate(str, params) {
    if (typeof str !== "string" || !params) return str;
    return str.replace(/\{(\w+)\}/g, (_, k) =>
        params[k] !== undefined && params[k] !== null ? String(params[k]) : `{${k}}`,
    );
}

/**
 * Resolve a translation key with fallback: active → en → key.
 * Returns the key string itself if no dictionary has it (visible in dev,
 * never crashes UI).
 */
export function resolve(lang, key, params) {
    const primary = lookup(DICTS[lang], key);
    if (typeof primary === "string") return interpolate(primary, params);
    if (lang !== FALLBACK) {
        const fb = lookup(DICTS[FALLBACK], key);
        if (typeof fb === "string") return interpolate(fb, params);
    }
    return key;
}

/**
 * Resolve a content sub-object (class/trait/dungeon).
 *
 * @returns the value at `content.<group>.<slug>.<field>` or the supplied
 *          `fallback` (typically the original backend string) when missing.
 *          NEVER undefined.
 */
export function resolveContent(lang, group, slug, field, fallback) {
    if (!slug) return fallback ?? "";
    const key = `content.${group}.${slug}${field ? "." + field : ""}`;
    const primary = lookup(DICTS[lang], key);
    if (typeof primary === "string") return primary;
    if (lang !== FALLBACK) {
        const fb = lookup(DICTS[FALLBACK], key);
        if (typeof fb === "string") return fb;
    }
    return fallback ?? slug;
}

const I18nContext = createContext({
    lang: FALLBACK,
    setLang: () => {},
    t: (k) => k,
    tContent: (_g, slug, _f, fb) => fb ?? slug,
});

export function I18nProvider({ children }) {
    const [lang, setLangState] = useState(() => readStoredLang() || detectBrowserLang());

    useEffect(() => {
        try {
            localStorage.setItem(STORAGE_KEY, lang);
        } catch (_e) {
            // ignore quota / privacy mode
        }
        if (typeof document !== "undefined") {
            document.documentElement.setAttribute("lang", lang);
        }
    }, [lang]);

    const setLang = useCallback((next) => {
        if (SUPPORTED.includes(next)) setLangState(next);
    }, []);

    const t = useCallback(
        (key, params) => resolve(lang, key, params),
        [lang],
    );
    const tContent = useCallback(
        (group, slug, field, fallback) => resolveContent(lang, group, slug, field, fallback),
        [lang],
    );

    const value = useMemo(
        () => ({ lang, setLang, t, tContent, supported: SUPPORTED }),
        [lang, setLang, t, tContent],
    );

    return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useT() {
    return useContext(I18nContext);
}
