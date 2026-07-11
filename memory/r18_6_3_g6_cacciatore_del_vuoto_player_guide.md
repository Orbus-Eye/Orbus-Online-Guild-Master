# Cacciatore del Vuoto · Guida di classe

> ⚠️ **GUIDA DI DESIGN — CLASSE NON ANCORA DISPONIBILE**
> Questa guida descrive il design del **Cacciatore del Vuoto**. La classe **non è ancora disponibile in gioco**, non è selezionabile, e non è ancora testabile.
> Contenuto pensato per allineare team di design e futuri playtester. Nessuna funzionalità qui descritta è attualmente live.

**Gate**: R18.6.3-G6 · **Scope**: PLAYER_GUIDE · **Classe pilota**: Cacciatore del Vuoto
**Data generazione**: 2026-07-08T22:15:00Z · **Stato**: DRAFT · in attesa di revisione PM · **Lingua**: italiano
**Governance**: DOCUMENTAL ONLY · nessun codice · nessuna implementazione tutorial/UI · sigilli 36 intatti · `lore_meta.py` invariato

---

## 1 · Nome della classe

**Cacciatore del Vuoto**

## 2 · Descrizione breve

Rituale specializzato nell'identificare, marchiare e annullare evocazioni, entità incorporee e distorsioni arcane. Non un mago da battaglia diretta: un cacciatore paziente che accumula progresso rituale (i **Frammenti di Onirade**) e lo spende in momenti decisivi.

## 3 · Fantasy della classe

Il Cacciatore del Vuoto pattuglia il velo tra i mondi. Riconosce le forme che gli altri non vedono, marchia il loro passaggio, e le annulla prima che possano radicarsi. È un rituale in movimento: legge il vuoto, lo interroga, lo dissolve. La sua identità è **anti-arcano** ma non anti-magia: la sua magia è di **controllo, silenziamento, cancellazione**.

## 4 · Ruolo nel gruppo

- **Ruolo**: DPS specialistico anti-evocazione · anti-incorporeo · anti-distorsione arcana
- **Posizionamento**: media distanza · dietro la prima linea · davanti ai supporti puri
- **Priorità bersagli**: evocazioni > incorporei > castatori nemici > mischia

## 5 · Statistica principale (main stat)

**Intelligenza**

## 6 · Priorità statistiche

1. **Intelligenza** — primaria · scala tutti gli aspetti rituali (generazione Frammenti, durata Marchio, affidabilità dei Payoff)
2. **Costituzione** — secondaria · sopravvivenza (armature leggere = fragile per definizione)
3. **Destrezza** — terziaria · movimento e posizionamento

**Nota Saggezza**: NON è statistica offensiva per il Cacciatore del Vuoto. Non aumenta né la generazione dei Frammenti né l'efficacia dei rituali. Utile su equipaggiamento universale, ma non è priorità.

**Nota Forza**: ininfluente per questa classe. Non usa armi pesanti né armatura pesante.

## 7 · Armor proficiency

- **Consentiti**: **stoffa** · **cuoio**
- **NON consentiti**: maglia · piastre
- **Consiglio**: la stoffa è la scelta rituale principale (canalizza meglio i Marchi). Il cuoio è alternativa per chi vuole più mobilità e protezione leggera.

## 8 · Weapon proficiency

- **Consentiti**: **focus** · **balestra** · **pugnale**
- **NON consentiti**: arco · spada · bastone · tomo · martello · reliquia (come arma) · ascia · scudo · lancia · arma in asta
- Il Cacciatore del Vuoto è un rituale, non un guerriero. Le sue armi sono **strumenti di canalizzazione**: applicano Marchi, generano Frammenti, chiudono rituali.

## 9 · Arma primaria raccomandata

**Focus** in mano principale.

- **Motivo**: miglior canalizzazione arcana · applica il Marchio del Vuoto in modo efficiente · massimizza il Drain · attiva i Payoff senza penalità di posa · **solo un Focus alla volta può essere equipaggiato**
- **Combinazione ideale**: Focus in mano principale + Pugnale nella secondaria
- **Alternativa**: Balestra a due mani (blocca la secondaria)

