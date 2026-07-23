# R18.6.RV3-IS2-B-P2B-RT2-B-1B-P0 · Mongo Runtime-State Provisioning Readiness & Isolated Integration Plan

**Regime**: `DOCUMENTAL_ONLY · READ-ONLY DISCOVERY · Italian_only · NO APPLY · SHA Policy §31 · STRICT STOP`
**Gate ID**: `R18.6.RV3-IS2-B-P2B-RT2-B-1B-P0 · MONGO PROVISIONING READINESS PLAN`
**Ancoraggio invariante**: `lore_meta.py` SHA256 = `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`
**Fonte upstream**: `R18.6.RV3-IS2-B-P2B-RT2-B-1A · CLOSED · PM-LOCKED` (Store Contract & non-wired adapter foundation)
**Status**: `ARTIFACT WRITTEN · PM ADJUDICATION REQUIRED · FORMAL CLOSURE HOLD`

---

## Section 1 · Executive Summary

Il gate `RT2-B-1B-P0` produce un piano documentale, evidence-based e read-only, per il **provisioning fisico** della collection Mongo che ospiterà lo stato di runtime delle spedizioni (`expedition_runtime_states`), il set di indici (identity + TTL + recovery), il modello permessi in 3 profili (provisioning · runtime · diagnostic), l'ambiente di integration-test isolato, la procedura di rollback e la matrice di failure. Il gate **non crea alcuna collection, alcun indice, alcun documento**; non modifica alcun servizio applicativo; non attiva alcun feature flag; non collega la libreria RT2-B-1A al runtime.

**Raccomandazione**: `HOLD-PENDING-PM-DECISIONS`. Le 12 domande `B1BQ01..B1BQ12` richiedono adjudication PM prima di autorizzare `RT2-B-1B (apply)`. Due aree presentano indeterminatezza operativa **elevata** (evidence-based) che il PM deve chiarire: (a) target database prod vs dev boundary (`B1BQ02`) e (b) modello di identità Mongo con separazione dei privilegi (`B1BQ04`/`B1BQ05`).

---

## Section 2 · Scope

**In scope (documentale)**: piano di provisioning, index set, TTL semantics, identity model, isolated integration-test env, rollback, failure matrix, capacity envelope, PM open questions, GO/HOLD recommendation.

**Out of scope (proibito in questo gate)**: Mongo collection creation · index creation · TTL index creation · DB writes · provisioning script execution · migration execution · runtime adapter wiring · expedition service modification · feature flag activation · real integration-test writes su Mongo · uso di credenziali production · OpenAPI / frontend / Registry / item generation.

---

## Section 3 · Governance

- Regime `DOCUMENTAL_ONLY · READ-ONLY DISCOVERY · Italian_only`.
- `lore_meta.py` invariant · anchor SHA `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`.
- Baseline chain `10/10 byte-identical`: IS2-A · IS2-B-P1 · IS2-B-P1-N1 · IS2-B-P2A · IS2-B-P2B-1 · IS2-B-P2B-RT1 · IS2-B-P2B-RT2-P0 · IS2-B-P2B-RT2-A · IS2-B-P2B-RT2-B-P0 · IS2-B-P2B-RT2-B-1A.
- `sealed integrity tests = 6 passed` · `sealed artifacts = 36/36 byte-identical` (verificato post-scrittura).
- `NEW SEAL = NO`.
- PRD **invariato** (SHA riferimento post-RT2-B-1A `53e57f14187ad67344b9af80ac5b78471b3a064faf1f7c6cdbdffd4bb93ba7b9`): nessun append RT2-B-1B-P0 in questo gate.
- Nessun closure manifest in fase P0 (draft state).
- SHA Policy §31: nessuno SHA embedded nei propri artefatti — dichiarati solo nel chat report finale.

---

## Section 4 · Source Chain

Provenienza documentale del gate `RT2-B-1B-P0`:

| # | Upstream artifact | Status |
|---|---|---|
| 1 | `RT2-B-P0` — Foundation Runtime Discovery Report | PM-LOCKED |
| 2 | `RT2-A` — CDV & Effect Engine · 24 code + 14 test | PM-LOCKED |
| 3 | `RT2-B-1A` — Store Contract & non-wired adapter (14 file) | PM-LOCKED |
| 4 | `RT2-B-1A` — Implementation Report MD (`77dc4172…`) | INVARIANT |
| 5 | `RT2-B-1A` — Implementation Report JSON (`bc92e363…`) | INVARIANT |
| 6 | `RT2-B-1A` — Final Closure MD/JSON + Manifest (`e0fc5adb…` / `4bbb1daf…` / `d848bc0e…`) | PM-LOCKED |
| 7 | Backend Mongo client init (`app/core/database.py:9`) | READ-ONLY EVIDENCE |
| 8 | Index provisioning (`app/core/indexes.py`) | READ-ONLY EVIDENCE |
| 9 | Startup lifespan (`app/core/lifespan.py`) | READ-ONLY EVIDENCE |
| 10 | Pytest DB isolation policy (`/app/memory/pytest_db_isolation_policy.md`) | READ-ONLY EVIDENCE |

---

## Section 5 · Mongo Environment Discovery

**Evidenza empirica raccolta in sola lettura**:

### 5.1 Client initialization
- File: `/app/backend/app/core/database.py:9`
- Riga: `mongo_client: AsyncIOMotorClient = AsyncIOMotorClient(MONGO_URL)`
- Pattern: **singleton top-level** istanziato all'import; condiviso via `db = mongo_client[DB_NAME]`.
- Consequenza: **un solo profilo credenziali** attivo per l'intero backend. Nessuna separazione runtime/provisioning/diagnostic implementata a livello di connection pool.

### 5.2 Environment variables (`/app/backend/.env`)
- `MONGO_URL="mongodb://localhost:27017"` — **senza autenticazione**, **senza TLS**, host locale.
- `DB_NAME=orbus_r16` — database dev/preview.
- `APP_ENV="development"`.
- **Nessun secret store** referenziato (Vault/KMS/AWS SM) nel codice esplorato.

