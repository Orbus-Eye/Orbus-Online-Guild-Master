// ROUND 6C Task 8 — Training Grounds page.
// Lists eligible (active, Lv5+, unspecialized) adventurers and surfaces the
// catalog filtered by current Training Grounds level (starter / full tier).
// Apply is one-click with a confirmation modal that previews the bonus +
// signature item the player will receive.
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";

import AppHeader from "../components/AppHeader";
import RespecModal from "../components/RespecModal";
import { useAuth } from "../context/AuthContext";
import { useT } from "../i18n/I18nContext";
import { api, formatApiError } from "../lib/api";

const MIN_LEVEL = 5;
const STAT_LABEL_IT = {
    strength: "STR",
    agility: "AGI",
    intellect: "INT",
    endurance: "END",
    faith: "FAI",
};

export default function Training() {
    const { t, lang } = useT();
    const { refreshGuild } = useAuth();
    const [catalog, setCatalog] = useState(null);
    const [adventurers, setAdventurers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedAdv, setSelectedAdv] = useState(null);
    const [selectedSpec, setSelectedSpec] = useState(null);
    const [applying, setApplying] = useState(false);
    // ROUND 6E — Respec state
    const [respecAdv, setRespecAdv] = useState(null);
    const [respecSubmitting, setRespecSubmitting] = useState(false);

    async function refresh() {
        setLoading(true);
        try {
            const [catR, advR] = await Promise.all([
                api.get("/training/catalog"),
                api.get("/adventurers"),
            ]);
            setCatalog(catR.data);
            setAdventurers(
                (advR.data?.adventurers || []).filter((a) => !a.is_retired)
            );
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        refresh();
    }, []);

    const eligibleAdvs = useMemo(() => {
        return adventurers.filter(
            (a) => (a.level || 1) >= MIN_LEVEL && !a.specialization
        );
    }, [adventurers]);
    const specializedAdvs = useMemo(
        () => adventurers.filter((a) => a.specialization),
        [adventurers]
    );

    const isUnlocked = catalog?.tier != null;
    const trainingLv = catalog?.training_grounds_level || 0;

    async function doApply() {
        if (!selectedAdv || !selectedSpec) return;
        setApplying(true);
        try {
            await api.post(`/training/specialize/${selectedAdv.id}`, {
                spec_slug: selectedSpec.slug,
            });
            toast.success(
                lang === "it"
                    ? `✦ ${selectedAdv.name} è ora ${selectedSpec.name_it}!`
                    : `✦ ${selectedAdv.name} is now a ${selectedSpec.name_en}!`
            );
            setSelectedAdv(null);
            setSelectedSpec(null);
            await refresh();
            await refreshGuild();
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setApplying(false);
        }
    }

    async function doRespec({ new_spec_slug, discard_signature_items }) {
        if (!respecAdv) return;
        setRespecSubmitting(true);
        try {
            const r = await api.post(`/training/respec/${respecAdv.id}`, {
                new_spec_slug,
                discard_signature_items,
            });
            const newName = r.data?.specialization?.name_it || new_spec_slug;
            toast.success(
                lang === "it"
                    ? `✦ ${respecAdv.name} ora è ${newName}!`
                    : `✦ ${respecAdv.name} is now ${newName}!`
            );
            setRespecAdv(null);
            await refresh();
            await refreshGuild();
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setRespecSubmitting(false);
        }
    }

    return (
        <div className="min-h-screen bg-background text-foreground">
            <AppHeader subtitleKey="nav.brand_subtitle_dashboard" />
            <main
                className="max-w-6xl mx-auto px-4 sm:px-6 py-6 font-mono"
                data-testid="training-page"
            >
                <header className="mb-6">
                    <div className="text-[10px] text-amber tracking-widest mb-2">
                        :: {t("training.title", "CAMPO DI ADDESTRAMENTO")}
                    </div>
                    <h1 className="text-3xl font-semibold tracking-tight">
                        {t("training.page_title", "Addestramento")}
                    </h1>
                    <p className="text-[12px] text-muted-foreground mt-2 max-w-2xl">
                        {t(
                            "training.page_intro",
                            "Specializza i tuoi avventurieri (Lv5+) in un ruolo dedicato. Ogni specializzazione fornisce un bonus permanente alle statistiche e un signature item legato all'avventuriero."
                        )}
                    </p>
                </header>

                {loading ? (
                    <div
                        data-testid="training-loading"
                        className="text-muted-foreground text-sm"
                    >
                        {t("common.loading")}
                    </div>
                ) : !isUnlocked ? (
                    <LockedBanner t={t} />
                ) : (
                    <>
                        <CatalogHeader catalog={catalog} t={t} />
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-4">
                            <EligibleColumn
                                advs={eligibleAdvs}
                                onPickAdv={(a) => {
                                    setSelectedAdv(a);
                                    setSelectedSpec(null);
                                }}
                                selectedAdv={selectedAdv}
                                t={t}
                                lang={lang}
                            />
                            <SpecColumn
                                catalog={catalog}
                                selectedAdv={selectedAdv}
                                selectedSpec={selectedSpec}
                                onPickSpec={setSelectedSpec}
                                t={t}
                                lang={lang}
                            />
                        </div>
                        {specializedAdvs.length > 0 && (
                            <SpecializedList
                                advs={specializedAdvs}
                                onPickRespec={setRespecAdv}
                                t={t}
                                lang={lang}
                            />
                        )}
                    </>
                )}

                {selectedAdv && selectedSpec && (
                    <ConfirmModal
                        adv={selectedAdv}
                        spec={selectedSpec}
                        cost={catalog.apply_cost_gold}
                        onClose={() => setSelectedSpec(null)}
                        onConfirm={doApply}
                        applying={applying}
                        t={t}
                        lang={lang}
                    />
                )}

                {respecAdv && (
                    <RespecModal
                        adv={respecAdv}
                        catalog={catalog}
                        onClose={() => setRespecAdv(null)}
                        onSubmit={doRespec}
                        submitting={respecSubmitting}
                        lang={lang}
                    />
                )}
            </main>
        </div>
    );
}

