# R18.5 Phase B.1 — Design Lock (DOCUMENTAL ONLY)

- **Round (corrected)**: `R18.5 — Itemization, ILVL & Gear Progression Rework`
- **Sottotitolo**: *Lv60 cap, item-centered endgame, lore-driven equipment*
- **Round (superseded)**: ~~`R18.5 — PWR Solo-Equip + XP Curve Lv60 + Item Tier Rework`~~
- **Fase**: B.1 — Design Lock (documentale, con lock PM SQ1..SQ10) — **PATCHED 2026-07-06T18:00:00Z**
- **Locked at UTC**: `2026-07-06T17:00:00Z` — **Correction Patch UTC**: `2026-07-06T18:00:00Z`
- **Governance**: **DOCUMENTAL ONLY** — 36 sigilli byte-identical, zero DB writes, zero code changes.

## 0-BIS. STRATEGIC CORRECTION 2026-07-06T18:00:00Z (autorità PM)

Il focus del round è stato ridirezionato dal PM. **NON leveling / XP curve refactor**. Il centro è: **oggetti, ILVL, rarità, utility, drop endgame, progressione equip post level max, coerenza con la lore di Orbus**.

### Correzioni tassative applicate

| Ambito | Prima (superseded) | Dopo (corrected) |
|---|---|---|
| Level cap | `MAX_VISIBLE_LEVEL=60` (soft, UI-only) | `MAX_ADVENTURER_LEVEL=60` **HARD CAP gameplay** + `MAX_EQUIPMENT_REQUIRED_LEVEL=60` |
| Overflow | XP accumula oltre Lv60 senza block | XP oltre Lv60 **NON aumenta** il livello. Progressione post-Lv60 = **ILVL/equip** |
| Player-facing item metric | `equipment_pwr` (PWR-centric) | **ILVL** player-facing principale. `equipment_pwr` = metrica calcolata secondaria. `total_power` retro-compat |
| ILVL range R18.5 iniziale | non definito | **1-60** (T1=1-15, T2=16-30, T3=31-45, T4=46-55, T5=56-60) |
| Itemization principle | rarity+tier meccanico | **Lore-driven**: item rare+ devono avere lore source e utility unica, NON solo "+stat" |

### Deprecated (mantenuti nel file per storia)
- Sezioni con `MAX_VISIBLE_LEVEL` (Sezioni 1, 5): **superseded** — leggere in chiave "hard cap Lv60".
- Formula `equipment_pwr` originale (Sezione 5): **superseded** — la formula finale è in **Gate 1 decisions SQ18** (ILVL-based).
- Coefficienti PWR provvisori (`tier_bonus 2/5`, `slot_completion +5`): **superseded** — vedi Gate 1 SQ18 lock.

### Principio guida (lore-driven itemization)
Le fonti lore valide per item rare+ (Rare, Epic, Legendary): **Ambash, Irthe, Velur, Efreto, Halodi, Alevora, Soe, Aveol, Ergolat, Krastlov, Adalan, Greatwood/Elfwood, Alberi della Vita, Faglie arcane, Vuoto, Luna Morta, Ciclo delle anime**. Ogni item T3+ nel batch R18.5 avrà `lore_source` obbligatorio. Esempio approvato: *"Lama della Faglia Quieta" (Ambash) — riduce rischio evento arcano instabile*. Esempio rifiutato: *"Spada Epica +15 Forza"*.

### Legendary policy (correction)
Massimo **4 Legendary** nel primo batch R18.5, non craftabili normalmente, non ottenibili da shop/premium, non necessari per completare gioco base, utility unica lore-legata memorabile.

### Riferimento normativo
Le risposte PM lockate a SQ11-SQ18 e le lore rules sono formalizzate in **`/app/memory/r18_5_phase_b_gate1_pm_decisions.md/.json`**. In caso di conflitto tra questo file e Gate 1 decisions → **Gate 1 prevale**.

---

## 0-TER. SCALE-UP CORRECTION 2026-07-06T19:00:00Z (autorità PM)

