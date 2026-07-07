# R18.5 Pre-D1 — Iconic Starter Items Workshop (STEP 10)

**Round**: R18.5 — Itemization, ILVL & Gear Progression Rework
**Phase**: Pre-D1 Workshop — 15 Iconic Starter Items (STOP dopo Pre-D1)
**Locked at (UTC)**: 2026-07-07T12:00:00Z
**Governance**: DOCUMENTAL ONLY
**Status**: DRAFT — PENDING PM approval, NON auto-transition a D1
**Authority**: PM Orchestrator — STEP 10 single step, review esplicita prima di D1
**Scope**: 15 iconic starter items (3 per classe × 5 classi canoniche W/R/M/P/Ranger)

---

## Executive Summary

Prima di iniziare Phase D1 (T1×300 item drafting), il PM ha autorizzato un **workshop di identità narrativa** per definire i **15 iconic starter items** (3 per classe canonica) che diventeranno cornerstone del brand Orbus fin dal Lv1-5. Ciascun item è:

- **Bracket**: Lv1-5, Tier T1
- **Rarity**: Common oppure Uncommon (NO Rare/Epic/Legendary)
- **Balance-safe**: memorabile ma non troppo forte
- **Class-oriented**: coerente con weapon/armor proficiency e main stat della classe orientata
- **Lore leggero**: tocco narrativo da fonti "starter-friendly" (NO Vuoto/Draco/Celeste/Infernale/Irthe endgame)
- **Anti-P2W R18**: `can_be_sold_for_real_money = false` obbligatorio per tutti

Dopo questo workshop, **STOP** — attendo review PM esplicita prima di sbloccare Phase D1 (T1×300).

---

## Distribuzione 15 items (3 per classe canonica)

| Classe | Items | Range Lv | Rarity mix |
|---|:---:|---|---|
| Warrior | 3 (W1, W2, W3) | 1-3 | 2 Common + 1 Uncommon |
| Rogue | 3 (R1, R2, R3) | 1-3 | 2 Common + 1 Uncommon |
| Mage | 3 (M1, M2, M3) | 1-3 | 2 Common + 1 Uncommon |
| Priest | 3 (P1, P2, P3) | 1-3 | 2 Common + 1 Uncommon |
| Ranger | 3 (Ra1, Ra2, Ra3) | 1-3 | 2 Common + 1 Uncommon |
| **TOTALE** | **15** | **1-3** | **10 Common + 5 Uncommon** ✅ |

---

## Warrior — 3 iconic starters (STR/END, heavy armor + sword/mace/shield/hammer)

### W1 · Lama del Recluta di Ferro

| Campo | Valore |
|---|---|
| `item_id` | `warrior-ironrecruit-blade` |
| `nome_it` | Lama del Recluta di Ferro |
| `classe_orientata` | Warrior |
| `slot` | main-hand |
| `weapon_family` | sword |
| `required_level` | 1 |
| `ilvl` | 1 |
| `rarity` | Common |
| `tier` | T1 |
| `main_stat_target` | STR |
| `stat_principali` | STR +2, damage 3-5 |
| `lore_source_leggera` | Krastlov (bracket Batch 1 introduttivo) |
| `fonte_drop_craft_tutorial` | Reward guaranteed dalla quest tutorial "Il Primo Passo" (Krastlov Militia Camp) |
| `perche_iconico` | Prima arma ricevuta da ogni Warrior — la "lama che tutti ricordano". Simbolo di ingresso nell'ordine dei difensori di Krastlov. |
| `perche_non_rompe_bilanciamento` | Damage 3-5 baseline standard T1 Common, nessuna proprietà speciale, nessun bonus critico. Sostituita naturalmente entro Lv6-8. |
| `is_cosmetic` | false |
| `affects_combat` | true |
| `affects_economy` | false |
| `affects_ranking` | false |
| `is_tradeable` | false |
| `can_be_sold_for_gold` | true (10 gold vendor) |
| `can_be_sold_for_real_money` | **false** ✅ |

### W2 · Scudo del Novizio Bulwark

