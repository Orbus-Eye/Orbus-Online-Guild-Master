# R18.5 — Phase D5 · T5 × 200 ENDGAME Item Table Drafting (Lv56-60) — STEP 18

**Round**: R18.5 — Itemization, ILVL & Gear Progression Rework
**Phase**: D5 — T5 × 200 ENDGAME Item Drafting (Lv56-60)
**STEP**: 18
**Locked at UTC**: `2026-07-07T17:48:00Z`
**Governance**: **DOCUMENTAL ONLY**
**Status**: 🟡 **DRAFT — PENDING PM approval (post-D4 CLOSED)**
**Authority**: PM Orchestrator — STEP 18 catena autorizzata post-STEP 17 D4 CLOSED + verbatim regole endgame rispettate

**Deliverables**:
- `/app/memory/r18_5_phase_d5_t5_item_table.md` (questo file)
- `/app/memory/r18_5_phase_d5_t5_item_table.json` (5832 righe · SHA256 `58e9f0ea86f7fb5eeaf00c53728fe15c4f4a40041c98e2639a339b873069ae6e`)

**Predecessori autoritativi**:
- `/app/memory/PRD.md` (R18.5 Phase D4 CLOSED post-STEP 17)
- `/app/memory/r18_5_phase_c0octies_batch5_lv56_60_matrix.md/.json` (9 dungeon + 2 Elite LIVE + 4 raid endgame)
- `/app/memory/r18_5_legendary_discovery_chain.md/.json` (7 Legendary APPROVED — L1-L7)
- `/app/memory/r18_5_phase_d0_item_table_blueprint.md/.json` (schema + 1500 distribution)
- `/app/memory/r18_5_phase_d4_t4_item_table.md/.json` (300 T4 CLOSED)
- `/app/memory/r18_5_craft_npcs_directory.md/.json` (5 NPC LOCKED)

**Regole HARD verbatim (rispettate 200/200)**:
- **Proficiency HARD BLOCK** post-Q6 D3 lesson — **inclusi 15 Legendary**
- Priest: NO scudo, NO piastre, NO cuoio, NO maglia
- Weapon backlog RESERVED: `strumento`/`falce`/`trinket_backlog` = 0 usi
- Anti-P2W: `can_be_sold_for_real_money=false` 200/200
- Classi canoniche: Warrior/Rogue/Mage/Priest/Ranger (NO drift)
- Legendary rules: utility unica, lore source forte, NO generic +stat, NO shop, NO craft normale
- Lore capstone T5 consentito (22/22 lore coverage post-D5)

---

## Sezione 1 — Tabella completa 200 item T5 (riferimento file JSON)

Per la tabella completa dei 200 item (ogni riga con `item_id`, `nome_it`, `classe_orientata`, `slot`, `weapon_family`, `armor_type`, `required_level`, `ilvl`, `rarity`, `tier`, `main_stat_target`, `stat_principali`, `lore_source`, `source`, `affects_combat`, `is_tradeable`, `iconic_family`, `affects_progression`, `affects_economy`, `affects_ranking`, `is_cosmetic`, `can_be_sold_for_gold`, `can_be_sold_for_real_money`, `item_binding_policy` + `chain_tag` per Legendary), vedere:

**`/app/memory/r18_5_phase_d5_t5_item_table.json`** (chiave `items[]`, 200 entries).

Sintesi:

| Metrica | Valore |
|---|:---:|
| Totale items | **200** |
| Warrior/Rogue/Mage/Priest/Ranger | **40 ciascuna** (0C + 0U + 14R + 23E + 3L) |
| ILVL range | 56–60 |
| Tier | T5 verbatim (100%) |

---

## Sezione 2 — Riepilogo numerico

| Vista | Valore |
|---|---|
| items totali | 200 |
| classi coperte | Warrior, Rogue, Mage, Priest, Ranger (40 ciascuna) |
| livelli coperti | Lv56–Lv60 (bracket Batch 5 ENDGAME) |
| tier | T5 (100%) |
| rarity | Common 0 · Uncommon 0 · Rare 70 · Epic 115 · Legendary 15 |
| anti-P2W | 200/200 `can_be_sold_for_real_money=false` (100%) |
| weapon backlog | `strumento`/`falce`/`trinket_backlog` = 0 usi (RESERVED) |
| **proficiency HARD** | **200/200 verified** — 0 violazioni (Priest scudo/piastre/cuoio/maglia = 0, inclusi Legendary) |
| NPC craft LOCKED | 5 usati · 0 nuovi autonomi |
| Legendary composition | 7 APPROVED + 4 HYBRID + 4 PROGRESSIVE (con PENDING PM) |
| Legendary bind-on-pickup | 15/15 |
| Legendary tradeable | 0/15 (all bind-on-pickup, no gold sell) |

---

## Sezione 3 — Rarity check 0/0/70/115/15 esatto

| Rarity | D5 count | Target PM verbatim | Match |
|---|:---:|:---:|:---:|
| Common | **0** | 0 | ✅ EXACT (NO Common endgame) |
| Uncommon | **0** | 0 | ✅ EXACT (NO Uncommon endgame) |
| Rare | **70** | 70 | ✅ EXACT |
| Epic | **115** | 115 | ✅ EXACT (dominante 57.5%) |
| Legendary | **15** | 15 | ✅ EXACT (cap catalog raggiunto) |
| **TOTALE** | **200** | 200 | ✅ EXACT |

**Endgame dominance**: Epic 57.5% + Legendary 7.5% = **65% high-tier**. Rare base 35%. Coerente con brief PM endgame.

---

## Sezione 4 — Level range check 56-60

**Verify**: min=56, max=60. Nessun item fuori range.

| Fascia | Count | Note |
|---|:---:|---|
| Lv56-57 | early bracket B5 | 3 dungeon (void-touched-outpost, starforged-approach, tower-of-adalan-summit) |
| Lv58-59 | mid bracket B5 | 3 dungeon (alevoran-warlord-throne, efreto-cursed-nexus, ambash-legendary-forge) + Elite (voidspire-5p, celestial-citadel-5p) + 2 raid (dragon-vault, void-cathedral, celestial-conclave) |
| Lv60 | late bracket B5 vetta | 3 dungeon (void-heart-sanctum, elder-wyrm-descent, pantheon-of-fallen-suns) + 1 raid finale (world-tree-collapse) |
| **TOTALE** | **200** | Bilanciato endgame ✅ |

