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
- Migrate `@app.on_event` → `lifespan`
- **Split `server.py` into modules** (auth, guilds, recruitment, expeditions, seeds, helpers) — flagged by testing agent
- Tighten CORS to known origins
- Password reset, refresh tokens, brute-force protection

### P2 — Premium tier
- `can_be_sold_for_real_money=true` cosmetic-only items (validator already enforces invariant)

## Known limits / debt
- Lifespan handlers still use deprecated `@app.on_event` (works, but should migrate)
- CORS `allow_origins='*'` + `allow_credentials=True` is technically invalid; harmless today (frontend uses Authorization header, not cookies). Tighten in Phase 2 once we know the final preview/prod origins.
- No password reset, no refresh token, no brute-force lockout in Phase 1 (intentional — deferred to a later security pass).
- Quick-action buttons on dashboard are intentionally `disabled` placeholders for phase-2/3.

## Next tasks
1. User-led review of Phase 1
2. Phase 2 scope confirmation (recruit-cost balance, stat ranges)
3. Implement Phase 2 endpoints + UI
