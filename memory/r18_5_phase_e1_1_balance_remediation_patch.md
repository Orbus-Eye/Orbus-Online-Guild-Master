# R18.5 — Phase E1.1 · Balance Remediation Patch (STEP 21)

**Round**: R18.5 — Itemization, ILVL & Gear Progression Rework
**Phase**: E1.1 — Balance Remediation Patch (post-E1 approval)
**STEP**: 21
**Locked at UTC**: `2026-07-07T18:30:00Z`
**Governance**: **DOCUMENTAL ONLY — MICRO-ECCEZIONE AUTORIZZATA PM** su file item table D1-D4 (`.json`) per fix 4 HIGH + 16 MEDIUM. Preserva 1500/1500, rarity, class, anti-P2W, tier, source. NO code/DB/migrations/sealed.
**Status**: ✅ **APPLIED**
**Authority**: PM Orchestrator — STEP 21 catena autorizzata post-E1 approval (HIGH=A + MEDIUM split execution)

**Deliverables**:
- `/app/memory/r18_5_phase_e1_1_balance_remediation_patch.md` (questo file)
- `/app/memory/r18_5_phase_e1_1_balance_remediation_patch.json` (841 righe · SHA256 `3e3f0ae7e3589be36e831cc1a8c53dd4720a2d0c4f1f0dcd10f3325262c8d3c3`)

---

## Sezione 1 — Lista 4 HIGH fixes (prima/dopo)

| # | item_id | phase | field | before | after |
|:---:|---|:---:|---|---|---|
| 1 | `priest-blessed-dagger` | D1 | `weapon_family` | `pugnale` | **`reliquia`** |
| 1 | `priest-blessed-dagger` | D1 | `nome_it` | Pugnale Benedetto | **Reliquia Benedetta** |
| 1 | `priest-blessed-dagger` | D1 | `stat_principali` | `WIS +2, damage 3-5, heal +2` | `WIS +2, heal +3, mana +4` |
| 2 | `priest-blessed-dagger-t2` | D2 | `weapon_family` | `pugnale` | **`reliquia`** |
| 2 | `priest-blessed-dagger-t2` | D2 | `nome_it` | Pugnale Benedetto T2 | **Reliquia Benedetta T2** |
| 2 | `priest-blessed-dagger-t2` | D2 | `stat_principali` | `WIS +4, damage 4-7, heal +3` | `WIS +4, heal +5, mana +7` |
| 3 | `rogue-soulforged-shortbow` | D3 | `weapon_family` | `arco` | **`balestra`** |
| 3 | `rogue-soulforged-shortbow` | D3 | `nome_it` | Arco Corto Forgiato d'Anima | **Balestra Forgiata d'Anima** |
| 3 | `rogue-soulforged-shortbow` | D3 | `stat_principali` | `AGI +12, damage 18-23, crit +3%` | `AGI +12, damage 18-23, range +3, crit +3%` |
| 4 | `rogue-soulforged-shortbow-master` | D3 | `weapon_family` | `arco` | **`balestra`** |
| 4 | `rogue-soulforged-shortbow-master` | D3 | `nome_it` | Arco Corto Forgiato d'Anima Maestro | **Balestra Forgiata d'Anima Maestro** |
| 4 | `rogue-soulforged-shortbow-master` | D3 | `stat_principali` | `AGI +18, damage 26-33, crit +5%, soul res +4%` | `AGI +18, damage 26-33, range +4, crit +5%, soul res +4%` |

**Governance HIGH**: preservati `item_id` (tracking) · `rarity` · `tier` · `classe_orientata` · `slot` · `lore_source` · `source` · `iconic_family` · `affects_*` · `anti-P2W` · `is_tradeable`. Rimossi campi damage per reliquia (non arma da colpo), aggiunti mana coerenti con pattern reliquia Priest esistente. Aggiunti `range` per balestra Rogue coerenti con pattern balestra esistente.

---

## Sezione 2 — Lista 16 MEDIUM stat outlier fixes + 6 PENDING PM (prima/dopo)

### 2.1 Fixed 16 MEDIUM (applicati)

