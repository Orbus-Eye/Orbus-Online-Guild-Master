# R18.6.RV3-IS2-B-P2B-RT2-B-2B-2-P0 · DRAIN TRANSITION FOUNDATION READINESS & COMPLETION-TO-FRAGMENT CONTRACT

**Gate**: `R18.6.RV3-IS2-B-P2B-RT2-B-2B-2-P0`
**Canonical name**: DRAIN TRANSITION FOUNDATION READINESS & COMPLETION-TO-FRAGMENT CONTRACT
**Regime**: **DOCUMENTAL ONLY · READ-ONLY DISCOVERY · NO CODE · NO APPLY · NO DB WRITES · NO FEATURE ACTIVATION**
**PM authority**: Message 168 (dispatch orchestrator)
**Draft date (UTC)**: 2026-02
**Parent gate closed**: `RT2-B-2B-1 · MARK & RESOURCE STATE TRANSITION FOUNDATION` (CLOSED · PM-LOCKED · V1 INCORPORATED)
**Baseline chain**: **15/15 (INVARIATA durante questo draft · +1 riservato a formal closure P0)**

---

## 1 · Executive summary

Il presente P0 disegna il contratto deterministico per **Drain** — startup, completion, cancellation — e la sua integrazione atomica con la primitiva Fragment già implementata in RT2-B-2B-1. Regime documentale: nessun code change, nessuna scrittura Mongo, nessuna attivazione flag. Il draft estrae 16 domande PM (**B2B2Q01…B2B2Q16**) senza auto-ratifica, coerente PM Message 168 §21.

Portata (PM §4):
- `START_DRAIN` (`NOT_STARTED → STARTED`) · `COMPLETE_DRAIN` (`STARTED → COMPLETED`) · `CANCEL_DRAIN` (`STARTED → CANCELLED`)
- **Completion-to-Fragment atomic batch** (unico event batch: drain completion + completion receipt + Fragment gain decision + overflow discard + eventual segment opening + event receipt + `state_version` +1)
- Invarianti bloccanti (PM §4 verbatim): Drain completato senza decisione Fragment = IMPOSSIBILE · Fragment assegnato senza Drain completato = IMPOSSIBILE · doppia assegnazione sul retry = IMPOSSIBILE · mutation parziale = IMPOSSIBILE
- Kill-switch separato: nuovo `cdv_drain_transitions_enabled` (default OFF), quintuple-gate composito
- Cancellation reason codes: riuso verbatim degli 8 codici già ratificati in RT2-B-2B-P0 B2BQ05

Fuori portata (PM §5): damage · healing · XP · loot · guild XP · success probability · combat resolution · item/affix/proc/cooldown · Legendary · PvP · public API · frontend · human tester activation. Il risultato del Drain resta transizione interna di stato.

## 2 · Scope

**IN**: transizioni pure `START_DRAIN`, `COMPLETE_DRAIN`, `CANCEL_DRAIN`; atomic completion-to-Fragment batch; kill-switch dedicato; Mark binding; execution identity server-authoritative; receipt policy 512/504+8 invariata; lease+fencing+CAS 8-step; audit contract 10 event ids; test contract 32+ casi. Precondizioni PM §4 verbatim mantenute (expedition active · single phase active · source valid · target valid · own active Mark · mark_id matches · application_id matches · Mark not expired · event not previously processed · receipt capacity available · valid lease+fencing · expected `state_version` matches).

**OUT**: Drain runtime executor separato (RT2-C effect execution) · reward payload · gameplay effect · public API/OpenAPI · frontend/UX · shared-env rollout · human tester activation · flag activation in production · Registry/Mongo provisioning · Registry migration.

## 3 · Governance

- Regime R18.6 · PM dispatch Message 168 vincolante · Regime documentale (nessun code change).
- Baseline chain **15/15 INVARIATA** durante il P0 (increment autorizzato solo su formal closure P0 = 16/16).
- Sealed integrity **36/36 byte-identical**: `pytest tests/backend_r18_4_sealed_integrity_test.py` → 6 PASS.
- `effect_engine` **396/396** serial + **396/396** xdist (config `-n 2 --dist loadscope`) · 1 warning benign (starlette `PendingDeprecationWarning`).
- `lore_meta.py` invariant SHA `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` · **INVARIANT**.
- OpenAPI paths **275** · new routes = 0 · frontend changes = 0 · `.env` changes = 0 · feature flag activation = 0.
- Fail-stop P0 attivati (§25 verbatim): **NONE** (nessun blocker documentale rilevato).

## 4 · Source chain

