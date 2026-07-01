// ROUND 16.3 Phase 1 — World Boss list page (mobile-first).
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, formatApiError } from "../lib/api";
import AppHeader from "../components/AppHeader";
import { toast } from "sonner";

function fmtRemaining(endsAt) {
    if (!endsAt) return "-";
    const ms = new Date(endsAt).getTime() - Date.now();
    if (ms <= 0) return "Terminato";
    const h = Math.floor(ms / 3600000);
    const m = Math.floor((ms % 3600000) / 60000);
    return h > 24 ? `${Math.floor(h / 24)}g ${h % 24}h` : `${h}h ${m}m`;
}

export default function WorldBoss() {
    const [events, setEvents] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const { data } = await api.get("/world-boss/active");
                if (!cancelled) setEvents(data.events || []);
            } catch (err) {
                if (!cancelled) toast.error(formatApiError(err));
            } finally {
                if (!cancelled) setLoading(false);
            }
        })();
        return () => { cancelled = true; };
    }, []);

    return (
        <div className="min-h-screen bg-background text-foreground">
            <AppHeader />
            <main className="max-w-4xl mx-auto px-4 py-6 pb-32 md:pb-8 font-mono">
                <header className="mb-6">
                    <h1 data-testid="worldboss-title"
                        className="text-amber text-xl tracking-widest">
                        :: World Boss
                    </h1>
                    <p className="text-[11px] text-muted-foreground mt-1">
                        Eventi cooperativi globali. Contribuisci con la tua gilda
                        a ridurre l&apos;HP del boss entro il timer.
                    </p>
                </header>
                {loading ? (
                    <div data-testid="worldboss-loading"
                         className="text-[11px] text-muted-foreground italic">
                        :: Caricamento...
                    </div>
                ) : events.length === 0 ? (
                    <div data-testid="worldboss-empty"
                         className="border border-border/60 bg-card/40 rounded-sm p-4">
                        <p className="text-[12px] text-muted-foreground">
                            Nessun evento World Boss attivo al momento. Torna presto —
                            gli eventi verranno pianificati dall&apos;amministrazione.
                        </p>
                    </div>
                ) : (
                    <ul className="space-y-3">
                        {events.map((ev) => {
                            const hpRatio = ev.total_hp
                                ? Math.max(0, ev.current_hp / ev.total_hp) : 0;
                            return (
                                <li key={ev.id}
                                    data-testid={`worldboss-event-${ev.id}`}
                                    className="border border-border/60 bg-card/40 rounded-sm p-4">
                                    <div className="flex flex-wrap items-baseline justify-between gap-2 mb-2">
                                        <h2 className="text-[14px] text-amber">
                                            {ev.name_it || ev.name_en}
                                        </h2>
                                        <span className={`text-[10px] px-2 py-0.5 rounded-sm border ${
                                            ev.status === "active"
                                                ? "border-green-500/40 text-green-400"
                                                : "border-amber/40 text-amber"
                                        }`}>
                                            {ev.status.toUpperCase()}
                                        </span>
                                    </div>
                                    <div className="text-[11px] text-muted-foreground mb-3">
                                        Fase {ev.phase} · {fmtRemaining(ev.ends_at)} rimanenti
                                    </div>
                                    <div className="mb-2">
                                        <div className="flex justify-between text-[10px] text-muted-foreground mb-1">
                                            <span>HP boss</span>
                                            <span>
                                                {(ev.current_hp || 0).toLocaleString()} /
                                                {" "}{(ev.total_hp || 0).toLocaleString()}
                                            </span>
                                        </div>
                                        <div className="h-2 w-full bg-secondary/40 rounded-sm overflow-hidden">
                                            <div
                                                className="h-full bg-amber transition-all"
                                                style={{ width: `${hpRatio * 100}%` }}
                                            />
                                        </div>
                                    </div>
                                    <div className="text-[10px] text-muted-foreground mb-3">
                                        Minacce: {(ev.threats || []).join(", ") || "—"}
                                    </div>
                                    <Link
                                        to={`/world-boss/${ev.id}`}
                                        data-testid={`worldboss-open-${ev.id}`}
                                        className="inline-block w-full md:w-auto text-center text-[11px] tracking-widest px-4 py-2.5 min-h-[44px] border border-amber text-amber rounded-sm hover:bg-amber/10 font-bold"
                                    >
                                        Apri evento →
                                    </Link>
                                </li>
                            );
                        })}
                    </ul>
                )}
            </main>
        </div>
    );
}
