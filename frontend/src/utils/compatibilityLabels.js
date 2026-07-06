/*
 * 🔒 R18.4.followup — UI 4-State Item Compatibility Activation — CLOSED & SEALED
 * R18.4.followup CLOSED & SEALED
 * DO NOT MODIFY. SHA256 verified in /app/backend/tests/backend_r18_4_sealed_integrity_test.py
 */
// R18.4.followup Phase B — UI 4-state compatibility labels + icons
// Governance: solo mapping enum → label IT + icona lucide-react.
// Zero logica policy (server-side responsability).

import { Ban, AlertTriangle, CheckCircle2, Globe, HelpCircle } from "lucide-react";

// Enum values locked in B.SQ (Phase B PM decisions):
//   compatibility_state: "blocked" | "not_recommended" | "recommended" | "universal"

export const COMPATIBILITY_LABELS_IT = {
    blocked: "Bloccato",
    not_recommended: "Non consigliato",
    recommended: "Consigliato",
    universal: "Universale",
};

export const COMPATIBILITY_ICONS = {
    blocked: Ban,
    not_recommended: AlertTriangle,
    recommended: CheckCircle2,
    universal: Globe,
};

// Tailwind color classes per stato (minimalista, no gradient, coerenti col PRD)
export const COMPATIBILITY_COLORS = {
    blocked: "text-red-600 border-red-600/40 bg-red-50 dark:bg-red-950/30",
    not_recommended: "text-amber-700 border-amber-600/40 bg-amber-50 dark:bg-amber-950/30",
    recommended: "text-green-700 border-green-600/40 bg-green-50 dark:bg-green-950/30",
    universal: "text-blue-700 border-blue-600/40 bg-blue-50 dark:bg-blue-950/30",
};

// Reason code → estensione IT per accessibility aria-label (B.SQ4)
export const REASON_CODE_LABELS_IT = {
    universal_item: "Item universale, equipaggiabile da qualsiasi classe",
    class_recommended: "Consigliato per questa classe",
    class_mismatch_soft: "Non consigliato per questa classe (equip permesso)",
    class_mismatch_hard: "Bloccato: questa classe non può equipaggiare questo item",
    slot_missing: "Slot non definito per questo item",
};

export const FALLBACK_ICON = HelpCircle;
export const FALLBACK_LABEL_IT = "Non determinato";

/**
 * Risolve lo slot da un item con fallback: preferisce `slot_type` (R18.4 canonical)
 * al legacy `item_type`. Necessario per shield items (item_type=shield, slot_type=armor).
 * B.SQ5 lock.
 *
 * @param {Object} item - Il documento item pubblico.
 * @returns {string|undefined} Lo slot risolto o undefined se nessuno dei due presente.
 */
export function resolveItemSlot(item) {
    if (!item) return undefined;
    return item.slot_type ?? item.item_type;
}
