// ROUND 16.3 Phase 7A Iter2 — Challenge preparation (team select + send).
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { api } from "../lib/api";
import AppHeader from "../components/AppHeader";

const TEAM_SIZE = 5;

export default function PvpChallenge() {
    const { defenderGuildId } = useParams();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [defender, setDefender] = useState(null);
    const [advs, setAdvs] = useState([]);
    const [selected, setSelected] = useState([]);
    const [submitting, setSubmitting] = useState(false);

    const load = useCallback(async () => {
        setLoading(true);
        try {
            // Fetch opponents list to hydrate defender (public payload only).
            const oppRes = await api.get("/pvp/opponents").catch(() => ({ data: { opponents: [] } }));
            const d = (oppRes.data?.opponents || []).find(
                (o) => o.guild_id === defenderGuildId,
            );
            setDefender(d || { guild_id: defenderGuildId, guild_name: "?", elo: "?" });
            const advRes = await api.get("/adventurers");
            const advs = advRes.data?.adventurers || advRes.data || [];
            setAdvs(advs.filter((a) => a.is_available !== false));
        } catch (e) {
            toast.error(e?.response?.data?.detail?.user_message || "Caricamento fallito");
        } finally {
            setLoading(false);
        }
    }, [defenderGuildId]);

    useEffect(() => { load(); }, [load]);

    const toggle = (id) => {
        setSelected((prev) => {
            if (prev.includes(id)) return prev.filter((x) => x !== id);
            if (prev.length >= TEAM_SIZE) return prev;
            return [...prev, id];
        });
    };

    const estPower = useMemo(() => {
        const set = new Set(selected);
        return advs.filter((a) => set.has(a.id)).reduce(
            (sum, a) => sum + (a.strength || 0) + (a.agility || 0)
                + (a.intellect || 0) + (a.endurance || 0)
                + (a.faith || 0) + (a.level || 1) * 3, 0
        );
    }, [selected, advs]);

    const submit = async () => {
        if (selected.length !== TEAM_SIZE) {
            toast.error(`Seleziona esattamente ${TEAM_SIZE} avventurieri.`);
            return;
        }
        setSubmitting(true);
        try {
            const r = await api.post(`/pvp/challenge/${defenderGuildId}`, {
                adventurer_ids: selected,
            });
            toast.success("Sfida inviata! L'avversario ha 24 ore per rispondere.");
            navigate(`/pvp/battles/${r.data.battle.id}`);
        } catch (e) {
            const d = e?.response?.data?.detail;
            toast.error(d?.user_message || d?.code || "Invio sfida fallito.");
        } finally {
            setSubmitting(false);
        }
    };

    if (loading) return (
        <div className="min-h-screen bg-zinc-950 text-zinc-100 pb-32 md:pb-8">
            <AppHeader />
            <div className="max-w-4xl mx-auto px-4 py-6 text-sm text-zinc-500">Caricamento…</div>
        </div>
    );

    return (
        <div className="min-h-screen bg-zinc-950 text-zinc-100 pb-32 md:pb-8">
            <AppHeader />
            <div className="max-w-4xl mx-auto px-4 py-6 space-y-6" data-testid="pvp-challenge-page">
                <Link to="/pvp" className="text-xs text-zinc-500 hover:text-zinc-300">
                    ← PvP
                </Link>
                <header className="border border-red-800/40 bg-red-950/20 rounded-md p-4">
                    <div className="text-xs uppercase tracking-wide text-red-300/70">Sfida in preparazione</div>
                    <div className="text-xl md:text-2xl font-semibold mt-1">{defender?.guild_name}</div>
                    <div className="text-xs text-zinc-500 mt-1">
                        Livello {defender?.guild_level ?? "?"} · <span className="font-mono">Elo {defender?.elo ?? "?"}</span>
                    </div>
                </header>

                <section>
                    <div className="flex items-center justify-between mb-3">
                        <h2 className="text-lg font-semibold">
                            Componi la squadra ({selected.length}/{TEAM_SIZE})
                        </h2>
                        <div className="text-xs text-zinc-500">
                            Potenza stimata: <span className="font-mono text-zinc-300">{estPower}</span>
                        </div>
                    </div>
                    {advs.length < TEAM_SIZE && (
                        <div className="mb-3 text-xs text-amber-300/80 border border-amber-900/40 bg-amber-950/20 rounded p-2">
                            Hai meno di 5 avventurieri disponibili. Impossibile inviare la sfida.
                        </div>
                    )}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2" data-testid="pvp-adv-picker">
                        {advs.map((a) => {
                            const on = selected.includes(a.id);
                            return (
                                <button
                                    key={a.id}
                                    onClick={() => toggle(a.id)}
                                    className={`text-left rounded-md border p-3 transition min-h-[44px] ${
                                        on
                                            ? "border-red-700 bg-red-950/40"
                                            : "border-zinc-800 bg-zinc-900/40 hover:border-zinc-700"
                                    }`}
                                    data-testid={`pvp-adv-${a.id}`}
                                >
                                    <div className="flex items-center justify-between gap-2">
                                        <span className="font-medium truncate">{a.name}</span>
                                        <span className="text-[11px] text-zinc-500">Lv {a.level || 1}</span>
                                    </div>
                                    <div className="text-[11px] text-zinc-500 mt-0.5">
                                        {a.class_name || a.class_slug || "?"}
                                        {a.specialization_slug && ` · ${a.specialization_slug}`}
                                    </div>
                                </button>
                            );
                        })}
                    </div>
                </section>

                <div className="border-t border-zinc-800 pt-4 flex flex-col md:flex-row md:justify-end gap-2">
                    <Link
                        to="/pvp"
                        className="inline-flex items-center justify-center px-4 py-2 rounded-md border border-zinc-800 hover:border-zinc-700 text-sm w-full md:w-auto min-h-[44px]"
                        data-testid="pvp-cancel-btn"
                    >
                        Annulla
                    </Link>
                    <button
                        disabled={submitting || selected.length !== TEAM_SIZE}
                        onClick={submit}
                        className="inline-flex items-center justify-center px-4 py-2 rounded-md bg-red-900/60 hover:bg-red-900/80 border border-red-800/60 text-sm w-full md:w-auto min-h-[44px] disabled:opacity-40 disabled:cursor-not-allowed"
                        data-testid="pvp-send-challenge-btn"
                    >
                        {submitting ? "Invio…" : "Invia Sfida"}
                    </button>
                </div>
            </div>
        </div>
    );
}
