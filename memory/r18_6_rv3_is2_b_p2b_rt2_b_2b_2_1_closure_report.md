# R18.6 · RV3 · IS2-B · P2B · RT2-B-2B-2-1 · Closure Report

> **Gate**: `RT2-B-2B-2-1` · Drain Transition & Completion-to-Fragment Foundation
> **Dispatch**: PM `AUTHORIZE_FORMAL_CLOSURE RT2-B-2B-2-1` (10-step integral dispatch)
> **Status**: `CLOSED · PM-LOCKED`

---

## 0 · Identity

| Field | Value |
|---|---|
| gate_id | `RT2-B-2B-2-1` |
| gate_title | Drain Transition & Completion-to-Fragment Foundation |
| closure_timestamp_utc | `2026-07-27T21:03:25Z` |
| pre_closure_baseline | `16/16` |
| **post_closure_baseline** | **`17/17`** |
| canonical_v1_anchor | `73c25f5e3fbc80c91509512f0c731683e3944373` |
| canonical_head_at_closure_start | `787b5a3a2d953e2ec2d0e8235021f00efce045af` |
| closure_commit | `PENDING` (STEP 9 output · to be registered in chat report post-commit) |

---

## 1 · Status declaration

```
RT2-B-2B-2-1 = CLOSED / PM-LOCKED
Phase A                  = COMPLETE
Phase A1 remediation     = COMPLETE
V1 real-Mongo            = COMPLETE
full-cap BSON            = VERIFIED (230,593 bytes ≤ 245,760)
deployment authorization = NOT AUTHORIZED
tester environment       = UNCHANGED
online feature flag      = NOT ACTIVATED (default OFF preserved)
```

---

## 2 · Scope implemented

- `START_DRAIN` · `COMPLETE_DRAIN` · `CANCEL_DRAIN` (17 result codes)
- Full rejection paths (`DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR`, `DRAIN_NOT_STARTED`, `DRAIN_ALREADY_COMPLETED`, `DRAIN_ALREADY_CANCELLED`)
- UUIDv4 server-side generation for `drain_execution_id`
- Mark ↔ Drain application binding invariance (`MARK_APPLICATION_CHANGED`, `MARK_OWNERSHIP_MISMATCH`)
- Fragment gain atomic mutation in COMPLETE_DRAIN (1 CAS · 1 state_version increment · 1 receipt)
- Overflow handling · resource segment materialization
- Authoritative `processed_event_keys` receipt (RAW BSON, no separate slot for completion)
- Lifecycle aggregation (start · complete · cancel receipts unified in ordinary ring)
- Lease · fencing token · CAS enforcement
- Deduplication by `event_id` · race (6-worker concurrent COMPLETE, complete↔cancel)
- Identifier bounds enforcement (source ≤ 64B, target ≤ 64B, event_id ≤ 96B — UTF-8 aware, zero mutation on invalid)
- 6-conditions feature gating (all-AND · short-circuit · default OFF)
- Localhost + Mongo allowlist isolation
- Audit map (10 event IDs)
- **Mongo adapter DrainDoc rehydration** (`_document_to_state` symmetric to active_marks)

---

## 3 · Deterministic patches applied (all NO DESIGN CHANGE)

### 3.1 · Dispatcher positive-mutation result-code fix (Phase A1 remediation)

| Field | Value |
|---|---|
| Root cause | dispatcher only recognized `SUCCESS` code as positive mutation; missed `DRAIN_STARTED`, `DRAIN_COMPLETED`, `DRAIN_CANCELLED` |
| File | `backend/app/stats/runtime/transitions/dispatcher.py` |
| Blob SHA pre-patch | (Phase A · pre-A1) |
| Blob SHA post-patch | `acb81ed000127523ee566200de4cb246f5150d0abe7ac89fd084c34e9b3053e1` |
| Diff summary | Added `DRAIN_STARTED`, `DRAIN_COMPLETED`, `DRAIN_CANCELLED` to positive-mutation code set |
| Verified by | `test_drain_fakestore.py` (positive-mutation invariance tests) |
| NO DESIGN CHANGE | ✅ (result codes unchanged, only recognition set extended) |

### 3.2 · Mongo adapter Drain rehydration (V1 real-Mongo prerequisite)

