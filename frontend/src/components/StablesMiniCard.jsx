// ROUND 16.3 Phase 8 V1 Iter2 — dashboard mini-card for Stables.
// Compact status: active mount, count owned, quick claim/travel CTA.
// Anti-P2W micro-disclaimer at the bottom.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { mountEmoji } from "./MountCard";

export default function StablesMiniCard() {
    const [state, setState] = useState({
        loading: true,
        totalOwned: 0,
        totalCatalog: 9,
        activeMount: null,
        starterClaimed: false,
    });

    useEffect(() => {
        let cancel = false;
        (async () => {
            try {
                const [minr, cat] = await Promise.all([
                    api.get("/stables/mine").catch(() => null),
                    api.get("/stables/catalog").catch(() => null),
                ]);
                if (cancel) return;
                const mineData = minr?.data || {};
                const catData = cat?.data || {};
                const owned = mineData.owned || [];
                const starter = owned.some((m) => m.slug === "ronzino-di-strada");
                setState({
                    loading: false,
                    totalOwned: mineData.total_owned ?? owned.length,
                    totalCatalog: catData.total ?? 9,
                    activeMount: mineData.active_mount || null,
                    starterClaimed: starter,
                });
            } catch {
                if (!cancel) setState((s) => ({ ...s, loading: false }));
            }
        })();
        return () => { cancel = true; };
    }, []);

    if (state.loading) return null;

    const active = state.activeMount;

    return (
        <Link
            to="/stables"
            className="block border border-green-900/40 rounded p-4 bg-green-950/10 hover:bg-green-950/20 transition"
            data-testid="stables-mini-card"
        >
            <div className="flex items-center justify-between mb-2">
                <div className="text-sm font-semibold text-zinc-100">
                    Stalla
                    <span className="ml-2 text-[9px] px-1.5 py-0.5 rounded uppercase tracking-wider bg-green-500/15 text-green-400 border border-green-500/40 font-mono">
                        NEW
                    </span>
                </div>
                <div className="text-[10px] uppercase tracking-wide text-green-400/70">Vai →</div>
            </div>
            <div className="flex items-baseline gap-3">
                <div className="text-2xl leading-none" aria-hidden>
                    {active ? mountEmoji(active.slug) : "🥾"}
                </div>
                <div className="flex-1 min-w-0">
                    {active ? (
                        <div className="text-sm text-green-300 truncate" data-testid="stables-mini-active">
                            {active.name_it}
                        </div>
                    ) : (
                        <div className="text-sm text-zinc-500">
                            {state.starterClaimed
                                ? "Nessuna cavalcatura attiva"
                                : "Rivendica il tuo primo cavallo"}
                        </div>
                    )}
                    <div className="text-[11px] text-zinc-500 mt-0.5 font-mono">
                        {state.totalOwned}/{state.totalCatalog} sbloccate
                    </div>
                </div>
            </div>
            <div className="text-[10px] text-emerald-500/70 mt-2 italic"
                 data-testid="stables-mini-antip2w">
                Solo cosmetico · nessun bonus di gioco
            </div>
        </Link>
    );
}
