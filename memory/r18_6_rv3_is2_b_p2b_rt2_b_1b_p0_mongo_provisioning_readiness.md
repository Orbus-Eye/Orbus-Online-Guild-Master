# R18.6.RV3-IS2-B-P2B-RT2-B-1B-P0 · Mongo Runtime-State Provisioning Readiness & Isolated Integration Plan (PATCHED · POST-B1BQ RATIFICATION)

**Regime**: `DOCUMENTAL_ONLY · READ-ONLY DISCOVERY · Italian_only · NO APPLY · SHA Policy §31 · STRICT STOP`
**Gate ID**: `R18.6.RV3-IS2-B-P2B-RT2-B-1B-P0 · MONGO PROVISIONING READINESS PLAN`
**Ancoraggio invariante**: `lore_meta.py` SHA256 = `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`
**Fonte upstream**: `R18.6.RV3-IS2-B-P2B-RT2-B-1A · CLOSED · PM-LOCKED`
**Patch dispatch**: 12/12 verdetti B1BQ ratificati dal PM + `RT2-B-1B-1 CONDITIONAL GO — LOCAL ISOLATED ONLY`
**Status**: `PATCHED · PM-RATIFIED · READY FOR FORMAL CLOSURE`

---

## Section 1 · Executive Summary

Il gate `RT2-B-1B-P0` produce, e ora integra con i verdetti PM ratificati, il piano documentale evidence-based e read-only per il **provisioning fisico** della collection `expedition_runtime_states`. Il PM ha ratificato tutte le 12 B1BQ e autorizzato uno slice successore condizionale — `RT2-B-1B-1 · LOCAL ISOLATED MONGO PROVISIONING & REAL ADAPTER INTEGRATION VALIDATION` — confinato a `LOCALHOST-ONLY / ISOLATED INTEGRATION`.

**Principio ambientale (lock architetturale)**:
- `LOCAL ISOLATED VALIDATION` → potenzialmente autorizzato in `RT2-B-1B-1` (dispatch Phase 2 separato).
- `SHARED ENVIRONMENT PROVISIONING` (preview / staging / production) → **VIETATO**.

**Recommendation**: `RT2-B-1B-P0 CLOSED / PM-LOCKED · RT2-B-1B-1 READY-TO-DISPATCH (LOCAL ISOLATED ONLY)`.

---

## Section 2 · Scope

**In scope (documentale, Phase 1)**: patch del piano P0 con verdetti B1BQ; integrazione performance acceptance p95; boundary `LOCAL` vs `SHARED`; scope canonico dello slice `RT2-B-1B-1`; procedura rollback 10-step; failure matrix; PM open questions ratificate.

**Out of scope (proibito in Phase 1)**: Mongo collection creation · index creation · TTL index creation · DB writes · provisioning script execution · migration execution · runtime adapter wiring · expedition service modification · feature flag activation · real integration-test writes su Mongo · uso di credenziali production · OpenAPI / frontend / Registry / item generation. `RT2-B-1B-1` code/apply è **out of scope in Phase 1** — dispatch separato Phase 2.

---

## Section 3 · Governance

- Regime `DOCUMENTAL_ONLY · READ-ONLY DISCOVERY · Italian_only`.
- `lore_meta.py` invariant · anchor SHA `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`.
- Baseline chain `10/10 byte-identical`: IS2-A · IS2-B-P1 · IS2-B-P1-N1 · IS2-B-P2A · IS2-B-P2B-1 · IS2-B-P2B-RT1 · IS2-B-P2B-RT2-P0 · IS2-B-P2B-RT2-A · IS2-B-P2B-RT2-B-P0 · IS2-B-P2B-RT2-B-1A.
- `sealed integrity tests = 6 passed` · `sealed artifacts = 36/36 byte-identical`.
- `NEW SEAL = NO`.
- PRD SHA riferimento pre-append: `53e57f14187ad67344b9af80ac5b78471b3a064faf1f7c6cdbdffd4bb93ba7b9` (post-RT2-B-1A). In questa Phase 1 verrà appeso 1 blocco `RT2-B-1B-P0` (idempotente).
- Closure manifest §31: manifest own SHA `NOT_EMBEDDED` — dichiarato SOLO nel chat report finale.

---

## Section 4 · Source Chain

