// ROUND 12.B — Page /seasons. Hero + my participation + reward placeholder + history.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import AppHeader from "../components/AppHeader";
import { Button } from "../components/ui/button";

const API = (process.env.REACT_APP_BACKEND_URL || "") + "/api";
const cfg = { withCredentials: true, timeout: 12_000 };

function daysLeft(iso) {
    if (!iso) return 0;
    const ms = new Date(iso).getTime() - Date.now();
    return Math.max(0, Math.floor(ms / 86400_000));
}

export default function Seasons() {
    const [current, setCurrent] = useState(null);
    const [seasons, setSeasons] = useState([]);
    const [participation, setParticipation] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        let cancelled = false;
        async function load() {
            try {
                const [curRes, listRes] = await Promise.all([
                    axios.get(`${API}/seasons/current`, cfg).catch((e) => {
                        if (e?.response?.status === 404) return { data: { season: null } };
                        throw e;
                    }),
                    axios.get(`${API}/seasons`, cfg).catch(() => ({ data: { seasons: [] } })),
                ]);
                if (cancelled) return;
                setCurrent(curRes.data.season || null);
                setSeasons(listRes.data.seasons || []);
                // Optional peek: defense team to surface rating (best-effort)
                try {
                    const dt = await axios.get(`${API}/pvp/defense-team`, cfg);
                    if (!cancelled) setParticipation(dt.data || null);
                } catch (e) {
                    // ROUND 11.4b — non-fatal peek; user might not be authed.
                    console.error("[Seasons] peek defense-team failed:", e?.response?.status);
                }
            } catch (err) {
                console.error("[Seasons] load failed:", err);
                if (!cancelled) setError(err?.response?.data?.detail?.user_message || "Caricamento fallito");
            } finally {
                if (!cancelled) setLoading(false);
            }
        }
        load();
        return () => { cancelled = true; };
    }, []);

    return (
        <div className="min-h-screen bg-background">
            <AppHeader />
            <main className="max-w-5xl mx-auto px-4 sm:px-6 py-6">
                <h1 className="text-2xl sm:text-3xl tracking-[0.2em] text-amber font-light mb-2" data-testid="seasons-title">
                    :: Stagioni delle Arene
                </h1>
                <p className="text-xs text-muted-foreground mb-6">
                    Stagioni cicliche con classifiche dedicate. Solo ricompense cosmetiche.
                </p>

                {loading && (
                    <p data-testid="seasons-loading" className="text-sm text-muted-foreground italic">
                        Caricamento stagione…
                    </p>
                )}
                {error && !loading && (
                    <p data-testid="seasons-error" className="text-sm text-red-400">{error}</p>
                )}

                {!loading && !current && !error && (
                    <div data-testid="seasons-empty" className="border border-dashed border-border rounded-sm p-6 text-center">
                        <p className="text-sm text-muted-foreground">Nessuna stagione attiva al momento. Stagione in arrivo.</p>
                    </div>
                )}

                {current && (
                    <>
                        {/* HERO */}
                        <section data-testid="season-hero" className="border border-amber/30 bg-card rounded-sm p-5 mb-5">
                            <div className="flex items-start justify-between gap-3 flex-wrap">
                                <div>
                                    <div className="text-[10px] tracking-[0.3em] text-muted-foreground uppercase">Stagione attuale</div>
                                    <h2 className="text-xl sm:text-2xl text-amber font-semibold mt-1" data-testid="season-name">
                                        {current.name_it}
                                    </h2>
                                    <p className="text-[11px] text-muted-foreground mt-1">
                                        Tema lore: <span className="text-foreground/90 capitalize">{current.lore_theme}</span>
                                    </p>
                                </div>
                                <div className="flex flex-col items-end gap-1">
                                    <span data-testid="season-status" className="text-[10px] uppercase tracking-[0.18em] text-emerald-400 border border-emerald-400/40 rounded-sm px-2 py-0.5">
                                        {current.status === "active" ? "Attiva" : current.status}
                                    </span>
                                    <span data-testid="season-countdown" className="text-[11px] text-muted-foreground">
                                        {daysLeft(current.ends_at)} giorni rimanenti
                                    </span>
                                </div>
                            </div>

                            <div className="mt-4 flex gap-2 flex-wrap">
                                <Link to="/arena" data-testid="goto-arena-btn">
                                    <Button size="sm">Vai all&apos;Arena</Button>
                                </Link>
                                <Link
                                    data-testid="goto-leaderboard-btn"
                                    to={`/leaderboard?scope=season&season=${current.slug}&category=arena_rating`}
                                >
                                    <Button size="sm" variant="outline">Classifica stagionale</Button>
                                </Link>
                            </div>
                        </section>

                        {/* MY PARTICIPATION */}
                        {participation && participation.team && (
                            <section data-testid="season-my-participation" className="border border-border bg-card rounded-sm p-4 mb-5">
                                <h3 className="text-sm tracking-[0.25em] text-amber mb-3">:: La mia partecipazione</h3>
                                <div className="flex items-center gap-3 flex-wrap text-xs">
                                    <span className="text-muted-foreground">Squadra difensiva: <strong className="text-foreground">configurata</strong></span>
                                    <span className="text-muted-foreground">Avventurieri: <strong className="text-foreground">{participation.team.adventurer_ids?.length || 0}/5</strong></span>
                                </div>
                            </section>
                        )}

                        {/* REWARD PREVIEW */}
                        <section data-testid="season-rewards" className="border border-border bg-card rounded-sm p-4 mb-5">
                            <h3 className="text-sm tracking-[0.25em] text-amber mb-2">:: Reward di fine stagione</h3>
                            <p className="text-[12px] text-foreground/85">
                                Le ricompense sono <strong>esclusivamente cosmetiche</strong>: badge profilo, cornici nome,
                                titoli onorifici, animazioni del trofeo. <strong className="text-amber/90">Nessun bonus potere</strong>,
                                nessun oro, nessun XP, nessun item competitivo.
                            </p>
                            <p className="mt-2 text-[11px] text-muted-foreground italic">
                                Anteprima dettagliata in arrivo nelle prossime build.
                            </p>
                        </section>

                        {/* HISTORY */}
                        <section data-testid="seasons-history" className="border border-border bg-card rounded-sm p-4">
                            <h3 className="text-sm tracking-[0.25em] text-amber mb-3">:: Storico stagioni</h3>
                            {seasons.filter((s) => s.status !== "active").length === 0 ? (
                                <p data-testid="seasons-history-empty" className="text-[11px] text-muted-foreground italic">
                                    Nessuna stagione conclusa ancora. La cronologia comincerà alla fine della preseason.
                                </p>
                            ) : (
                                <ul className="space-y-2">
                                    {seasons.filter((s) => s.status !== "active").map((s) => (
                                        <li key={s.season_id} className="flex items-center justify-between text-xs">
                                            <span>{s.name_it} ({s.lore_theme})</span>
                                            <span className="text-muted-foreground">{s.status}</span>
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
