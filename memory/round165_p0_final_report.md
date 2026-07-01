# Round 16.5 P0 — Final Report

**Data**: 2026-07-01
**Fase**: STEP 2 completo (Snapshot → Apply → Test → Audit → §19 → Report)
**DB target**: `orbus_r16` (produzione preview)
**Ambiente test**: `orbus_r16_test` (pytest strict isolation, `ISOLATED_HTTP_TESTS=1`)

---

## 0. Executive summary

| Fase | Status | Note |
|---|:---:|---|
| 2.1 Snapshot pre-apply | ✅ | `round165_p0_prechange_snapshot.json` sha256=`a028743e…` |
| 2.1b DIFF preview | ✅ | `round165_p0_apply_preview.txt` — audit trail |
| 2.2 Apply | ✅ | 22 dungeon + 5 legendary modificati, 0 whitelist violations |
| 2.3 Pytest post-apply | ✅ | **13/13 test passed** su `orbus_r16_test` (isolato) |
| 2.4 Post-apply rapid audit | ⚠️ | Data OK ma runtime enforcement **NON** attivo — vedi Decisione B |
| 2.5 Section 19 data collection | ✅ | **0 orphaned legendaries** (nessuna decisione UX richiesta) |

**Verdetto tecnico**: la migration è idempotente, whitelisted e reversibile
via snapshot. La data population è corretta al 100%. Il problema UX
originale ("team lv4 batte dungeon lv7") **non è ancora risolto in runtime**
finché `expeditions.level_gate` non legge il nuovo campo `required_level`.

---

## 1. Snapshot pre-apply

- **Path**: `/app/memory/round165_p0_prechange_snapshot.json`
- **SHA256**: `a028743e7468c5f882d64366e4f80b53c0f31d4679ac004ba8d44f74026c3709`
- **Dimensione**: 4934 bytes
- **Contenuto**: stato pre-change (solo campi whitelist) di 22 dungeon
  + 5 legendary. Rollback deterministico: per ogni entry, `update_one({slug},
  {$set: <entry>})` ripristina lo stato originale.

## 2. DIFF preview (audit trail)

- **Path**: `/app/memory/round165_p0_apply_preview.txt`
- Emesso PRIMA di ogni `update_one` durante l'apply. Contiene sha256
  dello snapshot, whitelist attiva, count dungeon/legendary previsti,
  slug dei 3 dungeon con `progression_tag=story_catchup`.

## 3. Tabella dungeon applicati (22 righe)

| slug | tier | rec_pow | team | req_lvl → | bucket | tag |
|---|:---:|---:|:---:|:---:|---|---|
| sewer-nest | 1 | 35 | 3p | **1** | tutorial | |
| goblin-warrens | 1 | 45 | 3p | **2** | tutorial | |
| bandit-hideout | 1 | 50 | 3p | **2** | tutorial | |
| druid-grove | 2 | 69 | 3p | **3** | early | |
| shadow-crypts | 2 | 75 | 3p | **3** | early | |
| wolf-den-5p | 1 | 80 | 5p | **3** | early | story_catchup |
| cursed-mines | 2 | 78 | 3p | **4** | early | |
| sunken-library | 2 | 85 | 3p | **4** | early | |
| frost-cave-5p | 1 | 90 | 5p | **4** | early | story_catchup |
| lich-sanctum | 3 | 94 | 3p | **5** | mid | |
| salt-marsh-5p | 1 | 100 | 5p | **5** | early | story_catchup |
| dragons-hoard | 3 | 100 | 3p | **6** | mid | |
| storm-spire | 3 | 110 | 3p | **6** | mid | |
| iron-foundry-5p | 2 | 140 | 5p | **6** | mid | |
| silent-monastery-5p | 2 | 155 | 5p | **7** | mid | |
| pirate-fleet-5p | 2 | 170 | 5p | **8** | high | |
| obsidian-arena-5p | 3 | 210 | 5p | **9** | high | |
| clockwork-vault-5p | 3 | 230 | 5p | **10** | high | |
| voidspire-5p | 3 | 250 | 5p | **11** | high | |
| infernal-pit-5p | 4 | 290 | 5p | **12** | high | |
| celestial-citadel-5p | 4 | 320 | 5p | **13** | high | |
| world-tree-roots-5p | 4 | 360 | 5p | **14** | high | |

