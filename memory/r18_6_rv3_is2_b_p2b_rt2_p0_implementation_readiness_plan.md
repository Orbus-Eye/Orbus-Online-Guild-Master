# R18.6.RV3-IS2-B-P2B-RT2-P0 · Implementation Readiness & Change Plan (PATCHED · PM-RATIFIED)

**Regime**: `DOCUMENTAL_ONLY · READ-ONLY DISCOVERY · NO_APPLY · Italian_only`
**Author role**: Documental agent (PM-directed)
**Dispatch (patch)**: Messaggio 114 — RT2-P0 Patch (integrazione 10 P0Q verdicts) + Formal Closure + PRD Append (Phase 1)
**Data patch**: 2026-02 (UTC)
**Ancoraggio invariante**: `lore_meta.py` SHA256 = `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`
**Sezioni totali**: 40/40 (ordine PM-vincolato)
**Stato**: `PM-RATIFIED · CLOSED · PM-LOCKED`

> **AVVERTENZA GOVERNANCE**: Documento **documentale**. Nessuna modifica al codice, nessun DB write, nessuna migration, nessuna generazione Registry, nessun apply runtime. Ogni gate RT2-A..E richiede dispatch PM esplicito successivo (RT2-A: `CONDITIONAL GO — awaiting Phase 2 dispatch`; RT2-B..E: `HOLD`).

---

## 1. Executive Summary

RT2-P0 chiude la readiness documentale per la traduzione di RT1 in codice. Con i verdetti PM ratificati (Messaggio 114), il piano introduce **la separazione architetturale netta**:
- **`STATELESS FOUNDATION` (RT2-A)** — implementabile, gestisce solo `pure computation` + `snapshot immutabile` + `shadow diagnostica`. Multi-worker safe by design.
- **`STATEFUL EFFECT RUNTIME` (RT2-B/C)** — non ancora production-ready. Richiede uno store cross-worker (contratto astratto `ExpeditionRuntimeStateStore` — definito, non implementato).

**Recommendation finale post-ratifica**: **`RT2-P0 CLOSED · RT2-A CONDITIONAL GO`** — in attesa di dispatch Phase 2 (RT2-A code). RT2-B/C/D/E rimangono `HOLD`. `Phase 2B item assignment = HOLD`. `Registry v3 = NOT AUTHORIZED`.

**10/10 P0Q risolte** verbatim dal PM. **0 fail-stop deterministici**. `TRANSIENT_STATE_DEPLOYMENT_CONFLICT` = `LATENT FOR RT2-B/C · NOT APPLICABLE TO RT2-A`. `PERFORMANCE_BASELINE_MISSING` = `BLOCKING FOR RT2-A CLOSURE · non blocking for initial implementation work` (contratto relative-baseline approvato).

**Invarianti RT1 preservate**: soft cap Int=100 con `post-cap effective return = 0.50`, dex=GENERIC_BASE_POWER_ONLY, combined proc cap=45%, Marks 5/source, 1/source-target, durata ≤10s, Fragments cap=5, Drain requires own Mark & does not consume, effect persistence=transient only, PvP default disabled, DB migration=not required.

---

## 2. Scope

### In-scope RT2-P0 (documental, patched)
- 10/10 P0Q verdicts integrati verbatim
- Architettura stateless/stateful separation
- RT2-A first code gate definito con file-change boundary + exclusions esplicite
- RT2-B/C hold rationale (multi-worker store contract abstract)
- 6 feature flag proposti (aggiornato da 5), tutti server-side default OFF
- Performance contract relative-baseline (P0Q07)
- Audit tiered sampling (P0Q09)
- Rollout 8 fasi (aggiornato da 7), RT2-A autorizza solo steps 1-3
- Shadow evaluation approved for RT2-A only, campi diagnostici minimi verbatim
- Compatibility contract (flags OFF → runtime behavior unchanged)
- Snapshot loadout campi minimi verbatim
- Atomicity RT2-A error rules verbatim
- Test matrix RT2-A obbligatoria
- Soft-cap boundary cases verbatim (99/100/101/105/200)

### Out-of-scope RT2-P0
- Qualsiasi modifica ai sorgenti runtime
- Qualsiasi DB write / migration / Registry / item generation
- OpenAPI changes
- Autorizzazione a RT2-A code start (arriva in Phase 2 dispatch separato)
- Autorizzazione a RT2-B..E
- Riapertura RT1 / P2B-1 / P2A / P1-N1 / IS2-B P1 / IS2-A

---

## 3. Governance

### 3.1 Regime attivo Phase 1
- `DOCUMENTAL_ONLY` · `READ-ONLY DISCOVERY` · `NO_APPLY` · `Italian_only`
- SHA Policy §31 assoluta: manifest own SHA = NOT EMBEDDED; SHA dichiarate solo in chat report
- Sealed integrity gate: `pytest backend/tests/backend_r18_4_sealed_integrity_test.py` → `6 passed / 36 byte-identical`
- `NEW SEAL = NO` (sigilli restano 36)
- Baseline invariance: IS2-A (8) · IS2-B P1 (4) · P1-N1 (3) · P2A (5) · P2B-1 (5) · RT1 (5) = **30 artefatti byte-identical**
- PRD append idempotente: esattamente **1 blocco RT2-P0 CLOSED**
- `lore_meta.py` SHA invariant
- `RT2-P0 sezioni = 40/40` invariant
- `JSON parse = PASS` invariant

