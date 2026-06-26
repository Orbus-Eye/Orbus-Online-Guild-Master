# Orbus Online — ROADMAP NEXT MAJOR BLOCKS

**Created**: 2026-06-26 (post-ROUND 5 / Phase 19)
**Status**: Planning. All 6 rounds are **proposals** awaiting user lock-in.
**Constraint**: No P2W, no power-gear monetization, no premium gates on raids/expeditions.

═══════════════════════════════════════════
## Dependency Graph (suggested order)

```
ROUND 6 ──┬──> ROUND 9 ──> ROUND 10
          │
          ├──> ROUND 8
          │
          v
ROUND 11 ──> ROUND 7
```

**Rationale**:
- ROUND 6 (Seasons) is the foundation — every later block consumes its
  season-pass / leaderboard reset machinery.
- ROUND 11 (Admin/Mod) must precede ROUND 7 (free-form Consortia chat)
  because chat moderation requires admin tools.
- ROUND 8 (Class progression) can ship independently after ROUND 6 (it
  consumes the season XP curve but not chat).
- ROUND 9 (Live events) depends on ROUND 6 (season cadence) for spawn
  triggers.
- ROUND 10 (Cosmetic monetization) ships last — needs ROUND 6 + ROUND 9
  to populate the cosmetic shop with season + event-themed items.

═══════════════════════════════════════════

## ROUND 6 — Seasons, Leagues & Competitive Ranking

**Goal**: Introduce a seasonal cadence (e.g. 8-week seasons) with leagues
(Bronze/Silver/Gold/Platinum/Diamond) and a season-reset of ranked
leaderboards. Non-ranked leaderboards (peak power, raid score) persist
across seasons.

**Features**:
- `seasons` collection with `start_at`, `end_at`, `status` (active/closed/preview)
- `league_tier` field on guilds, auto-promoted/demoted at season end
- New endpoints: `GET /api/seasons/current`, `GET /api/seasons/{id}/standings`, `GET /api/seasons/history`
- Season-end "Hall of Champions" snapshot (immutable, append-only)
- Soft-reset of certain weekly/monthly metrics; sticky-peak fields preserved
- UI: SeasonsBanner on Dashboard + League badge next to guild_name on leaderboard

**Hard constraints**:
- NO P2W. Promotion/demotion based purely on raid_score + expedition completion + weekly quest streak.
- NO season-pass that grants gameplay advantages (cosmetics only — gates ROUND 10).

**Technical risks**:
- Atomicity of season-end snapshot (60s migration window).
- Backward compat: existing leaderboard sort must not break.
- Index `(season_id, league_tier, score)` could be large — needs TTL on closed seasons.

**Dependencies**: none (foundation).
**Estimated effort**: **L** (~2–3 weeks).
**Path count delta**: +5 (~76 → 81).
**Files to touch**: `app/seasons/` (new), `app/leaderboard/services.py`, `frontend/src/pages/Seasons.jsx` (new), `frontend/src/components/LeagueBadge.jsx` (new).

═══════════════════════════════════════════

## ROUND 7 — Advanced Consortia & Cooperative PvE

**Goal**: Extend the consortium feature (Round 14.x base) with multi-guild
cooperative PvE — joint raids on "World Bosses" requiring 2–5 guilds.

**Features**:
- World Boss `consortium_raids` collection with shared damage tracking
- Up to 5 guilds × 20 advs = 100 participants
- Loot distribution proportional to damage contribution
- Consortium chat (Phase 19.x-style real-time channel, simple polling)
- Consortium roles (Leader, Officer, Member) with kick/promote permissions
- Audit trail for consortium actions

**Hard constraints**:
- NO P2W: world boss loot is cosmetic + materials only (no power gear).
- NO toxic incentive: no consortium-vs-consortium PvP.

