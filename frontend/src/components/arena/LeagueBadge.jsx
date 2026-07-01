// ROUND 12.B — LeagueBadge: shared visual chip for league tier.
//
// 7 tiers, ognuno con colore + label IT + emoji testuale.
// Riusato in Seasons, Arena, Leaderboard.

const LEAGUE_META = {
    unranked:  { label: "Senza classifica", classes: "border-muted-foreground/40 text-muted-foreground", glyph: "—" },
    bronze:    { label: "Bronzo",           classes: "border-amber-700/60 text-amber-500",                glyph: "🜂" },
    silver:    { label: "Argento",          classes: "border-zinc-400/50 text-zinc-300",                  glyph: "🜁" },
    gold:      { label: "Oro",              classes: "border-amber/60 text-amber",                       glyph: "🜃" },
    platinum:  { label: "Platino",          classes: "border-cyan-400/60 text-cyan-300",                  glyph: "✦" },
    diamond:   { label: "Diamante",         classes: "border-sky-400/70 text-sky-300",                    glyph: "◆" },
    master:    { label: "Maestro",          classes: "border-fuchsia-400/70 text-fuchsia-300",            glyph: "✯" },
};

export default function LeagueBadge({ league, size = "sm" }) {
    const meta = LEAGUE_META[league] || LEAGUE_META.unranked;
    const sizeCls = size === "lg"
        ? "text-xs px-2.5 py-1 tracking-[0.18em]"
        : "text-[10px] px-1.5 py-0.5 tracking-[0.18em]";
    return (
        <span
            data-testid={`league-badge-${league || "unknown"}`}
            className={`inline-flex items-center gap-1 border rounded-sm font-mono uppercase ${sizeCls} ${meta.classes}`}
        >
            <span aria-hidden>{meta.glyph}</span>
            <span>{meta.label}</span>
        </span>
    );
}
