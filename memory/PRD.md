# Orbus Online — PRD (Round 16.3 CLOSED incluso Phase 8 V1, 2026-07-01)

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
