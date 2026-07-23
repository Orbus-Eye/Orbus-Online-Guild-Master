# R18.6.RV3-IS2-B-P2B-RT2-B-P0 · State Store & Multi-Worker Coordination Architecture

**Regime**: `DOCUMENTAL_ONLY · READ-ONLY DISCOVERY · NO_APPLY · Italian_only · SHA Policy §31 · STRICT STOP`
**Gate ID**: `R18.6.RV3-IS2-B-P2B-RT2-B-P0 · TRANSIENT CLASS STATE STORE & MULTI-WORKER COORDINATION ARCHITECTURE`
**Stato**: `ARTIFACT_WRITTEN · PM_ADJUDICATION_REQUIRED · formal_closure=HOLD`
**Data**: 2026-02 (UTC)
**Ancoraggio invariante**: `lore_meta.py` SHA256 = `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`
**PRD reference (post-RT2-A)**: SHA256 = `240801dccfe046eda8673178a76ee78eab59d03cfee2f549a43e87af2fe1da6b` · **INVARIANT this gate**

---

## Sezione 1 · Executive summary

Il gate `R18.6.RV3-IS2-B-P2B-RT2-B-P0` produce l'architettura documentale per lo stato runtime transient (Marchi, Drenaggio, Frammenti, resource segments, event deduplication, class-state versioning, expedition ownership) sotto vincolo `DOCUMENTAL_ONLY · NO_APPLY`. Nessun codice, nessuna migrazione, nessun wiring. Deliverable = 2 file in `/app/memory/` + verifiche di governance. Il PM deve adjudicare 12 `B0Q` (5 bloccanti) prima di RT2-B code slice.

- **Store raccomandato**: `OPTION_2` — Mongo shared runtime-state documents (nuova collezione `expedition_runtime_states` + TTL index).
- **Writer autoritativo raccomandato**: `MODEL_A` — distributed lease con Mongo CAS + fencing token.
- **Modello di consistenza**: `ATOMIC_PER_EXPEDITION` per Fragment gain/spend · Drain completion · Mark cap · event deduplication.
- **NO_DB_MIGRATION baseline**: **INVALIDATA** dalla scelta Option 2 → segnalata come `NO_DB_MIGRATION_BASELINE_INVALID` (fail-stop candidato · PM adjudication B0Q09).
- **RT2-A wiring**: `NOT_IN_THIS_GATE`. Libreria RT2-A resta `NOT_RUNTIME_WIRED · DEFAULT-OFF`.
- **Applicativo, DB, OpenAPI, feature flag activation, Registry, item-gen: 0 modifiche.**

## Sezione 2 · Scope

**Incluso (documental)**: schema stato runtime · 4 modelli writer · 4 opzioni tecnologia · consistency/atomicity/CAS · event ordering + deduplication · TTL/cleanup/restart/recovery · failure matrix · migration classification · compatibility boundary · security & abuse · observability · test architecture (planned) · performance discovery · 12 `B0Q` · first code-slice proposal.

**Escluso questo gate**: qualsiasi codice · qualsiasi DB write · qualsiasi migration · qualsiasi Registry change · qualsiasi OpenAPI change · qualsiasi feature flag activation · qualsiasi wiring RT2-A · qualsiasi modifica infrastrutturale · nuovo sigillo (`NEW SEAL = NO`) · append PRD (PRD invariato).

## Sezione 3 · Governance

`SHA Policy §31` assoluta. Gli SHA dei 2 deliverable **NON** sono embedded nei file stessi: sono dichiarati **solo** nel chat report finale. Nessun append PRD in P0. Baseline chain invariant richiesta: `IS2-A · IS2-B P1 · P1-N1 · P2A · P2B-1 · RT1 · RT2-P0 · RT2-A` (8 gate). Anchor `lore_meta.py` invariant. `sealed integrity tests = 6 passed` · `sealed artifacts = 36/36 byte-identical`.

