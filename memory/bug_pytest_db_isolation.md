# Bug Pytest DB Isolation — Diagnosi (STEP F)

Data: 2026-07-01 13:25 UTC
Ambito: `/app/backend/tests/` (esclusi `_legacy`, `__pycache__`)

## Sintomo osservato durante il recovery
Il DB attivo `orbus_r16` è passato da **3 gilde e 15 avventurieri** (subito dopo il lifespan boot) a **152 gilde e ~880 avventurieri** in ~20 minuti. Le nuove gilde hanno tutte nomi pattern chiaramente da test suite: `R6B2A eda667`, `R5 35af5`, `R4 Guild DDB814`, `R112T14 fb4f0c`, `OC 3da6fd`, `P13Hero_*`, ecc. Il cleanup script `round14_cleanup_archive_demo_guilds.py` le ha correttamente identificate come junk (148/148 archiviate, 0 false positive).

**Causa**: quando pytest è stato lanciato (`python -m pytest tests/`) durante il recovery, i test hanno usato `MONGO_URL` e `DB_NAME` presi direttamente dal `.env` del backend → hanno scritto sul **DB attivo di produzione preview** invece che su un DB di test isolato.

## Analisi statica di `tests/conftest.py`

Path: `/app/backend/tests/conftest.py` (~1120 righe).

Il file:
1. **Carica il .env del backend con `load_dotenv(backend/.env)`** senza override — `DB_NAME` e `MONGO_URL` sono ereditati.
2. Poi carica `tests/.env.test` con `override=True`. Se il file esistesse e definisse `DB_NAME=orbus_r16_test`, farebbe l'override. **Attualmente il file esiste solo come template `.env.test.example`**, non come `.env.test`.
3. Ha una safety rail `_is_test_db()` che ritorna True se `APP_ENV in {"test", "testing", "ci"}` OPPURE se il `DB_NAME` matcha certi pattern (probabilmente `*_test`). Se ritorna False, i cleanup delle pollution pattern vengono skippati per sicurezza.
4. Definisce `ALLOWLIST_EMAILS` e `ALLOWLIST_GUILDS_LOWER` (email/nomi di giocatori reali) come frozenset — ogni cleanup che chiama `delete_many` DEVE filtrare per escludere allowlist. Questo è per la safety, non per l'isolation.
5. Contiene `TEST_POLLUTION_PATTERNS` (regex per identificare users/guilds/adventurers/items/dungeons/classes/traits di test): compressa via cleanup solo se `_is_test_db()==True`.

## Sorgente della fuga: singoli test file bypassano `conftest`

Ho grep-ato l'uso diretto di `MONGO_URL`/`DB_NAME` nei test:
```
backend_round13b_seasonal_increment_test.py:39    AsyncIOMotorClient(os.environ["MONGO_URL"]); client[os.environ["DB_NAME"]]
backend_phase55gh_smoke_test.py:42-46, 166, 189   MongoClient(MONGO_URL)[DB_NAME].adventurers.delete_many(...)
backend_round6e_respec_test.py:26-33              MongoClient(MONGO_URL)[DB_NAME]
backend_round6b2a_guards_test.py:25-33            MongoClient(MONGO_URL)[DB_NAME]
backend_phase19_2_raid_review_smoke_test.py:34-42 MongoClient(MONGO_URL)[DB_NAME]
```
Altri test file hardcodano il fallback:
```
backend_phase55gh_smoke_test.py:46  ..., "DB_NAME", "test_database"
backend_phase5_test.py:232          os.environ.get("DB_NAME", "test_database")
backend_phase8_test.py:35           return "test_database"
backend_phase6_test.py:45           return "test_database"
backend_phase7_test.py:38           return "test_database"
backend_phase55e_smoke_test.py:49   ..., "DB_NAME", "test_database"
```

Ogni test file apre la sua propria `AsyncIOMotorClient`/`MongoClient` puntando alla stessa `MONGO_URL` e leggendo `DB_NAME` dall'env → i test **scrivono direttamente sul DB attivo** (`orbus_r16` post-recovery, `test_database` pre-recovery). I fallback `"test_database"` sono un artefatto storico: quando `DB_NAME=test_database` era la config default, coincideva col DB attivo, e non c'era mai stata isolation vera.

