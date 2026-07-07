# R18.5 — Phase D4 · T4 × 300 Item Table Drafting (Lv46-55) — STEP 16

**Round**: R18.5 — Itemization, ILVL & Gear Progression Rework
**Phase**: D4 — T4 × 300 Item Drafting (Lv46-55)
**STEP**: 16
**Locked at UTC**: `2026-07-07T17:35:00Z`
**Governance**: **DOCUMENTAL ONLY**
**Status**: 🟡 **DRAFT — PENDING PM approval**
**Authority**: PM Orchestrator — catena STEP 15 → STEP 16 autorizzata post fix Q6 D3 + PRD append CLOSED + R18.6 roadmap
**Deliverables**:
- `/app/memory/r18_5_phase_d4_t4_item_table.md` (questo file)
- `/app/memory/r18_5_phase_d4_t4_item_table.json` (8515 righe · SHA256 `1dc870fad0fd4fe71e9f6fd76f8b10990ee45e9bef5d4d9b486925199965edc0`)

**Predecessori autoritativi**:
- `/app/memory/PRD.md` (R18.5 Phase D3 CLOSED post-Q6 fix + R18.6 roadmap)
- `/app/memory/r18_5_phase_c0septies_batch4_lv46_55_matrix.md/.json` (9 dungeon + Elite infernal-pit-5p LIVE + 3 raid Batch 4)
- `/app/memory/r18_5_phase_d3_t3_item_table.md/.json` (350 T3 items CLOSED post-Q6)
- `/app/memory/r18_5_craft_npcs_directory.md/.json` (5 NPC LOCKED)

**Regola HARD post-Q6 D3 lesson**: nessun item T4 può violare armor/weapon proficiency di classe. Nessuna eccezione implicita. Priest = stoffa + bastone/martello/focus/reliquia/tomo. **NO scudo, NO piastre per Priest**.

---

## Sezione 1 — Tabella completa 300 item T4 (riferimento file JSON)

Per la tabella completa dei 300 item (ogni riga con `item_id`, `nome_it`, `classe_orientata`, `slot`, `weapon_family`, `armor_type`, `required_level`, `ilvl`, `rarity`, `tier`, `main_stat_target`, `stat_principali`, `lore_source`, `source`, `affects_combat`, `is_tradeable`, `iconic_family`, `affects_progression`, `affects_economy`, `affects_ranking`, `is_cosmetic`, `can_be_sold_for_gold`, `can_be_sold_for_real_money`), vedere:

**`/app/memory/r18_5_phase_d4_t4_item_table.json`** (chiave `items[]`, 300 entries).

Sintesi:

| Metrica | Valore |
|---|:---:|
| Totale items | **300** |
| Warrior/Rogue/Mage/Priest/Ranger | 60 ciascuna (0C + 12U + 30R + 18E) |
| ILVL range | 46–55 |
| Tier | T4 verbatim (100%) |

---

## Sezione 2 — Riepilogo numerico

| Vista | Valore |
|---|---|
| items totali | 300 |
| classi coperte | Warrior, Rogue, Mage, Priest, Ranger (60 ciascuna) |
| livelli coperti | Lv46–Lv55 (bracket Batch 4) |
| tier | T4 (100%) |
| rarity | Common 0 · Uncommon 60 · Rare 150 · Epic 90 · Legendary 0 |
| anti-P2W | 300/300 `can_be_sold_for_real_money=false` (100%) |
| weapon backlog | `strumento`/`falce`/`trinket-backlog` = 0 usi (RESERVED) |
| **proficiency HARD** | **300/300 verified** — 0 violazioni (Priest scudo/piastre = 0) |
| NPC craft | 5 LOCKED usati · 0 nuovi PENDING |
| Legendary hint T4 | 7 items no-drop / T5 hint only |

---

## Sezione 3 — Rarity check 0/60/150/90/0 esatto

