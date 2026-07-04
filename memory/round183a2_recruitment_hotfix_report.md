# ROUND 18.3a.2 — Recruitment Hidden Class Filter Hotfix

**Round**: R18.3a.2
**Data sealing**: 2026-07-04T21:38Z
**Status**: CLOSED & SEALED
**Type**: Hotfix chirurgico (P0 produzione)
**Autore**: e1 main agent (autorizzato da PM decision Q2.a)

---

## §1 · Executive summary

**Bug live P0 risolto**: `POST /api/recruitment/refresh` restituiva HTTP 500 con probabilità ~15% (2/13) a causa di `filter_safe_class_pool` che includeva 2 classi hidden R18.3a (`cacciatore_di_mostri`, `cacciatore_del_vuoto`) senza campi `base_*` stat. Quando `rng.choice()` del generator le pescava, `klass["base_strength"]` sollevava `KeyError` e propagava HTTP 500.

**Patch**: 1 chiave aggiunta al filter MongoDB di `filter_safe_class_pool` in `app/adventurers/generator.py:89`:
```python
"is_playable": {"$ne": False},
```

**Impact**:
- 2 hidden classes escluse dal recruitment pool (11 classi legacy restano)
- HTTP 500 rate: **~15% → 0%** (verificato 10/10 curl + 100/100 test in-process)
- Zero DB write, zero schema migration, zero combat math change

**Backend downtime**: 0s (hot-reload).

---

## §2 · Root cause analysis

### Traceback originale
```
File "/app/backend/app/recruitment/routes.py", line 50, in refresh_recruitment_candidates
    return await refresh_candidates_for_guild(db, guild)
File "/app/backend/app/recruitment/services.py", line 366, in refresh_candidates_for_guild
    candidates = await _roll_and_persist_offer(db, updated_guild)
File "/app/backend/app/recruitment/services.py", line 225, in _roll_and_persist_offer
    c = await generate_candidate(...)
File "/app/backend/app/adventurers/generator.py", line 260, in generate_candidate
    candidate = _legacy_gen(klass, ...)
File "/app/backend/app/adventurers/common.py", line 115, in _generate_candidate
    "strength": _roll_stat(klass["base_strength"], bonus, rng=rng),
KeyError: 'base_strength'
```

### Root cause
- **Round originator**: R18.3a (2026-07-04T20:12Z) ha seedato `cacciatore_di_mostri` e `cacciatore_del_vuoto` come classi target migrazione con:
  - `is_playable=False` (non pescabili dal player-facing)
  - `migration_target_only=True` (accessibili solo via migration R18.3c)
  - `is_active=True` (visibili per audit/admin)
  - `is_base_class` non impostato (default treatment)
  - **Non seedati** i campi `base_strength / base_agility / base_intellect / base_endurance / base_faith` (verrebbero decisi in R18.3b P0-Q7..Q24, oggi ancora deferred).
- **`filter_safe_class_pool`** a `generator.py:87-109` filtra `is_active=True` + `is_test != True` + (`is_base_class=True` OR `is_base_class` unset AND `deprecated_at=None`). Le 2 hidden classes soddisfano il filtro perché sono `is_active=True` e non hanno `is_base_class` impostato + `deprecated_at=None`.
- **Recruitment generator** a `generate_candidate:256` fa `rng.choice(classes)` sul pool. Le 2 hidden classes hanno probabilità 2/13 ≈ 15% di essere pescate.
- **`_generate_candidate`** in `common.py:115` legge direttamente `klass["base_strength"]` senza `.get()` → KeyError.

### Perché il filtro `is_playable` mancava
R18.3a è stato progettato con `is_playable=False` come **flag semantico** ma solo il player-facing `/api/adventurer-classes` (routes.py) e la R18.3a.1 hotfix hanno applicato il filtro. Il recruitment generator è stato missed.

### Perché R18.3a.1 non l'ha rilevato
R18.3a.1 ha coperto `class_public()` serializer + `/api/adventurer-classes` listing route + backfill `role="TBD"`. Non ha coperto il recruitment generator pool query (usato da 2 endpoint distinti + starter fallback).

---

## §3 · Patch chirurgica

### File modificato
`/app/backend/app/adventurers/generator.py`

### Funzione modificata
`filter_safe_class_pool` (linee 87-109)

**Nota importante**: il brief PM citava `generator.py:64`, ma la linea 64 è il **traits** pool (`filter_safe_trait_pool`), non il classes pool. La modifica corretta è alle linee 87-109 (`filter_safe_class_pool`). Verifica: i 2 filter hanno pattern MongoDB simili — `{"is_active": True, "is_test": {"$ne": True}}` — probabilmente all'origine della confusione. La patch è stata applicata al classes pool (il target semanticamente corretto).

