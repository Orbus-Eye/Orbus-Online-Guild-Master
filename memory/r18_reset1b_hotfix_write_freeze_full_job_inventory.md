# R18.Reset.1b.hotfix.write_freeze_full — Job Inventory Snapshot

**Snapshot at**: 2026-07-05T10:08:00Z
**Purpose**: Coverage B2 per env `ORBUS_INTERNAL_JOB_FREEZE` (skip internal async jobs during apply).
**Status**: **B.0 DRAFT — awaiting PM review before B.1 patching starts.**

---

## Metodologia

Grep patterns eseguiti su `/app/backend/app/**/*.py` (escluso `tests/` e `scripts/`):
- `asyncio.create_task | asyncio.ensure_future` → **0 match** (nessun task spontaneo)
- `AsyncIOScheduler | apscheduler | BackgroundScheduler | add_job` → **0 match** (nessuno scheduler)
- `BackgroundTasks | celery | @celery` → **0 match** (nessuna coda async esterna)
- `on_event / lifespan` → **1 match** (`lifespan` ASGI in `app/core/lifespan.py`)
- `sweep | _resolve_expired | _resolve_stuck | recover_stuck | _reap_stuck` → multiple match (on-visit resolvers)

**Pattern architetturale Orbus** (autodichiarato in codice, es. `app/legendary_forge/__init__.py:6`, `app/resources/__init__.py:7`):
> "on-visit resolve (no scheduler)"

Non esistono job periodici. Ogni "job async" è invocato da:
1. **Lifespan boot** (una tantum al restart backend), oppure
2. **Route HTTP** (mutante o read-time), oppure
3. **`sweep_activities_for_guild`** chiamato da GET routes (bypass HTTP freeze potenziale).

---

## Categoria 1 — Lifespan boot seeds (⚠️ scrivono al restart backend)

Eseguiti UNA volta a ogni supervisor restart via `app/core/lifespan.py:lifespan()`. Coprire richiesto perché un restart backend mid-apply riattiva questi seeds.

| # | Job / helper | File | Righe scritte | Collezioni scritte | Include/Exclude | Motivazione |
|---|---|---|---|---|---|---|
| L1 | `run_round5_seeds_and_migrations` → `ensure_starter_roster_for_all_guilds` | `app/seeds/seed_round5.py:585` + `app/onboarding/services.py:123` | `insert_one` su `adventurers` per ogni guild sotto STARTER_TARGET (5) | **`adventurers`**, `audit_log` | **INCLUDE** | **Sospettato colpevole del drift +2** rilevato durante rollback CTRL 4. Scrive `adventurers` — collezione reset-impacted. |
| L2 | `run_all_seeds` (seed_runner) | `app/seeds/seed_runner.py:416` | Seeds vari (catalog) | `adventurer_classes`, `adventurer_traits`, `items`, `dungeons`, ... (CATALOG_INVARIANT) | **EXCLUDE** | Scrive solo catalog invariant. Non toccato dal reset. |
| L3 | `run_forge_seeds`, `run_forge_migration` | `app/seeds/seed_forge.py` | Seed forge catalog | `enchants`, `recipes`, `items` catalog | **EXCLUDE** | Catalog invariant. |
| L4 | `seed_territory_materials` | `app/seeds/seed_territory_materials.py` | Seed materiali territorio | `items` catalog | **EXCLUDE** | Catalog invariant. |
| L5 | `backfill_bound_fields_if_missing` | `app/inventory/bound.py` (importato in lifespan) | `update_many` su `inventory_items` per migrazione schema | **`inventory_items`** | **INCLUDE** | Scrive su `inventory_items` — collezione reset-impacted. Migration idempotente ma modifica documenti live. |
| L6 | `seed_signature_templates` | `app/training/seed_signature.py` | Insert `items` templates signature | `items` catalog | **EXCLUDE** | Catalog invariant. |
| L7 | `backfill_missing_signature_inventory_rows` | `app/training/seed_signature.py` | Insert `inventory_items` per signature mancanti | **`inventory_items`** | **INCLUDE** | Scrive su `inventory_items` — reset-impacted. |
| L8 | `seed_world_boss_catalog`, `seed_world_continents`, `seed_continent_event_catalog`, `seed_site_income_config`, `seed_resource_catalog`, `seed_legendary_forge_catalog`, `seed_arfus_forge_catalog`, `seed_guild_specialization_catalog`, `ensure_mount_catalog`, `ensure_narrative_routes` | `app/world_boss/`, `app/world/`, `app/world_events/`, `app/site_contracts/`, `app/resources/`, `app/legendary_forge/`, `app/arfus_forge/`, `app/guild_specialization/`, `app/stables/` | Seed catalog vari | Solo collezioni CATALOG_INVARIANT | **EXCLUDE** | Tutti catalog invariant. Nessuna scrittura su collezioni reset-impacted. |
| L9 | `seed_round12_preseason`, `seed_round12_rewards`, `seed_round12_demo_opponents`, `seed_round12_release_tester_roster`, `seed_round13a_dungeon_raid_lore`, `seed_round13a_items_lore` | `app/scripts/seed_round12_*.py`, `seed_round13a_*.py` | Seed release/lore | Mixed (verifica singolarmente) | **⚠ AMBIGUO** | `seed_round12_release_tester_roster` scrive potenzialmente su `adventurers` (test roster). **Chiedo review PM**. Altri sembrano catalog-only. |
| L10 | `run_forge_migration(db)` | `app/seeds/seed_forge.py` | Forge migration | Verificare | **⚠ AMBIGUO** | Nome "migration" suggerisce modifiche a documenti live. **Chiedo review PM**. |
| L11 | `ensure_bound_indexes`, `ensure_*_indexes` (audit, market, consortium, chat, shop, season, pvp, reward, cap_tracker, bound, indexes vari) | Vari `.services.py` | `create_index` (solo DDL) | Solo indici | **EXCLUDE** | DDL-only, nessun write documento. |

