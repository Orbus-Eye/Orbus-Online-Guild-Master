# R18.3f · Final Closure Report

**Documento**: `r18_3f_final_closure_report.md`
**Verdict PM**: **CLOSED · PM APPROVED · PM-LOCKED · NOT APPLIED · NOT SEALED**
**Regime**: DOCUMENTAL ONLY · READ-ONLY DISCOVERY · ITALIANO ONLY
**Sealed integrity**: 36/36 attesa · `lore_meta.py` = `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`

---

## 1 · Verdict CLOSED

- **R18.3f Class Slug Migration Readiness** = **PM APPROVED · CLOSED · PM-LOCKED**
- Runtime status = `NOT_IMPLEMENTED` · Apply status = `NOT_APPLIED` · Sealing status = `NOT_YET_SEALED`
- Governance: closure valida con acquisizione integrativa del corrective audit R18.3f-R1 · draft originale preservato.

## 2 · Draft originale preservato

I 3 file R18.3f originali (draft + manifest) sono **INVARIATI**:
- `/app/memory/r18_3f_class_slug_migration_readiness.md` — SHA `746ad94f7f186684f08c4d5ab4268ab719a2287b3dfc078b5d3e0a8f53b69668`
- `/app/memory/r18_3f_class_slug_migration_readiness.json` — SHA `d79401ebcbad376149a5ccb819fa8ead06cf180ad6b386022a94efe358ce3389`
- `/app/memory/r18_3f_class_slug_migration_readiness_manifest.json` — SHA `bc603ff8892f84efdafb6bdd1b6ddbe7c4b35b06eb165f2dc2c930c16debe63b`

Il draft originale **non viene riscritto retroattivamente**. Errori/inesattezze storiche restano registrati nell'audit corrective R18.3f-R1 e in questo closure report.

## 3 · R18.3f-R1 acquisito come corrective audit

I 2 file R18.3f-R1 audit sono **INVARIATI e AUTORITATIVI** sui fatti corretti dalla discovery:
- `/app/memory/r18_3f_mapping_null_reconciliation_audit.md` — SHA `cc2dc8e60422a61a2ab67221a632623059b46410a9e4c1a1657b6fa4b1b11e39`
- `/app/memory/r18_3f_mapping_null_reconciliation_audit.json` — SHA `9e15dfbcb2c057bf37ecb8dfda1153260f2f4ce10e10fd2234eec30926ae5cdc`

L'audit R18.3f-R1 **prevale** sui fatti corretti dalla discovery: 14 mapping legacy-source, categorie bridge_status corrette (mapped_canonical / mapped_alias / deprecated_alias / canonical_native), 268 NULL_CONFLICT, anomalie A6-A14, risk register R13-R18.

## 4 · Regola di precedenza documentale

- **R18.3f-R1** = autoritativo per: 14 mapping baseline · categorie R18.3e-ratificate · 268 riclassificazione null cohort · A6-A14 nuove anomalie · R13-R18 nuovi rischi · paladin reconciliation.
- **R18.3f originale** = valido storicamente per: governance (§1-3), scope, source of truth, dry-run architecture, idempotency, snapshot, rollback, audit trail, conflict handling, compatibility Class Halls, compatibility Rite of Rebirth, API impact, OpenAPI impact, DB impact, prerequisites P1-P20, GO/HOLD recommendation.
- **Errore semantico storico**: il draft R18.3f originale §17 categorizzava 11 mapping legacy come `canonical_native`. Errore rettificato in R18.3f-R1 §3 con categorizzazione ufficiale R18.3e (9 mapped_canonical + 3 mapped_alias + 2 deprecated_alias). NON riscritto retroattivamente.
- **Errore quantitativo storico**: il draft R18.3f originale §17 elencava 13 mapping (mancava `paladin → paladino`). Rettificato in R18.3f-R1: 14 mapping baseline confermati.
- **Errore classificazione null**: il draft R18.3f originale §12-13 classificava 268 null come "classless recruit / CLASSLESS_RECRUIT". Rettificato in R18.3f-R1: 100% NULL_CONFLICT (evidenza classe presente via 3 field alternativi).