function LockedBanner({ t }) {
    return (
        <div
            data-testid="training-locked-banner"
            className="border border-amber/40 bg-amber/5 rounded-sm p-6 text-center"
        >
            <div className="text-amber text-sm tracking-widest mb-3">
                🔒 {t("training.locked_title", "CAMPO DI ADDESTRAMENTO NON SBLOCCATO")}
            </div>
            <p className="text-[12px] text-muted-foreground mb-4 max-w-md mx-auto">
                {t(
                    "training.locked_desc",
                    "Sblocca il Campo di Addestramento dal Territorio (richiede Guild Hall Lv3 + Dormitori Lv2) per specializzare i tuoi avventurieri."
                )}
            </p>
            <Link
                to="/territory"
                data-testid="training-go-territory"
                className="inline-block text-[11px] tracking-widest border border-amber text-amber px-4 py-2 rounded-sm hover:bg-amber/10"
            >
                → {t("training.go_territory", "VAI AL TERRITORIO")}
            </Link>
        </div>
    );
}

function CatalogHeader({ catalog, t }) {
    return (
        <div
            data-testid="training-catalog-header"
            className="border border-border bg-card rounded-sm p-4 flex flex-wrap items-center justify-between gap-3 text-[11px]"
        >
            <div>
                <span className="text-muted-foreground tracking-widest">
                    {t("training.tg_level_label", "Campo di Addestramento")}:
                </span>{" "}
                <span className="text-amber font-bold">Lv{catalog.training_grounds_level}</span>
                <span className="mx-2 text-muted-foreground/40">·</span>
                <span className="text-muted-foreground tracking-widest">
                    {t("training.tier_label", "Tier")}:
                </span>{" "}
                <span
                    className="text-amber font-bold"
                    data-testid="training-tier-label"
                >
                    {catalog.tier === "starter" ? "STARTER" : "FULL HYBRID"}
                </span>
            </div>
            <div className="text-muted-foreground">
                <span className="tracking-widest">
                    {t("training.apply_cost_label", "Costo applicazione")}:
                </span>{" "}
                <span
                    className="text-amber font-bold"
                    data-testid="training-cost-display"
                >
                    {catalog.apply_cost_gold}g
                </span>
            </div>
        </div>
    );
}