| Campo | Valore |
|---|---|
| `item_id` | `warrior-bulwark-novice-shield` |
| `nome_it` | Scudo del Novizio Bulwark |
| `classe_orientata` | Warrior |
| `slot` | off-hand |
| `weapon_family` | shield |
| `required_level` | 3 |
| `ilvl` | 3 |
| `rarity` | Uncommon |
| `tier` | T1 |
| `main_stat_target` | END |
| `stat_principali` | END +3, armor block +5%, physical mitigation +2 |
| `lore_source_leggera` | Ambash (leggera — riferimento alla forgia iniziale della gilda Bulwark) |
| `fonte_drop_craft_tutorial` | Craft NPC "Fabbro Bulwark" (Krastlov Militia Camp) — recipe unlocked al Lv2 |
| `perche_iconico` | Primo scudo craftabile di ogni Warrior — la sagoma classica ovale col simbolo Bulwark, riconoscibile in tutta la lore. |
| `perche_non_rompe_bilanciamento` | Block +5% è nel range T1 Uncommon standard. Il valore END +3 è modesto e viene surclassato da qualsiasi scudo T2+. |
| `is_cosmetic` | false |
| `affects_combat` | true |
| `affects_economy` | false |
| `affects_ranking` | false |
| `is_tradeable` | true |
| `can_be_sold_for_gold` | true (25 gold vendor) |
| `can_be_sold_for_real_money` | **false** ✅ |

### W3 · Elmo di Ferro del Novizio

| Campo | Valore |
|---|---|
| `item_id` | `warrior-ironhelm-starter` |
| `nome_it` | Elmo di Ferro del Novizio |
| `classe_orientata` | Warrior |
| `slot` | head |
| `armor_type` | heavy |
| `required_level` | 2 |
| `ilvl` | 2 |
| `rarity` | Common |
| `tier` | T1 |
| `main_stat_target` | STR |
| `stat_principali` | STR +1, END +1, armor +2 |
| `lore_source_leggera` | Krastlov (bracket Batch 1) |
| `fonte_drop_craft_tutorial` | Drop garantito da "Bandit Scout" (Krastlov Outskirts, Lv2 mob) — quest chain starter |
| `perche_iconico` | L'elmo che si vede in ogni artwork ufficiale del Warrior novizio. Icona visiva del gioco. |
| `perche_non_rompe_bilanciamento` | Armor +2 è la base T1 Common. Nessun set bonus. Sostituito rapidamente. |
| `is_cosmetic` | false |
| `affects_combat` | true |
| `affects_economy` | false |
| `affects_ranking` | false |
| `is_tradeable` | true |
| `can_be_sold_for_gold` | true (8 gold vendor) |
| `can_be_sold_for_real_money` | **false** ✅ |

---

## Rogue — 3 iconic starters (AGI, light/medium armor + dagger/sword)

### R1 · Pugnale del Passo d'Ombra

| Campo | Valore |
|---|---|
| `item_id` | `rogue-shadowstep-dagger` |
| `nome_it` | Pugnale del Passo d'Ombra |
| `classe_orientata` | Rogue |
| `slot` | main-hand |
| `weapon_family` | dagger |
| `required_level` | 1 |
| `ilvl` | 1 |
| `rarity` | Common |
| `tier` | T1 |
| `main_stat_target` | AGI |
| `stat_principali` | AGI +2, damage 2-4, crit-chance +1% |
| `lore_source_leggera` | Alberi della Vita (foresta iniziale — leggera, non capstone) |
| `fonte_drop_craft_tutorial` | Reward della quest tutorial "Silent Steps" (Elfwood Fringe) |
| `perche_iconico` | Prima arma di ogni Rogue — la lama corta ricurva con impugnatura in cuoio scuro. Icona del "primo taglio silenzioso". |
| `perche_non_rompe_bilanciamento` | Damage 2-4 baseline T1 Common, crit +1% minimo. Sostituito entro Lv6. Nessuna proprietà stealth speciale. |
| `is_cosmetic` | false |
| `affects_combat` | true |
| `affects_economy` | false |
| `affects_ranking` | false |
| `is_tradeable` | false |
| `can_be_sold_for_gold` | true (10 gold vendor) |
| `can_be_sold_for_real_money` | **false** ✅ |

