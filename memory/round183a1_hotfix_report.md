# ROUND 18.3a.1 HOTFIX — `/api/adventurer-classes` HTTP 500 Blocker Fix

**Round**: R18.3a.1 (hotfix di R18.3a) · **Data**: 2026-07-04T20:06Z · **Autore**: e1 main agent
**Status**: HOTFIX APPLICATO ✅ — 3 fix chirurgici, 10 test aggiuntivi (71/71 regression), blocker rimosso.

---

## 1. Root cause

I 2 documenti seedati da R18.3a (`cacciatore_di_mostri`, `cacciatore_del_vuoto`) NON avevano il campo `role`. Il serializer `class_public()` in `/app/backend/app/adventurers/services.py:134` leggeva `doc["role"]` senza `.get()` → **KeyError: 'role'** → **HTTP 500** su:
- `GET /api/adventurer-classes` (player-facing) ⚠️
- `GET /api/admin/classes` (admin)

**Impatto**: lista classi irraggiungibile per tutti i player, non solo per le 2 target. Regressione totale.

---

## 2. Correzioni applicate (3 fix chirurgici in un unico pass)

### Fix 1 — Filtro hidden classes dal listing player-facing

**File**: `/app/backend/app/adventurers/routes.py` (line 46-56)

```python
# BEFORE:
async def list_classes():
    classes = (
        await db.adventurer_classes.find({"is_active": True}, {"_id": 0})
        ...
    )

# AFTER (R18.3a.1):
async def list_classes():
    # ROUND 18.3a.1 hotfix — escludi le classi hidden (is_playable=false)
    # dalla lista player-facing. Le classi target-migration R18.3a
    # (cacciatore_di_mostri, cacciatore_del_vuoto) restano invisibili
    # ai player fino al flip esplicito in R18.3 apply.
    classes = (
        await db.adventurer_classes.find(
            {"is_active": True, "is_playable": {"$ne": False}}, {"_id": 0}
        )
        ...
    )
```

**Effetto**: le 2 classi target-migration non arrivano più al serializer via endpoint player-facing (defense in depth).

### Fix 2 — Serializer `class_public()` difensivo

**File**: `/app/backend/app/adventurers/services.py` (line 126-180)

```python
# BEFORE (crash-prone):
"role": doc["role"],
"id": doc["id"],
"name": doc["name"],
"slug": doc["slug"],

# AFTER (R18.3a.1 defensive):
"role": doc.get("role", "TBD"),  # PM Q7-Q24 deferred
"id": doc.get("id"),
"name": doc.get("name") or doc.get("slug") or "",
"display_name_it": doc.get("display_name_it") or doc.get("name") or doc.get("slug") or "",
"slug": doc.get("slug"),
```

Inoltre esposto R18 metadata:
```python
"is_playable": doc.get("is_playable", True),
"migration_target_only": bool(doc.get("migration_target_only", False)),
"source_round": doc.get("source_round"),
"role_placeholder": bool(doc.get("role_placeholder", False)),
"role_pm_decision_pending": bool(doc.get("role_pm_decision_pending", False)),
```

**Effetto**: schema-evolution safe. Nuovi seed con schema minimale non crashano.

### Fix 3 — Backfill role="TBD" + marker deferred

**Script**: `/app/backend/app/scripts/round183a1_backfill_role_placeholder.py`

Update `adventurer_classes` sui 2 doc R18.3a:

```python
db.adventurer_classes.update_many(
    {"slug": {"$in": ["cacciatore_di_mostri", "cacciatore_del_vuoto"]},
     "source_round": "R18.3a"},
    {"$set": {
        "role": "TBD",                          # placeholder, PM Q7-Q24 deferred
        "role_placeholder": True,               # marker: valore provvisorio
        "role_pm_decision_pending": True,       # marker esplicito per PM
        "updated_at": <iso_utc>,
    }}
)
```

**Idempotenza confermata (verifica live)**:
- Primo `--apply`: `update_many: matched=2 modified=2` + `[audit] emitted`
- Secondo `--apply`: `all docs already backfilled — no update` + `[audit] already logged — skip`

---

## 3. Verifica curl end-to-end (live)

### Player-facing endpoint
```
GET /api/adventurer-classes
→ HTTP 200
→ 11 classi ritornate
→ cacciatore_di_mostri in list?  False ✅
→ cacciatore_del_vuoto in list?  False ✅
→ recruit_unassigned in list?    False ✅
→ sample: ['alchemist', 'bard', 'druid', 'mage', 'monk']
```

### Admin endpoint
```
GET /api/admin/classes (JWT admin)
→ HTTP 200
→ 13 classi ritornate (include hidden)
→ cacciatore_di_mostri in list?  True ✅
   role='TBD' · role_placeholder=True · role_pm_decision_pending=True · is_playable=False · migration_target_only=True
→ cacciatore_del_vuoto in list?  True ✅
   role='TBD' · role_placeholder=True · role_pm_decision_pending=True · is_playable=False · migration_target_only=True
```

Log backend live conferma:
```
INFO: "GET /api/adventurer-classes HTTP/1.1" 200 OK
INFO: "GET /api/admin/classes HTTP/1.1" 200 OK
```

---

## 4. Audit event opzionale emesso

**Event**: `R18_CLASS_ROLE_PLACEHOLDER_BACKFILLED` · **Idempotent**: sì

