# R18.3f · Class Slug Migration Readiness

**Documento**: `r18_3f_class_slug_migration_readiness.md`
**Regime**: DOCUMENTAL ONLY · READ-ONLY DISCOVERY · ITALIANO ONLY
**Gate padre**: R18.6.3 Cacciatore del Vuoto (ACTIVE-DESIGN-READY)
**Precondizione Gate 11**: P2 · IN PROGRESS (draft generato)
**Stato**: `DRAFT_GENERATED` · `review_status = PENDING_PM`
**Governance**: `apply_authorized = false` · `no_migration_applied = true` · `runtime_apply_ready = false`

---

## 1 · Executive summary

R18.3f definisce la **readiness tecnica** del sistema `class_slug` per una futura migrazione dai valori **legacy EN** ai valori **canonical IT** decisi in R18.5 → R18.6 → R18.6.1 → R18.6.3. Il documento è **piano di readiness**, non piano di esecuzione. Nessuna migrazione viene applicata, nessuna scrittura DB viene effettuata, nessun bridge runtime viene attivato. Discovery read-only, categorizzazione, dry-run contract, risk register, precondizioni Gate 11. Il valore live `class_slug` resta legacy EN. Il valore canonical IT resta esclusivamente in ambito documentale (catalog `adventurer_classes` porta già alcuni canonical IT ma non li applica live agli adventurers).

## 2 · Scope

- **In scope**: schema live discovery, mapping legacy→canonical, categorizzazione record, dry-run contract, snapshot/rollback contract, idempotency, audit trail, risk register, PM open questions, precondizioni Gate 11 (P1..P20).
- **Out of scope**: applicazione bridge live, scrittura `class_slug` in DB, migrazione adventurers, migrazione users, migrazione class_halls, migrazione class_specializations, attivazione runtime Hall/Trial, feature flag enable, OpenAPI changes, backend routes changes, frontend UI changes, test file creation, apply Registry v3, Gate 11 execution, Wave 1 kickoff (Monaco/Druido/Alchimista/Bardo/Negromante).

## 3 · Governance

- **PM-locked**: draft in attesa di review PM.
- **No auto-apply**: la generazione di questo documento **non abilita** alcun apply.
- **Explicit gate futuro**: Gate 11 richiederà PM directive esplicita separata dopo verifica delle 20 precondizioni P1..P20.
- **Fonte canonica classi**: `/app/memory/r18_6_1_canonical_27_class_halls_expansion.json` (27 Sale canonical).
- **Sealed integrity**: 36 seal invariati durante la generazione di questo documento. `lore_meta.py` anchor `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`.
- **Zero touch**: backend, frontend, OpenAPI, DB writes, test file, .env, package.json, requirements.txt — nessuna modifica.

## 4 · Schema live discovery (read-only)

Discovery eseguita in modalità read-only via query `count_documents` e `distinct` sul DB dichiarato dall'env (`MONGO_URL` + `DB_NAME`). Nessuna scrittura, nessun update, nessuna aggregation con `$out`/`$merge`.

Collections rilevanti individuate:

| Collection | Ruolo | class_slug field | Docs live |
|---|---|---|---|
| `adventurers` | source of truth avventuriero | `class_slug` (+ `class_name`, `class_role`, `adventurer_class_id`) | 3628 |
| `adventurers_r18_archive` | archivio storico | `class_slug` (mix legacy + canonical + placeholder) | 3415 |
| `adventurer_classes` | catalog classi | `slug`, `canonical_slug`, `alias_target`, `bridge_status`, `bridge_source_round`, `bridge_applied_at`, `is_base_class` | 18 |
| `class_halls` | sale runtime | `class_slug` | 11 |
| `class_halls_r18_archive` | archivio sale | `class_slug` | – |
| `class_specializations` | specializzazioni | (discovery futura) | – |
| `users` | account layer | **NON contiene class_slug** ✅ | 391 |

## 5 · Documento canonico avventuriero

- **Source of truth `class_slug` = collection `adventurers`** (documento avventuriero).
- Ogni avventuriero possiede: `adventurer_class_id` (UUID stringa → riferimento a `adventurer_classes.id`), `class_slug` (stringa lowercase legacy EN attuale), `class_name` (display legacy EN), `class_role` (DPS/Healer/Support/Tank).
- Il "documento canonico avventuriero" è definito come **il record singolo in `adventurers`**, non come cluster user/account/session.

