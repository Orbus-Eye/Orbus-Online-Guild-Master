# R18.6.RV3-IS2-B-P2B-RT2-B-P0 · Final Closure Report

**Regime**: `DOCUMENTAL_ONLY · READ-ONLY DISCOVERY · NO_APPLY · Italian_only · SHA Policy §31 · STRICT STOP`
**Gate ID**: `R18.6.RV3-IS2-B-P2B-RT2-B-P0 · TRANSIENT CLASS STATE STORE & MULTI-WORKER COORDINATION ARCHITECTURE`
**Stato**: `PM-RATIFIED · CLOSED · PM-LOCKED`
**Data closure**: 2026-02 (UTC)
**Ancoraggio invariante**: `lore_meta.py` SHA256 = `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`

---

## Requisito 1 · PM verdict

Il PM ha ratificato le 12 B0Q verbatim e ha ordinato la chiusura formale di `RT2-B-P0`. Architettura definitiva: `Mongo dedicated collection (expedition_runtime_states)` + `distributed lease + fencing token (Model A)` + `ATOMIC_PER_EXPEDITION`. `formal closure = GO`. `RT2-B-1A = CONDITIONAL GO` (Phase 2 dispatch pending).

## Requisito 2 · RT2-B-P0 CLOSED

`R18.6.RV3-IS2-B-P2B-RT2-B-P0` → **CLOSED · PM-LOCKED · IMMUTABLE**. Post-closure: nessuna scrittura sui 2 P0 artefatti patched, nè sui 3 closure artifacts.

## Requisito 3 · 40/40 sections

Il P0 patched conserva `40/40` sezioni nel MD e nel JSON companion (chiavi `section_01_...` → `section_40_...`), stesso ordine e stessi nomi rispetto alla versione pre-patch. Verificato programmaticamente.

## Requisito 4 · 12/12 B0Q resolved

Tutte le 12 B0Q sono `RESOLVED` con verdict verbatim del PM (dettaglio in `section_36_pm_open_questions` e top-level `pm_verdict_applied_2026_02`). `auto_ratified_by_agent = false`.

## Requisito 5 · Mongo dedicated collection selected

`store technology = OPTION 2 · Mongo dedicated runtime-state collection` · canonical name **`expedition_runtime_states`** (B0Q01).

## Requisito 6 · Distributed lease selected

`writer model = MODEL A · distributed lease per expedition` (B0Q02).

## Requisito 7 · Fencing token mandatory

Ogni mutation include filtro atomico su `fencing_token`. Stale writer resume → `STALE_WRITER_REJECTED`. Ogni nuova acquisizione valida `+1 fencing_token` (B0Q02 + B0Q08).

## Requisito 8 · Atomic-per-expedition consistency

`ATOMIC_PER_EXPEDITION` mandatorio per: Fragment gain/spend · Drain completion · Mark application+cap · event deduplication (4/4).

## Requisito 9 · Expedition-level ownership

`state ownership scope = one runtime-state document per expedition` · `adventurer_class_states keyed by adventurer_id` · ownership separata per Marchi/Drain/Frammenti/resource_segment/focus_bonus_usage (B0Q03). VIETATO: stato globale classe cross-spedizione · consumo stato altro avventuriero · stato persistente sul character document.

## Requisito 10 · CAS/versioning policy

`state_version = monotonic integer (initial=1)` · filtro mutation min = `{expedition_id, state_version, fencing_token}` · outcomes: match → atomic; version_mismatch → `STATE_VERSION_CONFLICT`; fencing_mismatch → `STALE_WRITER_REJECTED`; partial mutation → FORBIDDEN. Max 3 CAS retries (con fresh state read) (B0Q04).

## Requisito 11 · Server-authoritative ordering

`state-changing events = total ordered per expedition` · `event_sequence` assegnato dalla mutation accettata · client non sceglie sequenza · retry stesso `event_id` restituisce risultato precedente senza nuova mutation (B0Q05).

## Requisito 12 · Deduplication policy

Dedup key = `expedition_id + event_id`. Receipt bounded (event_id · event_type · source_adventurer_id · payload_hash · assigned_event_sequence · result_code · state_version_after · processed_at). `same event_id + same payload hash → idempotent prior-result response`. `same event_id + different payload hash → EVENT_ID_PAYLOAD_MISMATCH · REJECT`. Retention = lifetime documento stato. Al limite: fail-closed, no eviction during active expedition (B0Q06).

## Requisito 13 · TTL and cleanup policy

`active state inactivity TTL = 6 hours` · `completed/cancelled retention = 24 hours` · `dedup retention = until state-document expiry` · ogni mutation valida aggiorna `updated_at + expires_at` · orphan → TTL cleanup · manual = exceptional recovery. Baseline · non live authorization (B0Q07).