## 10 · Loop di gioco: Identifica → Marchia → Drena → Paga

Ogni scontro segue quattro passi:

1. **Identifica** — Riconosci il bersaglio giusto. Priorità: evocazioni e incorporei > castatori > mischia.
2. **Marchia** — Applica il **Marchio del Vuoto**. Silenzia le evocazioni · indebolisce gli incorporei nel tempo · prepara il Drain.
3. **Drena** — Colpisci il bersaglio marchiato con Focus, Balestra o Pugnale. Ogni colpo valido genera un **Frammento di Onirade**.
4. **Paga** — Spendi i Frammenti in un **Payoff**. Dispel di area (**3 Frammenti**) o annullamento di un'evocazione nemica (**5 Frammenti**).

## 11 · Marchio del Vuoto

- **Cos'è**: un sigillo rituale che imprimi su un bersaglio. Silenzia evocazioni, indebolisce incorporei nel tempo, e trasforma quel bersaglio in fonte di Frammenti quando lo colpisci.
- **Quanti attivi**: **3 di base** · **4 con Intelligenza 50** · **5 con Intelligenza 90** · massimo assoluto **5**
- **Durata**: **3 turni di base** · cresce con l'Intelligenza fino a un massimo pratico di **8 turni** · limite assoluto **10 turni** (nessun potenziamento può superarlo)
- **Regola refresh**: riapplicare il Marchio su un Marchio esistente azzera la durata. Non si accumulano: un Marchio solo per bersaglio.
- **Consiglio**: non riapplicare troppo presto. Aspetta la finestra corretta per rinnovare.

## 12 · Frammenti di Onirade

La risorsa unica del Cacciatore del Vuoto.

- **Non sono oggetti** · non finiscono nell'inventario · non si vendono · non si scambiano
- Sono un **progresso rituale** che accumuli durante uno scontro e spendi in quello scontro
- **Come si ottengono**: colpendo un bersaglio Marchiato con Focus, Balestra o Pugnale. Intelligenza alta = probabilità di un Frammento bonus sul colpo.
- **Quando si perdono**: fine scontro · morte del personaggio · passaggio a una fase maggiore dell'incontro. Non attraversano tra scontri.
- **Regola semplice**: se il bersaglio non è Marchiato, non generi Frammenti da lui.

## 13 · Cap 5

- **Valore**: **5 Frammenti** massimi
- **Regola**: sei già a 5? I nuovi Frammenti non vengono generati. Usa un Payoff per liberare spazio.
- **Design principle**: il cap 5 è **definitivo**. Nessun equipaggiamento, nessun Leggendario, nessuna combinazione può superarlo. Serve a mantenere una scelta reale tra Payoff intermedio e Payoff massimo.

## 14 · Payoff da 3 Frammenti — Dissolvenza rituale

- **Nome azione**: Dissolvenza rituale (Payoff minore)
- **Costo**: **3 Frammenti**
- **Effetto**: dispel arcano di area · rimuove effetti arcani sospesi intorno al bersaglio · libera gli alleati da eventuali maledizioni arcane in raggio
- **Quando usarlo**: 2+ alleati con debuff arcano · area piena di residui rituali · vantaggio subito, non più tardi
- **Reliability**: alta contro effetti comuni · con Intelligenza elevata copre anche effetti più rari · contro incantesimi leggendari lanciati dai boss serve la versione a 5 Frammenti

## 15 · Payoff da 5 Frammenti — Bando del Vuoto

