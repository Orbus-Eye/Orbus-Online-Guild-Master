# R18.6.RV3-IS2-B-P2B-RT2-B-1B-1 · Final Closure Report (Phase 1)

**Regime**: `DOCUMENTAL_ONLY · Italian_only · SHA §31 · STRICT STOP · LOCAL ISOLATED ONLY`
**Gate ID**: `R18.6.RV3-IS2-B-P2B-RT2-B-1B-1 · LOCAL ISOLATED MONGO PROVISIONING & REAL ADAPTER INTEGRATION VALIDATION`
**Stato**: `PM-RATIFIED · CLOSED · PM-LOCKED`
**Anchor**: `lore_meta.py` SHA `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` · INVARIANT
**Data closure**: 2026-02 (UTC)

---

## Requisito 1 · PM ratification

PM VERDICT: `LOCAL_MONGO_PROVISIONING_IMPLEMENTED · REAL_ADAPTER_TESTED · ALLOWLIST-GUARDED · IDEMPOTENT · ROLLBACK-VERIFIED · LOCALHOST-ONLY · NOT_RUNTIME_WIRED · NOT_PLAYER-AFFECTING`. Formal closure autorizzata. Shared-environment provisioning NOT AUTHORIZED. Runtime wiring NOT AUTHORIZED.

## Requisito 2 · Gate CLOSED

`RT2-B-1B-1 = CLOSED · PM-LOCKED`. Nessuna modifica ulteriore autorizzata su codice, test o report.

## Requisito 3 · Scope 12/12

Coverage integrale del verdict `B1BQ12`: idempotent provisioning · verification · rollback · collection creation · TTL index · schema/field validation · real Mongo adapter integration · CAS · lease/fencing · dedup · concurrent · cleanup.

## Requisito 4 · New files = 16 · Existing files modified = 0

- 4 code in `state_store/provisioning/` (`__init__`, `guards`, `unique_run_id`, `provisioning_command`)
- 12 test in `integration_real_mongo/` (2 support + 10 test file)
- Zero file esistenti modificati (verificato via SHA snapshot).

## Requisito 5 · Real Mongo tests = 57/57 PASS

`tests/effect_engine/state_store/integration_real_mongo/` — 57 test PASS in 2.10s. Zero flake.

## Requisito 6 · Combined regression = 284 PASS

`RT2-A = 136/136` + `RT2-B-1A = 91/91` + `RT2-B-1B-1 = 57/57` = **284 combined PASS**. Zero regressione.

## Requisito 7 · Idempotency validated

`test_apply_is_idempotent` + `test_apply_three_times_stable` → index signature identiche cross-run. Fail-stop `PROVISIONING_IDEMPOTENCY_UNDERDEFINED` = **`RESOLVED_BY_REAL_MONGO_INTEGRATION_TESTS`**.

## Requisito 8 · Rollback validated · residual databases = 0

`test_rollback_drops_collection`, `test_full_cycle_apply_rollback_reapply`, `test_rollback_idempotent_when_missing` → PASS. Post-suite `list_database_names()` → **0 database `orbus_r16_rt2b_it_*` residui**.

## Requisito 9 · Host/database guardrails attivi

- `TARGET_ENVIRONMENT_REJECTED` — host != loopback (test coverage: 3 test)
- `TARGET_DATABASE_REJECTED` — db non in allowlist (test coverage: 6 test)
- `FORBIDDEN_DATABASE_ORBUS_R16` — blocco esplicito `orbus_r16` (test coverage: 3 test)
- `DB_SCOPE_VIOLATION` — testato via `test_no_orbus_r16_writes_across_run` + `test_no_orbus_r16_test_writes`

## Requisito 10 · Collection e identity

Collection: `expedition_runtime_states`. Identity: **native `_id = expedition_id`** (nessun campo duplicato). Verificato via `test_apply_creates_collection_and_ttl_index`.

## Requisito 11 · TTL index

`expedition_runtime_states_expires_at_ttl` su `expires_at` con `expireAfterSeconds = 0`. Verificato via `list_indexes()` post-apply.

## Requisito 12 · CAS validation

`test_cas_real.py`: 6/6 PASS (create+get · duplicate `ALREADY_EXISTS` · CAS success · `STATE_VERSION_CONFLICT` · `STALE_WRITER_REJECTED` · state_version monotonicity).

## Requisito 13 · Lease and fencing validation

`test_lease_real.py`: 4/4 PASS (acquire · second acquire rejected while active · renewal preserves fencing token · release + reacquire bumps token).

## Requisito 14 · Deduplication validation

`test_dedup_real.py`: 3/3 PASS (idempotent no-op · `EVENT_ID_PAYLOAD_MISMATCH` · 10-retry loop).

