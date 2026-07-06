# R18.5 Gate 2 — PM Decisions Record (DOCUMENTAL ONLY)

- **Round**: `R18.5 — Itemization, ILVL & Gear Progression Rework`
- **Sottotitolo**: *Lv60 cap, item-centered endgame, lore-driven equipment*
- **Gate**: **Gate 2** (unlocks Phase C0-ter Live Class Matrix + successive expansion)
- **Autorità**: PM Orchestrator
- **Locked at UTC**: `2026-07-06T20:00:00Z`
- **Governance**: DOCUMENTAL ONLY — solo audit trail delle decisioni PM verbatim, ZERO nuove decisioni introdotte.
- **Predecessori**: Gate 1 (r18_5_phase_b_gate1_pm_decisions.md/.json) + C0-bis (r18_5_phase_c0bis_progression_dungeon_raid_matrix.md/.json)
- **Successore**: `r18_5_phase_c0ter_live_class_matrix.md/.json` (matrice classi live integrata)

## 1. Tier ↔ Rarity many-to-many strategy (PM verbatim)

Il mapping **1:1 di Gate 1 SQ12 è rimosso**. Nuova regola:

- **Tier** = fascia tecnica / ILVL / bracket di potenza.
- **Rarity** = qualità, rarità di drop e valore.
- Un item **T2** può essere **Common, Uncommon, o Rare**.
- Un item **T5** può essere **Rare, Epic, o Legendary**.
- **Legendary NON significa "tutto T5"** — è solo una piccola parte di T5.

### Implicazione superseding
Gate 1 SQ12 (Common↔T1, Uncommon↔T2, Rare↔T3, Epic↔T4, Legendary↔T5) **resta valido come colorazione UI del badge**, ma **non è più un mapping 1:1 numerico**. La rarity di un item è indipendente dal tier tecnico.

## 2. Crosswalk 1500 item PM-approved (aritmeticamente verificata)

| Tier | Common | Uncommon | Rare | Epic | Legendary | **Totale riga** |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **T1** | 220 | 80  | 0   | 0   | 0  | **300** |
| **T2** | 150 | 150 | 50  | 0   | 0  | **350** |
| **T3** | 30  | 160 | 130 | 30  | 0  | **350** |
| **T4** | 0   | 60  | 150 | 90  | 0  | **300** |
| **T5** | 0   | 0   | 70  | 115 | 15 | **200** |
| **Totale colonna** | **400** | **450** | **400** | **235** | **15** | **1500** |

### Verifica aritmetica eseguita
- ✅ Righe tier: 300+350+350+300+200 = **1500**
- ✅ Colonne rarity: 400+450+400+235+15 = **1500**
- ✅ Ogni riga tier sums al target: T1=300, T2=350, T3=350, T4=300, T5=200
- ✅ Ogni colonna rarity sums al target: Common=400, Uncommon=450, Rare=400, Epic=235, Legendary=15

### Interpretazione design (verbatim PM)

| Tier | Design intent |
|---|---|
| **T1** | Early game — prevalentemente Common (220), Uncommon (80) presenti |
| **T2** | Progressione iniziale/intermedia — Common ancora presente (150), Uncommon (150), Rare iniziano (50) |
| **T3** | Mid game serio — Rare importanti (130), Uncommon dominanti (160), Epic iniziano (30) |
| **T4** | Late game — Rare/Epic dominanti (150+90), Uncommon possibili come transizione (60) |
| **T5** | Endgame — solo Rare (70) / Epic (115) / Legendary (15). **NO Common/Uncommon a T5** |
| **Legendary** | **Solo T5**, max 15 item catalogo iniziale |

## 3. Canonical naming classi live (PM verbatim)

Le 5 classi live PM-lockate:

| Slug canonical | Label IT canonical | Legacy note |
|---|---|---|
| **Warrior** | Guerriero | — |
| **Rogue** | Ladro | — |
| **Mage** | Mago | canonical (era placeholder B.1 "Wizard") |
| **Priest** | Priest (legacy label mantenuto) | **NON Cleric drift** — Priest resta label |
| **Ranger** | Ranger (legacy label mantenuto) | — |

## 4. Purge drift Wizard/Cleric (documentale)

**Regola tassativa PM**:

