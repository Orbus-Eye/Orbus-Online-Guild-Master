# R18.6.RV3-IS2-B-P2B-RT2-B-2B-P0 · Class-State Transition Foundation · Readiness & State-Machine Contract

**Regime**: `DOCUMENTAL_ONLY · READ-ONLY DISCOVERY · Italian_only · NO APPLY · NO CODE · SHA §31 · STRICT STOP`
**Gate ID**: `R18.6.RV3-IS2-B-P2B-RT2-B-2B-P0`
**Anchor**: `lore_meta.py` SHA `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` · INVARIANT
**Upstream**: `RT2-B-2A CLOSED / PM-LOCKED` (manifest `da6eb1216bbc86f01941372ea2faa1ab6a39f408880427f8a53e6ea367747d89` · PRD `795d3b448c…22c5eb`)
**Status**: `DRAFT · READ-ONLY · PM_OPEN_QUESTIONS_EMITTED · NO AUTO-RATIFICATION · 2 FAIL-STOP TRIGGERED`
**Data**: 2026-02 (UTC)

---

## Sezione 1 · Executive Summary

Il gate `RT2-B-2B-P0` produce readiness plan per la state-machine deterministica di CdV class transitions (Mark · Drain · Fragment · Resource segment · Phase lifecycle · Terminalization) senza scrivere alcun codice. Discovery READ-ONLY ha rilevato **2 fail-stop TRIGGERED**: (a) `COMBAT_PHASE_BOUNDARY_UNDERDEFINED` — il runtime spedizione non possiede alcun concept di combat phase; (b) `CLASS_EVENT_ENTRYPOINT_UNDERDEFINED` — `apply_event_once` esiste come contract ma nessun servizio applicativo lo invoca. Entrambi richiedono adjudication PM prima di autorizzare code slice `RT2-B-2B-1`. 14 B2BQ estratte, **nessuna auto-ratificata**. Baseline governance intatta.

**Recommendation P0**: `RT2-B-2B-P0 READY FOR PM ADJUDICATION · RT2-B-2B-1 HOLD · fail-stop 2/6 TRIGGERED`.

---

## Sezione 2 · Scope

**In scope (documental only)**: state-machine deterministica per Mark/Drain/Fragment/Resource segment/Phase lifecycle/Terminalization; contract event schema, CAS, lease policy, dedup, ordering; failure isolation; audit boundary; test-user boundary invariance; API boundary invariance; 14 PM Open Questions non-auto-ratificate; 6 fail-stop valutati.

**Out of scope (P0 vietato)**: qualsiasi file `.py` applicativo · combat damage/healing · XP/loot rewards · guild XP · success-chance change · item procs/affix effects/cooldown engine · Legendary effects · boss dispel · anti-summon · PvP · frontend · public API changes · shared-env writes · FF activation · Mongo writes runtime.

---

## Sezione 3 · Governance

- Regime `DOCUMENTAL_ONLY · READ-ONLY DISCOVERY · Italian_only`.
- `lore_meta.py` invariant SHA `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`.
- Baseline chain **13/13 byte-identical** (INVARIATA in P0): `IS2-A · IS2-B-P1 · IS2-B-P1-N1 · IS2-B-P2A · IS2-B-P2B-1 · IS2-B-P2B-RT1 · IS2-B-P2B-RT2-P0 · IS2-B-P2B-RT2-A · IS2-B-P2B-RT2-B-P0 · IS2-B-P2B-RT2-B-1A · IS2-B-P2B-RT2-B-1B-P0 · IS2-B-P2B-RT2-B-1B-1 · IS2-B-P2B-RT2-B-2-P0`.
- Sealed integrity `6 passed · 36/36 byte-identical` (verificato in P0).
- Effect_engine tests `320/320 PASS` (invariante).
- OpenAPI `275 paths` invariante · new routes `0`.
- `NEW SEAL = NO`.
- SHA Policy §31: SHA dei 2 deliverable + eventuali closure artifact comunicati solo nel chat report finale; nessun self-SHA embedded.

---

## Sezione 4 · Source Chain

| # | Upstream artifact | Status | Rilevanza |
|---|---|---|---|
| 1 | `RT2-B-P0` State Store & Multi-Worker Architecture | PM-LOCKED | Contract origine 11 op |
| 2 | `RT2-B-1A` Store Contract & Non-Wired Adapter | PM-LOCKED | Library stand-alone |
| 3 | `RT2-B-1B-P0/1` Mongo Provisioning | PM-LOCKED | Real adapter validation |
| 4 | `RT2-B-2-P0` Local Runtime Wiring Readiness | PM-LOCKED | Wiring plan documentale |
| 5 | `RT2-B-2A` Shadow Wiring & Lifecycle Foundation | CLOSED / PM-LOCKED | Shell state, no transitions |
| 6 | `RT1` Runtime Stat & Effect Semantics | PM-LOCKED | Hard-lock caps (Marks/Fragments/Drain) |
| 7 | `RT2-A` CdV & Effect Engine | PM-LOCKED | Backbone effect engine non-wired |
| 8 | `app/stats/runtime/state_store/*` | READ-ONLY EVIDENCE | Contract 11 op, MarkDoc/DrainDoc/FragmentUsage |
| 9 | `app/stats/runtime/wiring/*` | READ-ONLY EVIDENCE | Shadow lifecycle attivo (post-2A) |
| 10 | `app/expeditions/services.py` | READ-ONLY EVIDENCE | Single-roll dispatch, no combat phase |
| 11 | Dispatch PM RT2-B-2B-P0 (Message 144) | RATIFYING DIRECTIVE | Origina questa readiness |

---

## Sezione 5 · Current Runtime Wiring

Post-`RT2-B-2A`:
- Hook T1 in `_dispatch_expedition:1095-1104` — shell state creation (audit-only, double-gate).
- Hook T2 in `_complete_one_expedition:712-731` — terminalization COMPLETED / COMPLETED_WITH_FAILURE.
- ExpeditionRuntimeCoordinator request-scoped (`wiring/coordinator.py`).
- MongoExpeditionRuntimeStateStore application-scoped, DB target allowlisted (`orbus_r16_rt2b_test` + pattern integrazione).
- Feature flag `cdv_transient_state_enabled` default OFF, `is_test_user` fail-closed server-authoritative.
- **Nessun class transition eseguito runtime** (verdict B2Q09 verbatim).

---

## Sezione 6 · Existing State-Store Contract

