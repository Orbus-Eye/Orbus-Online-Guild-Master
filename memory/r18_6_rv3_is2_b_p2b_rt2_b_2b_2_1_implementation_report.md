# R18.6.RV3-IS2-B-P2B-RT2-B-2B-2-1 · DRAIN TRANSITION & COMPLETION-TO-FRAGMENT FOUNDATION — IMPLEMENTATION REPORT (Phase A)

**Gate**: `R18.6.RV3-IS2-B-P2B-RT2-B-2B-2-1`
**Stato**: **IMPLEMENTED / PM-CLOSURE-PENDING / V1-REQUIRED**
**Executor**: Claude Fable (Emergent) · nuova sessione dedicata
**Fonte tecnica**: repository GitHub `Orbus-Eye/Orbus-Online-Guild-Master`
**Contratto canonico**: P0 `RT2-B-2B-2-P0` (CLOSED · PM-LOCKED · 16/16 B2B2Q verbatim)
**Baseline chain**: **16/16 INVARIATA** (nessun increment · closure vietata fino a V1 PASS)

---

## 1 · Executor capacity & GitHub preflight

```text
EXECUTOR_CONTEXT_CAPACITY = SUFFICIENT FOR COMPLETE PHASE A
CONTEXT_ANCHOR_PASS
```

| Anchor | Valore |
|---|---|
| Repository | `Orbus-Eye/Orbus-Online-Guild-Master` |
| Branch | `main` |
| Base commit (HEAD == origin/main, fetch eseguito) | `be9f62ff1419835a66af5291f2768db467361d11` |
| RT2-B-2B-2-1 partial files | **0** |
| Working tree unexpected changes (gate-attribuibili) | **0** |
| RT2-B-2B-2-P0 | CLOSED / PM-LOCKED |
| RT2-B-2B-2-1 PRD closure occurrence | 0 |
| Sealed integrity | **6 PASS** |
| Sealed artifacts | **36/36 byte-identical** |
| `lore_meta.py` SHA | `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` (invariante pre e post) |
| OpenAPI paths | **275** (invariante pre e post) |

**Nota piattaforma (non gate)**: il fork pod ha riscritto in 42 file tracked stringhe d'ambiente (URL preview / JOB_ID / UUID storici → `drain-dispatch`). Due file **SEALED** (`backend/app/scripts/round18_3e_apply_bridge.py`, `backend/app/scripts/round18_reset1b_apply_v1_3.py`) risultavano corrotti dalla sostituzione: **ripristinati byte-identical** da `origin/main` (fonte autoritativa) → sealed integrity tornata 6/6 PASS. Nessuna correzione applicata ad altri file non-gate (memory/log/test_reports restano come lasciati dalla piattaforma). Ricreato `backend/tests/.env.test` (gitignored, assente post-fork) secondo `pytest_db_isolation_policy.md`.

---

## 2 · Scope implementato (B2B2Q16 verbatim)

