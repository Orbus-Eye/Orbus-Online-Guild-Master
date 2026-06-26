# Orbus Online: Guild Master — PRD

## Original Problem (Phase 15 + 14.1)
Implement **Phase 15** (Daily Streak Counter) and **Phase 14.1** (Weekly Quest Variety)
to improve player retention. Requires server-authoritative streak calculation,
new daily/weekly quest tracking, moderate anti-inflationary rewards, strict audit
logging, and **no pay-to-win** elements.

## Architecture
- Backend: FastAPI (Python 3.11), Motor (async MongoDB), JWT auth, pytest.
- Frontend: React 18, react-router, Tailwind, shadcn/ui, custom i18n (it/en).
- Mongo: stand-alone preview cluster (no transactions) — every multi-doc mutation
  uses conditional `find_one_and_update` / `$inc` patterns + manual revert.
- Hosted: Preview at `guild-master-5.preview.emergentagent.com`, Production at `orbusonline.net`.

## Core Requirements (static)
- Atomic, server-authoritative streak + quest state.
- Idempotent claim endpoints (409 on duplicate).
- UTC reset (daily midnight, weekly ISO-Monday).
- Audit log for every reward claim.
- No reputation reward from daily/weekly quests.
- No competitive gear reward from quests.
- No premium / pay-to-win mechanic.

## Reward Economy (binding, locked by product)
| Layer | Tier | Reward |
|---|---|---|
| Daily Streak | D1 | 20g |
| Daily Streak | D3 | 50g + iron_shard×2 |
| Daily Streak | D5 | 100g + arcane_dust×1 |
| Daily Streak | D7 | 200g + healing_herb×3 |
| Streak cap | — | Soft cap 30 days; cycles weekly past D7 |
| Weekly quest | each | 80-180g + 1-2 common/uncommon materials |
| Weekly cap | per week | ~700g theoretical maximum |

## Personas
- **Casual returner**: logs in 1-3x/week. Benefits from streak forgiveness (gap≤1d).
- **Daily player**: completes all 3 daily quests, builds streak D1→D30.
- **Market trader**: buys/sells items; gets credit for both via weekly quests.
- **Crafter / Equip-focused**: crafts items / equips loot; covered by weekly hooks.

## What's Been Implemented (2026-06-26)
- ✅ Streak endpoints: `GET /api/quests/streak`, `POST /api/quests/streak/claim/{tier}`
- ✅ Weekly endpoints: `GET /api/quests/weekly`, `POST /api/quests/weekly/claim/{slug}`
- ✅ Weekly progress hooks in: expeditions, crafting, market (listing/buy), equipment.
- ✅ Audit events: `streak_updated`, `streak_reward_claimed`, `weekly_quest_claimed`,
  `weekly_rotation_generated`, `quest_reward_claimed`.
- ✅ Frontend components: `StreakBadge.jsx`, `WeeklyQuestsCard.jsx`.
- ✅ Dashboard layout updated (`Dashboard.jsx`).
- ✅ i18n keys (it/en) for streak, weekly, quests.weekly.
- ✅ Test suite: 22 backend pytest (ALL PASS), 10 frontend E2E (7 PASS, 1 PARTIAL, 2 deferred).
- ✅ Regression fix: 3 hardcoded path-count tests updated 49→53.

## Phase 16 (2026-06-26) — Online Feel + Market Fix + Consortiums MVP
- ✅ **Market route fix**: `Market.jsx` destructured non-existent `{token, loading}` from
  AuthContext → useEffect always triggered `navigate("/login")` → GuestOnly bounced to
  `/dashboard`. Replaced with `{user, guild}` (already gated by ProtectedRoute).
- ✅ **Server Chronicle** (`GET /api/chronicle?limit=&lang=`): public read-only activity
  feed derived from `audit_log`. Sanitization filters: no email, no user_id/ObjectId,
  no test guilds (`^Test`, `^G[\s_]<hex>`), no test owners (is_test_user OR
  `@orbus.test`/`@*.test`/`test@*`/`@test.*`). Whitelist of 6 public event types.
  Rarity-gated (Uncommon+) for `item_crafted`/`loot_awarded`.
- ✅ **Consortiums MVP** (`/api/consortiums*`): 6 endpoints. Cross-guild social groups.
  Constraints: 1 user/1 guild = 1 consortium, name 3-40 unique case-insensitive,
  no Test* prefix, no forbidden chars (`@<>\/`). Open join, no chat. NO bonus to
  gold/XP/loot/reputation/ranking. Audit events `consortium_created`, `consortium_joined`,
  `consortium_left`.
- ✅ Frontend: `ChronicleCard.jsx`, `Consortiums.jsx`, AppHeader nav link, App.js route.
- ✅ Test suite Phase 16: 11/11 backend tests PASS. Cross-suite regression: 72/72 PASS.
- ✅ OpenAPI path count: 53 → 60 (+1 chronicle, +6 consortiums).

## Backlog
- **P1** — Frontend test for active streak claim (Test 3) and weekly claim 422 (Test 5)
  — both blocked on simulating a real daily quest completion in browser. Backend
  equivalents already covered.
