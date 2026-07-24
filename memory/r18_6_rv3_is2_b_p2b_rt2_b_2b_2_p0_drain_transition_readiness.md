# R18.6.RV3-IS2-B-P2B-RT2-B-2B-2-P0 · DRAIN TRANSITION FOUNDATION READINESS & COMPLETION-TO-FRAGMENT CONTRACT

**Gate**: `R18.6.RV3-IS2-B-P2B-RT2-B-2B-2-P0`
**Canonical name**: DRAIN TRANSITION FOUNDATION READINESS & COMPLETION-TO-FRAGMENT CONTRACT
**Status**: **PATCHED · 16/16 B2B2Q PM-ADJUDICATED VERBATIM · AWAITS FORMAL CLOSURE**
**Regime**: **DOCUMENTAL ONLY · READ-ONLY DISCOVERY · NO CODE · NO APPLY · NO DB WRITES · NO FEATURE ACTIVATION**
**PM authority**: Message 168 (dispatch) · Message 170 (patch + adjudication)
**Draft date (UTC)**: 2026-02 · **Patch date (UTC)**: 2026-02
**Parent gate closed**: `RT2-B-2B-1 · MARK & RESOURCE STATE TRANSITION FOUNDATION` (CLOSED · PM-LOCKED · V1 INCORPORATED)
**Baseline chain**: **15/15 (INVARIATA durante questo patch · +1 riservato a formal closure P0)**

---

## 1 · Executive summary

Il presente P0 disegna il contratto deterministico per **Drain** — startup, completion, cancellation — e la sua integrazione atomica con la primitiva Fragment già implementata in RT2-B-2B-1. Regime documentale: nessun code change, nessuna scrittura Mongo, nessuna attivazione flag. Il draft è ora **PATCHATO** integrando i 16 verdict PM Message 170 in modalità VERBATIM (0 auto-ratifiche agent).

Portata (PM §4):
- `START_DRAIN` (`NOT_STARTED → STARTED`) · `COMPLETE_DRAIN` (`STARTED → COMPLETED`) · `CANCEL_DRAIN` (`STARTED → CANCELLED`)
- **Completion-to-Fragment atomic batch** unico (drain completion + completion receipt + Fragment gain decision + overflow discard + eventual segment opening + processed event receipt + `state_version` +1)
- Invarianti bloccanti (PM §4 verbatim): Drain completato senza decisione Fragment = IMPOSSIBILE · Fragment assegnato senza Drain completato = IMPOSSIBILE · doppia assegnazione sul retry = IMPOSSIBILE · mutation parziale = IMPOSSIBILE
- Kill-switch separato: nuovo `cdv_drain_transitions_enabled` (default OFF), **6-conditions gate composito** (PM Message 170 §13 normalization — non usare "quintuple-gate": sono 6 condizioni)
- Cancellation reason codes: riuso verbatim degli 8 codici già ratificati in RT2-B-2B-P0 B2BQ05
- Receipt storage rule PM §7: completion result payload **EMBEDDED** in processed event receipt · **NON** un secondo slot indipendente

Fuori portata (PM §5): damage · healing · XP · loot · guild XP · success probability · combat resolution · item/affix/proc/cooldown · Legendary · PvP · public API · frontend · human tester activation. Il risultato del Drain resta transizione interna di stato.

## 2 · Scope

**IN**: transizioni pure `START_DRAIN`, `COMPLETE_DRAIN`, `CANCEL_DRAIN`; atomic completion-to-Fragment batch; kill-switch dedicato; Mark binding; execution identity server-authoritative UUIDv4 completo; receipt policy 512/504+8 invariata; lease+fencing+CAS 8-step; audit contract 10 event ids; test contract 32+ casi; hard-lock max=1 Drain per (source,target) e max=1 per Mark application (PM Message 170 §18).

**OUT**: Drain runtime executor separato (RT2-C effect execution) · reward payload · gameplay effect · public API/OpenAPI · frontend/UX · shared-env rollout · human tester activation · flag activation in production · Registry/Mongo provisioning · Registry migration · focus_bonus mutation.

## 3 · Governance

- Regime R18.6 · PM dispatch Message 168 + adjudication Message 170 vincolanti · Regime documentale (nessun code change).
- Baseline chain **15/15 INVARIATA** durante il P0 patch (increment autorizzato solo su formal closure P0 = 16/16).
- Sealed integrity **36/36 byte-identical**: `pytest tests/backend_r18_4_sealed_integrity_test.py` → 6 PASS.
- `effect_engine` **396/396** serial + xdist · target invariante.
- `lore_meta.py` invariant SHA `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` · **INVARIANT**.
- OpenAPI paths **275** · new routes = 0 · frontend changes = 0 · `.env` changes = 0 · feature flag activation = 0.
- Fail-stop P0 (§25 verbatim): **NONE** (nessun blocker documentale rilevato).

## 4 · Source chain

