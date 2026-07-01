// ROUND 16.3 Phase 5A — Dashboard mini card for Legendary Forge.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";

export default function LegendaryForgeMiniCard() {
    const [state, setState] = useState({ loading: true, access: false,
        inProgress: 0, nextCompletion: null });

    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const cat = await api.get("/legendary-forge/catalog");
                if (cancelled) return;
                if (!cat.data.access) {
                    setState({ loading: false, access: false, inProgress: 0,
                        nextCompletion: null });
                    return;
                }
                const ord = await api.get("/legendary-forge/orders/mine")
                    .catch(() => ({ data: { in_progress: [] } }));
                if (cancelled) return;
                const ip = ord.data.in_progress || [];
                const next = ip.length > 0
                    ? ip.reduce((min, o) =>
                        !min || o.completes_at < min ? o.completes_at : min, null)
                    : null;
                setState({ loading: false, access: true,
                    inProgress: ip.length, nextCompletion: next });
            } catch {
                if (!cancelled) setState({ loading: false, access: false,
                    inProgress: 0, nextCompletion: null });
            }
        })();
        return () => { cancelled = true; };
    }, []);

    if (state.loading) return null;

    if (!state.access) {
        return (
            <div className="border border-slate-700 rounded-lg p-4 bg-slate-900/30"
                data-testid="legendary-mini-locked">
                <div className="flex items-center justify-between mb-1">
                    <div className="text-sm font-bold text-slate-300">⚒ Forgia Leggendaria</div>
                    <span className="text-[10px] px-2 py-0.5 border border-slate-600
                        text-slate-400 rounded">BLOCCATA</span>
                </div>
                <div className="text-xs text-muted-foreground">
                    Sblocca a <span className="text-amber-300 font-bold">Livello Gilda 5</span>.
                </div>
            </div>
        );
    }

    return (
        <Link to="/legendary-forge"
            className="block border border-amber-500/40 rounded-lg p-4
                bg-amber-950/10 hover:bg-amber-950/20 transition"
            data-testid="legendary-mini-card">
            <div className="flex items-center justify-between mb-2">
                <div className="text-sm font-bold text-amber-300">⚒ Forgia Leggendaria</div>
                <span className="text-[10px] px-2 py-0.5 border border-amber-500/60
                    text-amber-300 rounded">NEW</span>
            </div>
            <div className="text-xs text-muted-foreground mb-1">
                {state.inProgress > 0
                    ? <>{state.inProgress} ordine{state.inProgress !== 1 ? "i" : ""} in corso</>
                    : "Nessun ordine attivo"}
            </div>
            {state.nextCompletion && (
                <div className="text-[10px] text-amber-200">
                    Prossimo: {new Date(state.nextCompletion).toLocaleString("it-IT")}
                </div>
            )}
        </Link>
    );
}
