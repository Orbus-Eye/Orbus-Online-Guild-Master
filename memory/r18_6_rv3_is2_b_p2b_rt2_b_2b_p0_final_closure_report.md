# R18.6.RV3-IS2-B-P2B-RT2-B-2B-P0 · Class-State Transition Foundation · Final Closure Report

**Gate**: `R18.6.RV3-IS2-B-P2B-RT2-B-2B-P0`
**Canonical name**: CLASS-STATE TRANSITION FOUNDATION · READINESS & STATE-MACHINE CONTRACT
**Status**: **CLOSED · PM-LOCKED**
**Regime**: DOCUMENTAL ONLY · Italian · NO CODE · SHA §31 · MANIFEST_OWN_SHA_NOT_EMBEDDED
**PM adjudication authority**: PM Message 149
**Closure date (UTC)**: 2026-02

---

## 1 · Executive Summary

Gate `RT2-B-2B-P0` chiuso formalmente dopo adjudication PM (Message 149) delle 14 domande aperte `B2BQ01–B2BQ14`. I 2 fail-stop di lettura originalmente triggerati (`COMBAT_PHASE_BOUNDARY_UNDERDEFINED`, `CLASS_EVENT_ENTRYPOINT_UNDERDEFINED`) sono stati risolti tramite ratifica esplicita PM (Option B verbatim per entrambi). Zero code changes. Zero flag activation. Zero Mongo writes. Zero frontend touches. Baseline chain incrementata 13/13 → 14/14.

## 2 · B2BQ Adjudication Summary (14/14)

| ID | Topic | Chosen Option | PM Status |
|---|---|---|---|
| B2BQ01 | combat phase boundary source | **B** (expedition-as-single-phase) | PM_RATIFIED_WITH_CONDITIONS |
| B2BQ02 | class event internal entry point | **B** (extend ExpeditionRuntimeCoordinator) | PM_RATIFIED |
| B2BQ03 | Mark expiration model | **C** (hybrid) | PM_RATIFIED |
| B2BQ04 | Mark refresh timestamp policy | **A** (server-authoritative) | PM_RATIFIED |
| B2BQ05 | Drain cancellation policy | **A + mandatory reason code** | PM_RATIFIED_WITH_CONDITIONS |
| B2BQ06 | Drain completion output contract | **C** (result_code + assigned_event_sequence, NO gameplay payload) | PM_RATIFIED_WITH_CONDITIONS |
| B2BQ07 | Fragment gain source boundary | **A** (accepted Drain completion only) | PM_RATIFIED_WITH_CONDITIONS |
| B2BQ08 | Resource segment close conditions | **C + mandatory automatic closes** | PM_RATIFIED_WITH_CONDITIONS |
| B2BQ09 | Lease strategy per transition | **B** (short lease per server-authoritative event batch) | PM_RATIFIED_WITH_CONDITIONS |
| B2BQ10 | class-transition feature flag | **A** (`cdv_class_transitions_enabled` default OFF) | PM_RATIFIED |
| B2BQ11 | first transition code slice | **A** (Mark + Fragment + Resource Segment) | PM_RATIFIED_WITH_CONDITIONS |
| B2BQ12 | local integration-test strategy | **C** (FakeStore + MongoStore) | PM_RATIFIED |
| B2BQ13 | audit sampling | **A** (INFO+WARN+ERROR 100% locale) | PM_RATIFIED_WITH_CONDITIONS |
| B2BQ14 | state-document receipt bound | **fixed 512/504/8 · no eviction** | PM_RATIFIED_WITH_CONDITIONS |

- B2BQ adjudicated verbatim: **14/14**
- Agent auto-ratifications: **0**
- PM adjudication authority: `PM_MESSAGE_149`

## 3 · Fail-Stop Resolution (2/2)

| Fail-Stop ID | Original Status | Resolution | Adjudicated By |
|---|---|---|---|
| `COMBAT_PHASE_BOUNDARY_UNDERDEFINED` | TRIGGERED | RESOLVED · SINGLE_EXPEDITION_PHASE_V1 transitional model | B2BQ01 · Option B |
| `CLASS_EVENT_ENTRYPOINT_UNDERDEFINED` | TRIGGERED | RESOLVED · ExpeditionRuntimeCoordinator internal dispatch method | B2BQ02 · Option B |

Altri 4 fail-stop (`CLASS_STATE_ATOMICITY_CONFLICT`, `PUBLIC_API_SCOPE_EXPANSION_REQUIRED`, `SHARED_ENVIRONMENT_REQUIRED`, `ITEM_EFFECT_SCOPE_DEPENDENCY`): **NOT_TRIGGERED** (invariati).

## 4 · Ratified State-Machine Contract Summary