- `/app/memory/r18_6_rv3_is2_b_p2b_rt2_b_2b_1_final_closure_report.md` (SHA `5de28c0883fa4acfa6bd512108d7ec23b2bb5f6ffde944017a2b4715e752d249`)
- `/app/memory/r18_6_rv3_is2_b_p2b_rt2_b_2b_1_closure_manifest.json` (SHA `8c47b18bada7f255219f4afcca2dc0e0aea9e745833a52f0207815a0c346d2a5`)
- `/app/memory/r18_6_rv3_is2_b_p2b_rt2_b_2b_1_implementation_report.md/json`
- `/app/memory/r18_6_rv3_is2_b_p2b_rt2_b_2b_1_real_mongo_verification_addendum.md/json`
- `/app/memory/r18_6_rv3_is2_b_p2b_rt2_b_2b_p0_final_closure_report.md/json` (Q&A parent P0 · 14 verdetti PM)
- Codice runtime: `app/stats/runtime/transitions/*` + `app/stats/runtime/wiring/coordinator.py` + `app/stats/runtime/state_store/*` (foundation immutabile durante il draft/patch).

## 5 · Current Mark foundation

- `MarkDoc` (`app/stats/runtime/state_store/models.py`): `mark_id`, `application_id`, `source_adventurer_id`, `target_id`, `created_at`, `expires_at` (=`created_at + 10s`), `ritual_close_used`, `mark_version`.
- Invarianti verbatim: `active_marks ≤ 5 per source` · `one Mark per (source,target)` · duration ≤ 10s · lazy expiration authoritative server time · opportunistic cleanup · NO auto-eviction.
- Event types Mark: `APPLY_MARK`, `REFRESH_MARK`, `LAZY_MARK_EXPIRATION`, `OPPORTUNISTIC_MARK_CLEANUP`.
- Ownership check: source must equal caller identity; foreign-Mark drain = FORBIDDEN.

## 6 · Current Fragment foundation

- `AdventurerClassState.fragment_count ≤ 5` (`FRAGMENT_CAP=5`).
- Event types: `GAIN_FRAGMENT`, `SPEND_FRAGMENT`, `RESET_FRAGMENTS`, `DISCARD_FRAGMENT_OVERFLOW`.
- `GAIN_FRAGMENT` valido richiede **accepted Drain completion receipt** (`TrustedDrainReceipt` fixture-only in RT2-B-2B-1). In RT2-B-2B-2-1 la fixture sarà rimossa e sostituita da receipt reale generata dal Drain runtime.
- Overflow: discarded diagnostic-only · overflow reward = FORBIDDEN · partial credit = FORBIDDEN.

## 7 · Current coordinator entry point

- `ExpeditionRuntimeCoordinator.dispatch_class_state_event(event, trusted_context)` in `wiring/coordinator.py:242`.
- `trusted_context` (**PM Message 170 B2B2Q02**): contiene `authenticated user · is_test_user · environment · target Mongo · expedition identity · source-adventurer ownership · feature-flag snapshot`. Nessun campo trusted derivabile da header/query/body client.
- Audit emit interno via `_class_event_audit_id(event_type, result_code)` (attuali 11 canonical ids + `cdv_state_transition_conflict` rejection routing).
- Il Drain **riusa** questo entry point (nessun nuovo endpoint pubblico) aggiungendo nuovi `ClassEventType` values (`START_DRAIN`, `COMPLETE_DRAIN`, `CANCEL_DRAIN`).

## 8 · Current state-store contract

- Interfaccia `ExpeditionRuntimeStateStore` + implementazioni `FakeExpeditionRuntimeStateStore` (unit) + `MongoExpeditionRuntimeStateStore` (integration).
- Metodi: `create_state`, `get_state`, `reserve_writer`, `renew_writer_lease`, `release_writer`, `compare_and_update`, `apply_event_once`, `expire_state`, `delete_state`, `get_version`, `health_check`.
- CAS: `find_one_and_update` con filter `{_id, state_version, fencing_token, [dedup guards]}`; update `$inc/$set/$push`.
- Receipt policy: `MAX_PROCESSED_EVENTS = 512` (hard cap store-side); categorizzazione ORDINARY(504)/RESERVED(8) applicativa.

## 9 · Drain domain model

Campi `DrainDoc` obbligatori post-patch (PM §9 binding contract):
- `drain_execution_id: str` (server-authoritative UUIDv4 completo · vedi §10)
- `source_adventurer_id: str`
- `target_id: str`
- `mark_id: str` (nuovo campo introdotto dal code gate)
- `required_mark_application_id: str`
- `started_at: str` (ISO UTC)
- `completed_at: Optional[str]`
- `cancelled_at: Optional[str]`
- `runtime_status: DrainStatus` (`IN_PROGRESS` | `RESOLVED` | `CANCELLED` | `EXPIRED`)
- `cancellation_reason: Optional[str]` (uno degli 8 canonici · vedi §18)
- `drain_version: int` (monotonic per aggregato, initial=1)

Persistenza: `AdventurerClassState.active_drain_executions: Tuple[DrainDoc, ...]` (già presente).

