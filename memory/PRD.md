# Orbus Online — PRD (rolling)

> Stato aggiornato: 2026-06-27 — Fine ROUND 6B (Territorio + Adventurer Cap + Backend Guards + Save-as-Squad bonus). Pre-Redeploy bundle: 6A.2c + 6B.x.

## Problem statement (originale)

Costruire un MMO gestionale testuale full-stack (FastAPI + React + MongoDB)
chiamato "Orbus Online: Guild Master": il giocatore gestisce una gilda di
avventurieri, recluta personaggi, li equipaggia, li manda in dungeon ed
incursioni (raids), partecipa al mercato/aste, alla forgia, ai consorzi e
alla chat. Interfaccia testuale, scura, minimalista. Lingua italiana primaria.

## Architettura

- **Backend**: FastAPI async + Motor (Mongo). Tutti gli endpoint sotto `/api`.
- **Frontend**: React SPA (CRA + react-router) con Tailwind + shadcn/ui.
- **Auth**: JWT HS256 7gg, bcrypt. Emergent-Google opzionale (non in scope ora).
- **DB**: MongoDB con `MONGO_URL` + `DB_NAME` da env.
- **Lint gate**: `yarn lint:strict` deve passare 0 errors/0 warnings prima del deploy (BUILD_RULES R8).

## Personas

- **Player casual**: 5-15 min/giorno, vuole vedere progressi tangibili (gilda livella, struttures sbloccate, raid completati).
- **Player commited**: gestisce squadre custom, fa raid weekly, partecipa al consortium.
- **Power user**: roster 30+ avventurieri, ottimizza equip + traits, partecipa all'auction P2P.

## Implementato (cumulativo, ordinato per round)

### Phase 1-19.x (pre-ROUND 6)
Auth, guild, recruitment, dungeons, expeditions, inventory, equipment, forge,
raids, consortiums, chat, shop NPC, leaderboard, admin, audit log, daily/weekly
quests, chronicle, onboarding, ESLint flat config (Phase 19.x).

### ROUND 6A.1 (Adventurer Generator)
Generatore stat/trait probabilistico, esposizione `total_power` su API/UI.

### ROUND 6A.2a (Custom Squads)
CRUD backend `/api/squads`, UI `/squads` + `SquadBuilder` con validazione.

### ROUND 6A.2b (Load Squad + Trait Hygiene)
Dropdown "Load Squad" in ExpeditionNew + RaidBuilder, script `quarantine_and_migrate_traits.py`,
`display_name_it` hydration centralized via `frontend/src/utils/trait.js`.

### ROUND 6A.2c (Lint Gate + Invia Squadra)
ESLint strict config + R8 BUILD_RULES. Bottoni "Invia in Spedizione/Lancia Raid" su /squads, banner contestuale su Dungeons/Raids, auto-load su ExpeditionNew/RaidBuilder via `?squad_id=`.

### ROUND 6B.1 (Territorio data model)
Collezione `guild_structures`, 11 strutture, unlock_table dichiarativa (20 chiavi), upgrade costs, 3 endpoint `/api/territory[/purchase|/upgrade]`, migration script idempotente che ha backfillato **6.595 gilde** (Iron Lantern dormitories Lv7 LEGACY 👑).

### ROUND 6B.2a (Backend Core)
- Adventurer cap formula 5/10/15/20/25/30 + Lv7 LEGACY (50)
- `POST /api/recruitment/recruit` con cap guard 422
- `POST /api/adventurers/{id}/retire` con 6 precondizioni (in_expedition/in_squad/equipped/etc.)
- Decorator `require_unlocked()` + applicato a **14 endpoint** (shop buy/sell, auction list/buy, forge refine/enchant/disenchant/reroll, workshop craft, raid start, consortium create/join, chat global/consortium)
- Audit `adventurer_cap_reached`, `adventurer_retired`

### ROUND 6B.2b (Frontend UI)
- Pagina `/territory` con 11 card stateful (6 states: locked/buyable/upgradable/max/legacy/insufficient_gold)
- Banner ROSTER X/N + cap_reached toast con CTA in Recruitment
- Modal Retire su Adventurers con 4 codici errore handle
- Global 423 interceptor (toast warning + CTA "Vai al Territorio")
- Nav link "TERRITORIO" font-bold + 12 chiavi i18n IT/EN

### ROUND 6B.2c (Polish + bonus)
- Dashboard widget TERRITORIO (Avventurieri X/Y + Strutture X/11) + over-cap banner
- Bottone "💾 Salva come squadra" sui report vittoria (Expedition + Raid)
- SquadBuilder accetta `?adventurer_ids=...&type=...&suggested_name=...`
- Sezione "Territorio di Gilda" aggiunta a `/guide`
- Helper test legacy fixati (`backend_phase19_3_chat_test.py`, `backend_phase19_4b_shop_test.py`) per backward-compat con nuovi guard

## Backlog prioritizzato

### P0 (next round)
- Atomic transaction su `purchase`/`upgrade` (Motor session) — oggi solo gold-check, no deduzione atomic
- Materials check + deduction su territory upgrade
- T1/T2 raid differentiation guard dentro service (oggi solo `raid.start.t1` base)

### P1
- Over-cap "Gestisci roster" full modal con filtri (rarità/PWR/ruolo) + bulk retire
- Nav lock icons dinamici (richiede territory state in AppHeader Context)
- Caching `guild_structures` per-request (1 extra find_one per call guarded)

### P2
- Training Grounds hook (specializzazioni avventurieri) — ROUND 6C
- Husky pre-commit hook (deferred da 6A.2c)
- Refactor markets deprecated (`/api/market/*` 5 endpoint) — rimuovere o gating
- Mobile collapsable cards in /territory

### P3 backlog (storico)
- ROUND 6 Seasons/Leagues
- ROUND 11 Admin/Moderation + fix xdist flaky pytest

## Test coverage

- **Backend pytest** (subset key 7 suite): **81 passed in 77s** post-6B.2c.
- **Frontend lint strict**: 0 errors / 0 warnings (R8 ✅).
- **Browser smoke**: Territory page 11 card, Dashboard widget 42/50 + 7/11, Retire modal apre, Recruitment cap banner ROSTER 42/50.

## Test credentials

Vedi `/app/memory/test_credentials.md`. Account principale: `tester@orbus.test` / `password123`.

## Constraints invariati

- ❌ NO hard delete (retire soft, structures soft, traits quarantined)
- ❌ NO P2W, NO premium boost
- ❌ NO PII leak in API responses (no email, no `_id` Mongo)
- ❌ NO breaking change su endpoint esistenti
- ✅ Lint clean obbligatorio pre-deploy (R8)
- ✅ Migration idempotenti (`refuse APP_ENV=production`)
- ✅ Audit log proper su tutte le state-mutations rilevanti
