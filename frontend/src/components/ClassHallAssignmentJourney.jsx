import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { CheckCircle2, Gift, Loader2, LockKeyhole, Search } from "lucide-react";
import { toast } from "sonner";

import { api, formatApiError } from "../lib/api";
import { Button } from "./ui/button";


const statLabel = (value) => ({
    strength: "Forza",
    agility: "Destrezza",
    intellect: "Intelligenza",
    endurance: "Tempra",
    faith: "Fede",
}[value] || value);

const humanStep = (value) => value
    .replaceAll("_", " ")
    .replace(/^./, (char) => char.toUpperCase());


export default function ClassHallAssignmentJourney() {
    const [searchParams] = useSearchParams();
    const requestedAdventurerId = searchParams.get("adventurer") || "";
    const [halls, setHalls] = useState([]);
    const [recruits, setRecruits] = useState([]);
    const [selectedRecruitId, setSelectedRecruitId] = useState("");
    const [selectedHallId, setSelectedHallId] = useState("");
    const [trial, setTrial] = useState(null);
    const [stepIndex, setStepIndex] = useState(0);
    const [explicitConfirmation, setExplicitConfirmation] = useState(false);
    const [query, setQuery] = useState("");
    const [wave, setWave] = useState("all");
    const [loading, setLoading] = useState(true);
    const [busy, setBusy] = useState("");

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const [choicesResponse, rosterResponse] = await Promise.all([
                api.get("/class-halls/assignment/choices"),
                api.get("/adventurers"),
            ]);
            const choices = choicesResponse.data?.halls || [];
            const undecided = (rosterResponse.data?.adventurers || [])
                .filter((adventurer) => adventurer.class_selection_required);
            setHalls(choices);
            setRecruits(undecided);
            setSelectedRecruitId((current) => {
                if (
                    undecided.some(
                        (adventurer) => adventurer.id === requestedAdventurerId,
                    )
                ) {
                    return requestedAdventurerId;
                }
                if (undecided.some((adventurer) => adventurer.id === current)) {
                    return current;
                }
                return undecided[0]?.id || "";
            });
        } catch (error) {
            toast.error(formatApiError(error));
            setHalls([]);
            setRecruits([]);
        } finally {
            setLoading(false);
        }
    }, [requestedAdventurerId]);

    useEffect(() => {
        load();
    }, [load]);

    const selectedRecruit = recruits.find(
        (adventurer) => adventurer.id === selectedRecruitId,
    );
    const selectedHall = halls.find((hall) => hall.hall_id === selectedHallId);
    const visibleHalls = useMemo(() => {
        const needle = query.trim().toLocaleLowerCase("it");
        return halls.filter((hall) => {
            const waveMatches = wave === "all" || hall.wave === wave;
            const searchMatches = !needle || [
                hall.class_name_it,
                hall.hall_name_it,
                hall.hall_master_witness_npc,
                hall.starter_item_name_it,
            ].some((value) => (value || "").toLocaleLowerCase("it").includes(needle));
            return waveMatches && searchMatches;
        });
    }, [halls, query, wave]);

    const resetJourney = () => {
        setSelectedHallId("");
        setTrial(null);
        setStepIndex(0);
        setExplicitConfirmation(false);
    };

    const startTrial = async (hall) => {
        if (!selectedRecruitId) {
            toast.error("Seleziona prima una recluta senza classe.");
            return;
        }
        setBusy(`start:${hall.hall_id}`);
        try {
            const response = await api.post(`/class-halls/${hall.hall_id}/trial/start`, {
                adventurer_id: selectedRecruitId,
            });
            const nextTrial = response.data?.trial;
            setSelectedHallId(hall.hall_id);
            setTrial(nextTrial);
            setStepIndex(nextTrial?.status === "completed"
                ? (nextTrial.required_steps || hall.trial_steps || []).length
                : 0);
            setExplicitConfirmation(false);
        } catch (error) {
            toast.error(formatApiError(error));
        } finally {
            setBusy("");
        }
    };

    const completeTrial = async () => {
        if (!selectedHall || !trial) return;
        setBusy("complete");
        try {
            const response = await api.post(
                `/class-halls/${selectedHall.hall_id}/trial/complete`,
                {
                    adventurer_id: selectedRecruitId,
                    trial_id: trial.id,
                    completed_steps: trial.required_steps || selectedHall.trial_steps,
                },
            );
            setTrial(response.data?.trial);
            toast.success("Prova sicura completata. Ora puoi confermare il sentiero.");
        } catch (error) {
            toast.error(formatApiError(error));
        } finally {
            setBusy("");
        }
    };

    const confirmHall = async () => {
        if (!selectedHall || !trial || !explicitConfirmation) return;
        setBusy("confirm");
        try {
            const response = await api.post(
                `/class-halls/${selectedHall.hall_id}/class/confirm`,
                {
                    adventurer_id: selectedRecruitId,
                    trial_id: trial.id,
                    explicit_confirmation: true,
                },
            );
            const reward = response.data?.reward;
            toast.success(
                `${response.data?.micro_log_it || "Sentiero scelto."} `
                + `${reward?.item_name_it ? `Ricevuto: ${reward.item_name_it}.` : ""}`,
            );
            resetJourney();
            await load();
        } catch (error) {
            toast.error(formatApiError(error));
        } finally {
            setBusy("");
        }
    };

    if (loading) {
        return (
            <section className="border border-amber/35 bg-amber/5 rounded-sm p-5 mb-6">
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Loader2 size={14} className="animate-spin" />
                    Preparazione dei sentieri di classe…
                </div>
            </section>
        );
    }

    return (
        <section
            data-testid="class-hall-assignment-journey"
            className="border border-amber/40 bg-amber/5 rounded-sm p-4 sm:p-5 mb-7"
        >
            <div className="flex items-start justify-between gap-4 flex-wrap mb-4">
                <div>
                    <p className="text-[10px] tracking-[0.22em] text-amber uppercase mb-1">
                        Primo sentiero
                    </p>
                    <h2 className="text-lg font-semibold">
                        Una recluta nasce senza classe
                    </h2>
                    <p className="text-xs text-muted-foreground mt-1 max-w-3xl">
                        Scegli la Sala, completa una prova sicura senza ricompense
                        sfruttabili e conferma il cammino. Solo allora la recluta
                        ottiene classe, maestro testimone e il suo primo item di lore.
                    </p>
                </div>
                <span className="text-[10px] border border-amber/30 px-2 py-1 rounded-sm">
                    {halls.length} CLASSI · {recruits.length}/3 RECLUTE IN ATTESA
                </span>
            </div>

            {recruits.length === 0 ? (
                <div className="border border-border/70 bg-card/70 rounded-sm p-4 text-sm">
                    <p className="text-muted-foreground mb-3">
                        Non hai reclute senza classe. Le nuove reclute appariranno qui
                        prima di poter partire per spedizioni o usare equip specializzato.
                    </p>
                    <Link to="/recruitment">
                        <Button size="sm">Vai al reclutamento</Button>
                    </Link>
                </div>
            ) : (
                <>
                    <div className="mb-4">
                        <p className="text-[10px] tracking-widest text-muted-foreground mb-2">
                            1 · SCEGLI LA RECLUTA
                        </p>
                        <div className="flex flex-wrap gap-2">
                            {recruits.map((adventurer) => (
                                <button
                                    key={adventurer.id}
                                    type="button"
                                    onClick={() => {
                                        setSelectedRecruitId(adventurer.id);
                                        resetJourney();
                                    }}
                                    className={`text-left border rounded-sm px-3 py-2 transition-colors ${
                                        selectedRecruitId === adventurer.id
                                            ? "border-amber bg-amber/10"
                                            : "border-border bg-card hover:border-amber/45"
                                    }`}
                                >
                                    <span className="block text-sm font-medium">
                                        {adventurer.name}
                                    </span>
                                    <span className="block text-[10px] text-muted-foreground">
                                        Recluta · Senza Classe · Lv {adventurer.level}
                                    </span>
                                </button>
                            ))}
                        </div>
                    </div>

                    {trial && selectedHall && (
                        <div className="border border-amber/45 bg-card rounded-sm p-4 mb-5">
                            <div className="flex justify-between gap-3 flex-wrap mb-3">
                                <div>
                                    <p className="text-[10px] tracking-widest text-amber">
                                        3 · PROVA SICURA
                                    </p>
                                    <h3 className="font-semibold">
                                        {selectedHall.class_name_it} · {selectedHall.hall_name_it}
                                    </h3>
                                    <p className="text-xs text-muted-foreground">
                                        {selectedHall.hall_master_witness_npc}
                                    </p>
                                </div>
                                <button
                                    type="button"
                                    className="text-[10px] text-muted-foreground hover:text-foreground"
                                    onClick={resetJourney}
                                >
                                    cambia Sala
                                </button>
                            </div>

                            <ol className="space-y-2 mb-4">
                                {(trial.required_steps || selectedHall.trial_steps || [])
                                    .map((step, index) => {
                                        const done = index < stepIndex
                                            || trial.status === "completed";
                                        const active = index === stepIndex
                                            && trial.status !== "completed";
                                        return (
                                            <li
                                                key={step}
                                                className="flex items-center justify-between gap-3 border border-border/70 px-3 py-2 rounded-sm"
                                            >
                                                <span className="text-xs flex items-center gap-2">
                                                    {done
                                                        ? <CheckCircle2 size={14} className="text-emerald-400" />
                                                        : <span className="text-muted-foreground">{index + 1}.</span>}
                                                    {humanStep(step)}
                                                </span>
                                                {active && (
                                                    <Button
                                                        size="sm"
                                                        variant="outline"
                                                        onClick={() => setStepIndex(index + 1)}
                                                    >
                                                        Esegui
                                                    </Button>
                                                )}
                                            </li>
                                        );
                                    })}
                            </ol>

                            {trial.status !== "completed" ? (
                                <Button
                                    onClick={completeTrial}
                                    disabled={
                                        busy === "complete"
                                        || stepIndex < (trial.required_steps || []).length
                                    }
                                >
                                    {busy === "complete" && (
                                        <Loader2 size={14} className="animate-spin mr-2" />
                                    )}
                                    Completa la prova sicura
                                </Button>
                            ) : (
                                <div className="border-t border-border pt-4">
                                    <label className="flex items-start gap-2 text-xs mb-3 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={explicitConfirmation}
                                            onChange={(event) => (
                                                setExplicitConfirmation(event.target.checked)
                                            )}
                                            className="mt-0.5"
                                        />
                                        <span>
                                            Confermo che <strong>{selectedRecruit?.name}</strong>{" "}
                                            seguirà il sentiero <strong>{selectedHall.class_name_it}</strong>.
                                            La scelta è permanente salvo un futuro Rito di Rinascita.
                                        </span>
                                    </label>
                                    <Button
                                        onClick={confirmHall}
                                        disabled={!explicitConfirmation || busy === "confirm"}
                                    >
                                        {busy === "confirm" && (
                                            <Loader2 size={14} className="animate-spin mr-2" />
                                        )}
                                        Conferma Sala e ricevi l'item
                                    </Button>
                                </div>
                            )}
                        </div>
                    )}

                    <div className="flex items-center justify-between gap-3 flex-wrap mb-3">
                        <p className="text-[10px] tracking-widest text-muted-foreground">
                            2 · SCEGLI UNA DELLE 27 SALE
                        </p>
                        <div className="flex items-center gap-2 flex-wrap">
                            <label className="relative">
                                <Search
                                    size={13}
                                    className="absolute left-2 top-1/2 -translate-y-1/2 text-muted-foreground"
                                />
                                <input
                                    value={query}
                                    onChange={(event) => setQuery(event.target.value)}
                                    placeholder="Cerca classe, Sala, maestro o item"
                                    className="h-8 w-64 max-w-[75vw] bg-background border border-border rounded-sm pl-7 pr-2 text-xs"
                                />
                            </label>
                            {["all", "A", "B", "C", "D", "E"].map((value) => (
                                <button
                                    key={value}
                                    type="button"
                                    onClick={() => setWave(value)}
                                    className={`h-8 px-2 text-[10px] border rounded-sm ${
                                        wave === value
                                            ? "border-amber text-amber"
                                            : "border-border text-muted-foreground"
                                    }`}
                                >
                                    {value === "all" ? "TUTTE" : `ONDATA ${value}`}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                        {visibleHalls.map((hall) => (
                            <article
                                key={hall.hall_id}
                                className={`border rounded-sm p-3 bg-card ${
                                    selectedHallId === hall.hall_id
                                        ? "border-amber"
                                        : "border-border"
                                }`}
                            >
                                <div className="flex justify-between gap-2 mb-2">
                                    <div>
                                        <h3 className="font-semibold text-sm">
                                            {hall.class_name_it}
                                        </h3>
                                        <p className="text-[11px] text-amber/90">
                                            {hall.hall_name_it}
                                        </p>
                                    </div>
                                    <span className="text-[9px] border border-border h-fit px-1.5 py-0.5">
                                        {hall.wave}
                                    </span>
                                </div>
                                <p className="text-[11px] italic text-muted-foreground mb-2">
                                    “{hall.lore_hook_it}”
                                </p>
                                <dl className="text-[10px] space-y-1 mb-3">
                                    <div className="flex justify-between gap-2">
                                        <dt className="text-muted-foreground">Maestro</dt>
                                        <dd className="text-right">{hall.hall_master_witness_npc}</dd>
                                    </div>
                                    <div className="flex justify-between gap-2">
                                        <dt className="text-muted-foreground">Stat chiave</dt>
                                        <dd>{statLabel(hall.primary_stat)}</dd>
                                    </div>
                                    <div className="flex justify-between gap-2">
                                        <dt className="text-muted-foreground">Item iniziale</dt>
                                        <dd className="text-right text-amber">
                                            {hall.starter_item_name_it}
                                        </dd>
                                    </div>
                                </dl>
                                <p className="text-[10px] text-muted-foreground mb-3">
                                    {hall.gameplay_style_it}
                                </p>
                                {hall.class_mechanic && (
                                    <div
                                        className="border border-sky-500/30 bg-sky-500/5 rounded-sm p-2 mb-3"
                                        data-testid={`hall-mechanic-${hall.hall_id}`}
                                    >
                                        <p className="text-[10px] text-sky-400 font-medium mb-1">
                                            {hall.class_mechanic.name_it}
                                        </p>
                                        <p className="text-[9px] text-muted-foreground mb-1.5">
                                            {hall.class_mechanic.summary_it}
                                        </p>
                                        <div className="flex flex-wrap gap-1">
                                            {(hall.class_mechanic.resonance_tags || []).map((tag) => (
                                                <span
                                                    key={tag}
                                                    className="text-[9px] border border-sky-500/25 px-1.5 py-0.5 rounded-sm"
                                                    title="Tag di risonanza: equipaggia un item con questo tag per attivare il bonus di classe."
                                                >
                                                    {tag}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}
                                <Button
                                    size="sm"
                                    variant={selectedHallId === hall.hall_id ? "default" : "outline"}
                                    className="w-full"
                                    disabled={
                                        !hall.assignment_enabled
                                        || busy === `start:${hall.hall_id}`
                                    }
                                    onClick={() => startTrial(hall)}
                                >
                                    {busy === `start:${hall.hall_id}` ? (
                                        <Loader2 size={13} className="animate-spin mr-2" />
                                    ) : hall.assignment_enabled ? (
                                        <Gift size={13} className="mr-2" />
                                    ) : (
                                        <LockKeyhole size={13} className="mr-2" />
                                    )}
                                    {hall.assignment_enabled
                                        ? "Inizia la prova"
                                        : "Non abilitata su questo server"}
                                </Button>
                            </article>
                        ))}
                    </div>
                </>
            )}
        </section>
    );
}
