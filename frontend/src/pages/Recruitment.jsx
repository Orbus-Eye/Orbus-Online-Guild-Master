import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { api, formatApiError } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { Button } from "../components/ui/button";
import { toast } from "sonner";
import AppHeader from "../components/AppHeader";
import OverCapBanner from "../components/OverCapBanner";
import { TraitList } from "../components/TraitBadge";
import { useT } from "../i18n/I18nContext";
import { rarityLabel, tagLabel } from "../utils/displayLabels";

const RARITY_STYLE = {
    Common: { color: "#9ca3af", label: "Comune" },
    Uncommon: { color: "#22c55e", label: "Non comune" },
    Rare: { color: "#3b82f6", label: "Raro" },
    Epic: { color: "#a855f7", label: "Epico" },
};

const RarityBadge = ({ rarity }) => {
    const s = RARITY_STYLE[rarity] || RARITY_STYLE.Common;
    return (
        <span
            data-testid={`rarity-${rarity.toLowerCase()}`}
            className="inline-flex items-center text-[10px] tracking-widest border px-1.5 py-0.5 rounded-sm"
            style={{ color: s.color, borderColor: s.color + "55" }}
        >
            {s.label.toUpperCase()}
        </span>
    );
};

const RoleBadge = ({ role }) => (
    <span className="inline-flex items-center text-[10px] tracking-widest border border-border bg-secondary text-muted-foreground px-1.5 py-0.5 rounded-sm">
        {tagLabel(role).toUpperCase()}
    </span>
);

const StatRow = ({ label, value }) => (
    <div className="flex items-center justify-between text-xs py-1 border-b border-border/40 last:border-b-0">
        <span className="text-muted-foreground tracking-wider">{label}</span>
        <span className="text-foreground font-medium">{value}</span>
    </div>
);

const CandidateCard = ({ candidate, canAfford, overCap, onRecruit, onFreeze, busy, freezeFull }) => {
    const disabled = !canAfford || busy || overCap;
    let title = "Recluta questo avventuriero";
    if (overCap) {
        title = "Capienza avventurieri raggiunta. Potenzia Dormitori o congeda.";
    } else if (!canAfford) {
        title = "Oro insufficiente";
    }
    return (
    <div
        data-testid={`candidate-card-${candidate.candidate_id}`}
        className="border border-border bg-card rounded-sm p-4 flex flex-col"
    >
        <div className="flex items-start justify-between gap-2 mb-3">
            <div className="min-w-0">
                <div
                    data-testid="candidate-name"
                    className="text-base font-medium truncate"
                >
                    {candidate.name}
                </div>
                <div className="text-xs text-muted-foreground mt-0.5">
                    {candidate.class_name}
                </div>
            </div>
            <RarityBadge rarity={candidate.rarity} />
        </div>

        <div className="flex items-center gap-2 mb-3">
            <RoleBadge role={candidate.class_role} />
            <span className="text-[10px] text-muted-foreground tracking-widest">
                LVL {candidate.level}
            </span>
            {/* ROUND 6A.1 — unified total_power, same amber-bold styling as
                Adventurers.jsx roster, RaidBuilder and ExpeditionNew so the
                player compares candidates ↔ roster apples-to-apples. */}
            {typeof candidate.total_power === "number" && (
                <span
                    data-testid={`candidate-power-${candidate.candidate_id}`}
                    className="ml-auto text-xs text-amber font-bold tracking-widest"
                    title="Power totale (stats + level + rarity bonus). No equipaggiamento ancora."
                >
                    PWR {candidate.total_power}
                </span>
            )}
        </div>

        <div className="mb-4">
            <StatRow label="STR" value={candidate.strength} />
            <StatRow label="AGI" value={candidate.agility} />
            <StatRow label="INT" value={candidate.intellect} />
            <StatRow label="END" value={candidate.endurance} />
            <StatRow label="FAI" value={candidate.faith} />
        </div>

        <div className="mb-4">
            <div className="text-[10px] text-muted-foreground tracking-widest mb-1.5">
                TRAITS
            </div>
            <TraitList traits={candidate.traits} testid={`candidate-traits-${candidate.candidate_id}`} />
        </div>

        <div className="mt-auto flex items-center justify-between gap-2">
            <span className="text-xs text-amber" data-testid="candidate-cost">
                {candidate.cost_gold}g
            </span>
            <div className="flex items-center gap-1.5">
                {/* ROUND 11.3 TASK C — Freeze button. Disabled if bench full. */}
                <button
                    type="button"
                    data-testid={`freeze-btn-${candidate.candidate_id}`}
                    onClick={() => onFreeze && onFreeze(candidate)}
                    disabled={busy || freezeFull}
                    title={
                        freezeFull
                            ? "Panchina Reclute piena (2/2). Rilascia un candidato per liberare uno slot."
                            : "Congela in Panchina Reclute"
                    }
                    className="h-9 px-3 text-[11px] tracking-widest border border-amber/60 text-amber rounded-sm hover:bg-amber/10 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                    ❄ Congela
                </button>
                <Button
                    data-testid={`recruit-btn-${candidate.candidate_id}`}
                    onClick={() => onRecruit(candidate)}
                    disabled={disabled}
                    title={title}
                    className="h-9 rounded-sm bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed text-xs px-4"
                >
                    {busy ? "…" : "Recluta →"}
                </Button>
            </div>
        </div>
    </div>
    );
};

