# R18.6.RV3-IS2-B-P2B-RT2-B-1B-P0 · Final Closure Report (Phase 1)

**Regime**: `DOCUMENTAL_ONLY · READ-ONLY DISCOVERY · Italian_only · NO APPLY · SHA §31 · STRICT STOP`
**Gate ID**: `R18.6.RV3-IS2-B-P2B-RT2-B-1B-P0 · MONGO PROVISIONING READINESS PLAN`
**Stato**: `PM-RATIFIED · CLOSED · PM-LOCKED`
**Ancoraggio invariante**: `lore_meta.py` SHA256 = `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`
**Data closure**: 2026-02 (UTC)

---

## Requisito 1 · PM verdict

PM dispatch RT2-B-1B-P0 Patch ratifica: (a) 12/12 B1BQ verdicts (verbatim/semantic-equivalent), (b) apertura condizionale `RT2-B-1B-1 · LOCAL ISOLATED MONGO PROVISIONING & REAL ADAPTER INTEGRATION VALIDATION`, (c) architectural lock `LOCAL isolated potentially authorized · SHARED environments forbidden`, (d) formal closure documentale della Phase 1 senza avviare Phase 2.

## Requisito 2 · P0 CLOSED

`R18.6.RV3-IS2-B-P2B-RT2-B-1B-P0` → **`CLOSED · PM-LOCKED`**. Post-closure: nessuna scrittura ulteriore autorizzata sui 2 deliverable P0 patched, sui 3 artefatti closure, e sull'append PRD.

## Requisito 3 · 31/31 sections

Deliverable MD `/app/memory/r18_6_rv3_is2_b_p2b_rt2_b_1b_p0_mongo_provisioning_readiness.md` mantiene **31/31 sezioni** (executive summary … explicit STOP) post-patch. `JSON parse = PASS` sul deliverable JSON companion.

## Requisito 4 · B1BQ resolved = 12/12

Tutte le 12 PM open questions sono state ratificate e integrate verbatim (o semanticamente equivalenti) nel deliverable patched:
- B1BQ01 collection name, B1BQ02 db/env target, B1BQ03 provisioning mechanism,
- B1BQ04 provisioning identity (deroga localhost), B1BQ05 runtime identity,
- B1BQ06 initial indexes, B1BQ07 TTL policy, B1BQ08 backup&retention,
- B1BQ09 monitoring&alerting, B1BQ10 integration-test target,
- B1BQ11 rollback, B1BQ12 first apply slice.

## Requisito 5 · Collection name

`collection name = expedition_runtime_states` · **`DESIGN-LOCKED (B1BQ01)`** · `_id = expedition_id` (nativo, nessun campo duplicato). Provisioning si ferma su schema/indici pre-esistenti incompatibili.

## Requisito 6 · Local target database

Primo apply autorizzabile: **`orbus_r16_rt2b_test`** su `LOCALHOST-ONLY / LOCAL DEVELOPMENT · ISOLATED INTEGRATION`. Integration-test per-run: **`orbus_r16_rt2b_it_<unique_run_id>`**.

## Requisito 7 · Shared-environment prohibition

**VIETATO** primo apply su: `orbus_r16`, `orbus_r16_test`, preview, staging, production. Fail-stop: `Mongo host != localhost → TARGET_ENVIRONMENT_REJECTED`; `database name mismatch → TARGET_DATABASE_REJECTED`. Nessuna eccezione.

## Requisito 8 · Provisioning command model

`EXPLICIT IDEMPOTENT ADMINISTRATIVE COMMAND` + separate `READ-ONLY VERIFICATION COMMAND`. **NON AUTORIZZATI**: application startup provisioning, implicit collection creation during runtime, automatic index creation on service startup. Flags ratificati: `--dry-run · --apply · --verify · --rollback` con target esplicito.

## Requisito 9 · No-auth local exception