## 6 · Separazione user/account

- `users` (391 docs) **non contiene** field `class_slug`. Verificato: keys osservate = `['_id','created_at','email','id','is_admin','is_demo_owner','is_test_user','password_hash','updated_at','username']`.
- Nessuna migrazione class_slug è pertinente al layer `users`.
- Nessuna migrazione class_slug è pertinente al layer session/trial (fuori dallo scope di R18.3f, dato che trial è NOT_ACTIVE per il pilot).
- **Regola**: `account/user class_slug = NON source of truth` · `trial session class_slug = NON source of truth`.

## 7 · Posizione class_slug

Il campo `class_slug` (stringa lowercase) è posizionato:
- Direttamente sul documento avventuriero in `adventurers.class_slug`.
- In `class_halls.class_slug` come chiave di collegamento hall→classe.
- Nel catalog `adventurer_classes.slug` come identifier catalog + `canonical_slug` come target IT.
- Referenziato nel codice backend in ~302 punti su 32+ file (adventurers, equipment, training, pvp_continental, contracts, guilds, admin, core, forge, dungeons, market, inventory, onboarding, arfus_forge, audit).

## 8 · Campi classe esistenti

Field observati e loro ruolo (osservazione, non modifica):

| Field | Collection | Tipo osservato | Ruolo |
|---|---|---|---|
| `class_slug` | adventurers, class_halls, adventurer_classes.slug | string lowercase / null | identifier logico classe |
| `class_name` | adventurers, adventurer_classes | string (display legacy EN) | UI display |
| `class_role` | adventurers | string (DPS/Healer/Support/Tank) | role tag |
| `adventurer_class_id` | adventurers | UUID string | riferimento catalog |
| `canonical_slug` | adventurer_classes | string | target IT |
| `alias_target` | adventurer_classes | string | alias verso canonical |
| `bridge_status` | adventurer_classes | string | stato bridge nel catalog |
| `bridge_source_round` | adventurer_classes | string | round provenienza bridge |
| `bridge_applied_at` | adventurer_classes | datetime | timestamp bridge |
| `is_base_class` | adventurer_classes | bool | flag base class |
| `parent_class_slug` | adventurers (services) | string | possibile parent (specialization) |
| `class_slug_resolution_status` | catalog / seed metadata | string | stato risoluzione (es. `deferred_to_C5_R18_3f`) |

**Nessun nuovo field è proposto in questa fase.** Verifica esistenza equivalenti prima di ipotizzare estensione schema.

## 9 · Tipi dati osservati

- `class_slug`: `string` lowercase o `null` (268 null / 3628 in `adventurers`).
- `class_name`: `string` (display).
- `class_role`: `string` enum ristretto (4 valori).
- `adventurer_class_id`: `string` UUID4.
- Nessun `class_slug` osservato come integer, array, ObjectId, oggetto annidato.
- Timezone dei `bridge_applied_at`/`updated_at`: UTC (assunzione da convenzione backend, non verificata via lettura documenti).

## 10 · Valori legacy

Valori **legacy EN** osservati live in `adventurers.class_slug` (11 distinti):
`alchemist`, `bard`, `druid`, `mage`, `monk`, `paladin`, `priest`, `ranger`, `rogue`, `warlock`, `warrior`.

Valori legacy noti in **catalog** `adventurer_classes.slug` non presenti live nei distinct correnti:
`assassin`, `berserker`, `necromancer`.

## 11 · Valori canonici

Valori **canonical IT** osservati:
- **In `adventurer_classes.slug`** (catalog): `cacciatore_del_vuoto`, `cacciatore_di_mostri`, `recruit_unassigned`.
- **In `adventurers_r18_archive.class_slug`** (archivio): `cacciatore_del_vuoto`, `cacciatore_di_mostri`, `recruit_unassigned`.
- **In `adventurers.class_slug` live**: **0** (nessun avventuriero live ha ancora valore canonical IT).

Il piano canonical IT completo (target 13 slug + placeholder + test artifact) è definito in R18.6.1 e nel catalog `adventurer_classes`.

## 12 · Valori null