| # | item_id | phase | category | before | after |
|:---:|---|:---:|---|---|---|
| M1 | `warrior-ironrecruit-warblade` | D1 | power_creep_intra_tier | `STR +4, damage 6-10` | `STR +3, damage 6-10` |
| M2 | `warrior-guard-halberd` | D1 | power_creep_intra_tier | `STR +5, damage 8-12, reach +1` | `STR +4, damage 8-12, reach +1` |
| M3 | `warrior-heavy-belt-t2` | D2 | underpowered_intra_tier | `STR +2, END +3, hp +10` | `STR +4, END +3, hp +10` |
| M4 | `warrior-ergolat-siege-commander-plate` | D3 | underpowered_intra_tier | `STR +14, ...` | `STR +22, ...` (verso pool_mean 23.3) |
| M5 | `warrior-t4-emberking-siege-boss` | D4 | underpowered_intra_tier | `STR +19, ...` | `STR +27, ...` (verso pool_mean 28.67) |
| M6 | `warrior-black-forge-master-hammer` | D3 | power_creep_cross_tier | `STR +25, ...` | `STR +24, ...` (sotto T4 mean*1.10=24.53) |
| M7 | `rogue-wraith-warden-boss-dagger` | D3 | power_creep_cross_tier | `AGI +25, ...` | `AGI +24, ...` |
| M8 | `rogue-soul-abyss-ancestral-dagger` | D3 | power_creep_cross_tier | `AGI +26, ...` | `AGI +24, ...` |
| M9 | `mage-observatory-blind-astronomer-staff` | D3 | power_creep_cross_tier | `INT +25, ...` | `INT +24, ...` |
| M10 | `mage-celestial-seraph-staff` | D3 | power_creep_cross_tier | `INT +26, ...` | `INT +24, ...` |
| M11 | `priest-necropolis-guardian-mace` | D3 | power_creep_cross_tier | `WIS +25, ...` | `WIS +24, ...` |
| M12 | `priest-heretic-archbishop-mace` | D3 | power_creep_cross_tier | `WIS +26, ...` | `WIS +24, ...` |
| M13 | `priest-souldrain-ancestor-mace` | D3 | power_creep_cross_tier | `WIS +25, ...` | `WIS +24, ...` |
| M14 | `ranger-wyrmscale-vermeide-bow` | D3 | power_creep_cross_tier | `AGI +26, ...` | `AGI +24, ...` |
| M15 | `ranger-wraith-warden-boss-bow` | D3 | power_creep_cross_tier | `AGI +25, ...` | `AGI +24, ...` |
| M16 | `ranger-souldrain-ancestor-bow` | D3 | power_creep_cross_tier | `AGI +26, ...` | `AGI +24, ...` |

**Governance MEDIUM**: solo `stat_principali` modificato (main stat -1/-2 o verso pool mean). Preservati damage/crit/armor/mana/heal/range/soul res/utility teaser (dispell-chain, mass-soulbind-release, siege banner, ember-throne-teaser, ecc.). NO cambio tier/rarity/classe/lore/source/anti-P2W/utility.

### 2.2 PENDING PM 6 (design intent progressive marker sub-Epic)

| # | item_id | phase | classe | motivazione PENDING PM |
|:---:|---|:---:|:---:|---|
| P1 | `warrior-t4-legendary-emberking-crown-hint` | D4 | Warrior | STR=18 sub-Epic (pool_mean 28.67, z=-3.06). Hint T4 progressive verso Legendary T5 emberking-crown Warrior (bracket Infernale saturato D4). Sub-Epic voluto per anticipare narrative Legendary. Fix richiederebbe rework utility "LEGENDARY-hint teaser" o promozione rarity → creativa. |
| P2 | `warrior-t4-legendary-void-touched-hint` | D4 | Warrior | STR=18 sub-Epic hint verso L2 void-touched-blade T5 Rogue Legendary approved. Sub-Epic voluto. |
| P3 | `rogue-t4-legendary-soul-abyss-hint` | D4 | Rogue | AGI=18 sub-Epic hint verso P3 progressive-slot-03 T5 Rogue Legendary soul-bind future. Sub-Epic voluto. |
| P4 | `mage-t4-legendary-void-warlock-hint` | D4 | Mage | INT=18 sub-Epic hint verso L2 void-touched-blade cross-class hint. Sub-Epic voluto. |
| P5 | `priest-t4-legendary-celestial-halo-hint` | D4 | Priest | WIS=18 sub-Epic hint verso L3 seraph-halo-crown T5 Priest Legendary approved. Sub-Epic voluto. |
| P6 | `priest-t4-legendary-resurrect-hint` | D4 | Priest | WIS=17 sub-Epic hint verso P2 progressive-slot-02 T5 Priest Legendary resurrection future. Sub-Epic voluto. |