### 3.2 Application status atteso post-Phase 1
| Superficie | Δ |
|---|---:|
| backend code | 0 |
| frontend code | 0 |
| openapi | 0 |
| db_writes | 0 |
| migrations | 0 |
| new_seals | 0 |
| registry_generation | 0 |
| registry_apply | 0 |
| item_generation | 0 |
| env | 0 |

### 3.3 Autorizzazioni successive
- Phase 2 dispatch (RT2-A code) → previsto post-verifica Phase 1 (sigilli 36/36, PRD append=1, baseline byte-identical)
- RT2-B..E → dispatch PM esplicito successivo, ognuno con proprio verdict gate

---

## 4. Source Chain

Catena di autorità normativa (30 artefatti PM-locked + RT2-P0 patched):

1. **IS2-A** (8 artefatti · PM-locked)
2. **IS2-B Phase 1** (4 artefatti · PM-locked)
3. **IS2-B P1-N1** (3 artefatti · PM-locked)
4. **IS2-B Phase 2A** (5 artefatti · PM-locked)
5. **IS2-B P2B-1** (5 artefatti · Model A-T · PM-locked)
6. **IS2-B P2B-RT1** (5 artefatti · 45/45 sezioni · 15/15 RTQ · PM-locked)
7. **IS2-B P2B-RT2-P0** (2 artefatti plan + 3 artefatti closure · **PM-ratified · CLOSED · PM-LOCKED** in Phase 1)

Sealed source layer: 36 file byte-identical, mai toccati.

---

## 5. Current Architecture (Read-Only Discovery)

### 5.1 Layout backend (invariato)
Domain-driven monorepo: ~60 domini bounded context sotto `/app/backend/app/<domain>/` (routes.py + services.py + schemas.py per dominio). Composizione via `create_app()` in `app/core/app_factory.py` con `lifespan` in `app/core/lifespan.py`.

Ancora integrità: `/app/backend/app/content/lore_meta.py` (SEALED · SHA `a18f708b…65b8f`).

### 5.2 Deployment topology (osservato)
- Preview supervisor: `uvicorn server:app --workers 1 --reload`
- **Single worker**. `RESOLVED_BY_SCOPE_BOUNDARY` per RT2-A (pure/stateless/deterministic → multi-worker safe by design)
- Produzione: topologia non documentata in codebase → **irrelevant per RT2-A** grazie a scope boundary; blocca solo `RT2-B/C production activation`

### 5.3 Auth / DB / lifespan (invariati)
- JWT HS256 + CSRF double-submit
- Motor async client + UUID4 public ids
- Startup: `ensure_indexes` + 20+ seed idempotenti + `logger.info('Orbus backend ready')`

---

## 6. Runtime Entry Points

Endpoints critici (invariati rispetto al piano originale):

| Endpoint | Service | Ruolo RT2 |
|---|---|---|
| `POST /api/expeditions` | `_dispatch_expedition` | Snapshot loadout runtime (RT2-A entry) |
| `GET /api/expeditions/{id}` | `get_expedition` | Detail + report (RT2-D exposure decisione P0Q06 → NONE per RT2-A) |
| `POST /api/expeditions/replay-last` | `replay_last` | Replay dispatch |
| `POST /api/equipment/equip/unequip` | `equip_item_service` / `unequip_item_service` | Modifica loadout out-of-expedition |
| `POST /api/pvp/challenge` | `challenge → simulator` | PvP simulazione (RT2-D fail-closed target futuro) |

**RT2-A public API changes = NONE** (P0Q06 verbatim).

---

## 7. Expedition Lifecycle

Sequenza reale (invariata) — riepilogo:

```
_dispatch_expedition
  ├─ dungeon lookup + gate evaluation
  ├─ team composition validation
  ├─ FOR each adv: _load_equipment + _adventurer_effective_power
  ├─ compute_team_power + role bonuses
  ├─ compute_success_chance (clamp 10..95)
  ├─ threat resolution (Void/Undead additive)
  ├─ persist expeditions + expedition_members (SNAPSHOT frozen)
  └─ update guilds.$max max_team_power_ever

<time passes>

_complete_one_expedition (CAS atomic claim status:in_progress→completing)
  ├─ **CURRENT COMBAT RESOLVER (single RNG toss)**
  ├─ roll_loot + roll_materials
  ├─ apply rewards (gold, XP, loot, materials)
  ├─ audit write (gold_credited, loot_awarded)
  ├─ update expeditions doc status=completed
  └─ trigger achievements / quests / seasonal stats
```

