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

---

## Round 11.2 TASK 6 — Completed 2026-06-28

**Scope**: Guide player-facing + ADMIN_OPS.md + Addendum G1-G4 (Traits/Stats data-driven APIs + UI).

**Implemented**:
- Backend: `GET /api/traits/catalog` + `GET /api/stats/catalog` (public, no auth, PII-safe).
  Filters: `is_active != False AND is_test != True`. Polarity mapping (positive/negative/mixed).
- `/app/backend/app/catalog/{__init__,routes}.py` + `/app/backend/app/stats/public_catalog.py` (11 stats).
- Router registered in `app_factory.py`.
- Frontend: `Guide.jsx` aggiornato a 22 sezioni: aggiunte `7. Statistiche (catalog)` e `8. Tratti (catalog)` data-driven con lazy fetch on tab click + filtri client-side (q, polarity, rarity).
- Docs: `/app/memory/ADMIN_OPS.md` (accesso, endpoint admin, limiti, audit, bootstrap prod, esempi curl Bearer + Cookie+CSRF).
- Tests: `backend_round112_t6_catalog_test.py` (5 backend, 100% pass) + 7 frontend acceptance (testing agent iteration_13, 100% pass).

**Pending (P0)**: TASK 7 — Regression sweep 17-points (awaiting explicit user GO).
**Pending (P1)**: Post-deploy monitoring `auth.legacy_bearer_usage` (14gg), Bearer fallback cleanup.
**Pending (P2)**: `is_unlocked` on training catalog, `guilds.public_id` materialized index (Admin search O(n) → O(1)).

---

## Round 16.1 Phase 2 — Completed 2026-06-30

**Scope**: Roster filters/sort + Dungeon Preview narrato + Report "Perché è andata così".

**Backend**:
- `GET /api/adventurers` — added query params (`class_slug`, `spec_slug`, `role`, `race_slug`, `improvable_equip`, `no_spec`, `ready_for_dungeon`, `sort`) with in-process filter/sort overlay (`/app/backend/app/adventurers/routes.py`).
- `GET /api/dungeons/{slug}/preview?team_ids=...` — new endpoint returning `{dungeon, team_power, success_chance, injury_risk, threats[], threat_resolution, rewards_preview, weakness_suggestion_it/_en, caps_info}`. Source: `/app/backend/app/dungeons/preview.py`.
- `_build_why_narrative(lang, …)` in `/app/backend/app/expeditions/report_builder.py`. The builder now emits `report_summary.narrative_it` and `narrative_en` (≤600 chars each).

**Frontend**:
- `/app/frontend/src/components/RosterFilterBar.jsx` — sessionStorage-persisted bilingual filter/sort toolbar (class, role, improvable_equip, no_spec, ready_for_dungeon, sort).
- `/app/frontend/src/components/DungeonPreviewModal.jsx` — pre-launch narrated preview modal triggered from ExpeditionNew (button `btn-narrated-preview`). Mobile-friendly, bilingual, no spoilers.
- `/app/frontend/src/pages/Adventurers.jsx` — refetches with query params, renders RosterFilterBar, handles "no filter results" state.
- `/app/frontend/src/pages/ExpeditionNew.jsx` — added "✦ Narrated preview" button + modal that confirms expedition.
- `/app/frontend/src/pages/ExpeditionReport.jsx` — new `WhyNarrativeSection` (`details/summary`) shows `narrative_it`/`narrative_en` based on active language.

**Tests**:
- `backend/tests/backend_round161_phase2_test.py` — 7 tests (all pass): class filter, improvable_equip subset, power_desc sort, preview void dungeon threats, preview non-void empty threats, narrative bilingual unit, narrative on completed expedition.

**Constraints honored**: no balancing/economy changes, no localStorage for filters, IT+EN coverage on every new player-facing string.

**Pending (next)**: Round 16.1 Phase 3 — Class Hall espansa + Auto-Equip migliorato + Empty States + Guida.
