# R18.6.RV3-IS2-B-P2B-RT2-B-2-P0 · Local Runtime Wiring & Class-State Integration Readiness Plan

**Regime**: `DOCUMENTAL_ONLY · READ-ONLY DISCOVERY · Italian_only · NO APPLY · SHA Policy §31 · STRICT STOP`
**Gate ID**: `R18.6.RV3-IS2-B-P2B-RT2-B-2-P0 · LOCAL RUNTIME WIRING & CLASS-STATE INTEGRATION READINESS PLAN`
**Ancoraggio invariante**: `lore_meta.py` SHA256 = `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`
**Fonte upstream**: `R18.6.RV3-IS2-B-P2B-RT2-B-1B-1 · CLOSED · PM-LOCKED`
**PRD reference (pre-append)**: SHA256 = `0eb7477abdcda64ac1ca3c6d3272a04a089bad186b260f62ff7f13a1cb9a089b` (post-RT2-B-1B-1, INVARIANT in questo gate — nessun append P0)
**Status**: `DRAFT · READ-ONLY · PM_OPEN_QUESTIONS_EMITTED · NO AUTO-RATIFICATION`
**Data**: 2026-02 (UTC)

---

## Sezione 1 · Executive Summary

Il gate `RT2-B-2-P0` produce, **strettamente documentale e read-only**, il piano di readiness per la Phase successiva `RT2-B-2A · LOCAL SHADOW WIRING & STATE LIFECYCLE FOUNDATION`: il primo cablaggio del `MongoExpeditionRuntimeStateStore` al lifecycle applicativo delle spedizioni, in modalità **shadow / non-player-affecting**, confinato al **test-user boundary server-authoritative** (`users.is_test_user=True`), e sotto **feature flag `cdv_transient_state_enabled = false`** e `runtime_stat_shadow_enabled = false` (invarianti in P0). Nessuna modifica applicativa, DB, OpenAPI, FF, runtime wiring, item-gen, Registry, Mongo write autorizzata in questo gate: unico output = 2 deliverable (`.md` + `.json`) + 12 PM Open Questions **non auto-ratificate**. La state-store library è stand-alone (0 import fuori dal proprio namespace, verificato via grep). La chain state → gameplay è mediata dal contratto `ExpeditionRuntimeStateStore` (11 operazioni astratte, `create_state · get_state · compare_and_update · apply_event_once · reserve_writer · renew_writer_lease · release_writer · expire_state · delete_state · get_version · health_check`) ed è funzionalmente pronta ma richiede adjudication PM su 12 aree critiche (B2Q01–B2Q12) prima di autorizzare qualsiasi slice di codice successore.

**Recommendation P0**: `RT2-B-2-P0 CLOSED / PM-LOCKED` dopo ratifica di 12/12 B2Q · **RT2-B-2A HOLD / CONDITIONAL_GO_AFTER_ADJUDICATION**.

---

## Sezione 2 · Scope

**In scope (P0 documentale)**: mappatura lifecycle spedizione live · identificazione touchpoint per shadow-wire dello state store · caratterizzazione del boundary test-user server-authoritative · ricognizione class-state semantics per Cacciatore del Vuoto (CdV) · proposta di rollout 4-step con FF invarianti · 4 fail-stop (uno critico: TEST_USER_ELIGIBILITY) · 12 B2Q non-auto-ratificate · failure matrix runtime-wiring · risk register · scope canonico e esclusioni di `RT2-B-2A`.

**Out of scope (P0 vietato)**: modifica di qualsiasi file `.py` applicativo (expedition / adventurer / auth / core) · nuova collection / index / provisioning (`RT2-B-1B` gate è closed, provisioning shared-env resta vietato) · nuova rotta `/api/*` · OpenAPI mutation · FF activation · Registry v3 · item-gen · Mongo write in shared env · shadow read/write live · code slicing di `RT2-B-2A` · closure manifest · PRD append P0. Nessun nuovo sigillo (`NEW SEAL = NO`).

---

## Sezione 3 · Governance

- Regime `DOCUMENTAL_ONLY · READ-ONLY DISCOVERY · Italian_only`.
- `lore_meta.py` invariant · anchor SHA `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`.
- Baseline chain **12/12 byte-identical**: `IS2-A · IS2-B-P1 · IS2-B-P1-N1 · IS2-B-P2A · IS2-B-P2B-1 · IS2-B-P2B-RT1 · IS2-B-P2B-RT2-P0 · IS2-B-P2B-RT2-A · IS2-B-P2B-RT2-B-P0 · IS2-B-P2B-RT2-B-1A · IS2-B-P2B-RT2-B-1B-P0 · IS2-B-P2B-RT2-B-1B-1`.
- `sealed integrity tests = 6 passed` · `sealed artifacts = 36/36 byte-identical` (verificato in questo gate).
- `effect_engine tests = 284/284 passed` (verificato in questo gate — invariante).
- `NEW SEAL = NO` (P0 draft, non produce artefatti sigillabili).
- PRD SHA pre-append: `0eb7477abdcda64ac1ca3c6d3272a04a089bad186b260f62ff7f13a1cb9a089b`. **PRD delta in P0 = 0 append** (draft not-yet-ratified).
- SHA Policy §31 stretta: gli SHA dei 2 deliverable di questo P0 **NON sono embedded** dentro i file stessi — vengono comunicati **solo** nel chat report finale.
- Closure manifest §31: **non prodotto in P0** (draft phase). Sarà prodotto al momento della formal closure post-ratifica PM.

---

## Sezione 4 · Source Chain

| # | Upstream artifact | Status | Rilevanza |
|---|---|---|---|
| 1 | `RT2-B-P0` — State Store & Multi-Worker Architecture | PM-LOCKED | Contract origine (11 op astratte, Model A lease+fencing, Option 2 Mongo collection) |
| 2 | `RT2-B-1A` — Store Contract & Non-Wired Adapter Foundation | PM-LOCKED | 14 file library stand-alone (`interface.py`, `models.py`, `fake_store.py`, `mongo_adapter.py`) |
| 3 | `RT2-B-1B-P0` — Mongo Provisioning Readiness Plan | PM-LOCKED | 31 sezioni + 12/12 B1BQ ratificati |
| 4 | `RT2-B-1B-1` — Local Isolated Provisioning & Real Adapter Validation | PM-LOCKED | 16 nuovi file (4 provisioning + 12 test), 57/57 real Mongo test PASS, 284 combined |
| 5 | `RT2-A` — CdV & Effect Engine (24 code + 14 test) | PM-LOCKED | Effect engine backbone, FF invarianti |
| 6 | `RT1` — Runtime Stat & Effect Semantics Specification | PM-LOCKED | Hard-lock invariants (Marks ≤5 · Fragments ≤5 · Drain semantics) |
| 7 | `app/expeditions/routes.py` (139 righe) | READ-ONLY EVIDENCE | 6 rotte pubbliche `/api/expeditions/*` |
| 8 | `app/expeditions/services.py` (1378 righe) | READ-ONLY EVIDENCE | `_dispatch_expedition` · `_complete_one_expedition` · `complete_due_expeditions` |
| 9 | `app/auth/services.py` (324 righe) | READ-ONLY EVIDENCE | `is_test_user` derivato server-side da suffisso email `@orbus.test` |
| 10 | `app/admin/services.py` (grep results) | READ-ONLY EVIDENCE | Admin toggle `is_test_user` (CAS guard, server-only) |
| 11 | `app/stats/runtime/state_store/*` (7 file · 1653 righe) | READ-ONLY EVIDENCE | Library stand-alone, 0 import fuori namespace |
| 12 | `app/stats/runtime/feature_flags.py` (138 righe) | READ-ONLY EVIDENCE | Hard-force False su `cdv_transient_state_enabled` |
| 13 | Dispatch PM `RT2-B-2-P0` (message 101 orchestrator) | RATIFYING DIRECTIVE | Genera questa readiness |