RT2-A snapshot loadout è **immutabile all'avvio spedizione** (P0Q02 verdict), **non salvato come stato persistente del personaggio**, **non aggiornato da equip/unequip successivo**. Può esistere nel runtime context della spedizione. Nessuna nuova persistenza cross-request.

---

## 8. Equipment Lifecycle (invariata)

- Equip/unequip permesso solo out-of-expedition (`adv.is_available=True`)
- RT2-A: no hook lifecycle (deferito a RT2-E)
- RT2-A snapshot loadout campi minimi (P0Q02 verbatim, sez. 20)

---

## 9. Stat Evaluation Touchpoints

Call sites attuali invariati (§9 originale). **RT2-A target** applica ordine RT1-compliant + Int soft cap + dex normalization + soft-cap boundary cases obbligatori:

**Casi soft cap obbligatori (verbatim P0Q10)**:
| nominal_intelligence | effective_intelligence |
|---:|---:|
| 99 | 99.0 |
| 100 | 100.0 |
| 101 | 100.5 |
| 105 | 102.5 |
| 200 | 150.0 |

Formula equivalente: `if int ≤ 100: return int; else: return 100 + (int - 100) * 0.5`.

**Modifier order (RT2-A target)**:
```
base_stat
 → trait_flat_add
 → trait_percent_add (additive, applied once)
 → spec_flat_add
 → spec_percent_add (additive, applied once)
 → Int soft cap @ 100 (surplus × 0.50)
 → dex GENERIC_BASE_POWER_ONLY
 → round(int) + clamp≥0
 → power_score contribution
 → sum + level*2
```

---

## 10. Class-State Touchpoints

Situazione attuale: NESSUNO stato di classe transient runtime. Gap RT2-B (HOLD).

**Vincolo P0Q03 (verbatim)**: `RT2-B production activation = BLOCKED` finché non è disponibile un `single authoritative writer` per expedition state transition. **Vietati in produzione**: process-local dictionaries, worker-local cooldown/Mark/Fragment maps, in-memory locks limitati a un worker.

**Vincolo P0Q02 (verbatim)**: contratto astratto futuro `ExpeditionRuntimeStateStore` con operazioni minime:
- `create_expedition_state`
- `read_expedition_state`
- `compare_and_update`
- `deduplicate_event`
- `delete_expedition_state`
- `expire_expedition_state`

**NON implementare lo store produttivo in RT2-A.**

---

## 11. Effect-Engine Touchpoints

Situazione attuale: NESSUN effect engine. Combat resolver = una tirata RNG. Gap RT2-C (HOLD — dipende da RT2-B).

**RT2-A**: NESSUN effect engine, NESSUN proc, NESSUN cooldown, NESSUNO stacking. **Escluso esplicitamente** (P0Q10 verbatim).

---

## 12. Audit Touchpoints

Attuali: `app/audit/log.py::write_audit` + `first_events.py::emit_first_event`. Indici garantiti in lifespan.

**RT2-A eventi ammessi** (P0Q09 + P0Q10 verbatim):
- soft-cap evaluation event
- shadow comparison event
- invalid stat metadata event

**Tiered sampling policy (P0Q09 verbatim)**:
| level | prod | staging | test/dev |
|---|---:|---:|---:|
| DEBUG | 0% (salvo diagnostica autorizzata) | 100% | 100% |
| INFO | 10% (futura) | 100% | 100% |
| WARNING | 100% | 100% | 100% |
| ERROR | 100% | 100% | 100% |
| Security / hard-cap / atomic rollback / boss safeguard | **100%** | 100% | 100% |

**Divieto**: non campionare via codice casuale non deterministico senza reason code osservabile.

---

## 13. Proposed RT2 Decomposition

**Sequenza design-locked (P0Q01 verbatim)**: `RT2-A → RT2-B → RT2-C → RT2-D → RT2-E`.

**Dipendenze (P0Q01 verbatim)**:
- **A**: indipendente
- **B**: richiede state-store + multi-worker coordination
- **C**: richiede B + RNG/cooldown
- **D**: accompagna B/C, non li sostituisce
- **E**: richiede B/C/D completati

**Vincolo (P0Q01 verbatim)**: **Non combinare RT2-A con RT2-B nello stesso gate**.

Deviazione rispetto al piano originale: **NONE**. Sequenza confermata.

---

## 14. RT2-A · Stat Evaluation Foundation (FIRST CODE GATE · CONDITIONAL GO)

**Gate ID**: `R18.6.RV3-IS2-B-P2B-RT2-A · STAT EVALUATION FOUNDATION`
**Nature**: `STATELESS FOUNDATION · PURE · DETERMINISTIC · MULTI-WORKER-SAFE`

### 14.1 Scope autorizzabile (P0Q10 verbatim · 11 items)
1. canonical IT ↔ runtime stat bridge
2. pure equipment-stat aggregation
3. nominal-stat calculation
4. modifier-order implementation
5. Intelligence soft-cap function
6. effective-stat result model
7. expedition-start loadout snapshot
8. server-side default-OFF feature flags
9. shadow comparison path
10. unit/property/integration tests
11. performance baseline and benchmarks

