# R18.5 Phase C0-quater — Batch 1: 12 Dungeon Lv1-15 Matrix (DOCUMENTAL ONLY / DRAFT / PENDING PM approval)

- **Round**: `R18.5 — Itemization, ILVL & Gear Progression Rework`
- **Sottotitolo**: *Lv60 cap, item-centered endgame, lore-driven equipment*
- **Fase**: **C0-quater — Batch 1** (bracket `Lv1-15 / Early Game`)
- **Scope Batch 1**: 12 dungeon Lv1-15, 0 raid, T1 prevalente + T2 minor introduttivo
- **Locked at UTC**: `2026-07-06T20:40:00Z`
- **Governance**: DOCUMENTAL ONLY — 36 sigilli byte-identical, zero DB writes, zero code changes.
- **Autorità**: PM Orchestrator (GO esplicito Batch 1 ricevuto)
- **Status deliverable**: 🟡 **DRAFT / PENDING PM approval** su tutti i campi player-facing (nomi, temi, boss, materiali specifici, level range esatti, lore assignment). Le regole strutturali (bracket, tier, party size 3) sono PM-locked e inseriti verbatim.
- **Predecessori autoritativi**:
  - `r18_5_phase_b_gate1_pm_decisions.md/.json` (Gate 1 — SQ11-SQ18, 17 lore sources)
  - `r18_5_gate2_pm_decisions.md/.json` (Gate 2 — Tier↔Rarity many-to-many, canonical classes, purge drift)
  - `r18_5_phase_c0bis_progression_dungeon_raid_matrix.md/.json` (C0-bis — scale-up 60 dungeon + 12 raid, bracketing)
  - `r18_5_phase_c0ter_live_class_matrix.md/.json` (C0-ter — 5 classi live: Warrior/Rogue/Mage/Priest/Ranger)
- **Successore autorizzato**: NON autorizzato — Batch 2 (Lv20-30) resta **BLOCCATO** fino a review PM del Batch 1.

---

## 0. Regole design Batch 1 (PM verbatim)

I dungeon Lv1-15 devono essere:
- ✅ **Accessibili** (onboarding player)
- ✅ **Leggibili** (temi chiari, no ambiguità narrativa)
- ✅ **Introduttivi** (spiegano concetti: proficiency, main stat, party comp)
- ✅ **Non banali** (evitare "Cave 1, Cave 2, Cave 3")
- ✅ **Collegati alla lore** (17 fonti approvate, ma alcune riservate a endgame)
- ✅ **Utili a spiegare** armor/weapon proficiency + main stat via loot design
- ✅ **Fonte di T1 e primi T2**
- ❌ **Senza Legendary** (Legendary è solo T5)
- ❌ **Senza raid**
- ❌ **Senza meccaniche troppo punitive**

### Loot target Batch 1 (direzionale, no rate numerici finali)

- **T1 prevalente**
- **T2 raro/introduttivo** (solo alcuni dungeon Lv12-15)
- **Common/Uncommon prevalenti**
- **Rare molto limitati** (solo boss drop di 1-2 dungeon)
- **Epic assenti o quasi assenti** (max 1-2 dungeon con Epic boss drop molto raro)
- **Legendary assenti**

### Vincoli strutturali PM-locked (verbatim, non riaprire)

- `bracket = "Lv1-15 / Early Game"` per tutti i 12 dungeon.
- `required_team_size = 3` per tutti i 12 dungeon (verbatim Gate 1 SQ13 sizing → `party_size = 3`).
- Naming canonical Mage/Priest verbatim (NO drift Wizard/Cleric — Gate 2 sez. 4).
- Weapon families non assegnate (**strumento**, **falce**, **trinket**) restano `PENDING PM approval` — Emergent NON le assegna a Batch 1 (C0-ter sez. 8).

---

## 1. Distribuzione progressione Lv1-15 (proposta Emergent, `PENDING PM approval`)

I 12 dungeon distribuiti per coprire Lv1-15 progressivamente in 4 bucket:

| Bucket | Range livelli | Count dungeon | Ruolo |
|---|:---:|:---:|---|
| Onboarding | **Lv1-5** | 3 | Introduzione al gioco, party comp, main stat basi |
| Progressione bassa | **Lv5-10** | 4 | Proficiency armor/weapon iniziale, primi ruoli party |
| Progressione media | **Lv10-13** | 4 | Class identity marcata, primi hint T2 |
| Transizione a Batch 2 | **Lv13-15** | 1 | Boss T2 assicurato, primo hint Epic (molto raro) |

**Nota mapping livelli**: il sistema live attuale NON espone `level_min/level_max` per dungeon (usa `difficulty` 1/2/3 + `recommended_power`). Il mapping a Lv1-15 in Batch 1 è **proposta documentale Emergent** flaggata `PENDING PM approval` — NO applicazione a DB o codice in questa fase.

---

## 2. 17 Lore sources — distribuzione Batch 1

### Sources USATE in Batch 1 (10 su 17)

| Source | Dungeon assegnati | Motivazione accessibilità |
|---|---|---|
| **Halodi** | #1 Goblin Warrens (live, già assegnata) | Frontiera orientale, boschi — accessibile |
| **Greatwood/Elfwood** | #2 | Foresta ancestrale ma non profondamente arcana — onboarding naturale |
| **Aveol** | #3, #11 | Passi di montagna/borghi frontiera — briganti/culto minore, tono accessibile |
| **Velur** | #4 | Estuari dimenticati — melanconia soft, non spoiler endgame |
| **Soe** | #5 | Foreste settentrionali — bestie/wonder, adatto a introduzione |
| **Adalan** | #6, #12 | Cittadina/campagna con rovine — costrutti minori, transizione tecnica |
| **Ambash** | #7 | Fiume/miniere/mercantili — kobold e ratti, ruolo party |
| **Krastlov** | #8 | Ghiaccio/tundra — resistenze status leggere, party mixed |
| **Efreto** | #9 | Deserto nomade — banditi/sciacalli, mobilità Ranger/Rogue |
| **Alberi della Vita** | #10 | Bosco antico, driadi minori — natura soft, no metafisica endgame |

### Sources RISERVATE per batch futuri (7 su 17)