### 5.3 Naming conventions
Collection esistenti (estratto da `indexes.py` + moduli ensure_*): `users · guilds · adventurer_classes · adventurer_traits · adventurers · recruitment_offers · dungeons · items · expeditions · expedition_members · inventory_items · equipped_items · login_attempts · refresh_tokens · password_reset_tokens · squads · guild_structures · audit_log · market_* · consortium_* · chat_* · shop_* · seasons · pvp_* · rewards · achievements · class_halls · dashboard_* · world_boss · world · world_events · site_income_* · resources · legendary_forge · arfus_forge · trade_pacts · guild_specialization · pvp_season · stables · mounts_* · continent_events` · ecc.
- Pattern: `snake_case`, plural nouns.
- **`expedition_runtime_states`** aderisce alla convenzione.

### 5.4 Existing provisioning path
- Model **C attualmente attivo**: `app/core/lifespan.py` invoca `create_all_indexes(db)` + oltre 20 `ensure_*_indexes()` domain-scoped al boot.
- `create_index` di pymongo/motor è **idempotente** (no-op se spec matches).
- Pattern osservato: **implicit collection creation** via primo `create_index()` o primo write; nessun `db.create_collection(...)` esplicito nella codebase applicativa.

### 5.5 Existing TTL indexes (evidenza)
- `login_attempts.last_attempt_at` · `expireAfterSeconds = LOGIN_ATTEMPTS_TTL_SECONDS` (constante da `app.shared.constants`).
- `refresh_tokens.expires_at` · `expireAfterSeconds = 0` (Date-driven).
- `password_reset_tokens.expires_at` · `expireAfterSeconds = 0` (Date-driven).
- **Il pattern `expireAfterSeconds=0` con campo `expires_at` BSON `Date`** è già in produzione e riusabile per il design candidato.

### 5.6 Application Mongo permissions
- `MONGO_URL` locale senza credenziali → runtime process ha **root-equivalent** su Mongo locale.
- **Nessuna evidenza di `createUser`/`role`/`grantRolesToUser`** nel codice applicativo.
- **Nessuna evidenza empirica di production Mongo boundary** (credenziali separate, cluster remoto, TLS). Il preview URL `guild-master-5.preview.emergentagent.com` è definito, ma non c'è mapping esplicito a un `MONGO_URL` prod separato in `.env`.

### 5.7 Deployment environment configuration
- Supervisor configs: `/etc/supervisor/conf.d/supervisord.conf` (backend/frontend), `supervisord_code_server.conf`, `supervisord_nginx_proxy.conf`, `webhook-crond.conf`.
- **Nessun Dockerfile, nessun docker-compose, nessun manifest Kubernetes** nel repository esplorato (`/app`).
- **Nessuna CI directory** (`.github/`, `.gitlab-ci.yml` assenti).

### 5.8 Preview vs production database boundary
- `.env` corrente indica `APP_ENV="development"` con `DB_NAME=orbus_r16`.
- **Non è determinabile in questo P0**, dalla sola evidenza codice, l'ambiente di produzione con certezza — configurazione probabilmente iniettata a deployment-time. **PM_REVIEW → `B1BQ02`**.

### 5.9 Backup configuration
- Dump manuali in `/app/_mongo_dumps/` (evidenza: `adventurers_deprecated_pre_migrate_20260701_*.json`, `fresh_20260701_120426/`).
- Script applicativi con `_backup_snapshot()` in `app/scripts/round18_reset1b_apply_v1_1.py:256` (backup verso `/app/backend/backups/…`).
- **Nessun backup automatico schedulato · nessun PITR configurato · nessun cross-region snapshot** individuato.

### 5.10 Monitoring infrastructure
- `grep prometheus|grafana|datadog|newrelic|sentry` sul codebase applicativo → **zero risultati significativi** (una menzione in `security.py:183` come metric-hash placeholder, non integrazione).
- **`MONITORING_BASELINE_MISSING`** — nessuna infrastruttura di metriche/traccia integrata.

### 5.11 Alerting infrastructure
- **Nessuna evidenza empirica** di regole alert configurate (né Prometheus AlertManager, né PagerDuty/OpsGenie).

### 5.12 Test Mongo fixtures
- `/app/backend/tests/conftest.py:11-49` — **hard guard-rail** al conftest import time: rifiuta esecuzione pytest se `DB_NAME` non contiene `test` o `APP_ENV` non è `test/testing/ci`.
- `/app/backend/tests/.env.test` — override di `backend/.env` per test (linea 25 conftest).
- `_ISOLATED_BACKEND_PORT = 8002` — fixture `isolated_backend_url` che spawna un uvicorn subprocess con `DB_NAME=orbus_r16_test` + `APP_ENV=test` (conftest linee 296-340).

### 5.13 Local Mongo (dev)
- Mongo locale in ascolto su `localhost:27017` (evidenza `MONGO_URL`).
- Presenza `orbus_r16` (dev) e — implicitamente disponibile per il pattern isolated fixture — `orbus_r16_test`.

---

## Section 6 · Naming Conventions

- Collection candidate name: **`expedition_runtime_states`** — `snake_case`, plural noun, allineata al pattern osservato.
- Index naming candidate (proposto, PM_REVIEW): `expedition_runtime_states_id_unique`, `expedition_runtime_states_expires_at_ttl`, `expedition_runtime_states_status_expires_idx` (opzionale, recovery), `expedition_runtime_states_lease_expires_idx` (opzionale).
- Nessuna collisione lessicale con collection esistenti.
- **`player-facing export inclusion = forbidden`** (la collezione NON deve comparire in export cliente, leaderboard, chronicle player-facing).

---

## Section 7 · Candidate Collection

- **Nome candidato**: `expedition_runtime_states` · `PM_REVIEW` per adjudication finale (`B1BQ01`).
- **Naming collision**: `NONE` (grep evidence: 3 riferimenti trovati nel codebase — tutti dentro il package RT2-B-1A o test schema, nessuno in `indexes.py`/`lifespan.py`).
- **Existing collection**: `NOT PRESENT` in nessuna path di provisioning applicativa.
- **Database target proposto**: `orbus_r16` (dev/preview) + `orbus_r16_test` (test isolato). `PM_REVIEW → B1BQ02` per production DB name.
- **Environment scope**: dev + preview + test isolato. Production **PM_REVIEW**.
- **Player-facing export**: `FORBIDDEN` (runtime-only state, no chronicle/leaderboard/export inclusion).
- **Analytics ingestion**: `DISABLED_BY_DEFAULT` (nessuna pipeline analytics documentata al momento; nessun requisito imposto in RT2-B-1A).

