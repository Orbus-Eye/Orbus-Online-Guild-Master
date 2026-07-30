# Orbus Online — Roadmap operativa item-first

**Aggiornata:** 2026-07-30  
**Branch:** `main-260728`  
**HEAD di partenza:** `780c05894f60c99745e0a94a3a7c337895a86c4a`

Lo stato include modifiche locali non ancora committate o distribuite.

## Visione non negoziabile

```text
Recluta senza classe
→ confronto fra 27 Class Hall
→ prova sicura del sentiero
→ scelta esplicita
→ classe
→ item identitario
→ equip e build
→ spedizione
→ nuovi item, lore e scelte
```

Gli item sono il centro della progressione, della collezione e del racconto.
Ogni blueprint deve avere identità singolare. Una parte sostanziale deve essere
legata a luoghi, persone, eventi o misteri della lore di Orbus.

## Revamp carriera e formazioni — implementato localmente

- rarità avventuriero rimossa da ogni generazione player-facing;
- tutti nascono Comuni e avanzano per partecipazione cumulativa:
  `50 dungeon → Non comune`, `150 → Raro`, `500 + 5 raid → Epico`,
  `2000 + 150 raid → Leggendario`;
- ogni promozione raddoppia tutte le statistiche primarie rispetto al grado
  precedente: Comune ×1, Non-Comune ×2, Raro ×4, Epico ×8 e
  Leggendario ×16; i valori salvati restano quelli base;
- eventi carriera idempotenti e riconciliazione dello storico dungeon/raid;
- primi cinque fondatori gratuiti e deterministici;
- reclutamento successivo come costruzione esplicita di nome, razza e genere;
- rimossi API/UI di candidati casuali, refresh e panchina reclute;
- costo progressivo post-fondatori, cap Dormitori e rimborso su race concorrente;
- curva XP 1→80 elevata a `2.817.584 XP` cumulativi;
- dungeon canonici da 3, 5 e 7 membri;
- raid canonici da 10, 15, 20 e 40 membri, sempre in party da cinque;
- preset squadra estesi a tutte le sette dimensioni;
- 23 dungeon con nome italiano, descrizione e fonte lore autorevoli;
- quattro raid con identità, boss, fasi e reward profile dedicati;
- equipaggiamento fisico a dieci slot: arma, corazza, gambe, elmo,
  accessorio, schiena, due anelli e due monili;
- boss mondiale corretto per kill immediata, team esatto da tre,
  Class Hall obbligatoria e PWR comprensivo dell'equipaggiamento;
- crafting e forgia auditati: lavorano su template/istanze e non dipendono
  dal vecchio numero di slot; filtri equip player-facing estesi;
- Dormitori già scalano fino a 100 posti e sostengono il raid da 40;
- `L'Unico Anello della "Compagnia"` esiste come blueprint Unico Lv80,
  tiro segreto `1 su 1.000.000` per ogni gilda che contribuisce alla sconfitta
  di Alveora e claim globalmente non duplicabile.

La creazione del pool completo da 1500 item resta intenzionalmente successiva
al consolidamento e playtest di questo motore. I set con bonus combinati
restano l'ultima fase item.

## Baseline tester raggiunto localmente

### Recluta e Class Hall

- il reclutamento autorevole crea avventurieri senza classe;
- i cinque starter di una nuova Gilda sono classless;
- il marker è `recruit_status=recruit_unassigned`;
- `class_slug=null` da solo non riclassifica i conflitti legacy;
- equip specializzato e attività sono bloccati finché non viene scelta una Hall;
- tutte le 27 Hall Wave A–E sono `ACTIVE / APPROVED` in test;
- ogni Hall espone Maestro, lore, ruolo, stat, proficiency e prova safe-mode;
- la conferma è esplicita, atomica, CAS e idempotente;
- il primo item identitario viene consegnato esattamente una volta;
- produzione resta fail-closed e richiede allowlist esplicita.

### Item e progressione

- 135 item di Hall: `5 × 27 classi`;
- 135/135 ID, slug e nomi italiani unici, anche case-insensitive;
- 135/135 con fonte lore, flavor text e revisione lore;
- 27/27 signature item con definizione effetto statica nel codice;
- track raggiungibile per ogni Hall:
  - signature alla scelta;
  - seconda arma dopo aver equipaggiato la signature;
  - armatura dopo una spedizione;
  - reliquia al livello 2;
  - memoria/materiale dopo tre spedizioni;
- grant reconcile-forward ed esattamente una volta;
- Collection Book per Hall, wave, slot, stato ottenuto/equipaggiato e ricerca;
- dettaglio di lore, fonte, provenienza ed effetto visibile al tester.

### Catalogo persistente attuale

Su database Mongo locale isolato:

- 261 item attivi non-test;
- 261/261 ID, slug e nomi unici;
- 261/261 con `lore_reviewed=true` e `lore_source`;
- 261/261 con flavor text (`100%`);
- tutti i 135 item Hall presenti a livello 1;
- rarità normalizzate in minuscolo.

