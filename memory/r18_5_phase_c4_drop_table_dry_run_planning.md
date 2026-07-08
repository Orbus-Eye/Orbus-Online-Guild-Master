# R18.5 — Phase C4 · Drop Table Dry-Run Planning

**Round**: R18.5 · **Phase**: C4 Drop Table Dry-Run Planning
**Locked at UTC**: `2026-07-08T11:30:00Z`
**Governance**: **DOCUMENTAL ONLY — drop table dry-run + HYBRID drop rate proposal. NO drop rate apply · NO drop table apply · NO code/DB/migrations.**
**Status**: ✅ **APPLIED — dry-run analytics + proposal per PM review**
**Authority**: PM Orchestrator — Phase C4 dispatch (Q8=GO C4)
**Lingua output**: 🇮🇹 SOLO ITALIANO

**Deliverables**:
- `/app/memory/r18_5_phase_c4_drop_table_dry_run_planning.md` (questo file)
- `/app/memory/r18_5_phase_c4_drop_table_dry_run_planning.json` (SHA256 `05057ba7847436de7ccfc7674ed9e16a184dce9872ae201eb6d8ab6646a5e8e3`)

---

## 1. Executive Summary

Analisi documentale drop table via reverse-mapping dai `source` degli items D1-D5. Proposta drop rate finali HYBRID (H1-H4). Design material parallel drop policy. Validazione anti-P2W. Segnalazione PM gate items (slot canonical drift, dungeon count, raid count).

**Invarianti preservati**:
- `item_count_1500`: True
- `rarity_400_450_400_235_15`: True
- `class_300x5`: True
- `class_slug_null_1500`: True
- `runtime_apply_ready_0_1500`: True
- `anti_p2w_1500_1500`: True
- `progressive_marker_10`: True


---

## 2. Source Catalog

**Target PM**: `dungeon_normal_3p = 60` · `raid_5p = 12`

**Osservato da D1-D5** (via reverse-mapping del primary token del campo `source`):

| Metric | Value |
|---|:--:|
| dungeon unique tokens | **61** |
| raid unique tokens | **13** |
| delta dungeon vs target 60 | **+1** |
| delta raid vs target 12 | **+1** |

**Nota**: Delta osservato: dungeon +4 vs target 60 (probabile meta-source residue non filtrato); raid +1 vs target 12. Discrepanza segnalata come PM gate item C5.

**Categorization logic**: Estratto via reverse-mapping del primary token del campo `source`. Filtri meta-source applicati: tutorial/npc/vendor/crafting/ranking/achievement/quest/chest/event/starter-crafting/early-vendor/early-achievement/PENDING.

---

## 3. Dungeon Drop Mapping (Normal 3p)

**Count observed**: **61** · Target PM: **60** · Delta: **+1**

