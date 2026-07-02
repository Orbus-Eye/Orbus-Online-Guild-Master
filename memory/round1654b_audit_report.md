# Round 16.5.4b — STEP 1: Audit Read-Only Auto-Equip
**Data:** 2026-02 · **Modalità:** read-only (nessun codice modificato, nessuna scrittura DB)
**Autore:** E1 · **Scope:** analisi statica + query MongoDB non distruttive

---

## 0. TL;DR

L'endpoint `POST /api/adventurers/{id}/auto-equip` **esiste** e **già dichiara** una logica class-aware (primary/secondary stat weighting). Nella pratica **NON funziona** perché:

- il campo `stats` che la formula legge **NON esiste su nessun item** (0/113 equippables). Il boost primario/secondario è quindi **sempre 0**;
- il gate di livello usa i campi sbagliati (`required_level` / `level_requirement` invece di `required_adventurer_level`);
- il fallback anti-Legendary del level-gate condiviso (`resolve_item_required_level`) **non viene invocato**;
- due classi (`warlock`, `alchemist`) non hanno **NESSUN item** con `recommended_classes` compatibile → sempre unchanged.

**Conseguenza pratica**: l'auto-equip oggi seleziona in base al solo `power_score`, ignorando classe, stat primaria, minimo livello effettivo, e casing rarity. Il "fix" R16.5 sul min_level è **bypassato**.

---

## 1. Mappa dei file rilevanti

| File | Ruolo | Note |
|---|---|---|
| `app/backend/app/equipment/routes.py:47-57` | Route `POST /api/adventurers/{id}/auto-equip` | Delega a `auto_equip_adventurer` |
| `app/backend/app/equipment/auto_equip.py` | **Logica principale (303 righe)** | Fitness score + slot loop |
| `app/backend/app/equipment/compatibility.py` | `check_equip_compatibility` | usato correttamente da auto-equip |
| `app/backend/app/equipment/level_gate.py` | `resolve_item_required_level` + `enforce_item_level_requirement` | **NON usato da auto-equip** |
| `app/backend/app/equipment/services.py:186-189` | `equip_item_service` | invoca `enforce_item_level_requirement` correttamente |
| `app/backend/app/expeditions/formulas.py:95-104` | vero `item_equip_power` canonico (somma `*_bonus` + `power_score`) | **shadowato** da copia locale in auto_equip.py |
| `app/backend/app/items/services.py:36-41` | `item_public` — schema serializzato | espone `strength_bonus`/`agility_bonus`/… (NO `stats`) |
| `app/backend/app/shared/constants.py:65-66` | `EQUIPMENT_SLOTS = (weapon, armor, accessory)` | 3 slot |

---

## 2. Come funziona OGGI l'auto-equip (walkthrough logico)

```python
# app/equipment/auto_equip.py
async def auto_equip_adventurer(db, *, guild, adventurer_id, actor_user_id):
    adv = fetch(adventurers, {id, guild_id})                     # OK
    cls_meta = _load_class_meta(db, adv.class_slug)              # LEGGE adventurer_classes ✔
    primary = cls_meta.primary_stat  or 'strength'               # es. 'strength' per warrior
    secondaries = cls_meta.secondary_stats or []                 # es. ['endurance']

    current_by_slot = load equipped items per slot                # OK
    inv_rows = inventory_items where guild_id, is_active != False  # NO SORT deterministico
    items_pool = items where id in inv_rows.item_id AND is_active != False  # NO SORT

    for slot in ('weapon','armor','accessory'):
        for it in items_pool:
            if it.item_type != slot: continue
            req_lv = it.required_level or it.level_requirement or 1   # ⚠ CAMPI INESISTENTI
            if req_lv > adv.level: continue
            verdict = check_equip_compatibility(adv, it)               # OK (block/warning/ok)
            if verdict.severity == 'block': continue
            fit = _compute_fitness(it, primary, secondaries)           # ⚠ base solo power_score
            if verdict.severity == 'warning': fit *= 0.5
            candidates.append((fit, it))
        candidates.sort(key=lambda x: x[0], reverse=True)              # tie-break implicito
        best_fit, best_item = candidates[0]
        if best_fit > current_fit: swap else keep
```

