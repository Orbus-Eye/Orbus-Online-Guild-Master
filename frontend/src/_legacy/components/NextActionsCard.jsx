// ROUND 16.1 Phase 1 — Dashboard data-driven "Prossime Azioni" card.
// Pulls from GET /api/dashboard/suggestions. Renders up to 5 priority-sorted
// next-actions, each linking to the relevant page. Pure UI; backend chooses
// what to show. Bilingual (IT/EN) — picks the right field from the i18n ctx.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useT } from "../i18n/I18nContext";

export default function NextActionsCard() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const { lang } = useT();

    useEffect(() => {
        let cancelled = false;
        api.get("/dashboard/suggestions")
            .then((r) => { if (!cancelled) setData(r.data); })
            .catch(() => { if (!cancelled) setData({ suggestions: [] }); })
            .finally(() => { if (!cancelled) setLoading(false); });
        return () => { cancelled = true; };
    }, []);

    const it = lang === "it";
    const headerTitle = it ? "PROSSIME AZIONI CONSIGLIATE" : "NEXT RECOMMENDED ACTIONS";

    if (loading) {
        return (
            <section className="border border-border bg-card rounded-sm p-4" data-testid="next-actions-card">
                <div className="text-[10px] text-muted-foreground tracking-widest mb-2">{headerTitle}</div>
                <div className="text-xs text-muted-foreground">…</div>
            </section>
        );
    }

    const suggestions = data?.suggestions || [];
    if (suggestions.length === 0) return null;

    return (
        <section className="border border-border bg-card rounded-sm p-4" data-testid="next-actions-card">
            <div className="text-[10px] text-muted-foreground tracking-widest mb-3">
                {headerTitle}
            </div>
            <ul className="space-y-1.5">
                {suggestions.map((s) => (
                    <li key={s.id} data-testid={`next-action-${s.id}`}>
                        <Link
                            to={s.link}
                            className="flex items-center justify-between gap-3 border border-border/60 rounded-sm px-3 py-2 hover:bg-secondary/50 transition-colors"
                        >
                            <span className="flex items-center gap-2 min-w-0">
                                <span className="text-amber/85" aria-hidden="true">{s.icon}</span>
                                <span className="text-sm text-foreground truncate">
                                    {it ? s.title_it : s.title_en}
                                </span>
                            </span>
                            <span className="text-[10px] tracking-widest text-amber/85 shrink-0">
                                {it ? s.cta_it : s.cta_en} →
                            </span>
                        </Link>
                    </li>
                ))}
            </ul>
        </section>
    );
}