| # | Upstream artifact | Status |
|---|---|---|
| 1 | `RT2-B-P0` — Foundation Runtime Discovery Report | PM-LOCKED |
| 2 | `RT2-A` — CDV & Effect Engine (24 code + 14 test = 38 file) | PM-LOCKED |
| 3 | `RT2-B-1A` — Store Contract & non-wired adapter (14 file) | PM-LOCKED |
| 4 | `RT2-B-1A` — Implementation Report MD (`77dc4172…`) | INVARIANT |
| 5 | `RT2-B-1A` — Implementation Report JSON (`bc92e363…`) | INVARIANT |
| 6 | `RT2-B-1A` — Final Closure MD / JSON / Manifest (`e0fc5adb…` / `4bbb1daf…` / `d848bc0e…`) | PM-LOCKED |
| 7 | Backend Mongo client init (`app/core/database.py:9`) | READ-ONLY EVIDENCE |
| 8 | Existing index provisioning (`app/core/indexes.py`) | READ-ONLY EVIDENCE |
| 9 | Startup lifespan (`app/core/lifespan.py`) | READ-ONLY EVIDENCE |
| 10 | Pytest DB isolation policy (`/app/memory/pytest_db_isolation_policy.md`) | READ-ONLY EVIDENCE |
| 11 | RT2-B-1B-P0 Draft (pre-patch) | SUPERSEDED BY THIS PATCH |
| 12 | PM Dispatch RT2-B-1B-P0 Patch (12 B1BQ verdicts + CONDITIONAL GO for RT2-B-1B-1) | RATIFYING DIRECTIVE |

---

## Section 5 · Mongo Environment Discovery

Evidenza empirica invariata dal draft. Sintesi:

- **Client init**: `AsyncIOMotorClient(MONGO_URL)` singleton top-level in `/app/backend/app/core/database.py:9`. Un solo profilo credenziali.
- **Env**: `MONGO_URL="mongodb://localhost:27017"` (no auth, no TLS) · `DB_NAME=orbus_r16` · `APP_ENV="development"`.
- **Naming convention**: `snake_case` + plural nouns. `expedition_runtime_states` compatibile.
- **Provisioning path attuale**: Model C (startup ensure via `lifespan.py`).
- **TTL riusabili**: `expireAfterSeconds=0` su `refresh_tokens.expires_at` e `password_reset_tokens.expires_at`.
- **Permissions**: root-equivalent su Mongo locale (no auth).
- **Preview vs prod boundary**: nessuna evidenza empirica di prod DB in `.env`.
- **Deployment**: no Dockerfile / no docker-compose / no k8s manifest / no `.github/`.
- **Backup**: dump manuali in `/app/_mongo_dumps/`; no PITR / auto-backup.
- **Monitoring/alerting**: nessuna integrazione.
- **Test fixtures**: guard-rail hard `conftest.py:11-49` + isolated backend fixture porta `8002` + database di test `orbus_r16_test`.

---

## Section 6 · Naming Conventions

- Collection name: **`expedition_runtime_states`** — `PM_RATIFIED (B1BQ01)`.
- `_id = expedition_id` (indice `_id` nativo) — nessun campo duplicato `expedition_id` salvo necessità futura dimostrata.
- Index naming (post-ratifica):
  - Nativo: `_id` (implicito).
  - TTL: `expedition_runtime_states_expires_at_ttl` con `expireAfterSeconds=0` su campo `expires_at` (BSON Date).
- Indici recovery/monitoring **DEFERRED** — non creare nel primo slice.
- `player-facing export inclusion = FORBIDDEN`.
- `analytics ingestion = DISABLED_BY_DEFAULT`.

---

## Section 7 · Candidate Collection (DESIGN-LOCKED)

- **Nome**: `expedition_runtime_states` — **`DESIGN-LOCKED · PM_RATIFIED (B1BQ01)`**.
- **Naming collision**: `NONE` (verificato in fase discovery).
- **Existing collection**: `NOT PRESENT`.
- **Database target ratificati**:
  - **Provisioning manuale + verifica idempotente**: **`orbus_r16_rt2b_test`** su `LOCALHOST-ONLY / LOCAL DEVELOPMENT · ISOLATED INTEGRATION` — `PM_RATIFIED (B1BQ02)`.
  - **Integration-test automatizzati per-run**: **`orbus_r16_rt2b_it_<unique_run_id>`** — `PM_RATIFIED (B1BQ10)`.
- **Database VIETATI per il primo apply**: `orbus_r16`, `orbus_r16_test`, `preview`, `staging`, `production`. `SHARED ENVIRONMENT APPLY = FORBIDDEN`.
- **Fail-stop**:
  - `Mongo host != localhost` → `TARGET_ENVIRONMENT_REJECTED`
  - `database name != orbus_r16_rt2b_test` (per verifica manuale) o `!= orbus_r16_rt2b_it_<unique_run_id>` (per test) → `TARGET_DATABASE_REJECTED`
