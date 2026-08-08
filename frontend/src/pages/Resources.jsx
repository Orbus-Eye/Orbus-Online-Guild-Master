// ROUND 16.3 Phase 4 — Continent Resources overview.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, formatApiError } from "../lib/api";
import AppHeader from "../components/AppHeader";

const RARITY_CLS = {
    epic: "border-purple-500/60 text-purple-300",
    rare: "border-blue-500/60 text-blue-300",
};

export default function Resources() {
    const [state, setState] = useState({ loading: true, catalog: [], mine: null, err: null, stats: null });

    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const [c, m, s] = await Promise.all([
                    api.get("/resources/catalog"),
                    api.get("/resources/mine").catch((e) => ({ data: null, err: e })),
                    api.get("/resources/missions/stats").catch(() => ({ data: null })),
                ]);
                if (!cancelled) {
                    setState({
                        loading: false,
                        catalog: c.data.resources || [],
                        mine: m.data,
                        err: m.err ? formatApiError(m.err) : null,
                        stats: s.data || null,
                    });
                }
            } catch (err) {
                if (!cancelled) setState({ loading: false, catalog: [], mine: null,
                                          err: formatApiError(err), stats: null });
            }
        })();
        return () => { cancelled = true; };
    }, []);

    const currentSlug = state.mine?.current_continent;
    const invByItem = Object.fromEntries(
        (state.mine?.inventory || []).map((r) => [r.slug, r.quantity]),
    );
    const st = state.stats;

    return (
        <div className="min-h-screen bg-background text-foreground overflow-x-hidden">
            <AppHeader />
            <main className="max-w-4xl mx-auto px-4 py-6 pb-32 md:pb-8 font-mono">
                <div className="mb-4">
                    <Link to="/world" data-testid="resources-back"
                          className="text-[11px] text-muted-foreground hover:text-amber tracking-widest">
                        ← Torna al Mondo
                    </Link>
                </div>
                <header className="mb-5">
                    <h1 data-testid="resources-title"
                        className="text-amber text-xl tracking-widest">
                        :: Risorse Continentali
                    </h1>
                    <p className="text-[11px] text-muted-foreground mt-1">
                        Otto risorse rare, una per continente. Trovabili solo nel loro dominio d&apos;origine.
                    </p>
                </header>

                {state.loading && (
                    <div className="text-[11px] text-muted-foreground italic">
                        :: Caricamento...
                    </div>
                )}

                {!state.loading && state.err && (
                    <div data-testid="resources-blocked"
                         className="border border-amber/40 bg-amber/5 rounded-sm p-4 mb-4">
                        <p className="text-[12px] text-amber">{state.err}</p>
                    </div>
                )}

                {/* ROUND 17.2 P0.3 — Daily stats + gate banner */}
                {!state.loading && st && (
                    <div
                        data-testid="resources-daily-stats"
                        className="border border-border/60 bg-card/40 rounded-sm p-3 mb-4 text-[11px]"
                    >
                        {!st.gate_passed ? (
                            <p data-testid="resources-gate-warning" className="text-amber">
                                🔒 Richiede Livello di Gilda {st.min_guild_level}. Sei attualmente Lv {st.current_guild_level}.
                                Guadagna XP Gilda completando spedizioni.
                            </p>
                        ) : (
                            <div className="flex flex-wrap gap-x-6 gap-y-1 text-muted-foreground">
                                <span>
                                    Missioni oggi:{" "}
                                    <strong data-testid="resources-daily-used" className="text-foreground">
                                        {st.daily_used}/{st.daily_cap}
                                    </strong>
                                </span>
                                <span>Durata missione: <strong className="text-foreground">
                                    {Math.round((st.mission_duration_seconds || 780) / 60)} min
                                </strong></span>
                                <span>XP Gilda: <strong className="text-amber">
                                    +{st.prestige_reward_rare}
                                </strong>/<strong className="text-amber">+{st.prestige_reward_epic}
                                </strong> (rara/epica)</span>
                                {st.continents_used_today?.length > 0 && (
                                    <span data-testid="resources-continents-used">
                                        Continenti già raccolti oggi:{" "}
                                        <strong className="text-foreground">
                                            {st.continents_used_today.join(", ")}
                                        </strong>
                                    </span>
                                )}
                            </div>
                        )}
                    </div>
                )}

                {!state.loading && (
                    <div className="mb-4 flex gap-2 flex-wrap">
                        <Link to="/world/resource-gather"
                              data-testid="resources-cta-gather"
                              className="text-[11px] tracking-widest px-4 py-2.5 min-h-[44px] inline-flex items-center border border-amber text-amber rounded-sm hover:bg-amber/10 font-bold w-full md:w-auto justify-center">
                            Cerca risorsa →
                        </Link>
                        <Link to="/world/resource-missions"
                              data-testid="resources-cta-missions"
                              className="text-[11px] tracking-widest px-4 py-2.5 min-h-[44px] inline-flex items-center border border-border/60 text-foreground/80 hover:border-amber/60 rounded-sm w-full md:w-auto justify-center">
                            Missioni in corso →
                        </Link>
                    </div>
                )}

                {!state.loading && (
                    <div className="grid gap-3 md:grid-cols-2">
                        {state.catalog.map((r) => {
                            const owned = invByItem[r.slug] || 0;
                            const isMine = r.continent_slug === currentSlug;
                            return (
                                <div key={r.slug}
                                     data-testid={`resource-tile-${r.slug}`}
                                     className={`border rounded-sm p-4 ${isMine
                                         ? "border-amber/40 bg-card/60"
                                         : "border-border/40 bg-card/20 opacity-70"}`}>
                                    <div className="flex items-baseline justify-between gap-2 mb-2">
                                        <h3 className="text-[13px] text-amber tracking-wide">
                                            {r.name_it}
                                        </h3>
                                        <span className={`text-[10px] px-2 py-0.5 border rounded-sm ${RARITY_CLS[r.rarity] || "border-border/40"}`}>
                                            {r.rarity}
                                        </span>
                                    </div>
                                    <p className="text-[11px] text-muted-foreground mb-3 leading-relaxed">
                                        {r.description_it}
                                    </p>
                                    <div className="flex items-center justify-between text-[11px]">
                                        <span className="text-muted-foreground">
                                            Continente: <span className="text-foreground">{r.continent_slug}</span>
                                        </span>
                                        <span data-testid={`resource-qty-${r.slug}`}
                                              className={owned > 0 ? "text-amber" : "text-muted-foreground"}>
                                            {owned}× posseduto
                                        </span>
                                    </div>
                                    {!isMine && (
                                        <div className="text-[10px] text-muted-foreground italic mt-2">
                                            Trovabile solo in {r.continent_slug}.
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                )}
            </main>
        </div>
    );
}
