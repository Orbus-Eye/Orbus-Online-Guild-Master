# R18.3f-R1 · Canonical Mapping & Null Cohort Reconciliation Audit

**Documento**: `r18_3f_mapping_null_reconciliation_audit.md`
**Regime**: READ-ONLY DISCOVERY · DOCUMENTAL ONLY · ITALIANO ONLY
**Trigger**: PM verdict R18.3f = CONDITIONAL DRAFT · MICRO-REWORK REQUIRED
**Parent draft**: `r18_3f_class_slug_migration_readiness.md/.json` (**INVARIATI**)
**Governance**: `apply_authorized = false` · `no_migration_applied = true` · closure R18.3f = **HOLD**
**Sealed integrity**: 36/36 attesa · `lore_meta.py` = `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`

---

## 1 · Scope e trigger

Il draft R18.3f originale ha ricevuto verdict PM = **CONDITIONAL DRAFT**. Micro-rework in file separato (questo audit). 20 verifiche obbligatorie · 4 blocchi (A paladin · B category correction · C null cohort · D parent_class_slug + anomalie).

**File R18.3f originali NON modificati**:
- MD SHA `746ad94f7f186684f08c4d5ab4268ab719a2287b3dfc078b5d3e0a8f53b69668`
- JSON SHA `d79401ebcbad376149a5ccb819fa8ead06cf180ad6b386022a94efe358ce3389`
- Manifest SHA `bc603ff8892f84efdafb6bdd1b6ddbe7c4b35b06eb165f2dc2c930c16debe63b`

---

## 2 · BLOCCO A · Paladin Reconciliation

### 2.1 · Verifica 1: presenza `paladin` live

`db.adventurers.count_documents({'class_slug': 'paladin'})` = **303** ✅ (presente).

### 2.2 · Verifica 2: conteggio esatto

- `class_slug='paladin'`: **303**
- `class_slug='paladino'`: **0** (canonical target IT non ancora applicato live)
- `class_slug='priest'`: **278**

### 2.3 · Verifica 3: presenza `paladin` nel catalog

`db.adventurer_classes.find_one({'slug':'paladin'})` = **PRESENTE**:
- `slug`: `paladin`
- `canonical_slug`: **`paladino`** ✅
- `alias_target`: `None`
- `bridge_status`: **`mapped_canonical`**
- `bridge_source_round`: **`R18.3e Phase B`**
- `display_name_it`: `Paladino`
- `is_base_class`: `True`
- `is_active`: `True`

### 2.4 · Verifica 4: presenza `paladin` nel bridge registry

Registry canonico bridge di riferimento: `/app/memory/r18_3e_bridge_registry.json`.

- `bridge_entries` (18 total) contiene entry esplicita `paladin`:
  - `slug`: `paladin`
  - `canonical_slug`: `paladino`
  - `alias_target`: `null`
  - `bridge_status`: `mapped_canonical`
  - `bridge_source_round`: `R18.3e Phase B`
  - `confidence`: `HIGH`
  - `adventurers_live`: **303**
  - `display_name_it_live`: `Paladino`
- `reverse_map_canonical_to_legacy['paladino']` = `['paladin', 'priest']` ✅ many-to-one confermato

**File `r18_6_1_canonical_27_class_halls_expansion.json`** (registry Halls): contiene 27 canonical_it slug, tra cui `paladino`. Non è la fonte del bridge legacy→canonical (quello è R18.3e). Nessuna occorrenza di `paladin` legacy in R18.6.1 (correttamente, poiché R18.6.1 opera solo con canonical IT).

### 2.5 · Verifica 5: target canonico di `paladin`

**`paladin → paladino`** ✅ (mapped_canonical · confidence HIGH · R18.3e Phase B)

### 2.6 · Verifica 6: many-to-one `priest + paladin → paladino`