**Hard-lock PM Message 170 §18**:
- `maximum active Drain per (source_adventurer_id, target_id) pair = 1`
- `maximum active Drain per Mark application (mark_id, required_mark_application_id) = 1`
- Nuovo start con Drain STARTED esistente su stesso pair/application → `DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR`
- Drain terminali (COMPLETED/CANCELLED/EXPIRED) possono restare bounded nello storico fino a scadenza state document · NON bloccano nuovo Drain su nuova applicazione valida
- Preservate invarianti: `Drain consumes Mark = false` · `Fragment amount per accepted completion = 1` · `Drain completion at Fragment cap = accepted with overflow discarded`

## 10 · Drain execution identity (B2B2Q01 · `PM_RATIFIED_WITH_CONDITIONS`)

**Verdict PM Message 170 B2B2Q01 verbatim**:
- `drain_execution_id = "drn-" + canonical UUIDv4` (**NON troncato**)
- Esempio canonico: `drn-550e8400-e29b-41d4-a716-446655440000`
- **Vietato**: UUID troncato · client-provided · derivato da input · riutilizzabile post-cancel/complete
- **Replay stesso start event** → restituisce ID già assegnato dalla receipt precedente (dedup path)

Server-authoritative: client NON può controllare identity, ownership, application binding, event sequence, fencing token, Fragment result.

## 11 · Drain ownership

- `source_adventurer_id` di ogni comando Drain coincide con l'identità del caller autenticato (via `trusted_context.test_user_id`).
- Foreign-Drain (source ≠ caller) = FORBIDDEN → `OWNERSHIP_INVALID` (mapped a `MARK_OWNERSHIP_MISMATCH` reason canonico dove applicabile).
- Un Drain non può essere completato/annullato da `source_adventurer_id` diverso da quello che l'ha avviato.

## 12 · Mark binding (B2B2Q03 · `PM_RATIFIED`)

**Verdict PM Message 170 B2B2Q03 verbatim (strict application_id invariance)**:
- Drain conserva `mark_id` + `required_mark_application_id` (letti al `START_DRAIN`)
- **Refresh valido**: mantiene `mark_id` + `application_id` · estende `expires_at` · **non invalida** Drain
- **Scadenza + nuova applicazione** → nuovo `application_id` → old Drain binding **invalid** (anche stesso source/target)

Il Drain **NON consuma** il Mark; il Mark resta attivo fino a expiration/cleanup.

## 13 · START_DRAIN state machine

Transizione: `NOT_STARTED → STARTED` (creazione `DrainDoc` con `runtime_status=IN_PROGRESS`).

Sequenza atomica (event batch unico, 8-step):
1. lease acquire (short request-scoped, TTL 30s, fencing bump se new)
2. fencing token validation
3. read `state_version` expected
4. validate precondizioni (§14)
5. server-generate `drain_execution_id = "drn-" + UUIDv4` (dedup: se stesso start event già processato, ritorna prior ID)
6. apply mutation: append `DrainDoc(runtime_status=IN_PROGRESS, drain_execution_id, mark_id, application_id, started_at)`
7. `state_version += 1` · `last_event_sequence += 1` · persist `START_DRAIN` receipt (ORDINARY · payload EMBEDDED)
8. lease release/expire

## 14 · START_DRAIN validation (B2B2Q04-driven pattern reuse)

Precondizioni verbatim PM §4:
- expedition active (`runtime_status = ACTIVE`)
- single phase active (`phase_id` non terminale)
- source valid · target valid (non null · non self)
- own active Mark su `(source, target)` (Mark non scaduto)
- `mark_id` matches Mark
- `application_id` matches Mark
- **max Drain per (source,target) = 1** (hard-lock PM §18)
- **max Drain per Mark application = 1** (hard-lock PM §18)
- event not previously processed (dedup guard su `event_id`)
- receipt capacity available (ordinary slot free)
- valid lease + fencing token
- `expected_state_version` matches

Result codes rejection (B2B2Q09): `DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR`, `MARK_NOT_FOUND`, `MARK_EXPIRED`, `MARK_OWNERSHIP_MISMATCH`, `MARK_APPLICATION_CHANGED`, `TARGET_INVALID`, `SOURCE_INVALID`, `EXPEDITION_TERMINAL_REJECTED`, `PHASE_INACTIVE`, `RECEIPT_CAP_REACHED`, `EVENT_ID_PAYLOAD_MISMATCH`, `STATE_VERSION_CONFLICT`, `STALE_WRITER_REJECTED`, `LEASE_ACQUISITION_FAILED`, `RETRY_LIMIT_REACHED`.

## 15 · COMPLETE_DRAIN state machine

Transizione: `STARTED → COMPLETED` con **completion-to-Fragment atomic batch** (§26).

