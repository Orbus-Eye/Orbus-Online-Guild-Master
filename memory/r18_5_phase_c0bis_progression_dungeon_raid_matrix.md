# R18.5 Phase C0-bis — Progression, Dungeon/Raid & Class Equipment Matrix (DOCUMENTAL ONLY)

- **Round**: `R18.5 — Itemization, ILVL & Gear Progression Rework`
- **Sottotitolo**: *Lv60 cap, item-centered endgame, lore-driven equipment*
- **Fase**: **C0-bis** — Progression / Dungeon / Raid / Proficiency matrices (scale-up MMO reale)
- **Locked at UTC**: `2026-07-06T19:00:00Z`
- **Governance**: DOCUMENTAL ONLY — 36 sigilli byte-identical, zero DB writes, zero code changes, zero migration.
- **Predecessori**:
  - `r18_5_phase_b1_design_lock.md/.json` (patched — scale-up correction 0-TER aggiunta)
  - `r18_5_phase_b2_implementation_plan.md/.json` (patched)
  - `r18_5_phase_b_gate1_pm_decisions.md/.json` (autoritativo SQ11-SQ18, lore rules, base legendary policy)
  - `r18_5_phase_c0_item_table_drafting_support.md/.json` (superseded per scala catalogo reale, resta come micro-sample)
- **Autoritativo su**: scala catalogo reale (1500 item), 60 dungeon, 12 raid, proficiency system, ordine valutazione equip.

## 0. Superseding esplicito

Il **catalogo reale R18.5** supera il micro-batch B.1/C0 originale:

| Aspetto | B.1/C0 (superseded per catalogo reale) | Catalogo reale (questo file) |
|---|---|---|
| Item totali | 80 (micro-sample) | **1500 minimo** |
| Legendary max | 4 (micro-batch) | **max 15** (catalogo) |
| Dungeon | non pianificati | **60 dungeon** |
| Raid | non pianificati | **12 raid** |
| Proficiency system | non pianificato | **armor + weapon obbligatorie**, hard block |
| Progression Lv60 | "ILVL/equip" | ILVL / raid / loot raro / utility / ranking / mercato |

Gli 80 item + 13 draft C0 restano come **micro-sample / skeleton propositivo**, non come cap.

## 1. Matrice Lv1-60 — Progression Pacing (5 brackets)

| Bracket | Semantica gameplay | Percezione player desiderata |
|---|---|---|
| **Lv1-15** | Facile / onboarding / primi dungeon | *"entro nel gioco"* |
| **Lv16-30** | Progressione normale / prime build | *"costruisco la squadra"* |
| **Lv31-45** | Salita seria / dungeon più tecnici | *"devo iniziare a capire build, main stat ed equip"* |
| **Lv46-55** | Late game / ottimizzazione equip | *"devo farmare e ottimizzare"* |
| **Lv56-60** | Scalata finale / pre-raid + endgame | *"sto scalando una vetta"* |
| **Lv60** (endgame) | Cap hard — ILVL / raid / dungeon endgame / loot raro / ranking / mercato | *"inizia il vero endgame item-based"* |

### Vincoli progression
- `MAX_ADVENTURER_LEVEL = 60` (Gate 1 correction) — hard cap gameplay.
- XP oltre Lv60 non aumenta livello.
- Post-Lv60 = progressione **item-based** (ILVL / equip / raid / utility / ranking / mercato).

## 2. Matrice 60 dungeon — distribuzione per bracket (PM lock)

| Bracket | Dungeon count |
|---|---:|
| Lv1-15 | **12** |
| Lv16-30 | **14** |
| Lv31-45 | **16** |
| Lv46-55 | **10** |
| Lv56-60 | **8** |
| **Totale** | **60** |

**Distribuzione PM-locked**. Nomi, temi, lore source specifica, boss, affissi/modifier finali → **`PENDING PM approval`** individuale per dungeon.

## 3. Matrice 12 raid — distribuzione per bracket (PM lock)

