# R18.5 Phase C0-quinquies — Batch 2 Matrix (Lv16-30) — DOCUMENTAL ONLY

- **Round**: `R18.5 — Itemization, ILVL & Gear Progression Rework`
- **Fase**: **C0-quinquies — Batch 2 (Lv16-30) Normal Track + Raid introduttivi**
- **Locked at UTC**: `2026-07-06T21:40:00Z`
- **Governance**: **DOCUMENTAL ONLY** — 36 sigilli byte-identical, zero DB writes, zero code changes.
- **Autorità**: PM Orchestrator (Batch 1 CLOSED + Phase C0-quinquies autorizzata)
- **Status**: 🟡 **BATCH 2 DRAFT / PENDING PM approval**
- **Predecessori autoritativi**:
  - `r18_5_phase_b_gate1_pm_decisions.md/.json` (17 lore sources Gate 1)
  - `r18_5_gate2_pm_decisions.md/.json` (Gate 2)
  - `r18_5_phase_c0ter_live_class_matrix.md/.json` (5 classi live)
  - `r18_5_phase_c0quater_live_dungeon_audit.md/.json` (audit 24 dungeon + 3 raid)
  - `r18_5_phase_c0quater_batch1_informed_final.md/.json` (Batch 1 CLOSED)
- **Lore pool disponibile**: **22 fonti** (17 Gate 1 + 5 nuove standalone: Memoria, Mare, Draco, Celeste, Infernale)

---

## 0. Executive summary + aritmetica gap Batch 2

### 🔎 Query DB read-only — dungeon 3p LIVE non allocati Batch 1

Confermato via `db.dungeons.find({is_active: True, is_5p: False, slug: {$nin: batch1_slugs + training-yard}})`:

| Slug | Nome IT (LIVE) | req_lvl | lore_theme | content_family | Note |
|---|---|:---:|:---:|:---:|---|
| `dragons-hoard` | Tesoro del Drago | 6 | draco | arcane | LIVE, PM #4 → Batch 2 head |
| `storm-spire` | Guglia della Tempesta | 6 | ambash | arcane | LIVE, PM #4 → Batch 2 head |

**Gap analysis**:
- 2 LIVE 3p disponibili (`dragons-hoard`, `storm-spire`)
- Target Batch 2: **14 dungeon 3p** → **12 NUOVI 3p da progettare**
- 2 raid nuovi Lv20-30 (i 3 live sono B3/B4/B5 già lockati)

### 🎯 Distribuzione livelli Batch 2

| Bracket interno | Range | Dungeon | Raid |
|:---:|:---:|:---:|:---:|
| Early | Lv16-19 | 4 (2 LIVE + 2 NEW) | — |
| Mid | Lv20-25 | 5 (NEW) | 1 (Lv22-25) |
| Late | Lv26-30 | 5 (NEW) | 1 (Lv28-30) |
| **TOTAL** | **Lv16-30** | **14** | **2** |

---

## 1. 14 dungeon Lv16-30 — lista completa

| # | Slug | Nome IT | Lv range | Status | Lore | Teaching primario |
|:---:|---|---|:---:|:---:|:---:|---|
| 1 | `dragons-hoard` | Tesoro del Drago | Lv16 | 🟢 LIVE | Draco | Warrior/Rogue mid (draconic reveal) |
| 2 | `storm-spire` | Guglia della Tempesta | Lv17 | 🟢 LIVE | Ambash | Mage/Ranger arcane storm |
| 3 | `blackpine-thicket` | Boschetto del Pino Nero | Lv17-19 | 🟡 NEW | Greatwood/Elfwood | Ranger primary + Warrior tank intro |
| 4 | `ironhold-keep` | Forte di Ferro | Lv18-19 | 🟡 NEW | Krastlov | **Tank+Healer synergy** (Warrior+Priest) |
| 5 | `worldroot-hollow` | Cavità delle Radici del Mondo | Lv20-22 | 🟡 NEW | Alberi della Vita | All-class + first Rare guaranteed |
| 6 | `veiled-forge` | Fucina Velata | Lv21-23 | 🟡 NEW | Ambash (sub-tag fucina) | Warrior+Rogue crafting reveal |
| 7 | `tidebound-cove` | Insenatura della Marea Vincolata | Lv22-24 | 🟡 NEW | Mare | **Rogue+Ranger** naval mobility |
| 8 | `hollow-monastery` | Monastero Cavo | Lv23-25 | 🟡 NEW | Memoria | **Healer+DPS synergy** (Priest+Mage) |
| 9 | `wild-hunt-lair` | Tana della Caccia Selvaggia | Lv24-25 | 🟡 NEW | Soe | Ranger primary + all-class hunt |
| 10 | `frostbound-vault` | Cripta Legata al Gelo | Lv26-27 | 🟡 NEW | Halodi + Krastlov | Warrior+Priest cold resistance |
| 11 | `sunken-shipyard` | Cantiere Sommerso | Lv27-28 | 🟡 NEW | Velur + Mare | Rogue+Ranger late naval |
| 12 | `emberlord-hideout` | Nascondiglio del Signore delle Braci | Lv28-29 | 🟡 NEW | Aveol | Bandit signature (successor bandit-warlord B1) |
| 13 | `stormcaller-vault` | Cripta dell'Evocatempesta | Lv28-30 | 🟡 NEW | Draco | Mage Draco advanced |
| 14 | `bonefall-crypt` | Cripta della Caduta d'Ossa | Lv29-30 | 🟡 NEW | Krastlov | Priest+Warrior transition B3 + primo Epic |

