// Phase 13.1 — lazy trait effect preview widget.
// Consumes GET /api/adventurers/{id}/trait-preview only on expansion to avoid
// N+1 fetch on the roster page.
import { useState, useCallback } from "react";
import { getTraitPreview, formatApiError } from "../lib/api";
import { useT } from "../i18n/I18nContext";

const STAT_KEYS = ["strength", "agility", "intellect", "endurance", "faith"];

function statLabel(stat, tContent, fallback) {
    return tContent("stat", stat, "name", fallback || stat);
}

function deltaText(trait, tContent, t) {
    const mtype = trait.modifier_type;
    const val = trait.modifier_value;
    const affected = trait.affected_stat;
    const sign = val >= 0 ? "+" : "";
    if (STAT_KEYS.includes(affected) && mtype === "flat") {
        return `${sign}${val} ${statLabel(affected, tContent, affected)}`;
    }
    if (STAT_KEYS.includes(affected) && mtype === "percent") {
        return `${sign}${val}% ${statLabel(affected, tContent, affected)}`;
    }
    if (affected === "xp_gain" && mtype === "percent") {
        return `${sign}${val}% ${t("adventurers.traits.xp_gain_short")}`;
    }
    return t("adventurers.traits.no_effect");
}

export default function TraitPreviewWidget({ adventurerId, hasTraits }) {
    const { t, tContent } = useT();
    const [open, setOpen] = useState(false);
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchPreview = useCallback(async () => {
        if (data || loading) return;
        setLoading(true);
        setError(null);
        try {
            const res = await getTraitPreview(adventurerId);
            setData(res);
        } catch (err) {
            setError(formatApiError(err));
        } finally {
            setLoading(false);
        }
    }, [adventurerId, data, loading]);

    const onToggle = () => {
        const next = !open;
        setOpen(next);
        if (next) fetchPreview();
    };

    return (
        <div
            data-testid={`trait-preview-widget-${adventurerId}`}
            className="mt-2"
        >
            <button
                type="button"
                onClick={onToggle}
                data-testid={`trait-preview-toggle-${adventurerId}`}
                className="text-[10px] text-muted-foreground hover:text-amber tracking-widest"
            >
                {open ? "▾" : "▸"} {t("adventurers.traits.trait_effects")}
            </button>
            {open && (
                <div
                    data-testid={`trait-preview-body-${adventurerId}`}
                    className="mt-2 border border-border/60 bg-card/40 rounded-sm p-3 font-mono text-[11px] leading-relaxed"
                >
                    {loading && (
                        <div className="text-muted-foreground">
                            :: {t("adventurers.traits.loading")}
                            <span className="caret-blink" />
                        </div>
                    )}
                    {error && !loading && (
                        <div
                            data-testid={`trait-preview-error-${adventurerId}`}
                            className="text-red-400/80"
                        >
                            :: {t("adventurers.traits.unavailable")}
                        </div>
                    )}
                    {data && !loading && !error && (
                        <TraitPreviewBody
                            data={data}
                            adventurerId={adventurerId}
                            t={t}
                            tContent={tContent}
                            hasTraits={hasTraits}
                        />
                    )}
                </div>
            )}
        </div>
    );
}

function TraitPreviewBody({ data, adventurerId, t, tContent }) {
    const active = (data.applied_traits || []).filter(
        (tr) => tr.delta_summary && tr.delta_summary !== "no effect",
    );
    const flavor = (data.applied_traits || []).filter(
        (tr) => !tr.delta_summary || tr.delta_summary === "no effect",
    );
    const allFlavor = active.length === 0 && (data.xp_gain_percent || 0) === 0;

    if (allFlavor && (data.power_delta || 0) === 0) {
        return (
            <div data-testid={`trait-preview-empty-${adventurerId}`}>
                <div className="text-muted-foreground/80 mb-1">
                    :: {t("adventurers.traits.section_title")}
                </div>
                <div>{t("adventurers.traits.no_effects")}</div>
                {flavor.length > 0 && (
                    <div className="mt-2 text-muted-foreground">
                        {flavor.map((tr) => (
                            <div key={tr.id || tr.name}>
                                · {tContent("trait", traitSlug(tr.name), "name", tr.name)}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        );
    }

    return (
        <div>
            <div className="text-muted-foreground/80 mb-1">
                :: {t("adventurers.traits.section_title")}
            </div>
            <div className="grid grid-cols-1 gap-y-0.5">
                <div className="flex justify-between gap-3">
                    <span className="text-muted-foreground">
                        {t("adventurers.traits.base_power")}
                    </span>
                    <span data-testid={`trait-preview-base-${adventurerId}`}>
                        {data.base_power}
                    </span>
                </div>
                <div className="flex justify-between gap-3">
                    <span className="text-muted-foreground">
                        {t("adventurers.traits.effective_power")}
                    </span>
                    <span
                        data-testid={`trait-preview-effective-${adventurerId}`}
                        className={
                            data.power_delta > 0
                                ? "text-[#22c55e]"
                                : data.power_delta < 0
                                  ? "text-[#ef4444]"
                                  : ""
                        }
                    >
                        {data.power_delta > 0 ? "+" : ""}
                        {data.power_delta} → {data.effective_power}
                    </span>
                </div>
                {(data.xp_gain_percent || 0) !== 0 && (
                    <div className="flex justify-between gap-3">
                        <span className="text-muted-foreground">
                            {t("adventurers.traits.xp_gain")}
                        </span>
                        <span
                            data-testid={`trait-preview-xp-${adventurerId}`}
                            className={
                                data.xp_gain_percent > 0 ? "text-[#22c55e]" : "text-[#ef4444]"
                            }
                        >
                            {data.xp_gain_percent > 0 ? "+" : ""}
                            {data.xp_gain_percent}%
                        </span>
                    </div>
                )}
            </div>
            {active.length > 0 && (
                <div className="mt-2">
                    <div className="text-muted-foreground/80">
                        {t("adventurers.traits.active_modifiers")}
                    </div>
                    {active.map((tr) => (
                        <div
                            key={tr.id || tr.name}
                            data-testid={`trait-preview-active-${tr.name?.toLowerCase().replace(/\s+/g, "-")}`}
                        >
                            · {tContent("trait", traitSlug(tr.name), "name", tr.name)}{" "}
                            <span className="text-muted-foreground">
                                {localizedDelta(tr, t, tContent)}
                            </span>
                        </div>
                    ))}
                </div>
            )}
            {flavor.length > 0 && (
                <div className="mt-2">
                    <div className="text-muted-foreground/80">
                        {t("adventurers.traits.flavor_traits")}
                    </div>
                    {flavor.map((tr) => (
                        <div key={tr.id || tr.name} className="text-muted-foreground">
                            · {tContent("trait", traitSlug(tr.name), "name", tr.name)}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

// Backend trait names like "Brave", "Iron-Willed", "Quick Learner" → slugs
// matching the content.trait.<slug> keys: lowercase, spaces→underscores,
// hyphens kept verbatim (e.g. iron-willed).
function traitSlug(name) {
    if (!name) return "";
    return String(name).toLowerCase().replace(/\s+/g, "_");
}

function localizedDelta(tr, t, tContent) {
    return deltaText(tr, tContent, t);
}