**Legendary Lv distribution**:
- 14/15 Legendary a Lv60 (endgame vetta)
- 1/15 a Lv59 (ambash-forge-hammer Warrior dungeon boss)

---

## Sezione 5 — Class coverage check (~40/classe)

| Classe | Items | % | Common | Uncommon | Rare | Epic | Legendary |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Warrior** | 40 | 20% | 0 | 0 | 14 | 23 | 3 |
| **Rogue** | 40 | 20% | 0 | 0 | 14 | 23 | 3 |
| **Mage** | 40 | 20% | 0 | 0 | 14 | 23 | 3 |
| **Priest** | 40 | 20% | 0 | 0 | 14 | 23 | 3 |
| **Ranger** | 40 | 20% | 0 | 0 | 14 | 23 | 3 |
| **TOTALE** | **200** | 100% | 0 | 0 | 70 | 115 | 15 |

Classi canoniche verbatim: Warrior/Rogue/Mage/Priest/Ranger (NO Wizard/Cleric drift).
Bilanciamento equo perfetto: 40 items × 5 classi = 200 ✅.

---

## Sezione 6 — Proficiency check (HARD, inclusi 15 Legendary)

Proficiency verbatim (INVARIATA post-Q6 D3 lesson):

| Classe | Main stat | Armor | Weapon families |
|---|---|---|---|
| Warrior | STR | maglia + piastre | spada, ascia, martello, scudo, lancia, arma_in_asta |
| Rogue | AGI | cuoio | pugnale, spada, balestra |
| Mage | INT | stoffa | bastone, tomo, focus, pugnale, wand |
| Priest | WIS | **stoffa** | **bastone, martello, focus, reliquia, tomo** |
| Ranger | AGI | cuoio + maglia | arco, balestra, spada, pugnale, lancia |

**HARD verification 200/200**:

| Classe | Violation armor | Violation weapon | Legendary check | Status |
|---|:---:|:---:|:---:|:---:|
| Warrior | 0 | 0 | dragonlord-crown (piastre head OK) + ambash-forge-hammer (martello main-hand OK) + dragon-elder-scale (scudo off-hand OK) | ✅ HARD OK |
| Rogue | 0 | 0 | void-touched-blade (pugnale main-hand OK) + irthe-price-shroud (cuoio chest OK) + progressive-slot-03 (pugnale OK) | ✅ HARD OK |
| Mage | 0 | 0 | sole-nero-diadem (stoffa head OK) + ergolat-obelisk-focus (focus off-hand OK) + progressive-slot-01 (bastone OK) | ✅ HARD OK |
| **Priest** | **0 (no piastre/cuoio/maglia)** | **0 (no scudo)** | seraph-halo-crown (stoffa head OK) + celestial-conclave-mantle (stoffa chest OK) + progressive-slot-02 (reliquia OK) | ✅ **HARD OK (post-Q6 lesson propagata a D5)** |
| Ranger | 0 | 0 | worldroot-scepter (lancia main-hand OK — proficiency-valid) + halodi-fate-quiver (trinket OK) + progressive-slot-04 (arco OK) | ✅ HARD OK |

**Weapon backlog RESERVED verbatim Q6 D0**: `strumento`, `falce`, `trinket_backlog` = **0 items D5**. ✅

**Nota governance Legendary proficiency**: la proficiency HARD BLOCK è stata applicata anche ai 15 Legendary (7 approved + 4 hybrid + 4 progressive). Nessuna eccezione narrativa consentita.

---

## Sezione 7 — Source coverage (9 dungeon B5 + 2 Elite LIVE + 4 raid endgame + Craft NPC + secondarie)

**9 dungeon Batch 5 slug matrix verbatim** (source: `r18_5_phase_c0octies_batch5_lv56_60_matrix`):

| # | Slug | Lv | Lore |
|:---:|---|:---:|---|
| 1 | `void-touched-outpost` | 56 | Vuoto (nuova standalone) |
| 2 | `starforged-approach` | 57 | Celeste |
| 3 | `tower-of-adalan-summit` | 57 | Adalan |
| 4 | `alevoran-warlord-throne` | 58 | Alevora |
| 5 | `efreto-cursed-nexus` | 59 | Efreto |
| 6 | `ambash-legendary-forge` | 59 | Ambash (Legendary dungeon 1%) |
| 7 | `void-heart-sanctum` | 60 | Vuoto |
| 8 | `elder-wyrm-descent` | 60 | Draco (Legendary dungeon 1%) |
| 9 | `pantheon-of-fallen-suns` | 60 | Celeste (Legendary dungeon 1%, vetta Lv60) |

**2 Elite 5p LIVE** (fuori conteggio 60 Normal, traccia parallela storica):
- `voidspire-5p` LIVE (drift Lv=11 known no-rewrite)
- `celestial-citadel-5p` LIVE (drift Lv=13 known no-rewrite)

**4 raid endgame Lv56-60** (party_size=5p):
- `dragon-vault` LIVE (Lv58, Draco — Legendary L1 `dragonlord-crown` 2%)
- `void-cathedral` NEW (Lv57, Vuoto — Legendary L2 `void-touched-blade` 2%)
- `celestial-conclave` NEW (Lv58, Celeste — Legendary L3 `seraph-halo-crown` 2%)
- `world-tree-collapse` NEW (Lv60, Alberi della Vita — Legendary L4 `worldroot-scepter` 2%, RAID FINALE ULTIMO)

**Distribuzione source D5**:

| Fonte | D5 items | % catalog D5 |
|---|:---:|:---:|
| **Dungeon drop Batch 5** (9 dungeon) | **85** | 42.5% |
| **Raid drop Batch 5** (4 raid) | **61** | 30.5% |
| **Elite drop LIVE** (2 elite) | **10** | 5.0% |
| **Craft NPC 5 LOCKED** | **20** | 10.0% |
| **Achievement / Ranking / Quest / Vendor endgame** | **24** | 12.0% |
| **TOTALE** | **200** | 100% |

**Design endgame**: dungeon+raid+elite dominanti (**78% drop-based**), craft mid-tier (10%), non-drop endgame (12%). Coerente con brief PM endgame (Epic dominante, Legendary drop-only, no shop).