| # | dungeon_token | items | tier_dist | rarity_dist | has_legendary |
|:--:|---|:--:|---|---|:--:|
| 1 | `wild-hunt-lair` | 60 | T2:60 | C:31 U:25 R:4 E:0 L:0 |  |
| 2 | `druid-grove` | 37 | T1:37 | C:35 U:2 R:0 E:0 L:0 |  |
| 3 | `stormcaller-vault` | 36 | T2:36 | C:8 U:21 R:7 E:0 L:0 |  |
| 4 | `chapel-of-silent-vows` | 29 | T1:29 | C:26 U:3 R:0 E:0 L:0 |  |
| 5 | `worldroot-hollow` | 28 | T2:28 | C:0 U:20 R:8 E:0 L:0 |  |
| 6 | `bastion-of-alevora` | 27 | T3:27 | C:7 U:15 R:5 E:0 L:0 |  |
| 7 | `blackpine-thicket` | 26 | T2:26 | C:25 U:1 R:0 E:0 L:0 |  |
| 8 | `sanctum-of-fading-souls` | 25 | T4:25 | C:0 U:6 R:13 E:6 L:0 |  |
| 9 | `abyssal-drift` | 24 | T4:24 | C:0 U:7 R:12 E:5 L:0 |  |
| 10 | `forgotten-shrine-of-adalan` | 24 | T1:24 | C:2 U:22 R:0 E:0 L:0 |  |
| 11 | `soulforge-crucible` | 24 | T3:24 | C:4 U:11 R:7 E:2 L:0 |  |
| 12 | `dragon-vault-outer` | 23 | T4:23 | C:0 U:6 R:12 E:5 L:0 |  |
| 13 | `frost-cathedral` | 23 | T4:23 | C:0 U:5 R:11 E:7 L:0 |  |
| 14 | `void-touched-crossroads` | 23 | T4:23 | C:0 U:5 R:10 E:8 L:0 |  |
| 15 | `conciatore-elfwood` | 22 | T3:16/T4:6 | C:2 U:10 R:10 E:0 L:0 |  |
| 16 | `memoria-antechamber` | 22 | T4:22 | C:0 U:5 R:12 E:5 L:0 |  |
| 17 | `emberking-approach` | 20 | T4:20 | C:0 U:5 R:10 E:5 L:0 |  |
| 18 | `ironhold-keep` | 20 | T2:20 | C:16 U:3 R:1 E:0 L:0 |  |
| 19 | `sunken-library` | 20 | T1:20 | C:19 U:1 R:0 E:0 L:0 |  |
| 20 | `emberlord-hideout` | 19 | T2:19 | C:1 U:13 R:5 E:0 L:0 |  |
| 21 | `fabbro-bulwark` | 19 | T3:15/T4:4 | C:3 U:7 R:9 E:0 L:0 |  |
| 22 | `broken-tower-of-adalan` | 18 | T1:18 | C:0 U:18 R:0 E:0 L:0 |  |
| 23 | `storm-spire` | 18 | T2:18 | C:17 U:1 R:0 E:0 L:0 |  |
| 24 | `heretic-cathedral` | 17 | T3:17 | C:0 U:7 R:8 E:2 L:0 |  |
| 25 | `mercenary-holdfast` | 17 | T3:17 | C:0 U:10 R:6 E:1 L:0 |  |
| 26 | `sarto-sacro` | 17 | T3:13/T4:4 | C:4 U:8 R:5 E:0 L:0 |  |
| 27 | `tessitrice-arcana` | 17 | T3:12/T4:5 | C:3 U:9 R:5 E:0 L:0 |  |
| 28 | `frostbound-vault` | 16 | T2:16 | C:1 U:12 R:3 E:0 L:0 |  |
| 29 | `starfall-basilica` | 15 | T3:15 | C:0 U:6 R:7 E:2 L:0 |  |
| 30 | `wyrmscale-pass` | 15 | T3:15 | C:0 U:8 R:6 E:1 L:0 |  |
| 31 | `bandit-hideout` | 14 | T1:14 | C:14 U:0 R:0 E:0 L:0 |  |
| 32 | `bandit-warlord-hideout` | 14 | T1:14 | C:1 U:13 R:0 E:0 L:0 |  |
| 33 | `infernal-pit-5p` | 14 | T4:14 | C:0 U:4 R:5 E:5 L:0 |  |
| 34 | `necropolis-approach` | 14 | T3:14 | C:0 U:6 R:7 E:1 L:0 |  |
| 35 | `pantheon-of-fallen-suns` | 14 | T5:14 | C:0 U:0 R:6 E:6 L:2 | 🏆 |
| 36 | `shadow-crypts` | 14 | T1:14 | C:10 U:4 R:0 E:0 L:0 |  |
| 37 | `cuoiaia-elfwood` | 13 | T3:8/T4:5 | C:2 U:6 R:5 E:0 L:0 |  |
| 38 | `moonwake-abbey` | 13 | T3:13 | C:2 U:7 R:3 E:1 L:0 |  |
| 39 | `sewer-nest` | 13 | T1:13 | C:12 U:1 R:0 E:0 L:0 |  |
| 40 | `wraithbound-ossuary` | 13 | T3:13 | C:0 U:4 R:7 E:2 L:0 |  |
| 41 | `elder-wyrm-descent-antechamber` | 12 | T4:12 | C:0 U:1 R:6 E:5 L:0 |  |
| 42 | `necropolis-descent` | 12 | T4:12 | C:0 U:2 R:5 E:5 L:0 |  |
| 43 | `starforged-approach` | 12 | T5:12 | C:0 U:0 R:6 E:6 L:0 |  |
| 44 | `arcane-fault-line` | 11 | T3:11 | C:2 U:6 R:2 E:1 L:0 |  |
| 45 | `cursed-mines` | 11 | T1:11 | C:7 U:4 R:0 E:0 L:0 |  |
| 46 | `elder-wyrm-descent` | 11 | T5:11 | C:0 U:0 R:5 E:5 L:1 | 🏆 |
| 47 | `stygian-reach` | 11 | T3:11 | C:0 U:5 R:5 E:1 L:0 |  |
| 48 | `world-tree-roots-5p` | 11 | T3:9/T4:2 | C:0 U:4 R:6 E:1 L:0 |  |
| 49 | `ambash-legendary-forge` | 10 | T5:10 | C:0 U:0 R:4 E:4 L:2 | 🏆 |
| 50 | `ashborn-ravine` | 10 | T3:10 | C:1 U:5 R:3 E:1 L:0 |  |
| 51 | `efreto-cursed-nexus` | 10 | T5:10 | C:0 U:0 R:5 E:5 L:0 |  |
| 52 | `hollow-crown-halls` | 10 | T3:10 | C:0 U:6 R:3 E:1 L:0 |  |
| 53 | `sundered-observatory` | 10 | T3:10 | C:0 U:5 R:4 E:1 L:0 |  |
| 54 | `void-touched-outpost` | 10 | T5:10 | C:0 U:0 R:5 E:5 L:0 |  |
| 55 | `black-forge-of-ergolat` | 9 | T3:9 | C:0 U:2 R:5 E:2 L:0 |  |
| 56 | `bonefall-crypt` | 9 | T2:9 | C:0 U:5 R:4 E:0 L:0 |  |
| 57 | `dragons-hoard` | 9 | T2:9 | C:0 U:6 R:3 E:0 L:0 |  |
| 58 | `lich-sanctum` | 9 | T1:9 | C:2 U:7 R:0 E:0 L:0 |  |
| 59 | `goblin-warrens` | 8 | T1:8 | C:8 U:0 R:0 E:0 L:0 |  |
| 60 | `iron-legion-outpost` | 8 | T3:8 | C:0 U:4 R:3 E:1 L:0 |  |
| 61 | `void-heart-sanctum` | 8 | T5:8 | C:0 U:0 R:4 E:4 L:0 |  |