## Sezione 4 · Source chain

Predecessori: `RT2-A` (CLOSED · PM-LOCKED · foundation library) · `RT2-P0` (CLOSED · readiness plan) · `RT1` (CLOSED · power invariance baseline). Successori: `RT2-B-1..N`, `RT2-C`, `RT2-D`, `RT2-E` — **tutti HOLD**.

## Sezione 5 · Deployment discovery

Evidenze read-only raccolte in `/app` e `/etc/supervisor/conf.d/`:

- **Container definition**: `Dockerfile`, `docker-compose*.yml`, manifest Kubernetes → **NON PRESENTI** nella tree `/app`.
- **Supervisor backend**: `command=/root/.venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 1 --reload` (single-worker preview con hot-reload).
- **APP_URL env**: preview URL Emergent registrato in supervisor `environment=` blocco.
- **Kubernetes ingress**: presunto per convenzione (routing `/api` → `:8001`), evidenza applicativa non ispezionabile nel repo.
- **Horizontal scalability**: **NOT_DETERMINED_IN_REPO** — il PM deve chiarire la topologia produttiva.

## Sezione 6 · Worker topology

Preview attuale: 1 worker · hot-reload attivo · nessuna worker affinity applicativa. Le expedition si estendono su più richieste (start + polling completion tramite `complete_due_expeditions`). Non ci sono segnali di worker-local state produttivo. Se `workers>1` in produzione, richieste della stessa spedizione possono arrivare a worker diversi (LB round-robin di default).

## Sezione 7 · Available shared infrastructure

- **Mongo**: `motor 3.3.1` + `pymongo 4.6.3`. TTL indexes già usati (`expireAfterSeconds`). `find_one_and_update` = **68 usi** nel codice (CAS pattern standard). `start_session`/`start_transaction`/`with_transaction` = **0 usi** (implica pattern single-document CAS-first).
- **Redis / Celery / RQ / arq / Kafka / RabbitMQ / NATS / APScheduler**: **ASSENTI** da `requirements.txt`.
- **Object storage Tigris (S3-compat)**: presente ma **non applicabile** allo state store.
- **Scheduler applicativo**: **assente**; pattern documentato "on-visit expiry fallback + CAS lifecycle" (legendary_forge · arfus_forge · world_events · resources).

Conclusione discovery: **l'unica infrastruttura condivisa presente è MongoDB**.

## Sezione 8 · Expedition lifecycle

Endpoint attuali (RT1 baseline): `POST /api/expeditions` · `POST /api/expeditions/preview` · `GET /api/expeditions/last-completed` · `POST /api/expeditions/... (replay)` · `GET /api/expeditions` · `GET /api/expeditions/{id}`. Persistenza: `db.expeditions` + `db.expedition_members`. **Nessuna infrastruttura combat/phase/round nel codice attuale** (grep `combat_phase|combat_round|phase_id|round_id|turn_number` = 0 match). Completion driven "on-visit" via `complete_due_expeditions`. Nessun endpoint di class-event submission esistente.

## Sezione 9 · Runtime state requirements

Scope stato runtime: Marchi per source · Drain execution · Frammenti per source · resource_segment · event dedup · class-state version · expedition ownership. Escluso: valori finali item · progressione persistente · cross-expedition class state. State cross-request obbligatorio. State cross-worker obbligatorio se `workers>1`. Stato TTL-bounded. Stato eliminabile senza toccare personaggio persistente.

## Sezione 10 · State-store interface (contratto astratto)

Interfaccia candidata `ExpeditionRuntimeStateStore` con 11 operazioni: `create_state · get_state · compare_and_update · apply_event_once · reserve_writer · renew_writer_lease · release_writer · expire_state · delete_state · get_version · health_check`. Per ogni operazione sono definiti: input · output · atomicity guarantee · idempotency · conflict response · audit event · failure code (dettaglio nel JSON companion §10).

## Sezione 11 · Expedition state schema

