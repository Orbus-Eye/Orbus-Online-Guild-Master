# R18.6.RV3-IS2-B-P2B-RT2-B-P0 · State Store & Multi-Worker Coordination Architecture · PATCHED

**Regime**: `DOCUMENTAL_ONLY · READ-ONLY DISCOVERY · NO_APPLY · Italian_only · SHA Policy §31 · STRICT STOP`
**Gate ID**: `R18.6.RV3-IS2-B-P2B-RT2-B-P0`
**Stato**: `PATCHED · PM_VERDICTS_APPLIED · 12/12 B0Q RESOLVED · READY_FOR_RT2-B-1A_DISPATCH`
**Patch date**: 2026-02 (UTC)
**Ancoraggio invariante**: `lore_meta.py` SHA256 = `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`
**PRD reference (post-RT2-A, pre-P0 append)**: SHA256 = `240801dccfe046eda8673178a76ee78eab59d03cfee2f549a43e87af2fe1da6b`

> **PM VERDICT PATCH APPLIED** — Il PM ha ratificato le 12 B0Q e ha selezionato: `store technology = OPTION 2 (Mongo dedicated collection expedition_runtime_states)` · `writer strategy = MODEL A (distributed lease + fencing token)` · `consistency = ATOMIC_PER_EXPEDITION` · `event ordering = server authoritative` · `NO_DB_MIGRATION_BASELINE_INVALID = TRIGGERED_AND_ADJUDICATED` (schema provisioning change, no data backfill, split to RT2-B-1B) · `first code slice = RT2-B-1A (non-wired adapter foundation)`. Le 40 sezioni sono preservate in ordine e nomi; il contenuto è aggiornato per riflettere i verdict verbatim.

---

## Sezione 1 · Executive summary

Il gate `RT2-B-P0` è **PATCHED · PM-APPROVED**. Architettura ratificata: `Mongo dedicated collection` (`expedition_runtime_states`) + `distributed lease per expedition + fencing token` + `ATOMIC_PER_EXPEDITION`. 12/12 B0Q risolte verbatim. Fail-stop `NO_DB_MIGRATION_BASELINE_INVALID` = `TRIGGERED_AND_ADJUDICATED` (SCHEMA PROVISIONING CHANGE · no data backfill · split a `RT2-B-1B`). First code slice autorizzato: `RT2-B-1A · STATE STORE CONTRACT & NON-WIRED ADAPTER FOUNDATION` (CONDITIONAL_GO Phase 2 dispatch). Applicativo/DB/OpenAPI/Registry/item-gen/feature-flag/wiring = 0 modifiche in Phase 1.

## Sezione 2 · Scope

Documental only. Incluso: schema stato runtime + writer models + store options + consistency + CAS + event ordering + dedup + TTL + failure matrix + migration classification + compatibility boundary + security + observability + test architecture (planned) + performance discovery + 12 B0Q (RESOLVED) + first code slice proposal. Escluso questo gate: codice · DB write · migration · collection · index · OpenAPI · feature flag activation · wiring RT2-A · modifiche infrastrutturali · nuovo sigillo · nuovi B0Q non risolti.

## Sezione 3 · Governance

`SHA Policy §31` assoluta. Gli SHA dei deliverable **NON** sono embedded nei file stessi: dichiarati solo nel chat report. `PRD append idempotente = exactly 1`. Baseline chain 8/8 invariant: `IS2-A · IS2-B-P1 · IS2-B-P1-N1 · IS2-B-P2A · IS2-B-P2B-1 · IS2-B-P2B-RT1 · IS2-B-P2B-RT2-P0 · IS2-B-P2B-RT2-A`. Anchor `lore_meta.py` invariant. `sealed integrity tests = 6 passed` · `sealed artifacts = 36/36 byte-identical`.

## Sezione 4 · Source chain

Predecessori: `RT2-A` CLOSED PM-LOCKED · `RT2-P0` CLOSED · `RT1` CLOSED. Successori: `RT2-B-1A` CONDITIONAL GO (Phase 2 dispatch) · `RT2-B-1B` HOLD (provisioning gate futuro) · `RT2-B (gameplay integration) · RT2-C · RT2-D · RT2-E` tutti HOLD.

## Sezione 5 · Deployment discovery

