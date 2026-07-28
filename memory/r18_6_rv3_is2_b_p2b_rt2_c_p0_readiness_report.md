# R18.6 · RV3 · IS2-B · P2B · RT2-C-P0 · Generic Effect Engine · Readiness Report

> **Dispatch**: PM `R18.6.RV3-IS2-B-P2B-RT2-C-P0 · GENERIC EFFECT ENGINE — READINESS, ARCHITECTURE AND CONTRACT DISCOVERY`
> **Mode**: READ-ONLY DISCOVERY · no production writes · no PRD append · no baseline increment
> **Status**: `DISCOVERY COMPLETE / PM DECISIONS REQUIRED`

---

## 0 · Identity

| Field | Value |
|---|---|
| gate_id | `RT2-C-P0` |
| gate_title | Generic Effect Engine — Readiness, Architecture and Contract Discovery |
| timestamp_utc | `2026-07-28T05:35:00Z` |
| local_anchor | HEAD `f4c8c638cba7f59bbfe8e878fe46c311df743a96` (post-closure metadata-only lineage) |
| closure_commit | `c0d8150cf4aaab259ad0c7aefa5b0a86522ed340` |
| baseline | `17/17` (unchanged by this discovery) |
| context_anchor | `CONTEXT_ANCHOR_PASS` |

---

## 1 · Existing Architecture (evidence-based)

**Runtime layer** — `backend/app/stats/runtime/`

| Module | Lines | Role | Effect-adjacent? |
|---|---|---|---|
| `models.py` | 55 | `EffectiveStatResult` (stat pipeline output) | 🟡 stat-only, not runtime effects |
| `modifier_order.py` | 246 | Modifier ordering (stat pipeline) | 🟡 pipeline, not engine |
| `soft_caps.py` | 105 | Soft caps for stats | 🟡 pipeline |
| `stat_bridge.py` | 96 | Stat aggregator | 🟡 pipeline |
| `loadout_snapshot.py` | 118 | Loadout snapshot | 🟡 reserved |
| `equipment_aggregation.py` | 77 | Equipment aggregate | 🟡 pipeline |
| `events.py` | 143 | Event definitions | 🟢 relevant |
| `feature_flags.py` | 175 | 8 canonical flags | 🟢 relevant |

**State store** — `backend/app/stats/runtime/state_store/`

| Module | Lines | Role |
|---|---|---|
| `models.py` | 229 | `MarkDoc`, `DrainDoc`, `AdventurerClassState`, `EventReceipt`, `WriterLease`, `ExpeditionRuntimeState` |
| `interface.py` | 355 | Store abstraction |
| `mongo_adapter.py` | 697 | Motor async adapter (rehydration incl. DrainDoc) |
| `fake_store.py` | 695 | In-memory implementation |
| `fencing.py` | 79 | Fencing tokens |
| `errors.py` | 78 | Error hierarchy |
| `results.py` | 113 | `CasResultCode`, `TransitionResult` |
| `provisioning/*` | — | DB provisioning + allowlist verification |

**Transitions layer** — `backend/app/stats/runtime/transitions/`

| Module | Lines | Role |
|---|---|---|
| `models.py` | 403 | `TransitionResultCode` (44 codes total), transition request/result |
| `state_machine.py` | 795 | Mark/Fragment state machine |
| `drain.py` | 762 | RT2-B-2B-2-1 Drain state machine (pure) |
| `dispatcher.py` | 685 | Transition dispatcher (single writer) |
| `phase.py` | 90 | Phase gates |

**Wiring layer** — `backend/app/stats/runtime/wiring/`

| Module | Lines | Role |
|---|---|---|
| `coordinator.py` | 445 | Coordinator (6-conditions gate + orchestration) |
| `dispatcher.py` | 266 | Wiring dispatcher (audit + response invariance) |
| `audit.py` | 96 | Audit map (10 event IDs) |
| `feature_flags.py` | 131 | Flag gate helpers |
| `shadow_hooks.py` | 197 | Shadow comparison hooks |

**Existing state schema (ExpeditionRuntimeState top-level, 14 fields)**:
`expedition_id · state_version · created_at · updated_at · expires_at · runtime_status · owner_worker_or_lease_id · lease · loadout_snapshot_version · adventurer_class_states · processed_event_keys · last_event_sequence · fencing_token · MAX_PROCESSED_EVENTS=512`

