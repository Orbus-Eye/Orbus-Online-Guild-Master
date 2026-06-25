import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { Button } from "../components/ui/button";
import { useT } from "../i18n/I18nContext";

const API = (process.env.REACT_APP_BACKEND_URL || "") + "/api";

import { formatDateShort as fmtDate } from "../utils/dateFormat";

const RankBadge = ({ rank }) => {
    if (rank === 1)
        return (
            <span className="text-amber font-semibold" data-testid="rank-1">
                🏆 #1
            </span>
        );
    if (rank === 2)
        return (
            <span className="text-foreground/90 font-semibold" data-testid="rank-2">
                🥈 #2
            </span>
        );
    if (rank === 3)
        return (
            <span className="text-foreground/80 font-semibold" data-testid="rank-3">
                🥉 #3
            </span>
        );
    return <span className="text-muted-foreground">#{rank}</span>;
};

const DungeonTier = ({ slug }) => {
    if (!slug)
        return (
            <span className="text-muted-foreground text-xs italic">—</span>
        );
    const colorBySlug = {
        "goblin-warrens": "text-[#9ca3af]",
        "shadow-crypts": "text-[#a78bfa]",
        "dragons-hoard": "text-[#f59e0b]",
    };
    const color = colorBySlug[slug] || "text-foreground";
    return (
        <span className={`text-xs font-mono ${color}`}>{slug}</span>
    );
};

const Skeleton = () => (
    <tr className="border-t border-border" data-testid="leaderboard-skeleton-row">
        {[...Array(7)].map((_, i) => (
            <td key={`lb-skel-${i}`} className="px-3 py-3">
                <div className="h-3 bg-secondary rounded-sm w-full" />
            </td>
        ))}
    </tr>
);