11 operazioni astratte (verbatim `RT2-B-1A`):
`create_state · get_state · compare_and_update · apply_event_once · reserve_writer · renew_writer_lease · release_writer · expire_state · delete_state · get_version · health_check`.

CAS semantics: mutation richiede `expedition_id + expected_state_version + fencing_token + event_id`; success → `state_version += 1`; mismatch → `STATE_VERSION_CONFLICT` / `STALE_WRITER_REJECTED`; nessuna mutation parziale.

Dedup: `apply_event_once` con guard `processed_event_keys.event_id != <event_id>` in CAS filter; duplicate → `SUCCESS` idempotent con `assigned_event_sequence` invariato o `EVENT_ID_PAYLOAD_MISMATCH` se payload differisce.

---

## Sezione 7 · Class-State Schema

`ExpeditionRuntimeState.adventurer_class_states: tuple[AdventurerClassState, ...]` con per ciascun avventuriero CdV:
- `adventurer_id`, `class_slug="cacciatore_del_vuoto"`, `class_state_version` monotonic.
- `active_marks: tuple[MarkDoc, ...]` cap ≤ 5 per source.
- `active_drain_executions: tuple[DrainDoc, ...]`.
- `fragment_count: int` cap ≤ 5.
- `focus_bonus_usage: tuple[FragmentUsage, ...]` cap ≤ 2 per resource segment.
- `resource_segment_id: str | None`.
- `processed_event_keys` (contract-level).

---

## Sezione 8 · Event Model

Event schema minimo (verbatim §Dispatch):
- `event_id` (client-provided UUID4).
- `event_type` (enum whitelist: `mark_apply · mark_refresh · drain_start · drain_complete · drain_cancel · fragment_gain · fragment_spend · fragment_reset · resource_segment_open · resource_segment_close · phase_start · phase_end · expedition_terminalize`).
- `expedition_id`.
- `source_adventurer_id`.
- `target_id?` (opzionale per event target-agnostic).
- `payload_version`.
- `payload_hash` (SHA256 subset whitelist).
- `requested_at` (ISO UTC).
- `expected_state_version` (CAS guard).

**Server-derived** (client NON controlla):
- `event_sequence` (monotonic per expedition, server-authoritative).
- `fencing_token` (validated contro lease attivo).
- `owner_worker_or_lease_id`.
- `processed_at`.
- `result_code`.

---

> **PM Decision (B2BQ02, Message 149)**: `B` · `PM_RATIFIED` · `extend ExpeditionRuntimeCoordinator`

## Sezione 9 · Mark State Machine

Stati: `INACTIVE → ACTIVE → EXPIRED | REMOVED_ON_TERMINAL`.
- `INACTIVE → ACTIVE`: transition `mark_apply` se cap ≤ 5 per source AND (source,target) non ha già ACTIVE Mark AND expedition non-terminal.
- `ACTIVE → ACTIVE`: transition `mark_refresh` (aggiornamento `expires_at`, mai duplicate).
- `ACTIVE → EXPIRED`: lazy on next state access (Model C hybrid PM baseline) OR explicit `mark_expired` event.
- `ACTIVE → REMOVED_ON_TERMINAL`: expedition raggiunge stato terminale → tutti i Marks vengono transizionati atomicamente.
- Errore: `MARK_CAP_EXCEEDED` (6° apply) · `MARK_DUPLICATE_ACTIVE` (stesso source-target attivo) · `MARK_OWNERSHIP_VIOLATION` (allied consumption/refresh/transfer).

---

## Sezione 10 · Mark Ownership

Identità minima (verbatim §Dispatch): `expedition_id + source_adventurer_id + target_id`.
Campi obbligatori `MarkDoc`: `mark_id · application_id · source_adventurer_id · target_id · created_at · updated_at · expires_at · ritual_close_used · mark_version · state`.

Ownership rules:
- Solo il `source_adventurer_id` può refresh/expire/reject il proprio Mark.
- Allied consumption/refresh/transfer = **forbidden** (audit `cdv_mark_rejected` con `reason=OWNERSHIP_VIOLATION`).
- Drain di adv A non consuma Mark di adv B (verdict RT1 hard-lock).

---

## Sezione 11 · Mark Caps

Hard-lock RT1 preservati verbatim:
- `active_marks_per_source ≤ 5`.
- `mark_per_source_target ≤ 1`.
- `duration_seconds ≤ 10`.
- `automatic_eviction = false` (sixth Mark → `REJECTED`, non evicta il più vecchio).
- `sixth_mark_application_result = MARK_CAP_EXCEEDED`.

---

## Sezione 12 · Mark Expiration

**3 modelli confrontati** (baseline PM raccomandata = Model C):

| Modello | Trigger | Latenza consistenza | Complessità | Conflitti | Retry | Fencing |
|---|---|---|---|---|---|---|
| A · lazy | Solo su next access dello state | Alta (fino al prossimo evento) | Bassa | Nessuno | Nessuno | Solo su next event |
| B · explicit scheduled | Timer server emette `mark_expired` event | Bassa (~ms) | Alta (scheduler) | Molti (event flood) | Complessi | Ogni event |
| C · hybrid lazy+cleanup | Lazy on access + optional cleanup pass | Media (bounded) | Media | Ridotti | Occasionali | Solo su cleanup |

**PM baseline = C**. Motivazione: bilanciamento consistenza/complessità; no scheduler server; cleanup pass opzionale per gc TTL.

**Adjudication PM richiesta**: B2BQ03.

---

> **PM Decision (B2BQ03, Message 149)**: `C` · `PM_RATIFIED` · `hybrid (lazy validation obbligatoria + opportunistic cleanup)`

## Sezione 13 · Mark Refresh

`mark_refresh` policy candidata:
- Precondizione: Mark ACTIVE, stesso `(source, target)`, `expires_at` > `requested_at`.
- Mutation: aggiorna `expires_at = requested_at + duration_seconds` (max 10s).
- `mark_version += 1`.
- Idempotenza: `event_id` duplicato → previous result.
- Refresh timestamp policy: server-authoritative (`requested_at` ignorato per timestamp, usato solo per validazione window).

**Adjudication PM richiesta**: B2BQ04.

---

> **PM Decision (B2BQ04, Message 149)**: `A` · `PM_RATIFIED` · `server-authoritative timestamp`

## Sezione 14 · Multi-CdV Interaction

