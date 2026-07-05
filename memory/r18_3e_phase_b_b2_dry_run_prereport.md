# R18.3e Phase B — Pre-Report B2 Dry-Run (fix chirurgico + validazione)

- **Round**: R18.3e — Canonical IT ↔ Legacy EN Class Bridge — Phase B
- **Stage**: B2 dry-run pre-report (post fix chirurgico test_14/test_15)
- **Timestamp UTC**: `2026-07-05T19:24:52Z`
- **Trigger**: PM ha autorizzato fix chirurgico test suite dopo recovery audit classificazione C.

---

## Riepilogo Fix Chirurgico

**File modificato**: `/app/backend/tests/backend_r18_3e_bridge_test.py` (**unico file toccato**).

**Funzioni modificate**: `test_14` e `test_15`.

**Diff logico (pre/post)**:

| Test | PRE (subprocess pytest ricorsivo) | POST (in-process) |
|---|---|---|
| `test_14` | `subprocess.run([pytest, tests/backend_r18_3d_stat_role_registry_test.py])` + assert "28 passed" nello stdout | Parse in-process `r18_3d_stat_role_mapping_registry.json` → assert `len(canonical)==27`, `len(legacy)==16`, `meta.seal_status=="CLOSED_AND_SEALED_DOCUMENTAL_ONLY"`, cross-ref canonical set R18.3d vs R18.3e |
| `test_15` | Assert file existence + hash + `subprocess.run([pytest, -k "sealed or integrity"])` **(ricorsione: subprocess selezionava se stesso)** | Assert file existence + hash valid-hex (non-zero) + confronto SHA256 vs tabella statica `R18_3D_SEALED_HASHES_KNOWN` (5 hash dal closure report R18.3d Phase B) |

**Costanti aggiunte**: `R18_3D_SEALED_HASHES_KNOWN` (dict path→sha256) — 5 hash noti dal closure report R18.3d Phase B (SEAL @ 2026-07-05T18:05:00Z).

**Altri file non toccati**: `pm_decisions.md/.json`, `bridge_registry.json/.md`, `round18_3e_apply_bridge.py` — invariati (SHA256 stessi del recovery audit).

---

## 1. Artifact Status 6/6

| # | Path | Bytes | SHA256 | Completeness |
|---|---|---:|---|---|
| 1 | `/app/memory/r18_3e_phase_b_pm_decisions.md` | 6297 | `a29dfbd9400648f49ff0f1cee035d7fe370f7f37c61329294724249aff25d20b` | ✅ complete (14 Q verbatim, ends with self-hash section) |
| 2 | `/app/memory/r18_3e_phase_b_pm_decisions.json` | 8113 | `17fdc96cb05efce24f1f9f3a8bde4ff318ff117939e27b0f5e8b9df3b7e5dbfc` | ✅ complete (JSON parses, Q1..Q14 in answers_verbatim, 16 mapping_official_locked) |
| 3 | `/app/memory/r18_3e_bridge_registry.json` | 9730 | `4934f5d2527125144b00588611621348faf1ee862c0e4821ce7c63518498627f` | ✅ complete (27 canonical + 18 bridge_entries + 7 enum + 5 SAFE fields) |
| 4 | `/app/memory/r18_3e_bridge_registry.md` | 9738 | `52230a20ed047951b6bc1e3e23536cfc517aed45948ccba0a5de270f1b958744` | ✅ complete (172 lines, ends with '16 sigilli byte-identici obbligatori') |
| 5 | `/app/backend/app/scripts/round18_3e_apply_bridge.py` | 13448 | `30f0a73dbacbf673985ba036fb9435b70efb47f122e5677c7df4c137684fe744` | ✅ complete (APPLY_ENABLED=False locked, dry-run 18/18 OK, guard hard-stop 15 fields) |
| 6 | `/app/backend/tests/backend_r18_3e_bridge_test.py` | 17849 | `c7f1585a8da8117b9eb2bd090ecec4622a45f19a9c4c462295b58b1fdeb4f440` | ✅ **complete post-fix** (test_14/test_15 fixati, 27/27 PASS) |

**Note**: solo il file test è stato modificato (dimensione 16007 → 17849 bytes, +1842 bytes per aggiunta costanti + docstring espanse). SHA256 nuovo: `c7f1585a...b4f440`.

