// ROUND 15 — Fase 4 / Task 13 — Player-facing Guida sections introduced
// by Round 15. Renders 4 new SectionBlocks: equip compatibility, XP debuff,
// material drop, guild level + Imprese.
//
// Keeps all Italian copy here so future translation/edits are localised.

import { SectionBlock } from "./_shared";

const ListItem = ({ children }) => (
    <li className="ml-5 list-disc text-foreground/90">{children}</li>
);

function EquipCompatSection() {
    return (
        <SectionBlock id="equip-compat" title="34. Equipaggiamento per classe">
            <p className="mb-3">
                Ogni oggetto ha dei <strong>tag</strong> (es. arma a due mani,
                armatura pesante, focus arcano) che determinano se è
                <strong> compatibile</strong> con la classe di un avventuriero.
                Il controllo viene fatto al momento dell&apos;equip.
            </p>

            <div className="text-[11px] text-amber tracking-widest mt-4 mb-2">
                :: ARMI
            </div>
            <ul className="space-y-1 mb-4">
                <ListItem><strong>Spade/Asce a 2 mani:</strong> consigliate a Guerriero, Berserker, Paladino.</ListItem>
                <ListItem><strong>Pugnali / armi finesse:</strong> consigliate a Ladro, Assassino, Ranger.</ListItem>
                <ListItem><strong>Archi / armi a distanza:</strong> consigliate a Ranger.</ListItem>
                <ListItem><strong>Bastoni / Bacchette / Grimori (arcani):</strong> riservati a classi caster (Mago, Negromante, Druido, Sacerdote, Bardo). <em>Hard block</em> per Guerriero, Berserker, Paladino, Ladro, Assassino, Ranger, Monaco.</ListItem>
                <ListItem><strong>Mazze sacre / Scettri:</strong> consigliati a Sacerdote, Paladino.</ListItem>
            </ul>

            <div className="text-[11px] text-amber tracking-widest mt-4 mb-2">
                :: ARMATURE
            </div>
            <ul className="space-y-1 mb-4">
                <ListItem><strong>Pesante (piastre / cotta):</strong> Guerriero, Paladino, Berserker. <em>Hard block</em> per Mago, Negromante, Sacerdote, Druido, Bardo: la mobilità e la canalizzazione magica vengono compromesse.</ListItem>
                <ListItem><strong>Media (cuoio borchiato, scaglie leggere):</strong> Ranger, Ladro, Paladino, Bardo.</ListItem>
                <ListItem><strong>Leggera (cuoio, padded):</strong> Ladro, Assassino, Ranger, Monaco.</ListItem>
                <ListItem><strong>Vestaglie / cloth:</strong> Mago, Negromante, Sacerdote, Druido.</ListItem>
                <ListItem><strong>Universali (accessori):</strong> equipaggiabili da chiunque, nessun avviso.</ListItem>
            </ul>

            <div className="text-[11px] text-amber tracking-widest mt-4 mb-2">
                :: COSA SUCCEDE SE EQUIPAGGIO UN ITEM NON COMPATIBILE
            </div>
            <ul className="space-y-1">
                <ListItem><strong className="text-red-400">HARD BLOCK</strong>: l&apos;item NON viene equipaggiato, viene mostrato un avviso in italiano (es. <em>&quot;Questa classe non può indossare armatura pesante&quot;</em>). L&apos;item resta nell&apos;inventario, puoi assegnarlo a un altro avventuriero compatibile.</ListItem>
                <ListItem><strong className="text-amber">WARNING (efficiency)</strong>: l&apos;item si equipaggia ma viene mostrato l&apos;avviso <em>&quot;Equipaggiabile ma poco efficiente per questa classe&quot;</em>. I bonus dell&apos;item esistono, ma non sono allineati alla statistica primaria della classe.</ListItem>
                <ListItem><strong className="text-emerald-300">OK</strong>: nessun avviso. La classe sfrutta al meglio i bonus.</ListItem>
            </ul>
            <p className="text-[11px] text-muted-foreground mt-3 italic">
                Nessun item viene mai cancellato. Gli item legacy incompatibili
                sono stati riposti nell&apos;inventario automaticamente dal
                sistema durante l&apos;aggiornamento Round 15.
            </p>
        </SectionBlock>
    );
}