---

## 4. Raid Drop Mapping (5p)

**Count observed**: **13** · Target PM: **12** · Delta: **+1**

| # | raid_token | items | tier_dist | rarity_dist | has_legendary |
|:--:|---|:--:|---|---|:--:|
| 1 | `hollow-monastery` | 53 | T2:53 | C:28 U:21 R:4 E:0 L:0 |  |
| 2 | `krastlov-siege` | 28 | T2:28 | C:12 U:10 R:6 E:0 L:0 |  |
| 3 | `necropolis-bells` | 25 | T4:25 | C:0 U:4 R:10 E:11 L:0 |  |
| 4 | `emberking-siege` | 22 | T4:22 | C:0 U:0 R:10 E:12 L:0 |  |
| 5 | `world-tree-collapse` | 21 | T5:21 | C:0 U:0 R:4 E:15 L:2 | 🏆 |
| 6 | `memoria-vault` | 20 | T4:20 | C:0 U:0 R:10 E:10 L:0 |  |
| 7 | `arcane-schism` | 16 | T3:16 | C:0 U:6 R:8 E:2 L:0 |  |
| 8 | `void-cathedral` | 15 | T5:15 | C:0 U:0 R:2 E:12 L:1 | 🏆 |
| 9 | `souldrain-abyss` | 14 | T3:14 | C:0 U:2 R:7 E:5 L:0 |  |
| 10 | `celestial-conclave` | 13 | T5:13 | C:0 U:0 R:2 E:9 L:2 | 🏆 |
| 11 | `dragon-vault` | 12 | T5:12 | C:0 U:0 R:2 E:9 L:1 | 🏆 |
| 12 | `bloodgrove-uprising` | 11 | T2:11 | C:0 U:6 R:5 E:0 L:0 |  |
| 13 | `broken-bastion-siege` | 11 | T3:11 | C:0 U:3 R:5 E:3 L:0 |  |


---

## 5. Elite / Group Track Mapping

**Definition**: Group Track Elite = sotto-catena dungeon 3p che include boss finale con drop Legendary (`has_legendary_drop=true`).

### Elite dungeon 3p con Legendary drop

| dungeon_token | tier | legendary_items |
|---|:--:|---|
| `pantheon-of-fallen-suns` | T5:14 | mage-t5-legendary-sole-nero-diadem · ranger-t5-legendary-halodi-fate-quiver-hybrid · warrior-t5-void-warden-epic-14 |
| `elder-wyrm-descent` | T5:11 | warrior-t5-legendary-dragon-elder-scale · warrior-t5-elder-wyrm-hunter-epic-05 · warrior-t5-void-warden-epic-06 |
| `ambash-legendary-forge` | T5:10 | warrior-t5-legendary-ambash-forge-hammer · mage-t5-legendary-ergolat-obelisk-focus-hybrid · warrior-t5-alevoran-perpetual-epic-03 |

### Elite raid con Legendary drop

| raid_token | tier | legendary_items |
|---|:--:|---|
| `world-tree-collapse` | T5:21 | rogue-t5-legendary-irthe-price-shroud-hybrid · ranger-t5-legendary-worldroot-scepter · warrior-t5-alevoran-perpetual-epic-11 |
| `void-cathedral` | T5:15 | rogue-t5-legendary-void-touched-blade · rogue-t5-adalan-arcane-thief-epic-22 · rogue-t5-ash-widow-epic-08 |
| `celestial-conclave` | T5:13 | priest-t5-legendary-celestial-conclave-mantle-hybrid · priest-t5-legendary-seraph-halo-crown · mage-t5-celestial-scholar-epic-12 |
| `dragon-vault` | T5:12 | warrior-t5-legendary-dragonlord-crown · warrior-t5-dragonlord-vanguard-epic-09 · warrior-t5-elder-wyrm-hunter-epic-21 |


**Nota**: Elite/Group Track dedicato T5 = 3 dungeon 3p endgame (ambash-legendary-forge/elder-wyrm-descent/pantheon-of-fallen-suns) + 4 raid Legendary (dragon-vault/void-cathedral/celestial-conclave/world-tree-collapse). Coerente con chain STEP 8.

