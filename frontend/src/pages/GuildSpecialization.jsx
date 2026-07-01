// ROUND 16.3 Phase 6 Iter2 — Guild Specialization hub (choose + reset).
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { api, formatApiError } from "../lib/api";
import AppHeader from "../components/AppHeader";

const BADGE_CLASSES = {
    amber: "border-amber-500/50 text-amber-300 bg-amber-950/20",
    orange: "border-orange-500/50 text-orange-300 bg-orange-950/20",
    emerald: "border-emerald-500/50 text-emerald-300 bg-emerald-950/20",
    sky: "border-sky-500/50 text-sky-300 bg-sky-950/20",
    red: "border-red-500/50 text-red-300 bg-red-950/20",
    violet: "border-violet-500/50 text-violet-300 bg-violet-950/20",
};

export default function GuildSpecialization() {
    const [state, setState] = useState({
        loading: true, mine: null, catalog: [], err: null,
        confirmReset: false, resetSlug: null, submitting: false,
    });

    const load = useCallback(async () => {
        try {
            const [mine, cat] = await Promise.all([
                api.get("/guild-specialization/mine"),
                api.get("/guild-specialization/catalog"),
            ]);
            setState((s) => ({
                ...s, loading: false,
                mine: mine.data, catalog: cat.data.specializations || [],
                err: null,
            }));
        } catch (err) {
            const msg = formatApiError(err);
            toast.error(msg);
            setState((s) => ({ ...s, loading: false, err: msg }));
        }
    }, []);

    useEffect(() => { load(); }, [load]);

    const choose = useCallback(async (slug) => {
        setState((s) => ({ ...s, submitting: true }));
        try {
            await api.post(`/guild-specialization/choose/${slug}`);
            toast.success("Specializzazione scelta!");
            await load();
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setState((s) => ({ ...s, submitting: false }));
        }
    }, [load]);

    const doReset = useCallback(async (newSlug) => {
        setState((s) => ({ ...s, submitting: true }));
        try {
            await api.post(`/guild-specialization/reset/${newSlug}`);
            toast.success("Reset completato!");
            setState((s) => ({ ...s, confirmReset: false, resetSlug: null }));
            await load();
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setState((s) => ({ ...s, submitting: false }));
        }
    }, [load]);

    const activeSpec = state.mine?.specialization;
    const canChoose = state.mine?.can_choose;
    const guildLevel = state.mine?.guild_level;
    const nextReset = state.mine?.active_choice?.next_reset_available_at;
    const cooldownActive = nextReset && new Date(nextReset).getTime() > Date.now();

    return (
        <div className="min-h-screen bg-background text-foreground overflow-x-hidden">
            <AppHeader />
            <main className="max-w-4xl mx-auto px-4 py-6 pb-32 md:pb-8 font-mono"
                data-testid="guild-specialization-page">
                <h1 className="text-3xl md:text-4xl font-bold text-violet-300 mb-6"
                    data-testid="guild-specialization-title">
                    Specializzazione Gilda
                </h1>

                {state.loading && (
                    <div className="text-center text-muted-foreground py-12">Caricamento…</div>
                )}

                {!state.loading && !state.mine?.active_choice && (
                    <>
                        {!canChoose ? (
                            <div className="border border-slate-700 rounded p-6 bg-slate-900/40 text-center"
                                 data-testid="spec-blocked">
                                <p className="text-slate-200 mb-2">
                                    Raggiungi <b>Livello Gilda 8</b> per scegliere una specializzazione.
                                </p>
                                <p className="text-sm text-slate-500">
                                    Attualmente sei al livello {guildLevel}.
                                </p>
                            </div>
                        ) : (
                            <>
                                <div className="mb-4 p-4 rounded border border-violet-500/40 bg-violet-950/20 text-sm text-violet-200">
                                    La prima scelta è <b>gratuita</b>. Il reset costa 200.000 oro
                                    + 3× frammento_di_ergolat + cooldown 30 giorni.
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3"
                                     data-testid="spec-choose-grid">
                                    {state.catalog.map((s) => (
                                        <div key={s.slug}
                                             className={`border rounded p-4 ${BADGE_CLASSES[s.badge_color] || "border-slate-700 bg-slate-900/40"}`}
                                             data-testid={`spec-card-${s.slug}`}>
                                            <div className="font-semibold text-slate-100 mb-1">{s.name_it}</div>
                                            <div className="text-xs text-slate-400 mb-3">{s.description_it}</div>
                                            <button onClick={() => choose(s.slug)}
                                                    disabled={state.submitting}
                                                    className="min-h-[44px] w-full md:w-auto px-4 py-2 rounded bg-violet-500 hover:bg-violet-400 disabled:bg-slate-700 text-slate-900 font-semibold text-sm"
                                                    data-testid={`spec-choose-${s.slug}`}>
                                                Scegli
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            </>
                        )}
                    </>
                )}

                {!state.loading && activeSpec && (
                    <>
                        <section className={`border-2 rounded p-6 mb-6 ${BADGE_CLASSES[activeSpec.badge_color] || "border-slate-700 bg-slate-900/40"}`}
                                 data-testid="spec-active-banner">
                            <div className="text-xs uppercase text-slate-400 mb-2">Specializzazione Attuale</div>
                            <h2 className="text-2xl font-bold text-slate-100 mb-2">
                                {activeSpec.name_it}
                            </h2>
                            <p className="text-sm text-slate-300 leading-relaxed mb-3">
                                {activeSpec.description_it}
                            </p>
                            <div className="flex flex-wrap gap-2">
                                {(activeSpec.hook_categories || []).map((h) => (
                                    <span key={h}
                                          className="text-[10px] uppercase px-2 py-1 rounded bg-slate-800 text-slate-400">
                                        {h}
                                    </span>
                                ))}
                            </div>
                        </section>

                        <div className="mb-4 text-sm text-slate-400"
                             data-testid="spec-reset-info">
                            {cooldownActive ? (
                                <>Reset disponibile dal <b>{new Date(nextReset).toLocaleDateString()}</b>
                                    {" "}(cooldown 30 giorni)</>
                            ) : (
                                <>Reset disponibile ora. Costo: 200.000 oro + 3× frammento_di_ergolat.</>
                            )}
                        </div>

                        <button onClick={() => setState((s) => ({ ...s, confirmReset: true }))}
                                disabled={cooldownActive || state.submitting}
                                className="min-h-[44px] w-full md:w-auto px-6 py-3 rounded border border-red-500/60 text-red-300 hover:bg-red-950/40 disabled:opacity-50 font-semibold"
                                data-testid="spec-reset-cta">
                            Reset Specializzazione
                        </button>

                        {state.confirmReset && (
                            <div className="mt-4 p-4 border border-red-500/60 rounded bg-red-950/20"
                                 data-testid="spec-reset-modal">
                                <p className="text-sm text-red-200 mb-3">
                                    ⚠ Il reset costa 200.000 oro + 3× frammento_di_ergolat.
                                    Cooldown 30 giorni. Scegli la nuova specializzazione:
                                </p>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mb-3">
                                    {state.catalog.filter((s) => s.slug !== activeSpec.slug).map((s) => (
                                        <button key={s.slug}
                                                onClick={() => setState((st) => ({ ...st, resetSlug: s.slug }))}
                                                className={`min-h-[44px] px-3 py-2 rounded text-sm border text-left ${state.resetSlug === s.slug ? "border-red-500 bg-red-950/40 text-red-200" : "border-slate-600 text-slate-300"}`}
                                                data-testid={`spec-reset-select-${s.slug}`}>
                                            {s.name_it}
                                        </button>
                                    ))}
                                </div>
                                <div className="flex flex-col md:flex-row gap-2">
                                    <button onClick={() => state.resetSlug && doReset(state.resetSlug)}
                                            disabled={!state.resetSlug || state.submitting}
                                            className="min-h-[44px] w-full md:w-auto px-4 py-2 rounded bg-red-500 hover:bg-red-400 disabled:bg-slate-700 text-slate-900 font-semibold"
                                            data-testid="spec-reset-confirm">
                                        Conferma Reset
                                    </button>
                                    <button onClick={() => setState((s) => ({ ...s, confirmReset: false, resetSlug: null }))}
                                            className="min-h-[44px] w-full md:w-auto px-4 py-2 rounded border border-slate-600 text-slate-300"
                                            data-testid="spec-reset-cancel">
                                        Annulla
                                    </button>
                                </div>
                            </div>
                        )}

                        <div className="mt-6">
                            <Link to="/guild-specialization/catalog"
                                  className="text-sm text-violet-300 hover:text-violet-200"
                                  data-testid="spec-view-catalog">
                                → Consulta tutti gli archetipi
                            </Link>
                        </div>
                    </>
                )}
            </main>
        </div>
    );
}
