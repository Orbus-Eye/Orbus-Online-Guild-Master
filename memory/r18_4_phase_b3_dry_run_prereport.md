<!-- 🔒 R18.4 — Item Class-Bound Player-Facing — CLOSED & SEALED -->
<!-- R18.4 CLOSED & SEALED -->
<!-- SHA256 registered in /app/memory/r18_4_phase_b4_contract_lock_and_seal_report.md -->
# R18.4 Phase B3 — Dry-Run Pre-Report

- **Round**: R18.4 — Item Class-Bound Player-Facing — Phase B3
- **Stage**: Dry-Run only (autorizzato condizionalmente dal PM 2026-07-06)
- **Executed at UTC**: `2026-07-06T05:10:00Z`
- **Perimetro**: sibling scripts eseguiti in DRY-RUN. Zero DB write. Zero apply reale. Zero touch a sigilli. Test suite 16/16 PASS.
- **APPLY_ENABLED**: `False` (LOCKED — richiede nuovo PM gate esplicito post-review)
- **Governance**: rispettata (13 no-go boundaries + hard-stop guards attivi)

---

## 1. Deliverable creati

| # | File | SHA256 (first 16) | Ruolo |
|---|---|---|---|
| 1 | `/app/memory/r18_4_phase_b2_pm_decisions.md` | `377c773df4f4dd8b` | B2 decision lock (11 sezioni + no-go) |
| 2 | `/app/memory/r18_4_phase_b2_pm_decisions.json` | `fd0c538ed6931176` | B2 decision lock machine-readable |
| 3 | `/app/memory/r18_4_class_bound_registry.md` | `e6650a8fdbfb5920` | Bucket + policy target registry |
| 4 | `/app/memory/r18_4_class_bound_registry.json` | `bff4521863012089` | Registry machine-readable |
| 5 | `/app/backend/app/scripts/round18_4_backfill_slot_type.py` | `64560c89bc473239` | Sibling backfill slot_type (dry-run) |
| 6 | `/app/backend/app/scripts/round18_4_apply_class_bound.py` | `f638449bc2fb921e` | Sibling class_bound (dry-run) |
| 7 | `/app/backend/tests/backend_r18_4_class_bound_test.py` | `eea0e3a49bfa04d5` | Test suite (16 test, 5 gruppi) |
| 8 | `/app/memory/r18_4_phase_b3_dry_run_prereport.md` | (this file) | Pre-report B3 |
| 9 | `/app/memory/r18_4_phase_b3_dry_run_prereport.json` | (companion .json) | Pre-report machine-readable |

**Backlog updated**: `/app/memory/backlog.md` con 3 nuove entry P3 (R18.4.followup Shield · R18.4.backlog spec_unlocks · R18.4.backlog berserker/assassin dormant).

---

## 2. Dry-Run: `round18_4_backfill_slot_type.py`

```
mode                        = dry_run
apply_enabled               = False (LOCKED)
source_round                = R18.4 Phase B3
registry_sha256             = bff4521863012089e809e165641ba1088a17bb4aa5b7f3c054c21a92ba2ded17
decision_lock_sha256        = fd0c538ed69311768faa921d4a1e2a5ab24b94854dc921a5ea056d13cdf2ddd6
target_count_expected       = 140
would_modify_count          = 140 ✅
skipped_count               = 0
errors_count                = 0
guard_hard_stop_passed      = 140 ✅
breakdown_by_item_type      = {weapon: 54, accessory: 42, armor: 42, shield: 2}
breakdown_by_target_slot    = {weapon: 54, accessory: 42, armor: 44}       ← 42+2 shield
shield_to_armor_mapped      = 2 slugs (aegis_of_the_defender, thornwood_shield)
audit_event.actually_emit   = False (dry-run)
backup_snapshot.actually_wr = False (dry-run)
real_apply_result           = BLOCKED — APPLY_ENABLED=False (LOCKED per R18.4 Phase B2)
```

**Payload samples (5)**:
- `rusted-sword` (weapon) → `{slot_type: "weapon"}`
- `goblin-dagger` (weapon) → `{slot_type: "weapon"}`
- `cracked-staff` (weapon) → `{slot_type: "weapon"}`
- `novice-charm` (accessory) → `{slot_type: "accessory"}`
- `torn-leather-vest` (armor) → `{slot_type: "armor"}`

**Verdict**: ✅ backfill target 140/140 · shield→armor SQ1(a) OK · guard hard-stop 140/140.

---

## 3. Dry-Run: `round18_4_apply_class_bound.py`