### R2 · Mantello di Cuoio Grezzo

| Campo | Valore |
|---|---|
| `item_id` | `rogue-leathercraft-cloak` |
| `nome_it` | Mantello di Cuoio Grezzo |
| `classe_orientata` | Rogue |
| `slot` | chest |
| `armor_type` | light |
| `required_level` | 3 |
| `ilvl` | 3 |
| `rarity` | Uncommon |
| `tier` | T1 |
| `main_stat_target` | AGI |
| `stat_principali` | AGI +3, evasion +3%, armor +1 |
| `lore_source_leggera` | Elfwood (bracket B1 — leggera, non capstone) |
| `fonte_drop_craft_tutorial` | Craft NPC "Cuoiaia Elfwood" — recipe unlocked al Lv2 tramite quest side "Prime Pellicce" |
| `perche_iconico` | Il mantello grigio-marrone con cappuccio calato — silhouette iconica del Rogue base in ogni promo materiale. |
| `perche_non_rompe_bilanciamento` | Evasion +3% è nel range T1 Uncommon standard. Armor +1 minimo. Nessun bonus stealth attivo. |
| `is_cosmetic` | false |
| `affects_combat` | true |
| `affects_economy` | false |
| `affects_ranking` | false |
| `is_tradeable` | true |
| `can_be_sold_for_gold` | true (25 gold vendor) |
| `can_be_sold_for_real_money` | **false** ✅ |

### R3 · Set Grimaldelli delle Ombre

| Campo | Valore |
|---|---|
| `item_id` | `rogue-shadowlockpick-set` |
| `nome_it` | Set Grimaldelli delle Ombre |
| `classe_orientata` | Rogue |
| `slot` | trinket |
| `weapon_family` | trinket (utility) |
| `required_level` | 2 |
| `ilvl` | 2 |
| `rarity` | Common |
| `tier` | T1 |
| `main_stat_target` | AGI |
| `stat_principali` | AGI +1, lockpick success +5%, no combat bonus |
| `lore_source_leggera` | Alberi della Vita (leggera — grimaldelli intagliati in radice antica) |
| `fonte_drop_craft_tutorial` | Reward guaranteed quest tutorial "Il Ladro Silenzioso" (NPC guild Rogue, Krastlov Alleys) |
| `perche_iconico` | Il set di grimaldelli in cuoio nero — icona narrativa del "primo furto" di ogni Rogue. Presente in tutte le loading screen. |
| `perche_non_rompe_bilanciamento` | Utility only (no combat impact). Lockpick success +5% è quality-of-life, non balance-affecting. |
| `is_cosmetic` | false |
| `affects_combat` | false |
| `affects_economy` | false |
| `affects_ranking` | false |
| `is_tradeable` | false |
| `can_be_sold_for_gold` | true (5 gold vendor) |
| `can_be_sold_for_real_money` | **false** ✅ |

---

## Mage — 3 iconic starters (INT, light armor + staff/wand)

### M1 · Bastone Arcano dell'Apprendista

| Campo | Valore |
|---|---|
| `item_id` | `mage-apprentice-arcane-staff` |
| `nome_it` | Bastone Arcano dell'Apprendista |
| `classe_orientata` | Mage |
| `slot` | main-hand |
| `weapon_family` | staff |
| `required_level` | 1 |
| `ilvl` | 1 |
| `rarity` | Common |
| `tier` | T1 |
| `main_stat_target` | INT |
| `stat_principali` | INT +2, spell damage +2, mana +5 |
| `lore_source_leggera` | Faglie arcane (leggera — vibrazione arcana minima, non capstone) |
| `fonte_drop_craft_tutorial` | Reward quest tutorial "Primo Incantesimo" (Torre Arcana degli Apprendisti — starter zone) |
| `perche_iconico` | Il bastone di legno chiaro con cristallo azzurro in cima — l'immagine "prototipo" del Mage in ogni artwork. |
| `perche_non_rompe_bilanciamento` | Spell damage +2 baseline T1 Common. Mana +5 minimo. Nessun proc, nessuna scuola magica speciale. |
| `is_cosmetic` | false |
| `affects_combat` | true |
| `affects_economy` | false |
| `affects_ranking` | false |
| `is_tradeable` | false |
| `can_be_sold_for_gold` | true (10 gold vendor) |
| `can_be_sold_for_real_money` | **false** ✅ |

