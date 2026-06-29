// Phase 19.2 — P2.2 Player Guide in-game.
// TASK 6 G4 — Traits + Stats sezioni data-driven (lazy fetch).
// ROUND 11.4c — Refactored: shared primitives moved to `./guide/_shared.jsx`
// and the two data-driven catalog sections to `./guide/CatalogSections.jsx`.
// Guide.jsx now orchestrates the sticky nav + static section blocks.
// Single-page guide with anchor-link tabs. Italian-first.
// Pure text + tables; no images. Dark/minimal aesthetic to match the rest of the UI.
import { useState } from "react";
import AppHeader from "../components/AppHeader";
import RoleMarker from "../components/RoleMarker";
import { SECTIONS, SectionBlock } from "./guide/_shared";
import { StatsCatalogSection, TraitsCatalogSection } from "./guide/CatalogSections";

export default function Guide() {
    const [active, setActive] = useState("intro");

    const goTo = (id) => {
        setActive(id);
        const el = document.getElementById(id);
        if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    };

    return (
        <div className="min-h-screen bg-background text-foreground">
            <AppHeader subtitle="GUIDE" />
            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-6" data-testid="guide-page">
                <header className="mb-6">
                    <div className="text-[10px] text-amber tracking-widest mb-2">:: MANUALE DEL GUILD MASTER</div>
                    <h1 className="text-3xl font-semibold tracking-tight">Guida del Giocatore</h1>
                    <p className="text-sm text-muted-foreground mt-2 max-w-2xl">
                        Tutto quello che ti serve sapere per gestire la tua gilda, reclutare avventurieri,
                        affrontare dungeon e raid, e dominare la classifica.
                    </p>
                </header>

                {/* Sticky tab bar */}
                <nav
                    className="sticky top-[57px] z-10 bg-background/95 backdrop-blur border-b border-border mb-4 -mx-4 sm:-mx-6 px-4 sm:px-6 py-2 overflow-x-auto"
                    data-testid="guide-tabs"
                >
                    <div className="flex gap-1 flex-nowrap">
                        {SECTIONS.map((s) => (
                            <button
                                key={s.id}
                                type="button"
                                onClick={() => goTo(s.id)}
                                data-testid={`guide-tab-${s.id}`}
                                className={`text-[10px] tracking-widest whitespace-nowrap px-2.5 py-1.5 rounded-sm border ${
                                    active === s.id
                                        ? "border-amber text-amber bg-amber/10"
                                        : "border-border text-muted-foreground hover:border-amber/40"
                                }`}
                            >
                                {s.label}
                            </button>
                        ))}
                    </div>
                </nav>

                <SectionBlock id="intro" title="Introduzione">
                    <p>
                        <strong>Orbus Online: Guild Master</strong> è un MMO testuale di gestione gilde.
                        Tu sei il Maestro di Gilda: recluti avventurieri, li equipaggi, li invii in dungeon
                        e raid, gestisci risorse e reputazione. Niente sprite, niente animazioni — solo numeri,
                        decisioni e conseguenze.
                    </p>
                    <p className="mt-2">
                        L&apos;obiettivo è scalare la classifica pubblica raggiungendo il <strong>peak team power</strong>
                        più alto possibile e completando dungeon di tier crescente fino al raid.
                    </p>
                </SectionBlock>

                <SectionBlock id="gilda" title="Gilda e progressione">
                    <p>
                        Ogni account ha <strong>una sola gilda</strong>. La gilda ha:
                    </p>
                    <ul className="list-disc list-inside mt-2 space-y-1">
                        <li><strong>Livello</strong>: aumenta completando spedizioni e raid.</li>
                        <li><strong>Reputazione</strong>: sblocca dungeon e contenuti di end-game.</li>
                        <li><strong>Oro</strong>: usato per reclutare, comprare al mercato, e forgiare.</li>
                        <li><strong>Peak Team Power</strong>: il valore massimo di power mai raggiunto da una tua squadra (5p). È il criterio principale di ranking.</li>
                    </ul>
                </SectionBlock>

                <SectionBlock id="territorio" title="Territorio di Gilda">
                    <p>
                        Il <strong>Territorio</strong> è l&apos;insieme delle 11 strutture che la tua gilda può
                        costruire e potenziare. Ogni struttura sblocca o migliora una funzionalità del gioco.
                    </p>
                    <ul className="list-disc list-inside mt-2 space-y-1 text-[12px]">
                        <li><strong>Sala della Gilda</strong> — Cuore amministrativo, è il prerequisito principale per tutte le altre strutture.</li>
                        <li><strong>Dormitori</strong> — Determinano il cap del roster con scala progressiva da Lv1 (cap 5) a Lv11 (cap 100). Sequenza: 5 → 10 → 15 → 20 → 25 → 30 → 40 → 50 → 65 → 80 → 100. Costi gold + materiali progressivi.</li>
                        <li><strong>Bacheca Spedizioni</strong> — Sblocca dungeon di tier più alti.</li>
                        <li><strong>Sala della Guerra</strong> — Lv2 sblocca Raid T1, Lv3 i T2.</li>
                        <li><strong>Banco del Mercato</strong> — Mercato NPC (Lv1=compra, Lv2=vendi).</li>
                        <li><strong>Casa d&apos;Aste</strong> — Mercato player-to-player (Lv1=compra, Lv2=metti in vendita).</li>
                        <li><strong>Officina</strong> — Crafting di nuovi item dalle ricette.</li>
                        <li><strong>Fucina</strong> — Upgrade equipaggiamento (disincanta/raffina/incanta/reroll).</li>
                        <li><strong>Sala dei Consorzi</strong> — Lv1 per unirti, Lv2 per crearne uno.</li>
                        <li><strong>Sala delle Comunicazioni</strong> — Lv1 chat globale, Lv2 chat consorzio.</li>
                        <li><strong>Campo di Addestramento</strong> — Placeholder per specializzazioni (in arrivo ).</li>
                    </ul>
                    <p className="mt-3">
                        Vai a <code>/territory</code> per acquistare e potenziare le strutture. Ogni livello costa
                        gold + materiali; i prerequisiti (es. Fucina richiede Sala Gilda Lv2 + Officina Lv1) sono
                        visualizzati direttamente sulla card.
                    </p>
                    <p className="mt-3 text-amber/90 text-[12px] border-l-2 border-amber/60 pl-3">
                        <strong>Costi sempre scalati:</strong> il costo dichiarato sulla card
                        viene SEMPRE scalato dalle risorse della gilda. Se mancano gold o materiali, l&apos;azione
                        fallisce con un errore chiaro (codice 422 <code>resources.gold_insufficient</code> o
                        <code>resources.material_insufficient</code>) e la gilda NON subisce alcun debit parziale.
                        Le strutture non si comprano mai a costo zero.
                    </p>
                    <p className="mt-2 text-amber/90 text-[12px]">
                        <strong>👑 Lv7-Lv11 (Dormitori, )</strong>: la scala dei livelli ora si estende fino a <strong>Lv11 (cap 100)</strong>. Costi gold + materiali progressivi (no premium, no skip). I cap intermedi sono 40 (Lv7), 50 (Lv8), 65 (Lv9), 80 (Lv10), 100 (Lv11). Account legacy con Lv7 pre-Round 11.2 mantengono il loro cap; le strutture esistenti non vengono modificate.
                        migrazione una-tantum di . Non è acquistabile dall&apos;utente.
                    </p>
                    <p className="mt-2 text-muted-foreground text-[12px]">
                        Se una funzione del gioco mostra un toast <em>&quot;Funzione bloccata&quot;</em>, controlla il Territorio:
                        la struttura corrispondente non ha ancora il livello richiesto.
                    </p>
                </SectionBlock>

                <SectionBlock id="roster-cap" title="Capacità roster e Dormitori">
                    <p>
                        La gilda ha un <strong>cap massimo di avventurieri attivi</strong> determinato dal livello
                        dei <strong>Dormitori</strong>. Potenziare la struttura aumenta il cap:
                    </p>
                    <ul className="list-disc list-inside mt-2 space-y-1 text-[12px]">
                        <li>Lv0 = 0 · Lv1 = 5 · Lv2 = 10 · Lv3 = 15 · Lv4 = 20 · Lv5 = 25 · Lv6 = 30 · Lv7 (legacy) = 50</li>
                    </ul>
                    <p className="mt-3">
                        Quando il roster supera il cap (es. dopo un rollback o una riduzione di Dormitori) la
                        gilda entra in stato <strong>&quot;Roster oltre capacità&quot;</strong> e un banner rosso compare
                        in cima alle pagine Reclutamento, Spedizioni, Raid, Squadre e Territorio.
                    </p>
                    <p className="mt-3 text-[12px] border-l-2 border-amber/60 pl-3 text-amber/90">
                        <strong>AT-cap ≠ over-cap</strong>:
                        essere <em>esattamente a cap</em> (es. 5/5 con Dormitori Lv1) consente il gameplay
                        normale — puoi lanciare spedizioni, raid, costruire squadre ed equipaggiare con i
                        tuoi 5 avventurieri. Il blocco scatta SOLO quando <code>current &gt; cap</code> (vero
                        over-cap, ottenibile solo da un rollback difensivo o da una futura migrazione che
                        riduca il cap). Il reclutamento usa una proiezione (<code>5/5 → 6/5</code>) e quindi
                        rifiuta correttamente il nuovo recruit a cap pieno, lasciandoti le due vie d&apos;uscita
                        (potenzia Dormitori, oppure congeda un avventuriero).
                    </p>
                    <p className="mt-3 text-[12px]"><strong>Azioni bloccate</strong> finché sei over-cap (HTTP 423 <code>roster_over_capacity</code>, solo con <code>current &gt; cap</code>):</p>
                    <ul className="list-disc list-inside mt-1 space-y-1 text-[12px]">
                        <li>Reclutare nuovi avventurieri</li>
                        <li>Avviare spedizioni o raid (anche replay-last)</li>
                        <li>Creare/modificare squadre che includono membri eccedenti</li>
                        <li>Equipaggiare avventurieri congedati</li>
                    </ul>
                    <p className="mt-3 text-[12px]"><strong>Azioni sempre permesse</strong> (le tue vie d&apos;uscita):</p>
                    <ul className="list-disc list-inside mt-1 space-y-1 text-[12px]">
                        <li>Consultare roster, inventario, report storici (GET non sono mai bloccate)</li>
                        <li>Potenziare i Dormitori (aumenta il cap)</li>
                        <li>Congedare avventurieri (libera slot)</li>
                    </ul>
                    <p className="mt-3">
                        Per gestire il congedo in massa vai su <code>/roster/manage</code> dal banner: filtra per nome/ruolo/rarità,
                        ordina per Potenza/Livello, multi-seleziona e conferma. Il congedo è una soft-retire: i
                        <strong> vecchi report che includono l&apos;avventuriero congedato restano sempre leggibili</strong>,
                        e l&apos;equipaggiamento torna in inventario. Il congedo è reversibile via supporto.
                    </p>
                    <p className="mt-2 text-muted-foreground text-[12px]">
                        Prima di congedare, rimuovi manualmente l&apos;equipaggiamento bound se desideri trasferirlo
                        ad altri avventurieri. Niente item viene mai perso.
                    </p>
                </SectionBlock>

                <SectionBlock id="roster-health" title="Roster Health">
                    <p>
                        <strong>Roster Health</strong> è il widget in Dashboard che riassume lo stato della tua capacità roster.
                        Quattro stati colorati per identificare a colpo d&apos;occhio se devi intervenire:
                    </p>
                    <ul className="list-disc pl-5 space-y-1">
                        <li><strong className="text-emerald-300">Sano</strong> — capacità sotto il 70%, puoi reclutare liberamente.</li>
                        <li><strong className="text-yellow-300">Quasi Pieno</strong> — tra 70% e 90%, pianifica i prossimi recruit.</li>
                        <li><strong className="text-orange-300">Al Limite</strong> — tra 90% e 100%, ancora 1-2 slot.</li>
                        <li><strong className="text-red-400">Oltre Capacità</strong> — at-cap consentito (es. ricompense, drop avventuriero) ma non puoi reclutare nuovi finché non riduci il roster con congedo o potenziamento Dormitori.</li>
                    </ul>
                    <h3 className="mt-4 mb-2 text-amber tracking-wider text-[12px]">Item legati (bound)</h3>
                    <p>
                        Alcuni oggetti hanno il badge <strong>LEGATO A <em>{"{avventuriero}"}</em></strong>. Sono legati per design (es. ricompense personali, Signature Item da specializzazione, premi storia) e:
                    </p>
                    <ul className="list-disc pl-5 space-y-1">
                        <li>NON sono equipaggiabili da altri avventurieri.</li>
                        <li>NON sono vendibili al mercato NPC, né listabili in asta.</li>
                        <li>Restano sempre nel tuo Deposito anche dopo il congedo dell&apos;avventuriero (vedi Archivio).</li>
                    </ul>
                    <h3 className="mt-4 mb-2 text-amber tracking-wider text-[12px]">Suggerimento upgrade Dormitori</h3>
                    <p>
                        Quando lo stato è <strong>Quasi Pieno</strong>, <strong>Al Limite</strong> o <strong>Oltre Capacità</strong>,
                        il widget mostra direttamente il <strong>costo del prossimo upgrade dei Dormitori</strong>
                        (oro + materiali) — così sai immediatamente quanto serve risparmiare. Se sei già al livello massimo,
                        il suggerimento non viene mostrato.
                    </p>

                    <h3 className="mt-4 mb-2 text-amber tracking-wider text-[12px]">Archivio congedati</h3>
                    <p>
                        In <em>Gestione Roster → tab Archivio</em> trovi la lista di tutti gli avventurieri congedati con la
                        loro storia (livello al congedo, motivo, data). I report delle spedizioni a cui hanno partecipato
                        restano leggibili dalla Cronaca. Niente viene mai cancellato (soft delete).
                    </p>
                </SectionBlock>

                <SectionBlock id="ruoli" title="Ruoli">
                    <p>
                        Ogni avventuriero ricopre un <strong>ruolo</strong> (Tank, Healer, DPS,
                        Support) che determina la sua funzione in spedizione. Una squadra
                        bilanciata di ruoli completa più dungeon e raid di una squadra
                        sbilanciata, anche a parità di PWR totale.
                    </p>
                </SectionBlock>

                <SectionBlock id="archivio" title="Congedo e Archivio">
                    <p>
                        Il <strong>congedo</strong> non è una cancellazione: l&apos;avventuriero
                        viene spostato in <strong>archivio</strong>. Non occupa più posti nei
                        dormitori e non partecipa a spedizioni, ma il suo nome resta riservato e
                        il suo storico (livello, traits) viene conservato.
                    </p>
                    <p className="mt-2">
                        Un avventuriero archiviato può essere richiamato in roster solo se hai
                        capacità libera. Item personali (bound) restano legati anche dopo il
                        congedo: non sono né commerciabili né reclaim-abili da altri membri.
                    </p>
                </SectionBlock>

                <SectionBlock id="avventurieri" title="Avventurieri">
                    <p>
                        Gli <strong>avventurieri</strong> sono il cuore della tua gilda. Ogni
                        avventuriero ha: nome, livello (1-30), rarità (Common→Legendary),
                        ruolo, classe, statistiche, fino a 3 tratti permanenti, equipaggiamento
                        e (a Lv5+) eventuale specializzazione.
                    </p>
                    <p className="mt-2">
                        Il loro <strong>Power Score (PWR)</strong> è la sintesi numerica del
                        loro potere combinato. Avventurieri identici per PWR possono comportarsi
                        diversamente in base a tratti e specializzazioni: leggere le sezioni 10 e 11
                        è essenziale.
                    </p>
                </SectionBlock>

                <SectionBlock id="rarita" title="Rarità">
                    <p>
                        Ogni avventuriero ha una <strong>rarità</strong>, generata server-side
                        al reclutamento secondo pesi pubblici. La rarità influenza stat iniziali
                        e cap massimi a livello 30.
                    </p>
                    <ul className="list-disc list-inside text-[12px] mt-2 space-y-1">
                        <li><strong>Common</strong> — disponibile, stat base.</li>
                        <li><strong>Uncommon</strong> — leggermente sopra la media.</li>
                        <li><strong>Rare</strong> — top tier per dungeon avanzati.</li>
                        <li><strong>Epic</strong> — molto raro, cap stat elevati.</li>
                        <li><strong>Legendary</strong> — pochi per server, sbloccabili con condizioni speciali.</li>
                    </ul>
                </SectionBlock>

                <StatsCatalogSection active={active} />

                <TraitsCatalogSection active={active} />

                <SectionBlock id="reclutamento" title="Reclutamento">
                    <p>
                        Nella pagina <strong>Reclutamento</strong> trovi avventurieri-candidati
                        generati casualmente dal server. Per ogni candidato vedi: nome, rarità,
                        ruolo, classe, livello iniziale, stat preview e tratti.
                    </p>
                    <p className="mt-2">
                        Puoi fare <strong>refresh</strong> della lista (sostituisce i candidati,
                        può avere un costo o cooldown) oppure <strong>reclutare</strong> uno dei
                        candidati. Se il roster è pieno (Dormitori al massimo) ricevi un errore
                        chiaro: aumenta capacità prima.
                    </p>
                    <p className="mt-3">
                        <strong>Panchina Reclute (Round 11.3)</strong>: ogni candidato ha un&apos;icona
                        <em> ❄ Congela</em>. Cliccala per spostarlo nella <strong>Panchina</strong>:
                        resta lì anche dopo un refresh della lista. La panchina ha <strong>max 2 slot</strong>.
                        Dalla panchina puoi <em>Reclutare</em> il candidato (costo gold standard,
                        come da lista) oppure <em>Rilasciare</em> per liberare lo slot.
                        Il livello iniziale e i tratti del candidato non cambiano mai mentre è
                        congelato.
                    </p>
                </SectionBlock>

                <SectionBlock id="dungeon" title="Dungeon e Spedizioni">
                    <p>
                        I dungeon sono di due famiglie:
                    </p>
                    <ul className="list-disc list-inside mt-2 space-y-1">
                        <li><strong>Legacy (3p)</strong>: 10 dungeon storici da 3 avventurieri ciascuno.</li>
                        <li><strong>5p (Round 5)</strong>: 12 dungeon nuovi da squadre di 5 avventurieri.</li>
                    </ul>
                    <p className="mt-2">
                        Ogni dungeon ha un <strong>tier (T1→T4)</strong> e un <strong>recommended power</strong>.
                        Più ti avvicini o superi il recommended, maggiore è la success chance. Il report finale
                        ti dice esito, loot, XP e gold guadagnati.
                    </p>
                    <p className="mt-2">
                        <strong>Filtri (Phase 19.3)</strong>: sopra la lista dungeon trovi un pannello filtri.
                        Puoi combinare:
                    </p>
                    <ul className="list-disc list-inside mt-1 space-y-1">
                        <li><strong>Squadra</strong>: 3 / 5 / 7 eroi</li>
                        <li><strong>PWR min / max</strong>: range di power consigliato</li>
                        <li><strong>Difficoltà</strong>: facile / medio / difficile / elite</li>
                        <li><strong>Stato</strong>: disponibili / bloccati</li>
                    </ul>
                    <p className="mt-2 text-muted-foreground text-[12px]">
                        Suggerimento rapido: per la tua prima spedizione filtra <em>Squadra=3, Difficoltà=facile</em>.
                        Su mobile, tocca <em>FILTRI ▾</em> per aprire il pannello.
                    </p>
                    <p className="mt-3">
                        <strong>Livelli minimi (Round 11.3)</strong>: alcuni dungeon richiedono che
                        <em> tutti gli avventurieri del team</em> abbiano almeno un livello minimo
                        (es. Lv 3 per T2, Lv 5 per T3/T4, fino a Lv 8 per i contenuti Void/Undead).
                        Nella schermata di lancio spedizione, gli avventurieri sotto-soglia appaiono
                        <em> grigiati</em> con badge <code>Lv min: X</code> e non possono essere
                        selezionati. Il backend riapplica il controllo al dispatch — non c&apos;è modo
                        di aggirarlo lato client.
                    </p>
                    <p>
                        La classifica stagionale è organizzata in <strong>12 categorie</strong>
                        complete: arena (rating, win rate, attacchi/difese vinte), picco di
                        potenza, reputazione, e — dal Round 13b — sei nuove categorie
                        <strong>incrementali per stagione</strong>:
                    </p>
                    <ul className="list-disc list-inside mt-2 space-y-1 text-[12px]">
                        <li><strong>Dungeon completati</strong> — quanti dungeon hai chiuso con successo durante la stagione.</li>
                        <li><strong>Raid completati</strong> — raid 20-uomini con outcome victory/partial.</li>
                        <li><strong>Punteggio Raid</strong> — somma dei <code>raid_score</code> guadagnati.</li>
                        <li><strong>Sviluppo Territoriale</strong> — crescita livelli strutture rispetto all&apos;inizio stagione (delta).</li>
                        <li><strong>Contratti completati</strong> — daily, weekly e milestone reclamati.</li>
                        <li><strong>Allenamenti</strong> — somma del <code>power_score</code> guadagnato tramite specializzazioni.</li>
                    </ul>
                    <p className="mt-2 text-[11px] text-muted-foreground italic">
                        Tutti i contatori sono <strong>resettati</strong> all&apos;inizio di ogni stagione e
                        congelati alla chiusura. Le gilde demo e di test sono escluse dalle classifiche.
                    </p>
                </SectionBlock>

                <SectionBlock id="raid" title="Raid">
                    <p>
                        I raid sono contenuti end-game per squadre composte da <strong>4 party × 5 avventurieri</strong>
                        (20 totali). Richiedono un roster minimo della gilda e un <em>max team power</em> sufficiente.
                    </p>
                    <p className="mt-2">
                        Ogni party affronta una fase indipendente; il <strong>raid score</strong> finale è la
                        media pesata degli outcome di ogni party. Le ricompense includono gold, XP per avventuriero
                        e <em>dragon essence</em> (drop solo da T4-5p e raid).
                    </p>
                    <p className="mt-2">
                        I raid completati appaiono nella <strong>classifica raid pubblica</strong>
                        (<code>/api/leaderboard/raids</code>).
                    </p>
                    <p className="mt-3">
                        <strong>Builder filtri (Phase 19.4a)</strong>: sopra la lista degli avventurieri trovi un
                        pannello filtri per restringere velocemente il roster nei raid di alto livello.
                    </p>
                    <ul className="list-disc list-inside mt-1 space-y-1 text-[12px]">
                        <li><strong>Cerca</strong>, <strong>Ruolo</strong> (multi), <strong>Classe</strong>, <strong>Rarità</strong> (multi)</li>
                        <li><strong>Livello min/max</strong> e <strong>PWR min/max</strong></li>
                        <li><strong>Disponibilità</strong>: tutti / solo disponibili / nascondi occupati</li>
                        <li><strong>Ordinamento</strong>: PWR ↓, Livello ↓, Rarità ↓, Nome, Ruolo</li>
                    </ul>
                    <p className="mt-2 text-muted-foreground text-[12px]">
                        Un avventuriero già assegnato a un party scompare automaticamente dal pool: i filtri
                        non rompono mai i party in costruzione.
                    </p>
                    <p className="mt-3">
                        <strong>Livelli minimi raid (Round 11.3)</strong>: ogni raid ha un
                        <code> min_adventurer_level</code> (es. Lv 8-14 per i raid Void/Undead).
                        Gli avventurieri sotto-soglia appaiono grigiati nel pool con badge
                        <code> Lv min: X</code>; il bottone <em>Avvia raid</em> resta bloccato
                        finché ogni assegnato rispetta la soglia.
                    </p>
                    <p className="mt-3">
                        <strong>Lore Void / Non-Morti (Round 11.3)</strong>: nel catalogo trovi
                        15 nuovi contenuti (10 dungeon + 5 raid) tematici sull&apos;invasione del Vuoto
                        e sulla risalita dei Non-Morti. Hanno descrizioni narrative in italiano,
                        livelli minimi più alti e rappresentano l&apos;end-game corrente. Cerca tag
                        <em> Void</em> / <em>Undead</em> nei filtri.
                    </p>
                </SectionBlock>

                <SectionBlock id="classifiche" title="Classifiche (Round 11.3)">
                    <p>
                        Nella pagina <strong>Classifiche</strong> ora trovi <strong>8 categorie</strong>
                        di ranking pubblico. Ogni categoria mostra le top 10 gilde per quel
                        criterio, più la tua posizione (<em>my_entry</em>) se rientri nella top 500.
                    </p>
                    <ul className="list-disc list-inside mt-2 space-y-1 text-[12px]">
                        <li><strong>Peak Power</strong>: massimo team power mai raggiunto da una squadra della gilda.</li>
                        <li><strong>Raid Score</strong>: somma dei punteggi dei raid completati con successo.</li>
                        <li><strong>Dungeon Clears</strong>: numero totale di spedizioni dungeon vittoriose.</li>
                        <li><strong>Raid Clears</strong>: numero di raid completati con successo.</li>
                        <li><strong>Territory Score</strong>: punteggio accumulato dalle attività territoriali.</li>
                        <li><strong>Contracts Completed</strong>: contratti di gilda completati.</li>
                        <li><strong>Training Score</strong>: punteggio cumulato delle sessioni di addestramento.</li>
                        <li><strong>Roster Avg Level</strong>: livello medio del roster attivo (almeno 5 avventurieri).</li>
                    </ul>
                    <p className="mt-2 text-muted-foreground text-[12px]">
                        I dati sono cached lato server con TTL breve (~30s) per evitare carico.
                        Cambia categoria con i tab in alto; l&apos;URL mantiene la categoria selezionata
                        (puoi condividere link diretti).
                    </p>
                </SectionBlock>

                {/* ROUND 13a — Lore visibility pack */}
                <SectionBlock id="nuovi-dungeon-void" title="Nuovi Dungeon: Vuoto / Non-Morti (Round 11.3)">
                    <p>
                        Il <strong>Round 11.3</strong> ha introdotto <strong>10 nuovi dungeon</strong> dedicati al
                        ciclo del <strong>Vuoto Eterno</strong> e dei <strong>Non-Morti</strong>. Tutti sono già
                        attivi: li riconosci dal badge <code>NUOVO</code> e <code>✦ VUOTO</code> sulla pagina
                        Dungeon, con il <code>Lv min</code> richiesto per ogni avventuriero della squadra.
                    </p>
                    <ul className="list-disc list-inside mt-2 space-y-1 text-[12px]">
                        <li><strong>Echi del Filo Spezzato</strong> — Lv min 1, tema: vuoto onboarding.</li>
                        <li><strong>Il Sigillo Spezzato di Ergolat</strong> — Lv min 2, tema: ergolat.</li>
                        <li><strong>Gli Obelischi del Vuoto</strong> — Lv min 4, tema: vuoto.</li>
                        <li><strong>Tane Putride della Piaga dei Mille Volti</strong> — Lv min 6, tema: irthe.</li>
                        <li><strong>I Fili Lunari di Alevora</strong> — Lv min 8, tema: alevora.</li>
                        <li><strong>Corte Cripta di Ashkaroth</strong> — Lv min 10, tema: ashkaroth.</li>
                        <li><strong>Santuario Velato di Eclipthra</strong> — Lv min 12, tema: eclipthra.</li>
                        <li><strong>La Marea di Gralca</strong> — Lv min 15, tema: gralca.</li>
                        <li><strong>La Gola di Silenzio di Xal&apos;Zoraax</strong> — Lv min 18, tema: xal_zoraax (endgame).</li>
                        <li><strong>Prova della Punta dell&apos;Oblio</strong> — Lv min 20, tema: vuoto endgame.</li>
                    </ul>
                    <p className="mt-2 text-[11px] text-muted-foreground italic">
                        Tutti i dungeon di Orbus (vecchi e nuovi) sono stati riallineati alla lore del
                        Lore Book ufficiale. Le descrizioni e i nomi italiani sono ora canonici.
                    </p>
                </SectionBlock>

                <SectionBlock id="nuovi-raid-void" title="Nuovi Raid: Vuoto / Non-Morti (Round 11.3)">
                    <p>
                        Insieme ai dungeon, il <strong>Round 11.3</strong> ha aggiunto <strong>5 nuovi raid</strong>
                        (20 avventurieri, 4 parties × 5). Ognuno richiede un livello roster crescente:
                    </p>
                    <ul className="list-disc list-inside mt-2 space-y-1 text-[12px]">
                        <li><strong>Il Rituale del Vuoto</strong> — Lv min 10, boss: Officiante delle Orde.</li>
                        <li><strong>Marcia dei Figli di Irthe</strong> — Lv min 14, boss: Primogenito di Irthe.</li>
                        <li><strong>Il Gran Teatro di Alevora</strong> — Lv min 18, boss: Marionettista Lunare.</li>
                        <li><strong>Tempio del Vuoto Eterno</strong> — Lv min 24, boss: Erede del Tempio.</li>
                        <li><strong>L&apos;Ultimo Sussurro di Valys Mordivac</strong> — Lv min 30, boss: Valys Mordivac (endgame).</li>
                    </ul>
                    <p className="mt-2 text-[11px] text-muted-foreground italic">
                        I 3 raid baseline (Bastione Spezzato, Necropoli delle Mille Campane, Volta del Drago
                        Addormentato) sono stati anch&apos;essi riallineati alla lore.
                    </p>
                </SectionBlock>

                <SectionBlock id="lore-vuoto-nonmorte" title="Lore — Vuoto, Filo Spezzato, Non-Morti">
                    <p>
                        Il mondo di <strong>Orbus</strong> è attraversato dal <strong>Filo Spezzato</strong> e dalla
                        sua <strong>Sinfonia</strong>: una musica che non si ascolta, ma che ti suona. Dove il Filo
                        si lacera, il <strong>Vuoto Eterno</strong> trabocca. Non distrugge: divora ciò che ti
                        ricorda di essere.
                    </p>
                    <p className="mt-2">
                        I <strong>Sigilli di Ergolat</strong> non chiudono il Vuoto. Lo addomesticano. Quando uno
                        si incrina, le <strong>Orde Senza Volto</strong> fiutano l&apos;apertura e si moltiplicano
                        attorno agli <strong>Obelischi Neri</strong>. Gli <strong>Esiliati del Vuoto Eterno</strong>
                        sono uomini che hanno smesso di voler ricordare; pregano nelle <strong>Cripte d&apos;Ombra</strong>
                        chi non risponde più.
                    </p>
                    <p className="mt-2">
                        I <strong>Non-Morti</strong> della <strong>Piaga dei Mille Volti</strong> servono
                        <strong> Irthe</strong>, che cammina in processione senza ricordare dove era diretta.
                        <strong> Alevora la Marionettista Lunare</strong> tira i fili sotto la <strong>Luna Morta</strong>;
                        chi la osserva troppo a lungo diventa marionetta a sua volta.
                    </p>
                    <p className="mt-2">
                        Più in profondità, <strong>Ashkaroth</strong> presiede una corte di morti silenti; il suo
                        verdetto è inciso nelle ossa. <strong>Eclipthra</strong> abita un tempio dietro l&apos;eclissi;
                        il suo velo si solleva appena, ed è già abbastanza. <strong>Gralca</strong> guida una marea
                        che sale dove non c&apos;è cielo. <strong>Xal&apos;Zoraax</strong> non parla: occupa la
                        <strong> Gola del Silenzio</strong>.
                    </p>
                    <p className="mt-2">
                        All&apos;ultimo gradino c&apos;è <strong>Valys Mordivac</strong>, custode finale del
                        <strong> Tempio del Vuoto Eterno</strong>: il tempio non venera nulla, insegna a non aver
                        bisogno di nulla. La <strong>Punta dell&apos;Oblio</strong> è la prova ultima: l&apos;ultimo
                        passo conta sempre verso il basso.
                    </p>
                    <p className="mt-2 text-[11px] text-muted-foreground italic">
                        Tutti i lemmi sono presi verbatim dal <em>Lore Book di Orbus v1</em>. Gli oggetti
                        Leggendari hanno <code>spoiler_level: mystery</code> per non svelare il finale.
                    </p>
                </SectionBlock>

                <SectionBlock id="squadre" title="Squadre Personalizzate">
                    <p>
                        Le <strong>Squadre</strong> sono raggruppamenti di avventurieri salvati per riusarli
                        all&apos;istante. Sono <strong>pura comodità UX</strong>: nessun bonus al power, nessun
                        effetto magico. Servono solo a evitare di riselezionare manualmente lo stesso team
                        ogni volta che lanci una spedizione o un raid.
                    </p>
                    <p className="mt-2">Sono di 3 tipi, in base al contenuto:</p>
                    <ul className="mt-2 space-y-1 text-[12px]">
                        <li><strong>Dungeon 3</strong> — 3 avventurieri per dungeon a 3 slot</li>
                        <li><strong>Dungeon 5</strong> — 5 avventurieri per dungeon a 5 slot</li>
                        <li><strong>Raid 20</strong> — 20 avventurieri organizzati in 4 party da 5</li>
                    </ul>
                    <p className="mt-3">
                        <strong>Come crearle</strong>: vai su <code className="text-amber">/squads</code> →
                        click <strong>+ Nuova</strong> nella sezione del tipo desiderato. Cerca/filtra gli
                        avventurieri dal pool a sinistra, clicca per assegnare. Il power totale e gli
                        eventuali warning composizione (Manca Tank, Manca Healer, Troppi DPS) sono
                        ricalcolati in tempo reale. Salva quando il counter è pieno (es. 5/5).
                    </p>
                    <p className="mt-2">
                        <strong>Raid 20</strong>: il builder mostra 4 party slot (2×2 grid). Seleziona la party
                        attiva con il dropdown, poi clicca dal pool. Nessun avventuriero può finire in due
                        party diverse dello stesso raid.
                    </p>
                    <p className="mt-2">
                        <strong>Modifica / Archivia</strong>: dalla lista, ogni card squadra ha
                        <em> Modifica</em> e <em>Archivia</em>. L&apos;archiviazione è soft: la squadra non
                        viene mai eliminata davvero, scompare solo dalla lista attiva. Puoi sempre crearne
                        una nuova con lo stesso nome dopo aver archiviato.
                    </p>
                    <p className="mt-2 text-muted-foreground text-[12px]">
                        Limiti: nome 2-32 caratteri, niente HTML. Un avventuriero in spedizione/raid in corso
                        appare come <em>non disponibile</em> nella card squadra ma resta salvato — quando torna
                        libero, la squadra è di nuovo utilizzabile com&apos;è.
                    </p>
                    <p className="mt-2 text-muted-foreground text-[12px]">
                        <strong>Integrazione con expedition/raid</strong>: in arrivo nel prossimo update
                        — un selettore &quot;Carica squadra&quot; dentro
                        <code className="text-amber"> /expeditions/new</code> e
                        <code className="text-amber"> /raids/builder</code> per popolare il team con un click.
                    </p>
                </SectionBlock>

                <SectionBlock id="forge" title="Equipaggiamento e Fucina">
                    <p>
                        Ogni avventuriero ha 3 slot: <strong>weapon</strong>, <strong>armor</strong>, <strong>accessory</strong>.
                        Gli oggetti hanno rarità (Common → Uncommon → Rare → Epic), un livello richiesto e bonus statistici.
                    </p>
                    <p className="mt-2">
                        Equipaggi dall&apos;<strong>Inventario</strong>: click su un oggetto equipaggiabile → si apre
                        un modal con la lista degli avventurieri compatibili e una preview del power risultante.
                    </p>
                    <p className="mt-2">
                        Alla <strong>Forge</strong> puoi <em>raffinare</em> (refinement +1 → +10) o <em>incantare</em>
                        un oggetto per migliorarne i bonus. Refinement e incanto sono permanenti e legano l&apos;oggetto (◆ BOUND).
                    </p>
                    <p className="mt-3">
                        <strong>Livello richiesto item (Round 11.3)</strong>: ogni oggetto ha un
                        <code> required_adventurer_level</code>. Nel modal di equip gli oggetti
                        sotto-soglia per l&apos;avventuriero corrente appaiono grigiati con badge
                        <code> Lv X richiesto</code> e il bottone <em>Equip</em> è disabilitato.
                        Gli oggetti già equipaggiati in passato senza requisito sono lasciati come sono,
                        salvo un&apos;audit di pulizia che il team admin esegue periodicamente.
                    </p>
                </SectionBlock>

                {/* ROUND 13a — equip level gate + lore tematica */}
                <SectionBlock id="equip-level-gate" title="Livello richiesto per equipaggiare (Round 13a)">
                    <p>
                        Ogni oggetto della Fucina ha un <strong>livello minimo</strong> per essere
                        equipaggiato. La regola è uniforme su tutto il catalogo (~121 oggetti):
                    </p>
                    <ul className="list-disc list-inside mt-2 space-y-1 text-[12px]">
                        <li><strong>Comune</strong> — Lv 1</li>
                        <li><strong>Non comune</strong> — Lv 3</li>
                        <li><strong>Raro</strong> — Lv 5</li>
                        <li><strong>Epico</strong> — Lv 8</li>
                        <li><strong>Leggendario</strong> — Lv 12</li>
                    </ul>
                    <p className="mt-2">
                        Nel modal di equipaggiamento, gli oggetti che il tuo avventuriero non può ancora
                        portare sono <strong>greyed-out</strong> con badge <code>Lv X richiesto</code> e
                        tooltip esplicito. Il bottone Equip è disabilitato lato client; il backend
                        risponde <code>HTTP 423 equipment.required_level_not_met</code> se forzato.
                    </p>
                    <p className="mt-2 text-[11px] text-muted-foreground italic">
                        Al rilascio del Round 13a un&apos;audit ha rilasciato automaticamente
                        equipaggiamenti incompatibili. Gli oggetti restano nell&apos;inventario di gilda —
                        nessuna perdita di item, solo un &quot;ti tolgo l&apos;arma fino a che non sei pronto&quot;.
                    </p>
                </SectionBlock>

                <SectionBlock id="equip-lore-tematica" title="Lore tematica degli oggetti">
                    <p>
                        Il <strong>Round 13a</strong> ha riallineato i nomi italiani degli oggetti alla
                        lore di Orbus. Ogni rarità ha un&apos;impronta narrativa diversa:
                    </p>
                    <ul className="list-disc list-inside mt-2 space-y-1 text-[12px]">
                        <li><strong>Comune</strong>: nomi puliti, nessun riferimento lore (&quot;Spada di Ferro&quot;).</li>
                        <li><strong>Non comune</strong>: riferimenti soft, suffisso &quot;del Confine&quot;.</li>
                        <li><strong>Raro</strong>: suffisso &quot;delle Veglie&quot; + flavor 1-riga.</li>
                        <li><strong>Epico</strong>: suffisso &quot;del Filo Spezzato&quot;, flavor evocativo.</li>
                        <li><strong>Leggendario</strong>: nomi hand-written (es. <em>Arco Trafittore del Vuoto</em>,
                            <em> Pendente dell&apos;Oracolo Cieco</em>, <em>Eco della Sinfonia dei Fili</em>,
                            <em> Maschera della Luna Morta</em>), <code>spoiler_level: mystery</code>.</li>
                    </ul>
                    <p className="mt-2">
                        Nel <strong>Mercato</strong>, <strong>Asta</strong>, <strong>Inventario</strong> e modal
                        <strong> Equip</strong> vedi sempre il <code>display_name_it</code>. Il <code>flavor_text</code>
                        compare nel dettaglio dell&apos;oggetto: una riga, mai più di due.
                    </p>
                    <p className="mt-2 text-[11px] text-muted-foreground italic">
                        Lo slug tecnico (<code>iron-sword</code>, <code>voidpiercer-bow</code>, …) è invariato:
                        backwards-compat garantita su tutte le aste storiche e i bookmark.
                    </p>
                </SectionBlock>

                <SectionBlock id="bound-items" title="Item legati">
                    <p>
                        Alcuni oggetti sono <strong>legati</strong> (bound) all&apos;avventuriero
                        che li ha ottenuti. Item legati: non sono commerciabili (Mercato/Asta),
                        non sono equipaggiabili da altri membri, restano legati anche dopo
                        congedo/archiviazione del proprietario.
                    </p>
                    <p className="mt-2">
                        Sono identificati da un&apos;icona/badge dedicato in Inventario e Forge.
                        I bonus di set restano calcolati anche per item legati: il sistema non
                        crea differenze gameplay per il proprietario.
                    </p>
                </SectionBlock>

                <SectionBlock id="training" title="Campo di Addestramento e Specializzazioni">
                    <p>
                        Il <strong>Campo di Addestramento</strong> (Training Grounds) è la struttura del Territorio che
                        permette di specializzare gli avventurieri di livello 5 o superiore.
                    </p>
                    <h3 className="mt-3 mb-2 text-amber tracking-wider text-[12px]">Prerequisiti & livelli</h3>
                    <ul className="list-disc pl-5 space-y-1">
                        <li>Prereq: Guild Hall Lv3 + Dormitori Lv2.</li>
                        <li><strong>Lv1 (Starter)</strong> — sblocca le 4 specializzazioni base. Costo apply: 500 oro.</li>
                        <li><strong>Lv2</strong> — costo apply ridotto a 400 oro.</li>
                        <li><strong>Lv3 (Full Hybrid)</strong> — sblocca anche le 10 specializzazioni avanzate. Costo apply: 1500 oro.</li>
                        <li><strong>Lv4-6</strong> — placeholder per future estensioni (slot extra, respec, set bonus).</li>
                    </ul>
                    <h3 className="mt-4 mb-2 text-amber tracking-wider text-[12px]">Bonus stat</h3>
                    <p>
                        Ogni specializzazione fornisce un bonus permanente:
                        <strong> +2 alla stat principale</strong> della classe + <strong>+1 alla stat secondaria</strong>.
                        Bonus additivi (non moltiplicativi): NO P2W, NO power gear, solo crescita lineare.
                    </p>
                    <h3 className="mt-4 mb-2 text-amber tracking-wider text-[12px]">Le 4 specializzazioni Starter (Tier 1)</h3>
                    <ul className="list-disc pl-5 space-y-1">
                        <li><strong>Difensore</strong> (Tank) — Warrior / Paladin. +2 END, +1 STR. Signature: Egida del Difensore.</li>
                        <li><strong>Cecchino</strong> (DPS) — Ranger / Rogue. +2 AGI, +1 STR. Signature: Arco del Colpo Vero.</li>
                        <li><strong>Restauratore</strong> (Healer) — Priest / Druid. +2 FAI, +1 INT. Signature: Calice Sacro.</li>
                        <li><strong>Stratega</strong> (Support) — Bard / Paladin. +2 INT, +1 END / FAI. Signature: Stendardo da Battaglia.</li>
                    </ul>
                    <h3 className="mt-4 mb-2 text-amber tracking-wider text-[12px]">Le 10 Full Hybrid (Tier 3, da TG Lv3)</h3>
                    <p>
                        A partire da Training Grounds Lv3 si sbloccano <strong>10 specializzazioni avanzate</strong>
                       . Ogni Full Hybrid ha il proprio Signature Item Epico.
                    </p>
                    <ul className="list-disc pl-5 space-y-1 text-[12px]">
                        <li><strong>Furia</strong> (DPS Warrior) — Grand&apos;Ascia Insanguinata.</li>
                        <li><strong>Distruttore</strong> (Tank-DPS) — Manopole del Sfondatore.</li>
                        <li><strong>Assassino</strong> (Pure DPS Rogue) — Kris Silente.</li>
                        <li><strong>Arcanista</strong> (DPS Mage) — Focus Runico.</li>
                        <li><strong>Elementalista</strong> (AOE Mage) — Bastone della Tempesta.</li>
                        <li><strong>Cantore di Battaglia</strong> (Support Bard) — Corno di Guerra.</li>
                        <li><strong>Paladino Oscuro (NEW 6E)</strong> — Warrior/Paladin ibrido Tank/DPS oscuro.</li>
                        <li><strong>Difensore della Natura (NEW 6E)</strong> — Druid/Ranger ibrido protettivo.</li>
                        <li><strong>Maestro di Armi (NEW 6E)</strong> — Warrior/Ranger DPS pluristile.</li>
                        <li><strong>Guardiano Runico (NEW 6E)</strong> — Mage/Paladin ibrido magia difensiva.</li>
                    </ul>
                    <h3 className="mt-4 mb-2 text-amber tracking-wider text-[12px]">Signature Item</h3>
                    <p>
                        Applicare una specializzazione genera automaticamente un <strong>Signature Item</strong> legato
                        all&apos;avventuriero (slot dedicato, rarità Rare). Resta visibile nel tuo Deposito con il badge
                        <em> &quot;Legato a {"{nome}"}&quot;</em>. Non può essere disequipaggiato, venduto, listato o trasferito.
                    </p>
                    <p className="mt-2 text-muted-foreground text-[12px]">
                        <strong>Congedo di un avventuriero specializzato</strong>: la finestra di congedo mostra un warning rosso
                        + una checkbox esplicita <em>&quot;Distruggi anche il signature item&quot;</em>. La checkbox deve essere
                        spuntata per procedere. L&apos;item viene soft-discarded (resta in DB come storico, ma non più
                        utilizzabile e non più legato).
                    </p>
                    <h3 className="mt-4 mb-2 text-amber tracking-wider text-[12px]">Respec</h3>
                    <p>
                        <strong>Round 6E ha sbloccato il respec</strong>: puoi cambiare la specializzazione di un
                        avventuriero già specializzato dal pulsante <em>⟲ Respec</em> nella lista &quot;Avventurieri già
                        specializzati&quot;.
                    </p>
                    <ul className="list-disc pl-5 space-y-1 text-[12px]">
                        <li><strong>Costo crescente</strong> per respec_count: 800g + 1 polvere arcana (primo),
                            1200g + 2 polvere (secondo), 2000g + 3 polvere (terzo e successivi — cap fisso).
                        </li>
                        <li><strong>Cooldown 24h</strong> tra un respec e l&apos;altro per lo stesso avventuriero.</li>
                        <li><strong>Signature item attuale viene distrutto</strong> (soft-discard, irreversibile).
                            Il modal richiede una checkbox di conferma esplicita prima di procedere. Viene poi creato
                            un nuovo signature item per la nuova specializzazione.
                        </li>
                        <li><strong>Atomico server-side</strong>: oro + materiali debitati con CAS, su qualsiasi
                            fallimento intermedio i debit vengono rollbackati. Niente duplicazioni di signature.
                        </li>
                        <li><strong>NO P2W</strong>: costo modesto, non si può saltare la cooldown con denaro reale.</li>
                    </ul>
                    <h3 className="mt-4 mb-2 text-amber tracking-wider text-[12px]">Limiti attuali</h3>
                    <ul className="list-disc pl-5 space-y-1">
                        <li>Il respec richiede stessa classe-eligibility della nuova spec (es. un Mago non può
                            diventare Difensore).
                        </li>
                        <li>Slot extra, set bonus e tier 4-6 di Training Grounds restano placeholder per round
                            successivi.
                        </li>
                    </ul>
                </SectionBlock>

                <SectionBlock id="vault" title="Deposito e Inventario">
                    <p>
                        Il <strong>Deposito (Guild Vault)</strong> raccoglie tutti gli oggetti trovati nelle spedizioni.
                        Gli stack mostrano sia copie equipaggiate sia disponibili.
                    </p>
                    <p className="mt-2">
                        Puoi filtrare per tipo (weapon / armor / accessory / consumable / material) o per rarità.
                        Oggetti marcati ⚒ sono usati come <em>materiali di crafting</em>.
                    </p>
                    <p className="mt-3">
                        <strong>Quando un oggetto è vendibile (Phase 19.4a fix)</strong>:
                    </p>
                    <ul className="list-disc list-inside mt-1 space-y-1 text-[12px]">
                        <li><strong>Disponibile</strong>: quantità &gt; 0 dopo aver tolto equipaggiati e già in vendita.</li>
                        <li><strong>Non bound</strong>: oggetti raffinati/incantati (◆ BOUND) non sono vendibili.</li>
                        <li><strong>Non equipaggiato</strong>: rimuovi prima dall&apos;avventuriero.</li>
                        <li><strong>Tradeable</strong>: alcuni oggetti narrativi/legati sono &quot;Non commerciabili&quot;.</li>
                    </ul>
                    <p className="mt-2 text-muted-foreground text-[12px]">
                        Bug fix 19.4a: la pagina Mercato leggeva la chiave sbagliata della risposta API
                        (<code>items</code> invece di <code>inventory</code>) → la lista vendita appariva vuota anche
                        quando il deposito non lo era. Ora il deposito viene letto correttamente.
                    </p>
                </SectionBlock>

                <SectionBlock id="materiali" title="Materiali e dove trovarli">
                    <p>
                        I <strong>materiali</strong> sono risorse usate per potenziare strutture del
                        Territorio, craftare oggetti in Fucina e disincantare equip. Si ottengono
                        giocando: dungeon, raid, contratti, mercato NPC, disincanto.
                    </p>
                    <p className="mt-2">
                        Nessun materiale è acquistabile con denaro reale né tramite admin.
                        Sono <strong>non equipaggiabili</strong> e generalmente <strong>non legati</strong>
                        (puoi venderli in Asta).
                    </p>
                    <p className="mt-3">
                        Per il catalogo completo con descrizioni, rarità, fonti e usi: apri la pagina
                        pubblica <a href="/materials" className="text-amber underline" data-testid="guide-link-materials">/materials</a>.
                        Lo stesso elenco è esposto via API a <code>/api/materials/catalog</code>.
                    </p>
                    <p className="mt-3 text-[12px] text-muted-foreground">
                        <strong>Quando potenzi una struttura</strong>: il Territorio mostra ora il
                        costo completo (oro + materiali con quantità richiesta vs posseduta) PRIMA
                        del click. Materiali messi in vendita all&apos;Asta non sono spendibili per
                        upgrade (sono &quot;bloccati&quot; finché annulli il listing).
                    </p>
                </SectionBlock>

                <SectionBlock id="market" title="Mercato">
                    <p className="mb-3 text-amber/90 text-[12px] border-l-2 border-amber/60 pl-3">
                        <strong>Mercato ≠ Asta.</strong> Il Mercato è il negozio NPC di sistema (prezzi fissi,
                        rotazione giornaliera). L&apos;Asta è il marketplace player-to-player. Sono{" "}
                        <em>due sistemi distinti</em>: il bottone &quot;Vendi al Mercato&quot; vende a NPC; per vendere ad altri player
                        usa <strong>&quot;Metti all&apos;Asta&quot;</strong> dall&apos;inventario.
                    </p>
                    <p>
                        Il <strong>Mercato di Sistema</strong> (sezione <code>/market</code>) è il negozio gestito dal Mastro Mercante.
                        Offre fino a <strong>9 oggetti per ciclo</strong> (materiali Common/Uncommon + 1 Rare gated) che ruotano
                        <strong> ogni 2 ore</strong> (Round 13c).
                    </p>
                    <ul className="list-disc list-inside mt-2 space-y-1">
                        <li><strong>Compra</strong>: paghi gold, ricevi materiali/consumabili Common/Uncommon. Niente Legendary, niente forge endgame: il Mercato è pensato per coprire i buchi di crafting, non per saltare la progressione.</li>
                        <li><strong>Materiali abbondanti</strong>: stock triplicato sui Common (75-120 unità), raddoppiato sui Uncommon (20-30). I materiali rari restano gated (stock basso, prezzo alto).</li>
                        <li><strong>Vendi</strong>: il Mercato compra ogni oggetto vendibile al <strong>40%</strong> del prezzo d&apos;acquisto (gap anti-exploit). Bound/equipaggiati/in Asta sono rifiutati con un motivo specifico.</li>
                        <li><strong>Refresh</strong>: il countdown nell&apos;header è autoritativo lato server (no localStorage). Ogni 2 ore (allo scoccare dei minuti pari: 00, 02, 04, …, 22 UTC) la rotazione cambia.</li>
                        <li><strong>Rate limit</strong>: max 10 transazioni / 10s per evitare scraping.</li>
                        <li><strong>Quantità max</strong>: 99 per transazione.</li>
                    </ul>
                    <p className="mt-2">
                        Il <strong>Crafting</strong> consuma materiali del deposito per produrre oggetti seguendo ricette. Vedi
                        il tab Crafting (collegato dal deposito) per la lista delle ricette sbloccate.
                    </p>
                    <p className="mt-2 text-muted-foreground text-[12px]">
                        Vuoi vendere a un altro giocatore? Vai all&apos;<strong>Asta</strong> (sezione successiva).
                    </p>
                </SectionBlock>

                <SectionBlock id="auction" title="Asta">
                    <p>
                        L&apos;<strong>Asta</strong> (sezione <code>/auction</code>) è il marketplace dove le gilde si scambiano oggetti
                        a <strong>prezzo fisso</strong> (niente bidding per ora).
                    </p>
                    <ul className="list-disc list-inside mt-2 space-y-1">
                        <li><strong>Compra da giocatori</strong>: cerca per tipo, rarità, prezzo, livello. Vedi solo il nome pubblico della gilda venditrice — mai email o user id.</li>
                        <li><strong>Vendi all&apos;Asta</strong>: scegli un oggetto vendibile (non bound, non equipaggiato, tradeable), imposta prezzo per unità e quantità. La gilda acquirente paga, tu ricevi gold meno la commissione di sistema.</li>
                        <li><strong>Le mie inserzioni</strong>: puoi cancellare le tue listing in qualsiasi momento prima dell&apos;acquisto.</li>
                        <li><strong>Acquisto atomico</strong>: oro debitato, oggetto trasferito, listing rimossa in una sola transazione. Niente duplicazioni, niente perdite.</li>
                    </ul>
                    <p className="mt-2 text-muted-foreground text-[12px]">
                        Differenze rispetto al Mercato: il Mercato di Sistema è sempre disponibile a prezzo fisso (anti-grind), l&apos;Asta è un marketplace libero tra giocatori. Le vecchie URL <code>/api/market/listings*</code> continuano a funzionare via redirect automatico.
                    </p>
                </SectionBlock>

                <SectionBlock id="contracts" title="Contratti e Obiettivi di Gilda">
                    <p>
                        La <strong>Bacheca Contratti</strong> è una struttura del Territorio che apre tre canali
                        di retention: contratti giornalieri, contratti settimanali e milestone permanenti.
                    </p>
                    <h3 className="mt-3 mb-2 text-amber tracking-wider text-[12px]">Struttura & prerequisiti</h3>
                    <ul className="list-disc pl-5 space-y-1">
                        <li>Slug struttura: <code>contract_board</code>. Prereq: Guild Hall Lv2 + Bacheca Spedizioni Lv1.</li>
                        <li>Costo Lv1: 1200 oro + 3 frammento di ferro.</li>
                        <li>Lv1 sblocca daily + weekly + milestone Tier 1. Lv2/3 riservati per future estensioni.</li>
                    </ul>
                    <h3 className="mt-4 mb-2 text-amber tracking-wider text-[12px]">Contratti giornalieri (3 attivi)</h3>
                    <ul className="list-disc pl-5 space-y-1">
                        <li>Completa 1 spedizione → +60 oro</li>
                        <li>Crea 1 listing al mercato → +40 oro + 1 frammento di ferro</li>
                        <li>Crafta 1 oggetto → +50 oro</li>
                    </ul>
                    <p className="mt-2 text-muted-foreground text-[12px]">
                        Reset automatico ogni giorno a <strong>mezzanotte UTC</strong>. Anti-grind: NESSUNA reputazione
                        dai daily. Reward bilanciato per ~30% di un dungeon clear.
                    </p>
                    <h3 className="mt-4 mb-2 text-amber tracking-wider text-[12px]">Contratti settimanali (4 attivi su pool 8)</h3>
                    <ul className="list-disc pl-5 space-y-1">
                        <li>Completa 5 spedizioni → +250 oro + 2 frammento ferro + 2 Rep</li>
                        <li>Vendi 3 oggetti al mercato → +180 oro + 1 cuoio + 1 Rep</li>
                        <li>Potenzia 1 struttura del Territorio → +300 oro + 1 polvere arcana minore + 3 Rep</li>
                        <li>Applica 1 specializzazione → +200 oro + 1 polvere arcana minore + 2 Rep <em>(sinergia 6C)</em></li>
                        <li>Recluta 2 nuovi avventurieri → +150 oro + 1 frammento ferro + 1 Rep</li>
                        <li><strong>NEW 6E</strong>: Completa 3 raid → +280g + iron_shard + 3 Rep (richiede War Room)</li>
                        <li><strong>NEW 6E</strong>: Esegui 3 refinement in Fucina → +200g + iron_shard + 2 Rep (richiede Fucina)</li>
                        <li><strong>NEW 6E</strong>: Crea 2 listing in Asta → +220g + cuoio + 2 Rep (richiede Casa d&apos;Aste)</li>
                    </ul>
                    <p className="mt-2 text-muted-foreground text-[12px]">
                        Reset automatico ogni <strong>lunedì alle 00:00 UTC</strong>. La reputazione gilda è usata per il
                        leaderboard. <strong>Feature-gating</strong>: i contratti che richiedono una struttura
                        (raid → War Room, forge → Fucina, asta → Casa d&apos;Aste) appaiono solo se quella struttura è
                        sbloccata. Lo slot di rotazione settimanale non viene mai sprecato su un contratto bloccato.
                    </p>
                    <h3 className="mt-4 mb-2 text-amber tracking-wider text-[12px]">Milestone permanenti (3 Tier, completi)</h3>
                    <p>
                        I milestone <strong>non si resettano mai</strong> e sono organizzati in 3 tier progressivi:
                    </p>
                    <ul className="list-disc pl-5 space-y-1">
                        <li><strong>Tier 1 (3 milestone, attivi dal Day 1)</strong> — Spedizioni 10, Craft 10, Recruit 5.
                            Reward 100-200g + 5 Rep ciascuno.
                        </li>
                        <li><strong>Tier 2 (7 milestone, sblocco dopo aver claimato TUTTI i Tier 1)</strong> —
                            Spedizioni 50, Craft 50, Recruit 25, Raid 10, Market 30 vendite, Strutture 5 upgrade,
                            Spec applicate 3. Reward 600-1200g + 15-20 Rep.
                        </li>
                        <li><strong>Tier 3 (7 milestone end-game, sblocco dopo TUTTI i Tier 2)</strong> —
                            Spedizioni 200, Craft 200, Recruit 50, Raid 50, Market 100, Strutture 15, Spec 8.
                            Reward 2000-3000g + 50 Rep + greater_arcane_dust/iron_shard stacks.
                        </li>
                    </ul>
                    <h3 className="mt-4 mb-2 text-amber tracking-wider text-[12px]">Sinergia Round 6C ↔ Round 6D ↔ Round 6E</h3>
                    <p>
                        Applicare una spec incrementa <em>&quot;Applica 1 specializzazione&quot;</em>. Completare un raid,
                        fare un refinement in Fucina o listare in Asta incrementa i rispettivi contratti weekly 6E.
                        Reward conservativi anche per il respec — niente incentivi a spec-and-respec abuse.
                    </p>
                    <h3 className="mt-4 mb-2 text-amber tracking-wider text-[12px]">Garanzie fairness</h3>
                    <ul className="list-disc pl-5 space-y-1">
                        <li>NO P2W: solo oro, materiali comuni/uncommon, reputazione.</li>
                        <li>NO power gear nei reward: nessun oggetto con bonus combattimento.</li>
                        <li>NO premium / NO XP gilda diretta: la progressione resta nelle spedizioni.</li>
                        <li>Reward bilanciati: daily 30% / weekly 80% / milestone-T3 200% di un dungeon clear standard.</li>
                    </ul>
                </SectionBlock>

                <SectionBlock id="chronicle" title="Cronaca">
                    <p>
                        La <strong>Cronaca (Server Chronicle)</strong> mostra gli eventi recenti dei giocatori
                        sul server: spedizioni completate, oggetti epici trovati, raid vinti. Solo dati pubblici
                        (nome gilda, esito) — mai informazioni private.
                    </p>
                </SectionBlock>

                <SectionBlock id="consortium" title="Consorzi">
                    <p>
                        I <strong>Consorzi</strong> sono gruppi cooperativi tra gilde: condividi un buff settimanale
                        e un canale di comunicazione testuale. Ogni gilda può appartenere a un consorzio alla volta.
                    </p>
                    <p className="mt-2">
                        <strong>Consorzio ≠ Gilda.</strong> La gilda è privata, gestita dal singolo player.
                        Il consorzio è un&apos;alleanza multi-player pubblica.
                    </p>
                    <p className="mt-3">
                        <strong>Come scegliere un Consorzio</strong>: la lista a <code>/consortiums</code> mostra
                        per ogni consorzio nome, tag, numero membri e descrizione (clamp 2 righe). Se la
                        descrizione è lunga, clicca <em>&quot;Leggi tutto →&quot;</em> per aprire il <strong>modal di dettaglio</strong> con
                        descrizione completa, conteggio membri e bottone &quot;Entra&quot;. La descrizione è renderizzata
                        come testo letterale (nessun HTML eseguito — XSS-safe).
                    </p>
                    <p className="mt-2">
                        I membri del consorzio hanno accesso a una <strong>chat privata</strong> accessibile
                        dal menu <em>Chat → tab Consorzio</em>.
                    </p>
                </SectionBlock>

                <SectionBlock id="chat" title="Chat">
                    <p>
                        Dal menu <strong>Chat</strong> hai accesso a due canali:
                    </p>
                    <ul className="list-disc list-inside mt-2 space-y-1">
                        <li>
                            <strong>Globale</strong>: visibile a tutti i giocatori loggati. Per chiedere aiuto,
                            scambiare strategie o organizzare consorzi.
                        </li>
                        <li>
                            <strong>Consorzio</strong>: solo per i membri del tuo consorzio. Più tranquilla,
                            ideale per coordinare raid e crafting.
                        </li>
                    </ul>
                    <p className="mt-2">
                        <strong>Regole</strong>:
                    </p>
                    <ul className="list-disc list-inside mt-1 space-y-1">
                        <li>Niente dati personali, credenziali, email, token o link sospetti.</li>
                        <li>Massimo 500 caratteri per messaggio.</li>
                        <li>Rate limit: <strong>5 messaggi ogni 10 secondi</strong>. Oltre, il server ti dice di rallentare.</li>
                        <li>HTML/script non vengono renderizzati come HTML: scrivi pure quello che vuoi, ma niente formattazione ricca.</li>
                        <li>I messaggi possono essere moderati: rispettiamo regole di buona convivenza.</li>
                    </ul>
                    <p className="mt-2 text-muted-foreground text-[12px]">
                        L&apos;identità mostrata nella chat è il <em>nome pubblico della tua gilda</em>. Email, user id e
                        consortium id non sono mai esposti.
                    </p>
                </SectionBlock>

                <SectionBlock id="privacy" title="Privacy e Sicurezza">
                    <p>
                        <strong>Cosa NON condividere mai in chat</strong>:
                    </p>
                    <ul className="list-disc list-inside mt-1 space-y-1">
                        <li>Email o numero di telefono.</li>
                        <li>Password o token di sessione.</li>
                        <li>Codici di recupero o link di reset.</li>
                        <li>Dati di pagamento.</li>
                    </ul>
                    <p className="mt-2">
                        <strong>Cosa fa il server per te</strong>:
                    </p>
                    <ul className="list-disc list-inside mt-1 space-y-1">
                        <li>I tuoi user_id / guild_id interni non sono mai mostrati ad altri player.</li>
                        <li>La sola identità pubblica è il <em>nome della tua gilda</em>.</li>
                        <li>Gli account flaggati come test non inquinano la chat globale.</li>
                        <li>I tuoi messaggi sono visibili agli altri player nei canali a cui partecipi.</li>
                    </ul>
                    <p className="mt-2 text-muted-foreground text-[12px]">
                        Se qualcuno ti chiede password / token / codici di recupero in chat, non rispondere e segnalalo
                        al support.
                    </p>
                </SectionBlock>

                <SectionBlock id="tips" title="Suggerimenti base">
                    <ul className="list-disc list-inside space-y-2">
                        <li>
                            <strong>Equipaggia sempre i 3 slot</strong> prima di spedire una squadra: ogni slot vuoto
                            è power perso.
                        </li>
                        <li>
                            <strong>Non superare i 2 tentativi di rinomina</strong>: dopo il secondo, il nome è definitivo.
                        </li>
                        <li>
                            <strong>Bilancia il team</strong>: <RoleMarker role="Tank" /> + <RoleMarker role="Healer" /> + 3<RoleMarker role="DPS" /> è la composizione 5p standard.
                        </li>
                        <li>
                            <strong>Salva il gold</strong> per i raid: 20 avventurieri costano molto da equipaggiare.
                        </li>
                        <li>
                            <strong>Controlla il max team power</strong> ogni volta che equipaggi nuovo gear:
                            è la metrica che ti porta in classifica.
                        </li>
                        <li>
                            <strong>Esplora i dungeon T1 prima dei T2</strong>: il loot tier-1 sblocca i materiali
                            base che servono al crafting di tier intermedio.
                        </li>
                    </ul>
                </SectionBlock>

                {/* ROUND 12.C — Nuove sezioni Arena/Stagioni */}
                <SectionBlock id="stagioni" title="Stagioni delle Arene">
                    <p>
                        Le <strong>Stagioni</strong> sono cicli competitivi periodici nelle <em>Arene della Gloria</em>.
                        Ogni stagione ha un tema lore (Verglasio, Renovare, Luminara, Crepuscolo, Umbralia o Equilibrio)
                        e una durata definita. Stagione attuale: <strong>Preseason delle Arene</strong>, tema <em>Equilibrio</em>.
                    </p>
                    <p className="mt-2">
                        Al termine, la stagione passa a <em>ended</em> e poi a <em>archived</em>. Il <strong>rating
                        stagionale viene resettato
                                                                                                     </strong> a 1000 all&apos;inizio della stagione successiva, ma:
                    </p>
                    <ul className="list-disc list-inside space-y-1 mt-2 text-[12px]">
                        <li>Gilda, roster, item, oro, reputazione e progressi PVE <strong>NON</strong> vengono toccati.</li>
                        <li>Il <code>highest_league</code> raggiunto resta a vita nel tuo profilo.</li>
                        <li>I reward cosmetici ottenuti restano permanenti.</li>
                        <li>Lo storico match resta consultabile.</li>
                    </ul>
                </SectionBlock>

                <SectionBlock id="leghe" title="Leghe e progressione">
                    <p>
                        Ogni gilda partecipante a una stagione viene assegnata a una <strong>lega</strong> in base
                        al rating Elo. Le leghe sono 7, dalla più bassa alla più alta:
                    </p>
                    <ol className="list-decimal list-inside mt-2 space-y-1 text-[12px]">
                        <li><strong>Unranked</strong> — meno di 5 placement match giocati.</li>
                        <li><strong>Bronzo</strong> — rating 0–999.</li>
                        <li><strong>Argento</strong> — rating 1000–1199.</li>
                        <li><strong>Oro</strong> — rating 1200–1399.</li>
                        <li><strong>Platino</strong> — rating 1400–1599.</li>
                        <li><strong>Diamante</strong> — rating 1600–1799.</li>
                        <li><strong>Maestro</strong> — rating 1800+.</li>
                    </ol>
                    <p className="mt-2">
                        I primi <strong>5 match ranked</strong> sono i <em>placement match</em>: durante questa fase
                        sei &quot;Unranked&quot;. La <strong>highest_league</strong> è la lega più alta che hai mai toccato
                        nella stagione: una volta raggiunta, resta nel tuo profilo anche se cali.
                    </p>
                </SectionBlock>

                <SectionBlock id="arena" title="Arena delle Gilde (PvP)">
                    <p>
                        L&apos;<strong>Arena delle Gilde</strong> è il sistema PvP <strong>asincrono</strong> di Orbus.
                        Le sfide vengono simulate sul server con i nostri RNG crypto-grade; nessuna perdita di
                        oro, item, esperienza o avventurieri è prevista.
                    </p>
                    <h4 className="mt-3 mb-1 text-amber/90 text-[12px] tracking-wider">::: Squadra Difensiva</h4>
                    <p className="text-[12px]">
                        Imposta <strong>5 avventurieri attivi</strong> (Lv 3+ in preview, Lv 5+ in produzione)
                        come difesa permanente. Vengono usati ogni volta che un avversario ti sfida.
                    </p>
                    <h4 className="mt-3 mb-1 text-amber/90 text-[12px] tracking-wider">::: Sfida</h4>
                    <p className="text-[12px]">
                        Scegli 5 avventurieri attaccanti, selezioni un avversario nella tua lega ±1 e confermi.
                        Il server simula 3-5 round e produce un report narrativo IT. L&apos;esito può essere
                        Vittoria / Sconfitta / Pareggio (raro).
                    </p>
                    <h4 className="mt-3 mb-1 text-amber/90 text-[12px] tracking-wider">::: Limiti anti-abuse</h4>
                    <ul className="list-disc list-inside text-[12px] space-y-1">
                        <li><strong>10 sfide ranked al giorno</strong> (reset UTC 00:00).</li>
                        <li><strong>Max 3 sfide / giorno / stesso bersaglio</strong> (cooldown).</li>
                        <li>Le gilde appena create devono superare un&apos;<strong>account age gate</strong> prima di entrare in ranked.</li>
                        <li>Self-challenge bloccato.</li>
                    </ul>
                    <p className="mt-2 text-[12px] text-amber/90 italic">
                        Le squadre vengono <strong>snapshottate</strong> nel match: modifiche successive
                        all&apos;equipaggiamento non riscrivono partite passate.
                    </p>
                </SectionBlock>

                <SectionBlock id="fair-play" title="Fair Play e No P2W">
                    <p>
                        Orbus è <strong>no pay-to-win</strong> nelle Arene per design. In dettaglio:
                    </p>
                    <ul className="list-disc list-inside mt-2 space-y-1 text-[12px]">
                        <li>Nessun acquisto può aumentare rating, power, win rate o accessi giornalieri.</li>
                        <li>I <strong>reward stagionali</strong> sono <strong>esclusivamente cosmetici</strong>:
                            titoli, badge, cornici profilo, banner, icone lega, chat flair, hall of fame.
                        </li>
                        <li>Vietati boost di stat, oro, XP o item competitivi a tempo o premium.</li>
                        <li>Account-age gate, daily cap e cooldown per limitare smurfing e abusi multi-account.</li>
                        <li>La simulazione di combattimento usa RNG crypto-grade (<code>secrets.SystemRandom</code>)
                            non riproducibile lato client: impossibile replay-attack.
                        </li>
                    </ul>
                </SectionBlock>

                <SectionBlock id="lb-stagionale" title="Leaderboard stagionale">
                    <p>
                        Su <code>/leaderboard?scope=season</code> trovi le classifiche dedicate alla stagione attuale:
                    </p>
                    <ul className="list-disc list-inside mt-2 space-y-1 text-[11px]">
                        <li><strong>Arena — Rating</strong>: rating Elo corrente.</li>
                        <li><strong>Arena — Vittorie</strong>: vittorie ranked totali.</li>
                        <li><strong>Arena — Difese vinte</strong>: respinte riuscite quando vieni attaccato.</li>
                        <li><strong>Arena — Win rate</strong>: percentuale W/(W+L+D) con almeno 10 ranked.</li>
                        <li><strong>Picco di Potenza (stagionale)</strong>: massimo team_power raggiunto.</li>
                        <li><strong>Reputazione (stagionale)</strong>: reputazione gilda snapshot.</li>
                    </ul>
                    <p className="mt-2 text-[11px] text-muted-foreground italic">
                        Le entry arena_* mostrano anche il badge della lega per ogni gilda. Le gilde flaggate
                        come test_artifact sono escluse automaticamente.
                    </p>
                </SectionBlock>

                <div className="text-center text-[10px] text-muted-foreground mt-6 italic">
                    Buona avventura, Guild Master. — Orbus Online
                </div>
            </main>
        </div>
    );
}
