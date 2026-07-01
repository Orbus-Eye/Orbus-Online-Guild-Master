// ROUND 12.B — RatingChip: shared visual chip for Elo rating + optional delta.
export default function RatingChip({ rating, delta, size = "sm" }) {
    const cls = size === "lg" ? "text-base px-3 py-1.5" : "text-xs px-2 py-1";
    const deltaCls = delta == null
        ? ""
        : delta > 0
            ? "text-emerald-400"
            : delta < 0
                ? "text-red-400"
                : "text-muted-foreground";
    return (
        <span data-testid="rating-chip" className={`inline-flex items-center gap-1.5 border border-border bg-card rounded-sm font-mono ${cls}`}>
            <span className="text-muted-foreground">Rating</span>
            <strong className="text-foreground">{Number(rating ?? 1000).toLocaleString("it-IT")}</strong>
            {delta != null && delta !== 0 && (
                <span data-testid="rating-delta" className={`${deltaCls}`}>
                    {delta > 0 ? "+" : ""}{delta}
                </span>
            )}
        </span>
    );
}
