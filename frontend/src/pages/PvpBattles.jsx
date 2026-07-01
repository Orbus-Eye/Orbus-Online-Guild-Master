// ROUND 16.3 Phase 7A Iter2 — Active + history battles list.
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { api } from "../lib/api";
import AppHeader from "../components/AppHeader";

export default function PvpBattles() {
    const [loading, setLoading] = useState(true);
    const [tab, setTab] = useState("active");
    const [active, setActive] = useState([]);
    const [history, setHistory] = useState([]);
    const [myGuildId, setMyGuildId] = useState(null);

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const [g, b] = await Promise.all([
                api.get("/guilds/me"),
                api.get("/pvp/battles/mine"),
            ]);
            setMyGuildId(g.data?.guild?.id || g.data?.id);
            setActive(b.data?.active || []);
            setHistory(b.data?.history || []);
        } catch (e) {
            toast.error(e?.response?.data?.detail?.user_message || "Caricamento fallito");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { load(); }, [load]);

    const respond = async (battleId) => {
        const advRes = await api.get("/adventurers").catch(() => ({ data: { adventurers: [] } }));
        const advs = (advRes.data?.adventurers || advRes.data || [])
            .filter((a) => a.is_available !== false)
            .slice(0, 5)
            .map((a) => a.id);
        if (advs.length !== 5) {
            toast.error("Servono almeno 5 avventurieri disponibili per accettare.");
            return;
        }
        try {
            await api.post(`/pvp/battles/${battleId}/respond`, { adventurer_ids: advs });
            toast.success("Sfida accettata! Risoluzione entro 24 ore.");
            load();
        } catch (e) {
            toast.error(e?.response?.data?.detail?.user_message || "Errore accettazione.");
        }
    };

    const decline = async (battleId) => {
        try {
            await api.post(`/pvp/battles/${battleId}/decline`, {});
            toast.success("Sfida declinata.");
            load();
        } catch (e) {
            toast.error(e?.response?.data?.detail?.user_message || "Errore declino.");
        }
    };

    if (loading) return (
        <div className="min-h-screen bg-zinc-950 text-zinc-100 pb-32 md:pb-8">
            <AppHeader />
            <div className="max-w-6xl mx-auto px-4 py-6 text-sm text-zinc-500">Caricamento…</div>
        </div>
    );

    return (
        <div className="min-h-screen bg-zinc-950 text-zinc-100 pb-32 md:pb-8">
            <AppHeader />
            <div className="max-w-6xl mx-auto px-4 py-6 space-y-4" data-testid="pvp-battles-page">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                    <h1 className="text-2xl md:text-3xl font-semibold">Le mie battaglie</h1>
                    <Link to="/pvp"
                          className="inline-flex items-center justify-center px-4 py-2 rounded-md border border-zinc-800 hover:border-zinc-700 text-sm w-full md:w-auto min-h-[44px]"
                          data-testid="pvp-back-to-opponents">
                        ← Torna agli avversari
                    </Link>
                </div>

                <div className="flex gap-1 border-b border-zinc-800">
                    {["active", "history"].map((t) => (
                        <button key={t} onClick={() => setTab(t)}
                                className={`px-4 py-2 text-sm border-b-2 -mb-px min-h-[44px] ${
                                    tab === t
                                        ? "border-red-700 text-zinc-100"
                                        : "border-transparent text-zinc-500 hover:text-zinc-300"
                                }`}
                                data-testid={`pvp-tab-${t}`}>
                            {t === "active" ? `Attive (${active.length})` : `Storico (${history.length})`}
                        </button>
                    ))}
                </div>

                {tab === "active" ? (
                    active.length === 0 ? (
                        <div className="rounded-md border border-zinc-800 bg-zinc-900/40 p-6 text-center text-sm text-zinc-500"
                             data-testid="pvp-active-empty">
                            Nessuna battaglia attiva. <Link to="/pvp" className="text-red-400 hover:underline">Cerca un avversario</Link>.
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {active.map((b) => (
                                <ActiveBattleRow
                                    key={b.id} battle={b} myGuildId={myGuildId}
                                    onRespond={respond} onDecline={decline} />
                            ))}
                        </div>
                    )
                ) : (
                    history.length === 0 ? (
                        <div className="rounded-md border border-zinc-800 bg-zinc-900/40 p-6 text-center text-sm text-zinc-500"
                             data-testid="pvp-history-empty">
                            Nessuna battaglia risolta.
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {history.map((b) => (
                                <HistoryRow key={b.id} battle={b} myGuildId={myGuildId} />
                            ))}
                        </div>
                    )
                )}
            </div>
        </div>
    );
}

const STATUS_LABEL = {
    pending_response: "In attesa di risposta",
    resolving: "In risoluzione",
    resolved: "Risolta",
    declined: "Declinata",
    expired: "Scaduta",
};