- **Provisioning stop**: se collection esiste con schema/indici incompatibili → stop, non modificare, richiedere adjudication.

---

## Section 8 · Document Lifecycle

Schema documento (invariato rispetto al draft, sotto contratto RT2-B-1A):

| Campo | Tipo | Note |
|---|---|---|
| `_id` | string (= `expedition_id`) | UUID4 · nativa dedup |
| `state_version` | int64 | Monotonic; initial `1` |
| `runtime_status` | enum | `active` · `completed` · `cancelled` · `expired` |
| `owner_lease_id` | string \| null | Writer lease |
| `fencing_token` | int64 | Increment su nuova acquisizione lease |
| `lease_expires_at` | BSON Date | Scadenza lease writer |
| `last_event_sequence` | int64 | Server-authoritative |
| `loadout_snapshot_version` | int32 | Riferimento snapshot |
| `adventurer_class_states` | array subdocs | Marks/Drains/FragmentUsage per adventurer |
| `processed_event_receipts` | bounded ring (`RECEIPT_RING_CAP`) | Fail-closed su cap |
| `created_at` | BSON Date UTC | Immutable |
| `updated_at` | BSON Date UTC | Per-mutation |
| `expires_at` | BSON Date UTC | **TTL driver** · aggiornato a ogni mutation attiva; ricalcolato su terminal state |

**Requisito test state document**: `< 256 KiB` (performance acceptance §17). **Unbounded receipt growth = 0**.

---

## Section 9 · Index Requirements (RATIFIED · B1BQ06)

Set indici **iniziale autorizzabile** (in `RT2-B-1B-1`):

| # | Nome | Chiave | Tipo | Required | Note |
|---|---|---|---|---|---|
| I1 | (native `_id`) | `_id` | native | **REQUIRED** | `_id = expedition_id`; nessun indice aggiuntivo su expedition_id |
| I2 | `expedition_runtime_states_expires_at_ttl` | `expires_at` | TTL (`expireAfterSeconds=0`) | **REQUIRED** | Pattern identico a `refresh_tokens_ttl` esistente |

**Indici DEFERRED (NON creare nel primo slice)**:
- `runtime_status + expires_at` (recovery)
- `lease_expires_at` (lease reaper)
- `updated_at` (analytics)

Autorizzazione condizionata a query dimostrata + PM adjudication successiva.

---

## Section 10 · TTL Semantics (DESIGN-LOCKED · B1BQ07)

Valori TTL **PM_RATIFIED per validazione locale**:

| Stato | TTL | Calcolo `expires_at` |
|---|---|---|
| `active` (inactivity) | **6 hours** | `expires_at = last_valid_mutation_ts + 6h` |
| `completed` (terminal) | **24 hours** | `expires_at = completion_ts + 24h` |
| `cancelled` (terminal) | **24 hours** | `expires_at = cancellation_ts + 24h` |
| `expired` (grace) | **0** | Eligibile a rimozione al prossimo TTL sweep |

**Chiarimento critico (PM)**:
- `Mongo TTL deletion = asynchronous`
- `Exact deletion time = not guaranteed`
- **Nessuna logica applicativa deve dipendere dalla cancellazione esatta al secondo**.
- TTL monitor Mongo esegue sweep periodici (~60s cadence, non deterministico).

---

## Section 11 · Permissions (RATIFIED · B1BQ04 + B1BQ05)

Modello identity **stratificato per environment class**:

### 11.1 LOCAL isolated apply (RT2-B-1B-1 · deroga confinata)
- **Provisioning identity**: **current localhost no-auth Mongo connection**.
- **Runtime identity**: `runtime_adapter_wiring = false` → nessuna runtime identity effettivamente usata. Coincidenza temporanea provisioning/runtime **accettata** solo per LOCAL_TEST_ONLY.
- **Deroga**: `LOCAL_TEST_ONLY` confinata.
- **Guardrail obbligatori** (fail-stop se violati):
  - URI **esattamente** `localhost`
  - database name **esattamente** in allowlist (`orbus_r16_rt2b_test` OR `orbus_r16_rt2b_it_<unique_run_id>`)
  - **no wildcard** su database name
  - **no accesso** a `orbus_r16`, `orbus_r16_test`, o altri DB fuori allowlist
  - **no credenziali di produzione** loadate nel processo
  - output esplicito del target (URI + DB) **prima** dell'apply