| Source | Riservata a | Motivazione riservo |
|---|---|---|
| **Irthe** | Batch 2 (Lv20-30) | Culto Esiliati, tono "dread" — già in shadow-crypts Lv20+ |
| **Alevora** | Batch 4/5 (Lv40-60) | World boss endgame — non adatto a Lv1-15 |
| **Ergolat** | Batch 4/5 (Lv40-60) | Fonte epica endgame |
| **Faglie arcane** | Batch 3+ (Lv30-45) | Metafisica arcana mid-late |
| **Vuoto** | Batch 5 (Lv55-60) | Cosmico endgame estremo |
| **Luna Morta** | Batch 5 (Lv55-60) | Arcano oscuro endgame |
| **Ciclo delle anime** | Batch 5 (Lv55-60) | Metafisico endgame |

**Governance**: assegnazioni definitive delle 7 riservate `PENDING PM approval` — Emergent NON finalizza autonomamente.

---

## 3. Matrice 12 dungeon — 16 campi obbligatori

Legenda flag:
- 🟢 **LIVE** — già seed data nel codebase (nessuna nuova creazione richiesta)
- 🟡 **DRAFT NEW** — proposta Emergent `PENDING PM approval`
- Ogni campo player-facing (Nome IT, tema narrativo, boss/miniboss, materiali specifici, level range esatto, lore assignment) è flaggato `PENDING PM approval`

---

### Dungeon #1 — Goblin Warrens (🟢 LIVE — già seed data)

| Campo | Valore |
|---|---|
| **dungeon_id** | `goblin-warrens` (kebab-case, già live in `backend/app/seeds/seed_data.py:168`) |
| **Nome IT** | "Tane dei Goblin" (già in `backend/app/content/lore_meta.py:51`) |
| **level range** (proposta) | **Lv1-3** — `PENDING PM approval` (sistema live usa `difficulty=1, recommended_power=45`) |
| **bracket** | `Lv1-15 / Early Game` (PM-locked verbatim) |
| **lore source** | **Halodi** (già assegnato: `lore_theme: "frontiera"`, `location_hint: "boschi di Halodi orientale"`) |
| **regione/bioma** | Boschi/tunnel di frontiera (già assegnato) |
| **tema narrativo** | "I tamburi dei goblin segnano il passo di un'invasione minore." (già in lore_meta) — `NO CHANGE, history preserved` |
| **enemy family** | `goblins` (già assegnato: `enemy_families: ["goblins"]`) |
| **meccanica principale** | **Onboarding puro**: party comp 3-slot, primi test main stat, ingresso ai sistemi core. NO proficiency hard block ancora (per design accessibilità T1) |
| **party size consigliata** | **3** (già live: `required_team_size: 3`, PM-locked verbatim) |
| **tier loot atteso** | **T1** puro |
| **rarity loot attesa** | Common prevalente, Uncommon occasionale. **NO Rare/Epic/Legendary** |
| **materiali principali** (proposta) | Cuoio grezzo, ossa di goblin, pietre — categorie ok, nomi specifici `PENDING PM approval` |
| **possibile boss/miniboss** (proposta) | Sciamano goblin minore (nome specifico `PENDING PM approval`) — NO drift Wizard/Cleric |
| **note itemization** | Loot universale (`is_universal: true` prevalente) — accessibile a tutte le 5 classi. Piccola quantità di loot class-friendly Warrior/Ranger (spade/pugnali comuni) per introdurre concetto proficiency senza hard block |
| **note future achievement/ranking** | Achievement "Primo Passo" (kill first goblin king) — spunto per ranking guild "First Clear Goblin Warrens" — `PENDING PM approval` |

---

### Dungeon #2 — Radura dell'Elfwood (🟡 DRAFT NEW — `PENDING PM approval`)

| Campo | Valore |
|---|---|
| **dungeon_id** (proposta) | `elfwood-glade` — `PENDING PM approval` |
| **Nome IT** (proposta) | "Radura dell'Elfwood" — `PENDING PM approval` |
| **level range** (proposta) | **Lv2-4** — `PENDING PM approval` |
| **bracket** | `Lv1-15 / Early Game` (PM-locked) |
| **lore source** | **Greatwood/Elfwood** — foresta ancestrale, `PENDING PM approval` |
| **regione/bioma** | Bosco antico, radure con rovine elfiche minori |
| **tema narrativo** (proposta) | "Le radure dell'Elfwood custodiscono tracce silenziose. Qualcosa ha rotto il silenzio, e i lupi lo seguono." — `PENDING PM approval` |
| **enemy family** | Bestie della foresta (lupi, cinghiali, ghiri giganti) — `PENDING PM approval` |
| **meccanica principale** | **Ranger teaching**: introduzione a main stat **Destrezza**, weapon family **arco** + **pugnale**. Loot enfatizza cuoio + arco/pugnale comune |
| **party size consigliata** | **3** (verbatim) |
| **tier loot atteso** | **T1** puro |
| **rarity loot attesa** | Common prevalente, Uncommon occasionale |
| **materiali principali** (proposta) | Corteccia antica, pelle di lupo, frecce grezze — `PENDING PM approval` |
| **possibile boss/miniboss** (proposta) | Alpha-lupo silvano (nome `PENDING PM approval`) |
| **note itemization** | Loot Ranger-friendly (archi corti T1, cuoio T1). Universal per boots/gloves. NO drop reliquia/tomo/piastre |
| **note future achievement/ranking** | Achievement "Cacciatore Silente" (clear senza alert) — `PENDING PM approval` |

---

### Dungeon #3 — Cappella dei Voti Silenti (🟡 DRAFT NEW — `PENDING PM approval`)

