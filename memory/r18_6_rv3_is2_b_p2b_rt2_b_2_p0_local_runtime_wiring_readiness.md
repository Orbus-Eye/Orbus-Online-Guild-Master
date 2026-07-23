# R18.6.RV3-IS2-B-P2B-RT2-B-2-P0 · Local Runtime Wiring & Class-State Integration Readiness Plan · PATCHED · PM-RATIFIED 2026-02

**Regime**: `DOCUMENTAL_ONLY · READ-ONLY DISCOVERY · Italian_only · NO APPLY · SHA Policy §31 · STRICT STOP`
**Gate ID**: `R18.6.RV3-IS2-B-P2B-RT2-B-2-P0 · LOCAL RUNTIME WIRING & CLASS-STATE INTEGRATION READINESS PLAN`
**Ancoraggio invariante**: `lore_meta.py` SHA256 = `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`
**Fonte upstream**: `R18.6.RV3-IS2-B-P2B-RT2-B-1B-1 · CLOSED · PM-LOCKED`
**PRD reference (pre-append)**: SHA256 = `0eb7477abdcda64ac1ca3c6d3272a04a089bad186b260f62ff7f13a1cb9a089b` (post-RT2-B-1B-1, INVARIANT fino al PRD-append di questa closure)
**Status**: `PATCHED · PM-RATIFIED · 12/12 B2Q APPLIED VERBATIM · READY FOR FORMAL CLOSURE`
**Data patch**: 2026-02 (UTC)

> **PM VERDICT PATCH APPLICATO** — Il PM ha ratificato verbatim i 12 verdetti `B2Q01…B2Q12`. Contenuto delle sezioni aggiornato per riflettere i verdetti PM. Sezioni conservate `34/34` verbatim in ordine e nome. `JSON parse = PASS` preservato. Nessuna auto-ratificazione: le sezioni PM-Open-Questions (Sezione 32) sono transitate da `NON_AUTO_RATIFIED` a `PM_RATIFIED_VERBATIM_2026_02` per direttiva orchestrator.

---

## Sezione 1 · Executive Summary

Il gate `RT2-B-2-P0` produce, **strettamente documentale e read-only**, il piano di readiness per la Phase successiva `RT2-B-2A · LOCAL SHADOW WIRING & STATE LIFECYCLE FOUNDATION`: il primo cablaggio del `MongoExpeditionRuntimeStateStore` al lifecycle applicativo delle spedizioni, in modalità **shadow / non-player-affecting**, confinato al **test-user boundary server-authoritative** (`users.is_test_user=true`, verdict B2Q06), e sotto **feature flag `cdv_transient_state_enabled = false` di default** (verdict B2Q07, attivabile solo local/test env). Il **calcolo corrente resta autoritativo** (verdict B2Q01): il nuovo runtime è shadow-only, senza autorità gameplay in RT2-B-2A.

I 12 B2Q sono ora **PM-RATIFIED VERBATIM 2026-02**. 4/4 fail-stop `NOT_TRIGGERED`. Baseline chain 12/12 invariante. Governance intatta.

**Recommendation P0**: `RT2-B-2-P0 CLOSED / PM-LOCKED` · `RT2-B-2A READY-TO-DISPATCH` (Phase 2 orchestrator dispatch separato).

---

## Sezione 2 · Scope

**In scope (P0 documentale)**: mappatura lifecycle spedizione live · identificazione touchpoint per shadow-wire dello state store · caratterizzazione del boundary test-user server-authoritative · ricognizione class-state semantics per Cacciatore del Vuoto (CdV) · proposta di rollout con FF invarianti · 4 fail-stop · **12 B2Q RATIFICATI VERBATIM PM 2026-02** · failure matrix runtime-wiring · risk register · scope canonico e esclusioni di `RT2-B-2A`.

**Out of scope (P0 vietato)**: modifica di qualsiasi file `.py` applicativo (expedition / adventurer / auth / core) · nuova collection / index / provisioning · nuova rotta `/api/*` · OpenAPI mutation · FF activation · Registry v3 · item-gen · Mongo write in shared env · shadow read/write live · code slicing di `RT2-B-2A` · attivazione tester gameplay · frontend changes. Nessun nuovo sigillo (`NEW SEAL = NO`).

---

## Sezione 3 · Governance

- Regime `DOCUMENTAL_ONLY · READ-ONLY DISCOVERY · Italian_only`.
- `lore_meta.py` invariant · anchor SHA `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`.
- Baseline chain **12/12 byte-identical**: `IS2-A · IS2-B-P1 · IS2-B-P1-N1 · IS2-B-P2A · IS2-B-P2B-1 · IS2-B-P2B-RT1 · IS2-B-P2B-RT2-P0 · IS2-B-P2B-RT2-A · IS2-B-P2B-RT2-B-P0 · IS2-B-P2B-RT2-B-1A · IS2-B-P2B-RT2-B-1B-P0 · IS2-B-P2B-RT2-B-1B-1`.
- `sealed integrity tests = 6 passed` · `sealed artifacts = 36/36 byte-identical` (verificato).
- `effect_engine tests = 284/284 passed` (verificato — nessuna regressione).
- `NEW SEAL = NO`.
- PRD SHA pre-append: `0eb7477abdcda64ac1ca3c6d3272a04a089bad186b260f62ff7f13a1cb9a089b`. **PRD delta in questa closure Phase 1 = 1 append idempotente** (blocco `RT2-B-2-P0 · CLOSED`).
- SHA Policy §31 stretta: gli SHA dei 2 deliverable P0-patched + 3 closure artifact **NON sono embedded** dentro i file stessi — dichiarati **solo** nel chat report finale.
- Closure manifest §31: **manifest own SHA = NOT EMBEDDED**. Byte-exact verification post-scrittura.

---

## Sezione 4 · Source Chain

