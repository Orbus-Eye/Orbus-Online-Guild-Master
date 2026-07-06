# R18.5 — PWR Solo-Equip + XP Curve Lv60 + Item Tier Rework — Phase A Discovery

- **Round**: `R18.5 — PWR Solo-Equip + XP Curve Lv60 + Item Tier Rework`
- **Fase**: A — Discovery READ-ONLY (audit sistema attuale, no design lock, no naming)
- **Executed at UTC**: `2026-07-06T16:20:00Z`
- **Author**: MainAgent (E1)
- **Governance**: **36 sigilli byte-identical, zero DB writes, zero code changes**.

## 1. Executive summary

Il sistema attuale ha già le **fondamenta parziali** per gli obiettivi R18.5 ma con **gap operativi significativi** che vanno chiusi in Phase B:

- **XP curve**: **già estesa** oltre Lv60. `xp_required_for_level()` in `app/achievements/levels.py` è monotona senza hard cap (safety belt Lv200). Threshold noti: Lv50=289k, Lv60=442k, Lv100=1.36M. Nessun refactor curva necessario, solo eventuale re-tune tra Lv50 e Lv60.
- **Level cap**: **nessun hard cap esplicito** nel codice. Adventurers live sono tutti Lv1 (starter roster) → zero endgame content live giocato. Il gate per dungeon è `enforce_min_adventurer_level` (423 Locked); non c'è un `MAX_LEVEL` sentinel.
- **PWR (Power score)**: **già presente parzialmente**. Item ha `power_score` (numeric 0-60 visto). Adventurer ha `base_power = STR+AGI+INT+END+FAITH + level*2`, `equipment_power = sum(item.power_score per slot)`, `total_power = base + equipment`. Auto-equip usa fitness `primary + secondary + POWER_WEIGHT*power_score + tag_bonus`. **Manca**: PWR-per-tier standardizzato, formula PWR solo-equip (single-adventurer challenge), scaling budget per Lv60.
- **Item tier**: mappato su `rarity` (Common:52, Uncommon:36, Rare:38, Epic:36, Legendary:11 = 173 items totale). **Non esiste** concetto di "Tier" numerico o naming distinto (T1-T5 style). Legendary è il tier massimo attuale.
- **Slot equip**: c'è **doppia granularità**. `item_type` = weapon/armor/accessory/shield. `slot_type` è più granulare (`weapon_main`, `helm`, `chest`, `amulet`, `ring`) ma solo **17 items su 173** usano la granularità piena; il resto ha `slot_type = weapon|armor|accessory` (mapping semplice post-R18.4 SQ1a).
- **Drop table**: `DUNGEON_LOOT_TABLES` in `expeditions/loot_tables.py` con 24 dungeon (`goblin-warrens`, `shadow-crypts`, `dragons-hoard`, etc.). Goblin Warrens: 50% success drop, Common:85% + Uncommon:15%. Progressione già presente a Rare per dungeon endgame. **Manca**: drop di Epic/Legendary da dungeon Lv50-60.
- **Class-bound R18.4**: policy attiva (`item_binding_policy` hard/soft/universal + `slot_type` + `recommended_classes`). Endpoint `/api/adventurers/{id}/eligible-items` live. Badge UI 4-state integrato.

**Gap principali verso R18.5**:
1. PWR solo-equip non ha formula standardizzata (fitness auto-equip esiste ma non è "solo-equip challenge")
2. Item tier è implicito in rarity — R18.5 potrebbe volere Tier esplicito (T1-T5) con range PWR per tier locked
3. `min_level` vs `required_adventurer_level` duplicati sui item docs → rischio integrità
4. Goblin Warrens drop table non copre Rare/Epic → mancano item lv60 endgame
5. Sistema `set_id` (es. `drake_slayer`) esiste ma è opaque → potenziale sistema Set Bonus non ancora esposto

## 2. Stato XP curve attuale

