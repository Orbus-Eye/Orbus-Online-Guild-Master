import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "../context/AuthContext";
import { api, formatApiError } from "../lib/api";
import AppHeader from "../components/AppHeader";
import OnboardingChecklist from "../components/OnboardingChecklist";
import DailyQuestsCard from "../components/DailyQuestsCard";
import StreakBadge from "../components/StreakBadge";
import WeeklyQuestsCard from "../components/WeeklyQuestsCard";
import { Button } from "../components/ui/button";
import { useT } from "../i18n/I18nContext";
import { formatDateTime, formatRelative } from "../utils/dateFormat";

const Stat = ({ label, value, testid, accent = false }) => (
    <div className="border border-border bg-card rounded-sm p-4">
        <div className="text-[10px] text-muted-foreground tracking-widest mb-2">
            {label}
        </div>
        <div
            data-testid={testid}
            className={`text-2xl font-semibold ${accent ? "text-amber" : "text-foreground"}`}
        >
            {value}
        </div>
    </div>
);

const ActiveAction = ({ to, label, code, testid }) => (
    <Link
        to={to}
        data-testid={testid}
        className="block border border-border bg-card rounded-sm p-4 hover:bg-secondary/40 transition-colors group"
    >
        <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] text-amber tracking-widest">::{code}</span>
            <span className="text-[10px] text-amber group-hover:translate-x-0.5 transition-transform">
                →
            </span>
        </div>
        <div className="text-sm">{label}</div>
        <div className="text-[10px] text-muted-foreground mt-2">— ready —</div>
    </Link>
);

const LockedAction = ({ label, code, phase }) => (
    <button
        type="button"
        disabled
        aria-disabled="true"
        title={`Coming in ${phase}`}
        data-testid={`quickaction-${code}`}
        className="text-left border border-border bg-card/60 rounded-sm p-4 opacity-60 cursor-not-allowed disabled:cursor-not-allowed w-full"
    >
        <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] text-muted-foreground tracking-widest">
                ::{code}
            </span>
            <span className="text-[10px] text-muted-foreground border border-border rounded-sm px-1.5 py-0.5">
                {phase}
            </span>
        </div>
        <div className="text-sm">{label}</div>
        <div className="text-[10px] text-muted-foreground mt-2">— locked —</div>
    </button>
);

