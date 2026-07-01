// Badge rarità riutilizzabile — preparato per fasi future (drop di oggetti).
// Non usato in Fase 1 ma parte del kit visuale sobrio.
import { cn } from "@/lib/utils";

const STYLES = {
    common: "border-zinc-700 text-zinc-400",
    uncommon: "border-emerald-800 text-emerald-400",
    rare: "border-sky-800 text-sky-400",
    epic: "border-violet-800 text-violet-400",
};

const LABELS = {
    common: "Comune",
    uncommon: "Non comune",
    rare: "Raro",
    epic: "Epico",
};

export default function RarityBadge({ rarity = "common", className }) {
    const key = String(rarity).toLowerCase();
    const style = STYLES[key] ?? STYLES.common;
    const label = LABELS[key] ?? key;
    return (
        <span
            data-testid={`rarity-badge-${key}`}
            className={cn(
                "inline-flex items-center rounded-sm border px-1.5 py-0.5 text-[10px] uppercase tracking-wider",
                style,
                className,
            )}
        >
            {label}
        </span>
    );
}
