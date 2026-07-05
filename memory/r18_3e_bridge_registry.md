<!--
═══════════════════════════════════════════════════════════════════════
🔒 CLOSED & SEALED — R18.3e Phase B — 2026-07-05T20:15:00Z UTC
🔒 SEAL AUTHORITY: PM Orchestrator
🔒 SEAL NOTE: Bridge registry chiuso post B2 real apply (18/18 doc
🔒 adventurer_classes, apply_id 35302c0c-98dc-4b3b-b5b2-f1646540b74a).
🔒 e1_tester post-B2 4/4 PASS. 3 WARN accettati da PM (governance notes:
🔒 bridge_source_round precisione, expedition write side-effect, dungeon
🔒 label i18n backlog). APPLY_ENABLED sibling re-locked = False. Rollback
🔒 sibling operativo (dry-run PASS 18/18). Byte-identical enforcement:
🔒 verify manuale con sha256sum + registry aggregate.
═══════════════════════════════════════════════════════════════════════
-->

# R18.3e Bridge Registry — Legacy EN ↔ Canonical IT Class Bridge

- **Registry**: R18.3e Legacy EN ↔ Canonical IT Class Bridge
- **Version**: R18.3e.v1
- **Round**: R18.3e Phase B — Stage B2 (real apply completed & sealed)
- **Timestamp UTC (creation)**: `2026-07-05T18:39:19Z`
- **Timestamp UTC (SEAL)**: `2026-07-05T20:15:00Z`
- **Seal Authority**: PM Orchestrator
- **Seal Status**: `CLOSED_AND_SEALED_R18_3E_PHASE_B` (post B2 apply reale + tester 4/4 PASS)
- **Reference decision lock**: `/app/memory/r18_3e_phase_b_pm_decisions.md`
- **Reference discovery Phase A**: `/app/memory/r18_3e_phase_a_legacy_canonical_bridge_discovery.md`
- **Reference canonical set (R18.3d)**: `/app/memory/r18_3d_stat_role_mapping_registry.json`
- **Runtime wired**: **NO** (documento memoria pura, nessun import runtime)

---

## Governance

| Vincolo | Valore |
|---|---|
| Unwired by design | ✅ True |
| Hard-stop field write check | ✅ True (13 field BLOCKED) |
| Player-facing change | ❌ False (bridge admin/design only) |
| Recruitment unlock | ❌ False |
| Migration slug | ❌ False |
| Audit event emitted | ❌ False (B1 documental-only zero-audit) |

---

## 27 Canonical IT (LOCKED — riferimento R18.3d Phase B registry)

alchimista · artificiere · astrologo · bardo · burattinaio · cacciatore_del_sangue · cacciatore_del_vuoto · cacciatore_di_mostri · cartografo · cavaliere_della_morte · cavaliere_di_draghi · cronista · druido · fabbro_arcano · giocatore_d_azzardo · guerriero · ladro · mago · mercante · monaco · negromante · paladino · parassita · pittore · runista · sciamano · sognatore

**Totale**: 27 slug canonical IT immutabili.

---

## Enum `bridge_status` (7 valori)

| Valore | Semantica |
|---|---|
| `mapped_canonical` | Legacy slug → canonical target diretto (mapping 1:1 chiaro) |
| `mapped_alias` | Legacy slug → canonical target come alias (deprecated_alias semantic o canonical hidden) |
| `deprecated_alias` | Legacy deprecato (is_active=False) con alias verso legacy/canonical vivo |
| `technical_placeholder` | Slug tecnico escluso dal canonical set (es. `recruit_unassigned`) |
| `test_artifact` | Slug residuo da test admin (es. `test-class-5e0064`) |
| `canonical_native` | Slug che è già una canonical IT del set 27 (es. `cacciatore_di_mostri`, `cacciatore_del_vuoto`) |
| `ambiguous_pending_pm` | Non ancora risolto (riservato, non usato in v1 — PM ha risolto tutte le Q3-Q8) |

---

## 5 SAFE Metadata Field (apply scope)