function EligibleColumn({ advs, onPickAdv, selectedAdv, t, lang }) {
    return (
        <div className="border border-border bg-card rounded-sm p-4">
            <h2 className="text-[10px] text-amber tracking-widest mb-3">
                :: {t("training.eligible_title", "AVVENTURIERI ELEGGIBILI")}
                <span className="text-muted-foreground/60 ml-2">({advs.length})</span>
            </h2>
            {advs.length === 0 ? (
                <div
                    data-testid="training-no-eligible"
                    className="text-[11px] text-muted-foreground py-6 text-center"
                >
                    {t(
                        "training.no_eligible",
                        "Nessun avventuriero Lv5+ disponibile. Continua le spedizioni per fare livello."
                    )}
                </div>
            ) : (
                <ul className="space-y-1" data-testid="training-eligible-list">
                    {advs.map((a) => {
                        const isSel = selectedAdv?.id === a.id;
                        return (
                            <li key={a.id}>
                                <button
                                    type="button"
                                    onClick={() => onPickAdv(a)}
                                    data-testid={`training-eligible-${a.id}`}
                                    className={`w-full text-left px-3 py-2 text-[12px] rounded-sm border transition-colors ${
                                        isSel
                                            ? "border-amber bg-amber/10 text-foreground"
                                            : "border-transparent hover:border-border hover:bg-secondary/30 text-foreground/90"
                                    }`}
                                >
                                    <div className="flex items-center justify-between gap-2">
                                        <span>
                                            <span className="font-bold">{a.name}</span>
                                            <span className="text-muted-foreground ml-2">
                                                {a.class_name} · Lv{a.level}
                                            </span>
                                        </span>
                                        <span className="text-amber text-[10px]">
                                            PWR {a.total_power}
                                        </span>
                                    </div>
                                </button>
                            </li>
                        );
                    })}
                </ul>
            )}
            <div className="text-[10px] text-muted-foreground mt-3 border-t border-border pt-2">
                {lang === "it"
                    ? `Requisiti: Lv${MIN_LEVEL}+ e non già specializzato.`
                    : `Requirements: Lv${MIN_LEVEL}+ and not already specialized.`}
            </div>
        </div>
    );
}

function SpecColumn({ catalog, selectedAdv, selectedSpec, onPickSpec, t, lang }) {
    const advClass = selectedAdv?.class_slug;
    const specs = catalog.specs || [];
    return (
        <div className="border border-border bg-card rounded-sm p-4">
            <h2 className="text-[10px] text-amber tracking-widest mb-3">
                :: {t("training.spec_title", "SPECIALIZZAZIONI DISPONIBILI")}
                <span className="text-muted-foreground/60 ml-2">({specs.length})</span>
            </h2>
            {!selectedAdv ? (
                <div className="text-[11px] text-muted-foreground py-6 text-center">
                    {t(
                        "training.spec_pick_first",
                        "Seleziona prima un avventuriero per vedere le specializzazioni compatibili."
                    )}
                </div>
            ) : (
                <ul className="space-y-2" data-testid="training-spec-list">
                    {specs.map((s) => {
                        const eligible = s.eligible_classes.includes(advClass);
                        const isSel = selectedSpec?.slug === s.slug;
                        return (
                            <li key={s.slug}>
                                <button
                                    type="button"
                                    disabled={!eligible}
                                    onClick={() => eligible && onPickSpec(s)}
                                    data-testid={`training-spec-${s.slug}`}
                                    title={
                                        eligible
                                            ? ""
                                            : lang === "it"
                                            ? `Richiede classe: ${s.eligible_classes.join(", ")}`
                                            : `Requires class: ${s.eligible_classes.join(", ")}`
                                    }
                                    className={`w-full text-left p-3 rounded-sm border transition-colors ${
                                        !eligible
                                            ? "border-border bg-secondary/10 text-muted-foreground/40 cursor-not-allowed"
                                            : isSel
                                            ? "border-amber bg-amber/10 text-foreground"
                                            : "border-border hover:border-amber/60 hover:bg-secondary/30 text-foreground/90"
                                    }`}
                                >
                                    <div className="flex items-center justify-between mb-1">
                                        <span className="font-bold text-[12px]">
                                            {lang === "it" ? s.name_it : s.name_en}
                                        </span>
                                        <span className="text-[10px] text-amber tracking-widest">
                                            {s.tier === "starter" ? "STARTER" : "FULL"} · {s.role}
                                        </span>
                                    </div>
                                    <div className="text-[10px] text-muted-foreground">
                                        {lang === "it" ? s.description_it : s.description_en}
                                    </div>
                                    <div className="text-[10px] text-foreground/70 mt-1">
                                        {Object.entries(s.modifiers || {}).map(([k, v]) => (
                                            <span
                                                key={k}
                                                className="inline-block mr-2 text-amber/90"
                                            >
                                                +{v} {STAT_LABEL_IT[k] || k.toUpperCase()}
                                            </span>
                                        ))}
                                    </div>
                                </button>
                            </li>
                        );
                    })}
                </ul>
            )}
        </div>
    );
}