Il registry R18.5 da 1500 blueprint è design legacy basato su cinque archetipi,
non catalogo runtime. Contiene 4 record riservati e 10 marker progressivi.
Non va migrato alla cieca: richiede rimappatura alle 27 classi, audit dei nomi,
della lore, degli effetti e delle fonti.

### Strumenti tester

- reset ripetibile del viaggio senza perdere lo storico;
- rilascio delle prenotazioni equip;
- ricreazione esatta di cinque starter classless;
- smoke matrix read-only;
- grant item e set-max-level coerenti col contratto classless;
- pannello amministrativo per reset e matrice.

## Verifiche verdi

```text
16 test unitari classless/Class Hall
21 test proiezione/report effetti item
2 test copertura narrativa Common
39 test mirati finali in un'unica regressione
116 test real-Mongo dell'effect engine
6 test real-Mongo del percorso Hall
2 test HTTP black-box
seed e indici idempotenti
CAS concorrente e grant exactly-once
27 classi: assignment + signature equip
9 spedizioni × 3 membri: copertura delle 27 classi
27/27 signature: effetto applicato, target e magnitudo verificati
report item → effetto → stat → delta PWR
Collection Book: 27 Hall / 135 item
flake8 critical sui file nuovi
frontend production build
browser QA reale: catalogo, filtro Wave E, lore, fonti, effetti
browser console: 0 errori / 0 warning
FastAPI app: 306 route / 284 path OpenAPI
scritture shared/prod: 0
deploy: non eseguito
```

La suite storica monolitica non è verde né portabile in questo ambiente:
include test accoppiati a `/app`, credenziali SMTP, fixture con vecchie password,
database pre-popolati e `httpx` non dichiarato nell’ambiente corrente. Il suo
fallimento non viene contato come regressione del nuovo percorso, ma resta
debito di test da separare e bonificare. Non dichiarare più `557/557` come
verifica corrente senza riprodurre il vecchio ambiente.

## Debiti reali ancora aperti

1. Le 27 classi hanno meccanica e tre build item-driven, ma restano skill
   tree, encounter dedicati, telemetria e tuning con tester.
2. I 268 record legacy con `class_slug=null` sono preservati e richiedono
   classificazione, dry-run e rollback.
3. Il registry da 1500 richiede una nuova tassonomia a 27 classi.
4. La suite legacy deve essere divisa in unit, integration e acceptance,
   eliminando dipendenze da path, dati e credenziali storiche.
5. Mancano sessioni di bilanciamento con tester e telemetria per wave.

## Contratto catalogo canonico

Il catalogo principale finale contiene esattamente 1500 blueprint individuali:

| Rarità | Presenza catalogo | Quantità |
|---|---:|---:|
| Comune | 35% | 525 |
| Non-Comune | 25% | 375 |
| Raro | 20% | 300 |
| Epico | 15% | 225 |
| Leggendario | 4% | 60 |
| Unico | 1% | 15 |

La presenza nel catalogo non è una probabilità di drop. Drop, accesso,
livello richiesto e binding sono dimensioni separate. I Leggendari restano
endgame e richiedono il livello massimo. `L'Unico Anello della "Compagnia"`
appartiene alla rarità Unico ed è il solo artefatto con un drop casuale
estremamente basso.

Target di organizzazione:

- 1350 item di classe: 50 per ognuna delle 27 classi;
- 150 item universali o trasversali;
- 60 Leggendari: almeno 2 per classe, con i restanti mondiali/trasversali;
- 15 Unici legati alla lore e a imprese eccezionali;
- i set con bonus combinati non fanno parte di questa prima produzione e
  vengono progettati soltanto dopo il bilanciamento dei 1500 item individuali.

## Prossime tranche — ordine canonico

### T0 — Contratti e contatori autorevoli — TRANCHE 1 COMPLETATA

Implementato localmente:

- contratto centrale esatto `525/375/300/225/60/15`;
- rarità `Unique` canonica in backend e principali superfici item frontend;
- livello massimo autorevole 80 e blocco dell'avanzamento oltre il cap;
- Leggendari e Unici forzati al livello massimo anche sui record legacy;
- curva PvE autorevole su otto fasce da 10 livelli;
- 23 dungeon riallineati da livello 1 a 70 con PWR e XP coerenti;
- quattro raid riallineati ai livelli 40, 60, 70 e 80;
- audit runtime read-only tramite `/api/items/catalog-contract`;
- limite di lettura catalogo portato da 500 a 2000 record;
- protezione quote sui create/update/activate amministrativi;
- drop ordinari dei dungeon limitati a Comune–Epico;
- riserva del roll ultra-raro al solo Anello della Compagnia;
- audit offline JSON/JSONL/BSON senza connessioni database;
- 41 test unitari T0 verdi e build frontend di produzione verde.

Resta nella tranche successiva T0:

- collegare il guard quote al futuro import massivo dedicato;
- audit dry-run esatto dei 261 record quando sarà disponibile una snapshot;
- produrre piano di riclassificazione senza mutare dati condivisi;
- rendere atomiche le prenotazioni quota del futuro import concorrente.