export default function Dashboard() {
    const { user, guild, refreshGuild } = useAuth();
    const { t, lang } = useT();
    const navigate = useNavigate();
    const [lastRun, setLastRun] = useState(null); // {expedition, can_replay, cannot_replay_reason} | null
    const [lastRunStatus, setLastRunStatus] = useState("loading"); // loading | none | ready
    const [replayBusy, setReplayBusy] = useState(false);

    const fetchLast = useCallback(async () => {
        try {
            const { data } = await api.get("/expeditions/last-completed");
            setLastRun(data);
            setLastRunStatus("ready");
        } catch (err) {
            if (err?.response?.status === 404) {
                setLastRunStatus("none");
            } else {
                setLastRunStatus("none");
            }
        }
    }, []);

    useEffect(() => {
        fetchLast();
    }, [fetchLast]);

    const handleReplay = async () => {
        if (replayBusy) return;
        setReplayBusy(true);
        try {
            const { data } = await api.post("/expeditions/replay-last");
            toast.success(`Replay started: ${data.expedition.dungeon_name}`);
            await refreshGuild();
            navigate(`/expeditions/${data.expedition.id}`);
        } catch (err) {
            toast.error(formatApiError(err));
            // Refresh eligibility (state may have changed server-side)
            fetchLast();
        } finally {
            setReplayBusy(false);
        }
    };

    if (!guild) return null;
    const advCount = guild.adventurer_count ?? 0;

    return (
        <div className="min-h-screen bg-background text-foreground term-grid-bg term-scanline">
            <AppHeader />

            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
                <OnboardingChecklist />
                <div className="mb-6 grid gap-4 md:grid-cols-[1fr_minmax(220px,260px)]">
                    <DailyQuestsCard />
                    <StreakBadge />
                </div>
                <div className="mb-6">
                    <WeeklyQuestsCard />
                </div>

                <section className="mb-8">
                    <div className="text-xs text-amber tracking-widest mb-2">
                        {t("dashboard.guild_overview")}
                    </div>
                    <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
                        <div>
                            <h1
                                data-testid="guild-name"
                                className="text-3xl sm:text-4xl font-semibold tracking-tight"
                            >
                                {guild.name}
                            </h1>
                            {guild.description ? (
                                <p
                                    data-testid="guild-description"
                                    className="text-sm text-muted-foreground mt-2 max-w-2xl"
                                >
                                    {guild.description}
                                </p>
                            ) : (
                                <p className="text-sm text-muted-foreground/60 italic mt-2">
                                    {t("dashboard.no_description")}
                                </p>
                            )}
                        </div>
                        <div className="text-xs text-muted-foreground">
                            {t("dashboard.founded")}:{" "}
                            <span
                                data-testid="guild-created-at"
                                className="text-foreground"
                            >
                                {formatDateTime(guild.created_at, lang)}
                            </span>
                        </div>
                    </div>
                </section>

                <section className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-10">
                    <Stat label={t("dashboard.stats.level")} value={guild.level} testid="stat-level" accent />
                    <Stat
                        label={t("dashboard.stats.reputation")}
                        value={guild.reputation}
                        testid="stat-reputation"
                    />
                    <Stat label={t("dashboard.stats.gold")} value={guild.gold} testid="stat-gold" accent />
                    <Stat
                        label={t("dashboard.stats.adventurers")}
                        value={advCount}
                        testid="stat-adventurer-count"
                    />
                    <Stat
                        label={t("dashboard.stats.active_exp")}
                        value={guild.active_expedition_count ?? 0}
                        testid="stat-active-expeditions"
                        accent
                    />
                    <Stat
                        label={t("dashboard.stats.guild_id")}
                        value={
                            <span className="text-xs font-mono break-all">
                                {guild.id.slice(0, 8)}…
                            </span>
                        }
                        testid="stat-guild-id"
                    />
                </section>

                {/* Phase 7: progression mini-cards */}
                <section
                    className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 mb-8"
                    data-testid="phase7-progression"
                >
                    <Stat
                        label={t("dashboard.stats.completed")}
                        value={guild.total_expeditions_completed ?? 0}
                        testid="stat-total-completed"
                    />
                    <Stat
                        label={t("dashboard.stats.highest")}
                        value={
                            <span className="text-xs font-mono">
                                {guild.highest_dungeon_slug
                                    ? guild.highest_dungeon_slug
                                    : "—"}
                            </span>
                        }
                        testid="stat-highest-dungeon"
                    />
                    <Stat
                        label={t("dashboard.stats.last_loot")}
                        value={
                            guild.last_loot_item ? (
                                <span className="text-xs">
                                    {guild.last_loot_item.name}{" "}
                                    <span className="text-muted-foreground">
                                        · {guild.last_loot_item.rarity}
                                    </span>
                                </span>
                            ) : (
                                <span className="text-xs text-muted-foreground">
                                    None yet
                                </span>
                            )
                        }
                        testid="stat-last-loot"
                    />
                    {/* Phase 9.1: Peak Team Power badge → links to public leaderboard */}
                    <Link
                        to="/leaderboard"
                        data-testid="stat-peak-power-card"
                        className="border border-border bg-card rounded-sm p-4 hover:bg-secondary/40 hover:border-amber/55 transition-colors group block"
                        title={t("dashboard.peak_power_tooltip")}
                    >
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-[10px] text-amber tracking-widest">
                                {t("dashboard.stats.peak_power")}
                            </span>
                            <span className="text-[10px] text-amber group-hover:translate-x-0.5 transition-transform">
                                →
                            </span>
                        </div>
                        <div
                            className="text-2xl font-semibold text-amber"
                            data-testid="stat-peak-power"
                        >
                            {(guild.max_team_power_ever ?? 0) === 0
                                ? "—"
                                : guild.max_team_power_ever}
                        </div>
                        <div className="text-[10px] text-muted-foreground mt-2">
                            {(guild.max_team_power_ever ?? 0) === 0 ? (
                                "no expedition yet"
                            ) : (guild.max_team_power_ever ?? 0) >= 65 ? (
                                <span
                                    className="text-[#f59e0b]"
                                    data-testid="peak-power-dragon-unlock"
                                >
                                    🐉 dragons-hoard unlocked by peak
                                </span>
                            ) : (
                                "your strongest expedition power"
                            )}
                        </div>
                    </Link>
                </section>

                {/* Phase 8: Last Expedition replay card */}
                <section className="mb-8" data-testid="last-expedition-section">
                    <div className="text-xs text-amber tracking-widest mb-3">
                        {t("dashboard.last_expedition")}
                    </div>
                    {lastRunStatus === "loading" && (
                        <div
                            className="border border-border bg-card rounded-sm p-4 text-xs text-muted-foreground"
                            data-testid="last-expedition-loading"
                        >
                            loading<span className="caret-blink" />
                        </div>
                    )}
                    {lastRunStatus === "none" && (
                        <div
                            className="border border-border bg-card rounded-sm p-4 text-xs text-muted-foreground flex items-center justify-between gap-4 flex-wrap"
                            data-testid="last-expedition-empty"
                        >
                            <span>
                                No expeditions yet. Visit{" "}
                                <Link
                                    to="/dungeons"
                                    className="text-amber hover:underline"
                                >
                                    Dungeons
                                </Link>{" "}
                                to start one.
                            </span>
                        </div>
                    )}
                    {lastRunStatus === "ready" && lastRun?.expedition && (
                        <div
                            className="border border-border bg-card rounded-sm p-4"
                            data-testid="last-expedition-card"
                        >
                            <div className="flex items-start justify-between gap-3 flex-wrap mb-3">
                                <div>
                                    <div
                                        className="text-sm font-semibold"
                                        data-testid="last-expedition-dungeon-name"
                                    >
                                        {lastRun.expedition.dungeon_name}
                                    </div>
                                    <div className="text-[10px] text-muted-foreground mt-1">
                                        {formatRelative(lastRun.expedition.completed_at, lang, t)}{" "}
                                        · {formatDateTime(lastRun.expedition.completed_at, lang)}
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    {lastRun.expedition.result_summary === "Success" ? (
                                        <span
                                            className="inline-block text-[10px] tracking-widest border border-[#22c55e]/55 text-[#22c55e] px-2 py-1 rounded-sm"
                                            data-testid="last-expedition-result-success"
                                        >
                                            SUCCESS
                                        </span>
                                    ) : (
                                        <span
                                            className="inline-block text-[10px] tracking-widest border border-[#ef4444]/55 text-[#ef4444] px-2 py-1 rounded-sm"
                                            data-testid="last-expedition-result-failed"
                                        >
                                            FAILED
                                        </span>
                                    )}
                                    {lastRun.expedition.is_replay && (
                                        <span className="inline-block text-[10px] tracking-widest border border-amber/55 text-amber px-2 py-1 rounded-sm">
                                            REPLAY
                                        </span>
                                    )}
                                </div>
                            </div>
                            <div className="flex items-center justify-between gap-3 flex-wrap">
                                <Link
                                    to={`/expeditions/${lastRun.expedition.id}`}
                                    className="text-xs text-muted-foreground hover:text-foreground underline-offset-4 hover:underline"
                                    data-testid="last-expedition-view-report"
                                >
                                    view full report →
                                </Link>
                                <div
                                    title={
                                        lastRun.can_replay
                                            ? "Dispatch the same team to the same dungeon"
                                            : lastRun.cannot_replay_reason || "Cannot replay"
                                    }
                                >
                                    <Button
                                        type="button"
                                        onClick={handleReplay}
                                        disabled={!lastRun.can_replay || replayBusy}
                                        data-testid="replay-last-run-btn"
                                        className="bg-amber text-amber-foreground hover:bg-amber/90 rounded-sm font-semibold tracking-wide disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        {replayBusy ? "Starting…" : "Replay Last Run"}
                                    </Button>
                                </div>
                            </div>
                            {!lastRun.can_replay && lastRun.cannot_replay_reason && (
                                <div
                                    className="text-[10px] text-muted-foreground mt-3 italic"
                                    data-testid="replay-blocked-reason"
                                >
                                    ⚠ {lastRun.cannot_replay_reason}
                                </div>
                            )}
                        </div>
                    )}
                </section>

                <section>
                    <div className="text-xs text-muted-foreground tracking-widest mb-3">
                        {t("dashboard.quick_actions")}
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        <ActiveAction
                            to="/recruitment"
                            label={t("dashboard.actions.recruit")}
                            code="01"
                            testid="quickaction-01"
                        />
                        <ActiveAction
                            to="/adventurers"
                            label={t("dashboard.actions.adventurers")}
                            code="02"
                            testid="quickaction-02"
                        />
                        <ActiveAction
                            to="/dungeons"
                            label={t("dashboard.actions.dungeons")}
                            code="03"
                            testid="quickaction-03"
                        />
                        <ActiveAction
                            to="/inventory"
                            label={t("dashboard.actions.inventory")}
                            code="04"
                            testid="quickaction-04"
                        />
                    </div>
                </section>

                <section className="mt-10">
                    <div className="text-xs text-muted-foreground tracking-widest mb-3">
                        {t("dashboard.system_log")}
                    </div>
                    <div className="border border-border bg-card rounded-sm p-4 text-xs text-muted-foreground font-mono space-y-1">
                        <div>
                            <span className="text-amber">$</span> session opened for{" "}
                            <span className="text-foreground">@{user?.username}</span>
                        </div>
                        <div>
                            <span className="text-amber">$</span> guild{" "}
                            <span className="text-foreground">{guild.name}</span> — level{" "}
                            {guild.level}, gold {guild.gold}, adventurers {advCount}
                        </div>
                        <div>
                            <span className="text-amber">$</span> phase-3 modules pending
                            <span className="caret-blink" />
                        </div>
                    </div>
                </section>
            </main>
        </div>
    );
}