Deroga confinata **`LOCAL_TEST_ONLY`** per la sola combinazione `localhost + orbus_r16_rt2b_test | orbus_r16_rt2b_it_<unique_run_id>`. Guardrail obbligatori:
- URI **esattamente** `localhost`
- DB name **esattamente** in allowlist
- **no wildcard** su DB name
- **no accesso** a `orbus_r16`
- **no credenziali di produzione**
- output esplicito del target (URI + DB) **prima** dell'apply

Deroga non estensibile a shared environments.

## Requisito 10 · Future authenticated identity requirements

Ambienti condivisi (futuri, HOLD):
- `provisioning identity` **dedicated authenticated** con privilegi `createCollection · createIndex · dropIndex · dropCollection` limitati a db+collection autorizzati.
- `runtime identity` **dedicated authenticated** con privilegi `find · insert · findOneAndUpdate · update · delete` limitati alla sola `expedition_runtime_states`; **NON deve possedere** `createCollection · createIndex · dropCollection · admin-wide`.
- `diagnostic identity` **read-only** scoped alla collection.

## Requisito 11 · Initial index set

Autorizzabili nel primo apply:
- **I1** `_id` nativo (implicito, `_id = expedition_id`)
- **I2** `expedition_runtime_states_expires_at_ttl` su `expires_at` con `expireAfterSeconds = 0` · **REQUIRED**

DEFERRED (non creare): `runtime_status + expires_at`, `lease_expires_at`, `updated_at`.

## Requisito 12 · TTL values

**PM_RATIFIED (DESIGN-LOCKED per validazione)**:
- `active state inactivity = 6 hours` (`expires_at = last_valid_mutation_ts + 6h`)
- `completed state retention = 24 hours` (`expires_at = completion_ts + 24h`)
- `cancelled state retention = 24 hours` (`expires_at = cancellation_ts + 24h`)

Chiarimento: `Mongo TTL deletion = asynchronous`; `exact deletion time = not guaranteed`; nessuna logica applicativa deve dipendere dalla cancellazione al secondo.

## Requisito 13 · Backup treatment (localhost)

`orbus_r16_rt2b_test`: `backup = NOT REQUIRED · long-term retention = FORBIDDEN · archival = FORBIDDEN · sacrificabile · eliminabile interamente`. Shared env: adjudication operativa separata; baseline `no long-term retention · no automatic reactivation · restored states treated as suspect until manual reconciliation`.

## Requisito 14 · Monitoring boundary

`MONITORING_BASELINE_MISSING = ACKNOWLEDGED`.
- **Non bloccante** per: provisioning locale isolato, IT locale, rollback locale.
- **BLOCCANTE** per: preview, staging, production, runtime wiring in shared env.
- Evidenza minima RT2-B-1B-1 locale: provisioning command output, verification command output, test report, collection stats before/after, index list before/after, cleanup verification.

Nessuna soglia production ratificata in questo gate.

## Requisito 15 · Isolated integration-test target

**`orbus_r16_rt2b_it_<unique_run_id>`** su `localhost:27017`. Requirements:
- `unique_run_id = MANDATORY`
- `parallel isolation = MANDATORY` (compatibile `pytest-xdist -n 2`)
- `cleanup after success = MANDATORY`
- `cleanup after failure = BEST-EFFORT MANDATORY`
- `live data access = FORBIDDEN`

DB fisso `orbus_r16_rt2b_test` per verifica manuale + idempotenza provisioning.

## Requisito 16 · Rollback procedure

**10-STEP RATIFIED** (autorità locale: `operator executing the PM-authorized provisioning dispatch`):
1. verify all feature flags OFF
2. verify runtime wiring absent
3. verify Mongo host = localhost
4. verify database allowlist
5. stop integration-test writers
6. capture collection/index metadata
7. drop `expedition_runtime_states`
8. optionally drop isolated test database
9. verify collection absent
10. rerun compatibility tests

Proprietà: idempotente · target-specifico · dry-run capable · fail-stop su host/database inatteso. Comandi drop generici o senza allowlist: **VIETATI**.

## Requisito 17 · First apply slice (RT2-B-1B-1)

