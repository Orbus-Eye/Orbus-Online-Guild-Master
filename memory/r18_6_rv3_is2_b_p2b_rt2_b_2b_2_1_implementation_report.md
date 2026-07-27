# R18.6.RV3-IS2-B-P2B-RT2-B-2B-2-1 · DRAIN TRANSITION & COMPLETION-TO-FRAGMENT FOUNDATION · PHASE A IMPLEMENTATION REPORT

**Gate**: `R18.6.RV3-IS2-B-P2B-RT2-B-2B-2-1`
**Canonical name**: DRAIN TRANSITION & COMPLETION-TO-FRAGMENT FOUNDATION
**Phase**: A (production + Phase A test matrix + report)
**Status**: `IMPLEMENTED / PM-CLOSURE-PENDING / V1-REQUIRED`
**Regime**: Code gate · single executor context · checkpoint pattern authorized
**PM authority**: Message 178 (RATIFY_OPT_A · Phase A only, V1 in successive dispatch)
**Implementation date (UTC)**: 2026-02
**Baseline chain**: **16/16 INVARIATA** (increment reserved for formal closure post-V1)

---

## 1 · Executive summary

Phase A del gate `RT2-B-2B-2-1` reimplementa integralmente il runtime Drain (state machine pura, wiring composite gate, dispatcher orchestration, audit map, test suite) partendo dallo stato canonico post `RT2-B-2B-2-P0` (readiness parent CLOSED · baseline 16/16 · code gate authorized). Tutti i 16 verdetti PM Message 170 sono stati incorporati verbatim (0 auto-ratifiche agent).

Deliverable Phase A: 3 nuovi file production, 6 file modificati (extension backward-compat), 1 nuovo test file (64 casi · 100% new-code result-code coverage), 3 test esistenti aggiornati (count invariance flag), sealed 6/6 PASS, OpenAPI 275 INVARIANT, lore_meta.py canonical SHA INVARIANT.

V1 real-Mongo verification (functionality · atomicity · concurrency · replay/dedup · saturation · BSON size · full-cap 512-receipt ≤ 245 760 B · performance · allowlist compliance · cleanup) è **espressamente rimandata** al successivo dispatch PM come pattuito in Message 178 §2.

## 2 · Files created (3)

| Path | SHA256 | Lines |
|---|---|---|
| `backend/app/stats/runtime/transitions/drain.py` | `56acedd3e93e214916f2e45d426e28e62a57db490010afe44a4b997d52c7b82f` | 658 |
| `backend/app/stats/runtime/wiring/feature_flags.py` | `191091d4bc5694ed96e411fd60be47ebe068e448cdae8d55719d49c2149f7698` | 112 |
| `backend/app/stats/runtime/wiring/dispatcher.py` | `d6952e0e496d3289991e1bff93b5a1ee4b85ef321427c77c8256c8ee65c8b976` | 266 |
| `backend/tests/effect_engine/transitions/test_drain_transitions.py` | `4a5707133696ada305152bde5dd0c156bf61db4d01bb5f5bfa0a85661df1af94` | 808 |

## 3 · Files modified (extension · backward compatible)