| Bracket | Raid count | Ruolo narrativo |
|---|---:|---|
| Lv20-30 | **2** | raid introduttivi |
| Lv31-45 | **3** | raid intermedi |
| Lv46-55 | **3** | raid late game |
| Lv60 | **4** | raid endgame |
| **Totale** | **12** | — |

**Distribuzione PM-locked**. Nomi, meccaniche specifiche, drop rate finali → **`PENDING PM approval`**.

### Structural requirements dei raid (proposta strutturale, `PENDING PM` sui numeri finali)

Ogni raid deve richiedere:
1. **Team composition** — dimensione team + limiti classe.
2. **Ruoli obbligatori** — Tank + Healer + DPS (mix configurabile).
3. **Gear check** — min ILVL medio della squadra + avg PWR check.
4. **Armor proficiency corretta** — nessun bypass su proficiency mismatch.
5. **Weapon proficiency corretta** — idem.
6. **Main stat sensata** — verifica coerenza classi/build.
7. **Utility item** — richiesta almeno 1 utility item lore-linked nel loadout squadra.
8. **Reward superiori** — drop T4/T5 potenziato, chance Legendary aumentata (max drop 15 catalogo).
9. **Ranking dedicati** — leaderboard raid-specific + season ranking.

## 4. Matrice classi → main stat

### Main stat PM-approved (lista verbatim, 6 stat)
Forza · Destrezza · Costituzione · Intelligenza · Saggezza · Carisma

### Classi live (verbatim PM — attualmente attive)

| Classe (PM verbatim) | Naming drift osservato B.1 | Main stat proposta | Alternative PM | Status |
|---|---|---|---|---|
| **Warrior** | — | Forza | o Costituzione | `PENDING PM approval` |
| **Rogue** | — | Destrezza | — | `PENDING PM approval` |
| **Mage** | B.1 Extra D = "Wizard" | Intelligenza | — | `PENDING PM approval` — naming drift da chiarire |
| **Priest** | B.1 Extra D = "Cleric" | Saggezza | — | `PENDING PM approval` — naming drift da chiarire |
| **Ranger** | — | Destrezza | o Forza | `PENDING PM approval` |

### Classi bloccate (NO unlock in C0-bis)
- CdM (Cacciatore di Mostri) — HOLD R18.3f class_slug migration
- CdV — HOLD
- Berserker — dormant, no signature R18.5
- Assassin — dormant, no signature R18.5

### Bard
Bard role drift resta in **backlog**, non attivo in C0-bis (nessun mapping proposto).

### Observation naming drift Mage/Priest vs Wizard/Cleric
Discrepanza tra:
- PM verbatim C0-bis: **Warrior, Rogue, Mage, Priest, Ranger**
- B.1 Extra D placeholder: **Warrior, Paladin, Berserker, Rogue, Ranger, Assassin, Monk, Cleric, Wizard, Cacciatore di Mostri**

Da chiarire dal PM: (a) canonizzare Mage/Priest come nuovi nomi player-facing, (b) confermare "Wizard→Mage" e "Cleric→Priest" come rename, (c) o solo micro-sample B.1 aveva placeholder mai canonici. **`PENDING PM approval`**.

## 5. Matrice classi → armor proficiency (hard block)

### Armor types PM-approved (lista verbatim, 4 tipi)
stoffa · cuoio · maglia · piastre

### Regola tassativa PM
> *"Se non hai proficiency, non puoi equipaggiare quell'oggetto"* — hard block runtime, **non solo warning**.

### Proposta preliminare mapping classe → armor proficiency (tutti `PENDING PM approval`)

| Classe | stoffa | cuoio | maglia | piastre | Rationale (proposto, PM valida) |
|---|:-:|:-:|:-:|:-:|---|
| Warrior | ❌ | ❌ | ✅ | ✅ | Tank/DPS_melee, alta difesa |
| Rogue | ✅ | ✅ | ❌ | ❌ | Stealth/DPS, mobilità |
| Mage | ✅ | ❌ | ❌ | ❌ | DPS_ranged, casting non impedito |
| Priest | ✅ | ✅ | ❌ | ❌ | Healer, flessibilità difensiva light |
| Ranger | ❌ | ✅ | ✅ | ❌ | DPS_ranged + melee ibrido |