- **P2** — Surface streak `longest` on profile header (currently only on dashboard).
- **P2** — Mobile app (Expo) parity for streak/weekly UI.
- **P3** — Optional: leaderboard column for longest streak.

## Test Credentials
See `/app/memory/test_credentials.md`. Tester: `tester@orbus.test` / `password123`.

## API Contract Pinning
The full API contract for Phase 15 + Phase 14.1 is locked in
**`/app/memory/SPEC_PHASE15_PHASE14_1.md`**.

🔒 **Canonical field name**: the weekly quest threshold field is **`objective_target`**
(NOT `target`). Renaming it would break the frontend (`WeeklyQuestsCard.jsx`), the
22 backend pytest assertions, and any external API consumer. The naming convention
`objective_*` is paired with `objective_type` and MUST be preserved for any future
weekly-quest field.

---

## Phase 17 — ROUND 4: Equipment & Loot Advanced (2026-06-26)

### What's implemented (preview only, NOT deployed to prod)
- ✅ **Forge / Workshop**: 4 operations on per-instance inventory rows.
  - `POST /api/inventory/{instance_id}/refine` — +1 refinement with locked curve
    (100% rate at +1 → 8% at +10), cost gold + iron_shard/arcane_dust/dull_gem/dragon_essence.
  - `POST /api/inventory/{instance_id}/enchant-options` — 3-5 weighted enchant choices
    by item rarity (Q5 LOCKED: player picks).
  - `POST /api/inventory/{instance_id}/enchant` — apply chosen enchant.
  - `POST /api/inventory/{instance_id}/reroll-affixes` — escalating cost
    50/150/400/1000/2500, HARD CAP 5 per item.
  - `POST /api/inventory/{instance_id}/disenchant` — guaranteed materials by rarity
    + weighted random bonus; soft-delete via `disenchanted_at` (audit retention).
- ✅ **BoE (Bound-on-Equip) market guard** (Q8 LOCKED, CRITICAL):
  refine / enchant / reroll auto-set `inventory_items.is_bound=True`;
  `POST /api/market/listings` rejects bound rows with HTTP 422 + detail
  `market.bound_item_not_sellable`. Frontend resolves via i18n key `market.error_bound_item`.
- ✅ **Set bonuses & equipment-detail**:
  - `GET /api/sets`, `GET /api/enchants` (public lists).
  - `GET /api/adventurers/{id}/equipment-detail` returns slots + set_progress + active_bonuses.
  - Tier-based bonuses (3/5 pieces — Q3 LOCKED).
- ✅ **Seeds (idempotent on every boot)**: 3 item sets (drake_slayer / arcane_adept / goblin_hunter),
  13 enchants (Common→Epic), 1 new material `dragon_essence`, 5 Legendary baseline items.
- ✅ **Migration additive/idempotent**: all `inventory_items` rows back-filled with
  `instance_id`, `is_bound=False`, `refinement_level=0`, `enchants=[]`, `affixes=[]`,
  `reroll_count=0`, `disenchanted_at=None`. All `items` get `slot_type` + `set_id` +
  `max_refinement` + `enchant_slots` + `affix_pool_tag` defaults.
- ✅ **Frontend**: new `/forge` page (4 tabs), Inventory BOUND badge + tooltip +
  "Vai a Officina" link, AdventurerEquipment "BONUS SET ATTIVI" panel, Market i18n
  toast for 422 BoE, i18n IT+EN keys added.
- ✅ **Path count**: 61 → **69** (+8 endpoints).
- ✅ **Tests**: new `backend_phase17_round4_test.py` (28/28 PASS in 44.92s).
  Cross-suite regression: legacy tests updated to path 69; all 77/77 PASS for
  Phase 14.x + 16.

### Frontend testids added (canonical)
`nav-forge`, `forge-title`, `forge-tab-{refine|enchant|reroll|disenchant}`,
`forge-item-{instance_id}`, `forge-confirm-{tab}`, `forge-enchant-option-{slug}`,
`forge-enchant-options`, `inv-bound-badge-{row_id}`, `inv-goto-forge-{row_id}`,
`set-bonuses-panel`, `set-bonus-{slug}-{pieces}`, `set-progress-{slug}`,
`set-bonuses-empty`.

### Locked decisions ribadite (NON deviare in P18+)
- ❌ NO Mythic rarity in ROUND 4.
- ❌ NO item break/destroy on refinement failure.
- ❌ NO refund of gold on disenchant.
- ❌ NO ALLOWLIST changes.
- ❌ NO leaderboard formula tampering (set bonuses are runtime-only, not persisted on `max_team_power_ever`).
- ❌ NO real-money item purchase.
- ❌ NO premium boost.
- ✅ Bound items can NEVER be listed on market (frontend + backend dual enforcement).

### Backlog ROUND 4
- **P0** — User validation of /forge UI in preview, then redeploy prod with explicit confirm.
- **P1** — UI Tooltip upgrade from `title=` to shadcn `<Tooltip>` for richer BoE hover.
- **P2** — Weekly quest hook `weekly_refine_items_3` / `weekly_enchant_items_2`
  (deferred, optional).