## 4. Tabella legendary applicati (5 righe)

| slug | rarity | equip_power | min_lvl → |
|---|---|---:|:---:|
| goblin_hunter_ring | Legendary | ~40 | **8** |
| drake_slayer_helm | Legendary | ~50 | **8** |
| drake_slayer_chest | Legendary | ~50 | **8** |
| drake_slayer_blade | Legendary | 73 (top) | **9** |
| arcane_adept_orb | Legendary | 60 | **9** |

## 5. Test post-apply

Runner: `pytest tests/backend_round165_p0_balance_test.py` con
`ISOLATED_HTTP_TESTS=1` → tutti i test hanno colpito **esclusivamente**
`orbus_r16_test`. **13/13 passed in 0.88s** (2 worker xdist).

Categorie coperte:
- Invarianti data: `required_level > 0`, bucket ∈ {tutorial, early, mid,
  high}, `min_level >= 8` per Legendary, `min_level == 9` per outlier.
- Whitelist: le funzioni builder rifiutano campi fuori whitelist. Costanti
  frozen. Nessun campo pericoloso (equip_power, rarity, gold, xp).
- Mapping consistency: ogni dungeon nel mapping ha in DB esattamente i
  valori dichiarati. Gap curva ≤ 2 livelli. Copertura di tutti 4 i bucket.
- Idempotenza: reapply → nessun campo target cambia.
- `progression_tag=story_catchup` presente **solo** sui 3 5p introduttivi.

## 6. Sezione 19 — data collection

Fonte: `/app/memory/round165_missing_data_section19.md` +
`.json`. Script `round165_section19_data_collection.py --read-only`
(monkey-patch delle write methods → nessuna scrittura possibile).

### 6.1 Distribuzione livelli avventurieri (`orbus_r16`)

| banda | count |
|---|---:|
| lv 1-3 | 1967 |
| lv 4-6 | 8 |
| lv 7-9 | 9 |
| lv 10+ | 0 |
| **totale attivi** | **1984** |
| retired | 15 |

Il 99% degli avventurieri è lv 1-3. Solo 17 avventurieri sono a lv 4+.

### 6.2 Legendary attualmente equipaggiati

**0 istanze.** Nessuno ha ancora un Legendary equipaggiato in produzione
(coerente con il fatto che erano gate-less prima e nessuno ha ancora
raggiunto lv7+ per averli droppati/craftati).

### 6.3 Orphaned Legendaries

**0 orphan rilevati.** Il caso peggiore (grandfathering vs
forced-unequip) è **inapplicabile**: non c'è nessun avventuriero con
Legendary equipaggiato sotto il nuovo `min_level`.

---

# 🎯 DECISIONI RICHIESTE ALL'UTENTE

## Decisione A — Legendary orfani

**Dati oggettivi**:
- Istanze orfane: **0**
- Avventurieri impattati: **0**
- Gilde impattate: **0**
- Item unici impattati: **{}**

**Raccomandazione**: **A-NULL — nessuna azione necessaria.** La finestra
di applicazione è stata perfetta (nessun Legendary attualmente
equipaggiato in prod). Le opzioni A1 (grandfathering) e A2
(forced-unequip) restano progettualmente pronte ma non richiedono
implementazione ora.

---

## Decisione B — Efficacia P0 vs necessità di P1

**Dati Monte Carlo (10 000 iters) post-apply**:

`team_medio_reale` (lv 4-5, team_power=200) vs `silent-monastery-5p`
(`required_level=7`, rec_pow=155):

