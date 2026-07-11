# Orbus Online — PRD (Round 16.3 CLOSED incluso Phase 8 V1, 2026-07-01)

## 🎯 R18.5 — PWR Solo-Equip + XP Curve Lv60 + Item Tier Rework — Phase A Discovery READ-ONLY (2026-07-06)

**Round attivo**: `R18.5 — PWR Solo-Equip + XP Curve Lv60 + Item Tier Rework`
**Fase attiva**: A — Discovery READ-ONLY (audit sistema attuale, no design lock)
**Documento discovery**: `/app/memory/r18_5_phase_a_discovery.md/.json`
**Sigilli attivi**: **36** (invariati post-R18.P3).

### Prossimi round / status
- **R18.5** Phase A → **OPEN** (in corso)
- **R18.3f** Class Slug Migration → **HOLD**
- **R18.backlog.shield_slot_mapping_dedicated** → BACKLOG P2
- **R18.backlog.phase14_craft_workshop_lock_refactor** → BACKLOG P3 (nuovo, 4 test craft residue)
- **R18.backlog.phase14_shape_drift_refactor** → BACKLOG P3 (nuovo, 3 test shape drift residue)
- **R18.backlog.apply_pattern_spec** → BACKLOG P3

---

## 🧹 R18.P3 — Post-R18.4 Cleanup — CLOSED (2026-07-06)

**Round**: `R18.P3 — Post-R18.4 Cleanup & Backlog Triage`
**Fase**: B — Safe Cleanup Execution (chiude round R18.P3)
**Chiusura**: 2026-07-06T16:00:00Z UTC
**Note governance**: R18.P3 è **CLOSED (non sealed)** — modifiche solo su file non-sealed.
**Report finale**: `/app/memory/r18_p3_phase_b_safe_cleanup_execution_report.md/.json`

### Sintesi
- **P3.6** (Public API serializer exposure) → **CLOSED** (già completato in R18.4.followup Phase B/C).
- **P3.7** (phase14_* legacy debt) → **FIXED parziale** (3 su 10 test recuperati via soft-assert `>= 200` + password conformi).
- **P3.8** (SMTPRecipientsRefused) → **FIXED** (env flag `EMAIL_ENABLED` in `backend/app/core/email.py` + `.env.test` + dev `.env`).
- **P3.1, P3.2, P3.3, P3.4, P3.5** → **BACKLOG open** (defer/dedicated round).
- **Sigilli 36/36 byte-identical** verificati.
- **Zero DB writes**, **zero enforcement change**, **zero refactor auth flow**.
- **2 nuovi backlog P3 aperti** dalla Phase B (residual failure documentati per dedicated round futuro).

---

## 🧹 R18.P3 — Post-R18.4 Cleanup & Backlog Triage — Phase A READ-ONLY (2026-07-06)

**Round attivo**: `R18.P3 — Post-R18.4 Cleanup & Backlog Triage`
**Fase attiva**: A — Triage READ-ONLY di 8 P3 backlog items
**Documento triage**: `/app/memory/r18_p3_post_r18_4_cleanup_triage.md/.json`
**Governance**: zero DB writes, zero code changes, zero sealed touch (36 sigilli byte-identical).

### Stato prossimi round
- **R18.5** — PWR Solo-Equip + XP Curve Lv60 + Item Tier Rework → **NON aperto** (attesa GO PM)
- **R18.3f** — Class Slug Migration → **HOLD**
- **Phase D** — Playwright snapshot E2E → opzionale, delegabile al testing subagent

### Deliverable UI 4-state (chiuso in R18.4.followup Phase C)
- Badge **Bloccato / Non consigliato / Consigliato / Universale** con icona lucide + testo IT
- Endpoint `GET /api/adventurers/{id}/eligible-items` con contract 10-field
- Serializer `item_public()` espone raw `item_binding_policy` + canonical `slot_type` + derived `is_universal`
- Slot fallback `slot_type ?? item_type` applicato in `Inventory.jsx`, `InventoryEquipModal.jsx`, `AdventurerEquipment.jsx`

---

## 🔒 R18.4.followup Phase C — UI 4-State Item Compatibility Activation — CLOSED & SEALED (2026-07-06)

**Round**: `R18.4.followup — UI 4-State Item Compatibility Activation`
**Fase**: C — Integration + SEAL
**Chiusura Phase C**: 2026-07-06T11:35:00Z UTC — round CLOSED & SEALED
**Report finale**: `/app/memory/r18_4_followup_ui_4state_phase_c_integration_and_seal_report.md/.json`

### Sintesi Phase C
- Integrazione full 4-state badge in `AdventurerEquipment` page via consumo endpoint `/api/adventurers/{id}/eligible-items` (B.SQ6).
- Slot fallback `slot_type ?? item_type` applicato anche in `AdventurerEquipment.jsx::inventoryBySlot` (Risk 10.1 fully CLOSED).
- 4 nuovi test deterministici t10-t13 (blocked / not_recommended / recommended / universal) → 13/13 PASS totale.
- SEAL di **6 nuovi file** (2 memory contract + 3 code + 1 test), portando il totale a **36 sigilli** attivi.
- Sealed integrity 36/36 PASS (30 pre-esistenti byte-identical + 6 nuovi byte-identical).
- Backlog P3 `R18.backlog.phase14_legacy_test_cleanup` aggiunto (chiude Nota 2 PM).

### Sigilli Phase C (6/6)
1. `/app/backend/app/equipment/ui_4state.py`
2. `/app/frontend/src/components/ItemCompatibilityBadge.jsx`
3. `/app/frontend/src/utils/compatibilityLabels.js`
4. `/app/backend/tests/backend_r18_4_followup_ui_4state_test.py`
5. `/app/memory/r18_4_followup_ui_4state_phase_b_pm_decisions.md`
6. `/app/memory/r18_4_followup_ui_4state_phase_b_pm_decisions.json`

### Next-in-queue
- `R18.5` (o backlog P2/P3) in attesa di GO PM.

---

## R18.4.followup Phase B — UI 4-State Item Compatibility Activation — DELIVERED (2026-07-06)

**Round**: `R18.4.followup — UI 4-State Item Compatibility Activation`
**Fase**: B — Implementation (read-side API + UI activation)
**Chiusura Phase B**: 2026-07-06T09:24:00Z UTC — implementation completa, ready per Phase C review
**Report finale**: `/app/memory/r18_4_followup_ui_4state_phase_b_implementation_report.md/.json`

### Sintesi
- Serializer `item_public()` estende output con `slot_type`, `item_binding_policy`, `is_universal` (B.SQ1).
- Nuovo endpoint context-aware `GET /api/adventurers/{id}/eligible-items` con contract 4-state (B.SQ6).
- Helper `app/equipment/ui_4state.py` come single source of truth read-only derivation.
- Frontend `ItemCompatibilityBadge` + slot fallback `slot_type ?? item_type` (B.SQ4/SQ5, mitigazione Risk 10.1 shield).
- Test suite dedicata: **9/9 PASSED** backend (>= 8 minimo B.SQ8); frontend/E2E delegati a testing agent.
- **Sealed integrity 5/5 PASSED** — nessun sigillo dei 30 file R18.4 SEAL toccato.
- Zero DB writes, zero runtime enforcement change, zero migration.

### Next-in-queue Phase C (attesa GO PM)
- Integrazione full 4-state (blocked/not_recommended/recommended) nella `AdventurerEquipment` page.
- SEAL Phase C dei 6 nuovi file Phase B.


## R18.4 — Item Class-Bound Player-Facing — CLOSED & SEALED (2026-07-06)

**Round**: `R18.4` (Item Class-Bound Player-Facing — Option 3 Hybrid Refined)
**Chiusura**: 2026-07-06T07:20:00Z UTC — **CLOSED & SEALED** (autorità: PM Orchestrator)
**Report finale**: `/app/memory/r18_4_phase_b4_contract_lock_and_seal_report.md`

### Sintesi
- Backfill `items.slot_type` completato su **140 items** (54 weapon / 42 accessory / 44 armor incl. 2 shield → armor SQ1a).
- `items.item_binding_policy` applicato su **178 items** (11 hard / 146 soft / 21 universal) via bucket derivation SQ6 (hard = required_class_optional populated; universal = material/consumable; soft = residuo).
- 2 audit events reali emessi (`R18_4_SLOT_TYPE_BACKFILL_APPLIED`, `R18_4_ITEM_BINDING_POLICY_APPLIED`).
- Rollback dry-run readiness: 140+178 records feasible, backup snapshots pre-apply integri.
- e1_tester POST-APPLY gate: 4/4 macro PASS · zero regression · zero scope-creep.
- 46 test PASS + 3 skipped (16 R18.4 class_bound + 5 sealed_integrity_30 + 24+3 R16.5.4b baseline + 1 R18.3e sealed_16 cross-check).

### 11 nuovi sigilli R18.4 (SHA256 post-banner)
1. `/app/memory/r18_4_phase_b2_pm_decisions.md` → `83b5f60813cef99cc30d8f4704860ec7f17a40da0de64093b706efa2de974566`
2. `/app/memory/r18_4_phase_b2_pm_decisions.json` → `c73e6743a6fbb26177deb7e941ce6e900f38b3db08fd894451d8859711832be4`
3. `/app/memory/r18_4_class_bound_registry.md` → `e26065a1da92e98278163ee7a2dd757d65dbddbacb668ff43df2e44a3611b43c`
4. `/app/memory/r18_4_class_bound_registry.json` → `c3a58e3d94f0053870a12197b29c02e0ec7d17ddae5d85496ca17584d0a2059d`
5. `/app/backend/app/scripts/round18_4_backfill_slot_type.py` → `7108bf189415468bc7148f70186d6b5f2e1f7a618f712cbb2f02693e00ab54e6`
6. `/app/backend/app/scripts/round18_4_apply_class_bound.py` → `fda696467001d313128630735a4e91dc03f0af3cf8eb9da43ef4ca7e8f2c26fa`
7. `/app/backend/app/scripts/round18_4_backfill_slot_type_apply.py` → `6a9a3c5cb50fc97c436fe39a71d39657d199885fd0ae35d335e08c8dc60c8461`
8. `/app/backend/app/scripts/round18_4_apply_class_bound_apply.py` → `1358d42fa051623ed5e06a44ee8b5279fb11fd99afc44bb0596f06d312ec42b3`
9. `/app/backend/tests/backend_r18_4_class_bound_test.py` → `f0644e2c3df869c0344afb2e831f2fffc8759eaef7554ed1764d7ba0a74d5d28`
10. `/app/memory/r18_4_phase_b3_dry_run_prereport.md` → `3bb1484826710a9a8b688e6152150ad2c8a860352daaaf1978b1a686aef76d59`
11. `/app/memory/r18_4_phase_b3_real_apply_report.md` → `de0c9b4661ac17b9b16ea7bd4b1e90ec7909a7b46b899563eb04c8e2fad94585`

### Totale sigilli attivi post-B4
**30** = 19 pre-esistenti byte-identical + 11 R18.4 nuovi. Verifica statica in `/app/backend/tests/backend_r18_4_sealed_integrity_test.py` (5/5 test PASS).

### Backlog R18.4 P3 attivi (6)
1. `R18.4.followup — Shield slot mapping decision` (SQ1)
2. `R18.4.backlog — specialization_unlocks dead branch cleanup` (SQ2)
3. `R18.4.backlog — berserker/assassin dormant signature items` (SQ4)
4. `R18.4.backlog — Backfill Apply Idempotency Counter Pattern`
5. `R18.4.backlog — Class-Bound Apply Zero-Write Audit Noise`
6. `R18.4.followup — Public API serializer exposure of slot_type + item_binding_policy for UI activation`

### Prossimo round consigliato
`R18.4.followup — UI 4-State Item Compatibility Activation` (Phase A Discovery in corso, READ-ONLY). Nota: R18.5 già occupato in roadmap da "PWR Solo-Equip + XP Curve Lv60 + Item Tier Rework"; il round UI 4-state prende naming `R18.4.followup` per evitare conflitto.

### In HOLD
- `R18.3f — Class Slug Migration Planning` (rischio MEDIO/ALTO, no runtime bridge attivato; class_slug live resta legacy EN).

---

## R18.3e — Canonical IT ↔ Legacy EN Class Bridge — CLOSED & SEALED (2026-07-05)

**Round**: `R18.3e` (Legacy EN ↔ Canonical IT Class Bridge, Phase B post B2 real apply)
**Chiusura**: 2026-07-05T20:15:00Z UTC — **CLOSED & SEALED** (autorità: PM Orchestrator)
**Report finale**: `/app/memory/r18_3e_phase_b_final_closure_report.md`
**Seal registry aggregato**: `/app/memory/r18_3e_seal_registry.json`

### Sintesi
- 18/18 doc `adventurer_classes` aggiornati con 5 SAFE bridge metadata field (`canonical_slug`, `alias_target`, `bridge_status`, `bridge_source_round`, `bridge_applied_at`).
- Distribuzione: 9 mapped_canonical + 3 mapped_alias + 2 deprecated_alias + 2 canonical_native + 1 technical_placeholder + 1 test_artifact.
- 1 audit event aggregato `R18_3E_BRIDGE_METADATA_APPLIED` (apply_id `35302c0c-98dc-4b3b-b5b2-f1646540b74a`, applied_at `2026-07-05T19:45:31Z`).
- Rollback dry-run 18/18 PASS + backup pre-apply intatto.
- e1_tester post-B2 4/4 macro-tests PASS.
- 3 WARN accettati come governance notes documentate.

### 5 nuovi sigilli R18.3e (SHA256 finali)
1. `/app/memory/r18_3e_bridge_registry.json` → `44f30612c559385e0b44b3cefe785c879cd341ce2d7b64fa4e1fe71e577ee244`
2. `/app/memory/r18_3e_bridge_registry.md` → `4161fdf657992742843ffabc093ed509d8aef5945c979fff0704e518a5449b66`
3. `/app/backend/app/scripts/round18_3e_apply_bridge.py` → `942fe04070b1cf4f3763bc3e733889855960d3e6f46f8e191b93c11a7a10c7fd`
4. `/app/backend/app/scripts/round18_3e_rollback_bridge.py` → `7c39bdc4db665e17ee2928dfa2a378527e59461186b9eb7eead200b4f3b1a26c`
5. `/app/backend/tests/backend_r18_3e_bridge_test.py` → `6d948b716dd63387b21ca12fbaed2392278c902ef5823f4a26825fee8396f086`

### Totale sigilli attivi post-seal
**24** = 19 pre-esistenti byte-identical (14 R18.Reset.1b/1.2/1c + banner R18.Reset.2 contract-lock tests + 5 R18.3d Phase B) + 5 R18.3e nuovi.

