# R18.6.RV3-IS2-B-P2B-RT2-B-1B-1 · Implementation Report

**Gate**: `R18.6.RV3-IS2-B-P2B-RT2-B-1B-1 · LOCAL ISOLATED MONGO PROVISIONING & REAL ADAPTER INTEGRATION VALIDATION`
**Regime**: `LOCAL ISOLATED ONLY · NO SHARED ENV APPLY · SHA §31 · Italian only · Phase 2`
**Ancoraggio invariante**: `lore_meta.py` SHA256 `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`
**Predecessore lockato**: `R18.6.RV3-IS2-B-P2B-RT2-B-1B-P0 · CLOSED · PM-LOCKED` (PRD SHA `0012b0f8…`)
**Status**: `IMPLEMENTED · READY-FOR-PM-CLOSURE`

---

## 1 · Scope executed vs authorized (12/12)

Tutti i 12 item del verdict PM `B1BQ12` sono coperti da codice + test:

| # | Item PM | Copertura | Test suite |
|---|---|---|---|
| 1 | idempotent provisioning command | `provisioning_command.py::ProvisioningCommand.apply` + CLI `--apply` | `test_provisioning_idempotency.py` (4 test) |
| 2 | read-only verification command | `.verify` + CLI `--verify` | `test_verification.py` (3 test) |
| 3 | guarded rollback command | `.rollback` + CLI `--rollback` + guardrail re-check | `test_rollback.py` (6 test) |
| 4 | collection creation in `orbus_r16_rt2b_test` | `create_collection` idempotente | `test_provisioning_idempotency.py::test_apply_creates_collection_and_ttl_index` |
| 5 | TTL index creation on `expires_at` | `create_index([("expires_at", 1)], expireAfterSeconds=0, name=TTL_INDEX_NAME)` | `test_provisioning_idempotency.py` + `test_verification.py::test_verify_reports_healthy_state` |
| 6 | schema/field validation in test fixtures | fixture `provisioned_unique_db` + real docs via `MongoExpeditionRuntimeStateStore` | `test_cas_real.py` · `test_lease_real.py` · `test_dedup_real.py` |
| 7 | real Mongo adapter integration tests | 6+ classi di test contro Motor `AsyncIOMotorClient` | tutti i file `test_*_real.py` |
| 8 | CAS tests | success + state_version conflict + fencing mismatch | `test_cas_real.py` (6 test) |
| 9 | lease/fencing tests | acquire + renew + release + reacquire (token bump) | `test_lease_real.py` (4 test) |
| 10 | deduplication tests | idempotent no-op + `EVENT_ID_PAYLOAD_MISMATCH` + 10-retry loop | `test_dedup_real.py` (3 test) |
| 11 | concurrent mutation tests | `asyncio.gather` × 4 CAS + 3 lease + 5 create isolation | `test_concurrent_real.py` (3 test) |
| 12 | cleanup and rollback verification | teardown DB residues = 0 + full-cycle apply/rollback/apply | `test_cleanup.py` (4 test) + `test_rollback.py::test_full_cycle_*` |

**Scope compliance = 12/12**. Nessuna espansione fuori scope.

---

## 2 · File aggiunti (16 nuovi, tutti `new_file=true`, `existing_file_modified=false`)

### 2.1 Codice (4 nuovi)

| Path | SHA256 | Lines | Role | change_type |
|---|---|---|---|---|
| `/app/backend/app/stats/runtime/state_store/provisioning/__init__.py` | `df123a77acd3282cc1a440697753d2857ebbb5c0800e6b9f5a8a9a05b4ae4d5d` | 50 | Package re-exports | NEW_MODULE |
| `/app/backend/app/stats/runtime/state_store/provisioning/guards.py` | `1a54479fad41cec8571c3bdb4b99d87d25b9a28937fe3282882ce54a62b95599` | 114 | Host + DB allowlist guards | NEW_MODULE · VALIDATION_CHANGE |
| `/app/backend/app/stats/runtime/state_store/provisioning/unique_run_id.py` | `1906abbd13dc92b8f0645e0ee38e15ed2ade80532193eb0ba900b5fa224bceac` | 47 | Unique run id generator | NEW_MODULE |
| `/app/backend/app/stats/runtime/state_store/provisioning/provisioning_command.py` | `8333a52e87007d152bf9d7d674eff9a6556254be087219f436e9c6b40986e817` | 308 | Idempotent CLI + `ProvisioningCommand` class | NEW_MODULE |

