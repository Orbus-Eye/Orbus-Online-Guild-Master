// ROUND 16.3 Phase 2 — World overview (mobile-first).
// Three branches:
//   1) access=false        → gate card (CTA "Vai ai Raid")
//   2) access=true, no cont → 8 continents grid + "Scegli" modal
//   3) access=true + cont   → active presence card + neighbors CTA + change modal
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { api, formatApiError } from "../lib/api";
import AppHeader from "../components/AppHeader";

function fmtDate(iso, lang = "it") {
    if (!iso) return "—";
    try {
        return new Date(iso).toLocaleDateString(lang, {
            year: "numeric", month: "short", day: "numeric",
        });
    } catch { return iso; }
}

function fmtRelDays(iso) {
    if (!iso) return "—";
    const ms = new Date(iso).getTime() - Date.now();
    if (ms <= 0) return "disponibile";
    const d = Math.ceil(ms / 86400000);
    return `${d} giorni`;
}

function ContinentTile({ c, onChoose, disabled }) {
    return (
        <div
            data-testid={`world-continent-tile-${c.slug}`}
            className="border border-border/60 bg-card/40 rounded-sm p-4 hover:border-amber/40 transition-colors"
        >
            <div className="flex items-baseline justify-between gap-2 mb-2">
                <h3 className="text-[14px] text-amber tracking-wide">{c.name_it}</h3>
                <span className="text-[10px] text-muted-foreground uppercase">
                    {c.domain_it}
                </span>
            </div>
            <p className="text-[11px] text-muted-foreground mb-3 leading-relaxed">
                {c.description_it}
            </p>
            <div className="flex items-center gap-2 flex-wrap">
                <Link
                    to={`/world/continents/${c.slug}`}
                    data-testid={`world-continent-open-${c.slug}`}
                    className="text-[11px] tracking-widest px-3 py-2 min-h-[44px] inline-flex items-center border border-border/60 text-foreground/80 hover:border-amber/60 rounded-sm"
                >
                    Dettagli
                </Link>
                <button
                    type="button"
                    disabled={disabled}
                    onClick={() => onChoose(c)}
                    data-testid={`world-continent-choose-${c.slug}`}
                    className="text-[11px] tracking-widest px-3 py-2 min-h-[44px] w-full md:w-auto border border-amber text-amber rounded-sm hover:bg-amber/10 font-bold disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    Scegli continente
                </button>
            </div>
        </div>
    );
}

function ChooseModal({ open, mode, target, onConfirm, onCancel, busy }) {
    if (!open || !target) return null;
    const isChange = mode === "change";
    return (
        <div
            data-testid="world-choose-modal"
            className="fixed inset-0 z-50 bg-black/70 flex items-end md:items-center justify-center p-4"
            onClick={onCancel}
        >
            <div
                className="w-full max-w-md border border-amber/40 bg-card rounded-sm p-4"
                onClick={(e) => e.stopPropagation()}
            >
                <h3 className="text-amber text-[13px] tracking-widest mb-2">
                    :: {isChange ? "Cambia continente" : "Scegli continente"}
                </h3>
                <p className="text-[12px] text-muted-foreground mb-3">
                    Stai per {isChange ? "cambiare al" : "unirti al"} continente{" "}
                    <span className="text-foreground">{target.name_it}</span>{" "}
                    ({target.domain_it}).
                </p>
                <div className="border border-amber/30 bg-amber/5 rounded-sm p-3 mb-4">
                    <p className="text-[11px] text-amber leading-relaxed">
                        ⚠ Cooldown di 30 giorni prima di poter cambiare di nuovo.
                        La scelta è puramente narrativa (nessun bonus di gioco),
                        ma la storia della tua gilda viene registrata.
                    </p>
                </div>
                <div className="flex gap-2 flex-col md:flex-row">
                    <button
                        type="button"
                        onClick={onCancel}
                        disabled={busy}
                        data-testid="world-choose-cancel"
                        className="text-[11px] tracking-widest px-3 py-2.5 min-h-[44px] w-full md:w-auto border border-border/60 text-muted-foreground rounded-sm"
                    >
                        Annulla
                    </button>
                    <button
                        type="button"
                        onClick={onConfirm}
                        disabled={busy}
                        data-testid="world-choose-confirm"
                        className="text-[11px] tracking-widest px-3 py-2.5 min-h-[44px] w-full md:w-auto border border-amber text-amber rounded-sm hover:bg-amber/10 font-bold disabled:opacity-50"
                    >
                        {busy ? "…" : isChange ? "Conferma cambio" : "Conferma scelta"}
                    </button>
                </div>
            </div>
        </div>
    );
}

