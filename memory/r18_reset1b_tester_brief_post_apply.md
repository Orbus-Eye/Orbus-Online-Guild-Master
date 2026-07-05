# R18.Reset.1b — Tester Brief Post-Apply

**Round**: R18.Reset.1b post-apply verification
**Autore**: e1 main agent (preparato in fase planning, da usare DOPO apply reale)
**Target**: `e1_tester`
**Lingua**: IT (raccomandazione: rispondere in italiano)

⚠️ Questo brief deve essere invocato **solo dopo** che il PM ha dato OK esplicito e l'apply script è stato eseguito con `--apply --i-understand-this-will-reset-all-guilds`.

---

## Prerequisiti di esecuzione tester

Prima di iniziare i test:
1. Verifica esistenza directory backup: `/app/backend/backups/r18_reset1b_<timestamp>/manifest.json`
2. Verifica esistenza almeno 1 audit event `R18_FULL_GUILD_FRESH_START_APPLIED` in `audit_log`
3. Backend hot-reload post-apply (nessuna azione: hot-reload automatico)

---

## Test cases (12 totali)

### T01 — Guild Identity Preservation

**Obiettivo**: verificare che `name`, `owner_user_id`, `created_at` di ogni guild siano intatti post-apply.

**Query**:
```python
n_guilds = await db.guilds.count_documents({})
n_with_name = await db.guilds.count_documents({"name": {"$exists": True, "$ne": None, "$ne": ""}})
n_with_owner = await db.guilds.count_documents({"owner_user_id": {"$exists": True, "$ne": None}})
n_with_created_at = await db.guilds.count_documents({"created_at": {"$exists": True}})
```

**Assertion**:
- `n_guilds == 672`
- `n_with_name == 672` (100%)
- `n_with_owner == 672` (100%)
- `n_with_created_at == 672` (100%)

**Fail se**: qualsiasi count diverso.

---

### T02 — Starter Roster Regen: 5 adv per guild

**Obiettivo**: ogni guild ha esattamente 5 adventurers con flag `r18_reset1b_starter=True`.

**Query**:
```python
pipeline = [
    {"$match": {"r18_reset1b_starter": True}},
    {"$group": {"_id": "$guild_id", "n": {"$sum": 1}}},
]
async for r in db.adventurers.aggregate(pipeline):
    assert r["n"] == 5, f"guild {r['_id']} has {r['n']} starter adv"

total_starter = await db.adventurers.count_documents({"r18_reset1b_starter": True})
```

**Assertion**:
- Ogni gruppo per `guild_id` ha `n == 5`
- `total_starter == 672 * 5 == 3360`
- Nessuna guild con starter count != 5

**Fail se**: gruppi con count != 5 o total != 3360.

---

### T03 — Starter Adventurers: solo classi safe

**Obiettivo**: tutte le classi degli adv starter sono in `SAFE_STARTER_SLUGS` (11 legacy) e nessuna in blacklist.

**Query**:
```python
safe = {"alchemist", "bard", "druid", "mage", "monk", "paladin",
        "priest", "ranger", "rogue", "warlock", "warrior"}
blacklist = {"cacciatore_di_mostri", "cacciatore_del_vuoto"}
distinct_slugs = await db.adventurers.distinct(
    "class_slug", {"r18_reset1b_starter": True}
)
```

**Assertion**:
- `set(distinct_slugs).issubset(safe)` — subset del safe pool
- `not (set(distinct_slugs) & blacklist)` — intersection blacklist vuota

**Fail se**: qualsiasi slug fuori dal safe pool o dentro la blacklist.

---

### T04 — Starter Kit Inventory: 3 potions per guild

**Obiettivo**: ogni guild ha 3 doc in `inventory_items` con `item_slug=minor_healing_potion, r18_reset1b_starter_kit=True`.

**Query**:
```python
pipeline = [
    {"$match": {"r18_reset1b_starter_kit": True,
                "item_slug": "minor_healing_potion"}},
    {"$group": {"_id": "$guild_id", "n": {"$sum": 1}}},
]
```

**Assertion**:
- Ogni gruppo ha `n == 3`
- Total = 672 * 3 = **2016** doc

