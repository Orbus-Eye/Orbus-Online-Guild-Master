# R18.Reset.1b.ops — Backend Write-Freeze Playbook

> **Status:** CLOSED & SEALED (PM authorized on 2026-07-05T08:36:37Z)
> **Tester independent verification:** 8/8 PASS
> **Middleware:** /app/backend/app/core/maintenance.py
> **Wiring:** /app/backend/app/core/app_factory.py (dopo CSRF, esegue primo)

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

Sostituisci `$API_URL` con il preview URL (es. `https://drain-dispatch.preview.emergentagent.com`).

```bash
API_URL="https://drain-dispatch.preview.emergentagent.com"

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
API_URL="https://drain-dispatch.preview.emergentagent.com"

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
    -X POST "https://drain-dispatch.preview.emergentagent.com/api/auth/login" \
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

---

## Internal Job Freeze (R18.Reset.1b.hotfix.write_freeze_full)

Il `MaintenanceMiddleware` HTTP (gate 5) copre solo POST/PUT/PATCH/DELETE
inviati dai client. I **job async interni** (lifespan boot, GET-triggered
sweep, on-visit resolver) BYPASSANO il freeze HTTP. Questa sezione documenta
il **secondo layer** di freeze — `ORBUS_INTERNAL_JOB_FREEZE` — che li ferma.

### 1. Attivazione (runtime, no restart)

Metodo A — env var (richiede supervisor restart):
```bash
export ORBUS_INTERNAL_JOB_FREEZE=true
sudo supervisorctl restart backend
```

Metodo B — file flag (RUNTIME, nessun restart):
```bash
touch /tmp/orbus_internal_job_freeze.flag
```

Entrambi i metodi vengono riletti a OGNI invocazione del decorator
`@frozen_when_active`. Non c'e' caching.

### 2. Verifica che `orbus.onboarding.starter_roster` venga skippato

```bash
# Trigger manuale del boot (o attendi un hot-reload)
sudo supervisorctl restart backend
# Attendi ~10s
tail -n 20 /var/log/supervisor/backend.err.log | grep "Internal job skipped"
```

Log WARN atteso (esempio):
```
orbus.job_freeze - WARNING - Internal job skipped due to
ORBUS_INTERNAL_JOB_FREEZE — job=orbus.onboarding.starter_roster_for_all_guilds
```

### 3. Uso combinato HTTP maintenance + Internal Job Freeze

ORDINE PRE-APPLY (obbligatorio):
```bash
# 1. Attiva HTTP maintenance (gate 5)
touch /tmp/orbus_maintenance.flag
# 2. Attiva Internal Job Freeze (gate 7)
touch /tmp/orbus_internal_job_freeze.flag
# 3. Verifica entrambi
curl -X POST $REACT_APP_BACKEND_URL/api/auth/login \
  -H "Content-Type: application/json" -d '{}' -o /dev/null -w "%{http_code}\n"
# Atteso: 503
# 4. Ora esegui l'apply script v1.1 (in un'altra shell)
python -m app.scripts.round18_reset1b_apply_v1_1 --apply \
  --i-understand-this-will-reset-all-guilds
```

I due flag sono INDIPENDENTI: puoi disattivarne uno senza l'altro.

### 4. Disattivazione post-apply

```bash
rm -f /tmp/orbus_maintenance.flag
rm -f /tmp/orbus_internal_job_freeze.flag
# Verifica
curl -X POST $REACT_APP_BACKEND_URL/api/auth/login \
  -H "Content-Type: application/json" -d '{"email":"","password":""}' \
  -o /dev/null -w "%{http_code}\n"
# Atteso: 401 (o 400 - non piu' 503)
```

### 5. Escalation — cosa fare se un job scrive durante freeze

Se durante un apply reale rilevi che un job async interno HA scritto
(check `audit_log` per timestamp durante freeze window):

1. **STOP immediato** dell'apply (Ctrl+C sullo script v1.1).
2. Nota `event_type`, `actor_guild_id`, `source`, `created_at` dell'evento.
3. **Aggiungi il job al inventory** in
   `r18_reset1b_hotfix_write_freeze_full_job_inventory.md`.
4. Apri un round hotfix follow-up per patchare quel job specifico.
5. Non riprendere l'apply finche' il gap non e' chiuso.

### 6. Comandi verifica per job coperti (12/12)

```bash
# Job L1 — starter_roster
grep "Internal job skipped.*starter_roster" /var/log/supervisor/backend.err.log

# Job L5 — bound fields backfill
grep "Internal job skipped.*backfill_bound_fields" /var/log/supervisor/backend.err.log

# Job L7 — signature inventory backfill
grep "Internal job skipped.*backfill_missing_signature" /var/log/supervisor/backend.err.log

# Job L9 — release_tester_roster
grep "Internal job skipped.*release_tester" /var/log/supervisor/backend.err.log

# Job L10 — forge migration
grep "Internal job skipped.*run_forge_migration" /var/log/supervisor/backend.err.log

# Job R1/R2/R3 — sweep GET-triggered (test con GET /api/guilds/me)
curl -X GET $REACT_APP_BACKEND_URL/api/guilds/me -H "Authorization: Bearer $TOKEN"
grep "Internal job skipped.*(complete_due_expeditions|auto_resolve_stuck_raids|_resolve_expired_missions)" \
  /var/log/supervisor/backend.err.log

# Job D1/D2/D3/D4 — route-triggered resolvers (idem)
grep "Internal job skipped.*(legendary_forge|arfus_forge|world_boss|pvp_continental)" \
  /var/log/supervisor/backend.err.log
```

### 7. Live evidence del gap chiuso da gate 7

Durante il hot-reload backend del **2026-07-05T10:21:55Z** (Fase A del
seal R18.Reset.1b.hotfix), il lifespan boot ha scritto **2 adventurers**
sulla guild live `907b4ae4-8301-4852-bd65-b4e3937824f7` PRIMA dell'attivazione
del internal freeze:

```
orbus.onboarding - INFO - starter roster seeded:
  guild=drain-dispatch inserted=2
```

Dopo la patch B.2 del gate 7 hotfix (2026-07-05T10:56Z), lo stesso
trigger ha prodotto invece un `inserted=5` PRIMA dell'attivazione del
freeze — perche' il decorator `@frozen_when_active` legge il flag SOLO
quando attivo. Ecco perche' **il freeze DEVE essere attivato PRIMA**
del real apply, non dopo.

Il test 11 (`t11_gap_evidence_lifespan_starter_roster_frozen`) dimostra
formalmente che con freeze ON, il lifespan trigger produce
`inserted=0` + WARN log + return dict controllato. **Gap architetturale
chiuso.**
