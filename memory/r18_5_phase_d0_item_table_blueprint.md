# R18.5 Phase D0 — Item Table Schema + 1500 Distribution Blueprint (STEP 9)

**Round**: R18.5 — Itemization, ILVL & Gear Progression Rework
**Phase**: D0 — Schema + 1500 Blueprint (NON catalogo completo)
**Locked at (UTC)**: 2026-07-07T11:30:00Z
**Governance**: DOCUMENTAL ONLY
**Status**: DRAFT — 15 sezioni schema + blueprint distributivo, item finals PENDING D1-D5
**Authority**: PM Orchestrator — Q21 D→B verbatim (skip Phase C tech dry-run)
**Scope**: schema tabella item finale + distribuzione strategica 1500 item (T1×300, T2×350, T3×350, T4×300, T5×200)

---

## Executive Summary

Phase D0 definisce lo **schema strutturale finale** della tabella item R18.5 e il **blueprint distributivo** dei 1500 item pianificati. **Non genera** ancora gli item finali — è il pre-requisito per Phase D1-D5 (drafting per tier). Il blueprint copre 15 sezioni obbligatorie: schema, campi, distribuzioni per tier/rarity/slot/armor-type/weapon-family/dungeon-source/crafting/legendary/signature/proficiency/main-stat + Open Questions per D1.

---

## Sezione 1 — Schema finale tabella item

**Collection MongoDB target (design only, non creata)**: `items_r18_5` (o namespace equivalente da definire in D1).

### Struttura documento item (blueprint)

```
{
  "item_id": string (uuid4),
  "item_slug": string (kebab-case, unique),
  "name_it": string,
  "name_en": string (opzionale),
  "description": string,
  "utility_text": string,

  "slot_type": enum ["head", "chest", "legs", "hands", "feet", "main-hand", "off-hand", "ring", "amulet", "trinket", "consumable"],
  "item_type": enum ["armor", "weapon", "accessory", "consumable", "material", "quest", "cosmetic"],

  "rarity": enum ["common", "uncommon", "rare", "epic", "legendary"],
  "tier": int (1-5),
  "ilvl": int (1-60),

  "main_stat": enum ["STR", "AGI", "INT", "END", "FAI"],
  "secondary_stats": {stat: value, ...},

  "armor_type": enum ["light", "medium", "heavy"] | null (per non-armor),
  "weapon_family": enum ["sword", "dagger", "staff", "mace", "bow", "shield", "polearm", "wand", "hammer", "strumento", "falce", "trinket"] | null,

  "source_dungeon_slug": string | null,
  "source_raid_slug": string | null,
  "source_type": enum ["dungeon_drop", "raid_drop", "crafting", "achievement", "ranking", "quest", "world_boss", "vendor_special"],
  "lore_source": string (referenced from lore_meta),

  "class_proficiency": [enum "warrior", "rogue", "mage", "priest", "ranger"],
  "is_universal": bool,

  "drop_rate": float (0.0-1.0),

  "item_binding_policy": enum ["bind-on-pickup", "bind-on-equip", "unbound"],
  "is_tradeable": bool,
  "can_be_sold_for_gold": bool,
  "can_be_sold_for_real_money": bool,

  "is_cosmetic": bool,
  "affects_combat": bool,
  "affects_economy": bool,
  "affects_ranking": bool,

  "signature_capacity_slot": bool,

  "created_at_utc": string ISO,
  "updated_at_utc": string ISO
}
```

**Vincoli schema (design layer)**:
- `item_id` UUID4 string (public reference); mai esporre `_id` ObjectId
- `item_slug` UNIQUE index
- `rarity` derivato da `tier` via crosswalk (Sezione 5)
- `class_proficiency` array non vuoto (min 1 classe canonica)
- `is_universal = true` XOR `class_proficiency = [tutte 5]` — mutuamente esclusivi per semantica

---

## Sezione 2 — Campi obbligatori

Tutti i seguenti campi sono **NOT NULL** by design:

| Campo | Tipo | Vincolo |
|---|---|---|
| `item_id` | uuid4 string | UNIQUE |
| `item_slug` | string kebab | UNIQUE |
| `name_it` | string | 3-60 char |
| `slot_type` | enum | Sezione 6 |
| `item_type` | enum | armor/weapon/accessory/consumable/material/quest/cosmetic |
| `rarity` | enum | common..legendary |
| `tier` | int 1-5 | Coerente con rarity via crosswalk |
| `ilvl` | int 1-60 | Coerente con tier bracket |
| `main_stat` | enum | STR/AGI/INT/END/FAI |
| `armor_type` OR `weapon_family` | enum | Almeno uno valorizzato per gear |
| `source_type` | enum | Come sopra |
| `lore_source` | string | Referenced from lore_meta |
| `class_proficiency` | array | Min 1 |
| `is_universal` | bool | Default false |
| `item_binding_policy` | enum | bind-on-pickup/bind-on-equip/unbound |
| `is_tradeable` | bool | Coerente con binding |
| `can_be_sold_for_gold` | bool | |
| `can_be_sold_for_real_money` | bool | Anti-P2W R18 constraint |
| `is_cosmetic` | bool | |
| `affects_combat` | bool | |
| `affects_economy` | bool | |
| `affects_ranking` | bool | |
| `created_at_utc` | ISO string | datetime.now(timezone.utc) |
| `updated_at_utc` | ISO string | idem |

**Anti-P2W R18 rule (obbligatoria)**:
`can_be_sold_for_real_money = false` **automatico** se `affects_combat = true OR affects_economy = true OR affects_ranking = true`. Solo `is_cosmetic = true AND affects_combat = false AND affects_economy = false AND affects_ranking = false` può avere `can_be_sold_for_real_money = true`.

---

## Sezione 3 — Distribuzione 1500 item per TIER

| Tier | Level bracket | Item count | % catalog | Phase drafting |
|---|---|---:|---:|---|
| T1 | Lv1-15 (B1) | **300** | 20.0% | D1 |
| T2 | Lv16-30 (B2) | **350** | 23.3% | D2 |
| T3 | Lv31-45 (B3) | **350** | 23.3% | D3 |
| T4 | Lv46-55 (B4) | **300** | 20.0% | D4 |
| T5 | Lv56-60 (B5) | **200** | 13.3% | D5 |
| **TOTALE** | Lv1-60 | **1500** | 100.0% | D1-D5 |

**Rationale distribuzione**:
- T2/T3 mid-game hanno peso maggiore (349-350 item ciascuno) per copertura leveling più esteso
- T1 starter 300 item — bracket più corto ma diversità classe iniziale richiede volume
- T4 late-game 300 — bracket 10 livelli con Elite/Raid introduction
- T5 endgame 200 — bracket 5 livelli con focus qualità (Epic dominante + 15 Legendary cap total)

---

## Sezione 4 — Distribuzione 1500 item per RARITY

| Rarity | Item count | % catalog | Note |
|---|---:|---:|---|
| Common | 300 | 20.0% | Dominante T1, marginale T2 |
| Uncommon | 400 | 26.7% | Peso alto T1-T2, decrescente T3-T4 |
| Rare | 450 | 30.0% | Peso alto T2-T3, presente T4-T5 |
| Epic | 335 | 22.3% | Peso alto T4-T5, presente T3 |
| **Legendary** | **15** | **1.0%** | **CAP PM invariato** — solo T5 |
| **TOTALE** | **1500** | **100.0%** | |

**Legendary count breakdown**:
- 7 Legendary approved Batch 5 (Q13=A)
- 8 slot margine future gate PM (candidate discovery in Phase D5+)

---

## Sezione 5 — Crosswalk TIER × RARITY (matrice approvata)

| | T1 (300) | T2 (350) | T3 (350) | T4 (300) | T5 (200) | **Totale** |
|---|---:|---:|---:|---:|---:|---:|
| **Common** | 180 | 90 | 30 | 0 | 0 | **300** |
| **Uncommon** | 100 | 180 | 100 | 20 | 0 | **400** |
| **Rare** | 20 | 70 | 170 | 140 | 50 | **450** |
| **Epic** | 0 | 10 | 50 | 140 | 135 | **335** |
| **Legendary** | 0 | 0 | 0 | 0 | 15 | **15** |
| **TOTALE tier** | 300 | 350 | 350 | 300 | 200 | **1500** |