---

## Section 8 · Document Lifecycle

Schema documento candidato (già validato dai contratti frozen dataclass in `models.py`):

| Campo | Tipo | Note |
|---|---|---|
| `_id` / `expedition_id` | string | UUID4; `_id = expedition_id` (dedup index nativo) |
| `state_version` | int64 | Monotonic; initial `1`; incrementato a ogni CAS mutation |
| `runtime_status` | string enum | `active` · `completed` · `cancelled` · `expired` |
| `owner_lease_id` | string \| null | Writer lease ID corrente |
| `fencing_token` | int64 | Incrementa a ogni nuova acquisizione lease |
| `lease_expires_at` | Date (BSON) | Scadenza lease writer |
| `last_event_sequence` | int64 | Sequence server-authoritative |
| `loadout_snapshot_version` | int32 | Riferimento snapshot loadout |
| `adventurer_class_states` | array of subdocs | Marks/Drains/FragmentUsage per adventurer_id |
| `processed_event_receipts` | array bounded (`RECEIPT_RING_CAP`) | Ring-buffer con fail-closed su cap |
| `created_at` | Date (BSON) | UTC · immutable |
| `updated_at` | Date (BSON) | UTC · aggiornato ad ogni mutation |
| `expires_at` | Date (BSON) | UTC · **TTL driver** · aggiornato ad ogni mutation attiva; ricalcolato a `now + retention` su terminal state |

**Lifecycle stati**:
- `active` → `expires_at = now + active_inactivity_ttl` (default candidate: 6h)
- `completed` / `cancelled` → `expires_at = terminal_transition_time + terminal_retention_ttl` (default candidate: 24h)
- TTL monitor rimuove il documento quando `expires_at <= now`.

**Rischio Mongo 16 MB**:
- `processed_event_receipts` è bounded → nessuna crescita illimitata.
- `adventurer_class_states` limitato dal numero di adventurer per squad (≤ 4-6 per party attesa) × sub-strutture bounded → **envelope << 1 MB atteso**.
- Nessun payload denormalizzato di dungeon/item catalog nel documento.

---

## Section 9 · Index Requirements

Set indici valutato (ciascuno con giudizio evidence-based):

| # | Nome candidato | Chiave | Tipo | Required | Query servita | Cardinality | Write amp | Note |
|---|---|---|---|---|---|---|---|---|
| I1 | (native `_id`) | `_id` | native | REQUIRED | `find_one_and_update`, `find_one` per expedition_id | 1:1 | 0 | `_id = expedition_id`; nessun campo duplicato richiesto |
| I2 | `expedition_runtime_states_expires_at_ttl` | `expires_at` | TTL (`expireAfterSeconds=0`) | REQUIRED | Cleanup automatico documenti scaduti | high (equal to doc count) | +1 per update | Pattern identico a `refresh_tokens_ttl`/`password_reset_ttl` |
| I3 | `expedition_runtime_states_status_expires_idx` | `runtime_status, expires_at` | compound | OPTIONAL — `PM_REVIEW` | Query recovery per stati attivi vicini a expiry | medium | +1 per update | Serve solo se recovery-scan diventa una feature |
| I4 | `expedition_runtime_states_lease_expires_idx` | `lease_expires_at` | single | OPTIONAL — `PM_REVIEW` | Lease reaper (scavenger job) | medium | +1 per update | Serve solo se implementiamo lease reaper esplicito. In assenza → TTL fa già cleanup |
| I5 | `expedition_runtime_states_updated_at_idx` | `updated_at` | single | OPTIONAL — `PM_REVIEW` | Analytics/diagnostic | medium | +1 per update | Non giustificato senza query dimostrabile |

**Raccomandazione baseline (minima)**: `I1 + I2`. `I3/I4/I5` richiedono query dimostrata per essere autorizzati — evitare indici "per sicurezza". `PM_REVIEW → B1BQ06`.

**Note tecniche indice TTL**:
- Tipo BSON `Date` obbligatorio per `expires_at` (Mongo TTL monitor ignora stringhe ISO).
- Aggiornamento a **ogni mutation** (parte del CAS filter update payload).
- Comportamento su documenti terminali: `expires_at` ricalcolato a `terminal_transition_time + retention_ttl`.
- **TTL monitor lag**: Mongo esegue il TTL sweep ogni 60s in media, **non deterministico**. `NO immediate deletion expectation`.
- **Nessuna aspettativa di eliminazione entro un tempo garantito**.

---

## Section 10 · TTL Semantics

Baseline candidate (non APPLY-LOCKED in P0, `PM_REVIEW → B1BQ07`):

| Stato | TTL default | Meccanismo |
|---|---|---|
| `active` (inactivity) | **6 hours** dall'ultima mutation | `expires_at = updated_at + 6h` |
| `completed` (terminal) | **24 hours** dal transition | `expires_at = terminal_ts + 24h` |
| `cancelled` (terminal) | **24 hours** dal transition | `expires_at = terminal_ts + 24h` |
| `expired` (grace) | **0** (immediate cleanup on next TTL sweep) | Documento eligibile a rimozione al prossimo sweep |

**Calcolo `expires_at`**:
- Owner: **runtime writer** (store adapter) sotto CAS filter.
- Update trigger: ogni `compare_and_update` / `apply_event_once` / `renew_writer_lease` aggiorna `expires_at`.
- Terminal states: `expires_at = terminal_transition_ts + terminal_retention_ttl`.

**Distinzione active vs terminal**:
- Il campo `runtime_status` è la source of truth.
- Recovery: uno stato `active` con `expires_at` in prossimità della scadenza può essere resurrezionato da un writer che re-acquire il lease.
- Un writer non può ripristinare uno stato `expired` (fail-closed).

**Interazione con backup**: vedere Section 19.

---

## Section 11 · Permissions

Modello identity a **3 profili distinti**, non ancora implementato empiricamente (`MONGO_PERMISSION_MODEL_UNDERDEFINED` → `PM_REVIEW`):

### 11.1 Provisioning identity
- Ruolo Mongo: `dbAdmin` scoped al database target OPPURE ruolo custom `provisioning_role`.
- Grants richiesti: `createCollection`, `createIndex`, `dropIndex`, `dropCollection`, `listCollections`, `listIndexes`.
- Presenza: **SOLO durante provisioning/rollback autorizzato**. Credenziali NON caricate nel processo applicativo runtime.
- Rotazione: prima e dopo ogni finestra provisioning.

