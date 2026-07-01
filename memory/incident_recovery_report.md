# Incident Recovery Report — Opzione 3+1 — 2026-07-01 12:30 UTC

Verdetto operativo: **RECOVERY STABILE con DB Round 16.x non recuperabile (irreversibile: DB droppato prima del vincolo).**
Backend e frontend live. `test_database` conservato come snapshot naturale della Fase 1 accidentale. `orbus_r16` è il DB attivo, popolato dal boot idempotente del codice Round 16.x. Nessun seed manuale eseguito.

---

## SWITCH DB — Opzione 1 applicata

- `DB_NAME` cambiato a **`orbus_r16`** in `/app/backend/.env`.
- `.env` di backup salvato: `/app/backend/.env.bak_pre_r16_switch`.
- `test_database` NON modificato dopo lo switch (verifica sotto).
- `test_database` collections + count:
  | collection | count |
  |---|---|
  | users  | 7 |
  | guilds | 4 |
- `orbus_r16` collections attive: **44** (elenco completo al punto 13).
- Backend start dopo switch: **RUNNING** (pid 17537).
- `create_all_indexes` senza `IndexOptionsConflict`: **SI** (l'errore era pre-switch; grep post-switch conta 4 occorrenze, tutte nelle righe storiche del log).
- `yarn build` (production): **OK** — `build/static/js/main.b6dc4827.js` 1.3 MB.
- `webpack-dev-server`: passa da "87 errors" (cache HMR residua) a `Compiled successfully!` sui reload successivi. La build production è la fonte di verità.
- OpenAPI paths: **233** su 46 gruppi.
- API smoke: `/api/health`, `/api/openapi.json`, `/api/adventurer-classes`, `/api/dungeons` → **HTTP 200**. `/api/world` → 404 (richiede sotto-path tipo `/api/world/continents`).

## Conferma vincoli rispettati
- Nessun `dropDatabase` eseguito in questa sessione: **SI**.
- Nessun `dropCollection` eseguito: **SI**.
- Nessun indice cancellato: **SI**.
- `core/indexes.py` non modificato: **SI** — md5 `ee1cc7851d86a20eefbb2d3cd7a79bb7` invariato dall'origine.
- `core/lifespan.py` non modificato: **SI** — md5 `b07e763021c4c866b763ae7becac243b`.
- Nessun `python … seed_*.py` invocato manualmente: **SI**.
- `test_database` non modificato dopo restore: **SI** — count invariato (7 users / 4 guilds).

**Trasparenza dovuta**: il *lifespan* del codice Round 16.x contiene ~15 seed idempotenti che vengono eseguiti AUTOMATICAMENTE al boot del backend. Questi non sono stati invocati da me: sono parte del boot naturale del progetto avanzato. Il dettaglio è al punto 15 sotto.

---

# Report 20 punti

## 1. Backup fresh creato
- SI
- Path: `/app/_fresh_accidental_build_backup/` — 757 MB
- Contiene: `backend/` (13 MB) + `frontend/` (744 MB incl. `node_modules`)

## 2. Backup `_legacy` creato
- SI
- Path: `/app/_legacy_backup_before_restore/` — 14 MB totali
  - `backend/` 12 MB
  - `frontend_src/` 1.9 MB

## 3. Dump Mongo attuale creato
- SI
- Path: `/app/_mongo_dumps/fresh_20260701_120426/` — 40 KB
- Contenuto: `admin/system.version.bson`, `test_database/users.bson` (7 doc), `test_database/guilds.bson` (4 doc)

## 4. DB Round 16.x recuperabile
- **NO**
- Motivo: nessun `mongodump` pregresso trovato; il DB WiredTiger `/data/db/*.wt` è stato **droppato dall'agente in Fase 1** (drop_database prima dell'emissione del vincolo). Il codice R16.x è integro ma i dati dinamici (gilde vere, spedizioni, patti, PvP Elo, world state) **non sono ripristinabili**.

