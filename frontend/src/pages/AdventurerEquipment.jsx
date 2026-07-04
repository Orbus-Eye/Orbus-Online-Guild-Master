import { useEffect, useState, useCallback, useMemo } from "react";
import { Link, useParams } from "react-router-dom";
import { api, formatApiError } from "../lib/api";
import { toast } from "sonner";
import AppHeader from "../components/AppHeader";
import { useT } from "../i18n/I18nContext";
import { Button } from "../components/ui/button";
import {
    isItemUnderLeveled,
    itemReqLevelBadge,
    itemReqLevelTooltip,
} from "../utils/levelGate";
import { rarityLabel } from "../utils/displayLabels";

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
        {rarityLabel(rarity).toUpperCase()}
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
    if (it.power_score) parts.push(`+${it.power_score} POW`);
    return parts.join(" · ") || "no bonuses";
}

const SLOT_ORDER = ["weapon", "armor", "accessory"];
const SLOT_LABEL = { weapon: "Arma", armor: "Armatura", accessory: "Accessorio" };

export default function AdventurerEquipment() {
    const { t } = useT();
    const { id: advId } = useParams();
    const [equipment, setEquipment] = useState(null);
    const [adventurer, setAdventurer] = useState(null);
    const [inventory, setInventory] = useState([]);
    const [equipmentDetail, setEquipmentDetail] = useState(null);
    const [loading, setLoading] = useState(true);
    const [busy, setBusy] = useState(false);

    const isLocked = adventurer && !adventurer.is_available;

    const refresh = useCallback(async () => {
        try {
            const [eqRes, advRes, invRes, detailRes] = await Promise.all([
                api.get(`/adventurers/${advId}/equipment`),
                api.get("/adventurers"),
                api.get("/inventory"),
                api.get(`/adventurers/${advId}/equipment-detail`).catch(() => ({ data: null })),
            ]);
            setEquipment(eqRes.data);
            const matchedAdv = advRes.data.adventurers.find((a) => a.id === advId);
            setAdventurer(matchedAdv || null);
            setInventory(invRes.data.inventory || []);
            setEquipmentDetail(detailRes.data);
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setLoading(false);
        }
    }, [advId]);

    useEffect(() => {
        refresh();
    }, [refresh]);

    const inventoryBySlot = useMemo(() => {
        const out = { weapon: [], armor: [], accessory: [] };
        for (const row of inventory) {
            const it = row.item;
            if (!it) continue;
            if (row.available_quantity > 0 && out[it.item_type]) {
                out[it.item_type].push(row);
            }
        }
        return out;
    }, [inventory]);

    const doEquip = async (itemId, slot) => {
        setBusy(true);
        try {
            await api.post(`/adventurers/${advId}/equip`, { item_id: itemId, slot });
            toast.success(t("equipment_extra.toast_equipped", { slot }));
            await refresh();
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setBusy(false);
        }
    };

    const doUnequip = async (slot) => {
        setBusy(true);
        try {
            await api.post(`/adventurers/${advId}/unequip`, { slot });
            toast.success(t("equipment_extra.toast_unequipped", { slot }));
            await refresh();
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setBusy(false);
        }
    };

    // ROUND 17.2 pre-sealing hotfix — Auto-Equip button parity con
    // AdventurerDetailModal. Il tester non trovava il bottone perché
    // esisteva solo nel modale (accessibile dalla card), non nella
    // pagina dedicata `/adventurers/{id}/equipment`. Scope stretto:
    // riuso stesso endpoint + toast IT identici al modale.
    const [autoEquipBusy, setAutoEquipBusy] = useState(false);
    const handleAutoEquip = async () => {
        if (!advId || autoEquipBusy || isLocked) return;
        setAutoEquipBusy(true);
        try {
            const r = await api.post(`/adventurers/${advId}/auto-equip`);
            const s = r.data?.summary || {};
            const delta = (s.score_after ?? 0) - (s.score_before ?? 0);
            const swaps = s.swaps_count ?? 0;
            if (swaps === 0) {
                toast.info("Nessuna sostituzione possibile.", {
                    description: "Nessun oggetto compatibile più forte in inventario.",
                });
            } else {
                toast.success(
                    `${swaps} oggett${swaps === 1 ? "o aggiornato" : "i aggiornati"}`,
                    {
                        description: `Potere ${s.score_before ?? 0} → ${s.score_after ?? 0} (${delta >= 0 ? "+" : ""}${delta})`,
                    },
                );
            }
            await refresh();
        } catch (err) {
            const msg = err?.response?.data?.detail?.user_message
                || "Auto-equipaggiamento fallito. Riprova fra poco.";
            toast.error(msg);
        } finally {
            setAutoEquipBusy(false);
        }
    };

    return (
        <div className="min-h-screen bg-background text-foreground term-grid-bg">
            <AppHeader subtitleKey="nav.adventurers" />

            <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
                <Link
                    to="/adventurers"
                    className="text-xs text-muted-foreground hover:text-foreground inline-block mb-6"
                    data-testid="back-roster-link"
                >
                    ← back to roster
                </Link>

                {loading && (
                    <div className="text-xs text-muted-foreground">
                        loading equipment<span className="caret-blink" />
                    </div>
                )}

                {!loading && adventurer && equipment && (
                    <>
                        <div className="mb-6">
                            <div className="text-xs text-amber tracking-widest mb-2">
                                :: ADVENTURER EQUIPMENT
                            </div>
                            <h1
                                className="text-3xl font-semibold tracking-tight"
                                data-testid="equipment-adventurer-name"
                            >
                                {adventurer.name}
                            </h1>
                            <p className="text-sm text-muted-foreground mt-2">
                                {adventurer.class_name} · {adventurer.class_role} · Lvl{" "}
                                {adventurer.level}
                            </p>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
                            <div
                                className="border border-border bg-card rounded-sm p-3"
                                data-testid="equipment-base-power"
                            >
                                <div className="text-[10px] text-muted-foreground tracking-widest">
                                    BASE POWER
                                </div>
                                <div className="text-2xl font-semibold mt-1">
                                    {equipment.base_power}
                                </div>
                            </div>
                            <div
                                className="border border-border bg-card rounded-sm p-3"
                                data-testid="equipment-eq-power"
                            >
                                <div className="text-[10px] text-muted-foreground tracking-widest">
                                    EQUIPMENT POWER
                                </div>
                                <div className="text-2xl font-semibold text-amber mt-1">
                                    +{equipment.equipment_power}
                                </div>
                            </div>
                            <div
                                className="border border-border bg-card rounded-sm p-3"
                                data-testid="equipment-total-power"
                            >
                                <div className="text-[10px] text-muted-foreground tracking-widest">
                                    TOTAL POWER
                                </div>
                                <div className="text-2xl font-semibold text-[#22c55e] mt-1">
                                    {equipment.total_power}
                                </div>
                            </div>
                        </div>

                        {/* ROUND 17.2 pre-sealing hotfix — Auto-Equip button
                            parity con AdventurerDetailModal. Placement: sotto
                            i 3 power cards, sopra il banner locked. Disabled
                            se avventuriero locked o busy. */}
                        <div className="mb-6 flex items-center justify-end">
                            <button
                                type="button"
                                data-testid={`auto-equip-btn-page-${advId}`}
                                onClick={handleAutoEquip}
                                disabled={autoEquipBusy || isLocked}
                                className="px-3 py-1.5 rounded-sm text-xs font-medium tracking-wide bg-amber-400/90 text-black hover:bg-amber-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                                {autoEquipBusy ? "Equipaggiando…" : "Auto-Equipaggia"}
                            </button>
                        </div>

                        {isLocked && (
                            <div
                                data-testid="equipment-locked-banner"
                                className="text-xs text-amber border border-amber/40 bg-amber/10 px-3 py-2 rounded-sm mb-6"
                            >
                                Adventurer is in an expedition — equipment cannot be
                                modified until they return.
                            </div>
                        )}

                        {/* ROUND 4 — Set bonuses panel */}
                        <section
                            data-testid="set-bonuses-panel"
                            className="border border-border bg-card rounded-sm mb-6"
                        >
                            <div className="px-4 py-3 border-b border-border/60 bg-secondary/30 text-xs tracking-widest text-amber">
                                :: {t("set.active_bonuses_title")}
                            </div>
                            <div className="p-4">
                                {(!equipmentDetail || (equipmentDetail.active_bonuses || []).length === 0) ? (
                                    <div
                                        data-testid="set-bonuses-empty"
                                        className="text-[11px] text-muted-foreground italic"
                                    >
                                        {t("set.no_active_bonuses")}
                                    </div>
                                ) : (
                                    <ul className="space-y-1.5">
                                        {(equipmentDetail.active_bonuses || []).map((b, idx) => (
                                            <li
                                                key={`${b.set_slug}-${b.pieces}-${idx}`}
                                                data-testid={`set-bonus-${b.set_slug}-${b.pieces}`}
                                                className="text-[11px] flex items-center gap-2"
                                            >
                                                <span className="text-amber">◆</span>
                                                <span className="text-foreground">{b.set_slug}</span>
                                                <span className="text-muted-foreground">
                                                    ({b.pieces}pz)
                                                </span>
                                                <span className="text-[#22c55e]">
                                                    +{b.bonus_value} {b.bonus_stat.toUpperCase()}
                                                </span>
                                            </li>
                                        ))}
                                    </ul>
                                )}
                                {equipmentDetail && (equipmentDetail.set_progress || []).length > 0 && (
                                    <div className="mt-3 pt-3 border-t border-border/40 space-y-1">
                                        {equipmentDetail.set_progress.map((p) => (
                                            <div
                                                key={p.set_id}
                                                data-testid={`set-progress-${p.slug}`}
                                                className="text-[10px] text-muted-foreground"
                                            >
                                                <span className="text-foreground/80">{p.name}:</span>{" "}
                                                {t("set.progress_label", { owned: p.owned, total: p.total })}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </section>

                        {SLOT_ORDER.map((slot) => {
                            const equippedSlot = equipment.slots[slot];
                            const compatibles = inventoryBySlot[slot] || [];
                            return (
                                <section
                                    key={slot}
                                    data-testid={`slot-section-${slot}`}
                                    className="border border-border bg-card rounded-sm mb-4"
                                >
                                    <div className="flex items-center justify-between px-4 py-3 border-b border-border/60 bg-secondary/30">
                                        <div className="text-xs tracking-widest text-amber">
                                            :: {SLOT_LABEL[slot]}
                                        </div>
                                        {equippedSlot && (
                                            <Button
                                                data-testid={`unequip-${slot}-btn`}
                                                disabled={busy || isLocked}
                                                onClick={() => doUnequip(slot)}
                                                className="h-8 px-3 text-xs bg-secondary text-foreground hover:bg-secondary/80 border border-border rounded-sm"
                                                title={
                                                    isLocked
                                                        ? "Adventurer is in expedition"
                                                        : "Unequip"
                                                }
                                            >
                                                Unequip
                                            </Button>
                                        )}
                                    </div>

                                    <div className="p-4">
                                        {equippedSlot ? (
                                            <div data-testid={`slot-equipped-${slot}`} className="mb-4">
                                                <div className="flex items-center justify-between gap-3 flex-wrap">
                                                    <div>
                                                        <div className="font-medium">
                                                            {equippedSlot.item.name}{" "}
                                                            <span className="ml-2 align-middle">
                                                                <RarityBadge rarity={equippedSlot.item.rarity} />
                                                            </span>
                                                        </div>
                                                        <div className="text-xs text-muted-foreground mt-1">
                                                            {statBonusList(equippedSlot.item)}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        ) : (
                                            <div
                                                data-testid={`slot-empty-${slot}`}
                                                className="text-xs text-muted-foreground mb-4"
                                            >
                                                Empty slot.
                                            </div>
                                        )}

                                        <div className="text-[10px] text-muted-foreground tracking-widest border-t border-border/40 pt-3 mb-2">
                                            COMPATIBLE FROM INVENTORY
                                        </div>

                                        {compatibles.length === 0 ? (
                                            <div className="text-xs text-muted-foreground">
                                                No compatible items available.
                                            </div>
                                        ) : (
                                            <ul className="space-y-2">
                                                {compatibles.map((row) => {
                                                    // Round 11.3 — UI gate: item below adventurer level
                                                    // requirement. Backend stays authoritative.
                                                    const underLeveled = isItemUnderLeveled(row.item, adventurer);
                                                    const reqLv = row.item.required_adventurer_level || 1;
                                                    const tooltip = underLeveled
                                                        ? itemReqLevelTooltip(reqLv)
                                                        : equippedSlot
                                                        ? "Unequip first"
                                                        : isLocked
                                                        ? "Adventurer is in expedition"
                                                        : "Equip";
                                                    return (
                                                        <li
                                                            key={row.id}
                                                            data-testid={`compatible-${slot}-${row.item_id}`}
                                                            data-underleveled={underLeveled ? "1" : "0"}
                                                            className={`flex items-center justify-between gap-3 border border-border/60 rounded-sm px-3 py-2 ${
                                                                underLeveled ? "opacity-40" : ""
                                                            }`}
                                                            title={underLeveled ? tooltip : ""}
                                                        >
                                                            <div className="min-w-0">
                                                                <div className="text-sm font-medium truncate flex items-center gap-2 flex-wrap">
                                                                    <span>{row.item.name}</span>
                                                                    <RarityBadge rarity={row.item.rarity} />
                                                                    {underLeveled && (
                                                                        <span
                                                                            data-testid={`item-underleveled-badge-${row.item_id}`}
                                                                            className="text-[10px] tracking-wider border border-destructive/55 text-destructive px-1.5 py-0.5 rounded-sm"
                                                                        >
                                                                            {itemReqLevelBadge(reqLv)}
                                                                        </span>
                                                                    )}
                                                                </div>
                                                                <div className="text-[11px] text-muted-foreground">
                                                                    {statBonusList(row.item)} · available {row.available_quantity}/{row.total_quantity}
                                                                </div>
                                                            </div>
                                                            <Button
                                                                data-testid={`equip-${slot}-${row.item_id}-btn`}
                                                                disabled={busy || isLocked || !!equippedSlot || underLeveled}
                                                                onClick={() => doEquip(row.item_id, slot)}
                                                                className="h-8 px-3 text-xs bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm shrink-0 disabled:cursor-not-allowed"
                                                                title={tooltip}
                                                            >
                                                                Equip
                                                            </Button>
                                                        </li>
                                                    );
                                                })}
                                            </ul>
                                        )}
                                    </div>
                                </section>
                            );
                        })}
                    </>
                )}
            </main>
        </div>
    );
}
