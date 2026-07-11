# La Prova del Riflesso Vuoto · R18.6.3-G8 SAFE_MODE_TRIAL

> ⚠️ **DESIGN ONLY · NOT LIVE · NOT IMPLEMENTED**
> Documento di design della **Prova del Riflesso Vuoto**, prova safe-mode del Cacciatore del Vuoto.
> Nessuna implementazione runtime · nessun combat live · nessuna UI · nessun tutorial · nessun record enemy live · nessuna assegnazione classe.

**Sala**: Faro Rovesciato di Onirade · **Hall Master**: Nael di Onirade · **Classe**: Cacciatore del Vuoto
**Stato Sala**: PLANNED · **Stato Prova**: DESIGN ONLY

## 1 · Obiettivo pedagogico

La Prova del Riflesso Vuoto permette alla Recluta di:

- comprendere l'identità della classe **Cacciatore del Vuoto**
- imparare il loop canonico **Identify → Mark → Drain → Payoff**
- generare **Frammenti di Onirade** in scontro
- scegliere consapevolmente **Payoff 3F** (dispel area) o **Payoff 5F** (annullamento summon)
- comprendere **punti di forza** (letture, controlli anti-arcani) e **limiti** (fragilità, non-frontline)
- decidere in modo esplicito se **confermare la classe** o rinunciare

La Prova NON è: dungeon · sfida endgame · test punitivo · fonte farming · verifica equip · gara DPS.

## 2 · Fantasy della Prova

La Prova è un **rito di lettura**. La Recluta entra nel cerchio rituale al centro del Faro Rovesciato, e il Faro proietta manifestazioni controllate del velo che chiedono di essere lette, marchiate e sciolte.

- Fantasy dominante: *"non combatto per vincere, comprendo per decidere"*
- Tono: rituale · misurato · lettura del velo · nessun trionfalismo
- Nael è **presente ma non interviene** nel rito, se non con brevi guide vocali

**NON** è una prova di forza · **NON** è un boss fight · **NON** è una gara.

## 3 · Collocazione rispetto alla Sala

- **Dove**: cerchio rituale al centro della Sala Faro Rovesciato di Onirade (sez 8 · G7)
- **Attivazione**: la Recluta si avvicina al cerchio dopo il dialogo *"Metti i piedi dentro il cerchio"* (G7 sez 29)
- **Instanza**: Prova personale · non condivisa · non PvP · non gruppo
- **Uscita**: al termine, la Recluta ritorna nella Sala (G7 sez 30), non altrove
- **Fuori dalla Sala**: la Prova NON è accessibile da altre location. Non esistono repliche in altri Hall.

## 4 · Ingresso

- La Recluta è già dentro il Faro Rovesciato · dialoghi G7 completati
- Nael pronuncia la linea di transizione (G7 sez 29): *"Metti i piedi dentro il cerchio."*
- La Recluta entra nel cerchio → la Prova inizia
- **NO entry cost** · **NO equip check** · **NO gold check** · **NO material check** · **NO XP check**
- Se la Recluta esita, Nael non insiste. La rinuncia è possibile in ogni momento (sez 43 · 45)

## 5 · Ruolo di Nael durante la Prova

- Nael **osserva** dalla galleria superiore · non entra nel cerchio
- Interviene con **brevi guide vocali** — mai monologhi, mai comandi diretti
- Tono coerente con G7 sez 18-25: asciutto, sereno, osservante, misurato, enigmatico, non ostile
- Nael **NON**: attacca · protegge · risolve al posto della Recluta · giudica in tempo reale · profetizza
- Nael parla **al massimo 1-2 righe per fase** (sez 40)

## 6 · Regole safe-mode

Policy safe-mode LOCK (dispatch PM):