**EventReceipt (8 fields)**: `event_id · event_type · source_adventurer_id · payload_hash · assigned_event_sequence · result_code · state_version_after · processed_at`

**AdventurerClassState (7 fields, incl. `fragment_count: int = 0  # cap ≤ 5`)**

---

## 2 · `effect_engine` existing? — **NAME_ONLY / NOT GENERIC**

**Search result** (`find backend/app -path "*effect_engine*"`) = **0 files**.

`backend/tests/effect_engine/` **exists** with **54 test files** across 4 sub-namespaces (`foundation`, `state_store`, `transitions`, `wiring`), but this is a **test-organization namespace only**, hosting tests for the Mark/Drain/state-machine runtime, not tests of a generic effect engine.

**Verdict**: `NAME_ONLY / NOT GENERIC`. The name `effect_engine` is aspirational/historical in the test directory tree. **No generic effect engine exists in production**. RT2-C must **create a new foundation**, not extend existing code.

**Adjacent artifacts**:
- `EffectiveStatResult` (runtime/models.py:30) — stat-pipeline result, not runtime effect
- `RT2_FUTURE_CONSTANTS` reserves 3 flags: `item_effect_engine_enabled`, `cdv_item_hooks_enabled`, `effect_observability_enabled` → **explicit forward-declaration**, RT2-C should adopt these names
- `outcome.result.fragment_count_after` already threaded through dispatcher→wiring→audit → contract slot exists for Fragment-based payoff outputs

---

## 3 · Component integration map