### 11.2 SHARED environments (futuro — HOLD)
- **Provisioning identity**: `dedicated authenticated provisioning identity = MANDATORY`, ruolo custom con `createCollection · createIndex · dropIndex · dropCollection` limitati a **db+collection autorizzati**.
- **Runtime identity**: `dedicated authenticated runtime identity = MANDATORY`, ruolo custom con `find · insert · findOneAndUpdate · update · delete` limitati alla sola `expedition_runtime_states`; **NON deve possedere** `createCollection · createIndex · dropCollection · admin-wide`.
- **Diagnostic identity**: read-only scoped alla collection.

---

## Section 12 · Provisioning Models (RATIFIED · B1BQ03)

### 12.1 Model A · EXPLICIT IDEMPOTENT ADMINISTRATIVE COMMAND — **RATIFICATO**
- Comando separato per `--dry-run · --apply · --verify · --rollback`.
- `--apply` e `--rollback` richiedono **target esplicito** (URI + DB name esatti).
- Idempotente: re-run deve essere no-op se già consistente.
- Runbook con audit log obbligatorio.

### 12.2 Model B · Deployment migration step — **NON AUTORIZZATO**
- Nessuna infrastruttura CI/CD nel repo.

### 12.3 Model C · Application startup ensure — **ESPLICITAMENTE VIETATO**
Testo verbatim del verdict PM:
- `application startup provisioning = NOT AUTHORIZED`
- `implicit collection creation during runtime = NOT AUTHORIZED`
- `automatic index creation on service startup = NOT AUTHORIZED`

### 12.4 Comando complementare
`READ-ONLY VERIFICATION COMMAND` separato dal provisioning (idempotente, diagnostic identity o local no-auth in deroga LOCAL_TEST_ONLY).

---

## Section 13 · Recommended Provisioning (RATIFIED)

Script paths canonici (**DA CREARE in Phase 2 RT2-B-1B-1**, non in Phase 1):

1. **`scripts/rt2_b_1b_provision_expedition_runtime_states.py`** — idempotent administrative provisioning command.
   - Flags: `--dry-run · --apply · --verify · --rollback`
   - Input: `--target-uri=mongodb://localhost:27017 · --target-db=<allowlisted>`
   - Guardrail fail-stop: host != localhost, DB non in allowlist.
   - Output: JSON report con `collection_created`, `indexes_created`, `indexes_verified`, `elapsed_ms`, `target_uri`, `target_db`.

2. **`scripts/rt2_b_1b_verify_expedition_runtime_states.py`** — read-only verification.
   - Verifica: collection existence, `expedition_runtime_states_expires_at_ttl` spec match, sample doc `expires_at` BSON Date type.

3. **`scripts/rt2_b_1b_rollback_expedition_runtime_states.py`** — 10-step guarded rollback (§24).

**NON creare in Phase 1**. Nessuna esecuzione in Phase 1.

---

## Section 14 · Runtime Driver Boundary

- Runtime process (uvicorn + FastAPI) NON istanzia `MongoExpeditionRuntimeStateStore` in Phase 1 né in `RT2-B-1B-1`.
- `runtime_adapter_wiring = false` — verificato staticamente.
- `AsyncIOMotorClient(MONGO_URL)` singleton attuale rimane invariato per il resto del backend.
- Futuro `RT2-B-1B-2` (o gate successivo) potrà autorizzare la wiring — MAI in Phase 1.

---

## Section 15 · Isolated Test Environment (RATIFIED · B1BQ10)

### 15.1 Target integration-test (per-run)
- **`orbus_r16_rt2b_it_<unique_run_id>`** — database per esecuzione, non riusabile.
- Requirements ratificati:
  - `unique run identifier = MANDATORY` (es. UUID4 o timestamp + PID)
  - `parallel isolation = MANDATORY` (compatibile con `pytest-xdist -n 2`)
  - `cleanup after success = MANDATORY` (dropDatabase o dropCollection post-suite)
  - `cleanup after failure = BEST-EFFORT MANDATORY`
  - `live data access = FORBIDDEN`
  - Mongo host = `localhost`

### 15.2 Target verifica manuale / idempotenza provisioning
- **`orbus_r16_rt2b_test`** — database fisso per verifica manuale (`--dry-run`, `--verify`, `--apply` in dry sequence, `--rollback`).

### 15.3 Opzioni pre-esistenti (draft)
- **Option 1** CI service container — **NON APPLICABILE** (no CI infra).
- **Option 2** `orbus_r16_test` — **NON UTILIZZABILE** per RT2-B (verdict PM `B1BQ02`: databases pre-esistenti vietati).
- **Option 3** local ephemeral container — **NON RICHIESTA** (localhost Mongo dev sufficiente per RT2-B-1B-1).
- **Option 4** mock-only — **ESCLUSA** (già in RT2-B-1A).