| Parametro | Valore | Note |
|---|---|---|
| `retry_limit` | **unlimited** | La Recluta può riprovare quanto vuole |
| `cooldown` | **0** | Nessuna attesa tra tentativi |
| `death_penalty` | **none** | Nessuna morte permanente |
| `resource_loss` | **none** | Nessuna perdita risorse |
| `rare_resource_cost` | **none** | Nessun consumo risorse rare |
| `entry_cost` | **none** | Ingresso libero |
| `xp_reward` | **0** | Nessun XP |
| `gold_reward` | **0** | Nessun oro |
| `item_reward` | **0** | Nessun item |
| `material_reward` | **0** | Nessun materiale |
| `drop_table` | **assente** | Nessuna drop |
| `achievement_farmabile` | **none** | Nessun achievement farmabile |
| `class_assignment` | **NOT IMPLEMENTED** | Assegnazione runtime deferred |
| `class_slug_apply` | **false** | Design only |

La Prova **non produce alcuna valuta di gioco** e **non registra progressione persistente**.

## 7 · Struttura per fasi

La Prova è organizzata in **9 fasi sequenziali (FASE 0 → FASE 8)**. Ogni fase è didattica, non punitiva.

| Fase | Nome | Focus didattico | Fail-soft |
|---|---|---|---|
| **FASE 0** | Ingresso e orientamento | Riconoscere la Sala, il cerchio, il ruolo di Nael | N/A |
| **FASE 1** | Identify | Riconoscere il bersaglio o fenomeno corretto | Suggerimento di Nael |
| **FASE 2** | Mark | Applicare il Marchio del Vuoto al bersaglio giusto | Reset pacifico, riprova |
| **FASE 3** | Drain | Interagire con il bersaglio Marchiato · generare Frammenti | Reset pacifico, riprova |
| **FASE 4** | Payoff 3F | Comprendere il dispel di un'area arcana | Chiarimento vocale |
| **FASE 5** | Payoff 5F | Comprendere l'annullamento di una summon valida | Chiarimento vocale |
| **FASE 6** | Scenario degradato | Gestire un bersaglio standard senza perdere il loop | Suggerimento se stallo |
| **FASE 7** | Riepilogo di Nael | Sintesi delle scelte fatte · nessun voto numerico | N/A |
| **FASE 8** | Conferma esplicita o rinuncia | Scelta finale: *CONFERMA IL CAMMINO* / *NON SONO PRONTO* | Rinuncia sempre disponibile |

Ogni fase può essere **ripetuta illimitatamente** (sez 29). Nessun timer forzato (sez 35).

## 8 · Identify tutorial (FASE 1)

- La Recluta vede più manifestazioni nel cerchio: alcune arcane, alcune neutre
- **Obiettivo didattico**: distinguere il bersaglio corretto (arcano/velo) da distrattori (neutri)
- Nael guida vocalmente: *"Osserva. Non tutto ciò che si muove va marchiato."*
- Feedback concettuale: quando la Recluta identifica correttamente, l'entità corretta pulsa con la luce discendente del Faro
- **Errore**: nessuna penalità. Reset visivo e nuovo tentativo (sez 27 · 28)

## 9 · Mark tutorial (FASE 2)

- La Recluta applica il **Marchio del Vuoto** al bersaglio identificato
- Feedback concettuale: sul bersaglio Marchiato appare un sigillo silenzioso
- Nael: *"Il Marchio è la porta. Senza Marchio, niente passa."*
- **Errore comune**: marchiare un distrattore neutro → nessun sigillo appare · Nael suggerisce sottovoce di *"guardare meglio"*
- **NO consumo mana** in Prova · **NO cooldown** · **NO limite di applicazioni**

## 10 · Drain tutorial (FASE 3)

- Dopo il Marchio, ogni azione della Recluta contro il bersaglio Marchiato produce un **Frammento di Onirade** che si deposita nel circolo rituale della Recluta
- Nael: *"Ogni colpo che gli assesti lascia un Frammento nel tuo circolo."*
- Feedback concettuale: i Frammenti sono visibili come piccole luci discendenti nel circolo
- La Recluta osserva il conteggio salire (design_only · nessun contatore live implementato)

## 11 · Frammenti tutorial

