// FASE 9I — ADDESTRAMENTO (solo XP).
// La vecchia pagina "Addestramento e specializzazione" (ROUND 6C/6E)
// è stata sostituita: niente specializzazioni, niente respec.
// Regole server-authoritative: 2 posti, sessioni 1-24h, solo XP,
// bonus recupero +50% per chi è sotto il benchmark di gilda.

import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import AppHeader from "../components/AppHeader";
import GameImage from "../components/GameImage";
import { api, formatApiError } from "../lib/api";
import { avatarSources } from "../utils/gameAssets";
import { classLabel } from "../utils/displayLabels";

function formatRemaining(seconds) {
    const s = Math.max(0, Math.floor(seconds));
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    if (h > 0) return `${h}h ${m}m`;
    const sec = s % 60;
    return m > 0 ? `${m}m ${sec}s` : `${sec}s`;
}

function SessionCard({ session, onCancel, busy }) {
    const [remaining, setRemaining] = useState(session.remaining_seconds || 0);

    useEffect(() => {
        setRemaining(session.remaining_seconds || 0);
        const timer = setInterval(
            () => setRemaining((r) => Math.max(0, r - 1)),
            1000,
        );
        return () => clearInterval(timer);
    }, [session.id, session.remaining_seconds]);

    const total = (session.duration_hours || 1) * 3600;
    const pct = Math.min(100, Math.round(((total - remaining) / total) * 100));

    return (
        <div
            data-testid={`training-session-${session.id}`}
            className="border border-border bg-card rounded-sm p-4"
        >
            <div className="flex items-center justify-between gap-2 flex-wrap">
                <div className="font-semibold text-sm">
                    {session.adventurer_name}
                    <span className="text-muted-foreground font-normal">
                        {" "}· Lv {session.level_at_start}
                    </span>
                </div>
                {session.catchup_bonus && (
                    <span
                        data-testid="training-catchup-badge"
                        className="text-[10px] tracking-widest text-emerald-300 border border-emerald-400/50 rounded-sm px-2 py-0.5"
                    >
                        RECUPERO +50%
                    </span>
                )}
            </div>
            <div className="mt-2 grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px]">
                <div>
                    <div className="text-muted-foreground">XP/h</div>
                    <div className="font-mono">
                        {Math.floor(
                            (session.xp_per_hour || 0)
                            * (session.catchup_multiplier || 1),
                        )}
                    </div>
                </div>
                <div>
                    <div className="text-muted-foreground">XP prevista</div>
                    <div className="font-mono text-amber">{session.expected_xp}</div>
                </div>
                <div>
                    <div className="text-muted-foreground">Durata</div>
                    <div className="font-mono">{session.duration_hours}h</div>
                </div>
                <div>
                    <div className="text-muted-foreground">Tempo residuo</div>
                    <div
                        className="font-mono"
                        data-testid={`training-remaining-${session.id}`}
                    >
                        {remaining > 0 ? formatRemaining(remaining) : "completata…"}
                    </div>
                </div>
            </div>
            <div className="mt-2 h-2 bg-background border border-border rounded-sm overflow-hidden">
                <div className="h-full bg-amber/80" style={{ width: `${pct}%` }} />
            </div>
            <div className="mt-3 flex justify-end">
                <button
                    type="button"
                    disabled={busy}
                    onClick={() => onCancel(session)}
                    data-testid={`training-cancel-${session.id}`}
                    className="text-[10px] tracking-widest border border-border text-muted-foreground px-2 py-1 rounded-sm hover:text-red-300 hover:border-red-400/50 disabled:opacity-50"
                >
                    INTERROMPI (XP per le ore complete)
                </button>
            </div>
        </div>
    );
}

