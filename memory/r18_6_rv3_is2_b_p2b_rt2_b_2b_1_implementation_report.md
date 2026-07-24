# R18.6.RV3-IS2-B-P2B-RT2-B-2B-1 · Implementation Report

**Gate**: `R18.6.RV3-IS2-B-P2B-RT2-B-2B-1`
**Canonical name**: MARK & RESOURCE STATE TRANSITION FOUNDATION
**Status**: **IMPLEMENTED / PM-CLOSURE-PENDING**
**Regime**: CODE IMPLEMENTATION · localhost isolated · default-OFF · test-user fail-closed
**PM adjudication authority**: PM Message 151
**Implementation date (UTC)**: 2026-02

---

## 1 · Executive Summary

Implementata la primitive di transizioni class-state secondo i verdetti PM Message 151:
- **Mark** (apply/refresh/lazy expire/opportunistic cleanup/ownership+cap validation)
- **Fragment** (gain trusted-fixture-only/spend/reset/overflow discard)
- **Resource segment** (open/close automatico/close esplicito/focus bonus cap)
- **Event ordering + dedup** total-order per expedition
- **Lease per event batch + fencing + CAS** con retry max 3
- **Receipt policy** 512 total / 504 ordinary / 8 reserved (no eviction, no overwrite)
- **Feature flag** `cdv_class_transitions_enabled` default OFF (quadruple gate composito)
- **Audit** 11 event id + rejection routing (cdv_state_transition_conflict)
- **Boundary transitions/ ↔ wiring/** rispettato (no HTTP/env/Mongo/frontend deps in transitions/)
- **Public API changes = 0** · **frontend changes = 0** · **Mongo writes reali = 0** · **flag activation = 0**

Drain runtime = **NON IMPLEMENTATO** (deferred to `RT2-B-2B-2` per B2BQ11).

## 2 · File Changes

### Modified (6 file, in-scope PM §12)

| Path | SHA256 | Size | Lines | Diff |
|---|---|---|---|---|
| `backend/app/stats/runtime/feature_flags.py` | `ba27066a956d7e72ca31caca60411a87238930e50ec21e868f16d7549343d45d` | 6 344 | 162 | +7 / −1 (nuovo flag + count 7) |
| `backend/app/stats/runtime/state_store/models.py` | `f849fa87148c9b1e0b07ab5548b97d73f3c700eab4616786f454dc59452a183a` | 8 551 | 218 | +7 / −1 (MAX_PROCESSED_EVENTS 500→512) |
| `backend/app/stats/runtime/wiring/audit.py` | `7c344c49ba25b9489ce04a7f07505a11aa1362dd85fffccd760a551177b05469` | 4 075 | 137 | +18 / −2 (audit fields whitelist extension) |
| `backend/app/stats/runtime/wiring/coordinator.py` | `4ce05b28a480063090bf56e358b19b3e37924aaa0d3d385d7e3a94999b665164` | 16 796 | 406 | +169 (dispatch_class_state_event + audit event id mapping) |
| `backend/tests/effect_engine/foundation/test_feature_flags.py` | `dae77e3d6068a389c1a9d83e9200febd9edbfe71ef195c1df3c4c2b802e6327b` | 4 601 | 133 | +14 / −8 (expect count 7 + rt2b two-flag assertion) |
| `backend/tests/effect_engine/wiring/test_response_invariance.py` | `a530a7b602c08dd08369bfc829565699ef7ed7712222a9d1d7c9f9329ac1508c` | 2 513 | 64 | +3 / −3 (expect count 7) |

### New (11 file)

**Module `backend/app/stats/runtime/transitions/`** (5 file):

| Path | SHA256 | Size | Lines |
|---|---|---|---|
| `__init__.py` | `899aa33a06647d39fc0335f4946ac9ff405c13f16c2e1c2e46e4bc21229ff863` | 2 579 | 89 |
| `models.py` | `2150f08c02bd22f1d176d0a74a7cf1dcc7f1979a8b8ec6b4e8675a92f28c5aba` | 9 408 | 255 |
| `phase.py` | `357493b021e1c56dba21176de3f170e2615ed4883b0feadeea90d7db578d034b` | 3 022 | 92 |
| `state_machine.py` | `540173037c18491ca3b58a9e24e6b15e79b3ae7a05268a3af768aa53ac83afc5` | 26 192 | 720 |
| `dispatcher.py` | `3ffb62f550f635e0daf863a2726388dbc90a408dbcf43c6a0813a49314549afe` | 27 564 | 642 |

**Test suite `backend/tests/effect_engine/transitions/`** (6 file):

| Path | SHA256 | Size | Lines |
|---|---|---|---|
| `__init__.py` | `84c9c69410a38f8775c8c8d2564ed7153a577176a7a4e395d064fd66c7abef19` | 644 | 12 |
| `conftest.py` | `623cc693e6c298b92438cd7a2933cfb59eac83f43b388526d6d1054a0d614866` | 4 667 | 162 |
| `test_mark_transitions.py` | `26ba35b0845c65a23d7a4ef618fc881f0a336b794306c2320208f8fca73fda2b` | 7 265 | 147 |
| `test_fragment_transitions.py` | `564907c9bb086e1b9aa1eab53ddd129ddac90f55aba0b43b98205a2447c575f8` | 5 636 | 108 |
| `test_resource_segment.py` | `c821d903264174ce1f12276c4379a24280090f0702e51e2be72577c9727f981c` | 5 819 | 119 |
| `test_atomicity_gating_invariance.py` | `1007e52afde54586f07655f984989d31fad721c244e6018940b147a739301e1d` | 12 335 | 284 |

**Totale**: 6 modified + 11 new = 17 file di scope

## 3 · Test Matrix 37/37

| # | Item | File | Status |
|---|---|---|---|
| 1 | Mark apply success | test_mark_transitions.py | PASS |
| 2 | Mark duplicate source-target rejection | test_mark_transitions.py | PASS |
| 3 | Mark cap rejection (6th) | test_mark_transitions.py | PASS |
| 4 | Mark refresh success | test_mark_transitions.py | PASS |
| 5 | Expired Mark refresh rejection | test_mark_transitions.py | PASS |
| 6 | Lazy expiration | test_mark_transitions.py | PASS |
| 7 | Opportunistic cleanup | test_mark_transitions.py | PASS |
| 8 | Multi-CdV ownership isolation | test_mark_transitions.py | PASS |
| 9 | Fragment gain trusted receipt | test_fragment_transitions.py | PASS |
| 10 | Fragment gain w/o trusted receipt rejected | test_fragment_transitions.py | PASS |
| 11 | Fragment cap (≤5) | test_fragment_transitions.py | PASS |
| 12 | Fragment overflow discard | test_fragment_transitions.py | PASS |
| 13 | Fragment spend success | test_fragment_transitions.py | PASS |
| 14 | Fragment spend insufficient | test_fragment_transitions.py | PASS |
| 15 | Fragment negative/zero spend rejected | test_fragment_transitions.py | PASS |
| 16 | Phase reset (RESET_FRAGMENTS on phase end) | test_resource_segment.py | PASS |
| 17 | Expedition terminalization reset | test_resource_segment.py | PASS |
| 18 | Segment opens on first gain | test_resource_segment.py | PASS |
| 19 | Partial spend preserves segment | test_resource_segment.py | PASS |
| 20 | Zero balance closes segment | test_resource_segment.py | PASS |
| 21 | Explicit segment close (no refund) | test_resource_segment.py | PASS |
| 22 | Focus bonus cap ≤ 2/segment | test_resource_segment.py | PASS |
| 23 | Event ordering deterministic per expedition | test_atomicity_gating_invariance.py | PASS |
| 24 | Same-ID replay returns prior result | test_atomicity_gating_invariance.py | PASS |
| 25 | Same-ID payload mismatch rejection | test_atomicity_gating_invariance.py | PASS |
| 26 | Ordinary receipt cap 504 | test_atomicity_gating_invariance.py | PASS |
| 27 | Reserved lifecycle capacity 8 | test_atomicity_gating_invariance.py | PASS |
| 28 | Receipt no-eviction | test_atomicity_gating_invariance.py | PASS |
| 29 | State doc size < 256 KiB at cap | test_atomicity_gating_invariance.py | PASS |
| 30 | Lease acquisition success | test_atomicity_gating_invariance.py | PASS |
| 31 | Stale fencing rejection | test_atomicity_gating_invariance.py | PASS |
| 32 | CAS conflict returns conflict | test_atomicity_gating_invariance.py | PASS |
| 33 | Retry max 3 ceiling (static) | test_atomicity_gating_invariance.py | PASS |
| 34 | Feature flag OFF no-op | test_atomicity_gating_invariance.py | PASS |
| 35 | Non-test-user fail-closed | test_atomicity_gating_invariance.py | PASS |
| 36 | Mongo allowlist enforcement | test_atomicity_gating_invariance.py | PASS |
| 37 | Legacy response + reward invariant | test_atomicity_gating_invariance.py | PASS |

**Test tally**: 37 PASS · 0 SKIP · 0 FAIL · 0 XFAIL

Coverage deterministica:
- Authorized state transitions: 100% covered by ≥1 success test
- Rejection/result codes: 100% covered by ≥1 test
- Pre-existing fail-stops (13): statically verified as applicable/preserved

## 4 · Combined Test Suite

| Suite | Passed | Failed | Notes |
|---|---|---|---|
| `tests/effect_engine/transitions/` (new) | **37** | 0 | RT2-B-2B-1 |
| `tests/effect_engine/` (full) | **357** | 0 | 320 legacy + 37 new |
| `tests/backend_r18_4_sealed_integrity_test.py` | **6** | 0 | 36/36 byte-identical |
| **Total** | **363** | **0** | Zero regressions |

## 5 · Performance Acceptance (localhost isolated, FakeStore floor)

| Metric | Target p95 | Measured p95 | Status |
|---|---|---|---|
| Mark event batch | ≤ 35 ms | **0.07 ms** | ✅ PASS |
| Fragment event batch | ≤ 35 ms | **0.05 ms** | ✅ PASS |
| Resource-segment event batch | ≤ 35 ms | **0.04 ms** | ✅ PASS |
| Deduplicated retry | ≤ 25 ms | **0.02 ms** | ✅ PASS |
| Flags-OFF overhead | ≤ max(5%, 1 ms) | **0.004 ms** | ✅ PASS |

State document stress test:
- Receipt payload al cap 512: **160 959 byte (157.19 KiB)** < 256 KiB ✅
- Nessun `STATE_DOCUMENT_SIZE_BUDGET_EXCEEDED` triggerato

Note: le p95 sono sotto floor teorico su FakeStore (nessuna I/O Mongo reale). Metriche per real Mongo localhost saranno raccolte in gate successivo con env allowlisted `orbus_r16_rt2b_test`.

## 6 · Feature Gating

- Nuovo flag `cdv_class_transitions_enabled` in `RT2_B_RUNTIME_ATTIVABILE`
- Default OFF (verificato: `is_enabled('cdv_class_transitions_enabled') == False`)
- Gate composito ELEGGIBILITÀ (quadruple):
  1. `cdv_transient_state_enabled = true`
  2. `cdv_class_transitions_enabled = true`
  3. `authenticated user.is_test_user = true`
  4. `environment = localhost isolated + Mongo target allowlisted`
- Con flag OFF: 0 DB calls · 0 audit events · 0 state mutation (verificato test 34)
- Non-test-user: `TEST_USER_BOUNDARY_VIOLATION` fail-closed (verificato test 35)
- DB non allowlisted: `DB_NOT_ALLOWLISTED` fail-closed (verificato test 36)

## 7 · Boundary Compliance

| Boundary | Status |
|---|---|
| `transitions/` non importa `expeditions/` | ✅ (test 37) |
| `transitions/` non usa `os.environ` | ✅ (test 37) |
| `transitions/` non usa `fastapi` | ✅ (test 37) |
| `transitions/` non istanzia `AsyncIOMotorClient` | ✅ (test 37) |
| `wiring/coordinator.py` non duplica regole state-machine | ✅ (delegazione a dispatcher/state_machine) |
| Nessuna dipendenza circolare transitions↔wiring | ✅ (transitions non importa wiring) |
| Public API changes | 0 |
| OpenAPI schema changes | 0 |
| Frontend changes | 0 |
| Persistent user schema changes | 0 |
| Reward formula changes | 0 |
| Item Registry changes | 0 |
| Item generation | 0 |
| Mongo provisioning changes | 0 |
| `.env` mutation | 0 |
| Shared-environment configuration | 0 |

## 8 · Audit Events (11 canonici + conflict routing)

Mappa `event_type` → audit id in `wiring/coordinator.py::_class_event_audit_id()`:

- `cdv_mark_applied` · `cdv_mark_refreshed` · `cdv_mark_expired` · `cdv_mark_rejected`
- `cdv_fragment_gained` · `cdv_fragment_spent` · `cdv_fragment_reset` · `cdv_fragment_overflow_discarded`
- `cdv_resource_segment_opened` · `cdv_resource_segment_closed`
- `cdv_state_transition_conflict` (routing per: STATE_VERSION_CONFLICT, STALE_WRITER_REJECTED, EVENT_ID_PAYLOAD_MISMATCH, CAS_WITHOUT_VALID_LEASE, RETRY_CEILING_EXCEEDED, RECEIPT_CAP_REACHED, RESERVED_CAPACITY_EXHAUSTED, STATE_DOCUMENT_SIZE_BUDGET_EXCEEDED, EVENT_POST_TERMINAL_REJECTED)

Whitelist campi audit estesa (RT2-B-2B-1): +14 nuovi campi (event_id, event_type, event_sequence, reason_code, mark_id, mark_application_id, resource_segment_id, fragment_count_after, active_marks_count_after, focus_bonus_used_after, overflow_discarded, retry_attempts, dedup_reference, phase_id). Non registrati (PM §13): doc Mongo completo, full payload, credenziali, RNG seed, dati sensibili, reward payload.

## 9 · Fail-Stop Preservation

Tutti i 13 fail-stop attivi (PM §20) **preservati/monitorati**:

| # | Fail-Stop | Status |
|---|---|---|
| 1 | `PUBLIC_API_MODIFICATION_REQUIRED` | Non triggerato (public API invariata) |
| 2 | `FRONTEND_MODIFICATION_REQUIRED` | Non triggerato (frontend intatto) |
| 3 | `DRAIN_RUNTIME_TRANSITION_REQUIRED` | Non triggerato (Drain deferred RT2-B-2B-2, no runtime touches) |
| 4 | `CAS_WITHOUT_VALID_LEASE` | Enforced nel dispatcher (test 30 valida path acquire-lease) |
| 5 | `RECEIPT_EVICTION_REQUIRED` | Non triggerato (no eviction/no overwrite, test 28) |
| 6 | `STATE_DOCUMENT_SIZE_BUDGET_EXCEEDED` | Non triggerato (157 KiB al cap, test 29) |
| 7 | `TEST_USER_BOUNDARY_VIOLATION` | Enforced come gate (test 35) |
| 8 | `DB_SCOPE_VIOLATION` | Allowlist check (test 36) |
| 9 | `LEGACY_RESPONSE_OR_REWARD_DRIFT` | Non triggerato (public API invariata, test 37) |
| 10 | `ITEM_EFFECT_SCOPE_DEPENDENCY` | Non triggerato (nessuna item integration) |
| 11 | `RUNTIME_MODULE_BOUNDARY_VIOLATION` | Non triggerato (transitions/wiring boundary rispettato) |
| 12 | `TRANSITION_TEST_MATRIX_INCOMPLETE` | Non triggerato (37/37 PASS) |
| 13 | `CONTEXT_ANCHOR_FAIL` | Non triggerato (STEP 0 PASS) |

**Fail-stop count: 0/13**

## 10 · Governance Verification

| Item | Expected | Actual | Status |
|---|---|---|---|
| effect-engine baseline | 320 PASS | 320 PASS | ✅ |
| new transition tests | ALL PASS | 37/37 PASS | ✅ |
| combined suite (transitions + effect_engine + sealed) | ALL PASS | 363/363 PASS | ✅ |
| sealed integrity | 6 passed | 6 passed | ✅ |
| sealed artifacts | 36/36 byte-identical | 36/36 | ✅ |
| lore_meta.py invariant | `a18f708b…65b8f` | MATCH | ✅ |
| baseline chain durante code gate | 14/14 | 14/14 (invariato) | ✅ |
| OpenAPI paths | 275 | 275 | ✅ |
| new public routes | 0 | 0 | ✅ |
| frontend changes | 0 | 0 | ✅ |
| feature flag activation | 0 | 0 (nuovo flag creato default OFF) | ✅ |
| writes outside local allowlist | 0 | 0 | ✅ |
| residual integration DBs | 0 | 0 | ✅ |
| NEW SEAL | NO | NO | ✅ |
| RT2-B-2B-P0 closure manifest SHA | `4734761f…7fcdd0` | MATCH (invariante) | ✅ |

## 11 · Working Tree Scope

Modifiche attribuibili **ESCLUSIVAMENTE** a `RT2-B-2B-1`:

**Modified** (in-scope, 6 file):
```
backend/app/stats/runtime/feature_flags.py
backend/app/stats/runtime/state_store/models.py
backend/app/stats/runtime/wiring/audit.py
backend/app/stats/runtime/wiring/coordinator.py
backend/tests/effect_engine/foundation/test_feature_flags.py       (test expectation, PM §12 allowed)
backend/tests/effect_engine/wiring/test_response_invariance.py     (test expectation, PM §12 allowed)
```

**New** (in-scope, 11 file):
```
backend/app/stats/runtime/transitions/__init__.py
backend/app/stats/runtime/transitions/models.py
backend/app/stats/runtime/transitions/phase.py
backend/app/stats/runtime/transitions/state_machine.py
backend/app/stats/runtime/transitions/dispatcher.py
backend/tests/effect_engine/transitions/__init__.py
backend/tests/effect_engine/transitions/conftest.py
backend/tests/effect_engine/transitions/test_mark_transitions.py
backend/tests/effect_engine/transitions/test_fragment_transitions.py
backend/tests/effect_engine/transitions/test_resource_segment.py
backend/tests/effect_engine/transitions/test_atomicity_gating_invariance.py
```

**File non attribuibili al gate** (untracked pre-esistenti, non toccati da questa implementation):
- `_legacy_backup_before_restore/**` (backup pre-esistente)
- `_fresh_accidental_build_backup/**`, `_fresh_parcheggio_*` (backup pre-esistenti)
- `frontend/yarn.lock`, `mobile/yarn.lock` (yarn lockfiles pre-esistenti)
- `memory/r18_reset*.log`, `memory/round164_*.log` (log storici)

**Verificato**: nessun frontend file modificato · nessun `.env` toccato · nessuna route pubblica aggiunta.

## 12 · Regressions

**Zero regressions**. 
- 320 pre-existing effect_engine tests → 320 PASS (invariati)
- Sealed integrity 6/6 (36/36 byte-identical)
- OpenAPI 275 paths (invariata)
- lore_meta.py SHA invariante
- RT2-B-2B-P0 closure manifest SHA invariante

## 13 · Status Finale

- `RT2-B-2B-1` = **IMPLEMENTED / PM-CLOSURE-PENDING**
- `RT2-B-2B-P0` = CLOSED · PM-LOCKED (invariato)
- `RT2-B-2B-2 · DRAIN TRANSITION FOUNDATION` = HOLD · PLANNED (Drain deferred)
- Baseline chain length = **14/14** (INVARIATA durante code gate · incremento a 15 solo dopo formal closure PM successiva)
- NEW SEAL = **NO**
- Manifest generation = **NON EFFETTUATA** (closure artifact NOT in scope questo dispatch)
- PRD append = **NON EFFETTUATO** (closure NOT in scope questo dispatch)
- Testing agent / e1_tester / human tester = **NON INVOCATI**
- Shared environment activation = **NOT AUTHORIZED**
- Public API changes = **0** · Feature flag activation = **0**

## 14 · Explicit STOP

`RT2-B-2B-1` code gate **completato**. Attesa dispatch orchestrator successivo per:
- Formal closure (`RT2-B-2B-1` → CLOSED / PM-LOCKED)
- Baseline chain increment (14/14 → 15/15)
- PRD append idempotente
- Sealed integrity re-verify

**STRICT STOP.** Non aprire code gate `RT2-B-2B-2` (Drain). Non attivare tester umani. Non aggiungere alla baseline chain fino a ratifica PM.
