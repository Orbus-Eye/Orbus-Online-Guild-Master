// ROUND 16.3 Phase 6 Iter2 — Specialization Catalog (read-only 6 archetypes).
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import AppHeader from "../components/AppHeader";

const BADGE_CLASSES = {
    amber: "border-amber-500/50 text-amber-300 bg-amber-950/20",
    orange: "border-orange-500/50 text-orange-300 bg-orange-950/20",
    emerald: "border-emerald-500/50 text-emerald-300 bg-emerald-950/20",
    sky: "border-sky-500/50 text-sky-300 bg-sky-950/20",
    red: "border-red-500/50 text-red-300 bg-red-950/20",
    violet: "border-violet-500/50 text-violet-300 bg-violet-950/20",
};

export default function GuildSpecializationCatalog() {
    const [state, setState] = useState({ loading: true, catalog: [] });

    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const r = await api.get("/guild-specialization/catalog");
                if (!cancelled) setState({
                    loading: false,
                    catalog: r.data.specializations || [],
                });
            } catch {
                if (!cancelled) setState({ loading: false, catalog: [] });
            }
        })();
        return () => { cancelled = true; };
    }, []);

    return (
        <div className="min-h-screen bg-background text-foreground overflow-x-hidden">
            <AppHeader />
            <main className="max-w-4xl mx-auto px-4 py-6 pb-32 md:pb-8 font-mono"
                data-testid="spec-catalog-page">
                <Link to="/guild-specialization"
                      className="text-sm text-violet-300 hover:text-violet-200 inline-block mb-4"
                      data-testid="spec-catalog-back">
                    ← Torna alla Specializzazione
                </Link>

                <h1 className="text-2xl md:text-3xl font-bold text-violet-300 mb-2">
                    Archetipi Disponibili
                </h1>
                <p className="text-sm text-slate-400 mb-6">
                    6 archetipi con caratteristiche uniche.
                    Gli hooks di categoria saranno consumati da Phase 6.5+.
                </p>

                {state.loading && (
                    <div className="text-center text-muted-foreground py-8">Caricamento…</div>
                )}

                {!state.loading && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3"
                         data-testid="spec-catalog-grid">
                        {state.catalog.map((s) => (
                            <div key={s.slug}
                                 className={`border rounded p-4 ${BADGE_CLASSES[s.badge_color] || "border-slate-700 bg-slate-900/40"}`}
                                 data-testid={`spec-catalog-card-${s.slug}`}>
                                <div className="font-semibold text-slate-100 mb-1">
                                    {s.name_it}
                                </div>
                                <div className="text-xs text-slate-400 mb-3 leading-relaxed">
                                    {s.description_it}
                                </div>
                                <div className="flex flex-wrap gap-1">
                                    {(s.hook_categories || []).map((h) => (
                                        <span key={h}
                                              className="text-[10px] uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                                            {h}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
}