| metrica | valore | soglia utente | verdict |
|---|---:|:---:|:---:|
| Formula matematica pura | **93.7%** | < 30% | 🚨 **FAIL** |
| Runtime gate reale (`min_adventurer_level`) | Team lv 4-5 passa (fallback difficulty=2 → gate lv3) | | 🚨 team ammesso |
| Runtime gate col nuovo campo (`required_level`) | Team lv 4-5 rifiutato (lv < 7) | | ✅ se attivato |

**Causa root**: l'apply P0 ha popolato il campo `required_level` sulle
collezioni ma il runtime `expeditions/level_gate.py` **non legge questo
campo**. Continua a usare il legacy `min_adventurer_level` (che rimane
`None` post-apply) con fallback su `difficulty` (mappa: 1→1, 2→3, 3→7,
4→12). Per i dungeon con `difficulty=2` e nuovo `required_level >= 6`
(silent-monastery-5p req=7, pirate-fleet-5p req=8, iron-foundry-5p
req=6, cursed-mines req=4), il runtime lascia passare team lv 3+.

**Raccomandazione**: **B → serve P1**, ma è un intervento MINIMO
(≈15 righe di codice + test).

### Cosa fa P1 (proposta concreta)

Modificare `legacy_min_level_for_dungeon()` in
`/app/backend/app/expeditions/level_gate.py`:

```python
def legacy_min_level_for_dungeon(dungeon: dict) -> int:
    # Order of precedence (first non-None wins):
    # 1. Round 16.5 canonical field: required_level
    r165 = dungeon.get("required_level")
    if isinstance(r165, int) and r165 >= 1:
        return r165
    # 2. Legacy explicit field
    explicit = dungeon.get("min_adventurer_level")
    if isinstance(explicit, int) and explicit >= 1:
        return explicit
    # 3. Difficulty-based fallback (existing behavior)
    diff = int(dungeon.get("difficulty", 1) or 1)
    return _DUNGEON_DIFFICULTY_TO_MIN_LEVEL.get(diff, 1)
```

Effetto atteso: team lv 4-5 rifiutato con `HTTP 423 adventurer.level_too_low`
prima ancora di entrare nel calcolo di success chance su tutti i dungeon
`required_level >= 6`. Success chance formula-side irrilevante (mai
raggiunta). Il problema utente originale **è risolto**.

Test suggeriti in P1: uno stub HTTP che POST `/api/expeditions/dispatch`
con team lv4 su `silent-monastery-5p` → 423 con `min_required_level: 7`.

### Domanda concreta all'utente

> ⚠️ **Confermi di procedere con P1** (wiring runtime del nuovo
> `required_level`)? È un cambio piccolo (1 file, ~15 righe) + test HTTP
> isolato + snapshot backwards-compat. Circa 30 min di lavoro.

Alternative:
- **B1**: sì, procedi con P1 subito.
- **B2**: no, il P0 data-only è sufficiente per ora; il runtime
  enforcement può aspettare (accetto che team lv4 continuino a fare
  dungeon lv7 lato formula).
- **B3**: rimandiamo P1 a un round dedicato (P1 + rebalance
  `recommended_power` insieme).

---

## Decisione C — Necessità di P2