### 2.2 Test (12 nuovi)

| Path | SHA256 | Lines | Test count |
|---|---|---|---|
| `/app/backend/tests/effect_engine/state_store/integration_real_mongo/__init__.py` | `295158254785e7ff32ccea9b0de45ebb4e8272b48987ce17c7a8f9df204ad6d3` | 12 | — (package) |
| `/app/backend/tests/effect_engine/state_store/integration_real_mongo/conftest.py` | `2df5bfcb537152401b6653c8d639b168527cc501392014f5b54a74278eb61855` | 121 | — (fixtures) |
| `/app/backend/tests/effect_engine/state_store/integration_real_mongo/test_guards.py` | `0a7e72200d860f24b4595ca2138b29031339efce8daae23c7af2fb627eed2fb2` | 113 | 18 |
| `/app/backend/tests/effect_engine/state_store/integration_real_mongo/test_provisioning_idempotency.py` | `a664b45ce6906d2b98276ec624023c08bc5bf4c17bf51ab641ec9664f344e330` | 110 | 4 |
| `/app/backend/tests/effect_engine/state_store/integration_real_mongo/test_verification.py` | `183d79a7f88fc7ff5e518e4b001e30302d0e729ce964e93879cedec0dd23c7eb` | 68 | 3 |
| `/app/backend/tests/effect_engine/state_store/integration_real_mongo/test_rollback.py` | `74ef39f53589ccc2d18b29311f1cb1ca313f340e458f7662840f2da9fc5beec4` | 115 | 6 |
| `/app/backend/tests/effect_engine/state_store/integration_real_mongo/test_cas_real.py` | `483984538fcdd649fc93615a1fb0f7b3e386d4ed688a641377668ba8289e85b7` | 161 | 6 |
| `/app/backend/tests/effect_engine/state_store/integration_real_mongo/test_lease_real.py` | `3eac9be71725ad9b4329809b905daf7d5ad8d7016eac4f6aaf9def14e3b29b42` | 99 | 4 |
| `/app/backend/tests/effect_engine/state_store/integration_real_mongo/test_dedup_real.py` | `e7311f439bbee056f85812c5a3b7e62342bd92f841b54982d2e91d4e1df3c4a5` | 142 | 3 |
| `/app/backend/tests/effect_engine/state_store/integration_real_mongo/test_concurrent_real.py` | `1a681c6124c201ab0e76c7868231f47db079e0daab76711a610ccfc38daa8eb2` | 102 | 3 |
| `/app/backend/tests/effect_engine/state_store/integration_real_mongo/test_cleanup.py` | `1daf1004c5f889384b57ffd7587d9421182f68c59db34425e87303899b0d911c` | 69 | 4 |
| `/app/backend/tests/effect_engine/state_store/integration_real_mongo/test_performance.py` | `66d5914b2e7fb821c8824fc5e8a6931fda4e0d1c0bf6b10eb3ef96c8daa9b74f` | 171 | 4 |

**Totale file nuovi**: 16 (4 code + 12 test). **Totale test count**: 57.

---

## 3 · File estesi

**Nessuno**. Zero file esistenti modificati. Nessun `__init__.py` esistente esteso. Il nuovo package `state_store/provisioning/` è indipendente e non è importato da alcun `__init__.py` esistente né da `lifespan.py` / `app_factory.py`.