### 11.2 Runtime identity
- Ruolo Mongo: custom `runtime_role`.
- Grants richiesti: `find`, `insert`, `update`, `findAndModify` (per CAS), `delete` — **limitati alla collection `expedition_runtime_states`** (`{db: <target>, collection: "expedition_runtime_states"}`).
- **NON deve avere**: `createCollection`, `createIndex`, `dropCollection`, admin database-wide, `dropDatabase`.
- Caricato nel processo applicativo attraverso env var scoped (es. `RUNTIME_MONGO_URL`) — NON deve coincidere con `MONGO_URL` legacy.

### 11.3 Diagnostic identity
- Ruolo Mongo: `read` scoped alla collection `expedition_runtime_states`.
- Grants richiesti: `find`, `listIndexes` (solo la collection target).
- **Nessun accesso** a payload sensibili o credenziali applicative.
- Uso: dashboard operativi, incident response, forensic replay read-only.

**Attuale stato empirico**: **un unico profilo** (`MONGO_URL="mongodb://localhost:27017"` senza credenziali) → `MONGO_PERMISSION_MODEL_UNDERDEFINED`. `PM_REVIEW → B1BQ04` + `B1BQ05`.

---

## Section 12 · Provisioning Models

### 12.1 Model A · Explicit idempotent administrative command
- Descrizione: script CLI eseguito da operator con `provisioning identity`; idempotente; esce con report.
- Pro: **massima auditabilità**, credenziali provisioning isolate temporalmente, rollback-friendly.
- Contro: richiede runbook operator; non-automatic per environment neonati.
- **PM baseline preference**: SÌ.

### 12.2 Model B · Deployment migration/provisioning step
- Descrizione: step CI/CD (es. `helm hook`, `k8s Job`) eseguito una tantum al deploy.
- Pro: automatico, tracciabile via pipeline.
- Contro: **richiede infrastruttura CI/CD** attualmente **non presente** nel repo (vedere §5.7); mescola provisioning e deploy artifacts.
- Fattibilità: bassa nel P0 corrente.

### 12.3 Model C · Application startup ensure-collection/indexes
- Descrizione: `lifespan.py` invoca `create_index()` idempotenti al boot con **runtime identity**.
- Pro: pattern **attualmente in uso** per tutte le collection esistenti.
- Contro: **incompatibile con il modello permessi §11** — richiede al runtime `createIndex` (e implicitamente `createCollection` al primo write), violando least-privilege.
- Aggravante: startup provisioning writes = **NOT RECOMMENDED** dal PM baseline.

### 12.4 Raccomandazione
**Model A** (explicit idempotent administrative command + separate read-only verification command) con verifica idempotente + report SHA-tracked. **PM_REVIEW → B1BQ03**.

---

## Section 13 · Recommended Provisioning

**Design candidate** (documentale, no exec in P0):

1. **Provisioning script** `scripts/rt2_b_1b_provision_expedition_runtime_states.py`:
   - Input: `--env=<dev|preview|prod>` + credenziali provisioning identity via env var separato (`PROVISIONING_MONGO_URL`).
   - Actions idempotenti (in ordine): `listCollections` → se assente, `createCollection` → `createIndex` I1 (native, no-op) → `createIndex` I2 (TTL) → optional I3/I4/I5 solo se autorizzati da `B1BQ06`.
   - Output: JSON report con `collection_created: bool`, `indexes_created: [...]`, `indexes_verified: [...]`, `elapsed_ms`.

2. **Verification script** `scripts/rt2_b_1b_verify_expedition_runtime_states.py`:
   - Read-only con diagnostic identity.
   - Verifica: collection existence, index spec match (name + key + options), TTL `expireAfterSeconds` value, sampling di 1 documento (se presente) per validare campo `expires_at` type = BSON Date.

3. **Rollback script** `scripts/rt2_b_1b_rollback_expedition_runtime_states.py`:
   - Precondition asserts: feature flags OFF, no active runtime state, no runtime wiring, no active writers.
   - Actions ordinate (vedere §24).

**Nessuna esecuzione in questo gate**. Design solo. `PM_REVIEW → B1BQ03 + B1BQ12`.

---

## Section 14 · Runtime Driver Boundary

- Il **runtime process** (uvicorn + FastAPI application) NON deve istanziare `MongoExpeditionRuntimeStateStore` in questo gate.
- Motor client corrente (`AsyncIOMotorClient(MONGO_URL)`) rimane **shared singleton**. **Nessuna wiring**.
- Dependency injection: se in futuro `RT2-B-1B (apply)` autorizzasse la wiring, la collection sarà iniettata come `runtime_collection = mongo_client[db_name].expedition_runtime_states` in un factory dedicato, MAI top-level import.
- **Runtime process credentials** devono essere `runtime identity` (§11.2), non `provisioning identity`.

---

## Section 15 · Isolated Test Environment

### 15.1 Opzioni valutate

| # | Opzione | Fattibilità corrente | Raccomandazione |
|---|---|---|---|
| 1 | CI Mongo service container | **NON disponibile** — nessuna CI infrastructure nel repo (§5.7) | ATTUALMENTE NON FATTIBILE |
| 2 | Dedicated test database su Mongo non-production esistente | **DISPONIBILE** — `orbus_r16_test` già configurato (§5.12/§5.13) | **RACCOMANDATA** |
| 3 | Local ephemeral Mongo container | Fattibile ma richiede setup docker mancante | POSSIBILE FALLBACK |
| 4 | Mock-only validation | **INSUFFICIENTE** per chiudere RT2-B-1B | ESPLICITAMENTE ESCLUSA |

### 15.2 Target raccomandato
**Option 2**: dedicated test database `orbus_r16_test` sul Mongo dev.
- Isolamento: guardrail conftest esistente (§5.12) rifiuta pytest run se `DB_NAME` non contiene `test`.
- Collection isolata: `expedition_runtime_states` sul solo `orbus_r16_test`, MAI `orbus_r16`.
- Credenziali: `runtime identity + provisioning identity` scoped al test DB, mai production.
- Cleanup esplicito: `dropCollection` post-suite via teardown fixture; parallel-test isolation via `PYTEST_XDIST_WORKER` prefix nel nome collection oppure guard-rail su `-n 2`.
- Unique run identifier: `test_run_id` fixture per parametrizzare `expedition_id` (evita cross-worker collisions).
- **No access to live data**: guard-rail `_is_test_db()` (`conftest.py:107`).

