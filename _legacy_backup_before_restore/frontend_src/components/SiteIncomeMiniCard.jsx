// ROUND 16.3 Phase 3 — Dashboard mini card for site income.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";

export default function SiteIncomeMiniCard() {
    const [today, setToday] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const { data } = await api.get("/site-income/today");
                if (!cancelled) setToday(data);
            } catch {
                // Silent (guild-less user, etc.)
            } finally {
                if (!cancelled) setLoading(false);
            }
        })();
        return () => { cancelled = true; };
    }, []);

    if (loading || !today) return null;
    const claimed = !!today.claimed_at;

    return (
        <Link
            to="/site-contracts"
            data-testid="dashboard-site-income-card"
            className="block border border-border bg-card rounded-sm p-4 hover:border-amber/40 transition-colors group"
        >
            <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] text-amber tracking-widest font-bold">
                    :: INCARICHI DI SEDE
                </span>
                <span className="text-[10px] text-amber group-hover:translate-x-0.5 transition-transform">
                    →
                </span>
            </div>
            <div className="text-sm text-foreground">
                {claimed ? (
                    <span>
                        Reclamati oggi:{" "}
                        <span className="text-muted-foreground">
                            {today.total_amount} oro
                        </span>
                    </span>
                ) : (
                    <span>
                        <span data-testid="dashboard-site-income-amount"
                              className="text-amber">
                            {today.total_amount} oro
                        </span>{" "}
                        pronti da reclamare
                    </span>
                )}
            </div>
            {(today.breakdown?.event_modifier_pct ?? 0) !== 0 && (
                <div className="text-[10px] text-muted-foreground mt-1">
                    evento continentale{" "}
                    {today.breakdown.event_modifier_pct > 0 ? "+" : ""}
                    {today.breakdown.event_modifier_pct}%
                </div>
            )}
        </Link>
    );
}
