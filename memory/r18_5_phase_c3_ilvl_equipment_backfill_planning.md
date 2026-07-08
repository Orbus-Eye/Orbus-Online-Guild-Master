# R18.5 — Phase C3 · ILVL + Equipment Backfill Planning

**Round**: R18.5 · **Phase**: C3 ILVL + Equipment Backfill Planning
**Locked at UTC**: `2026-07-08T10:30:00Z`
**Governance**: **DOCUMENTAL ONLY — ILVL formula design + backfill plan design. NO backfill apply · NO ILVL implementation · NO migration · NO code · NO DB · NO drop table apply.**
**Status**: ✅ **APPLIED — planning documentale per PM review**
**Authority**: PM Orchestrator — Phase C3 dispatch (Q8=GO C3)
**Lingua output**: 🇮🇹 SOLO ITALIANO

**Deliverables**:
- `/app/memory/r18_5_phase_c3_ilvl_equipment_backfill_planning.md` (questo file)
- `/app/memory/r18_5_phase_c3_ilvl_equipment_backfill_planning.json` (SHA256 `87872f41360d7766e780007eb0bc90e4fe217d8176925e5adf3f86f461567aeb`)

**Hard constraints (verbatim PM)**:
- `MAX_ADVENTURER_LEVEL = 60`
- `MAX_EQUIPMENT_REQUIRED_LEVEL = 60`
- `no_levels_beyond_60`: **True**
- `post_lv60_progression`: ILVL · rarity · utility · raid endgame source · optimization · market/ranking relevance

---

## 1. Executive Summary

Definire in modalità solo-documentale la formula ILVL canonica, i bracket level→ilvl, i modifier di rarity, il trattamento Legendary, e il piano di backfill per campi equipment (armor_type, weapon_family, slot, required_level, ilvl, tier, rarity, main_stat_target, class_proficiency, runtime_apply_ready). NESSUNA implementazione, NESSUN backfill apply, NESSUNA migrazione.

**Scope in** (15 topics):
- ILVL formula design (data-driven da osservazione D1-D5)
- level → ilvl bracket mapping Lv1-60
- tier → ilvl range mapping T1-T5
- rarity modifier design (Common/Uncommon/Rare/Epic/Legendary)
- Legendary ILVL treatment (cap 60 endgame)
- equipment backfill plan per 10 campi
- existing live item compatibility plan (legacy items)
- min_level vs required_level normalization plan
- slot_type / item_type fallback handling
- adventurer equipment migration readiness (design only)
- class_slug=null interaction (compat C2 verbatim)
- no-apply validation checklist
- risk register
- GO/HOLD recommendation for C4
- PM open questions (8)

**Scope out** (deferito):
- Backfill apply (deferred a phase runtime enablement futura)
- ILVL implementation (out-of-scope)
- Migrazione live item / DB writes
- Drop table apply (C4)
- Class slug migration apply (C5)
- Anti-P2W runtime validator implementation

**Invarianti preservati** (nessuna modifica ammessa in C3):

- **item_count_total**: 1500
- **rarity_distribution**: {"Common": 400, "Uncommon": 450, "Rare": 400, "Epic": 235, "Legendary": 15}
- **class_distribution**: {"Warrior": 300, "Rogue": 300, "Mage": 300, "Priest": 300, "Ranger": 300}
- **tier_ranges**: {"T1": "Lv1-15", "T2": "Lv16-30", "T3": "Lv31-45", "T4": "Lv46-55", "T5": "Lv56-60"}
- **NO modifications to**: item count, rarity, tier, class distribution, stat, naming, source, proficiency, anti-P2W


---

## 2. ILVL Formula Design

**Principio**: Formula design-layer (NON implementazione). Deriva ILVL da (tier, required_level, rarity) con cap endgame 60.

**Formula canonica (pseudo-logica)**:

```
ilvl(item) = min( max( required_level + rarity_offset[rarity], tier_min[tier] ), MAX_EQUIPMENT_REQUIRED_LEVEL )
```

