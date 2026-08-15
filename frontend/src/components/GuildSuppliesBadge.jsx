// FASE 10F — Beni di Gilda: "85 / 120" con tooltip breve.
// Componente puro: riceve i valori (dalla guild in context o da
// /guild-supplies); non conosce l'API.

const TOOLTIP = "Usati per automatizzare le spedizioni nei dungeon già "
    + "completati. Si ripristinano ogni giorno.";

export default function GuildSuppliesBadge({
    supplies,
    cap = 120,
    compact = false,
}) {
    const value = Number.isFinite(Number(supplies)) ? Number(supplies) : null;
    return (
        <span
            data-testid="guild-supplies-badge"
            title={TOOLTIP}
            className={`inline-flex items-baseline gap-1 ${
                compact ? "" : "border border-amber/40 bg-amber/5 rounded-sm px-2 py-1"
            }`}
        >
            <span className="text-[9px] text-muted-foreground tracking-widest uppercase">
                Beni di Gilda
            </span>
            <span
                data-testid="guild-supplies-value"
                className="text-sm font-semibold text-amber tabular-nums"
            >
                {value === null ? "—" : `${value} / ${cap}`}
            </span>
        </span>
    );
}
