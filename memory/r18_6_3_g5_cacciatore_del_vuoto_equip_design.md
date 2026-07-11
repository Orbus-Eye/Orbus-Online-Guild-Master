# R18.6.3-G5 EQUIP_DESIGN · Cacciatore del Vuoto

**Gate**: R18.6.3-G5 · **Scope**: EQUIP_DESIGN · **Class Pilot**: Cacciatore del Vuoto (`cacciatore_del_vuoto`)
**Generated**: 2026-07-08T20:15:00Z · **Status**: DRAFT · pending PM review
**Governance**: DOCUMENTAL ONLY · no code · no DB · no migrations · no Registry v3 generation · no item rows · no drop tables · no crafting
**Seals anchor**: `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`
**Predecessor gates LOCKED**: R18.5 · R18.6 · R18.6.1 · R18.6.2 · G1 · G2 · G3 · G4
**Successor gate**: R18.6.3-G6 PLAYER_GUIDE (HOLD · attende G5 CLOSED)
**Canonical validation**: PASS · zero non-canonical class references

---

## Sezione 1 · Budget equip per tier (T1-T5)

| Tier | Level | Multiplier | Int direction | Sockets | Affix slots | Focus stat |
|---|---|---|---|---|---|---|
| **T1 Aspirante** | 1-15 | 1.00 | 10-25 | 0 | 1 | Int dominante · no proc Int |
| **T2 Cacciatore** | 16-30 | 1.35 | 25-45 | 0 | 2 | Int + vit sec · Int proc 10-20% |
| **T3 Iniziato** | 31-45 | 1.75 | 45-70 | 0-1 | 3 | Int dominante · Int 50 = +1 Marchio · proc 20-30% |
| **T4 Rituale** | 46-55 | 2.20 | 70-100 | 1-2 | 4 | Int 90 = +1 Marchio (cap 5) · proc 30-40% |
| **T5 Vuoto** | 56-60 | 2.70 | 90-115 (soft cap Int=100 non-minimum · linear-flattening) | 2-3 | 5 | Int soft cap 100 target progressione + diminishing returns · proc 45% cap · Marchio 8T (hard cap 10T) |

**Note gate isolation**: Budget direzionale · NO formule runtime · G6+ finalizza display · Registry v3 (HOLD) consumerà.

## Sezione 2 · Budget per rarity (Common-Legendary)

| Rarity | Multiplier | Affix count | Sockets max | Legendary utility |
|---|---|---|---|---|
| Common | 1.00 | 0-1 | 0 | No |
| Uncommon | 1.15 | 1-2 | 0 | No |
| Rare | 1.35 | 2-3 | 1 | No |
| Epic | 1.60 | 3-4 | 1-2 | No |
| **Legendary** | **1.85** | 4-5 | 2-3 | **YES** · ILVL=60 lock · utility_unique NO overrides |

**Rationale**: multiplier progression smooth · no step function · Legendary utility_unique senza overrides stat · anti-power-creep preservato · Legendary semantic G1 LOCK: `Legendary ILVL = 60 · nessun bonus Intelligenza pari a 60 aggiunto (utility_unique NON stat scaling override)`.

## Sezione 3 · Scaling qualitativo weapon

- **Concept**: scaling qualitativo · direzione relativa · **NO formule runtime · NO Destrezza scaling · NO parificazione balestra/focus**
- **Int dominance**: LOCK · Int primary scaling · linear-flattening Int 100+ (G1 SD-Q1 LOCK)
- **No dual scaling**: LOCK · Int single-stat · nessun override secondary

## Sezione 4 · Coefficienti direzionali Focus / Balestra / Pugnale

| Weapon | Throughput baseline | Identity | Trade-off |
|---|---|---|---|
| **focus** | **1.00** (baseline) | throughput arcano primario · applicazione Marchio · Drain principale · Payoff channeling · max 1 (PD-Q1 LOCK) | posizionamento mid-range · fragile |
| **balestra** | **0.85-0.90** (inferiore) | canalizzazione arcana ranged 2H · Drain ranged · sicurezza posizionale | throughput inferiore compensato da range · blocca off_hand (opportunity cost) |
| **pugnale** | **0.70-0.80** (inferiore sostenuto) | rituale off_hand default · ritual close +1F max 1× per Marchio · finisher opportunistico | damage sostenuto ridotto compensato da ritual close + burst opportunity |