- I **Frammenti di Onirade** si accumulano **max 5** (loop canonico G3)
- **NON** sono oggetti · **NON** vendibili · **NON** conservabili tra prove
- Nael: *"Cinque, al massimo. Cinque ti costringe a decidere."*
- Se la Recluta tenta di superare 5, i Frammenti in eccesso non si generano (design_only)
- Alla fine della fase, la Recluta ha in circolo 3-5 Frammenti secondo il ritmo scelto

## 12 · Payoff 3F tutorial (FASE 4)

- Con **3 Frammenti**, la Recluta può attivare il **Payoff a 3**: **dispel area arcana**
- Feedback concettuale: un'area intorno alla Recluta si libera dagli effetti arcani (design_only)
- Nael: *"Con tre, dissolvi. Un'area intorno a te si libera dagli effetti arcani."*
- La Prova mostra visivamente il "prima e dopo" concettuale: un'area sfumata torna chiara
- **NO danno numerico** · **NO XP** · **NO ricompensa**

## 13 · Payoff 5F tutorial (FASE 5)

- Con **5 Frammenti**, la Recluta può attivare il **Payoff a 5**: **annullamento di una summon valida** o rimozione di un incorporeo
- Nael: *"Con cinque, bandisci. Un'evocazione nemica scompare. Un incorporeo se ne va."*
- Vincolo canonico: **i boss NON possono essere banditi.** Solo evocazioni non-boss e incorporei.
- Nael ricorda: *"I boss? I boss restano. Non li scacci. Ma le loro evocazioni sì."*

## 14 · Summon valida

- La Prova presenta una **summon simulata** — entità didattica, temporanea, marcata:
  - `trial_only = true`
  - `non_persistent = true`
  - `no_loot = true`
  - `no_xp = true`
  - `not_bestiary_live = true`
- La summon reagisce al Payoff 5F scomparendo (design_only)
- **NON è** un enemy record del bestiario · **NON è** salvato in DB · **NON è** riutilizzato altrove

## 15 · Incorporeo

- La Prova presenta un **incorporeo simulato** — entità didattica, temporanea, con stesse marcature `trial_only / non_persistent / no_loot / no_xp / not_bestiary_live`
- L'incorporeo può essere **bandito** con Payoff 5F
- Feedback concettuale: dissolvenza silenziosa
- **NON** è mai un incorporeo canonico del bestiario di gioco

## 16 · Bersaglio standard

- La Prova presenta un **bersaglio standard** — un fenomeno del velo non-boss, non-summon, non-incorporeo
- Serve a insegnare: *"non tutto va bandito · a volte basta drenare e chiudere"*
- Marcature: `trial_only / non_persistent / no_loot / no_xp / not_bestiary_live`
- **NON** è un enemy live · **NON** ha statistiche di gioco · **NON** appare in altre location

## 17 · Scenario senza bersagli speciali (FASE 6)

- La FASE 6 propone uno scenario **senza summon né incorporei**, solo bersagli standard
- **Obiettivo didattico**: la Recluta impara a **mantenere il loop** anche quando il Payoff massimale non è applicabile
- Nael: *"Non sempre c'è qualcosa da bandire. A volte devi solo leggere e chiudere."*
- La Recluta comprende: **il loop funziona anche senza summon** — 3F resta utile per dispel area

## 18 · Focus tutorial

- **Focus** = arma primaria consigliata (G5 EQUIP · canonico)
- Fantasy: *"la voce che marchia"*
- Feedback concettuale: colpi ampi, letture pulite, generazione Frammenti stabile
- Nael: *"Il Focus è la voce. Inizia da qui."*

## 19 · Balestra tutorial

- **Balestra** = arma di distanza (G5 EQUIP · canonico)
- Fantasy: *"la distanza che protegge"*
- Feedback concettuale: colpi lenti ma sicuri, letture da lontano
- Nael: *"La Balestra è la distanza. Chi la sceglie subito spesso non ha capito."*

## 20 · Pugnale tutorial

- **Pugnale** = arma di chiusura (G5 EQUIP · canonico)
- Fantasy: *"il colpo che chiude"*
- Feedback concettuale: colpi brevi, richiede posizionamento
- Nael: *"Il Pugnale è la chiusura. Serve mano ferma."*

