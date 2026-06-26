# ROUND 4 — Equipment & Loot Advanced — Technical Brief

> **Status**: 📄 DRAFT for product/user review. **NOT** authorized for
> implementation. No code shipped from this document.

---

## A. Scope tecnico

### A.1 Equip slots avanzati
Espansione dal modello attuale (weapon / armor / accessory) a uno schema di
**8-10 slot** per adventurer:

| Slot key | Equipment type | Stat focus |
|---|---|---|
| `helm` | Helmet | endurance / faith |
| `chest` | Body armor | endurance / strength |
| `legs` | Leg armor | agility / endurance |
| `boots` | Footwear | agility |
| `weapon_main` | Main hand weapon | strength / intellect / faith |
| `weapon_off` | Off hand / shield | endurance / intellect |
| `ring_1` | Ring (left) | any |
| `ring_2` | Ring (right) | any |
| `amulet` | Necklace | any |
| `cape` (opt) | Cloak | small mixed bonuses |

Backward-compatibility: gli item ROUND 3 con `slot=weapon` mappano a
`weapon_main`; `slot=armor` mappa a `chest`; `slot=accessory` mappa a
`amulet`. Migrazione **additive** in seed.

### A.2 Set bonuses
- Nuova collection `item_sets`: `{id, slug, name, name_it, pieces:[item_slug,...], tiers:[{count, bonus}]}`
- I bonus si attivano per soglia: 2/4/6 pezzi tipicamente.
- Esempio: "Goblin Hunter Set" (5 pezzi) → 2pz +5 str, 4pz +10 agi, 5pz +15 dmg vs Goblin tag.
- Bonuses calcolati al volo nel `combat_engine`. NO persistenza, NO P2W.

### A.3 Refinement / Enhancement
- Livelli `+1` → `+10` (soft cap), con tasso di successo decrescente.
- Costo: gold + materiali rari + (opzionale, da decidere) item di rinforzo.
- **ROUND 4 NO break/destroy**: failure consuma materiali ma NON rompe l'item.
  Break logic eventuale solo da ROUND 5+ con item di protezione.
- Curva proposta (default, configurabile):

| Livello | Success rate | Cost gold | Materials |
|---|---|---|---|
| +1 | 100% | 50 | iron_shard ×2 |
| +2 | 90% | 100 | iron_shard ×4 |
| +3 | 75% | 200 | iron_shard ×6, arcane_dust ×1 |
| +4 | 60% | 400 | iron_shard ×8, arcane_dust ×2 |
| +5 | 45% | 800 | …, dull_gem ×1 |
| +6 | 35% | 1500 | …, dull_gem ×2 |
| +7 | 25% | 2500 | …, raw_leather ×8 |
| +8 | 18% | 4000 | … |
| +9 | 12% | 6000 | … |
| +10 | 8% | 10000 | … |

### A.4 Rarity tier expansion
Stato attuale: Common / Uncommon / Rare / Epic.
- **Proposta ROUND 4**: aggiungere **Legendary** (rarissimo, drop solo da
  dungeon T4+ e crafting end-game).
- **NON aggiungere Mythic in ROUND 4** (lasciare spazio per ROUND 5/6).
- Item Legendary: 2 affix garantiti + slot enchant garantito.

### A.5 Enchant slots
- Ogni item espone `enchant_slots: int` (0/1/2 in base alla rarity:
  Common 0, Uncommon 0, Rare 1, Epic 1-2, Legendary 2).
- Nuova collection `enchants` con bonus statici (es. "Of the Bear" → +3 str).
- L'enchant è **rimovibile** (disenchant restituisce gemma usata? — decidere).

### A.6 Item-affix system (prefix/suffix random rolls)
- Solo Rare+ ottengono affix random alla generazione del drop.
- 1 prefix + 1 suffix max per item, scelti da una pool di ~30 voci ciascuno.
- Affix esempi: prefix "Sharp" (+2 str), suffix "of the Wolf" (+3 agi).
- Salvati come `affixes: [{slug, slot:"prefix"|"suffix", bonus_stat, bonus_value}]`.

### A.7 Disenchant / Salvage
- `POST /api/inventory/{instance_id}/disenchant` → ritorna materiali
  proporzionati alla rarity. Item distrutto (`disenchanted_at` stamped).