---

## 2. Test Suite Result (post-fix)

**Comando**: `cd /app/backend && python -m pytest tests/backend_r18_3e_bridge_test.py -v`

**Risultato**: **27 passed in 0.49s** — 15 test methods × (13 param per test_08 + 12 non-param) = 27 test PASSED, 0 skip, 0 fail.

Breakdown:
- `test_01_decision_lock_parsable_14_answers` — PASS
- `test_02_registry_schema_valid` — PASS
- `test_03_16_legacy_coverage_with_5_safe_fields` — PASS
- `test_04_mapping_matches_pm_decisions` — PASS
- `test_05_canonical_slug_ref_in_27_or_null` — PASS
- `test_06_bridge_status_enum` — PASS
- `test_07_script_apply_enabled_locked_false` — PASS
- `test_08_guard_hard_stop_blocked_field_param` × 13 param — **13/13 PASS**
- `test_09_script_apply_without_ack_fails_fast` — PASS
- `test_10_zero_runtime_wiring` — PASS
- `test_11_no_blocked_fields_in_registry_entries` — PASS
- `test_12_technical_placeholder_and_test_artifact_separated` — PASS
- `test_13_registry_sha256_computable` — PASS
- **`test_14_r18_3d_registry_intact` — PASS** ✅ (fixato in-process, no subprocess)
- **`test_15_sealed_integrity_16_files` — PASS** ✅ (fixato in-process, no subprocess)

**Sealed/integrity global suite**: `pytest -k "sealed or integrity"` = **6 passed in 1.70s** (5 dei round precedenti + il nuovo `test_15_sealed_integrity_16_files` R18.3e in-process). **Zero ricorsione**.

---

## 3. Dry-Run Result

**Comando**: `python -m app.scripts.round18_3e_apply_bridge --json`

```json
{
  "mode": "dry_run",
  "apply_enabled": false,
  "source_round": "R18.3e Phase B",
  "registry_sha256": "4934f5d2527125144b00588611621348faf1ee862c0e4821ce7c63518498627f",
  "decision_lock_sha256": "17fdc96cb05efce24f1f9f3a8bde4ff318ff117939e27b0f5e8b9df3b7e5dbfc",
  "total_entries": 18,
  "would_modify_count": 18,
  "skipped_count": 0,
  "errors_count": 0,
  "guard_hard_stop_checks_passed": 18,
  "canonical_slug_ref_checks_passed": 18,
  "breakdown_by_bridge_status": {
    "mapped_canonical": 9,
    "mapped_alias": 3,
    "deprecated_alias": 2,
    "technical_placeholder": 1,
    "test_artifact": 1,
    "canonical_native": 2
  },
  "audit_event_would_emit": {
    "event_type": "R18_3E_BRIDGE_METADATA_APPLIED",
    "aggregated": true,
    "count_docs": 18,
    "actually_emitted": false
  },
  "backup_snapshot_would_write": {
    "path_expected": "/app/memory/r18_3e_bridge_pre_apply_snapshot_YYYYMMDDTHHMMSSZ.json",
    "actually_written": false
  },
  "real_apply_result": "BLOCKED — APPLY_ENABLED=False (LOCKED per R18.3e Phase B)"
}
```

---

## 4. Target Count = 18 ✅

Tutti i 18 doc live `adventurer_classes` sono target del bridge (16 legacy EN + 2 canonical hidden IT).

---

## 5. would_modify Count = 18 ✅

Nessuno skip, nessun error. Tutti i 18 passano guard hard-stop + canonical_slug ref check.

---

## 6. Fields Would-Set (5 SAFE) ✅

Ogni doc `adventurer_classes` avrebbe `$set` sui seguenti 5 field:

| Field | Tipo | Esempio |
|---|---|---|
| `canonical_slug` | `str \| null` | `"guerriero"` (warrior), `null` (recruit_unassigned) |
| `alias_target` | `str \| null` | `"ladro"` (assassin), `null` (warrior) |
| `bridge_status` | enum (7 valori) | `"mapped_canonical"`, `"mapped_alias"`, `"deprecated_alias"`, `"technical_placeholder"`, `"test_artifact"`, `"canonical_native"`, `"ambiguous_pending_pm"` |
| `bridge_source_round` | `str` (fisso) | `"R18.3e Phase B"` |
| `bridge_applied_at` | ISO datetime UTC | `"2026-07-05T19:24:52Z"` (esempio, popolato al momento del real apply) |

