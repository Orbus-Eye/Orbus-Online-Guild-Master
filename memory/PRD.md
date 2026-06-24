# Orbus Online: Guild Master — PRD

## Original problem statement (abridged)
Full-stack text-based MMO guild manager. Stack: FastAPI + MongoDB + React, JWT auth (HS256, 7d), dark mono terminal UI, all backend routes under `/api`. **Phase 1 only** in this iteration.

## User personas
- **Guild Master (player)** — registers, founds a guild, manages it over time.
- **Admin** — future phases (moderation, market controls). Schema flag `is_admin` reserved but not exposed.

## Core requirements (static)
- JWT email/password auth, bcrypt password hashing
- One guild per user (enforced by unique index + app check on `owner_user_id`)
- All endpoints prefixed with `/api`, OpenAPI at `/api/openapi.json`, docs at `/api/docs`
- Timestamps UTC ISO strings
- Public IDs are UUID4 strings; `_id` ObjectId never leaks
- Dark monospace terminal UI (JetBrains Mono, #0a0a0c bg, #d4a14a amber accent)

## What's been implemented (Phases 1 + 2)

### Phase 1 — 2026-06-23
- Backend FastAPI app with `/api` router
  - `GET /api/health`, `GET /api/openapi.json`, `GET /api/docs`
  - `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`
  - `POST /api/guilds`, `GET /api/guilds/me`
  - MongoDB indexes (users.email/id unique; guilds.id/owner_user_id unique; guilds.name)
  - Idempotent tester seed gated by `APP_ENV != "production"`
  - Lenient email validation (allows `.test` TLD)
- Frontend React (react-router 7)
  - Pages: `/`, `/login`, `/register`, `/create-guild`, `/dashboard`
  - Route guards: `GuestOnly`, `ProtectedRoute(requireGuild)`, `GuildGate`
  - AuthContext with localStorage `orbus_token`, auto-logout on 401
- Backend + frontend covered by testing agent (100% pass — 17/17 backend)

### Phase 2 — 2026-06-24
- Backend
  - 4 new collections: `adventurer_classes`, `adventurer_traits`, `adventurers`, `recruitment_offers`
  - Idempotent content seed at startup (all envs): **5 classes** (Warrior/Rogue/Mage/Priest/Ranger) + **5 traits** (Brave, Quick Learner, Frail, Sharp Eye, Devout)
  - New endpoints:
    - `GET /api/adventurer-classes` (public)
    - `GET /api/recruitment/candidates` — generates 4 random candidates, replaces prior offers
    - `POST /api/recruitment/recruit` — atomic claim+pay+create; refunds offer on insufficient-gold
    - `GET /api/adventurers` — list for current user's guild
  - `GET /api/guilds/me` now includes `adventurer_count`
  - Server-side stat generation; candidate stats saved server-side and not mutable by client
  - Cross-user isolation enforced via `guild_id` filter on offers
- Frontend
  - New pages: `/recruitment` (4-card grid + refresh + gold counter + insufficient-gold warning) and `/adventurers` (responsive: desktop table, mobile stacked cards)
  - New `AppHeader` shared nav (DASH/ADVENTURERS/RECRUIT + gold + username + logout); active route highlighted
  - Dashboard adds **Adventurers** stat card; quick-actions 01/02 are now active links to Recruit/Adventurers; 03/04 remain locked
  - Rarity badge palette: Common #9ca3af, Uncommon #22c55e, Rare #3b82f6, Epic #a855f7
- Testing agent: 100% pass — 14/14 new Phase-2 + 17/17 Phase-1 backend; all frontend flows incl. mobile 375×812

### Phase 3 — 2026-06-24
- Backend
  - 5 new collections: `dungeons`, `items`, `expeditions`, `expedition_members`, `inventory_items`
  - Idempotent content seed (always-on): **1 dungeon** (Goblin Warrens, 60s, recommended_power=45, base_gold=35, base_xp=25, team=3) + **5 items** (Rusted Sword / Goblin Dagger / Cracked Staff / Novice Charm / Torn Leather Vest) — all `can_be_sold_for_real_money=false`
  - New endpoints: `GET /api/dungeons`, `GET /api/items`, `POST /api/expeditions`, `GET /api/expeditions`, `GET /api/expeditions/{id}`, `GET /api/inventory`
  - `GET /api/guilds/me` now also exposes `active_expedition_count`, `last_expedition_id`, `last_expedition_summary` and triggers a lazy sweep
  - **Lazy completion sweep** with atomic claim (`find_one_and_update` filter `status='in_progress'` → `completing`) — idempotent, callable from `/guilds/me`, `/expeditions`, `/expeditions/{id}`
  - **Team-power formula**: Σ(STR+AGI+INT+END+FAI+level·2) +5/role present (Tank/DPS/Healer) +10 if all 3 roles → clamped success_chance 50 + (power − recommended), [10..95]
  - **Reward branches**: success → +base_gold +base_xp +50% loot drop (Common/Uncommon pool); failure → +25% gold +40% xp, no loot
  - **Level-up loop**: while `xp >= level·100` → level+1, xp −= old_level·100, +1 to class-appropriate stat (Warrior STR|END / Rogue AGI / Mage INT / Priest FAI / Ranger AGI|STR)
  - **Item monetization validator**: `can_be_sold_for_real_money=true` requires `is_cosmetic=true AND not affects_combat/economy/ranking`, enforced at seed/insert
  - **Cross-guild isolation**: 404 (not 403) on foreign expedition GETs; adventurer-id filter on POST scoped to user's guild
- Frontend
  - 5 new pages: `/dungeons`, `/dungeons/:slug/start` (team selection w/ live preview), `/expeditions` (live countdown + auto-poll), `/expeditions/:id` (after-action report w/ narrative + loot), `/inventory` (desktop table + mobile stacked cards)
  - Dashboard adds ACTIVE EXP stat + last-expedition deeplink; quick-actions Dungeons (03) and Inventory (04) now active links
  - AppHeader nav extended with DUNGEONS · EXPEDITIONS · VAULT (6 total)
  - Status badges: SUCCESS=#22c55e, FAILED=#ef4444, IN PROGRESS=amber; rarity palette continues
- Testing agent: 100% pass — 11/11 new Phase-3 + 14/14 Phase-2 + 17/17 Phase-1; full frontend e2e + mobile 375×812 verified

### Phase 4 — 2026-06-24
- Backend
  - `get_admin_user` dependency (gates `/api/admin/*`); tester promoted to `is_admin=true` on startup when `APP_ENV != "production"` (idempotent)
  - **16 admin endpoints**: `GET/POST/PATCH /api/admin/{classes,traits,dungeons,items}` + `POST /api/admin/{collection}/{id}/toggle-active` (soft-delete via flag)
  - **Trait effects at recruitment**: each candidate gets 0/1/2 traits via weighted random (50/35/15%); `_apply_trait_effects` adds `flat` modifiers to the 5 main stats with floor=1; `percent xp_gain` deferred (TODO Phase 5+)
  - Traits persist as denormalized snapshot on `adventurers.traits`; expedition `team_power` automatically uses them (no expedition-side changes)
  - Backward-compat: legacy adventurers without `traits` field serialize as `traits: []`
  - **Monetization invariant rinforzato**: `validate_item_monetization` enforced on both POST and PATCH `/api/admin/items` — `can_be_sold_for_real_money=true` requires `is_cosmetic=true AND NOT affects_combat/economy/ranking`
  - **Hardening expeditions** audit re-run: cross-guild adventurer 404, duplicate ids 400, busy adventurer 400, cross-guild GET expedition 404 (not 403), idempotency under concurrent fetch
- Frontend
  - New page `/admin` with 4 tabs (CLASSES / TRAITS / DUNGEONS / ITEMS) — table on desktop + stacked cards on mobile + shadcn Dialog editor with per-entity forms
  - Item editor: ticking "Real-money sale" auto-clears `is_cosmetic`/`affects_*` to maintain invariant (UI guard); warning panel shown; backend remains authoritative
  - Trait badges (green positive / red negative) added to Recruitment cards and Adventurers table+cards; tooltips show "+1 strength" / "-1 endurance" etc
  - AppHeader: ADMIN nav link visible only when `user.is_admin === true`
  - Non-admin user navigating to `/admin` → redirect to `/dashboard` with toast "Admin access required"
  - Mobile audit (390×844): all 6 main routes verified zero horizontal overflow
- Testing agent: **100% pass — 40/40 Phase-4 + 11/11 Phase-3 + 14/14 Phase-2 + 17/17 Phase-1 = 82/82 backend** + full frontend e2e + mobile responsive

## Prioritized backlog (next phases)

### P0 — Phase 4: Admin Panel + Trait Effects + Equip
- Admin CRUD over dungeons/items/classes/traits (with `validate_item_monetization` already in place)
- Apply trait `modifier_value` at recruit time (Brave +1 STR, Frail −1 END, Quick Learner +10% xp, Sharp Eye +1 AGI, Devout +1 FAI)
- Equip items to adventurers (slot per item_type), apply bonuses to expedition team_power
- Reputation system + public `/api/ranking/top` (no-auth, cached) for growth loops

### P1 — More content
- Additional dungeons of higher difficulty/team_size (e.g., 3-tier ladder)
- Rare/Epic loot pool, drop-rate balancing
- Market (player-to-player), gold sinks

### P2 — Phase 5: Polish
- ~~Migrate `@app.on_event` → `lifespan`~~ ✅ done (Phase 5)
- **Split `server.py` into modules** (auth, guilds, recruitment, expeditions, seeds, helpers) — deferred to **Phase 5.5**
- ~~Tighten CORS to known origins~~ ✅ env-gated (Phase 5)
- ~~Password reset, refresh tokens, brute-force protection~~ ✅ done (Phase 5)

### P2 — Premium tier
- `can_be_sold_for_real_money=true` cosmetic-only items (validator already enforces invariant)

## Phase 5 — 2026-06-24 (Security Hardening, scope-reduced)
Implemented (zero gameplay change, all 82 prior tests still pass + 21 new):
- FastAPI **`lifespan`** replaces `@app.on_event`
- **Env-gated CORS**: `APP_ENV=production` requires explicit `CORS_ORIGINS` (no `*`)
- **Reinforced password rules**: min 8 chars + ≥1 letter + ≥1 digit (regex), enforced on register and password-reset confirm
- **Login lockout**: collection `login_attempts`, 5 fails → 15-min lock → HTTP 429
- **Refresh tokens** (multi-device): collection `refresh_tokens`, opaque 256-bit token (SHA-256 hashed at rest), 30-day TTL
  - `POST /api/auth/refresh` (rotate access token)
  - `POST /api/auth/logout` (revoke a single refresh token — current device only)
  - Backward-compat: `access_token` still issued exactly as before
- **Password reset skeleton** (collection `password_reset_tokens`):
  - `POST /api/auth/password-reset/request` — always 200, reset link logged to backend console (no email send)
  - `POST /api/auth/password-reset/confirm` — single-use, 60-min TTL, revokes **all** refresh tokens on success
- **TTL indexes** on `login_attempts.last_attempt_at` (24h), `refresh_tokens.expires_at` (0s), `password_reset_tokens.expires_at` (0s)
- **MongoDB indexes audit**: 24+ indexes confirmed present on startup
- **Admin dependency audit**: all 16 `/api/admin/*` endpoints use `get_admin_user`
- 21 new pytest tests (`tests/backend_phase5_test.py`) covering all above behaviors
- TODO: reduce access TTL from 7d → 1h once the React frontend actively uses `/api/auth/refresh`

## Phase 6 — 2026-06-24 (Equip System + UI Password Reset)
Implemented (zero gameplay regression, **117/117 pytest PASS**: 103 prior + 14 new):
- **New collection `equipped_items`** (id, guild_id, adventurer_id, item_id, slot, equipped_at)
  - Indexes: id UNIQUE, guild_id, adventurer_id, item_id, **compound UNIQUE (adventurer_id, slot)**
- **3 new endpoints** under `/api/adventurers/{id}/equipment|equip|unequip`
- **Equipment locked** while an adventurer is in expedition (`is_available=false`) → HTTP 400
- **`/api/inventory`** extended with `total_quantity` / `equipped_quantity` / `available_quantity` (legacy `quantity` preserved as alias of total)
- **`/api/adventurers`** extended with `equipment`, `base_power`, `equipment_power`, `total_power`
- **`expedition_members`** snapshot extended with `equipment_snapshot`, `equipment_power_snapshot`, `total_power_snapshot` (immutable after start)
- **`team_power` formula** keeps the original shape (sum of per-member power + role bonuses), but each member's per-member contribution is now `total_power_snapshot` (base + equipment) when present. With no equipment the result is identical to Phase 3.
- **Item seed rebalanced** (idempotent upsert by slug) to give all 5 items meaningful slot/stat semantics:
  - Rusted Sword: weapon Common +1 STR / pow 1
  - Goblin Dagger: weapon Uncommon +2 AGI / pow 2
  - Cracked Staff: weapon Common +1 INT +1 FAI / pow 1
  - Novice Charm: accessory Common +1 FAI / pow 1
  - Torn Leather Vest: armor Common +1 END / pow 1
- **Monetization invariant intact**: all 5 seed items remain `can_be_sold_for_real_money=false`; validator still rejects combat-affecting items with realmoney=True (400)
- **UI Password Reset**: new public pages `/password-reset/request` and `/password-reset/confirm`, plus a `forgot password?` link on `/login`. Weak-password / bad-token errors render inline + via sonner toast.
- **Frontend**: `/adventurers` shows Power column + "manage" link; `/inventory` shows total/equipped/available columns + stat bonuses; `/adventurers/:id/equipment` is a full 3-slot equip page; `/expeditions/:id` shows the frozen equipment_snapshot per member.
- 14 new pytest tests in `tests/backend_phase6_test.py`

## Phase 7 — 2026-06-24 (Tier 2/3 Dungeons + Rare/Epic Loot + Equipment Delta)
Implemented (zero gameplay regression on Goblin Warrens — 133/133 pytest PASS: 117 prior + 16 new):
- **3 dungeons** total: Goblin Warrens (Tier 1, 60s/45/3, invariato), **Shadow Crypts** (Tier 2, 120s/60/3, gold 65/xp 50), **Dragon's Hoard** (Tier 3, 300s/80/3, gold 120/xp 90)
- **8 new items** (idempotent seeds): 4 Rare (Cryptbone Blade, Spiritglass Staff, Gravewarden Mail, Relic Signet) + 4 Epic (Drakefang Greatsword, Embermind Focus, Dragonscale Vest, Hoardlord's Seal). Tutti `can_be_sold_for_real_money=false`, `affects_combat=true`.
- **Loot tables per dungeon** (in `DUNGEON_LOOT_TABLES` constant): success-chance + weights per rarità. Failure restituisce SOLO Common (mai Rare/Epic). Goblin Warrens success 50% (Common 85, Uncommon 15); Shadow Crypts success 65% (Common 50, Uncommon 35, Rare 15) + failure 10% Common; Dragon's Hoard success 80% (Uncommon 50, Rare 35, Epic 15) + failure 5% Common.
- **Progression gate (soft, enforced backend)**: Shadow Crypts richiede `guild.level >= 1 AND adventurer_count >= 3`; Dragon's Hoard richiede `guild.level >= 2 OR best-three total_power >= 65`. `GET /api/dungeons` ritorna `unlocked` + `unlock_reason`. `POST /api/expeditions` → **HTTP 403 "Dungeon locked: ..."** se non sbloccato.
- **Equipment delta (smart enhancement)**: ogni expedition doc registra all'avvio (immutable):
  - `base_team_power` (senza equipment, con composition bonus)
  - `equipment_power_bonus` (somma equipment_power dei membri)
  - `final_team_power` (= team_power, backward-compat)
  - `success_chance_without_equipment`, `success_chance_with_equipment`
  - `equipment_delta_text` — narrativa generata: "No equipment was used on this run." / "Equipment contributed +N team power, improving success chance from X% to Y%." / "Equipment contributed +N team power. Success chance was already at maximum (95%)."
- **Dashboard stats** su `GET /api/guilds/me`: `highest_dungeon_slug`, `total_expeditions_completed`, `last_loot_item` (computed lazily).
- **`GET /api/dungeons` ora accetta auth opzionale** (Bearer): retro-compatibile con chiamate non autenticate (Phase 3 test) — quando l'utente è loggato, popola `unlocked` per la sua guild.
- 16 new pytest tests in `tests/backend_phase7_test.py` (seeds, gates, delta, loot table probabilistico ×60 success-runs per Rare/Epic, dashboard stats).
- **Frontend**: `/dungeons` mostra tier I/II/III + badge LOCKED + tooltip unlock_reason + CTA disabilitato per dungeon lockati; `/dungeons/:slug/start` mostra EQUIPMENT BONUS + TEAM POWER FINAL + success-chance color-coded (verde >75%, ambra 40-75%, rosso <40%) + warning sobrio "underpowered"; `/expeditions/:id` ha una sezione "Expedition Analysis" con tutti i 5 delta + narrative; `/dashboard` ha 3 mini-cards EXPEDITIONS DONE / HIGHEST DUNGEON / LAST LOOT.

## Known limits / debt
- Frontend continua a usare solo `access_token` (no refresh) — Phase 8+
- `server.py` ancora monolitico (~2.2k linee) — Phase 5.5c
- Password-reset via console log (solo se `APP_ENV != "production"`) — Phase 8 (Resend/SendGrid)
- Nessun rate-limit visibile a livello di rotta su `POST /api/expeditions` (solo lockout su login) — accettato per ora
- Gate Dragon's Hoard usa `best-three total_power CORRENTE` non "best three di sempre": una gilda che equipaggia e poi disequipaggia perde l'unlock se nuovi recruit hanno power basso. Comportamento documentato; semplice da estendere con `_max_team_power_ever` denormalizzato in Phase 8 se serve.
- Loot table hardcoded in `server.py` (constant `DUNGEON_LOOT_TABLES`), non in DB. Cambiare le percentuali richiede deploy. Per ora va bene; futuro: collection `dungeon_loot_tables`.

## Production hardening debt (Phase 5.6 audit — explicit deferrals)
- **JWT in localStorage**: vulnerabile a XSS. Migrare a httpOnly cookies con CSRF token in production deploy phase. Richiede CORS+CSRF middleware backend + refactor del flow auth frontend. Stima: 3-4h. Status: DEFERRED — refresh-token flow FE non ancora attivo, prerequisito non soddisfatto.
- **Email reale per password reset**: in `app/auth/services.py` il log del token è ora gated da `APP_ENV != "production"`. In production il log è soppresso ma manca ancora il mailer reale → l'endpoint `/api/auth/password-reset/request` risponde 200 senza inviare nulla. Wire Resend/SendGrid in Phase 8.
- **Function-level complexity refactor**: `start_expedition`, `_complete_one_expedition`, `recruit_adventurer`, `equip_item`, `ensure_indexes` (server.py) e `Admin.jsx`, `AdventurerEquipment.jsx` (FE) sono ancora monolitici. Splitting deferito a Phase 5.5d (server.py) / 5.5e (FE components).
- **TypeScript migration**: out of scope MVP. Da rivalutare quando il prodotto supera lo stadio early-MVP.

## Phase 8 — 2026-06-24 (max_team_power_ever + Replay Last Run)
Implemented (148/148 pytest PASS — 133 baseline + 15 new Phase 8 tests; zero regressions, OpenAPI: +2 paths, zero changes to existing):

**A. Sticky-peak gate fix (`max_team_power_ever`)**
- New denormalised field on `guilds`: `max_team_power_ever: int` (default 0 via `.get()` fallback — no migration needed for existing docs)
- Updated atomically via Mongo `$max` operator inside `_dispatch_expedition()` (shared by both `POST /api/expeditions` and `POST /api/expeditions/replay-last`)
- Dragon's Hoard gate now unlocks via: `guild.level >= 2 OR current_best_three >= 65 OR max_team_power_ever >= 65`
- New `unlock_reason` string: "Requires guild level 2, team power ≥ 65, or peak team power ever ≥ 65"
- Exposed in `GET /api/guilds/me` payload as `max_team_power_ever`

**B. Replay Last Run feature**
- New endpoints:
  - `GET /api/expeditions/last-completed` → 200 `{expedition, adventurer_ids, can_replay, cannot_replay_reason}` or 404 if no completed run
  - `POST /api/expeditions/replay-last` → 201 with new expedition (status=`in_progress`, `is_replay=true`), or 400/403/404 with explicit `detail`
- Server-side eligibility checks (`_check_replay_eligibility`): dungeon still active + gate unlocked for CURRENT guild, all 3 original adventurers still in guild and `is_available=True`, team size matches dungeon requirement
- Replay re-uses `_dispatch_expedition()` helper → same locks, same `$max` bump, same equipment-delta calculation. Equipment snapshot is FRESH from current state, not from original run.
- New `expedition.is_replay: bool` field surfaces a "REPLAY" badge in the UI
- Frontend:
  - `Dashboard.jsx`: new "LAST EXPEDITION" card under stats with result badge + "Replay Last Run" amber button. Disabled with tooltip when `can_replay=false`. Empty state with link to /dungeons when no run exists.
  - `ExpeditionReport.jsx`: "Replay This Run" button + "REPLAY" badge in the report header (only when this report is the current last-completed). Reuses the same backend endpoint.

**Tests added** (`tests/backend_phase8_test.py`, 15 cases):
1-6. max_team_power_ever: default 0, set after first run, never decreases ($max), unlocks Dragon's Hoard via peak, lock message mentions all 3 criteria, updates also via replay
7-15. Replay: 404 for fresh guild (both endpoints), correct shape after first run, happy path, recomputes power with current equipment, blocked when adventurer locked/removed, 400/403 when dungeon deactivated, original run untouched after replay

**Files modified**: `backend/server.py` (+182 / −2 net: helper extraction + 2 new endpoints + guild_public + gate update + expedition_public), `backend/tests/backend_phase8_test.py` (new, 332 lines), `frontend/src/pages/Dashboard.jsx` (+115 / −24), `frontend/src/pages/ExpeditionReport.jsx` (+72 / −5), `memory/PRD.md`

## Phase 5.6 — 2026-06-24 (Code Quality Quick-Wins, scope ridotto)
Implemented (zero behaviour change, **133/133 pytest PASS**, OpenAPI paths identical):
- **Secure RNG**: `random.{uniform,choice,choices,random,randint,sample}` sostituito con `secrets.SystemRandom()` in `server.py` (17 call sites) e `app/expeditions/loot_tables.py` (5 call sites). Distribuzioni/range invariati — solo la sorgente di entropia è aggiornata. Tutti i test probabilistici (loot table, Shadow Crypts failure-never-rare, ecc.) passano identici.
- **Password-reset log gated**: in `app/auth/services.py::request_password_reset` il `logger.info("[PASSWORD-RESET] ...")` è ora wrappato in `if APP_ENV != "production"`. In production il token non viene loggato (e l'endpoint risponde comunque 200 per evitare account enumeration).
- **Tester credentials documented**: `TESTER_PASSWORD = "password123"` in `app/shared/constants.py` ha un commento `# noqa: S105 — test fixture credential, not a real secret`. Il seeding via `seed_tester()` rimane gated da `APP_ENV != "production"`.
- **`.env.example`** creato (`/app/backend/.env.example`): documenta MONGO_URL, DB_NAME, JWT_SECRET, APP_ENV, CORS_ORIGINS con descrizioni e default. Nessun valore reale committato.
- **PRD updated**: nuova sezione "Production hardening debt" elenca i deferrals espliciti (JWT cookies, mailer reale, function/component refactor, TypeScript).

**Verified clean** (already aligned to spec — no fix needed):
- `is` vs `==` literal comparison: 0 occurrences (grep + pyflakes confirmed)
- React hook missing deps: 0 occurrences (eslint clean on Expeditions/ExpeditionNew/Recruitment/AdventurerEquipment/Admin)
- React array index keys: i-keys present only on Skeleton placeholders (Recruitment.jsx 108/215) e column-index iteration (Admin.jsx 473) — entrambi pattern accettabili (chiavi stabili nel contesto, nessun bug reale)
- `console.log/debug/info` frontend: 0 occurrences
- `print()` backend: 0 occurrences
- JWT_SECRET hardcoded default: assente, `app/core/config.py` usa `os.environ["JWT_SECRET"]` che raise KeyError se mancante

## Phase 5.5 — 2026-06-24 (Partial Modular Refactor — Data + Pure Logic)
Implemented (zero behaviour change, **133/133 pytest PASS** identical baseline):
- **Created** `/app/backend/app/` package skeleton with 3 submodules:
  - `app.shared.constants` — single source of truth for JWT/security/gameplay/equipment constants
  - `app.seeds.seed_data` — declarative CLASS_SEED, TRAIT_SEED, DUNGEON_SEED, ITEM_SEED (pure data, ~150 lines)
  - `app.expeditions.formulas` — pure functions: `compute_team_power`, `compute_success_chance`, `adventurer_base_power`, `item_equip_power`, `build_equipment_delta`
  - `app.expeditions.loot_tables` — `DUNGEON_LOOT_TABLES` constant + `roll_loot_for_dungeon(db, dungeon, success)` async helper
- **server.py shrunk** 2767 → 2541 lines (~226 lines removed of constant/data/formula duplication)
- `server.py` now imports all gameplay constants, seeds, formulas and the loot table from `app.*` and **no longer redefines them** (single source of truth)
- `server.py.pre-phase55.bak` retained as rollback safety net
- OpenAPI paths IDENTICHE pre/post refactor (34 paths totali, zero diff)
- Frontend NON toccato (zero changes)
- Tests NON modificati (133 esistenti passano identici)

**Deferred to Phase 5.5b (documented honestly)**:
- Route handlers (`/api/auth/*`, `/api/guilds/*`, etc.) remain in `server.py` — splitting requires first creating `app/core/{database,security,lifespan}.py` and rewiring all `Depends(get_current_user)` callsites. High risk for a single-session refactor; best done as Phase 5.5b with its own pytest gate.
- Pydantic schemas remain in `server.py`.
- Helper functions (inventory/equipment/recruitment snapshots) remain in `server.py` (they share the Motor `db` handle which needs to move to `app/core/database.py` first).

## Next tasks (Phase 8 candidates)
1. **Phase 5.5c**: split remaining 8 domains (guilds, adventurers, recruitment, dungeons, inventory, equipment, expeditions, admin) following the auth pattern established in 5.5b
2. **Replay last run** (best ROI: 1 endpoint + 1 button, big retention win)
3. **Real email integration** for password reset (Resend/SendGrid) + FE refresh-token consumption
4. **Onboarding tutorial** 5-step modal on first login
5. **`max_team_power_ever`** denormalised field so Dragon's Hoard gate is "sticky"

## Phase 5.5b — 2026-06-24 (Auth Domain Migration — POC for modular pattern)
Implemented (zero behavior change, **133/133 pytest PASS**, OpenAPI paths identical):
- **Created** `app/core/` scaffolding:
  - `app.core.config` — env-driven settings (MONGO_URL, DB_NAME, JWT_SECRET, APP_ENV) + `get_cors_origins()` + re-exports of gameplay/security constants from `app.shared.constants`
  - `app.core.database` — shared Motor `AsyncIOMotorClient` + `db` handle + `close_database()`
  - `app.core.security` — bcrypt helpers, JWT encode/decode, `validate_password_strength`, `bearer_scheme` (auto_error=False to preserve 401-on-missing-auth), `get_current_user`/`get_admin_user`/`get_optional_user` deps
- **Created** `app/auth/` domain:
  - `app.auth.schemas` — 6 Pydantic models (RegisterIn, LoginIn, RefreshIn, LogoutIn, PasswordResetRequestIn, PasswordResetConfirmIn) + `OrbusEmail` lenient type
  - `app.auth.services` — 14 functions: `register_user`, `authenticate_login`, `request_password_reset`, `confirm_password_reset`, refresh-token lifecycle (`_create/_consume/_revoke/_revoke_all`), login-lockout (`_check/_record/_reset`), opaque-token helpers (`_hash_token`, `_new_opaque_token`), and `user_public` projection. All accept `db` as first arg → unit-testable.
  - `app.auth.routes` — `APIRouter(prefix="/api/auth")` with all 7 endpoints (`register`, `login`, `me`, `refresh`, `logout`, `password-reset/{request,confirm}`)
- **server.py** trimmed 2541 → 2241 lines (−300 lines = −11.8%) — all auth helpers, schemas, security deps and 7 route handlers removed; replaced by `from app.core.*`/`from app.auth.*` re-exports + `app.include_router(auth_router)`
- **Backward-compat shims** in server.py: legacy `_check_login_lock(email)` etc (no `db` arg) still callable for any future code path
- **`server.py.pre-phase55b.bak`** retained as rollback safety net
- **OpenAPI paths**: 34/34 identical (zero diff between pre/post refactor)
- Frontend: zero changes
- Tests: zero changes (133 existing tests pass)

