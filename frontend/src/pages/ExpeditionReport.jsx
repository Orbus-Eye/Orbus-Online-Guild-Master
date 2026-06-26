import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { api, formatApiError } from "../lib/api";
import { useT } from "../i18n/I18nContext";
import { toast } from "sonner";
import AppHeader from "../components/AppHeader";
import { Button } from "../components/ui/button";
import { useAuth } from "../context/AuthContext";
import ExpeditionExplainer from "../components/ExpeditionExplainer";

const RARITY_COLOR = {
    Common: "#9ca3af",
    Uncommon: "#22c55e",
    Rare: "#3b82f6",
    Epic: "#a855f7",
};

const RarityBadge = ({ rarity }) => (
    <span
        className="inline-block text-[10px] tracking-widest border px-1.5 py-0.5 rounded-sm"
        style={{
            color: RARITY_COLOR[rarity] || RARITY_COLOR.Common,
            borderColor: (RARITY_COLOR[rarity] || RARITY_COLOR.Common) + "55",
        }}
    >
        {rarity?.toUpperCase()}
    </span>
);

import { translateDungeonName } from "../i18n/contentMap";
import { formatDateTime as formatDate } from "../utils/dateFormat";

const SummaryBadge = ({ summary, status }) => {
    if (status === "in_progress") {
        return (
            <span className="inline-block text-xs tracking-widest border border-amber/55 text-amber px-2 py-1 rounded-sm">
                IN PROGRESS
            </span>
        );
    }
    if (summary === "Success") {
        return (
            <span
                data-testid="report-success-badge"
                className="inline-block text-xs tracking-widest border border-[#22c55e]/55 text-[#22c55e] px-2 py-1 rounded-sm"
            >
                SUCCESS
            </span>
        );
    }
    if (summary === "Failed") {
        return (
            <span
                data-testid="report-failed-badge"
                className="inline-block text-xs tracking-widest border border-[#ef4444]/55 text-[#ef4444] px-2 py-1 rounded-sm"
            >
                FAILED
            </span>
        );
    }
    return null;
};

const Cell = ({ label, value, testid, accent = false }) => (
    <div className="border border-border bg-card rounded-sm p-4">
        <div className="text-[10px] text-muted-foreground tracking-widest mb-2">
            {label}
        </div>
        <div data-testid={testid} className={`text-xl font-semibold ${accent ? "text-amber" : ""}`}>
            {value}
        </div>
    </div>
);