**Tutte le celle di questa matrice sono `PENDING PM approval`**. Emergent NON può canonizzare hard block senza PM lock (impatta identità classe).

## 6. Matrice classi → weapon proficiency (hard block)

### Weapon families PM-approved (lista verbatim, 16 famiglie)
spada · ascia · martello · pugnale · arco · balestra · bastone · tomo · focus · strumento · falce · lancia · arma in asta · scudo · reliquia · trinket

### Proposta preliminare mapping classe → weapon proficiency (tutti `PENDING PM approval`)

| Classe / Weapon | spada | ascia | martello | pugnale | arco | balestra | bastone | tomo | focus | strumento | falce | lancia | arma in asta | scudo | reliquia | trinket |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **Warrior** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |
| **Rogue** | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Mage** | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Priest** | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| **Ranger** | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |

Famiglie non mappate a nessuna classe live in questa proposta preliminare: **strumento**, **falce** (candidati per Bard drift / classi future). `PENDING PM approval`.

**Tutte le celle sono `PENDING PM approval`** — impatta identità classe hard.

## 7. Matrice dungeon/raid → tier loot (proposta preliminare)

| Bracket | Content type | Tier loot prevalente | Note |
|---|---|---|---|
| Lv1-15 | 12 dungeon | **prevalentemente T1** | qualche T2 rare drop |
| Lv16-30 | 14 dungeon | **prevalentemente T2**, alcuni T3 | 2 raid intro Lv20-30 → chance T3 |
| Lv31-45 | 16 dungeon | **prevalentemente T3**, alcuni T4 | 3 raid intermedi → chance T4 |
| Lv46-55 | 10 dungeon | **prevalentemente T4** | 3 raid late → T4/T5 |
| Lv56-60 | 8 dungeon | **T4-T5 principale** | 4 raid endgame → **fonte principale T5 + Legendary drop (max 15 catalogo)** |

**Drop rate finali per tier/rarity nei dungeon/raid → `PENDING PM approval`**. La `Cripta delle Faglie di Ambash` (Gate 1 SQ15) è uno dei raid endgame Lv60.

## 8. Matrice dungeon/raid → lore source (17 fonti PM-approved)

### Lista lore sources approvate (verbatim Gate 1)
Ambash · Irthe · Velur · Efreto · Halodi · Alevora · Soe · Aveol · Ergolat · Krastlov · Adalan · Greatwood/Elfwood · Alberi della Vita · Faglie arcane · Vuoto · Luna Morta · Ciclo delle anime

### Regola
Ogni dungeon/raid deve avere **almeno una lore source** assegnata. Item T3+ droppati dal dungeon/raid ereditano priority sulla lore source del content per naming/utility narrative.

### Proposta distribuzione (`PENDING PM approval` sui match specifici)

| Bracket | # dungeon | # raid | Suggested lore sources pool |
|---|---:|---:|---|
| Lv1-15 | 12 | 0 | Greatwood/Elfwood, Adalan, Alberi della Vita, Halodi, Soe |
| Lv16-30 | 14 | 2 | Krastlov, Aveol, Irthe, Velur, Ergolat |
| Lv31-45 | 16 | 3 | Alevora, Efreto, Faglie arcane, Ambash (early) |
| Lv46-55 | 10 | 3 | Ambash, Vuoto, Luna Morta (mid) |
| Lv56-60 | 8 | 4 | Ambash (endgame — Cripta delle Faglie), Vuoto, Luna Morta, Ciclo delle anime |

**I match specifici lore→dungeon/raid sono `PENDING PM approval`**. Emergent NON assegna lore source in modo canonico.

## 9. Matrice dungeon/raid → required level (proposta pacing)

