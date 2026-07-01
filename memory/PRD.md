# Orbus Online — PRD (post-incident recovery 2026-07-01)

## Contesto post-incident
Il 2026-07-01, l'agente principale in Fase 1 ha erroneamente costruito un MVP fresh (Auth + Guild + Dashboard base) archiviando il progetto Round 16.x avanzato dentro `_legacy/`. Durante quel percorso ha eseguito `drop_database('test_database')` **prima** che il vincolo "NON droppare NULLA" venisse emesso, con perdita irreversibile dello **stato dinamico** del mondo pre-incident (gilde reali, spedizioni, achievement, PvP Elo, trade pact, world state).

Il 2026-07-01 12:30 UTC è stata completata la recovery operazione **Opzione 3+1**:
- codice Round 16.x ripristinato in `/app/backend/` e `/app/frontend/src/` (12 MB backend, 1.9 MB frontend);
- `DB_NAME` cambiato in `orbus_r16` (nuovo DB pulito). `test_database` conservato come snapshot naturale della Fase 1 accidentale;
- backend attivo con 233 endpoint OpenAPI, frontend build production OK.

## Stato attuale
- **Backend live**: 46 gruppi di endpoint API (admin 65, adventurers 9, auth 8, trade-pacts 7, arfus-forge 6, world-boss 6, world 6, quests 6, consortiums 6, raids 6, contracts 6, inventory 6, legendary-forge 5, pvp 5, seasons 5, expeditions 5, resources 5, market 4, auction 4, leaderboard 4, guild-specialization 4, dashboard 4, class-halls 3, achievements 3, site-income 3, altri).
- **DB attivo**: `orbus_r16`, 44 collection, cataloghi core seedati automaticamente dal lifespan (12 classi, 40 tratti, 22 dungeons, 130 items, 13 enchants, 8 continenti, 12 event catalog, 8 resource catalog, world boss "Alveora", 1 season, 14 signature templates).
- **Frontend live**: 5 pagine Landing/Login/Register/CreateGuild/Dashboard + tutte le pagine Round 16.x (Dashboard, Adventurers, ClassHalls, Forge, Raids, RaidBuilder, WorldBoss, World, Auction, Achievements, Admin, AdminAudit, TradePacts, GuildSpecialization, LegendaryForge, ArfusForge, ArfusResearch, Recruitment, Expeditions, Inventory, Chat).

## User personas (invariate)
- Guildmaster (giocatore principale)
- Admin
- Tester QA

## Roadmap post-recovery

### P0 — verifica funzionamento post-recovery
- Smoke test manuale del preview URL con `tester@orbus.test`.
- Verifica pytest full (1292 test) e triage failure attese vs regressioni.
- Verifica ownership check su endpoint `/api/guilds`, `/api/pvp`, `/api/trade-pacts`.

### P0 — completamento seed cataloghi
Ordine consigliato (vedi `incident_recovery_report.md` punto 16 per dettagli):
1. `round160_seed_classes_v2.py` (11 classi V2 + spec_v2)
2. `round160_seed_races.py` (50 razze)
3. `round160_seed_class_halls.py`
4. `round15_seed_achievements.py`
5. `round15_seed_class_identity.py`
6. `round15_seed_item_tags.py`

### P0 — completamento seed tester per demo
7. `seed_tester_adventurers.py`
8. `seed_tester_inventory.py`
9. `seed_round12_preseason.py`
10. `seed_round12_release_tester_roster.py`
11. `seed_round12_demo_opponents.py`
12. `seed_round12_rewards.py`
13. `seed_round13a_dungeon_raid_lore.py`
14. `seed_round13a_items_lore.py`

### P1 — completamento Round 16.3 Phase 7A (PvP Continentale)
Il modulo `app/pvp_continental/` contiene solo `__init__.py`: era il lavoro in corso al momento dell'incident. Da riprendere dalle direttive R16.3 Phase 7A originali (bracket ±200 Elo / ±3 guild level, new-player protection +20%, 3 sfide attive max, 12h cooldown, snapshot deterministico con seed=battle_id, 6 audit events UPPERCASE).

### P2 — cleanup e polish
- `.env`: valutare aggiunta di `ADMIN_EMAILS`, `TESTER_PASSWORD` (usati dal legacy senza default).
- Documentare la scelta `DB_NAME=orbus_r16` vs `test_database` nei runbook.
- Cache HMR frontend: script `rm -rf node_modules/.cache` in supervisor pre-start (opzionale).

## Fuori scopo immediato
- Rebuild dello stato dinamico pre-incident (gilde/spedizioni reali): perdita irreversibile, non recuperabile senza dump.
- Riscrittura Fase 1 fresh: **archiviata** in `_fresh_accidental_build_backup/` e `_fresh_parcheggio_*/`, non usata.

## File di riferimento
- `/app/memory/incident_recovery_report.md` — report dettagliato recovery.
- `/app/memory/test_credentials.md` — credenziali Fase 1 (test_database).
- `/app/memory/BUILD_RULES.md`, `PROD_DEPLOY_CHECKLIST_ROUND_*.md`, `REFACTOR_LOG.md` — docs Round 16.x pre-esistenti.
- `/app/backend/app/seeds/seed_runner.py` — orchestrator dei seed lifespan.