Con 2+ CdV nello stesso team spedizione:
- Ogni source ha proprio bucket `active_marks` (per-source cap 5).
- (source A, target X) e (source B, target X) → 2 Marks distinti (uno per source).
- No cross-source consumption/refresh/transfer (verdict RT1).
- Fragment count per-adventurer (bucket separato).
- Focus bonus usage per-adventurer + per resource segment.
- **Nessuna sinergia gameplay in P0** (deferred).

---

## Sezione 15 · Drain State Machine

Stati: `INACTIVE → REQUESTED → ACTIVE → COMPLETED | CANCELLED | REJECTED`.
- `INACTIVE → REQUESTED`: `drain_start` se source ha almeno 1 own active Mark ON target.
- `REQUESTED → ACTIVE`: server-authoritative transition (immediate post-CAS).
- `ACTIVE → COMPLETED`: `drain_complete` se own Mark ACTIVE at completion (verdict RT1).
- `ACTIVE → CANCELLED`: `drain_cancel` esplicito (client OR expedition terminal).
- `INACTIVE → REJECTED`: `drain_start` senza own Mark → `DRAIN_MARK_MISSING_AT_START` reject.
- `ACTIVE → REJECTED`: `drain_complete` senza own Mark → `DRAIN_MARK_MISSING_AT_COMPLETION` reject.
- `one_resolution_per_execution_id = true` — duplicate `drain_execution_id` → previous result.

---

> **PM Decision (B2BQ05, Message 149)**: `A + mandatory reason code` · `PM_RATIFIED_WITH_CONDITIONS` · `CANCELLED terminal + reason_code obbligatorio`

> **PM Decision (B2BQ06, Message 149)**: `C` · `PM_RATIFIED_WITH_CONDITIONS` · `result_code + assigned_event_sequence (senza gameplay payload)`

## Sezione 16 · Drain Validation

Precondizioni `drain_start`:
- Own active Mark su `target_id` (source == source Mark).
- Expedition non-terminal.
- Nessun Drain ACTIVE con stesso `drain_execution_id`.

Precondizioni `drain_complete`:
- Drain ACTIVE con stesso `drain_execution_id`.
- Own active Mark presente at completion.
- Drain non ancora resolved (idempotent guard).

**Drain consumes Mark = false** (verdict RT1).

---

> **PM Decision (B2BQ05, Message 149)**: `A + mandatory reason code` · `PM_RATIFIED_WITH_CONDITIONS` · `CANCELLED terminal + reason_code obbligatorio`

## Sezione 17 · Drain Idempotency

Guarantees:
- `one_resolution_per_drain_execution_id`.
- Duplicate `drain_start` (stesso execution_id) → previous state, no mutation.
- Duplicate `drain_complete` (stesso execution_id) → previous result, no re-execution.
- Cancellation policy (B2BQ05): PM-adjudicate se `CANCELLED` è terminal ammette re-open (default: NO).

---

> **PM Decision (B2BQ05, Message 149)**: `A + mandatory reason code` · `PM_RATIFIED_WITH_CONDITIONS` · `CANCELLED terminal + reason_code obbligatorio`

## Sezione 18 · Fragment State Machine

Fragment counter per-adventurer:
- Stati: `count ∈ [0, 5]` (integer).
- Transitions: `fragment_gain` (`+1`), `fragment_spend` (`-1`), `fragment_reset` (`0`).
- Overflow: 6° gain → **discarded diagnostic-only** (verdict RT1: NO reward/proc/conversion/credit).
- Reset trigger candidati (B2BQ08): phase_end · expedition_terminal · resource_segment_close · explicit event.

---

> **PM Decision (B2BQ07, Message 149)**: `A` · `PM_RATIFIED_WITH_CONDITIONS` · `accepted Drain completion only`

## Sezione 19 · Fragment Gain

Precondizioni:
- Source (adv CdV) con `fragment_count < 5`.
- Fragment gain source boundary (B2BQ07): PM decide se solo Drain complete OR anche altri event source.
- Se `fragment_count == 5` at gain → transition `fragment_overflow_discarded` (audit only, no state change nel counter).

---

> **PM Decision (B2BQ07, Message 149)**: `A` · `PM_RATIFIED_WITH_CONDITIONS` · `accepted Drain completion only`

## Sezione 20 · Fragment Spend

Precondizioni:
- `fragment_count > 0`.
- Focus bonus usage per-segment ≤ 2 (hard-lock RT1).
- Spend authorized events (baseline candidato): `mark_apply_focused`, `drain_start_focused` (deferred to RT2-C effect engine).

Post-spend: `fragment_count -= 1`, `focus_bonus_usage` incrementato per segment corrente.

---

> **PM Decision (B2BQ08, Message 149)**: `C + mandatory automatic closes` · `PM_RATIFIED_WITH_CONDITIONS` · `phase_end + explicit close + expedition_terminal + fragment_count->0`

## Sezione 21 · Fragment Overflow

Verdict RT1 hard-lock: `overflow = discarded`. Audit event `cdv_fragment_overflow_discarded` emesso. **Nessun reward · nessun proc · nessuna conversione · nessun credito differito**. Solo diagnostica.

---

> **PM Decision (B2BQ08, Message 149)**: `C + mandatory automatic closes` · `PM_RATIFIED_WITH_CONDITIONS` · `phase_end + explicit close + expedition_terminal + fragment_count->0`

## Sezione 22 · Resource Segments

`resource_segment_id` per-adventurer nel class state.
- Transitions: `resource_segment_open` (start new segment, assigns new id) · `resource_segment_close` (terminal per segment).
- Close conditions candidati (B2BQ08): phase_end, expedition_terminal, explicit close event, fragment_reset trigger.
- Focus bonus usage cap ≤ 2 **per segment**: at close, `focus_bonus_usage` reset per-adventurer for next segment.
- Fragment reset policy: PM adjudica se close ↔ fragment_reset o transitions indipendenti.

---

> **PM Decision (B2BQ08, Message 149)**: `C + mandatory automatic closes` · `PM_RATIFIED_WITH_CONDITIONS` · `phase_end + explicit close + expedition_terminal + fragment_count->0`

## Sezione 23 · Phase Lifecycle

**Fail-Stop TRIGGERED**: `COMBAT_PHASE_BOUNDARY_UNDERDEFINED`.

Discovery evidence:
- `grep combat_phase|phase_id|phase_start|phase_end|CombatPhase` in `/app/backend/app` = **0 risultati**.
- Il runtime spedizione modella spedizioni come **single roll at completion** (`_complete_one_expedition:316-711`), senza infrastruttura phase/round.

