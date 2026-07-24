# R18.6.RV3-IS2-B-P2B-RT2-B-2B-1 · REAL-MONGO TRANSITION VERIFICATION · Addendum V1

**Gate**: `R18.6.RV3-IS2-B-P2B-RT2-B-2B-1-V1`
**Canonical name**: REAL-MONGO TRANSITION VERIFICATION ADDENDUM
**Parent gate**: `R18.6.RV3-IS2-B-P2B-RT2-B-2B-1` (MARK & RESOURCE STATE TRANSITION FOUNDATION)
**Parent implementation report**: `/app/memory/r18_6_rv3_is2_b_p2b_rt2_b_2b_1_implementation_report.md`
**Status**: **REAL-MONGO VERIFIED · READY-FOR-FORMAL-CLOSURE**
**Regime**: Test/verification only · no new functional scope · localhost isolated · default-OFF · test-user fail-closed
**PM authority**: Message 162 (post-Message-153 verification dispatch)
**Verification date (UTC)**: 2026-02
**Scope**: verification/test-layer-only · **NO** code closure artifact · **NO** PRD append · **NO** baseline increment

---

## 1 · Executive Summary

Verificata la primitive di transizioni class-state RT2-B-2B-1 (Mark / Fragment / Resource Segment / event ordering / lease-fencing / receipt policy 512 / feature-flag composito) contro **MongoDB reale localhost** (non solo FakeStore). Coerente PM Message 153 §§4–10 e Message 162:

- **Matrix real-Mongo 30 item** (§5): `30/30 PASS`
- **Concurrency winner-unico 3 casi** (§6): `3/3 PASS`
- **BSON size @ receipt cap 512** (§7): `162 563 bytes` = **158.75 KiB** · target < 256 KiB · margine **37.98%**
- **Performance p95 MongoStore** separata da FakeStore (§8): tutti i target rispettati (max osservato 2.57 ms vs target 35 ms)
- **Feature gating adapter reale 4 casi** (§9): `4/4 PASS` (flag OFF · non-test-user · invalid ctx · non-allowlisted DB)
- **Governance**: sealed 36/36 byte-identical · lore_meta invariant `a18f708b…65b8f` · baseline chain 14/14 invariata
- **Public API / frontend / production files**: invariati (SHA256 identici pre/post V1)
- **17 fail-stop**: nessuno emesso · nessuna deviazione DESIGN_DEVIATION

### 1.1 · Deterministic failure discovered & fixed (test-layer only)

Durante la prima esecuzione combinata `pytest tests/effect_engine/` sono emerse 66 failure con traceback identico:

```
tests/effect_engine/state_store/test_contract_shared.py:52: in _run
    return asyncio.get_event_loop().run_until_complete(coro)
/usr/local/lib/python3.11/asyncio/events.py:681: in get_event_loop
    raise RuntimeError('There is no current event loop in thread %r.'
E   RuntimeError: There is no current event loop in thread 'MainThread'.
```

**Root cause** (deterministic, non-flaky): il pattern `asyncio.get_event_loop().run_until_complete(coro)` in Python 3.11.15 solleva `RuntimeError` quando nel thread `MainThread` non esiste un loop attivo E non è stato assegnato un default loop dalla policy. Dopo che le fixture di `integration_real_mongo/conftest.py` invocano `asyncio.run(...)` (che crea, esegue e chiude un loop, senza reinstallare il default), i test successivi in `state_store/test_*.py` che chiamano `asyncio.get_event_loop()` senza loop attivo falliscono sempre nell'ordine di raccolta di pytest (con o senza xdist `loadscope`).

**Fix minimale in-scope PM §10** (test/conftest-only, senza toccare produzione):

- `tests/effect_engine/state_store/test_mongo_adapter_unit.py:42` · `_run()`
- `tests/effect_engine/state_store/test_contract_shared.py:52` · `_run()`
- `tests/effect_engine/state_store/test_security.py:54` · `_run()`