- NO refund di gold. NO recovery di enchant gemme da Rare+ (per ora).

---

## B. Vincoli ereditati (NON deviare)

1. **Fair F2P** invariato. Niente paywall su refinement/enchant/affix.
2. **NO P2W**: tutti i materiali drop-only o crafting-only, mai acquistabili.
3. **NO real-money item purchase**.
4. **Anti-inflazione**: drop rate Legendary < 0.5% per dungeon clear T4+.
5. **ALLOWLIST intoccata**.
6. **Backward-compatible** con item esistenti ROUND 3 (mapping additivo).
7. **Migrazioni additive/idempotenti** (no rewrites di item esistenti).
8. **Atomic crafting/refinement** (CAS guards Mongo, idempotent endpoint).
9. **No reputation/ranking reward** da refinement/enchant.
10. **No tampering** con la leaderboard formula (continua a usare
    `max_team_power_ever`, non i bonus set istantanei).

---

## C. Modelli proposti

### C.1 Item esteso (`items`)
```python
class Item(BaseDocument):
    # existing
    slug: str
    name: str
    description: str
    rarity: Literal["Common","Uncommon","Rare","Epic","Legendary"]
    item_type: Literal["weapon","armor","accessory","material","consumable"]
    # NEW
    slot_type: Optional[Literal[
        "helm","chest","legs","boots",
        "weapon_main","weapon_off",
        "ring","amulet","cape",
    ]] = None
    set_id: Optional[str] = None         # FK → item_sets.id
    max_refinement: int = 0              # 0 = non rifinibile
    enchant_slots: int = 0
    affix_pool_tag: Optional[str] = None # tag for random affix rolls
```

### C.2 Nuova collection `item_sets`
```python
class ItemSet(BaseDocument):
    slug: str                            # unique
    name: str
    name_it: str
    description: Optional[str] = None
    pieces: List[str]                    # item_slug list
    tiers: List[ItemSetTier]             # ordered by `count` asc

class ItemSetTier(BaseModel):
    count: int                           # 2/4/5/6 etc.
    bonus_stat: Literal["strength","agility","intellect","endurance","faith"]
    bonus_value: int
    description: str
```

### C.3 Nuova collection `enchants`
```python
class Enchant(BaseDocument):
    slug: str
    name: str
    rarity: Literal["Common","Uncommon","Rare","Epic"]
    bonus_stat: str
    bonus_value: int
    cost_gold: int
    cost_materials: List[MaterialCost]
```

### C.4 `inventory_items` esteso (NUOVO: per-instance state)
```python
class InventoryItem(BaseDocument):
    guild_id: str
    item_id: str                         # template ref (items.id)
    instance_id: str                     # NEW: uuid4 unique per crafted/dropped piece
    quantity: int                        # stack count (only for stackables)
    # NEW per-instance fields (null for stackable mats):
    refinement_level: int = 0
    enchants: List[InventoryEnchant] = []
    affixes: List[InventoryAffix] = []
    bound_to_adventurer_id: Optional[str] = None
```

> **Migration strategy**: items esistenti ricevono `instance_id = inventory_items.id` (idempotente). Pile di materiali restano `quantity > 0` con `refinement_level=0, enchants=[], affixes=[]`.

### C.5 `equipped_items` (separare slot management)
```python
class EquippedItem(BaseDocument):
    adventurer_id: str                   # FK
    slot_type: str                       # canonical slot key
    instance_id: str                     # FK → inventory_items.instance_id
    equipped_at: datetime
```
Constraint: index unico `(adventurer_id, slot_type)`.

---