- `START_DRAIN` (`NOT_STARTED → STARTED`) · `COMPLETE_DRAIN` (`STARTED → COMPLETED`) · `CANCEL_DRAIN` (`STARTED → CANCELLED`) + tutti i rejection paths
- `drain_execution_id = "drn-" + canonical UUIDv4` completo, server-authoritative (B2B2Q01) · replay START → prior ID (dedup, nessun nuovo Drain)
- Mark/application binding strict (B2B2Q03) · refresh valido non invalida · nuova application invalida
- Completion-time Mark revalidation (B2B2Q04 · checks 1–12 pure-level; 13–15 lease/fencing/state_version dispatcher/store-side)
- Completion-to-Fragment **atomic batch** (B2B2Q07): status RESOLVED + Fragment decision fixed=1 (B2B2Q05) + overflow discard (B2B2Q06) + segment opening 0→positive (`"sg-"` prefix) + payload EMBEDDED + receipt + `state_version` +1 exactly once — **single CAS all-or-nothing**
- Fold-cancellation lazy (B2B2Q14): MARK_EXPIRED / MARK_APPLICATION_CHANGED / MARK_OWNERSHIP_MISMATCH a completion-time → Drain auto-CANCELLED **committato nella stessa unica receipt ordinaria** del triggering event
- Lifecycle bulk cancellation (B2B2Q11): PHASE_END / EXPEDITION_TERMINAL → tutti i Drain STARTED cancellati in **1 reserved lifecycle receipt per batch** (count + bounded list ≤ 32 id) · nessun hard cap globale di Drain concorrenti introdotto
- Hard-lock PM §18: max 1 Drain attivo per (source,target) pair · max 1 per Mark application · Drain terminali non bloccano
- Lease + fencing + CAS 8-step riusati · retry max 3 · CAS-only senza lease FORBIDDEN · no background renewer
- Feature flag dedicato `cdv_drain_transitions_enabled = false` (default OFF) · **6-conditions gate** (B2B2Q13) · kill-switch surgical: OFF ⇒ 0 DB calls · 0 audit events · 0 mutations, Mark/Fragment invariati
- Audit: 10 event ids B2B2Q15 + campi minimi whitelisted
- Il Drain NON consuma il Mark · NON spende Fragment · NON chiude segment · NON muta `focus_bonus_usage` (§30 DEFERRED)

## 3 · File changes

Base commit: `be9f62f` · nessun commit locale creato (working tree pronta per review PM).

### Nuovi (5)
| File | SHA256 (16) | Linee |
|---|---|---|
| `backend/app/stats/runtime/transitions/drain.py` | `30048e1ff0a12272` | 661 |
| `backend/tests/effect_engine/transitions/test_drain_pure.py` | `cb2c80af92d6dee3` | 450 |
| `backend/tests/effect_engine/transitions/test_drain_dispatcher.py` | `ad4ca1e81331dc6f` | 610 |
| `backend/tests/effect_engine/transitions/test_drain_mocked_mongo.py` | `1afb86bfd344cd10` | 184 |
| `backend/tests/effect_engine/transitions/test_drain_perf_fakestore.py` | `26f24b4203e7d579` | 161 |

### Modificati (9) — pre/post SHA256 (16)
| File | pre | post |
|---|---|---|
| `backend/app/stats/runtime/feature_flags.py` | `ba27066a956d7e72` | `342fb6b857199f16` |
| `backend/app/stats/runtime/state_store/models.py` | `f849fa87148c9b1e` | `21013daf0fe15cab` |
| `backend/app/stats/runtime/transitions/dispatcher.py` | `3ffb62f550f635e0` | `3b742df59f27f634` |
| `backend/app/stats/runtime/transitions/models.py` | `2150f08c02bd22f1` | `61cf98fea5299bb5` |
| `backend/app/stats/runtime/wiring/audit.py` | `7c344c49ba25b948` | `5bc68c8640385714` |
| `backend/app/stats/runtime/wiring/coordinator.py` | `4ce05b28a4800630` | `757eaa89c4254b13` |
| `backend/tests/effect_engine/foundation/test_feature_flags.py` | `dae77e3d6068a389` | `4f33482195fe80c5` |
| `backend/tests/effect_engine/transitions/conftest.py` | `623cc693e6c298b9` | `1324f839485ce3b4` |
| `backend/tests/effect_engine/wiring/test_response_invariance.py` | `a530a7b602c08dd0` | `3a8fe6aa47cb6031` |

Diff (gate files): **9 file modificati · +375 / −68** + 5 nuovi file (2.066 linee).
File boundary §15: **rispettato** — nessuna modifica a `state_store/interface.py`, `fake_store.py`, `mongo_adapter.py`, API pubbliche, frontend, OpenAPI, reward formulas, Registry, `.env`, shared env, persistent user schema.
Riuso confermato: `DrainDoc` · `DrainStatus` · `active_drain_executions` (estesi additivamente: `mark_id`, `cancelled_at`, `cancellation_reason`, `drain_version`, `start_event_id`, `completion_payload`).