**Costanti**:

| Costante | Valore |
|---|---|
| `tier_min` | T1=1 · T2=16 · T3=31 · T4=46 · T5=56 |
| `tier_max` | T1=15 · T2=30 · T3=45 · T4=55 · T5=60 |
| `rarity_offset` | Common=0 · Uncommon=+2 · Rare=+3 · Epic=+4 · Legendary=+5 |
| `MAX_EQUIPMENT_REQUIRED_LEVEL` | 60 |
| `legendary_ilvl_flat_cap` | 60 |

**Rationale data-driven**:

Rarity offset derivati dall'osservazione delle mediane ILVL per (tier, rarity) sui 1500 items D1-D5: il gap fra ilvl_med e required_level_med aumenta con la rarità. Legendary hanno ilvl=60 fisso (osservato 15/15 = 60). Il min(..., 60) garantisce il cap gameplay. Il max(..., tier_min) garantisce che nessun item di tier alto scenda sotto la soglia del tier.

**Nota governance**:

Formula usata SOLO per backfill design layer di eventuali item legacy o futuri. I 1500 items del catalogo D1-D5 hanno GIÀ ilvl valorizzato (0 missing) e NON devono essere modificati.

---

## 3. Level → ILVL Bracket Mapping (Lv1-60)

_Mapping bracket Lv → ilvl range aspettato (design layer). Coerente con tier_ranges._

| lv_range | tier | ilvl Common | ilvl Uncommon | ilvl Rare | ilvl Epic | ilvl Legendary |
|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **Lv1-5** | T1 | 1-5 | 3-7 | n/a | n/a | n/a |
| **Lv6-10** | T1 | 6-10 | 8-12 | n/a | n/a | n/a |
| **Lv11-15** | T1 | 9-15 | 13-15 | n/a | n/a | n/a |
| **Lv16-20** | T2 | 16-20 | 18-22 | n/a | n/a | n/a |
| **Lv21-25** | T2 | 21-25 | 23-27 | n/a | n/a | n/a |
| **Lv26-30** | T2 | 26-30 | 28-30 | 29-30 | n/a | n/a |
| **Lv31-35** | T3 | 31-35 | 33-37 | 34-38 | 35-39 | n/a |
| **Lv36-40** | T3 | 36-40 | 38-42 | 39-43 | 40-44 | n/a |
| **Lv41-45** | T3 | n/a | 43-45 | 44-45 | 45 | n/a |
| **Lv46-50** | T4 | n/a | 48-52 | 49-53 | 50-54 | n/a |
| **Lv51-55** | T4 | n/a | 53-55 | 54-55 | 55 | n/a |
| **Lv56-59** | T5 | n/a | n/a | 58-60 | 59-60 | 60 |
| **Lv60** | T5 | n/a | n/a | 60 | 60 | 60 |


**Post-Lv60**: Nessun item con required_level > 60. Post-Lv60 progression = ILVL/rarity/utility/raid endgame/optimization/market/ranking.

---

## 4. Tier → ILVL Range Mapping (T1-T5)

### Validation from observed D1-D5 (1500 items)

| tier · rarity | n | ilvl min | ilvl med | ilvl max |
|---|:--:|:--:|:--:|:--:|
| **T1 · Common** | 220 | 1 | 5 | 9 |
| **T1 · Uncommon** | 80 | 3 | 10 | 15 |
| **T2 · Common** | 150 | 16 | 19 | 25 |
| **T2 · Uncommon** | 150 | 20 | 26 | 30 |
| **T2 · Rare** | 50 | 26 | 29 | 30 |
| **T3 · Common** | 30 | 31 | 33 | 36 |
| **T3 · Uncommon** | 160 | 32 | 36 | 45 |
| **T3 · Rare** | 130 | 32 | 40 | 45 |
| **T3 · Epic** | 30 | 33 | 42 | 45 |
| **T4 · Uncommon** | 60 | 46 | 50 | 54 |
| **T4 · Rare** | 150 | 46 | 50 | 54 |
| **T4 · Epic** | 90 | 46 | 52 | 55 |
| **T5 · Rare** | 70 | 56 | 58 | 60 |
| **T5 · Epic** | 115 | 56 | 59 | 60 |
| **T5 · Legendary** | 15 | 60 | 60 | 60 |