### Diff
```python
# BEFORE (linee 87-103)
rows = await db.adventurer_classes.find(
    {
        "is_active": True,
        "is_test": {"$ne": True},
        "$or": [
            {"is_base_class": True},
            {"$and": [
                {"is_base_class": {"$exists": False}},
                {"deprecated_at": None},
            ]},
        ],
    },
    {"_id": 0},
).to_list(100)

# AFTER (linee 87-109 con nuovo commento marker)
rows = await db.adventurer_classes.find(
    {
        "is_active": True,
        "is_test": {"$ne": True},
        # ROUND 18.3a.2 HOTFIX — exclude hidden classes seeded by
        # R18.3a (`cacciatore_di_mostri`, `cacciatore_del_vuoto`) that
        # carry `is_playable=false` + `migration_target_only=true` and
        # lack `base_*` stat fields. Without this filter, recruitment
        # rng.choice would occasionally pick them and crash with
        # KeyError: 'base_strength' inside `_generate_candidate`.
        # `$ne: False` preserves legacy docs where `is_playable` is
        # unset (they pass) while excluding only explicit False.
        "is_playable": {"$ne": False},
        "$or": [
            {"is_base_class": True},
            {"$and": [
                {"is_base_class": {"$exists": False}},
                {"deprecated_at": None},
            ]},
        ],
    },
    {"_id": 0},
).to_list(100)
```

### Perché `$ne: False` e non `is_playable: True`
- I 11 doc legacy classes (warrior, rogue, mage, priest, ranger, paladin, druid, monk, bard, warlock, alchemist) NON hanno il campo `is_playable` seedato → `is_playable` è `undefined`.
- `{"is_playable": True}` scarterebbe TUTTI i 11 legacy (regression severa).
- `{"is_playable": {"$ne": False}}` accetta `undefined` + `True`, esclude solo `False` → 11 legacy passano, 2 hidden escluse. ✅

---

## §4 · Audit event

**Nome**: `R18_RECRUITMENT_HIDDEN_CLASS_FILTER_PATCHED`

**Aggiunto a**: `AUDIT_EVENT_WHITELIST` in `/app/backend/app/admin/audit_routes.py`

**Metadata emessa**:
```json
{
  "round": "R18.3a.2",
  "hotfix_for": "R18.3a",
  "file": "app/adventurers/generator.py",
  "function": "filter_safe_class_pool",
  "line_range": "87-109 (actual patch); brief cited line 64",
  "filter_added": "is_playable != false",
  "db_write": false,
  "schema_migration": false,
  "adventurers_touched": false,
  "combat_math_changed": false,
  "auto_equip_changed": false,
  "role_enum_changed": false,
  "player_facing_bug_fixed": true,
  "bug_source_round": "R18.3a",
  "bug_symptom": "HTTP 500 recruitment refresh ~15% failure rate due to hidden classes without base_* fields",
  "bug_endpoint": "/api/recruitment/refresh",
  "bug_error": "KeyError: 'base_strength'",
  "bug_probability_pre_patch": "~2/13 = ~15%",
  "hidden_slugs_excluded": ["cacciatore_di_mostri", "cacciatore_del_vuoto"],
  "hidden_docs_in_db_intact": 2,
  "hidden_docs_untouched": true
}
```

**Idempotenza**:
- Script apply: secondo run → `already logged — skip`
- Audit_log count: sempre 1

**Come emettere**:
```
cd /app/backend && python -m app.scripts.round183a2_recruitment_filter_hotfix --apply
```

---

## §5 · Test suite

**File**: `/app/backend/tests/backend_round183a2_recruitment_hotfix_test.py`
**Target**: ≥ 7 test
**Delivered**: **11 test**
**Result**: **11/11 PASS** (tempo esecuzione 1.08s)

| # | Test | Verifica | Status |
|---|---|---|---|
| 01 | `filter_safe_class_pool_excludes_hidden` | hidden classes NON nel pool | ✅ PASS |
| 02 | `filter_safe_class_pool_keeps_legacy` | 11 legacy classes preservate | ✅ PASS |
| 03 | `all_pool_classes_have_base_strength` | ogni classe pool ha `base_*` fields | ✅ PASS |
| 04 | `100_iterations_no_crash` | 100 `generate_candidate` senza KeyError | ✅ PASS |
| 05 | `hidden_classes_still_in_db` | DB non toccato (regression) | ✅ PASS |
| 06 | `adventurer_classes_route_no_hidden_leak` | R18.3a.1 filter regression | ✅ PASS |
| 07 | `audit_event_emitted` | audit event 1x emesso | ✅ PASS |
| 08 | `audit_whitelist_extended` | whitelist include nuovo evento | ✅ PASS |
| 09 | `generator_source_has_hotfix_marker` | source contiene marker | ✅ PASS |
| 10 | `r1812_guard_whitelist_intact` | R18.1.2 guard non toccato | ✅ PASS |
| 11 | `prior_r18_audit_events_intact` | cross-round whitelist regression | ✅ PASS |

### Regression cross-round
```
tests/backend_round1812_guard_test.py        (R18.1.2)
tests/backend_round182_talent_pilot_test.py  (R18.2)
tests/backend_round183a1_hotfix_test.py      (R18.3a.1)
tests/backend_round183a_prereq_test.py       (R18.3a)
tests/backend_round183c_migration_test.py    (R18.3c)
tests/backend_round183a2_recruitment_hotfix_test.py  (R18.3a.2 NEW)
```
**Risultato**: **87/87 PASS** in 2.06s.