| Field | Tipo | Valori attesi | Reversibile |
|---|---|---|---|
| `canonical_slug` | `str \| null` | uno dei 27 canonical IT o `null` | ✅ `$unset` |
| `alias_target` | `str \| null` | slug target alias (es. `ladro`) o `null` | ✅ `$unset` |
| `bridge_status` | enum | uno dei 7 valori sopra | ✅ `$unset` |
| `bridge_source_round` | `str` | `"R18.3e Phase B"` (fisso) | ✅ `$unset` |
| `bridge_applied_at` | ISO datetime UTC | timestamp `$set` | ✅ `$unset` |

**Target collection**: `adventurer_classes` (18 doc live).
**Eligible apply**: tutti i 18 doc (16 legacy + 2 canonical native).

---

## 13 Blocked Fields Hard-Stop (mai toccati dal bridge)

`class_slug` · `display_name_it` · `primary_stat` · `secondary_stats` · `role` · `base_strength` · `base_agility` · `base_intellect` · `base_endurance` · `base_faith` · `is_playable` · `is_active` · `is_canonical` (+ `slug` e `name` come guard applicativo del script B2).

Il dry-run script R18.3e ha un guard fail-fast che rifiuta qualsiasi payload contenente questi field.

---

## Tabella Mapping Bridge (18 entries)

### Mapped Canonical (9 righe, HIGH confidence)

| Legacy slug | canonical_slug | alias_target | bridge_status | Adventurers live | display_name_it live | Explanation |
|---|---|---|---|---:|---|---|
| `warrior` | `guerriero` | `null` | `mapped_canonical` | 331 | Guerriero | display_name_it match, canonical target diretto. |
| `rogue` | `ladro` | `null` | `mapped_canonical` | 302 | Ladro | display_name_it match, canonical target diretto. |
| `mage` | `mago` | `null` | `mapped_canonical` | 281 | Mago | display_name_it match, canonical target diretto. |
| `monk` | `monaco` | `null` | `mapped_canonical` | 327 | Monaco | display_name_it match, canonical target diretto. |
| `paladin` | `paladino` | `null` | `mapped_canonical` | 303 | Paladino | display_name_it match. `primary_stat="faith"` drift locked live (R18.3d — non toccato). |
| `druid` | `druido` | `null` | `mapped_canonical` | 311 | Druido | display_name_it match, canonical target diretto. |
| `alchemist` | `alchimista` | `null` | `mapped_canonical` | 299 | Alchimista | display_name_it match, canonical target diretto. |
| `bard` | `bardo` | `null` | `mapped_canonical` | 324 | Bardo | display_name_it match. `role="Support"` drift deferred a `R18.3d.followup` (PM Q12). |
| `necromancer` | `negromante` | `null` | `mapped_canonical` | 0 | Negromante | display_name_it match. `is_active=False` deprecato silenziosamente. |

### Mapped Alias (3 righe, MEDIUM confidence)

| Legacy slug | canonical_slug | alias_target | bridge_status | Adventurers live | display_name_it live | Explanation |
|---|---|---|---|---:|---|---|
| `priest` | `paladino` | `paladino` | `mapped_alias` | 278 | **Sacerdote** | PM Q3: deprecated_alias semantic verso `paladino`. `display_name_it="Sacerdote"` **preservato** (no UI change). Player continua a vedere "Sacerdote" fino a round UI dedicato. |
| `ranger` | `cacciatore_di_mostri` | `null` | `mapped_alias` | 299 | **Ranger** | PM Q6: canonical hidden target (coerente con R18.3a orphan migration design intent). No recruitment unlock, no label change. |
| `warlock` | `cacciatore_del_vuoto` | `null` | `mapped_alias` | 305 | **Occultista** | PM Q6: canonical hidden target. No recruitment unlock, no label change. **18 items** già bindano `cacciatore_del_vuoto` via `recommended_classes`. |

### Deprecated Alias (2 righe, is_active=False)

| Legacy slug | canonical_slug | alias_target | bridge_status | Adventurers live | display_name_it live | Explanation |
|---|---|---|---|---:|---|---|
| `assassin` | `null` | `ladro` | `deprecated_alias` | 0 | Assassino | PM Q4: `is_active=False`. Spec `assassin_spec` è subspec di `rogue`. NO migration. |
| `berserker` | `null` | `guerriero` | `deprecated_alias` | 0 | Berserker | PM Q5: `is_active=False`. Spec `berserker_spec` è subspec di `warrior`. NO rewrite `items.class_tags`. |