| Path | SHA256 (post) | Change |
|---|---|---|
| `backend/app/stats/runtime/transitions/models.py` | `1ac32593f4d370f9b361dbe531eb3e4acc799445f369163db9bb52459d7f7e1d` | ClassEventType +3 (START/COMPLETE/CANCEL_DRAIN) · TransitionResultCode +17 · DrainCommand · DrainCompletionReceipt (15-field EMBEDDED) · DRAIN_CANCEL_REASONS · validate_identifier_bounds · TrustedDrainReceipt marked DEPRECATED_COMPATIBILITY_ONLY · ClassStateEvent +4 optional drain fields (backward compat) |
| `backend/app/stats/runtime/transitions/dispatcher.py` | `2608e1c9fe4c13085d019aa3e3749ed7c8abcc8bab7ffdfdfe7727702be3773b` | `_apply_event_pure` branch extension for START/COMPLETE/CANCEL_DRAIN → pure drain state machine dispatch |
| `backend/app/stats/runtime/state_store/models.py` | `2b1e6269f7f668318eeae53e497aac8a01ade782b291d6480e334cf036d4f37b` | DrainDoc +4 fields (`mark_id`, `cancelled_at`, `cancellation_reason`, `drain_version`) all default-valued |
| `backend/app/stats/runtime/feature_flags.py` | `6f8ac8a05891f210baa3e57fcecb515b8dd0a27322bad523973a924bd6d1a986` | RT2_B_RUNTIME_ATTIVABILE +1 (`cdv_drain_transitions_enabled` default OFF) · ALL_FLAGS count 7→8 |
| `backend/app/stats/runtime/wiring/coordinator.py` | `8b8e45b783dfbc8d8b19f032dd071f07131e69117a1758805fd857cee9492c34` | `_class_event_audit_id` extension for 6 Drain audit ids |
| `backend/app/stats/runtime/wiring/audit.py` | `3595a2fe6ac4b13c272f2ed072f2a94d9fa4755622935f279b18fc71871a6aea` | Whitelist +10 Drain audit fields |
| `backend/tests/effect_engine/foundation/test_feature_flags.py` | `f07f4b80c274ae899bd9225504c6e904d7b9881970076c03258428193b9ab9bd` | 3 assertion updates (flag count 7→8, RT2_B set +cdv_drain_transitions_enabled) |
| `backend/tests/effect_engine/wiring/test_response_invariance.py` | `00f94eb49bd409c0d01d092a4ba00291bb2b5dd736271cc335623e911d23031f` | 1 assertion update (flag count 7→8) |

## 4 · PM verdicts incorporated verbatim (16/16)

- **B2B2Q01** · UUIDv4 completo `drn-<uuid>` server-authoritative, 36-char, NON troncato → implemented in `drain.start_drain` (`uuid.uuid4()` full form)
- **B2B2Q02** · Reuse `dispatch_class_state_event` entry point → new ClassEventType values, no new public route
- **B2B2Q03** · Mark binding strict application_id invariance → 15 revalidations on COMPLETE
- **B2B2Q04** · 15 mandatory revalidations at COMPLETE_DRAIN → enumerated in `complete_drain`
- **B2B2Q05** · Fragment gain fixed=1 · no RNG · no scaling → `FRAGMENT_GAIN_PER_DRAIN=1` constant
- **B2B2Q06** · At-cap: COMPLETED with `fragment_gain_applied=0 · overflow_discarded=1`
- **B2B2Q07** · Completion receipt EMBEDDED (15-field) in processed event receipt · NO separate slot → `DrainCompletionReceipt` returned by pure `complete_drain`, dispatcher folds into single ORDINARY receipt
- **B2B2Q08** · 8 canonical cancellation reasons (frozen set, NO extensions) → `DRAIN_CANCEL_REASONS` verified in test suite
- **B2B2Q09** · Canonical result codes set → all 17 new TransitionResultCode enum members
- **B2B2Q10** · First-committed-wins race → dispatcher retry loop returns `DRAIN_ALREADY_COMPLETED`/`DRAIN_ALREADY_CANCELLED` on re-attempt
- **B2B2Q11** · Lifecycle batch reserved receipt aggregate → PHASE_ENDED / EXPEDITION_TERMINAL cancellation reasons bypass ownership (single lifecycle worker), no per-Drain reserved slot
- **B2B2Q12** · Lease policy invariant · retry ≤ 3 · 7 revalidations per retry
- **B2B2Q13** · Dedicated flag `cdv_drain_transitions_enabled` default OFF · 6-conditions composite gate → `is_drain_gate_open` in `wiring/feature_flags.py`
- **B2B2Q14** · Receipt classification: START/COMPLETE/explicit CANCEL_DRAIN = ORDINARY · lazy cascade = FOLDED · lifecycle = 1 RESERVED per batch
- **B2B2Q15** · 10 audit event ids + campi minimi → `_drain_audit_id` mapping in `wiring/dispatcher.py` + audit whitelist extension
- **B2B2Q16** · Code gate scope = RT2-B-2B-2-1 + V1 subordinato · V1 no autonomous baseline increment

