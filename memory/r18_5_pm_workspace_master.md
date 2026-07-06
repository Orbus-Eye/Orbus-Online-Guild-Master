> **READ-ONLY MIRROR — authoritative decisions remain in PM gate files.**
> **No new design decisions may be introduced here.**

# R18.5 — PM Workspace Master (READ-ONLY MIRROR)

- **Round**: `R18.5 — Itemization, ILVL & Gear Progression Rework`
- **Sottotitolo**: *Lv60 cap, item-centered endgame, lore-driven equipment*
- **Locked at UTC**: `2026-07-06T19:00:00Z`
- **Status**: **READ-ONLY MIRROR**. Non fonte autoritativa. Non introduce decisioni nuove. Le decisioni restano nei file gate PM linkati.
- **Governance**: DOCUMENTAL ONLY — 36 sigilli byte-identical, zero DB writes, zero code changes.

## File autoritativi (fonti canoniche)

| File | Ruolo |
|:---|:---|
| `r18_5_phase_b1_design_lock.md/.json` (patched) | Design Lock originale + strategic correction (level cap, ILVL, lore-driven) + scale-up correction |
| `r18_5_phase_b2_implementation_plan.md/.json` (patched) | Implementation Plan documentale con correzioni |
| `r18_5_phase_b_gate1_pm_decisions.md/.json` | **Authoritative** su SQ11-SQ18, lore rules, legendary policy micro-batch |
| `r18_5_phase_c0_item_table_drafting_support.md/.json` | Micro-sample 80 item + 13 draft (superseded per scala catalogo reale) |
| `r18_5_phase_c0bis_progression_dungeon_raid_matrix.md/.json` | **Authoritative** su scala catalogo reale (1500 item), 60 dungeon, 12 raid, proficiency system, ordine valutazione equip |

**In caso di conflitto**: Gate 1 prevale su B.1/B.2 su SQ11-SQ18. C0-bis prevale su C0 sulla scala catalogo. Il presente workspace master non è mai autoritativo.

---

## 1. Cheat sheet Gate 1 — SQ11-SQ18

### Level cap & progressione
- `MAX_ADVENTURER_LEVEL = 60` (hard cap gameplay).
- `MAX_EQUIPMENT_REQUIRED_LEVEL = 60`.
- XP oltre Lv60 non aumenta livello. Progressione post-Lv60 = **ILVL / raid / loot / utility / ranking / mercato**.

### SQ11 — Starter → endgame slot transition
Soglia **Lv30**. Starter (Lv1-29): weapon, armor, accessory. Endgame (Lv30+): weapon, helm, chest, legs, accessory, shield.

### SQ12 — Tier / Rarity dual-label + colori
| Tier | Rarity | Colore badge |
|---|---|---|
| T1 | Common | grigio |
| T2 | Uncommon | verde |
| T3 | Rare | blu |
| T4 | Epic | viola |
| T5 | Legendary | oro |

Rarity = label testo primario. Tier = badge secondario. Testo + `aria-label` obbligatori (accessibility, non solo colore).

### SQ13 — Signature policy (micro-batch)
Min 15 / target 18 / max 25. Max 1 signature equipped/adv. Drop-only. No dormant class signature.

### SQ14 — Batch primo lotto (micro)
**Superseded per catalogo reale** (C0-bis sez. 10). Vale ancora come skeleton drafting: 80 item (T1=24/T2=20/T3=20/T4=12/T5=4), max 4 Legendary.

### SQ15 — Endgame dungeon
**"Cripta delle Faglie di Ambash"** (Lv50-60, fonte principale T4/T5).

### SQ16 — min_level / required_adventurer_level
`effective_required_level = required_adventurer_level if exists else min_level`. Dry-run obbligatorio, no auto-fix, no migration senza Gate 2.

### SQ17 — Workshop level per tier
T1=Lv1, T2=Lv2, T3=Lv3, T4=Lv4, T5=Lv5. Signature fuori dal forge.

### SQ18 — Formula equipment_pwr (ILVL-based, dry-run only, no runtime enforce)
```
equipment_pwr = ilvl + tier_bonus + slot_weight_bonus + utility_weight_bonus
```