Le fonti canoniche di questo P0 sono:
- `/app/memory/r18_6_rv3_is2_b_p2b_rt2_b_2b_1_final_closure_report.md` (SHA `5de28c0883fa4acfa6bd512108d7ec23b2bb5f6ffde944017a2b4715e752d249`)
- `/app/memory/r18_6_rv3_is2_b_p2b_rt2_b_2b_1_closure_manifest.json` (SHA `8c47b18bada7f255219f4afcca2dc0e0aea9e745833a52f0207815a0c346d2a5`)
- `/app/memory/r18_6_rv3_is2_b_p2b_rt2_b_2b_1_implementation_report.md/json`
- `/app/memory/r18_6_rv3_is2_b_p2b_rt2_b_2b_1_real_mongo_verification_addendum.md/json`
- `/app/memory/r18_6_rv3_is2_b_p2b_rt2_b_2b_p0_final_closure_report.md/json` (Q&A parent P0 con 14 verdetti PM)
- Codice runtime: `app/stats/runtime/transitions/*` + `app/stats/runtime/wiring/coordinator.py` + `app/stats/runtime/state_store/*` (foundation immutabile durante il draft).

## 5 · Current Mark foundation

Evidence dal codice attualmente CLOSED (RT2-B-2B-1):

- `MarkDoc` (`app/stats/runtime/state_store/models.py`): `mark_id`, `application_id`, `source_adventurer_id`, `target_id`, `created_at`, `expires_at` (=`created_at + 10s`), `ritual_close_used`, `mark_version`.
- Invarianti verbatim:
  - `active_marks ≤ 5 per source_adventurer_id` (`MARK_CAP_PER_SOURCE=5` in `state_machine.py`)
  - `one Mark per (source, target)` pair
  - duration ≤ 10s applicativi
  - lazy expiration authoritative server time
  - opportunistic cleanup all'access path
  - NO auto-eviction
- Event types Mark (`transitions/models.ClassEventType`): `APPLY_MARK`, `REFRESH_MARK`, `LAZY_MARK_EXPIRATION`, `OPPORTUNISTIC_MARK_CLEANUP`.
- Ownership check: source_adventurer_id must equal caller identity; foreign-Mark drain = FORBIDDEN. Verificato da `test_item_08_multi_cdv_ownership_isolation`.

## 6 · Current Fragment foundation

- `AdventurerClassState.fragment_count: int ≤ 5` (cap enforced in `state_machine.py:FRAGMENT_CAP=5`).
- Event types: `GAIN_FRAGMENT`, `SPEND_FRAGMENT`, `RESET_FRAGMENTS`, `DISCARD_FRAGMENT_OVERFLOW`.
- `GAIN_FRAGMENT` valido richiede **accepted Drain completion receipt** (`TrustedDrainReceipt` fixture-only in RT2-B-2B-1; in RT2-B-2B-2 la fixture sarà rimossa e sostituita da receipt generata dal Drain runtime reale).
- Overflow rule (verbatim RT2-B-2B-1 §): overflow oltre cap = discarded diagnostic-only · overflow reward = FORBIDDEN · partial credit = FORBIDDEN.
- Fragment produce `DISCARD_FRAGMENT_OVERFLOW` receipt (ORDINARY) per audit.

## 7 · Current coordinator entry point

- `ExpeditionRuntimeCoordinator.dispatch_class_state_event(event: ClassStateEvent, trusted_context: dict) -> DispatchOutcome` (`wiring/coordinator.py:242`).
- Trust context minimo: `feature_enabled`, `test_user_verified`, `db_allowlisted`, `phase_ended`, `test_user_id`.
- Audit emit interno via `_class_event_audit_id(event_type, result_code)` → 11 canonical ids (`transitions/state_machine.py` verbatim mapping) + `cdv_state_transition_conflict` rejection routing.
- Il Drain **riuserà** questo entry point (nessun nuovo endpoint pubblico) aggiungendo nuovi `ClassEventType` values (`START_DRAIN`, `COMPLETE_DRAIN`, `CANCEL_DRAIN`).

## 8 · Current state-store contract

- Interfaccia `ExpeditionRuntimeStateStore` (protocol) + implementazioni: `FakeExpeditionRuntimeStateStore` (in-memory unit tests) + `MongoExpeditionRuntimeStateStore` (real Mongo integration).
- Metodi: `create_state`, `get_state`, `reserve_writer`, `renew_writer_lease`, `release_writer`, `compare_and_update`, `apply_event_once`, `expire_state`, `delete_state`, `get_version`, `health_check`.
- CAS: `find_one_and_update` con filter `{_id, state_version, fencing_token, [dedup guards]}` · update `$inc: state_version=+1 / last_event_sequence=+1`, `$set:` mutation fields, `$push: processed_event_keys`.
- Receipt policy: `MAX_PROCESSED_EVENTS = 512` (hard cap store-side); enforcement categorizzazione ORDINARY(504)/RESERVED(8) applicativa in `transitions/state_machine.py`.

## 9 · Drain domain model

Struttura `DrainDoc` (già dormant in `state_store/models.py:73`) rifinita per RT2-B-2B-2:

Campi obbligatori (PM §9 binding contract):
- `drain_execution_id: str` (server-authoritative · vedi B2B2Q01)
- `source_adventurer_id: str`
- `target_id: str`
- `mark_id: str` (RT2-B-2B-2 add: attualmente `DrainDoc` non memorizza `mark_id`, solo `required_mark_application_id`; l'aggiunta è documentale per il code gate futuro)
- `required_mark_application_id: str`
- `started_at: str` (ISO UTC)
- `completed_at: Optional[str]`
- `cancelled_at: Optional[str]`
- `runtime_status: DrainStatus` (`IN_PROGRESS` | `RESOLVED` | `CANCELLED` | `EXPIRED`)
- `cancellation_reason: Optional[str]` (uno degli 8 canonici · vedi §18)
- `drain_version: int` (monotonic per aggregato, initial=1)

Rimozione futura: campo `reward_resolved: bool` presente ma inutilizzato (drain non produce reward direttamente). Sarà valutata rimozione o rinominazione (`fragment_gain_applied: bool`) al code gate.

Persistenza: `AdventurerClassState.active_drain_executions: Tuple[DrainDoc, ...]` (già presente). Un solo Drain simultaneo per `(source, target)` (single-in-flight rule).

## 10 · Drain execution identity

**Vincolo PM §8**: `drain_execution_id = server-authoritative`. Client-provided authoritative execution ID = **FORBIDDEN**. Il client/chiamante non trusted NON può controllare identity, ownership, application binding, event sequence, fencing token, Fragment result.

Draft proposto (subject to PM adjudication · **B2B2Q01**):
- **Opzione A** (agent recommendation): generato lato server all'accettazione di `START_DRAIN`, formato `drn-<uuid4[:16]>`, ritornato al chiamante nel `TransitionResult`. Client subsequent commands (`COMPLETE_DRAIN`, `CANCEL_DRAIN`) devono referenziare l'ID emesso.
- **Opzione B**: derivato deterministicamente da comando interno trusted (`sha256(expedition_id · source · target · mark_id · application_id · phase_id · nonce_server)[0:20]`) — deterministic replay-safe.

Il P0 raccomanda A per semplicità dedup + audit; PM adjudichi.

## 11 · Drain ownership

- `source_adventurer_id` di ogni comando Drain deve coincidere con l'identità del caller autenticato (già gestita dal coordinator via `trusted_context.test_user_id`).
- Foreign-Drain (source diverso dal caller) = FORBIDDEN → `OWNERSHIP_INVALID`.
- Un Drain non può essere completato/annullato da un `source_adventurer_id` diverso da quello che l'ha avviato. Enforcement server-side nel dispatcher (analogo a Mark ownership).

## 12 · Mark binding

Regola verbatim PM §9:
- `START_DRAIN`: richiede own active Mark su `(source, target)` non scaduto; salva `mark_id` + `required_mark_application_id`.
- `COMPLETE_DRAIN`: rivalidazione full — same `source_adventurer_id`, same `target_id`, same `mark_id`, same `application_id`; Mark ancora attivo (non expired) al momento della completion.
- **Refresh Mark** (stesso `mark_id`, `application_id` invariato, `expires_at` esteso): mantiene valido il Drain.
- **Nuova applicazione Mark dopo scadenza** (nuovo `application_id`): il vecchio Drain **NON PUÒ COMPLETARE** — rejection `MARK_APPLICATION_CHANGED`.

Effetti collaterali: il completion **NON consuma** il Mark; il Mark resta attivo fino a expiration/cleanup.

## 13 · START_DRAIN state machine

Transizione: `NOT_STARTED → STARTED` (creazione `DrainDoc` con `runtime_status=IN_PROGRESS`).

Sequenza atomica (event batch unico, 8-step):
1. lease acquire (short request-scoped, TTL 30s, fencing bump se new)
2. fencing token validation
3. read `state_version` expected
4. validate: expedition active · single phase active · caller identity · target valid · own active Mark on `(source, target)` · Mark not expired · no existing `DrainDoc` in progress per `(source, target)`
5. apply mutation: append `DrainDoc(runtime_status=IN_PROGRESS, drain_execution_id=<server>, mark_id, application_id, started_at)`
6. `state_version += 1` · `last_event_sequence += 1`
7. persist `START_DRAIN` receipt (ORDINARY category · vedi §34)
8. lease release/expire

## 14 · START_DRAIN validation

Precondizioni verbatim PM §4:
- expedition active (`runtime_status = ACTIVE`)
- single phase active (`phase_id` non terminale)
- source valid (esiste `AdventurerClassState`)
- target valid (target_id non null · non self)
- own active Mark su `(source, target)` (Mark non scaduto)
- `mark_id` matches Mark trovato
- `application_id` matches Mark trovato
- event not previously processed (dedup guard su `event_id`)
- receipt capacity available (ordinary slot free · vedi §34)
- valid lease + fencing token
- `expected_state_version` matches

Fallimenti (result codes): `MARK_NOT_FOUND`, `MARK_EXPIRED`, `MARK_OWNERSHIP_MISMATCH`, `TARGET_INVALID`, `SOURCE_INVALID`, `PHASE_ENDED`, `EVENT_POST_TERMINAL_REJECTED`, `RECEIPT_CAP_REACHED`, `STATE_VERSION_CONFLICT`, `STALE_WRITER_REJECTED`, `DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR` (nuovo).

## 15 · COMPLETE_DRAIN state machine

Transizione: `STARTED → COMPLETED` con **completion-to-Fragment atomic batch** (§26).

Sequenza atomica unica (single writer):
1. lease acquire · fencing validate · read `state_version`
2. rivalidate Mark binding (§12): same `mark_id` + `application_id` + Mark still active + not expired
3. validate Drain state: `runtime_status = IN_PROGRESS`, non `CANCELLED`, non `COMPLETED`
4. validate phase state: not phase_ended, not expedition terminal
5. compute Fragment outcome (§27–§28): amount from PM verdict B2B2Q05 · check cap → apply o overflow_discarded
6. compute segment opening (§29): if `fragment_count 0 → positive`, open segment
7. apply mutations atomically: `DrainDoc.runtime_status=RESOLVED`, `DrainDoc.completed_at`, `fragment_count += granted`, eventual `resource_segment_id`, `overflow_discarded` counter, completion receipt
8. `state_version += 1` (exactly once) · persist COMPLETE_DRAIN receipt (ORDINARY) · eventuale DISCARD_FRAGMENT_OVERFLOW receipt (ORDINARY se emessa) · eventuale OPEN_RESOURCE_SEGMENT (ORDINARY)

Nota: il P0 raccomanda che overflow discard e segment open siano REGISTRATI dentro la completion receipt (single receipt), NON come receipts separate, per non frammentare la ordinary capacity. Alternativa: receipt separate distinte per audit. → **B2B2Q14**.

## 16 · COMPLETE_DRAIN validation

Rivalidazioni verbatim PM §4:
- same source_adventurer_id (caller identity match)
- same target_id
- same mark_id
- same application_id
- Mark still active al momento della completion (server clock)
- Mark not expired (server clock)
- Drain execution not cancelled
- Drain execution not already completed (idempotency dedup)
- Expedition not terminal
- Phase still active
- Receipt capacity available (§34)
- Valid lease + fencing + state_version

Fallimenti canonici (rejection codes): `MARK_EXPIRED`, `MARK_OWNERSHIP_MISMATCH`, `MARK_APPLICATION_CHANGED`, `DRAIN_ALREADY_COMPLETED`, `DRAIN_CANCELLED`, `PHASE_ENDED`, `EXPEDITION_TERMINAL`, `EVENT_ID_PAYLOAD_MISMATCH`, `RECEIPT_CAP_REACHED`, `STATE_VERSION_CONFLICT`.

## 17 · CANCEL_DRAIN state machine

Transizione: `STARTED → CANCELLED`. Terminale per lo stesso `drain_execution_id`.

Trigger:
- **Explicit** (client/server): reason_code = `EXPLICIT_SERVER_CANCEL`
- **Automatic on phase end**: reason_code = `PHASE_ENDED`
- **Automatic on expedition terminal**: reason_code = `EXPEDITION_TERMINAL`
- **Cascade on Mark event**: reason_code = `MARK_EXPIRED` | `MARK_OWNERSHIP_MISMATCH` | `MARK_APPLICATION_CHANGED` | `TARGET_INVALID` | `SOURCE_INVALID`

Effetti: `DrainDoc.runtime_status = CANCELLED`, `cancelled_at`, `cancellation_reason` valorizzato con uno degli 8 codici. Nuovo tentativo su stesso `(source, target)` richiede **nuovo `drain_execution_id`** + revalidation completa.

## 18 · Cancellation reason codes

**Riuso verbatim** dagli 8 codici PM RT2-B-2B-P0 B2BQ05 (già presenti in `transitions/models.ReasonCode`):

1. `MARK_EXPIRED`
2. `MARK_OWNERSHIP_MISMATCH`
3. `MARK_APPLICATION_CHANGED`
4. `TARGET_INVALID`
5. `SOURCE_INVALID`
6. `PHASE_ENDED`
7. `EXPEDITION_TERMINAL`
8. `EXPLICIT_SERVER_CANCEL`

**Divieti**: non rinominare, non creare alias. Estensioni consentite SOLO se supportate da caso reale scoperto in discovery + non semanticamente sovrapponibili + presentate come domanda PM (**B2B2Q08**) + NON auto-ratificate.

Baseline agent recommendation per B2B2Q08: **NO extensions**. Gli 8 codici coprono l'intero space discovered.

## 19 · Completion result codes

Distinguere da cancellation reason codes (PM §7). Set proposto (subject to **B2B2Q09**):

- **Success**: `SUCCESS` (già esistente)
- **Rejection idempotency**: `DEDUPLICATED_NO_OP`, `DRAIN_ALREADY_COMPLETED`, `EVENT_ID_PAYLOAD_MISMATCH`
- **Rejection validation**: `MARK_EXPIRED`, `MARK_OWNERSHIP_MISMATCH`, `MARK_APPLICATION_CHANGED`, `TARGET_INVALID`, `SOURCE_INVALID`, `DRAIN_CANCELLED`, `PHASE_ENDED`, `EVENT_POST_TERMINAL_REJECTED`
- **Rejection infra**: `RECEIPT_CAP_REACHED`, `STATE_VERSION_CONFLICT`, `STALE_WRITER_REJECTED`, `CAS_WITHOUT_VALID_LEASE`, `RETRY_CEILING_EXCEEDED`, `STATE_DOCUMENT_SIZE_BUDGET_EXCEEDED`
- **Fragment interaction (non-blocking)**: `SUCCESS` con `overflow_discarded > 0` (informational · non un rejection code separato)

Nuovi codici proposti (subject PM): `DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR` (start rejection), `DRAIN_ALREADY_COMPLETED` (complete rejection), `DRAIN_CANCELLED` (complete rejection).

## 20 · Drain idempotency

Regole verbatim PM §15:
- Stesso `event_id + payload_hash` uguale → return prior result · no new mutation · **no second Fragment grant**
- Stesso `event_id + payload_hash diverso` → `EVENT_ID_PAYLOAD_MISMATCH` reject
- Stesso `drain_execution_id` completato con `event_id` diverso → `DRAIN_ALREADY_COMPLETED` · no mutation

Distinguere: replay stesso evento (dedup no-op) · completion duplicata con event diverso (rejection ALREADY_COMPLETED) · payload mismatch · stale state version.

Enforcement: dedup guard via `apply_event_once` sui receipts (già in `state_store` interface) + guard applicativo su `DrainDoc.runtime_status` == `RESOLVED`.

## 21 · Event ordering

Ordering totale per `expedition_id` (invariato da RT2-B-2B-1):
- `last_event_sequence` incrementato server-authoritative +1 per ogni event batch accepted
- CAS filter garantisce single writer per `state_version`
- Concurrent starts su stesso `(source, target)` → 1 SUCCESS + 1 `DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR`
- Concurrent completions stesso `drain_execution_id` → 1 SUCCESS + 1 `DRAIN_ALREADY_COMPLETED`
- Concurrent starts diversi drain executions (diverso target) → possono succedere entrambi (nessun conflitto logico oltre CAS conflict transiente)

## 22 · Cancellation races

Scenari e precedenza (baseline PM §14):

- **cancel vs complete**: se completion committed first → cancellation returns `ALREADY_COMPLETED` (no mutation). Se cancellation committed first → completion returns `DRAIN_CANCELLED`.
- **cancel vs cancel duplicata**: seconda cancel su stesso execution → `DRAIN_ALREADY_CANCELLED` (dedup no-op semantico) → **B2B2Q10**
- **cancel automatic (phase_end) vs cancel explicit**: se entrambi convergono, prevale il primo committed (single writer). Il secondo → dedup no-op.

## 23 · Expiration races

- **complete vs Mark expiration**: se Mark expires nel window tra start e complete, la revalidation al complete → `MARK_EXPIRED`. Il Drain viene AUTO-CANCELLATO con reason `MARK_EXPIRED` durante la stessa mutation? → **B2B2Q10** (opt: cancel-then-fail vs fail-without-cancel).
  - Agent recommendation: **cancel-then-fail** in singolo event batch (cancel = ordinary receipt, poi rejection) mantenendo l'atomicità.
- **complete vs Mark refresh**: refresh mantiene `application_id` invariato → Drain resta valido, no impact.
- **complete vs new Mark application** (dopo expiration): nuovo `application_id` ≠ salvato → `MARK_APPLICATION_CHANGED` + Drain cancelled con stesso reason.

## 24 · Terminalization races

- **complete vs phase_end**: baseline PM §14 → **terminalization/phase_end committed first → later completion REJECTED** (`PHASE_ENDED` o `EVENT_POST_TERMINAL_REJECTED`). Any in-flight Drain automaticamente CANCELLED (bulk cancellation batch usa RESERVED receipts).
- **complete vs expedition terminal**: analogo, reason = `EXPEDITION_TERMINAL`.
- **cancel vs terminalization**: cancel committed first → success. Terminalization first → cancel returns `EVENT_POST_TERMINAL_REJECTED` (o dedup no-op se il Drain era già stato bulk-cancelled).

## 25 · Completion receipt

Contenuto obbligatorio (PM §16 verbatim):

```
completion_receipt:
  drain_execution_id: str
  completion_event_id: str
  source_adventurer_id: str
  target_id: str
  mark_id: str
  application_id: str
  result_code: str                        # SUCCESS | rejection code
  mark_valid_at_completion: bool
  fragment_gain_requested: int            # amount richiesto (post PM B2B2Q05)
  fragment_gain_applied: int              # 0..5 (post cap check)
  fragment_overflow_discarded: int
  resource_segment_id: Optional[str]      # populated se segment opening avvenuta
  assigned_event_sequence: int
  state_version_after: int
  processed_at: str                        # ISO UTC
```

**Esclusioni PM §16**: damage · healing · XP · loot · item proc · combat result. La receipt è sufficiente per autorizzare la primitive `GAIN_FRAGMENT` (già implementata in RT2-B-2B-1) **senza fixture artificiale** nel futuro code gate — `TrustedDrainReceipt.fixture_only_marker` verrà rimosso.

## 26 · Completion-to-Fragment batch

Single atomic event batch (contratto verbatim PM §4):
- Drain completion status (`DrainDoc.runtime_status = RESOLVED`)
- Completion receipt (contenuto §25)
- Fragment gain result (`fragment_count += applied`)
- Overflow discard result (`overflow_discarded` counter incremented if amount > cap)
- Resource-segment opening quando required (`fragment_count 0 → positive`)
- Event receipt (dedup slot)
- `state_version` +1 exactly once

Invarianti verbatim PM §4:
- Drain completato senza decisione Fragment = IMPOSSIBILE (fragment decision è parte del batch)
- Fragment assegnato senza Drain completato = IMPOSSIBILE (gain path richiede completion receipt)
- Doppia assegnazione sul retry = IMPOSSIBILE (dedup via `event_id` + `drain_execution_id` status)
- Mutation parziale = IMPOSSIBILE (single CAS atomic apply)

## 27 · Fragment amount policy

**NOT AUTO-RATIFIED** → **B2B2Q05**. Quantità di Frammenti prodotta per accepted completion.

Opzioni presentate a PM:
- Opzione A: `1 fragment per completion` (baseline conservativa)
- Opzione B: variable amount (1..N) da payload trusted server-derived
- Opzione C: fixed constant configurabile via feature flag param (fuori scope P0)

Agent recommendation: **Opzione A (1 fragment per completion)** per semplicità determinismo + test contract + coerenza con RT1 baseline. PM adjudichi.

## 28 · Fragment cap and overflow

Vincoli verbatim PM §10:
- Fragment source = accepted Drain completion only (invariato)
- Fragment cap = 5 · overflow = discarded · overflow reward = FORBIDDEN
- partial completion grant = FORBIDDEN (o completa o rejection · no partial)

**Behavior when count == 5 già** (verbatim PM §10):
- Drain completion **may still complete** (NON annullata perché risorsa al cap)
- `fragment_granted = 0`
- `overflow_discarded += requested_amount`
- Receipt records `fragment_gain_applied=0, fragment_overflow_discarded=<requested>`
- Audit event `cdv_drain_fragment_overflow_discarded` emesso
- `SUCCESS` result code (Drain OK) con informativo overflow

→ **B2B2Q06** conferma questa policy.

## 29 · Resource segment interaction

Regole verbatim PM §11:
- Quando completion produce `fragment_count 0 → positive` (transizione strict): **APRE** resource segment nel medesimo event batch. Nuovo `resource_segment_id` = `sg-<uuid[:16]>`.
- Se segmento già attivo (`AdventurerClassState.resource_segment_id != None`): preserve current `resource_segment_id`.
- Il Drain **NON deve**: chiudere direttamente il segmento (auto-close resta in resource_segment lifecycle events), consumare Frammenti, incrementare `focus_bonus_usage`.

Il completion receipt include `resource_segment_id` solo se un segmento è associato all'adventurer post-mutation (open o preserved).

## 30 · Focus bonus boundary

Regola verbatim PM §12:
- `focus_bonus_usage` interaction with Drain = **DEFERRED**
- Nel gate Drain: Drain completion changes `focus_bonus_usage` = **FORBIDDEN**
- Preserva invariante: `focus_bonus_usage ≤ 2 per resource_segment` (invariato da RT2-B-2B-1)

Incremento + effetto concreto del focus bonus appartengono a RT2-C (effect execution) OR RT2-E (item hooks) → verdict separato futuro.

## 31 · Lease strategy

Regole verbatim PM §13:
- Lease TTL 30s (invariato) · short request-scoped
- Un event batch atomico Drain = 1 lease acquire → validate → apply → release/expire
- CAS-only without lease = **FORBIDDEN**
- Background lease renewer = **FORBIDDEN**

Il code gate futuro riutilizzerà `reserve_writer` + `release_writer` già implementati nello state store.

## 32 · Fencing

- `fencing_token` monotonic int, incrementato ad ogni **nuova acquisizione valida** (non su renewal).
- Ogni mutation CAS filter include `fencing_token`.
- Fencing mismatch → `STALE_WRITER_REJECTED`.
- Lease theft prevention: attacker con lease_id valido ma `fencing_token` stale → reject.

Nuovo scenario Drain: `START_DRAIN` acquire nuovo fencing token; `COMPLETE_DRAIN` submitted con fencing stale rispetto a un intervening writer → `STALE_WRITER_REJECTED`. Il caller deve fare re-acquire + retry.

## 33 · CAS and retries

- Automatic retries ≤ **3** (invariato da RT2-B-2B-1).
- Ogni retry: nuova lettura state · rivalidazione Marchio + Drain status + dedup check · nuova fencing verify.
- Ceiling raggiunto → `RETRY_CEILING_EXCEEDED` (return al caller · no further attempts).
- CAS-only without lease = FORBIDDEN.

Contratto atomic 8-step (§15) applicato ad ogni retry singolarmente.

## 34 · Receipt capacity

Baseline PM §17 (invariato):
- Total capacity 512 = 504 ordinary + 8 reserved
- Rolling eviction = **FORBIDDEN**

Classificazione Drain events proposta:
- `START_DRAIN` = **ORDINARY**
- `COMPLETE_DRAIN` = **ORDINARY**
- `CANCEL_DRAIN` (explicit) = **ORDINARY**
- `CANCEL_DRAIN` (automatic on phase_end / expedition_terminal) = **RESERVED** (parte del lifecycle event batch)
- `DRAIN_AUTO_CANCELLED_ON_MARK_EXPIRATION` = **ORDINARY** (agent recommendation) o **RESERVED** (alt) → **B2B2Q14**

Ordinary capacity esaurita durante Drain: `RECEIPT_CAP_REACHED` · no mutation. Reserved esaurita: `RESERVED_CAPACITY_EXHAUSTED` (evento eccezionale).

## 35 · Feature flags

Nuovo flag separato (PM §6): `cdv_drain_transitions_enabled` (default `false`).

Composizione quintuple-gate futura (verbatim):
```
cdv_transient_state_enabled = true
AND cdv_class_transitions_enabled = true
AND cdv_drain_transitions_enabled = true
AND authenticated user.is_test_user = true
AND environment = localhost isolated
AND Mongo target = allowlisted
```

Flag OFF (default): Drain DB calls = 0 · Drain audit events = 0 · Drain state mutations = 0 · Mark/Fragment gate behavior INVARIATO.

Motivazione: rischi aggiuntivi rispetto a Mark/Fragment (doppia completion, race con expiration, cancellation, Fragment grant atomico) giustificano kill-switch dedicato.

## 36 · Test-user boundary

- `test_user_verified=false` → `TEST_USER_BOUNDARY_VIOLATION` (fail-closed).
- `authenticated user.is_test_user=true` obbligatorio per attivazione Drain in localhost.
- Non-test-user Drain attempt: 0 DB writes · 0 audit events · 0 state mutation (verifica: analoga a `test_gating_02_non_test_user_fail_closed` in RT2-B-2B-1 V1).

## 37 · Environment and allowlist

- MONGO_URI hostname = localhost / 127.0.0.1 / socket locale.
- DB allowlist (invariato): `orbus_r16_rt2b_test` OR `orbus_r16_rt2b_it_<unique_run_id>`.
- Provisioning idempotente (from parent `RT2-B-P0` closed).
- Rejection di DB non allowlisted → `DB_NOT_ALLOWLISTED` (fail-closed).
- Shared-env rollout richiede **separate PM sign-off** (invariato).

## 38 · Audit

Definire almeno **10 audit events Drain** (PM §18 verbatim):

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

Policy sampling locale: INFO 100% · WARN 100% · ERROR 100%.

**Non registrare**: doc Mongo completo · payload completo · credenziali · RNG seed · reward payload · dati sensibili.

Whitelist audit fields aggiornata (extension in `wiring/audit.py`): campi già presenti in RT2-B-2B-1 (`expedition_id, source_adventurer_id, target_id, event_id, event_type, event_sequence, result_code, state_version_before, state_version_after, duration_ms, reason_code, mark_id, mark_application_id, resource_segment_id, fragment_count_after, overflow_discarded, retry_attempts, dedup_reference`) + nuovo `drain_execution_id`, `drain_status`, `fragment_gain_requested`, `fragment_gain_applied`.

## 39 · Failure isolation

- Mark failure non deve contaminare Drain state (test isolation).
- Drain failure non deve contaminare Fragment count (atomic batch garantisce all-or-nothing).
- Store infra error → `STORE_INFRA_ERROR` result code + `cdv_state_transition_conflict` audit → return al caller · no mutation.
- Nessun leak cross-expedition (verificato da state-store contract di RT2-B-1A).
- Nessun leak cross-adventurer (source_adventurer_id server-authoritative).

## 40 · Security and abuse

Threat model coperto:
- **Client-forged drain_execution_id**: FORBIDDEN by B2B2Q01 (server-authoritative).
- **Client-forged event_id**: dedup guard (`processed_event_keys.event_id`) impedisce replay/tamper.
- **Payload tamper on retry**: `payload_hash` mismatch → `EVENT_ID_PAYLOAD_MISMATCH`.
- **Lease theft**: fencing_token check → `STALE_WRITER_REJECTED`.
- **State version tampering**: CAS filter includes `state_version` → `STATE_VERSION_CONFLICT`.
- **Foreign Drain complete**: source ownership check → `OWNERSHIP_INVALID`.
- **Duplicate Fragment via retry**: dedup + `DrainDoc.runtime_status=RESOLVED` guard.
- **Overflow reward extraction**: FORBIDDEN by cap policy + no reward payload in receipt.
- **Cross-expedition Drain reference**: CAS filter `_id=expedition_id` isolates.

## 41 · Test architecture

Il code gate futuro userà (invariato dalla RT2-B-2B-1 pipeline):
- **Pure tests** (state machine): 0 network, 0 DB.
- **FakeStore** (`FakeExpeditionRuntimeStateStore`): in-memory, parametrized dispatcher.
- **Mocked Mongo** (`_InMemoryMongoCollectionMock`): CAS semantic simulator.
- **Real Mongo localhost** (`integration_real_mongo/`): fixture `provisioned_unique_db`, DB pattern `orbus_r16_rt2b_it_<unique_run_id>`, teardown drop.

Test matrix minima proposta = 32 casi (PM §19). Vedi §44 per enumerazione.

## 42 · Performance risks

- Completion-to-Fragment batch dimensione: la receipt include fragment fields addizionali (baseline stima < 400 byte per receipt). Con `RECEIPT_CAP_TOTAL=512`, doc size stimato peggior caso ≈ 205 000 byte < 262 144 (256 KiB) — verifica precisa richiesta nel code gate V1 real-Mongo.
- Concurrent Drain start su spedizione ad alta densità: CAS retry ≤ 3 · p95 attesa ≤ 35 ms (target RT2-B-2B-1).
- Nessun background scheduler introdotto.

## 43 · Compatibility

- Public API changes = **0** (endpoint invariati).
- OpenAPI paths = **275** (invariato).
- Frontend = **0** (no gameplay path exposed).
- `.env` = **0** (nuovo flag registrato lato `feature_flags.py`, non env).
- Registry / Mongo provisioning = **0** (state doc schema invariato struttura; nuovo `DrainDoc` è embedded in `AdventurerClassState`, già presente).
- Backward compatibility: `TrustedDrainReceipt` fixture-only marker sarà rimosso; ogni test attuale che genera receipt fixture-only sarà migrato a receipt generata dal Drain runtime.

## 44 · PM open questions (B2B2Q01–B2B2Q16)

Elenco sintetico (metadata completa: vedi JSON companion + §19 dispatch). Nessuna auto-ratifica.

1. **B2B2Q01** — Drain execution ID generation
2. **B2B2Q02** — START_DRAIN trusted event source
3. **B2B2Q03** — Mark binding and refresh behavior
4. **B2B2Q04** — Mark validation at completion
5. **B2B2Q05** — Fragment amount per accepted completion
6. **B2B2Q06** — Fragment outcome when already at cap
7. **B2B2Q07** — completion-to-Fragment atomic result contract
8. **B2B2Q08** — cancellation reason-code extensions (baseline: NO extensions)
9. **B2B2Q09** — completion/rejection result-code set
10. **B2B2Q10** — completion-vs-cancellation race precedence
11. **B2B2Q11** — completion-vs-phase-end precedence
12. **B2B2Q12** — lease and retry boundary
13. **B2B2Q13** — Drain feature-flag composition
14. **B2B2Q14** — receipt classification and capacity
15. **B2B2Q15** — audit contract
16. **B2B2Q16** — first code-gate exact scope

## 45 · First code-slice proposal

Subject to **B2B2Q16** (NON auto-ratificato). Proposta agent per `RT2-B-2B-2` code gate slice 1:

- **In-scope**: nuovi `ClassEventType` (`START_DRAIN`, `COMPLETE_DRAIN`, `CANCEL_DRAIN`), pure state machine transitions in `transitions/state_machine.py`, dispatcher extension in `transitions/dispatcher.py`, `_class_event_audit_id` mapping extension (10 new audit ids), feature flag `cdv_drain_transitions_enabled` add (default OFF), FakeStore contract tests (30+ casi), atomic completion-to-Fragment batch integrato.
- **Explicit HOLDS**: no shared-env, no human tester, no public API, no frontend, no reward, no damage, no combat resolution, no item effect, no focus_bonus effect implementation.
- **Deliverable**: implementation report MD/JSON, FakeStore test suite, no real-Mongo yet (deferred a V1 subordinato analogo a RT2-B-2B-1-V1).

## 46 · Explicit STOP

**STRICT STOP.** Il draft è documentale. Nessun code change, nessuna scrittura Mongo, nessuna attivazione flag. Baseline chain **15/15 INVARIATA**. Chiusura formale P0 attesa da orchestrator dispatch successivo che ratificherà le 16 B2B2Q.

**Fail-stop P0 attivati** (PM §25, 10 items):
- Drain requires public API → **NO**
- Drain requires frontend → **NO**
- Drain requires damage/reward implementation → **NO**
- completion-to-Fragment cannot be atomic → **NO**
- Mark binding cannot be revalidated → **NO**
- execution ID must be client-authoritative → **NO**
- lease/fencing/CAS contract conflict → **NO**
- receipt capacity requires eviction → **NO**
- shared environment required → **NO**
- item/effect dependency required → **NO**

**Fail-stop count = 0/10.**

**Attesa PM adjudication B2B2Q01…B2B2Q16.**