Il PM ha corretto la **scala del catalogo R18.5** da micro-batch (80 item) a **scala MMO reale**.

### Superseding (catalogo reale vs micro-sample)

| Ambito | B.1 originale (superseded per catalogo reale) | Catalogo reale (Phase C0-bis) |
|---|---|---|
| Item batch size | 80 item totali (SQ14 lock micro-batch) | **1500 equip minimo** |
| Legendary max | 4 (SQ14 lock micro-batch) | **max 15** (catalogo reale) |
| Dungeon count | non pianificato | **60 dungeon** (12/14/16/10/8 per bracket) |
| Raid count | non pianificato | **12 raid** (2/3/3/4 per bracket) |
| Proficiency system | non pianificato | **armor + weapon proficiency obbligatorie**, hard block |
| Progression Lv60+ | ILVL/equip | ILVL / raid / loot raro / utility / ranking / mercato |

**Nota**: gli 80 item + max 4 Legendary del batch originale restano validi come **micro-sample / skeleton** per il drafting iniziale, **NON come cap del catalogo reale**. Riferimento autoritativo del catalogo reale: `r18_5_phase_c0bis_progression_dungeon_raid_matrix.md/.json`.

### Nuovo principio: proficiency obbligatoria
Ordine valutazione equip PM-lockato: (1) proficiency → (2) main stat → (3) ILVL/rarity/tier → (4) utility. "Se non hai proficiency, non puoi equipaggiare quell'oggetto" (hard block runtime, non solo warning).

## 0. Lock PM verbatim — R18.5.SQ1..SQ10

| SQ | Answer | Decisione lockata |
|---|---|---|
| **SQ1** | (a) Formula polinomiale unica | Nessun `_LATE_CURVE` hand-tuned Lv50-60. Formula invariata. |
| **SQ2** | (b) Soft cap | `MAX_VISIBLE_LEVEL=60`. XP accumula oltre Lv60 senza errore. |
| **SQ3** | (c) Entrambi | `rarity` + nuovo `tier: 1..5`. Mapping: Common→T1..Legendary→T5. |
| **SQ4** | (c) Coesistenza | Nuovo `equipment_pwr`/`gear_pwr` + `total_power` retro-compat. |
| **SQ5** | (d) Ibrido | Starter 3 slot (weapon/armor/accessory), endgame 6 (weapon/helm/chest/legs/accessory/shield). Shield placeholder differito. |
| **SQ6** | (b) Mantieni entrambi | `min_level` + `required_adventurer_level` coesistono con cross-check. |
| **SQ7** | (c) Dual-label | UI "Common / T1", "Uncommon / T2", ecc. |
| **SQ8** | (b) Nuovo dungeon endgame | Loot T4/T5 solo da endgame dedicato. Goblin Warrens early-only. |
| **SQ9** | (b) Cap max signature | Max 1 signature equipped/adv. Out-of-forge in R18.5. |
| **SQ10** | (c) Defer | Set bonus NON attivato. Solo placeholder compat. |

## 1. XP curve / Lv60 soft cap policy (SQ1+SQ2)

- Formula `xp_required_for_level` invariata (polinomiale `5000 + round((lvl-10)^1.93 * 230)`).
- Nuovo `MAX_VISIBLE_LEVEL=60` in `app/shared/constants.py`.
- Serializer `adventurer_public()` clampa `level = min(level, MAX_VISIBLE_LEVEL)`.
- DB `adventurers.xp` cumulative preservato senza block. Forward-compat cap increment.

Threshold noti: Lv50=289.252, Lv55=361.803, **Lv60=442.260**, Lv70=626.670 (overflow visibile Lv60).

## 2. Tier taxonomy T1-T5 (SQ3)

Nuovo campo DB `items.tier: int (1..5)` additivo, non sostituisce `rarity`. NOT NULL post-migration.

| Tier | Target level range | Semantica |
|---|---|---|
| T1 | Lv 1-10 | Starter early |
| T2 | Lv 10-20 | Early mid |
| T3 | Lv 20-35 | Mid |
| T4 | Lv 35-50 | Late |
| T5 | Lv 50-60 | Endgame |

