# ROUND 18.Reset.0 — Full Guild Fresh Start Reset Plan

**Round**: R18.Reset.0
**Data apertura**: 2026-07-04T21:42Z
**Status**: OPEN — Planning-only, Audit-only
**Autore**: e1 main agent (autorizzato da PM decision GO A)

---

⚠️ **ZERO implementazione. ZERO DB write. ZERO reset execution. ZERO codice modificato. ZERO seed. ZERO decisioni sigillate.** Solo materiale per far decidere il PM.

---

## §1 · Executive summary

### Contesto

R18 rework è arrivato al punto di svolta post-R18.3c (sealing 2026-07-04T20:47Z): 496 orphan adventurers migrati (`priest→paladin`, `ranger→cacciatore_di_mostri`, `warlock→cacciatore_del_vuoto`, ecc.), catalog invariato, banner UI rilasciato. R18.3b.1 ha sigillato la mapping decision (**Opzione C.2 + R3**: mapping esplicito 6→5, Saggezza→intellect, ruolo atomico backend + role_display_it UI-only). R18.3a.2 hotfix ha risolto il bug live HTTP 500 su recruitment refresh.

Restano 2 problemi tecnici parcheggiati:
1. **Drift R18.1**: 4 test in `backend_round181_migration_test.py` falliscono perché 360 guilds + 1177 adventurers creati POST-R18.1 non hanno subito il backfill (class_slug, grade, max_roster_cap, r18_beta_opt_in).
2. **Warning `seed_round5.starter_backfill`**: routine di boot che tenta di leggere `base_strength` dalle classi hidden R18.3a. Catturato da try/except (nessun player-facing crash) ma persistente.

Il PM ha deciso di NON risolverli con R18.1.3 backfill puntuale, bensì valutare un **fresh start globale** (R18.Reset.0) che azzererebbe l'esperienza gilda mantenendo continuità di account.

### Numeri chiave (verificati read-only 2026-07-04T21:42Z)

| Metrica | Valore |
|---|---|
| **Guilds totali** | 672 |
| — `is_test_artifact=true` | 669 (99.6%) |
| — `is_demo_opponent=true` | 3 |
| — `is_grandfathered=true` | 7 |
| — con owner email `@orbus.test` | 280 |
| — con owner email `@orbus.preview` | 3 |
| — con owner email REAL domain (gmail/consumer/ecc.) | **0** |
| — orphan (no owner user found) | 389 |
| **Users totali** | 340 (333 @orbus.test + 3 @orbus.preview + 4 altri test) |
| — `is_admin=true` | 2 |
| — `is_test=true` | 0 (flag non usato) |
| **Adventurers totali** | 3302 |
| — con `class_slug` valido (post-R18.1) | 2125 (64%) |
| — con `class_slug=null` (drift orphan) | 1177 (36%) |
| — migrati in R18.3c | 496 |
| — `recruit_unassigned` | 85 |
| **Achievement progress rows** | 1686 |
| **PvP seasons** | 19 · Leaderboards: 36 · Cosmetici unlocked: 5 |
| **Expedition history** | 17 (di cui active/pending: check post) |
| **Recruitment offers cache** | 255 |
| **Inventory items** | 111 · Equipped: 20 |
| **Chat messages** | 2 |
| **Talent progress (R18.2 pilot)** | 0 doc (placeholder solo catalog) |
| **Collections premium/billing/subscription** | **NESSUNA** (solo `pvp_cosmetics_unlocked` cosmetico gratuito) |

### Trade-off nuova esperienza vs perdita progressione

| Dimensione | Perdita | Beneficio |
|---|---|---|
| **Progressione** | 3302 adventurers, 1686 achievement, 19 season leaderboards, 17 spedizioni | Onboarding pulito con enum R18 sigillato |
| **Contenuti user** | 2 chat_messages, 0 market_listings, 111 inventory items | Nessuna storia significativa persa |
| **Time-in-game** | Ranking, leaderboard, PvP ELO | Baseline pulita per stagioni post-R18 |
| **Rischio legale** | **Nessuno** (0 collections premium/billing) | GDPR simple |
| **Rischio player reali** | **Nessuno** (0 real domain users) | Fresh start è env cleanup |

### Interazione con drift R18.1

Il drift R18.1 (1177 adv senza class_slug/grade, 369 guilds senza max_roster_cap/r18_beta_opt_in) **verrebbe automaticamente risolto** da un reset controllato:
- Se reset ricrea starter roster: nuovi adv nascono con class_slug valido
- Se reset ricalcola max_roster_cap: 100% delle guild avrà il field
- Se reset resetta r18_beta_opt_in a False: 100% coverage

**Conclusione preliminare**: R18.1.3 backfill puntuale sarebbe **obsoleto** post-reset. Da confermare in §16 P0-14.

### Preview raccomandazioni PM

1. **Scope**: consigliato S3 (reset solo guild test) come dry-run, S1 (reset tutte) come go finale — nessun rischio real player.
2. **Archive pattern**: consigliato **Opzione B** (sibling collections `<original>_r18_archive`) — restore semplice, storage limitato (~50MB stimati), zero mongodump esterno.
3. **Timing**: post-reset welcome banner only (no pre-announcement — nessun player attivo da avvisare).
4. **Warning `seed_round5`**: registrato in §11 come `known_non_blocking_warning`. Riverifica post-reset.
5. **R18.3d**: resta PAUSED anche post-reset finché PM non decide se ancora rilevante (metadata append-only su catalog resta valido).

### Preview counting §16

| Priority | Domande |
|---|---|
| P0 (pre-reset) | 8 |
| P1 (pre-dry-run) | 5 |
| P2 (comunicazione) | 3 |
| P3 (cleanup post-reset) | 4 |
| **TOTALE** | **20** |

---

## §2 · Dati da preservare obbligatoriamente

**Filosofia PM**: preserve = "il player deve poter riconoscere la propria identità e continuità di account dopo il reset".