**Motivazione PENDING PM**: i 6 hint T4 sono progettati come marker narrative-progressive sub-Epic voluti, per anticipare i corrispondenti Legendary T5. Modificarli per allinearli alla mean pool_Epic_T4 (28.67) richiederebbe:
- (A) rework utility "LEGENDARY-hint teaser" → decisione creativa
- (B) promozione rarity Epic → Rare (drift catalog 1500) → NO
- (C) accettazione sub-Epic voluto → status quo

**Governance**: nessuna decisione autonoma. Documentati come PENDING PM per gate futuro (Phase C tech gate o iterazione E1.2).

---

## Sezione 3 — Item table files modificati (path + SHA256 before → after)

| File | Modified | SHA256 before E1.1 | SHA256 after E1.1 |
|---|:---:|---|---|
| `r18_5_phase_d1_t1_item_table.json` | ✅ YES | `2ac54bed298b1562...` | **`6058ae78b337c596d6ae3a94550dda90e20b4b5da284724e1481c3ffd8b1ddff`** |
| `r18_5_phase_d2_t2_item_table.json` | ✅ YES | `bb0db9ca28d5b954...` | **`e246f2773b8584772766124cd323358d3a750a1be853d0777d92eead3a2de6d5`** |
| `r18_5_phase_d3_t3_item_table.json` | ✅ YES | `27cf0003da4fba1c...` | **`b478ae641eec3f33e440cfec80a2e52da4a81c8fd76b7df9594234be09644d44`** |
| `r18_5_phase_d4_t4_item_table.json` | ✅ YES | `1dc870fad0fd4fe7...` | **`6d42a01983d6bcf37354f2b5ba99cff6a2b4d8b2c272819907a57dbfe9455acb`** |
| `r18_5_phase_d5_t5_item_table.json` | ❌ NO | `58e9f0ea86f7fb5e...` | `58e9f0ea86f7fb5eeaf00c53728fe15c4f4a40041c98e2639a339b873069ae6e` (unchanged) |

**Files `.md` D1-D5**: NON modificati in E1.1 (contengono solo aggregati/report; nessun aggregate cambia in E1.1: rarity/class/tier/source/anti-P2W tutti INVARIATI).

---

## Sezione 4 — Item count post-fix

| Vista | Valore |
|---|:---:|
| Totale items | **1500 / 1500** ✅ EXACT |
| D1 items | 300 |
| D2 items | 350 |
| D3 items | 350 |
| D4 items | 300 |
| D5 items | 200 |

Nessun item creato / cancellato. Preservazione 1500/1500 verificata.

---

## Sezione 5 — Rarity post-fix

| Rarity | Count post-fix | Target | Status |
|---|:---:|:---:|:---:|
| Common | 400 | 400 | ✅ EXACT |
| Uncommon | 450 | 450 | ✅ EXACT |
| Rare | 400 | 400 | ✅ EXACT |
| Epic | 235 | 235 | ✅ EXACT |
| Legendary | 15 | 15 | ✅ EXACT |
| **TOTALE** | **1500** | **1500** | ✅ **EXACT 400/450/400/235/15** |

Rarity 100% preservato (E1.1 non ha cambiato rarity di alcun item).

---

## Sezione 6 — Class distribution post-fix

| Classe | Count | Target | Status |
|---|:---:|:---:|:---:|
| Warrior | 300 | 300 | ✅ EXACT |
| Rogue | 300 | 300 | ✅ EXACT |
| Mage | 300 | 300 | ✅ EXACT |
| Priest | 300 | 300 | ✅ EXACT |
| Ranger | 300 | 300 | ✅ EXACT |
| **TOTALE** | **1500** | **1500** | ✅ **EXACT 300×5** |

