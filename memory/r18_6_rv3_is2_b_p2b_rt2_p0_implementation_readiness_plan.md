# R18.6.RV3-IS2-B-P2B-RT2-P0 · Implementation Readiness & Change Plan

**Regime**: `DOCUMENTAL_ONLY · READ-ONLY DISCOVERY · NO_APPLY · Italian_only`
**Author role**: Documental agent (PM-directed)
**Dispatch**: Messaggio 113 — RT2-P0 Implementation Readiness & Change Plan
**Data emissione**: 2026-02 (UTC)
**Ancoraggio invariante**: `lore_meta.py` SHA256 = `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`
**Sezioni totali**: 40/40 (ordine PM-vincolato)

> **AVVERTENZA GOVERNANCE**: Questo documento è esclusivamente un piano di implementazione documentale. Nessuna modifica al codice, nessun DB write, nessuna migration, nessuna generazione Registry, nessun apply runtime. La sola compilazione o dichiarazione qui non costituisce autorizzazione a costruire alcunché. Ogni gate RT2-A..E richiede un dispatch PM esplicito successivo.

---

## 1. Executive Summary

RT2-P0 formalizza il **piano eseguibile** per tradurre la spec RT1 (Runtime Stat & Effect Semantics, 45/45 sezioni, 15/15 RTQ, PM-locked) in codice, senza implementare nulla. L'obiettivo è identificare touchpoints reali, boundaries, ownership dei dati, collocazione stato transient, dispatch eventi, concorrenza, idempotenza, feature flags, test architecture, rollout, rollback, observability, rischi prestazionali.

**Raccomandazione finale**: `HOLD-PENDING-PM-DECISIONS`. Il piano è coerente e realizzabile, ma **4 PM open questions** sono bloccanti per RT2-A code start: `P0Q02` (transient-state storage), `P0Q03` (multi-worker coordination), `P0Q04` (feature-flag mechanism), `P0Q07` (performance thresholds). Nessun fail-stop deterministico è scattato in questo dispatch (deployment attuale = single-worker, quindi il rischio topologico è latente ma non attivo).

**Invarianti RT1 preservate**: soft cap Int=100, post-cap effective return=0.50, dex=GENERIC_BASE_POWER_ONLY, combined proc cap=45%, Marks 5/source, 1/source-target, durata ≤10s, Fragments cap=5, Drain requires own Mark & does not consume, effect persistence=transient only, PvP default disabled, DB migration=not required.

**Copertura**: 40 sezioni · change map ~40 voci · 5 gate proposti (RT2-A..E) · 5 feature flag proposti · 10 PM open questions · test matrix 14 family · risk register 8 rischi obbligatori + estensioni.

---

## 2. Scope

### In-scope per RT2-P0 (documental)
- Discovery read-only di adventurers, equipment, expeditions, combat resolver, formulas, audit, PvP, shared constants, item schemas, test fixtures, OpenAPI schemas, startup wiring
- Mappa dei file candidati a modifiche future con classificazione `change_type`
- Decomposizione RT2 in 5 sub-gate (A/B/C/D/E) con dipendenze
- Proposta feature flags (5), server-controlled, default OFF, distinct per environment
- Collocazione stato transient (loadout snapshot, Marks, Fragments, effect instances, cooldowns, RNG state, event dedup keys)
- Modello di concorrenza & atomicità
- Piano idempotenza
- Piano RNG server-authoritative
- Piano compatibility per item legacy senza effect metadata
- Boundary API/schema/migration
- Test architecture + matrix
- Rollout strategy (7 fasi, tutte PLANNED/HOLD)
- Shadow evaluation model
- Performance risks (thresholds `PM_REVIEW`)
- Security & abuse register
- Risk register + PM open questions
- Recommendation GO/HOLD

### Out-of-scope per RT2-P0
- Qualsiasi modifica ai sorgenti runtime (`/app/backend/app/**`)
- Qualsiasi write DB (index, seed, migration, backfill)
- OpenAPI changes
- Registry v3 generation o apply
- Item generation / Legendary final effects
- Autorizzazione a RT2-A..E o Phase 2B item assignment
- Riapertura di RT1

---

## 3. Governance

### 3.1 Regime attivo
- `DOCUMENTAL_ONLY` · `READ-ONLY DISCOVERY` · `NO_APPLY` · `Italian_only`
- SHA Policy §31: nessuna self-hash embedded; SHA dichiarate solo in chat
- Sealed integrity gate: `pytest backend/tests/backend_r18_4_sealed_integrity_test.py` deve restituire `6 passed / 36 byte-identical`
- Baseline invariance: IS2-A (8), IS2-B P1 (4), P1-N1 (3), P2A (5 aggregate), P2B-1 (5), RT1 (5) = **30 artefatti byte-identical richiesti**
- PRD invariance: **nessun append in RT2-P0**
- `lore_meta.py` SHA invariant

### 3.2 Application status atteso (post RT2-P0)
| Superficie | Δ atteso |
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

### 3.3 Autorizzazioni successive richieste
- RT2-A code start → dispatch PM esplicito dopo ratifica delle P0Q02/03/04/07
- Rollout ambito staging → dispatch PM successivo (post RT2-D)
- Live activation → dispatch PM successivo (post shadow evaluation approvata)

---

## 4. Source Chain

Catena di autorità normativa che RT2-P0 assume:

1. **IS2-A** (8 artefatti): Baseline Stat & Role invariants (PM-locked)
2. **IS2-B Phase 1** (4 artefatti): Attribute Semantics & Class Bindings (PM-locked)
3. **IS2-B P1-N1** (3 artefatti): Bug/gap Nettuno addendum (PM-locked)
4. **IS2-B Phase 2A** (envelope+closure, 5 artefatti): Budget Envelope Projection (PM-locked)
5. **IS2-B P2B-1** (5 artefatti): Budget Conversion Contract Options, Model A-T ratificato (PM-locked)
6. **IS2-B P2B-RT1** (5 artefatti): Runtime Stat & Effect Semantics Spec, 15 RTQ applicati (PM-locked)
7. **RT2-P0** (questo dispatch): Implementation Readiness — DOCUMENTAL, non ratificato ancora

Sealed source layer: 36 file `/app/backend/**` — byte-identical, mai toccati da nessun artefatto post-R18.3d.

---

## 5. Current Architecture (Read-Only Discovery)

### 5.1 Layout backend
```
/app/backend/
├── server.py                  # thin wrapper: from app.core.app_factory import create_app; app = create_app()
└── app/
    ├── core/
    │   ├── app_factory.py     # create_app(), CORS, CSRF, maintenance, router mounting
    │   ├── lifespan.py        # startup: ensure_indexes + seeds
    │   ├── database.py        # motor client + db handle
    │   ├── indexes.py         # create_all_indexes(db)
    │   ├── config.py          # MONGO_URL, DB_NAME, JWT_SECRET, APP_ENV, CORS
    │   ├── csrf.py            # CSRF middleware
    │   ├── maintenance.py     # MaintenanceMiddleware (write-freeze via env)
    │   └── stat_role_registry.py  # R18.3d SEALED — READ-ONLY UNWIRED loader
    ├── auth/, guilds/, dungeons/, expeditions/, equipment/, inventory/, items/
    ├── adventurers/, recruitment/, training/, class_halls/, talents/, squads/
    ├── pvp/, pvp_season/, pvp_continental/, seasons/, leaderboard/
    ├── raids/, world_boss/, world/, world_events/, resources/, site_contracts/
    ├── legendary_forge/, arfus_forge/, trade_pacts/, guild_specialization/
    ├── forge/, crafting/, market/, shop/, auction/, materials/
    ├── audit/, chronicle/, chat/, dashboard/, achievements/, quests/, contracts/
    ├── consortiums/, territory/, stables/, races/, catalog/, stats/
    ├── admin/, onboarding/, rewards/, shared/, scripts/, seeds/, content/
    └── content/lore_meta.py   # SEALED INTEGRITY ANCHOR
```

Ogni dominio è un **bounded context** con `routes.py`, `services.py`, `schemas.py`. Composizione via `create_app()` che monta ~60 router sotto `/api/<domain>`.

### 5.2 Lifespan (startup)
- `lifespan.py` esegue in ordine: `create_all_indexes` → audit/market/consortium/chat/shop/season/pvp/reward/xp_cap indexes → 20+ seed idempotenti → `logger.info("Orbus backend ready")`
- Zero dependency injection framework (import diretti). Nessun IoC container.

### 5.3 Deployment topology (osservato)
- Supervisor: `uvicorn server:app --host 0.0.0.0 --port 8001 --workers 1 --reload`
- **Single worker** in preview/dev.
- Produzione: topologia non documentata in codebase. **P0Q03 blocca**.

### 5.4 Auth
- JWT HS256, `JWT_SECRET` da env, 7 giorni access + 30 refresh. Header `Authorization: Bearer` o cookie httpOnly.
- CSRF double-submit per cookie-authed mutating requests.

### 5.5 DB layer
- Motor async client, DB handle globale `app.core.database.db`.
- Nessun ORM. Documents = dict Python. `_id` MongoDB ObjectId **mai** esposto (usato UUID4 `id` come public reference).
- Timestamps ISO string UTC.

---

## 6. Runtime Entry Points

Endpoints critici per il ciclo che RT2 dovrà innervare:

| Endpoint | Router | Service | Ruolo runtime |
|---|---|---|---|
| `POST /api/expeditions` | `expeditions/routes.py` | `start_expedition` → `_dispatch_expedition` | Dispatch (validate + snapshot + persist) |
| `POST /api/expeditions/replay-last` | `expeditions/routes.py` | `replay_last` → `_dispatch_expedition` | Replay dispatch |
| `GET /api/expeditions` | `expeditions/routes.py` | `list_expeditions` | List + lazy completion sweep |
| `GET /api/expeditions/{id}` | `expeditions/routes.py` | `get_expedition` | Detail + report builder |
| `GET /api/expeditions/last-completed` | `expeditions/routes.py` | `get_last_completed` | Replay eligibility |
| `POST /api/equipment/equip` | `equipment/routes.py` | `equip_item_service` | Modifica loadout (fuori spedizione) |
| `POST /api/equipment/unequip` | `equipment/routes.py` | `unequip_item_service` | Modifica loadout |
| `POST /api/pvp/challenge` | `pvp/routes.py` | `challenge` → `simulate_match` | PvP simulazione (no live combat) |
| `POST /api/raids/*` | `raids/*` | recovery + boss logic | Non ancora ciclo runtime completo |
| `POST /api/world_boss/*` | `world_boss/*` | Alveora V1 | Ciclo raid V1 |

**RT2 target**: `_dispatch_expedition` (snapshot loadout runtime) + `_complete_one_expedition` (attualmente 1 tirata RNG → deve diventare orchestrator eventi) + `pvp/simulator.py` (analoga estensione) + `world_boss` (Alveora hook readiness in RT2-E).

---

## 7. Expedition Lifecycle

Sequenza reale ricostruita da `expeditions/services.py`:

```
start_expedition(db, guild, payload)
 └─> _dispatch_expedition(db, guild, dungeon_id, adv_ids, is_replay=False)
      ├─ dungeon lookup + is_active check
      ├─ _evaluate_dungeon_gate (soft progression: guild.level, adv_count, max_team_power_ever)
      ├─ validate team composition (unique, size, availability, retired, playable class)
      ├─ enforce_min_adventurer_level (legacy min lv / dungeon.gate)
      ├─ FOR each adv: _load_equipment_for_adventurer → snapshot + eq_power
      ├─ FOR each adv: _adventurer_effective_power (traits + spec applied)
      ├─ compute_team_power(members) + role bonuses (+5 Tank/Healer/DPS, +10 all-3)
      ├─ compute_success_chance(team_power, recommended_power)
      ├─ compute_threat_resolution (Void/Undead — additive bonus)
      ├─ _build_equipment_delta (base vs final power + narrativa IT)
      ├─ insert expeditions doc (status=in_progress, snapshot fields)
      ├─ insert expedition_members docs (immutable snapshot per member)
      ├─ update adventurers.is_available=False
      └─ update guilds.$max max_team_power_ever

<time passes: dungeon.base_duration_seconds>

GET /api/expeditions/*        # triggers lazy sweep
 └─> complete_due_expeditions(db, guild_id)
      └─> _complete_one_expedition(db, exp_id)
           ├─ CAS: find_one_and_update({status:in_progress}, {$set:status:completing})
           ├─ ***COMBAT RESOLVER (attuale)***:
           │      final_score = _rng.randint(1, 100)
           │      success = final_score <= success_chance
           │      // NO events, NO procs, NO Marks, NO Fragments, NO cooldowns
           ├─ roll_loot_for_dungeon(db, dungeon, success)
           ├─ roll_materials_for_dungeon(db, dungeon, success)
           ├─ update guild.gold ($inc)
           ├─ FOR each member: apply XP (traits + arfus + primary-stat multiplier) + level-up loop + update adventurer
           ├─ FOR each loot_id: upsert inventory_items
           ├─ FOR each material: upsert inventory_items
           ├─ audit write (gold_credited, loot_awarded) — best-effort
           ├─ update expeditions doc (status=completed, rewards, log)
           ├─ evaluate_achievements("dungeon_completed") — best-effort
           ├─ starter fallback grant (one-shot per guild) — atomic guard
           ├─ emit_first_event("FIRST_EXPEDITION_COMPLETED") — idempotent
           ├─ increment_quest_progress + weekly + contract — best-effort
           ├─ on_expedition_completed (Guild XP drip +15/+5) — best-effort
           └─ increment_seasonal_stat("dungeon_clears") — idempotent CAS
```

**Osservazioni chiave**:
- **Combat resolver** = **una sola riga**: `_rng.randint(1, 100) <= success_chance`. RT2-C dovrà sostituirla con un dispatcher eventi che chiama Mark/Drain/Fragment/proc engine e produce `final_score` come funzione derivata di eventi risolti.
- **Snapshot loadout** già congelato in `equipment_snapshot` + `equipment_power_snapshot` + `total_power_snapshot` + `traits_snapshot` sui `expedition_members`. RT2-A può estendere ma non deve riscrivere.
- **CAS atomic claim** (`status: in_progress → completing`) previene doppie completions per la lazy sweep. RT2-C dovrà preservare questa proprietà + aggiungere idempotency keys per singoli eventi.
- **Best-effort audit** (try/except pass): RT2-D deve alzare selettivamente ad audit obbligatorio per eventi effect-critical (proc_fired, mark_applied, fragment_gained, drain_executed, cooldown_started).

---

## 8. Equipment Lifecycle

Da `equipment/services.py`:

- Equipaggia/unequipaggia solo **fuori dalla spedizione** (adventurer.is_available=True). Nessuna azione durante `in_progress`.
- `equip_item_service` esegue: validate item ownership, item type/slot match, class lock (signature items), 4-state UI computation, transactional upsert su `equipment` collection, invalida potenziale cache.
- `_load_equipment_for_adventurer(db, adv_id)` → `(slots_dict, eq_power_int, raw_rows_list)` — usato dal dispatch expedition per lo snapshot.
- Nessun trigger runtime al momento (equip/unequip = solo modifica statica).

**RT2 impact**: RT2-A introdurrà `loadout_snapshot` estesa (con effect metadata resolved) al dispatch time. RT2-E introdurrà hook lifecycle: `on_equip` / `on_unequip` (fuori-spedizione: eseguito subito e persistito in loadout metadata; dentro-spedizione: no-op perché non permesso).

---

## 9. Stat Evaluation Touchpoints

Punti attuali dove le stat effettive vengono calcolate:

| File:linea | Funzione | Ruolo | RT2 impact |
|---|---|---|---|
| `expeditions/formulas.py:59` | `adventurer_base_power(adv)` | Somma raw stats + level*2 | RT2-A: rimane; ora chiamato solo come fallback |
| `expeditions/formulas.py:75` | `adventurer_effective_power(adv)` | Base → trait modifiers → spec modifiers → sum + lvl*2 | RT2-A: DEVE estendere con Int soft cap (100 → 0.50 post-cap return) e generic dex-runtime rule |
| `expeditions/formulas.py:95` | `item_equip_power(item)` | Somma bonus stat + power_score | RT2-A: rimane; equip contribution atomic |
| `expeditions/formulas.py:107` | `compute_team_power(members)` | Somma per-member + role bonuses | RT2-A: rimane; sequenza modifiers pre-cap already respected |
| `expeditions/formulas.py:145` | `compute_success_chance(tp, rec)` | Clamp [10, 95] | RT2-A: rimane |
| `expeditions/services.py:953` | `base = _adventurer_effective_power(adv)` in `_dispatch_expedition` | Applica trait+spec al dispatch | RT2-A: entry point per Int soft cap |
| `training/catalog.py:apply_specialization_modifiers` | Spec modifier application | Fase 13-14 spec | RT2-A: verificare ordine `traits → spec → cap` conforme RT1 §12 |
| `expeditions/xp_modifier.py:compute_xp_multiplier` | Primary-stat XP debuff | Debuff XP se stat sotto threshold di classe | RT2-A: NO change (fuori-scope stat runtime) |

**Ordine di applicazione RT1-compliant (target RT2-A)**:
```
base_stat
 → trait_flat_add
 → trait_percent_add   (additive stacking, applied once)
 → spec_flat_add
 → spec_percent_add    (additive stacking, applied once)
 → Int SOFT CAP @ 100  (surplus × 0.50)
 → dex GENERIC_BASE_POWER_ONLY normalization
 → round(int) + clamp≥0
 → power_score contribution
 → sum + level*2
```

---

## 10. Class-State Touchpoints

Al momento **non esiste** stato di classe persistente durante l'esecuzione runtime (Marks, Fragments, resource segments, Drain execution records). Il codice attuale ha:

- `class_halls/` — routes/services per gestione hall passivo (buff persistenti a guild, non runtime)
- `training/catalog.py` — spec modifiers static
- `adventurers/services.py` — trait & class stats static
- `talents/` — struttura placeholder (talent trees WIP, non runtime attivo)