## Requisito 15 · Concurrency validation

`test_concurrent_real.py`: 3/3 PASS (4-way CAS race → 1 winner · 3-way lease race → 1 winner · 5-expedition isolation).

## Requisito 16 · Performance results (verbatim)

- `single-state read p95 = 0.21ms / 25ms budget`
- `CAS mutation p95 = 0.30ms / 35ms budget`
- `lease acquire p95 = 0.68ms / 35ms budget`
- `lease renew p95 = 0.39ms / 35ms budget`
- `dedup retry p95 = 0.27ms / 25ms budget`

Tutti sotto budget di ordini di grandezza. Caveat: `local metrics do NOT authorize shared or live rollout`.

## Requisito 17 · Writes limited to allowlisted databases

DB writes esclusivamente su: `orbus_r16_rt2b_test` (verifica manuale/idempotency) + `orbus_r16_rt2b_it_<unique_run_id>` (integration tests per-run). Guardrail statici + runtime enforcement.

## Requisito 18 · No writes fuori scope

- `orbus_r16` writes = **0** (verificato via `test_no_orbus_r16_writes_across_run`)
- `orbus_r16_test` writes = **0** (verificato via `test_no_orbus_r16_test_writes`)
- Network outside localhost = **0** (guardrail `verify_host_localhost` obbligatorio prima di ogni Mongo op)

## Requisito 19 · Residual databases = 0

Post-suite verification via `list_database_names()` → `orbus_r16_rt2b_it_*` residues = **0**. Teardown fixture `unique_test_db` esegue `drop_database` in loop dedicato (isolato dal loop del test).

## Requisito 20 · Runtime wiring = 0

`MongoExpeditionRuntimeStateStore` istanziato **esclusivamente dai test**. Nessun servizio applicativo (expedition/adventurer/inventory/combat) importa il modulo `provisioning`. Backend `AsyncIOMotorClient(MONGO_URL)` singleton unchanged.

## Requisito 21 · Feature flags OFF

`cdv_transient_state_enabled = false` · `runtime_stat_soft_cap_enabled = false` · `runtime_stat_shadow_enabled = false` · `item_effect_engine_enabled = false` · `cdv_item_hooks_enabled = false` · `effect_observability_enabled = false`. Nessun toggle in Phase 1 né in Phase 2 RT2-B-1B-1.

## Requisito 22 · Shared-environment provisioning HOLD

Blockers ancora aperti per apply su preview/staging/production:
- `authenticated identities` (provisioning + runtime + diagnostic) — non implementate in shared env
- `environment boundary` — prod DB non definito con evidenza empirica
- `monitoring baseline` — assente (nessuna piattaforma metrics integrata)
- `alerting` — nessuna regola configurata
- `backup policy` — non adjudicata per shared env

## Requisito 23 · Local isolated configuration approved

Configurazione collection/index/guardrail approvata **esclusivamente** per `LOCALHOST-ONLY / LOCAL ISOLATED INTEGRATION`. Non estensibile ad ambienti condivisi senza adjudication PM separata.

## Requisito 24 · Governance evidence

- `sealed integrity tests = 6 passed`
- `sealed artifacts = 36/36 byte-identical`
- `lore_meta.py` SHA `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` — **INVARIANT**
- Baseline chain **11/11 byte-identical**: IS2-A · IS2-B-P1 · IS2-B-P1-N1 · IS2-B-P2A · IS2-B-P2B-1 · IS2-B-P2B-RT1 · IS2-B-P2B-RT2-P0 · IS2-B-P2B-RT2-A · IS2-B-P2B-RT2-B-P0 · IS2-B-P2B-RT2-B-1A · IS2-B-P2B-RT2-B-1B-P0
- RT2-A 38 file **unchanged** · RT2-B-1A 14 file **unchanged**
- PRD pre-append SHA `0012b0f83cbede393be205480306a2323615b17aff22144031aba2871fea0e93` · **PRD delta = 1 append RT2-B-1B-1 block (idempotent)**
- `application_code_modified (existing files) = 0`
- Frontend / OpenAPI / Registry / item-gen / FF activation / runtime wiring = **0**

## Requisito 25 · Explicit STOP

Formal closure `RT2-B-1B-1` completa. Nessuna scrittura ulteriore autorizzata in Phase 1. In attesa di dispatch separato **Phase 2 (`RT2-B-2-P0 · Local Runtime Wiring Readiness Plan`)** da orchestrator.

**`STRICT STOP · Phase 1 documentale · fine`**.

---

**Fine documento** · Italian_only · DOCUMENTAL_ONLY · RT2-B-1B-1 PM-LOCKED · SHA Policy §31 · STRICT STOP
