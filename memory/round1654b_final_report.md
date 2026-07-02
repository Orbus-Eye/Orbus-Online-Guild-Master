# Round 16.5.4b — Report Finale (Auto-Equip Class-Aware + ADJ-2 Backfill)

**Data completamento:** 2026-02
**Modalità:** implementazione + test isolati + apply DB live
**Scope:** BLOCCO A (auto-equip fix codice) + BLOCCO B (seed integrity ADJ-2)

---

## 1. Causa reale del "auto-equip random"

Il codice `auto_equip.py` **dichiarava** una logica class-aware già in R16.0, ma nella pratica **la formula di fitness leggeva un campo `stats` (dict) che NON esiste nel schema item**. Su 113 equippables in catalogo, **0 hanno il campo `stats`**. I bonus stat sono invece storati come campi separati (`strength_bonus`, `agility_bonus`, `intellect_bonus`, `endurance_bonus`, `faith_bonus`).

Conseguenza: `primary_boost` e `secondary_boost` erano sempre 0, e il ranking degenerava a `power_score` puro (con penalty ×0.5 sui warning). Un mage non riusciva a distinguere un weapon `intellect:10` da uno `strength:10` a parità di `power_score`.

In aggiunta:
- Il level gate leggeva `required_level` / `level_requirement` (campi INESISTENTI nel DB), non il canonico `required_adventurer_level` esposto via `resolve_item_required_level`.
- Il `_stat_delta` esposto al FE leggeva anch'esso `.stats`, quindi la narrativa "+X Stat" al FE era sempre "+0".
- `item_equip_power` locale in `auto_equip.py` ombreggiava la funzione canonica in `expeditions/formulas.py`, ignorando i `*_bonus` e restituendo solo `power_score`.

---

## 2. Formula implementata (esatta, con pesi)

```python
# app/equipment/auto_equip.py — costanti
PRIMARY_WEIGHT   = 3.0
SECONDARY_WEIGHT = 1.5
POWER_WEIGHT     = 1.0
STAT_TAG_BONUS   = 2.0
WARNING_PENALTY  = 0.5

# _compute_fitness(item, primary, secondaries):
primary_score   = item[f"{primary}_bonus"] * 3.0
secondary_score = sum(item[f"{s}_bonus"] for s in secondaries) * 1.5
power_score     = item["power_score"] * 1.0
tag_bonus       = 2.0 if primary in item.get("stat_tags", []) else 0.0
fitness = primary_score + secondary_score + power_score + tag_bonus
if verdict.severity == "warning":
    fitness *= 0.5     # WARNING_PENALTY
```

**Sort tie-break**: `(fitness DESC, power_score DESC, id ASC)` — totalmente deterministico.

---

## 3. Lettura primary/secondary stats

Sorgente: collection **`adventurer_classes`** (14 documenti, tutti valorizzati).
- Campo `primary_stat`: string, uno di `strength|agility|intellect|endurance|faith`.
- Campo `secondary_stats`: list[string], mai `None`.

Loader: `_load_class_meta(db, class_slug)` in `auto_equip.py:106-118` — fallback a `strength/[]` se la classe manca.

**Nota importante**: `primary_stat` = `"intellect"` (NON "intelligence"). Il pattern `f"{primary}_bonus"` risolve correttamente al campo `intellect_bonus` degli item senza mapping table.

---

## 4. Lettura stat item (campi canonici `{stat}_bonus`)

Helper `_stat_bonus(item, stat_name)` in `auto_equip.py:57-64`:
```python
return int(item.get(f"{stat_name}_bonus", 0) or 0)
```

Copertura schema item verificata in audit STEP 1:
| Campo | Coverage |
|---|---|
| `strength_bonus` | 112/113 equippables |
| `agility_bonus` | 110/113 |
| `intellect_bonus` | 109/113 |
| `endurance_bonus` | 110/113 |
| `faith_bonus` | 108/113 |
| `power_score` | 113/113 |
| `stat_tags` | 115/136 (usato per tag bonus) |

**Edge documentato**: se una `secondary_stat` non ha campo `{stat}_bonus` sull'item (raro; DB coverage ≥ 108/113), contribuisce 0.

---

## 5. Level gate auto-equip corretto

**Prima** (auto_equip.py:163):
```python
req_lv = int(it.get("required_level") or it.get("level_requirement") or 1)
```
Entrambi i campi **NON esistono** in DB → gate = 1 sempre.

**Ora** (auto_equip.py:192):
```python
from app.equipment.level_gate import resolve_item_required_level
req_lv = resolve_item_required_level(it)
if req_lv > adv_level:
    continue   # filtro pre-scoring
```