**Non incluso**: `tests/backend_round181_migration_test.py` (4 drift noti: 1058 adv invalid class_slug, 1058 senza grade, 303/663 guilds max_roster_cap, 303/663 r18_beta_opt_in). Il drift è indipendente da R18.3a.2 e sarà affrontato in R18.1.3 (backfill) o obsoletato in R18.Reset.0.

### Verifica bug live risolto
```
API_URL=$REACT_APP_BACKEND_URL
TOKEN=<login tester@orbus.test>
for i in {1..10}; do
    curl -s -o /dev/null -w "%{http_code}" \
        -X POST "$API_URL/api/recruitment/refresh" \
        -H "Authorization: Bearer $TOKEN"
done
```
**Risultato**: `200 200 200 200 200 200 200 200 200 200` — **10/10 HTTP 200**, zero 500.

Prima della patch, statisticamente ~1-2 su 10 sarebbero stati 500. Con 100 iterazioni in-process del test #4, tutte 100 senza crash.

---

## §6 · Verifica DB stato

**Prima della patch**:
- `adventurer_classes` count: 18
- Classi passing filter attuale: 13 (11 legacy + 2 hidden senza `base_*`)
- Classi missing `base_strength`: 3 (`recruit_unassigned` non pescata + `cacciatore_di_mostri` + `cacciatore_del_vuoto`)

**Dopo la patch**:
- `adventurer_classes` count: 18 (invariato)
- Classi passing filter: 11 (solo legacy)
- Classi missing `base_strength`: 3 (identiche, invariate)
- 2 hidden restano intatte nel DB per audit/admin/dispatch guard (R18.1.2)

---

## §7 · Vincoli rispettati (checklist R18.3a.2)

- ✅ Zero DB write sui doc `adventurer_classes`
- ✅ Zero DB write sui doc `adventurers`
- ✅ Zero seed nuovi
- ✅ Zero schema migration
- ✅ Zero modifica combat math
- ✅ Zero modifica auto_equip formula
- ✅ Zero modifica reward / drop / economia / PvP / premium
- ✅ Zero hard delete
- ✅ Zero UI change
- ✅ Zero touch al VALID_ROLES enum
- ✅ Zero modifica R18.3d mapping registry (PAUSED)
- ✅ Zero backfill drift R18.1
- ✅ Solo modifica sorgente `generator.py` (1 chiave filter) + `audit_routes.py` (whitelist +1 evento) + audit event marker one-shot

---

## §8 · Files deliverable

| File | Tipo | Righe | Nota |
|---|---|---|---|
| `app/adventurers/generator.py` | Modified | +8 (commento + 1 chiave filter) | Patch chirurgica |
| `app/admin/audit_routes.py` | Modified | +7 (commento + 1 evento) | Whitelist estesa |
| `app/scripts/round183a2_recruitment_filter_hotfix.py` | New | 138 | Script apply audit event |
| `tests/backend_round183a2_recruitment_hotfix_test.py` | New | 246 | 11 test |
| `memory/round183a2_recruitment_hotfix_report.md` | New | ~340 | Questo report |
| `memory/orbus_world_roadmap.md` | Modified | +1 riga | R18.3a.2 sealed |
| `memory/backlog.md` | Modified | +100 (nuova sezione) | R18.3a.2 sealed |

---

## §9 · Appendice — Warning correlato pre-esistente (non coperto)

**Warning** rilevato ai backend logs (durante il boot post-patch, ma pre-esistente da R18.3a):
```
2026-07-04 21:31:14,147 - orbus.seed_round5 - WARNING - starter backfill failed: 'base_strength'
2026-07-04 21:31:14,147 - orbus.seed_round5 - INFO - ROUND 5 boot: ... starter_backfill=0 (idempotent)
```

**Interpretazione**: la routine `seed_round5` esegue uno `starter_backfill` al boot che tenta di completare gli starter adventurers per gilde legacy. Anche questa routine legge `klass["base_strength"]` da una selezione di `adventurer_classes` che probabilmente include le 2 hidden. Il fallback ha catturato l'eccezione (`starter_backfill=0`, no player-facing crash), ma il warning resta.

**Impact**: nullo player-facing (routine di boot con try/except). Migliorabile in un round successivo separato (es. `R18.3a.3` o consolidato in `R18.Reset.0`).

**Non coperto da R18.3a.2**: la patch tocca solo `filter_safe_class_pool` usato da `generate_candidate` (recruitment). Il starter fallback usa un pool separato interno a `seed_round5` (non ho indagato oltre per non uscire dallo scope hotfix).

---

## §10 · Segnala al PM

R18.3a.2 **CLOSED & SEALED**. Attendo che tu (PM):
1. Confermi verifica indipendente via `e1_tester`
2. Fornisca go per Round 2 (R18.Reset.0 planning audit-only)

**Non toccare R18.3d** (resta PAUSED come da direttiva).
**Non toccare drift R18.1** (resta in HOLD come da direttiva).

*Firma sealing: e1 main agent — 2026-07-04T21:38Z*