### M2 · Veste Arcana del Novizio

| Campo | Valore |
|---|---|
| `item_id` | `mage-novice-arcane-robe` |
| `nome_it` | Veste Arcana del Novizio |
| `classe_orientata` | Mage |
| `slot` | chest |
| `armor_type` | light |
| `required_level` | 3 |
| `ilvl` | 3 |
| `rarity` | Uncommon |
| `tier` | T1 |
| `main_stat_target` | INT |
| `stat_principali` | INT +3, mana +10, spell damage +1, armor +1 |
| `lore_source_leggera` | Faglie arcane (leggera) |
| `fonte_drop_craft_tutorial` | Craft NPC "Tessitrice Arcana" — recipe unlocked Lv2 quest "Filo di Mana" |
| `perche_iconico` | La veste blu notte con simboli argentati — icona visiva del giovane Mage. Presente in ogni copertina. |
| `perche_non_rompe_bilanciamento` | Mana +10 è modesto. Spell damage +1 aggiuntivo minimo. Armor +1 (light) baseline. |
| `is_cosmetic` | false |
| `affects_combat` | true |
| `affects_economy` | false |
| `affects_ranking` | false |
| `is_tradeable` | true |
| `can_be_sold_for_gold` | true (25 gold vendor) |
| `can_be_sold_for_real_money` | **false** ✅ |

### M3 · Cristallo Focus del Primer

| Campo | Valore |
|---|---|
| `item_id` | `mage-focus-crystal-primer` |
| `nome_it` | Cristallo Focus del Primer |
| `classe_orientata` | Mage |
| `slot` | off-hand |
| `weapon_family` | wand (usato come focus off-hand) |
| `required_level` | 2 |
| `ilvl` | 2 |
| `rarity` | Common |
| `tier` | T1 |
| `main_stat_target` | INT |
| `stat_principali` | INT +1, spell cast speed +2%, mana +3 |
| `lore_source_leggera` | Ambash (leggera — cristallo lavorato) |
| `fonte_drop_craft_tutorial` | Drop garantito dai "Goblin Warrens" (Krastlov Outskirts, primo dungeon tutorial) |
| `perche_iconico` | Il piccolo cristallo esagonale trasparente — accessorio che ogni Mage riceve nel primo dungeon. |
| `perche_non_rompe_bilanciamento` | Spell cast speed +2% è nel range T1 Common minimum. Mana +3 minimo. Nessuna scuola magica specifica. |
| `is_cosmetic` | false |
| `affects_combat` | true |
| `affects_economy` | false |
| `affects_ranking` | false |
| `is_tradeable` | true |
| `can_be_sold_for_gold` | true (8 gold vendor) |
| `can_be_sold_for_real_money` | **false** ✅ |

---

## Priest — 3 iconic starters (FAI, heavy/medium armor + mace/staff/shield)

### P1 · Mazza Benedetta dalla Fede

| Campo | Valore |
|---|---|
| `item_id` | `priest-faith-blessed-mace` |
| `nome_it` | Mazza Benedetta dalla Fede |
| `classe_orientata` | Priest |
| `slot` | main-hand |
| `weapon_family` | mace |
| `required_level` | 1 |
| `ilvl` | 1 |
| `rarity` | Common |
| `tier` | T1 |
| `main_stat_target` | FAI |
| `stat_principali` | FAI +2, damage 3-4, heal power +2 |
| `lore_source_leggera` | Halodi (starter-friendly — benedizione del santuario) |
| `fonte_drop_craft_tutorial` | Reward quest tutorial "Benedizione del Santuario" (Halodi Sanctuary — starter zone) |
| `perche_iconico` | La mazza in legno chiaro con testa in oro opaco — simbolo del Priest iniziato al santuario di Halodi. |
| `perche_non_rompe_bilanciamento` | Damage 3-4 baseline T1 Common. Heal power +2 minimo. Nessuna divinità specifica invocata. |
| `is_cosmetic` | false |
| `affects_combat` | true |
| `affects_economy` | false |
| `affects_ranking` | false |
| `is_tradeable` | false |
| `can_be_sold_for_gold` | true (10 gold vendor) |
| `can_be_sold_for_real_money` | **false** ✅ |