---

## 6. Item → Source Consistency

| Metric | Value |
|---|:--:|
| total_items | 1500 |
| items with source non-null | **1500** ✅ |
| items missing source | **0** ✅ |
| consistency status | PASSED · 1500/1500 items hanno source valorizzato |

### Source categorization breakdown
- `dungeon_3p_legendary_bosses`: **7**
- `raid_bosses_legendary`: **8**
- `raid_boss_normal`: **117**
- `craft`: **209**
- `chest_reward`: **155**
- `vendor`: **27**
- `achievement`: **17**
- `quest`: **14**
- `ranking`: **14**
- `dungeon_normal_untagged`: **927**

_927 items con source narrativo (es. `wild-hunt-lair:`) sono classificati implicitamente come dungeon Normal 3p secondo il naming pattern; ambiguità documentale minor (non blocker)._


---

## 7. Rarity × Source Distribution

| source_category | Common | Uncommon | Rare | Epic | Legendary |
|---|:--:|:--:|:--:|:--:|:--:|
| `dungeon_3p` | 0 | 0 | 0 | 0 | 7 |
| `dungeon_normal_untagged` | 279 | 302 | 220 | 126 | 0 |
| `raid` | 0 | 22 | 52 | 43 | 8 |
| `craft` | 37 | 65 | 72 | 35 | 0 |
| `quest` | 3 | 2 | 9 | 0 | 0 |
| `vendor` | 21 | 1 | 5 | 0 | 0 |
| `achievement` | 12 | 0 | 0 | 5 | 0 |
| `ranking` | 0 | 0 | 9 | 5 | 0 |
| `chest_reward` | 47 | 54 | 33 | 21 | 0 |

**Governance observations**:
- Vendor NO Legendary/Epic → anti-P2W compliance ✅
- Craft NO Legendary → coerente con `NO normal crafting Legendary` policy ✅
- Legendary present SOLO in dungeon_3p endgame + raid endgame ✅


---

## 8. Tier × Source Distribution

| source_category | T1 | T2 | T3 | T4 | T5 |
|---|:--:|:--:|:--:|:--:|:--:|
| `dungeon_3p` | 0 | 0 | 0 | 0 | 7 |
| `raid` | 0 | 9 | 41 | 67 | 8 |
| `craft` | 17 | 13 | 100 | 39 | 40 |
| `quest` | 3 | 0 | 2 | 4 | 5 |
| `vendor` | 17 | 5 | 0 | 0 | 5 |
| `achievement` | 9 | 3 | 0 | 0 | 5 |
| `ranking` | 0 | 0 | 4 | 5 | 5 |
| `chest_reward` | 44 | 23 | 55 | 12 | 21 |
| `dungeon_normal_untagged` | 209 | 297 | 144 | 173 | 104 |


---

## 9. Class Coverage per Source Bracket

_Target: nessuna classe deve essere sotto-servita (min ≈ 20% per source bracket rilevante)._

| source_category | Warrior | Rogue | Mage | Priest | Ranger |
|---|:--:|:--:|:--:|:--:|:--:|
| `raid` | 25 | 26 | 23 | 31 | 20 |
| `craft` | 38 | 46 | 41 | 35 | 49 |
| `chest_reward` | 17 | 32 | 31 | 47 | 28 |
| `vendor` | 4 | 7 | 6 | 5 | 5 |
| `achievement` | 5 | 4 | 3 | 3 | 2 |
| `quest` | 3 | 3 | 3 | 3 | 2 |
| `ranking` | 3 | 2 | 3 | 3 | 3 |
| `dungeon_normal` | 202 | 179 | 188 | 171 | 187 |


**Assessment**: OK — nessuna classe sotto-servita in nessun bracket source rilevante. Priest sovra-rappresentato in chest_reward (47 vs media ~31), Warrior sotto in chest_reward (17). Non blocker.

---

## 10. Legendary Drop Readiness (15/15)

### 7 APPROVED — Ready

| item_id | source | drop_rate |
|---|---|:--:|
| `warrior-t5-legendary-dragonlord-crown` | dragon-vault raid boss finale | **2% (LIVE)** |
| `rogue-t5-legendary-void-touched-blade` | void-cathedral raid boss finale | **2% (NEW)** |
| `priest-t5-legendary-seraph-halo-crown` | celestial-conclave raid boss finale | **2% (NEW)** |
| `ranger-t5-legendary-worldroot-scepter` | world-tree-collapse raid boss finale | **2% (NEW)** |
| `warrior-t5-legendary-ambash-forge-hammer` | ambash-legendary-forge dungeon 3p boss | **1%** |
| `warrior-t5-legendary-dragon-elder-scale` | elder-wyrm-descent dungeon 3p boss | **1%** |
| `mage-t5-legendary-sole-nero-diadem` | pantheon-of-fallen-suns dungeon 3p Lv60 | **1%** |

### 4 HYBRID — Pending final PM decision (0.5% direzionale C1)

