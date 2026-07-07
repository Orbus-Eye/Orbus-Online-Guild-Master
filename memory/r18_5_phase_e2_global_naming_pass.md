# R18.5 — Phase E2 · Global Naming Pass (STEP 23)

**Round**: R18.5 — Itemization, ILVL & Gear Progression Rework
**Phase**: E2 — Global Naming Pass (post-E1 CLOSED)
**STEP**: 23
**Locked at UTC**: `2026-07-07T18:45:00Z`
**Governance**: **DOCUMENTAL ONLY — MICRO-ECCEZIONE AUTORIZZATA PM** su file item table D1-D5 (`.json`) SOLO per naming fixes (armor_type EN→IT). NO stat/balance changes (unless typo-only, documentati).
**Status**: ✅ **APPLIED**
**Authority**: PM Orchestrator — STEP 23 catena autorizzata post-STEP 22 E1 CLOSED

**Deliverables**:
- `/app/memory/r18_5_phase_e2_global_naming_pass.md` (questo file)
- `/app/memory/r18_5_phase_e2_global_naming_pass.json` (552 righe · SHA256 `d398df4c8b1819f23918c4c2e55a4f889fe502890614cdb18e0dc59a54f42337`)

---

## Sezione 1 — Naming drift EN→IT fixes (151 items bulk-normalized)

**Mapping design intent applicato**:

| EN generic | IT-specific | Classi coinvolte |
|---|---|---|
| `heavy` | **`piastre`** | Warrior |
| `medium` | **`maglia`** | Warrior, Ranger |
| `light` | **`cuoio`** | Rogue, Ranger |
| `light` | **`stoffa`** | Mage, Priest (nessun caso — light era solo Rogue/Ranger) |

### 1.1 Distribuzione fixes per classe

| Fix | Count | %151 |
|---|:---:|:---:|
| `heavy` Warrior → `piastre` | **38** | 25.2% |
| `medium` Warrior → `maglia` | **17** | 11.3% |
| `medium` Ranger → `maglia` | **35** | 23.2% |
| `light` Rogue → `cuoio` | **50** | 33.1% |
| `light` Ranger → `cuoio` | **11** | 7.3% |
| **TOTALE** | **151** | 100% ✅ |

### 1.2 Distribuzione armor_type post-E2 (cumulative 1500)

| armor_type | Count | Change from pre-E2 |
|---|:---:|:---:|
| `stoffa` | 208 | invariato (Mage/Priest) |
| `cuoio` | **152** | +61 (91→152 da light Rogue+Ranger) |
| `maglia` | **100** | +52 (48→100 da medium Warrior+Ranger) |
| `piastre` | **88** | +38 (50→88 da heavy Warrior) |
| **TOTALE** | **548** | items con armor_type (weapons/trinket/ring/amulet non hanno armor_type) |

**Verifica finale**: **0 items** rimasti con armor_type `heavy`/`medium`/`light` ✅. Distribution completa in JSON `sezione_1_naming_drift_en_it_fixes.distribution_after_e2`.

**Governance**: bulk fix deterministico. Design intent preserved (Warrior heavy=piastre, Warrior medium=maglia, Ranger medium=maglia, Rogue light=cuoio, Ranger light=cuoio). Nessuna decisione creativa autonoma.

---

## Sezione 2 — Slug consistency fixes

### 2.1 Slug drift post-E1.1 (4 items HIGH fix)

Post-STEP 21 (E1.1), 4 items HIGH hanno weapon_family cambiato ma `item_id` preservato per tracking:

| item_id | weapon_family attuale | Slug drift | Resolution |
|---|:---:|---|---|
| `priest-blessed-dagger` | reliquia | item_id contains 'dagger' | **OPTION A (leave as-is)** — governance preservation tracking |
| `priest-blessed-dagger-t2` | reliquia | item_id contains 'dagger' | **OPTION A** |
| `rogue-soulforged-shortbow` | balestra | item_id contains 'shortbow' | **OPTION A** |
| `rogue-soulforged-shortbow-master` | balestra | item_id contains 'shortbow' | **OPTION A** |

