# R18.3d Phase B — Final Closure Report (Documental-Only SEAL)

- **Round**: R18.3d — Stat/Role Mapping Registry — Phase B
- **Chiusura tipo**: DOCUMENTAL-ONLY SEAL (NO DB APPLY)
- **Timestamp SEAL (UTC)**: `2026-07-05T18:05:00Z`
- **Seal Authority**: PM Orchestrator
- **Report generato (UTC)**: `2026-07-05T18:06:50Z`

---

## 1. MD companion creato

- **Path**: `/app/memory/r18_3d_stat_role_mapping_registry.md`
- **SHA256**: `2e360cfec4fa59db0f57e6a6dec6332eb6bca9d589d923ca27552cc16937c398`
- **Ruolo**: gemello human-readable del registry JSON, contiene stat mapping 6→5, role system, 27 canonical classes, 16 legacy live, drift documentation (bard, paladin), safe fields scope, hard-stop rules.
- **Wired to runtime**: NO. Documento memoria pura (nessun import).

---

## 2. R18.3d Phase B seal status

- **Status**: `CLOSED_AND_SEALED_DOCUMENTAL_ONLY` ✅
- **Sealed at (UTC)**: `2026-07-05T18:05:00Z`
- **Seal note**: *"Closed as documental-only registry. No DB metadata apply executed."*
- **Registry version**: `R18.3d.v2` (Q10.b correction applied — 27 canonical + 16 legacy)

### File sigillati (SHA256 finali post-seal)

| # | File | SHA256 | Banner "CLOSED & SEALED" |
|---|---|---|---|
| 1 | `/app/memory/r18_3d_stat_role_mapping_registry.json` | `3dec65cab59a92a36d52db7187fa3ae6aa01450e7160378722faa1bf54e2bb16` | ✅ (via `meta.seal_status` = `CLOSED_AND_SEALED_DOCUMENTAL_ONLY`) |
| 2 | `/app/memory/r18_3d_stat_role_mapping_registry.md` | `2e360cfec4fa59db0f57e6a6dec6332eb6bca9d589d923ca27552cc16937c398` | ✅ (banner testo header + footer) |
| 3 | `/app/backend/app/core/stat_role_registry.py` | `e1e083e3b923fcf547baa3cb1fee27816ef4a149217f49d47699c62c08ab134b` | ✅ (banner docstring modulo) |
| 4 | `/app/backend/app/scripts/round18_3d_apply_metadata.py` | `b439f429adabccf62897dae78fa163df5b2ba8c404d65f7f5f51f575f50c61d7` | ✅ (banner docstring modulo + banner APPLY_ENABLED false) |
| 5 | `/app/backend/tests/backend_r18_3d_stat_role_registry_test.py` | `12ee2df3316147985c3a83b4e30c9c38fac45facd260f8898f8f53f2aef7c1e2` | ✅ (banner docstring modulo) |

---

## 3. Conferma no DB apply

Verifica live su MongoDB (`orbus_r16`) subito prima del SEAL:

- **`audit_log` events con `event_type` matching `R18_3d|R18.3D|round18_3d|stat_role_registry`**: **0**
- **`audit_log` events con `metadata.source_round` matching `R18.3d`**: **0**
- **`adventurer_classes.count()`**: **18** (invariato dal pre-round)
- **`adventurer_classes` con `stat_role_registry_source_round` exists**: **0**
- **Sample doc `slug=warrior`** post-check: nessuno dei 5 SAFE field (`role_display_it`, `class_role_tags`, `design_primary_stat_it`, `design_secondary_stats_it`, `stat_role_registry_source_round`) è presente.
- **Delta collection `adventurer_classes` (baseline Phase A → SEAL time)**: **0** documenti scritti/modificati.
- **Delta collection `audit_log`**: **0** eventi R18.3d.

**Conclusione**: NESSUN SET operation eseguito. Catalog live coerente con baseline Phase A.

---

## 4. Conferma zero runtime wiring

Ricerca `grep -rn stat_role_registry /app/backend --include=*.py`:

```
/app/backend/app/core/stat_role_registry.py:63:    "stat_role_registry_source_round"        # (definizione costante interna)
/app/backend/app/scripts/round18_3d_apply_metadata.py:26,74,117: stat_role_registry_source_round  # (field name string in script UNWIRED)
/app/backend/tests/backend_r18_3d_stat_role_registry_test.py:36,196,203,208: from app.core.stat_role_registry  # (TEST SUITE ONLY - ATTESO)
```

**Runtime paths che importano `app.core.stat_role_registry`**: **0** (zero).