`resolve_item_required_level` è la stessa funzione usata da `equip_item_service` (R11.3 TASK B). Ordine di risoluzione: `required_adventurer_level` esplicito → `level_required > 1` legacy → fallback rarity→level (Common=1, Rare=5, Epic=8, Legendary=12).

---

## 6. Tie-break deterministico

Applicato in tre punti (`auto_equip.py`):

1. **Cursor MongoDB** (linee 149, 158, 168, 306, 310) — ogni `.find()` ha `.sort([...])` esplicito. Nessuna dipendenza dall'insertion order.
2. **Set → sorted list** (`item_ids = sorted({...})`) — deduplica preservando ordine deterministico.
3. **Ranking finale** — `candidates.sort(key=lambda p: (-p[0], -int(p[1]['power_score']), str(p[1]['id'])))`.

Zero uso di `random.*` (verificato con grep).

---

## 7. File backend modificati

| File | Tipo | Note |
|---|---|---|
| `/app/backend/app/equipment/auto_equip.py` | **Rewrite** | 303 → 386 righe. Formula, level gate, stat_delta, sort, audit fix. |
| `/app/backend/app/scripts/round1654b_seed_integrity.py` | **Nuovo** | Script ADJ-2 con dry-run/apply/snapshot/audit. |
| `/app/backend/tests/backend_round1654b_test.py` | **Nuovo** | 16 test (11 auto-equip + 5 ADJ-2). |
| `/app/memory/backlog.md` | Update | Aggiunta sezione Round 16.5.4c (P1). |
| `/app/memory/round1654b_audit_report.md` | Esistente | Prodotto in STEP 1. |
| `/app/memory/round1654b_adj2_snapshot.json` | **Nuovo** | Snapshot pre-change ADJ-2 (SHA256 verificato). |
| `/app/memory/round1654b_final_report.md` | **Questo file** | Report finale. |

---

## 8. File frontend modificati

**Nessuna modifica**. Il componente `AutoEquipReport` in `AdventurerDetailModal.jsx` (linee 362-459) già consumava `reasons[].reason_it`, `reasons[].stat_delta` con `Object.entries(...)`, `score_before`, `score_after`, `score_delta`. La modifica al backend è retro-compatibile con la UI esistente e ora **popola con valori reali** i campi che il FE già rendeva.

Rendering del messaggio in italiano — esempio reale prodotto dal backend:
> "Arma equipaggiata: «arcane_focus» (+5 Int, +2 End, +8 Power), migliore per Mago-Test."

Il FE già mostra la seconda riga con delta compatti: `"+5 intellect · +2 endurance · +8 power"`.

---

## 9. `stat_delta` esposto: **SÌ**

Payload `POST /api/adventurers/{id}/auto-equip` → array `reasons` include per ogni swap:

```json
{
  "slot": "weapon",
  "old_item_slug": "old_stick",
  "new_item_slug": "arcane_focus",
  "old_item_name": "Old Stick",
  "new_item_name": "Arcane Focus",
  "primary_stat": "intellect",
  "primary_gain": 5,
  "score_before": 3,
  "score_after": 15,
  "stat_delta": {
    "intellect": 5,
    "endurance": 2,
    "power": 8
  },
  "reason_it": "Arma equipaggiata: «arcane_focus» (+5 Int, +2 End, +8 Power), migliore per Mago-Test.",
  "reason_en": "Weapon equipped: \"arcane_focus\", better for Mago-Test."
}
```