**Relative order LOCK**: `focus > balestra > pugnale` (throughput arcano sostenuto)
**Identity asymmetry LOCK**: nessuna weapon flat superior · trade-off meaningful choice
**Gate 5 boundary**: SOLO direzione qualitativa · NO coefficienti runtime · Registry v3 (HOLD) consumerà

## Sezione 5 · Distribuzione stoffa/cuoio

| Tier | stoffa | cuoio | Note |
|---|---|---|---|
| T1 | 55% | 45% | balanced onboarding |
| T2 | 55% | 45% | balanced |
| T3 | 60% | 40% | shift Int focus emerge |
| T4 | 65% | 35% | endgame rituale · stoffa dominante |
| T5 | 70% | 30% | Legendary stoffa 3-4 · cuoio niche hybrid movement |

- **stoffa identity**: rituale · Int scaling primario · Marchi/Drain efficacy bonus tendenziale · fragilità accepted
- **cuoio identity**: hybrid · Int scaling primario ma secondary movement/positioning · niche builds che sacrificano throughput per survivability
- **No dual stat Int/Dex**: LOCK G2 · anche cuoio è Int-focus non hybrid

## Sezione 6 · Identità slot (14 canonical + universal_allowed)

| Slot | Class-specific | Universal allowed | Type |
|---|---|---|---|
| helmet | YES | NO | stoffa/cuoio |
| shoulders | YES | NO | stoffa/cuoio |
| chest | YES | NO | stoffa/cuoio |
| gloves | YES | NO | stoffa/cuoio |
| belt | YES | NO | stoffa/cuoio |
| legs | YES | NO | stoffa/cuoio |
| boots | YES | NO | stoffa/cuoio |
| cloak | NO | **YES** | universal |
| main_hand | YES | NO | focus/balestra_2h/pugnale |
| off_hand | YES | NO | pugnale (bloccato se balestra 2H) |
| neck | NO | **YES** | universal |
| ring1 | NO | **YES** | universal |
| ring2 | NO | **YES** | universal |
| trinket | YES | (accetta anche universal) | reliquia rituale class-specific |

- **Total slots**: 14
- **Universal_allowed count**: 4 (cloak · neck · ring1 · ring2)
- **Class-specific slots**: 10 + trinket flessibile
- **Lanterna**: NON assegnata a slot (decisione G5 NON_NECESSARIA · vedi sezione 13)

## Sezione 7 · Affix class-specific (10 famiglie obbligatorie)

| ID | Famiglia | Effetto concept | Slots eligible | Hard cap alignment |
|---|---|---|---|---|
| 1 | **Potenza Marchio** | ↑ rank arcano Marchio (DoT intensity qualitativa · silence robustness) | helmet/chest/trinket/main_hand | NON supera durata 10T · NON aumenta Marchi cap 5 |
| 2 | **Durata Marchio** | estende durata base qualitativo/direzionale | helmet/shoulders/chest/trinket | hard cap 10T LOCK G4 RM-Q5 |
| 3 | **Efficacia Drain** | ↑ proc chance +1F stack cap · combined ≤ 50% ceiling | gloves/main_hand/off_hand/trinket | proc 50% max · no uncapped scaling |
| 4 | **Qualità dispel (rank)** | eleva rank arcano rimosso da 3F Payoff | main_hand/off_hand/trinket/cloak | rank leggendario boss immune preserved G4 |
| 5 | **Interazione Frammenti** | modifica qualitativa (UI/flavor/shortening 0.1T · NO cap increase) | belt/trinket/off_hand | resource_cap 5 LOCK G4 RM-Q1 |
| 6 | **Efficacia Payoff** | ↑ reliability qualitativa · summon standard = 100% deterministico preserved | chest/trinket/main_hand | anti-random-waste safeguard G4 RM-Q4 |
| 7 | **Bonus anti-incorporeo** | ↑ gen extra su incorporei marchiati · durata DoT | gloves/main_hand/trinket | identity anti-arcano tematica |
| 8 | **Bonus anti-summon** | ↑ durata silenziamento +0.5T · reliability annullamento boss add-summon | shoulders/cloak/trinket | boss diretto MAI silenziato G4 LOCK |
| 9 | **Mobilità durante canalizzazione** | slow move durante focus channel · riduce penalty posizionamento | boots/legs/belt | no free movement · anti-cheese knockback |
| 10 | **Protezione durante rituali** | riduce danno Payoff cast 1T · riduce interrupt short-CC | chest/shoulders/cloak | MAI immunità hard-CC boss enrage/stun leggendario |