| # | Upstream artifact | Status | Rilevanza |
|---|---|---|---|
| 1 | `RT2-B-P0` — State Store & Multi-Worker Architecture | PM-LOCKED | Contract origine 11 op astratte |
| 2 | `RT2-B-1A` — Store Contract & Non-Wired Adapter Foundation | PM-LOCKED | Library stand-alone (14 file) |
| 3 | `RT2-B-1B-P0` — Mongo Provisioning Readiness Plan | PM-LOCKED | 31 sezioni + 12/12 B1BQ ratificati |
| 4 | `RT2-B-1B-1` — Local Isolated Provisioning & Real Adapter Validation | PM-LOCKED | 16 nuovi file, 57/57 real Mongo test, 284 combined |
| 5 | `RT2-A` — CdV & Effect Engine (24 code + 14 test) | PM-LOCKED | Effect engine backbone, FF invarianti |
| 6 | `RT1` — Runtime Stat & Effect Semantics Specification | PM-LOCKED | Hard-lock invariants (Marks/Fragments/Drain) |
| 7 | `app/expeditions/routes.py` (139 righe) | READ-ONLY EVIDENCE | 6 rotte pubbliche `/api/expeditions/*` |
| 8 | `app/expeditions/services.py` (1378 righe) | READ-ONLY EVIDENCE | `_dispatch_expedition` · `_complete_one_expedition` |
| 9 | `app/auth/services.py` (324 righe) | READ-ONLY EVIDENCE | `is_test_user` server-authoritative |
| 10 | `app/admin/services.py` | READ-ONLY EVIDENCE | Admin CAS toggle `is_test_user` |
| 11 | `app/stats/runtime/state_store/*` (7 file · 1653 righe) | READ-ONLY EVIDENCE | Library stand-alone, 0 import fuori namespace |
| 12 | `app/stats/runtime/feature_flags.py` (138 righe) | READ-ONLY EVIDENCE | Hard-force False su future constants |
| 13 | PM Dispatch RT2-B-2-P0 · PATCH (12 B2Q verdicts 2026-02) | RATIFYING DIRECTIVE | Origina questa PATCH |

---

## Sezione 5 · Discovery Methodology

Metodologia strettamente **grep / cat / read-only view** su `/app/backend/**/*.py`. Nessun `find_one` / `insert` / `update` verso Mongo · nessuna esecuzione uvicorn locale. Sette query eseguite in draft P0 (invariate post-patch):

1. `grep -rn "is_test_user"` → server-authoritative confermato in 4 servizi consumer.
2. `grep -rn "expedition"` → mappatura completa dei 30+ file.
3. `grep -rn "state_store\|from app.stats.runtime"` **escludendo il proprio namespace** → **0 risultati**. Library isolata.
4. `grep -rn "adventurer_class_states\|CdV\|Cacciatore del Vuoto"` → CdV solo come classe DB (`is_playable=false`), 0 runtime consumers.
5. `pytest tests/backend_r18_4_sealed_integrity_test.py -v` → 6 passed, `36/36 byte-identical`.
6. `pytest tests/effect_engine/ -q` → 284 passed (invariante).
7. `sha256sum /app/memory/PRD.md` → `0eb7477a…089b` invariante pre-append.

**Nessuna scrittura DB · nessun apply · nessun toggle FF · nessuna nuova collection · nessun import runtime aggiunto**.

---

## Sezione 6 · Expedition Lifecycle Discovery (READ-ONLY)

Il lifecycle spedizione live è composto da 3 fasi discrete, tutte gestite dai servizi in `app/expeditions/services.py`, esposti tramite 6 rotte in `app/expeditions/routes.py` (tutte `Depends(get_current_user)`, ownership check via `user_guild_or_404`):

**Fase A · Dispatch (`_dispatch_expedition`, righe 799–1076)**:
- Validazione dungeon gate, team size, class-slug whitelist (guard R18.1.2).
- Snapshot immutabile: `equipment_snapshot`, `traits_snapshot`, `total_power_snapshot`, `equipment_power_snapshot`.
- Calcolo `team_power = compute_team_power(members_for_power)`, `success_chance = compute_success_chance(team_power, dungeon["recommended_power"])` — **AUTORITATIVO** (verdict B2Q01).
- Applicazione threat resolution (ROUND 16.0 Phase 4) → bonus additivo capped ≤95%.
- Insert atomico su `db.expeditions` + `db.expedition_members`, `status="in_progress"`.
- Lock atomico `is_available=false` su avventurieri.

**Fase B · Lazy completion sweep (`complete_due_expeditions` / `_complete_one_expedition`, righe 316–711)**:
- CAS claim idempotente `find_one_and_update({status: "in_progress"}, {$set: {status: "completing"}})`.
- Random roll `final_score = _rng.randint(1, 100)` (`secrets.SystemRandom`).
- `success = final_score <= claimed["success_chance"]` — **AUTORITATIVO**.
- Applicazione XP con moltiplicatori (traits, class-primary-stat multiplier, leader_experience bonus), loot roll, materials roll.
- Terminal state: `status="completed"`, `result_summary`, `result_log`, `completed_at`.

**Fase C · Read/Report (`get_expedition`, `get_last_completed`)**:
- Trigger lazy sweep prima della read (idempotente).
- Build `report_summary + report_steps` (pure builder, no DB write).

**Chiave**: nessuna infrastruttura combat/phase/round esistente — la spedizione è modellata come **"single roll at completion"**, non come **event-driven multi-step**. In coerenza con verdict B2Q09, il class-state runtime resta **shell-only** in RT2-B-2A: nessuna transizione gameplay Mark/Drain/Fragment è autorizzata in questo slice.

---

## Sezione 7 · Runtime Wiring Touchpoints — PM VERDICT B2Q01 APPLIED VERBATIM

**PM Verdict B2Q01 (verbatim)**: `wiring layer = EXPEDITION SERVICE ORCHESTRATION LAYER` · **calcolo corrente resta autoritativo** · ordine 11-step deterministico.

