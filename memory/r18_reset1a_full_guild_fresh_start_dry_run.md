# ROUND 18.Reset.1a - Full Guild Fresh Start Dry-Run
**Data computazione**: 2026-07-05T06:37:27.193232+00:00
**Status**: DRY-RUN COMPLETED - Read-only, zero mutazioni.
**Round successivo (apply)**: R18.Reset.1b (non eseguito).

---
## 1. Executive Summary
Dry-run completato con successo in modalita' strict read-only. Il DB contiene 672 guild attive e 3314 adventurers. Il pool di classi safe per starter regeneration e' di **11 classi** (atteso 11). Zero collezioni premium/billing/subscription rilevate. Storage archive stimato: 4.7 MB (Opzione B, sibling `_r18_archive` collections). Nessuna operazione di scrittura eseguita. Self-audit del proprio sorgente: PASS.

---
## 2. Dry-run Counts
| # | Metrica | Valore |
|---|---|---|
| 01 | Guild totali attive | 672 |
| 02 | Guild con owner_user_id non-null | 672 |
| 03 | Guild orphan (no owner o utente inesistente) | 389 |
| 03bis | Guild linked a user esistente | 283 |
| 04a | Guild test/demo (heuristica name+flag) | 672 |
| 04b | Guild owner email @orbus.test | 280 |
| 04c | Guild owner email REAL domain | 0 |
| 05 | Adventurers da archiviare | 3314 |
| 06a | Inventory items | 111 |
| 06b | Equipped items | 20 |
| 06c | Items catalog (invariante) | 178 |
| 07 | Gold totale / max / avg / guild con gold>0 | 4083608 / 1000000 / 6076.8 / 672 |
| 07bis | Resources field | N/A - Il field `guilds.resources` non esiste in 0/N doc (sample e  |
| 08 | Achievement progress earned | 1686 |
| 09 | PvP seasons / leaderboards / continent LBs | 19 / 36 / 3 |
| 10a | Expeditions by status | {"completed": 14, "in_progress": 3} |
| 10b | Raids by status | {"completed": 1} |
| 10c | Resource missions by status | {} |
| 11a | Guild con banner R18.3c dismiss flag | 1 (dismissed: 1) |
| 11b | Adventurers migrati R18.3c | 496 |
| 12 | Cosmetici da archiviare (pvp+mount+narrative) | 5 + 2 + 1 = 8 |
| 13 | Audit log INVARIANTE (preserve only) | 11896 doc totali |
| 14 | Storage archive stimato | 4.7 MB (pattern B (sibling collections `_r18_archive`)) |

---
## 3. Preserve Identity Plan
**Collezioni preserve obbligatorie** (30 collections, mai toccate durante reset):
- `users`
- `refresh_tokens`
- `login_attempts`
- `password_reset_tokens`
- `audit_log`
- `audit_logs`
- `audit_events`
- `adventurer_classes`
- `adventurer_traits`
- `items`
- `item_sets`
- `enchants`
- `recipes`
- `races`
- `talent_tree_definitions`
- `achievements_catalog`
- `class_specializations`
- `dungeons`
- `raid_dungeons`
- `world_boss_catalog`
- `world_continents`
- `continent_event_catalog`
- `continent_resource_catalog`
- `legendary_recipe_catalog`
- `legendary_items_catalog`
- `arfus_technology_catalog`
- `guild_specialization_catalog`
- `narrative_routes`
- `mount_catalog`
- `counter_tags`
- `guild_site_income_config`

**Guild identity fields preserve**: `_id`, `id`, `public_id`, `owner_user_id`, `name`, `created_at`, `updated_at`, `is_test_artifact`, `is_grandfathered`, `is_demo_opponent`. Il name della guild NON viene mai modificato.

---
## 4. Archive Plan
**Pattern**: Opzione B (sibling collections `_r18_archive`). Ogni collection listata sotto verra' copiata in una collection gemella con suffisso `_r18_archive` durante R18.Reset.1b.

| Collection live | Archive target | Doc count |
|---|---|---|
| `adventurers` | `adventurers_r18_archive` | 3314 |
| `inventory_items` | `inventory_items_r18_archive` | 111 |
| `equipped_items` | `equipped_items_r18_archive` | 20 |
| `class_halls` | `class_halls_r18_archive` | 1673 |
| `achievement_progress` | `achievement_progress_r18_archive` | 1686 |
| `expeditions` | `expeditions_r18_archive` | 17 |
| `expedition_members` | `expedition_members_r18_archive` | 45 |
| `raids` | `raids_r18_archive` | 1 |
| `raid_participants` | `raid_participants_r18_archive` | 20 |
| `chat_messages` | `chat_messages_r18_archive` | 2 |
| `squads` | `squads_r18_archive` | 2 |
| `guild_structures` | `guild_structures_r18_archive` | 421 |
| `guild_specialization_choice` | `guild_specialization_choice_r18_archive` | 4 |
| `guild_trade_pacts` | `guild_trade_pacts_r18_archive` | 1 |
| `guild_site_income_ledger` | `guild_site_income_ledger_r18_archive` | 14 |
| `guild_world_presence` | `guild_world_presence_r18_archive` | 6 |
| `guild_xp_daily_cap_tracker` | `guild_xp_daily_cap_tracker_r18_archive` | 10 |
| `pvp_seasons` | `pvp_seasons_r18_archive` | 19 |
| `pvp_season_leaderboards` | `pvp_season_leaderboards_r18_archive` | 36 |
| `pvp_defense_teams` | `pvp_defense_teams_r18_archive` | 3 |
| `pvp_cosmetics_unlocked` | `pvp_cosmetics_unlocked_r18_archive` | 5 |
| `guild_mount_ownership` | `guild_mount_ownership_r18_archive` | 2 |
| `narrative_rewards_unlocked` | `narrative_rewards_unlocked_r18_archive` | 1 |
| `continent_leaderboard_snapshots` | `continent_leaderboard_snapshots_r18_archive` | 3 |
| `continent_event_instances` | `continent_event_instances_r18_archive` | 1 |
| `seasons` | `seasons_r18_archive` | 1 |
| `season_participations` | `season_participations_r18_archive` | 14 |
| `season_rewards` | `season_rewards_r18_archive` | 4 |
| `world_boss_events` | `world_boss_events_r18_archive` | 4 |
| `recruitment_offers` | `recruitment_offers_r18_archive` | 255 |
| `shop_daily_offers` | `shop_daily_offers_r18_archive` | 18 |
| `tester_tool_snapshots` | `tester_tool_snapshots_r18_archive` | 14 |

---
## 5. Reset Candidates
**Guild fields resettati**:
- `level`: 5 (sample) -> **1**
- `gold`: sum=4083608, avg=6076.8 -> **100 per guild**
- `reputation` -> **0**
- `current_roster_size` -> **5** (post-regen starter)
- `max_roster_cap` -> **ricomputato** via formula R18.1
- `r18_beta_opt_in` -> **false**
- `raids_completed_count`, `raids_victory_count`, `max_raid_score`, `last_raid_completed_at`, `max_team_power_ever` -> **0/0/0/null/0**
- `r18_roster_cap_computed_at` -> **ISO now**

**Collezioni azzerate completamente**: vedi §4.

---
## 6. Starter Roster Simulation
**Pool classi safe**: 11 classi (atteso: 11).

**Nessuna discrepanza**. Il pool safe combacia esattamente con l'atteso.

### Pool safe (slug ordinati)
- `alchemist`
- `bard`
- `druid`
- `mage`
- `monk`
- `paladin`
- `priest`
- `ranger`
- `rogue`
- `warlock`
- `warrior`

### Blacklist esplicita hidden slugs
- `cacciatore_di_mostri`
- `cacciatore_del_vuoto`

### Roster starter simulato per guild
- Size per guild: 5
- Sample simulato (primi 5): ['alchemist', 'bard', 'druid', 'mage', 'monk']

> Simulazione simbolica. Nessun doc creato in adventurers. Il pattern reale usera' rng deterministico con seed per guild_id per riproducibilita' del rollback.

---
## 7. Starter Kit Simulation
**Kit simbolico** (NO payload di scrittura, NO items reali):

- `gold` = **100**
- `potions_base` = **3**
- `xp_boosters` = **0**

**Note**:
- 100 gold e' il valore starter attualmente usato da guild onboarding (verificato su sample legacy).
- 3 pozioni base: proposta e1_dev, da confermare PM in P0-7.
- 0 XP booster: nessun payload P2W. Consistente con policy non-P2W.
- Rappresentazione SIMBOLICA: nessun doc `inventory_items` creato in questo dry-run.

---
## 8. Active/In-progress Activity Impact
**Expeditions by status**: {'completed': 14, 'in_progress': 3}

**Raids by status**: {'completed': 1}

**Resource missions by status**: {}

**Expedition members**: 45

**Raid participants**: 20

**Strategia proposta**: tutte le expedition/raid/resource mission attive vengono archived + delete durante R18.Reset.1b. Nessun completamento post-hoc. I player attivi al momento del reset (nessuno atteso) vedranno il banner welcome §14 al prossimo login.

---
## 9. Leaderboard/Achievements Impact
**Leaderboard state completo**: {
  "pvp_seasons": 19,
  "pvp_season_leaderboards": 36,
  "continent_leaderboard_snapshots": 3,
  "global_seasons": 1,
  "season_participations": 14,
  "season_rewards": 4
}

**Achievement progress**: 1686 doc

**Strategia raccomandata**: L.d (nuova era) + Ach.d (Hall of Fame + Founder badge combo). Vedi §12 di r18_reset0_full_guild_fresh_start_plan.md per il razionale completo.

---
## 10. R18 Migration/Banner Impact
**R18.3c orphan migration state**:
- Adventurers migrati R18.3c: 496
- Guild con banner field: 1
- Guild banner dismissed: 1

**Strategia**: banner R18.3c e' obsoleto post-reset. Il campo `migration_banner_r18_3c_dismissed` viene resettato o archiviato con la guild. Nuovo banner welcome R18.Reset.0 sostituisce.

---
## 11. seed_round5 Warning Analysis
**Warning**: `orbus.seed_round5 - WARNING - starter backfill failed: 'base_strength'`

**Location**: `app/scripts/seed_round5.py`

**Root cause (ipotesi)**:
La routine starter_backfill legge il catalog adventurer_classes SENZA filtro `is_playable != False`. Pesca quindi le 2 hidden classes R18.3a (cacciatore_di_mostri, cacciatore_del_vuoto) che sono seedate senza il campo `base_strength`. Alla lettura `klass['base_strength']` sollevano KeyError; il try/except cattura il fallimento (starter_backfill=0). Nessun impatto player-facing, solo log warning.

**Legge hidden classes senza filtro is_playable**: None

**Hidden classes senza base_strength in DB**: 3

**Player-facing impact**: none (try/except catch, silent no-op)

**Reset R18.Reset.1b lo rende obsoleto?**
PARZIALMENTE. Se dopo il reset seed_round5.starter_backfill viene ancora invocato al boot, il warning si ripresentera'. Se pero' il reset elimina la condizione trigger (es. tutte le guild hanno gia' roster >= threshold post-regen), la routine potrebbe non entrare piu' nel ramo che fallisce. Rivalutare post-reset con log inspection.

**Future patch candidate**: R18.3a.2-bis: patch simmetrica a filter_safe_class_pool. Aggiungere `is_playable != False` al pool di seed_round5. Fix di 1 linea, stesso pattern di R18.3a.2. Solo se warning persiste post-reset.

**Rischio residuo se NON patchiamo prima del reset apply**: BASSO. Il warning e' catturato, non causa HTTP 500 ne' corruzione dati. Puo' essere lasciato in HOLD fino a R18.Reset.1c (apply). Se dopo apply il warning resta, aprire R18.3a.2-bis come round dedicato.

**IMPORTANTE**: questo dry-run NON modifica `seed_round5.py`. Solo lettura e analisi.

---
## 12. Storage Estimate
**Pattern**: B (sibling collections `_r18_archive`)

**Storage totale stimato**: 4.7 MB (4924059 bytes)

**Retention proposta**: 90 giorni

**Breakdown per collection** (top-10 by size):

| Collection | Doc count | Avg obj (bytes) | Size (bytes) |
|---|---|---|---|
| `adventurers` | 3314 | 882 | 2925048 |
| `guild_structures` | 421 | 1400 | 589546 |
| `achievement_progress` | 1686 | 303 | 511417 |
| `class_halls` | 1673 | 293 | 491594 |
| `recruitment_offers` | 255 | 649 | 165584 |
| `inventory_items` | 111 | 467 | 51861 |
| `tester_tool_snapshots` | 14 | 2700 | 37810 |
| `expedition_members` | 45 | 834 | 37531 |
| `expeditions` | 17 | 2080 | 35371 |
| `pvp_season_leaderboards` | 36 | 447 | 16104 |

> Storage extra temporaneo per l'archive. La retention proposta e' 90 giorni (poi dump esterno + drop).

---
## 13. Rollback Plan
**Pattern**: Opzione B (sibling collections _r18_archive)

**Snapshot path**: `/app/memory/backups/r18_reset0_prestart/`

**Manifest file**: `manifest.json`

**Steps**:
- 1. Verifica manifest.json presente in snapshot_path
- 2. Per ogni collection listata: leggi <name>_r18_archive
- 3. Cancella docs live con marker archived_at_reset=True (marker che verra' inserito in R18.Reset.1b)
- 4. Insert docs da _r18_archive nella collection live (bulk sequenziale)
- 5. Emetti audit event R18_RESET0_ROLLED_BACK
- 6. Verifica count pre-reset == count post-rollback

**Restore time estimate**: 60 secondi

**Retention window**: 90 giorni

**Test fixture**: 1 guild sintetica + 3 adv + 1 expedition

**Comando CLI**:
```
python -m app.scripts.r18_reset0_rollback --confirm --manifest=/app/memory/backups/r18_reset0_prestart/manifest.json
```

> Il rollback NON usa hard delete su archive. Le collections _r18_archive restano intatte anche dopo rollback (per retention window).

---
## 14. Apply Plan (step-by-step per R18.Reset.1b)
**Target**: R18.Reset.1b (apply, NON in questo round)

**Steps** (non eseguiti in questo round):

- S1. Feature flag double-gate check (R18_REWORK_ENABLED, R18_TALENT_ENGINE_ENABLED restano OFF)
- S2. Precondition audit: run dry-run again, verifica counts stabili
- S3. Snapshot manifest.json produzione in /app/memory/backups/r18_reset0_prestart/
- S4. Per ogni collection in ARCHIVE_COLLECTIONS: aggregate([{$match:{}}, {$out: <name>_r18_archive}]) (HANDLED da apply, NON da questo dry-run)
- S5. Reset guilds fields (level=1, gold=100, reputation=0, ...) via update_many
- S6. Wipe adventurers live (delete_many) - o alternative A.c reset in-place a seconda P0-3
- S7. Regen starter roster: 5 adv per guild via safe class pool (11 legacy)
- S8. Regen starter kit: 100 gold + 3 potions + 0 XP
- S9. Emit audit event R18_FULL_GUILD_FRESH_START_APPLIED
- S10. Deploy banner UI ResetWelcomeBannerR18Reset0.jsx

**Tempo esecuzione stimato**: 5 minuti

**Reversibile via**: R18.Reset.1d rollback script

> Questo dry-run NON esegue nessuno di questi step. Descrizione text-only per R18.Reset.1b.

---
## 15. No-Write Proof
**Protezioni tecniche attive**:
- Self-audit statico all'avvio (grep del proprio sorgente)
- Wrapper safe_aggregate() blocca $out/$merge nelle pipeline
- Token forbidden smembrati per evitare falsi positivi
- Nessun import di funzioni mutanti

**Self-audit del sorgente**: PASS

**Chiamate DB consentite**: count_documents, find, aggregate (senza $out/$merge), distinct, list_collection_names, command('collstats', ...)

**Chiamate DB vietate**: insert_one, insert_many, update_one, update_many, replace_one, delete_one, delete_many, bulk_write, .drop(, .rename(

---
## 16. PM Decisions Required Before Reset.1b

**P0-a**. Conferma scope reset (S1 tutte 672 / S3 solo test 283 / S1-except-grandfathered)
- **Raccomandazione e1_dev**: S1 (0 real users, zero rischio)

**P0-b**. Conferma strategia adventurers (A.a delete + regen / A.b archive + regen / A.c reset in-place)
- **Raccomandazione e1_dev**: A.b (archive in adventurers_r18_archive + regen 5 starter per guild)

**P0-c**. Conferma starter kit: 100 gold + 3 pozioni base + 0 XP booster e' accettabile?
- **Raccomandazione e1_dev**: Accettabile. Aggiungerei anche 1 basic weapon per guild come welcome nell'apply, ma non richiesto in questo dry-run.

**P0-d**. Cosmetici earned (5+2+1 doc): archive tutti (come richiesto dal brief) o preserve pvp_cosmetics_unlocked?
- **Raccomandazione e1_dev**: Brief dice archive. Confermo archive. Alternativa preserve richiederebbe riscrittura Ach.d in Founder badge injection separata.

**P0-e**. Warning seed_round5: patchare pre-reset (R18.3a.2-bis) o attendere post-reset per verificare persistenza?
- **Raccomandazione e1_dev**: Attendere post-reset. Rischio residuo BASSO (try/except catch). Se persiste, aprire R18.3a.2-bis come round dedicato.

**P0-f**. Migration banner R18.3c: reset dismiss state su tutte le guild o preservare?
- **Raccomandazione e1_dev**: Reset (l'evento migration originale non e' piu' rilevante post-reset; nuovo banner welcome R18.Reset.0 sostituisce).

**P1-a**. Retention window archive: 30/60/90/180 giorni?
- **Raccomandazione e1_dev**: 90 giorni.

**P1-b**. Trigger reset: manual CLI script vs admin endpoint protected?
- **Raccomandazione e1_dev**: CLI script (stesso pattern R18.3c). Consenti anche admin endpoint per audit trail.

**P2-a**. Banner post-reset welcome dismissibile o sticky?
- **Raccomandazione e1_dev**: Dismissibile (analog. R18.3c).

---

*Firma: e1 main agent - dry-run generato 2026-07-05T06:37:27.193232+00:00*
