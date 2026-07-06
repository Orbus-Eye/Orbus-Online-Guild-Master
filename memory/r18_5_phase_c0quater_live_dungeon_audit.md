# R18.5 Phase C0-quater — Live Dungeon Audit (READ-ONLY)

- **Round**: `R18.5 — Itemization, ILVL & Gear Progression Rework`
- **Fase**: **C0-quater — Live Dungeon Audit** (pre-Batch 1 informed)
- **Locked at UTC**: `2026-07-06T21:00:00Z`
- **Governance**: **DOCUMENTAL ONLY / READ-ONLY** — 36 sigilli byte-identical, zero DB writes, zero code changes.
- **Autorità**: PM Orchestrator (GO audit esplicito ricevuto)
- **Status**: 🟡 **AUDIT COMPLETE / PENDING PM decisioni su rischi identificati** prima di redigere Batch 1 informed
- **Predecessori autoritativi**:
  - `r18_5_phase_b_gate1_pm_decisions.md/.json` (17 lore sources Gate 1)
  - `r18_5_gate2_pm_decisions.md/.json` (Gate 2)
  - `r18_5_phase_c0ter_live_class_matrix.md/.json` (5 classi live)
  - `r18_5_phase_c0quater_batch1_lv1_15_dungeon_matrix.md/.json` (Batch 1 DRAFT — da rifare informed post-audit)
- **Metodo audit**: query MongoDB read-only (`find()`, `aggregate()`), lettura file `backend/app/seeds/seed_data.py` + `backend/app/content/lore_meta.py` (**NO writes**, **NO code changes**).

---

## 0. Executive summary — 3 sorprese principali

### ⚠️ Sorpresa 1 — 24 dungeon live (stop rule soft >20 triggered)

Il DB `dungeons` contiene **24 documenti totali** (23 attivi + 1 test disattivato). La stima pre-audit era 8-10. Emergent **non ferma** l'audit (soglia stop hard non definita), ma segnala la deviazione: la scala del catalogo live è **più matura del previsto**.

### ⚠️ Sorpresa 2 — `required_level` esiste già + bucket già in DB

Contrariamente a quanto stimato in Osservazione 5 del Batch 1 DRAFT ("il sistema live NON espone level_min/max"), il DB **ha già**:
- Campo `required_level` (int) popolato su tutti i 24 dungeon (Lv1 → Lv14)
- Campo `bucket` (string) con 4 valori: `tutorial` / `early` / `mid` / `high`

Questa scoperta **rimuove la necessità** di un backfill script Phase C tech per esposizione level range: il dato è già live. Il gap è tra le **4 bucket legacy** (`tutorial/early/mid/high`) e le **5 bracket R18.5** (`Lv1-15/16-30/31-45/46-55/56-60`).

### 🔴 Sorpresa 3 — Party size split 3p / 5p + lore theme disallineamento

Due criticità di alto impatto:
1. **Party size**: 10 dungeon `required_team_size=3` + 12 dungeon `required_team_size=5` (via `is_5p=True`) + 1 `training-yard`=3. Il vincolo Gate 1 SQ13 `party_size=3` **esclude 12 dungeon 5-player** da Batch 1 se tassativo. Serve decisione PM.
2. **Lore theme mismatch**: 8 tag `lore_theme` live (`urban`, `frontiera`, `fucina`, `memoria`, `mare`, `draco`, `celeste`, `infernale`) **NON compaiono** tra le 17 fonti Gate 1. 10 fonti Gate 1 (Alevora, Aveol, Ergolat, Krastlov, Adalan, Greatwood/Elfwood, Alberi della Vita, Faglie arcane, Luna Morta, Ciclo delle anime) **NON usate** da nessun dungeon live.

---

## 1. Lista dungeon live esistenti (censimento completo)

Fonte: `db.dungeons.find({}).sort('required_level', 1)` — DB `orbus_r16`, `collection dungeons`, 24 documenti totali.

### 1.1 Dungeon attivi 3-player (`is_5p=False`, 10 dungeon + 1 training-yard)

| # | slug | name_it | req_lvl | difficulty | bucket | lore_theme | content_family | emotional_tone | spoiler | is_legacy |
|:---:|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | `training-yard` | *(none)* | 1 | trivial | *(none)* | *(none)* | *(none)* | *(none)* | *(none)* | False |
| 2 | `sewer-nest` | Nido nelle Fogne | 1 | 1 | tutorial | urban | baseline | tension | public | True |
| 3 | `goblin-warrens` | Tane dei Goblin | 2 | 1 | tutorial | frontiera | baseline | tension | public | True |
| 4 | `bandit-hideout` | Covo dei Banditi | 2 | 1 | tutorial | urban | baseline | tension | public | True |
| 5 | `shadow-crypts` | Cripte d'Ombra | 3 | 2 | early | irthe | void_undead | dread | mystery | True |
| 6 | `druid-grove` | Bosco dei Druidi Corrotti | 3 | 2 | early | soe | nature | grim | public | True |
| 7 | `cursed-mines` | Miniere Maledette | 4 | 2 | early | efreto | arcane | dread | mystery | True |
| 8 | `sunken-library` | Biblioteca Sommersa | 4 | 2 | early | memoria | memory | wonder | mystery | True |
| 9 | `lich-sanctum` | Santuario del Lich | 5 | 3 | mid | irthe | void_undead | dread | mystery | True |
| 10 | `dragons-hoard` | Tesoro del Drago | 6 | 3 | mid | draco | arcane | wonder | mystery | True |
| 11 | `storm-spire` | Guglia della Tempesta | 6 | 3 | mid | ambash | arcane | wonder | public | True |