**Ordine 11-step del lifecycle spedizione con shadow wiring RT2-B-2A** (verbatim PM):

1. Auth (JWT verify).
2. User load (`users.find_one({"id": current_user["id"]})`).
3. Adventurers / equipment load (`_load_equipment_for_adventurer`).
4. Runtime calc corrente (`compute_team_power`, `compute_success_chance`, threat resolution) — **AUTORITATIVO**.
5. Test-user + FF eval — evaluated once at expedition lifecycle entry (verdict B2Q07 congelato per operazione).
6. RT2-A shadow evaluation (`runtime_stat_shadow_enabled`) — audit only, no side-effect gameplay.
7. RT2-B state lifecycle (create shell state se `_shadow_wire_allowed`).
8. Prosecuzione legacy (dispatch flow completo, `insert_one` expedition + members, `is_available=false` lock).
9. Risoluzione (lazy sweep + `_complete_one_expedition` runtime corrente autoritativo).
10. Terminalization (state → COMPLETED / CANCELLED / COMPLETED_WITH_FAILURE, verdict B2Q04).
11. Risposta invariata (`expedition_public()` output byte-identico al pre-RT2-B-2A).

**Touchpoint mappati (5 candidati)**:

| # | Location | Operazione | Player-affecting |
|---|---|---|---|
| T1 | `_dispatch_expedition:989-1023` post `insert_one(exp_doc)` | `store.create_state(...)` shell vuoto | NO (shadow only) |
| T2 | `_complete_one_expedition:540-558` post `status="completed"` | `store.expire_state(...)` terminalization COMPLETED | NO |
| T3 | `get_expedition:1136-1174` | `store.get_state(...)` diagnostic-only, no output player | NO |
| T4 | `complete_due_expeditions:719-732` | coperto naturalmente da T2 | NO |
| T5 | `replay_last:1115-1132` | `store.create_state(...)` shell vuoto per nuovo exp_id | NO |

**Fail-safe principle**: ogni touchpoint è try/except non-blocking; fallimento shadow-write emette solo audit warn senza rollback player-visible.

---

## Sezione 8 · Test-User Eligibility Boundary (SERVER-AUTHORITATIVE) — PM VERDICT B2Q06 APPLIED VERBATIM

**PM Verdict B2Q06 (verbatim)**: `test-user eligibility = authenticated server-side user record`, campo `is_test_user` da `users` collection. **Trusted internal context**, non accettato dal client. **Vietati**: email hardcoded / query param / custom header / body flag / frontend override. **Fail closed**: missing user OR missing field OR `!= true` → shadow disabled.

**Evidence empirica (READ-ONLY)** — coerente con verdict:

| Aspetto | Evidenza |
|---|---|
| Fonte primaria | `app/auth/services.py:161-173` — `is_test = email.lower().endswith("@orbus.test")` at registration |
| Persistenza | Campo `users.is_test_user` (boolean, default false) |
| Public exposure | Serializzato in `user_public()` come flag diagnostico |
| Admin toggle | `app/admin/services.py:365-379` CAS guard `{"is_test_user": {"$ne": True}}` |
| Client control | **ZERO** — nessuna rotta pubblica accetta `is_test_user` in body/query/header |
| Consumer server-side | 4 servizi (`guilds`, `chronicle`, `chat`, `admin/tester_tools`) |

**Verdetto Fail-Stop `TEST_USER_ELIGIBILITY_UNDERDEFINED` → `NOT_TRIGGERED`**: boundary sufficiente e conforme al verdict PM B2Q06. Il tester `tester@orbus.test` è il canale legittimo per shadow activation local isolated.

---

## Sezione 9 · Feature Flag Invariance & Activation Ordering — PM VERDICT B2Q07 APPLIED VERBATIM

**PM Verdict B2Q07 (verbatim)**: FF = **server-side startup configuration**. Valutazione **once at expedition lifecycle entry** (**congelata per operazione**). RT2-B-2A può usare `runtime_stat_shadow_enabled=true` e `cdv_transient_state_enabled=true` **SOLO in test/local env**. `runtime_stat_soft_cap_enabled = false` (**soft cap non autoritativo**). Valori mancanti/invalidi → `false`. Nessun aggiornamento dinamico via DB/API.

**Stato attuale (READ-ONLY verified)**:

| Flag ID | Env var | Default | RT2-A runtime-attivabile | Hard-force False in RT2-A |
|---|---|---|---|---|
| `runtime_stat_soft_cap_enabled` | `ORBUS_FLAG_RUNTIME_STAT_SOFT_CAP_ENABLED` | `false` | ✅ | ✗ (soft cap NON autoritativo per verdict B2Q07) |
| `runtime_stat_shadow_enabled` | `ORBUS_FLAG_RUNTIME_STAT_SHADOW_ENABLED` | `false` | ✅ | ✗ |
| `cdv_transient_state_enabled` | `ORBUS_FLAG_CDV_TRANSIENT_STATE_ENABLED` | `false` | ✗ | ✅ (future constant, hard-forced False in RT2-A) |
| `item_effect_engine_enabled` | — | `false` | ✗ | ✅ |
| `cdv_item_hooks_enabled` | — | `false` | ✗ | ✅ |
| `effect_observability_enabled` | — | `false` | ✗ | ✅ |

**Invariante mantenuta in RT2-B-2-P0**: nessun toggle. `feature_flags.py:113-115` continua a hard-forzare `False` per `cdv_transient_state_enabled` finché il PM non ratifichi la sua attivabilità in dispatch futuro (RT2-B-2A gate).

**Rollout post-patch (allineato a verdict B2Q12)**:
1. **STEP 1 · RT2-B-2A** — abilitare `runtime_stat_shadow_enabled=true` + `cdv_transient_state_enabled=true` **SOLO in test/local env** (verdict B2Q07). Scope: shadow read/write + shell state creation.
2. **STEP 2 · RT2-B-2B (`CLASS-STATE TRANSITION FOUNDATION = PLANNED / HOLD`)** — introdurre transizioni Mark/Drain/Fragment (verdict B2Q09).
3. **STEP 3+ HOLD** — activation tester gameplay isolated (deferito, non autorizzato).

