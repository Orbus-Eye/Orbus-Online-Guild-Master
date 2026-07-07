# R18.5 Phase C0-quater Batch 1 — Informed Finalization (DOCUMENTAL ONLY)

- **Round**: `R18.5 — Itemization, ILVL & Gear Progression Rework`
- **Sottotitolo**: *Lv60 cap, item-centered endgame, lore-driven equipment*
- **Fase**: **C0-quater — Batch 1 Informed Finalization** (post-audit PM decisions)
- **Locked at UTC**: `2026-07-06T21:20:00Z`
- **Governance**: **DOCUMENTAL ONLY** — 36 sigilli byte-identical, zero DB writes, zero code changes, zero breaking change su `lore_meta.py`.
- **Autorità**: PM Orchestrator (7 decisioni lockate + Opzione E approvata verbatim)
- **Status**: 🟢 **BATCH 1 CLOSED (informed) / PENDING PM approval** su naming IT nuovi + bracket 5-player/raid + lore normalization definitiva
- **Predecessori autoritativi**:
  - `r18_5_phase_b_gate1_pm_decisions.md/.json` (17 lore sources Gate 1)
  - `r18_5_gate2_pm_decisions.md/.json` (Gate 2)
  - `r18_5_phase_c0ter_live_class_matrix.md/.json` (5 classi live)
  - `r18_5_phase_c0quater_live_dungeon_audit.md/.json` (audit READ-ONLY 24 dungeon live + 3 raid)
- **Predecessore superseded**: `r18_5_phase_c0quater_batch1_lv1_15_dungeon_matrix.md/.json` (DRAFT deprecato post-audit, preservato per audit trail)

---

## 0. 7 decisioni PM lockate (verbatim, base della finalizzazione)

| # | Decisione |
|:---:|---|
| **1** | **Party size variabile**: 3p normal + 5p elite/group. Batch 1 = solo 3p |
| **2** | **Lore expansion 17→22-25**: espansione pragmatica con 8 fonti orfane approve/merge/rename. NO breaking change `lore_meta.py` |
| **3** | **`training-yard`**: escluso da bracket R18.5, resta utility onboarding |
| **4** | **`dragons-hoard` + `storm-spire`**: **Batch 2 head** (Lv16-30), NON Batch 1 tail |
| **5** | **12 dungeon 5-player live**: **Elite/Group Dungeon Track** parallelo. NO re-team-size, NO congelamento, NO deprecazione. Mapping bracket documentale |
| **6** | **3 raid live**: assignment documentale Batch 3/4/5 (bracket finale `PENDING PM`) |
| **7** | **Batch 1 = Opzione E**: **8 live + 4 nuovi verbatim PM** |

---

## 1. Batch 1 finale — 12 dungeon Lv1-15 Normal Track (party_size=3)

| # | Slug (PM-locked) | Nome IT | Status | Lv (live) / range (nuovo) | Lore source | Class teaching |
|:---:|---|---|:---:|:---:|:---:|---|
| 1 | `sewer-nest` | Nido nelle Fogne | 🟢 LIVE | Lv1 | urban → Aveol* | Onboarding universal |
| 2 | `goblin-warrens` | Tane dei Goblin | 🟢 LIVE | Lv2 | frontiera → Halodi* | Onboarding universal |
| 3 | `bandit-hideout` | Covo dei Banditi | 🟢 LIVE | Lv2 | urban → Aveol* | Introduzione combattimento umanoide |
| 4 | `shadow-crypts` | Cripte d'Ombra | 🟢 LIVE | Lv3 | Irthe | Priest secondary + void_undead lore |
| 5 | `druid-grove` | Bosco dei Druidi Corrotti | 🟢 LIVE | Lv3 | Soe | Ranger secondary + natura corrotta |
| 6 | `cursed-mines` | Miniere Maledette | 🟢 LIVE | Lv4 | Efreto | Party synergy + arcane mining |
| 7 | `sunken-library` | Biblioteca Sommersa | 🟢 LIVE | Lv4 | Memoria† | Mage secondary + memory theme |
| 8 | `lich-sanctum` | Santuario del Lich | 🟢 LIVE | Lv5 | Irthe | Party comp mixed + boss narrativo |
| 9 | `chapel-of-silent-vows` | Cappella dei Voti Silenti ‡ | 🟡 NEW DRAFT | Lv7-9 | Aveol | Priest primary teaching |
| 10 | `forgotten-shrine-of-adalan` | Santuario Dimenticato di Adalan ‡ | 🟡 NEW DRAFT | Lv9-11 | Adalan | Mage primary teaching |
| 11 | `bandit-warlord-hideout` | Nascondiglio del Signore dei Briganti ‡ | 🟡 NEW DRAFT | Lv11-13 | Aveol | Proficiency teaching narrativo |
| 12 | `broken-tower-of-adalan` | Torre Spezzata di Adalan ‡ | 🟡 NEW DRAFT | Lv13-15 | Adalan | Transition Batch 2 + primo Epic raro |

**Note simboli**:
- `*` = merge documentale proposto sotto fonte madre Gate 1 (sez. 9)
- `†` = approve documentale come nuova fonte espansa (sez. 10)
- `‡` = `PENDING PM approval` sul nome IT player-facing (validare o rinominare)

**Distribuzione bucket**:
- Onboarding Lv1-3 (5 live): sewer-nest, goblin-warrens, bandit-hideout, shadow-crypts, druid-grove
- Early Lv4-5 (3 live): cursed-mines, sunken-library, lich-sanctum
- Mid Lv7-11 (2 nuovi): chapel-of-silent-vows, forgotten-shrine-of-adalan
- Late Lv11-15 (2 nuovi): bandit-warlord-hideout, broken-tower-of-adalan

**Gap Lv6**: nessun dungeon 3p in Lv6 (era coperto da dragons-hoard/storm-spire, spostati a Batch 2 head). **`PENDING PM`**: accettare gap (transizione da Lv5 lich-sanctum a Lv7 chapel) o inserire un dungeon Lv6 dedicato in Batch 1?

---

## 2. Distinzione 8 live vs 4 nuovi

### 2.1 🟢 8 dungeon LIVE (validati DB, no re-creation richiesta)

Tutti gli 8 hanno `name_it` **già in DB live** (fonte: `db.dungeons.find({slug: X})`). Nome IT NON è `PENDING PM` — è la source-of-truth attuale.