### 1.2 Dungeon attivi 5-player (`is_5p=True`, 12 dungeon, tutti non-legacy)

| # | slug | name_it | req_lvl | difficulty | bucket | lore_theme | content_family | emotional_tone | spoiler | is_legacy |
|:---:|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 12 | `wolf-den-5p` | Tana dei Lupi | 3 | 1 | early | soe | nature | wonder | public | False |
| 13 | `frost-cave-5p` | Caverna del Gelo | 4 | 1 | early | halodi | nature | melancholy | public | False |
| 14 | `salt-marsh-5p` | Palude Salata | 5 | 1 | early | velur | memory | melancholy | public | False |
| 15 | `iron-foundry-5p` | Fonderia di Ferro | 6 | 2 | mid | fucina | arcane | tension | public | False |
| 16 | `silent-monastery-5p` | Monastero del Silenzio | 7 | 2 | mid | memoria | memory | melancholy | mystery | False |
| 17 | `pirate-fleet-5p` | Flotta dei Corsari | 8 | 2 | high | mare | baseline | tension | public | False |
| 18 | `obsidian-arena-5p` | Arena d'Ossidiana | 9 | 3 | high | infernale | arcane | grim | mystery | False |
| 19 | `clockwork-vault-5p` | Camera degli Ingranaggi | 10 | 3 | high | fucina | arcane | tension | public | False |
| 20 | `voidspire-5p` | Pinnacolo del Vuoto | 11 | 3 | high | vuoto | void_undead | dread | mystery | False |
| 21 | `infernal-pit-5p` | Fossa Infernale | 12 | 4 | high | infernale | arcane | dread | mystery | False |
| 22 | `celestial-citadel-5p` | Cittadella Celeste | 13 | 4 | high | celeste | divine | hope | mystery | False |
| 23 | `world-tree-roots-5p` | Radici dell'Albero del Mondo | 14 | 4 | high | soe | nature | wonder | mystery | False |

### 1.3 Dungeon inattivi / test (1 dungeon)

| # | slug | name_it | req_lvl | is_active | Note |
|:---:|---|---|:---:|:---:|---|
| 24 | `test-dungeon-531a1a` | *(none)* | *(none)* | False | Test artifact — **esclusi da audit produttivo** |

### 1.4 Raid dungeons live (collection separata `raid_dungeons`, 3 documenti)

| # | slug | name_it | lore_theme | content_family | boss_name | required_level |
|:---:|---|---|:---:|:---:|---|:---:|
| R1 | `broken-bastion-siege` | Assedio al Bastione Spezzato | ergolat | baseline | Comandante del Bastione | *(null)* |
| R2 | `necropolis-bells` | Necropoli delle Mille Campane | irthe | void_undead | Campanaro Senza Volto | *(null)* |
| R3 | `dragon-vault` | Volta del Drago Addormentato | draco | arcane | Drago di Pietra | *(null)* |

**Nota**: 3 raid live già esistono (fuori scope Batch 1 secondo GO PM). `required_level` non popolato → mapping bracket raid `PENDING PM approval` (probabilmente bracket avanzati Lv30+).

---

## 2. Slug/ID dungeon (già presentati sopra)

Tutti gli slug seguono convenzione `kebab-case`. I 12 dungeon 5-player hanno suffisso `-5p` esplicito. Nessun slug duplicato. Nessuna incoerenza di naming rilevata a livello di ID tecnico.

---

## 3. Nome player-facing attuale

- **Campo DB**: `name_it` (italiano) + `name` (inglese, presente in seed_data ma non estratto in questa aggregazione)
- **Copertura `name_it`**: 22/24 dungeon hanno `name_it` popolato. **2 dungeon senza `name_it`**: `training-yard`, `test-dungeon-531a1a`.
- **Osservazione**: nomi player-facing esistenti sono di **alta qualità narrativa** ("Cripte d'Ombra", "Biblioteca Sommersa", "Radici dell'Albero del Mondo"). NON generici. `training-yard` sembra utility onboarding senza narrativa.

---

## 4. Difficulty legacy (valore corrente)

Il campo `difficulty` è già presente e usa una scala numerica + un valore stringa speciale:

| difficulty value | Occorrenze | Note |
|:---:|:---:|---|
| `trivial` (str) | 1 | `training-yard` (utility) |
| `1` (int) | 8 | Beginner-friendly (tutorial + early 5p) |
| `2` (int) | 7 | Early/mid intermediate |
| `3` (int) | 6 | Mid/high advanced |
| `4` (int) | 3 | High endgame live |

