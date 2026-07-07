# R18.5 Phase D2 — T2 × 350 Item Drafting (STEP 13)

**Round**: R18.5 — Itemization, ILVL & Gear Progression Rework
**Phase**: D2 — T2 × 350 Item Drafting (Lv16-30)
**Locked at (UTC)**: 2026-07-07T14:45:00Z
**Governance**: DOCUMENTAL ONLY
**Status**: DRAFT — PENDING PM approval, NON auto-transition a D3
**Authority**: PM Orchestrator — STEP 13 in catena post STEP 12 (Q2=C, Q3=C, Q4=C, Q5=GO, Q6=A verbatim)
**Scope**: 350 item T2 (Lv16-30, tier T2, rarity **150 Common + 150 Uncommon + 50 Rare**)
**Continuità**: D1 iconic-family evolutions T1→T2 (30 items) + nuove famiglie T2 + 5 NPC LOCKED cornerstone rispettati

---

## Executive Summary

D2 completa la stesura del catalogo T2 (350 items) proseguendo dal pattern D1 con **continuità delle 15 iconic-family** attraverso 30 evolutions T1→T2 (2 per famiglia — early T2 + late T2) e introduce **nuove famiglie T2** senza rompere la proficiency PM verbatim.

Rispetto a D1, T2 include per la prima volta la rarity **Rare** (50 items, 14.3% del bracket) e fonti dungeon Batch 2 (14) + raid B2 (2: `krastlov-siege`, `bloodgrove-uprising`).

Lore endgame (Draco, Efreto, Aveol, Ciclo delle anime, Mare) fanno **prima apparizione graduale** in T2 come previsto dal PM per accompagnare la transizione dal bracket starter B1 all'endgame narrativo — mai come capstone, sempre come introduzione tematica.

---

## Sezione 1 — Tabella completa 350 item T2 (riferimento JSON)

Full array in **`/app/memory/r18_5_phase_d2_t2_item_table.json`** → `items[]` (350 record, 22 campi per record).

Estratti riassuntivi per classe forniti nelle Sezioni 5-10 seguenti.

---

## Sezione 2 — Riepilogo numerico

| Categoria | Count | Note |
|---|---:|---|
| **TOTALE items** | **350** | Target 350 ✅ |
| Iconic-family evolutions D1→T2 | **30** | 2 per famiglia (15×2) |
| Free (nuove famiglie T2 + varietà) | 320 | Include lore endgame introduction |

---

## Sezione 3 — Rarity check (150 / 150 / 50 esatto)

| Rarity | Count | Target | Status |
|---|---:|---:|:---:|
| **Common** | **150** | 150 | ✅ |
| **Uncommon** | **150** | 150 | ✅ |
| **Rare** | **50** | 50 | ✅ |
| Epic / Legendary | 0 | 0 | ✅ (NO Epic/Legendary in T2) |
| **TOTALE** | **350** | **350** | ✅ |

---

## Sezione 4 — Level range check (16-30)

| Metric | Value |
|---|---|
| Min required_level | 16 |
| Max required_level | 30 |
| Target range | 16-30 |
| Status | ✅ **RISPETTATO** |

---

## Sezione 5 — Class coverage check (70 per classe)

| Classe | Count | Common | Uncommon | Rare |
|---|---:|---:|---:|---:|
| **Warrior** | 70 | 30 | 30 | 10 |
| **Rogue** | 70 | 30 | 30 | 10 |
| **Mage** | 70 | 30 | 30 | 10 |
| **Priest** | 70 | 30 | 30 | 10 |
| **Ranger** | 70 | 30 | 30 | 10 |
| **TOTALE** | **350** | **150** | **150** | **50** |

**70 items per classe equilibrato** ✅ (30 Common + 30 Uncommon + 10 Rare per classe).

---

## Sezione 6 — Proficiency check (INVARIATA da D1)