**Coerenza cross-tier**:
- Common presente solo T1-T3 (nessun Common endgame)
- Uncommon massimo T2 (peso starter esteso)
- Rare massimo T3-T4 (bracket più diffuso)
- Epic dominante T4-T5 (peso high-level)
- Legendary ESCLUSIVO T5 (PM strict verbatim)

---

## Sezione 6 — Distribuzione per SLOT

| Slot | Item count | % catalog |
|---|---:|---:|
| Head (helmet/circlet) | 130 | 8.7% |
| Chest (armor/robe) | 150 | 10.0% |
| Legs (leggings/pants) | 130 | 8.7% |
| Hands (gauntlets/gloves) | 120 | 8.0% |
| Feet (boots/shoes) | 120 | 8.0% |
| Main-hand (weapon) | 240 | 16.0% |
| Off-hand (shield/tome/orb) | 130 | 8.7% |
| Ring | 130 | 8.7% |
| Amulet | 120 | 8.0% |
| Trinket | 100 | 6.7% |
| Consumable | 80 | 5.3% |
| Material (crafting non-drop) | 50 | 3.3% |
| **TOTALE** | **1500** | **100.0%** |

**Nota**: main-hand weight più alto (16%) per varietà weapon families (12 famiglie incluse 3 backlog).

---

## Sezione 7 — Distribuzione per ARMOR TYPE

Armor totale = 650 item (head+chest+legs+hands+feet).

| Armor type | Item count | % armor | Coverage classi target |
|---|---:|---:|---|
| **Light** | 220 | 33.8% | Mage / Rogue (primary), Ranger (secondary) |
| **Medium** | 220 | 33.8% | Rogue / Ranger (primary), Priest (secondary) |
| **Heavy** | 210 | 32.3% | Warrior / Priest (primary) |

**Rationale**: distribuzione equilibrata per non favorire archetipi. Warrior/Priest heavy peso simile a Mage/Rogue light per non discriminare classi.

---

## Sezione 8 — Distribuzione per WEAPON FAMILY (240 main-hand + 130 off-hand = 370 weapon slot)

| Weapon family | Item count | % weapon | Class proficiency primaria |
|---|---:|---:|---|
| **Sword** | 55 | 14.9% | Warrior, Rogue |
| **Dagger** | 40 | 10.8% | Rogue |
| **Staff** | 45 | 12.2% | Mage, Priest |
| **Mace** | 40 | 10.8% | Priest, Warrior |
| **Bow** | 40 | 10.8% | Ranger |
| **Shield** (off-hand) | 60 | 16.2% | Warrior, Priest |
| **Polearm** | 30 | 8.1% | Warrior, Ranger |
| **Wand** | 25 | 6.8% | Mage, Priest |
| **Hammer** | 20 | 5.4% | Warrior |
| **Strumento** ⚠️ backlog | 5 | 1.4% | R18.P3 unassigned — PENDING |
| **Falce** ⚠️ backlog | 5 | 1.4% | R18.P3 unassigned — PENDING |
| **Trinket** (off-hand tome/orb) | 5 | 1.4% | Universal — PENDING |
| **TOTALE weapon** | **370** | **100.0%** | |

⚠️ Backlog: `strumento`, `falce`, `trinket` (3 unassigned da R18.P3) — mapping class proficiency **PENDING PM D1 Q**. Nel frattempo 15 slot totali riservati (5 per famiglia).

---

## Sezione 9 — Distribuzione per DUNGEON/RAID SOURCE

**Target**: mappa quanti item per ognuno dei 60 dungeon Normal 3p + 12 raid 5p + Elite 12 LIVE = 84 encounter live/design.

### 60 Normal Dungeon 3p — ~15 item medi per dungeon = ~900 item drop