**Legendary Discovery Chain coverage** (7 APPROVED + 4 HYBRID + 4 PROGRESSIVE):
- 4 primari raid boss finale (drop 2% direzionale) — LIVE + NEW
- 3 secondari dungeon boss finale (drop 1% direzionale)
- 4 hybrid pre-allocated (drop rate HYBRID direzionale)
- 4 progressive discovery placeholders (drop rate PENDING PM)

---

## Sezione 8 — Anti-P2W check (200/200)

| Verify | Valore |
|---|:---:|
| Total items | 200 |
| `can_be_sold_for_real_money = false` | **200 / 200** ✅ |
| Compliance rate | **100%** |
| Legendary `bind-on-pickup` | 15/15 ✅ |
| Legendary `is_tradeable = false` | 15/15 ✅ |
| Legendary `can_be_sold_for_gold = false` | 15/15 ✅ |
| Epic `bind-on-equip` | 115/115 (tradeable soft) |
| Rare `bind-on-equip` | 70/70 (tradeable soft) |

Ogni item D5: `affects_combat=true`, `affects_economy=false`, `is_cosmetic=false`. Legendary aggiungono `affects_ranking=true` (utility endgame narrativa). Flag statico su tutti. **Nessun runtime validator** (Phase C post-D5).

**Anti-P2W R18 rule (Sezione 2 D0)**: `can_be_sold_for_real_money = false` **enforced automatico** per tutti items D5 (affects_combat=true). ✅ verified 200/200.

---

## Sezione 9 — Epic 115/115 check

| Sub-vista | Count | Note |
|---|:---:|---|
| Total Epic | **115 / 115** ✅ | Target EXACT MATCH |
| Epic dungeon Batch 5 | ~52 | ~5-6 Epic per dungeon (boss + pre-boss + variant classe) |
| Epic raid Batch 5 | ~40 | ~10 Epic per raid (pre-boss + boss + variant classe + hint) |
| Epic Elite `voidspire-5p` + `celestial-citadel-5p` | ~10 | 1 Epic per classe × 2 elite |
| Epic craft/achievement/ranking | ~13 | NPC LOCKED endgame + achievement world-first + seasonal ranking |
| Epic per classe (bilanciato) | **23 × 5** | Warrior/Rogue/Mage/Priest/Ranger = 23 ciascuna ✅ |

**Governance Epic D5**:
- 115/115 con identità narrativa forte (boss finale, pre-boss, variant classe, achievement world-first, ranking seasonal)
- 115/115 con `can_be_sold_for_real_money=false`
- 115/115 con **teaser meccanica endgame** (void-corrupt cleanse, star-forge focus, polymorph interrupt, warlord-summon, curse-cleanse chain, reforge weapon, silence survive, dragon-breath, light/void alternate, primordial-breath capstone, reality-collapse capstone, divine-conclave capstone, root-collapse capstone) — **NO runtime enforcement**
- Bilanciamento equo per classe (23 × 5) — nessuna discriminazione classe

---

## Sezione 10 — Legendary 15/15 check + composition dettagliata

| Verify | Valore |
|---|:---:|
| Total Legendary rarity | **15** |
| Target PM verbatim | 15 (cap catalog) |
| Cumulative R18.5 | 15/15 (cap RAGGIUNTO — no future Legendary senza PM decision) |
| Status | ✅ EXACT MATCH |

### 10.1 Legendary composition dettagliata

#### 10.1.a Approved 7 (from Legendary Discovery Chain STEP 8)

| # | item_id | Nome IT | Classe | Slot | Lore | Source (drop) | Utility unica |
|:---:|---|---|---|:---:|---|---|---|
| L1 | `warrior-t5-legendary-dragonlord-crown` | Corona del Signore dei Draghi | Warrior | head | Draco | `dragon-vault` LIVE raid boss (2%) | Command Draconic (1x/enc guida drago giovane) |
| L2 | `rogue-t5-legendary-void-touched-blade` | Lama Toccata dal Vuoto | Rogue | main-hand pugnale | Vuoto | `void-cathedral` NEW raid boss (2%) | Void-Pierce (ignora armor narrativo) |
| L3 | `priest-t5-legendary-seraph-halo-crown` | Corona d'Aureola del Serafino | Priest | head stoffa | Celeste | `celestial-conclave` NEW raid boss (2%) | Divine Resurrect (1x/enc fallen ally) |
| L4 | `ranger-t5-legendary-worldroot-scepter` | Scettro della Radice del Mondo | Ranger | main-hand lancia | Alberi della Vita | `world-tree-collapse` NEW raid boss (2%) | Nature's Blessing (AoE HoT natural terrain) |
| L5 | `warrior-t5-legendary-ambash-forge-hammer` | Martello della Fucina di Ambash | Warrior | main-hand martello | Ambash | `ambash-legendary-forge` dungeon 3p boss (1%) | Reforge weapon mid-encounter |
| L6 | `warrior-t5-legendary-dragon-elder-scale` | Scaglia del Verme Ancestrale | Warrior | off-hand scudo | Draco | `elder-wyrm-descent` dungeon 3p boss (1%) | Temporary Dragon-scale Armor Buff |
| L7 | `mage-t5-legendary-sole-nero-diadem` | Diadema del Sole Nero | Mage | head stoffa | Celeste | `pantheon-of-fallen-suns` dungeon 3p Lv60 boss (1%) | Swap Light/Void Resist mid-encounter |

**Fonte governance L1-L7**: `r18_5_legendary_discovery_chain.md` STEP 8 verbatim. Utility narrative fantasy proposals; numeric finals (cooldown, %, scaling) PENDING PM Phase D-post gate.

#### 10.1.b Hybrid 4 pre-allocated (PM Q9 R18.5 verbatim)

| # | item_id | Nome IT | Classe | Slot | Lore | Source (drop HYBRID) | Utility unica |
|:---:|---|---|---|:---:|---|---|---|
| H1 | `priest-t5-legendary-celestial-conclave-mantle-hybrid` | Manto del Conclave Celeste | Priest | chest stoffa | Celeste | `celestial-conclave` raid secondary drop (HYBRID) | Celestial Barrier (1x/enc barriera divina massive damage) |
| H2 | `rogue-t5-legendary-irthe-price-shroud-hybrid` | Sudario del Prezzo di Irthe | Rogue | chest cuoio | Irthe | `world-tree-collapse` raid alternate drop (HYBRID Irthe capstone) | Death's Toll (1x/enc colpo letale con prezzo narrativo) |
| H3 | `mage-t5-legendary-ergolat-obelisk-focus-hybrid` | Focus dell'Obelisco di Ergolat | Mage | off-hand focus | **Ergolat** | `ambash-legendary-forge` dungeon alternate drop (HYBRID) | Absence Distortion (1x/enc obelisco silenzia nemici area) |
| H4 | `ranger-t5-legendary-halodi-fate-quiver-hybrid` | Faretra del Fato di Halodi | Ranger | trinket | Halodi | `pantheon-of-fallen-suns` dungeon alternate drop (HYBRID) | Fate Deflection (1x/enc attacco letale deviato narrativo) |