### Target backfill ranges (design layer, per futuri backfill legacy/nuovi item)

| tier | Common | Uncommon | Rare | Epic | Legendary |
|:--:|:--:|:--:|:--:|:--:|:--:|
| **T1** | 1-15 | 3-15 | — | — | — |
| **T2** | 16-30 | 20-30 | 26-30 | — | — |
| **T3** | 31-36 | 32-45 | 32-45 | 33-45 | — |
| **T4** | — | 46-54 | 46-55 | 46-55 | — |
| **T5** | — | — | 56-60 | 56-60 | 60 |


_Le rarity distribution per tier NON contengono tutti i buckets: es. T1 non ha Rare/Epic/Legendary; T4 non ha Common; T5 non ha Common/Uncommon. Questa asimmetria è VOLUTA da design (progressione tier). Backfill design mantiene questa asimmetria._

---

## 5. Rarity Modifiers

**Principio**: rarity_offset applicato in formula ilvl. Il gap ilvl vs required_level aumenta con la rarità.

| rarity | offset | note |
|---|:--:|---|
| **Common** | +0 | ilvl ≈ required_level; nessun bonus |
| **Uncommon** | +2 | ilvl leggermente sopra required_level (osservato med +2) |
| **Rare** | +3 | gap moderato (osservato med +3 vs required_level) |
| **Epic** | +4 | gap elevato (osservato med +4) |
| **Legendary** | +5 | gap max, ma cap flat 60 endgame (osservato ilvl=60 15/15) |


**Governance**: rarity_offset è design layer per BACKFILL FUTURI o normalizzazione LEGACY items. I 1500 D1-D5 sono già coerenti (0 items missing_ilvl).

---

## 6. Legendary ILVL Rules

- **Regola 1**: TUTTI i 15 Legendary hanno ilvl=60 (cap endgame, osservato 15/15).
- **Regola 2**: Il flat cap 60 vale sia per 11 design-ready (7 approved + 4 hybrid) sia per 4 progressive placeholder (P1-P4).
- **Regola 3**: Progressive placeholder P1-P4 mantengono ilvl=60 solo come design placeholder — restano `registry_status=reserved` e `runtime_apply_ready=false`.
- **Regola 4**: Nessun item non-Legendary può avere ilvl > 60 (violation → HARD BLOCK design).
- **Regola 5**: Nessuna promozione automatica a Legendary basata su ilvl (rarity resta invariante).

_Coerenza C0.L.1_: C0.L.1 numeric finals confermano ilvl=60 per 11 design-ready + 4 progressive reserved (tutti 15/15).

---

## 7. Equipment Backfill Plan (10 campi target)

**Principio**: Piano documentale per backfill futuro di 10 campi. NESSUN apply, NESSUNA migrazione, NESSUN DB write. Il catalogo D1-D5 attuale è già completo.