Class distribution 100% preservata (nessun cross-class promotion).

---

## Sezione 7 — Proficiency violations post-fix

| Vista | Count | Status |
|---|:---:|:---:|
| **Proficiency violations residue** | **0 / 4** | ✅ **CLEAN** (post 4 HIGH fix) |
| Priest scudo/piastre/cuoio/maglia | 0 | ✅ HARD BLOCK preserved |
| Weapon backlog `strumento`/`falce`/`trinket_backlog` | 0 | ✅ RESERVED preserved |

**HIGH violations risolte 4/4**:
- `priest-blessed-dagger` pugnale → reliquia ✅
- `priest-blessed-dagger-t2` pugnale → reliquia ✅
- `rogue-soulforged-shortbow` arco → balestra ✅
- `rogue-soulforged-shortbow-master` arco → balestra ✅

---

## Sezione 8 — Anti-P2W post-fix

| Vista | Valore | Status |
|---|:---:|:---:|
| Total items | 1500 | — |
| `can_be_sold_for_real_money = false` | 1500 / 1500 | ✅ PASSED |
| Anti-P2W violations | 0 | ✅ PASSED |
| Field inconsistency (affects_* true & real_money=true) | 0 | ✅ PASSED |

Anti-P2W 100% preservato (E1.1 non ha toccato campi `can_be_sold_for_real_money` / `affects_*`).

---

## Sezione 9 — SHA256 file modificati (dettaglio)

| File | Path | SHA256 finale post-E1.1 |
|---|---|---|
| D1 (T1) | `/app/memory/r18_5_phase_d1_t1_item_table.json` | `6058ae78b337c596d6ae3a94550dda90e20b4b5da284724e1481c3ffd8b1ddff` |
| D2 (T2) | `/app/memory/r18_5_phase_d2_t2_item_table.json` | `e246f2773b8584772766124cd323358d3a750a1be853d0777d92eead3a2de6d5` |
| D3 (T3) | `/app/memory/r18_5_phase_d3_t3_item_table.json` | `b478ae641eec3f33e440cfec80a2e52da4a81c8fd76b7df9594234be09644d44` |
| D4 (T4) | `/app/memory/r18_5_phase_d4_t4_item_table.json` | `6d42a01983d6bcf37354f2b5ba99cff6a2b4d8b2c272819907a57dbfe9455acb` |
| D5 (T5) | `/app/memory/r18_5_phase_d5_t5_item_table.json` | `58e9f0ea86f7fb5eeaf00c53728fe15c4f4a40041c98e2639a339b873069ae6e` (unchanged) |

---

## Sezione 10 — Sealed integrity result

**pytest** `backend/tests/backend_r18_4_sealed_integrity_test.py` post-write E1.1:

```
2 workers [6 items]
......                                                                   [100%]
============================== 6 passed in 0.44s ==============================
```

✅ **36 sigilli byte-identical VERIFIED** (pytest 6/6 PASSED).

---

## Sezione 11 — `git status`

```
 M memory/PRD.md                                     (STEP 19 append, tracked modified)
 M memory/r18_5_phase_d1_t1_item_table.json          (E1.1 HIGH#1 + MEDIUM#1-2)
 M memory/r18_5_phase_d2_t2_item_table.json          (E1.1 HIGH#2 + MEDIUM#3)
 M memory/r18_5_phase_d3_t3_item_table.json          (E1.1 HIGH#3-4 + MEDIUM#4, M6-M16)
 M memory/r18_5_phase_d4_t4_item_table.json          (E1.1 MEDIUM#5)
?? memory/r18_5_phase_d5_t5_item_table.md/.json       (untracked, dallo STEP 18)
?? memory/r18_5_phase_e1_global_balance_pass.md/.json (untracked, dallo STEP 20)
?? memory/r18_5_phase_e1_1_balance_remediation_patch.md/.json  (nuovi deliverable STEP 21)
```

**Nessun sealed file toccato · nessun `.py`/`.js`/`.jsx`/`.tsx`/`.ts` modificato · nessun `lore_meta.py` toccato**.

