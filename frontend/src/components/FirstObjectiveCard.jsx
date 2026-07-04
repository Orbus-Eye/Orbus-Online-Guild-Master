import { Link } from "react-router-dom";

/**
 * ROUND 17 STEP 0 — First Objective Card.
 *
 * Nudge Dashboard visualizzato SOLO se il player non ha ancora completato
 * nessuna spedizione (`total_expeditions_completed === 0`).
 *
 * Regole (da PM msg R17 Step 0 B/D):
 * - Nasconde automaticamente dopo la prima spedizione completata.
 * - Nessun XP gratis, nessun backfill artificiale: solo un "primo obiettivo"
 *   visibile che porta al flow corretto.
 * - CTA branch:
 *     - `advCount < 3` → "Recluta il primo team" → `/recruitment`
 *     - `advCount >= 3` → "Prepara la prima spedizione" → `/expeditions?starter=sewer-nest`
 *
 * Testo italiano. Responsive mobile (viewport 375/390 testati).
 */
export default function FirstObjectiveCard({ guild, advCount }) {
    if (!guild) return null;
    if ((guild.total_expeditions_completed ?? 0) > 0) return null;

    const needsRecruit = (advCount ?? 0) < 3;
    const ctaTo = needsRecruit
        ? "/recruitment"
        : "/dungeons?starter=training-yard";
    const ctaLabel = needsRecruit
        ? "Recluta il primo team"
        : "Prepara la prima spedizione";
    const ctaTestid = needsRecruit
        ? "first-objective-cta-recruit"
        : "first-objective-cta-expedition";

    return (
        <div
            data-testid="first-objective-card"
            className="border border-amber/60 bg-amber/5 rounded-sm p-4 mb-6"
        >
            <div className="flex items-start justify-between gap-3 flex-wrap">
                <div className="min-w-0 flex-1">
                    <div
                        className="text-[10px] text-amber tracking-widest mb-1"
                        data-testid="first-objective-badge"
                    >
                        📍 PRIMO OBIETTIVO
                    </div>
                    <h2
                        className="text-lg font-light text-foreground mb-2 leading-tight"
                        data-testid="first-objective-title"
                    >
                        Inizia la tua prima spedizione
                    </h2>
                    <p
                        className="text-sm text-foreground/85 leading-relaxed mb-3"
                        data-testid="first-objective-description"
                    >
                        {needsRecruit ? (
                            <>
                                Prima di partire ti serve una squadra.
                                Recluta almeno 3 avventurieri per iniziare.
                            </>
                        ) : (
                            <>
                                Scegli 3 avventurieri e completa il primo
                                dungeon per ottenere Prestigio e i primi
                                equipaggiamenti.
                            </>
                        )}
                    </p>
                    <p
                        className="text-[11px] text-muted-foreground mb-3"
                        data-testid="first-objective-reward-hint"
                    >
                        Ricompensa: Prestigio di Gilda + oro + equip iniziale.
                    </p>
                </div>
            </div>
            <Link
                to={ctaTo}
                data-testid={ctaTestid}
                className="inline-flex items-center text-xs tracking-widest font-bold border border-amber text-amber bg-amber/10 px-4 py-2 rounded-sm hover:bg-amber/20 transition-colors"
            >
                {ctaLabel} →
            </Link>
        </div>
    );
}
