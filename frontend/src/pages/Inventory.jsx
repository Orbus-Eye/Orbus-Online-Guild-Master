// Inventory page — Phase 14.4 (ROUND 1.5).
//
// Three improvements over the previous version (task 4 + 5):
//   1. Item requirements made explicit: shows the minimum level and the slot
//      the item must occupy. The slot is derived from `item.item_type`
//      (weapon → weapon, armor → armor, accessory → accessory).
//   2. Equip status is human-readable: "Available × N",
//      "Equipped by: <names>", or a combined view when both apply.
//   3. Contextual actions:
//        - "Manage on <adv>" link when the item is already equipped (jumps to
//          the AdventurerEquipment page where Unequip is available).
//        - Per-eligible-adventurer "Equip" buttons, gated by level / slot
//          compatibility / adventurer availability.
//
// The inventory model is documented as STACKS (multiple copies of the same
// item share one row; each equip consumes one reservation via
// `inventory_items.reserved_qty`). The UI surfaces this through
// `inventory_extra.model_note`.
//
// NOTE on backend coupling (ROUND 1.5 audit):
//   - GET /api/inventory returns aggregate equipped_quantity / available_quantity
//     but does NOT list which adventurer has each copy. We derive that on the
//     client by fetching /api/adventurers (which embeds each adventurer's
//     equipped slots) and indexing by item_id.
//   - "Replace" is intentionally NOT exposed as a single button: the equipment
//     API requires unequip → equip (two atomic ops). Surfacing it would
//     require either a backend swap endpoint (out of ROUND 1.5 scope) or a
//     two-step UI that risks half-completed swaps. We instead keep "Manage"
//     which deep-links to the slot-aware UI.
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, formatApiError } from "../lib/api";
import { toast } from "sonner";
import AppHeader from "../components/AppHeader";
import { useT } from "../i18n/I18nContext";
import { Button } from "../components/ui/button";
import InventoryEquipModal from "../components/InventoryEquipModal";

const RARITY_COLOR = {
    Common: "#9ca3af",
    Uncommon: "#22c55e",
    Rare: "#3b82f6",
    Epic: "#a855f7",
};

const RarityBadge = ({ rarity }) => (
    <span
        className="inline-block text-[10px] tracking-widest border px-1.5 py-0.5 rounded-sm"
        style={{
            color: RARITY_COLOR[rarity] || RARITY_COLOR.Common,
            borderColor: (RARITY_COLOR[rarity] || RARITY_COLOR.Common) + "55",
        }}
    >
        {rarity?.toUpperCase()}
    </span>
);

function statBonusList(it) {
    if (!it) return "";
    const parts = [];
    if (it.strength_bonus) parts.push(`+${it.strength_bonus} STR`);
    if (it.agility_bonus) parts.push(`+${it.agility_bonus} AGI`);
    if (it.intellect_bonus) parts.push(`+${it.intellect_bonus} INT`);
    if (it.endurance_bonus) parts.push(`+${it.endurance_bonus} END`);
    if (it.faith_bonus) parts.push(`+${it.faith_bonus} FAI`);
    return parts.join(" · ");
}

function buildEquippedByMap(adventurers) {
    // { item_id: [{ adventurer_id, adventurer_name, slot }] }
    const out = {};
    for (const a of adventurers || []) {
        const eq = a.equipment || {};
        for (const slot of ["weapon", "armor", "accessory"]) {
            const it = eq[slot]?.item;
            if (!it) continue;
            const list = out[it.id] || (out[it.id] = []);
            list.push({
                adventurer_id: a.id,
                adventurer_name: a.name,
                slot,
            });
        }
    }
    return out;
}