Evidenze immutate: `uvicorn server:app --host 0.0.0.0 --port 8001 --workers 1 --reload` (single-worker **preview**; **NON garanzia** per produzione multi-worker). `Dockerfile`, `docker-compose*.yml`, manifest k8s = **NON PRESENTI** in `/app`. `APP_URL` env preview. Kubernetes ingress presunto per convenzione. Horizontal scalability = `NOT_DETERMINED_IN_REPO` — l'architettura scelta (lease + fencing) **è progettata per N≥1 workers e sopravvive a scaling futuro senza ridisegno**.

## Sezione 6 · Worker topology

Preview: 1 worker · hot-reload. Le expedition si estendono su più richieste. Nessuna worker affinity applicativa. Nessuna sticky-session sul percorso spedizione. Il modello lease+fencing garantisce single-authoritative-writer indipendentemente dalla topologia (single-worker degrada trivialmente a single-writer).

## Sezione 7 · Available shared infrastructure

- **Mongo**: `motor 3.3.1` · `pymongo 4.6.3` · `find_one_and_update = 68 usi` · TTL indexes già usati · `start_session/with_transaction = 0`. **Unica infrastruttura condivisa presente e scelta come source-of-truth**.
- Redis / Celery / RQ / arq / Kafka / RabbitMQ / NATS / APScheduler = **ASSENTI** (`requirements.txt`).
- Object storage Tigris = presente ma non applicabile.

## Sezione 8 · Expedition lifecycle

Endpoint attuali: `POST /api/expeditions`, `POST /api/expeditions/preview`, `GET /api/expeditions/last-completed`, replay endpoint, `GET /api/expeditions`, `GET /api/expeditions/{id}`. Persistenza: `db.expeditions` + `db.expedition_members`. Nessuna infrastruttura combat/phase/round nel codice attuale. Completion on-visit via `complete_due_expeditions`. Nessun endpoint di class-event submission esistente (RT2-B target).

## Sezione 9 · Runtime state requirements

Scope stato runtime: Marchi per source · Drain execution · Frammenti per source · resource_segment · event dedup · class-state version · expedition ownership. Escluso: valori finali item · progressione persistente · cross-expedition class state. State cross-request obbligatorio. State cross-worker obbligatorio. Stato TTL-bounded. Stato eliminabile senza toccare personaggio persistente. **Cross_expedition_class_state = false** invariante.

## Sezione 10 · State-store interface (contratto astratto · PM ratified)

Interfaccia `ExpeditionRuntimeStateStore` con 11 operazioni: `create_state · get_state · compare_and_update · apply_event_once · reserve_writer · renew_writer_lease · release_writer · expire_state · delete_state · get_version · health_check`. Ogni operazione mutation-side filtra su `{expedition_id, state_version, lease_id, fencing_token}` (B0Q02+B0Q04). Ownership per-expedition (B0Q03). Adapter Mongo autorizzato in RT2-B-1A **con collezione iniettata**; NON istanziato dal runtime (B0Q10).

## Sezione 11 · Expedition state schema

Collezione canonica: **`expedition_runtime_states`** (PM verdict B0Q01). PK: `expedition_id` unique. Campi: `expedition_id · state_version (monotonic int, initial=1) · owner_worker_or_lease_id · fencing_token (monotonic) · lease_expires_at · created_at · updated_at · expires_at · runtime_status · loadout_snapshot_version · adventurer_class_states (map key adventurer_id) · processed_event_keys (bounded ring per B0Q06)`. Valori finali item **esclusi**. Dimensione stimata: `< 256 KiB` (B0Q11).

## Sezione 12 · CdV class-state schema

Per adventurer (keyed by `adventurer_id` · B0Q03): `active_marks (list, cap ≤ 5) · active_drain_executions · fragment_count (cap ≤ 5) · resource_segment_id · focus_bonus_usage[segment] (cap ≤ 2) · class_state_version`. Invarianti verbatim: `cross_expedition_class_state = false` · `phase_end reset → fragment_count=0` · `expedition_end reset → fragment_count=0` · `overflow = discarded`.

## Sezione 13 · Mark state

`MarkDoc`: `mark_id · application_id · source_adventurer_id · target_id · created_at · expires_at (=created_at+10s) · ritual_close_used · mark_version`. Hard-locks verbatim: active Marks ≤ 5 per source · Mark per source-target ≤ 1 · duration ≤ 10 s · automatic eviction = false. Enforcement via CAS su `state_version + fencing_token` in singolo `find_one_and_update` (pre-write pruning expired + append). Refresh sostituisce atomicamente `application_id`. Retry deduplicato per `event_id` (B0Q06).

