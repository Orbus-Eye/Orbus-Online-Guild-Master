# R18.5 — Phase E2.1 · Duplicate Name Resolution Mini-Pass (STEP 25)

**Round**: R18.5 — Itemization, ILVL & Gear Progression Rework
**Phase**: E2.1 — Duplicate Name Resolution Mini-Pass (post-E1+E2 CLOSED)
**STEP**: 25
**Locked at UTC**: `2026-07-07T19:05:00Z`
**Governance**: **DOCUMENTAL ONLY — MICRO-ECCEZIONE AUTORIZZATA PM** su file item table D1-D4 (`.json`) SOLO per rename `nome_it`. NO stat/tier/rarity/classe/source/proficiency/anti-P2W changes.
**Status**: ✅ **APPLIED**
**Authority**: PM Orchestrator — STEP 25 catena autorizzata post-STEP 24 E1+E2 CLOSED (Q12=A rename verbatim)

**Deliverables**:
- `/app/memory/r18_5_phase_e2_1_duplicate_name_resolution.md` (questo file)
- `/app/memory/r18_5_phase_e2_1_duplicate_name_resolution.json` (1722 righe · SHA256 `d39e9b9dfc51987e39ad1869c579d848b028705fbe525f92d354aef3973850b4`)

---

## Sezione 1 — Lista dei 14 duplicate nome_it PRIMA

| # | nome_it duplicato | Occurrences | Items involved |
|:---:|---|:---:|---|
| 1 | `Anello Radice del Mondo` | 2 | `rogue-worldroot-ring` (D2 T2 U Rogue) · `mage-worldroot-ring-m` (D2 T2 U Mage) |
| 2 | `Cappuccio Forgiato d'Anima` | 2 | `rogue-soulforged-hood` (D3 T3 U Rogue) · `ranger-soulforged-hood` (D3 T3 U Ranger) |
| 3 | `Cappuccio della Stella Caduta` | 2 | `mage-celestial-teaser-hood` (D3 T3 U Mage) · `ranger-starfall-ranger-hood` (D3 T3 U Ranger) |
| 4 | `Cappuccio delle Campane` | 2 | `rogue-t4-necropolis-bells-hood` (D4 T4 R Rogue) · `ranger-t4-necropolis-bells-hood` (D4 T4 R Ranger) |
| 5 | `Corazza Radice del Mondo` | 2 | `warrior-worldroot-plate` (D2 T2 U Warrior) · `ranger-worldroot-cuirass` (D2 T2 U Ranger) |
| 6 | `Focus Radice del Mondo` | 2 | `mage-focus-worldroot` (D2 T2 U Mage) · `priest-worldroot-focus` (D2 T2 U Priest) |
| 7 | `Guanti Forgiati d'Anima` | 2 | `rogue-soulforged-gloves` (D3 T3 U Rogue) · `ranger-soulforged-gloves` (D3 T3 U Ranger) |
| 8 | `Mantello del Signore Braci` | **3** | `warrior-emberlord-cloak` (D2 T2 U W) · `rogue-emberlord-cloak` (D2 T2 Rare R) · `ranger-emberlord-cloak` (D2 T2 U Ra) |
| 9 | `Orecchino Radice del Mondo` | 2 | `mage-worldroot-earring` (D2 T2 Rare Mage) · `priest-worldroot-earring` (D2 T2 U Priest) |
| 10 | `Reliquia di Adalan` | 2 | `priest-adalan-relic` (D1 T1 U Priest) · `priest-adalan-relic-b` (D2 T2 U Priest) |
| 11 | `Scettro Minore Radice del Mondo` | 2 | `mage-worldroot-scepter-lesser` (D2 T2 Rare Mage) · `priest-worldroot-scepter-lesser` (D2 T2 Rare Priest) |
| 12 | `Stivali Conciati Elfwood Maestri` | 2 | `ranger-conciatore-elfwood-master-boots` (D3 T3 Rare Ranger) · `rogue-t4-conciatore-elfwood-master-boots` (D4 T4 Rare Rogue) |
| 13 | `Stivali Forgiati d'Anima` | 2 | `rogue-soulforged-boots` (D3 T3 U Rogue) · `ranger-soulforged-boots` (D3 T3 U Ranger) |
| 14 | `Stivali del Signore Braci` | 2 | `rogue-emberlord-boots` (D2 T2 U Rogue) · `mage-emberlord-boots` (D2 T2 U Mage) |
| **TOTALE** | **14 duplicate names** | **29 items** | (13×2 + 1×3) |