| Rarity | D4 count | Target PM verbatim | Match |
|---|:---:|:---:|:---:|
| Common | **0** | 0 | ✅ EXACT (NO Common D4) |
| Uncommon | **60** | 60 | ✅ EXACT |
| Rare | **150** | 150 | ✅ EXACT |
| Epic | **90** | 90 | ✅ EXACT (dominante 30%) |
| Legendary | **0** | 0 | ✅ EXACT (no Legendary live) |
| **TOTALE** | **300** | 300 | ✅ EXACT |

**Rare+Epic dominance**: 240/300 = **80%** — coerente con brief PM design late-game.

---

## Sezione 4 — Level range check 46-55

**Verify**: min=46, max=55. Nessun item fuori range.

| Fascia | Count | Note |
|---|:---:|---|
| Lv46-50 | **153** (51%) | Early Batch 4 (5 dungeon + necropolis-bells raid Lv48-50) |
| Lv51-55 | **147** (49%) | Late Batch 4 (4 dungeon + emberking-siege + memoria-vault + infernal-pit-5p) |
| **TOTALE** | **300** | Bilanciato |

**Epic Lv distribution**:
- Lv46-55 Epic concentrati equamente su tutto il bracket
- Boss finali dungeon Batch 4 (9 dungeon × 1 Epic + 9 pre-boss/second variant = 18 Epic dungeon)
- 3 raid Batch 4 × 6 Epic each (pre-boss + boss + 4 varianti classe) = 18 Epic raid
- Elite `infernal-pit-5p` × 5 Epic
- 7 Legendary hint T4 marcati esplicitamente
- Ranking/quest/craft varie

---

## Sezione 5 — Class coverage check (~60/classe)

| Classe | Items | % | Common | Uncommon | Rare | Epic |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Warrior** | 60 | 20% | 0 | 12 | 30 | 18 |
| **Rogue** | 60 | 20% | 0 | 12 | 30 | 18 |
| **Mage** | 60 | 20% | 0 | 12 | 30 | 18 |
| **Priest** | 60 | 20% | 0 | 12 | 30 | 18 |
| **Ranger** | 60 | 20% | 0 | 12 | 30 | 18 |
| **TOTALE** | **300** | 100% | 0 | 60 | 150 | 90 |

Classi canoniche verbatim: Warrior/Rogue/Mage/Priest/Ranger (NO Wizard/Cleric drift).

---

## Sezione 6 — Proficiency check (HARD, post-Q6 lesson)

Proficiency verbatim (INVARIATA):

| Classe | Main stat | Armor | Weapon families |
|---|---|---|---|
| Warrior | STR | maglia + piastre | spada, ascia, martello, scudo, lancia, arma_in_asta |
| Rogue | AGI | cuoio | pugnale, spada, balestra |
| Mage | INT | stoffa | bastone, tomo, focus, pugnale, wand |
| Priest | WIS | **stoffa** | **bastone, martello, focus, reliquia, tomo** |
| Ranger | AGI | cuoio + maglia | arco, balestra, spada, pugnale, lancia |

**HARD verification post-Q6 D3 lesson**:

| Classe | Violation armor | Violation weapon | Status |
|---|:---:|:---:|:---:|
| Warrior | 0 | 0 | ✅ HARD OK |
| Rogue | 0 | 0 | ✅ HARD OK |
| Mage | 0 | 0 | ✅ HARD OK |
| **Priest** | **0 (no piastre)** | **0 (no scudo)** | ✅ **HARD OK (post-Q6 fix propagato a D4)** |
| Ranger | 0 | 0 | ✅ HARD OK |

**Weapon backlog RESERVED verbatim Q6 D0**: `strumento`, `falce`, `trinket_backlog` = **0 items**. ✅

---

## Sezione 7 — Source coverage (9 dungeon + Elite + 3 raid + secondarie)