- **Nome azione**: Bando del Vuoto (Payoff massimo)
- **Costo**: **5 Frammenti**
- **Effetto primario**: annulla un'evocazione nemica standard (l'evocazione scompare dal campo)
- **Contro evocazioni richiamate da un boss**: passa attraverso le protezioni ma può essere ridotto
- **Effetto alternativo**: bandisce un bersaglio incorporeo singolo dal campo
- **Fallback senza bersaglio valido**: il Payoff NON si attiva e i Frammenti NON vengono consumati. Il gioco ti dirà: *"Nessuna evocazione valida da annullare."*
- **Immunità boss diretto**: i boss stessi non possono essere bandi né annullati. Puoi solo colpire le loro evocazioni.
- **Safeguard deterministico**: contro un'evocazione standard, l'annullamento è **certo**. Non c'è probabilità di fallimento casuale. Contro evocazioni protette da un boss l'efficacia varia, ma la meccanica non diventa mai una roulette.

## 16 · Comportamento contro evocazioni

Le evocazioni sono il tuo bersaglio principale. Marchiale subito: il Marchio le **silenzia per alcuni turni**, bloccando le loro abilità (ma non il movimento). Quando hai 5 Frammenti, il Bando del Vuoto le rimuove del tutto.

## 17 · Comportamento contro incorporei

Le entità incorporee vengono indebolite dal Marchio nel tempo (dispel-over-time). Generi Frammenti su di loro leggermente più facilmente: sono target rituali per definizione. A 5 Frammenti puoi bandirle come un'evocazione.

## 18 · Comportamento contro boss

I boss possono essere marchiati (ma solo con **un Marchio alla volta**, e con effetto ridotto). Non puoi bandirli né annullarli. Puoi però annullare le loro **evocazioni**, ed è lì che decidi la partita: risparmia i Frammenti per la fase con le evocazioni critiche.

## 19 · Comportamento senza bersagli speciali

In uno scontro senza evocazioni né incorporei, il tuo loop è ridotto ma **funziona ancora**. Marchia i bersagli normali, drena, e usa i Payoff in modo utile: la dissolvenza rituale libera i tuoi alleati da debuff arcani anche in questi contesti. Non resti mai senza qualcosa da fare.

## 20 · Focus (arma)

- **Ruolo**: arma primaria a mano principale · la scelta standard
- **Punti forza**: miglior canalizzazione arcana · massima efficacia sull'applicazione del Marchio · può canalizzare un turno intero per ottenere un Frammento bonus (**massimo 2 canalizzazioni per segmento di risorsa**)
- **Punti deboli**: richiede posizionamento a media distanza · non ottimo in mischia stretta
- **Consiglio**: se non sei sicuro, scegli Focus. È la scelta bilanciata.

## 21 · Balestra (arma)

- **Ruolo**: opzione a distanza sicura · occupa entrambe le mani
- **Punti forza**: range esteso · sicurezza posizionale in incontri pericolosi in prima linea · applica il Marchio a bersagli difficili da raggiungere
- **Punti deboli**: occupa la mano secondaria (non puoi usare il Pugnale) · efficacia arcana leggermente inferiore rispetto al Focus · nessun bonus di canalizzazione
- **Importante**: la Balestra del Cacciatore del Vuoto è una **balestra di canalizzazione arcana**. Non è la balestra fisica del Cacciatore di Mostri: usa la tua **Intelligenza**, non la Destrezza.

## 22 · Pugnale (arma)

- **Ruolo**: arma rituale opportunistica · ideale come mano secondaria affiancata a un Focus
- **Punti forza**: chiude i rituali · se colpisci un bersaglio Marchiato con il Pugnale nell'ultima finestra prima che il Marchio scada, generi un **Frammento bonus** (una volta per Marchio)
- **Punti deboli**: danno sostenuto minore delle altre armi · richiede vicinanza al bersaglio
- **Consiglio**: il Pugnale premia la lettura del tempo. Colpisci al momento giusto, non subito.

## 23 · Stoffa (armor)

- **Identità**: la scelta rituale principale · massimizza la canalizzazione dei Marchi e del Drain
- **Quando sceglierla**: sempre come default, salvo esigenze specifiche di mobilità o protezione fisica

## 24 · Cuoio (armor)