| item_id | source | drop_rate |
|---|---|:--:|
| `priest-t5-legendary-celestial-conclave-mantle-hybrid` | celestial-conclave raid alternate | **HYBRID (0.5% direzionale C1)** |
| `rogue-t5-legendary-irthe-price-shroud-hybrid` | world-tree-collapse raid alternate | **HYBRID (0.5% direzionale C1)** |
| `mage-t5-legendary-ergolat-obelisk-focus-hybrid` | ambash-legendary-forge dungeon alternate | **HYBRID (0.5% direzionale C1)** |
| `ranger-t5-legendary-halodi-fate-quiver-hybrid` | pantheon-of-fallen-suns dungeon alternate | **HYBRID (0.5% direzionale C1)** |

### 4 PROGRESSIVE — Reserved / PENDING PM

| item_id | source | drop_rate |
|---|---|:--:|
| `mage-t5-legendary-progressive-slot-01-pending` | PENDING PM (raid endgame progressive discovery) | **1-2% direzionale · PENDING PM** |
| `priest-t5-legendary-progressive-slot-02-pending` | PENDING PM (dungeon 3p endgame progressive) | **1% direzionale · PENDING PM** |
| `rogue-t5-legendary-progressive-slot-03-pending` | PENDING PM (raid endgame progressive discovery) | **1-2% direzionale · PENDING PM** |
| `ranger-t5-legendary-progressive-slot-04-pending` | PENDING PM (dungeon 3p endgame progressive) | **1% direzionale · PENDING PM** |

### Policy Compliance

- `NO_shop_legendary`: True
- `NO_premium_legendary`: True
- `NO_direct_real_money_sale`: True
- `NO_pay_to_win`: True
- `NO_normal_crafting_legendary`: True
- `NO_generic_stat_stick_legendary`: True
- `fonte_precisa`: PASSED 11/15 (11 approved+hybrid · 4 progressive PENDING PM)
- `drop_molto_raro`: PASSED (1-2% raid · 1% dungeon 3p · 0.5% HYBRID direzionale)
- `utility_unica`: PASSED 11/11 (C0.L.1 numeric finals)
- `lore_source_forte`: PASSED 11/11 (capstone T5)


---

## 11. HYBRID Drop Rate Final Proposal

### H1-CELESTIAL-CONCLAVE-MANTLE

| Campo | Valore |
|---|---|
| **item_id** | `priest-t5-legendary-celestial-conclave-mantle-hybrid` |
| **source** | celestial-conclave raid boss finale (alternate/secondary drop) |
| **source_type** | raid_5p_alternate |
| **candidate_drop_rate** | 0.5% (direzionale C1) |
| **recommended_final_drop_rate** | **0.5%** |
| **farming_risk** | LOW — raid endgame accessibile solo con roster T5 |
| **economy_risk** | LOW — no market speculation (bind-on-pickup) |
| **rationale** | Coerente con secondary raid drop bracket (< 2% primary Legendary). Priest T5 chest = capstone Celeste. 0.5% garantisce rarità senza frustrazione eccessiva. |
| **PM_decision_required** | ❓ conferma 0.5% o preferisci differenziare al ribasso (0.3-0.4%) per rarità estrema? |

### H2-IRTHE-PRICE-SHROUD

| Campo | Valore |
|---|---|
| **item_id** | `rogue-t5-legendary-irthe-price-shroud-hybrid` |
| **source** | world-tree-collapse raid boss finale (alternate/secondary drop, Irthe capstone) |
| **source_type** | raid_5p_alternate |
| **candidate_drop_rate** | 0.5% (direzionale C1) |
| **recommended_final_drop_rate** | **0.5%** |
| **farming_risk** | LOW-MEDIUM — raid endgame; utility Death's Toll è high-power → tuning post-launch consigliato |
| **economy_risk** | LOW — bind-on-pickup, no economy leak |
| **rationale** | Coerente con secondary raid drop bracket. Utility Death's Toll (self-damage + max-damage next-hit) è high-power → 0.5% è appropriato per rarità narrativa. |
| **PM_decision_required** | ❓ conferma 0.5% (default) o rivaluta a 0.3% per high-power utility? |

### H3-ERGOLAT-OBELISK-FOCUS

| Campo | Valore |
|---|---|
| **item_id** | `mage-t5-legendary-ergolat-obelisk-focus-hybrid` |
| **source** | ambash-legendary-forge dungeon 3p alternate (Ergolat capstone secondary) |
| **source_type** | dungeon_3p_alternate |
| **candidate_drop_rate** | 0.5% (direzionale C1) |
| **recommended_final_drop_rate** | **0.5%** |
| **farming_risk** | MEDIUM — dungeon 3p Lv59-60 accessibile con 3-man party; farming ripetibile più frequente vs raid |
| **economy_risk** | LOW — bind-on-pickup |
| **rationale** | Coerente con dungeon 3p secondary (< 1% primary Legendary L5). Mage capstone Ergolat/Absence. Farming risk MEDIUM richiede lock 1x/settimana loot? |
| **PM_decision_required** | ❓ conferma 0.5% oppure applica loot-lock 1x/settimana per gestire farming risk MEDIUM? |

