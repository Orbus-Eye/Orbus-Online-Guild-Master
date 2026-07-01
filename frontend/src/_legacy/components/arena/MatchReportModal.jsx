// ROUND 12.B — MatchReportModal: fullscreen modale che mostra i 5 round IT.
import { useEffect } from "react";
import { Button } from "../ui/button";
import RatingChip from "./RatingChip";

const OUTCOME_LABEL = {
    attacker_win: { it: "Vittoria", cls: "text-emerald-400" },
    defender_win: { it: "Sconfitta", cls: "text-red-400" },
    draw: { it: "Pareggio", cls: "text-amber" },
};

export default function MatchReportModal({ match, onClose, myGuildId }) {
    useEffect(() => {
        const onKey = (e) => { if (e.key === "Escape") onClose?.(); };
        window.addEventListener("keydown", onKey);
        return () => window.removeEventListener("keydown", onKey);
    }, [onClose]);

    if (!match) return null;

    const iAmAttacker = match.attacker_guild_id === myGuildId;
    const rawOutcome = match.outcome;
    // Outcome from MY POV:
    let myOutcomeKey = rawOutcome;
    if (!iAmAttacker) {
        myOutcomeKey = rawOutcome === "attacker_win"
            ? "defender_win"
            : rawOutcome === "defender_win"
                ? "attacker_win"
                : "draw";
    }
    const myDelta = iAmAttacker
        ? (match.rating_delta_attacker ?? null)
        : (match.rating_delta_defender ?? null);
    // For display purposes: "Vittoria/Sconfitta" sempre dal mio POV.
    const myLabel = myOutcomeKey === "draw"
        ? { it: "Pareggio", cls: "text-amber" }
        : iAmAttacker
            ? OUTCOME_LABEL[rawOutcome]
            : (rawOutcome === "attacker_win"
                ? { it: "Sconfitta", cls: "text-red-400" }
                : { it: "Vittoria", cls: "text-emerald-400" });

    return (
        <div
            data-testid="match-report-modal"
            className="fixed inset-0 z-50 bg-background/90 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto"
            onClick={onClose}
        >
            <div
                className="bg-card border border-border rounded-sm max-w-2xl w-full p-5"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-sm tracking-[0.3em] text-amber">:: Resoconto Battaglia</h2>
                    <Button variant="ghost" size="sm" onClick={onClose} data-testid="match-close-btn">
                        Chiudi
                    </Button>
                </div>

                <div className="mb-4 grid grid-cols-2 gap-3 text-xs">
                    <div className="border border-border rounded-sm p-2">
                        <div className="text-[10px] text-muted-foreground">Attaccante</div>
                        <div className="font-mono">{match.attacker_guild_name}</div>
                        <div className="text-[10px] text-muted-foreground mt-1">Punteggio finale: <strong className="text-foreground">{match.final_attack_score}</strong></div>
                    </div>
                    <div className="border border-border rounded-sm p-2">
                        <div className="text-[10px] text-muted-foreground">Difensore</div>
                        <div className="font-mono">{match.defender_guild_name}</div>
                        <div className="text-[10px] text-muted-foreground mt-1">Punteggio finale: <strong className="text-foreground">{match.final_defense_score}</strong></div>
                    </div>
                </div>

                <div className="mb-4 flex items-center justify-between flex-wrap gap-2">
                    <span data-testid="match-outcome" className={`text-lg font-semibold ${myLabel.cls}`}>
                        {myLabel.it}
                    </span>
                    {myDelta != null && <RatingChip rating={match.rating_applied ? "" : ""} delta={myDelta} size="lg" />}
                </div>

                <div className="space-y-2" data-testid="match-rounds">
                    {(match.report_it || []).map((line, idx) => (
                        <div
                            key={`round-${idx}`}
                            data-testid={`match-round-${idx}`}
                            className="border border-border/60 bg-secondary/30 rounded-sm p-2 text-[13px] leading-relaxed"
                        >
                            {line}
                        </div>
                    ))}
                </div>

                <p className="mt-4 text-[10px] text-muted-foreground font-mono">
                    Combat v{match.combat_version} · RNG {match.rng_version} · seed {match.seed_hash}
                </p>
            </div>
        </div>
    );
}