**Note simboli**:
- Ogni campo player-facing (Nome IT, tema, boss, materiali specifici, level range esatto) è flaggato `PENDING PM approval` per i NEW DRAFT
- Live dungeon (#1, #2) mantengono `name_it` DB validato

---

## 2. Distinzione live vs new

### 2.1 🟢 2 dungeon LIVE (già in DB, drift required_level accettato PM #4)

| # | Slug | req_lvl LIVE | Batch 2 documental range | Drift |
|:---:|---|:---:|:---:|:---:|
| 1 | `dragons-hoard` | 6 | Lv16 | ✅ Known drift, no rewrite (PM #4) |
| 2 | `storm-spire` | 6 | Lv17 | ✅ Known drift, no rewrite (PM #4) |

### 2.2 🟡 12 dungeon NEW DRAFT (design proposto, NO creation live in questa fase)

Distribuzione per bracket interno:
- Early Lv17-19: `blackpine-thicket`, `ironhold-keep` (2)
- Mid Lv20-25: `worldroot-hollow`, `veiled-forge`, `tidebound-cove`, `hollow-monastery`, `wild-hunt-lair` (5)
- Late Lv26-30: `frostbound-vault`, `sunken-shipyard`, `emberlord-hideout`, `stormcaller-vault`, `bonefall-crypt` (5)

---

## 3. Inclusione motivata di `dragons-hoard` + `storm-spire` come Batch 2 head

**Decisione PM #4 verbatim (Batch 1 CLOSED)**: spostati a Batch 2 head, NON Batch 1 tail.

### 3.1 `dragons-hoard` — Batch 2 slot #1 (Lv16)

- **Nome IT LIVE**: "Tesoro del Drago"
- **Lore live**: `draco` (nuova fonte standalone Gate 1+5 expansion)
- **Motivazione**: tono narrativo "il drago dorme, le monete contano i suoi sogni" è reveal mid-game — Batch 2 head naturale
- **Teaching**: Warrior primary (spada/ascia T2), Rogue secondary (pugnale T2), primo drop draconico
- **Loot target**: T2 prevalente + primo hint materiale draconico T3 minor

### 3.2 `storm-spire` — Batch 2 slot #2 (Lv17)

- **Nome IT LIVE**: "Guglia della Tempesta"
- **Lore live**: `ambash` (Gate 1)
- **Motivazione**: tono narrativo "il fulmine sale, non scende" è reveal arcano mid-game — Batch 2 head naturale
- **Teaching**: Mage primary (bastone/focus T2), Ranger secondary (arco T2), arcane storm resistance
- **Loot target**: T2 prevalente + primo hint materiale arcane T3 minor

### 3.3 Governance drift documentato

Entrambi hanno `required_level=6` LIVE nel DB. Batch 2 documental range è Lv16-17. **Drift design-vs-runtime accettato PM #4 verbatim, NO rewrite runtime**. Se in Phase C tech futura PM autorizza riallineamento, sarà gate dedicato.

---

## 4. 2 raid introduttivi Lv20-30

### 4.1 Raid #1 — `krastlov-siege` (Lv22-25, proposta)

- **Slug proposta**: `krastlov-siege` (`PENDING PM approval`)
- **Nome IT proposta**: "Assedio delle Torri Gemelle di Krastlov" (`PENDING PM`)
- **Party size**: **5-player (5p) proposta** — coerente con Elite/Group Track policy PM #1 (raid = evento coordinato). `PENDING PM approval` — non decisa autonomamente.
- **Lore source**: **Krastlov** (fonte Gate 1 orfana in Batch 1 dungeon; Krastlov usato anche per 3 dungeon Batch 2)
- **Content family proposta**: `baseline` (militare/politico)
- **Tema narrativo proposta**: "Le Torri Gemelle di Krastlov cadono sotto un assedio invernale. Nessuno può ricordarne il nome del comandante — perché lui l'ha mangiato." (`PENDING PM`)
- **Enemy family proposta**: Guerrieri veterani + sciamano gelo + comandante-lich minore (`PENDING PM`, NO Cleric drift)
- **Meccanica principale**: Team composition espansa (5p) — Tank + Healer + 2 DPS + Utility. Prime meccaniche raid: interrupt casting, positioning cold zones, boss phase transitions.
- **Loot tier**: T2 assicurato + T3 introduttivo su boss + primo Epic guaranteed su boss finale
- **Rarity range**: Common/Uncommon/Rare regolari, Epic guaranteed boss finale
- **Materiali proposta**: Acciaio invernale, gemma di comando, filo consacrato di Krastlov (`PENDING PM`)
- **Boss proposta**: "Comandante Senza Memoria" (lich minore raid boss, `PENDING PM`)
- **Itemization notes**: Loot Tank/Healer-friendly primario (piastre T2-T3 minor, reliquia T2, martello T2). DPS accessories T2. NO Legendary. Introduce ranking dedicato raid.

### 4.2 Raid #2 — `bloodgrove-uprising` (Lv28-30, proposta)

- **Slug proposta**: `bloodgrove-uprising` (`PENDING PM approval`)
- **Nome IT proposta**: "Rivolta del Bosco Sanguigno" (`PENDING PM`)
- **Party size**: **5-player (5p) proposta** — stesso rationale raid #1. `PENDING PM approval`.
- **Lore source**: **Alberi della Vita** + **Greatwood/Elfwood** (entrambe orfane in live, priorità Batch 2)
- **Content family proposta**: `nature` (druidico/silvano)
- **Tema narrativo proposta**: "Il Bosco Sanguigno si è ribellato. Le linfe che nutrivano gli Alberi della Vita ora nutrono altro." (`PENDING PM`)
- **Enemy family proposta**: Druidi caduti + treants ancestrali + spirito-radice corrotto (`PENDING PM`)
- **Meccanica principale**: Team 5p con **ruoli espliciti** — Tank aggro-swap, Healer AoE recovery, DPS burst phase, Utility crowd-control. Multi-role synergy hard test.
- **Loot tier**: T2 + T3 assicurato + Epic guaranteed boss finale (+ rare hint di materiale Legendary crafting, NO Legendary item drop diretto)
- **Rarity range**: Common/Uncommon/Rare regolari, Epic guaranteed boss finale
- **Materiali proposta**: Linfa consacrata, corteccia ancestrale, semi del Bosco Sanguigno, filo verde (`PENDING PM`)
- **Boss proposta**: "Il Cuore Corrotto degli Alberi della Vita" (spirito-radice, `PENDING PM`)
- **Itemization notes**: Loot multi-role (accessori dedicati per Tank/Healer/DPS T2-T3). Introduce concetto "gear check pre-raid" (min ILVL suggerito Lv27+, non enforced runtime).

### 4.3 Governance raid Batch 2

- **`required_level`**: NON popolato (coerente con i 3 raid live che hanno anche `required_level=null`). Lv range documentale solo.
- **Team composition espansa**: Tank + Healer + 2 DPS + Utility (5p) — proposta orch, `PENDING PM final`.
- **Ranking dedicato**: nota per future gate PM (leaderboard raid per completion time, min ILVL, world first).
- **Party size raid — PENDING PM**: 5p è preferenza Emergent (allineato con Elite Track 5p live), MA `PENDING PM approval` — non decisa autonomamente per non violare governance policy Party Size (PM #1 dice "variabile" ma non specifica raid).

---

## 5. Lore source per ogni dungeon + raid Batch 2 (`PENDING PM` sui NEW)

### 5.1 Distribuzione lore Batch 2 (11 fonti su 22 usate)

| Fonte | Dungeon Batch 2 | Raid Batch 2 | Total usi |
|:---:|---|:---:|:---:|
| **Draco** (nuova standalone) | dragons-hoard, stormcaller-vault | — | 2 |
| **Ambash** | storm-spire, veiled-forge (sub-tag fucina) | — | 2 |
| **Greatwood/Elfwood** | blackpine-thicket | bloodgrove-uprising (co-source) | 1.5 |
| **Krastlov** | ironhold-keep, frostbound-vault (co-source), bonefall-crypt | krastlov-siege | 3.5 |
| **Alberi della Vita** | worldroot-hollow | bloodgrove-uprising (co-source) | 1.5 |
| **Mare** (nuova standalone) | tidebound-cove, sunken-shipyard (co-source) | — | 1.5 |
| **Memoria** (nuova standalone) | hollow-monastery | — | 1 |
| **Soe** | wild-hunt-lair | — | 1 |
| **Halodi** | frostbound-vault (co-source) | — | 0.5 |
| **Velur** | sunken-shipyard (co-source) | — | 0.5 |
| **Aveol** | emberlord-hideout | — | 1 |

**Copertura Batch 2**: 11 fonti distinct (50% del pool 22).

### 5.2 Priorità fonti orfane in Batch 1 → coperte in Batch 2

Fonti che in Batch 1 non avevano dungeon dedicato ora coperte in Batch 2:
- ✅ **Krastlov** — 3+ usi Batch 2 (ironhold-keep, frostbound-vault, bonefall-crypt, raid krastlov-siege)
- ✅ **Greatwood/Elfwood** — 1.5 usi (blackpine-thicket + raid bloodgrove-uprising)
- ✅ **Alberi della Vita** — 1.5 usi (worldroot-hollow + raid bloodgrove-uprising)
- ✅ **Mare** — 1.5 usi (tidebound-cove + sunken-shipyard)

### 5.3 Fonti riservate a Batch futuri (non usate Batch 2)

- **Alevora** — world boss endgame, Batch 5
- **Ergolat** — raid B3 live (broken-bastion-siege)
- **Adalan** — usata Batch 1 (2 slot), non riusata Batch 2 per bilanciamento
- **Efreto** — usata Batch 1 (cursed-mines), non riusata Batch 2 per bilanciamento
- **Faglie arcane** — riservata Batch 3+ (metafisica mid-late)
- **Vuoto** — usata Elite Track B5 (voidspire-5p), non usata Batch 2
- **Luna Morta** — riservata Batch 5 endgame
- **Ciclo delle anime** — riservata Batch 5 endgame
- **Irthe** — usata Batch 1 (shadow-crypts, lich-sanctum) + raid B4 (necropolis-bells), non riusata Batch 2 per bilanciamento
- **Celeste** (nuova standalone) — riservata Elite B5 (celestial-citadel-5p)
- **Infernale** (nuova standalone) — riservata Elite B2/B4 (obsidian-arena-5p, infernal-pit-5p)

---

## 6. Bracket + level range + party size

Tutti i **14 dungeon Batch 2** hanno:
- **Bracket verbatim**: `Lv16-30 / Mid-Early Game`
- **Party size**: **3** (Normal Track, PM #1 verbatim, NO 5p)

I **2 raid** hanno:
- **Bracket verbatim**: `Lv20-30 Raid Intro`
- **Party size proposta**: **5** — `PENDING PM approval`

### 6.1 Distribuzione level range dettagliata

| Slot | Slug | Lv range | Party size |
|:---:|---|:---:|:---:|
| 1 | `dragons-hoard` (LIVE) | Lv16 | 3 |
| 2 | `storm-spire` (LIVE) | Lv17 | 3 |
| 3 | `blackpine-thicket` | Lv17-19 | 3 |
| 4 | `ironhold-keep` | Lv18-19 | 3 |
| 5 | `worldroot-hollow` | Lv20-22 | 3 |
| 6 | `veiled-forge` | Lv21-23 | 3 |
| 7 | `tidebound-cove` | Lv22-24 | 3 |
| 8 | `hollow-monastery` | Lv23-25 | 3 |
| 9 | `wild-hunt-lair` | Lv24-25 | 3 |
| 10 | `frostbound-vault` | Lv26-27 | 3 |
| 11 | `sunken-shipyard` | Lv27-28 | 3 |
| 12 | `emberlord-hideout` | Lv28-29 | 3 |
| 13 | `stormcaller-vault` | Lv28-30 | 3 |
| 14 | `bonefall-crypt` | Lv29-30 | 3 |
| Raid 1 | `krastlov-siege` | Lv22-25 | 5 (PENDING PM) |
| Raid 2 | `bloodgrove-uprising` | Lv28-30 | 5 (PENDING PM) |

---

## 7. Enemy family per ciascun dungeon/raid

| # | Slug | Enemy family proposta |
|:---:|---|---|
| 1 | `dragons-hoard` (LIVE) | draconic (già `enemy_families` LIVE `PENDING PM verify`) |
| 2 | `storm-spire` (LIVE) | storm_elementals (già LIVE) |
| 3 | `blackpine-thicket` | Bestie boschive avanzate (lupi-alpha, orsi ancestrali) `PENDING PM` |
| 4 | `ironhold-keep` | Guerrieri caduti + costrutti gelo (`PENDING PM`) |
| 5 | `worldroot-hollow` | Driadi anziane + spiriti-radice + treants giovani (`PENDING PM`) |
| 6 | `veiled-forge` | Costrutti artigiani + fabbri-fantasma (`PENDING PM`) |
| 7 | `tidebound-cove` | Pirati veterani + creature marine (`PENDING PM`) |
| 8 | `hollow-monastery` | Monaci-eco + spettri contemplativi (`PENDING PM`) |
| 9 | `wild-hunt-lair` | Cacciatori spettrali + bestie leggendarie minori (`PENDING PM`) |
| 10 | `frostbound-vault` | Non-morti gelidi + guardiani cripta (`PENDING PM`) |
| 11 | `sunken-shipyard` | Marinai-relitto + costrutti navali (`PENDING PM`) |
| 12 | `emberlord-hideout` | Briganti signori + sicari elite (`PENDING PM`) |
| 13 | `stormcaller-vault` | Draconici minori + evocatori arcani (NO Wizard drift) (`PENDING PM`) |
| 14 | `bonefall-crypt` | Non-morti veterani + necrofagi (`PENDING PM`, NO Cleric drift) |
| R1 | `krastlov-siege` | Guerrieri Krastlov + sciamano gelo + comandante-lich minore (`PENDING PM`) |
| R2 | `bloodgrove-uprising` | Druidi caduti + treants ancestrali + spirito-radice corrotto (`PENDING PM`) |

---

## 8. Meccanica principale + class proficiency teaching (multi-role synergy)

Enfasi Batch 2 = **espansione multi-role synergy**. Ogni dungeon insegna almeno 2 classi in party synergy:

| # | Slug | Multi-role teaching primario |
|:---:|---|---|
| 1 | `dragons-hoard` | Warrior+Rogue (melee synergy vs boss draconic) |
| 2 | `storm-spire` | Mage+Ranger (ranged synergy vs storm elementals) |
| 3 | `blackpine-thicket` | Ranger+Warrior (Ranger scout+DPS, Warrior tank intro) |
| 4 | `ironhold-keep` | **Tank+Healer synergy** (Warrior tank + Priest healer — dungeon dedicato) |
| 5 | `worldroot-hollow` | All-class + first Rare guaranteed (party build matters) |
| 6 | `veiled-forge` | Warrior+Rogue (Warrior aggro, Rogue burst DPS) |
| 7 | `tidebound-cove` | Rogue+Ranger (mobility + ranged, naval terrain) |
| 8 | `hollow-monastery` | **Healer+DPS synergy** (Priest heal + Mage burst — dungeon dedicato) |
| 9 | `wild-hunt-lair` | Ranger primary + all-class hunt teaching |
| 10 | `frostbound-vault` | Warrior+Priest (tank + healer, cold resistance mechanics) |
| 11 | `sunken-shipyard` | Rogue+Ranger (mobility late, naval boss phase) |
| 12 | `emberlord-hideout` | Warrior+Rogue (proficiency check narrativo continuazione B1) |
| 13 | `stormcaller-vault` | Mage primary + Ranger (arcane DPS + support) |
| 14 | `bonefall-crypt` | Priest+Warrior (heal + tank, transition B3, primo Epic) |
| R1 | `krastlov-siege` | **Tank+Healer+2 DPS+Utility** (5p full comp, raid meccaniche standard) |
| R2 | `bloodgrove-uprising` | **Tank+Healer+2 DPS+Utility** (5p multi-role hard test) |

---

## 9. Loot tier atteso — T2 prevalente + T3 introduttivo

### 9.1 Distribuzione tier Batch 2

| Tier | Presenza Batch 2 | Note |
|:---:|---|---|
| **T1** | Coda (accessori occasionali) | Sotto-tier residuo Batch 1 |
| **T2** | **Prevalente** ovunque | Core loot Batch 2 |
| **T3** | Introduttivo su boss mid+ (dungeon #5+, raid) | Progressione verso Batch 3 |
| **T4** | ❌ Non presente | Riservato Batch 3+ |
| **T5** | ❌ Non presente | Riservato Batch 4/5 |

### 9.2 Boss drop Epic — regola PM verbatim

- **Epic drop solo boss ultimo del bracket** (dungeon #14 `bonefall-crypt`) + boss finale raid #2 (`bloodgrove-uprising`)
- Nessun Legendary in Batch 2 (Legendary solo T5, riservato B5)
- Rare regolare boss (dungeon #5+ e entrambi raid)

### 9.3 Rispetto crosswalk 1500

Batch 2 pesca principalmente:
- **Riga T2** (350 item: 150 Common + 150 Uncommon + 50 Rare)
- Primi item **Riga T3** (350 item: 30 Common + 160 Uncommon + 130 Rare + 30 Epic)

**Stima Batch 2 utilizzo**: ~40-50% del pool T2 + ~15-20% del pool T3. Rimanente riservato Batch 3.

---

## 10. Rarity range attesa

| Rarity | Presenza Batch 2 | Note |
|:---:|---|---|
| **Common** | Regolare ovunque | Backbone Batch 2 |
| **Uncommon** | **Prevalente** ovunque | Core Batch 2 (vs Common prevalente Batch 1) |
| **Rare** | Regolare boss mid+ | Introduzione consistente |
| **Epic** | Solo boss #14 + boss finale raid #2 (max 2-3 slot Batch 2 totali, rate `PENDING PM`) | Molto limitato |
| **Legendary** | ❌ **Assente** | Governance verbatim (T5 only) |

---

## 11. Materiali principali (`PENDING PM approval` su nomi specifici)

| # | Slug | Materiali proposta |
|:---:|---|---|
| 1 | `dragons-hoard` (LIVE) | Squame draconiche, oro antico, gemme opache (`PENDING PM verify` loot_tables SEALED) |
| 2 | `storm-spire` (LIVE) | Cristallo tempesta, cera arcana, filo elettrico (`PENDING PM verify`) |
| 3 | `blackpine-thicket` | Corteccia nera, resina druidica, artigli ancestrali (`PENDING PM`) |
| 4 | `ironhold-keep` | Acciaio invernale, ferro rinforzato, filo di comando (`PENDING PM`) |
| 5 | `worldroot-hollow` | Linfa antica T2-T3, radici ancestrali, semi silvani (`PENDING PM`) |
| 6 | `veiled-forge` | Metallo velato, essenza fabbrile, gemme rifinite T2-T3 (`PENDING PM`) |
| 7 | `tidebound-cove` | Cristallo marino, corallo grezzo T2, corda salata (`PENDING PM`) |
| 8 | `hollow-monastery` | Cera monastica, pergamena eco, cristallo memoria T2-T3 (`PENDING PM`) |
| 9 | `wild-hunt-lair` | Pelli veterane, ossa di bestia leggendaria minore, artigli T2 (`PENDING PM`) |
| 10 | `frostbound-vault` | Ghiaccio persistente T2-T3, filo consacrato invernale, ossa gelate (`PENDING PM`) |
| 11 | `sunken-shipyard` | Legno relitto, chiodi salati, gemme marine T2-T3 (`PENDING PM`) |
| 12 | `emberlord-hideout` | Acciaio elite, cuoio signore, gemme brace (`PENDING PM`) |
| 13 | `stormcaller-vault` | Cristallo tempesta T3, essenza draconica minore, filo elettrico avanzato (`PENDING PM`) |
| 14 | `bonefall-crypt` | Ossa consacrate T3, filo di controllo, gemma di anima minore (`PENDING PM`) |
| R1 | `krastlov-siege` | Acciaio invernale T3, gemma di comando, filo consacrato Krastlov, essenza-lich (`PENDING PM`) |
| R2 | `bloodgrove-uprising` | Linfa consacrata T3, corteccia ancestrale, semi Bosco Sanguigno, filo verde, materiale Legendary crafting hint (`PENDING PM`) |

---

## 12. Boss/miniboss proposte (`PENDING PM approval`)

| # | Slug | Boss/miniboss proposta |
|:---:|---|---|
| 1 | `dragons-hoard` (LIVE) | Custode Draconico (mini) + Drago di Rame Anziano (boss) (`PENDING PM verify`) |
| 2 | `storm-spire` (LIVE) | Elementale Tempesta Anziano + Signore-Fulmine (`PENDING PM verify`) |
| 3 | `blackpine-thicket` | Lupo-Alpha Ancestrale + Orso Anziano di Elfwood (`PENDING PM`) |
| 4 | `ironhold-keep` | Capitano-Comandante Caduto + Costrutto Assedio (`PENDING PM`) |
| 5 | `worldroot-hollow` | Driade Anziana + Radice-Cuore Antica (`PENDING PM`) |
| 6 | `veiled-forge` | Mastro-Fabbro Velato + Costrutto Padre (`PENDING PM`) |
| 7 | `tidebound-cove` | Ammiraglio Corsaro + Kraken Minore (`PENDING PM`) |
| 8 | `hollow-monastery` | Abate-Eco + Spettro-Meditante (`PENDING PM`) |
| 9 | `wild-hunt-lair` | Grande Cacciatore Spettrale + Grifone Ancestrale (`PENDING PM`) |
| 10 | `frostbound-vault` | Guardiano-Lich Minore + Elementale Cripta (`PENDING PM`) |
| 11 | `sunken-shipyard` | Ingegnere-Relitto + Kraken Costruttivo (`PENDING PM`) |
| 12 | `emberlord-hideout` | Il Signore delle Braci (successor Signore dei Briganti B1) + Guardaspalle Elite (`PENDING PM`) |
| 13 | `stormcaller-vault` | Evocatempesta Anziano (NON Wizard) + Draconico Minore (`PENDING PM`) |
| 14 | `bonefall-crypt` | Necrofago Anziano + Comandante-Ossa (boss transition B3, `PENDING PM`) |
| R1 | `krastlov-siege` | Comandante Senza Memoria (lich minore raid boss) + 2 fase (`PENDING PM`) |
| R2 | `bloodgrove-uprising` | Il Cuore Corrotto degli Alberi della Vita (spirito-radice) + 3 fase (`PENDING PM`) |

---

## 13. Itemization notes — coerenza proficiency (Gate 2 hard-block preservation)

Ogni dungeon Batch 2 rispetta coerenza **proficiency armor/weapon** (Gate 2 sez. 5-6). Loot design coerente con class matrix C0-ter:

| # | Slug | Loot proficiency-coherent |
|:---:|---|---|
| 1 | `dragons-hoard` | Warrior spade/asce T2, Rogue pugnali T2, universal accessori. NO stoffa/reliquia/tomo. |
| 2 | `storm-spire` | Mage bastoni/focus T2, stoffa T2. Ranger arco/pugnale T2, cuoio T2. Universal accessori. |
| 3 | `blackpine-thicket` | Ranger arco/pugnale/lancia T2, cuoio T2. Warrior spada T2, maglia T2. Universal. |
| 4 | `ironhold-keep` | Warrior maglia/piastre T2, spada/martello T2, scudo T2. Priest reliquia T2, stoffa T2, martello T2. |
| 5 | `worldroot-hollow` | Universal prevalente T2-T3 (accessori multi-class). All-class weapons T2. Primo Rare guaranteed. |
| 6 | `veiled-forge` | Warrior armi da forgia T2 (spada/ascia/martello), maglia T2. Rogue pugnale T2, cuoio T2. |
| 7 | `tidebound-cove` | Rogue pugnale/balestra T2, cuoio T2. Ranger arco/balestra T2, cuoio+maglia T2. |
| 8 | `hollow-monastery` | Priest reliquia/focus T2, stoffa T2, martello T2. Mage bastone/tomo/focus T2, stoffa T2. |
| 9 | `wild-hunt-lair` | Ranger arco/pugnale/lancia T2-T3 minor, cuoio+maglia T2. Universal accessori. |
| 10 | `frostbound-vault` | Warrior spada/martello T2-T3 minor, maglia T2-T3 minor. Priest reliquia T2, stoffa T2-T3 minor. |
| 11 | `sunken-shipyard` | Rogue pugnale/balestra T2-T3 minor, cuoio T2-T3. Ranger arco/balestra T2-T3. |
| 12 | `emberlord-hideout` | Warrior spada/ascia T2-T3, maglia T2-T3. Rogue pugnale T2-T3. Signature "signore" items (`PENDING PM`). |
| 13 | `stormcaller-vault` | Mage bastone/focus/tomo T2-T3, stoffa T2-T3. NO Wizard drift naming. |
| 14 | `bonefall-crypt` | Priest reliquia/focus/martello T3, stoffa T3. Warrior maglia/piastre T3, spada T3. **Primo Epic Batch 2** (max 1-2 slot). |
| R1 | `krastlov-siege` | Tank+Healer primary loot (Warrior piastre T3, Priest reliquia T3). DPS T2-T3. **Epic guaranteed boss finale**. |
| R2 | `bloodgrove-uprising` | Multi-role T3 (accessori dedicati Tank/Healer/DPS). **Epic guaranteed boss finale** + rare hint materiale Legendary crafting (no Legendary drop diretto). |

**Governance proficiency**: NESSUN dungeon Batch 2 drop item universale con "wrong armor" per una classe (es. Mage NON riceve piastre T2 T3). Rispetto verbatim Gate 2 sez. 5-6 senza runtime enforcement (Phase C tech BLOCCATA).

---

## 14. Achievement / ranking notes futuri

Ogni dungeon Batch 2 ha spunto achievement + ranking (`PENDING PM`):

| # | Slug | Achievement hint |
|:---:|---|---|
| 1 | `dragons-hoard` | "Prima Squama" (drop first draconic material) |
| 2 | `storm-spire` | "Fulmine Sale" (clear con Mage nel party) |
| 3 | `blackpine-thicket` | "Caccia Silente" (clear senza alert) |
| 4 | `ironhold-keep` | "Tank+Healer First" (clear con Warrior+Priest party) |
| 5 | `worldroot-hollow` | "Primo Rare Batch 2" (unlock su primo Rare guaranteed) |
| 6 | `veiled-forge` | "Fabbro Rivelato" (interact all forge nodes) |
| 7 | `tidebound-cove` | "Marea Cavalcata" (clear rapido sotto X sec) |
| 8 | `hollow-monastery` | "Eco Ascoltata" (clear con Priest+Mage party) |
| 9 | `wild-hunt-lair` | "Grande Cacciatore" (kill mini-boss senza morire) |
| 10 | `frostbound-vault` | "Gelo Rotto" (clear con Priest purifier boss) |
| 11 | `sunken-shipyard` | "Relitto Riparato" (`PENDING PM`) |
| 12 | `emberlord-hideout` | "Signore delle Braci Deposto" |
| 13 | `stormcaller-vault` | "Evocatempesta Silenziato" |
| 14 | `bonefall-crypt` | "Primo Epic Batch 2" (unlock su primo Epic drop) |
| R1 | `krastlov-siege` | **Ranking dedicato raid** ("First Kill Krastlov-Siege" world/server first, min ILVL leaderboard) |
| R2 | `bloodgrove-uprising` | **Ranking dedicato raid** ("First Kill Bloodgrove" world/server first, min ILVL) |

---

## 15. Rischi Batch 2

| # | Rischio | Severità | Origine | Mitigation |
|:---:|---|:---:|---|---|
| 1 | **12 nuovi dungeon design** (creation live richiede gate futuro + Phase C tech BLOCCATA) | 🟡 MEDIUM | Gap 3p live LIVE = 2 di 14 target | Documentato Batch 2 = DRAFT. Creation live deferita a gate PM successivo. |
| 2 | **2 nuovi raid design** — party size raid `PENDING PM approval` | 🟡 MEDIUM | PM #1 non specifica raid party size | Preferenza 5p documentata, `PENDING PM final`. |
| 3 | **Drift `required_level` LIVE dragons-hoard/storm-spire** (Lv6 vs Batch 2 head Lv16-17 documentale) | 🟢 LOW | Legacy scaling pre-R18.5 | Documentato PM #4 verbatim, NO rewrite. |
| 4 | **Naming IT player-facing** dei 12 nuovi + 2 raid — tutti `PENDING PM` | 🟢 LOW | Design proposta Emergent | PM approva/rinomina in gate futuro. |
| 5 | **Materiali specifici** — nomi `PENDING PM verify` | 🟢 LOW | Design proposta Emergent | Coerenza con loot_tables.py SEALED. |
| 6 | **Compatibility policy runtime per proficiency** (Gate 2 sez. 5-6) | 🟡 MEDIUM | Out-of-scope Batch 2 | Enforcement Phase C tech (BLOCCATA). |
| 7 | **Sovrapposizione lore Batch 1↔Batch 2** (Aveol, Draco, Memoria, Ambash usate in entrambe) | 🟢 LOW | Design bilanciamento | Differenziazione narrativa esplicita (chapel B1 vs emberlord B2, ecc.). Info-only. |
| 8 | **Krastlov utilizzato 3.5 volte in Batch 2** (concentrazione alta) | 🟡 MEDIUM | Priorità recupero fonte orfana Batch 1 | `PENDING PM`: accettare concentrazione o ridistribuire (impact medio). |
| 9 | **Nessuna fonte "endgame reveal" Batch 2** (Vuoto/Luna Morta/Ciclo delle anime/Alevora tutte riservate B4/B5) | 🟢 LOW | Design intenzionale | Info-only, nessuna azione. |
| 10 | **Boss `dragons-hoard` + `storm-spire` LIVE** — `PENDING PM verify` da loot_tables.py SEALED | 🟢 LOW | Read-only pending | Non blocker Batch 2 design. Verifica in gate PM successivo. |
| 11 | **Emergent NON verificato drop rates numerici Batch 2** (target direzionale solo, no rate specifici) | 🟢 LOW | Regola PM verbatim ("no rate finali B2") | Aligned con Batch 1 governance. |

---

## 16. Open Questions PM residue

### 16.1 Party size raid

- **Q1 (BATCH 2 KEY)**: Raid party size = **5-player** (preferenza Emergent) o **3-player** coerente con Normal Track? O bracket dedicato raid (es. 5-player fisso)?

### 16.2 Naming IT player-facing (14 dungeon + 2 raid = 16 nomi)

- **Q2**: Nome IT proposta per i 12 nuovi dungeon — approve verbatim o rinomina selettiva?
- **Q3**: Nome IT proposta per i 2 raid — approve verbatim o rinomina?
- **Q4**: `stormcaller-vault` — accettabile "Cripta dell'Evocatempesta" o rischia drift Wizard? (Emergent ha usato "Evocatempesta" per evitare "Stregone/Wizard")

### 16.3 Slug PM-lock

- **Q5**: Slug proposta per i 14 dungeon + 2 raid confermati per PM-lock (equivalente a Batch 1 slug policy)?

### 16.4 Bracket dungeon vs raid

- **Q6**: Bracket dungeon "Lv16-30 / Mid-Early Game" naming ufficiale confermato?
- **Q7**: Bracket raid "Lv20-30 Raid Intro" naming ufficiale?

### 16.5 Loot rate direzionali

- **Q8**: Epic drop rate su `bonefall-crypt` + raid #2 boss finale — direzionale accettabile o servono rate numerici specifici in Batch 2?

### 16.6 Concentrazione lore

- **Q9**: Krastlov usata 3.5 volte Batch 2 (concentrazione alta per priorità recupero orfana) — accettabile o ridistribuire?

### 16.7 Post-approval workflow

- **Q10**: Post-decisions Q1-Q9, aggiornare PRD.md con sezione "R18.5 Phase C0-quinquies Batch 2 CLOSED"?
- **Q11**: Autorizzare **Phase C0-sexies Batch 3** (Lv31-45) o pausa?
- **Q12**: `broken-bastion-siege` (raid live B3 lockato in Batch 1 CLOSED) — includere in Batch 3 design come "raid live head" (analogo dragons-hoard/storm-spire in Batch 2) o gestione separata?

---

## 17. Governance check finale Batch 2

- ✅ **14 dungeon Batch 2 esatti** (2 LIVE + 12 NEW DRAFT)
- ✅ **2 raid Batch 2 esatti** (entrambi NEW DRAFT)
- ✅ **16 sezioni obbligatorie** compilate
- ✅ **Distinzione live/new** chiara (sez. 2)
- ✅ **`dragons-hoard` + `storm-spire`** inclusi Batch 2 head con motivazione (sez. 3, PM #4 verbatim)
- ✅ **2 raid introduttivi Lv20-30** proposte motivate (sez. 4)
- ✅ **11 lore sources usate** su 22 disponibili — priorità orfane Batch 1 (Krastlov, Greatwood/Elfwood, Alberi della Vita) coperte (sez. 5)
- ✅ **Party size 3 per dungeon** verbatim, **`PENDING PM` per raid** (5p preferenza Emergent)
- ✅ **Teaching class multi-role synergy** (sez. 8)
- ✅ **Loot target T2 prevalente + T3 introduttivo**, NO Legendary, Epic solo boss ultimo (#14 + raid #2 finale) (sez. 9-10)
- ✅ **`PENDING PM approval`** su tutti i campi player-facing (nomi, temi, boss, materiali, level range, lore assignment sui NEW)
- ✅ **Naming canonical Mage/Priest** verbatim (NO drift Wizard/Cleric in `stormcaller-vault`, `bonefall-crypt`, ecc.)
- ✅ **Proficiency coherence** rispettata Gate 2 sez. 5-6 verbatim (sez. 13)
- ✅ **36 sigilli byte-identical** — nessuna modifica ai sealed files (attesa `pytest backend_r18_4_sealed_integrity_test.py` PASS)
- ✅ **Zero DB writes** — solo `find()` read-only per gap analysis 3p live
- ✅ **Zero code changes** (`.py` / `.js` / `.jsx` / `.tsx` intatti)
- ✅ **Zero migrations / apply scripts**
- ✅ **Zero dungeon/raid creation live** (12 nuovi dungeon + 2 raid = design docs)
- ✅ **Zero party_size rewrite** (dungeon 3p verbatim, raid `PENDING PM`)
- ✅ **Zero `required_level` rewrite** (drift live accettato as-is)
- ✅ **Zero `lore_meta.py` touch** (espansione fonti puramente documentale)
- ✅ **2 file deliverable creati** (`.md` + `.json`)

---

## 18. Handoff Batch 2

### 18.1 Deliverable prodotti

- ✅ `/app/memory/r18_5_phase_c0quinquies_batch2_lv16_30_matrix.md` (questo file)
- ✅ `/app/memory/r18_5_phase_c0quinquies_batch2_lv16_30_matrix.json` (mirror strutturato)

### 18.2 Prossimo step atteso

**PM Gate review Batch 2** → risposte alle 12 Open Questions (sez. 16) → chiusura formale Batch 2 con:
1. Aggiornamento PRD.md con sezione "R18.5 Phase C0-quinquies Batch 2 CLOSED"
2. Autorizzazione (o pausa) **Phase C0-sexies Batch 3** (Lv31-45) — includendo eventualmente `broken-bastion-siege` raid live B3 head come slot dedicato

**Batch 3-5 + Phase C tech dry-run**: 🔒 **BLOCCATI** fino a nuovo gate PM (governance sigilli `derive_ui_4state`/`item_public()` invariata).

---

**Batch 2 DRAFT CLOSED — pronto per PM final review + risposta Open Questions**.