export default function Inventory() {
    const { t, lang } = useT();
    const [rows, setRows] = useState(null);
    const [adventurers, setAdventurers] = useState([]);
    const [recipes, setRecipes] = useState([]);
    const [loading, setLoading] = useState(true);
    const [busyKey, setBusyKey] = useState(null);
    const [typeFilter, setTypeFilter] = useState("all");  // all|weapon|armor|accessory|consumable|material
    const [rarityFilter, setRarityFilter] = useState(new Set());
    const [equipRow, setEquipRow] = useState(null);

    // ROUND 6B FASE B — wrapped in useCallback so its identity is stable
    // across renders that DON'T change `lang`. This lets the mount/refresh
    // useEffect below depend on `refresh` directly (instead of `[]` with a
    // disable directive) AND fixes a latent bug: previously the effect was
    // mount-only, so toggling the language left stale localized recipe
    // names on screen until the user navigated away and back.
    const refresh = useCallback(async () => {
        try {
            const [invRes, advRes, recRes] = await Promise.all([
                api.get("/inventory"),
                api.get("/adventurers"),
                api.get(`/recipes?lang=${lang}`).catch(() => ({ data: { recipes: [] } })),
            ]);
            setRows(invRes.data.inventory);
            setAdventurers(advRes.data.adventurers || []);
            setRecipes(recRes.data.recipes || []);
        } catch (err) {
            toast.error(formatApiError(err));
            setRows([]);
        } finally {
            setLoading(false);
        }
    }, [lang]);

    useEffect(() => {
        refresh();
    }, [refresh]);

    const equippedByMap = useMemo(
        () => buildEquippedByMap(adventurers),
        [adventurers]
    );

    // Phase 14.7 — set of slugs that appear as input in any active recipe.
    const craftingMaterialSlugs = useMemo(() => {
        const out = new Set();
        for (const r of recipes || []) {
            for (const i of r.inputs || []) {
                if (i.item_slug) out.add(i.item_slug);
            }
        }
        return out;
    }, [recipes]);

    // Header summary counts by item_type.
    const countsByType = useMemo(() => {
        const c = { weapon: 0, armor: 0, accessory: 0, consumable: 0, material: 0 };
        for (const r of rows || []) {
            const t = r.item?.item_type;
            if (t && c[t] !== undefined) c[t] += r.total_quantity;
        }
        return c;
    }, [rows]);

    const filteredRows = useMemo(() => {
        return (rows || []).filter((r) => {
            const it = r.item;
            if (!it) return false;
            if (typeFilter !== "all" && it.item_type !== typeFilter) return false;
            if (rarityFilter.size > 0 && !rarityFilter.has(it.rarity)) return false;
            return true;
        });
    }, [rows, typeFilter, rarityFilter]);

    const toggleRarity = (r) => {
        const next = new Set(rarityFilter);
        if (next.has(r)) next.delete(r);
        else next.add(r);
        setRarityFilter(next);
    };

    const doEquip = async (advId, itemId, slot, key) => {
        setBusyKey(key);
        try {
            await api.post(`/adventurers/${advId}/equip`, { item_id: itemId, slot });
            toast.success(t("equipment_extra.toast_equipped", { slot }));
            await refresh();
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setBusyKey(null);
        }
    };

    return (
        <div className="min-h-screen bg-background text-foreground term-grid-bg">
            <AppHeader subtitleKey="nav.inventory" />

            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
                <div className="flex items-end justify-between gap-3 mb-6 flex-wrap">
                    <div>
                        <div className="text-xs text-amber tracking-widest mb-2">
                            :: GUILD VAULT
                        </div>
                        <h1 className="text-3xl font-semibold tracking-tight">{t("inventory.title")}</h1>
                        <p className="text-sm text-muted-foreground mt-2 max-w-2xl">
                            Items recovered from dungeon expeditions.
                        </p>
                        <p
                            className="text-[11px] text-muted-foreground/80 mt-2 max-w-2xl"
                            data-testid="inventory-model-note"
                        >
                            {t("inventory_extra.model_note")}
                        </p>
                    </div>
                    <div className="text-right">
                        <div className="text-[10px] text-muted-foreground tracking-widest">
                            STACKS
                        </div>
                        <div
                            data-testid="inventory-stack-count"
                            className="text-2xl font-semibold text-amber"
                        >
                            {rows?.length ?? "—"}
                        </div>
                    </div>
                </div>

                {loading && (
                    <div className="text-xs text-muted-foreground">
                        loading<span className="caret-blink" />
                    </div>
                )}

                {!loading && rows && rows.length === 0 && (
                    <div
                        data-testid="inventory-empty"
                        className="border border-border bg-card rounded-sm p-10 text-center"
                    >
                        <div className="text-amber text-xs tracking-widest mb-2">
                            :: DEPOSITO VUOTO
                        </div>
                        <p className="text-sm text-muted-foreground mb-5 max-w-md mx-auto">
                            🎁 Il tuo deposito è vuoto. Completa una spedizione per
                            ottenere il primo loot da equipaggiare o vendere.
                        </p>
                        <Link to="/dungeons">
                            <Button
                                data-testid="inventory-goto-dungeons"
                                className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm"
                            >
                                Go to Dungeons →
                            </Button>
                        </Link>
                    </div>
                )}

                {!loading && rows && rows.length > 0 && (
                    <>
                        {/* Phase 14.7 — Header summary + filters */}
                        <div className="mb-4 border border-border bg-card rounded-sm p-3" data-testid="inv-header-summary">
                            <div className="flex flex-wrap gap-3 text-[11px] mb-2">
                                {["weapon", "armor", "accessory", "consumable", "material"].map((k) => (
                                    <span key={k} data-testid={`inv-count-${k}`}>
                                        <span className="text-muted-foreground">{t(`inventory_extra.type_${k}`)}:</span>
                                        <span className="ml-1 text-amber font-semibold">{countsByType[k] || 0}</span>
                                    </span>
                                ))}
                            </div>
                            <div className="flex flex-wrap gap-1.5 pt-2 border-t border-border/60">
                                {["all", "weapon", "armor", "accessory", "consumable", "material"].map((k) => (
                                    <button
                                        key={k}
                                        data-testid={`inv-filter-type-${k}`}
                                        onClick={() => setTypeFilter(k)}
                                        className={`text-[10px] tracking-widest px-2 py-1 rounded-sm border ${
                                            typeFilter === k
                                                ? "border-amber text-amber bg-amber/10"
                                                : "border-border text-muted-foreground hover:border-amber/40"
                                        }`}
                                    >
                                        {t(`inventory_extra.type_${k}`).toUpperCase()}
                                    </button>
                                ))}
                                <span className="border-r border-border/60 mx-1" />
                                {["Common", "Uncommon", "Rare", "Epic"].map((r) => (
                                    <button
                                        key={r}
                                        data-testid={`inv-filter-rarity-${r}`}
                                        onClick={() => toggleRarity(r)}
                                        className={`text-[10px] tracking-widest px-2 py-1 rounded-sm border ${
                                            rarityFilter.has(r)
                                                ? "border-amber text-amber bg-amber/10"
                                                : "border-border text-muted-foreground hover:border-amber/40"
                                        }`}
                                    >
                                        {r.toUpperCase()}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="space-y-3" data-testid="inventory-cards">
                            {filteredRows.length === 0 && (
                                <div className="text-xs text-muted-foreground italic" data-testid="inv-filter-no-results">
                                    {t("inventory_extra.filter_empty")}
                                </div>
                            )}
                            {filteredRows.map((r) => {
                            const it = r.item;
                            if (!it) return null;
                            const slot = it.item_type; // weapon | armor | accessory
                            const levelReq = it.level_required || 1;
                            const equippedBy = equippedByMap[it.id] || [];

                            // Adventurers who could equip this item:
                            // - same slot is empty
                            // - level >= levelReq
                            // - is_available (not on expedition)
                            const eligible = adventurers.filter((a) => {
                                if (!a.is_available) return false;
                                if ((a.level || 1) < levelReq) return false;
                                const slotItem = a.equipment?.[slot]?.item;
                                return !slotItem;
                            });

                            const usableCount = adventurers.filter(
                                (a) => (a.level || 1) >= levelReq
                            ).length;
                            const hasAvailable = r.available_quantity > 0;

                            return (
                                <div
                                    key={r.id}
                                    data-testid={`inventory-card-${r.id}`}
                                    className="border border-border bg-card rounded-sm p-4"
                                >
                                    <div className="flex items-start justify-between gap-3 flex-wrap">
                                        <div className="min-w-0">
                                            <div className="font-medium truncate flex items-center gap-2 flex-wrap">
                                                <span data-testid={`inv-name-${r.id}`}>
                                                    {(lang === "en"
                                                        ? it.display_name_en
                                                        : it.display_name_it) || it.name}
                                                    {r.refinement_level > 0 ? ` +${r.refinement_level}` : ""}
                                                </span>
                                                <RarityBadge rarity={it.rarity} />
                                                {r.is_bound && (
                                                    <span
                                                        data-testid={`inv-bound-badge-${r.id}`}
                                                        className="inline-block text-[10px] tracking-widest border border-amber/60 text-amber px-1.5 py-0.5 rounded-sm"
                                                        title={t("inventory_extra.bound_tooltip")}
                                                    >
                                                        ◆ {t("inventory_extra.bound_badge")}
                                                    </span>
                                                )}
                                                {/* ROUND 6B.4 Task 2 — adventurer-bound badge.
                                                    Coexists with guild-bound (`is_bound`):
                                                    an item may be both. Resolves the name
                                                    locally via the loaded adventurers list. */}
                                                {r.bound_to_adventurer_id && (() => {
                                                    const boundAdv = adventurers.find((a) => a.id === r.bound_to_adventurer_id);
                                                    const advName = boundAdv?.name || (lang === "it" ? "avventuriero" : "adventurer");
                                                    return (
                                                        <span
                                                            data-testid={`inv-adv-bound-badge-${r.id}`}
                                                            className="inline-block text-[10px] tracking-widest border border-orange-500/40 text-orange-300 px-1.5 py-0.5 rounded-sm"
                                                            title={lang === "it"
                                                                ? `Legato a ${advName} (motivo: ${r.bound_reason || "—"})`
                                                                : `Bound to ${advName} (reason: ${r.bound_reason || "—"})`}
                                                        >
                                                            ⚔ {lang === "it" ? "Legato a" : "Bound to"} {advName}
                                                        </span>
                                                    );
                                                })()}
                                                {craftingMaterialSlugs.has(it.slug) && (
                                                    <span
                                                        data-testid={`inv-craft-mat-badge-${r.id}`}
                                                        className="inline-block text-[10px] tracking-widest border border-blue-500/40 text-blue-400 px-1.5 py-0.5 rounded-sm"
                                                        title={t("inventory_extra.crafting_material_tip")}
                                                    >
                                                        ⚒ {t("inventory_extra.crafting_material")}
                                                    </span>
                                                )}
                                            </div>
                                            <div className="text-[11px] text-muted-foreground mt-1">
                                                {slot} · power {it.power_score ?? 0}
                                                {statBonusList(it) ? ` · ${statBonusList(it)}` : ""}
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <div className="text-[10px] text-muted-foreground tracking-widest">
                                                ×{r.total_quantity}
                                            </div>
                                            <div className="text-[10px] text-muted-foreground mt-0.5">
                                                {t("inventory_extra.status_partial_equipped", {
                                                    equipped: r.equipped_quantity,
                                                    available: r.available_quantity,
                                                })}
                                            </div>
                                        </div>
                                    </div>

                                    {/* Requirements row */}
                                    <div
                                        className="mt-3 pt-3 border-t border-border/60"
                                        data-testid={`inv-requirements-${r.id}`}
                                    >
                                        <div className="text-[10px] text-muted-foreground tracking-widest mb-1">
                                            {t("inventory_extra.requirements_label")}
                                        </div>
                                        <div className="flex flex-wrap gap-2 text-[11px]">
                                            <span
                                                className="border border-border rounded-sm px-2 py-0.5"
                                                data-testid={`inv-req-level-${r.id}`}
                                            >
                                                {t("inventory_extra.req_level", { n: levelReq })}
                                            </span>
                                            <span
                                                className="border border-border rounded-sm px-2 py-0.5"
                                                data-testid={`inv-req-slot-${r.id}`}
                                            >
                                                {t("inventory_extra.req_slot", { slot: slot?.toUpperCase() || "—" })}
                                            </span>
                                            <span
                                                className="text-muted-foreground italic"
                                                data-testid={`inv-usable-count-${r.id}`}
                                            >
                                                {t("inventory_extra.usable_by", { n: usableCount })}
                                            </span>
                                        </div>
                                    </div>

                                    {/* Status row */}
                                    <div
                                        className="mt-3 pt-3 border-t border-border/60"
                                        data-testid={`inv-status-${r.id}`}
                                    >
                                        <div className="text-[10px] text-muted-foreground tracking-widest mb-1">
                                            {t("inventory_extra.status_label")}
                                        </div>
                                        <div className="flex flex-wrap gap-2 text-[11px]">
                                            {hasAvailable && (
                                                <span
                                                    className="border border-[#22c55e]/40 text-[#22c55e] rounded-sm px-2 py-0.5"
                                                    data-testid={`inv-status-available-${r.id}`}
                                                >
                                                    {t("inventory_extra.status_available")} × {r.available_quantity}
                                                </span>
                                            )}
                                            {equippedBy.length > 0 && (
                                                <span
                                                    className="border border-amber/40 text-amber rounded-sm px-2 py-0.5"
                                                    data-testid={`inv-status-equipped-${r.id}`}
                                                    title={equippedBy
                                                        .map((e) => `${e.adventurer_name} (${e.slot})`)
                                                        .join(", ")}
                                                >
                                                    {t("inventory_extra.status_equipped_by", {
                                                        names: equippedBy
                                                            .map((e) => e.adventurer_name)
                                                            .join(", "),
                                                    })}
                                                </span>
                                            )}
                                        </div>
                                    </div>

                                    {/* Actions row */}
                                    <div
                                        className="mt-3 pt-3 border-t border-border/60"
                                        data-testid={`inv-actions-${r.id}`}
                                    >
                                        <div className="text-[10px] text-muted-foreground tracking-widest mb-1">
                                            {t("inventory_extra.actions_label")}
                                        </div>

                                        {/* Phase 19.2 — P1.2: primary "Equipaggia" CTA opens modal with eligibility preview */}
                                        {hasAvailable && (
                                            <div className="mb-2">
                                                <Button
                                                    type="button"
                                                    data-testid={`inv-open-equip-modal-${r.id}`}
                                                    onClick={() => setEquipRow(r)}
                                                    className="h-7 px-2 text-[11px] bg-amber text-black hover:bg-amber/80 rounded-sm"
                                                    title={t("inventory_extra.status_available")}
                                                >
                                                    ▶ {t("inventory_extra.equip_button", "Equipaggia…")}
                                                </Button>
                                            </div>
                                        )}

                                        {/* Manage links for adventurers already wearing this item */}
                                        {equippedBy.length > 0 && (
                                            <div className="flex flex-wrap gap-2 mb-2">
                                                {equippedBy.map((e) => (
                                                    <Link
                                                        key={`${e.adventurer_id}-${e.slot}`}
                                                        to={`/adventurers/${e.adventurer_id}/equipment`}
                                                        data-testid={`inv-manage-${r.id}-${e.adventurer_id}`}
                                                        className="text-[11px] text-amber hover:underline"
                                                    >
                                                        {t("inventory_extra.manage_on_adventurer")} {e.adventurer_name}
                                                    </Link>
                                                ))}
                                            </div>
                                        )}

                                        {/* Equip buttons for eligible adventurers (only if stock available) */}
                                        {hasAvailable && eligible.length > 0 && (
                                            <div className="flex flex-wrap gap-2">
                                                {eligible.slice(0, 6).map((a) => {
                                                    const key = `${r.id}-${a.id}`;
                                                    return (
                                                        <Button
                                                            key={a.id}
                                                            data-testid={`inv-equip-${r.id}-${a.id}-btn`}
                                                            disabled={busyKey === key}
                                                            onClick={() =>
                                                                doEquip(a.id, it.id, slot, key)
                                                            }
                                                            className="h-7 px-2 text-[11px] bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm"
                                                            title={`${t("inventory_extra.status_available")} → ${a.name} (${slot})`}
                                                        >
                                                            ▶ {a.name}
                                                        </Button>
                                                    );
                                                })}
                                                {eligible.length > 6 && (
                                                    <span className="text-[11px] text-muted-foreground self-center">
                                                        +{eligible.length - 6}
                                                    </span>
                                                )}
                                            </div>
                                        )}

                                        {/* No-action explanation */}
                                        {hasAvailable && eligible.length === 0 && (
                                            <div
                                                className="text-[11px] text-muted-foreground italic"
                                                data-testid={`inv-no-eligible-${r.id}`}
                                            >
                                                {usableCount === 0
                                                    ? t("inventory_extra.not_usable_reason_level", { n: levelReq })
                                                    : t("inventory_extra.no_compatible_adventurer")}
                                            </div>
                                        )}

                                        {/* ROUND 4 — Forge link (refinable / enchantable items) */}
                                        {(it.item_type === "weapon" || it.item_type === "armor" || it.item_type === "accessory") && (
                                            <div className="mt-2">
                                                <Link
                                                    to="/forge"
                                                    data-testid={`inv-goto-forge-${r.id}`}
                                                    className="inline-block text-[11px] text-amber hover:underline"
                                                    title={t("inventory_extra.bound_tooltip")}
                                                >
                                                    ⚒ {t("inventory_extra.goto_forge")}
                                                </Link>
                                            </div>
                                        )}
                                    </div>

                                    {it.description && (
                                        <p className="text-[11px] text-muted-foreground mt-3 pt-3 border-t border-border/60 italic">
                                            {it.description}
                                        </p>
                                    )}
                                </div>
                            );
                        })}
                        </div>
                    </>
                )}
            </main>
            <InventoryEquipModal
                row={equipRow}
                adventurers={adventurers}
                onClose={() => setEquipRow(null)}
                onEquipped={refresh}
                lang={lang}
            />
        </div>
    );
}