export default function Leaderboard() {
    const { t, lang } = useT();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [refreshing, setRefreshing] = useState(false);

    const fetchData = useCallback(async () => {
        setRefreshing(true);
        setError(null);
        try {
            const r = await axios.get(`${API}/leaderboard/guilds?limit=50&offset=0`, {
                timeout: 15000,
            });
            setData(r.data);
        } catch (err) {
            setError(err?.response?.data?.detail || err.message || "Failed to load");
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    const entries = data?.entries || [];

    return (
        <div className="min-h-screen bg-background text-foreground term-grid-bg term-scanline">
            <header className="border-b border-border bg-background/95 backdrop-blur sticky top-0 z-20">
                <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
                    <Link
                        to="/"
                        data-testid="leaderboard-brand-link"
                        className="flex items-center gap-2 text-xs whitespace-nowrap text-muted-foreground hover:text-foreground"
                    >
                        <span className="text-amber">◆</span>
                        <span className="tracking-widest">{`ORBUS // ${t("leaderboard_page.brand_subtitle")}`}</span>
                    </Link>
                    <div className="flex items-center gap-2 text-xs">
                        <Link
                            to="/login"
                            data-testid="leaderboard-login-link"
                            className="text-muted-foreground hover:text-foreground border border-border px-2 py-1 rounded-sm hover:bg-secondary"
                        >
                            login
                        </Link>
                    </div>
                </div>
            </header>

            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
                <section className="mb-8">
                    <div className="text-xs text-amber tracking-widest mb-2">
                        :: PUBLIC RANKING
                    </div>
                    <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
                        <div>
                            <h1
                                data-testid="leaderboard-title"
                                className="text-3xl sm:text-4xl font-semibold tracking-tight"
                            >
                                {t("leaderboard.title")}
                            </h1>
                            <p className="text-sm text-muted-foreground mt-2 max-w-2xl">
                                Ranked by peak team power ever recorded. Tie-break by
                                level, then reputation, then guild age.
                            </p>
                        </div>
                        <Button
                            type="button"
                            onClick={fetchData}
                            disabled={refreshing}
                            data-testid="leaderboard-refresh-btn"
                            variant="outline"
                            className="rounded-sm h-9 border-border bg-transparent hover:bg-secondary text-xs tracking-widest"
                        >
                            {refreshing ? "refreshing…" : "↻ refresh"}
                        </Button>
                    </div>
                </section>

                {error && (
                    <div
                        className="border border-[#ef4444]/55 bg-[#ef4444]/5 text-[#fca5a5] rounded-sm p-3 text-xs mb-6"
                        data-testid="leaderboard-error"
                    >
                        {error}
                    </div>
                )}

                {/* Desktop table */}
                <div
                    className="hidden sm:block border border-border bg-card rounded-sm overflow-hidden"
                    data-testid="leaderboard-table"
                >
                    <table className="w-full text-sm">
                        <thead className="bg-secondary/60 text-[10px] tracking-widest text-muted-foreground">
                            <tr>
                                <th className="px-3 py-2 text-left">{t("leaderboard_page.rank")}</th>
                                <th className="px-3 py-2 text-left">{t("leaderboard_page.guild")}</th>
                                <th className="px-3 py-2 text-right">{t("leaderboard_page.peak_pwr_short")}</th>
                                <th className="px-3 py-2 text-right">{t("leaderboard_page.level_short")}</th>
                                <th className="px-3 py-2 text-right">{t("leaderboard_page.reputation_short")}</th>
                                <th className="px-3 py-2 text-left">{t("leaderboard_page.highest")}</th>
                                <th className="px-3 py-2 text-right">{t("leaderboard_page.expeditions_short")}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading &&
                                [...Array(6)].map((_, i) => (
                                    <Skeleton key={`skel-${i}`} />
                                ))}
                            {!loading && entries.length === 0 && (
                                <tr>
                                    <td
                                        colSpan={7}
                                        className="px-3 py-8 text-center text-xs text-muted-foreground italic"
                                        data-testid="leaderboard-empty"
                                    >
                                        No guilds in leaderboard yet
                                    </td>
                                </tr>
                            )}
                            {!loading &&
                                entries.map((e) => (
                                    <tr
                                        key={e.guild_id}
                                        data-testid={`leaderboard-row-${e.rank}`}
                                        className="border-t border-border hover:bg-secondary/30 transition-colors"
                                    >
                                        <td className="px-3 py-3">
                                            <RankBadge rank={e.rank} />
                                        </td>
                                        <td className="px-3 py-3">
                                            <div
                                                className="font-medium"
                                                data-testid={`leaderboard-guild-name-${e.rank}`}
                                            >
                                                {e.guild_name}
                                            </div>
                                            <div className="text-[10px] text-muted-foreground">
                                                {t("leaderboard.founded_at", { at: fmtDate(e.created_at, lang) })}
                                            </div>
                                        </td>
                                        <td
                                            className="px-3 py-3 text-right font-semibold text-amber"
                                            data-testid={`leaderboard-peak-${e.rank}`}
                                        >
                                            {e.max_team_power_ever}
                                        </td>
                                        <td className="px-3 py-3 text-right">
                                            {e.level}
                                        </td>
                                        <td className="px-3 py-3 text-right">
                                            {e.reputation}
                                        </td>
                                        <td className="px-3 py-3">
                                            <DungeonTier slug={e.highest_dungeon_slug} />
                                        </td>
                                        <td className="px-3 py-3 text-right text-muted-foreground">
                                            {e.total_expeditions_completed}
                                        </td>
                                    </tr>
                                ))}
                        </tbody>
                    </table>
                </div>

                {/* Mobile stacked cards */}
                <div className="sm:hidden space-y-3" data-testid="leaderboard-cards-mobile">
                    {loading &&
                        [...Array(4)].map((_, i) => (
                            <div
                                key={`m-skel-${i}`}
                                className="border border-border bg-card rounded-sm p-4 h-24 animate-pulse"
                            />
                        ))}
                    {!loading && entries.length === 0 && (
                        <div className="text-center text-xs text-muted-foreground italic py-8">
                            No guilds in leaderboard yet
                        </div>
                    )}
                    {!loading &&
                        entries.map((e) => (
                            <div
                                key={e.guild_id}
                                data-testid={`leaderboard-card-${e.rank}`}
                                className="border border-border bg-card rounded-sm p-4"
                            >
                                <div className="flex items-center justify-between mb-2">
                                    <RankBadge rank={e.rank} />
                                    <span className="text-amber font-semibold">
                                        {e.max_team_power_ever} pwr
                                    </span>
                                </div>
                                <div className="font-medium text-sm">
                                    {e.guild_name}
                                </div>
                                <div className="text-[10px] text-muted-foreground mt-2 flex flex-wrap gap-x-3 gap-y-1">
                                    <span>lvl {e.level}</span>
                                    <span>rep {e.reputation}</span>
                                    <span>{e.total_expeditions_completed} exp</span>
                                    {e.highest_dungeon_slug && (
                                        <DungeonTier slug={e.highest_dungeon_slug} />
                                    )}
                                </div>
                            </div>
                        ))}
                </div>

                {!loading && data && (
                    <div
                        className="text-[10px] text-muted-foreground mt-4 tracking-widest"
                        data-testid="leaderboard-meta"
                    >
                        showing {entries.length} of {data.total} guilds · ordered by peak
                        team power
                    </div>
                )}
            </main>

            <footer className="max-w-6xl mx-auto px-4 sm:px-6 py-6 text-xs text-muted-foreground border-t border-border">
                <span className="text-amber">$</span> orbus --leaderboard --public · raise
                your peak in{" "}
                <Link
                    to="/dungeons"
                    className="text-amber hover:underline"
                    data-testid="leaderboard-footer-dungeons-link"
                >
                    Dungeons
                </Link>
            </footer>
        </div>
    );
}
