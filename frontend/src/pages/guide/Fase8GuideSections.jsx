// FASE 8E (2026-08-08) — Sezioni Guida: le meccaniche dell'era attuale.
//
// Documenta in un unico blocco tutti i sistemi introdotti/riformati
// nelle tranche Fasi 1-8: PWR e Rating, curva di successo, Overpower,
// gate a potere (dungeon 70% / raid 75%), dungeon a stanze e bivi,
// riposo/fuga, reagenti per dungeon, professioni (Fucina/Cucina/
// Alchimia), consumabili e Pietra della Conoscenza, catch-up XP,
// avatar, raid a fasi, sblocco progressivo dei contenuti.
import { SectionBlock } from "./_shared";

export const FASE8_SECTIONS = [
    { id: "pwr-e-probabilita", label: "★ Potere, Rating e probabilità" },
    { id: "overpower", label: "★ Overpower: più forza, più bottino" },
    { id: "dungeon-a-stanze", label: "★ Dungeon a stanze e bivi" },
    { id: "raid-a-fasi", label: "★ Raid a fasi e checkpoint" },
    { id: "reagenti-e-professioni", label: "★ Reagenti, Cucina e Alchimia" },
    { id: "consumabili-e-pietra", label: "★ Consumabili e Pietra della Conoscenza" },
    { id: "catchup-e-avatar", label: "★ Recupero XP e ritratti" },
];

