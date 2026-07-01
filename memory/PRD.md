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

---

## Round 16.A Phase 2 — Audit Bridge (achievement+xp+onboarding.graduated) — 2026-06-30

**Scope**: scope ridotto rispetto a R16.B "full" (3 audit event vs 6). Wiring solo dei seguiti:
- `achievement_unlocked` (sostituisce legacy `audit_logs.achievement_completed` su collection sbagliata)
- `guild_xp_gained` (emesso da nuovo helper canonico `add_guild_xp`)
- `onboarding_graduated` (one-shot CAS sulla guild on false→true transition)

**Architettura**:
- Riusa **collection `audit_log` esistente** + helper `write_audit` (non bifurca con un secondo store).
- 3 nuovi `event_type` aggiunti all'allowlist (`audit/log.py`).
- Engine refactor: vecchio `_audit_completion` ora scrive su `audit_log` canonical (era `audit_logs` plural, collection orfana).
- Nuovo helper `add_guild_xp(db, guild_id, amount, source, source_id, points_delta=0)` in `achievements/engine.py`:
  - Atomic `find_one_and_update($inc)` + level recompute (logica identica al legacy `_apply_reward`).
  - Emette `guild_xp_gained` audit event quando `amount != 0`.
  - `_apply_reward` ora è un thin shim che chiama `add_guild_xp` con `source="achievement_unlock"`.
