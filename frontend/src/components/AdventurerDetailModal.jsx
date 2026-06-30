// AdventurerDetailModal — Phase 14.4 (ROUND 1.5).
// Displays a single adventurer's full sheet: level, XP progress bar,
// stats, traits with rarity/polarity, equipment per slot.
// Closes on X click, ESC key, backdrop click. Focus trap kept simple.
import { useEffect, useRef, useState } from "react";
import { X } from "lucide-react";
import { toast } from "sonner";
import { useT } from "../i18n/I18nContext";
import { TraitList } from "./TraitBadge";
import { SpecChip, SpecializationPanel } from "./SpecializationBadge";
import { getTraitLabel } from "@/utils/trait";
import { api } from "../lib/api";

const SLOTS = ["weapon", "armor", "accessory"];

const RARITY_COLOR = {
    common: "#9ca3af",
    uncommon: "#22c55e",
    rare: "#3b82f6",
    epic: "#a855f7",
};

const RARITY_LABEL = {
    common: "common",
    uncommon: "uncommon",
    rare: "rare",
    epic: "epic",
};

// Linear XP curve mirroring the backend (50 * level). If the backend
// later exposes per-level XP requirements, this should be replaced by
// a server-driven field. Documented in the report.
const xpForNextLevel = (level) => Math.max(1, 50 * Math.max(1, level));

const formatItemBonuses = (it) => {
    if (!it) return "";
    const parts = [];
    if (it.strength_bonus) parts.push(`+${it.strength_bonus} STR`);
    if (it.agility_bonus) parts.push(`+${it.agility_bonus} AGI`);
    if (it.intellect_bonus) parts.push(`+${it.intellect_bonus} INT`);
    if (it.endurance_bonus) parts.push(`+${it.endurance_bonus} END`);
    if (it.faith_bonus) parts.push(`+${it.faith_bonus} FAI`);
    return parts.join(" · ");
};