- `priest → paladino` (mapped_alias · confidence MEDIUM · live 278)
- `paladin → paladino` (mapped_canonical · confidence HIGH · live 303)
- **Many-to-one ammesso e ratificato dal registry R18.3e**.
- `reverse_map_canonical_to_legacy['paladino'] = ['paladin', 'priest']`.
- Somma live: 303 + 278 = 581 record che convergerebbero su `paladino` in migration futura.

### 2.7 · Verifica 7: numero totale mapping source

Registry R18.3e ha **18 bridge_entries** totali. Di queste:
- **14 legacy_source → canonical_target** (11 canonical target IT + 3 mapped_alias):
  - 9 `mapped_canonical`: warrior, rogue, mage, monk, **paladin**, druid, alchemist, bard, necromancer
  - 3 `mapped_alias`: priest, ranger, warlock
  - 2 `deprecated_alias`: assassin, berserker
- **2 `canonical_native`**: cacciatore_di_mostri, cacciatore_del_vuoto (canonical già target)
- **1 `technical_placeholder`**: recruit_unassigned
- **1 `test_artifact`**: test-class-5e0064

**Totale mapping source = 14** ✅ (matcha baseline PM: 11 originali + paladin + assassin + berserker).

---

## 3 · BLOCCO B · Mapping Category Correction (Semantic Fix)

### 3.1 · Verifica 8: correzione semantica obbligatoria

**Errore semantico nel draft R18.3f originale** (§17 tabella bridge): 11 mapping erano classificati come `canonical_native` (es. `warrior → guerriero`). Categoria **errata**.

**`canonical_native`** = valore che è **GIÀ** espresso nel canonical slug IT. Solo `cacciatore_di_mostri` e `cacciatore_del_vuoto` rientrano.

**`mapped_canonical` / `mapped_alias`** = legacy EN mappato verso canonical target IT.

### 3.2 · Categorie R18.3e (7 valori enum ufficiali)

Da `bridge_status_enum` in R18.3e:
1. `mapped_canonical`
2. `mapped_alias`
3. `deprecated_alias`
4. `technical_placeholder`
5. `test_artifact`
6. `canonical_native`
7. `ambiguous_pending_pm`

### 3.3 · Bridge registry CORRETTO (18 entries · 14 mapping source)

| # | legacy_source | canonical_target | bridge_status | confidence | live |
|---|---|---|---|---|---|
| 1 | `warrior` | `guerriero` | **mapped_canonical** | HIGH | 331 |
| 2 | `rogue` | `ladro` | **mapped_canonical** | HIGH | 302 |
| 3 | `mage` | `mago` | **mapped_canonical** | HIGH | 281 |
| 4 | `priest` | `paladino` | **mapped_alias** | MEDIUM | 278 |
| 5 | `ranger` | `cacciatore_di_mostri` | **mapped_alias** | MEDIUM | 299 |
| 6 | `monk` | `monaco` | **mapped_canonical** | HIGH | 327 |
| 7 | **`paladin`** | **`paladino`** | **mapped_canonical** | HIGH | **303** |
| 8 | `druid` | `druido` | **mapped_canonical** | HIGH | 311 |
| 9 | `alchemist` | `alchimista` | **mapped_canonical** | HIGH | 299 |
| 10 | `bard` | `bardo` | **mapped_canonical** | HIGH | 324 |
| 11 | `warlock` | `cacciatore_del_vuoto` | **mapped_alias** | MEDIUM | 305 |
| 12 | `necromancer` | `negromante` | **mapped_canonical** | MEDIUM | 0 |
| 13 | `assassin` | `ladro` | **deprecated_alias** | MEDIUM | 0 |
| 14 | `berserker` | `guerriero` | **deprecated_alias** | MEDIUM | 0 |
| 15 | `cacciatore_di_mostri` | (self) | **canonical_native** | HIGH | 0 |
| 16 | `cacciatore_del_vuoto` | (self) | **canonical_native** | HIGH | 0 |
| 17 | `recruit_unassigned` | N/A | **technical_placeholder** | HIGH | 0 |
| 18 | `test-class-5e0064` | N/A | **test_artifact** | HIGH | 0 |