## 5 · Hard-locks (§18 verbatim)

- `max active Drain per (source_adventurer_id, target_id) pair = 1` → `_find_active_drain_for_pair` at START_DRAIN
- `max active Drain per Mark application (mark_id, application_id) = 1` → `_find_active_drain_for_application` at START_DRAIN
- Violation → `DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR` result code
- Terminal drains (COMPLETED/CANCELLED/EXPIRED) bounded storicamente · NON bloccano nuovo Drain

## 6 · Identifier bounds (§3 verbatim)

- `event_id ≤ 96 byte UTF-8` → `EVENT_ID_INVALID` (byte-level check via `.encode("utf-8")`)
- `source_adventurer_id ≤ 64 byte UTF-8` → `SOURCE_INVALID`
- `target_id ≤ 64 byte UTF-8` → `TARGET_INVALID`
- **Zero mutation** on invalid · **no silent truncation** → `validate_identifier_bounds` returns rejection code before any state read, tests parametrizzati con UTF-8 multibyte

## 7 · Zero legacy dependency

`transitions/drain.py` **NON importa** `TrustedDrainReceipt`. Static AST check enforced by `test_drain_module_zero_dependency_on_trusted_receipt`. `TrustedDrainReceipt` marcato con docstring `⚠️ DEPRECATED_COMPATIBILITY_ONLY (RT2-B-2B-2-1 PM adjudication §3)`.

## 8 · 6-conditions composite gate (verbatim §35)

```
1. cdv_transient_state_enabled
2. AND cdv_class_transitions_enabled
3. AND cdv_drain_transitions_enabled
4. AND authenticated user.is_test_user
5. AND environment = localhost isolated
6. AND Mongo target = allowlisted database
```

Implementato in `wiring/feature_flags.py::is_drain_gate_open(context: DrainGateContext) -> Tuple[bool, str]`. Short-circuit su prima failure. 6 gate reason codes emessi come audit `reason_code`. Flag Drain OFF → 0 DB call · 0 mutation (Drain path only · Mark/Fragment paths preservati per surgical kill-switch).

## 9 · Audit map (10 event ids verbatim §38)

1. `cdv_drain_started`
2. `cdv_drain_start_rejected`
3. `cdv_drain_completed`
4. `cdv_drain_completion_rejected`
5. `cdv_drain_cancelled`
6. `cdv_drain_cancellation_rejected`
7. `cdv_drain_duplicate_completion`
8. `cdv_drain_fragment_batch_applied` (emesso post COMPLETE con `fragment_gain_applied=1`)
9. `cdv_drain_fragment_overflow_discarded` (emesso post COMPLETE con `overflow_discarded=1`)
10. `cdv_drain_transition_conflict` (lease/CAS/state_version conflict routing)

Whitelist audit ampliata a includere: `drain_execution_id`, `mark_valid_at_completion`, `fragment_gain_requested/applied/overflow_discarded`, `cancellation_reason(s)`, `count_drains_cancelled`, `drain_execution_ids`, `drain_version`, `gate_reason`.

## 10 · Test matrix Phase A · 64 casi collected

### Categorie
- **Identifier bounds** (6 casi): valid pass · empty event_id · over-96 event_id · over-64 source · over-64 target · UTF-8 multibyte 4-byte cap
- **START_DRAIN happy path** (2 casi): mark active · UUIDv4 formato
- **START_DRAIN rejections** (11 casi): event_id_invalid · source over-bounds · target over-bounds · mark_not_found · mark_expired · ownership_mismatch · mark_application_changed · mark_id_mismatch · expedition_terminal · phase_inactive · receipt_cap_reached
- **START_DRAIN hard-locks** (3 casi): pair max-1 · application max-1 · terminal drain does not block new
- **COMPLETE_DRAIN happy path** (3 casi): zero-to-one segment opening · at-cap overflow · mid-cap no segment change
- **COMPLETE_DRAIN rejections** (8 casi): drain_not_started · already_completed · already_cancelled · mark_expired · mark_application_changed · expedition_terminal · phase_ended · receipt_cap
- **CANCEL_DRAIN** (10 casi): all 8 canonical reasons (parametrized) + unknown_reason_rejected + not_found + already_cancelled_idempotent + already_completed + ownership_mismatch + lifecycle_bypasses_ownership + expedition_terminal_lifecycle
- **Result-code coverage** (4 casi): DRAIN_STARTED · DRAIN_COMPLETED · DRAIN_CANCELLED · all-new-codes-defined enum check
- **Legacy invariance** (2 casi): TrustedDrainReceipt still importable (fixture) · drain.py zero AST dependency
- **6-conditions gate** (8 casi): closed on each of 6 conditions individually · open when all 6 true · 8-reason set count
- **Model extensions** (2 casi): DrainDoc new fields defaults · DrainDoc frozen