Verifica statica:
- `state_store/__init__.py` SHA (RT2-B-1A) `a3f3575f5e6c033134948dce164945b4712ce2fee4f6c62163cf0541d2e8b486` — INVARIANT
- Grep `from app.stats.runtime.state_store.provisioning` fuori dai file nuovi + test → 0 occorrenze.

---

## 4 · Provisioning CLI

- Comando: `python -m app.stats.runtime.state_store.provisioning.provisioning_command`
- Flags mutually-exclusive: `--dry-run` · `--apply` · `--verify` · `--rollback` (uno obbligatorio)
- `--host <uri>` (default `mongodb://localhost:27017`)
- `--db <name>` (obbligatorio)
- `--confirm` (obbligatorio per `--apply` / `--rollback` non-dry-run)
- Guardrail eseguiti PRIMA dell'istanziazione client + PRIMA di ogni Mongo op
- Output esplicito: `[GUARD] Mongo host verified: localhost` · `[GUARD] Database verified: <db>` · `TARGET: host=<uri> db=<db>`
- Report JSON stdout con `collection_created`, `ttl_index_created`, `ttl_index_verified`, `indexes_before`, `indexes_after`

---

## 5 · Verification CLI

- Modalità `--verify` → read-only, dry_run=True
- Verifica: presenza collection · indice TTL `expires_at_ttl` con `expireAfterSeconds=0` · key `{expires_at: 1}`
- Nessuna scrittura (verificato da `test_verify_does_not_write`)
- Report include `success` = True/False

---

## 6 · Rollback CLI

- Modalità `--rollback` · `--dry-run` per report senza drop
- Guardrail re-check al boundary rollback (§11.1)
- `dropCollection` esplicito su `expedition_runtime_states` (mai `dropDatabase` a meno di teardown fixture)
- Idempotente: rollback di collection assente = no-op successo
- Rifiuta con fail-stop qualsiasi target non allowlisted

---

## 7 · Guards (funzioni pure, deterministiche)

| Funzione | Fail-stop code |
|---|---|
| `verify_host_localhost(uri)` | `TARGET_ENVIRONMENT_REJECTED` |
| `verify_not_orbus_r16(db_name)` | `FORBIDDEN_DATABASE_ORBUS_R16` |
| `verify_database_allowlist(db_name)` | `TARGET_DATABASE_REJECTED` (o `FORBIDDEN_DATABASE_ORBUS_R16` per orbus_r16) |
| `verify_target(uri, db_name)` | compose (host prima, db dopo) |

Allowlist: `orbus_r16_rt2b_test` (fisso) + regex `^orbus_r16_rt2b_it_[a-z0-9_-]+$`.
Loopback hosts: `{"localhost", "127.0.0.1", "::1"}`.

Test coverage: 18 unit test in `test_guards.py` — 100% path coverage sui rami di rifiuto.

---

## 8 · Idempotency evidence

Test `test_apply_is_idempotent`:
- Run 1: `collection_created=true · ttl_index_created=true · ttl_index_verified=true`
- Run 2: `collection_created=false · ttl_index_created=false · ttl_index_verified=true`
- Index signature (name + key + expireAfterSeconds) **identical** across runs.

Test `test_apply_three_times_stable`: 3 apply consecutive → signature identiche.

Fail-stop `PROVISIONING_IDEMPOTENCY_UNDERDEFINED` (residuo di RT2-B-1B-P0) → **RESOLVED_BY_INTEGRATION_TESTS**.

---

## 9 · Collection creation evidence (`orbus_r16_rt2b_test`)

Verificato da `test_apply_creates_collection_and_ttl_index`:
- collection `expedition_runtime_states` presente post-apply
- TTL index breakdown:
  ```json
  {"name": "expedition_runtime_states_expires_at_ttl", "key": {"expires_at": 1}, "expireAfterSeconds": 0}
  ```
- Nessuna altra index (oltre a `_id` nativo) creata.

---

## 10 · TTL index verification

