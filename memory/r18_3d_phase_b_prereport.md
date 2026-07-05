# R18.3d — Phase B · Pre-Report (STOP prima di B3 apply reale e B5 seal)

**Round**: `R18.3d` (Stat/Role Mapping Registry)
**Fase**: **B — Design-First Staged Apply**
**Data**: 2026-07-05T17:35:00Z UTC
**Autore**: e1_dev
**Stato**: ⏸ **STOP INTENZIONALE — attende gate PM per B3 apply reale + B5 seal**

**Sistema live healthy**: freeze OFF, backend `Application startup complete`, `/api/health` 200.

---

## 1 · Decision lock file creato

| Path | SHA256 |
|:---|:---|
| `/app/memory/r18_3d_phase_b_pm_decisions.md` | `fac05e2105505f877df5adee29866d0f9bb07c983e2b51cb27f2def49eafd8cd` |
| `/app/memory/r18_3d_phase_b_pm_decisions.json` | `7fba304f43b0e29fc86cf0a58000fbcecb56557ceee3b41a2212ab138c35443b` |

**Contenuto**: 10 risposte PM verbatim (Q1-Q10) + vincoli assoluti LOCKED. Nota agente su discrepanza conteggio 27/18/9 documentata in Q10 come `PM_clarification_needed_Q10_refinement`.

## 2 · Registry memory-only creato

| Path | SHA256 |
|:---|:---|
| `/app/memory/r18_3d_stat_role_mapping_registry.json` | `7e0f3f610787d0f47fdca507fd4c22b373764a378636e7f86722abcf0b377227` |

**Coverage**:
- **18 live classes** (elenco completo con `class_slug`, mapping IT→5-stat, `role_atomic_candidate`, `role_display_it`, `class_role_tags`, `confidence`, `needs_PM_review`, `notes`)
- **16 canonical design-only** (elenco completo dal source `orbus_r18_27_class_sources_manifest`, tutti con `design_only=true`, `in_live_db=false`)
- **Priority critical** (5): `paladin, warrior, rogue, cacciatore_di_mostri, cacciatore_del_vuoto`
- **Governance**: registry = DOCUMENTAL + ADMIN INTROSPECTION ONLY (Q4). `adventurer_classes` resta SoT live.
- **Stat mapping 6→5**: LOCKED (Q5), incluse collisioni Saggezza→intellect e Carisma→faith.
- **Role system**: `VALID_ROLES=(Tank,DPS,Healer)`, `role_display_it_candidate` admin-only (Q2), `class_role_tags_taxonomy` di 27 tag.

## 3 · 18 live classi coperte (elenco slug)

| # | slug | in_canonical_27 | priority | note breve |
|:---:|:---|:---:|:---:|:---|
| 1 | warrior | ✓ | critical | mapped strength |
| 2 | rogue | ✓ | critical | mapped agility |
| 3 | mage | ✓ | normal | mapped intellect |
| 4 | monk | ✓ | normal | mapped agility |
| 5 | paladin | ✓ | critical | **Q9 LOCKED faith** |
| 6 | druid | ✓ | normal | Carisma → faith |
| 7 | priest | ✗ | normal | LIVE ORPHAN, ~190 adv |
| 8 | ranger | ✗ | normal | LIVE ORPHAN, ~175 adv |
| 9 | warlock | ✗ | normal | LIVE ORPHAN, ~128 adv |
| 10 | bard | ✓ | normal | **Q8 drift Support** |
| 11 | alchemist | ✓ | normal | canonical alignment |
| 12 | necromancer | ✓ | normal | is_active=false |
| 13 | assassin | ✗ | normal | ORPHAN INACTIVE |
| 14 | berserker | ✗ | normal | ORPHAN INACTIVE |
| 15 | cacciatore_di_mostri | ✓ | critical | HIDDEN TBD |
| 16 | cacciatore_del_vuoto | ✓ | critical | HIDDEN TBD |
| 17 | recruit_unassigned | ✗ | placeholder | SKIP APPLY |
| 18 | test-class-5e0064 | ✗ | test-doc | SKIP APPLY |

## 4 · 16 canonical design-only coperte (elenco slug)

`artificiere · astrologo · burattinaio · cacciatore_del_sangue · cartografo · cavaliere_della_morte · cavaliere_di_draghi · cronista · fabbro_arcano · giocatore_dazzardo · mercante · parassita · pittore · runista · sciamano · sognatore`

Tutte con `design_only=true`, `in_live_db=false`, slug candidato non-finale (sarà confermato in round dedicato R18.3e o simili).

## 5 · Metadata SAFE dry-run status

**Comando eseguito**:
```
python -m app.scripts.round18_3d_apply_metadata --dry-run
```

**Esito**: exit 0