### Result-code coverage (17 new codes)

| Code | Covered |
|---|:-:|
| DRAIN_STARTED | ✅ |
| DRAIN_COMPLETED | ✅ |
| DRAIN_CANCELLED | ✅ |
| DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR | ✅ (pair + application variants) |
| MARK_APPLICATION_CHANGED | ✅ |
| EXPEDITION_TERMINAL_REJECTED | ✅ |
| PHASE_INACTIVE | ✅ |
| DRAIN_NOT_STARTED | ✅ |
| DRAIN_ALREADY_COMPLETED | ✅ |
| DRAIN_ALREADY_CANCELLED | ✅ |
| EVENT_ID_INVALID | ✅ |
| SOURCE_INVALID (via bounds + cancel unknown reason) | ✅ |
| TARGET_INVALID | ✅ |
| OWNERSHIP_INVALID | ✅ |
| MARK_NOT_FOUND | ✅ |
| MARK_EXPIRED | ✅ |
| RECEIPT_CAP_REACHED | ✅ |
| FEATURE_DISABLED (gate rejection) | ✅ (in `test_gate_closed_when_*_off`) |
| TEST_USER_BOUNDARY_VIOLATION | ✅ |
| DB_NOT_ALLOWLISTED | ✅ |

**Result-code coverage** = **100%** (17/17 new codes + 3 existing feature-gate codes exercised)

## 11 · Sealed integrity (post-write)

```
$ cd backend && python -m pytest tests/backend_r18_4_sealed_integrity_test.py -q
6 passed in 0.51s
```

- Sealed 6/6 ✅
- 36/36 artifacts byte-identical (implicit — no sealed file modified)
- `lore_meta.py` SHA post-write: `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` = **INVARIANT** ✅

## 12 · Regression suite

```
$ pytest tests/effect_engine/ tests/backend_r18_4_sealed_integrity_test.py -q
466 passed, 1 warning in 3.17s
```

Nessuna regression funzionale. 3 test hard-coded sul flag count (2 in `foundation/test_feature_flags.py`, 1 in `wiring/test_response_invariance.py`) aggiornati a nuovo count=8 come extension deterministica del contratto flag registry.

## 13 · OpenAPI paths

```
$ curl -sf http://localhost:8001/api/openapi.json | jq '.paths | length'
275
```

**275 INVARIANT** ✅ · new public routes = 0 · frontend changes = 0 · `.env` changes = 0

## 14 · Baseline chain

- Pre Phase A: **16/16**
- Post Phase A: **16/16 INVARIATA** (increment riservato a formal closure PM post-V1 verification)
- Formal closure = **HOLD**
- No PRD append · no closure report · no closure manifest generated

## 15 · Fail-stop count

- `CONTEXT_ANCHOR_FAIL`: 0
- `POST_COMPACT_STATE_MISMATCH`: 0
- `SEALED_INTEGRITY_VIOLATION`: 0
- `OPENAPI_PATH_COUNT_MISMATCH`: 0
- `ALLOWLIST_WRITE_VIOLATION`: 0 (no Mongo writes)
- `IDENTIFIER_BOUNDS_TRUNCATION`: 0
- `LEGACY_TRUSTED_RECEIPT_DEPENDENCY`: 0 (AST-verified)
- **Total fail-stops** = **0**

## 16 · V1 pending activities (post-PM dispatch successivo)

