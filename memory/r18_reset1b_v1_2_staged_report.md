# R18.Reset.1b.hotfix.v1_2 — STAGED APPLY Report (Step 1-5)

**Data report**: 2026-07-05T13:26:30Z UTC
**Autore**: e1_dev (agente AI)
**Direttiva PM**: STAGED APPLY v1.2 — Step 1-5 SOLO (nessun `--apply` reale)
**UTC_TS staged bundle**: `20260705T132515Z`

---

## Carry-over da sessione precedente (Step 0-1 già eseguiti)

Le seguenti evidenze persistite sono state verificate all'apertura di questa sessione
e usate come baseline immutabile:

- **Step 0 (SEAL v1.2)**:
  - File sigillato: `/app/backend/app/scripts/round18_reset1b_apply_v1_2.py`
  - sealed_at = `2026-07-05T13:15:00Z`
  - sealed_by = `PM_authorization`
  - Preflight snapshot: `/app/memory/r18_reset1b_hotfix_v1_2_preflight.json`
    (dimensione 1211 byte, mtime `2026-07-05T13:21`, 7 file elencati)

- **Step 1 (Snapshot BEFORE + Double Freeze)**:
  - Snapshot BEFORE: `/app/memory/r18_reset1b_v1_2_staged_db_snapshot_before.json`
    (at = `2026-07-05T13:16:00Z`)
  - Freeze flags (creati Jul 5 13:21):
    - `/tmp/orbus_maintenance.flag` (presente)
    - `/tmp/orbus_internal_job_freeze.flag` (presente)

---

## Report 15 punti — struttura v1.2

### 1. manifest path
```
/app/backend/backups/r18_reset1b_v1_2_staged_20260705T132515Z/manifest.json
```
Backup root:
`/app/backend/backups/r18_reset1b_v1_2_staged_20260705T132515Z/`
Contenuto: 33 file `.jsonl` (32 collezioni archiviabili + `guilds`) + `manifest.json`.
Dimensione totale: **5.7 MB**.

### 2. sha256 verification result
- **PASS** — verifica riga-per-riga eseguita da
  `round18_reset1b_staged_backup_materialize.py` (SEALED,
  sha256=`db42665587dc7a18d416e54eebedaa87fb9cf256dd0d43a868db43a1761a7dd9`).
- File verificati: **33**
- Righe totali hashate: **8501**
- Output test log:
  `/app/memory/r18_reset1b_v1_2_staged_materialize_log.txt`

### 3. guild count snapshot-at-apply
- Guilds attive al momento della lettura Step 2 (dry-run v1.2): **672**
- Guilds nel backup materializzato Step 3: **672 docs** su
  `guilds.jsonl` (invariante)
- Baseline Step 1 BEFORE: `guilds = 672`

### 4. adventurers da archiviare
- Adventurers live pre-apply: **3415 docs**
- Destinazione (in caso di REAL apply): `adventurers_r18_archive` via
  aggregate `$out` (append-only)
- Backup materializzato in `adventurers.jsonl` (3.1 MB, 3415 righe)

### 5. starter roster expected count (post REAL apply)
- Formula: `guild_count × 5` = **672 × 5 = 3360 adventurers**
- Strategia stat: `base_stats_exact_no_variance` (**PM Q1 confermato**)
- Classi safe usate: 11 (alchemist, bard, druid, mage, monk, paladin,
  priest, ranger, rogue, warlock, warrior)
- Preload: `[preload] 11/11 classi safe caricate con tutti i 5 base_*
  stats. OK.`
- Campione dry-run (guild `57ae4e07…f6540`, class `rogue`,
  `Starter 1`): `strength=5, agility=9, intellect=3, endurance=4,
  faith=2` — coerente con template `rogue` di
  `adventurer_classes.base_*_catalog_lookup`.

### 6. inventory kit expected (post REAL apply)
- Formato: 1 doc per gilda × 672 gilds = **672 inventory_items docs**
- `quantity` per doc: **3**
- `item_id` risolto (dry-run): **`fd5cbdef-3146-483c-b1fd-217b4da0a59d`**
  (minor_healing_potion)
- Vincolo indice unico `inv_guild_item_unique` su `{guild_id, item_id}`
  sarà rispettato (nessun doc duplicato per stessa gilda+item).

### 7. gold delta expected (in REAL apply, non in staged)
- Costante script: `STARTER_KIT_GOLD = 100`
- `gold_total_after` (post REAL apply, formula linea 790) =
  `guild_count × STARTER_KIT_GOLD` = `672 × 100` = **67,200**
- `gold_total_before` (Step 1 BEFORE) = **4,083,643**
- **Delta atteso in REAL apply**: `67,200 − 4,083,643 = −4,016,443`
- **Delta osservato in STAGED (Step 4)**: **0** (nessuna scrittura,
  invariato)