Nome canonico: `R18.6.RV3-IS2-B-P2B-RT2-B-1B-1 · LOCAL ISOLATED MONGO PROVISIONING & REAL ADAPTER INTEGRATION VALIDATION`.

Scope autorizzato (12 item):
1. idempotent provisioning command · 2. read-only verification command · 3. guarded rollback command · 4. collection creation in `orbus_r16_rt2b_test` · 5. TTL index creation on `expires_at` · 6. schema/field validation in test fixtures · 7. real Mongo adapter integration tests · 8. CAS tests · 9. lease/fencing tests · 10. deduplication tests · 11. concurrent mutation tests · 12. cleanup and rollback verification.

Esclusioni esplicite: `orbus_r16` writes, preview/staging/production writes, runtime wiring, expedition service changes, feature flag activation, RT2-A wiring, Marchio/Drenaggio/Frammenti gameplay, public API changes, frontend changes.

## Requisito 18 · No Mongo writes during P0

`mongo_collection_creation = 0` · `mongo_index_creation = 0` · `db_writes = 0` in Phase 1. Nessuna esecuzione di script provisioning/verifica/rollback. Nessun test di integrazione Mongo reale eseguito.

## Requisito 19 · No collection/index creation during P0

Verificato staticamente: nessuna call `db.expedition_runtime_states.*` è stata eseguita. Nessun `create_index`, nessun `createCollection`, nessuna interazione Mongo runtime.

## Requisito 20 · No runtime wiring

`runtime_adapter_wiring = false` invariato. Nessun servizio applicativo istanzia `MongoExpeditionRuntimeStateStore`. Backend `AsyncIOMotorClient(MONGO_URL)` singleton unchanged.

## Requisito 21 · Governance evidence

- `sealed integrity tests = 6 passed`
- `sealed artifacts = 36/36 byte-identical`
- `lore_meta.py SHA = a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` · **INVARIANT**
- baseline chain `10/10 byte-identical`: IS2-A · IS2-B-P1 · IS2-B-P1-N1 · IS2-B-P2A · IS2-B-P2B-1 · IS2-B-P2B-RT1 · IS2-B-P2B-RT2-P0 · IS2-B-P2B-RT2-A · IS2-B-P2B-RT2-B-P0 · IS2-B-P2B-RT2-B-1A
- RT2-A 24 backend + 14 test = 38 file **unchanged**
- RT2-B-1A 8 code + 6 test = 14 file **unchanged**
- RT2-B-1A 5 artefatti (impl MD/JSON + closure MD/JSON/manifest) **invariant**
- PRD pre-append SHA `53e57f14187ad67344b9af80ac5b78471b3a064faf1f7c6cdbdffd4bb93ba7b9` · **PRD delta = 1 append RT2-B-1B-P0 block (idempotent)**
- `application code modified = 0`
- `backend / frontend / OpenAPI modifications = 0`
- `feature flag activation = 0` · `runtime wiring = 0` · `Registry = 0` · `item generation = 0`

## Requisito 22 · STOP esplicito

Formal Closure `RT2-B-1B-P0` **Phase 1** completa. Nessuna scrittura ulteriore autorizzata in Phase 1. In attesa di dispatch separato **Phase 2 (`RT2-B-1B-1`)** da orchestrator.

**`STRICT STOP · Phase 1 documentale`**.

---

**Stato punti critici (post-Phase 1)**:
- `TARGET_DATABASE_UNDERDEFINED = RESOLVED`
- `MONGO_PERMISSION_MODEL_UNDERDEFINED = RESOLVED TRANSITIONALLY`
- `MONITORING_BASELINE_MISSING = ACKNOWLEDGED`
- `PROVISIONING_IDEMPOTENCY_UNDERDEFINED = TO BE VERIFIED IN RT2-B-1B-1`

---

**Fine documento** · Italian_only · DOCUMENTAL_ONLY · RT2-B-1B-P0 PM-LOCKED · SHA Policy §31 · STRICT STOP
