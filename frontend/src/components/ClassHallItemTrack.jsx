import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, Gift, Loader2, LockKeyhole, RefreshCw } from "lucide-react";
import { toast } from "sonner";

import { api, formatApiError } from "../lib/api";
import { Button } from "./ui/button";


const statusLabel = {
    claimed: "OTTENUTO",
    claimable: "RISCATTABILE",
    locked: "BLOCCATO",
};

const requirementText = (requirement) => {
    if (!requirement) return "";
    const current = requirement.current ?? 0;
    const target = requirement.target ?? 1;
    const labels = {
        class_hall_chosen: "Sala scelta",
        signature_item_equipped: "Item-firma equipaggiato",
        first_expedition_completed: "Spedizioni completate",
        adventurer_level_2: "Livello avventuriero",
        three_expeditions_completed: "Spedizioni completate",
    };
    return `${labels[requirement.milestone] || requirement.milestone}: ${current}/${target}`;
};


export default function ClassHallItemTrack() {
    const [adventurers, setAdventurers] = useState([]);
    const [selectedId, setSelectedId] = useState("");
    const [track, setTrack] = useState(null);
    const [loadingRoster, setLoadingRoster] = useState(true);
    const [loadingTrack, setLoadingTrack] = useState(false);
    const [busySlug, setBusySlug] = useState("");

    const loadAdventurers = useCallback(async () => {
        setLoadingRoster(true);
        try {
            const response = await api.get("/adventurers");
            const all = response.data?.adventurers || [];
            const assigned = all.filter((adventurer) => adventurer.class_hall_id);
            setAdventurers(assigned);
            setSelectedId((current) => (
                assigned.some((adventurer) => adventurer.id === current)
                    ? current
                    : (assigned[0]?.id || "")
            ));
            if (assigned.length === 0) setTrack(null);
        } catch (error) {
            toast.error(formatApiError(error));
        } finally {
            setLoadingRoster(false);
        }
    }, []);

    useEffect(() => { loadAdventurers(); }, [loadAdventurers]);

    useEffect(() => {
        const selected = adventurers.find((adventurer) => adventurer.id === selectedId);
        if (!selected?.class_hall_id) {
            setTrack(null);
            return undefined;
        }
        let cancelled = false;
        setLoadingTrack(true);
        api.get(`/class-halls/${selected.class_hall_id}/item-track`, {
            params: { adventurer_id: selected.id },
        }).then((response) => {
            if (!cancelled) setTrack(response.data);
        }).catch((error) => {
            if (!cancelled) {
                setTrack(null);
                toast.error(formatApiError(error));
            }
        }).finally(() => {
            if (!cancelled) setLoadingTrack(false);
        });
        return () => { cancelled = true; };
    }, [adventurers, selectedId]);

    const claim = async (entry) => {
        if (!track || entry.status !== "claimable") return;
        setBusySlug(entry.item.slug);
        try {
            const response = await api.post(
                `/class-halls/${track.hall.hall_id}/item-track/${entry.item.slug}/claim`,
                { adventurer_id: selectedId },
            );
            setTrack(response.data.track);
            toast.success(`${response.data.reward.item_name_it} aggiunto all'inventario.`);
        } catch (error) {
            toast.error(formatApiError(error));
        } finally {
            setBusySlug("");
        }
    };

    return (
        <section
            data-testid="class-hall-item-track"
            className="border border-amber/35 bg-card rounded-sm p-4 mb-5"
        >
            <div className="flex items-start justify-between gap-3 flex-wrap mb-4">
                <div>
                    <p className="text-[10px] tracking-[0.2em] text-amber mb-1">
                        :: SENTIERO DEGLI OGGETTI
                    </p>
                    <h2 className="text-base font-semibold">
                        Cinque reliquie, un'identità di classe
                    </h2>
                    <p className="text-[11px] text-muted-foreground mt-1 max-w-2xl">
                        Ogni Sala custodisce cinque item singolari. Equipaggia, viaggia e
                        fai crescere l'avventuriero per svelarli tutti.
                    </p>
                </div>
                <Button
                    size="sm"
                    variant="outline"
                    onClick={loadAdventurers}
                    disabled={loadingRoster}
                    data-testid="class-hall-item-track-refresh"
                >
                    <RefreshCw
                        size={13}
                        className={loadingRoster ? "animate-spin mr-2" : "mr-2"}
                    />
                    Aggiorna
                </Button>
            </div>

            {!loadingRoster && adventurers.length === 0 && (
                <div className="border border-border rounded-sm p-4 text-xs text-muted-foreground">
                    Completa prima la prova di una Sala: il Sentiero degli oggetti
                    apparirà qui.
                </div>
            )}

            {adventurers.length > 0 && (
                <>
                    <label className="block text-[10px] tracking-widest text-muted-foreground mb-3">
                        AVVENTURIERO
                        <select
                            value={selectedId}
                            onChange={(event) => setSelectedId(event.target.value)}
                            className="mt-1 block w-full sm:w-80 h-9 bg-background border border-border rounded-sm px-2 text-xs text-foreground"
                            data-testid="class-hall-item-track-adventurer"
                        >
                            {adventurers.map((adventurer) => (
                                <option key={adventurer.id} value={adventurer.id}>
                                    {adventurer.name} · {adventurer.class_display_name_it}
                                </option>
                            ))}
                        </select>
                    </label>

                    {loadingTrack && (
                        <div className="flex items-center gap-2 text-xs text-muted-foreground py-5">
                            <Loader2 size={14} className="animate-spin" />
                            Caricamento del sentiero…
                        </div>
                    )}

                    {!loadingTrack && track && (
                        <>
                            <div className="flex items-center justify-between text-[11px] mb-3">
                                <span className="text-amber">
                                    {track.hall.hall_name_it}
                                </span>
                                <span className="text-muted-foreground">
                                    {track.claimed_count}/{track.total_count} ottenuti
                                </span>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-5 gap-2">
                                {track.items.map((entry) => (
                                    <article
                                        key={entry.item.slug}
                                        data-testid={`class-hall-track-${entry.item.slug}`}
                                        className={`border rounded-sm p-3 flex flex-col ${
                                            entry.status === "claimed"
                                                ? "border-emerald-500/35 bg-emerald-500/5"
                                                : entry.status === "claimable"
                                                    ? "border-amber/55 bg-amber/5"
                                                    : "border-border bg-background/35"
                                        }`}
                                    >
                                        <div className="flex items-center justify-between gap-2 mb-2">
                                            <span className="text-[9px] tracking-widest text-muted-foreground">
                                                TAPPA {entry.order + 1}
                                            </span>
                                            {entry.status === "claimed" ? (
                                                <CheckCircle2 size={13} className="text-emerald-400" />
                                            ) : entry.status === "claimable" ? (
                                                <Gift size={13} className="text-amber" />
                                            ) : (
                                                <LockKeyhole size={13} className="text-muted-foreground" />
                                            )}
                                        </div>
                                        <h3 className="text-xs font-semibold mb-1">
                                            {entry.item.display_name_it}
                                        </h3>
                                        <p className="text-[10px] italic text-muted-foreground mb-2">
                                            “{entry.item.flavor_text_it}”
                                        </p>
                                        <p className="text-[10px] text-muted-foreground mb-2">
                                            {entry.item.acquisition_hint_it}
                                        </p>
                                        {entry.item.build_path_name_it && (
                                            <div className="mb-2 rounded border border-cyan-800/50 bg-cyan-950/20 p-2">
                                                <p className="text-[9px] tracking-widest text-cyan-300">
                                                    BUILD · {entry.item.build_path_name_it}
                                                </p>
                                                <p className="mt-1 text-[10px] text-cyan-100/70">
                                                    {entry.item.build_path_description_it}
                                                </p>
                                            </div>
                                        )}
                                        <p className="text-[10px] mt-auto mb-2">
                                            {requirementText(entry.requirement)}
                                        </p>
                                        {entry.status === "claimable" ? (
                                            <Button
                                                size="sm"
                                                onClick={() => claim(entry)}
                                                disabled={busySlug === entry.item.slug}
                                            >
                                                {busySlug === entry.item.slug && (
                                                    <Loader2 size={12} className="animate-spin mr-2" />
                                                )}
                                                Riscatta
                                            </Button>
                                        ) : (
                                            <span className="text-[9px] tracking-widest text-muted-foreground">
                                                {statusLabel[entry.status]}
                                            </span>
                                        )}
                                    </article>
                                ))}
                            </div>
                        </>
                    )}
                </>
            )}
        </section>
    );
}