function SpecializedList({ advs, onPickRespec, t, lang }) {
    return (
        <div className="mt-6 border border-border bg-card rounded-sm p-4">
            <h2 className="text-[10px] text-amber tracking-widest mb-3">
                :: {t("training.specialized_title", "AVVENTURIERI GIÀ SPECIALIZZATI")}
                <span className="text-muted-foreground/60 ml-2">({advs.length})</span>
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {advs.map((a) => (
                    <div
                        key={a.id}
                        data-testid={`training-specialized-${a.id}`}
                        className="border border-border/60 rounded-sm p-2 text-[11px] flex items-center justify-between gap-2"
                    >
                        <div className="min-w-0">
                            <div className="font-bold text-foreground/90 truncate">{a.name}</div>
                            <div className="text-muted-foreground">
                                {a.class_name} · Lv{a.level}
                            </div>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                            <span
                                data-testid={`training-spec-badge-${a.id}`}
                                className="text-[10px] tracking-widest border border-amber/60 text-amber px-2 py-0.5 rounded-sm whitespace-nowrap"
                            >
                                ✦ {lang === "it"
                                    ? a.specialization?.name_it
                                    : a.specialization?.name_en}
                            </span>
                            <button
                                type="button"
                                onClick={() => onPickRespec(a)}
                                data-testid={`training-respec-btn-${a.id}`}
                                className="text-[10px] tracking-widest border border-border text-muted-foreground hover:border-amber hover:text-amber px-2 py-0.5 rounded-sm whitespace-nowrap transition-colors"
                                title={t("training.respec_btn_title", "Cambia specializzazione (con costo + cooldown)")}
                            >
                                ⟲ {t("training.respec_btn", "Respec")}
                            </button>
                        </div>
                    </div>
                ))}
            </div>
            <div className="text-[10px] text-muted-foreground mt-3 border-t border-border pt-2">
                {t(
                    "training.respec_note_6e",
                    "ROUND 6E — Respec disponibile: costo crescente (800/1200/2000g + polvere arcana), cooldown 24h, signature item attuale viene distrutto."
                )}
            </div>
        </div>
    );
}

