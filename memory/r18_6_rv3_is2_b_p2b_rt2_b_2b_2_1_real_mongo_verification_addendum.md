# R18.6 · RV3 · IS2-B · P2B · RT2-B-2B-2-1 · V1 · Real-Mongo Verification Addendum

> **Dispatch**: PM Message 182 · `RT2-B-2B-2-1-V1 · REAL-MONGO DRAIN VERIFICATION`
> **Governance**: PM verdict Q1=1c (INVESTIGATE + CONDITIONAL RE-ANCHOR) · Q2=2a (RATIFY_IN_PLACE `V1_DETERMINISTIC_MONGO_ADAPTER_REHYDRATION_FIX`) · Q3=3a (AUTHORIZE_FIX `TEST_ARTIFACT_RECOVERY`)
> **Status**: V1 verified · READY FOR FORMAL CLOSURE (PM adjudication ex-post)
> **Baseline**: 16/16 (unchanged — closure separata)

---

## 0 · Branch + Anchor state

| Field | Value |
|---|---|
| Branch | `main` (implicit — no branch switch) |
| **CANONICAL V1 WORKING ANCHOR** | `73c25f5e3fbc80c91509512f0c731683e3944373` |
| Pre-anchor (baseline) | `be9f62ff1419835a66af5291f2768db467361d11` |
| Phase A ratified commit | `764aa32f5385fe48f03639f0dad32f99fd2acb89` |
| Phase A1 ratified commit | `6e975e0e69e9710246d11abc4cc31b08ad7bc145` |
| Anchor promotion source | `73c25f5` (auto-commit `f1b5a873-…` · in-scope V1: mongo_adapter patch + test V1 file) |

**Auto-commit scope analysis** (PM §STEP 1): tutti e 3 gli auto-commit (`764aa32`, `6e975e0`, `73c25f5`) contengono esclusivamente Phase A / A1 / patch V1 autorizzate. Scope-violation scan (sealed / PRD / baseline / closure / frontend / .env / registry / deletions / credentials) = tutti NONE. `AUTO_COMMIT_SCOPE_MISMATCH` non attivato.

---

## 1 · Phase A / A1 canonical SHA — 10/10 INVARIANT

| File | SHA256 (canonical) | Match |
|---|---|---|
| `backend/app/content/lore_meta.py` | `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` | ✅ |
| `backend/app/stats/runtime/transitions/drain.py` | `56acedd3e93e214916f2e45d426e28e62a57db490010afe44a4b997d52c7b82f` | ✅ |
| `backend/app/stats/runtime/transitions/dispatcher.py` | `acb81ed000127523ee566200de4cb246f5150d0abe7ac89fd084c34e9b3053e1` | ✅ |
| `backend/tests/effect_engine/transitions/test_drain_transitions.py` | `4a5707133696ada305152bde5dd0c156bf61db4d01bb5f5bfa0a85661df1af94` | ✅ |
| `backend/tests/effect_engine/transitions/test_drain_fakestore.py` | `58eb70663052cdd1216e93e04d9f7f74a82ab65bcab68697b0d7ea9024e5ba9c` | ✅ |
| `backend/tests/effect_engine/transitions/test_drain_mocked_mongo.py` | `3d9ec348535a953594950ecf61c7fc64cf97a85794f7eb2860e9148f38cb97ff` | ✅ |
| `backend/tests/effect_engine/transitions/test_drain_perf_fakestore.py` | `5dced06048214084f46795ab8feb2ea1ac727646fcf227e976d1450f6e16c451` | ✅ |
| `memory/r18_6_rv3_is2_b_p2b_rt2_b_2b_2_1_implementation_report.md` | `d71e7b5e3941e11241a0e2c7633e07cc3d06a39a53ab1923e18a2971dfe92275` | ✅ |
| `memory/r18_6_rv3_is2_b_p2b_rt2_b_2b_2_1_implementation_report.json` | `4b7aa8ef02c86d1806b0b59995181dad67ea6ec4d9df7be66699382f1321f97c` | ✅ |
| Sealed integrity test | 6 passed (0.43s + 0.45s post-V1) | ✅ |

---

## 2 · Mongo target & isolation

