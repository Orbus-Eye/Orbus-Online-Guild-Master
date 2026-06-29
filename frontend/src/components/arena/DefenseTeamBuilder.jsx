// ROUND 12.B — DefenseTeamBuilder.
// 5-slot picker. Mostra ruoli, livello, PWR. Greying degli avventurieri
// non eligibili. Bottone "Salva difesa" disabilitato finché team non valido.
import { useMemo, useState } from "react";
import { Button } from "../ui/button";
import { pvpEligibility } from "../../utils/pvpEligibility";

export default function DefenseTeamBuilder({
    adventurers = [],
    minLevel = 3,
    initialIds = [],
    onSave,
    saving = false,
    title = "Squadra Difensiva",
}) {
    const [chosenIds, setChosenIds] = useState(initialIds);

    const advById = useMemo(() => {
        const m = {};
        adventurers.forEach((a) => { m[a.id] = a; });
        return m;
    }, [adventurers]);

    const toggle = (id) => {
        setChosenIds((cur) => {
            if (cur.includes(id)) return cur.filter((x) => x !== id);
            if (cur.length >= 5) return cur;
            return [...cur, id];
        });
    };

    const isComplete = chosenIds.length === 5;

    // Composition summary
    const chosen = chosenIds.map((id) => advById[id]).filter(Boolean);
    const roles = chosen.reduce((acc, a) => {
        const r = a.role || "?";
        acc[r] = (acc[r] || 0) + 1;
        return acc;
    }, {});
    const totalPower = chosen.reduce((s, a) => s + (a.team_power || 0), 0);
    const avgLevel = chosen.length ? Math.round((chosen.reduce((s, a) => s + (a.level || 0), 0) / chosen.length) * 100) / 100 : 0;

    return (
        <div data-testid="defense-team-builder" className="border border-border bg-card rounded-sm p-4">
            <h3 className="text-sm tracking-[0.25em] text-amber mb-3">:: {title}</h3>

            {/* Slot summary */}
            <div className="flex items-center gap-2 mb-4 flex-wrap" data-testid="defense-slots">
                {[0, 1, 2, 3, 4].map((i) => {
                    const id = chosenIds[i];
                    const a = id ? advById[id] : null;
                    return (
                        <div
                            key={`slot-${i}`}
                            data-testid={`defense-slot-${i}`}
                            className={`border ${a ? "border-amber/60" : "border-dashed border-border"} rounded-sm px-2 py-1.5 text-xs min-w-[110px]`}
                        >
                            {a ? (
                                <>
                                    <div className="font-mono truncate">{a.name}</div>
                                    <div className="text-[10px] text-muted-foreground">
                                        Lv {a.level} · {a.role || "?"}
                                    </div>
                                </>
                            ) : (
                                <span className="text-muted-foreground text-[11px]">Slot {i + 1}</span>
                            )}
                        </div>
                    );
                })}
            </div>

            {/* Composition stats */}
            {chosen.length > 0 && (
                <div data-testid="defense-summary" className="mb-3 flex flex-wrap gap-3 text-[11px] text-muted-foreground">
                    <span>Totale PWR: <strong className="text-foreground">{totalPower}</strong></span>
                    <span>Livello medio: <strong className="text-foreground">{avgLevel}</strong></span>
                    <span>Ruoli: {Object.entries(roles).map(([r, n]) => `${r}×${n}`).join(", ") || "—"}</span>
                </div>
            )}

            {/* Adventurer picker grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2 max-h-[420px] overflow-y-auto" data-testid="defense-roster-grid">
                {adventurers.map((a) => {
                    const elig = pvpEligibility(a, { minLevel, alreadyChosenIds: chosenIds });
                    const picked = chosenIds.includes(a.id);
                    const disabled = !elig.eligible && !picked;
                    return (
                        <button
                            type="button"
                            key={a.id}
                            data-testid={`defense-pick-${a.id}`}
                            disabled={disabled}
                            onClick={() => toggle(a.id)}
                            className={`text-left border rounded-sm p-2 text-xs transition-colors ${
                                picked
                                    ? "border-amber/70 bg-amber/10 text-foreground"
                                    : disabled
                                        ? "border-border/40 bg-card/40 text-muted-foreground opacity-50 cursor-not-allowed"
                                        : "border-border bg-card hover:bg-secondary/40 text-foreground"
                            }`}
                            title={elig.reason || ""}
                        >
                            <div className="font-mono truncate">{a.name}</div>
                            <div className="text-[10px] text-muted-foreground">
                                Lv {a.level} · {a.role || "?"} · PWR {a.team_power || 0}
                            </div>
                            {disabled && (
                                <div className="text-[9px] text-red-400/80 mt-0.5">{elig.reason}</div>
                            )}
                        </button>
                    );
                })}
                {adventurers.length === 0 && (
                    <p className="col-span-full text-[11px] text-muted-foreground italic">
                        Nessun avventuriere disponibile.
                    </p>
                )}
            </div>

            <div className="mt-4 flex items-center justify-between gap-3">
                <p className="text-[11px] text-muted-foreground" data-testid="defense-counter">
                    {chosenIds.length}/5 selezionati · min Lv {minLevel}
                </p>
                <div className="flex gap-2">
                    <Button
                        variant="ghost" size="sm"
                        data-testid="defense-reset-btn"
                        onClick={() => setChosenIds([])}
                    >
                        Reset
                    </Button>
                    <Button
                        size="sm"
                        data-testid="defense-save-btn"
                        disabled={!isComplete || saving}
                        onClick={() => onSave?.(chosenIds)}
                    >
                        {saving ? "Salvataggio…" : "Salva difesa"}
                    </Button>
                </div>
            </div>
        </div>
    );
}