**Range PWR per tier (`PENDING PM approval`)**:
- T1: power_score 1-5, stat 1-8
- T2: 4-9, 5-14
- T3: 8-15, 10-22
- T4: 14-25, 18-36
- T5: 22-40, 30-60
- T5 signature (out-of-cap): 40-70, 50-100

## 3. Rarity ↔ tier mapping + dual-label (SQ3+SQ7)

Mapping fisso locked: Common→T1, Uncommon→T2, Rare→T3, Epic→T4, Legendary→T5.

**UI dual-label**: testo principale rarity fantasy ("Legendary"), badge secondario/tooltip tier code ("T5"). Colori badge tier `PENDING PM`: proposta T1=grey, T2=green, T3=blue, T4=purple, T5=gold.

`item_public()` serializer contract Phase C:
```json
{"rarity": "Legendary", "tier": 5, "tier_label": "T5"}
```

## 4. Slot taxonomy starter/endgame (SQ5)

### Starter slot (3, esistenti — invariati)
- `weapon`, `armor` (armor+shield collassati R18.4 SQ1a), `accessory`.

### Endgame slot (6, nuovo target Lv30+)
- `weapon`, `helm`, `chest`, `legs`, `accessory`, `shield` (placeholder, activation differita).

### Policy shield (SQ5 vincolo)
Mapping R18.4 SQ1a (`shield → slot_type=armor`) resta valido finché B.2 non propone piano compat sicuro. Nessuna attivazione distruttiva del slot `shield` dedicato.

### Transition policy
- Adv Lv <30: solo starter slot (3 visibili UI).
- Adv Lv >=30: endgame slot (6 visibili).
- Backwards compat: item `slot_type=armor` continuano equipabili come "armor generico".

`PENDING PM approval`: soglia switch (proposta Lv30).

## 5. PWR solo-equip formula (SQ4)

Nuovo `equipment_pwr` (alias `gear_pwr`) coesiste con `total_power` esistente.

```
equipment_pwr = sum(item.power_score for equipped)
              + tier_bonus  # 2 * count(T4) + 5 * count(T5)
              + slot_completion_bonus  # +5 se tutti slot visibili filled
```

### Esempio (Lv50 endgame full-equipped)
weapon T5 (40) + helm T4 (22) + chest T4 (25) + legs T4 (20) + accessory T3 (15) + shield T4 placeholder (18) = 140. Tier bonus 2*4+5*1=13. Slot completion +5. **equipment_pwr = 158**.

### Semantica
- Ranking gear / gear eval / leaderboard.
- NON sostituisce `total_power` per expedition power gating.

Serializer Phase C: `adventurer_public()` esporrà `equipment_power` (legacy), `total_power` (legacy), `equipment_pwr` (new), `gear_pwr` (alias).

`PENDING PM approval`: coefficienti tier_bonus (2/5) + slot_completion (5).

## 6. Stat budget per tier/livello (`PENDING PM`)

### Budget stat totale
| Tier | Budget | Distribuzione tipica |
|---|---|---|
| T1 | 1-8 | 1 primario 1-5, opzionale secondario 1-3 |
| T2 | 5-14 | 1 primario 3-8, 1 secondario 2-6 |
| T3 | 10-22 | 1 primario 5-12, 1 secondario 3-8, filler 0-2 |
| T4 | 18-36 | 1 primario 8-18, 1 secondario 5-12, filler 2-6 |
| T5 | 30-60 | 1 primario 12-25, 1 secondario 8-18, filler 5-15 |
| T5 signature | 50-100 | out-of-cap |

### Slot multiplier
Weapon 1.2x, Armor 1.0x, Accessory 0.7x, Shield 0.8x.

`PENDING PM approval`: intera tabella budget stat + slot multipliers.

## 7. Item family taxonomy

### Weapon
sword (STR+AGI), axe (STR), mace (STR+FAITH), dagger (AGI), bow (AGI), staff (INT+FAITH), wand (INT), crossbow (AGI+END).