// ROUND 11.3 TASK C — Freeze Bench card. Shown in the persistent "Panchina
// Reclute" section above the candidate pool. Survives `/refresh` because
// the bench lives on `guilds.recruit_freeze_bench` server-side.
const FrozenCard = ({ frozen, onRecruit, onRelease, busy, canAfford, overCap }) => {
    const disabled = !canAfford || busy || overCap;
    return (
        <div
            data-testid={`frozen-card-${frozen.frozen_id}`}
            className="border border-amber/40 bg-amber/5 rounded-sm p-3 flex flex-col"
        >
            <div className="flex items-start justify-between gap-2 mb-2">
                <div className="min-w-0">
                    <div className="text-sm font-medium truncate">{frozen.name}</div>
                    <div className="text-[10px] text-muted-foreground">
                        {frozen.class_name} · Lv {frozen.level} · {rarityLabel(frozen.rarity)}
                    </div>
                </div>
                <span className="text-amber text-[10px] tracking-widest">❄ PANCHINA</span>
            </div>
            <div className="text-[10px] text-muted-foreground mb-2">
                STR {frozen.strength} · AGI {frozen.agility} · INT {frozen.intellect} ·
                END {frozen.endurance} · FAI {frozen.faith}
            </div>
            {typeof frozen.total_power === "number" && (
                <div className="text-[10px] text-amber tracking-widest mb-2">
                    PWR {frozen.total_power}
                </div>
            )}
            <div className="mt-auto flex items-center justify-between gap-2">
                <span className="text-xs text-amber">{frozen.cost_gold || frozen.cost || 0}g</span>
                <div className="flex items-center gap-1.5">
                    <button
                        type="button"
                        data-testid={`release-btn-${frozen.frozen_id}`}
                        onClick={() => onRelease(frozen)}
                        disabled={busy}
                        className="h-8 px-2 text-[11px] border border-border text-muted-foreground hover:bg-secondary rounded-sm disabled:opacity-40"
                        title="Rilascia lo slot panchina"
                    >
                        Rilascia
                    </button>
                    <button
                        type="button"
                        data-testid={`recruit-frozen-btn-${frozen.frozen_id}`}
                        onClick={() => onRecruit(frozen)}
                        disabled={disabled}
                        className="h-8 px-3 text-[11px] tracking-widest bg-amber text-background font-bold rounded-sm hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed"
                        title={
                            overCap
                                ? "Capienza avventurieri raggiunta."
                                : !canAfford
                                ? "Oro insufficiente."
                                : "Recluta dalla panchina"
                        }
                    >
                        Recluta
                    </button>
                </div>
            </div>
        </div>
    );
};