### Formula di scoring attuale

```python
_compute_fitness(item, primary, secondaries):
    base = item_equip_power(item)                     # ⚠ locale, legge SOLO power_score o stats.values()
    primary_boost   = stats.get(primary, 0) * 2       # ⚠ stats == {} → SEMPRE 0
    secondary_boost = sum(stats.get(s,0) for s in sec) * 1  # ⚠ SEMPRE 0
    return base + primary_boost + secondary_boost
```

**Il boost stat non contribuisce mai.** Il ranking equivale a `power_score` puro con penalità 0.5 per warning.

---

## 3. Stato del DB (verifica read-only)

### 3.1 Catalogo classi
- Collection: **`adventurer_classes`** (14 docs, `class_catalog` è vuota → NON esiste)
- Campi `primary_stat` e `secondary_stats` **presenti su tutte le 14 classi**:

| slug | primary_stat | secondary_stats |
|---|---|---|
| warrior | strength | [endurance] |
| rogue | agility | [strength] |
| mage | intellect | [endurance] |
| priest | faith | [intellect] |
| ranger | agility | [endurance] |
| paladin | faith | [strength, endurance] |
| berserker | strength | [endurance] |
| druid | faith | [intellect] |
| necromancer | intellect | [agility] |
| monk | agility | [endurance, faith] |
| bard | intellect | [agility, faith] |
| assassin | agility | [strength] |
| warlock | intellect | [faith, agility] |
| alchemist | intellect | [agility, endurance] |

✅ **Nessun campo da inventare.** Il catalogo è già class-aware.

### 3.2 Schema items (113 equippables, campi effettivamente presenti)

| Campo | Coverage | Nota |
|---|---|---|
| `power_score` | 113/113 | ✅ affidabile |
| `strength_bonus` | 112/113 | ✅ int diretto (NO `stats` dict) |
| `agility_bonus` | 110/113 | ✅ |
| `intellect_bonus` | 109/113 | ✅ |
| `endurance_bonus` | 110/113 | ✅ |
| `faith_bonus` | 108/113 | ✅ |
| `class_tags` | 113/113 | ✅ |
| `recommended_classes` | 113/113 | ✅ |
| `required_adventurer_level` | 113/113 | ✅ **campo canonico R11.3** |
| `level_required` | 102/113 | legacy |
| `weapon_tags` | 49/113 | solo weapons |
| `armor_tags` | 32/113 | solo armor |
| `required_class_optional` | 11/113 | signature/class-locked |
| **`stats`** (dict) | **0/113** | ⚠ **NON ESISTE** |
| `specialization_unlocks` | 0/113 | non seeded |
| `is_universal` | 0/113 | non seeded |
| `min_level` (altro nome) | osservato 1 caso (`drake_slayer_blade`) | rumore |

### 3.3 Copertura item per rarità × slot (equippables)

| Rarity | Common | Uncommon | Rare | Epic | Legendary | **rare** | **epic** | **legendary** |
|---|---|---|---|---|---|---|---|---|
| weapon | 15 | 11 | 8 | 12 | 1 | 0 | 0 | 2 |
| armor | 12 | 7 | 4 | 5 | 2 | 0 | 0 | 2 |
| accessory | 9 | 7 | 7 | 5 | 2 | 0 | 0 | 2 |
| **TOT** | **36** | **25** | **19** | **22** | **5** | **0** | **0** | **6** |

**Bug adiacente #1**: rarità in minuscolo (`rare`/`epic`/`legendary`) — 6 legendary + N material_continental/event. La tabella `_RARITY_TO_MIN_LEVEL` in `level_gate.py:41` è **case-sensitive**, quindi i 6 legendary lowercase non ricadrebbero mai sul fallback → `resolve_item_required_level` restituirebbe 1 per essi (ma tutti hanno già `required_adventurer_level: 1` esplicito, quindi il bug esiste anche in via principale).

### 3.4 Copertura per classe × slot (`recommended_classes`)

