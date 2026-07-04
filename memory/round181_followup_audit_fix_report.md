# R18.1 Follow-up Report — Audit Observability Fix + Sub-3b Closure

**Data:** 2026-07-04
**Trigger:** `e1_tester` FAIL su TEST 4 (audit events R18_*) + HUMAN_REQUIRED su TEST 3b
**Autore:** e1 main agent
**Scope:** append-only, idempotent, feature-flag-OFF-compatibile

---

## 1. Root Cause Analysis — TEST 4 FAIL

### Diagnosi
Il main migration script `round181_schema_foundation.py` emette i 7 audit event R18_* via:
```python
await db.audit_events.insert_one({...})
```

Ma il **feed admin `/api/admin/audit/events`** (definito in `app/admin/audit_routes.py:170`) legge:
```python
await db.audit_log.find({...})
```

**Collezioni diverse.** Quello che il PM/tester vede via API è `audit_log` (6965 doc, 86 tipi distinti). Gli event R18_* stavano in `audit_events` (37 doc totali, 28 R18_*).

### Query diagnostiche eseguite (read-only)
```
[audit_events] total=37  R18_*=28
[audit_log]    total=6965 R18_*=0     ← qui l'API guarda
[audit_logs]   total=143  R18_*=0
[system_events] total=0
```

Confermato: **event mai leaked nell'audit_log admin feed** e whitelist di 64 tipi non li includeva.

### Perché la migration originale ha usato `audit_events`
`audit_events` è una collection ereditata da script/migration precedenti (usata anche da `round180_pm_decision_matrix.md` e simili audit tools). Il developer del main script ha preso la collection sbagliata come default — errore di observability, non di dati.

---

## 2. Fix applicato — Opzione B (retroactive emit)

### 2.a Nuovo script backfill (append-only, idempotent)
**File creato:** `/app/backend/app/scripts/round181_audit_log_backfill.py` (144 righe)

**Contract:**
- Legge il **primo** doc per event_type da `audit_events` (fonte di verità per timestamp originali + metadata operativi)
- Emette **1 event summary** per tipo in `audit_log` con schema conforme (id, event_type, actor_*, source, item_slug/template/quantity/gold_delta=None, metadata, created_at)
- **Metadata trasparente:**
  - `metadata.is_retroactive = True`
  - `metadata.round = "R18.1"`
  - `metadata.original_occurred_at = <timestamp_da_audit_events>`
  - `metadata.original_source = "script.round181_schema_foundation"`
  - + metadata operativi preservati (orphans_found, count, mapping, distribution, ecc.)
- **Idempotency:** check `{event_type, metadata.round=R18.1, metadata.is_retroactive=True}` — se già presente, skip
- **Guardrail flag:** feature flag `R18_REWORK_ENABLED` NON toccato (backfill puramente observability)

### 2.b Whitelist admin audit aggiornata
**File modificato:** `/app/backend/app/admin/audit_routes.py` (righe 113-123)

Aggiunti 7 event_type al `AUDIT_EVENT_WHITELIST` frozenset con commento:
```python
# ROUND 18.1 — Adventurer Identity & Schema Foundation (retroactive
# summary events emitted by `round181_audit_log_backfill.py`. Feature
# flag R18_REWORK_ENABLED remains OFF; these are observability-only).
"R18_MIGRATION_STARTED",
"R18_MIGRATION_COMPLETED",
"R18_ORPHAN_MARKED_UNASSIGNED",
"R18_GUARDIAN_CLERIC_ALIASED",
"R18_GRADE_BACKFILLED",
"R18_ROSTER_CAP_COMPUTED",
"R18_BETA_FIELD_PREPARED",
```

Effetto: il feed accetta il filtro `event_type=R18_*` senza 422; il default scope include gli event R18_* nel default listing.

### 2.c Comandi eseguiti
```bash
# 1. Dry-run (0 write)
python -m app.scripts.round181_audit_log_backfill --dry-run
  → 7 event marcati per emit, 0 already present

# 2. Apply
python -m app.scripts.round181_audit_log_backfill --apply
  → Inserted 7/7 retroactive event summaries into audit_log.
  → [verify] audit_log R18_* total: 7 (expected ≥ 7) ✅

# 3. Idempotency (2nd apply)
python -m app.scripts.round181_audit_log_backfill --apply
  → Inserted 0/7 retroactive event summaries into audit_log.
  → [verify] audit_log R18_* total: 7 ✅ IDEMPOTENT
```