- **Identità**: alternativa per chi vuole più mobilità e una protezione leggera migliore · resta una scelta con Intelligenza come statistica principale
- **Quando sceglierlo**: incontri dove il posizionamento è più difficile e serve reagire velocemente
- **Chiarimento importante**: il cuoio del Cacciatore del Vuoto è un **cuoio arcano**. Non è un cuoio da ladro né da cacciatore fisico. Anche col cuoio, la tua statistica primaria resta l'**Intelligenza**.

## 25 · Punti di forza

- Unico in grado di annullare evocazioni nemiche in modo affidabile
- Controlla incorporei e distorsioni arcane meglio di qualsiasi altra classe
- Loop chiaro e appagante: costruzione + spesa decisiva
- Skill ceiling alto: la lettura del tempo e la scelta del Payoff premiano il giocatore esperto
- Buon posizionamento a distanza media, versatile tra ranged e ritualista in mischia
- Sinergia forte in gruppo con classi che fanno danno diretto: il Cacciatore del Vuoto crea le finestre

## 26 · Punti deboli

- Fragile: stoffa e cuoio non reggono colpi diretti prolungati
- Non è una classe da mischia: se ti trovi accerchiato, hai poche opzioni
- AoE limitata: non è un caster di bruciature a raffica come il Mago
- Dipende dal Marchio: se non riesci a marchiare, non generi Frammenti
- Contro i boss diretti non annulli nulla: devi lavorare sulle loro evocazioni
- Skill floor più alto della media: chi non impara il loop resta indietro

## 27 · Errori comuni