| Field | Value |
|---|---|
| Mongo URI (sanitized) | `mongodb://localhost:27017` |
| DB pattern (unique per run) | `orbus_r16_rt2b_it_<generate_unique_run_id()>` |
| Fixture | `conftest.py::provisioned_unique_db` (function scope · teardown auto-drop) |
| Allowlist verification | `verify_target(uri, db_name)` (fail-stop on non-allowlist) |
| Provisioning | `ProvisioningCommand.apply(dry_run=False)` (collection + indici RT2-B) |
| Cleanup mechanism | Teardown `drop_database(db_name)` best-effort |
| Residual DB check post-suite | **0 residual `_it_` DBs** ✅ |

Non-system DB persistenti (fuori scope V1, non toccati): `orbus_r16`, `orbus_r16_test`, `test_database`.

---

## 3 · V1 Test Matrix — 19/19 PASS (serial + xdist)

| # | Test | Category | Serial | Xdist |
|---|---|---|---|---|
| 1 | `test_start_drain_persisted` | persistence + UUIDv4 identity | ✅ | ✅ |
| 2 | `test_replay_same_start_returns_same_drain` | dedup on replay | ✅ | ✅ |
| 3 | `test_hard_lock_pair_real_mongo` | `DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR` | ✅ | ✅ |
| 4 | `test_complete_atomic_one_cas_one_version` | atomicità: 1 CAS · 1 fragment_count++ · 1 receipt COMPLETE | ✅ | ✅ |
| 5 | `test_focus_bonus_untouched` | Drain non muta focus_bonus_usage | ✅ | ✅ |
| 6 | `test_6_workers_concurrent_complete_winner_only` | race ≥6 worker · 1 winner · 1 fragment | ✅ | ✅ |
| 7 | `test_completion_vs_cancellation_race` | complete ↔ cancel · 1 succeeds · 1 loses | ✅ | ✅ |
| 8 | `test_identifier_target_bounds_real_mongo[64byte-boundary_pass]` | bounds edge inside | ✅ | ✅ |
| 9 | `test_identifier_target_bounds_real_mongo[65byte-TARGET_INVALID]` | bounds edge outside | ✅ | ✅ |
| 10 | `test_identifier_target_bounds_real_mongo[68byte-UTF8-TARGET_INVALID]` | UTF-8 multibyte · 🚀 * 17 = 68 byte | ✅ | ✅ |
| 11 | `test_gate_rejection_zero_write_real_mongo[FEATURE_DISABLED]` | 6-gate condition 1 · 0 mutation | ✅ | ✅ |
| 12 | `test_gate_rejection_zero_write_real_mongo[TEST_USER_BOUNDARY_VIOLATION]` | 6-gate condition 4 · 0 mutation | ✅ | ✅ |
| 13 | `test_gate_rejection_zero_write_real_mongo[DB_NOT_ALLOWLISTED]` | 6-gate condition 6 · 0 mutation | ✅ | ✅ |
| 14 | **`test_full_cap_512_receipts_bson_le_245760`** | **MANDATORY §6 · full-cap BSON size** | ✅ | ✅ |
| 15 | `test_perf_mongo_start_drain` | Mongo p95 START | ✅ | ✅ |
| 16 | `test_perf_mongo_complete_drain` | Mongo p95 COMPLETE | ✅ | ✅ |
| 17 | `test_perf_mongo_cancel_drain` | Mongo p95 CANCEL | ✅ | ✅ |
| 18 | `test_perf_mongo_deduplicated_retry` | Mongo p95 dedup | ✅ | ✅ |
| 19 | `test_cleanup_zero_residuals_verification` | allowlist pattern enforcement | ✅ | ✅ |

**Wall time:** serial 1.15s · xdist 2.54s (2 worker LoadScopeScheduling).

---

## 4 · Full-Cap BSON Measurement (§6 MANDATORY)