**Options**:
- (A) Introdurre concept `combat_phase` server-side (RT2-B-2B code slice o gate dedicato).
- (B) Trattare l'expedition intera come singola phase (phase_start = dispatch, phase_end = terminalize).
- (C) Deferire class-state transition foundation fino a introduzione infrastruttura combat.

**Adjudication PM richiesta**: B2BQ01. **NON inventare phase boundary basato su singola request** (§Dispatch verbatim).

---

> **PM Decision (B2BQ01, Message 149)**: `B` · `PM_RATIFIED_WITH_CONDITIONS` · `expedition-as-single-phase`

## Sezione 24 · Expedition Terminalization

Transitions terminali (verdict B2Q04 upstream verbatim):
- `COMPLETED` (success=true post lazy sweep).
- `COMPLETED_WITH_FAILURE` (success=false post lazy sweep).
- `CANCELLED` (path esplicito, riservato futuro).

Post-terminal:
- Tutti i `active_marks` transizionati a `REMOVED_ON_TERMINAL`.
- `active_drain_executions` non-completed → `CANCELLED`.
- Resource segments aperti → `resource_segment_close` implicito.
- `fragment_count` non azzerato (audit-only), TTL cleanup 24h.
- Post-terminal events (class events) → **REJECTED** con `EXPEDITION_TERMINAL_LOCKED`.

---

> **PM Decision (B2BQ01, Message 149)**: `B` · `PM_RATIFIED_WITH_CONDITIONS` · `expedition-as-single-phase`

## Sezione 25 · CAS and Atomicity

CAS filter (verbatim §Dispatch + `mongo_adapter.py:272`):
- `{expedition_id, state_version: expected, fencing_token: expected, processed_event_keys.event_id != <event_id>}`.
- Mutation atomica: `state_version += 1`, `updated_at = now`, `processed_event_keys += (event_id, event_sequence)`.
- Mismatch → `STATE_VERSION_CONFLICT` or `STALE_WRITER_REJECTED`.
- Retry automatici max **3** con nuova `get_state` tra tentativi (server-side, non client).
- Nessuna mutation parziale (all-or-nothing).

**Fail-Stop candidato**: `CLASS_STATE_ATOMICITY_CONFLICT` se transition richiede mutation multi-document → **NOT TRIGGERED** in P0 (schema è single-document per-expedition).

---

> **PM Decision (B2BQ09, Message 149)**: `B` · `PM_RATIFIED_WITH_CONDITIONS` · `short lease per server-authoritative event batch`

## Sezione 26 · Lease Strategy

**3 modelli confrontati** (baseline PM raccomandata NON esplicita, adjudication B2BQ09):

| Modello | Semantica | Latenza | Conflitti | Complessità | Fencing | Retry |
|---|---|---|---|---|---|---|
| A · per transition | Lease acquisita all'inizio di ogni event, rilasciata post-CAS | Alta (2 write per event) | Bassa | Media | Ogni event | Complesso |
| B · per event batch | Lease acquisita per una serie di event (batch), rilasciata post-batch | Media | Media | Alta | Per batch | Medio |
| C · CAS-only for simple mutations | Nessuna lease; solo CAS su `state_version + fencing_token` | Bassa | Alta (retry stress) | Bassa | Solo CAS | Semplice |

Trade-off analizzati. Nessun nuovo ownership model contraddice `RT2-B-P0` (verdict verbatim §Dispatch).

**Adjudication PM richiesta**: B2BQ09.

---

> **PM Decision (B2BQ09, Message 149)**: `B` · `PM_RATIFIED_WITH_CONDITIONS` · `short lease per server-authoritative event batch`

## Sezione 27 · Event Ordering

Verdict verbatim §Dispatch: **state-changing class events = total ordered per expedition**.
- `event_sequence` server-authoritative monotonic.
- Terminal transition wins over later class events → post-terminal → REJECTED.
- Cross-expedition ordering NON garantito (per-expedition scope).
- Concurrent event su stesso expedition risolto via CAS + fencing_token; loser retry con nuova sequence.

---

> **PM Decision (B2BQ09, Message 149)**: `B` · `PM_RATIFIED_WITH_CONDITIONS` · `short lease per server-authoritative event batch`

## Sezione 28 · Deduplication

Verdict verbatim §Dispatch:
- Stesso `event_id + payload_hash` → **previous result**, no mutation, no side-effect.
- Stesso `event_id + payload_hash diverso` → `EVENT_ID_PAYLOAD_MISMATCH` REJECT.
- `processed_event_keys` mantiene `(event_id, event_sequence)` per rehydrate.
- TTL: `processed_event_keys` bound (B2BQ14 · state-document receipt bound).

---

> **PM Decision (B2BQ14, Message 149)**: `fixed bounded receipt set, NO rolling eviction` · `PM_RATIFIED_WITH_CONDITIONS` · `hard cap 512 total / 504 ordinary / 8 reserved · no eviction · no overwrite`

## Sezione 29 · Feature Flags

Preservazione verbatim §Dispatch:
- `cdv_transient_state_enabled` default OFF (invariato post RT2-B-2A).
- **Nuovo flag proposto** (baseline PM raccomandata = SÌ): `cdv_class_transitions_enabled` default OFF, hard-forced False in production. Attivazione: entrambi ON + `is_test_user=true` + localhost isolated env.
- Nessuna attivazione runtime in P0.

**Adjudication PM richiesta**: B2BQ10.

---

> **PM Decision (B2BQ10, Message 149)**: `A` · `PM_RATIFIED` · `nuovo flag cdv_class_transitions_enabled default OFF`

## Sezione 30 · Test-User Boundary

Invarianza post RT2-B-2A:
- `users.is_test_user` server-authoritative (email suffix `@orbus.test` + admin CAS toggle).
- Fail-closed su: missing user, missing field, value != true, DB error.
- Nessuna espansione del boundary in RT2-B-2B code slice: identico contratto B2Q06.
- Class transitions eseguiti solo se boundary passa (double-gate `cdv_transient_state_enabled` + `is_test_user`; con nuovo flag `cdv_class_transitions_enabled` → triple-gate).

---

> **PM Decision (B2BQ10, Message 149)**: `A` · `PM_RATIFIED` · `nuovo flag cdv_class_transitions_enabled default OFF`

## Sezione 31 · API Boundary

Verdict verbatim §Dispatch: `public API changes = none` in P0 e in RT2-B-2B-1 code slice.
- Nessun endpoint Mark/Drain/Fragment.
- Nessun campo response nuovo.
- Nessun websocket.
- Nessun frontend command.
- Primo code gate userà **eventi interni + fixture integrazione test**.

