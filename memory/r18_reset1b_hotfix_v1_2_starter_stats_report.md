# R18.Reset.1b.hotfix.v1_2 — Starter Roster Stat Generation Fix — REPORT

**Data**: 2026-07-05T13:10Z
**Autore**: e1 main agent
**Stato**: **IMPLEMENTATO — DRY-RUN OK — TEST SUITE 16/16 PASS — SEALED 6/6 INTATTI — STOP per staged GO PM**

---

## 1. Riepilogo decisioni PM applicate

| PM Q | Decisione | Implementazione |
|---|---|---|
| **Q1** | NO variance, `base_*` esatta da `adventurer_classes` | `_preload_class_base_stats` + `_regen_starter_roster` linee 366–386 di `round18_reset1b_apply_v1_2.py`. Fail-fast HARD STOP se classe safe manca `base_*`. |
| **Q2** | Doppio audit `APPLIED` + `APPLIED_V1_2`, skip V1_1 | `_emit_audit_events` linee 512–586. Metadata minima obbligatoria: `round`, `apply_script`, `apply_version="v1.2"`, `starter_kit_fix=true`, `starter_roster_stats_fix=true`, `stat_strategy="base_stats_exact_no_variance"`, `inventory_unique_index_respected=true`, `http_maintenance_required=true`, `internal_job_freeze_required=true`. |
| **Q3** | Guard intelligente: blocca solo apply attivo/non-rollbackato | `_apply_state_check` linee 199–307. 5 controlli: (1) `guilds` con `r18_reset1b_applied=true` >0, (2) `APPLIED_V1_2` senza rollback successivo, (3) `APPLIED` legacy con `metadata.apply_version=v1.2` senza rollback, (4) ambiguità metadata >0 rispetto rollback → **HARD STOP** no bypass silenzioso, (5) altrimenti PASS. |

---

## 2. Diff logico rispetto a v1.1

### V2.F1 — `_regen_starter_roster` (NUOVO)
```python
# v1.2: preload class base_* stats (fail-fast)
class_templates = await _preload_class_base_stats(db)
# HARD STOP se anche 1 classe safe manca base_* → RuntimeError

# In loop di generazione:
for i, class_slug in enumerate(picks):
    stats = class_templates[class_slug]  # KeyError impossibile qui
    docs_to_create.append({
        ...
        "strength": stats["strength"],   # V2.F1 nuovi 5 stat
        "agility": stats["agility"],
        "intellect": stats["intellect"],
        "endurance": stats["endurance"],
        "faith": stats["faith"],
        ...
        "r18_reset1b_stat_source":
            "adventurer_classes.base_*_catalog_lookup",
    })
```

### V2.F3 — Audit event (evento V1_2 non V1_1)
```python
AUDIT_EVENT_APPLIED = "R18_FULL_GUILD_FRESH_START_APPLIED"
AUDIT_EVENT_APPLIED_V1_2 = "R18_FULL_GUILD_FRESH_START_APPLIED_V1_2"
# Il vecchio APPLIED_V1_1 non è più emesso.
# Metadata `supersedes_versions=["v1.0_original", "v1.1_hotfix"]`.
```

### V2.F4 — Idempotency guard (5 controlli intelligenti)
```python
# Prima v1.1: guard = "any APPLIED event esistente → BLOCK"
# Ora v1.2: guard = 5 controlli distinguono active vs rollbackato
async def _apply_state_check(db):
    # (1) guilds.r18_reset1b_applied=true > 0 → BLOCK
    # (2) APPLIED_V1_2 senza rollback successivo → BLOCK
    # (3) legacy APPLIED con metadata.apply_version=v1.2 → BLOCK
    # (4) ambiguous_apply_events_no_version > rollback → HARD STOP
    # (5) altrimenti pass (storico v1.1 rollbackato OK)
```

### V2.F5 — Starter kit fix v1.1 MANTENUTO
Il fix F1 v1.1 (1 doc per `(guild_id, item_id)` con upsert `$setOnInsert`, quantity=STARTER_KIT_POTIONS=3) è **preservato invariato** nella funzione `_regen_starter_kit` (linee 429–503).

### V2.F6 — Backup path prefix
`/app/backend/backups/r18_reset1b_v1_2_<UTC-ISO>/` (invece di `r18_reset1b_v1_1_`).

