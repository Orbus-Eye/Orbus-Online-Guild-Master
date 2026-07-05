# R18.3d — Phase B · Pre-Report (Q10.b Correction Applied)

**Round**: `R18.3d` (Stat/Role Mapping Registry)
**Fase**: **B — Design-First Staged Apply (Q10.b Correction)**
**Data**: 2026-07-05T17:55:00Z UTC
**Autore**: e1_dev
**Stato**: ⏸ **STOP INTENZIONALE — attende verifica indipendente `e1_tester` e nuovo gate PM per B3 apply reale + B5 seal**

**Sistema live healthy**: freeze OFF, backend `Application startup complete`, `/api/health` 200.

---

## 0 · Correzione Q10.b applicata

**Motivazione**: il PM ha rigettato la struttura precedente (`18 live + 16 design-only = 34`) e ha imposto:

> `canonical_classes = 27` — 27 slug italiani verbatim LOCKED. Legacy live NON contano come canonical. Extra manifest esclusi con motivazione.

**Cambio struttura registry** (`R18.3d.v1` → `R18.3d.v2`):

| Sezione (v1) | Sezione (v2) | Delta |
|:---|:---|:---|
| `live_classes_18` | rimosso → sostituito | dei 18 live: 2 promossi a `canonical_classes` (slug identico) + 16 spostati in `legacy_live_classes` |
| `canonical_design_only_16` | rimosso → sostituito | 25 canoniche non-live in `canonical_classes` con `design_only=true` |
| — | `meta` (nuovo) | contiene tutti i count coerenti |
| — | `canonical_classes` (nuovo, 27) | 27 slug italiani LOCKED verbatim PM |
| — | `legacy_live_classes` (nuovo, 16) | classi live con `canonical_target=false` + eventuale alias |
| — | `excluded_manifest_entries` (nuovo, vuoto) | prevede motivazione per esclusioni future |

**Metadata count coerenti**:
- `canonical_classes` = **27** ✓
- `live_catalog_classes` = **18**
- `canonical_live_count` = **2** (cacciatore_di_mostri + cacciatore_del_vuoto, slug identici tra canonical e live)
- `legacy_live_classes_count` = **16**
- `design_only_classes_count` = **25** (27 - 2)
- `excluded_manifest_entries_count` = **0**

Nota: 27 canoniche PM = 27 dal manifest R18.0b, nessuna esclusione (`excluded_manifest_entries` = lista vuota by design).

---

## 1 · Decision lock file (invariato dalla v1)

| Path | Note |
|:---|:---|
| `/app/memory/r18_3d_phase_b_pm_decisions.md` | invariato — 10 risposte PM verbatim |
| `/app/memory/r18_3d_phase_b_pm_decisions.json` | invariato |

## 2 · Registry memory-only (v2 correzione Q10.b)

| Path | SHA256 |
|:---|:---|
| `/app/memory/r18_3d_stat_role_mapping_registry.json` | **`80f3bf9ea37cc146884db86cd0b7233a92ef21bd2b0e8a0a773f4aef9618431f`** |

**Contenuto**:
- `meta` con count coerenti (27/18/2/16/25/0)
- `stat_mapping_6_to_5` — 6→5 LOCKED (Q5)
- `role_system` — VALID_ROLES + role_display admin-only + tag taxonomy
- `canonical_classes` (27 entries) — slug italiani verbatim LOCKED
- `legacy_live_classes` (16 entries) — con `canonical_target=false`
- `excluded_manifest_entries` (0 entries, vuoto by design)
- `priority_critical_slugs` — 5 slug italiani (paladino, guerriero, ladro, + 2 cacciatori)
- `safe_metadata_fields_apply_scope` — con `eligible_apply_slugs=[cacciatore_di_mostri, cacciatore_del_vuoto]` + `legacy_live_slugs_hard_stop` (16)

## 3 · 27 canoniche coperte (slug verbatim locked)

`alchimista · artificiere · astrologo · bardo · burattinaio · cacciatore_del_sangue · cacciatore_del_vuoto · cacciatore_di_mostri · cartografo · cavaliere_della_morte · cavaliere_di_draghi · cronista · druido · fabbro_arcano · giocatore_d_azzardo · guerriero · ladro · mago · mercante · monaco · negromante · paladino · parassita · pittore · runista · sciamano · sognatore`