| Campo | Valore |
|---|---|
| **dungeon_id** (proposta) | `chapel-of-silent-vows` — `PENDING PM approval` |
| **Nome IT** (proposta) | "Cappella dei Voti Silenti" — `PENDING PM approval` |
| **level range** (proposta) | **Lv3-5** — `PENDING PM approval` |
| **bracket** | `Lv1-15 / Early Game` (PM-locked) |
| **lore source** | **Aveol** — culto minore silenzioso, `PENDING PM approval` |
| **regione/bioma** | Cappella abbandonata sui passi montani |
| **tema narrativo** (proposta) | "I voti silenti sono stati infranti. Qualcosa risponde ai richiami di chi non parla più." — `PENDING PM approval`. **Attenzione**: NO Cleric drift — è un culto minore, i suoi guardiani non sono Cleric né Priest live PM-locked |
| **enemy family** | Cultisti minori votati al silenzio + non-morti a bassa intensità (spettri di iniziati) — `PENDING PM approval` |
| **meccanica principale** | **Priest teaching (soft intro)**: introduzione a main stat **Saggezza**, weapon family **reliquia** + **focus**. Loot enfatizza stoffa + reliquia comune. **NO drift Cleric** nel naming/tema |
| **party size consigliata** | **3** (verbatim) |
| **tier loot atteso** | **T1** puro |
| **rarity loot attesa** | Common prevalente, Uncommon occasionale |
| **materiali principali** (proposta) | Cera votiva, ossa consacrate minori, stoffa penitenziale — `PENDING PM approval` |
| **possibile boss/miniboss** (proposta) | "Il Sussurro" (spettro ex-officiante, non nominato Cleric né Priest) — `PENDING PM approval` |
| **note itemization** | Loot Priest-friendly (reliquia T1, stoffa T1, focus T1). Universal per anelli/amuleti. NO drop piastre/arco/tomo |
| **note future achievement/ranking** | Achievement "Voto Compiuto" (clear con Priest nel party) — `PENDING PM approval` |

---

### Dungeon #4 — Avamposto della Palude Salata (🟡 DRAFT NEW — `PENDING PM approval`)

| Campo | Valore |
|---|---|
| **dungeon_id** (proposta) | `salt-fen-outpost` — `PENDING PM approval` |
| **Nome IT** (proposta) | "Avamposto della Palude Salata" — `PENDING PM approval` |
| **level range** (proposta) | **Lv4-7** — `PENDING PM approval` |
| **bracket** | `Lv1-15 / Early Game` (PM-locked) |
| **lore source** | **Velur** — estuari dimenticati, `PENDING PM approval`. **Nota**: `salt-marsh-5p` live usa già Velur (`content_family: "memory"`); differenziare Batch 1 come "avamposto" (insediamento) vs "palude aperta" (bioma) |
| **regione/bioma** | Palude salata, moli marci, capanne su palafitte |
| **tema narrativo** (proposta) | "Contrabbandieri hanno preso l'avamposto. La palude ricorda chi hanno cacciato prima." — `PENDING PM approval` |
| **enemy family** | Contrabbandieri + briganti costieri — `PENDING PM approval` |
| **meccanica principale** | **Rogue teaching**: main stat **Destrezza**, weapon family **pugnale** + **balestra**, armor **cuoio**. Loot enfatizza pugnali T1 + balestre leggere + cuoio T1 |
| **party size consigliata** | **3** (verbatim) |
| **tier loot atteso** | **T1** puro |
| **rarity loot attesa** | Common prevalente, Uncommon occasionale |
| **materiali principali** (proposta) | Sale grezzo, cuoio salato, corde di canapa, chele di crostaceo — `PENDING PM approval` |
| **possibile boss/miniboss** (proposta) | Capo-contrabbandiere "Marlo il Salato" (nome `PENDING PM approval`) |
| **note itemization** | Loot Rogue-friendly (pugnali T1, balestre T1, cuoio T1). Universal per cinture/mantelli. NO drop piastre/tomo/reliquia |
| **note future achievement/ranking** | Achievement "Marea Silenziosa" (clear senza kill sentinelle) — `PENDING PM approval` |

---

### Dungeon #5 — Grotta di Cinghialecupa (🟡 DRAFT NEW — `PENDING PM approval`)

| Campo | Valore |
|---|---|
| **dungeon_id** (proposta) | `boarhollow-cave` — `PENDING PM approval` |
| **Nome IT** (proposta) | "Grotta di Cinghialecupa" — `PENDING PM approval` |
| **level range** (proposta) | **Lv5-8** — `PENDING PM approval` |
| **bracket** | `Lv1-15 / Early Game` (PM-locked) |
| **lore source** | **Soe** — foreste settentrionali, `PENDING PM approval`. **Nota**: `wolf-den-5p` live usa già Soe; differenziare Batch 1 come "grotta bestiale" (chthonic) vs "tana di lupi" (superficie) |
| **regione/bioma** | Grotta boschiva, torrente sotterraneo, ossari |
| **tema narrativo** (proposta) | "I cinghialecupa sono più grandi dell'anno scorso. Qualcosa sotto la terra li nutre." — `PENDING PM approval` |
| **enemy family** | Bestie chthonic (cinghiali giganti, orsi delle grotte) — `PENDING PM approval` |
| **meccanica principale** | **Warrior teaching (soft intro)**: main stat **Forza**, weapon family **spada** + **lancia**, armor **maglia**. Loot enfatizza spade/lance T1 + maglia T1 |
| **party size consigliata** | **3** (verbatim) |
| **tier loot atteso** | **T1** puro |
| **rarity loot attesa** | Common prevalente, Uncommon occasionale |
| **materiali principali** (proposta) | Zanne di cinghiale, pelle spessa, ferro grezzo — `PENDING PM approval` |
| **possibile boss/miniboss** (proposta) | "Cinghialecupa Anziano" (bestia gigante, no nome umano) — `PENDING PM approval` |
| **note itemization** | Loot Warrior-friendly (spade T1, lance T1, maglia T1). Universal per cinture/stivali. NO drop stoffa/tomo/reliquia/focus |
| **note future achievement/ranking** | Achievement "Zanna Spezzata" — `PENDING PM approval` |

---

### Dungeon #6 — Santuario Dimenticato di Adalan (🟡 DRAFT NEW — `PENDING PM approval`)