## 21 · Posizionamento

- La Prova insegna: **non stare mai al centro degli scontri** — il Cacciatore del Vuoto legge dai margini
- Feedback concettuale: se la Recluta rimane troppo vicina al bersaglio, la lettura del velo si sfoca
- Nael: *"Non correre. Non stare mai fermo troppo a lungo."*

## 22 · Mobilità

- La Prova insegna: **movimento ritmico**, non frenetico
- Il velo premia chi legge il tempo, non chi corre
- Feedback concettuale: la mobilità è dosata, non atletica

## 23 · Fragilità della classe

- La Prova mostra chiaramente: **stoffa + cuoio non fermano una spada**
- Nella Prova safe-mode, la Recluta **non muore mai**, ma percepisce che una posizione sbagliata la avrebbe messa in difficoltà (feedback concettuale)
- Nael: *"Se ti trovi in mezzo, sei morto. Nella Prova no. Fuori dalla Prova sì."*

## 24 · Warning non-frontline

- Nael avvisa esplicitamente: *"Il Cacciatore del Vuoto non regge la prima linea. Non è debolezza: è specializzazione."*
- La Recluta deve comprendere che questa classe **non è per chi vuole incassare**
- La Prova non nasconde questo limite: lo insegna

## 25 · Errori comuni

- Marchiare distrattori neutri
- Attaccare senza aver Marchiato
- Attivare Payoff 5F su un boss (non funziona)
- Restare troppo vicino al bersaglio
- Cercare DPS massimo invece del loop
- Ignorare la generazione di Frammenti
- Aspettarsi ricompense (non esistono in Prova)

## 26 · Suggerimenti dinamici

- Se la Recluta si ferma **>30 secondi concettuali** senza agire, Nael suggerisce sottovoce
- I suggerimenti sono **brevi**, mai imperativi
- Esempi: *"Guarda meglio"* · *"Prima il Marchio"* · *"Non tutto va marchiato"*
- Nessun timer che chiude la fase automaticamente

## 27 · Fail-soft

- Nessun errore chiude la Prova
- Nessuna azione sbagliata produce danni permanenti
- Ogni errore è **recuperabile immediatamente**
- Il termine "fallimento" **non esiste** in Prova · esiste solo "riprova"

## 28 · Reset rapido

- La Recluta può richiedere un **reset rapido** in ogni momento (interazione col cerchio)
- Il reset riporta la fase corrente allo stato iniziale
- Frammenti in circolo azzerati · summon simulate riemesse · nessun cooldown

## 29 · Retry illimitato

- `retry_limit = unlimited`
- Nessun contatore di tentativi
- Nessuna soglia di tentativi che sblocca/blocca contenuto
- La Recluta può ricominciare la Prova dall'inizio quante volte vuole

## 30 · Zero cooldown

- `cooldown = 0`
- Tra un tentativo e l'altro non c'è attesa
- Tra una fase e l'altra non c'è attesa
- Le azioni della Prova (Mark, Drain, Payoff) non hanno cooldown in Prova (design didattico)

## 31 · Zero reward

- La Prova **non concede**: XP · oro · item · materiali · drop · achievement farmabili · progressione registrata · sblocchi runtime
- L'unica "ricompensa" concettuale è la **comprensione** — pedagogica, non farmabile
- La conferma classe finale (sez 42) **non è** una ricompensa: è una decisione

## 32 · Anti-farming

- Nessuna metrica ripetibile è ottimizzabile
- Nessun contatore che genera bonus a soglie
- Nessuna sessione di Prova può essere sfruttata per farmare risorse (perché **non esistono risorse**)
- Il completamento multiplo della Prova **non produce** vantaggi accumulabili

## 33 · Nessuna morte permanente

- `death_penalty = none`
- La Recluta non muore nella Prova
- Se subisce simulazioni concettuali di danno, il feedback è visivo/didattico, non punitivo
- Nessuna perdita di dati, progressione, item, gold, XP, reputation

