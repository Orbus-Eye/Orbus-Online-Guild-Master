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

## F. Domande aperte (da approvare prima di implementare)

1. **Tier rarity**: confermare **solo Legendary** (NO Mythic in ROUND 4).
2. **Refinement input**: solo gold + materiali, OPPURE serve un "item duplicato"
   come reagente (modello tipo Diablo enhancement)?
3. **Set bonuses activation**: bonus appaiono solo a piece-count raggiunto
   (es. 4pz = bonus 2pz + bonus 4pz cumulati)?
4. **Disenchant output**: materiali RANDOM (più variance) o GARANTITI
   (più predictable, scelta probabile per fairness)?
5. **Enchant selection**: random affix dal pool del player, oppure il
   player sceglie l'enchant da applicare?
6. **UI**: pagina dedicata **"Forge/Workshop"** nel menu principale, OPPURE
   estensione dell'Inventory esistente (sub-tab "Forge")?
7. **Affix re-roll**: feature ROUND 4 o posticipata? (Pro: depth. Contro:
   complessità + grind).
8. **Bound-on-equip**: gli item rifinati diventano legati all'adventurer
   (no transfer dopo equip)? Influisce su trading via marketplace.

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