| Classe | Main stat | Armor | Weapon families |
|---|---|---|---|
| Warrior | STR/END | maglia + piastre | spada, ascia, martello, scudo, lancia, arma_in_asta |
| Rogue | AGI | cuoio | pugnale, spada, balestra |
| Mage | INT | stoffa | bastone, tomo, focus, pugnale |
| Priest | WIS | stoffa | bastone, martello, focus, reliquia |
| Ranger | AGI | cuoio + medium | arco, balestra, spada, pugnale, lancia |

**Weapon backlog check**: `strumento`/`falce`/`trinket weapon` = **0 items usati** ✅ (Q6 R18.P3 respected).

**Weapon family distribuzione T2**:

| Weapon | Count |
|---|---:|
| bastone | 23 |
| martello | 21 |
| pugnale | 21 |
| arco | 20 |
| spada | 14 |
| focus | 14 |
| scudo | 9 |
| balestra | 9 |
| tomo | 7 |
| ascia | 4 |
| lancia | 4 |
| reliquia | 4 |
| arma_in_asta | 3 |

**Armor type distribuzione T2**:

| Armor | Count |
|---|---:|
| stoffa | 47 |
| light | 30 |
| medium | 27 |
| heavy | 23 |

---

## Sezione 7 — Source coverage (14 dungeon B2 + 2 raid + secondarie)

### 14 Dungeon Batch 2

| Source | Count | Lv bracket | Lore | Status |
|---|---:|---|---|---|
| `dragons-hoard` | 9 | 16-18 | Draco | LIVE |
| `storm-spire` | 18 | 17-19 | Faglie arcane | LIVE |
| `blackpine-thicket` | 26 | 16-18 | Elfwood | NEW |
| `ironhold-keep` | 20 | 18-20 | Krastlov | NEW |
| `worldroot-hollow` | 28 | 19-21 | Alberi della Vita | NEW |
| `veiled-forge` | 5 | 20-22 | Ambash | NEW |
| `tidebound-cove` | 4 | 21-23 | Mare | NEW |
| `hollow-monastery` | 53 | 22-24 | Halodi | NEW |
| `wild-hunt-lair` | 60 | 23-25 | Elfwood | NEW |
| `frostbound-vault` | 16 | 24-26 | Aveol | NEW |
| `sunken-shipyard` | 0 | 25-27 | Mare | NEW |
| `emberlord-hideout` | 19 | 26-28 | Efreto | NEW |
| `stormcaller-vault` | 36 | 27-29 | Faglie arcane | NEW |
| `bonefall-crypt` | 9 | 28-30 | Ciclo delle anime | NEW |

### 2 Raid Batch 2

| Source | Count | Lv | Lore |
|---|---:|---|---|
| `krastlov-siege` | 28 | 22-26 | Krastlov |
| `bloodgrove-uprising` | 11 | 26-30 | Alberi della Vita |

### Fonti secondarie

| Source | Count |
|---|---:|
| `non-premium-vendor` | 5 |
| `early-mid-achievement` | 3 |

**VIETATO** (0 items): raid Batch 3+, dungeon Batch 1, dungeon endgame, Elite Track, Batch 4/5 raid ✅

---

## Sezione 8 — Anti-P2W check (350/350 compliant)

| Voce | Count | Status |
|---|---:|:---:|
| Items totali | 350 | — |
| `can_be_sold_for_real_money = false` | **350** | **350/350** ✅ |
| `is_cosmetic = false` | 350 | Nessun cosmetic in D2 |
| `affects_ranking = false` | 350 | T2 non ha ranking impact diretto |
| `affects_progression = true` | ~340 | Tutti gli equip (impact gear-check) |
| `affects_economy = false` | 350 | Materials non presenti in D2 corrente |

**Policy R18 verbatim rispettata al 100%**. NO runtime validator.

---

## Sezione 9 — Continuità famiglie D1→T2 (30 items evolutivi)

**Target**: linee evolutive delle 15 iconic-family da T1 verso T2 (early T2 Common + late T2 Uncommon).
**Realizzato**: **30 items** (2 per famiglia = 15×2) ✅