### Armor
armor_heavy (END+STR), armor_medium (END+AGI), armor_light (AGI+INT), robe (INT+FAITH).

### Accessory
amulet (INT/FAITH), ring (AGI/STR), belt (END), trinket (variable).

### Shield (placeholder differito)
shield_heavy (END), shield_light (AGI+END).

`PENDING PM approval`: mapping primary stat per famiglia.

## 8. Naming conventions (pattern, NO naming finale)

**Structure**: `[Prefix?] + [Base] + [of Suffix?]`

- **Prefix (T3+)**: Affilato, Rinforzato, Antico, Runato, Benedetto, Maledetto, Etereo.
- **Base**: famiglia IT (Spada, Ascia, Bastone, ecc.).
- **Suffix (T4+)**: del Lupo, del Saggio, del Vuoto, dell'Alba.

Esempi: `Spada` (T1), `Spada Affilata` (T2), `Spada Runata` (T3), `Spada Runata del Lupo` (T4), `Antica Spada del Vuoto` (T5), naming unico signature (T5 out-of-forge).

### Policy IT + lore
- Coerenza `lore_source=orbus_lore_book_v1`.
- `lore_tags` esistenti (oblio, vuoto, alba, sigillo).
- Flavor text IT obbligatorio T3+.

### Vietato
Emoji, caratteri speciali (oltre `'`/`-`), copyright names.

`PENDING PM approval`: elenco completo prefix/suffix + naming finale per batch.

## 9. Class compatibility matrix (coerente R18.4)

Principi lockati:
- `item_binding_policy` R18.4 (hard/soft/universal) invariata.
- Nuove famiglie assegnate a `recommended_classes` + `class_tags` seguendo pattern R18.4.
- NO modifica policy esistenti sui 173 items live.

### Matrice preliminare famiglia × role (`PENDING PM`)

| Family | Tank | DPS_melee | DPS_ranged | Healer | Stealth |
|---|---|---|---|---|---|
| sword | soft-rec | soft-rec | mismatch | mismatch | mismatch |
| axe | soft-rec | soft-rec | mismatch | mismatch | mismatch |
| mace | soft-rec | soft-rec | mismatch | soft-rec | mismatch |
| dagger | mismatch | soft-rec | mismatch | mismatch | hard-rec |
| bow | mismatch | mismatch | soft-rec | mismatch | mismatch |
| staff | mismatch | mismatch | soft-rec | soft-rec | mismatch |
| wand | mismatch | mismatch | soft-rec | soft-rec | mismatch |
| armor_heavy | soft-rec | soft-rec | mismatch | mismatch | mismatch |
| armor_medium | soft-rec | soft-rec | soft-rec | mismatch | soft-rec |
| armor_light | mismatch | mismatch | soft-rec | mismatch | soft-rec |
| robe | mismatch | mismatch | mismatch | soft-rec | mismatch |
| amulet | universal | universal | universal | universal | universal |
| ring | universal | universal | universal | universal | universal |
| shield_heavy | soft-rec | soft-rec | mismatch | mismatch | mismatch |

Legenda: soft-rec = badge Consigliato (soft policy + in recommended_classes), mismatch = badge Non consigliato, hard-rec = hard policy + required_class match, universal = badge Universale.

`PENDING PM approval`: matrice completa (definitiva post-Class Guide).

## 10. Signature item policy (SQ9)

- Max **1 signature equipped/adventurer** (uniqueness constraint runtime).
- Nuovo flag DB `items.is_signature: bool` (default false).
- **Out-of-forge**: NO crafting signature in R18.5. Drop only da boss/raid/event.
- Set signature esistenti (drake_slayer_*): retagged `is_signature=true` in Phase C migration.

### Distribuzione target R18.5 (`PENDING PM`)
- Weapon T5 signature: 8-12
- Armor T5 signature: 4-6
- Accessory T5 signature: 2-4
- Shield T5 signature: 1-2 (placeholder)
- **Totale target**: **~15-25** signature R18.5.