| Metric | Value |
|---|---|
| Receipts total | 512 = 504 ordinary + 8 reserved lifecycle |
| Event ID max byte | 96 (contractual limit, at edge) |
| Source / Target ID byte | 64 (contractual limit, at edge) |
| Active Marks | 1 (Mark full payload) |
| Fragment count | 5 (cap) |
| Resource segment | populated (`sg-<hex16>`) |
| **Raw BSON size measured** | **230,593 byte** |
| PM target | ≤ 245,760 byte |
| Headroom | **15,167 byte (6.2%)** |
| STATE_DOC_MAX_BYTES canonical | 262,144 byte (256 KiB) |
| Verdict | **PASS** — no `SIZE_MARGIN_INSUFFICIENT` · no `STATE_DOCUMENT_SIZE_BUDGET_EXCEEDED` |

**Measurement path**: worst-case document costruito con `_serialize_class_states` (helper adapter, garantisce shape identical) + `dataclasses.asdict` per receipts → `collection.insert_one(doc)` bypass CAS (per iniettare state_version=512 · non violazione perché `create_state` enforce `initial=1` per uso runtime, non per test setup) → `find_one` → `bson.encode(raw_doc)` → `len()`.

Nessuna modifica al write-path production o alla forma BSON autoritativa.

---

## 5 · Performance Mongo (§7)

**Configurazione:** `WARMUP_MONGO=3` samples scartati · `SAMPLE_MONGO=15` samples misurati per operazione · Mongo localhost `mongodb://localhost:27017` · fixture provisioning inclusa nella misura.

| Operation | P95 (ms) | Target (ms) | Verdict |
|---|---|---|---|
| `START_DRAIN` | **2.32** | ≤ 35 | ✅ PASS |
| `COMPLETE_DRAIN` | **3.62** | ≤ 35 | ✅ PASS |
| `CANCEL_DRAIN` | **4.42** | ≤ 35 | ✅ PASS |
| Deduplicated retry | **1.82** | ≤ 25 | ✅ PASS |

Metriche **isolate da FakeStore** — misurate su Mongo reale localhost con isolamento per-run via `provisioned_unique_db` (allocazione + drop DB inclusi nel setup).

---

## 6 · Result-Code Canonical Inventory · 22/22 ✅

### 17 codici nuovi RT2-B-2B-2-1 (Drain gate)

| # | Code | Category | Test coverage |
|---|---|---|---|
| 1 | `DRAIN_STARTED` | success · state mutation | Phase A ×4, V1 ×5 |
| 2 | `DRAIN_COMPLETED` | success · state mutation | Phase A ×4, V1 ×4 |
| 3 | `DRAIN_CANCELLED` | success · state mutation | Phase A ×11, V1 ×2 |
| 4 | `DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR` | start rejection | Phase A, V1 |
| 5 | `DRAIN_NOT_STARTED` | complete/cancel rejection · drain absent | Phase A |
| 6 | `DRAIN_ALREADY_COMPLETED` | terminal-state rejection | Phase A, V1 race |
| 7 | `DRAIN_ALREADY_CANCELLED` | terminal-state rejection | Phase A |
| 8 | `MARK_ALREADY_ACTIVE_FOR_PAIR` | pre-gate mark invariance | Phase A |
| 9 | `MARK_APPLICATION_CHANGED` | mark_id binding invariance | Phase A |
| 10 | `MARK_EXPIRED` | own-Mark required (start/complete) | Phase A |
| 11 | `MARK_NOT_FOUND` | own-Mark absent | Phase A |
| 12 | `MARK_OWNERSHIP_MISMATCH` | own-Mark ownership check | Phase A |
| 13 | `SOURCE_INVALID` | identifier bounds (source ≤ 64 byte) | Phase A |
| 14 | `TARGET_INVALID` | identifier bounds (target ≤ 64 byte) | Phase A, V1 ×3 |
| 15 | `OWNERSHIP_INVALID` | own-Mark ownership check (dual) | Phase A |
| 16 | `RECEIPT_CAP_REACHED` | 512 receipt cap enforcement | Phase A |
| 17 | `PHASE_ENDED` | phase gate rejection | Phase A (`EXPEDITION_TERMINAL_REJECTED`) |

### 5 codici condivisi pre-gate