## Sezione 14 · Drain state

`DrainDoc`: `drain_execution_id · source_adventurer_id · target_id · required_mark_application_id · started_at · completed_at · runtime_status · resolution_version · reward_resolved`. Verbatim RT1: own active Mark required at start = true · own active Mark required at completion = true · Drain consumes Mark = false · one resolution per execution id = true. Doppio completamento: prevented via CAS su `{drain_execution_id, runtime_status: in_progress, completed_at: null, state_version, fencing_token}`. Doppia ricompensa: `reward_resolved=true` settato nella stessa transizione. Completion post Mark expiry: rejected al CAS. Retry: `apply_event_once` no-op (B0Q06).

## Sezione 15 · Fragment state

Owner = source adventurer · cap = 5 · reset a phase_start / phase_end / expedition_end = 0 · overflow discarded · focus_bonus cap 2 per segment. Atomicità: `gain = CAS + min(current+delta, 5)` · `spend = CAS con precondition count>=cost` · `reset = CAS set 0` · `segment open/close = CAS` · `focus_bonus_use = CAS increment reject se ==2`. Ogni CAS filtra `state_version + fencing_token` (B0Q04).

## Sezione 16 · Authoritative-writer models (confronto 4/4 · SELECTED = MODEL A)

**PM verdict B0Q02: SELECTED = MODEL A (distributed lease + fencing token).**

- **MODEL A · distributed lease + fencing token** → **SELECTED**. Mongo CAS su `{lease_holder, lease_expires_at, fencing_token}`. Fencing invalida writer stali anche dopo pausa/partizione. Nessuna affinità permanente. Lease TTL 30s · renewal 10s · grace 5s (B0Q08).
- **MODEL B · shared atomic state (no lease)** → NOT_SELECTED (viable but rejected: fencing token è richiesto invariante).
- **MODEL C · queue/actor** → NOT_SELECTED (nessun broker in stack).
- **MODEL D · single-worker affinity + recovery** → NOT_SELECTED (dipendenza ingress non evidenziata, richiede infra additiva).

## Sezione 17 · Store technology options (confronto 4/4 · SELECTED = OPTION 2)

**PM verdict B0Q01: SELECTED = OPTION 2 (Mongo dedicated runtime-state collection `expedition_runtime_states`).**

- **OPTION 1 · Redis / ephemeral esterno** → NOT_SELECTED.
- **OPTION 2 · Mongo dedicated collection** → **SELECTED** (`expedition_runtime_states` · TTL index · CAS).
- **OPTION 3 · existing expedition document extension** → NOT_SELECTED (nonostante backward-compat, il PM ha scelto separazione tra stato transient e documento persistente).
- **OPTION 4 · process-local fake store** → APPROVED_FOR_TESTS_ONLY (unit + contract test).

## Sezione 18 · Recommended architecture (PM ratified)

`OPTION_2` + `MODEL_A` + `ATOMIC_PER_EXPEDITION`. Primitiva: `find_one_and_update({_id: expedition_id, state_version: expected, fencing_token: expected}, {$inc: {state_version:1}, $set: mutation, $currentDate: {updated_at:true}})`. Total order per expedition via `state_version` monotonico + `event_sequence` server-authoritative (B0Q05). Deduplication via receipt (event_id · payload_hash · sequence · result_code · state_version_after · processed_at) (B0Q06). TTL index su `expires_at`. `RT2-A NOT WIRED`; `loadout_snapshot_version` riservato.

## Sezione 19 · Consistency model

`ATOMIC_PER_EXPEDITION` mandatorio per: `Fragment gain/spend · Drain completion · Mark application+cap · event deduplication`. `STRONG_CONSISTENCY` per writer lease acquire/renew/release. `READ_ONLY_STALE_ALLOWED` per `get_state / get_version`. `EVENTUAL_CONSISTENCY_ACCEPTABLE` per TTL sweep e audit emission. **4/4 ops ATOMIC_PER_EXPEDITION confermate**.

## Sezione 20 · Atomicity and CAS (B0Q04 verbatim)

Contratto: `state_version = monotonic int (initial=1)` · `mutation filter min = {_id: expedition_id, state_version: expected, fencing_token: expected}` · `outcomes: match → atomic mutation · version_mismatch → STATE_VERSION_CONFLICT · fencing_mismatch → STALE_WRITER_REJECTED · partial mutation → FORBIDDEN`. `Max CAS retries = 3` (solo dopo fresh state read). Non-retryable: payload invalido, ownership invalida, cap superato, fencing scaduto, same `event_id` con payload differente.

