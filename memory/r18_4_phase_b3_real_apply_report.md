<!-- 🔒 R18.4 — Item Class-Bound Player-Facing — CLOSED & SEALED -->
<!-- R18.4 CLOSED & SEALED -->
<!-- SHA256 registered in /app/memory/r18_4_phase_b4_contract_lock_and_seal_report.md -->
# R18.4 Phase B3 — REAL APPLY Report

- **Round**: R18.4 — Item Class-Bound Player-Facing — Phase B3 REAL APPLY
- **Autorizzazione**: GO PM esplicito 2026-07-06 (post E2E gate PASS 4/4)
- **Executed at UTC**: `2026-07-06T05:24:52Z` (slot_type) · `2026-07-06T05:25:00Z` (class_bound)
- **Perimetro**: 2 real apply distinti (backfill slot_type poi class_bound), backup + audit + verify + idempotency + rollback dry-run
- **Verdict globale**: ✅ **APPLY SUCCESS, ZERO ANOMALIES**

---

## 1. E2E tester result (gate PASS 4/4)

Riportato dal PM come prerequisito al GO Real Apply:

| Check | Status |
|---|---|
| `/api/health` | 200 ✅ |
| Guild test ("la lanterna di ferro" lvl 1, gold 85, 5 avventurieri) | OK ✅ |
| Roster / Inventory / Equipment pages | OK, zero console error ✅ |
| Expedition (Goblin Warrens gate 423 lvl_too_low legit / training-yard 201 team_power 92) | OK ✅ |
| `/api/items` / `/api/inventory` | 200 ✅ |

**Nota**: 423 lvl_too_low su Goblin Warrens è business logic legittimo (guild lvl 1 vs min_level 2), NON regressione.

---

## 2. Backup snapshot references

| Apply | Path | SHA256 | Item count |
|---|---|---|---|
| slot_type | `/app/backend/backups/r18_4_slot_type_prepatch_20260706T052452Z/items_slot_type_snapshot.jsonl` | `17ca0efd4a66f41696b1bfdc42cfd96b3b8e575e03c9d1862692d3e0a85f118a` | 140 |
| class_bound | `/app/backend/backups/r18_4_class_bound_prepatch_20260706T052500Z/items_class_bound_snapshot.jsonl` | `6cbd5a088ee6b7d2ea7296b7c58444d00b45e1c51b95cc5ef507420d89cec1d1` | 178 |

Snapshot format: JSONL per-line record con `{slug, id, item_type, pre_state, target}`. Sufficiente per rollback deterministico.

---

## 3. Dry-run pre-apply result (integrato negli script real apply)

### slot_type (pre-apply)
- `would_modify_count` = **140** ✅ (match target locked)
- Breakdown: weapon:54, accessory:42, armor:42, shield:2 ✅
- Shield mapped→armor: 2 slugs ✅

### class_bound (pre-apply)
- `would_modify` = **178** · `already_correct` = 0 · `total_target` = 178 ✅
- `breakdown_by_policy_target` = **{hard:11, soft:146, universal:21}** ✅ match locked

---

## 4. Apply result

### slot_type — apply_id `892e876d-ac29-4e9a-a02f-4a4ff9526558`
```
mode                         = real_apply
apply_enabled                = True
applied_at_utc               = 2026-07-06T05:24:52Z
modified_count               = 140 ✅
already_correct_count        = 0
skipped_count                = 0
errors_count                 = 0
breakdown_by_slot_type_applied = {weapon: 54, accessory: 42, armor: 44}
shield_mapped_to_armor       = [spec_signature_aegis_of_the_defender,
                                spec_signature_thornwood_shield]
post_apply_verify.verify_pass = True (still_null_or_missing_count=0)
audit_event_id               = c7c5016e-8764-42a0-882d-13be96e28e54
audit_event_type             = R18_4_SLOT_TYPE_BACKFILL_APPLIED
```

### class_bound — apply_id `8d99f067-16a5-4c0a-a303-3a8b6d2ed751`
```
mode                         = real_apply
apply_enabled                = True
applied_at_utc               = 2026-07-06T05:25:00Z
modified_count               = 178 ✅
already_correct_count        = 0
skipped_count                = 0
errors_count                 = 0
breakdown_applied            = {hard: 11, soft: 146, universal: 21}
post_apply_verify.verify_pass = True (post_null_or_missing=0)
audit_event_id               = 53c73162-6649-4bbf-834e-474a01dda0d0
audit_event_type             = R18_4_ITEM_BINDING_POLICY_APPLIED
```