---

## Sezione 5 · Discovery Methodology

Metodologia strettamente **grep / cat / read-only view** su `/app/backend/**/*.py`. Nessun `find_one` / `insert` / `update` verso Mongo · nessun `pytest` non-idempotente · nessuna esecuzione uvicorn locale. Sette query eseguite:

1. `grep -rn "is_test_user" /app/backend/app/**/*.py` → 30+ occorrenze, tutte server-authoritative (auth, admin, chronicle, chat, guilds).
2. `grep -rn "expedition" /app/backend/app --include="*.py" -l` → 30+ file, servizi core mappati.
3. `grep -rn "state_store\|from app.stats.runtime" /app/backend/app` **escludendo il proprio namespace** → **0 risultati**. Library isolata.
4. `grep -rn "adventurer_class_states\|CdV\|Cacciatore del Vuoto" /app/backend/app` → CdV presente solo come classe DB (`cacciatore_del_vuoto`, `is_playable=false`), 0 runtime consumers.
5. `pytest tests/backend_r18_4_sealed_integrity_test.py -v` → 6 passed, `36/36 byte-identical`, `lore_meta.py` invariant.
6. `pytest tests/effect_engine/ -q` → 284 passed (RT2-A 136 + RT2-B-1A 91 + RT2-B-1B-1 57).
7. `sha256sum /app/memory/PRD.md` → `0eb7477a…089b` invariante rispetto al post-RT2-B-1B-1.

**Nessuna scrittura DB · nessun apply · nessun toggle FF · nessuna nuova collection · nessun import runtime aggiunto**.

---

## Sezione 6 · Expedition Lifecycle Discovery (READ-ONLY)

Il lifecycle spedizione live è composto da 3 fasi discrete, tutte gestite dai servizi in `app/expeditions/services.py`, esposti tramite 6 rotte in `app/expeditions/routes.py` (tutte `Depends(get_current_user)`, ownership check via `user_guild_or_404`):

**Fase A · Dispatch (`_dispatch_expedition`, righe 799–1076)**:
- Validazione dungeon gate, team size, class-slug whitelist (guard R18.1.2).
- Snapshot immutabile: `equipment_snapshot`, `traits_snapshot`, `total_power_snapshot`, `equipment_power_snapshot`.
- Calcolo `team_power = compute_team_power(members_for_power)`, `success_chance = compute_success_chance(team_power, dungeon["recommended_power"])`.
- Applicazione threat resolution (`compute_threat_resolution`, ROUND 16.0 Phase 4) → bonus additivo capped ≤95%.
- Insert atomico su `db.expeditions` + `db.expedition_members`, `status="in_progress"`.
- Lock atomico `is_available=false` su avventurieri.
- Bump sticky `guild.max_team_power_ever` via `$max`.

**Fase B · Lazy completion sweep (`complete_due_expeditions` / `_complete_one_expedition`, righe 316–711)**:
- CAS claim `find_one_and_update({status: "in_progress"}, {$set: {status: "completing"}})` (idempotente).
- Random roll `final_score = _rng.randint(1, 100)` (`secrets.SystemRandom`).
- `success = final_score <= claimed["success_chance"]`.
- Applicazione XP con moltiplicatori (traits, class-primary-stat multiplier, leader_experience bonus), loot roll, materials roll.
- Update `db.adventurers` (XP + level-up loop), `db.guilds.gold`, `db.inventory_items` (upsert item + materiali).
- Achievement/quest/contract/seasonal hooks (all best-effort, try/except).
- Terminal state: `status="completed"`, `result_summary`, `result_log`, `completed_at`.

**Fase C · Read/Report (`get_expedition`, `get_last_completed`)**:
- Trigger lazy sweep prima della read (idempotente).
- Build `report_summary + report_steps` (pure builder, no DB write).
- Deriva `guild_prestige_delta` + `milestones` READ-ONLY.

