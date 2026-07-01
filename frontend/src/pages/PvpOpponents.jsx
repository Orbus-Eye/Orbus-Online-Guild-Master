// ROUND 16.3 Phase 7A Iter2 — PvP Continentale hub / opponents list.
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { api } from "../lib/api";
import AppHeader from "../components/AppHeader";
import PvpGuildLevelGate from "../components/PvpGuildLevelGate";

export default function PvpOpponents() {
    const [loading, setLoading] = useState(true);
    const [guild, setGuild] = useState(null);
    const [stats, setStats] = useState(null);
    const [opponents, setOpponents] = useState([]);
    const [locked, setLocked] = useState(null);
    const [sortDesc, setSortDesc] = useState(false);

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const g = await api.get("/guilds/me");
            const guildDoc = g.data?.guild || g.data;
            setGuild(guildDoc);
            if ((guildDoc?.level || 0) < 8) {
                setLocked({ current_level: guildDoc?.level || 0 });
                setLoading(false);
                return;
            }
            const [oppRes, adminRes] = await Promise.all([
                api.get("/pvp/opponents").catch((e) => {
                    if (e?.response?.status === 403) {
                        setLocked({ current_level: guildDoc?.level || 0 });
                        return { data: { opponents: [] } };
                    }
                    throw e;
                }),
                api.get("/admin/pvp/stats").catch(() => ({ data: null })),
            ]);
            setOpponents(oppRes.data?.opponents || []);
            // Fallback: my stats from opponents endpoint would need enrichment.
            // We rely on admin/pvp/stats top10 or /pvp/battles/mine to infer own Elo.
            const battlesRes = await api.get("/pvp/battles/mine")
                .catch(() => ({ data: { active: [], history: [] } }));
            const myBattles = [
                ...(battlesRes.data.active || []),
                ...(battlesRes.data.history || []),
            ];
            const wins = myBattles.filter((b) =>
                (b.outcome === "challenger_win" && b.challenger_guild_id === guildDoc.id) ||
                (b.outcome === "defender_win" && b.defender_guild_id === guildDoc.id) ||
                (b.outcome === "defender_forfeit" && b.challenger_guild_id === guildDoc.id)
            ).length;
            const losses = myBattles.filter((b) =>
                (b.outcome === "defender_win" && b.challenger_guild_id === guildDoc.id) ||
                (b.outcome === "challenger_win" && b.defender_guild_id === guildDoc.id) ||
                (b.outcome === "defender_forfeit" && b.defender_guild_id === guildDoc.id)
            ).length;
            const draws = myBattles.filter((b) => b.outcome === "draw").length;
            const activeCount = (battlesRes.data.active || []).filter(
                (b) => b.challenger_guild_id === guildDoc.id
            ).length;
            setStats({ elo: 1200, wins, losses, draws, active: activeCount });
        } catch (e) {
            toast.error(e?.response?.data?.detail?.user_message || "Caricamento fallito");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { load(); }, [load]);

    if (loading) return (
        <div className="min-h-screen bg-zinc-950 text-zinc-100 pb-32 md:pb-8">
            <AppHeader />
            <div className="max-w-6xl mx-auto px-4 py-6 text-sm text-zinc-500">
                Caricamento PvP…
            </div>
        </div>
    );

    if (locked) return (
        <div className="min-h-screen bg-zinc-950 text-zinc-100 pb-32 md:pb-8">
            <AppHeader />
            <PvpGuildLevelGate currentLevel={locked.current_level} />
        </div>
    );

    const sorted = [...opponents].sort((a, b) =>
        sortDesc ? b.elo - a.elo : a.elo - b.elo
    );

    return (
        <div className="min-h-screen bg-zinc-950 text-zinc-100 pb-32 md:pb-8">
            <AppHeader />
            <div className="max-w-6xl mx-auto px-4 py-6 space-y-6" data-testid="pvp-opponents-page">
                <header className="flex flex-col md:flex-row md:items-end md:justify-between gap-3">
                    <div>
                        <h1 className="text-2xl md:text-3xl font-semibold tracking-tight">
                            PvP Continentale
                        </h1>
                        <p className="text-sm text-zinc-400 mt-1">
                            Sfida asincrona 1v1 tra gilde dello stesso continente. Ricompense puramente cosmetiche.
                        </p>
                    </div>
                    <Link to="/pvp/battles"
                          className="inline-flex items-center justify-center px-4 py-2 rounded-md bg-red-900/40 hover:bg-red-900/60 border border-red-800/60 text-sm w-full md:w-auto min-h-[44px]"
                          data-testid="pvp-battles-link">
                        Le mie battaglie →
                    </Link>
                </header>

                {stats && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3" data-testid="pvp-my-stats">
                        <StatCell label="Elo" value={stats.elo} big />
                        <StatCell label="Vittorie" value={stats.wins} accent="text-emerald-400" />
                        <StatCell label="Sconfitte" value={stats.losses} accent="text-rose-400" />
                        <StatCell label={`Sfide attive`} value={`${stats.active}/3`} />
                    </div>
                )}

                <section>
                    <div className="flex items-center justify-between mb-3">
                        <h2 className="text-lg font-semibold">Avversari nel tuo continente</h2>
                        <button
                            onClick={() => setSortDesc((s) => !s)}
                            className="text-xs text-zinc-400 hover:text-zinc-200 px-2 py-1 rounded border border-zinc-800"
                            data-testid="pvp-sort-toggle">
                            Elo {sortDesc ? "↓" : "↑"}
                        </button>
                    </div>
                    {sorted.length === 0 ? (
                        <div className="rounded-md border border-zinc-800 bg-zinc-900/40 p-6 text-center text-sm text-zinc-500"
                             data-testid="pvp-opponents-empty">
                            Nessun avversario disponibile nel tuo continente entro il bracket
                            (±200 Elo o ±3 livelli).
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3" data-testid="pvp-opponents-grid">
                            {sorted.map((o) => (
                                <OpponentCard key={o.guild_id} opponent={o} />
                            ))}
                        </div>
                    )}
                </section>

                <p className="text-xs text-zinc-500 border-t border-zinc-800/60 pt-3">
                    Le battaglie PvP non generano oro, XP o loot — solo Elo e prestigio.
                </p>
            </div>
        </div>
    );
}

