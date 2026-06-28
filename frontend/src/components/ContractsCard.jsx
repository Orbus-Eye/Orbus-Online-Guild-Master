// ROUND 6D — Dashboard card showing claimable contracts at-a-glance.
// Aggregates daily + weekly + milestone "ready to claim" counts.
// Click → /contracts.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { useT } from "../i18n/I18nContext";
import { api } from "../lib/api";

export default function ContractsCard() {
    const { t } = useT();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let cancelled = false;
        async function load() {
            try {
                const [d, w, m] = await Promise.all([
                    api.get("/contracts/daily"),
                    api.get("/contracts/weekly"),
                    api.get("/contracts/milestones"),
                ]);
                if (cancelled) return;
                setData({
                    locked: d.data?.locked === true,
                    daily: d.data?.contracts || [],
                    weekly: w.data?.contracts || [],
                    milestones: m.data?.milestones || [],
                });
            } catch {
                if (!cancelled) setData({ locked: true, daily: [], weekly: [], milestones: [] });
            } finally {
                if (!cancelled) setLoading(false);
            }
        }
        load();
        return () => {
            cancelled = true;
        };
    }, []);

    if (loading || !data) {
        return (
            <div
                data-testid="contracts-card-loading"
                className="border border-border rounded-sm p-4 bg-card/40"
            >
                <div className="text-[10px] text-muted-foreground tracking-widest">
                    {t("contracts.card_title", "BACHECA CONTRATTI")}
                </div>
                <div className="text-xs text-muted-foreground mt-2">
                    {t("common.loading", "Caricamento…")}
                </div>
            </div>
        );
    }

    if (data.locked) {
        return (
            <div
                data-testid="contracts-card-locked"
                className="border border-border rounded-sm p-4 bg-card/40 opacity-70"
            >
                <div className="text-[10px] text-muted-foreground tracking-widest mb-2">
                    {t("contracts.card_title", "BACHECA CONTRATTI")}
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                    {t("contracts.card_locked_short",
                       "Sblocca la Bacheca Contratti dal Territorio.")}
                </p>
            </div>
        );
    }

    const claimableDaily = data.daily.filter((c) => c.can_claim).length;
    const claimableWeekly = data.weekly.filter((c) => c.can_claim).length;
    const claimableMilestones = data.milestones.filter((m) => m.can_claim).length;
    const totalClaimable = claimableDaily + claimableWeekly + claimableMilestones;
    const totalDaily = data.daily.length;
    const totalWeekly = data.weekly.length;

    // ROUND 6E Task 5 — pick the single highest-reward claimable across all
    // pools so the dashboard can hint the player at the most profitable
    // claim. Falls back to highest-progress if nothing is claimable.
    const claimablePool = [
        ...data.daily.filter((c) => c.can_claim).map((c) => ({ ...c, scope: "daily" })),
        ...data.weekly.filter((c) => c.can_claim).map((c) => ({ ...c, scope: "weekly" })),
        ...data.milestones.filter((m) => m.can_claim).map((m) => ({ ...m, scope: "milestone" })),
    ];
    const topClaim = claimablePool.length > 0
        ? claimablePool.reduce((a, b) =>
              (b.reward_gold || 0) > (a.reward_gold || 0) ? b : a
          )
        : null;

    return (
        <Link
            to="/contracts"
            data-testid="contracts-card-link"
            className="block border border-border rounded-sm p-4 bg-card/40 hover:border-amber/60 transition-colors"
        >
            <div className="flex items-center justify-between mb-3">
                <div className="text-[10px] text-amber tracking-widest">
                    {t("contracts.card_title", "BACHECA CONTRATTI")}
                </div>
                {totalClaimable > 0 && (
                    <span
                        data-testid="contracts-card-badge"
                        className="text-[10px] tracking-widest bg-amber text-background px-1.5 py-0.5 rounded-sm font-bold"
                    >
                        {totalClaimable} {t("contracts.card_badge_ready", "PRONTI")}
                    </span>
                )}
            </div>
            <ul className="space-y-1.5 text-xs">
                <li className="flex items-center justify-between">
                    <span className="text-muted-foreground">
                        {t("contracts.tab.daily", "Giornalieri")}
                    </span>
                    <span className="tabular-nums" data-testid="contracts-card-daily-count">
                        {claimableDaily}/{totalDaily}
                    </span>
                </li>
                <li className="flex items-center justify-between">
                    <span className="text-muted-foreground">
                        {t("contracts.tab.weekly", "Settimanali")}
                    </span>
                    <span className="tabular-nums" data-testid="contracts-card-weekly-count">
                        {claimableWeekly}/{totalWeekly}
                    </span>
                </li>
                <li className="flex items-center justify-between">
                    <span className="text-muted-foreground">
                        {t("contracts.tab.milestones", "Milestone")}
                    </span>
                    <span className="tabular-nums" data-testid="contracts-card-milestones-count">
                        {claimableMilestones}/{data.milestones.length}
                    </span>
                </li>
            </ul>
            {topClaim && (
                <div
                    data-testid="contracts-card-top-claim"
                    className="mt-3 pt-3 border-t border-amber/40 text-[10px]"
                >
                    <div className="text-amber/80 tracking-widest mb-0.5">
                        ★ {t("contracts.card_top_label", "REWARD PIÙ RICCO PRONTO")}
                    </div>
                    <div className="flex items-center justify-between text-foreground/90">
                        <span className="truncate" title={topClaim.slug}>
                            {topClaim.slug}
                        </span>
                        <span className="text-amber font-bold tabular-nums ml-2 shrink-0">
                            +{topClaim.reward_gold}g
                        </span>
                    </div>
                </div>
            )}
        </Link>
    );
}