**Fallback tolerance**: se `minor_healing_potion` non era presente nel catalog al momento dell'apply (edge case improbabile), il fallback defensivo skippa la creazione potions. In quel caso il test T04 deve verificare:
- `total_starter_kit == 0` (nessuna potion creata)
- Log backend contiene WARN `item minor_healing_potion non trovato nel catalog`
- Test T04 passa con status "SKIPPED (fallback defensive)"

**Fail se**: total non è 2016 e fallback log non presente.

---

### T05 — Gold totale post = 67.200

**Obiettivo**: la somma dei `gold` di tutte le 672 guild è esattamente **67.200** (672 × 100).

**Query**:
```python
pipeline = [{"$group": {"_id": None, "total": {"$sum": "$gold"}}}]
total = 0
async for r in db.guilds.aggregate(pipeline):
    total = r["total"]
```

**Assertion**:
- `total == 67_200`

**Fail se**: total != 67200.

---

### T06 — Archive Integrity

**Obiettivo**: le sibling `_r18_archive` contengono esattamente i doc archiviati.

**Query**:
```python
assertions = {
    "adventurers_r18_archive": 3314,       # da R18.Reset.1a snapshot
    "inventory_items_r18_archive": 111,
    "equipped_items_r18_archive": 20,
    "achievement_progress_r18_archive": 1686,
    "pvp_cosmetics_unlocked_r18_archive": 5,
    "guild_mount_ownership_r18_archive": 2,
    "narrative_rewards_unlocked_r18_archive": 1,
}
for coll, expected in assertions.items():
    n = await db[coll].count_documents({})
    assert n == expected, f"{coll}: expected {expected}, got {n}"
```

**Assertion**: ogni count matcha con tolleranza ±5% (per test data creation nel windows).

**Fail se**: mismatch > 5%.

---

### T07 — Zero cosmetici live post-apply

**Obiettivo**: nessun cosmetico earned resta player-facing.

**Query**:
```python
n_pvp = await db.pvp_cosmetics_unlocked.count_documents({})
n_mount = await db.guild_mount_ownership.count_documents({})
n_narr = await db.narrative_rewards_unlocked.count_documents({})
```

**Assertion**:
- `n_pvp == 0`
- `n_mount == 0`
- `n_narr == 0`

**Fail se**: qualsiasi count > 0.

---

### T08 — Banner R18.3c suppress

**Obiettivo**: `guilds.migration_banner_r18_3c_dismissed == True` per tutte le 672 guild.

**Query**:
```python
n_dismissed = await db.guilds.count_documents(
    {"migration_banner_r18_3c_dismissed": True}
)
```

**Assertion**:
- `n_dismissed == 672`

**Alternative endpoint check (integration test)**:
Con JWT tester valido, chiamare `GET /api/guilds/me/migration-banner` → response deve essere `{banner: null}` o `{show: false}` per almeno 1 guild campione.

**Fail se**: n_dismissed != 672 o endpoint restituisce banner attivo.

---

### T09 — Banner P2-a `r18_reset1b_banner_dismissed=False`

**Obiettivo**: il nuovo banner welcome ha flag `False` per tutte le 672 (mostra al prossimo login).

**Query**:
```python
n_pending = await db.guilds.count_documents(
    {"r18_reset1b_banner_dismissed": False}
)
```

**Assertion**:
- `n_pending == 672` (banner ancora da mostrare a tutte)

**Fail se**: n_pending != 672.

---

### T10 — Audit event singolo

**Obiettivo**: esattamente 1 evento `R18_FULL_GUILD_FRESH_START_APPLIED` con metadata completa.

**Query**:
```python
n_apply = await db.audit_log.count_documents(
    {"event_type": "R18_FULL_GUILD_FRESH_START_APPLIED"}
)
doc = await db.audit_log.find_one(
    {"event_type": "R18_FULL_GUILD_FRESH_START_APPLIED"},
    {"_id": 0}
)
meta = doc.get("metadata", {})
```

**Assertion**:
- `n_apply == 1`
- `meta.get("round") == "R18.Reset.1b"`
- `meta.get("mode") == "APPLY"`
- `meta.get("pm_decisions_applied") is not None`
- `meta.get("summary") is not None`