### 14.2 Esclusioni esplicite RT2-A (P0Q10 verbatim)
- Mark
- Drain
- Fragments
- proc RNG
- duration
- cooldown
- effect instances
- stacking
- boss safeguards
- item hooks
- Legendary effects
- DB migration
- public API

### 14.3 File-change boundary
Categorie ammesse: `NEW_MODULE`, `MODEL_EXTENSION`, `SERVICE_EXTENSION`, `VALIDATION_CHANGE`, `CONFIGURATION`, `TEST_ONLY`.

Vietato in RT2-A: DB collection creation · persistent model fields · migration scripts · Registry modifications · item seed modifications · frontend changes · OpenAPI changes.

**Necessità impreviste → `SCOPE_EXPANSION_REQUIRED` → STOP → PM ADJUDICATION.**

### 14.4 Compatibility contract (verbatim)
- Entrambi i flag OFF → `runtime behavior/formula/expedition/API` = **unchanged**
- Solo `runtime_stat_shadow_enabled = true` → nuovo calcolo eseguito, confrontato, **non autoritativo**
- `runtime_stat_soft_cap_enabled = true` → autoritativo **solo in ambiente autorizzato PM**
- **Nel primo gate RT2-A: `production authoritative enablement = forbidden`**

### 14.5 Atomicity RT2-A (side-effect free · verbatim)
- `invalid equipment stat` → reject candidate calculation
- `missing optional stat` → treat as zero
- `unknown stat field` → validation error
- `negative final nominal stat` → clamp to zero
- `calculation exception` → **current runtime result preserved**
- Shadow mode: candidate failure → **no gameplay impact**

### 14.6 Acceptance criteria RT2-A (P0Q07 relative-baseline + generali)
- Compilazione + lint verdi
- Test matrix §30 al 100%
- `functional stat calculation p95 overhead ≤ max(5% baseline, 1 ms)`
- `shadow evaluation p95 overhead ≤ max(10% baseline, 2 ms)`
- `memory growth per evaluated adventurer = bounded`
- `unbounded cache growth = 0`
- `database query increase = 0`
- `network call increase = 0`
- Sealed integrity: 6 passed / 36 byte-identical
- Feature flag rollback verificato (flip OFF → legacy path immediato)

