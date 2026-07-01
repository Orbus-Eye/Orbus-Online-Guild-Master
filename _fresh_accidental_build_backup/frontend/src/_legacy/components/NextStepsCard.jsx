// ROUND 14.v3 — Dashboard "Prossimi passi" card.
//
// Best-effort suggestion engine. Fetches inventory, raids and pvp matches in
// parallel (each wrapped in try/catch). Builds the priority-ordered list of
// candidate steps and renders the first 3 that apply. Always shows at least
// the "Market" evergreen fallback so the card is never empty.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../lib/api";
import { useAuth } from "../context/AuthContext";

// Priority order — first 3 applicable wins.
function buildSteps({ guild, advCount, inventoryCount, anyEquipped, arenaPlayed, raidsCompleted }) {
    const steps = [];
    if (advCount < 3) {
        steps.push({
            id: "recruit",
            icon: "⚔",
            label: "Recluta avventurieri",
            hint: `Roster ${advCount}/3 minimo. Aggiungi 3 candidati per partire.`,
            to: "/recruitment",
        });
    }
    if ((guild?.total_expeditions_completed ?? 0) === 0) {
        steps.push({
            id: "first-expedition",
            icon: "🎯",
            label: "Avvia la tua prima spedizione",
            hint: "Sceglie un dungeon Lv1 dalla board.",
            to: "/dungeons",
        });
    }
    if (inventoryCount === 0 || !anyEquipped) {
        steps.push({
            id: "equip-team",
            icon: "🛡",
            label: "Equipaggia il tuo team",
            hint: inventoryCount === 0
                ? "Inventario vuoto. Completa una spedizione per ottenere loot."
                : "Hai oggetti non equipaggiati. Apri il roster.",
            to: inventoryCount === 0 ? "/dungeons" : "/adventurers",
        });
    }
    if (!arenaPlayed) {
        steps.push({
            id: "arena",
            icon: "⚔",
            label: "Sfida l'Arena",
            hint: "PvP asincrono. Nessuna perdita di oro o avventurieri.",
            to: "/arena",
        });
    }
    if (raidsCompleted === 0) {
        steps.push({
            id: "first-raid",
            icon: "🐉",
            label: "Affronta il primo Raid",
            hint: "Servono 12+ avventurieri organizzati in 4 party.",
            to: "/raids",
        });
    }
    // Training-in-progress can't be derived from existing endpoints cheaply;
    // we surface Training as a generic next-action when nothing else applies.
    steps.push({
        id: "training",
        icon: "📚",
        label: "Allena un avventuriero",
        hint: "Specializza un eroe nei Training Grounds.",
        to: "/training",
    });
    steps.push({
        id: "market",
        icon: "🛒",
        label: "Esplora il Mercato",
        hint: "Materiali e consumabili dal banco NPC.",
        to: "/market",
    });
    return steps;
}

export default function NextStepsCard() {
    const { guild } = useAuth();
    const [state, setState] = useState({
        loading: true,
        inventoryCount: null,
        anyEquipped: null,
        arenaPlayed: null,
        raidsCompleted: null,
    });

    useEffect(() => {
        let cancelled = false;
        async function run() {
            const next = {
                inventoryCount: 0,
                anyEquipped: false,
                arenaPlayed: false,
                raidsCompleted: 0,
            };
            await Promise.all([
                api.get("/inventory").then((r) => {
                    const items = r.data?.inventory || [];
                    next.inventoryCount = items.length;
                    next.anyEquipped = items.some((it) => (it.equipped_quantity || 0) > 0);
                }).catch(() => {}),
                api.get("/raids").then((r) => {
                    const raids = r.data?.raids || [];
                    next.raidsCompleted = raids.filter(
                        (x) => x.outcome === "victory" || x.outcome === "partial",
                    ).length;
                }).catch(() => {}),
                api.get("/pvp/matches").then((r) => {
                    next.arenaPlayed = (r.data?.total || (r.data?.matches || []).length) > 0;
                }).catch(() => {}),
            ]);
            if (!cancelled) setState({ ...next, loading: false });
        }
        run();
        return () => { cancelled = true; };
    }, []);

    if (!guild) return null;

    const advCount = guild.adventurer_count ?? 0;
    const steps = buildSteps({
        guild,
        advCount,
        inventoryCount: state.inventoryCount ?? 0,
        anyEquipped: state.anyEquipped ?? false,
        arenaPlayed: state.arenaPlayed ?? false,
        raidsCompleted: state.raidsCompleted ?? 0,
    });
    const visible = steps.slice(0, 3);

    return (
        <section
            data-testid="next-steps-card"
            className="border border-amber/30 bg-card rounded-sm p-4 mb-6"
        >
            <div className="flex items-center justify-between mb-3">
                <div>
                    <div className="text-[10px] text-amber tracking-widest mb-0.5">
                        :: PROSSIMI PASSI
                    </div>
                    <p className="text-[11px] text-muted-foreground">
                        Suggerimenti dinamici basati sullo stato attuale della gilda.
                    </p>
                </div>
                {state.loading && (
                    <span
                        className="text-[10px] text-muted-foreground italic"
                        data-testid="next-steps-loading"
                    >
                        caricamento…
                    </span>
                )}
            </div>
            <ul className="space-y-2" data-testid="next-steps-list">
                {visible.map((s, idx) => (
                    <li key={s.id}>
                        <Link
                            to={s.to}
                            data-testid={`next-step-${s.id}`}
                            className="flex items-start gap-3 border border-border bg-background/30 rounded-sm p-3 hover:border-amber/55 hover:bg-secondary/30 transition-colors group"
                        >
                            <span
                                aria-hidden="true"
                                className="text-base shrink-0 mt-0.5"
                            >
                                {s.icon}
                            </span>
                            <span className="min-w-0 flex-1">
                                <span className="block text-sm text-foreground">
                                    <span className="text-[10px] text-muted-foreground tracking-widest mr-2">
                                        {idx + 1}.
                                    </span>
                                    {s.label}
                                </span>
                                <span className="block text-[11px] text-muted-foreground mt-0.5">
                                    {s.hint}
                                </span>
                            </span>
                            <span className="text-amber text-xs group-hover:translate-x-0.5 transition-transform shrink-0">
                                →
                            </span>
                        </Link>
                    </li>
                ))}
            </ul>
        </section>
    );
}