### Range ILVL per tier
| Tier | ILVL range |
|---|---|
| T1 | 1-15 |
| T2 | 16-30 |
| T3 | 31-45 |
| T4 | 46-55 |
| T5 | 56-60 |

### Tier bonus
| Tier | Bonus |
|---|---|
| T1 | +0 |
| T2 | +3 |
| T3 | +8 |
| T4 | +15 |
| T5 | +25 |

### Slot weight bonus
| Slot | Weight |
|---|---|
| weapon | 1.20 |
| chest | 1.15 |
| helm | 1.00 |
| legs | 1.00 |
| shield | 1.10 |
| accessory | 0.80 |

### Utility weight bonus
| Utility level | Bonus |
|---|---|
| none | +0 |
| minor | +3 |
| major | +8 |
| legendary | +15 |

---

## 2. Lore sources approvate (17 fonti PM verbatim)

Ambash · Irthe · Velur · Efreto · Halodi · Alevora · Soe · Aveol · Ergolat · Krastlov · Adalan · Greatwood/Elfwood · Alberi della Vita · Faglie arcane · Vuoto · Luna Morta · Ciclo delle anime

**Regola**: item T3+ obbligatoriamente `lore_source` + `utility` narrativa lore-linked. Item T1/T2 possono essere generic.

---

## 3. SUPERSEDING NOTE ESPLICITA — Catalogo reale ≠ Micro-batch

| Aspetto | Micro-batch B.1/C0 | **Catalogo reale (C0-bis)** |
|---|---|---|
| Item totali | 80 (skeleton drafting) | **1500 minimo** |
| Legendary max | 4 (micro-batch cap) | **15** (catalogo hard cap) |
| Dungeon | 0 (non pianificati) | **60** (12/14/16/10/8) |
| Raid | 0 (non pianificati) | **12** (2/3/3/4) |
| Proficiency system | non pianificato | **armor + weapon obbligatorie, hard block** |

**Il micro-batch 80/4 NON è più il target reale.** Skeleton drafting valido, non cap.

---

## 4. Regole tassative

### Lore-driven itemization (Gate 1)
- Item T3+ **devono** avere `lore_source` (da lista 17 fonti).
- Item T3+ **devono** avere `utility` narrativa lore-linked.
- Item T3+ **NON** possono essere solo "+stat".

### Proficiency system (C0-bis)
- Armor proficiency **obbligatoria** — se manca, **hard block** runtime.
- Weapon proficiency **obbligatoria** — se manca, hard block.

### Ordine valutazione equip (verbatim PM, C0-bis)
1. **Posso equipaggiarlo?** → proficiency (hard block se no)
2. **È adatto alla classe?** → main stat
3. **Quanto è forte?** → ILVL / rarity / tier
4. **Ha utility?** → effetti / lore / dungeon-specific

### Legendary policy (catalogo reale)
- Max 15 nel catalogo iniziale (hard cap).
- Utility unica obbligatoria.
- Lore source obbligatoria.
- Fonte precisa (raid/boss/dungeon endgame).
- Drop rarissimo. Non craftabili. Non shop. No pay-to-win. No pure stat stick.

---

## 5. Cheat sheet C0-bis — Progression / Dungeon / Raid / Proficiency

### 5 Brackets progression
| Bracket | Semantica | Percezione player |
|---|---|---|
| Lv1-15 | onboarding | *entro nel gioco* |
| Lv16-30 | prime build | *costruisco la squadra* |
| Lv31-45 | salita seria | *capisco build, main stat, equip* |
| Lv46-55 | late game | *farmare e ottimizzare* |
| Lv56-60 | scalata finale | *sto scalando una vetta* |
| Lv60 | endgame ILVL-based | *inizia il vero endgame* |

### 60 Dungeon (distribuzione PM-locked)
| Bracket | # Dungeon |
|---|---:|
| Lv1-15 | 12 |
| Lv16-30 | 14 |
| Lv31-45 | 16 |
| Lv46-55 | 10 |
| Lv56-60 | 8 |
| **Totale** | **60** |

### 12 Raid (distribuzione PM-locked)
| Bracket | # Raid |
|---|---:|
| Lv20-30 (intro) | 2 |
| Lv31-45 (intermedi) | 3 |
| Lv46-55 (late) | 3 |
| Lv60 (endgame) | 4 |
| **Totale** | **12** |

