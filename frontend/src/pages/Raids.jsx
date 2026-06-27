// Phase 18 — Raids list (read-only catalog + cooldown banner + history).
// Builder + report are deferred to Phase 18.1 (out of scope for ROUND 5 MVP).
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { toast } from "sonner";

import { api, formatApiError } from "../lib/api";
import AppHeader from "../components/AppHeader";
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
                if (found.squad_type !== "raid_20") {
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

    const squadQuery = activeSquad ? `?squad_id=${activeSquad.squad_id}` : "";

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
                            <span className="text-muted-foreground">(raid 20 avventurieri)</span>
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

                {/* Catalogue */}
                <section className="space-y-4 mb-8">
                    {(catalog || []).map((r) => (
                        <article
                            key={r.slug}
                            data-testid={`raid-card-${r.slug}`}
                            className="border border-border bg-card rounded-sm p-4"
                        >
                            <header className="flex items-start justify-between gap-2 mb-2 flex-wrap">
                                <h2 className="text-sm font-semibold tracking-wider">
                                    {t(`raids.catalog.${r.slug}.name`)}
                                </h2>
                                <div className="text-[10px] tracking-widest flex items-center gap-2">
                                    <span className="border border-border px-1.5 py-0.5 rounded-sm">T{r.tier}</span>
                                    <span className="border border-border px-1.5 py-0.5 rounded-sm">R{r.tier}</span>
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
                            <p className="text-[11px] text-muted-foreground italic mb-3">
                                {t(`raids.catalog.${r.slug}.description`)}
                            </p>
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
                                    to={`/raids/build/${r.slug}${squadQuery}`}
                                    data-testid={`raid-builder-link-${r.slug}`}
                                    className={`text-[11px] tracking-widest border px-3 py-1 rounded-sm ${r.unlocked ? "border-amber/60 text-amber hover:bg-amber/10" : "border-border/40 text-muted-foreground pointer-events-none opacity-50"}`}
                                >
                                    ▶ {t("raids.builder.title")}
                                </Link>
                            </div>
                        </article>
                    ))}
                </section>

                {/* History */}
                {history.length > 0 && (
                    <section className="border-t border-border pt-4" data-testid="raids-history-section">
                        <h3 className="text-xs tracking-widest text-amber mb-2">:: {t("raids.history_title")}</h3>
                        <ul className="space-y-1.5">
                            {history.slice(0, 10).map((r) => (
                                <li key={r.id} className="text-[11px] flex items-center gap-3 flex-wrap" data-testid={`raid-history-${r.id}`}>
                                    <span className="text-muted-foreground">{r.started_at.slice(0, 10)}</span>
                                    <span>{t(`raids.catalog.${r.raid_dungeon_slug}.name`)}</span>
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

                <div className="mt-6 text-[10px] text-muted-foreground italic">
                    Phase 18 MVP — il builder party-by-party (4 × 5) sarà rilasciato in Phase 18.1.
                    Gli endpoint backend sono già attivi (POST /api/raids/start) per smoke test API.
                </div>
            </main>
        </div>
    );
}
