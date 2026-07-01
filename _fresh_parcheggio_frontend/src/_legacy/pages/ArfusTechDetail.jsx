// ROUND 16.3 Phase 5B Iter2 — Arfus Tech Detail + Research CTA.
import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { api, formatApiError } from "../lib/api";
import AppHeader from "../components/AppHeader";

const APPLIES_LABEL = {
    expedition: "Spedizioni",
    raid: "Raid",
    world_boss: "World Boss",
    resource_gathering: "Gathering risorse",
    legendary_forge: "Forgia Leggendaria",
};

function formatHms(seconds) {
    if (!seconds || seconds <= 0) return "—";
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    if (h > 0) return `${h}h ${m}m`;
    if (m > 0) return `${m}m ${s}s`;
    return `${s}s`;
}

export default function ArfusTechDetail() {
    const { slug } = useParams();
    const navigate = useNavigate();
    const [state, setState] = useState({
        loading: true, data: null, err: null, submitting: false,
        showSlotWarn: false, activeCount: 0,
    });

    const load = useCallback(async () => {
        try {
            const [detail, mine] = await Promise.all([
                api.get(`/arfus-forge/catalog/${slug}`),
                api.get("/arfus-forge/technologies/mine").catch(() => ({ data: {} })),
            ]);
            setState((s) => ({
                ...s, loading: false, data: detail.data, err: null,
                activeCount: mine.data?.active_count || 0,
            }));
        } catch (err) {
            const msg = formatApiError(err);
            toast.error(msg);
            setState((s) => ({ ...s, loading: false, err: msg }));
        }
    }, [slug]);

    // eslint-disable-next-line react-hooks/exhaustive-deps
    useEffect(() => { load(); }, [slug]);

    const startResearch = useCallback(async () => {
        if (state.activeCount >= 4 && !state.showSlotWarn) {
            setState((s) => ({ ...s, showSlotWarn: true }));
            return;
        }
        setState((s) => ({ ...s, submitting: true, showSlotWarn: false }));
        try {
            await api.post(`/arfus-forge/research/${slug}`);
            toast.success("Ricerca avviata!");
            navigate("/arfus-forge/research");
        } catch (err) {
            toast.error(formatApiError(err));
            setState((s) => ({ ...s, submitting: false }));
        }
    }, [slug, state.activeCount, state.showSlotWarn, navigate]);

    const t = state.data;

    return (
        <div className="min-h-screen bg-background text-foreground overflow-x-hidden">
            <AppHeader />
            <main className="max-w-3xl mx-auto px-4 py-6 pb-32 md:pb-8 font-mono"
                data-testid="arfus-tech-detail-page">
                <Link to="/arfus-forge"
                      className="text-sm text-sky-300 hover:text-sky-200 inline-block mb-4"
                      data-testid="arfus-back-to-forge">
                    ← Torna alla Forgia
                </Link>

                {state.loading && (
                    <div className="text-center text-muted-foreground py-16"
                        data-testid="arfus-detail-loading">Caricamento…</div>
                )}

                {!state.loading && t && (
                    <>
                        <header className="mb-6">
                            <h1 className="text-2xl md:text-3xl font-bold text-amber-300 mb-2"
                                data-testid="arfus-detail-title">
                                {t.name_it}
                            </h1>
                            <div className="text-sm text-slate-400 mb-2">
                                Categoria: <span className="text-slate-200">{t.category}</span>
                                {" · "}Livello richiesto: {t.guild_level_required}
                            </div>
                            <p className="text-sm text-slate-300 leading-relaxed">
                                {t.description_it}
                            </p>
                        </header>

                        <section className="mb-4 border border-amber-500/30 rounded p-4 bg-amber-950/10">
                            <div className="text-xs text-slate-400 uppercase mb-1">Effetto</div>
                            <div className="text-2xl text-amber-300 font-semibold"
                                 data-testid="arfus-detail-effect">
                                +{t.effect_value}%
                            </div>
                            <div className="text-xs text-slate-500 mt-1">
                                (Cap di categoria: +{t.category_cap}%)
                            </div>
                        </section>

                        <section className="mb-4">
                            <div className="text-xs text-slate-400 uppercase mb-2">Applies to</div>
                            <div className="flex flex-wrap gap-2"
                                 data-testid="arfus-detail-applies">
                                {(t.applies_to || []).map((a) => (
                                    <span key={a}
                                          className="text-xs px-2 py-1 rounded bg-slate-800 border border-slate-700 text-slate-300">
                                        {APPLIES_LABEL[a] || a}
                                    </span>
                                ))}
                            </div>
                        </section>

                        <section className="mb-4 border border-slate-700 rounded p-4">
                            <div className="text-xs text-slate-400 uppercase mb-3">Costo ricerca</div>
                            <ul className="space-y-2 text-sm">
                                {(t.input_resources || []).map((r, i) => {
                                    const miss = (t.missing_requirements || []).find(
                                        (m) => m.slug === r.slug && m.type === "resource");
                                    const owned = miss ? miss.owned : r.qty;
                                    return (
                                        <li key={`r-${i}`}
                                            className={miss ? "text-red-300" : "text-slate-300"}
                                            data-testid={`arfus-cost-resource-${r.slug}`}>
                                            {r.slug}: {owned} / {r.qty}
                                            {miss && <span className="ml-2 text-xs">(mancante)</span>}
                                        </li>
                                    );
                                })}
                                {(t.input_materials || []).map((m, i) => {
                                    const miss = (t.missing_requirements || []).find(
                                        (x) => x.slug === m.slug && x.type === "material");
                                    const owned = miss ? miss.owned : m.qty;
                                    return (
                                        <li key={`m-${i}`}
                                            className={miss ? "text-red-300" : "text-slate-300"}
                                            data-testid={`arfus-cost-material-${m.slug}`}>
                                            {m.slug}: {owned} / {m.qty}
                                            {miss && <span className="ml-2 text-xs">(mancante)</span>}
                                        </li>
                                    );
                                })}
                                <li className={
                                        (t.missing_requirements || []).some((mm) => mm.type === "gold")
                                            ? "text-red-300" : "text-slate-300"}
                                    data-testid="arfus-cost-gold">
                                    Oro: {t.gold_status?.owned ?? 0} / {t.input_gold}
                                </li>
                            </ul>
                            <div className="text-xs text-slate-500 mt-3">
                                Durata ricerca: <span className="text-slate-300">
                                    {formatHms(t.research_duration_seconds)}</span>
                            </div>
                        </section>

                        {t.is_unlocked && (
                            <div className="mb-4 p-3 rounded border border-emerald-500/40 bg-emerald-950/20 text-sm text-emerald-300"
                                 data-testid="arfus-already-unlocked">
                                Questa tecnologia è già sbloccata.
                                <Link to="/arfus-forge/active" className="ml-2 underline">Vai alla gestione slot →</Link>
                            </div>
                        )}

                        {!t.is_unlocked && (
                            <>
                                {state.showSlotWarn && (
                                    <div className="mb-4 p-4 border border-amber-500/60 rounded bg-amber-950/40 text-sm text-amber-200"
                                         data-testid="arfus-slot-warning">
                                        ⚠ Hai già {state.activeCount} tecnologie attive.
                                        Sbloccarne un'altra è OK, ma per <b>attivarla</b> dovrai
                                        disattivarne una esistente (max 5 slot).
                                        <div className="mt-3 flex flex-col md:flex-row gap-2">
                                            <button onClick={startResearch}
                                                    className="min-h-[44px] w-full md:w-auto px-4 py-2 rounded bg-amber-500 hover:bg-amber-400 text-slate-900 font-semibold"
                                                    data-testid="arfus-confirm-research">
                                                Ho capito, avvia
                                            </button>
                                            <button onClick={() => setState((s) => ({ ...s, showSlotWarn: false }))}
                                                    className="min-h-[44px] w-full md:w-auto px-4 py-2 rounded border border-slate-600 text-slate-300"
                                                    data-testid="arfus-cancel-warning">
                                                Annulla
                                            </button>
                                        </div>
                                    </div>
                                )}

                                <button onClick={startResearch}
                                        disabled={state.submitting || !t.can_research}
                                        className="min-h-[44px] w-full md:w-auto px-6 py-3 rounded bg-amber-500 hover:bg-amber-400 disabled:bg-slate-700 disabled:text-slate-500 text-slate-900 font-semibold transition"
                                        data-testid="arfus-start-research-cta">
                                    {state.submitting ? "Avvio…" : "Avvia Ricerca"}
                                </button>
                                {!t.can_research && (
                                    <p className="text-xs text-slate-500 mt-2"
                                       data-testid="arfus-cannot-research-hint">
                                        Requisiti mancanti: {(t.missing_requirements || []).map((m) =>
                                            m.type === "gold" ? "oro" : (m.slug || m.type)).join(", ") || "nessuno"}
                                    </p>
                                )}
                            </>
                        )}
                    </>
                )}
            </main>
        </div>
    );
}
