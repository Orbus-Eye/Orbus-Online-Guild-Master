# ROUND 18.2 — Orphan Migration Plan (DRY-RUN ONLY)

**Round:** R18.2 PILOT · **Data:** 2026-07-04 · **Autore:** e1 main agent
**Status:** DRY-RUN COMPLETO. **NESSUN APPLY.** Apply reale richiede brief PM separato.

**Fonte dry-run**: `/app/backend/app/scripts/round182_orphan_migration_dry_run.py`
**Report JSON**: `/app/memory/round182_orphan_migration_dry_run.json`

---

## 1. Sommario esecutivo

Le 5 classi live orphan (496 adv attivi) sono state analizzate in modalità **read-only**. Zero write op eseguite.

| Source | Target | Type | Actual adv | Delta vs expected | Guilds impact | Item pool target | Rischio |
|---|---|---|---|---|---|---|---|
| priest | paladin | merge_into_existing | **190** | 0 | 175 | 92 | **BASSO** |
| ranger | cacciatore_mostri | migration_to_new_class | **175** | 0 | 175 | **0** | **ALTO** |
| warlock | cacciatore_vuoto | migration_to_new_class | **128** | 0 | 128 | **0** | **ALTO** |
| berserker | warrior | alias_deprecated | **3** | 0 | 3 | 69 | BASSO |
| assassin | rogue | alias_deprecated_zero_migration | **0** | 0 | 0 | 31 | n/a |
| **TOTALE** | | | **496** | 0 | | | |

**Zero adventurer in expedition attiva** al momento del dry-run → migration window sicura.

**Zero adventurer con talent_progress esistente** → coerente con R18.2 PILOT (schema only).

---

## 2. Piano migration per target

### Q1 — priest → paladin (190 adv)
- **Tipo**: merge_into_existing (Paladino esiste già come class_slug=paladin, playable=True)
- **Delta atteso 190 vs actual 190**: ✅ match esatto
- **Impatto**: 190 adv → 175 guilds impattate (avg 1.08 priest/guild)
- **Item pool target `paladin`**: 92 item (BASSO risk)
- **Off-class post-migration**: sample 5 mostra 0 caso di item recommended_for=priest (che finirebbe off-class in paladin). Dettaglio: molti priest hanno equipment weapon/armor generico compatibile paladin. Verifica full richiede audit item.recommended_classes → deferred a R18.3.

### Q2 — ranger → cacciatore_mostri (175 adv)
- **Tipo**: migration_to_new_class (target NON esiste live)
- **⚠️ BLOCKER**: `cacciatore_mostri` NON è nel catalog `adventurer_classes` — serve seed pre-migration
- **⚠️ BLOCKER**: 0 item pool per `cacciatore_mostri` → 175 adv post-migration sarebbero **naked** o con equipment generico
- **Delta 175 vs 175**: ✅ match
- **Pre-requisiti apply futuro**:
  1. Seed `cacciatore_mostri` in `adventurer_classes` (con `is_playable=true`)
  2. Migrare/estendere item pool (marcare item ranger-compatible come `recommended_classes: [ranger, cacciatore_mostri]` per bridge grandfathering)
  3. Warning UI banner: "La classe Ranger è stata rinominata Cacciatore di Mostri"

### Q3 — warlock → cacciatore_vuoto (128 adv)
- **Tipo**: migration_to_new_class (target NON esiste live)
- **⚠️ BLOCKER**: `cacciatore_vuoto` NON è nel catalog
- **⚠️ BLOCKER**: 0 item pool
- **Delta 128 vs 128**: ✅ match
- **Pre-requisiti**: come Q2, replicati

### Q4 — berserker → warrior (3 adv)
- **Tipo**: alias_deprecated (target esiste, class merge)
- **Delta 3 vs 3**: ✅ match
- **Impatto**: 3 adv, low risk. Item pool warrior=69 sufficiente.
- **Metrica extra**: `Via del Dominatore.TXT` da R18.0b conferma questa classe come ramo talento del Guerriero.

### Q5 — assassin → rogue (0 adv)
- **Tipo**: alias_deprecated_zero_migration
- **Delta 0 vs 0**: ✅ match, nessuna migration necessaria
- **Azione**: solo deprecare il class_slug=assassin nel catalog (marker `is_deprecated=true` o rimozione)

---

## 3. Impact matrix