| # | field | backfill_source_logic | current D1-D5 coverage |
|:--:|---|---|---|
| 1 | `armor_type` | match slot in {head/chest/legs/feet/hands/shoulder/waist/wrist} + class_proficiency → armor whitelist C2 | 1500/1500 present (o `null` per weapon slots) |
| 2 | `weapon_family` | match slot in {main-hand/off-hand/two-hand} + class_proficiency → weapon whitelist C2 | 1500/1500 present (o `null` per armor/trinket slots) |
| 3 | `slot` | must be in canonical list: head, chest, legs, feet, hands, shoulder, waist, wrist, neck, ring, trinket, main-hand, off-hand, two-hand | 1500/1500 present |
| 4 | `required_level` | tier → tier_range Lv (T1=1-15, T2=16-30, ...); item-specific interpolation optional | 1500/1500 present |
| 5 | `ilvl` | ilvl_formula = min(max(required_level + rarity_offset[rarity], tier_min[tier]), 60) | 1500/1500 present (0 missing) |
| 6 | `tier` | derive from required_level: 1-15→T1, 16-30→T2, 31-45→T3, 46-55→T4, 56-60→T5 | 1500/1500 present |
| 7 | `rarity` | NO auto-derive; rarity è invariante di design (400/450/400/235/15) | 1500/1500 present |
| 8 | `main_stat_target` | derive from class_proficiency: Warrior→STR, Rogue→AGI, Mage→INT, Priest→WIS, Ranger→AGI; eccezione 13 Warrior gear END-based (documented E1) | 1500/1500 present |
| 9 | `class_proficiency` | renamed from `classe_orientata` in C1 registry; canonical W/R/M/P/Ranger | 1500/1500 present (source_field=classe_orientata) |
| 10 | `runtime_apply_ready` | false 1500/1500 nel dry-run corrente; true solo post runtime enablement pipeline (out-of-scope C3) | 1500/1500 = false (dry-run) |


**No-apply governance**: TUTTO documentale. Il backfill APPLY sarà oggetto di gate futuro (post-Phase C completion + PM approval).

---

## 8. Legacy Item Compatibility (10 cases)

**Principio**: Analisi di compat per item LIVE ESISTENTI in DB (legacy pre-R18.5). Solo design piano, no apply, no rottura inventari.

| # | case | handling |
|:--:|---|---|
| 1 | legacy item senza `ilvl` | Backfill formula sezione 2. Fallback: `ilvl = required_level + 2` (safe default Uncommon-tier). NO overwrite se ilvl è già valorizzato. |
| 2 | legacy item senza `armor_type` o `weapon_family` | Derive from `slot` + `class_proficiency` C2 whitelist. Se ambiguità: mark `armor_type=UNKNOWN` (lock_state=`locked_unknown_item_type` C2). NO auto-guess. |
| 3 | `min_level` vs `required_level` | Normalize: `required_level = coalesce(required_level, min_level, 1)`. Preferenza campo canonical = `required_level`. NO drop di `min_level` (backwards-compat). |
| 4 | legacy item senza `slot_type` (solo `slot`) | slot_type = derive category (armor/weapon/trinket/consumable/material). NO renaming di slot esistente. |
| 5 | legacy item con `item_type` mancante | item_type fallback: derive from (slot, weapon_family, armor_type). Se tutto null → `item_type=UNKNOWN` (lock_state=`locked_unknown_item_type`). |
| 6 | legacy item con rarity non-canonical (es. 'legendary' lowercase) | Case-insensitive normalization → canonical form (`Legendary` capitalized). NO auto-promotion, NO auto-demotion. |
| 7 | legacy item nel roster inventario avventurieri | Backfill leggibile-only. Inventario esistente NON viene svuotato né riorganizzato. Ogni item ottiene ilvl/tier/rarity backfill in-place documentale. |
| 8 | legacy item premium/shop (se esistente) | Anti-P2W verification: se `can_be_sold_for_real_money=true` legacy → mark `p2w_legacy_flag=true` per audit; NO auto-conversion. PM review richiesta. |
| 9 | legacy item con class_proficiency lowercase o non-canonical | Case-insensitive normalization → Warrior/Rogue/Mage/Priest/Ranger canonical. NO drift, NO nuove classi (R10 rischio C2 tracked). |
| 10 | legacy item con `slot=universal` | lock_state=`universal_allowed` (bypass proficiency check C2). Include consumable/material/cosmetic. |


**Backwards-compat**: TUTTI i legacy items rimangono nell'inventario. Il backfill è additivo (fields aggiunti/normalizzati), NON distruttivo.

---

## 9. class_slug=null Interaction (compat C2)