| Field | Value |
|---|---|
| Classification | `V1_DETERMINISTIC_MONGO_ADAPTER_REHYDRATION_FIX` (PM Q2=2a ratified) |
| Root cause | `_document_to_state` stored `active_drain_executions` as raw dict tuple; V1 read-back requires typed `DrainDoc` instances |
| File | `backend/app/stats/runtime/state_store/mongo_adapter.py` |
| Blob SHA pre-patch | `85763c328861aeb8226ad0fd58443f759649c180` |
| Blob SHA post-patch | `44190b70ceaaa2163eae97eb0414147a42973646` |
| Lines changed | +25 / -1 |
| Diff summary | Added `DrainDoc`/`DrainStatus` imports; replaced `tuple(drains_raw)` with typed rehydration via `DrainDoc(...)` generator, symmetric to `active_marks` rehydration |
| Fields rehydrated | 13/13 (drain_execution_id, source_adventurer_id, target_id, required_mark_application_id, started_at, completed_at, runtime_status [enum coercion], resolution_version, reward_resolved, mark_id, cancelled_at, cancellation_reason, drain_version) |
| Verified by | `test_mongo_adapter_drain_rehydration.py` (11/11 PASS) + V1 real-Mongo persistence assertions |
| NO DESIGN CHANGE | ✅ (no new result codes, no field renames, no migration, no live normalization, BSON write-path unchanged, capacity unchanged, API unchanged) |

### 3.3 · V1 test artifact recovery (test-only)

| Field | Value |
|---|---|
| Classification | `TEST_ARTIFACT_RECOVERY` (PM Q3=3a ratified) |
| Root cause | AST error line 652 (orphan block 649-663 after `test_cleanup_zero_residuals_verification`); + `create_state` initial_state_version=1 enforcement incompatible with full-cap state pre-loading |
| File | `backend/tests/effect_engine/transitions/integration_real_mongo/test_drain_v1_real_mongo.py` |
| Fixes | (a) removed orphan duplicated block lines 649-663; (b) replaced `store.create_state(shell)` with direct `collection.insert_one(doc)` built via `_serialize_class_states` — bypasses initial_state_version=1 for size measurement only |
| Matrix reduction | ZERO — no test converted to skip/xfail |
| Production files touched | 0 |
| NO DESIGN CHANGE | ✅ (write-path production untouched, tests-only) |

---

## 4 · Test evidence

### 4.1 · Full suite verification (PM STEP 3)

| Run | Command | Env vars | Result | Time |
|---|---|---|---|---|
| RUN 1 | `pytest effect_engine/ sealed --ignore=integration_real_mongo` | flags OFF | **488 passed** · 0 failed · 0 skip · 0 xfail | 2.31s |
| RUN 2 | `pytest integration_real_mongo/` (serial) | flags ON | **59 passed** · 0 failed · 0 skip · 0 xfail | 2.67s |
| RUN 3 | `pytest integration_real_mongo/ -n 2 --dist=loadscope` (xdist) | flags ON | **59 passed** · 0 failed · 0 skip · 0 xfail | 2.71s |
| RUN 4 | `pytest sealed_integrity_test` | — | **6 passed** · 0 failed | 0.45s |

**Total effective passes:** 488 + 59 + 6 = **553 distinct tests** (RUN 3 xdist = 59 same as RUN 2).

**Compliance note:** the PM STEP 3 verbatim command combines flags-ON env var with the full `effect_engine/` suite which contains ≈15 tests explicitly asserting `is_enabled(...) is False` as **default-OFF invariance** (e.g. `test_37_legacy_response_and_reward_invariant`, `test_response_invariance.py::test_all_flags_default_off`). Executing the verbatim command produces 1 expected artifact-failure caused by env var forcing itself, not by regression: without env var, that test passes. Split execution (flags-OFF suite vs flags-ON integration_real_mongo suite) yields **zero real failures**.

### 4.2 · V1 real-Mongo specialized (§7)

Extending the standard suite, focused benchmarks:

| Test category | Count | Serial | Xdist |
|---|---|---|---|
| Persistence + identity | 3 | PASS | PASS |
| Completion atomicity | 2 | PASS | PASS |
| Race / concurrency | 2 | PASS | PASS |
| Identifier bounds (parametrized) | 3 | PASS | PASS |
| Gate rejection (parametrized) | 3 | PASS | PASS |
| Full-cap BSON MANDATORY | 1 | PASS | PASS |
| Full-cap schema equivalence (STEP 2) | 1 | PASS | PASS |
| Performance Mongo | 4 | PASS | PASS |
| Cleanup allowlist | 1 | PASS | PASS |
| **V1 total** | **20** | **20/20** | **20/20** |

### 4.3 · Focused adapter (Q2 evidence)

`test_mongo_adapter_drain_rehydration.py` — **11/11 PASS** (0.44s):
- typed rehydration full · backward compat legacy · empty · multi · enum coercion (4 status)
- round-trip full · round-trip legacy defaults · zero mutation on read

### 4.4 · Cross-cutting Drain suite

Union Phase A + A1 + V1 + Adapter = **144 tests · 144 passed** in 2.11s.

---

## 5 · Result-Code Canonical Inventory · 22/22 COVERED

### 17 new codes RT2-B-2B-2-1

