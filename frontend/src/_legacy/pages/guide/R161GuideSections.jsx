// ROUND 16.1 Phase 3 — Player-facing reference for the Game Clarity Pass.
// Adds 3 sections: Daily Loop, Team Composition for Dungeons, Roster
// Filters/Sort. All copy is provided in IT (primary) with EN annotations.

import { SectionBlock } from "./_shared";

export const R161_SECTIONS = [
    { id: "daily-loop",      label: "R16.1. Cosa fare ogni giorno" },
    { id: "team-composition", label: "R16.1. Come scegliere un team dungeon" },
    { id: "roster-filters",  label: "R16.1. Filtri e ordinamento del roster" },
];

export default function R161GuideSections() {
    return (
        <>
            <SectionBlock id="daily-loop" title="COSA FARE OGNI GIORNO · Daily loop">
                <p>
                    Il <strong>Daily Loop</strong> è la sequenza minima di azioni che ti
                    porta avanti senza farti perdere tempo. Vivi la tua sessione così:
                </p>
                <ol className="list-decimal list-inside space-y-1">
                    <li>
                        <strong>Apri la Dashboard</strong> — leggi la card &quot;Prossime azioni&quot;
                        per sapere subito cosa fare ora. <em>Open the dashboard and read the
                        Next Actions card.</em>
                    </li>
                    <li>
                        <strong>Reclama i daily</strong> — la card &quot;Daily Loop&quot; mostra i
                        progressi: ferma il primo dungeon, controlla il mercato, prepara una
                        spedizione. <em>Claim dailies as you go.</em>
                    </li>
                    <li>
                        <strong>Spendi le tue 1–2 spedizioni</strong> con team adatti al
                        dungeon (vedi sezione team composition).
                    </li>
                    <li>
                        <strong>Auto-Equipaggia chi torna</strong> dal dungeon: 1 click per
                        massimizzare il loro power score.
                    </li>
                    <li>
                        <strong>Sblocca specializzazioni</strong> nelle Sale di Classe se hai
                        avventurieri senza spec — boost permanente di stats.
                    </li>
                </ol>
                <p className="text-[11px] text-muted-foreground italic mt-2">
                    EN: Open the dashboard → claim dailies → spend 1–2 expeditions →
                    auto-equip survivors → unlock at least one specialization.
                </p>
            </SectionBlock>

            <SectionBlock
                id="team-composition"
                title="COME SCEGLIERE UN TEAM DUNGEON · Building a dungeon team"
            >
                <p>
                    Quando lanci una spedizione, l&apos;<strong>Anteprima narrata</strong>
                    (bottone <code>✦ Anteprima narrata</code>) ti dice prima del click cosa
                    succederà. Tre cose contano davvero:
                </p>
                <ul className="list-disc list-inside space-y-1">
                    <li>
                        <strong>Potere del team ≥ potere consigliato</strong>. Sotto il
                        consigliato la probabilità di successo cala rapidamente. <em>EN:
                        keep team power ≥ recommended power.</em>
                    </li>
                    <li>
                        <strong>Composizione ruoli</strong>: Tank tiene aggro, Healer
                        ripristina HP, DPS chiude i fight. Mancando uno qualsiasi il rischio
                        ferita sale. <em>EN: Tank + Healer + DPS is the safe core.</em>
                    </li>
                    <li>
                        <strong>Minacce e contromisure</strong>: dungeon Vuoto/Non-morti hanno
                        threat tag (es. <code>void</code>, <code>undead</code>). Una
                        specializzazione che le contrasta dà fino a <strong>+10% successo</strong>
                        e <strong>-15% rischio ferita</strong>. La preview elenca ogni
                        minaccia con ✓ se contrastata o ⚠ se scoperta. <em>EN: void/undead
                        dungeons reward bringing the right counter-spec.</em>
                    </li>
                </ul>
                <p className="text-[11px] text-muted-foreground italic mt-2">
                    Suggerimento: se la preview mostra ⚠ multiple, valuta di cambiare un
                    membro con uno specializzato sulla minaccia, oppure rimanda la
                    spedizione.
                </p>
            </SectionBlock>

            <SectionBlock
                id="roster-filters"
                title="FILTRI E ORDINAMENTO DEL ROSTER · Roster filters &amp; sort"
            >
                <p>
                    La pagina <code>Avventurieri</code> espone una barra di filtri/sort:
                </p>
                <ul className="list-disc list-inside space-y-1">
                    <li>
                        <strong>Classe / Ruolo</strong>: isola in 1 click tutti i mage o
                        tutti i tank. <em>EN: filter by class or role.</em>
                    </li>
                    <li>
                        <strong>Equip migliorabile</strong>: mostra solo gli avventurieri
                        con &lt;4 slot equipaggiati — candidati naturali per Auto-Equip.
                    </li>
                    <li>
                        <strong>Senza specializzazione</strong>: trova chi puoi
                        specializzare subito per un boost.
                    </li>
                    <li>
                        <strong>Pronto per dungeon</strong>: nasconde feriti, in spedizione,
                        in addestramento.
                    </li>
                    <li>
                        <strong>Sort</strong>: per livello, power score, stat primaria,
                        qualità equip, classe o nome (asc/desc).
                    </li>
                </ul>
                <p className="text-[11px] text-muted-foreground italic mt-2">
                    I filtri vengono mantenuti nella sessione del browser ma si resettano
                    al logout. <em>EN: filter state persists per browser session only.</em>
                </p>
            </SectionBlock>
        </>
    );
}