`PM_REVIEW → B1BQ10`.

---

## Section 16 · Integration-Test Matrix

Piano test **NO EXEC in P0**. Sedici scenari canonici pre-definiti per la futura suite `RT2-B-1B (apply)`:

| # | Scenario | Store variant | Verifica |
|---|---|---|---|
| 1 | Collection creation | provisioning | idempotente: seconda esecuzione no-op |
| 2 | Idempotent re-provisioning | provisioning | script eseguito 2× → collection unchanged |
| 3 | Index creation I1 (native `_id`) | provisioning | present after run |
| 4 | Index creation I2 (TTL) | provisioning | present, `expireAfterSeconds=0`, key = `expires_at` |
| 5 | Index definition verification | diagnostic | match spec vs declared |
| 6 | TTL index type validation | provisioning | `expires_at` BSON Date on 1 sample doc |
| 7 | CAS success | runtime | `state_version` bump + `fencing_token` preserved |
| 8 | CAS conflict on `state_version` | runtime | rejected → `STATE_VERSION_CONFLICT` |
| 9 | Stale fencing rejection | runtime | `STALE_WRITER_REJECTED` |
| 10 | Lease acquire / renew / takeover | runtime | fencing token increment on takeover |
| 11 | Duplicate-event suppression via receipt ring | runtime | `DEDUPLICATED_NO_OP` |
| 12 | Payload mismatch rejection | runtime | `EVENT_ID_PAYLOAD_MISMATCH` |
| 13 | Parallel mutation (2 writers race) | runtime | 1 wins, 1 rejected deterministically |
| 14 | State-version monotonicity | runtime | never decreases across N mutations |
| 15 | Terminal-state retention & TTL cleanup eligibility | runtime + diagnostic | TTL monitor eventually removes |
| 16 | Rollback verification | rollback | collection dropped, feature flags OFF, no leftover indexes |

**Nessun test che scriva su Mongo deve essere eseguito nel P0.**

---

## Section 17 · Performance Baseline

Baseline attesa (candidate, `PM_REVIEW → B1BQ09`):

| Metrica | Target |
|---|---|
| `find_one({_id: expedition_id})` | < 5 ms p50 · < 20 ms p95 |
| `findOneAndUpdate` (CAS) | < 15 ms p50 · < 50 ms p95 |
| Lease acquisition round-trip | < 30 ms p95 |
| TTL cleanup sweep lag | 0–120 s (Mongo TTL monitor cadence) |
| Adapter error rate | < 0.1 % excluding client-forge rejects |

Nessun benchmark eseguito in questo gate (no exec). I target sono candidati per la successiva P1 apply.

---

## Section 18 · Capacity

Stime evidence-based per envelope planning (assunzioni esplicite):

### 18.1 Assumptions
- Peak concurrent expeditions attivi: `500` (envelope preview) · `5.000` (envelope prod prima fase).
- State documents per expedition: `1` (uno-a-uno con expedition_id).
- Adventurer class states per document: `≤ 6` sub-docs.
- Processed event receipts per document: bounded by `RECEIPT_RING_CAP` (verifica in `mongo_adapter.py`; default env-configurable, atteso `20-50`).
- Average class-state sub-doc size: `1-2 KB`.
- Average total document size: `10-30 KB` (envelope).

### 18.2 Estimate table

| Scenario | Concurrent active | Peak collection size | Daily new docs (created + expired) | Notes |
|---|---|---|---|---|
| Low | 100 | ~3 MB | ~500 | envelope demo/QA |
| Expected | 500 | ~15 MB | ~2.500 | envelope preview |
| Stress | 5.000 | ~150 MB | ~25.000 | envelope prod fase 1 |

Nessuna dimensione supera i limiti Mongo document/collection. TTL cleanup mantiene la crescita bounded. **`PM_REVIEW → B1BQ09`** per baseline definitiva.

---

## Section 19 · Backup and Retention

