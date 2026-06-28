// ROUND 6B.4 Task 1 — Roster Health widget.
//
// Visualises the 4-state roster health (Healthy / Filling / At cap / Over cap)
// computed from `GET /api/roster/health`. Replaces the inline duplicated
// over-cap snippet that used to live in `Dashboard.jsx` and centralises the
// thresholds (0.7 / 0.9 / 1.0).
//
// • Healthy : current ≤ cap * 0.7  → green border / muted bar
// • Filling : 0.7 < ratio ≤ 0.9    → amber border / amber bar
// • At cap  : 0.9 < ratio ≤ 1.0    → orange border / orange bar
// • Over cap: ratio > 1.0          → red border + warning CTA (links territory)
//
// The card is intentionally read-only — actions live on /territory and
// /roster/manage. Click anywhere → navigates to /territory.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useT } from "../i18n/I18nContext";

const STATE_STYLE = {
    healthy: {
        border: "border-emerald-500/40",
        bar: "bg-emerald-500/80",
        label: "rosterHealth.state_healthy",
        dot: "bg-emerald-500",
    },
    filling: {
        border: "border-amber/50",
        bar: "bg-amber/80",
        label: "rosterHealth.state_filling",
        dot: "bg-amber",
    },
    at_cap: {
        border: "border-orange-500/60",
        bar: "bg-orange-500/80",
        label: "rosterHealth.state_at_cap",
        dot: "bg-orange-500",
    },
    over_cap: {
        border: "border-red-500/70",
        bar: "bg-red-500/90",
        label: "rosterHealth.state_over_cap",
        dot: "bg-red-500",
    },
};

export default function RosterHealthCard() {
    const { t } = useT();
    const [data, setData] = useState(null);
    const [error, setError] = useState(false);

    useEffect(() => {
        api.get("/roster/health")
            .then((r) => setData(r.data))
            .catch(() => setError(true));
    }, []);

    if (error) {
        return (
            <div
                data-testid="roster-health-error"
                className="border border-red-500/40 bg-red-500/5 rounded-sm p-3 text-[11px] text-red-300"
            >
                {t("rosterHealth.error", "Impossibile caricare lo stato del roster")}
            </div>
        );
    }
    if (!data) {
        return (
            <div
                data-testid="roster-health-loading"
                className="border border-border bg-card rounded-sm p-4 text-[11px] text-muted-foreground"
            >
                {t("rosterHealth.loading", "Caricamento stato roster…")}
            </div>
        );
    }

    const { current, cap, headroom, dormitory_level: dormLevel, state } = data;
    const style = STATE_STYLE[state] || STATE_STYLE.healthy;
    const ratio = cap > 0 ? Math.min(100, Math.round((current / cap) * 100)) : 0;
    const isOverCap = state === "over_cap";

    return (
        <Link
            to="/territory"
            data-testid="roster-health-card"
            className={`block border-2 ${style.border} bg-card rounded-sm p-4 transition-colors hover:bg-secondary/30`}
        >
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${style.dot}`} aria-hidden="true" />
                    <span
                        className="text-[10px] tracking-widest font-bold text-foreground/90"
                        data-testid="roster-health-state-label"
                    >
                        :: {t(style.label)}
                    </span>
                </div>
                <span className="text-[10px] text-amber">→</span>
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div>
                    <div className="text-[10px] text-muted-foreground tracking-widest mb-1">
                        {t("rosterHealth.adventurers_label")}
                    </div>
                    <div
                        className="text-2xl font-semibold text-foreground"
                        data-testid="roster-health-count"
                    >
                        <span className={isOverCap ? "text-red-400" : ""}>{current}</span>
                        <span className="text-muted-foreground text-base">/{cap}</span>
                    </div>
                    <div className="w-full bg-secondary h-1.5 rounded-sm mt-2 overflow-hidden">
                        <div
                            className={`h-full ${style.bar} transition-all`}
                            style={{ width: `${ratio}%` }}
                            data-testid="roster-health-bar"
                        />
                    </div>
                </div>
                <div>
                    <div className="text-[10px] text-muted-foreground tracking-widest mb-1">
                        {t("rosterHealth.headroom_label")}
                    </div>
                    <div
                        className="text-2xl font-semibold text-foreground"
                        data-testid="roster-health-headroom"
                    >
                        {isOverCap ? (
                            <span className="text-red-400">−{Math.abs(headroom)}</span>
                        ) : (
                            <span>{headroom}</span>
                        )}
                    </div>
                    <div className="text-[10px] text-muted-foreground mt-1">
                        {t("rosterHealth.dorm_level_label", { n: dormLevel })}
                    </div>
                </div>
            </div>

            {isOverCap && (
                <div
                    data-testid="roster-health-overcap-cta"
                    className="mt-3 pt-3 border-t border-red-500/30 text-[11px] text-red-200"
                >
                    {t("rosterHealth.overcap_hint")}
                </div>
            )}
        </Link>
    );
}