- **P2** — Affix random-roll on drop generation (currently affixes only appear via reroll
  on previously-affixed items; baseline drops are not yet affix-tagged in the loot table).
- **P3** — Mobile app (Expo) parity for Forge.
- **P3** — Forge log feed (recent operations history on /forge page).


---

## Phase 17.5 + 18 — ROUND 5: Team Size 5 + Solo Raids (2026-06-26)

### What's implemented (preview only, NOT deployed to prod)
- ✅ **Starter roster auto-pop** (`/app/backend/app/onboarding/services.py`):
  ensures every guild owns ≥5 advs. Idempotent; back-fill on lifespan boot
  covered 8788 advs across 2040 legacy guilds.
- ✅ **12 new 5p dungeons** (T1×3, T2×3, T3×3, T4×3 — `required_team_size=5`).
- ✅ **10 legacy dungeons** flagged `is_legacy=True`, kept at `required_team_size=3`.
- ✅ **+25% power bump** applied ONCE on 7 legacy T2/T3 dungeons (idempotent
  via `power_bumped: True` sentinel). T1 untouched.
- ✅ **dungeon_public** exposes `is_legacy`, `is_5p`, `power_bumped`, `tier_label`, `tags`.
- ✅ **guild_public** exposes `max_raid_score`, `last_raid_completed_at`,
  `raids_completed_count`, `raids_victory_count` (additive).
- ✅ **Raids module** (`/app/backend/app/raids/__init__.py`) — 6 endpoint:
  `GET /api/raids/catalog`, `POST /api/raids/preview`, `POST /api/raids/start`,
  `POST /api/raids/{id}/complete`, `GET /api/raids`, `GET /api/raids/{id}`.
- ✅ **3 raid_dungeons** seeded: `broken-bastion-siege`, `necropolis-bells`,
  `dragon-vault`.
- ✅ **Cooldown 15min per guild** (`raids.cooldown_active` sentinel detail).
- ✅ **Compound unique index** `raid_participants (raid_id, adventurer_id)`
  → DB-level anti-duplicate across parties.
- ✅ **dragon_essence drop sources**: T4 5p (in roadmap loot_tables) + Raid completion
  guaranteed (1-3 or 2-5 by tier, scaled by outcome multiplier).
- ✅ **max_team_power_ever NOT touched by raids**; `max_raid_score` separate metric.
- ✅ **Audit events new**: `starter_roster_seeded`, `dungeon_power_bumped`,
  `raid_started`, `raid_completed`.
- ✅ **Frontend Raids page** (`/app/frontend/src/pages/Raids.jsx`) with cooldown
  banner + 3 raid card + roster gate + history.
- ✅ **Nav link `RAID`** in AppHeader + i18n `nav.raids` IT/EN.
- ✅ **Path count**: 69 → **75** (+6).
- ✅ **Tests**: new `backend_phase17_5_round5_test.py` (20/20 PASS, 31s).
  Cross-suite: 14.x + 16 still 77/77 PASS.

### Locked decisions (§I of `/app/memory/ROUND_5_BRIEF.md`)
1. Starter roster auto-pop 5 ✅
2. Legacy dungeons keep team=3 ✅
3. T4 Legendary 5% (in roadmap loot table) ✅
4. dragon_essence from T4 + raid only ✅
5. max_raid_score separate metric ✅
6. +25% rec_power only T2/T3 legacy ✅
7. Cooldown 15min per-guild ✅

### Out of scope / Deferred to Phase 18.1+
- ⏳ **Raid Builder UI** (4 party × 5 picker). Backend endpoint `POST /api/raids/start`
  fully functional via API; UI builder will land in Phase 18.1.
- ⏳ **Raid Report multi-party UI** (`/raids/:id`). Backend `GET /api/raids/{id}` returns
  complete shape; UI consumer pending.
- ⏳ **T4 5p custom loot_tables curve** (Common 5/Uncommon 25/Rare 35/Epic 30/Legendary 5).
  Currently T4 dungeons inherit default loot pool. Phase 18.1 will extend
  `loot_tables.py` with explicit 5p curves.
- ⏳ **Weekly quest hooks raid**: `raid_completed_weekly`, `t4_5p_completed_weekly`.
- ⏳ **Leaderboard raid view** (`GET /api/leaderboard/raids` sorted by `max_raid_score`).

### Risks under monitoring
1. **Raid runtime**: `_outcome_for_chances` uses `random.Random(raid_id)` for
   deterministic replay-safe rolls. If same raid_id is replayed → same outcome.
   Mitigation: idempotent guard at start blocks `in_progress` concurrency.
2. **dragon_essence inflation**: 1-3 per raid + 2-5 from T4 raid. ~5-15 essence/week
   for active player. Forge consumes 3 for +10 refine. Acceptable.
3. **Starter roster recursion**: `create_guild → ensure_starter_roster` is wrapped
   in `try/except` to never block guild creation if seed data missing.
