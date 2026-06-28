# Orbus Online: Guild Master — PRD

## Status (2026-06-28)
- Round 6B.4 (Roster Health, Bound Items, Archive UI) — DONE
- Round 6C (Training Grounds + Specializations) — DONE + WARN P2 (signature visibility) RESOLVED
- Round 6D (Contract Board + Milestones) — DONE
- Round 11.1 (httpOnly cookies migration) — deferred

## Architecture
- FastAPI backend + MongoDB + React frontend
- All routes prefixed `/api`
- Auth: JWT bcrypt (legacy localStorage — migration deferred to 11.1)
- Tester whitelist: tester@orbus.test / password123 (is_admin=True)

## Implemented (cumulative)
- Auth, Guild, Adventurers (recruit/retire), Dungeons, Expeditions, Raids, Inventory, Equipment, Crafting, Forge, Market, Auction, Squads, Chronicle, Consortiums, Chat, Shop, Quests (daily+weekly+streak), Territory (12 structures), Training Grounds + Specializations, Contract Board (daily/weekly/milestones).

## Next Action Items (P0/P1)
- P0: e1_tester final validation Round 6C + 6D
- P1: Unified Guide (Guide.jsx) update for 6B.4 + 6C + 6D
- P1: Round 6E content (next iteration of contracts pool, milestones T2/T3)
- P2: httpOnly cookie migration (Round 11.1)
- P2: pytest xdist race fixes
