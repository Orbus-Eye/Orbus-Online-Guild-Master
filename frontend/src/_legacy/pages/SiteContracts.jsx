// ROUND 16.3 Phase 3 — Site contracts (Incarichi di Sede).
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { api, formatApiError } from "../lib/api";
import AppHeader from "../components/AppHeader";

function fmtDate(bucket) {
    try {
        return new Date(bucket + "T00:00:00Z").toLocaleDateString("it", {
            month: "short", day: "numeric",
        });
    } catch { return bucket; }
}

export default function SiteContracts() {
    const [today, setToday] = useState(null);
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [busy, setBusy] = useState(false);

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const [t, h] = await Promise.all([
                api.get("/site-income/today"),
                api.get("/site-income/history?days=7"),
            ]);
            setToday(t.data);
            setHistory(h.data.rows || []);
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { load(); }, [load]);

    const doClaim = async () => {
        setBusy(true);
        try {
            const { data } = await api.post("/site-income/claim");
            if (data.status === "ok") {
                toast.success(`Reclamati ${data.amount} oro`);
            } else {
                toast.info("Già reclamato oggi");
            }
            await load();
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setBusy(false);
        }
    };

    const alreadyClaimed = !!today?.claimed_at;

    return (
        <div className="min-h-screen bg-background text-foreground overflow-x-hidden">
            <AppHeader />
            <main className="max-w-3xl mx-auto px-4 py-6 pb-32 md:pb-8 font-mono">
                <header className="mb-4">
                    <h1 data-testid="site-contracts-title"
                        className="text-amber text-xl tracking-widest">
                        :: Incarichi di Sede
                    </h1>
                    <p className="text-[11px] text-muted-foreground mt-1">
                        La tua sede riceve piccoli incarichi ogni giorno.
                        Reclama l&apos;oro accumulato.
                    </p>
                </header>

                {loading && (
                    <div data-testid="site-contracts-loading"
                         className="text-[11px] text-muted-foreground italic">
                        :: Caricamento...
                    </div>
                )}

                {!loading && today && (
                    <section data-testid="site-contracts-today"
                             className="border border-amber/40 bg-card/40 rounded-sm p-4 mb-4">
                        <div className="flex items-baseline justify-between mb-3">
                            <div className="text-[11px] text-amber tracking-widest">
                                :: Oggi ({fmtDate(today.day_bucket)})
                            </div>
                            <div className="text-[10px] text-muted-foreground">
                                {alreadyClaimed ? "reclamato" : "in attesa"}
                            </div>
                        </div>
                        <div data-testid="site-contracts-today-total"
                             className="text-2xl text-foreground mb-3">
                            <span className="text-amber">{today.total_amount}</span>{" "}
                            <span className="text-[11px] text-muted-foreground">oro</span>
                        </div>

                        <div className="grid grid-cols-2 gap-3 text-[11px] mb-3">
                            <div>
                                <div className="text-muted-foreground">Base</div>
                                <div className="text-foreground">
                                    {today.breakdown?.base ?? 0}
                                </div>
                            </div>
                            <div>
                                <div className="text-muted-foreground">Livello</div>
                                <div className="text-foreground">
                                    +{today.breakdown?.level_bonus ?? 0}
                                </div>
                            </div>
                            <div>
                                <div className="text-muted-foreground">Reputazione</div>
                                <div className="text-foreground">
                                    +{today.breakdown?.reputation_bonus ?? 0}
                                </div>
                            </div>
                            <div>
                                <div className="text-muted-foreground">Evento</div>
                                <div data-testid="site-contracts-event-mod"
                                     className={
                                        (today.breakdown?.event_modifier_pct ?? 0) > 0
                                            ? "text-green-400"
                                            : (today.breakdown?.event_modifier_pct ?? 0) < 0
                                                ? "text-red-400"
                                                : "text-foreground"
                                     }>
                                    {(today.breakdown?.event_modifier_pct ?? 0) > 0 ? "+" : ""}
                                    {today.breakdown?.event_modifier_pct ?? 0}%
                                </div>
                            </div>
                        </div>

                        <button
                            type="button"
                            onClick={doClaim}
                            disabled={busy || alreadyClaimed}
                            data-testid="site-contracts-claim"
                            className="text-[11px] tracking-widest px-4 py-2.5 min-h-[44px] w-full md:w-auto border border-amber text-amber rounded-sm hover:bg-amber/10 font-bold disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                            {alreadyClaimed
                                ? `Reclamato: ${today.total_amount} oro`
                                : busy ? "…" : `Reclama ${today.total_amount} oro`}
                        </button>
                    </section>
                )}

                {!loading && (
                    <section>
                        <div className="text-[11px] text-amber tracking-widest mb-2">
                            :: Storico (7 giorni)
                        </div>
                        {history.length === 0 ? (
                            <div className="text-[11px] text-muted-foreground italic">
                                Nessuno storico ancora.
                            </div>
                        ) : (
                            <ul data-testid="site-contracts-history"
                                className="space-y-2">
                                {history.map((r) => (
                                    <li key={r.id}
                                        className="border border-border/60 bg-card/40 rounded-sm p-3 flex items-center justify-between">
                                        <div>
                                            <div className="text-[12px] text-foreground">
                                                {fmtDate(r.day_bucket)}
                                            </div>
                                            <div className="text-[10px] text-muted-foreground">
                                                {r.claimed_at ? "reclamato" : "in attesa"}
                                                {r.event_modifier_pct !== 0 ? (
                                                    <span className="ml-2">
                                                        · evento {r.event_modifier_pct > 0 ? "+" : ""}
                                                        {r.event_modifier_pct}%
                                                    </span>
                                                ) : null}
                                            </div>
                                        </div>
                                        <div className="text-[13px] text-amber">
                                            {r.total_amount}
                                        </div>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </section>
                )}

                <div className="mt-6">
                    <Link to="/dashboard"
                          className="text-[11px] text-muted-foreground hover:text-amber tracking-widest">
                        ← Dashboard
                    </Link>
                </div>
            </main>
        </div>
    );
}