### V2.F7 — Zero altre modifiche
`_archive_collections`, `_wipe_live_collections`, `_reset_guild_fields`, `_backup_snapshot`, `_verify_double_freeze` invariati vs v1.1.

---

## 3. Output DRY-RUN eseguito (su DB live, zero write)

```
[INFO] ====== R18.Reset.1b.hotfix.v1_2 START (mode=DRY_RUN) ======
[INFO] [preload] loading adventurer_classes base_* templates...
[INFO] [preload] 11/11 classi safe caricate con tutti i 5 base_* stats. OK.
[INFO] [backup] DRY_RUN: skipping backup snapshot creation.
[INFO] [archive] DRY_RUN: adventurers (3380 docs) -> adventurers_r18_archive
[INFO] [archive] DRY_RUN: inventory_items (111 docs) -> ...
... 32 collections ...
[INFO] [wipe] DRY_RUN: would wipe adventurers (3380 docs)
... 32 collections ...
[INFO] [reset_guilds] DRY_RUN: would update_many 672 guilds
[INFO] [regen_roster] mode=DRY_RUN guilds=672 total_adv_created=0
              stat_strategy=base_stats_exact_no_variance
[INFO] [regen_kit] DRY_RUN: would create 672 inventory_items
              (1 doc × 672 guilds, quantity=3, item_id=fd5cbdef-3146-...)
[INFO] [audit] DRY_RUN: would emit BOTH
       R18_FULL_GUILD_FRESH_START_APPLIED and
       R18_FULL_GUILD_FRESH_START_APPLIED_V1_2 with shared metadata
[INFO] ====== R18.Reset.1b.hotfix.v1_2 DONE (mode=DRY_RUN) ======
```

**Sample adv generato in DRY_RUN** (classe rogue, stats da catalog):
```json
{
  "id": "5328ddc5-6e4f-4386-a709-6afd50610b81",
  "guild_id": "57ae4e07-7fbe-44f2-b297-f5c0f42f6540",
  "class_slug": "rogue",
  "name": "Starter 1",
  "strength": 5, "agility": 9, "intellect": 3,
  "endurance": 4, "faith": 2,
  "hp_current": 100, "hp_max": 100,
  "r18_reset1b_hotfix_v1_2": true,
  "r18_reset1b_stat_source": "adventurer_classes.base_*_catalog_lookup"
}
```

Confronto con catalog live `adventurer_classes.slug=rogue`: `base_strength=5, base_agility=9, base_intellect=3, base_endurance=4, base_faith=2` → **MATCH ESATTO** (no variance, PM Q1 rispettato).

**Log completo**: `/app/memory/r18_reset1b_v1_2_dry_run_log.txt`

---

## 4. Test suite result — **16/16 PASS** ✅

```
tests/backend_round1b_hotfix_v1_2_starter_stats_test.py
  t01_sealed_scripts_untouched                  PASSED
  t02_v1_2_exists_as_sibling                    PASSED
  t03_all_11_safe_classes_have_base_stats       PASSED
  t04_dry_run_roster_5_stats_100_percent        PASSED
  t05_no_adv_null_stat                          PASSED
  t06_dry_run_kit_produces_expected_docs        PASSED
  t07_no_item_id_null                           PASSED
  t08_no_duplicate_key                          PASSED
  t09_guard_does_not_block_for_rolled_back_v1_1 PASSED  ← Q3 verified
  t10_guard_blocks_for_active_v1_2              PASSED  ← Q3 verified
  t11_double_audit_only_on_success              PASSED  ← Q2 verified
  t12_get_adventurers_schema_stat_safe          PASSED  ← 500 fix
  t13_get_dungeons_schema_stat_safe             PASSED  ← 500 fix
  t14_post_expeditions_no_keyerror_stat         PASSED  ← 500 fix
  t15_dry_run_no_db_writes                      PASSED
  t16_hard_stop_if_class_missing_base_stat      PASSED  ← Q1 fail-fast

Isolation: DB test = test_orbus_r18_hotfix_v1_2_<pid> (drop teardown)
Zero contatto con orbus_r16 / orbus_r16_test primari.
```