export default function Fase8GuideSections() {
    return (
        <>
            <SectionBlock id="pwr-e-probabilita" title="★ Potere, Rating e probabilità di successo">
                <p>
                    Ogni avventuriero ha un <strong>potere</strong> (PWR): statistiche + livello +
                    equipaggiamento + effetti degli oggetti. Il <strong>potere di squadra</strong> è la
                    somma dei membri più i bonus di ruolo (Tank/Guaritore/Attaccante presenti: fino a +25).
                </p>
                <p className="mt-2">
                    Confrontando il potere di squadra col <strong>potere consigliato</strong> del contenuto
                    ottieni il <strong>Rating di Potenza</strong>: 100% = parità. La probabilità di successo
                    segue una curva morbida:
                </p>
                <ul className="list-disc list-inside mt-2 space-y-1">
                    <li>Rating 75% → ~20% di successo (molto rischioso)</li>
                    <li>Rating 100% → <strong>50%</strong> (parità)</li>
                    <li>Rating 125% → ~80% (ben equipaggiati)</li>
                    <li>Rating 150% → ~94%</li>
                    <li>Rating 200%+ → <strong>100% garantito</strong></li>
                </ul>
                <p className="mt-2">
                    <strong>Accesso</strong>: per entrare in un dungeon serve almeno il <strong>70%</strong> del
                    potere consigliato (nei raid il <strong>75%</strong> del potere combinato). Il livello indicato
                    è una fascia consigliata, mai un blocco: conta solo il potere reale.
                </p>
            </SectionBlock>

            <SectionBlock id="overpower" title="★ Overpower: più forza, più bottino">
                <p>
                    Superato il 100% di Rating la vittoria è sempre più sicura — e l&apos;eccedenza diventa
                    <strong> bottino</strong>: ogni 25 punti di Rating oltre 100 aumenta gli oggetti e i
                    materiali trovati.
                </p>
                <ul className="list-disc list-inside mt-2 space-y-1">
                    <li>Rating 125–149% → bottino ×1.5</li>
                    <li>Rating 150–174% → ×2.0</li>
                    <li>Rating 175–199% → ×2.5</li>
                    <li>Rating 200%+ → <strong>×3.0</strong> (massimo)</li>
                </ul>
                <p className="mt-2">
                    È il motivo per cui <strong>rifare i dungeon vecchi conviene</strong>: una squadra di
                    fine gioco su un dungeon di fascia bassa va dritta a ×3.0 ed è la farm ufficiale dei
                    reagenti comuni. Oro ed esperienza non vengono moltiplicati.
                </p>
            </SectionBlock>

            <SectionBlock id="dungeon-a-stanze" title="★ Dungeon a stanze e bivi">
                <p>
                    I dungeon non sono più un blocco unico: si avanzano <strong>stanza per stanza</strong>,
                    ognuna col suo tempo, la sua probabilità (le stanze del boss sono più dure, le insidie
                    ambientali più morbide) e il suo bottino, che resta <em>in spalla</em> fino all&apos;uscita.
                </p>
                <p className="mt-2">Dopo ogni stanza superata scegli:</p>
                <ul className="list-disc list-inside mt-2 space-y-1">
                    <li><strong>Prosegui</strong> — avanti alla prossima stanza;</li>
                    <li><strong>Riposa e prosegui</strong> — +8% alla prossima stanza, ma +25% di tempo;</li>
                    <li><strong>Fuggi</strong> — porti in salvo il <strong>50% dell&apos;oro</strong> e ogni oggetto
                        al 50% (selezione casuale), ma l&apos;esperienza dell&apos;impresa incompiuta va perduta
                        (ne incassi metà, senza bonus).</li>
                </ul>
                <p className="mt-2">
                    Alcuni dungeon hanno <strong>bivi</strong>: una via prudente (+5 alla riuscita) contro una
                    via ricca (−8/−10 ma stanza del tesoro o boss opzionale). Al bivio decidi tu — e se non
                    decidi entro 24 ore, il gruppo prende la via prudente da solo.
                </p>
                <p className="mt-2">
                    <strong>Completare conta</strong>: solo a dungeon finito incassi il 100% del bottino con un
                    <strong> +25% di esperienza</strong>, il reagente del dungeon, l&apos;eventuale Pietra della
                    Conoscenza e i moltiplicatori Overpower. Se il gruppo viene travolto in una stanza, si
                    ritira col 25% del bottino e il 40% dell&apos;esperienza maturata. Mentre è nel dungeon,
                    il gruppo è impegnato e non può fare altro.
                </p>
            </SectionBlock>

            <SectionBlock id="raid-a-fasi" title="★ Raid a fasi e checkpoint">
                <p>
                    Un raid non è un dungeon più grosso: è un&apos;impresa in più <strong>fasi</strong> — avvicinamento,
                    <strong> boss intermedi</strong>, eventi, e il boss finale. La <em>Veglia di Lunacaduta</em> è il
                    primo raid col nuovo sistema.
                </p>
                <ul className="list-disc list-inside mt-2 space-y-1">
                    <li>Le fasi avanzano col timer: risolta una fase, parte la successiva.</li>
                    <li>Al <strong>checkpoint</strong> scegli: il <em>Rituale di Purificazione</em> (+5 alle fasi
                        restanti) o l&apos;<em>Assalto Diretto</em> (−8, ma +25% oro).</li>
                    <li>Cadere <strong>prima</strong> del checkpoint è una sconfitta; cadere <strong>dopo</strong> vale
                        comunque una vittoria parziale: il checkpoint è un vero traguardo.</li>
                </ul>
                <p className="mt-2">
                    L&apos;accesso è a <strong>potere combinato</strong> (75% del consigliato) e i raid restano i
                    contenuti più severi del gioco — con le ricompense più alte e i reagenti esclusivi.
                </p>
            </SectionBlock>

            <SectionBlock id="reagenti-e-professioni" title="★ Reagenti, Cucina e Alchimia">
                <p>
                    Ogni dungeon ha <strong>UN reagente principale</strong> coerente con la sua lore (le Ossa
                    Antiche dal Santuario del Lich, la Scaglia di Drago dal Tesoro del Drago…): «dove trovo X?»
                    ha sempre una risposta. I reagenti più rari — Polvere di Luna, Nucleo d&apos;Assedio,
                    Rintocco Spettrale, Essenza di Drago — cadono <strong>solo nei raid</strong>, garantiti a vittoria.
                </p>
                <p className="mt-2">
                    I Laboratori di Gilda hanno tre professioni:
                </p>
                <ul className="list-disc list-inside mt-2 space-y-1">
                    <li><strong>⚒ Fucina</strong> — armi, armature e accessori;</li>
                    <li><strong>🍲 Cucina</strong> — cibi che danno potere per le prossime spedizioni
                        (Stufato del Viandante, Banchetto dell&apos;Eroe);</li>
                    <li><strong>⚗ Alchimia</strong> — elisir e tonici, anche di esperienza
                        (il Tonico del Sapiente richiede Polvere di Luna: i raid contano).</li>
                </ul>
            </SectionBlock>

            <SectionBlock id="consumabili-e-pietra" title="★ Consumabili e Pietra della Conoscenza">
                <p>
                    Ogni avventuriero ha uno <strong>scomparto Consumabile</strong>: un solo oggetto attivo alla
                    volta, assegnato dal Deposito («Usa su…»). I <em>power</em> aggiungono potere alla partenza
                    (contano per Rating, probabilità e accesso!), gli <em>XP</em> moltiplicano l&apos;esperienza a fine
                    spedizione. Ogni spedizione completata consuma una carica; il buff si può annullare dalla
                    scheda dell&apos;avventuriero (senza rimborso).
                </p>
                <p className="mt-2">
                    La <strong>Pietra della Conoscenza</strong> cade dai dungeon completati (~1 su 5): data a un
                    avventuriero, gli garantisce <strong>+50% di esperienza per 5 spedizioni</strong>. Perfetta per
                    far crescere le nuove leve.
                </p>
            </SectionBlock>

            <SectionBlock id="catchup-e-avatar" title="★ Recupero XP, ritratti e sblocco dei contenuti">
                <p>
                    <strong>Recupero di gilda</strong>: quando i tuoi 5 avventurieri più forti hanno raggiunto il
                    livello 10, tutti quelli sotto il 10 guadagnano <strong>+25% di esperienza</strong> — le nuove
                    leve inseguono i campioni.
                </p>
                <p className="mt-2">
                    <strong>Ritratti</strong>: ogni avventuriero ha un ritratto della sua razza (maschile o
                    femminile). Dalla sua scheda puoi caricare un&apos;immagine dal tuo PC (PNG/JPEG/WEBP, max
                    2 MB) o tornare al ritratto razziale in qualsiasi momento.
                </p>
                <p className="mt-2">
                    <strong>Sblocco progressivo</strong>: dungeon e raid futuri restano nascosti — vedi i contenuti
                    sbloccati più la <em>prossima sfida</em>. Supera quella per svelare il resto del mondo.
                </p>
            </SectionBlock>
        </>
    );
}
