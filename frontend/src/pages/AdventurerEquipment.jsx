import { useEffect, useState, useCallback, useMemo } from "react";
import { Link, useParams } from "react-router-dom";
import { api, formatApiError } from "../lib/api";
import { toast } from "sonner";
import AppHeader from "../components/AppHeader";
import { Button } from "../components/ui/button";

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
    if (it.power_score) parts.push(`+${it.power_score} POW`);
    return parts.join(" · ") || "no bonuses";
}

const SLOT_ORDER = ["weapon", "armor", "accessory"];
const SLOT_LABEL = { weapon: "WEAPON", armor: "ARMOR", accessory: "ACCESSORY" };

export default function AdventurerEquipment() {
    const { id: advId } = useParams();
    const [equipment, setEquipment] = useState(null);
    const [adventurer, setAdventurer] = useState(null);
    const [inventory, setInventory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [busy, setBusy] = useState(false);

    const isLocked = adventurer && !adventurer.is_available;

    const refresh = useCallback(async () => {
        try {
            const [eqRes, advRes, invRes] = await Promise.all([
                api.get(`/adventurers/${advId}/equipment`),
                api.get("/adventurers"),
                api.get("/inventory"),
            ]);
            setEquipment(eqRes.data);
            const matchedAdv = advRes.data.adventurers.find((a) => a.id === advId);
            setAdventurer(matchedAdv || null);
            setInventory(invRes.data.inventory || []);
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
            toast.success(`Equipped on ${slot}`);
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
            toast.success(`Unequipped ${slot}`);
            await refresh();
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setBusy(false);
        }
    };

    return (
        <div className="min-h-screen bg-background text-foreground term-grid-bg">
            <AppHeader subtitle="EQUIPMENT" />

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

                        {isLocked && (
                            <div
                                data-testid="equipment-locked-banner"
                                className="text-xs text-amber border border-amber/40 bg-amber/10 px-3 py-2 rounded-sm mb-6"
                            >
                                Adventurer is in an expedition — equipment cannot be
                                modified until they return.
                            </div>
                        )}

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
                                                {compatibles.map((row) => (
                                                    <li
                                                        key={row.id}
                                                        data-testid={`compatible-${slot}-${row.item_id}`}
                                                        className="flex items-center justify-between gap-3 border border-border/60 rounded-sm px-3 py-2"
                                                    >
                                                        <div className="min-w-0">
                                                            <div className="text-sm font-medium truncate">
                                                                {row.item.name}{" "}
                                                                <span className="ml-2 align-middle">
                                                                    <RarityBadge rarity={row.item.rarity} />
                                                                </span>
                                                            </div>
                                                            <div className="text-[11px] text-muted-foreground">
                                                                {statBonusList(row.item)} · available {row.available_quantity}/{row.total_quantity}
                                                            </div>
                                                        </div>
                                                        <Button
                                                            data-testid={`equip-${slot}-${row.item_id}-btn`}
                                                            disabled={busy || isLocked || !!equippedSlot}
                                                            onClick={() => doEquip(row.item_id, slot)}
                                                            className="h-8 px-3 text-xs bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm shrink-0"
                                                            title={
                                                                equippedSlot
                                                                    ? "Unequip first"
                                                                    : isLocked
                                                                    ? "Adventurer is in expedition"
                                                                    : "Equip"
                                                            }
                                                        >
                                                            Equip
                                                        </Button>
                                                    </li>
                                                ))}
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