Collezione candidata: `expedition_runtime_states`. PK candidata: `expedition_id` (unique). Campi minimi: `expedition_id · state_version · owner_worker_or_lease_id · fencing_token · lease_expires_at · created_at · updated_at · expires_at · runtime_status · loadout_snapshot_version · adventurer_class_states (map) · processed_event_keys (ring)`. **Valori finali item esclusi** (mandato §7 direttiva PM). Dimensione stimata `1..8 KB` per expedition.

## Sezione 12 · CdV class-state schema

Per Cacciatore del Vuoto: `adventurer_id · active_marks (list, cap ≤ 5) · active_drain_executions · fragment_count (cap ≤ 5) · resource_segment_id · focus_bonus_usage[segment] (cap ≤ 2) · class_state_version`. Invarianti: `cross_expedition_class_state = false` · `phase_end reset → fragment_count=0` · `expedition_end reset → fragment_count=0` · `overflow = discarded`.

## Sezione 13 · Mark state

Doc `MarkDoc`: `mark_id · application_id · source_adventurer_id · target_id · created_at · expires_at (=created_at+10s) · ritual_close_used · mark_version`. **Hard-locks (verbatim)**: active Marks ≤ 5 per source · Mark per source-target ≤ 1 · duration ≤ 10 s · automatic eviction = false. Cap enforced via CAS su `state_version` in un singolo `find_one_and_update` (pre-write pruning di expired + append). Refresh sostituisce atomicamente `application_id` e resetta `expires_at`. Retry via `apply_event_once` → no-op idempotente.

## Sezione 14 · Drain state

Doc `DrainDoc`: `drain_execution_id · source_adventurer_id · target_id · required_mark_application_id · started_at · completed_at · runtime_status · resolution_version · reward_resolved`. **Preservato verbatim da RT1**: own active Mark required at start = true · own active Mark required at completion = true · Drain consumes Mark = false · one resolution per execution id = true. Doppio completamento: prevenuto da CAS su `{drain_execution_id, runtime_status: in_progress, completed_at: null}`. Doppia ricompensa: `reward_resolved=true` settato nella stessa transizione CAS. Completion dopo scadenza Marchio: rejettata al momento del CAS. Retry: `apply_event_once` no-op.

## Sezione 15 · Fragment state

Owner = source adventurer · cap = 5 · phase_start reset = 0 · phase_end reset = 0 · expedition_end reset = 0 · overflow = discarded · focus_bonus ≤ 2 per resource_segment. Atomicità: gain via `CAS + min(current+delta, 5)` · spend via CAS con precondizione `count >= cost` · reset unconditional set 0 · segment open/close via CAS · focus_bonus increment via CAS con reject se ==2.

## Sezione 16 · Authoritative-writer models (confronto 4/4)

- **MODEL A · distributed lease** (Mongo CAS + fencing token): source-of-truth condiviso · writer selection via CAS su lease vacante o scaduto · failover naturale via TTL · fencing invalida writer stali · `RECOMMENDED_PRIMARY`.
- **MODEL B · shared atomic state (no persistent writer)**: source-of-truth Mongo · writer selection ottimistico via `state_version` · nessun lease · **STRONG ALTERNATIVE** (contesa bassa può renderlo sufficiente).
- **MODEL C · queue/actor ownership**: richiede broker (Kafka/RabbitMQ/NATS/actor runtime) · `REJECTED_THIS_GATE` (§12 · nessuna evidenza di broker in stack).
- **MODEL D · single-worker affinity + recovery**: richiede consistent hashing ingress · **REJECTED_FOR_PRIMARY** (dipendenza infra non evidenziata).

## Sezione 17 · Store technology options (confronto 4/4)