**Plan**:
- 18 live classes analyzed
- **16 eligible** (esclusi 2 skip: `recruit_unassigned`, `test-class-5e0064`)
- Ogni entry riceverebbe 5 SAFE fields via `$set`: `role_display_it, class_role_tags, design_primary_stat_it, design_secondary_stats_it, stat_role_registry_source_round`
- Guard hard-stop: **nessun BLOCKED field nel payload** (auto-check passed)
- Nessuna scrittura al DB (dry-run mode)

**Output completo dry-run** (16 classi elencate con payload keys byte-exact) in log agente.

## 6 · Metadata SAFE apply status

⏸ **NON eseguito** — attende gate PM esplicito per B3 apply reale (`--apply --i-understand-this-will-write-metadata`).

Backup snapshot pre-apply predisposto (path derivato `/app/backend/backups/r18_3d_metadata_<apply_id>/adventurer_classes_pre_apply_<ts>.jsonl`) ma non generato in dry-run.

Verifica DB pre-apply:
- `audit_log` count: **11896** (invariato da Phase A baseline)
- `R18_3D_METADATA_APPLIED` events count: **0** (nessun apply avvenuto)
- `adventurer_classes.warrior` — tutti i 5 nuovi field valgono `None` (non ancora applicati)

## 7 · Test suite result

**Comando**: `pytest tests/backend_r18_3d_stat_role_registry_test.py -v`

**Esito**: ✅ **23/23 PASS** in 0.90s

| Test | Esito |
|:---|:---:|
| test_1_mapping_6_to_5_locked (6 parametrized) | PASS × 6 |
| test_2_registry_parses | PASS |
| test_3_live_classes_18_match_db | PASS |
| test_4_canonical_design_only_16 | PASS |
| test_5_apply_script_scope_safe_only | PASS |
| test_6_registry_module_unwired | PASS |
| test_7_no_player_facing_leak | PASS |
| test_8_bard_drift_documented | PASS |
| test_9_paladin_faith_accepted | PASS |
| test_10_guard_hard_stop_blocked_field (4 parametrized) | PASS × 4 |
| test_11_apply_script_dry_run_exit_0 | PASS |
| test_12_apply_without_ack_fails_30 | PASS |
| test_13_registry_sha256_computable | PASS |
| test_14_get_stat_role_mapping_helper | PASS |
| test_15_priority_critical_slugs | PASS |

## 8 · Bard drift documented (evidenza)

**Registry entry** (`/app/memory/r18_3d_stat_role_mapping_registry.json`, sezione `live_classes_18`):
```json
{
  "class_slug": "bard",
  "role_atomic_candidate": "Healer_or_DPS",
  "role_display_it": "Support",
  "class_role_tags": ["Support", "Buffer", "Debuffer", "Utility"],
  "needs_PM_review": true,
  "drift_flag": "bard_role_support_not_in_valid_roles",
  "notes": "BARD DRIFT (PM Q8): DB has role='Support' NOT in VALID_ROLES (Tank/DPS/Healer). PM decision: leave drift documented, NO fix on bard.role in Phase B. role_atomic_candidate is a hint (probably Healer or DPS), not applied. Backlog entry: R18.3d.followup — Bard Role Drift Resolution"
}
```

**Backlog entry**: `/app/memory/backlog.md` sezione `[BACKLOG] R18.3d.followup — Bard Role Drift Resolution` (P3, Status BACKLOG).

## 9 · Paladin faith documented (evidenza)

**Registry entry**:
```json
{
  "class_slug": "paladin",
  "class_name_it": "Paladino",
  "priority": "critical",
  "design_primary_stat_it": "Carisma",
  "design_secondary_stats_it": ["Forza", "Costituzione"],
  "mapped_primary_stat_live": "faith",
  "mapped_secondary_stats_live": ["strength", "endurance"],
  "role_atomic_candidate": "Tank",
  "role_display_it": "Healer/Tank",
  "class_role_tags": ["Healer", "Tank", "Support", "Holy"],
  "needs_PM_review": false,
  "notes": "PM Q9 LOCKED: Paladin primary_stat=faith (live catalog SoT); do NOT touch R15 seed; hybrid Tank/Support/Holy via class_role_tags"
}
```

Test `test_9_paladin_faith_accepted` PASS: verifica byte-exact di `mapped_primary_stat_live=faith`, `design_primary_stat_it=Carisma`, `role_display_it=Healer/Tank`, `class_role_tags` include `Holy` e `Support`.

## 10 · Zero runtime wiring confirmation

**Grep output** (`app.core.stat_role_registry` import scan):

```
$ rg "from app.core.stat_role_registry|import stat_role_registry" backend/app/
# results (excluding module itself, tests/, scripts/):
NONE
```