| Existing Component | Current Responsibility | RT2-C Integration Point | Required Modification | Risk | Sealed? |
|---|---|---|---|---|---|
| `state_store/models.py::ExpeditionRuntimeState` | root state doc | +field for `active_effect_instances`, `effect_history` (optional) | additive fields, defaults; NO removal | BSON growth vs 512-receipt cap | NO (RT2-B ratified) |
| `state_store/models.py::AdventurerClassState` | per-adventurer state | possibly +field for `active_effects` (per-target) | additive tuple; per-adventurer isolation | serialization symmetry (adapter needs rehydration pattern) | NO |
| `transitions/dispatcher.py` | single-writer dispatcher | +TransitionKind `APPLY_EFFECT/REMOVE_EFFECT/RESOLVE_EFFECT` | extend dispatcher table, mirror Drain patterns | positive-mutation code recognition (A1 pattern) | NO |
| `transitions/models.py::TransitionResultCode` | 44 codes | +N result codes for effect lifecycle | additive enum values | inventory canonicalization | NO |
| `mongo_adapter.py::_document_to_state` | rehydration | +typed rehydration for effect instances (mirror DrainDoc pattern) | +N lines symmetric block | schema equivalence to fixture | NO (V1-verified) |
| `wiring/coordinator.py` | 6-conditions gate | +sub-gate for effect engine (7th condition? or extend #2/#3) | wire new flag `generic_effect_engine_enabled` | flag topology decision (PM Q9) | NO |
| `wiring/audit.py` | 10 event IDs | +N audit event IDs for effect lifecycle | additive event set | audit map canonical count | NO |
| `wiring/feature_flags.py` | 8 flags | activate `item_effect_engine_enabled` + new `generic_effect_engine_enabled` | additive; default OFF | flag registry ratification | NO |
| `feature_flags.py::ALL_FLAGS` | 8-flag assertion | change to 9+ flags | update assert count | closed-set invariant | NO |
| `content/lore_meta.py` | sealed canonical | **NO CHANGE** | — | **SEALED_BREAK_REQUIRED risk if touched** | ✅ **SEALED** `a18f708b…65b8f` |
| Frontend (`I18nContext`, `contentMap`, etc.) | i18n + UI cards | +i18n keys for feedback events | additive keys; NO state mutation | feedback ordering / folding | NO |
| `expeditions/routes.py` | 1 route (`GET /{expedition_id}`) | possibly extend read model with effect summary | additive read field; NO write API | route count invariant (275) | NO |

---

## 4 · Proposed EffectDefinition contract

```python
@dataclass(frozen=True)
class EffectDefinition:
    effect_id: str                        # ≤ 64B UTF-8 (aligned with Mark/Drain identifiers)
    version: int                          # ≥ 1, monotonic per definition
    category: EffectCategory              # BUFF | DEBUFF | NEUTRAL | RESOURCE | FEEDBACK
    trigger: EffectTrigger                # ON_APPLY | ON_EVENT | ON_PHASE_END | ON_EXPEDITION_END
    target_scope: TargetScope             # SELF | SINGLE_TARGET | SQUAD | RESOURCE_SEGMENT
    duration_model: DurationModel         # INSTANT | UNTIL_PHASE | UNTIL_EXPEDITION | USES(n) | TIME(sec) | PERMANENT_UNTIL_REMOVED
    stacking: StackingPolicy              # NONE | REFRESH | REPLACE | ADDITIVE_CAP(n) | STRONGEST_WINS | SOURCE_ISOLATED | APPLICATION_ISOLATED
    magnitude_schema: MagnitudeSchema     # whitelisted keys+ranges (NO free-form)
    source_restrictions: Tuple[str, ...]  # allowed source class/item/trait tags
    tags: Tuple[str, ...]                 # ≤ 8 tags, each ≤ 32B UTF-8
    i18n_key: str                         # feedback lookup key (NOT localized string)
    feature_flag: str                     # required flag id
    audit_class: str                      # audit map slot
```

**Enforce**: no `eval`, no Python expressions in DB, no arbitrary field mutation. Definitions are **whitelisted** and **schema-validated**.

## 5 · Proposed EffectRequest contract

```python
@dataclass(frozen=True)
class EffectRequest:
    event_id: str                         # ≤ 96B (existing Mark/Drain contract)
    source_adventurer_id: str             # ≤ 64B
    target_id: str                        # ≤ 64B (may be self)
    effect_id: str                        # references EffectDefinition
    effect_version: int
    triggering_context: TriggerContext    # what caused this request (Drain/Mark/Item/Trait/Manual)
    idempotency_key: str                  # ≤ 96B (dedup on retry)
    timestamp: str                        # ISO UTC
    expected_state_version: Optional[int] # optional CAS hint
```

## 6 · Proposed EffectInstance contract

```python
@dataclass(frozen=True)
class EffectInstance:
    effect_instance_id: str               # server UUIDv4
    effect_id: str
    effect_version: int
    source_adventurer_id: str
    target_id: str
    triggering_application_id: str        # e.g. Mark.application_id or Drain.drain_execution_id
    started_at: str
    expires_at: Optional[str]             # depends on duration_model
    remaining_uses: Optional[int]
    stack_count: int                       # ≥ 1
    resolved_magnitude: Mapping[str, int]  # canonicalized from magnitude_schema
    lifecycle_status: EffectStatus         # ACTIVE | EXPIRED | CONSUMED | DISPELLED | INVALIDATED_SOURCE
    state_version_at_apply: int
```

## 7 · Proposed EffectResolution contract (dispatcher output)

```python
@dataclass(frozen=True)
class EffectResolution:
    request: EffectRequest
    accepted: bool
    result_code: TransitionResultCode
    created_instances: Tuple[EffectInstance, ...]
    updated_instances: Tuple[EffectInstance, ...]
    removed_instances: Tuple[str, ...]        # by instance_id
    resource_deltas: Mapping[str, int]        # (e.g. fragment_count delta)
    feedback_events: Tuple[FeedbackEvent, ...]
    audit_data: Mapping[str, str]
    receipt_payload: EventReceipt              # authoritative
```

---

## 8 · Effect Primitives — whitelist proposal

| Primitive | Description | Deterministic? | Phase A? |
|---|---|---|---|
| `stat_modifier_temporary` | modify stat by additive/multiplicative delta with cap | ✅ | ✅ |
| `cost_modifier` | modify a cost (currency, action point) | ✅ | 🟡 defer |
| `probability_intensity_modifier` | scale a probability/intensity by whitelisted factor | ✅ | 🟡 defer |
| `state_apply` / `state_remove` | apply/remove a status (whitelist) | ✅ | ✅ |
| `resource_generate` / `resource_consume` | +/− on whitelisted resource (Fragment, focus_bonus) | ✅ | ✅ |
| `duration_modifier` | modify duration of another instance | ✅ | 🟡 defer |
| `conditional_trigger` | if condition-met then trigger effect (bounded depth) | ✅ | 🟡 defer (chaining risk) |
| `on_event_completion` | trigger on event completion (Drain COMPLETE, Mark expire, etc.) | ✅ | ✅ |
| `on_phase_end` / `on_expedition_end` | trigger at phase/expedition boundary | ✅ | 🟡 defer |
| `feedback_only` | player-facing feedback without state mutation | ✅ | ✅ |

**NOT AUTHORIZED**: `eval`, scripting, plugin runtime, arbitrary field mutation, uncapped magnitude.

## 9 · Lifecycle · Stacking · Removal

### Duration options + recommendation
| Option | Use case | Recommended for CdV? |
|---|---|---|
| `INSTANT` | one-shot effect on apply | ✅ (fragment payoff) |
| `UNTIL_PHASE` | active during current phase | ✅ (temporary buff) |
| `UNTIL_EXPEDITION` | until expedition ends | 🟡 optional |
| `USES(n)` | consumed after N triggers | ✅ (Fragment-cost payoff) |
| `TIME(sec)` | wall-time expiry | ⚠️ requires TTL check, not preferred (state doc grows) |
| `PERMANENT_UNTIL_REMOVED` | persist across phases/expeditions | ❌ scope beyond RT2-C-Phase A |

### Stacking options + recommendation
| Policy | Semantic | Default? |
|---|---|---|
| `NONE` | new application rejected if existing | ✅ CdV default |
| `REFRESH` | extend duration | 🟡 opt-in per definition |
| `REPLACE` | swap with new magnitude | 🟡 opt-in |
| `ADDITIVE_CAP(n)` | stack up to N, each contributes | 🟡 opt-in |
| `STRONGEST_WINS` | keep highest magnitude | 🟡 opt-in |
| `SOURCE_ISOLATED` | stack allowed if different source | 🟡 opt-in |
| `APPLICATION_ISOLATED` | stack allowed per application_id | 🟡 opt-in |

### Removal triggers
`expiry (time/uses)` · `dispel (whitelisted)` · `consume` · `phase_end` · `expedition_end` · `source_invalidated` · `target_terminalized`

### Loop / recursion protection
- **Max trigger chaining depth = 3** (proposed cap)
- **Max effects per event = 8** (proposed cap)
- **No self-triggering** (definition-level guard)
- **Cycle detection**: track chain path per event, refuse if `effect_id` already in chain

## 10 · Determinism · Canonical Order

Proposed pipeline (per event):
```
validate_request
  → load_definition(effect_id, version) (fail-closed on missing/mismatch)
  → check_prerequisites (feature_gate, source_restrictions, state_pre)
  → resolve_target (target_scope enforcement)
  → resolve_stacking (against existing instances)
  → compute_mutation (magnitude, deltas, cap enforcement)
  → generate_feedback_events (ordered by definition priority)
  → commit_atomically (CAS on state_version)
  → persist_receipt_and_audit (single EventReceipt)
```

**Tie-break**: (definition_priority ASC, timestamp ASC, effect_instance_id ASC).
**Dedup**: (expedition_id, event_id) — existing receipt slot.
**Replay**: idempotent by (expedition_id, event_id, effect_id, effect_version, source, target, idempotency_key).
**Behavior on definition mismatch**: `EFFECT_DEFINITION_UNKNOWN` (result code) · 0 mutation.
**Version mismatch**: `EFFECT_VERSION_MISMATCH` · 0 mutation.

## 11 · Persistence · Atomicity options

| Option | Pros | Cons | Fit |
|---|---|---|---|
| **A) Embedded in state doc** (`active_effect_instances` tuple + `effect_history_receipts` shared with `processed_event_keys`) | atomic with existing CAS · zero new collection · zero cross-collection tx | BSON growth pressure (must stay ≤ 245,760) | ✅ **RECOMMENDED for Phase A** — align with Mark/Drain precedent |
| **B) Dedicated collection** (`effect_instances`) | unlimited scale · easier queries | cross-collection atomicity (transactions or 2-phase) · new backup surface · migration risk | ❌ NOT recommended (deviation from RT2-B precedent) |
| **C) Hybrid** (active in state doc, terminated in dedicated) | balance scale/atomicity | complexity, dual code path | 🟡 defer to post-Phase A |