Ognuna con: `slug`, `class_name_it`, `design_primary_stat_it`, `design_secondary_stats_it`, `mapped_primary_stat_live`, `mapped_secondary_stats_live`, `role_atomic_candidate`, `role_display_it`, `class_role_tags`, `exists_in_live_db`, `has_live_alias`, `alias_from_live_slug`, `design_only`, `confidence`, `needs_PM_review`, `priority`, `notes`, `source_round`.

## 4 · 16 legacy live coperte (documentale, no runtime touch)

| # | live_slug | alias_target | needs_PM_review | note |
|:---:|:---|:---:|:---:|:---|
| 1 | warrior | guerriero | N | alias evidente |
| 2 | rogue | ladro | N | alias evidente |
| 3 | mage | mago | N | alias evidente |
| 4 | monk | monaco | N | alias evidente |
| 5 | paladin | paladino | N | alias evidente (faith Q9 accepted) |
| 6 | druid | druido | N | alias evidente |
| 7 | necromancer | negromante | N | alias evidente (is_active=false) |
| 8 | bard | bardo | **Y** | drift Q8 (role="Support") |
| 9 | alchemist | alchimista | N | alias evidente |
| 10 | priest | **null** | **Y** | no canonical counterpart |
| 11 | ranger | **null** | **Y** | ambiguous target |
| 12 | warlock | **null** | **Y** | ambiguous target |
| 13 | assassin | **null** | **Y** | ambiguous, is_active=false |
| 14 | berserker | **null** | **Y** | ambiguous, is_active=false |
| 15 | recruit_unassigned | null | N | placeholder, skip forever |
| 16 | test-class-5e0064 | null | N | test doc, skip forever |

Tutte con `canonical_target=false`, `legacy_live=true`, `migration_or_alias_pending=true` (tranne placeholder).

**Alias asegnati (9)**: warrior→guerriero, rogue→ladro, mage→mago, monk→monaco, paladin→paladino, druid→druido, necromancer→negromante, bard→bardo, alchemist→alchimista.
**Alias NON assegnati (7)**: priest, ranger, warlock, assassin, berserker (5 ambigui, marker `no_alias_reason`) + placeholder (2).

## 5 · Metadata SAFE dry-run status (post Q10.b)

**Comando**: `python -m app.scripts.round18_3d_apply_metadata --dry-run`
**Esito**: exit 0

**Output pertinente**:
```
── R18.3d Phase B3 · Apply Metadata (Q10.b canonical=27) ──
canonical_classes=27 live_catalog=18 canonical_live=2 legacy_live=16 design_only=25
plan: 2 canonical class(es) eligible (intersezione canonical ∩ live_catalog)
  · cacciatore_del_vuoto: [class_role_tags, design_primary_stat_it, design_secondary_stats_it, role_display_it, stat_role_registry_source_round]
  · cacciatore_di_mostri: [class_role_tags, design_primary_stat_it, design_secondary_stats_it, role_display_it, stat_role_registry_source_round]

DRY_RUN complete. No DB writes performed. exit=0
```

**Diff dry-run pre/post correzione**:

| Metrica | Pre-Q10.b (v1) | Post-Q10.b (v2) | Delta |
|:---|:---:|:---:|:---:|
| Plan count | 16 | **2** | **-14** |
| Slug in plan | warrior, rogue, mage, monk, paladin, druid, priest, ranger, warlock, bard, alchemist, necromancer, assassin, berserker, cacciatore_di_mostri, cacciatore_del_vuoto | cacciatore_del_vuoto, cacciatore_di_mostri | 16→2 |
| Legacy live nel plan | 14 slug legacy inclusi | **0** | ✓ hard-stop attivo |

## 6 · Metadata SAFE apply status

⏸ **NON eseguito** — attende gate PM esplicito.

## 7 · Test suite result

**Comando**: `pytest tests/backend_r18_3d_stat_role_registry_test.py -v`
**Esito**: ✅ **28/28 PASS** in 0.91s

