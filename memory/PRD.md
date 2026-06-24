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

## Prioritized backlog (next phases)

### P0 — Phase 3: Dungeons & Expeditions
- `dungeons` catalog (seed at startup): name, tier, recommended level, gold/xp range
- `expeditions` collection: party of N adventurers → dungeon, async tick (or immediate resolve)
- `POST /api/expeditions` — dispatch party; consume stamina, lock adventurers (is_available=false)
- `GET /api/expeditions` / `GET /api/expeditions/{id}` — after-action report (loot, XP, casualties)
- Frontend `/dungeons` (browse + dispatch) and `/expeditions/:id` (report)

### P1 — Phase 3: Inventory
- `items` (templates) + `guild_inventory` (owned)
- Sell endpoint (gold gain)
- Frontend `/inventory` grid

### P2 — Phase 4: Reputation, Ranking, Market, Trait Effects
- Apply trait modifier_value/affected_stat at recruit time (right now traits are seed-only model)
- Guild rename (paid), public leaderboard `/api/ranking/top` (no-auth, growth lever)
- Player-to-player market, premium tier flag

### P2 — Phase 5: Admin Panel
- Promote `is_admin`, ban/unban, soft-rollback expeditions

## Known limits / debt
- Lifespan handlers still use deprecated `@app.on_event` (works, but should migrate)
- CORS `allow_origins='*'` + `allow_credentials=True` is technically invalid; harmless today (frontend uses Authorization header, not cookies). Tighten in Phase 2 once we know the final preview/prod origins.
- No password reset, no refresh token, no brute-force lockout in Phase 1 (intentional — deferred to a later security pass).
- Quick-action buttons on dashboard are intentionally `disabled` placeholders for phase-2/3.

## Next tasks
1. User-led review of Phase 1
2. Phase 2 scope confirmation (recruit-cost balance, stat ranges)
3. Implement Phase 2 endpoints + UI
