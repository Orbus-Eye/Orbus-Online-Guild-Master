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