function XpDebuffSection() {
    return (
        <SectionBlock id="xp-primary-stat" title="35. XP e statistica primaria">
            <p className="mb-3">
                Ogni classe ha una <strong>statistica primaria</strong> (Forza
                per il Guerriero, Intelletto per il Mago, ecc.). Se la statistica
                primaria di un avventuriero è troppo bassa per il suo livello,
                l&apos;XP che guadagna in spedizione viene ridotta.
            </p>
            <div className="text-[11px] text-amber tracking-widest mt-3 mb-2">
                :: FORMULA
            </div>
            <p className="mb-2">
                Soglia attesa: ogni livello richiede una statistica primaria
                leggermente più alta della precedente (la crescita è dolce ed
                è gestita dal sistema).
            </p>
            <ul className="space-y-1 mb-4">
                <ListItem>Statistica ok o margine fino a −10%: nessun debuff (XP intera).</ListItem>
                <ListItem>−10% / −20% sotto soglia: <strong>−10% XP</strong> (multiplier 0.90).</ListItem>
                <ListItem>−20% / −30% sotto soglia: <strong>−20% XP</strong> (multiplier 0.80).</ListItem>
                <ListItem>≥ −30% sotto soglia: <strong>−30% XP</strong> (multiplier 0.70). Cap floor: l&apos;XP non scende mai sotto il 70%.</ListItem>
            </ul>
            <div className="text-[11px] text-amber tracking-widest mt-3 mb-2">
                :: ESEMPIO
            </div>
            <p className="mb-2">
                <em>Mago Lv8 con Intelletto = 11 invece di 14</em> → −20% XP
                nelle spedizioni (deficit ~21%). Come migliorare:
            </p>
            <ul className="space-y-1 mb-3">
                <ListItem>Equipaggia oggetti che danno bonus Intelletto.</ListItem>
                <ListItem>Fai salire il livello (in modo che il base stat cresca con la classe).</ListItem>
                <ListItem>Cerca tratti che aumentano la statistica primaria.</ListItem>
            </ul>
            <p className="text-[12px] text-muted-foreground italic">
                Il debuff NON si applica al PvP (Elo invariato) né
                all&apos;XP di gilda guadagnata dalle Imprese (vedi sezione 37).
                È pensato per spingerti a costruire team coerenti, non per
                punire la sperimentazione.
            </p>
        </SectionBlock>
    );
}

function MaterialDropSection() {
    return (
        <SectionBlock id="drop-materiali" title="36. Drop materiali in spedizione">
            <p className="mb-3">
                I materiali ora possono droppare anche dalle spedizioni, con un
                <strong> roll separato</strong> rispetto agli item: una run può
                produrre solo un item, solo materiali, entrambi, o nessuno dei due.
            </p>
            <div className="text-[11px] text-amber tracking-widest mt-3 mb-2">
                :: COSA È CAMBIATO
            </div>
            <ul className="space-y-1 mb-3">
                <ListItem><strong>Drop rate +70%</strong> rispetto alla baseline pre-Round 15.</ListItem>
                <ListItem>Cap per rarità rispettato: Comune ≤ 85%, Non comune ≤ 55%, Raro ≤ 25%, Epico ≤ 15%.</ListItem>
                <ListItem>Materiali essenziali (Iron Shard, Raw Leather, Healing Herb) hanno un floor minimo del 17% in T1.</ListItem>
                <ListItem>In caso di fallimento della spedizione, il drop rate dei materiali è dimezzato (consolation drop, mai zero garantito).</ListItem>
            </ul>
            <p className="text-[12px] text-muted-foreground italic">
                I rate sono fissi data-driven, non aumentano con acquisti reali
                né con boost a pagamento. Nessun exploit, nessun paywall.
            </p>
        </SectionBlock>
    );
}

function GuildLevelSection() {
    return (
        <SectionBlock id="guild-level" title="37. Livello Gilda">
            <p className="mb-3">
                La tua gilda guadagna <strong>XP Gilda</strong> completando
                <strong> Imprese di Gilda</strong> (vedi sezione 38). Più Imprese
                completi, più sale il <strong>Livello Gilda</strong>.
            </p>
            <div className="text-[11px] text-amber tracking-widest mt-3 mb-2">
                :: CHECKPOINT CURVA (cumulativi)
            </div>
            <ul className="space-y-1 mb-3 text-[12px]">
                <ListItem>Lv 1 → 0 XP</ListItem>
                <ListItem>Lv 2 → 100 XP</ListItem>
                <ListItem>Lv 5 → 900 XP</ListItem>
                <ListItem>Lv 10 → 5.000 XP</ListItem>
                <ListItem>Lv 20 → ~25.000 XP</ListItem>
                <ListItem>Lv 30 → ~79.000 XP</ListItem>
                <ListItem>Lv 50 → ~300.000 XP</ListItem>
            </ul>
            <div className="text-[11px] text-amber tracking-widest mt-3 mb-2">
                :: COSA SBLOCCA
            </div>
            <ul className="space-y-1 mb-3">
                <ListItem>Titoli cosmetici (es. <em>&quot;Il Primo Passo&quot;</em>, <em>&quot;Vetta di Orbus&quot;</em>).</ListItem>
                <ListItem>Badge ed emblemi profilo.</ListItem>
                <ListItem>Cornici profilo speciali.</ListItem>
                <ListItem>Future QoL non competitive.</ListItem>
            </ul>
            <div className="text-[11px] text-red-400 tracking-widest mt-3 mb-2">
                :: NIENTE PAY-TO-WIN
            </div>
            <p className="text-[12px]">
                Il Livello Gilda <strong>non si compra</strong> e
                <strong> non si accelera</strong> con soldi reali. Non dà mai
                potere combat, bonus economici, vantaggi in leaderboard o in PvP.
                È puramente prestigio + cosmetica.
            </p>
        </SectionBlock>
    );
}