| Collection | Field | Motivazione preserve | Player-visible? |
|---|---|---|---|
| **`users`** | INTERA collection (id, email, password_hash, created_at, is_admin, is_test, updated_at, refresh_token_hash, ecc.) | Account login (JWT auth invariante). Cancellare o modificare = logout forzato = perdita di trust. | Sì (email, username) |
| **`refresh_tokens`** | INTERA collection (1722 doc) | Session continuity. Se azzerati, tutti i player devono re-login. Accettabile ma richiede warning nel banner. | Indirettamente |
| **`login_attempts`** | INTERA collection (3 doc) | Anti-brute-force history. Nessuna reason per cancellare. | No |
| **`password_reset_tokens`** | INTERA collection (5 doc) | Reset flow in corso. Non cancellare token attivi. | No |
| **`guilds`** | `_id`, `id`, `owner_user_id`, `name`, `public_id`, `created_at`, `updated_at`, `email` (se presente), `is_test`, `is_grandfathered`, `is_demo_opponent`, `is_test_artifact` | Identità gilda: name + owner binding. Grandfathered/demo/artifact flags per tag routing post-reset. | Sì (name) |
| **`audit_log`** | INTERA collection (11704 doc) | Historical audit trail (GDPR/compliance). Non cancellare mai — solo appendere. | No |
| **`audit_logs`** | INTERA collection (143 doc, sibling) | Come sopra. | No |
| **`audit_events`** | INTERA collection (37 doc) | R18.1/R18.3a/R18.3c/R18.3a.2/ecc. history events. | No |
| **`adventurer_classes`** | INTERA collection (18 doc) | Catalog seed. Sealed by R18.3a + R18.3a.1. Non toccare. | Sì (via API) |
| **`adventurer_traits`** | INTERA collection (41 doc) | Catalog trait pool R6B/R14. | Sì (via API) |
| **`items`** | INTERA collection (178 doc) | Item catalog. Sealed. | Sì (via API) |
| **`item_sets`** | INTERA collection (3 doc) | Catalog. Sealed. | Sì |
| **`enchants`** | INTERA collection (13 doc) | Catalog. | Sì |
| **`recipes`** | INTERA collection (5 doc) | Crafting catalog. | Sì |
| **`races`** | INTERA collection (50 doc) | Race catalog. | Sì |
| **`talent_tree_definitions`** | INTERA collection (540 doc) | R18.2 pilot placeholder. Feature-flagged OFF. Non toccare. | No (double-gated) |
| **`achievements_catalog`** | INTERA collection (110 doc) | Catalog def. Non cancellare. | Sì (via API) |
| **`class_specializations`** | INTERA collection (33 doc) | R16 specializations catalog. | Sì |
| **`dungeons`** | INTERA collection (24 doc) | Dungeon catalog. Sealed. | Sì |
| **`raid_dungeons`** | INTERA collection (3 doc) | Raid catalog. | Sì |
| **`world_boss_catalog`** | INTERA collection (1 doc) | R16.3 world boss catalog. | Sì |
| **`world_continents`** | INTERA collection (8 doc) | R16.3 continents catalog. | Sì |
| **`continent_event_catalog`** | INTERA collection (12 doc) | Continent events catalog. | Sì |
| **`continent_resource_catalog`** | INTERA collection (8 doc) | Continent resources catalog. | Sì |
| **`legendary_recipe_catalog`** | INTERA collection (6 doc) | R16.3 legendary forge catalog. | Sì |
| **`legendary_items_catalog`** | INTERA collection (6 doc) | Catalog. | Sì |
| **`arfus_technology_catalog`** | INTERA collection (10 doc) | R16.3 Arfus tech catalog. | Sì |
| **`guild_specialization_catalog`** | INTERA collection (6 doc) | R16.3 spec catalog. | Sì |
| **`narrative_routes`** | INTERA collection (5 doc) | R16.3 Phase 8 stables narrative catalog. | Sì |
| **`mount_catalog`** | INTERA collection (9 doc) | R16.3 Phase 8 mount catalog. | Sì |
| **`counter_tags`** | INTERA collection (1 doc) | System counter. | No |
| **`guild_site_income_config`** | INTERA collection (1 doc) | System config. | No |

**Totale preserve**: 30 collections (catalog + auth + audit + user).

### Sotto-condizioni preserve su `guilds`

Anche se l'INTERA collection `guilds` è preservata come identità, i FIELD che vanno resettati sono elencati in §3. Preserve fields per doc guild:
- `_id`, `id`, `public_id` (identity)
- `owner_user_id` (account link)
- `name` (player-facing identity, non modificare mai)
- `created_at` (storico)
- `email` (owner backref)
- Flag tag: `is_test`, `is_test_artifact`, `is_grandfathered`, `is_demo_opponent`
- `updated_at` (updated a reset time, non azzerato)

---

## §3 · Dati probabilmente da resettare (candidate, non decisione)

**Reset semantic**: append a valore starter/default, MAI hard delete del field. Il documento parent (guild/user) resta esistente.