---

## Sezione 12 — Eventuali PENDING PM residuals (outlier non corretti)

**Totale PENDING PM residuals**: **6 items** (design intent progressive marker sub-Epic voluto).

| # | item_id | phase | classe | motivazione |
|:---:|---|:---:|:---:|---|
| P1 | `warrior-t4-legendary-emberking-crown-hint` | D4 | Warrior | STR=18 sub-Epic voluto (hint verso Legendary T5 emberking-crown Infernale saturato) |
| P2 | `warrior-t4-legendary-void-touched-hint` | D4 | Warrior | STR=18 sub-Epic voluto (hint verso L2 void-touched-blade T5 Rogue) |
| P3 | `rogue-t4-legendary-soul-abyss-hint` | D4 | Rogue | AGI=18 sub-Epic voluto (hint verso P3 progressive-slot-03 T5 Rogue soul-bind) |
| P4 | `mage-t4-legendary-void-warlock-hint` | D4 | Mage | INT=18 sub-Epic voluto (hint verso L2 void-touched-blade cross-class) |
| P5 | `priest-t4-legendary-celestial-halo-hint` | D4 | Priest | WIS=18 sub-Epic voluto (hint verso L3 seraph-halo-crown T5 Priest) |
| P6 | `priest-t4-legendary-resurrect-hint` | D4 | Priest | WIS=17 sub-Epic voluto (hint verso P2 progressive-slot-02 T5 Priest resurrection) |

**Governance PENDING**: modificarli richiederebbe rework utility ("LEGENDARY-hint teaser") o promozione rarity → **decisione creativa PM**. Marcati esplicitamente `PENDING PM` per gate futuro (Phase C tech gate o iterazione E1.2 se richiesta).

---

## Governance check STEP 21 (E1.1)

| Voce | Stato |
|---|:---:|
| **36 sigilli byte-identical** | ✅ pytest 6/6 PASSED post-write |
| Zero DB writes | ✅ |
| Zero code changes `.py`/`.js`/`.jsx`/`.tsx`/`.ts` | ✅ |
| Zero migrations | ✅ |
| Zero item creation live (nuovi item) | ✅ |
| Zero drop table apply | ✅ |
| Zero economy changes | ✅ |
| `lore_meta.py` invariato | ✅ SHA256 `a18f708b...` invariato |
| Zero sealed file modification | ✅ |
| **Item table modification authorized (micro-eccezione PM)** | ✅ **D1/D2/D3/D4 .json AUTORIZZATA** |
| Item_id changes | ✅ ZERO (tutti gli item_id preservati per tracking) |
| Rarity changes | ✅ ZERO |
| Class changes | ✅ ZERO |
| Tier changes | ✅ ZERO |
| Lore source changes | ✅ ZERO |
| Source changes | ✅ ZERO (dungeon/raid/craft invariati) |
| Anti-P2W field changes | ✅ ZERO |
| Utility changes (nuove) | ✅ ZERO (utility esistenti preservate) |
| Catalog 1500/1500 preserved | ✅ |
| Classi canoniche Warrior/Rogue/Mage/Priest/Ranger | ✅ NO drift |
| Files deliverable | ✅ 2 (.md + .json) |

---

## Statement finale STEP 21

**E1.1 Balance Remediation Patch COMPLETED** ✅
- 4 HIGH proficiency fixes applicati (Priest pugnale→reliquia ×2, Rogue arco→balestra ×2)
- 16 MEDIUM stat outlier fixes applicati (2 power creep T1 + 3 underpowered legit + 11 cross-tier T3)
- 6 hint T4 marcati PENDING PM (design intent progressive marker sub-Epic voluto)
- Catalog 1500/1500 · rarity 400/450/400/235/15 · class 300×5 · **proficiency 0 residue** · anti-P2W 1500/1500 tutti EXACT MATCH
- 36 sigilli byte-identical
- 151 naming drift EN→IT residuo → **deferred a E2 (STEP 23)**

**Next in chain**: STEP 22 (PRD append E1 CLOSED) → STEP 23 (E2 Naming Pass).
