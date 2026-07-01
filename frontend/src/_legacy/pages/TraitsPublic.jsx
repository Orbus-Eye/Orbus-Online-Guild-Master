/* ROUND 11.2 TASK 8 — Public SEO page for traits.
 *
 * Route: /traits  (public, no auth required, no redirect)
 * Consumes GET /api/traits/catalog (same endpoint as Guide).
 * Groups traits in 3 buckets: Positivi / Negativi / Misti.
 * Includes meta tags + Open Graph + canonical + 2x CTA blocks.
 */
import { useEffect, useState } from "react";
import { api, formatApiError } from "@/lib/api";
import SeoHead from "@/components/SeoHead";
import PublicNavbar from "@/components/PublicNavbar";
import PublicCTA from "@/components/PublicCTA";


const POLARITY_LABEL = {
    positive: { label: "Positivo", cls: "text-emerald-300 border-emerald-500/40" },
    negative: { label: "Negativo", cls: "text-red-400 border-red-500/40" },
    mixed: { label: "Misto", cls: "text-amber border-amber/50" },
};

const RARITY_LABEL = {
    common: "Comune",
    uncommon: "Non comune",
    rare: "Raro",
    epic: "Epico",
    legendary: "Leggendario",
};


function TraitCard({ trait }) {
    const pol = POLARITY_LABEL[trait.polarity] || POLARITY_LABEL.positive;
    return (
        <article
            data-testid={`public-trait-card-${trait.id}`}
            className="border border-border rounded-sm bg-card/60 p-4 hover:border-amber/40 transition-colors"
        >
            <div className="flex items-start justify-between gap-2">
                <h3 className="text-sm font-semibold tracking-tight">
                    {trait.display_name_it}
                </h3>
                <span
                    className={`text-[10px] tracking-widest px-1.5 py-0.5 border rounded-sm whitespace-nowrap ${pol.cls}`}
                >
                    {pol.label}
                </span>
            </div>
            <p className="text-[12px] text-foreground/85 mt-2 leading-relaxed">
                {trait.description_it}
            </p>
            <p className="mt-3 text-[10px] text-muted-foreground tracking-wider">
                {RARITY_LABEL[trait.rarity] || trait.rarity}
                {trait.affected_stat && (
                    <>
                        {" · "}
                        <span className="text-foreground/80">{trait.affected_stat}</span>
                    </>
                )}
            </p>
        </article>
    );
}


function TraitGroup({ id, title, items, accentClass }) {
    if (!items?.length) return null;
    return (
        <section
            id={id}
            data-testid={`public-traits-group-${id}`}
            className="mt-10 scroll-mt-24"
        >
            <h2 className={`text-xs tracking-[0.3em] mb-3 ${accentClass}`}>
                :: {title} <span className="text-muted-foreground">({items.length})</span>
            </h2>
            <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
                {items.map((t) => (
                    <TraitCard key={t.id} trait={t} />
                ))}
            </div>
        </section>
    );
}


export default function TraitsPublic() {
    const [state, setState] = useState({ data: null, loading: true, error: null });

    useEffect(() => {
        api.get("/traits/catalog")
            .then((r) => setState({ data: r.data?.traits || [], loading: false, error: null }))
            .catch((err) => setState({ data: [], loading: false, error: formatApiError(err) }));
    }, []);

    const traits = state.data || [];
    const positives = traits.filter((t) => t.polarity === "positive");
    const negatives = traits.filter((t) => t.polarity === "negative");
    const mixed = traits.filter((t) => t.polarity === "mixed");

    const description = `${traits.length || "Tutti i"} tratti degli avventurieri in Orbus Online: Guild Master. Scopri quali bonus e malus modificano stat, esperienza e fortuna del tuo roster — dati ufficiali del catalogo gilda.`;

    return (
        <div className="min-h-screen bg-background text-foreground" data-testid="public-traits-page">
            <SeoHead
                title="Tratti degli Avventurieri — Orbus Online: Guild Master"
                description={description}
                canonical="https://orbusonline.net/traits"
                ogUrl="https://orbusonline.net/traits"
                ogType="article"
            />
            <PublicNavbar />

            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8 sm:py-10">
                {/* Hero */}
                <header className="mb-8">
                    <div className="text-[10px] text-amber tracking-widest mb-2">
                        :: CATALOGO PUBBLICO
                    </div>
                    <h1
                        data-testid="public-traits-h1"
                        className="text-3xl sm:text-4xl lg:text-5xl font-semibold tracking-tight"
                    >
                        Tratti degli Avventurieri
                    </h1>
                    <p className="text-sm sm:text-base text-muted-foreground mt-3 max-w-3xl">
                        Ogni avventuriero che recluti porta con sé 0-3 tratti permanenti che
                        modificano stat, comportamento e bonus. Qui sotto trovi l&apos;elenco
                        completo: positivi, negativi e doppio-taglio (misti). Nessun tratto
                        è acquistabile con denaro reale: il drop è interamente affidato alla
                        casualità server-side gated da pesi pubblici.
                    </p>
                </header>

                <PublicCTA
                    location="hero"
                    headline="Inizia la tua gilda. Costruisci il tuo Master."
                    subline="Gioco testuale, gratuito, no P2W. Strategia pura."
                />

                {/* Loading / error / data */}
                {state.loading && (
                    <p
                        data-testid="public-traits-loading"
                        className="mt-8 text-sm text-muted-foreground italic"
                    >
                        Caricamento del catalogo tratti…
                    </p>
                )}
                {state.error && !state.loading && (
                    <p
                        data-testid="public-traits-error"
                        className="mt-8 text-sm text-red-400"
                    >
                        Impossibile caricare i tratti. Riprova più tardi. ({state.error})
                    </p>
                )}
                {!state.loading && !state.error && (
                    <>
                        <TraitGroup
                            id="positivi"
                            title="Positivi"
                            items={positives}
                            accentClass="text-emerald-300"
                        />
                        <TraitGroup
                            id="misti"
                            title="Doppio taglio (misti)"
                            items={mixed}
                            accentClass="text-amber"
                        />
                        <TraitGroup
                            id="negativi"
                            title="Negativi"
                            items={negatives}
                            accentClass="text-red-400"
                        />
                        <p
                            data-testid="public-traits-total"
                            className="mt-10 text-[11px] text-muted-foreground"
                        >
                            {traits.length} tratti pubblicati ·
                            {" "}fonte: <code>/api/traits/catalog</code> ·
                            {" "}aggiornati live dal server.
                        </p>
                    </>
                )}

                {/* Footer CTA */}
                <div className="mt-12">
                    <PublicCTA
                        location="footer"
                        headline="Pronto a reclutare il tuo primo avventuriero?"
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