| Content | Bracket | Required level range (proposta) | Status |
|---|---|---|---|
| Dungeon Lv1-15 | starter | 1-15 (12 dungeon distribuiti) | `PENDING PM approval` |
| Dungeon Lv16-30 | early-mid | 16-30 (14 dungeon distribuiti) | `PENDING PM approval` |
| Raid Lv20-30 | intro | 20-30 (2 raid, min avg ILVL squadra proposto) | `PENDING PM approval` |
| Dungeon Lv31-45 | mid | 31-45 (16 dungeon distribuiti) | `PENDING PM approval` |
| Raid Lv31-45 | intermedi | 31-45 (3 raid) | `PENDING PM approval` |
| Dungeon Lv46-55 | late | 46-55 (10 dungeon distribuiti) | `PENDING PM approval` |
| Raid Lv46-55 | late | 46-55 (3 raid) | `PENDING PM approval` |
| Dungeon Lv56-60 | endgame | 56-60 (8 dungeon distribuiti) | `PENDING PM approval` |
| Raid Lv60 | endgame | 60 (4 raid, gear check ILVL medio squadra >=T4/T5) | `PENDING PM approval` |

## 10. Scala 1500 item — distribuzione tier + rarity (PM lock)

### Distribuzione per tier (PM-locked, verbatim)

| Tier | Level bracket | Count |
|---|---|---:|
| T1 | Lv1-15 | **300** |
| T2 | Lv16-30 | **350** |
| T3 | Lv31-45 | **350** |
| T4 | Lv46-55 | **300** |
| T5 | Lv56-60 | **200** |
| **Totale** | — | **1500** |

### Distribuzione per rarity (PM-locked, verbatim)

| Rarity | Count |
|---|---:|
| Common | **400** |
| Uncommon | **450** |
| Rare | **400** |
| Epic | **235** |
| **Legendary** | **15** ← hard cap catalogo |
| **Totale** | **1500** |

### Rapporto tier ↔ rarity nel catalogo reale
Il mapping Gate 1 SQ12 (Common→T1, Uncommon→T2, Rare→T3, Epic→T4, Legendary→T5) **non è più 1:1 numericamente** con le distribuzioni sopra:
- T1=300 ≠ Common=400 (300+ Common presenti in T1, ~100 in T2 come "low uncommon"?)
- T5=200 ≠ Legendary=15 (le altre 185 T5 saranno Epic Lv56-60).

**`PENDING PM approval`**: chiarimento del mapping definitivo tier×rarity nel catalogo reale — se il mapping Gate 1 SQ12 (1 rarity ↔ 1 tier) va mantenuto oppure sostituito da mapping soft (rarity distribuita cross-tier).

### Legendary policy (verbatim PM catalogo reale)

- **Max 15 Legendary** nel catalogo iniziale (hard cap).
- **Utility unica** obbligatoria.
- **Lore source** obbligatoria (da lista 17 fonti).
- **Fonte precisa** (specifico raid/boss/dungeon endgame).
- **Drop rarissimo** — no drop rate finale, `PENDING PM approval`.
- **Non craftabili** normalmente.
- **Non ottenibili da shop** — nessun pay-to-win.
- **Non devono essere semplici stat stick**.

**Esempio approvato**:
> *"Lama della Faglia Quieta"* — Fonte lore: **Ambash** — Utility: riduce il rischio di eventi arcani instabili nei dungeon legati alle faglie.

**Esempio rifiutato**:
> *"Spada Leggendaria +20 Forza"*.

## 11. Superseding note — vecchio hard cap 80 item

Il file `r18_5_phase_c0_item_table_drafting_support.md/.json` definiva **80 item totali** come batch primo lotto (Gate 1 SQ14 lock micro-batch). Questo cap è **superseded per il catalogo reale**:

- **80 item = micro-sample / skeleton propositivo**, valido per il drafting iniziale (13 draft esistenti + 67 righe compilabili PM).
- **Catalogo reale R18.5 = 1500 item minimo** (questa fase C0-bis).
- Gli 80 item + 13 draft C0 sono **non autoritativi** per il catalogo reale, ma **restano validi** come pattern/skeleton di riferimento per il naming/lore/utility.

**Riferimento autoritativo cap**: sezione 10 di questo file.