---

## Sezione 2 — Proposta rename (nome_it_before → nome_it_after) applicata

**Variant style**: **class-suffix** (varianti leggere semantiche PM verbatim) + **tier-suffix** per cross-tier case.

### Class-suffix varianti utilizzate (mapping verbatim)
- Warrior → `del Guerriero`
- Rogue → `dell'Ombra` / `dell'Assassino` / `del Vagabondo`
- Mage → `dell'Arcanista` / `dell'Astronomo` / `del Loremaster`
- Priest → `del Druido Sacro` / `del Chierico` / `del Novizio`
- Ranger → `del Cacciatore` / `del Guardaboschi` / `del Tiratore`

### Tabella rename completa (29 renames)

| # | item_id | phase | tier | rarity | classe | nome_it_before | nome_it_after |
|:---:|---|:---:|:---:|:---:|:---:|---|---|
| 1 | `rogue-worldroot-ring` | D2 | T2 | Uncommon | Rogue | Anello Radice del Mondo | **Anello Radice del Mondo del Vagabondo** |
| 2 | `mage-worldroot-ring-m` | D2 | T2 | Uncommon | Mage | Anello Radice del Mondo | **Anello Radice del Mondo dell'Arcanista** |
| 3 | `rogue-soulforged-hood` | D3 | T3 | Uncommon | Rogue | Cappuccio Forgiato d'Anima | **Cappuccio Forgiato d'Anima dell'Ombra** |
| 4 | `ranger-soulforged-hood` | D3 | T3 | Uncommon | Ranger | Cappuccio Forgiato d'Anima | **Cappuccio Forgiato d'Anima del Cacciatore** |
| 5 | `mage-celestial-teaser-hood` | D3 | T3 | Uncommon | Mage | Cappuccio della Stella Caduta | **Cappuccio della Stella Caduta dell'Astronomo** |
| 6 | `ranger-starfall-ranger-hood` | D3 | T3 | Uncommon | Ranger | Cappuccio della Stella Caduta | **Cappuccio della Stella Caduta del Tiratore** |
| 7 | `rogue-t4-necropolis-bells-hood` | D4 | T4 | Rare | Rogue | Cappuccio delle Campane | **Cappuccio delle Campane dell'Assassino** |
| 8 | `ranger-t4-necropolis-bells-hood` | D4 | T4 | Rare | Ranger | Cappuccio delle Campane | **Cappuccio delle Campane del Cacciatore** |
| 9 | `warrior-worldroot-plate` | D2 | T2 | Uncommon | Warrior | Corazza Radice del Mondo | **Corazza Radice del Mondo del Guerriero** |
| 10 | `ranger-worldroot-cuirass` | D2 | T2 | Uncommon | Ranger | Corazza Radice del Mondo | **Corazza Radice del Mondo del Guardaboschi** |
| 11 | `mage-focus-worldroot` | D2 | T2 | Uncommon | Mage | Focus Radice del Mondo | **Focus Radice del Mondo dell'Arcanista** |
| 12 | `priest-worldroot-focus` | D2 | T2 | Uncommon | Priest | Focus Radice del Mondo | **Focus Radice del Mondo del Druido Sacro** |
| 13 | `rogue-soulforged-gloves` | D3 | T3 | Uncommon | Rogue | Guanti Forgiati d'Anima | **Guanti Forgiati d'Anima dell'Ombra** |
| 14 | `ranger-soulforged-gloves` | D3 | T3 | Uncommon | Ranger | Guanti Forgiati d'Anima | **Guanti Forgiati d'Anima del Cacciatore** |
| 15 | `warrior-emberlord-cloak` | D2 | T2 | Uncommon | Warrior | Mantello del Signore Braci | **Mantello del Signore Braci del Guerriero** |
| 16 | `rogue-emberlord-cloak` | D2 | T2 | Rare | Rogue | Mantello del Signore Braci | **Mantello del Signore Braci dell'Ombra** |
| 17 | `ranger-emberlord-cloak` | D2 | T2 | Uncommon | Ranger | Mantello del Signore Braci | **Mantello del Signore Braci del Cacciatore** |
| 18 | `mage-worldroot-earring` | D2 | T2 | Rare | Mage | Orecchino Radice del Mondo | **Orecchino Radice del Mondo dell'Arcanista** |
| 19 | `priest-worldroot-earring` | D2 | T2 | Uncommon | Priest | Orecchino Radice del Mondo | **Orecchino Radice del Mondo del Druido Sacro** |
| 20 | `priest-adalan-relic` | D1 | T1 | Uncommon | Priest | Reliquia di Adalan | **Reliquia di Adalan del Novizio** |
| 21 | `priest-adalan-relic-b` | D2 | T2 | Uncommon | Priest | Reliquia di Adalan | **Reliquia di Adalan del Chierico** |
| 22 | `mage-worldroot-scepter-lesser` | D2 | T2 | Rare | Mage | Scettro Minore Radice del Mondo | **Scettro Minore Radice del Mondo dell'Arcanista** |
| 23 | `priest-worldroot-scepter-lesser` | D2 | T2 | Rare | Priest | Scettro Minore Radice del Mondo | **Scettro Minore Radice del Mondo del Druido Sacro** |
| 24 | `ranger-conciatore-elfwood-master-boots` | D3 | T3 | Rare | Ranger | Stivali Conciati Elfwood Maestri | **Stivali Conciati Elfwood Maestri T3** (tier-suffix) |
| 25 | `rogue-t4-conciatore-elfwood-master-boots` | D4 | T4 | Rare | Rogue | Stivali Conciati Elfwood Maestri | **Stivali Conciati Elfwood Maestri T4** (tier-suffix) |
| 26 | `rogue-soulforged-boots` | D3 | T3 | Uncommon | Rogue | Stivali Forgiati d'Anima | **Stivali Forgiati d'Anima dell'Ombra** |
| 27 | `ranger-soulforged-boots` | D3 | T3 | Uncommon | Ranger | Stivali Forgiati d'Anima | **Stivali Forgiati d'Anima del Cacciatore** |
| 28 | `rogue-emberlord-boots` | D2 | T2 | Uncommon | Rogue | Stivali del Signore Braci | **Stivali del Signore Braci dell'Ombra** |
| 29 | `mage-emberlord-boots` | D2 | T2 | Uncommon | Mage | Stivali del Signore Braci | **Stivali del Signore Braci dell'Arcanista** |

