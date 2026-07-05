# R18.Reset.1b.hotfix.v1_3 — FASE A REPORT (Design + Preflight + Dry-run + Test)

**Data**: 2026-07-05T14:47:00Z UTC
**Autore**: e1_dev
**Fase**: A (Design / Preflight / Dry-run / Test suite)
**Stato**: ✅ COMPLETATA — STOP e attesa GO PM per FASE B

Freeze status: `orbus_maintenance.flag` ACTIVE · `orbus_internal_job_freeze.flag` ACTIVE
7 sigilli byte-identici: ✅ PASS 7/7

---

## 1. Deliverable creati

| File | Tipo | Note |
|:---|:---|:---|
| `/app/backend/app/scripts/round18_reset1b_apply_v1_3.py` | Sibling script (NON sigillato) | 14 field patching + guards |
| `/app/backend/tests/backend_round1b_hotfix_v1_3_schema_compat_test.py` | Test suite | 20 test (17 PASS + 3 SKIP gate-blocking HTTP) |
| `/app/memory/r18_reset1b_hotfix_v1_3_preflight.json` | Preflight JSON | Machine-readable |
| `/app/memory/r18_reset1b_hotfix_v1_3_preflight.md` | Preflight narrativo | Leggibile PM |
| `/app/memory/r18_reset1b_hotfix_v1_3_dry_run_log.txt` | Log dry-run | exit=0, 3360 would-modify |
| `/app/memory/r18_reset1b_hotfix_v1_3_test_log.txt` | Log pytest | 17 PASS / 3 SKIP |
| `/app/memory/r18_reset1b_hotfix_v1_3_phase_a_report.md` | **Questo report** | Report FASE A |

Nessuno dei 7 sigilli è stato modificato.

## 2. Script v1.3 — Design sintetico

### Target
- Marker esclusivo: `r18_reset1b_hotfix_v1_2 = true`
- Target count guard: **=3360** (rifiuta se diverso)

### Campi patchati (14 totali)
**Hard-critical (fix 500)**:
1. `adventurer_class_id` ← catalog `id` (via `class_slug` lookup)
2. `experience` = 0
3. `is_available` = true

**Semantic parity**:
4. `class_name` ← catalog `name`
5. `class_role` ← catalog `role`
6. `rarity` = "Common"
7. `stamina` = 100
8. `morale` = 100
9. `status` = "idle"
10. `is_starter` = true
11. `traits` = []
12. `rename_count` = 0
13. `is_retired` = false
14. `grade` = "common" (normalizza il "F" v1.2)

**Marker tracking**: `r18_reset1b_hotfix_v1_3=true`, `..._at`, `..._apply_id`
**NON toccati**: id, guild_id, name, class_slug, stats5, level, xp, hp_current/max, created_at, marker v1.2, phase13_unbaked

### CLI Contract
- Default: **DRY_RUN** (nessuna scrittura)
- Apply real: `--apply --i-understand-this-will-patch-reset-adventurers` (doppio flag obbligatorio)
- Exit codes: `30` (double-flag mancante), `40` (freeze inattivo), `41` (mapping <11/11), `42` (target count != 3360), `43` (class_slug non-safe), `44` (idempotency block)

### Guards (fail-fast)
- ✅ Freeze required in APPLY (HTTP + internal job)
- ✅ Target count guard = 3360
- ✅ Mapping 11/11 catalog
- ✅ Idempotency: rifiuta se audit `APPLIED_V1_3` senza `ROLLED_BACK`
- ✅ Slug conformance whitelist
- ✅ Self-audit static

### Audit events (emessi solo dopo apply riuscito, sempre entrambi)
- `R18_STARTER_ROSTER_HOTFIX_APPLIED`
- `R18_STARTER_ROSTER_HOTFIX_APPLIED_V1_3`

Metadata condiviso:
```
round = R18.Reset.1b.hotfix.v1_3
apply_script = round18_reset1b_apply_v1_3.py
apply_version = v1.3
target_count = 3360
fields_patched = [14 fields]
class_mapping_count = 11
schema_compatibility_fix = true
http_maintenance_required = true
internal_job_freeze_required = true
apply_id = <uuid>
completed_at = <iso>
backup_reference = /app/backend/backups/r18_reset1b_v1_2_20260705T134230Z
supersedes_versions = ["v1.2"]
patch_stats = {…}
```

