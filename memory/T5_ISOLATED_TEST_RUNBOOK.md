# T5 — Esecuzione isolata del percorso tester

## Stato rilevato il 29 luglio 2026

La macchina espone MongoDB 8.3 soltanto su `127.0.0.1:27017` e non dispone
di Docker. È stato creato un ambiente Python temporaneo, separato dalla
repository, per eseguire lo stack backend mirato. Il test HTTP resta escluso
finché non viene avviata un'API collegata a un database sacrificabile.

## Runner fail-closed

`backend/app/scripts/t5_isolated_playtest_runner.py` prepara ed esegue
soltanto la regressione T5 mirata:

- percorso verticale tester;
- raggiungibilità delle 81 build;
- Laboratorio Build;
- integrazione Class Hall su Mongo reale isolato;
- test HTTP black-box solo con consenso esplicito aggiuntivo.

Il runner:

- è dry-run per impostazione predefinita;
- disabilita il caricamento del `.env` nel processo controllato;
- imposta `APP_ENV=test`, `MONGO_URL` loopback e un `DB_NAME` univoco in
  allowlist; il cleanup globale può quindi toccare soltanto quel DB per-run,
  che viene eliminato dal runner in `finally`;
- impedisce al fixture globale di sovrascrivere questo contesto controllato
  con un eventuale `tests/.env.test`;
- accetta soltanto `mongodb://127.0.0.1:27017`;
- non accetta credenziali, SRV o nomi database;
- usa i database unici in allowlist creati e rimossi dalla fixture;
- forza la suite mirata in seriale con `-n 0`;
- rifiuta HTTP non-loopback;
- richiede `--confirm-isolated-http-db` prima del test HTTP, che scrive dati.

## Sequenza operativa

Da `backend`, con un ambiente Python che contiene `requirements.txt`:

1. avviare un Mongo locale sacrificabile su `127.0.0.1:27017`;
2. eseguire l'anteprima:
   `python -m app.scripts.t5_isolated_playtest_runner`;
3. controllare che moduli mancanti siano vuoti e Mongo sia raggiungibile;
4. eseguire:
   `python -m app.scripts.t5_isolated_playtest_runner --run`;
5. percorso raccomandato per includere HTTP con API, porta e database gestiti
   automaticamente dal runner:
   `python -m app.scripts.t5_isolated_playtest_runner --run
   --start-isolated-http`;
6. per collaudare invece un'API loopback già avviata su un database separato
   e sacrificabile, aggiungere:
   `--include-http --http-base-url http://127.0.0.1:8000
   --confirm-isolated-http-db`.

Il flag HTTP è una conferma operativa: il runner può verificare che l'origine
sia locale, ma non può dimostrare dall'esterno quale database usi l'API.

## Ultima evidenza

Ultima esecuzione locale del 30 luglio 2026:

- `25 passed` nella regressione mirata T5 su MongoDB 8.3 e API gestita,
  inclusi i quattro test dei guardrail del runner;
- zero database temporanei `orbus_r16_rt2b_it_*` dopo il teardown;
- porta HTTP gestita chiusa dopo il teardown;
- unica segnalazione: deprecazione futura di `multipart` in Starlette,
  non bloccante e non collegata alla logica di gioco;
- entrambi i black-box HTTP verdi: onboarding item-first e reset tester.
- percorso minimo A–E verde: cinque viaggi completi, un raid reale da 20 e
  almeno dieci build risonanti osservate.
- copertura completa verde: 27 viaggi item-first, 81 build con copertura 3/3
  e 810 spedizioni endgame dedicate;
- ogni build ha dieci campioni comparabili e tutte le Wave espongono
  `full_coverage_ready=true`;
- due squadre indipendenti di quattro supporti senza item risonanti impediscono
  contaminazioni e forniscono cinque campioni per coorte e per build;
- due raid canonici coprono tutte le 27 classi rispettando il cooldown globale.
- confronto controllato e replica verdi: 27 classi e 81 build condividono
  almeno due coorti indipendenti, stesso incontro e cinque campioni per coorte;
- delta di equipaggiamento, effetto item e risonanza sono esposti senza
  applicare modifiche automatiche.
- la coda controllata è ordinata per gravità e assegna un ambito manuale:
  item, risonanza, incontro o analisi mista;
- ogni proposta espone punteggio, severità, motivazioni ed estremi delle
  build, mantenendo `automatic_change_allowed=false`.
- export `t5.manual-tuning.v1` deterministico: proposte e sospensioni possiedono
  payload ordinato e hash SHA-256 identico su due letture HTTP consecutive;
- il browser scarica il JSON canonico esatto: l'hash coincide con i byte del
  file e non soltanto con il contenuto logico;
- una replica richiede due impronte squadra distinte; segnali osservati con una
  sola squadra restano preliminari e non diventano proposte;
- `t5_completion_ready` certifica con un solo gate 27 viaggi, 81 build,
  campioni comparabili e replica indipendente completa;
- UI verificata su desktop e viewport mobile 390×844: nessun overflow
  orizzontale, pannello replica/export leggibile e console senza errori/warning.

## Gate

Gate tecnico T5 completato il 30 luglio 2026:

- preflight interamente verde;
- regressione mirata real-Mongo verde;
- API locale collegata a DB sacrificabile;
- black-box HTTP verde;
- nessuna scrittura su preview, staging o produzione.

Tutti i gate sopra sono verdi. T5 è tecnicamente completa e può passare alle
sessioni tester umane previste in T8; queste sessioni non autorizzano tuning
automatico né scritture su ambienti condivisi.
