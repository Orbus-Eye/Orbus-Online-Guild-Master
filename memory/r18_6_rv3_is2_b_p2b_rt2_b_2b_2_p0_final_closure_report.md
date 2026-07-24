# R18.6.RV3-IS2-B-P2B-RT2-B-2B-2-P0 · FINAL CLOSURE REPORT

**Gate**: `R18.6.RV3-IS2-B-P2B-RT2-B-2B-2-P0`
**Canonical name**: DRAIN TRANSITION FOUNDATION READINESS & COMPLETION-TO-FRAGMENT CONTRACT
**Status**: **CLOSED · PM-LOCKED**
**Closure date (UTC)**: 2026-02
**PM authority**: Message 168 (dispatch) · Message 170 (patch + adjudication + closure)
**Regime**: documentale · localhost isolated · default-OFF · test-user fail-closed · no shared-env · no human tester · no public API · no frontend
**Baseline chain**: 15 → **16/16**

---

## 1 · Executive summary

Il gate `RT2-B-2B-2-P0` chiude formalmente la fase di readiness/discovery per il futuro codice Drain. Le 16 questioni PM (**B2B2Q01…B2B2Q16**) sono state adjudicate verbatim in PM Message 170 e integrate nel readiness draft. Zero auto-ratifications da parte dell'agent. La normalizzazione lessicale "quintuple-gate" → "**6-conditions gate**" (PM §13) è applicata a tutti i draft. Sono introdotti due hard-lock supplementari (PM §18): `max active Drain per (source,target) = 1` e `max active Drain per Mark application = 1`. Il code gate futuro autorizzato in seguito è `R18.6.RV3-IS2-B-P2B-RT2-B-2B-2-1` con V1 subordinato `RT2-B-2B-2-1-V1`.

## 2 · 16/16 B2B2Q · verdict PM Message 170 verbatim

| ID | Titolo sintetico | Verdict PM | Sintesi vincolo |
|---|---|---|---|
| B2B2Q01 | Drain execution ID | `PM_RATIFIED_WITH_CONDITIONS` · A | `drn-<UUIDv4 completo>` · non troncato · non client-provided · replay stesso start → prior ID |
| B2B2Q02 | Trusted event source | `PM_RATIFIED` · A | Reuse `trusted_context` (auth user, is_test_user, env, target Mongo, expedition identity, ownership, feature-flag snapshot) |
| B2B2Q03 | Mark binding + refresh | `PM_RATIFIED` · A | Strict `application_id` invariance · refresh preserva Drain · reapplication invalida |
| B2B2Q04 | Mark validation at completion | `PM_RATIFIED` · A | **15 rivalidazioni atomiche** obbligatorie · defense-in-depth |
| B2B2Q05 | Fragment amount | `PM_RATIFIED_WITH_CONDITIONS` · A | **`fragment_gain_requested = 1` fisso** · vietati RNG/scaling/bonus |
| B2B2Q06 | Fragment outcome at cap | `PM_RATIFIED` · A | Al cap → COMPLETED · `applied=0`, `overflow_discarded=1` · no cancel/reject/proc/alt reward |
| B2B2Q07 | Completion-to-Fragment contract | `PM_RATIFIED_WITH_CONDITIONS` · A | **15-field receipt EMBEDDED in processed event receipt** · NO seconda slot |
| B2B2Q08 | Cancellation reason codes | `PM_RATIFIED` · A | **NO extensions** · 8 verbatim RT2-B-2B-P0 · nuove necessità → STOP/PM REVIEW |
| B2B2Q09 | Result codes canonici | `PM_RATIFIED_WITH_CONDITIONS` · A | Success 3 · start rejection 10 · state 3 · integrity/concurrency 5 |
| B2B2Q10 | Race completion vs cancellation | `PM_RATIFIED` · A | First-committed-wins · single writer · client clock non decide |
| B2B2Q11 | Race completion vs phase_end | `PM_RATIFIED_WITH_CONDITIONS` · A | **1 reserved receipt per lifecycle batch** (NON per drain) · simultaneous Drain hard cap NOT INTRODUCED · 8 reserved = 8 batch |
| B2B2Q12 | Lease e retry | `PM_RATIFIED` · A | 1 lease per event batch · fencing+CAS+lease mandatory · retry max 3 · 7 revalidations per retry |
| B2B2Q13 | Feature flag composition | `PM_RATIFIED` · A | `cdv_drain_transitions_enabled` (default OFF) · **6-conditions gate** ("quintuple-gate" DEPRECATO) |
| B2B2Q14 | Receipt classification + folding | `PM_RATIFIED_WITH_CONDITIONS` · A | Lazy Mark-expiration cancel **FOLDED** nella receipt ordinaria del triggering event · NO seconda receipt |
| B2B2Q15 | Audit contract | `PM_RATIFIED_WITH_CONDITIONS` · A | 10 event ids · sampling INFO/WARN/ERROR 100% · min fields specificati |
| B2B2Q16 | First code-gate scope | `PM_RATIFIED_WITH_CONDITIONS` · A | Code gate `RT2-B-2B-2-1` + V1 subordinato `RT2-B-2B-2-1-V1` · V1 NON incrementa baseline |