**Technical risks**:
- Chat moderation → REQUIRES ROUND 11 admin tools (mute/ban/profanity filter).
- Concurrency on shared damage counter (atomic `$inc` + audit hash).
- Out-of-sync UI between 100 participants (polling ≥ 5s + ETag caching).

**Dependencies**: ROUND 11 (moderation toolkit) MUST precede.
**Estimated effort**: **XL** (~4 weeks).
**Path count delta**: +10 (~81 → 91).
**Files to touch**: `app/consortia/` (extend), `app/consortium_chat/` (new), `app/world_bosses/` (new), `frontend/src/pages/ConsortiumRaid.jsx` (new).

═══════════════════════════════════════════

## ROUND 8 — Adventurer Progression, Roles & Advanced Classes

**Goal**: Deepen the adventurer system with level-up choices (talent
points), advanced class specializations (sub-classes), and role-specific
abilities used in expedition/raid resolvers.

**Features**:
- Adventurer level cap raised from 10 → 30
- 3 talent paths per class (e.g. Tank → Guardian / Berserker / Sentinel)
- `class_specialization` field, locked-in at level 10
- New `talent_points` resource granted per level-up
- Talent picks influence resolver (Phase 14.5 explainer ingests them)
- Retirement / re-talent mechanic (costs gold + materials, no premium)

**Hard constraints**:
- NO premium re-talent. Cost in gold/materials only.
- Talent imbalance audit: every patch must keep top-talent win-rate ±10%.

**Technical risks**:
- Resolver explainer must enumerate talent impact (UX clarity).
- Migration of existing adventurers (assign default specialization at L10).
- Class-balance regression in Phase 6 power formula tests (already flaky).

**Dependencies**: ROUND 6 (season XP curve).
**Estimated effort**: **L** (~3 weeks).
**Path count delta**: +6 (~91 → 97).
**Files to touch**: `app/adventurers/`, `app/expeditions/resolver.py`, `app/raids/resolver.py`, `frontend/src/pages/AdventurerDetail.jsx` (extend).

═══════════════════════════════════════════

## ROUND 9 — Live Events & Server Narrative

**Goal**: Time-limited "live events" (1–2 weeks) with unique dungeons,
event currencies, and a server-wide narrative ("Lanafuoco awakens",
"The Silver Crusade rides", etc.).

**Features**:
- `events` collection with `start_at`, `end_at`, `event_dungeons[]`
- Event-only currency (e.g. "Stelle del Vespro") tradeable for cosmetics
- Server-wide narrative ticker on landing page
- Push notifications via email (opt-in) for event start/end (uses Phase 9 SMTP)
- Event Hall of Fame snapshot per event

**Hard constraints**:
- NO event power-gear (cosmetics + reputation badges only).
- Event currency cannot be converted to gold or vice-versa.

**Technical risks**:
- Scheduling: event spawn relies on ROUND 6 season cadence.
- Cron-like job needed (FastAPI + APScheduler or external worker).
- Narrative i18n keys: each event ships with IT+EN copy.

**Dependencies**: ROUND 6 (season triggers).
**Estimated effort**: **M** (~2 weeks).
**Path count delta**: +4 (~97 → 101).
**Files to touch**: `app/events/` (new), `app/scheduler/` (new), `frontend/src/components/EventBanner.jsx` (new).

═══════════════════════════════════════════

## ROUND 10 — Fair Monetization & Cosmetic Identity

**Goal**: Introduce optional monetization that respects the no-P2W
constraint: cosmetic guild crests, custom guild banners, name color
chips, animated avatar frames. Backed by **real Stripe** integration
(test key already in pod env).

**Features**:
- Cosmetic shop `cosmetics` collection (catalog)
- `guild_cosmetic_inventory` per guild
- Stripe Checkout / Payment Intent integration
- One-time purchases (no subscriptions in v1)
- Refund window 7 days, Stripe webhook handler
- Cosmetics are PURELY visual (no stat / power / loot impact)