## 4 · Design note dichiarate (0 deviazioni sostanziali · 2 realizzazioni boundary-compliant)

1. **B2B2Q07 EMBEDDED payload — realizzazione boundary-compliant**: le `EventReceipt` sono costruite store-side (`apply_event_once`, file fuori boundary §15). Il payload 15-campi è quindi persistito nel `DrainDoc.completion_payload` **dentro lo stesso singolo CAS atomico** che scrive la processed event receipt, con linkage 1:1 (`completion_payload.completion_event_id == receipt.event_id`, sequence/version mirrorati). Invariante PM preservato al 100%: **una sola receipt ORDINARY consumata · MAI un secondo slot** (verificato dai test d01/mm01: 3 receipt per mark+start+complete). Nessuna condizione `SECOND_RECEIPT_SLOT_REQUIRED` attivata.
2. **`TrustedDrainReceipt` fixture (P0 §43)**: NON rimossa in questa Phase A. Il dispatch orchestrator §3 non la include nello scope e la rimozione modificherebbe il comportamento legacy `GAIN_FRAGMENT` (fail-stop `LEGACY_RESPONSE_OR_REWARD_DRIFT`). Rimozione/migrazione deferita ad adjudication PM (nota aperta per closure).

## 5 · Test matrix — 63 nuovi test · 459 totali

```text
failed = 0 · unexpected skipped = 0 · design deviations = 0 · fail-stops = 0
```

| Suite | Test | Esito |
|---|---|---|
| `test_drain_pure.py` (pure · 0 network/DB) | 31 | 31 PASS |
| `test_drain_dispatcher.py` (FakeStore + coordinator gating/audit) | 26 | 26 PASS |
| `test_drain_mocked_mongo.py` (adapter CAS semantics) | 5 | 5 PASS |
| `test_drain_perf_fakestore.py` (benchmark p95) | 1 | 1 PASS |
| effect_engine baseline (non-mongo) | 300 | 300 PASS (invariati) |
| effect_engine real-Mongo esistenti (2B-1 V1 heritage) | 96 | 96 PASS seriale¹ |
| sealed integrity | 6 | 6 PASS |

¹ `test_perf_mongo_p95` (test p95 real-Mongo del gate parent) è load-sensitive sotto xdist parallelo: PASS ripetuto in esecuzione seriale/isolata (9/9). Pre-esistente, non correlato al gate.

Copertura casi §16 dispatch: valid START (p02,d01) · Mark assente/scaduto/foreign/application mismatch (p04,p05,p08,p21) · replay START (d02,mm02) · cap pair/application (p09,p10,d17) · valid COMPLETE (p12,d01,mm01) · completion dopo refresh (p19) · dopo expiration/reapplication (p20,p21,d07,mm03) · dopo cancellation/phase end/terminalization (p25,d05,d08,d10) · duplicate completion (p24,d04,mm04) · payload mismatch (d03) · explicit cancellation (p26,d05) · lifecycle bulk (p30,p31,d08,d09,mm05) · atomicity (d01,mm01) · fixed gain=1 (p12) · overflow al cap (p17,d25) · segment opening/preservation (p15,p16) · focus invariance (p18) · winner-only race (d05,d06,p28) · lease failure (d12) · stale fencing (d13) · CAS conflict + retry limit (d14) · receipt cap (d15) · folding (d07,mm03) · lifecycle receipt aggregation (d08,mm05) · flag OFF (d18,d22,d23) · non-test user (d20) · environment/allowlist (d21) · legacy response invariance (d19,d26 + 300 baseline) · legacy reward invariance (d26 + baseline fragment suite).

## 6 · Result-code coverage (B2B2Q09 canonical set — 21/21)