Sostituito `asyncio.get_event_loop().run_until_complete(coro)` con `asyncio.new_event_loop().run_until_complete(coro)`, allineato al pattern già ratificato in `tests/effect_engine/transitions/conftest.py:28` (`run()` helper: `return asyncio.new_event_loop().run_until_complete(coro)`).

**Perché confinato al test layer**:
- Ricerca `grep -rn "asyncio.get_event_loop\|asyncio\.get_running_loop" /app/backend/app/stats/` → **0 occorrenze** in codice di produzione
- Nessuna modifica a `mongo_adapter.py`, `dispatcher.py`, `state_machine.py`, `phase.py`, `models.py`, `coordinator.py`, `audit.py` (SHA256 pre = SHA256 post: vedi §7)
- Nessuna modifica a `feature_flags.py`, `provisioning.py`, `state_store/models.py`

**Perché deterministic**:
- La failure appare in **ordine di collezione fisso** (alphabetical, entrambi con `-n 0` e `-n 2 --dist loadscope`)
- Riproducibilità 100% su 5 run consecutivi pre-fix
- Post-fix: 396/396 PASS ripetibile su `-n 0` e su `-n 2 --dist loadscope`

Verdetto governance: **fix di test-hygiene, non design change**. Nessuna DESIGN_DEVIATION emessa.

---

## 2 · Verification Matrix

### 2.1 · §5 Real-Mongo functional matrix (30 item PASS)

| # | test id | area | risultato |
|---|---|---|---|
| 01 | `test_item_01_apply_mark_success` | Mark apply | PASS |
| 02 | `test_item_02_duplicate_pair_rejected` | Mark ownership | PASS |
| 03 | `test_item_03_mark_cap_exceeded` | Mark cap ≤5 | PASS |
| 04 | `test_item_04_refresh_success` | Mark refresh | PASS |
| 05 | `test_item_05_expired_refresh_rejected` | Mark refresh | PASS |
| 06 | `test_item_06_lazy_expiration` | Mark lazy expire | PASS |
| 07 | `test_item_07_opportunistic_cleanup` | Mark cleanup | PASS |
| 08 | `test_item_08_multi_cdv_ownership_isolation` | Ownership | PASS |
| 09 | `test_item_09_fragment_gain_trusted` | Fragment gain | PASS |
| 10 | `test_item_10_fragment_gain_replay_dedup` | Fragment dedup | PASS |
| 11 | `test_item_11_fragment_gain_untrusted_rejected` | Fragment gating | PASS |
| 12 | `test_item_12_fragment_cap_overflow` | Fragment cap 5 | PASS |
| 13 | `test_item_13_fragment_spend_success` | Fragment spend | PASS |
| 14 | `test_item_14_fragment_spend_insufficient` | Fragment insufficient | PASS |
| 15 | `test_item_15_segment_opening` | Segment open | PASS |
| 16 | `test_item_16_partial_spend_preserves_segment` | Segment preserve | PASS |
| 17 | `test_item_17_zero_balance_closes_segment` | Segment auto-close | PASS |
| 18 | `test_item_18_explicit_segment_close` | Segment explicit close | PASS |
| 19 | `test_item_19_phase_end_reset` | Phase reset | PASS |
| 20 | `test_item_20_expedition_terminal_reset` | Expedition terminal | PASS |
| 21 | `test_item_21_event_total_ordering` | Event ordering | PASS |
| 22 | `test_item_22_same_id_same_payload_dedup` | Dedup same payload | PASS |
| 23 | `test_item_23_same_id_diff_payload_rejected` | Payload mismatch | PASS |
| 24 | `test_item_24_ordinary_cap_504_saturation` | Ordinary cap 504 | PASS |
| 25 | `test_item_25_reserved_lifecycle_capacity` | Reserved 8 | PASS |
| 26 | `test_item_26_no_eviction` | No eviction | PASS |
| 27 | `test_item_27_stale_fencing_rejected` | Fencing CAS | PASS |
| 28 | `test_item_28_state_version_cas_conflict` | state_version CAS | PASS |
| 29 | `test_item_29_retry_max_3` | Retry policy | PASS |
| 30 | `test_item_30_terminal_rejects_later_ordinary` | Terminal ordering | PASS |

