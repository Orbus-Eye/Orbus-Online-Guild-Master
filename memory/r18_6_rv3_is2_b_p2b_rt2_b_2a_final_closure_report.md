# R18.6.RV3-IS2-B-P2B-RT2-B-2A · Final Closure Report · PM-LOCKED

**Gate ID**: `R18.6.RV3-IS2-B-P2B-RT2-B-2A · LOCAL SHADOW WIRING & STATE LIFECYCLE FOUNDATION`
**Regime**: `CODE_GATE · IMPLEMENTED · CLOSED · PM-LOCKED · Italian_only · SHA §31 · STRICT STOP`
**Classificazione PM (Message 143)**: `LOCALLY_WIRED · SHADOW_ONLY · DEFAULT-OFF · TEST-USER GATED · FAIL-CLOSED · LEGACY-PATH PRESERVING · NOT GAMEPLAY-AUTHORITATIVE · NOT TESTER-GAMEPLAY-READY`
**Anchor**: `lore_meta.py` SHA `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` · INVARIANT
**Data closure**: 2026-02 (UTC)

---

## Requisito 1 · PM ratification

PM Message 143 ratifica il code gate `RT2-B-2A CODE_IMPLEMENTED / AWAITING FORMAL CLOSURE` come **`IMPLEMENTED / CLOSED`**. 12/12 B2Q design-locked verified. 0 deviations. 0 fail-stops. Tests PASS. Closure documentale autorizzata senza nuova adjudication.

## Requisito 2 · RT2-B-2A CLOSED

`R18.6.RV3-IS2-B-P2B-RT2-B-2A · LOCAL SHADOW WIRING & STATE LIFECYCLE FOUNDATION` = **`IMPLEMENTED / CLOSED / PM-LOCKED`**.

## Requisito 3 · Files touched = 13

Totale file toccati: **13** (10 nuovi + 3 modificati). Dettaglio nel closure manifest §31.

## Requisito 4 · New files = 10

Nuovi file introdotti:
1. `backend/app/stats/runtime/wiring/__init__.py`
2. `backend/app/stats/runtime/wiring/audit.py`
3. `backend/app/stats/runtime/wiring/coordinator.py`
4. `backend/app/stats/runtime/wiring/shadow_hooks.py`
5. `backend/tests/effect_engine/wiring/__init__.py`
6. `backend/tests/effect_engine/wiring/conftest.py`
7. `backend/tests/effect_engine/wiring/test_guardrails.py`
8. `backend/tests/effect_engine/wiring/test_shadow_lifecycle.py`
9. `backend/tests/effect_engine/wiring/test_anti_p2w.py`
10. `backend/tests/effect_engine/wiring/test_response_invariance.py`

## Requisito 5 · Existing files modified = 3

File esistenti modificati (delta chirurgico):
1. `backend/app/stats/runtime/feature_flags.py`
2. `backend/app/expeditions/services.py`
3. `backend/tests/effect_engine/foundation/test_feature_flags.py`

## Requisito 6 · Exact existing-file deltas

| Path | pre-change SHA | post-change SHA | Lines added | Lines removed |
|---|---|---|---|---|
| `feature_flags.py` | `b18cd19d61c13b38293c6fec74ad8688c86ab92041fb1cb777f9f182fe77068c` | `e669d17b3ae96aea5fd788e4ecafb2d24b55d7d664062e7585ad133fd89035d8` | +28 | -0 |
| `expeditions/services.py` | `8cacace0c70863a84cb344044d50007dfeb2ffd7d0bd2e1773731643d21af505` | `f61f82c258ed5fd2f0d726e8a1e1a89460d02e0c2916781a647f04a3aa1f23ad` | +38 | -0 |
| `test_feature_flags.py` | `170b6adc27412e905fb76108f6b157f804df467956dbe8158c1f702ddacffbb5` | `799c323f1202ff082e5dc1079dfee62a82f21ea50d2af0deb734bff8b0777500` | +17 | -8 |

**Totale delta esistenti**: `+83 · -8` righe. Nessun refactor.

## Requisito 7 · B2Q 12/12 IMPLEMENTED