- Colpire bersagli non Marchiati sperando di generare Frammenti (non succede)
- Sprecare il Payoff da 5 Frammenti su boss diretti (sono immuni all'annullamento)
- Riapplicare il Marchio troppo presto perdendo tempo di lancio
- Accumulare Frammenti fino al massimo senza mai spenderli (arrivi al cap e non generi più)
- Ignorare le evocazioni per colpire il boss (invertire priorità = perdere l'incontro)
- Usare Balestra e aspettarsi lo stesso danno del Cacciatore di Mostri (armi diverse, gameplay diverso)
- Sperare che la Saggezza aiuti (non è la tua statistica)

## 28 · Consigli per nuovi giocatori

- Inizia con Focus in mano principale · è la scelta più chiara e insegna il loop
- Marchia sempre prima di colpire · senza Marchio non hai porta d'ingresso al Drain
- Non aver paura di usare il Payoff a 3 Frammenti quando è utile · non aspettare sempre il massimo
- Impara a leggere la barra dei Frammenti · quando sei vicino al cap, prepara il Payoff
- Se il tuo Marchio scade e non hai spesa Frammenti, non è un dramma · i Frammenti restano finché lo scontro non termina
- In gruppo, comunica: *"ho i Frammenti pronti"*, *"la prossima ondata è mia"*

## 29 · Consigli avanzati

- Contro un boss con fasi di evocazione, risparmia i 5 Frammenti per la fase critica
- Con Focus, sfrutta la canalizzazione (fino a **2 volte per segmento di risorsa**) prima che il Marchio scada
- Con Pugnale in secondaria, il colpo finale prima della scadenza del Marchio ti regala un Frammento bonus · cronometra bene
- Il cambio arma durante lo scontro è consentito ma costa un turno · pianifica in anticipo il loadout
- In raid, coordina le tue evocazioni annullate con i cast del Mago · le tue finestre proteggono i suoi burst
- La Balestra sacrifica il Pugnale ma ti dà distanza · usala su incontri con AoE pesante in prima linea
- Quando raggiungi Intelligenza 50 sblocchi il **quarto Marchio attivo** · a **90 il quinto**. Costruisci l'equipaggiamento verso queste soglie.

## 30 · Compatibilità party/raid

- **Gruppo 3**: Paladino cura + Guerriero (o Cacciatore di Mostri) frontline + Cacciatore del Vuoto asse arcano. Le tre classi si completano.
- **Raid 5**: DPS specialistico anti-evocazione · sinergia forte con Mago (elimini le evocazioni che rompono i suoi burst) e con Paladino (cura). Il Guerriero tiene la threat, il quinto ruolo è flessibile.
- **Solo**: il loop funziona anche in solitaria. Contro nemici standard il ritmo è più lento del solito, ma i Payoff diventano utility (dispel dei tuoi stessi debuff). Non resti mai senza opzioni.

## 31 · Differenza dal Mago

Il **Mago** è un caster di bruciature dirette e aree elementali. Colpisce forte e ovunque. Il **Cacciatore del Vuoto** accumula progresso rituale e lo spende in momenti decisivi. Entrambi DPS con Intelligenza, ma nicchie diverse.

- **Scegli Vuoto** se ami costruzione → spesa · scelte strategiche sui Payoff · gestire le evocazioni
- **Scegli Mago** se vuoi bruciare tutto subito · danno diretto · AoE massimizzata

## 32 · Differenza dal Cacciatore di Mostri

Il **Cacciatore di Mostri** caccia le creature del mondo fisico: bestie · mostri corporei · prede da tracciare. Usa Destrezza · armi fisiche · balestra fisica. Il **Cacciatore del Vuoto** caccia le forme del non-mondo: evocazioni · incorporei · distorsioni. Usa Intelligenza · rituale · balestra di canalizzazione arcana.

- **Balestra condivisa · gameplay opposto**: il Cacciatore di Mostri abbatte corpi con la sua balestra fisica. Il Cacciatore del Vuoto canalizza Marchi con la sua balestra arcana. L'aspetto è simile; il gameplay è opposto.
- **Scegli Vuoto** se ti interessa la caccia rituale · controllo arcano · chiudere crepe nel velo
- **Scegli Cacciatore di Mostri** se ti interessa caccia fisica · mobilità · inseguimento e abbattimento diretto

## 33 · Differenza dal Paladino

Il **Paladino** è un supporto sacro che cura, protegge e sostiene il gruppo. Il **Cacciatore del Vuoto** è un DPS anti-arcano che elimina minacce specifiche. Ruoli **opposti** che coesistono benissimo in gruppo.

- **Sinergia**: uno dei duetti più efficaci · il Paladino cura mentre il Cacciatore del Vuoto neutralizza le fonti di threat arcano

## 34 · Penalità XP futura per main stat insufficiente

- **Descrizione**: è previsto un sistema che penalizzi l'esperienza guadagnata se la statistica principale di classe è troppo bassa rispetto al livello del personaggio. Per il Cacciatore del Vuoto la statistica principale è l'**Intelligenza**: chi la lascia indietro sacrifica progressione XP.
- **Stato attuale**: 🔒 **SISTEMA PREVISTO · NON ANCORA LIVE · in progettazione in un gate futuro**
- **Nota**: al momento questa penalità **NON è attiva**. È documentata in anticipo per orientare le scelte di build. Quando verrà introdotta, riceverai comunicazioni chiare in gioco.

## 35 · Sala di Classe

**Faro Rovesciato di Onirade**

Il luogo dove i Cacciatori del Vuoto imparano a leggere il velo. Non è un faro che illumina il mare: è un faro che **riflette all'indietro**, verso il mondo dietro il mondo. La sua luce non guida le navi: guida i rituali.

**Atmosfera**: silenziosa · ordinata · illuminata in modo strano. Il pavimento riflette come uno specchio d'acqua ferma. Al centro, uno spazio aperto per la prova.

## 36 · Hall Master

**Nael di Onirade** · Maestro del Faro Rovesciato

Nael non è un maestro d'armi. È un **lettore del velo**. Parla poco, osserva molto. Chi vuole diventare Cacciatore del Vuoto deve prima farsi guardare da lui.

**Ruolo narrativo**: guida narrativa dell'onboarding di classe · non combatte con l'aspirante · osserva e riflette.

## 37 · Prova safe-mode (teaser)

**La Prova del Riflesso Vuoto**

Nel Faro Rovesciato attende una prova per chi vuole diventare Cacciatore del Vuoto. Non richiede combattimento pericoloso: è un **esercizio guidato** in cui Nael insegna a riconoscere ciò che l'occhio comune non vede.

> I dettagli di come si affronta la Prova del Riflesso Vuoto saranno definiti in un gate successivo. Questa guida ne anticipa solo l'esistenza.

## 38 · Tooltip italiani (esempi player-facing)

- *"Frammenti di Onirade: {n}/5 · usa i Frammenti per attivare rituali del Vuoto"*
- *"Payoff pronto: dissolvenza rituale (spesa 3 Frammenti)"*
- *"Payoff massimo pronto: bando del Vuoto (spesa 5 Frammenti)"*
- *"Frammenti al massimo · spendi un Payoff per continuare a generare"*
- *"Frammento di Onirade catturato"*
- *"Dissolvenza rituale attivata · effetti arcani rimossi"*
- *"Evocazione annullata · bersaglio bandito dal campo"*
- *"Bersaglio incorporeo bandito"*
- *"Barriera arcana attivata · autoprotezione temporanea"*
- *"Rituale interrotto · Frammenti conservati"*
- *"Nessun bersaglio marchiabile · applica prima un Marchio del Vuoto"*
- *"Marchio del Vuoto svanito · nuovo Marchio richiesto per il Drain"*
- *"Nessuna evocazione valida da annullare."*
- *"La distorsione cambia forma. I Frammenti di Onirade si dissolvono."*

## 39 · Glossario

- **Cacciatore del Vuoto** — La classe pilota: rituale anti-evocazione, anti-incorporeo, anti-distorsione arcana.
- **Marchio del Vuoto** — Sigillo rituale applicato a un bersaglio · silenzia evocazioni · indebolisce incorporei · abilita il Drain.
- **Frammenti di Onirade** — Risorsa unica di classe · si accumula colpendo bersagli Marchiati · si spende nei Payoff.
- **Drain** — L'atto di colpire un bersaglio Marchiato per generare Frammenti.
- **Payoff** — L'attivazione rituale che spende Frammenti per un effetto decisivo (dispel di area a 3 Frammenti · bando a 5 Frammenti).
- **Dissolvenza rituale** — Payoff da 3 Frammenti · dispel arcano di area.
- **Bando del Vuoto** — Payoff da 5 Frammenti · annullamento evocazione o bando incorporeo.
- **Segmento di risorsa** — Uno scontro standard oppure una fase maggiore di un incontro complesso · reset dei Frammenti tra un segmento e l'altro.
- **Faro Rovesciato di Onirade** — La Sala di Classe del Cacciatore del Vuoto.
- **Nael di Onirade** — Maestro della Sala · guida narrativa dell'onboarding di classe.
- **Prova del Riflesso Vuoto** — Prova di ingresso della Sala · dettagli in gate futuro.

## 40 · Struttura chiavi i18n

- **Lingua bloccata**: italiano
- **Nessuna traduzione inglese** presente
- **Nessun testo bilingue** nel documento
- **Nota**: la struttura è pensata per essere estesa in futuro con altre lingue, MA in questa fase è disponibile SOLO in italiano.
- **Key pattern concept**: `class.cacciatore_del_vuoto.<sezione>.<chiave>` (concetto per gate futuro di implementazione i18n)
- **Lingua attualmente consegnata**: `it-IT`
- **Lingue future**: placeholder riservato · nessuna traduzione live · nessun testo bilingue

## 41 · Risk register (12 rischi tracciati)

| ID | Rischio | Severity | Status |
|---|---|---|---|
| PG-R1 | Player pensa che la classe sia già giocabile | MEDIUM | DESIGNED |
| PG-R2 | Confusione balestra Vuoto (arcana) vs Cacciatore di Mostri (fisica) | MEDIUM | DESIGNED |
| PG-R3 | Player spera che la Saggezza aiuti | LOW | DESIGNED |
| PG-R4 | Player usa 5F su boss diretti e resta deluso | MEDIUM | DESIGNED |
| PG-R5 | Aspettative sulla penalità XP creano frustrazione | MEDIUM | DESIGNED |
| PG-R6 | Menzione weapon family riservata (excluded from pilot · drift risk) | LOW-MEDIUM | DESIGNED |
| PG-R7 | Aspettative sulla Prova del Riflesso Vuoto (gate 8) | LOW | DESIGNED |
| PG-R8 | Nomi classi non canonici (hallucination) | LOW | DESIGNED |
| PG-R9 | Tooltip con codici tecnici visibili | LOW | DESIGNED |
| PG-R10 | Nuovi giocatori non capiscono cap 5 · overcap sprecato | LOW-MEDIUM | DESIGNED |
| PG-R11 | Loop 4-step complesso da comunicare senza tutorial in-game | LOW-MEDIUM | TRACKED PG1 |
| PG-R12 | Traduzioni inglesi accidentali | LOW | DESIGNED |

## 42 · PM Open Questions (PG-Q1..PG-Q8)

- **PG-Q1** · *Marker 'GUIDA DI DESIGN — CLASSE NON ANCORA DISPONIBILE' conferma?* → **a) LOCK formulazione**
- **PG-Q2** · *Tono guida (chiaro · non tecnico · doppio pubblico) conferma?* → **a) LOCK tono**
- **PG-Q3** · *Numeri player-facing autorizzati (Frammenti 5 · Payoff 3F/5F · Marchi 3/4/5 · Marchio 3-8T max 10T · Focus max 2/segmento) conferma?* → **a) LOCK**
- **PG-Q4** · *Sezione penalità XP futura come 'sistema previsto NON ancora live' conferma?* → **a) LOCK**
- **PG-Q5** · *Teaser 'Prova del Riflesso Vuoto' con 2-3 righe conferma?* → **a) LOCK teaser breve**
- **PG-Q6** · *i18n key structure 'italiano only · no traduzioni EN' conferma?* → **a) LOCK italiano only**
- **PG-Q7** · *Wave 1 successors HOLD fino G6+G7+G8+G9+G10 CLOSED?* → **a) LOCK HOLD**
- **PG-Q8** · *Sinergia party section (Paladino/Guerriero/Cacciatore di Mostri/Mago) conferma?* → **a) LOCK**