---

## Sezione 10 · RT1 Hard-Lock Preservation (verbatim)

Invarianti RT1 **preservati verbatim** in tutte le proposte di questa readiness:

- **Marks**: `active_marks_per_source ≤ 5` · `mark_per_source_target ≤ 1` · `duration_seconds ≤ 10` · `automatic_eviction = false`.
- **Drain**: `own_active_mark_required_at_start = true` · `own_active_mark_required_at_completion = true` · `Drain_consumes_Mark = false` · `one_resolution_per_execution_id = true`.
- **Fragments**: `fragment_count_cap = 5` · `overflow = discarded` · `phase_start_reset = 0` · `phase_end_reset = 0` · `expedition_end_reset = 0` · `focus_bonus_usage_per_segment ≤ 2`.

Codificati in `app/stats/runtime/state_store/models.py:19-23`. RT2-B-2A **non introduce** nuove transizioni gameplay (verdict B2Q09): cabla solo `create_state` + `expire_state` con shell state vuoto. Le semantiche Mark/Drain/Fragment restano hold fino a `RT2-B-2B · CLASS-STATE TRANSITION FOUNDATION = PLANNED / HOLD`.

---

## Sezione 11 · Class-State Integration Semantics (CdV) — PM VERDICT B2Q09 APPLIED VERBATIM

**PM Verdict B2Q09 (verbatim)**: `class gameplay transitions in RT2-B-2A = NONE`. **Solo shell state vuoto**. Mark apply/refresh/expire, Drain start/complete, Fragment gain/spend → gate successivo `RT2-B-2B · CLASS-STATE TRANSITION FOUNDATION = PLANNED / HOLD`.

**Cacciatore del Vuoto (CdV) — evidenza empirica READ-ONLY**:
- Slug canonico: `cacciatore_del_vuoto` (seedato in `round183a_class_migration_prereq_seed.py:52`).
- Attributi DB: `is_playable = false` · `migration_target_only = true`.
- Popolazione: 128 adventurers migrati da `warlock`.
- Whitelist expedition dispatch: `app/expeditions/services.py:887-890`.
- **Zero runtime consumers**: grep `adventurer_class_states` / `CdV` fuori dal namespace `state_store` = 0 risultati.

**Semantica shell-only ratificata (B2Q02 + B2Q09)**:
1. Al dispatch, shell state per ciascun avventuriero della squadra, keyed by `adventurer_id` (verdict PM B0Q03 upstream).
2. `state_version = 1` iniziale (verdict PM B0Q04). `fencing_token = 0`.
3. `runtime_status = ACTIVE` · `expires_at = created_at + 6h` (verdict PM B0Q07).
4. **Shell**: `active_marks = ()` · `active_drain_executions = ()` · `fragment_count = 0` · `focus_bonus_usage = ()` · `processed_event_keys = ()`.
5. **Nessuna transizione gameplay eseguita** in RT2-B-2A.

---

## Sezione 12 · Local Shadow Wiring Model — PM VERDICT B2Q02 APPLIED VERBATIM

**PM Verdict B2Q02 (verbatim)**: state creation **dopo validazione, prima della risoluzione**. Solo se `cdv_transient_state_enabled=true AND is_test_user=true AND Mongo target=localhost allowlisted`. Shell state vuoto (Marchi vuoti, Drenaggi vuoti, Frammenti=0, receipt vuote). **Nessuna transizione gameplay**.

**Modello proposto per RT2-B-2A** (allineato a verdict):

- **State creation @ T1 (`_dispatch_expedition`)** — dopo `_dispatch_expedition` validation (dungeon gate + team size + retired/unassigned guards + level gate) e prima della risoluzione (lazy sweep):
  ```python
  # Coordinated by request-scoped ExpeditionRuntimeCoordinator (B2Q03)
  # After validation, before resolution (B2Q02)
  if await coordinator.shadow_wire_allowed(current_user, guild):
      try:
          initial_state = ExpeditionRuntimeState(
              expedition_id=exp_id,
              state_version=1,
              fencing_token=0,
              created_at=now.isoformat(),
              updated_at=now.isoformat(),
              expires_at=(now + timedelta(hours=6)).isoformat(),
              runtime_status=RuntimeStatus.ACTIVE,
              adventurer_class_states=(),  # SHELL — nessuna transizione (B2Q09)
              processed_event_keys=(),
              last_event_sequence=0,
          )
          await coordinator.create_shell_state(exp_id, initial_state)
      except Exception as exc:
          # Fallback isolation (B2Q08): gameplay preserved, audit WARN
          audit_warn("runtime_state_shadow_failure", expedition_id=exp_id, err=str(exc))
  ```

- **Terminalization @ T2 (`_complete_one_expedition`)** — verdict B2Q04:
  - Success completion → `runtime_status = COMPLETED`.
  - Cancellation → `runtime_status = CANCELLED`.
  - Failure completion → `runtime_status = COMPLETED_WITH_FAILURE`.
  - Failure in shadow terminalize → gameplay response preserved + WARNING audit + orphan lasciato a TTL cleanup.

- **Vincoli architetturali verbatim**:
  - Try/except non-blocking.
  - Nessuna nuova dipendenza sync/blocking sul path critico.
  - Nessuna nuova rotta pubblica.
  - `expedition_public()` output invariante.
  - `user_public()` output invariante.

---

## Sezione 13 · State Lifecycle Foundation — PM VERDICT B2Q04 APPLIED VERBATIM