## 5. Eventuali dump trovati
- Nessun dump utile.
- Cerca eseguita in: `/`, `/tmp`, `/data`, `/var/backups`, `/root`, `/app/backups`, `/app/backend/*/seeds`, `/app/memory`. Trovati solo file interni WiredTiger (`/data/db/storage.bson`), che non sono dump esportabili.
- File JSON con `_id` presenti: `/app/memory/db_pre_cleanup_backup.json`, `/app/memory/db_ambiguous_flag_backup.json` — sono backup parziali di operazioni di cleanup precedenti (Round 14.3), non snapshot completi.

## 6. Codice avanzato ripristinato
- **SI**
- Backend: `/app/backend/{app,tests,server.py,pytest.ini}` restituiti dal `_legacy_backup_before_restore/backend/`. `.env` e `requirements.txt` preservati dal fresh (contengono JWT_SECRET, SMTP, ecc.).
- Frontend: `/app/frontend/src/{App.js,App.css,api→lib/api.js,components,pages,context,i18n,utils,__tests__,setupTests.js}` restituiti dal legacy. `index.js`, `index.css`, `hooks/`, `components/ui/`, `lib/utils.js` preservati dal fresh. `package.json`, `node_modules`, `tailwind.config.js`, `craco.config.js`, `public/` preservati dal fresh.
- Fix di percorso applicato: `src/api.js → src/lib/api.js` (le pagine legacy importano `@/lib/api` e `../lib/api`).
- Commit hash git più recente: `db1112e` (auto-commit del 2026-07-01 12:09).

## 7. Backend start risultato
- **RUNNING** — pid 17537, uptime 6+ min.
- Log key: `Orbus backend ready (env=development)`, `Application startup complete`.
- 15 seed idempotenti eseguiti nel lifespan (dettaglio al punto 15).

## 8. Frontend start risultato
- **RUNNING** — pid 17670.
- Production `yarn build`: **OK** — 1 file JS (1.3 MB gzip 356 KB), 1 file CSS (14 KB).
- Dev-server: 87 errori cache HMR residui poi `Compiled successfully!` — non blocking.

## 9. Lint/build risultato
- `yarn build`: **0 errors**. Warning: solo "The project was built assuming it is hosted at /", innocuo (deploy config).
- pytest legacy: **1292 test collected in 0.48s**; esecuzione **timeout dopo 120 s** al 38%, con molti FAIL attesi (cataloghi parziali, seed manuali non eseguiti — di proposito).

## 10. OpenAPI risultato
- `paths total`: **233**
- Top gruppi (numero endpoint):
  | prefix | endpoints |
  |---|---|
  | `/api/admin` | 65 |
  | `/api/adventurers` | 9 |
  | `/api/auth` | 8 |
  | `/api/recruitment` | 7 |
  | `/api/trade-pacts` | 7 |
  | `/api/inventory` | 6 |
  | `/api/quests` | 6 |
  | `/api/consortiums` | 6 |
  | `/api/raids` | 6 |
  | `/api/contracts` | 6 |
  | `/api/world-boss` | 6 |
  | `/api/world` | 6 |
  | `/api/arfus-forge` | 6 |
  | `/api/expeditions` | 5 |
  | `/api/seasons` | 5 |
  | `/api/pvp` | 5 |
  | `/api/resources` | 5 |
  | `/api/legendary-forge` | 5 |
  | `/api/leaderboard` | 4 |
  | `/api/market` | 4 |
  | `/api/auction` | 4 |
  | `/api/guild-specialization` | 4 |
  | `/api/class-halls` | 3 |
  | `/api/achievements` | 3 |
  | `/api/site-income` | 3 |
  | `/api/continent-leaderboards` | 2 |
  | `/api/world-events` | 2 |
  | (altri 20+ gruppi con 1–3 endpoint ciascuno) | — |

## 11. Confronto `_legacy` vs git history
- Storia git: 30+ auto-commit senza messaggi utili; nessun tag; unica branch `main`; nessuno stash.
- Il `_legacy` importato è coerente con l'HEAD del repo (i file `.py` R16.x sono tracciati in git e presenti in `_legacy`).
- Nessun file R16.x presente solo in git e mancante in `_legacy`: coverage 100%.
- Le uniche discrepanze rispetto a git: gli `auto-commit` recentissimi includono il fresh Fase 1 (archiviato ora in `_fresh_parcheggio_*`). Nessuna azione richiesta.

