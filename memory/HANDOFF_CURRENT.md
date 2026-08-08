# Orbus Online — Handoff corrente

**Data:** 2026-07-30  
**Repository:** `Orbus-Eye/Orbus-Online-Guild-Master`  
**Branch:** `main-260728`  
**HEAD di partenza:** `780c05894f60c99745e0a94a3a7c337895a86c4a`

## Direzione

- item-first;
- item con identità singolare e forte presenza della lore;
- avventuriero inizialmente senza classe;
- prima scelta identitaria tramite Class Hall;
- 27 classi disponibili e verificabili dai tester.

## Completato nel working tree

### Revamp 2026-07-30

- carriera Comune→Leggendario determinata soltanto da dungeon/raid svolti,
  con moltiplicatori primari ×1/×2/×4/×8/×16 derivati senza alterare le stat base;
- reclutamento RNG e panchina eliminati, cinque fondatori gratuiti e
  costruttore di modelli base per le reclute successive;
- curva lunga fino al livello 80 (`2.817.584 XP` cumulativi);
- dungeon 3/5/7 e raid 10/15/20/40 con builder/preset variabili;
- nomi e lore autorevoli per 23 dungeon e quattro raid;
- dieci slot equipaggiamento e compatibilità legacy `armor → chest`;
- boss mondiale, replay raid, crafting/forgia e Dormitori ricontrollati;
- Unico Anello della "Compagnia" Lv80 seedato e collegato a un solo roll globale 1/1.000.000
  per gilda contribuente alla sconfitta del boss mondiale Alveora;
- sintassi Python e JSX verificata e bundle frontend di produzione compilato;
- la suite backend completa non è eseguibile nell'ambiente corrente perché
  mancano `fastapi`, `python-dotenv` e `pytest-xdist`;
- il comando build standard incontra ancora l'incompatibilità ESLint 9/CRACO,
  ma il bundle compila correttamente escludendo quel solo plugin di lint.

- starter e nuovi reclutamenti classless;
- blocchi coerenti su equip e attività;
- 27 Class Hall con prova, conferma CAS e produzione fail-closed;
- 135 item Hall unici e lore-reviewed;
- progressione di cinque item raggiungibile per tutte le classi;
- seed, indici, idempotenza e concorrenza verificati su Mongo locale isolato;
- 261 item attivi unici nel catalogo persistente, tutti con flavor text;
- Collection Book con filtri, stato, lore, fonte ed effetto;
- reset e smoke matrix per tester;
- equip della signature per 27/27 classi;
- nove spedizioni da tre membri, copertura 27/27;
- 27/27 signature con effetto applicato e spiegato nel report;
- frontend compilato e percorso ispezionato nel browser senza errori.

## Verifiche correnti

```text
unit classless/Class Hall = 16 passed
item effect projection/report = 21 passed
Common lore coverage = 2 passed
final targeted regression = 39 passed
real Mongo effect engine = 116 passed
real Mongo Class Hall = 6 passed
HTTP black-box = 2 passed
FastAPI/OpenAPI = 306 routes / 283 paths
frontend production build = passed
browser QA = passed
shared/prod writes = 0
T8 tecnico = completato; checklist umana separata
```

La suite legacy monolitica è dipendente dal vecchio ambiente (`/app`, SMTP,
fixture pre-popolate, password non più valide, `httpx`). Va bonificata e non
deve essere presentata come verde. I test mirati del nuovo percorso sono verdi.

## Prossimo punto tecnico

Completata la prima tranche T0 del contratto item:

- catalogo target 1500 con quote esatte `525/375/300/225/60/15`;
- rarità `Unique`;
- livello massimo autorevole 80;
- curva PvE su otto fasce, dungeon fino al 70 e raid 40/60/70/80;
- T1 Wave A–E: ventisette meccaniche di classe, ottantuno build item-driven,
  contromisure, parità del budget di potenza e report tester;
- T2 prima tranche: ventitré dungeon canonici, sedici minacce, curva fino al
  livello 70 e anteprima sensibile a classi e item;
- T2 seconda tranche: sessantanove fasi leggibili, ventitré profili ricompensa
  blueprint-only e snapshot exactly-once limitati a Epico;
- T3 riallineata: quattro raid 40/60/70/80, diciassette responsabilità,
  undici fasi e PWR
  sensibile a item/contromisure; Leggendari solo come blueprint raid 80;