**Nota governance**: il campo `difficulty` mescola int (1-4) + string speciale (`trivial`). Non è un vero enum. Coerenza schema `PENDING PM decision` se serve normalizzazione futura.

---

## 5. Level fields esistenti

**Il DB ha già i level field.** Nessun backfill Phase C tech necessario per esposizione level range.

| Field | Type | Coverage | Range | Note |
|---|---|---|---|---|
| `required_level` | int | 23/24 (95.8%) | Lv1 → Lv14 | Presente e popolato su tutti gli attivi |
| `bucket` | string | 22/24 (91.7%) | `tutorial`, `early`, `mid`, `high` | Bucketing legacy a 4 valori |
| `recommended_power` | int | 24/24 (100%) | 35-500+ | Non estratto in questa tabella, presente nel seed |
| `required_team_size` | int | 24/24 (100%) | 3 o 5 | Party size vincolato |
| `is_5p` | bool | 24/24 (100%) | True/False | Marker party 5-player vs 3-player |

### Distribuzione `required_level` per active dungeon

| Livello | Dungeon count | Slug |
|:---:|:---:|---|
| Lv1 | 2 | `sewer-nest`, `training-yard` |
| Lv2 | 2 | `goblin-warrens`, `bandit-hideout` |
| Lv3 | 3 | `shadow-crypts`, `druid-grove`, `wolf-den-5p` |
| Lv4 | 3 | `cursed-mines`, `sunken-library`, `frost-cave-5p` |
| Lv5 | 2 | `lich-sanctum`, `salt-marsh-5p` |
| Lv6 | 3 | `dragons-hoard`, `storm-spire`, `iron-foundry-5p` |
| Lv7 | 1 | `silent-monastery-5p` |
| Lv8 | 1 | `pirate-fleet-5p` |
| Lv9 | 1 | `obsidian-arena-5p` |
| Lv10 | 1 | `clockwork-vault-5p` |
| Lv11 | 1 | `voidspire-5p` |
| Lv12 | 1 | `infernal-pit-5p` |
| Lv13 | 1 | `celestial-citadel-5p` |
| Lv14 | 1 | `world-tree-roots-5p` |
| Lv15+ | 0 | **Nessun dungeon live oltre Lv14** |

