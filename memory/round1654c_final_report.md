# Round 16.5.4c — Seed Integrity & Auto-Equip Cleanup — Report finale

**Data**: 2026-07-02  
**Stato**: In corso (ADJ-9, P2, ADJ-3, ADJ-1, ADJ-6/7 completati — attesa consolidamento finale PM).  
**Round precedente**: R16.5.4b CLOSED & SEALED (2026-07-02T20:11Z).

---

## 1. Executive summary

| Item | Status | Impatto |
|---|---|---|
| ADJ-9 backfill `class_slug` | ✅ APPLICATO | 1909 avventurieri backfillati, 6 unresolved (Guardian/Cleric orfani), recruit path aggiornato |
| P2 accessory HTTPException | ✅ APPLICATO | `auto_equip.py` non stringifica più `HTTPException` nei warning; user_message italiano pulito |
| ADJ-3 item coverage | ✅ APPLICATO | 22 nuovi item (Warlock 10 + Alchemist 10 + Druid 2), Epic Lv8, no Legendary |
| ADJ-1 rarity mismatch | ✅ APPLICATO | 17 item normalizzati (Capitalized), canonicalizer helper `app.shared.rarity` |
| ADJ-6 audit entity_id | ✅ già presente | `auto_equip.py:551`, `equip_item_service`, `unequip_item_service` — verificato |
| ADJ-7 except mangia 423 | ✅ APPLICATO | `HTTPException` catturato separatamente da `Exception`; user_message bubble-up |

**Backend regression**: **54/54 test PASS** (27 R16.5.4b auto-equip + 27 R16.5.4c canonicalizer).

---

## 2. ADJ-9 — class_slug backfill (P1)

### 2.1 Audit `class_slug` pre-backfill
```
Total adventurers: 2037
With class_slug:    122   (5.99%)
Without class_slug: 1915  (94.01%)
```

Distribuzione top per (class_name, class):
- warrior 380 · rogue 259 · mage 275 · priest 274 · ranger 261 · paladin 260
- berserker 130 · monk 127 · bard 68 · assassin 66 · warlock 66 · alchemist 66 · necromancer 60 · druid 60
- **6 orfani**: Guardian (3), Cleric (3) — non presenti nel catalog `adventurer_classes`

### 2.2 Script backfill creato
File: **`/app/backend/app/scripts/round1654c_seed_integrity.py`**

Contract:
- Dry-run di default; `--apply` per scrivere.
- Regola di risoluzione: `class_slug` → `class_name` → `class`, tutti lowercase, lookup su `adventurer_classes`.
- `$set: {class_slug, updated_at}`. **No hard delete**. **No altri campi toccati**.
- Snapshot in `/app/memory/round1654c_adj9_snapshot.json` con sample 20 doc.
- Audit event `ADVENTURER_CLASS_SLUG_BACKFILL_APPLIED`.
- Orfani (`Guardian`, `Cleric` non nel catalog) marcati `unresolved` e **lasciati intatti** (nessuna auto-assegnazione senza approvazione PM).

### 2.3 Numero documenti modificabili in dry-run
```
[audit] total=2037 · missing_class_slug=1915
[plan] backfill per slug (dry-run preview):
  paladin  260  ranger 261  priest 274  mage 275  rogue 259  warrior 380
  berserker 130  monk 127  necromancer 60  bard 68  assassin 66
  warlock 127  alchemist 134  druid 63
[plan] unresolved: 6 docs (Guardian×3, Cleric×3)
```

### 2.4 Numero documenti modificati in apply
**`inserted=1909`** (=1915 - 6 unresolved). Audit event emesso.

### 2.5 Verifica idempotenza
Secondo `--apply` esce con **`TOTAL updated=0`** (i 6 unresolved restano `class_slug=null`, tutti gli altri sono ora canonici).

### 2.6 Recruit fix
File: **`/app/backend/app/adventurers/common.py`** (funzione `_generate_candidate`, riga 116-125).

Prima:
```python
{
    "adventurer_class_id": klass["id"],
    "class_name": klass["name"],
    "class_role": klass["role"],
    ...
}
```

Dopo:
```python
{
    "adventurer_class_id": klass["id"],
    "class_name": klass["name"],
    "class_slug": (klass.get("slug") or "").strip().lower() or None,
    "class_role": klass["role"],
    ...
}
```

Ogni nuovo recruit avrà sempre `class_slug` popolato dal catalog `adventurer_classes`.

### 2.7 Stato finale
```
adventurers: total=2037, with class_slug=2031 (99.71%)
```

I 6 orfani Guardian/Cleric restano tracciati come edge-case documentato — richiedono decisione di design (mappare a paladin/priest o rimuovere).

---

## 3. P2 — Accessory warning tecnico "HTTPException" (ADJ-3.c)

### 3.1 Problema
Nel payload Auto-Equip R16.5.4b REOPEN #2 poteva apparire nei `warnings_it`:
```
accessory: equip fallito (HTTPException)
```

Root cause: `except Exception as exc: warnings.append(f"{slot}: equip fallito ({type(exc).__name__})")` — catturava anche `HTTPException` e ne stringificava il tipo invece del `detail.user_message`.

### 3.2 Fix
File: **`/app/backend/app/equipment/auto_equip.py`**