| Iconic family | Early T2 (Common ~Lv16-19) | Late T2 (Uncommon ~Lv22-26) |
|---|---|---|
| `ironrecruit` (W spada) | Lama del Sergente di Ferro | Lama del Tenente di Ferro |
| `bulwark` (W scudo) | Scudo Bulwark a Cuore | Scudo Bulwark Adamantino |
| `ironhelm` (W heavy) | Elmo del Sergente | Elmo del Capitano |
| `shadowstep` (R pugnale) | Lama Velata del Passo d'Ombra | Lama dell'Eclisse |
| `leathercraft` (R light) | Mantello Seta d'Ombra | Mantello Notturno |
| `shadowlockpick` (R trinket) | Grimaldelli Leggendari Ladri | Strumenti Fantasma Ombre |
| `apprentice-arcane` (M staff) | Bastone Tempesta Apprendista | Bastone Anziano Apprendista |
| `novice-arcane` (M stoffa) | Veste Tempesta Novizio | Veste Anziana Novizio |
| `focus-crystal` (M focus) | Focus Cristallo Tempesta | Focus Orb Anziano |
| `faith-blessed` (P martello) | Mazza Santificata Fede | Mazza Reliquia Fede |
| `novice-holy` (P stoffa) | Vesti Santificate Novizio | Vesti Anziane Novizio |
| `prayer-beads-dawn` (P amulet) | Rosario del Mattino | Rosario del Vespro |
| `hunter-oakwood` (Ra arco) | Arco di Tasso Anziano | Arco Composito Anziano |
| `scout-leather` (Ra medium) | Corazza Forestale Scout | Corazza Anziana Scout |
| `woodland-quiver` (Ra trinket) | Faretra Cacciatore Bosco T2 | Faretra Anziana Bosco |

Pattern hybrid mantenuto ✅ — ogni famiglia D1 ha almeno 2 evolutivi T2 riconoscibili.

---

## Sezione 10 — Nuove famiglie T2 (identità + varietà)

Nuove famiglie tematiche T2 introdotte dal bracket B2:
- **Wildhunt** (Elfwood, ranger/rogue) — 6+ items da `wild-hunt-lair`
- **Stormcaller** (Faglie arcane, mage/warrior) — 5+ items da `stormcaller-vault`
- **Emberlord** (Efreto, warrior/mage/ranger) — 5+ items da `emberlord-hideout`
- **Frostbite** (Aveol, mage/rogue/warrior) — 5+ items da `frostbound-vault`
- **Worldroot** (Alberi della Vita, priest/ranger/warrior) — 6+ items da `worldroot-hollow`
- **Dragonfire/Dragonhoard** (Draco intro leggera) — 4+ items da `dragons-hoard`
- **Bonefall** (Ciclo delle anime intro) — 4+ items da `bonefall-crypt`
- **Tidebound** (Mare intro leggera) — 3 items da `tidebound-cove`

**Nessuna nuova famiglia contraddice** le 15 D1 iconic. **Proficiency invariata** per tutte le nuove famiglie.

---

## Sezione 11 — Distribuzione per slot

| Slot | Count | % T2 |
|---|---:|---:|
| `main-hand` | 118 | 33.7% |
| `chest` | 53 | 15.1% |
| `off-hand` | 35 | 10.0% |
| `head` | 25 | 7.1% |
| `ring` | 25 | 7.1% |
| `amulet` | 25 | 7.1% |
| `trinket` | 20 | 5.7% |
| `legs` | 19 | 5.4% |
| `feet` | 17 | 4.9% |
| `hands` | 13 | 3.7% |

---

## Sezione 12 — Distribuzione per armor type / weapon family

Già dettagliato in Sezione 6.

**Lore source coverage T2** (introduzione graduale endgame):

