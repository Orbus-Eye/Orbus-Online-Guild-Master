// ROUND 16.3 Phase 7A Iter2 — PvP dashboard mini card.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";

export default function PvpMiniCard() {
    const [state, setState] = useState({
        loading: true, access: false, guildLevel: null,
        elo: 1200, wins: 0, losses: 0, draws: 0, active: 0, last: null,
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
                const b = await api.get("/pvp/battles/mine").catch(
                    () => ({ data: { active: [], history: [] } })
                );
                if (cancel) return;
                const active = b.data.active || [];
                const history = b.data.history || [];
                const wins = history.filter((x) =>
                    (x.outcome === "challenger_win" && x.challenger_guild_id === guild.id) ||
                    (x.outcome === "defender_win" && x.defender_guild_id === guild.id) ||
                    (x.outcome === "defender_forfeit" && x.challenger_guild_id === guild.id)
                ).length;
                const losses = history.filter((x) =>
                    (x.outcome === "defender_win" && x.challenger_guild_id === guild.id) ||
                    (x.outcome === "challenger_win" && x.defender_guild_id === guild.id) ||
                    (x.outcome === "defender_forfeit" && x.defender_guild_id === guild.id)
                ).length;
                const draws = history.filter((x) => x.outcome === "draw").length;
                const last = history[0] || null;
                setState({
                    loading: false, access: true, guildLevel: lvl,
                    elo: 1200, wins, losses, draws, active: active.length, last,
                });
            } catch {
                if (!cancel) setState((s) => ({ ...s, loading: false }));
            }
        })();
        return () => { cancel = true; };
    }, []);

    if (state.loading) return null;

    if (!state.access) {
        return (
            <div className="border border-zinc-800 rounded p-4 bg-zinc-900/40"
                 data-testid="pvp-mini-card-locked">
                <div className="text-sm font-semibold text-zinc-300 mb-1">
                    PvP Continentale
                </div>
                <div className="text-xs text-zinc-500">
                    🔒 Sblocca al Livello Gilda 8
                    {state.guildLevel != null && ` (attualmente lv ${state.guildLevel})`}
                </div>
            </div>
        );
    }

    return (
        <Link to="/pvp"
              className="block border border-red-900/40 rounded p-4 bg-red-950/10 hover:bg-red-950/20 transition"
              data-testid="pvp-mini-card">
            <div className="flex items-center justify-between mb-2">
                <div className="text-sm font-semibold text-zinc-100">PvP Continentale</div>
                <div className="text-[10px] uppercase tracking-wide text-red-400/70">Vai →</div>
            </div>
            <div className="flex items-baseline gap-3">
                <div className="font-mono text-2xl text-zinc-100">{state.elo}</div>
                <div className="text-[11px] text-zinc-500">Elo</div>
            </div>
            <div className="text-[11px] text-zinc-500 mt-1">
                V {state.wins} · S {state.losses} · P {state.draws}
                {state.active > 0 && (
                    <span className="ml-2 text-amber-400">· {state.active} attive</span>
                )}
            </div>
        </Link>
    );
}