Sequenza atomica unica (single writer):
1. lease acquire · fencing validate · read `state_version`
2. rivalidazioni obbligatorie (§16 · 15 checks)
3. compute Fragment outcome (§27–§28): `fragment_gain_requested=1` fisso · check cap → apply o overflow_discarded
4. compute segment opening (§29): if `fragment_count 0 → positive`, open segment
5. apply mutations atomically in single CAS: `DrainDoc.runtime_status=RESOLVED · completed_at`, `fragment_count += applied`, eventual `resource_segment_id`, `overflow_discarded` counter
6. `state_version += 1` (exactly once) · `last_event_sequence += 1`
7. **persist single processed event receipt** con completion result payload EMBEDDED (PM Message 170 B2B2Q07 verbatim: `receipt storage rule = result payload EMBEDDED in the processed event receipt · NON occupare un secondo slot indipendente`) · ORDINARY category
8. lease release/expire

## 16 · COMPLETE_DRAIN validation (B2B2Q04 · `PM_RATIFIED`)

**15 rivalidazioni atomiche obbligatorie (Message 170 B2B2Q04 verbatim)**:
1. source (source_adventurer_id match caller identity)
2. target (target_id match DrainDoc)
3. mark_id (match DrainDoc.mark_id)
4. application_id (match DrainDoc.required_mark_application_id)
5. Mark ownership (Mark.source_adventurer_id == caller)
6. Mark active (MarkDoc present nell'`active_marks` dell'adventurer)
7. Mark not expired (server clock < expires_at)
8. Drain status == STARTED (`DrainDoc.runtime_status = IN_PROGRESS`)
9. Drain not cancelled
10. Drain not completed (idempotency)
11. phase active (phase not ended)
12. expedition not terminal
13. valid lease
14. valid fencing token
15. expected `state_version` matches

Una sola falsa → rejected/cancelled per reason canonico · no Fragment · no partial mutation.

## 17 · CANCEL_DRAIN state machine

Transizione: `STARTED → CANCELLED`. Terminale per `drain_execution_id` corrente.

Trigger:
- **Explicit**: reason_code = `EXPLICIT_SERVER_CANCEL`
- **Automatic on phase_end**: reason_code = `PHASE_ENDED` (lifecycle batch · aggregate reserved receipt · §22-§24)
- **Automatic on expedition_terminal**: reason_code = `EXPEDITION_TERMINAL` (lifecycle batch)
- **Lazy Mark-expiration cascade** durante comando Drain: reason_code = `MARK_EXPIRED` | `MARK_OWNERSHIP_MISMATCH` | `MARK_APPLICATION_CHANGED` · **result FOLDED nella receipt ordinaria del triggering event** (PM B2B2Q14 verbatim · NO seconda receipt `DRAIN_AUTO_CANCELLED_ON_MARK_EXPIRATION`)
- **Cascade on Mark event**: `TARGET_INVALID` | `SOURCE_INVALID`

Effetti: `DrainDoc.runtime_status = CANCELLED · cancelled_at · cancellation_reason` valorizzato con uno degli 8 codici. Nuovo tentativo richiede **nuovo `drain_execution_id`** + revalidation completa.

## 18 · Cancellation reason codes (B2B2Q08 · `PM_RATIFIED`)

**PM Message 170 B2B2Q08 verbatim: NO extensions. Riuso verbatim 8 codici RT2-B-2B-P0 B2BQ05. NO alias · NO versioni abbreviate. Nuove necessità in code gate → STOP · PM REVIEW.**

1. `MARK_EXPIRED`
2. `MARK_OWNERSHIP_MISMATCH`
3. `MARK_APPLICATION_CHANGED`
4. `TARGET_INVALID`
5. `SOURCE_INVALID`
6. `PHASE_ENDED`
7. `EXPEDITION_TERMINAL`
8. `EXPLICIT_SERVER_CANCEL`

## 19 · Completion / rejection result codes (B2B2Q09 · `PM_RATIFIED_WITH_CONDITIONS`)

**PM Message 170 B2B2Q09 canonical set (verbatim)**:

- **Success**: `DRAIN_STARTED · DRAIN_COMPLETED · DRAIN_CANCELLED`
- **Start rejection**: `DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR · MARK_NOT_FOUND · MARK_EXPIRED · MARK_OWNERSHIP_MISMATCH · MARK_APPLICATION_CHANGED · TARGET_INVALID · SOURCE_INVALID · EXPEDITION_TERMINAL_REJECTED · PHASE_INACTIVE · RECEIPT_CAP_REACHED`
- **State**: `DRAIN_NOT_STARTED · DRAIN_ALREADY_COMPLETED · DRAIN_ALREADY_CANCELLED`
- **Integrity/concurrency**: `EVENT_ID_PAYLOAD_MISMATCH · STATE_VERSION_CONFLICT · STALE_WRITER_REJECTED · LEASE_ACQUISITION_FAILED · RETRY_LIMIT_REACHED`

Distinti dagli 8 cancellation reason codes (§18).

## 20 · Drain idempotency

- Stesso `event_id + payload_hash uguale` → return prior result · **no new mutation** · **no second Fragment grant** · **no new drain_execution_id** (returns prior ID)
- Stesso `event_id + payload_hash diverso` → `EVENT_ID_PAYLOAD_MISMATCH` reject
- Stesso `drain_execution_id` completato con `event_id` diverso → `DRAIN_ALREADY_COMPLETED` · no mutation
- Cancel su Drain già cancelled → `DRAIN_ALREADY_CANCELLED` · no mutation