**Totale Categoria 1 INCLUDE**: **L1, L5, L7** (3 job hard-include) + **L9, L10** (2 job ambigui da rivedere con PM).

---

## Categoria 2 — On-visit resolvers (invocati da GET route via `sweep_activities_for_guild`)

**Gap architetturale principale**: le GET request passano il MaintenanceMiddleware (che blocca solo POST/PUT/PATCH/DELETE). Ma le GET route chiamano `sweep_activities_for_guild` che INVOCA resolver che SCRIVONO.

Chiamanti GET identificati (grep `sweep_activities_for_guild`):
- `app/adventurers/routes.py:91` (GET /adventurers roster list)
- `app/adventurers/routes.py:218` (GET /adventurers roster health)
- `app/guilds/routes.py:54` (GET /guilds/me)

| # | Resolver (chiamato da sweep) | File | Collezioni scritte | Include/Exclude | Motivazione |
|---|---|---|---|---|---|
| R1 | `complete_due_expeditions` | `app/expeditions/services.py` | **`expeditions`**, **`expedition_members`**, `guilds` (rewards), `adventurers` (XP), `inventory_items` (loot), audit_log | **INCLUDE** | 5 collezioni reset-impacted. Scrive massicciamente. Chiamato da GET → bypass HTTP freeze. |
| R2 | `auto_resolve_stuck_raids_for_guild` | `app/raids/recovery.py:378` | **`raids`**, **`raid_participants`**, guilds (rewards), adventurers (XP), inventory_items (loot), audit_log | **INCLUDE** | 5 collezioni reset-impacted. |
| R3 | `_resolve_expired_missions_for_guild` | `app/resources/__init__.py:402` | **`resource_gathering_missions`** (Note: `resource_missions` da problem_statement — verificare naming), guilds (rewards), audit_log | **INCLUDE** | Reset-impacted (mission collection). |

---

## Categoria 3 — On-visit resolvers (invocati direttamente da route mutanti)

Questi sono chiamati DENTRO handler HTTP mutanti (POST/PUT/DELETE) o da altre GET route. Già coperti da `MaintenanceMiddleware` (gate 5) per il POST layer, MA se invocati da GET route (che passa il middleware) diventano gap.