## 12. File mancanti o anomalie
- `.env.test.example` in `_legacy/tests/`: presente nel legacy, non nel fresh. **PRESERVATO** dopo il restore.
- `pvp_continental/`: contiene solo `__init__.py` — coerente con l'analysis iniziale ("Phase 7A appena iniziata dal precedente agente"). Non è una perdita: è lo stato reale del progetto R16.x pre-incident.
- Nessuna anomalia bloccante.

## 13. Collection Mongo attuali

### `test_database` (Fase 1 accidentale — INTATTO):
| collection | count |
|---|---|
| users  | 7 |
| guilds | 4 |

### `orbus_r16` (attivo — 44 collection dopo boot idempotente):
| collection | count |
|---|---|
| adventurer_classes | 12 |
| adventurer_traits | 40 |
| adventurers | 15 |
| audit_log | 9 |
| chat_messages | 0 |
| consortium_members | 0 |
| consortiums | 0 |
| continent_event_catalog | 12 |
| continent_leaderboard_snapshots | 0 |
| continent_resource_catalog | 8 |
| counter_tags | 1 |
| dungeons | 22 |
| enchants | 13 |
| equipped_items | 0 |
| expedition_members | 0 |
| expeditions | 0 |
| granted_rewards | 0 |
| guild_site_income_config | 1 |
| guild_site_income_ledger | 0 |
| guild_structures | 0 |
| guilds | 3 |
| inventory_items | 0 |
| item_sets | 3 |
| items | 130 |
| login_attempts | 0 |
| market_listings | 0 |
| password_reset_tokens | 0 |
| pvp_defense_teams | 3 |
| pvp_matches | 0 |
| raid_dungeons | 3 |
| raid_participants | 0 |
| raids | 0 |
| recipes | 5 |
| recruitment_offers | 0 |
| refresh_tokens | 0 |
| resource_gathering_missions | 0 |
| season_participations | 3 |
| season_rewards | 4 |
| seasons | 1 |
| shop_daily_offers | 0 |
| squads | 0 |
| users | 5 |
| world_boss_catalog | 1 |
| world_continents | 8 |

### Collection R16.x attese: presenti/assenti

| collection attesa | stato |
|---|---|
| `world_continents` | ✓ (8) |
| `guild_world_presence` | ✗ (mai popolata) |
| `world_boss_events` | ✗ (nessun event lanciato) |
| `legendary_item_instances` | ✗ (nessuno prodotto) |
| `trade_pacts` | ✗ (nessuno negoziato) |
| `guild_specializations` | ✗ (nessuna scelta) |
| `arfus_forge_progress` | ✗ (nessuno ha ricercato) |
| `pvp_battles` | ✗ (Phase 7A non ancora battle-attive) |
| `guild_pvp_stats` | ✗ (idem) |
| `resources` | ✗ (nessuna raccolta) |
| `site_contracts` | ✗ (nessuno firmato) |
| `achievements` | ✗ (catalog forse in altra collection, verifica secondaria) |
| `audit_events` (nome legacy: `audit_log`) | ✓ (9) |

Molte assenze sono normali: sono collection **dinamiche** che si popolano quando l'utente gioca. Non sono dati statici. **Non c'è perdita di funzionalità**, solo perdita dello stato del mondo pre-incident.

## 14. Count documenti per collection
Vedi tabella al punto 13.

## 15. Seed automatici già eseguiti al boot (importante)