- introdurre la rarità `Unique` in schema, API, UI, filtri e ordinamenti;
- centralizzare livello massimo e regole di equip;
- separare `catalog_presence` da `acquisition_weight` e `drop_chance`;
- creare contatori automatici per rarità, classe, slot, fonte e livello;
- bloccare seed/import che superano uno dei sei contingenti;
- rimuovere il vecchio generatore 68/24/7/0.9/0.1 come fonte autorevole;
- definire snapshot, dry-run, migrazione idempotente e rollback.

### T1 — Profondità delle 27 classi

Contratto item-driven implementato localmente per tutte le Wave A–E:

- Guerriero, Ladro, Mago, Paladino e Cacciatore di Mostri hanno una
  meccanica statica server-owned distinta;
- Alchimista, Bardo, Druido, Monaco, Negromante, Sciamano e Cacciatore del
  Vuoto estendono lo stesso contratto senza aumentare il budget di potenza;
- Artificiere, Cartografo, Cronista, Fabbro Arcano, Mercante e Runista
  introducono percorsi di preparazione, controllo e utilità;
- Astrologo, Burattinaio, Giocatore d'Azzardo, Parassita, Pittore e Sognatore
  coprono controllo avanzato, rischio e alterazione;
- Cacciatore del Sangue, Cavaliere della Morte e Cavaliere di Draghi chiudono
  la Wave E con identità marziali avanzate;
- 27 classi coperte, con tre identità di build ciascuna: 81 percorsi totali;
- selezione automatica della build tramite tag degli item equipaggiati;
- bonus identità di base e risonanza item separati e osservabili;
- contromisure di classe collegate al sistema minacce dei dungeon;
- snapshot immutabile della meccanica alla partenza;
- report tester con sentiero, build, item risonante e contributo PWR;
- anteprima delle tre build nella scelta della Class Hall.

Il contratto T1 è completo sulle 27 classi. Restano tuning comparato,
telemetria e profondità futura delle skill, da guidare con sessioni tester.

- una meccanica distintiva e osservabile per ogni classe;
- almeno tre identità di build previste per classe;
- ruolo, stat, proficiency, minacce contrastate e limiti di equip coerenti;
- contratto replicato e verificato sulle Wave A–E;
- telemetria di contributo, sopravvivenza e impatto item.

Non si popolano ancora i 1500 item: si usano placeholder e il catalogo
esistente per provare le regole.

### T2 — Revisione dungeon

Prima tranche implementata localmente:

- contratto canonico unico per i 23 dungeon correnti;
- curva livello, PWR e XP applicata dalla fonte autorevole fino al livello 70;
- classificazione per difficoltà, durata, squadra ed encounter type;
- 16 famiglie di minacce distribuite sugli incontri;
- tutte le contromisure delle 27 classi risultano utili in almeno un dungeon;
- lista, anteprima, partenza, replay, completamento e report usano lo stesso
  snapshot canonico anche con record DB obsoleti;
- riconciliazione Mongo idempotente all'avvio, senza creare contenuti mancanti;
- anteprima aggiornata con potenza equipaggiamento, build item-driven e fonte
  della contromisura di classe.
- le contromisure di classe diventano operative solo con un sentiero attivato
  da un item risonante: l'equipaggiamento incide oltre al semplice PWR.

Seconda tranche implementata localmente:

- 69 fasi canoniche: ingresso, obiettivo e culmine per ciascun dungeon;
- ogni fase espone minacce, modificatore e condizione di successo leggibile;
- lo snapshot della spedizione congela fasi, minacce e versione della curva;
- 23 profili ricompensa blueprint-only, distinti per incontro e difficoltà;
- categorie ottenibili visibili senza percentuali riservate o item definitivi;
- rarità massima Epico: Leggendari e Unici vietati in ogni dungeon ordinario;
- profili sensibili alla classe e collegamento lore obbligatorio dalla
  difficoltà 2;
- anteprima e report espongono lo stesso profilo congelato;
- la risoluzione continua a usare un solo tiro persistito, preservando
  exactly-once, retry e assenza di doppio grant.

T2 è completa come contratto implementativo. Restano tuning con tester e
l'inclusione degli effetti item eseguibili nella stima dell'anteprima.

### T3 — Revisione raid

Prima tranche implementata localmente:

- quattro contratti canonici sulle fasce 40/60/70/80;
- diciassette responsabilità distribuite tra 2/3/4/8 squadre;
- undici fasi, con il culmine che richiede sempre tutte le squadre;
- il PWR raid include ora equipaggiamento e meccanica di classe;
- le contromisure item-risonanti assegnano fino a +6% alla squadra contro le
  minacce della propria responsabilità;
- anteprima e raid congelano responsabilità, fasi e profilo ricompensa;
- raid 40/60/70 limitati a ricompense fino a Epico;
- solo il raid 80 può autorizzare blueprint Leggendari, solo su vittoria;
- i profili loot raid vietano Unici e nessun raid può rilasciare l'Anello;
- la fonte segreta dell'Unico Anello appartiene esclusivamente al boss
  mondiale Alveora.