- **OPTION 1 · Redis / equivalent ephemeral**: NOT AVAILABLE in current stack → `REJECTED_THIS_GATE`.
- **OPTION 2 · Mongo shared runtime-state documents**: CAS + TTL + dedup + multi-worker safe → `RECOMMENDED_PRIMARY` (nuova collezione + TTL index).
- **OPTION 3 · existing expedition document extension**: backward-compatible additivo · `STRONG_ALTERNATIVE` (viable if PM prefers zero-new-collection).
- **OPTION 4 · process-local fake store**: `TEST_ONLY` (mandato §3).

## Sezione 18 · Recommended architecture

`OPTION_2` + `MODEL_A` + `ATOMIC_PER_EXPEDITION`. Primitiva atomica: `find_one_and_update` con filtro `{expedition_id, state_version: expected, fencing_token: lease_fencing}`. Total order per expedition via `state_version` monotonico. Deduplication via `processed_event_keys` ring size-bounded + TTL. TTL index su `expires_at`. **RT2-A NON wired in P0**: `loadout_snapshot_version` è campo riservato per integrazione futura.

## Sezione 19 · Consistency model

`ATOMIC_PER_EXPEDITION` (mandatorio) per: Fragment gain/spend · Drain completion · Mark application + cap · event deduplication (**4/4 confermate**). `STRONG_CONSISTENCY` per writer lease. `READ_ONLY_STALE_ALLOWED` per get_state/get_version. `EVENTUAL_CONSISTENCY_ACCEPTABLE` per TTL expiry sweep e audit event emission.

## Sezione 20 · Atomicity and CAS

Contratto: `expected_state_version` client-declared → server compara → mutation atomica via `find_one_and_update` con `$inc state_version` + `$set` mutation + `$currentDate updated_at`. Version mismatch → `VersionConflictError` senza partial mutation. Default retry `max_attempts=3 · backoff exponential-jitter base=25ms` (PM-reviewable). Non-retryable: integrity violations · cross-adventurer/cross-expedition mutation. Worker interrotto mid-mutation: single-document CAS è atomico → retry via `apply_event_once` è no-op idempotente.

## Sezione 21 · Versioning

`state_version = monotonic integer` (default). Successful mutation → `+1`. Presenti anche `class_state_version` per adventurer · `mark_version` per Marchio · `resolution_version` per Drain · `loadout_snapshot_version` riservato per RT2-A future wiring.

## Sezione 22 · Event ordering

`state-changing events = TOTAL_ORDER_PER_EXPEDITION` (**mandatorio**). Modelli più deboli rifiutati: non è dimostrabile la determinismo di Marchi/Drenaggio/Frammenti senza total order per expedition, salvo introdurre vector clocks o CRDT (out of scope).

## Sezione 23 · Event deduplication

Shape event: `event_id · expedition_id · source_adventurer_id · event_type · event_sequence · created_at`. Deduplication key = `event_id`. Retention default = expedition lifetime + 5 min (B0Q06). Duplicate valid event → `IDEMPOTENT_NOOP` con prior result reference. Same `event_id` con payload diverso → `INTEGRITY_VIOLATION_REJECT`. Out-of-order → `EventSequenceRejectedError`.

## Sezione 24 · Lease and ownership

`lease_id · owner_id · acquired_at · expires_at · renewed_at · lease_version · fencing_token` (monotonic). Default: `lease_ttl=30s · renewal a 50% · grace=3s`. **Fencing token OBBLIGATORIO**: ogni mutation include CAS su `fencing_token` match. Lease scaduto claimable dal prossimo worker · vecchio fencing invalidato. Nessuna persistenza recovery esterna al lease document.

## Sezione 25 · TTL and cleanup

`state TTL default = expedition_completion + 300s`. Completed/cancelled retention `300s`. Deduplication key retention allineato al TTL stato. Orphan cleanup via TTL index Mongo (nessun scheduler). Restart cleanup: N/A (stato persiste su Mongo). Manual recovery documentata come placeholder (RT2-B code slice). `cross_expedition_class_state = false` preservato.

## Sezione 26 · Restart and recovery