### 3.4 · Correzione applicata

- **Categoria corretta `canonical_native`**: 2 slug (cacciatore_di_mostri, cacciatore_del_vuoto)
- **Categoria corretta `mapped_canonical`**: 9 slug (warrior, rogue, mage, monk, paladin, druid, alchemist, bard, necromancer)
- **Categoria corretta `mapped_alias`**: 3 slug (priest, ranger, warlock)
- **Categoria corretta `deprecated_alias`**: 2 slug (assassin, berserker)
- **Categoria corretta `technical_placeholder`**: 1 slug (recruit_unassigned)
- **Categoria corretta `test_artifact`**: 1 slug (test-class-5e0064)

**Aggregato mapping source (legacy → canonical)**: 9 + 3 + 2 = **14** ✅.

### 3.5 · Nota su `paladin` mancante nel draft originale

Il draft R18.3f §17 ometteva la riga `paladin → paladino`. Il registry R18.3e canonico la contiene esplicitamente. **Correzione**: 14 mapping (non 13) è la baseline corretta post-reconciliation.

---

## 4 · BLOCCO C · 268 Null Cohort Reconciliation

### 4.1 · Verifica 9: totale null cohort

`db.adventurers.count_documents({'$or':[{'class_slug': None}, {'class_slug': {'$exists': False}}]})` = **268** ✅.

### 4.2 · Verifica 10: schema completo dei 268 null

Field union osservati su sample 30 doc (presente in 30/30):
`_id`, `id`, `guild_id`, `name`, `adventurer_class_id`, `class_name`, `class_role`, `rarity`, `level`, `experience`, `strength`, `agility`, `intellect`, `endurance`, `faith`, `stamina`, `morale`, `traits`, `is_available`, `is_starter`, `created_at`, `updated_at`, `phase13_unbaked`.

**Field NON presenti nei 268 null** (mentre presenti negli altri 3360 non-null): `status`, `grade`, `r18_reset1b_seed_source`, `r18_reset1b_starter`, `r18_reset1b_stat_source`, `r18_reset1b_hotfix_v1_2`, `r18_reset1b_hotfix_v1_3`, `xp`, `hp_max`, `hp_current`, `is_retired`.

### 4.3 · Verifica 11: evidenze stato Recluta

Distinct field-values su null cohort:
- `is_starter`: **[True]** (100%)
- `is_available`: **[True]** (100%)
- `is_retired`: **[]** (field non presente)
- `phase13_unbaked`: **[True]** (100%)
- `level`: **[1]** (100%)
- `rarity`: **['Common']** (100%)
- `status`: **[]** (field non presente)
- `grade`: **[]** (field non presente)

**Non esiste field `is_recruit`** in adventurers schema.

### 4.4 · Verifica 12: evidenze classe precedente / storia

- `class_history`: field NON presente.
- `previous_class`: field NON presente.
- `previous_class_slug`: field NON presente (nonostante `backend/app/guilds/routes.py:135` lo referenzi come metadato tecnico da filtrare).
- `career_events`: field NON presente.
- `career_started`: field NON presente.
- `career_history` (**collection**): `count_documents({})` = **0** (collection VUOTA).
- Nessuna evidenza di storia classe per i 268 null.

### 4.5 · Verifica 13: conflitti (null + campo classe alternativo non-null)

- `class_slug=null + class_name != null`: **268/268** ⚠️ CONFLICT
- `class_slug=null + adventurer_class_id != null`: **268/268** ⚠️ CONFLICT
- `class_name` distinct nei 268 null: `['Alchemist', 'Bard', 'Druid', 'Mage', 'Monk', 'Paladin', 'Priest', 'Ranger', 'Rogue', 'Warlock', 'Warrior']` (11 valori legacy EN)
- `class_role` distinct nei 268 null: `['DPS', 'Healer', 'Support', 'Tank']` (4 valori)
- `adventurer_class_id` distinct nei 268 null: 11 UUID (uno per classe)