```
mode                        = dry_run
apply_enabled               = False (LOCKED)
source_round                = R18.4 Phase B3
registry_sha256             = bff4521863012089e809e165641ba1088a17bb4aa5b7f3c054c21a92ba2ded17
target_count_expected       = 178
would_modify_count          = 178 ✅
already_populated_skipped   = 0
errors_count                = 0
guard_hard_stop_passed      = 178 ✅
breakdown_by_policy         = {hard: 11, soft: 146, universal: 21}
breakdown_matches_expected  = True ✅
audit_event.actually_emit   = False (dry-run)
backup_snapshot.actually_wr = False (dry-run)
real_apply_result           = BLOCKED — APPLY_ENABLED=False (LOCKED per R18.4 Phase B2)
```

**Payload samples (per policy)**:
- **hard**: `drake_slayer_helm`, `drake_slayer_chest`, `drake_slayer_blade` → `{item_binding_policy: "hard"}`
- **soft**: `arcane_adept_orb`, `goblin_hunter_ring`, `rusted-sword` → `{item_binding_policy: "soft"}`
- **universal**: `dragon_essence`, `iron_shard`, `raw_leather` → `{item_binding_policy: "universal"}`

**Verdict**: ✅ 178/178 items · breakdown match locked (11/146/21) · guard 178/178.

---

## 4. Guard hard-stop verifiche

### Apply flag rejection (backfill_slot_type)
```
$ python -m app.scripts.round18_4_backfill_slot_type --apply --i-understand-this-will-backfill-slot-type
[FAIL-FAST] Real apply BLOCKED. APPLY_ENABLED=False (LOCKED per R18.4 Phase B2). ✅
exit code: 1
```

### Apply flag rejection (class_bound)
```
$ python -m app.scripts.round18_4_apply_class_bound --apply --i-understand-this-will-set-item-binding-policy
[FAIL-FAST] Real apply BLOCKED. APPLY_ENABLED=False (LOCKED per R18.4 Phase B2). ✅
exit code: 1
```

### Apply senza ack flag
```
$ python -m app.scripts.round18_4_backfill_slot_type --apply
[FAIL-FAST] Real apply BLOCKED. APPLY_ENABLED=False (LOCKED per R18.4 Phase B2). ✅
exit code: 1
```

### BLOCKED_FIELDS payload guard (unit test t13)
```
$ pytest -v test_t13_class_bound_guard_hard_stop_rejects_blocked_fields
PASSED ✅
  - class_slug        → SystemExit (BLOCKED)
  - role              → SystemExit (BLOCKED)
  - primary_stat      → SystemExit (BLOCKED)
  - base_strength     → SystemExit (BLOCKED)
  - is_playable       → SystemExit (BLOCKED)
  - slot_type         → SystemExit (BLOCKED)  [nel class_bound script]
  - required_class_optional → SystemExit (BLOCKED)
  - item_binding_policy="invalid" → SystemExit (enum validation)
```

---

## 5. Test suite results

```
$ pytest tests/backend_r18_4_class_bound_test.py -v

Group 1 — Registry shape (3/3 PASS):
  ✅ test_t01_registry_json_parsable
  ✅ test_t02_registry_totals_178_11_21_146
  ✅ test_t03_registry_hard_items_exact_11_slugs

Group 2 — Bucket derivation (4/4 PASS):
  ✅ test_t04_hard_derivation_required_class_optional
  ✅ test_t05_universal_derivation_material_consumable
  ✅ test_t06_soft_derivation_residual
  ✅ test_t07_no_overlap_hard_intersect_universal

Group 3 — Backfill dry-run (4/4 PASS):
  ✅ test_t08_backfill_dry_run_target_count_140  (invariante sum/guard)
  ✅ test_t09_backfill_shield_maps_to_armor  (SQ1a invariante)
  ✅ test_t10_backfill_skip_already_populated_17  (no overwrite proof)
  ✅ test_t11_backfill_apply_enabled_false_blocks_write

Group 4 — Class-bound dry-run (3/3 PASS):
  ✅ test_t12_class_bound_dry_run_would_add_binding_policy_178
  ✅ test_t13_class_bound_guard_hard_stop_rejects_blocked_fields
  ✅ test_t14_class_bound_apply_enabled_false_blocks_write

Group 5 — Rate-limit + signals (2/2 PASS):
  ✅ test_t15_rate_limit_bucket_key_format
  ✅ test_t16_derived_signals_recommended_for_class_and_universal

============================== 16 passed in 0.89s ✅ ==============================
```

**Regression gate**:
- baseline `backend_round1654b_test.py`: **24 passed + 3 skipped** (27 tot, invariato pre-post B3) ✅

