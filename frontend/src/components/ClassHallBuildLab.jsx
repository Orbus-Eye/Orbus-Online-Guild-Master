import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { CheckCircle2, FlaskConical, Loader2, RefreshCw } from "lucide-react";
import { toast } from "sonner";

import { api, formatApiError } from "../lib/api";
import { Button } from "./ui/button";


export default function ClassHallBuildLab() {
    const [adventurers, setAdventurers] = useState([]);
    const [selectedId, setSelectedId] = useState("");
    const [lab, setLab] = useState(null);
    const [loading, setLoading] = useState(true);

    const loadRoster = useCallback(async () => {
        setLoading(true);
        try {
            const response = await api.get("/adventurers");
            const assigned = (response.data?.adventurers || []).filter(
                (adventurer) => adventurer.class_hall_id,
            );
            setAdventurers(assigned);
            setSelectedId((current) => (
                assigned.some((adventurer) => adventurer.id === current)
                    ? current
                    : (assigned[0]?.id || "")
            ));
            if (!assigned.length) setLab(null);
        } catch (error) {
            toast.error(formatApiError(error));
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { loadRoster(); }, [loadRoster]);

    useEffect(() => {
        const selected = adventurers.find(
            (adventurer) => adventurer.id === selectedId,
        );
        if (!selected?.class_hall_id) return undefined;
        let cancelled = false;
        setLoading(true);
        api.get(`/class-halls/${selected.class_hall_id}/build-lab`, {
            params: { adventurer_id: selected.id },
        }).then((response) => {
            if (!cancelled) setLab(response.data);
        }).catch((error) => {
            if (!cancelled) {
                setLab(null);
                toast.error(formatApiError(error));
            }
        }).finally(() => {
            if (!cancelled) setLoading(false);
        });
        return () => { cancelled = true; };
    }, [adventurers, selectedId]);

    return (
        <section className="mb-5 rounded-sm border border-cyan-800/50 bg-card p-4"
                 data-testid="class-hall-build-lab">
            <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
                <div>
                    <p className="mb-1 text-[10px] tracking-[0.2em] text-cyan-300">
                        :: LABORATORIO BUILD
                    </p>
                    <h2 className="flex items-center gap-2 text-base font-semibold">
                        <FlaskConical size={16} />
                        Isola un sentiero prima della prova
                    </h2>
                    <p className="mt-1 max-w-2xl text-[11px] text-muted-foreground">
                        Ogni campione deve appartenere a una sola build. Il laboratorio
                        segnala l'item necessario e gli equipaggiamenti concorrenti.
                    </p>
                </div>
                <Button size="sm" variant="outline" onClick={loadRoster}>
                    <RefreshCw size={13} className="mr-2" />
                    Aggiorna
                </Button>
            </div>

            {adventurers.length > 0 && (
                <label className="mb-3 block text-[10px] tracking-widest text-muted-foreground">
                    AVVENTURIERO
                    <select value={selectedId}
                            onChange={(event) => setSelectedId(event.target.value)}
                            className="mt-1 block h-9 w-full bg-background px-2 text-xs text-foreground sm:w-80">
                        {adventurers.map((adventurer) => (
                            <option key={adventurer.id} value={adventurer.id}>
                                {adventurer.name} · {adventurer.class_display_name_it}
                            </option>
                        ))}
                    </select>
                </label>
            )}

            {loading && (
                <div className="flex items-center gap-2 py-5 text-xs text-muted-foreground">
                    <Loader2 size={14} className="animate-spin" />
                    Analisi dell'equipaggiamento…
                </div>
            )}

            {!loading && lab && (
                <>
                    <div className="mb-3 flex flex-wrap items-center justify-between gap-2 text-xs">
                        <span className="text-cyan-300">
                            {lab.hall.class_name_it} · Wave {lab.hall.wave}
                        </span>
                        <span className="text-muted-foreground">
                            Build corrente: {lab.current_build?.resonance_active
                                ? lab.current_build.name_it
                                : "nessuna risonanza"}
                        </span>
                    </div>
                    <div className="grid gap-3 md:grid-cols-3">
                        {lab.paths.map((path) => (
                            <article key={path.build_id}
                                     className={`rounded-sm border p-3 ${
                                         path.isolated_ready
                                             ? "border-emerald-600/60 bg-emerald-950/20"
                                             : "border-border bg-background/35"
                                     }`}>
                                <div className="flex items-start justify-between gap-2">
                                    <div>
                                        <div className="text-sm font-semibold">
                                            {path.build_name_it}
                                        </div>
                                        <div className="text-[10px] text-cyan-300">
                                            {path.path_item.display_name_it}
                                        </div>
                                    </div>
                                    {path.isolated_ready && (
                                        <CheckCircle2 size={16} className="text-emerald-400" />
                                    )}
                                </div>
                                <p className="mt-2 text-[11px] text-muted-foreground">
                                    {path.description_it}
                                </p>
                                <div className="mt-2 text-[10px] text-muted-foreground">
                                    {path.owned ? "Posseduto" : "Da ottenere"} ·{" "}
                                    {path.equipped ? "equipaggiato" : "non equipaggiato"}
                                </div>
                                {path.competing_equipped_items.length > 0 && (
                                    <div className="mt-2 rounded bg-amber-950/30 p-2 text-[10px] text-amber-200">
                                        Rimuovi: {path.competing_equipped_items
                                            .map((item) => item.item_name_it)
                                            .join(", ")}
                                    </div>
                                )}
                                <p className="mt-2 text-[11px] text-foreground/80">
                                    {path.next_action_it}
                                </p>
                            </article>
                        ))}
                    </div>
                    <div className="mt-3">
                        <Button asChild size="sm">
                            <Link to={lab.equipment_url}>Apri equipaggiamento</Link>
                        </Button>
                    </div>
                </>
            )}
        </section>
    );
}
