// ROUND 16.3 Phase 5B Iter2 — Arfus Active slots management.
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { api, formatApiError } from "../lib/api";
import AppHeader from "../components/AppHeader";

const CAPS = {
    combat_damage: 30, combat_healing: 30, combat_defense: 30,
    counter_effectiveness: 30, exploration_luck: 15, team_morale: 30,
    leader_experience: 20, arcane_knowledge: 30, iron_will: 30,
    forge_efficiency: 10,
};

export default function ArfusActive() {
    const [state, setState] = useState({
        loading: true, technologies: [], activeCount: 0, maxActive: 5,
        bonuses: {}, catalog: {}, err: null, toggling: null,
    });

    const load = useCallback(async () => {
        try {
            const [mine, cat] = await Promise.all([
                api.get("/arfus-forge/technologies/mine"),
                api.get("/arfus-forge/catalog"),
            ]);
            const catalog = Object.fromEntries(
                (cat.data.technologies || []).map((t) => [t.slug, t]));
            setState((s) => ({
                ...s, loading: false,
                technologies: mine.data.technologies || [],
                activeCount: mine.data.active_count || 0,
                maxActive: mine.data.max_active_techs || 5,
                bonuses: mine.data.active_bonuses_by_category || {},
                catalog, err: null,
            }));
        } catch (err) {
            const msg = formatApiError(err);
            toast.error(msg);
            setState((s) => ({ ...s, loading: false, err: msg }));
        }
    }, []);

    useEffect(() => { load(); }, [load]);

    const toggle = useCallback(async (slug) => {
        setState((s) => ({ ...s, toggling: slug }));
        try {
            await api.post(`/arfus-forge/technologies/${slug}/toggle`);
            toast.success("Slot aggiornato");
            await load();
        } catch (err) {
            const msg = formatApiError(err);
            if (msg.includes("max_active_reached")) {
                toast.error("Massimo 5 slot attivi. Disattiva prima un'altra tech.");
            } else if (msg.includes("stack_same_category")) {
                toast.error("Non puoi attivare due tech della stessa categoria.");
            } else {
                toast.error(msg);
            }
        } finally {
            setState((s) => ({ ...s, toggling: null }));
        }
    }, [load]);

    return (
        <div className="min-h-screen bg-background text-foreground overflow-x-hidden">
            <AppHeader />
            <main className="max-w-3xl mx-auto px-4 py-6 pb-32 md:pb-8 font-mono"
                data-testid="arfus-active-page">
                <Link to="/arfus-forge"
                      className="text-sm text-sky-300 hover:text-sky-200 inline-block mb-4"
                      data-testid="arfus-active-back">
                    ← Torna alla Forgia
                </Link>

                <h1 className="text-2xl md:text-3xl font-bold text-amber-300 mb-2">
                    Slot Attivi ({state.activeCount}/{state.maxActive})
                </h1>
                <p className="text-sm text-slate-400 mb-6">
                    Massimo 5 slot attivi contemporaneamente. Nessuno stack same-category.
                </p>

                {state.loading && (
                    <div className="text-center text-muted-foreground py-8">Caricamento…</div>
                )}

                {!state.loading && state.technologies.length === 0 && (
                    <div className="border border-slate-700 rounded p-6 text-center text-slate-400"
                         data-testid="arfus-active-empty">
                        Non hai ancora sbloccato tecnologie di Arfus.
                        <div className="mt-3">
                            <Link to="/arfus-forge"
                                  className="inline-block min-h-[44px] w-full md:w-auto px-4 py-2 rounded bg-sky-500 hover:bg-sky-400 text-slate-900 font-semibold"
                                  data-testid="arfus-active-goto-forge">
                                Vai alla Forgia
                            </Link>
                        </div>
                    </div>
                )}

                {!state.loading && state.technologies.length > 0 && (
                    <>
                        <section className="mb-6"
                                 data-testid="arfus-tech-list">
                            <h2 className="text-lg text-slate-200 mb-3 border-b border-slate-800 pb-2">
                                Tecnologie sbloccate
                            </h2>
                            <ul className="space-y-3">
                                {state.technologies.map((t) => {
                                    const cat = state.catalog[t.technology_slug];
                                    if (!cat) return null;
                                    return (
                                        <li key={t.technology_slug}
                                            className="border border-slate-700 rounded p-4 bg-slate-900/40 flex items-center justify-between gap-3"
                                            data-testid={`arfus-tech-row-${t.technology_slug}`}>
                                            <div className="min-w-0 flex-1">
                                                <div className="font-semibold text-slate-100 truncate">
                                                    {cat.name_it}
                                                </div>
                                                <div className="text-xs text-slate-500">
                                                    {cat.category} · +{cat.effect_value}%
                                                </div>
                                            </div>
                                            <button
                                                onClick={() => toggle(t.technology_slug)}
                                                disabled={state.toggling === t.technology_slug}
                                                className={`min-h-[44px] w-24 md:w-32 py-2 rounded font-semibold text-sm transition ${
                                                    t.is_active
                                                        ? "bg-emerald-500 hover:bg-emerald-400 text-slate-900"
                                                        : "bg-slate-700 hover:bg-slate-600 text-slate-200"
                                                } disabled:opacity-50`}
                                                data-testid={`arfus-toggle-${t.technology_slug}`}>
                                                {state.toggling === t.technology_slug
                                                    ? "…"
                                                    : (t.is_active ? "ATTIVA" : "Disattiva")}
                                            </button>
                                        </li>
                                    );
                                })}
                            </ul>
                        </section>

                        <section className="border border-amber-500/30 rounded p-4 bg-amber-950/10"
                                 data-testid="arfus-bonuses-summary">
                            <h2 className="text-sm text-amber-300 uppercase mb-3">
                                Bonus Attivi Combinati
                            </h2>
                            {Object.keys(state.bonuses).length === 0 ? (
                                <p className="text-xs text-slate-500">
                                    Nessuna tech attiva. Attiva almeno una tech per applicare bonus.
                                </p>
                            ) : (
                                <ul className="space-y-1">
                                    {Object.entries(state.bonuses).map(([cat, val]) => (
                                        <li key={cat}
                                            className="flex items-center justify-between text-sm"
                                            data-testid={`arfus-bonus-${cat}`}>
                                            <span className="text-slate-300">{cat}</span>
                                            <span className="text-amber-300 font-mono">
                                                +{val}% <span className="text-xs text-slate-500">(cap {CAPS[cat] ?? "?"}%)</span>
                                            </span>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </section>
                    </>
                )}
            </main>
        </div>
    );
}