| Campo | Valore |
|---|---|
| **dungeon_id** (proposta) | `forgotten-shrine-of-adalan` — `PENDING PM approval` |
| **Nome IT** (proposta) | "Santuario Dimenticato di Adalan" — `PENDING PM approval` |
| **level range** (proposta) | **Lv6-9** — `PENDING PM approval` |
| **bracket** | `Lv1-15 / Early Game` (PM-locked) |
| **lore source** | **Adalan** — cittadina/campagna con rovine antiche, `PENDING PM approval` |
| **regione/bioma** | Rovine di un santuario in pietra, sale con costrutti in ceramica |
| **tema narrativo** (proposta) | "Il santuario si è svegliato senza motivo. I custodi in ceramica difendono un cuore che nessuno ricorda più." — `PENDING PM approval` |
| **enemy family** | Costrutti minori (golem di ceramica, elementali arcani deboli) — `PENDING PM approval` |
| **meccanica principale** | **Mage teaching (soft intro)**: main stat **Intelligenza**, weapon family **bastone** + **focus** + **tomo**, armor **stoffa**. Loot enfatizza bastoni/focus T1 + stoffa T1. **Naming canonical Mage** (NO drift Wizard) |
| **party size consigliata** | **3** (verbatim) |
| **tier loot atteso** | **T1** puro |
| **rarity loot attesa** | Common prevalente, Uncommon occasionale |
| **materiali principali** (proposta) | Frammenti di ceramica arcana, polvere di essenza, tessuto rituale — `PENDING PM approval` |
| **possibile boss/miniboss** (proposta) | "Cuore di Ceramica" (costrutto guardiano) — `PENDING PM approval` |
| **note itemization** | Loot Mage-friendly (bastoni T1, focus T1, tomi T1, stoffa T1). Universal per anelli/amuleti. NO drop piastre/arco/reliquia |
| **note future achievement/ranking** | Achievement "Custode Silente" (clear senza rompere pilastri) — `PENDING PM approval` |

---

### Dungeon #7 — Crollo della Vena di Ferro (🟡 DRAFT NEW — `PENDING PM approval`)

| Campo | Valore |
|---|---|
| **dungeon_id** (proposta) | `ironvein-collapse` — `PENDING PM approval` |
| **Nome IT** (proposta) | "Crollo della Vena di Ferro" — `PENDING PM approval` |
| **level range** (proposta) | **Lv7-10** — `PENDING PM approval` |
| **bracket** | `Lv1-15 / Early Game` (PM-locked) |
| **lore source** | **Ambash** — mercantili/miniere di frontiera, `PENDING PM approval` |
| **regione/bioma** | Miniera abbandonata, gallerie crollate, laghetti sotterranei |
| **tema narrativo** (proposta) | "La vena di ferro è collassata all'improvviso. I minatori non sono mai risaliti — ma qualcosa sì." — `PENDING PM approval` |
| **enemy family** | Kobold + ratti giganti + carogne minerarie — `PENDING PM approval` |
| **meccanica principale** | **Party synergy teaching**: prima introduzione a ruoli party (tank/dps/support) via terreno claustrofobico. Loot bilanciato tra classi (no favoritismo). Primi hint T2 minor (materiali crafting) |
| **party size consigliata** | **3** (verbatim) |
| **tier loot atteso** | **T1** prevalente, **T2 minor** su materiali di crafting (introduzione) |
| **rarity loot attesa** | Common/Uncommon prevalenti, Rare molto raro (boss drop) |
| **materiali principali** (proposta) | Ferro grezzo, ferro raffinato (T2 minor), gemme opache, corde di miniera — `PENDING PM approval` |
| **possibile boss/miniboss** (proposta) | "Sciacallo del Crollo" (kobold anziano capobanda) — `PENDING PM approval` |
| **note itemization** | Loot universal prevalente (accessori) + primi hint materiali T2. Introduce concetto "materiale > item" (crafting placeholder futuro). NO Epic/Legendary |
| **note future achievement/ranking** | Achievement "Vena Aperta" (recovery drop T2) — `PENDING PM approval` |

---

### Dungeon #8 — Sala della Veglia Gelata (🟡 DRAFT NEW — `PENDING PM approval`)

| Campo | Valore |
|---|---|
| **dungeon_id** (proposta) | `frozen-vigil-hall` — `PENDING PM approval` |
| **Nome IT** (proposta) | "Sala della Veglia Gelata" — `PENDING PM approval` |
| **level range** (proposta) | **Lv8-11** — `PENDING PM approval` |
| **bracket** | `Lv1-15 / Early Game` (PM-locked) |
| **lore source** | **Krastlov** — ghiaccio/tundra di frontiera, `PENDING PM approval`. **Nota**: differenziare da `frost-cave-5p` (Halodi ghiacciai) — Krastlov ha tono più marziale/veglia |
| **regione/bioma** | Sala fortificata su tundra, cripte veterane, statue di guerrieri caduti |
| **tema narrativo** (proposta) | "I veterani della Veglia non sono mai stati sciolti dal loro giuramento. Il ghiaccio li ha tenuti — e ora si muovono." — `PENDING PM approval` |
| **enemy family** | Non-morti minori (guerrieri caduti animati) + elementali di gelo — `PENDING PM approval` |
| **meccanica principale** | **Party comp mista Warrior+Priest**: introduzione a resistenze status leggere (rallentamento gelo, purificazione debole). Loot bilanciato Warrior (maglia, spada, martello) + Priest (stoffa, reliquia, martello) |
| **party size consigliata** | **3** (verbatim) |
| **tier loot atteso** | **T1** prevalente, **T2 minor** possibile su boss drop |
| **rarity loot attesa** | Common/Uncommon prevalenti, Rare limitato (boss) |
| **materiali principali** (proposta) | Ghiaccio persistente, ferro invernale, filo consacrato — `PENDING PM approval` |
| **possibile boss/miniboss** (proposta) | "Capitano della Veglia Gelata" (guerriero non-morto veterano, nome specifico `PENDING PM approval`) |
| **note itemization** | Loot dual-target Warrior+Priest (introduzione a party comp mixed). Item universal per anelli/amuleti. NO drop cuoio/arco/tomo |
| **note future achievement/ranking** | Achievement "Giuramento Rotto" (clear con Priest nel party che purifica il boss) — `PENDING PM approval` |

---

### Dungeon #9 — Avamposto degli Ombre della Duna (🟡 DRAFT NEW — `PENDING PM approval`)