const Skeleton = () => (
    <div className="border border-border bg-card rounded-sm p-4 animate-pulse">
        <div className="h-4 w-1/2 bg-secondary rounded-sm mb-3" />
        <div className="h-3 w-1/3 bg-secondary rounded-sm mb-6" />
        <div className="space-y-2">
            {[...Array(5)].map((_, i) => (
                <div key={`skel-line-${i}`} className="h-3 w-full bg-secondary rounded-sm" />
            ))}
        </div>
    </div>
);

export default function Recruitment() {
    const { guild, refreshGuild } = useAuth();
    const { t, lang } = useT();
    const [candidates, setCandidates] = useState(null);
    const [meta, setMeta] = useState(null);
    const [loading, setLoading] = useState(false);
    const [refreshing, setRefreshing] = useState(false);
    const [recruiting, setRecruiting] = useState(null);
    // ROUND 11.3 TASK C — Freeze bench state. Bench survives /refresh
    // (the backend persists it on `guilds.recruit_freeze_bench`).
    const [bench, setBench] = useState({ frozen: [], used_slots: 0, max_slots: 2 });
    const [benchBusy, setBenchBusy] = useState(null);  // freeze_id | candidate_id | null

    const fetchBench = useCallback(async () => {
        try {
            const { data } = await api.get("/recruitment/frozen");
            setBench(data);
        } catch (err) {
            // Non-fatal; bench will just be empty in the UI.
            // ROUND 11.4b — empty catch now logs the error for diagnosability.
            console.error("[Recruitment] failed to fetch frozen bench:", err);
        }
    }, []);

    const fetchCandidates = useCallback(async () => {
        setLoading(true);
        try {
            const { data } = await api.get("/recruitment/candidates");
            setCandidates(data.candidates);
            setMeta({
                refreshes_remaining_today: data.refreshes_remaining_today,
                next_refresh_cost_gold: data.next_refresh_cost_gold,
                can_refresh: data.can_refresh,
            });
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setLoading(false);
        }
    }, []);

    const doRefresh = useCallback(async () => {
        setRefreshing(true);
        try {
            const { data } = await api.post("/recruitment/refresh");
            setCandidates(data.candidates);
            setMeta({
                refreshes_remaining_today: data.refreshes_remaining_today,
                next_refresh_cost_gold: data.next_refresh_cost_gold,
                can_refresh: data.can_refresh,
            });
            if (data.refresh_cost_paid > 0) {
                toast.success(t("recruitment.refresh.toast_paid", { cost: data.refresh_cost_paid }));
            } else {
                toast.success(t("recruitment.refresh.toast_free"));
            }
            await refreshGuild();
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setRefreshing(false);
        }
    }, [refreshGuild, t]);

    useEffect(() => {
        fetchCandidates();
        fetchBench();
    }, [fetchCandidates, fetchBench]);

    const [territoryState, setTerritoryState] = useState(null);

    const fetchTerritoryCap = useCallback(async () => {
        try {
            const [terr, advs] = await Promise.all([
                api.get("/territory"),
                api.get("/adventurers"),
            ]);
            const dormLevel = Number(terr.data?.territory?.structures?.dormitories?.level || 0);
            // ROUND 11.2 TASK 4 — Dormitories extended to Lv11 (cap 100).
            // Keep this in sync with backend `structures.DORMITORY_CAP_BY_LEVEL`.
            const capByLevel = [0, 5, 10, 15, 20, 25, 30, 40, 50, 65, 80, 100];
            const cap = capByLevel[dormLevel] || 0;
            const current = (advs.data?.adventurers || []).length;
            setTerritoryState({ cap, current, dormitory_level: dormLevel, headroom: Math.max(0, cap - current) });
        } catch {
            // best-effort; banner just won't show
        }
    }, []);

    useEffect(() => { fetchTerritoryCap(); }, [fetchTerritoryCap]);

    const handleRecruit = async (candidate) => {
        setRecruiting(candidate.candidate_id);
        try {
            const { data } = await api.post("/recruitment/recruit", {
                candidate_id: candidate.candidate_id,
            });
            toast.success(`Recruited ${data.adventurer.name} (${data.adventurer.class_name}).`);
            // Remove the recruited card from the visible list
            setCandidates((prev) =>
                prev ? prev.filter((c) => c.candidate_id !== candidate.candidate_id) : prev,
            );
            // Refresh guild gold + adventurer count + cap state
            await refreshGuild();
            fetchTerritoryCap();
        } catch (err) {
            const detail = err?.response?.data?.detail;
            // ROUND 6B.3 Wave 1.5 — over-cap now returns 423 `roster_over_capacity`
            // (was 422 `recruitment.cap_reached`). The global axios interceptor
            // already shows a toast with CTA → /roster/manage, so we just need
            // to refresh the territory cap state here.
            if (detail?.code === "roster_over_capacity") {
                fetchTerritoryCap();
            } else if (detail?.code === "recruitment.cap_reached") {
                // Back-compat branch (would only trigger if backend rolls back).
                toast.error(detail.user_message || `Roster pieno (${detail.current}/${detail.cap}).`, {
                    action: {
                        label: "Vai al Territorio",
                        onClick: () => { window.location.href = "/territory"; },
                    },
                    duration: 6000,
                });
                fetchTerritoryCap();
            } else {
                toast.error(formatApiError(err));
            }
        } finally {
            setRecruiting(null);
        }
    };

    // ROUND 11.3 TASK C — bench handlers.
    const handleFreeze = useCallback(async (candidate) => {
        setBenchBusy(candidate.candidate_id);
        try {
            const { data } = await api.post("/recruitment/freeze", {
                candidate_id: candidate.candidate_id,
            });
            setBench(data);
            // Remove the candidate from the active pool (server already
            // deleted it; we mirror the state locally for UI consistency).
            setCandidates((prev) =>
                prev ? prev.filter((c) => c.candidate_id !== candidate.candidate_id) : prev,
            );
            toast.success(`${candidate.name} è in panchina (${data.used_slots}/${data.max_slots}).`);
        } catch (err) {
            const detail = err?.response?.data?.detail;
            if (detail?.code === "freeze_bench.full") {
                toast.warning(detail.user_message || "Panchina piena.");
            } else if (detail?.code === "freeze_bench.already_frozen") {
                toast.info("Già in panchina.");
            } else if (detail?.code === "recruit.candidate_not_found") {
                toast.error("Candidato non più disponibile. Aggiorna la pagina.");
            } else {
                toast.error(formatApiError(err));
            }
        } finally {
            setBenchBusy(null);
        }
    }, []);

    const handleRelease = useCallback(async (frozen) => {
        setBenchBusy(frozen.frozen_id);
        try {
            const { data } = await api.post("/recruitment/unfreeze", {
                frozen_id: frozen.frozen_id,
            });
            setBench(data);
            toast.info(`${frozen.name} rilasciato dalla panchina.`);
        } catch (err) {
            const detail = err?.response?.data?.detail;
            if (detail?.code === "freeze_bench.not_found") {
                toast.error("Slot non trovato (potrebbe essere stato già usato).");
                fetchBench();
            } else {
                toast.error(formatApiError(err));
            }
        } finally {
            setBenchBusy(null);
        }
    }, [fetchBench]);

    const handleRecruitFrozen = useCallback(async (frozen) => {
        setBenchBusy(frozen.frozen_id);
        try {
            const { data } = await api.post("/recruitment/recruit-frozen", {
                frozen_id: frozen.frozen_id,
            });
            toast.success(`Reclutato ${data.adventurer.name} dalla panchina.`);
            await fetchBench();
            await refreshGuild();
            fetchTerritoryCap();
        } catch (err) {
            const detail = err?.response?.data?.detail;
            if (detail?.code === "economy.insufficient_gold") {
                toast.error(detail.user_message || "Oro insufficiente.");
            } else if (detail?.code === "roster_over_capacity") {
                toast.error(
                    (detail.user_message || "Capienza raggiunta.") +
                    " Congeda un avventuriero o potenzia i Dormitori.",
                    { duration: 6000 },
                );
                fetchTerritoryCap();
            } else if (detail?.code === "freeze_bench.not_found") {
                toast.error("Slot non trovato (potrebbe essere stato già usato).");
                fetchBench();
            } else {
                toast.error(formatApiError(err));
            }
        } finally {
            setBenchBusy(null);
        }
    }, [fetchBench, fetchTerritoryCap, refreshGuild]);

    const gold = guild?.gold ?? 0;
    const cost = candidates?.[0]?.cost_gold ?? 20;
    const canAfford = gold >= cost;
    const overCap = !!(territoryState && territoryState.current >= territoryState.cap);

    return (
        <div className="min-h-screen bg-background text-foreground term-grid-bg">
            <AppHeader subtitle="RECLUTAMENTO" />

            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
                <OverCapBanner source="recruitment" />
                <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3 mb-6">
                    <div>
                        <div className="text-xs text-amber tracking-widest mb-2">
                            :: BACHECA RECLUTAMENTO
                        </div>
                        <h1 className="text-3xl font-semibold tracking-tight">
                            {t("recruitment.title")}
                        </h1>
                        <p className="text-sm text-muted-foreground mt-2 max-w-2xl">
                            {t("recruitment.subtitle")}
                        </p>
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="text-right">
                            <div className="text-[10px] text-muted-foreground tracking-widest">
                                ORO GILDA
                            </div>
                            <div
                                data-testid="guild-gold"
                                className="text-2xl font-semibold text-amber"
                            >
                                {gold}
                            </div>
                        </div>
                        {territoryState && (
                            <div
                                data-testid="recruitment-roster-banner"
                                className={`flex-1 sm:max-w-xs px-3 py-2 border rounded-sm text-xs ${
                                    territoryState.current >= territoryState.cap
                                        ? "border-red-400/60 bg-red-500/10 text-red-200"
                                        : "border-border bg-secondary/30 text-muted-foreground"
                                }`}
                            >
                                <div className="flex items-center justify-between gap-3">
                                    <span className="tracking-widest font-bold text-[10px]">ROSTER</span>
                                    <span data-testid="recruitment-roster-count">
                                        <strong className="text-foreground">{territoryState.current}</strong>
                                        /{territoryState.cap}
                                    </span>
                                </div>
                                <div className="w-full bg-background/50 h-1 rounded-sm mt-1.5 overflow-hidden">
                                    <div
                                        className={`h-full transition-all ${territoryState.current >= territoryState.cap ? "bg-red-400" : "bg-amber"}`}
                                        style={{ width: `${Math.min(100, Math.round((territoryState.current / Math.max(territoryState.cap, 1)) * 100))}%` }}
                                    />
                                </div>
                                {territoryState.current >= territoryState.cap && (
                                    <a
                                        href="/territory"
                                        data-testid="recruitment-cap-cta"
                                        className="block mt-2 text-[10px] text-amber tracking-widest hover:underline"
                                    >
                                        ▶ POTENZIA DORMITORI
                                    </a>
                                )}
                            </div>
                        )}
                        <div className="flex flex-col items-end gap-1">
                            <Button
                                data-testid="refresh-candidates-btn"
                                onClick={doRefresh}
                                disabled={refreshing || loading || !(meta?.can_refresh ?? true)}
                                variant="outline"
                                className="h-10 rounded-sm bg-transparent border-border hover:bg-secondary text-xs"
                                title={
                                    meta && meta.next_refresh_cost_gold > 0
                                        ? `Prossimo refresh: ${meta.next_refresh_cost_gold}o`
                                        : "Refresh gratuito disponibile"
                                }
                            >
                                {refreshing
                                    ? t("common.loading")
                                    : meta && meta.next_refresh_cost_gold > 0
                                    ? t("recruitment.refresh.cost_label", { cost: meta.next_refresh_cost_gold })
                                    : `↻ ${t("recruitment.refresh.free_label")}`}
                            </Button>
                            {meta && (
                                <div
                                    className="text-[10px] tracking-widest text-muted-foreground"
                                    data-testid="refresh-counter"
                                >
                                    {meta.refreshes_remaining_today > 0
                                        ? t("recruitment.refresh.free_remaining", { n: meta.refreshes_remaining_today })
                                        : `next: ${meta.next_refresh_cost_gold}${t("common.gold_short")}`}
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {!canAfford && candidates && candidates.length > 0 && (
                    <div
                        data-testid="insufficient-gold-warning"
                        className="text-xs text-amber/90 border border-amber/40 bg-amber/5 px-3 py-2 rounded-sm mb-4"
                    >
                        Oro insufficiente ({gold}o). Servono almeno {cost}o per ogni reclutamento.
                    </div>
                )}

                {/* ROUND 11.3 TASK C — Panchina Reclute (persistente). */}
                <section
                    data-testid="freeze-bench-section"
                    className="border border-amber/30 bg-card rounded-sm p-3 mb-6"
                >
                    <div className="flex items-center justify-between mb-3">
                        <div>
                            <div className="text-[10px] tracking-widest text-amber mb-0.5">
                                ❄ PANCHINA RECLUTE
                            </div>
                            <div
                                className="text-xs text-muted-foreground"
                                data-testid="freeze-bench-counter"
                            >
                                {bench.used_slots}/{bench.max_slots} · sopravvive ai refresh
                            </div>
                        </div>
                    </div>
                    {bench.frozen.length === 0 ? (
                        <div
                            className="text-[11px] text-muted-foreground italic"
                            data-testid="freeze-bench-empty"
                        >
                            {lang === "it"
                                ? "Nessun candidato in panchina. Usa \"❄ Congela\" su una card per conservarne uno tra un refresh e l'altro."
                                : "No candidate on the bench. Use \"❄ Freeze\" on a card to keep one across refreshes."}
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            {bench.frozen.map((f) => (
                                <FrozenCard
                                    key={f.frozen_id}
                                    frozen={f}
                                    onRecruit={handleRecruitFrozen}
                                    onRelease={handleRelease}
                                    busy={benchBusy === f.frozen_id}
                                    canAfford={canAfford}
                                    overCap={overCap}
                                />
                            ))}
                        </div>
                    )}
                </section>

                {loading && !candidates && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                        {[...Array(4)].map((_, i) => (
                            <Skeleton key={`skel-card-${i}`} />
                        ))}
                    </div>
                )}

                {candidates && candidates.length > 0 && (
                    <div
                        data-testid="candidates-grid"
                        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3"
                    >
                        {candidates.map((c) => (
                            <CandidateCard
                                key={c.candidate_id}
                                candidate={c}
                                canAfford={canAfford}
                                overCap={overCap}
                                onRecruit={handleRecruit}
                                onFreeze={handleFreeze}
                                busy={recruiting === c.candidate_id || benchBusy === c.candidate_id}
                                freezeFull={bench.used_slots >= bench.max_slots}
                            />
                        ))}
                    </div>
                )}

                {candidates && candidates.length === 0 && (
                    <div
                        data-testid="all-recruited-state"
                        className="border border-border bg-card rounded-sm p-8 text-center"
                    >
                        <div className="text-amber text-xs tracking-widest mb-2">
                            {lang === "it" ? ":: NESSUN CANDIDATO" : ":: NO CANDIDATES"}
                        </div>
                        <p className="text-sm text-muted-foreground mb-4">
                            {lang === "it"
                                ? "👥 Tutti i candidati sono stati reclutati o congelati. Aggiorna la board per richiamare nuovi aspiranti."
                                : "👥 All candidates have been recruited or frozen. Refresh the board to summon new hopefuls."}
                        </p>
                        <Button
                            onClick={doRefresh}
                            disabled={refreshing || !(meta?.can_refresh ?? true)}
                            data-testid="refresh-empty-btn"
                            className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm"
                        >
                            {refreshing
                                ? (lang === "it" ? "aggiornamento…" : "refreshing…")
                                : meta && meta.next_refresh_cost_gold > 0
                                ? (lang === "it"
                                    ? `↻ Aggiorna (${meta.next_refresh_cost_gold}g)`
                                    : `↻ Refresh (${meta.next_refresh_cost_gold}g)`)
                                : (lang === "it" ? "↻ Aggiorna candidati" : "↻ Refresh candidates")}
                        </Button>
                    </div>
                )}

                <div className="mt-8 text-xs text-muted-foreground">
                    <Link
                        to="/adventurers"
                        className="text-amber hover:underline"
                        data-testid="goto-adventurers"
                    >
                        Vedi avventurieri reclutati →
                    </Link>
                </div>
            </main>
        </div>
    );
}