export default function World() {
    const [state, setState] = useState({ loading: true, data: null });
    const [modal, setModal] = useState({ open: false, mode: null, target: null });
    const [busy, setBusy] = useState(false);

    const load = useCallback(async () => {
        try {
            const [ov, cs] = await Promise.all([
                api.get("/world/overview"),
                api.get("/world/continents"),
            ]);
            const merged = {
                ...ov.data,
                continents_available: ov.data.continents_available
                    || cs.data.continents || [],
            };
            setState({ loading: false, data: merged });
        } catch (err) {
            toast.error(formatApiError(err));
            setState({ loading: false, data: null });
        }
    }, []);

    useEffect(() => { load(); }, [load]);

    const openChoose = (c) => setModal({
        open: true,
        mode: state.data?.continent ? "change" : "join",
        target: c,
    });
    const cancelChoose = () => setModal({ open: false, mode: null, target: null });

    const confirmChoose = async () => {
        if (!modal.target) return;
        setBusy(true);
        try {
            const slug = modal.target.slug;
            const url = modal.mode === "change"
                ? `/world/continents/${slug}/change`
                : `/world/continents/${slug}/join`;
            await api.post(url);
            toast.success(modal.mode === "change"
                ? `Continente cambiato: ${modal.target.name_it}`
                : `Benvenuta in ${modal.target.name_it}`);
            cancelChoose();
            await load();
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setBusy(false);
        }
    };

    return (
        <div className="min-h-screen bg-background text-foreground overflow-x-hidden">
            <AppHeader />
            <main className="max-w-4xl mx-auto px-4 py-6 pb-32 md:pb-8 font-mono">
                <header className="mb-6">
                    <h1 data-testid="world-title" className="text-amber text-xl tracking-widest">
                        :: Mondo di Orbus
                    </h1>
                    <p className="text-[11px] text-muted-foreground mt-1">
                        Otto continenti tematici. Scegli dove ancorare la tua gilda.
                    </p>
                </header>

                {state.loading && (
                    <div data-testid="world-loading"
                         className="text-[11px] text-muted-foreground italic">
                        :: Caricamento...
                    </div>
                )}

                {/* Branch 1: NO access */}
                {!state.loading && state.data && state.data.access === false && (
                    <div data-testid="world-blocked"
                         className="border border-amber/40 bg-amber/5 rounded-sm p-4">
                        <div className="text-[13px] text-amber mb-2">
                            :: Accesso al Mondo bloccato
                        </div>
                        <p className="text-[12px] text-muted-foreground mb-4 leading-relaxed">
                            {state.data.requirement || "Completa il tuo primo raid per accedere al Mondo di Orbus."}
                        </p>
                        <Link
                            to={state.data.cta || "/raids"}
                            data-testid="world-blocked-cta"
                            className="inline-flex items-center w-full md:w-auto justify-center text-[11px] tracking-widest px-4 py-2.5 min-h-[44px] border border-amber text-amber rounded-sm hover:bg-amber/10 font-bold"
                        >
                            Vai ai Raid →
                        </Link>
                    </div>
                )}

                {/* Branch 2: access, NO continent */}
                {!state.loading && state.data?.access && !state.data.continent && (
                    <>
                        <div data-testid="world-nocontinent-header"
                             className="border border-border/60 bg-card/40 rounded-sm p-4 mb-4">
                            <div className="text-[12px] text-muted-foreground leading-relaxed">
                                Non hai ancora scelto un continente. Ogni continente
                                rappresenta una tradizione tematica. La scelta è
                                narrativa e sociale (gilde vicine); nessun bonus
                                statistico.
                            </div>
                        </div>
                        <div className="grid gap-3 md:grid-cols-2">
                            {(state.data.continents_available || []).map((c) => (
                                <ContinentTile key={c.slug} c={c} onChoose={openChoose} disabled={busy} />
                            ))}
                        </div>
                    </>
                )}

                {/* Branch 3: access + active continent */}
                {!state.loading && state.data?.access && state.data.continent && (
                    <div className="space-y-4">
                        <section data-testid="world-active-presence"
                                 className="border border-amber/40 bg-card/40 rounded-sm p-4">
                            <div className="flex items-baseline justify-between gap-2 flex-wrap mb-2">
                                <h2 data-testid="world-active-name"
                                    className="text-amber text-[14px] tracking-wide">
                                    {state.data.continent.name_it}
                                </h2>
                                <span className="text-[10px] text-muted-foreground uppercase">
                                    {state.data.continent.domain_it}
                                </span>
                            </div>
                            <p className="text-[11px] text-muted-foreground mb-3 leading-relaxed">
                                {state.data.continent.description_it}
                            </p>
                            <div className="grid grid-cols-2 gap-3 mb-3 text-[11px]">
                                <div>
                                    <div className="text-muted-foreground">Ancorata dal</div>
                                    <div data-testid="world-active-joined-at" className="text-foreground">
                                        {fmtDate(state.data.presence?.joined_at)}
                                    </div>
                                </div>
                                <div>
                                    <div className="text-muted-foreground">Prossimo cambio</div>
                                    <div data-testid="world-active-next-change"
                                         className="text-foreground">
                                        {fmtRelDays(state.data.next_change_available_at)}
                                    </div>
                                </div>
                                <div>
                                    <div className="text-muted-foreground">Gilde nel continente</div>
                                    <div data-testid="world-active-guilds-count" className="text-foreground">
                                        {state.data.guilds_in_continent_count ?? 0}
                                    </div>
                                </div>
                                <div>
                                    <div className="text-muted-foreground">Trasferimenti totali</div>
                                    <div className="text-foreground">
                                        {state.data.presence?.change_count ?? 0}
                                    </div>
                                </div>
                            </div>
                            <div className="flex flex-col md:flex-row gap-2">
                                <Link
                                    to={`/world/continents/${state.data.continent.slug}`}
                                    data-testid="world-open-continent"
                                    className="text-[11px] tracking-widest px-3 py-2.5 min-h-[44px] inline-flex items-center justify-center w-full md:w-auto border border-border/60 text-foreground/80 hover:border-amber/60 rounded-sm"
                                >
                                    Apri continente →
                                </Link>
                                <Link
                                    to="/world/neighbors"
                                    data-testid="world-open-neighbors"
                                    className="text-[11px] tracking-widest px-3 py-2.5 min-h-[44px] inline-flex items-center justify-center w-full md:w-auto border border-border/60 text-foreground/80 hover:border-amber/60 rounded-sm"
                                >
                                    Gilde vicine →
                                </Link>
                            </div>
                        </section>

                        <section>
                            <div className="text-[11px] text-muted-foreground tracking-widest mb-2">
                                :: Cambia continente
                            </div>
                            <div className="grid gap-3 md:grid-cols-2">
                                {(state.data.continents_available || []).filter(
                                    (c) => c.slug !== state.data.continent.slug,
                                ).length === 0 ? (
                                    <div className="text-[11px] text-muted-foreground italic">
                                        Nessun altro continente disponibile al momento.
                                    </div>
                                ) : null}
                                {/* Fallback: list all 8 continents so user can change */}
                                {(state.data.other_continents
                                  || state.data.continents_available
                                  || []).map((c) => (
                                    c.slug !== state.data.continent.slug ? (
                                        <ContinentTile
                                            key={c.slug}
                                            c={c}
                                            onChoose={openChoose}
                                            disabled={busy}
                                        />
                                    ) : null
                                ))}
                            </div>
                        </section>
                    </div>
                )}
            </main>

            <ChooseModal
                open={modal.open}
                mode={modal.mode}
                target={modal.target}
                onConfirm={confirmChoose}
                onCancel={cancelChoose}
                busy={busy}
            />
        </div>
    );
}