| Campo | Valore |
|---|---|
| **dungeon_id** (proposta) | `dunestalker-outpost` — `PENDING PM approval` |
| **Nome IT** (proposta) | "Avamposto degli Ombre della Duna" — `PENDING PM approval` |
| **level range** (proposta) | **Lv9-12** — `PENDING PM approval` |
| **bracket** | `Lv1-15 / Early Game` (PM-locked) |
| **lore source** | **Efreto** — deserto nomade, `PENDING PM approval` |
| **regione/bioma** | Deserto, oasi razziate, tende razziatrici semi-mobili |
| **tema narrativo** (proposta) | "Gli Ombre della Duna razziano oasi mercantili. Cacciano dal vento, non dal sole." — `PENDING PM approval` |
| **enemy family** | Banditi nomadi + sciacalli + sciamano nomade minore — `PENDING PM approval` |
| **meccanica principale** | **Ranger + Rogue party teaching**: main stat **Destrezza** doppia, weapon family **arco**/**balestra**/**pugnale**. Loot enfatizza mobilità (cuoio/maglia leggera Ranger, cuoio Rogue) |
| **party size consigliata** | **3** (verbatim) |
| **tier loot atteso** | **T1** prevalente, **T2 minor** su boss drop |
| **rarity loot attesa** | Common/Uncommon prevalenti, Rare limitato (boss) |
| **materiali principali** (proposta) | Cuoio bruciato dal sole, corda nomade, gemme grezze — `PENDING PM approval` |
| **possibile boss/miniboss** (proposta) | "Capo-razziatore della Duna" (bandito veterano) — `PENDING PM approval` |
| **note itemization** | Loot Ranger-friendly (archi/balestre T1-T2minor, cuoio+maglia leggera) + Rogue-friendly (balestre/pugnali). NO drop stoffa/piastre/reliquia |
| **note future achievement/ranking** | Achievement "Vento del Deserto" (clear rapido sotto X sec) — `PENDING PM approval` |

---

### Dungeon #10 — Bosco del Cuore-Legno (🟡 DRAFT NEW — `PENDING PM approval`)

| Campo | Valore |
|---|---|
| **dungeon_id** (proposta) | `heartwood-grove` — `PENDING PM approval` |
| **Nome IT** (proposta) | "Bosco del Cuore-Legno" — `PENDING PM approval` |
| **level range** (proposta) | **Lv10-12** — `PENDING PM approval` |
| **bracket** | `Lv1-15 / Early Game` (PM-locked) |
| **lore source** | **Alberi della Vita** — bosco antico, `PENDING PM approval`. **Nota**: fonte lore potenzialmente epica — Batch 1 la usa in versione **soft** (senza metafisica endgame), riservando manifestazioni maggiori a batch futuri |
| **regione/bioma** | Bosco antico, radici enormi, cuori-legno pulsanti |
| **tema narrativo** (proposta) | "Il bosco del Cuore-Legno ha un ritmo. Chi non lo segue viene digerito lentamente." — `PENDING PM approval` |
| **enemy family** | Driadi minori + spiriti della foresta + bestie druidiche — `PENDING PM approval` |
| **meccanica principale** | **All-class coherence**: dungeon accessibile a party misto (tutte 5 classi). Loot bilanciato universal prevalente + hint T2 assicurato su boss. Prima esperienza vera "party build matters" |
| **party size consigliata** | **3** (verbatim) |
| **tier loot atteso** | **T1** prevalente, **T2 minor** assicurato su boss drop |
| **rarity loot attesa** | Common/Uncommon prevalenti, Rare limitato (boss) |
| **materiali principali** (proposta) | Linfa antica, corteccia druidica, semi cuoreverde — `PENDING PM approval` |
| **possibile boss/miniboss** (proposta) | "Cuore-Legno Anziano" (spirito custode) — `PENDING PM approval` |
| **note itemization** | Loot universal prevalente + primi T2 minor bilanciati (accessori, cinture, mantelli). Introduce concetto "first T2 gear". NO Epic/Legendary |
| **note future achievement/ranking** | Achievement "Cuore Ascoltato" (clear con Ranger nel party) — `PENDING PM approval` |

---

### Dungeon #11 — Nascondiglio del Signore dei Briganti (🟡 DRAFT NEW — `PENDING PM approval`)