### Formula (`app/achievements/levels.py:40-53`)
- **Lv 1-10**: hand-tuned `_EARLY_CURVE` (Lv1=0, Lv2=100, ..., Lv10=5000).
- **Lv 11+**: `xp_required_for_level(lvl) = 5000 + round((lvl-10)^1.93 * 230)`.
- **Safety belt**: Lv200 (nessun hard cap giocabile).
- **Inverse**: `current_level_for_xp(xp)` con scan lineare O(50).

### Threshold cumulative (verified live)
| Level | XP cumulative |
|---|---|
| 1 | 0 |
| 5 | 900 |
| 10 | 5.000 |
| 20 | 24.576 |
| 30 | 79.596 |
| 40 | 168.144 |
| **50** | **289.252** |
| **55** | **361.803** |
| **60** | **442.260** |
| 70 | 626.670 |
| 80 | 842.080 |
| 100 | 1.364.615 |

### Gap verso Lv60
La curva è **già estesa e monotona**. Lv50→Lv60 richiede ~153k XP (delta 53%). Nessun refactor formula necessario. Eventuale re-tune Lv50-60 può usare `_LATE_CURVE` override table (pattern coerente con `_EARLY_CURVE`).

## 3. Stato level cap / Lv60 readiness

- **Cap live**: nessuno esplicito in codice. Safety belt a Lv200 in `current_level_for_xp`.
- **Adventurers live**: 100% a Lv1 (starter roster non giocato).
- **Guilds live**: 100% a Lv1, xp=None su top 3.
- **Gate operativo**: `enforce_min_adventurer_level` (423 Locked) per dungeon con `min_adventurer_level` esplicito o derivato via `dungeon.recommended_power/12` heuristic.
- **Assenza `MAX_LEVEL` constant**: nessun `MAX_LEVEL=60` o simile è definito → Phase B dovrà aggiungerlo se level cap Lv60 diventa hard-enforcement.

## 4. Stato PWR / solo-equip readiness

### Adventurer PWR (`app/expeditions/formulas.py`)
- `adventurer_base_power(adv)` = `STR + AGI + INT + END + FAITH + level*2` (integer).
- `adventurer_effective_power(adv)` = base + trait modifier (post Phase 13 traits).
- `total_power(adv)` = `base_power + equipment_power` esposto via serializer `adventurer_public()`.

### Equipment power (`app/equipment/services.py`)
- Per ogni item equipaggiato: `power_score` sommato in `equipment_power`.
- Slot map: `weapon`, `armor`, `accessory` (3 slot base).
- Serializer espone `power_score` per singolo item + total.

### Auto-equip fitness (`app/equipment/auto_equip.py`)
- `fitness = primary_score + secondary_score + POWER_WEIGHT * power_score + tag_bonus`
- Tie-break: `fitness DESC, power_score DESC, id ASC`.
- Deterministic, riproducibile.
- Rispetta class-bound policy R18.4 (hard block, soft demote, universal open).

### Legendary Forge power caps (`app/legendary_forge/__init__.py`)
- Cap primary/secondary/power_score per (type, rarity):
  - `Epic weapon/armor`: primary=5, secondary=2, power_score=7
  - `Legendary weapon/armor`: primary=7, secondary=3, power_score=10
  - `Epic accessory`: primary=2, secondary=2, power_score=7
  - `Legendary accessory`: primary=3, secondary=3, power_score=10
- Ma i drake_slayer items live hanno **power_score=60** per weapon, **35** per armor → **discrepanza** con i cap Legendary Forge. I `drake_slayer` sono probabilmente set signature "boss reward" fuori dalla Forge normale.

### Gap solo-equip
- **Non esiste** formula "solo-equip challenge" (adventurer da solo con equip completo → soglia difficoltà).
- **Non esiste** PWR-per-tier standardizzato (es. "Tier 3 item ha PWR base 25-35").
- L'attuale `power_score` è ad-hoc per item (seed-based, non derivato da formula).

## 5. Stato item tier

### Rarity attuale
Sistema **rarity 5-livelli** codificato come stringa: `Common / Uncommon / Rare / Epic / Legendary`.

Distribuzione live (173 items attivi):
| Rarity | Count | % |
|---|---|---|
| Common | 52 | 30% |
| Uncommon | 36 | 21% |
| Rare | 38 | 22% |
| Epic | 36 | 21% |
| Legendary | 11 | 6% |