**Nota governance H3 (Ergolat/Vuoto)**: PM ha indicato "Ergolat OR Vuoto" per H3 con direttiva "scegli quella non ancora usata dai 7 approvati". **Vuoto è già usato in L2 (void-touched-blade Rogue approved)** → per no-repeat lore-source Legendary, **Ergolat selezionato per H3** (assenza/obelischi/distorsione narrativa manifestata come Focus Mage). Decisione documentata come PM directive fulfillment (no autonomous decision — scelta letterale binaria PM). Se PM preferisce Vuoto (double-tap), swap immediato H3 → `mage-t5-legendary-void-obelisk-focus-hybrid` in Q3 post-D5.

#### 10.1.c Progressive Discovery 4 placeholders (PENDING PM — `chain_tag=PROGRESSIVE-4`)

| # | item_id | Classe | Slot | Lore proposta (PENDING PM) | Source proposta (PENDING PM) | Narrative direction (PENDING PM) |
|:---:|---|---|:---:|---|---|---|
| P1 | `mage-t5-legendary-progressive-slot-01-pending` | Mage | main-hand bastone | Memoria (echi cristallizzati endgame Mage) | Raid endgame progressive discovery (1-2%) | memoria-echo utility (recall past encounter action, replicate ally spell) |
| P2 | `priest-t5-legendary-progressive-slot-02-pending` | Priest | main-hand reliquia | Luna Morta (resurrection endgame Priest, capstone Ciclo delle anime) | Dungeon 3p endgame progressive discovery (1%) | resurrection-progressive utility (mass-resurrect party wipe recovery 1x/day) |
| P3 | `rogue-t5-legendary-progressive-slot-03-pending` | Rogue | main-hand pugnale | Ciclo delle anime (sanctum-of-fading-souls capstone Rogue soul-bind) | Raid endgame progressive discovery (1-2%) | soul-bind utility (steal 1 enemy passive for encounter duration) |
| P4 | `ranger-t5-legendary-progressive-slot-04-pending` | Ranger | main-hand arco | Greatwood/Elfwood (capstone Ranger nature-bond endgame) | Dungeon 3p endgame progressive discovery (1%) | nature-bond utility (summon 1 elfwood spirit companion for encounter) |

**Governance progressive**: campi minimi popolati (lore proposta + tipologia raid/dungeon + narrative direction). Tutti gli altri campi (drop_rate finale numerica, cooldown, %, scaling, boss finale specifico) esplicitamente marcati `PENDING PM`. Nessuna decisione autonoma. `chain_tag=PROGRESSIVE-4 (P1..P4)`.

### 10.2 Legendary per classe (bilanciamento)

| Classe | Legendary count | Breakdown |
|---|:---:|---|
| Warrior | 3 | L1 (dragonlord-crown) + L5 (ambash-forge-hammer) + L6 (dragon-elder-scale) |
| Rogue | 3 | L2 (void-touched-blade) + H2 (irthe-price-shroud) + P3 (soul-bind progressive) |
| Mage | 3 | L7 (sole-nero-diadem) + H3 (ergolat-obelisk-focus) + P1 (memoria progressive) |
| Priest | 3 | L3 (seraph-halo-crown) + H1 (celestial-conclave-mantle) + P2 (resurrection progressive) |
| Ranger | 3 | L4 (worldroot-scepter) + H4 (halodi-fate-quiver) + P4 (nature-bond progressive) |
| **TOTALE** | **15** | 7 APPROVED + 4 HYBRID + 4 PROGRESSIVE |

**Bilanciamento equo**: 3 Legendary per classe (nessuna classe favorita). Cap catalog 15/15 raggiunto.

### 10.3 Legendary rules compliance

| Regola PM strict verbatim | Compliance |
|---|:---:|
| Solo T5 | ✅ 15/15 tier=T5 |
| Max 15 catalog | ✅ 15/15 (cap RAGGIUNTO) |
| Utility unica | ✅ 15/15 (7 chain + 4 hybrid + 4 progressive PENDING descriptors) |
| Lore source forte | ✅ 11/15 forte (approved+hybrid) + 4/15 PENDING PM |
| NO generico +stat | ✅ 15/15 (utility narrativa in stat_principali) |
| NO shop | ✅ 15/15 (`can_be_sold_for_gold=false`) |
| NO craft normale | ✅ 15/15 (source = raid/dungeon endgame drop) |
| Drop rate direzionale 1-2% | ✅ 4 primari raid 2% + 3 secondari dungeon 1% (approved); HYBRID rate direzionale documentale; PROGRESSIVE rate PENDING PM |
| Bind-on-pickup | ✅ 15/15 |
| Anti-P2W `can_be_sold_for_real_money=false` | ✅ 15/15 |
| Proficiency HARD BLOCK (post-Q6) | ✅ 15/15 (Priest scudo/piastre = 0) |

---

## Sezione 11 — ⚡ ARITMETICA CUMULATIVA FINALE 1500/1500

**Verifica end-to-end** con conteggi reali estratti dai 5 file JSON deliverable (D1-D5):

| Rarity | D1 (300) | D2 (350) | D3 (350) | D4 (300) | D5 (200) | **Totale** | Target | Status |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Common** | 220 | 150 | 30 | 0 | 0 | **400** | 400 | ✅ EXACT |
| **Uncommon** | 80 | 150 | 160 | 60 | 0 | **450** | 450 | ✅ EXACT |
| **Rare** | 0 | 50 | 130 | 150 | **70** | **400** | 400 | ✅ EXACT |
| **Epic** | 0 | 0 | 30 | 90 | **115** | **235** | 235 | ✅ EXACT |
| **Legendary** | 0 | 0 | 0 | 0 | **15** | **15** | 15 | ✅ EXACT (cap catalog RAGGIUNTO) |
| **TOTALE tier** | 300 | 350 | 350 | 300 | **200** | **1500** | 1500 | ✅ **EXACT MATCH** |

