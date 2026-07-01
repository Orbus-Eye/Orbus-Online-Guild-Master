// ROUND 16.3 Phase 6 Iter2 — Trade Pact Request (find + invite).
import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { api, formatApiError } from "../lib/api";
import AppHeader from "../components/AppHeader";

export default function TradePactRequest() {
    const navigate = useNavigate();
    const [state, setState] = useState({
        loading: true, neighbors: [], err: null, sending: null,
    });

    const load = useCallback(async () => {
        try {
            const r = await api.get("/world/neighbors").catch(() => ({ data: { neighbors: [] } }));
            setState((s) => ({
                ...s, loading: false,
                neighbors: r.data.neighbors || r.data.guilds || [],
                err: null,
            }));
        } catch (err) {
            const msg = formatApiError(err);
            toast.error(msg);
            setState((s) => ({ ...s, loading: false, err: msg }));
        }
    }, []);

    useEffect(() => { load(); }, [load]);

    const invite = useCallback(async (targetGuildId, targetGuildName) => {
        setState((s) => ({ ...s, sending: targetGuildId }));
        try {
            await api.post(`/trade-pacts/request/${targetGuildId}`);
            toast.success(`Richiesta inviata a ${targetGuildName}`);
            navigate("/trade-pacts");
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setState((s) => ({ ...s, sending: null }));
        }
    }, [navigate]);

    return (
        <div className="min-h-screen bg-background text-foreground overflow-x-hidden">
            <AppHeader />
            <main className="max-w-3xl mx-auto px-4 py-6 pb-32 md:pb-8 font-mono"
                data-testid="trade-pact-request-page">
                <Link to="/trade-pacts"
                      className="text-sm text-emerald-300 hover:text-emerald-200 inline-block mb-4"
                      data-testid="trade-pact-request-back">
                    ← Torna ai Patti
                </Link>

                <h1 className="text-2xl md:text-3xl font-bold text-emerald-300 mb-2">
                    Nuova Richiesta di Patto
                </h1>
                <div className="mb-4 p-3 rounded border border-amber-500/40 bg-amber-950/20 text-xs text-amber-200"
                     data-testid="trade-pact-request-warnings">
                    ⚠ Solo gilde dello stesso continente possono stringere patti.<br />
                    ⚠ Max 3 patti attivi contemporaneamente.
                </div>

                {state.loading && (
                    <div className="text-center text-muted-foreground py-12">Caricamento…</div>
                )}

                {!state.loading && state.neighbors.length === 0 && (
                    <div className="border border-slate-700 rounded p-6 text-center text-slate-400"
                         data-testid="trade-pact-request-empty">
                        Nessuna gilda vicina disponibile nel tuo continente.
                    </div>
                )}

                {!state.loading && state.neighbors.length > 0 && (
                    <div className="space-y-3">
                        {state.neighbors.map((g) => {
                            const gid = g.guild_id || g.id;
                            const gname = g.guild_name || g.name || gid;
                            const glvl = g.guild_level || g.level;
                            return (
                                <div key={gid}
                                     className="border border-slate-700 rounded p-4 bg-slate-900/40 flex items-center justify-between gap-3"
                                     data-testid={`trade-pact-neighbor-${gid}`}>
                                    <div className="min-w-0 flex-1">
                                        <div className="font-semibold text-slate-100 truncate">
                                            {gname}
                                        </div>
                                        {glvl != null && (
                                            <div className="text-xs text-slate-500">Livello {glvl}</div>
                                        )}
                                    </div>
                                    <button onClick={() => invite(gid, gname)}
                                            disabled={state.sending === gid}
                                            className="min-h-[44px] px-4 py-2 rounded bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-700 disabled:text-slate-500 text-slate-900 font-semibold text-sm"
                                            data-testid={`trade-pact-invite-${gid}`}>
                                        {state.sending === gid ? "Invio…" : "Invia Richiesta"}
                                    </button>
                                </div>
                            );
                        })}
                    </div>
                )}
            </main>
        </div>
    );
}