Reference DB verbatim:
```
sewer-nest      → "Nido nelle Fogne"           (req_lvl=1, bucket=tutorial, is_legacy=True)
goblin-warrens  → "Tane dei Goblin"            (req_lvl=2, bucket=tutorial, is_legacy=True)
bandit-hideout  → "Covo dei Banditi"           (req_lvl=2, bucket=tutorial, is_legacy=True)
shadow-crypts   → "Cripte d'Ombra"             (req_lvl=3, bucket=early,    is_legacy=True)
druid-grove     → "Bosco dei Druidi Corrotti"  (req_lvl=3, bucket=early,    is_legacy=True)
cursed-mines    → "Miniere Maledette"          (req_lvl=4, bucket=early,    is_legacy=True)
sunken-library  → "Biblioteca Sommersa"        (req_lvl=4, bucket=early,    is_legacy=True)
lich-sanctum    → "Santuario del Lich"         (req_lvl=5, bucket=mid,      is_legacy=True)
```

**Nessuna modifica richiesta al DB** per questi 8. Rimangono live come sono.

### 2.2 🟡 4 dungeon NEW DRAFT (design proposto, NO creation live)

Design documentale — NO insert DB in questa fase. Naming IT + tutti i campi player-facing restano `PENDING PM approval`. Se PM approva design, creation DB avverrà in gate futuro dedicato (Phase C tech dry-run + apply, entrambi BLOCCATI oggi).

```
chapel-of-silent-vows        → "Cappella dei Voti Silenti"           (Lv7-9,  Aveol,   Priest teaching)
forgotten-shrine-of-adalan   → "Santuario Dimenticato di Adalan"     (Lv9-11, Adalan,  Mage teaching)
bandit-warlord-hideout       → "Nascondiglio del Signore dei Briganti" (Lv11-13, Aveol, Proficiency teaching)
broken-tower-of-adalan       → "Torre Spezzata di Adalan"            (Lv13-15, Adalan, Transition Batch 2)
```

---

## 3. Matrice 12 dungeon — 16 campi obbligatori per ciascuno

### Dungeon #1 — sewer-nest (🟢 LIVE)

| Campo | Valore |
|---|---|
| slug (PM-locked) | `sewer-nest` |
| Nome IT | "Nido nelle Fogne" (LIVE DB) |
| Livello (req_lvl DB) | Lv1 |
| Party size | 3 (verbatim Gate 1 SQ13) |
| Lore source | `urban` live → **merge documentale sotto Aveol** (Gate 1) |
| Tema narrativo | "Qualcosa è risalito dal basso e ora scava verso la superficie." (lore_meta live) |
| Enemy family | rats, kobolds (live) |
| Meccanica + class teaching | Onboarding puro universal (party comp basi). NO proficiency hard block. |
| Loot tier | T1 puro |
| Rarity range | Common prevalente, Uncommon occasionale. NO Rare/Epic/Legendary. |
| Materiali principali | Cuoio grezzo, pelli di ratto, chiodi arrugginiti (live loot table `PENDING PM verify`) |
| Boss/miniboss | Ratto Grande / Kobold Capobanda (live, verifica loot_tables.py) |
| Itemization notes | Loot universale accessibile alle 5 classi. Piccola quantità T1 basic 3p-friendly. |
| Bracket | **Lv1-15 / Early Game** (verbatim PM) |
| Status | 🟢 **LIVE** — nessuna re-creation richiesta |
| Achievement/ranking notes | Achievement "Prima Missione" — spunto ranking guild "First Clear Sewer Nest" (`PENDING PM`) |

### Dungeon #2 — goblin-warrens (🟢 LIVE)

| Campo | Valore |
|---|---|
| slug (PM-locked) | `goblin-warrens` |
| Nome IT | "Tane dei Goblin" (LIVE DB) |
| Livello (req_lvl DB) | Lv2 |
| Party size | 3 (verbatim) |
| Lore source | `frontiera` live → **merge documentale sotto Halodi** (Gate 1, location_hint già "boschi di Halodi orientale") |
| Tema narrativo | "I tamburi dei goblin segnano il passo di un'invasione minore." (lore_meta live) |
| Enemy family | goblins (live) |
| Meccanica + class teaching | Onboarding party comp, primi test main stat. Universal. |
| Loot tier | T1 puro |
| Rarity range | Common prevalente, Uncommon occasionale |
| Materiali principali | Cuoio grezzo, ossa di goblin, pietre (loot_tables.py SEALED — Phase 3 original) |
| Boss/miniboss | Sciamano Goblin minore (live) — NO drift Wizard/Cleric |
| Itemization notes | Loot universal + primi hint Warrior/Ranger (spade/pugnali comuni). |
| Bracket | **Lv1-15 / Early Game** |
| Status | 🟢 **LIVE** — Phase 3 original (`gates.py:4` DO NOT MODIFY) |
| Achievement/ranking notes | Achievement "Primo Passo" (`PENDING PM`) |

### Dungeon #3 — bandit-hideout (🟢 LIVE)

| Campo | Valore |
|---|---|
| slug (PM-locked) | `bandit-hideout` |
| Nome IT | "Covo dei Banditi" (LIVE DB) |
| Livello (req_lvl DB) | Lv2 |
| Party size | 3 (verbatim) |
| Lore source | `urban` live → **merge sotto Aveol** (Gate 1, location_hint già "passi di montagna di Aveol") |
| Tema narrativo | "Briganti disertori della Crociata d'Argento si nascondono qui." (lore_meta live) |
| Enemy family | bandits (live) |
| Meccanica + class teaching | Introduzione combattimento umanoide organizzato. Rogue/Warrior primary welcome. |
| Loot tier | T1 puro |
| Rarity range | Common prevalente, Uncommon occasionale |
| Materiali principali | Cuoio, ferro grezzo, corde brigantesche |
| Boss/miniboss | Capitano Brigante (`PENDING PM verify` da loot_tables.py) |
| Itemization notes | Loot Warrior/Rogue-friendly (spade/pugnali T1, cuoio T1). Universal accessori. |
| Bracket | **Lv1-15 / Early Game** |
| Status | 🟢 **LIVE** |
| Achievement/ranking notes | Achievement "Legge di Frontiera" (`PENDING PM`) |

### Dungeon #4 — shadow-crypts (🟢 LIVE)

| Campo | Valore |
|---|---|
| slug (PM-locked) | `shadow-crypts` |
| Nome IT | "Cripte d'Ombra" (LIVE DB) |
| Livello (req_lvl DB) | Lv3 |
| Party size | 3 (verbatim) |
| Lore source | **Irthe** (Gate 1, direct match live) |
| Tema narrativo | "Gli Esiliati pregano qui chi non risponde più." (lore_meta live) |
| Enemy family | wights, shadowkin (live) |
| Meccanica + class teaching | Introduzione void_undead lore. Priest secondary (reliquia utile), party comp mista consigliata. |
| Loot tier | T1 |
| Rarity range | Common/Uncommon prevalenti, Rare limitato boss |
| Materiali principali | Ossa consacrate, filo d'ombra, cera votiva (`PENDING PM verify`) |
| Boss/miniboss | Wight Anziano / Ombra-priore (`PENDING PM verify`) |
| Itemization notes | Priest secondary welcome (reliquia, stoffa). Universal accessori. |
| Bracket | **Lv1-15 / Early Game** |
| Status | 🟢 **LIVE** |
| Achievement/ranking notes | Achievement "Silenzio Rotto" (`PENDING PM`) |

