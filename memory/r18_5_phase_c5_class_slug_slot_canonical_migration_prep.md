# R18.5 — Phase C5 · Class Slug + Slot Canonical + Source Canonicalization Migration Prep (DOUBLE-TRACK)

**Round**: R18.5 · **Phase**: C5 Class Slug Migration Prep + Slot Canonical Migration Planning (DOUBLE-TRACK)
**Locked at UTC**: `2026-07-08T13:30:00Z`
**Governance**: **DOCUMENTAL ONLY — migration prep design layer (double-track A+B+C). NO migration apply · NO code/DB/migrations · NO auto-derive · NO runtime bridge.**
**Status**: ✅ **APPLIED — migration prep documental per PM review pre-C6**
**Authority**: PM Orchestrator — Phase C5 dispatch (Q8=GO double-track)
**Lingua output**: 🇮🇹 SOLO ITALIANO

**Deliverables**:
- `/app/memory/r18_5_phase_c5_class_slug_slot_canonical_migration_prep.md` (questo file)
- `/app/memory/r18_5_phase_c5_class_slug_slot_canonical_migration_prep.json` (SHA256 `bc9fb2e6d85e5bbaa9703125ed217448a6f32b1ede1b7b4d2448eac02f3ebd57`)

---

## Executive Summary — Triple Track

**Scope**:
- TRACK A · Class Slug Migration Prep (R18.3f readiness → R18.6 execute)
- TRACK B · Slot Canonical Migration Planning (Q4=A trinket→accessory + 8 alias table)
- TRACK C · Source Canonicalization (dungeon 61→60, raid 13→12, hollow-monastery non-raid)

**Invarianti preservati** (nessuna modifica ammessa in C5):

- `item_count_1500`: True
- `rarity_400_450_400_235_15`: True
- `class_300x5`: True
- `class_slug_null_1500_1500`: True
- `runtime_apply_ready_0_1500`: True
- `progressive_marker_10`: True
- `anti_p2w_1500_1500`: True
- `canonical_slot_count_14`: True
- `canonical_dungeon_count_60`: True
- `canonical_raid_count_12`: True


---

## TRACK A · Class Slug Migration Prep

### 1. class_slug null gap tracking
- **Current state**: class_slug=null 1500/1500 (100% gap)
- **Resolution status field**: `class_slug_resolution_status = deferred_to_C5_R18_3f (1500/1500)`
- **Invariante C5**: In C5: `class_slug=null` **PRESERVATO** (no auto-derive · no apply)
- **Target post-R18.6**: class_slug valorizzato lato adventurer (item side rimane `class_proficiency` canonical W/R/M/P/Ranger)

### 2. Roadmap C5→R18.3f→R18.6

| Step | Descrizione |
|---|---|
| **1. C5 prep** (this doc) | documentazione bridging + hook design (no apply) |
| **2. R18.3f readiness** | runtime prep for class_slug schema + adventurer.class_slug column · migration script design (no apply) |
| **3. R18.6 execute** | Class Halls · Classless Start · adventurer.class_slug population via UI onboarding |
| **4. post-R18.6** | runtime_apply_ready true per items applicable + class_slug non-null validator active |

### 3. Recruit unassigned handling
- **Permessi**: esistere nel roster · essere visualizzato in UI · ricevere prompt/tutorial onboarding · ricevere item universal_allowed (consumable/material/cosmetic)
- **Vietati**: equipaggiare gear specializzato (armor/weapon proficiency-locked) · essere considerato pienamente pronto per dungeon 3p/raid 5p · partecipare a Legendary drop encounter
- **Phase risoluzione**: C5 (prep) → R18.3f (readiness) → R18.6 (execute Class Hall assignment)

### 4. Classless Start R18.6 hooks
- **Narrative**: Recluta arrivata alla Gilda senza classe definita; interagisce con Class Halls per scegliere il proprio Path (W/R/M/P/Ranger)
- **UI**: Modal onboarding con 5 Class Hall cards + descrizione lore/utility
- **Gameplay**: Tutorial encounter pre-classe (universal_allowed items only)
- **Post-selection**: adventurer.class_slug = selected_class · runtime_apply_ready true per items W/R/M/P/Ranger applicable · class_proficiency lock enforcement attivo

### 5. class_proficiency bridging design
- **Principio**: class_proficiency (canonical item-side W/R/M/P/Ranger) NON deve auto-derivare adventurer.class_slug
- **NO auto-derive**: True
- **Pseudo-logic**: `IF adventurer.class_slug != None AND adventurer.class_slug == item.class_proficiency THEN equippable (dopo altri check C2). ELSE lock_state = locked_class_slug_null OR locked_proficiency_class`
- **Canonical map**: {"Warrior": "warrior", "Rogue": "rogue", "Mage": "mage", "Priest": "priest", "Ranger": "ranger"}