```
class        weapon  armor  acces
warrior          26     27     14
rogue            21      6      4
mage             16      4     14
priest           10      5     16
ranger           21      6      4
paladin          34     29     27
berserker        25     23     14
druid            10      5     16
necromancer      16      4     14
monk             13      6      1     ← accessory monk = 1 sola
bard             11      4     14
assassin         21      6      4
warlock           0      0      0     ← ZERO items
alchemist        0      0      0     ← ZERO items
```

**Bug adiacente #2**: `warlock` e `alchemist` (introdotti dopo R16.0) non hanno **nessun** item con `recommended_classes` che li menzioni. L'auto-equip finirà sempre in warning (off_class_tags) o unchanged.

### 3.5 Legendary con `required_adventurer_level: 1` (bypass R16.5)

```
legendary_sword_alveora    weapon    legendary rarity, req_level=1
legendary_armor_ambash     armor     legendary rarity, req_level=1
legendary_ring_velur       accessory legendary rarity, req_level=1
legendary_staff_efreto     weapon    legendary rarity, req_level=1
legendary_amulet_nathos    accessory legendary rarity, req_level=1
legendary_cape_aveol       armor     legendary rarity, req_level=1
```

**Bug adiacente #3**: 6 legendary con rarità lowercase E `required_adventurer_level: 1`. Anche il gate condiviso (`resolve_item_required_level`) restituirebbe 1 (spec > 1, non applica fallback). Un Lv1 potrebbe indossarli. Fuori scope R16.5.4b ma da tracciare in un round di seed-integrity.

---

## 4. Bug rilevati in `auto_equip.py` (in ordine di severità)

### 🔴 BUG #A — Formula fitness legge campo inesistente `stats`
**File:** `app/equipment/auto_equip.py:56-63`
```python
def _compute_fitness(item, primary, secondaries):
    stats = item.get("stats") or {}          # SEMPRE {}
    base = float(item_equip_power(item))
    primary_boost = float(stats.get(primary, 0)) * 2   # sempre 0
    secondary_boost = sum(float(stats.get(s,0)) for s in secondaries) * 1  # sempre 0
    return base + primary_boost + secondary_boost
```
**Impatto:** l'auto-equip class-aware **non è mai stato class-aware**. Il ranking è = `power_score` puro (con penalty 0.5 sui warning). Un `intellect_bonus:10` per un mage non pesa più di uno `strength_bonus:10`.

**Fix atteso:** leggere `item.get(f"{primary}_bonus", 0)` + `sum(item.get(f"{s}_bonus", 0) for s in secondaries)`.

### 🔴 BUG #B — Level gate su campi sbagliati
**File:** `app/equipment/auto_equip.py:163`
```python
req_lv = int(it.get("required_level") or it.get("level_requirement") or 1)
```
**Impatto:** i campi `required_level` e `level_requirement` **non esistono nel DB**. I campi reali sono `required_adventurer_level` (canonico R11.3, 113/113) e `level_required` (legacy, 102/113). L'auto-equip **NON usa mai il vero gate** e permetterebbe di equipaggiare oggetti Rare/Epic/Legendary sotto-livello se il caller diretto (`equip_item_service`) non fosse a sua volta protetto.

**Nota di sicurezza:** `equip_item_service` (chiamato da auto-equip come conseguenza dello swap) invoca `enforce_item_level_requirement` (level_gate.py) e lancerebbe 423. Attualmente il 423 finirebbe nel `except Exception` di `auto_equip.py:213` e produrrebbe solo un warning "equip fallito". Quindi in pratica **il gate finale c'è**, ma:
1. lo scoring pre-selezione spreca cicli valutando item invalidi;
2. il warning esposto al FE è generico e non spiega "livello troppo basso";
3. il messaggio 423 dettagliato viene perso.

**Fix atteso:** importare `resolve_item_required_level` e usarla nel loop `for it in items_pool`.

