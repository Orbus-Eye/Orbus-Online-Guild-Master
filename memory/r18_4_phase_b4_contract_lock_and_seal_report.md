<!-- 🔒 R18.4 — Item Class-Bound Player-Facing — CLOSED & SEALED -->
<!-- R18.4 CLOSED & SEALED -->
# 🔒 R18.4 — Item Class-Bound Player-Facing — CLOSED & SEALED

- **Round**: R18.4 — Item Class-Bound Player-Facing — Phase B4 Contract Lock + SEAL
- **Autorizzazione**: GO PM esplicito 2026-07-06 (post gate POST-APPLY e1_tester 4/4 PASS)
- **Sealed at UTC**: `2026-07-06T07:20:00Z`
- **Seal Authority**: PM Orchestrator
- **Perimetro**: apposizione banner + SHA256 registration + test statico integrità 30 sigilli + backlog P3. Zero DB write, zero apply, zero touch a runtime enforcement.
- **Final Status**: ✅ **R18.4 CLOSED & SEALED**

---

## 1. Header
**🔒 R18.4 — Item Class-Bound Player-Facing — CLOSED & SEALED**

---

## 2. POST-APPLY e1_tester gate result (4/4 PASS)

| Check | Status | Note |
|---|---|---|
| `/api/health` | 200 ✅ | live |
| Guild test "la lanterna di ferro" lvl 1, gold 85, 5 avventurieri | OK ✅ | dashboard render |
| Roster / Inventory / Equipment pages | OK ✅ | zero console error |
| Expedition (Goblin Warrens 423 lvl_too_low legit / training-yard 201 team_power 92) | OK ✅ | business logic legit |
| `/api/items` / `/api/inventory` | 200 ✅ | metadata post-apply visibile |

Gate score: **4/4 PASS**. Nessun scope-creep, nessuna regression, DB verificato live post-apply (11 hard, 146 soft, 21 universal, slot_type 54/44/42, null=0).

---

## 3. Lista 11 file sealed (path effettivi, naming ACTUAL su disco)

| # | Path effettivo | Formato | Ruolo |
|---|---|---|---|
| 1 | `/app/memory/r18_4_phase_b2_pm_decisions.md` | Markdown | B2 decision lock (11 sezioni SQ1-SQ7) |
| 2 | `/app/memory/r18_4_phase_b2_pm_decisions.json` | JSON | B2 decision lock machine-readable |
| 3 | `/app/memory/r18_4_class_bound_registry.md` | Markdown | Bucket + policy target registry |
| 4 | `/app/memory/r18_4_class_bound_registry.json` | JSON | Registry machine-readable |
| 5 | `/app/backend/app/scripts/round18_4_backfill_slot_type.py` | Python | B3 dry-run backfill slot_type |
| 6 | `/app/backend/app/scripts/round18_4_apply_class_bound.py` | Python | B3 dry-run class_bound |
| 7 | `/app/backend/app/scripts/round18_4_backfill_slot_type_apply.py` | Python | B3 real apply backfill slot_type |
| 8 | `/app/backend/app/scripts/round18_4_apply_class_bound_apply.py` | Python | B3 real apply class_bound |
| 9 | `/app/backend/tests/backend_r18_4_class_bound_test.py` | Python (test) | Test suite R18.4 (16 test) |
| 10 | `/app/memory/r18_4_phase_b3_dry_run_prereport.md` | Markdown | Pre-report B3 dry-run |
| 11 | `/app/memory/r18_4_phase_b3_real_apply_report.md` | Markdown | Real apply report B3 |

---

## 4. Mapping PM intended name → actual sealed name

| PM intended name | Actual sealed name (on disk) | Note |
|---|---|---|
| `r18_4_item_binding_registry.md` | `r18_4_class_bound_registry.md` | naming effettivo storicamente coerente col round B2/B3 |
| `r18_4_item_binding_registry.json` | `r18_4_class_bound_registry.json` | idem |
| `backend_r18_4_item_class_bound_test.py` | `backend_r18_4_class_bound_test.py` | naming test suite già in uso |
| `r18_4_phase_b3_dry_run_report.md` | `r18_4_phase_b3_dry_run_prereport.md` | il file effettivo ha suffix `_prereport` |
| Altri 7 file | match esatto con path proposto dal PM | — |

