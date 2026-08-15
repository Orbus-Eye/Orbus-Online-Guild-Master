import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "../context/AuthContext";
import { api, formatApiError } from "../lib/api";
import AppHeader from "../components/AppHeader";
import GameImage from "../components/GameImage";
import { guildBannerSources } from "../utils/gameAssets";
import OnboardingChecklistV2 from "../components/OnboardingChecklistV2";
import MigrationBannerR183c from "../components/MigrationBannerR183c";
import R18ResetBanner from "../components/R18ResetBanner";
import NextActionsCard from "../components/NextActionsCard";
import DailyLoopCard from "../components/DailyLoopCard";
import GuildProgressCard from "../components/GuildProgressCard";
import FirstObjectiveCard from "../components/FirstObjectiveCard";
import WorldMiniCard from "../components/WorldMiniCard";
import SiteIncomeMiniCard from "../components/SiteIncomeMiniCard";
import LegendaryForgeMiniCard from "../components/LegendaryForgeMiniCard";
import ArfusMiniCard from "../components/ArfusMiniCard";
import TradePactsMiniCard from "../components/TradePactsMiniCard";
import SpecializationMiniCard from "../components/SpecializationMiniCard";
import PvpMiniCard from "../components/PvpMiniCard";
import PvpSeasonMiniCard from "../components/PvpSeasonMiniCard";
import StablesMiniCard from "../components/StablesMiniCard";
import ContinentEventBanner from "../components/ContinentEventBanner";
import DailyQuestsCard from "../components/DailyQuestsCard";
import StreakBadge from "../components/StreakBadge";
import WeeklyQuestsCard from "../components/WeeklyQuestsCard";
import ChronicleCard from "../components/ChronicleCard";
import RosterHealthCard from "../components/RosterHealthCard";
import ContractsCard from "../components/ContractsCard";
import LastRaidCard from "../components/LastRaidCard";  // ROUND 16.5.1 B.3 UI
import { Button } from "../components/ui/button";
import { useT } from "../i18n/I18nContext";
import { formatDateTime, formatRelative } from "../utils/dateFormat";
import { DORM_CAP_BY_LEVEL, STRUCTURE_SLUGS } from "../utils/structures";

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

// FASE 9 A2 — voce compatta della striscia info nell'hero. Mantiene i
// data-testid storici (stat-gold, stat-reputation, …) che prima vivevano
// nella griglia Stat a fondo pagina.
const HeroStat = ({ label, value, testid, accent = false }) => (
    <div className="flex flex-col min-w-0">
        <span className="text-[9px] text-muted-foreground tracking-widest uppercase">
            {label}
        </span>
        <span
            data-testid={testid}
            className={`text-sm font-semibold truncate ${accent ? "text-amber" : "text-foreground"}`}
        >
            {value}
        </span>
    </div>
);

function TerritoryWidget() {
    const [territory, setTerritory] = useState(null);
    const [advCount, setAdvCount] = useState(null);

    useEffect(() => {
        Promise.all([api.get("/territory"), api.get("/adventurers")])
            .then(([t, a]) => {
                setTerritory(t.data?.territory || null);
                setAdvCount((a.data?.adventurers || []).length);
            })
            .catch(() => { /* best-effort widget */ });
    }, []);

    const summary = useMemo(() => {
        if (!territory) return null;
        const structures = territory.structures || {};
        const dormLevel = Number(structures.dormitories?.level || 0);
        const cap = DORM_CAP_BY_LEVEL[dormLevel] || 0;
        const unlocked = STRUCTURE_SLUGS.filter((s) => Number(structures[s]?.level || 0) >= 1).length;
        const overCap = advCount != null && advCount > cap;
        return { dormLevel, cap, unlocked, overCap };
    }, [territory, advCount]);

    if (!territory || !summary) return null;

    return (
        <div className="mb-6 space-y-3">
            {/* ROUND 6B.4 Task 1 — RosterHealthCard replaces the inline
                over-cap snippet. The new card already shows the 4-state
                colored stripe AND the over-cap CTA in red, so the previous
                duplicated banner is no longer needed. */}
            <RosterHealthCard />
            <Link
                to="/territory"
                data-testid="dashboard-territory-widget"
                className="block border border-border bg-card rounded-sm p-4 hover:border-amber/40 transition-colors"
            >
                <div className="flex items-center justify-between mb-3">
                    <span className="text-[10px] text-amber tracking-widest font-bold">:: TERRITORIO</span>
                    <span className="text-[10px] text-amber group-hover:translate-x-0.5">→</span>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <div className="text-[10px] text-muted-foreground tracking-widest mb-1">Strutture</div>
                        <div data-testid="dashboard-territory-unlocked" className="font-bold">
                            {summary.unlocked}/11
                        </div>
                        <div className="text-[10px] text-muted-foreground mt-1">sbloccate</div>
                    </div>
                    <div>
                        <div className="text-[10px] text-muted-foreground tracking-widest mb-1">Dormitori</div>
                        <div className="font-bold">Lv{summary.dormLevel}</div>
                        <div className="text-[10px] text-muted-foreground mt-1">cap roster {summary.cap}</div>
                    </div>
                </div>
            </Link>
        </div>
    );
}

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

