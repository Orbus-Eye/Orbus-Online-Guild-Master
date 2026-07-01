// ROUND 16.3 Phase 7B Iter2 — PvP Season overview (8 continent leaderboards).
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";

const CONTINENT_NAMES_IT = {
    ambash: "Ambash", velur: "Velur", soe: "Soe", efreto: "Efreto",
    irthe: "Irthe", nathos: "Nathos", ergolat: "Ergolat", aveol: "Aveol",
};

function formatCountdown(seconds) {
    if (!seconds || seconds <= 0) return "Terminata";
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return `${d}g ${h}h ${m}m`;
}

function rankColor(rank) {
    if (rank === 1) return "text-yellow-400";
    if (rank === 2) return "text-slate-300";
    if (rank === 3) return "text-orange-500";
    return "text-zinc-400";
}

function rankIcon(rank) {
    if (rank === 1) return "🏆";
    if (rank === 2) return "🥈";
    if (rank === 3) return "🥉";
    return "";
}

export default function PvpSeasonOverview() {
    const [season, setSeason] = useState(null);
    const [byContinent, setByContinent] = useState({});
    const [myGuildId, setMyGuildId] = useState(null);
    const [loading, setLoading] = useState(true);
    const [countdown, setCountdown] = useState(0);

    useEffect(() => {
        let cancel = false;
        (async () => {
            try {
                const [s, lb, g] = await Promise.all([
                    api.get("/pvp-season/current"),
                    api.get("/pvp-season/leaderboard/all-continents"),
                    api.get("/guilds/me").catch(() => null),
                ]);
                if (cancel) return;
                setSeason(s.data);
                setByContinent(lb.data.by_continent || {});
                setCountdown(s.data.time_remaining_seconds || 0);
                const guild = g?.data?.guild || g?.data;
                setMyGuildId(guild?.id || null);
            } finally {
                if (!cancel) setLoading(false);
            }
        })();
        return () => { cancel = true; };
    }, []);

    useEffect(() => {
        if (countdown <= 0) return undefined;
        const t = setInterval(() => setCountdown((c) => Math.max(0, c - 1)), 1000);
        return () => clearInterval(t);
    }, [countdown]);

    if (loading) {
        return (
            <div className="min-h-screen bg-zinc-950 text-zinc-100 p-4 pb-32 md:pb-8"
                 data-testid="pvp-season-overview-loading">
                <div className="text-zinc-500 text-sm">Caricamento stagione…</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-zinc-950 text-zinc-100 p-4 pb-32 md:pb-8 max-w-6xl mx-auto"
             data-testid="pvp-season-overview">
            {/* Header stagione */}
            <div className="border border-amber-900/40 rounded-lg p-6 mb-6 bg-gradient-to-br from-amber-950/20 to-zinc-950">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                    <div>
                        <div className="text-xs uppercase tracking-wider text-amber-400/80 mb-1">
                            Stagione PvP Continentale
                        </div>
                        <h1 className="text-3xl md:text-4xl font-bold text-zinc-100">
                            Stagione N° <span className="font-mono text-amber-400">{season?.season_number}</span>
                        </h1>
                    </div>
                    <div className="text-right">
                        <div className="text-xs text-zinc-500 uppercase tracking-wide mb-1">Termina tra</div>
                        <div className="font-mono text-2xl text-amber-300"
                             data-testid="pvp-season-countdown">
                            {formatCountdown(countdown)}
                        </div>
                    </div>
                </div>
                <div className="mt-3 flex flex-col md:flex-row gap-2 md:gap-4 text-xs text-zinc-500">
                    <div>Iniziata: {new Date(season?.started_at).toLocaleDateString("it-IT")}</div>
                    <div>Termina: {new Date(season?.ends_at).toLocaleDateString("it-IT")}</div>
                    <Link to="/pvp-season/cosmetics"
                          className="md:ml-auto text-amber-400 hover:text-amber-300 underline"
                          data-testid="pvp-season-cosmetics-link">
                        → I miei cosmetici
                    </Link>
                </div>
            </div>

            {/* Grid 8 continenti */}
            <h2 className="text-lg md:text-xl font-semibold mb-4 text-zinc-200">
                Classifiche continentali
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(CONTINENT_NAMES_IT).map(([slug, name]) => {
                    const rows = (byContinent[slug] || []).slice(0, 3);
                    const mine = (byContinent[slug] || []).find(r => r.guild_id === myGuildId);
                    const iAmInTop10 = !!mine;
                    return (
                        <Link key={slug}
                              to={`/pvp-season/leaderboard/${slug}`}
                              data-testid={`pvp-continent-card-${slug}`}
                              className={`block border rounded-lg p-4 transition ${
                                  iAmInTop10
                                      ? "border-amber-600/60 bg-amber-950/10 hover:bg-amber-950/20"
                                      : "border-zinc-800 bg-zinc-900/40 hover:bg-zinc-900/70"
                              }`}>
                            <div className="flex items-center justify-between mb-3">
                                <div className="text-sm font-semibold text-zinc-100">{name}</div>
                                {iAmInTop10 && (
                                    <span className="text-[9px] px-1.5 py-0.5 rounded uppercase tracking-wider bg-amber-500/20 text-amber-300 border border-amber-500/40 font-mono">
                                        Rank {mine.rank}
                                    </span>
                                )}
                            </div>
                            {rows.length === 0 ? (
                                <div className="text-xs text-zinc-500 italic">
                                    Nessuna gilda qualificata
                                </div>
                            ) : (
                                <div className="space-y-1.5">
                                    {rows.map((r) => (
                                        <div key={r.guild_id}
                                             className="flex items-center justify-between text-xs"
                                             data-testid={`pvp-top-${slug}-${r.rank}`}>
                                            <div className="flex items-center gap-2 min-w-0">
                                                <span className={`font-mono ${rankColor(r.rank)}`}>
                                                    {rankIcon(r.rank)} #{r.rank}
                                                </span>
                                                <span className="text-zinc-300 truncate">
                                                    {r.guild_name || r.guild_id.slice(0, 8)}
                                                </span>
                                            </div>
                                            <span className="font-mono text-zinc-400 shrink-0">
                                                {r.elo}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            )}
                            <div className="mt-3 text-[10px] text-amber-400/70 uppercase tracking-wide">
                                Vedi classifica completa →
                            </div>
                        </Link>
                    );
                })}
            </div>

            {/* Anti-P2W disclaimer */}
            <div className="mt-8 p-4 bg-zinc-900/50 border border-zinc-800 rounded"
                 data-testid="pvp-season-antip2w-disclaimer">
                <p className="font-mono uppercase text-emerald-400 text-xs mb-2">
                    Trasparenza Anti-Pay-to-Win
                </p>
                <p className="text-xs text-zinc-500 leading-relaxed">
                    Le classifiche stagionali PvP premiano con <strong className="text-zinc-300">cosmetici puramente decorativi</strong> (titoli, distintivi, cornici). Nessun cosmetico modifica oro, XP, statistiche avventurieri, potenza di combattimento, drop rate, o qualsiasi altro parametro di gameplay. Nessun cosmetico è acquistabile con denaro reale né influenza il matchmaking o le probabilità di successo.
                </p>
            </div>
        </div>
    );
}
