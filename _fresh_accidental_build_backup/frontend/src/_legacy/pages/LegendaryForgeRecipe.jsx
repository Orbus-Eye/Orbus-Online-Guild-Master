// ROUND 16.3 Phase 5A — Legendary Forge recipe detail + craft flow.
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { api, formatApiError } from "../lib/api";
import AppHeader from "../components/AppHeader";

export default function LegendaryForgeRecipe() {
    const { slug } = useParams();
    const navigate = useNavigate();
    const [state, setState] = useState({ loading: true, recipe: null, err: null });
    const [confirmOpen, setConfirmOpen] = useState(false);
    const [awareChecked, setAwareChecked] = useState(false);
    const [crafting, setCrafting] = useState(false);

    async function load() {
        try {
            const r = await api.get(`/legendary-forge/catalog/${slug}`);
            setState({ loading: false, recipe: r.data, err: null });
        } catch (err) {
            const msg = formatApiError(err);
            toast.error(msg);
            setState({ loading: false, recipe: null, err: msg });
        }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    useEffect(() => { load(); }, [slug]);

    async function handleCraft() {
        if (!awareChecked) {
            toast.error("Devi confermare di essere consapevole del BOP");
            return;
        }
        setCrafting(true);
        try {
            const r = await api.post(`/legendary-forge/craft/${slug}`);
            toast.success(`Forgiatura avviata! Order ${r.data.order.id.slice(0, 8)}…`);
            setConfirmOpen(false);
            navigate("/legendary-forge/orders");
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setCrafting(false);
        }
    }

    const r = state.recipe;
    return (
        <div className="min-h-screen bg-background text-foreground overflow-x-hidden">
            <AppHeader />
            <main className="max-w-3xl mx-auto px-4 py-6 pb-32 md:pb-8 font-mono"
                data-testid="recipe-detail-page">
                <div className="mb-4">
                    <Link to="/legendary-forge"
                        className="text-sm text-muted-foreground hover:text-amber-300"
                        data-testid="recipe-back">
                        ← Torna alla Forgia
                    </Link>
                </div>

                {state.loading && (
                    <div className="text-center text-muted-foreground py-16"
                        data-testid="recipe-loading">Caricamento…</div>
                )}

                {!state.loading && r && (
                    <>
                        <div className="mb-6">
                            <h1 className="text-2xl md:text-3xl font-bold text-amber-300
                                mb-1" data-testid="recipe-name">{r.name_it}</h1>
                            <div className="text-xs text-muted-foreground">
                                Output: <span className="text-amber-200">{r.output_slug}</span> ·
                                Lv.{r.guild_level_required}+ · Durata {(r.crafting_duration_seconds/60)|0} min
                            </div>
                        </div>

                        {/* Probabilità trasparenti */}
                        <section className="mb-6 border border-slate-700 rounded-lg p-4
                            bg-slate-900/40" data-testid="recipe-probabilities">
                            <h2 className="text-sm font-bold text-slate-300 mb-3">
                                🎲 Probabilità Trasparenti
                            </h2>
                            <div className="mb-3">
                                <div className="flex justify-between text-xs mb-1">
                                    <span>Successo</span>
                                    <span className="text-green-400 font-bold">
                                        {r.computed_success_chance}%</span>
                                </div>
                                <div className="h-2 bg-slate-800 rounded overflow-hidden">
                                    <div className="h-full bg-green-500"
                                        style={{width: `${r.computed_success_chance}%`}} />
                                </div>
                            </div>
                            <div className="grid grid-cols-3 gap-2 text-xs">
                                <div className="p-2 border border-amber-500/50 rounded
                                    bg-amber-950/20">
                                    <div className="text-amber-300 font-bold">Perfezionato</div>
                                    <div className="text-lg">{r.perfezionato_chance}%</div>
                                </div>
                                <div className="p-2 border border-slate-500/50 rounded
                                    bg-slate-800/40">
                                    <div className="text-slate-300 font-bold">Normale</div>
                                    <div className="text-lg">{r.normale_chance}%</div>
                                </div>
                                <div className="p-2 border border-orange-500/50 rounded
                                    bg-orange-950/20">
                                    <div className="text-orange-300 font-bold">Imperfetto</div>
                                    <div className="text-lg">{r.imperfetto_chance}%</div>
                                </div>
                            </div>
                        </section>

                        {/* Pity system */}
                        <section className="mb-6 border border-slate-700 rounded-lg p-4
                            bg-slate-900/40" data-testid="recipe-pity">
                            <h2 className="text-sm font-bold text-slate-300 mb-3">
                                🎯 Sistema Pity
                            </h2>
                            <div className="text-xs mb-2">
                                Craft senza Perfezionato: <span className="font-bold
                                    text-amber-300">{r.pity_status.counter} / {r.pity_status.threshold}</span>
                            </div>
                            <div className="h-2 bg-slate-800 rounded overflow-hidden mb-2">
                                <div className="h-full bg-amber-500 transition-all"
                                    style={{width: `${Math.min(100, (r.pity_status.counter / r.pity_status.threshold) * 100)}%`}} />
                            </div>
                            {r.pity_status.next_guaranteed_no_imperfetto && (
                                <div className="p-2 border border-amber-500/60 bg-amber-950/30
                                    rounded text-xs text-amber-300"
                                    data-testid="pity-warning">
                                    ⚡ Prossimo Imperfetto sarà forzato a Normale (pity attivo)
                                </div>
                            )}
                        </section>

                        {/* Costo */}
                        <section className="mb-6 border border-slate-700 rounded-lg p-4
                            bg-slate-900/40" data-testid="recipe-cost">
                            <h2 className="text-sm font-bold text-slate-300 mb-3">
                                💎 Costo
                            </h2>
                            <div className="mb-2">
                                <div className="text-xs text-muted-foreground mb-1">Risorse continentali</div>
                                {r.resources_status.map((res) => (
                                    <div key={res.slug} className="flex justify-between text-xs py-0.5">
                                        <span>{res.slug}</span>
                                        <span className={res.owned >= res.required ? "text-green-400" : "text-red-400"}>
                                            {res.owned} / {res.required} {res.owned >= res.required ? "✓" : "✗"}
                                        </span>
                                    </div>
                                ))}
                            </div>
                            <div className="mb-2">
                                <div className="text-xs text-muted-foreground mb-1">Materiali</div>
                                {r.materials_status.map((mat) => (
                                    <div key={mat.slug} className="flex justify-between text-xs py-0.5">
                                        <span>{mat.slug}</span>
                                        <span className={mat.owned >= mat.required ? "text-green-400" : "text-red-400"}>
                                            {mat.owned} / {mat.required} {mat.owned >= mat.required ? "✓" : "✗"}
                                        </span>
                                    </div>
                                ))}
                            </div>
                            <div className="flex justify-between text-xs py-0.5 border-t
                                border-slate-700 pt-2 mt-2">
                                <span>Oro</span>
                                <span className={r.gold_status.owned >= r.gold_status.required ? "text-green-400" : "text-red-400"}>
                                    {r.gold_status.owned.toLocaleString()} / {r.gold_status.required.toLocaleString()}
                                </span>
                            </div>
                        </section>

                        {/* BOP warning */}
                        <section className="mb-6 border-2 border-red-500/60 rounded-lg p-4
                            bg-red-950/20" data-testid="recipe-bop-warning">
                            <h2 className="text-sm font-bold text-red-300 mb-2">
                                ⚠ Legendary BOP (Bound On Pickup)
                            </h2>
                            <p className="text-xs text-red-100/80">
                                Questo oggetto sarà <span className="font-bold">legato alla tua gilda</span> dal
                                momento della creazione. Non potrà essere <span className="font-bold">commerciato,
                                scambiato, messo all'asta o venduto</span> per oro o denaro reale. Una volta forgiato,
                                resterà nel tuo inventario per sempre.
                            </p>
                        </section>

                        <button
                            disabled={!r.can_craft}
                            onClick={() => { setAwareChecked(false); setConfirmOpen(true); }}
                            className="w-full md:w-auto px-6 py-3 min-h-[44px]
                                bg-amber-600 text-white rounded-md hover:bg-amber-500
                                disabled:opacity-40 disabled:cursor-not-allowed
                                font-bold transition"
                            data-testid="recipe-craft-btn">
                            {r.can_craft ? "🔨 Forgia Ora" : "Requisiti mancanti"}
                        </button>

                        {!r.can_craft && r.missing_requirements.length > 0 && (
                            <div className="mt-2 text-xs text-red-400"
                                data-testid="recipe-missing">
                                Mancanti: {r.missing_requirements.map(m =>
                                    m.slug || m.type).join(", ")}
                            </div>
                        )}
                    </>
                )}

                {/* Modal conferma */}
                {confirmOpen && r && (
                    <div className="fixed inset-0 bg-black/80 z-50 flex items-center
                        justify-center p-4" data-testid="confirm-modal">
                        <div className="bg-slate-900 border-2 border-amber-500/60
                            rounded-lg p-6 max-w-md w-full">
                            <h3 className="text-lg font-bold text-amber-300 mb-3">
                                Conferma Forgiatura
                            </h3>
                            <p className="text-sm text-slate-300 mb-4">
                                Stai per forgiare <span className="text-amber-300 font-bold">
                                {r.name_it}</span>. L'oggetto sarà <span className="text-red-400
                                font-bold">BOP totale</span> — non commerciabile.
                            </p>
                            <label className="flex items-start gap-2 mb-4 cursor-pointer">
                                <input type="checkbox"
                                    checked={awareChecked}
                                    onChange={(e) => setAwareChecked(e.target.checked)}
                                    className="mt-1"
                                    data-testid="confirm-aware-checkbox" />
                                <span className="text-xs text-slate-300">
                                    Sono consapevole che questo oggetto sarà legato alla mia gilda
                                    e non potrà essere venduto o scambiato.
                                </span>
                            </label>
                            <div className="flex gap-2">
                                <button onClick={() => setConfirmOpen(false)}
                                    className="flex-1 px-4 py-2 min-h-[44px] border
                                        border-slate-600 rounded-md hover:bg-slate-800"
                                    data-testid="confirm-cancel">
                                    Annulla
                                </button>
                                <button onClick={handleCraft}
                                    disabled={!awareChecked || crafting}
                                    className="flex-1 px-4 py-2 min-h-[44px]
                                        bg-amber-600 text-white rounded-md
                                        hover:bg-amber-500 disabled:opacity-40
                                        disabled:cursor-not-allowed font-bold"
                                    data-testid="confirm-craft">
                                    {crafting ? "Forgiando…" : "🔨 Forgia"}
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}
