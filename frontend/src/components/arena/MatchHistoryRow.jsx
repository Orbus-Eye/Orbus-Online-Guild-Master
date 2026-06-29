// ROUND 12.B — MatchHistoryRow.
import RatingChip from "./RatingChip";

const OUTCOME_ICON = {
    attacker_win: "⚔️",
    defender_win: "🛡️",
    draw: "🤝",
};

function fmtRelative(iso) {
    if (!iso) return "—";
    const t = new Date(iso);
    const diff = (Date.now() - t.getTime()) / 1000;
    if (diff < 60) return "ora";
    if (diff < 3600) return `${Math.floor(diff / 60)}m fa`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h fa`;
    return `${Math.floor(diff / 86400)}g fa`;
}

export default function MatchHistoryRow({ match, myGuildId, onOpen }) {
    const iAmAttacker = match.attacker_guild_id === myGuildId;
    const opponentName = iAmAttacker ? match.defender_guild_name : match.attacker_guild_name;
    const role = iAmAttacker ? "ATT" : "DEF";
    let _myOutcome = match.outcome;
    if (!iAmAttacker) {
        _myOutcome = match.outcome === "attacker_win"
            ? "defender_win"
            : match.outcome === "defender_win"
                ? "attacker_win"
                : "draw";
    }
    const won = (iAmAttacker && match.outcome === "attacker_win")
        || (!iAmAttacker && match.outcome === "defender_win");
    const lost = (iAmAttacker && match.outcome === "defender_win")
        || (!iAmAttacker && match.outcome === "attacker_win");

    const delta = iAmAttacker
        ? match.rating_delta_attacker
        : match.rating_delta_defender;

    const outcomeCls = won ? "text-emerald-400" : lost ? "text-red-400" : "text-amber";
    const outcomeLabel = won ? "Vittoria" : lost ? "Sconfitta" : "Pareggio";

    return (
        <button
            type="button"
            data-testid={`match-row-${match.match_id}`}
            onClick={() => onOpen?.(match)}
            className="w-full flex items-center justify-between gap-3 border border-border rounded-sm bg-card hover:bg-secondary/40 transition-colors p-3 text-left"
        >
            <div className="flex items-center gap-3 min-w-0">
                <span aria-hidden className="text-lg shrink-0">{OUTCOME_ICON[match.outcome] || "•"}</span>
                <div className="min-w-0">
                    <div className="text-xs font-mono truncate">
                        <span className="text-muted-foreground mr-1.5">[{role}]</span>
                        vs {opponentName}
                    </div>
                    <div className="text-[10px] text-muted-foreground">{fmtRelative(match.created_at)}</div>
                </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
                <span className={`text-[11px] font-semibold ${outcomeCls}`}>{outcomeLabel}</span>
                {delta != null && delta !== 0 && (
                    <RatingChip rating={0} delta={delta} />
                )}
            </div>
        </button>
    );
}