Seconda tranche implementata localmente:

- token raid e frammenti Leggendari scalano tra wipe, parziale e vittoria;
- l'eleggibilità blueprint resta esclusiva della vittoria raid livello 80;
- ogni grant è registrato per `raid_id` in uno storico con indice unico;
- completamento manuale protetto da CAS `in_progress → resolving`, come il
  recovery, eliminando la race di doppia ricompensa;
- calcolo progressione condiviso tra completamento e recovery;
- bonus Forgia Arfus su XP e punteggio ora identici nei due percorsi;
- gli Unici restano fuori dai profili ordinari; l'Anello ha un roll separato
  esclusivamente per le gilde che contribuiscono alla sconfitta di Alveora.

T3 è completa come contratto implementativo. Restano bilanciamento dei valori
con tester e test d'integrazione sul Mongo isolato.

### T4 — Motore delle fonti e delle ricompense

Prima tranche implementata localmente:

- otto politiche canoniche coprono Hall, dungeon, raid, crafting,
  missione/evento/reputazione e fonte segreta;
- decisione unica per rarità, livello, binding, lockout, first-clear e
  duplicati;
- chiave grant SHA-256 stabile per guild, fonte, istanza e item;
- indice unico `reward_source_grants.grant_key` contro retry concorrenti;
- dungeon e raid dichiarano il proprio `source_policy_id`;
- Leggendari bloccati sotto il livello 80 e fuori dai dungeon ordinari;
- un solo roll ultra-raro: `L'Unico Anello della "Compagnia"`;
- probabilità privata Anello `0.000001` = `0,0001%` = circa uno su un milione;
- Anello livello 80, hard-bound e protetto contro una seconda assegnazione
  globale;
- fonte esclusiva: boss mondiale Alveora sconfitto, un tiro idempotente per
  evento e gilda con contributo positivo;
- le percentuali di presenza del catalogo restano separate dai drop rate.

Seconda tranche implementata localmente:

- il sampler runtime dei dungeon filtra i candidati tramite fonte e livello;
- item oltre il livello del contenuto e rarità endgame vengono esclusi prima
  dell'estrazione;
- simulatore Anello deterministico, read-only e limitato a 5.000.000 prove;
- il risultato dichiara sempre zero grant e zero mutazioni inventario;
- proiezione anti-inflazione calcola grant lordi, conversioni duplicati e
  nuovi item netti;
- fonti con oltre 10.000 nuovi item previsti richiedono revisione esplicita.

T4 è completa come fondazione implementativa. Restano l'applicazione del
motore agli altri grant legacy e la simulazione statistica con dati tester.

### T5 — Vertical slice tester completa — COMPLETATA

Prima tranche implementata localmente:

- nuovo contratto read-only server-owned per il percorso completo:
  Hall → item-firma → dungeon risonante → raid → grant → nuova build;
- la firma può essere provata dall'equip corrente o dallo snapshot immutabile
  di una spedizione, quindi il cambio equip successivo non cancella lo storico;
- dungeon valido solo se completato con una build realmente attivata dai tag
  degli item;
- raid valido solo se completato dopo quel dungeon dallo stesso avventuriero;
- ricompensa valida solo con `raid_reward_grants.status=applied` sullo stesso
  raid;
- nuova build valida solo in un'attività successiva al raid e con un
  `build_id` risonante diverso da quello del primo dungeon;
- telemetria aggregata per Hall, firme, dungeon, raid, grant, build distinte e
  percorsi completati;
- collo di bottiglia e prossima azione calcolati per il tester più avanzato;
- endpoint amministrativo read-only `/api/admin/tester-tools/vertical-slice`;
- pannello tester aggiornato con progresso 0/6 per avventuriero ed evidenza
  immediata della prossima prova richiesta;
- due test puri coprono sia il percorso valido sia il rifiuto di una seconda
  build usata prima della ricompensa raid.

Questa tranche ha reso misurabile la Definition of Done senza alterare
inventari o attività. Le tranche successive hanno completato percorsi reali
Wave A–E, confronto controllato, replica indipendente e verifica responsive.

Seconda tranche di strumentazione implementata localmente:

- matrice canonica Wave A–E derivata direttamente dal registry server-owned:
  `5/7/6/6/3` classi e `15/21/18/18/9` build;
- copertura complessiva misurata su 27 classi e 81 build, senza contare due
  volte lo stesso sentiero;
- primo gate separato: almeno un percorso end-to-end completato in ciascuna
  Wave;
- gate completo separato: tutte le tre build e almeno un percorso completo
  per ciascuna delle 27 classi;
- build osservate convalidate contro i tre `build_id` canonici della classe:
  ID inventati o snapshot corrotti non producono credito;
- coda prioritaria delle classi ancora da collaudare, con Wave e build
  mancanti;
- pannello tester con cinque schede Wave, contatori build e priorità operative;
- tre smoke test T5 coprono sequenza valida, ordine temporale errato e
  `build_id` non canonico.

La prossima tranche T5 non aggiunge altri contatori: esegue i percorsi reali,
registra i risultati nella matrice e usa i dati per il tuning.