## Sezione 8 · Affix VIETATI (14 regole esplicite)

- ❌ `+resource_cap` (Frammenti oltre 5) · **G4 RM-Q1 LOCK**
- ❌ Marchi attivi oltre hard cap 5 · **G4 RM-Q5 LOCK**
- ❌ Durata Marchio oltre 10T hard cap · **G4 RM-Q5 LOCK**
- ❌ Proc genera Frammenti da target NON Marchiati · **G4 anti-cheese LOCK**
- ❌ Bypass boss safeguard (dispel immunity · silence hard-cast · enrage cancel · boss diretto)
- ❌ Annullamento boss diretto · **G4 RM-Q4 LOCK**
- ❌ Bonus P2W · `can_be_sold_for_real_money=false` obbligatorio
- ❌ Doppio scaling Int/Dex · **G1 SD-Q1 LOCK**
- ❌ Gear migliore per Mago/Rogue/Ranger (cross-class optimal)
- ❌ Channel bonus focus oltre max 2/segmento risorsa · **G4 RM-Q2 LOCK**
- ❌ Ritual close pugnale oltre 1×/Marchio · **G4 RM-Q3 LOCK**
- ❌ PvP untested effect · **G4 RM-Q7 HOLD**
- ❌ Preserva Frammenti cross-fase maggiore · **G4 RM-Q6 LOCK**
- ❌ Chance fallimento casuale su summon standard · **G4 anti-random-waste safeguard LOCK**

## Sezione 9 · Gear sharing analysis

### vs Mago (Int shared · MEDIUM-HIGH overlap)
- Stat shared: **Intelligenza** · armor shared: **stoffa** · weapon shared: **focus**
- Mitigation: class_proficiency lock (Mago no balestra/pugnale · Vuoto no tomo/bastone/reliquia) · affix class-specific 1-10 targettate Marchio/Drain/Frammenti/Payoff · trinket class-specific · set bonus futuri class_slug lock

### vs Ladro/Rogue (Dex diverso · LOW overlap)
- Stat: nessuno shared (Dex vs Int) · armor: **cuoio** shared · weapon: **pugnale** shared
- Mitigation: main_stat divergence · pugnale gameplay divergente (Ladro=bleed/finisher · Vuoto=ritual close)

### vs Cacciatore di Mostri/Ranger (Dex diverso · LOW overlap)
- Stat: nessuno shared · armor: **cuoio** shared · weapon: **balestra + pugnale** shared
- Mitigation: **canonical differentiation LOCK G3** · balestra semantic split (fisica scaling Dex hunting vs canalizzazione arcana scaling Int) · main_stat divergence Int vs Dex

### Universal_allowed slots (4)
- cloak · neck · ring1 · ring2 · affix universali (vitalità/mana/regen/movement) · NO class-specific affix su universal (anti-monopolio)

## Sezione 10 · Registry v3 requirements/dependencies

**Status**: **HOLD** · G5 produce SOLO requirements · NON genera items · NON modifica R18.5 catalog

**Dependencies (G1-G4 LOCK)**:
- class_proficiency schema (G2) · class_stat_scaling schema (G1) · resource_mechanic schema (G4) · gameplay_loop schema (G3) · canonical_class_registry (R18.6.1)