### Runtime constraint
Al equip: `count(equipped where is_signature=true) <= 1`. Se già equipped → 400 IT "Solo 1 item leggendario può essere equipaggiato".

`PENDING PM approval`: numeri esatti + effetti unici.

## 11. Drop matrix (SQ8)

### Goblin Warrens (invariato early game)
Common:85, Uncommon:15. Success 50%. Nessun Rare/Epic/Legendary.

### Dungeon mid-tier esistenti
`shadow-crypts`, `dragons-hoard`, altri 24 dungeon — INVARIATI.

### Nuovo endgame dungeon Lv50-60 (SQ8 lock, `PENDING PM naming`)

| Slug placeholder | Level range | Rarity mix (success) | Success chance |
|---|---|---|---|
| `endgame-void-crucible` | Lv 50-60 | Rare:35, Epic:45, Legendary:20 | 40% |
| `endgame-oblivion-tower` (opt) | Lv 55-60 | Rare:20, Epic:50, Legendary:30 | 35% |

### Signature drop policy
Signature NON entrano nel weighted roll standard. Drop via `dungeon.rewards.signature_drop_id` boss encounter flag o event chain.

### Retro-compat
Additive only: nuovo entry in `loot_tables.py`. Nessuna modifica ai 24 dungeon esistenti.

`PENDING PM approval`: nomi endgame dungeon + drop rate finali.

## 12. Materials/crafting matrix

### Categorie granulari
- `essence_*` T1-T5 (dungeon materials roll, base crafting)
- `hide_*` T1-T4 (beast, armor crafting)
- `ore_*` T1-T5 (mining/expedition, weapon crafting)
- `crystal_*` T3-T5 (rare, enchant/refinement)
- `essence_signature_*` T5 (boss only, signature refinement POST-R18.5)

### Sub-categorie per tier
- T1-T2: `crude_*` (crude_leather, crude_iron_ore)
- T3: `refined_*` (refined_leather, steel_ingot)
- T4: `pristine_*` (pristine_crystal, mithril_ingot)
- T5: `essence_of_*` (essence_of_dawn, essence_of_void)

### Workshop gating (`PENDING PM approval`)
- T1 recipes: Workshop Lv1 (esistenti)
- T3 recipes: Workshop Lv3
- T4 recipes: Workshop Lv5
- T5 recipes: Workshop Lv7
- Signature crafting: NO in R18.5.

## 13. min_level / required_adventurer_level coexistence (SQ6)

Entrambi field coesistono.

### Regola precedenza (locked)
1. Se `required_adventurer_level >= 1` → autoritativo per equip gate.
2. Se null/assente → fallback `min_level`.
3. Entrambi assenti → default 1.

### Cross-check validation (proposto B.2)
Dry-run script identifica items divergenti (`min_level != required_adventurer_level`). Output: lista + rapporto. NO auto-fix.

### Normalization plan
- Divergenza >5%: proporre migration di massa (PM decision).
- Divergenza <5%: manuale item-by-item.

`PENDING PM approval`: policy post dry-run.

## 14. Future set bonus placeholder (SQ10)

**NO attivazione set bonus in R18.5**. NO endpoint, NO UI, NO 2pc/4pc/6pc, NO runtime calc.

### Compatibility per round futuro
- `items.set_id` esiste (`drake_slayer` visto).
- Future round aggiungerà collection `item_sets`:
```
{
  set_id: "drake_slayer",
  pieces: ["drake_slayer_blade","drake_slayer_helm",...],
  bonuses: [
    {pieces_required: 2, effect_slug: "drake_slayer_2pc"},
    {pieces_required: 4, effect_slug: "drake_slayer_4pc"},
    {pieces_required: 6, effect_slug: "drake_slayer_6pc"}
  ]
}
```

Non implementare in R18.5. Round dedicato futuro (R18.6 o R19.x).

## Extra A — Granularità materiali crafting

Vedi Section 12. Stack size stackable. Signature crafting materials rare drop <5%.