## Sezione 21 · Versioning

`state_version = monotonic integer` (B0Q04). Presenti anche `class_state_version` per adventurer · `mark_version` · `resolution_version` · `loadout_snapshot_version` (riservato RT2-A future wiring · unused in P0/1A).

## Sezione 22 · Event ordering (B0Q05 verbatim)

`state-changing events = total ordered per expedition (server-authoritative)`. `event_sequence` assegnato atomicamente dalla mutation accettata. Client **non può** scegliere sequenza autoritativa. Ogni mutation accettata: `last_event_sequence → last_event_sequence + 1`. Retry stesso `event_id`: nessuna nuova sequenza, restituisce risultato precedente, non muta. Eventi concorrenti serializzati via CAS sul documento spedizione.

## Sezione 23 · Event deduplication (B0Q06 verbatim)

Dedup key = `expedition_id + event_id`. Receipt min: `event_id · event_type · source_adventurer_id · payload_hash · assigned_event_sequence · result_code · state_version_after · processed_at`. `same event_id + same payload hash → idempotent prior-result response`. `same event_id + different payload hash → EVENT_ID_PAYLOAD_MISMATCH → reject`. Retention = lifetime del documento stato. Receipt bounded (max per spedizione configurabile · benchmark obbligatorio pre-integrazione runtime). Al limite: `fail closed · no receipt eviction during active expedition`.

## Sezione 24 · Lease and ownership (B0Q08 verbatim)

`lease_id · owner_id · acquired_at · expires_at · renewed_at · lease_version · fencing_token (monotonic)`. Defaults: `lease_duration = 30s · renewal_interval = 10s · grace_period = 5s`. Ogni nuova acquisizione valida `+1 fencing_token`. Scenari: worker crash before mutation → no state change; crash after mutation → retry deduplicated by event_id; lease expiry → nuovo worker acquires con fencing_token più alto; stale worker resume → mutation rejected. **Application clock alone insufficient**; acquire/renewal via atomic store mutation.

## Sezione 25 · TTL and cleanup (B0Q07 baseline)

`active state inactivity TTL = 6 hours` · `completed expedition retention = 24 hours` · `cancelled expedition retention = 24 hours` · `deduplication retention = until state-document expiry`. Ogni mutation valida aggiorna `updated_at + expires_at`. Cleanup: normal completion/cancellation → terminal + 24h TTL; orphan → TTL cleanup; manual → exceptional recovery. **Baseline values, non live authorization**; riesame post-misure reali.

## Sezione 26 · Restart and recovery

Stato sopravvive process restart (persistenza Mongo). Lease TTL 30s garantisce failover naturale. `worker crash before mutation → no change`. `worker crash after atomic mutation → retry deduplicated by event_id (B0Q06)`. `lease expiry → other worker acquires with higher fencing_token`. `stale worker resume → mutation rejected via fencing mismatch (STALE_WRITER_REJECTED)`. Nessun checkpoint additivo richiesto (lease document è sufficiente).

## Sezione 27 · Failure matrix

12 scenari coperti nel JSON companion (`section_27_failure_matrix`): worker crash before/after mutation · duplicate HTTP · message redelivery · lease expiration mid-mutation · store timeout · state version conflict · missing state · corrupted state · expedition cancellation race · phase-end reset race · two simultaneous Drain completions. Per ognuno: expected_behavior · retry_permitted · mutation_result · player_visible_result · audit_event · manual_recovery · data_loss_risk.

## Sezione 28 · Migration classification (B0Q09 CRITICAL · TRIGGERED_AND_ADJUDICATED)

`NO_DB_MIGRATION_BASELINE_INVALID = TRIGGERED FOR RT2-B`.

Chiarimento PM: `gameplay state semantics = transient` · `physical storage = Mongo persistent collection with TTL`. Transient descrive il lifecycle, non l'assenza di scritture Mongo.

Classificazione ratificata:
- `NEW_TRANSIENT_COLLECTION_REQUIRED = TRUE`
- `NEW_TTL_INDEX_REQUIRED = TRUE`
- `DATA_BACKFILL_REQUIRED = FALSE`
- `PERSISTENT_CHARACTER_SCHEMA_CHANGE = FALSE`