**Conclusione B.1**: TUTTI i 268 record hanno CLASSE ASSEGNATA via `class_name`+`class_role`+`adventurer_class_id`, MA `class_slug` field mancante/null.

### 4.6 · Verifica 14: documenti incompleti (schema anomalo)

Field mancanti rispetto ai 3360 non-null:
- Mancanti in 268/268: `status`, `grade`, `xp`, `hp_current`, `hp_max`, `is_retired`, `r18_reset1b_seed_source`, `r18_reset1b_starter`, `r18_reset1b_stat_source`, `r18_reset1b_hotfix_v1_2`, `r18_reset1b_hotfix_v1_3`
- Interpretazione: batch di seed pre-R16.5.4c/R18.reset1b (**pre-hotfix batch**).

### 4.7 · Verifica 15: distribuzione per status

Aggregate `$group` per `status`:
- `status=None`: **268/268** (field non popolato)

Nessuna distribuzione utile per `status` (uniforme null).

### 4.8 · Verifica 16: distribuzione temporale

Timestamp `created_at` osservati su 5 sample (tipo BSON = **string**, non Date):
- `2026-07-05T15:55:48.919796+00:00` (Druid)
- `2026-07-05T15:55:48.920356+00:00` (Monk)
- `2026-07-05T15:55:48.920777+00:00` (Ranger)
- `2026-07-05T15:55:48.921300+00:00` (Warrior)
- `2026-07-05T15:55:48.921794+00:00` (Priest)

**Batch temporale uniforme**: TUTTI creati nel range `2026-07-05T15:55:48.9...` (sub-secondo). **Single seed batch**.

**Nota**: `created_at` è STRING type. Aggregation `$dateToString` fallisce con `can't convert from BSON type string to Date`. Anomalia dati.

### 4.9 · Verifica 17: creation_source

- `creation_source`: field NON presente in adventurers schema.
- `created_by`: field NON presente.
- `source`: field NON presente.
- Nessun tracker esplicito di origine dei 268 (inferito da altri metadati assenti).

### 4.10 · Verifica 18: career/history evidence

- `career_history` collection: **0 docs** (VUOTA).
- Linked entries per 500 sample null adventurer ids: **0**.
- Nessuna evidenza di gameplay/progressione per i 268:
  - `xp > 0`: field non presente
  - `experience > 0`: 0 (tutti hanno `experience=0` o field default)
  - `level > 1`: 0 (tutti level=1)

**Conclusione**: nessuna evidenza di "vita" pregressa per i 268. Sono seed pre-hotfix mai attivati/mai giocati.

### 4.11 · Riclassificazione 4 sotto-cohort

| Sotto-cohort | Count | % | Note |
|---|---|---|---|
| `CLASSLESS_CONFIRMED` | **0** | 0.0% | Nessun record senza classe assegnata; tutti hanno `class_name`+`class_role`+`adventurer_class_id` |
| `NULL_UNRESOLVED` | **0** | 0.0% | Nessun record con evidenza insufficiente; classe evidente da 3 campi alternativi |
| `NULL_CONFLICT` | **268** | 100.0% | `class_slug=null` MA classe già assegnata via `class_name`+`class_role`+`adventurer_class_id` |
| `NO_ACTION` | **0** | 0.0% | Nessun record schema anomalo che richieda esclusione categorica |
| **TOTALE** | **268** | 100.0% | ✅ |

### 4.12 · Distribuzione NULL_CONFLICT per class_name