**BSON impact estimate for Option A**:
- Current full-cap: 230,593 bytes (headroom 15,167 = 6.2%)
- Assume 10 active effect instances × ~500 bytes each = ~5,000 bytes
- Projected: 235,593 bytes (headroom 10,167 = 4.1%)
- **Remains ≤ 245,760 target · ≤ 262,144 hard limit** ✅
- If per-effect payload grows >~800 bytes, headroom shrinks below safe margin → per-effect cap required

**Do NOT modify** `MAX_PROCESSED_EVENTS = 512` (504+8). Any reduction = `DESIGN_CHANGE_REQUIRED`.

## 12 · Receipt · Audit · Feedback separation

- **Authoritative mutation receipt** = existing `EventReceipt` (dedup key `(expedition_id, event_id)`). Reused unchanged.
- **Audit event** = separate `audit_data` field in `EffectResolution`, wired through `wiring/audit.py` (extend map with N new event IDs, no schema change).
- **Player-facing feedback event** = new tuple entries in state doc (candidate) OR streamed via post-mutation notifier (out-of-band). Must NOT contain localized strings.

**FeedbackEvent proposed shape**:
```python
@dataclass(frozen=True)
class FeedbackEvent:
    event_id: str
    effect_instance_id: str
    kind: FeedbackKind          # APPLY | REFRESH | EXPIRE | CONSUME | STACK_UP | STACK_CAP | RESIST | OVERFLOW | INVALIDATE
    source_adventurer_id: str
    target_id: str
    reason_code: str            # canonical
    magnitude_key_values: Mapping[str, int]
    duration_seconds_or_uses: Optional[int]
    stack_count_after: int
    i18n_key: str               # KEY only, no localized text
    visibility: FeedbackVisibility  # PUBLIC | PARTY | PRIVATE
    ordering_hint: int          # int for stable ordering within event
    timestamp: str
```