**Auto-ratifications by agent: 0.**

## 3 · Hard-lock supplementari (PM Message 170 §18)

Integrati nel readiness draft §9/§14:

| Hard-lock | Valore |
|---|---|
| `max active Drain per (source, target) pair` | **1** |
| `max active Drain per Mark application (mark_id, required_mark_application_id)` | **1** |
| Rejection code su violazione | `DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR` |
| Drain terminali (COMPLETED/CANCELLED/EXPIRED) | possono restare nello storico bounded fino a scadenza state document · NON bloccano nuova execution su nuova applicazione |
| `Drain consumes Mark` | **false** (invariante preservata) |
| `Fragment amount per accepted completion` | **1** (invariante preservata) |
| `Drain completion at Fragment cap` | **accepted with overflow discarded** (invariante preservata) |

## 4 · Normalizzazione lessicale "quintuple-gate" → "6-conditions gate"

PM Message 170 §13: `logical eligibility conditions = 6`. La dicitura "quintuple-gate" è **DEPRECATA**. Nel draft patchato l'unica menzione di "quintuple-gate" resta come nota di deprecazione (2 occorrenze totali, entrambe con marker "DEPRECATED"/"non usare"). Tutti i riferimenti canonici usano `6-conditions gate`.

Composizione (verbatim):
```
1. cdv_transient_state_enabled
2. AND cdv_class_transitions_enabled
3. AND cdv_drain_transitions_enabled
4. AND authenticated user.is_test_user
5. AND environment = localhost isolated
6. AND Mongo target = allowlisted database
```

## 5 · Governance final verification

| Item | Comando/riferimento | Valore |
|---|---|---|
| Combined `effect_engine + sealed` | `pytest tests/effect_engine/ tests/backend_r18_4_sealed_integrity_test.py` | **402 PASS · 0 FAIL · 1 warn benign · 3.10 s** |
| Sealed 36/36 byte-identical | 19 pre + 11 R18.4 + 6 followup | **PASS** |
| `lore_meta.py` SHA | `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` | **INVARIANT** |
| OpenAPI paths | `len(app.openapi()['paths'])` | **275** (invariant · 0 new routes) |
| Frontend / `.env` / Registry / Mongo provisioning changes | diff | **0** each |
| Feature flag activation | production toggle | **0** |
| Non-allowlisted DB writes | fixture allowlist enforcement | **0** |
| Residual integration databases | teardown scan | **0** |
| NEW SEAL | closure regime | **NO** |

## 6 · Fail-stop status P0 (10 items)

**Fail-stop count: `0 / 10`.** Nessun blocker documentale rilevato in tutta la fase P0 (draft + patch + closure).

## 7 · Deliverable prodotti in questa closure

| Deliverable | Path | SHA256 |
|---|---|---|
| Final closure report · MD | `/app/memory/r18_6_rv3_is2_b_p2b_rt2_b_2b_2_p0_final_closure_report.md` | *(SHA §chat-report)* |
| Final closure report · JSON | `/app/memory/r18_6_rv3_is2_b_p2b_rt2_b_2b_2_p0_final_closure_report.json` | *(SHA §chat-report)* |
| Closure manifest | `/app/memory/r18_6_rv3_is2_b_p2b_rt2_b_2b_2_p0_closure_manifest.json` | **NOT_EMBEDDED** (external §31 · chat report only) |
| PRD append | `/app/memory/PRD.md` (occurrence count = 1 · idempotent) | pre/post SHA in chat report |

## 8 · Baseline chain

**15 → 16/16** · unico nuovo elemento: `RT2-B-2B-2-P0` · V1 futuro (`RT2-B-2B-2-1-V1`) NON incrementerà separatamente.

## 9 · HOLD attivi

- `RT2-B-2B-2-1` (code gate DRAIN) — attende explicit orchestrator dispatch
- `RT2-B-2B-2-1-V1` (real-Mongo Drain verification · subordinato · no baseline increment)
- Human tester activation — NOT AUTHORIZED
- Shared-env rollout — separate PM sign-off required
- Feature flag `cdv_drain_transitions_enabled` — remains OFF
- Focus bonus mutation — DEFERRED (RT2-C effect execution / RT2-E item hooks)
- Damage/healing/XP/loot/guild XP/item effects/proc/cooldown — OUT OF SCOPE (RT2-C+)

## 10 · Verdict

**`RT2-B-2B-2-P0 CLOSED · PM-LOCKED`** — 16/16 B2B2Q PM-adjudicated verbatim · 0 fail-stop emessi · 0 design deviations · 0 code changes · 0 Mongo writes · 0 feature activation · governance chain 15→16/16 ratified.

**STRICT STOP.** NON aprire code gate `RT2-B-2B-2-1` in questo dispatch. NON invocare `testing_agent` / `e1_tester`. Attesa dispatch orchestrator successivo per code gate DRAIN.