| # | Test | Focus |
|:---:|:---|:---|
| 1 | mapping_6_to_5_locked (6 parametrized) | 6 mapping IT→live |
| 2 | registry_parses_meta_present | struttura v2 valida |
| 3 | canonical_27_locked | 27 slug italiani esatti |
| 4 | legacy_live_documented_separately | 16 legacy, no overlap con canonical |
| 5 | legacy_live_matches_db | 18 DB slugs = 16 legacy + 2 canonical∩live |
| 6 | excluded_manifest_entries_present | sezione esistente (empty by design) |
| 7 | safe_fields_scope | 5 SAFE + BLOCKED completi |
| 8 | eligible_apply_is_canonical_intersect_live | eligible=2, matches meta |
| 9 | registry_module_unwired | zero import runtime |
| 10 | no_player_facing_leak | zero leak in adventurers/services.py |
| 11 | bard_drift_documented | drift_flag + alias + backlog entry |
| 12 | paladin_faith_accepted | canonical paladino con faith + Holy |
| 13 | guard_hard_stop (4 parametrized) | rejects BLOCKED fields |
| 14 | legacy_live_hard_stop_in_plan | plan mai contiene legacy |
| 15 | dry_run_only_canonical_intersect_live | exit 0, count=2, no legacy in output |
| 16 | apply_without_ack_fails_30 | ack flag required |
| 17 | registry_sha256_computable | hash consistente |
| 18 | priority_critical_slugs | 5 critical in italiano |
| 19 | meta_counts_internally_consistent | tutti count coerenti |
| 20 | no_blocked_fields_in_canonical_entries | zero top-level BLOCKED |

**Delta test count**: v1 aveva 23 test, v2 ha 28 test (+5 nuovi: `legacy_live_matches_db`, `excluded_manifest_entries_present`, `eligible_apply_is_canonical_intersect_live`, `legacy_live_hard_stop_in_plan`, `meta_counts_internally_consistent`, `no_blocked_fields_in_canonical_entries` — 6 nuovi effettivi con 1 rimosso).

## 8 · Bard drift documented (evidenza post-Q10.b)

**Sezione legacy_live_classes** (16 entries), entry bard:
```json
{
  "live_slug": "bard", "live_role": "Support", "live_primary_stat": "intellect",
  "alias_target_canonical_slug": "bardo",
  "migration_or_alias_pending": true, "needs_PM_review": true,
  "legacy_live": true, "canonical_target": false,
  "drift_flag": "bard_role_support_not_in_valid_roles",
  "notes": "BARD DRIFT (Q8): live role='Support' NOT in VALID_ROLES..."
}
```

**Sezione canonical_classes**, entry bardo:
```json
{
  "slug": "bardo", "class_name_it": "Bardo",
  "role_atomic_candidate": "Healer_or_DPS",
  "role_display_it": "Support",
  "alias_from_live_slug": "bard",
  "drift_flag": "bard_alias_role_support_not_in_valid_roles",
  "needs_PM_review": true
}
```

**Backlog**: entry `R18.3d.followup — Bard Role Drift Resolution` presente in `/app/memory/backlog.md`.

## 9 · Paladin faith documented (evidenza post-Q10.b)

**Canonical entry `paladino`**:
```json
{
  "slug": "paladino", "class_name_it": "Paladino",
  "design_primary_stat_it": "Carisma",
  "design_secondary_stats_it": ["Forza", "Costituzione"],
  "mapped_primary_stat_live": "faith",
  "mapped_secondary_stats_live": ["strength", "endurance"],
  "role_atomic_candidate": "Tank",
  "role_display_it": "Healer/Tank",
  "class_role_tags": ["Healer", "Tank", "Support", "Holy"],
  "alias_from_live_slug": "paladin",
  "priority": "critical",
  "notes": "PM Q9 LOCKED: mapped_primary_stat_live=faith..."
}
```

**Legacy live entry `paladin`** (fonte SoT):
```json
{
  "live_slug": "paladin", "live_role": "Tank", "live_primary_stat": "faith",
  "alias_target_canonical_slug": "paladino",
  "notes": "paladin.primary_stat=faith (LIVE) accettato Q9. NO runtime touch."
}
```

Test `test_12_paladin_faith_accepted` PASS.

## 10 · Zero runtime wiring confirmation (invariato)

```
$ grep -rn "from app.core.stat_role_registry" backend/app/ | grep -v -E "stat_role_registry\.py|/tests/|/scripts/"
NONE
```

Nessun import runtime del modulo `stat_role_registry.py`.

Header commento nel modulo:
```
UNWIRED MODULE — DO NOT IMPORT FROM RUNTIME CODE PATHS WITHOUT NEW PM GO
```