**Feedback storage decision** (PM Q11): inline in state doc (max N per phase, folded in expedition report) OR emit-only via wiring hook (audit + client stream).

## 13 · First Consumer · CdV Fragment Payoff (proposals only)

Blocked constraints (verbatim): class=`cacciatore_del_vuoto` · main stat=`Intelligence` · priority `Intelligence→Cost→Dexterity` · fragment cap=5 · Mark duration=10s · active Marks=5 · combined proc=45% · focus_bonus ≤ 2 per resource_segment · dagger ritual-close ≤ 1 per Mark application.

### Payoff Option A — "Focus Burst" (INSTANT resource burst)
| Field | Value |
|---|---|
| Effect | Spend N Fragments (N ∈ [1,5]) to gain temporary Intelligence increase for current phase |
| Trigger | Player-driven (via new API endpoint) or automatic on Drain COMPLETE if threshold met |
| Cost | N Fragments (decrement `fragment_count`) |
| Target | Self (source adventurer) |
| Duration | UNTIL_PHASE |
| Stacking | NONE (only 1 active Focus Burst at a time) |
| Magnitude | Whitelist: +5×N Intelligence points (capped at soft_cap) |
| Feedback | APPLY event: "Focus Burst · +Xint · until phase end · N Fragments spent" |
| Risk | Bilanciamento: may over-emphasize Intelligence stat |
| Components touched | state (`fragment_count`, `active_effect_instances`), stat pipeline (Intelligence), feedback, audit, wiring |

### Payoff Option B — "Chain Mark" (USES-based Mark boost)
| Field | Value |
|---|---|
| Effect | Spend 3 Fragments to gain N=3 uses of "Enhanced Mark" (next 3 Marks have +duration/probability) |
| Trigger | Player-driven |
| Cost | 3 Fragments |
| Target | Self (applies to next Marks placed) |
| Duration | USES(3) |
| Stacking | REPLACE (new activation resets uses to 3) |
| Magnitude | Whitelist: +5s Mark duration OR +5% combined proc (mutually exclusive) |
| Feedback | APPLY · USES-decrement on each Mark trigger |
| Risk | Interacts with 10s duration and 45% combined proc — potential proc chain amplification |
| Components touched | Mark state machine, effect engine, feedback, audit |

### Payoff Option C — "Void Echo" (ON_EXPEDITION_END trigger)
| Field | Value |
|---|---|
| Effect | Accumulate Fragments; on expedition end, spend all N Fragments to gain bonus reward (XP invariant, only cosmetic/lore feedback) |
| Trigger | ON_EXPEDITION_END |
| Cost | ALL accumulated Fragments |
| Target | Self |
| Duration | INSTANT at expedition end |
| Stacking | NONE (evaluated once per expedition) |
| Magnitude | Cosmetic feedback + audit trail (**NO XP/loot/drop change**) |
| Feedback | Rich EXPIRE event with "Void Echo x N" for post-expedition report |
| Risk | Minimum bilanciamento (cosmetic) — safest for first payoff |
| Components touched | Effect engine, expedition end hook, audit, feedback, expedition report |

**PM decision required (Q7)**: pick Option A/B/C or combination. Option C is safest (cosmetic-only, zero XP/loot impact).

