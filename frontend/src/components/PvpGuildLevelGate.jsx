// ROUND 16.3 Phase 7A Iter2 — Level gate for PvP pages.
export default function PvpGuildLevelGate({ currentLevel }) {
    return (
        <div className="max-w-2xl mx-auto px-4 py-10" data-testid="pvp-level-gate">
            <div className="rounded-md border border-red-900/40 bg-red-950/10 p-6 text-center space-y-3">
                <div className="text-3xl">🔒</div>
                <h1 className="text-xl md:text-2xl font-semibold">
                    PvP Continentale bloccato
                </h1>
                <p className="text-sm text-zinc-400">
                    Il PvP si sblocca quando la tua gilda raggiunge il <b>livello 8</b>.
                </p>
                {currentLevel != null && (
                    <p className="text-xs text-zinc-500">
                        Livello attuale: <span className="font-mono">{currentLevel}</span> / 8
                    </p>
                )}
                <div className="border-t border-red-900/30 pt-3 text-xs text-zinc-500 text-left space-y-1">
                    <div className="text-zinc-300 mb-1">Come sbloccarlo:</div>
                    <div>• Completa spedizioni e raid per far salire di livello la gilda</div>
                    <div>• Firma incarichi di sede per XP passivo</div>
                    <div>• Sviluppa le Sale di Classe per rendere gli avventurieri più efficaci</div>
                </div>
            </div>
        </div>
    );
}
