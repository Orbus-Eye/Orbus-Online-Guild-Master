// ROUND 16.3 Phase 5B Iter2 — Arfus Dashboard mini card.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";

export default function ArfusMiniCard() {
    const [state, setState] = useState({
        loading: true, access: false, guildLevel: null,
        activeCount: 0, maxActive: 5, inProgress: 0,
    });

    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const cat = await api.get("/arfus-forge/catalog");
                if (cancelled) return;
                if (!cat.data.access) {
                    setState((s) => ({
                        ...s, loading: false, access: false,
                        guildLevel: cat.data.guild_level,
                    }));
                    return;
                }
                const research = await api.get("/arfus-forge/research/mine")
                    .catch(() => ({ data: {} }));
                if (cancelled) return;
                setState({
                    loading: false, access: true,
                    guildLevel: cat.data.guild_level,
                    activeCount: cat.data.active_count || 0,
                    maxActive: cat.data.max_active_techs || 5,
                    inProgress: (research.data.in_progress || []).length,
                });
            } catch {
                if (!cancelled) setState((s) => ({ ...s, loading: false }));
            }
        })();
        return () => { cancelled = true; };
    }, []);

    if (state.loading) return null;

    if (!state.access) {
        return (
            <div className="border border-slate-800 rounded p-4 bg-slate-950/40"
                 data-testid="arfus-mini-card-locked">
                <div className="text-sm font-semibold text-slate-300 mb-1">
                    Forgia di Arfus
                </div>
                <div className="text-xs text-slate-500">
                    Sblocca a Livello Gilda 6
                    {state.guildLevel != null && ` (attualmente lvl ${state.guildLevel})`}
                </div>
            </div>
        );
    }

    return (
        <Link to="/arfus-forge"
              className="block border border-amber-500/40 rounded p-4 bg-slate-900/40 hover:bg-slate-900/60 transition"
              data-testid="arfus-mini-card">
            <div className="flex items-center justify-between mb-2 gap-2">
                <div className="text-sm font-semibold text-amber-300">
                    Forgia di Arfus
                </div>
                <div className="text-xs text-slate-500">→</div>
            </div>
            <div className="flex flex-wrap gap-3 text-xs">
                <span className="text-slate-300"
                      data-testid="arfus-mini-slots">
                    {state.activeCount}/{state.maxActive} slot attivi
                </span>
                {state.inProgress > 0 && (
                    <span className="text-sky-300"
                          data-testid="arfus-mini-inprogress">
                        {state.inProgress} ricerca{state.inProgress > 1 ? "e" : ""} in corso
                    </span>
                )}
            </div>
        </Link>
    );
}