## 34 · Nessuna perdita risorse

- `resource_loss = none` · `rare_resource_cost = none`
- Nessun consumo di mana persistente · pozioni · reagenti · risorse rare
- Le "risorse" simulate della Prova (Frammenti) sono **interne al singolo scontro** e non persistono

## 35 · Durata attesa

- Fase per fase: pochi minuti concettuali (indicativi, non-lock)
- Totale Prova completa: **breve** — la Prova non è un dungeon
- Nessun timer forzato · nessuna scadenza · la Recluta può prendersi il tempo che vuole
- Design goal: la Recluta esce con **comprensione**, non con stanchezza

## 36 · Accessibilità

- La Prova è **accessibile a tutte le Recluta** che hanno completato l'ingresso in Sala
- Nessun requisito di livello · nessun equip prerequisito · nessuna dipendenza da altre Sale
- Design goal: la Prova è la **prima esperienza pratica** con la classe

## 37 · Leggibilità UI concettuale

- **UI NON implementata** (Gate 8 = design only)
- Concettualmente: indicatori chiari per Marchio applicato · conteggio Frammenti in circolo · Payoff disponibile 3F/5F · fase corrente
- Nessun HUD complesso · nessuna barra HP · nessuna barra risorsa numerica esposta come progressione persistente
- Design goal: chi legge il velo deve poter leggere anche lo stato della Prova a colpo d'occhio

## 38 · Feedback visivi

- Marchio applicato: sigillo silenzioso sul bersaglio
- Frammento generato: piccola luce discendente che si posa nel circolo
- Payoff 3F: alone chiaro che si espande, poi si contrae
- Payoff 5F: dissolvenza controllata dell'entità target
- Errore: assenza di feedback (nessuna reazione), non lampi punitivi

## 39 · Feedback audio

- Marchio: nota bassa, breve, ferma
- Drain: nota reiterata, pulsante
- Payoff 3F: riverbero ampio, corto
- Payoff 5F: silenzio momentaneo, poi risonanza chiusa
- Nael parla: tono asciutto, volume basso, mai gridato

## 40 · Dialoghi Nael durante la Prova

Nael parla **al massimo 1-2 righe per fase**, coerenti col tono G7:

**FASE 0** · *"Il cerchio è tuo. Non io."*
**FASE 1** · *"Osserva. Non tutto ciò che si muove va marchiato."*
**FASE 2** · *"Il Marchio è la porta. Senza Marchio, niente passa."*
**FASE 3** · *"Ogni colpo che gli assesti lascia un Frammento nel tuo circolo."*
**FASE 4** · *"Con tre, dissolvi. Un'area intorno a te si libera dagli effetti arcani."*
**FASE 5** · *"Con cinque, bandisci un'evocazione. Non il boss stesso."*
**FASE 6** · *"Non sempre c'è qualcosa da bandire. A volte devi solo leggere e chiudere."*
**FASE 7** · *"Hai visto abbastanza. Adesso pensa."*
**FASE 8** · *"Non è una firma di sangue. È una firma di comprensione. Decidi."*

Tono: asciutto · sereno · osservante · misurato · enigmatico · non ostile · **NON** villain · **NON** profeta · **NON** comico · **NON** copia Vessel · **NON** copia Ovyr.

## 41 · Riepilogo finale (FASE 7)

Alla fine, Nael offre un **riepilogo asciutto** delle scelte della Recluta:

- Marchi applicati (correttamente/erroneamente)
- Frammenti generati (ritmo medio)
- Payoff scelti (3F vs 5F, quale preferisci?)
- Posizionamento (dai margini o dal centro?)
- Errori comuni incontrati

Il riepilogo è **descrittivo, non numerico**. Nessun voto. Nessuna classifica. Nessun bonus.

## 42 · Conferma classe post-Prova (FASE 8)