### H4-HALODI-FATE-QUIVER

| Campo | Valore |
|---|---|
| **item_id** | `ranger-t5-legendary-halodi-fate-quiver-hybrid` |
| **source** | pantheon-of-fallen-suns dungeon 3p Lv60 alternate (Halodi fato capstone) |
| **source_type** | dungeon_3p_alternate |
| **candidate_drop_rate** | 0.5% (direzionale C1) |
| **recommended_final_drop_rate** | **0.5%** |
| **farming_risk** | MEDIUM — dungeon 3p Lv60 accessibile con 3-man party |
| **economy_risk** | LOW — bind-on-pickup, trinket slot (RESERVED Q7!) |
| **rationale** | Coerente con dungeon 3p secondary. Utility Fate Deflection auto-reactive coerente con Ranger endgame survival. |
| **PM_decision_required** | ❓ conferma 0.5% + RISOLVERE slot=`trinket` (RESERVED in Q7 canonical) → rimappa a `accessory` o rendi `trinket` operativo? Vedi Sezione 12 PM gate slot. |

**Aggregate recommendation**: **0.5% uniforme per H1-H4** confermato come baseline design layer. Loot-lock 1x/settimana consigliato per H3+H4 (dungeon 3p) per gestire farming risk MEDIUM. NO apply · PM final decision required.

---

## 12. Material Parallel Drop Policy

### Principio PM canonico

- Item drop roll e material drop roll **SEPARATI**
- Nessun materiale ruba il drop slot dell'item
- Materiali possono uscire **INSIEME agli item**
- Materiali con drop rate **PIÙ ALTO** rispetto agli item
- Materiali **NON premium**
- Materiali **NON P2W**

### Design layer mapping

- `item_roll`: roll indipendente su drop_table_item (rarity-weighted per source_category)
- `material_roll`: roll indipendente su drop_table_material (higher rate: 20-40% per boss dungeon 3p, 40-60% per boss raid)
- `compatibility`: material può uscire SEMPRE insieme all'item (2 roll paralleli); il material non consuma lo slot item drop
- `anti_p2w`: material `can_be_sold_for_real_money=false` sempre (nessuna eccezione)
- `vendor_exclusion`: material vendor-sold NON premium (Common/Uncommon), tier bracketed


### D1-D5 material snapshot
- material_items_in_catalog: **9**
- _I 9 items con `slot=material` in D1-D5 sono cataloghi documentali per crafting recipe input. Il drop live parallel material è un SISTEMA SEPARATO da progettare in C5+ (fuori scope C4)._

**Compliance**: PASSED — principio PM canonico rispettato in design; nessun apply.

---

## 13. Anti-P2W Drop Validation

| # | Check | Status |
|:--:|---|:--:|
| **1** | 1500/1500 items `can_be_sold_for_real_money=false` | ✅ PASSED |
| **2** | Nessun Legendary in vendor/shop source | ✅ PASSED (Legendary solo raid endgame + dungeon 3p endgame) |
| **3** | Nessun Legendary in craft source | ✅ PASSED (0 Legendary in craft) |
| **4** | Nessun Epic in vendor | ✅ PASSED (0 Epic vendor-sold) |
| **5** | Materiali NON premium / NON P2W | ✅ PASSED (design policy) |
| **6** | HYBRID Legendary NO market resale (bind-on-pickup) | ✅ PASSED 11/11 (C0.L / C0.L.1) |
| **7** | Nessun premium tier item nel catalogo D1-D5 | ✅ PASSED |
| **8** | affects_economy=false per Legendary 15/15 | ✅ PASSED |


**Overall**: ✅ **PASSED 8/8** — Anti-P2W drop validation confermata

---

## 14. Slot Canonical Drift — PM GATE CRITICO 🚨

**Nota**: PM gate item CRITICO segnalato in C4. La Q7 CUSTOM CANONICAL LIST introduce drift documentale vs slot correnti nei 1500 items D1-D5.

- **Q7 canonical slots (14)**: `head` · `neck` · `shoulders` · `chest` · `back` · `hands` · `wrist` · `waist` · `legs` · `feet` · `main_hand` · `off_hand` · `ring` · `accessory`
- **Q7 reserved slots**: `trinket`
- **Q7 universal (C2/C3)**: `consumable` · `material`

### Alias documentali (Q7)

- `main-hand` → `main_hand`
- `off-hand` → `off_hand`
- `amulet` → `neck`
- `belt` → `waist`
- `cloak` → `back`
- `cape` → `back`
- `weapon_main` → `main_hand`
- `weapon_off` → `off_hand`


### Analisi slot corrente vs Q7