---

## 3. Idempotenza fix verificata

| Run | Inserted | Total in audit_log R18_* |
|---|---|---|
| Dry-run | 0 (preview) | 0 (pre-apply) |
| Apply #1 | 7 | 7 |
| Apply #2 | 0 (all skip) | 7 |

Confermato via `count_documents({event_type: {$regex: "^R18_"}})` = 7 dopo entrambi gli apply.

---

## 4. Whitelist admin audit — 7 event_type verified

Test HTTP con Bearer token admin/tester su `$REACT_APP_BACKEND_URL/api/admin/audit/events?event_type=<evt>`:

| event_type | http_code | items.total |
|---|---|---|
| R18_MIGRATION_STARTED | 200 | 1 |
| R18_MIGRATION_COMPLETED | 200 | 1 |
| R18_ORPHAN_MARKED_UNASSIGNED | 200 | 1 |
| R18_GUARDIAN_CLERIC_ALIASED | 200 | 1 |
| R18_GRADE_BACKFILLED | 200 | 1 |
| R18_ROSTER_CAP_COMPUTED | 200 | 1 |
| R18_BETA_FIELD_PREPARED | 200 | 1 |

**Zero 422/403/500.** Response valid con `metadata.is_retroactive=true` visibile al PM.

Esempio payload (R18_MIGRATION_STARTED):
```json
{
  "id": "272baeeb-e169-4e91-8e5b-c8641a615f5a",
  "event_type": "R18_MIGRATION_STARTED",
  "source": "script.round181_audit_log_backfill",
  "metadata": {
    "round": "R18.1",
    "is_retroactive": true,
    "original_occurred_at": "2026-07-04T17:34:33.092623+00:00",
    "original_source": "script.round181_schema_foundation",
    "orphans_found": 91,
    "guardian_cleric_found": 6,
    "grade_missing": 2125
  },
  "created_at": "2026-07-04T17:52:58.852081+00:00"
}
```

---

## 5. Query finale di verifica

```
db.audit_log.count_documents({event_type: {"$regex": "^R18_"}}) → 7  ✅ ≥ 7
db.audit_log.distinct("event_type", {event_type: {"$regex": "^R18_"}}) →
  ['R18_BETA_FIELD_PREPARED', 'R18_GRADE_BACKFILLED',
   'R18_GUARDIAN_CLERIC_ALIASED', 'R18_MIGRATION_COMPLETED',
   'R18_MIGRATION_STARTED', 'R18_ORPHAN_MARKED_UNASSIGNED',
   'R18_ROSTER_CAP_COMPUTED']  ✅ 7 tipi distinti
```

**Migration observability chiusa.**

---

## 6. Sub-3b closure — Expedition guardrail status

### Scelta: Opzione B (test diagnostic read-only)

Il PM ha chiesto di verificare **via unit test / query read-only** che esista un guardrail in `POST /api/expeditions/*` che rifiuti `class_slug` fuori catalogo canonico OR `is_playable=false`.

### Findings (verifica su codice + DB)
Ho scannato `/app/backend/app/expeditions/*.py` (15 file: routes, services, formulas, preview, ecc.) cercando riferimenti a `recruit_unassigned` e `is_playable`:

```
grep -r "recruit_unassigned\|is_playable" app/expeditions/
→ Nessun match. Zero guardrail R18.3 pre-esistente.
```

**Questo è coerente col brief R18.1**: 
- SOFT enforcement, feature flag `R18_REWORK_ENABLED=false`
- Class-bound HARD gate è pianificato per **R18.3**, non R18.1
- Un guardrail introdotto ora sarebbe fuori scope e violerebbe il vincolo "zero player-facing UI/behavior change"

### Test diagnostic aggiunto
**File modificato:** `/app/backend/tests/backend_round181_migration_test.py`  
**Nuovo test:** `test_18_expedition_guardrail_status_r181_baseline`

Verifica tre condizioni:
1. La class doc `recruit_unassigned` ha `is_playable=False, is_talent_tree_eligible=False, drops_items=False` (barrier concettuale, non runtime)
2. Feature flag `R18_REWORK_ENABLED=false` → nessun enforcement runtime
3. **Fail-fast guard:** il codice `app/expeditions/*.py` NON contiene `recruit_unassigned` né `is_playable` — se un futuro merge introducesse guardrail R18.3 in anticipo (fuori brief), il test fallirebbe