| class_name | count | inferable canonical target (post-review) |
|---|---|---|
| Alchemist | 27 | alchimista |
| Bard | 26 | bardo |
| Druid | 28 | druido |
| Mage | 22 | mago |
| Monk | 22 | monaco |
| Paladin | 27 | paladino |
| Priest | 17 | paladino |
| Ranger | 28 | cacciatore_di_mostri |
| Rogue | 20 | ladro |
| Warlock | 23 | cacciatore_del_vuoto |
| Warrior | 28 | guerriero |
| **TOTALE** | **268** | ✅ |

**Nota (regola PM R3f-Q1 CUSTOM)**: nonostante l'inferabilità, NON auto-derivare. NULL_CONFLICT resta lo stato dichiarato · PM decide handling in gate futuro.

---

## 5 · BLOCCO D · parent_class_slug + Anomalie Aggiornate

### 5.1 · Verifica 19: parent_class_slug distinct

- `adventurers.parent_class_slug`: distinct **[]** (0 valori) · exists **0** · non-null **0**.
- `adventurer_classes.parent_class_slug`: distinct **[]** (0 valori) · exists **0**.
- `class_specializations.parent_class_slug`: distinct **[]** (0 valori) · exists **0**.

**Field `parent_class_slug` NON esiste live in nessuna collection** — nonostante `backend/app/adventurers/services.py:169` lo referenzi (`"parent_class_slug": doc.get("parent_class_slug")`). Codice dormant senza dati live.

### 5.2 · Verifica 20: anomalie aggiornate

**Anomalie originali (draft R18.3f)** confermate + integrate:

| ID | Severity | Descrizione | Status R18.3f-R1 |
|---|---|---|---|
| A1 | MEDIUM | 268 null cohort senza recruit_unassigned associato | ✅ RESOLVED: riclassificati 100% NULL_CONFLICT |
| A2 | MEDIUM | Discrepanza live legacy EN vs archive mix canonical IT | ✅ CONFERMATA (archive-only) |
| A3 | LOW | Catalog 18 slug vs live 11 slug delta 7 | ✅ CONFERMATA (necromancer+assassin+berserker legacy senza live · placeholder+test artifact+2 canonical_native senza live) |
| A4 | INFO | class_halls.class_slug allineato ai 11 live | ✅ CONFERMATA |
| A5 | LOW | parent_class_slug referenziato in services.py:169 ma non verificato | ⚠️ **UPGRADED** a **MEDIUM**: field NON esiste in NESSUNA collection · codice dormant |

**Anomalie NUOVE (R18.3f-R1)**:

| ID | Severity | Descrizione | Impact |
|---|---|---|---|
| **A6** | MEDIUM | 268 null cohort è batch uniforme `2026-07-05T15:55:48.9...` (single seed pre-hotfix) | Batch identificabile · migrazione può essere targettizzata |
| **A7** | LOW | `phase13_unbaked=True` per tutti 268 | Flag "phase 13 non completata" → questi record sono in sospeso |
| **A8** | INFO | `career_history` collection = **VUOTA** (0 docs) | Nessuna storia gameplay per NESSUN adventurer live/archive |
| **A9** | MEDIUM | `parent_class_slug` field 0 distinct in tutte le collection | Codice services.py:169 dormant · possibile refactor safe (fuori scope R18.3f) |
| **A10** | MEDIUM | `class_slug=null` è **reconstructable** via `class_name`+`adventurer_class_id`+`class_role` per tutti 268 | NULL_CONFLICT, non CLASSLESS · classe è già assegnata implicitamente |
| **A11** | LOW | `created_at` è STRING type in Mongo (non ISO Date) | Aggregation temporal fallisce · potenziali performance issue future |
| **A12** | LOW | 268 null cohort NON ha `status`, `grade`, `xp`, `hp_max`, `hp_current`, `is_retired`, `r18_reset1b_*` (presenti negli altri 3360) | Batch pre-reset1b/pre-hotfix · schema-drift storico |
| **A13** | INFO | `previous_class_slug` referenziato solo in `guilds/routes.py:135` come metadato tecnico da filtrare in Zero-leak (non memorizzato) | Coerente con audit R18.5 zero-leak |
| **A14** | INFO | `bridge_status_enum` R18.3e ha 7 valori (7° = `ambiguous_pending_pm`) safety escape hatch | Ammesso · nessuna entry attualmente in stato ambiguous |