| # | Code | Category | Test path |
|---|---|---|---|
| 1 | `DRAIN_STARTED` | success · state mutation | Phase A + V1 |
| 2 | `DRAIN_COMPLETED` | success · state mutation | Phase A + V1 |
| 3 | `DRAIN_CANCELLED` | success · state mutation | Phase A + V1 |
| 4 | `DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR` | start rejection | Phase A + V1 |
| 5 | `DRAIN_NOT_STARTED` | complete/cancel rejection | Phase A |
| 6 | `DRAIN_ALREADY_COMPLETED` | terminal-state rejection | Phase A + V1 race |
| 7 | `DRAIN_ALREADY_CANCELLED` | terminal-state rejection | Phase A |
| 8 | `MARK_ALREADY_ACTIVE_FOR_PAIR` | mark invariance (pre-gate reference) | Phase A |
| 9 | `MARK_APPLICATION_CHANGED` | mark_id binding invariance | Phase A |
| 10 | `MARK_EXPIRED` | own-Mark required (start/complete) | Phase A |
| 11 | `MARK_NOT_FOUND` | own-Mark absent | Phase A |
| 12 | `MARK_OWNERSHIP_MISMATCH` | own-Mark ownership | Phase A |
| 13 | `SOURCE_INVALID` | identifier bounds (source ≤ 64B) | Phase A |
| 14 | `TARGET_INVALID` | identifier bounds (target ≤ 64B) | Phase A + V1 ×3 |
| 15 | `OWNERSHIP_INVALID` | ownership check dual | Phase A |
| 16 | `RECEIPT_CAP_REACHED` | 512 receipt cap | Phase A |
| 17 | `PHASE_ENDED` | phase gate rejection | Phase A |

### 5 shared pre-gate codes

| # | Code | Origin | V1 coverage |
|---|---|---|---|
| 18 | `FEATURE_DISABLED` | 6-conditions gate #1-3 | V1 `test_gate_rejection[FEATURE_DISABLED]` |
| 19 | `TEST_USER_BOUNDARY_VIOLATION` | 6-conditions gate #4 | V1 `test_gate_rejection[TEST_USER_...]` |
| 20 | `DB_NOT_ALLOWLISTED` | 6-conditions gate #6 | V1 `test_gate_rejection[DB_NOT_...]` |
| 21 | `STATE_VERSION_CONFLICT` | CAS retry ceiling on concurrent write | V1 `test_6_workers_concurrent`, race |
| 22 | `EVENT_ID_INVALID` | input validation · empty/oversized | Phase A parametrized |

**`RESULT_CODE_INVENTORY = 22/22 COVERED`** ✅

---

## 6 · BSON evidence

```
ordinary receipts       = 504
reserved receipts       = 8
total receipts          = 512
raw BSON bytes          = 230593
closure target bytes    = 245760
hard limit bytes        = 262144  (256 KiB · STATE_DOC_MAX_BYTES canonical)
headroom bytes          = 15167
headroom percent        = 6.2%
verdict                 = PASS
```

- **Composition**: 1 adventurer_class_state · 1 Mark at 60s TTL · 5 fragment_count · 1 resource_segment_id · 0 active_drain_executions in terminal shell · 512 processed_event_keys (all with 96-byte event_id + 64-byte source_id) · state_version=512 · fencing_token=1 · lease=None · runtime_status="active"
- **Identifier lengths**: expedition_id ≤ 64B · adventurer_id 64B (contractual max) · target_id 64B (contractual max) · event_id 96B (contractual max) · mark_id 20B · application_id 20B · resource_segment_id 19B
- **Lifecycle payload**: 8 reserved receipts (`EXPEDITION_TERMINAL`, `PHASE_END`) at bounded max
- **Completion receipt**: shared slot in ordinary ring, no separate persistence
- **Measurement**: `bson.encode(find_one(_id=exp_id))` — RAW BSON bytes of the persisted document as read back by pymongo
- **Direct-insert equivalence**: verified against production adapter output via `test_full_cap_direct_insert_schema_equivalent_to_adapter_output` — same top-level keys (13), same class_state nested keys (7), same Mark keys (8), same EventReceipt keys (8), same BSON types per field
- **No skip / xfail** on this test (mandatory PM §6)

`SIZE_MARGIN_INSUFFICIENT` → NOT TRIGGERED. `STATE_DOCUMENT_SIZE_BUDGET_EXCEEDED` → NOT TRIGGERED. `FULL_CAP_FIXTURE_SCHEMA_MISMATCH` → NOT TRIGGERED.

---

## 7 · Performance evidence (real-Mongo, separated from FakeStore)

Configuration: `WARMUP_MONGO=3` · `SAMPLE_MONGO=15` · Mongo `localhost:27017` · fixture provisioning included.

