// FASE 9 — Sezioni Guida riscritte sul nuovo modello CLASSE → RUOLO
// FISSO. Le vecchie sezioni 32-34 (classe base vs specializzazione,
// sblocco spec) sono state sostituite: le specializzazioni e le build
// NON esistono più. Restano (aggiornate): Sale di Classe, Razza e
// Sesso, Colori statistiche, Auto-Equip, Minacce e Contromisure.

import { SectionBlock } from "./_shared";

const ListItem = ({ children }) => (
    <li className="ml-5 list-disc text-foreground/90">{children}</li>
);

// 32. Classe e ruolo fisso
function ClassRoleSection() {
    return (
        <SectionBlock id="classe-ruolo-fisso" title="32. Classe e ruolo fisso">
            <p className="mb-3">
                Dalla <strong>Fase 9</strong> ogni avventuriero appartiene a una
                delle <strong>27 classi canoniche</strong> e il suo{" "}
                <strong>ruolo è fisso</strong>: deriva SEMPRE dalla classe.
            </p>
            <ul className="space-y-1 mb-3">
                <ListItem><strong>13 classi da Danno (DPS)</strong> — es. Guerriero, Ladro, Mago, Runista, Pittore.</ListItem>
                <ListItem><strong>6 classi Difensore (Tank)</strong> — Paladino, Cacciatore di Mostri, Fabbro Arcano, Parassita, Cavaliere della Morte, Cavaliere di Draghi.</ListItem>
                <ListItem><strong>8 classi Guaritore (Healer)</strong> — Alchimista, Bardo, Druido, Sciamano, Cronista, Mercante, Astrologo, Sognatore.</ListItem>
            </ul>
            <p className="text-[11px] text-muted-foreground italic">
                Non esistono più specializzazioni selezionabili né build da
                attivare con gli oggetti: il Paladino è SEMPRE un Difensore,
                il Bardo è SEMPRE un Guaritore, il Guerriero è SEMPRE Danno.
                Se vuoi un ruolo diverso, scegli una classe diversa nella
                Sala di Classe.
            </p>
        </SectionBlock>
    );
}

// 33. Sale di Classe
function ClassHallsSection() {
    return (
        <SectionBlock id="sale-di-classe" title="33. Sale di Classe (Class Halls)">
            <p className="mb-3">
                Ogni gilda dispone di <strong>27 Sale di Classe</strong>, una per
                classe canonica. Nella pagina <code>/class-halls</code> ogni Sala
                mostra:
            </p>
            <ul className="space-y-1 mb-3">
                <ListItem>L&apos;<strong>emblema</strong> e l&apos;identità della classe, col <strong>ruolo fisso</strong> ben visibile.</ListItem>
                <ListItem>Lo <strong>stile di combattimento</strong> e i punti di forza.</ListItem>
                <ListItem>L&apos;<strong>equipaggiamento di classe</strong> (i tag arma/armatura che attivano la risonanza).</ListItem>
                <ListItem>La <strong>prova</strong> per ottenere la classe e il sentiero degli item della Sala.</ListItem>
                <ListItem>I <strong>4 set raid di classe</strong>, in ordine di progressione.</ListItem>
            </ul>
            <p className="text-[12px] text-muted-foreground">
                Una recluta nasce <strong>senza classe</strong>: supera la prova
                della Sala scelta e giura davanti al Maestro. La scelta assegna la
                classe (e quindi il ruolo), non una build.
            </p>
        </SectionBlock>
    );
}

// 34. Risonanza di classe
function ResonanceSection() {
    return (
        <SectionBlock id="risonanza-di-classe" title="34. Risonanza di classe">
            <p className="mb-3">
                Ogni classe ha una <strong>meccanica fissa</strong> (es. la{" "}
                <em>Tempra della Linea</em> del Guerriero) che concede un piccolo
                bonus di potere costante e un bonus di <strong>risonanza</strong>{" "}
                quando l&apos;avventuriero veste equipaggiamento della{" "}
                <strong>propria classe</strong>.
            </p>
            <ul className="space-y-1 mb-3">
                <ListItem><strong>+1</strong> potere per il solo fatto di avere una classe.</ListItem>
                <ListItem><strong>+2</strong> potere quando almeno un pezzo equipaggiato porta un tag canonico della classe (arma o armatura del suo arsenale).</ListItem>
                <ListItem>Con la risonanza attiva si attivano anche i <strong>counter tag</strong> della classe contro le minacce dei dungeon.</ListItem>
            </ul>
            <p className="text-[11px] text-muted-foreground italic">
                In breve: vesti la tua classe e la classe risponde. Nessuna build
                da indovinare.
            </p>
        </SectionBlock>
    );
}