## 3. Preflight (11 sezioni)

Sintesi dei principali punti dal preflight (dettaglio in
`r18_reset1b_hotfix_v1_3_preflight.md`):

| Punto | Esito |
|:---|:---:|
| target count 3360 | ✅ |
| catalog mapping 11/11 | ✅ |
| tutti gli slug della catalog hanno id + name + role + base_stats | ✅ |
| freeze both active | ✅ |
| idempotency: 0 prior APPLIED_V1_3 | ✅ |
| backup fresh v1.2 manifest sha256 33/33 | ✅ |
| enum canonici individuati | ✅ |
| campi runtime-critical tutti mappabili | ✅ |
| decisione xp: lasciato invariato (legacy) + experience aggiunto ex-novo | ✅ documentata |
| grade "F" → "common" | ✅ documentato |
| hard-stop conditions definite | ✅ 6 |

## 4. Dry-run — Risultato

Comando: `python -m app.scripts.round18_reset1b_apply_v1_3 --dry-run`
Exit: **0**

Output chiave:
```
MODE = DRY_RUN. Nessuna scrittura sara effettuata.
[freeze_check] both_active: true
[catalog_preload] loaded=11/11 ok=True
[target_scan] target_count=3360 expected=3360 slug_conformant=3360
[idempotency] prior_APPLIED_V1_3: 0, blocks_apply: false
[patch] DRY_RUN per slug: alchemist=299, bard=324, druid=311, mage=281,
  monk=327, paladin=303, priest=278, ranger=299, rogue=302, warlock=305,
  warrior=331  → TOTALE 3360 would_modify
[audit] DRY_RUN: would emit BOTH audit events with apply_id=<uuid>
patch_stats: adventurer_class_id_set=3360, ..., grade_updated=3360,
  hotfix_marker_set=3360
```

Nessuna scrittura effettuata (dry-run puro, verificato dal test `test_t10`).

## 5. Test suite — Risultato

Comando: `pytest tests/backend_round1b_hotfix_v1_3_schema_compat_test.py -v`
Exit: **0**
Risultato: **17 passed · 3 skipped · 0 failed**

### PASS (17)
1. `test_t01_sealed_scripts_untouched` — 7/7 sigilli byte-identici
2. `test_t02_v1_3_sibling_exists` — sibling presente, contiene sentinel
3. `test_t03_apply_without_ack_blocked` — exit=30
4. `test_t04_dry_run_target_count` — dry-run exit=0, target=3360
5. `test_t05_class_mapping_11_11` — 11/11 catalog OK
6. `test_t06_all_target_will_get_class_id` — union safe slugs = 3360
7. `test_t07_experience_zero_post_fix` — pre-fix invariant + payload
8. `test_t08_is_available_true_post_fix` — payload contains true
9. `test_t09_enum_canonical_values` — grade/rarity/status canonici
10. `test_t10_dry_run_no_db_write` — snapshot before==after
11. `test_t11_apply_requires_double_flag` — verifica combinazioni flag
12. `test_t12_idempotency_guard_present` — guard code presente
13. `test_t13_audit_events_declared` — entrambi eventi declared
14. `test_t17_inventory_kit_unchanged` — 672 doc × qty=3 = 2016
15. `test_t18_gold_invariant` — 67200 totale, min=max=100
16. `test_t19_no_hidden_classes_in_target` — 0 non-safe slug nel target
17. `test_t20_freeze_off_gate_documented` — 14/15/16 sono skipif-gated

### SKIP (3) — gate-blocking post-freeze-OFF (per design)
18. `test_t14_get_adventurers_http_live_200` — HTTP live
19. `test_t15_get_dungeons_http_live_200` — HTTP live
20. `test_t16_post_expedition_http_live_no_500` — HTTP live

**Motivazione dello skip**: con freeze attivo `POST /api/auth/login` → 503, non è possibile ottenere il JWT per i test autenticati. I 3 test hanno decoratore `@pytest.mark.skipif(_is_freeze_active(), ...)` e diventeranno gate-blocking obbligatori nella FASE B post-freeze-OFF finale.

## 6. HTTP Live Playbook per FASE B

Il PM ha specificato "learning v1.2": **niente più PASS simulati per endpoint HTTP runtime-critical**. Playbook proposto per la finestra HTTP live:

**Fase B step 12 (dopo apply v1.3 real + verifiche DB)**:
1. **Rimuovi freeze**: `rm /tmp/orbus_maintenance.flag /tmp/orbus_internal_job_freeze.flag`
2. **Esegui HTTP live gate** (comandi diretti curl + pytest deselect skipif):
   - `curl POST /api/auth/login` con `tester@orbus.test:password123` → aspettato 200 + JWT
   - `curl GET /api/adventurers` con Bearer → **aspettato 200** (gate blocker)
   - `curl GET /api/dungeons` con Bearer → aspettato 200
   - `curl POST /api/expeditions` con payload minimo → **NON deve dare 500**
3. **Se qualcuno fallisce**: riattivare i freeze immediatamente (`touch /tmp/orbus_*`) e riportare al PM con log + stato DB.
4. **Se tutti passano**: procedi con Step 14 (report finale FASE B) e stop per delega e1_tester al PM.

Alternativa: eseguire `pytest -k "http_live"` con freeze già disattivato — i 3 skipif si disattiveranno automaticamente e i test diventeranno gate-blocking pytest-driven.

## 7. Warning residui

- **`PendingDeprecationWarning` starlette formparsers** (14 warnings in pytest output) — dipendenza esterna, non correlato al reset.
- **`orbus.seed_round5.base_strength`** — HOLD/backlog P3 (PM directive).
- **Log job_freeze**: continua a skippare `orbus.inventory.backfill_bound_fields_if_missing` e `orbus.training.backfill_missing_signature_inventory_rows` (comportamento atteso durante il freeze).
- **Test collection warnings**: nessun warning bloccante sulla test suite v1.3.
- **Pytest workers**: gw0 e gw1 (pytest-xdist) — funzionamento normale.

Nessun warning nuovo introdotto da v1.3.

## 8. Stato sistema post-FASE A

| Item | Stato |
|:---|:---:|
| Freeze `orbus_maintenance.flag` | ACTIVE |
| Freeze `orbus_internal_job_freeze.flag` | ACTIVE |
| `GET /api/health` | 200 |
| `POST /api/auth/login` (con freeze) | 503 |
| 7 sigilli byte-identici | PASS |
| `GET /api/adventurers` (auth) | **500** (verrà risolto da apply v1.3) |
| DB writes durante FASE A | **0** |
| Audit `APPLIED_V1_3` count | 0 (pronto per FASE B) |

## 9. Backup Retention

**Backup fresh v1.2** (rollback source-of-truth se FASE B fallisce):
`/app/backend/backups/r18_reset1b_v1_2_20260705T134230Z/`
- Manifest sha256 line-by-line: **PASS 33/33** (verificato)
- Retention minima: 90 giorni
- **NON tocca** — nessun cleanup autorizzato

**Backup staged v1.2 (approved manifest)**:
`/app/backend/backups/r18_reset1b_v1_2_staged_20260705T132515Z/`
- Retention minima: 90 giorni
- **NON tocca**

## 10. Verdetto tecnico e1_dev per gate PM

**GO tecnico su FASE B**, con questi vincoli espliciti:
- Prima di apply v1.3 real, materializzare backup fresh **pre-v1.3** con timestamp UTC dedicato
- HTTP live tests devono essere il **gate bloccante** post-freeze-OFF (non simulati)
- Idempotency guard v1.3 attiva: retry apply v1.3 sullo stesso apply_id verrà bloccato con exit 44

## 11. STOP FASE A

Non procedo autonomamente con FASE B (real apply). Attendo GO PM esplicito con eventuali direttive aggiuntive (es. approve mapping deterministico 11/11, approve dei 14 campi patchati, approve del playbook HTTP live).

**Riepilogo pronto per gate PM**:
- Deliverable: 4 (script + test + 2 report)
- Dry-run: exit 0, would-modify 3360 (=target)
- Test suite: 17/20 PASS, 3 SKIP (gate-blocking HTTP)
- 7 sigilli intatti
- Freeze ancora attivo
- Nessuna scrittura DB
- Backup rollback source verificato intatto

**Aspetto GO PM per procedere con FASE B (real apply + 18 verifiche DB + HTTP live gate + freeze OFF + report finale).**
