# ROUND 18.3a — Orphan Migration Plan (SLUG-CORRECTED, DRY-RUN ONLY)

**Round:** R18.3a · **Data:** 2026-07-04 · **Autore:** e1 main agent
**Status:** DRY-RUN COMPLETO. **NESSUN APPLY su adventurers.** Apply reale richiede brief PM separato (R18.3).

**Fonte dry-run**: `/app/backend/app/scripts/round183a_orphan_migration_dry_run.py`
**Report JSON**: `/app/memory/round183a_orphan_migration_dry_run.json`
**Predecessor**: `/app/memory/round182_orphan_migration_plan.md` (deprecated per slug corretti)

---

## 0. Slug correction note

PM Q6 sigilla i seguenti slug canonici (con preposizione articolata):

| R18.2 (sbagliato, mai seedato) | R18.3a (corretto) |
|---|---|
| `cacciatore_mostri` | **`cacciatore_di_mostri`** |
| `cacciatore_vuoto` | **`cacciatore_del_vuoto`** |

Documenta: nessun record DB o audit event pre-R18.3a usa le forme brevi. Il dry-run R18.2 è stato quindi solo un artefatto testuale, senza impatto DB.

---

## 1. Sommario esecutivo

Le 5 classi live orphan (496 adv attivi) sono state analizzate in modalità **read-only**. Zero write op eseguite su `adventurers` durante il dry-run.

Modifiche DB effettuate SOLO in R18.3a (append-only, safety pre-req):
1. Seed 2 nuove classi in `adventurer_classes` con `is_playable=false + migration_target_only=true`.
2. Bridge item append: `recommended_classes` estese su 49 item esistenti (31 ranger + 18 warlock).

| Source | Target | Type | Actual adv | Delta vs expected | Guilds impact | Item pool target | Rischio |
|---|---|---|---|---|---|---|---|
| priest | paladin | merge_into_existing | **190** | 0 | 175 | 92 | **BASSO** |
| ranger | **cacciatore_di_mostri** | migration_to_new_class | **175** | 0 | 175 | **31** (post-bridge) | **BASSO** ✅ |
| warlock | **cacciatore_del_vuoto** | migration_to_new_class | **128** | 0 | 128 | **18** (post-bridge) | **BASSO** ✅ |
| berserker | warrior | alias_deprecated | **3** | 0 | 3 | 69 | BASSO |
| assassin | rogue | alias_deprecated_zero_migration | **0** | 0 | 0 | 31 | n/a |
| **TOTALE** | | | **496** | 0 | | | |

**Rischio ALTO → BASSO**: gli item pool per `cacciatore_di_mostri` (0 → 31) e `cacciatore_del_vuoto` (0 → 18) sono ora coperti grazie all'append-only bridge sul catalog `items`.

**Zero adventurer in expedition attiva** al momento del dry-run → migration window sicura.

**Zero adventurer con talent_progress esistente** → coerente con R18.2 PILOT (schema only).

---

## 2. R18.3a Class Seed — dettaglio

### `cacciatore_di_mostri`

```json
{
  "slug": "cacciatore_di_mostri",
  "name": "Cacciatore di Mostri",
  "display_name_it": "Cacciatore di Mostri",
  "is_playable": false,
  "migration_target_only": true,
  "is_canonical": true,
  "is_active": true,
  "source_round": "R18.3a",
  "source_slug_bridge": "ranger",
  "pm_decision": "Q2"
}
```

### `cacciatore_del_vuoto`

```json
{
  "slug": "cacciatore_del_vuoto",
  "name": "Cacciatore del Vuoto",
  "display_name_it": "Cacciatore del Vuoto",
  "is_playable": false,
  "migration_target_only": true,
  "is_canonical": true,
  "is_active": true,
  "source_round": "R18.3a",
  "source_slug_bridge": "warlock",
  "pm_decision": "Q3"
}
```

**Player-facing leak check** (post-seed, verificato live):
- `GET /api/adventurer-classes` — nessuna delle due classi appare (filtro implicit su `is_playable=false` via `_public_fields`/existing route logic).
- Recruitment routes (`recruitment/services.py`) — filtrano già su `is_playable` (verified via `expeditions/services.py:874`).
- Guard R18.1.2 (whitelist ext) — accetta questi 2 slug con `is_playable=false` in expedition dispatch (safety per R18.3 apply future).

---

## 3. R18.3a Item Bridge — dettaglio

### `ranger → cacciatore_di_mostri` (31 items)