Terza tranche, fondazione del tuning, implementata localmente:

- ogni partecipazione con build canonica alimenta un campione separato per
  classe e sentiero;
- metriche dungeon: campioni, esiti noti, successi e success rate;
- metriche raid: campioni, esiti partecipante, sopravvivenze e survival rate;
- medie PWR distinte per totale, equipaggiamento, effetto item e risonanza di
  classe, sempre derivate dagli snapshot congelati;
- confronto considerato inizialmente leggibile soltanto da cinque campioni per
  build, quindi obiettivo minimo esplicito `405 = 81 × 5`;
- coda di raccolta indica build, Wave e campioni ancora mancanti;
- tassi dungeon/raid estremi generano soltanto segnali da esaminare dopo la
  soglia minima; non applicano buff, nerf o altre mutazioni automatiche;
- metodologia esposta nel pannello per ricordare che difficoltà, livello e
  composizione della squadra sono variabili concorrenti;
- quattro smoke test T5 coprono percorso, ordine temporale, build non canonica
  e attivazione dei segnali soltanto dopo il campione minimo.

La strumentazione T5 è ora sufficiente per iniziare sessioni reali. Le formule
non devono essere modificate prima di avere campioni comparabili e contesto
dell'incontro.

Quarta tranche, raggiungibilità reale degli item, implementata localmente:

- audit iniziale del seed precedente: soltanto `28/81` build avevano almeno
  un tag presente nei cinque item Hall; 53 sentieri erano quindi impossibili
  da provare con il catalogo tester;
- 81 item equipaggiabili dichiarano ora un percorso canonico, esattamente tre
  per classe, mentre gli altri 54 conservano il proprio ruolo di
  progressione/lore senza inventare ulteriori build;
- ogni item di percorso espone nome, descrizione e tag della build attivata;
- assegnazione preserva gli item-firma Wave A e distribuisce i sentieri
  restanti tra arma, armatura e accessorio compatibile;
- audit puro risolve davvero ogni item attraverso il motore di classe:
  copertura `81/81`, dichiarazioni esatte `81/81`, associazioni invalide `0`;
- il seed fallisce prima di scrivere se manca una build, se una build ha più
  item dichiarati o se l'item stampato non attiva il sentiero promesso;
- la smoke matrix tester include il gate bloccante `hall_build_reachability`;
- Sentiero degli Oggetti e Collection Book mostrano la build legata all'item;
- due test puri e il contratto HTTP black-box proteggono seed, API e
  serializzazione pubblica.

Questa correzione è un prerequisito della raccolta campioni: da ora una build
assente dalla telemetria indica davvero una prova non eseguita, non un item
impossibile da ottenere o riconoscere.

Quinta tranche, Laboratorio Build, implementata localmente:

- endpoint read-only per ogni avventuriero assegnato a una Hall;
- mostra i tre sentieri canonici, l'item necessario, proprietà, quantità,
  stato equipaggiato e build attualmente risolta;
- individua gli item equipaggiati che attivano un sentiero concorrente;
- una build è `isolated_ready` soltanto se il suo item è equipaggiato, il
  resolver la conferma attiva e non esistono altre build concorrenti;
- prossima azione esplicita: ottenere l'item, equipaggiarlo, rimuovere i
  concorrenti, aggiornare il loadout oppure avviare l'attività;
- collegamento diretto alla pagina equipaggiamento, senza mutazioni automatiche
  o scorciatoie amministrative;
- interfaccia integrata nella pagina Class Hall, utilizzabile per qualsiasi
  avventuriero già assegnato;
- due test puri coprono build isolata e conflitto; il percorso HTTP verifica
  che l'item-firma del Guerriero isoli davvero Condottiero.

Il Laboratorio evita campioni ambigui: prima di un dungeon o raid il tester
può vedere se il risultato verrà attribuito a un solo sentiero item-driven.

Sesta tranche, normalizzazione dei campioni, implementata localmente:

- ogni attività conserva il rapporto tra potenza effettiva della squadra e
  potenza consigliata del dungeon o raid;
- quattro contesti separati: `underpowered`, `matched`, `overpowered` e
  `unknown`;
- intervallo comparabile server-owned T8: da `0,80` a `1,20` della
  potenza consigliata;
- tutti i campioni restano conteggiati e visibili, ma readiness, percentuali e
  segnali usano soltanto quelli `matched`;
- i cinque campioni minimi per build e il target `405` indicano quindi cinque
  attività comparabili, non cinque esiti qualsiasi;
- dungeon legacy recuperano la potenza consigliata dal record canonico senza
  modificare lo storico; i raid usano lo snapshot combinato già persistito;
- una serie di sconfitte sottopotenziate o vittorie sovrapotenziate non può
  più produrre automaticamente un falso segnale sulla build;
- pannello tester distingue campioni comparabili da campioni totali;
- quinto smoke test T5 dimostra che cinque sconfitte al 50% della potenza
  consigliata producono zero readiness e zero segnali di bilanciamento.

