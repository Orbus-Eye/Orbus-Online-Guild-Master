// ROUND 16.3 Phase 7B Iter2 — dashboard mini-card for PvP Season.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";

function formatCountdown(seconds) {
    if (!seconds || seconds <= 0) return "—";
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    if (d > 0) return `${d}g ${h}h`;
    if (h > 0) return `${h}h ${m}m`;
    return `${m}m`;
}

export default function PvpSeasonMiniCard() {
    const [state, setState] = useState({
        loading: true, access: false, guildLevel: null,
        seasonNumber: null, timeRemaining: 0,
        bestRank: null, bestContinent: null,
        cosmeticsCount: 0,
    });

    useEffect(() => {
        let cancel = false;
        (async () => {
            try {
                const g = await api.get("/guilds/me");
                const guild = g.data?.guild || g.data;
                const lvl = guild?.level || 0;
                if (lvl < 8) {
                    if (!cancel) setState((s) => ({
                        ...s, loading: false, access: false, guildLevel: lvl,
                    }));
                    return;
                }
                const [s, lb, cos] = await Promise.all([
                    api.get("/pvp-season/current").catch(() => null),
                    api.get("/pvp-season/leaderboard/all-continents").catch(() => null),
                    api.get("/pvp-season/cosmetics/mine").catch(() => null),
                ]);
                if (cancel) return;
                let bestRank = null;
                let bestContinent = null;
                const byC = lb?.data?.by_continent || {};
                for (const [slug, rows] of Object.entries(byC)) {
                    const mine = (rows || []).find(r => r.guild_id === guild.id);
                    if (mine && (bestRank === null || mine.rank < bestRank)) {
                        bestRank = mine.rank;
                        bestContinent = slug;
                    }
                }
                setState({
                    loading: false, access: true, guildLevel: lvl,
                    seasonNumber: s?.data?.season_number || null,
                    timeRemaining: s?.data?.time_remaining_seconds || 0,
                    bestRank, bestContinent,
                    cosmeticsCount: cos?.data?.total || 0,
                });
            } catch {
                if (!cancel) setState((st) => ({ ...st, loading: false }));
            }
        })();
        return () => { cancel = true; };
    }, []);

    if (state.loading) return null;

    if (!state.access) {
        return (
            <div className="border border-zinc-800 rounded p-4 bg-zinc-900/40"
                 data-testid="pvp-season-mini-card-locked">
                <div className="text-sm font-semibold text-zinc-300 mb-1">
                    Stagione PvP
                    <span className="ml-2 text-[9px] px-1.5 py-0.5 rounded uppercase tracking-wider bg-emerald-500/15 text-emerald-400 border border-emerald-500/40 font-mono">
                        NEW
                    </span>
                </div>
                <div className="text-xs text-zinc-500">
                    🔒 Sblocca al Livello Gilda 8
                    {state.guildLevel != null && ` (attualmente lv ${state.guildLevel})`}
                </div>
            </div>
        );
    }

    return (
        <Link to="/pvp-season"
              className="block border border-amber-900/40 rounded p-4 bg-amber-950/10 hover:bg-amber-950/20 transition"
              data-testid="pvp-season-mini-card">
            <div className="flex items-center justify-between mb-2">
                <div className="text-sm font-semibold text-zinc-100">
                    Stagione PvP
                    <span className="ml-2 text-[9px] px-1.5 py-0.5 rounded uppercase tracking-wider bg-emerald-500/15 text-emerald-400 border border-emerald-500/40 font-mono">
                        NEW
                    </span>
                </div>
                <div className="text-[10px] uppercase tracking-wide text-amber-400/70">Vai →</div>
            </div>
            <div className="flex items-baseline gap-3 mb-1">
                <div className="font-mono text-xl text-amber-300">
                    N°{state.seasonNumber ?? "?"}
                </div>
                <div className="text-[11px] text-zinc-500">
                    · Termina in <span className="font-mono text-zinc-300">{formatCountdown(state.timeRemaining)}</span>
                </div>
            </div>
            <div className="text-[11px] text-zinc-500 mt-1">
                {state.bestRank !== null ? (
                    <span>
                        Rank <span className="font-mono text-amber-300">#{state.bestRank}</span>
                        {" in "}
                        <span className="text-zinc-300 capitalize">{state.bestContinent}</span>
                    </span>
                ) : (
                    <span>Nessuna posizione in top 10</span>
                )}
                {state.cosmeticsCount > 0 && (
                    <span className="ml-2">
                        · <span className="font-mono text-zinc-300">{state.cosmeticsCount}</span> cosmetici
                    </span>
                )}
            </div>
        </Link>
    );
}