### 5.3 · Risk register aggiornato

Rischi ereditati dal draft originale (R1..R12): **INVARIATI**.

Nuovi rischi emersi da R18.3f-R1:

| ID | Severity | Rischio | Mitigation |
|---|---|---|---|
| **R13** | MEDIUM | 268 NULL_CONFLICT · classificazione errata come CLASSLESS_CONFIRMED | R18.3f-R1 riclassifica in NULL_CONFLICT · no auto-derive |
| **R14** | HIGH | Migration futura potrebbe erroneamente creare `class_slug='recruit_unassigned'` sui 268 null (regola PM violata) | `null → recruit_unassigned` auto-derive VIETATO · verdict NULL_CONFLICT esplicito |
| **R15** | LOW | `parent_class_slug` dormant referenced in services.py:169 potrebbe leggere `None` in produzione senza gestione esplicita | Codice safe (`doc.get(...)`) · nessun crash · monitoring suggerito |
| **R16** | MEDIUM | `created_at` STRING type breaks temporal aggregations · future migration potrebbe assumere Date | Normalizzazione dati fuori scope R18.3f · flag rischio per Gate 11 sub-plan |
| **R17** | INFO | `career_history` VUOTA · nessun rollback storico via history | Snapshot pre-apply resta unica strategia rollback (design §29 originale) |
| **R18** | LOW | Bridge `paladin → paladino` (mapped_canonical) many-to-one con `priest → paladino` (mapped_alias) · potenziale collision futura | Documented · migrated one cohort at time (§R3f-Q4 CUSTOM staged) |

---

## 6 · Regole ferree PM (R3f-QN CUSTOM) recepite

- **R3f-Q1 CUSTOM**: `null ≠ recluta` · NO auto-conversione a `recruit_unassigned` · 268 = **NULL_CONFLICT** (evidenza indipendente li conferma con classe assegnata via altri field).
- **R3f-Q2**: Paladin **CONFERMATO** nel registry R18.3e (mapped_canonical HIGH) · nessuno STOP mismatch · 14 mapping baseline.
- **R3f-Q3**: Archive canonical (`cacciatore_del_vuoto`, `cacciatore_di_mostri`, `recruit_unassigned` in `adventurers_r18_archive`) = HISTORICAL EVIDENCE · NO retro-propagazione · NO mutation.
- **R3f-Q4**: Migration futura **staged per mapping cohort** · schema cohort documentato · `apply_authorized=false`.
- **R3f-Q5**: Compat window minimum 4 settimane · condizioni uscita cumulative (7 gate) · design-only.
- **R3f-Q6**: Feature flag due livelli (`CLASS_SLUG_MIGRATION_ENABLED` globale + `migration_cohort_enabled[source, target]` per-cohort) · design-only.
- **R3f-Q7**: Frontend/backend compatibility review preventiva · condizione blocking per Gate 11.
- **R3f-Q8**: `test-class-5e0064` = **PRESERVE** · `migration_eligible=false` · `auto_map=false` · `runtime_propagation=false` · aggiungere guard esplicito in gate futuro.
- **R3f-Q9**: Snapshot + STOP immediato + rollback manuale double-gate · trigger STOP enumerati.
- **R3f-Q10**: PM-lock alla closure · sealing in 2 fasi (apply package + closure manifest) · **NO nuovo seal ora**.

---

## 7 · Sintesi verdict finale R18.3f-R1

### 7.1 · Blocco A · Paladin reconciliation