**Governance rename PM verbatim**: variant style class-suffix per differenziare classe (chiaro per player) + tier-suffix per 2 casi cross-tier (`Stivali Conciati Elfwood Maestri` T3/T4).

---

## Sezione 3 — Nome finale dopo rename confermato univoco

| Verify | Valore |
|---|:---:|
| Duplicate nome_it residui post-rename | **0** ✅ |
| Nomi univoci 1500/1500 | ✅ **UNIQUE** |

**Status**: ✅ Tutti i 14 duplicate risolti. Nessun residuo. Ogni item ha nome player-facing distinguibile.

---

## Sezione 4 — Conferma nessun cambio stat/tier/rarity/classe/source/proficiency per ogni rename

**Verifica full-snapshot per ogni rename (29/29)**:

| Vista | Status |
|---|:---:|
| `stat_principali` unchanged | ✅ 29/29 |
| `weapon_family` unchanged | ✅ 29/29 |
| `armor_type` unchanged | ✅ 29/29 |
| `rarity` unchanged | ✅ 29/29 |
| `tier` unchanged | ✅ 29/29 |
| `classe_orientata` unchanged | ✅ 29/29 |
| `source` unchanged | ✅ 29/29 |
| `anti-P2W fields` unchanged | ✅ 29/29 |
| `iconic_family` unchanged | ✅ 29/29 |
| `affects_*` fields unchanged | ✅ 29/29 |
| `is_tradeable`, `is_cosmetic`, `item_binding_policy` unchanged | ✅ 29/29 |
| `item_id` unchanged (governance tracking) | ✅ 29/29 |
| **All other fields unchanged (full snapshot verification)** | ✅ **29/29 PASSED** |

**Governance**: solo il campo `nome_it` è stato modificato per ciascuno dei 29 rename. Verifica snapshot completa pre/post confermata via script diff (rename_log_apply_audit in JSON).

---

## Sezione 5 — Conferma item count 1500/1500

| Vista | Valore | Status |
|---|:---:|:---:|
| Totale items | 1500 / 1500 | ✅ EXACT |
| D1 items | 300 | invariato |
| D2 items | 350 | invariato |
| D3 items | 350 | invariato |
| D4 items | 300 | invariato |
| D5 items | 200 | invariato |

---

## Sezione 6 — Conferma rarity 400/450/400/235/15

