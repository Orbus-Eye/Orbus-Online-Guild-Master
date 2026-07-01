// ROUND 16.3 Phase 6 Iter2 — Specialization Dashboard mini card.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";

export default function SpecializationMiniCard() {
    const [state, setState] = useState({
        loading: true, hasActive: false, name: null,
        canChoose: false, guildLevel: null,
    });

    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const r = await api.get("/guild-specialization/mine");
                if (cancelled) return;
                setState({
                    loading: false,
                    hasActive: !!r.data.active_choice,
                    name: r.data.specialization?.name_it || null,
                    canChoose: !!r.data.can_choose,
                    guildLevel: r.data.guild_level,
                });
            } catch {
                if (!cancelled) setState((s) => ({ ...s, loading: false }));
            }
        })();
        return () => { cancelled = true; };
    }, []);

    if (state.loading) return null;

    if (state.hasActive) {
        return (
            <Link to="/guild-specialization"
                  className="block border border-violet-500/40 rounded p-4 bg-slate-900/40 hover:bg-slate-900/60 transition"
                  data-testid="spec-mini-card-active">
                <div className="flex items-center justify-between mb-2 gap-2">
                    <div className="text-sm font-semibold text-violet-300">
                        Specializzazione
                    </div>
                    <div className="text-xs text-slate-500">→</div>
                </div>
                <div className="text-xs text-slate-300"
                     data-testid="spec-mini-card-name">
                    {state.name}
                </div>
            </Link>
        );
    }

    if (state.canChoose) {
        return (
            <Link to="/guild-specialization"
                  className="block border border-violet-500/50 rounded p-4 bg-violet-950/20 hover:bg-violet-950/30 transition"
                  data-testid="spec-mini-card-choose">
                <div className="text-sm font-semibold text-violet-300 mb-1">
                    Scegli la tua specializzazione
                </div>
                <div className="text-xs text-slate-400">
                    6 archetipi disponibili. Prima scelta gratuita.
                </div>
            </Link>
        );
    }

    return (
        <div className="border border-slate-800 rounded p-4 bg-slate-950/40"
             data-testid="spec-mini-card-locked">
            <div className="text-sm font-semibold text-slate-300 mb-1">
                Specializzazione Gilda
            </div>
            <div className="text-xs text-slate-500">
                Sblocca a Livello Gilda 8
                {state.guildLevel != null && ` (attualmente lvl ${state.guildLevel})`}
            </div>
        </div>
    );
}