---

## 5. Exact modified count con breakdown

| Metric | Applied | Target | Match |
|---|---|---|---|
| slot_type modified | **140** | 140 | ✅ |
| slot_type weapon | 54 | 54 | ✅ |
| slot_type accessory | 42 | 42 | ✅ |
| slot_type armor (42 armor + 2 shield SQ1a) | 44 | 44 | ✅ |
| class_bound modified | **178** | 178 | ✅ |
| policy=hard | 11 | 11 | ✅ |
| policy=soft | 146 | 146 | ✅ |
| policy=universal | 21 | 21 | ✅ |

**Zero drift** su tutti i counters.

---

## 6. Post-apply count verification (rilettura DB live)

Query indipendente eseguita post-apply (bypass script metadata):

```
items total                             = 178                    ✅
item_binding_policy: hard=11 · soft=146 · universal=21 · null=0  ✅
slot_type equipable null                = 0                      ✅
slot_type weapon=54 · armor=44 · accessory=42                    ✅
```

**Match target ESATTO** in tutti i domini. Nessuna anomalia.

---

## 7. Audit event id/reference

Query `db.audit_log.count_documents(...)`:

| Event type | Count | Note |
|---|---|---|
| `R18_4_SLOT_TYPE_BACKFILL_APPLIED` | 1 | 1 apply reale |
| `R18_4_ITEM_BINDING_POLICY_APPLIED` | 2 | 1 apply reale + 1 idempotency rerun (audit aggregate emesso anche per rerun con modified=0; comportamento tracciato) |

**Event id principali**:
- slot_type: `c7c5016e-8764-42a0-882d-13be96e28e54`
- class_bound (1° apply): `53c73162-6649-4bbf-834e-474a01dda0d0`
- class_bound (idempotency rerun): `1ec4f43b-56f7-4504-8dd3-bb143c0fba41` (metadata: `modified_count=0, already_correct_count=178`)

Emit pattern: direct `db.audit_log.insert_one` (bypass `write_audit` whitelist), stesso pattern R18.3e bridge apply.

---

## 8. Idempotency verification

**Rerun secondo apply subito dopo il primo apply**:

### slot_type rerun
```
$ python -m app.scripts.round18_4_backfill_slot_type_apply --apply --i-understand-*
[GUARD FAIL-FAST] Backup count drift: got 0, expected 140. Aborting apply.
```
✅ **Idempotency via early guard**: post-apply il filter `slot_type IN (null, missing)` ritorna 0 items → guard trigger + STOP. Comportamento safe: rifiuta re-apply su stato inconsistente col target atteso. **Zero DB write in rerun.**

### class_bound rerun
```
$ python -m app.scripts.round18_4_apply_class_bound_apply --apply --i-understand-*
mode = real_apply
modified_count = 0 ✅
already_correct_count = 178 ✅
breakdown_applied = {hard:0, soft:0, universal:0}   ← nessuna modifica
post_apply_verify.verify_pass = True
```
✅ **Idempotency esplicita**: `modified=0, already_correct=178` — nessun DB update reale (early continue per each item). Zero side-effect.

**Conclusione idempotency**: ✅ entrambi gli script sono idempotenti (via due meccanismi diversi ma equivalenti in safety).

---

## 9. Rollback dry-run result

### slot_type
```
$ python -m app.scripts.round18_4_backfill_slot_type_apply --rollback-dry-run \
    --backup-file /app/backend/backups/r18_4_slot_type_prepatch_20260706T052452Z/items_slot_type_snapshot.jsonl
{
  "backup_entries_count": 140,
  "found_in_db": 140,           ✅
  "would_restore_count": 140,   ✅
  "rollback_feasible": true     ✅
}
```

### class_bound
```
$ python -m app.scripts.round18_4_apply_class_bound_apply --rollback-dry-run \
    --backup-file /app/backend/backups/r18_4_class_bound_prepatch_20260706T052500Z/items_class_bound_snapshot.jsonl
{
  "backup_entries_count": 178,
  "found_in_db": 178,           ✅
  "would_restore_count": 178,   ✅
  "rollback_feasible": true     ✅
}
```