### Assenza concetto "Tier"
Nessun field `tier` o `item_tier` numerico esplicito. La rarity è l'unico proxy tier attuale.

### Rework potenziale R18.5
Possibili approcci (**decisione PM lockata in Phase B**):
- **Opzione A**: mantenere rarity + aggiungere `power_tier` numerico derivato (T1..T5)
- **Opzione B**: sostituire rarity con `tier` esplicito con range PWR per tier
- **Opzione C**: doppio schema — rarity (visual UI) + tier (power gating)

## 6. Stato equip slot (post-R18.4 SQ1a)

### `item_type` (raw taxonomy)
- `weapon` (armi)
- `armor` (armature)
- `accessory` (accessori)
- `shield` (scudi, mapped a `slot_type=armor` post-R18.4 SQ1a)
- `material` (materiali crafting)
- `consumable` (pozioni etc.)

### `slot_type` (canonical post-R18.4)
Distribuzione live (147 items equipabili):
| slot_type | Count | Note |
|---|---|---|
| `weapon` | 54 | mapping semplice (weapon type) |
| `armor` | 44 | mapping semplice (armor type + shield) |
| `accessory` | 42 | mapping semplice (accessory type) |
| `weapon_main` | 7 | granularità estesa (drake_slayer_blade etc.) |
| `chest` | 3 | granularità estesa (drake_slayer_chest etc.) |
| `helm` | 1 | granularità estesa (drake_slayer_helm) |
| `amulet` | 5 | granularità estesa |
| `ring` | 1 | granularità estesa |

### Gap identificato
Solo **17 items** su 147 usano granularità piena (weapon_main / helm / chest / amulet / ring). Gli altri 130 hanno slot_type = item_type (fallback). Se R18.5 vuole loadout Lv60 con slot dedicati (helm/chest/legs/hands/feet/main/off/amulet/ring1/ring2 = 10 slot), servirebbe migration.

### Slot potenziali per R18.5 (**decisione PM lockata in Phase B**)
Struttura estesa possibile (Diablo-like):
- `weapon_main`, `weapon_off` (o `shield` come off)
- `helm`, `chest`, `legs`, `hands`, `feet`
- `amulet`, `ring_1`, `ring_2`, `belt`

## 7. Stato item stats

### Bonus stats disponibili (per item doc)
- `strength_bonus`, `agility_bonus`, `intellect_bonus`, `endurance_bonus`, `faith_bonus` (5 stat)
- `power_score` (numerico, aggregate)
- `enchant_slots` (0-2 visto, upgrade slot count)
- `max_refinement` (0-10 visto, upgrade level cap)

### Range live (sample weapon Legendary drake_slayer_blade)
- `strength_bonus`: 10
- `agility_bonus`: 3
- `power_score`: 60
- `max_refinement`: 10
- `enchant_slots`: 2

### Budget stat teorico
Non c'è un budget stat esplicito documentato. La Legendary Forge ha caps `primary=7, secondary=3, power_score=10` ma sono **superati** dai drake_slayer signature items (out-of-forge).

### Redundancy `min_level` vs `required_adventurer_level`
Ogni item ha **entrambi** i field:
- `min_level`: 1-9 (esempio) — probabilmente semantica catalog vecchia
- `required_adventurer_level`: 1-12 (esempio, media 4.3) — semantica gate corrente
- **Rischio**: se non allineati → confusione UI + validazione.

## 8. Stato drop / crafting / materials

### Drop tables (`app/expeditions/loot_tables.py`)
24 dungeon con `DUNGEON_LOOT_TABLES`. Estratto:

| Dungeon | Success chance | Rarity mix (success) |
|---|---|---|
| `goblin-warrens` | 50% | Common:85, Uncommon:15 |
| `shadow-crypts` | 45% | Common:90, Uncommon:10 |
| `dragons-hoard` | 55% | Common:75, Uncommon:25 |
| `mid-tier` | 60-62% | Common:50-55, Uncommon:35, Rare:10-15 |
| `high-tier` | 65% | Common:45-50, Uncommon:35, Rare:15-20 |