## 12. Superseding note — vecchio max 4 Legendary

Il file `r18_5_phase_b_gate1_pm_decisions.md/.json` (Gate 1 SQ14) definiva **max 4 Legendary** nel batch primo lotto (80 item). Questo cap è **superseded per il catalogo reale**:

- **Max 4 Legendary** vale solo per il **micro-batch 80 item** (drafting iniziale C0).
- **Catalogo reale R18.5 = max 15 Legendary** (hard cap, sezione 10 di questo file).

Le 15 Legendary del catalogo reale devono rispettare integralmente la Legendary policy PM (sezione 10).

**Riferimento autoritativo cap Legendary**: sezione 10 di questo file.

## 13. Ordine valutazione equip (verbatim PM)

Il PM ha lockato l'ordine di valutazione:

1. **Posso equipaggiarlo?** → armor / weapon proficiency (**hard block** se no).
2. **È adatto alla classe?** → main stat.
3. **Quanto è forte?** → ILVL, rarity, tier.
4. **Ha utility?** → effetti speciali / lore / dungeon-specific.

### Impatto futuro (Phase C tech dry-run — NON in C0-bis)
- Serializer `GET /api/adventurers/{id}/eligible-items` (R18.4.followup Phase B/C, SEALED) potrebbe richiedere **estensione** per proficiency check.
- UI `ItemCompatibilityBadge` 4-state esistente (SEALED R18.4.followup C) potrebbe estendersi con nuovo stato **"no proficiency"** (5-state, oppure hard block prima del 4-state).
- Auto-equip logic (`app/equipment/auto_equip.py`, non-sealed) attualmente skippa con warning: potrebbe diventare **hard block** su proficiency mismatch.

**NON implementare ora**. Solo documentare come **requisito Phase C tech dry-run**.

## Self-check Phase C0-bis 20/20

- [x] Sezione 1 — 5 brackets Lv1-60 + percezione player (verbatim PM)
- [x] Sezione 2 — 60 dungeon distribuzione (12/14/16/10/8) PM-locked
- [x] Sezione 3 — 12 raid distribuzione (2/3/3/4) PM-locked + 9 structural requirements
- [x] Sezione 4 — Matrice classi → main stat (5 classi live, PENDING PM su valori finali)
- [x] Sezione 5 — Matrice classi → armor proficiency (4 armor types, hard block, PENDING PM)
- [x] Sezione 6 — Matrice classi → weapon proficiency (16 weapon families, PENDING PM)
- [x] Sezione 7 — Matrice dungeon/raid → tier loot (proposta preliminare)
- [x] Sezione 8 — Matrice dungeon/raid → lore source (17 fonti, PENDING PM su match specifici)
- [x] Sezione 9 — Matrice dungeon/raid → required level (proposta pacing)
- [x] Sezione 10 — Scala 1500 item (300/350/350/300/200) + rarity (400/450/400/235/15) PM-locked + Legendary policy
- [x] Sezione 11 — Superseding note vecchio hard cap 80 item
- [x] Sezione 12 — Superseding note vecchio max 4 Legendary
- [x] Sezione 13 — Ordine valutazione equip (4 step verbatim PM) + impatto Phase C tech
- [x] Observation naming drift Mage/Priest vs Wizard/Cleric documentata
- [x] Classi bloccate elencate (CdM, CdV, Berserker, Assassin)
- [x] Bard backlog notato
- [x] Nessuna finalizzazione autonoma di nomi/mapping proficiency/stat/utility/drop rate
- [x] Distribuzioni PM-locked verbatim: 60=12+14+16+10+8, 12=2+3+3+4, 1500=300+350+350+300+200, rarity=400+450+400+235+15
- [x] Legendary count nei mapping ≤ 15 (nessuno superato)
- [x] Zero DB writes, zero code changes, sigilli intatti

**Phase C0-bis CLOSED**. Attesa PM Gate 2 review + risposta agli item PENDING PM approval (proficiency mapping, main stat mapping, mapping tier×rarity nel catalogo reale, naming drift Mage/Priest).