### 6. Validator hooks C2 integration
- **Flow extended**: post class_slug population (R18.6), C2 validator step 3 (`class_slug is None + class_proficiency is None`) → step 4 (`class_slug is None but class_proficiency present`) sostituiti da: step 3' `class_slug != item.class_proficiency` → `locked_proficiency_class`
- **Integration points**:
  - C2 lock_state matrix estesa con `locked_proficiency_class` post-R18.6
  - UI badge nuovo: 'rosso · icona classe barrata' per `locked_proficiency_class`
  - class_slug null resolution rimuove `locked_class_slug_null` da matrix runtime post-R18.6


---

## TRACK B · Slot Canonical Migration

### 7. Slot alias mapping (additive)

**Principio**: Migration ADDITIVE · aggiunge `slot_canonical` a ogni item · preserva `slot_original` per audit · NO destructive rename

| slot_original | → slot_canonical | count D1-D5 | rationale |
|---|:--:|:--:|---|
| `trinket` | `accessory` | **68** | Q4=A · trinket = alias legacy/documentale RESERVED; accessory = slot canonico operativo; migration additive, mantiene `slot_original=trinket` per audit |
| `main-hand` | `main_hand` | **613** | Q7 C3 · underscore canonical (dash-hyphen alias legacy display) |
| `off-hand` | `off_hand` | **129** | Q7 C3 · underscore canonical |
| `amulet` | `neck` | **57** | Q7 C3 · `neck` slot canonico; `amulet` = alias legacy display |
| `belt` | `waist` | **0** | Q7 C3 · canonical rule (0 items osservati D1-D5, ma alias documentale per compat futuri) |
| `cloak` | `back` | **0** | Q7 C3 · canonical rule (0 items osservati) |
| `cape` | `back` | **0** | Q7 C3 · canonical rule (0 items osservati) |
| `weapon_main` | `main_hand` | **0** | Q7 C3 · canonical rule (0 items osservati) |
| `weapon_off` | `off_hand` | **0** | Q7 C3 · canonical rule (0 items osservati) |


**Totali**:
- Items migrating D1-D5: **867**
- Items universal (no migration): **26**
- Items already canonical: **607**
- **Total check: 1500 == 1500** ✅

### 8-9-10. Rules
- **Additive-only** · `slot_original` preservato · NO destructive rename
- **NO stat/tier/rarity/source/classe change**
- **Universal_allowed preservato** (`consumable`=17 · `material`=9) · NO migration
- Registry v1 (C1) rimane valido · registry v2 post-C5 aggiunge `slot_canonical` + `slot_original`

### 11. Canonical slot list finale (Q7 C3, 14 slots)

`head` · `neck` · `shoulders` · `chest` · `back` · `hands` · `wrist` · `waist` · `legs` · `feet` · `main_hand` · `off_hand` · `ring` · `accessory`

### 12. `trinket` RESERVED (NON slot operativo)
- **State**: trinket = alias legacy/documentale RESERVED · NON slot operativo
- **Post-migration**: 68 items ricevono `slot_canonical=accessory` · `slot_original=trinket` preservato per audit
- **NO 15° slot** · **NO sistema trinket**
- **Future note**: `trinket` può essere riattivato in phase futura post-R18.6 come slot narrativo/cosmetic (fuori scope C5)


---

## TRACK C · Source Canonicalization

### 13. Dungeon reconciliation 61 → 60

- **Observed C4**: 61 · **Canonical target Q5**: 60 · **Delta**: 1
- **Dungeon canonical 60**: (elenco completo in `.json` sezione 13)

**Token extra declassed (1)**:

| Field | Value |
|---|---|
| **token** | `void-heart-sanctum` |
| **items_count** | 8 |
| **classification** | **source_alias** |
| **rationale** | Q5 verbatim: dungeon canonical count RESTA 60 · token extra (`void-heart-sanctum`, 8 items T5) classificato source_alias · NON 61° dungeon · governance-safe tiebreak: last per items DESC + alphabetical |

### 14. Raid reconciliation 13 → 12

- **Observed C4**: 13 · **Canonical target Q6**: 12 · **Delta**: 1

**Raid canonical 12**: `krastlov-siege` · `necropolis-bells` · `emberking-siege` · `world-tree-collapse` · `memoria-vault` · `arcane-schism` · `void-cathedral` · `souldrain-abyss` · `celestial-conclave` · `dragon-vault` · `bloodgrove-uprising` · `broken-bastion-siege`

**hollow-monastery declassed**:

| Field | Value |
|---|---|
| **token** | `hollow-monastery` |
| **items_count** | 53 |
| **prev classification** | raid (C4 observed via `raid` keyword in source string) |
| **new classification** | **secondary_source (Q6 verbatim: non-raid)** |
| **sub-classification hint** | candidato dungeon 3p T2 large-encounter OR encounter narrativo secondary; PM può affinare in C6 |

