import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { api, formatApiError } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { Button } from "../components/ui/button";
import { toast } from "sonner";
import AppHeader from "../components/AppHeader";
import { TraitList } from "../components/TraitBadge";

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
    const [candidates, setCandidates] = useState(null);
    const [loading, setLoading] = useState(false);
    const [recruiting, setRecruiting] = useState(null);

    const fetchCandidates = useCallback(async () => {
        setLoading(true);
        try {
            const { data } = await api.get("/recruitment/candidates");
            setCandidates(data.candidates);
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchCandidates();
    }, [fetchCandidates]);

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
            // Refresh guild gold + adventurer count
            await refreshGuild();
        } catch (err) {
            toast.error(formatApiError(err));
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
                            Recruitment
                        </h1>
                        <p className="text-sm text-muted-foreground mt-2 max-w-2xl">
                            Four candidates are passing through the guild hall today. Each
                            costs <span className="text-amber">{cost} gold</span>. Refresh to
                            shuffle the roster.
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
                        <Button
                            data-testid="refresh-candidates-btn"
                            onClick={fetchCandidates}
                            disabled={loading}
                            variant="outline"
                            className="h-10 rounded-sm bg-transparent border-border hover:bg-secondary text-xs"
                        >
                            {loading ? "loading…" : "↻ Refresh"}
                        </Button>
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
                            onClick={fetchCandidates}
                            data-testid="refresh-empty-btn"
                            className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm"
                        >
                            ↻ Refresh candidates
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
