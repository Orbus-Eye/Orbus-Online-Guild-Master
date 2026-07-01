// ROUND 16.3 Phase 2 — Small dashboard card for Mondo (World).
// Best-effort: renders a compact box that adapts to gate/no-continent/with-continent.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";

export default function WorldMiniCard() {
    const [state, setState] = useState({ loading: true, data: null });

    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const { data } = await api.get("/world/overview");
                if (!cancelled) setState({ loading: false, data });
            } catch {
                if (!cancelled) setState({ loading: false, data: null });
            }
        })();
        return () => { cancelled = true; };
    }, []);

    if (state.loading) return null;
    if (!state.data) return null;

    return (
        <Link
            to="/world"
            data-testid="dashboard-world-card"
            className="block border border-border bg-card rounded-sm p-4 hover:border-amber/40 transition-colors group"
        >
            <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] text-amber tracking-widest font-bold">
                    :: MONDO
                </span>
                <span className="text-[10px] text-amber group-hover:translate-x-0.5 transition-transform">
                    →
                </span>
            </div>
            {state.data.access === false ? (
                <div className="text-sm text-muted-foreground">
                    Completa il primo raid per accedere al Mondo di Orbus.
                </div>
            ) : state.data.continent ? (
                <div>
                    <div className="text-sm text-foreground">
                        Ancorata a{" "}
                        <span data-testid="dashboard-world-continent"
                              className="text-amber">
                            {state.data.continent.name_it}
                        </span>
                    </div>
                    <div className="text-[10px] text-muted-foreground mt-1">
                        {state.data.continent.domain_it} ·{" "}
                        {state.data.guilds_in_continent_count ?? 0} gilde nel continente
                    </div>
                </div>
            ) : (
                <div>
                    <div className="text-sm text-foreground">
                        Scegli il tuo continente
                    </div>
                    <div className="text-[10px] text-muted-foreground mt-1">
                        8 mastocontinenti disponibili. Nessun bonus di gioco.
                    </div>
                </div>
            )}
        </Link>
    );
}