**Additive fields needed**:
- `class_slug` (`cacciatore_del_vuoto` snake_case)
- `armor_whitelist` (`["stoffa", "cuoio"]`)
- `weapon_whitelist` (`["focus", "balestra", "pugnale"]`)
- `resource_ref` (`Frammenti di Onirade`)
- `affix_class_specific_families` array (10 famiglie)
- `affix_forbidden_rules` array (14 regole)
- `budget_per_tier_ref` (T1-T5) · `budget_per_rarity_ref` (Common-Legendary)
- `ilvl_formula_ref` (G1 formula) · `legendary_semantic_ref` (`Legendary ILVL = 60 non +60 Int`)
- `hard_cap_lock_flags` (resource_cap=5 · marchi_max=5 · durata_max=10T · proc_max=45-50% · reliability_max=98%)

**Constraints**: NO new registry rows · NO new item IDs · NO bridge apply · NO class unlock · NO Hall activation

**Roadmap post-G5**: `R18.6.RV3 Registry v3 Additive Planning Gate` (currently HOLD · authorization dopo G5 CLOSED + PM ACK)

## Sezione 11 · Item quantity proposal (motivata · NO 80-100 target lockato)

**Proposta**: **≈ 110-130 items** class-specific + universal-eligible

| Tier | Armor set | Weapon | Accessory/Trinket | Total |
|---|---|---|---|---|
| T1 | 7 (Common) | 3 (Common) | 0 | **~10** |
| T2 | 14 (Common+Uncommon stoffa/cuoio) | 6 (2 rarity) | 4 (universal) | **~24** |
| T3 | 14 (Uncommon+Rare) | 6 | 5 (+1 trinket class-specific) | **~25** |
| T4 | 14 (Rare+Epic) | 6 | 5 | **~25** |
| T5 | 14 (Epic+Legendary) | 6 | 6 (incl. 2 Legendary trinket utility_unique) | **~26** |
| **TOTAL** | | | | **~110-130** |

**Rationale**:
- Copertura minima ma completa T×R (non tutti popolati · anti-inflation)
- 3 weapon type × 5 tier × 2 rarity min = 30 weapon (+ 4 Legendary utility_unique)
- Armor 7 slot × 5 tier × ~2 rarity = ~70 armor
- Accessory universal 4 slot × 5 tier × 2 rarity = ~40 (partial cross-class)
- Trinket class-specific 5 tier × 2 rarity + 2 Legendary = ~12

**Flexibility note**: PM può ridurre T1-T3 mainstream (~60-75) OR espandere T4-T5. Non è 80-100 target lockato: proposta motivata pilot Vuoto.

## Sezione 12 · Famiglie item

**Armor families**: `stoffa_rituale` (rituale · Int scaling · 7 slot × 5T × 2R) · `cuoio_hybrid_movement` (hybrid · Int-focus con secondary movement)

**Weapon families**: `focus` (rune arcano primary · 5T × 2R + 2 Legendary T5) · `balestra_arcana` (2H canalizzazione · 5T × 2R + 1 Legendary T5) · `pugnale_rituale` (rune blade off_hand · 5T × 2R + 1 Legendary T5)

**Accessory families**: `cloak_universal` · `neck_universal` · `ring_universal` × 2 slots · `trinket_class_specific` (reliquia rituale Vuoto · 5T × 2R + 2 Legendary utility_unique)

**Progression buckets**: onboarding T1-T2 (loop learning) · midgame T3-T4 (affix attivi · rituale identity emerging) · endgame T5 (Legendary utility_unique · knee point Int 100)

## Sezione 13 · Lanterna necessity decision

### 🎯 DECISION: **NON_NECESSARIA**

**Verdict**: Lanterna **NON necessaria** per Cacciatore del Vuoto readiness pilot.

**Consequence**:
- Lanterna resta **RESERVED permanente**
- Rimossa da roadmap readiness Vuoto
- **Sub-gate `R18.6.LTN` NON aperto**
- NON pre-Registry v3 requirement