### 🟠 BUG #C — `item_equip_power` locale ignora i `*_bonus`
**File:** `app/equipment/auto_equip.py:33-48`
```python
def item_equip_power(item):
    if "power_score" in item:
        return int(item.get("power_score") or 0)   # ← esce subito
    stats = item.get("stats") or {}
    return sum(int(v) for v in stats.values() if isinstance(v,(int,float)))
```
Poiché **tutti** gli equippables hanno `power_score`, la funzione ritorna solo quello e ignora i `*_bonus`. La funzione canonica in `expeditions/formulas.py:95` invece somma `strength_bonus + agility_bonus + intellect_bonus + endurance_bonus + faith_bonus + power_score`.

**Impatto:** il `base` è sottostimato in modo uniforme (bug simmetrico, non altera il ranking relativo perché sottostima tutto), MA `score_before`/`score_after` esposti al FE non riflettono il vero equipment power.

**Fix atteso:** eliminare la copia locale e importare `from app.expeditions.formulas import item_equip_power`.

### 🟠 BUG #D — Warlock e Alchemist senza copertura recommended_classes
Vedi §3.4. Data-side, fuori scope codice ma da flaggare come blocker UX per queste due classi.

### 🟡 BUG #E — `_stat_delta` legge `.stats` inesistente
**File:** `app/equipment/auto_equip.py:141-153`
```python
def _stat_delta(old, new):
    a = (old or {}).get("stats") or {}   # {} sempre
    b = new.get("stats") or {}           # {} sempre
    …
```
**Impatto:** la narrativa bilingue mostrata al FE (`+X Strength`) è **sempre "+0"** e il campo `reasons[].stat_delta` è sempre `{}`. Il `primary_gain` mostrato all'utente è sempre 0 → messaggi generici.

**Fix atteso:** costruire delta dai `*_bonus` reali.

### 🟡 BUG #F — Fetch inventory/items senza sort deterministico
**File:** `app/equipment/auto_equip.py:109-123`
```python
inv_rows = db.inventory_items.find({...}).to_list(2000)     # no .sort()
items_pool = db.items.find({...}).to_list(len(item_ids))    # no .sort()
```
**Impatto:** in caso di parità di fitness (tutt'altro che raro data la fitness ridotta a power_score), il tie-break dipende dall'ordine di inserimento Mongo. Idempotency test-friendly ma **non riproducibile** su ambienti freschi/backup restore. Segnalato dall'utente come pattern generale da correggere.

**Fix atteso:** `.sort([("id", 1)])` o `.sort([("power_score",-1),("id",1)])` esplicito.

### 🟢 BUG #G (osservazionale) — Rarità case-mixed
Vedi §3.3. Non fatalmente blocking l'auto-equip (l'items con rarity `legendary` lowercase hanno tutti `required_adventurer_level: 1` esplicito → non richiedono fallback rarity→level), ma è un debito tecnico che compromette dashboard/statistiche.

### 🟢 BUG #H (osservazionale) — `random.choice` non presente
Search grep in `auto_equip.py`: **nessuna occorrenza di `random.` o `randint`**. L'ordinamento è deterministico modulo BUG #F.

### 🟢 BUG #I — `write_audit` non passa `related_entity_id`
**File:** `app/equipment/auto_equip.py:267-276`
Non passa `related_entity_id=adv["id"]` (usato altrove come convenzione). L'ID adventurer è solo in metadata → dashboard di audit non filtrabili per avventuriero.

---

## 5. Proposta di formula scoring class-aware (per STEP 2, da approvare)

### 5.1 Obiettivi
1. Premiare stat primaria della classe (peso alto).
2. Premiare stat secondarie (peso medio).
3. Considerare `power_score` come baseline generica (peso basso).
4. Penalizzare **prima del ranking** i warning di compatibilità.
5. Escludere **prima del ranking** item sotto-livello via `resolve_item_required_level`.
6. Determinismo assoluto: sort esplicito.

### 5.2 Formula proposta