### 15. source_original vs source_canonical
- `source_original`: preservato invariato
- `source_canonical`: documentale · derivato via matching primary token
- **Categorie 5**: dungeon_canonical · raid_canonical · source_alias · secondary_source · meta_source (vendor/quest/craft/etc)

### 16. Anti-drift check

| # | Check | Status |
|:--:|---|:--:|
| 1 | dungeon canonical count == 60 | **PASSED (60)** |
| 2 | raid canonical count == 12 | **PASSED (12)** |
| 3 | 1500/1500 non-null source preservato | **PASSED** |
| 4 | hollow-monastery declassed to non-raid | **PASSED** |
| 5 | 1 extra dungeon token classificato source_alias | **PASSED (void-heart-sanctum)** |


---

## 17. Migration Validation Checklist (18 check)

| # | Check | Status |
|:--:|---|:--:|
| **1** | Additive-only migration (no destructive rename) | PASSED |
| **2** | slot_original preservato invariato | PASSED |
| **3** | source_original preservato invariato | PASSED |
| **4** | class_slug=null 1500/1500 preservato | PASSED |
| **5** | runtime_apply_ready=false 1500/1500 preservato | PASSED |
| **6** | 0 modifiche a stat/tier/rarity/source-content/classe/ilvl | PASSED |
| **7** | Universal_allowed (consumable/material) NO migration | PASSED |
| **8** | Slot canonical 14 confermato Q7 C3 | PASSED |
| **9** | trinket RESERVED (NON 15° slot, NON sistema) | PASSED |
| **10** | 68 trinket items → slot_canonical=accessory (Q4=A) | PASSED |
| **11** | Dungeon canonical count = 60 (61→60, 1 source_alias) | PASSED |
| **12** | Raid canonical count = 12 (13→12, hollow-monastery non-raid) | PASSED |
| **13** | 1500/1500 items catalog invariante count | PASSED |
| **14** | Progressive Discovery P1-P4 status PENDING PM post-C6 preservato | PASSED |
| **15** | Anti-P2W 1500/1500 preservato | PASSED |
| **16** | 36 seals byte-identical | TO VERIFY post-write |
| **17** | lore_meta.py invariato | PASSED (no touch) |
| **18** | Zero DB/code/migrations | PASSED |


---

## 18. Risk Register (10 rischi R1-R10)

| ID | Rischio | Severità | Mitigazione | Status |
|:--:|---|:--:|---|:--:|
| **R1** | class_slug null percentage rimane 100% fino a R18.6 · gap operativo lungo | MEDIUM | roadmap C5→R18.3f→R18.6 chiara · nessun blocker C6 (documentale) | DOCUMENTED |
| **R2** | slot alias collision post-migration (es. `trinket` runtime references residue) | MEDIUM | slot_original preservato · rollback path chiaro · pre-apply audit obbligatorio | DESIGNED |
| **R3** | 68 items trinket→accessory potrebbero rompere UI legacy che si aspetta 'trinket' slot | LOW-MEDIUM | UI display `slot_canonical`, tooltip advanced `slot_original`; pre-R18.6 UI update | DESIGNED |
| **R4** | Source misclassification (hollow-monastery secondary vs dungeon sub-type) | LOW-MEDIUM | PM può affinare classification in C6 · sub_classification_hint fornito | TRACKED to C6 |
| **R5** | source_alias declassed token (void-heart-sanctum) potrebbe essere content narrativo importante | LOW | PM review C6 può ripristinare a dungeon canonical (delta +1 accettato) | TRACKED to C6 |
| **R6** | R18.3f readiness richiede runtime schema class_slug pre-implementation | MEDIUM | C5 documenta hook · schema design in R18.3f (fuori scope C5) | DEFERRED to R18.3f |
| **R7** | Classless Start UI onboarding può frustrare user (extra step pre-gameplay) | LOW-MEDIUM | R18.6 UX polish · tutorial encounter pre-classe bilanciato | TRACKED to R18.6 |
| **R8** | class_proficiency canonical case-insensitive normalization rimane latent | LOW | R18.3f runtime migration script normalizza input | TRACKED to R18.3f |
| **R9** | Progressive Discovery source PENDING PM post-C6 blocca 4/15 Legendary runtime enable | MEDIUM | documented Q7 · finalizzazione autonoma post-C6 · no blocker C6 closure | TRACKED to post-C6 |
| **R10** | Anti-P2W runtime validator non implementato · dipende da runtime_apply_ready true | MEDIUM | C6 closure documenta gate pre-runtime · anti-P2W design 8/8 PASSED · implementation R18.6+ | DEFERRED to R18.6+ |


