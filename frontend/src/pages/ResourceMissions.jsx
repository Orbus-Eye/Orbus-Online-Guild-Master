// ROUND 16.3 Phase 4 — Resource missions list (in-progress + recent).
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { api, formatApiError } from "../lib/api";
import AppHeader from "../components/AppHeader";

function fmtRel(iso) {
    if (!iso) return "—";
    const ms = new Date(iso).getTime() - Date.now();
    if (ms <= 0) return "in scadenza";
    const m = Math.floor(ms / 60000);
    if (m < 60) return `${m}m`;
    return `${Math.floor(m / 60)}h${m % 60}m`;
}

const OUTCOME_LABEL = {
    completed_with_drop: { text: "Risorsa trovata!", cls: "text-green-400" },
    completed_no_drop: { text: "Missione riuscita ma nessuna risorsa", cls: "text-amber" },
    failed: { text: "Missione fallita", cls: "text-red-400" },
};

export default function ResourceMissions() {
    const [inProg, setInProg] = useState([]);
    const [recent, setRecent] = useState([]);
    const [loading, setLoading] = useState(true);

    const load = async () => {
        try {
            const { data } = await api.get("/resources/missions/mine");
            setInProg(data.in_progress || []);
            setRecent(data.recent || []);
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        load();
        const t = setInterval(load, 30000);
        return () => clearInterval(t);
    }, []);

    return (
        <div className="min-h-screen bg-background text-foreground overflow-x-hidden">
            <AppHeader />
            <main className="max-w-3xl mx-auto px-4 py-6 pb-32 md:pb-8 font-mono">
                <div className="mb-4">
                    <Link to="/world/resources"
                          className="text-[11px] text-muted-foreground hover:text-amber tracking-widest">
                        ← Torna alle Risorse
                    </Link>
                </div>
                <header className="mb-4">
                    <h1 data-testid="resource-missions-title"
                        className="text-amber text-xl tracking-widest">
                        :: Missioni di Raccolta
                    </h1>
                </header>

                {loading && (
                    <div className="text-[11px] text-muted-foreground italic">
                        :: Caricamento...
                    </div>
                )}

                {!loading && (
                    <>
                        <section className="mb-6">
                            <div className="text-[11px] text-amber tracking-widest mb-2">
                                :: In corso
                            </div>
                            {inProg.length === 0 ? (
                                <div className="text-[11px] text-muted-foreground italic">
                                    Nessuna missione in corso.
                                </div>
                            ) : (
                                <ul data-testid="resource-missions-inprogress"
                                    className="space-y-2">
                                    {inProg.map((m) => (
                                        <li key={m.id}
                                            data-testid={`mission-${m.id}`}
                                            className="border border-amber/40 bg-card/40 rounded-sm p-3">
                                            <div className="flex items-baseline justify-between">
                                                <div>
                                                    <div className="text-[13px] text-foreground">
                                                        {m.resource_slug}
                                                    </div>
                                                    <div className="text-[10px] text-muted-foreground mt-0.5">
                                                        {m.continent_slug} · squadra
                                                        Lv {(m.team_snapshot || []).reduce(
                                                            (a, x) => a + (x.level || 1), 0)}
                                                    </div>
                                                </div>
                                                <div className="text-[11px] text-amber">
                                                    {fmtRel(m.completes_at)}
                                                </div>
                                            </div>
                                            <div className="mt-2 text-[10px] text-muted-foreground">
                                                Success {m.success_chance}% · Drop {m.drop_rate}%
                                            </div>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </section>
                        <section>
                            <div className="text-[11px] text-amber tracking-widest mb-2">
                                :: Storico recente
                            </div>
                            {recent.length === 0 ? (
                                <div className="text-[11px] text-muted-foreground italic">
                                    Nessuna missione conclusa.
                                </div>
                            ) : (
                                <ul data-testid="resource-missions-recent"
                                    className="space-y-2">
                                    {recent.map((m) => {
                                        const oc = OUTCOME_LABEL[m.outcome] || {
                                            text: m.outcome || "?", cls: "text-muted-foreground",
                                        };
                                        return (
                                            <li key={m.id}
                                                className="border border-border/60 bg-card/40 rounded-sm p-3">
                                                <div className="flex items-baseline justify-between">
                                                    <div className="text-[12px] text-foreground">
                                                        {m.resource_slug}
                                                    </div>
                                                    <div className={`text-[10px] ${oc.cls}`}>
                                                        {oc.text}
                                                    </div>
                                                </div>
                                                {m.resources_obtained > 0 ? (
                                                    <div className="text-[11px] text-amber mt-1">
                                                        +{m.resources_obtained}× {m.resource_slug}
                                                    </div>
                                                ) : null}
                                            </li>
                                        );
                                    })}
                                </ul>
                            )}
                        </section>
                    </>
                )}
            </main>
        </div>
    );
}