| B2Q | Topic | Implementation evidence | Affected module | Test evidence | Status |
|---|---|---|---|---|---|
| B2Q01 | Wiring layer = expedition service orchestration | `expeditions/services.py:1095-1104` (hook T1 dispatch) · `712-731` (hook T2 completion) | `expeditions/services.py` | `test_expedition_public_contract_unchanged` | IMPLEMENTED |
| B2Q02 | State creation post-validation, pre-resolution | `shadow_hooks.py:_build_coordinator` post `insert_one`; `coordinator.create_shell_state` shell empty | `wiring/shadow_hooks.py` · `wiring/coordinator.py` | `test_create_shell_state_success` · `test_create_shell_state_is_empty_no_transitions` | IMPLEMENTED |
| B2Q03 | Request-scoped ExpeditionRuntimeCoordinator | `_build_coordinator` istanza per-request, no background renewer | `wiring/shadow_hooks.py:_build_coordinator` | `test_create_shell_state_success` | IMPLEMENTED |
| B2Q04 | Terminalization COMPLETED/CANCELLED/COMPLETED_WITH_FAILURE | `TerminalOutcome` enum + `terminalize()` method + `maybe_shadow_terminalize` maps success→COMPLETED/COMPLETED_WITH_FAILURE | `wiring/coordinator.py:TerminalOutcome` · `wiring/shadow_hooks.py:maybe_shadow_terminalize` | `test_terminalize_completed` · `test_terminalize_completed_with_failure` · `test_terminalize_cancelled` | IMPLEMENTED |
| B2Q05 | Audit substrate + whitelist/blacklist | `audit.py:_ALLOWED_FIELDS` (14 whitelist) · `_FORBIDDEN_FIELDS` (9 blacklist) · 5 event id | `wiring/audit.py` | `test_audit_whitelist_blacklist_disjoint` · `test_audit_forbidden_fields_verbatim_B2Q05` · `test_audit_allowed_fields_verbatim_B2Q05` · `test_audit_forbidden_field_drops_record` | IMPLEMENTED |
| B2Q06 | Test-user server-authoritative fail-closed | `shadow_hooks._guardrail_check`: `users.find_one({id, is_test_user})` + fail-closed on missing/error | `wiring/shadow_hooks.py:_guardrail_check` | `test_guardrail_flag_on_non_test_user_returns_false` · `test_guardrail_missing_user_fail_closed` · `test_guardrail_db_error_fail_closed` | IMPLEMENTED |
| B2Q07 | FF server-side startup, default OFF, frozen per op | `feature_flags.py` RT2_B_RUNTIME_ATTIVABILE + `lru_cache` snapshot memoized | `feature_flags.py` | `test_cdv_flag_default_off` · `test_cdv_flag_activation_via_env` · `test_future_constants_still_hard_forced_false` | IMPLEMENTED |
| B2Q08 | Fallback isolation, forbid duplicate/partial/silent | Coordinator try/except non-blocking, no partial mutation, `STORE_INFRA_ERROR` return | `wiring/coordinator.py` · `wiring/shadow_hooks.py` | `test_store_infra_error_isolation` · `test_maybe_shadow_dispatch_flag_off_noop` · `test_maybe_shadow_terminalize_flag_off_noop` | IMPLEMENTED |
| B2Q09 | Class gameplay transitions = NONE (shell only) | `create_shell_state` sets `adventurer_class_states=()`, `processed_event_keys=()`, `last_event_sequence=0` | `wiring/coordinator.py:create_shell_state` | `test_create_shell_state_is_empty_no_transitions` | IMPLEMENTED |
| B2Q10 | LOCALHOST allowlist enforcement | `coordinator._is_db_allowlisted` accetta solo `orbus_r16_rt2b_test` + pattern `orbus_r16_rt2b_it_<id>` · forbidden set contiene `orbus_r16` + `orbus_r16_test` | `wiring/coordinator.py:_is_db_allowlisted` | `test_db_forbidden_no_op` · `test_terminalize_forbidden_db_deferred` | IMPLEMENTED |
| B2Q11 | Application-scoped adapter dependency | `MongoExpeditionRuntimeStateStore(collection=...)` built via `db.client` (existing Motor client), no per-request client, no startup provisioning writes | `wiring/shadow_hooks.py:_build_coordinator` | `test_create_shell_state_success` (integration coverage) | IMPLEMENTED |
| B2Q12 | RT2-B-2A scope 12 items + 11 exclusions | 12 authorized scope items tutti presenti in code+test; 11 exclusions verified (no Mark/Drain/Fragment, no API changes, no frontend, no shared-env, no Legendary/item hooks) | intero modulo + test suite | 35 wiring tests · 0 public API delta · 0 frontend delta | IMPLEMENTED |