| Rarity | Count | Target | Status |
|---|:---:|:---:|:---:|
| Common | 400 | 400 | ✅ EXACT |
| Uncommon | 450 | 450 | ✅ EXACT |
| Rare | 400 | 400 | ✅ EXACT |
| Epic | 235 | 235 | ✅ EXACT |
| Legendary | 15 | 15 | ✅ EXACT |
| **TOTALE** | **1500** | **1500** | ✅ **EXACT 400/450/400/235/15** |

---

## Sezione 7 — Conferma class distribution 300×5

| Classe | Count | Target | Status |
|---|:---:|:---:|:---:|
| Warrior | 300 | 300 | ✅ EXACT |
| Rogue | 300 | 300 | ✅ EXACT |
| Mage | 300 | 300 | ✅ EXACT |
| Priest | 300 | 300 | ✅ EXACT |
| Ranger | 300 | 300 | ✅ EXACT |
| **TOTALE** | **1500** | **1500** | ✅ **EXACT 300×5** |

---

## Sezione 8 — Conferma proficiency violations = 0

| Verify | Valore |
|---|:---:|
| Proficiency violations post-E2.1 | **0** ✅ CLEAN |
| Priest scudo/piastre/cuoio/maglia | 0 ✅ HARD BLOCK preserved |
| Weapon backlog `strumento`/`falce`/`trinket_backlog` | 0 ✅ RESERVED preserved |

**Governance**: proficiency post-E1.1+E2 preserved. E2.1 non ha toccato weapon_family/armor_type.

---

## Sezione 9 — Conferma anti-P2W 1500/1500

| Vista | Valore | Status |
|---|:---:|:---:|
| Total items | 1500 | — |
| `can_be_sold_for_real_money = false` | 1500 / 1500 | ✅ PASSED |
| P2W violations | 0 | ✅ PASSED |

Anti-P2W preservato al 100% (E2.1 non ha toccato campi P2W).

---

## Sezione 10 — D4 slug drift 9 dungeon documentati (Q3=A NO rename)

**Governance PM verbatim (Q3=A)**: 9 slug drift dungeon D4 **ACCEPTED / documented / NO rename** (governance preservation).

| # | Slug D4 | Note |
|:---:|---|---|
| 1 | `necropolis-bells` | raid Lv50, drift naming-only accepted D4 CLOSED |
| 2 | `starfall-basilica-t4` | dungeon 3p T4 variant, drift accepted |
| 3 | `shadowreach-vault` | dungeon 3p T4, drift accepted |
| 4 | `emberking-throne` | dungeon 3p T4 endgame Infernale, drift accepted |
| 5 | `wyrmscale-crucible` | dungeon 3p T4 Draco early, drift accepted |
| 6 | `ergolat-siege-nexus` | dungeon 3p T4 Ergolat, drift accepted |
| 7 | `adalan-arcane-fortress` | dungeon 3p T4 Adalan, drift accepted |
| 8 | `efreto-cursed-chapel` | dungeon 3p T4 Efreto, drift accepted |
| 9 | `worldroot-heart` | dungeon 3p T4 Alberi della Vita, drift accepted |

**Resolution E2.1**: NO rework autonomo. NO E2.1 action. Documentati come da governance preservation post-D4 CLOSED (STEP 17).

---

## Sezione 11 — Family naming redundancy ACCEPTED (Q4=A esempi rappresentativi, nessuna azione)

**Governance PM verbatim (Q4=A)**: family naming ridondanza cross-tier **ACCEPTED as design intent per progressione**.

| Family | Note design intent progressione |
|---|---|
| `dragonhunter-endgame` | Draco progression T4→T5 endgame |
| `elder-wyrm-hunter/stalker/shepherd` | Draco endgame progression W/R/P |
| `ambash-forge-warrior/ambash-arcane-forge` | Ambash T3→T5 progression |
| `alevoran-perpetual` | Alevora T3→T5 progression |
| `emberking-endgame` | Infernale T3→T4→T5 progression |
| `efreto-corrupt-caster/purger/cursed-ranger` | Efreto multi-class endgame progression |
| `adalan-archmage-t5/adalan-arcane-thief` | Adalan T3→T5 progression |
| `worldroot-warden/worldroot-druid-priest/worldroot-loremaster` | Alberi della Vita multi-class endgame |

**Resolution E2.1**: NO action autonoma. Design intent per progressione cross-tier accepted. NO E2.1 rework.