### Technical Placeholder (1 riga)

| Legacy slug | canonical_slug | alias_target | bridge_status | Adventurers live | display_name_it live | Explanation |
|---|---|---|---|---:|---|---|
| `recruit_unassigned` | `null` | `null` | `technical_placeholder` | 0 | Da riassegnare | PM Q7: escluso dal canonical bridge. Hardcoded in `expeditions/services.py:907` guard e in `round181_schema_foundation.py`. |

### Test Artifact (1 riga)

| Legacy slug | canonical_slug | alias_target | bridge_status | Adventurers live | display_name_it live | Explanation |
|---|---|---|---|---:|---|---|
| `test-class-5e0064` | `null` | `null` | `test_artifact` | 0 | `null` | PM Q8: test artifact permanente. NO `delete_one`. |

### Canonical Native (2 righe — raccomandazione main agent, pending PM validation a gate B2)

| Slug | canonical_slug | alias_target | bridge_status | Adventurers live | display_name_it live | Explanation |
|---|---|---|---|---:|---|---|
| `cacciatore_di_mostri` | `cacciatore_di_mostri` (self) | `null` | `canonical_native` | 0 (adv) / **31 items** | Cacciatore di Mostri | Canonical IT del set 27. `is_playable=False`, `is_canonical=True`. Target di `ranger` alias. Raccomandazione main agent per auto-descrittività registry. |
| `cacciatore_del_vuoto` | `cacciatore_del_vuoto` (self) | `null` | `canonical_native` | 0 (adv) / **18 items** | Cacciatore del Vuoto | Canonical IT del set 27. `is_playable=False`, `is_canonical=True`. Target di `warlock` alias. Raccomandazione main agent per auto-descrittività registry. |

---

## Reverse Map Canonical → Legacy

| Canonical IT | Legacy source(s) |
|---|---|
| `guerriero` | `warrior`, `berserker` (deprecated_alias) |
| `ladro` | `rogue`, `assassin` (deprecated_alias) |
| `mago` | `mage` |
| `paladino` | `paladin`, `priest` (mapped_alias) |
| `monaco` | `monk` |
| `druido` | `druid` |
| `alchimista` | `alchemist` |
| `bardo` | `bard` |
| `negromante` | `necromancer` |
| `cacciatore_di_mostri` | `ranger` (mapped_alias), `cacciatore_di_mostri` (self, canonical_native) |
| `cacciatore_del_vuoto` | `warlock` (mapped_alias), `cacciatore_del_vuoto` (self, canonical_native) |

---

## 16 Canonical IT NON referenziate dal bridge

Le 16 canonical IT design-only non hanno legacy source mappato:

`artificiere` · `astrologo` · `burattinaio` · `cacciatore_del_sangue` · `cartografo` · `cavaliere_della_morte` · `cavaliere_di_draghi` · `cronista` · `fabbro_arcano` · `giocatore_d_azzardo` · `mercante` · `parassita` · `pittore` · `runista` · `sciamano` · `sognatore`

**Nota**: queste 16 restano canonical design-only, non presenti nel DB live. Sono target futuri di eventuali round di seed classi (fuori scope R18.3e).

---

## Backlog Entries Registered

- `R18.3d.followup — Bard Role Drift Resolution` (P3, già aperto)
- `R18.Backlog — Null Adventurer Class Slug Backfill Review` (P3, NEW da Q14)
- `R18.3f — Class Slug Migration Planning` (round deferred da Q9)

---

## Vincoli Assoluti (LOCKED)

- ❌ NO DB apply reale (bridge metadata)
- ❌ NO migration `class_slug`
- ❌ NO rewrite `adventurers` / `items`
- ❌ NO modifica frontend label player-facing
- ❌ NO unlock classi hidden
- ❌ NO seed nuove classi
- ❌ NO hard delete
- ❌ NO audit event emesso in B0/B1/B2 dry-run
- ❌ NO touch ai **16 sigilli** (14 R18.Reset.1b/1.2/1c + 2 R18.3d Phase B) — byte-identici obbligatori