**Il modulo `stat_role_registry.py` NON è importato da nessun runtime code path** (auto-equip, xp_modifier, combat, sorting, recruitment, matchmaking). L'unico import è dal test suite dedicato (`backend_r18_3d_stat_role_registry_test.py`), conforme alla policy PM Q4.

Header commento nel modulo:
```
UNWIRED MODULE — DO NOT IMPORT FROM RUNTIME CODE PATHS WITHOUT NEW PM GO
```

## 11 · Raccomandazione seal/no-seal R18.3d Phase B (giudizio tecnico)

### Stato deliverable

| Componente | Stato | Note |
|:---|:---:|:---|
| B0 Decision Lock (MD+JSON) | ✅ COMPLETE | 10 risposte PM verbatim, SHA256 tracciato |
| B1 Registry memory-only (JSON) | ✅ COMPLETE | 18 live + 16 design-only + governance |
| B2 Loader Python read-only unwired | ✅ COMPLETE | `stat_role_registry.py`, zero import runtime |
| B3 Sealed script apply (sibling, not sealed) | ✅ COMPLETE (dry-run only) | Doppio flag + guard hard-stop testato |
| B4 Test suite | ✅ 23/23 PASS | Coverage completa dei 10 punti self-check |
| B3 apply reale al DB | ⏸ ATTENDE PM GATE | Non lanciato in autonomia |
| B5 SEAL | ⏸ ATTENDE PM GATE | Non applicato |
| Backlog `R18.3d.followup Bard` | ✅ INSERITO | Backlog entry P3 aggiornata |

### Verifica invariante Phase B (delta vs Phase A)

| Metrica | Phase A baseline | Fine Phase B (STOP) | Delta |
|:---:|:---:|:---:|:---:|
| audit_log count | 11896 | 11896 | 0 ✅ |
| R18_3D_METADATA_APPLIED events | 0 | 0 | 0 ✅ |
| adventurer_classes.warrior nuovi field | None×5 | None×5 | 0 ✅ |
| 8 sigilli R18.Reset.1b | intatti | intatti | 0 ✅ |
| SEALED test file R18.Reset.2 | intatto | intatto | 0 ✅ |
| Frontend player-facing UI | invariato | invariato | 0 ✅ |
| Route/endpoint | 0 nuovi | 0 nuovi | 0 ✅ |
| Runtime consumer di `stat_role_registry.py` | 0 | 0 | 0 ✅ |

### Giudizio tecnico

**Raccomandazione**: ⏸ **STOP CONFORME — non procedere con B3 apply reale né B5 SEAL senza gate PM esplicito.**

**Motivazione**:
1. Tutti i deliverable memory-first (B0, B1, B2, B4) sono completi, testati, conformi ai vincoli LOCKED.
2. Il dry-run B3 conferma la planning: **16 classi eligible, zero touch a runtime field, guard hard-stop funzionante**.
3. Il B3 apply reale è idempotente e reversibile (`$unset` sui 5 field SAFE), ma essendo il **primo write al DB del round**, la responsabilità della GO deve restare al PM.
4. B5 SEAL richiede audit indipendente e conferma esplicita che nessuno degli 8 sigilli R18.Reset.1b sia stato compromesso — richiedibile via `e1_tester` o subagent testing.

**Se PM autorizza B3 apply reale**:
```
cd /app/backend && python -m app.scripts.round18_3d_apply_metadata \
  --apply \
  --i-understand-this-will-write-metadata
```
Aspettato: 16 modified, 0 skipped_no_doc, 1 audit event `R18_3D_METADATA_APPLIED`, 1 backup snapshot in `/app/backend/backups/r18_3d_metadata_<apply_id>/`.

**Se PM autorizza B5 SEAL**:
1. Sealed header su `round18_3d_apply_metadata.py` (rename semantica sibling → sealed)
2. Sealed header su `backend_r18_3d_stat_role_registry_test.py`
3. SHA256 registry JSON registrato in nuovo file `/app/memory/r18_3d_seal_registry.json`
4. Update PRD.md sezione "R18.3d — CLOSED & SEALED"
5. Closure report finale `/app/memory/r18_3d_final_closure_report.md`

### Domande residue per PM (opzionale gate B3/B5)

- **Refinement Q10**: la lista 16 canonical design-only proposta (da `orbus_r18_27_class_sources_manifest`) è ok o preferisce lista 9 diversamente selezionata? Se ok, procedo con B5.
- **Bard drift**: confermi che il `role_atomic_candidate="Healer_or_DPS"` è OK come hint pending, o preferisce hint singolo? (attualmente non applicato).
- **Delta apply**: preferisce B3 apply subito o solo B5 seal (registry documental only, no DB write mai)?

---

**FASE B R18.3D — B0/B1/B2/B4 COMPLETI + B3 DRY-RUN OK. STOP prima di B3 apply reale e B5 SEAL. Attende gate PM.**