Append-only su `recommended_classes` via `$addToSet`. Zero override, zero delete.

| Slot/Item Type | Rarity dist | Level dist |
|---|---|---|
| Vedi report JSON | Vedi report JSON | Vedi report JSON |

Post-bridge count: **31 item accessibili a `cacciatore_di_mostri`** (dal count pre-migration `db.items.count_documents({"recommended_classes": "cacciatore_di_mostri"})`).

### `warlock → cacciatore_del_vuoto` (18 items)

Append-only su `recommended_classes` via `$addToSet`. Zero override, zero delete.

Post-bridge count: **18 item accessibili a `cacciatore_del_vuoto`**.

**Vincoli rispettati**:
- ✅ Zero modifica a `stats`, `rarity`, `required_adventurer_level`, `required_level`, `power_score`, `drop_rate`, `is_tradeable`, `is_bound`.
- ✅ Solo `$addToSet` su `recommended_classes` (append-only, idempotente per definizione).
- ✅ Nessun item nuovo creato.
- ✅ Nessun item eliminato.

---

## 4. Piano migration per target (invariato dal R18.2 ex slug names)

### Q1 — priest → paladin (190 adv)
- **Tipo**: merge_into_existing (Paladino esiste già come class_slug=paladin, playable=True)
- **Delta atteso 190 vs actual 190**: ✅ match esatto
- **Impatto**: 190 adv → 175 guilds impattate (avg 1.08 priest/guild)
- **Item pool target `paladin`**: 92 item (BASSO risk)
- **Off-class post-migration**: sample 5 mostra 0 caso di item recommended_for=priest orphan.

### Q2 — ranger → **cacciatore_di_mostri** (175 adv)
- **Tipo**: migration_to_new_class (target esistente R18.3a live in catalog)
- ✅ **BLOCKER RISOLTO**: `cacciatore_di_mostri` esiste in `adventurer_classes` con marker canonical + migration_target_only + hidden from recruitment.
- ✅ **BLOCKER RISOLTO**: item pool aumentato da 0 → 31 tramite bridge append.
- **Delta 175 vs 175**: ✅ match
- **Pre-requisiti R18.3 apply**: TUTTI DONE post R18.3a.
- **Ancora da fare** in R18.3: flip `is_playable=false → true` + `migration_target_only=true → false` post apply, banner UI comunicazione, career_history snapshot per ogni migration.

### Q3 — warlock → **cacciatore_del_vuoto** (128 adv)
- **Tipo**: migration_to_new_class (target esistente R18.3a live in catalog)
- ✅ **BLOCKER RISOLTO**: seed R18.3a completato, bridge item pool 0 → 18.
- **Delta 128 vs 128**: ✅ match
- **Pre-requisiti**: come Q2.

### Q4 — berserker → warrior (3 adv)
- **Tipo**: alias_deprecated (target esiste, class merge)
- **Delta 3 vs 3**: ✅ match
- **Impatto**: 3 adv, low risk. Item pool warrior=69 sufficiente.

### Q5 — assassin → rogue (0 adv)
- **Tipo**: alias_deprecated_zero_migration
- **Delta 0 vs 0**: ✅ match, nessuna migration necessaria

---

## 5. Impact matrix

### Guilds impattate (invariato)
- **175 guilds** con almeno un priest (target paladin merge)
- **175 guilds** con almeno un ranger (target `cacciatore_di_mostri`)
- **128 guilds** con almeno un warlock (target `cacciatore_del_vuoto`)
- **3 guilds** con berserker
- **0 guilds** con assassin

### Adventurer in expedition attiva
- **0/496** → migration window sicura

### Rischio player-facing R18.3a
- ✅ Zero. Classi seedate con `is_playable=false` — nessuna esposizione a recruitment/onboarding/generator/training.
- ✅ Zero adventurer con class_slug `cacciatore_di_mostri` o `cacciatore_del_vuoto` (dry-run only, nessun apply).
- ✅ Guard R18.1.2 (whitelist ext) accetta questi 2 slug come dispatch-valid → nessun block su future migration.

---

## 6. Vincoli rispettati (R18.3a)