### Aspettative comportamento attuale (R18.1)
- **POST /expeditions**: **NON** rifiuta `recruit_unassigned`. Nessun guardrail attivo. Coerente.
- **UI Recruitment / Adventurers list**: **NON** mostra gli 85 orfani `recruit_unassigned` — verificato da tester in TEST 3.
- **Effetto pratico:** un adventurer con `class_slug=recruit_unassigned` è invisibile via UI, quindi **impossibile da selezionare in un dispatch UI**. La "protezione" è per omissione, non enforced.

### Roadmap chiara
Il guardrail HARD (400/403 su class_slug non-canonical o `is_playable=false`) è **P0 di R18.3** (Grade + Tomi + Roster 50 enforce + Class-Bound HARD). Non appartiene a R18.1 e non è stato implementato.

---

## 7. 3 constraint invariati — conferma

1. ✅ **ZERO HARD DELETE**  
   Verificato: `round181_audit_log_backfill.py` esegue solo `insert_one` in `audit_log`. Zero delete. Il main migration script `round181_schema_foundation.py` non è stato toccato.

2. ✅ **ZERO PLAYER-FACING UI CHANGES**  
   Nessun file `/app/frontend/**` modificato. `/api/guilds/me`, `/api/adventurers`, `/api/dungeons` — nessun cambio comportamento.

3. ✅ **ZERO MODIFICHE A ECONOMIA / PvP / PREMIUM / DROP / REWARD / AUTO-EQUIP / COMBAT MATH**  
   Fix limitato a:
   - Scrittura in `audit_log` (7 doc summary, observability-only)
   - Aggiunta 7 stringhe al `AUDIT_EVENT_WHITELIST` frozenset in `audit_routes.py` (nessuna logica di gameplay)
   - Aggiunta 2 test in `backend_round181_migration_test.py` (diagnostic-only)

---

## Deliverable finali (file toccati)

| File | Tipo | Righe | Scope |
|---|---|---|---|
| `/app/backend/app/scripts/round181_audit_log_backfill.py` | CREATED | 144 | Retroactive emit script |
| `/app/backend/app/admin/audit_routes.py` | MODIFIED | +11 (whitelist) | Admin API whitelist R18_* |
| `/app/backend/tests/backend_round181_migration_test.py` | MODIFIED | +80 (2 nuovi test) | test_17, test_18 |
| `/app/memory/round181_followup_audit_fix_report.md` | CREATED | this file | Follow-up report |

**Test suite R18.1 finale:** `18/18 PASSED in 0.09s` ✅

---

## Comandi riproducibili

```bash
# Verifica R18_* in audit_log
python3 -c "
import asyncio
from dotenv import dotenv_values
from motor.motor_asyncio import AsyncIOMotorClient
env = dotenv_values('/app/backend/.env')
c = AsyncIOMotorClient(env['MONGO_URL'])
async def m():
    n = await c[env['DB_NAME']].audit_log.count_documents({'event_type': {'\$regex': '^R18_'}})
    print(f'R18_* in audit_log: {n}')
asyncio.run(m())
"

# HTTP verifica admin feed
curl -s "\$REACT_APP_BACKEND_URL/api/admin/audit/events?event_type=R18_MIGRATION_STARTED" \
  -H "Authorization: Bearer \$TOKEN" | python3 -m json.tool

# Test suite R18.1 (18 test)
cd /app/backend && PYTHONPATH=/app/backend python -m pytest \
  tests/backend_round181_migration_test.py -c /dev/null \
  -p no:cacheprovider --confcutdir=/tmp -v

# Rollback backfill (emergenza)
python3 -c "
import asyncio
from dotenv import dotenv_values
from motor.motor_asyncio import AsyncIOMotorClient
env = dotenv_values('/app/backend/.env')
c = AsyncIOMotorClient(env['MONGO_URL'])
async def r():
    res = await c[env['DB_NAME']].audit_log.delete_many({
        'metadata.round': 'R18.1',
        'metadata.is_retroactive': True,
        'source': 'script.round181_audit_log_backfill'
    })
    print(f'rolled back: {res.deleted_count}')
asyncio.run(r())
"
```

---

**Firmato:** e1 main agent · 2026-07-04 · R18.1 Follow-up chiuso · Pronto per re-test `e1_tester`