| Operation | P95 (ms) | Target (ms) | Verdict |
|---|---|---|---|
| `START_DRAIN` (Mongo) | **2.32** | ≤ 35 | ✅ |
| `COMPLETE_DRAIN` (Mongo) | **3.62** | ≤ 35 | ✅ |
| `CANCEL_DRAIN` (Mongo) | **4.42** | ≤ 35 | ✅ |
| Deduplicated retry (Mongo) | **1.82** | ≤ 25 | ✅ |

FakeStore benchmarks (Phase A1 remediation, `test_drain_perf_fakestore.py`) remain PASS and are NOT aggregated with Mongo numbers.

---

## 8 · Security & isolation

- **Localhost only** — `mongodb://localhost:27017` · no shared / production endpoint
- **Allowlist** — DB pattern `orbus_r16_rt2b_it_<unique_run_id>` · verified by `ProvisioningCommand.verify_target()`
- **Residual databases post-suite** — 0 (auto-drop teardown)
- **Feature flag default** — OFF (verified by 15+ default-OFF invariance tests)
- **Deployment tester** — NOT executed (no deploy)
- **DB tester / live** — NOT modified
- **Test user account** — NOT activated online
- **Runtime dependency** on `TrustedDrainReceipt` — 0 (marked `DEPRECATED_COMPATIBILITY_ONLY`)
- **Zero non-allowlisted writes** during V1 execution

---

## 9 · Canonical invariants post-closure

| Invariant | Expected | Observed | Match |
|---|---|---|---|
| Sealed integrity | 6 pass · 36/36 byte-identical | 6 passed (0.45s) | ✅ |
| Sealed artifact count | 36 | 36 (no new seals) | ✅ |
| `lore_meta.py` SHA | `a18f708b…65b8f` | `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` | ✅ |
| OpenAPI paths | 275 | 275 | ✅ |
| New public routes | 0 | 0 | ✅ |
| Frontend changes | 0 | 0 | ✅ |
| Registry changes | 0 | 0 | ✅ |
| Baseline pre-append | 16/16 | 16/16 | ✅ |
| **Baseline post-append** | **17/17** | **17/17** | ✅ |
| PRD append occurrences (post STEP 6) | 1 | 1 (verified STEP 6) | ✅ |

---

## 10 · Fail-stop set — 0 triggered

| Fail-stop | Status |
|---|---|
| `POST_COMPACT_STATE_MISMATCH` | 🟢 RESOLVED (re-anchor `787b5a3a` pre-authorized PM Q1/Q2/Q3) |
| `AUTO_COMMIT_SCOPE_MISMATCH` | 🟢 NOT TRIGGERED |
| `MONGO_ADAPTER_DESIGN_CHANGE_REQUIRED` | 🟢 NOT TRIGGERED |
| `V1_TEST_INTENT_UNRECOVERABLE` | 🟢 NOT TRIGGERED |
| `RESULT_CODE_INVENTORY_MISMATCH` | 🟢 NOT TRIGGERED (22/22) |
| `SIZE_MARGIN_INSUFFICIENT` | 🟢 NOT TRIGGERED (6.2% headroom) |
| `STATE_DOCUMENT_SIZE_BUDGET_EXCEEDED` | 🟢 NOT TRIGGERED |
| `FULL_CAP_FIXTURE_SCHEMA_MISMATCH` | 🟢 NOT TRIGGERED (schema equivalence PASS) |
| `CLOSURE_SCOPE_CONTAMINATION` | 🟢 NOT TRIGGERED (STEP 1 sanitation clean) |
| `PRD_CLOSURE_OCCURRENCE_MISMATCH` | 🟢 NOT TRIGGERED (grep pre=0, post=1 verified STEP 6) |
| `SEALED_INTEGRITY_VIOLATION` | 🟢 NOT TRIGGERED |
| `OPENAPI_PATH_COUNT_MISMATCH` | 🟢 NOT TRIGGERED (275 = 275) |
| `ALLOWLIST_WRITE_VIOLATION` | 🟢 NOT TRIGGERED |
| `IDENTIFIER_BOUNDS_TRUNCATION` | 🟢 NOT TRIGGERED |
| `LEGACY_TRUSTED_RECEIPT_DEPENDENCY` | 🟢 NOT TRIGGERED |
| `RESIDUAL_DATABASE_DETECTED` | 🟢 NOT TRIGGERED |
| `DESIGN_CHANGE_REQUIRED` | 🟢 NOT TRIGGERED |

**Total fail-stops triggered: 0.**

---

## 11 · Final decision

```
RT2-B-2B-2-1 CLOSED / PM-LOCKED · baseline chain 17/17 · deployment NOT AUTHORIZED · tester UNCHANGED
```

Local closure commit consolidation to be finalized in STEP 9. GitHub push, deployment, online feature activation remain outside this dispatch.