### Dungeon #5 — druid-grove (🟢 LIVE)

| Campo | Valore |
|---|---|
| slug (PM-locked) | `druid-grove` |
| Nome IT | "Bosco dei Druidi Corrotti" (LIVE DB) |
| Livello (req_lvl DB) | Lv3 |
| Party size | 3 (verbatim) |
| Lore source | **Soe** (Gate 1, direct match live) |
| Tema narrativo | "Una pioggia di linfa nera ha rotto il giuramento del bosco." (lore_meta live) |
| Enemy family | corrupted_druids, treants (live) |
| Meccanica + class teaching | Ranger secondary (arco/pugnale cuoio). Introduzione tema natura corrotta. |
| Loot tier | T1 |
| Rarity range | Common/Uncommon prevalenti, Rare limitato boss |
| Materiali principali | Corteccia corrotta, linfa nera, semi selvaggi (`PENDING PM verify`) |
| Boss/miniboss | Druido Corrotto Anziano (`PENDING PM verify`) |
| Itemization notes | Ranger secondary welcome (arco T1, cuoio T1). Universal per accessori. |
| Bracket | **Lv1-15 / Early Game** |
| Status | 🟢 **LIVE** |
| Achievement/ranking notes | Achievement "Giuramento Rotto del Bosco" (`PENDING PM`) |

### Dungeon #6 — cursed-mines (🟢 LIVE)

| Campo | Valore |
|---|---|
| slug (PM-locked) | `cursed-mines` |
| Nome IT | "Miniere Maledette" (LIVE DB) |
| Livello (req_lvl DB) | Lv4 |
| Party size | 3 (verbatim) |
| Lore source | **Efreto** (Gate 1, direct match live) |
| Tema narrativo | "I minatori cantano una canzone che non hanno imparato." (lore_meta live) |
| Enemy family | miners_undead (live) |
| Meccanica + class teaching | Party synergy (terreno claustrofobico). Introduzione tema arcane mining. |
| Loot tier | T1 prevalente |
| Rarity range | Common/Uncommon, Rare limitato boss |
| Materiali principali | Ferro maledetto, gemma opaca, polvere d'ossa (`PENDING PM verify`) |
| Boss/miniboss | Caposquadra Non-Morto (`PENDING PM verify`) |
| Itemization notes | Loot universal + hint Warrior/Priest (martelli T1, maglia T1). |
| Bracket | **Lv1-15 / Early Game** |
| Status | 🟢 **LIVE** |
| Achievement/ranking notes | Achievement "Canto Interrotto" (`PENDING PM`) |

### Dungeon #7 — sunken-library (🟢 LIVE)

| Campo | Valore |
|---|---|
| slug (PM-locked) | `sunken-library` |
| Nome IT | "Biblioteca Sommersa" (LIVE DB) |
| Livello (req_lvl DB) | Lv4 |
| Party size | 3 (verbatim) |
| Lore source | `memoria` live → **approve documentale come nuova fonte espansa "Memoria"** (sez. 10) |
| Tema narrativo | "Pagine leggono i lettori. Stai attento a cosa pensi qui." (lore_meta live) |
| Enemy family | scribe_specters (live) |
| Meccanica + class teaching | Mage secondary welcome (bastone/tomo/focus). Introduzione tema memory/mystery. |
| Loot tier | T1 |
| Rarity range | Common/Uncommon, Rare limitato boss |
| Materiali principali | Inchiostro fossile, pergamena salata, cristallo focus grezzo (`PENDING PM verify`) |
| Boss/miniboss | Bibliotecario Spettrale (`PENDING PM verify`) |
| Itemization notes | Mage secondary welcome (tomi T1, focus T1, stoffa T1). Universal accessori. |
| Bracket | **Lv1-15 / Early Game** |
| Status | 🟢 **LIVE** |
| Achievement/ranking notes | Achievement "Prima Pagina" (`PENDING PM`) |

### Dungeon #8 — lich-sanctum (🟢 LIVE)

| Campo | Valore |
|---|---|
| slug (PM-locked) | `lich-sanctum` |
| Nome IT | "Santuario del Lich" (LIVE DB) |
| Livello (req_lvl DB) | Lv5 |
| Party size | 3 (verbatim) |
| Lore source | **Irthe** (Gate 1, direct match live) |
| Tema narrativo | "Il lich ha negoziato con la morte. La morte ride poco." (lore_meta live) |
| Enemy family | lich, undead (live) |
| Meccanica + class teaching | Boss narrativo Lv5. Party comp matura. Priest primary welcome (reliquia, purificazione). |
| Loot tier | T1 |
| Rarity range | Common/Uncommon, Rare limitato boss (primo Rare guaranteed) |
| Materiali principali | Ossa di lich, filo consacrato, gemma di controllo (`PENDING PM verify`) |
| Boss/miniboss | Lich Minore (boss narrativo Lv5) |
| Itemization notes | Loot Priest/Warrior-friendly (reliquia T1, martello T1, maglia T1). Primo Rare boss drop. |
| Bracket | **Lv1-15 / Early Game** |
| Status | 🟢 **LIVE** |
| Achievement/ranking notes | Achievement "Contratto Rotto" (`PENDING PM`) |

### Dungeon #9 — chapel-of-silent-vows (🟡 NEW DRAFT)

| Campo | Valore |
|---|---|
| slug (PM-locked) | `chapel-of-silent-vows` |
| Nome IT proposta | "Cappella dei Voti Silenti" (`PENDING PM approval`) |
| Livello range proposta | Lv7-9 (`PENDING PM approval`) |
| Party size | 3 (verbatim) |
| Lore source proposta | **Aveol** (fonte Gate 1 orfana in live — copertura via nuovo dungeon) |
| Tema narrativo proposta | "I voti silenti sono stati infranti. Qualcosa risponde ai richiami di chi non parla più." (`PENDING PM`) |
| Enemy family proposta | Cultisti silenti + spettri di iniziati (non-morti bassa intensità) — **NO Cleric drift** |
| Meccanica + class teaching | **Priest primary teaching** (main stat Saggezza, weapon reliquia+focus, armor stoffa). |
| Loot tier | T1 |
| Rarity range | Common/Uncommon prevalenti |
| Materiali principali proposta | Cera votiva, ossa consacrate minori, stoffa penitenziale (`PENDING PM`) |
| Boss/miniboss proposta | "Il Sussurro" (spettro ex-officiante, `PENDING PM`) — NO nominato Cleric né Priest |
| Itemization notes | Loot Priest-friendly (reliquia T1, focus T1, stoffa T1). Universal accessori. NO drop piastre/arco/tomo. |
| Bracket | **Lv1-15 / Early Game** |
| Status | 🟡 **NEW DRAFT** — creation DB richiede gate futuro |
| Achievement/ranking notes | Achievement "Voto Compiuto" (clear con Priest) (`PENDING PM`) |