- T3 seconda tranche: nove profili esito, token/frammenti tracciabili, CAS sul
  completamento e parità recovery inclusi i bonus Arfus;
- T4 prima tranche: otto politiche fonte, eleggibilità/binding/lockout/dedup e
  Anello isolato sul boss mondiale a `0,0001%`, livello 80, globalmente non
  duplicabile;
- T4 seconda tranche: filtro runtime dungeon, simulatore Anello read-only e
  proiezione anti-inflazione con soglia di revisione;
- T5 prima tranche: percorso Hall → firma → dungeon risonante → raid → grant
  → nuova build certificato dagli snapshot server-owned;
- endpoint read-only e pannello tester mostrano progresso 0/6, telemetria,
  evidenze e primo collo di bottiglia per avventuriero;
- la nuova build conta soltanto dopo il raid ricompensato e soltanto se il
  `build_id` risonante è diverso dal sentiero usato nel dungeon iniziale;
- matrice Wave A–E misura esattamente 27 classi e 81 build, con gate distinti
  per un percorso in ogni Wave e copertura completa di tutte le classi;
- coda tester indica le classi prioritarie e i `build_id` mancanti; snapshot
  con build non canoniche vengono ignorati;
- telemetria tuning aggrega per build successi dungeon, sopravvivenze raid e
  contributi PWR congelati;
- soglia iniziale di cinque campioni per build (`405` totali) prima del
  confronto; le percentuali estreme aprono solo segnali di revisione;
- pannello tester mostra campioni pronti, mancanti e segnali senza applicare
  modifiche automatiche alle formule;
- audit dei kit Hall ha rilevato e corretto una copertura reale iniziale di
  `28/81`: ora tutte le 81 build hanno esattamente un item dichiarato che il
  resolver canonico conferma come attivante;
- seed fail-closed, smoke matrix e HTTP black-box impediscono il ritorno di
  build irraggiungibili;
- Sentiero degli Oggetti e Collection Book mostrano quale build viene
  attivata da ciascuno degli 81 item di percorso;
- Laboratorio Build read-only mostra proprietà/equip dei tre item, build
  corrente, conflitti e prossima azione prima di registrare un campione;
- `isolated_ready` richiede item corretto equipaggiato, build confermata dal
  resolver e zero item concorrenti; nessuna modifica automatica al loadout;
- campioni tuning stratificati per rapporto PWR: sotto 0,80, comparabili
  0,80–1,20, sopra 1,20 e contesto ignoto;
- readiness, success/survival rate e segnali usano soltanto campioni
  comparabili; gli altri restano visibili ma non influenzano il tuning;
- runner T5 fail-closed aggiunto: dry-run predefinito, solo Mongo loopback,
  database per-run in allowlist, serializzazione `-n 0` e cleanup in `finally`;
- regressione T5 reale su MongoDB 8.3 e API loopback gestita: `17 passed`;
  nessun database temporaneo residuo e porta HTTP chiusa;
- fixture PvE allineata al gate livello 5 senza cambiare la nascita classless
  al livello 1;
- gli eventi audit `class_hall_safe_trial_started`,
  `class_hall_safe_trial_completed` e `class_hall_class_committed` non vengono
  più scartati e sono verificati in persistenza;
- Campo d'Addestramento ripristinato come prima attività item-first: livello
  1, difficoltà 1, tre avventurieri; viene ordinato prima dei dungeon normali;
- il Nido delle Fogne resta il primo contenuto di gruppo livello 1, mentre i
  Cunicoli dei Goblin mantengono correttamente il gate livello 5;
- entrambi i black-box HTTP sono verdi: onboarding pubblico completo e reset
  amministrativo ripetibile;
- percorso reale minimo Wave A–E verde: cinque classi rappresentative, cinque
  viaggi Hall → firma → dungeon → raid → grant → nuova build e almeno dieci
  build risonanti osservate;
- il lifecycle raid persiste il grant `applied` e ora supporta da due a otto
  squadre da cinque;
- `set-max` usa il catalogo canonico delle strutture e prepara 39 avventurieri
  al livello 80; `set-min` ripristina strutture, prenotazioni item e rosa 3;
- risolto il 500 del completamento raid causato dall'ombra tra modulo
  `random` e istanza `SystemRandom`;
- terza build sbloccata e provata per i cinque rappresentanti Wave;
- 75 spedizioni endgame reali sulle Radici dell'Albero del Mondo producono
  esattamente cinque campioni comparabili per ciascuna delle 15 build;