- `adventurers.class_slug = null`: **268 / 3628** documenti.
- `adventurers.class_slug` missing (field assente): **268 / 3628** (stesso conteggio → il null è field-present-value-null e/o field-absent equivalenti nella query).
- Interpretazione: recluta senza assegnazione classe attiva (classless recruit / recruit_unassigned semantico).
- **Regola**: `null` **NON** viene mappato automaticamente a `recruit_unassigned` in questa fase. Categorizzazione futura richiede PM directive.

## 13 · recruit_unassigned

- Presente nel catalog `adventurer_classes.slug` come slug canonical valid.
- Presente nell'archive `adventurers_r18_archive.class_slug`.
- **Non presente** nei live `adventurers.class_slug` (0 occ).
- Categoria: `technical_placeholder`.
- **NON convertire `null` → `recruit_unassigned` automaticamente**. Serve verdict PM esplicito post-review R18.3f.

## 14 · Test artifacts

- `test-class-5e0064` presente nel catalog `adventurer_classes.slug`.
- **Non presente** nei live `adventurers.class_slug` (0 occ).
- Categoria: `test_artifact`.
- Non deve essere mai propagato in produzione o presentato in UI.

## 15 · Valori sconosciuti

- Nessun valore sconosciuto (fuori dai 3 set: legacy EN, canonical IT catalog, technical_placeholder+test_artifact) osservato live durante la discovery corrente.
- Regola operativa futura: qualsiasi valore osservato non contemplato = verdict `UNKNOWN_VALUE`, forwardato al PM per classificazione.

## 16 · Anomalie

Anomalie rilevate in discovery:
- **A1**: 268 avventurieri live con `class_slug=null` senza contestuale valorizzazione `recruit_unassigned`. Impatto: potenziale ambiguità nel bridging. Severity: MEDIUM.
- **A2**: Discrepanza tra live (100% legacy EN) e archive (mix legacy + canonical). L'archive contiene già canonical IT (`cacciatore_del_vuoto`, `cacciatore_di_mostri`) → indica bridge parziale pregresso nel catalog o import da altra fonte, mai propagato agli adventurers live. Severity: MEDIUM (non blocker).
- **A3**: Catalog `adventurer_classes` contiene 18 slug (14 legacy + 3 canonical IT + 1 test artifact) → mismatch di 7 slug rispetto ai 11 slug distinti live. Severity: LOW (previsto).
- **A4**: `class_halls.class_slug` allineato ai 11 valori live → coerente col legacy EN.
- **A5**: `parent_class_slug` referenziato in `backend/app/adventurers/services.py:169` ma non verificato distinct in questa discovery. Follow-up documentale suggerito. Severity: LOW.

Nessuna anomalia con severity HIGH osservata.

## 17 · Bridge canonical IT ↔ legacy EN

Bridge documentale (design_only · apply_authorized=false · runtime_bridge_status=disabled):

| # | legacy_source (EN) | canonical_target (IT) | category | notes |
|---|---|---|---|---|
| 1 | `warrior` | `guerriero` | canonical_native | classe base |
| 2 | `rogue` | `ladro` | canonical_native | classe base |
| 3 | `mage` | `mago` | canonical_native | classe base |
| 4 | `priest` | `paladino` | canonical_native | rimappato R18.6 (priest→paladino) |
| 5 | `ranger` | `cacciatore_di_mostri` | canonical_native | rinominata R18.6.1 |
| 6 | `warlock` | `cacciatore_del_vuoto` | canonical_native | pilot R18.6.3 |
| 7 | `monk` | `monaco` | canonical_native | Wave 1 successor (HOLD) |
| 8 | `druid` | `druido` | canonical_native | Wave 1 successor (HOLD) |
| 9 | `bard` | `bardo` | canonical_native | Wave 1 successor (HOLD) |
| 10 | `alchemist` | `alchimista` | canonical_native | Wave 1 successor (HOLD) |
| 11 | `necromancer` | `negromante` | canonical_native | Wave 1 successor (HOLD) |
| 12 | `assassin` | `ladro` | mapped_legacy | alias verso `ladro` |
| 13 | `berserker` | `guerriero` | mapped_legacy | alias verso `guerriero` |

**13 mapping totali · design_only · no_migration_applied=true · apply_authorized=false.**