**PM direttiva "NO rename"**: rispettata al 100%. Naming effettivo mantenuto su disco. Mapping documentato qui per traccia auditabile.

---

## 5. SHA256 dei 11 sealed files (POST-banner)

| # | Path | SHA256 (post-banner) |
|---|---|---|
| 1 | `/app/memory/r18_4_phase_b2_pm_decisions.md` | `83b5f60813cef99cc30d8f4704860ec7f17a40da0de64093b706efa2de974566` |
| 2 | `/app/memory/r18_4_phase_b2_pm_decisions.json` | `c73e6743a6fbb26177deb7e941ce6e900f38b3db08fd894451d8859711832be4` |
| 3 | `/app/memory/r18_4_class_bound_registry.md` | `e26065a1da92e98278163ee7a2dd757d65dbddbacb668ff43df2e44a3611b43c` |
| 4 | `/app/memory/r18_4_class_bound_registry.json` | `c3a58e3d94f0053870a12197b29c02e0ec7d17ddae5d85496ca17584d0a2059d` |
| 5 | `/app/backend/app/scripts/round18_4_backfill_slot_type.py` | `7108bf189415468bc7148f70186d6b5f2e1f7a618f712cbb2f02693e00ab54e6` |
| 6 | `/app/backend/app/scripts/round18_4_apply_class_bound.py` | `fda696467001d313128630735a4e91dc03f0af3cf8eb9da43ef4ca7e8f2c26fa` |
| 7 | `/app/backend/app/scripts/round18_4_backfill_slot_type_apply.py` | `6a9a3c5cb50fc97c436fe39a71d39657d199885fd0ae35d335e08c8dc60c8461` |
| 8 | `/app/backend/app/scripts/round18_4_apply_class_bound_apply.py` | `1358d42fa051623ed5e06a44ee8b5279fb11fd99afc44bb0596f06d312ec42b3` |
| 9 | `/app/backend/tests/backend_r18_4_class_bound_test.py` | `f0644e2c3df869c0344afb2e831f2fffc8759eaef7554ed1764d7ba0a74d5d28` |
| 10 | `/app/memory/r18_4_phase_b3_dry_run_prereport.md` | `3bb1484826710a9a8b688e6152150ad2c8a860352daaaf1978b1a686aef76d59` |
| 11 | `/app/memory/r18_4_phase_b3_real_apply_report.md` | `de0c9b4661ac17b9b16ea7bd4b1e90ec7909a7b46b899563eb04c8e2fad94585` |

Formato banner apposto:
- **6 .md**: HTML comment header a top-of-file (3 righe: title + short banner + SHA256 reference)
- **3 .py + 1 test.py**: docstring header nel primo docstring (3 righe interne al `"""..."""`)
- **2 .json**: `_seal` field top-level (Opzione A, schema-safe). JSON validity **verificata** post-banner via `json.load()` + sibling script `_load_registry()` verify.

---

## 6. Totale sigilli finali

**30 sealed files totali** ✅

Breakdown:
- **19 pre-existing** (11 R18.Reset.1b/1.2 + 5 R18.3d + 3 R18.3e new_5 documental) — byte-identical
- **11 new R18.4** (post-banner, hash registrati)

**Target PM = 30 · Delivered = 30 · Match ✅**

---

## 7. 19 sigilli pre-esistenti byte-identical (PRE vs POST B4)

Verifica in-process via `/app/backend/tests/backend_r18_4_sealed_integrity_test.py::test_r18_4_b4_seal_01_preexisting_19_byte_identical` (PASS ✅).

