// ROUND 6B.2b — /territory page. 11-card grid with 6 states + Legacy.
// ROUND 11.2 EXT-2 — Inline CostBreakdown + Material lookup modal so the
// player can see required-vs-owned (gold + materials) before clicking
// Potenzia, and tap a material to learn where to farm it.
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import AppHeader from "../components/AppHeader";
import OverCapBanner from "../components/OverCapBanner";
import CostBreakdown from "../components/territory/CostBreakdown";
import MaterialSourceModal from "../components/territory/MaterialSourceModal";
import { api, formatApiError } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { useT } from "../i18n/I18nContext";
import {
    DORM_CAP_BY_LEVEL,
    STRUCTURE_SLUGS,
    getStructureDescription,
    getStructureName,
    resolveCardState,
} from "../utils/structures";

function GoldPill({ value }) {
    return (
        <span className="text-amber font-bold">{value}g</span>
    );
}

function StructureCard({ slug, structure, structures, gold, lang, busy, onPurchase, onUpgrade, onMaterialClick }) {
    const state = useMemo(
        () => resolveCardState({ slug, structure, structures, gold }),
        [slug, structure, structures, gold],
    );
    const name = getStructureName(slug, lang);
    const desc = getStructureDescription(slug, lang);
    const level = state.level;
    const isLegacy = state.kind === "legacy";

    const isLocked = state.kind === "locked_prereq";
    const isMax = state.kind === "max";
    const isBuyable = state.kind === "buyable";
    const isUpgradable = state.kind === "upgradable";
    const isInsufficient = state.kind === "insufficient_gold";

    // ROUND 11.2 EXT-2 — Backend-driven affordability check. Strict
    // `=== false` guard: if `can_afford` is undefined (legacy cards
    // pre-enrichment) we DO NOT disable, otherwise we'd silently lock
    // upgrades the player could actually pay for.
    const nextLevelCost = structure?.next_level_cost || null;
    const blockedByMaterials = (
        nextLevelCost !== null
        && nextLevelCost?.can_afford === false
        && isUpgradable // gold-side already covered by insufficient_gold
    );

    let cta = null;
    if (isLegacy) {
        cta = (
            <button
                disabled
                title={lang === "it"
                    ? "Sbloccata da migrazione storica. Non potenziabile."
                    : "Unlocked by legacy migration. Not upgradable."}
                data-testid={`territory-card-${slug}-cta`}
                className="w-full mt-3 px-3 py-2 text-xs tracking-widest font-bold bg-amber/20 text-amber border border-amber/30 rounded-sm cursor-not-allowed"
            >
                👑 {lang === "it" ? "LEGACY" : "LEGACY"}
            </button>
        );
    } else if (isMax) {
        cta = (
            <button
                disabled
                data-testid={`territory-card-${slug}-cta`}
                className="w-full mt-3 px-3 py-2 text-xs tracking-widest font-bold border border-border text-muted-foreground rounded-sm cursor-not-allowed"
            >
                {lang === "it" ? "Livello massimo" : "Max level reached"}
            </button>
        );
    } else if (isLocked) {
        const reqs = state.unmet.map((u) => `${getStructureName(u.slug, lang)} Lv${u.min_level}`).join(", ");
        cta = (
            <button
                disabled
                title={reqs}
                data-testid={`territory-card-${slug}-cta`}
                className="w-full mt-3 px-3 py-2 text-xs tracking-widest font-bold border border-border text-muted-foreground rounded-sm cursor-not-allowed"
            >
                🔒 {lang === "it" ? "Sblocca prima" : "Unlock first"}: {reqs}
            </button>
        );
    } else if (isBuyable || isUpgradable) {
        const verb = isBuyable
            ? (lang === "it" ? "▶ Compra" : "▶ Buy")
            : (lang === "it" ? "▶ Potenzia a Lv" : "▶ Upgrade to Lv");
        const disabled = busy || blockedByMaterials;
        const title = blockedByMaterials
            ? (lang === "it" ? "Materiali insufficienti" : "Not enough materials")
            : undefined;
        cta = (
            <button
                disabled={disabled}
                title={title}
                onClick={() => (isBuyable ? onPurchase(slug) : onUpgrade(slug))}
                data-testid={`territory-card-${slug}-cta`}
                className={`w-full mt-3 px-3 py-2 text-xs tracking-widest font-bold rounded-sm transition-opacity ${
                    blockedByMaterials
                        ? "border border-border text-muted-foreground cursor-not-allowed bg-secondary/40"
                        : "bg-amber text-background hover:opacity-90 disabled:opacity-50 disabled:cursor-wait"
                }`}
            >
                {verb} {isUpgradable ? state.targetLevel : ""} ({state.goldNeeded || state.cost?.gold || 0}g)
            </button>
        );
    } else if (isInsufficient) {
        const missing = (state.goldNeeded || 0) - (gold || 0);
        cta = (
            <button
                disabled
                title={lang === "it" ? `Gold mancanti: ${missing}` : `Missing gold: ${missing}`}
                data-testid={`territory-card-${slug}-cta`}
                className="w-full mt-3 px-3 py-2 text-xs tracking-widest font-bold border border-border text-muted-foreground rounded-sm cursor-not-allowed"
            >
                {lang === "it" ? "Gold insufficienti" : "Not enough gold"} ({state.goldNeeded}g)
            </button>
        );
    }

    // Special pill: dormitories show cap directly.
    const dormCap = slug === "dormitories" ? DORM_CAP_BY_LEVEL[level] || 0 : null;

    return (
        <div
            data-testid={`territory-card-${slug}`}
            className="border border-border bg-secondary/30 rounded-sm p-4 hover:border-amber/50 transition-colors"
        >
            <div className="flex items-start justify-between gap-3 mb-2">
                <h3 className="text-foreground font-bold text-sm tracking-wide" data-testid={`territory-card-${slug}-name`}>
                    {name}
                </h3>
                <span
                    className={`text-xs tracking-widest font-bold ${level > 0 ? "text-amber" : "text-muted-foreground"}`}
                    data-testid={`territory-card-${slug}-level`}
                >
                    Lv{level}{isLegacy ? " 👑" : ""}
                </span>
            </div>
            <p className="text-[11px] text-muted-foreground mb-2 leading-relaxed">{desc}</p>
            {dormCap !== null && level > 0 && (
                <div className="text-[11px] text-amber/80 mb-1">
                    {lang === "it" ? "Capienza" : "Capacity"}: {dormCap} {lang === "it" ? "avventurieri" : "adventurers"}
                </div>
            )}
            {nextLevelCost && (isUpgradable || isInsufficient || blockedByMaterials) && (
                <CostBreakdown
                    nextLevelCost={nextLevelCost}
                    lang={lang}
                    slug={slug}
                    onMaterialClick={onMaterialClick}
                />
            )}
            {cta}
        </div>
    );
}

