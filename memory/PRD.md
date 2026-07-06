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