Natura del change: **DB INFRASTRUCTURE / SCHEMA PROVISIONING CHANGE** — NON migrazione dati tradizionale · nessun backfill. Provisioning **da autorizzare/applicare in gate separato `RT2-B-1B`**. La decisione **non riapre RT1 o RT2-A**; invalida solo l'ipotesi `NO_DB_MIGRATION_REQUIRED` per il ramo stateful RT2-B/C.

## Sezione 29 · Compatibility boundary (invariante)

- `cdv_transient_state_enabled = false` · `item_effect_engine_enabled = false` · `RT2-A runtime wiring = false`.
- Con flag disabilitati: `current runtime behavior = unchanged`.
- Oggetti legacy e spedizioni esistenti: **non dipendono** dalla nuova collection · **non ricevono** class state · **non vengono** migrati · **non vengono** modificati.
- `RT1 baseline power calculation = unchanged`.

## Sezione 30 · Security and abuse

10 minacce mitigate server-authoritative: client-forged event IDs (server-generated `event_id`) · replay (`processed_event_keys` + `apply_event_once` · B0Q06) · sequence manipulation (server-assigned · B0Q05) · cross-adventurer state mutation (auth check + separated ownership · B0Q03) · cross-expedition access (owner check) · lease theft (fencing token · B0Q02) · state version tampering (server-authoritative) · over-cap Fragment injection (CAS min-cap) · foreign Mark consumption (`required_mark_application_id` ownership) · duplicate Drain reward (atomic `reward_resolved`). **All mutations = server-authoritative**.

## Sezione 31 · Observability

12 event id: `runtime_state_created · runtime_state_read_failed · runtime_state_conflict · runtime_state_updated · writer_lease_acquired · writer_lease_rejected · writer_lease_expired · duplicate_event_suppressed · event_sequence_rejected · class_state_cap_blocked · runtime_state_expired · runtime_state_recovered`. Severità/sampling/reason_code documentati nel JSON companion. **No sensitive data**: no email · no token · no JWT · no RNG seed · no boss metadata · no full loadout. Sampling tiered per verdict RTQ15.

## Sezione 32 · Test architecture (planned · code arrives with RT2-B-1A)

14 categorie di test: contract per store impl · multi-worker concurrency (pytest-xdist) · CAS conflict + retry exhaustion · lease failover · duplicate-event idempotency · event reordering rejection · worker-crash simulation · phase-reset race · Mark cap race · Drain double-resolution · Fragment gain/spend race · TTL/cleanup · store-timeout · fallback rejection. **Nessun test scritto in Phase 1 P0**. Testing autorizzato con RT2-B-1A **con collezione mockata / injected** (no Mongo reale).

## Sezione 33 · Performance discovery (B0Q11 tiered)

**RT2-B-1A**: `database calls in tests = 0 · network calls in tests = 0 · unbounded memory growth = 0 · contract-test behavior = deterministic`.
**RT2-B-1B (futuro)**: `single-state read p95 ≤ 25 ms · CAS mutation p95 ≤ 35 ms · lease acquire/renew p95 ≤ 35 ms · dedup retry p95 ≤ 25 ms · state doc < 256 KiB · Mongo hard-limit approach FORBIDDEN · unbounded processed-event growth FORBIDDEN`. Se metriche non riproducibili: `STATE_STORE_PERFORMANCE_BASELINE_MISSING = BLOCKING for RT2-B-1B CLOSURE`. **Le soglie non autorizzano traffico live.**

## Sezione 34 · Operational requirements

Monitoring futuro: `runtime_state_conflict rate · writer_lease_rejected rate · runtime_state_read_failed rate · TTL sweep latency · state_version distribution`. Alerting: `corrupted_state > 0 → page · lease_rejected spike → warn · conflict rate > SLA → warn`. Runbook: manual state recovery · manual lease invalidation · TTL rebuild · collection rollback. **Approvazione operativa new collection = DEFERRED_TO_RT2-B-1B** (B0Q12: naming, permessi, backup, TTL, monitoring, capacity, rollback, target env). Nessuna nuova dipendenza operativa oltre Mongo (già primary).

## Sezione 35 · Risk register (aggiornato)