`PENDING PM approval`: nomenclatura + drop rate.

## Extra B — Dimensione primo batch item (target 80-120)

### Distribuzione preliminare
| Tier | Count | Note |
|---|---|---|
| T1 | 25-35 | Early game |
| T2 | 20-30 | Early mid |
| T3 | 15-25 | Mid |
| T4 | 10-15 | Late |
| T5 base | 5-8 | Endgame rare |
| T5 signature | 15-25 | Out-of-forge R18.5 |
| **Range** | **90-138** | **Cap max 120 senza PM GO** |

### Split per slot
Weapon 40%, Armor 35%, Accessory 15%, Shield 5%, Materials/consumables 5%.

`PENDING PM approval`: distribuzione + slug pattern.

## Extra C — Regole nomi fantasy/lore

Vedi Section 8. Coerenza `orbus_lore_book_v1`. IT primaria (`display_name_it`), EN opzionale. Flavor text T3+. Signature naming curato unico.

`PENDING PM approval`: naming finale batch review.

## Extra D — Stat primarie per classe (`PENDING PM` — placeholder only)

**⚠️ NON finalizzare senza PM.**

| Class | Primary | Secondary | Role |
|---|---|---|---|
| Warrior | STR | END | Tank/DPS_melee |
| Paladin | STR+FAITH | END | Tank/Healer |
| Berserker (dormant) | STR | AGI | DPS_melee |
| Rogue | AGI | STR | DPS_melee |
| Ranger | AGI | INT | DPS_ranged |
| Assassin (dormant) | AGI | INT | Stealth |
| Monk | AGI+FAITH | END | DPS_melee/Healer |
| Cleric | FAITH | INT | Healer |
| Wizard | INT | FAITH | DPS_ranged |
| Cacciatore di Mostri | STR+AGI | END | DPS_melee |

**TUTTE `PENDING PM approval`** — dipendono da Class Guide + Stat Identity round futuri.

## Extra E — Rapporto con Class Guide + Stat Identity futuri

- Class Guide (round futuro): identity + stat priorities finali.
- Stat Identity (round futuro): semantica STR/AGI/INT/END/FAITH.

### Constraint R18.5
Item budget stat allineabile senza rework migration. `class_tags` con flag revisione futura (metadata, non runtime). Nessuna decisione stat priority hard-coded difficile da migrare.

## Extra F — Rapporto con R18.3f Class Slug Migration (HOLD)

Situazione: `class_slug` derivato con fallback `class_name.lower()`.

### Constraint R18.5
Phase C item seed NON hard-coded canonical class_slug. Uso `recommended_classes: ["warrior","paladin",...]` (lowercase slug italiano) migrable se R18.3f sblocca (es. `monster_hunter` vs `cacciatore_di_mostri`).

## Open Questions PM aggregate (emerse in B.1)

1. **R18.5.SQ11** — soglia switch starter→endgame: Lv30/25/35?
2. **R18.5.SQ12** — colori tier badge: T1=grey T2=green T3=blue T4=purple T5=gold (approvare?)
3. **R18.5.SQ13** — signature target R18.5: 15-25?
4. **R18.5.SQ14** — batch item distribution (Extra B): approvare?
5. **R18.5.SQ15** — endgame dungeon slug: `endgame-void-crucible`?
6. **R18.5.SQ16** — normalization min_level policy: fix massa vs manuale (post dry-run)?
7. **R18.5.SQ17** — workshop level per tier: Lv1(T1)/Lv3(T3)/Lv5(T4)/Lv7(T5)?
8. **R18.5.SQ18** — coefficienti PWR bonus: tier_bonus (2/5) + slot_completion (5)?

## Self-check Phase B.1 20/20
1-15. ✅ 14 tabelle obbligatorie + SQ verbatim
16-20. ✅ 6 extra sezioni PM (A-F)

**`PENDING PM approval`**: 8 R18.5.SQ11..SQ18 + valori numerici tabelle 5/6/9/11/12.

Ready for PM review → Phase B.1 CLOSED, procedo con B.2.
