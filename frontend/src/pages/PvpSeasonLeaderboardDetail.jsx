// ROUND 16.3 Phase 7B Iter2 — leaderboard detail per continente.
import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../lib/api";

const CONTINENT_NAMES_IT = {
    ambash: "Ambash", velur: "Velur", soe: "Soe", efreto: "Efreto",
    irthe: "Irthe", nathos: "Nathos", ergolat: "Ergolat", aveol: "Aveol",
};

function rankStyle(rank) {
    if (rank === 1) return { color: "text-yellow-400", icon: "🏆", label: "Campione" };
    if (rank === 2) return { color: "text-slate-300", icon: "🥈", label: "Podio" };
    if (rank === 3) return { color: "text-orange-500", icon: "🥉", label: "Podio" };
    if (rank <= 10) return { color: "text-zinc-400", icon: "", label: "Top 10" };
    return { color: "text-zinc-500", icon: "", label: "" };
}

export default function PvpSeasonLeaderboardDetail() {
    const { continentSlug } = useParams();
    const [data, setData] = useState(null);
    const [myGuildId, setMyGuildId] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        let cancel = false;
        (async () => {
            try {
                const [lb, g] = await Promise.all([
                    api.get(`/pvp-season/leaderboard/${continentSlug}`),
                    api.get("/guilds/me").catch(() => null),
                ]);
                if (cancel) return;
                setData(lb.data);
                const guild = g?.data?.guild || g?.data;
                setMyGuildId(guild?.id || null);
            } catch (e) {
                if (!cancel) {
                    setError(e?.response?.data?.detail?.user_message
                          || "Continente non trovato.");
                }
            } finally {
                if (!cancel) setLoading(false);
            }
        })();
        return () => { cancel = true; };
    }, [continentSlug]);

    if (loading) {
        return (
            <div className="min-h-screen bg-zinc-950 text-zinc-500 p-4 pb-32 md:pb-8 text-sm">
                Caricamento classifica…
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-zinc-950 text-zinc-100 p-4 pb-32 md:pb-8 max-w-3xl mx-auto"
                 data-testid="pvp-season-detail-error">
                <div className="border border-red-900/40 rounded p-6 bg-red-950/10">
                    <div className="text-sm text-red-300">{error}</div>
                    <Link to="/pvp-season"
                          className="inline-block mt-3 text-amber-400 hover:text-amber-300 underline text-sm">
                        ← Torna a Stagione PvP
                    </Link>
                </div>
            </div>
        );
    }

    const name = CONTINENT_NAMES_IT[continentSlug] || continentSlug;
    const entries = data?.entries || [];

    return (
        <div className="min-h-screen bg-zinc-950 text-zinc-100 p-4 pb-32 md:pb-8 max-w-4xl mx-auto"
             data-testid="pvp-season-leaderboard-detail">
            {/* Header */}
            <div className="mb-6">
                <Link to="/pvp-season"
                      className="text-xs text-zinc-500 hover:text-amber-400 uppercase tracking-wide inline-block mb-2"
                      data-testid="pvp-back-to-overview">
                    ← Torna a Stagione PvP
                </Link>
                <h1 className="text-3xl md:text-4xl font-bold text-zinc-100">
                    Classifica <span className="text-amber-400">{name}</span>
                </h1>
                <div className="text-xs text-zinc-500 mt-1">
                    Stagione N° <span className="font-mono text-zinc-300">{data?.season_number}</span>
                    {data?.finalized ? (
                        <span className="ml-2 text-amber-400/80">· Finalizzata (snapshot)</span>
                    ) : (
                        <span className="ml-2 text-emerald-400/80">· In corso (live)</span>
                    )}
                </div>
            </div>

            {/* Leaderboard table */}
            {entries.length === 0 ? (
                <div className="border border-zinc-800 rounded p-6 bg-zinc-900/40 text-center text-zinc-500 text-sm"
                     data-testid="pvp-leaderboard-empty">
                    Nessuna gilda qualificata in questo continente per la stagione attuale.
                    <div className="mt-2 text-xs">
                        Le gilde devono avere presenza continentale attiva e livello ≥ 8.
                    </div>
                </div>
            ) : (
                <div className="border border-zinc-800 rounded-lg overflow-hidden bg-zinc-900/40">
                    <div className="grid grid-cols-12 gap-2 px-4 py-2 text-[10px] uppercase tracking-wider text-zinc-500 border-b border-zinc-800 bg-zinc-950/50">
                        <div className="col-span-2 md:col-span-1">Rank</div>
                        <div className="col-span-5 md:col-span-5">Gilda</div>
                        <div className="col-span-2 md:col-span-2 text-right">Elo</div>
                        <div className="col-span-3 md:col-span-2 text-right">V/S/P</div>
                        <div className="hidden md:block col-span-2 text-right">Ricompensa</div>
                    </div>
                    {entries.map((e) => {
                        const rs = rankStyle(e.rank);
                        const mine = myGuildId && e.guild_id === myGuildId;
                        return (
                            <div key={e.guild_id}
                                 data-testid={`pvp-lb-row-${e.rank}`}
                                 className={`grid grid-cols-12 gap-2 px-4 py-3 text-sm border-b border-zinc-800/50 last:border-b-0 ${
                                     mine ? "bg-amber-950/20 border-l-2 border-l-amber-500" : ""
                                 }`}>
                                <div className={`col-span-2 md:col-span-1 font-mono font-bold ${rs.color}`}>
                                    {rs.icon} #{e.rank}
                                </div>
                                <div className="col-span-5 md:col-span-5 text-zinc-200 truncate">
                                    {e.guild_name || e.guild_id.slice(0, 12)}
                                    {mine && (
                                        <span className="ml-2 text-[9px] px-1 py-0.5 rounded uppercase bg-amber-500/20 text-amber-300 border border-amber-500/40 font-mono">
                                            Tu
                                        </span>
                                    )}
                                </div>
                                <div className="col-span-2 md:col-span-2 text-right font-mono text-zinc-300">
                                    {e.elo}
                                </div>
                                <div className="col-span-3 md:col-span-2 text-right font-mono text-xs text-zinc-500">
                                    {e.wins}/{e.losses}/{e.draws}
                                </div>
                                <div className="hidden md:block col-span-2 text-right text-[10px] text-zinc-500">
                                    {rs.label}
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Anti-P2W footer */}
            <div className="mt-6 text-[11px] text-zinc-500 italic text-center">
                Le ricompense sono <strong className="text-emerald-400/80">puramente decorative</strong> (titoli, distintivi, cornici). Zero impatto su gameplay.
            </div>
        </div>
    );
}