Questa normalizzazione non elimina tutte le variabili concorrenti, ma rimuove
la distorsione più evidente prima del confronto item/build.

Settima tranche, regressione isolata reale, completata localmente:

- runner T5 fail-closed, dry-run di default e senza caricamento del `.env`;
- Mongo accettato soltanto su `127.0.0.1:27017`, niente SRV, credenziali,
  query, nomi DB applicativi o destinazioni remote;
- ogni esecuzione usa database temporanei univoci in allowlist e li elimina
  anche in caso di errore;
- regressione seriale reale: `17 passed` su MongoDB 8.3 e API loopback
  avviata/arrestata dal runner;
- corretta la fixture delle 27 classi: l'avventuriero nasce ancora al livello
  1, ma la squadra sale al livello 5 prima dei Cunicoli dei Goblin, in linea
  con il primo gate PvE;
- registrati e verificati su Mongo i tre eventi audit del viaggio:
  prova iniziata, prova completata e classe confermata;
- corretto il ponte iniziale livello 1: il Campo d'Addestramento solitario
  viene ordinato prima degli altri dungeon, subito dopo Hall e item-firma;
- seed e contratto incontro concordano ora su difficoltà 1 e squadra da 1;
  il Nido delle Fogne resta il primo contenuto di gruppo livello 1;
- i due black-box HTTP certificano onboarding item-first e reset tester;
- dopo l'esecuzione non resta alcun database `orbus_r16_rt2b_it_*` e la porta
  HTTP gestita risulta chiusa;
- quattro test aggiuntivi verificano i blocchi del runner verso target non
  locali, la selezione seriale e il teardown innocuo.

Ottava tranche, percorso minimo Wave A–E, completata localmente:

- cinque rappresentanti certificati: Guerriero (A), Alchimista (B),
  Artificiere (C), Astrologo (D), Cacciatore del Sangue (E);
- tutti i 20 partecipanti passano realmente da una Class Hall e raggiungono
  il livello 80 tramite il tester tool controllato;
- i cinque rappresentanti equipaggiano la firma, completano il Campo
  d'Addestramento, partecipano allo stesso raid da quattro squadre, ricevono
  il grant applicato, cambiano item-build e completano una seconda attività;
- `minimum_wave_slice_ready` è vero per tutte le Wave; cinque viaggi completi
  e almeno dieci build risonanti distinte vengono osservati dagli snapshot;
- `set-max` crea con upsert il documento strutture quando manca; il successivo
  consolidamento lo ha esteso al catalogo canonico completo e a una rosa di 35;
- corretto il completamento raid: il generatore deterministico non viene più
  confuso con un'istanza `SystemRandom`, eliminando il 500 su ogni risoluzione;
- la regressione gestita sale a `18 passed`;
- la copertura minima per Wave è chiusa; quella completa delle 27 classi e
  81 build resta deliberatamente aperta.

Nona tranche, primo campione comparabile delle build, completata localmente:

- sbloccata e isolata anche la terza build per ciascuno dei cinque
  rappresentanti Wave;
- tutte le 15 build rappresentative vengono equipaggiate una alla volta e
  confermate dal Laboratorio Build senza item concorrenti;
- usate le Radici dell'Albero del Mondo, contenuto canonico Lv70/PWR 1600 da
  sette avventurieri, riallineato alla composizione T8;
- ogni partenza verifica a runtime che il rapporto PWR squadra/consigliato
  sia compreso tra `0,80` e `1,20`;
- raccolte 75 attività reali: cinque campioni comparabili per ognuna delle
  15 build;
- `sample_ready_build_count` sale a 15 e
  `total_comparable_samples` è esattamente 75;
- i cinque rappresentanti risultano `ready_for_tuning` con copertura 3/3;
- nessuna formula viene modificata automaticamente: i segnali estremi restano
  proposte di revisione da confrontare prima con il comportamento specifico
  degli item;
- la regressione resta `18 passed`, ora includendo anche il carico delle 75
  attività comparabili.

Decima tranche, copertura completa delle 27 classi, completata localmente:

- lo strumento tester può preparare 27 avventurieri per le Hall e quattro
  supporti non risonanti, restando entro la capienza reale dei Dormitori;
- tutte le 27 reclute nascono senza classe e attraversano prova sicura,
  conferma esplicita della Hall e consegna dell'item-firma;
- due raid canonici reali, separati dal cooldown globale previsto, coprono
  tutti i 27 avventurieri e persistono due grant `applied`;
- 27/27 viaggi Hall → firma → dungeon → raid → grant → nuova build risultano
  completi, con 54 build distinte già osservate prima del banco di tuning;
- tutte le 81 build vengono sbloccate, equipaggiate in isolamento e
  confermate dal Laboratorio Build;
- eseguite 405 spedizioni endgame dedicate, cinque per build, con quattro
  supporti privi di item risonanti per non contaminare il conteggio;
- ogni campione dedicato rispetta l'intervallo PWR `0,80–1,20`; eventuali
  attività comparabili del viaggio iniziale restano correttamente aggiuntive;
