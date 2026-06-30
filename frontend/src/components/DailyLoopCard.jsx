// ROUND 16.1 Phase 1 — "Cosa fare oggi" daily loop card.
// Pulls GET /api/dashboard/daily-loop, renders 6 daily steps with ✓/⏳
// status. No rewards, just guidance. Resets at UTC midnight server-side.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useT } from "../i18n/I18nContext";
import { Check, Clock } from "lucide-react";

export default function DailyLoopCard() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const { lang } = useT();
    const it = lang === "it";

    useEffect(() => {
        let cancelled = false;
        api.get("/dashboard/daily-loop")
            .then((r) => { if (!cancelled) setData(r.data); })
            .catch(() => { if (!cancelled) setData(null); })
            .finally(() => { if (!cancelled) setLoading(false); });
        return () => { cancelled = true; };
    }, []);

    if (loading || !data) return null;

    const headerTitle = it ? "COSA FARE OGGI" : "WHAT TO DO TODAY";
    const subLabel = it ? "azioni di oggi" : "today's actions";

    return (
        <section
            className="border border-border bg-card rounded-sm p-4"
            data-testid="daily-loop-card"
        >
            <header className="flex items-baseline justify-between gap-3 mb-3 flex-wrap">
                <div>
                    <div className="text-[10px] text-muted-foreground tracking-widest">
                        {headerTitle}
                    </div>
                    <div className="text-[11px] text-amber/80 mt-1">
                        {data.completed_count}/{data.total_count} {subLabel}
                    </div>
                </div>
                <div className="text-[10px] text-muted-foreground tracking-widest">
                    {data.date}
                </div>
            </header>

            <ul className="space-y-1.5">
                {data.items.map((it_step) => {
                    const title = it ? it_step.title_it : it_step.title_en;
                    return (
                        <li
                            key={it_step.id}
                            data-testid={`daily-loop-item-${it_step.id}`}
                        >
                            <Link
                                to={it_step.link}
                                className={`flex items-center justify-between gap-3 border border-border/60 rounded-sm px-3 py-2 transition-colors ${
                                    it_step.completed
                                        ? "bg-secondary/30"
                                        : "hover:bg-secondary/50"
                                }`}
                            >
                                <span className="flex items-center gap-2 min-w-0">
                                    {it_step.completed ? (
                                        <Check size={14} className="text-emerald-400/90 shrink-0" />
                                    ) : (
                                        <Clock size={14} className="text-muted-foreground/80 shrink-0" />
                                    )}
                                    <span
                                        className={`text-sm truncate ${
                                            it_step.completed
                                                ? "text-muted-foreground line-through"
                                                : "text-foreground"
                                        }`}
                                    >
                                        {title}
                                    </span>
                                </span>
                                {!it_step.completed && (
                                    <span className="text-[10px] tracking-widest text-amber/80 shrink-0">
                                        →
                                    </span>
                                )}
                            </Link>
                        </li>
                    );
                })}
            </ul>
        </section>
    );
}