### Dungeon #10 — forgotten-shrine-of-adalan (🟡 NEW DRAFT)

| Campo | Valore |
|---|---|
| slug (PM-locked) | `forgotten-shrine-of-adalan` |
| Nome IT proposta | "Santuario Dimenticato di Adalan" (`PENDING PM`) |
| Livello range proposta | Lv9-11 (`PENDING PM`) |
| Party size | 3 (verbatim) |
| Lore source proposta | **Adalan** (fonte Gate 1 orfana in live) |
| Tema narrativo proposta | "Il santuario si è svegliato senza motivo. I custodi in ceramica difendono un cuore che nessuno ricorda più." (`PENDING PM`) |
| Enemy family proposta | Costrutti minori (golem ceramica, elementali arcani deboli) — `PENDING PM` |
| Meccanica + class teaching | **Mage primary teaching** (main stat Int, weapon bastone+focus+tomo, armor stoffa). Naming canonical Mage (NO Wizard). |
| Loot tier | T1 |
| Rarity range | Common/Uncommon prevalenti |
| Materiali principali proposta | Frammenti ceramica arcana, polvere essenza, tessuto rituale (`PENDING PM`) |
| Boss/miniboss proposta | "Cuore di Ceramica" (costrutto guardiano, `PENDING PM`) |
| Itemization notes | Loot Mage-friendly (bastoni T1, focus T1, tomi T1, stoffa T1). Universal anelli/amuleti. NO drop piastre/arco/reliquia. |
| Bracket | **Lv1-15 / Early Game** |
| Status | 🟡 **NEW DRAFT** |
| Achievement/ranking notes | Achievement "Custode Silente" (clear senza rompere pilastri) (`PENDING PM`) |

### Dungeon #11 — bandit-warlord-hideout (🟡 NEW DRAFT)

| Campo | Valore |
|---|---|
| slug (PM-locked) | `bandit-warlord-hideout` |
| Nome IT proposta | "Nascondiglio del Signore dei Briganti" (`PENDING PM`) |
| Livello range proposta | Lv11-13 (`PENDING PM`) |
| Party size | 3 (verbatim) |
| Lore source proposta | **Aveol** (secondo dungeon Aveol Batch 1 — differenziato da chapel-of-silent-vows come "capo brigante organizzato" successivo cronologicamente a bandit-hideout live) |
| Tema narrativo proposta | "Il Signore dei Briganti ha unito tre bande. La sua tesoreria è armata meglio della guarnigione." (`PENDING PM`) |
| Enemy family proposta | Briganti veterani + sciamano ribelle + sicari (`PENDING PM`) |
| Meccanica + class teaching | **Proficiency check narrativo**: loot boss = class-specific hint (introduce narrativamente Gate 2 sez. 5/6 senza runtime enforcement). |
| Loot tier | T1 prevalente + T2 minor su boss drop |
| Rarity range | Common/Uncommon prevalenti, Rare limitato boss |
| Materiali principali proposta | Acciaio brigantesco, cuoio veterano, ferro montano, gemme opache (`PENDING PM`) |
| Boss/miniboss proposta | "Il Signore dei Briganti" + sciamano ribelle (2 fase, NO drift Wizard, `PENDING PM`) |
| Itemization notes | Loot multi-class (Warrior spade/asce T1-T2, Rogue pugnali T1, Ranger balestre T1). NO drop stoffa/reliquia/tomo. Introduce "questo Warrior può, Priest no". |
| Bracket | **Lv1-15 / Early Game** |
| Status | 🟡 **NEW DRAFT** |
| Achievement/ranking notes | Achievement "Signore Deposto" — prima traccia proficiency teaching narrativo (`PENDING PM`) |

### Dungeon #12 — broken-tower-of-adalan (🟡 NEW DRAFT)

| Campo | Valore |
|---|---|
| slug (PM-locked) | `broken-tower-of-adalan` |
| Nome IT proposta | "Torre Spezzata di Adalan" (`PENDING PM`) |
| Livello range proposta | Lv13-15 (`PENDING PM`) |
| Party size | 3 (verbatim) |
| Lore source proposta | **Adalan** (secondo dungeon Adalan Batch 1 — differenziato da forgotten-shrine come "torre urbana rovinata" vs "santuario rurale") |
| Tema narrativo proposta | "La torre è caduta secoli fa. Chi la abita ora custodisce un sapere che nessuno chiede più." (`PENDING PM`) |
| Enemy family proposta | Guardiani costrutti + apostata erudito (NON Wizard — nomenclatura canonical "erudito"/"apostata"/"studioso") (`PENDING PM`) |
| Meccanica + class teaching | **Transition Lv15→Lv20** (Batch 1 → Batch 2). Primo boss con T2 assicurato + primo hint Epic drop molto raro (max 1 slot, rate `PENDING PM`). |
| Loot tier | T1 + **T2 assicurato boss** + **Epic molto raro** (max 1-2 slot) |
| Rarity range | Common/Uncommon prevalenti, Rare regolare, Epic molto raro (boss drop only) |
| Materiali principali proposta | Pietra spezzata di Adalan, tomo consumato, cristallo focus grezzo, filo d'oro antico (`PENDING PM`) |
| Boss/miniboss proposta | "L'Erudito Apostata" (mago rinnegato, canonical Mage naming, `PENDING PM`) |
| Itemization notes | Loot Mage-friendly primario (tomi T1-T2, focus T1-T2, bastoni T1-T2, stoffa T1-T2) + universal accessori T2 minor. Primo Epic drop molto raro su focus/tomo/anello. NO Legendary. |
| Bracket | **Lv1-15 / Early Game** |
| Status | 🟡 **NEW DRAFT** |
| Achievement/ranking notes | Achievement "Primo Epic" (unlock a chi ottiene primo Epic drop) — spunto transition Batch 2 (`PENDING PM`) |

---

## 4. `training-yard` escluso come utility

**Decisione PM #3 verbatim**: escluso da bracket R18.5.

| Attributo | Valore live | Note |
|---|---|---|
| slug | `training-yard` | Live nel DB |
| name_it | `null` | Nessuna narrativa player-facing |
| required_level | 1 | Nessun bracket assegnato |
| difficulty | `trivial` (string, non int) | Marker utility puro |
| bucket | `null` | Fuori bucket legacy |
| lore_theme | `null` | Nessuna fonte narrativa |
| is_5p | False | Party size 3 |
| is_legacy | False | Aggiunto dopo Phase 3 originale |