### 15.4 Isolated backend fixture esistente
`isolated_backend_url` (conftest.py) rimane utilizzabile ma con `DB_NAME` override a `orbus_r16_rt2b_test`/`orbus_r16_rt2b_it_<unique_run_id>` — MAI `orbus_r16_test`.

---

## Section 16 · Integration-Test Matrix (SCOPE for RT2-B-1B-1)

**Scope canonico dello slice `RT2-B-1B-1`** (12 item verbatim dal verdict PM):

1. idempotent provisioning command
2. read-only verification command
3. guarded rollback command
4. collection creation in `orbus_r16_rt2b_test`
5. TTL index creation on `expires_at`
6. schema/field validation in test fixtures
7. real Mongo adapter integration tests
8. CAS tests
9. lease / fencing tests
10. deduplication tests
11. concurrent mutation tests
12. cleanup and rollback verification

**Esclusioni esplicite RT2-B-1B-1**:
- `orbus_r16` writes (VIETATO)
- preview / staging / production writes (VIETATO)
- runtime wiring (`runtime_adapter_wiring = false` mantenuto)
- expedition service changes
- feature flag activation
- RT2-A wiring
- Marchio / Drenaggio / Frammenti gameplay
- public API changes
- frontend changes

**Nessun test eseguito in Phase 1**. Design canonico solo.

---

## Section 17 · Performance Baseline (ACCEPTANCE · RT2-B-1B-1 locale)

Soglie **PM_RATIFIED** per l'apply locale isolato:

| Metrica | Target (p95) |
|---|---|
| `single-state read p95` | `≤ 25 ms` |
| `successful CAS mutation p95` | `≤ 35 ms` |
| `lease acquire/renew p95` | `≤ 35 ms` |
| `deduplicated retry p95` | `≤ 25 ms` |
| `test state document size` | `< 256 KiB` |
| `unbounded receipt growth` | `= 0` |
| `DB outside allowlisted test databases` | `= 0` |
| `network outside localhost` | `= 0` |

**Caveat esplicito PM**: `local metrics do NOT authorize shared or live rollout`. Il superamento delle soglie locali non abilita alcun apply su preview/staging/production.

---

## Section 18 · Capacity

Stime invariate rispetto al draft (envelope planning per apply futuri):

| Scenario | Concurrent active | Peak collection size | Daily new docs |
|---|---|---|---|
| Low | 100 | ~3 MB | ~500 |
| Expected | 500 | ~15 MB | ~2.500 |
| Stress | 5.000 | ~150 MB | ~25.000 |

Mongo document 16 MB limit risk: **LOW** (receipts bounded, class states bounded).

Le stime `Expected`/`Stress` **non sono autorizzate** per apply in Phase 1 né in `RT2-B-1B-1` (locale only, dati sintetici test).

---

## Section 19 · Backup and Retention (RATIFIED · B1BQ08)

### 19.1 LOCAL isolated (`orbus_r16_rt2b_test`, `orbus_r16_rt2b_it_<unique_run_id>`)
- `backup = NOT REQUIRED`
- `long-term retention = FORBIDDEN`
- `archival = FORBIDDEN`
- **Sacrificabile, eliminabile interamente**.

### 19.2 SHARED environments (futuro — HOLD)
- Adjudication operativa separata richiesta.
- Baseline dichiarata:
  - no long-term retention di runtime-state data
  - no automatic reactivation di stati ripristinati
  - stati recuperati da backup considerati sospetti/scaduti fino a **riconciliazione manuale**
- Quarantine procedure obbligatoria (già §19 draft).

---

## Section 20 · Monitoring (RATIFIED · B1BQ09)

`MONITORING_BASELINE_MISSING = ACKNOWLEDGED`.

### 20.1 Non bloccante per
- provisioning locale isolato (RT2-B-1B-1)
- test di integrazione locale
- rollback locale

### 20.2 BLOCCANTE per
- preview apply
- staging apply
- production apply
- runtime wiring in shared environment

### 20.3 Evidenza minima RT2-B-1B-1 (locale)
- provisioning command output
- verification command output
- test report
- collection stats before / after
- index list before / after
- cleanup verification

### 20.4 SHARED environments (futuro — HOLD)
Metriche minime richieste prima di apply condiviso:
- error rate
- CAS conflicts
- lease failures
- latency
- document size
- TTL cleanup lag
- permission failures

