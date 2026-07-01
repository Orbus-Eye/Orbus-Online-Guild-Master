// ROUND 16.3 Phase 5A — Legendary Forge orders list.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { api, formatApiError } from "../lib/api";
import AppHeader from "../components/AppHeader";

const QUALITY_STYLE = {
    perfezionato: "bg-amber-950/40 border-amber-500 text-amber-300",
    normale: "bg-slate-800 border-slate-500 text-slate-300",
    imperfetto: "bg-orange-950/40 border-orange-500 text-orange-300",
    failed: "bg-red-950/40 border-red-500 text-red-300",
};

function fmtTime(iso) {
    if (!iso) return "—";
    try { return new Date(iso).toLocaleString("it-IT"); } catch { return iso; }
}

function Countdown({ completesAt }) {
    const [ms, setMs] = useState(() => new Date(completesAt) - new Date());
    useEffect(() => {
        const id = setInterval(() => setMs(new Date(completesAt) - new Date()), 1000);
        return () => clearInterval(id);
    }, [completesAt]);
    if (ms <= 0) return <span className="text-green-400">Pronto! Ricarica.</span>;
    const s = Math.floor(ms / 1000);
    const m = Math.floor(s / 60), r = s % 60;
    return <span className="text-amber-300 font-mono">{m}m {r}s</span>;
}

export default function LegendaryForgeOrders() {
    const [state, setState] = useState({ loading: true, inProgress: [], recent: [], err: null });
    const [detail, setDetail] = useState(null);

    async function load() {
        try {
            const r = await api.get("/legendary-forge/orders/mine");
            setState({ loading: false, inProgress: r.data.in_progress || [],
                recent: r.data.recent || [], err: null });
        } catch (err) {
            const msg = formatApiError(err);
            toast.error(msg);
            setState({ loading: false, inProgress: [], recent: [], err: msg });
        }
    }
    useEffect(() => { load(); const id = setInterval(load, 30000);
        return () => clearInterval(id); }, []);

    return (
        <div className="min-h-screen bg-background text-foreground overflow-x-hidden">
            <AppHeader />
            <main className="max-w-3xl mx-auto px-4 py-6 pb-32 md:pb-8 font-mono"
                data-testid="orders-page">
                <div className="mb-4">
                    <Link to="/legendary-forge"
                        className="text-sm text-muted-foreground hover:text-amber-300"
                        data-testid="orders-back">
                        ← Torna alla Forgia
                    </Link>
                </div>
                <h1 className="text-2xl md:text-3xl font-bold text-amber-300 mb-6"
                    data-testid="orders-title">
                    I miei Ordini di Forgiatura
                </h1>

                {state.loading && <div className="text-center py-16 text-muted-foreground">
                    Caricamento…</div>}

                {!state.loading && (
                    <>
                        {/* In-Progress */}
                        <section className="mb-8" data-testid="orders-in-progress">
                            <h2 className="text-sm font-bold text-slate-300 mb-3
                                uppercase tracking-wide">
                                In Corso ({state.inProgress.length})
                            </h2>
                            {state.inProgress.length === 0 ? (
                                <div className="text-xs text-muted-foreground italic
                                    border border-dashed border-slate-700 rounded p-4
                                    text-center">
                                    Nessun ordine in corso.
                                </div>
                            ) : state.inProgress.map((o) => (
                                <div key={o.id} className="mb-3 border border-amber-500/40
                                    rounded-lg p-3 bg-slate-900/50"
                                    data-testid={`order-inprogress-${o.id}`}>
                                    <div className="flex justify-between items-start mb-2">
                                        <div>
                                            <div className="text-sm font-bold text-amber-300">
                                                {o.recipe_slug}
                                            </div>
                                            <div className="text-xs text-muted-foreground">
                                                Avviato {fmtTime(o.started_at)}
                                            </div>
                                        </div>
                                        <Countdown completesAt={o.completes_at} />
                                    </div>
                                </div>
                            ))}
                        </section>

                        {/* Recent */}
                        <section data-testid="orders-recent">
                            <h2 className="text-sm font-bold text-slate-300 mb-3
                                uppercase tracking-wide">
                                Storico Recente ({state.recent.length})
                            </h2>
                            {state.recent.length === 0 ? (
                                <div className="text-xs text-muted-foreground italic
                                    border border-dashed border-slate-700 rounded p-4
                                    text-center">
                                    Nessun ordine completato.
                                </div>
                            ) : state.recent.map((o) => {
                                const q = o.status === "failed" ? "failed" : o.result_quality;
                                const cls = QUALITY_STYLE[q] || QUALITY_STYLE.normale;
                                return (
                                    <button key={o.id}
                                        onClick={() => setDetail(o)}
                                        className={`w-full mb-2 text-left border rounded-lg
                                            p-3 hover:opacity-90 ${cls}`}
                                        data-testid={`order-recent-${o.id}`}>
                                        <div className="flex justify-between items-center">
                                            <div>
                                                <div className="text-sm font-bold">
                                                    {o.recipe_slug}
                                                </div>
                                                <div className="text-[10px] opacity-70">
                                                    {fmtTime(o.resolved_at || o.completes_at)}
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <div className="text-xs uppercase font-bold">
                                                    {o.status === "failed" ? "Fallito" : q}
                                                </div>
                                                {o.pity_applied && (
                                                    <div className="text-[10px] opacity-80">
                                                        pity ⚡
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </button>
                                );
                            })}
                        </section>
                    </>
                )}

                {/* Detail modal */}
                {detail && (
                    <div className="fixed inset-0 bg-black/80 z-50 flex items-center
                        justify-center p-4" data-testid="order-detail-modal"
                        onClick={() => setDetail(null)}>
                        <div className="bg-slate-900 border border-amber-500/60
                            rounded-lg p-5 max-w-md w-full"
                            onClick={(e) => e.stopPropagation()}>
                            <h3 className="text-lg font-bold text-amber-300 mb-3">
                                {detail.recipe_slug}
                            </h3>
                            <div className="text-xs space-y-1">
                                <div><span className="text-muted-foreground">Stato:</span> {detail.status}</div>
                                <div><span className="text-muted-foreground">Qualità:</span> {detail.result_quality || "—"}</div>
                                <div><span className="text-muted-foreground">Success roll:</span> {detail.success_roll ?? "—"}</div>
                                <div><span className="text-muted-foreground">Quality roll:</span> {detail.quality_roll ?? "—"}</div>
                                <div><span className="text-muted-foreground">Pity applicato:</span> {detail.pity_applied ? "Sì ⚡" : "No"}</div>
                                <div><span className="text-muted-foreground">Oro consumato:</span> {(detail.gold_consumed || 0).toLocaleString()}</div>
                                <div><span className="text-muted-foreground">Item ID:</span>
                                    <span className="font-mono text-[10px] break-all">
                                        {detail.result_item_instance_id || "nessuno"}</span></div>
                            </div>
                            <button onClick={() => setDetail(null)}
                                className="mt-4 w-full px-4 py-2 min-h-[44px]
                                    bg-slate-700 hover:bg-slate-600 rounded-md text-sm"
                                data-testid="order-detail-close">
                                Chiudi
                            </button>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}
