// Phase 18.1 — Raid Report multi-party.
// Shows 4 party outcome cards + rewards + per-participant detail.
// Includes a "force complete" button (smoke) for testing past-ends-at raids.
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { toast } from "sonner";

import { api, formatApiError } from "../lib/api";
import AppHeader from "../components/AppHeader";
import { useT } from "../i18n/I18nContext";


function outcomeLabel(t, outcome) {
    if (outcome === "victory") return t("raids.report.outcome_victory");
    if (outcome === "partial") return t("raids.report.outcome_partial");
    if (outcome === "wipe") return t("raids.report.outcome_wipe");
    return outcome || "—";
}

function outcomeColor(o) {
    if (o === "victory") return "text-[#22c55e]";
    if (o === "partial") return "text-amber";
    if (o === "wipe") return "text-destructive";
    return "text-muted-foreground";
}


export default function RaidReport() {
    const { t, lang } = useT();
    const { raid_id } = useParams();
    const [raid, setRaid] = useState(null);
    const [participants, setParticipants] = useState([]);
    const [busy, setBusy] = useState(false);

    async function load() {
        try {
            const r = await api.get(`/raids/${raid_id}`);
            setRaid(r.data.raid);
            setParticipants(r.data.participants || []);
        } catch (err) {
            toast.error(formatApiError(err));
        }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    useEffect(() => { load(); }, [raid_id]);

    async function forceComplete() {
        setBusy(true);
        try {
            const r = await api.post(`/raids/${raid_id}/complete`);
            setRaid(r.data.raid);
            toast.success("Raid completed");
            load();
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setBusy(false);
        }
    }

    if (!raid) {
        return (
            <div className="min-h-screen bg-background text-foreground">
                <AppHeader />
                <main className="max-w-6xl mx-auto px-4 sm:px-6 py-6"><div className="text-xs text-muted-foreground">…</div></main>
            </div>
        );
    }

    const slug = raid.raid_dungeon_slug;
    const raidName = lang === "it" ? t(`raids.catalog.${slug}.name`) : t(`raids.catalog.${slug}.name`);
    const partiesOutcome = raid.parties_outcome || [];
    const rewards = raid.rewards || {};

    return (
        <div className="min-h-screen bg-background text-foreground">
            <AppHeader />
            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-6" data-testid="raid-report-page">
                <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
                    <h1 className="text-xs tracking-[0.3em] text-amber">
                        :: {t("raids.report.title")} — {raidName}
                    </h1>
                    <Link to="/raids" className="text-[11px] text-muted-foreground hover:underline">
                        ← /raids
                    </Link>
                </div>

                {/* Top status */}
                <section className="border border-border bg-card rounded-sm p-4 mb-4" data-testid="raid-report-summary">
                    {raid.status === "in_progress" ? (
                        <div className="space-y-2">
                            <div className="text-xs text-amber">⏳ In corso · Ends at: {raid.ends_at}</div>
                            <button
                                onClick={forceComplete}
                                disabled={busy}
                                data-testid="report-force-complete-btn"
                                className="text-[11px] border border-border px-3 py-1.5 rounded-sm hover:bg-secondary/30"
                            >
                                {t("raids.report.complete_now")}
                            </button>
                        </div>
                    ) : (
                        <div className="space-y-1">
                            <div className={`text-sm font-semibold ${outcomeColor(raid.outcome)}`} data-testid="report-outcome">
                                {outcomeLabel(t, raid.outcome)}
                            </div>
                            <div className="text-[11px]"><strong>{t("raids.report.raid_score")}:</strong> {raid.raid_score}</div>
                            <div className="text-[11px]"><strong>{t("raids.report.duration")}:</strong> {Math.round((raid.duration_seconds || 0) / 60)} min</div>
                            {/* ROUND 6B.2c — Save as squad after raid victory */}
                            {raid.outcome === "victory" && participants.length === 20 && (
                                <Link
                                    to={`/squads/new?type=raid_20&adventurer_ids=${participants.map(p => p.adventurer_id).join(",")}&suggested_name=${encodeURIComponent("Raid " + (raid.raid_name || ""))}`}
                                    data-testid="raid-report-save-as-squad-btn"
                                    className="inline-flex items-center mt-2 text-[11px] tracking-widest font-bold border border-amber/60 text-amber px-3 py-1.5 rounded-sm hover:bg-amber/10 transition-colors"
                                >
                                    💾 Salva come squadra
                                </Link>
                            )}
                        </div>
                    )}
                </section>

                {/* 4 party outcome cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
                    {partiesOutcome.map((p) => {
                        const partyParts = participants.filter((x) => x.party_idx === p.party_idx);
                        return (
                            <article
                                key={p.party_idx}
                                data-testid={`report-party-${p.party_idx}`}
                                className="border border-border bg-card rounded-sm p-3"
                            >
                                <header className="flex items-center justify-between mb-2">
                                    <span className="text-[11px] tracking-widest text-amber">PARTY {p.party_idx}</span>
                                    <span className={`text-[11px] ${p.success ? "text-[#22c55e]" : "text-destructive"}`}>
                                        {p.success ? "✔" : "✕"} {p.success_chance}%
                                    </span>
                                </header>
                                <ul className="space-y-1">
                                    {partyParts.map((pp) => (
                                        <li
                                            key={pp.id}
                                            data-testid={`participant-${pp.id}`}
                                            className="text-[10px] flex items-center justify-between gap-1"
                                        >
                                            <span className="truncate">{pp.class_snapshot || "?"} L{pp.level_snapshot}</span>
                                            <span className={pp.outcome === "survived" ? "text-[#22c55e]" : "text-muted-foreground"}>
                                                {pp.outcome === "survived"
                                                    ? `+${pp.xp_gained} XP`
                                                    : t("raids.report.fainted")}
                                            </span>
                                        </li>
                                    ))}
                                </ul>
                            </article>
                        );
                    })}
                </div>

                {/* Rewards */}
                {raid.status === "completed" && (
                    <section className="border border-amber/40 bg-amber/5 rounded-sm p-4" data-testid="raid-rewards">
                        <h3 className="text-xs tracking-widest text-amber mb-2">:: {t("raids.report.rewards_label")}</h3>
                        <ul className="space-y-1 text-[11px]">
                            <li>{t("raids.report.gold_total")}: <strong>{rewards.gold_total ?? 0} g</strong></li>
                            <li>{t("raids.report.xp_per_member")}: <strong>{rewards.xp_per_member ?? 0}</strong></li>
                            <li>{t("raids.report.dragon_essence_drop")}: <strong>{rewards.dragon_essence_count ?? 0}</strong></li>
                        </ul>
                    </section>
                )}
            </main>
        </div>
    );
}
