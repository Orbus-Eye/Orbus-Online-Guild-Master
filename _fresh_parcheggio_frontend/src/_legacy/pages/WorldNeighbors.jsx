// ROUND 16.3 Phase 2 — World neighbors list (mobile-first).
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { api, formatApiError } from "../lib/api";
import AppHeader from "../components/AppHeader";

const ACTIVITY_LABEL = {
    attiva_oggi: { text: "attiva oggi", cls: "text-green-400 border-green-500/40" },
    attiva_settimana: { text: "questa settimana", cls: "text-amber border-amber/40" },
    attiva_mese: { text: "questo mese", cls: "text-muted-foreground border-border/60" },
    inattiva: { text: "inattiva", cls: "text-red-400/70 border-red-500/30" },
    inactive: { text: "inattiva", cls: "text-red-400/70 border-red-500/30" },
};

export default function WorldNeighbors() {
    const [state, setState] = useState({ loading: true, data: null, error: null });

    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const { data } = await api.get("/world/neighbors");
                if (!cancelled) setState({ loading: false, data, error: null });
            } catch (err) {
                const status = err?.response?.status;
                if (!cancelled) {
                    setState({
                        loading: false, data: null,
                        error: status === 409
                            ? "Devi prima ancorare la tua gilda a un continente."
                            : status === 403
                                ? "Completa il tuo primo raid per accedere al Mondo."
                                : formatApiError(err),
                    });
                    if (status !== 409 && status !== 403) toast.error(formatApiError(err));
                }
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
                          data-testid="world-neighbors-back"
                          className="text-[11px] text-muted-foreground hover:text-amber tracking-widest">
                        ← Torna al Mondo
                    </Link>
                </div>

                <header className="mb-4">
                    <h1 data-testid="world-neighbors-title"
                        className="text-amber text-xl tracking-widest">
                        :: Gilde vicine
                    </h1>
                    <p className="text-[11px] text-muted-foreground mt-1">
                        Fino a 8 gilde nel tuo stesso continente. Solo dati di
                        appartenenza — nessun ranking competitivo.
                    </p>
                </header>

                {state.loading && (
                    <div data-testid="world-neighbors-loading"
                         className="text-[11px] text-muted-foreground italic">
                        :: Caricamento...
                    </div>
                )}

                {!state.loading && state.error && (
                    <div data-testid="world-neighbors-blocked"
                         className="border border-amber/40 bg-amber/5 rounded-sm p-4">
                        <p className="text-[12px] text-amber mb-3">{state.error}</p>
                        <Link to="/world"
                              data-testid="world-neighbors-cta"
                              className="inline-flex items-center w-full md:w-auto justify-center text-[11px] tracking-widest px-4 py-2.5 min-h-[44px] border border-amber text-amber rounded-sm hover:bg-amber/10 font-bold">
                            Vai al Mondo →
                        </Link>
                    </div>
                )}

                {!state.loading && state.data && (
                    <>
                        <div className="text-[11px] text-muted-foreground mb-4">
                            Totale gilde nel continente:{" "}
                            <span data-testid="world-neighbors-total"
                                  className="text-foreground">
                                {state.data.total_in_continent}
                            </span>
                        </div>
                        {(state.data.nearby_guilds || []).length === 0 ? (
                            <div data-testid="world-neighbors-empty"
                                 className="border border-border/60 bg-card/40 rounded-sm p-4 text-[12px] text-muted-foreground">
                                Nessun&apos;altra gilda si è ancora ancorata qui.
                                Sei tra le prime pioniere.
                            </div>
                        ) : (
                            <ul data-testid="world-neighbors-list" className="space-y-2">
                                {state.data.nearby_guilds.map((g) => {
                                    const act = ACTIVITY_LABEL[g.activity]
                                        || ACTIVITY_LABEL.inactive;
                                    return (
                                        <li key={g.guild_id}
                                            data-testid={`world-neighbor-${g.guild_id}`}
                                            className="border border-border/60 bg-card/40 rounded-sm p-3">
                                            <div className="flex items-baseline justify-between gap-2 flex-wrap">
                                                <div>
                                                    <div className="text-[13px] text-foreground">
                                                        {g.name || "?"}
                                                    </div>
                                                    {g.banner_text ? (
                                                        <div className="text-[11px] text-muted-foreground italic mt-0.5">
                                                            « {g.banner_text} »
                                                        </div>
                                                    ) : null}
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-[10px] text-muted-foreground">
                                                        Lv {g.level ?? 1}
                                                    </span>
                                                    <span className={`text-[10px] px-2 py-0.5 rounded-sm border ${act.cls}`}>
                                                        {act.text}
                                                    </span>
                                                </div>
                                            </div>
                                        </li>
                                    );
                                })}
                            </ul>
                        )}
                    </>
                )}
            </main>
        </div>
    );
}