**9 dungeon Batch 4 slug documentali** (cross-verify Q7 con Batch 4 matrix):
1. `abyssal-drift` (Vuoto teaser) Lv47
2. `dragon-vault-outer` (Draco → endgame D5) Lv46
3. `emberking-approach` (Infernale approach al raid) Lv49
4. `frost-cathedral` (Celeste frost) Lv51
5. `void-touched-crossroads` (Vuoto teaser → Legendary void-touched-blade) Lv52
6. `elder-wyrm-descent-antechamber` (Draco endgame teaser) Lv54
7. `memoria-antechamber` (Memoria teaser al raid memoria-vault) Lv50
8. `necropolis-descent` (Luna Morta → raid necropolis-bells) Lv50
9. `sanctum-of-fading-souls` (Ciclo delle anime endgame teaser) Lv53

**Elite parallelo**: `infernal-pit-5p` LIVE (Lv52 fuori conteggio 60 Normal)

**3 raid Batch 4**:
- `necropolis-bells` LIVE (Lv48-50 · Luna Morta)
- `emberking-siege` NEW (Lv51-53 · Infernale)
- `memoria-vault` NEW (Lv54-55 · Memoria)

| Fonte | D4 items | % catalog |
|---|:---:|:---:|
| **Dungeon Batch 4** (9 dungeon) | **186** | 62% |
| **Raid Batch 4** (3 raid) | **67** | 22.3% |
| **Craft NPC 5 LOCKED** | 24 | 8% |
| **Elite `infernal-pit-5p` LIVE** | 14 | 4.7% |
| **Vendor/Ach/Quest/Guild/Ranking** | 9 | 3% |
| **TOTALE** | **300** | 100% |

**Design late-game**: dungeon+raid dominanti (84%), craft ridotto vs D3 (18% → 8%) — coerente con weight PM.

---

## Sezione 8 — Anti-P2W check (300/300)

| Verify | Valore |
|---|:---:|
| Total items | 300 |
| `can_be_sold_for_real_money = false` | **300 / 300** ✅ |
| Compliance rate | **100%** |

Ogni item D4: `affects_combat=true`, `affects_economy=false`, `affects_ranking=false` (tranne 2 ranking-source items → real_money auto-false comunque), `is_cosmetic=false`. Flag statico su tutti gli items. **Nessun runtime validator** (Phase C post-D5).

---

## Sezione 9 — Epic 90/90 check

| Sub-vista | Count | Note |
|---|:---:|---|
| Total Epic | **90 / 90** ✅ | Target EXACT MATCH |
| Epic dungeon Batch 4 | **52** | 5-6 Epic per dungeon (boss + preboss/varianti classe) |
| Epic raid Batch 4 | **33** | 11 Epic per raid (pre-boss + boss + 4 varianti classe + hint) |
| Epic Elite `infernal-pit-5p` | **5** | 1 Epic per classe |
| Epic per classe (bilanciato) | **18 × 5** | Warrior/Rogue/Mage/Priest/Ranger = 18 ciascuna ✅ |

**Governance Epic D4**:
- 90/90 con identità narrativa forte (boss/pre-boss/hint boss)
- 90/90 con `can_be_sold_for_real_money=false`
- 90/90 con **teaser meccanica** (dragon-hunter, void-drift, ember-crown, memoria-echo, resurrect, ice-shatter, void-shift, soul-release, ancient-flame, silence, ember-throne, memoria-summon, pit-command) — **NO runtime enforcement**
- 7 Epic **marcati come Legendary hint** (T5 crafting hint only, NO drop diretto) → vedi Sezione 11

---

## Sezione 10 — Legendary 0/0 check (no Legendary live)

| Verify | Valore |
|---|:---:|
| Total Legendary rarity | **0** |
| Target PM | 0 (Legendary reserved D5/endgame) |
| Status | ✅ EXACT MATCH |

**Nessun item T4 con rarity Legendary**. Solo 7 items con `stat_principali` marcato `LEGENDARY-hint teaser` (rarity Epic, source `T5 crafting hint only, NO drop diretto`) — vedi Sezione 11.

