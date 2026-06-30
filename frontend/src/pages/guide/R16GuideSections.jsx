// ROUND 16.0 — Phase 6 — Player-facing Guida sections covering R16.0 Phase 2-4.
// Topics: Base class vs Specialization, Class Halls, Unlock Flow,
//         Races & Gender, Stat Colors, Auto-Equip, Threats & Counters.
// All copy is Italian and references R16.0 changes.

import { SectionBlock } from "./_shared";

const ListItem = ({ children }) => (
    <li className="ml-5 list-disc text-foreground/90">{children}</li>
);

// 32. Classe base vs Specializzazione
function BaseVsSpecSection() {
    return (
        <SectionBlock id="classe-vs-spec" title="32. Classe base vs Specializzazione">
            <p className="mb-3">
                Dal <strong>Round 16.0</strong> ogni avventuriero appartiene a una <strong>classe base</strong>
                (Guerriero, Paladino, Ladro, Ranger, Monaco, Mago, Sacerdote, Druido,
                Bardo, <strong>Stregone</strong>) e può successivamente sbloccare una
                <strong> specializzazione</strong> tramite la <em>Sala di Classe</em> dedicata.
            </p>
            <ul className="space-y-1 mb-3">
                <ListItem><strong>Classe base</strong>: identità e statistiche primarie. Si assegna alla generazione dell'avventuriero.</ListItem>
                <ListItem><strong>Specializzazione</strong>: ramo avanzato (3 per classe base) che aggiunge counter tag, sinergie e item esclusivi.</ListItem>
            </ul>
            <p className="text-[11px] text-muted-foreground italic">
                Esempio: un Ladro può specializzarsi in <em>Assassino</em> (burst stealth)
                o <em>Duellante</em> (DPS frontale); un Mago può diventare <em>Negromante</em>
                (servitori) o <em>Elementalista</em> (AoE arcano); un Guerriero può
                diventare <em>Berserker</em> (frontline a 2 mani).
            </p>
        </SectionBlock>
    );
}

// 33. Sale di Classe (Class Halls)
function ClassHallsSection() {
    return (
        <SectionBlock id="sale-di-classe" title="33. Sale di Classe (Class Halls)">
            <p className="mb-3">
                Ogni gilda dispone di <strong>10 Sale di Classe</strong> (una per ciascuna classe base).
                Ogni Sala è un edificio testuale che racchiude:
            </p>
            <ul className="space-y-1 mb-3">
                <ListItem>Il <strong>livello</strong> della sala (sblocco progressivo via XP gilda e oro).</ListItem>
                <ListItem>Le <strong>3 specializzazioni</strong> sbloccabili per quella classe base.</ListItem>
                <ListItem>Gli <strong>avventurieri assegnati</strong> alla sala in addestramento.</ListItem>
            </ul>
            <p className="text-[12px] text-muted-foreground">
                Le Sale sono accessibili dalla pagina <code>/training</code> ed espongono i requisiti
                di sblocco per ogni ramo.
            </p>
        </SectionBlock>
    );
}

// 34. Sbloccare una Sala e una Specializzazione
function UnlockFlowSection() {
    return (
        <SectionBlock id="sblocco-sala-spec" title="34. Sbloccare una Sala e una Specializzazione">
            <p className="mb-3">
                Per portare un avventuriero a una specializzazione devi seguire 3 passi:
            </p>
            <ol className="space-y-2 mb-3 list-decimal ml-5">
                <li>
                    <strong>Sblocca la Sala di Classe</strong> della classe base
                    (richiede oro e XP gilda). La Sala diventa di livello 1.
                </li>
                <li>
                    <strong>Sblocca la specializzazione</strong> all'interno della Sala
                    (richiede materiali specifici e oro aggiuntivo). Endpoint:
                    <code className="ml-1">POST /api/class-halls/&lt;slug&gt;/unlock-specialization</code>.
                </li>
                <li>
                    <strong>Promuovi un avventuriero</strong> dalla classe base a quella
                    specializzazione tramite la pagina Addestramento.
                </li>
            </ol>
            <p className="text-[11px] text-muted-foreground italic">
                Nota R16.0: prima del rework, <em>Assassino</em>, <em>Berserker</em> e
                <em> Negromante</em> erano classi base reclutabili direttamente. Dal Round 16.0
                sono specializzazioni delle rispettive Sale (Ladro, Guerriero, Mago).
                Gli avventurieri esistenti sono stati migrati automaticamente alla
                rispettiva specializzazione mantenendo statistiche e livello.
            </p>
        </SectionBlock>
    );
}