- tutte le 15 build sono `sample_ready` e le cinque classi rappresentative
  sono `ready_for_tuning` con copertura 3/3;
- ogni campione è guardato a runtime dall'intervallo PWR `0,80–1,20`; nessun
  campione sotto/sovrapotenziato può essere contato per errore;
- nessuna modifica automatica alle formule è stata applicata sulla sola base
  dei segnali estremi;
- copertura completa T5 verde: 27 reclute scelgono realmente le 27 Hall,
  completano 27 viaggi item-first e osservano tutte le 81 build;
- due raid canonici coprono l'intera rosa rispettando il cooldown globale;
- quattro supporti assegnati ma senza item risonanti isolano il contributo
  della build sotto esame;
- 810 spedizioni endgame dedicate, divise tra due squadre indipendenti,
  garantiscono dieci campioni comparabili per ognuna delle 81 build;
- tutte le 27 classi sono `ready_for_tuning`, tutte le Wave hanno copertura
  completa e `sample_ready_build_count=81`;
- il runner gestisce in modo sicuro anche log non rappresentabili nella
  codepage Windows;
- confronto controllato aggiunto: stesso incontro e stessa impronta squadra
  per tutte le tre build della classe;
- 27 classi e 81 build superano il gate controllato e quello di replica con
  almeno due coorti e dieci campioni condivisi per build;
- ogni build espone delta dalla media di classe per potenza totale,
  equipaggiamento, effetto item e risonanza;
- la coda di revisione normalizzata spiega se il divario riguarda potenza,
  item, risonanza o esiti, senza applicare correzioni automatiche;
- pannello tester aggiornato con copertura controllata e motivazioni italiane;
- coda manuale di tuning ordinata per punteggio 0–100 e severità;
- responsabilità proposta distinta tra item, risonanza, incontro e analisi
  mista, con estremi delle build e spread usati come evidenza;
- statistiche base ed effetto eseguibile dell'item restano componenti
  separati nel report;
- ogni voce impone `automatic_change_allowed=false` e fornisce una prossima
  azione manuale, verificata end-to-end;
- export persistibile `t5.manual-tuning.v1` con payload ordinato e hash SHA-256
  deterministico verificato su richieste HTTP consecutive e sugli stessi byte
  scaricati dal browser;
- replica valida soltanto con due impronte squadra distinte; segnali non
  replicati restano sospensioni preliminari, non proposte;
- ordine temporale normalizzato in UTC e spread item/risonanza corretti contro
  le rispettive medie;
- gate globale `t5_completion_ready` verde soltanto con 27 viaggi, 81 build,
  campioni comparabili e replica completa;
- pannello tester verificato visivamente su desktop e mobile 390×844 senza
  overflow, con replica ed export leggibili e console priva di errori/warning;
- quattro test del runner confermano il rifiuto di Mongo/HTTP non-loopback,
  la selezione seriale della sola suite mirata e il teardown sicuro;
- Leggendari/Unici max-level;
- endpoint audit read-only;
- guard amministrativo delle quote;
- dungeon ordinari senza drop Legendary/Unique;
- Anello riservato come unico roll ultra-raro;
- audit offline JSON/JSONL/BSON;
- snapshot legacy 178: nessun duplicato/fonte mancante; tutti i Leggendari
  sono ora forzati al livello 80;
- 41 test unitari T0 e 25 regressioni T5 mirate real-Mongo/HTTP, inclusi i
  test di sicurezza del runner; build frontend verde;
- T5 tecnicamente completa; porte, database e build temporanei rimossi.

T6 e il gate tecnico T8 sono completati: catalogo 1500/1500, percorso reale
27 classi/81 build, regressione isolata, build frontend e controllo
desktop/mobile verdi. T7 resta rinviata. Il prossimo passo è distribuire il
branch autorizzato e raccogliere la checklist dei tester umani; nessun tuning
automatico viene autorizzato dai soli dati della suite.

## Da preservare

- `memory/BACKLOG.md`: modifica preesistente dell’utente;
- `.vs/`: directory non tracciata preesistente;
- 268 conflitti null legacy: nessuna mutazione senza migrazione dedicata;
- registry da 1500: legacy cinque archetipi, non importare alla cieca;
- nessun commit, push, deploy o scrittura su database condivisi senza mandato.
