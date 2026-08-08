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

---

# ADDENDUM · PM ADJUDICATION & CORREZIONE B2B2Q07 (Phase A conditionally ratified)

## A1 · Anomalia adjudicata

**Classificazione PM**: `B2B2Q07_PROCESSED_RECEIPT_PAYLOAD_LOCATION_MISMATCH`
La realizzazione iniziale persisteva il payload 15-campi in `DrainDoc.completion_payload`
(stesso CAS, 1 slot, linkage 1:1) — **non ratificata** come semanticamente equivalente a
"embedded in the processed-event receipt". Nessuna failure di atomicità · nessun secondo
slot consumato. Correzione deterministica confinata autorizzata con estensione minima del
file boundary (receipt/state-store models · FakeStore · Mongo adapter · test effect-engine).

**La §4.1 del report sopra è SUPERATA da questo addendum.**

## A2 · Correzione applicata

- `EventReceipt.result_payload: Optional[Dict] = None` (state_store/models.py): la
  processed-event receipt è ora la **FONTE AUTORITATIVA** del completion result.
- `apply_event_once(..., result_payload=None)` esteso in `interface.py`, `fake_store.py`,
  `mongo_adapter.py`: il payload è scritto **dentro la receipt, nello stesso singolo CAS**
  (`$push` receipt con payload embedded lato Mongo · EventReceipt lato Fake). Omesso quando
  `None` → receipt legacy byte-shape invariata.
- `complete_drain` (drain.py): costruisce il dict 15-campi **deterministicamente PRE-CAS**
  dallo schema canonico `DrainCompletionPayload` e lo consegna via
  `TransitionResult.result_payload`; il dispatcher lo passa allo store nello stesso CAS.
  Anche i **fold-commit** (B2B2Q14) embeddano il payload con `result_code = rejection` e
  `mark_valid_at_completion = false`.
- `DrainDoc` ridotto a **campi minimi**: status terminale · `completion_event_id`
  (linkage 1:1 con la receipt) · timestamp. `DrainDoc.completion_payload` NON è più
  popolato dal runtime (classificato **copia derivata non autoritativa · non usata**;
  soluzione preferita PM: nessuna duplicazione integrale).
- Vietati e verificati: seconda receipt = 0 · seconda mutation = 0 · secondo incremento
  `state_version` = 0 · persistenza post-CAS = 0 · doppia fonte autoritativa = 0.

## A3 · TrustedDrainReceipt — `DEPRECATED_COMPATIBILITY_ONLY`

Tipo legacy conservato (rimozione deferita a gate separato). Vincoli verificati dal nuovo
test `d27`: (a) `drain.py` non referenzia `TrustedDrainReceipt` (scan sorgente = 0);
(b) COMPLETE_DRAIN funziona con `trusted_drain_receipt=None`; (c) una fixture allegata al
nuovo percorso Drain è **ignorata** — non è fonte autoritativa del Fragment gain, nessun
gain fuori dal completion batch atomico, nessun reward/proc/mutation autonoma.

## A4 · File & SHA (correzione · pre = post Phase A iniziale, commit `5a07ab4`)

| File | pre (16) | post (16) |
|---|---|---|
| `backend/app/stats/runtime/state_store/models.py` | `21013daf0fe15cab` | `166339cb7dfffcb5` |
| `backend/app/stats/runtime/state_store/interface.py` | `3a26342fbc03bfc0` | `6b768441c9f393dd` |
| `backend/app/stats/runtime/state_store/fake_store.py` | `b6c841438741698a` | `d089b6052ffb453b` |
| `backend/app/stats/runtime/state_store/mongo_adapter.py` | `cafb968d41ce62b1` | `8c07fa9f19037880` |
| `backend/app/stats/runtime/transitions/drain.py` | `30048e1ff0a12272` | `d188d0fe5666f5f5` |
| `backend/app/stats/runtime/transitions/dispatcher.py` | `3b742df59f27f634` | `9896616d2dcac0d6` |
| `backend/app/stats/runtime/transitions/models.py` | `61cf98fea5299bb5` | `71cd6070549f4654` |
| `backend/tests/effect_engine/transitions/test_drain_pure.py` | `cb2c80af92d6dee3` | `8eb615c83486c0f8` |
| `backend/tests/effect_engine/transitions/test_drain_dispatcher.py` | `ad4ca1e81331dc6f` | `36fd6c7bd2127d20` |
| `backend/tests/effect_engine/transitions/test_drain_mocked_mongo.py` | `1afb86bfd344cd10` | `4cc8d2bde3b1022a` |

