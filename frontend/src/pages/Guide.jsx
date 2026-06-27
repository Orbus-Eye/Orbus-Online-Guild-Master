// Phase 19.2 — P2.2 Player Guide in-game.
// Single-page guide with anchor-link tabs. Italian-first.
// Pure text + tables; no images. Dark/minimal aesthetic to match the rest of the UI.
import { useState } from "react";
import AppHeader from "../components/AppHeader";
import RoleMarker from "../components/RoleMarker";

const SECTIONS = [
    { id: "intro", label: "1. Introduzione" },
    { id: "gilda", label: "2. Gilda e progressione" },
    { id: "ruoli", label: "3. Avventurieri e ruoli" },
    { id: "dungeon", label: "4. Dungeon / Spedizioni" },
    { id: "raid", label: "5. Raid" },
    { id: "forge", label: "6. Equipaggiamento e Forge" },
    { id: "vault", label: "7. Deposito / Inventario" },
    { id: "market", label: "8. Mercato e Crafting" },
    { id: "quest", label: "9. Quest e Streak" },
    { id: "consortium", label: "10. Cronaca e Consorzi" },
    { id: "tips", label: "11. Suggerimenti base" },
];

const SectionBlock = ({ id, title, children }) => (
    <section
        id={id}
        data-testid={`guide-section-${id}`}
        className="border border-border bg-card rounded-sm p-5 mb-4 scroll-mt-24"
    >
        <h2 className="text-sm tracking-[0.3em] text-amber mb-3">:: {title}</h2>
        <div className="prose prose-invert prose-sm max-w-none text-[13px] leading-relaxed text-foreground/90">
            {children}
        </div>
    </section>
);

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

                <SectionBlock id="ruoli" title="Avventurieri e ruoli">
                    <p>
                        Ogni avventuriero ha una classe e un ruolo. I ruoli sono prefissati con un marker ASCII
                        in tutte le liste per leggere a colpo d&apos;occhio:
                    </p>
                    <ul className="mt-2 space-y-1">
                        <li><RoleMarker role="Tank" withLabel /> — assorbe danni</li>
                        <li><RoleMarker role="Healer" withLabel /> — cura il gruppo</li>
                        <li><RoleMarker role="DPS" withLabel /> — danno principale</li>
                        <li><RoleMarker role="Ranger" withLabel /> — danno a distanza / utility</li>
                    </ul>
                    <p className="mt-2">
                        Statistiche: <strong>STR</strong> (forza), <strong>AGI</strong> (agilità),
                        <strong> INT</strong> (intelletto), <strong>END</strong> (endurance),
                        <strong> FAI</strong> (fede). Influenzano il <em>power</em> totale dell&apos;avventuriero.
                    </p>
                    <p className="mt-2">
                        <strong>Tratti</strong>: ogni avventuriero ha 0-3 tratti che modificano le statistiche
                        in modo permanente. I tratti possono essere positivi, negativi o misti.
                    </p>
                    <p className="mt-2">
                        <strong>Rinomina</strong>: puoi rinominare ogni avventuriero fino a <strong>2 volte
                        nella sua vita</strong> (rinomina gratuita, no oro). Dopo 2 rinomine il nome è definitivo.
                    </p>
                </SectionBlock>

                <SectionBlock id="dungeon" title="Dungeon / Spedizioni">
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
                </SectionBlock>

                <SectionBlock id="forge" title="Equipaggiamento e Forge">
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
                </SectionBlock>

                <SectionBlock id="vault" title="Deposito / Inventario">
                    <p>
                        Il <strong>Deposito (Guild Vault)</strong> raccoglie tutti gli oggetti trovati nelle spedizioni.
                        Gli stack mostrano sia copie equipaggiate sia disponibili.
                    </p>
                    <p className="mt-2">
                        Puoi filtrare per tipo (weapon / armor / accessory / consumable / material) o per rarità.
                        Oggetti marcati ⚒ sono usati come <em>materiali di crafting</em>.
                    </p>
                </SectionBlock>

                <SectionBlock id="market" title="Mercato e Crafting">
                    <p>
                        Il <strong>Mercato</strong> ti permette di mettere in vendita oggetti del deposito a prezzo fisso
                        (in gold). Altri giocatori possono acquistarli. Tassa di transazione: 5%.
                    </p>
                    <p className="mt-2">
                        Il <strong>Crafting (Forgia)</strong> consuma materiali per produrre oggetti tier intermedio.
                        Le ricette sono visibili nella pagina dedicata e hanno costi in oro + materiali specifici.
                    </p>
                </SectionBlock>

                <SectionBlock id="quest" title="Quest e Streak">
                    <p>
                        <strong>Quest giornaliere</strong>: 3 obiettivi rapidi che si resettano ogni 24h
                        (es. <em>completa 1 spedizione</em>, <em>recluta 1 avventuriero</em>).
                        Reward: gold + materiali.
                    </p>
                    <p className="mt-2">
                        <strong>Quest settimanali</strong>: 4 obiettivi medio-lunghi (1 settimana).
                        Includono obiettivi raid e mercato. Reward più consistenti.
                    </p>
                    <p className="mt-2">
                        <strong>Streak</strong>: completare almeno una quest al giorno mantiene la serie attiva.
                        Streak D3 / D5 / D7 sbloccano bonus crescenti.
                    </p>
                </SectionBlock>

                <SectionBlock id="consortium" title="Cronaca e Consorzi">
                    <p>
                        La <strong>Cronaca (Server Chronicle)</strong> mostra gli eventi recenti dei giocatori
                        sul server: spedizioni completate, oggetti epici trovati, raid vinti.
                    </p>
                    <p className="mt-2">
                        I <strong>Consorzi</strong> sono gruppi cooperativi tra gilde: condividi un buff settimanale
                        e un canale di comunicazione testuale. Ogni gilda può appartenere a un consorzio alla volta.
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

                <div className="text-center text-[10px] text-muted-foreground mt-6 italic">
                    Buona avventura, Guild Master. — Orbus Online
                </div>
            </main>
        </div>
    );
}