- `sample_ready_build_count=81`, tutte le classi sono `ready_for_tuning`,
  tutte le Wave hanno `full_coverage_ready=true` e il gate completo è verde;
- nessuna formula viene modificata automaticamente: i dati aprono la fase di
  revisione degli effetti item e della difficoltà, non buff o nerf ciechi;
- il runner stampa ora diagnostica sicura anche sulle codepage Windows e la
  regressione completa resta `18 passed`.

Undicesima tranche, confronto controllato delle build, completata localmente:

- ogni attività comparabile riceve una coorte stabile composta da tipo di
  contenuto, incontro e impronta anonima della squadra;
- le tre build di una classe vengono confrontate soltanto nelle coorti
  condivise in cui ognuna possiede almeno cinque campioni;
- il report separa potenza totale, equipaggiamento, effetto item e risonanza
  di classe, mostrando per ciascuna build il delta dalla media della classe;
- esiti dungeon e sopravvivenza raid vengono calcolati anche sul solo
  sottoinsieme controllato;
- spread di potenza, effetto item, risonanza ed esiti producono motivazioni
  esplicite di revisione, mai buff o nerf automatici;
- il gate HTTP completo certifica `27/27` classi e `81/81` build pronte nel
  confronto con stesso incontro e stessa squadra;
- il pannello tester mostra copertura controllata e classi da ispezionare con
  motivazioni leggibili;
- regressione isolata aggiornata a `19 passed`; build frontend di produzione
  verde e relativo artefatto locale rimosso.

Dodicesima tranche, coda manuale di tuning, completata localmente:

- ogni classe segnalata riceve un punteggio di gravità da 0 a 100 e una
  severità bassa, media, alta o critica;
- il punteggio combina spread controllato di potenza totale, statistiche
  equip, effetto item, risonanza ed esiti dungeon;
- gli estremi identificano la build più alta e più bassa per ciascun
  componente, preservando l'evidenza che ha generato il segnale;
- l'ambito consigliato distingue `item`, `class_resonance`, `encounter` e
  `mixed`, con un'azione manuale italiana coerente;
- le statistiche base dell'equipaggiamento sono trattate come responsabilità
  item, separatamente dall'effetto eseguibile;
- la coda è ordinata in modo deterministico per gravità, Wave e classe;
- `automatic_change_allowed=false` è obbligatorio su ogni proposta e
  verificato anche dal black-box HTTP completo;
- pannello tester aggiornato con severità, punteggio, ambito, motivazioni e
  prossima azione; regressione `19 passed` e build frontend verde.

Tredicesima tranche, replica ed export finale, completata localmente:

- due squadre di supporto indipendenti confermano ciascuna delle 81 build,
  mantenendo identici incontro e condizioni del confronto;
- 810 spedizioni endgame dedicate producono dieci campioni comparabili per
  build, cinque per ciascuna coorte indipendente;
- il gate di replica certifica `27/27` classi, `81/81` build e almeno due
  coorti condivise per build;
- l'export manuale usa lo schema `t5.manual-tuning.v1`, include proposte e
  sospensioni, mantiene `automatic_change_allowed=false` e possiede hash
  SHA-256 deterministico verificato da due letture HTTP consecutive;
- il pannello mostra copertura, replica, metodologia, azioni manuali e download
  dell'export senza applicare modifiche automatiche;
- verifica visiva reale completata su desktop e viewport mobile 390×844:
  pagina a larghezza piena, nessun overflow orizzontale, export leggibile e
  nessun errore o warning nella console;
- regressione isolata finale `25 passed`; database, porte e artefatto frontend
  temporanei rimossi dopo il collaudo.

Quattordicesima tranche, consolidamento qualità, completata localmente:

- effetto item e risonanza vengono normalizzati contro la propria media, non
  contro la potenza totale;
- la replica richiede due impronte squadra distinte: due incontri diversi con
  la stessa squadra non possono superare il gate;
- i segnali con una sola squadra restano preliminari e finiscono nelle
  sospensioni dell'export, mai nelle proposte confermate;
- timestamp con `Z`, offset diversi o datetime Mongo vengono normalizzati in
  UTC prima di valutare dungeon → raid → nuova build;
- il JSON scaricato è la rappresentazione canonica firmata: l'hash SHA-256
  mostrato coincide con i byte del file;
- `t5_completion_ready` richiede 27 viaggi, 81 build, campioni comparabili e
  replica indipendente completa;
- `set-max` usa tutte le strutture canoniche e prepara 39 avventurieri al
  livello 80 (27 classi e due coorti indipendenti da 6); `set-min` ripristina
  le strutture iniziali, libera gli item
  riservati e garantisce tre avventurieri attivi;
- il runner include i propri test di sicurezza e rifiuta host ambigui, porte
  implicite o privilegiate e URL malformati;
- build produzione e nuovo collaudo desktop/mobile verdi, console pulita e
  teardown verificato senza residui.

T5 è tecnicamente completa. Le sessioni con tester umani, la bonifica della
suite legacy necessaria al rilascio e la validazione su ambienti condivisi
appartengono a T8 e non autorizzano ancora modifiche automatiche di tuning.