const _LockedAction = ({ label, code, phase }) => (
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
    // FASE 9K — upload/rimozione banner personalizzato della gilda.
    const [bannerBusy, setBannerBusy] = useState(false);
    const bannerInputRef = useRef(null);

    const handleBannerFile = async (event) => {
        const file = event.target.files?.[0];
        event.target.value = "";  // stesso file ricaricabile
        if (!file) return;
        if (file.size > 4 * 1024 * 1024) {
            toast.error("Immagine troppo grande: massimo 4 MB.");
            return;
        }
        setBannerBusy(true);
        try {
            const fd = new FormData();
            fd.append("file", file);
            // Istanza `api`: CSRF + retry (lezione del bug avatar A1).
            await api.post("/guilds/banner", fd);
            toast.success("Banner della gilda aggiornato!");
            await refreshGuild();
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setBannerBusy(false);
        }
    };

    const handleBannerRemove = async () => {
        if (bannerBusy) return;
        setBannerBusy(true);
        try {
            await api.delete("/guilds/banner");
            toast.success("Banner rimosso: torna quello standard.");
            await refreshGuild();
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setBannerBusy(false);
        }
    };
    // FASE 9 A2 — livello di gilda nell'hero (best-effort, stessa fonte
    // di GuildProgressCard: /achievements/summary).
    const [guildLevel, setGuildLevel] = useState(null);

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

    useEffect(() => {
        api.get("/achievements/summary")
            .then(({ data }) => setGuildLevel(data?.guild_level ?? null))
            .catch(() => { /* best-effort: l'hero regge senza livello */ });
    }, []);

    const handleReplay = async () => {
        if (replayBusy) return;
        setReplayBusy(true);
        try {
            const { data } = await api.post("/expeditions/replay-last");
            toast.success(
                `Spedizione ripetuta: ${
                    data.expedition.dungeon_name_it
                    || data.expedition.dungeon_name
                }`,
            );
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
        <div className="min-h-screen bg-background text-foreground term-grid-bg term-scanline overflow-x-hidden">
            <AppHeader />

            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8 min-w-0">
                {/* ============================================================
                    FASE 9 A2 — GERARCHIA VISIVA OBBLIGATORIA:
                      1. HERO / IDENTITÀ DELLA GILDA
                      2. STREAK
                      3. PROSSIME AZIONI / AZIONI PRINCIPALI
                      4. PROGRESSIONE / ATTIVITÀ
                      5. RESTO
                    La gilda è la prima cosa che il giocatore vede: nome,
                    titolo/identità, livello e info essenziali vivono QUI,
                    non più a fondo pagina.
                   ============================================================ */}

                {/* 1 ─ HERO GILDA */}
                <section data-testid="dashboard-hero" className="mb-6">
                    <div
                        className="banner-fantasy h-40 sm:h-52 group/banner"
                        data-testid="dashboard-hero-banner"
                    >
                        <GameImage
                            sources={guildBannerSources(guild)}
                            alt=""
                            className="w-full h-full object-cover"
                        />
                        {/* FASE 9K — gestione banner personalizzato */}
                        <div className="absolute top-2 right-2 z-10 flex gap-1.5">
                            <input
                                ref={bannerInputRef}
                                type="file"
                                accept="image/png,image/jpeg,image/webp"
                                className="hidden"
                                data-testid="guild-banner-file-input"
                                onChange={handleBannerFile}
                            />
                            <button
                                type="button"
                                data-testid="guild-banner-upload-btn"
                                disabled={bannerBusy}
                                onClick={() => bannerInputRef.current?.click()}
                                className="text-[9px] tracking-widest bg-black/55 border border-border text-foreground/85 px-2 py-1 rounded-sm hover:bg-black/75 disabled:opacity-50"
                                title="PNG, JPEG o WEBP · massimo 4 MB"
                            >
                                {bannerBusy ? "…" : "🖼 CAMBIA BANNER"}
                            </button>
                            {guild.custom_banner_url && (
                                <button
                                    type="button"
                                    data-testid="guild-banner-remove-btn"
                                    disabled={bannerBusy}
                                    onClick={handleBannerRemove}
                                    className="text-[9px] tracking-widest bg-black/55 border border-border text-foreground/85 px-2 py-1 rounded-sm hover:bg-black/75 disabled:opacity-50"
                                >
                                    ✖ RIMUOVI BANNER
                                </button>
                            )}
                        </div>
                        <div className="banner-overlay">
                            <div className="text-[10px] text-amber tracking-[0.3em]">
                                :: SALA DEL TRONO
                            </div>
                            <h1
                                data-testid="guild-name"
                                className="font-fantasy text-2xl sm:text-4xl font-semibold tracking-tight text-foreground"
                            >
                                {guild.name}
                            </h1>
                            {guild.description ? (
                                <p
                                    data-testid="guild-description"
                                    className="text-xs sm:text-sm text-muted-foreground mt-1 max-w-2xl line-clamp-2"
                                >
                                    {guild.description}
                                </p>
                            ) : (
                                <p className="text-xs text-muted-foreground/60 italic mt-1">
                                    {t("dashboard.no_description")}
                                </p>
                            )}
                        </div>
                    </div>
                    {/* Striscia info essenziali agganciata al banner. */}
                    <div
                        data-testid="dashboard-hero-stats"
                        className="border border-border border-t-0 bg-card rounded-b-sm px-4 py-3 flex flex-wrap items-center gap-x-6 gap-y-2"
                    >
                        <div className="flex items-center gap-2 pr-4 border-r border-border/60">
                            <span className="text-[9px] text-muted-foreground tracking-widest uppercase">
                                Livello Gilda
                            </span>
                            <span
                                data-testid="hero-guild-level"
                                className="text-lg font-semibold text-amber"
                            >
                                {guildLevel != null ? `Lv ${guildLevel}` : "—"}
                            </span>
                        </div>
                        <HeroStat
                            label={t("dashboard.stats.gold")}
                            value={guild.gold}
                            testid="stat-gold"
                            accent
                        />
                        <HeroStat
                            label={t("dashboard.stats.reputation")}
                            value={guild.reputation}
                            testid="stat-reputation"
                        />
                        <HeroStat
                            label={t("dashboard.stats.adventurers")}
                            value={advCount}
                            testid="stat-adventurer-count"
                        />
                        <HeroStat
                            label={t("dashboard.stats.active_exp")}
                            value={guild.active_expedition_count ?? 0}
                            testid="stat-active-expeditions"
                            accent
                        />
                        {/* FASE 10F — Beni di Gilda sempre visibili in hero */}
                        <div
                            className="flex flex-col"
                            title={"Usati per automatizzare le spedizioni nei dungeon già completati. Si ripristinano ogni giorno."}
                        >
                            <span className="text-[9px] text-muted-foreground tracking-widest uppercase">
                                Beni di Gilda
                            </span>
                            <span
                                data-testid="stat-guild-supplies"
                                className="text-lg font-semibold text-amber tabular-nums"
                            >
                                {guild.guild_supplies ?? "—"} / {guild.guild_supplies_cap ?? 120}
                            </span>
                        </div>
                        <div className="ml-auto flex flex-col items-end min-w-0">
                            <span className="text-[9px] text-muted-foreground tracking-widest uppercase">
                                {t("dashboard.founded")}
                            </span>
                            <span
                                data-testid="guild-created-at"
                                className="text-[11px] text-foreground truncate"
                            >
                                {formatDateTime(guild.created_at, lang)}
                            </span>
                            <span
                                data-testid="stat-guild-id"
                                className="text-[9px] font-mono text-muted-foreground/70"
                            >
                                #{guild.id.slice(0, 8)}
                            </span>
                        </div>
                    </div>
                </section>

                {/* Banner di sistema (rari, dismissibili): sotto l'hero. */}
                <MigrationBannerR183c />
                <R18ResetBanner />

                {/* 2 ─ STREAK — molto visibile, subito sotto l'identità. */}
                <div className="mb-6" data-testid="dashboard-streak-slot">
                    <StreakBadge />
                </div>

                {/* 3 ─ AZIONI PRINCIPALI */}
                {/* ROUND 16.1 Phase 1 — bilingual data-driven onboarding */}
                <div className="mb-6">
                    <OnboardingChecklistV2 />
                </div>
                {/* ROUND 17 STEP 0 — Nudge "Primo obiettivo" per gilde
                    che non hanno mai completato una spedizione. */}
                <FirstObjectiveCard guild={guild} advCount={advCount} />
                {/* ROUND 16.1 Phase 1 — data-driven next actions */}
                <div className="mb-6">
                    <NextActionsCard />
                </div>
                <div className="mb-6">
                    <DailyQuestsCard />
                </div>
                {/* ROUND 16.1 Phase 1 — "Cosa fare oggi" rolling daily loop */}
                <div className="mb-6">
                    <DailyLoopCard />
                </div>
                <section className="mb-6">
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

                {/* 4 ─ PROGRESSIONE / ATTIVITÀ */}
                <div className="mb-6">
                    <GuildProgressCard />
                </div>
                <TerritoryWidget />

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
                                Nessuna spedizione ancora. Vai ai{" "}
                                <Link
                                    to="/dungeons"
                                    className="text-amber hover:underline"
                                >
                                    Dungeon
                                </Link>{" "}
                                per avviarne una.
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
                                        {lastRun.expedition.dungeon_name_it
                                            || lastRun.expedition.dungeon_name}
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

                <div className="mb-6">
                    <WeeklyQuestsCard />
                </div>
                <div className="mb-6">
                    <ContractsCard />
                </div>
                {/* ROUND 16.5.1 B.3 UI — Ultimo raid card */}
                <div className="mb-6">
                    <LastRaidCard />
                </div>
                <div className="mb-6">
                    <ChronicleCard limit={15} />
                </div>

                {/* 5 ─ RESTO (mondo, forge, PvP, scuderie, log) */}
                <div className="mb-4">
                    <ContinentEventBanner />
                </div>
                <div className="mb-4 grid gap-4 md:grid-cols-2">
                    <SiteIncomeMiniCard />
                    <WorldMiniCard />
                </div>
                <div className="mb-4">
                    <LegendaryForgeMiniCard />
                </div>
                <div className="mb-4">
                    <ArfusMiniCard />
                </div>
                <div className="mb-4 grid gap-4 md:grid-cols-2">
                    <TradePactsMiniCard />
                    <SpecializationMiniCard />
                </div>
                <div className="mb-4">
                    <PvpMiniCard />
                </div>
                <div className="mb-4">
                    <PvpSeasonMiniCard />
                </div>
                <div className="mb-4">
                    <StablesMiniCard />
                </div>

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
                            <span className="text-foreground">{guild.name}</span> — gold{" "}
                            {guild.gold}, adventurers {advCount}
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
