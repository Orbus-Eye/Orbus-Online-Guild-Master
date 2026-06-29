// ROUND 12.B — Arena page. Defense team builder + opponents picker + challenge flow + history.
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";

import AppHeader from "../components/AppHeader";
import { Button } from "../components/ui/button";
import LeagueBadge from "../components/arena/LeagueBadge";
import DefenseTeamBuilder from "../components/arena/DefenseTeamBuilder";
import OpponentCard from "../components/arena/OpponentCard";
import MatchReportModal from "../components/arena/MatchReportModal";
import MatchHistoryRow from "../components/arena/MatchHistoryRow";
import { pvpEligibility } from "../utils/pvpEligibility";

const API = (process.env.REACT_APP_BACKEND_URL || "") + "/api";
const cfg = { withCredentials: true, timeout: 15_000 };

const DAILY_LIMIT = 10;

export default function Arena() {
    const [season, setSeason] = useState(null);
    const [defenseInfo, setDefenseInfo] = useState(null);  // { team, summary, min_level_required, team_size_required }
    const [opponents, setOpponents] = useState([]);
    const [history, setHistory] = useState([]);
    const [adventurers, setAdventurers] = useState([]);
    const [myGuild, setMyGuild] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [savingDefense, setSavingDefense] = useState(false);

    const [pickerOpen, setPickerOpen] = useState(false);
    const [pickerOpp, setPickerOpp] = useState(null);
    const [attackIds, setAttackIds] = useState([]);
    const [challenging, setChallenging] = useState(false);
    const [reportMatch, setReportMatch] = useState(null);

    const fetchAll = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [sRes, gRes, advRes, dtRes, hRes, oppRes] = await Promise.all([
                axios.get(`${API}/seasons/current`, cfg).catch((e) => {
                    if (e?.response?.status === 404) return { data: { season: null } };
                    throw e;
                }),
                axios.get(`${API}/guilds/me`, cfg),
                axios.get(`${API}/adventurers`, cfg).catch(() => ({ data: { adventurers: [] } })),
                axios.get(`${API}/pvp/defense-team`, cfg),
                axios.get(`${API}/pvp/matches?limit=20`, cfg).catch(() => ({ data: { matches: [] } })),
                axios.get(`${API}/pvp/opponents`, cfg).catch((e) => {
                    if (e?.response?.status === 423) return { data: { opponents: [] } };
                    throw e;
                }),
            ]);
            setSeason(sRes.data.season || null);
            const guildData = gRes.data?.guild || gRes.data || null;
            setMyGuild(guildData);
            setAdventurers(advRes.data?.adventurers || advRes.data || []);
            setDefenseInfo(dtRes.data);
            setHistory(hRes.data?.matches || []);
            setOpponents(oppRes.data?.opponents || []);
        } catch (err) {
            console.error("[Arena] load failed:", err);
            setError(err?.response?.data?.detail?.user_message || "Caricamento fallito.");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { fetchAll(); }, [fetchAll]);

    const minLv = defenseInfo?.min_level_required ?? 3;
    const teamSize = defenseInfo?.team_size_required ?? 5;
    const hasValidDefense = !!(defenseInfo?.team?.is_valid);
    const initialDefenseIds = defenseInfo?.team?.adventurer_ids || [];

    // Daily counter (compute locally from history filtered to today UTC + attacker_guild_id = me).
    const todayAttacks = useMemo(() => {
        if (!myGuild) return 0;
        const todayUTC = new Date();
        todayUTC.setUTCHours(0, 0, 0, 0);
        return history.filter((m) =>
            m.attacker_guild_id === myGuild.id
            && new Date(m.created_at) >= todayUTC
            && m.mode === "ranked"
        ).length;
    }, [history, myGuild]);
    const remainingAttacks = Math.max(0, DAILY_LIMIT - todayAttacks);

    const handleSaveDefense = async (ids) => {
        setSavingDefense(true);
        try {
            const r = await axios.put(`${API}/pvp/defense-team`, { adventurer_ids: ids }, cfg);
            setDefenseInfo(r.data);
            toast.success("Squadra difensiva salvata.");
        } catch (err) {
            console.error("[Arena] save defense failed:", err);
            const detail = err?.response?.data?.detail;
            const warnings = detail?.warnings ? ` (${detail.warnings.join("; ")})` : "";
            toast.error((detail?.user_message || "Salvataggio fallito.") + warnings);
        } finally {
            setSavingDefense(false);
        }
    };

    const openPicker = (opp) => {
        setPickerOpp(opp);
        setAttackIds([]);
        setPickerOpen(true);
    };

    const toggleAttacker = (id) => {
        setAttackIds((cur) => {
            if (cur.includes(id)) return cur.filter((x) => x !== id);
            if (cur.length >= teamSize) return cur;
            return [...cur, id];
        });
    };

    const submitChallenge = async () => {
        if (attackIds.length !== teamSize) return;
        setChallenging(true);
        try {
            const r = await axios.post(`${API}/pvp/challenge`, {
                opponent_guild_public_id: pickerOpp.guild_public_id,
                attacker_adventurer_ids: attackIds,
                mode: "ranked",
            }, cfg);
            setPickerOpen(false);
            setReportMatch(r.data.match);
            await fetchAll();  // refresh opponents + history + defense
        } catch (err) {
            console.error("[Arena] challenge failed:", err);
            const d = err?.response?.data?.detail;
            const warn = d?.warnings ? ` (${d.warnings.join("; ")})` : "";
            toast.error((d?.user_message || "Sfida fallita.") + warn);
        } finally {
            setChallenging(false);
        }
    };

    return (
        <div className="min-h-screen bg-background">
            <AppHeader />
            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-6">
                <header className="mb-6">
                    <h1 className="text-2xl sm:text-3xl tracking-[0.2em] text-amber font-light" data-testid="arena-title">
                        :: Arena delle Gilde
                    </h1>
                    <p className="text-xs text-muted-foreground mt-2 max-w-2xl">
                        PvP asincrono e non distruttivo. Nessuna perdita di oro, item o avventurieri.
                        Il rating sale e scende; il resto della gilda resta intatto.
                    </p>
                </header>

                {loading && <p data-testid="arena-loading" className="text-sm text-muted-foreground italic">Caricamento Arena…</p>}
                {error && !loading && <p data-testid="arena-error" className="text-sm text-red-400">{error}</p>}

                {!loading && !season && !error && (
                    <div data-testid="arena-no-season" className="border border-dashed border-border rounded-sm p-6 text-center">
                        <p className="text-sm text-muted-foreground">
                            Nessuna stagione attiva. L&apos;Arena è chiusa.
                        </p>
                        <Link to="/seasons" className="mt-3 inline-block">
                            <Button size="sm" variant="outline">Vai alle Stagioni</Button>
                        </Link>
                    </div>
                )}

                {!loading && season && (
                    <>
                        {/* ELIGIBILITY BANNER */}
                        <div
                            data-testid="arena-eligibility-banner"
                            className={`border rounded-sm px-3 py-2 mb-5 text-xs flex items-center justify-between flex-wrap gap-2 ${
                                hasValidDefense
                                    ? "border-emerald-500/40 text-emerald-300"
                                    : "border-amber/40 text-amber"
                            }`}
                        >
                            <span>
                                {hasValidDefense
                                    ? "✓ Pronto per ranked. Buona caccia, custode."
                                    : "✦ Imposta una difesa valida per partecipare alle ranked."}
                            </span>
                            <span data-testid="arena-daily-counter" className="text-muted-foreground">
                                Sfide oggi: <strong className="text-foreground">{todayAttacks}/{DAILY_LIMIT}</strong>
                            </span>
                        </div>

                        {/* DEFENSE TEAM */}
                        <DefenseTeamBuilder
                            adventurers={adventurers}
                            minLevel={minLv}
                            initialIds={initialDefenseIds}
                            saving={savingDefense}
                            onSave={handleSaveDefense}
                        />

                        {/* OPPONENTS */}
                        <section data-testid="arena-opponents" className="mt-6 border border-border bg-card rounded-sm p-4">
                            <div className="flex items-center justify-between mb-3">
                                <h3 className="text-sm tracking-[0.25em] text-amber">:: Avversari disponibili</h3>
                                <Button size="sm" variant="ghost" onClick={fetchAll} data-testid="opponents-refresh-btn">
                                    Ricarica
                                </Button>
                            </div>
                            {opponents.length === 0 ? (
                                <p data-testid="opponents-empty" className="text-[12px] text-muted-foreground italic">
                                    Nessun avversario nelle vicinanze. Riprova più tardi o configura prima la tua difesa.
                                </p>
                            ) : (
                                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                                    {opponents.map((o) => (
                                        <OpponentCard
                                            key={o.guild_public_id}
                                            opp={o}
                                            onChallenge={openPicker}
                                            disabled={!hasValidDefense || remainingAttacks <= 0}
                                        />
                                    ))}
                                </div>
                            )}
                            {!hasValidDefense && (
                                <p className="mt-2 text-[10px] text-muted-foreground italic">
                                    Sfide bloccate finché non salvi una squadra difensiva.
                                </p>
                            )}
                            {remainingAttacks <= 0 && (
                                <p className="mt-2 text-[10px] text-amber italic">
                                    Hai esaurito le sfide giornaliere (10/giorno UTC). Reset a mezzanotte UTC.
                                </p>
                            )}
                        </section>

                        {/* HISTORY */}
                        <section data-testid="arena-history" className="mt-6 border border-border bg-card rounded-sm p-4">
                            <h3 className="text-sm tracking-[0.25em] text-amber mb-3">:: Storico match</h3>
                            {history.length === 0 ? (
                                <p data-testid="history-empty" className="text-[12px] text-muted-foreground italic">
                                    Nessun match nello storico. Comincia sfidando un avversario.
                                </p>
                            ) : (
                                <div className="space-y-2">
                                    {history.map((m) => (
                                        <MatchHistoryRow
                                            key={m.match_id}
                                            match={m}
                                            myGuildId={myGuild?.id}
                                            onOpen={async (cur) => {
                                                // Open report — re-fetch detail to include `report_it`.
                                                try {
                                                    const r = await axios.get(`${API}/pvp/matches/${cur.match_id}`, cfg);
                                                    setReportMatch(r.data.match);
                                                } catch (err) {
                                                    console.error("[Arena] open report failed:", err);
                                                    toast.error("Impossibile aprire il report.");
                                                }
                                            }}
                                        />
                                    ))}
                                </div>
                            )}
                        </section>
                    </>
                )}
            </main>

            {/* PICKER MODAL */}
            {pickerOpen && pickerOpp && (
                <div
                    data-testid="attacker-picker-modal"
                    className="fixed inset-0 z-50 bg-background/90 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto"
                    onClick={() => !challenging && setPickerOpen(false)}
                >
                    <div
                        className="bg-card border border-border rounded-sm max-w-2xl w-full p-5"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="flex items-center justify-between mb-3">
                            <h2 className="text-sm tracking-[0.3em] text-amber">:: Scegli i 5 attaccanti</h2>
                            <Button variant="ghost" size="sm" onClick={() => setPickerOpen(false)} disabled={challenging}>
                                Annulla
                            </Button>
                        </div>
                        <p className="text-[11px] text-muted-foreground mb-3">
                            Sfidi: <strong className="text-foreground">{pickerOpp.guild_name}</strong>
                            {" · "}<LeagueBadge league={pickerOpp.league} /> · Rating {pickerOpp.rating}
                        </p>
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 max-h-[50vh] overflow-y-auto">
                            {adventurers.map((a) => {
                                const elig = pvpEligibility(a, { minLevel: minLv, alreadyChosenIds: attackIds });
                                const picked = attackIds.includes(a.id);
                                const disabled = !elig.eligible && !picked;
                                return (
                                    <button
                                        type="button"
                                        key={a.id}
                                        disabled={disabled}
                                        onClick={() => toggleAttacker(a.id)}
                                        data-testid={`attack-pick-${a.id}`}
                                        className={`text-left border rounded-sm p-2 text-xs ${
                                            picked
                                                ? "border-amber/70 bg-amber/10"
                                                : disabled
                                                    ? "border-border/40 opacity-50 cursor-not-allowed"
                                                    : "border-border bg-card hover:bg-secondary/40"
                                        }`}
                                        title={elig.reason || ""}
                                    >
                                        <div className="font-mono truncate">{a.name}</div>
                                        <div className="text-[10px] text-muted-foreground">
                                            Lv {a.level} · {a.role || "?"} · PWR {a.team_power || 0}
                                        </div>
                                        {disabled && (
                                            <div className="text-[9px] text-red-400/80 mt-0.5">{elig.reason}</div>
                                        )}
                                    </button>
                                );
                            })}
                        </div>
                        <div className="mt-4 flex justify-between items-center">
                            <span className="text-xs text-muted-foreground">
                                {attackIds.length}/{teamSize} selezionati
                            </span>
                            <Button
                                size="sm"
                                disabled={attackIds.length !== teamSize || challenging}
                                onClick={submitChallenge}
                                data-testid="attacker-confirm-btn"
                            >
                                {challenging ? "Combattendo…" : "Conferma sfida"}
                            </Button>
                        </div>
                    </div>
                </div>
            )}

            {/* MATCH REPORT */}
            {reportMatch && (
                <MatchReportModal
                    match={reportMatch}
                    myGuildId={myGuild?.id}
                    onClose={() => setReportMatch(null)}
                />
            )}
        </div>
    );
}