**Classificazione**:
- Gameplay source of truth **while expedition is active**: `YES`.
- Long-term business record: `NO`.
- Character progression record: `NO`.
- Audit record: `NO` (l'audit trail persistente vive su `audit_log` esistente + emit di CDV a valle).

**Trattamento**:
- **Included in normal backup**: **SÌ** — collection inclusa per consistenza di ripristino di uno stato attivo interrotto.
- **Excluded from long-term archival**: **SÌ** — snapshot > 7 giorni non necessari (documenti già TTL-cleaned).
- **Point-in-time restore implications**:
  - Restore che riattivi documenti in stato `expired` NON deve rimettere in circolazione spedizioni concluse.
  - Guard-rail: restore procedure deve applicare un `updateMany({runtime_status: {$in: ["expired","completed","cancelled"]}}, {$set: {expires_at: now}})` per accelerare cleanup post-restore.
- **Recovery after regional failure**: dipende dalla topologia Mongo prod (`PM_REVIEW → B1BQ08`).

**Regola inderogabile**: **una restore non deve riattivare automaticamente spedizioni ormai terminate**. Procedura di restore deve prevedere una fase di **quarantena documentale** con verifica manuale prima di riabilitare i writer.

---

## Section 20 · Monitoring

Metriche candidate (proposte, non configurate in P0):

| Metric | Type | Note |
|---|---|---|
| `expedition_runtime_states_document_count` | gauge | Total docs in collection |
| `expedition_runtime_states_active_count` | gauge | `runtime_status = active` |
| `expedition_runtime_states_terminal_count` | gauge | terminal states pending cleanup |
| `expedition_runtime_states_storage_bytes` | gauge | via `collStats` |
| `expedition_runtime_states_avg_doc_size_bytes` | gauge | via `collStats.avgObjSize` |
| `expedition_runtime_states_p95_doc_size_bytes` | histogram | sampled |
| `store_read_latency_ms` | histogram | `find_one` |
| `store_cas_latency_ms` | histogram | `findOneAndUpdate` |
| `store_lease_acquire_latency_ms` | histogram | end-to-end |
| `cas_conflict_rate` | counter | per second |
| `stale_writer_rejection_rate` | counter | per second |
| `duplicate_event_suppression_rate` | counter | per second |
| `ttl_cleanup_lag_seconds` | gauge | age of oldest expired doc still present |
| `store_timeout_rate` | counter | per second |
| `adapter_error_rate` | counter | per error class |

**`MONITORING_BASELINE_MISSING`** — nessuna piattaforma di metriche/traccia integrata al codebase corrente. `PM_REVIEW → B1BQ09`.

---

## Section 21 · Alerting

Regole candidate (soglie **PM_REVIEW**, non definitive senza baseline empirica):

| Alert | Trigger candidato | Severity |
|---|---|---|
| High CAS conflict rate | `cas_conflict_rate > 5 %` sustained 5m | warning |
| Lease renewal failures | `> 10 fail/min` sustained 5m | warning |
| Stale writer spikes | `> 20 stale/min` for 5m | warning |
| Document size growth | `p95_doc_size > 500 KB` | warning |
| TTL cleanup lag | `ttl_cleanup_lag_seconds > 300` sustained 10m | warning |
| Store latency degradation | `cas_latency_p95 > 200 ms` sustained 5m | critical |
| Unexpected terminal-state accumulation | `terminal_count > 10 %` of active for 15m | warning |
| Mongo permission failures | `AUTH_FAIL_COUNT > 0` | critical |
| Duplicate reward protection failure | `duplicate_reward_leak_count > 0` | critical |

Se baseline assente: **`MONITORING_BASELINE_MISSING`** come `PM_REVIEW` per l'apply (non blocker per il piano P0). `PM_REVIEW → B1BQ09`.

---

## Section 22 · Security

- Nessun payload PII nel documento (nessuna email, nessun IP, nessuna password).
- `owner_lease_id` e `fencing_token` sono valori server-generated non-guessable.
- Runtime identity ha grants scoped alla sola collection (§11.2) → nessuna esfiltrazione lateral su altre collezioni possibile via runtime credentials.
- Diagnostic identity read-only (§11.3) → nessuna scrittura possibile.
- Isolated test env (§15) → dati reali mai accessibili in test.
- TLS: **PM_REVIEW** per il target prod (`B1BQ02`). Attuale localhost dev senza TLS.
- Secret rotation: **PM_REVIEW → B1BQ04/B1BQ05**.

---

## Section 23 · Operational Ownership

- Provisioning: operator identità dedicata, runbook manuale, audit log obbligatorio.
- Runtime: backend service account.
- Diagnostic: SRE / on-call read-only.
- Rollback: operator + SRE approver.
- Emergency drop: **PM approval required**.

`PM_REVIEW → B1BQ11` per assegnazione formale ruoli.

---

## Section 24 · Rollback

Procedura ordinata (**NO EXEC in P0**):

1. **Verify all related feature flags OFF**: `runtime_stat_soft_cap_enabled`, `runtime_stat_shadow_enabled`, `cdv_transient_state_enabled`, `item_effect_engine_enabled`, `cdv_item_hooks_enabled`, `effect_observability_enabled` → tutti `false`.
2. **Verify no runtime wiring active**: nessun servizio applicativo importa `MongoExpeditionRuntimeStateStore` in modo eager. Solo lazy DI opzionale.
3. **Stop any isolated test writers**: kill uvicorn spawn su porta 8002, cleanup fixture pytest attive.
4. **Verify no active production state**: `db.expedition_runtime_states.count({runtime_status: "active"}) == 0` con diagnostic identity.
5. **Preserve required diagnostic evidence**: `mongodump --collection=expedition_runtime_states` verso `/app/_mongo_dumps/rollback_<ts>/`.
6. **Drop optional indexes** (I3/I4/I5 se creati): `dropIndex` per ciascuno.
7. **Drop TTL index** (I2): `dropIndex('expedition_runtime_states_expires_at_ttl')`.
8. **Drop transient collection**: `dropCollection('expedition_runtime_states')`.
9. **Verify legacy runtime unchanged**: `expeditions`, `expedition_members` invariati (indici pre-esistenti conservati).

**Nel futuro apply gate**: ogni drop deve essere **esplicitamente autorizzato**, **target-specifico** (database + collection nomi verificati), fail-stop su database inatteso (`if db_name != expected: raise`).

---

## Section 25 · Failure Matrix

Tredici scenari analizzati con `detection · fail-stop · auto-recovery · manual-recovery · rollback · audit-evidence`:

| # | Failure | Detection | Fail-stop | Auto recovery | Manual recovery | Rollback | Audit evidence |
|---|---|---|---|---|---|---|---|
| 1 | Collection already exists | `listCollections` pre-check | NO (idempotent) | continua | — | — | log JSON `already_exists=true` |
| 2 | Wrong database selected | `db_name` assertion pre-provisioning | **YES** | — | env correction + rerun | drop only after `db_name` verify | provisioning_report.json `db_selected=<actual>` |
| 3 | Insufficient provisioning permissions | Mongo error `Unauthorized` on `createCollection` | **YES** | — | grant provisioning role, rerun | — | Mongo error log + provisioning_report.json |
| 4 | Index name collision | `listIndexes` pre-check | **YES** | — | manual index rename or drop-then-recreate | drop conflicting index | listIndexes snapshot pre/post |
| 5 | Incompatible existing index | key/options mismatch | **YES** | — | drop-then-recreate under maintenance window | dropIndex + recreate | listIndexes diff |
| 6 | TTL field wrong type | sample doc validation post-write | **YES** | — | data migration + type fix | dropCollection if safe | sample doc snapshot |
| 7 | Partial index provisioning | provisioning report reads created list | **YES** | — | complete missing indexes | drop partial indexes | report step-by-step |
| 8 | Provisioning interrupted (SIGTERM) | provisioning report incomplete | **YES** | — | rerun (idempotent) | — | interruption timestamp |
| 9 | Verification command fails | verify script exit != 0 | **YES** | — | investigate + fix + reverify | — | verify_report.json |
| 10 | Cleanup fails | teardown fixture exception | **YES** in test | — | manual cleanup | — | pytest logs + Mongo state |
| 11 | Test database contains unrelated data | pre-suite guard-rail count | **YES** | — | drop test DB (autorizzato only if `test` in name) | — | conftest logs |
| 12 | Rollback targets wrong collection | assertion `collection_name == 'expedition_runtime_states'` | **YES** | — | abort rollback | — | rollback log |
| 13 | Backup restores expired documents | post-restore query for `runtime_status in [expired,completed,cancelled]` | **YES** | — | apply cleanup update | — | restore_report.json |

---

## Section 26 · Compatibility

- **RT2-A CDV & Effect Engine (24 code + 14 test)**: nessuna modifica, contract compatibility completa. RT2-B-1A adapter già consuma dati derivabili dall'output CDV senza scrittura DB.
- **RT2-B-1A store contract**: pienamente compatibile — il design proposto qui riflette 1:1 il contract sotto test in `test_contract_shared.py`.
- **Expedition service esistente**: **non toccato**. Continua a operare su `expeditions` + `expedition_members`. La collezione runtime-state è additiva.
- **Legacy adventurers/items/inventory**: nessuna interazione, nessuna dipendenza incrociata.
- **Feature flags**: rimangono OFF (§8 RT2-B-1A closure requirement 21).

---

## Section 27 · Risk Register

| # | Risk | Impact | Likelihood | Mitigation | Owner |
|---|---|---|---|---|---|
| R1 | Prod DB target undefined | HIGH | MEDIUM | `B1BQ02` adjudication; provisioning wrapper con `--env` obbligatorio | PM + SRE |
| R2 | Runtime identity con privilegi eccessivi | HIGH | HIGH (stato attuale) | `B1BQ04/05` — separare provisioning e runtime credentials | PM + SRE |
| R3 | Nessuna baseline monitoring | MEDIUM | HIGH | `B1BQ09` — introdurre metrics endpoint prima dell'apply | PM |
| R4 | TTL monitor non deterministico | LOW | HIGH | Alert su `ttl_cleanup_lag_seconds`; documentare aspettativa non-immediate | Backend team |
| R5 | Restore riattiva spedizioni concluse | HIGH | LOW | Quarantine procedure + updateMany post-restore | SRE |
| R6 | Test cross-worker collision (`pytest-xdist -n 2`) | MEDIUM | LOW | Prefix collection name via `PYTEST_XDIST_WORKER` env in test builder | Backend team |
| R7 | Nessuna CI infrastructure | LOW | MEDIUM (per apply) | Option 2 (dedicated test DB) mitiga; option 1 richiede CI setup separato | PM |
| R8 | Runtime wiring accidentale prima di PM approval | HIGH | LOW | Static grep in seal test + runtime import assertion | Governance |

---

## Section 28 · PM Open Questions

12 domande aperte, **NESSUNA auto-ratificata**. Ogni domanda include: evidence attuale, opzioni, agent recommendation, security/operational/migration/rollback impact, blocking flag.

### B1BQ01 · Final collection name
- Evidence: candidate `expedition_runtime_states` allineato a naming conventions; nessuna collision.
- Options: (a) `expedition_runtime_states` (candidate), (b) alternative name con prefisso `rt_` o `runtime_`.
- Agent recommendation: (a).
- Security impact: minimal.
- Operational impact: minimal.
- Migration impact: minimal (nome fissato prima di apply).
- Rollback impact: minimal.
- Blocking: **YES per apply**.

### B1BQ02 · Target database and environments
- Evidence: `DB_NAME=orbus_r16` (dev); `orbus_r16_test` (test); production DB **non presente in `.env` esplorato**.
- Options: (a) usare `orbus_r16` per dev+preview, `orbus_r16_test` per test, `<PROD_DB_NAME>` per production (da fornire), (b) database dedicato `orbus_runtime` cross-env, (c) collection nel database corrente (a).
- Agent recommendation: (a) — mantenere pattern esistente.
- Security impact: **HIGH** — necessario TLS + auth in prod.
- Operational impact: HIGH.
- Migration impact: MEDIUM.
- Rollback impact: MEDIUM.
- Blocking: **YES per apply**.

### B1BQ03 · Provisioning mechanism
- Evidence: pattern attuale = Model C (§12.3); PM baseline preference = Model A.
- Options: (a) Model A explicit idempotent command + verifier, (b) Model B deployment migration, (c) Model C startup ensure.
- Agent recommendation: (a).
- Security impact: HIGH (Model A separa temporalmente credenziali provisioning).
- Operational impact: MEDIUM (richiede runbook).
- Migration impact: MEDIUM.
- Rollback impact: LOW.
- Blocking: **YES per apply**.

### B1BQ04 · Provisioning identity permissions
- Evidence: nessuna evidenza di ruoli configurati; `MONGO_PERMISSION_MODEL_UNDERDEFINED`.
- Options: (a) ruolo custom `provisioning_role` scoped al DB target con `createCollection/createIndex/dropIndex/dropCollection`, (b) `dbAdmin` scoped.
- Agent recommendation: (a).
- Security impact: HIGH.
- Operational impact: MEDIUM.
- Migration impact: LOW.
- Rollback impact: LOW.
- Blocking: **YES per apply**.

### B1BQ05 · Runtime identity permissions
- Evidence: runtime attualmente con root-equivalent su Mongo locale.
- Options: (a) ruolo custom `runtime_role` scoped alla sola collection con `find/insert/update/findAndModify/delete`, (b) ruolo `readWrite` DB-level (troppo ampio).
- Agent recommendation: (a).
- Security impact: HIGH.
- Operational impact: MEDIUM.
- Migration impact: LOW.
- Rollback impact: LOW.
- Blocking: **YES per apply**.

### B1BQ06 · Final index set
- Evidence: I1 (`_id` native) + I2 (TTL) required; I3/I4/I5 optional senza query dimostrata.
- Options: (a) minimal set `I1 + I2`, (b) include I3 (status+expires) per recovery, (c) full set I1..I5.
- Agent recommendation: (a) — avoid indici "per sicurezza". Autorizzare I3 solo con query recovery dimostrata.
- Security impact: minimal.
- Operational impact: (b)/(c) = write amplification maggiore.
- Migration impact: LOW.
- Rollback impact: LOW.
- Blocking: **YES per apply**.

### B1BQ07 · TTL operational values
- Evidence: baseline candidate `active=6h`, `completed/cancelled=24h`. Nessun valore in produzione.
- Options: (a) baseline candidate, (b) `active=2h/completed=12h` (aggressive), (c) `active=24h/completed=7d` (conservative).
- Agent recommendation: (a).
- Security impact: (c) aumenta storage retention.
- Operational impact: (b) maggiore rischio expired-mid-play.
- Migration impact: LOW (parametrizzabile via env).
- Rollback impact: LOW.
- Blocking: **YES per apply**.

### B1BQ08 · Backup and retention treatment
- Evidence: dump manuali; nessun auto-backup/PITR/cross-region.
- Options: (a) include in normal backup + exclude long-term archival + quarantine on restore, (b) exclude runtime-state from tutti backup (accept loss on incident).
- Agent recommendation: (a).
- Security impact: LOW.
- Operational impact: MEDIUM.
- Migration impact: LOW.
- Rollback impact: MEDIUM (restore complexity).
- Blocking: **YES per apply**.

### B1BQ09 · Monitoring and alert policy
- Evidence: `MONITORING_BASELINE_MISSING` — nessuna piattaforma metrics.
- Options: (a) introdurre `/api/admin/metrics` (Prometheus-format) prima dell'apply, (b) deferire monitoring a fase successiva.
- Agent recommendation: (a) — almeno counter/gauge minimi (CAS conflict rate, TTL lag).
- Security impact: metrics endpoint deve essere admin-only.
- Operational impact: HIGH (visibilità mancante è un blocker operativo).
- Migration impact: MEDIUM.
- Rollback impact: LOW.
- Blocking: **YES per apply**.

### B1BQ10 · Isolated integration-test target
- Evidence: Option 2 (`orbus_r16_test`) disponibile e in uso.
- Options: (a) Option 2 (dedicated test DB), (b) Option 3 (ephemeral local container).
- Agent recommendation: (a).
- Security impact: LOW.
- Operational impact: LOW.
- Migration impact: LOW.
- Rollback impact: LOW.
- Blocking: **YES per apply**.

### B1BQ11 · Rollback authority and procedure
- Evidence: nessuna procedura formalizzata; nessuna authority matrix.
- Options: (a) SRE + PM approval per drop; runbook `rt2_b_1b_rollback_runbook.md`, (b) SRE-only authority.
- Agent recommendation: (a).
- Security impact: LOW.
- Operational impact: MEDIUM.
- Migration impact: LOW.
- Rollback impact: **HIGH** (definisce il rollback).
- Blocking: **YES per apply**.

### B1BQ12 · First provisioning/apply slice
- Evidence: RT2-B-1A closed; RT2-B-1B (apply) HOLD.
- Options: (a) slice minimale: provisioning `orbus_r16_test` only + integration-test matrix (Section 16) + verification script + rollback script, (b) full apply cross-env in un solo slice.
- Agent recommendation: (a).
- Security impact: LOW.
- Operational impact: MEDIUM.
- Migration impact: LOW.
- Rollback impact: LOW (slice minimale = rollback minimale).
- Blocking: **YES per apply**.

**Nessuna auto-ratifica.**

---

## Section 29 · Provisioning Readiness

| Categoria | Ready | Note |
|---|---|---|
| Collection design | **YES** (PM_REVIEW `B1BQ01`) | naming + schema definiti |
| Index design | **YES** (PM_REVIEW `B1BQ06`) | I1+I2 baseline chiara |
| TTL design | **YES** (PM_REVIEW `B1BQ07`) | pattern esistente riusabile |
| Permission model | **NO** — `MONGO_PERMISSION_MODEL_UNDERDEFINED` (`B1BQ04/05`) | credenziali attuali non separate |
| Target DB boundary | **NO** — `TARGET_DATABASE_UNDERDEFINED` (`B1BQ02`) per prod | dev/preview OK, prod da chiarire |
| Provisioning mechanism | **YES** — Model A raccomandato (PM_REVIEW `B1BQ03`) | idempotenza dimostrabile |
| Isolated test env | **YES** — Option 2 disponibile (`B1BQ10`) | `orbus_r16_test` operativo |
| Integration-test matrix | **YES** (design) | 16 scenari definiti |
| Monitoring baseline | **NO** — `MONITORING_BASELINE_MISSING` (`B1BQ09`) | nessuna metrics platform |
| Backup treatment | **YES** design (PM_REVIEW `B1BQ08`) | quarantine procedure definita |
| Rollback procedure | **YES** design (PM_REVIEW `B1BQ11`) | 9 step ordinati |
| Failure matrix | **YES** (13 scenari) | vedere Section 25 |

---

## Section 30 · GO/HOLD Recommendation

**Recommendation**: `HOLD-PENDING-PM-DECISIONS`.

**Rationale**:
- Il piano documentale è **completo** (31 sezioni, 12 B1BQ, 13 failure scenarios, 16 integration-test cases, 3 identity profiles, 3 provisioning models, 4 isolated-test options).
- **2 aree presentano indeterminatezza operativa alta** che il PM deve chiudere prima di autorizzare l'apply:
  - `MONGO_PERMISSION_MODEL_UNDERDEFINED` (B1BQ04+B1BQ05) → nessun profilo credenziali separato oggi.
  - `TARGET_DATABASE_UNDERDEFINED` in prod (B1BQ02) → nessuna evidenza empirica di prod Mongo boundary.
- **1 area di visibilità** (`MONITORING_BASELINE_MISSING`, B1BQ09) → PM_REVIEW ma non blocker documentale.
- Nessun fail-stop hard rilevato per il piano stesso (isolated test env presente, provisioning idempotency dimostrata da pattern esistente, nessuna index collision).

**Next action items**:
1. PM adjudication di **tutte** le 12 B1BQ (priorità: B1BQ02 · B1BQ04 · B1BQ05 · B1BQ12).
2. Alla ratifica PM, apertura gate `RT2-B-1B (apply)` — slice minimale su `orbus_r16_test` (Option 2).
3. Nessuna scrittura Mongo prima della ratifica.

---

## Section 31 · Explicit STOP

Piano documentale `RT2-B-1B-P0` completato. Nessuna collection creata. Nessun indice creato. Nessun test Mongo reale eseguito. Nessuna wiring runtime attivata. Nessun feature flag attivato. Nessuna modifica applicativa. PRD invariato. `NEW SEAL = NO`.

**STRICT STOP · Phase 0 documentale**. In attesa di adjudication PM delle 12 B1BQ prima di autorizzare `RT2-B-1B (apply)`.

---

**Fine documento** · Italian_only · DOCUMENTAL_ONLY · READ-ONLY DISCOVERY · RT2-B-1B-P0 draft · SHA Policy §31 · STRICT STOP