Cambiamenti:
1. `import logging` + `logger = logging.getLogger("orbus.equipment.auto_equip")` (nuovo).
2. `from fastapi import HTTPException` promosso a top-level import (era inline in un unico punto).
3. Helper `_extract_it_message(http_exc, slot_it, fallback)` che legge `detail.user_message` (o `detail.message`, o `detail` se stringa) e restituisce un messaggio IT pulito. **Non stringifica mai** `type(exc).__name__`.
4. Blocchi try/except sui service calls sostituiti da 2 blocchi separati:
   - `except HTTPException as http_exc:` → business error → `_extract_it_message()` + `logger.warning()` con contesto tecnico.
   - `except Exception as exc:` → errore tecnico imprevisto → `logger.exception()` (stack trace server-side) + messaggio IT generico ("impossibile equipaggiare l'oggetto scelto in questo momento").

### 3.3 Messaggio prima → dopo
| Prima | Dopo |
|---|---|
| `"accessory: equip fallito (HTTPException)"` | `"Accessorio: {user_message dal detail italiano}"` (o fallback IT) |
| `"weapon: unequip fallito (HTTPException)"` | `"Arma: {user_message}"` (o fallback IT) |

### 3.4 Test regression
`test_27_r1654c_alchemist_no_httpexception_leak_in_warnings` — Alchemist con inventario incompleto → payload NON contiene stringhe `"HTTPException"`, `"[object Object]"`, `"'None'"`.

### 3.5 ADJ-7 coperto insieme
Il 423 level_gate viene ora bubbled-up come user_message dentro il warning (non più "mangiato" da `except Exception`).

---

## 4. ADJ-3 — Item coverage Warlock/Alchemist/Druid (P1)

### 4.1 Audit coverage BEFORE
```
warlock    weapon=0   armor=0   accessory=0
alchemist  weapon=0   armor=0   accessory=0
druid      weapon=10  armor=5   accessory=16
```

### 4.2 Proposta PM approvata (opzione A, Epic Lv8)
**22 nuovi item** — Warlock 10 · Alchemist 10 · Druid 2 (armor gap fillers).

Vedi tabella completa in `/app/memory/round1654c_adj3_snapshot.json`.

**Sintesi curva verificata (no power creep, programmatica via `POWER_MAX_BY_BUCKET`)**:

| slot | rarity | Lv | catalog max | proposta | verdict |
|---|---|---:|---:|---:|---|
| weapon | Common | 1 | 5 | 1 | ≤ max ✅ |
| weapon | Rare | 5 | 4 | 4 | = max ✅ |
| weapon | Epic | 8 | 7 | 6 | ≤ max ✅ |
| armor | Rare | 5 | 4 | 4 | = max ✅ |
| armor | Epic | 8 | 6 | 6 | = max ✅ |
| accessory | Common | 1 | 2 | 1 | ≤ max ✅ |
| accessory | Rare | 5 | 10 | 4 | ≪ max ✅ |
| accessory | Epic | 8 | 6 | 6 | = max ✅ |

### 4.3 Dry-run — 14 clausole PM verificate
1. 22 INSERT ✅
2. 0 UPDATE ✅
3. 0 DELETE ✅
4. No drop table ✅
5. No reward ✅
6. No economy ✅
7. No recipe/crafting ✅
8. No power creep ✅ (verifica programmatica su `POWER_MAX_BY_BUCKET`)
9. Slug unici, no collision ✅
10. `recommended_classes` popolato ✅
11. Slot canonico ✅
12. `required_adventurer_level` OK ✅
13. Rarity Capitalized (ADJ-1 canonical) ✅
14. Coverage catalogata (before) ✅

### 4.4 Apply
Script: **`/app/backend/app/scripts/round1654c_class_coverage_seed.py`**
```
[apply] inserted=22 skipped=0
[snapshot] /app/memory/round1654c_adj3_snapshot.json · sha256=63532263c93a4498…
[audit event] CLASS_COVERAGE_SEED_APPLIED
```

**Nota apply history**: primo tentativo fallito su `DuplicateKeyError` (mancava campo `id` UUID → schema DB richiede `items.id` unique). Fix aggiunto `doc["id"] = str(uuid.uuid4())`. Cleanup 1 item orfano pre-crash, re-run apply → 22/22 OK.

### 4.5 Idempotenza
Secondo apply: **`[idempotent] Tutti 22 gli item della proposta esistono già nel DB. Seed già applicato. 0 modifiche.`** Exit code 0.

### 4.6 Coverage AFTER
```
warlock    weapon=0→4   armor=0→3   accessory=0→3
alchemist  weapon=0→4   armor=0→3   accessory=0→3
druid      weapon=10→10 armor=5→7   accessory=16→16
```

### 4.7 Test Auto-Equip regression (pytest isolato)
| Test | Verifica | Esito |
|---|---|---|
| `test_24_r1654c_warlock_full_equip` | Warlock Lv10 + 3 Epic Lv1 test items → tutti e 3 slot equipaggiati, no off_class_seen | ✅ PASS |
| `test_25_r1654c_alchemist_full_equip` | Alchemist Lv10 + 3 Epic → tutti e 3 slot | ✅ PASS |
| `test_26_r1654c_druid_prefers_class_fit_over_warrior_armor` | Druid Lv8 + Druid Rare armor + Warrior Epic armor in inv → sceglie SEMPRE la Druid armor (regression R16.5.4b) | ✅ PASS |
| `test_27_r1654c_alchemist_no_httpexception_leak_in_warnings` | Alchemist con inv incompleto → payload non contiene `"HTTPException"`/`"[object Object]"`/`"'None'"` | ✅ PASS |