function ConfirmModal({ adv, spec, cost, onClose, onConfirm, applying, t, lang }) {
    const sigItem = SPEC_SIG_PREVIEW[spec.signature_item_slug] || {};
    return (
        <div
            data-testid="training-confirm-modal"
            className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4"
            onClick={onClose}
        >
            <div
                onClick={(e) => e.stopPropagation()}
                className="max-w-md w-full border border-amber bg-card rounded-sm p-5 text-[12px] space-y-4"
            >
                <h3 className="text-amber tracking-widest text-[11px] mb-2">
                    :: {t("training.confirm_title", "CONFERMA SPECIALIZZAZIONE")}
                </h3>
                <div>
                    <div className="text-muted-foreground tracking-widest text-[10px]">
                        {t("training.confirm_target", "Avventuriero")}
                    </div>
                    <div className="text-foreground font-bold">
                        {adv.name}
                        <span className="text-muted-foreground ml-2">
                            ({adv.class_name} · Lv{adv.level})
                        </span>
                    </div>
                </div>
                <div>
                    <div className="text-muted-foreground tracking-widest text-[10px]">
                        {t("training.confirm_spec", "Specializzazione")}
                    </div>
                    <div className="text-amber font-bold">
                        ✦ {lang === "it" ? spec.name_it : spec.name_en}
                    </div>
                    <div className="text-foreground/70 mt-1">
                        {Object.entries(spec.modifiers || {}).map(([k, v]) => (
                            <span key={k} className="inline-block mr-2 text-amber/90">
                                +{v} {STAT_LABEL_IT[k] || k.toUpperCase()}
                            </span>
                        ))}
                    </div>
                </div>
                <div>
                    <div className="text-muted-foreground tracking-widest text-[10px]">
                        {t("training.confirm_signature", "Signature Item (legato)")}
                    </div>
                    <div className="text-orange-300 font-bold">
                        ⚔ {sigItem.name_it || spec.signature_item_slug}
                        {sigItem.rarity ? (
                            <span className="text-[10px] ml-2 text-muted-foreground">
                                ({sigItem.rarity})
                            </span>
                        ) : null}
                    </div>
                </div>
                <div className="text-[10px] text-amber/70 border-t border-border pt-2">
                    ⚠ {t(
                        "training.respec_warning",
                        "La specializzazione è PERMANENTE in Round 6C. Il respec non sarà disponibile fino a Round 6D."
                    )}
                </div>
                <div className="flex items-center justify-between gap-2 pt-2">
                    <button
                        type="button"
                        onClick={onClose}
                        disabled={applying}
                        data-testid="training-cancel-btn"
                        className="px-3 py-1.5 text-[11px] tracking-widest border border-border text-muted-foreground rounded-sm hover:border-foreground"
                    >
                        {t("common.cancel")}
                    </button>
                    <button
                        type="button"
                        onClick={onConfirm}
                        disabled={applying}
                        data-testid="training-confirm-btn"
                        className="px-3 py-1.5 text-[11px] tracking-widest border border-amber text-amber rounded-sm hover:bg-amber/10 disabled:opacity-50"
                    >
                        {applying ? "…" : `${t("training.confirm_apply", "APPLICA")} — ${cost}g`}
                    </button>
                </div>
            </div>
        </div>
    );
}

// Minimal preview of the signature item names (server is authoritative; this
// is a UX nicety so the modal doesn't show a slug). Catalog mirrors the
// backend SPEC_SIGNATURE_ITEMS table.
const SPEC_SIG_PREVIEW = {
    spec_signature_aegis_of_the_defender: { name_it: "Egida del Difensore", rarity: "Rare" },
    spec_signature_truestrike_bow: { name_it: "Arco del Colpo Vero", rarity: "Rare" },
    spec_signature_sacred_chalice: { name_it: "Calice Sacro", rarity: "Rare" },
    spec_signature_battle_standard: { name_it: "Stendardo da Battaglia", rarity: "Rare" },
    spec_signature_bloodied_greataxe: { name_it: "Grand'Ascia Insanguinata", rarity: "Epic" },
    spec_signature_breakers_gauntlets: { name_it: "Manopole del Sfondatore", rarity: "Epic" },
    spec_signature_silent_kris: { name_it: "Kris Silente", rarity: "Epic" },
    spec_signature_runed_focus: { name_it: "Focus Runico", rarity: "Epic" },
    spec_signature_storm_rod: { name_it: "Bastone della Tempesta", rarity: "Epic" },
    spec_signature_warhorn: { name_it: "Corno di Guerra", rarity: "Epic" },
};
