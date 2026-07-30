// Crafting page — Phase 14.6 (ROUND 3.B).
// Lists recipes with per-guild eligibility and exposes a one-click craft
// action. Backend is /api/recipes + POST /api/recipes/{slug}/craft.
import { useCallback, useEffect, useState } from "react";
import { api, formatApiError } from "../lib/api";
import { toast } from "sonner";
import AppHeader from "../components/AppHeader";
import { Button } from "../components/ui/button";
import { useT } from "../i18n/I18nContext";

const RARITY_COLOR = {
    Common: "#9ca3af",
    Uncommon: "#22c55e",
    Rare: "#3b82f6",
    Epic: "#a855f7",
    Legendary: "#f59e0b",
    Unique: "#ef4444",
};

const STATUS_COLOR = {
    craftable: "#22c55e",
    missing_materials: "#f59e0b",
    insufficient_gold: "#f59e0b",
    requires_level: "#9ca3af",
};

function RarityChip({ rarity }) {
    const c = RARITY_COLOR[rarity] || RARITY_COLOR.Common;
    return (
        <span
            className="inline-block text-[10px] tracking-widest border px-1.5 py-0.5 rounded-sm"
            style={{ color: c, borderColor: c + "55" }}
        >
            {(rarity || "").toUpperCase()}
        </span>
    );
}

export default function Crafting() {
    const { t, lang } = useT();
    const [recipes, setRecipes] = useState(null);
    const [loading, setLoading] = useState(true);
    const [busy, setBusy] = useState(null);

    // ROUND 6B FASE B — useCallback so identity is stable and the effect
    // below can list `refresh` directly (no eslint-disable needed). Reloads
    // when `lang` changes so recipe names re-localize on the fly.
    const refresh = useCallback(async () => {
        try {
            const r = await api.get(`/recipes?lang=${lang}`);
            setRecipes(r.data.recipes || []);
        } catch (err) {
            toast.error(formatApiError(err));
            setRecipes([]);
        } finally {
            setLoading(false);
        }
    }, [lang]);

    useEffect(() => {
        refresh();
    }, [refresh]);

    const doCraft = async (slug) => {
        setBusy(slug);
        try {
            const r = await api.post(`/recipes/${slug}/craft?lang=${lang}`);
            const out = r.data.output_item;
            toast.success(
                `${t("crafting.toast_crafted")}: ${out.name} × ${out.quantity}`
            );
            await refresh();
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setBusy(null);
        }
    };

    return (
        <div className="min-h-screen bg-background text-foreground term-grid-bg">
            <AppHeader subtitleKey="nav.crafting" />
            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
                <div className="mb-6">
                    <div className="text-xs text-amber tracking-widest mb-2">
                        :: GUILD WORKSHOP
                    </div>
                    <h1 className="text-3xl font-semibold tracking-tight">
                        {t("crafting.title")}
                    </h1>
                    <p className="text-sm text-muted-foreground mt-2 max-w-2xl">
                        {t("crafting.subtitle")}
                    </p>
                </div>

                {loading && (
                    <div className="text-xs text-muted-foreground">
                        loading<span className="caret-blink" />
                    </div>
                )}

                {!loading && recipes && recipes.length === 0 && (
                    <div
                        data-testid="crafting-empty"
                        className="border border-border bg-card rounded-sm p-10 text-center text-sm text-muted-foreground"
                    >
                        {t("crafting.empty")}
                    </div>
                )}

                {!loading && recipes && recipes.length > 0 && (
                    <div className="space-y-3" data-testid="crafting-list">
                        {recipes.map((r) => {
                            const color = STATUS_COLOR[r.status] || "#9ca3af";
                            return (
                                <div
                                    key={r.slug}
                                    data-testid={`recipe-card-${r.slug}`}
                                    className="border border-border bg-card rounded-sm p-4"
                                >
                                    <div className="flex items-start justify-between gap-3 flex-wrap">
                                        <div className="min-w-0">
                                            <div className="font-medium flex items-center gap-2 flex-wrap">
                                                <span data-testid={`recipe-name-${r.slug}`}>
                                                    {r.display_name}
                                                </span>
                                                <RarityChip rarity={r.output.rarity} />
                                            </div>
                                            <p className="text-[11px] text-muted-foreground mt-1">
                                                {r.description}
                                            </p>
                                        </div>
                                        <span
                                            data-testid={`recipe-status-${r.slug}`}
                                            className="text-[10px] tracking-widest border px-2 py-1 rounded-sm whitespace-nowrap"
                                            style={{ color, borderColor: color + "55" }}
                                        >
                                            {t(`crafting.status_${r.status}`)}
                                        </span>
                                    </div>

                                    <div className="mt-3 pt-3 border-t border-border/60 grid grid-cols-1 sm:grid-cols-2 gap-3 text-[12px]">
                                        <div data-testid={`recipe-inputs-${r.slug}`}>
                                            <div className="text-[10px] text-muted-foreground tracking-widest mb-1">
                                                {t("crafting.inputs")}
                                            </div>
                                            <ul className="space-y-1">
                                                {r.inputs.map((i) => {
                                                    const miss = r.missing[i.item_slug] || 0;
                                                    return (
                                                        <li
                                                            key={i.item_slug}
                                                            className={miss ? "text-amber" : ""}
                                                        >
                                                            • {i.item_name} × {i.quantity}
                                                            {miss > 0 && (
                                                                <span className="text-amber/90 ml-1">
                                                                    ({t("crafting.missing")} {miss})
                                                                </span>
                                                            )}
                                                        </li>
                                                    );
                                                })}
                                                <li>
                                                    • {t("crafting.gold_cost")}: {r.gold_cost}g
                                                    {r.gold_short > 0 && (
                                                        <span className="text-amber/90 ml-1">
                                                            ({t("crafting.short")} {r.gold_short})
                                                        </span>
                                                    )}
                                                </li>
                                            </ul>
                                        </div>
                                        <div>
                                            <div className="text-[10px] text-muted-foreground tracking-widest mb-1">
                                                {t("crafting.output")}
                                            </div>
                                            <div className="text-sm">
                                                {r.output.name} × {r.output.quantity}
                                            </div>
                                            <div className="text-[10px] text-muted-foreground mt-1">
                                                {t("crafting.req_guild_level", {
                                                    n: r.required_guild_level,
                                                })}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="mt-3 pt-3 border-t border-border/60">
                                        <Button
                                            data-testid={`craft-btn-${r.slug}`}
                                            disabled={
                                                r.status !== "craftable" || busy === r.slug
                                            }
                                            onClick={() => doCraft(r.slug)}
                                            className="bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-40 rounded-sm h-8 px-3 text-xs"
                                            title={
                                                r.status !== "craftable"
                                                    ? t(`crafting.status_${r.status}`)
                                                    : ""
                                            }
                                        >
                                            {busy === r.slug
                                                ? t("crafting.crafting")
                                                : `▶ ${t("crafting.craft")}`}
                                        </Button>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </main>
        </div>
    );
}