// 35. Razza e Sesso
function RacesGenderSection() {
    return (
        <SectionBlock id="razze-sesso" title="35. Razza e Sesso">
            <p className="mb-3">
                Ogni nuovo avventuriero riceve una
                <strong> razza</strong> (50 disponibili) e un <strong>sesso</strong>
                (maschile / femminile, 50/50). Sono campi puramente <em>narrativi</em>:
                non influenzano statistiche, danno o equipaggiamento.
            </p>
            <ul className="space-y-1 mb-3">
                <ListItem><strong>Razza</strong> (es. Umano del Nord, Elfo silvano, Nano delle profondità, Orchetto delle steppe, …). Distribuzione bilanciata per rarità.</ListItem>
                <ListItem><strong>Sesso</strong>: solo flavor, mostrato nel profilo dell&apos;avventuriero.</ListItem>
            </ul>
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
                Usa i colori per scremare il roster a colpo d&apos;occhio: un Ladro con
                Destrezza <em>cyan</em> è in linea con la sua classe; un Guerriero
                con Forza <em>rossa</em> non è ottimale.
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
                <ListItem>Filtra gli item per <strong>compatibilità di classe</strong> (la classe È il criterio: niente build, niente spec).</ListItem>
                <ListItem>Esclude item con <em>hard block</em> (es. armatura pesante su Mago).</ListItem>
                <ListItem>Ordina per <strong>punteggio</strong> aggregato delle statistiche utili al ruolo della classe.</ListItem>
                <ListItem>Equipaggia uno per <strong>slot</strong> (testa, corpo, mani, armi, accessori).</ListItem>
                <ListItem>Lascia liberi gli slot per cui non c&apos;è equip valido nel deposito.</ListItem>
            </ul>
            <p className="text-[11px] text-muted-foreground italic">
                L&apos;operazione è <strong>idempotente</strong>: rieseguirla con lo stesso
                inventario non cambia il risultato. È tracciata in audit con l&apos;event
                type <code>adventurer_auto_equipped</code>.
            </p>
        </SectionBlock>
    );
}

// 39. Minacce e Contromisure
function ThreatsCountersSection() {
    return (
        <SectionBlock id="minacce-contromisure" title="39. Minacce e Contromisure (Vuoto / Non-morti)">
            <p className="mb-3">
                I dungeon del <strong>Vuoto</strong> e della <strong>Non-morte</strong> portano <em>minacce</em> specifiche
                (es. <em>Corruzione del Vuoto</em>, <em>Maledizione</em>, <em>Non-morti</em>, <em>Barriera Magica</em>).
                Gli avventurieri possono <em>contrastarle</em> grazie ai <strong>counter tag della loro classe</strong>{" "}
                (attivi con la risonanza di classe) o ai loro <strong>tratti</strong>.
            </p>

            <div className="text-[11px] text-amber tracking-widest mt-4 mb-2">
                :: COME FUNZIONA
            </div>
            <ul className="space-y-1 mb-4">
                <ListItem>Ogni dungeon Vuoto/Non-morti ha da 2 a 4 <strong>minacce</strong> assegnate.</ListItem>
                <ListItem>Ogni classe porta due <strong>counter tag</strong> fissi (es. il Negromante <code>counter_undead</code> + <code>counter_void</code>); alcuni tratti ne aggiungono altri.</ListItem>
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
                    Una squadra con <strong>Negromante</strong> (counter_undead + counter_void),{" "}
                    <strong>Paladino</strong> (counter_undead + counter_curse) e{" "}
                    <strong>Mago</strong> (counter_spell + counter_magic_barrier) in risonanza
                    contrasta le minacce → bonus successo e riduzione ferite.
                </ListItem>
                <ListItem>
                    Una squadra senza counter tag rilevanti → ratio 0% → nessun bonus, nessuna riduzione.
                </ListItem>
            </ul>

            <p className="text-[11px] text-muted-foreground italic">
                Attivo solo sui dungeon del Vuoto e della Non-morte. Gli altri
                dungeon mantengono il comportamento standard.
            </p>
        </SectionBlock>
    );
}

export default function R16GuideSections() {
    return (
        <>
            <ClassRoleSection />
            <ClassHallsSection />
            <ResonanceSection />
            <RacesGenderSection />
            <StatColorsSection />
            <AutoEquipSection />
            <ThreatsCountersSection />
        </>
    );
}