Enforcement via `apply_event_once` (state_store) + guard applicativo su `DrainDoc.runtime_status`.

## 21 · Event ordering

Ordering totale per `expedition_id` (invariato da RT2-B-2B-1):
- `last_event_sequence` incrementato +1 per ogni event batch accepted
- CAS filter garantisce single writer per `state_version`
- Concurrent starts stesso `(source,target)` → 1 SUCCESS + 1 `DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR`
- Concurrent completions stesso `drain_execution_id` → 1 SUCCESS + 1 `DRAIN_ALREADY_COMPLETED`
- Concurrent starts diversi drain executions (diverso target) → possono succedere entrambi

## 22 · Cancellation races (B2B2Q10 · `PM_RATIFIED`)

**PM Message 170 B2B2Q10 verbatim (first-committed-wins)**:
- Precedenza determinata da primo event batch validamente committato via lease/fencing/CAS.
- Completion first → later cancellation → `DRAIN_ALREADY_COMPLETED` · **no mutation**
- Cancellation first → later completion → `DRAIN_ALREADY_CANCELLED` · **no mutation · no Fragment**
- **Un solo writer** modifica lo stato · **orario client NON determina precedenza**

## 23 · Expiration races

- **complete vs Mark expiration**: se Mark scade nel window tra start e complete, revalidation al complete → `MARK_EXPIRED`. Il Drain viene **AUTO-CANCELLATO con reason `MARK_EXPIRED` foldato nella receipt del triggering event** (PM B2B2Q14 verbatim · no separate receipt).
- **complete vs Mark refresh**: refresh mantiene `application_id` invariato → Drain resta valido, no impact.
- **complete vs new Mark application** (dopo expiration): nuovo `application_id` ≠ salvato → rejection `MARK_APPLICATION_CHANGED` + Drain cancelled (folded in stessa receipt).

## 24 · Terminalization races (B2B2Q11 · `PM_RATIFIED_WITH_CONDITIONS`)

**PM Message 170 B2B2Q11 verbatim (lifecycle batch precedence)**:
- **Phase-end committed first** → all STARTED Drains → CANCELLED con `PHASE_ENDED` · later completion **rejected**
- **Completion first** → completion valida · Fragment outcome valido · successivo phase-end cancella **solo Drain ancora STARTED**

**Reserved receipt policy CRITICA (PM Message 170 §11)**:
- Phase-end usa **ONE reserved lifecycle receipt** per l'INTERO atomic lifecycle batch (NON una receipt per Drain cancellato)
- Lifecycle receipt contenuto: `count_drains_cancelled · bounded list of drain_execution_ids cancelled · aggregate cancellation_reason · state_version_after`
- **`simultaneous Drain hard cap = NOT INTRODUCED`** (nessun cap globale al numero di Drain concorrenti — solo il cap max=1 per pair/application)
- Le **8 receipt riservate = 8 lifecycle event batch** (NON 8 singoli Drain cancellati)

Analogo per expedition terminal: aggregate reserved receipt · reason `EXPEDITION_TERMINAL`.

## 25 · Completion receipt (B2B2Q07 · `PM_RATIFIED_WITH_CONDITIONS`)

**Field set VERBATIM PM Message 170 B2B2Q07 (15 campi)**:

```
completion_receipt (EMBEDDED in processed event receipt · same slot):
  drain_execution_id: str
  completion_event_id: str
  source_adventurer_id: str
  target_id: str
  mark_id: str
  application_id: str
  result_code: str                       # SUCCESS | rejection code
  mark_valid_at_completion: bool
  fragment_gain_requested: int           # fissato = 1 (B2B2Q05)
  fragment_gain_applied: int             # 0 o 1 (post cap check)
  fragment_overflow_discarded: int       # 0 o 1
  resource_segment_id: Optional[str]
  assigned_event_sequence: int
  state_version_after: int
  processed_at: str                      # ISO UTC
```

**Receipt storage rule OBBLIGATORIA (PM Message 170 B2B2Q07 verbatim)**:
- Completion receipt = **result payload EMBEDDED in the processed event receipt**
- **NON occupare un secondo slot indipendente nella capacità 512**

**Esclusioni**: damage · healing · XP · loot · item proc · combat result · RNG seed · reward payload.

## 26 · Completion-to-Fragment batch (B2B2Q07 · `PM_RATIFIED_WITH_CONDITIONS`)

Single atomic event batch (contratto verbatim PM §4 + Message 170 §7):
- Drain completion status (`DrainDoc.runtime_status = RESOLVED`)
- Completion result payload (§25 · EMBEDDED nel processed event receipt)
- Fragment gain result (`fragment_count += applied`, sempre 0 o 1)
- Overflow discard result (`overflow_discarded` counter incremented se al cap)
- Resource-segment opening quando `fragment_count 0 → positive`
- Processed event receipt (dedup slot · ORDINARY · payload EMBEDDED)
- `state_version` +1 exactly once