## 18 · Mapping validation

- 11 canonical_native (1:1 con classi base canonical).
- 2 mapped_legacy (assassin→ladro, berserker→guerriero) → alias verso canonical esistenti.
- `paladino` è canonical_target per `priest` (rimappato R18.6, non `paladin`).
- `priest` compare 0 volte live in `adventurers.class_slug` distinct → il campo `paladin` è invece presente. Follow-up: verificare in fase futura se il catalog conserva `priest` come alias verso `paladino` o se il campo live `paladin` è già la forma target.
- Nessun canonical_target coincide con un legacy_source (no self-map).
- Nessun duplicato canonical_target ambiguo (assassin+rogue→ladro e berserker+warrior→guerriero sono alias voluti).

## 19 · Canonical-native handling

- Nessuna azione runtime.
- Se un record live avesse già canonical IT (attualmente 0), verdict = `CANONICAL_NATIVE` · `NO_ACTION` (già target).
- L'archive contiene 2 canonical native (`cacciatore_del_vuoto`, `cacciatore_di_mostri`) → non propagati, restano solo in archive.

## 20 · Mapped-legacy handling

- Verdict = `MAPPED_LEGACY` · azione futura proposta (**non applicata ora**) = riscrittura `class_slug` legacy → canonical target IT + snapshot pre/post + audit_log entry.
- Bridging applica solo su avventurieri live con `class_slug` in {`warrior`,`rogue`,`mage`,`priest`,`ranger`,`warlock`,`monk`,`druid`,`bard`,`alchemist`,`necromancer`,`assassin`,`berserker`}.
- `paladin` osservato live ma non nel bridge legacy_source (già target IT? follow-up documentale).

## 21 · Technical-placeholder handling

- Verdict = `TECHNICAL_PLACEHOLDER`.
- `recruit_unassigned` = placeholder canonico ammesso.
- `null` / missing = **CLASSLESS_RECRUIT** (categoria distinta).
- Nessuna auto-derivazione da null a placeholder senza PM directive.

## 22 · Test-artifact handling

- Verdict = `TEST_ARTIFACT`.
- `test-class-5e0064` = artifact di test presente nel catalog.
- Regola: mai propagare in ambiente production. Escludere da qualsiasi bridge apply. Se osservato live in adventurers = ALERT + quarantine (non presente attualmente).

## 23 · Unknown-value handling

- Verdict = `UNKNOWN_VALUE`.
- Qualsiasi valore fuori dai set noti (canonical_native ∪ mapped_legacy ∪ technical_placeholder ∪ test_artifact) = forwardato al PM per classificazione manuale.
- Nessuna auto-classificazione. Nessuna cancellazione. Nessuna sostituzione automatica.

## 24 · No-auto-derive policy

- **NO** auto-derivazione da `class_name` a `class_slug`.
- **NO** auto-derivazione da `adventurer_class_id` a `class_slug` (anche se possibile via join catalog).
- **NO** conversione automatica di `null` in `recruit_unassigned`.
- **NO** fallback lookup runtime su null → catalog default.
- Ogni conversione richiede: (1) PM directive esplicita · (2) dry-run · (3) snapshot · (4) audit trail · (5) rollback plan.

## 25 · Migration candidate model

Struttura concettuale (design only · non implementata) di un record di migrazione candidato:

```
MigrationCandidate {
  adventurer_id: string (UUID)
  current_class_slug: string | null
  current_class_name: string | null
  current_adventurer_class_id: string (UUID) | null
  proposed_verdict: enum { CANONICAL_NATIVE, MAPPED_LEGACY, TECHNICAL_PLACEHOLDER,
                           TEST_ARTIFACT, CLASSLESS_RECRUIT, UNKNOWN_VALUE,
                           CONFLICT, NO_ACTION }
  proposed_target_class_slug: string | null
  bridge_reason: string (verbatim mapping row reference)
  applied: false (sempre false in questa fase)
  dry_run: true
  snapshot_pre_hash: string | null
  timestamp_generated: datetime UTC
  pm_approval_required: true
}
```

- Modello concettuale · nessuna collection Mongo creata · nessun index creato.

## 26 · Dry-run architecture

Contratto dry-run obbligatorio:

