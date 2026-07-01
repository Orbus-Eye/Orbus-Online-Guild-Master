// ROUND 16.3 Phase 5B Iter2 — Arfus Research orders (in-progress + history).
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { api, formatApiError } from "../lib/api";
import AppHeader from "../components/AppHeader";

function useCountdown(iso) {
    const [now, setNow] = useState(Date.now());
    useEffect(() => {
        const t = setInterval(() => setNow(Date.now()), 1000);
        return () => clearInterval(t);
    }, []);
    if (!iso) return { text: "—", remaining: 0, done: true };
    const then = new Date(iso).getTime();
    const remaining = Math.max(0, Math.floor((then - now) / 1000));
    const h = Math.floor(remaining / 3600);
    const m = Math.floor((remaining % 3600) / 60);
    const s = remaining % 60;
    const text = h > 0 ? `${h}h ${m}m ${s}s` : `${m}m ${s}s`;
    return { text, remaining, done: remaining === 0 };
}

function OrderRow({ order }) {
    const cd = useCountdown(order.completes_at);
    const total = order.duration_seconds || 1;
    const elapsedPct = Math.min(100, ((total - cd.remaining) / total) * 100);
    return (
        <div className="border border-slate-700 rounded p-4 bg-slate-900/40"
             data-testid={`arfus-order-inprogress-${order.id}`}>
            <div className="flex items-center justify-between mb-2 gap-2 flex-wrap">
                <div className="font-semibold text-slate-100 truncate">
                    {order.technology_slug}
                </div>
                <div className="text-sm text-amber-300 font-mono"
                     data-testid={`arfus-order-countdown-${order.id}`}>
                    {cd.done ? "In risoluzione…" : cd.text}
                </div>
            </div>
            <div className="h-2 bg-slate-800 rounded overflow-hidden">
                <div className="h-full bg-sky-500 transition-all"
                     style={{ width: `${elapsedPct}%` }} />
            </div>
            <div className="text-xs text-slate-500 mt-2">
                Oro speso: {order.gold_consumed}
            </div>
        </div>
    );
}

export default function ArfusResearch() {
    const [state, setState] = useState({
        loading: true, inProgress: [], recent: [], err: null,
    });

    const load = useCallback(async () => {
        try {
            const r = await api.get("/arfus-forge/research/mine");
            setState({
                loading: false,
                inProgress: r.data.in_progress || [],
                recent: r.data.recent || [],
                err: null,
            });
        } catch (err) {
            const msg = formatApiError(err);
            toast.error(msg);
            setState((s) => ({ ...s, loading: false, err: msg }));
        }
    }, []);

    useEffect(() => {
        load();
        const t = setInterval(load, 30000);
        return () => clearInterval(t);
    }, [load]);

    return (
        <div className="min-h-screen bg-background text-foreground overflow-x-hidden">
            <AppHeader />
            <main className="max-w-3xl mx-auto px-4 py-6 pb-32 md:pb-8 font-mono"
                data-testid="arfus-research-page">
                <Link to="/arfus-forge"
                      className="text-sm text-sky-300 hover:text-sky-200 inline-block mb-4"
                      data-testid="arfus-research-back">
                    ← Torna alla Forgia
                </Link>

                <h1 className="text-2xl md:text-3xl font-bold text-amber-300 mb-6">
                    Ricerche di Arfus
                </h1>

                {state.loading && (
                    <div className="text-center text-muted-foreground py-8">Caricamento…</div>
                )}

                {!state.loading && (
                    <>
                        <section className="mb-6"
                                 data-testid="arfus-research-inprogress-section">
                            <h2 className="text-lg text-slate-200 mb-3 border-b border-slate-800 pb-2">
                                In corso ({state.inProgress.length})
                            </h2>
                            {state.inProgress.length === 0 ? (
                                <p className="text-sm text-slate-500 py-4"
                                   data-testid="arfus-no-inprogress">
                                    Nessuna ricerca in corso. Vai alla Forgia per iniziarne una.
                                </p>
                            ) : (
                                <div className="space-y-3">
                                    {state.inProgress.map((o) => <OrderRow key={o.id} order={o} />)}
                                </div>
                            )}
                        </section>

                        <section data-testid="arfus-research-history-section">
                            <h2 className="text-lg text-slate-200 mb-3 border-b border-slate-800 pb-2">
                                Storico (ultime {Math.min(20, state.recent.length)})
                            </h2>
                            {state.recent.length === 0 ? (
                                <p className="text-sm text-slate-500 py-4"
                                   data-testid="arfus-no-history">
                                    Nessuna ricerca completata.
                                </p>
                            ) : (
                                <ul className="space-y-2">
                                    {state.recent.slice(0, 20).map((o) => (
                                        <li key={o.id}
                                            className="border border-slate-800 rounded p-3 bg-slate-900/20"
                                            data-testid={`arfus-order-done-${o.id}`}>
                                            <div className="flex items-center justify-between gap-2 flex-wrap">
                                                <span className="font-semibold text-slate-100 truncate">
                                                    {o.technology_slug}
                                                </span>
                                                <span className="text-xs text-emerald-400">
                                                    completata
                                                </span>
                                            </div>
                                            <div className="text-xs text-slate-500 mt-1">
                                                {o.resolved_at ? new Date(o.resolved_at).toLocaleString() : "—"}
                                            </div>
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