| Verifica | Esito |
|---|---|
| paladin live | 303 ✅ |
| catalog | present · canonical_slug=paladino · mapped_canonical · R18.3e Phase B ✅ |
| bridge registry R18.3e | present · confidence HIGH · adventurers_live=303 ✅ |
| target canonico | `paladino` ✅ |
| many-to-one | priest+paladin → paladino ✅ (reverse_map R18.3e conferma) |
| mapping source count | **14** ✅ |
| STOP mismatch? | **NO** · reconciliation completata |

### 7.2 · Blocco B · Category correction

| Categoria | Slug count | Draft R18.3f originale | Correzione R18.3f-R1 |
|---|---|---|---|
| `canonical_native` | 2 | 11 (ERRATO) | **2** ✅ (solo cacciatore_di_mostri, cacciatore_del_vuoto) |
| `mapped_canonical` | 9 | 0 (mancante) | **9** ✅ |
| `mapped_alias` | 3 | 0 (mancante) | **3** ✅ |
| `deprecated_alias` | 2 | 0 (mancante) | **2** ✅ |
| `technical_placeholder` | 1 | 1 | 1 ✅ |
| `test_artifact` | 1 | 1 | 1 ✅ |
| `ambiguous_pending_pm` | 0 | 0 | 0 (safety hatch) |
| **totale bridge_entries** | **18** | 13 (incompleto) | **18** ✅ |

### 7.3 · Blocco C · 268 null cohort

| Sotto-cohort | Count | Note |
|---|---|---|
| `CLASSLESS_CONFIRMED` | 0 | |
| `NULL_UNRESOLVED` | 0 | |
| `NULL_CONFLICT` | **268** | 100% · tutti hanno classe implicita via `class_name`+`adventurer_class_id`+`class_role` ma `class_slug=null` |
| `NO_ACTION` | 0 | |
| **totale** | **268** ✅ | |

### 7.4 · Blocco D · parent_class_slug + anomalie

- `parent_class_slug`: **0 distinct** in tutte le collection → codice dormant (A9 MEDIUM).
- Nuove anomalie: **A6-A14** (9 anomalie aggiuntive).
- Nuovi rischi: **R13-R18** (6 rischi aggiuntivi).

---

## 8 · Governance R18.3f-R1

- **Closure R18.3f**: **HOLD** · PM decide se accettare micro-rework in questo file separato oppure richiedere rework diretto ai file R18.3f originali (che restano INVARIATI).
- **File R18.3f originali NON modificati**.
- **Pilot Certificate + Pilot Manifest INVARIATI**.
- **PRD NON toccato** in questa fase.
- **Gate 11** = NOT AUTHORIZED.
- **Wave 1** (Monaco/Druido/Alchimista/Bardo/Negromante) = HOLD.
- **RV3-EV** = HOLD.
- **Runtime implementation** = NOT AUTHORIZED.
- **Sealed integrity**: attesa 36/36 PASS · `lore_meta.py` invariato.

---

## 🛑 STOP FINALE · R18.3f-R1 AUDIT GENERATO · PENDING PM VERDICT

- 20 verifiche completate ✅
- Paladin reconciliation: CONFERMATO 14 mapping baseline
- Category correction: 11 mapping riclassificati da `canonical_native` → `mapped_canonical` (9) / `mapped_alias` (3) / `deprecated_alias` (2 nuovi introdotti nel bridge R18.3e)
- 268 null cohort: 100% **NULL_CONFLICT** (nessun CLASSLESS_CONFIRMED)
- parent_class_slug: **0 distinct** · codice dormant · upgrade a MEDIUM
- 9 anomalie nuove (A6-A14) · 6 rischi nuovi (R13-R18)

**Attendo verdict PM finale su R18.3f (CLOSE / REWORK / HOLD).**

- `apply_authorized = false`
- `no_migration_applied = true`
- `class_slug write count = 0`
- `db writes = 0`
- Nessun apply · nessun Gate 11 · nessun Wave 1 kickoff senza PM directive esplicita