## 14 · Compatibility & Legacy invariance

| Concern | Handling |
|---|---|
| Legacy documents without effect state | `active_effect_instances` defaults to `()` on rehydration (adapter mirror of active_marks pattern) |
| In-progress expeditions | flag OFF → 0 mutation on effect path; existing Mark/Drain flow unaffected |
| Event replay | dedup via existing `EventReceipt` |
| Response invariance | test_response_invariance.py extended: with flag OFF, effect operations return canonical "feature disabled" WITHOUT mutating state |
| Reward invariance | Payoff Options A/B/C do NOT modify XP/loot/drop rate/equip/canonical probabilities |
| Legacy reports | Feedback events folded in expedition report as **additive** section; legacy reports unchanged |
| Non-test accounts | 6-conditions gate blocks activation for non-test users |
| Feature flag OFF | 0 DB writes on effect path |
| Rollback | Effect state additive; older code ignores `active_effect_instances` field on read |

**Fail-closed + backward-compatible**. No migration destrutting existing docs.

## 15 · Feature gating proposal

Adopt already-reserved `RT2_FUTURE_CONSTANTS`:
- `item_effect_engine_enabled` (from reserved set)
- `cdv_item_hooks_enabled` (from reserved set)
- `effect_observability_enabled` (from reserved set)

Plus **new**:
- `generic_effect_engine_enabled` (new global flag, default OFF)
- `cdv_fragment_payoff_enabled` (new sub-flag for CdV consumer)
- Possibly per-payoff sub-flag (e.g. `cdv_focus_burst_enabled`, `cdv_chain_mark_enabled`, `cdv_void_echo_enabled`)

**Gate minimum (7-condition variant)**:
1. `generic_effect_engine_enabled = true`
2. `cdv_class_transitions_enabled = true` (existing)
3. `cdv_drain_transitions_enabled = true` (existing)
4. Consumer-specific flag (e.g. `cdv_fragment_payoff_enabled`)
5. `user.is_test_user = true`
6. environment = localhost isolated
7. Mongo target = allowlisted database

**No online activation**. Default OFF everywhere.

## 16 · Canonical limits proposal

| Limit | Proposed value | Rationale |
|---|---|---|
| `effect_id` max bytes | 64 UTF-8 | mirror Mark/Drain identifier bound |
| `effect_instance_id` max bytes | 40 (UUIDv4 hex prefix + separator) | server-side gen |
| `source_adventurer_id` / `target_id` max bytes | 64 UTF-8 | existing invariant |
| `application_id` (triggering) max bytes | 32 UTF-8 | matches Mark contract |
| Tags per definition | ≤ 8 | prevent tag explosion |
| Tag length | ≤ 32B UTF-8 each | reasonable |
| Magnitude keys | ≤ 12 | schema-validated whitelist |
| Stack cap per definition | ≤ 5 (default 1) | prevent runaway |
| Active effect instances per target | ≤ 16 | BSON headroom |
| Active effect instances per expedition | ≤ 64 | total cap |
| Feedback entries per event | ≤ 8 | ordering deterministic |
| Trigger chain depth | ≤ 3 | anti-recursion |
| Effects processed per event | ≤ 8 | batch bound |
| Effect definition version | int ≥ 1 | monotonic |
| Receipt payload size (effect data) | +≤ 100 bytes/event | BSON budget preservation |

**No truncation. No silent normalization. Fail with `IDENTIFIER_BOUNDS_TRUNCATION` mirror.**

## 17 · Test strategy — future matrix (NO writes)

| Test category | Est. count Phase A | Est. count real-Mongo | Notes |
|---|---|---|---|
| Pure resolution (no store) | 15-20 | — | mirror `test_drain_transitions.py` shape |
| Stacking behaviors (per policy) | 8-12 | — | one per policy variant |
| Duration model (all 6 options) | 6-8 | — | expiry mechanics |
| Refresh / replace semantics | 6-8 | — | interaction with existing instance |
| Caps / overflow / soft caps | 6-8 | — | magnitude cap enforcement |
| Invalid definitions | 6-8 | — | missing / version mismatch |
| Replay / dedup | 4-6 | 2-3 | `event_id` reuse |
| Race / CAS conflict | 4-6 | 4-6 | winner-only |
| Lifecycle cleanup | 4-6 | 4-6 | ON_PHASE_END / ON_EXPEDITION_END |
| FakeStore benchmark | 4-6 | — | perf targets |
| Mocked Mongo | 4-6 | — | adapter shape |
| Real-Mongo persistence | — | 12-15 | mirror V1 matrix |
| Full-cap BSON | — | 1 | MANDATORY |
| Performance Mongo p95 | — | 4-6 | START/END/DISPEL/REFRESH |
| Feature gating (7-cond) | 6-8 | 2-3 | all combinations |
| Legacy invariance | 4-6 | — | rehydration from legacy |
| Feedback ordering | 3-5 | — | tie-break rules |
| i18n parameter safety | 2-3 | — | no localized strings in state |
| Property-based (if coherent) | 3-5 | — | opt-in |