- `onboarding_graduated`:
  - CAS atomico `find_one_and_update({"id":gid, "onboarding_graduated_at": None}, {"$set":{"onboarding_graduated_at":now}})` garantisce 1-shot.
  - **No backfill retroattivo**: gilde già `dismissed_implicit=True` PRIMA di Phase 2 verranno marcate al primo hit sul dashboard endpoint (graceful — l'evento è "per il futuro", non per la storia).

**File modificati**:
- `backend/app/audit/log.py` — 3 nuovi event_type in allowlist.
- `backend/app/achievements/engine.py` — `_audit_completion` riscritto + nuovo `add_guild_xp` + `_apply_reward` shim + `trigger_event` passato dall'engine.
- `backend/app/dashboard/routes.py` — CAS + audit emit in `get_dashboard_onboarding`.
- `backend/tests/backend_round16A_phase2_test.py` — 7 test (T01-T07), tutti pass.

**Test result**: 7/7 PASS Phase 2 · 48 passed + 1 skipped (DEFERRED) totale R16.A+R16.1+phase14_4+dev_seed.

**Conferme vincoli**:
- ❌ Nessuna modifica a `guild_xp_reward` / valori catalog achievement.
- ❌ Nessun hard delete.
- ❌ R16.B (3 audit event restanti: MATERIAL_DROPPED, ADVENTURER_XP_GAINED, LEADERBOARD_SCORE_UPDATED) NON in scope.
- ❌ Phase 3 (admin read-only) NON iniziata.
- ✅ Tutti 3 event idempotenti (CAS-protected).


## Round 16.A Phase 3 — Admin Read-Only Audit Dashboard — 2026-06-30 — **ROUND 16.A CLOSED ✅**

**Scope**: Admin dashboard read-only + sweep XP spedizioni + E2E verification + sigillo R16.A.

**Cosa è stato fatto**:
- 3 nuovi endpoint sotto `/api/admin/audit/*` (gated `get_admin_user`):
  - `GET /api/admin/audit/trigger-emissions` (feed Phase 1 con filtri + paginazione).
  - `GET /api/admin/audit/events` (feed Phase 2 whitelist-guarded su `event_type ∈ {achievement_unlocked, guild_xp_gained, onboarding_graduated}`).
  - `GET /api/admin/audit/summary?window_hours=N` (KPI aggregati, clamp interno `min(N, 720h)`, espone `window_clamped: bool`).
- Frontend: nuova pagina `pages/AdminAudit.jsx` (3 tab IT: Riepilogo / Emissioni Trigger / Timeline Audit) su `/admin/audit`, linkata da `AdminOps.jsx`.
- Sweep `add_guild_xp` su `app/expeditions/services.py`: verificato statico (0 occorrenze `guild_xp`, no-op). Sweep code path residue (quests, contracts, seasons) schedulato per R16.B.
- 2 E2E pytest aggiunti (`test_e2e_tester_advanced_emits_onboarding_graduated_once`, `test_e2e_new_player_full_flow`).

**File principali**:
- `backend/app/admin/audit_routes.py` (NEW, 216 righe).
- `backend/tests/backend_round16A_phase3_test.py` (NEW, 10 test inclusi 2 E2E).
- `frontend/src/pages/AdminAudit.jsx` (NEW, 420 righe).
- `frontend/src/App.js` (route `/admin/audit` mounted).
- `frontend/src/pages/AdminOps.jsx` (link audit dashboard).

**Verification finale**:
- pytest R16.A P3: 10/10 PASS.
- Suite estesa (R16.1 P1+P2+P3 + R16.A P1+P2+P3 + Phase 14.4 + dev-seed): **58 passed, 1 skipped, 0 failed**.
- E2E browser `e1_tester`: **3/3 PASS** (admin gate, idempotenza onboarding, whitelist filter).
- Totale: **60 test PASS** (58 backend + 3 E2E browser, 1 skipped feature-gated).

**Conferme vincoli**:
- ❌ Nessun deploy.
- ❌ Nessuna modifica a economia/XP/drop rate/balancing.
- ❌ Nessun hard delete.
- ❌ R16.B (`material_dropped`, `adventurer_xp_gained`, `leaderboard_score_updated`) NON iniziato.
- ✅ Round 16.A **OFFICIALLY CLOSED** post verifica E2E.

**Raccomandazione next round**: **R16.B — Audit Coverage Extension + Sweep XP Round 2** (aggiungere 3 audit event mancanti, sweep `add_guild_xp` su quests/contracts/seasons, persistere `leaderboard_snapshots`). Stima 1.5-2gg dev + 0.5gg test. R16.C (QoL polish — smooth-scroll guide, lock-in spec UI, CSV export admin audit) resta P2.


---

## Round 16.3 Phase 1 closed & Phase 2 ready-to-verify — 2026-07-01

**Phase 1 (World Boss V1 Alveora)** — 🟢 CLOSED ✅. 10 endpoint idempotenti CAS + on-visit fallback + recovery CLI. 21 test PASS + 1 skipped by design. Whitelist audit R16.A esteso con 7 event UPPERCASE `WORLD_BOSS_*`.

**Phase 2 (Mondo & 8 Mastocontinenti V1)** — 🟡 READY-TO-VERIFY:
- Backend `app/world/__init__.py` (~460 righe): seed 8 continenti (`ambash/velur/soe/efreto/irthe/nathos/ergolat/aveol`), access gate via primo raid completed, cooldown 30gg UTC su change, CAS active→archived, NO hard delete.
- 9 endpoint: `/api/world/{overview,continents,continents/{slug},continents/{slug}/join,continents/{slug}/change,neighbors}` (6 public) + `/api/admin/world/{continents-stats,dev/grant-first-raid/{gid},continents/{slug}}` (3 admin, 403 non-admin).
- 3 nuovi audit event UPPERCASE (`WORLD_CONTINENT_JOINED/CHANGED`, `WORLD_ACCESS_GRANTED`) in `EVENT_TYPES` + `AUDIT_EVENT_WHITELIST`.
- Frontend mobile-first: `pages/World.jsx` (3 branch), `pages/WorldContinent.jsx`, `pages/WorldNeighbors.jsx`, `components/WorldMiniCard.jsx` in Dashboard V2, nav "Mondo" macro-sezione dopo Missioni con badge NEW. Modal cooldown 30gg warning.
- Test: **22 PASS** in `backend_round163_phase2_test.py`. Regression **108 passed / 2 skipped / 0 failed**.
- Vincoli: NO deploy, NO hard delete, NO cambi economia/XP/drop/PvP, NO scheduler globale, NO P2W (puro flavor + social).

**Report**: `/app/memory/round163_phase2_final_report.md` (13 sezioni).
**Roadmap**: Phase 1 → CLOSED, Phase 2 → READY-TO-VERIFY.
**Next**: R16.3 Phase 3 — Eventi continentali admin + Incarichi di Sede (entrate passive con cap).


---

## Round 16.3 Phase 3 ready-to-verify — 2026-07-01

**Phase 3 (Eventi Continentali + Incarichi di Sede V1)** — 🟡 READY-TO-VERIFY:

- Backend 2 moduli: `app/world_events/__init__.py` (12 eventi seed, instances CAS, on-visit expire fallback) + `app/site_contracts/__init__.py` (config singleton, ledger daily unique `(guild_id, day_bucket)`, formula trasparente, claim CAS).
- **12 endpoint** (5 pubblici + 7 admin) sotto `/api/world-events/*` e `/api/site-income/*`. Admin gated 403 non-admin.
- **Formula trasparente**: `min(round((base + level_bonus + reputation_bonus) * (1 + event_mod_pct/100)), hard_cap)`. Config default: base 20, +5/level, cap 500, rep cap 1.2. Sanity: lv 1 = 20 oro/g, lv 10 = 65, hard cap 500 (piccolo vs raid).
- **12 eventi catalog** con 5 modificatori `site_income_pct` (`[-15, +15]`) + 6 flavor + 1 `mission_risk_pct` esposto ma non applicato (preparazione Phase 4-5). Badge UI +/-X% trasparente.
- **5 nuovi audit event** UPPERCASE (`CONTINENT_EVENT_CREATED/ACTIVATED/EXPIRED`, `SITE_INCOME_CLAIMED`, `SITE_INCOME_CONFIG_UPDATED`) in whitelist admin filter.
- **Frontend mobile-first**: `WorldEvents.jsx`, `SiteContracts.jsx`, `SiteIncomeMiniCard.jsx`, `ContinentEventBanner.jsx`. Nav +2 voci con badge NEW.
- **Test**: 28/28 PASS. Regression totale **136/138 PASS · 0 fail** (108 pre-esistenti + 28 nuovi). Zero regressioni.
- **Recovery script**: `app/scripts/expire_stuck_continent_events.py` (dry-run/apply).
- **Cleanup dev**: `app/scripts/reset_test_account_world_state.py` eseguito post-sigillo Phase 2 → tester@ambash pulito.

**Vincoli rispettati**: NO deploy · NO hard delete (T25) · NO scheduler globale · NO P2W · cap conservativi.

**Report finale**: `/app/memory/round163_phase3_final_report.md` (14 sezioni).

**Next**: R16.3 Phase 4 — Risorse continentali (8 slug) + classifiche continentali basiche.


---

## Round 16.3 Phase 4 ready-to-verify — 2026-07-01

**Phase 4 (Risorse Continentali V0 + Classifiche Continentali V0)** — 🟡 READY-TO-VERIFY:

- Backend `app/resources/__init__.py` (~714 righe compact single-file): seed idempotente **8 risorse** (5 epic + 3 rare, una per continente `cristallo_di_ambash/cenere_di_velur/linfa_di_soe/nucleo_di_efreto/osso_di_irthe/seme_di_nathos/frammento_di_ergolat/sigillo_di_aveol`), missioni 30 min / 20 oro / team 3 avv idle esistenti, CAS `_resolve_mission` idempotente, on-visit expiry + CLI recovery. Item mirror in `items` collection con `item_type="material_continental"` per riuso inventory infrastructure.
- **Drop rate CONSERVATIVE**: 3% epic / 5% rare base + max `+10%` bonus da eventi `site_income_pct > 0` (`+2%` per evento attivo). `market_cap_daily_per_guild=3` persistito nel catalog per Phase 6.
- **Classifiche V0**: `resource_gathering_count` + `site_income_total`, 7gg rolling, freschezza 24h, top 20 per continente. Snapshot immutabili in `continent_leaderboard_snapshots`, on-visit compute. **Read-only, ZERO reward economico**.
- **11 endpoint** (7 public + 4 admin), 5 nuovi audit event UPPERCASE (`RESOURCE_MISSION_STARTED/COMPLETED/FAILED`, `RESOURCE_GRANTED`, `LEADERBOARD_SNAPSHOT_COMPUTED`) in `EVENT_TYPES` + `AUDIT_EVENT_WHITELIST`. Admin gated 403 non-admin, dev grant gated `APP_ENV != production`.
- **Frontend mobile-first**: `Resources.jsx`, `ResourceGather.jsx`, `ResourceMissions.jsx`, `ContinentLeaderboards.jsx`. Nav +2 voci (Risorse sotto Gilda, Classifiche sotto Mondo). Badge event modifier trasparente. ESLint clean.
- **Test**: **30/30 PASS** in `backend_round163_phase4_test.py`. Regression bundle R16.x + Phase14.4 + dev-seed: **208 passed / 2 skipped / 2 failed** (le 2 failure sono debito legacy R16.0: 966 gilde senza alchemist hall + 6336 avventurieri senza race_slug, pre-esistenti a Phase 4). Zero regressioni Phase 4.
- **Bug scoperto** (solo test, no produzione): `test_adventurers_released_after_resolve` (T12) riscritto per semantica corretta (lock esplicito + resolve + verifica release). `_resolve_mission` produttivo era già corretto.
- **Task A completato**: 2 WARN Phase 3 chiariti (`level_bonus=15` formula corretta con `guild_level` dinamico; `presence.continent=null` risolto via reset script). Nessun fix codice richiesto.
- **Recovery script**: `app/scripts/recover_stuck_resource_missions.py` (`--dry-run/--apply/--guild-id`).

**Vincoli rispettati**: NO deploy · NO hard delete (T22 + T26 verificano) · NO scheduler globale · NO P2W · NO buff economici da leaderboard · NO cambi economia/XP/drop esistenti · drop rate CONSERVATIVE cap `+10%` event bonus · cross-continent block (T07).

**Report finale**: `/app/memory/round163_phase4_final_report.md` (15 sezioni).

**Next round proposto**: R16.3 Phase 5 — Forgia Leggendaria & Forgia di Arfus (receipts che consumano risorse continentali, legendary BOP `is_tradeable=false`).


---

## Round 16.3 Phase 4 closed (post-verify) — 2026-07-01

**🟢 OFFICIALLY CLOSED ✅** — E2E `e1_tester` 3/3 PASS post-verify. Bug UX su `/api/adventurers` fixato (ora riflette `is_available=False` + `status="resource_gathering"`). Utility `POST /api/admin/resources/dev/complete/{mission_id}` gated APP_ENV. 37/37 pytest (30+7). Regression 215/217 (2 legacy R16.0 debt).

---

## Round 16.3 Phase 5A backend closed — 2026-07-01

**Phase 5A (Forgia Leggendaria) — iterazione 1/2** — 🟡 BACKEND CLOSED / FRONTEND PENDING:

- Backend `app/legendary_forge/__init__.py` (~665 righe compact): seed idempotente **6 ricette** + 6 legendary items. Determinismo RNG `_rng_for(guild_id, order_id)`. Guild-level gate 5. Durata craft 180s V1.
- **BOP totale**: legendary instances in collection dedicata `legendary_item_instances`. Tutti flag NO_TRADE + `bound_to_guild_id`.
- **Stat cap hard +50% vs epic baseline 2026-Q2**: `EPIC_STAT_BASELINE` + `LEGENDARY_CAP` + `_validate_base_stats_within_cap()` seed-time guardrail. Clamp → `LEGENDARY_STAT_CLAMPED` audit.
- **Pity system**: 5 streak senza perfezionato → 6° imperfetto forzato a normale. Reset su perfezionato reale.
- **Materiali rimappati**: brief originale usava 8 slug inesistenti → rimappato su reali (`iron_shard, raw_leather, arcane_dust, greater_arcane_dust, dragon_essence`) con approvazione utente + doc esplicita nel report.
- **8 endpoint** (5 public + 3 admin), 5 audit UPPERCASE, whitelist 23→28. Recovery script `recover_stuck_legendary_orders.py`.
- **Test**: 33/33 PASS. Regression full **248 passed / 2 skipped / 2 failed** (2 legacy R16.0 debt). Zero regressioni Phase 5A.
- **3 bug scoperti+fixati** durante Phase 5A: signature `user_guild_or_404`, DuplicateKey → collection dedicata, test IDs collision → uuid prefix.

**Vincoli**: NO deploy · NO hard delete · NO scheduler · NO P2W · NO RMT · BOP totale · clamp hard · preview trasparente · pity trasparente · guild lvl 5 gate.

**Report**: `/app/memory/round163_phase5A_final_report.md` (15 sezioni).

**Next**: attesa `e1_tester` E2E backend → iterazione 2 Frontend (LegendaryForge.jsx + LegendaryForgeRecipe.jsx + LegendaryForgeOrders.jsx + MiniCard + nav) → sigillo OFFICIALLY CLOSED.


---

## Round 16.3 Phase 5A OFFICIALLY CLOSED ✅ — 2026-07-01 (Iterazione 3 Frontend)

**Phase 5A (Forgia Leggendaria) — completa Backend + Frontend + Docs**:

- **Frontend web** (3 pagine + 1 mini-card):
  - `LegendaryForge.jsx` — hub ricette (gate lvl 5).
  - `LegendaryForgeRecipe.jsx` — dettaglio con **probabilità trasparenti**, pity status, checklist requisiti, **warning BOP** con checkbox awareness obbligatoria pre-craft.
  - `LegendaryForgeOrders.jsx` — ordini attivi + storico + auto-refresh 30s.
  - `LegendaryForgeMiniCard.jsx` — mini-card in Dashboard V2.
- **Wiring**: +3 route `ProtectedRoute requireGuild` in `App.js`, voce nav "Forgia Leggendaria" (badge NEW), mount MiniCard in Dashboard.
- **Vincoli UI**: mobile-first, `pb-32 md:pb-8`, touch target ≥44x44, no `overflow-x` fisso, tema dark coerente, `data-testid` naming coerente.

**Osservazioni non-bloccanti** (post-testing manuale utente):
1. `/api/market/listings` → 307 redirect a `/api/auction/listings` (consolidamento intenzionale).
2. PATCH admin recipe usa **query string** `?is_active=<bool>` (non body).
3. Slug leggendari: **`legendary_cape_aveol`** (non `cloak_aveol`).

**Validazione finale**:
- `pytest tests/backend_round163_phase5A_test.py -q` → **38/38 PASS**.
- `yarn build` → OK (1 warning legacy non-Phase-5A in ClassHalls.jsx).
- Bundle: 348.29 kB gzip (-9 B).

**Report completo**: `/app/memory/round163_phase5A_final_report.md` sez. 17.

**Next tasks**:
- ⏳ Attesa conferma utente per **Phase 5B — Forgia di Arfus (P1)** — bilanciamento tecnologie passive gilda con cap +30% totale.
- 🔒 Phase 6+ (P2): patti commerciali gilda, specializzazioni gilda, PvP continentale, stalla/cavalcature — in coda dopo Phase 5B.
- 🐛 Debito tecnico R16.0 (`test_t03_alchemist_class_halls_per_guild`, `test_t03_all_adventurers_have_race_and_gender`) — noto, non-bloccante, non regression Phase 5A.

---

## Round 16.3 Phase 5B — Backend + Chronicle Enhancement 🟡 (2026-07-01)

**Phase 5B Iterazione 1 — BACKEND CLOSED / FRONTEND PENDING**:

- **Forgia di Arfus V0** (10 tecnologie passive, cap +30% con category
  caps differenziati, max 5 attive, no stack same-cat, guild lvl ≥ 6,
  CAS orders + on-visit resolve)
- **Applier integrato** in 5 servizi (expedition XP, raid score+XP,
  world_boss contribution, resource drop-rate, legendary success+perfezionato)
- **Chronicle Enhancement**: `legendary_perfezionato` server-wide
  announcement via riuso `audit_log` (no nuova collection)
- 9 endpoint arfus (6 public + 3 admin) + 5 nuovi audit UPPERCASE

**Validazione**:
- Phase 5B: 39 passed, 1 skipped
- R16.3 phases 1-5B: 185 passed, 2 skipped, 0 fail
- Backward-compat Phase 5A: 38/38 pass

**Deviazioni dal brief** (rationale nel report §6):
1. Chronicle NON usa nuova collection — reuse `audit_log` (strictly better)
2. `/api/chronicle/latest` non aggiunto — `/api/chronicle?limit=N` equivalente
3. Whitelist +5 (non +7) — 2 opzionali skipped per design

**Report**: `/app/memory/round163_phase5B_final_report.md`

**Next Action Items**:
- ⏳ Verifica manuale utente Phase 5B backend
- ⏳ Iterazione 2 Frontend Phase 5B (3 pagine + MiniCard)
- 🔒 Phase 6+ (P2): patti commerciali, specializzazioni, PvP, stalla
- 🐛 Debito legacy pre-esistente: `test_openapi_path_count_is_61`
  (hard-coded, path count ora 218), raid lifecycle 423 pre-esistenti,
  2 alchemist/adventurers noti — non regressions Phase 5B