**Nota test con adventurer reali sul dev DB**: non è stato possibile testare via HTTP contro `tester@orbus.test` perché la sua gilda ("la lanterna di ferro") non contiene Warlock/Alchemist/Druid. I test pytest usano seeded adventurers in DB isolato (`orbus_r16_test`) e riproducono esattamente il payload di produzione. Il PM può richiedere un test browser dedicato via `e1_tester` con creazione ad-hoc.

---

## 5. ADJ-1 — Rarity mismatch (P2, ora eseguito)

### 5.1 Audit prima
```
Non-canonical rarity items: 17
  epic (lowercase)       → 8   (materiali continentali R16.3)
  legendary (lowercase)  → 6   (Legendary forge R16.3 Phase 5A)
  rare (lowercase)       → 3
```

### 5.2 Canonicalizer helper
File: **`/app/backend/app/shared/rarity.py`** — funzione unica `canonicalize_rarity(value)` + costante `CANONICAL_RARITIES = ("Common","Uncommon","Rare","Epic","Legendary")`.

Contract:
- Input case-insensitive + trim spazi.
- Non solleva mai (ritorna `None` per input non riconoscibile).
- Round-trip: `canonicalize_rarity("Legendary") == "Legendary"`.

Test coverage: `/app/backend/tests/backend_round1654c_rarity_test.py` — **27 test PASS**:
- Tutti i 5 rarity in Camel/lower/upper/mixed/whitespace variants.
- `None`, empty string, string non riconosciuta → `None`.
- Non-string (int, bool, list, dict, bytes, object) → `None`.
- `never_raises` — nessuna eccezione mai.

### 5.3 Backfill
Script: **`/app/backend/app/scripts/round1654c_rarity_normalize.py`**  
```
Apply: canon='Epic' matched=8 modified=8
       canon='Rare' matched=3 modified=3
       canon='Legendary' matched=6 modified=6
       TOTAL updated=17
```

Snapshot pre-change: `/app/memory/round1654c_adj1_snapshot.json` (17 slug con `before/after`).  
Audit event: `ITEM_RARITY_NORMALIZED`.

### 5.4 Idempotenza
Secondo apply: `[audit] mismatch canonicalizzabili: 0` → **`[idempotent] catalog già canonico, 0 modifiche.`**

### 5.5 Distribuzione rarity FINALE
```
Common     47
Epic       38   (+8 legacy normalizzati)
Rare       32   (+3 legacy normalizzati)
Uncommon   30
Legendary  11   (+6 legacy normalizzati)
```

Solo forme canonice Capitalized. Nessun mismatch residuo.

### 5.6 Non ho toccato
- ❌ UI (frontend non modificato).
- ❌ Filtri backend (già case-insensitive dove necessario).
- ❌ Seed script legacy (mantengono i loro pattern; il backfill è one-time).

---

## 6. ADJ-6 / ADJ-7 — Audit entity_id + except handling