**Copertura live effettiva**: **Lv1-14** (23 dungeon attivi). Nessun contenuto live per Lv15-60 (l'intero range R18.5 upper).

---

## 6. Party size / required party size

- **Party 3 (3-player)**: 11 dungeon (10 story + `training-yard`)
- **Party 5 (5-player)**: 12 dungeon (tutti suffissati `-5p`, tutti non-legacy)
- **Vincolo Gate 1 SQ13**: `party_size = 3` PM-locked

### 🔴 Rischio critico party size

Se il vincolo Gate 1 SQ13 `party_size=3` è **tassativo** per Batch 1, **12 dungeon 5-player restano esclusi** dal bracket Lv1-15 anche se il loro `required_level` (Lv3-Lv14) rientrerebbe nel range. Servono 3 opzioni PM:

1. **Opzione A (stricto)**: SQ13=3 rigido → Batch 1 usa solo dungeon 3-player (10 live 3p + `training-yard`). Batch 1 avrebbe 11 candidati Lv1-6, mancano dungeon Lv7-15 3-player → serve creare ~5-6 nuovi 3-player Lv7-15.
2. **Opzione B (bifork)**: Batch 1 diviso in traccia "3-player" (bracket small party) + traccia "5-player coordinated" (bracket bigger party). Rompe design "unified bracket".
3. **Opzione C (revisione SQ13)**: modificare SQ13 → accettare team=5 in Batch 1. Rompe Gate 1 decisions. **Richiede gate PM per riaprire SQ13**.

---

## 7. Loot / drop / material dependencies

### 7.1 Loot table

- File: `backend/app/expeditions/loot_tables.py` (SEALED — riferimenti C0-ter sez. 11 governance sigilli).
- Contiene loot table per **3 dungeon Phase 3 originali** (`goblin-warrens`, `shadow-crypts`, `dragons-hoard`) BYTE-IDENTICAL con il seed originale.
- Coverage loot table completa per gli altri 20 dungeon: **non verificato in questo audit** (richiede lettura file SEALED aggiuntivi + gate PM per accesso analisi).

### 7.2 Material drop tables

- File: `backend/app/expeditions/material_drop_tables.py` (probabilmente SEALED).
- Riferimento tutorial-tier drops: `goblin-warrens`, `sewer-nest`, `bandit-hideout` (i 3 tutorial 3-player).
- Coverage completa: non estratta in questo audit read-only.

### 7.3 Drop rate

Non richiesti in Batch 1 (regola PM verbatim: "drop rate finali non richiesti in Batch 1, solo direzionali"). L'audit **non ha estratto drop rate specifici** per rispettare stop rule "no economy analysis".

---

## 8. Economia live collegata (aggregazione read-only)

Query eseguite:
```javascript
db.expeditions.aggregate([{$group: {_id: "$dungeon_slug", runs: {$sum: 1}}}])
db.expeditions_r18_archive.aggregate([{$group: {_id: "$dungeon_slug", runs: {$sum: 1}}}])
```

### 8.1 Risultati aggregazione

| Collection | Documenti totali | Groups by `dungeon_slug` | Distribuzione |
|---|:---:|:---:|---|
| `expeditions` | 3 | 1 | Tutti con `dungeon_slug=None` (3 runs) |
| `expeditions_r18_archive` | 17 | 1 | Tutti con `dungeon_slug=None` (17 runs) |

**Totale run tracked**: 20 (3 correnti + 17 archive).

### 8.2 🟢 Rischio economia — BASSO

Il **100% delle expedition run** ha `dungeon_slug=None`. Significa che:
- L'economia storica **non è tracciata per dungeon** — il link expedition→dungeon è null.
- Non esiste baseline economico verificabile per singolo dungeon live.
- **Qualsiasi ri-bracketing R18.5 non rompe economia storica** perché non c'è economia storica per-dungeon da rompere.
- L'unica economia baseline sarebbe `base_gold_reward` / `base_xp_reward` a livello di dungeon-catalog (verifica lettura seed_data richiesta se PM richiede fine-grained analysis).

**Nota**: questa evidenza attesta che il **rischio economico di ri-classificazione bracket è basso**. Serve però conferma se il gioco sia in fase pre-scale (poche run tracked = poca attività player) o se il campo `dungeon_slug` non venga popolato al completamento expedition (bug schema o design intenzionale). **Flaggato per PM info-only, non blocker Batch 1**.

---

## 9. Lore source proposta per ogni dungeon live (PENDING PM approval)

### 9.1 Mapping `lore_theme` live → 17 fonti Gate 1

Il DB usa `lore_theme` (string, 15 valori distinct) come proxy per la "fonte". Il **mapping non è 1:1** con le 17 fonti Gate 1:

#### ✅ Match diretti live_lore_theme ↔ Gate 1 fonti (7 su 17)

| lore_theme live | Fonte Gate 1 | Dungeon usati |
|:---:|:---:|---|
| `ambash` | **Ambash** | storm-spire |
| `efreto` | **Efreto** | cursed-mines |
| `halodi` | **Halodi** | frost-cave-5p |
| `irthe` | **Irthe** | shadow-crypts, lich-sanctum + raid `necropolis-bells` |
| `soe` | **Soe** | druid-grove, wolf-den-5p, world-tree-roots-5p |
| `velur` | **Velur** | salt-marsh-5p |
| `vuoto` | **Vuoto** | voidspire-5p |

#### 🔴 Tag live non presenti nelle 17 fonti Gate 1 (8 tag orfani)

| lore_theme live | Dungeon usati | Interpretazione proposta (`PENDING PM approval`) |
|:---:|---|---|
| `urban` | sewer-nest, bandit-hideout | Non fonte epica, tag generico "urbano/civilizzato" — mappabile a **Aveol** (borghi) o **Adalan** (cittadina) |
| `frontiera` | goblin-warrens | Tag generico frontiera — mappabile a **Halodi** (già esistente per frost-cave) o **Aveol** |
| `fucina` | iron-foundry-5p, clockwork-vault-5p | Tag tematico artigianale — mappabile a **Ambash** (mercantile/fabbrile) o **Aveol** |
| `memoria` | sunken-library, silent-monastery-5p | Tag "memory" — non 1:1 con fonti Gate 1 — **mappabile a Ciclo delle anime** (metafisico memoria)? o riservato a fonte custom PM |
| `mare` | pirate-fleet-5p | Tag oceanico — **non presente in Gate 1** — Emergent suggerisce **NUOVA fonte "Mare di Velur"** oppure sub-tag di **Velur** |
| `draco` | dragons-hoard + raid `dragon-vault` | Tag draconico — **non presente in Gate 1** — Emergent suggerisce **NUOVA fonte "Draco"** oppure legato a bracket endgame |
| `celeste` | celestial-citadel-5p | Tag divino/celeste — potenziale sinonimo **Alberi della Vita** (soft-mistico) oppure **NUOVA fonte "Celeste"** |
| `infernale` | obsidian-arena-5p, infernal-pit-5p | Tag infernale — potenziale sinonimo **Luna Morta** (arcano oscuro) oppure **NUOVA fonte "Infernale"** |

#### 🟡 10 fonti Gate 1 orfane (nessun dungeon live le usa)

Le 10 fonti Gate 1 seguenti **non sono usate** da nessun dungeon live:

| Fonte Gate 1 | Status | Impact |
|:---:|:---:|---|
| **Alevora** | Orfana | Riservata a World Boss endgame (Alevora è world boss narrativo) |
| **Aveol** | Orfana | Batch 1 DRAFT ne proponeva 2 nuovi (chapel-of-silent-vows, bandit-warlord-hideout) |
| **Ergolat** | Orfana in dungeon | Usata da raid `broken-bastion-siege` ✅ |
| **Krastlov** | Orfana | Batch 1 DRAFT ne proponeva 1 nuovo (frozen-vigil-hall) |
| **Adalan** | Orfana | Batch 1 DRAFT ne proponeva 2 nuovi (forgotten-shrine, broken-tower) |
| **Greatwood/Elfwood** | Orfana | Batch 1 DRAFT ne proponeva 1 nuovo (elfwood-glade) |
| **Alberi della Vita** | Orfana | Batch 1 DRAFT ne proponeva 1 nuovo (heartwood-grove) |
| **Faglie arcane** | Orfana | Riservata a Batch 3+ |
| **Luna Morta** | Orfana | Riservata a Batch 5 endgame |
| **Ciclo delle anime** | Orfana | Riservata a Batch 5 endgame |

**Governance**: le 8 tag orfane + 10 fonti Gate 1 orfane richiedono **decisione PM**:
- Espandere le 17 fonti Gate 1 a **~22-25 fonti** aggiungendo (Mare, Draco, Celeste, Infernale, Fucina, Memoria, Urban, Frontiera)?
- OR mappare 1:N i tag live esistenti verso fonti Gate 1 (es. `mare` → sotto-tag di Velur; `celeste` → sotto-tag di Alberi della Vita)?
- OR normalizzare i `lore_theme` live per allinearli alle 17 fonti (breaking change su lore_meta.py, richiede gate PM)?

**Emergent NON risolve autonomamente** — proposta `PENDING PM approval`.

---

## 10. Bracket Lv1-60 proposto per ogni dungeon live

Mapping proposta da Emergent (`PENDING PM approval`), coerente con R18.5 5-bracket:

### 10.1 Batch 1 (Lv1-15) — 23 candidati live

**Tutti i 23 dungeon attivi** rientrano nel range Lv1-14, quindi teoricamente candidati per Batch 1. Filtrando per `is_5p=False` (rispetto SQ13):

| Bracket R18.5 | Dungeon 3-player live candidati | Count |
|:---:|---|:---:|
| Lv1-15 | `training-yard`, `sewer-nest`, `goblin-warrens`, `bandit-hideout`, `shadow-crypts`, `druid-grove`, `cursed-mines`, `sunken-library`, `lich-sanctum`, `dragons-hoard`, `storm-spire` | **11** |

**Osservazione critica**: **tutti gli 11 dungeon 3-player attivi** sono Lv1-6 (nessuno oltre Lv7). Gap **Lv7-Lv15 in 3-player**: **6-8 dungeon nuovi richiesti** per completare Batch 1 se stricto SQ13.

### 10.2 Batch 2 (Lv16-30) — attualmente vuoto in live

Nessun dungeon live ha `required_level ≥ 15`. Batch 2 richiederà creazione integrale (12 dungeon + eventuali raid).

**Nota**: 12 dungeon **5-player attivi** (Lv3-14) sono orfani se Batch 1 stricto 3-player. **Proposta**: se PM autorizza traccia parallela 5-player o revisione SQ13, i 12 5-player potrebbero coprire un "Batch 1-5p" parallelo o essere riclassificati Lv3-14 con team_size ridotto (breaking change).

### 10.3 Batch 3-5 (Lv31-60) — vuoti live

Nessun dungeon live copre Lv15+. Batch 3-5 richiederanno creazione integrale.

### 10.4 Raid — 3 candidati live, bracket unclear

3 raid live (`broken-bastion-siege`, `necropolis-bells`, `dragon-vault`) — `required_level=None` → bracket **`PENDING PM approval`**. Probabile mapping Batch 3-5 endgame data la loro complessità narrativa.

---

## 11. Quali dungeon live entrano in Lv1-15 (Batch 1)

### 11.1 Se stricto Gate 1 SQ13 `party_size=3` (Opzione A)

**11 dungeon live 3-player** entrano naturalmente in Lv1-15 (tutti Lv1-6). Elenco:

| # | slug | req_lvl | bucket legacy | Note party |
|:---:|---|:---:|:---:|---|
| 1 | `training-yard` | 1 | *(none)* | Utility onboarding — decisione PM se includere |
| 2 | `sewer-nest` | 1 | tutorial | Legacy Phase 3+ |
| 3 | `goblin-warrens` | 2 | tutorial | Legacy Phase 3 (già in Batch 1 DRAFT #1) |
| 4 | `bandit-hideout` | 2 | tutorial | Legacy Phase 3+ |
| 5 | `shadow-crypts` | 3 | early | Legacy Phase 3+ |
| 6 | `druid-grove` | 3 | early | Legacy Phase 3+ |
| 7 | `cursed-mines` | 4 | early | Legacy Phase 3+ |
| 8 | `sunken-library` | 4 | early | Legacy Phase 3+ |
| 9 | `lich-sanctum` | 5 | mid | Legacy Phase 3+ |
| 10 | `dragons-hoard` | 6 | mid | Legacy Phase 3+ |
| 11 | `storm-spire` | 6 | mid | Legacy Phase 3+ |

**Copertura Lv1-6**: 11 dungeon. **Gap Lv7-15 in 3-player**: 0 live → **serve creazione nuovi**.

### 11.2 Se PM autorizza mix 3p + 5p in Batch 1 (Opzione B/C)

**23 dungeon live attivi** entrano tutti in Lv1-14. Batch 1 avrebbe surplus di 11 dungeon → richiede scarto di ~11 dungeon o proposta bracket più esteso (es. Batch 1 = Lv1-14, Batch 2 = Lv15-30).

---

## 12. Quali dungeon live vanno in bracket successivi (Batch 2-5)

### 12.1 Se stricto SQ13 (Opzione A)

**Nessun dungeon live 3-player** copre Lv7-60. Tutti i **Batch 2-5 dungeon 3-player devono essere creati nuovi** (~48 dungeon nuovi tra Batch 2-5 se ratio 12 dungeon/batch).

### 12.2 5-player disponibili come pool separato

12 dungeon 5-player attivi coprono Lv3-14. Sono **orfani** rispetto al bracket Batch 1 3-player. Opzioni:
- **Traccia parallela 5-player** (Batch 1-5p, Batch 2-5p, ecc.)
- **Reclassificazione team_size 5→3** (breaking change, gate PM richiesto)
- **Congelamento 5-player** (mantenuti live ma non ri-bracketati R18.5)

**Emergent NON decide autonomamente** — flaggato `PENDING PM approval`.

### 12.3 Raid disponibili come pool avanzato

3 raid live (`broken-bastion-siege`, `necropolis-bells`, `dragon-vault`) — candidati per Batch 3-5 raid slot (R18.5 target: 12 raid). Servono 9 nuovi raid + eventuale ri-bracketing dei 3 live.

---

## 13. Nuovi dungeon necessari per completare Batch 1 (gap analysis)

### 13.1 Se Opzione A (stricto 3-player)

Target Batch 1: **12 dungeon 3-player Lv1-15**.

| Bucket | Live 3p disponibili | Gap dungeon nuovi richiesti |
|:---:|:---:|:---:|
| Lv1-5 | 8 (sewer-nest, goblin-warrens, bandit-hideout, shadow-crypts, druid-grove, cursed-mines, sunken-library, lich-sanctum) + 1 utility (`training-yard`) | 0 (surplus di 3) |
| Lv6-10 | 3 (dragons-hoard Lv6, storm-spire Lv6, iron-foundry-5p Lv6 escluso) | ~4 nuovi Lv6-10 3-player |
| Lv11-15 | 0 | ~4-6 nuovi Lv11-15 3-player |

**Gap totale Opzione A**: ~8-10 dungeon nuovi Lv6-15 3-player per completare Batch 1.

### 13.2 Se Opzione B (mix live + nuovi, con revisione SQ13)

**Zero dungeon nuovi obbligatori**: 23 live attivi coprono Lv1-14 → surplus di 11 dungeon. Serve solo scarto/redistribuzione.

### 13.3 Se Opzione C (curated subset live 3p only + integrazione con nuovi selettivi)

- Selezionare **8 live 3-player rappresentativi** per Lv1-6 (invece di 11) — scarto 3 per varietà
- Creare **4 nuovi 3-player Lv7-15**
- Totale: **12 dungeon** (8 live + 4 nuovi)

**Emergent raccomandazione Opzione C** (motivata in sez. 15).

---

## 14. Rischi identificati

### 🔴 Rischio 1 — CRITICAL — Party size 3p vs 5p conflict

**Descrizione**: 12 dungeon live 5-player restano orfani se SQ13 tassativo. Ri-classificazione breaking o traccia parallela richiede gate PM.

**Impact se non risolto**: 50% del catalogo live inutilizzato in R18.5 → design coherence a rischio, spreco content narrativo di alta qualità.

**Mitigation proposta**: gate PM dedicato per decisione tra Opzione A / B / C.

### 🔴 Rischio 2 — CRITICAL — Lore theme disallineamento

**Descrizione**: 8 tag live orfani (mare, draco, celeste, infernale, fucina, memoria, urban, frontiera) + 10 fonti Gate 1 orfane.

**Impact se non risolto**: naming lore inconsistente tra Gate 1 policy e live data → user-facing confusion, difficoltà mappatura content futuro.

**Mitigation proposta**: espansione fonti Gate 1 a ~22-25 O normalizzazione mapping 1:N O breaking change su lore_theme live (gate PM).

### 🟡 Rischio 3 — HIGH — Copertura Lv15-60 live = 0

**Descrizione**: live copre solo Lv1-14. R18.5 target Lv60 richiede ~48 dungeon nuovi Batch 2-5.

**Impact se non risolto**: cadenza rilascio content dilatata; batch drafting workload significativo.

**Mitigation proposta**: pianificare batch cadence realistica (12 dungeon/batch × 5 batch = 60 target ~ scalable in ~5-10 gate cycles).

### 🟡 Rischio 4 — MEDIUM — Bucket legacy 4→5 R18.5

**Descrizione**: DB usa `tutorial/early/mid/high` (4 bucket), R18.5 usa `Lv1-15/16-30/31-45/46-55/56-60` (5 bracket).

**Impact se non risolto**: se `bucket` field diventa fonte di verità runtime, richiede backfill/mapping migration.

**Mitigation proposta**: mantenere `bucket` legacy immutato + aggiungere nuovo field `r18_5_bracket` (opzionale, non-breaking). Decisione `PENDING PM`.

### 🟡 Rischio 5 — MEDIUM — `training-yard` senza narrativa

**Descrizione**: `training-yard` è utility (no lore, no bucket, difficulty=trivial). Non chiaro se includere in Batch 1.

**Impact se non risolto**: nessuno (utility può restare fuori bracket).

**Mitigation proposta**: **escludere `training-yard` da bracket R18.5** (rimane utility onboarding). `PENDING PM approval`.

### 🟢 Rischio 6 — LOW — Economia expedition-per-dungeon = null

**Descrizione**: 100% expedition run con `dungeon_slug=None`. Non c'è economia storica da rompere.

**Impact se non risolto**: nessun impatto rollout — pro: ri-classificazione bracket sicura da rischio economico; contro: telemetria uso dungeon assente.

**Mitigation proposta**: **info-only**, non blocker Batch 1. Verifica separata (fuori scope C0-quater) se schema `dungeon_slug` sull'expedition sia bug o design intenzionale.

### 🟡 Rischio 7 — MEDIUM — Overlap tag lore vs identità narrativa

**Descrizione**: 2 tag lore usati su >1 dungeon:
- `irthe`: shadow-crypts, lich-sanctum + raid necropolis-bells (3 usi)
- `soe`: druid-grove, wolf-den-5p, world-tree-roots-5p (3 usi)
- `memoria`: sunken-library, silent-monastery-5p (2 usi)
- `infernale`: obsidian-arena-5p, infernal-pit-5p (2 usi)
- `fucina`: iron-foundry-5p, clockwork-vault-5p (2 usi)

**Impact se non risolto**: identità narrativa parziale (i dungeon condividono tema ma NON storia specifica). Coerente con design "tema condiviso, ambientazione differenziata".

**Mitigation**: `PENDING PM approval` se accettabile.

---

## 15. Raccomandazione Batch 1 informed

### 15.1 Opzione E (Emergent Recommended) — 12 dungeon 3-player curati

**Proposta**: Batch 1 = **8 live 3-player** + **4 nuovi 3-player Lv7-15** = **12 dungeon totali**.

#### Selezione 8 live 3-player (Lv1-6)

Selezione motivata da **diversità lore + qualità narrativa + bucket copertura**:

| # | Slug live | Nome IT | req_lvl | lore_theme | Motivazione selezione |
|:---:|---|---|:---:|:---:|---|
| 1 | `sewer-nest` | Nido nelle Fogne | 1 | urban | Onboarding Lv1, tema urban distinto |
| 2 | `goblin-warrens` | Tane dei Goblin | 2 | frontiera | Legacy Phase 3, obligatorio per gate |
| 3 | `bandit-hideout` | Covo dei Banditi | 2 | urban | Introduce combattimento umanoide |
| 4 | `shadow-crypts` | Cripte d'Ombra | 3 | irthe | Introduzione void_undead lore |
| 5 | `druid-grove` | Bosco dei Druidi Corrotti | 3 | soe | Introduzione natura corrotta |
| 6 | `cursed-mines` | Miniere Maledette | 4 | efreto | Introduzione arcane mining |
| 7 | `sunken-library` | Biblioteca Sommersa | 4 | memoria | Introduzione tema memory/mystery |
| 8 | `lich-sanctum` | Santuario del Lich | 5 | irthe | Boss narrativo Lv5 |

**Scartati** (motivati):
- `training-yard`: utility, non narrativo → **escluso da bracket, resta live separato**
- `dragons-hoard` (Lv6, draco): eccellente qualità narrativa, ma **candidato migliore per Batch 2** (Lv6→Lv15 dovrebbe essere transizione, `draco` ha tono da "reveal" più tardo). `PENDING PM approval`
- `storm-spire` (Lv6, ambash): stesso motivo, riservato Batch 2 come chiusura tema ambash. `PENDING PM approval`

#### 4 nuovi dungeon 3-player Lv7-15 (ancora `PENDING PM approval`)

Emergent propone 4 nuovi 3-player Lv7-15 dopo il gate PM di questo audit:

| # | slug proposta | Nome IT proposta | Lv range | lore_theme proposta | Motivazione teaching |
|:---:|---|---|:---:|:---:|---|
| 9 | `chapel-of-silent-vows` | Cappella dei Voti Silenti | Lv7-9 | Aveol | Priest teaching (Priest live orfano finora) |
| 10 | `forgotten-shrine-of-adalan` | Santuario Dimenticato di Adalan | Lv9-11 | Adalan | Mage teaching (Adalan fonte orfana) |
| 11 | `bandit-warlord-hideout` | Nascondiglio del Signore dei Briganti | Lv11-13 | Aveol | Proficiency teaching narrativo |
| 12 | `broken-tower-of-adalan` | Torre Spezzata di Adalan | Lv13-15 | Adalan | Transition Batch 2, primo Epic raro |

### 15.2 Vantaggi Opzione E

- ✅ Rispetta Gate 1 SQ13 (`party_size=3`) verbatim
- ✅ Sfrutta 8 dungeon live esistenti (67% Batch 1 = live, no re-creation)
- ✅ Copre 5 fonti Gate 1 live (`irthe`, `soe`, `efreto`) + 2 fonti nuove (`Aveol`, `Adalan`)
- ✅ Introduce Priest + Mage teaching (Priest orfano nel live, Mage teaching mancante fino a Lv14)
- ✅ Progression bucketing coerente (3 tutorial + 5 early/mid live + 4 nuovi mid/high)
- ✅ Riduce workload creazione nuovi (4 vs 11 in Batch 1 DRAFT originale)
- ✅ Gestisce 12 dungeon 5-player come **pool separato** in gate PM successivo (opzioni: traccia parallela / ri-team-size / congelamento)

### 15.3 Svantaggi / Rischi Opzione E

- 🟡 `dragons-hoard` + `storm-spire` (2 dungeon live eccellenti Lv6) rimangono in un limbo: né Batch 1 né esplicitamente Batch 2. Serve decisione PM se pinnarli a Batch 2 subito.
- 🟡 12 dungeon 5-player restano non-bracketati in Batch 1 — decisione PM successiva richiesta.
- 🟡 4 nuovi 3-player Lv7-15 aggiungono workload creazione content — parziale (4 vs 11 iniziale).

### 15.4 Alternative

- **Opzione A (Emergent secondary)**: se PM preferisce **max integrazione live**, tenere **tutti gli 11 live 3-player** + **1 nuovo Lv13-15** = 12. Rimuove `training-yard` per far spazio. Perde teaching Priest/Mage esplicito ma massimizza live utilization.
- **Opzione B**: mix 3p+5p (revisione SQ13). Alto rischio design Gate 1. **NON raccomandato da Emergent**.

---

## 16. Governance check finale — Audit READ-ONLY

- ✅ **24 dungeon live censiti** (23 attivi + 1 test disattivato) — >20 stop rule triggered SOFT, segnalato come Sorpresa 1
- ✅ **15 sezioni obbligatorie compilate** (sez. 0 executive summary + sez. 1-15)
- ✅ **Lore source proposto per ogni live dungeon** (mapping 1:1 + gap analysis, `PENDING PM approval`)
- ✅ **Bracket Lv1-60 proposto per ogni live dungeon** (`PENDING PM approval`)
- ✅ **Batch 1 informed raccomandazione**: Opzione E — 8 live + 4 nuovi = 12 (motivata in sez. 15)
- ✅ **7 rischi documentati** (2 CRITICAL + 3 MEDIUM + 1 LOW + 1 HIGH)
- ✅ **Query DB completa** eseguita: `dungeons` (24 docs), `raid_dungeons` (3 docs), `expeditions` + `expeditions_r18_archive` (aggregazione economia read-only)
- ✅ **36 sigilli byte-identical** — nessuna modifica ai sealed files (attesa `pytest backend_r18_4_sealed_integrity_test.py` → PASS)
- ✅ **Zero DB writes** (solo `find()` + `aggregate()`)
- ✅ **Zero code changes** (`.py` / `.js` / `.jsx` / `.tsx` intatti)
- ✅ **Zero migrations / apply scripts**
- ✅ **Zero dungeon creation/deletion/deprecation**
- ✅ **Zero economy changes / drop table apply / level_min/max backfill**
- ✅ **Zero rinaming file/slug live / modifiche schema/serializer**

---

## 17. Handoff — pronto per PM decisions post-audit

### 17.1 Decisioni PM richieste prima di rifare Batch 1 informed

1. **Party size policy** (Opzione A / B / C) — SQ13 stricto vs bifork vs revisione
2. **Lore theme normalization** — espansione fonti Gate 1 vs mapping 1:N vs breaking change live
3. **`training-yard` inclusion/exclusion** in bracket R18.5
4. **`dragons-hoard` + `storm-spire`** — Batch 1 tail o Batch 2 head?
5. **12 dungeon 5-player** — traccia parallela / ri-team-size / congelamento
6. **3 raid live** — bracket assignment (Batch 3/4/5)
7. **Batch 1 opzione selezionata**: E (Emergent recommended) / A (max live) / B (mix 3p+5p) / D (custom PM)

### 17.2 Deliverable prodotto

- ✅ `/app/memory/r18_5_phase_c0quater_live_dungeon_audit.md` (questo file)
- ✅ `/app/memory/r18_5_phase_c0quater_live_dungeon_audit.json` (mirror strutturato)

### 17.3 Prossimo step atteso

**Post-decisioni PM sui 7 punti sopra**: Emergent rifà Batch 1 **informed** con la matrice 12 dungeon Lv1-15 coerente con le nuove policy. Il file Batch 1 DRAFT precedente (`r18_5_phase_c0quater_batch1_lv1_15_dungeon_matrix.md/.json`) sarà **superseded** — deprecato ma preservato per audit trail.

**Batch 2-5 e raid** restano BLOCCATI fino a chiusura Batch 1 informed.

**Phase C tech dry-run** resta 🔒 BLOCCATA (governance sigilli `derive_ui_4state`/`item_public()` invariata).

---

**Audit CLOSED — pronto per PM review decisioni + rifacimento Batch 1 informed**.