**Governance verbatim**: item_id preservati per tracking cross-tier (Option A). Slug naming drift documentato per PM Q2 gate. Se PM autorizza rinomina in Phase C tech gate → Option B (breaks tracking).

### 2.2 D4 slug drift (9 dungeon, accepted D4 CLOSED)

9 slug drift D4 documentati in STEP 17 (D4 CLOSED). Governance: accettato PM in D4 closure, deferred a naming pass post-D5. **Nessun rework in E2 su slug D4** (governance preservation, Q3 gate PM).

---

## Sezione 3 — Naming IT consistency fixes

**Verifica**: nomi IT già consistenti in italiano — es. "Corazza a Piastre del Novizio" · "Mantello di Cuoio Grezzo" · "Veste Arcana del Novizio" · "Corpetto di Cuoio dello Scout" · "Vesti Sacre del Novizio". Il naming drift era **solo nel campo `armor_type`**, non nei nomi IT.

**Typo-only stat fixes applicati in E2**: **0** (nessun typo evidente rilevato in scan bulk). Se PM ha riferimenti specifici, Q per iterazione E2.1.

**Status Sezione 3**: ✅ PASSED — nomi IT già consistenti, no rework necessario.

---

## Sezione 4 — Family naming consistency (iconic_family cross-tier)

**Iconic families cumulative** verificate. Cumulative ridondanze T4/T5 documentate in D5 Sezione 14 e E1 risk_6:
- `dragonhunter-endgame` · `elder-wyrm-hunter` · `elder-wyrm-stalker` (Draco endgame)
- `ambash-forge-warrior` · `ambash-arcane-forge` (Ambash endgame)
- `alevoran-perpetual` (Alevora endgame)
- `emberking-endgame` · `efreto-corrupt-caster` · `efreto-purger` · `efreto-cursed-ranger` (Infernale endgame)
- `adalan-arcane-thief` · `adalan-archmage-t5` (Adalan endgame)

**Governance E2**: iconic families cross-tier verificate. Nessuna rework autonoma (richiederebbe decisione creativa PM). Q4 gate PM per autorizzazione E2.1 rework.

---

## Sezione 5 — Duplicate/near-duplicate resolution

**Duplicate `nome_it` rilevati**: **14** (details in JSON `sezione_5_duplicate_near_duplicate_resolution.duplicates_detail`).

**Governance**: duplicate documentati per PM decision. Rename autonomo richiederebbe decisione creativa → **PENDING PM** (backlog E2.1 se richiesto, o Phase C tech gate).

---

## Sezione 6 — Legendary naming review (15/15)

| Verify | Valore | Status |
|---|:---:|:---:|
| Total Legendary | **15 / 15** | ✅ EXACT |
| Nomi IT memorabili + lore forte | 11 approved+hybrid | ✅ |
| PENDING PM placeholder markers esplicit | 4 progressive (P1-P4) | ✅ |

**Naming Legendary review**: 15 nomi IT verified memorabili e coerenti con lore forte. I 4 progressive placeholders (`progressive-slot-01-pending` fino a `progressive-slot-04-pending`) sono esplicitamente marcati `PENDING PM` sia nel nome che nel `chain_tag`.

Dettaglio completo dei 15 nomi in JSON `sezione_6_legendary_naming_review_15_15.names_15`.

---

## Sezione 7 — NPC naming cross-tier consistency

**5 NPC LOCKED slug + IT names verified consistent cross-tier D1-D5**:

| NPC slug | IT name | T1 | T2 | T3 | T4 | T5 | Totale |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `fabbro-bulwark` | Fabbro Bulwark | 0 | 0 | 15 | 4 | 4 | 23 |
| `cuoiaia-elfwood` | Cuoiaia Elfwood | 0 | 0 | 8 | 5 | 4 | 17 |
| `sarto-sacro` | Sarto Sacro | 0 | 0 | 13 | 4 | 4 | 21 |
| `tessitrice-arcana` | Tessitrice Arcana | 0 | 0 | 12 | 5 | 4 | 21 |
| `conciatore-elfwood` | Conciatore Elfwood | 0 | 0 | 16 | 6 | 4 | 26 |
| **TOTALE** | | 0 | 0 | 64 | 24 | 20 | **108** |