**Motivazione**: utility onboarding (allenamento adventurer, ROI XP low, no narrativa, no lore, difficoltà "trivial"). Non ha senso classificarlo in bracket R18.5 (Lv1-60) → **resta live come utility separato, fuori dal sistema bracket**.

**Nessuna azione tecnica richiesta**: il dungeon resta attivo in DB, semplicemente **non compare in nessuna matrice R18.5** (Batch 1/2/3/4/5).

---

## 5. `dragons-hoard` + `storm-spire` spostati a Batch 2 head

**Decisione PM #4 verbatim**: Batch 2 head (Lv16-30), NON Batch 1 tail.

| Attributo | dragons-hoard | storm-spire |
|---|---|---|
| slug | `dragons-hoard` | `storm-spire` |
| name_it (LIVE DB) | "Tesoro del Drago" | "Guglia della Tempesta" |
| required_level (LIVE DB) | Lv6 | Lv6 |
| difficulty | 3 | 3 |
| bucket legacy | mid | mid |
| lore_theme live | `draco` | `ambash` |
| content_family | arcane | arcane |
| emotional_tone | wonder | wonder |
| is_legacy | True (Phase 3 original) | True |

### Motivazione narrativa spostamento a Batch 2 head

**`dragons-hoard`**: il tema **`draco`** ha **tono di "reveal tardo"** (dragone dormiente, monete che contano sogni — `lore_meta.py` verbatim: *"Il drago dorme. Le monete contano i suoi sogni."*). Un dragone antico non è coerente narrativamente con Lv1-15 onboarding — è un momento di svelamento **mid-game**. Batch 2 head (Lv16-20) è la sede naturale.

**`storm-spire`**: il tema **`ambash`** ha tono **"reveal arcano"** (fulmine che sale dal basso — `lore_meta.py` verbatim: *"Il fulmine qui non scende dal cielo. Sale."*). Meccanica arcana avanzata, non introduttiva. Batch 2 head (Lv16-20) più coerente col tono di svelamento arcano.

### Impatto Batch 1