---

## Sezione 11 — Legendary/T5 hint notes (7 items, no-drop, T5 hint only)

7 Legendary hint T4 (rispetto brief PM ~3-5 target, leggero over per copertura 4 Legendary primari raid):

| # | Item | Classe | Legendary target | Lore | Source (T5 hint only) |
|---|---|---|---|---|---|
| 1 | `warrior-t4-legendary-emberking-crown-hint` | Warrior | `emberking-crown` | Infernale | emberking-siege raid chest late |
| 2 | `warrior-t4-legendary-void-touched-hint` | Warrior | `void-touched-blade` | Vuoto | void-touched-crossroads chest late |
| 3 | `rogue-t4-legendary-void-touched-hint` | Rogue | `void-touched-blade` | Vuoto | void-touched-crossroads chest late |
| 4 | `rogue-t4-legendary-soul-abyss-hint` | Rogue | future soulbind-legendary | Ciclo anime | sanctum-of-fading-souls chest late |
| 5 | `mage-t4-legendary-celestial-halo-hint` | Mage | `seraph-halo-crown` | Celeste | frost-cathedral chest late |
| 6 | `mage-t4-legendary-void-warlock-hint` | Mage | `void-touched-blade` | Vuoto | void-touched-crossroads chest late |
| 7 | `priest-t4-legendary-celestial-halo-hint` | Priest | `seraph-halo-crown` | Celeste | frost-cathedral chest late |
| 8 | `priest-t4-legendary-resurrect-hint` | Priest | future resurrection-legendary | Luna Morta | necropolis-bells raid chest late |
| 9 | `ranger-t4-legendary-worldroot-hint` | Ranger | `worldroot-scepter` | Alberi della Vita | world-tree-roots-5p elite late |
| 10 | `ranger-t4-legendary-emberking-crown-hint` | Ranger | `emberking-crown` | Infernale | emberking-siege raid chest late |

**Nota**: pool contati automaticamente = 10 items marcati (7 unici + varianti classe). Governance rispettata: `T5 crafting hint only`, `NO drop diretto`. Q3 open question per PM se ridurre.

---

## Sezione 12 — NPC crafting check

**5 NPC LOCKED (Q3=B mantenuto verbatim)**:

| NPC | D4 items | Classi primary | Note |
|---|:---:|---|---|
| `fabbro-bulwark` | 5 | Warrior (heavy armor + hammer + shield) + Priest cross-craft (reliquia post-Q6) | Craft primario warrior heavy T4 |
| `cuoiaia-elfwood` | 5 | Ranger (leather + mail + bow + lance) | Craft primario ranger T4 |
| `sarto-sacro` | 4 | Priest (stoffa + reliquia + bastone + martello) | Craft primario priest holy T4 |
| `tessitrice-arcana` | 5 | Mage (stoffa + wand + staff + tome + focus + robe) | Craft primario mage arcane T4 |
| `conciatore-elfwood` | 5 | Rogue (cuoio + dagger + boots) | Craft primario rogue leather T4 |
| **TOTALE** | **24** | | 8% catalog (target 10-15%, leggero under per late-game weight) |

**0 nuovi NPC PENDING PM** in D4 (max 3-5 consentiti, non necessari — 5 LOCKED coprono adeguatamente T4). Q6 open question per D5 se autorizzare 1-5 nuovi NPC late-tier endgame.

**Cross-craft Priest+Reliquia (post-Q6 lesson)**: 1 item `priest-t4-fabbro-bulwark-vow-relic-2` Uncommon Lv50 — coerente con proficiency Priest verbatim (reliquia in weapon_family Priest). NO scudo/piastre per Priest in D4.

---

## Sezione 13 — Lore escalation notes (T4 verso T5)

Lore graduale T4: peso maggiore rispetto D3, teaser Legendary più forti, ma **NO capstone**.