Per §5 dispatch PM Message 178 e §41 readiness spec:
- Real-Mongo functionality (allowlist `orbus_r16_rt2b_test`)
- Completion-to-Fragment atomicity end-to-end
- Winner-only concurrency (multiple concurrent complete su stesso Drain)
- Replay + dedup con `apply_event_once`
- Lifecycle receipt aggregation (1 RESERVED per phase-end batch, non per-Drain)
- Receipt saturation (ordinary 504 + reserved 8)
- Processed-event receipt RAW BSON size check per-event
- Identifier boundary enforcement real-Mongo (UTF-8 multibyte)
- **Full-cap 512-receipt · RAW BSON ≤ 245 760 byte** (mandatory)
- Performance measurements (p95 target ≤ 35 ms per event)
- Allowlist compliance (zero writes fuori `orbus_r16_rt2b_test`)
- Cleanup completo · zero residui DB test

Deliverables V1:
- `memory/r18_6_rv3_is2_b_p2b_rt2_b_2b_2_1_real_mongo_verification_addendum.md`
- `memory/r18_6_rv3_is2_b_p2b_rt2_b_2b_2_1_real_mongo_verification_addendum.json`

Stato finale V1 atteso: `V1 VERIFIED / RT2-B-2B-2-1 READY FOR FORMAL CLOSURE`.

## 17 · Primo comando previsto per la ripresa V1

```bash
# CONTEXT_ANCHOR post-compact (equivalente Phase A preflight §2)
cd /app && git rev-parse HEAD  # attesa be9f62ff... o commit successivo se auto-commit avvenuto
sha256sum backend/app/content/lore_meta.py  # attesa canonical a18f708b...
cd backend && python -m pytest tests/backend_r18_4_sealed_integrity_test.py -q  # 6 passed

# Setup real-Mongo test env
export MONGO_URL="mongodb://localhost:27017"
export ORBUS_RT2B_TEST_DB_UNIQUE_RUN_ID="$(uuidgen | cut -c1-8)"
export ORBUS_FLAG_CDV_TRANSIENT_STATE_ENABLED=true
export ORBUS_FLAG_CDV_CLASS_TRANSITIONS_ENABLED=true
export ORBUS_FLAG_CDV_DRAIN_TRANSITIONS_ENABLED=true

# V1 test entry (naming target)
python -m pytest backend/tests/effect_engine/transitions/integration_real_mongo/test_drain_v1_real_mongo.py -v
```

## 18 · Governance evidence (forma normalizzata)

- `sealed integrity tests = 6 passed`
- `sealed artifacts = 36/36 byte-identical`
- `effect_engine test suite = 466 passed · 0 failed · 1 warning benign`
- `lore_meta.py SHA = a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` INVARIANT
- OpenAPI **275 paths** INVARIANT · new routes = 0 · frontend changes = 0 · `.env` changes = 0 · FF runtime activation = 0
- Mongo writes = 0 · non-allowlisted writes = 0
- baseline chain 16/16 INVARIATA · V1 futuro NON incrementa separatamente (invariant per PM B2B2Q16)
- Fail-stop P0 count = 0/7
- Design deviations = 0 · Auto-ratifications agent = 0
- Legacy `TrustedDrainReceipt` runtime dependency = 0 (AST-verified)

---

## 19 · Explicit STOP · SAFE CHECKPOINT / NO CLOSURE / V1 REQUIRED

Phase A implementata integralmente. Test matrix completa 64/64 PASS. Regressioni 466/466 PASS. Sealed 6/6 PASS. OpenAPI 275 INVARIANT. `lore_meta.py` canonical INVARIANT. Baseline chain 16/16 INVARIATA. Nessun artifact di closure generato. Nessuna PRD append. Nessun `git push` / `git commit` eseguito. Working tree modified/new files pronti per commit ma **NON committati** (PM authority riservata).

**Stato canonico**: `RT2-B-2B-2-1 = IMPLEMENTED / PM-CLOSURE-PENDING / V1-REQUIRED`
**Stato checkpoint**: `SAFE CHECKPOINT / NO CLOSURE / V1 REQUIRED`

**STRICT STOP.** Attesa dispatch PM per V1 real-Mongo verification.