| Vincolo | Status |
|---|---|
| Zero hard delete (adventurer, classi, item) | ✅ |
| Zero apply migration reale su adventurer | ✅ |
| Zero modifica a stats/rarity/level/drop/power/reward | ✅ |
| Zero nuovo item creato | ✅ |
| Zero player-facing UI change | ✅ |
| Feature flag `R18_REWORK_ENABLED=false` preservato | ✅ |
| Feature flag `R18_TALENT_ENGINE_ENABLED=false` preservato | ✅ |
| Append-only su `recommended_classes` (idempotente `$addToSet`) | ✅ |
| Idempotency script | ✅ (secondo run: 0 modifiche) |
| Audit event `R18_CLASS_MIGRATION_PREREQ_READY` emesso | ✅ |
| Whitelist admin audit estesa | ✅ |
| Test coverage ≥ 13 test | ✅ (16 test in `backend_round183a_prereq_test.py`) |

---

## 7. Rollback plan (invariato dal R18.2)

Prima dell'apply R18.3 futuro, snapshot obbligatorio:

```python
# Step 1 — Snapshot pre-migration
db.career_history.insert_one({
    "adventurer_id": adv.id,
    "event_type": "r18_migration_snapshot",
    "class_slug_before": adv.class_slug,
    "class_slug_after": migration_map[adv.class_slug],
    "snapshot_at": iso_now,
    "round": "R18.3"
})

# Step 2 — Apply
db.adventurers.update_many(
    {"class_slug": source_slug},
    {"$set": {"class_slug": target_slug,
              "r18_migrated_at": iso_now,
              "r18_migrated_from": source_slug}}
)

# Step 3 — Rollback (emergenza)
db.adventurers.update_many(
    {"r18_migrated_from": {"$exists": True}},
    {"$set": {"class_slug": "$r18_migrated_from"},
     "$unset": {"r18_migrated_at": 1, "r18_migrated_from": 1}}
)
```

**Rollback R18.3a stesso** (se necessario):
```python
# Remove bridged slug from items
db.items.update_many(
    {"recommended_classes": "cacciatore_di_mostri"},
    {"$pull": {"recommended_classes": "cacciatore_di_mostri"}}
)
db.items.update_many(
    {"recommended_classes": "cacciatore_del_vuoto"},
    {"$pull": {"recommended_classes": "cacciatore_del_vuoto"}}
)
# Remove seeded classes (soft: mark is_active=false)
db.adventurer_classes.update_many(
    {"slug": {"$in": ["cacciatore_di_mostri", "cacciatore_del_vuoto"]}},
    {"$set": {"is_active": False}}
)
```

---

## 8. Recommendation: R18.3 apply gate

L'apply reale (spostamento class_slug 303 adv da ranger/warlock → target) non deve avvenire prima di:

1. ✅ **DONE R18.3a**: Seed `cacciatore_di_mostri` + `cacciatore_del_vuoto` in `adventurer_classes`
2. ✅ **DONE R18.3a**: Extension `recommended_classes` per bridge item (49 item totali)
3. ✅ **DONE R18.1.2**: Guard whitelist accetta questi 2 slug
4. ⏳ **R18.3**: Career_history snapshot policy attiva
5. ⏳ **R18.3**: UI banner IT preparato ("La classe Ranger è stata rinominata Cacciatore di Mostri", "La classe Warlock è stata rinominata Cacciatore del Vuoto")
6. ⏳ **R18.3**: Flip flag `is_playable=false → true` + `migration_target_only=true → false` sui 2 slug post apply
7. ⏳ **R18.3** (opzionale): Guild-level opt-in R18 (`r18_beta_opt_in=true`) se preferito rollout graduale

**NON eseguire apply in R18.3a.** Bocciare qualsiasi PR che lo faccia senza brief separato R18.3.

---

## 9. Audit event R18.3a emesso

**Event type**: `R18_CLASS_MIGRATION_PREREQ_READY` · **Idempotent**: sì

**Metadata inserita in `audit_log`**:

```json
{
  "round": "R18.3a",
  "classes_seeded": ["cacciatore_di_mostri", "cacciatore_del_vuoto"],
  "is_playable": false,
  "migration_target_only": true,
  "item_bridge_strategy": "recommended_classes_append_only",
  "item_bridge_counts": {
    "cacciatore_di_mostri": 31,
    "cacciatore_del_vuoto": 18
  },
  "orphans_impacted_estimated": 303,
  "migration_apply": false,
  "dry_run_only": true,
  "slug_correction_from_R18_2": true,
  "corrected_slugs_from_R18_2": {
    "cacciatore_mostri": "cacciatore_di_mostri",
    "cacciatore_vuoto": "cacciatore_del_vuoto"
  }
}
```

---

## Firma

e1 main agent · 2026-07-04 · R18.3a class-migration-prereq COMPLETE · ZERO write on adventurers.
