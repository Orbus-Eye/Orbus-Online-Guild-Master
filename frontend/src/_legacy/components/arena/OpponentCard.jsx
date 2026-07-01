// ROUND 12.B — OpponentCard for matchmaking list.
// PII guard: visualizza solo guild_public_id/nome/lega/rating/band/last_active.
import { Button } from "../ui/button";
import LeagueBadge from "./LeagueBadge";
import RatingChip from "./RatingChip";

export default function OpponentCard({ opp, onChallenge, disabled }) {
    return (
        <div
            data-testid={`opponent-card-${opp.guild_public_id}`}
            className="border border-border bg-card rounded-sm p-3 flex flex-col gap-2"
        >
            <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                    <div className="font-mono text-sm truncate" data-testid="opponent-name">
                        {opp.guild_name}
                    </div>
                    <div className="text-[10px] text-muted-foreground mt-0.5">
                        {opp.last_active_relative ? `Attiva ${opp.last_active_relative}` : "—"}
                    </div>
                </div>
                <LeagueBadge league={opp.league} />
            </div>
            <div className="flex items-center gap-2 flex-wrap">
                <RatingChip rating={opp.rating} />
                <span className="text-[10px] text-muted-foreground px-2 py-1 border border-border rounded-sm">
                    PWR {opp.total_power_band}
                </span>
                <span className="text-[10px] text-muted-foreground px-2 py-1 border border-border rounded-sm">
                    Lv ⌀ {opp.average_level}
                </span>
            </div>
            <Button
                size="sm"
                data-testid={`challenge-btn-${opp.guild_public_id}`}
                disabled={disabled}
                onClick={() => onChallenge?.(opp)}
            >
                Sfida
            </Button>
        </div>
    );
}
