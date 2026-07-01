// ROUND 16.3 Phase 7B Iter2 — cosmetici sbloccati + catalog.
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";

const CONTINENT_NAMES_IT = {
    ambash: "Ambash", velur: "Velur", soe: "Soe", efreto: "Efreto",
    irthe: "Irthe", nathos: "Nathos", ergolat: "Ergolat", aveol: "Aveol",
};

const TYPE_LABEL_IT = {
    title: "Titolo",
    badge: "Distintivo",
    frame: "Cornice",
};

const TYPE_ICON = {
    title: "👑",
    badge: "🎖",
    frame: "🖼",
};

export default function PvpSeasonCosmetics() {
    const [tab, setTab] = useState("mine");
    const [mine, setMine] = useState({ items: [], by_type: {}, total: 0 });
    const [catalog, setCatalog] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let cancel = false;
        (async () => {
            try {
                const [m, c] = await Promise.all([
                    api.get("/pvp-season/cosmetics/mine"),
                    api.get("/pvp-season/cosmetics/catalog"),
                ]);
                if (cancel) return;
                setMine(m.data);
                setCatalog(c.data.entries || []);
            } finally {
                if (!cancel) setLoading(false);
            }
        })();
        return () => { cancel = true; };
    }, []);

    const unlockedSlugs = useMemo(
        () => new Set((mine.items || []).map(i => i.cosmetic_slug)),
        [mine.items],
    );

    const catalogByContinent = useMemo(() => {
        const grouped = {};
        for (const entry of catalog) {
            const slug = entry.continent_slug;
            if (!grouped[slug]) grouped[slug] = [];
            grouped[slug].push(entry);
        }
        return grouped;
    }, [catalog]);

    if (loading) {
        return (
            <div className="min-h-screen bg-zinc-950 text-zinc-500 p-4 pb-32 md:pb-8 text-sm">
                Caricamento cosmetici…
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-zinc-950 text-zinc-100 p-4 pb-32 md:pb-8 max-w-5xl mx-auto"
             data-testid="pvp-season-cosmetics-page">
            <div className="mb-4">
                <Link to="/pvp-season"
                      className="text-xs text-zinc-500 hover:text-amber-400 uppercase tracking-wide">
                    ← Torna a Stagione PvP
                </Link>
                <h1 className="text-3xl md:text-4xl font-bold text-zinc-100 mt-2">
                    Cosmetici <span className="text-amber-400">PvP</span>
                </h1>
                <div className="text-xs text-zinc-500 mt-1">
                    Titoli, distintivi e cornici sbloccati partecipando alle stagioni PvP.
                </div>
            </div>

            {/* Anti-P2W notice */}
            <div className="mb-4 px-3 py-2 border border-emerald-900/40 bg-emerald-950/10 rounded text-[11px] text-emerald-300/80"
                 data-testid="pvp-cosmetics-antip2w-notice">
                <strong className="font-mono uppercase">Anti-Pay-to-Win:</strong>{" "}
                cosmetici puramente decorativi. Zero impatto su statistiche, oro, XP o gameplay.
            </div>

            {/* Tabs */}
            <div className="flex gap-2 mb-4 border-b border-zinc-800">
                <button
                    onClick={() => setTab("mine")}
                    data-testid="pvp-cosmetics-tab-mine"
                    className={`px-4 py-2 text-sm min-h-[44px] transition ${
                        tab === "mine"
                            ? "border-b-2 border-amber-500 text-amber-300"
                            : "text-zinc-500 hover:text-zinc-300"
                    }`}>
                    I Miei Cosmetici
                    <span className="ml-2 text-[10px] font-mono text-zinc-500">
                        ({mine.total || 0})
                    </span>
                </button>
                <button
                    onClick={() => setTab("catalog")}
                    data-testid="pvp-cosmetics-tab-catalog"
                    className={`px-4 py-2 text-sm min-h-[44px] transition ${
                        tab === "catalog"
                            ? "border-b-2 border-amber-500 text-amber-300"
                            : "text-zinc-500 hover:text-zinc-300"
                    }`}>
                    Catalogo Completo
                    <span className="ml-2 text-[10px] font-mono text-zinc-500">
                        ({catalog.length})
                    </span>
                </button>
            </div>

            {/* Tab: mine */}
            {tab === "mine" && (
                <div data-testid="pvp-cosmetics-mine-panel">
                    {mine.items.length === 0 ? (
                        <div className="border border-zinc-800 rounded p-8 bg-zinc-900/40 text-center"
                             data-testid="pvp-cosmetics-mine-empty">
                            <div className="text-4xl mb-2 opacity-40">🏆</div>
                            <div className="text-sm text-zinc-400">
                                Non hai ancora sbloccato cosmetici.
                            </div>
                            <div className="text-xs text-zinc-500 mt-2">
                                Partecipa alle stagioni PvP e piazzati nella top 10 per ottenere titoli, distintivi e cornici.
                            </div>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                            {mine.items.map((it) => (
                                <div key={it.id}
                                     data-testid={`pvp-cosmetic-mine-${it.cosmetic_slug}`}
                                     className="border border-amber-800/50 rounded-lg p-4 bg-amber-950/10">
                                    <div className="flex items-center gap-2 mb-2">
                                        <span className="text-2xl">{TYPE_ICON[it.type] || "✨"}</span>
                                        <div className="flex-1 min-w-0">
                                            <div className="text-sm font-semibold text-zinc-100 truncate">
                                                {it.name_it}
                                            </div>
                                            <div className="text-[10px] uppercase tracking-wider text-amber-400/70 font-mono">
                                                {TYPE_LABEL_IT[it.type] || it.type}
                                                {" · "}
                                                {CONTINENT_NAMES_IT[it.continent_slug] || it.continent_slug}
                                            </div>
                                        </div>
                                    </div>
                                    <div className="text-[10px] text-zinc-500 font-mono">
                                        Stagione N°{it.season_number} · Rank #{it.rank_awarded}
                                    </div>
                                    <div className="text-[10px] text-zinc-600 mt-1">
                                        Sbloccato: {new Date(it.unlocked_at).toLocaleDateString("it-IT")}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* Tab: catalog */}
            {tab === "catalog" && (
                <div data-testid="pvp-cosmetics-catalog-panel">
                    {Object.entries(CONTINENT_NAMES_IT).map(([slug, name]) => {
                        const entries = catalogByContinent[slug] || [];
                        if (entries.length === 0) return null;
                        return (
                            <div key={slug} className="mb-6">
                                <h3 className="text-sm font-semibold text-zinc-300 mb-2 uppercase tracking-wider">
                                    {name}
                                </h3>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                    {entries.map((e) => {
                                        const unlocked = unlockedSlugs.has(e.cosmetic_slug);
                                        return (
                                            <div key={e.cosmetic_slug}
                                                 data-testid={`pvp-catalog-${e.cosmetic_slug}`}
                                                 className={`border rounded-lg p-3 transition ${
                                                     unlocked
                                                         ? "border-amber-700/60 bg-amber-950/10"
                                                         : "border-zinc-800 bg-zinc-900/30 opacity-60"
                                                 }`}>
                                                <div className="flex items-start gap-2 mb-2">
                                                    <span className="text-xl">{TYPE_ICON[e.type] || "✨"}</span>
                                                    <div className="flex-1 min-w-0">
                                                        <div className="text-xs font-semibold text-zinc-200 truncate">
                                                            {e.name_it}
                                                        </div>
                                                        <div className="text-[9px] uppercase tracking-wider text-zinc-500 font-mono">
                                                            {TYPE_LABEL_IT[e.type]} · Rank ≤{e.rank_required}
                                                        </div>
                                                    </div>
                                                    {unlocked && (
                                                        <span className="text-emerald-400 text-sm" title="Sbloccato">✓</span>
                                                    )}
                                                </div>
                                                <div className="text-[10px] text-zinc-500 leading-snug">
                                                    {e.description_it}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