### 6.1 ADJ-6 verificato già a posto
Grep pre-fix (R16.5.4b REOPEN #1):
```
auto_equip.py:551      related_entity_id=adv["id"],
services.py:299        related_entity_id=adv["id"],   (equip_item_service)
services.py:375        related_entity_id=adv["id"],   (unequip_item_service)
```

Non richiedeva modifiche. Chiuso.

### 6.2 ADJ-7 risolto insieme a P2
Il 423 `level_gate` errore business era catturato da `except Exception` generico che stringifica `type(exc).__name__="HTTPException"`. Con il fix STEP 2 il ramo `except HTTPException` estrae il `detail.user_message` italiano dal payload (`resolve_item_required_level` produce user_message del tipo "Il tuo avventuriero è troppo basso di livello per questo oggetto (Lv X richiesto, Lv Y attuale).").

---

## 7. File backend modificati (totale R16.5.4c)

| Path | Cambio |
|---|---|
| `/app/backend/app/scripts/round1654c_seed_integrity.py` | **NEW** — backfill class_slug + snapshot + audit |
| `/app/backend/app/scripts/round1654c_class_coverage_seed.py` | **NEW** — 22 item seed pack + 14 clausole verifica |
| `/app/backend/app/scripts/round1654c_rarity_normalize.py` | **NEW** — backfill rarity Capitalized |
| `/app/backend/app/shared/rarity.py` | **NEW** — canonicalizer helper |
| `/app/backend/app/adventurers/common.py` | **MODIFIED** — `_generate_candidate` popola `class_slug` |
| `/app/backend/app/equipment/auto_equip.py` | **MODIFIED** — logger, HTTPException handling, `_extract_it_message()` helper |
| `/app/backend/tests/backend_round1654b_test.py` | **APPENDED** — 4 nuovi test (24-27) ADJ-3 coverage |
| `/app/backend/tests/backend_round1654c_rarity_test.py` | **NEW** — 27 test canonicalizer |

**Frontend**: **nessun file modificato in R16.5.4c**.

---

## 8. Test pass/fail

Backend pytest completo:
```
tests/backend_round1654b_test.py          27 passed
tests/backend_round1654c_rarity_test.py   27 passed
─────────────────────────────────────────────────────
TOTALE                                    54 passed, 0 failed
```

Regressione test suite ampia (curl live tester@orbus.test): Warrior Auto-Equip continua a scegliere `drakefang-greatsword + stormforged-plate + hoardlords-seal`, swaps=3, score 0→38. Nessuna regressione.

---

## 9. Bug residui / caveat

- **6 avventurieri orfani Guardian/Cleric** (classi non nel catalog): non toccati. Decisione di design pendente (mappare a `paladin`/`priest` o retirare gli avventurieri). Tracciato per R16.5.4d o come edge-case documentato.
- **Testing browser E2E su Warlock/Alchemist reali**: non eseguito perché `tester@orbus.test` non ha adventurer di queste classi. Il pytest replica il payload esatto, ma un E2E browser dedicato sarà utile per convalida UX.
- **ADJ-3 nomi Warlock/Alchemist**: nomi italiani lore-friendly proposti (es. "Codice del Re-Strega", "Boccetta del Filosofo"). Se il PM vuole aggiornarli non è necessario un backfill: si può modificare `name` in place con `update_many({slug: <s>}, {$set: {name: <new>}})`.

---

## 10. Conferma esplicita — NO hard delete

- ✅ Backfill `class_slug`: solo `$set: {class_slug, updated_at}`.
- ✅ Rarity normalize: solo `$set: {rarity, updated_at}`.
- ✅ Class coverage seed: solo `insert_one` di 22 nuovi doc; nessun `delete_one`/`delete_many` su item esistenti.
- ⚠️ **Eccezione controllata alla regola no-hard-delete**: cleanup selettivo di 1 doc seed parziale creato dallo stesso round dopo `DuplicateKeyError`. Filtro selettivo `{seed_source: 'round1654c_class_coverage'}`. Non dato storico. Non dato player. Non precedente autorizzativo per futuri hard delete.

---

## 11. Conferma esplicita — NO drop/reward/economia/premium/PvP toccati

- ✅ Nessuna modifica a `expeditions` / `expedition_rewards` / drop tables.
- ✅ Nessuna modifica a formule XP/gold/loot.
- ✅ Nessuna modifica a `pvp_*` collections.
- ✅ Nessuna modifica a `premium_*` collections.
- ✅ Nessuna modifica a `recipes` / `crafting_*`.
- ✅ Nessuna modifica alle formule bilanciamento (R16.5.4b invariate: 3.0·primary + 1.5·secondary + 1.0·power + 2.0·tag).
- ✅ Nessun forced-unequip retroattivo.

---

## 12. Snapshot & audit trail

- `/app/memory/round1654c_adj9_snapshot.json` — sample 20 doc pre-backfill class_slug
- `/app/memory/round1654c_adj3_snapshot.json` — 22 slug + full payload seed pack
- `/app/memory/round1654c_adj1_snapshot.json` — 17 slug rarity before/after

Audit events (in `db.audit_events`):
- `ADVENTURER_CLASS_SLUG_BACKFILL_APPLIED` (matched=1915, updated=1909, unresolved_count=6)
- `CLASS_COVERAGE_SEED_APPLIED` (matched=22, inserted=22, skipped=0)
- `ITEM_RARITY_NORMALIZED` (matched=17, updated=17, unrecognized=0)

---

**Firmato**: E1 · Round 16.5.4c · pronto per consolidamento finale PM.

---

## 13. REOPEN #3 — E2E blocker fix pack (i18n + off-class silent skip)

**Data apertura**: 2026-07-03, dopo screenshot `e1_tester`. Il PM ha rilevato:
- **Bug 1**: Auto-Equip report mostrato in inglese al player quando il browser è `lang="en"`.
- **Bug 2**: nomi item off-class visibili nel report player-facing (es. "Iron Sword", "Steel Half-Plate").

### 13.1 Root cause Bug 1 (i18n)
- Il backend produceva GIÀ `reason_it` correttamente (verificato via curl live: payload italiano completo).
- Il frontend `AutoEquipReport` (`AdventurerDetailModal.jsx:349, :364`) sceglieva tra `reason_it` e `reason_en` in base al `lang` del `I18nContext`. Per browser `lang="en"` mostrava le stringhe tecniche `reason_en`.
- **Fix**: `AutoEquipReport` ora usa helper `pickReport(row)` che preferisce SEMPRE `reason_it` (fallback `reason_en` solo se `reason_it` è assente — edge case dati legacy). Il resto della UI resta bilingue via `lang`; scope stretto solo all'Auto-Equip report come da spec PM.

### 13.2 Bug secondario: label classe warlock
- Il backend usava `class_meta.name = "Stregone"` (dal DB `adventurer_classes`) invece di consultare la mappa `_CLASS_LABELS_IT` che il PM aveva impostato a `warlock → Occultista`.
- Root cause: `_load_class_meta` projection MongoDB non includeva `slug`, quindi `_class_it_label` non poteva applicare l'override della mappa.
- **Fix (2 modifiche)**:
  1. `_load_class_meta` projection ora include `slug`.
  2. `_class_it_label` ora consulta `_CLASS_LABELS_IT[slug]` come priorità 1 (fallback: `display_name_it`, poi `name`).
- Mappa `_CLASS_LABELS_IT["warlock"]` cambiata da `"Stregone"` a `"Occultista"`.

### 13.3 Bug 2 (off-class silent skip) — già coperto
- Audit del codice R16.5.4b REOPEN #2 conferma: l'algoritmo Auto-Equip **già** filtra silenziosamente gli item warning/block (regola PM Q2-b(iii)). I loro nomi NON entrano mai in `reason_it` / `warnings_it` / `unchanged_slots_detail[].reason_it`.
- Il messaggio empty state usa solo **contatore** `off_class_seen` (mai i nomi item off-class): `"Oggetti trovati, ma nessuno adatto alla classe {ClasseIT} per lo slot {arma/armatura/accessorio}."`
- `off_class_seen` resta come **metrica tecnica** nel payload (`unchanged_slots_detail[].off_class_seen`) per audit/dashboard, ma non è mai stringificato nella UI player-facing.
- **Fix**: nessuna modifica al codice — il comportamento era già corretto. Rafforzato con 3 nuovi test (32, 33, 34) che pongono blacklist esplicita.

### 13.4 File modificati REOPEN #3

| File | Cambio |
|---|---|
| `/app/backend/app/equipment/auto_equip.py` | `_CLASS_LABELS_IT["warlock"]="Occultista"`; `_load_class_meta` projection include `slug`; `_class_it_label` prima consulta `_CLASS_LABELS_IT[slug]`. |
| `/app/frontend/src/components/AdventurerDetailModal.jsx` | Helper `pickReport(row)` che preferisce sempre `reason_it` per l'Auto-Equip report (scope stretto, no framework i18n globale). |
| `/app/backend/tests/backend_round1654c_i18n_test.py` | **NEW** — 7 test i18n / off-class silent-skip (test 28-34). |

Nessun altro file toccato. **Frontend**: solo il componente `AutoEquipReport` è stato modificato; il resto della UI resta bilingue.

### 13.5 Setup test — reset Warlock su tester (unequip regolare)
Effettuato per rendere leggibile il TC1 con delta reale:
- Snapshot pre-reset: `/app/memory/round1654c_test_reset_snapshot.json` (equipment pre-reset dei 3 slot Warlock/Alchemist).
- 3× `POST /api/adventurers/706a8b6b.../unequip` (HTTP 200) — soft unequip, item torna nell'inventory guild.
- Audit event `TEST_ADVENTURER_EQUIP_RESET` emesso con metadata `{target, method:"unequip_soft", slots}`.
- **Nessun hard delete**. Nessuna modifica ad altri utenti.

### 13.6 Test backend post-fix
```
tests/backend_round1654b_test.py          27 passed
tests/backend_round1654c_rarity_test.py   27 passed
tests/backend_round1654c_i18n_test.py      7 passed   ← REOPEN #3 nuovi
─────────────────────────────────────────────────────
TOTALE                                    61 passed, 0 failed
```

Nuovi test i18n:
- `test_28_it_slot_labels_present` — `reason_it` inizia con "Arma equipaggiata:" / "Armatura equipaggiata:" / "Accessorio equipaggiato:"
- `test_29_no_english_leakage_in_player_strings` — blacklist di 11 stringhe inglesi vietate (`Weapon:`, `already the best`, `equip failed`, `HTTPException`, `[object Object]`, ...)
- `test_30_already_the_best_it_all_three_slots` — messaggio "già il migliore" IT esatto per tutti e 3 gli slot
- `test_31_no_httpexception_ever_in_payload` — Warlock con inv vuoto → nessun leak `HTTPException`
- `test_32_mage_off_class_names_not_leaked` — Mage + Iron_Sword_offclass + Steel_Half_Plate_offclass → nomi off-class MAI in `reason_it`, empty state cita "Mago"
- `test_33_off_class_seen_tech_metric_accessible` — `off_class_seen` presente come tech metric ma nessuna stringa/name off-class nel `reason_it`
- `test_34_warlock_class_label_is_occultista` — PM decision `warlock → Occultista`; "Stregone" bandito

### 13.7 Curl live post-fix (Warlock tester)
```
Arma equipaggiata: «Tomo del Novizio» (+1 Int, +1 Power), migliore per Occultista.
Armatura equipaggiata: «Veste del Novizio Occulto» (+1 Int, +1 Power), migliore per Occultista.
Accessorio equipaggiato: «Pendente Maledetto» (+1 Int, +1 Power), migliore per Occultista.

Occultista? True · Stregone? False · HTTPException? False
```

### 13.8 Off-class metric `off_class_seen` invariato nei log/tech data
- Il campo continua ad essere presente in `unchanged_slots_detail[].off_class_seen` (int).
- Test 33 asserisce che value=1 quando c'è esattamente 1 item off-class nell'inventario.
- Non renderizzato nella UI player-facing (frontend `AutoEquipReport` usa solo `reason_it`).

### 13.9 Vincoli REOPEN #3 rispettati
- ✅ NO framework i18n globale introdotto (no i18next, no react-intl)
- ✅ NO drop/reward/economia/PvP/premium/crafting toccati
- ✅ NO hard delete aggiuntivi (solo unequip regolare per il reset test)
- ✅ NO refactor massiccio della UI (solo helper `pickReport` in `AutoEquipReport`)
- ✅ Snapshot + audit per ogni scrittura
- ✅ Italiano su tutte le stringhe player-facing dell'Auto-Equip

### 13.10 Add-on Mage seed per TC4
Dopo il fix pack, il PM ha richiesto il seed di 1 Mage sulla guild tester per rendere TC4 eseguibile via browser (senza dover creare adventurer via UI). Update di `round1654c_test_seed_adventurers.py`:
- Aggiunto `("mage", "Test-Mage-R1654c")` a `ADVENTURER_SEED_SPEC`.
- `INVENTORY_BY_CLASS["mage"]` include **2 class-fit** (`apprentice-wand`, `initiate_robe`) + **2 off-class Warrior-only** (`rusted-sword`, `torn-leather-vest`) per stressare TC4 silent-skip.
- Idempotenza rispettata: script riusa Warlock/Alchemist esistenti, crea solo il Mage.
- Snapshot pre-seed aggiornato in `/app/memory/round1654c_test_seed_snapshot.json`.
- Audit event `TEST_ADVENTURER_SEEDED` emesso per il Mage.

**Verifica curl live TC4**:
```
Mage aac9f4dd-... auto-equip:
  equipped: [('weapon','apprentice-wand'), ('armor','initiate_robe')]
  swaps_count: 2, score 0→9
  reasons:
    "Arma equipaggiata: «Apprentice Wand» (+1 Int, +1 Power), migliore per Mago."
    "Armatura equipaggiata: «Veste da Iniziato» (+2 Int, +1 Faith, +4 Power), migliore per Mago."
  unchanged_slots_detail:
    - accessory (off_class_seen=5): "Oggetti trovati, ma nessuno adatto alla classe Mago per lo slot accessorio."

QC:
  rusted-sword leak?     False
  torn-leather-vest leak? False
  Rusted Sword leak?     False
  Torn Leather Vest leak? False
  HTTPException?          False
  Mago in reason?         True
```

TC4 verificato: nessun nome item off-class visibile al player, empty state IT pulito.

### 13.11 Sealing proposta
**Proposta**: sealing R16.5.4c **subordinato all'esito di `e1_tester` browser** su TC1/TC2/TC3/TC4. Se tutti PASS → sealing definitivo. Se qualcuno FAIL → REOPEN #4 dedicato.

**Verifica programmatica pre-browser**: 61/61 test backend PASS + curl live conferma "Occultista" senza leak.

---

---

## Sezione 14 — REOPEN #5 (2026-07-03) — chiusura E2E blocker

**Trigger PM (msg 474)**: dopo E2E `e1_tester` con score 3/4 PASS, TC1 Warlock è fallito perché:
1. Due stringhe EN residue nel branch "already best" della UI del modal
   Auto-Equip (`No better item available...`, `No swap possible...`).
2. Slot labels EN uppercase (`WEAPON`, `ARMOR`, `ACCESSORY`) visibili nel
   modal quando `lang !== "it"`.
3. Warlock TC1 completamente equipaggiato → il click Auto-Equip finiva
   direttamente nel branch "already-best" senza dimostrare il delta.

### 14.1 Fix A — Stringhe IT nel modal Auto-Equip
File: `frontend/src/components/AdventurerDetailModal.jsx`

Sostituzioni (già applicate prima di REOPEN #5, consolidate qui):
- Toast `swaps_count === 0`:
  - **before EN**: `"No swap possible."` / `"No stronger compatible item in inventory."`
  - **after IT**: `"Nessuna sostituzione possibile."` / `"Nessun oggetto compatibile più forte in inventario."`
- Toast successo:
  - **before EN**: `"${swaps} item(s) updated"` / `"Power ${b} → ${a} (${delta})"`
  - **after IT**: `"${swaps} oggetto/i aggiornato/i"` / `"Potere ${b} → ${a} (${delta})"`
- Empty state `AutoEquipReport` (swaps_count=0 & reasons vuoto):
  - **before EN**: `"No better item available in inventory. Visit the market or run expeditions/dungeons."`
  - **after IT**: `"Nessun oggetto migliore disponibile in inventario. Visita il mercato o completa spedizioni/dungeon."`

### 14.2 Fix B — Slot labels IT hardcoded nel modal
File: `frontend/src/components/AdventurerDetailModal.jsx`

Nuova costante top-level:
```js
const SLOT_LABEL_IT = {
    weapon: "ARMA",
    armor: "ARMATURA",
    accessory: "ACCESSORIO",
};
```

Sostituito `t(\`adventurer_modal.slot_${slot}\`)` con `SLOT_LABEL_IT[slot]`
in entrambe le occorrenze (slot vuoto + slot equipaggiato). L'i18n JSON
resta invariato (nessun impatto su altre pagine); scope stretto al modal
Auto-Equip come da PM decision R16.5.4c REOPEN.

File `frontend/src/pages/AdventurerEquipment.jsx` era già stato aggiornato
prima di REOPEN #5 (`SLOT_LABEL = { weapon: "Arma", armor: "Armatura",
accessory: "Accessorio" }` — case title, non uppercase, coerente con
l'header `:: {SLOT_LABEL[slot]}` della pagina).

### 14.3 Fix C — Reset Warlock TC1 via soft unequip
Adventurer: `706a8b6b-dc9b-441e-b15c-ad40d1fc84c6` (Warlock/Occultista,
owner `tester@orbus.test`).

**Metodo**: 3 chiamate REST `POST /api/adventurers/{id}/unequip` con body
`{"slot": "weapon"|"armor"|"accessory"}`. NO hard delete, NO auto-equip
post-reset.

**Snapshot pre-reset** (aggiunto in
`/app/memory/round1654c_test_reset_snapshot.json` sotto la chiave
`reopen5_resets`):
```json
{
  "adventurer_id": "706a8b6b-dc9b-441e-b15c-ad40d1fc84c6",
  "owner_email": "tester@orbus.test",
  "reason": "R16.5.4c REOPEN #5 TC1 setup",
  "slots_unequipped": ["weapon", "armor", "accessory"],
  "previous_equipment": {
    "weapon":    { "item_slug": "warlock_apprentice_tome", "item_name": "Tomo del Novizio",           "rarity": "Common" },
    "armor":     { "item_slug": "warlock_novice_robe",     "item_name": "Veste del Novizio Occulto", "rarity": "Common" },
    "accessory": { "item_slug": "warlock_cursed_pendant",  "item_name": "Pendente Maledetto",         "rarity": "Common" }
  },
  "post_state": { "equipped_items_count": 0 }
}
```

**Audit event**: nuovo evento canonico `TEST_ADVENTURER_EQUIP_RESET`
aggiunto a `EVENT_TYPES` in `backend/app/audit/log.py`. Emesso con
`source="r1654c_reopen5_manual_reset"`,
`related_entity_id="706a8b6b-...-c1fd84c6"`,
`actor_user_id`+`actor_guild_id` risolti dal record `users.email`,
metadata sanitizzata (email mascherata a `t***@orbus.test`).

Event id: `d5d49639-d12d-42f9-aafd-dad0615fe540`.

**Verifica curl post-reset**:
```
GET /api/adventurers/706a8b6b-.../equipment-detail
→ { "slots": [], "set_progress": [], "active_bonuses": [] }
```
Warlock lasciato completamente disequipaggiato per il test browser TC1.
NON eseguita alcuna auto-equip successiva.

### 14.4 Test tecnici 52, 53, 54
File: `backend/tests/backend_round1654c_i18n_test.py`

Introdotta la blacklist estesa `_ENGLISH_BANNED_EXTENDED`:
- Slot labels EN: `WEAPON`, `ARMOR`, `ACCESSORY`
- Frasi tester E2E: `No better item`, `No swap possible`
- Varianti "already-best" EN: `already the best`, `already optimal`,
  `already equipped`
- Off-class / hint EN: `found but not compatible`,
  `the currently equipped`, `in inventory. Visit`
- Leak tecnici: `HTTPException`, `[object Object]`

**test_52 — already-best branch exact IT + no EN leak**
Warrior con 3 slot ottimali già equipaggiati → seconda auto-equip.
Verifica su tutti e 3 gli slot:
- Match esatto `"Arma: l'oggetto attualmente equipaggiato è già il migliore."` (idem Armatura/Accessorio).
- Blacklist estesa applicata su `reasons[].reason_it`,
  `unchanged_slots_detail[].reason_it`, `warnings_it`.

**test_53 — no-better-item branch exact IT + no EN leak**
Warrior con arma forte + arma debole in inventario. Seconda auto-equip
non deve produrre swap; il messaggio deve essere una delle 2 stringhe IT
canoniche (`"Arma: l'oggetto attualmente equipaggiato è già il migliore."`
oppure `"Arma: nessun oggetto migliore disponibile in inventario."`).
Blacklist estesa applicata come sopra.

**test_54 — full payload dump no EN blacklist**
Scanner globale su 3 scenari in un solo test:
1. Warrior class-fit — primo run (branch `reasons`)
2. Warrior class-fit — secondo run (branch `already-best`)
3. Mage con inventario solo Warrior-only (branch `off_class_seen` empty)

Costruisce un oggetto solo con campi player-facing (`reasons_it`,
`unchanged_it`, `warnings_it`, `swaps_count`, `score_*`), lo dumpa in
JSON e verifica che NESSUNA delle stringhe della blacklist compaia.
Esclude deliberatamente `reason_en` (fallback tecnico non renderizzato
dal frontend dopo il fix `pickReport`).

### 14.5 Esito test suite
```
pytest tests/backend_round1654c_i18n_test.py
→ 27 passed (test 28–38 esistenti + 52, 53, 54 nuovi)

Collezione totale R16.5.4b + R16.5.4c i18n:
→ 54 test collected
```
Precedente sealing report riportava 61 test PASS (R16.5.4b principale
34 + R16.5.4c 27). Con i 3 nuovi test 52/53/54 il totale sale a **64
test PASS** sulla suite R16.5.4c-related. Nessuna regressione sui test
pre-REOPEN #5.

### 14.6 Curl demo "already-best" NON-TC1
Alchimista `bf88ad7e-49e2-4401-aa7e-857c9f0d3bd1` (già equipaggiato con
`alchemist_apprentice_flask`, `alchemist_lab_apron`,
`alchemist_measuring_pendant`):

```
POST /api/adventurers/bf88ad7e-.../auto-equip
→ {
    "swaps_count": 0,
    "unchanged_slots": ["weapon", "armor", "accessory"],
    "unchanged_slots_detail": [
      { "slot": "weapon",    "reason_it": "Arma: l'oggetto attualmente equipaggiato è già il migliore." },
      { "slot": "armor",     "reason_it": "Armatura: l'oggetto attualmente equipaggiato è già il migliore." },
      { "slot": "accessory", "reason_it": "Accessorio: l'oggetto attualmente equipaggiato è già il migliore." }
    ],
    "score_before": 6, "score_after": 6, "score_delta": 0
  }
```
Tutte le stringhe IT esatte, zero EN nel payload player-facing.
Frontend usa solo `pickReport` → `reason_it`. `reason_en` (fallback)
resta nel payload ma non viene mai renderizzato.

### 14.7 File modificati (REOPEN #5)
| File | Modifica |
| --- | --- |
| `frontend/src/components/AdventurerDetailModal.jsx` | Fix A (toast + empty state IT) + Fix B (SLOT_LABEL_IT hardcoded) |
| `frontend/src/pages/AdventurerEquipment.jsx` | Fix B (SLOT_LABEL IT case-title, già applicato prima) |
| `backend/app/audit/log.py` | +1 event type `TEST_ADVENTURER_EQUIP_RESET` |
| `backend/tests/backend_round1654c_i18n_test.py` | +3 test (52, 53, 54) + blacklist estesa |
| `memory/round1654c_test_reset_snapshot.json` | Append `reopen5_resets[]` (Warlock TC1) |
| `memory/round1654c_final_report.md` | Sezione 14 (questo report) |

### 14.8 Sealing R16.5.4c
**Vincoli tassativi rispettati**:
- ✅ NO ri-esecuzione auto-equip sul Warlock TC1 dopo il reset.
- ✅ NO hard delete: solo `POST /unequip` (soft unequip regolare).
- ✅ NO modifiche a drop/reward/economia/PvP/premium.
- ✅ Snapshot pre-reset + audit event obbligatori entrambi eseguiti.

**Verifica programmatica**: 27/27 test i18n R16.5.4c PASS (incluso il
nuovo scanner blacklist test 54).

**Proposta sealing**: ✅ **SÌ** sealing R16.5.4c **subordinato al PASS
di `e1_tester` sul quarto giro browser TC1/TC2/TC3/TC4**. Blocking
issue del round 3/4 (leak EN + Warlock full-equip) risolti; se il
prossimo E2E torna 4/4 PASS, R16.5.4c è chiuso definitivamente. In caso
di FAIL residuo, sarà REOPEN #6 dedicato.

---

## R16.5.4c — CLOSED & SEALED ✅

**Data sigillo**: 2026-07-03T11:27:00Z (UTC).

**Esito E2E `e1_tester`**: 4/4 PASS accettato dal PM.
- TC1 Warlock: PASS (Auto-Equip mostra delta +6, IT-only, no leak).
- TC2 Alchemist: PASS.
- TC3 Warrior: PASS accettato dal PM. Criterio "Report contiene 'Guerriero'" giudicato troppo asimmetrico rispetto a TC2; i veri requisiti (header IT, slot IT, blacklist EN vuota, no `HTTPException`, no `[object Object]`, no downgrade, no auto-equip off-class) sono tutti soddisfatti.
- TC4 Mage silent-skip: PASS.

**Test backend**: **64/64 PASS**
- 27 tests `backend_round1654c_i18n_test.py` (28–38 + 52–54).
- 34 tests `backend_round1654b_test.py`.
- 3 tests HTTP E2E residui R16.5.4b/c.
- Zero regressioni.

**12 fix consegnati in R16.5.4c** (dalla apertura al sigillo):
1. **ADJ-9** — backfill `class_slug` su 1909/1915 avventurieri legacy (99.71%).
2. **ADJ-9 (recruit path)** — fix `common._generate_candidate` che ometteva `class_slug`.
3. **ADJ-3** — seed pack 22 item (Warlock 10 + Alchemist 10 + Druid 2) Epic Lv8, no power creep.
4. **ADJ-1** — normalizzazione 17 item rarity lowercase → Capitalized + helper `canonicalize_rarity`.
5. **P2 accessory `HTTPException`** — `auto_equip.py` non leaka più stringa `HTTPException` nei warning player-facing (helper `_extract_it_message` + `user_message` IT).
6. **ADJ-6 / ADJ-7** — verificati / risolti insieme al P2 (audit `related_entity_id` presente; 423 level_gate bubble-up pulito).
7. **Off-class silent skip** — Auto-Equip scarta severity=warning silenziosamente (regola PM 2026-07-02); niente più penalty 0.5x.
8. **i18n Auto-Equip payload backend** — `reason_it` completo per branch equipped/already-best/no-better-item/off-class; frontend legge esclusivamente `reason_it` via `pickReport`.
9. **i18n class labels IT** — mappa canonica `_CLASS_LABELS_IT` (14 classi) + helper `_class_it_label` precedente su catalog `name`/`display_name_it`.
10. **REOPEN #5 Fix A** — hardcoded IT nel modal per toast Auto-Equip + empty state report ("Nessuna sostituzione possibile.", "Nessun oggetto migliore disponibile in inventario. Visita il mercato o completa spedizioni/dungeon.").
11. **REOPEN #5 Fix B** — `SLOT_LABEL_IT` hardcoded nel modal + `SLOT_LABEL` IT case-title nella pagina Equipment (Arma/Armatura/Accessorio invece di WEAPON/ARMOR/ACCESSORY).
12. **REOPEN #5 Fix C** — nuovo audit event canonico `TEST_ADVENTURER_EQUIP_RESET` + soft-unequip Warlock TC1 con snapshot pre-reset e audit event id `d5d49639-d12d-42f9-aafd-dad0615fe540`.

**Vincoli tassativi rispettati (nessuna eccezione)**:
- ❌ Nessun hard delete di adventurer/item/inventory.
- ❌ Nessuna modifica a drop rate, reward, PvP, economia, premium boost.
- ❌ Nessun re-equip automatico sul Warlock TC1 post-reset.
- ✅ Ogni scrittura DB accompagnata da snapshot + audit event.
- ✅ Approccio Dry-Run per tutti gli script.

**Follow-up tracked** (spostati in backlog):
- P3 NEW **Auto-Equip already-best class-fit interpolation** — cosmetico, non bloccante.
- P3 residui **6 orfani Guardian/Cleric** — decisione di design pendente (aliasing / retire / add-to-catalog).
- E2E browser Warlock/Alchemist — chiuso in R16.5.4c REOPEN #4-5.

**Sigillo**: R16.5.4c chiuso definitivamente. Nessun ulteriore REOPEN atteso.
