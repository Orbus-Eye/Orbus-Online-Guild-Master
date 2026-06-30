// ROUND 16.0 — Phase 4 — Player-facing Guida section for Threats & Counters.
// Active only on Void/Undead dungeons. No loot bonus, only success +12% / -8% injuries (cap).

import { SectionBlock } from "./_shared";

const ListItem = ({ children }) => (
    <li className="ml-5 list-disc text-foreground/90">{children}</li>
);

function ThreatsCountersSection() {
    return (
        <SectionBlock id="minacce-contromisure" title="39. Minacce e Contromisure (Vuoto / Non-morti)">
            <p className="mb-3">
                I dungeon del <strong>Vuoto</strong> e della <strong>Non-morte</strong> portano <em>minacce</em> specifiche
                (es. <em>Corruzione del Vuoto</em>, <em>Maledizione</em>, <em>Non-morti</em>, <em>Barriera Magica</em>).
                Gli avventurieri possono <em>contrastarle</em> grazie alla loro <strong>specializzazione</strong> o ai loro <strong>tratti</strong>.
            </p>

            <div className="text-[11px] text-amber tracking-widest mt-4 mb-2">
                :: COME FUNZIONA
            </div>
            <ul className="space-y-1 mb-4">
                <ListItem>Ogni dungeon Vuoto/Non-morti ha da 2 a 4 <strong>minacce</strong> assegnate.</ListItem>
                <ListItem>Ogni specializzazione/tratto rilevante porta uno o più <strong>counter tag</strong> (es. <code>counter_undead</code>, <code>counter_void</code>, <code>counter_curse</code>).</ListItem>
                <ListItem>A inizio spedizione si calcola il <strong>ratio</strong> (minacce contrastate / minacce totali).</ListItem>
                <ListItem>Il ratio fornisce un bonus al success_chance fino a <strong>+12%</strong> e una riduzione delle ferite gravi fino a <strong>-8%</strong> (cap).</ListItem>
                <ListItem><strong>NESSUN bonus al bottino.</strong> Le drop table non vengono toccate.</ListItem>
            </ul>

            <div className="text-[11px] text-amber tracking-widest mt-4 mb-2">
                :: ESEMPIO PRATICO
            </div>
            <ul className="space-y-1 mb-4">
                <ListItem>
                    Dungeon <em>Lich Sanctum</em> con minacce <code>[non-morti, maledizione, boss, barriera magica]</code>.
                </ListItem>
                <ListItem>
                    Una squadra con <strong>Esorcista</strong> (counter_undead + counter_curse) e <strong>Cavaliere Runico</strong> (counter_spell + counter_magic_barrier) contrasta 4/4 minacce → ratio 100% → <strong>+12% successo, -8% ferite</strong>.
                </ListItem>
                <ListItem>
                    Una squadra senza counter tag rilevanti → ratio 0% → nessun bonus, nessuna riduzione.
                </ListItem>
            </ul>

            <div className="text-[11px] text-amber tracking-widest mt-4 mb-2">
                :: NUOVI TRATTI DI MISSIONE (R16.0)
            </div>
            <p className="mb-2 text-[12px]">
                Dieci nuovi tratti narrativi disponibili nel pool:
            </p>
            <ul className="space-y-1 mb-4 text-[12px]">
                <ListItem><strong>Specialista Missioni Lunghe</strong>, <strong>Pianificatore Veloce</strong>, <strong>Intraprendente</strong>, <strong>Prudente</strong>.</ListItem>
                <ListItem><strong>Stratega Anti-Boss</strong> (counter_boss), <strong>Sesto Senso per le Trappole</strong> (counter_trap), <strong>Disgregatore Arcano</strong> (counter_spell + counter_magic_barrier).</ListItem>
                <ListItem><strong>Cacciatore di Non-morti</strong> (counter_undead), <strong>Tracciatore di Bestie</strong> (counter_beast), <strong>Resistente al Vuoto</strong> (counter_void).</ListItem>
            </ul>

            <p className="text-[11px] text-muted-foreground italic">
                Attivo solo sui dungeon del Vuoto e della Non-morte. Gli altri dungeon mantengono il comportamento Round 15 invariato.
            </p>
        </SectionBlock>
    );
}

export default function R16GuideSections() {
    return (
        <>
            <ThreatsCountersSection />
        </>
    );
}
