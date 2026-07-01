// ROUND 6E Task 1 — Respec modal.
//
// Opens from Training.jsx when the user clicks "Cambia specializzazione" on
// an already-specialized adventurer. Shows current spec, picks a new one
// (filtered by class + tier), previews stat delta, forces an explicit
// signature discard checkbox before allowing confirmation.
//
// Server is authoritative: cost, cooldown, eligibility are all enforced by
// `POST /api/training/respec/{adventurer_id}`. This modal is presentational
// only — even the "next allowed at" countdown comes from the API.
import { useMemo, useState } from "react";

import { useT } from "../i18n/I18nContext";

const STAT_LABEL = {
    strength: "STR",
    agility: "AGI",
    intellect: "INT",
    endurance: "END",
    faith: "FAI",
};

// Cost table mirrors backend `respec_cost_for_count` (display-only; server
// validates the actual debit). Index = respec_count BEFORE this respec.
const RESPEC_COSTS = [
    { gold: 800, dust: 1 },
    { gold: 1200, dust: 2 },
    { gold: 2000, dust: 3 },
];

function costFor(count) {
    if (count <= 0) return RESPEC_COSTS[0];
    if (count === 1) return RESPEC_COSTS[1];
    return RESPEC_COSTS[2];
}

export default function RespecModal({
    adv, catalog, onClose, onSubmit, submitting, lang,
}) {
    const { t } = useT();
    const currentSpec = adv?.specialization;
    const respecCount = Number(adv?.specialization_respec_count || 0);
    const cost = costFor(respecCount);

    // Filter specs: must be eligible for adv class + not the current one
    // + respect tier (catalog already returns only unlocked tiers).
    const advClass = adv?.class_slug;
    const candidateSpecs = useMemo(() => {
        const specs = catalog?.specs || [];
        return specs.filter(
            (s) =>
                s.slug !== currentSpec?.slug &&
                Array.isArray(s.eligible_classes) &&
                s.eligible_classes.includes(advClass),
        );
    }, [catalog, advClass, currentSpec]);

    const [newSpec, setNewSpec] = useState(null);
    const [discardChecked, setDiscardChecked] = useState(false);

    const canConfirm =
        !!newSpec && discardChecked && !submitting;

    const oldMods = currentSpec?.modifiers || {};
    const newMods = newSpec?.modifiers || {};

    function handleConfirm() {
        if (!canConfirm) return;
        onSubmit({
            new_spec_slug: newSpec.slug,
            discard_signature_items: true,
        });
    }

    return (
        <div
            data-testid="respec-modal"
            className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4 overflow-y-auto"
            onClick={onClose}
        >
            <div
                onClick={(e) => e.stopPropagation()}
                className="max-w-lg w-full border border-amber bg-card rounded-sm p-5 text-[12px] space-y-4 my-8"
            >
                <header className="border-b border-border pb-3">
                    <div className="text-amber tracking-widest text-[10px] mb-1">
                        :: {t("respec.title", "CAMBIA SPECIALIZZAZIONE")}
                    </div>
                    <h3 className="text-foreground font-bold text-base">
                        {adv?.name}
                        <span className="text-muted-foreground text-[11px] font-normal ml-2">
                            {adv?.class_name} · Lv{adv?.level}
                        </span>
                    </h3>
                </header>

                {/* Current spec */}
                <section data-testid="respec-current-section">
                    <div className="text-muted-foreground tracking-widest text-[10px] mb-1">
                        {t("respec.current_spec", "Spec attuale")}
                    </div>
                    <div className="text-foreground">
                        ✦ {lang === "it" ? currentSpec?.name_it : currentSpec?.name_en}
                    </div>
                    <div className="text-[10px] text-amber/80 mt-1">
                        {Object.entries(oldMods).map(([k, v]) => (
                            <span key={k} className="inline-block mr-2">
                                +{v} {STAT_LABEL[k] || k.toUpperCase()}
                            </span>
                        ))}
                    </div>
                    {respecCount > 0 && (
                        <div
                            className="text-[10px] text-muted-foreground mt-1"
                            data-testid="respec-count-display"
                        >
                            {t("respec.count_label", "Respec già effettuati")}: {respecCount}
                        </div>
                    )}
                </section>

                {/* New spec picker */}
                <section>
                    <div className="text-muted-foreground tracking-widest text-[10px] mb-2">
                        {t("respec.pick_new", "Nuova specializzazione")}
                    </div>
                    {candidateSpecs.length === 0 ? (
                        <div
                            data-testid="respec-no-candidates"
                            className="text-[11px] text-muted-foreground border border-border rounded-sm p-3 text-center"
                        >
                            {t(
                                "respec.no_candidates",
                                "Nessuna specializzazione alternativa compatibile con questa classe."
                            )}
                        </div>
                    ) : (
                        <ul className="space-y-1.5" data-testid="respec-spec-list">
                            {candidateSpecs.map((s) => {
                                const isSel = newSpec?.slug === s.slug;
                                return (
                                    <li key={s.slug}>
                                        <button
                                            type="button"
                                            onClick={() => setNewSpec(s)}
                                            data-testid={`respec-spec-${s.slug}`}
                                            className={`w-full text-left p-2.5 rounded-sm border transition-colors ${
                                                isSel
                                                    ? "border-amber bg-amber/10 text-foreground"
                                                    : "border-border hover:border-amber/60 hover:bg-secondary/30"
                                            }`}
                                        >
                                            <div className="flex items-center justify-between">
                                                <span className="font-bold text-[12px]">
                                                    {lang === "it" ? s.name_it : s.name_en}
                                                </span>
                                                <span className="text-[10px] text-amber tracking-widest">
                                                    {s.tier === "starter" ? "STARTER" : "FULL"} · {s.role}
                                                </span>
                                            </div>
                                            <div className="text-[10px] text-amber/90 mt-1">
                                                {Object.entries(s.modifiers || {}).map(([k, v]) => (
                                                    <span key={k} className="inline-block mr-2">
                                                        +{v} {STAT_LABEL[k] || k.toUpperCase()}
                                                    </span>
                                                ))}
                                            </div>
                                        </button>
                                    </li>
                                );
                            })}
                        </ul>
                    )}
                </section>

                {/* Delta preview */}
                {newSpec && (
                    <section
                        data-testid="respec-delta-preview"
                        className="border border-border/60 bg-secondary/10 rounded-sm p-3"
                    >
                        <div className="text-[10px] text-muted-foreground tracking-widest mb-1">
                            {t("respec.delta_label", "Variazione bonus")}
                        </div>
                        <div className="text-[11px] text-foreground flex items-center gap-2 flex-wrap">
                            <span className="text-muted-foreground line-through">
                                {Object.entries(oldMods)
                                    .map(([k, v]) => `+${v} ${STAT_LABEL[k] || k}`)
                                    .join(" ")}
                            </span>
                            <span className="text-amber">→</span>
                            <span className="text-amber font-bold">
                                {Object.entries(newMods)
                                    .map(([k, v]) => `+${v} ${STAT_LABEL[k] || k}`)
                                    .join(" ")}
                            </span>
                        </div>
                    </section>
                )}

                {/* Cost & cooldown */}
                <section
                    data-testid="respec-cost-section"
                    className="border-t border-border pt-3 text-[11px] space-y-1"
                >
                    <div className="flex items-center justify-between">
                        <span className="text-muted-foreground tracking-widest">
                            {t("respec.cost_label", "Costo")}
                        </span>
                        <span
                            data-testid="respec-cost-display"
                            className="text-amber font-bold"
                        >
                            {cost.gold}g + {cost.dust} {t("respec.dust_unit", "Polvere Arcana Minore")}
                        </span>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="text-muted-foreground tracking-widest">
                            {t("respec.cooldown_label", "Cooldown prossimo respec")}
                        </span>
                        <span className="text-foreground/80">
                            {t("respec.cooldown_value", "24 ore")}
                        </span>
                    </div>
                </section>

                {/* Warning + checkbox */}
                <section
                    data-testid="respec-warning-section"
                    className="border border-red-500/50 bg-red-500/5 rounded-sm p-3"
                >
                    <div className="text-red-300 text-[11px] mb-2 font-bold">
                        ⚠ {t("respec.warning_title", "ATTENZIONE — IRREVERSIBILE")}
                    </div>
                    <p className="text-[11px] text-red-200/90 leading-relaxed mb-3">
                        {t(
                            "respec.warning_body",
                            "Il signature item attuale verrà distrutto definitivamente (soft-discard, non recuperabile). Verrà creato un nuovo signature item per la nuova specializzazione."
                        )}
                    </p>
                    <label className="flex items-start gap-2 cursor-pointer">
                        <input
                            type="checkbox"
                            checked={discardChecked}
                            onChange={(e) => setDiscardChecked(e.target.checked)}
                            data-testid="respec-discard-checkbox"
                            className="mt-0.5 accent-red-500"
                        />
                        <span className="text-[11px] text-red-100">
                            {t(
                                "respec.discard_confirm",
                                "Confermo: distruggi il signature item attuale"
                            )}
                        </span>
                    </label>
                </section>

                {/* Actions */}
                <div className="flex items-center justify-between gap-2 pt-2">
                    <button
                        type="button"
                        onClick={onClose}
                        disabled={submitting}
                        data-testid="respec-cancel-btn"
                        className="px-3 py-1.5 text-[11px] tracking-widest border border-border text-muted-foreground rounded-sm hover:border-foreground"
                    >
                        {t("common.cancel", "Annulla")}
                    </button>
                    <button
                        type="button"
                        onClick={handleConfirm}
                        disabled={!canConfirm}
                        data-testid="respec-confirm-btn"
                        className="px-3 py-1.5 text-[11px] tracking-widest border border-amber text-amber rounded-sm hover:bg-amber/10 disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                        {submitting
                            ? "…"
                            : `${t("respec.confirm_btn", "RESPEC")} — ${cost.gold}g`}
                    </button>
                </div>
            </div>
        </div>
    );
}
