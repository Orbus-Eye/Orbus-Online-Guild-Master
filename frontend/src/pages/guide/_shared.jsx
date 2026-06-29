// ROUND 11.4c — Shared primitives extracted from `Guide.jsx`.
//
// Contains:
//   • `SECTIONS` — full tab list driving the sticky nav.
//   • `POLARITY_LABEL`, `RARITY_LABEL` — i18n label maps for traits.
//   • `formatModifier()` — pretty-print helper for stat modifiers.
//   • `SectionBlock` — visual shell used by every guide section.
//
// Splitting these out keeps `Guide.jsx` focused on orchestration and lets
// the data-driven sections (Stats / Traits catalog) live in their own
// module without circular imports.

export const SECTIONS = [
    { id: "intro", label: "1. Introduzione" },
    { id: "gilda", label: "2. Gilda e progressione" },
    { id: "territorio", label: "3. Territorio di Gilda" },
    { id: "roster-cap", label: "4. Capacità roster e Dormitori" },
    { id: "roster-health", label: "5. Roster Health" },
    { id: "archivio", label: "6. Congedo e Archivio" },
    { id: "avventurieri", label: "7. Avventurieri" },
    { id: "ruoli", label: "8. Ruoli" },
    { id: "rarita", label: "9. Rarità" },
    { id: "stats-catalog", label: "10. Statistiche" },
    { id: "traits-catalog", label: "11. Tratti" },
    { id: "reclutamento", label: "12. Reclutamento" },
    { id: "dungeon", label: "13. Dungeon e Spedizioni" },
    { id: "raid", label: "14. Raid" },
    { id: "classifiche", label: "14b. Classifiche" },
    { id: "squadre", label: "15. Squadre Personalizzate" },
    { id: "forge", label: "16. Equipaggiamento e Fucina" },
    { id: "bound-items", label: "17. Item legati" },
    { id: "training", label: "18. Addestramento e Specializzazioni" },
    { id: "vault", label: "19. Deposito e Inventario" },
    { id: "materiali", label: "20. Materiali e dove trovarli" },
    { id: "market", label: "21. Mercato" },
    { id: "auction", label: "22. Asta" },
    { id: "contracts", label: "23. Contratti e Obiettivi di Gilda" },
    { id: "chronicle", label: "24. Cronaca" },
    { id: "consortium", label: "25. Consorzi" },
    { id: "chat", label: "26. Chat" },
    { id: "privacy", label: "27. Privacy e Sicurezza" },
    { id: "tips", label: "28. Suggerimenti base" },
];

// TASK 6 G4 — i18n + UX helpers per le sezioni data-driven.
export const POLARITY_LABEL = {
    positive: { label: "Positivo", cls: "text-emerald-300 border-emerald-500/40" },
    negative: { label: "Negativo", cls: "text-red-400 border-red-500/40" },
    mixed: { label: "Misto", cls: "text-amber border-amber/50" },
};

export const RARITY_LABEL = {
    common: "Comune",
    uncommon: "Non comune",
    rare: "Raro",
    epic: "Epico",
    legendary: "Leggendario",
};

export function formatModifier(modifier_type, modifier_value) {
    if (modifier_value == null || modifier_value === 0) return "—";
    const sign = modifier_value > 0 ? "+" : "";
    if (modifier_type === "percent") return `${sign}${modifier_value}%`;
    return `${sign}${modifier_value}`;
}

export const SectionBlock = ({ id, title, children }) => (
    <section
        id={id}
        data-testid={`guide-section-${id}`}
        className="border border-border bg-card rounded-sm p-5 mb-4 scroll-mt-24"
    >
        <h2 className="text-sm tracking-[0.3em] text-amber mb-3">:: {title}</h2>
        <div className="prose prose-invert prose-sm max-w-none text-[13px] leading-relaxed text-foreground/90">
            {children}
        </div>
    </section>
);