### Guilds impattate
- **175 guilds** con almeno un priest (target paladin merge, non-breaking)
- **175 guilds** con almeno un ranger (target cacciatore_mostri, breaking senza pre-seed)
- **128 guilds** con almeno un warlock (target cacciatore_vuoto, breaking senza pre-seed)
- **3 guilds** con berserker
- **0 guilds** con assassin

### Adventurer in expedition attiva
- **0/496** → migration window sicura

### Adventurer con talent_progress
- **0/496** → schema R18.2 PILOT non ancora populato → nessun conflitto

### Rischio player-facing
- **priest → paladino**: nome cambia da "Sacerdote" a "Paladino". Banner UI necessario in fase apply.
- **ranger → Cacciatore di Mostri**: cambio nome + potenzialmente classe naked (0 item). Banner + free-retrain window suggerita.
- **warlock → Cacciatore del Vuoto**: idem sopra.
- **berserker → warrior**: 3 adv, communication one-shot.

---

## 4. Rollback plan

Prima dell'apply futuro, snapshot obbligatorio:

**Step 1 — Snapshot pre-migration**:
```python
# For each adventurer in migration set:
db.career_history.insert_one({
    "adventurer_id": adv.id,
    "event_type": "r18_migration_snapshot",
    "class_slug_before": adv.class_slug,
    "class_slug_after": migration_map[adv.class_slug],
    "snapshot_at": datetime.now(timezone.utc).isoformat(),
    "round": "R18.3"  # or when apply happens
})
```

**Step 2 — Apply**:
```python
db.adventurers.update_many(
    {"class_slug": source_slug},
    {"$set": {
        "class_slug": target_slug,
        "r18_migrated_at": iso_now,
        "r18_migrated_from": source_slug
    }}
)
```

**Step 3 — Rollback (emergenza)**:
```python
# Reset from field snapshot
async for adv in db.adventurers.find({"r18_migrated_from": {"$exists": True}}):
    db.adventurers.update_one(
        {"id": adv["id"]},
        {"$set": {"class_slug": adv["r18_migrated_from"]},
         "$unset": {"r18_migrated_at": 1, "r18_migrated_from": 1}}
    )
```

---

## 5. Rischi tecnici

### **ALTO** — Item pool ZERO per cacciatore_mostri + cacciatore_vuoto
- 303 adv (175+128) post-migration senza item class-compatible
- Grandfathering necessario: marcare item ranger-tagged come compatible con cacciatore_mostri (bridge)
- Alternative: soft class-bound R18.4 SOFT dovrebbe partire DOPO apply migration + seed item

### **ALTO** — Target class doc missing
- `cacciatore_mostri` e `cacciatore_vuoto` NON esistono in `adventurer_classes`
- Il guard R18.1.1 expedition (deny recruit_unassigned + is_playable=false + not in catalog) **bloccherebbe** 303 adv post-migration se il seed non precede la migration
- **Fix pre-migration**: `db.adventurer_classes.insert_many([{slug: cacciatore_mostri, name_it: "Cacciatore di Mostri", is_playable: True, ...}, ...])`

### **MEDIO** — Player-facing name change
- Priest (Sacerdote) → Paladino: fantasy shift moderato
- Ranger → Cacciatore di Mostri: fantasy shift alto
- Serve banner UI + IT messaggio comunicazione one-shot in fase apply

### **BASSO** — R17 legacy fields
- Alcuni priest hanno `legacy_class_original=Cleric` (post R18.1 alias). Preservare o clean-up?
- **Suggerimento**: preservare, aggiungere `legacy_class_hop_2=priest` in career_history

---

## 6. Recommendation: R18.3 apply gate

L'apply reale non deve avvenire prima di:
1. ✅ Seed `cacciatore_mostri` + `cacciatore_vuoto` in `adventurer_classes`
2. ✅ Extension `recommended_classes` per bridge item (ranger→[ranger, cacciatore_mostri])
3. ✅ Career_history snapshot policy attiva
4. ✅ UI banner IT preparato
5. ✅ Guild-level opt-in R18 (`r18_beta_opt_in=true`) — se preferito flow graduale

**NON eseguire apply in R18.2 PILOT.** Bocciare qualsiasi PR che lo faccia senza brief separato.

---

## Firma

e1 main agent · 2026-07-04 · R18.2 orphan migration DRY-RUN complete · ZERO write.
