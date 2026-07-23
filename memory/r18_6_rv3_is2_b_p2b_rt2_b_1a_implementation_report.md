# R18.6.RV3-IS2-B-P2B-RT2-B-1A · Implementation Report

**Regime**: `NEW_MODULE code gate · Italian_only · SHA Policy §31 · STRICT STOP · non-wired to runtime`
**Gate ID**: `R18.6.RV3-IS2-B-P2B-RT2-B-1A · STATE STORE CONTRACT & NON-WIRED ADAPTER FOUNDATION`
**Data**: 2026-02 (UTC)
**Ancoraggio invariante**: `lore_meta.py` SHA256 = `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`
**PRD reference (post-RT2-B-P0 closure · INVARIANT this gate)**: SHA256 = `dad2f48ab834f1c47cd385f08099b2a3f01b95689c3fa5b4ebbcd58f673a98bd`

---

## Sezione 1 · Scope executed vs authorized (11/11)

Tutti gli 11 item autorizzati dal PM in `RT2-B-P0 §37` (B0Q10 verdict verbatim) sono stati implementati:

| # | Item autorizzato | Consegnato in |
|---:|---|---|
| 1 | `ExpeditionRuntimeStateStore` interface (11 ops) | `interface.py` |
| 2 | State schemas (Expedition + AdventurerClassState) | `models.py` |
| 3 | Lease schemas (WriterLease + fencing_token) | `models.py` |
| 4 | Fencing-token validation (pure logic) | `fencing.py` |
| 5 | CAS result types (enum + dataclasses) | `results.py` |
| 6 | Event receipt schemas | `models.py` (`EventReceipt`) |
| 7 | Fake in-memory test store · PRODUCTION_USE=FORBIDDEN | `fake_store.py` |
| 8 | Mongo adapter with injected collection · NON-WIRED | `mongo_adapter.py` |
| 9 | Shared contract-test suite parametrizzata fake/mongo-mock | `conftest.py` + `test_contract_shared.py` |
| 10 | Unit tests with mocked Mongo collection | `test_mongo_adapter_unit.py` |
| 11 | Security and validation tests (≥10 vettori) | `test_security.py` + `test_schemas.py` |

## Sezione 2 · File aggiunti (14 nuovi · 0 modifiche a file esistenti)

Vedi il JSON companion `section_02_new_files_added` per SHA256 · line count · byte size di ciascun file (8 code + 6 test).

- Package root code: `/app/backend/app/stats/runtime/state_store/`
- Package root test: `/app/backend/tests/effect_engine/state_store/`

## Sezione 3 · Struttura moduli state-store

```
/app/backend/app/stats/runtime/state_store/
├── __init__.py         · public exports
├── interface.py        · ExpeditionRuntimeStateStore ABC (11 ops)
├── models.py           · State / Lease / Receipt / ClassState schemas
├── results.py          · CasResultCode enum + CasResult / LeaseAcquireResult / ReadResult
├── errors.py           · StoreError hierarchy
├── fencing.py          · fencing / state_version validation (pure logic)
├── fake_store.py       · in-memory · TEST-ONLY (PRODUCTION_USE=FORBIDDEN)
└── mongo_adapter.py    · DI collection · NON-WIRED (0 direct motor/pymongo imports)
```

## Sezione 4 · `ExpeditionRuntimeStateStore` · 11 operazioni

`create_state · get_state · compare_and_update · apply_event_once · reserve_writer · renew_writer_lease · release_writer · expire_state · delete_state · get_version · health_check`.

Ogni operazione è documentata via docstring con: preconditions · atomicity guarantee · idempotency · conflict result · timeout behavior · retry behavior · audit event · failure code.

## Sezione 5 · State schema

`ExpeditionRuntimeState` (frozen dataclass): `expedition_id · state_version (monotonic int, initial=1 · B0Q04) · created_at · updated_at · expires_at · runtime_status · owner_worker_or_lease_id · lease · loadout_snapshot_version (reserved RT2-A future wiring) · adventurer_class_states · processed_event_keys (bounded ring MAX=500 default) · last_event_sequence · fencing_token`.

Immutable. Cambio di stato SEMPRE via CAS + nuova istanza. Valori finali item ESCLUSI (mandato RT2-B-P0 §7).

## Sezione 6 · Lease schema