| # | Path (rel /app/) | SHA256 (invariato pre-post B4) |
|---|---|---|
| 1 | `backend/app/core/job_freeze.py` | `487c9223532c3016...` |
| 2 | `backend/app/scripts/round18_reset1b_apply_v1_1.py` | (registry) |
| 3 | `backend/app/scripts/round18_reset1b_apply_v1_2.py` | (registry) |
| 4 | `backend/app/scripts/round18_reset1b_apply_v1_3.py` | (registry) |
| 5 | `backend/app/scripts/round18_reset1b_staged_backup_materialize.py` | (registry) |
| 6 | `backend/app/scripts/round18_reset1c_field_cleanup.py` | (registry) |
| 7 | `backend/tests/backend_round1b_write_freeze_full_test.py` | (registry) |
| 8 | `backend/tests/backend_round1b_hotfix_starter_kit_test.py` | (registry) |
| 9 | `backend/tests/backend_round1b_hotfix_v1_2_starter_stats_test.py` | (registry) |
| 10 | `backend/tests/backend_round1b_hotfix_v1_3_schema_compat_test.py` | (registry) |
| 11 | `backend/tests/backend_r18_reset2_banner_dismiss_test.py` | (registry) |
| 12 | `backend/app/core/stat_role_registry.py` | `e1e083e3b923fcf5...` |
| 13 | `backend/app/scripts/round18_3d_apply_metadata.py` | `b439f429adabccf6...` |
| 14 | `backend/tests/backend_r18_3d_stat_role_registry_test.py` | `12ee2df331614798...` |
| 15 | `memory/r18_3d_stat_role_mapping_registry.json` | `3dec65cab59a92a3...` |
| 16 | `memory/r18_3d_stat_role_mapping_registry.md` | `2e360cfec4fa59db...` |
| 17 | `memory/r18_3e_bridge_registry.md` | `44f30612c559385e...` |
| 18 | `backend/app/scripts/round18_3e_apply_bridge.py` | (registry) |
| 19 | `memory/r18_3e_phase_b_final_closure_report.md` | (registry) |

**Verified**: `missing=0, mismatches=0` → **ALL 19 BYTE-IDENTICAL POST-B4 ✅**

Fonte hash pre-B4: `/app/memory/r18_3e_seal_registry.json` (registry aggregate R18.3e).
Verifica automatica in `test_r18_4_b4_seal_01_preexisting_19_byte_identical`.

---

## 8. 11 nuovi sigilli R18.4 (SHA256 registrati post-banner)

Vedi sezione 5 sopra per elenco completo.

Verifica automatica in `test_r18_4_b4_seal_02_new_11_byte_identical` (PASS ✅).
Test aggregato `test_r18_4_b4_seal_03_aggregate_count_30` conferma count = **30/30**.

---

## 9. Backup snapshots (hash-registered only, sealed=false)

**NOT part of the 30-file seal scope** — hash-registrati per audit trail.

```yaml
- backup_snapshot_path: /app/backend/backups/r18_4_slot_type_prepatch_20260706T052452Z/items_slot_type_snapshot.jsonl
  sha256:               17ca0efd4a66f41696b1bfdc42cfd96b3b8e575e03c9d1862692d3e0a85f118a
  created_at_utc:       2026-07-06T05:24:52Z
  item_count:           140
  sealed:               false
  reason:               "backup artifact, not part of 30-file seal scope"

- backup_snapshot_path: /app/backend/backups/r18_4_class_bound_prepatch_20260706T052500Z/items_class_bound_snapshot.jsonl
  sha256:               6cbd5a088ee6b7d2ea7296b7c58444d00b45e1c51b95cc5ef507420d89cec1d1
  created_at_utc:       2026-07-06T05:25:00Z
  item_count:           178
  sealed:               false
  reason:               "backup artifact, not part of 30-file seal scope"
```

---

## 10. JSON support artifacts (hash-registered only, sealed=false)

**NOT part of the 30-file seal scope** — hash-registrati per audit trail.