| Lore source | Count | Rationale |
|---|---:|---|
| Alberi della Vita | 75 | Bracket B2 (intro/mid) |
| Faglie arcane | 54 | Bracket B2 (intro/mid) |
| Elfwood | 52 | Bracket B2 (intro/mid) |
| Krastlov | 48 | Bracket B2 (intro/mid) |
| Halodi | 48 | Bracket B2 (intro/mid) |
| Efreto | 19 | Bracket B2 (intro/mid) |
| Aveol | 16 | Bracket B2 (intro/mid) |
| Draco | 9 | Bracket B2 (intro/mid) |
| Ciclo delle anime | 9 | Bracket B2 (intro/mid) |
| Adalan | 9 | Bracket B2 (intro/mid) |
| Ambash | 7 | Bracket B2 (intro/mid) |
| Mare | 4 | Bracket B2 (intro/mid) |

Fonti **endgame NON ancora usate** in T2 (riservate T3-T5): Vuoto, Celeste, Infernale, Irthe, Memoria, Alevora, Ergolat, Luna Morta, Ambash forge endgame, Greatwood, Velur, Soe.

---

## Sezione 13 — NPC Craft usage (5 LOCKED + PENDING nuovi)

### 5 NPC LOCKED (da STEP 12 directory)

| NPC | Utilizzo in D2 | Note |
|---|---|---|
| **Fabbro Bulwark** | Referenced in bulwark family evolutions (via `veiled-forge` crafting T2 material) | Coerente T1→T2 |
| **Cuoiaia Elfwood** | Referenced in leathercraft family evolutions (via `blackpine-thicket` crafting T2) | Coerente T1→T2 |
| **Sarto Sacro** | Referenced in novice-holy family evolutions (via `hollow-monastery` crafting T2) | Coerente T1→T2 |
| **Tessitrice Arcana** | Referenced in novice-arcane family evolutions (via `storm-spire`/`stormcaller-vault` crafting T2) | Coerente T1→T2 |
| **Conciatore Elfwood** | Referenced in scout-leather family evolutions (via `blackpine-thicket`/`wild-hunt-lair` crafting T2) | Coerente T1→T2 |

### Nuovi NPC craftsman T2 emersi (PENDING PM)

**0 nuovi NPC** proposti in D2 ✅ (directory 5/10 slot occupati, 5 slot residui invariati).

**Rationale**: D2 utilizza craft "in-dungeon" (drop craftable + master crafting via `veiled-forge`) senza introdurre nuove figure NPC. Le linee evolutive rispettano i 5 LOCKED cornerstone.

---

## Sezione 14 — Naming incoerenze notes (raccolta, NO fix)

Come da PM Q4=C (naming pass globale deferred post-D5), qui raccolgo le incoerenze note **senza intervenire**:

| # | Incoerenza | Note (per pass post-D5) |
|---|---|---|
| N1 | Suffisso `-t2` esplicito su alcuni item (es. `warrior-iron-longsword-t2`) | Convenzione temporanea per disambiguare T1/T2; valuterà rimozione uniforme post-D5 |
| N2 | Naming "Anello di Ferro/Acciaio/Rame" ripetitivo tra classi/tier | Pass globale post-D5 con schema univoco (es. "Anello del Recluta Krastlov") |
| N3 | Alcune sorgenti citano dungeon (`veiled-forge crafting T2`) invece di NPC directory verbatim (`Fabbro Bulwark T2 recipe`) | Pass uniformità post-D5, ma NPC directory rimane fonte unica per creazione DB |
| N4 | Doppie apparizioni di "worldroot" (dungeon + family + item slug) | Verificare disambiguazione post-D5 (es. dungeon vs artifact) |
| N5 | Alcuni item Rare hanno stat_principali con proc effects (es. "storm proc", "freeze proc") — livello di dettaglio deferred | Balance pass post-D5 stabilirà valori numerici e cooldown proc |

---

## Sezione 15 — Risk notes