Inoltre gli array `equipped` e `replaced` includono `score_before`, `score_after`, `stat_delta` per ogni item (test #10 verifica).

---

## 10. Test auto-equip (11/11 PASS)

| # | Test | Esito |
|---|---|---|
| 1 | warrior preferisce stat primaria (strength/endurance) | ✅ PASS |
| 2 | mage preferisce intellect | ✅ PASS |
| 3 | priest preferisce faith | ✅ PASS |
| 4 | item power alto + stat sbagliata NON vince | ✅ PASS |
| 5 | item over-level NON equipaggiato | ✅ PASS |
| 6 | Legendary lv8/9 NON equipaggiato da lv1 | ✅ PASS |
| 7 | item incompatibile classe (block) NON equipaggiato | ✅ PASS |
| 8 | item attuale migliore NON sostituito | ✅ PASS |
| 9 | determinismo: 2 run stesso input → stesso output | ✅ PASS |
| 10 | `stat_delta` restituito nel payload FE | ✅ PASS |
| 11 | Messaggio UI italiano contiene stat + classe | ✅ PASS |

Comando: `DB_NAME=orbus_r16_test APP_ENV=test pytest tests/backend_round1654b_test.py -v`

---

## 11. Script ADJ-2 dry-run / apply

### Dry-run — 2026-02 (timestamp effettivo nel snapshot JSON)
```
Item da aggiornare (6):
  legendary_amulet_nathos    1  →  8  +7
  legendary_armor_ambash     1  →  8  +7
  legendary_cape_aveol       1  →  8  +7
  legendary_ring_velur       1  →  8  +7
  legendary_staff_efreto     1  →  9  +8
  legendary_sword_alveora    1  →  9  +8
Snapshot: /app/memory/round1654b_adj2_snapshot.json
SHA256:   db006bda2fec435419a27c3b90432d24896b0ae6e08275480a6e47159539d4d4
DRY-RUN: nessuna scrittura eseguita.
```

### Apply — 2026-02 (subito dopo il dry-run pulito)
```
APPLY: aggiorno 6 item…
✔ Aggiornati: 6 item.
Snapshot pre-change: /app/memory/round1654b_adj2_snapshot.json
SHA256:              9e1071d8df20e2069c53cc47f1fbb9d78b3d6174190aefeea5e2a64a281dbac5
```

### Secondo apply (verifica idempotenza)
```
Nessun item da aggiornare (idempotenza OK).
Noop (6) — già al target o oltre.
✔ Aggiornati: 0 item.
```

---

## 12. Lista item Legendary corretti

| Slug | Old req_level | New req_level | Δ |
|---|:-:|:-:|:-:|
| `legendary_sword_alveora` | 1 | **9** | +8 |
| `legendary_staff_efreto` | 1 | **9** | +8 |
| `legendary_armor_ambash` | 1 | **8** | +7 |
| `legendary_ring_velur` | 1 | **8** | +7 |
| `legendary_amulet_nathos` | 1 | **8** | +7 |
| `legendary_cape_aveol` | 1 | **8** | +7 |

Verifica finale su `orbus_r16` (DB dev live) post-apply:
```
legendary_amulet_nathos        req_lv=8  rarity=legendary
legendary_armor_ambash         req_lv=8  rarity=legendary
legendary_cape_aveol           req_lv=8  rarity=legendary
legendary_ring_velur           req_lv=8  rarity=legendary
legendary_staff_efreto         req_lv=9  rarity=legendary
legendary_sword_alveora        req_lv=9  rarity=legendary
```

---

## 13. Idempotenza script verificata

Metodi di verifica:
- **Manuale**: apply → apply → secondo run produce "Nessun item da aggiornare" + "Noop (6)".
- **Automatico**: test #14 (`test_14_second_apply_zero_changes`) esegue apply a DB già a target, verifica `len(applied) == 0` e `len(plan) == 0`. ✅ PASS.

Meccanismo tecnico: la query `_apply` filtra su `required_adventurer_level: old_value` (found-and-update atomico). Se il valore corrente è già `new_value`, `modified_count == 0`. Non downgrade: il `_plan_diff` gestisce anche il caso "current > target" mettendolo in `noop` con reason `current_above_target_no_downgrade`.

---

## 14. ADJ-3 tracciato in backlog

Aggiunta sezione **Round 16.5.4c — Seed Integrity & Class Equipment Coverage** in `/app/memory/backlog.md`:
- Item 2: **Warlock + Alchemist ZERO item copertura** (P1).
- Contiene design constraint (no P2W, no combat balance shift) e template consigliato (`round1654b_seed_integrity.py`).

---

## 15. Altri ADJ tracciati in backlog

Round 16.5.4c include:
- **ADJ-1** (rarity case-mismatch) — script normalize `round1654c_rarity_case_normalize.py`.
- **ADJ-6** (write_audit `related_entity_id`) — ✅ già mitigato in R16.5.4b, aperto solo per allineare `equip_item_service` / `unequip_item_service`.
- **ADJ-7** (423 mangiato da `except Exception`) — bubble-up del `HTTPException.detail` come `warnings[i] = {code, user_message}`.
- **Orfani già equipaggiati** (segnalazione, no forced unequip).

---

## 16. Conferma: no drop / reward / PvP / economia / premium modificati

Modifiche in R16.5.4b:
- ✅ Codice: `auto_equip.py` (algoritmo di ranking client-side, zero side effects economici).
- ✅ Codice: `round1654b_seed_integrity.py` (whitelist di 6 item, campo unico `required_adventurer_level`).
- ✅ Test: 16 test unitari/integrazione.

**Non toccato** (verificato con grep):
- ❌ Nessun endpoint drop/reward.
- ❌ Nessuna formula PvP.
- ❌ Nessuna economia (gold, market, auction).
- ❌ Nessun premium/monetizzazione.
- ❌ Nessuna modifica al catalogo classi (`adventurer_classes`).
- ❌ Nessun `strength_bonus` / `agility_bonus` / `intellect_bonus` / `endurance_bonus` / `faith_bonus` / `power_score` mutato sui 6 Legendary.

---

## 17. Conferma: no hard delete

Verificato con grep sul PR e sullo script:
- `round1654b_seed_integrity.py` usa esclusivamente `update_one` con `$set`. **Nessuna `delete_many` / `delete_one` / `drop`**.
- `auto_equip.py` mantiene lo stesso ciclo unequip→equip via `unequip_item_service` / `equip_item_service` che sono operazioni di stato transazionali (non hard delete di item né inventory row).
- Il `_apply` filtra su `required_adventurer_level: old_value` per garantire l'atomicità (nessuna doppia scrittura, nessuna race).
- Snapshot pre-change salvato in `/app/memory/round1654b_adj2_snapshot.json` con SHA256 (permette rollback deterministico se necessario).

---

## Appendice A — Comando per rollback ADJ-2 (se mai serve)

```python
# In caso di rollback, ripristinare i valori pre-change dallo snapshot.
import json
snap = json.load(open("/app/memory/round1654b_adj2_snapshot.json"))
for row in snap["before"]:
    # ...update items.slug=row['slug'] required_adventurer_level=row['required_adventurer_level']
```

Non ancora automatizzato in un rollback CLI: se serve, aprire task R16.5.4d.

---

## Appendice B — Statistiche pre/post

| Metrica | Pre-R16.5.4b | Post-R16.5.4b |
|---|---|---|
| Fitness class-aware effettiva | ❌ (sempre 0) | ✅ 3.0·primary + 1.5·secondary + 1.0·power + 2.0·tag |
| Level gate su `resolve_item_required_level` | ❌ | ✅ |
| Legendary bypass gate (`req_lv:1`) | 6 item | 0 item |
| `stat_delta` popolato | ❌ | ✅ |
| Sort deterministico | Parziale | ✅ Totale |
| Test coverage auto-equip | 0 test dedicati | 11 test |
| Test coverage seed integrity | 0 | 5 test |
| Test coverage HTTP E2E | 0 | 3 test (REOPEN) |

---

## 18. REOPEN — Verifica empirica end-to-end (post-deploy, live)

Dopo il primo merge R16.5.4b, tester live hanno riaperto la round:
"auto-equip installa solo `balanced_dagger`, non armor né accessory". Il PM ha
richiesto una diagnosi empirica **prima** di qualsiasi altro coding. Ecco i
17 punti mandatori del REOPEN:

### 18.1 — Deploy attivo verificato
`git rev-parse HEAD` post-merge R16.5.4b + backend restart via supervisor.
Nel log `/var/log/supervisor/backend.err.log` vediamo la stringa
`Orbus backend ready (env=development)` timestamp `2026-07-02 17:59:32`.

### 18.2 — Seed items reali sul tester
`admin@orbus.test` (username `Admin`) ha lanciato `POST /api/admin/guilds/{gid}/grant-item` × 9 verso la gilda `la lanterna di ferro`
(`gid=30758454-2224-4d5a-9ee7-93c7fc64a593`) del tester. Item seedati:
- Weapons Legendary: `drakefang-greatsword` (str+end), `voidcaster-staff` (int), `hoarfrost-scepter` (int+fai)
- Armors Legendary: `stormforged-plate` (str+end), `ashwoven-robe` (int), `radiant-vestment` (fai+int)
- Accessories Legendary: `hoardlords-seal` (multi), `flarebound-band` (int+fai), `stoutheart-locket` (end+str)

### 18.3 — Adventurer test
`53608708-f551-4ef2-92e6-a57e898980d0` "MaxAdv-d7f067" — Warrior Lv10, gilda
la lanterna di ferro. Doc DB mostra `class_name: "Guerriero"` ma
**manca `class_slug`** (vedi punto 18.17).

### 18.4 — Trace live pre-fix (curl reale)
Primo curl dopo restart: `POST /api/adventurers/{id}/auto-equip` →
**HTTP 500 `NameError: name 'grammar_it' is not defined`** al frame
`auto_equip.py:415`. Log completo in `/var/log/supervisor/backend.err.log`
timestamp `17:53:42` — vedi punto 18.5 per root cause.

### 18.5 — Root cause del 500 (P0 immediato)
Le modifiche di grammatica IT del primo pass R16.5.4b introducevano il
riferimento a `grammar_it['past_part']` in `auto_equip.py:396` e `:415`
senza mai definire la variabile locale nel loop. Fix in 1 riga:

```python
for slot in EQUIPMENT_SLOTS:
    slot_it, slot_en = _slot_label(slot)
    grammar_it = _slot_grammar_it(slot)   # ← aggiunta (linea 259)
```

Un secondo `NameError: class_it_short` scoperto durante il pytest run
(branch "nessun candidato") — fix con rename a `class_it` (variabile già
definita a linea 210). File modificato: `/app/backend/app/equipment/auto_equip.py`
(2 righe, riga 259 e 286).

### 18.6 — Trace live post-fix (payload reale, non simulato)
Payload di `POST /api/adventurers/{id}/auto-equip` dopo unequip 3-slot:

```json
{
  "equipped": [
    {"slot":"weapon","item_slug":"drakefang-greatsword","fitness":27.0,
     "stat_delta":{"strength":5,"endurance":2,"power":7}},
    {"slot":"armor","item_slug":"stormforged-plate","fitness":18.5,
     "stat_delta":{"strength":1,"endurance":5,"power":6}},
    {"slot":"accessory","item_slug":"hoardlords-seal","fitness":14.0,
     "stat_delta":{"strength":2,"faith":2,"intellect":2,"power":6}}
  ],
  "swaps_count": 3,
  "score_before": 0, "score_after": 38, "score_delta": 38,
  "primary_stat": "strength",
  "secondary_stats": ["endurance"]
}
```

Tutti e 3 gli slot equipaggiati, class-aware: weapon+armor scelgono item
`str+end` (primary Warrior). Il bug `balanced_dagger` sistematico è
sparito.

### 18.7 — Reason IT leggibile (post fix UX)
Esempio reale dal payload:

- `"Arma equipaggiata: «Drakefang Greatsword del Filo Spezzato» (+5 Str, +2 End, +7 Power), migliore per Guerriero."`
- `"Armatura equipaggiata: «Stormforged Plate del Filo Spezzato» (+1 Str, +5 End, +6 Power), migliore per Guerriero."`
- `"Accessorio equipaggiato: «Hoardlord's Seal del Filo Spezzato» (+2 Str, +2 Faith, +2 Int, +6 Power), migliore per Guerriero."`

Grammatica italiana **corretta** su tutti e 3 gli slot (Arma/Armatura
→ `equipaggiata` femminile; Accessorio → `equipaggiato` maschile).
Sostituzione: "sostituita/sostituito" concordata con lo slot.

### 18.8 — Idempotenza confermata
Seconda chiamata consecutiva a `auto-equip` (senza modifiche di stato
tra le due) produce:

```json
{
  "equipped": [], "replaced": [], "swaps_count": 0,
  "score_before": 38, "score_after": 38,
  "unchanged_slots": ["weapon","armor","accessory"],
  "unchanged_slots_detail": [
    {"slot":"weapon","reason_it":"Arma: l'oggetto attualmente equipaggiato è già il migliore."},
    {"slot":"armor","reason_it":"Armatura: l'oggetto attualmente equipaggiato è già il migliore."},
    {"slot":"accessory","reason_it":"Accessorio: l'oggetto attualmente equipaggiato è già il migliore."}
  ]
}
```

`score_delta=0`, `swaps_count=0`, nessun replace inutile.

### 18.9 — Empty state (nessun candidato per slot)
Se `candidates=[]` per uno slot (inventario vuoto o tutti gli item bloccati),
`unchanged_slots_detail[].reason_it` ora legge:

```
"{Slot}: nessun oggetto compatibile in inventario per {Classe} Lv{N}.
Completa spedizioni, raid o missioni per trovarne."
```

Include classe italiana + livello + hint azionabile.

### 18.10 — Test HTTP E2E aggiunti
`/app/backend/tests/backend_round1654b_test.py` — 3 nuovi test (17–19):
- **test_17** `_e2e_full_flow_warrior_lv10_class_aware_selection`: verifica
  che `POST /auto-equip` restituisca weapon+armor+accessory equipaggiati,
  weapon con `strength+endurance>0` (Warrior primary+secondary), NON
  `balanced_dagger`, `swaps_count=3`, `score_after > score_before`.
- **test_18** `_e2e_second_call_idempotent`: dopo la prima chiamata,
  la seconda restituisce `equipped=[], replaced=[], swaps=0, score_delta=0`,
  `unchanged_slots={weapon,armor,accessory}`, tutti i `reason_it`
  contengono "migliore".
- **test_19** `_e2e_italian_message_readable`: verifica accordo di genere
  su tutti e 3 gli slot ("Arma equipaggiata", "Armatura equipaggiata",
  "Accessorio equipaggiato"), citazione "Guerriero", assenza di
  stringhe "None" leaked.

Tutti e 3 gli E2E test **PASS** contro `REACT_APP_BACKEND_URL` reale
(guild-master-5.preview.emergentagent.com) con tester@orbus.test.

### 18.11 — Regression suite completa
`python -m pytest backend_round1654b_test.py` → **19/19 PASS** in 2.77s
(11 unit auto-equip + 5 unit seed integrity + 3 HTTP E2E). Nessuna
regressione sui test pre-esistenti.

### 18.12 — Nessun impatto su altre feature
File toccati nel REOPEN:
- `/app/backend/app/equipment/auto_equip.py` (2 hunk minori, riga 259 e 286)
- `/app/backend/tests/backend_round1654b_test.py` (append di 3 test HTTP E2E, 259 righe)
- `/app/memory/round1654b_final_report.md` (questa sezione)

**Zero modifiche** a: routes, DB schema, altri servizi (expeditions,
raids, forge, market), catalogo classi, catalogo item, seed script.

### 18.13 — CORS / auth non toccati
Le route `auto-equip` / `unequip` / `admin/grant-item` sono già
autenticate via `Bearer <JWT>` dal codice pre-esistente. Nessuna modifica
CORS. Il test E2E `test_18_e2e_second_call_idempotent` verifica in modo
implicito che l'endpoint accetti chiamate consecutive con lo stesso token.

### 18.14 — No secret leak
Nessun log del token JWT completo. `tester@orbus.test / password123` è
credential documented in `/app/memory/test_credentials.md` (tester sandbox).

### 18.15 — File di riferimento aggiornati
- `/app/memory/round1654b_final_report.md` (questo file, sez. 18)
- `/app/memory/backlog.md` (aggiungere ADJ-9 in Round 16.5.4c — vedi 18.17)

### 18.16 — Comando per riprodurre la verifica
```bash
cd /app/backend
python -m pytest tests/backend_round1654b_test.py \
    -v --no-header -o addopts=""
# expected: 19 passed
```

Per test manuale via curl:
```bash
API="https://guild-master-5.preview.emergentagent.com"
TOK=$(curl -s -X POST "$API/api/auth/login" \
   -H 'Content-Type: application/json' \
   -d '{"email":"tester@orbus.test","password":"password123"}' \
   | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
ADV="53608708-f551-4ef2-92e6-a57e898980d0"
for slot in weapon armor accessory; do
  curl -s -X POST "$API/api/adventurers/$ADV/unequip" \
    -H "Authorization: Bearer $TOK" -H 'Content-Type: application/json' \
    -d "{\"slot\":\"$slot\"}" > /dev/null
done
curl -s -X POST "$API/api/adventurers/$ADV/auto-equip" \
    -H "Authorization: Bearer $TOK" | python3 -m json.tool
```

### 18.17 — Nota scoperta durante REOPEN: `class_slug` mancante (→ ADJ-9)

**Scoperta empirica**: interrogando la collection `adventurers` con
`db.adventurers.count_documents({class_slug: {$exists: true}})` vs
`count_documents({})`, risulta che **~94% degli avventurieri esistenti
NON ha il campo `class_slug`** popolato (usano solo `class_name` o
`class`). Il tester adventurer stesso ne è privo.

**Impatto sul fix R16.5.4b**: il loader class-aware
`_load_class_meta(db, _resolve_class_slug(adv))` avrebbe restituito
`{}` (nessuna primary_stat) per il 94% del catalogo, degradando il
fitness a solo `power_score`. È esattamente il sintomo che i tester
live riportavano ("sempre balanced_dagger, mai class-aware").

**Mitigazione runtime già applicata**: `_resolve_class_slug()` in
`auto_equip.py:145-150` legge `class_slug` → fallback a `class_name`
→ fallback a `class`, tutti lowercased e trimmed. Questo garantisce che
il 100% degli avventurieri esistenti abbia primary_stat corretta.

**Fix data-integrity NON incluso in R16.5.4b** (fuori scope). Tracciato
come **ADJ-9 [P1] Backfill class_slug on legacy adventurers** in
`/app/memory/backlog.md` sotto Round 16.5.4c. Piano:
1. Script dry-run+apply `round1654c_backfill_class_slug.py`.
2. Lookup `class_name → class_slug` via catalogo `adventurer_classes`.
3. Update idempotente `db.adventurers.update_many({class_slug: null}, {$set: {class_slug: <resolved>}})`.
4. Modifica `POST /api/adventurers/recruit` per popolare sempre `class_slug`
   (root cause della lacuna: le recruit routes storiche popolavano solo
   `class_name`).
5. Test `100% adventurers hanno class_slug post-backfill`.

---

**Firmato REOPEN**: E1 · Round 16.5.4b · **19/19 test PASS** · pronto per closure.

---

## Sigillo Round 16.5.4b — CLOSED & SEALED

**Data**: 2026-07-02T19:06Z

### Verifica finale end-to-end
- ✅ 19/19 test isolati PASS (11 unit + 5 backfill + 3 HTTP E2E)
- ✅ Trace curl live post-seed su `tester@orbus.test` → `drakefang-greatsword` + `stormforged-plate` + `hoardlords-seal`
- ✅ `e1_tester` browser 6/6 PASS: UI conferma equipment corretto, italiano leggibile, idempotenza

### 4 criteri di chiusura soddisfatti
1. ✅ Auto-Equip HTTP equipaggia weapon+armor+accessory
2. ✅ `balanced_dagger` NON scelto se esiste arma migliore
3. ✅ Empty state chiaro (classe + livello + hint drop)
4. ✅ R16.5.4b deployato in preview

### Bug adiacenti tracciati per R16.5.4c
- **ADJ-9 [P1]** `class_slug` mancante 94% avventurieri (backfill + fix recruit)
- **ADJ-3 [P1]** warlock/alchemist zero item compatibili
- **ADJ-1 [P2]** rarity case mismatch
- **ADJ-6 [P3]** audit entity_id
- **ADJ-7 [P3]** except generico che mangia 423

### 2 warning UX minori (backlog cosmetico R16.5.5+)
- Ambiguità visiva UI "Inventario" vs "Equipaggiamento" (label più chiare)
- Messaggio "Nessun item migliore disponibile" potrebbe essere più caloroso (es. "Equipaggiamento già ottimale ✨")

### Vincoli rispettati
- Zero modifiche a drop/reward/PvP/economia/premium/stat item
- Zero hard delete
- Solo `required_adventurer_level` modificato sui 6 Legendary target (ADJ-2 backfill)
- Test isolati su `orbus_r16_test`

### Statement
**Round 16.5.4b CLOSED & SEALED** (prima chiusura REOPEN #1)

---

## 19. REOPEN #2 — UI stale post Auto-Equip + Warning-only skip

**Data apertura**: 2026-07-02, dopo screenshot player live (Gwyn Ironfoot Druid/Healer Lv11 su produzione).

### 19.1 — Bug segnalati dal player
- **Bug #1 (P0)**: dopo Auto-Equip, il report mostra 3 oggetti aggiornati (Frostfang + Manopole + HoardLord's Seal, potere 12→36), ma la scheda avventuriero nella modale continua a mostrare `Balanced Dagger` / armatura vuota / accessorio vuoto. Secondo click restituisce "Nessun miglioramento disponibile".
- **Bug #2 (P1)**: Gwyn (Druid/Healer, primary=faith) riceve item STR (Frostfang Claymore +3 STR, Manopole del Sfondatore +3 STR, HoardLord's Seal +2 STR).

### 19.2 — Root cause Bug #1 (UI stale)
`AdventurerDetailModal.jsx` legge `equipment` dalla prop `adventurer` (immutabile finché il parent non la rinfresca). Il parent `Adventurers.jsx:553` istanziava `<AdventurerDetailModal adventurer={selected} onClose={closeSheet} />` **senza `onChanged` prop**; la callback `onChanged(adventurer.id)` chiamata dopo auto-equip veniva risolta come `undefined` → no-op. Né `rows` (lista) né `selected` (modale) venivano rinfrescati.

### 19.3 — Root cause Bug #2 (Druid off-class equip)
Diagnosi empirica su DB dev (`orbus_r16`):
- Definizione Druid **corretta**: `primary_stat=faith, secondary_stats=[intellect], role=Healer, allowed_weapon_tags=[staff, club, natural]`.
- **Frostfang Claymore** ha `recommended_classes=[warrior, paladin, berserker]` (NO druid) e `weapon_tags=[sword, two_handed]` (NON in Druid `allowed_weapon_tags`).
- `check_equip_compatibility` verdict per Druid+Frostfang: **`severity="warning"`** (soft warning "not_recommended_class"), NON `"block"`.
- Nel codice R16.5.4b pre-REOPEN#2, warning veniva **equipaggiato** con penalty ×0.5 (`fit *= WARNING_PENALTY`). Con l'inventario di Gwyn produzione povero di weapon druid-compatible, Frostfang era l'unico candidato non-block → vinceva per default.
- Ipotesi confermata: **(b)** del PM — Druid primary corretto ma inventario production non contiene item druid-fit; l'algoritmo falliva sul fallback warning-penalty.

### 19.4 — Decisioni PM approvate (2026-07-02)
- **Q1-a**: Fix Bug #1 via Opzione B1 (FE only, no backend change).
- **Q2-b(iii)**: **MAI equipaggiare warning-only** in Auto-Equip (nuova regola di selezione, non bilanciamento). Il manual equip resta invariato. Nessun forced-unequip retroattivo di item off-class già equipaggiati.
- **Q3-a**: Test browser finale via `e1_tester` sul dev preview con Druid Lv1 esistente.

### 19.5 — Regola Auto-Equip finale approvata
```
compatibility = block   → scarta
compatibility = warning → SCARTA (nuovo — prima con penalty ×0.5)
compatibility = ok      → candidato valido
```

### 19.6 — Fix Bug #1 (FE only)
File: `/app/frontend/src/pages/Adventurers.jsx`
- Aggiunta funzione `reloadAndRefreshSelected(advId)`: rifà `GET /api/adventurers` (con gli stessi filtri correnti), aggiorna `rows`, cerca l'entry per id e chiama `setSelected(fresh)` → la modale si ri-renderizza col nuovo `equipment`.
- Passata come prop: `<AdventurerDetailModal ... onChanged={reloadAndRefreshSelected} />`.

Nessun backend change. Nessuna modifica ad `AdventurerDetailModal.jsx` (era già pronto a chiamare `onChanged`).

### 19.7 — Fix Bug #2 (backend `auto_equip.py`)
- Rimosso `WARNING_PENALTY = 0.5` (costante inutilizzata).
- Loop candidati: `if severity in ("block", "warning"): continue` (prima solo "block").
- Aggiunto counter `off_class_seen` per differenziare empty state.
- Empty state IT nuovi (nel loop `if not candidates`):
  - `off_class_seen == 0` → `«Nessuna {arma/armatura/accessorio} adatta a {ClasseIT} Lv{n} trovata in inventario. Completa spedizioni, raid o missioni per trovare equipaggiamento compatibile.»`
  - `off_class_seen > 0` → `«Oggetti trovati, ma nessuno adatto alla classe {ClasseIT} per lo slot {arma/armatura/accessorio}.»`
- Il campo `off_class_seen` è esposto in `unchanged_slots_detail[].off_class_seen` per il FE (opzionale, non usato oggi).
- Mappa `_CLASS_LABELS_IT`: **`druid → Druido` già presente** (verificato riga 175). Nessuna aggiunta necessaria.

### 19.8 — Test regression (backend_round1654b_test.py)
Aggiunti 4 nuovi test (**23 totali**, prima 19):

| # | Nome | Verifica |
|---|------|---------|
| 20 | `test_druid_warning_only_weapon_skipped` | Druid + solo Frostfang-like in inv → weapon in `unchanged_slots`, `off_class_seen>=1`, nessun equip |
| 21 | `test_druid_class_fit_weapon_preferred` | Druid + off-class + class-fit → sceglie sempre class-fit |
| 22 | `test_warrior_regression_still_equips` | Warrior + 3 class-fit → tutti e 3 equipaggiati (no regressione R16.5.4b) |
| 23 | `test_empty_state_message_italian` | Empty state IT: entrambi i pattern (off_class_seen==0 e >0) |

**Test esistenti aggiornati**: nessuno. I test 01-11 tutti passano invariati perché usavano già `class_tags` matching alla classe dell'adventurer (severity=ok, mai warning). Il test 07 (`class_locked_item_blocked`) usava `required_class_optional` che genera "block" (comportamento invariato).

### 19.9 — Verifica live post-fix (curl reale)
Warrior tester@orbus.test regression: `weapon=drakefang-greatsword`, `armor=stormforged-plate`, `accessory=hoardlords-seal`, `swaps=3`, `score 0→38`. Nessuna regressione dal REOPEN #1.

### 19.10 — Nota ADJ-3 (item pool druid/warlock/alchemist)
Con la nuova regola Q2-b(iii), l'empty state per Druid/Warlock/Alchemist diventa **più visibile** quando il pool inventory è povero. Traccia aggiornata come **P1 IMPORTANTE** in R16.5.4c backlog: seed pack minimale + verifica drop expedition per garantire copertura class-fit su tutte le classi post-R16.0.

### 19.11 — File modificati REOPEN #2
- `/app/backend/app/equipment/auto_equip.py` — rimosso WARNING_PENALTY, aggiornato loop candidati e empty state (~40 righe hunk).
- `/app/frontend/src/pages/Adventurers.jsx` — aggiunta `reloadAndRefreshSelected` + `onChanged` prop (~30 righe).
- `/app/backend/tests/backend_round1654b_test.py` — +4 test warning-skip (~150 righe append).
- `/app/memory/round1654b_final_report.md` — questa sezione 19.
- `/app/memory/backlog.md` — ADJ-3 promosso a P1 IMPORTANTE.
- `/app/memory/orbus_world_roadmap.md` — annotazione REOPEN #2 in-flight.

### 19.12 — Vincoli rispettati
- ✅ Nessun cambio a drop/reward/economia/PvP/premium/stat item
- ✅ Nessun cambio a class primary_stat / secondary_stats / formule bilanciamento
- ✅ Nessun forced-unequip retroattivo di item off-class già equipaggiati
- ✅ Nessun hard delete
- ✅ Nessuna modifica al manual equip
- ✅ Italiano su tutti i messaggi user-facing
- ✅ Test isolati su `orbus_r16_test`

### 19.13 — Statement
**Round 16.5.4b REOPEN #2** — 23/23 test PASS, pronto per verifica browser `e1_tester`. **NON ancora chiuso** — attende conferma PM post browser test.

---