Invarianti (verbatim PM §4):
- Drain completato senza decisione Fragment = IMPOSSIBILE
- Fragment assegnato senza Drain completato = IMPOSSIBILE
- Doppia assegnazione sul retry = IMPOSSIBILE (dedup event_id + DrainDoc.runtime_status)
- Mutation parziale = IMPOSSIBILE (single CAS all-or-nothing)

## 27 · Fragment amount policy (B2B2Q05 · `PM_RATIFIED_WITH_CONDITIONS`)

**PM Message 170 B2B2Q05 verbatim (fixed=1)**:
- `accepted Drain completion → fragment_gain_requested = 1`
- **Vietato**: RNG · scaling refresh count · scaling equip · bonus item · bonus Legendary · moltiplicatori fase
- Variazioni future → **nuovo balance verdict PM** (fuori scope P0 e code gate RT2-B-2B-2-1)

## 28 · Fragment cap and overflow (B2B2Q06 · `PM_RATIFIED`)

**PM Message 170 B2B2Q06 verbatim (at-cap behavior)**:

Se `fragment_count == 5`:
- Drain status → **COMPLETED**
- `fragment_gain_requested = 1`
- `fragment_gain_applied = 0`
- `fragment_overflow_discarded = 1`
- **No cancellation · no rejection · no credito futuro · no proc · no ricompensa alternativa**

Audit event: `cdv_drain_fragment_overflow_discarded` emesso (§38).

## 29 · Resource segment interaction

Regole verbatim PM §11 (invariate):
- Quando completion produce `fragment_count 0 → positive` (transizione strict): APRE resource segment nello stesso event batch. Nuovo `resource_segment_id = "sg-" + uuid[:16]`.
- Se segmento già attivo: preserve current `resource_segment_id`.
- Il Drain **NON**: chiude direttamente segmento · consuma Frammenti · incrementa `focus_bonus_usage`.

`resource_segment_id` incluso nella completion receipt solo se associato all'adventurer post-mutation.

## 30 · Focus bonus boundary

Regola verbatim PM §12:
- `focus_bonus_usage` interaction with Drain = **DEFERRED**
- Nel gate Drain: Drain completion changes `focus_bonus_usage` = **FORBIDDEN**
- Preserva invariante: `focus_bonus_usage ≤ 2 per resource_segment` (invariato da RT2-B-2B-1)
- Incremento + effetto concreto → RT2-C (effect execution) o RT2-E (item hooks) · verdict separato futuro

## 31 · Lease strategy (B2B2Q12 · `PM_RATIFIED`)

**PM Message 170 B2B2Q12 verbatim (existing policy)**:
- One short request-scoped lease per event batch
- **Valid fencing token mandatory · CAS inside lease mandatory · CAS-only FORBIDDEN**
- Retry max 3 · background renewer FORBIDDEN
- Ogni retry rivalida: Mark · application binding · Drain status · expedition/phase state · dedup receipt · receipt capacity · fencing token

## 32 · Fencing

- `fencing_token` monotonic int, incrementato ad ogni nuova acquisizione valida (non su renewal).
- Ogni mutation CAS filter include `fencing_token`.
- Fencing mismatch → `STALE_WRITER_REJECTED`.
- Lease theft prevention: attacker con lease_id valido ma `fencing_token` stale → reject.

## 33 · CAS and retries

- Automatic retries ≤ **3** (PM B2B2Q12 invariato)
- Ogni retry: nuova lettura state · rivalidazione Mark + Drain status + dedup + fencing + capacity (**7 rivalidazioni per retry** verbatim B2B2Q12)
- Ceiling raggiunto → `RETRY_LIMIT_REACHED` · return al caller
- CAS-only without lease = FORBIDDEN

## 34 · Receipt capacity (B2B2Q14 · `PM_RATIFIED_WITH_CONDITIONS`)

Baseline PM §17 (invariato): total 512 · ordinary 504 · reserved 8 · rolling eviction = **FORBIDDEN**.

**Classificazione Drain events (PM Message 170 B2B2Q14 verbatim)**:
- `START_DRAIN` = **ORDINARY**
- `COMPLETE_DRAIN` = **ORDINARY** (completion payload EMBEDDED nella stessa receipt · NO seconda slot)
- **Explicit** `CANCEL_DRAIN` = **ORDINARY**
- **Lazy Mark-expiration cancellation** durante comando Drain: cancellation/rejection result **FOLDED INTO the triggering ordinary event receipt** · **NO seconda receipt** `DRAIN_AUTO_CANCELLED_ON_MARK_EXPIRATION`
- **Lifecycle cancellation** (phase_end / expedition_terminal): **aggregate in lifecycle batch · usa 1 reserved receipt** (per batch, non per Drain · §24)

Ordinary capacity esaurita: `RECEIPT_CAP_REACHED` · no mutation. Reserved esaurita: `RESERVED_CAPACITY_EXHAUSTED`.

## 35 · Feature flags (B2B2Q13 · `PM_RATIFIED`)

**PM Message 170 B2B2Q13 verbatim (dedicated flag)**:

