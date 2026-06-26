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

## Backlog
- **P1** — Frontend test for active streak claim (Test 3) and weekly claim 422 (Test 5)
  — both blocked on simulating a real daily quest completion in browser. Backend
  equivalents already covered.
- **P2** — Surface streak `longest` on profile header (currently only on dashboard).
- **P2** — Mobile app (Expo) parity for streak/weekly UI.
- **P3** — Optional: leaderboard column for longest streak.

## Test Credentials
See `/app/memory/test_credentials.md`. Tester: `tester@orbus.test` / `password123`.