**Deviations**: **0/12**. Auto-ratification: **0/12** (PM verdicts applicati verbatim).

## Requisito 8 · Tests 320/320 PASS

`pytest backend/tests/effect_engine/ -q` → **320 passed in 2.51s**. Zero regressione.

## Requisito 9 · Baseline 284 PASS

Baseline `RT2-A + RT2-B-1A + RT2-B-1B-1` = 136 + 91 + 57 = **284 tests · 284 PASS** invariante.

## Requisito 10 · Wiring tests 35 PASS

`pytest backend/tests/effect_engine/wiring/ -v` → **35 passed** (10 lifecycle + 7 guardrail + 10 anti-P2W/audit + 8 registry).

## Requisito 11 · Foundation test +1 PASS

Test `test_rt2b_active_flag_is_cdv_transient` (nuovo, ratifica registrazione `cdv_transient_state_enabled` in `RT2_B_RUNTIME_ATTIVABILE`). Test `test_rt2_future_constants_are_four` rinominato in `test_rt2_future_constants_are_three` (aggiornato per rispecchiare la nuova struttura). Foundation tests totali: 15 (14 pre-existing + 1 nuovo, aggiornato asserzioni).

## Requisito 12 · Double-gate contract

Guardrail applicato in ordine:
1. **FF gate**: `feature_flags.is_enabled("cdv_transient_state_enabled")` — short-circuit se OFF → return `(False, None)`.
2. **Eligibility gate**: `db.users.find_one({id, is_test_user=1})` — fail-closed su `is_test_user != True`.

Verificato con `test_guardrail_flag_off_returns_false` + `test_guardrail_flag_on_non_test_user_returns_false`. **Short-circuit garantito**: con FF OFF, zero DB access (verificato via smoke test `mock_db.users.find_one.call_count == 0`).

## Requisito 13 · Test-user fail-closed contract

Fail-closed su 4 scenari:
1. `is_test_user != True` → False.
2. `users.find_one` restituisce `None` (utente inesistente) → False.
3. `current_user["id"]` mancante/None → False.
4. `db.users.find_one` raise Exception (Mongo down) → False.

Verificato con `test_guardrail_missing_user_fail_closed` + `test_guardrail_db_error_fail_closed`. **NEVER FAIL-OPEN**.

## Requisito 14 · Feature flags default OFF

`cdv_transient_state_enabled` = default `False` (in assenza di env var `ORBUS_FLAG_CDV_TRANSIENT_STATE_ENABLED`). In produzione shared: env var non settata → flag rimane OFF. Attivazione solo via env var esplicita in ambiente locale/test.

`runtime_stat_soft_cap_enabled` = default `False` (soft cap NON autoritativo per B2Q07 verbatim).

`item_effect_engine_enabled`, `cdv_item_hooks_enabled`, `effect_observability_enabled` = hard-forced `False` in `RT2_FUTURE_CONSTANTS`.

## Requisito 15 · Legacy path authoritative

Il calcolo corrente (`compute_team_power`, `compute_success_chance`, threat resolution, XP multipliers, loot roll, materials roll) resta **AUTORITATIVO**. Lo shadow wiring:
- **Non modifica** `team_power` / `success_chance` / `final_score` / `gold_reward` / `xp_reward` / `loot`.
- **Non emette side-effect** su `db.expeditions` / `db.adventurers` / `db.guilds` / `db.inventory_items`.
- **Non altera** il codice di calcolo autoritativo (nessuna riga modificata nelle funzioni di calcolo).

## Requisito 16 · Shadow calculation behavior