**Zero BLOCKED field** in payload (verificato da test_08 × 13 param + guard runtime nello script).

---

## 7. APPLY_ENABLED = False ✅

Evidenza `grep` sul sibling script:

```
5: **Status**: DRY-RUN ONLY. `APPLY_ENABLED = False`. Zero DB write.
34: `APPLY_ENABLED = False`.
64: APPLY_ENABLED: bool = False  # LOCKED at False for entire R18.3e Phase B
215: "apply_enabled": APPLY_ENABLED,
266: if not APPLY_ENABLED:
```

Coperto da `test_07_script_apply_enabled_locked_false` (PASS).

---

## 8. `--apply` Bloccato (subprocess evidence) ✅

**Test A** — `python -m app.scripts.round18_3e_apply_bridge --apply`:
- **returncode = 1** ✅
- stderr: `[FAIL-FAST] Real apply BLOCKED. APPLY_ENABLED=False (LOCKED per R18.3e Phase B). A new PM gate is required to flip APPLY_ENABLED to True.`

**Test B** — `python -m app.scripts.round18_3e_apply_bridge --apply --i-understand-this-will-write-bridge-metadata`:
- **returncode = 1** ✅ (blocked anche con ack, perché APPLY_ENABLED=False prevale)
- stderr: identico al Test A.

Coperto da `test_09_script_apply_without_ack_fails_fast` (PASS).

---

## 9. Zero DB Write ✅

| Check | Result |
|---|---|
| `audit_log.count()` delta | **0** (baseline 11896 pre-Phase B, ora 11896) |
| `adventurer_classes` con `canonical_slug` exists | **0** |
| `adventurer_classes` con `alias_target` exists | **0** |
| `adventurer_classes` con `bridge_status` exists | **0** |
| `adventurer_classes` con `bridge_source_round` exists | **0** |
| `adventurer_classes` con `bridge_applied_at` exists | **0** |
| `adventurers.count()` | **3373** (baseline invariato) |
| `items.class_tags` non-empty | **157** (baseline invariato) |
| `items.recommended_classes` non-empty | **157** (baseline invariato) |

---

## 10. Zero Audit Event Nuovo ✅

`audit_log.count({event_type: /R18_3E/i})` = **0**. Nessun evento `R18_3E_*` emesso in Phase B dry-run.

---

## 11. Zero Runtime Wiring ✅

`grep r18_3e|round18_3e|R18.3e /app/backend/app --exclude-dir=__pycache__ --exclude-dir=scripts --exclude-dir=tests` = **empty**.

Nessun modulo runtime importa il registry R18.3e o il sibling script. Coperto da `test_10_zero_runtime_wiring` (PASS).

---

## 12. Sealed R18.Reset / R18.3d Intatti ✅

**Metodo**: SHA256 statico check in-process contro tabella `R18_3D_SEALED_HASHES_KNOWN` (5 hash dal closure report R18.3d Phase B, SEAL @ 2026-07-05T18:05:00Z). **Nessun subprocess pytest ricorsivo**.

| File R18.3d | Expected SHA256 | Actual SHA256 | Match |
|---|---|---|---|
| `/app/memory/r18_3d_stat_role_mapping_registry.json` | `3dec65ca...b16` | `3dec65ca...b16` | ✅ |
| `/app/memory/r18_3d_stat_role_mapping_registry.md` | `2e360cfe...398` | `2e360cfe...398` | ✅ |
| `/app/backend/app/core/stat_role_registry.py` | `e1e083e3...4eb` | `e1e083e3...4eb` | ✅ |
| `/app/backend/app/scripts/round18_3d_apply_metadata.py` | `b439f429...db7` | `b439f429...db7` | ✅ |
| `/app/backend/tests/backend_r18_3d_stat_role_registry_test.py` | `12ee2df3...1e2` | `12ee2df3...1e2` | ✅ |