### Regole C2 verbatim (immutate)
- class_slug=null NON auto-derivato (rule PM Q7=CONFIRMED)
- NO runtime bridge · NO migration · NO apply
- risoluzione differita a C5 (Class Slug Migration Prep / R18.3f Readiness) + R18.6 (Class Halls · Classless Start)

### Impatto su C3
- Items possono ricevere ILVL documentale (ilvl è indipendente da class_slug)
- Backfill ilvl NON richiede class_slug
- Avventurieri con class_slug=null restano `locked_recruit_unassigned` o `locked_class_slug_null` (C2) → non equip-ready per gear specializzato
- Backfill di `class_proficiency` sui items resta canonical W/R/M/P/Ranger (indipendente dalla migrazione slug lato adventurer)


**Current state**:
- `class_slug_null_1500_1500`: True
- `class_slug_resolution_status`: `deferred_to_C5_R18_3f`
- `adventurer_side_handling`: documentato in C2, risoluzione live in R18.6

---

## 10. Slot / item_type Fallback Handling

**Canonical slots (14)**:

`head` · `chest` · `legs` · `feet` · `hands` · `shoulder` · `waist` · `wrist` · `neck` · `ring` · `trinket` · `main-hand` · `off-hand` · `two-hand`

**Canonical item_types (7)**:

`armor` · `weapon` · `trinket` · `accessory` · `consumable` · `material` · `cosmetic`

**Fallback priority order**:
- 1. slot canonical valido → item_type derived
- 2. slot + weapon_family present → item_type=weapon
- 3. slot + armor_type present → item_type=armor
- 4. slot in {neck, ring, trinket} + no weapon/armor → item_type=trinket/accessory
- 5. no slot / null → item_type=UNKNOWN (lock_state=`locked_unknown_item_type`)


_consumable/material/cosmetic bypass proficiency check (lock_state=`universal_allowed` C2)_

---

## 11. Adventurer Equipment Migration Readiness (design only)

**Principio**: Design layer per la futura migrazione runtime. Nessuna implementazione in C3.

| adventurer_state | equipment_backfill_readiness |
|---|---|
| class_slug valido + level valid + inventory populated | **READY (nominal path)** |
| class_slug=null + class_proficiency canonical | **PARTIAL — items ricevono backfill; avventuriero non equip finché class_slug non risolto (C5/R18.3f)** |
| recruit_unassigned (no classe) | **BLOCKED — deve completare Class Halls R18.6 prima di equip-ready** |
| legacy senza required_level valorizzato | **PARTIAL — default level=1; PM review case-by-case** |
| inventory con legacy item p2w flag | **AUDIT — mark p2w_legacy_flag=true; PM review** |


_TUTTA la migrazione è deferita a phase runtime enablement post-C6. C3 documenta solo le rotte._

---

## 12. No-Apply Validation Checklist (15 check)

| # | check | status |
|:--:|---|:--:|
| **1** | ILVL formula design layer only | PASSED — formula documentale, nessun apply |
| **2** | Rarity distribution 400/450/400/235/15 preservata | PASSED — no modifiche |
| **3** | Class distribution 300×5 preservata | PASSED |
| **4** | Tier ranges T1-T5 preservati | PASSED |
| **5** | MAX_ADVENTURER_LEVEL=60 rispettato | PASSED — no items con required_level > 60 |
| **6** | MAX_EQUIPMENT_REQUIRED_LEVEL=60 rispettato | PASSED |
| **7** | Legendary ilvl flat cap 60 | PASSED — osservato 15/15 = 60 |
| **8** | 0 items D1-D5 modificati | PASSED — read-only |
| **9** | class_slug=null 1500/1500 preservato | PASSED — Q7 CONFIRMED |
| **10** | runtime_apply_ready=false 1500/1500 preservato | PASSED — dry-run |
| **11** | progressive_marker count=10 preservato | PASSED — Q4=B C1 |
| **12** | Anti-P2W 1500/1500 preservato | PASSED |
| **13** | 36 seals byte-identical | TO VERIFY post-write (pytest) |
| **14** | lore_meta.py invariato | PASSED — no touch |
| **15** | Zero DB/code/migrations | PASSED — DOCUMENTAL ONLY |