| Codice | Test |
|---|---|
| DRAIN_STARTED | p02 · d01 |
| DRAIN_COMPLETED | p12 · d01 · mm01 |
| DRAIN_CANCELLED | p26 · d05 |
| DRAIN_ALREADY_IN_PROGRESS_FOR_PAIR | p09 · p10 · d17 |
| MARK_NOT_FOUND | p04 · d17 |
| MARK_EXPIRED | p05 (start) · p20/d07/mm03 (fold) |
| MARK_OWNERSHIP_MISMATCH | p08 · p22 |
| MARK_APPLICATION_CHANGED | p21 |
| TARGET_INVALID | p06 · d17 |
| SOURCE_INVALID | p07 · p27 |
| EXPEDITION_TERMINAL_REJECTED | d10 |
| PHASE_INACTIVE | d08 · d11 |
| RECEIPT_CAP_REACHED | d15 |
| DRAIN_NOT_STARTED | p23 · d16 |
| DRAIN_ALREADY_COMPLETED | p24 · p28 · d04 · d06 |
| DRAIN_ALREADY_CANCELLED | p25 · p29 · d05 |
| EVENT_ID_PAYLOAD_MISMATCH | d03 |
| STATE_VERSION_CONFLICT | d14 (trigger retry path) |
| STALE_WRITER_REJECTED | d13 |
| LEASE_ACQUISITION_FAILED | d12 · d25 |
| RETRY_LIMIT_REACHED | d14 (3 tentativi esatti) |

Cancellation reason codes: 8/8 canonici, `NO extensions` (p27 verifica rejection di reason non canonico · `len(CANONICAL_CANCELLATION_REASONS) == 8`).

## 7 · Performance FakeStore (§17 · 120 iterazioni · p95)

| Metrica | Misurato | Target | Esito |
|---|---|---|---|
| START_DRAIN p95 | 0.155 ms | ≤ 35 ms | PASS |
| COMPLETE_DRAIN + Fragment p95 | 0.152 ms | ≤ 35 ms | PASS |
| CANCEL_DRAIN p95 | 0.117 ms | ≤ 35 ms | PASS |
| deduplicated retry p95 | 0.076 ms | ≤ 25 ms | PASS |
| flags-OFF overhead p95 | 0.042 ms | ≤ max(5%, 1 ms) | PASS |

Queste metriche **non sostituiscono** la V1 real-Mongo.

## 8 · Feature gating · atomicity · receipt · audit

- **Gating (B2B2Q13)**: `cdv_drain_transitions_enabled` default OFF · 6-conditions gate. Test d18: OFF ⇒ store calls = 0, audit = 0, mutations = 0. Test d19: Mark/Fragment operativi con Drain OFF (surgical). Test d23: env flag default OFF governa in assenza di override. FF runtime activation in produzione = 0. `.env` changes = 0.
- **Atomicity (B2B2Q07)**: completion senza decisione Fragment / Fragment senza completion / doppio Fragment su retry / mutation parziale = IMPOSSIBILI (single CAS; test p24, d04, mm01, mm04). `state_version` +1 exactly once per batch (d01, mm01).
- **Receipt (B2B2Q14)**: 512 totale / 504 ordinary / 8 reserved invariati · eviction/overwrite FORBIDDEN (store fail-closed, d15). START/COMPLETE/CANCEL espliciti = ORDINARY. Fold lazy = stessa receipt del triggering event (d07, mm03). Lifecycle = 1 reserved receipt per batch con count + bounded list (d08, mm05). 8 slot riservati = 8 lifecycle batch (nessun cap globale Drain introdotto).
- **Audit (B2B2Q15)**: 10/10 event ids emessi e verificati (d24, d25): `cdv_drain_started · cdv_drain_start_rejected · cdv_drain_completed · cdv_drain_completion_rejected · cdv_drain_cancelled · cdv_drain_cancellation_rejected · cdv_drain_duplicate_completion · cdv_drain_fragment_batch_applied · cdv_drain_fragment_overflow_discarded · cdv_drain_transition_conflict`. Whitelist campi estesa con i campi minimi PM; blacklist invariata (no payload Mongo completo, no credenziali, no RNG, no reward).