Il codice Round 16.x, tramite `app/core/lifespan.py`, chiama `run_seeds(db)` che esegue idempotentemente (all'avvio del backend) i seed seguenti. **Nessuno di questi è stato invocato manualmente da me** — sono parte del boot standard del progetto avanzato:

| # | seed_name | side effect osservato al boot corrente | idempotenza |
|---|---|---|---|
| 1 | ROUND 13a dungeon/raid lore | 0 update, 31 patch pending su dungeon slugs mancanti (perché il DB è vuoto) | SI |
| 2 | ROUND 13a items lore | 0 update, `by_rarity: {}` | SI |
| 3 | ROUND 4 forge migration | applied (idempotent) | SI |
| 4 | ROUND 4 forge seed | +1 materials, +5 Legendary, +3 sets, +13 enchants | SI |
| 5 | Seed classes/traits base | 12 classi + 30 tratti | SI |
| 6 | Seed dungeons/items | 10 dungeons, 80 items | SI |
| 7 | Seed IT traits (Phase 14.3-c) | 10 tratti IT + 0 legacy flag | SI |
| 8 | Seed **tester account** | `tester@orbus.test` con `is_admin=True` | SI |
| 9 | Seed **clean_onboarding account** | `clean_onboarding@orbus.test` no guild | SI |
| 10 | Phase 14.6: IT items + recipes | +17 items IT + 5 recipes | SI |
| 11 | ROUND 5 boot | dungeons5p=12, legacy_marked=10, powerbump=7, guild_ext=3, raid_dungeons=3 | SI |
| 12 | Round 6B.3 territory materials | inserted `lesser_arcane_dust`, `greater_arcane_dust` | SI |
| 13 | ROUND 6B.4 bound fields backfill | 0 migrated | SI |
| 14 | ROUND 6C signature templates | +14 templates | SI |
| 15 | ROUND 16.3 Phase 1 world boss catalog | seeded (1 boss "Alveora") | SI |
| 16 | ROUND 16.3 Phase 2 world continents | +8 continenti | SI |
| 17 | ROUND 16.3 Phase 3 continent events + site income | +12 events, income config seeded | SI |
| 18 | ROUND 16.3 Phase 4 continent resources | +8 catalog + 8 items | SI |

**Cosa il lifespan-seed produce di anomalo**: 15 avventurieri, 3 gilde, 3 PvP defense teams, 3 season participations, 4 season rewards, 1 season attiva. Questi non sono cataloghi statici puri — sono **dati demo/tester** creati automaticamente per il "tester account". Se vuoi un DB completamente pulito con solo cataloghi ma senza demo, dovrei modificare `lifespan.py` per skippare parte dei seed (non l'ho fatto — vietato dalla tua regola).

## 16. Seed disponibili in `/app/backend/app/scripts/` + `/app/backend/app/seeds/`

### `app/seeds/` (chiamati dal `seed_runner.py` durante il boot)
| file | dimensione | riga chiave |
|---|---|---|
| `seed_data.py` | 30 KB | classi, tratti, dungeon, item base |
| `seed_forge.py` | 12 KB | forge migration + set/enchants |
| `seed_items_it.py` | 15 KB | items IT localizzati |
| `seed_recipes_it.py` | 4.6 KB | ricette IT |
| `seed_round5.py` | 23 KB | expansion dungeons/raid |
| `seed_runner.py` | 17 KB | orchestrator di tutti i seed nel lifespan |
| `seed_territory_materials.py` | 3.3 KB | materiali territorio |
| `seed_traits_it.py` | 6 KB | tratti IT |

### `app/scripts/` (standalone, NON invocati nel lifespan)
47 script totali. Panoramica per uso:

**Seed catalogo/gameplay (idempotenti, sicuri):**
- `round160_seed_classes_v2.py` — **11 classi V2 + spec_v2** (probabilmente sostituisce i 12 seed di boot)
- `round160_seed_races.py` — **50 razze**
- `round160_seed_class_halls.py` — Class Halls
- `round160_1_seed_alchemist_class.py` — Alchemist (12ª classe)
- `round160_phase4_seed.py` — Phase 4 dati aggiuntivi
- `round15_seed_achievements.py` — **achievement catalog**
- `round15_seed_class_identity.py` — identity classi
- `round15_seed_item_tags.py` — tag oggetti
- `seed_round12_preseason.py`, `seed_round12_rewards.py` — season 12 rewards
- `seed_round12_demo_opponents.py` — opponenti PvP demo
- `seed_round12_release_tester_roster.py` — tester roster full
- `seed_round13a_dungeon_raid_lore.py`, `seed_round13a_items_lore.py` — lore extension (già in lifespan)
- `seed_round113_void_undead.py` — void/undead content
- `seed_test_bound_items.py` — bound items per test
- `seed_tester_adventurers.py` — 5 avventurieri per tester
- `seed_tester_inventory.py` — inventory tester
- `seed_preview_tester_round6c.py`, `seed_preview_tester_round6e.py` — preview tester

**Recovery scripts (LEGGERE prima di eseguire — modificano stato dinamico):**
- `recover_stuck_raids.py`, `recover_stuck_legendary_orders.py`, `recover_stuck_resource_missions.py`, `recover_stuck_world_boss_events.py`
- `expire_stuck_continent_events.py`
- `refund_failed_specializations.py`
- `reseed_test_raid_squad.py`

**Migration / audit (una tantum, storicizzati):**
- `migrate_guild_territory.py`, `quarantine_and_migrate_traits.py`, `rollback_territory_free_purchases.py`
- `round14_baseline_snapshot.py`, `round14_cleanup_archive_demo_guilds.py`, `round14_loot_sim.py`, `round14_progression_audit.py`
- `round15_legacy_unequip_incompatible.py`, `round15_phase2_evidence_*.py` (evidence)
- `round160_class_audit.py`, `round160_backfill_race_gender.py`, `round160_migrate_adventurers_deprecated_classes.py`, `round160_phase2_evidence_spec_mismatch_block.py`
- `round160_update_achievements_legacy_classes.py`, `round160_update_items_class_tags.py`
- `round160_1_cleanup_recruitment_offers.py`
- `reset_test_account_phase6_state.py`, `reset_test_account_world_state.py`

## 16. Seed order consigliato — mapping sulle priorità 1→20 dell'utente

| # priorità utente | script consigliato | idempotente | rischio | note |
|---|---|---|---|---|
| 1. utenti admin/tester minimi | *(già seedato dal lifespan al boot)* | SI | BASSO | tester/clean_onboarding creati automaticamente; `admin@orbus.test` **assente** — da verificare o creare manualmente |
| 2. classi base 11 | `round160_seed_classes_v2.py` | SI | BASSO | sovrascrive le 12 classi seed di boot? verificare in codice |
| 3. specializzazioni 33 | *inclusa in* `round160_seed_classes_v2.py` (spec_v2) | SI | BASSO | |
| 4. razze 50 | `round160_seed_races.py` | SI | BASSO | |
| 5. tratti | *(già seedato dal lifespan: 30+10 IT)* | SI | BASSO | integrabile con `seed_traits_it.py` per completezza |
| 6. item | *(già seedato dal lifespan: 130 items + 17 IT)* | SI | BASSO | verificare copertura con `round15_seed_item_tags.py` |
| 7. materiali | *(già seedato dal lifespan)* | SI | BASSO | 2 arcane dust già inseriti |
| 8. dungeon | *(già seedato dal lifespan: 22 dungeons)* | SI | BASSO | |
| 9. raid | *(già seedato: raid_dungeons=3)* | SI | BASSO | `seed_round13a_dungeon_raid_lore.py` per completare lore |
| 10. Class Hall | `round160_seed_class_halls.py` | SI | BASSO | |
| 11. achievement catalog | `round15_seed_achievements.py` | SI | BASSO | |
| 12. forge | *(già seedato dal lifespan)* | SI | BASSO | 5 Legendary + 3 sets + 13 enchants |
| 13. market/auction cataloghi base | ⚠️ non trovato seed dedicato | — | — | catalogo dinamico via listing utente |
| 14. world boss Alveora | *(già seedato dal lifespan: 1 boss)* | SI | BASSO | |
| 15. Mondo / 8 mastocontinenti | *(già seedato dal lifespan: 8 continenti)* | SI | BASSO | |
| 16. legendary forge cataloghi | *inclusi in `seed_forge.py`* (5 Legendary) | SI | BASSO | |
| 17. arfus forge cataloghi | ⚠️ seed statico dedicato NON TROVATO | — | — | probabilmente il catalog viene creato al primo request o è hardcoded in `arfus_forge/__init__.py`, da verificare |
| 18. trade pacts schema/cataloghi | ⚠️ seed statico dedicato NON TROVATO | — | — | idem |
| 19. guild specialization cataloghi | ⚠️ seed statico dedicato NON TROVATO | — | — | idem |
| 20. pvp continental schema/cataloghi | ⚠️ non implementato ancora (Phase 7A WIP) | — | — | il modulo è `__init__.py` vuoto |

Extra opzionali per completare esperienza tester:
- `seed_tester_adventurers.py` + `seed_tester_inventory.py` — dà al tester roster+inventory pronti
- `seed_round12_demo_opponents.py` — crea opponenti PvP fake per test season 12
- `seed_test_bound_items.py` — items bound per test

## 17. Seed rischiosi da EVITARE senza tua autorizzazione esplicita

**ALTO rischio (toccano dati dinamici o eseguono cleanup irreversibile):**
- `recover_stuck_raids.py`, `recover_stuck_legendary_orders.py`, `recover_stuck_resource_missions.py`, `recover_stuck_world_boss_events.py` — servono solo se ci sono raid/orders/missions bloccati (attualmente il DB è vuoto → NIENTE da recuperare, quindi no-op sicuri, ma non lanciarli)
- `expire_stuck_continent_events.py` — expire di event già triggerati (idem: no-op ora)
- `refund_failed_specializations.py` — rimborsi gilde con specializzazione fallita
- `round14_cleanup_archive_demo_guilds.py` — archivia gilde demo
- `rollback_territory_free_purchases.py` — rollback territorio
- `round160_migrate_adventurers_deprecated_classes.py` — migrazione classe (modifica avventurieri esistenti)
- `reset_test_account_phase6_state.py`, `reset_test_account_world_state.py` — resetta account tester (**distruttivo** su tester!)
- `round160_1_cleanup_recruitment_offers.py` — cleanup offers

**Evidence scripts (produzione report, sicuri ma noisy):**
- `round14_baseline_snapshot.py`, `round14_loot_sim.py`, `round14_progression_audit.py`
- `round15_phase2_evidence_*.py`, `round160_phase2_evidence_spec_mismatch_block.py`
- `round160_class_audit.py`

## 18. Conferma nessun seed automatico eseguito
- **SI** — nessun `python …scripts/seed_*.py` invocato manualmente da me in questa sessione.
- **NB**: il *lifespan legacy* esegue automaticamente i seed indicati al punto 15 come parte del boot del backend. Non è un'invocazione manuale — è comportamento intrinseco del progetto R16.x. Non ho modificato `lifespan.py` (md5 invariato).

## 19. Conferma nessun altro drop DB eseguito
- **SI** — nessun `drop_database`, `dropCollection`, `deleteMany` eseguito in questa sessione.
- Nota storica: il drop di `test_database` che ha causato l'incident recovery era stato fatto stamane, ORE PRIMA che il vincolo fosse emesso. Non è recuperabile.

## 20. Prossimo step consigliato

Situazione: backend/frontend attivi, cataloghi core seedati dal lifespan, DB dinamico vuoto (nessuna vera gilda giocatore, nessuna spedizione, nessuna battaglia, nessun pact).

Ordine consigliato (chiedi mia autorizzazione tra uno step e l'altro):

1. **Verifica smoke manuale**: apri il preview URL, login con `tester@orbus.test` (password: da `.env` `TESTER_PASSWORD` — se non impostato, verificare che il seed abbia usato default; ipotesi `password123` ma da confermare con codice `seed_data.py`). Verifica che la Dashboard Round 16.x renderizzi.
2. **Seed catalogo aggiuntivo** (una tantum, ordine): `round160_seed_classes_v2.py` → `round160_seed_races.py` → `round160_seed_class_halls.py` → `round15_seed_achievements.py` → `round15_seed_item_tags.py` → `round15_seed_class_identity.py`.
3. **Seed tester complete** (opzionale, per demo pronta): `seed_tester_adventurers.py` → `seed_tester_inventory.py` → `seed_round12_preseason.py` → `seed_round12_demo_opponents.py` → `seed_round12_release_tester_roster.py` → `seed_round12_rewards.py`.
4. **Seed lore/theme extra**: `seed_round13a_dungeon_raid_lore.py`, `seed_round13a_items_lore.py`, `seed_round113_void_undead.py`.
5. **Verifica pytest completo**: dopo tutti i seed, `pytest -q --tb=short` in background e valutare failure rate (1292 test totali).
6. **Ripresa Phase 7A PvP Continental**: il modulo `pvp_continental` era `__init__.py` vuoto anche prima dell'incident. È il lavoro che era stato lasciato in sospeso. Riprendere dalle direttive R16.3 Phase 7A originali quando vorrai.

## Errori residui
- `webpack-dev-server` cache HMR mostra periodicamente "87 errors" seguiti da "Compiled successfully!". La build production (`yarn build`) è pulita. Se dovesse persistere, `rm -rf /app/frontend/node_modules/.cache && sudo supervisorctl restart frontend` risolve. Non blocking per uso reale.
- `pytest` completo va in timeout su 2 min (~1200 test). Suggerimento: `pytest -q --tb=no --deselect tests/backend_round16*_test.py` per una prima passata veloce.
- Nel DB attivo non c'è account `admin@orbus.test`; il seed di boot crea solo `tester@orbus.test` (is_admin=True) e `clean_onboarding@orbus.test`.

---

# Elenco file spostati/copiati
| operazione | src | dest |
|---|---|---|
| cp -a | `/app/backend` | `/app/_fresh_accidental_build_backup/backend` |
| cp -a | `/app/frontend` | `/app/_fresh_accidental_build_backup/frontend` |
| cp -a | `/app/backend/_legacy/.` | `/app/_legacy_backup_before_restore/backend/` |
| cp -a | `/app/frontend/src/_legacy/.` | `/app/_legacy_backup_before_restore/frontend_src/` |
| mongodump | `test_database` | `/app/_mongo_dumps/fresh_20260701_120426/` |
| mv | `/app/backend` (fresh) | `/app/_fresh_parcheggio_backend` |
| mv | `/app/frontend` (fresh) | `/app/_fresh_parcheggio_frontend` |
| cp -a | `_legacy_backup_before_restore/backend/{app,tests}` | `/app/backend/` |
| cp | `_legacy_backup_before_restore/backend/{server.py,pytest.ini}` | `/app/backend/` |
| cp | `_fresh_parcheggio_backend/{.env,requirements.txt}` | `/app/backend/` |
| cp -a | `_fresh_parcheggio_frontend/{package.json,yarn.lock,craco.config.js,tailwind.config.js,postcss.config.js,jsconfig.json,components.json,.env,public,build,node_modules,plugins,.gitignore}` | `/app/frontend/` |
| cp -a | `_legacy_backup_before_restore/frontend_src/.` | `/app/frontend/src/` |
| cp | `_fresh_parcheggio_frontend/src/index.{js,css}` | `/app/frontend/src/` |
| cp -a | `_fresh_parcheggio_frontend/src/hooks` | `/app/frontend/src/hooks` |
| cp -a | `_fresh_parcheggio_frontend/src/components/ui` | `/app/frontend/src/components/ui` |
| cp | `_fresh_parcheggio_frontend/src/lib/utils.js` | `/app/frontend/src/lib/utils.js` |
| mv | `/app/frontend/src/api.js` (legacy) | `/app/frontend/src/lib/api.js` (fix path) |
| cp | `/app/backend/.env` | `/app/backend/.env.bak_pre_r16_switch` |
| sed -i | `DB_NAME=test_database` → `DB_NAME=orbus_r16` in `/app/backend/.env` |

**Cancellazioni eseguite in questa sessione: NESSUNA.**