## 11 · Raccomandazione seal/no-seal Phase B post-Q10.b

### Stato deliverable v2

| Componente | Stato | Note |
|:---|:---:|:---|
| B0 Decision Lock | ✅ COMPLETE (v1 invariato) | 10 risposte PM verbatim |
| B1 Registry v2 (27+16+0) | ✅ COMPLETE | 27 canonical LOCKED, 16 legacy separate |
| B2 Loader Python UNWIRED | ✅ UPDATED | Validation aggiornata per struttura v2 |
| B3 Sibling script v2 | ✅ COMPLETE (dry-run only) | Plan ridotto a 2, legacy hard-stop attivo |
| B4 Test suite v2 | ✅ **28/28 PASS** in 0.91s | +5 test nuovi Q10.b-specifici |
| B3 apply reale | ⏸ ATTENDE PM GATE | Non lanciato |
| B5 SEAL | ⏸ ATTENDE PM GATE | Non applicato |
| Backlog `R18.3d.followup Bard` | ✅ INSERITO | P3 |

### Verifica invariante Phase B (v2 vs baseline)

| Metrica | Baseline | Post-Q10.b | Delta |
|:---:|:---:|:---:|:---:|
| audit_log count | 11896 | **11896** | 0 ✅ |
| R18_3D_METADATA_APPLIED events | 0 | **0** | 0 ✅ |
| `cacciatore_di_mostri` 5 nuovi field | None×5 | **None×5** | 0 ✅ |
| `cacciatore_del_vuoto` 5 nuovi field | None×5 | **None×5** | 0 ✅ |
| `warrior` 5 nuovi field | None×5 | None×5 | 0 ✅ |
| 8 sigilli R18.Reset.1b | intatti | **intatti (test_t01 PASS)** | 0 ✅ |
| SEALED test file R18.Reset.2 | intatto | intatto | 0 ✅ |
| Runtime consumer di stat_role_registry | 0 | **0** | 0 ✅ |

### SHA256 file v2 (audit trail)

| Path | SHA256 (16 char) |
|:---|:---|
| `/app/memory/r18_3d_stat_role_mapping_registry.json` | `80f3bf9ea37cc146…` |
| `/app/backend/app/core/stat_role_registry.py` | `238aa0dbc5c6e920…` |
| `/app/backend/app/scripts/round18_3d_apply_metadata.py` | `1bb015a4825d9be0…` |
| `/app/backend/tests/backend_r18_3d_stat_role_registry_test.py` | `b2062ea7324e2af1…` |

### Giudizio tecnico (post-Q10.b)

**Raccomandazione**: ⏸ **STOP CONFORME — attende verifica indipendente `e1_tester` (7 punti PM) e nuovo gate PM per B3 apply reale + B5 SEAL.**

**Note tecniche importanti**:
1. Il **dry-run è ora significativamente più conservativo**: da 16 a 2 classi eligible. Le 14 rimosse (legacy inglesi) sono documentate in `legacy_live_classes` con `canonical_target=false`.
2. Le uniche 2 classi eligible sono i **cacciatori hidden** (`is_playable=false`, `migration_target_only=true`). Il B3 apply reale toccherebbe metadata puramente descrittivi su documenti non-player-facing.
3. **Alternativa "documental-only"** ora ancora più valida: dato che le 2 classi canonical∩live sono hidden e in TBD design, l'utilità pratica di applicare metadata al DB è marginale. Il registry JSON documentale è probabilmente sufficiente da solo.

### 7 punti verifica `e1_tester` (per riferimento)

1. registry canonico = 27 classi ✓ (test_3_canonical_27_locked)
2. nessuna classe extra non autorizzata ✓ (test_3 slug set assertion)
3. live legacy documentate separatamente, no double count ✓ (test_4)
4. 5 SAFE fields unici candidati ✓ (test_7)
5. dry-run no BLOCKED touch ✓ (test_13, test_15)
6. zero DB write pre-apply ✓ (audit_log 11896=11896)
7. test suite PASS ✓ (28/28)

---

**FASE B R18.3D (Q10.b corretta) — B0/B1/B2/B4 COMPLETI + B3 DRY-RUN 2 classi. STOP prima di apply reale e SEAL. Attende `e1_tester` + nuovo gate PM.**