| # | Resolver | File | Collezioni scritte | Trigger points | Include/Exclude | Motivazione |
|---|---|---|---|---|---|---|
| D1 | `_resolve_expired_for_guild` (legendary_forge) | `app/legendary_forge/__init__.py:599` | **`guild_arfus_research_orders`** o `legendary_forge_crafting_orders`, `inventory_items` (loot), audit_log | Righe 778 (POST/GET route flow) | **INCLUDE** | Reset-impacted (inventory_items). Da verificare se anche GET route lo chiama — SAFE INCLUDE. |
| D2 | `_resolve_expired_for_guild` (arfus_forge) | `app/arfus_forge/__init__.py:599` | **`guild_arfus_research_orders`**, `inventory_items`, audit_log | Riga 617 | **INCLUDE** | Come D1. |
| D3 | `try_resolve_expired_events_for_guild` (world_boss) | `app/world_boss/__init__.py:359` | **`world_boss_events`**, `guilds` (rewards), audit_log | Riga 413 (varie route) | **INCLUDE** | Reset-impacted (world_boss_events). |
| D4 | `auto_resolve_stuck_battles_for_guild` (pvp_continental) | `app/pvp_continental/resolver.py:516` | **`pvp_battles`**, `pvp_challenge_cooldowns`, audit_log | Chiamato da `pvp_continental/services.py:541` | **INCLUDE** | Anche se `pvp_battles` non è in ARCHIVE_COLLECTIONS del reset, la battaglia scrive stat che possono drift. **SAFE INCLUDE (conservative default)**. |

---

## Categoria 4 — Onboarding route (POST /guilds create)

| # | Job | File | Collezioni | Include/Exclude | Motivazione |
|---|---|---|---|---|---|
| O1 | `ensure_starter_roster` (chiamato da POST /guilds) | `app/onboarding/services.py:71` invocato in `app/guilds/routes.py:34` | `adventurers`, `audit_log` | **EXCLUDE** (già coperto) | Chiamato DENTRO POST /guilds handler → MaintenanceMiddleware blocca la POST con 503 prima ancora che il codice del handler venga eseguito. Gate 5 già lo copre. Nessun bisogno di guard aggiuntivo. |

---

## Summary coverage decisions

| Categoria | Job totali analizzati | Include | Exclude | Ambigui (PM review) |
|---|---|---|---|---|
| 1 — Lifespan boot | 11 | 3 (L1, L5, L7) | 6 (L2,L3,L4,L6,L8,L11) | 2 (L9, L10) |
| 2 — GET-triggered sweep | 3 | 3 (R1, R2, R3) | 0 | 0 |
| 3 — Route-triggered resolvers | 4 | 4 (D1, D2, D3, D4) | 0 | 0 |
| 4 — Onboarding POST | 1 | 0 | 1 (O1, coperto da gate 5) | 0 |
| **TOTALE** | **19** | **10** | **7** | **2** |

---

## ⚠️ Ambigui — DECISIONE PM RICHIESTA

### AMB-1 — `seed_round12_release_tester_roster`

**Path**: `/app/backend/app/scripts/seed_round12_release_tester_roster.py`
**Trigger**: chiamato al lifespan boot (linea 67 lifespan.py, dentro try/except).
**Contesto**: dal commento in lifespan.py riga 65-67:
> "ROUND 12.D.3 — preview-only: free tester's stuck adventurers so they can build a PvP defense team. No-op in production."

**Effetto plausibile**: modifica campi di `adventurers` per tester account (`tester@orbus.test`). Non insert new — solo update.

**Domande per PM**:
1. INCLUDE (safe: no adventurer writes during freeze anche se solo tester)?
2. EXCLUDE (è preview-only e tester-scoped, drift trascurabile)?

**Mia raccomandazione**: **INCLUDE conservative** — modifica documento `adventurers` (collezione reset-impacted). Il freeze deve essere massimalista.

### AMB-2 — `run_forge_migration`

