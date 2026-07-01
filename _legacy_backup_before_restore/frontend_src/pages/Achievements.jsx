import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import AppHeader from "@/components/AppHeader";

// ROUND 15 — Phase 3 — Achievements page
const CAT_IT = {
    primi_passi: "Primi Passi",
    roster: "Roster",
    dungeon: "Dungeon",
    raid: "Raid",
    equipaggiamento: "Equipaggiamento",
    classi_stats: "Classi e Statistiche",
    territorio: "Territorio",
    crafting: "Fucina",
    economia: "Economia",
    pvp_stagioni: "PvP / Stagioni",
    leaderboard: "Leaderboard",
    consorzi: "Consorzi",
    lore: "Lore & Esplorazione",
    meta_beta: "Segrete",
};

const FILTERS = [
    { key: "all", label: "Tutti" },
    { key: "in_progress", label: "In corso" },
    { key: "completed", label: "Completati" },
];

function XPBar({ progress }) {
    const into = progress?.xp_into_level ?? 0;
    const span = (progress?.next_level_at ?? 0) - (progress?.xp ?? 0) + into;
    const pct = span > 0 ? Math.min(100, Math.floor((into / span) * 100)) : 0;
    return (
        <div className="w-full">
            <div className="flex justify-between text-[10px] text-muted-foreground mb-1">
                <span data-testid="guild-level-label">Lv {progress?.level ?? 1}</span>
                <span data-testid="guild-xp-progress">
                    {into} / {span} XP
                </span>
            </div>
            <div className="h-2 bg-card border border-border rounded-sm overflow-hidden">
                <div
                    data-testid="guild-xp-fill"
                    className="h-full bg-amber/80 transition-all"
                    style={{ width: `${pct}%` }}
                />
            </div>
        </div>
    );
}

function AchievementRow({ entry, progress }) {
    const done = progress?.completed_at != null;
    const current = progress?.progress_current ?? 0;
    const target = entry.progress_target ?? 1;
    const pct = target > 0 ? Math.min(100, Math.floor((current / target) * 100)) : 0;
    return (
        <li
            data-testid={`achievement-row-${entry.slug}`}
            className={`border ${done ? "border-amber/40" : "border-border"} bg-card rounded-sm p-3 flex items-start gap-3`}
        >
            <div className="text-lg pt-0.5" aria-hidden>
                {done ? "✓" : entry.is_hidden ? "?" : "◇"}
            </div>
            <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                    <div className="font-medium truncate">{entry.name_it}</div>
                    <div className="text-[10px] text-muted-foreground whitespace-nowrap">
                        {entry.points} pt · +{entry.guild_xp_reward} XP
                    </div>
                </div>
                <div className="text-[11px] text-muted-foreground mt-1">
                    {entry.description_it}
                </div>
                {!done && (
                    <div className="mt-2">
                        <div className="h-1.5 bg-background border border-border rounded-sm overflow-hidden">
                            <div className="h-full bg-amber/60" style={{ width: `${pct}%` }} />
                        </div>
                        <div className="text-[10px] text-muted-foreground mt-1">
                            {current} / {target}
                        </div>
                    </div>
                )}
                {done && (
                    <div className="text-[10px] text-amber mt-2">
                        Completato · {entry.reward_payload?.title_it && (
                            <span>Titolo: <em>{entry.reward_payload.title_it}</em></span>
                        )}
                        {entry.reward_payload?.badge_slug && (
                            <span>Badge: {entry.reward_payload.badge_slug}</span>
                        )}
                        {entry.reward_payload?.frame_slug && (
                            <span>Cornice: {entry.reward_payload.frame_slug}</span>
                        )}
                    </div>
                )}
            </div>
        </li>
    );
}