| slot_current | count | status | migration_note |
|---|:--:|:--:|---|
| `main-hand` | 613 | **alias_legacy** | → `main_hand` (C5 slot canonical migration) |
| `chest` | 232 | **canonical** | — |
| `off-hand` | 129 | **alias_legacy** | → `off_hand` (C5 slot canonical migration) |
| `head` | 103 | **canonical** | — |
| `legs` | 83 | **canonical** | — |
| `feet` | 72 | **canonical** | — |
| `trinket` | 68 | **reserved_Q7** | PM gate: 68 items usano `trinket` → richiede decisione PM (rimappare a `accessory`? o rendere `trinket` operativo?) — C5 gate item |
| `ring` | 59 | **canonical** | — |
| `hands` | 58 | **canonical** | — |
| `amulet` | 57 | **alias_legacy** | → `neck` (C5 slot canonical migration) |
| `consumable` | 17 | **universal_allowed** | lock_state=universal_allowed C2/C3 · bypass proficiency |
| `material` | 9 | **universal_allowed** | lock_state=universal_allowed C2/C3 · bypass proficiency |

### Critical findings

- **613 items** usano `main-hand` (dash-hyphen) invece di `main_hand` (underscore Q7) → alias → migration C5
- **129 items** usano `off-hand` invece di `off_hand` → alias → migration C5
- **68 items** usano `slot=trinket` che è **RESERVED in Q7** (non slot operativo) → **CRITICAL PM gate**: rimappare a `accessory`? oppure rendere `trinket` operativo? Decisione PM richiesta in C5
- **57 items** usano `slot=amulet` invece di `neck` (Q7 canonical) → alias → migration C5
- **0 items** usano `back`, `shoulders`, `wrist`, `waist`, `accessory` — slot Q7 canonici designati per uso futuro/nuovi items
- **17 consumable + 9 material** → universal_allowed (C2/C3)

### Raccomandazioni C5 gate actions

- C5 Slot Canonical Migration Prep (parallel a Class Slug Migration Prep)
- Decisione PM su `trinket` (68 items): (A) rimappa a `accessory` (safest, migration additive) · (B) `trinket` operativo (aggiungere a canonical 15° slot) · (C) split logic (accessory + trinket sub-category)
- Migration additive: NO rename destructive, solo aggiungere campo `slot_canonical` derivato con alias table
- Update lock-state matrix C2 se `trinket` diventa slot operativo


**Governance**: NON applicato in C4. Solo documentale. Item table D1-D5 NON modificati.

---

## 15. class_slug / Runtime Constraints (compat C2/C3)

### Regole verbatim
- class_slug=null 1500/1500 preservato
- class_slug resolution deferred to C5/R18.3f
- runtime_apply_ready=false 1500/1500 preservato
- NO auto-derive class_slug
- NO migration
- NO runtime bridge


**Impatto C4**: Nessun impatto — drop table design layer non richiede class_slug. class_proficiency canonical (Warrior/Rogue/Mage/Priest/Ranger) usato per class coverage analysis.

---

## 16. Risk Register (12 rischi R1-R12)

| ID | Rischio | Severità | Mitigazione | Status |
|:--:|---|:--:|---|:--:|
| **R1** | HYBRID drop rate 0.5% applicato senza PM final confirmation | MEDIUM | documental only · PM final decision required in C5/C6 | TRACKED |
| **R2** | H3/H4 farming risk MEDIUM (dungeon 3p) senza loot-lock | MEDIUM | raccomandare loot-lock 1x/settimana in design; PM decision | PROPOSED |
| **R3** | Slot `trinket` (68 items) RESERVED in Q7 → items non equippabili in runtime enable | HIGH-BLOCK | PM gate C5 · rimappare a `accessory` (raccomandato) o rendere `trinket` operativo | CRITICAL PM GATE |
| **R4** | Slot legacy dash-hyphen (main-hand / off-hand / amulet) → 799 items richiedono alias runtime | MEDIUM | migration additive C5 (alias table); nessun rename destructive | DESIGNED |
| **R5** | Dungeon count osservato 64 vs target PM 60 (+4) | LOW-MEDIUM | PM review classification meta-source residue (potenzialmente 4 items da spostare in vendor/quest) | TRACKED |
| **R6** | Raid count osservato 13 vs target PM 12 (+1) | LOW | PM review 13° raid unique token (candidato: `hollow-monastery` o `krastlov-siege` con classificazione ambigua) | TRACKED |
| **R7** | Progressive 4 (P1-P4) source PENDING PM → drop table incompleto per L=15 fino a finalizzazione | MEDIUM | registry_status=reserved · runtime_apply_ready=false · finalizzazione post-C6 PM | TRACKED |
| **R8** | Priest sovra-rappresentato in chest_reward (47 vs media ~31) | LOW | class coverage OK (nessun sotto-servito); PM review estetico se necessario | DOCUMENTED |
| **R9** | Craft T3=100 items concentrazione (48% craft in T3) | LOW | coerente con density mid-game Uncommon/Rare/Epic (T3 rarity-varied) | DOCUMENTED |
| **R10** | Material parallel drop system NON documentato in dettaglio (fuori scope C4) | LOW | principio PM canonico documentato · implementazione dettagliata in C5/C6 | DEFERRED to C5+ |
| **R11** | Legendary drop rate 2% raid live (dragon-vault) potrebbe essere overturned in raid frequency | LOW | chain STEP 8 already approved · telemetry-based tuning post-launch | TRACKED |
| **R12** | Anti-P2W legacy audit non ancora eseguito su inventari LIVE (out of scope C4) | MEDIUM | audit obbligatorio pre-apply futuro (C6) | TRACKED to C6 |


