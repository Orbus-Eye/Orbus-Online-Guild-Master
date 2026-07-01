// ROUND 16.3 Phase 2 — Continent detail page (mobile-first).
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { toast } from "sonner";
import { api, formatApiError } from "../lib/api";
import AppHeader from "../components/AppHeader";

export default function WorldContinent() {
    const { slug } = useParams();
    const [continent, setContinent] = useState(null);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const [c, ov] = await Promise.all([
                    api.get(`/world/continents/${slug}`),
                    api.get("/world/overview").catch(() => ({ data: {} })),
                ]);
                if (!cancelled) {
                    setContinent(c.data.continent);
                    setStats(ov.data);
                }
            } catch (err) {
                if (!cancelled) toast.error(formatApiError(err));
            } finally {
                if (!cancelled) setLoading(false);
            }
        })();
        return () => { cancelled = true; };
    }, [slug]);

    const isCurrent = stats?.continent?.slug === slug;

    return (
        <div className="min-h-screen bg-background text-foreground overflow-x-hidden">
            <AppHeader />
            <main className="max-w-3xl mx-auto px-4 py-6 pb-32 md:pb-8 font-mono">
                <div className="mb-4">
                    <Link
                        to="/world"
                        data-testid="world-continent-back"
                        className="text-[11px] text-muted-foreground hover:text-amber tracking-widest"
                    >
                        ← Torna al Mondo
                    </Link>
                </div>

                {loading && (
                    <div data-testid="world-continent-loading"
                         className="text-[11px] text-muted-foreground italic">
                        :: Caricamento...
                    </div>
                )}

                {!loading && !continent && (
                    <div data-testid="world-continent-notfound"
                         className="border border-border/60 bg-card/40 rounded-sm p-4 text-[12px] text-muted-foreground">
                        Continente non trovato o inattivo.
                    </div>
                )}

                {!loading && continent && (
                    <>
                        <header className="mb-5">
                            <div className="flex items-baseline justify-between gap-2 flex-wrap">
                                <h1 data-testid="world-continent-name"
                                    className="text-amber text-2xl tracking-widest">
                                    {continent.name_it}
                                </h1>
                                <span className="text-[10px] text-muted-foreground uppercase">
                                    :: {continent.domain_it}
                                </span>
                            </div>
                            <div className="text-[11px] text-muted-foreground mt-1">
                                Divinità patrona: {continent.deity_it || "—"}
                            </div>
                        </header>

                        <section data-testid="world-continent-lore"
                                 className="border border-border/60 bg-card/40 rounded-sm p-4 mb-4">
                            <div className="text-[11px] text-amber tracking-widest mb-2">
                                :: Lore
                            </div>
                            <p className="text-[12px] text-muted-foreground leading-relaxed">
                                {continent.description_it}
                            </p>
                        </section>

                        {continent.theme_tags?.length ? (
                            <section data-testid="world-continent-tags"
                                     className="border border-border/60 bg-card/40 rounded-sm p-4 mb-4">
                                <div className="text-[11px] text-amber tracking-widest mb-2">
                                    :: Temi
                                </div>
                                <div className="flex flex-wrap gap-2">
                                    {continent.theme_tags.map((t) => (
                                        <span key={t}
                                              className="text-[10px] tracking-wide px-2 py-1 border border-border/60 text-muted-foreground rounded-sm">
                                            {t}
                                        </span>
                                    ))}
                                </div>
                            </section>
                        ) : null}

                        <section className="border border-border/60 bg-card/40 rounded-sm p-4 mb-4">
                            <div className="text-[11px] text-amber tracking-widest mb-2">
                                :: Stato
                            </div>
                            <div className="text-[11px] text-muted-foreground">
                                Il continente è{" "}
                                <span className={continent.is_active
                                    ? "text-green-400" : "text-red-400"}>
                                    {continent.is_active ? "attivo" : "inattivo"}
                                </span>.
                            </div>
                            {isCurrent && (
                                <div data-testid="world-continent-current-badge"
                                     className="mt-2 text-[11px] text-amber">
                                    ★ La tua gilda è ancorata qui.
                                </div>
                            )}
                        </section>

                        <div className="flex flex-col md:flex-row gap-2">
                            <Link
                                to="/world"
                                data-testid="world-continent-goback"
                                className="text-[11px] tracking-widest px-3 py-2.5 min-h-[44px] inline-flex items-center justify-center w-full md:w-auto border border-border/60 text-foreground/80 hover:border-amber/60 rounded-sm"
                            >
                                ← Mondo
                            </Link>
                            {isCurrent && (
                                <Link
                                    to="/world/neighbors"
                                    data-testid="world-continent-neighbors"
                                    className="text-[11px] tracking-widest px-3 py-2.5 min-h-[44px] inline-flex items-center justify-center w-full md:w-auto border border-amber text-amber rounded-sm hover:bg-amber/10 font-bold"
                                >
                                    Gilde vicine →
                                </Link>
                            )}
                        </div>
                    </>
                )}
            </main>
        </div>
    );
}