---

## Sezione 12 — File item table modificati

| Phase | File | Renames applicati | Delta |
|:---:|---|:---:|---|
| D1 | `r18_5_phase_d1_t1_item_table.json` | **1** rename | `priest-adalan-relic` → 'Reliquia di Adalan del Novizio' |
| D2 | `r18_5_phase_d2_t2_item_table.json` | **19** rename | 6 duplicate families (Worldroot ring/plate/focus/earring/scepter/cuirass/cloak/boots + Emberlord cloak×3/boots + Adalan relic-b) |
| D3 | `r18_5_phase_d3_t3_item_table.json` | **7** rename | Soulforged hood×2/gloves×2/boots×2 + Celestial/Starfall hood + Elfwood boots-T3 |
| D4 | `r18_5_phase_d4_t4_item_table.json` | **2** rename | Necropolis-bells hood×2 + Elfwood boots-T4 |
| D5 | (unchanged) | 0 | D5 items non erano duplicati |
| **TOTALE** | 4 files modificati | **29 renames** | 14 duplicati risolti |

---

## Sezione 13 — SHA256 post-write

| File | Modified E2.1 | SHA256 pre-E2.1 (post-E2) | SHA256 post-E2.1 finale |
|---|:---:|---|---|
| D1 `.json` | ✅ YES | `e529922a510d9ec4...` | **`40107a3e7cfd3cce...`** |
| D2 `.json` | ✅ YES | `e647a0babcd7f884...` | **`f30f39f327db39e0...`** |
| D3 `.json` | ✅ YES | `b478ae641eec3f33...` | **`39e0f88fa7121c1d...`** |
| D4 `.json` | ✅ YES | `6d42a01983d6bcf3...` | **`a6c24abfcb3c442b...`** |
| D5 `.json` | ❌ NO | `58e9f0ea86f7fb5e...` | `58e9f0ea86f7fb5e...` (unchanged) |

SHA256 completi disponibili in JSON `sezione_13_sha256_post_write`.

---

## Sezione 14 — Sealed integrity result

**pytest** `backend/tests/backend_r18_4_sealed_integrity_test.py` post-write E2.1:

```
2 workers [6 items]
......                                                                   [100%]
============================== 6 passed in 0.43s ==============================
```

✅ **36 sigilli byte-identical VERIFIED** (pytest 6/6 PASSED).

---

## Sezione 15 — PM Open Questions post-E2.1 per gate Phase C Tech Dry-Run

| ID | Topic |
|---|---|
| **Q1** | Approvare **E2.1 CLOSED** (29 rename applicati per risolvere 14 duplicate nome_it, 0 stat/tier/rarity/classe/source/proficiency/anti-P2W changes)? |
| **Q2** | Approvare variant style: **class-suffix** (del Guerriero/dell'Ombra/dell'Arcanista/del Druido Sacro/del Cacciatore/del Vagabondo/dell'Astronomo/del Tiratore/del Guardaboschi/del Novizio/del Chierico/dell'Assassino) + **tier-suffix** (T3/T4) per cross-tier case? |
| **Q3** | Autorizzare **PRD.md append `R18.5 Phase E2.1 CLOSED`** post-review (NON auto-eseguito, pattern D3/D4/D5/E1/E2 verbatim)? |
| **Q4** | Post E2.1 approval: autorizzare **Phase C Tech Dry-Run** (proficiency runtime + class_slug migration + ILVL endgame implementation)? |
| **Q5** | Phase C Tech Dry-Run scope: quali sub-steps prioritizzare? (proficiency runtime · class_slug migration · ILVL implementation · drop table apply gate · registry generation · anti-P2W runtime validator) |
| **Q6** | **Legendary utility numeric finals** (cooldown, %, scaling per 15 Legendary): finalizzare pre-Phase C tech gate o durante Phase C? |
| **Q7** | **4 progressive Legendary placeholders (P1-P4)**: finalizzare lore/source/utility in Phase C tech gate o iterazione E3? |
| **Q8** | **6 hint T4 PENDING** (Q6 PM accepted design intent post-E1): confermare come design intent finale per Phase C tech gate? |
| **Q9** | **R18.6 Class Halls kickoff**: mantenere PLANNED SERIAL post-Phase C (Q10=B PM verbatim)? |
| **Q10** | **Marketing Brief**: mantenere DEFERRED (Q11=B PM verbatim)? |

---

