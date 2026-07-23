# R18.6.RV3-IS2-B-P2B-RT2-B-2-P0 · Final Closure Report (Phase 1) · PM-LOCKED

**Regime**: `DOCUMENTAL_ONLY · Italian_only · SHA §31 · STRICT STOP`
**Gate ID**: `R18.6.RV3-IS2-B-P2B-RT2-B-2-P0 · LOCAL RUNTIME WIRING & CLASS-STATE INTEGRATION READINESS PLAN`
**Stato**: `PM-RATIFIED · CLOSED · PM-LOCKED`
**Anchor**: `lore_meta.py` SHA `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` · INVARIANT
**Data closure**: 2026-02 (UTC)

---

## Requisito 1 · PM verdict

**PM VERDICT VERBATIM 2026-02**: 12/12 B2Q ratificati (`B2Q01…B2Q12`). Wiring layer = `EXPEDITION SERVICE ORCHESTRATION LAYER`. Calcolo corrente resta autoritativo. First integration mode = `LOCAL SHADOW ONLY`. Test-user eligibility = server-side `is_test_user`, fail-closed. FF default OFF. State creation post-validation. State lifecycle only, no class transitions. Adapter = application-scoped dependency. Public API changes = 0. Frontend changes = 0. Shared-env activation = FORBIDDEN. Tester gameplay activation = NOT AUTHORIZED. First code gate = `RT2-B-2A`. Exclusions RT2-B-2A verbatim (soft-cap, Mark/Drain/Fragment transitions, class rewards, effect engine, proc/duration/cooldown, item hooks, Legendary, public API, frontend, shared-env writes, tester gameplay activation). `RT2-B-2B` = `PLANNED / HOLD`. Governance invariante.

## Requisito 2 · P0 CLOSED

`RT2-B-2-P0 = CLOSED · PM-LOCKED`. Nessuna modifica ulteriore autorizzata su artefatti P0. Phase 2 (`RT2-B-2A`) sarà inviata come dispatch orchestrator separato.

## Requisito 3 · 34/34 sections

MD companion e JSON companion mantengono `sections count = 34/34` verbatim in ordine e nome. `JSON parse = PASS` preservato.

## Requisito 4 · B2Q resolved = 12/12

Tutti i 12 B2Q sono `PM_RATIFIED_VERBATIM_2026_02`. Auto-ratification count = 0. Dettaglio nel JSON companion `section_32_pm_open_questions`.

## Requisito 5 · Wiring layer = expedition service orchestration

Verdict B2Q01 verbatim: `EXPEDITION SERVICE ORCHESTRATION LAYER` — ordine 11-step (auth → user load → adventurers/equipment → runtime calc → test-user+FF eval → RT2-A shadow → RT2-B lifecycle → prosecuzione legacy → risoluzione → terminalization → risposta invariata).

## Requisito 6 · Current calculation remains authoritative

Il calcolo corrente (`compute_team_power`, `compute_success_chance`, threat resolution, XP multipliers, loot roll, materials roll) resta **AUTORITATIVO** in RT2-B-2A. Il runtime state store è **shadow-only** senza autorità gameplay.

## Requisito 7 · First integration mode = local shadow only

Verdict B2Q02 + B2Q10 verbatim: shadow creation autorizzata solo con `cdv_transient_state_enabled=true AND is_test_user=true AND Mongo target=localhost allowlisted` (`orbus_r16_rt2b_test`, `orbus_r16_rt2b_it_<unique_run_id>`). Shell state vuoto, nessuna transizione gameplay.

## Requisito 8 · Test-user eligibility = server-side is_test_user, fail-closed

Verdict B2Q06 verbatim: authenticated server-side user record, campo `users.is_test_user`. **Vietati**: email hardcoded, query param, custom header, body flag, frontend override. **Fail closed**: missing user OR missing field OR `!= true` → shadow disabled.

## Requisito 9 · FF remain default OFF

Verdict B2Q07 verbatim: FF = server-side startup configuration, evaluated once at expedition lifecycle entry (**frozen per operation**). Attivazione `runtime_stat_shadow_enabled=true` + `cdv_transient_state_enabled=true` **SOLO** in test/local env. `runtime_stat_soft_cap_enabled = false` (soft cap NON autoritativo). Valori mancanti/invalidi → false. Nessun aggiornamento dinamico via DB/API.

## Requisito 10 · State created after expedition validation

Verdict B2Q02 verbatim: state creation **dopo validazione (dungeon gate, team size, retired/unassigned/level guards), prima della risoluzione (lazy sweep)**. Shell vuoto (Marchi vuoti, Drenaggi vuoti, Frammenti=0, receipt vuote).

## Requisito 11 · State lifecycle only, no class transitions

Verdict B2Q09 verbatim: `class gameplay transitions in RT2-B-2A = NONE`. Solo shell state vuoto. Mark apply/refresh/expire, Drain start/complete, Fragment gain/spend → gate successivo `RT2-B-2B · CLASS-STATE TRANSITION FOUNDATION = PLANNED / HOLD`.

## Requisito 12 · Adapter = application-scoped dependency