**File**: `tests/effect_engine/transitions/integration_real_mongo/test_transitions_real_mongo.py` (SHA256 vedi §7)

### 2.2 · §6 Concurrency winner-unico (3/3 PASS)

| # | test id | scenario | risultato |
|---|---|---|---|
| C1 | `test_concurrency_01_mark_apply_single_winner` | 8 dispatcher concorrenti su APPLY_MARK stessa `(source,target)` | PASS · 1 SUCCESS + 7 conflict-mapped |
| C2 | `test_concurrency_02_fragment_spend_single_winner` | 8 dispatcher concorrenti su SPEND_FRAGMENT su balance limitato | PASS · 1 SUCCESS + 7 CAS conflict / insufficient |
| C3 | `test_concurrency_03_phase_reset_single_winner` | Multiplo PHASE_END_RESET concorrente | PASS · 1 SUCCESS + repliche idempotent |

**File**: `tests/effect_engine/transitions/integration_real_mongo/test_atomicity_bson_perf_gating.py`

### 2.3 · §7 BSON size at receipt cap 512 (PASS)

| Metrica | Valore | Target | Verdetto |
|---|---|---|---|
| `bson.encode()` doc size @ 512 receipts | **162 563 byte** (158.75 KiB) | < 262 144 (256 KiB) | **PASS** |
| Margine residuo | **99 581 byte** (97.25 KiB) | ≥ 0 | **PASS** |
| Utilizzo cap | **62.02 %** | ≤ 100 % | **PASS** |

Test: `test_bson_size_at_512_receipts` · valore misurato via `bson.encode(await find_one())` post-scrittura reale su Mongo localhost.

### 2.4 · §8 Performance p95 MongoStore (5/5 PASS)

Sample size = 30 iterazioni per canale, misurate via `time.monotonic()` in ms.

| Operazione | mean (ms) | p95 (ms) | target p95 | verdetto |
|---|---|---|---|---|
| APPLY_MARK | 2.021 | **2.337** | ≤ 35.0 | PASS · margine 93.3 % |
| GAIN_FRAGMENT | 2.034 | **2.437** | ≤ 35.0 | PASS · margine 93.0 % |
| CLOSE_RESOURCE_SEGMENT | 2.078 | **2.569** | ≤ 35.0 | PASS · margine 92.7 % |
| Dedup replay | 1.357 | **1.721** | ≤ 25.0 | PASS · margine 93.1 % |
| flags-OFF short-circuit | 0.008 | **0.009** | ≤ 1.0 (o 5% mark p95) | PASS · margine 99.1 % |

Test: `test_perf_mongo_p95` · file JSON persistito: `/tmp/rt2b2b1_v1_mongo_perf.json`.

**Nota**: p95 MongoStore separata da p95 FakeStore per costruzione (fixture `provisioned_unique_db` istanzia `MongoExpeditionRuntimeStateStore` con `AsyncIOMotorClient` reale su `mongodb://localhost:27017`).

### 2.5 · §9 Feature gating adapter reale (4/4 PASS)

| # | test id | gate condition | verdetto atteso | risultato |
|---|---|---|---|---|
| G1 | `test_gating_01_flag_off_zero_mongo_writes` | `feature_enabled=False` | `FEATURE_DISABLED` · `state_version` invariato · `processed_event_keys=[]` | PASS |
| G2 | `test_gating_02_non_test_user_fail_closed` | `test_user_verified=False` | `TEST_USER_BOUNDARY_VIOLATION` · `state_version` invariato | PASS |
| G3 | `test_gating_03_invalid_ctx_defaults_false` | `trusted_context={}` (all-defaults False) | `FEATURE_DISABLED` (fail-closed) | PASS |
| G4 | `test_gating_04_non_allowlisted_db_fail_closed` | `db_allowlisted=False` | `DB_NOT_ALLOWLISTED` · `state_version` invariato | PASS |