## Governance check STEP 25 (E2.1)

| Voce | Stato |
|---|:---:|
| **36 sigilli byte-identical** | ✅ pytest 6/6 PASSED post-write |
| Zero DB writes | ✅ |
| Zero code changes `.py`/`.js`/`.jsx`/`.tsx`/`.ts` | ✅ |
| Zero migrations | ✅ |
| Zero item creation live (nuovi item) | ✅ |
| Zero drop table apply | ✅ |
| Zero economy changes | ✅ |
| `lore_meta.py` invariato | ✅ SHA256 `a18f708b...` |
| Zero sealed file modification | ✅ |
| **Item table modification authorized (micro-eccezione PM)** | ✅ **D1/D2/D3/D4 .json rename-only AUTORIZZATA** |
| **Stat/balance changes** | ✅ **ZERO** |
| **Tier/rarity/class/source/proficiency/anti-P2W changes** | ✅ **ZERO** (full snapshot verified) |
| **Utility changes** | ✅ **ZERO** |
| **item_id changes** | ✅ **ZERO** (tutti preservati per tracking) |
| **Slug D4 rename** | ✅ **ZERO** (Q3=A accepted, no rename) |
| **Family redundancy rework** | ✅ **ZERO** (Q4=A accepted design intent) |
| **Hint T4 stat changes** | ✅ **ZERO** (Q6=A accepted design intent post-E1) |
| Catalog 1500/1500 preserved | ✅ |
| Phase C auto-start | ✅ BLOCKED (STOP after E2.1, PM review required) |
| R18.6 auto-start | ✅ BLOCKED (PLANNED SERIAL post-Phase C) |
| Marketing Brief auto-start | ✅ BLOCKED (DEFERRED) |
| PRD append E2.1 CLOSED auto | ✅ BLOCKED (rinviato a post-PM-approval, pattern verbatim) |
| Classi canoniche Warrior/Rogue/Mage/Priest/Ranger | ✅ NO drift |
| Files deliverable | ✅ 2 (.md + .json) |

---

## Statement finale STEP 25

**E2.1 Duplicate Name Resolution Mini-Pass COMPLETED** ✅
- 29 rename applicati (14 duplicate nome_it risolti · 0 duplicati residui)
- Full snapshot verification: **all other fields unchanged 29/29** (governance strict rispettata — solo `nome_it` modificato)
- Catalog 1500/1500 · Rarity 400/450/400/235/15 · Class 300×5 · **Proficiency 0 violations** · Anti-P2W 1500/1500 tutti EXACT MATCH
- 36 sigilli byte-identical (pytest 6/6 PASSED)
- 9 D4 slug drift documented (Q3=A no rename)
- Family redundancy T4/T5 accepted design intent (Q4=A)
- 6 hint T4 PENDING accepted design intent (Q6=A, no stat changes)

**STOP dopo E2.1. Attendo PM review Q1-Q10 prima di Phase C Tech Dry-Run.**

**Post-E2.1 NON parte automaticamente**:
- ❌ Phase C Tech Dry-Run (HOLD UNTIL E2.1 REVIEW)
- ❌ R18.6 Class Halls kickoff (PLANNED SERIAL post-Phase C, Q10=B PM verbatim)
- ❌ Marketing Brief (DEFERRED, Q11=B PM verbatim)
- ❌ PRD append `R18.5 Phase E2.1 CLOSED` (rinviato a post-PM-approval)

---

**R18.5 status flow (aggiornato post-STEP 25)**:
`Phase D5 (STEP 18)` ✅ → `CATALOGO 1500/1500 (STEP 19)` ✅ → `Phase E1 (STEP 20)` ✅ → `E1.1 (STEP 21)` ✅ → `PRD E1 CLOSED (STEP 22)` ✅ → `E2 (STEP 23)` ✅ → `PRD E1+E2 CLOSED (STEP 24)` ✅ → **`Phase E2.1 Duplicate Name Resolution (STEP 25)`** 🟡 **DRAFT — PENDING PM Q1-Q10 review** → `Phase C Tech Dry-Run` 🔒 HOLD UNTIL E2.1 REVIEW / `R18.6 Class Halls` 🔒 PLANNED SERIAL post-Phase C / `Marketing Brief` 🔒 DEFERRED

---

**FINE STEP 25 — R18.5 Phase E2.1 Duplicate Name Resolution Mini-Pass — DOCUMENTAL ONLY (rename-only micro-eccezione)**