1. **Input**: dataset target (es. `adventurers` live).
2. **Read-only**: solo `count_documents` + `distinct` + `find({limit:N})` (no update/insert/delete).
3. **Candidate classification**: per ogni record → verdict + proposed_target.
4. **Preview report**: aggregato per verdict, aggregato per bridge row.
5. **Conflict report**: elenco record con verdict `CONFLICT` o `UNKNOWN_VALUE`.
6. **Unknown report**: elenco record con verdict `UNKNOWN_VALUE`.
7. **No mutation**: nessuna scrittura, nessun `$out`, nessun `$merge`, nessuna aggregation con side effects.
8. **Snapshot prerequisite**: snapshot pre-apply obbligatorio (dettaglio §28).
9. **Explicit apply gate futuro**: apply richiede PM directive dedicata + Gate 11 authorized.

## 27 · Idempotency

- Dry-run **idempotent per definizione** (no writes).
- Apply futuro (fuori scope R18.3f) dovrà accettare `Idempotency-Key` per garantire replay-safe.
- Ogni record di migrazione futuro dovrà avere `dry_run=true|false` esplicito.
- **Idempotency-Key contract futuro** (design_only): header o body param, TTL suggerito 24h, chiave = hash(target_batch_id + timestamp_intent).
- Ripetizioni consecutive con stessa Idempotency-Key = single-effect.

## 28 · Snapshot requirements

Snapshot pre-apply obbligatorio (design only · non implementato):