```python
PRIMARY_WEIGHT   = 3.0
SECONDARY_WEIGHT = 1.5
POWER_WEIGHT     = 1.0
WARNING_PENALTY  = 0.5          # invariato, moltiplicativo sul totale

def _stat_bonus(item, stat_name):
    return int(item.get(f"{stat_name}_bonus", 0) or 0)

def _class_aware_fitness(item, primary, secondaries):
    primary_score   = _stat_bonus(item, primary) * PRIMARY_WEIGHT
    secondary_score = sum(_stat_bonus(item, s) for s in secondaries) * SECONDARY_WEIGHT
    generic_score   = int(item.get("power_score", 0) or 0) * POWER_WEIGHT
    # Bonus tie-break: stat-tag alignment con la classe (opzionale, +2 flat se
    # `primary` è nei `stat_tags` dell'item — utile per differenziare item
    # con identici bonus numerici ma "tematici" per la classe).
    tag_bonus = 2.0 if primary in (item.get("stat_tags") or []) else 0.0
    return primary_score + secondary_score + generic_score + tag_bonus
```

### 5.3 Filtri pre-ranking (hard exclusions)

```python
def _is_candidate(item, adv, adv_level):
    if item.get("item_type") != expected_slot_type: return False
    req_level = resolve_item_required_level(item)          # ← NUOVO
    if req_level > adv_level: return False
    verdict = check_equip_compatibility(adv, item)
    if verdict["severity"] == "block": return False
    return True, verdict
```

### 5.4 Sort deterministico

```python
candidates.sort(key=lambda pair: (
    -pair[0],                           # fitness DESC
    -int(pair[1].get("power_score", 0)),# tie: power_score DESC
    pair[1].get("id", "")               # tie finale: id ASC
))
```

### 5.5 Esempio numerico (mage Lv10 vs due weapon)

- **Legendary "drake_slayer_blade"** (`strength:10, agility:3, power_score:60`, req_lv:12): **escluso** (livello) ✅
- **Epic "arcane_focus"** (ipotetico) (`intellect:5, endurance:2, power_score:8`): fit = `5*3 + 2*1.5 + 8*1 = 26`
- **Uncommon "mage_staff"** (ipotetico) (`intellect:3, power_score:4`): fit = `3*3 + 0 + 4 = 13`

Mage sceglierebbe il focus arcano ✅ (oggi sceglie il drake slayer se equippabile, per via del `power_score:60` che schiaccia tutto).

---

## 6. Checkpoint richiesto (6 punti)

### ✅ Punto 1 — Endpoint auto-equip esiste?
**Sì.** `POST /api/adventurers/{id}/auto-equip` (`equipment/routes.py:47`), delega a `auto_equip_adventurer` (`equipment/auto_equip.py`, 303 righe).

### ✅ Punto 2 — Come calcola oggi il "best item"?
Loop per slot (weapon/armor/accessory) sui `items_pool` derivati da `inventory_items`, filtro (item_type, livello, block-compatibility), scoring `fitness = power_score + 2*primary_stat + 1*secondary_stat`, penalty ×0.5 sui warning, sort DESC, sostituzione se `best_fit > current_fit`. **In pratica** il ranking è quasi `power_score` puro perché i boost stat leggono un campo inesistente.

### ✅ Punto 3 — Classe + primary/secondary stat entrano nella logica?
**Solo formalmente.** Il codice recupera correttamente `primary_stat`/`secondary_stats` da `adventurer_classes` (che li ha), ma li applica a `item.get("stats")` che è `{}` per tutti i 113 equippables. Impatto reale = 0.

### ✅ Punto 4 — `min_level` viene rispettato dall'auto-equip?
**No, non nel loop dell'auto-equip.** Legge `required_level`/`level_requirement` (campi inesistenti). Il gate finale scatta comunque perché `equip_item_service` chiama `enforce_item_level_requirement`, ma il 423 finisce dentro un `except Exception` generico e produce solo un warning "equip fallito ({name})" al FE. Serve invocare `resolve_item_required_level` esplicitamente nel filtro `_is_candidate`.

### ✅ Punto 5 — `class_catalog` (o equivalente) esiste con `primary_stat`/`secondary_stat`?
**Sì**, ma la collection si chiama `adventurer_classes` (non `class_catalog`, che è vuota).
- 14 documenti, tutti con `primary_stat` (string, sempre valorizzato) e `secondary_stats` (list[string], sempre valorizzato).
- Nessun campo da inventare o migrare.

### ✅ Punto 6 — Formula proposta (dettagliata in §5)