export default function Achievements() {
    const [summary, setSummary] = useState(null);
    const [catalog, setCatalog] = useState([]);
    const [progress, setProgress] = useState([]);
    const [filter, setFilter] = useState("all");
    const [category, setCategory] = useState("all");
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let cancelled = false;
        (async () => {
            setLoading(true);
            try {
                const [s, c, p] = await Promise.all([
                    api.get("/achievements/summary"),
                    api.get(`/achievements/catalog${filter !== "all" ? `?state=${filter}` : ""}`),
                    api.get("/achievements/progress"),
                ]);
                if (!cancelled) {
                    setSummary(s.data);
                    setCatalog(s.data ? (c.data.achievements || []) : []);
                    setProgress(p.data.progress || []);
                }
            } finally {
                if (!cancelled) setLoading(false);
            }
        })();
        return () => {
            cancelled = true;
        };
    }, [filter]);

    const progressBySlug = useMemo(() => {
        const m = {};
        for (const p of progress) m[p.achievement_slug] = p;
        return m;
    }, [progress]);

    const categories = useMemo(() => {
        const set = new Set(catalog.map((c) => c.category));
        return ["all", ...Array.from(set).sort()];
    }, [catalog]);

    const visible = useMemo(() => {
        const filtered = category === "all" ? catalog : catalog.filter((c) => c.category === category);
        const grouped = {};
        for (const e of filtered) {
            grouped[e.category] = grouped[e.category] || [];
            grouped[e.category].push(e);
        }
        return grouped;
    }, [catalog, category]);

    return (
        <div className="min-h-screen bg-background text-foreground">
            <AppHeader />
            <main className="max-w-5xl mx-auto px-4 py-6">
                <h1 className="text-2xl font-light mb-6" data-testid="achievements-title">
                    Imprese di Gilda
                </h1>
                {summary && (
                    <section data-testid="achievements-summary" className="border border-border bg-card rounded-sm p-4 mb-6">
                        <div className="text-[10px] text-muted-foreground tracking-widest mb-3">
                            :: PROGRESSO GILDA
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                            <div>
                                <div className="text-[10px] text-muted-foreground">LIVELLO GILDA</div>
                                <div data-testid="guild-level" className="text-3xl font-light text-amber">
                                    Lv {summary.guild_level}
                                </div>
                            </div>
                            <div>
                                <div className="text-[10px] text-muted-foreground">XP TOTALE</div>
                                <div data-testid="guild-xp-total" className="text-3xl font-light">
                                    {summary.guild_xp}
                                </div>
                            </div>
                            <div>
                                <div className="text-[10px] text-muted-foreground">PUNTI IMPRESE</div>
                                <div data-testid="guild-points" className="text-3xl font-light">
                                    {summary.achievement_points}
                                </div>
                            </div>
                        </div>
                        <div className="mt-4">
                            <XPBar progress={summary.progress} />
                        </div>
                        <div className="text-[11px] text-muted-foreground mt-3">
                            <span data-testid="completed-count">{summary.completed_count}</span> di{" "}
                            <span data-testid="total-catalog">{summary.total_catalog_count}</span> imprese completate
                        </div>
                    </section>
                )}

                <div className="flex flex-wrap items-center gap-2 mb-4">
                    {FILTERS.map((f) => (
                        <button
                            key={f.key}
                            data-testid={`filter-${f.key}`}
                            onClick={() => setFilter(f.key)}
                            className={`text-xs px-3 py-1 border rounded-sm transition-colors ${
                                filter === f.key
                                    ? "border-amber/60 text-amber"
                                    : "border-border text-muted-foreground hover:text-foreground"
                            }`}
                        >
                            {f.label}
                        </button>
                    ))}
                    <select
                        data-testid="category-filter"
                        value={category}
                        onChange={(e) => setCategory(e.target.value)}
                        className="bg-card text-xs border border-border rounded-sm px-2 py-1 text-foreground"
                    >
                        {categories.map((c) => (
                            <option key={c} value={c}>
                                {c === "all" ? "Tutte le categorie" : (CAT_IT[c] || c)}
                            </option>
                        ))}
                    </select>
                </div>

                {loading && (
                    <div className="text-xs text-muted-foreground">Caricamento imprese…</div>
                )}
                {!loading && Object.keys(visible).length === 0 && (
                    <div data-testid="achievements-empty" className="text-xs text-muted-foreground border border-border bg-card rounded-sm p-4">
                        Nessuna impresa in questa vista.
                    </div>
                )}
                {!loading && Object.keys(visible).sort().map((catKey) => (
                    <section key={catKey} className="mb-6">
                        <div className="text-[10px] text-muted-foreground tracking-widest mb-3">
                            :: {(CAT_IT[catKey] || catKey).toUpperCase()}
                        </div>
                        <ul data-testid={`achievement-category-${catKey}`} className="space-y-2">
                            {visible[catKey].map((e) => (
                                <AchievementRow
                                    key={e.slug}
                                    entry={e}
                                    progress={progressBySlug[e.slug]}
                                />
                            ))}
                        </ul>
                    </section>
                ))}

                <div className="mt-6 text-[11px] text-muted-foreground">
                    <Link
                        to="/dashboard"
                        data-testid="back-to-dashboard"
                        className="hover:text-foreground"
                    >
                        ← torna alla Dashboard
                    </Link>
                </div>
            </main>
        </div>
    );
}