### 14.7 Deliverable code (futuri · HOLD until Phase 2 dispatch)
- `app/stats/runtime_evaluator.py` (NEW_MODULE)
- `app/stats/soft_caps.py` (NEW_MODULE)
- `app/stats/loadout_snapshot.py` (NEW_MODULE)
- `app/expeditions/services.py` (SERVICE_EXTENSION, flag-gated)
- `app/core/feature_flags.py` (NEW_MODULE, server-side config)
- test suite dedicata (TEST_ONLY, backend/tests/effect_engine/foundation/*)

### 14.8 Risk level
`MEDIUM` · Blockers rimasti: NONE per implementation work (baseline measurement acquisisce dati durante RT2-A stessa · P0Q07 explicit).

---

## 15. RT2-B · Transient Class State (HOLD)

**Gate ID**: `R18.6.RV3-IS2-B-P2B-RT2-B · TRANSIENT CLASS STATE`
**Status**: **`HOLD · PRODUCTION ACTIVATION BLOCKED`** (P0Q03 verdict)

**Prerequisiti bloccanti**:
- Selezione mechanism `ExpeditionRuntimeStateStore` (attualmente `production transient-state storage = NOT SELECTED` · P0Q02 verbatim)
- Multi-worker `single authoritative writer` coordination (P0Q03 verbatim)

**Design astratto già definito**: `ClassStateManager` API contract (apply_mark, consume_mark, expire_marks, get_active_marks_by_source, gain_fragment, spend_fragments, execute_drain). Non implementabile finché lo store produttivo non è selezionato.

**Nessun code start autorizzato**.

---

## 16. RT2-C · Generic Effect Engine (HOLD)

**Gate ID**: `R18.6.RV3-IS2-B-P2B-RT2-C · GENERIC EFFECT ENGINE`
**Status**: **`HOLD · PRODUCTION ACTIVATION BLOCKED`**

**Prerequisiti**:
- RT2-A completato + PM-locked
- RT2-B completato (state store operativo)
- RNG server-authoritative expedition-scoped operativo
- Cooldown/duration/stacking policy PM-ratified

**Nessun code start autorizzato**.

---

## 17. RT2-D · Observability & Hardening (HOLD)

**Gate ID**: `R18.6.RV3-IS2-B-P2B-RT2-D · OBSERVABILITY & HARDENING`
**Status**: **`HOLD`**

Accompagna B/C, **non li sostituisce** (P0Q01 verbatim). Audit tiered sampling (P0Q09) è policy ratificata e applicabile trasversalmente a partire da RT2-A per gli event-type ammessi in §12.

---

## 18. RT2-E · Item Hook Enablement (HOLD)

**Gate ID**: `R18.6.RV3-IS2-B-P2B-RT2-E · ITEM HOOK ENABLEMENT`
**Status**: **`HOLD`**

**Prerequisito**: RT2-B/C/D completati.
**Nessun effect finale** assegnato a nessun item — invariante.

---

## 19. Feature Flags (P0Q04 verbatim · SERVER-SIDE CONFIGURATION APPROVED)

**Mechanism**: environment/centralized application settings · read at startup · server controlled · default **false**.

**Vietati**:
- Local storage client
- Query parameter
- Account-editable preference
- DB flag dinamico
- Feature flag via API pubblica

### 19.1 Flag richieste (6 totali, tutte default `false`)

| flag_id | scope | gate RT2 | attivabile in RT2-A |
|---|---|---|:---:|
| `runtime_stat_soft_cap_enabled` | globale | RT2-A | **SÌ (solo ambiente autorizzato PM)** |
| `runtime_stat_shadow_enabled` | globale | RT2-A | **SÌ (shadow diagnostica)** |
| `cdv_transient_state_enabled` | globale | RT2-B | NO (costante futura, no behavior) |
| `item_effect_engine_enabled` | globale | RT2-C | NO (costante futura, no behavior) |
| `cdv_item_hooks_enabled` | globale | RT2-E | NO (costante futura, no behavior) |
| `effect_observability_enabled` | globale | RT2-D | NO (costante futura, no behavior) |

**In RT2-A**: solo le prime due sono attive; le altre quattro **dichiarate come costanti future** e **non devono attivare comportamento**.

### 19.2 Fail-safe
- `missing flag → false`
- `invalid flag → startup validation failure OPPURE false con ERROR esplicito`
- **Nessun flag auto-abilitato in produzione**

---

## 20. Transient-State Placement (P0Q02 verbatim)

### 20.1 RT2-A — `NOT REQUIRED`
Consentiti solo oggetti in-memory a vita breve per la richiesta corrente:
- `LoadoutSnapshot`
- `EffectiveStatResult`
- `SoftCapEvaluation`
- `ShadowComparisonResult`

Vincoli assoluti:
- Non sopravvivono alla richiesta
- **Non sono state store**
- **No DB**
- **Non condivisi fra worker**

### 20.2 RT2-B/C — `production transient-state storage = NOT SELECTED`
Contratto astratto futuro `ExpeditionRuntimeStateStore` (operazioni minime):
- `create_expedition_state`
- `read_expedition_state`
- `compare_and_update`
- `deduplicate_event`
- `delete_expedition_state`
- `expire_expedition_state`

**Non implementare lo store produttivo in RT2-A.**

### 20.3 Snapshot loadout — campi minimi (verbatim)
`adventurer_id` · `expedition_id` · `base stats` · `equipment-derived flat stats` · `permanent modifiers` · `temporary modifiers present at start` · `nominal stats` · `effective stats` · `soft-cap result` · `source item blueprint list` · `snapshot_version` · `created_at`.

Regole:
- Immutabile all'avvio spedizione
- **Non salvato come stato persistente del personaggio**
- Non aggiornato da equip/unequip successivo
- Può esistere nel contesto runtime **già usato** dalla spedizione
- Se serve **nuova persistenza cross-request** → **STOP `PERSISTENCE_BASELINE_CONFLICT`** (RT2-A può ripiegare su calcolo puro + shadow senza snapshot persistente)

---

## 21. Concurrency Model (P0Q03 verbatim — `RESOLVED_BY_SCOPE_BOUNDARY`)

**RT2-A**: `PURE / STATELESS / DETERMINISTIC` → **multi-worker safe by design**. Nessuna coordinazione cross-worker richiesta.

**RT2-B/C production activation = BLOCKED**. Obbligatorio `single authoritative writer` per expedition state transition.

**Vietati in produzione per RT2-B/C**:
- Process-local dictionaries
- Worker-local cooldown/Mark/Fragment maps
- In-memory locks limitati a un worker

**Fail-stop status**:
- `TRANSIENT_STATE_DEPLOYMENT_CONFLICT` = `LATENT FOR RT2-B/C · NOT APPLICABLE TO RT2-A`

---

## 22. Atomicity Model

RT2-A è **side-effect free** (§14.5 verbatim). Nessuna transazione DB, nessuna race condition possibile.

RT2-B/C: atomicity delegata a `ExpeditionRuntimeStateStore.compare_and_update` (contratto astratto). Non implementata in Phase 1.

`ATOMICITY_PERSISTENCE_CONFLICT` = **NOT_TRIGGERED**.

---

## 23. Idempotency Plan

RT2-A: no idempotency runtime richiesta (side-effect free).

RT2-B/C: dedup via `ExpeditionRuntimeStateStore.deduplicate_event` (contratto astratto).

Key design futura: `(expedition_id, event_seq_int, event_type_str)`.

---

## 24. RNG Plan

**RT2-A**: NESSUN RNG runtime. Il calcolo statistico è **deterministico puro**. Test suite riproducibile.

**RT2-C (futuro)**: `SERVER_AUTHORITATIVE_EXPEDITION_SCOPED_PRNG` — dettaglio nel piano originale (invariato). Non implementabile finché RT2-A/B non completati.

---

## 25. Compatibility Plan

**Contract RT2-A (verbatim §14.4)**:
- Entrambi i flag OFF → runtime/formula/expedition/API `unchanged`
- Solo `runtime_stat_shadow_enabled = true` → non autoritativo (solo confronto)
- `runtime_stat_soft_cap_enabled = true` in produzione = `forbidden` in first gate

**Legacy item**: nessun retro-branding, nessun rename, nessun effetto automatico sui 9 preserved items, nessuna invalidazione.

**Test dedicati** (§30 test matrix): `test_legacy_item_compat.py` + `test_preserved_items_no_effect.py`.

---

## 26. Schema Boundary

RT2-A: nessuna estensione schema pubblica. `MODEL_EXTENSION` interna possibile solo per `LoadoutSnapshot` come struttura runtime (**non persistita**, non esposta).

Nessuna nuova collection DB. Nessuna feature_flags collection (rimpiazzata da server-side configuration · P0Q04).

---

## 27. API Boundary (P0Q06 verbatim)

**RT2-A public API changes = NONE**.
- `OpenAPI modification = 0`
- `New endpoint = 0`
- `Response-field extension = 0`

Info shadow: **server-side, audit/diagnostic only, non player-facing**. Esposizione futura → gate API dedicato (post-RT2-D minimo).

---

## 28. Migration Boundary

**RT2-A DB migration = NOT REQUIRED · NOT AUTHORIZED**.

- Nessuna nuova collection
- Nessuna migration di schema esistente
- Nessun backfill

Se necessità impreviste → `SCOPE_EXPANSION_REQUIRED` → STOP.

---

## 29. Test Architecture

Test suite RT2-A obbligatoria:
- `backend/tests/effect_engine/foundation/` (NEW_DIR)
  - `test_stat_bridge.py`
  - `test_equipment_aggregation.py`
  - `test_modifier_order.py`
  - `test_soft_cap.py` (include i 5 casi verbatim: 99/100/101/105/200)
  - `test_rounding.py`
  - `test_loadout_snapshot.py`
  - `test_feature_flags.py`
  - `test_shadow_comparison.py`
- `backend/tests/effect_engine/foundation/property/` (NEW_DIR)
  - `test_monotonicity.py`
  - `test_nonneg_output.py`
  - `test_deterministic_output.py`
  - `test_flag_off_equivalence.py`
- `backend/tests/effect_engine/foundation/integration/`
  - `test_expedition_start_snapshot.py`
  - `test_snapshot_immutability.py`
  - `test_shadow_no_impact.py`
  - `test_legacy_items_compat.py`
- `backend/tests/effect_engine/foundation/performance/`
  - `test_baseline_functional.py`
  - `test_baseline_shadow.py`

Sealed integrity guard preservato invariato.

---

## 30. Test Matrix RT2-A (obbligatoria · verbatim)

### 30.1 Unit
- stat bridge (IT↔runtime)
- equipment stat aggregation
- modifier order enforcement
- soft-cap boundaries **(99/100/101/105/200)**
- rounding rules

### 30.2 Property
- monotonicity of effective stat
- non-negative output
- deterministic output (same input → same output)
- disabled-flag equivalence (both flags OFF → identical to legacy path)

### 30.3 Integration
- equipment aggregation at dispatch time
- expedition start snapshot creation
- snapshot immutability post-start
- shadow no-impact (shadow ON, soft cap OFF → gameplay identical)

### 30.4 Compatibility
- legacy items without effect metadata
- missing optional stats treated as zero
- flags OFF identical behavior

### 30.5 Performance
- baseline functional (no RT2-A code active)
- authoritative calculation (soft_cap ON, autorizzato ambiente PM)
- shadow calculation (shadow ON, autoritative OFF)

---

## 31. Rollout Strategy (P0Q08 verbatim · 8 fasi · RT2-A autorizza solo 1-3)

| # | Fase | RT2-A autorizzato |
|:---:|---|:---:|
| 1 | unit and property tests | **SÌ** |
| 2 | local development flags enabled | **SÌ** |
| 3 | automated integration environment | **SÌ** |
| 4 | test-user-only environment | NO (verdict PM successivo) |
| 5 | controlled staging | NO |
| 6 | production shadow evaluation | NO |
| 7 | limited non-shadow activation | NO |
| 8 | general availability | NO |

**RT2-A autorizza esclusivamente steps 1-3.** Ogni passaggio successivo richiede verdict PM esplicito.

---

## 32. Shadow Evaluation (P0Q05 verbatim · APPROVED FOR RT2-A ONLY)

**Modello**: shadow mode calcola in parallelo il candidato senza modificare il risultato autoritativo.

**Deve calcolare**:
- current runtime stat result
- candidate RT1 stat result
- delta
- reason codes
- evaluation latency

**NON deve**:
- Modificare power reale
- Modificare successo spedizione
- Modificare statistiche salvate
- Modificare item / ricompense
- **Esporre al client**

### 32.1 Campi diagnostici minimi (verbatim)
- `expedition_id`
- `adventurer_id`
- `nominal_intelligence`
- `effective_intelligence`
- `current_base_power`
- `candidate_base_power`
- `power_delta`
- `soft_cap_applied`
- `evaluation_duration_ms`
- `reason_code`

**Divieto**: non registrare loadout intero o dati sensibili.

---

## 33. Rollback Strategy

**RT2-A rollback**: flip `runtime_stat_soft_cap_enabled=false` E `runtime_stat_shadow_enabled=false` → immediate legacy path restore.

- Data loss: **None** (side-effect free)
- Recovery time: **Immediate** (next request)
- Rollback verification test obbligatorio: flip ON → dispatch → flip OFF → dispatch → snapshot identical

**Critical constraint**: nessun rollback richiede modifiche DB.

---

## 34. Observability Integration

RT2-A audit events ammessi (§12):
- `SOFT_CAP_EVALUATION`
- `SHADOW_COMPARISON`
- `INVALID_STAT_METADATA`

Sampling: tiered per severity (§12 tabella P0Q09).

Metrics: `p50/p95/p99 latency` per event; `evaluation_duration_ms` per shadow comparison.

**Redaction**: nessun loadout intero, nessuna email, nessun user_id non mascherato.

---

## 35. Performance Risks (P0Q07 verbatim · RELATIVE-BASELINE PERFORMANCE CONTRACT APPROVED)

### 35.1 Acceptance criteria RT2-A
- `functional stat calculation p95 overhead ≤ max(5% baseline, 1 ms)`
- `shadow evaluation p95 overhead ≤ max(10% baseline, 2 ms)`
- `memory growth per evaluated adventurer = bounded`
- `unbounded cache growth = 0`
- `database query increase = 0`
- `network call increase = 0`

### 35.2 Regole applicazione
- Soglie applicate **stesso ambiente + stesso fixture set**
- Se baseline non riproducibile: **`PERFORMANCE_BASELINE_MISSING = BLOCKING FOR RT2-A CLOSURE · non blocking for initial implementation work`**
- RT2-B/C richiederanno soglie separate basate su eventi

### 35.3 Status corrente
`PERFORMANCE_BASELINE_MISSING` = **NOT_BLOCKING** per Phase 2 code start (contratto relative-baseline permette baseline measurement DURANTE RT2-A implementation stessa).

---

## 36. Security and Abuse

Rischi (invariati vs piano originale):
- Client-forged trigger events → server-side only (RT2-C target)
- Replayed events → idempotency (RT2-C target)
- Predictable RNG → HMAC seed derivation (RT2-C target)
- Equip-swap cooldown reset → cooldown persistent (RT2-C target)
- Effect metadata tampering → Pydantic + integrity SHA (RT2-E target)
- Over-cap resource injection → cap enforcement (RT2-B target)
- Cross-adventurer Mark consumption → source ownership (RT2-B target)

**RT2-A**: side-effect free → superficie di attacco minima. Solo shadow diagnostic exposure server-side (audit only, non player-facing).

---

## 37. Risk Register

R01 (transient state multi-worker) → **RESOLVED_BY_SCOPE_BOUNDARY per RT2-A**. Rimane HIGH per RT2-B/C → blocca production activation. Mitigation attesa: `ExpeditionRuntimeStateStore` production selection.

R05 (feature flag desync) → **RESOLVED_BY_P0Q04** (server-side config, no DB, no client).

R06 (audit volume) → **RESOLVED_BY_P0Q09** (tiered sampling ratificato).

R07 (legacy item compat) → coperto da test dedicati (§30).

R08 (soft-cap FE-BE divergence) → server truth authoritative; FE mirror deferred to post-RT2-A.

R09 (performance regression) → **RESOLVED_BY_P0Q07** (relative-baseline contract).

R10 (RNG determinism drift) → non applicabile in RT2-A (no RNG).

Rischi RT2-A residui: **LOW-MEDIUM**. Nessuno blocking.

---

## 38. PM Open Questions (10/10 RESOLVED · verdicts ratificati)

| ID | Topic | Status | Verdict summary |
|---|---|:---:|---|
| **P0Q01** | RT2 gate decomposition | ✅ APPROVED · DESIGN-LOCKED | Sequenza A→B→C→D→E. Non combinare A con B. |
| **P0Q02** | Transient-state storage | ✅ RESOLVED | RT2-A: NOT REQUIRED (LoadoutSnapshot etc. in-memory a vita breve). RT2-B/C: contratto astratto `ExpeditionRuntimeStateStore` (6 ops). Store produttivo NON in RT2-A. |
| **P0Q03** | Multi-worker coordination | ✅ RESOLVED_BY_SCOPE_BOUNDARY | RT2-A pure/stateless/deterministic → multi-worker safe. RT2-B/C production activation BLOCKED. |
| **P0Q04** | Feature-flag mechanism | ✅ APPROVED | Server-side configuration: env/centralized settings, read at startup, default false, no DB, no client. 6 flag richieste (2 attive RT2-A). Fail-safe: missing→false. |
| **P0Q05** | Shadow-evaluation scope | ✅ APPROVED FOR RT2-A ONLY | Calcola candidato + delta + reason codes + latency. Non modifica autoritativo. Non esporre al client. 10 campi diagnostici minimi. |
| **P0Q06** | Public API exposure | ✅ APPROVED | Public API changes = NONE per RT2-A. OpenAPI mod = 0. Shadow: server-side, audit only. |
| **P0Q07** | Performance thresholds | ✅ APPROVED · RELATIVE-BASELINE | p95 functional ≤ max(5% baseline, 1 ms); shadow ≤ max(10% baseline, 2 ms). DB/network increase = 0. Bounded memory. Baseline missing = BLOCKING FOR CLOSURE, NON per implementation. |
| **P0Q08** | Rollout environment order | ✅ APPROVED · DESIGN-LOCKED | 8 fasi. RT2-A autorizza solo 1-3. Ogni step successivo → verdict PM. |
| **P0Q09** | Audit sampling policy | ✅ TIERED SAMPLING APPROVED | DEBUG prod 0%; INFO staging 100% prod 10%; WARNING/ERROR 100%; security/hard-cap/rollback/safeguard 100%. Reason code osservabile obbligatorio. |
| **P0Q10** | First code gate | ✅ APPROVED | First gate = RT2-A · STAT EVALUATION FOUNDATION. Scope 11 items verbatim. Esclusioni esplicite. Soft-cap boundary cases 99/100/101/105/200. Compatibility contract. Atomicity rules. |

**Applied count**: **10/10 verbatim**. **Auto-ratificazione**: **NONE**.

---

## 39. RT2 Code Readiness (post-ratifica)

| Gate | Design complete | Blockers | Code start authorized |
|---|:---:|---|:---:|
| **RT2-A** | ✅ (§14) | NONE (baseline durante implementation) | **CONDITIONAL GO — awaiting Phase 2 dispatch** |
| RT2-B | Design astratto | `ExpeditionRuntimeStateStore` production selection + multi-worker writer | **HOLD** |
| RT2-C | Design astratto | RT2-A/B completati + RNG + cooldown ratificati | **HOLD** |
| RT2-D | Design astratto | Accompagna B/C (P0Q01) | **HOLD** |
| RT2-E | Design astratto | RT2-B/C/D completati | **HOLD** |

**Fail-stop status**:
- `TRANSIENT_STATE_DEPLOYMENT_CONFLICT` = `LATENT FOR RT2-B/C · NOT APPLICABLE TO RT2-A`
- `ATOMICITY_PERSISTENCE_CONFLICT` = `NOT_TRIGGERED`
- `FEATURE_FLAG_INFRASTRUCTURE_MISSING` = `RESOLVED_BY_P0Q04` (server-side configuration)
- `PERFORMANCE_BASELINE_MISSING` = `NOT_BLOCKING FOR IMPLEMENTATION · BLOCKING FOR CLOSURE`
- `PERSISTENCE_BASELINE_CONFLICT` = `NOT_TRIGGERED` (P0Q02 conferma no cross-request persistence)
- `SCOPE_EXPANSION_REQUIRED` = `NOT_TRIGGERED`

---

## 40. GO/HOLD Recommendation (POST-RATIFICA)

### Raccomandazione finale
**`RT2-P0 CLOSED · PM-LOCKED`** · **`RT2-A CONDITIONAL GO`** (in attesa Phase 2 dispatch orchestratore).

### Razionale
- 10/10 P0Q ratificate verbatim
- Nessun fail-stop deterministico attivo
- Separazione stateless/stateful esplicita → RT2-A production-ready by scope boundary
- RT2-B/C stateful runtime: production activation BLOCKED da store contract + multi-worker writer
- Baseline invariance preservata (30/30 artefatti byte-identical)
- Sealed integrity mantenuta (6 passed / 36 byte-identical)
- Application status: 0 modifiche ovunque

### Stato oggetti post-Phase 1
- `RT2-P0` = **CLOSED / PM-LOCKED**
- `RT2-A` = **CONDITIONAL GO — awaiting orchestrator Phase 2 dispatch**
- `RT2-B / C / D / E` = **HOLD**
- `Phase 2B item assignment` = **HOLD**
- `Registry v3` = **NOT AUTHORIZED**
- `Gate 11 · Monaco · NC1 · AFX2` = **HOLD**

### STOP esplicito
Phase 1 documentale completa. **Non anticipare RT2-A code**. In attesa di Phase 2 dispatch separato.

---

**Fine documento** · 40/40 sezioni · Italian_only · DOCUMENTAL_ONLY · PM-RATIFIED · SHA Policy §31 · STRICT STOP