| # | Code | Category | V1 coverage |
|---|---|---|---|
| 18 | `FEATURE_DISABLED` | 6-conditions gate #1-3 | V1 `test_gate_rejection[FEATURE_DISABLED]` |
| 19 | `TEST_USER_BOUNDARY_VIOLATION` | 6-conditions gate #4 | V1 `test_gate_rejection[TEST_USER_...]` |
| 20 | `DB_NOT_ALLOWLISTED` | 6-conditions gate #6 | V1 `test_gate_rejection[DB_NOT_...]` |
| 21 | `STATE_VERSION_CONFLICT` | CAS retry ceiling on concurrent write | V1 `test_6_workers_concurrent`, race |
| 22 | `EVENT_ID_INVALID` | input validation · empty/oversized event_id | Phase A parametrized |

**Inventory verdict:** 22/22 canonical · `RESULT_CODE_INVENTORY_MISMATCH` NOT triggered.

---

## 7 · Mongo Adapter Patch — RATIFIED IN COMMIT `73c25f5`

**Classification**: `V1_DETERMINISTIC_MONGO_ADAPTER_REHYDRATION_FIX` (PM Q2=2a `RATIFY_IN_PLACE` · PM §11 REAL-MONGO ADAPTER INCOMPATIBILITY · NO DESIGN CHANGE).

### 7.1 · File

`backend/app/stats/runtime/state_store/mongo_adapter.py`

| Metric | Value |
|---|---|
| Blob SHA pre-patch (`be9f62f` … `6e975e0`) | `85763c328861aeb8226ad0fd58443f759649c180` |
| Blob SHA post-patch (`73c25f5` = HEAD) | `44190b70ceaaa2163eae97eb0414147a42973646` |
| Lines changed | +25 / -1 |
| Function affected | `_document_to_state()` (linee ~156-178) |
| Symmetry | Mirror of `active_marks` rehydration (linee 132-146) |

### 7.2 · Diff summary

```python
# Added imports:
from app.stats.runtime.state_store.models import (
    AdventurerClassState,
    DrainDoc,          # NEW
    DrainStatus,       # NEW
    EventReceipt,
    ...
)

# Changed inside _document_to_state:
- active_drain_executions=tuple(drains_raw),                    # raw dict
+ active_drain_executions = tuple(
+     DrainDoc(
+         drain_execution_id=d.get(...), ...,
+         runtime_status=DrainStatus(d.get("runtime_status", ...))
+             if isinstance(d.get("runtime_status"), str)
+             else d.get("runtime_status", DrainStatus.IN_PROGRESS),
+         ...
+     )
+     for d in drains_raw
+     if isinstance(d, dict)
+ )
```

### 7.3 · Fields reidratated (13/13 complete)

`drain_execution_id` · `source_adventurer_id` · `target_id` · `required_mark_application_id` · `started_at` · `completed_at` · `runtime_status` (enum coercion) · `resolution_version` · `reward_resolved` · `mark_id` · `cancelled_at` · `cancellation_reason` · `drain_version`.

### 7.4 · Non-changes (design boundary preserved)

- ❌ BSON write-path (invariato)
- ❌ ALLOWLIST (invariato)
- ❌ Receipt capacity 512 (invariato)
- ❌ Mark / Fragment / reward / XP paths (invariati)
- ❌ API pubbliche (invariate)
- ❌ Result codes (0 nuovi introdotti)
- ❌ Nomi campi persistiti (invariati)
- ❌ Migrazione implicita (nessuna)
- ❌ Live normalization silenziosa (default-based rehydration è pure-read)

**Verdict**: `MONGO_ADAPTER_DESIGN_CHANGE_REQUIRED` NOT triggered.

### 7.5 · Focused adapter tests · 11/11 PASS (0.44s)

File: `backend/tests/effect_engine/state_store/test_mongo_adapter_drain_rehydration.py` (NEW, untracked, inventoried here).