**Nessuna soglia production ratificata in questo gate**.

---

## Section 21 · Alerting

Regole candidate (`PM_REVIEW` esteso a `RT2-B-1B-2+` / shared environment gate). Invariate rispetto al draft. Nessuna configurazione in Phase 1.

---

## Section 22 · Security

- Nessun PII nel documento.
- `owner_lease_id`, `fencing_token` server-generated.
- LOCAL_TEST_ONLY deroga no-auth confinata (§11.1) — non estensibile.
- SHARED environments: authenticated identities mandatory (§11.2), TLS mandatory in prod.
- Secret rotation: parte di adjudication shared-env.

---

## Section 23 · Operational Ownership

- **LOCAL RT2-B-1B-1**: `operator executing the PM-authorized provisioning dispatch` (autorità confinata al dispatch).
- **SHARED environments (futuro)**: SRE + PM approval; runbook `rt2_b_1b_rollback_runbook.md`.

---

## Section 24 · Rollback (RATIFIED · B1BQ11 · 10-STEP)

Procedura **10-step** ratificata (autorità locale: `operator executing the PM-authorized provisioning dispatch`):

1. **Verify all feature flags OFF**: 6 flag RT2-A/RT2-B (`runtime_stat_soft_cap_enabled`, `runtime_stat_shadow_enabled`, `cdv_transient_state_enabled`, `item_effect_engine_enabled`, `cdv_item_hooks_enabled`, `effect_observability_enabled`).
2. **Verify runtime wiring absent**: static grep + import assertion.
3. **Verify Mongo host = localhost**: URI check.
4. **Verify database allowlist**: DB name esattamente in `{orbus_r16_rt2b_test, orbus_r16_rt2b_it_<unique_run_id>}`.
5. **Stop integration-test writers**: terminate isolated backend fixture, kill test processes.
6. **Capture collection/index metadata**: `listCollections`, `listIndexes`, `collStats` → JSON snapshot in `/app/_mongo_dumps/rollback_<ts>/`.
7. **Drop `expedition_runtime_states`**: `dropCollection` esplicito.
8. **Optionally drop isolated test database**: `dropDatabase` **solo** se target DB nome termina con `_test` OR `_it_<unique_run_id>`.
9. **Verify collection absent**: post-drop `listCollections` deve NON contenere `expedition_runtime_states`.
10. **Rerun compatibility tests**: RT2-A `136/136` + RT2-B-1A `91/0` — verifica byte-identical baseline.

**Proprietà rollback**:
- Idempotente
- Target-specifico (host + DB check obbligatorio)
- Dry-run capable
- Fail-stop su host o database inatteso
- **VIETATI** comandi drop generici o senza allowlist

---

## Section 25 · Failure Matrix

13 scenari invariati (draft) + 2 nuovi enforcement post-B1BQ:

| # | Failure | Detection | Fail-stop | Recovery |
|---|---|---|---|---|
| 1 | Collection already exists | `listCollections` | NO (idempotent) | continue |
| 2 | Wrong database selected | DB name assertion | **YES** (`TARGET_DATABASE_REJECTED`) | env correction |
| 3 | Wrong Mongo host | URI assertion | **YES** (`TARGET_ENVIRONMENT_REJECTED`) | fail-stop hard |
| 4 | Insufficient provisioning permissions | Mongo Unauthorized | YES | grant role (shared env) |
| 5 | Index name collision | `listIndexes` | YES | manual rename/drop-recreate |
| 6 | Incompatible existing index | key/options mismatch | YES | drop-then-recreate |
| 7 | TTL field wrong type | sample doc validation | YES | data migration |
| 8 | Partial index provisioning | report reads created list | YES | complete missing |
| 9 | Provisioning interrupted | report incomplete | YES | rerun idempotent |
| 10 | Verification command fails | script exit != 0 | YES | investigate + reverify |
| 11 | Cleanup fails | teardown exception | YES | manual cleanup |
| 12 | Test database contains unrelated data | pre-suite guard-rail | YES | drop test DB (only if allowlisted) |
| 13 | Rollback targets wrong collection | assertion collection name | YES | abort rollback |
| 14 | Rollback targets wrong DB | assertion DB allowlist | YES | abort rollback |
| 15 | Backup restores expired documents | post-restore query | YES | apply cleanup update |

---

## Section 26 · Compatibility