Shadow evaluation è **audit-only** (event `runtime_stat_shadow_evaluated`). Nessun campo response, nessun bonus applicato. Il `evaluation_hash` è un digest SHA256 stabile del subset whitelist per correlare log senza esporre PII/RNG.

## Requisito 17 · State lifecycle shell behavior

Shell state document creato in `expedition_runtime_states` (DB isolato `orbus_r16_rt2b_test`) con:
- `state_version=1`, `fencing_token=0`, `runtime_status=ACTIVE`.
- `adventurer_class_states=()`, `processed_event_keys=()`, `last_event_sequence=0`, `owner_worker_or_lease_id=None`, `lease=None`.
- TTL: `expires_at = created_at + 6h` (B0Q07 verbatim upstream).
- Terminalization: `expire_state` → `runtime_status=EXPIRED`, retention 24h post-completion.

## Requisito 18 · No Mark transitions

`ExpeditionRuntimeState.adventurer_class_states` = `()` shell vuoto. **Nessuna** invocazione di `apply_event_once` con `type="mark_applied"` / `"mark_refreshed"` / `"mark_expired"` nel runtime applicativo. Verificato via `grep`: 0 occorrenze nel modulo `wiring/`.

## Requisito 19 · No Drain transitions

**Nessuna** invocazione di `apply_event_once` con `type="drain_started"` / `"drain_resolved"` nel runtime. Verificato via `grep`: 0 occorrenze.

## Requisito 20 · No Fragment transitions

**Nessuna** invocazione con `type="fragment_gained"` / `"fragment_spent"`. `fragment_count=0` invariante nel shell state.

## Requisito 21 · Mongo allowlist

DB target enforcement via `coordinator._is_db_allowlisted`:
- **Consentiti**: `orbus_r16_rt2b_test` (exact) + pattern regex `orbus_r16_rt2b_it_<alphanumeric_underscore>`.
- **Vietati (blocklist esplicita)**: `orbus_r16`, `orbus_r16_test`.
- **Vietati (fallback)**: qualsiasi altro nome (empty, preview, staging, production).

Fail-closed: DB non allowlisted → coordinator ritorna `DB_NOT_ALLOWLISTED` senza tentare create/expire. Test: `test_db_forbidden_no_op` + `test_terminalize_forbidden_db_deferred`.

## Requisito 22 · No shared/live writes

`writes to orbus_r16 = 0` · `writes to orbus_r16_test = 0` · `writes outside allowlisted local Mongo = 0` in P0 e in P2A code implementation. La suite test usa `FakeExpeditionRuntimeStateStore` in-memory (0 write reali). L'attivazione shadow richiede env var + user + DB allowlist coincidentemente presenti.

## Requisito 23 · API paths invariant

`openapi_paths_total = 275` (verificato via `curl /api/openapi.json` + JSON parse) — **invariante rispetto a RT2-B-1B-1 closure**. Nuove rotte `runtime`/`shadow`/`wiring` = **0**.

## Requisito 24 · Response contract invariant

`expedition_public()` shape verificato via `test_expedition_public_contract_unchanged`: nessuna chiave con prefisso `runtime_state_` / `shadow_` / `class_state_`. Campi legacy (`id`, `guild_id`, `dungeon_id`, `status`, `team_power`, `success_chance`, `gold_reward`, `xp_reward`) tutti presenti nel payload player-facing.

## Requisito 25 · Rewards invariant

`gold_reward` / `xp_reward` / loot / materiali / achievement / quest / contract / seasonal counters **byte-identici** al pre-RT2-B-2A. Il hook T1 è **post `insert_one(exp_doc)`** e il hook T2 è **post terminalization**; entrambi try/except non-blocking, non partecipano al calcolo autoritativo.

## Requisito 26 · Audit scope

5 event id emessi (verbatim B2Q05):
- `runtime_stat_shadow_evaluated` (T1 pre-create, audit-only).
- `runtime_state_created` (T1 create_state SUCCESS o ALREADY_EXISTS silent).
- `runtime_state_terminalized` (T2 expire_state SUCCESS o DEDUPLICATED_NO_OP).
- `runtime_state_shadow_failure` (create/expire exception o DB not allowlisted).
- `runtime_state_cleanup_deferred` (NOT_FOUND terminalize o cleanup lasciato a TTL).