**Full regression** (Hotfix v1.1 + Write_Freeze_Full + v1.2 = **39/39 PASS**):
```bash
cd /app/backend && python -m pytest \
  tests/backend_round1b_hotfix_starter_kit_test.py \
  tests/backend_round1b_write_freeze_full_test.py \
  tests/backend_round1b_hotfix_v1_2_starter_stats_test.py -v
```

---

## 5. Sealed integrity check — **6/6 INTATTI** ✅

| Script | Baseline sha256 | Post-implementation | Result |
|---|---|---|---|
| `round18_reset1b_apply.py` (v1.0) | `657d5853a5b20300...` | `657d5853a5b20300...` | ✅ OK |
| `round18_reset1b_apply_v1_1.py` | `14d38bf8ea66c878...` | `14d38bf8ea66c878...` | ✅ OK |
| `round18_reset1c_restore_from_jsonl_manifest.py` | `453b87c8a83e303e...` | `453b87c8a83e303e...` | ✅ OK |
| `round18_reset1c_field_cleanup.py` | `fe2d39bf1a2a1189...` | `fe2d39bf1a2a1189...` | ✅ OK |
| `round18_reset1b_staged_backup_materialize.py` | `db42665587dc7a18...` | `db42665587dc7a18...` | ✅ OK |
| `app/core/job_freeze.py` | `487c9223532c3016...` | `487c9223532c3016...` | ✅ OK |

**ALL_MATCH_6_SEALED: True**. Nessuno script sealed toccato durante l'implementazione v1.2.

Baseline snapshot preservato in `/app/memory/r18_reset1b_hotfix_v1_2_preflight.json`.

---

## 6. Deliverable

| File | Path | Status |
|---|---|---|
| Script v1.2 sibling | `/app/backend/app/scripts/round18_reset1b_apply_v1_2.py` | **NUOVO** (~690 righe), NOT SEALED yet |
| Test suite | `/app/backend/tests/backend_round1b_hotfix_v1_2_starter_stats_test.py` | **NUOVO** (16 test, ~490 righe) |
| Preflight baseline | `/app/memory/r18_reset1b_hotfix_v1_2_preflight.json` | **NUOVO** |
| Dry-run log | `/app/memory/r18_reset1b_v1_2_dry_run_log.txt` | **NUOVO** |
| Questo report | `/app/memory/r18_reset1b_hotfix_v1_2_starter_stats_report.md` | **NUOVO** |

---

## 7. Vincoli rispettati

- ✅ ZERO modifica script sealed (6/6 verificato pre/post via sha256+mtime)
- ✅ ZERO apply reale eseguito (solo dry-run)
- ✅ ZERO DB write intenzionale (dry-run mode + test DB isolato)
- ✅ ZERO patch a `seed_round5`, R18.1.3, R18.3d, R18.X, SMTP
- ✅ ZERO hard delete
- ✅ v1.2 creato come **sibling** (non patch), stesso pattern v1.1 vs v1.0 sealed
- ✅ Doppio freeze prerequisite check integrato (`_verify_double_freeze` linee 315–325)
- ✅ Idempotency guard NON silent bypass (HARD STOP su stato ambiguo)

---

## 8. Open questions per PM (rimanenti)

Nessuna. Le 3 open questions del brief v1.2 sono state risolte dal PM prima di questa implementazione e applicate come specificato.

---

## 9. Gate finale

**🛑 STOP — Nessun apply reale eseguito. In attesa nuovo staged GO PM.**

Sequenza per l'apply reale v1.2 (SOLO dopo tuo GO esplicito):

1. **Attivare doppio freeze**:
   ```bash
   touch /tmp/orbus_maintenance.flag
   touch /tmp/orbus_internal_job_freeze.flag
   ```
2. **Verificare stato pulito**:
   - `guilds` con `r18_reset1b_applied=true`: **0** (verificato dopo cleanup 2026-07-05T12:05Z) ✅
   - Nessun `APPLIED_V1_2` event esistente ✅
3. **Staged pre-apply verify** (opzionale, come per v1.1 apply): materialize backup con helper sealed
4. **Comando apply reale**:
   ```bash
   cd /app/backend && python -m app.scripts.round18_reset1b_apply_v1_2 \
     --apply --i-understand-this-will-reset-all-guilds \
     2>&1 | tee /app/memory/r18_reset1b_v1_2_real_apply_log.txt
   ```

---

**Fine report.**