### 3 WARN accettati (governance notes)
1. WARN 1: `bridge_source_round="R18.3e Phase B"` accettato come precisione phase-level, no normalization.
2. WARN 2: expedition write side-effect dal tester (Campo d'Addestramento L1), non R18.3e-caused, no gameplay regression.
3. WARN 3: dungeon label i18n → backlog `R18.Backlog — Dungeon Label i18n Consistency Review` (P3).

### Regression result
- 27/27 R18.3e bridge test PASS
- 6/6 sealed/integrity PASS
- 4/4 e1_tester post-B2 macro PASS
- 0 regression sui 19 sigilli pre-esistenti

### Backlog aperti/confermati dal round
1. `R18.Backlog — Seed Idempotent Timestamp Churn Noise` (P3, da W1 investigation)
2. `R18.Tooling — DryRun/Apply Path Readiness Gate` (P3, da W3 scope drift, già aperto)
3. `R18.Backlog — Dungeon Label i18n Consistency Review` (P3, da WARN 3)

### Prossimo round consigliato
`R18.4 — Item class-bound player-facing` (P2, in attesa GO PM). Caveat: usare il bridge R18.3e come input documentale/metadata senza assumere che `class_slug` live sia canonical IT (i doc adventurers restano su legacy EN slug). `R18.3f — Class Slug Migration Planning` resta deferred.

---

## R18.3d Phase B — CLOSED & SEALED (documental-only)
Timestamp: 2026-07-05T18:06:50Z
Nota: Closed as documental-only registry. No DB metadata apply executed.
File sigillati: registry JSON + MD companion + stat_role_registry.py + round18_3d_apply_metadata.py + test suite
Prossimo round consigliato: R18.3e (bridge IT↔EN) o R18.4 con caveat

## Stato attuale
**Round 16.3 OFFICIALLY CLOSED ✅** — ciclo completo Fasi 1..8 V1 sigillato. Ciclo PvP (Phase 7A 1v1 + Phase 7B Leaderboard/Cosmetici) chiuso end-to-end. **Phase 8 V1 (Stalla cosmetica) chiusa** con Backend Iter1 + Frontend Iter2.

Totali sessione: **106/106 backend pytest PASS** con DB isolation attiva, frontend smoke 15/15 PASS, disclaimer anti-P2W visibile ×5 (3 PvP + 2 Stables), zero regression.

Vedi `/app/memory/round163_final_report.md` per il consolidamento finale sigillato.

## Contesto post-incident
Il 2026-07-01, l'agente principale in Fase 1 ha erroneamente costruito un MVP fresh (Auth + Guild + Dashboard base) archiviando il progetto Round 16.x avanzato dentro `_legacy/`. Durante quel percorso ha eseguito `drop_database('test_database')` **prima** che il vincolo "NON droppare NULLA" venisse emesso, con perdita irreversibile dello **stato dinamico** del mondo pre-incident (gilde reali, spedizioni, achievement, PvP Elo, trade pact, world state).

Il 2026-07-01 12:30 UTC è stata completata la recovery operazione **Opzione 3+1**:
- codice Round 16.x ripristinato in `/app/backend/` e `/app/frontend/src/` (12 MB backend, 1.9 MB frontend);
- `DB_NAME` cambiato in `orbus_r16` (nuovo DB pulito). `test_database` conservato come snapshot naturale della Fase 1 accidentale;
- backend attivo con 233+ endpoint OpenAPI, frontend build production OK.

## Fasi Round 16.3 (tutte chiuse)

| Phase | Descrizione | Stato |
|---|---|---|
| 1 | World Boss V1 Alveora | ✅ CLOSED |
| 2 | Mondo & 8 Mastocontinenti | ✅ CLOSED |
| 3 | Eventi Continentali + Site Contracts | ✅ CLOSED |
| 4 | Continental Resources V0 + Classifiche | ✅ CLOSED |
| 5A | Legendary Forge (BOP, cap +50%, pity) | ✅ CLOSED |
| 5B | Arfus Forge (tech tree passivo, cap +30%) | ✅ CLOSED |
| 6 | Trade Pacts V0 + Guild Specialization V0 | ✅ CLOSED |
| **7A** | **PvP Continentale 1v1** | ✅ **CLOSED** |
| **7B** | **Leaderboard Settimanale + Cosmetici** | ✅ **CLOSED** |
| **8 V1** | **Stalla & Cavalcature (cosmetic-only, narrative)** | ✅ **CLOSED** |
| 8 V2 | Rotte narrative su 3 domini restanti + variante esplorativa `-5% travel time` | 🔴 FUTURE / DESIGN REVIEW REQUIRED |

## Test suite Round 16.3 (Phase 7 + 8)
- `test_pvp_phase7a_p0.py`: 33/33 PASS
- `test_pvp_season_phase7b_p0.py`: 31/31 PASS
- `test_stables_phase8_v1.py`: 28/28 PASS
- Regression baseline (`test_forge_actions_p0.py`, `test_races_endpoint_p1.py`): 12/12 PASS
- **Totale sessione Phase 7+8 V1**: **106/106 PASS** con DB isolation attiva (`orbus_r16_test`)

## User personas (invariate)
- Guildmaster (giocatore principale)
- Admin
- Tester QA

## Debito tecnico residuo P3
Vedi `/app/memory/round163_final_report.md` sezione "Debito tecnico residuo P3":
1. Pytest HTTP admin bypass DB isolation
2. Startup handler `_seed_r163_phase3_startup` cleanup
3. Schema drift Alchemist (3 doc con `parent_class_slug` vs `class_slug`)
4. ESLint warning `ClassHalls.jsx:244`
5. Guard-rail self-test mancante
6. Mobile viewport verification workaround

## Prossima raccomandazione
1. **P3 Debt cleanup** (Iter C — attivo in questa sessione)
2. **Design review anti-P2W** per Phase 8 V2 (`-5% travel time` deve essere esclusivo di rotte narrative dedicate, mai su farm loop di gathering/expedition)
3. Solo dopo review approvata: implementare Phase 8 V2

## Fuori scopo immediato
- Rebuild dello stato dinamico pre-incident (gilde/spedizioni reali): perdita irreversibile, non recuperabile senza dump.
- Riscrittura Fase 1 fresh: **archiviata** in `_fresh_accidental_build_backup/` e `_fresh_parcheggio_*/`, non usata.

## File di riferimento (consolidati)
- `/app/memory/round163_final_report.md` — **consolidamento sigillato Round 16.3**
- `/app/memory/orbus_world_roadmap.md` — roadmap aggiornata Phase 7 CLOSED
- `/app/memory/incident_recovery_report.md` — report recovery
- `/app/memory/test_credentials.md` — credenziali test
- `/app/memory/BUILD_RULES.md`, `PROD_DEPLOY_CHECKLIST_ROUND_*.md`, `REFACTOR_LOG.md`
- Report fasi 1..7: `/app/memory/round163_phase[N]_final_report.md`, `round163_phase7[a|b]_iter[1|2]_[backend|frontend]_report.md`

---

## R18.Reset.1b — CLOSED & SEALED (2026-07-05)

**Round**: `R18.Reset.1b` (Full Guild Fresh Start)
**Chiusura**: 2026-07-05T15:04:00Z UTC — **CLOSED & SEALED** (autorità: PM Orchestrator)
**Report finale**: `/app/memory/r18_reset1b_final_closure_report.md`

### Sintesi
- **672 guild** riallineate (nome preservato, gold=100, progressione azzerata)
- **3360 adventurers starter** rigenerati (11 classi safe, `base_stats_exact_no_variance` dal catalog)
- **3415 adventurers storici** archiviati soft in `adventurers_r18_archive` (no hard delete)
- **672 kit iniziali** (minor_healing_potion × 3 = 2016 potion totali)
- **Endpoint runtime** operativi post-v1.3 (adventurers, dungeons, expeditions no-500)

### 8 sigilli attivi (registry: `r18_reset1b_hotfix_v1_3_seal_registry.json`)
1. `round18_reset1b_apply.py` (initial)
2. `round18_reset1b_apply_v1_1.py`
3. `round18_reset1b_apply_v1_2.py`
4. `round18_reset1b_apply_v1_3.py` ← **NEW SEAL 2026-07-05**
5. `round18_reset1b_staged_backup_materialize.py`
6. `round18_reset1c_field_cleanup.py`
7. `round18_reset1c_restore_from_jsonl_manifest.py`
8. `app/core/job_freeze.py`

### Known Deferred Scope
- **M4 Banner dismiss endpoint** — deferred a **R18.Reset.2 — Fresh Start Banner UI/API**
- Brief pronto: `/app/memory/r18_reset2_fresh_start_banner_brief.md`
- Nessuna implementazione fino a GO PM esplicito

### Backup retention (90 giorni minimo)
- `r18_reset1b_v1_2_staged_20260705T132515Z/` (staged approved)
- `r18_reset1b_v1_2_20260705T134230Z/` (fresh pre-apply v1.2)
- **`r18_reset1b_hotfix_v1_3_prepatch_20260705T145721Z/`** (fresh pre-apply v1.3, rollback source-of-truth)

### Backlog aperto
- `R18.Tooling.AuditEventIdempotencyKey` — vedi `/app/memory/backlog.md`

### HOLD confermati dopo il SEAL
- `R18.1 drift`
- `R18.3d Stat/Role Mapping Registry`
- `Traits`
- `Fatigue/Cucina`
- `SMTP R17`

### Prossimo round consigliato
`R18.Reset.2 — Fresh Start Banner UI/API` (in attesa GO PM) → **completato e chiuso** (vedi sezione successiva).

---

## R18.Reset.2 — CLOSED & SEALED (2026-07-05)

**Round**: `R18.Reset.2` (Fresh Start Banner UI/API)
**Chiusura**: 2026-07-05T16:04:00Z UTC — **CLOSED & SEALED** (autorità: PM Orchestrator)
**Report finale**: `/app/memory/r18_reset2_final_closure_report.md`
**Test suite**: `/app/backend/tests/backend_r18_reset2_banner_dismiss_test.py` (15/15 PASS, header SEALED banner applicato)

### Sintesi
- Endpoint `POST /api/guilds/me/r18-reset-banner/dismiss` implementato, autenticato, idempotente, tenant-isolated.
- Endpoint `GET /api/guilds/me/r18-reset-banner` espone `{show, dismissed, message_it}` con testo byte-exact IT-locale LOCKED.
- Componente React `R18ResetBanner.jsx` integrato in Dashboard, palette scura Orbus, nessuna emoji, no gradient viola.
- Field `r18_reset1b_banner_dismissed` (bool) + `r18_reset1b_banner_dismissed_at` (ISO UTC) persistiti in `guilds`.
- Nessun leak metadata tecnici (backup, archive, apply_id, hotfix marker) in `GET /api/guilds/me`.
- Zero side-effect su altri endpoint (adventurers, dungeons, expeditions, inventory, migration-banner).

### Deliverable del round
- 2 endpoint backend (`POST` dismiss + `GET` state)
- 1 componente React frontend (`R18ResetBanner.jsx`)
- 1 test suite backend end-to-end (15 test PASS)
- 1 report closure 8 punti
- 1 contract-lock documentale nel registry `r18_reset1b_hotfix_v1_3_seal_registry.json` (sezione `contract_lock_tests`)

### Test integrity
- `test_t01_sealed_scripts_untouched` (8 sigilli R18.Reset.1b) → **PASS** post-R18.Reset.2 (nessuno script sealed alterato)
- Regression e1_tester dedicato → 4/4 PASS

### Nuove voci di backlog aperte
- `R18.Backlog — Migration Banner State Schema Review` (WARN 1, P3, documentale)
- `R18.Backlog — Dungeon Locked Status Code Consistency Review` (WARN 2, P3, contract REST)

### Prossimo round consigliato
`R18.3d — Stat/Role Mapping Registry` (brief pronto: `/app/memory/r18_3d_stat_role_mapping_registry_brief.md`) → **in attesa GO PM esplicito, NESSUNA implementazione**.

---

## Full Guild Fresh Start Reset — CLOSED & SEALED (2026-07-05)

**Blocco completo**: sequenza `R18.Reset.1b` + `R18.Reset.1b.hotfix.v1_3` + `R18.Reset.2`
**Chiusura formale**: 2026-07-05T16:30:00Z UTC — **CLOSED & SEALED** (autorità: PM Orchestrator)

### Composizione del blocco
| Round | Stato | Documento chiusura |
|:---|:---:|:---|
| R18.Reset.1b (Full Guild Fresh Start) | 🔒 CLOSED & SEALED | `/app/memory/r18_reset1b_final_closure_report.md` |
| R18.Reset.1b.hotfix.v1_3 (Schema Compat Fix) | 🔒 CLOSED & SEALED | `/app/memory/r18_reset1b_hotfix_v1_3_phase_a_report.md` + `/app/memory/r18_reset1b_hotfix_v1_3_phase_b_prereport.md` |
| R18.Reset.2 (Fresh Start Banner UI/API) | 🔒 CLOSED & SEALED | `/app/memory/r18_reset2_final_closure_report.md` |

### Risultato consolidato
- **672 guild** riallineate (nome preservato, gold=100, progressione azzerata).
- **3360 adventurers starter** rigenerati sui base_stats catalog (11 classi safe).
- **3415 adventurers storici** archiviati soft in `adventurers_r18_archive` (no hard delete).
- **672 kit iniziali** minor_healing_potion × 3 (= 2016 potion totali).
- **Banner UI/API** operativo, byte-exact IT-locale, idempotente, tenant-isolated.
- **Sistema live healthy**, freeze OFF permanente, endpoint runtime no-500.
- **8 sigilli R18.Reset.1b** ancora byte-identici (verificato via `test_t01_sealed_scripts_untouched`).

### Backlog aperto del blocco
1. `R18.Tooling.AuditEventIdempotencyKey` (P3)
2. `R18.Backlog — Migration Banner State Schema Review` (P3)
3. `R18.Backlog — Dungeon Locked Status Code Consistency Review` (P3)

### HOLD confermati dopo il SEAL
- `R18.1 drift`
- `R18.3d Stat/Role Mapping Registry` (brief pronto, HOLD implementazione)
- `Traits`
- `Fatigue/Cucina`
- `SMTP R17`
- `orbus.seed_round5.base_strength` warning (P3, HOLD)

### Next-in-queue (attesa GO PM)
`R18.3d — Stat/Role Mapping Registry`


---

## R18.5 Phase B.1 + B.2 — Design Lock & Implementation Plan (2026-07-06) — DOCUMENTAL ONLY

**Stato**: 🟢 **CLOSED (documentale)** — in attesa **PM Gate 1** (GO Phase C)
**Locked at UTC**: `2026-07-06T17:20:00Z`
**Governance**: DOCUMENTAL ONLY — 36 sigilli byte-identical, zero DB writes, zero code changes.

### Deliverable (4 file in `/app/memory/`)
| File | Ruolo | Size |
|:---|:---|---:|
| `r18_5_phase_b1_design_lock.md` | Design Lock leggibile (14 tabelle + 6 sezioni extra) | 15.028 B |
| `r18_5_phase_b1_design_lock.json` | Design Lock machine-readable (mirror) | 5.370 B |
| `r18_5_phase_b2_implementation_plan.md` | Implementation Plan leggibile (10 sezioni) | 9.967 B |
| `r18_5_phase_b2_implementation_plan.json` | Implementation Plan machine-readable (mirror) | 11.081 B |

### Design Lock Phase B.1 (highlights)
- **XP curve Lv60**: formula polinomiale invariata (SQ1a); **soft cap** `MAX_VISIBLE_LEVEL=60` (SQ2b) — clamp UI only, XP DB continuo.
- **Item tier rework**: nuovo campo `items.tier` int 1..5 (SQ3c) + dual-label rarity/tier UI (SQ7c).
- **PWR solo-equip**: nuovo campo `adventurers.equipment_pwr` (alias `gear_pwr`) computato, coesiste con `total_power` (SQ4c).
- **Slot endgame**: ibrido starter 3 (weapon/armor/accessory) + endgame 6 (helm/chest/legs/…) attivato a soglia Lv30 (SQ5d).
- **Signature policy**: max 1 signature equipped/adv (SQ9b), drop-only (no crafting R18.5), 15-25 signature target (`PENDING PM`).
- **Set bonus**: differito (SQ10c) — solo placeholder collection `item_sets`.

### Implementation Plan Phase B.2 (highlights)
- **6 migration/dry-run plan** (tier backfill, MAX_VISIBLE_LEVEL constant, equipment_pwr computed, is_signature backfill, endgame slots additive, min_level cross-check).
- **4 registry documentali** in `/app/memory/` (item_family, signature, drop_matrix, naming).
- **Test plan**: 12 unit + 8 integration + 6 regression + 4-state deterministic coverage.
- **Rollback plan** per ogni migration (snapshot mongodump + rollback script + verification SHA256).
- **DB impact**: 5 collezioni (~200 update + ~100 insert), idempotency mandatory.
- **Frontend impact**: 8 componenti (~130 lines), 3 SEALED preserved.
- **Backend/API impact**: 9 endpoint (serializer patch + 1 new leaderboard opzionale), `derive_ui_4state` **SEALED preserved**.
- **Auto-equip**: `compatibility.py` + `bindings.py` + `ui_4state.py` **SEALED preserved** — solo `auto_equip.py` (non-sealed) estende fitness con tier_bonus tie-break.
- **Phase C/D/E breakdown**: 12 sub-step totali, ogni gate autorizzato singolarmente dal PM.

### 8 nuove Sub-Question aperte al PM (Gate 1)
1. **SQ11** — soglia starter→endgame slot transition (proposta Lv30, PM confirm)
2. **SQ12** — tier badge colors (proposta grey/green/blue/purple/gold)
3. **SQ13** — signature target count finale (proposta 15-25)
4. **SQ14** — batch item distribution T1..T5 (proposta 25-35 / 20-30 / 15-25 / 10-15 / 5-8 + 15-25 signature)
5. **SQ15** — endgame dungeon slug + naming player-facing (placeholder `endgame-void-crucible`)
6. **SQ16** — min_level normalization policy (auto-fix vs manual, dry-run threshold 5%)
7. **SQ17** — workshop level minimo per tier (T1=1, T3=3, T4=5, T5=7 proposto)
8. **SQ18** — PWR bonus coefficients (tier_bonus T4=2/T5=5, slot_completion_bonus=5 proposto)

### 7 PM Gate sequenziali
1. **Gate 1** (ATTESA): PM review B.1 + risposte SQ11-SQ18 → GO Phase C
2. **Gate 2**: PM review dry-run report Phase C → GO backfill apply Phase D.2
3. **Gate 3**: PM approval naming registry (80-120 items) → GO seed Phase D.3
4. **Gate 4**: PM approval endgame dungeon naming + drop rate → GO seed Phase D.4
5. **Gate 5**: PM review Phase D end-to-end → GO Phase E
6. **Gate 6**: PM approval SEAL perimeter Phase E → GO SEAL apposition
7. **Gate 7**: PM approval post-SEAL report → CLOSED R18.5

### Governance validation Phase B.1 + B.2
- ✅ **36/36 sigilli byte-identical** (`backend_r18_4_sealed_integrity_test.py` PASS)
- ✅ **Zero file .py/.js/.jsx/.ts/.tsx modificati** (git diff = empty su codice)
- ✅ **Zero DB writes** (nessuno script eseguito su MongoDB)
- ✅ **JSON validity**: entrambi B.1.json e B.2.json parse clean via `python -m json.tool`
- ✅ **Simmetria .md/.json** rispettata per B.1 e B.2 (pattern R18.4)
- ✅ **`PENDING PM approval`** marcato su tutti i numeri di bilanciamento, naming player-facing, stat priorities, drop rate finali, colors, coefficients

### Next-in-queue (attesa GO PM Gate 1)
`R18.5 Phase C — Migration Dry-Run` (documentale + script dry-run, **NO apply**)



---

## R18.5 — Strategic Correction + Gate 1 Lock + Phase C0 (2026-07-06T18:00:00Z) — DOCUMENTAL ONLY

**Stato**: 🟡 **Direction corretta**, **Gate 1 CLOSED**, **Phase C0 CLOSED** (deliverable pronto). Attesa **compilazione + approvazione PM tabella item** per sbloccare Phase C tech.

### 🔄 Strategic Correction (autorità PM)

Il focus del round è stato ridirezionato. **Nuovo titolo**:

> **R18.5 — Itemization, ILVL & Gear Progression Rework**
> *Lv60 cap, item-centered endgame, lore-driven equipment*

**NON è più**: leveling / XP curve refactor.
**È**: oggetti, ILVL, rarità, utility, drop endgame, progressione equip post level max, coerenza lore di Orbus.

### Correzioni tassative applicate

| Ambito | Prima (superseded) | Dopo (corrected) |
|---|---|---|
| Level cap | `MAX_VISIBLE_LEVEL=60` (soft UI-only) | `MAX_ADVENTURER_LEVEL=60` **hard cap gameplay** + `MAX_EQUIPMENT_REQUIRED_LEVEL=60` |
| Overflow XP > Lv60 | accumula, no block | **NO level up**. Progressione post-Lv60 = **ILVL/equip** |
| Player-facing item metric | `equipment_pwr` (PWR-centric) | **ILVL** (player-facing principale). `equipment_pwr` = metrica calcolata secondaria (dry-run only). `total_power` retro-compat |
| ILVL range R18.5 | non definito | **1-60** (T1=1-15, T2=16-30, T3=31-45, T4=46-55, T5=56-60) |
| Principio itemization | rarity+tier meccanico | **Lore-driven** — item T3+ obbligatoriamente lore-linked con utility unica |

### 🔒 Gate 1 CLOSED — 8 Sub-Question lockate (verbatim PM)

| SQ | Decisione |
|---|---|
| **SQ11** | Soglia starter→endgame **Lv30 confermato**. Shield senza modifica distruttiva |
| **SQ12** | Dual-label + colori: T1→grigio, T2→verde, T3→blu, T4→viola, T5→oro. Non solo colore, richiesto testo + aria-label |
| **SQ13** | Signature **min 15 / target 18 / max 25**. Max 1 equipped/adv. Drop-only. No dormant class signature |
| **SQ14** | Batch **80 item totali** — T1=24 / T2=20 / T3=20 / T4=12 / T5=4 (**Legendary hard cap 4**) |
| **SQ15** | Endgame dungeon: **"Cripta delle Faglie di Ambash"** — Lv50-60, fonte T4/T5 |
| **SQ16** | Precedenza `required_adventurer_level > min_level`. Dry-run obbligatorio, no auto-fix |
| **SQ17** | Workshop level: T1→Lv1, T2→Lv2, T3→Lv3, T4→Lv4, T5→Lv5. Signature fuori dal forge |
| **SQ18** | Formula ILVL-based: `equipment_pwr = ilvl + tier_bonus + slot_weight + utility_weight`. Solo dry-run, no runtime enforce |

### Lore sources approvate (T3+ obbligatorie)
Ambash, Irthe, Velur, Efreto, Halodi, Alevora, Soe, Aveol, Ergolat, Krastlov, Adalan, Greatwood/Elfwood, Alberi della Vita, Faglie arcane, Vuoto, Luna Morta, Ciclo delle anime (17 fonti).

### Legendary policy
- Max **4** nel primo batch R18.5
- Non craftabili normalmente
- Non ottenibili shop/premium
- Non necessari per gioco base
- Utility unica lore-legata, memorabile

### 📊 Phase C0 CLOSED — PM Item Table Drafting Support

**Deliverable**: schema 14 campi PM-defined + skeleton 80 righe compilabile in-place + 13 draft esempi come stimolo creativo.

| Tier | Draft Emergent | Da compilare PM | Totale |
|---|---:|---:|---:|
| T1 | 3 | 21 | 24 |
| T2 | 2 | 18 | 20 |
| T3 | 3 | 17 | 20 |
| T4 | 3 | 9 | 12 |
| T5 | 2 (Legendary) | 2 | 4 |
| **Totale** | **13** (≤15 cap C0) | **67** | **80** |

Ogni draft flaggato `🟢 DRAFT PENDING PM approval / DRAFT ONLY / NOT FINAL`. Ogni item T3+ nei draft ha `lore_source` (da lista Gate 1) + `utility` narrativa. Nessuna finalizzazione da parte di Emergent.

### 📋 Deliverable finali R18.5 Direction Correction

**File patchati (4)**:
| File | SHA256 post-patch |
|:---|:---|
| `r18_5_phase_b1_design_lock.md` | `62963e3e…4d` |
| `r18_5_phase_b1_design_lock.json` | `8c8b04d0…0c` |
| `r18_5_phase_b2_implementation_plan.md` | `ecd6a64e…b6` |
| `r18_5_phase_b2_implementation_plan.json` | `0e8186d6…2d` |

**File nuovi (4)**:
| File | SHA256 |
|:---|:---|
| `r18_5_phase_b_gate1_pm_decisions.md` | `758d5311…b9` |
| `r18_5_phase_b_gate1_pm_decisions.json` | `d8bb6d7f…de` |
| `r18_5_phase_c0_item_table_drafting_support.md` | `c357524a…c3` |
| `r18_5_phase_c0_item_table_drafting_support.json` | `d63a39ae…62` |

### Governance validation (Direction Correction + Gate 1 + C0)
- ✅ **36/36 sigilli byte-identical** (pytest PASS)
- ✅ **Zero file .py/.js/.jsx/.ts/.tsx modificati** (git diff pulito su codice)
- ✅ **Zero DB writes**
- ✅ **4 JSON validity** (python -m json.tool clean)
- ✅ **Legendary count draft**: 2 ≤ 4 (rispetto SQ14 hard cap)
- ✅ **Draft count C0**: 13 ≤ 15 (rispetto cap C0 rule)
- ✅ **Ogni item T3+ nei draft** ha `lore_source` + `utility`
- ✅ **Ogni draft flaggato** `PENDING PM approval`

### Next-in-queue
**PM azione**: compilare le 67 righe vuote e rivedere/approvare i 13 draft nella tabella `r18_5_phase_c0_item_table_drafting_support.md`. Una volta approvata la tabella item, potrà essere aperta **Phase C tech dry-run** (scripts backfill + validation).

**NO Phase C tech dry-run** finché PM non completa C0. Nessun altro deliverable Emergent in questa iterazione.


---

## R18.5 Phase C0-bis — Scale-up + Progression/Dungeon/Raid/Proficiency Matrices (2026-07-06T19:00:00Z) — DOCUMENTAL ONLY

**Stato**: 🟡 **Scale-up applicato**. **Phase C0-bis CLOSED** (deliverable pronto). Attesa **PM Gate 2 review** + risposte agli item PENDING PM su proficiency mapping, main stat, naming drift.

### 🔄 Scale-up correction (autorità PM)

Il PM ha corretto la scala del catalogo R18.5 da micro-batch a **MMO reale**:

| Aspetto | Micro-batch B.1/C0 | **Catalogo reale (C0-bis)** |
|---|---|---|
| Item totali | 80 (skeleton) | **1500 minimo** |
| Legendary max | 4 (micro-batch) | **15** (catalogo hard cap) |
| Dungeon | 0 | **60** (12/14/16/10/8) |
| Raid | 0 | **12** (2/3/3/4) |
| Proficiency system | non pianificato | **armor + weapon obbligatorie, hard block runtime** |
| Progression post-Lv60 | ILVL/equip | ILVL / raid / loot raro / utility / ranking / mercato |

**Il micro-batch 80/4 resta valido come skeleton drafting**, non come cap catalogo reale.

### 📋 Deliverable C0-bis (3 nuovi + 3 patched)

**File nuovi**:
| File | SHA256 |
|:---|:---|
| `r18_5_phase_c0bis_progression_dungeon_raid_matrix.md` | `506811f8…3f` |
| `r18_5_phase_c0bis_progression_dungeon_raid_matrix.json` | `dc990821…fa` |
| `r18_5_pm_workspace_master.md` (READ-ONLY MIRROR) | `3a923fed…48` |

**File patched (superseding notes)**:
| File | SHA256 post-patch |
|:---|:---|
| `r18_5_phase_b1_design_lock.md` | `7da73b15…22` |
| `r18_5_phase_b1_design_lock.json` | `312d1ab8…df` |
| `r18_5_phase_c0_item_table_drafting_support.md` | `d271f018…2a` |
| `r18_5_phase_c0_item_table_drafting_support.json` | `5bdf74f5…d7` |

### 🎯 12 sezioni C0-bis (deliverable principale)

1. **5 brackets progression** Lv1-60 + percezione player (verbatim PM)
2. **60 dungeon** distribuzione PM-locked: 12/14/16/10/8
3. **12 raid** distribuzione PM-locked: 2/3/3/4 + 9 structural requirements (team, ruoli, gear check, proficiency, main stat, utility, reward, ranking)
4. **Matrice classi → main stat** (5 classi live × 6 stat) — tutti `PENDING PM approval`
5. **Matrice classi → armor proficiency** (5 × 4 armor types, hard block) — tutti `PENDING PM`
6. **Matrice classi → weapon proficiency** (5 × 16 weapon families) — tutti `PENDING PM`
7. **Matrice dungeon/raid → tier loot** (proposta preliminare per bracket)
8. **Matrice dungeon/raid → lore source** (17 fonti PM-approved)
9. **Matrice dungeon/raid → required level** (proposta pacing)
10. **Scala 1500 item** — tier (300/350/350/300/200) + rarity (400/450/400/235/15) PM-locked + Legendary policy (max 15, utility unica, lore-linked, no craft/shop/paywin/statstick)
11. **Superseding note** vecchio hard cap 80 item
12. **Superseding note** vecchio max 4 Legendary
13. **Ordine valutazione equip** (verbatim PM): proficiency → main stat → ILVL/rarity/tier → utility

### 🔎 Observation naming drift documentata

Discrepanza tra:
- **PM C0-bis verbatim**: Warrior, Rogue, **Mage**, **Priest**, Ranger
- **B.1 Extra D placeholder**: Warrior, Paladin, Berserker, Rogue, Ranger, Assassin, Monk, **Cleric**, **Wizard**, Cacciatore di Mostri

Da chiarire dal PM: canonizzazione Mage/Priest o conferma rename Wizard→Mage / Cleric→Priest. **`PENDING PM approval`**.

### 💡 Workspace Master (READ-ONLY MIRROR)

Header PM verbatim: *"READ-ONLY MIRROR — authoritative decisions remain in PM gate files. No new design decisions may be introduced here."*
Contiene: cheat sheet Gate 1 (SQ11-SQ18), 17 lore sources, superseding note esplicita, regole tassative, cheat sheet C0-bis (5 brackets + 60 dungeon + 12 raid + 1500 items + rarity + proficiency matrices), 10 item PENDING PM aperti, nota consulenza workflow (non decisione). **Non introduce decisioni nuove**.

### Governance validation
- ✅ **36/36 sigilli byte-identical** (pytest PASS)
- ✅ **Zero file .py/.js/.jsx/.ts/.tsx modificati**
- ✅ **Zero DB writes**
- ✅ **5 JSON validity** (tutti clean)
- ✅ **Distribuzioni PM-locked verbatim**: 60=12+14+16+10+8 · 12=2+3+3+4 · 1500=300+350+350+300+200 · rarity=400+450+400+235+15
- ✅ **Legendary count catalogo reale**: 15 (hard cap rispettato)
- ✅ **Nessuna finalizzazione autonoma** su nomi player-facing, proficiency mapping, main stat, utility, drop rate

### 10 item PENDING PM aperti (Gate 2)
1. Classe → main stat finale (Warrior Forza vs Costituzione, Ranger Destrezza vs Forza)
2. Classe → armor proficiency finale (matrice 5×4 hard block)
3. Classe → weapon proficiency finale (matrice 5×16 hard block)
4. Naming drift Mage/Priest vs B.1 Wizard/Cleric
5. Mapping tier↔rarity nel catalogo reale (Gate 1 SQ12 1:1 non è più coerente numericamente con 1500 items)
6. Nomi player-facing dei 60 dungeon
7. Nomi player-facing dei 12 raid + meccaniche specifiche
8. Drop rate finali per tier/rarity nei dungeon/raid
9. Match specifici lore↔dungeon/raid (17 fonti × 72 content)
10. Utility narrative delle 15 Legendary + effetti finali

### Next-in-queue
**PM Gate 2**: review C0-bis + risposte ai 10 item PENDING PM (proficiency mapping e naming drift sono bloccanti per identità classe). Solo dopo Gate 2 potrà aprirsi **Phase C0-ter** (eventuale expansion tabella 1500) o **Phase C tech dry-run** (backfill scripts documentali, sempre NO apply).


## R18.5 Phase C0-ter — Gate 2 CLOSED + Live Class Matrix (2026-07-06T20:00:00Z) — DOCUMENTAL ONLY

**Stato**: 🟢 **Gate 2 CLOSED** + **Phase C0-ter CLOSED**. Attesa **PM Gate 2 review formale** del deliverable prima di sbloccare eventuale **Phase C0-quater** (batch iterativi dungeon/raid naming) OR **Phase C tech dry-run** (backfill scripts documentali, sempre NO apply). Phase C tech resta **BLOCCATA** fino a nuovo gate PM esplicito.

### File autoritativi C0-ter (untracked, ready for PM review)

| File | Path | SHA256 |
|---|---|---|
| Gate 2 PM Decisions Record (MD) | `/app/memory/r18_5_gate2_pm_decisions.md` | `a269d3a807af1c85e02fd1a7c31e5efcab969a3b69a4f3207515eb9b42603ec3` |
| Gate 2 PM Decisions Record (JSON) | `/app/memory/r18_5_gate2_pm_decisions.json` | `36b68234fdd4b2261a93e3f5cff115b2ca1e37dad9049e7b3e9c8ba14361f2e8` |
| Phase C0-ter Live Class Matrix (MD) | `/app/memory/r18_5_phase_c0ter_live_class_matrix.md` | `1fdebdd26c0464f896e04d34f5c930c96c15105c79922d0b0510a863879ad692` |
| Phase C0-ter Live Class Matrix (JSON) | `/app/memory/r18_5_phase_c0ter_live_class_matrix.json` | `859b29129b693d3d775a1dc4e82bdf65df9656d03a0929279a058327f6f872e4` |

### 🔒 3 decisioni bloccanti Gate 2 risolte inline (verbatim PM)

1. **Tier ↔ Rarity many-to-many** (Gate 2 sez. 1) — il mapping 1:1 di Gate 1 SQ12 è rimosso. Tier = fascia tecnica/ILVL; Rarity = qualità e drop. Un T2 può essere Common/Uncommon/Rare; un T5 può essere Rare/Epic/Legendary. Legendary NON significa "tutto T5" — è solo una piccola parte di T5. Gate 1 SQ12 resta valido come **colorazione UI del badge**, non più mapping numerico.

2. **Canonical naming classi live** (Gate 2 sez. 3) — 5 classi PM-lockate: **Warrior**, **Rogue**, **Mage** (canonical, era placeholder B.1 "Wizard"), **Priest** (legacy label mantenuto, NON Cleric drift), **Ranger**.

3. **5 classi live identity** (C0-ter sez. 1-5) — matrice PM verbatim registrata:

| Classe | Main stat | Armor prof. | Weapon prof. (count) |
|---|---|---|---|
| Warrior | Forza | maglia, piastre | spada, ascia, martello, scudo, lancia, arma_in_asta (6) |
| Rogue | Destrezza | cuoio | pugnale, spada, balestra (3) |
| Mage | Intelligenza | stoffa | bastone, tomo, focus, pugnale (4) |
| Priest | Saggezza | stoffa | bastone, martello, focus, reliquia (4) |
| Ranger | Destrezza | cuoio, maglia | arco, balestra, spada, pugnale, lancia (5) |

### 📊 Crosswalk 1500 item PM-approved (aritmeticamente verificata)

Matrice 5×5 Tier×Rarity con **verifica aritmetica eseguita**: righe tier 300+350+350+300+200 = **1500**, colonne rarity 400+450+400+235+15 = **1500**. Cfr. `r18_5_gate2_pm_decisions.md` sez. 2 per la tabella completa.

- **T1**: 220 Common + 80 Uncommon = 300
- **T2**: 150 Common + 150 Uncommon + 50 Rare = 350
- **T3**: 30 Common + 160 Uncommon + 130 Rare + 30 Epic = 350
- **T4**: 60 Uncommon + 150 Rare + 90 Epic = 300
- **T5**: 70 Rare + 115 Epic + 15 Legendary = 200 (NO Common/Uncommon a T5)
- **Legendary**: solo T5, max 15 item catalogo iniziale.

### 🧹 Purge drift Wizard → Mage / Cleric → Priest (documentale)

**Regola tassativa PM** (Gate 2 sez. 4):
- **Wizard** e **Cleric** sono **drift vietati**.
- Da rimuovere/correggere in file futuri e placeholder B.1 dove presenti.
- NON usare come sinonimi di Mage/Priest.
- NON introdurre nuove classi o rename senza gate PM esplicito.

**Scope purge in C0-ter** (verbatim):
- **Solo documentale**. Nessun touch al codice runtime.
- Placeholder B.1 Extra D (Wizard, Cleric) restano nel file B.1 come **history preserved**, ma sono formalmente `deprecated` — canonizzazione a Mage/Priest.
- Naming futuro (item, dungeon, raid, UI copy) userà **Mage** e **Priest** verbatim.
- Rimozione fisica da codice runtime → **NON in C0-ter**, richiede gate PM dedicato.

### ⚔️ 3 weapon families NON assegnate a classi live — `PENDING PM approval`

3 famiglie su 16 non coperte da nessuna delle 5 classi live PM (C0-ter sez. 8):

| Weapon family | Nota |
|---|---|
| **strumento** | Candidato per Bard drift (in backlog) o classe futura (musicista/bardo/scaldo) |
| **falce** | Candidato per classe futura (reaper/necromante/druido?) |
| **trinket** | Categoria "accessorio generico" — possibile universal o riservato a classi future |

**Governance**: Emergent NON assegna autonomamente queste 3 famiglie. Verranno lockate dal PM in future gate.

### 📋 6 remaining non-blocking PM items (verbatim Gate 2 sez. 9)

Item PENDING PM che restano aperti dopo Gate 2, **NON bloccanti** per l'expansion di Phase C0-ter / C tech. Possono essere risolti a batch nelle fasi successive:

1. **Nomi e temi dei 60 dungeon** — batch iterativi futuri.
2. **Nomi e meccaniche dei 12 raid** — batch iterativi futuri.
3. **Drop rate finali** per bracket / tier / rarity.
4. **Lore source specifiche** per ogni dungeon/raid (17 fonti × 72 istanze content).
5. **Utility narrative + effetti** dei 15 Legendary.
6. **Signature items design finale** (max 25 signature — Gate 1 SQ13 lockato su count/policy, design specifico non ancora fissato).

### 🛡️ Governance check C0-ter

- ✅ **36 sigilli byte-identical** — nessuna modifica ai sealed files (verifica: `pytest backend/tests/backend_r18_4_sealed_integrity_test.py` attesa PASS)
- ✅ **Zero code changes** (`.py` / `.js` / `.jsx` / `.tsx` intatti, verificato via `git status`)
- ✅ **Zero DB writes**
- ✅ **Zero migrations / apply scripts**
- ✅ **Solo audit trail verbatim PM** — nessuna decisione nuova introdotta nei file C0-ter
- ✅ **Aritmetica crosswalk 1500 verificata** (righe + colonne + totale)
- ✅ **Naming canonical Mage/Priest** usato ovunque nei file C0-ter (no Wizard/Cleric drift)

### 🎯 Handoff — pronto per Gate 2 review PM

**Prossimo step atteso** (a discrezione PM):
- **Phase C0-quater** — batch iterativi dungeon/raid naming (60 dungeon + 12 raid, 17 lore sources × 72 istanze content). Ancora documentale.
- **Phase C tech dry-run** — backfill scripts documentali per `weapon_family` + `armor_type` (BLOCCATO fino a nuovo gate PM esplicito). Impact analysis già registrato in C0-ter sez. 9 (endpoint `/api/adventurers/{id}/eligible-items`, UI `ItemCompatibilityBadge`, auto-equip, serializer `item_public()`, DB backfill dry-run).

**Attenzione governance sigilli** (C0-ter sez. 11): la rottura del sigillo di `derive_ui_4state` o `item_public()` per aggiungere il proficiency hard-block richiede **gate PM dedicato** con motivazione esplicita e preservation plan dei 36 sigilli byte-identical (o accettazione della loro modifica con nuovo hash registry).

**Files chiave R18.5 (cumulativo)**:
- `/app/memory/r18_5_phase_a_discovery.md/.json` (Discovery)
- `/app/memory/r18_5_phase_b1_design_lock.md/.json` (Design Lock)
- `/app/memory/r18_5_phase_b2_implementation_plan.md/.json` (Implementation Plan)
- `/app/memory/r18_5_phase_b_gate1_pm_decisions.md/.json` (Gate 1 CLOSED)
- `/app/memory/r18_5_phase_c0_item_table_drafting_support.md/.json` (Phase C0 CLOSED)
- `/app/memory/r18_5_phase_c0bis_progression_dungeon_raid_matrix.md/.json` (Phase C0-bis CLOSED)
- `/app/memory/r18_5_pm_workspace_master.md` (PM workspace master, cumulative)
- `/app/memory/r18_5_gate2_pm_decisions.md/.json` (**Gate 2 CLOSED** — nuovo)
- `/app/memory/r18_5_phase_c0ter_live_class_matrix.md/.json` (**Phase C0-ter CLOSED** — nuovo)

**R18.5 status flow**:
`Phase A` ✅ → `Phase B.1/B.2` ✅ → `Gate 1` ✅ → `Phase C0` ✅ → `Phase C0-bis` ✅ → **`Gate 2` ✅ + `Phase C0-ter` ✅** → *Phase C0-quater* ⏸ *PENDING PM* / *Phase C tech dry-run* 🔒 *BLOCKED gate PM*

## R18.5 Phase C0-quater Batch 1 Informed — CLOSED (2026-07-06T21:20:00Z) — DOCUMENTAL ONLY

**Stato**: 🟢 **Phase C0-quater CLOSED**. Include il ciclo completo: audit READ-ONLY del catalogo dungeon live + finalization Batch 1 Lv1-15 con 7 decisioni PM lockate. Attesa **PM Gate review formale** del deliverable prima di sbloccare **Phase C0-quinquies** (Batch 2 Lv16-30) — autorizzata come next step.

### File autoritativi C0-quater (untracked, ready for PM review)

| File | Path | SHA256 |
|---|---|---|
| Live Dungeon Audit (MD) | `/app/memory/r18_5_phase_c0quater_live_dungeon_audit.md` | `9252ee01c27e15c948fdf75190ebd706239f6c41a6b306ca4e450d0b73c5fe14` |
| Live Dungeon Audit (JSON) | `/app/memory/r18_5_phase_c0quater_live_dungeon_audit.json` | `db8329cf803a552cac71427fd5746555b4395741c4403592a1ebc9ef36d09912` |
| Batch 1 Informed Finalization (MD) | `/app/memory/r18_5_phase_c0quater_batch1_informed_final.md` | `7f59bfb297d10ad55cd9723a37ca8ed38a3a5c0365b81063ab19e2ee4f8ce2d2` |
| Batch 1 Informed Finalization (JSON) | `/app/memory/r18_5_phase_c0quater_batch1_informed_final.json` | `f43beb6fd604105d95bd3313b66be625504185cb96ce963ac6e9391fb6f6ad40` |

**Predecessore superseded**: `/app/memory/r18_5_phase_c0quater_batch1_lv1_15_dungeon_matrix.md/.json` (DRAFT deprecato post-audit, preservato per audit trail).

### 🎯 Batch 1 finale — 12 dungeon Lv1-15 Normal Track (party_size=3)

**8 LIVE approvati** (nessuna re-creation richiesta, `name_it` già validato DB):

| # | Slug | Nome IT | Lv | Lore source (post-expansion) |
|:---:|---|---|:---:|:---:|
| 1 | `sewer-nest` | Nido nelle Fogne | 1 | Aveol (ex-tag `urban` merged) |
| 2 | `goblin-warrens` | Tane dei Goblin | 2 | Halodi (ex-tag `frontiera` merged) |
| 3 | `bandit-hideout` | Covo dei Banditi | 2 | Aveol (ex-tag `urban` merged) |
| 4 | `shadow-crypts` | Cripte d'Ombra | 3 | Irthe |
| 5 | `druid-grove` | Bosco dei Druidi Corrotti | 3 | Soe |
| 6 | `cursed-mines` | Miniere Maledette | 4 | Efreto |
| 7 | `sunken-library` | Biblioteca Sommersa | 4 | **Memoria** (nuova fonte standalone) |
| 8 | `lich-sanctum` | Santuario del Lich | 5 | Irthe |

**4 NEW DRAFT approvati** (design proposto, NO creation live in questa fase):

| # | Slug (PM-locked) | Nome IT proposta | Lv range | Lore source | Teaching |
|:---:|---|---|:---:|:---:|---|
| 9 | `chapel-of-silent-vows` | Cappella dei Voti Silenti | Lv7-9 | Aveol | Priest PRIMARY |
| 10 | `forgotten-shrine-of-adalan` | Santuario Dimenticato di Adalan | Lv9-11 | Adalan | Mage PRIMARY |
| 11 | `bandit-warlord-hideout` | Nascondiglio del Signore dei Briganti | Lv11-13 | Aveol | Proficiency teaching narrativo |
| 12 | `broken-tower-of-adalan` | Torre Spezzata di Adalan | Lv13-15 | Adalan | Transition Batch 2 + primo Epic |

### 📚 Lore expansion 17 → 22 fonti (PM decisions lockate)

**Espansione pragmatica approvata** — 5 nuove fonti standalone, **zero merge**, **zero breaking change** su `lore_meta.py`:

| Nuova fonte | Origin tag live | Dungeon che la usano | Modalità |
|:---:|:---:|---|:---:|
| **Memoria** | `memoria` | sunken-library (Batch 1), silent-monastery-5p (Elite) | Standalone (recommended Emergent) |
| **Mare** | `mare` | pirate-fleet-5p (Elite B2) | **Standalone** (Q1 PM = no merge sotto Velur) |
| **Draco** | `draco` | dragons-hoard (Batch 2 head), dragon-vault (raid B5) | Standalone (recommended Emergent) |
| **Celeste** | `celeste` | celestial-citadel-5p (Elite B5) | **Standalone** (Q2 PM = no merge sotto Alberi della Vita) |
| **Infernale** | `infernale` | obsidian-arena-5p, infernal-pit-5p (Elite B2/B4) | **Standalone** (Q3 PM = no merge sotto Luna Morta) |

**Sub-tag preservato** (non conta come nuova fonte): `fucina` resta come sotto-classe di **Ambash** (Fucine di Ambash — iron-foundry-5p, clockwork-vault-5p).

**Totale post-expansion**: **22 fonti** (target 22-25 rispettato, spazio per 3 future).

### ⚔️ Elite/Group Dungeon Track — 12 dungeon 5-player live approvati

**Governance PM #5**: NO re-team-size, NO congelamento, NO deprecazione. Bracket documentale approvato:

| Bracket | Count | Dungeon 5-player |
|:---:|:---:|---|
| **Batch 1 Elite (Lv1-15)** | 5 | wolf-den-5p, frost-cave-5p, salt-marsh-5p, iron-foundry-5p, silent-monastery-5p |
| **Batch 2 Elite (Lv16-30)** | 3 | pirate-fleet-5p, obsidian-arena-5p, clockwork-vault-5p |
| **Batch 3 Elite (Lv31-45)** | 1 | world-tree-roots-5p |
| **Batch 4 Elite (Lv46-55)** | 1 | infernal-pit-5p |
| **Batch 5 Elite (Lv56-60)** | 2 | voidspire-5p, celestial-citadel-5p |
| **TOTAL** | **12** | Equivalente al catalogo live 5p |

### 🔴 3 drift endgame documentati — known drift, no rewrite (PM decision)

| Slug | Drift | Governance PM |
|---|---|---|
| `voidspire-5p` | `required_level=11` LIVE vs Vuoto endgame → Batch 5 Elite (Lv56-60) | **Known drift, NO runtime rewrite** |
| `infernal-pit-5p` | `required_level=12` LIVE vs Infernale endgame → Batch 4 Elite (Lv46-55) | **Known drift, NO runtime rewrite** |
| `celestial-citadel-5p` | `required_level=13` LIVE vs Celeste endgame → Batch 5 Elite (Lv56-60) | **Known drift, NO runtime rewrite** |

**Rationale**: il drift è puramente design-vs-runtime. DB rimane invariato. Riallineamento eventuale in future Phase C tech (BLOCCATA).

### 🐉 Raid bracket live approvati

| Raid slug | Nome IT | Lore | Bracket approvato |
|---|---|:---:|:---:|
| `broken-bastion-siege` | Assedio al Bastione Spezzato | Ergolat | **Batch 3 Raid (Lv31-45)** |
| `necropolis-bells` | Necropoli delle Mille Campane | Irthe | **Batch 4 Raid (Lv46-55)** |
| `dragon-vault` | Volta del Drago Addormentato | **Draco** (nuova standalone) | **Batch 5 Raid (Lv56-60) — endgame capstone** |

**Raid pool R18.5**: 3 live + **9 nuovi da progettare** in gate futuri = 12 raid target totali.

### 🔒 Ulteriori decisioni PM lockate in questa chiusura

- **`training-yard`**: escluso da bracket R18.5, resta utility onboarding (fuori sistema Batch 1-5)
- **`dragons-hoard` + `storm-spire`**: spostati a **Batch 2 head** (Lv16-30), NON Batch 1 tail. Drift `required_level=6` LIVE accettato as-is.
- **Party size policy**: variabile 3p Normal Track + 5p Elite/Group Track. Batch 1 Normal Track = solo 3p verbatim.

### 🛡️ Governance state C0-quater CLOSED

- ✅ **36 sigilli byte-identical** — nessuna modifica ai sealed files (verificato `pytest backend/tests/backend_r18_4_sealed_integrity_test.py` → 6 passed 0.39s)
- ✅ **Zero code changes** (`.py` / `.js` / `.jsx` / `.tsx` / `.ts` intatti, verificato via `git status`)
- ✅ **Zero DB writes** — `dungeons` (24), `raid_dungeons` (3), `expeditions` (3) tutti invariati pre-post audit
- ✅ **Zero migrations / apply scripts**
- ✅ **Zero dungeon/raid creation live** (4 nuovi Batch 1 = design docs)
- ✅ **`lore_meta.py` invariato** (espansione 17→22 puramente documentale)
- ✅ **Naming canonical Mage/Priest** verbatim in tutti i deliverable (NO drift Wizard/Cleric)
- ✅ **Aritmetica verificata programmaticamente**: 12 dungeon Batch 1 (8+4), 12 Elite Track (5+3+1+1+2), 3 raid, 8 orphan lore tags → 22 fonti expansion, 8 residual risks, 15 Open Questions PM

### 🎯 Handoff — Phase C0-quinquies Batch 2 AUTHORIZED

**Prossimo step autorizzato**: **Phase C0-quinquies** — Batch 2 (Lv16-30) Normal Track = **14 dungeon 3-player** (incluso `dragons-hoard` + `storm-spire` come head) + **2 raid introduttivi** Lv20-30 (party size raid `PENDING PM` — preferenza orchestratore 5p).

**Deliverable Batch 2 attesi**:
- `/app/memory/r18_5_phase_c0quinquies_batch2_lv16_30_matrix.md`
- `/app/memory/r18_5_phase_c0quinquies_batch2_lv16_30_matrix.json`

**Batch 3-5 + Phase C tech dry-run**: 🔒 **BLOCCATI** fino a nuovo gate PM (governance sigilli `derive_ui_4state`/`item_public()` invariata).

**Files chiave R18.5 (cumulativo aggiornato)**:
- Predecessori: `phase_a_discovery`, `phase_b1_design_lock`, `phase_b2_implementation_plan`, `gate1_pm_decisions`, `phase_c0_item_table_drafting_support`, `phase_c0bis_progression_dungeon_raid_matrix`, `pm_workspace_master`
- Gate 2: `r18_5_gate2_pm_decisions.md/.json`, `r18_5_phase_c0ter_live_class_matrix.md/.json`
- **C0-quater** (nuovo): `r18_5_phase_c0quater_batch1_lv1_15_dungeon_matrix.md/.json` (DRAFT superseded), `r18_5_phase_c0quater_live_dungeon_audit.md/.json`, `r18_5_phase_c0quater_batch1_informed_final.md/.json`

**R18.5 status flow (aggiornato)**:
`Phase A` ✅ → `Phase B.1/B.2` ✅ → `Gate 1` ✅ → `Phase C0` ✅ → `Phase C0-bis` ✅ → `Gate 2` ✅ + `Phase C0-ter` ✅ → **`Phase C0-quater Batch 1` ✅ CLOSED** → *`Phase C0-quinquies Batch 2`* 🟡 *AUTHORIZED — in progress* / *Phase C tech dry-run* 🔒 *BLOCKED gate PM*

## R18.5 Phase C0-quinquies Batch 2 Lv16-30 — CLOSED (2026-07-06T21:40:00Z) — DOCUMENTAL ONLY

**Stato**: 🟢 **Phase C0-quinquies Batch 2 CLOSED**. 14 dungeon Normal Track 3p + 2 raid introduttivi 5p lockati. PM decisions Q1-Q12 approvate in blocco. Prossimo step autorizzato: **Phase C0-sexies Batch 3 Lv31-45**.

### File autoritativi C0-quinquies Batch 2 (tracked, SHA256 verified)

| File | Path | SHA256 |
|---|---|---|
| Batch 2 Matrix (MD) | `/app/memory/r18_5_phase_c0quinquies_batch2_lv16_30_matrix.md` | `f9d9a62d172e7f62ca6f89a7485b4702e3c5d76e66868b09745622c6e905fa5a` |
| Batch 2 Matrix (JSON) | `/app/memory/r18_5_phase_c0quinquies_batch2_lv16_30_matrix.json` | `9a890af9a02a2b077e42d60a53b8c171cd7ac187b52227e0a80753b6c4f849e1` |

**Auto-commit**: `e059b66` (`+861` insertions, 3 file, zero source/sealed touched).

### 🎯 14 dungeon Batch 2 approvati (Lv16-30, Normal Track, party_size=3)

**2 LIVE head — drift `required_level=6` accepted PM4** (nessuna re-creation, `name_it` DB validato):

| # | Slug | Nome IT | Lv range | Lore source |
|:---:|---|---|:---:|:---:|
| 1 | `dragons-hoard` | Tesoro del Drago | Lv16 | **Draco** (nuova standalone) |
| 2 | `storm-spire` | Guglia della Tempesta | Lv17 | Ambash |

**12 NEW DRAFT approvati** (design proposto, NO creation live, naming IT PM-approved in blocco Q2):

| # | Slug | Nome IT | Lv range | Lore source |
|:---:|---|---|:---:|:---:|
| 3 | `blackpine-thicket` | Boschetto del Pino Nero | Lv17-19 | Greatwood/Elfwood |
| 4 | `ironhold-keep` | Forte di Ferro | Lv18-19 | **Krastlov** (multi-bracket) |
| 5 | `worldroot-hollow` | Cavità delle Radici del Mondo | Lv20-22 | Alberi della Vita |
| 6 | `veiled-forge` | Fucina Velata | Lv21-23 | Ambash (sub-tag `fucina`) |
| 7 | `tidebound-cove` | Insenatura della Marea Vincolata | Lv22-24 | **Mare** (nuova standalone) |
| 8 | `hollow-monastery` | Monastero Cavo | Lv23-25 | **Memoria** (nuova standalone) |
| 9 | `wild-hunt-lair` | Tana della Caccia Selvaggia | Lv24-25 | Soe |
| 10 | `frostbound-vault` | Cripta Legata al Gelo | Lv26-27 | Halodi + **Krastlov** (co-source) |
| 11 | `sunken-shipyard` | Cantiere Sommerso | Lv27-28 | Velur + **Mare** (co-source) |
| 12 | `emberlord-hideout` | Nascondiglio del Signore delle Braci | Lv28-29 | Aveol |
| 13 | `stormcaller-vault` | Cripta dell'Evocatempesta | Lv28-30 | **Draco** (secondo dungeon Draco Batch 2) |
| 14 | `bonefall-crypt` | Cripta della Caduta d'Ossa | Lv29-30 | **Krastlov** |

### 🐉 2 raid introduttivi Batch 2 approvati (Lv20-30, party_size=5p verbatim Q1)

| # | Slug | Nome IT | Lv range | Party size | Lore source | Boss |
|:---:|---|---|:---:|:---:|:---:|---|
| R1 | `krastlov-siege` | Assedio delle Torri Gemelle di Krastlov | Lv22-25 | **5** | **Krastlov** (fonte orfana Batch 1) | Comandante Senza Memoria (lich minore, 2 fasi) |
| R2 | `bloodgrove-uprising` | Rivolta del Bosco Sanguigno | Lv28-30 | **5** | Alberi della Vita + Greatwood/Elfwood | Il Cuore Corrotto degli Alberi della Vita (spirito-radice, 3 fasi) |

**Regola party size lockata (PM decision Q1)**: **Normal=3p · Elite=5p · Raid=5p**. No 6p/4p, no conversione a 3p.

### 🌿 Krastlov overlap accepted (multi-bracket coerente)

**PM decision Q9 LOCKED** — Krastlov usata 4× cumulative senza ridistribuzione:

| Dungeon/Raid | Bracket | Ruolo Krastlov |
|---|:---:|---|
| `frozen-vigil-hall` | Batch 1 Lv8-11 | Uso Batch 1 |
| `ironhold-keep` | Batch 2 Lv18-19 | Uso Batch 2 |
| `frostbound-vault` | Batch 2 Lv26-27 | Co-source Batch 2 |
| `bonefall-crypt` | Batch 2 Lv29-30 | Uso Batch 2 |
| `krastlov-siege` (raid) | Batch 2 Lv22-25 | Raid Batch 2 |

**Rationale**: coerenza narrativa multi-bracket (Krastlov = territorio esteso con siti multipli). No lore drift.

### 🎨 Naming player-facing Batch 2 approved in blocco (PM decision Q2-Q7)

- **12 nomi IT nuovi dungeon**: approvati verbatim (nessuna rinomina selettiva).
- **2 nomi IT raid**: approvati verbatim.
- **Slug lock**: 14 dungeon + 2 raid slug PM-locked.
- **Bracket naming**: "Batch 2 Normal Track Lv16-30" + "Batch 2 Raid Intro Lv20-30" ufficiali.
- **`stormcaller-vault` "Cripta dell'Evocatempesta"** — accepted (Q4), NO drift Wizard.

### 🎁 Loot target Batch 2 rispettato

**Tier distribution**:
- **T1** — Coda residua (accessori occasionali)
- **T2** — **Prevalente ovunque** ✅
- **T3** — Introduttivo su boss mid+ (dungeon #5+, raid) ✅
- **T4** — Assente (riservato Batch 3+) ✅
- **T5** — Assente (riservato Batch 4/5) ✅

**Rarity distribution**:
- **Common** — Regolare ovunque
- **Uncommon** — Prevalente (shift vs Common prevalente Batch 1)
- **Rare** — Regolare boss mid+
- **Epic** — Solo boss finale `bonefall-crypt` + boss finale raid `bloodgrove-uprising` (2-3 slot totali max) — direzionale, drop rate numerici differiti (PM Q8 accepted)
- **Legendary** — **Assente ✅** (T5 only, riservato Batch 5 endgame)

### 🛡️ Governance state Batch 2 CLOSED

- ✅ **36 sigilli byte-identical** (`pytest backend/tests/backend_r18_4_sealed_integrity_test.py` → 6 passed 0.39s)
- ✅ **Zero code changes** (`.py` / `.js` / `.jsx` / `.tsx` / `.ts` intatti)
- ✅ **Zero DB writes** — `dungeons` (24), `raid_dungeons` (3), `expeditions` (3) invariati
- ✅ **Zero migrations / apply scripts / hard delete**
- ✅ **Zero dungeon/raid creation live** (12 nuovi dungeon + 2 raid = design docs only)
- ✅ **`lore_meta.py` invariato**
- ✅ **NO party_size rewrite** (5p raid verbatim, Elite Track drift `voidspire-5p` / `infernal-pit-5p` / `celestial-citadel-5p` **not touched Batch 2** — resta known drift no-rewrite)
- ✅ **NO required_level rewrite** (drift `dragons-hoard`/`storm-spire` Lv6 vs bracket Lv16-17 documentato risk_3 LOW)
- ✅ **Aritmetica verificata**: 14 dungeon Batch 2 (2 LIVE + 12 NEW), 2 raid (0 LIVE + 2 NEW), 11/22 lore sources usate, 4 orphan Batch 1 covered, 11 risks (2 MEDIUM + 9 LOW), 12 Open Questions PM Q1-Q12 **ALL LOCKED**

### 📊 R18.5 catalogo dungeon cumulative post-Batch 2

| Track | Batch 1 | Batch 2 | Batch 3+ | Total design |
|---|:---:|:---:|:---:|:---:|
| **Normal 3p** | 12 (8 LIVE + 4 NEW) | 14 (2 LIVE + 12 NEW) | 26 residui (Lv31-60) | ~52 |
| **Elite 5p** | 5 LIVE | 3 LIVE | 4 LIVE (B3+B4+B5) | 12 LIVE |
| **Raid 5p** | — | 2 NEW | 1 LIVE B3 + 2 NEW B3 + 6 futuri | 12 total |

### 🎯 Handoff — Phase C0-sexies Batch 3 AUTHORIZED

**Prossimo step autorizzato**: **Phase C0-sexies** — Batch 3 (Lv31-45) Normal Track = **16 dungeon 3-player** (mix live + new) + **3 raid intermedi Lv31-45** (1 LIVE `broken-bastion-siege` + 2 NEW DRAFT, party size **5p verbatim**).

**Regole design Batch 3 (PM lockate)**:
- **T3 prevalente + T4 introduttivo raro** (solo boss dungeon o raid)
- **Rare prevalenti + Epic peso significativo** (drop rate più alto vs Batch 1-2)
- **Legendary assenti**
- Dungeon più tecnici, main stat più rilevante, armor/weapon proficiency peso maggiore
- Primi **gear check seri** (min ILVL suggerito, non enforced runtime)
- Utility item più rilevanti, materiali più specifici
- Raid intermedi non banali

**Elite Track già assegnato Batch 3**: `world-tree-roots-5p` (traccia parallela, NON conteggiato nei 16 normal).

**Deliverable Batch 3 attesi**:
- `/app/memory/r18_5_phase_c0sexies_batch3_lv31_45_matrix.md`
- `/app/memory/r18_5_phase_c0sexies_batch3_lv31_45_matrix.json`

**Batch 4-5 + Phase C tech dry-run + Item table 1500**: 🔒 **BLOCCATI** fino a nuovo gate PM.

**Files chiave R18.5 (cumulativo aggiornato)**:
- Predecessori: `phase_a_discovery`, `phase_b1_design_lock`, `phase_b2_implementation_plan`, `gate1_pm_decisions`, `phase_c0_item_table_drafting_support`, `phase_c0bis_progression_dungeon_raid_matrix`, `pm_workspace_master`, `gate2_pm_decisions`, `phase_c0ter_live_class_matrix`
- C0-quater: `phase_c0quater_live_dungeon_audit`, `phase_c0quater_batch1_informed_final`
- **C0-quinquies** (nuovo): `r18_5_phase_c0quinquies_batch2_lv16_30_matrix.md/.json`

**R18.5 status flow (aggiornato)**:
`Phase A` ✅ → `Phase B.1/B.2` ✅ → `Gate 1` ✅ → `Phase C0` ✅ → `Phase C0-bis` ✅ → `Gate 2` ✅ + `Phase C0-ter` ✅ → `Phase C0-quater Batch 1` ✅ CLOSED → **`Phase C0-quinquies Batch 2`** ✅ **CLOSED** → *`Phase C0-sexies Batch 3`* 🟡 *AUTHORIZED — pending write* / *Phase C tech dry-run + Item table 1500* 🔒 *BLOCKED gate PM*

## R18.5 Phase C0-sexies Batch 3 Lv31-45 — CLOSED (2026-07-07T08:35:00Z) — DOCUMENTAL ONLY

**Stato**: 🟢 **Phase C0-sexies Batch 3 CLOSED**. 16 dungeon Normal Track 3p + 3 raid intermedi 5p (1 LIVE + 2 NEW DRAFT) lockati. PM decisions Q1-Q16 approvate in blocco (Q1/Q2/Q5/Q15/Q16 verbatim). Prossimo step autorizzato: **Phase C0-septies Batch 4 Lv46-55** (NO Phase C tech dry-run, NO item table 1500 ora).

### File autoritativi C0-sexies Batch 3 (SHA256 verified)

| File | Path | SHA256 |
|---|---|---|
| Batch 3 Matrix (MD) | `/app/memory/r18_5_phase_c0sexies_batch3_lv31_45_matrix.md` | `6deb0890d943d963eb19abc152dff6602192f18e034b4273daea7005450c1061` |
| Batch 3 Matrix (JSON) | `/app/memory/r18_5_phase_c0sexies_batch3_lv31_45_matrix.json` | `e9045a1d6d6b4cbbfbd4830a81e278de107d1b23181719d8da27d3d9dbe72963` |

### 🎯 16 dungeon Batch 3 approvati (Lv31-45, Normal Track, party_size=3, tutti NEW DRAFT)

**Gap analysis critical**: gli 11 dungeon 3p live sono già tutti allocati (8 in Batch 1 + 2 in Batch 2 + `training-yard` escluso). **0 LIVE disponibili** in Batch 3 → tutti **NEW DRAFT** (PM Q1 approved).

#### Early Lv31-35 (5 dungeon)

| # | Slug | Nome IT | Lv range | Lore source |
|:---:|---|---|:---:|:---:|
| 1 | `bastion-of-alevora` | Bastione di Alevora | Lv31-32 | **Alevora** (orfana B1 coperta) |
| 2 | `arcane-fault-line` | Faglia Arcana | Lv32-33 | **Faglie arcane** (orfana B1 coperta) |
| 3 | `moonwake-abbey` | Abbazia della Veglia Lunare | Lv33-34 | **Luna Morta** (orfana B1 coperta) |
| 4 | `soulforge-crucible` | Crogiolo della Forgia d'Anime | Lv34-35 | **Ciclo delle anime** (orfana B1 coperta) |
| 5 | `hollow-crown-halls` | Sale della Corona Cava | Lv34-35 | Aveol |

#### Mid Lv36-40 (5 dungeon)

| # | Slug | Nome IT | Lv range | Lore source |
|:---:|---|---|:---:|:---:|
| 6 | `ashborn-ravine` | Gola delle Braci Nate | Lv36-37 | **Infernale** (nuova standalone) |
| 7 | `stygian-reach` | Landa di Stigia | Lv37-38 | Ciclo delle anime |
| 8 | `sundered-observatory` | Osservatorio Frantumato | Lv38-39 | Faglie arcane |
| 9 | `mercenary-holdfast` | Roccaforte dei Mercenari | Lv39-40 | Alevora |
| 10 | `wyrmscale-pass` | Passo delle Scaglie di Vermeide | Lv40 | Draco |

#### Late Lv41-45 (6 dungeon)

| # | Slug | Nome IT | Lv range | Lore source |
|:---:|---|---|:---:|:---:|
| 11 | `necropolis-approach` | Approccio alla Necropoli | Lv41-42 | Luna Morta |
| 12 | `starfall-basilica` | Basilica della Stella Caduta | Lv42-43 | **Celeste** (nuova standalone) |
| 13 | `iron-legion-outpost` | Avamposto della Legione di Ferro | Lv43-44 | **Krastlov** (5× cum ACCEPTED) |
| 14 | `wraithbound-ossuary` | Ossario dei Vincolati Spettrali | Lv44-45 | Ciclo delle anime |
| 15 | `heretic-cathedral` | Cattedrale degli Eretici | Lv44-45 | Aveol |
| 16 | `black-forge-of-ergolat` | Fucina Nera di Ergolat | Lv45 | **Ergolat** (orfana B1 coperta) |

### 🐉 3 raid intermedi Batch 3 approvati (Lv31-45, party_size=5p verbatim)

| # | Slug | Nome IT | Lv range | Party | Status | Lore source | Boss |
|:---:|---|---|:---:|:---:|:---:|:---:|---|
| R1 | `arcane-schism` | Scisma Arcano | Lv33-36 | **5** | NEW DRAFT | Faglie arcane | Il Rift-Overseer Anonimo (3 fase) |
| R2 | `broken-bastion-siege` | Assedio al Bastione Spezzato | Lv37-40 | **5** | **LIVE** | **Ergolat** (orfana B1 coperta) | Comandante del Bastione (LIVE DB) |
| R3 | `souldrain-abyss` | Abisso della Drenaggio d'Anime | Lv42-45 | **5** | NEW DRAFT | Ciclo delle anime | L'Antenato Divoratore (3 fase) |

**`broken-bastion-siege` LIVE drift**: **known drift, NO rewrite ora** — potenziali drift `required_level` / `required_team_size` / meccaniche live-vs-design accettati as-is (governance PM verbatim).

### 🌿 Krastlov 5× cumulative ACCEPTED (Q5 verbatim)

**PM decision Q5 verbatim**: Krastlov **5× cumulative accettato** — macro-regione multi-bracket con identità, scala, nemici, meccaniche e reward diversi. **NO cap, NO redistribuzione**. Regola futura: **da Batch 4 monitorare varietà lore** (raccomandazione PM, non blocco rigido).

| Dungeon/Raid | Bracket | Lv | Ruolo Krastlov |
|---|:---:|:---:|---|
| `frozen-vigil-hall` | B1 | Lv8-11 | Uso Batch 1 |
| `ironhold-keep` | B2 | Lv18-19 | Uso Batch 2 |
| `frostbound-vault` | B2 | Lv26-27 | Co-source Batch 2 |
| `bonefall-crypt` | B2 | Lv29-30 | Uso Batch 2 |
| `krastlov-siege` (raid) | B2 | Lv22-25 | Raid Batch 2 |
| `iron-legion-outpost` | B3 | Lv43-44 | Uso Batch 3 (5° cumulative) |

### 🎁 Loot target Batch 3 rispettato (design mid-game serio)

**Tier distribution**:
- **T1** — Assente (fuori bracket)
- **T2** — Coda residua (accessori early Lv31-35)
- **T3** — **Prevalente ovunque** ✅
- **T4** — **Raro / introduttivo** — solo boss dungeon #5, #6+, #16 + tutti i raid ✅
- **T5** — Assente (riservato Batch 4/5) ✅

**Rarity distribution**:
- **Common** — Coda residua early Lv31-35
- **Uncommon** — Regolare ovunque
- **Rare** — **Prevalente** ovunque ✅
- **Epic** — **Peso alto** — **~20 slot** (12 boss finale dungeon #5-16 + 4 pre-boss late + 6 raid Epic slot) ✅
- **Legendary** — **Assente ✅** (solo 2 hint crafting no-drop: `frammento di aureola` #12, `frammento di Ciclo` R3)

### 🛡️ Gear check seri Batch 3 (documentali, non enforced runtime)

- **Min ILVL range**: 31-45 (dungeon) · 34-43 (raid)
- Ogni encounter documenta `min_ilvl`, `role_required`, `proficiency_required`, `utility_recommended`
- **Proficiency runtime enforcement**: 🔒 **BLOCCATO** (governance PM)
- Main stat peso significativo: STR (#1, #9, #13), INT (#2, #8), WIS (#3, #11), DEX (#4, #7)
- Utility item peso maggiore: fire-resist obbligatoria #6, soul-veil obbligatoria #14/R3, siege-focus banner obbligatoria R2

### 📚 Lore coverage Batch 3 (9 su 22 usate, 5 orfane B1 finalmente coperte)

**5 orfane Batch 1 coperte in Batch 3**:
- **Alevora** (2× #1, #9)
- **Ergolat** (dungeon #16 + raid R2 LIVE)
- **Faglie arcane** (3× #2, #8, R1)
- **Luna Morta** (2× #3, #11)
- **Ciclo delle anime** (4× #4, #7, #14, R3)

**Nuove standalone introdotte**: Infernale (#6), Celeste (#12).
**Multi-bracket accepted**: Draco (3× cum), Aveol (4× cum), Krastlov (5× cum PM Q5 verbatim).

### 🛡️ Governance state Batch 3 CLOSED

- ✅ **36 sigilli byte-identical** (`pytest backend/tests/backend_r18_4_sealed_integrity_test.py` → 6 passed 0.38-0.43s)
- ✅ **Zero code changes** (`.py` / `.js` / `.jsx` / `.tsx` / `.ts` intatti)
- ✅ **Zero DB writes** — `dungeons` (24), `raid_dungeons` (3), `expeditions` (3) invariati
- ✅ **Zero migrations** / apply scripts / hard delete
- ✅ **Zero dungeon/raid creation live** (16 nuovi dungeon + 2 raid = design docs only)
- ✅ **`lore_meta.py` invariato**
- ✅ **Zero party_size rewrite** (5p raid verbatim, Elite Track drift not touched)
- ✅ **Zero required_level rewrite** (R2 broken-bastion-siege drift known no-rewrite)
- ✅ **Classi canoniche Warrior/Rogue/Mage/Priest/Ranger verbatim** — NO drift Wizard/Cleric
- ✅ **Aritmetica**: 16 dungeon (0 LIVE + 16 NEW), 3 raid (1 LIVE + 2 NEW), 9/22 lore usate, ~20 slot Epic, 0 Legendary drop

### 📊 R18.5 catalogo dungeon cumulative post-Batch 3

| Track | B1 | B2 | B3 | Sub-total post-B3 | Riservato B4/B5 |
|---|:---:|:---:|:---:|:---:|:---:|
| **Normal 3p** | 12 (8L+4N) | 14 (2L+12N) | 16 (0L+16N) | **42** | ~10-19 |
| **Elite 5p LIVE** | 5 | 3 | 1 (world-tree-roots-5p) | **9** | 3 (1 B4 + 2 B5) |
| **Raid 5p** | — | 2 NEW | 3 (1L+2N) | **5** | 7 futuri |

### 🎯 Handoff — Phase C0-septies Batch 4 AUTHORIZED (PM Q16 = A)

**Prossimo step autorizzato**: **Phase C0-septies** — Batch 4 (Lv46-55) Normal + Elite Track + Raid late-game.

**Scope Batch 4 (PM verbatim)**:
- **10 dungeon totali Lv46-55** (Normal 3p + Elite 5p, distinzione esplicita richiesta)
- **3 raid late-game Lv46-55**: 1 LIVE `necropolis-bells` + 1-2 NEW DRAFT (party_size=5 verbatim)
- Target macro cumulativo: **60 dungeon totali + 12 raid totali** (documentare aritmetica trasparente)

**Regole design Batch 4 (PM verbatim)**:
- **T4 prevalente + T5 raro / hint**
- **Epic peso alto + Rare meno centrale**
- **NO Legendary drop finale** (solo hint narrativo/no-drop consentito)
- Gear check **forti** · Main stat **importante** · Proficiency **obbligatoria nel design** (no runtime)
- Utility item più frequenti, materiali rari, boss riconoscibili, achievement/ranking seri
- Preparazione al Batch 5 / Lv60 endgame

**Lore guidance Batch 4 (PM raccomandazione)**: **aumentare varietà, ridurre Krastlov se non necessario**. Candidate preferenziali: Ergolat, Luna Morta, Infernale, Celeste, Memoria, Draco, Faglie arcane, Irthe, Halodi, Alevora.

**Deliverable Batch 4 attesi**:
- `/app/memory/r18_5_phase_c0septies_batch4_lv46_55_matrix.md`
- `/app/memory/r18_5_phase_c0septies_batch4_lv46_55_matrix.json`

**Batch 5 + Phase C tech dry-run + Item table 1500**: 🔒 **BLOCCATI** fino a gate PM formale (Q16 verbatim: no tech dry-run/item table ora).

**Files chiave R18.5 (cumulativo aggiornato)**:
- Predecessori: `phase_a_discovery`, `phase_b1_design_lock`, `phase_b2_implementation_plan`, `gate1_pm_decisions`, `phase_c0_item_table_drafting_support`, `phase_c0bis_progression_dungeon_raid_matrix`, `pm_workspace_master`, `gate2_pm_decisions`, `phase_c0ter_live_class_matrix`
- C0-quater: `phase_c0quater_live_dungeon_audit`, `phase_c0quater_batch1_informed_final`
- C0-quinquies: `r18_5_phase_c0quinquies_batch2_lv16_30_matrix.md/.json`
- **C0-sexies** (nuovo): `r18_5_phase_c0sexies_batch3_lv31_45_matrix.md/.json`

**R18.5 status flow (aggiornato)**:
`Phase A` ✅ → `Phase B.1/B.2` ✅ → `Gate 1` ✅ → `Phase C0` ✅ → `Phase C0-bis` ✅ → `Gate 2` ✅ + `Phase C0-ter` ✅ → `Phase C0-quater Batch 1` ✅ CLOSED → `Phase C0-quinquies Batch 2` ✅ CLOSED → **`Phase C0-sexies Batch 3`** ✅ **CLOSED** → *`Phase C0-septies Batch 4`* 🟡 *AUTHORIZED — pending write* / *Phase C tech dry-run + Item table 1500* 🔒 *BLOCKED gate PM*

## R18.5 Phase C0-septies Batch 4 Lv46-55 — CLOSED (2026-07-07T08:40:00Z) — DOCUMENTAL ONLY

**Stato**: 🟢 **Phase C0-septies Batch 4 CLOSED**. 10 dungeon totali Lv46-55 (9 Normal 3p NEW + 1 Elite 5p LIVE) + 3 raid late-game 5p (1 LIVE + 2 NEW) lockati. PM decisions Q1-Q18 approvate in blocco (Q1=D chiarimento definitivo, Q17 GO, Q18=A Batch 5 endgame). Prossimo step autorizzato: **Phase C0-octies Batch 5 Lv56-60 ENDGAME**.

### 🎯 Q1 RESOLVED — Chiarimento definitivo target macro dungeon (PM verbatim)

**Il target macro "60 dungeon totali" = SOLO Normal Dungeon Track 3p.**

| Traccia | Conteggio 60 | Status |
|---|:---:|---|
| **Normal Dungeon 3p** | ✅ **DENTRO 60** | 51/60 post-B4 |
| **Elite/Group 5p** | ❌ **FUORI 60** | contenuto parallelo storico |
| **Raid 5p** | ❌ **FUORI dungeon** | target separato 12 raid |

**Aritmetica cumulativa Normal 3p** (verificata):

| Batch | Normal 3p | Cumulative | Missing to 60 |
|---|:---:|:---:|:---:|
| B1 | 12 (8L + 4N) | 12 | 48 |
| B2 | 14 (2L + 12N) | 26 | 34 |
| B3 | 16 (0L + 16N) | 42 | 18 |
| **B4** | **9 (0L + 9N)** | **51** | **9** |
| **B5 endgame (target)** | **9** | **60** | **0** ✅ |

**Batch 5 deve completare 9 Normal 3p** per raggiungere **60/60**.

### File autoritativi C0-septies Batch 4 (SHA256 verified)

| File | Path | SHA256 |
|---|---|---|
| Batch 4 Matrix (MD) | `/app/memory/r18_5_phase_c0septies_batch4_lv46_55_matrix.md` | `e5f776b1d3f5e60d00f359e5949e7f2cb56ad86bd2a36e48220de5400ad9b2bd` |
| Batch 4 Matrix (JSON) | `/app/memory/r18_5_phase_c0septies_batch4_lv46_55_matrix.json` | `d7b416a04bc91783a77903885cabcc095064c1680c0b21f4f94eb3b5db037737` |

### 🎯 10 dungeon Batch 4 approvati (Lv46-55)

#### 9 Normal 3p NEW DRAFT — DENTRO conteggio 60

| # | Slug | Nome IT | Lv range | Lore source |
|:---:|---|---|:---:|:---:|
| 1 | `ashen-warcamp` | Accampamento delle Ceneri | Lv46-47 | Ergolat |
| 2 | `moonveil-shrine` | Santuario del Velo Lunare | Lv46-48 | Luna Morta |
| 3 | `hollow-flame-pit` | Fossa della Fiamma Cava | Lv47-48 | Infernale |
| 4 | `crimson-forge-outpost` | Avamposto della Forgia Cremisi | Lv48-49 | Halodi |
| 5 | `sepulcher-of-echoes` | Sepolcro degli Echi | Lv49-50 | Memoria |
| 6 | `black-lantern-conclave` | Conclave della Lanterna Nera | Lv50-51 | Irthe |
| 7 | `sunfallen-basilica` | Basilica del Sole Caduto | Lv51-52 | Celeste |
| 8 | `blightborn-caverns` | Caverne dei Nati dal Marciume | Lv53-54 | Efreto |
| 9 | `wyrmking-antechamber` | Anticamera del Re dei Vermi | Lv54-55 | **Draco** (bridge B5) |

#### 1 Elite 5p LIVE — FUORI conteggio 60 (traccia parallela)

| # | Slug | Nome IT | Lv range | Party | Lore | Status |
|:---:|---|---|:---:|:---:|:---:|:---:|
| — | `infernal-pit-5p` | Pozzo Infernale (proposta) | Lv46-55 | **5** | Infernale | **LIVE** (drift `required_level=12` known no-rewrite) |

### 🐉 3 raid late-game Batch 4 approvati (Lv46-55, party_size=5 verbatim) — FUORI conteggio dungeon

| # | Slug | Nome IT | Lv range | Party | Status | Lore | Boss |
|:---:|---|---|:---:|:---:|:---:|:---:|---|
| R1 | `necropolis-bells` | Necropoli delle Mille Campane | Lv46-50 | **5** | **LIVE** | Irthe | Il Campanaro dell'Aldilà (LIVE DB) |
| R2 | `emberking-siege` | Assedio del Re delle Braci | Lv50-53 | **5** | NEW DRAFT | Infernale | Il Re delle Braci Ardenti (3 fase) |
| R3 | `memoria-vault` | Volta della Memoria | Lv53-55 | **5** | NEW DRAFT | Memoria | Il Guardiano-Archivista dell'Oblio (3 fase) |

**Raid cumulative post-B4**: 8/12 (B5 = 1 LIVE `dragon-vault` + 3 NEW = 4 finale, target 12 ✅ aligned).

**`necropolis-bells` LIVE drift**: **known drift, NO rewrite ora** — potenziali drift `required_level` / `required_team_size` / meccaniche live-vs-design accettati as-is (analogo policy `broken-bastion-siege` B3).

### 🌿 Lore recurrence 4× ACCEPTED (Q6-Q9 verbatim)

**PM decision Q6-Q9 verbatim**: recurrence 4× per Infernale, Memoria, Irthe, Draco **ACCEPTED** (analogo Krastlov 5×). **NO cap rigido**, ma **B5 variety watch OBBLIGATORIA**.

| Fonte | Cumulative post-B4 | Justification |
|---|:---:|---|
| **Infernale** | 4× (B3 + B4 dungeon + Elite + raid) | Nazione ostile late-game |
| **Memoria** | 4× (B1 + B2 + B4 dungeon + raid) | Biblioteca cosmica multi-bracket |
| **Irthe** | 4× (B1×2 + B4 dungeon + raid) | Undead late-game |
| **Draco** | 4× (B2×2 + B3 + B4) | Bridge verso `dragon-vault` capstone B5 |

**B5 variety watch OBBLIGATORIA**: evitare ulteriore concentrazione su queste 4 fonti + Krastlov (già 5×).

### 🎨 Naming player-facing Batch 4 approved in blocco (Q5, Q12, Q15 verbatim)

- **9 nomi IT nuovi dungeon**: approvati verbatim
- **2 nomi IT nuovi raid**: approvati verbatim
- **Slug lock**: 9 dungeon + 2 raid slug PM-locked
- **Bracket naming**: "Batch 4 Late Game Lv46-55" + "Batch 4 Raid Late-Game" ufficiali
- **Boss narrative** proposta: approvata verbatim

### 🎁 Loot target Batch 4 rispettato (design "late game vero")

**Tier distribution**:
- **T1-T2** — Assenti (fuori bracket)
- **T3** — Coda residua (accessori occasionali early Lv46-49)
- **T4** — **Prevalente ovunque** ✅
- **T5** — **Raro / hint crafting only** — NO drop diretto (allineato Q11 B3 accepted) ✅

**Rarity distribution**:
- **Common** — Assente
- **Uncommon** — Coda residua early Lv46-49
- **Rare** — Regolare (meno centrale vs Batch 3)
- **Epic** — **Peso alto** — **~30-32 slot** (Epic guaranteed su 9 boss finale + 4 pre-boss late + Elite Epic 2× + raid Epic 2-3×) ✅
- **Legendary** — **Assente drop ✅** — solo 7 hint crafting material (no drop): #5, #7, #9, `infernal-pit-5p`, R1, R2, R3

### 🛡️ Gear check forti Batch 4 (documentali, non enforced runtime)

- **Min ILVL range**: 46-54 (Normal 3p) · 48 (Elite 5p LIVE) · 47-53 (raid)
- **Proficiency obbligatoria nel design**: fire_resist T4 obbligatoria #3/#10/R2 · undead-slaying weapon obbligatoria #6/R1 · soul-veil T4 obbligatoria — **NO runtime enforcement** (governance PM)
- Main stat gate check serio: STR (#1, #4, R2), INT (#3, #5, R3), WIS (#2, #6, R1), DEX (#5, #8), mix (#7, #9, #10)
- Utility item peso maggiore: fire-resist potion, moon-veil, memory-lens, undead-slaying, light/shadow potion, poison-cleanse, siege banner, bell-ward trinket

### 📚 Lore coverage post-Batch 4 (~21/22 fonti)

**Fonti usate B4 (9 di 22)**: Ergolat, Luna Morta, Infernale, Halodi, Memoria, Irthe, Celeste, Efreto, Draco.

**Fonti NON usate B4 (PM guidance "varietà, ridurre Krastlov" rispettata)** ✅:
- Krastlov (5× stop-cumulative B3), Aveol (4× stop-cumulative B3), Faglie arcane (3× saturata B3), Ciclo delle anime (4× saturata B3), Alevora (riservata B5)

**Coverage cumulativa post-B4**: **~21 su 22 fonti** — **1 orfana residua** riservata **Batch 5 endgame** (nomi PENDING sync definitivo audit).

### 🛡️ Governance state Batch 4 CLOSED

- ✅ **36 sigilli byte-identical** (`pytest backend/tests/backend_r18_4_sealed_integrity_test.py` → 6 passed 0.37-0.38s)
- ✅ **Zero code changes** (`.py` / `.js` / `.jsx` / `.tsx` / `.ts` intatti)
- ✅ **Zero DB writes** — `dungeons` (24), `raid_dungeons` (3), `expeditions` (3) invariati
- ✅ **Zero migrations** / apply scripts / hard delete
- ✅ **Zero dungeon/raid creation live** (9 Normal + 2 raid nuovi = design docs only)
- ✅ **`lore_meta.py` invariato**
- ✅ **Zero party_size rewrite** (5p Elite+Raid verbatim)
- ✅ **Zero required_level rewrite** (`infernal-pit-5p` + `necropolis-bells` drift known no-rewrite)
- ✅ **Item table live creation ZERO** (target 1500 items BLOCCATO gate PM Q18=A verbatim)
- ✅ **Phase C tech dry-run NOT INITIATED** (Q18=A verbatim)
- ✅ **Classi canoniche Warrior/Rogue/Mage/Priest/Ranger verbatim** — NO drift
- ✅ **PM autonomous decision new = ZERO** (rispetto precisazione governance PM ribadita)

### 📊 R18.5 catalogo dungeon cumulative post-Batch 4 (Q1=D chiarimento)

| Track | B1 | B2 | B3 | B4 | Sub-total post-B4 | Riservato B5 | **Target macro** |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Normal 3p (DENTRO 60)** | 12 | 14 | 16 | **9** | **51** | 9 | **60** ✅ |
| Elite 5p LIVE (FUORI 60) | 5 | 3 | 1 (world-tree-roots-5p) | 1 (infernal-pit-5p) | 10 | 2 (voidspire-5p, celestial-citadel-5p) | 12 parallel |
| Raid 5p (FUORI dungeon) | 0 | 2 | 3 | 3 | 8 | 4 (1L+3N) | 12 ✅ |

### 🎯 Handoff — Phase C0-octies Batch 5 ENDGAME AUTHORIZED (PM Q18=A verbatim)

**Prossimo step autorizzato**: **Phase C0-octies** — Batch 5 (Lv56-60) ENDGAME vetta.

**Scope Batch 5 (PM verbatim)**:
- **9 Normal Dungeon 3p Lv56-60** (per raggiungere **60/60** cumulativo target macro)
- **Elite/Group 5p paralleli** se necessari, FUORI conteggio 60 (2 Elite LIVE: `voidspire-5p`, `celestial-citadel-5p`)
- **4 raid endgame Lv56-60** (per raggiungere **12/12** raid target): 1 LIVE `dragon-vault` + 3 NEW DRAFT (party_size=5 verbatim)

**Regole design Batch 5 (PM verbatim)**:
- **T5 prevalente + T4 ancora presente**
- **Epic dominante**
- **Legendary drop introduction consentita ma RARISSIMA**

**Regole LEGENDARY (PM strict verbatim)**:
- Legendary solo T5
- Massimo **15 nel catalogo reale** da 1500 items
- Batch 5 può introdurre alcuni **Legendary candidate** (indicativamente 3-5, con margine per gli altri in future gate)
- Ogni Legendary deve avere **utility unica** e **lore source forte**
- **NO Legendary generico +stat** · **NO Legendary shop** · **NO Legendary craft normale**

**Preparazione endgame (Batch 5 deve iniziare a preparare)**: ILVL endgame · raid farming · utility item · signature item future · ranking · mercato · gear optimization.

**Lore guidance Batch 5 (PM verbatim)**:
- Coprire **l'ultima lore source orfana residua** (1/22 residua post-B4)
- **Motivare ogni recurrence alta** (variety watch obbligatoria)
- Usare fonti adatte a endgame
- **Evitare altra concentrazione Krastlov** se non indispensabile

**Candidate forti B5**: Ergolat, Luna Morta, Infernale, Celeste, Memoria, Draco, Faglie arcane, Irthe, Halodi, Alevora, **Vuoto** (nuova candidata endgame introdotta dal PM).

**Deliverable Batch 5 attesi**:
- `/app/memory/r18_5_phase_c0octies_batch5_lv56_60_matrix.md`
- `/app/memory/r18_5_phase_c0octies_batch5_lv56_60_matrix.json`

**Phase C tech dry-run + Item table 1500**: 🔒 **BLOCCATI** fino a gate PM formale (Q18=A verbatim: no tech/no item table ora).

**Files chiave R18.5 (cumulativo aggiornato)**:
- Predecessori: `phase_a_discovery`, `phase_b1_design_lock`, `phase_b2_implementation_plan`, `gate1_pm_decisions`, `phase_c0_item_table_drafting_support`, `phase_c0bis_progression_dungeon_raid_matrix`, `pm_workspace_master`, `gate2_pm_decisions`, `phase_c0ter_live_class_matrix`
- C0-quater: `phase_c0quater_live_dungeon_audit`, `phase_c0quater_batch1_informed_final`
- C0-quinquies: `r18_5_phase_c0quinquies_batch2_lv16_30_matrix.md/.json`
- C0-sexies: `r18_5_phase_c0sexies_batch3_lv31_45_matrix.md/.json`
- **C0-septies** (nuovo): `r18_5_phase_c0septies_batch4_lv46_55_matrix.md/.json`

**R18.5 status flow (aggiornato)**:
`Phase A` ✅ → `Phase B.1/B.2` ✅ → `Gate 1` ✅ → `Phase C0` ✅ → `Phase C0-bis` ✅ → `Gate 2` ✅ + `Phase C0-ter` ✅ → `Phase C0-quater Batch 1` ✅ CLOSED → `Phase C0-quinquies Batch 2` ✅ CLOSED → `Phase C0-sexies Batch 3` ✅ CLOSED → **`Phase C0-septies Batch 4`** ✅ **CLOSED** → *`Phase C0-octies Batch 5 ENDGAME`* 🟡 *AUTHORIZED — pending write* / *Phase C tech dry-run + Item table 1500* 🔒 *BLOCKED gate PM*


---

## R18.5 Phase C0-octies Batch 5 Lv56-60 ENDGAME — CLOSED (2026-07-07T11:00:00Z) — DOCUMENTAL ONLY

**Stato**: 🟢 **Phase C0-octies Batch 5 ENDGAME CLOSED**. 9 Normal Dungeon 3p Lv56-60 NEW + 4 raid endgame 5p (1 LIVE `dragon-vault` + 3 NEW DRAFT: `void-cathedral`, `celestial-conclave`, `world-tree-collapse`) + 2 Elite/Group 5p LIVE paralleli fuori conteggio 60 (`voidspire-5p`, `celestial-citadel-5p`) lockati. PM decisioni Q1-Q21 approvate in blocco (Q1-Q4 GO in blocco, Q9 accept Draco 6× cumulative, Q13=A 7 Legendary approved, Q17 Vuoto approved come 17ª lore source, Q21 D→B sequenza Mini-Gate Legendary Discovery Chain → Phase D Item Table Drafting). Prossimo step autorizzato: **Mini-Gate Legendary Discovery Chain (STEP 8) → Phase D0 Item Table Blueprint (STEP 9)** in sequenza automatica. Phase C tech dry-run **NON in agenda ora**.

### 🎯 R18.5 Aritmetica catalogo — FINAL LOCK (60/60 + 12/12 + 12/12 + 22/22)

| Track | B1 | B2 | B3 | B4 | B5 | **Cumulative finale** | **Target macro** | **Status** |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Normal 3p** | 12 | 14 | 16 | 9 | **9** | **60** | 60 | ✅ **RAGGIUNTO** |
| **Elite/Group 5p (LIVE, fuori 60)** | 5 | 3 | 1 | 1 | **2** | **12** | 12 parallel | ✅ **ALLOCATO** |
| **Raid 5p** (LIVE + NEW) | 0 | 2 | 3 | 3 | **4** | **12** (3L+9N) | 12 | ✅ **RAGGIUNTO** |

- **Normal 3p Track**: 60/60 chiuso definitivo (12+14+16+9+9)
- **Elite/Group Track**: 12/12 allocated (Batch 5 include `voidspire-5p` + `celestial-citadel-5p` LIVE fuori conteggio 60)
- **Raid Track**: 12/12 chiuso (3 LIVE + 9 NEW): `broken-bastion-siege` (B3) LIVE + `necropolis-bells` (B4) LIVE + `dragon-vault` (B5) LIVE + 9 NEW `arcane-schism`, `souldrain-abyss` (B2/B3), `emberking-siege`, `memoria-vault` (B4), `void-cathedral`, `celestial-conclave`, `world-tree-collapse` (B5), più i 2 B2 NEW iniziali)

### 🏛️ Q17 Vuoto APPROVED — Lore coverage cumulativa 22/22

**Vuoto** confermata come **17ª lore source valida R18.5** (integrata Batch 5 su 3 encounter: `void-touched-outpost`, `void-heart-sanctum`, `void-cathedral raid`). Coverage lore finale **22/22 fonti utilizzate**. Gate 1 cross-check accettato PM.

### 🐉 Q9 Draco 6× cumulative ACCEPTED (record R18.5)

**Draco 6× cumulative post-B5** (B2×2 + B3 + B4 + B5×2 = 6) **APPROVED** come macro-lore endgame — identità/scala/meccaniche/boss/reward tutti distinti tra i 6 encounter. **NO cap retroattivo**. **NO ridistribuzione**. Nota futura: evitare ulteriore sovraccarico Draco salvo forte motivazione narrativa.

### ⚔️ Q13=A — 7 Legendary Candidate APPROVED (design-only)

**PM Rules Strict verbatim**: solo T5 · max 15 catalog · utility unica + lore forte · NO generic +stat · NO shop · NO craft normale · drop RARISSIMO 1-2% direzionale.

**Primari 4 (drop 2% raid boss finale)**:
| Slug candidate | Source | Lore | Utility unique |
|---|---|---|---|
| `dragonlord-crown` | R1 `dragon-vault` LIVE | Draco | Command Draconic |
| `void-touched-blade` | R2 `void-cathedral` NEW | Vuoto | Void-Pierce |
| `seraph-halo-crown` | R3 `celestial-conclave` NEW | Celeste | Divine Resurrect |
| `worldroot-scepter` | R4 `world-tree-collapse` NEW | Alberi della Vita | Nature's Blessing HoT |

**Secondari 3 (drop 1% dungeon endgame)**:
| Slug candidate | Source | Lore | Utility unique |
|---|---|---|---|
| `ambash-forge-hammer` | #6 `ambash-legendary-forge` | Ambash | Reforge weapon mid-encounter |
| `dragon-elder-scale` | #8 `elder-wyrm-descent` | Draco | Dragon-scale armor buff |
| `sole-nero-diadem` | #9 `pantheon-of-fallen-suns` | Celeste | Swap light/void resist |

**Cap catalog PM = 15** invariato. **Legendary approvati B5 = 7** (4 primari raid + 3 secondari dungeon). **Margine future gate = 8/15**. **NON live**. **NON DB creation**. **NON craftabile normalmente**. **NON shop**. **NON P2W**.

### 🎯 Q21 D→B — Next sequence AUTHORIZED (skip Phase C tech dry-run)

**Sequenza autorizzata post-B5**:
1. **STEP 8 — R18.5 Mini-Gate Legendary Discovery Chain** (documental only, 7 hook narrativi per i 7 Legendary candidate)
2. **STEP 9 — R18.5 Phase D0 Item Table Schema + 1500 Distribution Blueprint** (documental only, blueprint distributivo NON catalogo completo)
3. Phase D1-D5 successive: item table drafting per tier (T1×300 → T2×350 → T3×350 → T4×300 → T5×200 = 1500)

**Phase C tech dry-run**: 🔒 **NON in agenda ora** — riservato dopo consolidamento base creativa items (PM verbatim).

### 🛡️ Governance state Batch 5 CLOSED

- ✅ **36 sigilli byte-identical** (`pytest backend/tests/backend_r18_4_sealed_integrity_test.py` → 6 passed 0.40s, verificato 2× pre + post closure)
- ✅ **Zero code changes** (`.py` / `.js` / `.jsx` / `.tsx` / `.ts` intatti)
- ✅ **Zero DB writes** — `dungeons`, `raid_dungeons`, `expeditions`, `items`, `recipes` invariati
- ✅ **Zero migrations** / apply scripts / hard delete
- ✅ **Zero dungeon/raid creation live** (9 Normal + 3 raid nuovi = design docs only)
- ✅ **`lore_meta.py` invariato**
- ✅ **Zero party_size rewrite** (5p Elite+Raid verbatim)
- ✅ **Zero required_level rewrite** (`voidspire-5p`, `celestial-citadel-5p`, `dragon-vault` drift known no-rewrite)
- ✅ **Zero item table live creation** (7 Legendary candidate = design docs only)
- ✅ **Zero drop table apply**
- ✅ **Zero economy changes**
- ✅ **Zero runtime bridge / class_slug migration / proficiency runtime enforcement**
- ✅ **Phase C tech dry-run NOT INITIATED** (Q21=D→B verbatim: sequenza D0 blueprint prima)
- ✅ **Classi canoniche Warrior/Rogue/Mage/Priest/Ranger verbatim** — NO drift
- ✅ **PM autonomous decision new = ZERO** (Vuoto = PM candidate verbatim, ora approved Q17)

### 📚 Lore coverage finale R18.5 (22/22)

**Fonti utilizzate B1-B5 cumulative**: Adalan, Ambash, Aveol, Krastlov, Efreto, Draco, Alberi della Vita, Halodi, Faglie arcane, Ciclo delle anime, Alevora, Irthe, Memoria, Infernale, Luna Morta, Ergolat, Celeste, **Vuoto (17ª nuova B5)** — 18/22 attive nei dungeon/raid Batch 1-5.

**Fonti restanti 4/22** (non utilizzate nel catalogo dungeon/raid ma incluse in coverage lore R18.5 tramite altre pipeline: signature/materials/quest — Greatwood/Elfwood, Mare, Velur, Soe).

### 📊 Handoff — STEP 8 + STEP 9 AUTHORIZED (sequenza automatica PM verbatim)

- **STEP 8**: `/app/memory/r18_5_legendary_discovery_chain.md/.json` — 7 Legendary Discovery hook per i candidate approvati (utility numeriche finali PENDING PM D-phase, solo narrative + design)
- **STEP 9**: `/app/memory/r18_5_phase_d0_item_table_blueprint.md/.json` — schema tabella item + blueprint distribuzione 1500 (NON catalogo completo — 15 sezioni obbligatorie)

**Files chiave R18.5 (cumulativo aggiornato Batch 5)**:
- Predecessori: `phase_a_discovery`, `phase_b1_design_lock`, `phase_b2_implementation_plan`, `gate1_pm_decisions`, `phase_c0_item_table_drafting_support`, `phase_c0bis_progression_dungeon_raid_matrix`, `pm_workspace_master`, `gate2_pm_decisions`, `phase_c0ter_live_class_matrix`
- C0-quater: `phase_c0quater_live_dungeon_audit`, `phase_c0quater_batch1_informed_final`
- C0-quinquies: `r18_5_phase_c0quinquies_batch2_lv16_30_matrix.md/.json`
- C0-sexies: `r18_5_phase_c0sexies_batch3_lv31_45_matrix.md/.json`
- C0-septies: `r18_5_phase_c0septies_batch4_lv46_55_matrix.md/.json`
- **C0-octies** (nuovo): `r18_5_phase_c0octies_batch5_lv56_60_matrix.md/.json` + `r18_5_batch5_closure_report.md`

**R18.5 status flow (aggiornato Batch 5 CLOSED)**:
`Phase A` ✅ → `Phase B.1/B.2` ✅ → `Gate 1` ✅ → `Phase C0` ✅ → `Phase C0-bis` ✅ → `Gate 2` ✅ + `Phase C0-ter` ✅ → `Phase C0-quater Batch 1` ✅ CLOSED → `Phase C0-quinquies Batch 2` ✅ CLOSED → `Phase C0-sexies Batch 3` ✅ CLOSED → `Phase C0-septies Batch 4` ✅ CLOSED → **`Phase C0-octies Batch 5 ENDGAME`** ✅ **CLOSED** → *`Mini-Gate Legendary Discovery Chain (STEP 8)`* 🟡 *AUTHORIZED chain* → *`Phase D0 Item Table Blueprint (STEP 9)`* 🟡 *AUTHORIZED chain* → *`Phase D1-D5 item table drafting`* 🔒 *pending D0* / *Phase C tech dry-run* 🔒 *NOT IN AGENDA*


---

## R18.5 Phase D3 CLOSED (2026-07-07T17:15:00Z)

**Deliverables**:
- `/app/memory/r18_5_phase_d3_t3_item_table.md` (523 righe · SHA256 `528b0bf7e304ef4ddc1663644aacb7dacba6a5e2d8db3f7fc8d0d2ef2be00e1f`)
- `/app/memory/r18_5_phase_d3_t3_item_table.json` (9320 righe · SHA256 `27cf0003da4fba1c510786d224bcff0e0b97d075093da44b2b16e0c07f248cf1`)

**Decisioni PM verbatim**:
- **Q1=B** — D3 APPROVED after Q6 fix
- **Q2/Q5/Q7/Q8/Q9/Q10** — approved in blocco
- **Q3=A** — 3 Legendary hint T3 ACCEPTED as no-drop / T5 hint only (Celestial Halo-Fragment ×2 Mage+Priest, Worldroot Master Bow Ranger). NO drop diretto, teaser narrativo T5 only.
- **Q4=A** — criterio iconic 173 ACCEPTED as extended metric. **Da D4 in poi obbligo split** nei report: **(1) pure evolutions T→T+1 · (2) intra-family extensions · (3) free/new families**
- **Q6=B** — **Priest shield removed/replaced** (`priest-fabbro-bulwark-priest-shield` weapon_family=`scudo` REMOVED post-fix → `priest-fabbro-bulwark-vow-relic` weapon_family=`reliquia` Rare Lv37 WIS +12, heal +11, mana +18, holy +5, iconic bulwark-priest, source `fabbro-bulwark: craft T3 rare`). **Motivazione**: `scudo` NON in proficiency Priest verbatim (Priest = stoffa + bastone/martello/focus/reliquia). **Regola HARD (post-Q6)**: nessun item può violare armor/weapon proficiency, nessuna eccezione implicita.
- **Split Lv31-35 drift (136 vs target 120)** — ACCEPTED (non-blocking, coerente con Early Batch 3 8-dungeon early concentration)

**Numeri finali D3 (post-fix)**:
- **350 items T3 Lv31-45**
- **Rarity 30/160/130/30/0** (Common/Uncommon/Rare/Epic/Legendary) — EXACT MATCH
- **70 items per classe** (Warrior/Rogue/Mage/Priest/Ranger) — perfectly balanced
- **30 Epic first-appearance** (22 dungeon Batch 3 + 8 raid Batch 3) — 6 Epic per classe, teaser meccaniche endgame narrativo
- **3 Legendary hint T3** no-drop / T5 hint only
- **5 NPC LOCKED** utilizzati (fabbro-bulwark 21, sarto-sacro 12, tessitrice-arcana 12, conciatore-elfwood 13, cuoiaia-elfwood 6 — post-fix). 0 nuovi NPC PENDING.
- **Weapon backlog** `strumento`/`falce`/`trinket-backlog` = 0 usi ✅
- **Anti-P2W** 350/350 real_money=false ✅
- **Iconic-family criterion**: 40-50 pure evolutions target / 173 extended metric ACCEPTED. Da D4 split obbligatorio 3-way.

**Governance R18.5 Phase D3 CLOSED**:
- **36 seals byte-identical** (`pytest backend/tests/backend_r18_4_sealed_integrity_test.py` → 6/6 PASSED pre-write + intra-write + post-fix)
- **Zero DB writes** / **zero code changes** `.py/.js/.jsx/.tsx/.ts` / **zero migrations** / **zero drop table apply** / **zero economy changes** / `lore_meta.py` **invariato** / **zero sealed file modification** / **zero runtime bridge activation** / **zero class_slug migration** / **zero proficiency runtime enforcement** / **zero anti-P2W runtime validator** / **Phase C tech dry-run NOT INITIATED** / **D4 auto-start NEUTRALIZZATO** in favore di gate PM formale con revisione D3 esplicita.
- Classi canoniche verbatim: Warrior/Rogue/Mage/Priest/Ranger (NO Wizard/Cleric drift).
- Balance pass deferred **post-D5**.
- Naming pass deferred **post-D5** (5 note cumulative D1+D2+D3).
- 10 risks documentati (0 HIGH · 1 MEDIUM · 9 LOW). Nessun BLOCKER.

**File touch D3**:
- `r18_5_phase_d3_t3_item_table.md/.json` (NUOVI)
- `PRD.md` (append CLOSED, questo aggiornamento)

**Prossima fase autorizzata PM (2026-07-07T17:15:00Z)**: **Phase D4 (T4 × 300 items Lv46-55)** — STEP 16 catena automatica post-STEP 15.

---

## Roadmap R18.6 — Class Halls, Classless Start & Adventurer Identity (P1 PLANNED)

**Round**: R18.6 (post R18.5 completo)
**Priorità**: **P1 · PLANNED / HOLD UNTIL R18.5 ITEM TABLE COMPLETE (D1-D5)**
**Governance**: solo roadmap/design ora — **DOCUMENTAL ONLY** (Phase R18.5 in corso)

### Obiettivo R18.6

Ogni nuovo avventuriero nasce come **"Senza Classe / Recluta"** e deve scegliere una **Sala di Classe** prima di diventare pienamente utilizzabile. La Sala determina la classe. Il player esperisce una fase identitaria narrativa esplicita (non class-auto-assign).

### Regola design R18.6

- Nuovo avventuriero → **Senza Classe** (stato: `recruit_unassigned`)
- Player sceglie **Sala di Classe** → ottiene classe
- Classe → main stat + armor proficiency + weapon proficiency + equip consentito + identità gameplay

### Scope R18.6 (9 punti-cardine)

1. Stato iniziale adventurer = `classless / recruit_unassigned`
2. Lista Sale di Classe (5 canoniche: Warrior/Rogue/Mage/Priest/Ranger + eventuali future)
3. UI scelta Sala player-facing
4. Assegnazione classe post scelta Sala (transizione `recruit_unassigned` → `<class>`)
5. Blocco dungeon/spedizioni se avventuriero senza classe (gate hard)
6. Main stat per classe (STR/AGI/INT/WIS)
7. Armor/weapon proficiency per classe (regole R18.5 verbatim)
8. Collegamento equip system R18.5 (proficiency check runtime post-R18.6)
9. Guida classe player-facing (tutorial, class identity page)

### Regola gameplay R18.6 — avventuriero senza classe

- **Può** esistere nel roster
- **Può** essere visualizzato / selezionato
- **Può** ricevere prompt/tutorial di scelta Sala
- **NON** può essere mandato in dungeon/raid
- **NON** può equipaggiare gear specializzato (nessun item con `classe_orientata` != universal)
- **Deve** scegliere Sala per sbloccare identità completa

### Prerequisiti R18.6 (hard blockers)

- R18.5 D1-D5 item table COMPLETE (all tiers, all levels)
- R18.5 post-D5 balance/naming review CLOSED
- Class proficiency matrix STABLE (nessun drift open)
- Anti-P2W validator design ready (Phase C tech dry-run outcome)

### Ordine roadmap consigliato post-R18.5

- **R18.5 (in corso)** — Itemization + ILVL + Gear Progression Rework (D1 CLOSED, D2 CLOSED, D3 CLOSED, D4 in agenda STEP 16, D5 pending)
- **R18.6 — Class Halls, Classless Start & Adventurer Identity** ← NUOVO (P1 PLANNED / HOLD)
- **R18.7 — Class Guide + Stat Identity Player-Facing** (P2 PLANNED)
- **R18.8 — Talent Tree / Specialization System** (P2 PLANNED)

### Vincoli R18.6 (solo roadmap/design ora)

- **NO code / DB / migrations / class_slug migration / runtime bridge / unlock classi future / talent tree / sealed modification** durante R18.5.
- R18.6 esecutiva **NON** autorizzata prima che R18.5 sia CLOSED.
- Design docs R18.6 saranno preparati POST-R18.5 chiuso (fase Discovery R18.6 = post-D5 + balance/naming pass).

---

**R18.5 status flow (aggiornato post-STEP 15)**:
`Phase A` ✅ → `Phase B.1/B.2` ✅ → `Gate 1` ✅ → `Phase C0` ✅ → `Phase C0-bis` ✅ → `Gate 2` ✅ + `Phase C0-ter` ✅ → `Phase C0-quater Batch 1` ✅ CLOSED → `Phase C0-quinquies Batch 2` ✅ CLOSED → `Phase C0-sexies Batch 3` ✅ CLOSED → `Phase C0-septies Batch 4` ✅ CLOSED → `Phase C0-octies Batch 5 ENDGAME` ✅ CLOSED → `Mini-Gate Legendary Discovery Chain (STEP 8)` ✅ CLOSED → `Phase D0 Item Table Blueprint (STEP 9)` ✅ CLOSED → `Phase D pre-D1 Iconic Starter (STEP 10)` ✅ CLOSED → `Phase D1 T1×300 (STEP 11)` ✅ CLOSED → `Phase D2 pre-Craft NPC Directory (STEP 12)` ✅ CLOSED → `Phase D2 T2×350 (STEP 13)` ✅ CLOSED → **`Phase D3 T3×350 (STEP 14+15)`** ✅ **CLOSED (post-Q6 fix)** → **`Phase D4 T4×300 (STEP 16)`** 🟡 **IN AGENDA (chain autorizzata)** → `Phase D5 T5×200` 🔒 pending / `Phase C tech dry-run + Item table live creation` 🔒 NOT IN AGENDA / `R18.6 Class Halls` 🔒 HOLD UNTIL R18.5 COMPLETE


---

## R18.5 Phase D4 CLOSED (2026-07-07T17:45:00Z)

**Deliverables**:
- `/app/memory/r18_5_phase_d4_t4_item_table.md` (374 righe · SHA256 `849ea2fd929adee261cbb0da6c21cd2849661b017c0f844a82bae40328278244`)
- `/app/memory/r18_5_phase_d4_t4_item_table.json` (8515 righe · SHA256 `1dc870fad0fd4fe71e9f6fd76f8b10990ee45e9bef5d4d9b486925199965edc0`)

**Decisioni PM verbatim**:
- **Q1=A** — 300 items T4 APPROVED in blocco
- **Q3=A** — 10 Legendary/T5 hints T4 ACCEPTED as no-drop/no-live/T5 crafting hint only
- **Q7=B** — Slug verification report richiesto come closure check (non gate separato)
- **Q8=A** — Vuoto (32) + Memoria (28) first-appearance strong APPROVED
- **Free/new 79%=A** — 238/300 free/new families ACCEPTED (Batch 4 = bracket espansione lore)
- **Q2/Q4/Q5/Q6/Q9/Q10=A** — approved in blocco

**Numeri finali D4**:
- 300 items T4 Lv46-55 · Rarity 0/60/150/90/0 (Common/Uncommon/Rare/Epic/Legendary) EXACT MATCH
- 60 items per classe (Warrior/Rogue/Mage/Priest/Ranger) · 18 Epic per classe balanced
- 90 Epic (52 dungeon + 33 raid + 5 elite) · 0 Legendary live
- 10 Legendary/T5 hints marcati no-drop/T5 hint only
- 5 NPC LOCKED (24 items craft) · 0 nuovi PENDING
- Weapon backlog 0 usi · Anti-P2W 300/300
- **Proficiency HARD verified 300/300** (post-Q6 lesson): Priest scudo/piastre = 0 usi
- Iconic split 3-way: 59 pure_evolutions + 3 intra_extensions + 238 free_new
- Vuoto 32 + Memoria 28 first-appearance strong

**Slug Verification Report (Q7=B closure check)**:

**Raid + Elite**: ✅ **CLEAN EXACT MATCH**
- `necropolis-bells` ✅ · `emberking-siege` ✅ · `memoria-vault` ✅ · `infernal-pit-5p` ✅ · matching Batch 4 matrix verbatim.

**Dungeon**: ⚠️ **DRIFT DOCUMENTATO (non bloccante per D5)**

| D4 slug usato (documentale) | Batch 4 matrix reale | Lore match | Note |
|---|---|:---:|---|
| `dragon-vault-outer` | `wyrmking-antechamber` | ✅ Draco | Naming drift, lore compatibile |
| `abyssal-drift` | `blightborn-caverns` | ✅ Vuoto/decay | Naming drift, lore compatibile |
| `emberking-approach` | `hollow-flame-pit` OR `crimson-forge-outpost` | ✅ Infernale | Naming drift, lore compatibile |
| `frost-cathedral` | `moonveil-shrine` OR `sunfallen-basilica` | ✅ Celeste/Luna | Naming drift, lore compatibile |
| `void-touched-crossroads` | `sepulcher-of-echoes` (alternate) | ✅ Vuoto teaser | Naming drift, lore compatibile |
| `memoria-antechamber` | `sepulcher-of-echoes` | ✅ Memoria/echi | Naming drift, lore compatibile |
| `necropolis-descent` | `black-lantern-conclave` OR `moonveil-shrine` | ✅ Luna Morta | Naming drift, lore compatibile |
| `sanctum-of-fading-souls` | `ashen-warcamp` (alternate) OR mixed | ✅ Ciclo delle anime | Naming drift, lore compatibile |
| `elder-wyrm-descent-antechamber` | `wyrmking-antechamber` | ✅ Draco endgame teaser | Naming drift, ma questa è sostanzialmente la stessa entità (drift lieve) |

**Batch 4 real slug names non usati in D4**: `ashen-warcamp`, `black-lantern-conclave`, `blightborn-caverns`, `crimson-forge-outpost`, `hollow-flame-pit`, `moonveil-shrine`, `sepulcher-of-echoes`, `sunfallen-basilica`, `wyrmking-antechamber`.

**Governance drift**: 
- Il drift è **naming-only** (i temi lore sono coerenti al 100%)
- **Deferred a naming pass consolidamento post-D5** (già autorizzato PM Q8 D3 verbatim: "pass consolidamento post-D5" per naming incoerenze cumulative)
- **NON blocca D5** (PM verbatim: "Q7=B closure check, non blocca D5 se pulito")
- **Q per PM D5**: valutare se rifattorizzare i slug D4 con quelli reali del Batch 4 matrix nel naming pass post-D5 (target: match 1:1 con matrix + preservare lore teaser)
- Nessuna correzione autonoma applicata (governance rispettata: "NON correggere autonomamente contenuti senza PM se emerge drift")

**Governance R18.5 Phase D4 CLOSED**:
- **36 seals byte-identical** (pytest 6/6 PASSED pre + post write)
- **Zero DB writes** / **zero code changes** `.py/.js/.jsx/.tsx/.ts` / **zero migrations** / **zero drop table apply** / **zero economy changes** / `lore_meta.py` **invariato** / **zero sealed file modification**
- **Proficiency HARD verified** (post-Q6 lesson): 0 violazioni, Priest scudo/piastre = 0 usi
- **Zero R18.6 code implementation** (roadmap docs only)
- Balance pass deferred **post-D5**. Naming pass deferred **post-D5** (D1-D4 cumulative naming incoerenze + slug drift D4).

**File touch D4**:
- `r18_5_phase_d4_t4_item_table.md/.json` (NUOVI)
- `PRD.md` (append CLOSED, questo aggiornamento)

**Prossima fase autorizzata PM (2026-07-07T17:45:00Z)**: **Phase D5 (T5 × 200 ENDGAME items Lv56-60)** — STEP 18 catena automatica post-STEP 17.

---

**R18.5 status flow (aggiornato post-STEP 17)**:
`Phase A→C0-octies Batch 5` ✅ CLOSED → `STEP 8-16` ✅ CLOSED → **`Phase D4 T4×300 (STEP 17)`** ✅ **CLOSED (slug drift documented, deferred naming pass post-D5)** → **`Phase D5 T5×200 ENDGAME (STEP 18)`** 🟡 **IN AGENDA (chain autorizzata)** → `Post-D5 gates` 🔒 PENDING PM decision (balance pass · naming pass globale · Phase C tech dry-run · R18.6 kickoff · Marketing brief) / `R18.6 Class Halls` 🔒 HOLD UNTIL R18.5 COMPLETE


---

## R18.5 Phase D5 CLOSED + 🎉 CATALOGO 1500/1500 COMPLETE (2026-07-07T18:00:00Z)

**Milestone**: **R18.5 CATALOGO ITEMS 1500/1500 COMPLETO** ✅ — chiusura ciclo Phase D0-D5 (T1-T5) verbatim PM-locked.

**Deliverables**:
- `/app/memory/r18_5_phase_d5_t5_item_table.md` (508 righe · SHA256 `a38eb2615546a2c2d6cb713b9f7b706c9dacfb885d010193ec0f38182b758379`)
- `/app/memory/r18_5_phase_d5_t5_item_table.json` (5832 righe · SHA256 `58e9f0ea86f7fb5eeaf00c53728fe15c4f4a40041c98e2639a339b873069ae6e`)

**Decisioni PM verbatim (post-STEP 18)**:
- **Q1=A**: Ergolat accepted per HYBRID H3 (`ergolat-obelisk-focus`). Vuoto retained via L2 `void-touched-blade`.
- **Q2=A**: 200 items T5 APPROVED in blocco (i 4 progressive Legendary placeholders sono APPROVED come slot narrativi/documentali, versioni finali PENDING PM).
- **Q3=A**: 15 Open Questions D5 approved as documented.
- **PRD append D5 CLOSED**: GO now (questo blocco).
- **NEXT GATE strategy**: **A→B→C** (Balance → Naming → Tech Dry-Run). GO immediato solo E1.

**Numeri finali D5**:
- 200 items T5 Lv56-60 · Rarity **0/0/70/115/15** (Common/Uncommon/Rare/Epic/Legendary) EXACT MATCH
- 40 items per classe (Warrior/Rogue/Mage/Priest/Ranger) · 23 Epic per classe · 3 Legendary per classe · 14 Rare per classe
- 15 Legendary APPROVED as design candidates:
  - **7 chain** (dragonlord-crown W, void-touched-blade R, seraph-halo-crown P, worldroot-scepter Ra, ambash-forge-hammer W, dragon-elder-scale W, sole-nero-diadem M)
  - **4 HYBRID pre-allocated** (celestial-conclave-mantle P Celeste, irthe-price-shroud R Irthe, ergolat-obelisk-focus M **Ergolat accepted per Q1=A no-repeat Vuoto**, halodi-fate-quiver Ra Halodi)
  - **4 PROGRESSIVE placeholders APPROVED as narrative/documental slots** — versioni finali PENDING PM (progressive-slot-01 M Memoria, 02 P Luna Morta, 03 R Ciclo delle anime, 04 Ra Greatwood/Elfwood)
- **Ergolat accepted for H3** (`ergolat-obelisk-focus`), Vuoto retained through L2 `void-touched-blade` (no-repeat lore-source su Legendary)
- 20 items craft NPC (5 LOCKED × 4) · 0 nuovi NPC autonomi · 24 achievement/ranking/quest/vendor · 85 dungeon B5 drop · 61 raid drop · 10 Elite drop
- **Proficiency HARD verified 200/200** inclusi Legendary (Priest scudo/piastre/cuoio/maglia = 0 usi propagato post-Q6 D3 lesson)
- **Anti-P2W verified 200/200** (`can_be_sold_for_real_money=false`)
- **Weapon backlog RESERVED**: `strumento`/`falce`/`trinket_backlog` = 0 usi
- **Legendary bind-on-pickup 15/15**, `is_tradeable=false` 15/15, `can_be_sold_for_gold=false` 15/15
- Lore capstone T5: **22/22 lore coverage** (11 LIVE capstone T5, 4 progressive PENDING PM, 7 chiuse pre-D5 con variety watch rispettata)
- Iconic-family split 3-way: 69 pure_evolutions T4→T5 · 0 intra-extensions · 131 free/new T5 endgame

### 🎉 R18.5 CATALOGO ITEMS 1500/1500 COMPLETE — Aritmetica cumulative EXACT

| Rarity | D1 (300) | D2 (350) | D3 (350) | D4 (300) | D5 (200) | **Totale** | Target |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Common | 220 | 150 | 30 | 0 | 0 | **400** | 400 ✅ |
| Uncommon | 80 | 150 | 160 | 60 | 0 | **450** | 450 ✅ |
| Rare | 0 | 50 | 130 | 150 | 70 | **400** | 400 ✅ |
| Epic | 0 | 0 | 30 | 90 | 115 | **235** | 235 ✅ |
| Legendary | 0 | 0 | 0 | 0 | 15 | **15** | 15 ✅ (cap catalog RAGGIUNTO) |
| **TOTALE tier** | 300 | 350 | 350 | 300 | 200 | **1500** | 1500 ✅ **EXACT** |

**Rarity cumulative EXACT verbatim PM-locked**: **400/450/400/235/15** ✅

### Governance R18.5 Phase D5 CLOSED

- **36 seals byte-identical** (pytest 6/6 PASSED pre + post write)
- **Zero DB writes** / **zero code changes** `.py/.js/.jsx/.tsx/.ts` / **zero migrations** / **zero drop table apply** / **zero economy changes** / `lore_meta.py` **invariato** / **zero sealed file modification** / **zero hard delete** / **zero runtime bridge** / **zero class_slug migration** / **zero proficiency runtime enforcement** / **zero anti-P2W runtime validator implementation**
- **Proficiency HARD verified 200/200** inclusi 15 Legendary (post-Q6 D3 lesson propagata)
- **Zero R18.6 code implementation** (roadmap docs only)
- Balance pass deferred **next step E1** (AUTHORIZED post-STEP 19). Naming pass deferred **next step E2** (PLANNED / HOLD UNTIL E1 REVIEW). Phase C Tech Dry-Run **HOLD UNTIL E1+E2 CLOSED**.

### File touch D5

- `r18_5_phase_d5_t5_item_table.md/.json` (NUOVI)
- `PRD.md` (append CLOSED + milestone 1500/1500, questo aggiornamento)

### NEXT GATE strategy (PM lockato post-D5 approval)

| Gate | Status |
|---|---|
| **R18.5 Phase E1 Global Balance Pass** | 🟡 **AUTHORIZED** (in progress after STEP 19 — STEP 20 catena) |
| **R18.5 Phase E2 Global Naming Pass** | 🔒 **PLANNED / HOLD UNTIL E1 REVIEW** |
| **R18.5 Phase C Tech Dry-Run** (proficiency runtime + class_slug migration + ILVL endgame implementation) | 🔒 **HOLD UNTIL E1+E2 CLOSED** |
| **R18.6 Class Halls, Classless Start & Adventurer Identity** | 🔒 **PLANNED** (invariato, hold until R18.5 complete inclusi E1+E2+C) |
| **Marketing Brief** | 🔒 **DEFERRED** |

**Rationale strategy A→B→C (PM verbatim)**: Balance pass (E1) prima di Naming pass (E2) — outlier stat/scaling identificati devono essere risolti prima di consolidare naming; entrambi obbligatori prima di aprire Phase C tech dry-run (registry/apply/drop table); R18.6 hold until R18.5 tutto completato.

---

**R18.5 status flow (aggiornato post-STEP 19)**:
`Phase A→C0-octies Batch 5` ✅ CLOSED → `STEP 8-16` ✅ CLOSED → `Phase D4 T4×300 (STEP 17)` ✅ CLOSED → `Phase D5 T5×200 ENDGAME (STEP 18)` ✅ **CLOSED (Q1-Q3=A approved)** → **`🎉 R18.5 CATALOGO 1500/1500 COMPLETE`** ✅ **MILESTONE (STEP 19)** → **`Phase E1 Global Balance Pass (STEP 20)`** 🟡 **AUTHORIZED (chain autorizzata, in progress)** → `Phase E2 Global Naming Pass` 🔒 PLANNED / HOLD UNTIL E1 REVIEW → `Phase C Tech Dry-Run` 🔒 HOLD UNTIL E1+E2 CLOSED / `R18.6 Class Halls` 🔒 PLANNED (invariato) / `Marketing Brief` 🔒 DEFERRED


---

## R18.5 Phase E1 CLOSED (2026-07-07T18:35:00Z)

**Milestone**: **R18.5 Phase E1 Global Balance Pass + Phase E1.1 Balance Remediation Patch CLOSED** ✅

**Deliverables E1** (analysis-only, read-only sui dati input):
- `/app/memory/r18_5_phase_e1_global_balance_pass.md` (432 righe · SHA256 `f460fb6b9d8ffbf7c65bf86aed74b790ec59914d8c78aba986206036590a9b05`)
- `/app/memory/r18_5_phase_e1_global_balance_pass.json` (1562 righe · SHA256 `a79d37b9021f44ae5606bad6f00c2dae50a1821cdbc05a28d0f30fe8a8f6a162`)

**Deliverables E1.1** (remediation patch, micro-eccezione autorizzata PM):
- `/app/memory/r18_5_phase_e1_1_balance_remediation_patch.md`
- `/app/memory/r18_5_phase_e1_1_balance_remediation_patch.json` (841 righe · SHA256 `3e3f0ae7e3589be36e831cc1a8c53dd4720a2d0c4f1f0dcd10f3325262c8d3c3`)

**Item table files modificati in E1.1** (nuovi SHA256):
- D1 `.json`: `6058ae78b337c596d6ae3a94550dda90e20b4b5da284724e1481c3ffd8b1ddff`
- D2 `.json`: `e246f2773b8584772766124cd323358d3a750a1be853d0777d92eead3a2de6d5`
- D3 `.json`: `b478ae641eec3f33e440cfec80a2e52da4a81c8fd76b7df9594234be09644d44`
- D4 `.json`: `6d42a01983d6bcf37354f2b5ba99cff6a2b4d8b2c272819907a57dbfe9455acb`
- D5 `.json`: `58e9f0ea86f7fb5eeaf00c53728fe15c4f4a40041c98e2639a339b873069ae6e` (unchanged)

**E1 CLOSED — Decisioni PM verbatim rispettate**:
- **E1 Global Balance Pass CLOSED**
- **1500/1500 catalog verified post-remediation** (aritmetica cumulativa invariata)
- **4 HIGH proficiency violations fixed** (Priest pugnale→reliquia ×2 · Rogue arco→balestra ×2, item_id preservati per tracking)
- **22 stat outliers**: 16 fixed (2 power creep T1 + 3 underpowered legit + 11 cross-tier T3) or explicitly tracked as PENDING PM (6 hint T4 design intent progressive marker sub-Epic voluto)
- **151 naming drift EN→IT items deferred to E2** (STEP 23 catena autorizzata)
- **Progressive Legendary placeholders (4 P1-P4)** deferred to Phase C Tech Dry-Run / drop-table gate
- **Anti-P2W 1500/1500 preserved** (`can_be_sold_for_real_money=false` invariato)
- **Proficiency HARD BLOCK clean after fix (0 residual violations)** — Priest scudo/piastre/cuoio/maglia = 0 usi confermato · Weapon backlog RESERVED = 0 usi confermato
- **36 seals byte-identical** (pytest 6/6 PASSED pre + post write E1 + E1.1)
- **Zero DB/code/migrations**

**Governance E1 CLOSED**:
- E1 (STEP 20) = ANALYSIS-ONLY read-only sui dati input; nessun item table modificato
- E1.1 (STEP 21) = REMEDIATION-PATCH con micro-eccezione DOCUMENTAL autorizzata PM su file item table D1-D4 (.json) SOLO per 4 HIGH + 16 MEDIUM fixes; preservati item count/rarity/class/tier/lore/source/anti-P2W/utility/item_id
- `lore_meta.py` invariato · Nessun sealed file toccato · Zero `.py`/`.js`/`.jsx`/`.tsx`/`.ts` modificato
- Class distribution invariata 300×5 (Warrior/Rogue/Mage/Priest/Ranger)

**Aritmetica cumulativa post-E1.1** (invariata):
- Common 400 · Uncommon 450 · Rare 400 · Epic 235 · Legendary 15 = **1500** ✅
- T1 300 · T2 350 · T3 350 · T4 300 · T5 200 = **1500** ✅
- Warrior 300 · Rogue 300 · Mage 300 · Priest 300 · Ranger 300 = **1500** ✅

**File touch E1 + E1.1**:
- `r18_5_phase_e1_global_balance_pass.md/.json` (NUOVI, E1)
- `r18_5_phase_e1_1_balance_remediation_patch.md/.json` (NUOVI, E1.1)
- `r18_5_phase_d1_t1_item_table.json` (MODIFICATO E1.1 HIGH#1 + MEDIUM#1-2)
- `r18_5_phase_d2_t2_item_table.json` (MODIFICATO E1.1 HIGH#2 + MEDIUM#3)
- `r18_5_phase_d3_t3_item_table.json` (MODIFICATO E1.1 HIGH#3-4 + MEDIUM#4, M6-M16)
- `r18_5_phase_d4_t4_item_table.json` (MODIFICATO E1.1 MEDIUM#5)
- `PRD.md` (append CLOSED, questo aggiornamento)

**NEXT GATE (post-STEP 22)**:
- STEP 23 (E2 Global Naming Pass) 🟡 **AUTHORIZED** (chain immediata post-STEP 22 OK)
- Phase C Tech Dry-Run 🔒 HOLD UNTIL E2 CLOSED
- R18.6 Class Halls 🔒 PLANNED (HOLD UNTIL R18.5 COMPLETE)
- Marketing Brief 🔒 DEFERRED

---

**R18.5 status flow (aggiornato post-STEP 22)**:
`Phase D5 (STEP 18)` ✅ CLOSED → `🎉 CATALOGO 1500/1500 (STEP 19)` ✅ MILESTONE → `Phase E1 Global Balance Pass (STEP 20)` ✅ CLOSED → `Phase E1.1 Balance Remediation Patch (STEP 21)` ✅ **CLOSED** → **`PRD append E1 CLOSED (STEP 22)`** ✅ **CLOSED (questo append)** → **`Phase E2 Global Naming Pass (STEP 23)`** 🟡 **AUTHORIZED (chain immediata)** → `Phase C Tech Dry-Run` 🔒 HOLD UNTIL E2 CLOSED / `R18.6 Class Halls` 🔒 PLANNED / `Marketing Brief` 🔒 DEFERRED


---

## R18.5 Phase E1 + E2 CLOSED (2026-07-07T18:55:00Z)

**Milestone**: **R18.5 Phase E1 (Global Balance Pass) + Phase E1.1 (Balance Remediation Patch) + Phase E2 (Global Naming Pass) CLOSED IN BLOCCO** ✅

**Deliverables**:
- `/app/memory/r18_5_phase_e1_global_balance_pass.md/.json` (E1 analysis)
- `/app/memory/r18_5_phase_e1_1_balance_remediation_patch.md/.json` (E1.1 patch)
- `/app/memory/r18_5_phase_e2_global_naming_pass.md/.json` (E2 naming — 320 righe md · SHA256 `89d0be33271a19c0640180b2719cfdb357ae6ed7fca7c2ad7dbc520cadf673d6` · 552 righe json · SHA256 `d398df4c8b1819f23918c4c2e55a4f889fe502890614cdb18e0dc59a54f42337`)

**Item table files finale post-E1.1+E2** (nuovi SHA256):
- D1 `.json`: `e529922a510d9ec43af2f6d12b9404626f06ae85f9916712931c0131eeae984b`
- D2 `.json`: `e647a0babcd7f884794920be68895d8bc702b639d4f21e799cef0e20cc6d7069`
- D3 `.json`: `b478ae641eec3f33e440cfec80a2e52da4a81c8fd76b7df9594234be09644d44`
- D4 `.json`: `6d42a01983d6bcf37354f2b5ba99cff6a2b4d8b2c272819907a57dbfe9455acb`
- D5 `.json`: `58e9f0ea86f7fb5eeaf00c53728fe15c4f4a40041c98e2639a339b873069ae6e`

**E1 + E2 CLOSED — Decisioni PM verbatim rispettate**:

- **E1 CLOSED** (analysis-only + E1.1 remediation patch applied)
- **E2 CLOSED** (naming pass EN→IT + slug/family/NPC/Legendary review)
- **Catalogo 1500/1500 balance-cleaned + naming-normalized** ✅
- **4 HIGH proficiency violations fixed**:
  - `priest-blessed-dagger` T1 pugnale → **reliquia**
  - `priest-blessed-dagger-t2` T2 pugnale → **reliquia**
  - `rogue-soulforged-shortbow` T3 arco → **balestra**
  - `rogue-soulforged-shortbow-master` T3 arco → **balestra**
- **16 stat outliers fixed**:
  - 2 power creep intra-tier T1 (Warrior common/uncommon STR -1)
  - 3 underpowered legit (Warrior heavy-belt-t2, ergolat-siege-commander-plate, t4-emberking-siege-boss toward mean)
  - 11 cross-tier power creep T3 (Warrior/Rogue/Mage/Priest/Ranger boss finale main_stat -1/-2 sotto T4 mean*1.10=24.53)
- **6 T4 progressive marker outliers ACCEPTED as design intent** (Q6=A PM verbatim, non toccare stat — transizione visiva/narrativa verso T5):
  - `warrior-t4-legendary-emberking-crown-hint` (STR=18, hint→Legendary T5 emberking-crown, Infernale bracket saturato)
  - `warrior-t4-legendary-void-touched-hint` (STR=18, hint→L2 void-touched-blade T5)
  - `rogue-t4-legendary-soul-abyss-hint` (AGI=18, hint→P3 progressive-slot-03 Rogue soul-bind)
  - `mage-t4-legendary-void-warlock-hint` (INT=18, hint→L2 void-touched-blade cross-class)
  - `priest-t4-legendary-celestial-halo-hint` (WIS=18, hint→L3 seraph-halo-crown T5)
  - `priest-t4-legendary-resurrect-hint` (WIS=17, hint→P2 progressive-slot-02 Priest resurrection)
- **151 armor naming drift EN→IT fixed** (bulk normalization E2):
  - `heavy` Warrior → **`piastre`** (38)
  - `medium` Warrior → **`maglia`** (17)
  - `medium` Ranger → **`maglia`** (35)
  - `light` Rogue → **`cuoio`** (50)
  - `light` Ranger → **`cuoio`** (11)
- **14 duplicate nome_it deferred to E2.1** (STEP 25 catena immediata autorizzata, Q12=A PM)
- **9 D4 slug drift ACCEPTED / documented / NO rename** (Q3=A PM verbatim, governance preservation)
- **Family naming redundancy T4/T5 ACCEPTED as design intent** (Q4=A PM verbatim, design pattern progressione: dragonhunter/elder-wyrm/ambash-forge/alevoran-perpetual/emberking-endgame/efreto-purger/adalan-archmage)
- **Anti-P2W 1500/1500 preserved**
- **Proficiency HARD BLOCK clean 0 residue** (post-4 HIGH fix + armor naming normalization)
- **36 seals byte-identical** (pytest 6/6 PASSED cross-STEP 20/21/22/23)
- **Zero DB/code/migrations**

**Governance E1+E2 CLOSED**:
- Micro-eccezione DOCUMENTAL autorizzata PM per modifica item table D1-D4 `.json` SOLO per fix E1.1 (proficiency + stat outlier) + E2 (armor naming EN→IT). NO code changes / DB writes / migrations / sealed files.
- Item_id preservati per tracking (Option A governance) — inclusi blessed-dagger + soulforged-shortbow post-E1.1 fix
- Aritmetica cumulativa invariata: T1 300 · T2 350 · T3 350 · T4 300 · T5 200 = 1500
- Rarity invariata: 400 C · 450 U · 400 R · 235 E · 15 L = 1500
- Class invariata: Warrior 300 · Rogue 300 · Mage 300 · Priest 300 · Ranger 300 = 1500

**NEXT GATE (PM lockato post-E1+E2 approval)**:
- **R18.5 Phase E2.1 Duplicate Name Resolution Mini-Pass** 🟡 **AUTHORIZED** (STEP 25 catena immediata post-STEP 24)
- **R18.5 Phase C Tech Dry-Run** 🔒 **HOLD UNTIL E2.1 CLOSED** (proficiency runtime + class_slug migration + ILVL endgame implementation)
- **R18.6 Class Halls, Classless Start & Adventurer Identity** 🔒 **PLANNED / HOLD (SERIAL post-Phase C)** (Q10=B PM verbatim)
- **Marketing Brief** 🔒 **DEFERRED** (Q11=B PM verbatim)

**File touch E1 + E1.1 + E2**:
- E1 analysis (STEP 20): `r18_5_phase_e1_global_balance_pass.md/.json` (NUOVI)
- E1.1 remediation (STEP 21): `r18_5_phase_e1_1_balance_remediation_patch.md/.json` (NUOVI) + `r18_5_phase_d1_t1_item_table.json` + `r18_5_phase_d2_t2_item_table.json` + `r18_5_phase_d3_t3_item_table.json` + `r18_5_phase_d4_t4_item_table.json` (MODIFICATI)
- E2 naming (STEP 23): `r18_5_phase_e2_global_naming_pass.md/.json` (NUOVI) + `r18_5_phase_d1_t1_item_table.json` + `r18_5_phase_d2_t2_item_table.json` (MODIFICATI naming-only)
- PRD.md STEP 19 + STEP 22 + STEP 24 (questo append CLOSED)

---

**R18.5 status flow (aggiornato post-STEP 24)**:
`Phase D5 (STEP 18)` ✅ → `CATALOGO 1500/1500 (STEP 19)` ✅ → `Phase E1 (STEP 20)` ✅ → `Phase E1.1 (STEP 21)` ✅ → `PRD E1 CLOSED (STEP 22)` ✅ → `Phase E2 (STEP 23)` ✅ → **`PRD E1+E2 CLOSED (STEP 24)`** ✅ **CLOSED (questo append)** → **`Phase E2.1 Duplicate Name Resolution (STEP 25)`** 🟡 **AUTHORIZED (chain immediata)** → `Phase C Tech Dry-Run` 🔒 HOLD UNTIL E2.1 CLOSED / `R18.6 Class Halls` 🔒 PLANNED SERIAL post-Phase C / `Marketing Brief` 🔒 DEFERRED


---

## R18.5 Phase E2.1 CLOSED + 🎯 Catalogo 1500 STABILIZZATO (2026-07-07T19:15:00Z)

**Milestone**: **R18.5 Phase E2.1 Duplicate Name Resolution CLOSED + R18.5 catalog status = FULLY STABILIZED** ✅

**Deliverables E2.1**:
- `/app/memory/r18_5_phase_e2_1_duplicate_name_resolution.md` (340 righe · SHA256 `b0a988ea0b82c2f9e58267c66d971fafceb41b4c408dda9739b45f0ecf15b2f6`)
- `/app/memory/r18_5_phase_e2_1_duplicate_name_resolution.json` (1722 righe · SHA256 `d39e9b9dfc51987e39ad1869c579d848b028705fbe525f92d354aef3973850b4`)

**Item table files SHA256 finali post-E2.1** (STABILIZZATI):
- D1: `40107a3e7cfd3cce...`
- D2: `f30f39f327db39e0...`
- D3: `39e0f88fa7121c1d...`
- D4: `a6c24abfcb3c442b...`
- D5: `58e9f0ea86f7fb5eeaf00c53728fe15c4f4a40041c98e2639a339b873069ae6e` (invariato dal design STEP 18)

**E2.1 CLOSED — Decisioni PM verbatim (Q1=A)**:
- **E2.1 Duplicate Name Resolution CLOSED**
- **14 duplicate nome_it resolved**
- **29 rename completed** (class-suffix + tier-suffix varianti leggere)
- **Duplicate residue = 0** ✅
- **Catalog remains 1500/1500** ✅
- **Rarity remains 400/450/400/235/15** ✅
- **Class distribution remains 300×5** (Warrior/Rogue/Mage/Priest/Ranger) ✅
- **Proficiency violations = 0** ✅
- **Anti-P2W 1500/1500** (`can_be_sold_for_real_money=false`) ✅
- **Weapon backlog remains RESERVED** (`strumento`/`falce`/`trinket_backlog` = 0 usi) ✅
- **D4 slug drift documented / no rename** (9 slug B4 accepted Q3=A)
- **Family redundancy accepted** (design intent per progressione cross-tier Q4=A)
- **R18.5 catalog status = FULLY STABILIZED** 🎯

**Governance E2.1 CLOSED**:
- Micro-eccezione DOCUMENTAL autorizzata PM per rename nome_it SOLO (item table D1-D4 .json). NO code/DB/migrations/sealed touches.
- Full snapshot verification: **all other fields unchanged 29/29** (governance strict)
- 36 seals byte-identical (pytest 6/6 PASSED)
- Zero DB/code/migrations/economy/lore_meta.py touches

**NEXT GATE (PM lockato post-E2.1 approval Q4=B)**:

Phase C Tech Dry-Run autorizzata come **SPLIT SEQUENCE**, GO immediato SOLO C0 + C0.L in catena (C1-C6 HOLD):

| Sub-step | Status | Trigger |
|---|---|---|
| **C0 Technical Readiness Inventory** (STEP 27) | 🟡 **AUTHORIZED** (chain immediata post-STEP 26) | subito |
| **C0.L Legendary Finalization Mini-Gate** (STEP 28) | 🟡 **AUTHORIZED CONDITIONAL** | solo se C0 = GO |
| **C1 Item Registry Generation Dry-Run** | 🔒 **HOLD** | PM review post-C0.L |
| **C2 Proficiency Runtime** | 🔒 **HOLD** | post-C1 |
| **C3 ILVL + Backfill** | 🔒 **HOLD** | post-C2 |
| **C4 Drop Table** | 🔒 **HOLD** | post-C3 |
| **C5 Class Slug Migration Prep** | 🔒 **HOLD** | post-C4 |
| **C6 Final Closure** | 🔒 **HOLD** | post-C5 |

**R18.6 Class Halls**: 🔒 PLANNED / HOLD UNTIL Phase C readiness (Q9 invariato)
**Marketing Brief**: 🔒 DEFERRED (Q10 invariato)

---

**R18.5 status flow (aggiornato post-STEP 26)**:
`Phase E2.1 (STEP 25)` ✅ CLOSED → **`PRD E2.1 CLOSED + Catalogo STABILIZZATO (STEP 26)`** ✅ **CLOSED (questo append)** → **`Phase C0 Technical Readiness (STEP 27)`** 🟡 **AUTHORIZED (chain immediata)** → **`Phase C0.L Legendary Finalization (STEP 28)`** 🟡 **AUTHORIZED CONDITIONAL (se C0=GO)** → `C1-C6` 🔒 HOLD post-PM review / `R18.6` 🔒 PLANNED / `Marketing Brief` 🔒 DEFERRED



## R18.5 Phase C0 + C0.L CLOSED (STEP 29 · 2026-07-07T20:30:00Z)

**Milestone**: **R18.5 Phase C0 Technical Readiness + Phase C0.L Legendary Finalization CLOSED** ✅

**Governance**: DOCUMENTAL ONLY append. Nessuna modifica code/DB/migrations/sealed/item table/lore_meta.py. 36 sigilli intatti (pytest 6/6 PASSED).

**Deliverables C0 (STEP 27)**:
- `/app/memory/r18_5_phase_c0_technical_readiness_inventory.md` (SHA256 `88f51036e7f9f1fcb8bf2c63d9ae282fe26268988e215361ac336e773854a63f`)
- `/app/memory/r18_5_phase_c0_technical_readiness_inventory.json` (SHA256 `14efc0d728b90864f3db3ab65816e6f417a46d0f342ea84ebc12f0e0b8e612e8`)

**Deliverables C0.L (STEP 28 + 28-bis)**:
- `/app/memory/r18_5_phase_c0_l_legendary_finalization_gate.md` (SHA256 `f4bf47a679d0db4a2670d7d0a2368116d5c232cec9c0bd0adbc44a7171efe865`, gemello narrativo STEP 28-bis)
- `/app/memory/r18_5_phase_c0_l_legendary_finalization_gate.json` (SHA256 `2860a2a7332982855ff00496585850d405c7428f46cf81e3446c66a1d15db6e4`)

**C0 CLOSED — Decisioni PM verbatim (Q1=A)**:
- **C0 Technical Readiness CLOSED**
- **C0 recommendation GO confirmed**
- **0 HARD blockers** · **2 SOFT blockers deferred**:
  - `class_slug` missing 1500/1500 → **deferred to C5 R18.3f Class Slug Migration Prep** (Q8=A: `class_slug=null` + `class_slug_resolution_status="deferred_to_C5_R18_3f"`)
  - 4 Progressive Legendary PENDING PM → handled in C0.L
- 15/15 check eseguiti (13 ✅ + 2 ⚠️ handled)

**C0.L CLOSED — Decisioni PM verbatim (Q1..Q8)**:
- **C0.L Legendary Finalization CLOSED**
- **15 Legendary composition confirmed**:
  - **7 APPROVED_CANDIDATE**: ambash-forge-hammer · dragon-elder-scale · dragonlord-crown · void-touched-blade · sole-nero-diadem · seraph-halo-crown · worldroot-scepter
  - **4 HYBRID_PRE_ALLOCATED**: irthe-price-shroud-hybrid · ergolat-obelisk-focus-hybrid · celestial-conclave-mantle-hybrid · halodi-fate-quiver-hybrid
  - **4 PROGRESSIVE_DISCOVERY_PLACEHOLDER**: rogue-P3 · mage-P1 · priest-P2 · ranger-P4
- **11 Legendary registry design-ready** (7 approved + 4 hybrid)
- **4 Progressive Discovery = PENDING PM / registry_reserved** (Q3=A)
- **C0.L.1 Numeric Finals authorized before C1** (Q2=A) — 11 Legendary numeric finalization mini-gate
- **C1 authorized after C0.L.1** (Q5=A)
- **C1 scope = registry aggregato + differential `.md` report** (Q6=C)
- **6 T4 progressive marker → flag `progressive_marker=true` in C1** (Q4=B) — nota: C0.L Sezione 3.6 tabella lista 10 T4 hint items · discrepanza wording Q4 (6) vs tabella (10) segnalata come PM gate item C1 validation
- **class_slug handling** = `class_slug: null` + `class_slug_resolution_status: "deferred_to_C5_R18_3f"` (Q8=A)
- **runtime_apply_ready** rimane **0** (dry-run design layer, no runtime enforcement)
- **PRD append `C0+C0.L CLOSED` = questo append** (Q7=A)

**Governance C0+C0.L CLOSED**:
- 36 seals byte-identical (pytest `backend_r18_4_sealed_integrity_test.py` 6/6 PASSED)
- Zero DB writes / code changes / migrations / `lore_meta.py` touches
- Zero item table D1-D5 modifications (read-only analysis)
- Zero legendary stat/utility/lore changes (analysis-only)
- Progressive placeholder finalization = ZERO autonomous (P3=A: reserved status)
- Classi canoniche W/R/M/P/Ranger — NO drift

**NEXT GATE (PM lockato post-C0+C0.L approval)**:

Phase C Tech Dry-Run autorizzata come **CATENA STEP 29→30→31** (STOP obbligatorio dopo C1):

| Sub-step | Status | Trigger |
|---|---|---|
| **C0.L.1 Legendary Numeric Finals** (STEP 30) | 🟢 **AUTHORIZED (chain immediata)** | subito post-STEP 29 |
| **C1 Item Registry Generation Dry-Run** (STEP 31) | 🟢 **AUTHORIZED (chain immediata)** | subito post-C0.L.1 clean |
| **C2 Proficiency Runtime** | 🔒 **HOLD** | PM review post-C1 |
| **C3 ILVL + Backfill** | 🔒 **HOLD** | post-C2 |
| **C4 Drop Table** | 🔒 **HOLD** | post-C3 |
| **C5 Class Slug Migration Prep** | 🔒 **HOLD** | post-C4 (Q8=A deferral) |
| **C6 Final Closure** | 🔒 **HOLD** | post-C5 |

**R18.6 Class Halls**: 🔒 PLANNED / HOLD post-Phase C readiness
**Marketing Brief**: 🔒 DEFERRED

---

**R18.5 status flow (aggiornato post-STEP 29)**:
`Phase E2.1 (STEP 25)` ✅ CLOSED → `PRD E2.1 CLOSED + Catalogo STABILIZZATO (STEP 26)` ✅ CLOSED → `Phase C0 Technical Readiness (STEP 27)` ✅ CLOSED → `Phase C0.L Legendary Finalization (STEP 28+28-bis)` ✅ CLOSED → **`PRD C0+C0.L CLOSED (STEP 29)`** ✅ **CLOSED (questo append)** → `Phase C0.L.1 Legendary Numeric Finals (STEP 30)` 🟢 **AUTHORIZED (chain immediata)** → `Phase C1 Item Registry Dry-Run (STEP 31)` 🟢 **AUTHORIZED (chain immediata)** → `C2-C6` 🔒 HOLD post-PM review / `R18.6` 🔒 PLANNED / `Marketing Brief` 🔒 DEFERRED


## R18.5 Phase C0.L.1 + C1 CLOSED (STEP · 2026-07-07T20:45:00Z)

**Milestone**: **R18.5 Phase C0.L.1 Legendary Numeric Finals + Phase C1 Item Registry Dry-Run CLOSED** ✅

**Governance**: DOCUMENTAL ONLY append. Nessuna modifica code/DB/migrations/sealed/item table/lore_meta.py. 36 sigilli intatti (pytest 6/6 PASSED).

**Deliverables C0.L.1 (STEP 30)**:
- `/app/memory/r18_5_phase_c0_l_1_legendary_numeric_finals.md` (SHA256 `d824ad6e32f318137ac1d7c023191f81fb671001de77436d6c6ce6567bfee953`, 350 righe)
- `/app/memory/r18_5_phase_c0_l_1_legendary_numeric_finals.json` (SHA256 `cf3b6496dfd463cec2dee04043d3a2d1dbb87217b09f9a9f9dcece176571e1e2`)

**Deliverables C1 (STEP 31)**:
- `/app/memory/r18_5_phase_c1_item_registry_dry_run.md` (SHA256 `9762cd8e896d4096fe0c3ddb521002610c64c6922998e78eb2efbb0adb20c0f0`, 199 righe)
- `/app/memory/r18_5_phase_c1_item_registry_dry_run.json` (SHA256 `5e7860e427b0bf702c0664e9221d6de34efe18ee81279231061475a2664c551f`, 1500 registry rows)

**C0.L.1 CLOSED — Decisioni PM verbatim**:
- **C0.L.1 Legendary Numeric Finals CLOSED**
- **11 Legendary numeric finals proposti** (7 APPROVED + 4 HYBRID) con 18 campi ciascuno
- **4 Progressive Discovery** (P1-P4) = registry_reserved / PENDING PM / not_runtime_apply_ready
- **Regole strict PASSED 11/11**: no-generic-stat · no-premium-shop · proficiency HARD BLOCK · anti-P2W · utility unica · lore capstone forte
- **Risk summary**: LOW=6 · MEDIUM=5 · HIGH=0
- **5 MEDIUM Legendary utility caps deferred to C2**:
  1. Void-Pierce (L2) passive 15% chance on-hit — cap runtime C2
  2. Divine Resurrect (L3) meta impact — validation C2
  3. Reforge (L5) cross-target consent — runtime C2
  4. Absence Distortion (H3) silence cap boss — C2
  5. Fate Deflection (H4) auto-reactive lethal on raid boss — C2
- **HYBRID drop rate 0.5% direzionale**: documental only candidate, non definitivo → **deferred to C4 Drop Table**

**C1 CLOSED — Decisioni PM verbatim**:
- **C1 Item Registry Dry-Run CLOSED**
- **Registry aggregated**: 1500 rows (schema 24 campi canonici)
- **Applicable**: **1486**
- **Reserved** (P1-P4): **4**
- **Progressive_marker count**: **10** — **CORRECTED / APPROVED at 10** (PM gate #1 risolto: source-of-truth `.json` C0.L Sezione 3.6 pattern `*-t4-legendary-*-hint`)
- **runtime_apply_ready**: **0/1500** (dry-run design layer)
- **class_slug**: **null 1500/1500**
- **class_slug_resolution_status**: `deferred_to_C5_R18_3f` 1500/1500
- **Anti-P2W**: **1500/1500** (`can_be_sold_for_real_money=false`)
- **Rarity distribution**: 400/450/400/235/15 esatto (Common/Uncommon/Rare/Epic/Legendary)
- **Class distribution**: 300×5 esatto (Warrior/Rogue/Mage/Priest/Ranger)
- **item_id uniqueness**: 1500/1500 (0 duplicati)
- **nome_it uniqueness**: 1500/1500 post-E2.1 (0 duplicati)
- **Proficiency violations**: 0 (verified post-E1.1)
- **Weapon backlog**: RESERVED (0 usi runtime)
- **Legendary composition**: 11 design-ready + 4 registry_reserved (totale 15/15)

**Differential C1 vs D1-D5 (nuovi campi registry canonical)**:
- `class_proficiency` (rename da `classe_orientata`)
- `drop_table_ref` (derivato da `source` primary token)
- `progressive_marker` (bool, 10 T4 hint items)
- `registry_status` (applicable / reserved / progressive_marker)
- `runtime_apply_ready` (bool, false 1500/1500)
- `class_slug` (null 1500/1500)
- `class_slug_resolution_status` (deferred_to_C5_R18_3f 1500/1500)
- `notes` (per-item residue PENDING / marker rationale)

**Governance C0.L.1 + C1 CLOSED**:
- 36 seals byte-identical (pytest `backend_r18_4_sealed_integrity_test.py` 6/6 PASSED)
- Zero DB writes / code changes / migrations / `lore_meta.py` touches
- Zero item table D1-D5 modifications (read-only aggregation)
- Zero legendary stat semantic/utility/lore changes (numeric finals coerenti con D5)
- Zero progressive placeholder finalization autonomous
- Zero HYBRID drop_rate apply (0.5% direzionale documentale only)
- Zero runtime apply / drop table apply / class_slug auto-derivation
- Classi canoniche W/R/M/P/Ranger — NO drift

**NEXT GATE (PM lockato post-C0.L.1+C1 approval)**:

Phase C Tech Dry-Run continua con **C2 Proficiency Runtime Preparation** (DOCUMENTAL ONLY draft):

| Sub-step | Status | Trigger |
|---|---|---|
| **C2 Proficiency Runtime Preparation** | 🟢 **AUTHORIZED (chain immediata)** | subito post-STEP 1 PRD append |
| **C3 ILVL + Backfill** | 🔒 **HOLD** | PM review post-C2 |
| **C4 Drop Table** | 🔒 **HOLD** | post-C3 (HYBRID drop rate PM final richiesto qui) |
| **C5 Class Slug Migration Prep** | 🔒 **HOLD** | post-C4 (class_slug null resolution) |
| **C6 Final Closure** | 🔒 **HOLD** | post-C5 |

**R18.6 Class Halls / Classless Start**: 🔒 PLANNED / HOLD post-Phase C readiness (class_slug null e recruit_unassigned handling formalizzati qui)
**Marketing Brief**: 🔒 DEFERRED

---

**R18.5 status flow (aggiornato)**:
`Phase C0 (STEP 27)` ✅ CLOSED → `Phase C0.L (STEP 28+28-bis)` ✅ CLOSED → `PRD C0+C0.L CLOSED (STEP 29)` ✅ CLOSED → `Phase C0.L.1 (STEP 30)` ✅ CLOSED → `Phase C1 (STEP 31)` ✅ CLOSED → **`PRD C0.L.1+C1 CLOSED (questo append)`** ✅ **CLOSED** → **`Phase C2 Proficiency Runtime Preparation`** 🟢 **AUTHORIZED (chain immediata)** → `C3-C6` 🔒 HOLD post-PM review / `R18.6` 🔒 PLANNED / `Marketing Brief` 🔒 DEFERRED


## R18.5 Phase C2 CLOSED (STEP · 2026-07-08T10:30:00Z)

**Milestone**: **R18.5 Phase C2 Proficiency Runtime Preparation CLOSED** ✅

**Governance**: DOCUMENTAL ONLY append. Nessuna modifica code/DB/migrations/sealed/item table/lore_meta.py. 36 sigilli intatti (pytest 6/6 PASSED).

**Deliverables C2**:
- `/app/memory/r18_5_phase_c2_proficiency_runtime_preparation.md` (SHA256 `86cc0e61b634494125b26a64948c57a8371b83449f936f9cdc9d730775d3d789`, 408 righe)
- `/app/memory/r18_5_phase_c2_proficiency_runtime_preparation.json` (SHA256 `7c7b83ef65d902e43d81d79d5418d198541abbce7a9cb701846d232bc9ce2bba`)

**C2 CLOSED — Decisioni PM verbatim (Q1-Q8)**:

- **Q1=APPROVED** — C2 Proficiency Runtime Preparation design approved come baseline documentale.
- **Q2=ACCEPT 5/5** — 5 Legendary MEDIUM caps accettati come design baseline (non runtime-ready).
- **Q3=DESIGN CONFIRMED** — Divine Resurrect (L3): design attuale confermato (encounter attivi permessi con cap design; no trivializzazione wipe/boss/raid; no implementazione runtime).
- **Q4=OPT-IN OBBLIGATORIO** — Reforge (L5) cross-target: **opt-in obbligatorio**, NO auto-accept nemmeno per guild members; consent target sempre richiesto.
- **Q5=50% DURATA** — Absence Distortion (H3) su elite dungeon 3p: **silence_effective_duration = 50%** (NO full immunity default).
- **Q6=NO-OP FAIR (A)** — Fate Deflection (H4) boss single-target no-add: **A) no-op fair** (NO deflect boss self = immunity).
- **Q7=CONFIRMED** — class_slug null handling confermato: NO auto-derive · NO runtime bridge · NO migration · risoluzione differita a C5/R18.3f + R18.6; recruit_unassigned non equip-ready per gear specializzato.
- **Q8=GO C3** — GO su Phase C3 ILVL + Equipment Backfill Planning (DOCUMENTAL ONLY).

**Approvazioni C2 dettagliate (design layer)**:

- **Validator design APPROVED** (10-step decision flow + 10-case matrix)
- **Lock-state matrix APPROVED (10 stati)**: `equippable` · `locked_class_slug_null` · `locked_recruit_unassigned` · `locked_proficiency_armor` · `locked_proficiency_weapon` · `locked_level` · `locked_reserved_placeholder` · `locked_runtime_not_ready` · `locked_unknown_item_type` · `universal_allowed`
- **UI state mapping APPROVED** (10 badge/tooltip IT)
- **class_slug null handling CONFIRMED** (NO auto-derive · phase resolution C5/R18.3f + R18.6)
- **recruit_unassigned / classless handling CONFIRMED** (permessi: roster/visualizzazione/prompt-tutorial; vietati: equip gear specializzato, full-dungeon/raid readiness)
- **progressive_marker count = 10 CONFIRMED** (source-of-truth C0.L Sezione 3.6)
- **5 Legendary caps ACCEPTED as design baseline (non runtime-ready)**:
  - Void-Pierce (L2): max 1 proc/round
  - Divine Resurrect (L3): encounter attivi allowed as design (cap 1x/enc · target fallen ally same encounter)
  - Reforge (L5): **opt-in obbligatorio** (consent target); consent-deny → cooldown NON consumato (fair)
  - Absence Distortion (H3): boss immune · elite **50% duration**
  - Fate Deflection (H4): boss single-target no-add = **no-op fair** (no deflect boss self immunity)

**Governance C2 CLOSED**:
- 36 seals byte-identical (pytest `backend_r18_4_sealed_integrity_test.py` 6/6 PASSED)
- Zero DB writes / code changes / migrations / `lore_meta.py` touches
- Zero item table D1-D5 modifications (read-only design layer)
- Zero runtime apply / registry apply / drop table apply
- Zero class_slug migration apply / auto-derivation
- Zero proficiency runtime enforcement implementation
- Zero anti-P2W runtime validator implementation
- Classi canoniche W/R/M/P/Ranger — NO drift

**NEXT GATE (PM lockato post-C2 approval Q8=GO)**:

| Sub-step | Status | Trigger |
|---|---|---|
| **C3 ILVL + Equipment Backfill Planning** | 🟢 **AUTHORIZED (chain immediata)** | subito post-STEP 1 PRD append |
| **C4 Drop Table** | 🔒 **HOLD** | PM review post-C3 (HYBRID drop rate PM final richiesto qui) |
| **C5 Class Slug Migration Prep** | 🔒 **HOLD** | post-C4 (class_slug null resolution) |
| **C6 Final Closure** | 🔒 **HOLD** | post-C5 |

**R18.6 Class Halls / Classless Start**: 🔒 PLANNED / HOLD post-Phase C readiness
**Marketing Brief**: 🔒 DEFERRED

---

**R18.5 status flow (aggiornato post-C2 CLOSED)**:
`C0` ✅ → `C0.L` ✅ → `PRD C0+C0.L CLOSED` ✅ → `C0.L.1` ✅ → `C1` ✅ → `PRD C0.L.1+C1 CLOSED` ✅ → `C2 Proficiency Runtime Preparation` ✅ → **`PRD C2 CLOSED (questo append)`** ✅ **CLOSED** → **`Phase C3 ILVL + Equipment Backfill Planning`** 🟢 **AUTHORIZED (chain immediata)** → `C4-C6` 🔒 HOLD post-PM review / `R18.6` 🔒 PLANNED / `Marketing Brief` 🔒 DEFERRED


## R18.5 Phase C3 CLOSED (STEP · 2026-07-08T11:30:00Z)

**Milestone**: **R18.5 Phase C3 ILVL + Equipment Backfill Planning CLOSED** ✅

**Governance**: DOCUMENTAL ONLY append. Nessuna modifica code/DB/migrations/sealed/item table/lore_meta.py. 36 sigilli intatti (pytest 6/6 PASSED).

**Deliverables C3**:
- `/app/memory/r18_5_phase_c3_ilvl_equipment_backfill_planning.md` (SHA256 `cf048bc3367601db70839dff04f79479506da353160066c3c8991db01a6671a9`, 408 righe)
- `/app/memory/r18_5_phase_c3_ilvl_equipment_backfill_planning.json` (SHA256 `87872f41360d7766e780007eb0bc90e4fe217d8176925e5adf3f86f461567aeb`)

**C3 CLOSED — Decisioni PM verbatim (Q1-Q8)**:

- **Q1=APPROVED** — ILVL formula `ilvl(item) = min(max(required_level + rarity_offset[rarity], tier_min[tier]), 60)`. `MAX_ADVENTURER_LEVEL=60`, `MAX_EQUIPMENT_REQUIRED_LEVEL=60`, Legendary ≤ 60.
- **Q2=ACCEPT** — Rarity offsets Common:0 · Uncommon:+2 · Rare:+3 · Epic:+4 · Legendary:+5 (cap 60). Rivalutabili solo se C4/C6 mostra problemi.
- **Q3=APPROVED FLAT 60** — Legendary flat cap 60 approvato: 15 documentali (11 design-ready + 4 Progressive Discovery placeholder) con `ilvl=60` documentale; Progressive `registry_status=reserved` / PENDING PM / `runtime_apply_ready=false`.
- **Q4=ACCEPT** — Legacy fallback `legacy_ilvl = required_level + 2` (default Uncommon-safe).
- **Q5=CONFIRM** — `p2w_legacy_flag=true` per audit only. NO auto-conversion · NO cancellazione · PM review case-by-case.
- **Q6=CONFIRM** — `coalesce(required_level, min_level, 1)`. `required_level` = campo canonico · `min_level` = legacy/fallback.
- **Q7=CUSTOM CANONICAL** — Slot canonical list definitiva (**14 slots**):
  - `head` · `neck` · `shoulders` · `chest` · `back` · `hands` · `wrist` · `waist` · `legs` · `feet` · `main_hand` · `off_hand` · `ring` · `accessory`
  - **Alias documentali (NOT slot separati)**: `belt → waist` · `cloak → back` · `cape → back` · `weapon_main → main_hand` · `weapon_off → off_hand`
  - **`back` OBBLIGATORIO** come slot canonico (cloak/mantelli)
  - **`waist` canonico** · **`belt` = alias legacy display**, NON slot separato
  - **`trinket` RESERVED** per sistema futuro, **NON slot operativo ora**
  - Nessun alias deve creare nuovo slot runtime
- **Q8=GO C4** — GO su Phase C4 Drop Table Dry-Run Planning (DOCUMENTAL ONLY).

**Governance C3 CLOSED**:
- 36 seals byte-identical (pytest `backend_r18_4_sealed_integrity_test.py` 6/6 PASSED)
- Zero DB writes / code changes / migrations / `lore_meta.py` touches
- Zero item table D1-D5 modifications (read-only design layer)
- Zero backfill apply · zero ILVL implementation
- Zero registry apply · zero drop table apply
- Zero class_slug migration · zero auto-derivation
- Classi canoniche W/R/M/P/Ranger — NO drift

**NEXT GATE (PM lockato post-C3 approval Q8=GO)**:

| Sub-step | Status | Trigger |
|---|---|---|
| **C4 Drop Table Dry-Run Planning** | 🟢 **AUTHORIZED (chain immediata)** | subito post-STEP 1 PRD append |
| **C5 Class Slug Migration Prep** | 🔒 **HOLD** | PM review post-C4 (class_slug null resolution + slot canonical migration) |
| **C6 Final Closure** | 🔒 **HOLD** | post-C5 |

**R18.6 Class Halls / Classless Start**: 🔒 PLANNED post-Phase C readiness
**Marketing Brief**: 🔒 DEFERRED

---

**R18.5 status flow (aggiornato post-C3 CLOSED)**:
`C0-C2` ✅ → `C3 ILVL + Equipment Backfill Planning` ✅ → **`PRD C3 CLOSED (questo append)`** ✅ **CLOSED** → **`Phase C4 Drop Table Dry-Run Planning`** 🟢 **AUTHORIZED (chain immediata)** → `C5-C6` 🔒 HOLD / `R18.6` 🔒 PLANNED / `Marketing Brief` 🔒 DEFERRED


## R18.5 Phase C4 CLOSED (STEP · 2026-07-08T13:30:00Z)

**Milestone**: **R18.5 Phase C4 Drop Table Dry-Run Planning CLOSED** ✅

**Governance**: DOCUMENTAL ONLY append. 36 sigilli intatti (pytest 6/6 PASSED). Zero modifiche code/DB/migrations/sealed/item table/`lore_meta.py`.

**Deliverables C4**:
- `/app/memory/r18_5_phase_c4_drop_table_dry_run_planning.md` (SHA256 `ffc75045c33935aed647db12ed2f5348f911b12df3d9c2310eb834df93e44199`, 582 righe)
- `/app/memory/r18_5_phase_c4_drop_table_dry_run_planning.json` (SHA256 `05057ba7847436de7ccfc7674ed9e16a184dce9872ae201eb6d8ab6646a5e8e3`)

**C4 CLOSED — Decisioni PM verbatim (Q1-Q8)**:

- **Q1=APPROVED** — C4 design layer input per C5 (no drop table apply, no runtime).
- **Q2=0.5% UNIFORME** — HYBRID H1-H4 drop rate final design recommendation **0.5% uniforme** (NON runtime; H2 NON differenziato a 0.3%).
- **Q3=LOOT-LOCK APPROVED** — Loot-lock **1×/settimana** approvato per H3 `ergolat-obelisk-focus` + H4 `halodi-fate-quiver` (design only).
- **Q4=A · trinket→accessory ADDITIVE** — `accessory` = slot canonico operativo · `trinket` = alias legacy/documentale RESERVED · in C5 mappare 68 items `slot=trinket` → `slot_canonical=accessory` · mantenere `slot_original=trinket` per audit · **NO 15° slot** · **NO sistema trinket** · NO cambio stat/tier/rarity/source/classe.
- **Q5=DUNGEON=60** — Dungeon canonical count **RESTA 60**; token extra classificato `source_alias`/`secondary_source`, **NON 61° dungeon**.
- **Q6=RAID=12** — Raid canonical count **RESTA 12**; **`hollow-monastery` classificato non-raid** (dungeon/secondary_source/source_alias); NO 13° raid.
- **Q7=PROGRESSIVE POST-C6** — 4 Progressive Discovery source **PENDING PM post-C6** (NON finalizzare in C5); restano `reserved` · `runtime_apply_ready=false` · `registry_status=reserved/PENDING PM`.
- **Q8=GO C5 DOUBLE-TRACK** — GO Phase C5 Class Slug Migration Prep **+ Slot Canonical Migration Planning (DOUBLE-TRACK)** DOCUMENTAL ONLY.

**Approvazioni C4 dettagliate**:
- Source non-null **1500/1500** ✅
- Anti-P2W validation **8/8 PASSED** ✅
- HYBRID H1-H4 drop rate design recommendation = **0.5% uniform** (design layer, no runtime)
- H3/H4 loot-lock **1×/settimana** design approved
- **`trinket → accessory` canonical alias approved** (additive, NO 15° slot, `slot_original` preservato per audit)
- **Dungeon canonical count remains 60** (token extra = `source_alias`/`secondary_source`)
- **Raid canonical count remains 12** (`hollow-monastery` classificato non-raid)
- Progressive Discovery sources remain PENDING PM **post-C6**
- Slot canonical drift documentato: 613 `main-hand` + 129 `off-hand` + 68 `trinket` + 57 `amulet` → alias additivi (migration C5)
- Class coverage OK · no bracket sotto-servito
- Legendary policy compliance: NO shop/premium/real-money/P2W/normal-craft/generic-stat 15/15 ✅

**Governance C4 CLOSED**:
- 36 seals byte-identical (pytest `backend_r18_4_sealed_integrity_test.py` 6/6 PASSED)
- Zero DB writes / code changes / migrations / `lore_meta.py` touches
- Zero item table D1-D5 modifications (read-only reverse-mapping)
- Zero drop rate apply · zero drop table apply · zero economy changes
- Zero class_slug migration / auto-derivation
- Classi canoniche W/R/M/P/Ranger — NO drift

**NEXT GATE (post-C4 approval Q8=GO)**:

| Sub-step | Status | Trigger |
|---|---|---|
| **C5 Class Slug Migration Prep + Slot Canonical + Source Canonicalization (DOUBLE-TRACK)** | 🟢 **AUTHORIZED (chain immediata)** | subito post-STEP 1 PRD append |
| **C6 Final Phase C Closure Report** | 🔒 **HOLD** | PM review post-C5 |

**R18.6 Class Halls · Classless Start · Adventurer Identity**: 🔒 PLANNED (esecuzione class_slug migration + slot_canonical migration + progressive finalization)
**Marketing Brief**: 🔒 DEFERRED

---

**R18.5 status flow (aggiornato post-C4 CLOSED)**:
`C0-C3` ✅ → `C4 Drop Table Dry-Run Planning` ✅ → **`PRD C4 CLOSED (questo append)`** ✅ **CLOSED** → **`Phase C5 Migration Prep (DOUBLE-TRACK)`** 🟢 **AUTHORIZED (chain immediata)** → `C6` 🔒 HOLD post-PM review / `R18.6` 🔒 PLANNED / `Marketing Brief` 🔒 DEFERRED


## R18.5 Phase C5 CLOSED (with mandatory slug errata · 2026-07-08T14:30:00Z)

**Milestone**: **R18.5 Phase C5 Class Slug + Slot Canonical + Source Canonicalization Migration Prep CLOSED** ✅ (with mandatory slug errata Q1+Q5)

**Governance**: DOCUMENTAL ONLY append. 36 sigilli intatti. Zero modifiche code/DB/migrations/sealed/item table/`lore_meta.py`.

**Deliverables C5**:
- `/app/memory/r18_5_phase_c5_class_slug_slot_canonical_migration_prep.md` (SHA256 `71aa46c6b8415ceb4c2c70e8643b0bef4a41cc375f6a091fa050e2a6f5e1c1c2`)
- `/app/memory/r18_5_phase_c5_class_slug_slot_canonical_migration_prep.json` (SHA256 `bc9fb2e6d85e5bbaa9703125ed217448a6f32b1ede1b7b4d2448eac02f3ebd57`)

**C5 CLOSED — Decisioni PM verbatim (Q1-Q8)**:

- **Q1=APPROVED with mandatory slug errata** — C5 approvata con obbligo di correzione terminologica su class_slug (vedi sotto).
- **Q2=CONFIRM** — Slot alias mapping 9 entries (867 items migrating D1-D5 additive; NO 15° slot; `trinket` RESERVED).
- **Q3=B** — `hollow-monastery` = **`secondary_source`** generico · **non-raid** · **non-13° raid** · **non-61° dungeon** · può restare fonte narrativa/secondaria T2 fuori dal conteggio canonico.
- **Q4=CONFIRM DECLASS** — `void-heart-sanctum` (8 items T5) = `source_alias`/`secondary_source` · canonical dungeon count = **60**.
- **Q5=CONFIRM roadmap + FIX canonical slug mapping** — C5→R18.3f→R18.6 confirmed + fix mandatory slug errata.
- **Q6=DEFERRED** — Classless Start UX / Class Halls modal → **design PM dedicato in R18.6**; C6 riporta solo hook handoff (NO modal design dettagliato · NO UI · NO runtime enforcement).
- **Q7=B** — Registry v2 dry-run **in C6 Final Closure** (non subito post-C5, non in R18.3f).
- **Q8=GO C6** — Phase C6 Final Phase C Closure Report + Registry v2 Dry-Run authorized dopo slug errata.

### 🚨 MANDATORY SLUG ERRATA (Q1+Q5 verbatim)

Il mapping precedente `Warrior→warrior · Rogue→rogue · Mage→mage · Priest→priest · Ranger→ranger` era **ambiguo**. I 5 slug inglesi (`warrior/rogue/mage/priest/ranger`) NON sono `canonical_class_slug` — sono solo `legacy_class_label` / `legacy_class_key`.

**Canonical live slug targets (obbligatori da C6 in poi)**:

| legacy_class_label | legacy_class_key | canonical_class_slug | canonical_class_name_it |
|---|---|---|---|
| Warrior | `warrior` | **`guerriero`** | Guerriero |
| Rogue | `rogue` | **`ladro`** | Ladro |
| Mage | `mage` | **`mago`** | Mago |
| Priest | `priest` | **`paladino`** ⚠️ NOTA: paladino, NON priest/prete | Paladino |
| Ranger | `ranger` | **`cacciatore_di_mostri`** | Cacciatore di Mostri |

**C6 deve distinguere sempre 4 campi** per ogni item/adventurer reference: `legacy_class_label` · `legacy_class_key` · `canonical_class_slug` · `canonical_class_name_it`.

**Nessuna migrazione applicata ora.** Solo terminologia corretta nei documenti C6 e Registry v2.

**Approvazioni C5 CLOSED dettagliate**:
- Slot canonical migration plan approved (additive-only, 867 items migrating, 26 universal_allowed, 607 already canonical)
- `trinket → accessory` approved (68 items, `slot_original=trinket` audit)
- `main-hand → main_hand` normalization approved (613 items)
- `off-hand → off_hand` normalization approved (129 items)
- `amulet → neck` approved (57 items)
- `hollow-monastery` = `secondary_source` non-raid
- `void-heart-sanctum` = `source_alias`/`secondary_source` non-61° dungeon
- Canonical **dungeon count = 60** · **raid count = 12**
- class_slug roadmap confirmed (C5 prep → R18.3f readiness → R18.6 execute)
- **Slug errata**: 4-field taxonomy obbligatoria (legacy_label · legacy_key · canonical_slug · canonical_name_it)
- Registry v2 dry-run authorized **in C6 Final Closure**
- R18.6 Class Halls UX **deferred to dedicated PM design**
- 36 seals byte-identical · zero DB/code/migrations · classi canoniche W/R/M/P/Ranger — NO drift

**NEXT GATE (post-C5 approval Q8=GO C6)**:

| Sub-step | Status | Trigger |
|---|---|---|
| **C6 Final Phase C Closure Report + Registry v2 Dry-Run** | 🟢 **AUTHORIZED (chain immediata)** | subito post-STEP 1 PRD append |
| **R18.3f Class Slug Migration Readiness** | 🔒 **HOLD** | PM review post-C6 |
| **R18.6 Class Halls · Classless Start · Adventurer Identity** | 🔒 **PLANNED** | post-R18.3f |
| **Future Apply Phase** (registry/drop/backfill/runtime enforcement) | 🔒 **HOLD** | PM gate dedicato |
| **Progressive Discovery Legendary Finalization (P1-P4)** | 🔒 **HOLD** | PM gate dedicato post-C6 |
| **Marketing Brief** | 🔒 **DEFERRED** | — |

---

**R18.5 status flow (aggiornato post-C5 CLOSED)**:
`C0-C4` ✅ → `C5 Class Slug + Slot + Source Migration Prep (double-track)` ✅ → **`PRD C5 CLOSED with slug errata (questo append)`** ✅ **CLOSED** → **`Phase C6 Final Closure Report + Registry v2 Dry-Run`** 🟢 **AUTHORIZED (chain immediata)** → `R18.3f` 🔒 HOLD / `R18.6` 🔒 PLANNED / `Future Apply Phase` 🔒 HOLD / `Marketing Brief` 🔒 DEFERRED


## R18.6 Class Halls Design CLOSED (with PM final Q1-Q8 answers · 2026-07-08T15:30:00Z)

**Milestone**: **R18.6 Class Halls · Classless Start · Adventurer Identity Design CLOSED** ✅ (with PM final answers Q1-Q8 verbatim)

**Governance**: DOCUMENTAL ONLY append. 36 sigilli byte-identical. `lore_meta.py` invariato (SHA256 `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`). Zero modifiche code/DB/migrations/sealed/item table/R18.5 artifacts/R18.6 design files.

**Deliverables R18.6 approvati**:
- `/app/memory/r18_6_class_halls_classless_start_design.md` (SHA256 `9c866733928411499e1112f9f10815ddfbf84cba71a750abc61b965fa07566e0`)
- `/app/memory/r18_6_class_halls_classless_start_design.json` (SHA256 `e90754214310778b16fc6c0010b87e4fefd3723354b5099ad3b4770374b49deb`)

### R18.6 Design Completed — Scope 13 Sezioni

1. Executive Summary
2. Classless initial state (recruit_unassigned handling)
3. Class Halls Design (5 Sale)
4. Class Hall choice flow (onboarding → modal → conferma → lock post-scelta)
5. Classless lock rules (derivati C2 lock_state matrix #3/#4/#5/#10 — NO nuovi lock_state)
6. Class Hall → Class → Proficiency matrix (PM lockata verbatim)
7. UI/UX player-facing (testuale minimalista Orbus)
8. Italian copy prompts (welcome tooltip · roster badge · modal · warning · confirmation · log Gilda)
9. R18.5 interaction notes (READ-ONLY reference · zero modifiche)
10. R18.3f interaction notes (HOLD · handoff requisiti RQ1-RQ8 documentali)
11. Risk register (12 rischi documentati)
12. PM Open Questions Q1-Q8 (chiuse in questo append verbatim)
13. GO/HOLD recommendation

### 5 Class Halls Approved (with 5 Hall Masters verbatim Q2=A)

| Class Hall | canonical_class_slug | canonical_class_name_it | Hall Master (Q2=A verbatim) |
|---|---|---|---|
| **Fortezza d'Acciaio** | `guerriero` | Guerriero | **Comandante Aldric del Ferro** |
| **Loggia dei Sussurri** | `ladro` | Ladro | **Maestra dei Sussurri Selene** |
| **Circolo dei Nove Sigilli** | `mago` | Mago | **Arcimago Vessel di Memoria** |
| **Reliquiario della Luce Fissa** | `paladino` ⚠️ | **Paladino** (NON priest/prete) | **Custode Isabeau dell'Alba** |
| **Capanno del Sentiero Selvaggio** | `cacciatore_di_mostri` | **Cacciatore di Mostri** | **Vecchio Falconiere Ovyr** |

Hall Masters approvati come **NPC narrativi documentali** — nessun vendor/shop/premium collegato.

### PM Final Answers Q1-Q8 (verbatim)

- **Q1 = C** — **Rite of Rebirth** = **one-time high-cost future option**
  - disponibile solo dopo soglia futura da definire · nessun real-money shortcut · nessun abuso continuo (una sola volta per adventurer)
  - reset/riconversione equip → gate futuro dedicato
  - **NON implementare ora** · design layer only in R18.6 · gate futuro separato

- **Q2 = A** — Hall Masters **CONFERMATI VERBATIM** (5 NPC narrativi come da R18.6 design)

- **Q3 = CUSTOM** — Recluta (`recruit_unassigned`) fate:
  - ✅ **dismissal/congedo AMMESSO** (libera slot Gilda)
  - ❌ **sell/vendita NON AMMESSO**
  - ❌ **transfer/trasferimento NON AMMESSO**
  - **Rationale PM**: liberare spazio ok, evitare mercato Reclute senza identità

- **Q4 = A** — `recruit_unassigned.idle_xp_rate = 0%`
  - Recluta senza classe **NON guadagna XP idle**
  - tutorial/prompt ok, ma **NO progressione utile** fino a scelta Sala

- **Q5 = A** — **1 prova safe-mode dedicata per ognuna delle 5 Sale** (design only ora)
  - 5 encounter scripted (uno per Hall)
  - ognuno mostra `main_stat` + `armor proficiency` + `weapon proficiency` + identità classe
  - **evita scelta cieca** · design layer only · runtime deferred a R18.6 live

- **Q6 = B** — `recruit_unassigned` **cap = 3** per Gilda (simultanee)
  - evita overflow onboarding
  - dismissal Q3 libera slot

- **Q7 = A** — Rito di consacrazione = **istantaneo** (no timer reale)
  - peso della scelta viene da: conferma esplicita + preview Sala + Rite of Rebirth una tantum (Q1)
  - **no 8h reali · no tick in-game**

- **Q8 = B** — Hall trait = **simbolico/narrativo/UI flavor**
  - **NO stat bonus · NO combat bonus · NO economy bonus · NO ranking bonus · NO progression bonus**
  - Ammessi: titolo descrittivo · badge narrativo · testo profilo · log Gilda · flavor tooltip
  - **I talenti veri restano gate futuro separato** (non R18.6)

### Approvazioni R18.6 CLOSED dettagliate

- 5 Class Halls approved (Fortezza d'Acciaio · Loggia dei Sussurri · Circolo dei Nove Sigilli · Reliquiario della Luce Fissa · Capanno del Sentiero Selvaggio)
- 5 Hall Masters approved verbatim (Aldric del Ferro · Selene · Vessel di Memoria · Isabeau dell'Alba · Ovyr)
- Proficiency matrix PM-lockata verbatim (guerriero/ladro/mago/paladino/cacciatore_di_mostri)
- Slug canonical usati verbatim (con slug errata Q1+Q5 di C5)
- Terminologia critica confermata: **Paladino** (NON priest/prete) · **Cacciatore di Mostri** (underscore composto slug)
- Lock_state reuse C2 (10 stati) — NO nuovi lock_state introdotti
- UI badge C2 (ambra · icona porta) — riuso verbatim
- 12 risk register entries documentate
- 13 sezioni scope complete
- **Rite of Rebirth** = one-time high-cost future option (non-premium, no real-money) — Q1=C
- **`recruit_unassigned` dismissal** ammesso, sell/transfer NON ammesso — Q3=CUSTOM
- **`recruit_unassigned` idle XP** = 0% — Q4=A
- **1 Prova di Sala** per ognuna delle 5 Halls (design only) — Q5=A
- **Cap `recruit_unassigned`** per Gilda = 3 — Q6=B
- **Rito consacrazione** = istantaneo — Q7=A
- **Hall trait** = simbolico UI flavor only (NO gameplay bonus) — Q8=B

### Governance Constraints Confirmed R18.6 CLOSED

- **R18.5 Phase C** rimane **CLOSED / LOCKED** — zero modifiche autorizzate
- **R18.3f Class Slug Migration Readiness** rimane **🔒 HOLD** — no auto-start authorized, GO PM separato richiesto
- **Apply Phase** rimane **🔒 HOLD** — 7 preconditions richieste (backup DB · dry-run tech · rollback · seal governance · migration order · failure recovery · PM approval)
- **Progressive Discovery Legendary Finalization (P1-P4)** rimane **🔒 HOLD** — dedicated PM gate post-C6
- **R18.6 live implementation** (UI + funnel + lock_state runtime) rimane **🔒 HOLD** — richiede R18.3f apply + Apply Phase
- **Marketing Brief** rimane **⏸️ DEFERRED** — no priority
- **R18.6 design files** dopo questo append CLOSED sono **🔒 LOCKED** — no re-write senza nuovo GO PM esplicito
- **NO code · NO DB · NO migrations · NO item creation · NO registry apply · NO drop table apply · NO class_slug migration apply · NO class_slug auto-derivation · NO runtime bridge · NO proficiency runtime enforcement · NO Class Halls implementation · NO UI code · NO sealed file modification · NO hard delete**
- **Sealed integrity**: pytest 6/6 passed post-append
- **`lore_meta.py`**: SHA256 `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` — **INVARIATO**

### Rationale PM per HOLD prossimo gate (verbatim)

Prima di implementare Class Halls live, serve preparare bene:
- `class_slug` schema (`adventurer.class_slug` · `adventurer.class_hall_id` · `adventurer.class_hall_assigned_at` · `adventurer.recruit_status`)
- Bridge legacy EN → canonical IT (translation policy immutable lookup)
- `recruit_unassigned` handling runtime (dismissal, cap=3, idle_xp=0%)
- Migration script draft (retroattiva legacy adventurers)

Tutto materiale **R18.3f**, che però rimane **HOLD** finché il PM non emette **GO esplicito separato**.

### NEXT GATE STATE POST-R18.6 CLOSED

| Track | Status | Trigger |
|---|---|---|
| **R18.3f Class Slug Migration Readiness** | 🔒 **HOLD** | GO PM esplicito separato (RACCOMANDATO come next gate, ma non ancora autorizzato) |
| **Progressive Discovery Legendary Finalization (P1-P4)** | 🔒 **HOLD** | dedicated PM gate post-C6 · può procedere parallelo a R18.3f prep |
| **Apply Phase** (Registry / Drop / Backfill / Class_slug / Runtime enforcement) | 🔒 **HOLD** | 7 preconditions + PM coordinated GO |
| **R18.6 live** (Class Halls UI + funnel + lock_state runtime + Rite of Rebirth gate + Prova di Sala encounter) | 🔒 **HOLD** | richiede R18.3f apply + Apply Phase completata |
| **Marketing Brief** | ⏸️ **DEFERRED** | no priority |

---

**R18.5 + R18.6 combined status flow (aggiornato post-R18.6 CLOSED)**:
`R18.5 C0-C6` ✅ **CLOSED · LOCKED** → `R18.6 Class Halls Design (Q1-Q8 resolved)` ✅ **CLOSED · LOCKED (this append)** → `R18.3f` 🔒 HOLD / `Progressive Discovery` 🔒 HOLD / `Apply Phase` 🔒 HOLD / `R18.6 live` 🔒 HOLD / `Marketing Brief` ⏸️ DEFERRED

🛑 **STOP dopo R18.6 CLOSED.** Sistema in **HOLD assoluto**. Nessun auto-start. Attendo GO PM esplicito per il prossimo gate.


## R18.6.1 Canonical 27 Class Halls Expansion CLOSED (with PM final Q1-Q8 · 2026-07-08T16:30:00Z)

**Milestone**: **R18.6.1 Canonical 27 Class Halls Expansion CLOSED** ✅ (with PM final answers Q1-Q8 verbatim + 2 mandatory hall_master renames)

**Governance**: DOCUMENTAL ONLY append. 36 sigilli byte-identical. `lore_meta.py` invariato (SHA256 `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`). Zero modifiche code/DB/migrations/sealed/item table/R18.5 artifacts/R18.6 files/R18.6.1 files (LOCKED dopo questo append).

**Deliverables R18.6.1 approved**:
- `/app/memory/r18_6_1_canonical_27_class_halls_expansion.md` (SHA256 `58cbeb02d2c41603007494b549a78f46b3c7ce03e97babe662ff677494c438bc`)
- `/app/memory/r18_6_1_canonical_27_class_halls_expansion.json` (SHA256 `5eeaeab62fb016f712945cbcf8266854d73f2d64871a9187c3f4abe0e08b189d`)

### Principle 1:1 Canonical

**27 classi = 27 Sale canoniche**. NO Sale condivise. Ogni nuovo avventuriero nasce **Senza Classe / `recruit_unassigned`** (`class_slug=null`). Classe ottenibile SOLO tramite: Sala → prova safe-mode → conferma → assegnazione classe → `class_slug` → sblocco identità/proficiency/equip.

**5 Sale ACTIVE-DESIGN-READY**: `guerriero · ladro · mago · paladino · cacciatore_di_mostri` (verbatim R18.6 LOCKED).
**22 Sale PLANNED / LOCKED-UNTIL-CLASS-READY**: le altre 22 classi.

### 27 Hall Names (approved)

Fortezza d'Acciaio · Loggia dei Sussurri · Circolo dei Nove Sigilli · Reliquiario della Luce Fissa · Capanno del Sentiero Selvaggio · Distilleria del Vapore Verde · Officina Fumante di Rame · Osservatorio delle Costellazioni Fisse · Taverna della Corda Spezzata · Teatro dei Fili di Ferro · Ossario del Cinghiale Bianco · Faro Rovesciato di Onirade · Camera delle Mappe Vive · Cripta del Vessillo Nero · Ariale del Signore delle Fiamme · Scriptorium del Presente Eterno · Radura del Salice Millenario · Fucina degli Anelli Silenti · Sala dei Dadi di Ossidiana · Loggia del Bilico Onesto · Cortile della Corda di Cinabro · Ossario del Cerchio Chiuso · Cripta della Radice Cava · Atelier dei Pigmenti Insanguinati · Cerchio delle Pietre Incise · Capanna dei Tamburi Fermi · Camera dei Sogni Aperti.

### 27 Hall Masters PM APPROVED (Q1 verbatim · 5 LOCKED + 22 approved incl. 2 mandatory renames)

**5 LOCKED (R18.6 Q2=A · invariati)**:
- Guerriero → **Comandante Aldric del Ferro**
- Ladro → **Maestra dei Sussurri Selene**
- Mago → **Arcimago Vessel di Memoria**
- Paladino → **Custode Isabeau dell'Alba**
- Cacciatore di Mostri → **Vecchio Falconiere Ovyr**

**22 approved (20 verbatim + 2 RENAMES obbligatorie anti-collisione)**:

⚠️ **2 RENAMES MANDATORY**:
- **Cronista**: Ambrose di Mnemos → **`Orien di Mnemos`** (evita collisione con **Ambroise** Bardo)
- **Giocatore d'Azzardo**: Sylas Nod → **`Marek Nod`** (evita collisione con **Silas** Nomeperduto Negromante)

**20 verbatim confermati**: Ilyra Ottavia · Nolan Vent · Cassian Vale · Ambroise · Melisandre Corda · Grim Rohl · Nael di Onirade · Odran il Mite · Vaeric Rahn · Aelor Draconis · Bran del Salice · Corvus Anello · Yara della Bilancia · Ren Silenzio · Silas Nomeperduto · Ada Cava · Genoveva Rosso · Halvard Nove · Vaska Tamburo · Elyrah dei Nove Sogni.

**Totale**: **27/27 Hall Masters PM APPROVED · 0 PENDING**.

**Nota governance**: le 2 rinomine sono canonizzate in questo PRD append. I file R18.6.1 `.md/.json` restano con la nomenclatura originale (Ambrose/Sylas) come snapshot documentale del design pre-review. Da questo punto in avanti la **fonte di verità canonica** per hall_master naming è questo PRD append (Orien di Mnemos · Marek Nod).

### Roadmap Readiness in 4 Wave (Q2 verbatim · nessun auto-unlock · gate PM individuale per classe)

**Wave 1** (bridge/riuso tecnico favorevole):
1. **Cacciatore del Vuoto** ⭐ PRIMO PILOTA (R18.6.2 dispatched)
2. Monaco
3. Druido
4. Alchimista
5. Bardo
6. Negromante

**Wave 2** (tecniche/rituali/supporto): 7. Runista · 8. Sciamano · 9. Astrologo · 10. Fabbro Arcano · 11. Artificiere · 12. Cronista

**Wave 3** (marziali avanzate/dark): 13. Cacciatore del Sangue · 14. Cavaliere della Morte · 15. Cavaliere di Draghi · 16. Burattinaio · 17. Parassita

**Wave 4** (sistemiche/creative alta complessità): 18. Cartografo · 19. Mercante · 20. Giocatore d'Azzardo · 21. Pittore · 22. Sognatore

**Ogni passaggio PLANNED → ACTIVE richiede**: `main_stat` · `armor_proficiency` · `weapon_proficiency` · gameplay loop · risorsa/meccanica di classe · equip dedicato sufficiente · guida player-facing · Sala completa · prova safe-mode tecnica · readiness tecnica · review PM.

### Rite of Rebirth Cost Model APPROVED (Q3 verbatim)

- Una tantum per avventuriero · **ISTANTANEO** (no timer reale)
- Non premium · non real-money · non acquistabile con valuta esterna
- **Costo ibrido (4 componenti)**:
  1. Contributo elevato di risorse Gilda
  2. **Sigillo di Rinascita account-bound** (ottenibile via achievement/progressione · non tradabile · non vendibile)
  3. Perdita progressione specifica classe precedente (talenti · abilità di classe)
  4. Equip incompatibile rimosso automaticamente → inviato all'inventario personale (non distrutto)
- **Livello generale dell'avventuriero preservato**
- **Flusso**: classe attuale rimossa → `class_slug=null` temporaneo → Senza Classe → accesso SOLO Sale ACTIVE-DESIGN-READY (mai Sale PLANNED) → nuova prova safe-mode → nuova assegnazione classe
- **Storico classi precedenti conservato** per audit + achievement futuri (log identity persistente)

### 27 Safe-Mode Trial Concepts APPROVED as Baseline (Q4 verbatim)

- Ogni prova sarà **rivista tecnicamente al readiness gate** della singola classe
- **Regole comuni safe-mode**:
  - Insegna il loop base della classe (fair intro gameplay)
  - **NO morte permanente**
  - **NO consumo risorse rare**
  - **NO drop endgame**
  - **NO farmabile** (una-tantum per Recluta · dismissal libera)
  - **NON sostituisce dungeon/tutorial generale della Gilda**
  - Permette al player di **capire se la classe gli piace prima della conferma**

### Cavaliere di Draghi ↔ Stables Integration (Q5 verbatim)

- **Class Hall ≠ Stables** · Class Hall **INTEGRA** Stables · Class Hall **NON sostituisce** Stables
- **Hall gestisce**: identità classe · addestramento · prova safe-mode · legame cavaliere-drago · abilità/progressione classe
- **Stables gestisce (Round 16.3 Phase 8, invariato)**: proprietà drago · custodia · allevamento · cura · gestione · cavalcature · inventario/stato drago
- **Selezione Cavaliere di Draghi**:
  - NON concede drago raro automaticamente
  - NON crea un secondo inventario draghi
  - NON duplica breeding
  - Può sbloccare legame iniziale o prova con drago temporaneo safe-mode
  - **Richiede integrazione tecnica dedicata** al readiness gate (Wave 3, gate PM separato)

### Dark Class Identities LOCKED (Q6 canonical differentiation)

- **Cacciatore del Sangue** = *il proprio sangue come arma* (caccia · marchi di sangue · sacrificio personale controllato · duello/inseguimento preda). **NO** evoca morti · **NO** cadaveri · **NO** ospite · **NO** parassita
- **Parassita** = *il corpo vivente come ecosistema* (simbiosi · infestazione · adattamento · assorbimento · trasferimento risorse/condizioni). **NO** necromanzia · **NO** comando anime · **NO** sacrificio sangue
- **Negromante** = *morte, anime, servitori* (morte · anime · cadaveri · evocazioni · controllo campo tramite servitori). **NO** emomanzia · **NO** simbiosi con ospiti vivi · **NO** marchi Sangue

### Creative Class Identities LOCKED (Q7 canonical differentiation)

- **Bardo** = *esegue* (performance · ritmo · sequenze musicali · supporto gruppo · tempo di esecuzione · weapon family futura `strumento` **RESERVED**)
- **Pittore** = *crea* (pigmenti · segni · tele · forme create · zone dipinte sul campo · combinare colori per effetti/zone/forme temporanee). **NO** ritmo · **NO** sogni
- **Sognatore** = *altera possibilità e percezione* (sogno · possibilità · previsione · stati alterati · effetti ritardati · realtà alternative). **NO** pigmenti · **NO** performance

### Architettura HUB + Satelliti / Off-Site (Q8 verbatim)

- **Modello**: **Complesso Gilda → Atrio delle Vocazioni → 27 accessi/portali/percorsi → Sale locali o satellitari**
- Ogni Sala è **distinta** · può essere:
  - interna Gilda (es. Fortezza d'Acciaio, Loggia dei Sussurri)
  - adiacente (es. Capanno del Sentiero Selvaggio sul limite del bosco)
  - regione specifica (es. Faro Rovesciato di Onirade su isolotto artificiale del lago)
  - spazio istanziato (es. Camera dei Sogni Aperti)
  - raggiungibile via portale
- **Tutte 27 visibili dal sistema centrale (Atrio delle Vocazioni)**, ma NON tutte nello stesso edificio fisico
- **5 ACTIVE-DESIGN-READY**: accesso immediato dall'Atrio
- **22 PLANNED**: appaiono **sigillate · non disponibili · in preparazione · classe non ancora sbloccata** (NO selection)

### Zero-Touch Governance Confirmed R18.6.1 CLOSED

- **R18.5 Phase C** rimane **CLOSED / LOCKED** — zero modifiche
- **R18.6 Class Halls Design (5 Sale)** rimane **CLOSED / LOCKED** — zero modifiche
- **R18.6.1 Canonical 27 Halls** rimane **CLOSED / LOCKED** dopo questo append — zero modifiche future
- **R18.3f Class Slug Migration Readiness** rimane **🔒 HOLD** — no auto-start
- **Apply Phase** rimane **🔒 HOLD** — 7 preconditions
- **Progressive Discovery (P1-P4)** rimane **🔒 HOLD**
- **R18.6 live implementation** rimane **🔒 HOLD**
- **22 Sale PLANNED activation** rimane **🔒 HOLD** — Wave 1-4 gate PM individuale per classe
- **Marketing Brief** rimane **⏸️ DEFERRED**
- **Zero code · zero DB · zero migrations · zero item creation · zero registry apply · zero drop table apply · zero class_slug migration · zero class_slug auto-derivation · zero runtime bridge · zero proficiency runtime enforcement · zero Class Halls implementation · zero UI code · zero sealed file modification · zero hard delete · zero auto-unlock 22 classi PLANNED**
- **Sealed integrity**: pytest 6/6 passed post-append
- **`lore_meta.py`**: SHA256 `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` — **INVARIATO**

### First Readiness Candidate: Cacciatore del Vuoto (Wave 1 · #1)

**R18.6.2 Class Readiness Framework dispatched (documental only)** — pilota **Cacciatore del Vuoto** (`class_slug=cacciatore_del_vuoto` · `hall_id=hall_cacciatore_del_vuoto` · Sala: Faro Rovesciato di Onirade · Hall Master: Nael di Onirade).

R18.6.2 proporrà: main_stat + armor prof + weapon prof + gameplay loop + resource mechanic (candidati: Marchi del Vuoto / Void Essence / Onirade Fragments) + bridge legacy analysis + prova safe-mode detailed + impact registry v2 + rischi.

**R18.6.2 NON attiva Cacciatore del Vuoto live** — solo piano documentale in attesa di gate PM successivo.

---

**Combined status flow (aggiornato post-R18.6.1 CLOSED)**:
`R18.5 C0-C6` ✅ CLOSED · LOCKED → `R18.6 (5 Sale)` ✅ CLOSED · LOCKED → **`R18.6.1 (27 Sale canonical)` ✅ CLOSED · LOCKED (this append)** → `R18.6.2 Class Readiness Framework (Vuoto pilot)` 🟢 **DISPATCHED (documental only, no live activation)** → `R18.3f` 🔒 HOLD / `Wave 1-4 progressive activation` 🔒 HOLD / `R18.6 live` 🔒 HOLD / `Apply Phase` 🔒 HOLD / `Progressive Discovery` 🔒 HOLD / `Marketing Brief` ⏸️ DEFERRED

🛑 **STOP dopo R18.6.1 CLOSED + R18.6.2 dispatch.** Sistema in **HOLD assoluto** post-R18.6.2 design. Nessun auto-start. Attendo GO PM esplicito per il prossimo gate.


## R18.6.2 Class Readiness Framework APPROVED + R18.6.3 Cacciatore del Vuoto Pilot STARTED (2026-07-08T17:00:00Z)

**Milestone**: **R18.6.2 Framework PM APPROVED** ✅ + **R18.6.3 Pilot STARTED · current gate=G1 STAT_DESIGN** 🟢

**Governance**: DOCUMENTAL ONLY append. 36 sigilli byte-identical. `lore_meta.py` invariato (`a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`). Zero code/DB/migrations/sealed/R18.5/R18.6/R18.6.1/R18.6.2 modifiche (tutti LOCKED post-approval).

### Framework 10-Gate APPROVED (F-Q1 verbatim · NO merge)

Sequenza obbligatoria · ogni gate produce **deliverable separato e verificabile** · nessun bypass · nessun accorpamento:

1. **STAT_DESIGN** → main_stat + rationale
2. **PROFICIENCY_DESIGN** → armor + weapon whitelist
3. **GAMEPLAY_LOOP** → loop 4-step base
4. **RESOURCE_MECHANIC** → risorsa canonica + generazione/consumo/scope
5. **EQUIP_DESIGN** → equip base + gap analysis Registry v2
6. **PLAYER_GUIDE** → guida IT canonical (15 fields structured schema)
7. **HALL_COMPLETION** → verifica 20 campi hall profile + hall_master LOCKED
8. **SAFE_MODE_TRIAL** → prova tecnica (obiettivi/restrizioni/fallback/esiti)
9. **TECH_READINESS** → schema DB delta + validator equip + lock_state integration + migration path READINESS-ONLY
10. **PM_REVIEW** → explicit GO PLANNED → ACTIVE-DESIGN-READY

### Wave 1 Progression Policy (F-Q2 verbatim)

- **Wave 1 SERIALE durante pilot Vuoto** (NO parallelization)
- **Monaco = next candidate** ma **NON ancora autorizzato**
- Dopo **PM_REVIEW Vuoto** completo si valuterà parallelizzazione classi Wave 1 successive
- No wave skip · Wave 2 dispatch solo dopo Wave 1 completamente ACTIVE (6/6)

### Registry v3 HOLD (F-Q3 + V-Q5 verbatim)

- Dispatch **DOPO EQUIP_DESIGN Vuoto** · gate futuro dedicato **`R18.6.RV3 — Registry v3 Additive Planning`**
- **Additivo · modulare · separato da R18.5 LOCKED**
- Stima 80-100 items resta **stima, NON target**
- R18.5 Registry v2 LOCKED · zero modifiche

### Sigillo di Rinascita Design HOLD (F-Q4 verbatim)

- Gate dedicato futuro **`R18.6.RB1 — Rite of Rebirth & Sigillo di Rinascita Design`**
- **Timing**: DOPO PM_REVIEW Vuoto · PRIMA implementazione seconda classe (Monaco)
- **NON integrare in R18.3f** · gate dedicato separato

### Player-Facing Guide 15 Fields Schema (F-Q5 verbatim)

**Italiano canonical + struttura i18n-ready** · NO traduzioni ora · schema campi strutturati:

```
class_name · class_slug · summary · main_stat · armor_proficiency ·
weapon_proficiency · gameplay_style · strengths · weaknesses ·
resource · core_loop · recommended_equipment · hall_name ·
hall_master · safe_mode_trial
```

### Cacciatore del Vuoto — Pilot Locks (V-Q1..V-Q8 verbatim)

- **V-Q1 · main_stat = `Intelligenza` LOCKED**
  - Rationale PM: unica primaria · balestra = canalizzazione arcana **NON** gear Rogue/Ranger riciclato
  - Penalità XP main stat insufficiente si applica **senza eccezioni**
- **V-Q2 · armor = `cuoio` + `stoffa`** (NO maglia · NO piastre) · entrambi devono privilegiare Intelligenza (no doppia identità statistica)
- **V-Q3 · weapon = `focus` + `pugnale` + `balestra`** · **`lanterna` RESERVED FUTURE**
  - NO in catalogo R18.5 · NO runtime-ready · valutabile in EQUIP_DESIGN
  - NO arco · NO bastone · NO tomo · NO spada
- **V-Q4 · resource = `Frammenti di Onirade`** LOCKED
  - Cap iniziale **5** · scope **encounter-local** · reset a fine dungeon/raid/prova
  - **NON mana alternativo · NON valuta · NON crafting · NON premium · NON trasferibile**
  - Generazione/consumo numerico definiti nel gate **RESOURCE_MECHANIC** (Gate 4)
- **V-Q5**: come F-Q3 · Registry v3 solo dopo EQUIP_DESIGN
- **V-Q6 · access mix**: primo accesso **Atrio delle Vocazioni → portale approdo di Onirade → breve traversata barca** (no combat obbligatorio · no valuta · no equip · no fail · no block Recluta) → **Faro Rovesciato**. Successivi accessi: **portale rapido Gilda**.
- **V-Q7 · retry safe-mode ILLIMITATO**: cooldown=0 · death_penalty=none · resource_loss=none
  - **Anti-farming**: NO drop · NO XP · NO valuta · NO materiali · NO achievement farmabile
  - Fail produce spiegazione + suggerimento + reset rapido + nuovo tentativo
- **V-Q8 · framework 10-gate CONFERMATO** per Monaco e tutte le classi successive · eventuali modifiche framework solo dopo PM_REVIEW Vuoto completo

### ⚠️ CORREZIONE OBBLIGATORIA — Legacy Bridge Cacciatore del Vuoto

Il report R18.6.2 conteneva errore di classificazione (`bridge_legacy=NONE / canonical-new`). **Correzione canonica**:

```yaml
legacy_bridge_source: warlock
canonical_target_slug: cacciatore_del_vuoto
bridge_status: mapped_design_only
migration_status: not_applied
runtime_bridge_status: disabled
```

**Mapping canonico**: `warlock → cacciatore_del_vuoto`

**Regole enforced**:
- **NO** auto-derive
- **NO** migration apply
- **NO** runtime bridge attivo
- **NO** modifica dati live
- **NO** assegnazione automatica classe

**Il bridge serve per readiness/migrazione futura**, NON per assegnare la classe ai nuovi avventurieri. **I nuovi avventurieri continuano a nascere `class_slug=null · status=recruit_unassigned`** (regola R18.6/R18.6.1 invariata).

### R18.6.3 Pilot Cacciatore del Vuoto STARTED

- **Status**: 🟢 STARTED (pilot Wave 1 · #1)
- **Current gate**: **G1 STAT_DESIGN** (dispatched)
- **Deliverable G1**:
  - `/app/memory/r18_6_3_g1_cacciatore_del_vuoto_stat_design.md`
  - `/app/memory/r18_6_3_g1_cacciatore_del_vuoto_stat_design.json`
- **Vincolo Gate 1**: SOLO stat design · NO proficiency (Gate 2) · NO gameplay loop (Gate 3) · NO resource (Gate 4)
- **NO Gate 2 auto-start**

### Governance Constraints Confirmed R18.6.2 APPROVED + R18.6.3 STARTED

- **R18.5 / R18.6 / R18.6.1 / R18.6.2** = **CLOSED · LOCKED** · zero modifiche
- **R18.3f · Apply Phase · Progressive Discovery · R18.6 live · 22 Sale PLANNED activation · Marketing Brief** = **🔒 HOLD / ⏸️ DEFERRED**
- **R18.6.RV3 · R18.6.RB1** = **🔒 HOLD** · gate futuri dedicati
- **Zero code · zero DB · zero migrations · zero item creation · zero registry apply · zero class_slug apply · zero runtime bridge · zero sealed touch · zero `lore_meta.py` touch**
- **Sealed integrity**: pytest 6/6 passed post-append
- **`lore_meta.py` SHA256**: `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` · **INVARIATO**

---

**Combined status flow (aggiornato)**:
`R18.5 C0-C6 LOCKED` → `R18.6 LOCKED` → `R18.6.1 LOCKED` → `R18.6.2 Framework LOCKED` → **`R18.6.3 Cacciatore del Vuoto Pilot STARTED · G1 STAT_DESIGN 🟢`** → G2 PROFICIENCY_DESIGN 🔒 HOLD → G3..G10 🔒 HOLD → `R18.6.RV3 Registry v3` 🔒 HOLD → `R18.6.RB1 Rite of Rebirth` 🔒 HOLD → `Wave 1 successivi (Monaco/Druido/Alchimista/Bardo/Negromante)` 🔒 HOLD → `Wave 2/3/4` 🔒 HOLD → `R18.3f` 🔒 HOLD → `Apply Phase` 🔒 HOLD → `Marketing Brief` ⏸️ DEFERRED

🛑 **STOP dopo R18.6.3-G1 STAT_DESIGN dispatch.** Nessun auto-start Gate 2. Attendo PM review Gate 1 + GO esplicito per Gate 2.


## R18.6.3-G1 STAT_DESIGN CLOSED (with PM final SD-Q1..SD-Q7 · 2026-07-08T17:30:00Z)

**Milestone**: **R18.6.3 Gate 1 STAT_DESIGN CLOSED** ✅ · Gate 2 PROFICIENCY_DESIGN **AUTHORIZED** 🟢

**Governance**: DOCUMENTAL ONLY append. 36 sigilli byte-identical. `lore_meta.py` invariato (`a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`). Zero code/DB/migrations/sealed/R18.5/R18.6/R18.6.1/R18.6.2/G1 modifiche (tutti LOCKED post-approval).

### ⚠️ PRECISAZIONE SEMANTICA OBBLIGATORIA — Legendary ILVL

- **"Legendary flat +60"** era **ERRATO** semanticamente e viene **corretto in tutti i documenti futuri**
- **Corretto**: **"Legendary ILVL = 60"**
- **NON significa "+60 Intelligenza"**
- **ILVL e valore statistica primaria sono sistemi DISTINTI**
- Nessun Legendary riceve automaticamente `+60 Intelligenza`
- Budget statistico Legendary futuro deve rispettare: T5 · rarity budget · soft cap Int 100 · balance classe · utility unica · anti-power-creep

### PM Answers SD-Q1..SD-Q7 (verbatim locked in G1)

- **SD-Q1 · Soft cap Intelligenza = 100 (linear-flattening, NON hard cap)**
  - Int 1-90 → crescita piena
  - Int 91-100 → crescita ancora rilevante
  - Int >100 → diminishing returns progressivi
  - NO blocco artificiale · NO azzeramento bonus · NO step bruschi · NO scaling infinito lineare

- **SD-Q2 · Secondary=Costituzione · Tertiary=Destrezza**
  - Rationale: Vuoto deve restare esposto durante Marchio/Drain/Payoff senza diventare fragile burst puro
  - Dex terziaria · NON aumenta danno principale · NON sostituisce Int · NO build Dex equivalente · NO balestra weapon fisica Ranger/Rogue

- **SD-Q3 · Diminishing returns curve = linear-flattening continua e leggibile**
  - Fino Int 90 → rendimento pieno
  - Int 91-100 → appiattimento leggero
  - Oltre Int 100 → appiattimento progressivo
  - NO curva logaritmica opaca · NO step rigidi 30/60/90 · NO soglie con salti improvvisi
  - Formula numerica definitiva resta futura, NON implementare ora

- **SD-Q4 · Bridge legacy warlock gestito in R18.3f**
  - **NON** creare gate duplicato `R18.6.LB1` (rejected)
  - Bridge canonico: `warlock → cacciatore_del_vuoto` · `bridge_status=mapped_design_only · migration_status=not_applied · runtime_bridge_status=disabled`
  - Nuovi avventurieri restano `class_slug=null · recruit_unassigned` · ottengono classe SOLO tramite Faro Rovesciato

- **SD-Q5 · Tiered soft XP penalty · XP MAI = 0 (hard-block rejected)**
  - Baseline direzionale su rapporto `main_stat_effettiva / main_stat_raccomandata`:
    - ≥85% → 100% XP
    - 70-84% → 90% XP
    - 55-69% → 75% XP
    - <55% → 50% XP
  - **XP minimum = 50%** · non può scendere a 0 per sola carenza main stat
  - Policy globale futura (non esclusiva Vuoto) · G1 documenta solo che Vuoto usa Intelligenza come stat di riferimento futuro

- **SD-Q6 · Saggezza = non prioritaria, preservata per utility difensiva futura**
  - **NON usare termine "dump" come lock definitivo**
  - Saggezza NON aumenta: danno principale · Marchio · generazione Frammenti · Drain · Payoff
  - Può in futuro contribuire a: resistenza al Vuoto · resistenza distorsioni mentali · durata ridotta stati onirici ostili · utility difensiva secondaria
  - NO build Wisdom alternativa

- **SD-Q7 · Balestra scaling MEDIO-ALTO confermato**
  - Focus → Int **ALTO** (canalizzazione/controllo)
  - Balestra → Int **MEDIO-ALTO** (applicazione precisa Marchi)
  - Pugnale → Int **RIDOTTO** (opportunità ravvicinata/rituale/payoff)
  - NO parificare balestra al focus · NO scaling Dex · NO penalty accuracy senza Dex · NO requisito Dex nascosto · NO build ranged fisica
  - Balestra Vuoto = strumento di canalizzazione arcana a distanza (**NON** weapon Ranger/Rogue)

### G1 STAT_DESIGN Approved Summary

- **main_stat = Intelligenza 🔒 LOCKED**
- **soft_cap_Int = 100** · linear-flattening
- **priority order**: Intelligenza → Costituzione → Destrezza · Saggezza non core (utility difensiva futura) · Forza no role
- **Damage profile**: Focus ALTO · Balestra MEDIO-ALTO · Pugnale RIDOTTO · NO Dex/Str damage scaling
- **XP main-stat penalty**: tiered soft (min 50%, mai 0) · policy globale
- **Bridge warlock → cacciatore_del_vuoto**: `mapped_design_only · not_applied · disabled` · gestito in R18.3f (no LB1 duplicato)
- **Legendary ILVL = 60** (NON "+60 Int") · Legendary budget rispetta soft cap Int 100

### Gate 2 PROFICIENCY_DESIGN AUTHORIZED

- **Status**: 🟢 AUTHORIZED (dispatch in questo append)
- **Scope**: SOLO armor whitelist (cuoio + stoffa) + weapon whitelist (focus + pugnale + balestra) + `lanterna` RESERVED valuation
- **Vincolo**: SOLO proficiency · NO gameplay loop (Gate 3) · NO resource (Gate 4) · NO equip base (Gate 5)
- **NO Gate 3 auto-start**

### Governance Constraints Confirmed G1 CLOSED

- **R18.5 / R18.6 / R18.6.1 / R18.6.2 / R18.6.3-G1** = **CLOSED · LOCKED** · zero modifiche
- **R18.6.3-G3..G10** = **🔒 HOLD** (gate PM individuale)
- **R18.6.RV3 · R18.6.RB1 · R18.3f · Apply Phase · Progressive Discovery · R18.6 live · Wave 1 successivi · Wave 2-4 · Marketing Brief** = **🔒 HOLD / ⏸️ DEFERRED**
- **Zero code · zero DB · zero migrations · zero item creation · zero registry apply · zero class_slug apply · zero legacy bridge apply · zero runtime bridge · zero sealed touch**
- **Sealed integrity**: pytest 6/6 passed
- **`lore_meta.py` SHA256**: `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` · **INVARIATO**

---

**Combined status flow (aggiornato)**:
`R18.5 → R18.6 → R18.6.1 → R18.6.2 LOCKED` → `R18.6.3 Cacciatore del Vuoto Pilot STARTED` → **`G1 STAT_DESIGN ✅ CLOSED (this append)`** → **`G2 PROFICIENCY_DESIGN 🟢 AUTHORIZED (dispatched)`** → G3..G10 🔒 HOLD → `R18.6.RV3` 🔒 HOLD → `R18.6.RB1` 🔒 HOLD → `Wave 1 successivi` 🔒 HOLD → `R18.3f` 🔒 HOLD (bridge warlock handling) → `Apply Phase` 🔒 HOLD → `Marketing Brief` ⏸️ DEFERRED

🛑 **STOP dopo R18.6.3-G2 PROFICIENCY_DESIGN dispatch.** Nessun auto-start Gate 3. Attendo PM review G2 + GO esplicito Gate 3.


## R18.6.3-G2 PROFICIENCY_DESIGN CLOSED (with PM final PD-Q1..PD-Q6 · 2026-07-08T18:00:00Z)

**Milestone**: **R18.6.3 Gate 2 PROFICIENCY_DESIGN CLOSED** ✅ · Gate 3 GAMEPLAY_LOOP **AUTHORIZED** 🟢

**Governance**: DOCUMENTAL ONLY append. 36 sigilli byte-identical. `lore_meta.py` invariato (`a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`). Zero code/DB/migrations/sealed/R18.5/R18.6/R18.6.1/R18.6.2/G1/G2 modifiche (tutti LOCKED post-approval).

### G2 Approved Summary

- **armor whitelist**: `cuoio` + `stoffa` LOCKED (entrambi Int-focus · no dual stat identity)
- **weapon whitelist**: `focus` + `pugnale` + `balestra` LOCKED
- **armor excluded**: `maglia` · `piastre`
- **weapon excluded**: `arco` · `spada` · `bastone` · `tomo` · `martello` · `reliquia` · `ascia` · `scudo` · `lancia` · `arma_in_asta`

### PM Answers PD-Q1..PD-Q6 (verbatim locked)

- **PD-Q1 · NO dual-focus · max 1 focus equipaggiato**
  - **Focus**: weapon primaria · preferenza main_hand · **max 1**
  - **Pugnale**: off_hand rituale o main_hand secondaria in build dedicate future
  - **Balestra**: **two-handed** · occupa main_hand · **BLOCCA off_hand**
  - **Loadout consentiti**: Focus+Pugnale · Focus singolo · Pugnale+Focus (inversione mano futura) · Balestra 2H · Pugnale singolo
  - Regola: focus resta weapon primaria · pugnale **NON può sostituirlo** come miglior scaling
  - NO regole slot runtime ora (documental only)

- **PD-Q2 · Soglia numerica balestra DEFERRED a Gate 5 EQUIP_DESIGN**
  - G3 mantiene SOLO gerarchia qualitativa: Focus=ALTO · Balestra=MEDIO-ALTO · Pugnale=RIDOTTO
  - Coefficienti finali richiedono: budget item · ILVL · rarity · affix · velocità weapon · slot occupancy · confronto Focus/Pugnale
  - **NON definire coefficienti finali in GAMEPLAY_LOOP (Gate 3)**

- **PD-Q3 · Sub-gate dedicato futuro `R18.6.LTN — Lanterna Weapon Family Readiness`**
  - **Timing**: DOPO Gate 5 EQUIP_DESIGN · PRIMA Registry v3 (solo se Gate 5 conferma necessità lanterna)
  - Lanterna resta: **RESERVED FUTURE · NOT EQUIPPABLE · NOT REGISTRY-READY · NOT RUNTIME-READY**
  - NO item lanterna · NO slot · NO family live · NO registry entry · NO proficiency operativa ora

- **PD-Q4 · `class_proficiency = "cacciatore_del_vuoto"` (lowercase snake_case)**
  - **NON usare**: `CacciatoreDelVuoto` · `VoidHunter` · `Warlock`
  - `warlock` resta esclusivamente: `legacy_bridge_source=warlock · canonical_target_slug=cacciatore_del_vuoto · mapped_design_only · not_applied · runtime_disabled`

- **PD-Q5 · Tooltip UI player-facing = italiano puro**
  - **NO codici come `[C2#7]`, `ERR-PROF-04`, `LOCK_12`** nell'UI standard
  - Esempi approvati:
    - "Non puoi equipaggiare questo oggetto: la tua classe non possiede la proficiency richiesta."
    - "Richiede la classe Cacciatore del Vuoto."
    - "Richiede il livello 42."
    - "Scegli una Sala di Classe prima di equipaggiare oggetti specializzati."
  - Codici tecnici (es. `error_code="LOCKED_PROFICIENCY_WEAPON"`) SOLO in log/telemetria/debug, MAI in UI standard

- **PD-Q6 · Affix class-specific integrati in Gate 5 EQUIP_DESIGN**
  - **NO sub-doc separato `R18.6.AFX` ora**
  - Gate 5 DEVE includere sezione obbligatoria "Cacciatore del Vuoto — Class-Specific Affix Design"
  - Esempi affix da progettare in Gate 5: potenza Marchio · durata Marchio · efficacia Drain · generazione Frammenti · efficacia Payoff · bonus contro incorporei · bonus contro summon/distorsioni Vuoto
  - Vincoli: NO affix generici che rendano gear migliore per Mago/Rogue/Ranger · NO doppio scaling Int/Dex · NO modifica catalogo R18.5 · NO item generation prima Gate 5
  - Post Gate 5: affix approvati → Registry v3 Planning · sub-gate AFX aperto solo se volume/complessità richiedono

### Gear Sharing Policy Chiarita (verbatim PM)

Item condiviso per weapon/armor family **NON è automaticamente ottimale** per tutte le classi:
- Cuoio Dex → adatto Rogue/Ranger · **NON** ottimale per Vuoto
- Cuoio Int + affix Marchio → identità Vuoto
- Balestra Dex → identità fisica Ranger/Rogue
- Balestra Int + affix Vuoto → identità Vuoto

**Mitigation stack**: `class_proficiency + main_stat_target + affix class-specific + XP/main-stat messaging` · **NO nuove eccezioni alla proficiency**

### Gate 3 GAMEPLAY_LOOP AUTHORIZED

- **Status**: 🟢 AUTHORIZED (dispatch in questo append)
- **Scope**: SOLO gameplay loop · COME si gioca la classe
- **Vincoli**: NO resource numeric finalization (Gate 4) · NO damage coefficient finalization (Gate 5) · NO affix design (Gate 5) · NO Gate 4 auto-start

### Governance Constraints Confirmed G2 CLOSED

- **R18.5 / R18.6 / R18.6.1 / R18.6.2 / G1 / G2** = **CLOSED · LOCKED** · zero modifiche
- **R18.6.3-G4..G10** · **R18.6.LTN** · **R18.6.RV3** · **R18.6.RB1** · **R18.3f** · **Apply Phase** · **Progressive Discovery** · **Wave 1 successivi** · **Wave 2-4** · **Marketing Brief** = **🔒 HOLD / ⏸️ DEFERRED**
- **Zero code · zero DB · zero migrations · zero item creation · zero registry apply · zero class_slug apply · zero legacy bridge apply · zero runtime bridge · zero sealed touch · zero lanterna unlock**
- **Sealed integrity**: pytest 6/6 passed
- **`lore_meta.py` SHA256**: `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` · **INVARIATO**

---

**Combined status flow (aggiornato)**:
`R18.5 → R18.6 → R18.6.1 → R18.6.2 LOCKED` → `R18.6.3 Vuoto Pilot` → G1 ✅ CLOSED → **G2 ✅ CLOSED (this append)** → **G3 GAMEPLAY_LOOP 🟢 AUTHORIZED (dispatched)** → G4..G10 🔒 HOLD → `R18.6.LTN` 🔒 HOLD → `R18.6.RV3` 🔒 HOLD → `R18.6.RB1` 🔒 HOLD → altri gate/wave 🔒 HOLD

🛑 **STOP dopo R18.6.3-G3 GAMEPLAY_LOOP dispatch.** Nessun auto-start Gate 4. Attendo PM review G3 + GO esplicito Gate 4.


## R18.6.3-G3 GAMEPLAY_LOOP CLOSED (Cacciatore del Vuoto · 2026-07-08T19:00:00Z)

**Milestone**: **R18.6.3 Gate 3 GAMEPLAY_LOOP CLOSED** ✅ · Gate 4 RESOURCE_MECHANIC **AUTHORIZED** 🟢

**Governance**: DOCUMENTAL ONLY append. 36 sigilli byte-identical. `lore_meta.py` invariato (`a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`). Zero code/DB/migrations/sealed/R18.5/R18.6/R18.6.1/R18.6.2/G1/G2 modifiche (tutti LOCKED post-approval).

### G3 Approved Summary

- **Gameplay Loop**: 4-step **Identify → Mark → Drain → Payoff** LOCKED
  - **Identify**: priorità target (incorporeo > summon > caster > melee)
  - **Mark**: applicazione Marchio del Vuoto (dispel-over-time + silenziamento summon) tramite focus canaliza
  - **Drain**: colpi focus/balestra/pugnale su target marchiato → generano Frammenti di Onirade → accumulo verso cap encounter
  - **Payoff**: consumo Frammenti (3F dispel area / 5F annullamento boss summon)
- **Identity anti-summon/anti-incorporeo**: Cacciatore del Vuoto è specialista contro summon, incorporei, distorsioni arcane. Anti-arcano e rituale.
- **Anti-stall (loop degradato)**: senza summon/incorporei il loop rimane funzionale (Drain diretto su target normali · Payoff utility) · no empty combat
- **Weapon roles**:
  - **focus** = primaria main_hand · applicazione Marchio · Drain principale · Payoff channeling · max 1 (PD-Q1 LOCK) · no dual-focus
  - **balestra** = 2H · ranged arcana · applicazione Marchio a distanza · Drain ranged · blocca off_hand
  - **pugnale** = rituale/opportunistica off_hand · chiude rituali · Payoff ravvicinato
- **Differentiation Mago**: Mago = burst caster AoE elemental (spell puro, no accumulo) · Vuoto = Mark-based drain-payoff (accumulo → burst decisivo). Ruoli DPS distinti. Non competition-ready sugli stessi encounter.
- **Differentiation Cacciatore di Mostri**: main_stat Destrezza vs Intelligenza · armor cuoio+maglia vs stoffa+cuoio · weapon arco/balestra/spada/pugnale/lancia vs focus/balestra/pugnale. Balestra weapon family condivisa MA gameplay non condiviso: balestra fisica scaling Destrezza (ranged hunting) vs balestra di canalizzazione arcana scaling Intelligenza medio-alto (applicazione Marchi). Zero overlap target · complementari in raid.
- **Differentiation Paladino**: Paladino = Healer/Support sacro (difensivo/curativo) vs Vuoto = DPS anti-Vuoto (offensivo). Ruoli opposti · coesistono in raid.
- **Canonical class validation**: **PASS** · non-canonical class references = 0 · guard rule attiva contro `/app/memory/r18_6_1_canonical_27_class_halls_expansion.json`
- **Semantic anchors preservati**: `Legendary ILVL = 60 (non +60 Int)` · slug `cacciatore_del_vuoto` snake_case · tooltip UI italiano puro · zero code `[Cx#y]` player-facing
- **Gate 4 RESOURCE_MECHANIC authorized**: input da G3 = loop 4-step + Marchi/Frammenti/Payoff conceptual interactions + cap concept 5 + generation/consumption concept → G4 numeric finalization

### Gate isolation preservata

- G3 ha definito **flussi, ruoli, differentiation, anti-stall, anti-power-creep, interazioni concettuali, UX language**
- G3 NON ha definito coefficienti numerici finali (danno per colpo, drop rate, soglie Int esatte, durata Marchio in turni) → **Gate 4 RESOURCE_MECHANIC**
- G3 NON ha definito slot/rarity/stat allocation equip → **Gate 5 EQUIP_DESIGN**

### Files locked

- `/app/memory/r18_6_3_g3_cacciatore_del_vuoto_gameplay_loop.md` LOCKED
- `/app/memory/r18_6_3_g3_cacciatore_del_vuoto_gameplay_loop.json` LOCKED
- Zero modifiche a R18.5/R18.6/R18.6.1/R18.6.2/G1/G2 (tutti LOCKED post-approval)

### PM verdict

- **R18.6.3-G3 = CLOSED** ✅
- **R18.6.3-G4 RESOURCE_MECHANIC = AUTHORIZED** 🟢
- **R18.6.3-G5 EQUIP_DESIGN = HOLD** 🔒 (attende G4 CLOSED)


## R18.6.3-G4 RESOURCE_MECHANIC CLOSED (Cacciatore del Vuoto · with PM binding answers RM-Q1..RM-Q7 · 2026-07-08T20:00:00Z)

**Milestone**: **R18.6.3 Gate 4 RESOURCE_MECHANIC CLOSED** ✅ · Gate 5 EQUIP_DESIGN **AUTHORIZED** 🟢

**Governance**: DOCUMENTAL ONLY append. 36 sigilli byte-identical. `lore_meta.py` invariato (`a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`). Zero code/DB/migrations/sealed/R18.5/R18.6/R18.6.1/R18.6.2/G1/G2/G3 modifiche (tutti LOCKED post-approval).

### G4 Approved Summary

- **Resource**: **Frammenti di Onirade** · class-exclusive `cacciatore_del_vuoto` · encounter-local · non loot · non inventory · non tradeable · non currency
- **Cap**: **5 LOCK DEFINITIVO** · **indipendente da Intelligenza**
- **Cap indipendenza Int**: LOCK · Int scala su generation probability · payoff reliability · durata Marchio · dispel efficacy · summon nullification chance — MAI su cap
- **Generation**: 1F base per hit su target Marchiato · target non marchiato = 0F · unmarked = zero income · no passive gen
- **Int proc scale**: 0%→10%→20%→30%→40%→45% cap (Int 100+) · linear-flattening
- **Weapon generation matrix LOCK**:
  - **focus**: 1F/hit + Int proc + **channel bonus +1F max 2 attivazioni per SEGMENTO RISORSA**
  - **balestra**: 1F/hit + Int proc (-0.05 penalty) · no channel · 2H = opportunity cost off_hand
  - **pugnale**: 1F/hit + Int proc + **ritual close +1F max 1× per applicazione Marchio** · refresh Marchio NON resetta idoneità bonus
- **Consumption**: atomico · indivisibile · 3F dispel area · 5F annullamento summon boss-invocate
- **Reset condition**: end_of_encounter · end_of_dungeon_room · end_of_raid_phase · player_death · party_wipe · logout/disconnect
- **Reset per fase maggiore boss multi-fase**: NUOVO set abilità · nuovo obiettivo meccanico · nuovo stato boss · nuova arena · transizione narrativa esplicita. **NO reset** su: soglia HP senza cambio meccanico · breve invulnerabilità · wave secondaria · cambio target · animazione · intermezzo minimo · micro-fase · cambio postura
- **UI reset fase**: "La distorsione cambia forma. I Frammenti di Onirade si dissolvono."
- **Payoff 3F (dispel area)**: cast 1T · re-castable senza cooldown · Int reliability 80-98% · effetti arcani validi = deterministico contro effetti dispellabili (Int modifica efficacia/rank, non chance base)
- **Payoff 5F (summon nullification)**:
  - Target **summon STANDARD valida**: **annullamento 100% DETERMINISTICO** (anti-random-waste safeguard LOCK)
  - Target **summon boss-invocata**: efficacia soggetta a safeguard boss + Int scaling (affidabilità vs add-boss · qualità dispel · effetti secondari) — MAI trasformata in "spendo 5F → 2% fallimento casuale"
  - Target **boss diretto**: **IMMUNE** · cast **BLOCCATO** UI se no target valido · **no consumo** · messaggio player: *"Nessuna evocazione valida da annullare."*
  - **5F NON può**: annullare boss · annullare fase · interrompere enrage · cancellare hard mechanic · rimuovere cast letali non-summon · CC totale al boss
- **Marchio del Vuoto LOCK**:
  - **Durata scaling Int**: 3T → 4 → 5 → 6 → 7 → **8T** (Int 100+) · **+0.5T per 50 Int oltre 100** · **hard cap assoluto 10T**
  - **Nessun affix G5 può superare hard cap 10T**
  - **Marchi attivi**: base 3 · +1 Int50 · +1 Int90 · **hard cap 5**
  - **G5 NON può aumentare max Marchi oltre 5**
  - Refresh Marchio: durata reset · NO overlap stacking · **refresh NON crea nuovo Marchio · NON riattiva bonus Pugnale ritual close**
- **PvE silenziamento summon**: 3T (summon standard) · durata ridotta su boss/add protette · boss diretto MAI silenziamento totale
- **PvP effect**: **HOLD** · `effect_status=undefined · runtime_status=disabled` · richiede gate futuro "PvP Class Effect Normalization"
- **Anti-stall clarification (PM verbatim)**: "Generazione minima ≥3F garantita" = **target accessibilità loop dopo Marchio+Drain corretti** · **NON** significa 3 Frammenti gratuiti · **NON** generazione passiva · **NON** Frammenti senza bersaglio Marchiato. Bersaglio non marchiato = 0F LOCK. Loop degradato senza summon/incorporei resta funzionale via bersagli standard Marchiati.
- **Boss safeguards LOCK**: Marchio stack cap 1 su boss · dispel immunity parziale (DoT -50%) · silenziamento SOLO ability non-lethal MAI enrage/hard-cast · 5F annullamento IMMUNE · gen proc bonus 0% su boss (anti-farm) · Int bonus cap +5% max · no boss softlock · no perma-stun (silence cap 1T) · no dispel-spam
- **Gate 5 EQUIP_DESIGN authorized**: input da G4 = cap 5 LOCK · generation matrix weapon · Int 5-axis scaling · Marchio durata + max cap · Payoff 3F/5F deterministic vs summon standard · boss safeguards · reset policy fase maggiore → G5 EQUIP_DESIGN

### PM Binding Answers RM-Q1..RM-Q7 (LOCKED · verbatim distillate)

- **RM-Q1**: cap 5 LOCK indipendente da Int · G5 vietato: `+resource_cap` affix · Legendary cap 6 · bonus temporanei >5 · overcap nascosto
- **RM-Q2**: Focus channel bonus LOCK · max 2 per SEGMENTO RISORSA (encounter single-phase OR fase maggiore boss multi-fase con reset RM-Q6) · NO reset via cambio target/wave minore/micro-fase/cambio postura/transizione visiva · NO rigenerazione via uscita-rientro combat/cambio equip/refresh Marchio
- **RM-Q3**: Pugnale ritual close LOCK · +1F max 1× per applicazione Marchio · refresh durata stesso Marchio NON resetta idoneità · nuovo bonus solo dopo Marchio precedente terminato/rimosso + nuova applicazione valida
- **RM-Q4**: Boss add-summon priority LOCK · 5F opera su summon boss-invocate · Boss diretto IMMUNE + cast bloccato + no consumo + messaggio "Nessuna evocazione valida da annullare" · **anti-random-waste safeguard**: summon standard = 100% deterministico · summon boss-invocata = safeguard boss + Int scaling
- **RM-Q5**: Marchio durata scaling Int 3T→8T LOCK · hard cap assoluto 10T · nessun Marchio >10T · refresh NON crea nuovo · nessun affix G5 supera · Marchi attivi hard cap 5 · G5 non può aumentare
- **RM-Q6**: Reset per FASE MAGGIORE · nuovo set abilità/obiettivo meccanico/stato boss/arena/transizione narrativa · NO soglie HP/invulnerabilità/wave secondaria/cambio target/animazione/micro-fase · reset = Frammenti 0 · contatori gen reset · bonus Focus max 2 disponibile · no carry-over cross-phase
- **RM-Q7**: Silenziamento summon PvE-only LOCK · PvP HOLD · no copia auto PvE · no valore provvisorio · richiede gate futuro dedicato

### Gate isolation preservata

- G4 ha definito **meccanica risorsa numerica** (cap · generation matrix · Int scaling 5 assi · Payoff · reset · boss safeguards)
- G4 NON ha definito coefficienti danno finali weapon · budget statistico item · ILVL scaling · affix design · Registry v3 → **Gate 5 EQUIP_DESIGN**
- G4 NON ha definito PvP effect normalization → **gate futuro PvP dedicato (HOLD)**

### Files locked

- `/app/memory/r18_6_3_g4_cacciatore_del_vuoto_resource_mechanic.md` **LOCKED**
- `/app/memory/r18_6_3_g4_cacciatore_del_vuoto_resource_mechanic.json` **LOCKED**
- Zero modifiche a R18.5/R18.6/R18.6.1/R18.6.2/G1/G2/G3 (tutti LOCKED post-approval)

### PM verdict

- **R18.6.3-G4 = CLOSED** ✅
- **R18.6.3-G5 EQUIP_DESIGN = AUTHORIZED** 🟢
- **R18.6.3-G6 PLAYER_GUIDE = HOLD** 🔒 (attende G5 CLOSED)


## R18.6.3-G5 EQUIP_DESIGN CLOSED (Cacciatore del Vuoto · PM APPROVED · with binding answers EQ-Q1..EQ-Q8 + micro-fix T5/Int · 2026-07-08T21:15:00Z)

**Milestone**: **R18.6.3 Gate 5 EQUIP_DESIGN = PM APPROVED = CLOSED** ✅ · R18.6.RV3 Registry v3 Additive Planning **AUTHORIZED** 🟢 · Gate 6 PLAYER_GUIDE **HOLD** 🔒

**Governance**: DOCUMENTAL ONLY append. 36 sigilli byte-identical. `lore_meta.py` invariato (`a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f`). Zero code/DB/migrations · zero item generation · zero Registry v3 apply · zero CSV · zero mock · zero modifica catalogo R18.5 LOCKED.

### G5 Micro-Fix Applied (pre-closure)

- **T5 tier boundaries corretti**: T5 = Lv56-60 (era Lv55-60) · Lv55 appartiene esclusivamente a T4 · Lv56 primo livello T5
- **Int T5 direction aggiornata**: `expected Int range = 90-115` (era `100+`) · **soft cap Intelligenza = 100 NON-MINIMUM · linear-flattening preserved** · Int 100 = target progressione + diminishing returns · NON requisito minimo T5 · NON requisito equip · NON hard cap
- **ILVL example calc aggiornato**: esempio T5 Legendary aggiornato a lv 60 (hard cap) · rimosso esempio lv 55 (non più T5)
- **NON modificato**: main stat · priorità stat · coefficienti qualitativi · affix · budget tier · rarity multiplier · proficiency

### G5 Approved Summary (verbatim PM decisions EQ-Q1..EQ-Q8)

#### EQ-Q1 · Quantità item — LOCK
- **Design envelope**: 110-130 items
- **Planning target**: ≈120 items
- **Registry v3 deve distinguere**: `new_class_specific_rows` · `new_shared_family_rows` · `existing_universal_eligible_references`
- **NO duplicazione universali per target artificiale**

#### EQ-Q2 · Lanterna — LOCK
- **Status**: `reserved_future_review` (NON `NON_NECESSARIA_forever`)
- **NO proficiency** · **NO Registry v3 row** · **NO item** · **NO sub-gate R18.6.LTN**
- **Rivalutabile SOLO con futuro GO PM esplicito**

#### EQ-Q3 · Stoffa/Cuoio T5 — LOCK
- **Distribuzione T5**: 70% stoffa · 30% cuoio
- **stoffa identity**: canalizzazione · Marchio · Drain · Intelligenza primaria
- **cuoio identity**: mobilità · posizionamento · protezione leggera · Intelligenza primaria
- **NO build Destrezza alternativa** · cuoio Vuoto è Int-focus, MAI Dex hybrid

#### EQ-Q4 · Legendary multiplier — LOCK
- **1.85× budget TOTALE** (inclusa utility_unique)
- **NO 1.85× su stat grezze** · **NO utility su budget già massimizzato** · **NO stat-stick generico**
- **Utility unica consuma parte del budget** · Legendary ILVL=60 · nessun bonus Intelligenza pari a 60 aggiunto (semantic G1 correction LOCK)

#### EQ-Q5 · Combined proc ceiling — LOCK
- **45% hard cap** (Int + affix + set + Legendary + combinazioni tutte)
- **NO stacking bypass** via affix/set/Legendary/combinazioni
- **Coerente con G4 limite** (Int 45% cap Int 100+ soft cap linear-flattening)

#### EQ-Q6 · Universal equipment coverage — LOCK
- **4 posizioni universali equip**: `back` · `neck` · `ring A` · `ring B`
- **Slot canonico**: `ring` (ring A e ring B sono POSIZIONI equip, NON nuovi slot canonici)
- **Slot canonici approvati**: `back` · `neck` · `ring` · `accessory`
- **`trinket` = alias legacy documentale** → riferisce lo slot canonico **`accessory`** (NON nuovo slot operativo)
- **NO `ring1`/`ring2` come slot canonici** salvo futuro gate

#### EQ-Q7 · Weapon coefficients — LOCK (design direction only)
- **Order LOCK**: focus > balestra > pugnale
- **focus** = **1.00 baseline**
- **balestra** = **0.85-0.90 direzionale**
- **pugnale** = **0.70-0.80 direzionale**
- **SOLO DESIGN DIRECTION** · NON formula runtime · NON coefficienti live
- **NO scaling Destrezza**

#### EQ-Q8 · Registry v3 — GO
- **GO R18.6.RV3 Registry v3 Additive Planning**
- **Timing**: dopo G5 CLOSED, PRIMA di Gate 6 PLAYER_GUIDE
- **Gate 6 HOLD fino review RV3**

### Sintesi finale G5 CLOSED

Cacciatore del Vuoto readiness pilot equip architecture LOCKED: budget T1-T5 multiplier 1.0→2.7 · rarity Common-Legendary 1.0-1.85 · weapon focus/balestra/pugnale direzionali (focus baseline · balestra 0.85-0.90 · pugnale 0.70-0.80) · armor stoffa/cuoio 55/45→70/30 · 4 slot universali (back/neck/ring×2) · 10 affix families class-specific · 14 affix vietati · gear sharing analysis vs Mago/Ladro/Cacciatore di Mostri LOCKED · Lanterna `reserved_future_review` · item quantity envelope 110-130 planning target ≈120 · Registry v3 Additive Planning authorized · Gate 6 HOLD. Zero code/DB touch · 36 seals intact · Legendary ILVL=60 semantic preserved · Int soft cap 100 non-minimum · linear-flattening preserved · slot canonici formalizzati (back/neck/ring/accessory · trinket=alias→accessory).

### Files locked

- `/app/memory/r18_6_3_g5_cacciatore_del_vuoto_equip_design.md` **LOCKED post-micro-fix**
- `/app/memory/r18_6_3_g5_cacciatore_del_vuoto_equip_design.json` **LOCKED post-micro-fix**
- Zero modifiche a R18.5/R18.6/R18.6.1/R18.6.2/G1/G2/G3/G4 (tutti LOCKED post-approval)

### PM verdict

- **R18.6.3-G5 = CLOSED · PM APPROVED** ✅
- **R18.6.RV3 Registry v3 Additive Planning = AUTHORIZED** 🟢
- **R18.6.3-G6 PLAYER_GUIDE = HOLD** 🔒 (attende RV3 review + PM GO esplicito)
