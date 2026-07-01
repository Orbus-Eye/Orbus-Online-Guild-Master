// ROUND 16.3 Phase 3 — World events page (evento attivo continente).
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, formatApiError } from "../lib/api";
import AppHeader from "../components/AppHeader";

function fmtRel(iso) {
    if (!iso) return "—";
    const ms = new Date(iso).getTime() - Date.now();
    if (ms <= 0) return "in scadenza";
    const h = Math.floor(ms / 3600000);
    if (h < 48) return `${h}h`;
    return `${Math.floor(h / 24)}g`;
}

function ModifierBadge({ cat }) {
    if (!cat || !cat.modifier_type) return null;
    const v = cat.modifier_value || 0;
    if (cat.modifier_type === "site_income_pct") {
        const cls = v > 0
            ? "text-green-400 border-green-500/40"
            : v < 0 ? "text-red-400 border-red-500/40"
            : "text-muted-foreground border-border/60";
        return (
            <span data-testid="world-event-modifier"
                  className={`text-[11px] px-2 py-1 border ${cls} rounded-sm`}>
                {v > 0 ? "+" : ""}{v}% entrate passive sedi
            </span>
        );
    }
    if (cat.modifier_type === "mission_risk_pct") {
        return (
            <span data-testid="world-event-modifier"
                  className="text-[11px] px-2 py-1 border border-amber/40 text-amber rounded-sm">
                +{v}% rischio missione (in arrivo)
            </span>
        );
    }
    return null;
}

export default function WorldEvents() {
    const [state, setState] = useState({ loading: true, data: null, err: null });

    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const { data } = await api.get("/world-events/mine");
                if (!cancelled) setState({ loading: false, data, err: null });
            } catch (err) {
                const status = err?.response?.status;
                if (!cancelled) setState({
                    loading: false, data: null,
                    err: status === 403
                        ? "Completa il tuo primo raid per accedere agli eventi del Mondo."
                        : status === 409
                            ? "Devi prima ancorare la tua gilda a un continente."
                            : formatApiError(err),
                });
            }
        })();
        return () => { cancelled = true; };
    }, []);

    return (
        <div className="min-h-screen bg-background text-foreground overflow-x-hidden">
            <AppHeader />
            <main className="max-w-3xl mx-auto px-4 py-6 pb-32 md:pb-8 font-mono">
                <div className="mb-4">
                    <Link to="/world"
                          data-testid="world-events-back"
                          className="text-[11px] text-muted-foreground hover:text-amber tracking-widest">
                        ← Torna al Mondo
                    </Link>
                </div>
                <header className="mb-4">
                    <h1 data-testid="world-events-title"
                        className="text-amber text-xl tracking-widest">
                        :: Eventi Continentali
                    </h1>
                    <p className="text-[11px] text-muted-foreground mt-1">
                        Cambiamenti stagionali e occasioni che influenzano il tuo continente.
                    </p>
                </header>

                {state.loading && (
                    <div data-testid="world-events-loading"
                         className="text-[11px] text-muted-foreground italic">
                        :: Caricamento...
                    </div>
                )}

                {!state.loading && state.err && (
                    <div data-testid="world-events-blocked"
                         className="border border-amber/40 bg-amber/5 rounded-sm p-4">
                        <p className="text-[12px] text-amber mb-3">{state.err}</p>
                        <Link to="/world"
                              className="inline-flex items-center w-full md:w-auto justify-center text-[11px] tracking-widest px-4 py-2.5 min-h-[44px] border border-amber text-amber rounded-sm hover:bg-amber/10 font-bold">
                            Vai al Mondo →
                        </Link>
                    </div>
                )}

                {!state.loading && state.data && !state.data.active && (
                    <div data-testid="world-events-none"
                         className="border border-border/60 bg-card/40 rounded-sm p-4 text-[12px] text-muted-foreground">
                        Nessun evento attivo nel tuo continente
                        <span className="text-foreground/80">
                            {" "}({state.data.continent_slug}).
                        </span>
                    </div>
                )}

                {!state.loading && state.data?.active && (
                    <section data-testid="world-events-active"
                             className="border border-amber/40 bg-card/40 rounded-sm p-4">
                        <div className="flex items-baseline justify-between gap-2 mb-2 flex-wrap">
                            <h2 data-testid="world-events-active-name"
                                className="text-amber text-[14px] tracking-wide">
                                {state.data.active.catalog?.name_it}
                            </h2>
                            <span className="text-[10px] text-muted-foreground uppercase">
                                {state.data.active.catalog?.category}
                            </span>
                        </div>
                        <p className="text-[12px] text-muted-foreground leading-relaxed mb-3">
                            {state.data.active.catalog?.description_it}
                        </p>
                        <div className="mb-3">
                            <ModifierBadge cat={state.data.active.catalog} />
                        </div>
                        <div className="grid grid-cols-2 gap-3 text-[11px]">
                            <div>
                                <div className="text-muted-foreground">Continente</div>
                                <div className="text-foreground">
                                    {state.data.continent_slug}
                                </div>
                            </div>
                            <div>
                                <div className="text-muted-foreground">Termine tra</div>
                                <div data-testid="world-events-remaining"
                                     className="text-foreground">
                                    {fmtRel(state.data.active.instance?.ends_at)}
                                </div>
                            </div>
                        </div>
                    </section>
                )}
            </main>
        </div>
    );
}