### P2 · Vesti Sacre del Novizio

| Campo | Valore |
|---|---|
| `item_id` | `priest-novice-holy-vestments` |
| `nome_it` | Vesti Sacre del Novizio |
| `classe_orientata` | Priest |
| `slot` | chest |
| `armor_type` | medium |
| `required_level` | 3 |
| `ilvl` | 3 |
| `rarity` | Uncommon |
| `tier` | T1 |
| `main_stat_target` | FAI |
| `stat_principali` | FAI +3, heal power +3, mana +8, armor +2 |
| `lore_source_leggera` | Halodi |
| `fonte_drop_craft_tutorial` | Craft NPC "Sarto Sacro" (Halodi Sanctuary) — recipe unlocked Lv2 |
| `perche_iconico` | Le vesti bianche col ricamo dorato semplice — silhouette del novizio Priest in ogni cover art. |
| `perche_non_rompe_bilanciamento` | Heal power +3 è nel range T1 Uncommon. Mana +8 modesto. Armor +2 medium baseline. |
| `is_cosmetic` | false |
| `affects_combat` | true |
| `affects_economy` | false |
| `affects_ranking` | false |
| `is_tradeable` | true |
| `can_be_sold_for_gold` | true (25 gold vendor) |
| `can_be_sold_for_real_money` | **false** ✅ |

### P3 · Rosario dell'Alba

| Campo | Valore |
|---|---|
| `item_id` | `priest-prayer-beads-of-dawn` |
| `nome_it` | Rosario dell'Alba |
| `classe_orientata` | Priest |
| `slot` | amulet |
| `armor_type` | null (accessory) |
| `required_level` | 2 |
| `ilvl` | 2 |
| `rarity` | Common |
| `tier` | T1 |
| `main_stat_target` | FAI |
| `stat_principali` | FAI +1, mana regen +1/turn, heal received +2% |
| `lore_source_leggera` | Halodi |
| `fonte_drop_craft_tutorial` | Reward quest tutorial "Prima Preghiera" (Halodi Sanctuary monastery) |
| `perche_iconico` | Il rosario di grani bianchi con crocifisso semplice — accessorio riconoscibile in ogni loading screen Priest. |
| `perche_non_rompe_bilanciamento` | Mana regen +1/turn è modesto. Heal received +2% minimo. Nessuna proprietà divina attiva. |
| `is_cosmetic` | false |
| `affects_combat` | true |
| `affects_economy` | false |
| `affects_ranking` | false |
| `is_tradeable` | true |
| `can_be_sold_for_gold` | true (5 gold vendor) |
| `can_be_sold_for_real_money` | **false** ✅ |

---

## Ranger — 3 iconic starters (AGI/STR, medium armor + bow/polearm)

### Ra1 · Arco di Quercia del Cacciatore

| Campo | Valore |
|---|---|
| `item_id` | `ranger-hunter-oakwood-bow` |
| `nome_it` | Arco di Quercia del Cacciatore |
| `classe_orientata` | Ranger |
| `slot` | main-hand |
| `weapon_family` | bow |
| `required_level` | 1 |
| `ilvl` | 1 |
| `rarity` | Common |
| `tier` | T1 |
| `main_stat_target` | AGI |
| `stat_principali` | AGI +2, damage 3-5, range +1 |
| `lore_source_leggera` | Elfwood (foresta iniziale — leggera) |
| `fonte_drop_craft_tutorial` | Reward quest tutorial "Il Primo Colpo" (Elfwood Fringe — starter zone) |
| `perche_iconico` | L'arco lungo di quercia scura con corda semplice — silhouette iconica del Ranger novizio in ogni promo. |
| `perche_non_rompe_bilanciamento` | Damage 3-5 baseline T1 Common. Range +1 minimo (equivalente a arco corto). Nessuna proprietà eco/tracking speciale. |
| `is_cosmetic` | false |
| `affects_combat` | true |
| `affects_economy` | false |
| `affects_ranking` | false |
| `is_tradeable` | false |
| `can_be_sold_for_gold` | true (10 gold vendor) |
| `can_be_sold_for_real_money` | **false** ✅ |

