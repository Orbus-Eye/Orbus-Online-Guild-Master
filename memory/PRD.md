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

---

## Round 16.1 Phase 3 — Completed 2026-06-30

**Scope**: Class Hall espansa + Auto-Equip migliorato (bilingual reasons) + Empty States audit + Guida estesa.

**Backend**:
- `/app/backend/app/class_halls/services.py` — added `enrich_halls_for_ui()` (adventurers_of_class, available_to_specialize, top_adventurers[:3], specializations[3] bilingual, bonuses[] placeholder, unlock_hint_it/en). BASE_CLASS_SLUGS expanded to 11 (alchemist added). SPECS_BY_CLASS constant exposed.
- `/app/backend/app/class_halls/routes.py` — `GET /api/class-halls` now returns `{halls, base_classes, kpi}` with `kpi: {halls_unlocked, halls_total, specs_unlocked, specs_total}`.
- `/app/backend/app/equipment/auto_equip.py` — response extended with `reasons[]` (slot, old/new item, stat_delta, primary_gain, reason_it, reason_en), `unchanged_slots_detail[]` (slot, reason_it, reason_en), `score_delta`, `primary_stat`, bilingual `warnings_it/en`. Backwards-compatible.

**Frontend**:
- `/app/frontend/src/pages/ClassHalls.jsx` — full rewrite, bilingual IT/EN via I18nContext, KPI top right, Top Members list, no-spec hint, specializations grid with role badge + unlockable state, ACTIVE BONUSES placeholder, empty-state CTA.
- `/app/frontend/src/components/AdventurerDetailModal.jsx` — bilingual `AutoEquipReport` inline panel after click. Shows Power before→after with colored delta, structured reasons (per slot) with stat_delta breakdown, unchanged slots reasons, and empty CTA.
- `/app/frontend/src/pages/Expeditions.jsx` — empty state now bilingual (Italian + English).
- `/app/frontend/src/pages/Recruitment.jsx` — freeze-bench and all-recruited empty states now bilingual.
- `/app/frontend/src/pages/guide/R161GuideSections.jsx` (NEW) — 3 new sections: Cosa fare ogni giorno, Come scegliere un team dungeon, Filtri e ordinamento del roster (bilingual). Registered in `_shared.jsx` SECTIONS + wired in `Guide.jsx`.

**Tests**: `backend/tests/backend_round161_phase3_test.py` — 6 tests, all pass:
1. class-halls returns 11 halls with all new fields + kpi
2. auto-equip carries bilingual reasons + score_delta
3. auto-equip idempotent (2nd call → 0 swaps)
4. KPI totals match halls/specs counters
5. /api/expeditions list shape (empty-state contract)
6. unlock-specialization is idempotent

**Pytest count (Round 16.x bundle)**: phase1=8, phase2=7, phase3=6, round160_phase4=16 → 37/37 PASS

**Empty states audited & bilingualized (≥6 pages)**:
1. `/adventurers` — no-filter-results (NEW)
2. `/recruitment` — bench empty + all-recruited (bilingual)
3. `/inventory` — already CTA dungeon (R14.v3, OK)
4. `/expeditions` — bilingual + CTA dungeons
5. `/raids` — pre-existing, OK
6. `/class-halls` — recruitment CTA when no halls unlocked
7. `/auto-equip` modal — "no better item available" bilingual

**Pending (next, Phase 4)**: Test 17 checklist + report 17 punti consolidated.

---

## Round 16.1 Phase 4 — Completed 2026-06-30 — ROUND 16.1 CLOSED

**Scope**: Stabilizzazione e validazione del Round 16.1 (no nuove feature).

**Verifiche eseguite**:
- Checklist 17 punti completata: 17/17 PASS.
- Pytest R16.1 bundle (phase1+2+3 + phase14_4): 26/26 PASS.
- Frontend lint: 0 errors, 6 warnings cosmetici.
- Regression smoke: dashboard endpoints, recruitment (no deprecated), classes catalog (11 base), mobile nav, auto-equip compatibility.