## Requisito 14 · Restart/failover policy

`lease duration = 30s · renewal = 10s · grace = 5s` · fencing_token increments on new acquisition · worker crash before mutation → no state change · worker crash after atomic mutation → retry dedup by event_id · lease expiry → other worker acquires with higher fencing_token · stale worker resume → mutation rejected · application clock alone insufficient (B0Q08).

## Requisito 15 · NO_DB_MIGRATION baseline invalidated for RT2-B

`NO_DB_MIGRATION_BASELINE_INVALID = TRIGGERED FOR RT2-B`. Chiarimento PM: `gameplay state semantics = transient` · `physical storage = Mongo persistent collection with TTL`. È **DB INFRASTRUCTURE / SCHEMA PROVISIONING CHANGE**, non migrazione dati tradizionale (B0Q09).

## Requisito 16 · No data backfill required

`DATA_BACKFILL_REQUIRED = FALSE` · `PERSISTENT_CHARACTER_SCHEMA_CHANGE = FALSE`. `NEW_TRANSIENT_COLLECTION_REQUIRED = TRUE` · `NEW_TTL_INDEX_REQUIRED = TRUE` (B0Q09).

## Requisito 17 · First code slice RT2-B-1A

Canonical: `R18.6.RV3-IS2-B-P2B-RT2-B-1A · STATE STORE CONTRACT & NON-WIRED ADAPTER FOUNDATION`. Scope autorizzato: ExpeditionRuntimeStateStore interface · schemas (state/lease/receipt) · fencing validation · CAS result types · fake in-memory store · Mongo adapter con collezione iniettata (NON istanziato dal runtime) · contract-test suite · unit test con Mongo mocked · security tests (B0Q10).

## Requisito 18 · Provisioning split to RT2-B-1B

Creazione collezione `expedition_runtime_states`, TTL index, real DB integration tests, operational approval → **`RT2-B-1B` (separate future gate · NOT AUTHORIZED IN THIS DISPATCH)** (B0Q09 + B0Q10 + B0Q12).

## Requisito 19 · Operational dependency decision

`reuse existing Mongo deployment = APPROVED_IN_PRINCIPLE` · `new external service = NOT_APPROVED` · `Redis = NOT_REQUIRED` · `broker = NOT_REQUIRED` · **operational approval effettiva della new collection = DEFERRED_TO_RT2-B-1B** (B0Q12).

## Requisito 20 · RT2-A remains unwired

`RT2-A runtime wiring = false` · `cdv_transient_state_enabled = false` · `item_effect_engine_enabled = false` · `RT2-A library = default-OFF · foundation ready for future integration`. Con flag disabilitati: `current runtime behavior = unchanged`.

## Requisito 21 · No collection created

`collection creation during Phase 1 = 0`. La creazione fisica di `expedition_runtime_states` è **deferred** a `RT2-B-1B`.

## Requisito 22 · No index created

`index creation during Phase 1 = 0`. TTL index su `expires_at` è **deferred** a `RT2-B-1B`.

## Requisito 23 · No code implemented during P0

`backend code changes = 0` · `frontend code changes = 0` · `test file changes = 0` · `RT2-A files unchanged` (24/24) · `sealed set unchanged (36)`.

## Requisito 24 · Governance evidence

- `sealed integrity tests = 6 passed`
- `sealed artifacts = 36/36 byte-identical`
- `lore_meta.py SHA = a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` · invariant
- `PRD pre-append reference SHA = 240801dccfe046eda8673178a76ee78eab59d03cfee2f549a43e87af2fe1da6b`
- baseline chain **8/8 byte-identical**: `IS2-A · IS2-B-P1 · IS2-B-P1-N1 · IS2-B-P2A · IS2-B-P2B-1 · IS2-B-P2B-RT1 · IS2-B-P2B-RT2-P0 · IS2-B-P2B-RT2-A`
- `existing backend files unchanged` · `frontend unchanged` · `OpenAPI unchanged`
- `DB writes = 0` · `collection creation = 0` · `index creation = 0`
- `migrations = 0` · `feature flag activation = 0` · `runtime wiring = 0`
- `Registry changes = 0` · `item generation = 0`

## Requisito 25 · STOP esplicito

Closure formale `RT2-B-P0` completa. `RT2-B-1A = CONDITIONAL_GO_AWAITING_PHASE_2_DISPATCH`. Nessuna ulteriore scrittura autorizzata in Phase 1. In attesa di dispatch Phase 2 (RT2-B-1A code) da orchestrator.

---

**Fine documento** · Italian_only · DOCUMENTAL_ONLY · RT2-B-P0 PM-LOCKED · SHA Policy §31 · STRICT STOP