- RT2-A CDV & Effect Engine: nessuna modifica · contract compatibility completa.
- RT2-B-1A store contract: 1:1 alignment.
- Expedition service esistente: non toccato.
- Feature flags: OFF invariate.
- Backend Mongo client singleton: invariato.

---

## Section 27 · Risk Register

| # | Risk | Impact | Likelihood | Mitigation post-B1BQ |
|---|---|---|---|---|
| R1 | Prod DB target undefined | HIGH | MEDIUM | SHARED APPLY FORBIDDEN in Phase 2 |
| R2 | Runtime identity over-privileged | HIGH | HIGH (dev only) | LOCAL_TEST_ONLY deroga; shared env identities mandatory |
| R3 | No monitoring baseline | MEDIUM | HIGH | shared env apply BLOCKED until baseline |
| R4 | TTL monitor non-deterministic | LOW | HIGH | esplicitato §10; nessuna dipendenza al secondo |
| R5 | Restore reactivates terminated expeditions | HIGH | LOW | quarantine procedure §19.2 |
| R6 | Test cross-worker collision | MEDIUM | LOW | `unique_run_id` per DB test (§15.1) |
| R7 | No CI infrastructure | LOW | MEDIUM | localhost Mongo sufficient for RT2-B-1B-1 |
| R8 | Accidental runtime wiring pre-authorization | HIGH | LOW | seal test + static import grep in RT2-B-1B-1 |
| R9 | Provisioning idempotency not yet empirically verified | HIGH | MEDIUM | **TO BE VERIFIED IN RT2-B-1B-1** (real localhost run) |

---

## Section 28 · PM Open Questions — RATIFIED

**Stato**: `12/12 RATIFICATE`. Verdict PM verbatim (o semanticamente equivalenti).

### B1BQ01 · Final collection name — `PM_RATIFIED`
- `collection name = expedition_runtime_states`
- `_id = expedition_id` (native index, no duplicate field)
- provisioning stops on incompatible pre-existing schema/indexes

### B1BQ02 · Database ed ambiente target — `PM_RATIFIED`
- Primo apply: **`orbus_r16_rt2b_test`** su `LOCALHOST-ONLY / LOCAL DEVELOPMENT · ISOLATED INTEGRATION`
- **VIETATI**: `orbus_r16`, `orbus_r16_test`, preview, staging, production
- Fail-stop: `Mongo host != localhost → TARGET_ENVIRONMENT_REJECTED`; `database name mismatch → TARGET_DATABASE_REJECTED`

### B1BQ03 · Provisioning mechanism — `PM_RATIFIED`
- `EXPLICIT IDEMPOTENT ADMINISTRATIVE COMMAND` + separate `READ-ONLY VERIFICATION COMMAND`
- Application startup / implicit collection creation / automatic index creation on service startup **NON AUTORIZZATI**
- Flags: `--dry-run · --apply · --verify · --rollback` con target esplicito

### B1BQ04 · Provisioning identity (deroga localhost) — `PM_RATIFIED`
- Ambiente locale isolato: `current localhost no-auth Mongo connection`; `temporary coincidence with runtime identity = ACCEPTED`
- Deroga confinata: `LOCAL_TEST_ONLY`
- Guardrail obbligatori (§11.1)
- Ambienti condivisi: `dedicated authenticated provisioning identity = MANDATORY`

### B1BQ05 · Runtime identity — `PM_RATIFIED`
- Primo apply locale: `runtime_adapter_wiring = false` → nessuna runtime identity effettivamente usata
- Ambienti condivisi: `dedicated authenticated runtime identity = MANDATORY` con privilegi scoped alla sola collection

### B1BQ06 · Indici iniziali autorizzabili — `PM_RATIFIED`
- Identità: `_id = expedition_id` (nativo, nessun indice aggiuntivo)
- TTL: `field = expires_at`, `expireAfterSeconds = 0`, `required = TRUE`
- Recovery/monitoring `DEFERRED` (NON creare nel primo slice)

### B1BQ07 · TTL policy — `PM_RATIFIED (DESIGN-LOCKED per validazione)`
- `active state inactivity = 6 hours`
- `completed state retention = 24 hours`
- `cancelled state retention = 24 hours`
- `Mongo TTL deletion = asynchronous; exact deletion time = not guaranteed`

### B1BQ08 · Backup and retention (localhost) — `PM_RATIFIED`
- `orbus_r16_rt2b_test`: `backup = NOT REQUIRED · long-term retention = FORBIDDEN · archival = FORBIDDEN · SACRIFICABILE`
- Shared env futuri: adjudication separata

