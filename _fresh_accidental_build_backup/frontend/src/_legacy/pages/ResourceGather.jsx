// ROUND 16.3 Phase 4 — Send resource gathering mission (mobile-first).
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { api, formatApiError } from "../lib/api";
import AppHeader from "../components/AppHeader";

const TEAM_SIZE = 3;

export default function ResourceGather() {
    const nav = useNavigate();
    const [mine, setMine] = useState(null);
    const [adventurers, setAdventurers] = useState([]);
    const [pickedResource, setPickedResource] = useState(null);
    const [team, setTeam] = useState([]);
    const [loading, setLoading] = useState(true);
    const [busy, setBusy] = useState(false);

    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const [c, m, advs] = await Promise.all([
                    api.get("/resources/catalog"),
                    api.get("/resources/mine"),
                    api.get("/adventurers"),
                ]);
                if (cancelled) return;
                setMine({ ...m.data, catalog: c.data.resources || [] });
                const arr = advs.data.adventurers || advs.data || [];
                setAdventurers(Array.isArray(arr) ? arr : []);
                // Auto-pick the local resource
                const localRes = (c.data.resources || []).find(
                    (r) => r.continent_slug === m.data.current_continent,
                );
                setPickedResource(localRes || null);
            } catch (err) {
                toast.error(formatApiError(err));
            } finally {
                if (!cancelled) setLoading(false);
            }
        })();
        return () => { cancelled = true; };
    }, []);

    const toggleAdv = (id) => {
        setTeam((prev) => prev.includes(id)
            ? prev.filter((x) => x !== id)
            : prev.length < TEAM_SIZE ? [...prev, id] : prev);
    };

    const canSubmit = pickedResource && team.length === TEAM_SIZE && !busy;

    const submit = async () => {
        if (!canSubmit) return;
        setBusy(true);
        try {
            const { data } = await api.post("/resources/gather", {
                resource_slug: pickedResource.slug,
                adventurer_ids: team,
            });
            toast.success(`Missione avviata: ${pickedResource.name_it}`);
            nav(`/world/resource-missions`);
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setBusy(false);
        }
    };

    const idleAdvs = adventurers.filter((a) => {
        const s = a.status || "idle";
        return s === "idle" || s === "available" || !s;
    });

    return (
        <div className="min-h-screen bg-background text-foreground overflow-x-hidden">
            <AppHeader />
            <main className="max-w-3xl mx-auto px-4 py-6 pb-32 md:pb-8 font-mono">
                <div className="mb-4">
                    <Link to="/world/resources"
                          data-testid="resource-gather-back"
                          className="text-[11px] text-muted-foreground hover:text-amber tracking-widest">
                        ← Torna alle Risorse
                    </Link>
                </div>
                <header className="mb-4">
                    <h1 data-testid="resource-gather-title"
                        className="text-amber text-xl tracking-widest">
                        :: Missione di Raccolta
                    </h1>
                    <p className="text-[11px] text-muted-foreground mt-1">
                        Invia 3 avventurieri disponibili. Costo: 20 oro. Durata: 30 minuti.
                    </p>
                </header>

                {loading && (
                    <div className="text-[11px] text-muted-foreground italic">
                        :: Caricamento...
                    </div>
                )}

                {!loading && pickedResource && (
                    <section data-testid="resource-gather-picked"
                             className="border border-amber/40 bg-card/40 rounded-sm p-4 mb-4">
                        <div className="text-[11px] text-amber tracking-widest mb-2">
                            :: Risorsa
                        </div>
                        <div className="text-[14px] text-foreground">
                            {pickedResource.name_it}
                        </div>
                        <div className="text-[10px] text-muted-foreground mt-1">
                            {pickedResource.rarity} · drop base{" "}
                            {pickedResource.rarity === "epic" ? 3 : 5}%
                        </div>
                    </section>
                )}

                {!loading && !pickedResource && (
                    <div data-testid="resource-gather-no-resource"
                         className="border border-amber/40 bg-amber/5 rounded-sm p-4 mb-4 text-[12px] text-amber">
                        Nessuna risorsa raccoglibile: la tua gilda non è
                        ancorata a un continente.
                    </div>
                )}

                {!loading && pickedResource && (
                    <section>
                        <div className="text-[11px] text-amber tracking-widest mb-2">
                            :: Squadra ({team.length}/{TEAM_SIZE})
                        </div>
                        {idleAdvs.length < TEAM_SIZE ? (
                            <div className="text-[11px] text-red-400 italic mb-3">
                                Non hai abbastanza avventurieri disponibili
                                ({idleAdvs.length}/{TEAM_SIZE}).
                            </div>
                        ) : null}
                        <ul data-testid="resource-gather-adv-list"
                            className="space-y-2 mb-4">
                            {idleAdvs.map((a) => {
                                const picked = team.includes(a.id);
                                return (
                                    <li key={a.id}>
                                        <button
                                            type="button"
                                            onClick={() => toggleAdv(a.id)}
                                            data-testid={`resource-gather-adv-${a.id}`}
                                            disabled={!picked && team.length >= TEAM_SIZE}
                                            className={`w-full text-left border rounded-sm p-3 min-h-[44px] ${picked
                                                ? "border-amber/60 bg-amber/10"
                                                : "border-border/60 bg-card/40 hover:border-border"}`}
                                        >
                                            <div className="flex items-center justify-between">
                                                <span className="text-[12px] text-foreground">
                                                    {picked ? "✓ " : ""}{a.name}
                                                </span>
                                                <span className="text-[10px] text-muted-foreground">
                                                    Lv {a.level || 1}
                                                </span>
                                            </div>
                                        </button>
                                    </li>
                                );
                            })}
                        </ul>
                        <button
                            type="button"
                            onClick={submit}
                            disabled={!canSubmit}
                            data-testid="resource-gather-submit"
                            className="text-[11px] tracking-widest px-4 py-2.5 min-h-[44px] w-full md:w-auto border border-amber text-amber rounded-sm hover:bg-amber/10 font-bold disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                            {busy ? "…" : `Invia squadra (20 oro)`}
                        </button>
                    </section>
                )}
            </main>
        </div>
    );
}