**Failure drop**: 0-10% chance, quasi sempre Common only.

### Materials drop (`app/expeditions/material_drop_tables.py`)
`roll_materials_for_dungeon()` è **INDEPENDENT roll** da item drop (Round 15 Phase 2). Classificazione dungeon tier (`_classify_dungeon_tier`) + `boosted_rate(base_rate, rarity)`.

### Crafting workshop (Round 14-15)
Endpoint `POST /api/recipes/{recipe_slug}/craft` esiste. Test residue phase14 mostrano `feature.locked 423` (Workshop Livello 1 required). Recipes esistono (`db.recipes` collection, 6 legendary forge + arfus 10). `db.materials` collection popolata.

### Gap R18.5
- **Nessun dungeon** droppa Epic o Legendary a rate misurabile via loot table standard (Legendary è tipicamente set signature reward).
- **Materials Lv60**: non è chiaro se esistano materiali di tier alto per craft endgame.
- **Workshop Lv1 gate** blocca test suite phase14 (issue P3 stanziato).

## 9. Dipendenze con R18.4 class-bound

### Attivi
- `db.items.item_binding_policy` (hard:11, soft:146, universal:16) — enforcement in `app/equipment/compatibility.py` (sealed).
- `db.items.slot_type` (raw canonical, esposto).
- `/api/adventurers/{id}/eligible-items` (endpoint context-aware full 4-state).
- Badge UI `ItemCompatibilityBadge` (blocked/not_recommended/recommended/universal).
- `app/equipment/ui_4state.py` (pure function derivation).

### Rischi R18.5
Qualsiasi modifica a `item_binding_policy`, `slot_type`, `class_tags`, `recommended_classes` deve rispettare:
1. **Sealed integrity 36/36 byte-identical** (test hard blocking).
2. **Runtime enforcement** in `equipment/compatibility.py` sealed.
3. **Endpoint contract** in `adventurers/routes.py` (locked B.SQ6).

Se R18.5 introduce nuovo `tier` field o rifà `power_score`, il nuovo campo deve essere additivo e non alterare policy R18.4.

## 10. Dipendenze UI

Componenti frontend impattati da item metadata:

| Component / Page | Dipendenze | Post-R18.4.followup Phase C |
|---|---|---|
| `pages/Inventory.jsx` | item.name, rarity, slot, is_universal | ✅ badge Universale + slot fallback |
| `pages/AdventurerEquipment.jsx` | eligible-items API + 4-state badge | ✅ full 4-state integrato |
| `components/InventoryEquipModal.jsx` | slot fallback + badge Universale | ✅ integrato |
| `components/ItemCompatibilityBadge.jsx` | enum → JSX (sealed R18.4.followup C) | ✅ SEALED |
| `utils/compatibilityLabels.js` | resolveItemSlot helper (sealed) | ✅ SEALED |
| `utils/displayLabels.js` | itemTypeLabel, rarityLabel | mapping IT stringhe |
| Vari `RarityBadge` inline | rarity → color | inline components |
| `components/territory/*Modal.jsx` | material items | crafting UI |

Se R18.5 aggiunge `tier` esplicito, `RarityBadge` va esteso (o creato `TierBadge`).

## 11. Dipendenze backend / API

### Endpoints impattati da item schema change
| Endpoint | Serializer | Impatto R18.5 |
|---|---|---|
| `GET /api/items` | `item_public()` | expose new fields (tier?) |
| `GET /api/items/{slug}` | idem | idem |
| `GET /api/inventory` | inventory row + `item_public()` | idem |
| `GET /api/adventurers` | `adventurer_public()` con equipment join | idem |
| `GET /api/adventurers/{id}/equipment` | `equipment_public()` | idem |
| `GET /api/adventurers/{id}/eligible-items` | `derive_ui_4state()` (sealed R18.4.followup) | **NO CHANGE** (sealed) |
| `GET /api/recipes/*` | recipe + result item | idem |
| `POST /api/expeditions/complete` | loot roll + XP → level up | tune XP curve if needed |