| Collection | Field | Reset value proposto | Rationale |
|---|---|---|---|
| **`guilds`** | `level` | `1` | Starter level |
| `guilds` | `gold` | `100` | Starter gold (match onboarding) |
| `guilds` | `reputation` | `0` | Fresh reputation |
| `guilds` | `current_roster_size` | `0` (dopo reset adventurers) o `5` (dopo starter regen) | Ricomputed post-reset |
| `guilds` | `max_roster_cap` | ricomputato via formula R18.1 (`5 + guild_level*5` o simile) | Ripristino coerenza R18.1 |
| `guilds` | `resources` (se dict) | starter values | Fresh economy |
| `guilds` | `raids_completed_count`, `raids_victory_count`, `max_raid_score`, `last_raid_completed_at`, `max_team_power_ever` | 0/0/0/null/0 | Fresh raid stats |
| `guilds` | `r18_beta_opt_in` | `false` | Ricomputato (fix drift R18.1 test_12) |
| `guilds` | `r18_roster_cap_computed_at` | ISO now (ricomputato) | Reset tracking |
| **`adventurers`** | **INTERA collection** — reset scope da decidere | Vedi Opzione A/B/C in §8 | 3302 doc + 1177 drift |
| **`inventory_items`** | INTERA collection (111 doc) | Archive + delete o azzeramento? | Post-adventurer decision |
| **`equipped_items`** | INTERA collection (20 doc) | Archive + delete o azzeramento? | Post-adventurer decision |
| **`class_halls`** | INTERA collection (1673 doc) | Reset xp/progression, preserve enrollment ID? | Da decidere |
| **`achievement_progress`** | INTERA collection (1686 doc) | Archive; reset counters a 0 | Fresh achievement chase |
| **`granted_rewards`** | INTERA collection (0 doc) | Nothing to reset | — |
| **`squads`** | INTERA collection (2 doc) | Archive + delete | Squad ricreata post-reset |
| **`expeditions`** | INTERA collection (17 doc) | Archive + delete | Fresh expedition history |
| **`expedition_members`** | INTERA collection (45 doc) | Archive + delete | Cascade |
| **`raids`** | INTERA collection (1 doc) | Archive + delete | Fresh raids |
| **`raid_participants`** | INTERA collection (20 doc) | Archive + delete | Cascade |
| **`recruitment_offers`** | INTERA collection (255 doc) | Cache reset (nessun archive necessario) | Volatile cache |
| **`shop_daily_offers`** | INTERA collection (18 doc) | Cache reset | Volatile daily |
| **`chat_messages`** | INTERA collection (2 doc) | Archive + delete | Fresh chat |
| **`consortiums`** | 0 doc — nothing to reset | — | — |
| **`consortium_members`** | 0 doc | — | — |
| **`guild_specialization_choice`** | INTERA collection (4 doc) | Reset choice → null (o archive) | Fresh spec |
| **`guild_trade_pacts`** | INTERA collection (1 doc) | Archive + delete | Fresh pacts |
| **`guild_structures`** | INTERA collection (421 doc) | Reset a starter set | Fresh territory |
| **`guild_arfus_research_orders`** | 0 doc | — | — |
| **`guild_arfus_technologies`** | 0 doc | — | — |
| **`guild_site_income_ledger`** | INTERA collection (14 doc) | Archive | Ledger continua? |
| **`guild_pvp_stats`** | 0 doc | — | — |
| **`guild_world_presence`** | INTERA collection (6 doc) | Reset (nessun mount ownership post-reset) | Fresh world |
| **`guild_mount_ownership`** | INTERA collection (2 doc) | Preserve o archive? — cosmetico earned | **DECIDERE** (Q P2-3) |
| **`narrative_rewards_unlocked`** | INTERA collection (1 doc) | Preserve o archive? — cosmetico | **DECIDERE** (Q P2-3) |
| **`narrative_route_completions`** | 0 doc | — | — |
| **`pvp_battles`** | 0 doc | — | — |
| **`pvp_matches`** | 0 doc | — | — |
| **`pvp_challenge_cooldowns`** | 0 doc | — | — |
| **`pvp_seasons`** | INTERA collection (19 doc) | Archive; nuova season 20 | Fresh season |
| **`pvp_season_leaderboards`** | INTERA collection (36 doc) | Archive; nuova season | Storico read-only |
| **`pvp_defense_teams`** | INTERA collection (3 doc) | Reset (adventurer refs invalidati) | Cascade |
| **`pvp_cosmetics_unlocked`** | INTERA collection (5 doc) | Preserve (cosmetico earned, non-P2W) | **RACCOMANDATO PRESERVE** |
| **`continent_leaderboard_snapshots`** | INTERA collection (3 doc) | Archive; nuova stagione | Fresh leaderboard |
| **`continent_event_instances`** | INTERA collection (1 doc) | Reset | — |
| **`seasons`** | INTERA collection (1 doc) | Archive; nuova season | — |
| **`season_participations`** | INTERA collection (14 doc) | Archive | Storico |
| **`season_rewards`** | INTERA collection (4 doc) | Archive | Storico |
| **`world_boss_events`** | INTERA collection (4 doc) | Archive | Fresh boss |
| **`legendary_forge_crafting_orders`** | 0 doc | — | — |
| **`legendary_forge_pity_counters`** | 0 doc | — | — |
| **`legendary_item_instances`** | 0 doc | — | — |
| **`resource_gathering_missions`** | 0 doc | — | — |
| **`market_listings`** | 0 doc | — | — |
| **`career_history`** | 0 doc (embedded in adventurers) | — | — |
| **`adventurer_talent_progress`** | 0 doc (R18.2 placeholder) | — | Nothing to reset |
| **`tester_tool_snapshots`** | INTERA collection (14 doc) | Archive | Dev-only |
| **`guild_xp_daily_cap_tracker`** | INTERA collection (10 doc) | Reset | Volatile |

**Totale reset candidate**: 46 collections (di cui ~15 hanno 0 doc — nothing to reset).

**Conteggio doc reset totale stimato**: ~7500 doc (3302 adv + 1686 achievement + 1673 class_halls + 421 structures + 255 recruit + ...).

---

## §4 · Dati da archiviare (proposta pattern)

### Opzioni

| Opzione | Descrizione | Pro | Contro |
|---|---|---|---|
| **A** — mongodump JSON dump | Dump completo pre-reset in `/app/memory/backups/r18_reset0_prestart/` (BSON + JSON) | Standard mongo tool, restore trivial via `mongorestore` | File esterni, no online query, ~50-100MB storage |
| **B** — Sibling collections `<orig>_r18_archive` | Nuova collection `adventurers_r18_archive` (copy), `expeditions_r18_archive`, ecc. Aggiungi `snapshot_at` + `archive_reason=R18.Reset.0` + `restore_ref` a ogni doc archiviato. | Query online del legacy, restore selettivo, no external files | Raddoppia storage (temporaneamente), namespace clutter |
| **C** — Clone in DB separato | Clone `orbus_db_v2` → `orbus_db_v2_pre_reset_snapshot` | Isolamento massimo, restore = renaming DB | Difficile query cross-DB, gestione connessione doppia |

### Raccomandazione tecnica (non vincolante)

**Opzione B** con retention 90 giorni:
- Restore semplice: `db.adventurers.insertMany(await db.adventurers_r18_archive.find({}).toArray())`
- Nessuna dipendenza da tool esterni (mongodump)
- Consente diagnostics live post-reset (es. `db.adventurers_r18_archive.count({class_slug: null})` per verificare drift historic)
- Storage estimate: ~50MB (7500 doc, mediamente 6KB ciascuno)
- Rotation policy: dopo 90 giorni, dump JSON e drop collection

### Manifest archive (proposta)