## 43 · GO/HOLD Recommendation Gate 7 HALL_COMPLETION

- **Gate 6 status**: DRAFT · pending PM review + risposte PG-Q1..PG-Q8
- **Gate 7 status**: 🔒 **HOLD** · attende PM ACK Gate 6 + GO esplicito Gate 7
- **Gate 7 scope preview**: HALL_COMPLETION · finalizza layout della Sala del Faro Rovesciato · Nael dialoghi onboarding · flow entry class · quest chain minimal · SOLO documentazione della Sala · NO tutorial implementation · NO Prova del Riflesso Vuoto gameplay (gate 8) · NO class unlock · NO Hall activation runtime
- **NO Gate 7 auto-start · NO Wave 1 auto-start (Monaco/Druido/Alchimista/Bardo/Negromante)**
- **Recommended next step**: PM review G6 PLAYER_GUIDE + risposte PG-Q1..PG-Q8 → G6 CLOSED verdict → GO Gate 7 HALL_COMPLETION

---

## 🛑 STOP obbligatorio a fine G6 · Non procedere a Gate 7 senza nuovo GO PM

> ⚠️ **GUIDA DI DESIGN — CLASSE NON ANCORA DISPONIBILE**
> Questa guida descrive il design del **Cacciatore del Vuoto**. La classe **non è ancora disponibile in gioco**.

Attendo PM review Gate 6 PLAYER_GUIDE + risposte a **PG-Q1..PG-Q8**. Nessun auto-start Gate 7 · Nessun auto-start Wave 1 successors · Nessuna modifica R18.5/R18.6/R18.6.1/R18.6.2/G1/G2/G3/G4/G5/RV3 (tutti LOCKED).