### Serializer entry point
`app/items/services.py::item_public()` — NON sealed, estensibile per nuovi field (pattern già usato in R18.4.followup Phase B).

## 12. Dipendenze auto-equip

`app/equipment/auto_equip.py` (**NON sealed**):
- `pick_best_item(adventurer, candidates)` → `(item, delta_pwr)`.
- Fitness formula documentata (primary + secondary + POWER_WEIGHT*power_score + tag_bonus).
- Rispetta `item_binding_policy` (skippa blocked, demota soft-mismatch, favorisce recommended).

`app/equipment/compatibility.py` (**SEALED R18.3e**):
- Gate function `can_equip(adventurer, item)` → bool.
- Non modificabile senza re-seal round.

`app/equipment/level_gate.py` / `level_audit.py`:
- Enforce `required_adventurer_level` at equip time.
- Se R18.5 rinomina o unifica `min_level` con `required_adventurer_level`, questi audit vanno aggiornati.

## 13. Rischi

| Categoria | Rischio | Severità |
|---|---|---|
| **DB** | Aggiungere `tier` field a 173 items richiede migration backfill (script apply, non sealed touch) | **medio** |
| **DB** | Deprecare `min_level` (redundant) senza migration rompe validation | alto |
| **Code** | Modificare `power_score` semantics rompe Legendary Forge cap check | **alto** |
| **Code** | Nuova formula PWR solo-equip deve coexistere con `adventurer_base_power` esistente | medio |
| **Code** | Nuovo slot_type granulare (helm/chest/etc.) rompe frontend fallback `slot_type ?? item_type` se non estende inventoryBySlot map | medio |
| **Frontend** | `RarityBadge` inline components sparsi (grep necessario) → coverage completa richiede audit | basso |
| **Test** | Aggiornare drop tables Goblin Warrens rompe seed determinism (loot_sim scripts) | medio |
| **Integrazione R18.4** | Qualsiasi touch a sealed files (equipment/compatibility.py, equipment/bindings.py, apply scripts) blocca il round | **critical** |
| **Regression** | Modificare `item_binding_policy` semantics rompe eligible-items endpoint contract | **critical** |
| **Backwards compat** | Adventurers live esistono con equipment; migration deve preservare equipment attivi | alto |

## 14. Open Questions PM (binary-answerable, stile B.SQ)

### R18.5 Design Lock — Sub-Questions per Phase B

1. **R18.5.SQ1 — XP curve Lv50-Lv60 override**: mantenere formula polinomiale attuale (Lv60=442k) o introdurre `_LATE_CURVE` hand-tuned override table Lv51-Lv60?
2. **R18.5.SQ2 — Level cap hard-enforcement**: introdurre `MAX_ADVENTURER_LEVEL=60` constant + gate applicativo (block XP grants oltre Lv60) o lasciare soft (curve monotona senza block)?
3. **R18.5.SQ3 — Item tier explicit field**: aggiungere `tier` numeric (T1-T5) esplicito o mantenere `rarity` come unico proxy tier?
4. **R18.5.SQ4 — PWR solo-equip formula**: nuova formula PWR standalone (es. `PWR = (base_power + equipment_power) * class_multiplier`) o mantenere `total_power` esistente come sufficiente?
5. **R18.5.SQ5 — Slot granularity**: espandere slot da 3 (weapon/armor/accessory) a 10 (Diablo-like) o mantenere 3 base + `slot_type` metadata per uso UI?
6. **R18.5.SQ6 — `min_level` deprecation**: rimuovere `min_level` field (duplicato con `required_adventurer_level`) o mantenere entrambi con validation cross-check?
7. **R18.5.SQ7 — Rarity → Tier rename**: mantenere labeling `Common/Uncommon/Rare/Epic/Legendary` (visual UI stabile) o rinominare in `T1/T2/T3/T4/T5` (semantica gioco-meccanica)?
8. **R18.5.SQ8 — Drop table Lv60**: estendere Goblin Warrens (o creare nuovo dungeon `goblin-warrens-elite`) con drop Rare/Epic per Lv55-60?
9. **R18.5.SQ9 — Signature items out-of-forge**: mantenere power_score=60 signature items fuori dai Legendary Forge cap (drake_slayer set) o forzare tutti dentro il cap?
10. **R18.5.SQ10 — Set bonus system**: attivare `set_id` visible via UI + endpoint (set bonus 2pc/4pc/6pc) o mantenere `set_id` come metadata opaque?