### 8. minor_healing_potion item_id resolved
- `item_id = fd5cbdef-3146-483c-b1fd-217b4da0a59d`
- Fonte: catalogo `items` (178 doc), risolto tramite lookup slug
  `minor_healing_potion` all'interno di `regen_kit`.
- Nessun fallback usato.

### 9. HTTP maintenance verification
- Flag file: `/tmp/orbus_maintenance.flag` — **PRESENTE**
  (dimensione 0B, mtime Jul 5 13:21)
- Test funzionale via preview URL
  (`https://drain-dispatch.preview.emergentagent.com`):
  - `GET  /api/health` → **HTTP 200** `{"status":"ok","env":"development"}`
  - `POST /api/auth/login` (payload valido) → **HTTP 503**
    `{"detail":"Orbus è temporaneamente in manutenzione. Riprova tra
    poco."}`
- Middleware `MaintenanceMiddleware` correttamente attivo:
  whitelist GET su `/api/health` + `/api/openapi.json`, block su
  scritture. Log backend conferma 503 su `POST/PUT/PATCH/DELETE
  /api/auth/login`.

### 10. internal job freeze verification
- Flag file: `/tmp/orbus_internal_job_freeze.flag` — **PRESENTE**
- Wrapper `job_freeze.py` (SEALED,
  sha256=`487c9223532c30165ef1bdba86bdc33976c4d82b7801e8509c6dd3dfa17311be`).
- Evidenza dai log di boot backend (2026-07-05 13:25:45):
  ```
  orbus.job_freeze - WARNING - Internal job skipped due to
    ORBUS_INTERNAL_JOB_FREEZE — job=orbus.inventory.backfill_bound_fields_if_missing
  orbus.job_freeze - WARNING - Internal job skipped due to
    ORBUS_INTERNAL_JOB_FREEZE — job=orbus.training.backfill_missing_signature_inventory_rows
  ```
- Entrambi i job async che bypassano HTTP sono correttamente skippati
  dal freeze interno.

### 11. dry-run v1.2 exit status
- Comando: `python -m app.scripts.round18_reset1b_apply_v1_2 --dry-run`
- **Exit code: 0**
- Log: `/app/memory/r18_reset1b_v1_2_staged_dry_run_log.txt`
  (11 798 byte)
- Highlights:
  - `MODE = DRY_RUN. Nessuna scrittura sara' effettuata.`
  - Preload classi: 11/11 OK
  - Archive: 32 collezioni pianificate ($out)
  - Wipe: 32 collezioni pianificate (delete_many)
  - Reset guilds: `would update_many 672 guilds`
  - Roster: `stat_strategy=base_stats_exact_no_variance` (PM Q1)
  - Audit: `would emit BOTH R18_FULL_GUILD_FRESH_START_APPLIED and
    R18_FULL_GUILD_FRESH_START_APPLIED_V1_2 with shared metadata`
    (PM Q4: doppio evento confermato)
  - Nessun warning bloccante.

### 12. DB snapshot before/after staged invariato
- BEFORE: `/app/memory/r18_reset1b_v1_2_staged_db_snapshot_before.json`
  (Step 1, `at=2026-07-05T13:16:00Z`)
- AFTER (Step 4):
  `/app/memory/r18_reset1b_v1_2_staged_db_snapshot_after.json`
  (`at=2026-07-05T13:26:17.860533Z`)

| Collezione        | BEFORE  | AFTER   | DELTA | Stato |
|-------------------|--------:|--------:|------:|:-----:|
| guilds            |     672 |     672 |    +0 | OK    |
| adventurers       |    3415 |    3415 |    +0 | OK    |
| inventory_items   |     111 |     111 |    +0 | OK    |
| items             |     178 |     178 |    +0 | OK    |
| expeditions       |      17 |      17 |    +0 | OK    |
| raids             |       1 |       1 |    +0 | OK    |
| audit_log         |   11831 |   11831 |    +0 | OK    |
| users             |     340 |     340 |    +0 | OK    |
| **gold_total**    | 4083643 | 4083643 |    +0 | OK    |

**RESULT: PASS** — DB invariance mantenuta (delta=0 su tutte le 8
collezioni tracciate + gold_total). Log:
`/app/memory/r18_reset1b_v1_2_staged_invariance_check_log.txt`.

Verifica idempotenza audit: `R18_FULL_GUILD_FRESH_START_APPLIED_V1_2`
count = **0** (nessun apply reale eseguito). Anche
`R18_FULL_GUILD_FRESH_START_APPLIED` = 0 (post-rollback pulito).

### 13. sealed scripts integrity invariata (7 sigilli totali)
Verifica esplicita SHA256 + mtime contro
`/app/memory/r18_reset1b_hotfix_v1_2_preflight.json`:

| # | file                                                       | sha256 | mtime |
|--:|:-----------------------------------------------------------|:------:|:-----:|
| 1 | `app/scripts/round18_reset1b_apply.py`                     | OK     | OK    |
| 2 | `app/scripts/round18_reset1b_apply_v1_1.py`                | OK     | OK    |
| 3 | `app/scripts/round18_reset1c_restore_from_jsonl_manifest.py` | OK   | OK    |
| 4 | `app/scripts/round18_reset1c_field_cleanup.py`             | OK     | OK    |
| 5 | `app/scripts/round18_reset1b_staged_backup_materialize.py` | OK     | OK    |
| 6 | `app/core/job_freeze.py`                                   | OK     | OK    |
| 7 | `app/scripts/round18_reset1b_apply_v1_2.py`                | OK     | OK    |

- Postflight snapshot:
  `/app/memory/r18_reset1b_v1_2_staged_sealed_postflight.json`
- Log verifica:
  `/app/memory/r18_reset1b_v1_2_staged_sealed_check_log.txt`
- **Pytest** `-k "sealed or integrity"`: **4 passed** in 1.71s
  - `test_t01_sealed_scripts_untouched` (v1_2) PASS
  - `test_t01_sealed_script_untouched` (hotfix_starter_kit) PASS
  - `test_06_whitelist_slugs_sealed` (round18.12 guard) PASS
  - `test_t03_counter_threat_referential_integrity` (round160) PASS
- **RESULT: 7/7 PASS** — nessun sigillo modificato.

### 14. warning residui
- **Warning bloccanti**: nessuno.
- **Warning informativi / accettati**:
  1. `PendingDeprecationWarning` pytest (`starlette.formparsers` /
     `import multipart`) — dipendenza esterna starlette, non correlata
     al reset; già presente in tutte le esecuzioni pytest.
  2. `orbus.seed_round5.base_strength` — stato **HOLD/backlog** per
     direttiva PM (P3, non bloccante).
  3. Log mobile: `Ngrok tunnel took too long to connect` — ambiente
     mobile expo, non correlato al backend/DB.
- Nessun warning nuovo introdotto da v1.2.

### 15. go/no-go tecnico e1_dev
- **Verdetto tecnico: GO (staged tecnicamente valido)**
- Motivazione:
  - Dry-run v1.2 exit 0, plan coerente con manifesto v1.2.
  - Backup materializzato + sha256 line-by-line PASS su 33 file /
    8 501 righe.
  - DB invarianza staged confermata (delta=0 su 8 collezioni +
    gold_total).
  - Double freeze HTTP + internal job attivo e funzionalmente
    verificato via curl.
  - 7 sigilli integri (SHA256 + mtime + pytest).
  - Idempotency guard verificata: audit_log conta zero eventi
    `R18_FULL_GUILD_FRESH_START_APPLIED_V1_2`.
  - Nessun warning bloccante introdotto.
- **Attenzione PM**:
  - Il REAL apply causerà `gold_delta = −4 016 443` (reset a 100 gold
    per ognuna delle 672 gilds). Comportamento voluto da manifesto v1.2.
  - Il REAL apply archivierà 3 415 adventurers "historically drifted"
    (incluse le 15 con null stats note) e ne rigenererà 3 360 con
    `base_stats_exact_no_variance` corretti.

---

## STATE — STOP Step 7

Fermo qui. **Nessun REAL apply eseguito**. Nessuna rimozione dei flag
freeze. Nessuna modifica ai sigilli.

- Freeze flags: **ancora ATTIVI** (verifica post-Step 5: OK).
- Sistema: in **doppio freeze** (HTTP + Internal Job).
- Backup staged persistente:
  `/app/backend/backups/r18_reset1b_v1_2_staged_20260705T132515Z/`
- Attesa **GO PM** per procedere con REAL apply v1.2.

### Comando previsto per REAL apply (NON eseguito)
```bash
cd /app/backend && python -m app.scripts.round18_reset1b_apply_v1_2 \
  --apply --i-understand-this-will-reset-all-guilds
```

### Log/artefatti generati in questa sessione (Step 2-6)
- `/app/memory/r18_reset1b_v1_2_staged_dry_run_log.txt`
- `/app/memory/r18_reset1b_v1_2_staged_materialize_log.txt`
- `/app/memory/r18_reset1b_v1_2_staged_db_snapshot_after.json`
- `/app/memory/r18_reset1b_v1_2_staged_invariance_check_log.txt`
- `/app/memory/r18_reset1b_v1_2_staged_integrity_log.txt`
- `/app/memory/r18_reset1b_v1_2_staged_sealed_check_log.txt`
- `/app/memory/r18_reset1b_v1_2_staged_sealed_postflight.json`
- `/app/backend/backups/r18_reset1b_v1_2_staged_20260705T132515Z/`
  (33 file jsonl + manifest.json)
- `/app/memory/r18_reset1b_v1_2_staged_report.md` (questo file)
- Nuovo script helper (NON sigillato, sibling di supporto invariance):
  `/app/backend/app/scripts/round18_reset1b_v1_2_staged_invariance_check.py`
