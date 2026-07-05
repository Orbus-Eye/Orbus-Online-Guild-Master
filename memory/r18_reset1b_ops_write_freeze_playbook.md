# R18.Reset.1b.ops — Backend Write-Freeze Playbook

**Round:** R18.Reset.1b.ops
**Autore:** e1 main agent
**Data:** 2026-07-05 (UTC)
**Status:** READY FOR REVIEW
**Autorizzazione PM:** brief R18.Reset.1b.ops (Msg 149)
**Piano 1b §16 gate:** copre hard blocker gate 5 (backend_write_freeze)

⚠️ **R18.Reset.1b APPLY resta BLOCKED** in attesa di sign-off PM anche dopo questo playbook. Questo documento sblocca solo il gate 5 del piano 1b §16, non il gate 4 (`pm_sign_off_renewed`).

---

## 1. Come attivare `ORBUS_MAINTENANCE_MODE=true` (comandi esatti)

Ci sono **due metodi**. Il metodo A è quello consigliato per l'apply reale (env var); il metodo B è quello di emergenza / testing (file flag runtime).

### Metodo A — Env var (richiede supervisor restart)

```bash
# 1) Aggiungi la variabile al backend/.env (una riga, senza spazi)
echo 'ORBUS_MAINTENANCE_MODE=true' >> /app/backend/.env

# 2) Riavvia il backend perche' python legga la nuova env
sudo supervisorctl restart backend

# 3) Verifica che il backend sia up
curl -s "$API_URL/api/health" | head -c 200 && echo
```

**Nota:** Il backend legge `os.getenv("ORBUS_MAINTENANCE_MODE", ...)` all'avvio E ad ogni request (via `_is_maintenance_enabled()`). Ma `dotenv.load_dotenv()` in `server.py` popola `os.environ` solo all'import — quindi la modifica al `.env` **richiede restart** per essere riflessa nel process env di uvicorn.

### Metodo B — File flag (runtime, no restart, consigliato per test)

```bash
# Attiva
touch /tmp/orbus_maintenance.flag

# Disattiva
rm -f /tmp/orbus_maintenance.flag
```

Il middleware controlla la presenza del file **ad ogni request** (I/O extra minimo su `Path().exists()`). Toggle immediato, no restart.

Priorità: env var → file flag. Se entrambi sono attivi, il middleware blocca. Se entrambi sono inattivi, il middleware passa tutto.

---

## 2. Come verificare che POST/PUT/PATCH/DELETE rispondano 503 (curl examples)

Sostituisci `$API_URL` con il preview URL (es. `https://guild-master-5.preview.emergentagent.com`).

```bash
API_URL="https://guild-master-5.preview.emergentagent.com"

# POST bloccato
curl -i -X POST "$API_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"x","password":"y"}'
# Atteso:
#   HTTP/1.1 503
#   Retry-After: 60
#   Content-Type: application/json
#   {"detail":"Orbus è temporaneamente in manutenzione. Riprova tra poco."}

# PUT/PATCH/DELETE su endpoint autenticato (anche senza token)
for M in PUT PATCH DELETE; do
    curl -s -o /dev/null -w "$M -> %{http_code}\n" -X $M "$API_URL/api/guilds/me"
done
# Atteso: tutti 503

# GET/HEAD/OPTIONS passano
curl -s -o /dev/null -w "GET   -> %{http_code}\n" "$API_URL/api/health"
curl -s -o /dev/null -w "OPTIONS -> %{http_code}\n" -X OPTIONS "$API_URL/api/health" \
    -H "Origin: http://example.com" -H "Access-Control-Request-Method: POST"
# Atteso: 200 e 200/204 rispettivamente (mai 503)
```

---

## 3. Come eseguire dry-run immediato pre-apply

Con `ORBUS_MAINTENANCE_MODE=true` **già attivo**, esegui il dry-run pre-apply:

```bash
cd /app/backend
python -m app.scripts.round18_reset1b_apply
```

**Atteso:**
- Exit code: `0`
- Log riga iniziale: `MODE = DRY_RUN` (senza flag `--apply`)
- Zero DB mutations (verificabile via snapshot before/after)
- Log line finale: `====== R18.Reset.1b DONE (mode=DRY_RUN) ======`

**Se exit code ≠ 0 → STOP.** Non procedere all'apply. Riporta al PM.

---

## 4. Come generare snapshot-at-apply + manifest sha256

Il backup + manifest sha256 sono generati automaticamente dal `--apply` step S2 di `round18_reset1b_apply.py`. Non serve un comando separato.