**R18.5 CATALOGO 1500/1500 COMPLETO** ✅

**Note drift documented** (non-blocking):
- D2 Rare=50 vs blueprint D0 originale Rare D2=70 → drift accettato in D2 closure (PM approved).
- D3 Uncommon=160 vs blueprint D0 originale Uncommon D3=100 → drift accettato in D3 closure (PM approved).
- Aritmetica finale 1500/1500 verificata verbatim con conteggi reali su file JSON (script Python check `sum(counts.values())` su 5 files). Drift compensati end-to-end.

**Governance**: aritmetica cumulativa lockata post-D5. Nessun ulteriore item T1-T5 può essere aggiunto senza rientrare nel target 1500 (o richiesta esplicita PM ridistribuzione).

---

## Sezione 12 — NPC crafting check (5 LOCKED + 0 nuovi in D5)

**5 NPC LOCKED (Q3=B mantenuto verbatim, no autonomous new)**:

| NPC | D5 items | Classi primary | Note endgame T5 |
|---|:---:|---|---|
| `fabbro-bulwark` | 4 | Warrior (heavy armor + hammer + shield) + Priest cross-craft (reliquia post-Q6) | Craft primario warrior heavy T5 endgame |
| `cuoiaia-elfwood` | 4 | Ranger (leather + mail + bow + lance) | Craft primario ranger T5 endgame |
| `sarto-sacro` | 4 | Priest (stoffa + reliquia + bastone + martello) | Craft primario priest holy T5 endgame |
| `tessitrice-arcana` | 4 | Mage (stoffa + wand + staff + tome + focus + robe) | Craft primario mage arcane T5 endgame |
| `conciatore-elfwood` | 4 | Rogue (cuoio + dagger + boots) | Craft primario rogue leather T5 endgame |
| **TOTALE** | **20** | | 10% catalog D5 (bilanciamento endgame vs 8% D4) |

**0 nuovi NPC autonomi in D5**. Eventuali proposte endgame-only PENDING PM Q6 post-D5:
- Candidati narrative-consistent (PENDING): "Maestro Fabbro delle Leggende" (ambash-legendary-forge boss), "Custode del Vuoto" (void-cathedral), "Fabbro-Serafino Cieco" (starforged-approach)
- Governance: nessuna decisione autonoma. PM decide se autorizzare 1-3 nuovi NPC endgame-only iconic T5.

**Cross-craft Priest+Reliquia (post-Q6 lesson propagata)**: presente su `sarto-sacro` T5 (reliquia in weapon_family Priest). NO scudo/piastre/cuoio/maglia per Priest in D5. ✅

---

## Sezione 13 — Lore capstone notes (22/22 lore coverage post-D5)

**Coverage cumulative finale R18.5** post-D5:

| Lore | Coverage endgame D5 | Note |
|---|---|---|
| **Draco** | ✅ **CAPSTONE ENDGAME** — L1 dragonlord-crown Legendary + L6 dragon-elder-scale Legendary + elder-wyrm-descent dungeon + dragon-vault raid (23 items D5) | Record 6× cumulative post-B5. |
| **Vuoto** | ✅ **CAPSTONE ENDGAME** — L2 void-touched-blade Legendary + void-cathedral raid + void-touched-outpost + void-heart-sanctum dungeon (38 items D5) | Ergolat/Vuoto HYBRID: Ergolat selezionato per no-repeat (documentato). |
| **Celeste** | ✅ **CAPSTONE ENDGAME** — L3 seraph-halo-crown Legendary + L7 sole-nero-diadem Legendary + H1 celestial-conclave-mantle HYBRID + celestial-conclave raid + starforged-approach + pantheon-of-fallen-suns (43 items D5, +2 Elite LIVE bridge) | Massima coverage endgame. |
| **Ambash** | ✅ CAPSTONE ENDGAME — L5 ambash-forge-hammer Legendary + ambash-legendary-forge dungeon (9 items D5) | Bracket crafting endgame chiuso. |
| **Alberi della Vita** | ✅ **CAPSTONE ENDGAME** — L4 worldroot-scepter Legendary + world-tree-collapse raid (20 items D5) | Lore-source 2× cumulative R18.5, capstone raid finale ultimo. |
| **Irthe** | ✅ CAPSTONE endgame — H2 irthe-price-shroud HYBRID Legendary (1 item D5 Legendary standalone) | Lore-source deriva morte/prezzo endgame Rogue. |
| **Ergolat** | ✅ CAPSTONE endgame — H3 ergolat-obelisk-focus HYBRID Legendary (1 item D5 Legendary standalone) | Lore-source deriva assenza/obelischi endgame Mage. |
| **Halodi** | ✅ CAPSTONE endgame — H4 halodi-fate-quiver HYBRID Legendary (1 item D5 Legendary standalone) | Lore-source deriva fato/deviazione endgame Ranger. |
| **Adalan** | ✅ CAPSTONE dungeon — tower-of-adalan-summit dungeon B5 endgame (4 items D5) | Chiude bridge B1 broken-tower-of-adalan (3× cumulative). |
| **Alevora** | ✅ CAPSTONE dungeon — alevoran-warlord-throne dungeon B5 (6 items D5) | Chiude bracket militare Alevora (3× cumulative). |
| **Efreto** | ✅ CAPSTONE dungeon — efreto-cursed-nexus dungeon B5 (10 items D5) | Chiude bracket arcane cursed (3× cumulative). |
| **Memoria** | ⚠️ RESERVED D5 progressive-slot-01 (Mage, PENDING PM) — lore-source proposta memoria-echo utility | Capstone T5 progressive (non live). |
| **Luna Morta** | ⚠️ RESERVED D5 progressive-slot-02 (Priest, PENDING PM) — resurrection endgame | Capstone T5 progressive (non live). |
| **Ciclo delle anime** | ⚠️ RESERVED D5 progressive-slot-03 (Rogue, PENDING PM) — soul-bind endgame | Capstone T5 progressive (non live). |
| **Greatwood/Elfwood** | ⚠️ RESERVED D5 progressive-slot-04 (Ranger, PENDING PM) — nature-bond endgame | Capstone T5 progressive (non live). |
| **Infernale** | ✅ Bracket bracket saturato D4 — NO Legendary primary D5 Infernale (D4 emberking-siege raid + emberking-crown hint marker in D4) | Chiuso D4 endgame. |
| **Krastlov** | ❌ NO T5 endgame — variety watch obbligatoria post-B4 rispettata | Chiuso D3 (bracket military standard). |
| **Faglie arcane** | ❌ NO T5 endgame — variety watch | Chiuso D3 (bracket arcane standard). |
| **Aveol** | ❌ NO T5 endgame — variety watch | Chiuso D3. |
| **Soe** | ❌ NO T5 endgame — variety watch | Chiuso D2 (bracket early standard). |
| **Velur** | ❌ NO T5 endgame — variety watch | Chiuso D2 (bracket early standard). |
| **Mare** | ❌ NO T5 endgame — variety watch | Chiuso D3 (bracket standalone standard). |