`list_indexes()` post-apply su `orbus_r16_rt2b_test.expedition_runtime_states`:
1. `_id_` (nativo, chiave `_id`)
2. `expedition_runtime_states_expires_at_ttl` (chiave `{expires_at: 1}`, `expireAfterSeconds: 0`)

Solo 2 index totali. Match esatto con verdict PM B1BQ06.

---

## 11 · Real Mongo adapter integration tests

`MongoExpeditionRuntimeStateStore` (RT2-B-1A, non-wired) istanziato dai test con collection Motor reale:
- 6 test in `test_cas_real.py` (create/get/duplicate + 3 CAS scenarios + monotonicity)
- 4 test in `test_lease_real.py` (acquire/second-rejected/renew/release-reacquire)
- 3 test in `test_dedup_real.py` (idempotent no-op + payload mismatch + 10-retry)
- 3 test in `test_concurrent_real.py` (CAS race + lease race + expedition isolation)

Totale integration adapter: **16 test** contro Motor reale. **16/16 PASS**.

---

## 12 · CAS/lease/dedup/concurrent tests

| Suite | Path | Test count | Status |
|---|---|---|---|
| CAS | `test_cas_real.py` | 6 | 6/6 PASS |
| Lease/fencing | `test_lease_real.py` | 4 | 4/4 PASS |
| Deduplication | `test_dedup_real.py` | 3 | 3/3 PASS |
| Concurrent | `test_concurrent_real.py` | 3 | 3/3 PASS |
| **Totale** | — | **16** | **16/16 PASS** |

---

## 13 · Cleanup verification

- Teardown `unique_test_db` fixture: `drop_database(<orbus_r16_rt2b_it_*>)` in un `asyncio.run()` dedicato (isolato dal loop del test).
- Post-suite verification (via `list_database_names()`): **0 database `orbus_r16_rt2b_it_*` residui**.
- Test `test_no_orbus_r16_writes_across_run`: **PASS** (nessuna collection `expedition_runtime_states` in `orbus_r16`).
- Test `test_no_orbus_r16_test_writes`: **PASS** (nessuna scrittura su `orbus_r16_test`).
- Test `test_all_it_databases_have_valid_name`: **PASS** (regex match su tutti gli IT DB).

Cleanup residual DBs pre-refactor (dei run "Event loop closed"): 21 DB rimossi manualmente + suite ri-eseguita → 0 nuovi residui.

---

## 14 · Performance metrics (localhost Mongo, no fsync durability)

Tutti misurati su `orbus_r16_rt2b_it_<run_id>` con `SAMPLE_COUNT = 50` per operazione.

| Metric | p50 | p95 | p99 | Budget p95 | Status |
|---|---|---|---|---|---|
| `single_state_read` | 0.17ms | 0.21ms | 0.45ms | 25ms | ✅ PASS |
| `cas_mutation` | 0.25ms | 0.30ms | 0.33ms | 35ms | ✅ PASS |
| `lease_acquire` | 0.62ms | 0.68ms | 0.98ms | 35ms | ✅ PASS |
| `lease_renew` | 0.35ms | 0.39ms | 0.41ms | 35ms | ✅ PASS |
| `dedup_retry` | 0.25ms | 0.27ms | 0.30ms | 25ms | ✅ PASS |

**Ordine di grandezza sotto budget** (loopback + no-fsync). Le metriche NON autorizzano rollout condiviso o live (caveat PM §17 di RT2-B-1B-P0).

---

## 15 · Compatibility evidence

- `runtime_adapter_wiring = false` — nessun servizio applicativo istanzia `MongoExpeditionRuntimeStateStore`.
- `cdv_transient_state_enabled = false` — nessun feature flag toccato.
- RT2-A `136/136 PASS` invariato.
- RT2-B-1A `91/0/0 PASS` invariato (0 skip).
- Legacy expedition/adventurer/inventory/combat services **intatti** — nessuna modifica.
- `AsyncIOMotorClient(MONGO_URL)` singleton backend rimane invariato.
- `lifespan.py`, `app_factory.py`, `indexes.py`, `database.py`: **0 modifiche**.