`WriterLease` (frozen dataclass): `lease_id · owner_id · acquired_at · expires_at · renewed_at · lease_version · fencing_token (monotonic)`. Defaults verbatim B0Q08: `lease_duration=30s · renewal_interval=10s · grace_period=5s`. `fencing_token` incrementa ad **ogni nuova acquisizione**, **preservato** su renewal.

## Sezione 7 · CAS result types

Enum `CasResultCode` con 10 codici stabili stringati: `SUCCESS · STATE_VERSION_CONFLICT · STALE_WRITER_REJECTED · DEDUPLICATED_NO_OP · EVENT_ID_PAYLOAD_MISMATCH · OWNERSHIP_INVALID · CAP_EXCEEDED · LEASE_EXPIRED · NOT_FOUND · ALREADY_EXISTS`. Dataclasses risultato: `CasResult · LeaseAcquireResult · ReadResult`. **Partial mutation vietata**: se `code != SUCCESS`, nessun campo dello stato è cambiato.

## Sezione 8 · Event receipt schema

`EventReceipt` (frozen dataclass): `event_id · event_type · source_adventurer_id · payload_hash · assigned_event_sequence · result_code · state_version_after · processed_at`. Dedup key = `(expedition_id, event_id)`. Retention allineata al lifetime del documento stato. Ring bounded (`MAX_PROCESSED_EVENTS`). Al limite: `CAP_EXCEEDED` fail-closed (no eviction durante expedition attiva).

## Sezione 9 · Fake in-memory store

`FakeExpeditionRuntimeStateStore` con storage `dict[expedition_id, ExpeditionRuntimeState]` + `asyncio.Lock`. Marker esplicito: `PRODUCTION_USE = "FORBIDDEN"` (module-level constant). Il costruttore contiene `assert PRODUCTION_USE == "FORBIDDEN"` come sanity gate. Solo per test/dev/fixture. Clock iniettabile per test deterministici.

## Sezione 10 · Mongo adapter

`MongoExpeditionRuntimeStateStore(collection, clock=None)`. Costruttore SOLLEVA `ValueError` se `collection is None`. Nessun import di `motor` / `pymongo` (verificato via test `test_no_direct_db_import_in_adapter` che fa grep del source e assert `== 0` occorrenze). Filtro CAS canonico su ogni mutation:

```
{_id: expedition_id, state_version: expected_state_version, fencing_token: expected_fencing_token}
```

Primitiva atomica: `find_one_and_update` con `$inc {state_version: 1} + $set mutation + updated_at ISO`. In `apply_event_once`, il filtro include anche il guard concorrente `processed_event_keys.event_id: {$ne: event_id}`. Error mapping: qualsiasi exception adapter-level → `StoreInfraError`. **NON istanziato dal runtime applicativo.**

## Sezione 11 · Shared contract-test suite

`conftest.py` espone la fixture `store` parametrizzata su `["fake", "mongo_mock"]`. Il `mongo_mock` variant usa un `_InMemoryMongoCollectionMock` custom (in-memory, no `mongomock` dependency) che replica il subset di API Mongo usato dall'adapter (`insert_one · find_one · find_one_and_update · delete_one`) con matching di operatori (`$or · $ne · $lt · $gt · $nin` + equality). Il file `test_contract_shared.py` contiene ~19 test parametrizzati che girano identicamente su entrambe le implementazioni: create + get + not_found · duplicate create · lease acquire/renew/release · lease expiry → new fencing token · CAS success/conflict/stale · dedup idempotent · EVENT_ID_PAYLOAD_MISMATCH · sequence + version monotonicity · expire/delete/get_version/health.

## Sezione 12 · Unit tests Mongo adapter

`test_mongo_adapter_unit.py`: injection contract (None → ValueError · AsyncMock accepted) · CAS filter shape verification via call log inspection · dedup guard `$ne` on `processed_event_keys.event_id` verification · error mapping (`RuntimeError → StoreInfraError`) su `find_one` e `find_one_and_update` · duplicate insert → `ALREADY_EXISTS` · `get_state` reconstruction · **assert source-level 0 import di motor/pymongo**.

## Sezione 13 · Security tests

