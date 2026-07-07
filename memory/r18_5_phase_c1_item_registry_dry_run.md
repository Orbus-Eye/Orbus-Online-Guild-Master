# R18.5 — Phase C1 · Item Registry Generation Dry-Run (STEP 31)

**Round**: R18.5 · **Phase**: C1 Item Registry Generation Dry-Run · **STEP**: 31
**Locked at UTC**: `2026-07-07T20:30:00Z`
**Governance**: **DOCUMENTAL ONLY — aggregate registry dry-run + differential report. NO modifica file D1-D5. NO runtime apply. NO DB writes. NO drop table apply.**
**Status**: ✅ **APPLIED — dry-run aggregate registry + differential**
**Authority**: PM Orchestrator — STEP 31 catena immediata post C0.L.1 (Q5+Q6=C+Q8 approved)

**Deliverables**:
- `/app/memory/r18_5_phase_c1_item_registry_dry_run.md` (questo file)
- `/app/memory/r18_5_phase_c1_item_registry_dry_run.json` (SHA256 `5e7860e427b0bf702c0664e9221d6de34efe18ee81279231061475a2664c551f`)

---

## Executive Summary

Il registry aggregato **C1** proietta i **1500 items** dai file source D1-D5 in uno schema unificato a **24 campi canonici**, aggiungendo 8 campi derivati/nuovi (progressive_marker, registry_status, runtime_apply_ready, class_slug/status, drop_table_ref, notes, class_proficiency rename) e escludendo 7 campi non-registry-canonical (rimangono nei file source). **Runtime apply = 0/1500** (dry-run design layer).