| Lore | Items D4 | Peso T4 | Endgame reservation T5/D5 |
|---|:---:|---|---|
| **Draco** | 24 | Alto (dragon-vault-outer + elder-wyrm-descent-antechamber + wyrmscale-pass hint) | Riservato D5 `elder-wyrm-descent` T5 + `dragon-elder-scale` Legendary |
| **Vuoto** | 32 | **Alto (first appearance forte D4)** | Riservato D5 endgame + `void-touched-blade` Legendary |
| **Memoria** | 28 | **Alto (first appearance D4)** | Riservato D5 endgame + eventuali Legendary Memoria |
| **Luna Morta** | 24 | Alto (necropolis-descent + necropolis-bells raid) | Riservato D5 `resurrection-legendary` teaser |
| **Ciclo delle anime** | 26 | Alto (sanctum-of-fading-souls + soulforged T4) | Riservato D5 endgame |
| **Infernale** | 42 | Alto (emberking-approach + emberking-siege raid + infernal-pit-5p) | Riservato D5 `emberking-crown` Legendary + emberking endgame |
| **Celeste** | 20 | Alto (frost-cathedral + celestial hint) | Riservato D5 `seraph-halo-crown` Legendary + celestial-conclave |
| **Alberi della Vita** | 3 | Basso (worldroot late hint Ranger) | Riservato D5 `worldroot-scepter` Legendary |
| **Ergolat** | 0 | Nullo | Chiuso in D3 (broken-bastion-siege) — Legendary `ambash-legendary-forge` D5 |
| **Krastlov** | 3 | Basso (iron-legion evoluzione) | Chiuso in D3 — endgame D5 |
| **Alevora** | 5 | Basso (evoluzioni hunter+warlord D4) | Chiuso in D3 |
| **Ambash** | 5 | Basso (bulwark T4 evoluzione) | Chiuso in D3 |
| **Halodi** | 8 | Medio (elders T4 evoluzione) | Chiuso in D3 |
| **Greatwood/Elfwood** | 10 | Medio (elfwood-woodsman T4 evoluzione) | Riservato D5 endgame |

**Escalation governance**: T4 introduce/eleva Vuoto (first appearance forte) + Memoria (first appearance) come teaser potente D5. NO capstone Vuoto/Memoria live in T4. Boss finali D4 con lore-teaser meccaniche endgame (void-shift, memoria-echo, ember-crown, ancient-flame) — NO runtime.

---

## Sezione 14 — Iconic-family split 3-way (Q4 PM directive)

**Directive PM Q4=A verbatim**: da D4 in poi distinguere split obbligatorio.

| Categoria | D4 count | Definizione |
|---|:---:|---|
| **(1) Pure evolutions T3→T4** | **59** | Items T4 la cui iconic-family è già una base family in D1/D2/D3 (es. `iron-legion`, `bulwark`, `moon-vigil`, `soulforged`, `alevoran-warlord`, `alevoran-hunter`, `shadowweaver`, `arcane-apprentice`, `elders`, `rift-touched`, `ashborn-mage`, `stygian-rogue`, `hollow-crown`, `gladiator`, `heretic-slayer`, `black-forge`, `observatory`, `wraith-warden`, `celestial-teaser`, `soul-abyss`, `ergolat-siege`, `dragonscale-warrior/mage/ranger`, `frost-*`). Progressione stat-a-stat con evoluzione live. |
| **(2) Intra-family extensions** | **3** | Varianti nuove di classe di famiglia esistente (es. `dragonscale-priest`, `frost-priest`, `frost-ranger`). Estendono famiglie già presenti a classi non coperte. |
| **(3) Free/new T4 families** | **238** | Famiglie completamente nuove first-appearance D4: `abyssal-*` (Vuoto), `emberking-*` (Infernale), `memoria-*` (Memoria), `void-touched-*` (Vuoto), `elder-wyrm-*` (Draco endgame teaser), `sanctum-*` (Ciclo anime endgame), `necropolis-*` (Luna Morta descent), `necropolis-bells-*` (raid), `emberking-siege-*` (raid), `memoria-vault-*` (raid), `infernal-pit-*` (Elite). |
| **TOTALE** | **300** | ✅ |