## 5 · 14 mapping legacy-source finali

Registry canonico bridge di riferimento: `/app/memory/r18_3e_bridge_registry.json`.

**9 mapped_canonical**:
1. `warrior → guerriero` (HIGH · live 331)
2. `rogue → ladro` (HIGH · live 302)
3. `mage → mago` (HIGH · live 281)
4. `monk → monaco` (HIGH · live 327)
5. `paladin → paladino` (HIGH · live 303)
6. `druid → druido` (HIGH · live 311)
7. `alchemist → alchimista` (HIGH · live 299)
8. `bard → bardo` (HIGH · live 324)
9. `necromancer → negromante` (MEDIUM · live 0)

**3 mapped_alias**:
10. `priest → paladino` (MEDIUM · live 278)
11. `ranger → cacciatore_di_mostri` (MEDIUM · live 299)
12. `warlock → cacciatore_del_vuoto` (MEDIUM · live 305)

**2 deprecated_alias** (live=0):
13. `assassin → ladro` (MEDIUM · live 0)
14. `berserker → guerriero` (MEDIUM · live 0)

**Regola semantica LOCK**: uno slug legacy EN con canonical target IT **NON è `canonical_native`**. È `mapped_canonical` (canonical target IT dominante) o `mapped_alias` (alias su target già altrimenti raggiungibile) o `deprecated_alias` (alias con adventurers_live=0 destinato a rimozione futura). `canonical_native` è riservato ai record già valorizzati con lo slug canonico IT nel campo `class_slug`.

## 6 · 18 registry entries totali

- 14 mapping legacy-source (§5)
- 2 canonical_native: `cacciatore_di_mostri`, `cacciatore_del_vuoto`
- 1 technical_placeholder: `recruit_unassigned`
- 1 test_artifact: `test-class-5e0064`

**Totale bridge_entries = 18** (matcha `adventurer_classes` catalog docs=18).

**bridge_status_enum ufficiale R18.3e (7 valori)**: `mapped_canonical`, `mapped_alias`, `deprecated_alias`, `technical_placeholder`, `test_artifact`, `canonical_native`, `ambiguous_pending_pm`.

## 7 · Paladin reconciliation

- **paladin live** = **303** in `adventurers.class_slug`
- **paladin catalog** = presente in `adventurer_classes` con `canonical_slug=paladino`, `bridge_status=mapped_canonical`, `bridge_source_round=R18.3e Phase B`, `is_active=true`
- **paladin bridge registry R18.3e** = presente con `confidence=HIGH`, `adventurers_live=303`
- **canonical target** = `paladino`
- **STOP mismatch** = NO · reconciliation OK · registry conferma

## 8 · Priest/paladin many-to-one

- `priest → paladino` (mapped_alias · MEDIUM · live 278)
- `paladin → paladino` (mapped_canonical · HIGH · live 303)
- Reverse map R18.3e: `paladino ← ['paladin', 'priest']`
- **Many-to-one ratificato dal registry**
- **Salvaguardia obbligatoria (LOCK)**: priest cohort e paladin cohort **DEVONO essere migrate come cohort SEPARATE**. **MAI nello stesso batch**. Rationale: mapping semanticamente diversi (mapped_alias vs mapped_canonical), confidence diversa (MEDIUM vs HIGH), evitare collisione di target semantica e audit ambiguity in caso di rollback.

## 9 · 268 NULL_CONFLICT lock

- `db.adventurers.count_documents({'$or':[{'class_slug': None}, {'class_slug': {'$exists': False}}]})` = **268**
- Riclassificazione R18.3f-R1:
  - `CLASSLESS_CONFIRMED` = **0**
  - `NULL_UNRESOLVED` = **0**
  - `NULL_CONFLICT` = **268** (100%)
  - `NO_ACTION` = **0**