function StatCell({ label, value, accent, big }) {
    return (
        <div className="rounded-md border border-zinc-800 bg-zinc-900/40 p-3">
            <div className="text-[11px] uppercase tracking-wide text-zinc-500">{label}</div>
            <div className={`${big ? "text-2xl md:text-3xl" : "text-xl"} font-mono ${accent || "text-zinc-100"}`}>
                {value}
            </div>
        </div>
    );
}

function OpponentCard({ opponent }) {
    return (
        <div className="rounded-md border border-zinc-800 bg-zinc-900/40 p-4 flex flex-col md:flex-row md:items-center gap-3"
             data-testid={`pvp-opponent-${opponent.guild_id}`}>
            <div className="flex-1 min-w-0">
                <div className="font-medium truncate">{opponent.guild_name}</div>
                <div className="text-xs text-zinc-500 mt-0.5">
                    Livello {opponent.guild_level} · <span className="font-mono">Elo {opponent.elo}</span>
                </div>
                <div className="text-[11px] text-zinc-600 mt-1">
                    V {opponent.wins} · S {opponent.losses} · P {opponent.draws}
                </div>
            </div>
            <Link
                to={`/pvp/challenge/${opponent.guild_id}`}
                className="inline-flex items-center justify-center px-4 py-2 rounded-md bg-red-900/50 hover:bg-red-900/70 border border-red-800/60 text-sm w-full md:w-auto min-h-[44px]"
                data-testid={`pvp-challenge-btn-${opponent.guild_id}`}>
                Sfida
            </Link>
        </div>
    );
}