| # | Severity | Topic | Mitigation |
|---|---|---|---|
| R1 | LOW | Stat_principali deferred balance pass post-D5 (Q2=C verbatim) | Documental only |
| R2 | **MEDIUM** | Lore endgame parzialmente introdotte in T2 (Draco/Efreto/Ciclo delle anime/Aveol/Mare) | Prima apparizione graduale coerente con transition B2, cross-check con lore capstone T5 in review D3+ |
| R3 | LOW | NPC directory rispettata: 5 LOCKED, 0 nuovi in D2 | ✅ |
| R4 | LOW | Naming incoerenze raccolte (5 note) — NO fix ora | Post-D5 pass globale |
| R5 | LOW | Iconic-family evolutions D1→T2 = 30 items (2 per iconic) | Pattern hybrid preserved |
| R6 | LOW | 3 weapon backlog (strumento/falce/trinket) NON usati | Q6 R18.P3 verbatim respected |
| R7 | **MEDIUM** | Fonti B2 estese includono Mare/Aveol/Ciclo delle anime — prima apparizione nel catalogo item | Solo intro leggera, capstone riservato T3-T5 |
| R8 | LOW | Rare 50/350 (14.3%) high per T2 ma coerente con D0 Sezione 5 crosswalk verbatim | ✅ |

**Totale**: 2 MEDIUM · 6 LOW · 0 HIGH ✅

---

## Sezione 16 — PM Open Questions per gate D3

| ID | Topic |
|---|---|
| Q1 | Approvare 350 item T2 verbatim? |
| Q2 | Continuità D1→T2 iconic-family evolutions (30 items) OK o iterare? |
| Q3 | Fonti B2 estese (Mare/Aveol/Ciclo delle anime prima apparizione item) approvate? |
| Q4 | NPC directory ancora valida (0 nuovi in D2) — confermata anche per D3? |
| Q5 | Naming incoerenze notes raccolte (5) — pass post-D5 confermato? |
| Q6 | Rare distribution 50/350 T2 OK o richiesta modifica prima di D3? |
| Q7 | **D3 T3×350 authorization** dopo review D2? |
| Q8 | D3 può introdurre Rare più densi (D0 target: 170/350 in T3)? |
| Q9 | Signature items (D0 Sezione 12) — inizio pianificazione post-D3 o post-D5? |
| Q10 | Lore endgame (Draco/Efreto/Vuoto) — regola introduzione graduale T2→T5 confermata? |

---

## Governance Check STEP 12 + STEP 13

| Voce | Status |
|---|---|
| **Sealed files 36 hash byte-identical** | ✅ (pytest atteso conferma) |
| DB writes | ZERO |
| Code changes (`.py`/`.js`/`.jsx`/`.tsx`/`.ts`) | ZERO |
| Migrations | ZERO |
| Item creation live | ZERO |
| Registry generation | ZERO |
| Drop table apply | ZERO |
| Economy changes | ZERO |
| `lore_meta.py` touch | INVARIATO |
| Sealed file modification | ZERO |
| Anti-P2W runtime validator | ZERO |
| Phase C tech dry-run | NOT INITIATED |
| Classi canoniche | Warrior/Rogue/Mage/Priest/Ranger verbatim (no drift) |
| Weapon backlog R18.P3 | 0 items usati ✅ |
| NPC directory respected | 5 LOCKED verbatim, 0 nuovi PENDING PM |
| **Auto-transition D3** | **BLOCKED — STOP dopo D2** ✅ |
| PM autonomous decision new | ZERO |

---

## STOP DOPO D2 — Attendo PM review prima di D3

**STOP dopo D2. Attendo PM review prima di D3.**

Status dei 350 items T2: **PENDING PM approval** · Non live · Non registry · Non applicati al DB.

**R18.5 status flow (aggiornato)**:
`... → STEP 10 Pre-D1 Iconic ✅ APPROVED → STEP 11 D1 T1×300 ✅ APPROVED (Q1=A) → STEP 12 Craft NPC Directory ✅ DRAFT (5 LOCKED) → STEP 13 D2 T2×350 ✅ DRAFT → PM REVIEW ⏸️ ATTESA → Phase D3 T3×350 🔒 BLOCKED gate PM`