**Estimated totals**: Phase A ≈ **95-125** tests · Real-Mongo ≈ **30-40** tests
**Context capacity required**: comparable to Phase A RT2-B (36 tests + A1 51 tests + V1 20 tests + adapter 11 tests = 118 tests over Phase A + V1). RT2-C likely +25-35% context, feasible in single Phase-A dispatch + separate V1.

## 18 · File plan (proposal, NO creation)

### Production
- `backend/app/stats/runtime/effects/__init__.py`
- `backend/app/stats/runtime/effects/models.py` (EffectDefinition, EffectRequest, EffectInstance, FeedbackEvent, enums)
- `backend/app/stats/runtime/effects/registry.py` (definition whitelist loader; static)
- `backend/app/stats/runtime/effects/engine.py` (pure resolution logic)
- `backend/app/stats/runtime/effects/dispatcher.py` (single-writer path integration)
- `backend/app/stats/runtime/effects/lifecycle.py` (expiry / phase_end / expedition_end handlers)
- Extend: `state_store/models.py` (+`active_effect_instances`, +`FeedbackEvent` if inline)
- Extend: `transitions/models.py` (+N result codes)
- Extend: `mongo_adapter.py` (+rehydration block for effect instances)
- Extend: `wiring/coordinator.py` (+effect dispatch path)
- Extend: `wiring/audit.py` (+N audit event IDs)
- Extend: `wiring/feature_flags.py` (+new flag helpers)
- Extend: `feature_flags.py` (add `generic_effect_engine_enabled` + cdv_fragment_payoff_enabled)

### Tests (mirror existing structure)
- `backend/tests/effect_engine/effects/test_engine_pure.py`
- `backend/tests/effect_engine/effects/test_stacking.py`
- `backend/tests/effect_engine/effects/test_duration.py`
- `backend/tests/effect_engine/effects/test_lifecycle_boundaries.py`
- `backend/tests/effect_engine/effects/test_engine_fakestore.py`
- `backend/tests/effect_engine/effects/test_engine_mocked_mongo.py`
- `backend/tests/effect_engine/effects/test_engine_perf_fakestore.py`
- `backend/tests/effect_engine/effects/integration_real_mongo/test_effects_v1_real_mongo.py`
- `backend/tests/effect_engine/effects/test_feedback_ordering.py`
- `backend/tests/effect_engine/effects/test_response_invariance_effects.py`

## 19 · Risk register

| Risk | Severity | Mitigation |
|---|---|---|
| BSON growth exceeds 245,760 target | HIGH | Per-effect payload cap ≤ 100 bytes · active_instances cap ≤ 16/target · reserved lifecycle slot preserved |
| Trigger chain infinite loop | HIGH | Chain depth ≤ 3 · effect_id cycle detection |
| Balance impact on CdV payoff | MEDIUM | Start with Option C (cosmetic-only) · defer XP/loot changes |
| Legacy doc migration destructive | MEDIUM | Additive fields with defaults · rehydration mirror pattern |
| Feature flag proliferation | LOW | Adopt already-reserved constants |
| Test volume overwhelming Phase A | MEDIUM | Split Phase A + V1 like RT2-B-2B-2-1 · use A1 remediation pattern if needed |
| Feedback event ordering nondeterministic | MEDIUM | Explicit ordering_hint + tie-break (definition_priority, timestamp) |
| Response invariance regression | HIGH | Extend test_response_invariance.py before implementation |
| i18n leakage into state doc | MEDIUM | i18n_key only, tested by `test_i18n_parameter_safety` |
| CAS pressure on effect apply/remove | LOW | Reuse existing single-writer dispatcher |

## 20 · Fail-stops attivi durante discovery (all NOT TRIGGERED)