- La Recluta si presenta davanti a Nael dopo il riepilogo
- Nael offre la scelta esplicita (design-only):
  - **CONFERMA IL CAMMINO** → intenzione registrata come *design intent only* · nessuna assegnazione runtime · nessun `class_slug apply` · nessun class unlock · nessuna Hall activation
  - **NON SONO PRONTO** → torno all'Atrio delle Vocazioni · nessuna penalità · nessun consumo
- Nael: *"Non è una firma di sangue. È una firma di comprensione. Decidi."*
- Gate 8: `class_assignment = NOT IMPLEMENTED` · `class_slug_apply = false` · `runtime_assignment = absent`
- La class assignment runtime è **deferred** ai gate tecnici successivi (Gate 9 TECH_READINESS in HOLD)

## 43 · Rinuncia

- La Recluta può rinunciare in **qualsiasi momento**
- Linea di rinuncia (canonica G7 HC-Q6): *"Non tutti leggono il velo. Non è una colpa."*
- Nessuna penalità · nessun consumo · nessun blocco di future visite
- Torno all'Atrio delle Vocazioni

## 44 · Comportamento retry

- Se la Recluta sceglie di ripetere la Prova (dopo rinuncia o dopo conferma):
  - Il progresso concettuale **non è cumulativo** (nessuna scorciatoia)
  - Nael accoglie senza sorpresa: *"Torni. Va bene."*
  - Il flow è identico dalla FASE 0
- **Nessun sblocco progressivo** basato su retry count

## 45 · Comportamento abbandono

- Se la Recluta abbandona la Sala prima della FASE 8:
  - Nessuna assegnazione classe è mai stata tentata (design-only)
  - Nessun record persistente della Prova
  - La Recluta può tornare in seguito attraverso l'Atrio delle Vocazioni
- **Nessun timer** di abbandono forzato

## 46 · Nessuna assegnazione automatica

- **Vincolo canonico G7 HC-Q5 LOCK CRITICAL**: nessuna assegnazione automatica in nessun punto della Prova
- La conferma classe (FASE 8) è **esplicita** · **manuale** · **volontaria**
- Nessuna scelta implicita · nessun timer di conferma · nessuna deriva narrativa che assegni la classe
- In Gate 8: `class_slug apply = false` · `runtime_assignment = absent` · `class_assignment = design_only`

## 47 · Risk register (15 rischi tracciati)

| ID | Rischio | Severity | Status |
|---|---|---|---|
| TR-R1 | Recluta percepisce la Prova come punitiva | MEDIUM | DESIGNED (safe-mode LOCK) |
| TR-R2 | Recluta cerca farm di risorse in Prova | LOW | DESIGNED (anti-farming sez 32) |
| TR-R3 | Retry illimitato genera loop compulsivo | LOW-MEDIUM | DESIGNED (nessun sblocco basato su retry) |
| TR-R4 | Feedback visivi confusi con altri UX di gioco | MEDIUM | DESIGNED (linguaggio visivo Sala-specifico) |
| TR-R5 | Nael troppo distaccato durante la Prova | LOW-MEDIUM | DESIGNED (1-2 righe per fase) |
| TR-R6 | Confusione con dungeon | MEDIUM | DESIGNED (marker + fantasy rituale) |
| TR-R7 | Aspettativa di reward | MEDIUM | DESIGNED (marker "zero reward" comunicato in G6/G7) |
| TR-R8 | Recluta confonde bersagli didattici con bestiario canonico | LOW-MEDIUM | DESIGNED (marker `trial_only`) |
| TR-R9 | Class assignment runtime accidentalmente attivato | LOW | DESIGNED (LOCK CRITICAL HC-Q5) |
| TR-R10 | Payoff 5F applicato a boss senza feedback chiaro | MEDIUM | DESIGNED (Nael avvisa esplicitamente) |
| TR-R11 | Fragilità classe percepita come "bug" invece di feature | LOW-MEDIUM | DESIGNED (Nael la spiega esplicitamente) |
| TR-R12 | Confusione con Prova del Mago | MEDIUM | DESIGNED (fantasy rituale distintivo) |
| TR-R13 | Confusione con Cacciatore di Mostri | MEDIUM | DESIGNED (semantic guard G7 · lore differente) |
| TR-R14 | Frammenti confusi con item inventariabili | LOW | DESIGNED (Nael: *"non sono oggetti"* sez 11) |
| TR-R15 | Recluta si aspetta boss finale | LOW | DESIGNED (fantasy pedagogico, non gara) |