---

## 13. Risk Register

| ID | Rischio | Severità | Mitigazione | Status |
|:--:|---|:--:|---|:--:|
| **R1** | ILVL formula backfill non deterministico su legacy items con dati partial | MEDIUM | fallback safe: ilvl = required_level + 2; NO overwrite se già presente | DESIGNED |
| **R2** | Legacy item senza class_proficiency canonical (drift lowercase o custom) | MEDIUM | case-insensitive normalization + audit report pre-apply futuro | DESIGNED |
| **R3** | min_level vs required_level conflict in legacy items | LOW-MEDIUM | coalesce(required_level, min_level, 1); preserve min_level as backwards-compat | DESIGNED |
| **R4** | Legendary progressive placeholder P1-P4 riceve ilvl backfill prematurely | MEDIUM | flat ilvl=60 (documentale placeholder) MA registry_status=reserved + runtime_apply_ready=false; NO promotion | DESIGNED |
| **R5** | T4 progressive_marker (10 items) confusi con Legendary durante backfill | LOW | progressive_marker=true flag preservato; rarity=Epic invariato; NO promozione | DESIGNED |
| **R6** | Legacy inventario avventurieri rotto da backfill (data-loss) | HIGH-BLOCK | backfill = ADDITIVO, NON DISTRUTTIVO; PM review pre-apply obbligatoria futura | DESIGNED |
| **R7** | Anti-P2W legacy flag missed durante backfill (item premium residuo) | HIGH-BLOCK | audit obbligatorio p2w_legacy_flag=true pre-apply; PM review case-by-case | DESIGNED |
| **R8** | class_slug=null interazione con adventurer inventory backfill | MEDIUM (C2 tracked) | class_slug=null NON blocca ilvl backfill sui items; blocca equip-readiness lato adventurer (C2 lock_state) | DESIGNED |
| **R9** | HYBRID drop rate 0.5% direzionale scambiato per finale durante backfill drop_table_ref | MEDIUM | drop_table_ref è REF (source token) non drop_rate; drop_rate PM final richiesto in C4 | TRACKED to C4 |
| **R10** | Slot canonical mismatch (es. 'main_hand' vs 'main-hand' vs 'mainhand') | MEDIUM | canonical list `main-hand`/`off-hand`/`two-hand`; normalization case-insensitive + separator-agnostic in audit | DESIGNED |
| **R11** | Post-Lv60 progression flow non chiaro senza raid endgame source cross-check | LOW-MEDIUM | post-Lv60 progression = ILVL/rarity/utility/raid endgame source/optimization/market-ranking (cross-check con matrix Batch 1-5 in C4) | TRACKED |
| **R12** | Backfill item_type UNKNOWN residuo dopo fallback | LOW | lock_state=`locked_unknown_item_type` C2 (safety net); PM review pre-apply | DESIGNED |


---

## 14. GO/HOLD Recommendation

### Phase C4 Drop Table
- **Recommendation**: **GO — soggetto a PM approval esplicito post-C3 review**
- **Rationale**: C3 ILVL + backfill plan fornisce input coerente per C4 Drop Table (drop_table_ref già mappato in C1). C4 dovrà finalizzare i drop_rate HYBRID (0.5% direzionale) e cross-checkare con matrix Batch 1-5.

**Conditions richieste**:
- PM approval C3 (Q1-Q8)
- HYBRID drop_rate PM final decision (0.5% direzionale confermato o differenziato)
- Legendary drop rate approved 7 confermati (2% raid / 1% dungeon 3p, chain STEP 8)
- Progressive drop rate 4 (P1-P4) restano PENDING PM oppure finalizzati in C4 mini-gate

**Risks se GO**:
- R9 HYBRID drop_rate confusion → mitigato via ref token vs rate numeric
- R11 post-Lv60 progression flow → mitigato via cross-check matrix in C4