- Evidenze classe presenti per ogni record: `class_name` valorizzato (11 valori) · `class_role` valorizzato (4 valori) · `adventurer_class_id` valorizzato (11 UUID). `class_slug` è l'unico field mancante.
- **Regola LOCK**: i 268 record **NON sono Reclute**. `class_slug=null ≠ recruit_unassigned`. NO auto-conversion. NO fill implicito. NO runtime auto-derive.

## 10 · Zero CLASSLESS_CONFIRMED

`CLASSLESS_CONFIRMED = 0` · condizione R3f-Q1 CUSTOM (5 criteri richiesti) **non soddisfatta da nessun record** dei 268:
1. stato Recluta esistente — parzialmente vero (is_starter=True) ma anche recluta ha classe assegnata nei 268
2. assenza classe storica — la classe è attuale (class_name+class_role+adventurer_class_id popolati)
3. assenza evidenza assegnazione — evidenza presente
4. flusso creazione compatibile — batch seed pre-hotfix, non flusso "recluta senza classe"
5. zero conflitti con altri campi — 100% conflict (class_slug=null ma classe altrove)

## 11 · A1 diagnostic RESOLVED / data STILL OPEN

- **A1 diagnostic classification**: RESOLVED — l'ambiguità sul significato dei 268 null è chiusa (verdict: NULL_CONFLICT 100%).
- **A1 data inconsistency**: STILL OPEN — il campo `class_slug` continua a essere null per 268 record. La rimediazione dati richiede: gate futuro dedicato `R18.3f-NC1 Null Conflict Remediation Planning`. Rimediazione = deterministica, versionata, auditata, snapshot-backed, PM-approved. **NOT AUTHORIZED NOW**.

## 12 · A2 archive-only

- `adventurers_r18_archive.class_slug` distinct 11 (mix legacy + canonical IT + placeholder): `alchemist`, `bard`, `cacciatore_del_vuoto`, `cacciatore_di_mostri`, `druid`, `mage`, `monk`, `paladin`, `recruit_unassigned`, `rogue`, `warrior`.
- Archive contiene canonical IT già bridged storicamente.
- **Policy CONFIRMED**: archive = historical evidence · NO retro-propagation · NO mutation archive · NO copia automatica verso live.
- Non-blocking per closure R18.3f.

## 13 · Anomalie A1-A14 · status finale

| ID | Severity | Status closure |
|---|---|---|
| **A1** | MEDIUM | **RESOLVED (diagnostic) · STILL OPEN (data · rimediazione in R18.3f-NC1)** |
| **A2** | MEDIUM | CONFIRMED · archive-only policy · non-blocking |
| **A3** | LOW | CONFIRMED · catalog 18 vs live 11 (delta 7 atteso) |
| **A4** | INFO | CONFIRMED · class_halls aligned |
| **A5** | MEDIUM (upgraded) | UPGRADED · parent_class_slug field 0 distinct · dormant code · **NON creare** · review in Gate 11 |
| **A6** | MEDIUM | 268 batch seed uniforme `2026-07-05T15:55:48.9...` pre-R16.5.4c ADJ-9 + pre-R18-reset1b |
| **A7** | LOW | phase13_unbaked=True per tutti 268 · flag "phase 13 pending" |
| **A8** | INFO | `career_history` collection VUOTA (0 docs) · **NON utilizzabile come evidence** · NO retroactive reconstruction · NO backfill · NO inference |
| **A9** | MEDIUM | `parent_class_slug` 0 distinct in tutte le collection · dormant |
| **A10** | MEDIUM | 268 reconstructable via `class_name`+`class_role`+`adventurer_class_id` |
| **A11** | LOW | `created_at` STRING type · **OUT OF SCOPE R18.3f** · data hygiene technical debt · Gate 11 prerequisite review |
| **A12** | LOW | 11 field mancanti nei 268 (status/grade/xp/hp_*/is_retired/r18_reset1b_*) |
| **A13** | INFO | `previous_class_slug` solo Zero-leak metadata filter (`guilds/routes.py:135`) |
| **A14** | INFO | `bridge_status_enum` R18.3e 7° valore (`ambiguous_pending_pm`) safety hatch inutilizzata |