- **Phase model**: `SINGLE_EXPEDITION_PHASE_V1` · phase_id = `expedition:<expedition_id>:phase:1` · TRANSITORIO
- **Event entry point**: `ExpeditionRuntimeCoordinator.dispatch_class_state_event(event, trusted_context)` · server-side internal only
- **Mark expiration**: hybrid (lazy validation OBBLIGATORIA + opportunistic cleanup, NO scheduled)
- **Mark refresh**: server-authoritative timestamp · duration ≤ 10s · Mark scaduto → REFRESH rejected
- **Drain cancellation**: terminal + reason_code obbligatorio ∈ {8 codici}
- **Drain completion output**: audit-only (`drain_execution_id, status, result_code, mark_valid_at_completion, assigned_event_sequence, state_version_after, processed_at`) · NO gameplay payload
- **Fragment gain source**: accepted Drain completion only · in RT2-B-2B-1 testata via trusted fixture
- **Resource segment close**: phase_end + explicit_close + expedition_terminal + fragment_count→0 · focus_bonus_usage ≤ 2/segment
- **Lease/atomicity model**: short lease per event batch + CAS obbligatorio dentro il lease · retry max 3 · nessun background renewer
- **Class-transition feature flag**: nuovo `cdv_class_transitions_enabled` default OFF · gate composito quadruple (transient+class+test_user+localhost isolated + Mongo allowlisted)
- **Receipt policy**: total 512 / ordinary 504 / reserved 8 · no eviction · no overwrite · no duplicate removal · `RECEIPT_CAP_REACHED` fail closed su saturazione
- **Audit sampling**: localhost 100%/100%/100% (INFO/WARN/ERROR); prod policy = NEW PM ADJUDICATION richiesta
- **Test strategy**: FakeStore + real Mongo localhost (`orbus_r16_rt2b_test`, `orbus_r16_rt2b_it_<unique_run_id>`) · zero DB residui · parallel isolated

## 5 · First Code Slice Authorization

- **Gate**: `R18.6.RV3-IS2-B-P2B-RT2-B-2B-1 · MARK & RESOURCE STATE TRANSITION FOUNDATION`
- **Status**: **CONDITIONAL_GO · READY-TO-DISPATCH** (attende orchestrator explicit dispatch)
- **Scope ratificato**: Mark apply/refresh/lazy expiration/opportunistic cleanup/ownership+cap · Fragment gain primitive (trusted-fixture only) + spend + reset + overflow discard · resource segment open/close · event ordering · receipt generation · lease+fencing+CAS event batches · flag default-OFF · test-user fail-closed · FakeStore+MongoStore
- **Drain**: **DEFERRED to `RT2-B-2B-2 · DRAIN TRANSITION FOUNDATION`** · status HOLD
- **Public API changes**: **0** (invariante ratificata)
- **Human tester activation**: **NOT AUTHORIZED**
- **Shared environment**: **NOT AUTHORIZED**

## 6 · Governance Invariants (Preservate)

| Invariant | Value |
|---|---|
| lore_meta.py SHA | `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` (canonical, invariato) |
| Baseline chain length | **14/14** (post RT2-B-2B-P0 closure · byte-identical) |
| Sealed integrity tests passed | 6 |
| Sealed artifacts byte-identical | 36/36 |
| Effect-engine tests passed | 320/320 |
| OpenAPI paths total | 275 |
| New OpenAPI routes | 0 |
| Backend code changes | **0** |
| Frontend touches | **0** |
| Mongo writes | **0** |
| Feature flag activations | **0** |
| Registry changes | **0** |
| New seal | **NO** |
| PRD delta P0 | 1 (append idempotente sezione RT2-B-2B-P0) |
| Manifest own SHA embedded | **NO** (SHA §31 rispettato) |

## 7 · Hard-Lock Preservation (Verbatim)

- Active Marks ≤ **5** per source adventurer
- Marks per source-target pair ≤ **1**
- Mark duration ≤ **10 seconds**
- Sixth Mark application = **rejected** · automatic eviction = **false**
- Fragments ≤ **5** · overflow **discarded** (diagnostic only, NO reward/proc/conversion/credit)
- focus_bonus_usage ≤ **2** per resource segment
- Drain requires own active Mark = **true** · Drain consumes Mark = **false**
- One Drain resolution per `drain_execution_id`
- Allied Mark consumption/refresh/transfer = **forbidden**
- State document < **256 KiB** expected fixture load

## 8 · Deliverable Manifest (Records)

| # | Path | Role | Status |
|---|---|---|---|
| 1 | `/app/memory/r18_6_rv3_is2_b_p2b_rt2_b_2b_p0_class_state_transition_readiness.md` | Readiness draft (patched) | EXISTING_FILE_MODIFIED |
| 2 | `/app/memory/r18_6_rv3_is2_b_p2b_rt2_b_2b_p0_class_state_transition_readiness.json` | Readiness draft (patched) | EXISTING_FILE_MODIFIED |
| 3 | `/app/memory/r18_6_rv3_is2_b_p2b_rt2_b_2b_p0_final_closure_report.md` | Closure report (this file) | NEW_FILE |
| 4 | `/app/memory/r18_6_rv3_is2_b_p2b_rt2_b_2b_p0_final_closure_report.json` | Closure report structured | NEW_FILE |
| 5 | `/app/memory/r18_6_rv3_is2_b_p2b_rt2_b_2b_p0_closure_manifest.json` | Manifest §31 (own SHA NOT_EMBEDDED) | NEW_FILE |
| 6 | `/app/memory/PRD.md` | PRD post-append idempotente | EXISTING_FILE_MODIFIED |

SHA di tutti i record comunicati esclusivamente nel chat report finale (SHA §31).

## 9 · Explicit STOP

- Regime `DOCUMENTAL ONLY / READ-ONLY / NO APPLY / NO CODE` **rispettato integralmente**
- **NON** aprire `RT2-B-2B-1` code gate in questa closure (attende orchestrator dispatch)
- **NON** invocare `testing_agent` / `e1_tester`
- **NON** attivare feature flag, tester umano, shared environment
- Manifest's own SHA comunicato SOLO nel chat report finale

---

**RT2-B-2B-P0 · CLOSED · PM-LOCKED · STRICT STOP.**
