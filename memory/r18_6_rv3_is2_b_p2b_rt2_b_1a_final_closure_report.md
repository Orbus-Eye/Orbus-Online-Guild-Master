# R18.6.RV3-IS2-B-P2B-RT2-B-1A · Final Closure Report

**Regime**: `DOCUMENTAL_ONLY · Italian_only · SHA Policy §31 · STRICT STOP · non-wired to runtime`
**Gate ID**: `R18.6.RV3-IS2-B-P2B-RT2-B-1A · STATE STORE CONTRACT & NON-WIRED ADAPTER FOUNDATION`
**Stato**: `PM-RATIFIED · CLOSED · PM-LOCKED`
**Data closure**: 2026-02 (UTC)
**Ancoraggio invariante**: `lore_meta.py` SHA256 = `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`

---

## Requisito 1 · PM ratification

Msg #170 originale (RT2-B-1A code gate) + Msg remediation (Opzione B autorizzata) ratificano la chiusura formale di `RT2-B-1A`. `UNEXPECTED_TEST_SKIP = RESOLVED_BY_TEST_REWRITE`.

## Requisito 2 · RT2-B-1A CLOSED

`R18.6.RV3-IS2-B-P2B-RT2-B-1A` → **CLOSED · PM-LOCKED**. Post-closure: nessuna scrittura ulteriore autorizzata sui deliverable + implementation reports + closure artifacts.

## Requisito 3 · Implementation scope 11/11

Tutti gli 11 item autorizzati B0Q10 sono stati consegnati (verificati in implementation report `77dc4172…` / `bc92e363…`).

## Requisito 4 · New files = 14

8 code (stand-alone library) + 6 test (contract + security + schemas + mongo unit + conftest + __init__).

## Requisito 5 · Modified test files during remediation = 1

**Solo `test_security.py`** modificato durante la remediation PM-autorizzata (Opzione B). Il rewrite ha rimosso lo skip `mongo_mock` variant e migrato il monkeypatch a `pytest.MonkeyPatch` fixture (test-scoped, auto-cleanup, safe sotto `pytest-xdist`). **Zero modifiche codice applicativo**. Nessun `TESTABILITY_CONTRACT_GAP` triggered.

## Requisito 6 · RT2-B-1A tests = 91 passed / 0 skipped

Post-remediation: **`RT2-B-1A tests = 91 passed / 0 skipped / 0 failed`** in `0.48s`. Il test `test_receipt_ring_fail_closed` ora passa in entrambe le varianti (`fake` + `mongo_mock`).

## Requisito 7 · Pre-remediation unexpected skip = 1 · resolved = yes

Classificazione: **`UNEXPECTED_TEST_SKIP = RESOLVED_BY_TEST_REWRITE`**.