- **Wizard** e **Cleric** sono **drift vietati**.
- Da **rimuovere/correggere** in file futuri e placeholder B.1 dove presenti.
- **NON usare come sinonimi** di Mage/Priest.
- **NON introdurre nuove classi o rename** senza gate PM esplicito.

### Scope purge in C0-ter
- **Solo documentale**. Nessun touch al codice runtime.
- Placeholder B.1 Extra D (Wizard, Cleric) restano nel file B.1 come **history preserved**, ma sono formalmente `deprecated` — canonizzazione a Mage/Priest.
- Naming futuro (item, dungeon, raid, UI copy) userà **Mage** e **Priest** verbatim.
- Rimozione fisica da codice runtime → **NON in C0-ter**, richiede gate PM dedicato.

## 5. Armor proficiency — hard-block policy (PM verbatim)

**Regola**: "Se una classe non ha armor proficiency, **non può equipaggiare** quell'armor type".

- **Hard block**, non warning.
- **Logica respinta**: "può equipaggiarlo chiunque, ma è consigliato ad alcuni".
- **Logica ammessa** solo per:
  - consumabili
  - materiali
  - risorse
  - accessori generici rarissimi
  - item non equipaggiabili

### Impatto runtime (documentale, non implementato in C0-ter)
Il futuro Phase C tech dry-run dovrà estendere `/api/adventurers/{id}/eligible-items` con nuovo `reason_code` = `proficiency_missing_armor`.

## 6. Weapon proficiency — hard-block policy (PM verbatim)

**Regola**: "Se una classe non ha weapon proficiency, **non può equipaggiare** quella weapon family".

- **Hard block runtime** richiesto (futuro Phase C tech).
- Simmetrico alla policy armor (sezione 5).

### Impatto runtime (documentale)
Reason_code nuovo: `proficiency_missing_weapon`.

## 7. Main stat policy (PM verbatim)

- **Main stat** = cuore della performance della classe.
- Deve essere **visibile nel design item** (naming, stat, utility che scalano con main stat).
- Deve essere **visibile nella futura guida classi** (in-game/help/UI).

## 8. Ordine valutazione equip (PM verbatim, riaffermato)

1. **Posso equipaggiarlo?** → armor/weapon proficiency (**hard block** se no)
2. **È adatto alla classe?** → main stat
3. **Quanto è forte?** → ILVL, rarity, tier
4. **Ha utility?** → effetti speciali / lore / dungeon-specific

## 9. Lista dei remaining non-blocking PM items (audit-only, non riaprire ora)

Item PENDING PM che restano aperti dopo Gate 2, ma **NON bloccanti** per l'expansion di Phase C0-ter / C tech:

1. **Nomi e temi dei 60 dungeon** — batch iterativi futuri.
2. **Nomi e meccaniche dei 12 raid** — batch iterativi futuri.
3. **Drop rate finali** per bracket / tier / rarity.
4. **Lore source specifiche** per ogni dungeon/raid (17 fonti × 72 istanze content).
5. **Utility narrative + effetti** dei 15 Legendary.
6. **Signature items design finale** (max 25 signature — Gate 1 SQ13 lockato su count/policy, design specifico non ancora fissato).

**Nota**: questi 6 item **non sono blocker** per l'implementazione della struttura tecnica. Possono essere risolti a batch nelle fasi successive.

## Self-check Gate 2

- [x] Sezione 1 — tier↔rarity many-to-many strategy verbatim PM
- [x] Sezione 2 — Crosswalk 1500 aritmeticamente verificata (righe, colonne, totale = 1500)
- [x] Sezione 3 — Canonical naming Warrior/Rogue/Mage/Priest/Ranger verbatim PM
- [x] Sezione 4 — Purge drift Wizard/Cleric documentale
- [x] Sezione 5 — Armor proficiency hard-block policy
- [x] Sezione 6 — Weapon proficiency hard-block policy
- [x] Sezione 7 — Main stat policy
- [x] Sezione 8 — Ordine valutazione equip (4 step verbatim)
- [x] Sezione 9 — 6 remaining non-blocking items
- [x] Solo audit trail verbatim PM — nessuna decisione nuova introdotta
- [x] Zero DB writes / Zero code changes / Sigilli intatti

**Gate 2 CLOSED**. Prossimo: **Phase C0-ter** (Live Class Matrix Integration — matrice classi 5×proficiency+main stat).