export default function Territory() {
    const { t, lang } = useT();
    const { guild, refreshGuild } = useAuth();
    const [territory, setTerritory] = useState(null);
    const [loading, setLoading] = useState(true);
    const [busy, setBusy] = useState(false);
    // ROUND 11.2 EXT-2 — Shared material-lookup modal state.
    const [materialModalSlug, setMaterialModalSlug] = useState(null);

    const fetchTerritory = async () => {
        try {
            const { data } = await api.get("/territory");
            setTerritory(data.territory);
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchTerritory(); }, []);

    const doPurchase = async (slug) => {
        if (busy) return; // ROUND 6B.3 — defensive guard vs. fast double-click
        setBusy(true);
        try {
            const { data } = await api.post("/territory/purchase", { structure_slug: slug });
            setTerritory(data.territory);
            toast.success(`${getStructureName(slug, lang)} ${lang === "it" ? "sbloccata!" : "unlocked!"}`);
            refreshGuild();
        } catch (err) {
            const detail = err?.response?.data?.detail;
            if (detail?.code === "resources.gold_insufficient") {
                toast.error(lang === "it"
                    ? `Gold insufficiente: servono ${detail.required}, hai ${detail.available}`
                    : `Not enough gold: need ${detail.required}, you have ${detail.available}`);
            } else if (detail?.code === "resources.material_insufficient") {
                toast.error(lang === "it"
                    ? `Materiale insufficiente: ${detail.slug} (servono ${detail.required}, hai ${detail.available})`
                    : `Not enough ${detail.slug}: need ${detail.required}, you have ${detail.available}`);
            } else {
                toast.error(formatApiError(err));
            }
        } finally {
            setBusy(false);
        }
    };

    const doUpgrade = async (slug) => {
        if (busy) return; // ROUND 6B.3 — defensive guard vs. fast double-click
        setBusy(true);
        try {
            const { data } = await api.post("/territory/upgrade", { structure_slug: slug });
            setTerritory(data.territory);
            toast.success(`${getStructureName(slug, lang)} ${lang === "it" ? "potenziata!" : "upgraded!"}`);
            refreshGuild();
        } catch (err) {
            const detail = err?.response?.data?.detail;
            if (detail?.code === "resources.gold_insufficient") {
                toast.error(lang === "it"
                    ? `Gold insufficiente: servono ${detail.required}, hai ${detail.available}`
                    : `Not enough gold: need ${detail.required}, you have ${detail.available}`);
            } else if (detail?.code === "resources.material_insufficient") {
                toast.error(lang === "it"
                    ? `Materiale insufficiente: ${detail.slug} (servono ${detail.required}, hai ${detail.available})`
                    : `Not enough ${detail.slug}: need ${detail.required}, you have ${detail.available}`);
            } else {
                toast.error(formatApiError(err));
            }
        } finally {
            setBusy(false);
        }
    };

    const progress = useMemo(() => {
        if (!territory) return { sum: 0, max: 0, unlocked: 0 };
        let sum = 0;
        let unlocked = 0;
        const slugs = Object.keys(territory.structures || {});
        for (const slug of slugs) {
            const lvl = Number(territory.structures[slug]?.level || 0);
            sum += lvl;
            if (lvl >= 1) unlocked += 1;
        }
        return { sum, max: slugs.length * 6, unlocked, total: slugs.length };
    }, [territory]);

    return (
        <div className="min-h-screen bg-background text-foreground">
            <AppHeader subtitleKey="nav.brand_subtitle_dashboard" />
            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8" data-testid="territory-page">
                <OverCapBanner source="territory" />
                <div className="mb-6">
                    <h1 className="text-3xl font-semibold tracking-tight" data-testid="territory-title">
                        {lang === "it" ? "TERRITORIO" : "TERRITORY"}
                    </h1>
                    <p className="text-sm text-muted-foreground mt-1 max-w-2xl">
                        {lang === "it"
                            ? "Costruisci e potenzia le strutture della tua gilda per sbloccare nuove funzionalità."
                            : "Build and upgrade your guild's structures to unlock new features."}
                    </p>
                </div>

                {/* Top stats row */}
                {territory && (
                    <div className="border border-border bg-card rounded-sm p-4 mb-6 grid grid-cols-2 sm:grid-cols-4 gap-4" data-testid="territory-summary">
                        <div>
                            <div className="text-[10px] tracking-widest text-muted-foreground">
                                {lang === "it" ? "GILDA" : "GUILD"}
                            </div>
                            <div className="text-sm font-bold mt-1">{guild?.name}</div>
                        </div>
                        <div>
                            <div className="text-[10px] tracking-widest text-muted-foreground">
                                {lang === "it" ? "GOLD" : "GOLD"}
                            </div>
                            <div className="text-sm font-bold mt-1"><GoldPill value={guild?.gold || 0} /></div>
                        </div>
                        <div>
                            <div className="text-[10px] tracking-widest text-muted-foreground">
                                {lang === "it" ? "SBLOCCATE" : "UNLOCKED"}
                            </div>
                            <div className="text-sm font-bold mt-1" data-testid="territory-unlocked-count">
                                {progress.unlocked}/{progress.total}
                            </div>
                        </div>
                        <div>
                            <div className="text-[10px] tracking-widest text-muted-foreground">
                                {lang === "it" ? "PROGRESSO" : "PROGRESS"}
                            </div>
                            <div className="mt-1">
                                <div className="w-full bg-secondary h-2 rounded-sm overflow-hidden">
                                    <div
                                        className="bg-amber h-full transition-all"
                                        style={{ width: `${Math.min(100, Math.round((progress.sum / Math.max(progress.max, 1)) * 100))}%` }}
                                        data-testid="territory-progress-bar"
                                    />
                                </div>
                                <div className="text-[10px] text-muted-foreground mt-1">{progress.sum}/{progress.max}</div>
                            </div>
                        </div>
                    </div>
                )}

                {loading && <div className="text-xs text-muted-foreground">{t("common.loading", "Caricamento...")}</div>}

                {/* Grid 11 strutture */}
                {territory && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="territory-grid">
                        {STRUCTURE_SLUGS.map((slug) => (
                            <StructureCard
                                key={slug}
                                slug={slug}
                                structure={territory.structures[slug]}
                                structures={territory.structures}
                                gold={guild?.gold || 0}
                                lang={lang}
                                busy={busy}
                                onPurchase={doPurchase}
                                onUpgrade={doUpgrade}
                                onMaterialClick={setMaterialModalSlug}
                            />
                        ))}
                    </div>
                )}
            </main>
            <MaterialSourceModal
                slug={materialModalSlug}
                open={Boolean(materialModalSlug)}
                onOpenChange={(open) => { if (!open) setMaterialModalSlug(null); }}
                lang={lang}
            />
        </div>
    );
}