**PM Verdict B2Q04 (verbatim)**: terminalization → **success = COMPLETED**, **cancellation = CANCELLED**, **failure = COMPLETED_WITH_FAILURE**. Dopo runtime corrente, prima della risposta se tecnicamente possibile. Failure in shadow → gameplay response preserved + WARNING audit + orphan a TTL cleanup. **Vietato**: ritirare rewards, duplicare, ritentare indefinitamente.

**Ciclo di vita minimo per `expedition_runtime_states`**:

| Transizione | Trigger applicativo | Store operation | Terminal state | Note |
|---|---|---|---|---|
| CREATE (initial) | `_dispatch_expedition` post-validation, pre-resolution (B2Q02) | `create_state` shell | ACTIVE | shell vuoto B2Q09 |
| ATTACH (writer) | `RT2-B-2B` reserved | `reserve_writer` | — | HOLD |
| MUTATE (event) | `RT2-B-2B` reserved | `apply_event_once` | — | HOLD |
| RELEASE | `RT2-B-2B` reserved | `release_writer` | — | HOLD |
| TERMINALIZE success | `_complete_one_expedition` post `status="completed"`, success=true | `expire_state` con target `COMPLETED` | COMPLETED | B2Q04 |
| TERMINALIZE cancel | `_complete_one_expedition` cancellation path (non-existent oggi, future) | `expire_state` con target `CANCELLED` | CANCELLED | B2Q04 reserved |
| TERMINALIZE failure | `_complete_one_expedition` post `status="completed"`, success=false | `expire_state` con target `COMPLETED_WITH_FAILURE` | COMPLETED_WITH_FAILURE | B2Q04 |
| DELETE (recovery) | Manual op only | `delete_state` | — | Fuori scope RT2-B-2A |

**In RT2-B-2A solo CREATE + 3 varianti TERMINALIZE** sono cablate. Le altre operazioni restano contract-only.

---

## Sezione 14 · Store Adapter Selection — PM VERDICT B2Q11 APPLIED VERBATIM

**PM Verdict B2Q11 (verbatim)**: adapter lifecycle = **application-scoped dependency**. Requisiti:
- **One adapter per app process**.
- **Existing Mongo client lifecycle** (riutilizzo `AsyncIOMotorClient` singleton).
- **Collection handle injected**.
- **No per-request client**.
- **No startup provisioning writes**.
- **No implicit index/collection creation**.
- **Costruito solo con host+db+collection allowlisted** (verdict B2Q10).
- **Senza flag**: mutation path non invocato.
- **Verifica collection può essere read-only**.

**Decisione ratificata**: `MongoExpeditionRuntimeStateStore` è application-scoped, injected via lifespan-based singleton, wrappato dal `ExpeditionRuntimeCoordinator` request-scoped (B2Q03) per le operazioni per-request.

**FakeExpeditionRuntimeStateStore**: marker `PRODUCTION_USE = FORBIDDEN` verbatim in `fake_store.py:2-3`. Solo test-only.

---

## Sezione 15 · Fencing Token & State Version Handling (recap runtime) — PM VERDICT B2Q03 APPLIED VERBATIM

**PM Verdict B2Q03 (verbatim)**: lease owner = **request-scoped ExpeditionRuntimeCoordinator**. Gestisce lease solo per **create/terminalize/cancel/cleanup**. **No background renewer**. Marchi/Drain/Frammenti in gate successivo (RT2-B-2B).

**Semantica ridotta al minimo in RT2-B-2A**:
- `state_version = 1` al create, invariato durante lifetime.
- `fencing_token = 0` al create (no writer lease necessario per shell state creation).
- Nessun CAS retry loop applicativo richiesto: `create_state` outcomes = `SUCCESS | ALREADY_EXISTS (silent noop)`.
- Nessun background lease renewer (verdict B2Q03).
- Il fencing/state_version machinery diventa rilevante da RT2-B-2B in poi.

---

## Sezione 16 · Event Sequencing at Runtime

**Non-scope in RT2-B-2A**: `apply_event_once` **NON chiamato** dal runtime applicativo (verdict B2Q09 no transitions). Il sequencing server-authoritative (verdict PM B0Q05 upstream) resta contract-only.

**Scope in RT2-B-2B (PLANNED / HOLD)**: eventi combat (mark_applied, drain_started, drain_resolved, fragment_gained, fragment_spent) saranno emessi da event bus in-memory con dedup via `event_id = expedition_id + adventurer_id + phase_id + type + payload_hash`.

---

## Sezione 17 · Idempotency & Retry at Runtime — PM VERDICT B2Q08 APPLIED VERBATIM

**PM Verdict B2Q08 (verbatim)** — fallback isolation policy:
- **Shadow stat failure** → preserva calcolo corrente + audit warning + response unchanged.
- **State creation failure** → preserva gameplay + no class-state execution + no reward linked + audit.
- **Lease/CAS failure** → no partial mutation + no automatic fallback che concede benefici.
- **Terminalization failure** → gameplay preserved + state a TTL + warning.
- **FORBIDDEN**: duplicate reward, partial new-runtime reward, silent granting fallback.

**Idempotency posture RT2-B-2A**:
- `create_state` naturalmente idempotente: duplicate → `ALREADY_EXISTS` silent no-op.
- `expire_state` naturalmente idempotente: duplicate → `DEDUPLICATED_NO_OP`.
- **Retry loop applicativo**: **NO retry loop**. Fallimento → warn log, nessun impatto sul flusso player-visible.

---

## Sezione 18 · Failure Mode Matrix (runtime-wiring) — allineata a B2Q08

12 scenari runtime-wiring:

