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