**Fail-Stop TRIGGERED**: `CLASS_EVENT_ENTRYPOINT_UNDERDEFINED`. Il runtime attuale NON offre event entry point interno (grep `process_class_event · class_event · event_bus · EventBus` = 0 risultati outside `state_store` namespace).

**Adjudication PM richiesta**: B2BQ02 (class event internal entry point).

---

> **PM Decision (B2BQ02, Message 149)**: `B` · `PM_RATIFIED` · `extend ExpeditionRuntimeCoordinator`

## Sezione 32 · Audit and Observability

**16 audit events minimi** (verbatim §Dispatch):
1. `cdv_mark_apply_evaluated`
2. `cdv_mark_applied`
3. `cdv_mark_refreshed`
4. `cdv_mark_expired`
5. `cdv_mark_rejected`
6. `cdv_drain_started`
7. `cdv_drain_completed`
8. `cdv_drain_cancelled`
9. `cdv_drain_rejected`
10. `cdv_fragment_gained`
11. `cdv_fragment_spent`
12. `cdv_fragment_overflow_discarded`
13. `cdv_fragment_reset`
14. `cdv_resource_segment_opened`
15. `cdv_resource_segment_closed`
16. `cdv_state_transition_conflict`

Sampling policy candidata (B2BQ13): INFO 100% · WARN 100%. Nessun payload sensibile, Mongo dump, seed, rewards.

---

> **PM Decision (B2BQ13, Message 149)**: `A` · `PM_RATIFIED_WITH_CONDITIONS` · `INFO 100% + WARN 100% + ERROR 100% (all-log locale)`

## Sezione 33 · Failure Isolation

Invarianza post B2Q08:
- Transition failure → previous state preserved · no partial mutation · audit warn.
- Store infra error → `STORE_INFRA_ERROR` result_code, no reward linked, no downstream side-effect.
- Lease/CAS conflict → retry max 3, poi return `STATE_VERSION_CONFLICT` → audit `cdv_state_transition_conflict`.
- **FORBIDDEN**: duplicate reward · partial new-runtime reward · silent granting fallback.

---

## Sezione 34 · Compatibility

- Con `cdv_class_transitions_enabled` OFF → behavior identico al post-RT2-B-2A (shell state only, no transitions).
- Con `cdv_class_transitions_enabled` ON + FF/test-user gates OFF → identico OFF (triple-gate).
- Con tutti i gate ON + localhost allowlisted → class transitions eseguiti su test-user only.
- Legacy path `_complete_one_expedition` autoritativo invariato.

---

## Sezione 35 · Security and Abuse

Threat surface class transitions:
- Client-forged event_id/payload → `EVENT_ID_PAYLOAD_MISMATCH` reject + rate-limit audit.
- Client-forged fencing_token/event_sequence → server-derived, client input ignored.
- Cross-expedition state poisoning → ownership check + CAS su expedition_id.
- Post-terminal event replay → REJECTED (terminal wins).
- Allied Mark consumption/refresh/transfer → `MARK_OWNERSHIP_VIOLATION` REJECT.
- Fragment overflow abuse → discarded diagnostic (no reward path).
- Cross-env leak → B2Q10 allowlist locale only.

---

## Sezione 36 · Test Architecture

**Test proposti** (NON scritti in P0):
- Unit: state-machine transitions per Mark/Drain/Fragment/Resource/Phase/Terminalization.
- Integration: `apply_event_once` end-to-end con FakeStore + MongoStore isolated.
- CAS conflict / retry / fencing → forzare `STATE_VERSION_CONFLICT` e verificare retry ≤ 3.
- Dedup: duplicate event_id + payload_hash → previous result; mismatch → reject.
- Ordering: concurrent event → linearizzabilità per-expedition.
- Anti-P2W: no reward/proc/conversion su class transitions.
- Regression: 320 baseline tests invariati.
- Local integration-test strategy (B2BQ12): TBD PM.

---

> **PM Decision (B2BQ12, Message 149)**: `C` · `PM_RATIFIED` · `both FakeStore + MongoStore isolated`

## Sezione 37 · Performance Risks

- `apply_event_once` p95 stimato ≤ 25ms (baseline `create_state = 0.21ms` misurato). Overhead trascurabile per shadow.
- State document size cap **256 KiB expected fixture load**. Con `processed_event_keys` unbound → risk growth.
- Adjudication B2BQ14: state-document receipt bound (TTL o cap ricevute).
- Concurrent event stress → CAS conflict retry può degradare p95; monitoring via `cdv_state_transition_conflict`.

---

> **PM Decision (B2BQ14, Message 149)**: `fixed bounded receipt set, NO rolling eviction` · `PM_RATIFIED_WITH_CONDITIONS` · `hard cap 512 total / 504 ordinary / 8 reserved · no eviction · no overwrite`

## Sezione 38 · Risk Register

| ID | Rischio | Severity | Mitigazione |
|---|---|---|---|
| R01 | Combat phase inesistente | HIGH | Fail-stop TRIGGERED · B2BQ01 adjudication |
| R02 | Class event entry point mancante | HIGH | Fail-stop TRIGGERED · B2BQ02 adjudication |
| R03 | Mark refresh timestamp race | MEDIUM | Server-authoritative timestamp (B2BQ04) |
| R04 | Drain cancellation race | MEDIUM | one_resolution_per_execution_id (B2BQ05) |
| R05 | Fragment overflow abuse | LOW | discarded diagnostic (RT1 hard-lock) |
| R06 | Focus bonus > 2 per segment | MEDIUM | Cap CAS check + resource_segment_close reset |
| R07 | State doc size overflow | MEDIUM | Receipt bound (B2BQ14) + TTL cleanup |
| R08 | Post-terminal event replay | LOW | REJECTED terminal-wins |
| R09 | Cross-expedition state poisoning | RESOLVED | CAS su expedition_id + ownership |
| R10 | Allied Mark manipulation | RESOLVED | MARK_OWNERSHIP_VIOLATION reject |
| R11 | Retry storm on conflict | MEDIUM | Cap retry 3 + audit `cdv_state_transition_conflict` |
| R12 | Lease deadlock (Model A/B) | MEDIUM | TBD B2BQ09 |
| R13 | Public API scope creep | LOW | verdict `public API = none` verbatim |
| R14 | Item effect scope dependency | RESOLVED | Item hooks HOLD (RT2-E), zero dependency |

---

