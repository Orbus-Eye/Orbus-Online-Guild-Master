import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";

// ROUND 15 — Phase 3 — Dashboard card
export default function GuildProgressCard() {
    const [summary, setSummary] = useState(null);
    const [nextUp, setNextUp] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let cancelled = false;
        (async () => {
            setLoading(true);
            try {
                const [s, c, p] = await Promise.all([
                    api.get("/achievements/summary"),
                    api.get("/achievements/catalog?state=in_progress"),
                    api.get("/achievements/progress"),
                ]);
                if (cancelled) return;
                setSummary(s.data);
                // Pick top 3 not-completed achievements with the highest progress %
                const progressBySlug = {};
                for (const row of (p.data.progress || [])) {
                    progressBySlug[row.achievement_slug] = row;
                }
                const ranked = (c.data.achievements || [])
                    .filter((e) => !progressBySlug[e.slug]?.completed_at)
                    .map((e) => ({
                        entry: e,
                        progress: progressBySlug[e.slug] || { progress_current: 0, progress_target: e.progress_target },
                    }))
                    .map((pp) => ({
                        ...pp,
                        pct: pp.progress.progress_target > 0
                            ? pp.progress.progress_current / pp.progress.progress_target
                            : 0,
                    }))
                    .sort((a, b) => b.pct - a.pct)
                    .slice(0, 3);
                setNextUp(ranked);
            } finally {
                if (!cancelled) setLoading(false);
            }
        })();
        return () => {
            cancelled = true;
        };
    }, []);

    if (loading) {
        return (
            <div
                data-testid="guild-progress-card-loading"
                className="border border-border bg-card rounded-sm p-4 text-xs text-muted-foreground"
            >
                Caricamento progresso gilda…
            </div>
        );
    }
    if (!summary) return null;

    const into = summary.progress?.xp_into_level || 0;
    const span = (summary.progress?.next_level_at || 0) - summary.guild_xp + into;
    const pct = span > 0 ? Math.min(100, Math.floor((into / span) * 100)) : 0;

    return (
        <div
            data-testid="guild-progress-card"
            className="border border-border bg-card rounded-sm p-4"
        >
            <div className="flex items-center justify-between mb-2">
                <div className="text-[10px] text-muted-foreground tracking-widest">
                    :: PRESTIGIO DI GILDA
                </div>
                <Link
                    to="/achievements"
                    data-testid="link-achievements"
                    className="text-[11px] text-amber hover:underline"
                >
                    Vedi tutte le Imprese →
                </Link>
            </div>

            <div className="flex items-baseline gap-4 mb-3">
                <div>
                    <div className="text-[10px] text-muted-foreground">LV PRESTIGIO</div>
                    <div className="text-2xl font-light text-amber" data-testid="card-guild-level">
                        Lv {summary.guild_level}
                    </div>
                </div>
                <div className="flex-1">
                    <div className="flex justify-between text-[10px] text-muted-foreground mb-1">
                        <span>{into} / {span} XP Prestigio</span>
                        <span data-testid="card-points">{summary.achievement_points} pt</span>
                    </div>
                    <div className="h-2 bg-background border border-border rounded-sm overflow-hidden">
                        <div
                            className="h-full bg-amber/80"
                            style={{ width: `${pct}%` }}
                            data-testid="card-xp-fill"
                        />
                    </div>
                </div>
            </div>

            {/* ROUND 16.5.3 P1 — "Cosa fare per salire" (drip XP hint) */}
            <div
                data-testid="how-to-level-up"
                className="mb-3 pt-3 border-t border-border/50"
            >
                <div className="text-[10px] text-muted-foreground mb-1 tracking-widest">
                    :: COSA FARE PER SALIRE
                </div>
                <ul className="text-[11px] space-y-1 text-foreground/80">
                    <li data-testid="hint-expedition"
                        className="flex items-center justify-between gap-2">
                        <span>Completa una spedizione</span>
                        <span className="text-amber/80 font-mono whitespace-nowrap">+15 XP</span>
                    </li>
                    <li data-testid="hint-raid"
                        className="flex items-center justify-between gap-2">
                        <span>Vinci un raid</span>
                        <span className="text-amber/80 font-mono whitespace-nowrap">+80 XP</span>
                    </li>
                    <li data-testid="hint-resource-mission"
                        className="flex items-center justify-between gap-2">
                        <span>Completa una missione risorse</span>
                        <span className="text-amber/80 font-mono whitespace-nowrap">+10 XP</span>
                    </li>
                </ul>
            </div>

            {nextUp.length > 0 && (
                <div data-testid="next-up-list">
                    <div className="text-[10px] text-muted-foreground mb-1">
                        Prossime imprese
                    </div>
                    <ul className="text-[11px] space-y-1">
                        {nextUp.map((n) => (
                            <li
                                key={n.entry.slug}
                                data-testid={`next-up-${n.entry.slug}`}
                                className="flex items-center justify-between gap-2"
                            >
                                <span className="truncate">{n.entry.name_it}</span>
                                <span className="text-muted-foreground whitespace-nowrap">
                                    {n.progress.progress_current}/{n.progress.progress_target}
                                </span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}