Emesso via `logger.info("audit_event <json>")` con whitelist campo enforced e blacklist rifiuto record. **Nessuna nuova collection audit** · **nessun endpoint pubblico** · **nessun campo di risposta** · **nessun log player-facing**.

## Requisito 27 · Kill-switch

Rollback tramite:
1. **FF-off kill switch**: unset `ORBUS_FLAG_CDV_TRANSIENT_STATE_ENABLED` + restart backend → shadow wiring inibito immediatamente. State documents esistenti restano nel DB isolato, TTL sweep li rimuove.
2. **Env target invalidation**: settare `ORBUS_RT2B_WIRING_TARGET_DB` a DB non-allowlisted → coordinator returns `DB_NOT_ALLOWLISTED` per ogni hook.
3. **Guardrail deny (mass)**: admin toggle `users.is_test_user=False` per tutti gli utenti test → nessuna shadow evaluation triggerata.

## Requisito 28 · Rollback plan

- **Layer 1 (immediate)**: FF-off via env variable + restart. Nessuna azione codice/DB richiesta.
- **Layer 2 (code)**: revert commit RT2-B-2A → touchpoint ripristinano behavior pre-2A. State documents orphan cleaned by TTL 6h/24h.
- **Layer 3 (DB, local isolated only)**: `db.expedition_runtime_states.drop()` in `orbus_r16_rt2b_test` → riprovisioning via RT2-B-1B-1 `ProvisioningCommand`.

**Data loss risk**: **ZERO** (state document transient, nessun dato player persistente).

## Requisito 29 · Runtime activation NOT authorized

Attivazione runtime `cdv_transient_state_enabled=true` in ambiente shared/preview/staging/production: **NOT AUTHORIZED**. Rimane vincolata a `LOCALHOST ISOLATED ONLY` (B2Q10 verbatim). Nessun dispatch orchestrator autorizza activation shared-env in RT2-B-2A.

## Requisito 30 · Tester gameplay activation NOT authorized

Attivazione gameplay per tester `@orbus.test` in ambiente condiviso: **NOT AUTHORIZED**. Il tester può solo eseguire flow con FF OFF (behavior identico al pre-RT2-B-2A). Activation isolata riservata a step successivo (RT2-B-2D o equivalente) con dispatch orchestrator dedicato.

## Requisito 31 · Governance evidence

- `sealed integrity tests = 6 passed` · `sealed artifacts = 36/36 byte-identical` (verificato in P3 closure).
- `effect_engine tests = 320/320 passed` (baseline 284 + foundation +1 + wiring +35).
- `lore_meta.py` SHA `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` · **INVARIANT**.
- **Baseline chain 13/13 byte-identical**: `IS2-A · IS2-B-P1 · IS2-B-P1-N1 · IS2-B-P2A · IS2-B-P2B-1 · IS2-B-P2B-RT1 · IS2-B-P2B-RT2-P0 · IS2-B-P2B-RT2-A · IS2-B-P2B-RT2-B-P0 · IS2-B-P2B-RT2-B-1A · IS2-B-P2B-RT2-B-1B-P0 · IS2-B-P2B-RT2-B-1B-1 · IS2-B-P2B-RT2-B-2-P0`.
- API paths totali = 275 invariante.
- Frontend changes = 0 · OpenAPI changes = 0 · persistent user schema unchanged.
- Registry v3 changes = 0 · item generation runs = 0 · FF activation runtime = 0.
- Writes to `orbus_r16` = 0 · writes outside allowlisted local Mongo = 0.
- `NEW SEAL = NO`.

## Requisito 32 · Explicit STOP

Formal closure `RT2-B-2A` completa. Nessuna auto-progressione autorizzata. **HOLD assoluti**: RT2-B-2B · shared-env · tester gameplay activation · RT2-C/D/E · Phase 2B item assignment · Registry v3.

**`STRICT STOP · Phase 3 closure documentale · fine`**.

---

**Fine documento** · Italian_only · RT2-B-2A PM-LOCKED · SHA Policy §31 · STRICT STOP