---

## 3 · Full test suite verdicts

### 3.1 · `pytest tests/effect_engine/` combined

| Modalità | Comando | Risultato |
|---|---|---|
| Serial | `python -m pytest tests/effect_engine/ -n 0` | **396 passed** in ~3.79 s · 1 warning benign (starlette PendingDeprecationWarning `multipart`) |
| xdist default | `python -m pytest tests/effect_engine/` (addopts `-n 2 --dist loadscope`) | **396 passed** in ~2.91 s · 1 warning benign |

Breakdown (collezione):
- `foundation/`: 41 test
- `state_store/` (contract + security + adapter unit): 106 test (fake + mongo_mock parametrized)
- `state_store/integration_real_mongo/`: 57 test
- `transitions/` (FakeStore): 37 test
- `transitions/integration_real_mongo/`: 39 test (30 matrix + 3 concurrency + 1 BSON + 1 perf + 4 gating)
- `wiring/`: ~ 116 test (audit/anti_p2w/guardrails/response_invariance/shadow_lifecycle)

### 3.2 · `pytest tests/backend_r18_4_sealed_integrity_test.py`

| test id | descrizione | risultato |
|---|---|---|
| `test_r18_4_b4_seal_01_preexisting_19_byte_identical` | 19 sigilli R18 pre-esistenti | PASS |
| `test_r18_4_b4_seal_02_new_11_byte_identical` | 11 sigilli R18.4 nuovi | PASS |
| `test_r18_4_b4_seal_03_aggregate_count_36` | Aggregate 36/36 | PASS |
| `test_r18_4_b4_seal_04_hash_shape_validity` | SHA256 shape | PASS |
| `test_r18_4_b4_seal_05_no_duplicate_paths` | Nessun path duplicato | PASS |
| `test_r18_4_followup_seal_06_new_6_byte_identical` | 6 sigilli followup UI 4-state | PASS |

**Totale sealed: 36/36 byte-identical (19 + 11 + 6)**

### 3.3 · lore_meta.py invariant

```
sha256(app/content/lore_meta.py) = a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f
```

**Verdetto**: prefix `a18f708b…65b8f` = **INVARIATO** rispetto al baseline R18.4 · governance PASS.

### 3.4 · Baseline chain 14/14

Nessun documento closure/manifest/PRD/append modificato in questa V1. La baseline chain governance (14 file · R18.3d/R18.3e/R18.3f/R18.4/R18.4.followup/R18.5/R18.6.RV3.IC1/IS1/IS2A/IS2B) resta **INVARIATA**.

---

## 4 · MongoDB allowlist compliance

Coerente PM Message 153 §4:

| Parametro | Valore in uso | Allowlist | Verdetto |
|---|---|---|---|
| MONGO_URI | `mongodb://localhost:27017` | localhost / 127.0.0.1 / socket locale | PASS |
| DB name pattern | `orbus_r16_rt2b_it_<unique_run_id>` (via `it_database_name(generate_unique_run_id())`) | `orbus_r16_rt2b_test` OR `orbus_r16_rt2b_it_<unique_run_id>` | PASS |
| Network fuori localhost | 0 | 0 | PASS |
| Residual databases post-teardown | 0 (via `drop_database` in fixture teardown) | 0 | PASS |
| Parallel isolation | unique run_id per fixture invocation | required | PASS |

Fixture attive: `unique_test_db` (fresh DB per test), `provisioned_unique_db` (fresh DB + collection + indici RT2-B provisioning applicato).

---

## 5 · Deviation from previous session