```
fitness(item, class) =
    3.0 * item.{primary_stat}_bonus
  + 1.5 * sum(item.{secondary_stat}_bonus)
  + 1.0 * item.power_score
  + 2.0 if primary_stat in item.stat_tags else 0
Warning verdict → fitness *= 0.5
Filtri hard: item_type match, resolve_item_required_level(item) ≤ adv.level, severity != block
Sort: (fitness DESC, power_score DESC, id ASC)
```

Pesi tunabili in cima al modulo come costanti (`PRIMARY_WEIGHT`, `SECONDARY_WEIGHT`, `POWER_WEIGHT`, `WARNING_PENALTY`).

---

## 7. Bug adiacenti rilevati (NON fixare senza approvazione)

| ID | Severità | Descrizione | Scope suggerito |
|---|---|---|---|
| ADJ-1 | 🟡 Data | Rarity con case-mismatch (`legendary`/`epic`/`rare` lowercase, ~11 docs) | Nuovo round "seed integrity" |
| ADJ-2 | 🔴 Data | 6 Legendary equippables con `required_adventurer_level: 1` → bypassano il gate R16.5 pure equipaggiando manualmente | Blocker P0 separato: `round1655_legendary_min_level_backfill.py` |
| ADJ-3 | 🔴 Data | `warlock` + `alchemist`: ZERO items con `recommended_classes` compatibile → auto-equip inutile per queste classi | P0 separato: seed patch items per classi post-R16 |
| ADJ-4 | 🟡 Codice | `item_equip_power` locale in `auto_equip.py` shadowa il canonico e sottostima `equipment_power`; anche `score_before`/`score_after` esposti al FE sono sbagliati | Includibile in STEP 2 R16.5.4b se approvato (rimozione locale, import canonico) |
| ADJ-5 | 🟡 Codice | Fetch `items_pool`/`inv_rows` senza `.sort(...)`. Determinismo dipende da ordine Mongo | Includibile in STEP 2 (aggiungere sort esplicito) |
| ADJ-6 | 🟢 Codice | `write_audit` non passa `related_entity_id=adv.id`. Adventurer ID solo in metadata | Includibile in STEP 2 (1 riga) |
| ADJ-7 | 🟢 Codice | Il ramo `except Exception` in equip fallito nasconde il 423 strutturato del level_gate → warning generico | Da valutare: bubble-up il 423 detail come `warnings[i].code` |

---

## 8. Perimetro raccomandato per STEP 2

**In scope (Class-Aware Fix):**
- Fix BUG #A (formula legge campi giusti `*_bonus`)
- Fix BUG #B (`resolve_item_required_level` come gate)
- Fix BUG #E (`_stat_delta` legge `*_bonus`)
- ADJ-4 (rimuovere shadow di `item_equip_power`)
- ADJ-5 (sort deterministico)

**Fuori scope (backlog separato):**
- ADJ-1/ADJ-2 (data fix: rarity casing + legendary req_level backfill)
- ADJ-3 (data fix: warlock/alchemist item coverage)
- ADJ-6/ADJ-7 (polish audit + bubble-up 423)

**Test da aggiungere in STEP 2:**
- mage Lv10 con arcane focus + drake slayer sub-livello → sceglie arcane focus
- warrior Lv12 con drake slayer disponibile → lo equipaggia (primary=strength coincide)
- alchemist qualunque → tutti gli slot restano `unchanged` con reason `no_compatible_item` (documentare come limite noto data-side, ADJ-3)
- idempotency: seconda invocazione con inventory invariato = 0 swap
- rarity=`legendary` lowercase Lv-1: continuano a essere equippabili (documentare come debito, ADJ-2)

---

## 9. STOP — Attendo approvazione

Nessuna riga di codice è stata modificata. Nessuna scrittura è stata effettuata sul DB (solo `find` / `aggregate` / `count_documents`).

Prossima azione richiesta all'utente:
1. Approvazione formula scoring (§5) e pesi.
2. Conferma perimetro STEP 2 (§8) o richiesta di allargamento agli ADJ-*.
3. Decisione su ADJ-2/ADJ-3 (data fixes): round separato o incluso.