**Fail se**: count != 1 o metadata incompleta.

---

### T11 — seed_round5 warning verification

**Obiettivo**: verificare se il warning `seed_round5.starter_backfill failed: 'base_strength'` persiste post-apply.

**Metodo**:
```bash
tail -n 200 /var/log/supervisor/backend.err.log | grep "seed_round5.*starter backfill failed"
```

**Assertion**:
- Se **0 righe match** → warning risolto by construction (T11 PASS)
- Se **≥ 1 riga match** → warning persiste. T11 FAIL con action item:
  > Aprire `R18.3a.3` hotfix: patch simmetrica a R18.3a.2 in `seed_round5.py` (aggiungere filter `is_playable != False` al pool internal).

**Nota**: T11 FAIL non è un blocker apply (l'apply è comunque completo). È un promemoria per un round successivo.

---

### T12 — Idempotency + Rollback dry-run

**Obiettivo**:
- (a) Un secondo run di apply deve rifiutare con exit=2
- (b) Rollback script deve eseguire in dry-run senza errori

**Metodo**:
```bash
# T12.a — idempotency
cd /app/backend && python -m app.scripts.round18_reset1b_apply --apply --i-understand-this-will-reset-all-guilds
echo "exit code: $?"

# T12.b — rollback dry-run
cd /app/backend && python -m app.scripts.round18_reset1b_rollback
echo "exit code: $?"
```

**Assertion**:
- T12.a: exit code == **2** + stdout contiene `"already present"` o `"Rifiuto re-apply"`
- T12.b: exit code == **0** + stdout contiene `"MODE = DRY_RUN"` + `"DONE"`

**Fail se**: exit code diverso o messaggi mancanti.

---

## Sintesi assertion counts

| Test | Assertion critica | Passing count expected |
|---|---|---:|
| T01 | Guild identity | 672 |
| T02 | 5 adv per guild | 672 gruppi × 5 = 3360 total |
| T03 | Slug safe subset | 11 slug max, 0 blacklist |
| T04 | 3 potions per guild | 672 × 3 = 2016 total |
| T05 | Gold sum | 67.200 |
| T06 | Archive integrity | ~5400 doc archiviati |
| T07 | Zero cosmetici live | 0 |
| T08 | Banner R18.3c suppress | 672 |
| T09 | Banner P2-a pending | 672 |
| T10 | Audit event singolo | 1 |
| T11 | seed_round5 warning | 0 (o R18.3a.3 pending) |
| T12 | Idempotency+rollback dry | exit 2 + exit 0 |

## Test report expected structure

```json
{
  "round": "R18.Reset.1b post-apply",
  "computed_at": "<ISO>",
  "summary": {"passed": 12, "failed": 0, "skipped": 0},
  "tests": [
    {"id": "T01", "status": "PASS|FAIL|SKIPPED", "details": "..."},
    ...
  ],
  "action_items_for_main_agent": [
    "if T11 FAIL: open R18.3a.3 hotfix",
    "if T04 SKIPPED: verify potion slug in catalog before next apply",
    ...
  ]
}
```

## Non-blocker notes

- **Test data drift**: durante il window di test, agent test possono creare guild sintetiche. Le assertion T02, T04, T05 hanno tolleranza implicita ±5% per questo.
- **Rollback test in produzione**: T12.b è **dry-run only**. Non eseguire mai `--confirm-rollback` in questo brief. Il rollback reale richiede nuovo brief PM.
- **Warning seed_round5**: T11 FAIL è un follow-up, non un blocker.

## Non-goal

- ❌ Non testare UI banner (non implementato in R18.Reset.1b)
- ❌ Non testare compensation cosmetica (deferrita a R18.Reset.2)
- ❌ Non testare R18.3d mapping registry (PAUSED)
- ❌ Non testare drift R18.1 (HOLD)

## Firma

*Tester brief preparato in fase planning R18.Reset.1b · 2026-07-05T07:10Z*

Da invocare da `e1_tester` **dopo** che il PM ha autorizzato ed eseguito l'apply reale.