Storia forense:
- Pre-remediation validation: `90 passed + 1 unexpected skipped` (skip motivato tecnicamente da limite di framework, non da deferimento a RT2-B-1B → mismatch semantico rilevato dall'adjudication PM §2).
- PM remediation Msg (Opzione B): single-test rewrite authorized (solo `test_security.py`).
- Post-remediation validation: **91 passed + 0 skipped**.
- `unexpected skipped tests = 0 post-remediation`.

## Requisito 8 · Unexpected skipped tests = 0 post-remediation

Verificato via `pytest -rs` output: nessun `SKIPPED [n]` nella suite RT2-B-1A post-rewrite.

## Requisito 9 · Planned deferred tests = 0

**Nessun test è marcato come `planned deferred`** per questo gate. La formula "planned deferred = 1" è **NON usata** per il test `test_receipt_ring_fail_closed` (che ora passa) né per alcun altro test.

## Requisito 10 · RT2-A regression = 136/136 passed

Suite completa RT2-A foundation post-remediation: `136 passed in 1.49s`. Zero test regrediti.

## Requisito 11 · Combined pass count = 227

Suite combinata `effect_engine/` (RT2-A + RT2-B-1A): **`227 passed in 1.51s`**.

## Requisito 12 · Store ABC and 11 operations

`ExpeditionRuntimeStateStore` (abstract) con 11 metodi: `create_state · get_state · compare_and_update · apply_event_once · reserve_writer · renew_writer_lease · release_writer · expire_state · delete_state · get_version · health_check`.

## Requisito 13 · State/lease/receipt schemas

`ExpeditionRuntimeState · AdventurerClassState · MarkDoc · DrainDoc · FragmentUsage · WriterLease · EventReceipt` (frozen dataclasses in `models.py`).

## Requisito 14 · CAS and fencing contract

Filtro CAS canonico su ogni mutation: `{_id: expedition_id, state_version: expected_state_version, fencing_token: expected_fencing_token}`. `state_version` monotonic (initial=1). `fencing_token` incrementa su ogni nuova acquisizione lease.

## Requisito 15 · Fake store production prohibition

`FakeExpeditionRuntimeStateStore` marker module-level `PRODUCTION_USE = "FORBIDDEN"` + constructor assertion. Verificato da `test_fake_store_marks_production_use_forbidden`.

## Requisito 16 · Mongo adapter DI-only

`MongoExpeditionRuntimeStateStore(collection, clock=None)`. Costruttore SOLLEVA `ValueError` se `collection is None`. Zero import diretti di `motor`/`pymongo` (verificato da `test_no_direct_db_import_in_adapter`). NON istanziato dal runtime applicativo.

## Requisito 17 · Mocked Mongo validation

Suite `test_mongo_adapter_unit.py` + `test_contract_shared.py[mongo_mock]` gira su `_InMemoryMongoCollectionMock` (custom in-memory replica di API Mongo). Zero DB reali. Zero network.

## Requisito 18 · Security vectors (12)

1. Event replay idempotente (10× retry stesso `event_id` → `DEDUPLICATED_NO_OP`)
2. `EVENT_ID_PAYLOAD_MISMATCH` (client-forged payload)
3. Sequence server-authoritative (client-forge impossibile)
4. Cross-expedition state isolated
5. Lease theft blocked by fencing (`STALE_WRITER_REJECTED`)
6. State version tampering blocked (`STATE_VERSION_CONFLICT`)
7. Fragment cap schema-level (gameplay enforcement HOLD)
8. Duplicate Drain reward via dedup (`drain-exec-42-complete` retry → `DEDUPLICATED_NO_OP`)
9. Cross-adventurer attribution preserved (source_adventurer_id in receipt)
10. Fake store `PRODUCTION_USE = "FORBIDDEN"` marker
11. Fake store no network / no DB (source-level assert)
12. Receipt ring bounded fail-closed (`CAP_EXCEEDED` · 91° test ora attivo su entrambe le varianti)

## Requisito 19 · DB calls = 0 · Network calls = 0

Verificato da test source-level assertion + zero import di `motor`/`pymongo`/`socket`/`requests`/`httpx` in `fake_store.py` e `mongo_adapter.py` (adapter usa injection).

## Requisito 20 · Collection creation = 0 · Index creation = 0 · Runtime wiring = 0

Nessuna operazione infra eseguita durante il gate. Nessun servizio applicativo istanzia `MongoExpeditionRuntimeStateStore`. Provisioning deferito a `RT2-B-1B`.

## Requisito 21 · Feature flags remain false (6)

- `runtime_stat_soft_cap_enabled = false`
- `runtime_stat_shadow_enabled = false`
- `cdv_transient_state_enabled = false` (default OFF · non attivato in questo gate)
- `item_effect_engine_enabled = false`
- `cdv_item_hooks_enabled = false`
- `effect_observability_enabled = false`

`feature flag activation in environments = 0`.

## Requisito 22 · RT2-B-1B provisioning remains separate (HOLD)

Creazione fisica di `expedition_runtime_states`, TTL index su `expires_at`, real DB integration tests, operational approval → **`RT2-B-1B` gate separato · HOLD · NOT AUTHORIZED IN THIS DISPATCH**.

## Requisito 23 · RT2-B-1B-P0 = conditionally authorized (post-closure)

Post-closure di RT2-B-1A: **`RT2-B-1B-P0` (Mongo provisioning readiness plan · DOCUMENTAL ONLY) = CONDITIONALLY AUTHORIZED**. Attende dispatch Phase 2 separato da orchestrator. `RT2-B-1B apply` rimane HOLD.

## Requisito 24 · Governance evidence

- `sealed integrity tests = 6 passed` · `sealed artifacts = 36/36 byte-identical`
- `lore_meta.py SHA = a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` · invariant
- baseline chain `9/9 byte-identical`: IS2-A · IS2-B-P1 · IS2-B-P1-N1 · IS2-B-P2A · IS2-B-P2B-1 · IS2-B-P2B-RT1 · IS2-B-P2B-RT2-P0 · IS2-B-P2B-RT2-A · IS2-B-P2B-RT2-B-P0
- PRD pre-append SHA `dad2f48ab834f1c47cd385f08099b2a3f01b95689c3fa5b4ebbcd58f673a98bd` · **PRD delta = 1 append RT2-B-1A block (idempotent)**
- RT2-A 24 files unchanged
- 13/14 RT2-B-1A files unchanged (1 solo `test_security.py` remediation-edited)
- Implementation reports MD/JSON invariati
- `existing_file_modified = false` per 13/14 file · `remediation_edited = true` per `test_security.py` (esplicito nel manifest)
- `NEW SEAL = NO` · `sealed set size = 36`

## Requisito 25 · STOP esplicito

Formal Closure `RT2-B-1A` completa post-remediation. Nessuna scrittura ulteriore autorizzata in Phase 1. In attesa di dispatch Phase 2 (RT2-B-1B-P0 documental) da orchestrator.

---

**Fine documento** · Italian_only · DOCUMENTAL_ONLY · RT2-B-1A PM-LOCKED · SHA Policy §31 · STRICT STOP
