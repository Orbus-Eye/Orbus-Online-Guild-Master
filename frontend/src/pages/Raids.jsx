import RaidCountdown from "../components/RaidCountdown";  // ROUND 16.5.1 B.4 UI
// Builder + report are deferred to Phase 18.1 (out of scope for ROUND 5 MVP).
import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { toast } from "sonner";

import { api, formatApiError } from "../lib/api";
import AppHeader from "../components/AppHeader";
import GameImage from "../components/GameImage";
import { raidImageSources } from "../utils/gameAssets";
import OverCapBanner from "../components/OverCapBanner";
import { useT } from "../i18n/I18nContext";

function CountdownPill({ seconds }) {
    const [remaining, setRemaining] = useState(seconds || 0);
    useEffect(() => {
        setRemaining(seconds || 0);
        if (!seconds || seconds <= 0) return;
        const t = setInterval(() => setRemaining((r) => Math.max(0, r - 1)), 1000);
        return () => clearInterval(t);
    }, [seconds]);
    if (remaining <= 0) return null;
    const mm = String(Math.floor(remaining / 60)).padStart(2, "0");
    const ss = String(remaining % 60).padStart(2, "0");
    return (
        <div
            className="text-xs text-amber border border-amber/40 bg-amber/10 px-3 py-2 rounded-sm mb-4"
            data-testid="raids-cooldown-banner"
        >
            ⏳ {mm}:{ss}
        </div>
    );
}