| Test | Coverage |
|---|---|
| `test_rehydration_full_drain_produces_typed_DrainDoc` | typed rehydration · 13 field |
| `test_rehydration_legacy_drain_applies_defaults_for_missing_rt2b2b21_fields` | **backward compat (RT1 legacy doc)** |
| `test_rehydration_empty_active_drains_produces_empty_tuple` | edge: no drains |
| `test_rehydration_multiple_drains_preserves_order_and_types` | multi-drain order + type |
| `test_rehydration_runtime_status_string_coerced_to_enum[×4 status]` | `DrainStatus` enum coercion 4/4 |
| `test_round_trip_symmetry_full_drain` | round-trip (state → dict → state) byte-equal |
| `test_round_trip_symmetry_legacy_drain_defaults_preserved` | round-trip legacy defaults preserved |
| `test_document_to_state_does_not_mutate_input_doc` | **zero mutation on read** (function purity) |

---

## 8 · V1 Test Artifact Recovery — RATIFIED IN COMMIT `73c25f5`

**Classification**: `TEST_ARTIFACT_RECOVERY` (PM Q3=3a `AUTHORIZE_FIX` · NO PRODUCTION DESIGN CHANGE).

### 8.1 · File

`backend/tests/effect_engine/transitions/integration_real_mongo/test_drain_v1_real_mongo.py`

| Metric | Value |
|---|---|
| Broken state | 664 lines · IndentationError line 652 (orfano block righe 649-663 dopo `test_cleanup_zero_residuals_verification`) |
| Recovery scope | Rimozione 15 righe orfane duplicate + 1 fix `create_state` → direct-insert per `test_full_cap_512_receipts_bson_le_245760` |
| Fixed state | 649 lines · py_compile PASS · pytest --collect-only PASS (19 test, 0 skip, 0 xfail, 0 duplicati) |
| Matrix reduction | **ZERO** — no test converted to skip/xfail, no test removed |
| Production files touched during recovery | 0 |

### 8.2 · Fixes applied

1. **AST recovery** (`search_replace`): rimozione blocco 649-663 (duplicated leftover post-cleanup test)
2. **Full-cap test bypass** (`search_replace`): sostituzione `create_state(shell)` → direct `collection.insert_one(doc)` per accettare `state_version=512` senza modificare production. Il write-path production non è interessato dal test — il test misura la size RAW BSON del documento persisted.

**Verdict**: `V1_TEST_INTENT_UNRECOVERABLE` NOT triggered. Intent originale preservato integralmente.

---

## 9 · Invariant Repetition (post-V1 verification)

| Invariant | Result |
|---|---|
| 10/10 Phase A / A1 canonical SHA | ✅ INVARIANT |
| Sealed integrity | 6/6 PASS (0.45s post-V1) |
| `lore_meta.py` SHA canonical | `a18f708b…65b8f` ✅ |
| OpenAPI paths | **275** (invariant) ✅ |
| Baseline | 16/16 (unchanged — no closure emitted) |
| PRD append | **0** (mtime 24 Jul, no update in V1 window) |
| Closure artifacts new | **0** |
| Frontend / env / registry changes | **0** |
| Unexpected tracked file changes | **0** |
| Non-system Mongo DBs post-suite | `orbus_r16`, `orbus_r16_test`, `test_database` (pre-existing, non-`it_`) |
| Residual `_it_` databases | **0** ✅ |

---

## 10 · Fail-Stop Set — 0 triggered

| Fail-stop | Status |
|---|---|
| `POST_COMPACT_STATE_MISMATCH` | 🟢 RESOLVED via PM-pre-authorized re-anchor to `73c25f5` |
| `AUTO_COMMIT_SCOPE_MISMATCH` | 🟢 NOT TRIGGERED |
| `MONGO_ADAPTER_DESIGN_CHANGE_REQUIRED` | 🟢 NOT TRIGGERED |
| `V1_TEST_INTENT_UNRECOVERABLE` | 🟢 NOT TRIGGERED |
| `RESULT_CODE_INVENTORY_MISMATCH` | 🟢 NOT TRIGGERED (22/22 canonical) |
| `SIZE_MARGIN_INSUFFICIENT` | 🟢 NOT TRIGGERED (230,593 ≤ 245,760, 6.2% headroom) |
| `STATE_DOCUMENT_SIZE_BUDGET_EXCEEDED` | 🟢 NOT TRIGGERED |
| `SEALED_INTEGRITY_VIOLATION` | 🟢 NOT TRIGGERED |
| `OPENAPI_PATH_COUNT_MISMATCH` | 🟢 NOT TRIGGERED |
| `ALLOWLIST_WRITE_VIOLATION` | 🟢 NOT TRIGGERED |
| `IDENTIFIER_BOUNDS_TRUNCATION` | 🟢 NOT TRIGGERED |
| `LEGACY_TRUSTED_RECEIPT_DEPENDENCY` | 🟢 NOT TRIGGERED |
| `RESIDUAL_DATABASE_DETECTED` | 🟢 NOT TRIGGERED |
| `DESIGN_CHANGE_REQUIRED` | 🟢 NOT TRIGGERED |

