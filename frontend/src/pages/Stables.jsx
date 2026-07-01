// ROUND 16.3 Phase 8 V1 Iter2 — Stalle & Cavalcature main page.
// 3 sections: Le Mie Cavalcature | Catalogo Completo | Rotte Narrative.
// Purely cosmetic feature — see anti-P2W disclaimer in the footer.
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { api, formatApiError } from "../lib/api";
import AppHeader from "../components/AppHeader";
import MountCard from "../components/MountCard";
import NarrativeRouteCard from "../components/NarrativeRouteCard";

const TABS = [
    { key: "mine", label: "Le Mie Cavalcature" },
    { key: "catalog", label: "Catalogo Completo" },
    { key: "routes", label: "Rotte Narrative" },
];

export default function Stables() {
    const [tab, setTab] = useState("mine");
    const [loading, setLoading] = useState(true);
    const [busy, setBusy] = useState(false);
    const [catalog, setCatalog] = useState({ mounts: [], total: 0, active_mount_slug: null });
    const [mine, setMine] = useState({ owned: [], active_mount: null, total_owned: 0 });
    const [routes, setRoutes] = useState({ routes: [], total: 0 });

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const [cat, minr, rts] = await Promise.all([
                api.get("/stables/catalog"),
                api.get("/stables/mine"),
                api.get("/stables/narrative-routes"),
            ]);
            setCatalog(cat.data || {});
            setMine(minr.data || {});
            setRoutes(rts.data || {});
        } catch (e) {
            toast.error(formatApiError(e));
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { load(); }, [load]);

    const alreadyClaimedStarter = (mine.owned || []).some(
        (m) => m.slug === "ronzino-di-strada",
    );

    const claimStarter = async () => {
        setBusy(true);
        try {
            await api.post("/stables/quest/starter/claim");
            toast.success("Hai ricevuto il tuo Ronzino di Strada. Buon viaggio!");
            await load();
        } catch (e) {
            toast.error(formatApiError(e));
        } finally {
            setBusy(false);
        }
    };

    const activateMount = async (slug) => {
        setBusy(true);
        try {
            await api.post("/stables/set-active", { mount_slug: slug });
            toast.success(`Cavalcatura attivata.`);
            await load();
        } catch (e) {
            toast.error(formatApiError(e));
        } finally {
            setBusy(false);
        }
    };

    const deactivateMount = async () => {
        setBusy(true);
        try {
            await api.post("/stables/set-active", { mount_slug: null });
            toast.success("Cavalcatura disattivata. Ora viaggi a piedi.");
            await load();
        } catch (e) {
            toast.error(formatApiError(e));
        } finally {
            setBusy(false);
        }
    };

    const travelRoute = async (slug) => {
        setBusy(true);
        try {
            const r = await api.post(`/stables/narrative-routes/${slug}/travel`);
            const rname = r.data?.reward_name_it || r.data?.reward_slug || "una ricompensa cosmetica";
            toast.success(`Hai percorso la rotta. Ricompensa: ${rname}.`);
            await load();
        } catch (e) {
            toast.error(formatApiError(e));
        } finally {
            setBusy(false);
        }
    };

    const active = mine.active_mount;

    return (
        <div className="min-h-screen bg-zinc-950 text-zinc-100 pb-32 md:pb-8">
            <AppHeader />
            <main className="max-w-5xl mx-auto px-4 pt-6">
                {/* Header */}
                <div className="mb-6">
                    <div className="flex items-baseline gap-3 flex-wrap">
                        <h1 className="text-2xl md:text-3xl font-semibold tracking-tight" data-testid="stables-title">
                            Stalla della Gilda
                        </h1>
                        <span className="text-[10px] px-1.5 py-0.5 rounded uppercase tracking-wider bg-green-500/15 text-green-400 border border-green-500/40 font-mono">
                            NEW
                        </span>
                    </div>
                    <div className="text-sm text-zinc-400 mt-1">
                        <span className="font-mono text-zinc-300" data-testid="stables-count">
                            {mine.total_owned}/{catalog.total || 9}
                        </span>
                        {" "}cavalcature possedute
                        {active ? (
                            <> · Attualmente in sella a{" "}
                                <span className="text-green-400">{active.name_it}</span></>
                        ) : (
                            <> · Nessuna cavalcatura attiva</>
                        )}
                    </div>
                </div>

                {/* Starter claim CTA */}
                {!alreadyClaimedStarter && (
                    <div className="mb-6 rounded-lg border border-green-800/50 bg-green-950/20 p-4"
                         data-testid="stables-starter-cta">
                        <div className="flex items-start gap-3 flex-wrap md:flex-nowrap">
                            <div className="text-3xl">🐎</div>
                            <div className="flex-1 min-w-0">
                                <div className="text-sm font-semibold text-zinc-100">
                                    Rivendica il Tuo Primo Cavallo
                                </div>
                                <div className="text-xs text-zinc-400 mt-1">
                                    Il Ronzino di Strada è un compagno modesto ma leale, disponibile fin dal
                                    primo giorno di ogni gilda. Solo cosmetico — nessun bonus di gioco.
                                </div>
                            </div>
                            <button
                                type="button"
                                onClick={claimStarter}
                                disabled={busy}
                                data-testid="stables-claim-starter-btn"
                                className="w-full md:w-auto text-sm font-medium px-4 py-2 rounded bg-green-600 hover:bg-green-500 text-white disabled:opacity-50 min-h-[44px] md:min-h-0"
                            >
                                Rivendica il Ronzino
                            </button>
                        </div>
                    </div>
                )}

                {/* Tabs */}
                <div className="mb-4 border-b border-zinc-800 flex gap-1 overflow-x-auto"
                     data-testid="stables-tabs">
                    {TABS.map((t) => (
                        <button
                            key={t.key}
                            type="button"
                            onClick={() => setTab(t.key)}
                            data-testid={`stables-tab-${t.key}`}
                            className={`text-xs md:text-sm font-medium px-3 py-2 whitespace-nowrap border-b-2 transition min-h-[44px] md:min-h-0 ${tab === t.key
                                ? "border-green-500 text-green-400"
                                : "border-transparent text-zinc-500 hover:text-zinc-300"}`}
                        >
                            {t.label}
                        </button>
                    ))}
                </div>

                {loading ? (
                    <div className="text-sm text-zinc-500 py-8 text-center">Caricamento…</div>
                ) : (
                    <>
                        {tab === "mine" && (
                            <div className="grid gap-3 md:grid-cols-2" data-testid="stables-mine-list">
                                {mine.owned?.length ? (
                                    mine.owned.map((m) => (
                                        <MountCard
                                            key={m.slug}
                                            mount={{ ...m, is_owned: true }}
                                            busy={busy}
                                            onActivate={activateMount}
                                            onDeactivate={deactivateMount}
                                        />
                                    ))
                                ) : (
                                    <div className="text-sm text-zinc-500 col-span-2 py-8 text-center border border-dashed border-zinc-800 rounded">
                                        Non possiedi ancora nessuna cavalcatura. Rivendica il Ronzino
                                        oppure ottieni cavalcature dai World Boss, Imprese e Crafting.
                                    </div>
                                )}
                            </div>
                        )}
                        {tab === "catalog" && (
                            <div className="grid gap-3 md:grid-cols-2" data-testid="stables-catalog-list">
                                {catalog.mounts?.map((m) => (
                                    <MountCard
                                        key={m.slug}
                                        mount={m}
                                        busy={busy}
                                        onActivate={activateMount}
                                        onDeactivate={deactivateMount}
                                    />
                                ))}
                            </div>
                        )}
                        {tab === "routes" && (
                            <div className="grid gap-3" data-testid="stables-routes-list">
                                {routes.routes?.map((r) => (
                                    <NarrativeRouteCard
                                        key={r.slug}
                                        route={r}
                                        busy={busy}
                                        onTravel={travelRoute}
                                    />
                                ))}
                            </div>
                        )}
                    </>
                )}

                {/* Anti-P2W disclaimer (visible full) */}
                <section
                    className="mt-8 rounded-lg border border-emerald-800/40 bg-emerald-950/10 p-4"
                    data-testid="stables-antip2w-disclaimer"
                >
                    <div className="text-xs font-semibold uppercase tracking-wider text-emerald-400 mb-2">
                        Trasparenza Anti-Pay-to-Win
                    </div>
                    <div className="text-xs text-zinc-400 leading-relaxed space-y-1">
                        <p>
                            Le cavalcature e le rotte narrative sono <strong className="text-zinc-200">
                            puramente decorative</strong>.
                        </p>
                        <p>
                            Nessuna cavalcatura modifica potenza, oro, XP, drop rate, reputazione,
                            velocità di viaggio o qualunque parametro competitivo. Le ricompense delle
                            rotte narrative sono <strong className="text-zinc-200">esclusivamente</strong> badge
                            cosmetici, titoli onorifici o frammenti di lore.
                        </p>
                        <p>
                            Tutti i contenuti della Stalla sono <strong className="text-zinc-200">
                            free-to-earn</strong>: non esiste alcuna via di acquisto con valuta reale.
                        </p>
                    </div>
                </section>
            </main>
        </div>
    );
}