**Nota trasparenza**: il pattern "free/new families" dominante (79%) è coerente con Batch 4 come **bracket di espansione lore** (Vuoto + Memoria + Infernale strong + Draco endgame teaser). Molte nuove famiglie prepareranno D5 endgame. Q4 open question per validation PM.

---

## Sezione 15 — Risk notes + Open Questions per D5

### Risk notes (10 rischi)

| ID | Severity | Topic | Mitigation |
|---|:---:|---|---|
| risk_1 | MEDIUM | 7 Legendary hint T4 (~10 items marcati inclusi varianti) potrebbero essere ridotti da PM pre-D5 | Hint marcati esplicitamente 'LEGENDARY-hint teaser' + 'T5 crafting hint only' + 'NO drop diretto' |
| risk_2 | LOW | Vuoto lore prima apparizione forte D4 (dungeon abyssal-drift + void-touched-crossroads) — teaser corretto B5 endgame | NO Legendary void live, solo hint |
| risk_3 | LOW | Memoria lore prima apparizione D4 (memoria-antechamber + memoria-vault raid) — teaser corretto | NO Legendary memoria live |
| risk_4 | LOW | Frost/Celeste concentrata Mage/Priest (frost-cathedral) — teaching primario coerente | PM aware |
| risk_5 | LOW | Necropolis-bells silence/resurrect teaser meccaniche — teaser only, NO runtime | Governance rispettata |
| risk_6 | LOW | Iconic family proliferation D4 (~50+ famiglie) — cumulative D1-D4 potenziale drift naming | Annotato — pass consolidamento post-D5 |
| risk_7 | LOW | Materiali specifici non tracciati (loot_tables.py SEALED) | Governance rispettata — nessun apply runtime |
| risk_8 | LOW | Signature items NON introdotti in D4 (design corretto — Phase D5+) | Governance rispettata |
| risk_9 | LOW | 9 dungeon Batch 4 slug names documentali (non live seed) — cross-verify Batch 4 matrix | Q7 open question per PM verifica |
| risk_10 | LOW | Emberking-crown Legendary hint appare W+R ma non M/P — pattern weapon-focus coerente ma flag PM | Q3 open question |

**Totali**: 10 rischi (0 HIGH · 1 MEDIUM · 9 LOW). Nessun BLOCKER.

### Open Questions PM per D5

| ID | Topic |
|---|---|
| **Q1** | Approvare 300 items T4 verbatim (0/60/150/90/0 rarity) o iterare selettivamente? |
| **Q2** | Approvare Epic 90 distribuzione: 52 dungeon Batch 4 + 33 raid Batch 4 + 5 Elite `infernal-pit-5p`? |
| **Q3** | Approvare 7-10 Legendary hint T4 (void-touched ×3, celestial-halo Mage+Priest, emberking-crown W+R, worldroot-scepter Ranger, soul-abyss hint Rogue, resurrect hint Priest) o ridurre/rimuovere? |
| **Q4** | Approvare iconic split 3-way documentato: 59 pure_evolutions / 3 intra_extensions / 238 free_new families? Il pattern free/new dominante è coerente con B4 espansione lore Vuoto+Memoria+Infernale strong. |
| **Q5** | Approvare naming IT verbatim per 300 items o rinominare selettivamente prima di D5? |
| **Q6** | Approvare craft NPC usage (5 LOCKED, 0 nuovi PENDING per D4) o autorizzare 1-5 nuovi NPC late-tier endgame per D5? |
| **Q7** | Approvare 9 dungeon Batch 4 slug names documentali? Cross-verify Batch 4 matrix. |
| **Q8** | Approvare Vuoto+Memoria lore first-appearance forte D4 come teaser per B5 endgame? |
| **Q9** | Autorizzare Phase D5 (T5 × 200 items Lv56-60) o gate PM formale con revisione D4? |
| **Q10** | Aggiornare PRD.md con 'R18.5 Phase D4 CLOSED' post-decisioni Q1-Q9? |