**Coverage lore-source status post-D5**:
- **22/22 lore-sources hanno rappresentazione R18.5** ✅ (Vuoto introdotta B5, 17ª Gate 1 cross-check audit sync `r18_5_phase_c0quater_live_dungeon_audit.json` PENDING Q9).
- **11 lore capstone T5 LIVE** (Draco, Vuoto, Celeste, Ambash, Alberi della Vita, Irthe, Ergolat, Halodi, Adalan, Alevora, Efreto)
- **4 lore capstone T5 PROGRESSIVE placeholders PENDING PM** (Memoria, Luna Morta, Ciclo delle anime, Greatwood/Elfwood)
- **7 lore chiuse pre-D5** (Infernale D4, Krastlov D3, Faglie arcane D3, Aveol D3, Soe D2, Velur D2, Mare D3) — variety watch rispettata

**Lore teaser T4 → capstone T5**:
- 7 Legendary hint T4 (documentati in D4 Sezione 11) → **materializzati in T5 come Legendary reali** (7 approved + 4 hybrid + 4 progressive)
- **NO più teaser in T5** (Sezione 10.3 legendary_hint_items_deprecated_t5)

---

## Sezione 14 — Iconic-family split 3-way (Q4 PM directive propagata)

**Directive PM Q4=A verbatim propagata da D4**: da D4 in poi distinguere split obbligatorio.

| Categoria | D5 count | Definizione | % D5 |
|---|:---:|---|:---:|
| **(1) Pure evolutions T4→T5** | **69** | Items T5 con iconic-family che estende una base family già presente in D1-D4 (es. `dragonhunter-endgame`, `elder-wyrm-hunter`, `elder-wyrm-stalker`, `adalan-archmage-t5`, `sunfallen-champion`, `worldbreaker`, `emberking-endgame`, `efreto-corrupt-caster`, `efreto-purger`, `efreto-cursed-ranger`, `adalan-arcane-thief`, `ambash-arcane-forge`, `ambash-forge-warrior`, `alevoran-perpetual`, `elfwood-worldroot`). Progressione stat-a-stat con evoluzione endgame T5. | 34.5% |
| **(2) Intra-family extensions** | **0** | Nessuna variante nuova di classe di famiglia esistente in D5 (endgame favorisce free/new standalone) | 0.0% |
| **(3) Free/new T5 endgame families** | **131** | Famiglie completamente nuove first-appearance D5 endgame: `dragonlord-vanguard`, `void-warden`, `void-shade`, `silent-heart`, `pantheon-shadow`, `celestial-scholar`, `pantheon-conjurer`, `worldtree-loremaster`, `seraph-halo-priest`, `celestial-conclave-priest`, `void-cleric`, `pantheon-oracle`, `worldroot-druid-priest`, `starforged-vessel`, `elder-wyrm-shepherd`, `worldroot-warden`, `halodi-fate-ranger`, `celestial-starforged-ranger`, `void-scout`, `pantheon-marksman`, + **15 iconic Legendary standalone** (dragonlord-legendary, void-touched-legendary, seraph-halo-legendary, worldroot-legendary, ambash-forge-legendary, dragon-elder-legendary, sole-nero-legendary, celestial-conclave-hybrid, irthe-price-hybrid, ergolat-obelisk-hybrid, halodi-fate-hybrid, progressive-discovery-pending). | 65.5% |
| **TOTALE** | **200** | ✅ | 100% |

**Nota trasparenza endgame**: il pattern "free/new endgame families" dominante (65.5%) è coerente con Batch 5 come **bracket capstone endgame** (Legendary discovery + capstone lore + PROGRESSIVE placeholders). Le pure evolutions (34.5%) mantengono continuità narrative con D1-D4 (dragonhunter, elder-wyrm-hunter, adalan-archmage, sunfallen-champion, emberking-endgame, efreto-purger, ecc.). Intra-family = 0 perché endgame preferisce standalone finale rispetto a estensioni intra. Q per PM validation split.

---

## Sezione 15 — Risk notes + Open Questions post-D5 per PM

### 15.1 Risk notes (12 rischi)

