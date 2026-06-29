// ROUND 11.3 Fase 3D — Multi-category leaderboard.
//
// Replaces the legacy single-table layout (peak-power only) with a Tabs
// (desktop) / Dropdown (mobile) selector over 8 categories served by
// `GET /api/leaderboard?category=<slug>&limit=50`. Persists the selected
// category in the URL `?category=` query string so a link to a specific
// ranking is shareable + survives back/forward navigation.
//
// Layout decisions:
//   * Header label/description come from the payload (server-authoritative
//     IT copy). FE never invents category names.
//   * `is_me=true` row → amber highlight + "👤" marker.
//   * `my_entry != null` AND `my_entry.rank > 50` → "La tua posizione"
//     card pinned above the table.
//   * `roster_avg_level` → score / 100 displayed as "Lv X.YZ".
//   * Skeleton during fetch; empty state IT if entries.length < 3.
import { useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import axios from "axios";

import { useT } from "../i18n/I18nContext";

const API = (process.env.REACT_APP_BACKEND_URL || "") + "/api";

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

const SkeletonRow = ({ i }) => (
    <tr className="border-t border-border" data-testid="leaderboard-skeleton-row">
        {[...Array(3)].map((_, k) => (
            <td key={`lb-skel-${i}-${k}`} className="px-3 py-3">
                <div className="h-3 bg-secondary rounded-sm w-full" />
            </td>
        ))}
    </tr>
);

function formatScore(category, score) {
    // `roster_avg_level` returns score as avg×100; render as a decimal.
    if (category === "roster_avg_level") {
        return `Lv ${(Number(score) / 100).toFixed(2)}`;
    }
    return Number(score).toLocaleString("it-IT");
}

export default function Leaderboard() {
    const { t } = useT();
    const [searchParams, setSearchParams] = useSearchParams();
    const initialCategory = searchParams.get("category") || "peak_power";

    const [categories, setCategories] = useState([]);
    const [category, setCategory] = useState(initialCategory);
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Categories catalog (single fetch on mount).
    useEffect(() => {
        let cancelled = false;
        axios.get(`${API}/leaderboard/categories`, { timeout: 10_000 })
            .then((r) => {
                if (cancelled) return;
                setCategories(r.data.categories || []);
            })
            .catch(() => {
                if (cancelled) return;
                // Fallback: a hard-coded 8 slugs to keep the picker usable
                // if the catalog endpoint flakes. Labels remain blank → the
                // server-side category fetch will still populate the header.
                setCategories([
                    "peak_power", "raid_score", "dungeon_clears", "raid_clears",
                    "territory_score", "contracts_completed", "training_score",
                    "roster_avg_level",
                ].map((s) => ({ slug: s, label_it: s, description_it: "" })));
            });
        return () => { cancelled = true; };
    }, []);

    // Fetch category rows.
    const fetchCategory = useCallback(async (slug) => {
        setLoading(true);
        setError(null);
        try {
            // ROUND 11.4a — cookie auth is the canonical flow (withCredentials).
            // Bearer-from-localStorage fallback removed; the public LB endpoint
            // accepts unauthenticated callers anyway.
            const r = await axios.get(
                `${API}/leaderboard?category=${encodeURIComponent(slug)}&limit=50`,
                { timeout: 15_000, withCredentials: true },
            );
            setData(r.data);
        } catch (err) {
            // ROUND 11.4b — explicit error log (no more silent catch).
            console.error("[Leaderboard] fetchCategory failed:", err);
            const detail = err?.response?.data?.detail;
            const msg = typeof detail === "object"
                ? (detail.user_message || detail.code || "Errore")
                : (detail || err.message || "Caricamento fallito");
            setError(msg);
            setData(null);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchCategory(category);
    }, [category, fetchCategory]);

    // Update URL when category changes.
    const handleCategoryChange = (slug) => {
        setCategory(slug);
        setSearchParams((prev) => {
            const next = new URLSearchParams(prev);
            next.set("category", slug);
            return next;
        });
    };

    const entries = data?.entries || [];
    const myEntry = data?.my_entry || null;
    const showMyEntryPin = myEntry && !entries.some((e) => e.is_me);

    const tooFewEntries = !loading && entries.length > 0 && entries.length < 3;

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
                        <span className="tracking-widest">ORBUS // CLASSIFICA</span>
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
                <section className="mb-6">
                    <div className="text-xs text-amber tracking-widest mb-2">
                        :: PUBLIC RANKING
                    </div>
                    <h1
                        data-testid="leaderboard-title"
                        className="text-3xl sm:text-4xl font-semibold tracking-tight mb-2"
                    >
                        {data?.category_label_it || t("leaderboard.title")}
                    </h1>
                    {data?.category_description_it && (
                        <p
                            className="text-sm text-muted-foreground max-w-2xl"
                            data-testid="leaderboard-description"
                        >
                            {data.category_description_it}
                        </p>
                    )}
                </section>

                {/* Category picker — Tabs on desktop, native select on mobile. */}
                <div
                    className="mb-6 border border-border bg-card rounded-sm p-2"
                    data-testid="leaderboard-category-picker"
                >
                    {/* Desktop tabs */}
                    <div className="hidden sm:flex flex-wrap gap-1">
                        {categories.map((c) => (
                            <button
                                key={c.slug}
                                type="button"
                                onClick={() => handleCategoryChange(c.slug)}
                                data-testid={`leaderboard-tab-${c.slug}`}
                                className={`text-[11px] tracking-widest px-3 py-1.5 rounded-sm transition-colors ${
                                    category === c.slug
                                        ? "bg-amber text-background font-bold"
                                        : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                                }`}
                            >
                                {c.label_it}
                            </button>
                        ))}
                    </div>
                    {/* Mobile select */}
                    <select
                        className="sm:hidden w-full bg-background border border-border text-xs px-2 py-2 rounded-sm"
                        value={category}
                        onChange={(e) => handleCategoryChange(e.target.value)}
                        data-testid="leaderboard-category-select-mobile"
                    >
                        {categories.map((c) => (
                            <option key={c.slug} value={c.slug}>
                                {c.label_it}
                            </option>
                        ))}
                    </select>
                </div>

                {error && (
                    <div
                        className="border border-[#ef4444]/55 bg-[#ef4444]/5 text-[#fca5a5] rounded-sm p-3 text-xs mb-6"
                        data-testid="leaderboard-error"
                    >
                        {error}
                    </div>
                )}

                {/* "La tua posizione" card pinned above table if outside top 50. */}
                {showMyEntryPin && (
                    <div
                        data-testid="leaderboard-my-entry-pin"
                        className="mb-4 border border-amber/60 bg-amber/5 rounded-sm p-3 flex items-center justify-between"
                    >
                        <div>
                            <div className="text-[10px] tracking-widest text-amber mb-1">
                                :: LA TUA POSIZIONE
                            </div>
                            <div className="text-sm font-medium">
                                <RankBadge rank={myEntry.rank} />{" "}
                                <span className="ml-2">{myEntry.guild_name}</span>
                            </div>
                        </div>
                        <span className="text-amber font-semibold">
                            {formatScore(category, myEntry.score)}
                        </span>
                    </div>
                )}

                {/* Empty-data states. */}
                {!loading && entries.length === 0 && !error && (
                    <div
                        className="border border-border bg-card rounded-sm p-8 text-center text-xs text-muted-foreground"
                        data-testid="leaderboard-empty"
                    >
                        Non abbastanza dati per questa classifica.
                    </div>
                )}
                {tooFewEntries && (
                    <div
                        className="mb-4 border border-border bg-card rounded-sm p-3 text-xs text-muted-foreground italic"
                        data-testid="leaderboard-few-entries"
                    >
                        Non abbastanza dati per questa classifica.
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
                                <th className="px-3 py-2 text-left">RANK</th>
                                <th className="px-3 py-2 text-left">GILDA</th>
                                <th className="px-3 py-2 text-right">PUNTEGGIO</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading &&
                                [...Array(6)].map((_, i) => <SkeletonRow key={i} i={i} />)}
                            {!loading &&
                                entries.map((e) => (
                                    <tr
                                        key={`${e.guild_public_id}-${e.rank}`}
                                        data-testid={`leaderboard-row-${e.rank}`}
                                        className={`border-t border-border transition-colors ${
                                            e.is_me
                                                ? "bg-amber/10 hover:bg-amber/15"
                                                : "hover:bg-secondary/30"
                                        }`}
                                    >
                                        <td className="px-3 py-3">
                                            <RankBadge rank={e.rank} />
                                        </td>
                                        <td className="px-3 py-3 font-medium">
                                            {e.is_me && (
                                                <span className="mr-2 text-amber" aria-label="me">
                                                    👤
                                                </span>
                                            )}
                                            {e.guild_name}
                                        </td>
                                        <td className="px-3 py-3 text-right font-semibold text-amber">
                                            {formatScore(category, e.score)}
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
                                className="border border-border bg-card rounded-sm p-4 h-16 animate-pulse"
                            />
                        ))}
                    {!loading &&
                        entries.map((e) => (
                            <div
                                key={`${e.guild_public_id}-${e.rank}`}
                                data-testid={`leaderboard-card-${e.rank}`}
                                className={`border rounded-sm p-3 flex items-center justify-between gap-3 ${
                                    e.is_me
                                        ? "border-amber/60 bg-amber/10"
                                        : "border-border bg-card"
                                }`}
                            >
                                <div className="min-w-0">
                                    <div className="text-xs text-muted-foreground">
                                        <RankBadge rank={e.rank} />
                                    </div>
                                    <div className="font-medium truncate">
                                        {e.is_me && "👤 "}{e.guild_name}
                                    </div>
                                </div>
                                <div className="text-amber font-semibold shrink-0">
                                    {formatScore(category, e.score)}
                                </div>
                            </div>
                        ))}
                </div>

                {!loading && data && entries.length > 0 && (
                    <div
                        className="text-[10px] text-muted-foreground mt-4 tracking-widest"
                        data-testid="leaderboard-meta"
                    >
                        mostrate {entries.length} gilde · calcolato il{" "}
                        {data.computed_at ? new Date(data.computed_at).toLocaleString("it-IT") : "—"}
                    </div>
                )}
            </main>

            <footer className="max-w-6xl mx-auto px-4 sm:px-6 py-6 text-xs text-muted-foreground border-t border-border">
                <span className="text-amber">$</span> orbus --leaderboard --public ·
                cambia categoria per stile di gioco diverso.
            </footer>
        </div>
    );
}