**Correzione DB name accolta e applicata**. La prima proposta ("`orbus_r18_6_rt2b_test`") non era nell'allowlist PM §4 ed avrebbe emesso fail-stop `NON_ALLOWLISTED_DB_WRITE`. L'implementazione effettiva in `integration_real_mongo/conftest.py` usa `it_database_name(generate_unique_run_id())` che produce nomi conformi al pattern `orbus_r16_rt2b_it_<uuid>` (allowlisted). Nessuna scrittura è mai avvenuta su nomi fuori allowlist.

---

## 6 · Fail-stop status

| Fail-stop id | Descrizione | Emesso? |
|---|---|---|
| FS-01 | NON_ALLOWLISTED_DB_WRITE | NO |
| FS-02 | NETWORK_OUTSIDE_LOCALHOST | NO |
| FS-03 | RESIDUAL_TEST_DB | NO |
| FS-04 | BSON_SIZE_BUDGET_EXCEEDED | NO (158.75 KiB < 256 KiB) |
| FS-05 | PERF_P95_TARGET_MISS | NO (max 2.57 ms < 35 ms) |
| FS-06 | GATE_LEAK (flag ON in prod path) | NO |
| FS-07 | TEST_USER_BOUNDARY_LEAK | NO |
| FS-08 | RECEIPT_EVICTION_OBSERVED | NO |
| FS-09 | FENCING_STALE_ACCEPTED | NO |
| FS-10 | STATE_VERSION_TAMPERED | NO |
| FS-11 | DEDUP_PAYLOAD_MISMATCH_ACCEPTED | NO |
| FS-12 | ORDINARY_CAP_504_OVERRUN | NO |
| FS-13 | RESERVED_8_MISUSE | NO |
| FS-14 | CROSS_EXPEDITION_LEAK | NO |
| FS-15 | CROSS_ADVENTURER_LEAK | NO |
| FS-16 | LORE_META_DRIFT | NO (SHA prefix `a18f708b…65b8f` invariato) |
| FS-17 | SEALED_INTEGRITY_DRIFT | NO (36/36 byte-identical) |

**Emessi: 0/17 · Regime FAIL-STOP OFF → REAL-MONGO VERIFIED**

---

## 7 · File integrity snapshot (post-V1)

### 7.1 · Production files (INVARIATI vs implementation report parent)