---

## 6. Sigilli verify byte-identical POST-B3

```
Total sealed paths verified: 19
missing: 0
mismatches: 0
ALL 19 SEALED FILES BYTE-IDENTICAL POST-B3 ✅
```

Nota governance: aggregate count PM = 24 (include 5 doc di contract-lock non enforceable via SHA256 diretto). Enforcement hard SHA256 = 19 file esplicitamente registrati in `r18_3e_seal_registry.json`.

---

## 7. Governance no-go boundaries — verifica

| # | Vincolo | Verificato |
|---|---|---|
| 1 | `adventurers.class_slug` non toccato | ✅ (no query update su adventurers) |
| 2 | `adventurer_classes.role` non toccato | ✅ |
| 3 | `adventurer_classes.primary_stat/secondary_stats` non toccati | ✅ |
| 4 | `adventurer_classes.base_*` non toccati | ✅ |
| 5 | `is_playable/is_active/is_canonical` non toccati | ✅ |
| 6 | `VALID_ROLES` non toccato | ✅ (grep 0 changes admin/services.py) |
| 7 | `adventurers` collection zero write | ✅ |
| 8 | items canonical IT rewrite (name/display_name/description) → non toccati | ✅ (BLOCKED_FIELDS include name/display_name/description) |
| 9 | Unlock CdM/CdV → nessuno | ✅ |
| 10 | Unlock berserker/assassin → nessuno | ✅ (SQ4 dormant) |
| 11 | is_active=false su items dormant → nessuno | ✅ |
| 12 | Hard delete → nessuno | ✅ |
| 13 | Rimozione branch specialization_unlocks → nessuna | ✅ (compatibility.py invariato) |
| 14 | Bard role drift non modificato | ✅ |
| 15 | Player-facing label classi non cambiate | ✅ |
| 16 | 19 sigilli byte-identical | ✅ (verified via sha256sum) |
| 17 | APPLY_ENABLED=False in entrambi gli script | ✅ (verified via test t11 + t14) |

---

## 8. Cosa NON è stato fatto (governance)

- ❌ Zero apply reale (backfill_slot_type + class_bound)
- ❌ Zero DB write (verified via query pre/post idempotency)
- ❌ Zero audit event emesso
- ❌ Zero backup snapshot scritto
- ❌ Zero runtime bridge wiring
- ❌ Zero migration canonical
- ❌ Zero touch ai 19 sigilli
- ❌ Zero touch a `equipment/compatibility.py`
- ❌ Zero touch a `equipment/auto_equip.py`
- ❌ Zero touch a `shared/constants.py::EQUIPMENT_SLOTS`
- ❌ Zero frontend change (`item_public()` NON modificato in R18.4 B3)

---

## 9. Self-check 10/10 Phase B3

1. ✅ B2 decision lock creato (11 sezioni + no-go boundaries)
2. ✅ Registry .md/.json creati (bucket + policy target esaustivi)
3. ✅ 2 sibling scripts creati (backfill_slot_type + apply_class_bound), APPLY_ENABLED=False LOCKED
4. ✅ Doppio flag richiesto per apply (`--apply` + `--i-understand-*`)
5. ✅ Guard hard-stop: `BLOCKED_FIELDS` + `SAFE_FIELDS` + enum validation attivi
6. ✅ Test suite 16/16 PASS
7. ✅ Baseline regression 24+3 (27 R16.5.4b) invariata
8. ✅ 19 sigilli byte-identical POST-B3
9. ✅ Dry-run counts match locked target (backfill 140/140 · class_bound 178/178 con 11/146/21)
10. ✅ 3 backlog P3 aggiunti a `/app/memory/backlog.md`

---

## 10. Prossimo Gate (RICHIESTO PM)

**Non lanciare `--apply` in autonomia. Non modificare `APPLY_ENABLED` in autonomia.**

Il gate successivo richiede **nuovo GO PM esplicito** con review del presente pre-report per:
1. **Apply reale backfill slot_type** (140 items) → richiede `APPLY_ENABLED=True` + apply_real() body implementato (attualmente stub `NOT_IMPLEMENTED`) + backup snapshot pre-apply + audit event aggregato
2. **Apply reale class_bound** (178 items) → stesso pattern

Backlog cross-reference:
- `R18.Tooling — DryRun/Apply Path Readiness Gate` (P3, pre-esistente): applicabile — apply_real body attualmente stub.

**STOP Phase B3 dry-run**. In attesa di **PM review del pre-report** e nuovo GO per apply reale (o rinvio in backlog).