## Sezione 39 · PM Open Questions (B2BQ01-14 · NO AUTO-RATIFICATION)

Ogni domanda: `question_id · evidence · options · agent_recommendation · affected_modules · gameplay_impact · state_impact · security_impact · test_impact · blocking`. Dettaglio verbatim nel JSON companion `section_39_pm_open_questions`. Sintesi:

- **B2BQ01** · Combat phase boundary source (FAIL-STOP `COMBAT_PHASE_BOUNDARY_UNDERDEFINED` TRIGGERED).
- **B2BQ02** · Class event internal entry point (FAIL-STOP `CLASS_EVENT_ENTRYPOINT_UNDERDEFINED` TRIGGERED).
- **B2BQ03** · Mark expiration model (Model A/B/C; PM baseline = C).
- **B2BQ04** · Mark refresh timestamp policy (server-authoritative).
- **B2BQ05** · Drain cancellation policy (CANCELLED terminal, no re-open).
- **B2BQ06** · Drain completion output contract (result_code + drain_execution_id).
- **B2BQ07** · Fragment gain source boundary (Drain complete only vs multi-source).
- **B2BQ08** · Resource segment close conditions (phase_end / expedition_terminal / explicit).
- **B2BQ09** · Lease strategy per transition (A/B/C).
- **B2BQ10** · Class-transition feature flag (`cdv_class_transitions_enabled` default OFF).
- **B2BQ11** · First transition code slice (Mark+Fragment+Segment first, Drain PM_REVIEW).
- **B2BQ12** · Local integration-test strategy (FakeStore + MongoStore isolated).
- **B2BQ13** · Audit sampling (INFO 100% · WARN 100%).
- **B2BQ14** · State-document receipt bound (TTL o cap N eventi).

**Agent auto-ratification count = 0** · **PM adjudication (Message 149) applied verbatim = 14/14**.
### PM Adjudication (Message 149) · 14/14 VERBATIM VERDICTS · Agent auto-ratifications = 0


**B2BQ01 · combat phase boundary source**
- chosen_option: `B` (expedition-as-single-phase)
- pm_status: `PM_RATIFIED_WITH_CONDITIONS`
- authority: PM_MESSAGE_149
- rationale: Modello TRANSITORIO SINGLE_EXPEDITION_PHASE_V1. Combat-phase reale richiede version bump + PM adjudication dedicata futura.
- conditions:
  - phase_model = SINGLE_EXPEDITION_PHASE_V1
  - phase_id deterministico = expedition:<expedition_id>:phase:1
  - phase start: dopo validazione + inizializzazione expedition state
  - phase end: immediatamente prima terminalizzazione expedition
  - stato iniziale: Fragments=0, resource_segment=inactive
  - stato finale: Fragments->0, resource_segment->closed, active Drains->cancelled
  - modello TRANSITORIO: real combat-phase richiede version bump + dedicated PM adjudication
  - fail-stop COMBAT_PHASE_BOUNDARY_UNDERDEFINED = RESOLVED_BY_TRANSITIONAL_SINGLE_PHASE_MODEL
- resolves_fail_stop: `COMBAT_PHASE_BOUNDARY_UNDERDEFINED`

**B2BQ02 · class event internal entry point**
- chosen_option: `B` (extend ExpeditionRuntimeCoordinator)
- pm_status: `PM_RATIFIED`
- authority: PM_MESSAGE_149
- rationale: Estensione coordinator interno, coerente con architettura RT2-B-2A shadow wiring.
- conditions:
  - entry point method: dispatch_class_state_event(event, trusted_context)
  - server-side only · non-esposto come route pubblica · non-importato frontend
  - server-authoritative · flag-gated · is_test_user=true · Mongo localhost allowlisted
  - VIETATO: public Mark/Drain/Fragment endpoint
  - VIETATO: admin gameplay route
  - VIETATO: client-controlled event_sequence / fencing_token
  - fail-stop CLASS_EVENT_ENTRYPOINT_UNDERDEFINED = RESOLVED_BY_INTERNAL_COORDINATOR_DISPATCH
- resolves_fail_stop: `CLASS_EVENT_ENTRYPOINT_UNDERDEFINED`

**B2BQ03 · Mark expiration model**
- chosen_option: `C` (hybrid (lazy validation obbligatoria + opportunistic cleanup))
- pm_status: `PM_RATIFIED`
- authority: PM_MESSAGE_149
- rationale: Modello hybrid PM-baseline; nessun background scheduler introdotto in RT2-B-2B-1.
- conditions:
  - validita': expires_at > authoritative_server_time
  - lazy validation OBBLIGATORIA su ogni accesso rilevante (apply, refresh, drain gate, hook check)
  - opportunistic cleanup CONSENTITO durante mutation/read/terminalization
  - scheduled expiration NON richiesta
  - nessun background scheduler in RT2-B-2B-1
  - Mark scaduto -> no Drain, no refresh, no hook, no ritual-close eligibility

**B2BQ04 · Mark refresh timestamp policy**
- chosen_option: `A` (server-authoritative timestamp)
- pm_status: `PM_RATIFIED`
- authority: PM_MESSAGE_149
- rationale: Server-authoritative clock impedisce clock-skew manipulation da client.
- conditions:
  - refresh timestamp source = authoritative server clock
  - new expires_at = server_now + configured_mark_duration
  - configured_mark_duration <= 10 seconds
  - refresh mantiene mark_id/application_id/ownership
  - refresh NON ripristina ritual_close_used
  - refresh incrementa mark_version + state_version
  - Mark gia' scaduto -> REFRESH_MARK -> MARK_EXPIRED -> rejected (richiede APPLY_MARK nuovo)

**B2BQ05 · Drain cancellation policy**
- chosen_option: `A + mandatory reason code` (CANCELLED terminal + reason_code obbligatorio)
- pm_status: `PM_RATIFIED_WITH_CONDITIONS`
- authority: PM_MESSAGE_149
- rationale: Terminale coerente con RT1 one_resolution_per_execution_id; reason_code richiesto per auditability.
- conditions:
  - STARTED -> CANCELLED terminale per stesso drain_execution_id · NON riapribile
  - reason_code obbligatorio in {MARK_EXPIRED, MARK_OWNERSHIP_MISMATCH, MARK_APPLICATION_CHANGED, TARGET_INVALID, SOURCE_INVALID, PHASE_ENDED, EXPEDITION_TERMINAL, EXPLICIT_SERVER_CANCEL}
  - nuovo Drain richiede nuovo drain_execution_id + tutte precondizioni ri-valide
  - completion su vecchio ID -> result_code=DRAIN_ALREADY_CANCELLED · no mutation · no reward · no Fragment

