// ROUND 16.3 Phase 6 Iter2 — Trade Pacts hub (attivi + ricevute + inviate).
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { api, formatApiError } from "../lib/api";
import AppHeader from "../components/AppHeader";

export default function TradePacts() {
    const [state, setState] = useState({
        loading: true, active: [], incoming: [], outgoing: [],
        maxAccepted: 3, err: null, actioning: null,
        confirmDissolve: null,
    });

    const load = useCallback(async () => {
        try {
            const [mine, received] = await Promise.all([
                api.get("/trade-pacts/mine"),
                api.get("/trade-pacts/received"),
            ]);
            const allMine = mine.data.pacts || [];
            const active = allMine.filter((p) => p.status === "accepted");
            const outgoing = allMine.filter((p) => p.status === "pending_request");
            setState((s) => ({
                ...s, loading: false,
                active, incoming: received.data.pacts || [], outgoing,
                maxAccepted: mine.data.max_accepted || 3, err: null,
            }));
        } catch (err) {
            const msg = formatApiError(err);
            toast.error(msg);
            setState((s) => ({ ...s, loading: false, err: msg }));
        }
    }, []);

    useEffect(() => { load(); }, [load]);

    const doAction = useCallback(async (pactId, method, path, extraMsg) => {
        setState((s) => ({ ...s, actioning: pactId }));
        try {
            const url = `/trade-pacts/${pactId}${path}`;
            await (method === "delete" ? api.delete(url) : api.post(url));
            toast.success(extraMsg || "Azione completata");
            setState((s) => ({ ...s, confirmDissolve: null }));
            await load();
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setState((s) => ({ ...s, actioning: null }));
        }
    }, [load]);

    return (
        <div className="min-h-screen bg-background text-foreground overflow-x-hidden">
            <AppHeader />
            <main className="max-w-4xl mx-auto px-4 py-6 pb-32 md:pb-8 font-mono"
                data-testid="trade-pacts-page">
                <div className="mb-6 flex flex-col md:flex-row md:items-end md:justify-between gap-3">
                    <div>
                        <h1 className="text-3xl md:text-4xl font-bold text-emerald-300 mb-1"
                            data-testid="trade-pacts-title">
                            Patti Commerciali
                        </h1>
                        <p className="text-sm text-muted-foreground">
                            Alleanze sociali tra gilde dello stesso continente.
                            Max {state.maxAccepted} patti attivi.
                        </p>
                    </div>
                    <Link to="/trade-pacts/request"
                          className="inline-flex items-center justify-center min-h-[44px] w-full md:w-auto px-4 py-2 rounded bg-emerald-500 hover:bg-emerald-400 text-slate-900 font-semibold"
                          data-testid="trade-pacts-new-cta">
                        + Nuova Richiesta
                    </Link>
                </div>

                {state.loading && (
                    <div className="text-center text-muted-foreground py-12">Caricamento…</div>
                )}

                {!state.loading && (
                    <>
                        <section className="mb-6"
                                 data-testid="trade-pacts-active-section">
                            <h2 className="text-lg text-slate-200 mb-3 border-b border-slate-800 pb-2 flex items-center justify-between">
                                <span>Patti Attivi</span>
                                <span className="text-xs text-emerald-300 font-mono">
                                    {state.active.length}/{state.maxAccepted}
                                </span>
                            </h2>
                            {state.active.length === 0 ? (
                                <p className="text-sm text-slate-500 py-4"
                                   data-testid="trade-pacts-no-active">
                                    Nessun patto attivo. Invia la tua prima richiesta!
                                </p>
                            ) : (
                                <div className="space-y-3">
                                    {state.active.map((p) => (
                                        <div key={p.id}
                                             className="border border-emerald-500/40 rounded p-4 bg-slate-900/40"
                                             data-testid={`trade-pact-active-${p.id}`}>
                                            <div className="flex items-center justify-between mb-2 gap-2 flex-wrap">
                                                <div>
                                                    <div className="text-sm text-slate-500">Partner</div>
                                                    <div className="text-slate-100 font-mono text-xs truncate">
                                                        {p.guild_a_id === p.guild_a_id ? p.guild_b_id : p.guild_a_id}
                                                    </div>
                                                </div>
                                                <button onClick={() => setState((s) => ({ ...s, confirmDissolve: p.id }))}
                                                        className="min-h-[44px] px-3 py-2 rounded border border-red-500/60 text-red-300 text-sm"
                                                        data-testid={`trade-pact-dissolve-${p.id}`}>
                                                    Sciogli
                                                </button>
                                            </div>
                                            {p.activated_at && (
                                                <div className="text-xs text-slate-500">
                                                    Attivo dal {new Date(p.activated_at).toLocaleDateString()}
                                                </div>
                                            )}
                                            {state.confirmDissolve === p.id && (
                                                <div className="mt-3 p-3 border border-red-500/40 rounded bg-red-950/20"
                                                     data-testid={`trade-pact-dissolve-confirm-${p.id}`}>
                                                    <p className="text-xs text-slate-300 mb-2">
                                                        ⚠ Sciogliere unilateralmente attiva un cooldown di 7 giorni.
                                                    </p>
                                                    <div className="flex flex-col md:flex-row gap-2">
                                                        <button onClick={() => doAction(p.id, "post", "/dissolve?reason=unilateral", "Patto sciolto")}
                                                                disabled={state.actioning === p.id}
                                                                className="min-h-[44px] w-full md:w-auto px-3 py-2 rounded bg-red-500 hover:bg-red-400 text-slate-900 font-semibold"
                                                                data-testid={`trade-pact-dissolve-unilateral-${p.id}`}>
                                                            Sciogli (unilaterale)
                                                        </button>
                                                        <button onClick={() => doAction(p.id, "post", "/dissolve?reason=mutual", "Patto sciolto")}
                                                                disabled={state.actioning === p.id}
                                                                className="min-h-[44px] w-full md:w-auto px-3 py-2 rounded border border-slate-600 text-slate-300"
                                                                data-testid={`trade-pact-dissolve-mutual-${p.id}`}>
                                                            Sciogli (mutuo)
                                                        </button>
                                                        <button onClick={() => setState((s) => ({ ...s, confirmDissolve: null }))}
                                                                className="min-h-[44px] w-full md:w-auto px-3 py-2 rounded border border-slate-700 text-slate-400"
                                                                data-testid={`trade-pact-dissolve-cancel-${p.id}`}>
                                                            Annulla
                                                        </button>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </section>

                        <section className="mb-6"
                                 data-testid="trade-pacts-incoming-section">
                            <h2 className="text-lg text-slate-200 mb-3 border-b border-slate-800 pb-2">
                                Richieste in arrivo ({state.incoming.length})
                            </h2>
                            {state.incoming.length === 0 ? (
                                <p className="text-sm text-slate-500 py-3">Nessuna richiesta pending.</p>
                            ) : (
                                <div className="space-y-3">
                                    {state.incoming.map((p) => (
                                        <div key={p.id}
                                             className="border border-sky-500/40 rounded p-4 bg-slate-900/40"
                                             data-testid={`trade-pact-incoming-${p.id}`}>
                                            <div className="text-sm text-slate-300 mb-2">
                                                Da: <span className="font-mono text-xs">{p.guild_a_id}</span>
                                            </div>
                                            <div className="text-xs text-slate-500 mb-3">
                                                Ricevuta il {new Date(p.requested_at).toLocaleString()}
                                            </div>
                                            <div className="flex flex-col md:flex-row gap-2">
                                                <button onClick={() => doAction(p.id, "post", "/accept", "Patto accettato")}
                                                        disabled={state.actioning === p.id}
                                                        className="min-h-[44px] w-full md:w-auto px-4 py-2 rounded bg-emerald-500 hover:bg-emerald-400 text-slate-900 font-semibold"
                                                        data-testid={`trade-pact-accept-${p.id}`}>
                                                    Accetta
                                                </button>
                                                <button onClick={() => doAction(p.id, "post", "/reject", "Richiesta rifiutata")}
                                                        disabled={state.actioning === p.id}
                                                        className="min-h-[44px] w-full md:w-auto px-4 py-2 rounded border border-slate-600 text-slate-300"
                                                        data-testid={`trade-pact-reject-${p.id}`}>
                                                    Rifiuta
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </section>

                        <section data-testid="trade-pacts-outgoing-section">
                            <h2 className="text-lg text-slate-200 mb-3 border-b border-slate-800 pb-2">
                                Richieste inviate ({state.outgoing.length})
                            </h2>
                            {state.outgoing.length === 0 ? (
                                <p className="text-sm text-slate-500 py-3">Nessuna richiesta in uscita.</p>
                            ) : (
                                <ul className="space-y-2">
                                    {state.outgoing.map((p) => (
                                        <li key={p.id}
                                            className="border border-slate-700 rounded p-3 flex items-center justify-between gap-2"
                                            data-testid={`trade-pact-outgoing-${p.id}`}>
                                            <div className="text-sm text-slate-300 min-w-0 flex-1">
                                                <div className="text-xs text-slate-500">A</div>
                                                <div className="font-mono text-xs truncate">{p.guild_b_id}</div>
                                            </div>
                                            <button onClick={() => doAction(p.id, "post", "/dissolve?reason=mutual", "Richiesta annullata")}
                                                    disabled={state.actioning === p.id}
                                                    className="min-h-[44px] px-3 py-2 rounded border border-slate-600 text-slate-300 text-xs"
                                                    data-testid={`trade-pact-cancel-${p.id}`}>
                                                Annulla
                                            </button>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </section>
                    </>
                )}
            </main>
        </div>
    );
}