- Worker crash **prima** della mutation: no state change · client retry idempotente.
- Worker crash **dopo** la mutation prima della response: mutation committed atomicamente · retry via `apply_event_once` è no-op con prior result.
- Process restart: stato sopravvive (persistenza Mongo). Nessun checkpoint aggiuntivo richiesto.

## Sezione 27 · Failure matrix

Copre 12 scenari (dettagliati nel JSON companion `section_27_failure_matrix`): worker crash before/after mutation · duplicate HTTP · message redelivery · lease expiration mid-mutation · store timeout · state version conflict · missing state · corrupted state document · expedition cancellation race · phase-end reset race · two simultaneous Drain completions. Per ogni scenario: expected behavior, retry_permitted, mutation_result, player_visible_result, audit_event, manual_recovery, data_loss_risk.

## Sezione 28 · Migration classification

Categorie possibili: `RUNTIME_ONLY_SHARED_EPHEMERAL` (Option 1/4) · `BACKWARD_COMPATIBLE_EXISTING_DOCUMENT_EXTENSION` (Option 3) · `NEW_TRANSIENT_COLLECTION_REQUIRED` (Option 2) · `EXTERNAL_SHARED_STORE_REQUIRED` (Option 1). Raccomandazione agente: **`NEW_TRANSIENT_COLLECTION_REQUIRED`** (Option 2). Alternativa: `BACKWARD_COMPATIBLE_EXISTING_DOCUMENT_EXTENSION` (Option 3).

**Baseline `NO_DB_MIGRATION_REQUIRED` risulta INVALIDATA da Option 2**: `NO_DB_MIGRATION_BASELINE_INVALID` è registrato come fail-stop candidato (§28 direttiva PM). Non viene creata alcuna migrazione in P0. **Il report è completato senza forzare workaround**; il PM adjudica B0Q09 per selezionare tra Option 2 (accetta migrazione) e Option 3 (evita migrazione tramite estensione documento).

## Sezione 29 · Compatibility boundary

- `class-state feature flags disabled → current runtime unchanged`.
- `RT2-A library = remains unwired`.
- `legacy expeditions = no state-store dependency`.
- `legacy items = no class-state hooks`.
- `RT1 baseline power calculation = unchanged`.
- `RT2-A and RT2-B wired in P0 = false`.

## Sezione 30 · Security and abuse

10 minacce analizzate con mitigazioni server-authoritative: client-forged event IDs (server-generated uuid4) · event replay (`processed_event_keys` + `apply_event_once`) · sequence manipulation (server assigns) · cross-adventurer mutation (authorization owner check) · cross-expedition access (owner_guild_id check) · lease theft (fencing token) · state version tampering (server-authoritative) · over-cap Fragment injection (CAS min-cap) · foreign Mark consumption (`required_mark_application_id` ownership) · duplicate Drain reward (`reward_resolved` in stessa CAS). **All mutations = server-authoritative**.

## Sezione 31 · Observability

12 event id documentati con severità/sampling/reason_code (dettaglio nel JSON companion): `runtime_state_created · runtime_state_read_failed · runtime_state_conflict · runtime_state_updated · writer_lease_acquired · writer_lease_rejected · writer_lease_expired · duplicate_event_suppressed · event_sequence_rejected · class_state_cap_blocked · runtime_state_expired · runtime_state_recovered`. **No sensitive data**: no email · no token · no JWT · no RNG seed · no boss metadata · no full loadout. Sampling tiered per verdict RTQ15.

## Sezione 32 · Test architecture (planned · no code in P0)

14 categorie di test pianificate: contract per store impl · multi-worker concurrency · CAS conflict · lease failover · duplicate-event · event reordering · worker-crash simulation · phase-reset race · Mark cap race · Drain double-resolution · Fragment gain/spend race · TTL/cleanup · store-timeout · fallback rejection. **Nessun test scritto in P0**.

## Sezione 33 · Performance discovery