**Fix applicati**:
1. `tests/backend_phase14_4_round15_test.py::test_round15_introduces_no_new_endpoints` — convertito da hard-coded count a baseline snapshot file `tests/baselines/openapi_paths_round161.txt` (155 paths). Test ora drift-resistant.
2. `frontend/src/pages/guide/R16GuideSections.jsx` — 7 apostrofi escapati per pulire lint.
3. Test credentials: account `clean_onboarding@orbus.test` aggiunto in `/app/memory/test_credentials.md`.

**Conferme esplicite**:
- ❌ Nessun hard delete eseguito.
- ❌ Nessuna modifica a economia / drop / XP / PvP / bilanciamento.

**Endpoint nuovi R16.x bundle** (rispetto a R15):
- `/api/class-halls`, `/api/class-halls/{slug}/unlock-specialization`
- `/api/dungeons/{slug}/preview`
- `/api/dashboard/{suggestions,onboarding,daily-loop}` + claim/dismiss

**Raccomandazione next round**: **R16.A — Achievement Hooks** (massimo ritorno percepito + zero rischio bilanciamento + chiusura naturale del Game Clarity Pass).

**Report finale**: `/app/memory/round161_final_report.md`.

---

## Round 16.A Phase 1 — Achievement Trigger Emission Layer (in progress, 2026-06-30)

**Goal**: emit the 11 trigger_event values previously declared in the achievement catalog. Pure wiring — no new features, no economy/reward changes.

**Centralised emitter**: `backend/app/achievements/trigger_emitter.py::emit_achievement_trigger` — delegates to existing `evaluate_achievements` engine, logs structured, supports optional `idempotency_key` (writes to `trigger_emissions` collection for trace + dedup).

**Wiring map (11 events, 10 WIRED + 1 DEFERRED)**:

| # | Event | Status | File |
|---|---|---|---|
| 1 | `item_crafted` | ✅ WIRED | `crafting/services.py::craft_recipe` |
| 2 | `market_purchase` | ✅ WIRED | `market/services.py::buy_listing` (buyer) |
| 3 | `auction_purchase` | ✅ WIRED | `market/services.py::buy_listing` (buyer, alias) |
| 4 | `auction_sale` | ✅ WIRED | `market/services.py::buy_listing` (seller, gated `flips_to_sold`) |
| 5 | `consortium_joined` | ✅ WIRED | `consortiums/services.py::join_consortium` |
| 6 | `season_league_reached` | ✅ WIRED | `pvp/services.py::_apply_rating` (when `highest_league` advances) |
| 7 | `leaderboard_rank_reached` | ⏸ DEFERRED | leaderboard ranks computed on-demand; no per-guild rank-update hook |
| 8 | `item_disenchanted` | ✅ WIRED | `forge/services.py::disenchant_instance` |
| 9 | `material_purchased` | ✅ WIRED | `market/services.py::buy_listing` (when `item_type == "material"`) |
| 10 | `pvp_match_completed` | ✅ WIRED | `pvp/services.py::_apply_rating` (both attacker & defender, `outcome` in payload) |
| 11 | `territory_upgraded` | ✅ WIRED | `territory/services.py::upgrade_structure` |

**Tests**: `backend/tests/backend_round16A_phase1_test.py` — 14 passed, 1 skipped (DEFERRED).
**Regression**: R16.1 P1+P2+P3 + Phase14.4 + dev-seed = 27/27 PASS. Total **41 passed, 1 skipped**.

**Design decisions**:
- **Dedup**: optional `idempotency_key` upserted into `trigger_emissions` for trace only. Engine's existing CAS on `achievement_progress` is the real dedup. The collection gives us an inspectable audit trail for debugging.
- **Auction = Market**: same backing service. Fire both `market_purchase` and `auction_purchase` for the buyer (catalogs separate them).
- **PvP outcome**: fired for BOTH sides per user instruction. Idempotency key = `{match_id}:att` / `{match_id}:def`.

**Vincoli rispettati**: NO modifiche a economia / drop / XP / PvP / bilanciamento / reward achievement / valori catalog.