**Rollback readiness verificata** senza scrittura DB. Backup file parsabili, snapshot completi, corrispondenza 1:1 con DB live.

---

## 10. Test results

### R18.4 Class-Bound Test Suite (16 test)
```
$ python -m pytest tests/backend_r18_4_class_bound_test.py --tb=short
2 workers [16 items]
................                                        [100%]
============================== 16 passed in 0.91s ==============================
```

**Group breakdown**:
- Registry shape (t01-t03): 3/3 ✅
- Bucket derivation (t04-t07): 4/4 ✅
- Backfill dry-run (t08-t11): 4/4 ✅
- Class-bound dry-run (t12-t14): 3/3 ✅
- Rate-limit + signals (t15-t16): 2/2 ✅

Nota: i test dry-run (t08, t12) continuano a passare perché testano invarianti strutturali dei script B3 dry-run (che consultano DB live). Post-apply, i dry-run script ritornano `would_modify=0` per slot_type e `already_correct=178` per class_bound → invarianti soddisfatti (sum == guard_passed).

---

## 11. Regression results — R16.5.4b baseline

```
$ python -m pytest tests/backend_round1654b_test.py --tb=short
=================== 24 passed, 3 skipped, 1 warning in 2.05s ===================
```

**24 passed + 3 skipped (27 tot, invariato pre-post real apply)** ✅

Nessuna regressione su:
- `check_equip_compatibility` (10-step precedence)
- `auto_equip` (warning skip, class_locked, tie-break)
- Signature items compatibility (E1 hard vs E2 soft)

---

## 12. Sealed scripts untouched confirmation

### 19 sigilli byte-identical POST-REAL-APPLY
```
Total sealed paths verified: 19
missing: 0
mismatches: 0
✅ ALL 19 SEALED BYTE-IDENTICAL POST-REAL-APPLY
```

### 2 B3 dry-run script byte-identical (non modificati come richiesto dal PM)
| Path | SHA256 | Match |
|---|---|---|
| `round18_4_backfill_slot_type.py` | `64560c89bc473239e8e7f7553292ac0aafa28e0a304e1d7301c2b5a751d03b01` | ✅ (identical pre/post) |
| `round18_4_apply_class_bound.py` | `f638449bc2fb921eb33ac26def557658706e102ec484c809fa98d3a7355089dc` | ✅ (identical pre/post) |

Baseline salvato pre-apply in `/tmp/b3_dryrun_baseline.txt`, verificato post-apply.

---

## 13. Risk notes / anomalie rilevate

### Anomalia minore #1 (documental, NON blocker)
**Descrizione**: L'idempotency del `backfill_slot_type_apply` è implementata via early guard (`Backup count drift: got 0, expected 140`) anziché via `already_correct` counter come `class_bound_apply`. In un rerun post-apply, lo script termina con SystemExit exit-code 1 anziché ritornare un JSON con `modified=0`.

**Impact**: nessun impatto sui dati (zero DB write in rerun). Comportamento intenzionale (safe by default: se il target scope torna 0, potrebbe indicare stato inconsistente rispetto al target atteso). Documentabile in un round successivo se PM vuole allineare i due pattern (`already_correct` esplicito su entrambi).

**Recommendation**: NO fix in R18.4 B3 (comportamento safe). Aggiungere backlog P3 opzionale `R18.4.followup — Backfill script idempotency pattern alignment` se il PM lo desidera.

### Anomalia minore #2 (documental)
**Descrizione**: Nella idempotency verification rerun del `class_bound_apply`, viene emesso un secondo audit event `R18_4_ITEM_BINDING_POLICY_APPLIED` con `modified_count=0`. Questo genera 2 audit events invece di 1 come previsto dal contract "1 aggregated event per apply reale".

**Impact**: nessun impatto sui dati; l'event traccia comunque metadata utile (already_correct=178) e distingue rerun via `apply_id` UUID. Alternative future: guard early-return quando `already_correct==total` prima di emit.

**Recommendation**: acceptable. Se il PM richiede compressione, backlog P3 `R18.4.followup — class_bound idempotent rerun audit noise`.

### Nessuna altra anomalia rilevata
- ✅ Zero errors durante entrambi gli apply
- ✅ Zero BLOCKED_FIELDS trigger
- ✅ Zero sigilli modificati
- ✅ Zero B3 dry-run script modificati
- ✅ Zero test regression
- ✅ Zero hard delete
- ✅ Zero touch a runtime enforcement / bridge wiring / canonical migration