| Bracket | Dungeon count | Item medi/dungeon | Sub-total |
|---|---:|---:|---:|
| T1 B1 (Lv1-15) | 12 | ~17 | ~200 |
| T2 B2 (Lv16-30) | 14 | ~15 | ~210 |
| T3 B3 (Lv31-45) | 16 | ~15 | ~240 |
| T4 B4 (Lv46-55) | 9 | ~17 | ~150 |
| T5 B5 (Lv56-60) | 9 | ~11 | ~100 |
| **TOTALE dungeon drop** | **60** | ~15 | **~900** |

### 12 Raid 5p — ~15 item medi per raid = ~180 item drop

- 3 LIVE (`broken-bastion-siege`, `necropolis-bells`, `dragon-vault`) — ~50 item
- 9 NEW DRAFT — ~130 item

### Elite 5p LIVE (fuori conteggio 60) — ~10 item medi = ~120 item drop parallel

### Non-drop sources (~300 item)

| Source | Item count |
|---|---:|
| Crafting recipes (endgame + mid-game) | 100 |
| Achievement rewards | 60 |
| Ranking seasonal rewards | 40 |
| Quest rewards | 60 |
| World boss (Round 16.3 catalog integration) | 30 |
| Vendor special (T1-T2 starter) | 10 |
| **TOTALE non-drop** | **~300** |

**Totale approssimativo**: 900 dungeon drop + 180 raid drop + 120 elite drop + 300 non-drop = **1500** ✅

---

## Sezione 10 — Distribuzione per CRAFTING / ACHIEVEMENT / RANKING (non-drop)

| Sotto-categoria non-drop | Item count | Note |
|---|---:|---|
| **Crafting recipes T4-T5** | 60 | Peso alto endgame, no Legendary craftabili |
| **Crafting recipes T2-T3** | 40 | Mid-game crafting standard |
| **Achievement rewards** | 60 | Unique per achievement, Rare/Epic mix, no Legendary |
| **Ranking seasonal rewards** | 40 | PvP + PvE ranking, Epic dominant |
| **Quest rewards** | 60 | Main + side quest, T1-T5 spread |
| **World boss** | 30 | Round 16.3 catalog integration (LIVE, no rewrite) |
| **Vendor special (T1-T2)** | 10 | Starter vendor T1 iconic items |
| **TOTALE non-drop** | **300** | 20% catalog |

**Vincolo**: **NO Legendary craftabile normalmente** (PM strict verbatim). Nessuno dei 15 Legendary del catalog è ottenibile via crafting/achievement/ranking/quest — solo drop 2%/1% dai raid/dungeon endgame.

---

## Sezione 11 — Legendary 7/15 candidate mapping (integrazione STEP 8)

**Cap catalog**: **15** invariato (PM strict verbatim).
**Approved Batch 5**: **7** (Q13=A verbatim).
**Margine future gate**: **8** (candidate discovery in Phase D5+).

### Mapping 7 approved (dettaglio da STEP 8)

| # | Legendary slug | Source slug | Source type | Lore | Drop rate | Utility fantasy |
|---|---|---|---|---|---:|---|
| L1 | `dragonlord-crown` | `dragon-vault` (LIVE) | Raid boss finale | Draco | 2% | Command Draconic |
| L2 | `void-touched-blade` | `void-cathedral` (NEW) | Raid boss finale | Vuoto | 2% | Void-Pierce |
| L3 | `seraph-halo-crown` | `celestial-conclave` (NEW) | Raid boss finale | Celeste | 2% | Divine Resurrect |
| L4 | `worldroot-scepter` | `world-tree-collapse` (NEW) | Raid boss finale | Alberi della Vita | 2% | Nature's Blessing HoT |
| L5 | `ambash-forge-hammer` | `ambash-legendary-forge` | Dungeon 3p boss | Ambash | 1% | Reforge weapon mid-encounter |
| L6 | `dragon-elder-scale` | `elder-wyrm-descent` | Dungeon 3p boss | Draco | 1% | Dragon-scale armor buff |
| L7 | `sole-nero-diadem` | `pantheon-of-fallen-suns` | Dungeon 3p Lv60 boss | Celeste | 1% | Swap light/void resist |

### 8 slot margine future gate

