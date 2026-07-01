// ROUND 16.3 Phase 1 — World Boss event detail + send-team + ranking + report.
import { useCallback, useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api, formatApiError } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import AppHeader from "../components/AppHeader";
import { toast } from "sonner";

export default function WorldBossEvent() {
    const { eventId } = useParams();
    const { guild } = useAuth();
    const [event, setEvent] = useState(null);
    const [catalog, setCatalog] = useState(null);
    const [participation, setParticipation] = useState(null);
    const [ranking, setRanking] = useState([]);
    const [advs, setAdvs] = useState([]);
    const [selected, setSelected] = useState([]);
    const [busy, setBusy] = useState(false);

    const load = useCallback(async () => {
        try {
            const [{ data: det }, { data: rk }, { data: rost }] = await Promise.all([
                api.get(`/world-boss/events/${eventId}`),
                api.get(`/world-boss/events/${eventId}/ranking`),
                api.get(`/adventurers`),
            ]);
            setEvent(det.event);
            setCatalog(det.catalog);
            setParticipation(det.guild_participation);
            setRanking(rk.ranking || []);
            const rosterList = rost.adventurers || rost || [];
            setAdvs(Array.isArray(rosterList) ? rosterList : []);
        } catch (err) {
            toast.error(formatApiError(err));
        }
    }, [eventId]);
    useEffect(() => { load(); }, [load]);

    const join = async () => {
        setBusy(true);
        try {
            await api.post(`/world-boss/events/${eventId}/join`);
            toast.success("Gilda iscritta all'evento");
            await load();
        } catch (err) { toast.error(formatApiError(err)); }
        finally { setBusy(false); }
    };

    const sendTeam = async () => {
        if (selected.length !== 3) {
            toast.error("Seleziona esattamente 3 avventurieri");
            return;
        }
        setBusy(true);
        try {
            const { data } = await api.post(
                `/world-boss/events/${eventId}/send-team`,
                { adventurer_ids: selected },
            );
            toast.success(`Contributo registrato: ${data.contribution.toLocaleString()}`);
            setSelected([]);
            await load();
        } catch (err) { toast.error(formatApiError(err)); }
        finally { setBusy(false); }
    };

    const toggleAdv = (id) => {
        setSelected((s) => s.includes(id) ? s.filter((x) => x !== id) : (s.length < 3 ? [...s, id] : s));
    };

    if (!event) {
        return (
            <div className="min-h-screen bg-background text-foreground">
                <AppHeader />
                <main className="max-w-4xl mx-auto px-4 py-6 font-mono">
                    <p data-testid="worldboss-event-loading" className="text-[11px] text-muted-foreground">
                        :: Caricamento evento...
                    </p>
                </main>
            </div>
        );
    }

    const currentPhase = (catalog?.phases || []).find((p) => p.n === event.phase) || {};
    const hpRatio = event.total_hp ? Math.max(0, event.current_hp / event.total_hp) : 0;
    const availableAdvs = advs.filter((a) => a.is_available !== false
                                              && !a.expedition_in_progress);

    return (
        <div className="min-h-screen bg-background text-foreground">
            <AppHeader />
            <main className="max-w-4xl mx-auto px-4 py-6 pb-32 md:pb-8 font-mono">
                <header className="mb-6">
                    <Link to="/world-boss" className="text-[10px] text-muted-foreground hover:text-amber">
                        ← Torna alla lista
                    </Link>
                    <h1 data-testid="worldboss-event-title" className="text-amber text-xl tracking-widest mt-2">
                        :: {event.name_it || event.name_en}
                    </h1>
                    <p className="text-[11px] text-muted-foreground mt-1">
                        {catalog?.description_it}
                    </p>
                </header>

                {/* HP + fase */}
                <section className="border border-border/60 bg-card/40 rounded-sm p-4 mb-4">
                    <div className="text-amber tracking-widest text-[11px] mb-2">
                        :: Fase {event.phase} — {currentPhase.name_it || "—"}
                    </div>
                    <div className="mb-3">
                        <div className="flex justify-between text-[10px] text-muted-foreground mb-1">
                            <span>HP</span>
                            <span>
                                {(event.current_hp || 0).toLocaleString()} /
                                {" "}{(event.total_hp || 0).toLocaleString()}
                            </span>
                        </div>
                        <div className="h-3 w-full bg-secondary/40 rounded-sm overflow-hidden">
                            <div className="h-full bg-amber transition-all"
                                 style={{ width: `${hpRatio * 100}%` }} />
                        </div>
                    </div>
                    <div className="text-[10px] text-muted-foreground">
                        Minacce attive: {(event.threats || []).join(", ") || "—"}
                    </div>
                </section>

                {/* Partecipazione + invia squadra */}
                <section className="border border-border/60 bg-card/40 rounded-sm p-4 mb-4">
                    <div className="text-amber tracking-widest text-[11px] mb-2">
                        :: La tua gilda
                    </div>
                    {!participation ? (
                        <>
                            <p className="text-[11px] text-muted-foreground mb-3">
                                La tua gilda non ha ancora aderito all&apos;evento.
                            </p>
                            <button
                                data-testid="worldboss-join-btn"
                                onClick={join}
                                disabled={busy || event.status !== "active"}
                                className="w-full md:w-auto text-[11px] tracking-widest px-4 py-2.5 min-h-[44px] border border-amber text-amber rounded-sm hover:bg-amber/10 disabled:opacity-50 font-bold"
                            >
                                {busy ? "…" : "Partecipa all'evento"}
                            </button>
                        </>
                    ) : (
                        <>
                            <div className="text-[11px] text-foreground/85 mb-3">
                                Contributo totale gilda:
                                {" "}<span className="text-amber">
                                    {(participation.total_contribution || 0).toLocaleString()}
                                </span>
                                {" "}· Squadre inviate: {participation.teams_sent || 0}
                            </div>
                            {event.status === "active" && (
                                <>
                                    <div className="text-[10px] text-muted-foreground mb-2">
                                        Seleziona 3 avventurieri disponibili:
                                    </div>
                                    <ul className="space-y-1 mb-3 max-h-[40vh] overflow-y-auto">
                                        {availableAdvs.length === 0 ? (
                                            <li className="text-[11px] text-muted-foreground italic">
                                                :: Nessun avventuriero disponibile
                                            </li>
                                        ) : availableAdvs.map((a) => (
                                            <li key={a.id}>
                                                <button
                                                    data-testid={`worldboss-adv-${a.id}`}
                                                    onClick={() => toggleAdv(a.id)}
                                                    className={"w-full text-left text-[11px] px-2 py-2 min-h-[44px] border-l-2 " +
                                                        (selected.includes(a.id)
                                                            ? "border-amber bg-amber/5"
                                                            : "border-border/40 hover:border-amber/40")}
                                                >
                                                    <span className="text-foreground/90">{a.name}</span>
                                                    <span className="text-[10px] text-muted-foreground ml-2">
                                                        {a.class_slug} · lvl {a.level}
                                                    </span>
                                                </button>
                                            </li>
                                        ))}
                                    </ul>
                                    <button
                                        data-testid="worldboss-send-team-btn"
                                        onClick={sendTeam}
                                        disabled={busy || selected.length !== 3}
                                        className="w-full md:w-auto text-[11px] tracking-widest px-4 py-2.5 min-h-[44px] border border-amber text-amber rounded-sm hover:bg-amber/10 disabled:opacity-50 font-bold"
                                    >
                                        {busy ? "…" : `Invia squadra (${selected.length}/3)`}
                                    </button>
                                </>
                            )}
                        </>
                    )}
                </section>

                {/* Ranking */}
                <section className="border border-border/60 bg-card/40 rounded-sm p-4 mb-4">
                    <div className="text-amber tracking-widest text-[11px] mb-3">
                        :: Classifica gilde
                    </div>
                    {ranking.length === 0 ? (
                        <p className="text-[11px] text-muted-foreground italic">:: Nessuna partecipazione</p>
                    ) : (
                        <ul className="space-y-1" data-testid="worldboss-ranking">
                            {ranking.map((r) => (
                                <li key={r.guild_id} className="text-[11px] flex justify-between border-b border-border/30 py-1">
                                    <span>#{r.rank} <span className={r.guild_id === guild?.id ? "text-amber" : "text-foreground/85"}>{r.guild_name}</span></span>
                                    <span className="text-muted-foreground">
                                        {r.contribution.toLocaleString()} · {r.teams_sent} squadre
                                    </span>
                                </li>
                            ))}
                        </ul>
                    )}
                </section>

                {(event.status === "completed" || event.status === "failed") && (
                    <Link
                        to={`/world-boss/${eventId}/report`}
                        data-testid="worldboss-view-report"
                        className="inline-block w-full md:w-auto text-center text-[11px] tracking-widest px-4 py-2.5 min-h-[44px] border border-amber text-amber rounded-sm hover:bg-amber/10 font-bold"
                    >
                        Vedi Report Finale →
                    </Link>
                )}
            </main>
        </div>
    );
}