Diff correzione: 10 file · **+185 / −31**. Boundary esteso SOLO ai componenti autorizzati.
Non toccati: provisioning Mongo · allowlist DB · API pubbliche · OpenAPI · frontend ·
Registry · reward · item effect · `.env` · shared environment. `SCOPE_EXPANSION_REQUIRED`
= non attivato.

## A5 · Test aggiunti & revalidation Phase A (integralmente verde)

Nuovi test: `d27` (zero dipendenza TrustedDrainReceipt nel nuovo runtime Drain) ·
`d28` (fold-rejection payload embedded nella receipt del triggering event).
Aggiornati: `p13` · `d01` · `mm01` (asserzione payload nella processed-event receipt +
DrainDoc senza copia autoritativa + receipt legacy `result_payload=None`).

```text
failed = 0 · unexpected skipped = 0 · design deviations = 0 · fail-stops = 0
second receipt slot = 0
state_version increments per completion batch = 1
processed-event receipt contains completion payload = PASS (d01 · mm01 · d28 · p13)
TrustedDrainReceipt dependency in new Drain runtime = 0 (d27)

Suite Drain                  = 65/65 PASS (63 + 2 nuovi)
effect_engine non-Mongo      = 365/365 PASS (baseline legacy invariata)
mocked-Mongo Drain           = 5/5 PASS (payload roundtrip reale su adapter)
real-Mongo heritage seriale  = 96/96 PASS (57 state_store + 39 transitions ·
                               test_perf_mongo_p95 load-sensitive solo sotto xdist,
                               PASS ripetuto in seriale — pre-esistente)
sealed integrity             = 6 PASS · sealed artifacts 36/36 byte-identical ✓
lore_meta.py SHA             = a18f708b…965b8f ✓ · OpenAPI paths = 275 ✓
result-code coverage         = 21/21 ✓ · legacy response/reward invariance ✓
benchmark FakeStore p95 (rerun) = START 0.103ms · COMPLETE+Fragment 0.134ms ·
                               CANCEL 0.111ms · dedup retry 0.411ms ·
                               flags-OFF 0.042ms — tutti entro soglia
```

## A6 · Incidente piattaforma & working-tree attribution (conferma finale)

- **42 file** riscritti dalla env-substitution del fork pod (URL/JOB_ID/UUID storici →
  `drain-dispatch`): artefatti piattaforma, non gate. **2 file sealed ripristinati
  byte-identical da `origin/main`** → sealed integrity 6/6 · **36/36 byte-identical
  CONFERMATO** post-correzione.
- **Auto-commit piattaforma** (meccanismo `emergent-agent-e1`, NESSUNA azione git
  dell'executor): `5a07ab4` (Phase A iniziale + file env-substitution piattaforma +
  report) e `46a91e7` (artefatti build/deploy piattaforma: `frontend/build/*`,
  `.emergent/emergent.yml`). Base gate: `be9f62f`. Il remote `origin` risulta rimosso
  dalla configurazione locale dalla piattaforma: push/merge/PR **non eseguiti
  dall'executor** (gestione remota via piattaforma).
- Working tree corrente: SOLO i 10 file della correzione B2B2Q07 + questi 2 report
  aggiornati + `frontend/yarn.lock` untracked (artefatto ripristino ambiente dev,
  non gate).

**Esito post-correzione**: `RT2-B-2B-2-1 = IMPLEMENTED / PM-CLOSURE-PENDING / V1-REQUIRED`
— V1 real-Mongo AUTORIZZATA (nessun nuovo verdict richiesto) capacità permettendo.
Nessun closure report creato.

---

# ADDENDUM 2 · V1 REAL-MONGO DRAIN VERIFICATION (RT2-B-2B-2-1-V1 · subordinato)

