/* ROUND 11.2 TASK 8 — Public SEO page for stats.
 *
 * Route: /stats  (public, no auth required, no redirect)
 * Consumes GET /api/stats/catalog.
 * Groups stats in 3 buckets: Primarie (affects_pwr) / Derivata (PWR sintesi) /
 * Meta (level/xp/rarity/morale/stamina). Includes meta tags + 2x CTA.
 */
import { useEffect, useState } from "react";
import { api, formatApiError } from "@/lib/api";
import SeoHead from "@/components/SeoHead";
import PublicNavbar from "@/components/PublicNavbar";
import PublicCTA from "@/components/PublicCTA";


// Static grouping (stable since stats catalog is code-defined).
const PRIMARY_KEYS = new Set(["strength", "agility", "intellect", "endurance", "faith"]);
const SYNTHESIS_KEYS = new Set(["power_score"]);


function StatCard({ stat }) {
    return (
        <article
            data-testid={`public-stat-card-${stat.key}`}
            className="border border-border rounded-sm bg-card/60 p-4 hover:border-amber/40 transition-colors"
        >
            <div className="flex items-baseline justify-between gap-2">
                <h3 className="text-sm font-semibold tracking-tight">
                    {stat.display_name_it}
                </h3>
                <span className="font-mono text-[10px] text-muted-foreground">
                    {stat.key}
                </span>
            </div>
            <p className="text-[12px] text-foreground/85 mt-2 leading-relaxed">
                {stat.description_it}
            </p>
            <div className="mt-3 flex flex-wrap gap-2 text-[10px] text-muted-foreground">
                {stat.affects_pwr && (
                    <span className="border border-amber/40 text-amber px-1.5 py-0.5 rounded-sm">
                        Concorre a PWR
                    </span>
                )}
                {stat.implemented === false && (
                    <span className="border border-border px-1.5 py-0.5 rounded-sm">
                        documentazione, non ancora applicata nei calcoli
                    </span>
                )}
            </div>
        </article>
    );
}


function StatGroup({ id, title, items, accentClass }) {
    if (!items?.length) return null;
    return (
        <section
            id={id}
            data-testid={`public-stats-group-${id}`}
            className="mt-10 scroll-mt-24"
        >
            <h2 className={`text-xs tracking-[0.3em] mb-3 ${accentClass}`}>
                :: {title} <span className="text-muted-foreground">({items.length})</span>
            </h2>
            <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
                {items.map((s) => (
                    <StatCard key={s.key} stat={s} />
                ))}
            </div>
        </section>
    );
}


export default function StatsPublic() {
    const [state, setState] = useState({ data: null, loading: true, error: null });

    useEffect(() => {
        api.get("/stats/catalog")
            .then((r) => setState({ data: r.data?.stats || [], loading: false, error: null }))
            .catch((err) => setState({ data: [], loading: false, error: formatApiError(err) }));
    }, []);

    const stats = state.data || [];
    const primary = stats.filter((s) => PRIMARY_KEYS.has(s.key));
    const synthesis = stats.filter((s) => SYNTHESIS_KEYS.has(s.key));
    const meta = stats.filter(
        (s) => !PRIMARY_KEYS.has(s.key) && !SYNTHESIS_KEYS.has(s.key),
    );

    const description = `${stats.length || "Tutte le"} statistiche degli avventurieri in Orbus Online: Guild Master. Forza, Agilità, Intelletto, Resistenza, Fede e Power Score — come funzionano e quali influenzano il match-making delle spedizioni.`;

    return (
        <div className="min-h-screen bg-background text-foreground" data-testid="public-stats-page">
            <SeoHead
                title="Statistiche degli Avventurieri — Orbus Online: Guild Master"
                description={description}
                canonical="https://orbusonline.net/stats"
                ogUrl="https://orbusonline.net/stats"
                ogType="article"
            />
            <PublicNavbar />

            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8 sm:py-10">
                <header className="mb-8">
                    <div className="text-[10px] text-amber tracking-widest mb-2">
                        :: CATALOGO PUBBLICO
                    </div>
                    <h1
                        data-testid="public-stats-h1"
                        className="text-3xl sm:text-4xl lg:text-5xl font-semibold tracking-tight"
                    >
                        Statistiche degli Avventurieri
                    </h1>
                    <p className="text-sm sm:text-base text-muted-foreground mt-3 max-w-3xl">
                        Ogni avventuriero è descritto da un insieme di statistiche che
                        determinano combattimento, durata in spedizione, ranking pubblico.
                        Le statistiche <em>primarie</em> contribuiscono al Power Score (PWR);
                        le <em>meta</em> governano stamina, morale e progressione. Server-side
                        autoritativo — niente boost da denaro reale.
                    </p>
                </header>

                <PublicCTA
                    location="hero"
                    headline="Inizia la tua gilda. Costruisci il tuo Master."
                    subline="Gioco testuale, gratuito, no P2W. Strategia pura."
                />

                {state.loading && (
                    <p
                        data-testid="public-stats-loading"
                        className="mt-8 text-sm text-muted-foreground italic"
                    >
                        Caricamento del catalogo statistiche…
                    </p>
                )}
                {state.error && !state.loading && (
                    <p
                        data-testid="public-stats-error"
                        className="mt-8 text-sm text-red-400"
                    >
                        Impossibile caricare le statistiche. Riprova più tardi. ({state.error})
                    </p>
                )}
                {!state.loading && !state.error && (
                    <>
                        <StatGroup
                            id="primarie"
                            title="Primarie (concorrono a PWR)"
                            items={primary}
                            accentClass="text-amber"
                        />
                        <StatGroup
                            id="sintesi"
                            title="Sintesi (Power Score)"
                            items={synthesis}
                            accentClass="text-emerald-300"
                        />
                        <StatGroup
                            id="meta"
                            title="Meta & Progressione"
                            items={meta}
                            accentClass="text-foreground/80"
                        />
                        <p
                            data-testid="public-stats-total"
                            className="mt-10 text-[11px] text-muted-foreground"
                        >
                            {stats.length} statistiche documentate ·
                            {" "}fonte: <code>/api/stats/catalog</code> ·
                            {" "}aggiornate live dal server.
                        </p>
                    </>
                )}

                <div className="mt-12">
                    <PublicCTA
                        location="footer"
                        headline="Pronto a costruire la squadra perfetta?"
                        subline="Crea l'account in 30 secondi: nessuna carta, niente download."
                    />
                </div>

                <footer className="mt-10 text-center text-[10px] text-muted-foreground italic">
                    Orbus Online: Guild Master · MMO testuale di gestione gilde
                </footer>
            </main>
        </div>
    );
}