export default function AdventurerDetailModal({ adventurer, onClose, onChanged }) {
    const { t, lang } = useT();
    const dialogRef = useRef(null);
    const [autoEquipBusy, setAutoEquipBusy] = useState(false);

    const handleAutoEquip = async () => {
        if (!adventurer?.id || autoEquipBusy) return;
        setAutoEquipBusy(true);
        try {
            const r = await api.post(`/adventurers/${adventurer.id}/auto-equip`);
            const s = r.data || {};
            const delta = (s.score_after ?? 0) - (s.score_before ?? 0);
            const swaps = s.swaps_count ?? 0;
            if (swaps === 0) {
                const w = (s.warnings && s.warnings[0]) || "Nessuno swap possibile.";
                toast.info(w, { description: "Nessun item compatibile più potente in inventario." });
            } else {
                toast.success(
                    `Auto-equipaggiamento completato: ${swaps} oggetto${swaps === 1 ? "" : "i"} aggiornat${swaps === 1 ? "o" : "i"}`,
                    {
                        description: `Potere ${s.score_before}→${s.score_after} (${delta >= 0 ? "+" : ""}${delta})`,
                    },
                );
            }
            if (typeof onChanged === "function") onChanged(adventurer.id);
        } catch (err) {
            const msg = err?.response?.data?.detail?.user_message
                || "Auto-equipaggiamento fallito. Riprova fra poco.";
            toast.error(msg);
        } finally {
            setAutoEquipBusy(false);
        }
    };

    useEffect(() => {
        if (!adventurer) return undefined;
        const onKey = (e) => {
            if (e.key === "Escape") onClose();
        };
        document.addEventListener("keydown", onKey);
        // Focus the close button so ESC + initial focus work.
        const closeBtn = dialogRef.current?.querySelector(
            "[data-testid='adventurer-modal-close']"
        );
        closeBtn?.focus();
        return () => document.removeEventListener("keydown", onKey);
    }, [adventurer, onClose]);

    if (!adventurer) return null;

    const xpNeeded = xpForNextLevel(adventurer.level);
    const xpCurrent = Math.max(0, Math.min(xpNeeded, adventurer.experience || 0));
    const xpPct = Math.round((xpCurrent / xpNeeded) * 100);
    const equipment = adventurer.equipment || {};

    return (
        <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="adv-modal-title"
            data-testid="adventurer-detail-modal"
            className="fixed inset-0 z-50 flex items-center justify-center px-3 py-6"
            onClick={(e) => {
                if (e.target === e.currentTarget) onClose();
            }}
        >
            <div
                className="absolute inset-0 bg-black/70 backdrop-blur-sm"
                aria-hidden="true"
                onClick={onClose}
                data-testid="adventurer-modal-backdrop"
            />
            <div
                ref={dialogRef}
                className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto border border-border bg-card rounded-sm p-5 sm:p-6 shadow-xl"
            >
                <button
                    type="button"
                    onClick={onClose}
                    aria-label={t("adventurer_modal.close")}
                    data-testid="adventurer-modal-close"
                    className="absolute top-3 right-3 p-1.5 rounded-sm text-muted-foreground hover:text-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-amber"
                >
                    <X size={18} />
                </button>

                <div className="text-[10px] text-amber tracking-widest mb-2">
                    :: {t("adventurer_modal.header")}
                </div>
                <h2
                    id="adv-modal-title"
                    data-testid="adventurer-modal-name"
                    className="text-2xl font-semibold tracking-tight flex items-center gap-2 flex-wrap"
                >
                    <span>{adventurer.name}</span>
                    <SpecChip
                        spec={adventurer.specialization}
                        lang={lang}
                        testid="adventurer-modal-spec-chip"
                    />
                </h2>
                <div className="text-xs text-muted-foreground mt-1">
                    {adventurer.class_name} · {adventurer.class_role} ·{" "}
                    {t("adventurer_modal.level", { n: adventurer.level })}
                </div>

                {/* XP progress */}
                <div className="mt-5">
                    <div className="flex items-center justify-between text-[10px] text-muted-foreground tracking-widest mb-1.5">
                        <span>{t("adventurer_modal.experience")}</span>
                        <span data-testid="adventurer-modal-xp">
                            {xpCurrent} / {xpNeeded}
                        </span>
                    </div>
                    <div className="h-2 w-full bg-secondary rounded-sm overflow-hidden">
                        <div
                            data-testid="adventurer-modal-xp-bar"
                            className="h-full bg-amber transition-all"
                            style={{ width: `${xpPct}%` }}
                        />
                    </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-5 gap-2 mt-5">
                    {[
                        ["STR", adventurer.strength],
                        ["AGI", adventurer.agility],
                        ["INT", adventurer.intellect],
                        ["END", adventurer.endurance],
                        ["FAI", adventurer.faith],
                    ].map(([k, v]) => (
                        <div
                            key={k}
                            data-testid={`adventurer-modal-stat-${k.toLowerCase()}`}
                            className="border border-border rounded-sm p-2 text-center"
                        >
                            <div className="text-[9px] text-muted-foreground tracking-widest">
                                {k}
                            </div>
                            <div className="text-base font-semibold">{v}</div>
                        </div>
                    ))}
                </div>

                {/* Power / Condition */}
                <div className="grid grid-cols-2 gap-2 mt-3 text-xs">
                    <div className="border border-border rounded-sm p-2 flex justify-between">
                        <span className="text-muted-foreground">
                            {t("adventurer_modal.total_power")}
                        </span>
                        <span data-testid="adventurer-modal-power" className="font-semibold">
                            {adventurer.total_power}
                        </span>
                    </div>
                    <div className="border border-border rounded-sm p-2 flex justify-between">
                        <span className="text-muted-foreground">
                            {t("adventurer_modal.condition")}
                        </span>
                        <span className="text-muted-foreground italic text-[11px]">
                            {t("adventurer_modal.condition_rested")}
                        </span>
                    </div>
                </div>

                {/* Specialization (ROUND 6C) — rendered only when present */}
                <SpecializationPanel
                    spec={adventurer.specialization}
                    lang={lang}
                    t={t}
                />

                {/* Traits */}
                <div className="mt-5">
                    <div className="text-[10px] text-muted-foreground tracking-widest mb-2">
                        {t("adventurer_modal.traits")}
                    </div>
                    {(!adventurer.traits || adventurer.traits.length === 0) ? (
                        <div className="text-xs text-muted-foreground italic">
                            {t("adventurer_modal.no_traits")}
                        </div>
                    ) : (
                        <>
                            <TraitList traits={adventurer.traits} testid="adventurer-modal-traits" />
                            <ul className="mt-2 text-[11px] text-muted-foreground space-y-1">
                                {adventurer.traits.map((tr) => (
                                    <li key={tr.id || getTraitLabel(tr)}>
                                        <span className="text-foreground">{getTraitLabel(tr)}</span>
                                        {tr.description ? ` — ${tr.description}` : ""}
                                    </li>
                                ))}
                            </ul>
                        </>
                    )}
                </div>

                {/* Equipment */}
                <div className="mt-5">
                    <div className="text-[10px] text-muted-foreground tracking-widest mb-2">
                        {t("adventurer_modal.equipment")}
                    </div>
                    <div className="space-y-2">
                        {SLOTS.map((slot) => {
                            const eq = equipment[slot];
                            const it = eq?.item;
                            if (!it) {
                                return (
                                    <div
                                        key={slot}
                                        data-testid={`adventurer-modal-slot-${slot}`}
                                        className="border border-border rounded-sm p-2 flex items-center justify-between"
                                    >
                                        <span className="text-[10px] text-muted-foreground uppercase tracking-widest">
                                            {t(`adventurer_modal.slot_${slot}`)}
                                        </span>
                                        <span className="text-xs text-muted-foreground italic">
                                            {t("adventurer_modal.slot_empty")}
                                        </span>
                                    </div>
                                );
                            }
                            const rarity = (it.rarity || "").toLowerCase();
                            const color = RARITY_COLOR[rarity] || RARITY_COLOR.common;
                            const bonuses = formatItemBonuses(it);
                            return (
                                <div
                                    key={slot}
                                    data-testid={`adventurer-modal-slot-${slot}`}
                                    className="border border-border rounded-sm p-2"
                                >
                                    <div className="flex items-center justify-between gap-2">
                                        <div className="flex items-center gap-2 min-w-0">
                                            <span className="text-[9px] text-muted-foreground uppercase tracking-widest shrink-0">
                                                {t(`adventurer_modal.slot_${slot}`)}
                                            </span>
                                            <span className="text-sm font-medium truncate">{it.name}</span>
                                        </div>
                                        <span
                                            className="text-[10px] tracking-widest border px-1.5 py-0.5 rounded-sm shrink-0"
                                            style={{ color, borderColor: color + "55" }}
                                        >
                                            {(RARITY_LABEL[rarity] || rarity).toUpperCase()}
                                        </span>
                                    </div>
                                    {bonuses && (
                                        <div className="text-[11px] text-amber mt-1">{bonuses}</div>
                                    )}
                                </div>
                            );
                        })}
                    </div>

                    <div className="mt-4 flex items-center justify-end gap-2">
                        <button
                            type="button"
                            data-testid={`auto-equip-btn-${adventurer.id}`}
                            onClick={handleAutoEquip}
                            disabled={autoEquipBusy}
                            className="px-3 py-1.5 rounded-sm text-xs font-medium tracking-wide bg-amber-400/90 text-black hover:bg-amber-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            {autoEquipBusy ? "Equipaggiando…" : "Auto-Equipaggia"}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