Stime documentali (senza baseline concreta):
- state mutations per expedition: `20..200`
- peak concurrent expeditions: `UNKNOWN`
- state size: `1..8 KB`
- deduplication key volume: `20..200` per expedition
- read/write latency proposta: `p95 < 20ms end-to-end`

`STATE_STORE_PERFORMANCE_BASELINE_MISSING` → registrato come **PM_REVIEW** (non blocker · benchmark bundle in RT2-B code slice).

## Sezione 34 · Operational requirements

Monitoring: `runtime_state_conflict rate · writer_lease_rejected rate · runtime_state_read_failed rate · TTL sweep latency · state_version distribution`. Alerting: `corrupted_state count > 0 → page · lease_rejected rate spike → warn · conflict_rate > SLA → warn`. Runbook placeholders: manual state recovery · manual lease invalidation · TTL-index rebuild · collection rollback. Nessuna nuova dipendenza operativa oltre Mongo.

## Sezione 35 · Risk register

8 rischi registrati: R01 Mongo replica-set unavailable (MEDIUM · PM review) · R02 production worker count unknown (MEDIUM · PM review) · R03 NO_DB_MIGRATION baseline invalidated (HIGH · PM review B0Q09) · R04 performance baseline missing (LOW) · R05 clock skew su lease TTL (LOW_MEDIUM) · R06 processed_event_keys unbounded growth (MEDIUM) · R07 hot-reload single-worker hides multi-worker bugs (MEDIUM) · R08 state document size growth (LOW).

## Sezione 36 · PM open questions (12 · NO AUTO-RATIFICAZIONE)

`B0Q01` state-store technology · `B0Q02` writer strategy · `B0Q03` ownership scope · `B0Q04` versioning policy · `B0Q05` ordering policy · `B0Q06` deduplication retention · `B0Q07` TTL default · `B0Q08` restart/failover · `B0Q09` migration classification · `B0Q10` first RT2-B code slice · `B0Q11` performance acceptance · `B0Q12` operational dependency approval. Blocking = 11/12 (tutti tranne B0Q11 marcato non-blocker). **Nessuna auto-ratificazione.**

## Sezione 37 · First code-slice proposal (RT2-B-1)

Scope proposto: (a) creazione collezione + TTL index idempotente · (b) implementazione Mongo di `ExpeditionRuntimeStateStore` · (c) in-memory fake store per test · (d) contract test suite. **Escluso**: wiring a expedition services · attivazione feature flag class-state · logica Marchi/Drenaggio/Frammenti · wiring RT2-A · modifiche OpenAPI · public API changes. Authorization required: adjudication PM su `B0Q01/B0Q02/B0Q09/B0Q10` almeno.

## Sezione 38 · RT2-B readiness

`state = HOLD_PENDING_PM_DECISIONS`. Blocked by: `B0Q01 · B0Q02 · B0Q09 · B0Q10 · B0Q12`. Unblocked upon PM verdict sui 5 blockers.

## Sezione 39 · GO/HOLD recommendation

**`HOLD-PENDING-PM-DECISIONS`**. Motivazione: 12 B0Q emesse (5 bloccanti). Architettura raccomandata (Option 2 · Model A) rientra nello stack Mongo esistente senza introduzione di nuove tecnologie; tuttavia la baseline `NO_DB_MIGRATION_REQUIRED` è invalidata da Option 2 → richiesta adjudication `B0Q09`. Nessun fail-stop deterministico auto-detected in discovery read-only; `NO_DB_MIGRATION_BASELINE_INVALID` è registrato come candidato che richiede adjudication PM, non come auto-blocker in questa fase documental.

## Sezione 40 · STOP esplicito

**STOP**. Deliverables documentali scritti · PM adjudication richiesta · no codice · no migration · no wiring · PRD invariato · sealed set invariato (36) · anchor invariante.

---

**Fine documento** · Italian_only · DOCUMENTAL_ONLY · RT2-B-P0 · SHA Policy §31 · STRICT STOP