**B2BQ06 · Drain completion output contract**
- chosen_option: `C` (result_code + assigned_event_sequence (senza gameplay payload))
- pm_status: `PM_RATIFIED_WITH_CONDITIONS`
- authority: PM_MESSAGE_149
- rationale: Output audit-only; gameplay payload deferred a RT2-C. Nessuna esposizione pubblica.
- conditions:
  - output interno obbligatorio: drain_execution_id, status, result_code, mark_valid_at_completion, assigned_event_sequence, state_version_after, processed_at
  - ESCLUSIONI: damage=absent · healing=absent · XP=absent · loot=absent · fragment_reward_amount=absent · combat_result=absent
  - output interno auditabile · NON aggiunto alla response pubblica
  - public API contract invariato

**B2BQ07 · Fragment gain source boundary**
- chosen_option: `A` (accepted Drain completion only)
- pm_status: `PM_RATIFIED_WITH_CONDITIONS`
- authority: PM_MESSAGE_149
- rationale: In RT2-B-2B-1 (Drain rinviato): primitive Fragment gain implementata + testata con trusted fixture equivalente a Drain completion receipt valida.
- conditions:
  - GAIN_FRAGMENT valido richiede: accepted drain_execution_id + accepted Drain completion receipt
  - verifica: ownership CdV · stessa expedition · stessa fase · completion non gia' usata per gain · Mark valido al completion
  - in RT2-B-2B-1: primitive testata con trusted fixture, NON collegata al gameplay runtime
  - VIETATO: client grant · admin grant · gain da Mark apply · gain da item · gain da overflow · gain da spedizione completata

**B2BQ08 · Resource segment close conditions**
- chosen_option: `C + mandatory automatic closes` (phase_end + explicit close + expedition_terminal + fragment_count->0)
- pm_status: `PM_RATIFIED_WITH_CONDITIONS`
- authority: PM_MESSAGE_149
- rationale: Massima robustezza; chiusura esplicita non converte/rimborsa Frammenti.
- conditions:
  - chiusure obbligatorie: fragment_count -> 0 · phase ends · expedition terminal · explicit server-side CLOSE_RESOURCE_SEGMENT
  - spesa parziale con Frammenti positivi -> mantiene stesso resource_segment_id
  - nuovo segmento apre solo quando fragment_count: 0 -> positive
  - preservare hard-lock: focus_bonus_usage <= 2 per segment
  - chiusura esplicita NON converte ne' rimborsa Frammenti

**B2BQ09 · Lease strategy per transition**
- chosen_option: `B` (short lease per server-authoritative event batch)
- pm_status: `PM_RATIFIED_WITH_CONDITIONS`
- authority: PM_MESSAGE_149
- rationale: Ogni event server-authoritative = batch atomico. CAS obbligatorio DENTRO il lease.
- conditions:
  - ogni evento server-authoritative = event batch atomico
  - batch APPLY_MARK = 1 batch
  - batch COMPLETE_DRAIN + future Fragment gain = 1 batch
  - batch END_PHASE + reset resources + cancel Drains = 1 batch
  - sequenza: (1) acquire short request-scoped lease (2) obtain/validate fencing token (3) read expected state_version (4) apply mutations atomically (5) increment state_version once (6) persist event receipt (7) release/expire lease
  - CAS obbligatorio DENTRO il lease
  - CAS-only senza lease valido = FORBIDDEN
  - retry max 3 · ogni retry rilettura stato + verifica lease/fencing validi
  - nessun background lease renewer in RT2-B-2B-1

**B2BQ10 · class-transition feature flag**
- chosen_option: `A` (nuovo flag cdv_class_transitions_enabled default OFF)
- pm_status: `PM_RATIFIED`
- authority: PM_MESSAGE_149
- rationale: Nuovo flag dedicato PM baseline; gate composito quadruple-check.
- conditions:
  - nuovo flag: cdv_class_transitions_enabled default OFF
  - gate composito ELEGGIBILITA': cdv_transient_state_enabled=true AND cdv_class_transitions_enabled=true AND is_test_user=true AND environment=localhost isolated AND Mongo target=allowlisted
  - valore mancante/invalido -> false
  - flag OFF: 0 DB calls · 0 audit events · 0 state mutation

**B2BQ11 · first transition code slice**
- chosen_option: `A` (Mark + Fragment + Resource Segment (Drain rinviato a RT2-B-2B-2))
- pm_status: `PM_RATIFIED_WITH_CONDITIONS`
- authority: PM_MESSAGE_149
- rationale: Scope contained; Fragment gain testata via trusted fixture (Drain runtime deferred).
- conditions:
  - gate name: R18.6.RV3-IS2-B-P2B-RT2-B-2B-1 · MARK & RESOURCE STATE TRANSITION FOUNDATION
  - scope: Mark apply/refresh/lazy expiration/opportunistic cleanup/ownership+cap validation · Fragment gain primitive/spend/reset/overflow discard · resource segment open/close · event ordering · event receipt generation · lease+fencing+CAS event batches · flag default-OFF · test-user fail-closed · FakeStore + real-Mongo local tests
  - Fragment condition: GAIN_FRAGMENT implementata SENZA sorgente gameplay reale · test usa trusted fixture Drain completion receipt
  - ESCLUSO: Drain runtime transitions · damage · healing · XP · loot · guild XP · item effects · proc · cooldown engine · public API · frontend · shared environment · human tester activation
  - Drain rinviato a RT2-B-2B-2 · DRAIN TRANSITION FOUNDATION · status PLANNED / HOLD

**B2BQ12 · local integration-test strategy**
- chosen_option: `C` (both FakeStore + MongoStore isolated)
- pm_status: `PM_RATIFIED`
- authority: PM_MESSAGE_149
- rationale: Coverage duplicata FakeStore+MongoStore, pattern coerente con RT2-B-1B-1.
- conditions:
  - test layers: pure state-machine · FakeStore contract · mocked Mongo adapter · real Mongo localhost integration
  - DB consentiti: orbus_r16_rt2b_test · orbus_r16_rt2b_it_<unique_run_id>
  - DB vietati: orbus_r16 · orbus_r16_test · preview · staging · production
  - ogni suite Mongo: unique run ID · cleanup · parallel isolation · zero DB residui