Path atteso del backup dopo l'apply reale:
```
/app/backend/backups/r18_reset1b_<TS>/
    manifest.json
    adventurers.jsonl
    inventory_items.jsonl
    ... (33 file JSONL totali)
    guilds.jsonl
```

**Verifica pre-apply che la directory `/app/backend/backups/` sia scrivibile:**
```bash
mkdir -p /app/backend/backups/ && touch /app/backend/backups/.write_test && rm /app/backend/backups/.write_test && echo "backup dir writable"
```

**Verifica sha256 manifest dopo l'apply** (per validare integrità pre-produzione):
```bash
# Trova il backup piu' recente
BACKUP_DIR=$(ls -td /app/backend/backups/r18_reset1b_* | head -1)
echo "Latest backup: $BACKUP_DIR"

# Il tool R18.Reset.1c ha una funzione di verifica sha256 stand-alone
# usabile in DRY_RUN (safe): esegue solo la verifica dei digest, no restore
cd /app/backend
python -m app.scripts.round18_reset1c_restore_from_jsonl_manifest \
    --manifest-path "$BACKUP_DIR/manifest.json"
# In DRY_RUN esegue _verify_sha256_all(). Se sha256 mismatch -> HARD STOP.
```

---

## 5. Come eseguire apply reale R18.Reset.1b (comando esatto con doppio flag)

⚠️ **NON eseguire senza il gate 4 `pm_sign_off_renewed` = SATISFIED.**

Precondizioni obbligatorie (checklist):

- [ ] `ORBUS_MAINTENANCE_MODE=true` attivo (metodo A env var o metodo B file flag).
- [ ] Verificato via curl che POST → 503 (vedi sezione 2).
- [ ] Dry-run pre-apply eseguito e exit 0 (vedi sezione 3).
- [ ] Dir `/app/backend/backups/` scrivibile (vedi sezione 4).
- [ ] Piano 1b §16 gate 4 `pm_sign_off_renewed` = SATISFIED.
- [ ] Piano 1b §16 gate 5 `backend_write_freeze` = SATISFIED (questo playbook).
- [ ] Testers dormono / traffic minimo.

**Comando apply reale:**

```bash
cd /app/backend
python -m app.scripts.round18_reset1b_apply \
    --apply \
    --i-understand-this-will-reset-all-guilds
```

**Atteso:**
- Log riga iniziale: `MODE = APPLY` (entrambi i flag rilevati)
- Step S2 crea `/app/backend/backups/r18_reset1b_<TS>/` con `manifest.json` + 33 JSONL
- Step S3 esegue `aggregate($out)` per 32 archive collections
- Step S4 esegue `delete_many({})` sulle 32 live collections
- Step S5 esegue `update_many` su 672 (o count effettivo) guild
- Step S6 esegue `insert_many` di 5 avventurieri per guild (starter roster)
- Step S7 esegue `insert_many` di 3 pozioni per guild (starter kit)
- Step S8 emette audit event `R18_FULL_GUILD_FRESH_START_APPLIED`
- Exit code: `0`

**Se qualsiasi step fallisce → vai alla sezione 8 (Rollback path).**

---

## 6. Come verificare post-apply (checklist)

Dopo apply reale (exit 0), esegui le seguenti verifiche **prima** di disattivare maintenance mode:

```bash
API_URL="https://guild-master-5.preview.emergentagent.com"

# 6a. audit event applied presente
python3 -c "
import asyncio, os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')
async def go():
    c = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = c[os.environ['DB_NAME']]
    n = await db.audit_log.count_documents({'event_type':'R18_FULL_GUILD_FRESH_START_APPLIED'})
    print(f'audit APPLIED events = {n} (expect >=1)')
asyncio.run(go())
"

# 6b. Verifica che le 32 archive collection esistano ora
python3 -c "
import asyncio, os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')
async def go():
    c = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = c[os.environ['DB_NAME']]
    all_c = await db.list_collection_names()
    arch = sorted([x for x in all_c if x.endswith('_r18_archive')])
    print(f'archive collections created: {len(arch)} (expect 32)')
asyncio.run(go())
"

# 6c. Guild count invariato (identity preserved, ma field resettati)
python3 -c "
import asyncio, os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')
async def go():
    c = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = c[os.environ['DB_NAME']]
    guilds_total = await db.guilds.count_documents({})
    with_reset_marker = await db.guilds.count_documents({'r18_reset1b_applied': True})
    print(f'guilds total = {guilds_total} (expect same as pre-apply)')
    print(f'guilds with r18_reset1b_applied=True = {with_reset_marker}')
asyncio.run(go())
"

# 6d. Sanity smoke test (con maintenance ancora ON, quindi GET only)
curl -s "$API_URL/api/health" | head -c 200 && echo
curl -s "$API_URL/api/openapi.json" -o /dev/null -w "openapi: %{http_code}\n"
```