**Autorizzazione**: PM §6 (post-correzione B2B2Q07 · revalidation integralmente verde ·
capacità sessione sufficiente). **Nessun nuovo verdict richiesto.**
**Ambiente**: Mongo reale localhost · fixture `provisioned_unique_db`
(`orbus_r16_rt2b_it_<unique_run_id>` · teardown drop) · nessuna scrittura fuori allowlist.

## V1.1 · File

`backend/tests/effect_engine/transitions/integration_real_mongo/test_drain_real_mongo.py`
(9 test · nuovo · SHA sotto). Nessun file production modificato dalla V1.

## V1.2 · Matrice V1 (9/9 PASS · 3 run consecutivi stabili)

| # | Verifica | Esito |
|---|---|---|
| v01 | Payload 15-campi **REALMENTE persistito nella processed-event receipt** (lettura RAW BSON) · 1 sola ordinary receipt · DrainDoc senza copia autoritativa (`completion_payload=None` · `completion_event_id` linkage) · atomic batch (fragment+status+segment+receipt+version nello stesso doc) · `state_version` +1 exactly once · rehydration/coercion | PASS |
| v02 | Replay START → prior execution ID · duplicate completion (dedup + `DRAIN_ALREADY_COMPLETED`) · fragment = 1 | PASS |
| v03 | Concurrency winner-only: 6 worker concorrenti stessa execution → **1 solo `DRAIN_COMPLETED`** · fragment = 1 · 1 sola receipt con payload | PASS |
| v04 | Lifecycle aggregation: 3 Drain STARTED → PHASE_END → 1 reserved receipt · tutti CANCELLED `PHASE_ENDED` · later completion `PHASE_INACTIVE` | PASS |
| v05 | Receipt saturation reale (504 ordinary) → `RECEIPT_CAP_REACHED` fail-closed · 0 mutation | PASS |
| v06 | BSON size worst-case al cap (504 receipt · 1 payload ogni 2) | PASS (vedi finding) |
| v07 | Performance reale p95 (40 cicli): START **3.458 ms** · COMPLETE+Fragment **6.001 ms** · CANCEL **3.127 ms** — tutti ≤ 35 ms | PASS |
| v08 | Allowlist rejection (`orbus_r16` → `DB_NOT_ALLOWLISTED`) · non-test-user fail-closed · 0 writes (doc invariato `state_version=1`) | PASS |
| v09 | Zero dipendenza `TrustedDrainReceipt` su store reale: fixture forgiata allegata → ignorata · payload autoritativo con execution ID reale | PASS |

Cleanup: **zero database residui** (`rt2b_it_*` = [] post-run).
Suite complessiva post-V1: **365/365 non-Mongo · 105/105 real-Mongo seriale
(96 heritage + 9 V1) · sealed 6/6 · OpenAPI 275 · lore_meta invariante.**

## V1.3 · FINDING BSON (da sottoporre al PM · non bloccante · invariante hard rispettata)

Misura reale worst-case (504 receipt, 1 completion payload ogni 2 — mix massimo
realistico dato che ogni completion richiede il proprio START ordinario):

```text
measured            = 261.545 B
hard budget         = 262.144 B (STATE_DOC_MAX_BYTES · 256 KiB)  → RISPETTATO (margine 599 B)
stima P0 §42        = 215.040 B (210 KiB)                        → SUPERATA
```

L'invariante hard è rispettata ma il margine al saturamento assoluto è minimo.
Raccomandazione per il PM (decisione fuori scope executor): aggiornare la stima P0
e/o valutare in un gate futuro una compaction del payload (es. ID abbreviati nel
payload receipt) prima di qualunque aumento di capacità receipt.

## V1.4 · Esito

```text
RT2-B-2B-2-1     = IMPLEMENTED / PM-CLOSURE-PENDING (V1 PASS · finding BSON notificato)
RT2-B-2B-2-1-V1  = VERIFIED (subordinato · nessuna closure autonoma · nessun baseline increment)
baseline chain    = 16/16 INVARIATA · formal closure attende dispatch PM
```

---

# ADDENDUM 3 · V1S · FULL-CAP BSON CAPACITY HARDENING (PM adjudication)