Ogni collection archiviata riceve un manifest JSON in `/app/memory/backups/r18_reset0_prestart/manifest.json`:
```json
{
  "round": "R18.Reset.0",
  "snapshot_at": "2026-07-XX",
  "archive_pattern": "B",
  "collections": [
    {"name": "adventurers", "doc_count": 3302, "archive_name": "adventurers_r18_archive", "checksum": "..."},
    ...
  ],
  "retention_days": 90,
  "restore_command_template": "db.<name>.insertMany(await db.<archive_name>.find({}).toArray())"
}
```

---

## §5 · Dati da NON toccare (invariant sui round successivi)

**Zero read, zero write, zero query** durante R18.Reset.0 e reset esecuzione:

1. **`adventurer_classes`** (18 doc) — catalog sealed R18.3a + R18.3a.1 role_placeholder + R18.3a.2 filter
2. **`items`** + **`item_sets`** + **`enchants`** + **`recipes`** (199 doc totali) — catalog seed
3. **`talent_tree_definitions`** (540 doc) — R18.2 pilot placeholder (feature-flagged OFF, double-gate)
4. **`achievements_catalog`** (110 doc) — catalog def
5. **`adventurer_traits`** (41 doc) — trait pool catalog R6B/R14
6. **`class_specializations`** (33 doc) — R16 spec catalog
7. **`dungeons`** (24 doc) + **`raid_dungeons`** (3 doc) — dungeon catalog
8. **`world_boss_catalog`**, **`world_continents`**, **`continent_*_catalog`**, **`legendary_*_catalog`**, **`arfus_technology_catalog`**, **`guild_specialization_catalog`**, **`narrative_routes`**, **`mount_catalog`**, **`races`** — R16.3 catalogs
9. **Enum backend**:
   - `VALID_ROLES=("Tank","DPS","Healer")` in `admin/services.py`
   - `primary_stat` fields (strength/agility/intellect/endurance/faith)
   - `base_*` stat fields
10. **Feature flags**:
    - `R18_REWORK_ENABLED=false`
    - `R18_TALENT_ENGINE_ENABLED=false` (double-gate R18.2)
11. **Audit log storico** (`audit_log`, `audit_logs`, `audit_events` — 11884 doc totali) — MAI cancellare, solo appendere. Storicità delle round R18 (R18.1, R18.1.2, R18.2, R18.3a, R18.3a.1, R18.3a.2, R18.3b, R18.3b.1, R18.3c) preservata.
12. **Guard R18.1.2 whitelist** in `expeditions/services.py` — dispatch validity per hidden classes preservata.
13. **27 slug candidati registry** (12 classi seedate + 15 candidate memory-only) — preservati come registry.
14. **`round183b1_stat_role_enum_reconciliation_matrix.md/.json`** — PM decision C.2+R3 sealed.
15. **R18.3d mapping registry** (PAUSED) — non touch.

---

## §6 · Impatto utenti reali vs test

### Segmentation query (read-only)

```python
async for r in db.guilds.aggregate([
    {'$lookup': {'from': 'users', 'localField': 'owner_user_id',
                 'foreignField': 'id', 'as': 'owner'}},
    {'$unwind': {'path': '$owner', 'preserveNullAndEmptyArrays': True}},
    {'$project': {'email': {'$toLower': {'$ifNull': ['$owner.email', '']}},
                  'is_demo_opponent': 1, 'is_test_artifact': 1, ...}},
])
```

### Risultati verificati (2026-07-04T21:42Z)

| Segment | Count | % Total |
|---|---|---|
| **`is_test_artifact=true`** | 669 | 99.6% |
| **`is_demo_opponent=true`** | 3 | 0.4% |
| **`is_grandfathered=true`** | 7 | 1.0% |
| **Owner email `@orbus.test`** | 280 | 41.7% |
| **Owner email `@orbus.preview`** | 3 | 0.4% |
| **Owner email REAL domain** | **0** | **0%** |
| **Orphan (owner ID senza user)** | 389 | 57.9% |

### Conclusione

**Zero player reali** in produzione. Tutte le 672 guild sono classificate come test artifact/demo AI/orphan. Il reset è **operativamente un test env cleanup con effetto zero su player veri**. Nessun rischio legale (0 collezioni premium/billing/subscription).

### 4 Scope alternative da proporre PM

| Scope | Descrizione | Rischio | Fattibilità immediata |
|---|---|---|---|
| **S1 — Reset totale** | Reset tutte le 672 guild (test + demo + orphan + grandfathered) | Nessuno (0 real users) | ✅ Immediata |
| **S2 — Reset solo reali** | Reset solo guild con owner email REAL — sarebbe 0 guild | N/A | 0 target |
| **S3 — Reset solo test** | Reset solo `@orbus.test`/`@orbus.preview` (283 guild) | Nessuno | ✅ Immediata |
| **S4 — Reset opt-in** | UI per guild owner: "Reset now"/"Keep as-is" | Basso | Richiede UI, timing lungo |

**Raccomandazione tecnica** (non vincolante): S1 (reset totale), dato che 0 real users. Ma se PM vuole trattare `is_grandfathered=true` (7 guild) con rispetto (badge Founder, ecc.), può escludere solo quelle → S1'.

---

## §7 · Impatto leaderboard

### Stato attuale

- **`pvp_seasons`** — 19 doc (una attiva)
- **`pvp_season_leaderboards`** — 36 doc (rank per adventurer per season)
- **`pvp_cosmetics_unlocked`** — 5 doc (cosmetico earned)
- **`continent_leaderboard_snapshots`** — 3 doc
- **`seasons`** — 1 doc (season globale)
- **`season_participations`** — 14 doc
- **`season_rewards`** — 4 doc

### Opzioni post-reset

| Opzione | Descrizione | Player experience |
|---|---|---|
| **L.a** — Azzera tutto | Delete + no archive | Ranking = 0 all. No hall of fame. |
| **L.b** — Archive + fresh season | Archive → nuova season 20 (nuovi rank) | Storico read-only accessible. Fresh season |
| **L.c** — Preserve cosmetici, reset ranking | Preserve `pvp_cosmetics_unlocked`, archive rest | Player mantiene badges. Ranking numerico azzerato |
| **L.d** — Nuova era: preserve solo cosmetici + timestamp | Preserve cosmetici. Rank reset. Timestamp nuova era. | Migliore player experience |