### Fasi successive (HOLD)
- **C5 Class Slug Migration Prep** — HOLD post-C4 · class_slug null resolution formalizzata qui (C2 rule + Q7 CONFIRMED)
- **C6 Final Closure** — HOLD post-C5
- **R18.6 Class Halls / Classless Start** — PLANNED post-Phase C · recruit_unassigned + Class Halls implementation

---

## 15. PM Open Questions post-C3

| ID | Topic |
|:--:|---|
| **Q1** | Approvare C3 ILVL formula design (min(max(required_level + rarity_offset, tier_min), 60)) come baseline documentale? |
| **Q2** | Rarity offset proposti (Common:0 · Uncommon:+2 · Rare:+3 · Epic:+4 · Legendary:+5 con cap 60): accettare o affinare? |
| **Q3** | Legendary ilvl flat cap 60 (osservato 15/15): confermare per progressive placeholder P1-P4 anche a livello documentale? |
| **Q4** | Backfill formula fallback per legacy items senza ilvl: `ilvl = required_level + 2` (safe Uncommon default) — accettare o preferire fallback diverso? |
| **Q5** | Legacy items premium/p2w flag: `p2w_legacy_flag=true` per audit (NO auto-conversion) — confermare policy PM review case-by-case? |
| **Q6** | min_level vs required_level normalization: coalesce(required_level, min_level, 1) — preferenza campo canonical = `required_level`. Confermare? |
| **Q7** | Slot canonical list (14 slots: head/chest/legs/feet/hands/shoulder/waist/wrist/neck/ring/trinket/main-hand/off-hand/two-hand): completa o richiede aggiunte (es. `back` per cloak, `belt` separato da waist)? |
| **Q8** | Autorizzare Phase C4 Drop Table con condizioni GO documentate in `go_hold_recommendation.phase_c4_drop_table`? |


---

## 16. Governance Check C3

| Voce | Stato |
|---|:--:|
| `sealed` | VERIFIED pytest 6/6 (post STEP 1 PRD append + STEP 2 C3 draft) |
| `db_writes` | ZERO |
| `code_changes` | ZERO |
| `migrations` | ZERO |
| `item_creation_live` | ZERO |
| `registry_apply` | ZERO |
| `registry_generation_live` | ZERO |
| `drop_table_apply` | ZERO |
| `economy_changes` | ZERO |
| `lore_meta_py_touch` | ZERO (invariato) |
| `sealed_file_modification` | ZERO |
| `hard_delete` | ZERO |
| `runtime_bridge` | ZERO |
| `class_slug_migration_apply` | ZERO |
| `class_slug_auto_derivation` | ZERO (Q7 CONFIRMED verbatim) |
| `proficiency_runtime_enforcement_implementation` | ZERO (design only) |
| `anti_p2w_runtime_validator_implementation` | ZERO (design only) |
| `equipment_backfill_apply` | ZERO (design plan only) |
| `ilvl_implementation` | ZERO (formula design only) |
| `c4_auto_start` | BLOCKED (STOP after C3 per direttiva PM) |
| `r18_6_kickoff` | BLOCKED (PLANNED) |
| `marketing_brief` | BLOCKED (DEFERRED) |
| `classi_canoniche` | Warrior/Rogue/Mage/Priest/Ranger — NO drift |
| `italian_language_output` | ENFORCED |
| `documental_only_regime` | ENFORCED |
| `files_deliverable` | 2 (.md + .json) |
| `invariants_preserved_count` | {"rarity_400_450_400_235_15": true, "class_300x5": true, "tier_ranges_T1_T5": true, "MAX_ADVENTURER_LEVEL_60": true, "class_slug_null_1500": true, "runtime_apply_ready_0_1500": true, "progressive_marker_10": true, "anti_p2w_1500_1500": true} |


---

## Stop after C3

- **`auto_transition_c4`**: `false`
- **Nota**: **STOP dopo C3. Attendo PM review Q1-Q8 + GO esplicito prima di C4 Drop Table.**