function ActiveBattleRow({ battle, myGuildId, onRespond, onDecline }) {
    const isDefender = battle.defender_guild_id === myGuildId;
    const isPending = battle.status === "pending_response";
    const deadline = battle.response_deadline || battle.resolves_at;
    return (
        <div className="rounded-md border border-zinc-800 bg-zinc-900/40 p-4 space-y-2"
             data-testid={`pvp-active-battle-${battle.id}`}>
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
                <div>
                    <div className="text-sm font-medium">
                        {isDefender ? "Ti sfida" : "Stai sfidando"}: <span className="text-zinc-300">{isDefender ? battle.challenger_guild_id : battle.defender_guild_id}</span>
                    </div>
                    <div className="text-xs text-zinc-500 mt-1">
                        <span className="uppercase tracking-wide">{STATUS_LABEL[battle.status] || battle.status}</span>
                        {deadline && <> · scade {new Date(deadline).toLocaleString("it-IT")}</>}
                    </div>
                </div>
                <div className="flex gap-2 flex-wrap">
                    {isDefender && isPending && (
                        <>
                            <button onClick={() => onRespond(battle.id)}
                                    className="px-3 py-1.5 rounded-md bg-emerald-900/50 hover:bg-emerald-900/70 border border-emerald-800/60 text-xs min-h-[44px] w-full md:w-auto"
                                    data-testid={`pvp-accept-${battle.id}`}>
                                Accetta
                            </button>
                            <button onClick={() => onDecline(battle.id)}
                                    className="px-3 py-1.5 rounded-md bg-zinc-800/60 hover:bg-zinc-700/70 border border-zinc-700 text-xs min-h-[44px] w-full md:w-auto"
                                    data-testid={`pvp-decline-${battle.id}`}>
                                Declina
                            </button>
                        </>
                    )}
                    <Link to={`/pvp/battles/${battle.id}`}
                          className="px-3 py-1.5 rounded-md border border-zinc-700 hover:border-zinc-600 text-xs min-h-[44px] w-full md:w-auto inline-flex items-center justify-center"
                          data-testid={`pvp-detail-${battle.id}`}>
                        Dettagli
                    </Link>
                </div>
            </div>
        </div>
    );
}

const OUTCOME_LABEL = {
    challenger_win: { label: "Vittoria attaccante", color: "text-emerald-400" },
    defender_win: { label: "Vittoria difensore", color: "text-emerald-400" },
    draw: { label: "Pareggio", color: "text-zinc-400" },
    defender_forfeit: { label: "Forfait avversario", color: "text-amber-400" },
};

function HistoryRow({ battle, myGuildId }) {
    const meIsChall = battle.challenger_guild_id === myGuildId;
    const won =
        (battle.outcome === "challenger_win" && meIsChall) ||
        (battle.outcome === "defender_win" && !meIsChall) ||
        (battle.outcome === "defender_forfeit" && meIsChall);
    const lost =
        (battle.outcome === "defender_win" && meIsChall) ||
        (battle.outcome === "challenger_win" && !meIsChall) ||
        (battle.outcome === "defender_forfeit" && !meIsChall);
    const label = won ? "Vittoria" : lost ? "Sconfitta" : "Pareggio";
    const color = won ? "text-emerald-400" : lost ? "text-rose-400" : "text-zinc-400";
    const eloBefore = meIsChall ? battle.challenger_elo_snapshot : battle.defender_elo_snapshot;
    const eloAfter = meIsChall ? battle.challenger_elo_after : battle.defender_elo_after;
    const delta = eloAfter != null && eloBefore != null ? eloAfter - eloBefore : null;
    return (
        <div className="rounded-md border border-zinc-800 bg-zinc-900/40 p-4"
             data-testid={`pvp-history-${battle.id}`}>
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
                <div>
                    <div className="text-sm">
                        <span className={`font-semibold ${color}`}>{label}</span>
                        <span className="text-zinc-500"> · {OUTCOME_LABEL[battle.outcome]?.label || battle.outcome}</span>
                    </div>
                    <div className="text-xs text-zinc-500 mt-1">
                        vs <span className="text-zinc-300">{meIsChall ? battle.defender_guild_id : battle.challenger_guild_id}</span>
                        {battle.resolved_at && <> · {new Date(battle.resolved_at).toLocaleDateString("it-IT")}</>}
                    </div>
                    {delta != null && (
                        <div className="text-xs mt-1">
                            Elo <span className="font-mono">{eloBefore}</span> → <span className="font-mono">{eloAfter}</span>{" "}
                            <span className={delta > 0 ? "text-emerald-400" : delta < 0 ? "text-rose-400" : "text-zinc-500"}>
                                ({delta > 0 ? "+" : ""}{delta})
                            </span>
                        </div>
                    )}
                </div>
                <Link to={`/pvp/battles/${battle.id}`}
                      className="px-3 py-1.5 rounded-md border border-zinc-700 hover:border-zinc-600 text-xs min-h-[44px] w-full md:w-auto inline-flex items-center justify-center"
                      data-testid={`pvp-history-report-${battle.id}`}>
                    Report
                </Link>
            </div>
        </div>
    );
}