export default function Raids() {
    const { t, lang: _lang } = useT();
    const [searchParams, setSearchParams] = useSearchParams();
    const squadIdParam = searchParams.get("squad_id") || "";
    const [activeSquad, setActiveSquad] = useState(null);
    const [catalog, setCatalog] = useState(null);
    const [history, setHistory] = useState([]);
    const [cooldown, setCooldown] = useState(0);
    const [loading, setLoading] = useState(true);
    // FASE 1.5 — PULISCI report raid (conferma a due step, come Spedizioni).
    const [confirmClear, setConfirmClear] = useState(false);
    const [clearBusy, setClearBusy] = useState(false);
    const confirmTimerRef = useRef(null);

    const doClearReports = async () => {
        if (!confirmClear) {
            setConfirmClear(true);
            clearTimeout(confirmTimerRef.current);
            confirmTimerRef.current = setTimeout(
                () => setConfirmClear(false), 5000,
            );
            return;
        }
        clearTimeout(confirmTimerRef.current);
        setClearBusy(true);
        try {
            const { data } = await api.post("/raids/reports/clear");
            toast.success(`Rapporti raid puliti: ${data.cleared}`);
            setConfirmClear(false);
            await load();
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setClearBusy(false);
        }
    };

    async function load() {
        try {
            const [c, h] = await Promise.all([
                api.get("/raids/catalog"),
                api.get("/raids"),
            ]);
            setCatalog(c.data.raid_dungeons);
            setCooldown(c.data.cooldown_seconds_remaining || 0);
            setHistory(h.data.raids || []);
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => { load(); }, []);

    // ROUND 6A.2c — fetch the saved squad referenced by ?squad_id.
    // ROUND 6A.2c.fix — fetch ALL squads (not only raid_20) so we can detect
    // cross-type IDs and surface an explicit Italian toast, mirroring the
    // Dungeons.jsx guard.
    useEffect(() => {
        if (!squadIdParam) { setActiveSquad(null); return; }
        let cancelled = false;
        api.get("/squads")
            .then(({ data }) => {
                if (cancelled) return;
                const found = (data.squads || []).find((s) => s.squad_id === squadIdParam);
                if (!found) {
                    toast.warning(
                        "Squadra non trovata. La squadra potrebbe essere stata archiviata.",
                    );
                    setActiveSquad(null);
                    setSearchParams({}, { replace: true });
                    return;
                }
                if (!found.squad_type.startsWith("raid_")) {
                    toast.warning(
                        "Questa squadra è per dungeon. Vai alla pagina Dungeon.",
                    );
                    setActiveSquad(null);
                    setSearchParams({}, { replace: true });
                    return;
                }
                setActiveSquad(found);
            })
            .catch(() => { if (!cancelled) toast.error("Errore caricamento squadra"); });
        return () => { cancelled = true; };
    }, [squadIdParam, setSearchParams]);

    const clearSquadFilter = () => {
        setActiveSquad(null);
        const next = new URLSearchParams(searchParams);
        next.delete("squad_id");
        setSearchParams(next, { replace: true });
    };

    return (
        <div className="min-h-screen bg-background text-foreground">
            <AppHeader />
            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-6" data-testid="raids-page">
                <OverCapBanner source="raids" />
                <h1 className="text-xs tracking-[0.3em] text-amber mb-4" data-testid="raids-title">
                    :: {t("raids.title", "RAID")}
                </h1>

                <CountdownPill seconds={cooldown} />

                {/* ROUND 6A.2c — Squad context banner */}
                {activeSquad && (
                    <div
                        data-testid="raids-squad-banner"
                        className="border border-amber/40 bg-amber/10 rounded-sm px-4 py-3 mb-4 flex items-center justify-between gap-3 flex-wrap"
                    >
                        <div className="text-xs text-amber">
                            <span className="tracking-widest">▶ Stai usando la squadra:</span>{" "}
                            <strong data-testid="raids-squad-banner-name">{activeSquad.name}</strong>{" "}
                            <span className="text-muted-foreground">
                                ({activeSquad.adventurer_ids.length} avventurieri)
                            </span>
                        </div>
                        <button
                            type="button"
                            data-testid="raids-squad-clear"
                            onClick={clearSquadFilter}
                            className="text-[11px] tracking-widest border border-amber/60 text-amber px-3 py-1 rounded-sm hover:bg-amber hover:text-background transition-colors"
                        >
                            ✕ Annulla filtro
                        </button>
                    </div>
                )}

                {loading && <div className="text-xs text-muted-foreground">…</div>}

                {/* ROUND 16.5.1 B.4 UI — Raid in corso con countdown live */}
                {history.filter((r) => r.status === "in_progress").length > 0 && (
                    <section className="border border-amber/40 bg-amber/5 rounded-sm px-4 py-3 mb-6"
                             data-testid="raids-active-section">
                        <h3 className="text-xs tracking-widest text-amber mb-2">
                            :: RAID IN CORSO
                        </h3>
                        <ul className="space-y-2">
                            {history.filter((r) => r.status === "in_progress")
                              .map((r) => (
                                <li key={r.id}
                                    className="text-[11px] flex items-center gap-3 flex-wrap"
                                    data-testid={`raid-active-${r.id}`}>
                                    <span>{r.raid_name_it || t(`raids.catalog.${r.raid_dungeon_slug}.name`)}</span>
                                    <RaidCountdown endsAt={r.ends_at}
                                                   remainingSeconds={r.remaining_seconds}
                                                   status={r.status}
                                                   testid={`raid-active-countdown-${r.id}`} />
                                    <Link to={`/raids/${r.id}/report`}
                                          className="text-amber hover:underline ml-auto"
                                          data-testid={`raid-active-link-${r.id}`}>
                                        dettaglio →
                                    </Link>
                                </li>
                              ))}
                        </ul>
                    </section>
                )}

                {/* Catalogue */}
                <section className="space-y-4 mb-8">
                    {(catalog || []).map((r) => {
                        const itName = r.name_it || t(`raids.catalog.${r.slug}.name`);
                        const itDesc = r.description_it || t(`raids.catalog.${r.slug}.description`);
                        const minLvl = r.min_adventurer_level || 1;
                        const matchingSquad = activeSquad
                            && activeSquad.squad_type === `raid_${r.min_roster_size}`;
                        const cardSquadQuery = matchingSquad
                            ? `?squad_id=${activeSquad.squad_id}`
                            : "";
                        return (
                        <article
                            key={r.slug}
                            data-testid={`raid-card-${r.slug}`}
                            className="border border-border bg-card rounded-sm p-4 card-fantasy"
                        >
                            {/* FASE 4 — banner del raid */}
                            <div className="-mx-4 -mt-4 mb-3 h-28 overflow-hidden">
                                <GameImage
                                    sources={raidImageSources(r.slug)}
                                    alt=""
                                    className={
                                        "w-full h-full object-cover " +
                                        (r.unlocked ? "" : "grayscale opacity-70")
                                    }
                                />
                            </div>
                            <header className="flex items-start justify-between gap-2 mb-2 flex-wrap">
                                <h2 className="text-sm font-semibold tracking-wider">
                                    {itName}
                                </h2>
                                <div className="text-[10px] tracking-widest flex items-center gap-2 flex-wrap">
                                    <span className="border border-border px-1.5 py-0.5 rounded-sm">T{r.tier}</span>
                                    {r.is_new && (
                                        <span
                                            className="border border-emerald-500/60 text-emerald-400 px-1.5 py-0.5 rounded-sm"
                                            data-testid={`raid-new-badge-${r.slug}`}
                                            title="Contenuto introdotto nel Round 11.3"
                                        >
                                            NUOVO
                                        </span>
                                    )}
                                    {r.is_void_undead && (
                                        <span
                                            className="border border-violet-500/60 text-violet-300 px-1.5 py-0.5 rounded-sm"
                                            data-testid={`raid-void-badge-${r.slug}`}
                                            title="Lore: Vuoto / Non-Morti"
                                        >
                                            ✦ VUOTO
                                        </span>
                                    )}
                                    {/* ROUND 13a Fix 1 — Lv min badge sempre visibile, mutato per Lv1 */}
                                    <span
                                        className={`px-1.5 py-0.5 rounded-sm border ${minLvl > 1 ? "border-amber-500/50 text-amber-400" : "border-border/50 text-muted-foreground"}`}
                                        data-testid={`raid-min-level-badge-${r.slug}`}
                                        title={`Livello minimo richiesto per ogni avventuriero: Lv ${minLvl}`}
                                    >
                                        Lv min: {minLvl}
                                    </span>
                                    {!r.unlocked && (
                                        <span
                                            className="border border-amber/50 text-amber px-1.5 py-0.5 rounded-sm"
                                            data-testid={`raid-locked-${r.slug}`}
                                        >
                                            🔒 LOCKED
                                        </span>
                                    )}
                                </div>
                            </header>
                            {r.boss_name && (
                                <div className="text-[11px] text-amber-400/80 mb-1" data-testid={`raid-boss-${r.slug}`}>
                                    Boss: <strong>{r.boss_name}</strong>
                                </div>
                            )}
                            <p className="text-[11px] text-muted-foreground italic mb-2" data-testid={`raid-desc-${r.slug}`}>
                                {itDesc}
                            </p>
                            {r.narrative_hook && (
                                <p
                                    className="text-[11px] italic text-amber-400/80 mb-3 border-l-2 border-amber-500/40 pl-2"
                                    data-testid={`raid-hook-${r.slug}`}
                                >
                                    &laquo;{r.narrative_hook}&raquo;
                                </p>
                            )}
                            <dl className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] mb-2">
                                <div><dt className="text-muted-foreground">Power</dt><dd>{r.recommended_power_combined}</dd></div>
                                <div><dt className="text-muted-foreground">Roster</dt>
                                    <dd data-testid={`raid-roster-${r.slug}`}>
                                        {r.guild_roster_count}/{r.min_roster_size}
                                    </dd>
                                </div>
                                <div><dt className="text-muted-foreground">Durata</dt><dd>{Math.round(r.base_duration_seconds / 60)} min</dd></div>
                                <div><dt className="text-muted-foreground">Reward</dt><dd>{r.base_gold_reward}g · {r.base_xp_per_member} XP/adv</dd></div>
                            </dl>
                            {r.gate_reason && (
                                <div className="text-[11px] text-amber italic">
                                    {r.gate_reason === "roster_too_small"
                                        ? t("raids.gate.roster_too_small", { need: r.min_roster_size, have: r.guild_roster_count })
                                        : t("raids.gate.max_team_power_too_low", { need: r.gate?.min_max_team_power_ever || "?", have: r.guild_max_team_power_ever })}
                                </div>
                            )}
                            {/* Phase 18.1 — Builder + last report links */}
                            <div className="mt-3 flex items-center gap-2 flex-wrap">
                                <Link
                                    to={`/raids/build/${r.slug}${cardSquadQuery}`}
                                    data-testid={`raid-builder-link-${r.slug}`}
                                    className={`text-[11px] tracking-widest border px-3 py-1 rounded-sm ${r.unlocked ? "border-amber/60 text-amber hover:bg-amber/10" : "border-border/40 text-muted-foreground pointer-events-none opacity-50"}`}
                                >
                                    ▶ {t("raids.builder.title")}
                                </Link>
                            </div>
                        </article>
                        );
                    })}
                    {/* FASE 1.9 — visibilità progressiva: accenno ai raid
                        ancora nascosti, senza spoiler. */}
                    {(catalog?.[0]?.hidden_upcoming_count > 0) && (
                        <div
                            data-testid="raids-hidden-hint"
                            className="text-[11px] text-muted-foreground italic text-center"
                        >
                            🔮 Altri {catalog[0].hidden_upcoming_count} raid attendono
                            oltre l&apos;orizzonte. Supera la prossima sfida per svelarli.
                        </div>
                    )}
                </section>

                {/* History */}
                {history.length > 0 && (
                    <section className="border-t border-border pt-4" data-testid="raids-history-section">
                        <div className="flex items-center justify-between gap-3 mb-2 flex-wrap">
                            <h3 className="text-xs tracking-widest text-amber">:: {t("raids.history_title")}</h3>
                            {history.some((r) => r.status !== "in_progress") && (
                                <button
                                    type="button"
                                    data-testid="btn-clear-raid-reports"
                                    onClick={doClearReports}
                                    disabled={clearBusy}
                                    className={`text-[10px] tracking-widest border rounded-sm px-2 py-1 ${
                                        confirmClear
                                            ? "border-red-500/70 text-red-400 hover:bg-red-500/10"
                                            : "border-border text-muted-foreground hover:bg-secondary"
                                    }`}
                                >
                                    {clearBusy ? "…" : confirmClear ? "⚠ CONFERMI LA PULIZIA?" : "🧹 PULISCI"}
                                </button>
                            )}
                        </div>
                        <ul className="space-y-1.5">
                            {history.slice(0, 10).map((r) => (
                                <li key={r.id} className="text-[11px] flex items-center gap-3 flex-wrap" data-testid={`raid-history-${r.id}`}>
                                    <span className="text-muted-foreground">{r.started_at.slice(0, 10)}</span>
                                    <span>{r.raid_name_it || t(`raids.catalog.${r.raid_dungeon_slug}.name`)}</span>
                                    <span className={r.outcome === "victory" ? "text-[#22c55e]" : r.outcome === "partial" ? "text-amber" : "text-destructive"}>
                                        {r.outcome || r.status}
                                    </span>
                                    <span>score {r.raid_score}</span>
                                    <Link
                                        to={`/raids/${r.id}/report`}
                                        className="text-amber hover:underline ml-auto"
                                        data-testid={`raid-report-link-${r.id}`}
                                    >
                                        report →
                                    </Link>
                                </li>
                            ))}
                        </ul>
                    </section>
                )}
                {history.length === 0 && !loading && (
                    <section
                        className="border-t border-border pt-4"
                        data-testid="raids-history-empty"
                    >
                        <h3 className="text-xs tracking-widest text-amber mb-2">
                            :: NESSUN RAID COMPLETATO
                        </h3>
                        <p className="text-[12px] text-muted-foreground italic">
                            Non hai ancora affrontato un raid. Il primo richiede 10
                            avventurieri in due party da cinque; i raid successivi
                            arrivano a 15, 20 e 40 membri.
                        </p>
                    </section>
                )}

                <div className="mt-6 text-[10px] text-muted-foreground italic">
                    Ogni raid usa party da cinque e una formazione coerente con il
                    proprio contratto: 10, 15, 20 oppure 40 avventurieri.
                </div>
            </main>
        </div>
    );
}