| # | Scenario | Player-visible impact | Recovery | Reward risk |
|---|---|---|---|---|
| F01 | `create_state` fallisce (Mongo down) | Nessuno | Audit WARN, gameplay procede | ZERO (no reward linked) |
| F02 | `expire_state` fallisce (Mongo down) | Nessuno | TTL sweep interno raccoglie orphan | ZERO |
| F03 | `create_state` timeout | Nessuno | Audit WARN | ZERO |
| F04 | Duplicate `create_state` (retry HTTP) | Nessuno | `ALREADY_EXISTS` silent | ZERO |
| F05 | Test-user boundary check fallisce (Mongo query users) | Nessuno | Fail-closed (return False) | ZERO |
| F06 | FF `cdv_transient_state_enabled` toggled off mid-expedition | Nessuno | Congelato per operazione (B2Q07) | ZERO |
| F07 | State expires mid-expedition (TTL 6h) | Nessuno in RT2-B-2A | N/A (no reads runtime) | ZERO |
| F08 | `shadow_wire_allowed` divergenza (create vs terminalize) | Nessuno | ExpeditionRuntimeCoordinator garantisce coerenza | ZERO |
| F09 | Admin flips `is_test_user=False` mid-flight | Nessuno | Expedition procede, state document TTL cleanup | ZERO |
| F10 | Non-test-user erroneamente rilevato come test-user | **CRITICO in shared prod, N/A local isolated** | Fail-closed + audit alerting | ZERO (RT2-B-2A gameplay-preserving) |
| F11 | State document orphan (create ok, no terminalize) | Nessuno | TTL 6h + 24h post-completion cleanup | ZERO |
| F12 | Concurrent lazy-sweep + explicit report call | Nessuno | CAS store-safe | ZERO |

**Zero reward risk garantito** dalla fallback isolation policy B2Q08.

---

## Sezione 19 · Compatibility Boundary (existing gameplay unchanged)

**Invariante duro**:
- `cdv_transient_state_enabled = false` in produzione fino a RT2-B-2A local ratificato.
- `runtime_stat_shadow_enabled = false` in produzione shared (attivabile solo local test).
- Con flag disattivati → **runtime behavior byte-identical** al pre-RT2-B-2A.
- Gameplay `expedition_public()` output invariante.
- `_dispatch_expedition` output invariante.
- `_complete_one_expedition` output invariante.
- Nessun campo aggiunto a `expedition_public`.
- Nessun campo aggiunto a `user_public`.
- **Calcolo corrente resta autoritativo** (verdict B2Q01).

---

## Sezione 20 · Public API Scope

**Verdetto Fail-Stop `PUBLIC_API_SCOPE_EXPANSION_REQUIRED` → `NOT_TRIGGERED`**.

RT2-B-2A **non richiede nuove rotte pubbliche** (verdict B2Q12 scope). OpenAPI scope invariante rispetto a RT2-B-1B-1 closure. **Public API changes = 0** · **frontend changes = 0**.

---

## Sezione 21 · Observability Plan — PM VERDICT B2Q05 APPLIED VERBATIM

**PM Verdict B2Q05 (verbatim)**: audit destination = **existing server-side structured audit/logging substrate**. **No nuova collection audit** / **no endpoint pubblico** / **no campo risposta** / **no log player-facing**.

**Eventi audit da emettere (verbatim PM)**:
- `runtime_stat_shadow_evaluated`
- `runtime_state_created`
- `runtime_state_terminalized`
- `runtime_state_shadow_failure`
- `runtime_state_cleanup_deferred`

**Campi consentiti (verbatim PM)**: `expedition_id`, `adventurer_id`, `test-user eligibility`, `current/candidate power`, `delta`, `soft-cap applied`, `state version`, `result code`, `duration_ms`.

**Campi VIETATI (verbatim PM)**: `seed RNG`, `intero loadout`, `credenziali`, `payload Mongo completo`.

| Event ID | Trigger | Severity | Sampling |
|---|---|---|---|
| `runtime_stat_shadow_evaluated` | RT2-A shadow evaluation completa (audit only) | INFO | 100% |
| `runtime_state_created` | Shadow `create_state` success | INFO | 100% |
| `runtime_state_terminalized` | Terminalization success (COMPLETED / CANCELLED / COMPLETED_WITH_FAILURE) | INFO | 100% |
| `runtime_state_shadow_failure` | Shadow write/terminalize exception | WARN | 100% |
| `runtime_state_cleanup_deferred` | Terminalization failure → orphan lasciato a TTL | WARN | 100% |

---

## Sezione 22 · Security & Abuse Surface

**Minacce identificate + mitigazioni server-authoritative**:

1. **Client-forged shadow wiring** → impossibile: server-side `_shadow_wire_allowed`, no client parameter (B2Q06).
2. **Test-user impersonation** → mitigato da `is_test_user` server-derived (email suffix + admin CAS toggle).
3. **Cross-guild shadow state write** → `user_guild_or_404` ownership check invariante.
4. **State document poisoning via forged event_id** → N/A in RT2-B-2A (`apply_event_once` non chiamato).
5. **FF override via env manipulation** → memoized `@lru_cache` + hard-force in `feature_flags.py:113-115`.
6. **Reward duplication via shadow retry** → forbidden per B2Q08 policy (no partial reward, no silent granting).
7. **Cross-env leak (shadow write in shared prod)** → mitigato da B2Q10 host+db allowlist (`orbus_r16_rt2b_test`, `orbus_r16_rt2b_it_<unique_run_id>`), vietati `orbus_r16`, `orbus_r16_test`, preview, staging, production.

---

## Sezione 23 · Test Architecture (Planned RT2-B-2A) — allineata a B2Q12

**Test proposti (NON scritti in P0)** — 12 categorie autorizzate per RT2-B-2A (verdict B2Q12):