**Path**: `/app/backend/app/seeds/seed_forge.py`
**Trigger**: chiamato al lifespan boot (linea 74 lifespan.py, PRIMA di `run_forge_seeds`).
**Contesto**: nome suggerisce migration schema (update documenti esistenti) su forge catalog.

**Domande per PM**:
1. INCLUDE (safe se scrive su collezioni live non-catalog)?
2. EXCLUDE (se scrive solo su catalog invariant come nome suggerirebbe)?

**Mia raccomandazione**: **verificare il source** prima della decisione. Se scrive solo `items`/`recipes` catalog → EXCLUDE. Se scrive `inventory_items` o `guilds` → INCLUDE.

---

## Note tecniche coverage

1. **HTTP maintenance freeze (gate 5) copre**: tutti i POST/PUT/PATCH/DELETE handler HTTP → i job invocati DENTRO tali handler sono già bloccati transitivamente. Nessun guard aggiuntivo serve per la Categoria 4 (O1).

2. **Internal freeze (gate 7 NEW) deve coprire**: job invocati fuori dal ciclo POST/PUT/PATCH/DELETE, ovvero:
   - Boot-time seeds (Categoria 1)
   - GET-triggered sweep resolvers (Categoria 2)
   - Resolver invocati da altri contesti non-HTTP (Categoria 3 conservative)

3. **Nessun scheduler o cron trovato**: quindi la definizione "internal job" per Orbus si riduce a "codice async invocato non da POST/PUT/PATCH/DELETE HTTP". Il decorator `@frozen_when_active` si adatta bene a questo pattern.

4. **Pattern decorator applicabile**: tutti i 10 job identificati come INCLUDE sono `async def`. Nessuna variante sync-only necessaria.

5. **`orbus.onboarding.starter_roster`** (job che ha causato drift +2):
   - Trigger 1: `guilds/routes.py:34` POST → coperto da gate 5 (HTTP freeze)
   - Trigger 2: `seed_round5.py:603` boot lifespan (via `ensure_starter_roster_for_all_guilds`) → **NON coperto** attualmente → **richiede gate 7**
   - Conclusione: L1 INCLUDE è **hard-required** e mirato al colpevole.

---

## Ordine di patch proposto (Fase B.1+, dopo PM review)

1. Creare `/app/backend/app/core/job_freeze.py` (helper + decorator).
2. Patch L1 (`ensure_starter_roster_for_all_guilds` in `app/onboarding/services.py:123`) — **CRITICAL fix per il drift +2 documentato**.
3. Patch L5, L7 (backfill_bound_fields, backfill_signature_inventory).
4. Patch R1, R2, R3 (sweep resolvers).
5. Patch D1, D2, D3, D4 (route-triggered resolvers).
6. Decidere AMB-1, AMB-2 con PM prima di patchare.
7. Playbook `/app/memory/r18_reset1b_ops_write_freeze_playbook.md` — sezione "Internal Job Freeze".
8. Test suite `/app/backend/tests/backend_round1b_write_freeze_full_test.py` (10 cases).

---

## Vincoli rispettati fino ad ora (B.0)

- ✅ **ZERO code change** (solo grep read-only)
- ✅ **ZERO DB write**
- ✅ **ZERO modifica script sealed** (5/5 preflight/postflight OK)
- ✅ **ZERO test eseguito**
- ✅ **ZERO patch** applicata a nessun file `.py`
- ✅ Solo creazione MD inventory in `/app/memory/`

---

**STOP alla B.0 — attendo review PM per:**
1. Conferma coverage 10 job hard-include (Categoria 1: L1,L5,L7 / Categoria 2: R1,R2,R3 / Categoria 3: D1,D2,D3,D4).
2. Decisione AMB-1 (`seed_round12_release_tester_roster`) → INCLUDE / EXCLUDE.
3. Decisione AMB-2 (`run_forge_migration`) → INCLUDE / EXCLUDE (o verifica preliminare).
4. Conferma exclude Categoria 4 (O1 già coperto da gate 5).
5. Autorizzazione a procedere con B.1 (creazione helper + decorator) → B.5 (report finale).