- `LOCAL_POST_CLOSURE_STATE_MISMATCH` 🟢
- `SEALED_INTEGRITY_VIOLATION` 🟢
- `OPENAPI_PATH_COUNT_MISMATCH` 🟢
- `EXISTING_EFFECT_ENGINE_CONTRACT_CONFLICT` 🟢 (existing = NAME_ONLY, no conflict)
- `BSON_CAPACITY_REGRESSION_REQUIRED` 🟢 (proposal preserves 512 · fits headroom)
- `SEALED_BREAK_REQUIRED` 🟢 (`lore_meta.py` unchanged in proposal)
- `MIGRATION_DESTRUCTIVE_REQUIRED` 🟢 (additive-only proposal)
- `INSUFFICIENT_CONTEXT_FOR_COMPLETE_DISCOVERY` 🟢

## 21 · Recommended Next Gate

**`RT2-C-P1 · Generic Effect Engine · Phase A pure-resolution foundation`**

Scope suggerito:
- Definitions registry (static whitelist) + validation
- EffectDefinition/Request/Instance/Resolution models
- Pure engine: apply/remove/query (no store integration)
- Stacking + duration + magnitude cap semantics
- Feedback event ordering
- 95-125 pure tests + FakeStore adapter tests
- Flags: `generic_effect_engine_enabled`, `cdv_fragment_payoff_enabled` (both default OFF)
- **NO Mongo integration in P1** (deferred to P2)
- **NO CdV payoff implementation in P1** (contract only, consumer in P3)

Then RT2-C-P2 = mocked-Mongo + adapter symmetry; RT2-C-V1 = real-Mongo + full-cap; RT2-C-P3 = CdV first payoff (Option C recommended).

## 22 · PM Open Questions (§17 · max 12)

See `open_pm_questions` section in JSON companion for structured Q&A. Chat summary:

1. **Primitive whitelist scope** — which 3-5 primitives in Phase A? _Recommendation: `stat_modifier_temporary`, `state_apply`/`state_remove`, `resource_generate`/`resource_consume`, `on_event_completion`, `feedback_only`._
2. **Persistence model** — Embedded (A) / Collection (B) / Hybrid (C)? _Recommendation: A (Embedded), aligned with Mark/Drain precedent._
3. **Stacking default** — NONE by default? _Recommendation: yes, opt-in per definition._
4. **Duration model default** — INSTANT + UNTIL_PHASE + USES(n) in Phase A? _Recommendation: yes; defer TIME(sec) and PERMANENT._
5. **Trigger chaining** — allow with depth ≤ 3 or disable entirely in Phase A? _Recommendation: disable in Phase A (chain_depth=1 only)._
6. **Feedback model** — inline in state doc or out-of-band? _Recommendation: inline with cap (8/event) + expedition-report folding._
7. **First CdV payoff** — Option A/B/C or combination? _Recommendation: Option C first (cosmetic-only, safest)._
8. **BSON budget** — per-effect payload cap? _Recommendation: ≤ 100 bytes per instance record._
9. **Feature flag topology** — global-only or global+per-consumer? _Recommendation: global (`generic_effect_engine_enabled`) + per-consumer sub-flag._
10. **Result-code inventory scope** — 22 like RT2-B-2B-2-1 or more? _Recommendation: 18-25 new codes; canonicalize during Phase A._
11. **Response invariance strictness** — 0 mutation with flag OFF? _Recommendation: yes, hard-enforced (mirror RT2-B)._
12. **Test volume** — split Phase A + V1 like RT2-B-2B-2-1? _Recommendation: yes; A = 95-125 pure/FakeStore/mocked, V1 = 30-40 real-Mongo._

---

## 23 · Final verdict

```
RT2-C-P0 DISCOVERY COMPLETE / PM DECISIONS REQUIRED
```

- 0 production writes · 0 test writes · 0 PRD append · 0 baseline increment · 0 deploy
- Only 2 authorized artifacts created: this MD + companion JSON
- All fail-stops: NOT TRIGGERED
- Effect engine architecture is **NAME_ONLY / NOT GENERIC** in existing repo → RT2-C must **create new foundation**
- Reserved future flags (`item_effect_engine_enabled`, `cdv_item_hooks_enabled`, `effect_observability_enabled`) already staged for adoption
- Recommended next dispatch: `RT2-C-P1` (Phase A pure-resolution)

Awaiting PM decisions on the 12 open questions before authorization of RT2-C-P1.