1. **DI Mongo adapter** — verificare application-scoped singleton (B2Q11).
2. **Request-scoped ExpeditionRuntimeCoordinator** — verificare lifecycle per-request (B2Q03).
3. **RT2-A shadow evaluation** — audit event `runtime_stat_shadow_evaluated`.
4. **Test-user fail-closed** — boundary Mongo error → return False.
5. **FF default-OFF** — no shadow wiring quando FF off.
6. **State creation post-validation** — timing correct rispetto a dungeon gate/team size validation.
7. **Empty CdV class-state init** — shell state vuoto verbatim (B2Q09).
8. **Terminalization** — COMPLETED / CANCELLED / COMPLETED_WITH_FAILURE verbatim (B2Q04).
9. **Audit events server-side** — 5 event id emessi (B2Q05).
10. **Local Mongo integration tests** — solo `orbus_r16_rt2b_it_<unique_run_id>` (B2Q10).
11. **Compatibility + regression tests** — `expedition_public()` invariante, 284 combined regression.
12. **Failure-isolation tests** — shadow failure preserva gameplay + no reward linked (B2Q08).

**Zero test scritti in P0**. Suite completa parte di RT2-B-2A dispatch.

---

## Sezione 24 · Performance Considerations

**Overhead atteso di RT2-B-2A (shadow only)**:
- `create_state` p95 ≤ 25ms (misurato in RT2-B-1B-1 local isolated: **0.21ms**). Overhead trascurabile.
- `expire_state` (terminalize) p95 stimato ≤ 25ms.
- Boundary check p95 stimato ≤ 5ms.
- Overhead totale critical path stimato: **< 30ms** al dispatch, **< 20ms** al completion.
- Try/except async non-blocking preserva latency percepita player.

**Baseline definitiva**: da misurare in RT2-B-2A closure suite (test-perf-benchmark su path critico completo).

---

## Sezione 25 · Rollback & Recovery

**Strategie rollback disponibili per RT2-B-2A**:

1. **FF-off rollback**: `ORBUS_FLAG_CDV_TRANSIENT_STATE_ENABLED=false` + restart backend → shadow wiring inibito. State documents esistenti → TTL sweep.
2. **Code rollback**: revert commit RT2-B-2A → touchpoint ripristinano behavior pre-2A. State documents orphan cleaned by TTL.
3. **DB rollback (local isolated only)**: `db.expedition_runtime_states.drop()` → riprovisioning via `provisioning_command` (RT2-B-1B-1).

**Data loss risk**: **ZERO** (state document transient, nessun dato player persistente).

---

## Sezione 26 · Rollout Ordering (post-patch, allineato B2Q07 + B2Q12)

1. **STEP 1 · RT2-B-2A** (READY-TO-DISPATCH post-closure P0) — LOCAL SHADOW WIRING & STATE LIFECYCLE FOUNDATION.
2. **STEP 2 · RT2-B-2B** (`PLANNED / HOLD`) — CLASS-STATE TRANSITION FOUNDATION (verdict B2Q09).
3. **STEP 3+ HOLD** — shared-env activation / tester gameplay activation (NOT AUTHORIZED per B2Q10).

**Vincolo trasversale**: nessun toggle FF senza dispatch dedicato. Ogni step richiede formal closure del precedente + PM adjudication + baseline chain preservata.

---

## Sezione 27 · First Code Slice Scope (RT2-B-2A) — PM VERDICT B2Q12 APPLIED VERBATIM

**Canonical name**: `R18.6.RV3-IS2-B-P2B-RT2-B-2A · LOCAL SHADOW WIRING & STATE LIFECYCLE FOUNDATION`.

**Authorized scope 12 item (verbatim PM verdict B2Q12)**:
1. DI Mongo adapter.
2. Request-scoped ExpeditionRuntimeCoordinator.
3. RT2-A shadow evaluation.
4. Test-user fail-closed.
5. FF default-OFF.
6. State creation post-validation.
7. Empty CdV class-state init.
8. Terminalization (COMPLETED / CANCELLED / COMPLETED_WITH_FAILURE).
9. Audit events server-side.
10. Local Mongo integration tests.
11. Compatibility + regression tests.
12. Failure-isolation tests.

**Application-scope**: 1 nuovo modulo `app/expeditions/runtime_shadow_hooks.py` (o naming equivalente) + 1 nuovo modulo per `ExpeditionRuntimeCoordinator` + 3 call site modification in `app/expeditions/services.py` + lifespan-based store injection + audit event registration + suite test.

---

## Sezione 28 · Explicit Exclusions from RT2-B-2A — PM VERDICT B2Q12 APPLIED VERBATIM

**Fuori scope RT2-B-2A (verbatim PM)**:
- Authoritative soft-cap (soft cap NON autoritativo per B2Q07).
- **Mark / Drain / Fragment transitions** (deferite a `RT2-B-2B · CLASS-STATE TRANSITION FOUNDATION = PLANNED / HOLD`).
- Class rewards.
- Effect engine (deferito RT2-C).
- Proc / duration / cooldown.
- Item hooks (deferiti RT2-E).
- Legendary.
- **Public API changes**.
- **Frontend**.
- **Shared-env writes**.
- **Tester gameplay activation**.

---

## Sezione 29 · Fail-Stop Register (4)

**Valutazione esplicita** dei 4 fail-stop del dispatch:

| Fail-Stop ID | Stato | Motivazione |
|---|---|---|
| `EXPEDITION_LIFECYCLE_WIRING_UNDERDEFINED` | **NOT_TRIGGERED** | Wiring layer ratificato B2Q01 (11-step orchestration). 5 touchpoint mappati. |
| `TEST_USER_ELIGIBILITY_UNDERDEFINED` | **NOT_TRIGGERED** | Ratificato B2Q06 verbatim: server-authoritative, fail-closed. 4 consumer coerenti. |
| `RUNTIME_ADAPTER_TARGET_CONFLICT` | **NOT_TRIGGERED** | Ratificato B2Q11: application-scoped dependency, MongoExpeditionRuntimeStateStore unico target. |
| `PUBLIC_API_SCOPE_EXPANSION_REQUIRED` | **NOT_TRIGGERED** | Ratificato B2Q12 exclusions: public API changes = 0, frontend = 0. |

**Tutti e 4 i fail-stop restano `NOT_TRIGGERED` post-patch**.

---

## Sezione 30 · Risk Register