**Gap identificato**: nessuna struttura in-memory per stato transient di classe (Warlock's Mark, Necromancer's Fragment, Sacred Champion's Charge, ecc.). Questo è lo scope RT2-B: introdurre `ClassStateManager` come componente in-process con lifecycle allineato all'expedition/PvP simulation.

---

## 11. Effect-Engine Touchpoints

**Al momento non esiste un effect engine** nel senso RT1. Il "combat" è una singola tirata RNG. Nessun proc, nessun cooldown runtime, nessuna durata di effetto, nessuno stacking, nessun refresh.

Gli item legacy hanno `power_score` + `strength_bonus` + `agility_bonus` + `intellect_bonus` + `endurance_bonus` + `faith_bonus` come contribuzione statica. **Nessun campo `effect_metadata`** al momento.

**Gap identificato**: scope RT2-C completo. Include:
- `EffectInstance` dataclass (id, source_adv_id, target_adv_id?, effect_type, magnitude, duration_end_ts, cooldown_end_ts, stack_count, tags)
- `EffectEngine` dispatcher (trigger event → RNG proc check → apply/refresh/stack)
- `ProcResolver` (individual proc rolls + combined proc cap enforcement @ 45%)
- Compatibility: item senza `effect_metadata` = passthrough (nessun proc, comportamento identico ad oggi)

---

## 12. Audit Touchpoints

Da `audit/log.py` (369 righe) e `audit/first_events.py` (115 righe):

- `write_audit(db, event_type, actor_guild_id, ...)` — insert su `audit_log` collection con:
  - `event_type`, `actor_user_id?`, `actor_guild_id?`, `related_entity_id?`
  - `metadata` sanitized (mask email, drop keys sensibili)
  - timestamp UTC ISO
- `emit_first_event(db, event_type, guild_id, extra)` — idempotent one-shot per (guild, event_type)
- `ensure_audit_indexes(db)` — indici on `event_type`, `actor_guild_id`, `created_at`

**RT2 impact**:
- RT2-D: aggiungere event_type nuovi obbligatori:
  - `MARK_APPLIED` / `MARK_EXPIRED` / `MARK_CONSUMED`
  - `FRAGMENT_GAINED` / `FRAGMENT_SPENT`
  - `DRAIN_EXECUTED` / `DRAIN_REJECTED_NO_MARK`
  - `EFFECT_PROC_FIRED` / `EFFECT_PROC_CAPPED` / `EFFECT_REFRESHED` / `EFFECT_STACKED`
  - `COOLDOWN_STARTED` / `COOLDOWN_ENDED`
  - `HARD_CAP_HIT_INT` / `SOFT_CAP_APPLIED`
  - `EXPEDITION_COMBAT_STARTED` / `EXPEDITION_COMBAT_RESOLVED`
- Sampling policy per event ad alto volume (`EFFECT_PROC_FIRED`) — **P0Q09 blocca**.

---

## 13. Proposed RT2 Decomposition

5 sub-gate ordinati per dipendenza:

```
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│ RT2-A   │ → │ RT2-B   │ → │ RT2-C   │ → │ RT2-D   │ → │ RT2-E   │
│ Stat    │   │ Class   │   │ Effect  │   │ Obs &   │   │ Item    │
│ Eval    │   │ State   │   │ Engine  │   │ Harden  │   │ Hooks   │
└─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘
     ↓ nessuna       ↓ classi         ↓ generico      ↓ audit/perf   ↓ item metadata
     regressione     senza effetti    senza item      + PvP fail     consumo (no
     power calc      finali            finali          closed         final effects)
```

Motivazione ordine:
- **RT2-A** (stat eval) è prerequisito per tutto: Int cap deve funzionare prima che B/C possano avere basi corrette.
- **RT2-B** (class state) è prerequisito di C: Marks/Fragments devono esistere prima che il proc engine possa consumarli o triggerarli.
- **RT2-C** (effect engine) è prerequisito di D: observability e safeguards richiedono che gli eventi esistano.
- **RT2-D** (obs + hardening) è prerequisito di E: attivare item hooks senza safeguards è alto rischio.
- **RT2-E** (item hooks) chiude il ciclo enabling ma **NON assegna alcun effect finale** agli item (rimane Phase 2B esplicita).

Deviazione proposta rispetto alla sequenza PM: **nessuna**. La sequenza dettata è coerente e coprente.

---

## 14. RT2-A · Stat Evaluation Foundation

**Obiettivo**: implementare loadout snapshot esteso + Int soft cap + dex normalization + ordine dei modifiers RT1-compliant. Nessun proc, nessun effect.

**Deliverable code (futuri, HOLD)**:
- `app/stats/runtime_evaluator.py` (NEW_MODULE, ~200-300 LOC): funzione pura `evaluate_runtime_stats(adv, traits, spec, equipment) → RuntimeStatSnapshot` (dataclass frozen)
- `app/stats/soft_caps.py` (NEW_MODULE, ~80 LOC): funzione pura `apply_int_soft_cap(int_value: int) → int` con contract:
  ```
  se int_value ≤ 100: return int_value
  altrimenti: return 100 + int((int_value - 100) * 0.50)
  ```
- `expeditions/services.py` (SERVICE_EXTENSION): il call site `base = _adventurer_effective_power(adv)` diventa `snapshot = evaluate_runtime_stats(...); base = snapshot.total_base_power`; sostituzione **feature-flag gated** (`runtime_stat_soft_cap_enabled=False` → path attuale)
- `expeditions/formulas.py` (NO_CHANGE se la logica va nel nuovo modulo, altrimenti SERVICE_EXTENSION con hook `apply_int_soft_cap`)
- `stats/public_catalog.py` (NO_CHANGE, ma potenziale annotation `soft_cap_at=100` per Int in fase separata)

**Acceptance criteria RT2-A**:
1. Unit test: 20+ casi di Int soft cap (0, 1, 50, 99, 100, 101, 150, 200, 500, edge negativi → 0)
2. Property test: `apply_int_soft_cap` monotonically non-decreasing
3. Integration: snapshot ≡ current output quando flag=OFF
4. Regression: `pytest backend/tests/` deve rimanere green
5. Sealed integrity: 6 passed / 36 byte-identical
6. Feature flag rollback verificato (flip → immediate return to legacy path)

**Risk**: MEDIUM. Cambia il calcolo del team_power. Backward compat critica.

---

## 15. RT2-B · Transient Class State

**Obiettivo**: introdurre lifecycle Marks / Fragments / Drain execution records in-process, allineato all'expedition simulation. Isolamento multi-CdV (Class of Value / Combat di Valore — Warlock's Mark, Necromancer's Fragment, ecc.).

**Deliverable code (futuri, HOLD)**:
- `app/class_runtime/` (NEW_MODULE dir):
  - `state_manager.py` (~250 LOC): `ClassStateManager` con API:
    - `apply_mark(source_adv_id, target_adv_id, duration_seconds, expedition_id) → MarkResult`
    - `consume_mark(source_adv_id, target_adv_id, expedition_id) → bool`
    - `expire_marks(current_ts, expedition_id) → int` (chiamato al tick)
    - `get_active_marks_by_source(source_adv_id, expedition_id) → list[Mark]` (≤5)
    - `gain_fragment(adv_id, expedition_id) → FragmentResult` (cap=5)
    - `spend_fragments(adv_id, count, expedition_id) → bool`
    - `execute_drain(source_adv_id, target_adv_id, expedition_id) → DrainResult` (require own mark, not consume)
  - `models.py` (~100 LOC): dataclass Mark, Fragment, DrainRecord, ResourceSegment (tutti transient, no DB)
  - `isolation.py` (~50 LOC): `ExpeditionScope` context manager per isolare stato per expedition_id

**Storage**: **in-process dict** keyed per `expedition_id`. Nessuna persistenza DB (RT1 §XX conferma).

**Acceptance criteria RT2-B**:
1. Unit test: Mark lifecycle (apply/expire/consume/count-per-source-cap=5/count-per-target=1)
2. Unit test: Fragment lifecycle (gain/spend/cap=5)
3. Unit test: Drain require own mark + not consume
4. Concurrency test: 2 dispatch expedition simultanei → stato isolato per expedition_id
5. Cleanup test: expedition completion → state manager purga entry
6. Feature flag: `cdv_transient_state_enabled=False` → tutte le API sono no-op (return default)
7. Sealed integrity: 6/36
8. `TRANSIENT_STATE_DEPLOYMENT_CONFLICT` verificato → nessun conflitto a single-worker

**Risk**: HIGH. Introduce stato in-process. Rischio principale in multi-worker deploy (P0Q03 blocca).

---

## 16. RT2-C · Generic Effect Engine

**Obiettivo**: dispatcher eventi generico che, dato un `TriggerEvent`, consulta gli `EffectMetadata` disponibili (da item, class ability, spec talent), tira RNG per proc, applica effetti con cooldown/duration/stacking/refresh atomico. Enforce combined proc cap 45%. Boss safeguards.

**Deliverable code (futuri, HOLD)**:
- `app/effect_engine/` (NEW_MODULE dir):
  - `models.py` (~150 LOC): `EffectInstance`, `EffectMetadata`, `TriggerEvent`, `ProcRoll`, `Cooldown`
  - `dispatcher.py` (~300 LOC): `EffectDispatcher.dispatch(event, context) → list[EffectResult]`
  - `proc_resolver.py` (~150 LOC): individual proc rolls + combined cap @ 45%
  - `cooldown_manager.py` (~100 LOC): per-source, per-effect cooldown tracking
  - `duration_tracker.py` (~100 LOC): tick-based expiration
  - `stacking_policy.py` (~150 LOC): per-effect stacking rules (replace, stack, refresh)
  - `boss_safeguards.py` (~100 LOC): hard-cap check + boss immunity list
  - `atomic_executor.py` (~100 LOC): all-or-nothing execution wrapper con rollback in-process

**Integration point**: `expeditions/services.py::_complete_one_expedition` diventa combat orchestrator quando `item_effect_engine_enabled=True`. Il singolo `_rng.randint(1,100)` è sostituito da un loop di eventi:

```python
if item_effect_engine_enabled:
    combat_ctx = CombatContext.for_expedition(claimed, members, dungeon)
    while not combat_ctx.is_resolved():
        event = combat_ctx.next_event()  # tick eventi discreti
        effects = effect_dispatcher.dispatch(event, combat_ctx)
        combat_ctx.apply(effects)
    final_score = combat_ctx.compute_final_score()  # deriva da eventi risolti
    success = final_score <= claimed["success_chance"]
else:
    # legacy path unchanged
    final_score = _rng.randint(1, 100)
    success = final_score <= claimed["success_chance"]
```

**Acceptance criteria RT2-C**:
1. Unit test: proc individual roll (25%, 45%, 100%, 0% edge)
2. Unit test: combined proc cap = 45% verificato con 3+ effetti tutti >20%
3. Integration test: cooldown block re-fire prima della scadenza
4. Integration test: duration expire → effect removed atomically
5. Integration test: stacking (max stack N)
6. Integration test: refresh (same effect + new duration = replace end_ts)
7. Property test: RNG deterministic given fixed seed (RT2 RNG plan)
8. Concurrency test: duplicate event → single execution (idempotency)
9. Legacy compatibility: `item_effect_engine_enabled=False` → identical to today
10. Boss safeguard: hard-cap hit → no effect applied
11. Sealed integrity: 6/36

**Risk**: HIGH. Cambia radicalmente il combat resolver. Feature flag critico. Shadow evaluation obbligatoria prima di live activation.

---

## 17. RT2-D · Observability & Hardening

**Obiettivo**: audit obbligatorio per eventi effect-critical, idempotency key infrastructure, performance instrumentation, PvP fail-closed, backward compatibility tests.

**Deliverable code (futuri, HOLD)**:
- `audit/log.py` (SERVICE_EXTENSION): nuovi event_type (vedi §12) + sampling policy per proc events ad alto volume (P0Q09)
- `effect_engine/observability.py` (NEW_MODULE, ~150 LOC): metrics collector (event count, effect count, avg latency), audit hooks
- `effect_engine/idempotency.py` (NEW_MODULE, ~80 LOC): dedup key builder + in-process set con TTL
- `pvp/simulator.py` (SERVICE_EXTENSION): fail-closed check — se `item_effect_engine_enabled=True` ma il calcolo fallisce, PvP simulation rejected con reason code `EFFECT_ENGINE_FAILURE`
- `tests/test_effect_engine_compat.py` (NEW_TEST, ~200 LOC): matrix di test compatibilità item legacy senza effect metadata

**Acceptance criteria RT2-D**:
1. Audit events emesso per ogni proc/mark/fragment/drain/cooldown
2. Idempotency: duplicate event → single audit entry
3. Performance instrumentation: p50/p95/p99 latency per event
4. PvP fail-closed: engine failure → PvP challenge rejected
5. Legacy compatibility: 9 preserved item validati con test dedicato → nessun effect triggered
6. Sealed integrity: 6/36

**Risk**: MEDIUM. Additivo su audit e metrics. Rischio esplosione volume log (P0Q09).

---

## 18. RT2-E · Item Hook Enablement

**Obiettivo**: preparare gli item ad accettare `effect_metadata` senza assegnare alcun effect finale. Enabling per Legendary Forge hook + CdV item ready. **Zero effect finali** in questa fase.

**Deliverable code (futuri, HOLD)**:
- `items/schemas.py` (SCHEMA_EXTENSION additiva): campo opzionale `effect_metadata: Optional[EffectMetadata]` con default None. Schema backward-compatible.
- `items/services.py` (SERVICE_EXTENSION): serializer include `effect_metadata` quando presente, altrimenti omit.
- `equipment/services.py` (SERVICE_EXTENSION): quando l'item ha `effect_metadata` E `cdv_item_hooks_enabled=True` → registra hook nella loadout snapshot; altrimenti passthrough attuale.
- `legendary_forge/`, `arfus_forge/` (NO_CHANGE runtime, hook readiness solo)
- Class Halls (`class_halls/services.py`, SERVICE_EXTENSION): registrazione ability metadata quando `cdv_transient_state_enabled=True` e `cdv_item_hooks_enabled=True`.

**Acceptance criteria RT2-E**:
1. Item legacy senza `effect_metadata` → `equip/unequip/dispatch` = 100% identico ad oggi
2. Item con `effect_metadata` ma flag=OFF → treatement come legacy
3. Item con `effect_metadata` E flag=ON → hook registered in loadout, nessun effect fired (nessun trigger event ancora)
4. **Nessun effect finale** assegnato a nessun item — verifica esplicita
5. Schema backward compat: OpenAPI diff → solo additive fields, no removals, no rename
6. Sealed integrity: 6/36

**Risk**: LOW-MEDIUM. Solo enabling. Nessun effect attivo.

---

## 19. Feature Flags

**Requisiti (RT2-P0 dichiarati)**:
- Server-controlled (backend env var o DB config collection, decisione P0Q04)
- No client activation
- Distinct per environment (dev/preview/staging/production separati)
- Rollback senza modifica dati (flag OFF → path legacy immediato)
- Nessun effetto sui player quando disabilitate
- Default OFF ovunque tranne test unitari dedicati

**5 flag proposti** (tutti default OFF):

| flag_id | scope | RT2 gate | impatto | rollback difficulty |
|---|---|---|---|---|
| `runtime_stat_soft_cap_enabled` | globale | RT2-A | attiva Int soft cap + dex normalization + ordine modifiers | LOW (flip OFF = legacy path) |
| `cdv_transient_state_enabled` | globale | RT2-B | attiva Marks/Fragments/Drain in-process | LOW (flip OFF = state manager no-op) |
| `item_effect_engine_enabled` | globale | RT2-C | attiva effect dispatcher su combat resolver | LOW-MEDIUM (state cleanup at flip) |
| `cdv_item_hooks_enabled` | globale | RT2-E | attiva hook registration per item con effect_metadata | LOW (loadout snapshot rebuild) |
| `effect_observability_enabled` | globale | RT2-D | attiva audit + metrics per effect events | LOW (flip OFF = drop events) |

**Mechanism candidate (P0Q04 blocca)**:
- Option A: env var (`ORBUS_FLAG_RUNTIME_STAT_SOFT_CAP=1`) → richiede supervisor restart per flip
- Option B: DB `feature_flags` collection + in-memory cache 60s TTL → hot flip
- Option C: file flag (`/tmp/orbus_flag_*.enabled`) → analog a `ORBUS_MAINTENANCE_MODE`
- Option D: admin endpoint `/api/admin/flags` + Mongo backing + refresh event

**Raccomandazione agent (non ratificata)**: **Option B** (DB + cache). Motivazione: hot flip, environment-distinct (DB per env), no supervisor restart, testabile, roll-forward/roll-back rapido. Dipendenza: nuova collection `feature_flags` (index unico su flag_id) — richiede DB write autorizzato PRIMA di RT2-A (P0Q04).

---

## 20. Transient-State Placement

Mapping struttura → collocazione:

| Struttura | Collocazione proposta | Persistenza | Motivazione |
|---|---|---|---|
| loadout snapshot | `expedition_members.equipment_snapshot` (già esistente) + eventuale campo esteso `effect_hooks_snapshot` | DB (snapshot immutable) | Determinismo replay + report |
| active Marks | `ClassStateManager.marks[expedition_id][source_id][target_id]` in-process dict | in-process only | RT1 §XX transient only, no DB |
| Drain execution records | `ClassStateManager.drains[expedition_id][source_id]` list | in-process only | audit event già copre persistenza |
| Fragments | `ClassStateManager.fragments[expedition_id][adv_id]` int (cap=5) | in-process only | transient RT1 |
| resource segments | `ClassStateManager.segments[expedition_id][adv_id][seg_key]` | in-process only | transient RT1 |
| active effects | `EffectDispatcher.instances[expedition_id]` list[EffectInstance] | in-process only | transient RT1 |
| cooldowns | `CooldownManager.cd[expedition_id][source_id][effect_key]` end_ts | in-process only | transient RT1 |
| RNG state | `PRNGManager.states[expedition_id]` (seed + sequence) | in-process only durante expedition, discarded al complete | RT2 RNG plan §24 |
| event dedup keys | `IdempotencyStore.keys[expedition_id]` set con TTL | in-process only | Bounded per expedition lifespan |

**Verifica `DB persistence = not required`**: **CONFERMATO** per topologia attuale (single worker). **NON GARANTITO** in produzione multi-worker → **P0Q03 blocca** decisione finale. Se produzione = multi-worker con affinity, transient in-process OK con sticky routing. Se multi-worker senza affinity → **fail-stop `TRANSIENT_STATE_DEPLOYMENT_CONFLICT`** e migrazione a Redis obbligatoria (nuovo blocker DB migration).

---

## 21. Concurrency Model

**Contesto attuale**:
- Uvicorn `--workers 1` (single process). GIL Python attivo.
- Async I/O (Motor) → nessuna vera concorrenza CPU-bound, ma **task interleaving** possibile su await point.
- Multiple concurrent expeditions: distinti `expedition_id`, isolamento naturale via keying su exp_id in tutte le strutture in-process.
- Rischio primario: race su expedition_id condiviso durante `await db.*` interleave.

**Modello proposto RT2**:

| Rischio | Mitigazione |
|---|---|
| Duplicate events (retry / replay) | Idempotency key = `(expedition_id, event_seq, event_type)` in `IdempotencyStore` |
| Simultaneous Mark applications (same source, same target) | `ClassStateManager.apply_mark` è synchronous (no await interleave) + check-cap-5-per-source atomic |
| Concurrent Drain completion | Drain gated by `consume_mark=False` → non c'è race; solo audit event dup possibile (mitigato da idempotency) |
| Fragment race (2 gain events same tick) | Sequential dispatch in `EffectDispatcher.dispatch` (one event at a time per exp) |
| Cooldown race | Cooldown check + set in synchronous block (no await between check and set) |
| Multiple effect triggers (chain) | Chain limit + `IdempotencyStore` prevents infinite loop |
| Multiple CdV on one target | Target-side aggregation with per-source segregation (Mark: 1/source-target, cap 5/source) |
| Expedition cancellation | State manager purge on cancellation event (rollback) |

**Nessuna primitiva non supportata dallo stack**: no `threading.Lock` (async context), no `asyncio.Lock` cross-request (state manager is per-expedition, single-worker), no Redis (unless P0Q03 forces multi-worker).

---

## 22. Atomicity Model

**Casi che richiedono atomicity**:

1. **Effect execution (proc → apply → audit)**: rollback all-or-nothing se una delle 3 fails. Implementato con `atomic_executor.py` in-process (compensating action).
2. **Combat completion (CAS su expeditions.status)**: già atomic via `find_one_and_update({status:in_progress}, {$set:{status:completing}})`. Preservare.
3. **Mark apply**: atomic in synchronous block (no await interleave possible).
4. **Fragment gain/spend**: atomic in synchronous block.
5. **Cooldown start**: atomic (check + set synchronous).

**Nessuna nuova persistenza DB richiesta** per atomicity: tutto in-process. Se P0Q03 forza multi-worker → migrazione a Redis MULTI/EXEC o Mongo transactions → **ATOMICITY_PERSISTENCE_CONFLICT** potenziale fail-stop.

**Baseline attuale**: `NO_DB_TRANSACTIONS`. RT2 non introduce transactions se topology rimane single-worker.

---

## 23. Idempotency Plan

**Key design**: `idempotency_key = (expedition_id, event_seq_int, event_type_str)` unico per evento.

**Store**: `IdempotencyStore.keys[expedition_id]: set[str]` in-process + TTL = expedition lifespan (auto-purge on complete).

**Coverage**:
- Effect proc events: dedup su (exp_id, tick_seq, effect_key, source, target)
- Mark applied: (exp_id, tick_seq, MARK_APPLIED, source, target)
- Fragment gained: (exp_id, tick_seq, FRAGMENT_GAINED, adv_id)
- Drain executed: (exp_id, tick_seq, DRAIN_EXECUTED, source, target)
- Cooldown started: (exp_id, effect_key, source) — only one active cooldown per (effect, source)

**Audit event dedup**: piggyback sullo store (write_audit call preceduta da idempotency check).

**Rollback**: on expedition cancel → purge store entry.

**Cross-worker**: NOT SUPPORTED without Redis. Dependency on P0Q03.

---

## 24. RNG Plan

**Target futuro**: `SERVER_AUTHORITATIVE_EXPEDITION_SCOPED_PRNG`.

**Design**:
- **Seed creation**: `seed = hash((JWT_SECRET, expedition_id, dispatch_ts_iso))` → HMAC-SHA256 truncated to 128 bit. Deterministic given inputs.
- **Storage**: `PRNGManager.states[expedition_id] = {seed: bytes, sequence: int}` in-process only. **NEVER persisted to DB**. **NEVER exposed in API responses**. **NEVER logged in audit** (only `rng_sequence_length` and `rng_committed_count` metadata OK).
- **Sequence advancement**: each `roll()` call increments `sequence`; PRNG output = `HMAC-SHA256(seed, sequence).uint32() % max`.
- **Deterministic test injection**: env var `ORBUS_TEST_PRNG_SEED=<hex>` → override seed generation quando `APP_ENV=test` only. **NEVER honored in production**.
- **Event ordering**: sequential per expedition; PRNG calls tagged per event type ({combat: [seq0, seq1], proc: [seq2, seq3], mark_placement: [seq4], ...}) — ricostruibile per audit ma seed **mai** disclosed.
- **Retry behavior**: on effect execution failure → sequence NOT advanced (retry uses same output); on effect success → sequence advanced.
- **Prevention of duplicate rolls**: `IdempotencyStore` + `sequence` immutability post-commit.
- **Non-exposure in API/log**: seed masked come `"<REDACTED_16>"`; solo `sequence_count` esposto.

**Legacy fallback**: quando `runtime_stat_soft_cap_enabled=False` (RT2-A gate) e `item_effect_engine_enabled=False` (RT2-C gate) → `secrets.SystemRandom()` attuale rimane (non-seeded). Path invariato.

**Deviation warning**: introduce dependency implicita su `JWT_SECRET` per seed. Se `JWT_SECRET` rotato → determinismo si rompe (accettabile, seed diverso non impatta correctness).

---

## 25. Compatibility Plan

**Requisiti (da RT1 + Messaggio 112 verdetti)**:
- `legacy item without effect metadata = valid item with no effect` (invariante)
- Nessun retro-branding (non riclassificare item esistenti come "runtime-enabled" senza chiaro flag)
- Nessun rename
- Nessun effetto automatico sui **nove preserved item** (elencati in RT1 baseline, PM-locked)
- Nessuna invalidazione degli item esistenti
- Feature disabled = comportamento attuale invariato

**Verifica automatizzata**:
- Test `test_legacy_item_compat.py` (NEW_TEST): itera su tutti gli item da `items` collection, verifica che con flags OFF il comportamento equip/unequip/expedition sia identico snapshot-to-snapshot rispetto al pre-RT2.
- Test `test_preserved_items_no_effect.py` (NEW_TEST): whitelist esplicita dei 9 preserved item, verifica che nessun `effect_metadata` sia mai attivato (anche con flags ON).

**Schema evolution**: solo campi additive opzionali (`Optional[EffectMetadata]`). Nessun campo rimosso, nessun rename, nessuna semantica esistente modificata.

**OpenAPI diff atteso post-RT2-E**: solo aggiunte a schema `Item` (campo `effect_metadata`) e `Adventurer` (campi transient come nested opzionali se decisione P0Q06 lo autorizza; altrimenti nulla).

---

## 26. Schema Boundary

Classificazione modifiche schema future:

| Change | Class | Motivazione |
|---|---|---|
| `Item.effect_metadata` (Optional, RT2-E) | `INTERNAL_SCHEMA_ONLY` se non esposto in API, altrimenti `READ_ONLY_RESPONSE_EXTENSION` | P0Q06 decide |
| `Adventurer.runtime_stat_snapshot` (Optional, RT2-A) | `READ_ONLY_RESPONSE_EXTENSION` se esposto in `/api/adventurers/{id}`, altrimenti `INTERNAL_SCHEMA_ONLY` | Decisione RT2-A design |
| `expedition_members.effect_hooks_snapshot` (Optional, RT2-E) | `INTERNAL_SCHEMA_ONLY` | Snapshot interno, mai esposto |
| `expeditions.combat_events_summary` (Optional, RT2-D) | `READ_ONLY_RESPONSE_EXTENSION` per report expedition | Osservabilità utente-facing |
| `audit_log.event_type` (nuovi valori RT2-D) | `NO_API_CHANGE` (audit endpoint admin-only) | Extension enum values |
| `feature_flags` collection (RT2-A gate, se P0Q04=Option B) | `NEW_INTERNAL_SCHEMA` + admin route → `READ_ONLY_RESPONSE_EXTENSION` per `/api/admin/flags` | Nuova collection |

**Zero BREAKING_CHANGE** attesi.

---

## 27. API Boundary

Classificazione modifiche API future (target baseline `public API changes = none for RT2-A through RT2-D`):

| API | RT2 gate | Change class |
|---|---|---|
| `POST /api/expeditions` | RT2-A/C | `NO_API_CHANGE` (comportamento invariato con flag OFF; snapshot esteso interno) |
| `GET /api/expeditions/{id}` | RT2-D | `READ_ONLY_RESPONSE_EXTENSION` opzionale (`combat_events_summary`) → decisione P0Q06 |
| `POST /api/pvp/challenge` | RT2-D | `NO_API_CHANGE` (fail-closed reason code internal) |
| `GET /api/adventurers/{id}` | RT2-A | `NO_API_CHANGE` (soft cap è interna al calcolo) |
| `POST /api/equipment/equip` | RT2-E | `NO_API_CHANGE` (hook registration interna) |
| `POST /api/admin/flags` | RT2-A gate | `NEW_INTERNAL_EVENT` + `NEW_ADMIN_ENDPOINT` (se P0Q04=Option B) |
| `GET /api/items/{id}` | RT2-E | `READ_ONLY_RESPONSE_EXTENSION` opzionale (`effect_metadata` se P0Q06 lo autorizza) |

**Baseline PM raccomandata**: `public API changes = none for RT2-A through RT2-D`. RT2-E può richiedere `READ_ONLY_RESPONSE_EXTENSION` per `effect_metadata` — decisione P0Q06.

**Nessuna modifica OpenAPI in RT2-P0**. Nessuna modifica OpenAPI in RT2-A..D. Solo RT2-E potenzialmente additive read-only.

---

## 28. Migration Boundary

**Baseline dichiarata (RT1 confermato)**: `DB migration = not required` per tutte le fasi RT2-A..E.

**Verifica per gate**:
- RT2-A: nessuna migration (soft cap è calcolo in-memory)
- RT2-B: nessuna migration (state in-process)
- RT2-C: nessuna migration (effect engine in-process)
- RT2-D: nessuna migration; solo nuovi event_type audit (schema audit_log è dict-based, no schema strict)
- RT2-E: nessuna migration (campo `effect_metadata` è optional additive)

**Eccezione condizionale**: se P0Q04 = Option B (DB feature flags) → richiede creazione collection `feature_flags` PRIMA di RT2-A code start. Questo è **un DB write authorized** che deve essere approvato dal PM separatamente. NON è una migration di schema esistente, è una nuova collection.

**Fail-stop trigger**: se P0Q03 forza multi-worker senza affinity → migrazione a Redis obbligatoria → **ATOMICITY_PERSISTENCE_CONFLICT** fail-stop.

---

## 29. Test Architecture

**Attuale**:
- `backend/tests/` contiene 100+ file test (`backend_*.py`)
- pytest + pytest-asyncio + Motor test client
- Sealed integrity test (`backend_r18_4_sealed_integrity_test.py`) — 36 file byte-identical guard
- Class-bound test (`backend_r18_4_class_bound_test.py`)
- 4-state UI test (`backend_r18_4_followup_ui_4state_test.py`)
- Test fixture `conftest.py` con orphan cleanup

**RT2 test architecture proposta**:
- `backend/tests/effect_engine/` (NEW_DIR):
  - `test_soft_cap.py` (RT2-A)
  - `test_class_state_manager.py` (RT2-B)
  - `test_effect_dispatcher.py` (RT2-C)
  - `test_proc_resolver.py` (RT2-C)
  - `test_cooldown_manager.py` (RT2-C)
  - `test_duration_tracker.py` (RT2-C)
  - `test_stacking_policy.py` (RT2-C)
  - `test_boss_safeguards.py` (RT2-C)
  - `test_idempotency_store.py` (RT2-C)
  - `test_rng_prng_manager.py` (RT2-C)
  - `test_observability.py` (RT2-D)
  - `test_effect_engine_compat.py` (RT2-D)
  - `test_multi_cdv_isolation.py` (RT2-B/C)
  - `test_feature_flag_matrix.py` (RT2-A..E)
- `backend/tests/effect_engine/property/` (NEW_DIR): hypothesis-based property tests
- Sealed integrity guard: preservato invariato (le nuove test files sono outside i 36 sealed)

**Coverage target**:
- Unit: ≥95% su moduli nuovi
- Integration: ogni gate acceptance criteria coperto
- Property: soft cap monotonicity, proc cap ≤45%, mark cap ≤5, fragment cap ≤5
- Concurrency: simultaneous dispatch, race su idempotency, cleanup on cancel
- Performance: latency p50/p95/p99 misurati (senza soglia definita — P0Q07)

---

## 30. Test Matrix

| # | Family | Componenti coinvolti | Precondizione | Comportamento atteso | Failure mode | Gate |
|---|---|---|---|---|---|---|
| 1 | Unit soft cap | `soft_caps.apply_int_soft_cap` | any int | monotonic + post-cap × 0.50 | wrong scaling | RT2-A |
| 2 | Unit stat evaluator | `runtime_evaluator.evaluate_runtime_stats` | adv+traits+spec+equip | RT1-compliant order | wrong order | RT2-A |
| 3 | Unit class state | `ClassStateManager.*` | expedition scope | lifecycle correct | leak between exp | RT2-B |
| 4 | Unit effect dispatcher | `EffectDispatcher.dispatch` | trigger event | correct effects fired | wrong dispatch | RT2-C |
| 5 | Unit proc resolver | `proc_resolver` + combined cap | proc list | combined ≤45% | cap violation | RT2-C |
| 6 | Property soft cap | `apply_int_soft_cap` | hypothesis int | monotonic non-decreasing | non-monotonic | RT2-A |
| 7 | Property proc cap | proc set | hypothesis multi-proc | combined ≤45% | cap breach | RT2-C |
| 8 | Integration full dispatch | expedition full cycle | flags OFF | identical to today | regression | RT2-A..E |
| 9 | Integration flags ON | expedition full cycle | flags ON | RT1-compliant | wrong behavior | RT2-A..E |
| 10 | Concurrency dispatch | 3+ simultaneous dispatch | multi-exp | isolated state | cross-leak | RT2-B/C |
| 11 | Idempotency | duplicate event | dedup store | single execution | double-fire | RT2-C |
| 12 | Multi-CdV isolation | 3 different CdV, 1 target | targets | per-source segregation | mark corruption | RT2-B |
| 13 | Hard-cap | Int=200 | soft cap | Int_eff=150 (100+50×0.5) | wrong cap | RT2-A |
| 14 | Boss safeguard | boss immune list | trigger | no effect applied | immune bypassed | RT2-C |
| 15 | Feature flag matrix | 5 flags × 2 states | expedition | 32 combo verified | flag leak | RT2-A..E |
| 16 | Legacy compatibility | 9 preserved items | flags ON | no effect fired | preserved broken | RT2-E |
| 17 | Equip/unequip cycle | during expedition | in-progress | operation rejected | operation permitted | RT2-A/E |
| 18 | Expedition snapshot | dispatch time | snapshot frozen | immutable post-start | mutation | RT2-A |
| 19 | Failure rollback | effect exec fails | atomic executor | rollback + audit | partial state | RT2-C |
| 20 | Performance latency | effect dispatch | 10k events | p95 < TBD (P0Q07) | over threshold | RT2-D |
| 21 | Sealed integrity | 36 files | any RT2 change | 6 passed / 36 byte-identical | drift | RT2-A..E |

---

## 31. Rollout Strategy

**7 fasi**, tutte PLANNED/HOLD, **nessuna autorizzata da RT2-P0**:

1. **tests only** — RT2-A code merged, tutti i test unit/property/integration green, flag default OFF. Zero player-facing change.
2. **local/dev flag enabled** — sviluppatore in locale con `ORBUS_FLAG_*=1`. Nessun impatto ambient.
3. **test-user-only activation** — flag ON in preview env solo per user `is_test_user=True` (già supportato dal guardrail admin). Restanti user rimangono OFF path.
4. **controlled staging** — staging env con flag ON per 100% user. Osservazione ≥7 giorni. Audit + performance metrics collected.
5. **shadow evaluation** — production env: engine calcola output candidato ma **non** modifica risultato reale (§32). Diff tracking + reason codes + performance timing. Durata ≥14 giorni.
6. **limited live activation** — production env con flag ON per subset user (canary 5% → 25% → 50%). Rollback rapido su regression detection.
7. **general availability** — production env flag ON per 100% user.

**Nessuna fase autorizzata da RT2-P0**. Ogni transizione richiede dispatch PM esplicito e ratifica delle metrics.

---

## 32. Shadow Evaluation

**Modello**: RT2 engine calcola il risultato candidato in parallelo, ma il risultato **reale** rimane quello del path legacy.

**Implementazione (design, HOLD)**:
- `expeditions/services.py::_complete_one_expedition` con flag `shadow_evaluation_enabled=True`:
  ```python
  # legacy path (source of truth)
  legacy_score = _rng.randint(1, 100)
  legacy_success = legacy_score <= claimed["success_chance"]

  # candidate path (SHADOW ONLY)
  if shadow_evaluation_enabled:
      try:
          candidate_ctx = CombatContext.for_expedition(...)
          candidate_score = candidate_ctx.compute_final_score()
          candidate_success = candidate_score <= claimed["success_chance"]
          shadow_diff = {
              "expedition_id": exp_id,
              "legacy_score": legacy_score,
              "candidate_score": candidate_score,
              "legacy_success": legacy_success,
              "candidate_success": candidate_success,
              "diff_pct": abs(legacy_score - candidate_score),
              "reason_codes": candidate_ctx.reason_codes(),
              "candidate_latency_ms": candidate_ctx.elapsed_ms,
          }
          await write_audit(db, event_type="SHADOW_EVAL_DIFF", ...)
      except Exception as exc:
          await write_audit(db, event_type="SHADOW_EVAL_FAILURE", metadata={"error": str(exc)})

  # ONLY legacy result used for player-facing outcome
  final_score = legacy_score
  success = legacy_success
  ```

**Output raccolti** (solo per confronto, non per player):
- current vs candidate score/success
- reason codes (perché candidate ha divergent)
- performance timing (p50/p95/p99 latency)
- hard-cap diagnostics (quante volte è scattato Int soft cap)

**Non registrare dati sensibili**: nessun JWT, nessuna email, nessun PII. Solo IDs (masked) + numeriche.

**Successo shadow**: ≥95% agreement rate + zero critical divergences per ≥14 giorni → autorizzazione PM a Fase 6 limited live.

---

## 33. Rollback Strategy

**Principio**: flip flag OFF → immediate return al legacy path senza migration.

**Rollback matrix per gate**:

| Gate | Rollback action | Data loss | Recovery time |
|---|---|---|---|
| RT2-A | `runtime_stat_soft_cap_enabled=False` | None | Immediate (next request) |
| RT2-B | `cdv_transient_state_enabled=False` | Transient state (per-expedition) purged; expedition results already committed remain | Immediate (in-flight expeditions complete with legacy path) |
| RT2-C | `item_effect_engine_enabled=False` | Transient effect state purged; committed results remain | Immediate; in-flight expeditions restart resolver as legacy |
| RT2-D | `effect_observability_enabled=False` | Audit events stop emitting; existing audit rows preserved | Immediate |
| RT2-E | `cdv_item_hooks_enabled=False` | Loadout snapshot rebuild required at next dispatch; existing snapshots ignored | Immediate for new dispatches |

**Critical constraint**: **nessun rollback può richiedere modifiche DB**. Se un gate richiede DB migration per rollback → fail-stop `ROLLBACK_MIGRATION_REQUIRED` (obbligatorio segnalare).

**Rollback verification test** (RT2-D acceptance): per ogni gate, test dedicato flippa flag ON → dispatch → flippa OFF → dispatch → verifica identical to pre-ON.

---

## 34. Observability Integration

**Componenti**:

1. **Audit log** (`audit/log.py`, existing): esteso in RT2-D con nuovi event_type (vedi §12). Sampling per proc-events (P0Q09).
2. **Metrics collector** (`effect_engine/observability.py`, new): in-process counter/timer/histogram, aggregato per (expedition_id, event_type). Snapshot esposto in expedition complete → merged in `expeditions.combat_events_summary` (se P0Q06 autorizza).
3. **Log lines** (`logger("orbus")`, existing): livello INFO per gate transitions, WARNING per rollback triggers, ERROR per engine failures + PvP fail-closed.
4. **Alerts** (out of scope RT2-P0): thresholds su:
   - shadow_eval_diff_rate > 5%
   - effect_engine_failure_rate > 0.1%
   - proc_cap_breach (must be zero)
   - dispatch latency p95 > TBD (P0Q07)

**Redaction**:
- JWT_SECRET mai loggato (assunto)
- RNG seed masked (`REDACTED_16`)
- Email mask via `_mask_email` (existing)
- User_id parziale mask (`_mask_user_id`, existing)

---

## 35. Performance Risks

**Rischi identificati** (soglie **PM_REVIEW**, nessun valore definitivo senza baseline):

| Metric | Rischio | Soglia proposta (PM_REVIEW) | Mitigation |
|---|---|---|---|
| effect evaluation latency (per event) | slow proc resolver | p50 < 2ms · p95 < 5ms · p99 < 15ms | Precomputed lookup + minimize dict allocations |
| events per expedition | exponential chain | ≤ 500 events / expedition | Chain depth limit + event budget |
| active effects per adventurer | memory bloat | ≤ 20 concurrent | Stacking policy enforcement |
| active Marks per expedition | memory / lookup cost | ≤ 5×N adventurers = 5×5 = 25 per exp | RT1 cap already 5/source |
| cooldown records | memory | ≤ 100 per exp | TTL-based eviction |
| audit log volume | DB pressure | ≤ 1000 events/expedition | Sampling policy P0Q09 |
| memory per expedition | RAM leak | ≤ 5 MB per active expedition | Purge on complete |

**Fail-stop `PERFORMANCE_BASELINE_MISSING`**: **ATTIVO/PARZIALE**. Nessuna baseline pre-RT2 esiste. Le soglie sopra sono proposte tecniche non ratificate. **P0Q07 blocca** ratifica finale. Raccomandazione agent: eseguire misurazione baseline (RT2-A pre-code) su expedition legacy dispatch per stabilire p50/p95 attuale. Questa misurazione NON è in scope RT2-P0.

---

## 36. Security and Abuse

Rischi obbligatoriamente valutati (RT1 + Messaggio 112):

| Rischio | Server-side validation | Reject policy | Reason code | Test |
|---|---|---|---|---|
| Client-forged trigger events | Tutti gli eventi generati server-side; nessun endpoint accetta events da client | HTTP 400 su tentativi | `CLIENT_TRIGGER_FORBIDDEN` | RT2-D |
| Replayed events | Idempotency key check (§23) | Silent dedup | `EVENT_REPLAY_DEDUP` | RT2-C/D |
| Predictable RNG | Seed derivato da JWT_SECRET (non-exportable) | N/A | N/A | RT2-C |
| Equip-swap cooldown reset | Cooldown persistente per (adv_id, effect_key) attraverso equip changes | Reject silent | `COOLDOWN_ACTIVE` | RT2-C |
| Duplicate reward resolution | CAS on expeditions.status (esistente) + starter fallback guard (esistente) | 409 | `EXPEDITION_ALREADY_COMPLETED` | RT2-C |
| Invalid boss metadata | Whitelist boss_id + hard-cap check | 400 | `INVALID_BOSS_METADATA` | RT2-C |
| Effect metadata tampering | Schema validation Pydantic + integrity SHA per item template | 400 | `ITEM_METADATA_TAMPERED` | RT2-E |
| Over-cap resource injection | ClassStateManager enforces caps at every op | Reject | `RESOURCE_CAP_EXCEEDED` | RT2-B |
| Cross-adventurer Mark consumption | Drain requires Mark by same source (RT1 §XX) | Reject | `MARK_NOT_OWNED_BY_SOURCE` | RT2-B |

**Nessun endpoint client-facing che accetta effect events**. Tutti gli event generation è server-authoritative.

---

## 37. Risk Register

| risk_id | description | affected_gate | severity | likelihood | detection | mitigation | rollback | blocking |
|---|---|---:|---:|---:|---|---|---|:---:|
| R01 | Process-local transient state in multi-worker deployment | RT2-B/C | HIGH | MEDIUM | Test in staging con `--workers 2+` | Sticky routing OR Redis migration | Flag OFF | **YES (P0Q03)** |
| R02 | Expedition retries (lazy sweep re-run) | RT2-C | MEDIUM | LOW | CAS on status already existing | Preserved via existing CAS | Automatic (CAS) | NO |
| R03 | Duplicate events (chain fire) | RT2-C | MEDIUM | MEDIUM | Idempotency store dedup | `IdempotencyStore` | Flag OFF | NO |
| R04 | Missing target metadata (target adv retired mid-expedition) | RT2-B/C | LOW | LOW | Snapshot at dispatch (existing) | Use snapshot data | Reject with reason code | NO |
| R05 | Feature-flag desynchronization (env vs DB) | RT2-A gate | HIGH | MEDIUM (se P0Q04=Option A) | Single source of truth enforced | DB flags with cache | Manual refresh | **YES (P0Q04)** |
| R06 | Audit-volume explosion (proc events × 500 per exp × 10k exp/day) | RT2-D | HIGH | HIGH | Metrics DB size | Sampling policy | Reduce sample rate | **YES (P0Q09)** |
| R07 | Legacy item compatibility break (nine preserved items) | RT2-E | CRITICAL | LOW | Test `test_preserved_items_no_effect.py` | Whitelist enforcement | Flag OFF | NO |
| R08 | Soft-cap divergence between UI and server (client shows uncapped Int, server caps) | RT2-A | MEDIUM | MEDIUM | Integration test FE-BE contract | FE mirror soft cap logic OR expose capped value only | Server truth | NO |
| R09 | Performance regression at scale | RT2-C/D | HIGH | MEDIUM | Load test + metrics | Precomputed lookup + event budget | Flag OFF | **YES (P0Q07)** |
| R10 | RNG determinism drift on JWT_SECRET rotation | RT2-C | LOW | LOW | Change management | Documented behavior | Accept new determinism | NO |
| R11 | Effect chain infinite loop | RT2-C | HIGH | LOW | Chain depth limit | Hard limit 10 hops | Break + audit | NO |
| R12 | Shadow evaluation memory pressure | RT2-D shadow | MEDIUM | MEDIUM | Metrics | Sampling for shadow eval | Flag shadow OFF | NO |

**Rischi blocking**: R01 (P0Q03), R05 (P0Q04), R06 (P0Q09), R09 (P0Q07).

---

## 38. PM Open Questions

**Nessuna auto-ratificazione**. 10/10 questions emesse.

### P0Q01 · RT2 gate decomposition
- **evidence**: Sequenza dettata da PM (RT2-A..E) coerente con dipendenze; nessuna deviazione tecnica identificata.
- **options**: (a) Accettare sequenza A→B→C→D→E come dichiarata; (b) Split RT2-D in D1 (audit) + D2 (perf) per riduzione superficie change; (c) Merge RT2-D + RT2-E in un unico gate hardening+enable.
- **agent_recommendation**: (a) — Accettare sequenza. La split proposta non riduce rischio significativamente.
- **affected_files**: nessuno (decisione strutturale)
- **risk**: LOW se accettata; MEDIUM se split (più coordinamento).
- **blocking**: NO (ma bloccante per RT2-A design se non ratificata)

### P0Q02 · Transient-state storage mechanism
- **evidence**: RT1 dichiara `effect persistence = transient only`; deployment attuale = single-worker. Nessun sistema di storage transient cross-request esistente.
- **options**: (a) In-process dict con lifecycle bound a expedition_id (raccomandato per single-worker); (b) Redis per topologia multi-worker; (c) Ibrido: in-process + snapshot su DB su expedition complete (audit-only, non recovery).
- **agent_recommendation**: (a) per single-worker attuale; migrare a (b) se P0Q03 conferma multi-worker in produzione.
- **affected_files**: `app/class_runtime/state_manager.py` (NEW), `app/effect_engine/dispatcher.py` (NEW)
- **risk**: HIGH se topologia cambia post-implementation
- **blocking**: **YES** (RT2-B code start bloccato)

### P0Q03 · Multi-worker coordination
- **evidence**: Preview supervisor = `--workers 1`. Produzione topologia non documentata in codebase.
- **options**: (a) Single-worker anche in produzione (raccomandato per RT2 in-process semplice); (b) Multi-worker con sticky routing per expedition_id (richiede load balancer configuration); (c) Multi-worker con Redis backing (richiede nuova dipendenza infra); (d) Hybrid: pool async dentro single-worker (raccomandato solo se produzione = single-container).
- **agent_recommendation**: (a) o (d). Se (b) o (c) → **fail-stop `TRANSIENT_STATE_DEPLOYMENT_CONFLICT`** attivato + escalation obbligatoria.
- **affected_files**: infrastruttura (fuori codebase) + `class_runtime/`, `effect_engine/`
- **risk**: CRITICAL — determina architettura runtime intera
- **blocking**: **YES** (blocca RT2-B/C/D)

### P0Q04 · Feature-flag mechanism
- **evidence**: Nessuna infrastruttura feature-flag centralizzata. Solo env vars discrete e file flag (`ORBUS_MAINTENANCE_MODE`).
- **options**: (a) env var + supervisor restart (semplice, no hot flip); (b) DB collection `feature_flags` + cache 60s (hot flip, richiede DB write autorizzato); (c) File flag (`/tmp/orbus_flag_*.enabled`, analog maintenance); (d) Admin endpoint + Mongo backing.
- **agent_recommendation**: (b) DB collection con admin endpoint per hot flip. Environment-distinct via APP_ENV in flag_id.
- **affected_files**: `admin/routes.py` (NEW admin endpoint), `feature_flags/` (NEW module), lifespan.py (index)
- **risk**: MEDIUM — introduce nuova dipendenza infra
- **blocking**: **YES** (blocca RT2-A code start)

### P0Q05 · Shadow-evaluation scope
- **evidence**: Modello shadow proposto § 32. Rischio memory pressure per calcolo doppio.
- **options**: (a) Shadow su 100% expeditions in staging; (b) Shadow su sampling 10% in staging; (c) Shadow su tutti in produzione con sampling 1%; (d) Shadow disabilitato in produzione.
- **agent_recommendation**: (a) staging 100% + (c) produzione 1% sampling per ≥14 giorni.
- **affected_files**: `effect_engine/observability.py`, config
- **risk**: MEDIUM (memory pressure)
- **blocking**: NO (decisione post-RT2-D)

### P0Q06 · Public API exposure
- **evidence**: Baseline PM raccomandata `public API changes = none for RT2-A through RT2-D`. RT2-E potenziale additive.
- **options**: (a) Zero API changes fino a RT2-E; (b) Aggiungere `combat_events_summary` in `GET /api/expeditions/{id}` in RT2-D (read-only, opt-in via query param); (c) Espone `effect_metadata` in `GET /api/items/{id}` in RT2-E.
- **agent_recommendation**: (a) per RT2-A..D. (c) per RT2-E limitato a admin endpoint inizialmente.
- **affected_files**: `expeditions/routes.py`, `items/routes.py`
- **risk**: LOW se additive read-only
- **blocking**: NO (decisione RT2-D+)

### P0Q07 · Performance thresholds
- **evidence**: Nessuna baseline pre-RT2. Soglie §35 sono proposte tecniche non ratificate.
- **options**: (a) Misurare baseline pre-RT2 (workload sintetico) e derivare thresholds come baseline + 20% slack; (b) Adottare soglie proposte agent come `PM_REVIEW`; (c) Deferire decisione a post-RT2-D quando metrics reali disponibili.
- **agent_recommendation**: (a) per RT2-A pre-code. Se non fattibile in tempo, (c).
- **affected_files**: nessuno (misurazione)
- **risk**: HIGH — impossibile decidere GA senza baseline
- **blocking**: **YES** (blocca ratifica RT2-D thresholds → live GA)

### P0Q08 · Rollout environment order
- **evidence**: Sequenza §31 proposta (7 fasi). Nessuna deviazione richiesta.
- **options**: (a) Accettare sequenza 7 fasi; (b) Compattare fase 3+4 in unica (test-user in staging); (c) Estendere shadow evaluation a 30 giorni.
- **agent_recommendation**: (a).
- **affected_files**: nessuno (governance)
- **risk**: LOW
- **blocking**: NO

### P0Q09 · Audit sampling policy
- **evidence**: R06 rischio audit-volume explosion. Proc events dominano volumetria.
- **options**: (a) Full audit (nessuna sampling) — rischio DB pressure alto; (b) Full audit critical events (Mark, Drain, cooldown, cap_hit) + sampling 10% proc events; (c) Sampling per event_type dedicato (Mark 100%, proc 5%, cooldown 100%).
- **agent_recommendation**: (b) o (c) — (c) più conservativo.
- **affected_files**: `audit/log.py`, `effect_engine/observability.py`
- **risk**: MEDIUM (audit trail completeness vs cost)
- **blocking**: **YES** (RT2-D acceptance)

### P0Q10 · First code gate scope
- **evidence**: RT2-A dichiarato §14. Rischio scope creep.
- **options**: (a) RT2-A come dichiarato (Stat Evaluation Foundation only); (b) RT2-A + soft cap only, dex normalization deferita a RT2-A1; (c) RT2-A + soft cap + feature flag infra (RT2-A0 preliminare per P0Q04).
- **agent_recommendation**: (c) — RT2-A0 preliminare per feature flag infra + baseline measurement, poi RT2-A come dichiarato.
- **affected_files**: nessuno (governance)
- **risk**: LOW (split additiva) — MEDIUM se (a) e P0Q04 non risolta
- **blocking**: **YES** (RT2-A start bloccato)

---

## 39. RT2 Code Readiness

**Riepilogo readiness per gate**:

| Gate | Design complete | Blockers | Code start authorized |
|---|:---:|---|:---:|
| RT2-A0 (preliminare, se P0Q10=c) | Partial (P0Q04 required) | P0Q04, P0Q07 | NO |
| RT2-A | YES (§14) | P0Q02, P0Q04, P0Q07 (baseline), P0Q10 | NO |
| RT2-B | YES (§15) | P0Q02, P0Q03 | NO |
| RT2-C | YES (§16) | RT2-A/B completati, P0Q03 | NO |
| RT2-D | YES (§17) | RT2-C completato, P0Q07, P0Q09 | NO |
| RT2-E | YES (§18) | RT2-C/D completati, P0Q06 | NO |

**Nessun gate autorizzato**. Tutti in `HOLD-PENDING-PM-DECISIONS`.

**Fail-stop status**:
- `TRANSIENT_STATE_DEPLOYMENT_CONFLICT`: **LATENT** (single-worker attuale OK; produzione da confermare via P0Q03)
- `ATOMICITY_PERSISTENCE_CONFLICT`: **NOT_TRIGGERED** (in-process atomicity fattibile)
- `FEATURE_FLAG_INFRASTRUCTURE_MISSING`: **PARTIAL** (env vars disponibili come minimo viable; DB collection preferita — P0Q04 decide)
- `PERFORMANCE_BASELINE_MISSING`: **PARTIAL_BLOCKING** (nessuna baseline pre-RT2 esistente → thresholds sono `PM_REVIEW` — P0Q07)

---

## 40. GO/HOLD Recommendation

### Raccomandazione finale
**`HOLD-PENDING-PM-DECISIONS`**

### Razionale
Il piano è **tecnicamente coerente, coprente e realizzabile** con la topologia attuale (single worker). Nessun fail-stop deterministico è attivo. Le invarianti RT1 sono preservate integralmente nel design.

Tuttavia, **4 PM open questions bloccano** il code start di RT2-A:

1. **P0Q02** (transient-state storage) — decisione architetturale
2. **P0Q03** (multi-worker coordination) — determina se rischio R01 è latente o attivo
3. **P0Q04** (feature-flag mechanism) — infrastruttura prerequisito
4. **P0Q07** (performance thresholds) — baseline pre-RT2 obbligatoria per ratifica soglie

Additionally, **P0Q09** (audit sampling) blocca RT2-D e **P0Q10** (first code gate scope) blocca RT2-A start.

### Prerequisiti minimi per GO su RT2-A
1. Ratifica PM di P0Q02 (storage), P0Q03 (topology), P0Q04 (flag mechanism), P0Q10 (scope).
2. Autorizzazione DB write per creare collection `feature_flags` (se P0Q04=Option B).
3. Autorizzazione a baseline measurement pre-RT2 (P0Q07).
4. Nessuna regressione su sealed integrity.

### Cosa RT2-P0 chiude
- Discovery completa e documentata
- Change map dettagliata per tutti i 5 gate futuri
- Decomposizione ratificabile
- Feature flags proposti
- Test architecture pronta
- Risk register aggiornato
- 10/10 PM open questions emesse per adjudication

### Stato post-RT2-P0
- `RT2-P0 = ARTIFACT_WRITTEN · PM_ADJUDICATION_REQUIRED · FORMAL_CLOSURE = HOLD`
- `RT2-A / B / C / D / E = HOLD`
- `Phase 2B item assignment = HOLD`
- Nessuna auto-progressione

### STOP esplicito
Il presente documento è **discovery + plan**. Nessun codice sarà scritto, nessuna infrastruttura sarà creata, nessuna decisione sarà ratificata unilateralmente. In attesa di dispatch PM successivo per adjudication delle 10 PM open questions.

---

**Fine documento** · 40/40 sezioni · Italian_only · DOCUMENTAL_ONLY · SHA Policy §31 · STRICT STOP
