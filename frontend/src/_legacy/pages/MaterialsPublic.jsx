/* ROUND 11.2 EXT S3 Parte D — Public SEO page for materials.
 *
 * Route: /materials (public, no auth, no redirect)
 * Consumes GET /api/materials/catalog (server-side filtered: no equipment).
 * Anti-spoiler by design: only `item_type=material` slugs in MATERIAL_CATALOG.
 */
import { useEffect, useState } from "react";
import { api, formatApiError } from "@/lib/api";
import SeoHead from "@/components/SeoHead";
import PublicNavbar from "@/components/PublicNavbar";
import PublicCTA from "@/components/PublicCTA";


const RARITY_LABEL = {
    common: "Comune",
    uncommon: "Non comune",
    rare: "Raro",
    epic: "Epico",
    legendary: "Leggendario",
};

const RARITY_CLS = {
    common: "border-border text-foreground/85",
    uncommon: "border-emerald-500/40 text-emerald-300",
    rare: "border-blue-500/40 text-blue-300",
    epic: "border-violet-500/40 text-violet-300",
    legendary: "border-amber/60 text-amber",
};


function MaterialCard({ material }) {
    const rcls = RARITY_CLS[material.rarity] || RARITY_CLS.common;
    return (
        <article
            data-testid={`public-material-card-${material.slug}`}
            className="border border-border rounded-sm bg-card/60 p-4 hover:border-amber/40 transition-colors"
        >
            <div className="flex items-start justify-between gap-2">
                <h3 className="text-sm font-semibold tracking-tight">
                    {material.display_name_it}
                </h3>
                <span
                    className={`text-[10px] tracking-widest px-1.5 py-0.5 border rounded-sm whitespace-nowrap ${rcls}`}
                >
                    {RARITY_LABEL[material.rarity] || material.rarity}
                </span>
            </div>
            <p className="text-[12px] text-foreground/85 mt-2 leading-relaxed">
                {material.description_it}
            </p>
            {(material.sources || []).length > 0 && (
                <div className="mt-3">
                    <p className="text-[10px] tracking-widest text-amber/90 mb-1">:: DOVE SI TROVA</p>
                    <ul className="space-y-0.5 text-[11px] text-foreground/85">
                        {material.sources.map((s, i) => (
                            <li key={i}>
                                <strong className="text-foreground/95">{s.label_it}</strong>
                                {s.tier && <> · <span className="text-muted-foreground">Tier {s.tier}</span></>}
                                {s.note_it && <> · {s.note_it}</>}
                            </li>
                        ))}
                    </ul>
                </div>
            )}
            {(material.used_for_it || []).length > 0 && (
                <div className="mt-3">
                    <p className="text-[10px] tracking-widest text-foreground/60 mb-1">:: USI PRINCIPALI</p>
                    <ul className="space-y-0.5 text-[11px] text-foreground/80">
                        {material.used_for_it.map((u, i) => (
                            <li key={i}>· {u}</li>
                        ))}
                    </ul>
                </div>
            )}
        </article>
    );
}


export default function MaterialsPublic() {
    const [state, setState] = useState({ data: null, loading: true, error: null });

    useEffect(() => {
        api.get("/materials/catalog")
            .then((r) => setState({ data: r.data?.materials || [], loading: false, error: null }))
            .catch((err) => setState({ data: [], loading: false, error: formatApiError(err) }));
    }, []);

    const materials = state.data || [];
    const description = `${materials.length || "Tutti i"} materiali e risorse di Orbus Online: Guild Master. Frammenti, polveri arcane, reagenti — dove ottenerli e in quali ricette/potenziamenti si usano. Catalogo ufficiale lato server.`;

    return (
        <div className="min-h-screen bg-background text-foreground" data-testid="public-materials-page">
            <SeoHead
                title="Materiali e Risorse — Orbus Online: Guild Master"
                description={description}
                canonical="https://orbusonline.net/materials"
                ogUrl="https://orbusonline.net/materials"
                ogType="article"
            />
            <PublicNavbar />

            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8 sm:py-10">
                <header className="mb-8">
                    <div className="text-[10px] text-amber tracking-widest mb-2">
                        :: CATALOGO PUBBLICO
                    </div>
                    <h1
                        data-testid="public-materials-h1"
                        className="text-3xl sm:text-4xl lg:text-5xl font-semibold tracking-tight"
                    >
                        Materiali e Risorse
                    </h1>
                    <p className="text-sm sm:text-base text-muted-foreground mt-3 max-w-3xl">
                        I <strong>materiali</strong> sono le risorse non-equip usate per potenziare
                        le strutture del Territorio, craftare oggetti in Fucina e disincantare equip.
                        Si ottengono giocando: dungeon, raid, contratti, mercato NPC, disincanto.
                        Nessun materiale è acquistabile con denaro reale.
                    </p>
                </header>

                <PublicCTA
                    location="hero"
                    headline="Inizia la tua gilda. Costruisci il tuo Master."
                    subline="Gioco testuale, gratuito, no P2W. Strategia pura."
                />

                {state.loading && (
                    <p
                        data-testid="public-materials-loading"
                        className="mt-8 text-sm text-muted-foreground italic"
                    >
                        Caricamento del catalogo materiali…
                    </p>
                )}
                {state.error && !state.loading && (
                    <p
                        data-testid="public-materials-error"
                        className="mt-8 text-sm text-red-400"
                    >
                        Impossibile caricare i materiali. Riprova più tardi. ({state.error})
                    </p>
                )}
                {!state.loading && !state.error && (
                    <>
                        <section className="mt-10" data-testid="public-materials-grid">
                            <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
                                {materials.map((m) => (
                                    <MaterialCard key={m.slug} material={m} />
                                ))}
                            </div>
                        </section>
                        <p
                            data-testid="public-materials-total"
                            className="mt-10 text-[11px] text-muted-foreground"
                        >
                            {materials.length} materiali documentati ·
                            {" "}fonte: <code>/api/materials/catalog</code> ·
                            {" "}server-side filtered (no equipment, no test, no admin).
                        </p>
                    </>
                )}

                <div className="mt-12">
                    <PublicCTA
                        location="footer"
                        headline="Pronto a potenziare il tuo Territorio?"
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