Se qualcosa non torna → NON disattivare maintenance mode → vai alla sezione 8.

---

## 7. Come disattivare `ORBUS_MAINTENANCE_MODE=false`

### Se hai usato il metodo A (env var):

```bash
# 1) Rimuovi la variabile dal .env
sed -i '/^ORBUS_MAINTENANCE_MODE=/d' /app/backend/.env
# (oppure setta a false: sed -i 's/^ORBUS_MAINTENANCE_MODE=true/ORBUS_MAINTENANCE_MODE=false/' /app/backend/.env)

# 2) Riavvia il backend
sudo supervisorctl restart backend

# 3) Verifica ritorno normale
curl -s -o /dev/null -w "POST /api/auth/login -> %{http_code}\n" \
    -X POST "https://guild-master-5.preview.emergentagent.com/api/auth/login" \
    -H "Content-Type: application/json" -d '{"email":"x","password":"y"}'
# Atteso: 401 (o 400), NON 503
```

### Se hai usato il metodo B (file flag):

```bash
rm -f /tmp/orbus_maintenance.flag
# Nessun restart necessario. Effetto immediato al prossimo request.
```

---

## 8. Rollback path se qualcosa fallisce (link a R18.Reset.1c)

Se l'apply reale di R18.Reset.1b fallisce o produce output inatteso:

### 8a. Immediate freeze
1. **NON disattivare `ORBUS_MAINTENANCE_MODE`** (mantieni il write-freeze).
2. **NON toccare le collection live** o gli archive.

### 8b. Localizza il backup
```bash
BACKUP_DIR=$(ls -td /app/backend/backups/r18_reset1b_* | head -1)
ls "$BACKUP_DIR/manifest.json" || echo "MANIFEST MISSING - CRITICAL"
```

Se il manifest **non esiste** o l'apply non è arrivato allo step S2 → escalation immediata al PM. Il rollback JSONL non può procedere senza backup.

### 8c. Rollback via `round18_reset1c_restore_from_jsonl_manifest.py`

**PRIMA il dry-run (obbligatorio):**
```bash
cd /app/backend
python -m app.scripts.round18_reset1c_restore_from_jsonl_manifest \
    --manifest-path "$BACKUP_DIR/manifest.json"
# Atteso exit 0, sha256 verify PASS, "R18.Reset.1b APPLY REMAINS BLOCKED"
```

**Se dry-run OK e PM autorizza, apply reale del rollback:**
```bash
python -m app.scripts.round18_reset1c_restore_from_jsonl_manifest \
    --manifest-path "$BACKUP_DIR/manifest.json" \
    --confirm-rollback
# Attesa emissione audit event R18_FULL_GUILD_FRESH_START_ROLLED_BACK
```

### 8d. Post-rollback verify
```bash
# audit event ROLLED_BACK presente
python3 -c "
import asyncio, os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')
async def go():
    c = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = c[os.environ['DB_NAME']]
    n = await db.audit_log.count_documents({'event_type':'R18_FULL_GUILD_FRESH_START_ROLLED_BACK'})
    print(f'ROLLED_BACK audit events = {n}')
asyncio.run(go())
"
```

### 8e. Solo dopo rollback verified → disattiva maintenance
Segui la sezione 7 SOLO dopo che il rollback è verificato e PM ha dato OK.

### Reference documenti
- Report R18.Reset.1c (rollback completeness): `/app/memory/r18_reset1c_rollback_completeness_report.md`
- Script rollback: `/app/backend/app/scripts/round18_reset1c_restore_from_jsonl_manifest.py`
- Piano 1b §16 human approval gate: `/app/memory/r18_reset1b_full_guild_fresh_start_apply_plan.md`

---

## Test evidence

Playbook validato in dry-run via test suite 8/8 PASS. Log dettagliato: `/app/memory/r18_reset1b_ops_test_report.txt`. Snapshot DB during-maintenance verify: `/app/memory/r18_reset1b_ops_isolated_before.json` vs `..._isolated_after.json` → `DIFF_VERDICT: CLEAN`.

**R18.Reset.1b APPLY resta BLOCKED.** Questo playbook chiude il gate 5 di §16. Gate 4 (`pm_sign_off_renewed`) resta PENDING in attesa del brief PM esplicito post-review.

*Firma: e1 main agent — 2026-07-05T08:20:46Z*
