import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { api, formatApiError } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { Button } from "../components/ui/button";
import { toast } from "sonner";
import AppHeader from "../components/AppHeader";
import { TraitList } from "../components/TraitBadge";
import { useT } from "../i18n/I18nContext";

const RARITY_STYLE = {
    Common: { color: "#9ca3af", label: "Common" },
    Uncommon: { color: "#22c55e", label: "Uncommon" },
    Rare: { color: "#3b82f6", label: "Rare" },
    Epic: { color: "#a855f7", label: "Epic" },
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
        {role?.toUpperCase()}
    </span>
);

const StatRow = ({ label, value }) => (
    <div className="flex items-center justify-between text-xs py-1 border-b border-border/40 last:border-b-0">
        <span className="text-muted-foreground tracking-wider">{label}</span>
        <span className="text-foreground font-medium">{value}</span>
    </div>
);

const CandidateCard = ({ candidate, canAfford, onRecruit, busy }) => (
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
            <Button
                data-testid={`recruit-btn-${candidate.candidate_id}`}
                onClick={() => onRecruit(candidate)}
                disabled={!canAfford || busy}
                title={!canAfford ? "Not enough gold" : "Recruit this adventurer"}
                className="h-9 rounded-sm bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed text-xs px-4"
            >
                {busy ? "…" : "Recruit →"}
            </Button>
        </div>
    </div>
);

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
    const { t } = useT();
    const [candidates, setCandidates] = useState(null);
    const [meta, setMeta] = useState(null);
    const [loading, setLoading] = useState(false);
    const [refreshing, setRefreshing] = useState(false);
    const [recruiting, setRecruiting] = useState(null);

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
    }, [fetchCandidates]);

    const [territoryState, setTerritoryState] = useState(null);

    const fetchTerritoryCap = useCallback(async () => {
        try {
            const [terr, advs] = await Promise.all([
                api.get("/territory"),
                api.get("/adventurers"),
            ]);
            const dormLevel = Number(terr.data?.territory?.structures?.dormitories?.level || 0);
            const capByLevel = [0, 5, 10, 15, 20, 25, 30, 50];
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
            if (detail?.code === "recruitment.cap_reached") {
                toast.error(detail.user_message || `Roster pieno (${detail.current}/${detail.cap}). Potenzia i Dormitori.`, {
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

    const gold = guild?.gold ?? 0;
    const cost = candidates?.[0]?.cost_gold ?? 20;
    const canAfford = gold >= cost;

    return (
        <div className="min-h-screen bg-background text-foreground term-grid-bg">
            <AppHeader subtitle="RECRUIT" />

            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
                <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3 mb-6">
                    <div>
                        <div className="text-xs text-amber tracking-widest mb-2">
                            :: RECRUITMENT BOARD
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
                                GUILD GOLD
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
                                        ? `Next refresh costs ${meta.next_refresh_cost_gold}g`
                                        : "Free refresh available"
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
                        Insufficient gold ({gold}g). You need at least {cost}g per recruit.
                    </div>
                )}

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
                                onRecruit={handleRecruit}
                                busy={recruiting === c.candidate_id}
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
                            :: ROSTER EMPTY
                        </div>
                        <p className="text-sm text-muted-foreground mb-4">
                            All current candidates have been recruited. Refresh to call new
                            ones to the hall.
                        </p>
                        <Button
                            onClick={doRefresh}
                            disabled={refreshing || !(meta?.can_refresh ?? true)}
                            data-testid="refresh-empty-btn"
                            className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm"
                        >
                            {refreshing
                                ? "refreshing…"
                                : meta && meta.next_refresh_cost_gold > 0
                                ? `↻ Refresh (${meta.next_refresh_cost_gold}g)`
                                : "↻ Refresh candidates"}
                        </Button>
                    </div>
                )}

                <div className="mt-8 text-xs text-muted-foreground">
                    <Link
                        to="/adventurers"
                        className="text-amber hover:underline"
                        data-testid="goto-adventurers"
                    >
                        View hired adventurers →
                    </Link>
                </div>
            </main>
        </div>
    );
}