## 15. Raccomandazione Phase B

### Proposta scope Phase B

**Split Phase B in 2 sub-fase** (raccomandato dato lo scope):
- **Phase B.1 — Design Lock** (documentale, con PM SQ 1-10 answers): produce `r18_5_phase_b1_design_lock.md/.json`.
- **Phase B.2 — Implementation Plan** (documentale, dopo B.1): produce `r18_5_phase_b2_implementation_plan.md/.json`.

### Lista tabelle da definire in Phase B.1 (design lock)

1. **`r18_5_slot_taxonomy.md`** — mapping slot equip (3 vs 10 slot decision, backwards compat con `slot_type` current).
2. **`r18_5_tier_taxonomy.md`** — mapping tier (T1-T5 vs rarity, budget PWR per tier).
3. **`r18_5_pwr_formula.md`** — formula PWR solo-equip + soglie per tier.
4. **`r18_5_stat_budget.md`** — budget stat per tier + slot (STR/AGI/INT/END/FAITH range).
5. **`r18_5_item_family_taxonomy.md`** — famiglie equip (weapon subtypes: sword/axe/bow/staff; armor: light/medium/heavy).
6. **`r18_5_naming_conventions.md`** — nomi base + prefissi/suffissi player-facing (locked PM).
7. **`r18_5_class_compatibility_matrix.md`** — matrice class × slot × item_family (allineata con R18.4).
8. **`r18_5_item_signature_policy.md`** — signature items fuori dai cap (mantenere/vincolare).
9. **`r18_5_drop_matrix.md`** — drop table per dungeon (Goblin Warrens Lv1-10, dungeon mid Lv20-40, dungeon endgame Lv45-60).
10. **`r18_5_materials_crafting.md`** — materials per tier, ricette Lv60 endgame.
11. **`r18_5_xp_curve_lv60_override.md`** — override table Lv51-60 (se R18.5.SQ1=yes).
12. **`r18_5_set_bonus_system.md`** — set bonus taxonomy (se R18.5.SQ10=yes).

### Rischio Phase B (documentale)
**BASSO** — solo doc, zero code change, zero DB write. Rischio implementation (Phase C) da valutare dopo lock design.

### Governance rispettata Phase A
- **Sigilli 36/36 byte-identical** verificato via `pytest backend_r18_4_sealed_integrity_test.py` → 6/6 PASSED.
- **Zero DB writes** — solo query `find/count_documents` in audit.
- **Zero code changes** — working tree diff Phase A: solo `memory/PRD.md` (documental) + 2 doc discovery.

---

## Self-check Phase A discovery 15/15
1. ✅ Executive summary (< 300 parole, gap identificati)
2. ✅ Stato XP curve (formula + threshold + gap)
3. ✅ Level cap / Lv60 readiness
4. ✅ PWR / solo-equip readiness
5. ✅ Item tier (rarity distribution + rework opzioni)
6. ✅ Slot equip post-R18.4 SQ1a
7. ✅ Item stats (budget + range + redundancy)
8. ✅ Drop / crafting / materials
9. ✅ Dipendenze R18.4 class-bound
10. ✅ Dipendenze UI (7 componenti)
11. ✅ Dipendenze backend / API (8 endpoints)
12. ✅ Dipendenze auto-equip
13. ✅ Rischi (10 righe categoria/severità)
14. ✅ Open Questions PM (10 SQ binary-answerable)
15. ✅ Raccomandazione Phase B (split B.1/B.2 + 12 tabelle proposte)

---

**Ready for PM review** → attesa risposte alle 10 R18.5.SQ + autorizzazione Phase B (o split in Phase B.1 design lock).