function ImpreseSection() {
    return (
        <SectionBlock id="imprese-gilda" title="38. Imprese di Gilda">
            <p className="mb-3">
                Le Imprese sono obiettivi a lungo termine che premiano la tua
                gilda con XP Gilda, punti Imprese e ricompense cosmetiche.
                Trovi la lista completa su{" "}
                <a href="/achievements" data-testid="guide-link-achievements" className="text-amber hover:underline">
                    /achievements
                </a>.
            </p>

            <div className="text-[11px] text-amber tracking-widest mt-3 mb-2">
                :: LE 14 CATEGORIE
            </div>
            <ul className="space-y-1 mb-4 text-[12px]">
                <ListItem><strong>Primi Passi</strong> — Tutorial e prime volte.</ListItem>
                <ListItem><strong>Roster</strong> — Reclutamenti totali.</ListItem>
                <ListItem><strong>Dungeon</strong> — Spedizioni completate.</ListItem>
                <ListItem><strong>Raid</strong> — Raid completati.</ListItem>
                <ListItem><strong>Equipaggiamento</strong> — Oggetti equipaggiati.</ListItem>
                <ListItem><strong>Classi e Statistiche</strong> — Specializzazione delle classi.</ListItem>
                <ListItem><strong>Territorio</strong> — Edifici potenziati.</ListItem>
                <ListItem><strong>Fucina</strong> — Oggetti forgiati e disenchant.</ListItem>
                <ListItem><strong>Economia</strong> — Mercato e Asta.</ListItem>
                <ListItem><strong>PvP / Stagioni</strong> — Partite e leghe.</ListItem>
                <ListItem><strong>Leaderboard</strong> — Posizioni in classifica (cosmetic-only).</ListItem>
                <ListItem><strong>Consorzi</strong> — Membri attivi.</ListItem>
                <ListItem><strong>Lore &amp; Esplorazione</strong> — Riferimenti narrativi (Irthe, Ergolat, Alevora).</ListItem>
                <ListItem><strong>Segrete</strong> — Imprese nascoste, si rivelano solo al completamento.</ListItem>
            </ul>

            <div className="text-[11px] text-amber tracking-widest mt-3 mb-2">
                :: REGOLE
            </div>
            <ul className="space-y-1 mb-3">
                <ListItem>Le ricompense sono <strong>solo cosmetiche</strong>: titolo, badge, cornice. Mai oro, mai item gameplay, mai boost.</ListItem>
                <ListItem><strong>Idempotenti</strong>: ogni Impresa dà XP e punti una volta sola.</ListItem>
                <ListItem>Le Imprese <strong>segrete</strong> non vengono mostrate nella vista &quot;in corso&quot; — diventano visibili solo dopo essere state completate.</ListItem>
                <ListItem>I grant di un admin (eventi, supporto) <strong>non</strong> contano per le Imprese del giocatore.</ListItem>
            </ul>

            <div className="text-[11px] text-amber tracking-widest mt-3 mb-2">
                :: ESEMPI (non-segrete)
            </div>
            <ul className="space-y-1 text-[12px]">
                <ListItem><em>Il Primo Passo</em> → crea la tua prima gilda. Reward: titolo &quot;Il Primo Passo&quot;.</ListItem>
                <ListItem><em>Cento Reclute</em> → recluta 100 avventurieri.</ListItem>
                <ListItem><em>Vetta di Orbus</em> → raggiungi la vetta di una classifica pubblica. Reward: titolo &quot;Vetta di Orbus&quot;.</ListItem>
                <ListItem><em>Veterano dei Raid</em> → completa 20 raid. Reward: cornice profilo.</ListItem>
                <ListItem><em>Erede di Irthe</em> → completa la prima spedizione in territorio di Irthe. Reward: titolo &quot;Erede di Irthe&quot;.</ListItem>
            </ul>
        </SectionBlock>
    );
}

export default function R15GuideSections() {
    return (
        <>
            <EquipCompatSection />
            <XpDebuffSection />
            <MaterialDropSection />
            <GuildLevelSection />
            <ImpreseSection />
        </>
    );
}