`test_security.py` + `test_schemas.py` coprono i 12 vettori (≥10 richiesti):
1. Event replay idempotente (10 retry stesso event_id → DEDUPLICATED_NO_OP)
2. `EVENT_ID_PAYLOAD_MISMATCH` (client-forged payload)
3. Sequence server-authoritative (client non sceglie)
4. Cross-expedition state isolated (mutation su A non tocca B)
5. Lease theft blocked (fencing mismatch → `STALE_WRITER_REJECTED`)
6. State version tampering blocked (`state_version=999` → `STATE_VERSION_CONFLICT`)
7. Over-cap Fragment injection (schema-level; gameplay enforcement HOLD)
8. Duplicate Drain reward via dedup (`drain-exec-42-complete` retry → `DEDUPLICATED_NO_OP`)
9. Cross-adventurer attribution preserved (`source_adventurer_id` in receipt)
10. Fake store `PRODUCTION_USE = "FORBIDDEN"` marker asserted
11. Fake store no network/DB (source-level grep asserts)
12. Receipt ring fail-closed at limit

## Sezione 14 · Test count + esito

- `RT2-B-1A state_store suite`: **90 passed + 1 skipped** (skip = `test_receipt_ring_fail_closed[mongo_mock]`, deterministic-only fake variant).
- `RT2-A foundation suite`: **136/136 passed** (regressione = 0).
- `Sealed integrity`: **6 passed** · `sealed artifacts = 36/36 byte-identical`.
- `Combined RT2-A + RT2-B-1A`: **226 passed + 1 skipped**.

## Sezione 15 · Compatibility evidence

- `RT2-A files unchanged = 24/24` (10 backend module + 14 test file · SHAs invariati).
- `cdv_transient_state_enabled` flag remains `false` · nessuna attivazione.
- Nessun servizio expedition esistente istanzia `MongoExpeditionRuntimeStateStore`.
- La libreria RT2-B-1A è **raggiungibile solo dai test**.
- Legacy expeditions / legacy items: 0 dipendenze aggiunte.
- RT1 baseline power calculation: unchanged.

## Sezione 16 · Governance

- `sealed integrity tests = 6 passed` · `sealed artifacts = 36/36 byte-identical`
- `lore_meta.py` SHA `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` invariant
- **Baseline invariance chain 9/9 byte-identical**: IS2-A · IS2-B-P1 · IS2-B-P1-N1 · IS2-B-P2A · IS2-B-P2B-1 · IS2-B-P2B-RT1 · IS2-B-P2B-RT2-P0 · IS2-B-P2B-RT2-A · IS2-B-P2B-RT2-B-P0
- `RT2-A 24 files unchanged` (verificato pre/post-gate via SHAs registrati)
- `PRD invariato` (SHA `dad2f48a...`) · no append RT2-B-1A in questa fase
- `NEW SEAL = NO` · `sealed set size = 36`

## Sezione 17 · Application status (tutti a 0)

`code(non-wired)=14 nuovi file NON istanziati dal runtime · frontend modifications=0 · OpenAPI=0 · DB writes=0 · Mongo collection creation=0 · Mongo index creation=0 · migrations=0 · feature flag activation=0 · runtime wiring=0 · Registry=0 · item generation=0 · database calls in tests=0 · network calls in tests=0`.

## Sezione 18 · Fail-stop detection

**NONE**. Nessuna espansione di scope. Nessuna necessità di DB reale. Nessuna violazione di governance. Nessuna regressione sui 136 test RT2-A.

## Sezione 19 · Recommendation

**`RT2-B-1A = READY-FOR-PM-CLOSURE`**. Motivazione: 11/11 item autorizzati consegnati · 90 store tests PASS + 1 skipped deterministic · 136/136 RT2-A regressione 0 · 6/6 sealed integrity · adapter DI-only · zero wiring · zero DB · zero network · RT2-A intatto · baseline chain 9/9. Next gate: `R18.6.RV3-IS2-B-P2B-RT2-B-1B` (Mongo collection + TTL index provisioning · **NOT AUTHORIZED** in questo dispatch).

## Sezione 20 · STOP esplicito

Implementazione code completa. Library stand-alone non-wired. In attesa del verdict PM di formal closure per l'append PRD e la lock definitiva del gate.

---

**Fine documento** · Italian_only · NEW_MODULE code gate · RT2-B-1A · SHA §31 · STRICT STOP