| ID | Severity | Topic | Mitigation |
|---|:---:|---|---|
| risk_1 | **HIGH** | 15 Legendary composition contiene 4 PROGRESSIVE placeholders con PENDING PM fields (lore-source finale + source finale + utility numeric finale + drop rate finale) — richiedono finalization prima runtime apply | Placeholders esplicitamente marcati `PENDING PM` su lore_source, source, utility_unique + `chain_tag=PROGRESSIVE-4`. Governance: no autonomous decision. Q1-Q4 post-D5. |
| risk_2 | MEDIUM | 4 HYBRID Legendary condividono lore-source con approved (H1 Celeste-mantle Priest overlap con L3 seraph-halo-crown Priest; H4 Halodi-ranger nuovo standalone; H2 Irthe-Rogue nuovo standalone; H3 Ergolat-Mage nuovo standalone) — potential utility overlap con approved | Utility unique diversificate: L3 (Divine Resurrect) vs H1 (Celestial Barrier assorbimento). Documentato governance no-repeat lore-source per H3 (Ergolat over Vuoto). |
| risk_3 | MEDIUM | Legendary utility numeriche in `stat_principali` sono narrative descriptors, NON valori numerici finali (cooldown, scaling, %) — PENDING PM Phase D-post gate | Coerente con Legendary Discovery Chain STEP 8 governance: utility fantasy proposals only, numeric finals PENDING PM. Q4 post-D5. |
| risk_4 | MEDIUM | Ergolat HYBRID (H3) selezionato al posto di Vuoto — decisione documentata come letterale fulfillment PM directive "Ergolat OR Vuoto, scegli quella non ancora usata dai 7 approvati" (Vuoto già in L2 approved). Se PM vuole Vuoto HYBRID (double-tap), swap richiesto | `chain_tag='HYBRID-4 (H3 Ergolat/Vuoto — Ergolat selezionato per no-repeat Vuoto)'` esplicito. PM decide swap in Q3 post-D5. |
| risk_5 | LOW | Iconic family split 3-way: T5 endgame domina free/new endgame (65.5%) rispetto a pure T4→T5 evolutions (34.5%) e intra-family = 0 | Documentato coerente con endgame bracket (Legendary discovery + capstone). Q per PM validation split. |
| risk_6 | LOW | Naming iconic families endgame ridondanza con D4 (dragonhunter, elder-wyrm-hunter, ambash-forge-warrior, alevoran-perpetual) — potenziale drift naming cumulativo D1-D5 | Annotato per **naming pass globale post-D5** come da direttiva PM D3 Q8 + D4 Q7=B closure check verbatim + slug drift D4 documented. |
| risk_7 | LOW | Coverage lore capstone T5 non copre Memoria/Luna Morta/Ciclo delle anime/Greatwood/Elfwood come Legendary approved+hybrid (solo progressive placeholders PENDING) — potenziale under-representation endgame | Progressive placeholders con lore-source proposals documentate (P1-P4). PM decide finalization in Q1-Q4 post-D5. |
| risk_8 | LOW | Weapon family L4 worldroot-scepter Ranger usa `lancia` (proficiency-valid) invece di `arco` per differenziazione da P4 progressive-slot-04 (arco). Coerente ma anomalia narrativa scettro-lancia | Scettro-lancia radice narrativamente accettabile (documentato). PM decide se swap a bastone/arco in Q post-D5. |
| risk_9 | LOW | H4 halodi-fate-quiver Ranger slot=trinket (non main-hand) — differenzia da P4 progressive-slot-04 (main-hand arco) | Trinket slot valido per Ranger. Documentato coerente. |
| risk_10 | LOW | 17ª Gate 1 lore-source audit cross-check ancora PENDING (documentato in B5 matrix risk_8 e Q17 B5) | Cross-check formale con audit C0-quater da eseguire pre-Phase C tech dry-run. Non blocca D5. Q9 post-D5. |
| risk_11 | LOW | Aritmetica cumulativa Rare drift D2 (50 vs blueprint D0 70) e Uncommon drift D3 (160 vs blueprint D0 100) — drift accettati in D2/D3 closure (PM approved) | Documentato accettato PM D2/D3 closure. Aritmetica finale 1500/1500 verificata verbatim con conteggi reali (Sezione 11). |
| risk_12 | LOW | Cap Legendary catalog 15/15 raggiunto — no future Legendary senza PM decision (blueprint D0 Sezione 11: "8 slot margine future gate" ora ridotto a 0) | Documentato. Se PM autorizza future Legendary post-R18.5, richiesta esplicita ridistribuzione o cap increase. |

**Totali**: 12 rischi (1 HIGH · 4 MEDIUM · 7 LOW). risk_1 HIGH = **PROGRESSIVE placeholders PENDING PM finalization** — mitigato con chain_tag esplicito e documentazione governance. Nessun BLOCKER runtime (Phase C tech dry-run non toccata).

### 15.2 Open Questions post-D5 per PM (15 Q)

| ID | Topic |
|---|---|
| **Q1** | Approvare 200 items T5 verbatim (0/0/70/115/15 rarity) o iterare selettivamente? |
| **Q2** | Approvare 15 Legendary composition: 7 APPROVED (from Chain STEP 8) + 4 HYBRID (H1 Celeste-mantle Priest, H2 Irthe-shroud Rogue, H3 Ergolat-focus Mage, H4 Halodi-quiver Ranger) + 4 PROGRESSIVE placeholders (P1 Mage-memoria, P2 Priest-resurrection, P3 Rogue-soul-bind, P4 Ranger-nature-bond) — PENDING PM finalization utility+source+drop rate su 4 progressive? |
| **Q3** | Approvare scelta Ergolat over Vuoto per H3 HYBRID (no-repeat Vuoto già in L2 approved void-touched-blade) o swap a Vuoto-focus Mage (double-tap)? |
| **Q4** | Approvare Legendary utility numeriche narrative (fantasy proposals) come layer design, con numeric finals (cooldown, %, scaling) PENDING gate PM Phase D-post o iterare adesso? |
| **Q5** | Approvare naming IT verbatim per 200 items o rinominare selettivamente in naming pass globale post-D5? |
| **Q6** | Approvare craft NPC usage (5 LOCKED, 0 nuovi autonomi in D5) o autorizzare 1-3 nuovi NPC endgame-only iconic T5 (Maestro Fabbro delle Leggende, Custode del Vuoto, Fabbro-Serafino Cieco)? |
| **Q7** | Approvare source coverage: 85 dungeon B5 + 61 raid + 10 Elite + 20 craft NPC + 24 achievement/ranking/quest/vendor = 200 o iterare bilanciamento? |
| **Q8** | Approvare aritmetica cumulativa finale 1500/1500 verbatim (400 Common + 450 Uncommon + 400 Rare + 235 Epic + 15 Legendary), con drift D2/D3 accettati documentati (Sezione 11)? |
| **Q9** | Approvare lore capstone T5 22/22 con 17ª Gate 1 cross-check ancora PENDING (mitigation risk_10)? Autorizzare cross-check audit sync pre-Phase C? |
| **Q10** | **Balance pass globale post-D5**: quando avviare? Blueprint D0 iniziale prevedeva Uncommon/Rare/Epic drift accettati; ora richiede balance pass su drift D2/D3 cumulativi accettati + gap analysis 1500 catalog. |
| **Q11** | **Naming pass globale post-D5**: quando avviare? D1-D5 hanno drift naming cumulativi (iconic family ridondanze + slug D4 drift documented + potenziali endgame ridondanze). |
| **Q12** | Autorizzare PRD.md append `R18.5 Phase D5 CLOSED` + `R18.5 CATALOGO 1500/1500 COMPLETO` post-review formale (**NON auto-eseguito**, richiede GO esplicito PM)? |
| **Q13** | Post-D5 next gate: (A) Balance pass, (B) Naming pass, (C) Phase C tech dry-run (proficiency runtime + class_slug migration + ILVL endgame implementation), (D) R18.6 kickoff (Class Halls), (E) Marketing brief, (F) Pausa gate PM consolidamento base creativa? |
| **Q14** | Legendary drop rate design (2% raid boss finale APPROVED + 1% dungeon endgame APPROVED + rate HYBRID direzionale documentale + rate PROGRESSIVE PENDING) — mantenere direzionale documentale o approfondire numeric finals in Phase D-post gate? |
| **Q15** | R18.5 catalogo 1500/1500 completato (assumendo Q1-Q14 approved) — attivare Phase C tech dry-run o pausa consolidamento base creativa? |