**B2BQ13 · audit sampling**
- chosen_option: `A` (INFO 100% + WARN 100% + ERROR 100% (all-log locale))
- pm_status: `PM_RATIFIED_WITH_CONDITIONS`
- authority: PM_MESSAGE_149
- rationale: 100% locale non diventa automaticamente policy produzione; shared env richiede nuova adjudication.
- conditions:
  - localhost integration: INFO transition=100% · WARN rejection/conflict=100% · ERROR integrity/security=100%
  - NON registrare: intero doc Mongo · full payload · credenziali · RNG seed · dati sensibili · reward payload non ratificati
  - prima di shared env -> audit sampling+retention richiede NEW PM ADJUDICATION
  - 100% locale NON diventa automaticamente policy produzione

**B2BQ14 · state-document receipt bound**
- chosen_option: `fixed bounded receipt set, NO rolling eviction` (hard cap 512 total / 504 ordinary / 8 reserved · no eviction · no overwrite)
- pm_status: `PM_RATIFIED_WITH_CONDITIONS`
- authority: PM_MESSAGE_149
- rationale: Cap statico deterministico; TTL su singole chiavi embedded escluso.
- conditions:
  - hard cap: total receipt capacity = 512
  - ordinary class-event ceiling = 504
  - reserved lifecycle/system = 8
  - slot riservati per: phase end · expedition terminalization · cancellation · cleanup-critical lifecycle
  - saturazione (504 ordinarie): new ordinary event -> RECEIPT_CAP_REACHED · fail closed · no mutation
  - PRESERVARE: active receipt eviction=FORBIDDEN · old receipt overwrite=FORBIDDEN · duplicate receipt removal=FORBIDDEN
  - receipt restano fino a scadenza stato
  - size guard: 512 receipt + fixture stress -> state document < 256 KiB DIMOSTRATO
  - se superato -> STATE_DOCUMENT_SIZE_BUDGET_EXCEEDED · STOP · no automatic cap increase
  - NON usare TTL per singole chiavi embedded


---

## Sezione 40 · First Code-Slice Proposal (PM_REVIEW)

Candidato: `R18.6.RV3-IS2-B-P2B-RT2-B-2B-1 · MARK & RESOURCE STATE TRANSITION FOUNDATION`.

Scope candidato:
- Mark apply/refresh/expire · Fragment gain/spend/reset · resource segment open/close.
- State-machine models (Enum StateType per Mark/Drain/Fragment).
- Atomic transition functions con CAS + fencing.
- Event receipts (`processed_event_keys` growth policy TBD B2BQ14).
- Local Mongo integration tests (allowlist B2Q10).
- Flags default-OFF (nuovo `cdv_class_transitions_enabled` TBD B2BQ10).
- Test-user fail-closed invariato.

**Drain**: incluso OR rinviato a `RT2-B-2B-2` in base a discovery e B2BQ01/02/05. Scelta = `PM_REVIEW` (B2BQ11).

**Esclusioni verbatim `RT2-B-2B-1`**: combat damage · healing · XP/loot rewards · guild XP · success-chance changes · item procs · affix effects · cooldown engine · Legendary effects · boss dispel · anti-summon · PvP · frontend · public API changes · shared-env writes.

---

> **PM Decision (B2BQ11, Message 149)**: `A` · `PM_RATIFIED_WITH_CONDITIONS` · `Mark + Fragment + Resource Segment (Drain rinviato a RT2-B-2B-2)`

## Sezione 41 · Readiness

| Aspetto | Stato |
|---|---|
| State-store contract | READY (11 op astratte, adapter reale validato RT2-B-1B-1) |
| Shell state lifecycle | READY (post RT2-B-2A) |
| Class-state schema | READY (MarkDoc, DrainDoc, FragmentUsage in models.py) |
| Event schema | READY (event_id, event_type, payload_hash contract) |
| Combat phase boundary | **NOT READY** (fail-stop TRIGGERED · B2BQ01) |
| Class event entry point | **NOT READY** (fail-stop TRIGGERED · B2BQ02) |
| Mark state machine | READY (design documentato) |
| Drain state machine | READY (design documentato) |
| Fragment state machine | READY (design documentato) |
| Resource segments | READY (design documentato) |
| Feature flag scope | PENDING (B2BQ10) |
| Lease strategy | PENDING (B2BQ09) |
| First code slice scope | PENDING (B2BQ11) |
| Integration test strategy | PENDING (B2BQ12) |

---

## Sezione 42 · GO/HOLD Recommendation

**`RT2-B-2B-P0`**: `READY FOR PM ADJUDICATION`. 14 B2BQ emesse, nessuna auto-ratificata. 2 fail-stop TRIGGERED (COMBAT_PHASE_BOUNDARY · CLASS_EVENT_ENTRYPOINT). 4 fail-stop NOT_TRIGGERED (CLASS_STATE_ATOMICITY_CONFLICT · PUBLIC_API_SCOPE_EXPANSION_REQUIRED · SHARED_ENVIRONMENT_REQUIRED · ITEM_EFFECT_SCOPE_DEPENDENCY).

**`RT2-B-2B-1`**: `HOLD · CONDITIONAL_GO_AFTER_ADJUDICATION`. Dispatch code slice autorizzabile solo dopo:
1. Ratifica PM di 14/14 B2BQ.
2. Risoluzione formale dei 2 fail-stop triggered.
3. Formal closure `RT2-B-2B-P0` con manifest §31.

**Shared-env activation** e **tester gameplay activation**: `LOCK · NOT_AUTHORIZED`.

---

## Sezione 43 · Explicit STOP

Draft `RT2-B-2B-P0` completo. Nessuna scrittura ulteriore autorizzata:
- Nessuna modifica applicativa.
- Nessuna scrittura DB.
- Nessun toggle FF.
- Nessuna nuova rotta.
- Nessun closure manifest in P0 draft (produrre solo post-adjudication PM).
- Nessun PRD append in P0 draft.

In attesa di:
1. Ratifica PM verbatim delle 14 B2BQ.
2. Adjudication dei 2 fail-stop triggered (`COMBAT_PHASE_BOUNDARY_UNDERDEFINED` · `CLASS_EVENT_ENTRYPOINT_UNDERDEFINED`).
3. Dispatch orchestrator per formal closure `RT2-B-2B-P0` post-adjudication.

**`STRICT STOP · Phase P0 CLOSED post-PM adjudication (Msg 149) · documental only · fine`**.

---

**Fine documento** · Italian_only · DOCUMENTAL_ONLY · RT2-B-2B-P0 DRAFT · SHA §31 · STRICT STOP