**Raccomandazione**: **L.d** (preserve cosmetici + timestamp nuova era). Piccola compensazione simbolica per ogni pvp_cosmetics_unlocked.

---

## §8 · Impatto adventurers / items / resources

### Adventurers (3302 doc)

3 opzioni tecniche:

| Opzione | Descrizione | Complexity | Reversibility |
|---|---|---|---|
| **A.a** — Delete hard + regen | Delete 3302 doc. Regen 5-10 starter per guild via seed_round5. | Bassa | ❌ Solo via archive |
| **A.b** — Archive + regen | Copy in `adventurers_r18_archive` (3302 doc). Delete original. Regen starter. | Media | ✅ Restore via archive |
| **A.c** — Reset in-place | Ogni adv: `level=1, xp=0, equipment=[], gold_earned=0` ma `class_slug` preservato (i 496 R18.3c restano paladin/cacciatori) | Media | ✅ Ma solo campo-level |

**Raccomandazione**: **A.b** (archive + regen). Preserva la storia dei 496 orphan migrati (utile per debug post-mortem), permette rollback pulito, e "fresh start" è più semantico che "reset di campi".

### Items in inventory (111 doc)

| Opzione | Descrizione |
|---|---|
| **I.a** — Delete + regen starter items | Reset inventory. Starter items via seed. |
| **I.b** — Archive + regen | Copy in `inventory_items_r18_archive`. Delete. Regen. |
| **I.c** — Preserve | Nessun reset. Ma sarebbero "orfani" senza adventurers → problemi. |

**Raccomandazione**: **I.b** (cascade da A.b).

### Equipped items (20 doc)

Cascade da adventurers: se A.b, allora anche equipped items archiviati + regen 0.

### Resources gathered

Se `guilds.resources` è un dict embedded, reset a valori starter.

---

## §9 · Impatto R18 migrations già fatte

| Round | Cosa succede se reset guild + regen adventurers |
|---|---|
| **R18.1** (grade backfill, max_roster_cap, r18_beta_opt_in) | I 2125 adv con grade+class_slug → archiviati. Nuovi starter regen avranno automaticamente grade + class_slug valido (regeneration usa `filter_safe_class_pool` post-R18.3a.2 patch = 11 legacy classes valide). `max_roster_cap` ricomputato. `r18_beta_opt_in` reset a false. **Drift R18.1 automaticamente risolto**. |
| **R18.1.2** (guard whitelist expedition) | Codebase invariato. Guard resta valida per le 2 hidden classes. |
| **R18.2** (talent pilot 540 placeholder) | `talent_tree_definitions` (540 doc) intatti. `adventurer_talent_progress` (0 doc) invariato. |
| **R18.3a** (hidden classes catalog) | 2 hidden classes restano in `adventurer_classes`. `is_playable=false` + `migration_target_only=true` invariati. |
| **R18.3a.1** (role placeholder TBD) | Catalog invariato. `role="TBD"` + `role_placeholder=true` + `role_pm_decision_pending=true` restano. |
| **R18.3c** (496 orphan migrati) | Gli adventurer migrati sono archiviati (A.b). La migration è "storicizzata" ma non live. Post-reset, i nuovi starter usano solo le 11 legacy classes. **Ne consegue**: se PM vuole preservare la migration decision (paladin/cacciatori come classi player), deve regen usando tutti i 13 pool classes (legacy + 2 hidden se `is_playable=true`) OPPURE tenere le 2 hidden sole per admin-only. Da decidere in Q P0-6. |
| **R18.3a.2** (recruitment filter) | Codebase invariato. Filtro `is_playable != false` resta attivo. Post-reset, il pool recruitment è 11 legacy. |
| **R18.3b.1** (stat/role reconciliation C.2+R3) | Sealed. Memory file. Nessun impatto DB. |
| **R18.3d** (mapping registry) | PAUSED. Nessun impatto (mai applicato). |

### Impact riassunto §9

- ✅ R18.1 drift → risolto automaticamente
- ✅ Catalog seeded → tutti intatti
- ⚠️ R18.3c decision → sto **archiviando** la migration ma il rationale della decisione (paladin+cacciatori come target canonici) resta valido nel design intent. Verifica Q P0-6.

---

## §10 · Impatto achievements

### Stato attuale

- **`achievements_catalog`** — 110 doc (catalog def, non toccare)
- **`achievement_progress`** — 1686 doc (progress user)
- **`pvp_cosmetics_unlocked`** — 5 doc (cosmetici earned)
- **`narrative_rewards_unlocked`** — 1 doc (narrative rewards)
- **`guild_mount_ownership`** — 2 doc (mount earned)

### Opzioni post-reset

| Opzione | Descrizione |
|---|---|
| **Ach.a** — Reset totale | Archive achievement_progress. Rest a 0. Nessuna hall of fame. |
| **Ach.b** — Hall of Fame preserve | Archive achievement_progress. Aggiungi `hall_of_fame_earned=[<slug>]` a `guilds` per achievement top-tier. |
| **Ach.c** — Prime-mover bonus | Reset progress. Aggiungi trait/badge cosmetico ai player pre-reset (`badge_founder`). |
| **Ach.d** — Combo b+c | Hall of Fame + Founder badge |

**Raccomandazione**: **Ach.d** — offre continuità simbolica sia via hall of fame sia via badge. Nessun P2W. Da approfondire in Q P0-8.

---

## §11 · Impatto recruitment / starter_backfill / seed_round5 warning

### Warning tracked

**Warning testuale** (registrato al backend startup):
```
2026-07-04 21:31:14 - orbus.seed_round5 - WARNING - starter backfill failed: 'base_strength'
2026-07-04 21:31:14 - orbus.seed_round5 - INFO - ROUND 5 boot: ... starter_backfill=0 (idempotent)
```

**Status**: **`known_non_blocking_warning`**

### Analisi

- `seed_round5.starter_backfill` è routine di boot che tenta di completare gli starter adventurers per gilde legacy che mancano di roster minimo.
- La routine legge classi da `adventurer_classes` con un pool internal che **non filtra `is_playable`** → include le 2 hidden classes R18.3a senza `base_*` fields.
- Alla lettura `klass["base_strength"]`, KeyError → catturato da `try/except` → warning + `starter_backfill=0` come outcome (silent no-op).
- **Player-facing impact: nullo** (nessun crash, nessun leak). Solo log warning.

