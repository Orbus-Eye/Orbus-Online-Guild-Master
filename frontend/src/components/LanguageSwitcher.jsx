import { useT } from "../i18n/I18nContext";

/**
 * Compact EN | IT toggle for the navbar.
 *
 * Always renders two pills; the active one is highlighted. Switch is
 * instant (Context re-render) and persisted by I18nContext.
 */
export default function LanguageSwitcher() {
    const { lang, setLang } = useT();
    return (
        <div
            className="inline-flex items-center gap-0.5 border border-border rounded-sm overflow-hidden"
            data-testid="language-switcher"
        >
            <button
                type="button"
                onClick={() => setLang("en")}
                data-testid="lang-en-btn"
                aria-pressed={lang === "en"}
                className={`px-2 py-1 text-[10px] tracking-widest transition-colors ${
                    lang === "en"
                        ? "bg-amber text-amber-foreground"
                        : "text-muted-foreground hover:text-foreground hover:bg-secondary"
                }`}
            >
                EN
            </button>
            <button
                type="button"
                onClick={() => setLang("it")}
                data-testid="lang-it-btn"
                aria-pressed={lang === "it"}
                className={`px-2 py-1 text-[10px] tracking-widest transition-colors ${
                    lang === "it"
                        ? "bg-amber text-amber-foreground"
                        : "text-muted-foreground hover:text-foreground hover:bg-secondary"
                }`}
            >
                IT
            </button>
        </div>
    );
}