- **Nuovo flag**: `cdv_drain_transitions_enabled = default false`
- **Gate composito 6-conditions** (**NORMALIZZAZIONE PM Message 170 §13**: "quintuple-gate" DEPRECATO · usare `6-conditions gate`):

```
1. cdv_transient_state_enabled
2. AND cdv_class_transitions_enabled
3. AND cdv_drain_transitions_enabled
4. AND authenticated user.is_test_user
5. AND environment = localhost isolated
6. AND Mongo target = allowlisted database
```

- **Flag Drain OFF**: 0 DB calls · 0 audit events · 0 mutations (Drain path)
- Mark/Fragment già implementati **NON** disabilitati dal solo flag Drain (kill-switch surgical)

## 36 · Test-user boundary

- `test_user_verified=false` → `TEST_USER_BOUNDARY_VIOLATION` (fail-closed)
- `authenticated user.is_test_user=true` obbligatorio per attivazione Drain in localhost
- Non-test-user Drain attempt: 0 DB writes · 0 audit events · 0 state mutation (verifica analoga a `test_gating_02_non_test_user_fail_closed` RT2-B-2B-1 V1)

## 37 · Environment and allowlist

- MONGO_URI hostname = localhost / 127.0.0.1 / socket locale
- DB allowlist (invariato): `orbus_r16_rt2b_test` OR `orbus_r16_rt2b_it_<unique_run_id>`
- Provisioning idempotente (from parent RT2-B-P0 closed)
- Rejection DB non allowlisted → `DB_NOT_ALLOWLISTED`
- Shared-env rollout richiede separate PM sign-off

## 38 · Audit (B2B2Q15 · `PM_RATIFIED_WITH_CONDITIONS`)

**10 audit event ids verbatim PM Message 170 B2B2Q15**:

1. `cdv_drain_started`
2. `cdv_drain_start_rejected`
3. `cdv_drain_completed`
4. `cdv_drain_completion_rejected`
5. `cdv_drain_cancelled`
6. `cdv_drain_cancellation_rejected`
7. `cdv_drain_duplicate_completion`
8. `cdv_drain_fragment_batch_applied`
9. `cdv_drain_fragment_overflow_discarded`
10. `cdv_drain_transition_conflict`

Policy locale: INFO 100% · WARN 100% · ERROR 100%.

**Campi minimi audit (PM Message 170 B2B2Q15 verbatim)**:
`expedition_id · source_adventurer_id · target_id · drain_execution_id · event_id · Mark/application binding · result_code · cancellation_reason (se presente) · sequence · state_version_before/after · Fragment requested/applied/discarded · duration`

**Vietato**: doc Mongo completo · full payload · credenziali · RNG seed · reward payload · dati sensibili.

## 39 · Failure isolation

- Mark failure non contamina Drain state
- Drain failure non contamina Fragment count (atomic batch all-or-nothing)
- Store infra error → `STORE_INFRA_ERROR` result code + `cdv_state_transition_conflict` audit → return al caller · no mutation
- Nessun leak cross-expedition (state-store contract RT2-B-1A)
- Nessun leak cross-adventurer (source_adventurer_id server-authoritative)

## 40 · Security and abuse

Threat model coperto:
- **Client-forged drain_execution_id**: FORBIDDEN by B2B2Q01 (server-authoritative UUIDv4 completo)
- **Client-forged event_id**: dedup guard impedisce replay/tamper
- **Payload tamper on retry**: `payload_hash` mismatch → `EVENT_ID_PAYLOAD_MISMATCH`
- **Lease theft**: fencing_token check → `STALE_WRITER_REJECTED`
- **State version tampering**: CAS filter includes `state_version` → `STATE_VERSION_CONFLICT`
- **Foreign Drain complete**: source ownership check → `MARK_OWNERSHIP_MISMATCH`
- **Duplicate Fragment via retry**: dedup + `DrainDoc.runtime_status=RESOLVED` guard
- **Overflow reward extraction**: FORBIDDEN by cap policy + no reward payload
- **Cross-expedition Drain reference**: CAS filter `_id=expedition_id` isolates

## 41 · Test architecture

Il code gate futuro userà (invariato dalla RT2-B-2B-1 pipeline):
- **Pure tests** (state machine): 0 network, 0 DB
- **FakeStore**: in-memory, parametrized dispatcher
- **Mocked Mongo**: `_InMemoryMongoCollectionMock` CAS semantic simulator
- **Real Mongo localhost** (V1 subordinato): fixture `provisioned_unique_db`, DB pattern `orbus_r16_rt2b_it_<unique_run_id>`, teardown drop

Test matrix minima proposta = 32 casi (PM §19).

## 42 · Performance risks

- Completion payload EMBEDDED riduce ordinary consumption (1 receipt per completion vs 3 alternativi).
- Concurrent Drain start su spedizione ad alta densità: CAS retry ≤ 3 · p95 target ≤ 35 ms (in linea RT2-B-2B-1).
- Nessun background scheduler.
- BSON size stimato al cap 512 receipts con Drain payload embedded < 210 KiB (verifica precisa a V1 real-Mongo).

## 43 · Compatibility