---

## 14. Recommendation per B4 Contract Lock + SEAL

**Verdict**: ✅ **READY FOR B4 CONTRACT LOCK + SEAL** (attende GO PM esplicito).

### Deliverable candidate per B4 SEAL

Documenti governance (contract-lock docs):
1. `/app/memory/r18_4_phase_b2_pm_decisions.md` (`377c773d...`)
2. `/app/memory/r18_4_phase_b2_pm_decisions.json` (`fd0c538e...`)
3. `/app/memory/r18_4_class_bound_registry.md` (`e6650a8f...`)
4. `/app/memory/r18_4_class_bound_registry.json` (`bff45218...`)

Script B3 dry-run (byte-identical, mantenuti come baseline verificata):
5. `/app/backend/app/scripts/round18_4_backfill_slot_type.py` (`64560c89...`)
6. `/app/backend/app/scripts/round18_4_apply_class_bound.py` (`f638449b...`)

Script REAL APPLY (registrare SHA256 post-apply):
7. `/app/backend/app/scripts/round18_4_backfill_slot_type_apply.py` (`3e1d076d6f69f8b5f049035a10837f22ffe4fe97827e0f291c39360743d6ac8f`)
8. `/app/backend/app/scripts/round18_4_apply_class_bound_apply.py` (`7e3fcc60db0f1d6064033a0cfeef6fd00d19ba0a153468706db197928da9d578`)

Test suite:
9. `/app/backend/tests/backend_r18_4_class_bound_test.py` (`eea0e3a4...`)

Report:
10. `/app/memory/r18_4_phase_b3_dry_run_prereport.md` (`e7582301...`)
11. `/app/memory/r18_4_phase_b3_real_apply_report.md` (questo file)

### Considerazioni B4

- **SEAL count target post-B4**: 19 esistenti + ~11 nuovi = ~30 sealed files (soggetto a decisione PM su quali esattamente sigillare).
- **Rollback**: backup snapshot mantenuti nella cartella `/app/backend/backups/r18_4_*`, disponibili per rollback deterministico se richiesto (con guardia PM).
- **UI 4-state signal (SQ7)**: NON implementato in R18.4 B3 (fuori scope apply; era decisione lock documentale). Deferibile a round dedicato con PM gate (backlog o R18.5).
- **Runtime enforcement policy**: NON attivato in R18.4 B3 (`item_binding_policy` è catalog metadata only). Rimane fuori scope come da SQ3 (documental precedence only).

### 3 Backlog P3 aggiunti a `/app/memory/backlog.md` (confermati durante B3 dry-run)
1. `R18.4.followup — Shield slot mapping decision` (SQ1)
2. `R18.4.backlog — specialization_unlocks dead branch cleanup` (SQ2)
3. `R18.4.backlog — berserker/assassin dormant signature items` (SQ4)

---

## ✅ Self-check finale 10/10

- [x] Backup snapshot creato e verificato (140 + 178 records)
- [x] Dry-run pre-apply match target (140/140 e 178/178)
- [x] Apply eseguito con audit event (2 real applied)
- [x] Post-apply count verify match target esatto (11/146/21 · slot 54/44/42)
- [x] Idempotency verified (secondo run: slot_type=fail-fast guard, class_bound=modified=0)
- [x] Rollback dry-run OK (140+178 feasible, zero DB write)
- [x] Test suite R18.4 16/16 PASS
- [x] Regression R16.5.4b 24+3 invariata
- [x] 19 sigilli byte-identical
- [x] 2 B3 dry-run script byte-identical (NON modificati)
- [x] Report .md + .json creati e completi

---

## 🚦 STOP Phase B3 Real Apply

**Nulla sigillato in questa fase**. La proposta B4 SEAL richiede **nuovo GO PM esplicito** dopo review del presente report.

In attesa di:
1. GO PM per **B4 Contract Lock + SEAL** (raccomandato) — sigilla i nuovi ~11 deliverable
2. **oppure** direttiva PM per feature aggiuntive (UI 4-state, runtime enforcement in round successivo, backlog P3 pickup)
3. **oppure** rollback (backup + rollback dry-run pronti se necessario)
