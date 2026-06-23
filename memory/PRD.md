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

## What's been implemented (Phase 1) — 2026-06-23
- Backend FastAPI app with `/api` router
  - `GET /api/health`, `GET /api/openapi.json`, `GET /api/docs`
  - `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`
  - `POST /api/guilds`, `GET /api/guilds/me`
  - MongoDB indexes (users.email/id unique; guilds.id/owner_user_id unique; guilds.name)
  - Idempotent tester seed gated by `APP_ENV != "production"`
  - Lenient email validation (allows `.test` TLD via `email_validator(test_environment=True)`)
- Frontend React (react-router 7)
  - Pages: `/`, `/login`, `/register`, `/create-guild`, `/dashboard`
  - Route guards: `GuestOnly`, `ProtectedRoute(requireGuild)`, `GuildGate`
  - AuthContext with localStorage `orbus_token`, auto-logout on 401
  - Dark/mono terminal aesthetic, shadcn primitives (Button, Input, Label, Textarea), sonner toaster
- Test credentials documented at `/app/memory/test_credentials.md`
- Backend + frontend covered by testing agent (100% pass)

## Prioritized backlog (next phases)

### P0 — Phase 2: Adventurers & Recruiting
- `adventurers` collection (id, guild_id, name, class, level, stats, status, hired_at)
- `POST /api/adventurers/recruit` (paid in gold, randomized stats)
- `GET /api/adventurers` (list owned)
- `DELETE /api/adventurers/{id}` (dismiss)
- Frontend: `/adventurers` table view + recruit dialog

### P1 — Phase 3: Dungeons & Expeditions
- `dungeons` catalog (seed at startup), `expeditions` collection
- `POST /api/expeditions` (party of adventurers → dungeon, async tick)
- Result reports: loot, XP, casualties
- Frontend: `/dungeons` browse + dispatch flow, `/expeditions/:id` after-action report

### P1 — Phase 3: Inventory
- `items` (templates) + `guild_inventory` (owned)
- Sell / equip endpoints
- Frontend: `/inventory` grid

### P2 — Phase 4: Reputation, Ranking, Market
- Guild rename (paid), public leaderboard `/api/ranking`
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