---

## Governance check STEP 18 (D5)

| Voce | Stato |
|---|---|
| **36 sigilli byte-identical** | ✅ VERIFIED (pytest 6/6 pre-write; da ri-verificare post-write) |
| Zero DB writes | ✅ ZERO |
| Zero code changes `.py`/`.js`/`.jsx`/`.tsx`/`.ts` | ✅ ZERO |
| Zero migrations / apply scripts | ✅ ZERO |
| Zero item creation live | ✅ ZERO |
| Zero drop table apply | ✅ ZERO |
| Zero economy changes | ✅ ZERO |
| `lore_meta.py` invariato | ✅ INVARIATO |
| Zero sealed file modification | ✅ ZERO |
| Zero hard delete | ✅ ZERO |
| Zero runtime bridge activation | ✅ ZERO |
| Zero class_slug migration | ✅ ZERO |
| Zero proficiency runtime enforcement | ✅ ZERO (documental only, HARD static check verified INCLUSI Legendary) |
| Zero anti-P2W runtime validator | ✅ ZERO (documental only) |
| **Priest scudo/piastre/cuoio/maglia HARD BLOCK** | ✅ **ZERO usi (post-Q6 lesson propagata a D5)** |
| **Proficiency 200/200 HARD verified** | ✅ **0 violazioni (inclusi 15 Legendary)** |
| Weapon backlog `strumento`/`falce`/`trinket_backlog` = 0 usi | ✅ VERIFIED |
| D5 NON auto-transition (STOP after D5) | ✅ (STOP dopo D5, no Phase C tech / R18.6 / balance / naming pass auto-start) |
| Signature planning ZERO | ✅ (Phase C tech + Signature system future) |
| R18.6 code implementation ZERO | ✅ (design docs only in PRD roadmap) |
| Classi canoniche verbatim | ✅ Warrior/Rogue/Mage/Priest/Ranger |
| PM autonomous decision new | ✅ ZERO (4 progressive slots esplicitamente PENDING PM, Ergolat over Vuoto scelta documentata come letteral fulfillment PM directive) |
| Files deliverable | ✅ 2 (.md + .json) |
| Items deliverable total | ✅ 200 |
| Rarity target 0/0/70/115/15 | ✅ EXACT MATCH |
| Class target 40×5 | ✅ EXACT MATCH |
| Level range 56-60 | ✅ VERIFIED |
| Epic 115/115 | ✅ EXACT MATCH |
| Rare 70/70 | ✅ EXACT MATCH |
| Legendary 15/15 | ✅ EXACT MATCH (cap catalog RAGGIUNTO) |
| Aritmetica cumulativa 1500/1500 | ✅ **EXACT MATCH** |
| No Common / No Uncommon endgame | ✅ VERIFIED (D5 = 0 Common + 0 Uncommon endgame) |
| **PRD append `R18.5 Phase D5 CLOSED`** | 🔒 **NON eseguito** (rinviato post-approvazione formale PM — pattern D3/D4 rispettato) |

---

## Statement finale (obbligatorio brief PM)

**STOP dopo D5. R18.5 CATALOGO 1500/1500 COMPLETO.** Attendo PM review formale delle Open Questions Q1-Q15 + GO esplicito prima di:
- PRD.md append `R18.5 Phase D5 CLOSED` + `R18.5 CATALOGO 1500/1500 COMPLETO`
- Next gate decision: Balance pass / Naming pass / Phase C tech dry-run / R18.6 kickoff / Marketing brief / Pausa consolidamento

**NO auto-transition a Phase C tech dry-run.** **NO auto-transition a R18.6.** **NO balance pass autonomo.** **NO naming pass autonomo.** **NO seal touch.** **NO codice/DB/migrations.** **NO PRD append D5 CLOSED auto** (rinviato a post-PM-approval — pattern D3/D4 verbatim rispettato).

---

**R18.5 status flow (aggiornato post-STEP 18)**:
`Phase A` ✅ → `Phase B.1/B.2` ✅ → `Gate 1` ✅ → `Phase C0` ✅ → `Phase C0-bis` ✅ → `Gate 2` ✅ + `Phase C0-ter` ✅ → `Phase C0-quater Batch 1` ✅ CLOSED → `Phase C0-quinquies Batch 2` ✅ CLOSED → `Phase C0-sexies Batch 3` ✅ CLOSED → `Phase C0-septies Batch 4` ✅ CLOSED → `Phase C0-octies Batch 5 ENDGAME` ✅ CLOSED → `Mini-Gate Legendary Chain STEP 8` ✅ CLOSED → `Phase D0 STEP 9` ✅ CLOSED → `Phase D pre-D1 Iconic Starter STEP 10` ✅ CLOSED → `Phase D1 T1×300 STEP 11` ✅ CLOSED → `Phase D2 pre-Craft NPC STEP 12` ✅ CLOSED → `Phase D2 T2×350 STEP 13` ✅ CLOSED → `Phase D3 T3×350 STEP 14+15` ✅ CLOSED (post-Q6 fix) → `Phase D4 T4×300 STEP 16+17` ✅ CLOSED (slug drift documented, naming pass deferred post-D5) → **`Phase D5 T5×200 ENDGAME STEP 18`** 🟡 **DRAFT — PENDING PM Q1-Q15 review** → **`R18.5 CATALOGO 1500/1500 COMPLETO (post-approval)`** 🔒 **PENDING PM formal review** → `Post-D5 gates` 🔒 (Balance/Naming/Phase C tech/R18.6/Marketing/Pausa — PENDING PM Q13 decision) / `R18.6 Class Halls` 🔒 HOLD UNTIL R18.5 COMPLETE

---

**FINE STEP 18 — R18.5 Phase D5 T5×200 ENDGAME Item Table Drafting — DOCUMENTAL ONLY — CATALOGO R18.5 1500/1500 COMPLETO (POST-APPROVAL FORMAL PM)**