## 14 · Risk register consolidato

**CRITICAL**:
- **R9** · sealed integrity violated during future apply · mitigation: sealed apply package + pre-apply manifest + snapshot + dry-run + cohort boundary + post-batch integrity + manual stop gate.

**HIGH**:
- **R1** · migration parziale → stato inconsistente
- **R2** · auto-derive drift
- **R6** · API breaking change
- **R7** · Class Halls out-of-sync
- **R10** · rollback fallito
- **R14** · auto-derive 268 NULL_CONFLICT → recruit_unassigned **VIETATO**

**MEDIUM**:
- **R3** · test artifact propagation
- **R4** · conflict record UI mismatch
- **R5** · 268 null ambiguità (risolta a livello classification, aperta a livello data)
- **R11** · idempotency key collision
- **R13** · NULL_CONFLICT vs CLASSLESS_CONFIRMED misuse
- **R16** · created_at STRING type breaks temporal aggregations

**LOW**:
- **R8** · career_history frammentato (mitigato dal vuoto absoluto: A8)
- **R12** · performance batch 3628 record
- **R15** · parent_class_slug dormant read None
- **R18** · bridge paladin/priest many-to-one collision

**INFO**:
- **R17** · career_history VUOTA · snapshot pre-apply unica rollback strategy

Totale rischi tracked: **R1-R18 = 18 rischi**.

## 15 · Migrazione staged per cohort

Sequenza obbligatoria (design_only · NOT AUTHORIZED NOW):

1. **Registry validation**: verifica bridge_entries invariati vs R18.3e sealed baseline
2. **Full dry-run read-only**: candidate classification su tutti gli adventurers live (3628)
3. **Snapshot verified**: snapshot pre-apply della collection target con hash manifest
4. **Cohort count freeze**: freeze del count candidati per cohort · nessun cambio non spiegato
5. **Canary controlled**: batch limitato N=10-50 record del cohort target · verifica post-batch
6. **Source mapping cohort**: applicazione batch full del cohort corrente · UN cohort per volta
7. **Post-batch validation**: verifica integrità (conteggi, seal, canonical, archive integrity)
8. **Integrity check**: pytest sealed + hash lore_meta invariante
9. **Explicit stop gate**: STOP obbligatorio · attesa PM GO per cohort successivo
10. **Cohort successiva**: ripete step 5-9

**Cohort separate obbligatorie** (LOCK):
- `warlock → cacciatore_del_vuoto` (305 record)
- `priest → paladino` (278 record) · MAI insieme con paladin
- `paladin → paladino` (303 record) · MAI insieme con priest
- `warrior → guerriero` (331 record)
- `rogue → ladro` (302 record)
- `mage → mago` (281 record)
- `monk → monaco` (327 record)
- `druid → druido` (311 record)
- `alchemist → alchimista` (299 record)
- `bard → bardo` (324 record)
- `ranger → cacciatore_di_mostri` (299 record)
- `necromancer → negromante` (0 record)
- `assassin → ladro` (0 record)
- `berserker → guerriero` (0 record)

**NON one-shot** · **NON Wave 1 design order** · staging per cohort è ortogonale al design order delle classi.

## 16 · Null remediation dependency (R18.3f-NC1)