**Rationale**:
1. G2 weapon whitelist LOCKED (focus/balestra/pugnale) · aggiungere Lanterna richiederebbe rework G2 non giustificato
2. Loop 4-step Identify/Mark/Drain/Payoff (G3 LOCK) è coperto dai 3 weapon: focus=rituale primary · balestra=ranged safety · pugnale=melee ritual close
3. 3 axis weapon copertura completa: throughput arcano · range/sicurezza · finisher rituale · **nessun gap gameplay identificato**
4. Anti-power-creep: più weapon = più gear pool = più budget · **NO ROI positivo** dato che 3 weapon già coprono asse identity
5. Distinctness: Lanterna può collidere con concetti future Mago/Chierico (holy/light themes) · Vuoto identity anti-arcano si esprime meglio con focus/balestra/pugnale rituali
6. Nessuna PM directive esplicita richiede Lanterna · G5 decision-space per readiness pilot

**Future reactivation conditions** (opzionale):
- Gate futuro PvP class effect normalization
- PM directive post-launch che introduce identity gap non coperto
- Legendary utility_unique T5 gate futuro come slot esoterico dedicato (NON T1-T5 mainstream)

**Roadmap action**: rimuovere Lanterna da readiness Vuoto · mantenere RESERVED permanent per uso futuro non-Vuoto/out-of-scope

## Sezione 14 · Compatibilità ILVL (formula G1)

**Formula LOCK G1**: `min(max(required_level + rarity_offset, tier_min), 60)`

| Rarity | Offset |
|---|---|
| Common | 0 |
| Uncommon | +2 |
| Rare | +5 |
| Epic | +10 |
| Legendary | +15 |

**Tier min**: T1=1 · T2=16 · T3=31 · T4=46 · T5=56 · **ILVL hard cap: 60**

**Legendary ILVL LOCK**: **60** · semantic `Legendary ILVL = 60 · nessun bonus Intelligenza pari a 60 aggiunto (utility_unique NON stat scaling override)` · affix non può alterare ILVL Legendary (resta 60)

**Esempi**:
- T2 Common lvl 20 → `min(max(20+0, 16), 60)` = **20**
- T3 Rare lvl 40 → `min(max(40+5, 31), 60)` = **45**
- T5 Legendary lvl 60 → `min(max(60+15, 56), 60)` = **60** (hard cap · Legendary ILVL=60 semantic LOCK)

**No runtime execution G5**.

## Sezione 15 · Legendary utility interaction

**Semantic LOCK G1 preserved**: `Legendary ILVL = 60 · nessun bonus Intelligenza pari a 60 aggiunto (utility_unique NON stat scaling override)`

**Utility_unique examples concept** (quality-of-life · MAI stat overrides):
- **Legendary Focus T5 "Focus di Onirade"**: Payoff 5F cast time 0.5T invece di 1T (utility quality)
- **Legendary Trinket T5 A "Sigillo del Vuoto"**: Marchio applicato applica silence +0.5T (soft · rispetta hard cap 10T)
- **Legendary Trinket T5 B "Cuore di Onirade"**: Payoff 3F feedback visual/audio esteso (QoL · no stat)

**Guarantees**:
- NO stat scaling overrides
- NO cap bypass
- NO hard cap alteration
- NO P2W advantage
- Progressive Discovery Legendary P1-P4 gate futuro (HOLD) rispetterà semantic LOCK

## Sezione 16 · Anti-power-creep

- ✅ Int soft cap 100 linear-flattening preserved
- ✅ Frammenti cap 5 hard NO affix bypass · **G4 RM-Q1 LOCK**
- ✅ Marchi cap 5 hard NO affix bypass · **G4 RM-Q5 LOCK**
- ✅ Marchio duration 10T hard cap NO affix bypass · **G4 RM-Q5 LOCK**
- ✅ Proc 50% ceiling combined Int+affix
- ✅ Reliability 98% ceiling
- ✅ Legendary utility_unique NO overrides
- ✅ NO dual scaling Int/Dex · **G1 LOCK**
- ✅ NO boss bypass affix
- ✅ NO cross-class optimal gear
- ✅ Channel bonus max 2/segmento · **G4 RM-Q2 LOCK**
- ✅ Ritual close max 1×/Marchio · **G4 RM-Q3 LOCK**
- ✅ NO phase reset bypass · **G4 RM-Q6 LOCK**
- ✅ NO random-waste 5F · **G4 RM-Q4 LOCK**
- **Budget progression smooth** T1→T5 1.0→2.7 · rarity Common→Legendary 1.0→1.85 · combined max ~5.0x (MMO tradition)
- **15 safeguards summary rules**