### 1500 Item — distribuzione per tier (PM-locked)
| Tier | Bracket | Count |
|---|---|---:|
| T1 | Lv1-15 | 300 |
| T2 | Lv16-30 | 350 |
| T3 | Lv31-45 | 350 |
| T4 | Lv46-55 | 300 |
| T5 | Lv56-60 | 200 |
| **Totale** | — | **1500** |

### 1500 Item — distribuzione per rarity (PM-locked)
| Rarity | Count |
|---|---:|
| Common | 400 |
| Uncommon | 450 |
| Rare | 400 |
| Epic | 235 |
| **Legendary** | **15** ← hard cap |
| **Totale** | **1500** |

### Armor proficiency (4 tipi PM)
stoffa · cuoio · maglia · piastre

### Weapon families (16 PM)
spada · ascia · martello · pugnale · arco · balestra · bastone · tomo · focus · strumento · falce · lancia · arma in asta · scudo · reliquia · trinket

### Classi live (PM verbatim)
Warrior · Rogue · Mage · Priest · Ranger

### Classi bloccate (no unlock in C0-bis)
CdM · CdV · Berserker (dormant) · Assassin (dormant)

### Bard
Role drift in backlog, no mapping in C0-bis.

### Naming drift osservato (`PENDING PM`)
B.1 Extra D placeholder aveva "Wizard" / "Cleric". PM C0-bis usa "Mage" / "Priest". Da chiarire dal PM.

---

## 6. Item PENDING PM approval attualmente aperti

### Da Gate 1
- SQ11-SQ18 sono **lockate**, ma i valori numerici finali di drop rate, gear check ILVL, coefficienti sono ancora aperti in Phase C tech dry-run.

### Da C0-bis
1. Mapping classe → main stat finale (Warrior Forza vs Costituzione, Ranger Destrezza vs Forza).
2. Mapping classe → armor proficiency finale (matrice 5×4 hard block, impatta identità classe).
3. Mapping classe → weapon proficiency finale (matrice 5×16 hard block).
4. Naming drift Mage/Priest vs B.1 Wizard/Cleric — canonizzazione.
5. Mapping tier↔rarity nel catalogo reale (Gate 1 SQ12 1:1 non è più numericamente coerente con 1500 items).
6. Nomi player-facing dei 60 dungeon.
7. Nomi player-facing dei 12 raid + meccaniche specifiche.
8. Drop rate finali per tier/rarity nei dungeon/raid.
9. Match specifici lore↔dungeon/raid (17 fonti × 60+12 content).
10. Utility narrative delle 15 Legendary + effetti finali.

---

## 7. Nota di consulenza al PM (non decisione)

Il workflow suggerito per sbloccare Phase C tech dry-run:

1. **PM Gate 2** — review C0-bis + risposte agli item PENDING PM sezione 6 (soprattutto proficiency mapping + naming drift, che sono bloccanti per l'identità classe).
2. **Phase C0-ter** (eventuale) — expansion delle proposte C0-bis in item table completa (1500 items compilabile PM), con revisione naming/lore/utility/stat.
3. **Phase C tech dry-run** — scripts backfill (tier, ilvl, is_signature, min_level cross-check) + validation, sempre in dry-run senza apply.
4. **Phase D** — apply post-GO PM dry-run report.

**Non è una decisione, è una proposta di sequenza.** Il PM può cambiare ordine.

---

## 8. Governance recap

- ✅ 36 sigilli byte-identical mantenuti.
- ✅ Zero DB writes.
- ✅ Zero code changes.
- ✅ Distribuzioni PM-locked verbatim ovunque (60=12+14+16+10+8, 12=2+3+3+4, 1500=300+350+350+300+200, rarity=400+450+400+235+15).
- ✅ Legendary count ≤ 15 (catalogo reale) e ≤ 4 (micro-batch).
- ✅ Ogni mapping proposto flaggato `PENDING PM approval`.
- ✅ Naming drift Mage/Priest osservato, non canonizzato.
- ✅ Questo file NON introduce decisioni nuove — è un mirror.

---

*Fine workspace master. Torna sempre ai file gate autoritativi per decisioni definitive.*