## 48 · PM Open Questions (TR-Q1..TR-Q8)

- **TR-Q1** · *Struttura 9 fasi (FASE 0 → FASE 8) conferma?* → **a) LOCK 9 fasi** · b) collassare FASE 4+5 in un'unica fase · c) altra proposta PM
- **TR-Q2** · *Payoff 5F fallisce su boss con feedback esplicito da Nael (non silenzioso)?* → **a) LOCK feedback esplicito** · b) silenzioso + suggerimento dopo 30s · c) altra proposta PM
- **TR-Q3** · *Suggerimenti dinamici Nael dopo 30s di stallo conferma?* → **a) LOCK 30s** · b) 15s · c) 60s · d) disattivare suggerimenti
- **TR-Q4** · *Entità didattiche marcate `trial_only/non_persistent/no_loot/no_xp/not_bestiary_live` conferma naming?* → **a) LOCK naming attuale** · b) rinomina proposta PM
- **TR-Q5** · *Conferma classe FASE 8 con 2 opzioni "CONFERMA IL CAMMINO" / "NON SONO PRONTO" conferma?* → **a) LOCK 2 opzioni** · b) aggiungere terza opzione "RIPETI LA PROVA" (esplicita)
- **TR-Q6** · *Reset rapido interazione col cerchio conferma?* → **a) LOCK reset rapido** · b) reset solo a fine fase
- **TR-Q7** · *Riepilogo finale descrittivo (nessun voto) conferma?* → **a) LOCK descrittivo** · b) aggiungere metriche non-numeriche (es. "cauto/veloce")
- **TR-Q8** · *Marker `SALA DI DESIGN — NON ANCORA ISTANZIATA IN GIOCO` esteso alla Prova?* → **a) LOCK marker esteso** · b) marker specifico "PROVA DI DESIGN — NON ANCORA ISTANZIATA IN GIOCO"

## 49 · GO/HOLD Recommendation Gate 9 TECH_READINESS

- **Gate 8 status**: DRAFT · pending PM review + risposte TR-Q1..TR-Q8
- **Gate 9 TECH_READINESS status**: 🔒 **HOLD** · attende PM ACK Gate 8 + GO esplicito
- **Gate 9 scope preview**: definizione dei requisiti tecnici runtime (endpoint API, schema DB, flow di attivazione, class_slug apply, Hall activation, bridge apply) per la Sala + la Prova. **Nessuna implementazione** in Gate 9: solo specifica tecnica preparatoria.
- **NO Gate 9 auto-start** · **NO Wave 1 auto-start** · **NO class unlock auto-start** · **NO Hall activation auto-start**
- **Recommended next step**: PM review G8 SAFE_MODE_TRIAL + risposte TR-Q1..TR-Q8 → G8 CLOSED verdict → GO Gate 9 TECH_READINESS

---

## 🛑 STOP obbligatorio a fine G8 · Non procedere a Gate 9 senza nuovo GO PM

> ⚠️ **PROVA DI DESIGN — NON ANCORA ISTANZIATA IN GIOCO**
> Questa documentazione descrive il design della **Prova del Riflesso Vuoto**. La Prova **non è ancora istanziata runtime**. Nessun combat live · nessun enemy record live · nessun bestiario · nessun XP · nessun oro · nessun item · nessuna assegnazione classe.

Attendo PM review Gate 8 SAFE_MODE_TRIAL + risposte a **TR-Q1..TR-Q8**. Nessun auto-start Gate 9 · Nessun auto-start Wave 1 successors · Nessuna modifica R18.5/R18.6/R18.6.1/R18.6.2/G1/G2/G3/G4/G5/RV3/G6/G7 (tutti LOCKED).
