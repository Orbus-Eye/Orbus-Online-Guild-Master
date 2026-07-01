// ROUND 16.3 Phase 5A — Legendary Forge hub.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { api, formatApiError } from "../lib/api";
import AppHeader from "../components/AppHeader";

const QUALITY_TAG = {
    perfezionato: "text-amber-300 border-amber-500/60",
    normale: "text-slate-300 border-slate-500/60",
    imperfetto: "text-orange-300 border-orange-500/60",
};

export default function LegendaryForge() {
    const [state, setState] = useState({ loading: true, access: false,
        recipes: [], guildLevel: null, err: null });

    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const r = await api.get("/legendary-forge/catalog");
                if (!cancelled) setState({
                    loading: false,
                    access: r.data.access,
                    recipes: r.data.recipes || [],
                    guildLevel: r.data.guild_level,
                    err: null,
                });
            } catch (err) {
                if (!cancelled) {
                    const msg = formatApiError(err);
                    toast.error(msg);
                    setState({ loading: false, access: false, recipes: [],
                        guildLevel: null, err: msg });
                }
            }
        })();
        return () => { cancelled = true; };
    }, []);

    return (
        <div className="min-h-screen bg-background text-foreground overflow-x-hidden">
            <AppHeader />
            <main className="max-w-4xl mx-auto px-4 py-6 pb-32 md:pb-8 font-mono"
                data-testid="legendary-forge-page">
                <div className="mb-6">
                    <h1 className="text-3xl md:text-4xl font-bold text-amber-300 mb-2"
                        data-testid="legendary-forge-title">
                        Forgia Leggendaria
                    </h1>
                    <p className="text-sm text-muted-foreground">
                        Crea oggetti leggendari — BOP (Bound On Pickup), non commerciabili.
                    </p>
                </div>

                {state.loading && (
                    <div className="text-center text-muted-foreground py-16"
                        data-testid="legendary-forge-loading">Caricamento…</div>
                )}

                {!state.loading && !state.access && (
                    <div className="border border-amber-500/40 rounded-lg p-8
                        text-center bg-amber-950/20"
                        data-testid="legendary-forge-locked">
                        <div className="text-6xl mb-4 opacity-40 select-none">⚒</div>
                        <h2 className="text-xl font-bold text-amber-300 mb-2">
                            Forgia Bloccata
                        </h2>
                        <p className="text-sm text-muted-foreground mb-6">
                            Raggiungi <span className="text-amber-300 font-bold">
                                Livello Gilda 5</span> per accedere alla Forgia Leggendaria.
                        </p>
                        <Link to="/expeditions"
                            className="inline-block w-full md:w-auto px-6 py-3
                                min-h-[44px] bg-primary text-primary-foreground
                                rounded-md hover:opacity-90"
                            data-testid="legendary-forge-cta-missions">
                            Vai alle Spedizioni
                        </Link>
                    </div>
                )}

                {!state.loading && state.access && (
                    <>
                        <div className="mb-4 text-xs text-muted-foreground">
                            Livello Gilda: <span className="text-amber-300 font-bold">
                                {state.guildLevel}</span>
                        </div>
                        <div className="mb-6 flex flex-wrap gap-2">
                            <Link to="/legendary-forge/orders"
                                className="px-4 py-2 min-h-[44px] border border-slate-600
                                    rounded-md hover:bg-slate-800/50 text-sm"
                                data-testid="legendary-forge-orders-link">
                                📜 I miei ordini
                            </Link>
                        </div>
                        <div className="grid md:grid-cols-2 gap-4">
                            {state.recipes.map((r) => {
                                return (
                                    <Link key={r.slug}
                                        to={`/legendary-forge/recipe/${r.slug}`}
                                        className="border border-amber-500/40 rounded-lg
                                            p-4 hover:border-amber-500 transition
                                            bg-slate-900/50"
                                        data-testid={`recipe-card-${r.slug}`}>
                                        <div className="flex items-start justify-between mb-2">
                                            <h3 className="text-lg font-bold text-amber-300">
                                                {r.name_it}
                                            </h3>
                                            <span className="text-xs px-2 py-0.5 border
                                                border-amber-500/60 text-amber-300 rounded">
                                                Lv.{r.guild_level_required}+
                                            </span>
                                        </div>
                                        <div className="text-xs text-muted-foreground mb-3">
                                            Output: {r.output_slug}
                                        </div>
                                        <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                                            <div>
                                                <div className="text-muted-foreground">Successo</div>
                                                <div className="text-green-400 font-bold">
                                                    {r.computed_success_chance}%
                                                </div>
                                            </div>
                                            <div>
                                                <div className="text-muted-foreground">Oro</div>
                                                <div className="text-yellow-300 font-bold">
                                                    {r.gold.toLocaleString()}
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex gap-2 text-[10px] flex-wrap">
                                            <span className={`px-2 py-0.5 rounded border ${QUALITY_TAG.perfezionato}`}>
                                                Perfezionato {r.perfezionato_chance}%
                                            </span>
                                            <span className={`px-2 py-0.5 rounded border ${QUALITY_TAG.normale}`}>
                                                Normale {r.normale_chance}%
                                            </span>
                                            <span className={`px-2 py-0.5 rounded border ${QUALITY_TAG.imperfetto}`}>
                                                Imperfetto {r.imperfetto_chance}%
                                            </span>
                                        </div>
                                    </Link>
                                );
                            })}
                        </div>
                    </>
                )}
            </main>
        </div>
    );
}