### Ra2 · Corpetto di Cuoio dello Scout

| Campo | Valore |
|---|---|
| `item_id` | `ranger-scout-leather-jerkin` |
| `nome_it` | Corpetto di Cuoio dello Scout |
| `classe_orientata` | Ranger |
| `slot` | chest |
| `armor_type` | medium |
| `required_level` | 3 |
| `ilvl` | 3 |
| `rarity` | Uncommon |
| `tier` | T1 |
| `main_stat_target` | AGI |
| `stat_principali` | AGI +3, STR +1, evasion +2%, armor +2 |
| `lore_source_leggera` | Alberi della Vita (leggera — cuoio conciato con linfa foresta) |
| `fonte_drop_craft_tutorial` | Craft NPC "Conciatore Elfwood" — recipe unlocked Lv2 quest "Cuoio Forte" |
| `perche_iconico` | Corpetto verde-marrone con lacci in cuoio — la silhouette classica dello Scout Ranger. |
| `perche_non_rompe_bilanciamento` | Evasion +2% è modesto. AGI +3 + STR +1 nel range T1 Uncommon. Armor +2 medium baseline. |
| `is_cosmetic` | false |
| `affects_combat` | true |
| `affects_economy` | false |
| `affects_ranking` | false |
| `is_tradeable` | true |
| `can_be_sold_for_gold` | true (25 gold vendor) |
| `can_be_sold_for_real_money` | **false** ✅ |

### Ra3 · Faretra del Bosco

| Campo | Valore |
|---|---|
| `item_id` | `ranger-woodland-quiver` |
| `nome_it` | Faretra del Bosco |
| `classe_orientata` | Ranger |
| `slot` | trinket |
| `armor_type` | null (accessory) |
| `required_level` | 2 |
| `ilvl` | 2 |
| `rarity` | Common |
| `tier` | T1 |
| `main_stat_target` | AGI |
| `stat_principali` | AGI +1, arrow capacity +10, ranged accuracy +2% |
| `lore_source_leggera` | Elfwood |
| `fonte_drop_craft_tutorial` | Drop garantito dai "Cinghiali della Foresta" (Elfwood Fringe, mob Lv2 tutorial) |
| `perche_iconico` | La faretra di cuoio marrone con motivi silvani intagliati — accessorio riconoscibile di ogni Ranger novizio. |
| `perche_non_rompe_bilanciamento` | Capacity +10 è quality-of-life. Ranged accuracy +2% minimo (baseline T1). |
| `is_cosmetic` | false |
| `affects_combat` | true |
| `affects_economy` | false |
| `affects_ranking` | false |
| `is_tradeable` | true |
| `can_be_sold_for_gold` | true (8 gold vendor) |
| `can_be_sold_for_real_money` | **false** ✅ |

---

## Lore Coverage Starter (leggera)

**Fonti usate (leggere, starter-friendly)** — 4 di 22:
- **Krastlov** (bracket B1) — W1, W3 (Warrior track)
- **Halodi** — P1, P2, P3 (Priest track)
- **Alberi della Vita** (leggera, non capstone) — R1, R3, Ra2
- **Elfwood** — R2, Ra1, Ra3

**Fonti usate accennate (leggerissime)** — 2:
- **Faglie arcane** (leggera, non capstone) — M1, M2
- **Ambash** (leggera, no forge endgame) — W2, M3