## Sezione 17 · Anti-P2W

- `can_be_sold_for_real_money=false` LOCK (R18.5 1500/1500)
- NO exception Vuoto · NO premium boost · NO paywall endgame · NO energy purchase advantage · NO stat cosmetic
- **Cosmetic-only pay allowed**: solo cosmetic pure NO-stat (R18.5 conforme)
- Affix forbidden rule_7 (P2W bonuses) LOCK

## Sezione 18 · Risk register + PM Open Questions + GO/HOLD

**Risk Register (15 rischi tracciati)** — highlights:
- EQ-R1 Budget T5 endgame trivial (MEDIUM · DESIGNED)
- EQ-R2 Item quantity 110-130 onerosa (MEDIUM · **OPEN_FOR_PM**)
- EQ-R4 Gear sharing Mago clone visivo (MEDIUM · TRACKED PG1)
- EQ-R6 Legendary utility_unique ambigua rischio stat sneak (MEDIUM · TRACKED PG1)
- EQ-R8 Cuoio niche T5 30% (MEDIUM · DESIGNED)
- EQ-R10 Registry v3 additive fields consumption error (MEDIUM · TRACKED PG2)
- EQ-R13 Set bonus futuri rompere anti-power-creep (MEDIUM · TRACKED PG3)
- EQ-R15 PvP HOLD frena adozione competitive (LOW-MEDIUM · TRACKED PG3)

### PM Open Questions (EQ-Q1..EQ-Q8)

- **EQ-Q1** · *Item quantity 110-130 o T1-T3 (~60-75)?* → **a) LOCK 110-130**
- **EQ-Q2** · *Lanterna NON_NECESSARIA LOCK?* → **b) NON_NECESSARIA now · reserved future review**
- **EQ-Q3** · *Distribuzione stoffa/cuoio T5 70/30?* → **a) LOCK 70/30**
- **EQ-Q4** · *Rarity multiplier Legendary 1.85x?* → **a) LOCK 1.85x**
- **EQ-Q5** · *Proc combined 50% ceiling?* → **c) LOCK 45% (nessun affix bypass Int cap)**
- **EQ-Q6** · *Universal_allowed 4 slot?* → **a) LOCK 4 slot**
- **EQ-Q7** · *Weapon coefficient direzionali?* → **a) LOCK direzione qualitativa**
- **EQ-Q8** · *Registry v3 Additive Planning Gate post-G5 CLOSED?* → **a) authorize post-G5 CLOSED**

### GO/HOLD Gate 6 PLAYER_GUIDE

- **Gate 5 status**: DRAFT · pending PM review + risposte EQ-Q1..EQ-Q8
- **Gate 6 status**: 🔒 HOLD · attende PM ACK Gate 5 + GO esplicito Gate 6
- **Gate 6 scope preview**: PLAYER_GUIDE onboarding · tooltip italiano · tutorial concept · UX flow · pedagogy loop 4-step · fallback state guidance · SOLO player-facing documentation · NO gameplay implementation · NO Registry v3 · NO drop tables

---

## 🛑 STOP before Gate 6 PLAYER_GUIDE

**Non procedere a Gate 6 senza nuovo GO PM.**
**Non attivare Registry v3 Additive Planning Gate senza nuovo GO PM.**

Attendo PM review Gate 5 + risposte a **EQ-Q1..EQ-Q8**. Nessun auto-start · nessuna modifica R18.5/R18.6/R18.6.1/R18.6.2/G1/G2/G3/G4 (tutti LOCKED).
