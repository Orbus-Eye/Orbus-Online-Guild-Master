# Pytest DB Isolation Policy (Round 16.3 Iter B, P2.1)

**Data**: 01 Luglio 2026
**Stato**: ATTIVA ✅
**Autore**: E1 (main agent)

---

## Regola fondamentale

**Pytest DEVE scrivere SOLO sul DB test dedicato `orbus_r16_test`, MAI sul DB dev/preview `orbus_r16`.**

Questa policy è enforced automaticamente da un guard-rail hardcoded in `/app/backend/tests/conftest.py` che viene eseguito a **conftest import time** (prima di qualsiasi test module).

---

## Come funziona l'isolation

### 1. File `.env.test` (gitignored)
Path: `/app/backend/tests/.env.test`

Contiene le override che pytest applica:
```
DB_NAME=orbus_r16_test
APP_ENV=test
```

Ordine di caricamento in `conftest.py`:
1. `load_dotenv(backend/.env)` → carica `DB_NAME=orbus_r16` (dev)
2. `load_dotenv(tests/.env.test, override=True)` → **sovrascrive** con `DB_NAME=orbus_r16_test`

### 2. Guard-rail hardcoded

Subito dopo il caricamento `.env.test`, `conftest.py` asserta:

```python
_db_name_looks_testy = (
    _pytest_db_name.endswith("_test")
    or "test" in _pytest_db_name.lower()
)
_app_env_is_test = _pytest_app_env in {"test", "testing", "ci"}
if not (_db_name_looks_testy or _app_env_is_test):
    raise RuntimeError("REFUSING to run pytest against non-test DB: ...")
```

Se `DB_NAME` non contiene la stringa `test` E `APP_ENV` non è `test/testing/ci`, pytest **si rifiuta di avviare** con un errore chiaro.

### 3. Comportamento nei test file

I test file che ri-caricano `.env` con `load_dotenv(backend/.env)` **SENZA `override=True`** vedono ancora `orbus_r16_test` perché:
- `python-dotenv` con `override=False` (default) NON sovrascrive variabili già in `os.environ`
- `conftest.py` ha già impostato `os.environ["DB_NAME"]=orbus_r16_test` prima che qualsiasi test module venga importato

**Regola per autori di test**: usare `load_dotenv(path)` (senza `override=True`) oppure meglio ancora leggere direttamente da `os.environ`.

---

## Come verificare che l'isolation sia attiva

```bash
cd /app/backend
python -m pytest tests/test_forge_actions_p0.py -v 2>&1 | head -5
# Aspettato: nessun errore "REFUSING to run pytest..."

# Verifica DB usato:
python -c "
import os
os.environ.pop('DB_NAME', None)
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path('/app/backend/.env'))
load_dotenv(Path('/app/backend/tests/.env.test'), override=True)
print('DB_NAME =', os.environ['DB_NAME'])
print('APP_ENV =', os.environ.get('APP_ENV'))
"
# Aspettato:
# DB_NAME = orbus_r16_test
# APP_ENV = test

# Dopo pytest, verifica che orbus_r16_test esista in mongo:
mongosh --quiet --eval 'db.getMongo().getDBNames().filter(n => n.startsWith("orbus"))'
# Aspettato: ["orbus_r16", "orbus_r16_test"]
```

---

## Cosa NON è protetto (limitazioni note)

1. **Subprocess che caricano solo `backend/.env`**: nessun subprocess simile è attualmente presente nei test, ma se venissero introdotti in futuro dovrebbero anch'essi propagare `DB_NAME=orbus_r16_test`.

2. **Test che chiamano `MongoClient(url)[hardcoded_name]`**: alcuni legacy test hardcodano `"test_database"` come fallback. Con la nuova policy, questi test scrivono in `test_database` (che è vuoto/orfano nel preview), NON in `orbus_r16`. Nessun impatto sul DB dev.

3. **Il guard-rail non impedisce `drop_database("orbus_r16")`** se qualcuno lo chiama esplicitamente. La blacklist qui è aggiuntiva:
   - MAI chiamare `drop_database(<any name>)` senza verificare `.endswith("_test")`
   - MAI `delete_many({})` (senza filtro) su qualsiasi collection
   - MAI modificare `ALLOWLIST_EMAILS` / `ALLOWLIST_GUILDS_LOWER` a runtime

---

## Verifica applicata (P2.1)

- ✅ `/app/backend/tests/.env.test` esteso con `DB_NAME=orbus_r16_test` + `APP_ENV=test`
- ✅ `/app/backend/tests/conftest.py` guard-rail hardcoded aggiunto (righe 22-46)
- ✅ Documento policy creato (questo file)
- ✅ Test targeted eseguiti per verificare che il DB test sia usato (vedere `round163_debt_p2_report.md`)

