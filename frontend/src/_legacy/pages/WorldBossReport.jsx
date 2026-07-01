// ROUND 16.3 Phase 1 — World Boss report page.
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, formatApiError } from "../lib/api";
import AppHeader from "../components/AppHeader";
import { toast } from "sonner";

export default function WorldBossReport() {
    const { eventId } = useParams();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        (async () => {
            try {
                const { data: d } = await api.get(`/world-boss/events/${eventId}/report`);
                setData(d);
            } catch (err) {
                toast.error(formatApiError(err));
            } finally { setLoading(false); }
        })();
    }, [eventId]);

    if (loading) {
        return (
            <div className="min-h-screen bg-background text-foreground">
                <AppHeader />
                <main className="max-w-4xl mx-auto px-4 py-6 font-mono">
                    <p className="text-[11px] text-muted-foreground">:: Caricamento report...</p>
                </main>
            </div>
        );
    }
    if (!data) {
        return (
            <div className="min-h-screen bg-background text-foreground">
                <AppHeader />
                <main className="max-w-4xl mx-auto px-4 py-6 font-mono">
                    <p className="text-[11px] text-red-400">Report non disponibile</p>
                </main>
            </div>
        );
    }
    const ev = data.event;
    const reward = data.reward;

    return (
        <div className="min-h-screen bg-background text-foreground">
            <AppHeader />
            <main className="max-w-4xl mx-auto px-4 py-6 pb-32 md:pb-8 font-mono">
                <header className="mb-6">
                    <Link to={`/world-boss/${eventId}`} className="text-[10px] text-muted-foreground hover:text-amber">
                        ← Torna all&apos;evento
                    </Link>
                    <h1 data-testid="worldboss-report-title" className="text-amber text-xl tracking-widest mt-2">
                        :: Report Finale — {ev.name_it || ev.name_en}
                    </h1>
                </header>
                <section className="border border-border/60 bg-card/40 rounded-sm p-4 mb-4">
                    <div className="text-[12px] mb-2">
                        Esito: <span className={ev.status === "completed" ? "text-green-400" : "text-red-400"}>
                            {ev.status === "completed" ? "COMPLETATO" : "FALLITO"}
                        </span>
                    </div>
                    <div className="text-[10px] text-muted-foreground">
                        Durata: {ev.starts_at} → {ev.resolved_at || ev.ends_at}
                    </div>
                </section>
                <section className="border border-border/60 bg-card/40 rounded-sm p-4">
                    <div className="text-amber tracking-widest text-[11px] mb-2">
                        :: Ricompense della tua gilda
                    </div>
                    {!reward ? (
                        <p className="text-[11px] text-muted-foreground italic">
                            :: La tua gilda non ha ricevuto ricompense (non partecipante o contributo assente).
                        </p>
                    ) : (
                        <>
                            <div className="text-[11px] mb-2">
                                Rank: <span className="text-amber">#{reward.rank}</span>
                                · Contributo: <span className="text-amber">{reward.contribution.toLocaleString()}</span>
                            </div>
                            <ul className="space-y-1" data-testid="worldboss-report-rewards">
                                {Object.entries(reward.rewards || {}).map(([k, v]) => (
                                    <li key={k} className="text-[11px] flex justify-between border-b border-border/30 py-1">
                                        <span className="text-foreground/85">{k === "gold" ? "Oro" : k.replace(/_/g, " ")}</span>
                                        <span className="text-amber">+{v.toLocaleString()}</span>
                                    </li>
                                ))}
                            </ul>
                        </>
                    )}
                </section>
            </main>
        </div>
    );
}
