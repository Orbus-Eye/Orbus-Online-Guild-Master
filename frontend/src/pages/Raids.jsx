// Phase 18 — Raids list (read-only catalog + cooldown banner + history).
// Builder + report are deferred to Phase 18.1 (out of scope for ROUND 5 MVP).
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";

import { api, formatApiError } from "../lib/api";
import AppHeader from "../components/AppHeader";
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
    const { t } = useT();
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

    return (
        <div className="min-h-screen bg-background text-foreground">
            <AppHeader />
            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-6" data-testid="raids-page">
                <h1 className="text-xs tracking-[0.3em] text-amber mb-4" data-testid="raids-title">
                    :: {t("raids.title", "RAID")}
                </h1>

                <CountdownPill seconds={cooldown} />

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
                                    {r.name_it || r.name}
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
                                {r.description_it || r.description}
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
                                        ? `Servono ${r.min_roster_size} avventurieri (hai ${r.guild_roster_count})`
                                        : `Picco team_power richiesto: ${r.gate?.min_max_team_power_ever || "?"} (tuo: ${r.guild_max_team_power_ever})`}
                                </div>
                            )}
                        </article>
                    ))}
                </section>

                {/* History */}
                {history.length > 0 && (
                    <section className="border-t border-border pt-4" data-testid="raids-history-section">
                        <h3 className="text-xs tracking-widest text-amber mb-2">:: STORIA</h3>
                        <ul className="space-y-1.5">
                            {history.slice(0, 10).map((r) => (
                                <li key={r.id} className="text-[11px] flex items-center gap-3 flex-wrap" data-testid={`raid-history-${r.id}`}>
                                    <span className="text-muted-foreground">{r.started_at.slice(0, 10)}</span>
                                    <span>{r.raid_dungeon_slug}</span>
                                    <span className={r.outcome === "victory" ? "text-[#22c55e]" : r.outcome === "partial" ? "text-amber" : "text-destructive"}>
                                        {r.outcome || r.status}
                                    </span>
                                    <span>score {r.raid_score}</span>
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