**Solo consumer**:
1. La sua test suite `backend_r18_3d_stat_role_registry_test.py` (ATTESO — non-runtime).
2. Il suo sibling script `round18_3d_apply_metadata.py` (UNWIRED, `APPLY_ENABLED = False`, mai lanciato dal boot).

**Test-of-record `test_9_registry_module_unwired`**: PASSED (verifica dinamica dell'assenza di import runtime).

---

## 5. Conferma test suite result

### Test suite dedicata R18.3d Phase B

```bash
pytest tests/backend_r18_3d_stat_role_registry_test.py -v
```

**Risultato**: **28/28 PASSED** in `0.90s`

Breakdown:
- `test_1_mapping_6_to_5_locked` (6 param) — PASS
- `test_2_registry_parses_meta_present` — PASS
- `test_3_canonical_27_locked` — PASS
- `test_4_legacy_live_documented_separately` — PASS
- `test_5_legacy_live_matches_db` — PASS
- `test_6_excluded_manifest_entries_present` — PASS
- `test_7_safe_fields_scope` — PASS
- `test_8_eligible_apply_is_canonical_intersect_live` — PASS
- `test_9_registry_module_unwired` — PASS
- `test_10_no_player_facing_leak` — PASS
- `test_11_bard_drift_documented` — PASS
- `test_12_paladin_faith_accepted` — PASS
- `test_13_guard_hard_stop_blocked_field` (4 param) — PASS
- `test_14_legacy_live_hard_stop_in_plan` — PASS
- `test_15_dry_run_only_canonical_intersect_live` — PASS
- `test_16_apply_without_ack_fails_30` — PASS
- `test_17_registry_sha256_computable` — PASS
- `test_18_priority_critical_slugs` — PASS
- `test_19_meta_counts_internally_consistent` — PASS
- `test_20_no_blocked_fields_in_canonical_entries` — PASS

### Sealed / integrity regression suite

```bash
pytest -k "sealed or integrity" -v
```

**Risultato**: **5/5 PASSED** in `1.68s`

Breakdown:
- `test_t01_sealed_scripts_untouched` (round1b_hotfix_v1_2_starter_stats) — PASS
- `test_t01_sealed_scripts_untouched` (round1b_hotfix_v1_3_schema_compat) — PASS
- `test_t01_sealed_script_untouched` (round1b_hotfix_starter_kit) — PASS
- `test_06_whitelist_slugs_sealed` (round1812_guard) — PASS
- `test_t03_counter_threat_referential_integrity` (round160_phase4) — PASS

**Nessuna regression** sui sigilli R18.Reset.1b / R18.Reset.2 / round160 / round1812.

---

## 6. Conferma 27 canonical + 16 legacy separate

Estrazione diretta dal registry JSON:

- `canonical_classes[]` length = **27** ✅
- `legacy_live_classes[]` length = **16** ✅
- `excluded_manifest_entries[]` length = **0**
- `meta.canonical_classes` = 27
- `meta.live_catalog_classes` = 18 (16 legacy live + 2 canonical live: `cacciatore_di_mostri`, `cacciatore_del_vuoto`)
- `meta.canonical_live_count` = 2 (intersezione canonical ∩ live)
- `meta.legacy_live_classes_count` = 16
- `meta.design_only_classes_count` = 25 (27 canonical − 2 canonical live)

**Test `test_19_meta_counts_internally_consistent`**: PASSED (i counter meta combaciano con i len effettivi).

**Legacy live slugs registrati (16)**: `warrior`, `rogue`, `mage`, `monk`, `paladin`, `druid`, `priest`, `ranger`, `warlock`, `bard`, `alchemist`, `necromancer`, `assassin`, `berserker`, `recruit_unassigned`, `test-class-5e0064`.

**Canonical live slugs (2)**: `cacciatore_di_mostri`, `cacciatore_del_vuoto` (unici eligibili per hypothetical B3 apply — attualmente hidden e non toccati).

**Drift documentati (mantenuti)**:
- `bard.role = "Support"` (out of `VALID_ROLES=(Tank,DPS,Healer)`) — inserito a backlog come `R18.3d.followup — Bard Role Drift Resolution` (P3).
- `paladin.primary_stat = "faith"` (canonical design = `strength`) — LOCKED live su `faith` per non corrompere 480 paladini live post-reset. Nessuna azione richiesta.

---

## 7. Backlog R18.3e creato

- **Path**: `/app/memory/backlog.md`
- **Section**: `## Backlog aperti`
- **Entry appena inserita (verbatim as PM directed)**:

```
[BACKLOG] R18.3e — Canonical IT ↔ Legacy EN Class Bridge
Origine: R18.3d Phase B Q10.b + verifica e1_tester (canonical 27 IT vs live 16 EN legacy quasi disgiunti)
Obiettivo: mappare legacy live EN verso canonical IT; decidere se usare `alias_target`, `canonical_slug`, o migration vera.
Vincoli: NO recruitment change senza approvazione PM. NO runtime fields change senza PM.

Esempi da valutare in quel round (draft, NON applicati):
  warrior     → guerriero
  rogue       → ladro
  mage        → mago
  priest      → paladino OPPURE classe legacy da dismettere (decisione PM)
  ranger      → cacciatore_di_mostri
  warlock     → cacciatore_del_vuoto
  monk        → monaco
  druid       → druido
  bard        → bardo
  alchemist   → alchimista
  necromancer → negromante

Priorità: P2 (blocker prerequisito per R18.4 se R18.4 tocca item class-bound player-facing)
Status: BACKLOG
```

**HOLD section** aggiornata: `R18.3d Stat/Role Mapping Registry` marcato come `CLOSED & SEALED 2026-07-05 (documental-only, no DB apply)` per tracciabilità.

**PRD.md** aggiornato con sezione header:
```
## R18.3d Phase B — CLOSED & SEALED (documental-only)
Timestamp: 2026-07-05T18:06:50Z
Nota: Closed as documental-only registry. No DB metadata apply executed.
File sigillati: registry JSON + MD companion + stat_role_registry.py + round18_3d_apply_metadata.py + test suite
Prossimo round consigliato: R18.3e (bridge IT↔EN) o R18.4 con caveat
```

---

## 8. Prossimo round consigliato

**Raccomandazione primaria**: **R18.3e — Canonical IT ↔ Legacy EN Class Bridge** (P2).

**Motivazione**:
- Il registry R18.3d ha bloccato il fatto (canonical 27 IT vs live 16 EN sono quasi disgiunti — intersezione = 2 slug hidden).
- Qualsiasi feature player-facing che riguardi classi (in particolare **R18.4 — Item class-bound player-facing**) rischia di rimanere non-coerente tra il set canonical (IT) e il set live (EN legacy) senza un layer di bridge esplicito.
- Le opzioni tecniche pre-scoutate sono `alias_target` (soft mapping) vs `canonical_slug` (hard rewrite in doc live) vs migration vera (rewrite slug + backfill 3360+ adventurers post-reset). La scelta ricade sul PM.

**Alternativa accettabile**: procedere direttamente con **R18.4 accettando il caveat**, purché il PM autorizzi esplicitamente che gli item class-bound siano indicizzati sui **slug live** (16 EN legacy) e NON sui slug canonical (27 IT). In quel caso R18.3e slitta a P3 e va documentato che il gioco resterà player-facing sui nomi legacy inglesi fino al bridge.

### Caveat esplicito per R18.4

Se il PM decide di procedere con R18.4 **prima** di R18.3e:
1. Gli item class-bound saranno legati esclusivamente ai 16 slug legacy live EN.
2. Le 25 canonical design-only IT (non presenti in live catalog) non riceveranno item drop né recipe binding.
3. Al momento in cui R18.3e sarà eseguito, sarà necessario un round di **item rebind migration** per riallineare gli item ai nuovi slug canonical — potenziale WARN sul contract API pubblico.
4. Il frontend continuerà a mostrare slug legacy EN nei display class-bound fino al bridge.

**Il PM ha già bloccato `NO recruitment change senza approvazione PM` e `NO runtime fields change senza PM` sul backlog R18.3e — questi vincoli restano validi anche quando R18.3e sarà eseguito.**

---

## Attestazione finale

- ✅ 5/5 file sigillati con banner "CLOSED & SEALED" verificabili (JSON via `meta.seal_status`, MD/Python/script/test via docstring header)
- ✅ 5/5 SHA256 registrati e riproducibili
- ✅ 28/28 R18.3d suite PASSED
- ✅ 5/5 sealed/integrity regression PASSED
- ✅ 0 audit_log events R18.3d (no DB apply)
- ✅ 0 adventurer_classes docs con SAFE metadata applied (no SET)
- ✅ 0 runtime import di `app.core.stat_role_registry` (UNWIRED verificato)
- ✅ Backlog R18.3e registrato verbatim
- ✅ PRD.md aggiornato con sezione R18.3d Phase B CLOSED & SEALED
- ✅ Nessuna regressione su sigilli R18.Reset.1b / R18.Reset.2

**R18.3d Phase B è chiuso. Il registry resta artefatto documentale immutabile per riferimento futuro. Nessun impatto runtime. Nessun impatto DB.**

**In attesa di GO PM per R18.3e o R18.4 (con caveat esplicito). STOP.**