**Governance E2**: NO autonomous new NPC. Slug + IT names verified consistent cross-tier T3-T5 (T1-T2 no craft NPC come da blueprint D0).

**Status Sezione 7**: ✅ PASSED — 5 NPC LOCKED consistent cross-tier.

---

## Sezione 8 — Typo-only stat fixes

**Applicati in E2**: **0**.

Nessun typo evidente rilevato in scan bulk stat_principali. **NO stat changes applicati in E2** (governance verbatim PM: solo naming, no balance).

Se PM ha riferimenti specifici a typo residui, Q per iterazione E2.1.

---

## Sezione 9 — Item count post-fix

| Vista | Valore |
|---|:---:|
| Totale items | **1500 / 1500** ✅ EXACT |
| D1 items | 300 |
| D2 items | 350 |
| D3 items | 350 |
| D4 items | 300 |
| D5 items | 200 |

Nessun item creato / cancellato / duplicato.

---

## Sezione 10 — Rarity post-fix

| Rarity | Count | Target | Status |
|---|:---:|:---:|:---:|
| Common | 400 | 400 | ✅ EXACT |
| Uncommon | 450 | 450 | ✅ EXACT |
| Rare | 400 | 400 | ✅ EXACT |
| Epic | 235 | 235 | ✅ EXACT |
| Legendary | 15 | 15 | ✅ EXACT |
| **TOTALE** | **1500** | **1500** | ✅ **EXACT 400/450/400/235/15** |

Rarity 100% preservato (E2 naming-only, no rarity changes).

---

## Sezione 11 — Class distribution post-fix

| Classe | Count | Target | Status |
|---|:---:|:---:|:---:|
| Warrior | 300 | 300 | ✅ EXACT |
| Rogue | 300 | 300 | ✅ EXACT |
| Mage | 300 | 300 | ✅ EXACT |
| Priest | 300 | 300 | ✅ EXACT |
| Ranger | 300 | 300 | ✅ EXACT |
| **TOTALE** | **1500** | **1500** | ✅ **EXACT 300×5** |

Class distribution 100% preservata.

---

## Sezione 12 — SHA256 file modificati

| File | Modified | SHA256 pre-E2 | SHA256 post-E2 finale |
|---|:---:|---|---|
| D1 `.json` | ✅ YES | `6058ae78b337c596...` | **`e529922a510d9ec43af2f6d12b9404626f06ae85f9916712931c0131eeae984b`** |
| D2 `.json` | ✅ YES | `e246f2773b858477...` | **`e647a0babcd7f884794920be68895d8bc702b639d4f21e799cef0e20cc6d7069`** |
| D3 `.json` | ❌ NO | `b478ae641eec3f33...` | `b478ae641eec3f33e440cfec80a2e52da4a81c8fd76b7df9594234be09644d44` (unchanged, E1.1 finale) |
| D4 `.json` | ❌ NO | `6d42a01983d6bcf3...` | `6d42a01983d6bcf37354f2b5ba99cff6a2b4d8b2c272819907a57dbfe9455acb` (unchanged, E1.1 finale) |
| D5 `.json` | ❌ NO | `58e9f0ea86f7fb5e...` | `58e9f0ea86f7fb5eeaf00c53728fe15c4f4a40041c98e2639a339b873069ae6e` (unchanged, D5 STEP 18) |

**Nota**: D3/D4 avevano già naming IT-specific (no drift EN generic). D5 aveva già naming IT-specific dal Design (STEP 18). Solo D1 e D2 richiedevano bulk fix EN→IT.

---

## Sezione 13 — Sealed integrity result