R01 Mongo replica-set status confermare (MEDIUM · PM review pre-1B). R02 production worker count unknown (MEDIUM · design lease-based sopravvive N≥1). R03 NO_DB_MIGRATION baseline invalidated (**RESOLVED via B0Q09**). R04 performance baseline missing (LOW · benchmark in 1B). R05 clock skew su lease (LOW_MEDIUM · fencing token + atomic acquire mitiga). R06 processed_event_keys unbounded (**RESOLVED via B0Q06 fail-closed cap**). R07 hot-reload preview hides multi-worker bugs (MEDIUM · contract test multi-worker in 1A). R08 state document > 256 KiB (LOW · hard cap · B0Q11).

## Sezione 36 · PM open questions (12 · RESOLVED 12/12 · verdict verbatim)

**Tutti e 12 i B0Q sono `RESOLVED` con verdict verbatim del PM. Il dettaglio completo è nel JSON companion `section_36_pm_open_questions` e nel top-level `pm_verdict_applied_2026_02`.** Nessuna auto-ratificazione. Sintesi:
- `B0Q01` = OPTION_2 · `expedition_runtime_states`
- `B0Q02` = MODEL_A · distributed lease + fencing token
- `B0Q03` = per-expedition ownership; adventurer_class_states keyed by adventurer_id
- `B0Q04` = monotonic int state_version (initial=1) · max 3 retries · filter min: expedition_id + state_version + fencing_token
- `B0Q05` = total order per expedition · server-authoritative sequence
- `B0Q06` = dedup key = expedition_id+event_id · receipt bounded · fail-closed
- `B0Q07` = 6h inactivity TTL · 24h post-completion retention (baseline)
- `B0Q08` = lease 30s / renew 10s / grace 5s · fencing_token increments on new acquisition
- `B0Q09` = TRIGGERED_AND_ADJUDICATED · SCHEMA_PROVISIONING_CHANGE · no backfill · split RT2-B-1B
- `B0Q10` = RT2-B-1A · non-wired adapter foundation
- `B0Q11` = 1A criteria (0 DB/network/unbounded · deterministic) + 1B future p95 targets
- `B0Q12` = Mongo reuse APPROVED_IN_PRINCIPLE · operational approval DEFERRED to 1B

## Sezione 37 · First code-slice proposal (RT2-B-1A · PM approved)

Canonical name: **`R18.6.RV3-IS2-B-P2B-RT2-B-1A · STATE STORE CONTRACT & NON-WIRED ADAPTER FOUNDATION`**.

Authorized scope (B0Q10 verbatim): `ExpeditionRuntimeStateStore interface · state schemas · lease schemas · fencing-token validation · CAS result types · event receipt schemas · fake in-memory test store · Mongo adapter implementation with injected collection (NOT wired to runtime) · shared contract-test suite · unit tests with mocked Mongo collection · security and validation tests`.

Excluded (deferred to RT2-B-1B or later): `Mongo collection creation · TTL index creation · real DB integration tests · runtime wiring · expedition service changes · feature flag activation · Mark/Drain/Fragment gameplay execution · RT2-A wiring · public API changes`.

**Hard rule**: **Il Mongo adapter può essere implementato ma NON deve essere istanziato dal runtime applicativo.**

## Sezione 38 · RT2-B readiness

`RT2-B-P0 = CLOSED_PM_LOCKED_AT_PHASE_1_END` · `RT2-B-1A = CONDITIONAL_GO_AWAITING_PHASE_2_DISPATCH` · `RT2-B-1B = PLANNED_HOLD_NOT_AUTHORIZED` · `RT2-B gameplay integration = HOLD` · `RT2-C/D/E = HOLD`.

## Sezione 39 · GO/HOLD recommendation

**`RT2-B-P0 = CLOSE_AND_LOCK · RT2-B-1A = CONDITIONAL_GO`**. Motivazione: 12/12 B0Q risolte verbatim; architettura ratificata; fail-stop critico (B0Q09) adjudicato via split gate; nessuna dipendenza infrastrutturale nuova richiesta per il code slice 1A; boundary invariants preservate.

## Sezione 40 · STOP esplicito

**STOP Phase 1**. Deliverables patched · closure emesso · PRD append idempotente · governance verificata · Sealed set invariato (36) · anchor invariante · baseline chain 8/8 invariante · RT2-A files unchanged. In attesa di Phase 2 dispatch (RT2-B-1A code) da orchestrator.

---

**Fine documento** · Italian_only · DOCUMENTAL_ONLY · RT2-B-P0 PATCHED · SHA Policy §31 · STRICT STOP