```yaml
- support_artifact_path: /app/memory/r18_4_phase_b3_dry_run_prereport.json
  sha256:                14864f6f289e1ce5e7cad3c0a01bd38cc8809d1db563f82b6757c19ca5b5990d
  created_at_utc:        2026-07-06T05:10:00Z
  verified_at_utc:       2026-07-06T07:20:00Z
  sealed:                false
  reason:                "support artifact (JSON), not part of 30-file seal scope; sibling .md is sealed"

- support_artifact_path: /app/memory/r18_4_phase_b3_real_apply_report.json
  sha256:                393d897b14992aa760f08ca08e6f27e8e3e18f206d84cd3bc9f64e270b75e94b
  created_at_utc:        2026-07-06T05:35:00Z
  verified_at_utc:       2026-07-06T07:20:00Z
  sealed:                false
  reason:                "support artifact (JSON), not part of 30-file seal scope; sibling .md is sealed"
```

---

## 11. Backlog P3 aggiunti pre-SEAL

Aggiunti in `/app/memory/backlog.md`:

| # | Backlog entry | Priority | Origin |
|---|---|---|---|
| 1 | `R18.4.backlog — Backfill Apply Idempotency Counter Pattern` | P3 | risk note #1 B3 real apply |
| 2 | `R18.4.backlog — Class-Bound Apply Zero-Write Audit Noise` | P3 | risk note #2 B3 real apply |
| 3 | `R18.4.followup — Public API serializer exposure of slot_type + item_binding_policy for UI activation` | P3 | tester POST-APPLY nota + PM directive |

Note: le 3 backlog P3 già create in B3 dry-run (Shield SQ1, spec_unlocks SQ2, berserker/assassin SQ4) restano confermate.

**Totale backlog P3 R18.4 aperti**: **6** (3 originali B3 + 3 nuovi B4).

---

## 12. Audit events reference (real apply eseguiti in B3)