**Hard constraints**:
- ❌ NO P2W: zero gameplay advantage from any purchase.
- ❌ NO loot boxes / gacha mechanics.
- ❌ NO season pass that gates content (only cosmetic season pass allowed).
- Refunds honored within 7 days without questions.

**Technical risks**:
- Payment compliance (PCI-DSS handled by Stripe but audit trail required).
- Currency-display localization (€/$/£/etc.).
- Webhook idempotency (retry storms must not double-credit cosmetics).
- Anti-fraud: refund abuse mitigation needs admin review (→ ROUND 11).

**Dependencies**: ROUND 6 (season pass cosmetic), ROUND 9 (event-themed cosmetics), ROUND 11 (refund admin tools).
**Estimated effort**: **XL** (~4 weeks).
**Path count delta**: +8 (~101 → 109).
**Files to touch**: `app/cosmetics/` (new), `app/payments/` (new, Stripe), `frontend/src/pages/Shop.jsx` (new), `frontend/src/components/CosmeticPreview.jsx` (new).

═══════════════════════════════════════════

## ROUND 11 — Admin, Moderation & Ops Dashboard

**Goal**: First-class admin tools for moderating chat, refunding
purchases, banning bad actors, inspecting audit trails, and running
ops jobs (cleanup, leaderboard re-sync, season transition).

**Features**:
- Admin Dashboard (separate `/admin/*` UI) — already partial scaffolding
- Chat moderation: mute/ban/report queue
- Refund admin panel (Stripe-aware)
- Audit trail viewer (read-only, with filters by event_type)
- Manual leaderboard re-sync trigger
- Test-account flagging UI (replace manual Python scripts)
- Read-only "leaderboard preview" before season close

**Hard constraints**:
- All admin actions logged in `audit` collection with reason text.
- No silent ops: every cleanup batch produces a downloadable JSON backup
  (already established pattern, see `/app/memory/db_*_backup.json`).

**Technical risks**:
- Authorization: admin endpoints must enforce `is_admin=True` + 2FA (future).
- Frontend bundle size: separate admin chunk via code-split.
- Audit log retention vs storage growth (TTL or cold storage).

**Dependencies**: none (can ship in parallel with ROUND 6, but must precede ROUND 7 chat and ROUND 10 refunds).
**Estimated effort**: **L** (~3 weeks).
**Path count delta**: +12 (~109 → 121).
**Files to touch**: `app/admin/` (extend heavily), `frontend/src/pages/admin/*` (new), `app/audit/admin_views.py` (new).

═══════════════════════════════════════════

## Suggested cumulative path-count timeline

| Round | After ship | Notes |
|---|---|---|
| Current (post-Phase 19) | 76 | Baseline |
| + ROUND 6 | ~81 | Foundation |
| + ROUND 11 | ~93 | Admin tools (parallel with R6) |
| + ROUND 7 | ~103 | World bosses (needs R11) |
| + ROUND 8 | ~109 | Talent progression |
| + ROUND 9 | ~113 | Live events |
| + ROUND 10 | ~121 | Cosmetic shop |

═══════════════════════════════════════════

## Open questions for user (to lock in before ROUND 6 GO)

1. Season length: 8 weeks (suggested), 4 weeks, or custom?
2. League promotion criteria: pure raid_score or weighted with expeditions + weekly quests?
3. Stripe in ROUND 10: one-time only, or also subscriptions for "founder cosmetic vault"?
4. Chat moderation in ROUND 7: AI-assisted profanity filter (cost) or human-only review (delay)?
5. Localization roadmap: stay IT+EN or open to community translations in ROUND 9?

## NOT in scope (explicit non-goals)

- ❌ Real-money trading of in-game items.
- ❌ NFT or blockchain integration.
- ❌ PvP combat between guilds (only cooperative PvE).
- ❌ Mobile-native app (web-responsive remains the only client).
- ❌ Voice chat (only text-based).