**Chiave**: **nessuna infrastruttura combat/phase/round esistente** — la spedizione è modellata come **"single roll at completion"**, non come **event-driven multi-step**. Il class-state runtime (Marks/Drain/Fragments) NON è ancora invocato in gameplay reale. Questo è un vincolo architetturale critico per RT2-B-2A: il primo wiring **non introduce combat semantics**, cabla solo la coppia `create_state` (all'inizio della Fase A) + `expire_state` (al termine della Fase B), **in ambito shadow** e **solo per test-user**.

---

## Sezione 7 · Runtime Wiring Touchpoints (candidati per RT2-B-2A)

Cinque touchpoint identificati per il **primo cablaggio proposto** (analisi documentale, NON implementazione):

| # | Location | Operazione candidata | Read/Write | Player-affecting | Note |
|---|---|---|---|---|---|
| T1 | `_dispatch_expedition` righe 989–1023 (post `insert_one(exp_doc)`) | `store.create_state(expedition_id, initial_state)` | Shadow write | **NO** (shadow only) | Boundary: solo se `is_test_user=True` e FF `cdv_transient_state_enabled` |
| T2 | `_complete_one_expedition` righe 540–558 (post `status="completed"` update) | `store.expire_state(expedition_id)` | Shadow write | **NO** | Terminal state su store, TTL 24h retention |
| T3 | `get_expedition` righe 1136–1174 | `store.get_state(expedition_id)` | Shadow read | **NO** | Diagnostica solo, no output player-facing |
| T4 | `complete_due_expeditions` righe 719–732 (sweep loop) | Nessuna (naturalmente coperto da T2) | — | — | — |
| T5 | `replay_last` righe 1115–1132 (`is_replay=True`) | Nuovo T1 per replay expedition_id | Shadow write | **NO** | Identico a T1, `is_replay=true` marker in metadata |

**Fail-safe design principle**: **ogni touchpoint è try/except-wrapped e non-blocking**. Un fallimento shadow-write **NON blocca** dispatch/completion/report. Emette solo un audit event `runtime_state_shadow_write_failed` (livello WARN) senza rollback della spedizione player-visible.

**Boundary duro proposto**:
```python
async def _shadow_wire_allowed(db, current_user, guild) -> bool:
    if not feature_flags.is_enabled("cdv_transient_state_enabled"):
        return False
    # test-user boundary: server-authoritative
    owner_id = guild.get("owner_user_id") or guild.get("user_id")
    owner = await db.users.find_one({"id": owner_id}, {"_id": 0, "is_test_user": 1})
    return bool((owner or {}).get("is_test_user"))
```

Questo boundary è **strict server-side**: nessun parametro client, nessun header, nessun query-string override.

---

## Sezione 8 · Test-User Eligibility Boundary (SERVER-AUTHORITATIVE)

**Evidence empirica (READ-ONLY)** su come `is_test_user` viene attualmente determinato:

| Aspetto | Evidenza |
|---|---|
| Fonte principale | `app/auth/services.py:161-173` — `is_test = email.lower().endswith("@orbus.test")` |
| Persistenza | Campo `users.is_test_user` (boolean, default false) |
| Public exposure | Serializzato in `user_public()` come feature diagnostica (`app/auth/services.py:47`) |
| Modifiche | **Admin-only**, via `app/admin/services.py:365-379` CAS guard `{"is_test_user": {"$ne": True}}` |
| Client control | **ZERO** — nessuna rotta pubblica accetta `is_test_user` in body/query/header |
| Consumer server-side | `app/guilds/services.py:75-83` · `app/chronicle/services.py:95` · `app/chat/services.py:130-137` · `app/admin/tester_tools.py:51-91` |
| Filter policy | Test-users esclusi da leaderboard / chronicle / chat cross-user (in prod) |

**Verdetto Fail-Stop `TEST_USER_ELIGIBILITY_UNDERDEFINED` → `NOT_TRIGGERED`**: il boundary è **server-authoritative**, non client-controllable, e già consumato coerentemente da 4 servizi in produzione. Non esistono email hardcoded, non esistono parametri client per override, non esistono query-string per bypass. Il boundary è sufficiente per RT2-B-2A shadow wiring senza ulteriore hardening applicativo.

**Raccomandazione (non-ratificata)**: **riutilizzare l'attuale meccanismo verbatim** in RT2-B-2A tramite helper server-side non-esportato (`_shadow_wire_allowed` esemplificato in Sezione 7). Il tester `tester@orbus.test` già presente in `/app/memory/test_credentials.md` è **il canale legittimo** per activation isolata.

---

## Sezione 9 · Feature Flag Invariance & Activation Ordering

**Stato attuale (READ-ONLY verified)**:

| Flag ID | Env var | Default | RT2-A runtime-attivabile | Hard-force False in RT2-A |
|---|---|---|---|---|
| `runtime_stat_soft_cap_enabled` | `ORBUS_FLAG_RUNTIME_STAT_SOFT_CAP_ENABLED` | `false` | ✅ | ✗ |
| `runtime_stat_shadow_enabled` | `ORBUS_FLAG_RUNTIME_STAT_SHADOW_ENABLED` | `false` | ✅ | ✗ |
| `cdv_transient_state_enabled` | `ORBUS_FLAG_CDV_TRANSIENT_STATE_ENABLED` | `false` | ✗ | ✅ (future constant) |
| `item_effect_engine_enabled` | — | `false` | ✗ | ✅ |
| `cdv_item_hooks_enabled` | — | `false` | ✗ | ✅ |
| `effect_observability_enabled` | — | `false` | ✗ | ✅ |

**Invariante mantenuta in RT2-B-2-P0**: nessun toggle. `feature_flags.py:113-115` continua a hard-forzare `False` per `cdv_transient_state_enabled` finché il PM **non ratifichi** la sua attivabilità in un dispatch futuro (RT2-B-2A o successivo).

**Ordine 4-step raccomandato (proposto, NON ratificato)**:
1. **STEP 1 · RT2-B-2A** — abilitare `runtime_stat_shadow_enabled` in ambiente test-only, **con FF `cdv_transient_state_enabled` ancora hard-forced False**. Scope: shadow read/write dello state store per test-user, no CdV semantics live.
2. **STEP 2 · RT2-B-2B (ipotetico)** — rimuovere hard-force di `cdv_transient_state_enabled` dal codice (patch minima a `feature_flags.py` per spostarlo da `RT2_FUTURE_CONSTANTS` a `RT2_A_RUNTIME_ATTIVABILE`), mantenendo default `false`. **NO player-facing effects ancora**.
3. **STEP 3 · RT2-B-2C (ipotetico)** — attivare CdV class-state semantics runtime **solo per test-user + FF on**. Marks/Drain/Fragments cablati a livelli combat mock (test-only).
4. **STEP 4 · RT2-B-2D (ipotetico)** — activation controlled rollout per tester gameplay (email `@orbus.test`), sempre gated FF + `is_test_user`.

**Nessuno di questi 4 step è autorizzato in P0**. Il P0 richiede solo che il PM adjudichi B2Q07 (activation ordering).

---

## Sezione 10 · RT1 Hard-Lock Preservation (verbatim)

I seguenti invarianti RT1 restano **preservati verbatim** in tutte le proposte di questa readiness. Nessuna deviazione è autorizzata in RT2-B-2A o successive senza dispatch dedicato:

- **Marks**: `active_marks_per_source ≤ 5` · `mark_per_source_target ≤ 1` · `duration_seconds ≤ 10` · `automatic_eviction = false`.
- **Drain**: `own_active_mark_required_at_start = true` · `own_active_mark_required_at_completion = true` · `Drain_consumes_Mark = false` · `one_resolution_per_execution_id = true`.
- **Fragments**: `fragment_count_cap = 5` · `overflow = discarded` · `phase_start_reset = 0` · `phase_end_reset = 0` · `expedition_end_reset = 0` · `focus_bonus_usage_per_segment ≤ 2`.

Questi cap sono già codificati in `app/stats/runtime/state_store/models.py:19-23` e sono enforced store-side via CAS. RT2-B-2A **non introduce** nuova semantica di Marks/Drain/Fragments live: cabla solo `create_state` + `expire_state` come skeleton lifecycle. La semantica di combat resta hold fino a step successivi.

---

## Sezione 11 · Class-State Integration Semantics (CdV)

**Cacciatore del Vuoto (CdV) — evidenza empirica**:
- Slug canonico: `cacciatore_del_vuoto` (seedato in `round183a_class_migration_prereq_seed.py:52`).
- Attributi DB: `is_playable = false` · `migration_target_only = true`.
- Popolazione: 128 adventurers migrati da `warlock` (script `round183c_migration_apply.py:61`).
- Whitelist expedition dispatch (safety guard R18.1.2): `cacciatore_di_mostri`, `cacciatore_del_vuoto` ammessi via `_R18_MIGRATION_TARGET_WHITELIST` in `app/expeditions/services.py:887-890`.
- **Zero runtime consumers**: grep di `adventurer_class_states` / `CdV` fuori dal namespace `state_store` restituisce solo commenti e script di migration.

**Semantica di integrazione proposta (NON ratificata)**:
1. Al dispatch, il `_shadow_wire_allowed` boundary determina se popolare `adventurer_class_states` per **ciascun avventuriero della squadra**, keyed by `adventurer_id` (verdict PM B0Q03).
2. Il `state_version` iniziale = 1 (verdict PM B0Q04).
3. `fencing_token` iniziale = 0 (nessun writer alla creazione).
4. `runtime_status = ACTIVE` · `expires_at = created_at + 6h` (verdict PM B0Q07, TTL inactivity).
5. Al completion (`_complete_one_expedition`), transizione a `runtime_status = EXPIRED` con `expires_at = completed_at + 24h` (retention post-completion).
6. Nessun campo CdV-specifico persistito al di fuori dello schema esistente (`active_marks · active_drain_executions · fragment_count · resource_segment_id · focus_bonus_usage`).

---

## Sezione 12 · Local Shadow Wiring Model (SCOPE-LOCKED)

**Modello proposto per RT2-B-2A**:

- **Shadow write @ T1 (`_dispatch_expedition`)**:
  ```python
  if await _shadow_wire_allowed(db, current_user, guild):
      try:
          initial_state = ExpeditionRuntimeState(
              expedition_id=exp_id,
              state_version=1,
              fencing_token=0,
              created_at=now.isoformat(),
              updated_at=now.isoformat(),
              expires_at=(now + timedelta(hours=6)).isoformat(),
              runtime_status=RuntimeStatus.ACTIVE,
              adventurer_class_states=(),  # bootstrap vuoto — nessuna CdV live
          )
          await state_store.create_state(exp_id, initial_state)
      except Exception as exc:
          logger.warning("runtime_state_shadow_write_failed exp_id=%s err=%s", exp_id, exc)
  ```
- **Shadow expire @ T2 (`_complete_one_expedition`)**:
  ```python
  if await _shadow_wire_allowed_by_expedition(db, exp_id):
      try:
          await state_store.expire_state(exp_id)
      except Exception:
          pass
  ```
- **Shadow read @ T3 (`get_expedition`)** — opzionale, coperto da FF separato o `runtime_stat_shadow_enabled`. Ritorna diagnostica **NON esposta nel payload player-facing** (solo audit log).

**Vincoli architetturali verbatim**:
- Try/except non-blocking (nessun rollback della spedizione player-visible).
- Nessuna nuova dipendenza sync/blocking sul path critico.
- Nessuna nuova rotta pubblica.
- Nessun output visibile al player (`expedition_public` invariante).

---

## Sezione 13 · State Lifecycle Foundation (create/attach/complete/expire)

Ciclo di vita minimo proposto per lo state document `expedition_runtime_states`:

| Transizione | Trigger applicativo | Store operation | State version | Fencing token |
|---|---|---|---|---|
| CREATE (initial) | `_dispatch_expedition` (post `insert_one`) | `create_state` | `1` | `0` (no writer) |
| ATTACH (writer) | Reserved for RT2-B-2C (combat semantics) | `reserve_writer` | invariato | `+1` (increment su nuova acquisizione) |
| MUTATE (event) | Reserved for RT2-B-2C (Marks/Drain/Fragments) | `apply_event_once` | `+1` per event | invariato |
| RELEASE | Reserved for RT2-B-2C | `release_writer` | invariato | invariato |
| EXPIRE (completion) | `_complete_one_expedition` (post `status="completed"`) | `expire_state` | invariato | invariato |
| DELETE (recovery) | Manual op only | `delete_state` | — | — |

**In RT2-B-2A solo CREATE + EXPIRE** sono cablate. Le altre 5 operazioni restano nel contract ma **non chiamate dal runtime** (test-only fino a RT2-B-2C+).

---

## Sezione 14 · Store Adapter Selection (Fake vs Mongo)

**Decisione ratificata upstream (RT2-B-1B-1)**: `MongoExpeditionRuntimeStateStore` è l'unica implementazione autorizzata per il runtime applicativo. `FakeExpeditionRuntimeStateStore` è **`PRODUCTION_USE = FORBIDDEN`** (marker verbatim in `fake_store.py:2-3`), usable solo in fixture/unit/contract test.

**Punto aperto B2Q02**: come istanziare `MongoExpeditionRuntimeStateStore` nel runtime applicativo? Opzioni identificate:

- **OPZIONE A · lifespan-based injection** (analogo a `db` singleton in `app/core/database.py`): istanziare `store = MongoExpeditionRuntimeStateStore(collection=db.expedition_runtime_states)` in `lifespan.py` startup, espore via dependency injection FastAPI.
- **OPZIONE B · lazy factory per-request**: creare il store on-demand nei servizi, con lifecycle per-request.
- **OPZIONE C · module-level singleton**: creare il store a livello modulo in `app.stats.runtime.state_store`, riferire via import.

**Raccomandazione (non-ratificata)**: **OPZIONE A** — coerente con il pattern `db` singleton già usato in `app/core/database.py`, minimizza il churn architetturale, evita per-request overhead. Adjudication PM richiesto.

---

## Sezione 15 · Fencing Token & State Version Handling (recap runtime)

Nel modello RT2-B-2A (`create_state + expire_state` only), la semantica fencing/state_version è ridotta al minimo:

- `state_version = 1` al create, invariato durante lifetime (`expire_state` non richiede CAS su `state_version` per B0Q04 → `expire_state` è una transizione terminale CAS su `runtime_status ∉ terminal`, non su `state_version`).
- `fencing_token = 0` al create, invariato (nessun writer lease).
- Nessuna CAS retry loop applicativo richiesto in RT2-B-2A (solo `ALREADY_EXISTS` come possible outcome di `create_state`, gestito silently).

Il fencing/state_version machinery diventa rilevante da RT2-B-2C in poi (quando Marks/Drain/Fragments diventano live).

---

## Sezione 16 · Event Sequencing at Runtime

**Non-scope in RT2-B-2A**: `apply_event_once` non è chiamato dal runtime applicativo in RT2-B-2A. Il sequencing server-authoritative (verdict PM B0Q05) resta contract-only.

**Scope in RT2-B-2C (ipotetico)**: eventi combat (mark_applied, drain_started, drain_resolved, fragment_gained, fragment_spent) saranno emessi da un event bus in-memory con dedup via `event_id = expedition_id + adventurer_id + phase_id + type + payload_hash`. Adjudication PM richiesto (B2Q08).

---

## Sezione 17 · Idempotency & Retry at Runtime

**RT2-B-2A idempotency posture**:
- `create_state` è naturalmente idempotente: duplicate create → `CasResultCode.ALREADY_EXISTS`, treated as silent no-op (già completato da un altro worker o retry HTTP).
- `expire_state` è naturalmente idempotente: duplicate expire → `DEDUPLICATED_NO_OP`.

**Retry policy applicativa (non-blocking)**: **NO retry loop**. Fallimento shadow-write → warning log, nessun impatto sul flusso spedizione player-visible.

---

## Sezione 18 · Failure Mode Matrix (runtime-wiring)

12 scenari runtime-wiring analizzati (dettaglio completo nel JSON companion `section_18_failure_matrix`):

| # | Scenario | Player-visible impact | Recovery |
|---|---|---|---|
| F01 | `create_state` fallisce (Mongo down) | Nessuno (try/except) | Log warn, expedition procede |
| F02 | `expire_state` fallisce (Mongo down) | Nessuno | TTL sweep prenderà via `expires_at` |
| F03 | `create_state` timeout | Nessuno | Log warn, expedition procede |
| F04 | Duplicate `create_state` (retry HTTP) | Nessuno | `ALREADY_EXISTS` silent |
| F05 | Test-user boundary check fallisce (Mongo query) | Nessuno | Boundary defaults to False (fail-closed) |
| F06 | FF `cdv_transient_state_enabled` toggled off mid-expedition | Nessuno | Shadow write skipped, expedition ok |
| F07 | State expires mid-expedition (TTL 6h) | Nessuno in RT2-B-2A (no reads) | N/A |
| F08 | `_shadow_wire_allowed_by_expedition` diverge da `_shadow_wire_allowed` | Nessuno | Design garantisce coerenza (owner check) |
| F09 | Migration di test-user (admin flips is_test_user=False) mid-flight | Nessuno | Expedition completa, state document TTL cleanup |
| F10 | Non-test-user erroneamente rilevato come test-user | **CRITICO** in produzione shared, N/A local isolated | Fail-closed check + audit alerting |
| F11 | State document orphan (create_state ok, no expire) | Nessuno | TTL 6h + 24h post-completion garantisce cleanup |
| F12 | Concurrent lazy-sweep + explicit report call | Nessuno | Store è thread/concurrent-safe via CAS |

---

## Sezione 19 · Compatibility Boundary (existing gameplay unchanged)

**Invariante duro**:
- `cdv_transient_state_enabled = false` in produzione fino a RT2-B-2C ratificato.
- `runtime_stat_shadow_enabled = false` in produzione shared (attivabile solo local test).
- Con flag disattivati → **runtime behavior byte-identical** al pre-RT2-B-2A.
- Gameplay `expedition_public()` output invariante · `_dispatch_expedition` output invariante · `_complete_one_expedition` output invariante.
- Nessun campo aggiunto a `expedition_public`.
- Nessun campo aggiunto a `user_public`.
- Nessuna dipendenza sync bloccante su `MongoExpeditionRuntimeStateStore` nel critical path.

---

## Sezione 20 · Public API Scope

**Verdetto Fail-Stop `PUBLIC_API_SCOPE_EXPANSION_REQUIRED` → `NOT_TRIGGERED`**.

RT2-B-2A **non richiede nuove rotte pubbliche**. Il primo cablaggio è confinato ai servizi interni. OpenAPI scope invariante rispetto a RT2-B-1B-1 closure.

**Punto aperto B2Q10**: la diagnostica shadow (view state document di una spedizione test-user) richiede una rotta admin-only? **Raccomandazione (non-ratificata)**: NO in RT2-B-2A. Se necessaria in fasi future, sarà rotta `/api/admin/runtime-state/{expedition_id}` con guard admin + `is_test_user` filter.

---

## Sezione 21 · Observability Plan

Eventi audit da emettere in RT2-B-2A (verdict PM RT2-B-P0 §31, sottoinsieme applicabile):

| Event ID | Trigger | Severity | Sampling |
|---|---|---|---|
| `runtime_state_created` | Shadow `create_state` success | INFO | 100% |
| `runtime_state_shadow_write_failed` | Shadow `create_state` exception | WARN | 100% |
| `runtime_state_expired` | Shadow `expire_state` success | INFO | 100% |
| `runtime_state_shadow_expire_failed` | Shadow `expire_state` exception | WARN | 100% |

**Nessun dato sensibile** loggato: no email, no JWT, no PII, no boss metadata. Solo `expedition_id`, `event_type`, `runtime_status`, `timestamp`.

---

## Sezione 22 · Security & Abuse Surface

**Minacce identificate + mitigazioni server-authoritative** (in linea con RT2-B-P0 §30):

1. **Client-forged shadow wiring**: impossibile — no client parameter, `_shadow_wire_allowed` è server-side.
2. **Test-user impersonation**: mitigato dalla registrazione server-authoritative di `is_test_user` (email suffix + admin CAS toggle).
3. **Cross-guild shadow state write**: ownership check via `user_guild_or_404` prima di ogni operazione (invariante applicativa).
4. **State document poisoning via forged event_id**: N/A in RT2-B-2A (no `apply_event_once` chiamato dal runtime).
5. **FF override via env manipulation**: mitigato dalla lettura memoizzata `@lru_cache` in `feature_flags.py:86` + hard-force in `feature_flags.py:113-115`.

---

## Sezione 23 · Test Architecture (Planned RT2-B-2A)

**Test proposti (NON scritti in P0)**:

- **T-2A-01** · Unit: `_shadow_wire_allowed` restituisce True solo se `FF=on + is_test_user=True`.
- **T-2A-02** · Unit: `_shadow_wire_allowed` fail-closed su Mongo error nella lookup `users`.
- **T-2A-03** · Integration: `_dispatch_expedition` con `is_test_user=True` + FF on → `expedition_runtime_states` document creato.
- **T-2A-04** · Integration: `_dispatch_expedition` con `is_test_user=False` → **nessun** documento in `expedition_runtime_states`.
- **T-2A-05** · Integration: `_complete_one_expedition` con test-user → runtime_status = EXPIRED.
- **T-2A-06** · Integration: FF off → `expedition_runtime_states` documenti = 0.
- **T-2A-07** · Regression: 284 test effect_engine invariati + tutti i test spedizione existing invariati.
- **T-2A-08** · Chaos: Mongo down durante shadow write → expedition player-visible unchanged.
- **T-2A-09** · Concurrency: dispatch parallelo (2 test-user) → 2 documenti separati, isolati.
- **T-2A-10** · Boundary: admin toggles is_test_user off mid-flight → expedition procede senza rollback.

**Zero test scritti in P0**. Approvazione test-suite è parte di RT2-B-2A dispatch.

---

## Sezione 24 · Performance Considerations

**Overhead atteso di RT2-B-2A (shadow only)**:
- `create_state` p95 ≤ 25ms (misurato in RT2-B-1B-1 local isolated: **0.21ms**). Overhead trascurabile.
- `expire_state` non misurato in isolation ma è single-document CAS: p95 stimato ≤ 25ms.
- Test-user boundary check: 1 `find_one({"id": user_id}, {"is_test_user": 1})` → p95 stimato ≤ 5ms su collection `users` con `id UNIQUE` index.

**Impatto atteso su path critico**: **< 30ms totali** al dispatch, con try/except non-blocking. **< 20ms** al completion. Trascurabile per l'esperienza player.

**Baseline missing**: non esistono ancora misure locali reali di `create_state + expire_state` **dentro** al lifecycle spedizione. Adjudication PM richiesto per definire performance acceptance in RT2-B-2A (B2Q11).

---

## Sezione 25 · Rollback & Recovery

**Strategie rollback disponibili per RT2-B-2A** (mai eseguite in P0):

1. **FF-off rollback**: setting `ORBUS_FLAG_CDV_TRANSIENT_STATE_ENABLED=false` + restart backend → shadow wiring immediatamente inibito. State documents esistenti restano nel DB, TTL sweep li rimuove.
2. **Code rollback**: revert del commit di RT2-B-2A → `_shadow_wire_allowed` non esiste più, tutti i touchpoint ripristinano behavior pre-2A. State documents esistenti restano nel DB (harmless orphan, TTL cleanup).
3. **DB rollback** (locale isolated only): `db.expedition_runtime_states.drop()` → tutti gli state documents distrutti. Riprovisioning richiede re-esecuzione di `provisioning_command` (RT2-B-1B-1).

**Data loss risk**: **ZERO** (state document è transient, non contiene dati player persistenti).

---

## Sezione 26 · Rollout Ordering (4-step)

**Proposto (NON ratificato)**:

1. **STEP 1 · Enable shadow read/write in test env** — FF `runtime_stat_shadow_enabled=true` in local test only. Verifica end-to-end del lifecycle create→expire. Coverage: T-2A-* test suite.
2. **STEP 2 · Enable transient class-state in test env** — Rimozione hard-force di `cdv_transient_state_enabled` in `feature_flags.py` (spostamento da `RT2_FUTURE_CONSTANTS` a `RT2_A_RUNTIME_ATTIVABILE`). Default resta `false`. Adjudication PM richiesto.
3. **STEP 3 · Activate CdV combat semantics in tests** — Marks/Drain/Fragments cablati a livello combat mock (RT2-B-2C). Test-only, no production preview.
4. **STEP 4 · Tester gameplay activation isolated** — Rollout per tester `@orbus.test` in ambiente isolato. Adjudication PM finale + monitoring.

**Vincolo trasversale**: **nessun toggle FF senza dispatch dedicato**. Ogni step richiede formal closure del precedente + PM adjudication + baseline chain preservata.

---

## Sezione 27 · First Code Slice Scope (RT2-B-2A · PROPOSED, NON ratificato)

**Canonical name proposto**: `R18.6.RV3-IS2-B-P2B-RT2-B-2A · LOCAL SHADOW WIRING & STATE LIFECYCLE FOUNDATION`.

**Authorized scope (proposta)**:
- Aggiunta di 1 modulo `app/expeditions/runtime_shadow_hooks.py` con `_shadow_wire_allowed` + `_shadow_create_state` + `_shadow_expire_state`.
- 3 call site modifications in `app/expeditions/services.py`: uno in `_dispatch_expedition` (post `insert_one`), uno in `_complete_one_expedition` (post `status="completed"`), uno in `replay_last` (analogo a dispatch).
- **NO** modifica a `_shadow_wire_allowed` come rotta pubblica.
- **NO** modifica a `expedition_public()`.
- **NO** modifica a `user_public()`.
- Aggiunta di lifespan-based injection del `store` singleton in `app/core/lifespan.py` (OPZIONE A raccomandata).
- Suite test T-2A-01 → T-2A-10 (10 test).
- Audit event registration (`runtime_state_created`, `runtime_state_expired`, `_shadow_*_failed`).

**File touched estimate**: 3-5 nuovi + 2-3 esistenti modificati (services + lifespan).

---

## Sezione 28 · Explicit Exclusions from RT2-B-2A

**Fuori scope RT2-B-2A (deferred a RT2-B-2C o successivi)**:
- Marks/Drain/Fragments live semantics.
- Combat phase/round infrastructure.
- Event bus / event emission runtime.
- `apply_event_once` chiamato dal runtime.
- `reserve_writer` / `renew_writer_lease` / `release_writer` chiamati dal runtime.
- Public API expansion.
- Player-facing UI su runtime state.
- Shared-environment provisioning (RT2-B-1B lock).
- Registry v3 / item-gen generation.
- CdV re-activation (`is_playable=true`).

---

## Sezione 29 · Fail-Stop Register (4)

**Valutazione esplicita** dei 4 fail-stop del dispatch:

| Fail-Stop ID | Stato | Motivazione |
|---|---|---|
| `EXPEDITION_LIFECYCLE_WIRING_UNDERDEFINED` | **NOT_TRIGGERED** | Lifecycle 3-fasi (Dispatch/Sweep/Report) è completamente mappato con 5 touchpoint candidati (Sezione 7). Boundary shadow-only è definito. |
| `TEST_USER_ELIGIBILITY_UNDERDEFINED` | **NOT_TRIGGERED** | `is_test_user` è **server-authoritative** (email suffix `@orbus.test` a registration, admin CAS toggle, persistito in `users`). No client parameter/header/query-string. 4 servizi consumer confermano coerenza. |
| `RUNTIME_ADAPTER_TARGET_CONFLICT` | **NOT_TRIGGERED** | `MongoExpeditionRuntimeStateStore` unica implementazione autorizzata (RT2-B-1B-1 lock). `FakeExpeditionRuntimeStateStore` marker `PRODUCTION_USE = FORBIDDEN`. Adjudication PM richiesta per instantiation pattern (B2Q02) ma target è univoco. |
| `PUBLIC_API_SCOPE_EXPANSION_REQUIRED` | **NOT_TRIGGERED** | RT2-B-2A non richiede nuove rotte pubbliche. OpenAPI scope invariante rispetto a RT2-B-1B-1 closure. Nessuna rotta admin-only richiesta in P2A. |

**Tutti e 4 i fail-stop sono NOT_TRIGGERED**. Il gate P0 può produrre readiness senza escalation critica al PM.

---

## Sezione 30 · Risk Register

| Rischio | Severity | Mitigazione |
|---|---|---|
| R01 · MongoDB down su shadow write durante dispatch | LOW | Try/except non-blocking, expedition procede. Audit warn. |
| R02 · Test-user boundary bypass in produzione shared | MEDIUM | RT2-B-2A confinato a local isolated. Shared provisioning HOLD. |
| R03 · FF hard-force removal accidentale in produzione | MEDIUM | Adjudication PM esplicito per STEP 2. Code review obbligatoria. |
| R04 · State document orphan buildup | LOW | TTL 6h inactivity + 24h post-completion. `expire_state` idempotent. |
| R05 · Performance overhead peggiora player latency | LOW | p95 stimato < 30ms su path critico. Try/except async non-blocking. |
| R06 · Instantiation pattern OPZIONE A introduce lifespan tightening | LOW_MEDIUM | Adjudication B2Q02. Analogo esistente `db` singleton. |
| R07 · CdV runtime state contains sensitive PII | RESOLVED | Schema esclude PII/JWT/RNG per contract (RT2-B-P0 §30). |
| R08 · Concurrent replay double-create | LOW | `create_state` returns `ALREADY_EXISTS` silent — idempotent. |
| R09 · Test-user toggle race mid-flight | LOW | Boundary check al dispatch; toggle successivo non retro-influisce. |
| R10 · Runtime wiring introduces test coverage gap | MEDIUM | Suite T-2A-01→10 richiesta in RT2-B-2A closure gate. |

---

## Sezione 31 · Governance Evidence Snapshot

- `lore_meta.py` SHA `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` · **INVARIANT** (verificato in questo gate).
- Baseline chain **12/12 byte-identical** (Sezione 3).
- `sealed integrity tests = 6 passed` · `sealed artifacts = 36/36 byte-identical` (verificato).
- `effect_engine tests = 284/284 passed` (verificato — nessuna regressione).
- Application code modifications = **0**.
- OpenAPI / Registry / item-gen / FF activation / runtime wiring = **0**.
- Mongo writes / new collections / new indices = **0**.
- Frontend changes = **0**.
- PRD delta = **0 append in P0** (draft phase). PRD SHA invariante `0eb7477a…089b`.
- `NEW SEAL = NO`.

---

## Sezione 32 · PM Open Questions (12 · B2Q01 → B2Q12 · NO AUTO-RATIFICATION)

Ogni domanda include: `question_id`, `evidence`, `options`, `agent_recommendation`, `affected_files`, `gameplay_impact`, `DB_impact`, `test_impact`, `blocking`.

**B2Q01 · Instantiation pattern del `MongoExpeditionRuntimeStateStore` runtime**
- **evidence**: `app/core/database.py:9` singleton `AsyncIOMotorClient`. `app/core/lifespan.py` esistente per startup. `mongo_adapter.py` accetta collection injected.
- **options**: (A) lifespan-based singleton injection · (B) lazy factory per-request · (C) module-level singleton.
- **agent_recommendation**: A — coerente con pattern `db` singleton, minimo churn.
- **affected_files**: `app/core/lifespan.py`, nuovo helper `app/expeditions/runtime_shadow_hooks.py`.
- **gameplay_impact**: nessuno con FF off.
- **DB_impact**: nessuno in RT2-B-2-P0. In RT2-B-2A dipende da B1BQ03 (provisioning locale).
- **test_impact**: T-2A-03 · T-2A-06 · T-2A-09.
- **blocking**: SI per RT2-B-2A dispatch.

**B2Q02 · Boundary check semantics: fail-closed vs fail-open su Mongo error nella lookup `users`**
- **evidence**: `app/guilds/services.py:75-83` esegue `find_one({"id": user_id}, {"is_test_user":1, "email":1})` in modo simile.
- **options**: (A) fail-closed (return False su exception) · (B) fail-open (return True per continuare shadow) · (C) fail-open con audit event WARN.
- **agent_recommendation**: A — sicurezza prima di ogni cosa. Un DB error non deve espandere il boundary.
- **affected_files**: `app/expeditions/runtime_shadow_hooks.py`.
- **gameplay_impact**: nessuno.
- **DB_impact**: nessuno.
- **test_impact**: T-2A-02.
- **blocking**: SI per RT2-B-2A dispatch.

**B2Q03 · Guild owner_user_id vs current_user["id"] check**
- **evidence**: `app/guilds/services.py:75` verifica `owner_user_id`. `_dispatch_expedition` riceve `guild` dict validato.
- **options**: (A) usare `guild["owner_user_id"]` · (B) usare `current_user["id"]` (equivalente per single-owner guilds) · (C) verificare entrambi coincidono.
- **agent_recommendation**: A — coerente con pattern esistente in guilds/services.py.
- **affected_files**: `app/expeditions/runtime_shadow_hooks.py`.
- **gameplay_impact**: nessuno con FF off.
- **DB_impact**: nessuno.
- **test_impact**: T-2A-01.
- **blocking**: SI.

**B2Q04 · Shadow write asincrono vs sincrono nel critical path**
- **evidence**: `_dispatch_expedition` è già `async`, `await store.create_state(...)` è naturale. Overhead p95 ≤ 25ms (RT2-B-1B-1 misurato 0.21ms).
- **options**: (A) async await inline · (B) `asyncio.create_task` fire-and-forget · (C) task queue (Redis/Celery — non presente).
- **agent_recommendation**: A per RT2-B-2A. B è tentante ma introduce race su TTL cleanup se completion arriva prima della create.
- **affected_files**: `app/expeditions/services.py`.
- **gameplay_impact**: potenziale +25ms p95 sul dispatch. Trascurabile.
- **DB_impact**: 1 create per dispatch (test-user only).
- **test_impact**: T-2A-03, T-2A-08 (chaos).
- **blocking**: SI.

**B2Q05 · Shadow write al `replay_last` (is_replay=true)**
- **evidence**: `_dispatch_expedition(is_replay=True)` produce nuova expedition_id. Naturalmente coperto da T1.
- **options**: (A) trattare come dispatch normale (create_state su nuovo exp_id) · (B) skip shadow write per replay.
- **agent_recommendation**: A — replay è un dispatch full-fledged. Ogni exp_id merita il proprio state.
- **affected_files**: nessuno aggiuntivo (T1 già copre).
- **gameplay_impact**: nessuno.
- **DB_impact**: 1 create per replay.
- **test_impact**: potrebbe richiedere T-2A-11 (replay).
- **blocking**: NO (default A è sicuro).

**B2Q06 · Expire timing: al primo `_complete_one_expedition` o dopo tutto il post-completion sweep**
- **evidence**: `_complete_one_expedition:540-558` update `status="completed"`. Successivi hooks (achievements, quests, seasonal) sono try/except best-effort.
- **options**: (A) expire dopo `status="completed"` update · (B) expire alla fine di tutti gli hooks · (C) expire alla prima read dello state.
- **agent_recommendation**: A — semantica pulita. Post-completion hooks non richiedono state runtime.
- **affected_files**: `app/expeditions/services.py`.
- **gameplay_impact**: nessuno.
- **DB_impact**: 1 update per completion.
- **test_impact**: T-2A-05.
- **blocking**: SI.

**B2Q07 · Activation ordering 4-step (Sezione 26)**
- **evidence**: FF invarianti attuali. 4 step proposti.
- **options**: (A) 4-step come proposto · (B) 3-step (fusione step 2+3) · (C) 5-step (aggiungere step 0 = solo lifespan wiring senza shadow write).
- **agent_recommendation**: A. Ogni step ha una closure gate distinta, minimize risk.
- **affected_files**: dipende da step.
- **gameplay_impact**: STEP 4 produce first player-facing side-effect.
- **DB_impact**: STEP 1 avvia writes locali test-only.
- **test_impact**: 10 test per RT2-B-2A, TBD per successivi step.
- **blocking**: SI per rollout roadmap.

**B2Q08 · Event bus architecture (deferred a RT2-B-2C, decisione ora?)**
- **evidence**: nessun event bus esistente. `apply_event_once` è contract-only.
- **options**: (A) in-memory event bus per-process · (B) Mongo change stream · (C) library esterna (kombu, dramatiq).
- **agent_recommendation**: A per RT2-B-2C. Coerente con stack single-worker preview.
- **affected_files**: modulo nuovo `app/stats/runtime/event_bus.py` (in RT2-B-2C).
- **gameplay_impact**: nessuno in RT2-B-2A.
- **DB_impact**: nessuno diretto (event_receipt scritto tramite `apply_event_once`).
- **test_impact**: TBD RT2-B-2C.
- **blocking**: NO per RT2-B-2A. **BLOCKING per RT2-B-2C**.

**B2Q09 · TTL 6h inactivity vs completion timing**
- **evidence**: verdict PM B0Q07 = `6h inactivity TTL · 24h post-completion retention`.
- **options**: (A) usare 6h + 24h come verdict PM · (B) allineare TTL a `expedition.completes_at` (varia per dungeon) · (C) 24h flat per tutti.
- **agent_recommendation**: A — verdict PM già ratificato in RT2-B-P0.
- **affected_files**: `app/expeditions/runtime_shadow_hooks.py`.
- **gameplay_impact**: nessuno.
- **DB_impact**: TTL index sweep interno Mongo.
- **test_impact**: T-2A-07 (regression TTL).
- **blocking**: SI (deve rispettare verdict PM upstream).

**B2Q10 · Admin diagnostic endpoint su runtime state**
- **evidence**: nessun endpoint esistente.
- **options**: (A) nessun endpoint in RT2-B-2A · (B) `GET /api/admin/runtime-state/{expedition_id}` admin-only · (C) endpoint dev-only gated da APP_ENV.
- **agent_recommendation**: A. Ogni endpoint nuovo richiede OpenAPI scope expansion (`PUBLIC_API_SCOPE_EXPANSION_REQUIRED` triggered).
- **affected_files**: nessuno.
- **gameplay_impact**: nessuno.
- **DB_impact**: nessuno.
- **test_impact**: nessuno.
- **blocking**: NO (default A conservativo).

**B2Q11 · Performance acceptance threshold per RT2-B-2A**
- **evidence**: baseline `create_state = 0.21ms local isolated` (RT2-B-1B-1).
- **options**: (A) p95 ≤ 25ms (verdict PM RT2-B-P0 §33) · (B) p95 ≤ 10ms (10x safety margin) · (C) p95 ≤ 5ms (in linea con existing services).
- **agent_recommendation**: A (verdict PM upstream). Threshold conservativo.
- **affected_files**: test suite T-2A-*.
- **gameplay_impact**: latency delta trascurabile.
- **DB_impact**: nessuno diretto.
- **test_impact**: 1 test perf-benchmark.
- **blocking**: NO se A adottato verbatim.

**B2Q12 · Test-user gameplay activation (STEP 4) — quando?**
- **evidence**: 1 test-user seedato (`tester@orbus.test`) in `/app/memory/test_credentials.md`. Attualmente nessun'attivazione runtime CdV.
- **options**: (A) STEP 4 solo dopo RT2-B-2C stable · (B) STEP 4 dopo RT2-B-2A per validare shadow flow live · (C) STEP 4 skip, tester continues con class attivi non-CdV.
- **agent_recommendation**: A. STEP 4 è per attivazione CdV live end-to-end, richiede combat semantics ready.
- **affected_files**: nessuno in P0.
- **gameplay_impact**: STEP 4 produce first player-facing CdV activation.
- **DB_impact**: `db.adventurer_classes.update({slug:"cacciatore_del_vuoto"}, {$set:{is_playable:True}})` in ambiente isolato.
- **test_impact**: end-to-end suite tester gameplay.
- **blocking**: NO per RT2-B-2A. **BLOCKING per activation roadmap**.

---

## Sezione 33 · GO/HOLD Recommendation

**RT2-B-2-P0**: `READY_FOR_PM_ADJUDICATION`. 12/12 B2Q emesse senza auto-ratificazione. 4/4 fail-stop `NOT_TRIGGERED`. Governance invariante. Baseline chain 12/12 preservata.

**RT2-B-2A**: `HOLD · CONDITIONAL_GO_AFTER_ADJUDICATION`. Dispatch autorizzabile solo dopo:
1. Ratifica PM di 12/12 B2Q.
2. Chiusura formale di questo `RT2-B-2-P0` con manifest §31 esterno.
3. PRD append idempotente (1 blocco `RT2-B-2-P0 · CLOSED`).
4. Confirmed baseline chain 13/13 byte-identical dopo closure.

**Shared-environment provisioning**: `LOCK · NOT_AUTHORIZED_UNTIL_RT2-B-2D+`.

---

## Sezione 34 · Explicit STOP

Formal readiness plan `RT2-B-2-P0` completo. Nessuna scrittura ulteriore autorizzata:
- Nessuna modifica applicativa.
- Nessuna scrittura DB.
- Nessun toggle FF.
- Nessuna nuova rotta.
- Nessun closure manifest in P0 (draft).
- Nessun PRD append in P0 (draft).

In attesa di:
1. Ratifica PM verbatim delle 12 B2Q.
2. Dispatch orchestrator per formal closure `RT2-B-2-P0`.
3. Dispatch orchestrator per `RT2-B-2A · LOCAL SHADOW WIRING & STATE LIFECYCLE FOUNDATION` (Phase 2).

**`STRICT STOP · Phase P0 documentale · fine`**.

---

**Fine documento** · Italian_only · DOCUMENTAL_ONLY · RT2-B-2-P0 DRAFT · SHA Policy §31 · STRICT STOP