| Rischio | Severity | Mitigazione |
|---|---|---|
| R01 · Mongo down su shadow write | LOW | Try/except non-blocking (B2Q08) |
| R02 · Test-user boundary bypass in prod shared | MEDIUM | B2Q10 host+db allowlist locale only |
| R03 · FF hard-force removal accidentale | MEDIUM | Adjudication PM esplicito, code review |
| R04 · State document orphan buildup | LOW | TTL 6h + 24h (verdict B0Q07) |
| R05 · Performance overhead | LOW | p95 < 30ms critical path, non-blocking |
| R06 · Application-scoped adapter singleton race | LOW | B2Q11 one adapter per process |
| R07 · PII in state document | RESOLVED | Contract esclude PII/JWT/RNG (B2Q05 fields whitelist) |
| R08 · Concurrent replay double-create | LOW | `ALREADY_EXISTS` silent idempotent |
| R09 · Test-user toggle race mid-flight | LOW | FF+eligibility congelati per operazione (B2Q07) |
| R10 · Test coverage gap | MEDIUM | 12 test categorie richieste in RT2-B-2A closure |
| R11 · Reward duplication via shadow retry | RESOLVED | B2Q08 forbid partial/duplicate/silent granting |
| R12 · Shadow write shared env leak | RESOLVED | B2Q10 allowlist locale only |

---

## Sezione 31 · Governance Evidence Snapshot

- `lore_meta.py` SHA `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` · **INVARIANT** (verificato).
- Baseline chain **12/12 byte-identical** (Sezione 3).
- `sealed integrity tests = 6 passed` · `sealed artifacts = 36/36 byte-identical` (verificato).
- `effect_engine tests = 284/284 passed` (verificato — nessuna regressione).
- Application code modifications = **0** in P0.
- OpenAPI / Registry / item-gen / FF activation / runtime wiring = **0**.
- Mongo writes / new collections / new indices = **0**.
- Frontend changes = **0**.
- Public API changes = **0**.
- PRD delta = **1 append idempotente** (blocco `RT2-B-2-P0 · CLOSED`) in questa Phase 1 closure.
- `NEW SEAL = NO`.
- RT2-A (38 file) + RT2-B-1A (14 file) + RT2-B-1B-1 (16 file) **unchanged**.

---

## Sezione 32 · PM Open Questions (12 · B2Q01 → B2Q12 · PM RATIFIED VERBATIM 2026-02)

Tutte 12 le B2Q sono ora `PM_RATIFIED_VERBATIM_2026_02`. Dettaglio completo (verdict verbatim) nel JSON companion `section_32_pm_open_questions`. Sintesi:

- **B2Q01** = `EXPEDITION SERVICE ORCHESTRATION LAYER` · calcolo corrente autoritativo · 11-step order.
- **B2Q02** = state creation dopo validazione, prima della risoluzione · shell vuoto · no gameplay transitions.
- **B2Q03** = request-scoped `ExpeditionRuntimeCoordinator` · no background renewer.
- **B2Q04** = terminalization `COMPLETED / CANCELLED / COMPLETED_WITH_FAILURE` · gameplay preserved on failure.
- **B2Q05** = existing server-side audit substrate · 5 event id · fields whitelist + forbidden list.
- **B2Q06** = server-side `users.is_test_user` · fail-closed · no client control.
- **B2Q07** = server-side startup FF · frozen once at lifecycle entry · soft-cap NON autoritativo.
- **B2Q08** = fallback isolation policy · zero reward duplication/partial/silent granting.
- **B2Q09** = `class gameplay transitions in RT2-B-2A = NONE` · `RT2-B-2B = PLANNED / HOLD`.
- **B2Q10** = LOCALHOST ISOLATED ONLY · allowlist `orbus_r16_rt2b_test` + `orbus_r16_rt2b_it_<unique_run_id>`.
- **B2Q11** = application-scoped dependency · injected collection · no per-request client.
- **B2Q12** = 12 authorized scope items + 11 exclusions (verbatim in Sezioni 27+28).

**Auto-ratification count = 0**. Ratifica formalmente in mano al PM verbatim direttiva orchestrator.

---

## Sezione 33 · GO/HOLD Recommendation

**RT2-B-2-P0**: `READY FOR FORMAL CLOSURE / PM-LOCKED`. 12/12 B2Q **RATIFIED VERBATIM PM 2026-02**. 4/4 fail-stop `NOT_TRIGGERED`. Governance invariante. Baseline chain 12/12 preservata.

**RT2-B-2A**: `READY-TO-DISPATCH` (Phase 2 orchestrator dispatch separato). Scope canonico + esclusioni ratificate.

**RT2-B-2B**: `PLANNED / HOLD` (verdict B2Q09).

**Shared-environment provisioning + tester gameplay activation**: `LOCK · NOT AUTHORIZED`.

---

## Sezione 34 · Explicit STOP

Formal readiness plan `RT2-B-2-P0` PATCHED + PM-RATIFIED completo. Autorizzata in questa Phase 1:
- **1 patch** dei 2 artefatti RT2-B-2-P0 (MD + JSON) — questa operazione.
- **3 nuovi artefatti** di closure (MD, JSON, manifest §31) — pipeline immediata post-patch.
- **1 append PRD** idempotente (blocco `RT2-B-2-P0 · CLOSED`).

Nessuna scrittura ulteriore autorizzata: nessuna modifica applicativa, nessuna scrittura DB, nessun toggle FF, nessuna nuova rotta.

In attesa di:
- Dispatch orchestrator separato per Phase 2 `RT2-B-2A · LOCAL SHADOW WIRING & STATE LIFECYCLE FOUNDATION`.

**`STRICT STOP · Phase 1 documentale · fine`**.

---

**Fine documento** · Italian_only · DOCUMENTAL_ONLY · RT2-B-2-P0 PATCHED · PM-RATIFIED · SHA Policy §31 · STRICT STOP