**pytest** `backend/tests/backend_r18_4_sealed_integrity_test.py` post-write E2:

```
2 workers [6 items]
......                                                                   [100%]
============================== 6 passed in 0.44s ==============================
```

✅ **36 sigilli byte-identical VERIFIED** (pytest 6/6 PASSED).

---

## Sezione 14 — `git status`

```
 M memory/PRD.md                                            (STEP 19+22 append)
 M memory/r18_5_phase_d1_t1_item_table.json                  (E1.1 + E2 naming)
 M memory/r18_5_phase_d2_t2_item_table.json                  (E1.1 + E2 naming)
 M memory/r18_5_phase_d3_t3_item_table.json                  (E1.1 HIGH#3-4 + MEDIUM#4, M6-M16)
 M memory/r18_5_phase_d4_t4_item_table.json                  (E1.1 MEDIUM#5)
?? memory/r18_5_phase_e1_1_balance_remediation_patch.md/.json  (STEP 21)
?? memory/r18_5_phase_e2_global_naming_pass.md/.json           (STEP 23 nuovo)
```

**Nessun sealed file toccato · nessun `.py`/`.js`/`.jsx`/`.tsx`/`.ts` modificato · `lore_meta.py` invariato SHA256 `a18f708b...`**.

---

## Sezione 15 — PM Open Questions post-E2 per gate Phase C Tech Dry-Run

| ID | Topic |
|---|---|
| **Q1** | Approvare **E2 CLOSED** (151 armor naming drift EN→IT fixed, 0 stat changes, 0 typo, 1500/1500 preserved)? |
| **Q2** | Approvare **slug preservation post-E1.1** (blessed-dagger + soulforged-shortbow item_id preservati per tracking, weapon_family cambiato reliquia/balestra)? OR autorizzare rinomina item_id in Phase C tech gate (breaks tracking)? |
| **Q3** | **D4 slug drift 9 dungeon** (accepted D4 CLOSED, naming-only): mantenere accettato per governance o autorizzare rinomina in E2.1 pre-Phase C? |
| **Q4** | **Iconic family cumulative ridondanze T4/T5** (dragonhunter/elder-wyrm/ambash-forge/alevoran-perpetual/emberking-endgame/efreto-purger/adalan-archmage/adalan-arcane-thief): accettare governance preservation o autorizzare rework naming families in E2.1? |
| **Q5** | Autorizzare **PRD.md append `R18.5 Phase E2 CLOSED`** post-review (NON auto-eseguito, pattern D3/D4/D5/E1 verbatim)? |
| **Q6** | Post E2 approval: autorizzare **Phase C Tech Dry-Run** (proficiency runtime + class_slug migration + ILVL endgame implementation)? |
| **Q7** | **Legendary utility numeric finals** (cooldown, %, scaling per 15 Legendary — 11 approved+hybrid + 4 progressive): finalizzare pre-Phase C tech gate o durante Phase C? |
| **Q8** | **4 progressive Legendary placeholders (P1-P4)**: finalizzare lore/source/utility in Phase C tech gate o iterazione E3? |
| **Q9** | **6 hint T4 PENDING PM (sub-Epic voluto)**: accettare come design intent finale o iterazione E1.2 rework? |
| **Q10** | **R18.6 Class Halls kickoff**: mantenere PLANNED / HOLD UNTIL Phase C tech dry-run CLOSED? |
| **Q11** | **Marketing Brief**: mantenere DEFERRED? |
| **Q12** | **14 duplicate/near-duplicate nome_it** rilevati in Sezione 5: rename in E2.1 o accettare come voluto (varianti T-suffix)? |

---

## Governance check STEP 23 (E2)

