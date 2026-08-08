/*
 * 🔒 R18.4.followup — UI 4-State Item Compatibility Activation — CLOSED & SEALED
 * R18.4.followup CLOSED & SEALED
 * DO NOT MODIFY. SHA256 verified in /app/backend/tests/backend_r18_4_sealed_integrity_test.py
 */
// R18.4.followup Phase B — ItemCompatibilityBadge
// Componente riutilizzabile per badge UI 4-state (blocked/not_recommended/recommended/universal).
// Props derivano da payload endpoint /api/adventurers/{id}/eligible-items.
// Governance: rendering only, zero policy logic (server-side).

import {
    COMPATIBILITY_LABELS_IT,
    COMPATIBILITY_ICONS,
    COMPATIBILITY_COLORS,
    REASON_CODE_LABELS_IT,
    FALLBACK_ICON,
    FALLBACK_LABEL_IT,
} from "../utils/compatibilityLabels";

/**
 * Badge visivo per lo stato di compatibilità di un item rispetto a un avventuriero.
 *
 * @param {Object} props
 * @param {string} props.compatibilityState - Uno di "blocked"|"not_recommended"|"recommended"|"universal"
 * @param {string} [props.reasonCode] - Optional reason code from backend (per aria-label esteso)
 * @param {string} [props.className] - Optional custom Tailwind classes
 * @param {string} [props.size] - "sm" (default) | "md"
 */
export default function ItemCompatibilityBadge({
    compatibilityState,
    reasonCode,
    className = "",
    size = "sm",
}) {
    const label = COMPATIBILITY_LABELS_IT[compatibilityState] ?? FALLBACK_LABEL_IT;
    const Icon = COMPATIBILITY_ICONS[compatibilityState] ?? FALLBACK_ICON;
    const color = COMPATIBILITY_COLORS[compatibilityState] ?? "text-muted-foreground border-muted";

    const reasonLabel = REASON_CODE_LABELS_IT[reasonCode];
    const ariaLabel = reasonLabel ? `${label}: ${reasonLabel}` : label;

    // Sizing minimalista (B.SQ4 mobile-first: sempre icona + testo, no tooltip complessa)
    const paddingCls = size === "md" ? "px-2 py-1 text-sm" : "px-1.5 py-0.5 text-xs";
    const iconSize = size === "md" ? 16 : 14;

    return (
        <span
            role="status"
            aria-label={ariaLabel}
            data-testid={`item-compat-badge-${compatibilityState || "unknown"}`}
            className={`inline-flex items-center gap-1 rounded border ${color} ${paddingCls} font-medium whitespace-nowrap ${className}`}
        >
            <Icon size={iconSize} aria-hidden="true" />
            <span data-testid={`item-compat-badge-label`}>{label}</span>
        </span>
    );
}

export { ItemCompatibilityBadge };