## Proposta di isolamento (SOLO DIAGNOSI, NON IMPLEMENTATA)

### Opzione 1 (minima, low-risk)
Creare `/app/backend/tests/.env.test` (gitignored, template esiste come `.env.test.example`) con:
```
DB_NAME=orbus_r16_test
APP_ENV=test
```
`conftest.py` già carica `tests/.env.test` con `override=True`. Dopo questa modifica, tutti i test che usano `os.environ["DB_NAME"]` durante l'esecuzione di pytest vedranno `orbus_r16_test` invece di `orbus_r16`.

**Pro**: modifica minima, no code change nei test file.
**Contro**: se un test lancia un subprocess che carica solo `.env` (senza `.env.test`), rimane esposto. Ma non ci sono subprocess in questi test — usano tutti in-process client.

### Opzione 2 (robusta, medio-risk)
Modificare `conftest.py` per esportare `os.environ["DB_NAME"]` in una fixture `session`:
```python
@pytest.fixture(scope="session", autouse=True)
def isolate_test_db():
    orig = os.environ.get("DB_NAME")
    os.environ["DB_NAME"] = os.environ.get("TEST_DB_NAME", "orbus_r16_test")
    yield
    if orig: os.environ["DB_NAME"] = orig
```
Con `autouse=True` la fixture parte in automatico per ogni test session, e `os.environ["DB_NAME"]` risulta cambiato prima che qualsiasi `AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]` venga eseguito.

**Pro**: garantisce isolation senza toccare test file.
**Contro**: alcuni test file possono aver già valutato `DB_NAME` a module-level (top-of-file). Verifica caso per caso.

### Opzione 3 (definitiva ma invasiva)
Refactor: centralizzare `MONGO_URL`/`DB_NAME` in una fixture `db_test` e obbligare tutti i test file a passare tramite quella. Richiede grep+rewrite di ~40 file di test.

### Teardown / cleanup
Dopo l'isolation, il DB `orbus_r16_test` va **droppato tra un run e l'altro** (dropDatabase del DB TEST è sicuro, mai del DB principale). Il conftest attuale ha già una funzione di cleanup post-test che elimina pattern (users/guilds/adventurers con nomi test) — con l'isolation attiva basta chiamare `db.dropDatabase()` di `orbus_r16_test` prima del session start.

## Verifica sicurezza aggiuntiva (safety rail)
Suggerimento: aggiungere un check assert in `conftest.py` che **rifiuti l'esecuzione se `DB_NAME` non finisce con `_test`** o se `APP_ENV != "test"`. Esempio:
```python
assert os.environ["DB_NAME"].endswith("_test") or os.environ.get("APP_ENV") == "test", \
    "REFUSE: pytest attempted to run against non-test DB. Set DB_NAME=<something>_test or APP_ENV=test"
```

## Blacklist da evitare
Le seguenti operazioni sono **VIETATE** anche dopo isolation:
- `drop_database(<any name>)` a livello di test **senza** verificare che il nome finisca in `_test`.
- Chiamare `delete_many({})` (senza filtro) su qualsiasi collection.
- Modificare la ALLOWLIST del conftest a runtime.

## Verdetto STEP F
- **Bug confermato**: nessun isolation attivo tra pytest e DB preview/dev. I test scrivono direttamente.
- **Impatto storico**: 148 gilde junk create durante l'incident recovery. Già cleanup-ate al 100% dallo script `round14_cleanup_archive_demo_guilds.py`.
- **Correzione consigliata (NON APPLICATA da me)**: Opzione 1 + safety rail. Modifiche minime, non richiedono rewrite dei test file.
- **NON esiste il file `tests/.env.test`**, solo il template. Basta crearlo con `DB_NAME=orbus_r16_test` per bloccare la fuga.

## Cosa NON ho fatto
- ❌ Non ho eseguito full pytest (rispettata la regola).
- ❌ Non ho creato `tests/.env.test` (attendo tua autorizzazione).
- ❌ Non ho modificato `conftest.py`.
- ❌ Non ho modificato alcun test file.