- Public API changes = **0** (endpoint invariati, 275)
- Frontend = **0**
- `.env` = **0** (nuovo flag lato `feature_flags.py`, non env)
- Registry / Mongo provisioning = **0**
- Backward compatibility: `TrustedDrainReceipt.fixture_only_marker` sarà rimosso in RT2-B-2B-2-1; ogni test attuale che genera fixture sarà migrato a receipt reale.

## 44 · PM open questions (B2B2Q01–B2B2Q16) · POST-ADJUDICATION

**Tutte 16 domande adjudicate verbatim da PM Message 170. 0 agent auto-ratifications.**

| ID | Titolo | Verdict PM | Blocking |
|---|---|---|---|
| B2B2Q01 | Drain execution ID generation | Option A · UUIDv4 completo · `PM_RATIFIED_WITH_CONDITIONS` | YES |
| B2B2Q02 | START_DRAIN trusted event source | Option A (reuse) · `PM_RATIFIED` | NO |
| B2B2Q03 | Mark binding + refresh | Option A strict application_id · `PM_RATIFIED` | YES |
| B2B2Q04 | Mark validation at completion | Option A full 15-check · `PM_RATIFIED` | YES |
| B2B2Q05 | Fragment amount | Option A fixed=1 · `PM_RATIFIED_WITH_CONDITIONS` | YES |
| B2B2Q06 | Fragment outcome at cap | Option A completes+discarded · `PM_RATIFIED` | YES |
| B2B2Q07 | Completion-to-Fragment atomic contract | Option A · 15-field EMBEDDED receipt · `PM_RATIFIED_WITH_CONDITIONS` | YES |
| B2B2Q08 | Cancellation reason codes | Option A · NO extensions (8 verbatim) · `PM_RATIFIED` | NO |
| B2B2Q09 | Completion/rejection result codes | Option A + canonical set · `PM_RATIFIED_WITH_CONDITIONS` | NO |
| B2B2Q10 | Completion-vs-cancellation race | Option A first-committed-wins · `PM_RATIFIED` | YES |
| B2B2Q11 | Completion-vs-phase-end | Option A lifecycle batch + 1 reserved receipt aggregate · `PM_RATIFIED_WITH_CONDITIONS` | YES |
| B2B2Q12 | Lease and retry | Option A existing policy · `PM_RATIFIED` | NO |
| B2B2Q13 | Drain feature-flag composition | Option A dedicated flag · 6-conditions gate · `PM_RATIFIED` | YES |
| B2B2Q14 | Receipt classification + folding | Option A + folding (no separate `DRAIN_AUTO_CANCELLED_ON_MARK_EXPIRATION`) · `PM_RATIFIED_WITH_CONDITIONS` | NO |
| B2B2Q15 | Audit contract | Option A 10 event ids + campi minimi · `PM_RATIFIED_WITH_CONDITIONS` | NO |
| B2B2Q16 | First code-gate scope | Option A code gate `RT2-B-2B-2-1` + V1 subordinato · `PM_RATIFIED_WITH_CONDITIONS` | YES |

## 45 · First code-slice proposal (B2B2Q16 · `PM_RATIFIED_WITH_CONDITIONS`)

**PM Message 170 B2B2Q16 verbatim**:

- **Code gate**: `R18.6.RV3-IS2-B-P2B-RT2-B-2B-2-1 · DRAIN TRANSITION & COMPLETION-TO-FRAGMENT FOUNDATION`
- **Scope**: START/COMPLETE/CANCEL · rejection paths · server-generated UUIDv4 execution ID · Mark/application binding · completion-time Mark revalidation (15 checks) · completion-to-Fragment atomic batch · resource-segment opening · Drain receipts (ORDINARY + reserved lifecycle aggregate) · lease/fencing/CAS · ordering/races · dedup · dedicated default-OFF flag · test-user fail-closed · audit mappings 10 events · pure/FakeStore/mocked-Mongo tests (32+ casi)
- **V1 subordinato**: `RT2-B-2B-2-1-V1 · REAL-MONGO DRAIN VERIFICATION` (functional matrix · winner-only concurrency · completion-to-Fragment atomicity · duplicate completion · cancellation races · receipt capacity · BSON size · performance · allowlist · cleanup)
- **V1 NON ottiene baseline chain increment autonomo** né closure autonoma
- **Escluso**: damage · healing · XP · loot · guild XP · item effects · proc · cooldown engine · focus bonus mutation · public API · frontend · shared env · human testers

## 46 · Explicit STOP

**STRICT STOP.** Draft PATCHATO integrando i 16 verdict PM Message 170 verbatim (0 auto-ratifications agent). Il P0 attende formal closure dispatch. Nessun code change, nessuna scrittura Mongo, nessuna attivazione flag. Baseline chain **15/15 INVARIATA** durante il patch.

**Fail-stop P0 attivati** (PM §25, 10 items): **0/10**.

Attesa formal closure dispatch per generazione 3 artifact (final_closure_report MD/JSON + closure_manifest JSON) + PRD append + baseline chain increment 15→16/16.