---

## Change history

| Data | Modifica | Autore |
|---|---|---|
| 2026-07-01 | Policy creata, isolation attivata (Round 16.3 Iter B P2.1) | E1 main agent |
| 2026-07-01 | **P3.1 HTTP admin bypass fixato** — fixture `isolated_backend_url` + autouse env override quando `ISOLATED_HTTP_TESTS=1` | E1 main agent |

---

## P3.1 — HTTP admin bypass isolation (Round 16.3 Iter C)

### Problema originale

I test HTTP che colpiscono `REACT_APP_BACKEND_URL` bypassavano il guard-rail DB isolation, perché il backend running su :8001 gestito da supervisor usa `backend/.env` → `DB_NAME=orbus_r16` (DB dev). Risultato: test HTTP scrivevano su `orbus_r16` invece che `orbus_r16_test`.

### Strategia scelta: **Opzione B — second uvicorn instance opt-in**

Motivazione della scelta:
- ✅ Backend prod-dev (:8001) **rimane completamente intoccato**: browser dev-preview continua a funzionare durante i test
- ✅ Zero rischio di race con supervisor auto-restart
- ✅ Isolation è opt-in (env flag) → backward-compat totale con test esistenti
- ✅ Fixture pytest gestisce lifecycle: spawn + health check + teardown automatici
- ✅ Se il subprocess non risponde in 30s → RuntimeError esplicito, mai silent-fallback su prod DB

Alternative scartate:
- ❌ **Env var + supervisor restart**: complicato lifecycle, race conditions, browser dev-preview interrotto
- ❌ **Monkey-patch database module**: molto invasivo, non traccia bene errori runtime

### Implementazione

In `/app/backend/tests/conftest.py`:

```python
@pytest.fixture(scope="session")
def isolated_backend_url() -> str:
    if os.environ.get("ISOLATED_HTTP_TESTS") == "1":
        proc = _spawn_isolated_backend()  # uvicorn :8002 con DB_NAME=orbus_r16_test
        try: yield "http://127.0.0.1:8002"
        finally: proc.terminate()
    else:
        yield os.environ.get("REACT_APP_BACKEND_URL") or ""

@pytest.fixture(scope="session", autouse=True)
def _apply_isolated_backend_env(isolated_backend_url):
    # Override transparente REACT_APP_BACKEND_URL quando isolated attivo
    if os.environ.get("ISOLATED_HTTP_TESTS") == "1":
        os.environ["REACT_APP_BACKEND_URL"] = isolated_backend_url
    yield
```

### Attivazione

```bash
cd /app/backend
ISOLATED_HTTP_TESTS=1 python -m pytest tests/ -n 0
```

Nota: `-n 0` (serial) è necessario perché il subprocess uvicorn è single-instance. Xdist workers riusano lo stesso port :8002 (safe: solo il controller spawna).

### Evidence P3.1 (2026-07-01)

Snapshot `orbus_r16` PRE / POST `pytest tests/test_stables_phase8_v1.py` con `ISOLATED_HTTP_TESTS=1`:

| Collection | PRE | POST | Match |
|---|---|---|---|
| `guild_mount_ownership` | 2 | 2 | ✅ |
| `narrative_route_completions` | 0 | 0 | ✅ |
| `pvp_seasons` | 15 | 15 | ✅ |
| `guilds` | 153 | 153 | ✅ |
| `adventurers` | 890 | 890 | ✅ |

**Risultato**: 5/5 collezioni INVARIATE. Le scritture confluiscono in `orbus_r16_test`. Isolation funziona end-to-end.

### Note sui test skip in modalità isolated

I test `test_14_set_active_not_owned_returns_403` e `test_15_travel_narrative_route_wrong_domain_returns_403` sono marcati `pytest.skip` quando `ISOLATED_HTTP_TESTS=1`, perché dipendono dallo stato "vergine" del tester account. Nel DB test lo stato del tester è non-deterministico (accumulato tra run). Le stesse assertion sono coperte in modo decoupled da `test_17` e `test_18` che usano fixture guild dedicate `p8v1_guild_0` sotto controllo direct-DB.

### Uso raccomandato

- **Sviluppo/CI locale**: `ISOLATED_HTTP_TESTS=1` per garanzia hard isolation
- **Smoke test rapido dev**: default (senza flag), tocca prod-dev DB come prima
- **Full pytest safe**: `ISOLATED_HTTP_TESTS=1 pytest tests/ -n 0` con snapshot pre/post per doppia verifica