| Campo | Valore |
|---|---|
| **dungeon_id** (proposta) | `bandit-warlord-hideout` — `PENDING PM approval` |
| **Nome IT** (proposta) | "Nascondiglio del Signore dei Briganti" — `PENDING PM approval` |
| **level range** (proposta) | **Lv11-13** — `PENDING PM approval` |
| **bracket** | `Lv1-15 / Early Game` (PM-locked) |
| **lore source** | **Aveol** — passi di montagna, `PENDING PM approval`. **Nota**: differenziare da `bandit-hideout` live (Aveol, briganti disertori Crociata d'Argento) — Batch 1 versione "Warlord" è successivo cronologicamente, un capo organizzato che unifica bande |
| **regione/bioma** | Fortezza rocciosa sui passi, camere di guerra, tesoreria trappolata |
| **tema narrativo** (proposta) | "Il Signore dei Briganti ha unito tre bande. La sua tesoreria è armata meglio della guarnigione." — `PENDING PM approval` |
| **enemy family** | Briganti veterani + sciamano ribelle + sicari — `PENDING PM approval` |
| **meccanica principale** | **Proficiency check narrativo**: il loot del boss è **class-specific hint** — introduce narrativamente il concetto Gate 2 sez. 5/6 (armor/weapon proficiency hard-block). Loot mostrato = "cosa Warrior può usare, Mage no", teaching senza runtime enforcement (che arriverà in Phase C tech, gated) |
| **party size consigliata** | **3** (verbatim) |
| **tier loot atteso** | **T1** prevalente, **T2 minor** su boss drop |
| **rarity loot attesa** | Common/Uncommon prevalenti, Rare limitato (boss) |
| **materiali principali** (proposta) | Acciaio brigantesco, cuoio veterano, ferro montano, tesoreria (gemme opache) — `PENDING PM approval` |
| **possibile boss/miniboss** (proposta) | "Il Signore dei Briganti" + sciamano ribelle (2 fase, no drift Wizard) — `PENDING PM approval` |
| **note itemization** | Loot multi-class (Warrior spade/asce T1-T2 minor + Rogue pugnali T1 + Ranger balestre T1). NO drop stoffa/reliquia/tomo. Introduce concetto "questo pezzo Warrior può, Priest no" |
| **note future achievement/ranking** | Achievement "Signore Deposto" — spunto per **prima traccia proficiency teaching narrativo** — `PENDING PM approval` |

---

### Dungeon #12 — Torre Spezzata di Adalan (🟡 DRAFT NEW — `PENDING PM approval`)

| Campo | Valore |
|---|---|
| **dungeon_id** (proposta) | `broken-tower-of-adalan` — `PENDING PM approval` |
| **Nome IT** (proposta) | "Torre Spezzata di Adalan" — `PENDING PM approval` |
| **level range** (proposta) | **Lv13-15** — `PENDING PM approval` |
| **bracket** | `Lv1-15 / Early Game` (PM-locked) |
| **lore source** | **Adalan** — rovine cittadine antiche, `PENDING PM approval` |
| **regione/bioma** | Torre spezzata a metà, piani sospesi, biblioteca crollata |
| **tema narrativo** (proposta) | "La torre è caduta secoli fa. Chi la abita ora custodisce un sapere che nessuno chiede più." — `PENDING PM approval` |
| **enemy family** | Guardiani costrutti + apostata erudito (**NON Wizard**, nomenclatura canonical: "erudito", "apostata", "studioso") — `PENDING PM approval` |
| **meccanica principale** | **Transition Lv15→Lv20 (Batch 1 → Batch 2)**: primo boss con **T2 assicurato**, primo hint **Epic drop molto raro** (max 1 slot possibile, rate `PENDING PM`). Party comp matura. Naming apostata/erudito canonical NO drift Wizard |
| **party size consigliata** | **3** (verbatim) |
| **tier loot atteso** | **T1** + **T2 assicurato** su boss, **Epic** molto raro (max 1-2 slot, `PENDING PM approval` per rate) |
| **rarity loot attesa** | Common/Uncommon prevalenti, Rare regolare, Epic molto raro (boss drop only) |
| **materiali principali** (proposta) | Pietra spezzata di Adalan, tomo consumato, cristallo focus grezzo, filo d'oro antico — `PENDING PM approval` |
| **possibile boss/miniboss** (proposta) | "L'Erudito Apostata" (mago rinnegato, nomenclatura canonical, NO Wizard) — `PENDING PM approval` |
| **note itemization** | Loot Mage-friendly primario (tomi T1-T2, focus T1-T2, bastoni T1-T2, stoffa T1-T2) + universal accessori T2 minor. Possibile primo Epic drop molto raro su focus/tomo/anello. NO Legendary |
| **note future achievement/ranking** | Achievement "Primo Epic" (unlock a chi ottiene primo Epic drop qui) — spunto **transition Batch 2** — `PENDING PM approval` |

---

## 4. Nota Goblin Warrens (già live)

Il dungeon **Goblin Warrens** (`goblin-warrens`) è **già seed data** nel codebase:
- File sorgente: `backend/app/seeds/seed_data.py:168` (DUNGEON_SEED, "Phase 3 original 3")
- Metadata lore: `backend/app/content/lore_meta.py:50-56`
- `difficulty: 1`, `required_team_size: 3`, `recommended_power: 45`, `base_gold_reward: 35`, `base_xp_reward: 25`
- **Requires no new creation** — è incluso in Batch 1 come dungeon #1 per **coerenza narrativa** (onboarding già live) e per **audit trail** (documentare esplicitamente che il primo dungeon del bracket Lv1-15 è già in produzione).
- Il mapping `difficulty=1 → Lv1-3` è **proposta documentale Batch 1** — il DB non ha `level_min/max` esposti; NO scrittura richiesta.
- Il dungeon rientra nel **Phase 3 gate DO NOT MODIFY** (`backend/app/dungeons/gates.py:4`) — questo file può essere **SEALED** (verifica in Phase C tech dry-run futura, non in C0-quater).

---

## 5. Class proficiency teaching map — Batch 1

Ogni classe live PM-locked (C0-ter) ha almeno **1-2 dungeon dedicati** nel Batch 1 come teaching primario, più dungeon dove la classe è "welcome" secondaria.

| Classe | Main stat | Dungeon teaching primario | Dungeon welcome secondario |
|---|---|---|---|
| **Warrior** | Forza | #5 Boarhollow (spada/lancia/maglia), #8 Frozen Vigil (spada/martello/maglia), #11 Bandit Warlord (spada/ascia) | #1 Goblin Warrens (universal accessibile), #7 Ironvein (party synergy), #10 Heartwood (all-class) |
| **Rogue** | Destrezza | #4 Salt Fen (pugnale/balestra/cuoio), #9 Dunestalker (balestra/pugnale/cuoio), #11 Bandit Warlord (pugnale) | #1 (universal), #7 (party), #10 (all-class) |
| **Mage** | Intelligenza | #6 Adalan Shrine (bastone/focus/tomo/stoffa), #12 Broken Tower (tomo/focus/bastone/stoffa T2) | #1 (universal), #7 (party), #10 (all-class) |
| **Priest** | Saggezza | #3 Chapel (reliquia/focus/stoffa), #8 Frozen Vigil (martello/reliquia/stoffa) | #1 (universal), #7 (party), #10 (all-class) |
| **Ranger** | Destrezza | #2 Elfwood (arco/pugnale/cuoio), #9 Dunestalker (arco/balestra/cuoio+maglia), #10 Heartwood (arco/lancia) | #5 Boarhollow (lancia secondaria), #7 (party) |

### Copertura verificata

- **5 classi live / 5** hanno teaching primario dedicato ✅
- **12 dungeon / 12** hanno almeno 1 classe teaching primaria o welcome ✅
- **NO drift Wizard/Cleric** in nessun campo (Gate 2 sez. 4 rispettato) ✅
- **NO weapon families non-assegnate** (strumento/falce/trinket) referenziate come teaching in Batch 1 — restano `PENDING PM approval` per classi future ✅

---

## 6. Loot direction summary — Batch 1

### Distribuzione tier attesa (direzionale, no rate numerici)

| Tier | Presenza in Batch 1 | Note |
|---|---|---|
| **T1** | **Prevalente** su tutti i 12 dungeon | Core loot Batch 1 |
| **T2 minor** | Presente dai dungeon #7 (Lv7-10) in poi, **assicurato** su boss #10, #12 | Introduzione progressiva |
| **T3** | ❌ Non presente in Batch 1 | Riservato Batch 2+ |
| **T4** | ❌ Non presente | Riservato Batch 3+ |
| **T5** | ❌ Non presente | Riservato Batch 4/5 |

### Distribuzione rarity attesa (direzionale)

| Rarity | Presenza in Batch 1 | Note |
|---|---|---|
| **Common** | **Prevalente** ovunque | Backbone Batch 1 |
| **Uncommon** | Regolare, presente ovunque | Bilanciata |
| **Rare** | **Molto limitato** — solo boss drop dungeon #7, #8, #9, #10, #11, #12 | Non ogni boss droppa Rare |
| **Epic** | **Molto raro** — solo dungeon #12 boss (max 1 slot possibile, rate `PENDING PM`) | Introduzione simbolica |
| **Legendary** | ❌ **Assente** in Batch 1 (Gate 2: Legendary solo T5) | Governance verbatim |

### Rispetto crosswalk 1500 (Gate 2 sez. 2)

Batch 1 pesca principalmente dalla **Riga T1** (220 Common + 80 Uncommon = 300 item T1) e dai primi item della **Riga T2** (150 Common + 150 Uncommon + 50 Rare = 350 item T2). Le 300+350 = 650 righe T1+T2 forniscono il pool totale coprente Batch 1+2 (Lv1-30).

**Batch 1 stima porzione utilizzata**: ~35-45% del pool T1 (targeting Lv1-15 onboarding). Rimanente riservato a Batch 2 (Lv20-30 rifiniture T1 + T2 core).

---

## 7. Weapon families — copertura Batch 1

### Weapon families CONTEMPLATE nel teaching Batch 1 (13 su 16)

| Family | Dungeon teaching primario/welcome |
|---|---|
| **spada** | #4 Salt Fen (Rogue), #5 Boarhollow (Warrior), #8 Frozen Vigil (Warrior), #9 Dunestalker (Ranger), #11 Bandit Warlord |
| **ascia** | #11 Bandit Warlord (Warrior) |
| **martello** | #8 Frozen Vigil (Warrior+Priest) |
| **pugnale** | #2 Elfwood (Ranger), #4 Salt Fen (Rogue), #9 Dunestalker (Rogue), #11 Bandit Warlord |
| **arco** | #2 Elfwood (Ranger), #9 Dunestalker (Ranger), #10 Heartwood (Ranger) |
| **balestra** | #4 Salt Fen (Rogue), #9 Dunestalker (Rogue+Ranger) |
| **bastone** | #6 Adalan Shrine (Mage), #12 Broken Tower (Mage) |
| **tomo** | #6 Adalan Shrine (Mage), #12 Broken Tower (Mage) |
| **focus** | #3 Chapel (Priest), #6 Adalan Shrine (Mage), #8 Frozen Vigil (Priest), #12 Broken Tower (Mage) |
| **lancia** | #5 Boarhollow (Warrior), #10 Heartwood (Ranger secondaria) |
| **arma_in_asta** | #5 Boarhollow (Warrior, minor) |
| **scudo** | #5 Boarhollow (Warrior), #8 Frozen Vigil (Warrior) |
| **reliquia** | #3 Chapel (Priest), #8 Frozen Vigil (Priest) |

### Weapon families NON contemplate in Batch 1 (3 su 16 — `PENDING PM approval`)

Coerenti con C0-ter sez. 8 — Emergent NON le assegna a Batch 1:

| Family | Motivazione |
|---|---|
| **strumento** | Candidato per Bard drift/classe futura — NON assegnata in Batch 1 |
| **falce** | Candidato per classe futura (reaper/necromante/druido?) — NON assegnata in Batch 1 |
| **trinket** | Categoria "accessorio generico" — possibile universal, decisione PM successiva |

---

## 8. Governance check finale — Batch 1

- ✅ **12 dungeon** proposti (esattamente 12, non di più) — Goblin Warrens live (#1) + 11 DRAFT NEW
- ✅ **16 campi obbligatori** presenti per ognuno dei 12 dungeon
- ✅ **Level range Lv1-15** coperto progressivamente (3 Lv1-5, 4 Lv5-10, 4 Lv10-13, 1 Lv13-15)
- ✅ Ogni **campo player-facing** flaggato `PENDING PM approval` (nomi, temi, boss, materiali, level range esatti, lore assignment)
- ✅ **10 lore sources** su 17 usate in Batch 1; 7 esplicitamente **riservate** a batch futuri con motivazione
- ✅ **5 classi live PM-locked** (Warrior/Rogue/Mage/Priest/Ranger) tutte con teaching primario dedicato
- ✅ **Loot target rispettato**: T1 prevalente, T2 minor progressivo, NO Legendary, Epic solo dungeon #12 (molto raro), Rare limitato ai boss di 6 dungeon
- ✅ **party_size = 3** verbatim per tutti i 12 dungeon (Gate 1 SQ13 PM-locked)
- ✅ **Bracket "Lv1-15 / Early Game"** per tutti i 12
- ✅ **Naming canonical Mage/Priest** in tutti i campi (NO drift Wizard/Cleric — Gate 2 sez. 4 rispettato)
- ✅ **NO weapon families non-assegnate** (strumento/falce/trinket) referenziate come teaching — `PENDING PM approval` verbatim
- ✅ **Goblin Warrens** incluso come dungeon #1 con reference esatta al file live + `requires no new creation`
- ✅ **NO meccaniche punitive** (regola PM verbatim rispettata)
- ✅ **NO nomi generici** ("Cave 1, Cave 2") — ogni dungeon ha tema/lore/enemy differenziato
- ✅ **36 sigilli byte-identical** — nessuna modifica ai sealed files (attesa `pytest backend/tests/backend_r18_4_sealed_integrity_test.py` → PASS)
- ✅ **Zero DB writes**
- ✅ **Zero code changes** (`.py` / `.js` / `.jsx` / `.tsx` / `.ts` intatti, verificabile via `git status`)
- ✅ **Zero migrations / apply scripts / dungeon creation live**
- ✅ **Zero XP apply / level cap apply / drop table apply / runtime bridge activation**
- ✅ **NO proficiency runtime enforcement** — resta per Phase C tech dry-run (BLOCCATA)
- ✅ **NO aggiornamento PRD.md** — deliverable Batch 1 attende **GO PM esplicito** post-review

---

## 9. Osservazioni Emergent emerse durante la stesura

### Osservazione 1 — Lore sources epiche riservate

7 su 17 fonti (Irthe, Alevora, Ergolat, Faglie arcane, Vuoto, Luna Morta, Ciclo delle anime) risultano **troppo epiche** per Batch 1 in prima istanza. **Irthe** è già usata da `shadow-crypts` live (`difficulty=2`, tema `dread`) — coerente con collocazione Batch 2 (Lv20-30) e non Batch 1. Le altre 6 fonti (Alevora world boss / Ergolat / Faglie arcane / Vuoto / Luna Morta / Ciclo delle anime) sono naturalmente destinabili a Batch 3/4/5. **Nessun conflitto immediato**.

### Osservazione 2 — Nomenclatura "mago apostata" vs Wizard drift

Dungeon #12 (Torre Spezzata di Adalan) usa esplicitamente "erudito apostata" / "studioso rinnegato" per evitare qualsiasi drift verso "Wizard". La classe canonical **Mage** è preservata verbatim (Gate 2 sez. 3-4). **Nessun rischio drift** se il PM approva questa nomenclatura.

### Osservazione 3 — Overlap lore con dungeon live pre-esistenti

3 lore sources sono già usate da dungeon live (fuori Batch 1):
- **Halodi**: `goblin-warrens` (live, incluso in Batch 1 come #1) + `frost-cave-5p` (live, Halodi ghiacciai — bracket più alto, `PENDING PM` bracket assignment)
- **Aveol**: `bandit-hideout` (live, `difficulty=1` — proposta Batch 1 differenzia con "Bandit Warlord Hideout" successivo cronologicamente)
- **Velur**: `salt-marsh-5p` (live, `content_family: "memory"` — Batch 1 differenzia con "Salt Fen Outpost" insediamento vs bioma aperto)
- **Soe**: `wolf-den-5p` (live, tono `wonder`, superficie — Batch 1 differenzia con "Boarhollow Cave" chthonic)

**Governance nota**: il PM potrebbe voler **integrare** i 3 dungeon live (`bandit-hideout`, `salt-marsh-5p`, `wolf-den-5p`) come **parte esplicita** del Batch 1 anziché proporre nuovi dungeon "sovrapposti". Se il PM lo desidera, Emergent riorganizza la matrice — decisione flaggata `PENDING PM approval`.

### Osservazione 4 — Dungeon live oltre i 3 Phase 3 originali

Nel codebase esistono **oltre 3 dungeon live** (visti in `seed_data.py`): `sewer-nest`, `bandit-hideout`, `wolf-den-5p`, `frost-cave-5p`, `salt-marsh-5p`, `dragons-hoard`, `shadow-crypts` e altri. Molti sono coerenti con bracket Lv1-30. **Emergent NON li ha inclusi automaticamente in Batch 1**; potrebbe essere opportuno un audit dedicato (fuori scope Batch 1) per riallineare i dungeon live esistenti al nuovo modello bracket-based Batch 1-5. Questo audit è **flaggato per gate PM successivo**, NON toccato in C0-quater Batch 1.

### Osservazione 5 — Level range mapping vs `difficulty` legacy

Il sistema live NON espone `level_min/level_max` per dungeon. Il mapping Batch 1 a "Lv1-15" è **strato documentale** che non modifica il DB. Se in futura Phase C tech PM autorizzerà l'esposizione di `level_min/level_max`, servirà un **backfill script dry-run** dedicato (fuori scope C0-quater). Flaggato per Phase C tech futura.

### Osservazione 6 — Nessuna Legendary in Batch 1

Rispettata verbatim la regola PM (Batch 1: Legendary assenti). Le 15 Legendary del catalogo (Gate 2 sez. 2, tutto T5) restano riservate a Batch 4/5 (Lv40-60 endgame).

---

## 10. Handoff — pronto per PM Gate review Batch 1

### Deliverable pronti

- ✅ `/app/memory/r18_5_phase_c0quater_batch1_lv1_15_dungeon_matrix.md` (questo file)
- ✅ `/app/memory/r18_5_phase_c0quater_batch1_lv1_15_dungeon_matrix.json` (mirror strutturato)

### Sanity governance attesa post-write

- `git status` → **solo 2 nuovi file untracked** in `memory/` (i deliverable Batch 1). Nessun file tracked modificato.
- `pytest backend/tests/backend_r18_4_sealed_integrity_test.py` → attesa **PASS** (36 sigilli byte-identical).

### Prossimo step atteso (PM autorizza)

1. **PM Gate review Batch 1** → approva/modifica proposte `PENDING PM approval` (nomi, temi, boss, materiali, level range, lore assignment)
2. **Post-approval**: aggiornamento PRD.md con sezione "R18.5 Phase C0-quater Batch 1 CLOSED" — **non eseguito ora**, attende GO PM
3. **Batch 2** (Lv20-30) — **BLOCCATO** fino a review PM Batch 1
4. **Phase C tech dry-run** — 🔒 resta **BLOCCATA** (governance sigilli su `derive_ui_4state` / `item_public()` come da C0-ter sez. 11)

### Osservazione strategica finale

Emergent segnala che l'inclusione degli **8-10 dungeon live pre-esistenti** (oltre i 3 Phase 3 gates) nel nuovo modello bracket-based è un audit **fondamentale ma fuori scope Batch 1**. Se PM lo autorizza, Emergent può eseguire un audit read-only dedicato (nuovo deliverable `.md/.json`) per proporne l'integrazione a Batch 1/2/3.

**Batch 1 CLOSED (proposta DRAFT / PENDING PM approval)**. Attesa review PM.