- **R18.3f-NC1 Null Conflict Remediation Planning** = nuovo gate documentale futuro
- **Status**: `NOT AUTHORIZED NOW` · MANDATORY PRE-APPLY DEPENDENCY (P4+ successor)
- Scope: definire il backfill dei 268 NULL_CONFLICT con criteri deterministici · versionati · auditati · snapshot-backed · PM-approved
- **Vincolo**: nessuna migrazione class_slug può essere applicata prima che R18.3f-NC1 sia CLOSED. I 268 record devono avere strategia rimediazione definita ed approvata dal PM prima di essere touched.
- **Fuori scope R18.3f-NC1**: creazione item, modifica catalogo R18.5, Registry v3 apply, class_slug apply per gli altri 3360 non-null.

## 17 · No-auto-derive policy (LOCK)

- **NO** `class_name` → `class_slug` auto-derive
- **NO** `adventurer_class_id` → `class_slug` auto-derive
- **NO** `null` → `recruit_unassigned` auto-convert
- **NO** runtime fallback lookup on null → catalog default
- **NO** archive → live retro-propagation
- Ogni conversione: PM directive + dry-run + snapshot + audit trail + rollback plan

## 18 · Runtime bridge DISABLED

- `runtime_bridge_status = disabled`
- `CLASS_SLUG_MIGRATION_ENABLED = false` (kill switch globale futuro)
- `migration_cohort_enabled[source, target] = false` (per-cohort flag futuro · design_only)
- Feature flag due livelli richiesti prima di qualunque apply · design documentato in R18.3f-R1 §6 (R3f-Q6)

## 19 · Migration NOT APPLIED

- `class_slug write count in R18.3f (incluso -R1 e closure)` = **0**
- `db writes` = **0**
- `collections touched` = **0** (solo read-only distinct/count)
- Migration bridge apply = **NOT AUTHORIZED**

## 20 · PM-lock policy

- **R18.3f** = **PM-LOCKED, NOT YET SEALED**
- Modifica futura richiede: (1) explicit PM reopen · (2) motivazione · (3) impact analysis · (4) diff documentale · (5) nuova review · (6) aggiornamento manifest
- File **NON aggiunti al seal system ora** (2-phase sealing: apply package pre-execution + closure manifest post-apply). 36 seal esistenti restano invariati.

## 21 · Governance result

- **R18.3f** = **PM APPROVED · CLOSED · PM-LOCKED · NOT APPLIED · NOT SEALED** 🏆
- **R18.3f-R1** = corrective audit acquisito (autoritativo su fatti corretti)
- **Draft R18.3f originale** = preservato storicamente (SHA immutati)
- **Precondizione P2** Gate 11 = **CLOSED** (draft generato + R1 audit + closure) → **P3** (review PM completata) può ora essere marcata CLOSED
- **P3** = **CLOSED** con questo dispatch
- **P4-P20** = restano HOLD/NOT_STARTED
- **Gate 11** = **NOT AUTHORIZED** (14 precondizioni residue)
- **Wave 1** = **HOLD**
- **RV3-EV** = **AUTHORIZED** (dispatch parallelo con questo closure)
- **R18.3f-NC1** = HOLD · pre-apply dependency
- **Monaco** = HOLD
- **Rite of Rebirth** (R18.6.RB1) = HOLD
- **Runtime implementation** = NOT AUTHORIZED

---

## 🛑 STOP FINALE · R18.3f CLOSED · PM-LOCKED · NOT APPLIED · NOT SEALED

- Pilot R18.6.3 Cacciatore del Vuoto = ACTIVE-DESIGN-READY (invariato)
- R18.3f = PM APPROVED · CLOSED · PM-LOCKED (con questo dispatch)
- Sealed integrity 36/36 attesa PASS
- `lore_meta.py` = invariato
- Pilot Certificate + Pilot Manifest = IMMUTABILI
- R18.3f originali (3 file) + R18.3f-R1 audit (2 file) = IMMUTABILI
- Backend/frontend/OpenAPI/test/DB = zero touch

Prossimo passo dispatch: R18.6.RV3-EV Eligibility Validation (STEP 3 di questo dispatch PM).