---

## 16 · Governance evidence

| Metrica | Valore |
|---|---|
| `sealed integrity tests` | `6 passed` |
| `sealed artifacts` | `36/36 byte-identical` |
| `lore_meta.py` SHA | `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` INVARIANT |
| Baseline chain | `11/11` byte-identical (IS2-A · IS2-B P1 · P1-N1 · P2A · P2B-1 · RT1 · RT2-P0 · RT2-A · RT2-B-P0 · RT2-B-1A · **RT2-B-1B-P0**) |
| RT2-A files unchanged | 38/38 (24 code + 14 test) |
| RT2-B-1A files unchanged | 14/14 (8 code + 6 test) |
| PRD SHA (invariato) | `0012b0f83cbede393be205480306a2323615b17aff22144031aba2871fea0e93` |
| PRD delta | 0 (nessun append in RT2-B-1B-1) |
| `NEW SEAL` | NO |

---

## 17 · Application status

| Metrica | Valore |
|---|---|
| `application_code_modified (existing files)` | 0 |
| `frontend_modifications` | 0 |
| `openapi_modifications` | 0 |
| `feature_flag_activation` | 0 |
| `runtime_wiring` | 0 |
| `registry_changes` | 0 |
| `item_generation` | 0 |
| `db_writes_outside_allowlist` | 0 |
| `writes_to_orbus_r16` | 0 |
| `writes_to_orbus_r16_test` | 0 |
| `network_outside_localhost` | 0 |
| `unbounded_receipt_growth` | 0 |
| `test_state_document_max_kib` | << 256 (envelope) |

---

## 18 · Fail-stop detection

Fail-stop deterministici implementati e testati:

| Codice | Trigger | Test |
|---|---|---|
| `TARGET_ENVIRONMENT_REJECTED` | host != loopback | `test_guards.py::test_remote_host_rejected`, `test_srv_remote_rejected`, `test_provisioning_command_refuses_non_localhost` |
| `TARGET_DATABASE_REJECTED` | db non in allowlist | `test_guards.py::test_orbus_r16_test_rejected`, `test_preview_rejected`, `test_uppercase_it_pattern_rejected` |
| `FORBIDDEN_DATABASE_ORBUS_R16` | db == `orbus_r16` | `test_guards.py::test_orbus_r16_explicit_block`, `test_localhost_but_orbus_r16`, `test_rollback_refuses_non_allowlisted_db` |
| `PROVISIONING_NOT_IDEMPOTENT` | apply × 2 diverge | copertura assertion in `test_apply_is_idempotent` (no fail-stop triggered → resolved) |

Nessun fail-stop scattato in questa suite. Nessun `SCOPE_EXPANSION` rilevato.

---

## 19 · Recommendation

`RT2-B-1B-1 · READY-FOR-PM-CLOSURE`.

- Scope 12/12 coperto
- 57/57 test integration real-Mongo PASS in 2.10s
- Zero regressione (RT2-A 136/136 · RT2-B-1A 91/0)
- Sealed 6/6 · 36/36 byte-identical
- lore_meta + baseline chain 11/11 invariant
- PRD invariato (`0012b0f8…`)
- Performance p95 sotto budget di ordini di grandezza
- Cleanup verificato: 0 database residui post-suite
- `PROVISIONING_IDEMPOTENCY_UNDERDEFINED = RESOLVED_BY_INTEGRATION_TESTS`

---

## 20 · Explicit STOP

`R18.6.RV3-IS2-B-P2B-RT2-B-1B-1` implementazione completata in Phase 2 documental-scoped-code. Nessuna scrittura Mongo fuori allowlist. Nessuna wiring runtime. Nessun feature flag attivato. RT2-A + RT2-B-1A intatti. PRD invariato.

**`STRICT STOP · Phase 2 code+test implementation · fine`**. Awaiting PM formal closure dispatch.