Riservati per candidate discovery in Phase D5+ (previa approvazione PM). Distribuzione ipotetica bilanciamento (**PENDING PM Q**):
- 2-3 slot per lore sources sottouso (Alberi della Vita, Halodi, Luna Morta, Ergolat, Aveol)
- 2-3 slot per classi che potrebbero avere Legendary class-specific (attualmente utility neutre)
- 2-3 slot riservati unpredicted future gate

---

## Sezione 12 — Signature Item Capacity Planning

Signature item = item personalizzati per classe/character con properties uniche (introdotto Round 6C, currently 14 signature templates in seed).

**Capacity R18.5 planning**:
- **Riservati 5 slot signature per classe canonica** × 5 classi = **25 signature slot** (design-only per D-phase completion)
- Non contati nei 1500 (extra layer, gestito da collection separata `signature_templates_r18_5`)
- Signature slots collegati a `signature_capacity_slot = true` sul field item schema (Sezione 1)

**Vincoli**:
- Signature NON conta come Legendary
- Signature NON è shop / P2W
- Signature è per-character, NON tradeable

---

## Sezione 13 — Class Proficiency Coverage (Warrior/Rogue/Mage/Priest/Ranger)

**Target**: distribuzione equa tra 5 classi canoniche. Ogni classe deve avere accesso a ~1/5 del catalog effettivo (dropping universal items).

### Distribuzione approssimativa 1500 item per class proficiency primaria

| Classe | Item primari | % catalog | Note |
|---|---:|---:|---|
| **Warrior** | 300 | 20.0% | Heavy armor + sword/mace/shield/hammer |
| **Rogue** | 290 | 19.3% | Light/medium armor + dagger/sword |
| **Mage** | 280 | 18.7% | Light armor + staff/wand |
| **Priest** | 280 | 18.7% | Heavy/medium armor + mace/staff/shield/wand |
| **Ranger** | 250 | 16.7% | Medium armor + bow/polearm |
| **Universal** (`is_universal = true`) | 100 | 6.7% | Consumables, materials, cosmetics, accessories generici |
| **TOTALE** | **1500** | **100.0%** | |

**Coverage check**: tutte 5 classi canoniche ≥16% catalog. Nessuna discriminazione.

**Backlog 3 weapon families unassigned** (`strumento`, `falce`, `trinket`) → mapping class proficiency **PENDING PM D1 Q** (currently 15 slot temporanei allocati fuori conteggio classe).

---

## Sezione 14 — Main Stat Coverage (STR/AGI/INT/END/FAI)

**Target**: distribuzione equilibrata dei main stat tra i 1500 item. Ogni stat deve avere ~20% coverage.

| Main stat | Item count | % catalog | Classi primarie associate |
|---|---:|---:|---|
| **STR** (Strength) | 320 | 21.3% | Warrior, Ranger (secondary) |
| **AGI** (Agility) | 300 | 20.0% | Rogue, Ranger (primary) |
| **INT** (Intelligence) | 300 | 20.0% | Mage |
| **END** (Endurance) | 280 | 18.7% | Warrior, Priest (tanking) |
| **FAI** (Faith) | 300 | 20.0% | Priest, Mage (secondary) |
| **TOTALE** | **1500** | **100.0%** | |

**Note**:
- STR leggermente più alto (21.3%) per warrior + weapon primary reliance
- END dedicato a tanking (Warrior/Priest heavy armor)
- FAI dedicato a casting divino (Priest primary, Mage secondary per some cross-role builds)

---

## Sezione 15 — Open Questions PM per iniziare D1

Prima di avviare Phase D1 (T1×300 item drafting), il PM deve rispondere:

### Q1 — Naming/slug schema
Approvare naming convention IT + slug kebab-case verbatim?

### Q2 — Item ID vs item slug primary
Confermare che `item_id` (uuid4) è chiave pubblica e `item_slug` è secondary unique (per readability)?

### Q3 — Crosswalk TIER × RARITY (Sezione 5)
Approvare matrice 5×5 (300+400+450+335+15=1500) o iterare valori?

### Q4 — Distribuzione slot (Sezione 6)
Approvare 12-slot enum + count o iterare (es. main-hand 16% troppo alto/basso)?

