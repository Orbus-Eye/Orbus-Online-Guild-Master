// ROUND 16.3 Phase 5B Iter2 — Arfus Forge hub (Tech Tree).
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { api, formatApiError } from "../lib/api";
import AppHeader from "../components/AppHeader";

const CATEGORY_GROUPS = [
    {
        title: "Combattimento",
        slugs: ["via_del_ferro", "mano_del_guaritore", "pelle_di_pietra",
                 "arte_del_contrasto", "spirito_del_guerriero", "perseveranza"],
    },
    {
        title: "Esplorazione & Sapienza",
        slugs: ["occhio_del_cacciatore", "saggezza_del_mentore",
                 "conoscenza_arcana"],
    },
    { title: "Forgia", slugs: ["via_del_forgiatore"] },
];

const APPLIES_LABEL = {
    expedition: "Spedizioni",
    raid: "Raid",
    world_boss: "World Boss",
    resource_gathering: "Gathering",
    legendary_forge: "Forgia Leggendaria",
};

function StatusBadge({ tech }) {
    if (tech.is_active_for_guild) {
        return <span className="text-xs px-2 py-1 rounded border border-emerald-500/60 text-emerald-300"
                      data-testid={`arfus-status-active-${tech.slug}`}>ATTIVA</span>;
    }
    if (tech.is_unlocked) {
        return <span className="text-xs px-2 py-1 rounded border border-sky-500/60 text-sky-300"
                      data-testid={`arfus-status-unlocked-${tech.slug}`}>SBLOCCATA</span>;
    }
    return <span className="text-xs px-2 py-1 rounded border border-slate-500/60 text-slate-400"
                  data-testid={`arfus-status-locked-${tech.slug}`}>BLOCCATA</span>;
}

function TechCard({ tech }) {
    return (
        <Link
            to={`/arfus-forge/tech/${tech.slug}`}
            className="block border border-slate-700 hover:border-amber-500/60 rounded p-4 bg-slate-900/40 transition min-h-[44px]"
            data-testid={`arfus-tech-card-${tech.slug}`}>
            <div className="flex items-start justify-between mb-2 gap-2">
                <div className="flex-1 min-w-0">
                    <div className="font-semibold text-slate-100 truncate"
                         data-testid={`arfus-tech-name-${tech.slug}`}>
                        {tech.name_it}
                    </div>
                    <div className="text-xs text-slate-500">Livello {tech.guild_level_required}+</div>
                </div>
                <StatusBadge tech={tech} />
            </div>
            <div className="flex items-baseline gap-2 mb-2">
                <span className="text-amber-300 text-lg font-mono"
                      data-testid={`arfus-tech-effect-${tech.slug}`}>
                    +{tech.effect_value}%
                </span>
                <span className="text-xs text-slate-400">(cap +{tech.category_cap}%)</span>
            </div>
            <div className="flex flex-wrap gap-1">
                {(tech.applies_to || []).map((a) => (
                    <span key={a}
                          className="text-[10px] uppercase tracking-wide px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                        {APPLIES_LABEL[a] || a}
                    </span>
                ))}
            </div>
        </Link>
    );
}

