// ROUND 16.3 Phase 3 — Slim banner for active continent event.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";

export default function ContinentEventBanner() {
    const [data, setData] = useState(null);

    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const { data } = await api.get("/world-events/mine");
                if (!cancelled) setData(data);
            } catch {
                if (!cancelled) setData(null);
            }
        })();
        return () => { cancelled = true; };
    }, []);

    if (!data?.active) return null;
    const cat = data.active.catalog;
    const v = cat?.modifier_value || 0;
    const modText = cat?.modifier_type === "site_income_pct"
        ? `${v > 0 ? "+" : ""}${v}% entrate sedi`
        : null;

    return (
        <Link
            to="/world-events"
            data-testid="dashboard-event-banner"
            className="block border border-amber/30 bg-amber/5 rounded-sm p-3 hover:border-amber/60 transition-colors"
        >
            <div className="flex items-center justify-between gap-2 flex-wrap">
                <div>
                    <div className="text-[10px] text-amber tracking-widest">
                        :: EVENTO CONTINENTALE
                    </div>
                    <div className="text-[13px] text-foreground mt-1">
                        {cat?.name_it}
                        {modText ? (
                            <span className="text-[10px] text-amber ml-2">
                                {modText}
                            </span>
                        ) : null}
                    </div>
                </div>
                <span className="text-[10px] text-amber">→</span>
            </div>
        </Link>
    );
}