### Verifica: è ancora rilevante post-reset?

Dipende dall'esito reset:

| Scenario post-reset | Warning ancora rilevante? |
|---|---|
| Reset ricrea starter roster via `seed_round5.starter_backfill` all'onboarding | ✅ Sì, warning si ripresenterà |
| Reset elimina la necessità di starter_backfill (nuovo generator dedicato R18.Reset.1 onboarding) | ❌ No, warning obsoleto |
| Reset mantiene `seed_round5.starter_backfill` come routine di boot | ✅ Sì, warning si ripresenterà |

### Raccomandazione tecnica

**Solo diagnostica ora**. Post-reset, riverifica:
- Se il warning persiste, considera patch simmetrica a `seed_round5` (filtra `is_playable`) come R18.3a.3.
- Se il warning è obsoleto (starter path diverso), scarta.

---

## §12 · Piano dry-run

### Design (non implementato)

Script `/app/backend/app/scripts/r18_reset0_dry_run.py` (da creare in round successivo, **NON in R18.Reset.0**).

Struttura:
1. **Input**: `--scope=S1|S2|S3|S4`, `--verbose`
2. **Fase 1 — Read snapshot**: `db.list_collection_names()` + `count_documents()` per ogni collection reset candidate. Stampa tabella pre-reset.
3. **Fase 2 — Simulazione write**: per ogni collection reset candidate, genera JSON diff `{before: {level: 5, gold: 500, ...}, after: {level: 1, gold: 100, ...}}` senza applicare `update_many`.
4. **Fase 3 — Archive plan**: stampa comandi archive che sarebbero eseguiti (Opzione B: `db.adventurers.aggregate([{$out: 'adventurers_r18_archive'}])`).
5. **Fase 4 — Metrics post-simulation**: predice count post-reset (0 per adventurers, 5×672=3360 per starter, ecc.).
6. **Fase 5 — Report**: dump di `/app/memory/backups/r18_reset0_dry_run_report.json` con diff completo.

### Fixture di test consigliata

- 1 guild sintetica in DB test (`is_test_artifact=true, name="RESET_TEST_FIXTURE"`)
- 3 adventurers sintetici linked
- 1 expedition sintetica
- 1 achievement progress row

Il dry-run deve dimostrare:
- Fixture correttamente riconosciuta come reset candidate
- Nessuna scrittura reale al DB durante dry-run
- Diff JSON coerente
- Idempotenza: 2 dry-run identici → stesso output

### Timing suggerito

Dry-run **dopo** che PM risponde a §16 (P0 answers). Non implementare finché scope non è definito.

---

## §13 · Piano rollback

### Snapshot pre-reset

**Path**: `/app/memory/backups/r18_reset0_prestart/`

**Contenuto (Opzione B archive pattern)**:
- Sibling collections `<name>_r18_archive` in DB (già gestite da script apply)
- **Manifest JSON** in `/app/memory/backups/r18_reset0_prestart/manifest.json`:
  ```json
  {
    "round": "R18.Reset.0",
    "snapshot_at": "2026-07-XX",
    "archive_pattern": "B",
    "scope": "S1|S2|S3|S4",
    "collections": [
      {"name": "adventurers", "doc_count_pre": 3302, "archive_name": "adventurers_r18_archive", "checksum_sample": "..."},
      {"name": "guilds", "doc_count_pre": 672, "archive_name": "guilds_r18_archive", "checksum_sample": "..."},
      ...
    ],
    "retention_days": 90,
    "reset_script": "app/scripts/r18_reset0_apply.py",
    "rollback_script": "app/scripts/r18_reset0_rollback.py"
  }
  ```

### Comando restore

Rollback script (da creare in R18.Reset.1 apply round, **NON in R18.Reset.0 planning**):
```python
# app/scripts/r18_reset0_rollback.py
async def rollback():
    manifest = load_manifest()
    for col in manifest["collections"]:
        # 1. Empty current live collection
        await db[col["name"]].delete_many({"archived_at_reset": True})  # marker
        # 2. Copy from archive back to live
        docs = await db[col["archive_name"]].find({}).to_list(None)
        if docs:
            await db[col["name"]].insert_many(docs)
    # 3. Emit rollback audit event
    await emit_audit("R18_RESET0_ROLLED_BACK", metadata=...)
```

### Time-to-rollback

Stimato: **< 60 secondi** per 7500 doc totali (mongo bulk insert è fast).

### Retention window

**Proposta**: 90 giorni. Dopo, dump JSON esterno + drop collections `_r18_archive` per storage cleanup.

### Testing rollback

Su fixture (1 guild sintetica). Il test verifica:
1. Pre-reset count == pre-rollback count (identici post-rollback)
2. Zero diff JSON tra doc live e doc archive (post-rollback)
3. Audit event `R18_RESET0_ROLLED_BACK` emesso
4. Idempotenza: 2 rollback consecutivi → 2° è no-op

---

## §14 · Comunicazione UI/player

### Testo candidato IT (byte-exact, non deploy)

#### Opzione A — Post-reset welcome only (raccomandata)

**Component name** (proposta): `ResetWelcomeBannerR18Reset0.jsx`

**Testo**:
- **Titolo**: `Benvenuto nella Nuova Era di Orbus!`
- **Corpo**: `Il tuo mondo è stato ridefinito. La tua gilda "{guild.name}" inizia una nuova avventura con classi canoniche, obiettivi rinnovati e progressione bilanciata. Il tuo nome, la tua storia, il tuo ruolo di Master restano tuoi. Tutto il resto è pronto per essere riscritto.`
- **CTA**: `Inizia la nuova avventura` (dismiss)
- **Persistenza**: dismissibile (analog. a R18.3c banner)
- **Endpoint dismiss**: `POST /api/guilds/me/reset0-banner/dismiss` (nuovo, symmetric a R18.3c)
- **Endpoint read**: `GET /api/guilds/me/reset0-banner` (nuovo)

#### Opzione B — Pre-reset announcement (opzionale, sconsigliata dato 0 real players)