## 9 · Regressioni & invarianti

- effect_engine baseline: 300/300 PASS invariati (serial + xdist) · real-Mongo heritage 96/96 PASS seriale
- sealed integrity 6 PASS · sealed artifacts 36/36 byte-identical
- `lore_meta.py` SHA invariante · OpenAPI 275 paths (0 nuove route) · frontend changes = 0 · Registry = 0 · item-gen = 0 · Mongo provisioning changes = 0 · reward formulas = 0 · persistent user schema = 0
- Legacy result-code behavior invariato (`RETRY_CEILING_EXCEEDED` / `CAS_WITHOUT_VALID_LEASE` / `PHASE_ENDED` / `EVENT_POST_TERMINAL_REJECTED` restano i codici legacy per eventi non-Drain; i codici canonici Drain si applicano SOLO ai 3 nuovi event types)

## 10 · Fail-stop

**Attivati: 0/18.** Nessun `TRUNCATED_EXECUTION_ID` · `CLIENT_AUTHORITATIVE_EXECUTION_ID` · `COMPLETION_FRAGMENT_ATOMICITY_FAILURE` · `SECOND_RECEIPT_SLOT_REQUIRED` · `LIFECYCLE_RECEIPT_PER_DRAIN_REQUIRED` · `DRAIN_REWARD_OR_EFFECT_DEPENDENCY` · `FOCUS_USAGE_MUTATION_REQUIRED` · `PUBLIC_API_MODIFICATION_REQUIRED` · `FRONTEND_MODIFICATION_REQUIRED` · `SHARED_ENVIRONMENT_REQUIRED` · `RECEIPT_EVICTION_REQUIRED` · `CAS_WITHOUT_VALID_LEASE` · `TEST_USER_BOUNDARY_VIOLATION` · `DB_SCOPE_VIOLATION` · `LEGACY_RESPONSE_OR_REWARD_DRIFT` · `RUNTIME_MODULE_BOUNDARY_VIOLATION` · `TRANSITION_TEST_MATRIX_INCOMPLETE` · `CONTEXT_ANCHOR_FAIL`.

## 11 · Git / working tree status

```text
branch                = main
base commit           = be9f62ff1419835a66af5291f2768db467361d11
final local commit    = NONE (nessun commit creato · push/merge/PR non autorizzati)
working tree          = gate files (9 M + 5 ??) interamente attribuibili al gate
                        + artefatti piattaforma pre-esistenti (env substitution,
                        non toccati) + 2 sealed script RIPRISTINATI a HEAD
files changed (gate)  = 14 codice/test + 2 report memory
```

## 12 · Handoff V1 (`RT2-B-2B-2-1-V1 · REAL-MONGO DRAIN VERIFICATION` · PRE-AUTHORIZED / REQUIRED)

- Riusare fixture `provisioned_unique_db` (`orbus_r16_rt2b_it_<unique_run_id>`, teardown drop) del parent V1
- Matrice funzionale reale: start/complete/cancel · winner-only concurrency multi-worker · completion-to-Fragment atomicity · duplicate completion · cancellation races · receipt capacity 512/504+8 · BSON size al cap con Drain payload embedded (target < 210 KiB stimato P0 §42) · performance p95 reale · allowlist rejection · cleanup
- I test mocked-Mongo (`test_drain_mocked_mongo.py`) forniscono il template diretto per la versione real-Mongo
- V1 NON incrementa baseline · NON produce closure autonoma · formal closure e 16/16 → 17/17 vietati fino a V1 PASS

**Esito**: `RT2-B-2B-2-1 = IMPLEMENTED / PM-CLOSURE-PENDING / V1-REQUIRED` — **STRICT STOP**.
