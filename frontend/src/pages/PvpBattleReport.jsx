// ROUND 16.3 Phase 7A Iter2 — Battle detail + narrative log.
import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { toast } from "sonner";
import { api } from "../lib/api";
import AppHeader from "../components/AppHeader";

export default function PvpBattleReport() {
    const { battleId } = useParams();
    const [loading, setLoading] = useState(true);
    const [battle, setBattle] = useState(null);

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const r = await api.get(`/pvp/battles/${battleId}`);
            setBattle(r.data?.battle || r.data);
        } catch (e) {
            toast.error(e?.response?.data?.detail?.user_message || "Battaglia non trovata");
        } finally {
            setLoading(false);
        }
    }, [battleId]);

    useEffect(() => { load(); }, [load]);

    if (loading) return (
        <div className="min-h-screen bg-zinc-950 text-zinc-100 pb-32 md:pb-8">
            <AppHeader />
            <div className="max-w-4xl mx-auto px-4 py-6 text-sm text-zinc-500">Caricamento…</div>
        </div>
    );

    if (!battle) return (
        <div className="min-h-screen bg-zinc-950 text-zinc-100 pb-32 md:pb-8">
            <AppHeader />
            <div className="max-w-4xl mx-auto px-4 py-6 text-sm text-zinc-500">
                Battaglia non disponibile.
            </div>
        </div>
    );

    const mvpAdv = [
        ...(battle.challenger_team || []),
        ...(battle.defender_team || []),
    ].find((a) => a.id === battle.mvp_adventurer_id);

    const battleLog = Array.isArray(battle.battle_log) ? battle.battle_log : [];

    const chDelta = battle.challenger_elo_after != null
        ? battle.challenger_elo_after - battle.challenger_elo_snapshot
        : null;
    const dfDelta = battle.defender_elo_after != null
        ? battle.defender_elo_after - battle.defender_elo_snapshot
        : null;

    return (
        <div className="min-h-screen bg-zinc-950 text-zinc-100 pb-32 md:pb-8">
            <AppHeader />
            <div className="max-w-4xl mx-auto px-4 py-6 space-y-5" data-testid="pvp-battle-report-page">
                <Link to="/pvp/battles" className="text-xs text-zinc-500 hover:text-zinc-300">
                    ← Battaglie
                </Link>

                <header className="border border-red-800/40 bg-red-950/10 rounded-md p-4 space-y-2">
                    <div className="text-xs uppercase tracking-wide text-red-300/70">
                        Report battaglia · {battle.continent_slug}
                    </div>
                    <div className="flex items-center justify-between gap-3">
                        <div className="flex-1 min-w-0">
                            <div className="text-xs text-zinc-500">Attaccante</div>
                            <div className="text-sm md:text-base font-medium truncate">
                                {battle.challenger_guild_id}
                            </div>
                            <EloRow before={battle.challenger_elo_snapshot} after={battle.challenger_elo_after} delta={chDelta} />
                        </div>
                        <div className="text-2xl font-mono text-zinc-500">vs</div>
                        <div className="flex-1 min-w-0 text-right">
                            <div className="text-xs text-zinc-500">Difensore</div>
                            <div className="text-sm md:text-base font-medium truncate">
                                {battle.defender_guild_id}
                            </div>
                            <EloRow before={battle.defender_elo_snapshot} after={battle.defender_elo_after} delta={dfDelta} right />
                        </div>
                    </div>
                    <div className="pt-2 border-t border-red-900/30 text-sm">
                        Esito: <span className="font-semibold">{outcomeLabel(battle.outcome)}</span>
                        {mvpAdv && (
                            <span className="ml-3 inline-flex items-center gap-1 px-2 py-0.5 rounded bg-amber-900/30 border border-amber-700/50 text-amber-200 text-[11px]"
                                  data-testid="pvp-mvp-badge">
                                MVP · {mvpAdv.name}
                            </span>
                        )}
                    </div>
                </header>

                <section>
                    <h2 className="text-lg font-semibold mb-3">Cronaca della battaglia</h2>
                    {battleLog.length === 0 ? (
                        <div className="rounded-md border border-zinc-800 bg-zinc-900/40 p-4 text-sm text-zinc-500 italic"
                             data-testid="pvp-battle-log-empty">
                            La cronaca non è ancora disponibile. Torna dopo la risoluzione.
                        </div>
                    ) : (
                        <ol className="space-y-2" data-testid="pvp-battle-log">
                            {battleLog.map((step, i) => (
                                <li key={i}
                                    className="pl-4 border-l-2 border-red-800/60 py-1"
                                    data-testid={`pvp-log-turn-${step.turn}`}>
                                    <div className="text-[11px] uppercase tracking-wide text-red-400/60">
                                        Turno {step.turn}
                                    </div>
                                    <div className="text-sm font-mono leading-relaxed text-zinc-200">
                                        {step.text_it}
                                    </div>
                                </li>
                            ))}
                        </ol>
                    )}
                </section>

                <TeamsPanel battle={battle} />

                <p className="text-xs text-zinc-500 border-t border-zinc-800/60 pt-3">
                    Le battaglie PvP non generano oro, XP o loot. Solo Elo e prestigio.
                </p>
            </div>
        </div>
    );
}

function outcomeLabel(o) {
    return {
        challenger_win: "Vittoria dell'attaccante",
        defender_win: "Vittoria del difensore",
        draw: "Pareggio",
        defender_forfeit: "Forfait del difensore",
    }[o] || (o || "In corso");
}

function EloRow({ before, after, delta, right }) {
    if (before == null) return null;
    return (
        <div className={`text-xs mt-1 ${right ? "text-right" : ""}`}>
            <span className="font-mono">{before}</span>
            {after != null && (
                <>
                    {" → "}
                    <span className="font-mono">{after}</span>{" "}
                    <span className={delta > 0 ? "text-emerald-400" : delta < 0 ? "text-rose-400" : "text-zinc-500"}>
                        ({delta > 0 ? "+" : ""}{delta})
                    </span>
                </>
            )}
        </div>
    );
}

function TeamsPanel({ battle }) {
    return (
        <section className="grid grid-cols-1 md:grid-cols-2 gap-3" data-testid="pvp-teams-panel">
            <TeamCard title="Squadra attaccante" team={battle.challenger_team || []} />
            <TeamCard title="Squadra difensore" team={battle.defender_team || []} />
        </section>
    );
}

function TeamCard({ title, team }) {
    return (
        <div className="rounded-md border border-zinc-800 bg-zinc-900/40 p-3">
            <div className="text-xs uppercase tracking-wide text-zinc-500 mb-2">{title}</div>
            {team.length === 0 ? (
                <div className="text-xs text-zinc-600 italic">Nessuna squadra registrata (in attesa di risposta).</div>
            ) : (
                <ul className="space-y-1">
                    {team.map((a) => (
                        <li key={a.id} className="text-sm flex items-center justify-between gap-2">
                            <span className="truncate">
                                {a.name}
                                <span className="text-[11px] text-zinc-500 ml-2">
                                    {a.class_slug}
                                </span>
                            </span>
                            <span className="text-[11px] text-zinc-500 font-mono">Lv {a.level_snapshot}</span>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}