Metadata:
```json
{
  "round": "R18.3a.1",
  "hotfix_for": "R18.3a",
  "reason": "Prevent HTTP 500 on class_public() when doc missing 'role'",
  "slugs_affected": ["cacciatore_di_mostri", "cacciatore_del_vuoto"],
  "role_placeholder_value": "TBD",
  "role_pm_decision_pending": true,
  "pm_decision_deferred_questions": "Q7-Q24",
  "docs_matched": 2,
  "docs_backfilled": 2
}
```

Whitelist admin `AUDIT_EVENT_WHITELIST` esteso con `R18_CLASS_ROLE_PLACEHOLDER_BACKFILLED`.

---

## 5. Test suite (10 nuovi + 61 regression = 71/71 PASS)

**File**: `/app/backend/tests/backend_round183a1_hotfix_test.py`

| # | Test | Scope | Status |
|---|---|---|---|
| 01 | `class_public_serializer_defensive_all_fields` | Doc minimale (solo slug/is_active/is_playable) non crasha, role='TBD' default | ✅ |
| 02 | `class_public_empty_doc_no_crash` | Edge case empty doc → tutti default | ✅ |
| 03 | `role_placeholder_backfilled` | I 2 doc target hanno role='TBD' + placeholder=true + pending=true | ✅ |
| 04 | `role_backfill_idempotent` | Marker stabili post-apply (secondo read identico) | ✅ |
| 05 | `audit_event_backfill_emitted` | `R18_CLASS_ROLE_PLACEHOLDER_BACKFILLED` emesso + metadata completa | ✅ |
| 06 | `audit_whitelist_backfill_event` | Whitelist admin include event type | ✅ |
| 07 | `list_classes_route_has_is_playable_filter` | Route sorgente contiene filtro `$ne: False` | ✅ |
| 08 | `class_public_source_has_tbd_default` | Serializer sorgente contiene `doc.get("role", "TBD")` | ✅ |
| 09 | `previous_test_modules_importable` | Regression sanity R18.1/R18.2/R18.1.2/R18.3a moduli importabili | ✅ |
| 10 | `q7_q24_deferred_marker_present` | Marker `role_pm_decision_pending=true` presente (zero decisione PM) | ✅ |

**Regression cross-round completa**:
```
tests/backend_round181_migration_test.py:      18/18 PASS
tests/backend_round182_talent_pilot_test.py:   15/15 PASS
tests/backend_round1812_guard_test.py:         12/12 PASS
tests/backend_round183a_prereq_test.py:        16/16 PASS
tests/backend_round183a1_hotfix_test.py:       10/10 PASS
-----------------------------------------------------------
TOTAL:                                         71/71 PASS in 0.68s
```

---

## 6. Vincoli rispettati

| Vincolo | Status |
|---|---|
| Zero riapertura R18.1.1 / R18.1.2 / R18.2 PILOT (sealed) | ✅ |
| Zero decisione PM su role finale (Q7-Q24 rispettati) | ✅ (`role='TBD'` + `role_pm_decision_pending=true`) |
| Zero modifica al guard R18.1.2 | ✅ (`expeditions/services.py` non toccato) |
| Zero modifiche combat math / drop / reward / economia / PvP / premium | ✅ |
| Zero hard delete dei 2 doc seeded | ✅ (solo `$set` idempotente) |
| Zero player-facing UI change | ✅ (endpoint ora RIPRISTINATO, non modificato semanticamente) |
| Idempotenza backfill | ✅ (verificato live: secondo run = 0 modifiche) |
| Filter `is_playable != False` sul route pubblico | ✅ |
| Serializer difensivo (tutti campi con `.get()`) | ✅ |
| Test suite ≥ 6 nuovi | ✅ (10 delivered) |
| Regression cross-round 61+ | ✅ (71/71 PASS) |

---

## 7. File toccati/creati

| Path | Op | Descrizione |
|---|---|---|
| `/app/backend/app/adventurers/routes.py` | Patch (5 righe) | Fix 1: filtro `is_playable != False` |
| `/app/backend/app/adventurers/services.py` | Patch (60 righe) | Fix 2: serializer difensivo + R18 metadata expose |
| `/app/backend/app/admin/audit_routes.py` | Patch (5 righe) | Whitelist esteso a `R18_CLASS_ROLE_PLACEHOLDER_BACKFILLED` |
| `/app/backend/app/scripts/round183a1_backfill_role_placeholder.py` | New (140 righe) | Fix 3: backfill idempotente + audit emit |
| `/app/backend/tests/backend_round183a1_hotfix_test.py` | New (10 test, 210 righe) | Test suite hotfix |
| `/app/memory/round183a1_hotfix_report.md` | New | Questo report |

---

## 8. R18.3a status update

- **R18.3a**: `PARTIAL SEAL → RESEAL POST-HOTFIX ✅`
  - Pre-req migration DONE, blocker HTTP 500 corretto in R18.3a.1
  - Test 71/71 PASS end-to-end
  - Pronto per verifica tester #2

Il PM può ora considerare R18.3a **technically-sealed** (con hotfix R18.3a.1 come "asterisco tecnico" che rimuove il blocker senza toccare le decisioni PM deferrate su role/Q7-Q24).

---

## 9. Firma

**R18.3a.1 hotfix CLOSED ✅ (2026-07-04T20:06Z)**

Test 10/10 (nuovi) + 61/61 (regression) = **71/71 PASS**. Blocker HTTP 500 rimosso. `role="TBD"` placeholder con marker esplicito `role_pm_decision_pending=true` (Q7-Q24 deferred). Zero decisioni sul role finale.

*Firma: e1 main agent · 2026-07-04T20:06Z · R18.3a.1 HOTFIX COMPLETE*