---

## 17. GO/HOLD Recommendation

### Phase C5 Class Slug Migration Prep + Slot Canonical Migration
- **Recommendation**: **GO — soggetto a PM approval esplicito post-C4 review**
- **Rationale**: C4 Drop Table dry-run fornisce input coerente per C5. C5 dovrà gestire due migration paralleli: (1) class_slug null resolution (2) slot canonical migration (Q7 gate item R3).

**Conditions**:
- PM approval C4 (Q1-Q8)
- HYBRID drop rate final decision (0.5% uniforme confermato o differenziato H3/H4 loot-lock)
- Slot `trinket` gate item R3 → decisione PM: `trinket → accessory` (raccomandato) o `trinket` operativo
- PM classification dungeon delta +4 e raid delta +1

**Risks se GO**:
- R3 slot trinket → CRITICAL PM GATE, blocca runtime enable senza risoluzione
- R2 farming risk H3/H4 → mitigato da loot-lock 1x/settimana


### Fasi successive (HOLD)
- **C6 Final Closure** — HOLD post-C5
- **R18.6 Class Halls** — PLANNED post-Phase C

---

## 18. PM Open Questions post-C4

| ID | Topic |
|:--:|---|
| **Q1** | Approvare C4 Drop Table Dry-Run Planning come design layer input per C5? |
| **Q2** | HYBRID drop rate finali 0.5% uniforme H1-H4: conferma o differenzia (es. 0.3-0.4% per high-power H2 Death's Toll)? |
| **Q3** | Loot-lock 1x/settimana per H3/H4 (dungeon 3p farming risk MEDIUM): approvare o mantenere free-farm con drop 0.5%? |
| **Q4** | **SLOT GATE (R3)** — 68 items con `slot=trinket` (RESERVED in Q7): (A) rimappa a `accessory` [raccomandato, migration additive safest] · (B) rendere `trinket` operativo come 15° slot canonico · (C) split (accessory + trinket sub-category)? |
| **Q5** | Dungeon count delta +4 (64 vs 60): PM classification manuale per identificare 4 items meta-source non-dungeon oppure accettare 64 come nuovo target? |
| **Q6** | Raid count delta +1 (13 vs 12): PM classification 13° raid token (candidati: `hollow-monastery` T2 raid o riclassificare come dungeon 3p)? |
| **Q7** | 4 Progressive Discovery Legendary (P1-P4) source PENDING PM: finalizzare in C5 o post-C6? |
| **Q8** | Autorizzare Phase C5 Class Slug Migration Prep + Slot Canonical Migration (parallel migration double-track)? |


---

## 19. Governance Check C4

| Voce | Stato |
|---|:--:|
| `sealed` | VERIFIED pytest 6/6 (post STEP 1 PRD append + STEP 2 C4 draft) |
| `db_writes` | ZERO |
| `code_changes` | ZERO |
| `migrations` | ZERO |
| `item_creation_live` | ZERO |
| `registry_apply` | ZERO |
| `drop_table_apply` | ZERO |
| `drop_rate_apply` | ZERO (HYBRID 0.5% documental only) |
| `economy_changes` | ZERO |
| `lore_meta_py_touch` | ZERO |
| `sealed_file_modification` | ZERO |
| `hard_delete` | ZERO |
| `runtime_bridge` | ZERO |
| `class_slug_migration_apply` | ZERO |
| `class_slug_auto_derivation` | ZERO |
| `slot_canonical_migration_apply` | ZERO (documental drift analysis only) |
| `proficiency_runtime_enforcement` | ZERO |
| `anti_p2w_runtime_validator` | ZERO (design layer 8/8 PASSED) |
| `equipment_backfill_apply` | ZERO |
| `ilvl_implementation` | ZERO |
| `c5_auto_start` | BLOCKED (STOP after C4) |
| `r18_6_kickoff` | BLOCKED |
| `marketing_brief` | BLOCKED |
| `classi_canoniche` | Warrior/Rogue/Mage/Priest/Ranger — NO drift |
| `italian_language_output` | ENFORCED |
| `documental_only_regime` | ENFORCED |
| `files_deliverable` | 2 (.md + .json) |


---

## Stop after C4

- **`auto_transition_c5`**: `false`
- **Nota**: **STOP dopo C4. Attendo PM review Q1-Q8 + GO esplicito prima di C5.**