## D. Endpoint nuovi proposti

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/inventory/{instance_id}/refine` | Avanza refinement +1, atomico, audit |
| `POST` | `/api/inventory/{instance_id}/enchant` | Applica enchant in uno slot, atomico |
| `POST` | `/api/inventory/{instance_id}/disenchant` | Distrugge item → materiali |
| `POST` | `/api/adventurers/{id}/equip/{slot}` | Equip with auto-unequip slot esistente |
| `POST` | `/api/adventurers/{id}/unequip/{slot}` | Unequip esplicito |
| `GET` | `/api/sets` | Lista set + tiers (pubblico, per UI compendium) |
| `GET` | `/api/sets/{slug}` | Detail di un set + pezzi mancanti |
| `GET` | `/api/adventurers/{id}/equipment` | Equipaggiamento corrente + set bonuses attivi |
| `GET` | `/api/enchants` | Lista enchant disponibili (pubblico) |

**Path count atteso**: 61 → **~70** (stima: +9 nuovi endpoint).

---

## E. Game-balance considerations

- **Refinement success rate** decrescente (+1=100% … +10=8%): scoraggia
  push estremi senza renderli impossibili.
- **NO permadeath item** in ROUND 4: failure consuma materiali ma item
  resta intatto a livello precedente. Break/destroy → posticipato ROUND 5.
- **Set bonuses moderati**: +2 a +15 stat totali sul set completo, NON
  bonus % moltiplicativo a team_power. Mantiene la leaderboard equa.
- **Drop rate Legendary**: 0.3% per T4 clear, 0.5% per T5+ (T5 = dungeon
  end-game futuro, non in ROUND 4).
- **Materiali end-game** (per refinement +7+): drop esclusivi da dungeon T4
  esistenti, NO nuovi dungeon richiesti.
- **Enchant gem economy**: gem droppano da disenchant Rare+ → loop chiuso,
  no inflation.

---

## F. Domande aperte — 🔒 LOCKED (2026-06-26, post user-review)

Tutte le 8 domande sono state risolte. Le risposte qui sotto sono **vincolanti**
per l'implementazione. Qualunque deviazione richiede nuovo go esplicito.

| # | Topic | Decisione locked |
|---|---|---|
| Q1 | Tier rarity | **A — Solo Legendary** (drop rate 0.3-0.5% da T4+). NO Mythic in ROUND 4. |
| Q2 | Refinement input | **C — Oro + materiali + reagenti rari da dungeon**. NO item duplicato come fuel. |
| Q3 | Set bonuses | **A — Tier-based**. Bonus piccolo a 3/5 pezzi, bonus più forte a 5/5. NO all-or-nothing puro. |
| Q4 | Disenchant output | **C — Materiale base GARANTITO + bonus random pesato sulla rarità** dell'item. |
| Q5 | Enchant selection | **B — Scelta giocatore tra 3-5 opzioni dal pool**. NO slot machine pura. |
| Q6 | UI | **A — Nuova pagina dedicata "Forge / Workshop"**. Separata dal Crafting base. |
| Q7 | Affix reroll | **A — Sì, attivo**. Costo crescente. Cap/limiti anti-abuso (vedi §E.7). |
| Q8 | Bound-on-Equip | **A — Item refinato OR enchantato → BoE**. NON vendibile sul mercato. UI deve spiegare il motivo. |

### Implicazioni vincolanti derivate

- **§A.2 Set bonuses** → schema `tiers` ridotto a 2 soglie standard: `pieces_required ∈ {3, 5}`. Tier `3pz` piccolo (es. +3/+4 a una stat), tier `5pz` forte (es. +8/+10 e/o +1 perk passivo non competitive).
- **§A.3 Refinement** → tabella costi rimane come proposto in §A.3 (gold + iron_shard + arcane_dust + dull_gem). Aggiungere un nuovo reagente raro `dragon_essence` (drop solo da T4+, idempotent seed) per refinement +7 → +10.
- **§A.5/A.6 Enchant + Affix UX** → endpoint enchant deve restituire 3-5 opzioni casuali pesate per rarità item, lo `apply` accetta il `slug` scelto dal player. Affix reroll: nuovo endpoint `POST /api/inventory/{instance_id}/reroll-affixes`, costo crescente esponenziale (50 → 150 → 400 → 1000 → 2500, hard cap 5 reroll/item).
- **§A.7 Disenchant** → output struct: `{ materials_guaranteed: [{slug, qty}], materials_bonus: [{slug, qty}] }`. Il guaranteed scala lineare con rarity; il bonus è weighted random.
- **§Q8 BoE enforcement (CRITICO)**:
  - `inventory_items.is_bound: bool` (NUOVO campo)
  - Diventa `True` automaticamente al **primo** refinement OR enchant OR reroll.
  - `app/market/services.py::create_listing` deve rifiutare con **422** se l'`InventoryItem` ha `is_bound=True`, con messaggio i18n esplicito.
  - UI inventory: badge `[BOUND]` (i18n "Legato all'oggetto") accanto al nome + tooltip "Item rifinito/incantato: non più vendibile al mercato".

### Vincoli ROUND 4 ribaditi (NON deviare)

- ❌ NO Mythic
- ❌ NO P2W, NO premium boost
- ❌ NO item di potere vendibile con denaro reale
- ❌ NO hard delete (qualsiasi disenchant marca il record con `disenchanted_at`, lo lascia in collection per audit retention)
- ❌ NO ALLOWLIST changes
- ❌ NO cleanup leaderboard
- ❌ NO bonus consorzio
- ❌ NO modifiche SMTP/P0/branding
- ✅ Vecchi item ROUND 3 devono restare compatibili (mapping additivo, mai breaking)
- ✅ Mercato DEVE impedire la vendita di item bound/refined/enchantati (enforcement backend + UI feedback)
- ✅ Preview prima → smoke test → solo allora redeploy prod con conferma utente

---

## F-bis. Audit dei file esistenti che ROUND 4 toccherà

> Read-only mapping. NESSUNA modifica al codice prima del GO esplicito.

| File | Impatto | Tipo di intervento previsto |
|---|---|---|
| `backend/app/inventory/models.py` (o equivalente schema) | **Alto** | Add `instance_id` (uuid4), `is_bound`, `refinement_level`, `enchants[]`, `affixes[]`, `disenchanted_at` |
| `backend/app/inventory/services.py` | **Alto** | Migration helper idempotente (vedi §F-ter), backward-compat read |
| `backend/app/inventory/routes.py` | **Medio** | New endpoints: `/refine`, `/enchant`, `/disenchant`, `/reroll-affixes`, `/enchant-options` |
| `backend/app/items/models.py` (template) | Medio | Add `slot_type`, `set_id`, `max_refinement`, `enchant_slots`, `affix_pool_tag` |
| `backend/app/items/services.py` / `routes.py` | Basso | Read-only di nuovi campi (non break) |
| `backend/app/equipment/services.py` (Phase 14 esistente) | **Alto** | Re-target di `equip_item_service` su `instance_id` invece di `item_id` aggregato; aggiungere `EquippedItem` con uniqueness `(adventurer_id, slot_type)` |
| `backend/app/adventurers/*` | Medio | `GET /api/adventurers/{id}/equipment` nuova endpoint che include set-bonus calcolati al volo |
| `backend/app/market/services.py::create_listing` | **Critico** | **Guard BoE**: 422 se `inventory_items.is_bound=True` |
| `backend/app/market/routes.py` | Basso | Pass-through del 422 (Pydantic exception handler) |
| `backend/app/audit/log.py` | Basso | Aggiungere event_types: `item_refined`, `item_refine_failed`, `item_enchanted`, `item_disenchanted`, `item_reroll_affix`, `item_equipped_slot`, `item_unequipped_slot` |
| `backend/app/seeds/seed_items_it.py` | Medio | Aggiungere `dragon_essence` material + ~3-5 item Legendary baseline (idempotent upsert) |
| `backend/app/seeds/seed_sets.py` (NUOVO) | Nuovo | Idempotent seed di 3-5 set base (es. "Goblin Hunter", "Drake Slayer", "Arcane Adept") |
| `backend/app/seeds/seed_enchants.py` (NUOVO) | Nuovo | Idempotent seed di ~12-15 enchant base |
| `backend/app/quests/services.py` | Basso | Hook weekly quest `weekly_refine_items_3` e `weekly_enchant_items_2` (opzionale, ma coerente con Phase 14.1) |
| `frontend/src/pages/Forge.jsx` (NUOVO) | **Alto** | Nuova pagina dedicata con 4 tab: Refine / Enchant / Reroll / Disenchant |
| `frontend/src/pages/Inventory.jsx` | Medio | Badge `[BOUND]` + tooltip i18n + bottone "Vai a Forge" |
| `frontend/src/pages/AdventurerEquipment.jsx` | **Alto** | Nuovo schema 8-10 slot, set bonuses display, set progression UI |
| `frontend/src/pages/Market.jsx` | Basso | Già OK: mostra 422 dal backend come toast — solo testo i18n da aggiungere |
| `frontend/src/components/AppHeader.jsx` | XS | NavLink `Forge` |
| `frontend/src/App.js` | XS | Route `/forge` (ProtectedRoute requireGuild) |
| `frontend/src/i18n/lang/{it,en}.json` | Basso | Nuove chiavi: `forge.*`, `inventory.bound.*`, `set.*`, `enchant.*`, `affix.*`, `nav.forge` |
| Test backend `tests/backend_phase17_round4_test.py` (NUOVO) | Nuovo | 25-30 test: migration idempotency, refine atomic, BoE guard, set bonus calc, reroll cap, disenchant output, leaderboard invariance |

**Path count guard test** (3 file esistenti) → update da 61 → ~70 (numero finale fissato al primo deploy preview).

---

## F-ter. Migration plan additivo/idempotente

> Tutto fatto via lifespan idempotent seed/migration. Zero downtime.
> Tutti gli step sono `update_many` con guard `field: {$exists: False}` —
> ri-run sicuro N volte.

**Step 0 — Schema migration (eseguita all'avvio backend, una sola volta logicamente)**:
```python
# Add instance_id to inventory_items legacy rows (idempotent).
# Existing row id is reused as instance_id (1:1) — preserves marketplace
# listings that reference the row id.
await db.inventory_items.update_many(
    {"instance_id": {"$exists": False}},
    [{"$set": {"instance_id": "$id"}}],   # aggregation pipeline update
)
# Add default refinement/enchant/affix/is_bound fields
await db.inventory_items.update_many(
    {"refinement_level": {"$exists": False}},
    {"$set": {
        "refinement_level": 0,
        "enchants": [],
        "affixes": [],
        "is_bound": False,
        "disenchanted_at": None,
    }},
)
```

**Step 1 — Items template schema** (template `items` collection):
```python
await db.items.update_many(
    {"slot_type": {"$exists": False}},
    {"$set": {
        "set_id": None,
        "max_refinement": 0,
        "enchant_slots": 0,
        "affix_pool_tag": None,
    }},
)
# slot_type derivation from legacy `slot` (idempotent map):
LEGACY_SLOT_MAP = {
    "weapon":    "weapon_main",
    "armor":     "chest",
    "accessory": "amulet",
}
for legacy, new in LEGACY_SLOT_MAP.items():
    await db.items.update_many(
        {"slot": legacy, "slot_type": {"$in": [None, ""]}},
        {"$set": {"slot_type": new}},
    )
```

**Step 2 — Set/Enchant seed (idempotent upsert by slug)**:
- `seed_sets.py` → `replace_one({slug}, doc, upsert=True)` per ogni set definito
- `seed_enchants.py` → idem
- `seed_items_it.py` esteso → upsert `dragon_essence` material + 3-5 Legendary baseline

**Step 3 — Indices (idempotent via `create_index`)**:
- `inventory_items.instance_id` UNIQUE
- `equipped_items.{adventurer_id, slot_type}` UNIQUE composite
- `item_sets.slug` UNIQUE
- `enchants.slug` UNIQUE

**Step 4 — Equipment migration** (legacy `adventurer.equipped_items[]` array → new `equipped_items` collection):
- Per ogni adventurer con `equipped_items[]` non vuoto, upsert nella nuova collection con `slot_type` derivato.
- Lasciare l'array legacy invariato per N round (backward read fallback in `equipment/services.py`).
- Rollback safety: l'array legacy resta source-of-truth in caso di problemi.

**Step 5 — Audit log event_types**:
- Aggiungere ai `EVENT_TYPES` di `audit/log.py` i nuovi 7 tipi (puramente additivo).

### Rollback strategy
- Step 0/1/2/3 sono additivi → rollback = ignorare i nuovi campi (vecchio codice continua a funzionare).
- Step 4: la collection nuova `equipped_items` non sostituisce nulla, solo affianca → rollback = leggere dal legacy array. Per N round.

---

## F-quater. UI Mockup testuale — pagina "Forge / Workshop"

> Mobile-first, coerente con il design system esistente (font monospace,
> tema scuro, accenti amber, `data-testid` ovunque). Frontend page path: `/forge`.

```
┌─────────────────────────────────────────────────────────────┐
│ :: OFFICINA / FORGE                                  Gold 1.2k│
│ ⚒ Rifinisci · ✨ Incanta · 🔄 Affinanza · 🗡 Smonta            │   (4 tab)
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ ┌─── Item Selector ──────────────────────────────────┐      │
│ │  Filtra: [ ●Tutti  ○Rifinibili  ○Incantabili      │      │
│ │           ○Smontabili ]                            │      │
│ │  ┌──────────────────────────────────────────┐     │      │
│ │  │ ▣ Spada di Ferro                  +0 / +5│     │      │
│ │  │   Common · Weapon · weapon_main          │     │      │
│ │  │   [Forgia]                               │     │      │
│ │  ├──────────────────────────────────────────┤     │      │
│ │  │ ▣ Elmo del Drago Minore          +3 / +7│     │      │
│ │  │   Rare · Helm · helm  [BOUND]            │     │      │
│ │  │   Sharp +2 STR · of the Wolf +3 AGI      │     │      │
│ │  │   [Continua]                             │     │      │
│ │  └──────────────────────────────────────────┘     │      │
│ └────────────────────────────────────────────────────┘      │
│                                                              │
│ ┌─── Operation Panel (tab Rifinisci) ─────────────────┐     │
│ │  Selezionato: Spada di Ferro  +0                    │     │
│ │  Prossimo livello: +1   Success: 100%               │     │
│ │  Costo: 50 gold + iron_shard ×2                     │     │
│ │  ⚠ Una volta rifinito, l'oggetto diventa LEGATO     │     │
│ │     (non sarà più vendibile al mercato).            │     │
│ │  [ CONFERMA RIFINITURA ]   [ Annulla ]              │     │
│ └─────────────────────────────────────────────────────┘     │
│                                                              │
│ ── Log forge recenti ────                                    │
│ • 12 min fa: Hai rifinito Asta del Sangue +2 (success)       │
│ • 1h fa: Hai incantato Amuleto Lunare con "Faith Mantle"    │
└─────────────────────────────────────────────────────────────┘
```

**Tab "Incanta"** (mockup):
```
Selezionato: Anello del Boscaiolo  (Rare, 1 enchant slot disponibile)
3 opzioni sorteggiate per te (scegli 1):
  ⊙ Of the Wolf      +3 AGI       [Comune]    cost: 80g
  ⊙ Sharp Edge       +2 STR       [Uncommon]  cost: 120g
  ⊙ Arcane Spark     +2 INT       [Rare]      cost: 200g
[ Conferma scelta ]   [ Rigenera opzioni (50g) ]
⚠ L'oggetto diventerà LEGATO dopo l'incanto.
```

**Tab "Affinanza" (Reroll)**:
```
Selezionato: Elmo del Drago Minore  (2 affix attivi)
Affix attuali:  Sharp +2 STR · of the Wolf +3 AGI
Reroll #1/5     Costo: 50g
[ Reroll ]      ← genera 2 nuovi affix random, conferma prima di salvare
```

**Tab "Smonta" (Disenchant)**:
```
Selezionato: Spada Arrugginita  (Common)
Smontando otterrai:
  Garantito: iron_shard ×2
  Bonus random (peso 30%): arcane_dust ×1
⚠ L'oggetto verrà distrutto.
[ CONFERMA SMONTAGGIO ]
```

**data-testid plan** (estratto):
- `forge-tab-refine`, `forge-tab-enchant`, `forge-tab-reroll`, `forge-tab-disenchant`
- `forge-item-{instance_id}` per ogni riga in selector
- `forge-confirm-refine`, `forge-confirm-enchant`, `forge-confirm-reroll`, `forge-confirm-disenchant`
- `forge-enchant-option-{slug}` per ogni opzione mostrata
- `forge-bound-badge-{instance_id}`, `forge-bound-tooltip`
- `forge-log-{event_id}` per il log eventi

**Inventory.jsx aggiornamenti**:
- Badge `[BOUND]` (i18n: IT "Legato", EN "Bound") accanto al nome
- Tooltip al hover: "Oggetto rifinito/incantato — non più vendibile al mercato"
- Per item bound: il bottone "Vendi al mercato" è disabilitato + tooltip
- Bottone aggiuntivo "Vai a Forge" per ogni item rifinibile/incantabile

**AdventurerEquipment.jsx aggiornamenti**:
- Layout slot rinnovato (8-10 slot visivamente raggruppati: armatura sopra, accessori sotto)
- Pannello "Set bonuses attivi" sotto la lista slot (es. "Goblin Hunter 3/5 — +3 STR")
- Highlight pezzi della stessa set con un marker colorato

---

## F-quinquies. Plan di esecuzione consigliato (per ROUND 4 kick-off)

Quando arriverà il "GO" esplicito, l'ordine sarà:

1. **Backend foundation** (mezza giornata)
   - Migration step 0+1+2+3 in lifespan
   - Add `seeds/seed_sets.py`, `seeds/seed_enchants.py`
   - Add Pydantic models per Item/Set/Enchant/InventoryItem instance fields
   - Add audit event_types
2. **Backend services & routes** (1 giornata)
   - `inventory/services.py::refine_item`, `enchant_item`, `disenchant_item`, `reroll_affixes`, `get_enchant_options`
   - `equipment/services.py` refactor su `instance_id` + nuova collection `equipped_items`
   - **CRITICO**: `market/services.py::create_listing` BoE guard (422 + i18n key)
3. **Backend tests** (mezza giornata)
   - 25-30 test in nuovo file `tests/backend_phase17_round4_test.py`
   - Coverage: migration idempotency, refine atomic CAS, BoE guard, set bonus calc, reroll cap, disenchant output, leaderboard invariance, audit, no-regression Phase 14/15/16
4. **Frontend** (1-1.5 giornate)
   - Nuova pagina `/forge` con 4 tab (Refine/Enchant/Reroll/Disenchant)
   - Update Inventory + AdventurerEquipment + Market 422 toast + NavLink Forge + i18n
5. **Smoke test preview + frontend testing_agent_v3** (mezza giornata)
6. **Report finale** + standby per user validation prima di redeploy prod

**Path count atteso**: 61 → **70-72** (+9-11 endpoints). I 3 path-count guard test verranno aggiornati una sola volta a numero finale.

---



## G. Stima sforzo

| Area | Effort | Risk |
|---|---|---|
| Item model migration + backward compat | M | M (data integrity) |
| Refinement endpoint + atomic logic | M | M (CAS guards) |
| Enchant system (collection + endpoint) | M | L |
| Affix random-roll system | M | M (balance) |
| Equipment slots redesign + new collection | **L** | H (toccare adventurer detail page) |
| Set bonuses calc engine | M | L (read-only, idempotente) |
| Disenchant logic + material return | M | L |
| UI Workshop/Forge | **L** | M (UX coerenza, mobile responsive) |
| Testing suite (15-20 backend + 10 frontend) | M-L | L |
| Path count guard updates | XS | XS |

**Stima totale**: ~3-4 giornate di lavoro per backend completo + UI base.
ROUND 5/6 separato per Mythic, item-break, refinement-protection.

---

## H. Path count

| Step | Endpoints | Path count |
|---|---|---|
| Pre-ROUND 4 | baseline + Phase 16.1 | 61 |
| ROUND 4 | refine/enchant/disenchant/equip/unequip/sets/enchants/adv-equipment | **~70** |
| Δ | +9 endpoints (stima) | +9 |

---

## I. Open risk register

1. **Migrazione `inventory_items` → instance_id**: rischio doppi update se
   non idempotente. Mitigazione: seed migration con `_id` snapshot + replay log.
2. **Leaderboard impact**: i set bonus NON devono alterare
   `max_team_power_ever`. Mitigazione: calcolare team_power senza set bonus
   istantanei (solo stat base + refinement).
3. **Adventurer detail UI**: schermo già denso. Possibile redesign mobile.
4. **Marketplace impact**: item con `instance_id` e affix unici NON sono
   stackable → la marketplace deve gestire single-piece listings (già supporta
   `quantity=1`, ma serve UI per affix display).
5. **Audit log volume**: refine/enchant fan-out può triplicare i row.
   Mitigazione: log "compatti" (1 row per operation, no fan-out per affix).

---

## J. NON in ROUND 4 (esplicito)

- ❌ Item break / destroy on refinement failure
- ❌ Refinement protection items / scrolls
- ❌ Mythic rarity
- ❌ End-game dungeon T5+ (separato in ROUND 5)
- ❌ Reroll affix
- ❌ Item transmog / cosmetic
- ❌ Real-money item purchase
- ❌ Premium boost / pay-to-skip
- ❌ Set bonus that scales linearly with team_power (anti-leaderboard-distortion)

---

## Changelog

- **2026-06-26** — Brief drafted post-Phase 16.1 deploy. Awaiting user review on §F domande aperte before any implementation kick-off.
