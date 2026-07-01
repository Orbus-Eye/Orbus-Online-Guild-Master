// ROUND 16.3 Phase 8 V1 Iter2 — reusable mount card for /stables catalog.
// Renders one mount with rarity accent, domain, and ownership/active status.
// Purely cosmetic — no stats displayed because no stats exist by design.

const RARITY_COLORS = {
    common: { text: "text-zinc-400", border: "border-zinc-700",
              badge: "bg-zinc-800/60 text-zinc-300", label: "Comune" },
    uncommon: { text: "text-green-400", border: "border-green-800/60",
                badge: "bg-green-950/40 text-green-400", label: "Non comune" },
    rare: { text: "text-blue-400", border: "border-blue-800/60",
            badge: "bg-blue-950/40 text-blue-400", label: "Rara" },
    epic: { text: "text-purple-400", border: "border-purple-800/60",
            badge: "bg-purple-950/40 text-purple-400", label: "Epica" },
};

const DOMAIN_LABEL_IT = {
    starter: "Starter",
    ambash: "Ambash",
    velur: "Velur",
    soe: "Soe",
    efreto: "Efreto",
    irthe: "Irthe",
    nathos: "Nathos",
    ergolat: "Ergolat",
    aveol: "Aveol",
};

const SOURCE_TYPE_LABEL_IT = {
    starter_quest: "Missione iniziale",
    world_boss_drop: "Ricompensa World Boss",
    achievement: "Impresa sbloccata",
    craft: "Crafting dedicato",
    narrative: "Rotta narrativa",
    admin_grant: "Assegnazione admin",
};

// Emoji per slug — leggeri, no immagini pesanti.
const MOUNT_EMOJI = {
    "ronzino-di-strada": "🐎",
    "scarabeo-runico": "🪲",
    "cervo-lunare": "🦌",
    "lupo-delle-fronde": "🐺",
    "salamandra-di-efreto": "🦎",
    "segugio-cinereo": "🐕",
    "remora-tempestosa": "🐟",
    "ombra-sellata": "👻",
    "grifone-delle-alture": "🦅",
};

export function mountEmoji(slug) {
    return MOUNT_EMOJI[slug] || "🐴";
}

export function domainLabelIt(slug) {
    return DOMAIN_LABEL_IT[slug] || slug;
}

export default function MountCard({ mount, onActivate, onDeactivate, busy }) {
    const rar = RARITY_COLORS[mount.rarity] || RARITY_COLORS.common;
    const isOwned = Boolean(mount.is_owned);
    const isActive = Boolean(mount.is_active);
    const emoji = mountEmoji(mount.slug);

    const borderClass = isActive
        ? "border-green-500/70 ring-1 ring-green-500/30"
        : isOwned
            ? `${rar.border} border`
            : "border-zinc-800/50 border";

    return (
        <div
            data-testid={`mount-card-${mount.slug}`}
            className={`rounded-lg p-4 bg-zinc-900/50 transition ${borderClass} ${!isOwned ? "opacity-60" : ""}`}
        >
            <div className="flex items-start gap-3">
                <div className="text-3xl leading-none select-none" aria-hidden>
                    {emoji}
                </div>
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                        <div className="text-sm font-semibold text-zinc-100 truncate"
                             data-testid={`mount-name-${mount.slug}`}>
                            {mount.name_it}
                        </div>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded uppercase tracking-wider font-mono ${rar.badge}`}>
                            {rar.label}
                        </span>
                        {isActive && (
                            <span
                                className="text-[10px] px-1.5 py-0.5 rounded uppercase tracking-wider font-mono bg-green-500/20 text-green-400 border border-green-500/40"
                                data-testid={`mount-active-badge-${mount.slug}`}
                            >
                                Attiva
                            </span>
                        )}
                    </div>
                    <div className="text-[11px] text-zinc-500 mt-0.5">
                        Dominio: <span className="text-zinc-400">{domainLabelIt(mount.domain_slug)}</span>
                    </div>
                    <div className="text-xs text-zinc-400 mt-2 leading-relaxed">
                        {mount.description_it}
                    </div>
                    {mount.lore_it && (
                        <div className="text-[11px] text-zinc-500 mt-2 italic leading-relaxed">
                            {mount.lore_it}
                        </div>
                    )}
                    {!isOwned && (
                        <div className="mt-3 text-[11px] text-zinc-500">
                            Come ottenere:{" "}
                            <span className="text-zinc-400 font-mono">
                                {SOURCE_TYPE_LABEL_IT[mount.source_type] || mount.source_type}
                            </span>
                        </div>
                    )}
                    {isOwned && (
                        <div className="mt-3 flex flex-wrap gap-2">
                            {!isActive && (
                                <button
                                    type="button"
                                    disabled={busy}
                                    onClick={() => onActivate?.(mount.slug)}
                                    data-testid={`mount-activate-btn-${mount.slug}`}
                                    className="w-full md:w-auto text-xs font-medium px-3 py-2 rounded bg-green-600 hover:bg-green-500 text-white disabled:opacity-50 disabled:cursor-not-allowed min-h-[44px] md:min-h-0"
                                >
                                    Attiva
                                </button>
                            )}
                            {isActive && (
                                <button
                                    type="button"
                                    disabled={busy}
                                    onClick={() => onDeactivate?.()}
                                    data-testid={`mount-deactivate-btn-${mount.slug}`}
                                    className="w-full md:w-auto text-xs font-medium px-3 py-2 rounded border border-zinc-700 hover:bg-zinc-800 text-zinc-300 disabled:opacity-50 min-h-[44px] md:min-h-0"
                                >
                                    Disattiva
                                </button>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