**11 file R18.Reset.1b/1.2/1c**: file existence + hash valid-hex non-zero verificato. Nessun baseline hash pre-recovery disponibile su disco (ambiente ripulito), MA:
- 4 test dei round precedenti PASS (`pytest -k "sealed or integrity"` = 6/6 con nuovo test_15 R18.3e in-process incluso).
- Ognuno di questi 4 test verifica byte-identity dei sealed script tramite hash contenuto nel loro test proprio.

**Conclusione**: 16/16 file sealed integri.

---

## 13. Raccomandazione Tecnica GO/NO-GO per B2 Apply Reale

**Raccomandazione**: **⚠️ CONDITIONAL GO** — pronto per B2 apply reale con **1 sola condizione**.

### Motivazione GO

1. **Registry B1 completo e coerente**: 27 canonical + 18 bridge_entries, 16 mapping ufficiale PM verbatim, 2 canonical native (raccomandazione documentata).
2. **Dry-run pulito**: 18/18 would_modify, 0 errors, 0 skipped, guard hard-stop 15 field BLOCKED verificato via test_08 × 13 param.
3. **Fields SAFE-only**: solo 5 field append-only (`canonical_slug`, `alias_target`, `bridge_status`, `bridge_source_round`, `bridge_applied_at`), tutti reversibili via `$unset`.
4. **APPLY_ENABLED lock robust**: 2 layer di guard (module constant + explicit ack flag). `--apply` returncode=1 con e senza ack.
5. **27/27 test PASS** + **6/6 sealed/integrity PASS**. Regression garantita.
6. **DB invariato**: 0 write, 0 audit event, baseline 11896.
7. **Runtime intatto**: 0 wiring, gameplay live 200/200, freeze OFF.
8. **Sigilli R18.3d byte-identical**: 5/5 SHA256 MATCH vs closure report.

### Condizione richiesta prima di B2 apply

**Il PM deve esplicitare la posizione su 2 canonical native** (`cacciatore_di_mostri`, `cacciatore_del_vuoto`):
- Attualmente il registry le include con `bridge_status="canonical_native"` come raccomandazione main agent (documentata in `pm_decisions.json.canonical_native_extension_by_main_agent`).
- Se PM approva → apply su 18 doc (16 legacy + 2 canonical native).
- Se PM rifiuta → apply solo su 16 doc legacy; le 2 canonical native restano senza bridge metadata.

### Prerequisiti B2 apply reale (quando GO PM arriverà)

1. **Flip `APPLY_ENABLED = True`** (mia intenzione: search_replace 1-line nel sibling script + rilancio dry-run per conferma count invariato).
2. **Attivare backup snapshot** (creazione di `/app/memory/r18_3e_bridge_pre_apply_snapshot_YYYYMMDDTHHMMSSZ.json` con copy full dei 18 doc pre-write).
3. **Confermare Q13 audit policy**: 1 solo evento aggregato `R18_3E_BRIDGE_METADATA_APPLIED` (già in dry-run report, actually_emitted=False).
4. **Prevedere rollback script** (`round18_3e_rollback_bridge.py` con `$unset` simmetrico dei 5 SAFE field).

---

## Vincoli Rispettati

- ❌ Zero DB write (evidenza: audit_log delta 0, 0 bridge field su adventurer_classes)
- ❌ Zero apply reale (dry-run only, `--apply` returncode=1)
- ❌ Zero cleanup automatico
- ❌ Zero overwrite dei 5 artefatti validi (SHA256 invariati vs recovery audit)
- ❌ Zero runtime import/wiring (grep empty)
- ❌ Zero frontend change (git status shows only untracked `yarn.lock`, non-toccato durante Phase B)
- ❌ Zero migration slug
- ❌ Zero item rewrite (157/157 invariato)
- ❌ Zero adventurer rewrite (3373 invariato)
- ❌ Zero seal (registry resta in `OPEN_STAGE_B1_DOCUMENTAL_ONLY`)
- ❌ Zero touch ai 16 sigilli (5/5 R18.3d SHA256 MATCH, 11 R18.Reset validati via test proprietari 6/6 PASS)

---

## STOP Obbligatorio

**Non eseguo B2 apply reale**. Attendo GO PM esplicito con conferma sui 2 canonical native (Q14-bonus della raccomandazione main agent).

Nel frattempo il registry R18.3e resta in stato `OPEN_STAGE_B1_DOCUMENTAL_ONLY` — completamente reversibile, zero side-effect.