// 35. Razza e Sesso
function RacesGenderSection() {
    return (
        <SectionBlock id="razze-sesso" title="35. Razza e Sesso">
            <p className="mb-3">
                Ogni nuovo avventuriero generato dal Round 16.0 riceve una
                <strong> razza</strong> (50 disponibili) e un <strong>sesso</strong>
                (maschile / femminile, 50/50). Sono campi puramente <em>narrativi</em>:
                non influenzano statistiche, danno o equipaggiamento.
            </p>
            <ul className="space-y-1 mb-3">
                <ListItem><strong>Razza</strong> (es. Umano del Nord, Elfo silvano, Nano delle profondità, Orchetto delle steppe, …). Distribuzione bilanciata per rarità.</ListItem>
                <ListItem><strong>Sesso</strong>: solo flavor, mostrato nel profilo dell'avventuriero.</ListItem>
            </ul>
            <p className="text-[11px] text-muted-foreground italic">
                Gli avventurieri pre-R16.0 sono stati <strong>retroattivamente</strong>
                arricchiti con razza e sesso (oltre 92.000 record aggiornati in modo
                atomico e idempotente).
            </p>
        </SectionBlock>
    );
}

// 36. Colori delle statistiche
function StatColorsSection() {
    return (
        <SectionBlock id="stat-colors" title="36. Colori delle statistiche">
            <p className="mb-3">
                I valori delle statistiche nel roster e nelle pagine di dettaglio sono
                colorati per qualità relativa al massimo previsto per il livello:
            </p>
            <ul className="space-y-1 mb-3 text-[12px]">
                <li className="flex items-center gap-2">
                    <span className="inline-block w-3 h-3 rounded-sm bg-red-400/80" />
                    <strong className="text-red-400/90">Scarsa</strong> — &lt; 40% del massimo previsto
                </li>
                <li className="flex items-center gap-2">
                    <span className="inline-block w-3 h-3 rounded-sm bg-yellow-400/80" />
                    <strong className="text-yellow-400/90">Media</strong> — 40-70%
                </li>
                <li className="flex items-center gap-2">
                    <span className="inline-block w-3 h-3 rounded-sm bg-green-400/80" />
                    <strong className="text-green-400/90">Buona</strong> — 70-90%
                </li>
                <li className="flex items-center gap-2">
                    <span className="inline-block w-3 h-3 rounded-sm bg-cyan-400/80" />
                    <strong className="text-cyan-400/90">Eccellente</strong> — ≥ 90%
                </li>
            </ul>
            <p className="text-[11px] text-muted-foreground italic">
                Usa i colori per scremare il roster a colpo d'occhio: un Ladro con
                Destrezza <em>cyan</em> e Forza <em>rossa</em> è una build coerente;
                un Guerriero con Forza <em>rossa</em> non è ottimale.
            </p>
        </SectionBlock>
    );
}

// 37. Auto-Equipaggia
function AutoEquipSection() {
    return (
        <SectionBlock id="auto-equip" title="37. Auto-Equipaggia">
            <p className="mb-3">
                Il bottone <strong>Auto-Equipaggia</strong> (nella scheda dettaglio di
                ogni avventuriero) seleziona automaticamente il miglior set di
                equipaggiamento <em>compatibile</em> presente nel Deposito della gilda.
            </p>
            <div className="text-[11px] text-amber tracking-widest mt-4 mb-2">
                :: COME SCEGLIE
            </div>
            <ul className="space-y-1 mb-3">
                <ListItem>Filtra gli item per <strong>compatibilità di classe</strong> base e specializzazione.</ListItem>
                <ListItem>Esclude item con <em>hard block</em> (es. armatura pesante su Mago).</ListItem>
                <ListItem>Ordina per <strong>punteggio</strong> aggregato delle statistiche utili alla classe.</ListItem>
                <ListItem>Equipaggia uno per <strong>slot</strong> (testa, corpo, mani, armi, accessori).</ListItem>
                <ListItem>Lascia liberi gli slot per cui non c'è equip valido nel deposito.</ListItem>
            </ul>
            <p className="text-[11px] text-muted-foreground italic">
                L'operazione è <strong>idempotente</strong>: rieseguirla con lo stesso
                inventario non cambia il risultato. È tracciata in audit con l'event
                type <code>adventurer_auto_equipped</code>.
            </p>
        </SectionBlock>
    );
}

// 39. Minacce e Contromisure (already exists from Phase 4)
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
            <BaseVsSpecSection />
            <ClassHallsSection />
            <UnlockFlowSection />
            <RacesGenderSection />
            <StatColorsSection />
            <AutoEquipSection />
            <ThreatsCountersSection />
        </>
    );
}