---

## 19. GO/HOLD Recommendation

### Phase C6 Final Phase C Closure Report
- **Recommendation**: **GO — soggetto a PM approval esplicito post-C5 review**
- **Rationale**: C5 completa il triple-track migration prep (A: class_slug · B: slot canonical · C: source canonicalization). C6 sarà il Final Phase C Closure Report che aggrega tutto (C0→C5) e prepara handoff a R18.3f / R18.6 execution.

**Conditions**:
- PM approval C5 (Q1-Q8)
- Progressive Discovery 4 (P1-P4) source PENDING PM finalizzato post-C6 (fuori scope C6 closure)
- hollow-monastery sub_classification affinato in C6 (dungeon 3p T2 large-encounter vs secondary_source generico)
- source_alias declassed token (void-heart-sanctum) può essere restore dungeon canonical (delta +1 accettato) — decisione PM in C6

**Risks se GO**:
- R6 R18.3f readiness dipendenza · non blocca C6 closure documental
- R9 Progressive finalization post-C6 · non blocca C6 closure


### Fasi successive
- **R18.3f readiness** — PLANNED post-C6 · runtime schema class_slug + migration script design (execution R18.6)
- **R18.6 Class Halls / Classless Start** — PLANNED · esecuzione live migration + Class Halls UI + adventurer identity
- **Marketing Brief** — DEFERRED

---

## 20. PM Open Questions

| ID | Topic |
|:--:|---|
| **Q1** | Approvare C5 double-track migration prep (A class_slug · B slot canonical · C source canonicalization) come design layer input per C6 Final Closure? |
| **Q2** | Slot alias mapping 9 entries (trinket→accessory 68 items + 4 alias con items D1-D5 + 5 canonical rule 0 items): conferma o affinare? |
| **Q3** | hollow-monastery sub-classification: (A) `dungeon_3p T2 large-encounter` [53 items T2 · candidato dungeon canonico #61 alternativo] · (B) `secondary_source` generico [Q6 verbatim] · (C) split narrativo (raid alternate cancellato → dungeon)? |
| **Q4** | source_alias declassed token = **`void-heart-sanctum`** (8 items T5): conferma declass o preferisci sostituire con altro token (indicare quale) o accettare 61 dungeon canonici? |
| **Q5** | Class Slug Roadmap C5→R18.3f→R18.6: confermare timing (post-C6 closure → R18.3f readiness → R18.6 execute) o accelerare/ritardare? |
| **Q6** | Classless Start UX (Class Halls modal onboarding): approvare hook design R18.6 o richiede design PM dedicato? |
| **Q7** | Registry v2 post-C5 aggiungerà campi (`slot_canonical`, `slot_original`, `source_canonical`, `source_original`): timing per generation registry v2? (A) subito post-C5 approval · (B) in C6 Final Closure · (C) in R18.3f readiness |
| **Q8** | Autorizzare Phase C6 Final Phase C Closure Report (aggregate C0→C5 + handoff R18.3f/R18.6)? |


---

## Governance

| Voce | Stato |
|---|:--:|
| `sealed` | VERIFIED pytest 6/6 (post STEP 1 PRD append + STEP 2 C5 draft) |
| `db_writes` | ZERO |
| `code_changes` | ZERO |
| `migrations` | ZERO (design prep only) |
| `item_creation_live` | ZERO |
| `registry_apply` | ZERO |
| `drop_table_apply` | ZERO |
| `drop_rate_apply` | ZERO |
| `economy_changes` | ZERO |
| `lore_meta_py_touch` | ZERO |
| `sealed_file_modification` | ZERO |
| `hard_delete` | ZERO |
| `runtime_bridge` | ZERO |
| `class_slug_migration_apply` | ZERO (prep only) |
| `class_slug_auto_derivation` | ZERO |
| `slot_migration_apply` | ZERO (mapping design only) |
| `source_migration_apply` | ZERO (reconciliation design only) |
| `proficiency_runtime_enforcement` | ZERO |
| `anti_p2w_runtime_validator` | ZERO |
| `equipment_backfill_apply` | ZERO |
| `ilvl_implementation` | ZERO |
| `c6_auto_start` | BLOCKED (STOP after C5) |
| `r18_6_kickoff` | BLOCKED (PLANNED) |
| `marketing_brief` | BLOCKED (DEFERRED) |
| `classi_canoniche` | Warrior/Rogue/Mage/Priest/Ranger — NO drift |
| `italian_language_output` | ENFORCED |
| `documental_only_regime` | ENFORCED |
| `files_deliverable` | 2 (.md + .json) |


---

## Stop after C5

- **`auto_transition_c6`**: `false`
- **Nota**: **STOP dopo C5. Attendo PM review Q1-Q8 + GO esplicito prima di C6.**
