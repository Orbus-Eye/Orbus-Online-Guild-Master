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
import { classLabel } from "../utils/displayLabels";
import axios from "axios";
import { api, API, getCsrfToken } from "../lib/api";
import GameImage from "./GameImage";
import { avatarSources } from "../utils/gameAssets";

const SLOTS = [
    "weapon", "chest", "legs", "head", "accessory", "back",
    "ring_1", "ring_2", "trinket_1", "trinket_2",
];

// ROUND 16.5.4c REOPEN #5 Fix B — slot labels sempre in italiano nel
// modal-scope (adiacente al bottone Auto-Equip). Prima si affidavano a
// `t("adventurer_modal.slot_*")` che restituiva WEAPON/ARMOR/ACCESSORY
// se `lang === "en"`, generando leak player-facing durante il flow
// Auto-Equip. Scope stretto: solo questo componente.
const SLOT_LABEL_IT = {
    weapon: "ARMA",
    chest: "CORAZZA",
    legs: "GAMBE",
    head: "ELMO",
    accessory: "ACCESSORIO",
    back: "SCHIENA",
    ring_1: "ANELLO I",
    ring_2: "ANELLO II",
    trinket_1: "MONILE I",
    trinket_2: "MONILE II",
};

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
    // ROUND 16.1 Phase 3 — keep the response to render a bilingual report.
    const [autoEquipResult, setAutoEquipResult] = useState(null);
    // FASE 3.3 — annulla consumabile attivo.
    const [consumableBusy, setConsumableBusy] = useState(false);
    // FASE 6 — upload/rimozione ritratto personalizzato.
    const [avatarBusy, setAvatarBusy] = useState(false);
    const avatarInputRef = useRef(null);

    const handleAvatarFile = async (event) => {
        const file = event.target.files?.[0];
        event.target.value = "";  // stesso file ricaricabile
        if (!file || !adventurer?.id) return;
        if (file.size > 2 * 1024 * 1024) {
            toast.error("Immagine troppo grande: massimo 2 MB.");
            return;
        }
        setAvatarBusy(true);
        try {
            const fd = new FormData();
            fd.append("file", file);
            await axios.post(
                `${API}/adventurers/${adventurer.id}/avatar`, fd,
                {
                    withCredentials: true,
                    headers: { "X-CSRF-Token": getCsrfToken() || "" },
                },
            );
            toast.success("Ritratto aggiornato!");
            if (typeof onChanged === "function") onChanged(adventurer.id);
        } catch (err) {
            const msg = err?.response?.data?.detail?.user_message
                || "Caricamento del ritratto fallito.";
            toast.error(msg);
        } finally {
            setAvatarBusy(false);
        }
    };

    const handleAvatarRemove = async () => {
        if (!adventurer?.id || avatarBusy) return;
        setAvatarBusy(true);
        try {
            await api.delete(`/adventurers/${adventurer.id}/avatar`);
            toast.success("Ritratto rimosso: torna l'avatar della razza.");
            if (typeof onChanged === "function") onChanged(adventurer.id);
        } catch (err) {
            const msg = err?.response?.data?.detail?.user_message
                || "Rimozione fallita.";
            toast.error(msg);
        } finally {
            setAvatarBusy(false);
        }
    };

    const handleCancelConsumable = async () => {
        if (!adventurer?.id || consumableBusy) return;
        setConsumableBusy(true);
        try {
            await api.delete(`/adventurers/${adventurer.id}/consumable`);
            toast.success("Consumabile annullato (cariche residue perse).");
            if (typeof onChanged === "function") onChanged(adventurer.id);
        } catch (err) {
            const msg = err?.response?.data?.detail?.user_message
                || "Impossibile annullare il consumabile.";
            toast.error(msg);
        } finally {
            setConsumableBusy(false);
        }
    };

    const handleAutoEquip = async () => {
        if (!adventurer?.id || autoEquipBusy) return;
        setAutoEquipBusy(true);
        try {
            const r = await api.post(`/adventurers/${adventurer.id}/auto-equip`);
            const s = r.data || {};
            setAutoEquipResult(s);
            const delta = (s.score_after ?? 0) - (s.score_before ?? 0);
            const swaps = s.swaps_count ?? 0;
            if (swaps === 0) {
                // ROUND 16.5.4c REOPEN #5 — Auto-Equip toast sempre IT
                // (scope stretto: player-facing dell'Auto-Equip).
                toast.info("Nessuna sostituzione possibile.", {
                    description:
                        "Nessun oggetto compatibile più forte in inventario.",
                });
            } else {
                // ROUND 16.5.4c REOPEN #5 — toast successo sempre IT.
                toast.success(
                    `${swaps} oggett${swaps === 1 ? "o aggiornato" : "i aggiornati"}`,
                    {
                        description: `Potere ${s.score_before ?? 0} → ${s.score_after ?? 0} (${delta >= 0 ? "+" : ""}${delta})`,
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

    const xpNeeded = adventurer.experience_to_next_level;
    const atLevelCap = xpNeeded === null;
    const safeXpNeeded = Math.max(1, xpNeeded || 1);
    const xpCurrent = Math.max(0, Math.min(safeXpNeeded, adventurer.experience || 0));
    const xpPct = atLevelCap ? 100 : Math.round((xpCurrent / safeXpNeeded) * 100);
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
                    className="text-2xl font-semibold tracking-tight flex items-center gap-3 flex-wrap"
                >
                    {/* FASE 4 — ritratto razza/genere */}
                    <GameImage
                        sources={avatarSources(adventurer)}
                        alt=""
                        className="w-14 h-14 rounded-full border-2 border-amber/40 shrink-0"
                    />
                    <span className="font-fantasy">{adventurer.name}</span>
                    <SpecChip
                        spec={adventurer.specialization}
                        lang={lang}
                        testid="adventurer-modal-spec-chip"
                    />
                </h2>
                <div className="text-xs text-muted-foreground mt-1">
                    {classLabel(adventurer.class_slug) || adventurer.class_name} · {adventurer.class_role} ·{" "}
                    {t("adventurer_modal.level", { n: adventurer.level })}
                </div>
                {/* FASE 6 — gestione ritratto personalizzato */}
                <div className="mt-2 flex items-center gap-2 flex-wrap">
                    <input
                        ref={avatarInputRef}
                        type="file"
                        accept="image/png,image/jpeg,image/webp"
                        className="hidden"
                        data-testid={`avatar-file-input-${adventurer.id}`}
                        onChange={handleAvatarFile}
                    />
                    <button
                        type="button"
                        data-testid={`avatar-upload-btn-${adventurer.id}`}
                        disabled={avatarBusy}
                        onClick={() => avatarInputRef.current?.click()}
                        className="text-[10px] tracking-widest border border-border text-muted-foreground px-2 py-1 rounded-sm hover:bg-secondary disabled:opacity-50"
                        title="PNG, JPEG o WEBP · massimo 2 MB"
                    >
                        {avatarBusy ? "…" : "🖼 CAMBIA RITRATTO"}
                    </button>
                    {adventurer.custom_avatar_url && (
                        <button
                            type="button"
                            data-testid={`avatar-remove-btn-${adventurer.id}`}
                            disabled={avatarBusy}
                            onClick={handleAvatarRemove}
                            className="text-[10px] tracking-widest border border-border text-muted-foreground px-2 py-1 rounded-sm hover:bg-secondary disabled:opacity-50"
                        >
                            ✖ RIMUOVI
                        </button>
                    )}
                </div>
                {/* ROUND 16.0 — Race + Gender row (prominent, IT). */}
                {(adventurer.race_slug || adventurer.gender) && (
                    <div
                        data-testid="adventurer-modal-race-gender"
                        className="text-xs text-amber/85 mt-1.5"
                        aria-label={`Razza ${adventurer.race_name_it || adventurer.race_slug || 'sconosciuta'}, sesso ${adventurer.gender === 'female' ? 'Femmina' : adventurer.gender === 'male' ? 'Maschio' : 'sconosciuto'}`}
                    >
                        <span className="text-muted-foreground">Razza:</span>{" "}
                        <span className="text-foreground">
                            {adventurer.race_name_it || (adventurer.race_slug
                                ? adventurer.race_slug.replace(/_/g, ' ')
                                : '—')}
                        </span>
                        {adventurer.gender && (
                            <>
                                {" · "}
                                <span className="text-muted-foreground">Sesso:</span>{" "}
                                <span className="text-foreground">
                                    {adventurer.gender === 'female' ? 'Femmina ♀' : 'Maschio ♂'}
                                </span>
                            </>
                        )}
                    </div>
                )}

                {/* XP progress */}
                <div className="mt-5">
                    <div className="flex items-center justify-between text-[10px] text-muted-foreground tracking-widest mb-1.5">
                        <span>{t("adventurer_modal.experience")}</span>
                        <span data-testid="adventurer-modal-xp">
                            {atLevelCap ? "LIVELLO MASSIMO" : `${xpCurrent} / ${safeXpNeeded}`}
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

                {adventurer.career && (
                    <div
                        className="mt-4 border border-amber/25 bg-amber/5 p-3 rounded-sm"
                        data-testid="adventurer-career-progress"
                    >
                        <div className="flex justify-between gap-3 text-[10px] tracking-widest">
                            <span className="text-amber">CARRIERA · {adventurer.career.rarity}</span>
                            <span className="text-muted-foreground">
                                STAT ×{adventurer.career.stat_multiplier} · {adventurer.career.dungeons_completed} dungeon · {adventurer.career.raids_completed} raid
                            </span>
                        </div>
                        {adventurer.career.next_rarity ? (
                            <p className="text-[11px] text-muted-foreground mt-2">
                                Prossimo grado: <strong className="text-foreground">{adventurer.career.next_rarity}</strong>.
                                Mancano {adventurer.career.remaining.dungeons} dungeon
                                {adventurer.career.remaining.raids > 0
                                    ? ` e ${adventurer.career.remaining.raids} raid`
                                    : ""}.
                            </p>
                        ) : (
                            <p className="text-[11px] text-amber mt-2">Grado Leggendario raggiunto.</p>
                        )}
                    </div>
                )}

                {/* Stats */}
                <div className="grid grid-cols-5 gap-2 mt-5">
                    {[
                        ["STR", adventurer.strength],
                        ["AGI", adventurer.agility],
                        ["INT", adventurer.intellect],
                        ["END", adventurer.endurance],
                        ["FAI", adventurer.faith],
                    ].map(([k, v], index) => {
                        const statKeys = ["strength", "agility", "intellect", "endurance", "faith"];
                        const baseValue = adventurer.base_stats?.[statKeys[index]];
                        return (
                        <div
                            key={k}
                            data-testid={`adventurer-modal-stat-${k.toLowerCase()}`}
                            className="border border-border rounded-sm p-2 text-center"
                        >
                            <div className="text-[9px] text-muted-foreground tracking-widest">
                                {k}
                            </div>
                            <div className="text-base font-semibold">{v}</div>
                            {adventurer.rarity_stat_multiplier > 1 && baseValue != null && (
                                <div className="text-[8px] text-muted-foreground">
                                    {baseValue} × {adventurer.rarity_stat_multiplier}
                                </div>
                            )}
                        </div>
                        );
                    })}
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
                                            {SLOT_LABEL_IT[slot]}
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
                                                {SLOT_LABEL_IT[slot]}
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

                    {/* FASE 3.3 — scomparto Consumabile */}
                    {adventurer.active_consumable?.charges_left > 0 && (
                        <div
                            className="mt-4 border border-amber/40 bg-amber/5 rounded-sm p-3 flex items-center justify-between gap-3 flex-wrap"
                            data-testid={`adv-consumable-${adventurer.id}`}
                        >
                            <div className="text-[11px]">
                                <span className="text-amber font-semibold">
                                    ✨ {adventurer.active_consumable.name_it}
                                </span>{" "}
                                <span className="text-muted-foreground">
                                    {adventurer.active_consumable.type === "xp_boost"
                                        ? `+${Math.round((adventurer.active_consumable.magnitude || 0) * 100)}% XP`
                                        : `+${adventurer.active_consumable.magnitude} potere`}
                                    {" · "}
                                    {adventurer.active_consumable.charges_left} spedizioni rimaste
                                </span>
                            </div>
                            <button
                                type="button"
                                data-testid={`adv-consumable-cancel-${adventurer.id}`}
                                onClick={handleCancelConsumable}
                                disabled={consumableBusy}
                                className="text-[10px] tracking-widest border border-border text-muted-foreground px-2 py-1 rounded-sm hover:bg-secondary disabled:opacity-50"
                            >
                                {consumableBusy ? "…" : "ANNULLA"}
                            </button>
                        </div>
                    )}

                    <div className="mt-4 flex items-center justify-end gap-2">
                        <button
                            type="button"
                            data-testid={`auto-equip-btn-${adventurer.id}`}
                            onClick={handleAutoEquip}
                            disabled={autoEquipBusy}
                            className="px-3 py-1.5 rounded-sm text-xs font-medium tracking-wide bg-amber-400/90 text-black hover:bg-amber-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            {autoEquipBusy
                                ? (lang === "it" ? "Equipaggiando…" : "Equipping…")
                                : (lang === "it" ? "Auto-Equipaggia" : "Auto-Equip")}
                        </button>
                    </div>

                    {/* ROUND 16.1 Phase 3 — bilingual auto-equip report */}
                    {autoEquipResult && (
                        <AutoEquipReport
                            result={autoEquipResult}
                            lang={lang}
                            onDismiss={() => setAutoEquipResult(null)}
                        />
                    )}
                </div>
            </div>
        </div>
    );
}

// ROUND 16.1 Phase 3 — Inline report panel rendered after Auto-Equip click.
// ROUND 16.5.4c REOPEN — Il PM ha stabilito che il report Auto-Equip
// deve essere SEMPRE in italiano (payload backend `reason_it` /
// `unchanged_slots_detail[].reason_it`), a prescindere dal `lang`
// dell'utente. Motivi:
//   1. Il PM non ha ancora deciso una politica i18n globale.
//   2. Il backend R16.5.4b/c popola `reason_it` completo e leggibile;
//      `reason_en` è un semplice fallback tecnico.
//   3. Nomi item off-class rimangono già filtrati lato backend.
// Il resto della UI (label esterne del pannello) resta bilingue via
// `lang` — questo scope è ristretto alle stringhe player-facing del
// report Auto-Equip come da spec R16.5.4c REOPEN #3.
function AutoEquipReport({ result, lang, onDismiss }) {
    const it = lang === "it";
    const delta = result.score_delta ?? ((result.score_after ?? 0) - (result.score_before ?? 0));
    const deltaColor = delta > 0 ? "text-emerald-400" : delta < 0 ? "text-destructive" : "text-muted-foreground";
    const reasons = result.reasons || [];
    const unchanged = result.unchanged_slots_detail || [];
    // Piccolo helper: preferisce sempre `reason_it`; solo se assente
    // (edge case in dati legacy) fa fallback a `reason_en`.
    const pickReport = (row) => row?.reason_it || row?.reason_en || "";
    return (
        <div
            data-testid="auto-equip-report"
            className="mt-4 border border-amber/40 bg-amber/5 rounded-sm p-3 text-sm"
        >
            <div className="flex items-baseline justify-between gap-3 mb-2">
                <div>
                    <div className="text-[10px] text-amber tracking-widest">
                        {it ? ":: REPORT AUTO-EQUIP" : ":: AUTO-EQUIP REPORT"}
                    </div>
                    <div className="text-sm mt-0.5">
                        {it ? "Potere" : "Power"}{" "}
                        <span className="font-semibold">{result.score_before}</span>{" "}
                        →{" "}
                        <span className="font-semibold">{result.score_after}</span>{" "}
                        <span
                            data-testid="auto-equip-delta"
                            className={`${deltaColor} font-bold tracking-wide`}
                        >
                            ({delta >= 0 ? "+" : ""}{delta})
                        </span>
                    </div>
                </div>
                <button
                    type="button"
                    data-testid="auto-equip-report-dismiss"
                    onClick={onDismiss}
                    className="text-[10px] tracking-widest text-muted-foreground hover:text-foreground border border-border rounded-sm px-2 py-0.5"
                >
                    {it ? "CHIUDI" : "DISMISS"}
                </button>
            </div>

            {reasons.length > 0 && (
                <section className="mb-2">
                    <div className="text-[10px] text-muted-foreground tracking-widest mb-1">
                        {it ? ":: MIGLIORAMENTI" : ":: IMPROVEMENTS"}
                    </div>
                    <ul className="space-y-1">
                        {reasons.map((r, i) => (
                            <li
                                key={`${r.slot}-${i}`}
                                data-testid={`auto-equip-reason-${r.slot}`}
                                className="text-xs border-l-2 border-emerald-400/55 pl-2 py-0.5"
                            >
                                <div className="text-foreground/90">
                                    {pickReport(r)}
                                </div>
                                {r.stat_delta && Object.keys(r.stat_delta).length > 0 && (
                                    <div className="text-[10px] text-muted-foreground mt-0.5">
                                        {Object.entries(r.stat_delta)
                                            .map(([k, v]) => `${v > 0 ? "+" : ""}${v} ${k}`)
                                            .join(" · ")}
                                    </div>
                                )}
                            </li>
                        ))}
                    </ul>
                </section>
            )}

            {unchanged.length > 0 && (
                <section>
                    <div className="text-[10px] text-muted-foreground tracking-widest mb-1">
                        {it ? ":: SLOT NON MIGLIORATI" : ":: UNCHANGED SLOTS"}
                    </div>
                    <ul className="space-y-0.5">
                        {unchanged.map((u, i) => (
                            <li
                                key={`${u.slot}-${i}`}
                                data-testid={`auto-equip-unchanged-${u.slot}`}
                                className="text-xs text-muted-foreground italic border-l-2 border-border pl-2 py-0.5"
                            >
                                {pickReport(u)}
                            </li>
                        ))}
                    </ul>
                </section>
            )}

            {(result.swaps_count ?? 0) === 0 && reasons.length === 0 && (
                <p className="text-xs text-muted-foreground italic">
                    {/* ROUND 16.5.4c REOPEN #5 — messaggio empty state
                        sempre IT (scope stretto: Auto-Equip report). */}
                    Nessun oggetto migliore disponibile in inventario.
                    Visita il mercato o completa spedizioni/dungeon.
                </p>
            )}
        </div>
    );
}