Se PM decide pre-announcement:
- **Titolo**: `Prepara la tua gilda per la Nuova Era`
- **Corpo**: `Orbus si rinnova: in arrivo un fresh start con classi canoniche, mappe rinnovate, sistemi di progressione bilanciati. Il tuo nome, il tuo account, il tuo ruolo di Master restano tuoi. Tutto il resto rinasce.`
- **CTA**: `Scopri di più` (link a changelog) + `OK, sono pronto` (opt-in flag `r18_reset0_optin=true`)

### Timing raccomandato

- **Pre-reset**: skip (nessun player attivo da avvisare)
- **Post-reset**: banner welcome, dismissibile, persistente fino a click

### Localization

Italiano only per R18.Reset.0. Localizzazione EN/altre lingue in round successivo se necessario.

### Compensation cosmetica (dettaglio Q P0-8)

- **Founder badge**: cosmetico UI, non-P2W, `badge="founder_r18"` in `pvp_cosmetics_unlocked` — segna "hai giocato prima della Nuova Era"
- **Titolo gilda**: `title="prima_era"` visibile in profilo — segno di longevità
- **Hall of Fame**: link nel banner welcome a `hall_of_fame_r18` (nuova view) con top achievement pre-reset

---

## §15 · Rischi legali / account / premium

### GDPR compliance