| Event id | Event type | Apply | Modified count | Note |
|---|---|---|---|---|
| `c7c5016e-8764-42a0-882d-13be96e28e54` | `R18_4_SLOT_TYPE_BACKFILL_APPLIED` | slot_type | 140 | Primary apply, breakdown weapon:54/accessory:42/armor:44 |
| `53c73162-6649-4bbf-834e-474a01dda0d0` | `R18_4_ITEM_BINDING_POLICY_APPLIED` | class_bound | 178 | Primary apply, breakdown hard:11/soft:146/universal:21 |
| `1ec4f43b-56f7-4504-8dd3-bb143c0fba41` | `R18_4_ITEM_BINDING_POLICY_APPLIED` | class_bound rerun (idempotency) | 0 | already_correct=178, audit noise minor (risk note #2) |

Audit events emessi via `db.audit_log.insert_one` (bypass whitelist, pattern R18.3e).

---

## 13. Rollback dry-run readiness

Verificato in B3 real apply report (sez. 9).

| Component | Status |
|---|---|
| Backup snapshot slot_type (140 records) | ✅ presente + parsable |
| Backup snapshot class_bound (178 records) | ✅ presente + parsable |
| Rollback dry-run slot_type | ✅ `rollback_feasible: true`, found_in_db=140 |
| Rollback dry-run class_bound | ✅ `rollback_feasible: true`, found_in_db=178 |
| Rollback real path | NON attivato in B4 (nessuna necessità), disponibile via `--rollback-dry-run` flag |

---

## 14. Hard delete = 0 confermato

Nessun `delete_one`/`delete_many` chiamato durante l'intero flow R18.4 (B2 documental → B3 dry-run → B3 real apply → B4 SEAL). Verificato via code review + audit log inspection. Zero data loss.

---

## 15. Test R18.4 16/16 PASS (rerun post-banner)

```
$ pytest tests/backend_r18_4_class_bound_test.py
............... 16 passed in 0.90s ✅
```

Group breakdown post-banner:
- Registry shape (t01-t03): **3/3 PASS**
- Bucket derivation (t04-t07): **4/4 PASS**
- Backfill dry-run (t08-t11): **4/4 PASS**
- Class-bound dry-run (t12-t14): **3/3 PASS**
- Rate-limit + signals (t15-t16): **2/2 PASS**

**Nessuna regressione dal banner apposition.**

---

## 16. Regression R16.5.4b 24+3 invariata (rerun post-banner)

```
$ pytest tests/backend_round1654b_test.py
=================== 24 passed, 3 skipped, 1 warning in 2.08s ✅
```

Baseline invariata pre/post B4 apposition. Nessuna regression su compatibility/auto-equip.

---

## 17. Test verifica sigilli 30 SHA256 match confermato

Nuovo test statico creato: `/app/backend/tests/backend_r18_4_sealed_integrity_test.py`

```
$ pytest tests/backend_r18_4_sealed_integrity_test.py
..... 5 passed in 0.37s ✅

test_r18_4_b4_seal_01_preexisting_19_byte_identical    PASS ✅
test_r18_4_b4_seal_02_new_11_byte_identical            PASS ✅
test_r18_4_b4_seal_03_aggregate_count_30               PASS ✅
test_r18_4_b4_seal_04_hash_shape_validity              PASS ✅
test_r18_4_b4_seal_05_no_duplicate_paths               PASS ✅
```

**Nota**: il test statico `backend_r18_4_sealed_integrity_test.py` **NON è esso stesso sealed** (perché tracciare 30 hash all'interno di un file che deve avere un hash tra i 30 crea auto-referenza). Il test è mantenuto stabile via PM discretion; eventuali future evoluzioni (drift → aggiungere nuovi hash) sono gate-controllate.

SHA256 test statico (documental, non sealed):
`0b177a798a3610e6af869322739edb93baba67adac686ff7628fd29092f33706`

Cross-check parallelo: `pytest tests/backend_r18_3e_bridge_test.py::test_15_sealed_integrity_16_files` continua a PASS ✅ (16 file subset dei 19 esistenti).

---

## 18. Final status

# 🔒 **R18.4 CLOSED & SEALED**

- Total sealed files: **30/30** ✅
- Test suite: **16+5 = 21/21 PASS** ✅
- Regression baseline: **24+3 invariata** ✅
- Sigilli byte-identical: **19+11 = 30/30 verified** ✅
- Governance: NO scope creep, NO runtime enforcement, NO rename, NO delete, NO cambio target ✅
- Backlog P3: 6 entry attive per follow-up futuri ✅

**Round R18.4 chiuso ufficialmente**. Prossimo round richiede nuovo PM gate.

---

## 19. Recommendation for next round

### Opzione A — R18.5 (UI 4-state activation, high value user-facing)
- Attivare i signal `recommended_for_class` + `is_universal` nel `item_public()` serializer (SQ7 documentale già lockato).
- Impatto backend: `/api/items`, `/api/admin/items`, inventory item embed → esporre `slot_type` + `item_binding_policy` + derived signals.
- Impatto frontend: catalog cards con binding badges 4-state (block/warning/recommended/universal).
- Rif. backlog: `R18.4.followup — Public API serializer exposure`.
- Suggested phasing: A1 discovery lite → A2 serializer + tests → A3 UI badges + tests → A4 SEAL.

### Opzione B — R18.3f (Class Slug Migration Planning)
- Migrazione `adventurers.class_slug` legacy EN → canonical IT via bridge R18.3e (attualmente sealed documental).
- Impatto: adventurers collection write (fuori scope R18.4). Richiede PM gate esplicito.
- Rif. backlog: `R18.3f — Class Slug Migration Planning` (P2 pre-esistente).

### Opzione C — R18.4.backlog pickup (low-hanging follow-ups)
- Idempotency pattern alignment su `backfill_slot_type_apply` (risk note #1).
- Audit noise compressione su `class_bound_apply` rerun (risk note #2).
- Shield slot mapping revisit (SQ1).
- Specialization_unlocks branch cleanup (SQ2).
- Berserker/assassin dormant items revisit (SQ4).

**Raccomandazione agent**: **Opzione A (R18.5 UI 4-state)** per massima value delivery user-facing, coerente con lock documentale già completo di SQ7.

Decisione finale: attesa direttiva PM.

---

**Sigillo finale**: `🔒 R18.4 — Item Class-Bound Player-Facing — CLOSED & SEALED`  ·  **2026-07-06T07:20:00Z**
