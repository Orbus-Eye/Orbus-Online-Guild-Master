// ROUND 16.3 Phase 8 V1 Iter2 — narrative route card for /stables.
// Cosmetic reward only (badge/title/lore) — enforced by backend catalog.

import { domainLabelIt } from "./MountCard";

const REWARD_TYPE_LABEL_IT = {
    cosmetic_badge: "Distintivo cosmetico",
    cosmetic_title: "Titolo onorifico",
    lore_entry: "Voce di lore",
};

export default function NarrativeRouteCard({ route, onTravel, busy }) {
    const completed = Boolean(route.is_completed);
    const canTravel = Boolean(route.can_travel);
    const domains = Array.isArray(route.required_mount_domains)
        ? route.required_mount_domains
        : [];
    const domainsIt = domains.map(domainLabelIt).join(", ");

    let statusPill = null;
    if (completed) {
        statusPill = (
            <span
                className="text-[10px] px-1.5 py-0.5 rounded uppercase tracking-wider font-mono bg-zinc-800/60 text-zinc-400 border border-zinc-700"
                data-testid={`route-status-${route.slug}`}
            >
                ✓ Completata
            </span>
        );
    } else if (canTravel) {
        statusPill = (
            <span
                className="text-[10px] px-1.5 py-0.5 rounded uppercase tracking-wider font-mono bg-green-500/15 text-green-400 border border-green-500/40"
                data-testid={`route-status-${route.slug}`}
            >
                Percorribile
            </span>
        );
    } else {
        statusPill = (
            <span
                className="text-[10px] px-1.5 py-0.5 rounded uppercase tracking-wider font-mono bg-red-950/40 text-red-400 border border-red-800/60"
                data-testid={`route-status-${route.slug}`}
            >
                Cavalcatura mancante
            </span>
        );
    }

    return (
        <div
            data-testid={`route-card-${route.slug}`}
            className={`rounded-lg p-4 bg-zinc-900/50 border ${completed
                ? "border-zinc-700/50 opacity-70"
                : canTravel
                    ? "border-green-800/50"
                    : "border-zinc-800/60"}`}
        >
            <div className="flex items-start justify-between gap-2 flex-wrap">
                <div className="text-sm font-semibold text-zinc-100" data-testid={`route-name-${route.slug}`}>
                    {route.name_it}
                </div>
                {statusPill}
            </div>
            <div className="text-[11px] text-zinc-500 mt-1">
                Richiede: <span className="text-zinc-400">{domainsIt || "—"}</span>
            </div>
            <div className="text-xs text-zinc-400 mt-2 leading-relaxed">
                {route.description_it}
            </div>
            {route.lore_it && (
                <div className="text-[11px] text-zinc-500 mt-2 italic leading-relaxed">
                    {route.lore_it}
                </div>
            )}
            <div className="mt-3 flex flex-col md:flex-row md:items-center md:justify-between gap-2">
                <div className="text-[11px] text-zinc-500">
                    Ricompensa:{" "}
                    <span className="text-emerald-400 font-mono">
                        {REWARD_TYPE_LABEL_IT[route.reward_type] || route.reward_type}
                    </span>
                    {route.reward_name_it && (
                        <> · <span className="text-zinc-300">{route.reward_name_it}</span></>
                    )}
                </div>
                {canTravel && !completed && (
                    <button
                        type="button"
                        disabled={busy}
                        onClick={() => onTravel?.(route.slug)}
                        data-testid={`route-travel-btn-${route.slug}`}
                        className="w-full md:w-auto text-xs font-medium px-3 py-2 rounded bg-green-600 hover:bg-green-500 text-white disabled:opacity-50 disabled:cursor-not-allowed min-h-[44px] md:min-h-0"
                    >
                        Cavalca la Rotta
                    </button>
                )}
                {!canTravel && !completed && route.missing_reason && (
                    <div className="text-[10px] text-red-400 md:max-w-[50%] md:text-right">
                        {route.missing_reason}
                    </div>
                )}
            </div>
        </div>
    );
}