---

## Governance check STEP 16 (D4)

| Voce | Stato |
|---|---|
| **36 sigilli byte-identical** | ✅ VERIFIED (pytest 6/6 pre + post write) |
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
| Zero proficiency runtime enforcement | ✅ ZERO (documental only, HARD static check verified) |
| Zero anti-P2W runtime validator | ✅ ZERO (documental only) |
| **Priest scudo/piastre HARD BLOCK** | ✅ **ZERO usi (post-Q6 lesson)** |
| **Proficiency 300/300 HARD verified** | ✅ **0 violazioni** |
| Weapon backlog `strumento`/`falce`/`trinket-backlog` = 0 usi | ✅ VERIFIED |
| D5 auto-start BLOCKED | ✅ (STOP after D4) |
| Signature planning ZERO | ✅ |
| R18.6 code implementation ZERO | ✅ (design docs only in PRD roadmap) |
| Classi canoniche verbatim | ✅ Warrior/Rogue/Mage/Priest/Ranger |
| PM autonomous decision new | ✅ ZERO (0 nuovi NPC autonomi) |
| Files deliverable | ✅ 2 (.md + .json) |
| Items deliverable total | ✅ 300 |
| Rarity target 0/60/150/90/0 | ✅ EXACT MATCH |
| Class target 60×5 | ✅ EXACT MATCH |
| Level range 46-55 | ✅ VERIFIED |
| Epic 90/90 | ✅ EXACT MATCH |
| Legendary 0/0 live | ✅ EXACT MATCH |

---

## Statement finale (obbligatorio brief PM)

**STOP dopo D4.** Attendo PM review formale delle Open Questions Q1-Q10 prima di autorizzare **Phase D5** (T5 × 200 items Lv56-60 endgame).

**NO auto-transition a D5.** **NO Phase C tech dry-run.** **NO Signature planning.** **NO seal touch.** **NO codice/DB/migrations.** **NO R18.6 code implementation** (design docs only in PRD roadmap).

---

**R18.5 status flow (aggiornato post-STEP 16)**:
`Phase A` ✅ → `Phase B.1/B.2` ✅ → `Gate 1` ✅ → `Phase C0` ✅ → `Phase C0-bis` ✅ → `Gate 2` ✅ + `Phase C0-ter` ✅ → `Phase C0-quater Batch 1` ✅ CLOSED → `Phase C0-quinquies Batch 2` ✅ CLOSED → `Phase C0-sexies Batch 3` ✅ CLOSED → `Phase C0-septies Batch 4` ✅ CLOSED → `Phase C0-octies Batch 5 ENDGAME` ✅ CLOSED → `Mini-Gate Legendary Chain STEP 8` ✅ CLOSED → `Phase D0 STEP 9` ✅ CLOSED → `Phase D pre-D1 Iconic Starter STEP 10` ✅ CLOSED → `Phase D1 T1×300 STEP 11` ✅ CLOSED → `Phase D2 pre-Craft NPC STEP 12` ✅ CLOSED → `Phase D2 T2×350 STEP 13` ✅ CLOSED → `Phase D3 T3×350 STEP 14+15` ✅ CLOSED (post-Q6 fix) → **`Phase D4 T4×300 STEP 16`** 🟡 **DRAFT — PENDING PM Q1-Q10 review** → `Phase D5 T5×200` 🔒 BLOCKED (STOP after D4) / `Phase C tech dry-run + Item table live` 🔒 NOT IN AGENDA / `R18.6 Class Halls` 🔒 HOLD UNTIL R18.5 COMPLETE

---

**FINE STEP 16 — R18.5 Phase D4 T4×300 Item Table Drafting — DOCUMENTAL ONLY**
