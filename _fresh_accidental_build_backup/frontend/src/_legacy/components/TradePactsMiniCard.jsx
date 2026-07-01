// ROUND 16.3 Phase 6 Iter2 — Trade Pacts Dashboard mini card.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";

export default function TradePactsMiniCard() {
    const [state, setState] = useState({
        loading: true, active: 0, incoming: 0, max: 3,
    });

    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const [mine, received] = await Promise.all([
                    api.get("/trade-pacts/mine").catch(() => ({ data: {} })),
                    api.get("/trade-pacts/received").catch(() => ({ data: {} })),
                ]);
                if (cancelled) return;
                const activePacts = (mine.data.pacts || []).filter(
                    (p) => p.status === "accepted");
                setState({
                    loading: false,
                    active: activePacts.length,
                    incoming: (received.data.pacts || []).length,
                    max: mine.data.max_accepted || 3,
                });
            } catch {
                if (!cancelled) setState((s) => ({ ...s, loading: false }));
            }
        })();
        return () => { cancelled = true; };
    }, []);

    if (state.loading) return null;

    return (
        <Link to="/trade-pacts"
              className="block border border-emerald-500/40 rounded p-4 bg-slate-900/40 hover:bg-slate-900/60 transition"
              data-testid="trade-pacts-mini-card">
            <div className="flex items-center justify-between mb-2 gap-2">
                <div className="text-sm font-semibold text-emerald-300">
                    Patti Commerciali
                </div>
                <div className="text-xs text-slate-500">→</div>
            </div>
            <div className="flex flex-wrap gap-3 text-xs">
                <span className="text-slate-300"
                      data-testid="trade-pacts-mini-active">
                    {state.active}/{state.max} attivi
                </span>
                {state.incoming > 0 && (
                    <span className="text-sky-300"
                          data-testid="trade-pacts-mini-incoming">
                        {state.incoming} in arrivo
                    </span>
                )}
            </div>
        </Link>
    );
}