**Rischi**: **nessuno operativo**, dato che:
- 0 collezioni `premium`, `subscription`, `billing`, `payment`, `transaction`, `purchase`
- 0 user con email reale (solo `@orbus.test`/`@orbus.preview`)
- 0 dati sensibili al di fuori di email + password_hash (già memorizzata come hash bcrypt)
- Backup archive collections `_r18_archive` mantengono lo storico (right-to-be-forgotten se richiesto in futuro, cancellare manualmente il singolo doc dall'archive)

### Consumer rights

**Comunicazione trasparente**: banner welcome §14 dichiara esplicitamente "il tuo nome resta tuo, tutto il resto è ridefinito". Nessun claim ingannevole.

### Backup retention GDPR

**Standard**: 30-90 giorni. Proposta R18.Reset.0: **90 giorni** per rollback + archive query, poi dump esterno.

### Subscription attive

**Nessuna**. `pvp_cosmetics_unlocked` (5 doc) sono cosmetici earned via gameplay, non paid.

### Testing con demo account

Prima dell'apply reale, dry-run + rollback test su fixture (§12, §13).

### Riepilogo rischi

| Categoria | Rischio | Mitigazione |
|---|---|---|
| **Legal (GDPR)** | Nessuno | 0 dati sensibili, archive preservato |
| **Consumer** | Nessuno | 0 real users |
| **Financial** | Nessuno | 0 premium/billing |
| **Reputational** | Basso | Comunicazione trasparente banner |
| **Technical (data loss)** | Basso | Archive + rollback plan |

---

## §16 · Domande PM finali

**Target**: ≥ 15
**Delivered**: **20 domande**, ordinate per priority.

### P0 — Prima di qualsiasi reset reale (8 domande)

**P0-1. Scope reset: quale approccio?**
- **A**: S1 (reset tutte le 672 guild — nessun rischio real user)
- **B**: S3 (reset solo `@orbus.test`/`@orbus.preview` = 283 guild)
- **C**: S1 escludendo `is_grandfathered=true` (7 guild) — badge Founder alle 7 preservate
- **D**: Altro
- **Raccomandazione tecnica e1_dev** (non vincolante): **A** (S1 completo), poiché 0 real users. Se vuoi trattare i 7 grandfathered con rispetto, aggiungi `C`.

**P0-2. Cosa preservare oltre a guild.name?**
- **A**: Solo `name` + `owner_user_id` + `created_at` + tag flags
- **B**: Come A + guild `level` (mantieni progressione livello gilda)
- **C**: Come B + `reputation`
- **D**: Come A + achievement hall of fame + cosmetici
- **Raccomandazione**: **D** — preserve identità simbolica (livello + achievement history + cosmetici pvp) senza P2W

**P0-3. Cosa fare con adventurers (3302)?**
- **A**: A.a (delete hard + regen 5 starter per guild)
- **B**: A.b (archive in `adventurers_r18_archive` + regen)
- **C**: A.c (reset in-place, preserve class_slug — i 496 R18.3c restano paladin/cacciatori)
- **Raccomandazione**: **B** (archive + regen). Preserva history, rollback safe, fresh semantico.

**P0-4. Cosa fare con items/equipment (131 doc totali)?**
- **A**: Archive tutto (cascade da adventurers)
- **B**: Delete hard (cascade)
- **C**: Preserve inventory guild-level (items non-equipped)
- **Raccomandazione**: **A** (archive cascade da adventurers). Restore semplice se rollback.

**P0-5. Reset scope adventurers class_slug: come regen?**
- **A**: Solo 11 legacy classes (post-R18.3a.2 filter, senza hidden)
- **B**: 13 classes (11 legacy + 2 hidden, se PM decide di rendere `cacciatore_di_mostri`/`cacciatore_del_vuoto` playable via `is_playable=true` post-reset)
- **C**: Solo per casi migration critical, 13 classes; per starter, 11 legacy
- **Raccomandazione**: **A** — safest. Le 2 hidden restano seedate ma non pescabili finché PM non decide R18.3d/futuro.

**P0-6. Preservi la R18.3c migration decision post-reset?**
- **A**: No, archive completa (i 496 orphan migration si vede solo in `adventurers_r18_archive`)
- **B**: Sì, ma solo come design intent (memory file R18.3c report resta autorevole)
- **C**: Sì, e post-reset applica di nuovo il mapping su nuovi adventurers che verranno creati con class_slug legacy (rare)
- **Raccomandazione**: **B** — design intent preserved via memory, nessun re-apply necessario post-reset (nuovi adv non hanno il problema orphan legacy).

**P0-7. Come gestisci gold/resources?**
- **A**: Reset totale a starter (100 gold, 0 resources)
- **B**: Reset gold. Preserve `resources` earned da mission legacy (dubbio: valore emotivo?)
- **C**: Reset totale + starter kit R18 (100 gold + 3 starter potions + basic weapon)
- **Raccomandazione**: **C** — welcome kit è UX friendly

**P0-8. Compensation cosmetica per player pre-reset?**
- **A**: Nessuna
- **B**: Badge `founder_r18` per tutti i user pre-reset (cosmetico, non-P2W)
- **C**: Badge + titolo profilo `title="prima_era"`
- **D**: Badge + titolo + Hall of Fame view (achievement top-tier archivio read-only)
- **Raccomandazione**: **D** — massimo valore simbolico, zero costo

### P1 — Prima del dry-run (5 domande)

**P1-1. Archive pattern: A, B, o C?**
- **A**: mongodump JSON esterno
- **B**: sibling collections `_r18_archive` (Opzione raccomandata §4)
- **C**: DB clone separato
- **Raccomandazione**: **B**

**P1-2. Retention window archive?**
- **A**: 30 giorni
- **B**: 60 giorni
- **C**: 90 giorni
- **D**: 180 giorni
- **Raccomandazione**: **C** (90 giorni)

**P1-3. Cosa fare con leaderboard/season?**
- **A**: L.a (azzera tutto)
- **B**: L.b (archive + season 20 fresh)
- **C**: L.c (preserve cosmetici, reset ranking)
- **D**: L.d (nuova era: preserve cosmetici + timestamp)
- **Raccomandazione**: **D**

**P1-4. Achievement post-reset?**
- **A**: Ach.a (reset totale)
- **B**: Ach.b (Hall of Fame + badge cosmetici)
- **C**: Ach.c (prime-mover bonus)
- **D**: Ach.d (Hall of Fame + Founder badge combo)
- **Raccomandazione**: **D**

**P1-5. Chi triggera il reset?**
- **A**: Manuale via admin endpoint `POST /api/admin/r18-reset0/apply` (auth required)
- **B**: CLI script `python -m app.scripts.r18_reset0_apply --apply --scope=S1`
- **C**: Automatico a data specifica (cron-based)
- **Raccomandazione**: **B** (CLI script, come pattern R18.3c). Consenti anche admin endpoint per audit trail.

### P2 — Comunicazione player experience (3 domande)

**P2-1. Timing banner?**
- **A**: Post-reset welcome only
- **B**: Pre-reset announcement + post-reset welcome
- **C**: Pre-reset opt-in
- **Raccomandazione**: **A** (nessun player attivo pre-reset da avvisare)

**P2-2. Banner dismissibile?**
- **A**: Sì, dismiss button (come R18.3c)
- **B**: Sticky finché player non completa onboarding-2.0
- **C**: Sticky per 7 giorni poi auto-dismiss
- **Raccomandazione**: **A** (analog. R18.3c)

**P2-3. Preserve o archive cosmetici (`pvp_cosmetics_unlocked`, `guild_mount_ownership`, `narrative_rewards_unlocked`)?**
- **A**: Preserve tutti (5+2+1 doc totali)
- **B**: Archive tutti
- **C**: Preserve solo `pvp_cosmetics_unlocked`, archive rest
- **Raccomandazione**: **A** (totale 8 doc, low cost, high value simbolico)

### P3 — Cleanup tecnico post-reset (4 domande)

**P3-1. R18.1.3 drift backfill: ancora necessario?**
- **A**: No (reset ricrea tutto pulito, drift risolto by construction)
- **B**: Sì, per doc non touched dal reset (es. audit_log legacy — ma quelli non hanno bisogno di backfill)
- **Raccomandazione**: **A** — obsoleto post-reset

**P3-2. R18.3d mapping registry: applicarlo post-reset?**
- **A**: Sì, subito dopo reset (fresh baseline pulita)
- **B**: No, resta PAUSED (mapping è UI-only, non blocking)
- **C**: Sì, ma solo per admin panel debug (non player-facing)
- **Raccomandazione**: **A** o **C** — utile per admin/audit, zero cost

**P3-3. Warning `seed_round5.starter_backfill`: patchare post-reset?**
- **A**: Sì, se il warning si ripresenta (patch simmetrica a R18.3a.2 in `seed_round5`)
- **B**: No, resta obsoleto (nuovo starter path)
- **C**: Verifica prima, decide dopo
- **Raccomandazione**: **C** — riverifica post-reset. Se warning persiste, opera R18.3a.3 hotfix.

**P3-4. `adventurer_talent_progress` (R18.2 pilot, 0 doc): reset o preserve?**
- **A**: Preserve (0 doc, nothing to reset)
- **B**: N/A (nessun impatto)
- **Raccomandazione**: **B** (irrelevant)

---

## §17 · Vincoli assoluti R18.Reset.0 (rispettati)

- ✅ Zero reset reale
- ✅ Zero DB write (nemmeno index)
- ✅ Zero hard delete
- ✅ Zero codice modificato (solo memory files creati)
- ✅ Zero seed
- ✅ Zero schema migration
- ✅ Zero combat math change
- ✅ Zero reward/drop/economia/PvP/premium change
- ✅ Zero UI player-facing (banner testo solo in report §14, non deploy)
- ✅ Zero modifica account
- ✅ Zero modifica gilde live
- ✅ Zero modifica adventurers live
- ✅ Zero modifica item live
- ✅ Zero patch a `seed_round5.py` (warning registrato in §11 come non-blocking)
- ✅ Zero patch a `generator.py` (R18.3a.2 già sealed)
- ✅ Zero decisioni sigillate come definitive (20 domande PM in §16)
- ✅ Solo: lettura DB (`find`/`aggregate`) per stats + scritture in `/app/memory/r18_reset0_*.md/json`
- ✅ Feature flag `R18_REWORK_ENABLED=false` invariato
- ✅ R18.3d resta PAUSED
- ✅ R18.3a.2 sealing rispettato

---

## §18 · Firma

**R18.Reset.0 OPEN — Planning-only READY.**

*Firma: e1 main agent · 2026-07-04T21:42Z*

Attendo risposte PM alle 20 domande §16 per procedere.

**Raccomandazione ordine di risposta PM**: rispondere prima **P0-1** (scope) e **P0-3** (adventurers strategy), poiché sono i due assi che determinano il volume di lavoro downstream. Dopo P0-1+P0-3, gli altri P0 sono più facili da decidere (dipendenti dal contesto scope+adventurer).

In assenza di risposte, il sistema resta stable in modalità Opzione B implicit del PM design (nessun reset, drift R18.1 in HOLD, R18.3d PAUSED).