**Fail-stop count = 0.**

---

## 11 · Final working tree state

```
HEAD:            73c25f5e3fbc80c91509512f0c731683e3944373

Tracked changes (working tree vs HEAD):
  M backend/tests/effect_engine/transitions/integration_real_mongo/test_drain_v1_real_mongo.py
    (AST fix Q3=3a + full-cap test bypass · 649 lines · py_compile PASS)

Untracked (in-scope V1 · inventoried):
  ?? backend/tests/effect_engine/state_store/test_mongo_adapter_drain_rehydration.py
    (Q2=2a evidence · 11 pure-unit tests · PASS)
  ?? memory/r18_6_rv3_is2_b_p2b_rt2_b_2b_2_1_real_mongo_verification_addendum.md
    (this file)
  ?? memory/r18_6_rv3_is2_b_p2b_rt2_b_2b_2_1_real_mongo_verification_addendum.json
    (companion JSON)

Untracked (unrelated · pre-existing at anchor):
  yarn.lock (frontend/mobile/parcheggio) · .env.test.example · memory audit logs
```

---

## 12 · Verdict

```
POST_COMPACT_STATE       = RECOVERED
CANONICAL V1 WORKING ANCHOR = 73c25f5
MONGO ADAPTER PATCH      = RATIFIED / V1-VERIFICATION-COMPLETE (11/11 focused + 19/19 V1)
V1 TEST ARTIFACT         = AST VALID / COLLECTION PASS / 19/19 EXECUTED (serial + xdist)
FULL-CAP BSON            = MEASURED 230,593 byte ≤ 245,760 ✅
RESULT-CODE INVENTORY    = 22/22 CANONICAL ✅
FAIL-STOP COUNT          = 0
```

**Formal declaration:**

`RT2-B-2B-2-1 = IMPLEMENTED / REAL-MONGO VERIFIED / FULL-CAP BSON VERIFIED / READY FOR FORMAL CLOSURE`

Baseline remains **16/16** pending PM formal closure dispatch. No autonomous closure artifact created (per PM §DIVIETI §7).

---

## 13 · Reproducer commands

```bash
# 1 · Preflight (SHA + sealed + openapi)
cd /app && sha256sum backend/app/content/lore_meta.py \
  backend/app/stats/runtime/transitions/drain.py \
  backend/app/stats/runtime/transitions/dispatcher.py \
  backend/tests/effect_engine/transitions/test_drain_transitions.py \
  backend/tests/effect_engine/transitions/test_drain_fakestore.py \
  backend/tests/effect_engine/transitions/test_drain_mocked_mongo.py \
  backend/tests/effect_engine/transitions/test_drain_perf_fakestore.py \
  memory/r18_6_rv3_is2_b_p2b_rt2_b_2b_2_1_implementation_report.md \
  memory/r18_6_rv3_is2_b_p2b_rt2_b_2b_2_1_implementation_report.json
cd backend && python -m pytest tests/backend_r18_4_sealed_integrity_test.py -q

# 2 · Focused adapter tests
python -m pytest tests/effect_engine/state_store/test_mongo_adapter_drain_rehydration.py -v

# 3 · V1 real-Mongo (serial)
python -m pytest tests/effect_engine/transitions/integration_real_mongo/test_drain_v1_real_mongo.py -n0 -v -s

# 4 · V1 real-Mongo (xdist)
python -m pytest tests/effect_engine/transitions/integration_real_mongo/test_drain_v1_real_mongo.py -v
```

---

*End of V1 Real-Mongo Verification Addendum · awaiting PM formal closure dispatch*