Verdict B2Q11 verbatim: `MongoExpeditionRuntimeStateStore` è application-scoped, one adapter per process, existing Mongo client lifecycle riutilizzato, collection handle injected, no per-request client, no startup provisioning writes, no implicit index/collection creation, costruito solo con host+db+collection allowlisted (B2Q10), senza flag mutation path non invocato.

## Requisito 13 · Public API changes = 0 · Frontend changes = 0

Verdict B2Q12 exclusions verbatim: public API changes = 0. Frontend changes = 0. OpenAPI scope invariante rispetto a RT2-B-1B-1 closure.

## Requisito 14 · Shared environment activation = forbidden

Verdict B2Q10 verbatim: LOCALHOST ISOLATED ONLY. Vietati: `orbus_r16`, `orbus_r16_test`, preview, staging, production. Shared-environment activation = **FORBIDDEN** in RT2-B-2A.

## Requisito 15 · Tester gameplay activation = not authorized

Verdict B2Q12 exclusions verbatim: tester gameplay activation = **NOT AUTHORIZED** in RT2-B-2A. Deferita a step successivo con dispatch orchestrator dedicato.

## Requisito 16 · First code gate = RT2-B-2A

Verdict B2Q12 verbatim: primo code gate autorizzato è `R18.6.RV3-IS2-B-P2B-RT2-B-2A · LOCAL SHADOW WIRING & STATE LIFECYCLE FOUNDATION`. Dispatch Phase 2 orchestrator separato.

## Requisito 17 · Exclusions RT2-B-2A (verbatim)

Verdict B2Q12 exclusions verbatim (11):
- Authoritative soft-cap.
- Mark / Drain / Fragment transitions.
- Class rewards.
- Effect engine.
- Proc / duration / cooldown.
- Item hooks.
- Legendary.
- Public API changes.
- Frontend.
- Shared-env writes.
- Tester gameplay activation.

## Requisito 18 · No Mongo writes during P0

`Mongo writes in P0 = 0`. Nessuna nuova collection, nessun nuovo index, nessun provisioning eseguito, nessun apply eseguito. Solo scritture su `/app/memory/` (5 file documentali: 2 patched + 3 closure artifact) + 1 PRD append.

## Requisito 19 · No code changes during P0

`Application code modifications in P0 = 0`. Nessun file `.py` applicativo modificato. Nessun nuovo modulo aggiunto ad `app/`. Discovery strettamente READ-ONLY.

## Requisito 20 · No runtime wiring during P0

`Runtime wiring in P0 = 0`. `MongoExpeditionRuntimeStateStore` continua a non essere istanziato dal runtime applicativo. Zero import fuori dal namespace `app/stats/runtime/state_store/*`.

## Requisito 21 · RT2-B-2B (transitions) = PLANNED / HOLD

`R18.6.RV3-IS2-B-P2B-RT2-B-2B · CLASS-STATE TRANSITION FOUNDATION = PLANNED / HOLD`. Mark apply/refresh/expire, Drain start/complete, Fragment gain/spend introdotti in RT2-B-2B. Nessuna implementazione autorizzata in RT2-B-2A.

## Requisito 22 · Governance evidence

- `sealed integrity tests = 6 passed` (verificato in P0).
- `sealed artifacts = 36/36 byte-identical`.
- `lore_meta.py` SHA `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` · **INVARIANT**.
- Baseline chain **12/12 byte-identical**: `IS2-A · IS2-B-P1 · IS2-B-P1-N1 · IS2-B-P2A · IS2-B-P2B-1 · IS2-B-P2B-RT1 · IS2-B-P2B-RT2-P0 · IS2-B-P2B-RT2-A · IS2-B-P2B-RT2-B-P0 · IS2-B-P2B-RT2-B-1A · IS2-B-P2B-RT2-B-1B-P0 · IS2-B-P2B-RT2-B-1B-1`.
- PRD SHA pre-append (P0): `0eb7477abdcda64ac1ca3c6d3272a04a089bad186b260f62ff7f13a1cb9a089b`.
- **PRD delta in questa closure Phase 1 = 1 append idempotente**.
- `NEW SEAL = NO`.

## Requisito 23 · RT2-A + RT2-B-1A + RT2-B-1B-1 files unchanged

- **RT2-A (38 file)** unchanged (24 code + 14 test).
- **RT2-B-1A (14 file)** unchanged (7 lib code + 7 test).
- **RT2-B-1B-1 (16 file)** unchanged (4 provisioning code + 12 integration test).

Total upstream code files invariance: **68/68 unchanged**.

## Requisito 24 · Combined effect-engine regression = 284/284 PASS

`pytest backend/tests/effect_engine/ -q` → **284 passed**.
Composizione: `RT2-A = 136` + `RT2-B-1A = 91` + `RT2-B-1B-1 = 57` = **284 combined**. Zero regressione.

## Requisito 25 · Explicit STOP

Formal closure `RT2-B-2-P0` completa. Nessuna scrittura ulteriore autorizzata in Phase 1. In attesa di dispatch separato **Phase 2 (`RT2-B-2A · LOCAL SHADOW WIRING & STATE LIFECYCLE FOUNDATION`)** da orchestrator.

**`STRICT STOP · Phase 1 documentale · fine`**.

---

**Fine documento** · Italian_only · DOCUMENTAL_ONLY · RT2-B-2-P0 PM-LOCKED · SHA Policy §31 · STRICT STOP