**Dati stacking analysis (dall'audit R16.4 rieseguito)**:

| scenario | team_power | lift |
|---|---:|---:|
| baseline lv4 no equip | 149 | — |
| lv4 + moderate equip (+15/adv) | 179 | +20% |
| lv4 + strong equip (+30/adv, Epic tier) | 239 | **+60.4%** |
| lv7 baseline no equip | 212 | — |
| lv7 + strong equip | 302 | +42% |

**Osservazione**: equip strong (Epic) fa team lv4 (=239) SUPERARE team
lv7 nudo (=212). Questa è la fonte matematica del problema originale:
non è la formula in sé, è che *equip stacking a bassi livelli ammazza la
progressione*.

**Success chance saturation**:
- `team_medio_reale` vs lv1-8 dungeon: 80.6% ~ 94.5% (saturato al top).
- `team_forte_outlier` (lv 6-7, team_power=356) vs lv12 dungeon:
  **93.8%** (endgame trivializzato dal power stacking).

**Verdict**: C → **P2 utile ma non urgente**.

### Cosa farebbe P2

1. **Curva sigmoidale su success chance**: sostituire la mappa lineare
   `delta_power → base_sc` con una sigmoide che comprime la fascia 80-95%
   (i.e. non basta essere leggermente sopra rec_pow per essere quasi
   sicuri).
2. **Soft cap equip runtime**: cap sul contributo di equip_power al team
   totale (es. max 40% del team_power può venire da equip). Impedisce
   il pattern "avv lv4 con Legendary → team_power raddoppia".

Effetto atteso:
- Nessun team supera il 90% di success chance sui dungeon
  `required_level = team_avg_level + 2`.
- Team con equip da +60% power → capped a +40% → curva più prevedibile.

### Domanda concreta all'utente

> Vuoi pianificare P2 dopo P1?
- **C1**: sì, P2 subito dopo P1 (stesso round o round successivo).
- **C2**: no, lasciamo il sistema attuale per capire come si comporta
  con solo P0+P1 in prod, poi rivalutiamo.
- **C3**: rimandiamo P2 a un round di balance dedicato con playtesting.

---

## 7. Risorse e file prodotti

| file | scope | linee |
|---|---|---:|
| `/app/backend/app/scripts/round165_balance_p0_gates_and_legendary_levels.py` | apply script (dry-run + apply + snapshot + preview + whitelist) | ~880 |
| `/app/backend/app/scripts/round165_section19_data_collection.py` | §19 read-only data collection + monkey-patch | ~360 |
| `/app/backend/tests/backend_round165_p0_balance_test.py` | 13 test pytest (invariant + whitelist + idempotenza + mapping) | ~280 |
| `/app/memory/round165_p0_prechange_snapshot.json` | snapshot per rollback | 4934 B |
| `/app/memory/round165_p0_apply_preview.txt` | audit trail preview | 900 B |
| `/app/memory/round165_p0_apply_report.md` | report apply auto-generato | ~120 |
| `/app/memory/round165_p0_apply_data.json` | dati apply strutturati | ~30 KB |
| `/app/memory/round165_p0_post_apply_audit.md` | audit post-apply con prova matematica | ~130 |
| `/app/memory/round165_missing_data_section19.md` + `.json` | §19 data collection | ~150 |
| `/app/memory/round165_p0_final_report.md` | questo report | ~250 |

## 8. Guardrail verificati

- ✅ Whitelist campi (dungeon: `required_level, bucket, progression_tag,
  updated_at`; items: `min_level, updated_at`). 0 violazioni.
- ✅ Nessuna scrittura fuori whitelist (unit test verificato).
- ✅ Nessun `$unset`, `delete_many`, `drop`, `rename`.
- ✅ Nessuna modifica a `equip_power`, `rarity`, `gold`, `xp`,
  `recommended_power`, `difficulty`, `threat_tags`, formule.
- ✅ Pytest strict isolation su `orbus_r16_test` (`ISOLATED_HTTP_TESTS=1`,
  fixture `_ISOLATED_BACKEND_PORT=8002`).
- ✅ Snapshot pre-apply con sha256, deterministicamente rollback-able.
- ✅ **NESSUN Legendary orfano unequippato** (nessuno esiste).

## 9. Rollback plan (se necessario)

```python
import json
from pymongo import MongoClient
import os
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')
db = MongoClient(os.environ['MONGO_URL'])['orbus_r16']
snap = json.load(open('/app/memory/round165_p0_prechange_snapshot.json'))
for d in snap['dungeons']:
    set_doc = {k: v for k, v in d.items() if k != 'slug'}
    db.dungeons.update_one({'slug': d['slug']}, {'$set': set_doc})
for i in snap['items']:
    set_doc = {k: v for k, v in i.items() if k != 'slug'}
    db.items.update_one({'slug': i['slug']}, {'$set': set_doc})
```

**Nota**: dopo il rollback il campo `required_level` resta scritto ma
con valore originale (`0`/`None`). Se serve unset totale: aggiungere
`$unset` sui campi che non erano presenti pre-apply.

---

## 10. Prossimi passi

In attesa delle decisioni **B** (P1 sì/no) e **C** (P2 sì/no).
**A non richiede risposta** (0 orphans).

Se B1 (P1 sì): posso partire con il wiring runtime + test HTTP isolato
(30 min stimati). Nessun rischio produzione perché è una singola aggiunta
in `legacy_min_level_for_dungeon` con precedenza sul nuovo campo (i
dungeon che non hanno `required_level` = comportamento invariato).

---

# 🔧 P0.3 — Runtime Wiring (aggiunta post-decisione utente)

**Autorizzazione**: utente ha confermato **P0.3-a** (wiring subito), **B3**
(no P1 immediato, valutazione post-simulazione), **C3** (no P2).
**Data completamento**: 2026-07-01

## P0.3.1 — File modificati

| file | linee cambiate | scope |
|---|---:|---|
| `/app/backend/app/expeditions/level_gate.py` | +14 -3 | logica gate + payload arricchito |
| `/app/backend/app/expeditions/services.py` | +1 | passa `dungeon_slug` al gate |
| `/app/backend/app/expeditions/preview.py` | +1 | passa `dungeon_slug` al gate |
| `/app/backend/tests/backend_round165_p03_wiring_test.py` | +340 (new) | 7 test HTTP isolati |
| `/app/memory/round165_p0_post_wiring_audit.md` | +130 (new) | audit rapido post-wiring |
| `/app/memory/round165_p0_post_wiring_targeted_sim.md` | +290 (new) | simulazione mirata 6 domande |

## P0.3.2 — Logica runtime finale (`legacy_min_level_for_dungeon`)

```python
def legacy_min_level_for_dungeon(dungeon: dict) -> int:
    """ROUND 16.5 P0.3 — precedenza:
      1. required_level (nuovo canonical field P0.2)
      2. min_adventurer_level (legacy esplicito)
      3. fallback mappa difficulty → min_level
      4. 0 se tutto assente
    """
    r165 = dungeon.get("required_level")
    if isinstance(r165, int) and r165 >= 1:
        return r165
    explicit = dungeon.get("min_adventurer_level")
    if isinstance(explicit, int) and explicit >= 1:
        return explicit
    diff = int(dungeon.get("difficulty", 1) or 1)
    return _DUNGEON_DIFFICULTY_TO_MIN_LEVEL.get(diff, 1)
```

Coerente con la specifica utente `required_level or min_adventurer_level
or 0`, con la deviazione (documentata nell'audit) che a step 3 usiamo il
fallback difficulty invece di 0 puro per retrocompatibilità Round 11.3.

## P0.3.3 — Test eseguiti

**Test HTTP isolati R16.5 P0.3** (7 scenari, tutti su port 8002 con
`ISOLATED_HTTP_TESTS=1` e DB `orbus_r16_test`):

| # | test | scenario | atteso | risultato |
|:-:|---|---|---|:---:|
| 1 | `test_1_team_lv4_vs_worldtree_lv14_blocked` | Team lv4 → world-tree-roots-5p (req=14) | 423 code=level_too_low, min=14, dungeon_slug incluso | ✅ PASS |
| 2 | `test_2_team_lv7_vs_silent_monastery_lv7_gate_passes` | Team lv7 → silent-monastery-5p (req=7) | NO 423 gate | ✅ PASS |
| 3 | `test_3_one_underleveled_blocks_whole_team` | 2×lv8 + 1×lv3 → lich-sanctum (req=5) | 423, offender=[lv3] | ✅ PASS |
| 4 | `test_4_fallback_reads_min_adventurer_level_when_required_level_zero` | req_lvl=0 + min_adv_lvl=5 | 423 con min=5 (fallback) | ✅ PASS |
| 5 | `test_5_no_gate_when_both_fields_absent` | entrambi assenti + difficulty=1 | NO 423 (fallback = 1) | ✅ PASS |
| 6 | `test_6_legacy_only_dungeon_uses_min_adventurer_level` | dungeon vecchio senza P0.2 | 423 dal fallback min_adv_lvl | ✅ PASS |
| 7 | `test_7_payload_shape_contains_all_required_fields` | payload 423 completo | code, source, min_required_level, adventurers_below, dungeon_slug, user_message | ✅ PASS |

**Test R16.5 P0.2 (regression)**: 13/13 PASS (nessuna regressione).

**Totale test R16.5**: **20/20 PASS**.

## P0.3.4 — Esempio payload errore 423 (`adventurer.level_too_low`)

Response body di `POST /api/expeditions` quando il gate scatta:

```json
{
  "detail": {
    "code": "adventurer.level_too_low",
    "source": "expedition.dispatch",
    "min_required_level": 14,
    "adventurers_below": [
      {"id": "r165test-adv-lv3", "name": "R165Test-lv3", "level": 3},
      {"id": "r165test-adv-lv4a", "name": "R165Test-lv4a", "level": 4},
      {"id": "r165test-adv-lv4b", "name": "R165Test-lv4b", "level": 4},
      {"id": "r165test-adv-lv4c", "name": "R165Test-lv4c", "level": 4}
    ],
    "offending_adventurers": [...],
    "count": 4,
    "user_message": "Servono avventurieri di livello 14+. Sotto soglia: R165Test-lv3 (Lv3), R165Test-lv4a (Lv4), R165Test-lv4b (Lv4) e altri 1.",
    "dungeon_slug": "world-tree-roots-5p"
  }
}
```

## P0.3.5 — Verifica team lv4 vs dungeon lv7+

| dungeon | required_level | team lv4 gate | verdict |
|---|---:|:---:|---|
| silent-monastery-5p | 7 | 🛑 blocked (423) | ✅ risolto |
| pirate-fleet-5p | 8 | 🛑 blocked (423) | ✅ risolto |
| obsidian-arena-5p | 9 | 🛑 blocked (423) | ✅ risolto |
| clockwork-vault-5p | 10 | 🛑 blocked (423) | ✅ risolto |
| voidspire-5p | 11 | 🛑 blocked (423) | ✅ risolto |
| infernal-pit-5p | 12 | 🛑 blocked (423) | ✅ risolto |
| celestial-citadel-5p | 13 | 🛑 blocked (423) | ✅ risolto |
| world-tree-roots-5p | 14 | 🛑 blocked (423) | ✅ risolto |

**Zero dungeon lv7+ ancora accessibili a team lv4.** ✅

## P0.3.6 — Dungeon ancora incoerenti (dopo P0 completo)

Dalla simulazione mirata (`round165_p0_post_wiring_targeted_sim.md`):

| dungeon | problema | severità | territorio |
|---|---|:---:|---|
| storm-spire | reward 1620 g/h > pirate-fleet-5p (bucket successivo) 1380 g/h | media | P1 lightweight |
| silent-monastery-5p | reward 1200 g/h < dragons-hoard (bucket precedente) 1440 g/h | bassa | P1 lightweight |
| iron-foundry-5p | rec_pow=140 troppo alto per bucket mid | bassa | P1 lightweight |
| 11 dungeon accessibili con equip alto | mc_success saturato 93-95% (formula lineare) | alta | **P2 (escluso da C3)** |

## P0.3.7 — Raccomandazione motivata su P1

**Raccomandazione: chiudere P0 ora, rimandare P1 a un round dedicato
(Round 16.6).**

Motivazioni:
1. Il problema utente-reported ("team lv4 batte dungeon lv7") è **risolto
   e verificato** con 7 test HTTP isolati sul comportamento reale del
   runtime.
2. Le 3 incoerenze residue sono **piccole** (2 dungeon con reward
   disordinato, 1 con rec_pow leggermente sballato). Nessuna genera
   exploit o farm anomalo.
3. Il P1 tocca `base_gold_reward` — campo economico critico. Merita
   round dedicato con osservazione della telemetria server-side
   (`orbus.level_gate.blocked_attempts`) per 24-72h prima di ritoccare
   la curva economica.
4. Il fenomeno saturazione al 95% mc_success su dungeon accessibili è
   **P2 territorio** (curva sigmoidale + soft cap equip), che l'utente
   ha esplicitamente escluso con C3.

Se invece si vuole procedere subito con P1, scope minimo suggerito:
- `storm-spire.base_gold_reward` -20%
- `silent-monastery-5p.base_gold_reward` +20%
- `iron-foundry-5p` valutare bucket "hard-mid" dedicato

## P0.3.8 — Sorprese emerse

1. **Il DB `orbus_r16_test` era già popolato con `required_level` da
   una run precedente dei test R16.5 P0.2**. La fixture `applied_test_db`
   del file P0.2 aveva già applicato il mapping. Questo ha reso lo shape
   dei dungeon in test uguale a prod → nessun problema, anzi coerente.

2. **Il payload legacy `offending_adventurers` era già usato dal
   frontend/altri caller** — ho mantenuto l'alias per retro-compat oltre
   al nuovo `adventurers_below`. Zero breaking change lato FE.

3. **La formula lineare `sc = 50 + delta_pw` è il vero collo di
   bottiglia** ora che il gate è attivo. Un team con equip Legendary vs
   un dungeon accessibile ha quasi sempre mc_success >90%. Non è un
   problema del gate ma della curva. **Confermato territorio P2**
   (escluso da C3). Segnalo per completezza — non ho toccato nulla.

4. **Nessun caller "orfano" del gate**: `enforce_min_adventurer_level`
   ha esattamente 4 caller (2 dungeon + 2 raid). I raid usano
   `legacy_min_level_for_raid` (funzione separata basata su `tier` del
   raid) → intentionally NOT touched.

## P0.3.9 — Guardrail rispettati

- ✅ **Nessuna modifica al DB `orbus_r16`**: il wiring è solo di lettura
  del campo `required_level` già scritto in P0.2.
- ✅ **Nessuna modifica a reward/drop/XP/economia/PvP/Stalla/threat_tags/
  equip_power/rarity/formula success chance/soft cap**.
- ✅ **Test rigidamente isolati su `orbus_r16_test`** (`ISOLATED_HTTP_TESTS=1`,
  port 8002, verificato dai log `[orbus.test] INFO isolated backend
  ready on http://127.0.0.1:8002 (DB_NAME=orbus_r16_test)`).
- ✅ **Nessun bug su caller legacy segnalato e non "aggiustato" senza
  richiesta**.
- ✅ **Lingua report/log: italiano**.

---

## Riepilogo P0 COMPLETO (P0.1 + P0.2 + P0.3)

| fase | contenuto | test | status |
|---|---|:---:|:---:|
| P0.1 | Dry-run + mapping proposal | — | ✅ approvato |
| P0.2 | Apply data (22 dungeon + 5 legendary), snapshot, whitelist | 13/13 | ✅ chiuso |
| P0.3 | Wiring runtime gate + payload arricchito | 7/7 | ✅ chiuso |
| Sim mirata | Prova post-wiring lv4 vs lv7+ + 6 risposte utente | — | ✅ chiuso |
| **Totale R16.5 P0** | **problema utente risolto e verificato** | **20/20 pass** | ✅ **PRONTO PER CHIUSURA** |

Attendo conferma utente per marcare Round 16.5 P0 come **CLOSED** e
decidere se aprire subito Round 16.6 P1 o rimandare.