### Q5 — Armor type % (Sezione 7)
Approvare 33.8% light / 33.8% medium / 32.3% heavy o iterare?

### Q6 — Weapon family + 3 backlog (`strumento`, `falce`, `trinket`)
Approvare mapping class proficiency verbatim o assegnare/deferire i 3 backlog a R18.P3 formalmente?

### Q7 — Distribuzione dungeon/raid source (Sezione 9)
Approvare ~15 item medi per dungeon o iterare per bilanciamento specifico?

### Q8 — Non-drop 300 item breakdown (Sezione 10)
Approvare 100 craft + 60 achievement + 40 ranking + 60 quest + 30 world boss + 10 vendor?

### Q9 — Legendary future 8 slot margine (Sezione 11)
Approvare progressive discovery in Phase D5+ o pre-allocare 8 candidate ora?

### Q10 — Signature capacity 25 slot (Sezione 12)
Approvare 5 per classe × 5 classi = 25 signature separati da 1500 catalog?

### Q11 — Class proficiency distribution (Sezione 13)
Approvare W20%/R19.3%/M18.7%/P18.7%/Ra16.7%/Uni6.7% o iterare Ranger sotto media?

### Q12 — Main stat distribution (Sezione 14)
Approvare STR21.3%/AGI20%/INT20%/END18.7%/FAI20% o iterare?

### Q13 — Anti-P2W policy fields
Approvare enforcement automatico `can_be_sold_for_real_money = false` per item con `affects_combat|economy|ranking = true`?

### Q14 — D1 start authorization
Autorizzare avvio Phase D1 (T1×300 item drafting) dopo risposte Q1-Q13?

### Q15 — Deferred items (Round 18.P3 shield slot mapping)
Blocco R18.P3 shield slot mapping resta separato da D1 o integrato?

---

## Governance Check Phase D0 Blueprint

| Voce | Status |
|---|---|
| Sealed files 36 hash byte-identical | ✅ (pytest verificato pre + post append PRD) |
| DB writes | ZERO |
| Code changes (`.py`/`.js`/`.jsx`/`.tsx`/`.ts`) | ZERO |
| Migrations | ZERO |
| Item creation live | ZERO |
| Drop table apply | ZERO |
| Economy changes | ZERO |
| `lore_meta.py` touch | INVARIATO |
| Sealed file modification | ZERO |
| Item table live creation | ZERO (blueprint design only) |
| Phase C tech dry-run | NOT INITIATED (Q21 D→B verbatim) |
| Anti-P2W policy coverage | ✅ Sezione 2 obbligatoria |
| PM autonomous decision new | ZERO (tutte distribuzioni ancorate a PM decisions precedenti) |
| Files deliverable | 2 (.md + .json) |
| Class proficiency 5 canoniche | Warrior/Rogue/Mage/Priest/Ranger verbatim |

---

## Handoff — Phase D1 (T1 Lv1-15 × 300 item)

Post-D0 blueprint, la sequenza autorizzata continua con **Phase D1**:

- **Scope D1**: 300 item T1 (Lv1-15, bracket B1)
- **Distribuzione D1 rarity** (Sezione 5): Common 180 + Uncommon 100 + Rare 20 + Epic 0 + Legendary 0
- **Deliverable D1**: file matrix + tabella items T1 completa (300 righe)
- **Gate D1**: risposte a Open Questions D0 (Q1-Q15) obbligatorie prima di iniziare

**R18.5 status flow (aggiornato post STEP 9)**:
`... → C0-octies B5 CLOSED → Mini-Gate Legendary Discovery Chain (STEP 8) ✅ DRAFT → Phase D0 Item Table Blueprint (STEP 9) ✅ DRAFT → Phase D1 T1×300 item drafting 🔒 pending PM Q1-Q15 → Phase D2 T2×350 → D3 T3×350 → D4 T4×300 → D5 T5×200 (con 7 Legendary integrati)`

**Phase C tech dry-run**: 🔒 **NON in agenda** (Q21 D→B verbatim: dopo consolidamento base creativa).