### B1BQ09 · Monitoring & alerting — `PM_RATIFIED`
- `MONITORING_BASELINE_MISSING = ACKNOWLEDGED`
- Non bloccante: provisioning locale isolato, IT locale, rollback locale
- Bloccante: preview, staging, production, runtime wiring in shared env
- Evidenza minima RT2-B-1B-1 locale definita in §20.3

### B1BQ10 · Integration-test target — `PM_RATIFIED`
- Target IT: `local Mongo localhost:27017` · database `orbus_r16_rt2b_it_<unique_run_id>`
- Requirements: unique_run_id mandatory · parallel isolation mandatory · cleanup after success mandatory · cleanup after failure best-effort · live data access forbidden
- DB fisso `orbus_r16_rt2b_test` per verifica manuale/idempotente

### B1BQ11 · Rollback — `PM_RATIFIED (10-STEP)`
- Autorità locale: `operator executing the PM-authorized provisioning dispatch`
- Procedura §24 (10 step)
- Proprietà: idempotente · target-specifico · dry-run capable · fail-stop su host/DB inatteso
- Comandi drop generici o senza allowlist: **VIETATI**

### B1BQ12 · First provisioning/apply slice — `PM_RATIFIED`
- Nome canonico: `R18.6.RV3-IS2-B-P2B-RT2-B-1B-1 · LOCAL ISOLATED MONGO PROVISIONING & REAL ADAPTER INTEGRATION VALIDATION`
- Scope 12 item (§16)
- Esclusioni esplicite (§16)

---

## Section 29 · Provisioning Readiness (POST-RATIFICATION)

| Categoria | Ready | Nota |
|---|---|---|
| Collection design | **YES** | `PM_RATIFIED B1BQ01` |
| Index design | **YES** | I1+I2 authorized · I3/I4/I5 DEFERRED |
| TTL design | **YES** | 6h/24h/24h ratified |
| Permission model | **YES (LOCAL_TEST_ONLY)** | shared env identities mandatory (deferred) |
| Target DB boundary | **YES** | localhost isolated authorized · shared BLOCKED |
| Provisioning mechanism | **YES** | Model A ratified |
| Isolated test env | **YES** | `orbus_r16_rt2b_test` + `orbus_r16_rt2b_it_<run_id>` |
| Integration-test matrix | **YES** | 12 item scope in RT2-B-1B-1 |
| Monitoring baseline | **ACKNOWLEDGED MISSING** | non-blocking locally · blocking shared |
| Backup treatment | **YES** | not required locally · quarantine shared |
| Rollback procedure | **YES** | 10-step ratified |
| Failure matrix | **YES** | 15 scenari |
| Performance acceptance | **YES** | p95 targets ratified (§17) |

---

## Section 30 · GO/HOLD Recommendation

**Recommendation**: `RT2-B-1B-P0 CLOSED / PM-LOCKED · RT2-B-1B-1 READY-TO-DISPATCH (LOCAL ISOLATED ONLY)`.

**Rationale**:
- Piano documentale completo (31/31 sezioni).
- 12/12 B1BQ ratificate dal PM.
- 3 fail-stop iniziali risolti / risolti transitoriamente / acknowledged; 1 fail-stop residuo (`PROVISIONING_IDEMPOTENCY_UNDERDEFINED`) è **TO BE VERIFIED IN RT2-B-1B-1** — non pregiudica la chiusura P0.
- Boundary architetturale chiaro: LOCAL isolated potenzialmente autorizzato · SHARED environments vietati.
- Scope RT2-B-1B-1 canonico definito (12 item).
- Rollback 10-step ratificato.
- Performance acceptance p95 ratificati per apply locale.

**Next action (Phase 2, dispatch separato)**:
1. `RT2-B-1B-1 · LOCAL ISOLATED MONGO PROVISIONING & REAL ADAPTER INTEGRATION VALIDATION` — code/apply gate.
2. Nessuna scrittura Mongo in Phase 1.

---

## Section 31 · Explicit STOP

Piano documentale `RT2-B-1B-P0 (PATCHED · POST-B1BQ)` completato. Nessuna collection creata. Nessun indice creato. Nessuna scrittura Mongo eseguita. Nessuna wiring runtime attivata. Nessun feature flag attivato. Nessuna modifica applicativa.

**STRICT STOP · Phase 1 documentale**. In attesa di dispatch separato Phase 2 (`RT2-B-1B-1`).

---

**Fine documento (PATCHED)** · Italian_only · DOCUMENTAL_ONLY · READ-ONLY DISCOVERY · RT2-B-1B-P0 patched · SHA Policy §31 · STRICT STOP
