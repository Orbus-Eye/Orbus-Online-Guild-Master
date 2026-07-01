// ROUND 16.3 Phase 4 — Continent Leaderboards V0.
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { toast } from "sonner";
import { api, formatApiError } from "../lib/api";
import AppHeader from "../components/AppHeader";

const TYPES = [
    { id: "resource_gathering_count", label: "Risorse raccolte (7gg)" },
    { id: "site_income_total", label: "Oro incarichi di sede (7gg)" },
];

export default function ContinentLeaderboards() {
    const { slug } = useParams();
    const [continentSlug, setContinentSlug] = useState(slug || null);
    const [ltype, setLtype] = useState("resource_gathering_count");
    const [snap, setSnap] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // If no slug in URL, ask backend for the guild's current continent
        let cancelled = false;
        (async () => {
            if (!continentSlug) {
                try {
                    const { data } = await api.get("/world/overview");
                    if (!cancelled && data.continent?.slug) {
                        setContinentSlug(data.continent.slug);
                    } else if (!cancelled) {
                        setLoading(false);
                    }
                } catch {
                    if (!cancelled) setLoading(false);
                }
            }
        })();
        return () => { cancelled = true; };
    }, [continentSlug]);

    useEffect(() => {
        if (!continentSlug) return;
        let cancelled = false;
        setLoading(true);
        (async () => {
            try {
                const { data } = await api.get(
                    `/continent-leaderboards/${continentSlug}/${ltype}`,
                );
                if (!cancelled) setSnap(data.snapshot);
            } catch (err) {
                if (!cancelled) toast.error(formatApiError(err));
            } finally {
                if (!cancelled) setLoading(false);
            }
        })();
        return () => { cancelled = true; };
    }, [continentSlug, ltype]);

    return (
        <div className="min-h-screen bg-background text-foreground overflow-x-hidden">
            <AppHeader />
            <main className="max-w-3xl mx-auto px-4 py-6 pb-32 md:pb-8 font-mono">
                <div className="mb-4">
                    <Link to="/world"
                          data-testid="lb-back"
                          className="text-[11px] text-muted-foreground hover:text-amber tracking-widest">
                        ← Torna al Mondo
                    </Link>
                </div>
                <header className="mb-4">
                    <h1 data-testid="lb-title"
                        className="text-amber text-xl tracking-widest">
                        :: Classifiche Continentali
                    </h1>
                    <p className="text-[11px] text-muted-foreground mt-1">
                        Top 20 gilde del tuo continente. Puramente informativo.
                    </p>
                </header>

                {!continentSlug && !loading && (
                    <div data-testid="lb-no-continent"
                         className="border border-amber/40 bg-amber/5 rounded-sm p-4 text-[12px] text-amber">
                        Devi essere ancorato a un continente per vedere le classifiche.
                    </div>
                )}

                {continentSlug && (
                    <>
                        <div className="mb-4 flex gap-2 flex-wrap">
                            {TYPES.map((t) => (
                                <button
                                    key={t.id}
                                    type="button"
                                    onClick={() => setLtype(t.id)}
                                    data-testid={`lb-type-${t.id}`}
                                    className={`text-[10px] tracking-widest px-3 py-2 min-h-[44px] border rounded-sm ${ltype === t.id
                                        ? "border-amber text-amber bg-amber/10 font-bold"
                                        : "border-border/60 text-muted-foreground"}`}
                                >
                                    {t.label}
                                </button>
                            ))}
                        </div>
                        <div className="text-[11px] text-muted-foreground mb-2">
                            Continente: <span className="text-foreground">{continentSlug}</span>
                            {snap?.computed_at && (
                                <span> · calcolato {new Date(snap.computed_at).toLocaleString("it")}</span>
                            )}
                        </div>
                        {loading ? (
                            <div className="text-[11px] text-muted-foreground italic">
                                :: Caricamento...
                            </div>
                        ) : (snap?.entries || []).length === 0 ? (
                            <div data-testid="lb-empty"
                                 className="border border-border/60 bg-card/40 rounded-sm p-4 text-[12px] text-muted-foreground">
                                Nessuna gilda in classifica.
                            </div>
                        ) : (
                            <ol data-testid="lb-list" className="space-y-2">
                                {snap.entries.map((e) => (
                                    <li key={e.guild_id}
                                        data-testid={`lb-entry-${e.rank}`}
                                        className="border border-border/60 bg-card/40 rounded-sm p-3 flex items-center justify-between">
                                        <div className="flex items-center gap-3">
                                            <span className="text-[11px] text-amber w-6">
                                                #{e.rank}
                                            </span>
                                            <span className="text-[13px] text-foreground">
                                                {e.guild_name}
                                            </span>
                                        </div>
                                        <span className="text-[12px] text-amber">
                                            {e.score}
                                        </span>
                                    </li>
                                ))}
                            </ol>
                        )}
                    </>
                )}
            </main>
        </div>
    );
}