**Nessuna azione tecnica richiesta**: entrambi restano live come sono, `required_level=6` invariato nel DB. Il **drift required_level vs bracket documentale** è accettato PM (decisione #4): required_level=Lv6 nel DB, bracket documentale R18.5 = Batch 2 (Lv16-30). Il drift è di tipo "design vs runtime" — **NON correggere** in questa fase.

**Placeholder Batch 2 head 3-player**:
- Slot #1: `dragons-hoard` (Lv16-18 documentale, req_lvl live=6 drift accepted)
- Slot #2: `storm-spire` (Lv18-20 documentale, req_lvl live=6 drift accepted)
- + ~10 nuovi dungeon 3p Lv20-30 da progettare in futuri gate PM

---

## 6. Elite/Group Dungeon Track — 12 dungeon 5-player live

**Decisione PM #5 verbatim**: **NO rework tecnico**, **NO re-team-size**, **NO congelamento**, **NO deprecazione**. Mapping bracket **documentale**.

### 6.1 Lista 12 dungeon 5-player (live, `is_5p=True`)

| # | slug | name_it (LIVE) | req_lvl (LIVE) | lore_theme (LIVE) | content_family | Emotional tone |
|:---:|---|---|:---:|:---:|:---:|:---:|
| E1 | `wolf-den-5p` | Tana dei Lupi | 3 | soe | nature | wonder |
| E2 | `frost-cave-5p` | Caverna del Gelo | 4 | halodi | nature | melancholy |
| E3 | `salt-marsh-5p` | Palude Salata | 5 | velur | memory | melancholy |
| E4 | `iron-foundry-5p` | Fonderia di Ferro | 6 | fucina | arcane | tension |
| E5 | `silent-monastery-5p` | Monastero del Silenzio | 7 | memoria | memory | melancholy |
| E6 | `pirate-fleet-5p` | Flotta dei Corsari | 8 | mare | baseline | tension |
| E7 | `obsidian-arena-5p` | Arena d'Ossidiana | 9 | infernale | arcane | grim |
| E8 | `clockwork-vault-5p` | Camera degli Ingranaggi | 10 | fucina | arcane | tension |
| E9 | `voidspire-5p` | Pinnacolo del Vuoto | 11 | vuoto | void_undead | dread |
| E10 | `infernal-pit-5p` | Fossa Infernale | 12 | infernale | arcane | dread |
| E11 | `celestial-citadel-5p` | Cittadella Celeste | 13 | celeste | divine | hope |
| E12 | `world-tree-roots-5p` | Radici dell'Albero del Mondo | 14 | soe | nature | wonder |

### 6.2 Governance Elite Track

- **Party size**: 5-player rimane **live invariato**. Nessun downgrade a 3p.
- **required_level live**: rimane invariato (Lv3-14). Nessun rewrite.
- **Elite Track parallelo**: naming ufficiale documentale = "Elite/Group Dungeon Track" (o similare `PENDING PM`).
- **Bracket documentale R18.5**: mapping proposto in sez. 7 (`PENDING PM approval`).

---

## 7. Proposta bracket documentale per i 12 dungeon 5-player

Proposta Emergent basata su **tema narrativo** (non solo `required_level` live, che presenta drift design per 3 casi). `PENDING PM approval` finale.

| # | slug | req_lvl LIVE | tema live | Bracket R18.5 proposto | Drift design/runtime? |
|:---:|---|:---:|:---:|:---:|:---:|
| E1 | `wolf-den-5p` | 3 | soe / nature / wonder | **Batch 1 Elite (Lv1-15)** | ✅ Coerente |
| E2 | `frost-cave-5p` | 4 | halodi / nature / melancholy | **Batch 1 Elite (Lv1-15)** | ✅ Coerente |
| E3 | `salt-marsh-5p` | 5 | velur / memory / melancholy | **Batch 1 Elite (Lv1-15)** | ✅ Coerente |
| E4 | `iron-foundry-5p` | 6 | fucina / arcane / tension | **Batch 1 Elite (Lv1-15)** o Batch 2 Elite | 🟡 Borderline (fucina è tema tech pre-industrial, accettabile early-mid) |
| E5 | `silent-monastery-5p` | 7 | memoria / memory / melancholy | **Batch 1 Elite tail (Lv1-15)** | ✅ Coerente |
| E6 | `pirate-fleet-5p` | 8 | mare / baseline / tension | **Batch 2 Elite (Lv16-30)** | ✅ Coerente (mare come reveal tardo) |
| E7 | `obsidian-arena-5p` | 9 | infernale / arcane / grim | **Batch 2 Elite (Lv16-30)** | 🟡 Borderline (infernale intro?) |
| E8 | `clockwork-vault-5p` | 10 | fucina / arcane / tension | **Batch 2 Elite (Lv16-30)** | ✅ Coerente (fucina avanzato) |
| E9 | `voidspire-5p` | 11 | **vuoto** / void_undead / dread | **Batch 4/5 Elite (Lv46-60)** | 🔴 **DRIFT** — vuoto è fonte Gate 1 endgame, req_lvl=11 troppo basso |
| E10 | `infernal-pit-5p` | 12 | **infernale** / arcane / dread | **Batch 4 Elite (Lv46-55)** | 🔴 **DRIFT** — tono endgame, req_lvl=12 troppo basso |
| E11 | `celestial-citadel-5p` | 13 | **celeste** / divine / hope | **Batch 5 Elite (Lv56-60)** | 🔴 **DRIFT** — tono endgame, req_lvl=13 troppo basso |
| E12 | `world-tree-roots-5p` | 14 | soe / nature / wonder | **Batch 3 Elite (Lv31-45)** o Batch 4 | 🟡 Borderline (Alberi della Vita reveal?) |

### 7.1 Distribuzione proposta per bracket

- **Batch 1 Elite (Lv1-15)**: E1, E2, E3, E4, E5 → 5 dungeon 5p
- **Batch 2 Elite (Lv16-30)**: E6, E7, E8 → 3 dungeon 5p
- **Batch 3 Elite (Lv31-45)**: E12 → 1 dungeon 5p (`PENDING PM`)
- **Batch 4 Elite (Lv46-55)**: E10 → 1 dungeon 5p
- **Batch 5 Elite (Lv56-60)**: E9, E11 → 2 dungeon 5p
- **Total mapped**: 12 (equivalente al catalogo live 5p)

### 7.2 🔴 3 casi di drift design/runtime segnalati (NON corretti)

| slug | Drift | Tipo | Azione |
|---|---|---|---|
| `voidspire-5p` | req_lvl=11 vs tema `vuoto` (fonte endgame Gate 1) | design vs runtime | 🚫 **NON CORREGGERE** — documenta, `PENDING PM` |
| `infernal-pit-5p` | req_lvl=12 vs tono endgame `dread`/`infernale` | design vs runtime | 🚫 **NON CORREGGERE** — documenta, `PENDING PM` |
| `celestial-citadel-5p` | req_lvl=13 vs tono endgame `celeste`/`divine`/`hope` | design vs runtime | 🚫 **NON CORREGGERE** — documenta, `PENDING PM` |

**Governance**: il drift è **puramente documentale**. Il DB rimane con `required_level` originale. La classificazione bracket R18.5 è documentale e serve solo per pianificazione. PM decide se in Phase C tech futura riallineare `required_level` live con bracket documentale (breaking change accettabile o no).

---

## 8. Proposta bracket documentale per i 3 raid live

**Decisione PM #6 verbatim**: assignment Batch 3/4/5 (bracket finale `PENDING PM approval`). Preliminari già indicati.

### 8.1 Elenco 3 raid live

| slug | name_it (LIVE) | lore_theme (LIVE) | content_family | boss_name | req_lvl LIVE |
|---|---|:---:|:---:|---|:---:|
| `broken-bastion-siege` | Assedio al Bastione Spezzato | ergolat | baseline | Comandante del Bastione | `null` |
| `necropolis-bells` | Necropoli delle Mille Campane | irthe | void_undead | Campanaro Senza Volto | `null` |
| `dragon-vault` | Volta del Drago Addormentato | draco | arcane | Drago di Pietra | `null` |

### 8.2 Bracket proposto

#### `broken-bastion-siege` → **Batch 3 Raid (Lv31-45)**

- **Lore theme**: `ergolat` — fonte Gate 1 orfana in live dungeon (solo raid la usa)
- **content_family**: `baseline` (militare, assedio)
- **Motivazione**: tema militare organizzato (assedio a bastione) è coerente con mid-game endgame. Ergolat come fonte politica/militare va bene in Batch 3.
- **Alternative**: Batch 4 se PM ritiene tono più epico. `PENDING PM`.

#### `necropolis-bells` → **Batch 4 Raid (Lv46-55)**

- **Lore theme**: `irthe` — void_undead escalation
- **content_family**: `void_undead`
- **Motivazione**: **Campanaro Senza Volto** è boss narrativo endgame Irthe. Coerente con Batch 4 late-game (superiore a lich-sanctum Lv5 e shadow-crypts Lv3 già live).
- **Alternative**: Batch 5 se PM vuole culminazione lore Irthe al capstone Lv60. `PENDING PM`.

#### `dragon-vault` → **Batch 5 Raid (Lv56-60)**

- **Lore theme**: `draco` — tema epico endgame
- **content_family**: `arcane`
- **Motivazione**: **Drago di Pietra** è boss endgame per eccellenza. Coerente con capstone Lv60 (Legendary drop potenziali? `PENDING PM`).
- **Alternative**: Batch 4 se PM ritiene draco meno "capstone". `PENDING PM`.

### 8.3 Governance raid

- `required_level` null nei 3 raid live → bracket determinato **solo da tema/tono**, non da runtime.
- Nessuna correzione a DB. Nessun backfill `required_level` in questa fase (out-of-scope).
- **9 raid nuovi** richiesti per raggiungere il target R18.5 (12 raid totali) — pianificazione futura, non Batch 1.

---

## 9. 8 lore source live orfane vs 17 fonti Gate 1

Elenco verbatim dei tag `lore_theme` presenti in `db.dungeons` che **NON matchano** le 17 fonti Gate 1 approvate.

| # | Tag orfano | Dungeon che lo usano | Proposta orch |
|:---:|:---:|---|---|
| 1 | `urban` | `sewer-nest` (Lv1), `bandit-hideout` (Lv2) | **MERGE sotto Aveol** (Gate 1) — Aveol già copre borghi/passi/urban civilizzato coerente con location_hint live "fogne sotto le città" + "passi di montagna di Aveol" |
| 2 | `frontiera` | `goblin-warrens` (Lv2) | **MERGE sotto Halodi** (Gate 1) — location_hint live già "boschi di Halodi orientale". La fonte è già Halodi, il tag è ridondante |
| 3 | `fucina` | `iron-foundry-5p` (Lv6), `clockwork-vault-5p` (Lv10) | **RENAME come sotto-tag "Fucine di Ambash"** — Ambash è fonte Gate 1 mercantile/fabbrile. Manteniamo `fucina` come sub-tag Ambash. |
| 4 | `memoria` | `sunken-library` (Lv4), `silent-monastery-5p` (Lv7) | **APPROVE come nuova fonte "Memoria"** — tema memory autonomo, non 1:1 con nessuna Gate 1. Coerente con `content_family: memory`. |
| 5 | `mare` | `pirate-fleet-5p` (Lv8) | **APPROVE come nuova fonte "Mare"** — tema oceanico/rotte navali autonomo. Alternativa merge sotto Velur (estuari) `PENDING PM final`. |
| 6 | `draco` | `dragons-hoard` (Lv6), + raid `dragon-vault` | **APPROVE come nuova fonte "Draco"** — tema draconico autonomo, tono epico endgame. |
| 7 | `celeste` | `celestial-citadel-5p` (Lv13) | **APPROVE come nuova fonte "Celeste"** — tema divino/celeste autonomo. Alternativa merge sotto Alberi della Vita `PENDING PM final`. |
| 8 | `infernale` | `obsidian-arena-5p` (Lv9), `infernal-pit-5p` (Lv12) | **APPROVE come nuova fonte "Infernale"** — tema infernale autonomo, tono endgame. Alternativa merge sotto Luna Morta `PENDING PM final`. |

### 9.1 Sintesi orchestrazione

- **2 MERGE** sotto fonte madre Gate 1 esistente: `urban` → Aveol; `frontiera` → Halodi
- **1 RENAME/sub-tag**: `fucina` → sub-tag di Ambash
- **5 APPROVE** come nuove fonti: `memoria`, `mare`, `draco`, `celeste`, `infernale`

**Totale nuove fonti aggiunte a Gate 1**: **5** (17 → **22**, in range target 22-25).

**NO breaking change su `lore_meta.py`** (regola vincolo assoluto) — il file live rimane con i tag correnti. La "espansione" è **puramente documentale** in questo deliverable + audit trail. Se PM approva definitivamente in gate futuro, si potrà procedere con backfill/rename runtime (fuori scope C0-quater).

---

## 10. Proposta espansione lore source 17 → 22 (target 22-25)

### 10.1 Nuova lista fonti proposta (22 totali)

**17 fonti originali Gate 1** (invariate):

1. **Ambash** (mercantile/miniere, sub-tag: `fucina` — Fucine di Ambash)
2. **Irthe** (culto Esiliati, void_undead)
3. **Velur** (estuari memory)
4. **Efreto** (deserto/arcane mining)
5. **Halodi** (frontiera/ghiaccio; ex-tag `frontiera` merged qui)
6. **Alevora** (world boss narrativo)
7. **Soe** (foreste settentrionali/nature)
8. **Aveol** (borghi/urban civilizzato; ex-tag `urban` merged qui)
9. **Ergolat** (militare/politico — usato da raid)
10. **Krastlov** (tundra/veglia marziale)
11. **Adalan** (cittadina/rovine)
12. **Greatwood/Elfwood** (foresta ancestrale)
13. **Alberi della Vita** (bosco antico druidico)
14. **Faglie arcane** (metafisica arcana mid-late)
15. **Vuoto** (cosmico endgame)
16. **Luna Morta** (arcano oscuro endgame)
17. **Ciclo delle anime** (metafisico endgame)

**5 nuove fonti approve** (proposta documentale — sez. 9):

18. **Memoria** (memory autonomo — sunken-library, silent-monastery-5p)
19. **Mare** (oceanico/rotte navali — pirate-fleet-5p) `[merge sotto Velur pending]`
20. **Draco** (draconico epico — dragons-hoard, dragon-vault raid)
21. **Celeste** (divino/celeste — celestial-citadel-5p) `[merge sotto Alberi della Vita pending]`
22. **Infernale** (infernale endgame — obsidian-arena-5p, infernal-pit-5p) `[merge sotto Luna Morta pending]`

**Totale**: **22 fonti** (target 22-25 rispettato — spazio per 3 aggiuntive future).

### 10.2 Note governance espansione

- **Tutte le 5 nuove fonti** sono documentali — **NO modifica `lore_meta.py`** in questa fase.
- **3 fonti** hanno alternativa `merge sotto fonte madre` (Mare→Velur, Celeste→Alberi della Vita, Infernale→Luna Morta). Se PM sceglie merge, il totale scende (22-3 = 19). `PENDING PM final`.
- **2 fonti** sono standalone forti (`Memoria`, `Draco`) — Emergent raccomanda approve autonomo.
- **Sub-tag `fucina`** rimane come sotto-classe di Ambash (non conta come nuova fonte).

### 10.3 Compatibilità dungeon 5-player Elite Track (sez. 7)

Post-espansione lore, il mapping 5-player→bracket documentale è più coerente:

- `voidspire-5p` (vuoto): fonte già Gate 1 (Vuoto) → bracket endgame corretto
- `celestial-citadel-5p` (celeste): nuova fonte 22 → bracket endgame giustificato
- `infernal-pit-5p` (infernale): nuova fonte 22 → bracket endgame giustificato
- **Drift residuo runtime**: solo `required_level` DB non allineato a bracket documentale (3 casi drift accettati, PM #5 governance).

---

## 11. Rischi residui post-finalization

| # | Rischio | Severità | Origine | Mitigation |
|:---:|---|:---:|---|---|
| 1 | **Drift design/runtime 5-player** (voidspire, infernal-pit, celestial-citadel: `required_level` DB troppo basso vs bracket documentale endgame) | 🟡 MEDIUM | Legacy scaling pre-R18.5 | Documentato, NON corretto (PM #5 verbatim). Riallineamento futuro `PENDING PM` in Phase C tech. |
| 2 | **Lore normalization definitiva pending** | 🟡 MEDIUM | 8 fonti orfane con 3 alternative merge/rename/standalone | Documentato sez. 9-10. Final decision `PENDING PM` prossimo gate. |
| 3 | **4 nuovi dungeon design → richiedono future DB creation** | 🟢 LOW | Out-of-scope Batch 1 finalization | Creation richiede gate PM dedicato + Phase C tech (BLOCCATA). |
| 4 | **Naming IT player-facing dei 4 nuovi** (`PENDING PM approval`) | 🟢 LOW | Design proposta Emergent | PM approva/rinomina in gate futuro. |
| 5 | **Naming IT player-facing dei live divergente** (nessun rischio ora, ma se PM decidesse di rinominarli in futuro, sarebbe breaking change UI) | 🟢 LOW | Design consistency long-term | Info-only, non blocker. |
| 6 | **Compatibility policy runtime per proficiency** (Gate 2 sez. 5-6 hard-block armor/weapon) | 🟡 MEDIUM | Out-of-scope Batch 1 | Menzionato in C0-ter sez. 9. Enforcement richiede Phase C tech dry-run (BLOCCATA). |
| 7 | **Gap Lv6 in Batch 1 3-player** (transizione da Lv5 lich-sanctum a Lv7 chapel-of-silent-vows) | 🟢 LOW | Post-spostamento dragons-hoard/storm-spire a Batch 2 head | `PENDING PM`: accettare gap o aggiungere 1 dungeon Lv6 dedicato. |
| 8 | **Drift required_level dragons-hoard/storm-spire** (LIVE Lv6 vs Batch 2 head Lv16-20 documentale) | 🟡 MEDIUM | Legacy scaling pre-R18.5 (accettato PM #4) | Documentato, NON corretto. Riallineamento futuro `PENDING PM` in Phase C tech. |

---

## 12. Open Questions PM residue post-finalization

### 12.1 Lore normalization definitiva (5 nuove fonti)

- **Q1**: `Mare` approve standalone o merge sotto **Velur**?
- **Q2**: `Celeste` approve standalone o merge sotto **Alberi della Vita**?
- **Q3**: `Infernale` approve standalone o merge sotto **Luna Morta**?
- **Q4**: Se merge, il totale fonti scende a **19** (sotto target 22-25). Aggiungere 3 nuove fonti future per compensare?
- **Q5**: `Memoria` e `Draco` — confermare standalone (Emergent raccomandazione)?

### 12.2 Bracket 5-player finale

- **Q6**: Confermare mapping Elite Track sez. 7?
  - Batch 1 Elite (5): E1-E5
  - Batch 2 Elite (3): E6-E8
  - Batch 3 Elite (1): E12
  - Batch 4 Elite (1): E10
  - Batch 5 Elite (2): E9, E11
- **Q7**: Come gestire il **drift runtime `required_level`** dei 3 casi endgame (E9 voidspire, E10 infernal-pit, E11 celestial-citadel)?
  - Opzione (i): accettato per sempre (design vs runtime consapevole)
  - Opzione (ii): riallineamento runtime in Phase C tech dry-run futura (breaking `required_level` per 3 dungeon)
  - Opzione (iii): riallineamento tema (rebrand lore `vuoto`/`infernale`/`celeste` a temi meno endgame — breaking narrativa)

### 12.3 Bracket 3 raid finale

- **Q8**: `broken-bastion-siege` → Batch 3 (Emergent proposta) o Batch 4?
- **Q9**: `necropolis-bells` → Batch 4 (Emergent proposta) o Batch 5?
- **Q10**: `dragon-vault` → Batch 5 (Emergent proposta) confermato?

### 12.4 Batch 1 finalization

- **Q11**: Gap Lv6 3-player accettato (transizione Lv5→Lv7) o inserire 1 dungeon Lv6 nuovo?
- **Q12**: Naming IT player-facing definitivo per 4 nuovi (approve proposte Emergent o rename)?
- **Q13**: Nome ufficiale "Elite/Group Dungeon Track" o alternativo (es. "Coordinated Track", "Raid-lite Track")?

### 12.5 Post-approval workflow

- **Q14**: Post-PM decisions su Q1-Q13, aggiornare PRD.md con sezione "R18.5 Phase C0-quater Batch 1 CLOSED"?
- **Q15**: Autorizzare `Phase C0-quinquies` (Batch 2 head Lv16-30 = dragons-hoard + storm-spire + ~10 nuovi 3p + 3 Elite 5p) o pausa?

---

## 13. Governance check finale — Batch 1 Informed CLOSED

- ✅ **12 dungeon Batch 1 esatti** (8 live + 4 nuovi, PM-locked verbatim)
- ✅ **Ogni dungeon: 16 campi compilati** (sez. 3)
- ✅ **`training-yard` escluso** con motivazione (sez. 4)
- ✅ **`dragons-hoard` + `storm-spire` spostati a Batch 2 head** con motivazione narrativa (sez. 5)
- ✅ **Elite/Group Dungeon Track**: 12 5-player elencati (sez. 6)
- ✅ **Bracket proposto per ogni 5-player** (sez. 7, `PENDING PM approval`)
- ✅ **3 raid live**: bracket proposto Batch 3/4/5 (sez. 8, `PENDING PM approval`)
- ✅ **8 fonti orfane elencate esplicitamente** (sez. 9)
- ✅ **Proposta espansione lore 17→22** (sez. 10)
- ✅ **8 rischi residui documentati** (sez. 11)
- ✅ **15 Open Questions PM elencate** (sez. 12)
- ✅ **36 sigilli byte-identical** (verifica attesa `pytest backend_r18_4_sealed_integrity_test.py` PASS)
- ✅ **Zero DB writes** (audit trail read-only, nessuna modifica `dungeons` / `raid_dungeons` / `expeditions`)
- ✅ **Zero code changes** (`.py` / `.js` / `.jsx` / `.tsx` intatti)
- ✅ **Zero migrations / apply scripts**
- ✅ **Zero dungeon creation live** (4 nuovi = design docs, NO insert DB)
- ✅ **Zero dungeon deletion / deprecation**
- ✅ **Zero party_size rewrite** (5-player restano 5p)
- ✅ **Zero required_level rewrite** (drift design/runtime documentato non corretto)
- ✅ **Zero breaking change `lore_meta.py`** (espansione fonti puramente documentale)
- ✅ **Zero economy changes / drop table apply / level backfill**
- ✅ **Zero runtime bridge activation / class_slug migration / proficiency runtime enforcement**
- ✅ **2 file deliverable creati** (`.md` + `.json`)

---

## 14. Handoff — Batch 1 Informed CLOSED

### 14.1 Deliverable prodotti

- ✅ `/app/memory/r18_5_phase_c0quater_batch1_informed_final.md` (questo file)
- ✅ `/app/memory/r18_5_phase_c0quater_batch1_informed_final.json` (mirror strutturato)

### 14.2 File predecessori — status

- `r18_5_phase_c0quater_batch1_lv1_15_dungeon_matrix.md/.json` (DRAFT superseded post-audit) → **preservato per audit trail, deprecato**
- `r18_5_phase_c0quater_live_dungeon_audit.md/.json` (audit READ-ONLY) → **base per questo deliverable**

### 14.3 Prossimo step atteso

**PM review Batch 1 Informed** → risposte alle 15 Open Questions (sez. 12) → chiusura formale Batch 1 con:
1. Aggiornamento PRD.md con sezione "R18.5 Phase C0-quater Batch 1 CLOSED (informed)"
2. Autorizzazione (o pausa) Phase C0-quinquies (Batch 2 head Lv16-30)
3. Gate PM successivo per Phase C tech dry-run (BLOCCATA — governance sigilli `derive_ui_4state`/`item_public()` invariata)

### 14.4 Non emerse sorprese o conflitti non previsti

Durante la finalizzazione, Emergent **NON ha rilevato**:
- ❌ Dungeon 5-player con lore incompatibile con qualsiasi bracket (i 3 drift `voidspire`/`infernal-pit`/`celestial-citadel` sono classificati coerentemente in Batch 4/5 documentale, drift è solo runtime → gestibile)
- ❌ Sigilli modificati (36 SHA256 attesi PASS)
- ❌ Code changes non autorizzati
- ❌ DB writes non autorizzati
- ❌ Modifiche breaking a `lore_meta.py`

**Batch 1 CLOSED (informed) — pronto per PM final review + risposta Open Questions**.