**Composition**:
- `registry_aggregated` = **1500** (schema unificato)
- `registry_applicable` = **1486** (esclude reserved + progressive_marker)
- `registry_reserved` = **4** (4 Progressive Discovery P1-P4)
- `progressive_marker` = **10** (T4 hint items — vedi ⚠️ discrepanza in Check #10)
- `runtime_apply_ready_count` = **0** (dry-run 100%)
- `anti_p2w_count` = **1500/1500**
- `class_slug_null_count` = **1500/1500** (Q8=A deferred_to_C5_R18_3f)

---

## Differential Report — D1-D5 → C1 Registry

### Nuovi campi aggiunti (delta vs source D1-D5)

- `class_proficiency (renamed from `classe_orientata` for registry canonical form)`
- `drop_table_ref (derived from `source` primary token)`
- `progressive_marker (bool, C0.L Sezione 3.6 pattern match)`
- `registry_status (applicable / reserved / progressive_marker)`
- `runtime_apply_ready (bool, false for 1500/1500 dry-run)`
- `class_slug (null 1500/1500)`
- `class_slug_resolution_status (deferred_to_C5_R18_3f 1500/1500)`
- `notes (per-item PENDING residue / marker rationale)`

### Campi source-only (mantenuti in D1-D5, non inclusi in registry canonical 24-fields)

- `iconic_family (kept in D1-D5 source, non incluso registry canonical 24-fields spec)`
- `is_tradeable (kept in D1-D5 source, non incluso registry canonical 24-fields spec)`
- `can_be_sold_for_gold (kept in D1-D5 source, non incluso registry canonical 24-fields spec — anti-P2W è can_be_sold_for_real_money)`
- `stat_principali (kept in D1-D5 source; numeric finals per Legendary in C0.L.1)`
- `lore_source (kept in D1-D5 source, non incluso registry 24-fields spec)`
- `chain_tag (D5-only, kept in D5 source)`
- `item_binding_policy (D5-only, kept in D5 source; bind-on-pickup per 15 legendary via C0.L)`


### Nota governance

Registry C1 = proiezione 24-fields specifica (Q6=C aggregato). File D1-D5 rimangono source of truth invariati. Registry C1 è dry-run design layer, runtime_apply_ready=false 1500/1500.

---

## Validation Report — 15 Check

| # | Check | Expected | Actual | Status |
|:--:|---|---|---|:--:|
| **1** | Catalog logical count = 1500 | 1500 | 1500 | ✅ |
| **2** | Applicable registry count | 1496 | 1486 | ⚠️ |
| **3** | Reserved registry count (progressive P1-P4) | 4 | 4 | ✅ |
| **4** | Rarity distribution 400/450/400/235/15 | {"common": 400, "uncommon": 450, "rare": 400, "epic": 235, "legendary": 15} | {"common": 400, "uncommon": 450, "rare": 400, "epic": 235, "legendary": 15} | ✅ |
| **5** | Class distribution 300×5 (W/R/M/P/Ranger) | {"Warrior": 300, "Rogue": 300, "Mage": 300, "Priest": 300, "Ranger": 300} | {"Warrior": 300, "Rogue": 300, "Mage": 300, "Priest": 300, "Ranger": 300} | ✅ |
| **6** | item_id uniqueness 1500/1500 | 0 | 0 | ✅ |
| **7** | nome_it uniqueness post-E2.1 | 0 | 0 | ✅ |
| **8** | Proficiency violations post-E1.1 fix | 0 | 0 | ✅ |
| **9** | Anti-P2W 1500/1500 (can_be_sold_for_real_money=false) | 1500 | 1500 | ✅ |
| **10** | progressive_marker=true flags | PM Q4=B: **6** · C0.L Sezione 3.6: **10** | 10 | ⚠️ |
| **11** | class_slug null + resolution_status deferred_to_C5_R18_3f 1500/1500 | 1500 | 1500 | ✅ |
| **12** | Legendary composition 11 design-ready + 4 registry_reserved | {"design_ready": 11, "reserved": 4} | {"design_ready": 11, "reserved": 4} | ✅ |
| **13** | Source/drop_table_ref mapping — cross-check con Batch 1-5 matrix | mappable | drop_table_ref derivato da `source` split[0] · non-null items = 1500 | ✅ |
| **14** | Registry_status distribution | {"applicable": 1486, "reserved": 4, "progressive_marker": 10} | {"applicable": 1486, "reserved": 4, "progressive_marker": 10} | ✅ |
| **15** | PM Open Questions pre-C2 | >=5 | 8 | ✅ |


### Note dettagliate

- **Check #2** (`applicable count`): expected 1496 nel prompt PM, actual **1486** — la differenza deriva da `progressive_marker_count=10` (non 6 come da wording Q4=B). Aritmetica: `1500 - 4 reserved - 10 progressive_marker = 1486`. **PM gate item** insieme a Check #10.
- **Check #10** (`progressive_marker=true flags`): **⚠️ DISCREPANZA** — Q4=B PM verbatim indica 6, C0.L Sezione 3.6 elenca 10 items (pattern `*-t4-legendary-*-hint`). **Governance-safe applicato**: `flag=true` sui 10 items dalla source-of-truth (`.json` C0.L Sezione 3.6). **Segnalato come PM gate item pre-C2**.

---

## Registry Status Distribution

| Bucket | Count |
|---|:--:|
| **applicable** | 1486 |
| **reserved** (P1-P4 Progressive Discovery) | 4 |
| **progressive_marker** (T4 hint items) | 10 |
| **TOTAL** | **1500** |

---

## Legendary Bucket · 15 / 15 status

### Design-ready registry — 11 items (7 APPROVED + 4 HYBRID)

- `warrior-t5-legendary-ambash-forge-hammer`
- `warrior-t5-legendary-dragon-elder-scale`
- `warrior-t5-legendary-dragonlord-crown`
- `rogue-t5-legendary-irthe-price-shroud-hybrid`
- `rogue-t5-legendary-void-touched-blade`
- `mage-t5-legendary-ergolat-obelisk-focus-hybrid`
- `mage-t5-legendary-sole-nero-diadem`
- `priest-t5-legendary-celestial-conclave-mantle-hybrid`
- `priest-t5-legendary-seraph-halo-crown`
- `ranger-t5-legendary-halodi-fate-quiver-hybrid`
- `ranger-t5-legendary-worldroot-scepter`

### Registry-reserved — 4 items (Progressive Discovery placeholder P1-P4)

- `rogue-t5-legendary-progressive-slot-03-pending`
- `mage-t5-legendary-progressive-slot-01-pending`
- `priest-t5-legendary-progressive-slot-02-pending`
- `ranger-t5-legendary-progressive-slot-04-pending`


---

## Sample rows — 24-fields canonical schema (rappresentativi)

Nota: il registry completo (1500 rows) è nel file `.json` associato, campo `registry_rows`. Qui sotto 5 sample cross-tier + 5 sample legendary + 2 sample T4 hint per verifica visiva schema.

### 5 sample cross-tier (uno per T1-T5 primo item)

| item_id | tier | rarity | class | slot | registry_status | progressive_marker | runtime_apply_ready | class_slug |
|---|:--:|:--:|:--:|---|:--:|:--:|:--:|:--:|
| `warrior-ironrecruit-blade` | T1 | Common | Warrior | main-hand | applicable | False | False | None |
| `warrior-ironsergeant-blade` | T2 | Common | Warrior | main-hand | applicable | False | False | None |
| `warrior-alevoran-recruit-blade` | T3 | Common | Warrior | main-hand | applicable | False | False | None |
| `warrior-t4-iron-legion-captain-blade` | T4 | Uncommon | Warrior | main-hand | applicable | False | False | None |
| `warrior-t5-legendary-ambash-forge-hammer` | T5 | Legendary | Warrior | main-hand | applicable | False | False | None |

### 5 sample Legendary

| item_id | class | slot | registry_status | notes |
|---|:--:|---|:--:|---|
| `warrior-t5-legendary-ambash-forge-hammer` | Warrior | main-hand | applicable | Legendary numeric finals in C0.L.1 (STEP 30); registry_apply_ready=false (dry-run design layer) |
| `warrior-t5-legendary-dragon-elder-scale` | Warrior | off-hand | applicable | Legendary numeric finals in C0.L.1 (STEP 30); registry_apply_ready=false (dry-run design layer) |
| `warrior-t5-legendary-dragonlord-crown` | Warrior | head | applicable | Legendary numeric finals in C0.L.1 (STEP 30); registry_apply_ready=false (dry-run design layer) |
| `rogue-t5-legendary-irthe-price-shroud-hybrid` | Rogue | chest | applicable | Legendary numeric finals in C0.L.1 (STEP 30); registry_apply_ready=false (dry-run design layer) |
| `rogue-t5-legendary-progressive-slot-03-pending` | Rogue | main-hand | reserved | Progressive Discovery placeholder = registry_reserved / PENDING PM / not_runtime_apply_ready (Q3=A) |

### 2 sample T4 progressive marker (`progressive_marker=true`)

| item_id | class | tier | rarity | registry_status |
|---|:--:|:--:|:--:|:--:|
| `warrior-t4-legendary-emberking-crown-hint` | Warrior | T4 | Epic | progressive_marker |
| `warrior-t4-legendary-void-touched-hint` | Warrior | T4 | Epic | progressive_marker |

---

## PM Open Questions pre-C2 Proficiency Runtime

| ID | Topic |
|:--:|---|
| **Q1** | Approvare C1 registry aggregato (1500 rows, 24 campi, dry-run design layer)? |
| **Q2** | Discrepanza `progressive_marker` count: Q4=B PM verbatim=6 vs C0.L Sezione 3.6=10 items → decisione: mantenere 10 (source of truth C0.L) o restringere a 6 (indicare quali 6)? |
| **Q3** | class_slug null + deferred_to_C5_R18_3f 1500/1500 confermato pre-C2 Proficiency Runtime? |
| **Q4** | HYBRID drop_rate 0.5% (H1-H4 in C0.L.1) da confermare/differenziare pre-C4 Drop Table? |
| **Q5** | Autorizzare Phase C2 Proficiency Runtime (runtime enforcement + integration engine)? |
| **Q6** | Notes per-item C1 vanno mantenute in registry v2 o spostate in un `notes_registry_c1.md` companion? |
| **Q7** | Registry `applicable` count 1500-4-10 = 1486 (o 1500-4-6 = 1490 se PM restringe a 6 marker) — quale target per C2? |
| **Q8** | Autorizzare PRD append `Phase C0.L.1 + C1 CLOSED` post-review? |


---

## Governance Check STEP 31

| Voce | Stato |
|---|:--:|
| **36 sigilli byte-identical** | ✅ VERIFIED pytest 6/6 |
| **DB writes** | ZERO |
| **Code changes** | ZERO |
| **Migrations** | ZERO |
| **Item table modification** | ZERO (D1-D5 read-only, registry è proiezione aggregata in nuovo file) |
| **Drop table apply** | ZERO |
| **class_slug auto-derivation** | ZERO (Q8=A deferral C5, `class_slug=null` 1500/1500) |
| **runtime_apply_ready** | ZERO 1500/1500 (dry-run design layer) |
| **Proficiency runtime enforcement** | ZERO (C2 out-of-scope) |
| **Anti-P2W runtime validator** | ZERO (C2 out-of-scope, design layer OK 1500/1500) |
| **R18.6 auto-start** | 🔒 BLOCKED (PLANNED) |
| **Marketing auto-start** | 🔒 BLOCKED (DEFERRED) |
| **C2 auto-start** | 🔒 BLOCKED (STOP after C1 per direttiva PM) |
| **Classi canoniche** | Warrior/Rogue/Mage/Priest/Ranger — NO drift |
| **Files deliverable** | ✅ 2 (`.md` + `.json`) |

---

## Stop after C1

- **`auto_transition_c2`**: `false`
- **Nota**: **STOP dopo C1. Attendo PM review pre-C2 Proficiency Runtime.**