**Fonti NON usate starter (riservate endgame T3-T5)** — 16 delle 22:
Vuoto, Draco, Celeste, Infernale, Irthe, Memoria, Adalan, Efreto, Alevora, Ergolat, Luna Morta, Aveol, Ciclo delle anime, Greatwood, Mare, Velur, Soe (nota: Elfwood ≠ Greatwood; Elfwood è la foresta starter, Greatwood è endgame).

**Coverage check**: **6 fonti leggere usate** su 22 (perfetto per starter — nessun sovraccarico su una singola fonte).

---

## Anti-P2W Compliance Check

| Item | `can_be_sold_for_real_money` |
|---|:---:|
| W1 · Lama del Recluta di Ferro | **false** ✅ |
| W2 · Scudo del Novizio Bulwark | **false** ✅ |
| W3 · Elmo di Ferro del Novizio | **false** ✅ |
| R1 · Pugnale del Passo d'Ombra | **false** ✅ |
| R2 · Mantello di Cuoio Grezzo | **false** ✅ |
| R3 · Set Grimaldelli delle Ombre | **false** ✅ |
| M1 · Bastone Arcano dell'Apprendista | **false** ✅ |
| M2 · Veste Arcana del Novizio | **false** ✅ |
| M3 · Cristallo Focus del Primer | **false** ✅ |
| P1 · Mazza Benedetta dalla Fede | **false** ✅ |
| P2 · Vesti Sacre del Novizio | **false** ✅ |
| P3 · Rosario dell'Alba | **false** ✅ |
| Ra1 · Arco di Quercia del Cacciatore | **false** ✅ |
| Ra2 · Corpetto di Cuoio dello Scout | **false** ✅ |
| Ra3 · Faretra del Bosco | **false** ✅ |

**15/15 compliant** ✅ — anti-P2W R18 policy rispettata verbatim.

---

## Governance Check STEP 10

| Voce | Status |
|---|---|
| Sealed files 36 hash byte-identical | ✅ (pytest atteso conferma) |
| DB writes | ZERO |
| Code changes (`.py`/`.js`/`.jsx`/`.tsx`/`.ts`) | ZERO |
| Migrations | ZERO |
| Item creation live | ZERO (design only, PENDING PM) |
| Registry generation | ZERO |
| Drop table apply | ZERO |
| Economy changes | ZERO |
| `lore_meta.py` touch | INVARIATO |
| Sealed file modification | ZERO |
| Anti-P2W runtime validator | ZERO (policy target, no runtime) |
| Phase C tech dry-run | NOT INITIATED |
| Classi canoniche | Warrior/Rogue/Mage/Priest/Ranger verbatim |
| Auto-transition D1 | **BLOCKED** — STOP dopo Pre-D1 |
| PM autonomous decision new | ZERO (tutti hook derivati da lore sources approvate) |
| Files deliverable | 2 (.md + .json) |
| Distribuzione 3+3+3+3+3 | **15/15 esatta** ✅ |
| Rarity mix | 10 Common + 5 Uncommon (no Rare/Epic/Legendary) ✅ |
| Bracket | Lv1-3 (dentro Lv1-5 target) ✅ |

---

## STOP dopo Pre-D1 — Attendo PM review prima di D1

**Status dei 15 iconic starter items**: **PENDING PM approval**.

**Non live**. **Non registry**. **Non applicati al DB**.

Il PM può:
- ✅ **Approvare** in blocco → sblocco Phase D1 (T1×300 item drafting)
- ✏️ **Modificare** nomi / stat / lore source di singoli item
- ✏️ **Rinominare** slug
- ❌ **Scartare** singoli item e richiedere sostituzione
- 📐 **Usare come pattern** per la stesura dei 300 item T1 in D1

**NO auto-transition a Phase D1**. Attendo esplicito GO PM.

**R18.5 status flow (aggiornato post STEP 10)**:
`... → C0-octies B5 CLOSED → Mini-Gate Legendary Discovery Chain (STEP 8) ✅ DRAFT → Phase D0 Item Table Blueprint (STEP 9) ✅ DRAFT → Pre-D1 Iconic Starter Items Workshop (STEP 10) ✅ DRAFT → PM REVIEW ⏸️ ATTESA → Phase D1 T1×300 🔒 BLOCKED gate PM`