export default function ArfusForge() {
    const [state, setState] = useState({
        loading: true, access: false, guildLevel: null,
        technologies: [], activeCount: 0, maxActive: 5, err: null,
    });

    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const r = await api.get("/arfus-forge/catalog");
                if (!cancelled) setState({
                    loading: false,
                    access: r.data.access,
                    guildLevel: r.data.guild_level,
                    technologies: r.data.technologies || [],
                    activeCount: r.data.active_count || 0,
                    maxActive: r.data.max_active_techs || 5,
                    err: null,
                });
            } catch (err) {
                if (!cancelled) {
                    const msg = formatApiError(err);
                    toast.error(msg);
                    setState((s) => ({ ...s, loading: false, err: msg }));
                }
            }
        })();
        return () => { cancelled = true; };
    }, []);

    const bySlug = Object.fromEntries((state.technologies || []).map((t) => [t.slug, t]));

    return (
        <div className="min-h-screen bg-background text-foreground overflow-x-hidden">
            <AppHeader />
            <main className="max-w-4xl mx-auto px-4 py-6 pb-32 md:pb-8 font-mono"
                data-testid="arfus-forge-page">
                <div className="mb-6">
                    <h1 className="text-3xl md:text-4xl font-bold text-amber-300 mb-2"
                        data-testid="arfus-forge-title">
                        Forgia di Arfus
                    </h1>
                    <p className="text-sm text-muted-foreground">
                        Tecnologie passive che potenziano tutta la gilda.
                        Max 5 slot attivi, no stack same-category.
                    </p>
                </div>

                {state.loading && (
                    <div className="text-center text-muted-foreground py-16"
                        data-testid="arfus-forge-loading">Caricamento…</div>
                )}

                {!state.loading && !state.access && (
                    <div className="border border-amber-700/50 rounded p-6 bg-amber-950/20 text-center"
                        data-testid="arfus-forge-blocked">
                        <div className="text-lg font-semibold text-amber-300 mb-3">
                            Accesso bloccato
                        </div>
                        <p className="text-sm text-slate-300 mb-4">
                            Raggiungi <b>Livello Gilda 6</b> per accedere alla Forgia di Arfus.
                            {state.guildLevel != null && (
                                <span className="block mt-1 text-slate-400">
                                    Attualmente sei al livello {state.guildLevel}.
                                </span>
                            )}
                        </p>
                        <Link to="/expeditions"
                              className="inline-block min-h-[44px] w-full md:w-auto px-6 py-3 rounded bg-amber-500 hover:bg-amber-400 text-slate-900 font-semibold transition"
                              data-testid="arfus-goto-expeditions">
                            Vai alle Missioni
                        </Link>
                    </div>
                )}

                {!state.loading && state.access && (
                    <>
                        <div className="mb-6 border border-slate-700 rounded p-4 bg-slate-900/40"
                             data-testid="arfus-slot-summary">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm text-slate-300">Slot Attivi</span>
                                <span className="text-lg font-semibold text-amber-300"
                                      data-testid="arfus-slot-count">
                                    {state.activeCount} / {state.maxActive}
                                </span>
                            </div>
                            <div className="h-2 bg-slate-800 rounded overflow-hidden">
                                <div
                                    className="h-full bg-amber-500 transition-all"
                                    style={{ width: `${Math.min(100, (state.activeCount / state.maxActive) * 100)}%` }}
                                    data-testid="arfus-slot-progress" />
                            </div>
                            <div className="mt-4 flex flex-col md:flex-row gap-2">
                                <Link to="/arfus-forge/research"
                                      className="inline-flex items-center justify-center min-h-[44px] w-full md:w-auto px-4 py-2 rounded border border-sky-500/60 text-sky-300 hover:bg-sky-950/40 text-sm"
                                      data-testid="arfus-goto-research">
                                    Ricerche
                                </Link>
                                <Link to="/arfus-forge/active"
                                      className="inline-flex items-center justify-center min-h-[44px] w-full md:w-auto px-4 py-2 rounded border border-emerald-500/60 text-emerald-300 hover:bg-emerald-950/40 text-sm"
                                      data-testid="arfus-goto-active">
                                    Gestisci slot attivi
                                </Link>
                            </div>
                        </div>

                        {CATEGORY_GROUPS.map((g) => (
                            <section key={g.title} className="mb-6"
                                     data-testid={`arfus-group-${g.title}`}>
                                <h2 className="text-lg text-slate-200 mb-3 border-b border-slate-800 pb-2">
                                    {g.title}
                                </h2>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                    {g.slugs.map((slug) => {
                                        const t = bySlug[slug];
                                        if (!t) return null;
                                        return <TechCard key={slug} tech={t} />;
                                    })}
                                </div>
                            </section>
                        ))}
                    </>
                )}
            </main>
        </div>
    );
}
