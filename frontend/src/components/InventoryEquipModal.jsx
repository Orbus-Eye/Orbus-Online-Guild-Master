// Phase 19.2 — P1.2 Inventory equip modal.
// Opens when player clicks "Equipaggia" on an equippable item.
// Shows item details + list of compatible adventurers (slot empty,
// level >= required, is_available) with stat preview (current → after).
//
// Reuses backend POST /api/adventurers/{id}/equip. No new backend logic.
import { useEffect, useMemo, useState } from "react";
import { X } from "lucide-react";
import { api, formatApiError } from "../lib/api";
import { toast } from "sonner";
import { useT } from "../i18n/I18nContext";
import RoleMarker from "./RoleMarker";

const RARITY_COLOR = {
    common: "#9ca3af",
    uncommon: "#22c55e",
    rare: "#3b82f6",
    epic: "#a855f7",
};

function bonusList(it) {
    if (!it) return [];
    const o = [];
    if (it.strength_bonus) o.push(["STR", it.strength_bonus]);
    if (it.agility_bonus) o.push(["AGI", it.agility_bonus]);
    if (it.intellect_bonus) o.push(["INT", it.intellect_bonus]);
    if (it.endurance_bonus) o.push(["END", it.endurance_bonus]);
    if (it.faith_bonus) o.push(["FAI", it.faith_bonus]);
    return o;
}

export default function InventoryEquipModal({ row, adventurers, onClose, onEquipped, lang = "it" }) {
    const { t } = useT();
    const [busyId, setBusyId] = useState(null);

    useEffect(() => {
        if (!row) return undefined;
        const onKey = (e) => { if (e.key === "Escape") onClose(); };
        document.addEventListener("keydown", onKey);
        return () => document.removeEventListener("keydown", onKey);
    }, [row, onClose]);

    const eligible = useMemo(() => {
        if (!row?.item) return [];
        const slot = row.item.item_type;
        const levelReq = row.item.level_required || 1;
        return (adventurers || []).filter((a) => {
            if (!a.is_available) return false;
            if ((a.level || 1) < levelReq) return false;
            const slotItem = a.equipment?.[slot]?.item;
            return !slotItem;
        });
    }, [row, adventurers]);

    if (!row?.item) return null;
    const it = row.item;
    const slot = it.item_type;
    const rarity = (it.rarity || "common").toLowerCase();
    const color = RARITY_COLOR[rarity] || RARITY_COLOR.common;
    const bonuses = bonusList(it);

    const equip = async (adv) => {
        setBusyId(adv.id);
        try {
            await api.post(`/adventurers/${adv.id}/equip`, { item_id: it.id, slot });
            toast.success(t("equipment_extra.toast_equipped", { slot }));
            onEquipped?.();
            onClose();
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setBusyId(null);
        }
    };

    return (
        <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="equip-modal-title"
            data-testid="inventory-equip-modal"
            className="fixed inset-0 z-[60] flex items-center justify-center px-3 py-6"
            onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
        >
            <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} aria-hidden="true" />
            <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto border border-border bg-card rounded-sm p-5 sm:p-6 shadow-xl">
                <button
                    type="button"
                    onClick={onClose}
                    aria-label="Chiudi"
                    data-testid="equip-modal-close"
                    className="absolute top-3 right-3 p-1.5 rounded-sm text-muted-foreground hover:text-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-amber"
                >
                    <X size={18} />
                </button>

                <div className="text-[10px] text-amber tracking-widest mb-2">:: EQUIPAGGIA</div>
                <h2 id="equip-modal-title" className="text-xl font-semibold tracking-tight flex items-center gap-2 flex-wrap">
                    <span data-testid="equip-modal-item-name">
                        {(lang === "en" ? it.display_name_en : it.display_name_it) || it.name}
                        {row.refinement_level > 0 ? ` +${row.refinement_level}` : ""}
                    </span>
                    <span
                        className="text-[10px] tracking-widest border px-1.5 py-0.5 rounded-sm"
                        style={{ color, borderColor: color + "55" }}
                    >
                        {rarity.toUpperCase()}
                    </span>
                    {row.is_bound && (
                        <span className="text-[10px] tracking-widest border border-amber/60 text-amber px-1.5 py-0.5 rounded-sm">
                            ◆ BOUND
                        </span>
                    )}
                </h2>
                <div className="text-xs text-muted-foreground mt-1">
                    {slot?.toUpperCase()} · power {it.power_score ?? 0}
                </div>

                {/* Bonuses */}
                {bonuses.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1.5" data-testid="equip-modal-bonuses">
                        {bonuses.map(([k, v]) => (
                            <span key={k} className="text-[11px] text-amber border border-amber/40 rounded-sm px-2 py-0.5">
                                +{v} {k}
                            </span>
                        ))}
                    </div>
                )}

                {/* Eligible list */}
                <div className="mt-5">
                    <div className="text-[10px] text-muted-foreground tracking-widest mb-2">
                        AVVENTURIERI COMPATIBILI ({eligible.length})
                    </div>
                    {eligible.length === 0 ? (
                        <div className="text-xs text-muted-foreground italic" data-testid="equip-modal-no-eligible">
                            Nessun avventuriero compatibile: lo slot deve essere libero, livello richiesto {it.level_required || 1}+,
                            e l&apos;avventuriero non deve essere in spedizione.
                        </div>
                    ) : (
                        <ul className="space-y-2" data-testid="equip-modal-eligible-list">
                            {eligible.map((a) => {
                                const after = (a.total_power || 0) + (it.power_score || 0);
                                return (
                                    <li
                                        key={a.id}
                                        data-testid={`equip-modal-adv-${a.id}`}
                                        className="border border-border rounded-sm p-3 flex items-center justify-between gap-3 flex-wrap"
                                    >
                                        <div className="min-w-0 flex items-center gap-2">
                                            <RoleMarker role={a.class_role} />
                                            <div className="min-w-0">
                                                <div className="text-sm font-medium truncate">{a.name}</div>
                                                <div className="text-[11px] text-muted-foreground">
                                                    {a.class_name} · Lv {a.level} · power{" "}
                                                    <span className="text-foreground">{a.total_power}</span>
                                                    <span className="mx-1 text-muted-foreground">→</span>
                                                    <span className="text-amber font-medium" data-testid={`equip-preview-${a.id}`}>
                                                        {after}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                        <button
                                            type="button"
                                            onClick={() => equip(a)}
                                            disabled={busyId === a.id}
                                            data-testid={`equip-modal-btn-${a.id}`}
                                            className="text-[11px] tracking-widest bg-amber text-black px-3 py-1.5 rounded-sm hover:bg-amber/80 disabled:opacity-40"
                                        >
                                            {busyId === a.id ? "…" : `▶ Equipaggia su ${a.name.split(" ")[0]}`}
                                        </button>
                                    </li>
                                );
                            })}
                        </ul>
                    )}
                </div>

                <div className="mt-5 flex justify-end">
                    <button
                        type="button"
                        onClick={onClose}
                        data-testid="equip-modal-close-btn"
                        className="text-[11px] tracking-widest border border-border px-3 py-1.5 rounded-sm hover:bg-secondary"
                    >
                        Chiudi
                    </button>
                </div>
            </div>
        </div>
    );
}