| Path | SHA256 (post-V1) | Delta |
|---|---|---|
| `backend/app/stats/runtime/state_store/mongo_adapter.py` | `cafb968d41ce62b1934b99279f8f831467926af4a268a13bc9cf34428d4e0bde` | — (patch BSON serialization già registrato nell'implementation report parent §2.2) |
| `backend/app/stats/runtime/transitions/__init__.py` | `899aa33a06647d39fc0335f4946ac9ff405c13f16c2e1c2e46e4bc21229ff863` | INVARIATO |
| `backend/app/stats/runtime/transitions/models.py` | `2150f08c02bd22f1d176d0a74a7cf1dcc7f1979a8b8ec6b4e8675a92f28c5aba` | INVARIATO |
| `backend/app/stats/runtime/transitions/phase.py` | `357493b021e1c56dba21176de3f170e2615ed4883b0feadeea90d7db578d034b` | INVARIATO |
| `backend/app/stats/runtime/transitions/state_machine.py` | `540173037c18491ca3b58a9e24e6b15e79b3ae7a05268a3af768aa53ac83afc5` | INVARIATO |
| `backend/app/stats/runtime/transitions/dispatcher.py` | `3ffb62f550f635e0daf863a2726388dbc90a408dbcf43c6a0813a49314549afe` | INVARIATO |
| `backend/app/stats/runtime/wiring/coordinator.py` | `4ce05b28a480063090bf56e358b19b3e37924aaa0d3d385d7e3a94999b665164` | INVARIATO |
| `backend/app/stats/runtime/wiring/audit.py` | `7c344c49ba25b9489ce04a7f07505a11aa1362dd85fffccd760a551177b05469` | INVARIATO |
| `backend/app/stats/runtime/wiring/__init__.py` | `8272c6beb6b413b5e1903bd8759d43236f6badcfc21972e739c1f6ba381a5cc1` | INVARIATO |
| `backend/app/stats/runtime/wiring/shadow_hooks.py` | `98f1b24b2bf5d231ef1fdf77693c185c20bf47d7d959bb2dfb44ff1e64e0842a` | INVARIATO |
| `backend/app/content/lore_meta.py` | `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` | INVARIATO |

### 7.2 · Test files modificati in V1 (test-layer-only, PM §10)

| Path | SHA256 (post-V1) | Cambio |
|---|---|---|
| `backend/tests/effect_engine/state_store/test_mongo_adapter_unit.py` | `02002d79bc6ad44a7a20db6b16469defed37a36bc33ded0aec250e1cb5765cf6` | `_run()` helper: `get_event_loop` → `new_event_loop` (linee 41-46) |
| `backend/tests/effect_engine/state_store/test_contract_shared.py` | `7e1dabc7839f9e549746bca93e053777b93668f08c06b07f7b9c8c6ca7e0238e` | `_run()` helper: `get_event_loop` → `new_event_loop` (linee 51-56) |
| `backend/tests/effect_engine/state_store/test_security.py` | `8d2c9349b466c75be33a3569a7d4e07d27e921b2d1745b845349049fefe073a6` | `_run()` helper: `get_event_loop` → `new_event_loop` (linee 53-58) |

### 7.3 · Test files nuovi (real-Mongo integration, già inclusi nell'implementation report parent)

| Path | Ruolo |
|---|---|
| `backend/tests/effect_engine/transitions/integration_real_mongo/__init__.py` | package marker |
| `backend/tests/effect_engine/transitions/integration_real_mongo/conftest.py` | fixtures `unique_test_db`, `provisioned_unique_db` (allowlist-safe) |
| `backend/tests/effect_engine/transitions/integration_real_mongo/test_transitions_real_mongo.py` | 30 test matrix §5 |
| `backend/tests/effect_engine/transitions/integration_real_mongo/test_atomicity_bson_perf_gating.py` | 9 test (§6/§7/§8/§9) |

---

## 8 · Ledger deliverable (V1)

| Deliverable | Path | Prodotto? |
|---|---|---|
| Addendum V1 · MD | `/app/memory/r18_6_rv3_is2_b_p2b_rt2_b_2b_1_real_mongo_verification_addendum.md` | YES (questo file) |
| Addendum V1 · JSON | `/app/memory/r18_6_rv3_is2_b_p2b_rt2_b_2b_1_real_mongo_verification_addendum.json` | YES |
| Closure artifact | — | **NO** (verification-only, per PM §10) |
| PRD append | — | **NO** (verification-only) |
| Baseline chain increment | — | **NO** (14/14 invariata) |

---

## 9 · Verdict

**REAL-MONGO VERIFIED · READY-FOR-FORMAL-CLOSURE**

Il gate `R18.6.RV3-IS2-B-P2B-RT2-B-2B-1-V1` completa la verifica real-Mongo del gate parent `RT2-B-2B-1`. Zero fail-stop emessi. Zero deviazioni design. Zero writes su DB fuori allowlist. Zero modifiche produzione oltre la patch adattatore già registrata nel parent (`mongo_adapter.py`). Il fix del test-layer `asyncio.get_event_loop → new_event_loop` è coerente con il pattern già ratificato in `transitions/conftest.py` ed è documentato pre/post SHA in §7.2.

In attesa di formal closure dispatch orchestrator per gate parent `RT2-B-2B-1`.

**HOLD attivi (nessuna deviazione)**:
- Drain runtime · deferred a `RT2-B-2B-2`
- Human tester activation · deferred (fuori regime V1)
- Flag activation (`cdv_class_transitions_enabled`) · resta OFF in produzione