### T6 — Pool finale dei 1500 item

**Stato tecnico locale 2026-07-30: COMPLETATO.** Le sessioni con tester
umani e il tuning guidato dalla telemetria restano nel gate T8; non vengono
usati per cambiare automaticamente le percentuali approvate.

- catalogo deterministico `t6.final.v1`: 1500/1500 blueprint;
- quote verificate: `525/375/300/225/60/15`;
- 50 item per ognuna delle 27 classi e 150 universali;
- 135 item Hall conservati e normalizzati, senza riscrivere gli ID Mongo
  esistenti; i record legacy restano compatibili durante la migrazione tester;
- tutti i blueprint hanno nome singolare, lore revisionata, flavor, effetto,
  slot (incluso `material`), livello, binding e acquisizione esplicita;
- 23 dungeon e 4 raid coperti in ogni fascia di rarità dichiarata;
- raid item reward con roll deterministico, ledger idempotente e replay sicuro
  anche dal recupero;
- i dungeon ordinari si fermano a Epico, i raid non rilasciano Unici;
- i 14 Unici non casuali sono traguardi endgame Lv80; l'unico Unico casuale è
  `L'Unico Anello della "Compagnia"` da Alveora, `1/1.000.000`;
- seed Mongo in batch realmente idempotente: prima esecuzione 1500 insert,
  seconda esecuzione 0 insert e 0 modifiche sul database isolato;
- simulazione deterministica: 100.000 iterazioni per ciascuno dei 46 rami
  dungeon e 8 rami raid, zero errori e zero leakage endgame;
- hash catalogo validato:
  `b609d2697a55543841a0a6ee1b1722fd1d7489a04c9ecb97208be3e8add68840`.

- audit e riclassificazione dei 261 item runtime esistenti;
- conservare solo item coerenti, singolari e con fonte verificabile;
- produrre i blueprint mancanti per wave di classe e fonte;
- raggiungere esattamente 525/375/300/225/60/15;
- raggiungere 50 item per ciascuna classe e 150 trasversali;
- richiedere per ogni item nome unico, lore, flavor, effetto, slot, classe,
  livello, fonte, binding e regole di acquisizione;
- validare automaticamente unicità, quote, raggiungibilità e assenza di
  oggetti senza fonte;
- popolare i pool di dungeon e raid soltanto dopo il superamento dei gate;
- eseguire simulazioni, sessioni tester e tuning finale.

### T7 — Set di classe, dopo il catalogo principale

**Stato 2026-07-30: RINVIATA su decisione del proprietario del progetto.**
T8 viene eseguita sul catalogo dei 1500 item individuali; nessun set o bonus
2/4 viene introdotto nella tester release. T7 potrà essere riaperta soltanto
dopo telemetria e feedback reali dei tester.

- progettare i set soltanto usando la telemetria delle build reali;
- bonus combinati leggibili e non obbligatori;
- prima proposta: un set da quattro pezzi per classe, bonus 2/4;
- evitare che i set sostituiscano la varietà dei 1500 item individuali;
- trattare quantità, rarità e inclusione nel totale come contratto separato.

### T8 — Tester release

**Stato tecnico locale 2026-07-30: COMPLETATO.** La release per i tester è
riproducibile e fail-closed; la checklist umana resta distinta e deve essere
compilata dai tester reali, senza trasformarsi in autorizzazione al tuning.

- runner unico T8 con dry-run predefinito e Mongo esclusivamente loopback;
- database temporaneo per esecuzione, teardown garantito e zero residui;
- percorso T5 reale completo: `25 passed` su Mongo e API HTTP isolate;
- gate T6/T8: `40 passed`, quote `525/375/300/225/60/15` e 1500/1500;
- build frontend di produzione verde;
- console Tester Tools con gate tecnici, sei verifiche umane e note;
- controllo reale desktop e mobile 390×844, nessun overflow orizzontale e
  zero errori console;
- razze giocabili inizializzate anche dopo un reset isolato;
- rosa MAX riallineata a 39 e MIN a 3;
- Radici dell'Albero del Mondo riallineate a squadra 7, PWR 1600 e banda
  comparabile 80–120%;
- nessun set di classe incluso, nessun deploy e nessun tuning automatico.

- checklist desktop/mobile e dati resettabili;
- regressione portabile su classless, Hall, equip, dungeon, raid e ricompense;
- audit economico e simulazioni dei drop;
- nessuna scrittura condivisa o produzione senza autorizzazione;
- solo dopo autorizzazione: commit, push e distribuzione.

## Definition of Done finale

La roadmap principale è completa quando un tester può ripetere senza
interventi manuali il ciclo classless → Hall → item → equip → dungeon → raid
→ ricompensa → nuova build per tutte le 27 classi; vede l'impatto degli item
nel risultato; trova fonti e lore comprensibili; dispone di almeno tre identità
di build; il catalogo rispetta esattamente le sei quote e nessun item è privo
di una fonte raggiungibile; la release passa una suite portabile, isolata e
riproducibile. I set di classe restano una fase successiva separata.