export default function Training() {
    const [overview, setOverview] = useState(null);
    const [adventurers, setAdventurers] = useState([]);
    const [selectedId, setSelectedId] = useState("");
    const [preview, setPreview] = useState(null);
    const [hours, setHours] = useState(8);
    const [busy, setBusy] = useState(false);
    const [loading, setLoading] = useState(true);

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const [ov, advs] = await Promise.all([
                api.get("/training"),
                api.get("/adventurers"),
            ]);
            setOverview(ov.data);
            setAdventurers(advs.data?.adventurers || []);
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { load(); }, [load]);

    useEffect(() => {
        if (!selectedId) { setPreview(null); return; }
        let cancelled = false;
        api.get(`/training/preview/${selectedId}`)
            .then((r) => { if (!cancelled) setPreview(r.data); })
            .catch(() => { if (!cancelled) setPreview(null); });
        return () => { cancelled = true; };
    }, [selectedId]);

    const candidates = useMemo(
        () => adventurers.filter(
            (a) => a.is_available && a.class_slug && (a.level || 1) < 80,
        ),
        [adventurers],
    );

    const capacity = overview?.capacity || { used: 0, max: 2 };
    const slotsFree = capacity.used < capacity.max;
    const expectedXp = preview
        ? Math.floor((preview.xp_per_hour_effective || 0) * hours)
        : null;

    const handleStart = async () => {
        if (!selectedId || busy) return;
        setBusy(true);
        try {
            await api.post("/training/start", {
                adventurer_id: selectedId,
                duration_hours: hours,
            });
            toast.success("Addestramento avviato!");
            setSelectedId("");
            setPreview(null);
            await load();
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setBusy(false);
        }
    };

    const handleCancel = async (session) => {
        if (busy) return;
        setBusy(true);
        try {
            const { data } = await api.post(`/training/${session.id}/cancel`);
            if (data.completed) {
                toast.success(`Sessione completata: +${data.xp_awarded} XP`);
            } else {
                toast.success(
                    `Sessione interrotta: +${data.xp_awarded} XP `
                    + `(${data.hours_credited} ore complete)`,
                );
            }
            await load();
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setBusy(false);
        }
    };

    return (
        <div className="min-h-screen bg-background text-foreground term-grid-bg">
            <AppHeader subtitleKey="nav.brand_subtitle_dashboard" />
            <main className="max-w-4xl mx-auto px-4 sm:px-6 py-6">
                <div className="mb-4 flex items-baseline justify-between gap-3 flex-wrap">
                    <div>
                        <h1
                            data-testid="training-title"
                            className="text-xl sm:text-2xl font-semibold tracking-tight font-fantasy"
                        >
                            Addestramento
                        </h1>
                        <p className="text-xs text-muted-foreground mt-1 max-w-xl">
                            Due posti, sessioni fino a 24 ore, SOLO esperienza:
                            niente oro, oggetti o reagenti. Utile per far
                            recuperare le retrovie, ma i dungeon e i raid
                            restano la via principale. Chi è sotto il livello
                            dei tuoi campioni si addestra il 50% più in fretta.
                        </p>
                    </div>
                    <div
                        data-testid="training-capacity"
                        className="text-[11px] tracking-widest text-muted-foreground"
                    >
                        POSTI{" "}
                        <span className={slotsFree ? "text-emerald-400/90" : "text-red-300"}>
                            {capacity.used}/{capacity.max}
                        </span>
                        {overview?.benchmark_level != null && (
                            <>
                                {" · "}BENCHMARK GILDA{" "}
                                <span className="text-amber">Lv {overview.benchmark_level}</span>
                            </>
                        )}
                    </div>
                </div>

                {loading && (
                    <div className="text-xs text-muted-foreground border border-border bg-card rounded-sm p-6">
                        Caricamento<span className="caret-blink" />
                    </div>
                )}

                {!loading && (
                    <>
                        {/* Sessioni attive */}
                        <section className="mb-6 space-y-3" data-testid="training-active-sessions">
                            {(overview?.sessions || []).length === 0 ? (
                                <div className="border border-border bg-card rounded-sm p-4 text-xs text-muted-foreground italic">
                                    Nessuna sessione in corso. La sala attende.
                                </div>
                            ) : (
                                overview.sessions.map((s) => (
                                    <SessionCard
                                        key={s.id}
                                        session={s}
                                        onCancel={handleCancel}
                                        busy={busy}
                                    />
                                ))
                            )}
                        </section>

                        {/* Nuova sessione */}
                        <section
                            className="border border-border bg-card rounded-sm p-4 mb-6"
                            data-testid="training-start-panel"
                        >
                            <div className="text-[10px] text-amber tracking-widest mb-3">
                                :: NUOVA SESSIONE
                            </div>
                            {!slotsFree ? (
                                <p className="text-xs text-muted-foreground italic">
                                    La sala è piena ({capacity.used}/{capacity.max}).
                                    Attendi la fine di una sessione.
                                </p>
                            ) : (
                                <>
                                    <div className="grid sm:grid-cols-2 gap-3">
                                        <label className="text-xs flex flex-col gap-1">
                                            <span className="text-muted-foreground">Avventuriero</span>
                                            <select
                                                data-testid="training-adventurer-select"
                                                value={selectedId}
                                                onChange={(e) => setSelectedId(e.target.value)}
                                                className="bg-secondary border border-border rounded-sm px-2 py-2"
                                            >
                                                <option value="">— scegli —</option>
                                                {candidates.map((a) => (
                                                    <option key={a.id} value={a.id}>
                                                        {a.name} · {classLabel(a.class_slug)} · Lv {a.level}
                                                    </option>
                                                ))}
                                            </select>
                                        </label>
                                        <label className="text-xs flex flex-col gap-1">
                                            <span className="text-muted-foreground">
                                                Durata: <strong>{hours}h</strong> (max 24)
                                            </span>
                                            <input
                                                type="range"
                                                min="1"
                                                max="24"
                                                value={hours}
                                                data-testid="training-hours-slider"
                                                onChange={(e) => setHours(Number(e.target.value))}
                                                className="accent-amber"
                                            />
                                        </label>
                                    </div>

                                    {preview && (
                                        <div
                                            className="mt-3 border border-border/60 rounded-sm p-3 flex items-center gap-3 flex-wrap"
                                            data-testid="training-preview"
                                        >
                                            <GameImage
                                                sources={avatarSources(
                                                    adventurers.find((a) => a.id === selectedId) || {},
                                                )}
                                                alt=""
                                                className="w-10 h-10 rounded-full border border-amber/30"
                                            />
                                            <div className="text-[11px] space-x-4">
                                                <span>
                                                    XP/h:{" "}
                                                    <strong className="font-mono">
                                                        {preview.xp_per_hour_effective}
                                                    </strong>
                                                    {preview.catchup_bonus && (
                                                        <span className="text-emerald-300"> (+50% recupero)</span>
                                                    )}
                                                </span>
                                                <span>
                                                    XP prevista:{" "}
                                                    <strong className="font-mono text-amber" data-testid="training-expected-xp">
                                                        {expectedXp}
                                                    </strong>
                                                </span>
                                                <span className="text-muted-foreground">
                                                    Benchmark: Lv {preview.benchmark_level}
                                                </span>
                                            </div>
                                        </div>
                                    )}

                                    <div className="mt-3 flex justify-end">
                                        <button
                                            type="button"
                                            data-testid="training-start-btn"
                                            disabled={!selectedId || busy}
                                            onClick={handleStart}
                                            className="text-[11px] tracking-widest font-bold border border-amber/60 text-amber px-4 py-2 rounded-sm hover:bg-amber/10 disabled:opacity-40"
                                        >
                                            {busy ? "…" : "AVVIA ADDESTRAMENTO"}
                                        </button>
                                    </div>
                                </>
                            )}
                        </section>

                        {/* Storico recente */}
                        {(overview?.recent || []).length > 0 && (
                            <section data-testid="training-recent">
                                <div className="text-[10px] text-muted-foreground tracking-widest mb-2">
                                    :: SESSIONI RECENTI
                                </div>
                                <ul className="text-xs space-y-1">
                                    {overview.recent.map((r) => (
                                        <li
                                            key={r.id}
                                            className="flex justify-between gap-2 border-b border-border/40 py-1"
                                        >
                                            <span className="truncate">
                                                {r.adventurer_name}
                                                {r.status === "cancelled" ? " · interrotta" : ""}
                                            </span>
                                            <span className="font-mono text-amber shrink-0">
                                                +{r.xp_awarded} XP
                                            </span>
                                        </li>
                                    ))}
                                </ul>
                            </section>
                        )}

                        <div className="mt-6 text-xs">
                            <Link
                                to="/adventurers"
                                className="text-muted-foreground hover:text-foreground underline-offset-2 hover:underline"
                            >
                                ← Torna al roster
                            </Link>
                        </div>
                    </>
                )}
            </main>
        </div>
    );
}