| Voce | Stato |
|---|:---:|
| **36 sigilli byte-identical** | ✅ pytest 6/6 PASSED post-write |
| Zero DB writes | ✅ |
| Zero code changes `.py`/`.js`/`.jsx`/`.tsx`/`.ts` | ✅ |
| Zero migrations | ✅ |
| Zero item creation live | ✅ |
| Zero drop table apply | ✅ |
| Zero economy changes | ✅ |
| `lore_meta.py` invariato | ✅ SHA256 `a18f708b...` invariato |
| Zero sealed file modification | ✅ |
| **Item table modification authorized (micro-eccezione PM)** | ✅ **D1/D2 .json naming-only AUTORIZZATA** |
| **Stat/balance changes** | ✅ **ZERO** (E2 naming-only, no stat changes) |
| Typo-only fixes | ✅ 0 (nessun typo rilevato) |
| Utility changes (nuove) | ✅ ZERO |
| Item_id changes | ✅ ZERO (tutti gli item_id preservati) |
| Rarity/class/tier/lore/source changes | ✅ ZERO |
| Anti-P2W field changes | ✅ ZERO |
| Catalog 1500/1500 preserved | ✅ |
| Phase C auto-start | ✅ BLOCKED (STOP after E2, PM review required) |
| R18.6 auto-start | ✅ BLOCKED (PLANNED, HOLD UNTIL Phase C CLOSED) |
| Marketing Brief auto-start | ✅ BLOCKED (DEFERRED) |
| PRD append E2 CLOSED auto | ✅ BLOCKED (rinviato a post-PM-approval, pattern D3/D4/D5/E1 verbatim) |
| Classi canoniche Warrior/Rogue/Mage/Priest/Ranger | ✅ NO drift |
| Files deliverable | ✅ 2 (.md + .json) |

---

## Statement finale STEP 23

**STOP dopo E2. Attendo PM review Q1-Q12 prima di Phase C Tech Dry-Run.**

**E2 Global Naming Pass COMPLETED** ✅
- 151 armor naming drift EN→IT fixed bulk (heavy/medium Warrior → piastre/maglia; medium Ranger → maglia; light Rogue/Ranger → cuoio)
- 0 stat/balance changes (E2 naming-only per governance PM)
- 0 typo stat fixes (nessun typo evidente rilevato)
- 4 slug drift post-E1.1 documentati (item_id preservati per tracking — Option A)
- 14 duplicate nome_it documentati (backlog Q12 gate PM)
- Iconic family cumulative ridondanze documentate (Q4 gate PM)
- NPC 5 LOCKED consistent cross-tier verified
- Legendary 15/15 naming review PASSED
- Catalog 1500/1500 · rarity 400/450/400/235/15 · class 300×5 · **proficiency 0 residue** · anti-P2W 1500/1500 tutti EXACT MATCH
- 36 sigilli byte-identical

**Post-E2 NON parte automaticamente**:
- ❌ Phase C Tech Dry-Run (HOLD UNTIL E2 REVIEW)
- ❌ R18.6 Class Halls kickoff (PLANNED)
- ❌ Marketing Brief (DEFERRED)
- ❌ PRD append `R18.5 Phase E2 CLOSED` (rinviato a post-PM-approval)
- ❌ Rework autonomo iconic family / slug D4 / duplicate nome_it / hint T4 PENDING (tutti PENDING PM Q gate)

**Attendo il tuo GO esplicito.**

---

**R18.5 status flow (aggiornato post-STEP 23)**:
`Phase D5 (STEP 18)` ✅ CLOSED → `CATALOGO 1500/1500 (STEP 19)` ✅ MILESTONE → `Phase E1 (STEP 20)` ✅ CLOSED → `Phase E1.1 (STEP 21)` ✅ CLOSED → `PRD E1 CLOSED (STEP 22)` ✅ CLOSED → **`Phase E2 Global Naming Pass (STEP 23)`** 🟡 **DRAFT — PENDING PM Q1-Q12 review** → `Phase C Tech Dry-Run` 🔒 HOLD UNTIL E2 REVIEW / `R18.6 Class Halls` 🔒 PLANNED / `Marketing Brief` 🔒 DEFERRED

---

**FINE STEP 23 — R18.5 Phase E2 Global Naming Pass — DOCUMENTAL ONLY (naming-only micro-eccezione)**