- Snapshot completo collection `adventurers` (o filtrato al subset target) → collection `adventurers_r18_3f_snapshot_pre_apply` (design_only, non creata).
- Metadati snapshot: `snapshot_id` (UUID4), `snapshot_hash` (SHA256 dell'export), `record_count`, `generated_at` (UTC), `pm_approval_ref`.
- Snapshot obbligatorio anche prima di qualsiasi dry-run che touche >0 record (dry-run puro read-only non richiede snapshot).
- Retention snapshot ≥ 30 giorni post-apply.

## 29 · Rollback strategy

- **Piano**: se apply fallisce o produce risultati inattesi → restore da snapshot pre-apply.
- **Trigger rollback**: (a) verdict PM esplicito, (b) errore >X% record, (c) violazione integrity check post-apply.
- **Rollback contract**: overwrite di `adventurers` (o subset) con documenti snapshot originali + audit log entry `rollback_applied`.
- **Rollback idempotent**: rollback replicato deve produrre lo stesso stato finale.
- **Snapshot post-rollback**: obbligatorio anche dopo rollback per audit trail.
- **NON implementato in R18.3f**. Design only.

## 30 · Audit trail

Ogni operazione futura (dry-run + apply + rollback) dovrà emettere audit event:

```
AuditEvent {
  event_id: UUID4
  event_type: enum { r18_3f.dry_run.started, r18_3f.dry_run.completed,
                     r18_3f.apply.started, r18_3f.apply.record_migrated,
                     r18_3f.apply.completed, r18_3f.rollback.started,
                     r18_3f.rollback.completed }
  actor: string (user_id admin)
  target_adventurer_id: string | null
  before_state: object | null
  after_state: object | null
  verdict: enum (see §25)
  timestamp: datetime UTC
  pm_approval_ref: string
  snapshot_id: string
}
```

Audit trail scritto su collection `audit_log` esistente (verificato: già presente). Nessuna nuova collection audit richiesta.

## 31 · Conflict handling

Verdict `CONFLICT` emesso quando:
- Record ha `class_slug` legacy EN ma `class_name` incoerente col bridge (es. `class_slug=warlock` + `class_name=Warrior`).
- Record ha `class_slug` = valore canonical IT ma `adventurer_class_id` punta a catalog entry legacy EN (o viceversa).
- Record ha `class_slug` ≠ null ma missing `adventurer_class_id`.
- Multiple sorgenti candidate (es. `parent_class_slug` presente e diverge da `class_slug`).

Handling: **NO auto-fix**. Report al PM. Attesa PM directive record-by-record o batch.

## 32 · Cacciatore del Vuoto

- **Pilot R18.6.3** = ACTIVE-DESIGN-READY.
- Canonical target: `cacciatore_del_vuoto`.
- Legacy source: `warlock`.
- Live adventurers con `class_slug=warlock`: subset dei 3628 (conteggio esatto in preview futura).
- **Nessun avventuriero live è attualmente `cacciatore_del_vuoto`**. Solo l'archive contiene tale slug.
- **Nessuna migrazione applicata** in questa fase. Il bridge è documentato e disponibile per apply futuro.

## 33 · Bridge warlock

Riga di bridge dedicata:

```
bridge_id: R18_3F_BRIDGE_06
legacy_source: warlock
canonical_target: cacciatore_del_vuoto
category: canonical_native
bridge_status: mapped_design_only
migration_status: not_applied
runtime_bridge_status: disabled
apply_authorized: false
pm_approval_ref: FR-Q5 LOCK (R18.6.3-G10)
```

Il valore `warlock` in `class_name` legacy resta invariato in live. La display IT `Cacciatore del Vuoto` è definita nel catalog `adventurer_classes` come `display_name_it`, ma non applicata come `class_slug`.

## 34 · Compatibilità Class Halls

- `class_halls` (11 live) usa `class_slug` come chiave.
- Migration `class_slug` → richiede aggiornamento coerente delle referenze `class_halls.class_slug`.
- **NON in scope R18.3f**. Design only: propagazione a class_halls sarà gate dedicato (candidato Gate 11 sub-step) o parte di Apply Phase.
- `class_specializations` idem (referenza probabile via class_slug o parent_class_slug — follow-up discovery necessaria).

## 35 · Compatibilità Rite of Rebirth

- `Rite of Rebirth` (R18.6.RB1) = HOLD.
- Se attivato in futuro, dovrà consumare `class_slug` canonical IT dopo apply migration.
- Fino ad allora resta compatibile col legacy EN (nessun cambio richiesto).
- Nessuna dipendenza bloccante di R18.6.RB1 su R18.3f apply (Rite of Rebirth è HOLD indipendentemente).

## 36 · Storico classi

- `career_history` collection presente in DB (verificata via `list_collection_names`).
- Storico potrebbe contenere referenze `class_slug` legacy. Follow-up discovery: verificare campi.
- Migration futura deve: (a) preservare storico legacy come immutable audit, (b) valutare se aggiornare storico corrente o accodare eventi di conversione.
- **Regola preservation**: storico legacy IT-fied opzionale, decisione PM.
- **Archive `adventurers_r18_archive`** = **NON toccare** (immutabile per definizione).

## 37 · API impact

- API con esposizione `class_slug` (backend routes):
  - `/adventurers` (list, detail) → serializza `class_slug` corrente
  - `/pvp_continental/*` → include `class_slug` in payload team
  - `/training/*` → resolve `class_slug` per eligibility
  - `/equipment/*` → usa `class_slug` per compatibility check
  - `/inventory/*` → filter/serialize su class binding
  - `/forge/*` → class-bound craft
  - `/guilds/*` → potenziale leak `previous_class_slug` (già filtrato per Zero-leak)
- **Impatto migration** (design only): API response cambierebbe da legacy EN a canonical IT. Breaking change dal punto di vista consumer frontend.
- **Compatibility strategy** (design only, non implementata):
  - Fase 1 (attuale): API espone legacy EN.
  - Fase 2 (post-apply): API espone canonical IT + campo compat `class_slug_legacy` opzionale per N settimane.
  - Fase 3 (post-N-settimane): rimozione campo compat.
- **NON applicato ora.** OpenAPI diff = 0.

## 38 · OpenAPI impact

- OpenAPI runtime = **INVARIATO** in R18.3f.
- Nessuna modifica a `/api/openapi.json`.
- Nessun nuovo endpoint proposto per apply migration (l'apply endpoint sarà definito in gate futuro).
- Documento OpenAPI dovrà essere versionato prima di qualsiasi apply (baseline snapshot obbligatorio).

## 39 · DB impact

- DB writes in R18.3f = **0**.
- Collections touched in R18.3f = **0** (solo read-only distinct/count).
- Indici modificati = **0**.
- Aggregazioni con side effects = **0**.
- Nuove collections create = **0**.
- Impatto futuro apply (design only): update batch su `adventurers.class_slug` + update `class_halls.class_slug` + update coerente su collections dipendenti + write audit_log + write snapshot collection.

## 40 · Prerequisites

Elenco precondizioni Gate 11 (P1..P20 · **20 precondizioni obbligatorie**):

| ID | Precondizione | Status attuale |
|---|---|---|
| **P1** | Pilot R18.6.3 Cacciatore del Vuoto = ACTIVE-DESIGN-READY | ✅ CLOSED |
| **P2** | R18.3f Class Slug Migration Readiness draft generato | 🔄 IN PROGRESS (this document) |
| **P3** | R18.3f review PM completata + verdict CLOSED | 🔒 NOT STARTED |
| **P4** | Snapshot pre-apply architecture approvata | 🔒 NOT STARTED |
| **P5** | Idempotency contract approvato | 🔒 NOT STARTED |
| **P6** | Rollback plan approvato | 🔒 NOT STARTED |
| **P7** | Audit trail schema approvato | 🔒 NOT STARTED |
| **P8** | API compatibility strategy approvata | 🔒 NOT STARTED |
| **P9** | Frontend consumer impact assessment completato | 🔒 NOT STARTED |
| **P10** | R18.6.RV3-EV Eligibility Validation Gate completato | 🔒 HOLD |
| **P11** | Feature flag `CLASS_SLUG_MIGRATION_ENABLED` (design_only) definito | 🔒 NOT STARTED |
| **P12** | Conflict handling verdict tree PM-approved | 🔒 NOT STARTED |
| **P13** | Unknown value escalation policy PM-approved | 🔒 NOT STARTED |
| **P14** | Test data isolation policy (test-class-5e0064) confermata | 🔒 NOT STARTED |
| **P15** | Class Halls sync strategy approvata | 🔒 NOT STARTED |
| **P16** | Class Specializations sync strategy approvata | 🔒 NOT STARTED |
| **P17** | career_history preservation strategy approvata | 🔒 NOT STARTED |
| **P18** | archive immutability confermata (adventurers_r18_archive read-only) | 🔒 NOT STARTED |
| **P19** | Sealed integrity 36/36 verificata pre-Gate 11 | 🔒 NOT STARTED (verifica al momento del gate) |
| **P20** | PM directive esplicita di autorizzazione Gate 11 | 🔒 NOT STARTED |

Nessuna precondizione è considerata implicita. Gate 11 = NOT AUTHORIZED fino al completamento P1..P20.

## 41 · Risk register

| ID | Rischio | Severity | Mitigation |
|---|---|---|---|
| **R1** | Migration parziale (subset record migrato, altri no) → stato inconsistente | HIGH | Batch atomici · snapshot pre-batch · rollback batch-level · idempotency |
| **R2** | Auto-derive da `class_name` senza approvazione PM → drift semantico | HIGH | No-auto-derive policy §24 · verdict `NO_ACTION` per default |
| **R3** | Propagazione test artifact `test-class-5e0064` in produzione | MEDIUM | Escludere in preview · quarantine record · alert |
| **R4** | Conflict record (class_slug ≠ class_name) → mismatch UI | MEDIUM | Verdict `CONFLICT` · PM review record-by-record |
| **R5** | 268 record con `class_slug=null` → ambiguità classless recruit vs bug | MEDIUM | Verdict `CLASSLESS_RECRUIT` · PM decision su placeholder vs mantenimento null |
| **R6** | Breaking change API consumer (frontend, integrazioni) | HIGH | Fase compat con doppio field (legacy + canonical) per N settimane |
| **R7** | class_halls out-of-sync post-migration | HIGH | Sync coerente contestuale · verifica hall→adventurer allineamento |
| **R8** | career_history storico frammentato tra legacy e canonical | LOW | Immutable audit · nessun rewrite storico |
| **R9** | Sealed integrity infrangibile durante gate futuro apply | CRITICAL | Verifica seal pre + post ogni operazione · abort su drift |
| **R10** | Rollback fallito → stato irrecuperabile | HIGH | Snapshot multipli · rollback testato in staging · dry-run rollback pre-apply |
| **R11** | Idempotency key collision → apply doppio | MEDIUM | UUID4 key · TTL 24h · state check pre-apply |
| **R12** | Impatto performance batch update su 3628 record | LOW | Batch size limitato (es. 500/batch) · rate limit interno |

Nessun rischio residuo critico non mitigabile identificato.

## 42 · PM open questions

Elenco domande PM aperte (R3f-Q1..R3f-Q10):

- **R3f-Q1** — 268 record con `class_slug=null`: verdict target = `CLASSLESS_RECRUIT` (mantenere null) o migrazione automatica a `recruit_unassigned`? *Recommendation*: mantenere `null` finché non c'è UX confirmato per placeholder visibile.
- **R3f-Q2** — `paladin` osservato live ma non nel bridge legacy_source: è già canonical target (paladino/paladin) o mapping supplementare richiesto? *Recommendation*: verificare catalog + eventuale row bridge `paladin → paladino` se richiesto.
- **R3f-Q3** — Archive contiene 2 canonical IT già bridged: propagazione retroattiva agli adventurer live o restare archive-only? *Recommendation*: archive-only per preservare consistenza storica.
- **R3f-Q4** — Timing apply migration: pre-Wave 1 kickoff (una-shot) o per-Wave (batch per classe)? *Recommendation*: batch per Wave per ridurre blast radius.
- **R3f-Q5** — API compatibility phase: N settimane con doppio field. Quanto è N? *Recommendation*: N=4 settimane minimum + verifica consumer confirm.
- **R3f-Q6** — Feature flag `CLASS_SLUG_MIGRATION_ENABLED`: gate globale o per-classe? *Recommendation*: per-classe per allineamento con Wave rollout.
- **R3f-Q7** — Frontend impact: refactor client bridge (canonical IT) preventivo o post-apply? *Recommendation*: preventivo (frontend accetta entrambi) per hot-swap safe.
- **R3f-Q8** — Test artifact `test-class-5e0064`: rimuovere dal catalog o preservare come test-only? *Recommendation*: preservare + guard runtime che ne blocca la selezione live.
- **R3f-Q9** — Rollback timing: automatico se >X% errori o solo manuale post-PM review? *Recommendation*: threshold automatico + manual override obbligatorio (double-gate).
- **R3f-Q10** — Sealing R18.3f documento (aggiunta al 36-seal system): ora o dopo apply completo? *Recommendation*: dopo apply completo per evitare mutable content pre-apply.

## 43 · GO/HOLD recommendation

| Componente | Verdict |
|---|---|
| R18.3f draft documentale | ✅ **DRAFT_GENERATED** (this document) |
| R18.3f PM review | 🕐 **PENDING** |
| R18.3f apply migration | 🔒 **HOLD** |
| Gate 11 (P1..P20) | 🔒 **NOT AUTHORIZED** |
| RV3-EV Eligibility Validation | 🔒 **HOLD** |
| Wave 1 kickoff (Monaco/Druido/Alchimista/Bardo/Negromante) | 🔒 **HOLD** |
| Runtime bridge activation | 🔒 **DISABLED** |
| OpenAPI/backend/frontend changes | 🔒 **NOT AUTHORIZED** |

**Recommendation al PM**: procedere con review R18.3f draft. Nessun apply, nessuna migration, nessun Gate 11 kickoff prima di PM directive esplicita post-review.

---

## 🛑 STOP FINALE · R18.3f DRAFT GENERATO · PENDING_PM

- `apply_authorized = false`
- `no_migration_applied = true`
- `runtime_bridge_status = disabled`
- `class_slug write` = 0 occorrenze (nessuna scrittura DB effettuata)
- `Idempotency-Key` = design only (contract §27)
- `dry_run` = design only (contract §26)
- 20 precondizioni Gate 11 (P1..P20) documentate §40
- 13 bridge mapping (11 canonical_native + 2 mapped_legacy) documentati §17
- 4 categorie speciali (canonical_native, mapped_legacy, technical_placeholder, test_artifact) documentate §19-22
- 8 verdict admessi (CANONICAL_NATIVE, MAPPED_LEGACY, TECHNICAL_PLACEHOLDER, TEST_ARTIFACT, CLASSLESS_RECRUIT, UNKNOWN_VALUE, CONFLICT, NO_ACTION) documentati §25
- Sealed integrity 36/36 verificata pre + post generazione documento
- `lore_meta.py` anchor invariato
- backend/frontend/OpenAPI diff = 0
- Certificate + Pilot Manifest R18.6.3 IMMUTATI

**Attendo PM verdict su R18.3f prima di ogni ulteriore azione.**