export default function ExpeditionReport() {
    const { t, tContent, lang } = useT();
    const { id } = useParams();
    const navigate = useNavigate();
    const { refreshGuild } = useAuth();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [replayInfo, setReplayInfo] = useState(null); // {can_replay, cannot_replay_reason, expeditionId} | null
    const [replayBusy, setReplayBusy] = useState(false);
    const pollRef = useRef(null);

    const fetchOne = useCallback(async () => {
        try {
            const { data } = await api.get(`/expeditions/${id}`);
            setData(data);
        } catch (err) {
            toast.error(formatApiError(err));
            setData({ notFound: true });
        } finally {
            setLoading(false);
        }
    }, [id]);

    const fetchReplayEligibility = useCallback(async () => {
        try {
            const { data: lc } = await api.get("/expeditions/last-completed");
            // Only show the replay action when this report IS the last-completed run
            if (lc?.expedition?.id === id) {
                setReplayInfo({
                    can_replay: !!lc.can_replay,
                    cannot_replay_reason: lc.cannot_replay_reason,
                    expeditionId: id,
                });
            } else {
                setReplayInfo(null);
            }
        } catch {
            setReplayInfo(null);
        }
    }, [id]);

    const handleReplay = async () => {
        if (replayBusy) return;
        setReplayBusy(true);
        try {
            const { data } = await api.post("/expeditions/replay-last");
            toast.success(t("expedition_report_page.replay_toast", { name: data.expedition.dungeon_name }));
            await refreshGuild();
            navigate(`/expeditions/${data.expedition.id}`);
        } catch (err) {
            toast.error(formatApiError(err));
            fetchReplayEligibility();
        } finally {
            setReplayBusy(false);
        }
    };

    useEffect(() => {
        fetchOne();
    }, [fetchOne]);

    // If still in_progress, poll every 5s until completed; then refresh guild gold counter
    useEffect(() => {
        if (pollRef.current) clearInterval(pollRef.current);
        if (data?.expedition?.status === "in_progress") {
            pollRef.current = setInterval(fetchOne, 5000);
        } else if (data?.expedition?.status === "completed") {
            refreshGuild();
            // Phase 8: check whether this report is the last-completed → show replay
            fetchReplayEligibility();
        }
        return () => clearInterval(pollRef.current);
    }, [data?.expedition?.status, fetchOne, refreshGuild, fetchReplayEligibility]);

    if (loading) {
        return (
            <div className="min-h-screen bg-background">
                <AppHeader subtitleKey="expedition_report_page.brand_subtitle" />
                <main className="max-w-4xl mx-auto px-4 sm:px-6 py-8 text-xs text-muted-foreground">
                    loading<span className="caret-blink" />
                </main>
            </div>
        );
    }

    if (!data || data.notFound || !data.expedition) {
        return (
            <div className="min-h-screen bg-background">
                <AppHeader subtitleKey="expedition_report_page.brand_subtitle" />
                <main className="max-w-4xl mx-auto px-4 sm:px-6 py-12 text-center">
                    <div className="text-amber text-xs tracking-widest mb-2">:: NOT FOUND</div>
                    <p className="text-sm text-muted-foreground mb-4">
                        That expedition is not in your guild log.
                    </p>
                    <Link to="/expeditions">
                        <Button className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm">
                            ← back to expeditions
                        </Button>
                    </Link>
                </main>
            </div>
        );
    }

    const { expedition: e, members, loot_items, report_summary, report_steps } = data;
    const isDone = e.status === "completed";

    return (
        <div className="min-h-screen bg-background text-foreground term-grid-bg">
            <AppHeader subtitleKey="expedition_report_page.brand_subtitle" />

            <main className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
                <Link to="/expeditions" className="text-xs text-muted-foreground hover:text-foreground" data-testid="back-to-expeditions">
                    ← back to expeditions
                </Link>

                <div className="flex items-start justify-between gap-3 mt-4 mb-6 flex-wrap">
                    <div>
                        <div className="text-xs text-amber tracking-widest mb-2">
                            :: AFTER-ACTION REPORT
                        </div>
                        <h1 data-testid="report-dungeon-name" className="text-3xl font-semibold tracking-tight">
                            {translateDungeonName(tContent, e.dungeon_name, lang)}
                        </h1>
                        <div className="text-xs text-muted-foreground mt-1">
                            {isDone
                                ? t("expedition_report_page.completed_at", { at: formatDate(e.completed_at, lang) })
                                : t("expedition_report_page.started_at", { at: formatDate(e.started_at, lang) })}
                        </div>
                    </div>
                    <div className="flex items-center gap-3 flex-wrap">
                        <SummaryBadge summary={e.result_summary} status={e.status} />
                        {e.is_replay && (
                            <span
                                className="inline-block text-[10px] tracking-widest border border-amber/55 text-amber px-2 py-1 rounded-sm"
                                data-testid="report-replay-badge"
                                title={t("expedition_report_page.replay_title")}
                            >
                                REPLAY
                            </span>
                        )}
                        {isDone && replayInfo && (
                            <div
                                title={
                                    replayInfo.can_replay
                                        ? "Dispatch the same team again"
                                        : replayInfo.cannot_replay_reason || "Cannot replay"
                                }
                            >
                                <Button
                                    type="button"
                                    onClick={handleReplay}
                                    disabled={!replayInfo.can_replay || replayBusy}
                                    data-testid="report-replay-this-run-btn"
                                    className="bg-amber text-amber-foreground hover:bg-amber/90 rounded-sm font-semibold tracking-wide disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {replayBusy ? "Starting…" : "Replay This Run"}
                                </Button>
                            </div>
                        )}
                    </div>
                </div>

                <section className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
                    <Cell label="TEAM POWER" value={e.team_power} testid="report-team-power" accent />
                    <Cell label="SUCCESS CHANCE" value={`${e.success_chance}%`} testid="report-success-chance" />
                    <Cell
                        label="FINAL SCORE"
                        value={e.final_score != null ? e.final_score : "—"}
                        testid="report-final-score"
                    />
                    <Cell
                        label="GOLD REWARD"
                        value={isDone ? `${e.gold_reward}g` : "—"}
                        testid="report-gold-reward"
                        accent
                    />
                </section>

                {/* Narrative log */}
                {e.result_log && (
                    <section className="mb-6">
                        <div className="text-[10px] text-muted-foreground tracking-widest mb-2">
                            :: NARRATIVE
                        </div>
                        <blockquote
                            data-testid="report-narrative"
                            className="border-l-2 border-amber pl-4 py-2 bg-card/40 text-sm text-foreground/90 italic"
                        >
                            {e.result_log}
                        </blockquote>
                    </section>
                )}

                {/* Phase 14.5 — Explainability layer */}
                {isDone && (
                    <ExpeditionExplainer
                        summary={report_summary}
                        steps={report_steps}
                        members={members}
                    />
                )}

                {/* Phase 7: Expedition Analysis (equipment delta) */}
                <section className="mb-6" data-testid="report-analysis">
                    <div className="text-[10px] text-muted-foreground tracking-widest mb-2">
                        :: EXPEDITION ANALYSIS
                    </div>
                    <div className="border border-border bg-card rounded-sm p-4 text-sm">
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1">
                            <div className="flex justify-between border-b border-border/40 py-1">
                                <span className="text-muted-foreground text-xs">{t("expedition_report_page.recommended_power")}</span>
                                <span className="font-medium">{e.team_power && e.success_chance != null ? "" : ""}{e.recommended_power ?? "—"}</span>
                            </div>
                            <div className="flex justify-between border-b border-border/40 py-1">
                                <span className="text-muted-foreground text-xs">{t("expedition_report_page.base_power")}</span>
                                <span data-testid="analysis-base-power" className="font-medium">{e.base_team_power}</span>
                            </div>
                            <div className="flex justify-between border-b border-border/40 py-1">
                                <span className="text-muted-foreground text-xs">{t("expedition_report_page.equipment_bonus")}</span>
                                <span data-testid="analysis-eq-bonus" className="font-medium text-amber">+{e.equipment_power_bonus}</span>
                            </div>
                            <div className="flex justify-between border-b border-border/40 py-1">
                                <span className="text-muted-foreground text-xs">{t("expedition_report_page.final_power")}</span>
                                <span data-testid="analysis-final-power" className="font-medium text-[#22c55e]">{e.final_team_power}</span>
                            </div>
                            <div className="flex justify-between border-b border-border/40 py-1">
                                <span className="text-muted-foreground text-xs">{t("expedition_report_page.success_no_equip")}</span>
                                <span className="font-medium">{e.success_chance_without_equipment}%</span>
                            </div>
                            <div className="flex justify-between border-b border-border/40 py-1">
                                <span className="text-muted-foreground text-xs">{t("expedition_report_page.success_final")}</span>
                                <span className="font-medium text-[#22c55e]">{e.success_chance_with_equipment}%</span>
                            </div>
                        </div>
                        {e.equipment_delta_text && (
                            <div
                                data-testid="analysis-narrative"
                                className="mt-3 text-xs text-foreground/90 border-t border-border/40 pt-3 italic"
                            >
                                {e.equipment_delta_text}
                            </div>
                        )}
                    </div>
                </section>

                {/* Team */}
                <section className="mb-6">
                    <div className="text-[10px] text-muted-foreground tracking-widest mb-3">
                        :: PARTY ({members?.length ?? 0})
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                        {members?.map((m) => (
                            <div
                                key={m.id}
                                data-testid={`report-member-${m.adventurer_id}`}
                                className="border border-border bg-card rounded-sm p-3"
                            >
                                <div className="font-medium truncate">{m.name_snapshot}</div>
                                <div className="text-[11px] text-muted-foreground mt-0.5">
                                    {m.class_name_snapshot} · {m.role_snapshot} · lvl{" "}
                                    {m.level_snapshot}
                                </div>
                                <div className="grid grid-cols-5 gap-1 text-[10px] text-muted-foreground mt-2">
                                    <span>STR {m.strength_snapshot}</span>
                                    <span>AGI {m.agility_snapshot}</span>
                                    <span>INT {m.intellect_snapshot}</span>
                                    <span>END {m.endurance_snapshot}</span>
                                    <span>FAI {m.faith_snapshot}</span>
                                </div>
                                {(m.equipment_snapshot?.length > 0 || m.equipment_power_snapshot > 0) && (
                                    <div
                                        data-testid={`report-member-equipment-${m.adventurer_id}`}
                                        className="mt-2 pt-2 border-t border-border/60"
                                    >
                                        <div className="text-[10px] text-muted-foreground tracking-widest mb-1">
                                            EQUIPMENT (snapshot) · +{m.equipment_power_snapshot} pow
                                        </div>
                                        <div className="flex flex-wrap gap-1">
                                            {m.equipment_snapshot?.map((eq, idx) => {
                                                // Phase 19.1 hotfix — defensive: snapshot may be partial
                                                const slot = (eq?.slot || "?").toString();
                                                const slotInitial = slot.charAt(0).toUpperCase() || "?";
                                                return (
                                                    <span
                                                        key={`${slot}-${idx}`}
                                                        className="text-[10px] text-amber border border-amber/40 px-1 py-0.5 rounded-sm"
                                                        title={`${slot} · ${eq?.rarity || ""}`}
                                                    >
                                                        {slotInitial}·{eq?.item_name || "—"}
                                                    </span>
                                                );
                                            })}
                                        </div>
                                    </div>
                                )}
                                {isDone && (
                                    <div className="text-[11px] text-amber mt-2">
                                        +{e.xp_reward} XP
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </section>

                {/* Loot */}
                <section>
                    <div className="text-[10px] text-muted-foreground tracking-widest mb-3">
                        :: LOOT
                    </div>
                    {!isDone && (
                        <div className="text-xs text-muted-foreground">
                            results sealed until party returns<span className="caret-blink" />
                        </div>
                    )}
                    {isDone && (!loot_items || loot_items.length === 0) && (
                        <div data-testid="report-no-loot" className="text-xs text-muted-foreground border border-border bg-card rounded-sm p-4">
                            No loot recovered from this run.
                        </div>
                    )}
                    {isDone && loot_items && loot_items.length > 0 && (
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3" data-testid="report-loot-grid">
                            {loot_items.map((it, idx) => (
                                <div
                                    key={`${it.id}-${idx}`}
                                    data-testid={`loot-item-${it.slug}`}
                                    className="border border-border bg-card rounded-sm p-3 flex items-start gap-3"
                                >
                                    <div className="text-amber text-lg">◇</div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center justify-between gap-2">
                                            <div className="font-medium truncate">{it.name}</div>
                                            <RarityBadge rarity={it.rarity} />
                                        </div>
                                        <div className="text-[11px] text-muted-foreground mt-1">
                                            {it.item_type} · power {it.power_score}
                                        </div>
                                        <div className="text-[11px] text-muted-foreground mt-1">
                                            {it.description}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </section>
            </main>
        </div>
    );
}