**Stima P0 210 KiB**: `P0_SIZE_ESTIMATE_SUPERSEDED_BY_MEASURED_DATA` (P0 non modificato · varianza registrata qui).

## V1S.1 · Compaction applicata (solo rappresentazione interna · semantica invariata)
1. **Alias BSON brevi** per `result_payload` persistito (mongo_adapter · layer interno non pubblico); rehydration rimappa ai 15 nomi canonici.
2. **Omissione deterministica** dei 5 campi payload duplicati 1:1 dai campi base della STESSA receipt (`completion_event_id`·`source_adventurer_id`·`assigned_event_sequence`·`state_version_after`·`processed_at`): ricostruiti in rehydration per copia esatta dallo stesso documento (deterministica · nessun campo canonico rimosso al layer applicativo · verificata da v01/v09 su RAW BSON).
3. **Lifecycle bounded payload** (§4 PM): `cancelled_count` reale · `sample_execution_ids ≤ 8` · `execution_ids_truncated` · reason — persistito nella reserved receipt (test v04 + d08); `LIFECYCLE_CANCELLED_IDS_BOUND 32→8`.

File modificati V1S: `mongo_adapter.py` · `transitions/drain.py` · `transitions/dispatcher.py` · `test_drain_real_mongo.py` (v06 full-cap riscritto · v01/v04/v09 aggiornati).

## V1S.2 · Misura full-cap (512 = 504 max-mix legale 252 START+252 COMPLETE + 8 reserved max · RAW BSON su Mongo reale · id a lunghezza massima · stato terminale + tombstones + segment data)
```text
pre-compaction  = 298.576 B
post-compaction = 264.052 B   (−34.524 B)
hard limit      = 262.144 B   → SUPERATO di 1.908 B
closure target  = 245.760 B   → SUPERATO di 18.292 B
misura precedente (504 senza reserved · id corti) = 261.545 B
```

## V1S.3 · FAIL-STOP dichiarato
```text
STATE_DOCUMENT_SIZE_BUDGET_EXCEEDED (al full-cap sintetico max-length)
SIZE_REMEDIATION_REQUIRES_DESIGN_CHANGE → STOP → PM REVIEW
```
**Causa del margine insufficiente**: gli id client-supplied (`event_id`·`source_adventurer_id`·`target_id`) NON hanno length validation contrattuale → il worst-case "legalmente accettato" non è bounded. Le compaction consentite residue sono insufficienti (~2 KB recuperabili). Il rientro nel target richiede uno tra: (a) **length validation contrattuale** sugli id client (design change); (b) **alias dei campi base receipt** (incl. `event_id` usato nei CAS filter/dedup: contract-adjacent). Entrambi richiedono verdict PM.
Il test `test_v06_bson_size_at_full_cap_512` resta nel repo come misuratore, marcato `xfail` documentato (non conteggiato come unexpected failure).

## V1S.4 · Revalidation (tutto il resto integralmente verde)
```text
non-Mongo 365/365 · real-Mongo seriale 103/103 + perf heritage PASS isolato
+ 1 xfail documentato (v06) · sealed 6/6 · OpenAPI 275 · lifecycle bounded PASS ·
winner-only/saturation/dedup/replay PASS · legacy invariance PASS ·
second receipt slot = 0 · state_version per batch = 1 · DB residui = 0
TrustedDrainReceipt = DEPRECATED_COMPATIBILITY_ONLY (test d27/v09 preservati)
```
**Git hygiene (§8)**: inventario commit piattaforma `5a07ab4`/`46a91e7` registrato (Addendum 2/§A6); patch del diff in-scope ricavabile da base `be9f62f`; nessun reset distruttivo eseguito; push/merge/PR non eseguiti. Sanitation della history (branch pulita) eseguibile solo con autorizzazione git separata (vincolo piattaforma: azioni git write gestite da "Save to GitHub").

**Esito**: `RT2-B-2B-2-1-V1S = EXECUTED / SIZE-TARGET-NOT-MET / PM-REVIEW-REQUIRED` · formal closure resta VIETATA · baseline 16/16 invariata.
